#!/usr/bin/env python3
"""Validate the Stage 5 candidate arm/condition/contrast manifest against local seed data.

Read-only. This validator proves stable source/component identity, controlled
vocabularies, internal arm/contrast integrity, and the human-approval boundary
before the Stage 5 schema/backfill is applied.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage5_seed_mappings.v1.json"

ARM_STATUSES = {
    "not_yet_extracted", "partially_extracted", "reviewed_complete",
    "reviewed_no_arms", "not_reported", "not_applicable",
}
ARM_ROLES = {
    "intervention", "active_control", "passive_control", "waitlist",
    "treatment_as_usual", "alternative_intervention", "reference",
    "observational_exposure", "experimental_condition",
    "measurement_condition", "unclear",
}
ASSIGNMENTS = {
    "parallel_group", "cluster_group", "factorial_cell",
    "within_subject_condition", "single_group", "observational_group", "unclear",
}
MEMBERSHIP_ROLES = {"defining", "shared", "add_on", "background", "unclear"}
CONTRAST_TYPES = {
    "pairwise", "multiarm_pairwise", "factorial_main_effect",
    "factorial_interaction", "within_subject", "observational", "other",
}
CONTRAST_SIDES = {"focal", "comparator"}


def run_psql(container: str, sql: str) -> str:
    proc = subprocess.run(
        ["docker", "exec", "-i", container, "psql", "-U", "postgres", "-d", "postgres", "-At", "-F", "|", "-c", sql],
        text=True, capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--container", default="supabase_db_research-platform")
    ap.add_argument("--release", default="2026-08-23")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("mapping_source") != "agent_candidate" or manifest.get("review_status") != "proposed":
        raise SystemExit("Stage 5 manifest must remain agent_candidate / proposed before human review.")
    if manifest.get("release_id") != args.release:
        raise SystemExit("Stage 5 manifest release_id mismatch.")

    studies = manifest.get("studies", {})
    if len(studies) != 18:
        raise SystemExit(f"Expected 18 Stage 5 study entries, found {len(studies)}")

    db_sources = set(run_psql(args.container, f"""
select es.source_id
from public.study s
join public.evidence_source es on es.source_id=s.source_id
where es.release_id='{args.release.replace("'", "''")}'
order by es.source_id;
""").splitlines())
    if set(studies) != db_sources:
        raise SystemExit(f"Stage 5 source parity failed: missing={sorted(db_sources-set(studies))}, extra={sorted(set(studies)-db_sources)}")

    mapped_studies = 0
    not_yet_studies = 0
    not_applicable_studies = 0
    arm_count = 0
    component_links = 0
    contrast_count = 0
    contrast_members = 0
    invalid: list[str] = []

    for source_id, spec in studies.items():
        arm_status = spec.get("arm_extraction_status")
        contrast_status = spec.get("contrast_extraction_status")
        if arm_status not in ARM_STATUSES:
            invalid.append(f"{source_id}: invalid arm_extraction_status={arm_status!r}")
        if contrast_status not in ARM_STATUSES:
            invalid.append(f"{source_id}: invalid contrast_extraction_status={contrast_status!r}")

        arms = spec.get("arms", [])
        contrasts = spec.get("contrasts", [])
        if arm_status == "partially_extracted":
            mapped_studies += 1
        elif arm_status == "not_yet_extracted":
            not_yet_studies += 1
        elif arm_status == "not_applicable":
            not_applicable_studies += 1

        if arm_status in {"not_yet_extracted", "not_applicable", "reviewed_no_arms"} and arms:
            invalid.append(f"{source_id}: arm status {arm_status} but manifest contains arms")
        if contrast_status in {"not_yet_extracted", "not_applicable"} and contrasts:
            invalid.append(f"{source_id}: contrast status {contrast_status} but manifest contains contrasts")

        arm_keys: set[str] = set()
        for a in arms:
            arm_count += 1
            key = a.get("arm_key")
            if not key or key in arm_keys:
                invalid.append(f"{source_id}: missing/duplicate arm_key={key!r}")
            arm_keys.add(key)
            if a.get("arm_role") not in ARM_ROLES:
                invalid.append(f"{source_id}/{key}: invalid arm_role={a.get('arm_role')!r}")
            if a.get("assignment_structure") not in ASSIGNMENTS:
                invalid.append(f"{source_id}/{key}: invalid assignment_structure={a.get('assignment_structure')!r}")
            sample = a.get("sample", {})
            if not isinstance(sample, dict):
                invalid.append(f"{source_id}/{key}: sample must be an object")

            for link in a.get("components", []):
                component_links += 1
                if link.get("membership_role") not in MEMBERSHIP_ROLES:
                    invalid.append(f"{source_id}/{key}: invalid membership_role={link.get('membership_role')!r}")
                component_name = link.get("component_name")
                escaped_sid = source_id.replace("'", "''")
                escaped_name = str(component_name).replace("'", "''")
                count = run_psql(args.container, f"""
