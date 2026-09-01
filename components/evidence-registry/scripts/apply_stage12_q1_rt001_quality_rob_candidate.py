#!/usr/bin/env python3
"""Apply the rt-2026-001 Stage 12 quality/RoB appraisal candidate locally.

The script writes only Stage 7 candidate appraisal/status rows. Every scientific
row remains mapping_source=agent_candidate and review_status=proposed until a
separate governed human-review packet is explicitly approved.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage12_q1_rt001_quality_rob_candidate.v1.json"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str, *, capture: bool = False) -> str:
    cmd = [
        "docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|",
    ]
    result = run(cmd, input_text=sql, capture=capture)
    return result.stdout.strip() if capture else ""


def lit(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def one(raw: str, label: str) -> str:
    rows = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(rows) != 1:
        raise RuntimeError(f"Expected exactly one {label}; got {rows!r}")
    return rows[0]


def resolve_study(container: str, source_id: str) -> int:
    return int(one(psql(container, f"select study_id from public.study where source_id={lit(source_id)};", capture=True), f"study for {source_id}"))


def resolve_outcome(container: str, study_id: int, row: dict[str, Any]) -> int:
    raw = psql(container, f"""
select outcome_id
from public.evidence_outcome
where study_id={study_id}
  and outcome_name={lit(row['outcome_name'])}
  and evidence_rung is not distinct from {lit(row.get('legacy_rung'))}
  and timepoint is not distinct from {lit(row.get('raw_timepoint'))}
order by outcome_id;
""", capture=True)
    return int(one(raw, f"outcome {row['outcome_name']}/{row.get('legacy_rung')}/{row.get('raw_timepoint')}"))


def resolve_contrast(container: str, study_id: int, contrast_key: str | None) -> int | None:
    if contrast_key is None:
        return None
    raw = psql(container, f"select contrast_id from public.study_contrast where study_id={study_id} and contrast_key={lit(contrast_key)};", capture=True)
    return int(one(raw, f"contrast {contrast_key}"))


def study_domain_sql(study_id: int, assessment_key: str, domain: dict[str, Any]) -> str:
    return f"""
insert into public.assessment_domain_judgement(
  study_quality_assessment_id,result_rob_assessment_id,domain_key,domain_label,judgement,
  supporting_text,notes,order_index,mapping_source,review_status
)
select
  a.study_quality_assessment_id,null,{lit(domain['domain_key'])},{lit(domain['domain_label'])},{lit(domain['judgement'])},
  {lit(domain.get('supporting_text'))},{lit(domain.get('notes'))},{lit(domain.get('order_index'))},'agent_candidate','proposed'
from public.study_quality_assessment a
where a.study_id={study_id} and a.assessment_key={lit(assessment_key)}
on conflict (study_quality_assessment_id,domain_key) where study_quality_assessment_id is not null
do update set
  domain_label=excluded.domain_label,
  judgement=excluded.judgement,
  supporting_text=excluded.supporting_text,
  notes=excluded.notes,
  order_index=excluded.order_index,
  mapping_source='agent_candidate',
  review_status='proposed',
  updated_at=now()
where public.assessment_domain_judgement.mapping_source='agent_candidate'
  and public.assessment_domain_judgement.review_status='proposed';
"""


def result_domain_sql(outcome_id: int, assessment_key: str, domain: dict[str, Any]) -> str:
    return f"""
insert into public.assessment_domain_judgement(
  study_quality_assessment_id,result_rob_assessment_id,domain_key,domain_label,judgement,
  supporting_text,notes,order_index,mapping_source,review_status
)
select
  null,a.result_rob_assessment_id,{lit(domain['domain_key'])},{lit(domain['domain_label'])},{lit(domain['judgement'])},
  {lit(domain.get('supporting_text'))},{lit(domain.get('notes'))},{lit(domain.get('order_index'))},'agent_candidate','proposed'
from public.result_risk_of_bias_assessment a
where a.outcome_id={outcome_id} and a.assessment_key={lit(assessment_key)}
on conflict (result_rob_assessment_id,domain_key) where result_rob_assessment_id is not null
do update set
  domain_label=excluded.domain_label,
  judgement=excluded.judgement,
  supporting_text=excluded.supporting_text,
  notes=excluded.notes,
  order_index=excluded.order_index,
  mapping_source='agent_candidate',
  review_status='proposed',
  updated_at=now()
