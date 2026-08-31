-- HRP Transfer Evidence Registry v1.1
-- Stage 9: orthogonal population/context facets, explicit extraction status,
-- component delivery-context mappings, and proposition-relative context fit.
--
-- Scientific rule:
--   life stage != role != health context != cognitive status != education
--   != setting != delivery context != geography != application family.
--
-- Raw population_summary, population_tags, study.setting and component delivery
-- fields are retained as compatibility/source text. Stage 9 adds normalized lenses.

-- ===========================================================================
-- 1. Controlled population/context ontology
-- ===========================================================================

create table public.population_context_term (
  term_id text primary key,
  facet_kind text not null check (
    facet_kind in (
      'life_stage','role','health_condition_context','baseline_cognitive_status',
      'education_level','study_setting','delivery_context','geography'
    )
  ),
  canonical_label text not null,
  description text not null,
  parent_term_id text references public.population_context_term(term_id) on delete restrict,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  unique (facet_kind, canonical_label)
);

comment on table public.population_context_term is
'Orthogonal controlled terms for population and context matching. Application family remains a separate Stage 3 many-to-many lens.';

insert into public.population_context_term (term_id, facet_kind, canonical_label, description, parent_term_id) values
-- life stage
('pc_life_child','life_stage','child','Child participants where childhood is explicit in the reviewed record.',null),
('pc_life_young_adult','life_stage','young_adult','Young-adult participants where explicitly reported or coded in the reviewed record.',null),
('pc_life_adult','life_stage','adult','Adult participants without a more specific life-stage classification.',null),
('pc_life_older_adult','life_stage','older_adult','Older-adult participants where explicitly reported or coded in the reviewed record.',null),
-- role
('pc_role_student','role','student','Learner/student role in an educational or study context.',null),
('pc_role_university_student','role','university_student','Student enrolled in higher education or explicitly described as an undergraduate/university student.','pc_role_student'),
('pc_role_school_student','role','school_student','Student/pupil in a school setting.','pc_role_student'),
('pc_role_early_career_knowledge_worker','role','early_career_knowledge_worker','Early-career worker engaged primarily in knowledge work.',null),
-- health / condition context
('pc_health_healthy_nonclinical','health_condition_context','healthy_or_nonclinical','Participants explicitly described as healthy/nonclinical or coded healthy in the reviewed record.',null),
('pc_health_learning_difficulties','health_condition_context','learning_difficulties','Participants explicitly described as having learning difficulties.',null),
-- baseline cognitive status
('pc_cog_cognitively_normal','baseline_cognitive_status','cognitively_normal','Participants explicitly described as cognitively normal.',null),
-- education level
('pc_edu_kindergarten','education_level','kindergarten','Kindergarten / early-years formal education context.',null),
('pc_edu_school','education_level','school_education','School-level education where a more specific stage is not required.',null),
('pc_edu_middle_school','education_level','middle_school','Middle-school education context.','pc_edu_school'),
('pc_edu_higher','education_level','higher_education','University/undergraduate/higher-education context.',null),
-- study setting
('pc_setting_research_training','study_setting','research_training_setting','Research intervention/training context without a more precise environment asserted.',null),
('pc_setting_controlled_research','study_setting','controlled_research','Controlled experimental/research setting.',null),
('pc_setting_school','study_setting','school','School setting.',null),
('pc_setting_university_classroom','study_setting','university_classroom','University classroom setting.',null),
('pc_setting_community','study_setting','community','Community-based setting.',null),
('pc_setting_online','study_setting','online_remote','Online/remote study setting.',null),
('pc_setting_lab','study_setting','laboratory','Laboratory setting.',null),
('pc_setting_evidence_synthesis','study_setting','evidence_synthesis','Study row represents a review/synthesis rather than a primary participant setting.',null),
-- delivery context
('pc_delivery_guided_training','delivery_context','guided_training','Training delivered with explicit guidance.',null),
('pc_delivery_researcher_facilitated','delivery_context','researcher_facilitated','Delivery explicitly facilitated by a researcher.',null),
('pc_delivery_tablet_game','delivery_context','tablet_game','Training delivered through tablet-game activities.',null),
('pc_delivery_structured_task_training','delivery_context','structured_task_training','Structured task-based training protocol.',null),
-- geography
('pc_geo_china','geography','china','China / Chinese setting or population where explicit in the reviewed record.',null);

-- ===========================================================================
-- 2. Per-study facet extraction status
-- ===========================================================================

create table public.study_population_context_status (
  study_id bigint not null references public.study(study_id) on delete cascade,
  facet_kind text not null check (
    facet_kind in (
      'life_stage','role','health_condition_context','baseline_cognitive_status',
      'education_level','study_setting','geography'
    )
  ),
  extraction_status text not null check (
    extraction_status in (
      'not_yet_extracted','candidate_mapped','reviewed_mapped',
      'reviewed_no_mapping','not_reported','not_applicable'
    )
  ),
  notes text,
  mapping_source text not null default 'migration' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  updated_at timestamptz not null default now(),
  primary key (study_id, facet_kind)
);

