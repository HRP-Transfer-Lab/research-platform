#!/usr/bin/env python3
"""Apply Stage 6 candidate quantitative mappings to local Supabase.

All inserted scientific mappings remain agent_candidate/proposed. Historical
one-effect compatibility fields are not modified. Existing human-approved
Stage 6 rows/statuses are never overwritten by this replay helper.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage6_seed_mappings.v1.json"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str, *, tuples_only: bool = False) -> str:
    cmd = ["docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres"]
    if tuples_only:
        cmd.extend(["-A", "-t", "-F", "|"])
    result = run(cmd, input_text=sql, capture=tuples_only)
    return result.stdout.strip() if tuples_only else ""


def lit(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def one(rows: str, label: str) -> str:
    values = [r.strip() for r in rows.splitlines() if r.strip()]
    if len(values) != 1:
        raise SystemExit(f"Expected exactly one {label}; got {values!r}")
    return values[0]


def resolve_outcome(container: str, row: dict) -> tuple[str, str]:
    source_id = row["source_id"]
    sql = f"""
select eo.outcome_id, eo.study_id
from public.evidence_outcome eo
join public.study s on s.study_id = eo.study_id
where s.source_id = {lit(source_id)}
  and eo.outcome_name = {lit(row['outcome_name'])}
  and eo.evidence_rung is not distinct from {lit(row.get('legacy_rung'))}
  and eo.timepoint is not distinct from {lit(row.get('raw_timepoint'))}
order by eo.outcome_id;
"""
    value = one(psql(container, sql, tuples_only=True), f"outcome {source_id}/{row['outcome_name']}")
    outcome_id, study_id = value.split("|", 1)
    return outcome_id, study_id


def resolve_contrast(container: str, study_id: str, source_id: str, contrast_key: str | None) -> str | None:
    if contrast_key is None:
        return None
    return one(
        psql(
            container,
            f"select contrast_id from public.study_contrast where study_id={study_id} and contrast_key={lit(contrast_key)} order by contrast_id;",
            tuples_only=True,
        ),
        f"contrast {source_id}/{contrast_key}",
    )


def resolve_arm(container: str, study_id: str, source_id: str, arm_key: str) -> str:
    return one(
        psql(
            container,
            f"select arm_id from public.study_arm where study_id={study_id} and arm_key={lit(arm_key)} order by arm_id;",
            tuples_only=True,
        ),
        f"arm {source_id}/{arm_key}",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Stage 6 candidate quantitative seed mappings to local Supabase.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("mapping_source") != "agent_candidate" or manifest.get("review_status") != "proposed":
        raise SystemExit("Stage 6 seed manifest must remain agent_candidate/proposed.")

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running.")

    print(f"Applying Stage 6 candidate mappings: {manifest['manifest_version']} ({manifest['release_id']})")

    outcome_count = effect_count = arm_summary_count = 0

    for row in manifest["mappings"]:
        outcome_count += 1
        outcome_id, study_id = resolve_outcome(args.container, row)
        source_id = row["source_id"]

        psql(args.container, f"""
update public.outcome_stage6_status
set quantitative_extraction_status={lit(row['quantitative_extraction_status'])},
    mapping_source='agent_candidate',
    review_status='proposed',
    notes={lit('Stage 6 seed candidate quantitative mapping; absence of extracted numbers does not imply a null effect or no reported quantitative result.')},
    updated_at=now()
where outcome_id={outcome_id}
  and mapping_source in ('migration','agent_candidate')
  and review_status <> 'approved';
""")

        for effect in row.get("effects", []):
            contrast_id = resolve_contrast(args.container, study_id, source_id, effect.get("contrast_key"))
            psql(args.container, f"""
