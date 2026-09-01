#!/usr/bin/env python3
"""Apply one manifest-driven Stage 12 quality/RoB appraisal candidate locally.

All scientific rows remain agent_candidate/proposed. This script never performs
human approval and never mutates the historical release or CSI Gateway.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import apply_stage12_q1_rt001_quality_rob_candidate as base
from stage12_quality_batch_common import decision_count

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = base.DEFAULT_CONTAINER


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply one manifest-driven Stage 12 quality/RoB candidate locally.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--manifest", type=Path, required=True)
    args = ap.parse_args()

    running = base.run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    batch_id = str(manifest.get("batch_id") or "")
    source_id = str(manifest.get("source_id") or "")
    if not batch_id.startswith("quality_"):
        raise RuntimeError(f"Unexpected quality appraisal batch_id {batch_id!r}")
    if not source_id.startswith("rt-"):
        raise RuntimeError(f"Unexpected source_id {source_id!r}")
    if manifest.get("mapping_source") != "agent_candidate" or manifest.get("review_status") != "proposed":
        raise RuntimeError("Candidate manifest must remain agent_candidate/proposed")

    study = manifest.get("study_assessment") or {}
    results = manifest.get("result_assessments") or []
    if not study or not results:
        raise RuntimeError("Quality manifest requires one study assessment and at least one result assessment")

    required_frameworks = {str(study["framework_key"])} | {str(r["framework_key"]) for r in results}
    rows = base.psql(args.container, """
select framework_key from public.assessment_framework_definition
where active=true order by framework_key;
""", capture=True).splitlines()
    active_frameworks = set(rows)
    missing_frameworks = sorted(required_frameworks - active_frameworks)
    if missing_frameworks:
        raise RuntimeError(f"Required active assessment frameworks missing: {missing_frameworks}")

    study_id = base.resolve_study(args.container, source_id)
    current_study_status = base.one(base.psql(args.container, f"""
select mapping_source||'|'||review_status||'|'||assessment_status
from public.study_quality_status where study_id={study_id};
""", capture=True), "study quality status")
    if current_study_status.startswith("human_review|approved|"):
        raise RuntimeError(f"{source_id} study quality status is already human-approved; refusing candidate overwrite")

    resolved_results: list[tuple[dict[str, Any], int, int | None]] = []
    for result in results:
        outcome_id = base.resolve_outcome(args.container, study_id, result)
        status = base.one(base.psql(args.container, f"""
select mapping_source||'|'||review_status||'|'||assessment_status
from public.result_rob_status where outcome_id={outcome_id};
""", capture=True), f"result status {outcome_id}")
        if status.startswith("human_review|approved|"):
            raise RuntimeError(f"Outcome {outcome_id} RoB status is already human-approved; refusing candidate overwrite")
        contrast_id = base.resolve_contrast(args.container, study_id, result.get("contrast_key"))
        resolved_results.append((result, outcome_id, contrast_id))

    historical_before = base.psql(args.container, """
select
 (select status from public.evidence_release where release_id='2026-08-23'),
 (select count(*) from public.release_source_version where release_id='2026-08-23'),
 (select count(*) from public.csi_gateway_evidence_card where evidence_release_id='2026-08-23'),
 (select count(*) from public.csi_gateway_claim where evidence_release_id='2026-08-23');
""", capture=True)

    sql: list[str] = ["begin;", "set local lock_timeout='5s';", "set local statement_timeout='120s';"]
    sql.append(f"""
update public.study_quality_status
set assessment_status='reviewed_complete',mapping_source='agent_candidate',review_status='proposed',
    notes={base.lit(f'{batch_id} candidate study-level appraisal complete; human approval required.')},updated_at=now()
where study_id={study_id} and mapping_source in ('migration','agent_candidate') and review_status='proposed';
""")
    sql.append(f"""
insert into public.study_quality_assessment(
  study_id,assessment_key,assessment_kind,framework_key,framework_version,overall_judgement,
  assessment_status,notes,assessor,assessed_on,mapping_source,review_status
) values (
  {study_id},{base.lit(study['assessment_key'])},{base.lit(study['assessment_kind'])},{base.lit(study['framework_key'])},
  {base.lit(study.get('framework_version'))},{base.lit(study.get('overall_judgement'))},{base.lit(study['assessment_status'])},
  {base.lit(study.get('notes'))},null,null,'agent_candidate','proposed'
)
on conflict (study_id,assessment_key) do update set
  assessment_kind=excluded.assessment_kind,
  framework_key=excluded.framework_key,
  framework_version=excluded.framework_version,
  overall_judgement=excluded.overall_judgement,
  assessment_status=excluded.assessment_status,
  notes=excluded.notes,
  mapping_source='agent_candidate',review_status='proposed',updated_at=now()
where public.study_quality_assessment.mapping_source='agent_candidate'
  and public.study_quality_assessment.review_status='proposed';
