#!/usr/bin/env python3
"""Apply conservative Stage 10 seed mappings to local Supabase only."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage10_seed_mappings.v1.json"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str, *, tuples_only: bool = False) -> str:
    cmd = ["docker","exec","-i",container,"psql","-v","ON_ERROR_STOP=1","-U","postgres","-d","postgres"]
    if tuples_only:
        cmd.extend(["-A","-t","-F","|"])
    completed = run(cmd, input_text=sql, capture=tuples_only)
    return completed.stdout.strip() if tuples_only else ""


def q(value: str | None) -> str:
    if value is None:
        return "null"
    return "'" + value.replace("'", "''") + "'"


def b(value: bool | None) -> str:
    if value is None:
        return "null"
    return "true" if value else "false"


def resolve_study(container: str, source_id: str) -> str:
    out = psql(container, f"select study_id from public.study where source_id={q(source_id)};", tuples_only=True)
    if not out or "\n" in out:
        raise SystemExit(f"Expected exactly one study for {source_id}; got {out!r}")
    return out


def resolve_component(container: str, source_id: str, component_name: str) -> str:
    out = psql(container, f"""
select ic.component_id
from public.intervention_component ic
join public.study s on s.study_id=ic.study_id
where s.source_id={q(source_id)} and ic.component_name={q(component_name)};
""", tuples_only=True)
    if not out or "\n" in out:
        raise SystemExit(f"Expected exactly one component for {source_id}/{component_name}; got {out!r}")
    return out


def resolve_outcome(container: str, source_id: str, outcome_name: str) -> str:
    out = psql(container, f"""
select eo.outcome_id
from public.evidence_outcome eo
join public.study s on s.study_id=eo.study_id
where s.source_id={q(source_id)} and eo.outcome_name={q(outcome_name)};
""", tuples_only=True)
    if not out or "\n" in out:
        raise SystemExit(f"Expected exactly one outcome for {source_id}/{outcome_name}; got {out!r}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()

    running = run(["docker","inspect","-f","{{.State.Running}}",args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    if payload.get("mapping_source") != "agent_candidate" or payload.get("review_status") != "proposed":
        raise SystemExit("Stage 10 mapper only accepts agent_candidate/proposed manifest")

    # Remove/revert only unreviewed machine state. Human-reviewed rows are untouched.
    psql(args.container, """
delete from public.harm_observation where mapping_source='agent_candidate' and review_status='proposed';
delete from public.study_participation_observation where mapping_source='agent_candidate' and review_status='proposed';
delete from public.component_implementation_observation where mapping_source='agent_candidate' and review_status='proposed';
delete from public.component_reporting_assessment where mapping_source='agent_candidate' and review_status='proposed';
delete from public.support_dependence_observation where mapping_source='agent_candidate' and review_status='proposed';
delete from public.boundary_condition_observation where mapping_source='agent_candidate' and review_status='proposed';

update public.study_harms_status
set extraction_status='not_yet_extracted', assessment_mode='not_yet_extracted', systematic_assessment=null,
    notes=null, mapping_source='migration', review_status='proposed', updated_at=now()
where review_status='proposed' and mapping_source in ('migration','agent_candidate');

update public.component_implementation_status
set extraction_status='not_yet_extracted', notes=null, mapping_source='migration', review_status='proposed', updated_at=now()
where review_status='proposed' and mapping_source in ('migration','agent_candidate');
""")

    for row in payload["harms_status_overrides"]:
        study_id = resolve_study(args.container, row["source_id"])
        psql(args.container, f"""
update public.study_harms_status set
  extraction_status={q(row['extraction_status'])},
  assessment_mode={q(row['assessment_mode'])},
  systematic_assessment={b(row.get('systematic_assessment'))},
  notes={q(row.get('notes'))},
  mapping_source='agent_candidate', review_status='proposed', updated_at=now()
where study_id={study_id} and review_status='proposed';
""")

    for row in payload["harm_observations"]:
        study_id = resolve_study(args.container, row["source_id"])
        outcome_id = resolve_outcome(args.container, row["source_id"], row["outcome_name"])
        psql(args.container, f"""
insert into public.harm_observation (
  study_id,outcome_id,harm_type,harm_label,severity,serious,event_count,participant_count,
  withdrawal_due_to_harm,systematically_assessed,result_summary,evidence_basis,mapping_source,review_status
) values (
  {study_id},{outcome_id},{q(row['harm_type'])},{q(row['harm_label'])},{q(row.get('severity'))},{b(row.get('serious'))},
  null,null,{b(row.get('withdrawal_due_to_harm'))},{b(row.get('systematically_assessed'))},
  {q(row['result_summary'])},{q(row['evidence_basis'])},'agent_candidate','proposed'
);
""")

    for row in payload["participation_observations"]:
        study_id = resolve_study(args.container, row["source_id"])
        psql(args.container, f"""