insert into public.effect_estimate (
  outcome_id, contrast_id, estimate_key, estimate_scope, estimate_type,
  metric, estimate_value, standard_error, ci_level, ci_lower, ci_upper,
  p_value, n_analysed, adjustment_status, model_specification,
  time_or_model_label, unit, scale_direction, source_reported, rationale,
  mapping_source, review_status
) values (
  {outcome_id}, {lit(contrast_id)}, {lit(effect['estimate_key'])},
  {lit(effect['estimate_scope'])}, {lit(effect['estimate_type'])},
  {lit(effect['metric'])}, {lit(effect['estimate_value'])},
  {lit(effect.get('standard_error'))}, {lit(effect.get('ci_level'))},
  {lit(effect.get('ci_lower'))}, {lit(effect.get('ci_upper'))},
  {lit(effect.get('p_value'))}, {lit(effect.get('n_analysed'))},
  {lit(effect['adjustment_status'])}, {lit(effect.get('model_specification'))},
  {lit(effect.get('time_or_model_label'))}, {lit(effect.get('unit'))},
  {lit(effect['scale_direction'])}, {lit(effect.get('source_reported', True))},
  {lit(effect.get('rationale'))}, 'agent_candidate', 'proposed'
)
on conflict (outcome_id, estimate_key) do update set
  contrast_id=excluded.contrast_id,
  estimate_scope=excluded.estimate_scope,
  estimate_type=excluded.estimate_type,
  metric=excluded.metric,
  estimate_value=excluded.estimate_value,
  standard_error=excluded.standard_error,
  ci_level=excluded.ci_level,
  ci_lower=excluded.ci_lower,
  ci_upper=excluded.ci_upper,
  p_value=excluded.p_value,
  n_analysed=excluded.n_analysed,
  adjustment_status=excluded.adjustment_status,
  model_specification=excluded.model_specification,
  time_or_model_label=excluded.time_or_model_label,
  unit=excluded.unit,
  scale_direction=excluded.scale_direction,
  source_reported=excluded.source_reported,
  rationale=excluded.rationale,
  updated_at=now()
where public.effect_estimate.mapping_source in ('migration','agent_candidate')
  and public.effect_estimate.review_status <> 'approved';
""")
            effect_count += 1

        for summary in row.get("arm_summaries", []):
            arm_id = resolve_arm(args.container, study_id, source_id, summary["arm_key"])
            psql(args.container, f"""
insert into public.arm_outcome_summary (
  outcome_id, arm_id, summary_key, n_analysed, mean, sd, se, proportion,
  count, change_mean, change_sd, unit, source_reported, rationale,
  mapping_source, review_status
) values (
  {outcome_id}, {arm_id}, {lit(summary['summary_key'])},
  {lit(summary.get('n_analysed'))}, {lit(summary.get('mean'))},
  {lit(summary.get('sd'))}, {lit(summary.get('se'))},
  {lit(summary.get('proportion'))}, {lit(summary.get('count'))},
  {lit(summary.get('change_mean'))}, {lit(summary.get('change_sd'))},
  {lit(summary.get('unit'))}, {lit(summary.get('source_reported', True))},
  {lit(summary.get('rationale'))}, 'agent_candidate', 'proposed'
)
on conflict (outcome_id, arm_id, summary_key) do update set
  n_analysed=excluded.n_analysed,
  mean=excluded.mean,
  sd=excluded.sd,
  se=excluded.se,
  proportion=excluded.proportion,
  count=excluded.count,
  change_mean=excluded.change_mean,
  change_sd=excluded.change_sd,
  unit=excluded.unit,
  source_reported=excluded.source_reported,
  rationale=excluded.rationale,
  updated_at=now()
where public.arm_outcome_summary.mapping_source in ('migration','agent_candidate')
  and public.arm_outcome_summary.review_status <> 'approved';
""")
            arm_summary_count += 1

    print(
        f"STAGE 6 CANDIDATE MAPPINGS APPLIED: outcomes={outcome_count}; "
        f"effects={effect_count}; arm_summaries={arm_summary_count}"
    )
    print("All Stage 6 candidate mappings remain review_status=proposed / mapping_source=agent_candidate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
