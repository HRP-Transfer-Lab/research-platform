#!/usr/bin/env python3
"""Validate Stage 6 first-class quantitative effect architecture locally.

Read-only. Confirms per-outcome extraction state, first-class effect counts,
contrast/arm study integrity, historical effect conservation, and the human
approval boundary for the 2026-08-23 seed release.
"""
from __future__ import annotations

import argparse
import subprocess

DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_RELEASE = "2026-08-23"


def run_psql(container: str, sql: str) -> str:
    proc = subprocess.run(
        ["docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres", "-At", "-F", "|", "-c", sql],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout.strip()


def scalar(container: str, sql: str) -> int:
    value = run_psql(container, sql).strip()
    return int(value or 0)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Stage 6 quantitative effect architecture in local Supabase.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--release", default=DEFAULT_RELEASE)
    args = ap.parse_args()
    release = args.release.replace("'", "''")

    counts = run_psql(args.container, f"""
select
  (select count(*) from public.evidence_outcome eo join public.study s on s.study_id=eo.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}'),
  (select count(*) from public.outcome_stage6_status os join public.evidence_outcome eo on eo.outcome_id=os.outcome_id join public.study s on s.study_id=eo.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}'),
  (select count(*) from public.effect_estimate ee join public.evidence_outcome eo on eo.outcome_id=ee.outcome_id join public.study s on s.study_id=eo.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}'),
  (select count(*) from public.arm_outcome_summary aos join public.evidence_outcome eo on eo.outcome_id=aos.outcome_id join public.study s on s.study_id=eo.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}');
""")
    if counts != "38|38|1|0":
        raise SystemExit(f"Stage 6 count mismatch: expected 38|38|1|0, got {counts}")

    status_dist = run_psql(args.container, f"""
select
  count(*) filter (where os.quantitative_extraction_status='partially_extracted'),
  count(*) filter (where os.quantitative_extraction_status='not_yet_extracted'),
  count(*) filter (where os.quantitative_extraction_status not in ('partially_extracted','not_yet_extracted'))
from public.outcome_stage6_status os
join public.evidence_outcome eo on eo.outcome_id=os.outcome_id
join public.study s on s.study_id=eo.study_id
join public.evidence_source es on es.source_id=s.source_id
where es.release_id='{release}';
""")
    if status_dist != "1|37|0":
        raise SystemExit(f"Unexpected Stage 6 status distribution: {status_dist}")

    scope_dist = run_psql(args.container, f"""
select
  count(*) filter (where ee.estimate_scope='source_level_synthesis'),
  count(*) filter (where ee.estimate_scope='study_contrast'),
  count(*) filter (where ee.estimate_scope not in ('source_level_synthesis','study_contrast'))
from public.effect_estimate ee
join public.evidence_outcome eo on eo.outcome_id=ee.outcome_id
join public.study s on s.study_id=eo.study_id
join public.evidence_source es on es.source_id=s.source_id
where es.release_id='{release}';
""")
    if scope_dist != "1|0|0":
        raise SystemExit(f"Unexpected Stage 6 estimate-scope distribution: {scope_dist}")

    bad_scope = scalar(args.container, """
select count(*) from public.effect_estimate
where (estimate_scope='study_contrast' and contrast_id is null)
   or (estimate_scope<>'study_contrast' and contrast_id is not null);
""")
    if bad_scope:
        raise SystemExit(f"Found {bad_scope} invalid estimate-scope/contrast combinations.")

    cross_study_effect = scalar(args.container, """
select count(*)
from public.effect_estimate ee
join public.evidence_outcome eo on eo.outcome_id=ee.outcome_id
join public.study_contrast sc on sc.contrast_id=ee.contrast_id
where ee.contrast_id is not null and eo.study_id <> sc.study_id;
""")
    if cross_study_effect:
        raise SystemExit(f"Found {cross_study_effect} cross-study contrast/outcome effect links.")

    cross_study_summary = scalar(args.container, """
select count(*)
from public.arm_outcome_summary aos
join public.evidence_outcome eo on eo.outcome_id=aos.outcome_id
join public.study_arm sa on sa.arm_id=aos.arm_id
where eo.study_id <> sa.study_id;
""")
    if cross_study_summary:
        raise SystemExit(f"Found {cross_study_summary} cross-study arm/outcome summary links.")

    invalid_ci = scalar(args.container, """
select count(*) from public.effect_estimate
where ci_lower is not null and ci_upper is not null and ci_lower > ci_upper;
""")
    if invalid_ci:
        raise SystemExit(f"Found {invalid_ci} effect estimates with impossible CI ordering.")

    legacy_rows = run_psql(args.container, f"""
select count(*)
from public.evidence_outcome eo
join public.study s on s.study_id=eo.study_id
join public.evidence_source es on es.source_id=s.source_id
where es.release_id='{release}'
  and (eo.effect_metric is not null or eo.effect_estimate is not null or eo.ci_lower is not null or eo.ci_upper is not null);
""")
    if legacy_rows != "1":
        raise SystemExit(f"Expected exactly one historical quantitative compatibility row; found {legacy_rows}")

    conservation = run_psql(args.container, f"""
select
  es.source_id,
  eo.outcome_name,
  eo.effect_metric,
  eo.effect_estimate,
  eo.ci_lower,
  eo.ci_upper,
  ee.estimate_scope,
  ee.estimate_type,
  ee.metric,
  ee.estimate_value,
  ee.ci_level,
  ee.ci_lower,
  ee.ci_upper,
  ee.contrast_id
from public.evidence_outcome eo
join public.study s on s.study_id=eo.study_id
join public.evidence_source es on es.source_id=s.source_id
join public.effect_estimate ee on ee.outcome_id=eo.outcome_id
where es.release_id='{release}'
  and eo.effect_estimate is not null;
""")
    expected = "rt-2026-007|overall post-training working memory|Hedges_g|0.191|0.062|0.32|source_level_synthesis|standardised_mean_difference|Hedges_g|0.191||0.062|0.32|"
    if conservation != expected:
        raise SystemExit(f"Historical quantitative conservation failed:\n{conservation}")

    fabricated = scalar(args.container, f"""
select count(*)
from public.effect_estimate ee
join public.evidence_outcome eo on eo.outcome_id=ee.outcome_id
join public.study s on s.study_id=eo.study_id
join public.evidence_source es on es.source_id=s.source_id
where es.release_id='{release}'
  and (ee.standard_error is not null or ee.ci_level is not null or ee.p_value is not null or ee.n_analysed is not null);
""")
    if fabricated:
        raise SystemExit(f"Found {fabricated} seed effect rows with quantitative fields not supported by the seed manifest.")

    promoted = scalar(args.container, f"""
select
  (select count(*) from public.outcome_stage6_status os join public.evidence_outcome eo on eo.outcome_id=os.outcome_id join public.study s on s.study_id=eo.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}' and os.mapping_source='agent_candidate' and os.review_status='approved')
+ (select count(*) from public.effect_estimate ee join public.evidence_outcome eo on eo.outcome_id=ee.outcome_id join public.study s on s.study_id=eo.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}' and ee.mapping_source='agent_candidate' and ee.review_status='approved')
+ (select count(*) from public.arm_outcome_summary aos join public.evidence_outcome eo on eo.outcome_id=aos.outcome_id join public.study s on s.study_id=eo.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}' and aos.mapping_source='agent_candidate' and aos.review_status='approved');
""")
    if promoted:
        raise SystemExit(f"Human approval boundary failed: {promoted} agent candidates are approved.")

    print("STAGE 6 EFFECT ARCHITECTURE VALID: outcomes=38; status_rows=38; effects=1; arm_summaries=0")
    print("status_distribution: partially_extracted=1; not_yet_extracted=37")
    print("estimate_scope_integrity: PASS (source_level_synthesis=1; study_contrast=0)")
    print("cross_study_link_integrity: PASS")
    print("legacy_effect_conservation: PASS (Hedges_g=0.191; CI=0.062..0.32; CI level remains unknown)")
    print("no_fabricated_quantitative_fields: PASS")
    print("human_approval_boundary: PASS (0 agent candidates promoted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
