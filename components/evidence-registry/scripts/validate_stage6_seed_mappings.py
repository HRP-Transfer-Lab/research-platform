#!/usr/bin/env python3
"""Validate Stage 6 quantitative seed mappings against the local Registry.

Read-only. Proves stable outcome-key parity, controlled quantitative semantics,
contrast-scope rules, conservative missingness, and the human-approval boundary.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage6_seed_mappings.v1.json"

STATUSES = {
    "not_yet_extracted", "partially_extracted", "reviewed_complete",
    "reviewed_no_quantitative_estimate", "not_reported", "not_applicable",
}
SCOPES = {
    "study_contrast", "within_arm", "single_group", "association",
    "measurement", "source_level_synthesis", "other",
}
TYPES = {
    "raw_mean", "raw_proportion", "change_score", "mean_difference",
    "standardised_mean_difference", "odds_ratio", "risk_ratio",
    "hazard_ratio", "correlation", "regression_coefficient", "rate_ratio", "other",
}
ADJUSTMENT = {"unadjusted", "adjusted", "partially_adjusted", "not_applicable", "unclear"}
SCALE = {"higher_is_better", "higher_is_worse", "neutral_or_metric_defined", "unclear"}


def run_psql(container: str, sql: str) -> str:
    proc = subprocess.run(
        ["docker", "exec", "-i", container, "psql", "-U", "postgres", "-d", "postgres", "-At", "-F", "|", "-c", sql],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout.strip()


def norm(v):
    return "" if v is None else str(v)


def key(row: dict) -> tuple[str, str, str, str]:
    return (
        norm(row.get("source_id")),
        norm(row.get("outcome_name")),
        norm(row.get("legacy_rung")),
        norm(row.get("raw_timepoint")),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--container", default="supabase_db_research-platform")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    mappings = manifest.get("mappings", [])

    if manifest.get("mapping_source") != "agent_candidate" or manifest.get("review_status") != "proposed":
        raise SystemExit("Stage 6 manifest must remain agent_candidate / proposed before human review.")
    if len(mappings) != 38:
        raise SystemExit(f"Expected 38 Stage 6 outcome mappings, found {len(mappings)}")

    manifest_keys = [key(row) for row in mappings]
    if len(set(manifest_keys)) != 38:
        raise SystemExit("Duplicate stable outcome keys found in Stage 6 manifest.")

    db_sql = r"""
select s.source_id, o.outcome_name, coalesce(o.evidence_rung,''), coalesce(o.timepoint,'')
from public.evidence_outcome o
join public.study s on s.study_id=o.study_id
order by s.source_id, o.outcome_id;
"""
    db_keys = []
    for line in run_psql(args.container, db_sql).splitlines():
        parts = line.split("|", 3)
        if len(parts) != 4:
            raise SystemExit(f"Unexpected database row: {line}")
        db_keys.append(tuple(parts))
    if len(db_keys) != 38:
        raise SystemExit(f"Expected 38 database outcomes, found {len(db_keys)}")

    missing = sorted(set(db_keys) - set(manifest_keys))
    extra = sorted(set(manifest_keys) - set(db_keys))
    if missing or extra:
        print("Missing manifest keys:", missing)
        print("Extra manifest keys:", extra)
        raise SystemExit("Stage 6 stable outcome-key parity failed.")

    invalid = []
    effects = 0
    arm_summaries = 0
    partial = 0
    not_yet = 0
    contrast_effects = 0
    pooled_effects = 0

    for row in mappings:
        k = key(row)
        status = row.get("quantitative_extraction_status")
        if status not in STATUSES:
            invalid.append((k, "quantitative_extraction_status", status))
        partial += status == "partially_extracted"
        not_yet += status == "not_yet_extracted"

        row_effects = row.get("effects", [])
        row_summaries = row.get("arm_summaries", [])
        effects += len(row_effects)
        arm_summaries += len(row_summaries)

        estimate_keys = [e.get("estimate_key") for e in row_effects]
        if len(estimate_keys) != len(set(estimate_keys)) or any(not x for x in estimate_keys):
            invalid.append((k, "estimate_keys", estimate_keys))

        for e in row_effects:
            scope = e.get("estimate_scope")
            etype = e.get("estimate_type")
            adjustment = e.get("adjustment_status")
            scale = e.get("scale_direction")
            if scope not in SCOPES:
                invalid.append((k, "estimate_scope", scope))
            if etype not in TYPES:
                invalid.append((k, "estimate_type", etype))
            if adjustment not in ADJUSTMENT:
                invalid.append((k, "adjustment_status", adjustment))
            if scale not in SCALE:
                invalid.append((k, "scale_direction", scale))

            contrast_key = e.get("contrast_key")
            if scope == "study_contrast":
                contrast_effects += 1
                if not contrast_key:
                    invalid.append((k, "study_contrast_without_contrast_key", contrast_key))
            elif contrast_key is not None:
                invalid.append((k, "noncontrast_scope_with_contrast_key", contrast_key))
            if scope == "source_level_synthesis":
                pooled_effects += 1

            lo, hi = e.get("ci_lower"), e.get("ci_upper")
            if (lo is None) != (hi is None):
                invalid.append((k, "partial_ci", (lo, hi)))
            if lo is not None and hi is not None and lo > hi:
                invalid.append((k, "ci_order", (lo, hi)))
            if e.get("ci_level") is not None and not (0 < float(e["ci_level"]) <= 1):
                invalid.append((k, "ci_level", e.get("ci_level")))
            if e.get("n_analysed") is not None and float(e["n_analysed"]) <= 0:
                invalid.append((k, "n_analysed", e.get("n_analysed")))

    if invalid:
        for item in invalid:
            print("INVALID:", item)
        raise SystemExit(f"Found {len(invalid)} invalid Stage 6 mapping values.")

    # Seed-specific conservation gate from the read-only audit.
    if effects != 1 or pooled_effects != 1 or contrast_effects != 0 or arm_summaries != 0:
        raise SystemExit(
            f"Unexpected Stage 6 seed quantitative surface: effects={effects}, pooled={pooled_effects}, "
            f"contrast_effects={contrast_effects}, arm_summaries={arm_summaries}"
        )
    if partial != 1 or not_yet != 37:
        raise SystemExit(f"Expected 1 partially_extracted and 37 not_yet_extracted rows; got {partial} and {not_yet}")

    target = next(row for row in mappings if row["source_id"] == "rt-2026-007" and row["outcome_name"] == "overall post-training working memory")
    effect = target["effects"][0]
    if effect["metric"] != "Hedges_g" or effect["estimate_value"] != 0.191 or effect["ci_lower"] != 0.062 or effect["ci_upper"] != 0.32:
        raise SystemExit("Historical rt-2026-007 quantitative estimate was not preserved exactly.")
    if effect.get("ci_level") is not None or effect.get("n_analysed") is not None or effect.get("standard_error") is not None:
        raise SystemExit("Stage 6 manifest inferred CI level, N, or SE not present in the seed.")

    print("STAGE 6 SEED MAPPINGS VALID: outcomes=38; partially_extracted=1; not_yet_extracted=37")
    print("effects=1; source_level_synthesis=1; study_contrast_effects=0; arm_summaries=0")
    print("stable_outcome_identity: PASS")
    print("controlled_quantitative_semantics: PASS")
    print("contrast_scope_integrity: PASS")
    print("legacy_effect_conservation: PASS (Hedges_g=0.191; CI=0.062..0.32; CI level remains unknown)")
    print("no_fabricated_quantitative_fields: PASS")
    print("human_approval_boundary: PASS (manifest remains agent_candidate / proposed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
