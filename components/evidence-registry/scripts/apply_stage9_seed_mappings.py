#!/usr/bin/env python3
"""Apply conservative Stage 9 candidate population/context mappings to local Supabase."""
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


def psql(container: str, sql: str, *, tuples_only: bool = False) -> str:
    cmd = ["docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres"]
    if tuples_only:
        cmd.extend(["-A", "-t", "-F", "|"])
    return run(cmd, input_text=sql, capture=tuples_only).stdout.strip() if tuples_only else ""


def q(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Stage 9 candidate population/context seed mappings locally.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    if payload.get("mapping_source") != "agent_candidate" or payload.get("review_status") != "proposed":
        raise SystemExit("Stage 9 seed mapper only accepts agent_candidate/proposed manifest")

    # Remove only prior machine-candidate mappings; never touch human-reviewed rows.
    psql(args.container, """
delete from public.study_population_context_term where mapping_source='agent_candidate' and review_status='proposed';
delete from public.component_delivery_context_term where mapping_source='agent_candidate' and review_status='proposed';
update public.study_population_context_status
set extraction_status='not_yet_extracted', mapping_source='migration', review_status='proposed', notes=null, updated_at=now()
where review_status='proposed' and mapping_source in ('migration','agent_candidate');
update public.component_delivery_context_status
set extraction_status='not_yet_extracted', mapping_source='migration', review_status='proposed', notes=null, updated_at=now()
where review_status='proposed' and mapping_source in ('migration','agent_candidate');
""")

    for row in payload["study_mappings"]:
        source_id = row["source_id"]
        study_id = psql(args.container, f"select study_id from public.study where source_id={q(source_id)};", tuples_only=True)
        if not study_id or "\n" in study_id:
            raise SystemExit(f"Expected exactly one study for {source_id}; got {study_id!r}")
        term_id = row["term_id"]
        facet = psql(args.container, f"select facet_kind from public.population_context_term where term_id={q(term_id)};", tuples_only=True)
        if not facet:
            raise SystemExit(f"Unknown Stage 9 term {term_id}")
        psql(args.container, f"""
insert into public.study_population_context_term (
  study_id, term_id, relationship, evidence_basis, mapping_source, review_status
) values (
  {study_id}, {q(term_id)}, {q(row['relationship'])}, {q(row['evidence_basis'])}, 'agent_candidate', 'proposed'
)
on conflict (study_id, term_id, relationship) do update set
  evidence_basis=excluded.evidence_basis,
  mapping_source='agent_candidate',
  review_status='proposed',
  updated_at=now();

update public.study_population_context_status
set extraction_status='candidate_mapped', mapping_source='agent_candidate', review_status='proposed',
    notes='Candidate mapping(s) present; human review required.', updated_at=now()
where study_id={study_id} and facet_kind={q(facet)}
  and review_status='proposed';
""")

    for row in payload["component_delivery_mappings"]:
        source_id = row["source_id"]
        component_name = row["component_name"]
        component_id = psql(args.container, f"""
select ic.component_id
from public.intervention_component ic
join public.study s on s.study_id=ic.study_id
where s.source_id={q(source_id)} and ic.component_name={q(component_name)};
""", tuples_only=True)
        if not component_id or "\n" in component_id:
            raise SystemExit(f"Expected exactly one component for {source_id}/{component_name}; got {component_id!r}")
        psql(args.container, f"""
insert into public.component_delivery_context_term (
  component_id, term_id, evidence_basis, mapping_source, review_status
) values (
  {component_id}, {q(row['term_id'])}, {q(row['evidence_basis'])}, 'agent_candidate', 'proposed'
)
on conflict (component_id, term_id) do update set
  evidence_basis=excluded.evidence_basis,
  mapping_source='agent_candidate',
  review_status='proposed',
  updated_at=now();

update public.component_delivery_context_status
set extraction_status='candidate_mapped', mapping_source='agent_candidate', review_status='proposed',
    notes='Candidate delivery-context mapping(s) present; human review required.', updated_at=now()
where component_id={component_id} and review_status='proposed';
""")

    counts = psql(args.container, """
select
  (select count(*) from public.study_population_context_status),
  (select count(*) from public.study_population_context_term),
  (select count(*) from public.component_delivery_context_status),
  (select count(*) from public.component_delivery_context_term),
  (select count(*) from public.context_fit_assessment),
  (select count(*) from public.study_population_context_term where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.component_delivery_context_term where mapping_source='agent_candidate' and review_status='approved')
+ (select count(*) from public.context_fit_assessment where mapping_source='agent_candidate' and review_status='approved');
""", tuples_only=True)
    print("STAGE 9 CANDIDATE MAPPINGS APPLIED")
    print("study_status_rows|study_links|component_status_rows|delivery_links|context_fit|agent_promoted")
    print(counts)
    print("All Stage 9 seed mappings remain agent_candidate / proposed; context-fit judgements remain empty.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
