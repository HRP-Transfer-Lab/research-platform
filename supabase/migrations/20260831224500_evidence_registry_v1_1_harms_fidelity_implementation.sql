-- HRP Transfer Evidence Registry v1.1
-- Stage 10: harms, fidelity, support dependence, implementation, participation flow and scientific boundaries.
--
-- Scientific rules:
--   not reported != no harm
--   harm != harms-reporting completeness
--   fidelity/adherence != study quality/RoB
--   support dependence != Bridge success
--   attrition != adherence != withdrawal due to harm

-- 1. Harms taxonomy and per-study completeness state
create table public.harm_type_definition (
  harm_type text primary key,
  label text not null,
  description text not null,
  active boolean not null default true
);

insert into public.harm_type_definition (harm_type,label,description) values
('physical_adverse_event','Physical adverse event','Physical adverse event or symptom attributable or potentially attributable to exposure/intervention.'),
('psychological_worsening','Psychological worsening','Worsening in psychological state, distress or functioning.'),
('performance_tradeoff','Performance trade-off','Worsening, decrement or adverse performance trade-off on a measured task/function.'),
('fatigue_or_burden','Fatigue or burden','Fatigue, effort burden, overload or other participant burden.'),
('loss_of_autonomy_or_dependency','Loss of autonomy or dependency','Evidence of dependency, reduced independent capability or loss of cognitive agency.'),
('withdrawal_due_to_harm','Withdrawal due to harm','Withdrawal explicitly attributed to adverse effects or harm.'),
('serious_adverse_event','Serious adverse event','Serious adverse event as defined/reported by the source.'),
('other_harm','Other harm','Other reviewed adverse consequence not captured above.');

create table public.study_harms_status (
  study_id bigint primary key references public.study(study_id) on delete cascade,
  extraction_status text not null default 'not_yet_extracted' check (
    extraction_status in ('not_yet_extracted','candidate_signal_present','reviewed_complete','reviewed_no_harm_observed','not_reported','not_systematically_assessed','not_applicable')
  ),
  assessment_mode text not null default 'not_yet_extracted' check (
    assessment_mode in ('not_yet_extracted','not_reported','passive_or_incidental','systematic','unclear','not_applicable')
  ),
  systematic_assessment boolean,
  notes text,
  mapping_source text not null default 'migration' check (mapping_source in ('migration','agent_candidate','human_review','manual')),
  review_status text not null default 'proposed' check (review_status in ('proposed','reviewed','approved','rejected')),
  updated_at timestamptz not null default now()
);