""")
    for domain in study.get("domains", []):
        sql.append(base.study_domain_sql(study_id, study["assessment_key"], domain))

    for result, outcome_id, contrast_id in resolved_results:
        sql.append(f"""
update public.result_rob_status
set assessment_status='reviewed_complete',mapping_source='agent_candidate',review_status='proposed',
    notes={base.lit(f'{batch_id} candidate result-specific RoB appraisal complete; human approval required.')},updated_at=now()
where outcome_id={outcome_id} and mapping_source in ('migration','agent_candidate') and review_status='proposed';
""")
        sql.append(f"""
insert into public.result_risk_of_bias_assessment(
  outcome_id,contrast_id,effect_estimate_id,assessment_key,framework_key,framework_version,
  estimand_or_result_scope,overall_judgement,assessment_status,notes,assessor,assessed_on,
  mapping_source,review_status
) values (
  {outcome_id},{base.lit(contrast_id)},null,{base.lit(result['assessment_key'])},{base.lit(result['framework_key'])},
  {base.lit(result.get('framework_version'))},{base.lit(result.get('estimand_or_result_scope'))},
  {base.lit(result.get('overall_judgement'))},{base.lit(result['assessment_status'])},{base.lit(result.get('notes'))},
  null,null,'agent_candidate','proposed'
)
on conflict (outcome_id,assessment_key) do update set
  contrast_id=excluded.contrast_id,
  effect_estimate_id=excluded.effect_estimate_id,
  framework_key=excluded.framework_key,
  framework_version=excluded.framework_version,
  estimand_or_result_scope=excluded.estimand_or_result_scope,
  overall_judgement=excluded.overall_judgement,
  assessment_status=excluded.assessment_status,
  notes=excluded.notes,
  mapping_source='agent_candidate',review_status='proposed',updated_at=now()
where public.result_risk_of_bias_assessment.mapping_source='agent_candidate'
  and public.result_risk_of_bias_assessment.review_status='proposed';
""")
        for domain in result.get("domains", []):
            sql.append(base.result_domain_sql(outcome_id, result["assessment_key"], domain))

    sql.append("commit;")
    base.psql(args.container, "\n".join(sql))

    expected = decision_count(manifest)
    candidate_count = int(base.one(base.psql(args.container, f"""
select
  (select count(*) from public.study_quality_status where study_id={study_id} and mapping_source='agent_candidate' and review_status='proposed')
+ (select count(*) from public.result_rob_status r join public.evidence_outcome eo on eo.outcome_id=r.outcome_id where eo.study_id={study_id} and r.mapping_source='agent_candidate' and r.review_status='proposed')
+ (select count(*) from public.study_quality_assessment where study_id={study_id} and mapping_source='agent_candidate' and review_status='proposed')
+ (select count(*) from public.result_risk_of_bias_assessment a join public.evidence_outcome eo on eo.outcome_id=a.outcome_id where eo.study_id={study_id} and a.mapping_source='agent_candidate' and a.review_status='proposed')
+ (select count(*) from public.assessment_domain_judgement d join public.study_quality_assessment a on a.study_quality_assessment_id=d.study_quality_assessment_id where a.study_id={study_id} and d.mapping_source='agent_candidate' and d.review_status='proposed')
+ (select count(*) from public.assessment_domain_judgement d join public.result_risk_of_bias_assessment a on a.result_rob_assessment_id=d.result_rob_assessment_id join public.evidence_outcome eo on eo.outcome_id=a.outcome_id where eo.study_id={study_id} and d.mapping_source='agent_candidate' and d.review_status='proposed');
""", capture=True), "candidate count"))
    if candidate_count != expected:
        raise RuntimeError(f"Expected exactly {expected} {source_id} candidate review-surface rows; found {candidate_count}")

    historical_after = base.psql(args.container, """
select
 (select status from public.evidence_release where release_id='2026-08-23'),
 (select count(*) from public.release_source_version where release_id='2026-08-23'),
 (select count(*) from public.csi_gateway_evidence_card where evidence_release_id='2026-08-23'),
 (select count(*) from public.csi_gateway_claim where evidence_release_id='2026-08-23');
""", capture=True)
    if historical_before != historical_after:
        raise RuntimeError(f"Historical release/Gateway parity changed unexpectedly: {historical_before!r} -> {historical_after!r}")

    revision = base.psql(args.container, "select current_revision from public.scientific_state_revision where singleton=true;", capture=True)
    print("STAGE 12 QUALITY / ROB CANDIDATE APPLIED")
    print(f"batch_id|{batch_id}")
    print(f"source_id|{source_id}")
    print(f"study_id|{study_id}")
    print(f"result_assessments|{len(results)}")
    print("study_assessments|1")
    print(f"domain_judgements|{len(study.get('domains', [])) + sum(len(r.get('domains', [])) for r in results)}")
    print(f"status_candidates|{1 + len(results)}")
    print(f"candidate_review_surface_rows|{candidate_count}")
    print(f"scientific_state_revision|{revision}")
    print("human_review_decisions_applied|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