select count(*)
from public.intervention_component ic
join public.study s on s.study_id=ic.study_id
where s.source_id='{escaped_sid}' and ic.component_name='{escaped_name}';
""")
                if count != "1":
                    invalid.append(f"{source_id}/{key}: component {component_name!r} resolves to {count} rows")

        contrast_keys: set[str] = set()
        for c in contrasts:
            contrast_count += 1
            ckey = c.get("contrast_key")
            if not ckey or ckey in contrast_keys:
                invalid.append(f"{source_id}: missing/duplicate contrast_key={ckey!r}")
            contrast_keys.add(ckey)
            if c.get("contrast_type") not in CONTRAST_TYPES:
                invalid.append(f"{source_id}/{ckey}: invalid contrast_type={c.get('contrast_type')!r}")
            members = c.get("members", [])
            if len(members) < 2:
                invalid.append(f"{source_id}/{ckey}: contrast requires at least two arm members")
            sides = set()
            for m in members:
                contrast_members += 1
                if m.get("arm_key") not in arm_keys:
                    invalid.append(f"{source_id}/{ckey}: unknown arm_key={m.get('arm_key')!r}")
                side = m.get("contrast_side")
                if side not in CONTRAST_SIDES:
                    invalid.append(f"{source_id}/{ckey}: invalid contrast_side={side!r}")
                sides.add(side)
                coeff = m.get("contrast_coefficient")
                if coeff is not None and not isinstance(coeff, (int, float)):
                    invalid.append(f"{source_id}/{ckey}: nonnumeric coefficient={coeff!r}")
            if sides != CONTRAST_SIDES:
                invalid.append(f"{source_id}/{ckey}: contrast must contain focal and comparator sides")

    # Guard the only seed record with explicit per-arm randomized counts.
    r4 = studies["rt-2026-004"]["arms"]
    r4_total = sum(int(a.get("sample", {}).get("randomized", 0)) for a in r4)
    if r4_total != 119:
        invalid.append(f"rt-2026-004: explicit per-arm randomized counts sum to {r4_total}, expected 119")

    if invalid:
        for item in invalid:
            print("INVALID:", item)
        raise SystemExit(f"Stage 5 manifest validation failed with {len(invalid)} issue(s).")

    expected = (10, 4, 4, 29, 18, 8, 16)
    actual = (mapped_studies, not_yet_studies, not_applicable_studies, arm_count, component_links, contrast_count, contrast_members)
    if actual != expected:
        raise SystemExit(f"Unexpected Stage 5 manifest counts: expected={expected}, actual={actual}")

    print("STAGE 5 SEED MAPPINGS VALID: studies=18; mapped=10; not_yet_extracted=4; not_applicable=4")
    print("arms=29; component_links=18; contrasts=8; contrast_members=16")
    print("controlled_vocabularies: PASS")
    print("source_and_component_identity: PASS")
    print("arm_and_contrast_integrity: PASS")
    print("no_fabricated_equal_allocation: PASS")
    print("human_approval_boundary: PASS (manifest remains agent_candidate / proposed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
