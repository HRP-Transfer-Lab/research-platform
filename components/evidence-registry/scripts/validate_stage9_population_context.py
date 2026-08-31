#!/usr/bin/env python3
"""Validate Stage 9 population/context architecture and conservative seed mappings locally."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage9_seed_mappings.v1.json"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd = ["docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|"]
    return run(cmd, input_text=sql, capture=True).stdout.strip()


def scalar(container: str, sql: str) -> int:
    value = psql(container, sql)
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"Expected integer SQL result; got {value!r}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"STAGE 9 POPULATION/CONTEXT INVALID: {message}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Stage 9 population/context architecture in local Supabase.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    require(running == "true", f"local database container {args.container!r} is not running")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    term_count = scalar(args.container, "select count(*) from public.population_context_term;")
    require(term_count == 28, f"expected 28 controlled population/context terms; got {term_count}")

    facet_counts = psql(args.container, """
select string_agg(facet_kind||':'||n::text, ',' order by facet_kind)
from (
  select facet_kind, count(*) n from public.population_context_term group by facet_kind
) x;
""")
    expected_facets = "baseline_cognitive_status:1,delivery_context:4,education_level:4,geography:1,health_condition_context:2,life_stage:4,role:4,study_setting:8"
    require(facet_counts == expected_facets, f"controlled facet inventory changed: {facet_counts!r}")

    study_count = scalar(args.container, "select count(*) from public.study;")
    component_count = scalar(args.container, "select count(*) from public.intervention_component;")
    require(study_count == 18, f"expected 18 seed studies; got {study_count}")
    require(component_count == 13, f"expected 13 seed components; got {component_count}")

    study_status = scalar(args.container, "select count(*) from public.study_population_context_status;")
    component_status = scalar(args.container, "select count(*) from public.component_delivery_context_status;")
    require(study_status == 18 * 7, f"expected 126 study facet status rows; got {study_status}")
    require(component_status == 13, f"expected 13 component delivery status rows; got {component_status}")

    expected_study_links = len(manifest["study_mappings"])
    expected_delivery_links = len(manifest["component_delivery_mappings"])
    actual_study_links = scalar(args.container, "select count(*) from public.study_population_context_term;")
    actual_delivery_links = scalar(args.container, "select count(*) from public.component_delivery_context_term;")
    require(actual_study_links == expected_study_links, f"expected {expected_study_links} study mappings; got {actual_study_links}")
    require(actual_delivery_links == expected_delivery_links, f"expected {expected_delivery_links} delivery mappings; got {actual_delivery_links}")

    facet_mismatch = scalar(args.container, """
select count(*)
from public.study_population_context_term spct
join public.population_context_term pct on pct.term_id=spct.term_id
where pct.facet_kind='delivery_context';
""")
    delivery_mismatch = scalar(args.container, """
select count(*)
from public.component_delivery_context_term cdct
join public.population_context_term pct on pct.term_id=cdct.term_id
where pct.facet_kind<>'delivery_context';
""")
    require(facet_mismatch == 0, f"delivery-context terms attached at study level={facet_mismatch}")
    require(delivery_mismatch == 0, f"non-delivery terms attached to components={delivery_mismatch}")

    candidate_status_consistency = scalar(args.container, """
select count(*)
from public.study_population_context_term x
join public.population_context_term t on t.term_id=x.term_id
join public.study_population_context_status s on s.study_id=x.study_id and s.facet_kind=t.facet_kind
where x.mapping_source='agent_candidate' and x.review_status='proposed'
  and not (s.extraction_status='candidate_mapped' and s.mapping_source='agent_candidate' and s.review_status='proposed');
""")
    require(candidate_status_consistency == 0, f"candidate study mappings without matching candidate_mapped status={candidate_status_consistency}")

    unmapped_status_bad = scalar(args.container, """
select count(*)
from public.study_population_context_status s
where not exists (
  select 1 from public.study_population_context_term x
  join public.population_context_term t on t.term_id=x.term_id
  where x.study_id=s.study_id and t.facet_kind=s.facet_kind
)
and s.review_status='proposed'
and s.extraction_status<>'not_yet_extracted';
""")
    require(unmapped_status_bad == 0, f"unmapped study facets not explicitly not_yet_extracted={unmapped_status_bad}")

    delivery_status_bad = scalar(args.container, """
