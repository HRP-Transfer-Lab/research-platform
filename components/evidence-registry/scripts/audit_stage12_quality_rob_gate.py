#!/usr/bin/env python3
"""Read-only strict Stage 12 quality/RoB completion gate.

Release-ready means every normalized study/result has a human-reviewed terminal
assessment state. A reviewed_complete subject must have at least one approved,
reviewed-complete assessment with at least one approved domain judgement.
An explicit not_applicable state requires human authority and a rationale.
"""
from __future__ import annotations

import argparse
import subprocess

DEFAULT_CONTAINER = "supabase_db_research-platform"
TERMINAL = ("reviewed_complete", "not_applicable")


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=False, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|",
    ]
    result = run(cmd, input_text=sql, capture=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def scalar(container: str, sql: str) -> int:
    return int(psql(container, sql) or "0")


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit strict Stage 12 quality/RoB release readiness without mutation.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    print("=== STAGE 12 QUALITY / ROB STRICT GATE ===")
    print("study_quality_status|count")
    print(psql(args.container, "select assessment_status,count(*) from public.study_quality_status group by assessment_status order by assessment_status;"))
    print("result_rob_status|count")
    print(psql(args.container, "select assessment_status,count(*) from public.result_rob_status group by assessment_status order by assessment_status;"))
    print("assessment_counts|study_quality|result_rob|domains")
    print(psql(args.container, """
select
 (select count(*) from public.study_quality_assessment),
 (select count(*) from public.result_risk_of_bias_assessment),
 (select count(*) from public.assessment_domain_judgement);
"""))

    study_open = scalar(args.container, "select count(*) from public.study_quality_status where assessment_status not in ('reviewed_complete','not_applicable');")
    result_open = scalar(args.container, "select count(*) from public.result_rob_status where assessment_status not in ('reviewed_complete','not_applicable');")

    closed_study_without_human_authority = scalar(args.container, """
select count(*) from public.study_quality_status
where assessment_status in ('reviewed_complete','not_applicable')
  and not (mapping_source in ('human_review','manual') and review_status='approved');
""")
    closed_result_without_human_authority = scalar(args.container, """
select count(*) from public.result_rob_status
where assessment_status in ('reviewed_complete','not_applicable')
  and not (mapping_source in ('human_review','manual') and review_status='approved');
""")

    study_complete_without_assessment = scalar(args.container, """
select count(*)
from public.study_quality_status s
where s.assessment_status='reviewed_complete'
  and not exists (
    select 1 from public.study_quality_assessment a
    where a.study_id=s.study_id
      and a.assessment_status='reviewed_complete'
      and a.mapping_source in ('human_review','manual')
      and a.review_status='approved'
  );
""")
    result_complete_without_assessment = scalar(args.container, """
select count(*)
from public.result_rob_status s
where s.assessment_status='reviewed_complete'
  and not exists (
    select 1 from public.result_risk_of_bias_assessment a
    where a.outcome_id=s.outcome_id
      and a.assessment_status='reviewed_complete'
      and a.mapping_source in ('human_review','manual')
      and a.review_status='approved'
  );
""")

    completed_study_assessment_without_domain = scalar(args.container, """
select count(*)
from public.study_quality_assessment a
where a.assessment_status='reviewed_complete'
  and a.mapping_source in ('human_review','manual') and a.review_status='approved'
  and not exists (
    select 1 from public.assessment_domain_judgement d
    where d.study_quality_assessment_id=a.study_quality_assessment_id
      and d.mapping_source in ('human_review','manual') and d.review_status='approved'
  );
""")
    completed_result_assessment_without_domain = scalar(args.container, """
select count(*)
from public.result_risk_of_bias_assessment a
where a.assessment_status='reviewed_complete'
  and a.mapping_source in ('human_review','manual') and a.review_status='approved'
  and not exists (
    select 1 from public.assessment_domain_judgement d
    where d.result_rob_assessment_id=a.result_rob_assessment_id
      and d.mapping_source in ('human_review','manual') and d.review_status='approved'
  );
""")

    study_na_without_rationale = scalar(args.container, """
select count(*) from public.study_quality_status
where assessment_status='not_applicable'
  and (notes is null or btrim(notes)='');
""")
    result_na_without_rationale = scalar(args.container, """
select count(*) from public.result_rob_status
where assessment_status='not_applicable'
  and (notes is null or btrim(notes)='');
""")

    print("gate_metric|count")
    metrics = [
        ("study_status_nonterminal", study_open),
        ("result_status_nonterminal", result_open),
        ("closed_study_status_without_human_authority", closed_study_without_human_authority),
        ("closed_result_status_without_human_authority", closed_result_without_human_authority),
        ("reviewed_complete_study_without_approved_assessment", study_complete_without_assessment),
        ("reviewed_complete_result_without_approved_assessment", result_complete_without_assessment),
        ("completed_study_assessment_without_approved_domain", completed_study_assessment_without_domain),
        ("completed_result_assessment_without_approved_domain", completed_result_assessment_without_domain),
        ("study_not_applicable_without_rationale", study_na_without_rationale),
        ("result_not_applicable_without_rationale", result_na_without_rationale),
    ]
    for name, value in metrics:
        print(f"{name}|{value}")

    failures = [(name, value) for name, value in metrics if value]
    if failures:
        print("STAGE 12 QUALITY / ROB STRICT GATE|OPEN")
        return 2

    print("STAGE 12 QUALITY / ROB STRICT GATE|PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
