#!/usr/bin/env python3
"""Validate Stage 8 proposition/synthesis/body-certainty/body-EML architecture locally."""
from __future__ import annotations

import argparse
import subprocess

DEFAULT_CONTAINER = "supabase_db_research-platform"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|",
    ]
    return run(cmd, input_text=sql, capture=True).stdout.strip()


def scalar(container: str, sql: str) -> int:
    value = psql(container, sql)
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"Expected integer SQL result; got {value!r}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"STAGE 8 BODY EVIDENCE ARCHITECTURE INVALID: {message}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Stage 8 body evidence architecture in local Supabase.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    require(running == "true", f"local database container {args.container!r} is not running")

    status = psql(args.container, "select scope_key||'|'||curation_status||'|'||mapping_source||'|'||review_status from public.body_evidence_stage8_status order by scope_key;")
    require(status == "seed_body_curation|not_yet_curated|migration|proposed", f"unexpected Stage 8 curation status: {status!r}")

    counts = psql(args.container, """
select
  (select count(*) from public.evidence_proposition),
  (select count(*) from public.proposition_evidence_contribution),
  (select count(*) from public.body_evidence_synthesis),
  (select count(*) from public.synthesis_outcome),
  (select count(*) from public.body_certainty_assessment),
  (select count(*) from public.body_maturity_assessment),
  (select count(*) from public.body_approved_claim);
""")
    require(counts == "0|0|0|0|0|0|0", f"immutable seed must have zero typed body objects; got {counts}")

    legacy = psql(args.container, """
select
  (select count(*) from public.evidence_synthesis),
  (select count(*) from public.synthesis_source),
  (select count(*) from public.approved_claim);
""")
    require(legacy == "0|0|0", f"legacy body tables changed unexpectedly: {legacy}")

    source_eml = scalar(args.container, "select count(*) from public.evidence_maturity_assessment where scope='record_contribution' and source_id is not null;")
    legacy_body_eml = scalar(args.container, "select count(*) from public.evidence_maturity_assessment where scope='body_of_evidence' or synthesis_id is not null or claim_id is not null;")
    require(source_eml == 18, f"expected 18 source record-contribution EML rows; got {source_eml}")
    require(legacy_body_eml == 0, f"legacy body/synthesis/claim EML must remain zero; got {legacy_body_eml}")

    eml_distribution = psql(args.container, """
select string_agg(maturity_level::text||':'||n::text, ',' order by maturity_level)
from (
  select maturity_level, count(*) n
  from public.evidence_maturity_assessment
  where scope='record_contribution' and source_id is not null
  group by maturity_level
) x;
""")
    require(eml_distribution == "1:7,2:10,4:1", f"source EML distribution changed: {eml_distribution!r}")

    pooled = psql(args.container, """
select s.source_id||'|'||eo.outcome_name||'|'||ee.estimate_scope||'|'||ee.estimate_type||'|'||ee.metric||'|'||ee.estimate_value::text||'|'||ee.ci_lower::text||'|'||ee.ci_upper::text||'|'||coalesce(ee.contrast_id::text,'NULL')
from public.effect_estimate ee
join public.evidence_outcome eo on eo.outcome_id=ee.outcome_id
join public.study s on s.study_id=eo.study_id
where ee.estimate_scope='source_level_synthesis';
""")
    require(pooled == "rt-2026-007|overall post-training working memory|source_level_synthesis|standardised_mean_difference|Hedges_g|0.191|0.062|0.32|NULL", f"source-level pooled effect changed: {pooled!r}")

    grade_definition = psql(args.container, "select framework_key||'|'||subject_kind from public.assessment_framework_definition where framework_key='grade';")
    require(grade_definition == "grade|body_certainty_reserved", f"GRADE framework boundary changed: {grade_definition!r}")

    wrong_grade = scalar(args.container, """
select
  (select count(*) from public.quality_assessment where lower(tool)='grade')
+ (select count(*) from public.study_quality_assessment where framework_key='grade')
+ (select count(*) from public.result_risk_of_bias_assessment where framework_key='grade');
""")
    require(wrong_grade == 0, f"GRADE attached to source/study/result subjects={wrong_grade}")

    privileges = psql(args.container, """
select string_agg(
  table_name||':'||
  (case when has_table_privilege('authenticated','public.'||table_name,'SELECT') then 'S' else '-' end)||
  (case when has_table_privilege('authenticated','public.'||table_name,'INSERT') then 'I' else '-' end)||
  (case when has_table_privilege('authenticated','public.'||table_name,'UPDATE') then 'U' else '-' end)||
  (case when has_table_privilege('authenticated','public.'||table_name,'DELETE') then 'D' else '-' end),
  ',' order by table_name
)
from (values ('approved_claim'),('evidence_synthesis'),('synthesis_source')) v(table_name);
""")
    expected_privileges = "approved_claim:S---,evidence_synthesis:S---,synthesis_source:S---"
    require(privileges == expected_privileges, f"legacy body compatibility privileges invalid: {privileges!r}")

    agent_promoted = scalar(args.container, """
select
  (select count(*) from public.evidence_proposition where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.proposition_evidence_contribution where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.body_evidence_synthesis where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.synthesis_outcome where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.body_certainty_assessment where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.body_maturity_assessment where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.body_approved_claim where mapping_source='agent_candidate' and review_status='approved');
""")
    require(agent_promoted == 0, f"Stage 8 agent candidates promoted={agent_promoted}")

    integrity_triggers = scalar(args.container, """
select count(*) from pg_trigger
where not tgisinternal
  and tgname in (
    'validate_stage8_contribution_link',
    'validate_stage8_synthesis_outcome',
    'validate_stage8_body_certainty',
    'validate_stage8_body_maturity',
    'validate_stage8_body_claim',
    'prevent_stage8_agent_proposition_approval',
    'prevent_stage8_agent_contribution_approval',
    'prevent_stage8_agent_synthesis_approval',
    'prevent_stage8_agent_outcome_approval',
    'prevent_stage8_agent_certainty_approval',
    'prevent_stage8_agent_maturity_approval',
    'prevent_stage8_agent_claim_approval'
  );
""")
    require(integrity_triggers == 12, f"expected 12 Stage 8 integrity/human-gate triggers; got {integrity_triggers}")

    maturity_constraint = scalar(args.container, """
select count(*) from pg_constraint
where conrelid='public.body_maturity_assessment'::regclass
  and conname='body_maturity_approved_review_check';
""")
    require(maturity_constraint == 1, "approved body maturity/review consistency constraint missing")

    print("STAGE 8 BODY EVIDENCE ARCHITECTURE VALID: propositions=0; contributions=0; body_syntheses=0; synthesis_outcomes=0; body_certainty=0; body_eml=0; body_claims=0")
    print("body_curation_status: PASS (not_yet_curated)")
    print("legacy_body_compatibility: PASS (0 rows; authenticated read-only)")
    print("source_eml_boundary: PASS (18 record-contribution rows; distribution 1:7 / 2:10 / 4:1; 0 legacy body EML)")
    print("source_level_synthesis_effect_boundary: PASS (Hedges_g=0.191; CI=0.062..0.32; no contrast)")
    print("grade_subject_boundary: PASS (GRADE reserved for synthesis_outcome body certainty)")
    print("body_eml_subject_and_replication_guards: PASS")
    print("claim_approval_boundary: PASS")
    print("human_approval_boundary: PASS (0 agent candidates promoted)")
    print("no_fabricated_body_objects_or_judgements: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