insert into public.study_participation_observation (
  study_id,flow_kind,participant_count,source_field,evidence_basis,mapping_source,review_status
) values (
  {study_id},{q(row['flow_kind'])},{int(row['participant_count'])},{q(row.get('source_field'))},{q(row['evidence_basis'])},'agent_candidate','proposed'
)
on conflict (study_id,flow_kind,participant_count,source_field) do update set
  evidence_basis=excluded.evidence_basis,mapping_source='agent_candidate',review_status='proposed',updated_at=now();
""")

    for row in payload["implementation_observations"]:
        component_id = resolve_component(args.container, row["source_id"], row["component_name"])
        psql(args.container, f"""
insert into public.component_implementation_observation (
  component_id,dimension,observation_kind,value_text,value_numeric,unit,status_or_level,evidence_basis,mapping_source,review_status
) values (
  {component_id},{q(row['dimension'])},{q(row['observation_kind'])},{q(row.get('value_text'))},null,null,null,
  {q(row['evidence_basis'])},'agent_candidate','proposed'
);
update public.component_implementation_status
set extraction_status='candidate_mapped',mapping_source='agent_candidate',review_status='proposed',
    notes='Candidate Stage 10 observation present; human review required.',updated_at=now()
where component_id={component_id} and dimension={q(row['dimension'])} and review_status='proposed';
""")

    for row in payload["support_dependence_observations"]:
        study_id = resolve_study(args.container, row["source_id"])
        component_id = resolve_component(args.container, row["source_id"], row["component_name"])
        outcome_id = resolve_outcome(args.container, row["source_id"], row["outcome_name"])
        psql(args.container, f"""
insert into public.support_dependence_observation (
  study_id,component_id,outcome_id,support_type,support_presence,support_requirement,autonomy_status,evidence_basis,mapping_source,review_status
) values (
  {study_id},{component_id},{outcome_id},{q(row['support_type'])},{q(row['support_presence'])},{q(row['support_requirement'])},
  {q(row.get('autonomy_status'))},{q(row['evidence_basis'])},'agent_candidate','proposed'
);
update public.component_implementation_status
set extraction_status='candidate_mapped',mapping_source='agent_candidate',review_status='proposed',
    notes='Candidate support-dependence evidence present; does not establish Bridge success.',updated_at=now()
where component_id={component_id} and dimension='support_dependence' and review_status='proposed';
""")

    for row in payload["boundary_observations"]:
        study_id = resolve_study(args.container, row["source_id"])
        component_id = "null"
        outcome_id = "null"
        if row.get("component_name"):
            component_id = resolve_component(args.container, row["source_id"], row["component_name"])
        if row.get("outcome_name"):
            outcome_id = resolve_outcome(args.container, row["source_id"], row["outcome_name"])
        psql(args.container, f"""
insert into public.boundary_condition_observation (
  study_id,component_id,outcome_id,boundary_dimension,boundary_direction,boundary_summary,evidence_basis,mapping_source,review_status
) values (
  {study_id},{component_id},{outcome_id},{q(row['boundary_dimension'])},{q(row['boundary_direction'])},
  {q(row['boundary_summary'])},{q(row['evidence_basis'])},'agent_candidate','proposed'
);
""")

    counts = psql(args.container, """
select
  (select count(*) from public.study_harms_status),
  (select count(*) from public.harm_observation),
  (select count(*) from public.study_participation_observation),
  (select count(*) from public.component_implementation_status),
  (select count(*) from public.component_implementation_observation),
  (select count(*) from public.component_reporting_assessment),
  (select count(*) from public.support_dependence_observation),
  (select count(*) from public.boundary_condition_observation),
  (
    (select count(*) from public.study_harms_status where mapping_source='agent_candidate' and review_status='approved')+
    (select count(*) from public.harm_observation where mapping_source='agent_candidate' and review_status='approved')+
    (select count(*) from public.study_participation_observation where mapping_source='agent_candidate' and review_status='approved')+
    (select count(*) from public.component_implementation_status where mapping_source='agent_candidate' and review_status='approved')+
    (select count(*) from public.component_implementation_observation where mapping_source='agent_candidate' and review_status='approved')+
    (select count(*) from public.support_dependence_observation where mapping_source='agent_candidate' and review_status='approved')+
    (select count(*) from public.boundary_condition_observation where mapping_source='agent_candidate' and review_status='approved')
  );
""", tuples_only=True)
    print("STAGE 10 CANDIDATE MAPPINGS APPLIED")
    print("harm_status|harms|participation|impl_status|impl_obs|component_reporting|support|boundaries|agent_promoted")
    print(counts)
    print("No zero-harm, fidelity, adherence, cost, TIDieR or Bridge judgement was inferred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
