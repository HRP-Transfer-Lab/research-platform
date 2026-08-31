#!/usr/bin/env python3
"""Read-only Stage 10 audit of harms, fidelity, dependence and implementation signals."""
from __future__ import annotations

import argparse
import subprocess

DEFAULT_CONTAINER = "supabase_db_research-platform"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container,
        "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres",
        "-A", "-t", "-F", "|",
    ]
    return run(cmd, input_text=sql, capture=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit current Stage 10 harms/implementation source signals locally.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    print("=== COMPONENT IMPLEMENTATION RAW FIELDS ===")
    print("source_id|component_id|component_name|provider|delivery_mode|setting|tailoring|fidelity|prompt_status|protocol_json")
    components = psql(args.container, r"""
select
  s.source_id,
  ic.component_id,
  regexp_replace(ic.component_name, E'[\n\r|]+', ' ', 'g'),
  coalesce(regexp_replace(ic.provider, E'[\n\r|]+', ' ', 'g'),'NULL'),
  coalesce(regexp_replace(ic.delivery_mode, E'[\n\r|]+', ' ', 'g'),'NULL'),
  coalesce(regexp_replace(ic.setting, E'[\n\r|]+', ' ', 'g'),'NULL'),
  coalesce(regexp_replace(ic.tailoring, E'[\n\r|]+', ' ', 'g'),'NULL'),
  coalesce(regexp_replace(ic.fidelity, E'[\n\r|]+', ' ', 'g'),'NULL'),
  coalesce(regexp_replace(ic.prompt_status, E'[\n\r|]+', ' ', 'g'),'NULL'),
  replace(coalesce(ic.protocol_json::text,'{}'),'|','/')
from public.intervention_component ic
join public.study s on s.study_id=ic.study_id
order by s.source_id, ic.component_id;
""")
    print(components or "<none>")

    print("=== IMPLEMENTATION FIELD COVERAGE ===")
    print("components|provider|delivery_mode|setting|tailoring|fidelity|prompt_status|protocol_json_nonempty")
    coverage = psql(args.container, r"""
select
  count(*),
  count(*) filter (where nullif(btrim(provider),'') is not null),
  count(*) filter (where nullif(btrim(delivery_mode),'') is not null),
  count(*) filter (where nullif(btrim(setting),'') is not null),
  count(*) filter (where nullif(btrim(tailoring),'') is not null),
  count(*) filter (where nullif(btrim(fidelity),'') is not null),
  count(*) filter (where nullif(btrim(prompt_status),'') is not null),
  count(*) filter (where protocol_json <> '{}'::jsonb)
from public.intervention_component;
""")
    print(coverage)

    print("=== STUDY SAMPLE / COMPLETION SIGNALS ===")
    print("source_id|study_id|sample_json")
    sample = psql(args.container, r"""
select s.source_id, s.study_id, replace(coalesce(s.sample_json::text,'{}'),'|','/')
from public.study s
where s.sample_json <> '{}'::jsonb
order by s.source_id;
""")
    print(sample or "<none>")

    print("=== STAGE 4 OUTCOME ROLE INVENTORY ===")
    print("outcome_role|links")
    roles = psql(args.container, r"""
select outcome_role, count(*)
from public.outcome_role_link
group by outcome_role
order by outcome_role;
""")
    print(roles or "<none>")

    print("=== EXPLICIT HARM-ROLE OUTCOMES ===")
    print("source_id|outcome_id|outcome_name|result_direction|result_summary|mapping_source|review_status")
    harm_rows = psql(args.container, r"""
select
  s.source_id,
  eo.outcome_id,
  regexp_replace(eo.outcome_name, E'[\n\r|]+', ' ', 'g'),
  coalesce(eo.result_direction,'NULL'),
  coalesce(regexp_replace(eo.result_summary, E'[\n\r|]+', ' ', 'g'),'NULL'),
  orl.mapping_source,
  orl.review_status
from public.outcome_role_link orl
join public.evidence_outcome eo on eo.outcome_id=orl.outcome_id
join public.study s on s.study_id=eo.study_id
where orl.outcome_role='harm'
order by s.source_id, eo.outcome_id;
""")
    print(harm_rows or "<none>")

    print("=== STAGE 4 BRIDGE EVIDENCE INVENTORY ===")
    print("bridge_links|outcomes_with_bridge")
    bridge = psql(args.container, r"""
select count(*), count(distinct outcome_id)
from public.outcome_bridge_evidence;
""")
    print(bridge)

    print("=== SOURCE RAW-RECORD KEYWORD SIGNALS (CANDIDATE ONLY) ===")
    print("source_id|harms|withdrawal|fidelity_adherence|prompt_scaffold_dependence|burden_fatigue|modification_tailoring|cost_resources")
    signals = psql(args.container, r"""
select
  es.source_id,
  case when es.raw_record::text ~* '(adverse|harm|worsen|side[ -]?effect|trade[- ]?off)' then 'yes' else 'no' end,
  case when es.raw_record::text ~* '(withdraw|dropout|attrition|discontinu)' then 'yes' else 'no' end,
  case when es.raw_record::text ~* '(fidelity|adherence|compliance|completion)' then 'yes' else 'no' end,
  case when es.raw_record::text ~* '(prompt|scaffold|support dependence|dependent|autonom|without ai|without prompt|unprompted)' then 'yes' else 'no' end,
  case when es.raw_record::text ~* '(burden|fatigue|effort cost|workload)' then 'yes' else 'no' end,
  case when es.raw_record::text ~* '(modif|tailor|adapt)' then 'yes' else 'no' end,
  case when es.raw_record::text ~* '(cost|resource|staff time|time burden|economic)' then 'yes' else 'no' end
from public.evidence_source es
where
  es.raw_record::text ~* '(adverse|harm|worsen|side[ -]?effect|trade[- ]?off|withdraw|dropout|attrition|discontinu|fidelity|adherence|compliance|completion|prompt|scaffold|support dependence|dependent|autonom|without ai|without prompt|unprompted|burden|fatigue|effort cost|workload|modif|tailor|adapt|cost|resource|staff time|time burden|economic)'
order by es.source_id;
""")
    print(signals or "<none>")

    print("=== PROTOCOL JSON KEYWORD SIGNALS (CANDIDATE ONLY) ===")
    print("source_id|component_id|component_name|signal_categories")
    protocol_signals = psql(args.container, r"""
select
  s.source_id,
  ic.component_id,
  regexp_replace(ic.component_name, E'[\n\r|]+', ' ', 'g'),
  concat_ws(',',
    case when ic.protocol_json::text ~* '(fidelity|adherence|compliance|completion)' then 'fidelity_adherence' end,
    case when ic.protocol_json::text ~* '(prompt|scaffold|dependent|autonom|without ai|without prompt|unprompted)' then 'support_dependence' end,
    case when ic.protocol_json::text ~* '(burden|fatigue|workload)' then 'burden_fatigue' end,
    case when ic.protocol_json::text ~* '(modif|tailor|adapt)' then 'modification_tailoring' end,
    case when ic.protocol_json::text ~* '(cost|resource|staff time)' then 'cost_resources' end
  )
from public.intervention_component ic
join public.study s on s.study_id=ic.study_id
where ic.protocol_json::text ~* '(fidelity|adherence|compliance|completion|prompt|scaffold|dependent|autonom|without ai|without prompt|unprompted|burden|fatigue|workload|modif|tailor|adapt|cost|resource|staff time)'
order by s.source_id, ic.component_id;
""")
    print(protocol_signals or "<none>")

    print("=== EXISTING STAGE 10 TARGET TABLES ===")
    target_tables = psql(args.container, r"""
select count(*)
from information_schema.tables
where table_schema='public'
  and table_name in (
    'study_harms_status',
    'harm_observation',
    'component_implementation_status',
    'component_implementation_observation',
    'support_dependence_observation',
    'boundary_condition_observation'
  );
""")
    print(f"stage10_target_tables_present|{target_tables}")

    counts = psql(args.container, "select (select count(*) from public.study)||(E'|')||(select count(*) from public.intervention_component)||(E'|')||(select count(*) from public.evidence_outcome);")
    if counts != "18|13|38":
        raise SystemExit(f"STAGE 10 AUDIT FAIL: expected 18 studies / 13 components / 38 outcomes; got {counts}")

    print("STAGE 10 AUDIT PASS: raw harms/implementation/support-dependence signals inventoried; no Stage 10 scientific judgement was created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
