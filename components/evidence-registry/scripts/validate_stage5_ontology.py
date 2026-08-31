#!/usr/bin/env python3
"""Validate Stage 5 study-arm/component/contrast architecture in local Supabase."""
from __future__ import annotations

import argparse
import subprocess


def run_psql(container: str, sql: str) -> str:
    proc = subprocess.run(
        ["docker", "exec", "-i", container, "psql", "-U", "postgres", "-d", "postgres", "-At", "-F", "|", "-c", sql],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout.strip()


def scalar(container: str, sql: str) -> int:
    value = run_psql(container, sql).strip()
    return int(value or "0")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--container", default="supabase_db_research-platform")
    ap.add_argument("--release", default="2026-08-23")
    args = ap.parse_args()

    release = args.release.replace("'", "''")

    counts = run_psql(args.container, f"""
select
  (select count(*) from public.study s join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}'),
  (select count(*) from public.study_stage5_status ss join public.study s on s.study_id=ss.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}'),
  (select count(*) from public.study_arm a join public.study s on s.study_id=a.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}'),
  (select count(*) from public.arm_component ac join public.study_arm a on a.arm_id=ac.arm_id join public.study s on s.study_id=a.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}'),
  (select count(*) from public.study_contrast c join public.study s on s.study_id=c.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}'),
  (select count(*) from public.contrast_arm_member cam join public.study_contrast c on c.contrast_id=cam.contrast_id join public.study s on s.study_id=c.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}');
""")

    expected = "18|18|29|18|8|16"
    if counts != expected:
        raise SystemExit(f"Stage 5 count mismatch: expected {expected}, got {counts}")

    checks = {
        "studies_without_status": f"""
select count(*) from public.study s
join public.evidence_source es on es.source_id=s.source_id
left join public.study_stage5_status ss on ss.study_id=s.study_id
where es.release_id='{release}' and ss.study_id is null;
""",
        "orphan_arm_components": """
select count(*) from public.arm_component ac
left join public.study_arm a on a.arm_id=ac.arm_id
left join public.intervention_component ic on ic.component_id=ac.component_id
where a.arm_id is null or ic.component_id is null;
""",
        "cross_study_arm_components": """
select count(*) from public.arm_component ac
join public.study_arm a on a.arm_id=ac.arm_id
join public.intervention_component ic on ic.component_id=ac.component_id
where a.study_id <> ic.study_id;
""",
        "orphan_contrast_members": """
select count(*) from public.contrast_arm_member cam
left join public.study_contrast c on c.contrast_id=cam.contrast_id
left join public.study_arm a on a.arm_id=cam.arm_id
where c.contrast_id is null or a.arm_id is null;
""",
        "cross_study_contrast_members": """
select count(*) from public.contrast_arm_member cam
join public.study_contrast c on c.contrast_id=cam.contrast_id
join public.study_arm a on a.arm_id=cam.arm_id
where c.study_id <> a.study_id;
""",
        "contrasts_without_two_sides": """
select count(*) from (
  select c.contrast_id,
    bool_or(cam.contrast_side='focal') as has_focal,
    bool_or(cam.contrast_side='comparator') as has_comparator
  from public.study_contrast c
  left join public.contrast_arm_member cam on cam.contrast_id=c.contrast_id
  group by c.contrast_id
) q where not coalesce(has_focal,false) or not coalesce(has_comparator,false);
""",
        "agent_candidates_approved": """
select
  (select count(*) from public.study_arm where mapping_source='agent_candidate' and review_status='approved') +
  (select count(*) from public.arm_component where mapping_source='agent_candidate' and review_status='approved') +
  (select count(*) from public.study_contrast where mapping_source='agent_candidate' and review_status='approved') +
  (select count(*) from public.contrast_arm_member where mapping_source='agent_candidate' and review_status='approved') +
  (select count(*) from public.study_stage5_status where arm_mapping_source='agent_candidate' and arm_review_status='approved') +
  (select count(*) from public.study_stage5_status where contrast_mapping_source='agent_candidate' and contrast_review_status='approved');
""",
    }

    failures = []
    for label, sql in checks.items():
        value = scalar(args.container, sql)
        if value != 0:
            failures.append((label, value))

    explicit_status = run_psql(args.container, f"""
select
  count(*) filter (where ss.arm_extraction_status='partially_extracted'),
  count(*) filter (where ss.arm_extraction_status='not_yet_extracted'),
  count(*) filter (where ss.arm_extraction_status='not_applicable'),
  count(*) filter (where ss.contrast_extraction_status='partially_extracted'),
  count(*) filter (where ss.contrast_extraction_status='not_yet_extracted'),
  count(*) filter (where ss.contrast_extraction_status='not_applicable')
from public.study_stage5_status ss
join public.study s on s.study_id=ss.study_id
join public.evidence_source es on es.source_id=s.source_id
where es.release_id='{release}';
""")
    if explicit_status != "10|4|4|6|8|4":
        failures.append(("explicit_status_distribution", explicit_status))

    reused_components = scalar(args.container, """
select count(*) from (
  select ac.component_id
  from public.arm_component ac
  group by ac.component_id
  having count(distinct ac.arm_id) > 1
) q;
""")
    multi_component_arms = scalar(args.container, """
select count(*) from (
  select ac.arm_id
  from public.arm_component ac
  group by ac.arm_id
  having count(distinct ac.component_id) > 1
) q;
""")

    if reused_components < 1:
        failures.append(("component_reuse_across_arms", reused_components))
    if multi_component_arms < 1:
        failures.append(("multi_component_arm_support", multi_component_arms))

    if failures:
        for label, value in failures:
            print(f"FAIL {label}: {value}")
        raise SystemExit("Stage 5 ontology validation failed.")

    print("STAGE 5 STUDY-ARM ARCHITECTURE VALID: studies=18; status_rows=18; arms=29; component_links=18; contrasts=8; contrast_members=16")
    print("status_distribution: arms(partial=10/not_yet=4/not_applicable=4); contrasts(partial=6/not_yet=8/not_applicable=4)")
    print(f"factorial_component_reuse: PASS (reused_components={reused_components}; multi_component_arms={multi_component_arms})")
    print("arm_component_integrity: PASS")
    print("contrast_membership_integrity: PASS")
    print("human_approval_boundary: PASS (0 agent candidates promoted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