create table public.harm_observation (
  harm_observation_id bigserial primary key,
  study_id bigint not null references public.study(study_id) on delete cascade,
  arm_id bigint references public.study_arm(arm_id) on delete restrict,
  outcome_id bigint references public.evidence_outcome(outcome_id) on delete restrict,
  contrast_id bigint references public.study_contrast(contrast_id) on delete restrict,
  harm_type text not null references public.harm_type_definition(harm_type),
  harm_label text not null,
  severity text check (severity is null or severity in ('mild','moderate','severe','serious','unclear','not_applicable')),
  serious boolean,
  event_count integer check (event_count is null or event_count >= 0),
  participant_count integer check (participant_count is null or participant_count >= 0),
  withdrawal_due_to_harm boolean,
  systematically_assessed boolean,
  result_summary text not null,
  evidence_basis text not null,
  mapping_source text not null default 'human_review' check (mapping_source in ('migration','agent_candidate','human_review','manual')),
  review_status text not null default 'proposed' check (review_status in ('proposed','reviewed','approved','rejected')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index harm_observation_study_idx on public.harm_observation(study_id);
create index harm_observation_outcome_idx on public.harm_observation(outcome_id) where outcome_id is not null;
create index harm_observation_type_idx on public.harm_observation(harm_type);

-- 2. Participation-flow facts; deliberately distinct from adherence and harm withdrawal
create table public.study_participation_observation (
  participation_observation_id bigserial primary key,
  study_id bigint not null references public.study(study_id) on delete cascade,
  flow_kind text not null check (flow_kind in ('enrolled','entered','randomized','completed','analysed','followup_assessed','other')),
  participant_count integer not null check (participant_count >= 0),
  source_field text,
  evidence_basis text not null,
  mapping_source text not null default 'human_review' check (mapping_source in ('migration','agent_candidate','human_review','manual')),
  review_status text not null default 'proposed' check (review_status in ('proposed','reviewed','approved','rejected')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (study_id, flow_kind, participant_count, source_field)
);
create index study_participation_study_idx on public.study_participation_observation(study_id);

-- 3. Component implementation completeness and observations
create table public.component_implementation_status (
  component_id bigint not null references public.intervention_component(component_id) on delete cascade,
  dimension text not null check (dimension in (
    'provider','materials_procedures','delivery_mode','fidelity','adherence','tailoring','modification','support_dependence','implementation_burden','cost_resources'
  )),
  extraction_status text not null default 'not_yet_extracted' check (
    extraction_status in ('not_yet_extracted','candidate_mapped','reviewed_mapped','reviewed_no_mapping','not_reported','not_applicable')
  ),
  notes text,
  mapping_source text not null default 'migration' check (mapping_source in ('migration','agent_candidate','human_review','manual')),
  review_status text not null default 'proposed' check (review_status in ('proposed','reviewed','approved','rejected')),
  updated_at timestamptz not null default now(),
  primary key (component_id, dimension)
);

create table public.component_implementation_observation (
  implementation_observation_id bigserial primary key,
  component_id bigint not null references public.intervention_component(component_id) on delete cascade,
  dimension text not null check (dimension in (
    'provider','materials_procedures','delivery_mode','fidelity','adherence','tailoring','modification','support_dependence','implementation_burden','cost_resources'
  )),
  observation_kind text not null,
  value_text text,
  value_numeric numeric,
  unit text,
  status_or_level text,
  evidence_basis text not null,
  mapping_source text not null default 'human_review' check (mapping_source in ('migration','agent_candidate','human_review','manual')),
  review_status text not null default 'proposed' check (review_status in ('proposed','reviewed','approved','rejected')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (num_nonnulls(value_text,value_numeric,status_or_level) >= 1)
);
create index component_impl_obs_component_idx on public.component_implementation_observation(component_id);
create index component_impl_obs_dimension_idx on public.component_implementation_observation(dimension);

-- 4. Legitimate Stage 10 subject for TIDieR/component reporting or fidelity frameworks
create table public.component_reporting_assessment (
  component_reporting_assessment_id bigserial primary key,
  component_id bigint not null references public.intervention_component(component_id) on delete cascade,
  assessment_key text not null,
  framework_key text not null references public.assessment_framework_definition(framework_key),
  framework_version text,
  overall_judgement text,
  assessment_status text not null default 'assessment_in_progress' check (
    assessment_status in ('assessment_in_progress','partially_assessed','reviewed_complete','insufficient_information','not_applicable')
  ),
  notes text,
  assessor text,
  assessed_on date,
  mapping_source text not null default 'human_review' check (mapping_source in ('migration','agent_candidate','human_review','manual')),
  review_status text not null default 'proposed' check (review_status in ('proposed','reviewed','approved','rejected')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (component_id, assessment_key)
);

-- 5. Support / prompt dependence; result-aware and study-aware
create table public.support_dependence_observation (
  support_dependence_id bigserial primary key,
  study_id bigint not null references public.study(study_id) on delete cascade,
  component_id bigint references public.intervention_component(component_id) on delete restrict,
  outcome_id bigint references public.evidence_outcome(outcome_id) on delete restrict,
  support_type text not null check (support_type in (
    'continuous_scaffold','explicit_prompt','cue_triggered_support','human_coaching','ai_assistance','materials_or_tool_support','unsupported_or_autonomous','unclear'
  )),
  support_presence text not null check (support_presence in ('present','absent','variable','unclear','not_applicable')),
  support_requirement text not null check (support_requirement in ('required','optional','removed_at_test','absent_at_test','unclear','not_applicable')),
  autonomy_status text check (autonomy_status is null or autonomy_status in ('scaffold_dependent','partially_independent','unsupported_demonstrated','autonomy_not_tested','unclear')),
  evidence_basis text not null,
  mapping_source text not null default 'human_review' check (mapping_source in ('migration','agent_candidate','human_review','manual')),
  review_status text not null default 'proposed' check (review_status in ('proposed','reviewed','approved','rejected')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index support_dependence_study_idx on public.support_dependence_observation(study_id);
create index support_dependence_outcome_idx on public.support_dependence_observation(outcome_id) where outcome_id is not null;

-- 6. Scientific boundary observations
create table public.boundary_condition_observation (
  boundary_condition_id bigserial primary key,
  study_id bigint not null references public.study(study_id) on delete cascade,
  component_id bigint references public.intervention_component(component_id) on delete restrict,
  outcome_id bigint references public.evidence_outcome(outcome_id) on delete restrict,
  proposition_id bigint references public.evidence_proposition(proposition_id) on delete restrict,
  boundary_dimension text not null check (boundary_dimension in (
    'population','context','baseline_state','dose_or_exposure','delivery','support_dependence','time_or_durability','transfer','performance_tradeoff','implementation','other'
  )),
  boundary_direction text not null check (boundary_direction in (
    'limits_generalisation','conditional_effect','reversal_or_harm','null_boundary','requires_support','independence_not_demonstrated','effect_dissociation','observational_association','other'
  )),
  boundary_summary text not null,
  evidence_basis text not null,
  mapping_source text not null default 'human_review' check (mapping_source in ('migration','agent_candidate','human_review','manual')),
  review_status text not null default 'proposed' check (review_status in ('proposed','reviewed','approved','rejected')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index boundary_condition_study_idx on public.boundary_condition_observation(study_id);
create index boundary_condition_proposition_idx on public.boundary_condition_observation(proposition_id) where proposition_id is not null;

-- 7. Deterministic default status rows
create or replace function private.ensure_stage10_study_status()
returns trigger language plpgsql security definer set search_path=public,pg_temp as $$
begin
  insert into public.study_harms_status(study_id) values(new.study_id) on conflict(study_id) do nothing;
  return new;
end; $$;
revoke all on function private.ensure_stage10_study_status() from public, anon, authenticated;
create trigger ensure_stage10_study_status after insert on public.study for each row execute function private.ensure_stage10_study_status();
insert into public.study_harms_status(study_id) select study_id from public.study on conflict(study_id) do nothing;

create or replace function private.ensure_stage10_component_status()
returns trigger language plpgsql security definer set search_path=public,pg_temp as $$
begin
  insert into public.component_implementation_status(component_id,dimension)
  select new.component_id, d from unnest(array[
    'provider','materials_procedures','delivery_mode','fidelity','adherence','tailoring','modification','support_dependence','implementation_burden','cost_resources'
  ]::text[]) d
  on conflict(component_id,dimension) do nothing;
  return new;
end; $$;
revoke all on function private.ensure_stage10_component_status() from public, anon, authenticated;
create trigger ensure_stage10_component_status after insert on public.intervention_component for each row execute function private.ensure_stage10_component_status();
insert into public.component_implementation_status(component_id,dimension)
select ic.component_id,d from public.intervention_component ic cross join unnest(array[
  'provider','materials_procedures','delivery_mode','fidelity','adherence','tailoring','modification','support_dependence','implementation_burden','cost_resources'
]::text[]) d on conflict(component_id,dimension) do nothing;

-- 8. Scientific integrity guards
create or replace function private.validate_stage10_study_links()
returns trigger language plpgsql security definer set search_path=public,pg_temp as $$
declare v_study bigint;
begin
  if tg_table_name='harm_observation' then
    if new.arm_id is not null then select study_id into v_study from public.study_arm where arm_id=new.arm_id; if v_study is distinct from new.study_id then raise exception 'Stage 10 harm arm/study mismatch'; end if; end if;
    if new.outcome_id is not null then select study_id into v_study from public.evidence_outcome where outcome_id=new.outcome_id; if v_study is distinct from new.study_id then raise exception 'Stage 10 harm outcome/study mismatch'; end if; end if;
    if new.contrast_id is not null then select study_id into v_study from public.study_contrast where contrast_id=new.contrast_id; if v_study is distinct from new.study_id then raise exception 'Stage 10 harm contrast/study mismatch'; end if; end if;
  elsif tg_table_name='support_dependence_observation' then
    if new.component_id is not null then select study_id into v_study from public.intervention_component where component_id=new.component_id; if v_study is distinct from new.study_id then raise exception 'Stage 10 support component/study mismatch'; end if; end if;
    if new.outcome_id is not null then select study_id into v_study from public.evidence_outcome where outcome_id=new.outcome_id; if v_study is distinct from new.study_id then raise exception 'Stage 10 support outcome/study mismatch'; end if; end if;
  else
    if new.component_id is not null then select study_id into v_study from public.intervention_component where component_id=new.component_id; if v_study is distinct from new.study_id then raise exception 'Stage 10 boundary component/study mismatch'; end if; end if;
    if new.outcome_id is not null then select study_id into v_study from public.evidence_outcome where outcome_id=new.outcome_id; if v_study is distinct from new.study_id then raise exception 'Stage 10 boundary outcome/study mismatch'; end if; end if;
  end if;
  return new;
end; $$;
revoke all on function private.validate_stage10_study_links() from public, anon, authenticated;
create trigger validate_stage10_harm_links before insert or update on public.harm_observation for each row execute function private.validate_stage10_study_links();
create trigger validate_stage10_support_links before insert or update on public.support_dependence_observation for each row execute function private.validate_stage10_study_links();
create trigger validate_stage10_boundary_links before insert or update on public.boundary_condition_observation for each row execute function private.validate_stage10_study_links();

create or replace function private.validate_stage10_component_reporting_framework()
returns trigger language plpgsql security definer set search_path=public,pg_temp as $$
declare v_subject text;
begin
  select subject_kind into v_subject from public.assessment_framework_definition where framework_key=new.framework_key;
  if v_subject not in ('component_reporting_or_fidelity','custom') then
    raise exception 'Framework % with subject_kind % cannot attach to component reporting/fidelity', new.framework_key, v_subject;
  end if;
  return new;
end; $$;
revoke all on function private.validate_stage10_component_reporting_framework() from public, anon, authenticated;
create trigger validate_stage10_component_reporting_framework before insert or update on public.component_reporting_assessment for each row execute function private.validate_stage10_component_reporting_framework();

create or replace function private.prevent_stage10_agent_self_approval()
returns trigger language plpgsql security definer set search_path=public,pg_temp as $$
begin
  if new.mapping_source='agent_candidate' and new.review_status='approved' then raise exception 'Stage 10 agent_candidate rows cannot self-promote to approved'; end if;
  return new;
end; $$;
revoke all on function private.prevent_stage10_agent_self_approval() from public, anon, authenticated;
create trigger prevent_stage10_agent_harm_status before insert or update on public.study_harms_status for each row execute function private.prevent_stage10_agent_self_approval();
create trigger prevent_stage10_agent_harm before insert or update on public.harm_observation for each row execute function private.prevent_stage10_agent_self_approval();
create trigger prevent_stage10_agent_participation before insert or update on public.study_participation_observation for each row execute function private.prevent_stage10_agent_self_approval();
create trigger prevent_stage10_agent_impl_status before insert or update on public.component_implementation_status for each row execute function private.prevent_stage10_agent_self_approval();
create trigger prevent_stage10_agent_impl_obs before insert or update on public.component_implementation_observation for each row execute function private.prevent_stage10_agent_self_approval();
create trigger prevent_stage10_agent_reporting before insert or update on public.component_reporting_assessment for each row execute function private.prevent_stage10_agent_self_approval();
create trigger prevent_stage10_agent_support before insert or update on public.support_dependence_observation for each row execute function private.prevent_stage10_agent_self_approval();
create trigger prevent_stage10_agent_boundary before insert or update on public.boundary_condition_observation for each row execute function private.prevent_stage10_agent_self_approval();

-- 9. RLS / Workbench grants
alter table public.harm_type_definition enable row level security;
alter table public.study_harms_status enable row level security;
alter table public.harm_observation enable row level security;
alter table public.study_participation_observation enable row level security;
alter table public.component_implementation_status enable row level security;
alter table public.component_implementation_observation enable row level security;
alter table public.component_reporting_assessment enable row level security;
alter table public.support_dependence_observation enable row level security;
alter table public.boundary_condition_observation enable row level security;

revoke all on table public.harm_type_definition from anon, authenticated;
revoke all on table public.study_harms_status from anon, authenticated;
revoke all on table public.harm_observation from anon, authenticated;
revoke all on table public.study_participation_observation from anon, authenticated;
revoke all on table public.component_implementation_status from anon, authenticated;
revoke all on table public.component_implementation_observation from anon, authenticated;
revoke all on table public.component_reporting_assessment from anon, authenticated;
revoke all on table public.support_dependence_observation from anon, authenticated;
revoke all on table public.boundary_condition_observation from anon, authenticated;

grant select on table public.harm_type_definition to authenticated, service_role;
grant select,insert,update,delete on table public.study_harms_status, public.harm_observation, public.study_participation_observation, public.component_implementation_status, public.component_implementation_observation, public.component_reporting_assessment, public.support_dependence_observation, public.boundary_condition_observation to authenticated, service_role;
grant usage,select on all sequences in schema public to authenticated, service_role;

create policy stage10_harm_type_read on public.harm_type_definition for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

-- helper pattern: readers viewer/editor/owner; writers editor/owner
create policy stage10_harms_status_read on public.study_harms_status for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy stage10_harms_status_write on public.study_harms_status for all to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[]))) with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy stage10_harm_read on public.harm_observation for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy stage10_harm_write on public.harm_observation for all to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[]))) with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy stage10_participation_read on public.study_participation_observation for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy stage10_participation_write on public.study_participation_observation for all to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[]))) with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy stage10_impl_status_read on public.component_implementation_status for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy stage10_impl_status_write on public.component_implementation_status for all to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[]))) with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy stage10_impl_obs_read on public.component_implementation_observation for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy stage10_impl_obs_write on public.component_implementation_observation for all to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[]))) with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy stage10_reporting_read on public.component_reporting_assessment for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy stage10_reporting_write on public.component_reporting_assessment for all to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[]))) with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy stage10_support_read on public.support_dependence_observation for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy stage10_support_write on public.support_dependence_observation for all to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[]))) with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy stage10_boundary_read on public.boundary_condition_observation for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy stage10_boundary_write on public.boundary_condition_observation for all to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[]))) with check ((select private.has_workbench_role(array['editor','owner']::text[])));

-- 10. Audit coverage
create trigger audit_study_harms_status after insert or update or delete on public.study_harms_status for each row execute function private.audit_workbench_change();
create trigger audit_harm_observation after insert or update or delete on public.harm_observation for each row execute function private.audit_workbench_change();
create trigger audit_study_participation after insert or update or delete on public.study_participation_observation for each row execute function private.audit_workbench_change();
create trigger audit_component_implementation_status after insert or update or delete on public.component_implementation_status for each row execute function private.audit_workbench_change();
create trigger audit_component_implementation_observation after insert or update or delete on public.component_implementation_observation for each row execute function private.audit_workbench_change();
create trigger audit_component_reporting_assessment after insert or update or delete on public.component_reporting_assessment for each row execute function private.audit_workbench_change();
create trigger audit_support_dependence_observation after insert or update or delete on public.support_dependence_observation for each row execute function private.audit_workbench_change();
create trigger audit_boundary_condition_observation after insert or update or delete on public.boundary_condition_observation for each row execute function private.audit_workbench_change();
