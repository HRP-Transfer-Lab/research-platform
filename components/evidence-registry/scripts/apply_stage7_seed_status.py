#!/usr/bin/env python3
"""Apply Stage 7 status-only seed backfill to local Supabase.

The immutable seed contains no formal quality/RoB judgements. This replay helper
therefore resolves all 18 studies and 38 stable outcomes and records only
not_yet_assessed status. It never creates framework assignments or judgements.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage7_seed_status.v1.json"


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
    return "'" + str(value).replace("'", "''") + "'"


def one(rows: str, label: str) -> str:
    values = [row.strip() for row in rows.splitlines() if row.strip()]
    if len(values) != 1:
        raise SystemExit(f"Expected exactly one {label}; got {values!r}")
    return values[0]


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Stage 7 status-only seed backfill to local Supabase.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("mapping_source") != "migration" or manifest.get("review_status") != "proposed":
        raise SystemExit("Stage 7 status manifest must remain migration/proposed.")
    if manifest.get("body_certainty", {}).get("status") != "deferred_to_stage8":
        raise SystemExit("Stage 7 body certainty must remain deferred_to_stage8.")
    backfill = manifest.get("assessment_backfill", {})
    if any(backfill.get(key) for key in ("study_quality_assessments", "result_risk_of_bias_assessments", "domain_judgements")):
        raise SystemExit("Stage 7 immutable seed backfill must not contain assessment judgements.")

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running.")

    study_status = manifest["study_identity"]["status"]
    study_count = 0
    for source_id in manifest["study_identity"]["source_ids"]:
        study_id = one(
            psql(args.container, f"select study_id from public.study where source_id={lit(source_id)} order by study_id;", tuples_only=True),
            f"study for {source_id}",
        )
        psql(args.container, f"""
update public.study_quality_status
set assessment_status={lit(study_status)},
    mapping_source='migration',
    review_status='proposed',
    notes='Immutable seed has no formal study/report quality assessment; no framework or judgement inferred.',
    updated_at=now()
where study_id={study_id}
  and mapping_source in ('migration','agent_candidate')
  and review_status <> 'approved';
""")
        study_count += 1

    identity_path = REPO_ROOT / manifest["result_identity"]["identity_manifest"]
    stage4 = json.loads(identity_path.read_text(encoding="utf-8"))
    result_status = manifest["result_identity"]["status"]
    result_count = 0
    for item in stage4["mappings"]:
        source_id = item["source_id"]
        outcome_name = item["outcome_name"]
        legacy_rung = item.get("legacy_rung")
        raw_timepoint = item.get("raw_timepoint")
        rows = psql(args.container, f"""
select eo.outcome_id
from public.evidence_outcome eo
join public.study s on s.study_id=eo.study_id
where s.source_id={lit(source_id)}
  and eo.outcome_name={lit(outcome_name)}
  and eo.evidence_rung is not distinct from {lit(legacy_rung)}
  and eo.timepoint is not distinct from {lit(raw_timepoint)}
order by eo.outcome_id;
""", tuples_only=True)
        outcome_id = one(rows, f"outcome {source_id}/{outcome_name}/{legacy_rung}/{raw_timepoint}")
        psql(args.container, f"""
update public.result_rob_status
set assessment_status={lit(result_status)},
    mapping_source='migration',
    review_status='proposed',
    notes='Immutable seed has no formal result-specific risk-of-bias assessment; no framework or judgement inferred.',
    updated_at=now()
where outcome_id={outcome_id}
  and mapping_source in ('migration','agent_candidate')
  and review_status <> 'approved';
""")
        result_count += 1

    print(f"STAGE 7 STATUS-ONLY BACKFILL APPLIED: studies={study_count}; results={result_count}; study_assessments=0; result_rob_assessments=0; domain_judgements=0")
    print("No Stage 7 framework assignments or quality/RoB/GRADE judgements were created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