where public.assessment_domain_judgement.mapping_source='agent_candidate'
  and public.assessment_domain_judgement.review_status='proposed';
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply rt-2026-001 quality/RoB appraisal candidates locally.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("batch_id") != "quality_q1_rt001":
        raise RuntimeError("Unexpected quality appraisal batch_id")
    if manifest.get("source_id") != "rt-2026-001":
        raise RuntimeError("This pilot only accepts source rt-2026-001")
    if manifest.get("mapping_source") != "agent_candidate" or manifest.get("review_status") != "proposed":
        raise RuntimeError("Candidate manifest must remain agent_candidate/proposed")

    framework_rows = psql(args.container, """
select framework_key from public.assessment_framework_definition
where framework_key in ('rob2','custom') and active=true
order by framework_key;
""", capture=True).splitlines()
    if framework_rows != ["custom", "rob2"]:
        raise RuntimeError(f"Expected active custom and rob2 frameworks; got {framework_rows!r}")

    source_id = manifest["source_id"]
    study_id = resolve_study(args.container, source_id)

    current_study_status = one(psql(args.container, f"""
select mapping_source||'|'||review_status||'|'||assessment_status
from public.study_quality_status where study_id={study_id};
""", capture=True), "study quality status")
    if current_study_status.startswith("human_review|approved|"):
        raise RuntimeError("rt-2026-001 study quality status is already human-approved; refusing candidate overwrite")

    resolved_results: list[tuple[dict[str, Any], int, int | None]] = []
    for result in manifest["result_assessments"]:
        outcome_id = resolve_outcome(args.container, study_id, result)
        status = one(psql(args.container, f"""
select mapping_source||'|'||review_status||'|'||assessment_status
from public.result_rob_status where outcome_id={outcome_id};
""", capture=True), f"result status {outcome_id}")
        if status.startswith("human_review|approved|"):
            raise RuntimeError(f"Outcome {outcome_id} RoB status is already human-approved; refusing candidate overwrite")
        contrast_id = resolve_contrast(args.container, study_id, result.get("contrast_key"))
        resolved_results.append((result, outcome_id, contrast_id))

    historical_before = psql(args.container, """
select
 (select status from public.evidence_release where release_id='2026-08-23'),
 (select count(*) from public.release_source_version where release_id='2026-08-23'),
 (select count(*) from public.csi_gateway_evidence_card where evidence_release_id='2026-08-23'),
 (select count(*) from public.csi_gateway_claim where evidence_release_id='2026-08-23');
""", capture=True)

    study = manifest["study_assessment"]
    sql: list[str] = ["begin;", "set local lock_timeout='5s';", "set local statement_timeout='120s';"]
    sql.append(f"""
update public.study_quality_status
set assessment_status='reviewed_complete',mapping_source='agent_candidate',review_status='proposed',
    notes={lit('Q1 rt-2026-001 candidate study-level appraisal complete; human approval required.')},updated_at=now()
where study_id={study_id} and mapping_source in ('migration','agent_candidate') and review_status='proposed';
""")
    sql.append(f"""
insert into public.study_quality_assessment(
  study_id,assessment_key,assessment_kind,framework_key,framework_version,overall_judgement,
  assessment_status,notes,assessor,assessed_on,mapping_source,review_status
) values (
  {study_id},{lit(study['assessment_key'])},{lit(study['assessment_kind'])},{lit(study['framework_key'])},
  {lit(study.get('framework_version'))},{lit(study.get('overall_judgement'))},{lit(study['assessment_status'])},
  {lit(study.get('notes'))},null,null,'agent_candidate','proposed'
)
on conflict (study_id,assessment_key) do update set
  assessment_kind=excluded.assessment_kind,
  framework_key=excluded.framework_key,
  framework_version=excluded.framework_version,
  overall_judgement=excluded.overall_judgement,
  assessment_status=excluded.assessment_status,
  notes=excluded.notes,
  mapping_source='agent_candidate',
  review_status='proposed',
  updated_at=now()
where public.study_quality_assessment.mapping_source='agent_candidate'
  and public.study_quality_assessment.review_status='proposed';
""")
    for domain in study["domains"]:
        sql.append(study_domain_sql(study_id, study["assessment_key"], domain))

    for result, outcome_id, contrast_id in resolved_results:
        sql.append(f"""
update public.result_rob_status
set assessment_status='reviewed_complete',mapping_source='agent_candidate',review_status='proposed',
    notes={lit('Q1 rt-2026-001 candidate result-specific RoB 2 appraisal complete; human approval required.')},updated_at=now()
where outcome_id={outcome_id} and mapping_source in ('migration','agent_candidate') and review_status='proposed';
""")
        sql.append(f"""
insert into public.result_risk_of_bias_assessment(
  outcome_id,contrast_id,effect_estimate_id,assessment_key,framework_key,framework_version,
  estimand_or_result_scope,overall_judgement,assessment_status,notes,assessor,assessed_on,
  mapping_source,review_status
) values (
  {outcome_id},{lit(contrast_id)},null,{lit(result['assessment_key'])},{lit(result['framework_key'])},
  {lit(result.get('framework_version'))},{lit(result.get('estimand_or_result_scope'))},
  {lit(result.get('overall_judgement'))},{lit(result['assessment_status'])},{lit(result.get('notes'))},
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
  mapping_source='agent_candidate',
  review_status='proposed',
  updated_at=now()
where public.result_risk_of_bias_assessment.mapping_source='agent_candidate'
  and public.result_risk_of_bias_assessment.review_status='proposed';
""")
        for domain in result["domains"]:
            sql.append(result_domain_sql(outcome_id, result["assessment_key"], domain))

    sql.append("commit;")
    psql(args.container, "\n".join(sql))

    candidate_count = int(one(psql(args.container, f"""
select
  (select count(*) from public.study_quality_status where study_id={study_id} and mapping_source='agent_candidate' and review_status='proposed')
+ (select count(*) from public.result_rob_status r join public.evidence_outcome eo on eo.outcome_id=r.outcome_id where eo.study_id={study_id} and r.mapping_source='agent_candidate' and r.review_status='proposed')
+ (select count(*) from public.study_quality_assessment where study_id={study_id} and mapping_source='agent_candidate' and review_status='proposed')
+ (select count(*) from public.result_risk_of_bias_assessment a join public.evidence_outcome eo on eo.outcome_id=a.outcome_id where eo.study_id={study_id} and a.mapping_source='agent_candidate' and a.review_status='proposed')
+ (select count(*) from public.assessment_domain_judgement d join public.study_quality_assessment a on a.study_quality_assessment_id=d.study_quality_assessment_id where a.study_id={study_id} and d.mapping_source='agent_candidate' and d.review_status='proposed')
+ (select count(*) from public.assessment_domain_judgement d join public.result_risk_of_bias_assessment a on a.result_rob_assessment_id=d.result_rob_assessment_id join public.evidence_outcome eo on eo.outcome_id=a.outcome_id where eo.study_id={study_id} and d.mapping_source='agent_candidate' and d.review_status='proposed');
""", capture=True), "candidate count"))
    if candidate_count != 28:
        raise RuntimeError(f"Expected exactly 28 rt-2026-001 candidate review-surface rows; found {candidate_count}")

    historical_after = psql(args.container, """
select
 (select status from public.evidence_release where release_id='2026-08-23'),
 (select count(*) from public.release_source_version where release_id='2026-08-23'),
 (select count(*) from public.csi_gateway_evidence_card where evidence_release_id='2026-08-23'),
 (select count(*) from public.csi_gateway_claim where evidence_release_id='2026-08-23');
""", capture=True)
    if historical_before != historical_after:
        raise RuntimeError(f"Historical release/Gateway parity changed unexpectedly: {historical_before!r} -> {historical_after!r}")

    revision = psql(args.container, "select current_revision from public.scientific_state_revision where singleton=true;", capture=True)
    print("STAGE 12 Q1 RT001 QUALITY / ROB CANDIDATE APPLIED")
    print(f"source_id|{source_id}")
    print(f"study_id|{study_id}")
    print("result_assessments|3")
    print("study_assessments|1")
    print("domain_judgements|20")
    print("status_candidates|4")
    print(f"candidate_review_surface_rows|{candidate_count}")
    print(f"scientific_state_revision|{revision}")
    print("human_review_decisions_applied|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
