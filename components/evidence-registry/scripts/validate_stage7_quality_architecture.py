#!/usr/bin/env python3
"""Validate Stage 7 typed quality and result-risk-of-bias architecture locally."""
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
        raise SystemExit(f"STAGE 7 QUALITY ARCHITECTURE INVALID: {message}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Stage 7 quality/RoB architecture in local Supabase.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    require(running == "true", f"local database container {args.container!r} is not running")

    frameworks = scalar(args.container, "select count(*) from public.assessment_framework_definition;")
    studies = scalar(args.container, "select count(*) from public.study;")
    study_status = scalar(args.container, "select count(*) from public.study_quality_status;")
    outcomes = scalar(args.container, "select count(*) from public.evidence_outcome;")
    result_status = scalar(args.container, "select count(*) from public.result_rob_status;")
    study_assessments = scalar(args.container, "select count(*) from public.study_quality_assessment;")
    result_assessments = scalar(args.container, "select count(*) from public.result_risk_of_bias_assessment;")
    domains = scalar(args.container, "select count(*) from public.assessment_domain_judgement;")
    legacy_quality = scalar(args.container, "select count(*) from public.quality_assessment;")

    require(frameworks == 10, f"expected 10 registered framework definitions; got {frameworks}")
    require(studies == 18 and study_status == 18, f"expected 18 studies/status rows; got {studies}/{study_status}")
    require(outcomes == 38 and result_status == 38, f"expected 38 outcomes/result-status rows; got {outcomes}/{result_status}")
    require(study_assessments == 0, f"seed should have 0 study-quality assessment judgements; got {study_assessments}")
    require(result_assessments == 0, f"seed should have 0 result-RoB assessment judgements; got {result_assessments}")
    require(domains == 0, f"seed should have 0 domain judgements; got {domains}")
    require(legacy_quality == 0, f"historical seed expected 0 compatibility quality rows; got {legacy_quality}")

    non_default_study_status = scalar(args.container, "select count(*) from public.study_quality_status where assessment_status <> 'not_yet_assessed';")
    non_default_result_status = scalar(args.container, "select count(*) from public.result_rob_status where assessment_status <> 'not_yet_assessed';")
    require(non_default_study_status == 0, f"seed study-quality status must remain not_yet_assessed; non-default={non_default_study_status}")
    require(non_default_result_status == 0, f"seed result-RoB status must remain not_yet_assessed; non-default={non_default_result_status}")

    grade_definition = psql(args.container, "select framework_key||'|'||subject_kind from public.assessment_framework_definition where framework_key='grade';")
    require(grade_definition == "grade|body_certainty_reserved", f"GRADE registry boundary invalid: {grade_definition!r}")
    result_frameworks = psql(args.container, "select string_agg(framework_key, ',' order by framework_key) from public.assessment_framework_definition where subject_kind='result_risk_of_bias';")
    require(result_frameworks == "rob2,robins_i", f"unexpected built-in result-RoB frameworks: {result_frameworks!r}")

    grade_attachments = scalar(args.container, """
select
  (select count(*) from public.study_quality_assessment where framework_key='grade')
+ (select count(*) from public.result_risk_of_bias_assessment where framework_key='grade');
""")
    require(grade_attachments == 0, f"GRADE must not attach to study/result subjects; got {grade_attachments}")

    invalid_study_framework = scalar(args.container, """
select count(*)
from public.study_quality_assessment sqa
join public.assessment_framework_definition afd using (framework_key)
where afd.subject_kind in ('result_risk_of_bias','component_reporting_or_fidelity','body_certainty_reserved')
   or (sqa.assessment_kind='methodological_quality' and afd.subject_kind not in ('study_methodological_quality','custom'))
   or (sqa.assessment_kind='reporting_completeness' and afd.subject_kind not in ('study_reporting_completeness','custom'))
   or (sqa.assessment_kind='review_methodology' and afd.subject_kind not in ('study_review_methodology','custom'))
   or (sqa.assessment_kind='measurement_quality' and afd.subject_kind not in ('study_measurement_quality','custom'))
   or (sqa.assessment_kind='other' and afd.subject_kind <> 'custom');
""")
    require(invalid_study_framework == 0, f"invalid study/framework links={invalid_study_framework}")

    invalid_result_framework = scalar(args.container, """
select count(*)
from public.result_risk_of_bias_assessment rra
join public.assessment_framework_definition afd using (framework_key)
where afd.subject_kind not in ('result_risk_of_bias','custom');
""")
    require(invalid_result_framework == 0, f"invalid result/framework links={invalid_result_framework}")

    cross_study = scalar(args.container, """
select count(*)
from public.result_risk_of_bias_assessment rra
join public.evidence_outcome eo on eo.outcome_id=rra.outcome_id
join public.study_contrast sc on sc.contrast_id=rra.contrast_id
where rra.contrast_id is not null and eo.study_id <> sc.study_id;
""")
    require(cross_study == 0, f"cross-study outcome/contrast RoB links={cross_study}")

    effect_mismatch = scalar(args.container, """
select count(*)
from public.result_risk_of_bias_assessment rra
join public.effect_estimate ee on ee.effect_estimate_id=rra.effect_estimate_id
where rra.effect_estimate_id is not null
  and (
    ee.outcome_id <> rra.outcome_id
    or (rra.contrast_id is not null and ee.contrast_id is distinct from rra.contrast_id)
    or ee.estimate_scope='source_level_synthesis'
  );
""")
    require(effect_mismatch == 0, f"cross-outcome/contrast or synthesis-effect RoB links={effect_mismatch}")

    invalid_domain_subjects = scalar(args.container, """
select count(*) from public.assessment_domain_judgement
where (study_quality_assessment_id is null) = (result_rob_assessment_id is null);
""")
    require(invalid_domain_subjects == 0, f"domain rows without exactly one typed assessment subject={invalid_domain_subjects}")

    promoted = scalar(args.container, """
select
  (select count(*) from public.study_quality_assessment where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.result_risk_of_bias_assessment where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.assessment_domain_judgement where mapping_source='agent_candidate' and review_status='approved');
""")
    require(promoted == 0, f"agent candidates promoted={promoted}")

    trigger_count = scalar(args.container, """
select count(*)
from pg_trigger
where not tgisinternal
  and tgname in (
    'validate_stage7_study_quality_framework',
    'validate_stage7_result_rob_link',
    'ensure_stage7_study_quality_status',
    'ensure_stage7_result_rob_status'
  );
""")
    require(trigger_count == 4, f"expected 4 Stage 7 integrity/status triggers; got {trigger_count}")

    print(f"STAGE 7 QUALITY ARCHITECTURE VALID: frameworks={frameworks}; studies={studies}; study_status_rows={study_status}; results={outcomes}; result_status_rows={result_status}")
    print(f"assessment_counts: study_quality={study_assessments}; result_rob={result_assessments}; domains={domains}; legacy_quality={legacy_quality}")
    print("status_only_seed_boundary: PASS (18 studies + 38 results all not_yet_assessed)")
    print("framework_subject_integrity: PASS (RoB 2/ROBINS-I=result-level; GRADE=body-certainty reserved)")
    print("cross_subject_link_integrity: PASS")
    print("grade_attachment_boundary: PASS (0 source/study/result GRADE assessments)")
    print("no_fabricated_quality_or_rob_judgements: PASS")
    print("human_approval_boundary: PASS (0 agent candidates promoted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