create table public.study_population_context_term (
  study_id bigint not null references public.study(study_id) on delete cascade,
  term_id text not null references public.population_context_term(term_id) on delete restrict,
  relationship text not null check (
    relationship in ('entire_sample','includes_subgroup','study_context','unclear_scope')
  ),
  evidence_basis text not null,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (study_id, term_id, relationship)
);

create index study_population_context_term_term_idx on public.study_population_context_term(term_id);
create index study_population_context_term_review_idx on public.study_population_context_term(review_status, mapping_source);

-- ===========================================================================
-- 3. Component-level delivery-context status/mapping
-- ===========================================================================

create table public.component_delivery_context_status (
  component_id bigint primary key references public.intervention_component(component_id) on delete cascade,
  extraction_status text not null check (
    extraction_status in (
      'not_yet_extracted','candidate_mapped','reviewed_mapped',
      'reviewed_no_mapping','not_reported','not_applicable'
    )
  ),
  notes text,
  mapping_source text not null default 'migration' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  updated_at timestamptz not null default now()
);

create table public.component_delivery_context_term (
  component_id bigint not null references public.intervention_component(component_id) on delete cascade,
  term_id text not null references public.population_context_term(term_id) on delete restrict,
  evidence_basis text not null,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (component_id, term_id)
);

create index component_delivery_context_term_term_idx on public.component_delivery_context_term(term_id);

-- ===========================================================================
-- 4. Proposition-relative context fit / boundary assessment
-- ===========================================================================

create table public.context_fit_assessment (
  context_fit_assessment_id bigserial primary key,
  proposition_id bigint not null references public.evidence_proposition(proposition_id) on delete cascade,
  study_id bigint not null references public.study(study_id) on delete cascade,
  fit_dimension text not null check (
    fit_dimension in (
      'population','role','health_condition_context','baseline_cognitive_status',
      'education','setting','delivery','geography','overall_context'
    )
  ),
  fit_judgement text not null check (
    fit_judgement in ('direct_match','close_match','partial_match','distant_match','not_assessed')
  ),
  boundary_summary text,
  rationale text not null,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (proposition_id, study_id, fit_dimension)
);

comment on table public.context_fit_assessment is
'Proposition-relative matching/boundary assessment. Context fit is not study quality, RoB, GRADE certainty, effect magnitude, application family, or EML.';

create index context_fit_proposition_idx on public.context_fit_assessment(proposition_id);
create index context_fit_study_idx on public.context_fit_assessment(study_id);

-- ===========================================================================
-- 5. Integrity and default-status triggers
-- ===========================================================================

create or replace function private.ensure_stage9_study_status()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
  insert into public.study_population_context_status (study_id, facet_kind, extraction_status, mapping_source, review_status)
  select new.study_id, facet_kind, 'not_yet_extracted', 'migration', 'proposed'
  from unnest(array[
    'life_stage','role','health_condition_context','baseline_cognitive_status',
    'education_level','study_setting','geography'
  ]::text[]) facet_kind
  on conflict (study_id, facet_kind) do nothing;
  return new;
end;
$$;

revoke all on function private.ensure_stage9_study_status() from public, anon, authenticated;
create trigger ensure_stage9_study_status
after insert on public.study
for each row execute function private.ensure_stage9_study_status();

insert into public.study_population_context_status (study_id, facet_kind, extraction_status, mapping_source, review_status)
select s.study_id, f.facet_kind, 'not_yet_extracted', 'migration', 'proposed'
from public.study s
cross join unnest(array[
  'life_stage','role','health_condition_context','baseline_cognitive_status',
  'education_level','study_setting','geography'
]::text[]) f(facet_kind)
on conflict (study_id, facet_kind) do nothing;

create or replace function private.ensure_stage9_component_delivery_status()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
  insert into public.component_delivery_context_status (component_id, extraction_status, mapping_source, review_status)
  values (new.component_id, 'not_yet_extracted', 'migration', 'proposed')
  on conflict (component_id) do nothing;
  return new;
end;
$$;

revoke all on function private.ensure_stage9_component_delivery_status() from public, anon, authenticated;
create trigger ensure_stage9_component_delivery_status
after insert on public.intervention_component
for each row execute function private.ensure_stage9_component_delivery_status();

insert into public.component_delivery_context_status (component_id, extraction_status, mapping_source, review_status)
select component_id, 'not_yet_extracted', 'migration', 'proposed'
from public.intervention_component
on conflict (component_id) do nothing;

create or replace function private.validate_stage9_study_term_facet()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_facet text;
begin
  select facet_kind into v_facet from public.population_context_term where term_id=new.term_id;
  if v_facet = 'delivery_context' then
    raise exception 'Delivery-context term % must attach to a component, not a study population/context mapping', new.term_id;
  end if;
  return new;
