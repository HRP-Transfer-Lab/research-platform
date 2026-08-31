#!/usr/bin/env python3
"""Validate Stage 10 harms/fidelity/support-dependence architecture locally."""
from __future__ import annotations

import argparse
import subprocess

DEFAULT_CONTAINER = "supabase_db_research-platform"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd=["docker","exec","-i",container,"psql","-v","ON_ERROR_STOP=1","-U","postgres","-d","postgres","-A","-t","-F","|"]
    return run(cmd,input_text=sql,capture=True).stdout.strip()


def scalar(container: str, sql: str) -> int:
    v=psql(container,sql)
    try: return int(v)
    except ValueError as exc: raise SystemExit(f"Expected integer SQL result; got {v!r}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"STAGE 10 HARMS/IMPLEMENTATION INVALID: {message}")


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--container",default=DEFAULT_CONTAINER); args=ap.parse_args()
    running=run(["docker","inspect","-f","{{.State.Running}}",args.container],capture=True).stdout.strip()
    require(running=="true",f"local database container {args.container!r} is not running")

    require(scalar(args.container,"select count(*) from public.harm_type_definition;")==8,"expected 8 harm types")
    require(scalar(args.container,"select count(*) from public.study;")==18,"expected 18 studies")
    require(scalar(args.container,"select count(*) from public.intervention_component;")==13,"expected 13 components")
    require(scalar(args.container,"select count(*) from public.study_harms_status;")==18,"expected 18 harms-status rows")
    require(scalar(args.container,"select count(*) from public.component_implementation_status;")==130,"expected 130 component implementation status rows")

    counts=psql(args.container,"""
select
 (select count(*) from public.harm_observation),
 (select count(*) from public.study_participation_observation),
 (select count(*) from public.component_implementation_observation),
 (select count(*) from public.component_reporting_assessment),
 (select count(*) from public.support_dependence_observation),
 (select count(*) from public.boundary_condition_observation);
""")
    require(counts=="1|8|4|0|1|3",f"unexpected Stage 10 observation counts: {counts}")

    rt013=psql(args.container,"""
select s.source_id||'|'||hs.extraction_status||'|'||hs.assessment_mode||'|'||coalesce(hs.systematic_assessment::text,'NULL')||'|'||ho.harm_type||'|'||eo.outcome_name||'|'||coalesce(ho.event_count::text,'NULL')||'|'||coalesce(ho.participant_count::text,'NULL')
from public.study_harms_status hs
join public.study s on s.study_id=hs.study_id
join public.harm_observation ho on ho.study_id=s.study_id
left join public.evidence_outcome eo on eo.outcome_id=ho.outcome_id
where s.source_id='rt-2026-013';
""")
    require(rt013=="rt-2026-013|candidate_signal_present|passive_or_incidental|false|performance_tradeoff|memory test performance|NULL|NULL",f"rt-013 harm semantics changed: {rt013!r}")

    no_harm_claims=scalar(args.container,"""
select count(*) from public.study_harms_status
where extraction_status='reviewed_no_harm_observed';
""")
    require(no_harm_claims==0,f"seed fabricated reviewed no-harm conclusions={no_harm_claims}")
    zero_events=scalar(args.container,"select count(*) from public.harm_observation where event_count=0;")
    require(zero_events==0,f"seed fabricated zero-event harm observations={zero_events}")
    harm_withdrawals=scalar(args.container,"select count(*) from public.harm_observation where withdrawal_due_to_harm is true;")
    require(harm_withdrawals==0,f"seed fabricated withdrawal-due-to-harm observations={harm_withdrawals}")

    flows=psql(args.container,"""
select string_agg(s.source_id||':'||p.flow_kind||':'||p.participant_count::text,',' order by s.source_id,p.flow_kind,p.participant_count)
from public.study_participation_observation p join public.study s on s.study_id=p.study_id;
""")
    expected_flows="rt-2026-001:analysed:51,rt-2026-001:randomized:54,rt-2026-006:completed:138,rt-2026-006:randomized:162,rt-2026-009:enrolled:23,rt-2026-009:followup_assessed:22,rt-2026-015:completed:168,rt-2026-015:entered:180"
    require(flows==expected_flows,f"participation flow changed: {flows!r}")
    adherence_obs=scalar(args.container,"select count(*) from public.component_implementation_observation where dimension='adherence';")
    require(adherence_obs==0,"participation flow must not auto-create adherence observations")

    impl=psql(args.container,"""
select string_agg(s.source_id||':'||io.dimension||':'||io.value_text,',' order by s.source_id,io.dimension,io.value_text)
from public.component_implementation_observation io
join public.intervention_component ic on ic.component_id=io.component_id
join public.study s on s.study_id=ic.study_id;
""")
    require("rt-2026-001:delivery_mode:guided cognitive training" in impl,"rt-001 delivery observation missing")
    require("rt-2026-003:delivery_mode:researcher-facilitated tablet games" in impl,"rt-003 delivery observation missing")
    require("rt-2026-004:delivery_mode:structured matching-to-sample training" in impl,"rt-004 delivery observation missing")
    require("rt-2026-015:materials_procedures:" in impl,"rt-015 procedures observation missing")
    unsupported_impl=scalar(args.container,"select count(*) from public.component_implementation_observation where dimension in ('fidelity','adherence','implementation_burden','cost_resources');")
    require(unsupported_impl==0,f"unsupported fidelity/adherence/burden/cost observations={unsupported_impl}")

    support=psql(args.container,"""
select s.source_id||'|'||eo.outcome_name||'|'||sd.support_type||'|'||sd.support_presence||'|'||sd.support_requirement||'|'||sd.autonomy_status
from public.support_dependence_observation sd
join public.study s on s.study_id=sd.study_id
left join public.evidence_outcome eo on eo.outcome_id=sd.outcome_id;
""")
    require(support=="rt-2026-015|independent no-AI writing quality|ai_assistance|absent|absent_at_test|unsupported_demonstrated",f"rt-015 support/autonomy semantics changed: {support!r}")

    boundary=psql(args.container,"""
select string_agg(s.source_id||':'||b.boundary_direction,',' order by s.source_id,b.boundary_direction)
from public.boundary_condition_observation b join public.study s on s.study_id=b.study_id;
""")
    require(boundary=="rt-2026-015:independence_not_demonstrated,rt-2026-016:effect_dissociation,rt-2026-018:observational_association",f"boundary evidence changed: {boundary!r}")

    stage4_harm=scalar(args.container,"select count(*) from public.outcome_role_link where outcome_role='harm';")
    stage4_bridge=scalar(args.container,"select count(*) from public.outcome_bridge_evidence;")
    require(stage4_harm==0,f"Stage 10 must not auto-promote Stage 4 harm roles; got {stage4_harm}")
    require(stage4_bridge==0,f"Stage 10 must not auto-promote Stage 4 Bridge evidence; got {stage4_bridge}")

    tidier=psql(args.container,"select framework_key||'|'||subject_kind from public.assessment_framework_definition where framework_key='tidier';")
    require(tidier=="tidier|component_reporting_or_fidelity",f"TIDieR framework boundary changed: {tidier!r}")
    require(scalar(args.container,"select count(*) from public.component_reporting_assessment;")==0,"seed must not fabricate TIDieR assessments")

    agent_promoted=scalar(args.container,"""
select
 (select count(*) from public.study_harms_status where mapping_source='agent_candidate' and review_status='approved')+
 (select count(*) from public.harm_observation where mapping_source='agent_candidate' and review_status='approved')+
 (select count(*) from public.study_participation_observation where mapping_source='agent_candidate' and review_status='approved')+
 (select count(*) from public.component_implementation_status where mapping_source='agent_candidate' and review_status='approved')+
 (select count(*) from public.component_implementation_observation where mapping_source='agent_candidate' and review_status='approved')+
 (select count(*) from public.component_reporting_assessment where mapping_source='agent_candidate' and review_status='approved')+
 (select count(*) from public.support_dependence_observation where mapping_source='agent_candidate' and review_status='approved')+
 (select count(*) from public.boundary_condition_observation where mapping_source='agent_candidate' and review_status='approved');
""")
    require(agent_promoted==0,f"Stage 10 agent candidates promoted={agent_promoted}")

    candidate_status=scalar(args.container,"select count(*) from public.component_implementation_status where extraction_status='candidate_mapped' and mapping_source='agent_candidate' and review_status='proposed';")
    require(candidate_status==5,f"expected 5 candidate-mapped implementation dimensions (4 observations + rt015 support); got {candidate_status}")
    untouched_harms=scalar(args.container,"select count(*) from public.study_harms_status where extraction_status='not_yet_extracted' and mapping_source='migration' and review_status='proposed';")
    require(untouched_harms==17,f"expected 17 harms statuses to remain not_yet_extracted; got {untouched_harms}")

    triggers=scalar(args.container,"""
select count(*) from pg_trigger where not tgisinternal and tgname in (
 'ensure_stage10_study_status','ensure_stage10_component_status',
 'validate_stage10_harm_links','validate_stage10_support_links','validate_stage10_boundary_links','validate_stage10_component_reporting_framework',
 'prevent_stage10_agent_harm_status','prevent_stage10_agent_harm','prevent_stage10_agent_participation','prevent_stage10_agent_impl_status',
 'prevent_stage10_agent_impl_obs','prevent_stage10_agent_reporting','prevent_stage10_agent_support','prevent_stage10_agent_boundary'
);
""")
    require(triggers==14,f"expected 14 Stage 10 status/integrity/human-gate triggers; got {triggers}")

    print("STAGE 10 HARMS/IMPLEMENTATION VALID: harm_types=8; studies=18; harm_status=18; harms=1; participation=8; components=13; impl_status=130; impl_obs=4; support=1; boundaries=3; component_reporting=0")
    print("no_harm_noninference: PASS (17 not_yet_extracted; 0 reviewed-no-harm claims)")
    print("performance_tradeoff_harm_signal: PASS (rt-2026-013 only)")
    print("participation_vs_adherence_vs_harm_withdrawal: PASS")
    print("implementation_missingness: PASS (no fabricated fidelity/adherence/burden/cost)")
    print("support_dependence_vs_bridge: PASS (rt-015 unsupported test encoded; Stage 4 Bridge remains 0)")
    print("boundary_evidence: PASS (rt-015 / rt-016 / rt-018)")
    print("tidier_subject_boundary: PASS (legitimate component subject; 0 fabricated assessments)")
    print("human_approval_boundary: PASS (0 agent candidates promoted)")
    return 0


if __name__=='__main__':
    raise SystemExit(main())
