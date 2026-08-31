#!/usr/bin/env python3
"""Read-only audit of current population/context signals before Stage 9 normalization."""
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Stage 9 population/context source fields in local Supabase.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    print("=== STUDY POPULATION / CONTEXT INVENTORY ===")
    print("source_id|study_id|population_summary|population_tags|age_min|age_max|age_mean|setting|sample_json")
    studies = psql(args.container, r"""
select
  s.source_id,
  s.study_id,
  coalesce(regexp_replace(s.population_summary, E'[\n\r|]+', ' ', 'g'), 'NULL'),
  case when cardinality(s.population_tags)=0 then '[]' else array_to_string(s.population_tags, ',') end,
  coalesce(s.age_min::text,'NULL'),
  coalesce(s.age_max::text,'NULL'),
  coalesce(s.age_mean::text,'NULL'),
  coalesce(regexp_replace(s.setting, E'[\n\r|]+', ' ', 'g'),'NULL'),
  replace(coalesce(s.sample_json::text,'{}'),'|','/')
from public.study s
order by s.source_id, s.study_id;
""")
    print(studies)

    print("=== COMPONENT DELIVERY / SETTING INVENTORY ===")
    print("source_id|study_id|component_id|component_name|provider|delivery_mode|setting")
    components = psql(args.container, r"""
select
  s.source_id,
  s.study_id,
  ic.component_id,
  regexp_replace(ic.component_name, E'[\n\r|]+', ' ', 'g'),
  coalesce(regexp_replace(ic.provider, E'[\n\r|]+', ' ', 'g'),'NULL'),
  coalesce(regexp_replace(ic.delivery_mode, E'[\n\r|]+', ' ', 'g'),'NULL'),
  coalesce(regexp_replace(ic.setting, E'[\n\r|]+', ' ', 'g'),'NULL')
from public.intervention_component ic
join public.study s on s.study_id=ic.study_id
order by s.source_id, ic.component_id;
""")
    print(components or "<none>")

    print("=== FIELD COVERAGE ===")
    print("studies|population_summary|population_tags_nonempty|age_any|study_setting|components|component_provider|component_delivery|component_setting")
    coverage = psql(args.container, r"""
select
  (select count(*) from public.study),
  (select count(*) from public.study where nullif(btrim(population_summary),'') is not null),
  (select count(*) from public.study where cardinality(population_tags)>0),
  (select count(*) from public.study where age_min is not null or age_max is not null or age_mean is not null),
  (select count(*) from public.study where nullif(btrim(setting),'') is not null),
  (select count(*) from public.intervention_component),
  (select count(*) from public.intervention_component where nullif(btrim(provider),'') is not null),
  (select count(*) from public.intervention_component where nullif(btrim(delivery_mode),'') is not null),
  (select count(*) from public.intervention_component where nullif(btrim(setting),'') is not null);
""")
    print(coverage)

    print("=== EXISTING STAGE 3 APPLICATION-FAMILY LENS ===")
    print("application_links|sources_with_application_links|distinct_application_families")
    app = psql(args.container, r"""
select
  (select count(*) from public.source_version_application_family),
  (select count(distinct source_version_id) from public.source_version_application_family),
  (select count(distinct application_family_key) from public.source_version_application_family);
""")
    print(app)

    print("=== CURRENT NORMALIZED POPULATION/CONTEXT TABLES ===")
    existing = psql(args.container, r"""
select count(*)
from information_schema.tables
where table_schema='public'
  and table_name in (
    'population_context_term',
    'study_population_context_term',
    'study_population_context_status',
    'context_fit_assessment'
  );
""")
    print(f"stage9_target_tables_present|{existing}")

    study_count = int(psql(args.container, "select count(*) from public.study;"))
    if study_count != 18:
        raise SystemExit(f"STAGE 9 AUDIT FAIL: expected 18 studies, got {study_count}")

    print("STAGE 9 AUDIT PASS: raw population/context and delivery fields inventoried; no normalized Stage 9 classifications were created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