end;
$$;

revoke all on function private.validate_stage9_study_term_facet() from public, anon, authenticated;
create trigger validate_stage9_study_term_facet
before insert or update on public.study_population_context_term
for each row execute function private.validate_stage9_study_term_facet();

create or replace function private.validate_stage9_component_delivery_term()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_facet text;
begin
  select facet_kind into v_facet from public.population_context_term where term_id=new.term_id;
  if v_facet <> 'delivery_context' then
    raise exception 'Component delivery mapping requires delivery_context term; got % (%)', new.term_id, v_facet;
  end if;
  return new;
end;
$$;

revoke all on function private.validate_stage9_component_delivery_term() from public, anon, authenticated;
create trigger validate_stage9_component_delivery_term
before insert or update on public.component_delivery_context_term
for each row execute function private.validate_stage9_component_delivery_term();

create or replace function private.prevent_stage9_agent_self_approval()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if new.mapping_source='agent_candidate' and new.review_status='approved' then
    raise exception 'Stage 9 agent_candidate rows cannot self-promote to approved';
  end if;
  return new;
end;
$$;

revoke all on function private.prevent_stage9_agent_self_approval() from public, anon, authenticated;
create trigger prevent_stage9_agent_study_term_approval before insert or update on public.study_population_context_term for each row execute function private.prevent_stage9_agent_self_approval();
create trigger prevent_stage9_agent_study_status_approval before insert or update on public.study_population_context_status for each row execute function private.prevent_stage9_agent_self_approval();
create trigger prevent_stage9_agent_component_term_approval before insert or update on public.component_delivery_context_term for each row execute function private.prevent_stage9_agent_self_approval();
create trigger prevent_stage9_agent_component_status_approval before insert or update on public.component_delivery_context_status for each row execute function private.prevent_stage9_agent_self_approval();
create trigger prevent_stage9_agent_context_fit_approval before insert or update on public.context_fit_assessment for each row execute function private.prevent_stage9_agent_self_approval();

-- ===========================================================================
-- 6. RLS, grants and audit
-- ===========================================================================

alter table public.population_context_term enable row level security;
alter table public.study_population_context_status enable row level security;
alter table public.study_population_context_term enable row level security;
alter table public.component_delivery_context_status enable row level security;
alter table public.component_delivery_context_term enable row level security;
alter table public.context_fit_assessment enable row level security;

revoke all on table public.population_context_term from anon, authenticated;
revoke all on table public.study_population_context_status from anon, authenticated;
revoke all on table public.study_population_context_term from anon, authenticated;
revoke all on table public.component_delivery_context_status from anon, authenticated;
revoke all on table public.component_delivery_context_term from anon, authenticated;
revoke all on table public.context_fit_assessment from anon, authenticated;

grant select on table public.population_context_term to authenticated, service_role;
grant select, insert, update, delete on table public.study_population_context_status to authenticated, service_role;
grant select, insert, update, delete on table public.study_population_context_term to authenticated, service_role;
grant select, insert, update, delete on table public.component_delivery_context_status to authenticated, service_role;
grant select, insert, update, delete on table public.component_delivery_context_term to authenticated, service_role;
grant select, insert, update, delete on table public.context_fit_assessment to authenticated, service_role;
grant usage, select on sequence public.context_fit_assessment_context_fit_assessment_id_seq to authenticated, service_role;

create policy population_context_term_workbench_read on public.population_context_term for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy study_population_context_status_read on public.study_population_context_status for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy study_population_context_status_write on public.study_population_context_status for all to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[]))) with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy study_population_context_term_read on public.study_population_context_term for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy study_population_context_term_write on public.study_population_context_term for all to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[]))) with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy component_delivery_context_status_read on public.component_delivery_context_status for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy component_delivery_context_status_write on public.component_delivery_context_status for all to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[]))) with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy component_delivery_context_term_read on public.component_delivery_context_term for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy component_delivery_context_term_write on public.component_delivery_context_term for all to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[]))) with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy context_fit_assessment_read on public.context_fit_assessment for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy context_fit_assessment_write on public.context_fit_assessment for all to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[]))) with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create trigger audit_study_population_context_status after insert or update or delete on public.study_population_context_status for each row execute function private.audit_workbench_change();
create trigger audit_study_population_context_term after insert or update or delete on public.study_population_context_term for each row execute function private.audit_workbench_change();
create trigger audit_component_delivery_context_status after insert or update or delete on public.component_delivery_context_status for each row execute function private.audit_workbench_change();
create trigger audit_component_delivery_context_term after insert or update or delete on public.component_delivery_context_term for each row execute function private.audit_workbench_change();
create trigger audit_context_fit_assessment after insert or update or delete on public.context_fit_assessment for each row execute function private.audit_workbench_change();