select count(*)
from public.component_delivery_context_status s
where (
  exists (select 1 from public.component_delivery_context_term x where x.component_id=s.component_id)
  and s.extraction_status<>'candidate_mapped'
) or (
  not exists (select 1 from public.component_delivery_context_term x where x.component_id=s.component_id)
  and s.extraction_status<>'not_yet_extracted'
);
""")
    require(delivery_status_bad == 0, f"component delivery status/mapping inconsistency={delivery_status_bad}")

    agent_promoted = scalar(args.container, """
select
  (select count(*) from public.study_population_context_term where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.study_population_context_status where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.component_delivery_context_term where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.component_delivery_context_status where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.context_fit_assessment where mapping_source='agent_candidate' and review_status='approved');
""")
    require(agent_promoted == 0, f"Stage 9 agent candidates promoted={agent_promoted}")

    fit_count = scalar(args.container, "select count(*) from public.context_fit_assessment;")
    require(fit_count == 0, f"immutable seed must not contain context-fit judgements; got {fit_count}")

    stage3_app = psql(args.container, """
select
  (select count(*) from public.source_version_application_family),
  (select count(distinct source_version_id) from public.source_version_application_family),
  (select count(distinct application_family) from public.source_version_application_family);
""")
    require(stage3_app == "32|18|7", f"Stage 3 application-family lens changed: {stage3_app!r}")

    rt004 = psql(args.container, """
select string_agg(t.term_id,',' order by t.term_id)
from public.study_population_context_term x
join public.population_context_term t on t.term_id=x.term_id
join public.study s on s.study_id=x.study_id
where s.source_id='rt-2026-004' and t.facet_kind in ('life_stage','role','health_condition_context','education_level');
""")
    require(rt004 == "pc_edu_higher,pc_health_healthy_nonclinical,pc_life_young_adult,pc_role_university_student", f"rt-2026-004 orthogonal facets changed: {rt004!r}")

    rt005 = psql(args.container, """
select string_agg(t.term_id||':'||x.relationship,',' order by t.term_id)
from public.study_population_context_term x
join public.population_context_term t on t.term_id=x.term_id
join public.study s on s.study_id=x.study_id
where s.source_id='rt-2026-005' and t.facet_kind='life_stage';
""")
    require(rt005 == "pc_life_older_adult:includes_subgroup,pc_life_young_adult:includes_subgroup", f"rt-2026-005 subgroup preservation changed: {rt005!r}")

    geography = psql(args.container, """
select s.source_id||'|'||t.term_id||'|'||x.relationship
from public.study_population_context_term x
join public.population_context_term t on t.term_id=x.term_id
join public.study s on s.study_id=x.study_id
where t.facet_kind='geography';
""")
    require(geography == "rt-2026-015|pc_geo_china|entire_sample", f"geography non-inference boundary changed: {geography!r}")

    triggers = scalar(args.container, """
select count(*) from pg_trigger
where not tgisinternal and tgname in (
  'ensure_stage9_study_status','ensure_stage9_component_delivery_status',
  'validate_stage9_study_term_facet','validate_stage9_component_delivery_term',
  'prevent_stage9_agent_study_term_approval','prevent_stage9_agent_study_status_approval',
  'prevent_stage9_agent_component_term_approval','prevent_stage9_agent_component_status_approval',
  'prevent_stage9_agent_context_fit_approval'
);
""")
    require(triggers == 9, f"expected 9 Stage 9 status/integrity/human-gate triggers; got {triggers}")

    print(
        "STAGE 9 POPULATION/CONTEXT VALID: "
        f"terms={term_count}; studies={study_count}; study_status_rows={study_status}; "
        f"study_links={actual_study_links}; components={component_count}; delivery_links={actual_delivery_links}; context_fit=0"
    )
    print("orthogonal_population_facets: PASS")
    print("explicit_missingness_status: PASS")
    print("mixed_sample_subgroup_preservation: PASS")
    print("study_setting_vs_delivery_context: PASS")
    print("geography_noninference: PASS")
    print("application_family_separation: PASS (32 links / 18 sources / 7 families unchanged)")
    print("context_fit_nonfabrication: PASS")
    print("human_approval_boundary: PASS (0 agent candidates promoted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
