-- HRP Transfer Evidence Registry v1.1
-- Stage 7: typed study/report quality and result-specific risk of bias.
--
-- Scientific rules:
--   study/report quality != result-specific RoB != body-level certainty
--   reporting completeness != risk of bias
--   GRADE is body-level and remains structurally reserved for Stage 8
--   absence of an assessment row != low risk / high quality
--
-- Additive only: historical public.quality_assessment remains compatibility data.

-- ===========================================================================
-- 1. Controlled assessment framework registry
-- ===========================================================================

create table public.assessment_framework_definition (
  framework_key text primary key,
  label text not null,
  framework_family text not null,
  subject_kind text not null check (
    subject_kind in (
      'study_methodological_quality',
      'study_reporting_completeness',
      'study_review_methodology',
      'study_measurement_quality',
      'result_risk_of_bias',
      'component_reporting_or_fidelity',
      'body_certainty_reserved',
      'custom'
    )
  ),
  version_label text,
  publisher_or_owner text,
  description text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

insert into public.assessment_framework_definition (
  framework_key, label, framework_family, subject_kind, publisher_or_owner, description
) values
  ('rob2', 'RoB 2', 'risk_of_bias', 'result_risk_of_bias', 'Cochrane', 'Risk-of-bias framework for a specific randomized-trial result/estimand.'),
  ('robins_i', 'ROBINS-I', 'risk_of_bias', 'result_risk_of_bias', 'Cochrane', 'Risk-of-bias framework for a specific non-randomized intervention result.'),
  ('robis', 'ROBIS', 'review_methodology', 'study_review_methodology', 'University of Bristol / collaborators', 'Risk-of-bias framework for systematic reviews; applies to the review study/report subject.'),
  ('amstar2', 'AMSTAR 2', 'review_methodology', 'study_review_methodology', 'AMSTAR', 'Critical appraisal of systematic reviews of healthcare interventions.'),
  ('consort', 'CONSORT', 'reporting', 'study_reporting_completeness', 'CONSORT Group', 'Randomized-trial reporting guidance/checklist; not itself a risk-of-bias judgement.'),
  ('prisma', 'PRISMA', 'reporting', 'study_reporting_completeness', 'PRISMA Group', 'Systematic-review reporting guidance/checklist; not itself a body-certainty judgement.'),
  ('tidier', 'TIDieR', 'reporting_fidelity', 'component_reporting_or_fidelity', 'TIDieR Group', 'Intervention description/reporting framework; reserved for component/fidelity use and Stage 10 expansion.'),
  ('cosmin', 'COSMIN', 'measurement_quality', 'study_measurement_quality', 'COSMIN initiative', 'Measurement-property methodological/quality framework where scientifically appropriate.'),
  ('grade', 'GRADE', 'body_certainty', 'body_certainty_reserved', 'GRADE Working Group', 'Body-of-evidence certainty framework. Registered for vocabulary only; Stage 7 provides no source/study/result attachment path.'),
  ('custom', 'Custom / other', 'custom', 'custom', null, 'Explicitly described custom framework where a standard registered framework is not appropriate.');

-- ===========================================================================
-- 2. Explicit assessment state per scientific subject
-- ===========================================================================

create table public.study_quality_status (
  study_id bigint primary key references public.study(study_id) on delete cascade,
  assessment_status text not null default 'not_yet_assessed' check (
    assessment_status in (
      'not_yet_assessed','assessment_in_progress','partially_assessed',
      'reviewed_complete','not_applicable'
    )
  ),
  mapping_source text not null default 'migration' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.result_rob_status (
  outcome_id bigint primary key references public.evidence_outcome(outcome_id) on delete cascade,
  assessment_status text not null default 'not_yet_assessed' check (
    assessment_status in (
      'not_yet_assessed','assessment_in_progress','partially_assessed',
      'reviewed_complete','not_applicable'
    )
  ),
  mapping_source text not null default 'migration' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ===========================================================================
-- 3. Study/report-level typed assessment
-- ===========================================================================

create table public.study_quality_assessment (
  study_quality_assessment_id bigserial primary key,
  study_id bigint not null references public.study(study_id) on delete cascade,
  assessment_key text not null,
  assessment_kind text not null check (
    assessment_kind in (
      'methodological_quality','reporting_completeness','review_methodology',
      'measurement_quality','other'
    )
  ),
  framework_key text not null references public.assessment_framework_definition(framework_key),
  framework_version text,
  overall_judgement text,
  assessment_status text not null default 'assessment_in_progress' check (
    assessment_status in (
      'assessment_in_progress','partially_assessed','reviewed_complete',
      'insufficient_information','not_applicable'
    )
  ),
  notes text,
  assessor text,
  assessed_on date,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (study_id, assessment_key)
);

create index study_quality_assessment_study_idx on public.study_quality_assessment(study_id);
create index study_quality_assessment_framework_idx on public.study_quality_assessment(framework_key);

-- ===========================================================================
-- 4. Result-specific risk-of-bias assessment
-- ===========================================================================

create table public.result_risk_of_bias_assessment (
  result_rob_assessment_id bigserial primary key,
  outcome_id bigint not null references public.evidence_outcome(outcome_id) on delete cascade,
  contrast_id bigint references public.study_contrast(contrast_id) on delete cascade,
  effect_estimate_id bigint references public.effect_estimate(effect_estimate_id) on delete cascade,
  assessment_key text not null,
  framework_key text not null references public.assessment_framework_definition(framework_key),
  framework_version text,
  estimand_or_result_scope text,
  overall_judgement text,
  assessment_status text not null default 'assessment_in_progress' check (
    assessment_status in (
      'assessment_in_progress','partially_assessed','reviewed_complete',
      'insufficient_information','not_applicable'
    )
  ),
  notes text,
  assessor text,
  assessed_on date,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (outcome_id, assessment_key)
);

create index result_rob_assessment_outcome_idx on public.result_risk_of_bias_assessment(outcome_id);
create index result_rob_assessment_contrast_idx on public.result_risk_of_bias_assessment(contrast_id);
create index result_rob_assessment_effect_idx on public.result_risk_of_bias_assessment(effect_estimate_id);
create index result_rob_assessment_framework_idx on public.result_risk_of_bias_assessment(framework_key);

-- ===========================================================================
-- 5. Domain judgements with real foreign-key subjects
-- ===========================================================================

create table public.assessment_domain_judgement (
  assessment_domain_judgement_id bigserial primary key,
  study_quality_assessment_id bigint references public.study_quality_assessment(study_quality_assessment_id) on delete cascade,
  result_rob_assessment_id bigint references public.result_risk_of_bias_assessment(result_rob_assessment_id) on delete cascade,
  domain_key text not null,
  domain_label text not null,
  judgement text not null,
  supporting_text text,
  notes text,
  order_index integer,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (
    (study_quality_assessment_id is not null and result_rob_assessment_id is null)
    or
    (study_quality_assessment_id is null and result_rob_assessment_id is not null)
  )
);

create unique index assessment_domain_study_unique_idx
  on public.assessment_domain_judgement(study_quality_assessment_id, domain_key)
  where study_quality_assessment_id is not null;
create unique index assessment_domain_result_unique_idx
  on public.assessment_domain_judgement(result_rob_assessment_id, domain_key)
  where result_rob_assessment_id is not null;

-- ===========================================================================
-- 6. Framework/subject and cross-link integrity guards
-- ===========================================================================

create or replace function private.validate_stage7_study_quality_framework()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  subject text;
begin
  select afd.subject_kind into subject
  from public.assessment_framework_definition afd
  where afd.framework_key = new.framework_key;

  if subject is null then
    raise exception 'Unknown Stage 7 framework %', new.framework_key;
  end if;

  if subject in ('result_risk_of_bias','component_reporting_or_fidelity','body_certainty_reserved') then
    raise exception 'Framework % with subject_kind % cannot be attached to study_quality_assessment', new.framework_key, subject;
  end if;

  if new.assessment_kind = 'methodological_quality' and subject not in ('study_methodological_quality','custom') then
    raise exception 'Framework % is incompatible with methodological_quality', new.framework_key;
  elsif new.assessment_kind = 'reporting_completeness' and subject not in ('study_reporting_completeness','custom') then
    raise exception 'Framework % is incompatible with reporting_completeness', new.framework_key;
  elsif new.assessment_kind = 'review_methodology' and subject not in ('study_review_methodology','custom') then
    raise exception 'Framework % is incompatible with review_methodology', new.framework_key;
  elsif new.assessment_kind = 'measurement_quality' and subject not in ('study_measurement_quality','custom') then
    raise exception 'Framework % is incompatible with measurement_quality', new.framework_key;
  elsif new.assessment_kind = 'other' and subject <> 'custom' then
    raise exception 'assessment_kind=other requires framework_key=custom';
  end if;

  return new;
end;
$$;

revoke all on function private.validate_stage7_study_quality_framework() from public, anon, authenticated;
create trigger validate_stage7_study_quality_framework
before insert or update on public.study_quality_assessment
for each row execute function private.validate_stage7_study_quality_framework();

create or replace function private.validate_stage7_result_rob_link()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  subject text;
  outcome_study_id bigint;
  contrast_study_id bigint;
  effect_outcome_id bigint;
  effect_contrast_id bigint;
  effect_scope text;
begin
  select afd.subject_kind into subject
  from public.assessment_framework_definition afd
  where afd.framework_key = new.framework_key;

  if subject not in ('result_risk_of_bias','custom') then
    raise exception 'Framework % with subject_kind % cannot be attached to a result risk-of-bias assessment', new.framework_key, subject;
  end if;

  select eo.study_id into outcome_study_id
  from public.evidence_outcome eo
  where eo.outcome_id = new.outcome_id;

  if new.contrast_id is not null then
    select sc.study_id into contrast_study_id
    from public.study_contrast sc
    where sc.contrast_id = new.contrast_id;
    if contrast_study_id is distinct from outcome_study_id then
      raise exception 'Stage 7 RoB contrast/outcome cross-study mismatch: outcome %, contrast %', new.outcome_id, new.contrast_id;
    end if;
  end if;

  if new.effect_estimate_id is not null then
    select ee.outcome_id, ee.contrast_id, ee.estimate_scope
      into effect_outcome_id, effect_contrast_id, effect_scope
    from public.effect_estimate ee
    where ee.effect_estimate_id = new.effect_estimate_id;

    if effect_outcome_id is distinct from new.outcome_id then
      raise exception 'Stage 7 RoB effect/outcome mismatch: effect %, outcome %', new.effect_estimate_id, new.outcome_id;
    end if;
    if new.contrast_id is not null and effect_contrast_id is distinct from new.contrast_id then
      raise exception 'Stage 7 RoB effect/contrast mismatch: effect %, contrast %', new.effect_estimate_id, new.contrast_id;
    end if;
    if effect_scope = 'source_level_synthesis' then
      raise exception 'Source-level synthesis effect % requires review/body-level appraisal, not trial-result RoB', new.effect_estimate_id;
    end if;
  end if;

  return new;
end;
$$;

revoke all on function private.validate_stage7_result_rob_link() from public, anon, authenticated;
create trigger validate_stage7_result_rob_link
before insert or update on public.result_risk_of_bias_assessment
for each row execute function private.validate_stage7_result_rob_link();

-- ===========================================================================
-- 7. Deterministic status rows after importer replay
-- ===========================================================================

create or replace function private.ensure_stage7_study_quality_status()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  insert into public.study_quality_status (study_id, notes)
  values (new.study_id, 'Stage 7 study-quality status created from normalized study; no quality judgement inferred.')
  on conflict (study_id) do nothing;
  return new;
end;
$$;

revoke all on function private.ensure_stage7_study_quality_status() from public, anon, authenticated;
create trigger ensure_stage7_study_quality_status
after insert on public.study
for each row execute function private.ensure_stage7_study_quality_status();

create or replace function private.ensure_stage7_result_rob_status()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  insert into public.result_rob_status (outcome_id, notes)
  values (new.outcome_id, 'Stage 7 result-RoB status created from normalized outcome; no risk-of-bias judgement inferred.')
  on conflict (outcome_id) do nothing;
  return new;
end;
$$;

revoke all on function private.ensure_stage7_result_rob_status() from public, anon, authenticated;
create trigger ensure_stage7_result_rob_status
after insert on public.evidence_outcome
for each row execute function private.ensure_stage7_result_rob_status();

insert into public.study_quality_status (study_id, notes)
select s.study_id, 'Stage 7 study-quality status created for pre-existing normalized study; no quality judgement inferred.'
from public.study s
on conflict (study_id) do nothing;

insert into public.result_rob_status (outcome_id, notes)
select eo.outcome_id, 'Stage 7 result-RoB status created for pre-existing normalized outcome; no risk-of-bias judgement inferred.'
from public.evidence_outcome eo
on conflict (outcome_id) do nothing;

-- ===========================================================================
-- 8. RLS, Workbench grants and audit coverage
-- ===========================================================================

alter table public.assessment_framework_definition enable row level security;
alter table public.study_quality_status enable row level security;
alter table public.result_rob_status enable row level security;
alter table public.study_quality_assessment enable row level security;
alter table public.result_risk_of_bias_assessment enable row level security;
alter table public.assessment_domain_judgement enable row level security;

revoke all on table public.assessment_framework_definition from anon, authenticated;
revoke all on table public.study_quality_status from anon, authenticated;
revoke all on table public.result_rob_status from anon, authenticated;
revoke all on table public.study_quality_assessment from anon, authenticated;
revoke all on table public.result_risk_of_bias_assessment from anon, authenticated;
revoke all on table public.assessment_domain_judgement from anon, authenticated;

grant select on table public.assessment_framework_definition to service_role, authenticated;
grant select, insert, update, delete on table public.study_quality_status to service_role, authenticated;
grant select, insert, update, delete on table public.result_rob_status to service_role, authenticated;
grant select, insert, update, delete on table public.study_quality_assessment to service_role, authenticated;
grant select, insert, update, delete on table public.result_risk_of_bias_assessment to service_role, authenticated;
grant select, insert, update, delete on table public.assessment_domain_judgement to service_role, authenticated;
grant usage, select on sequence public.study_quality_assessment_study_quality_assessment_id_seq to service_role, authenticated;
grant usage, select on sequence public.result_risk_of_bias_assessment_result_rob_assessment_id_seq to service_role, authenticated;
grant usage, select on sequence public.assessment_domain_judgement_assessment_domain_judgement_id_seq to service_role, authenticated;

create policy assessment_framework_workbench_read
on public.assessment_framework_definition for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy study_quality_status_workbench_read
on public.study_quality_status for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy result_rob_status_workbench_read
on public.result_rob_status for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy study_quality_assessment_workbench_read
on public.study_quality_assessment for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy result_rob_assessment_workbench_read
on public.result_risk_of_bias_assessment for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy assessment_domain_workbench_read
on public.assessment_domain_judgement for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy study_quality_status_workbench_update
on public.study_quality_status for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy result_rob_status_workbench_update
on public.result_rob_status for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy study_quality_assessment_workbench_insert
on public.study_quality_assessment for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy study_quality_assessment_workbench_update
on public.study_quality_assessment for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy study_quality_assessment_workbench_delete
on public.study_quality_assessment for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy result_rob_assessment_workbench_insert
on public.result_risk_of_bias_assessment for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy result_rob_assessment_workbench_update
on public.result_risk_of_bias_assessment for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy result_rob_assessment_workbench_delete
on public.result_risk_of_bias_assessment for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy assessment_domain_workbench_insert
on public.assessment_domain_judgement for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy assessment_domain_workbench_update
on public.assessment_domain_judgement for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy assessment_domain_workbench_delete
on public.assessment_domain_judgement for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create trigger audit_study_quality_status
after insert or update or delete on public.study_quality_status
for each row execute function private.audit_workbench_change();
create trigger audit_result_rob_status
after insert or update or delete on public.result_rob_status
for each row execute function private.audit_workbench_change();
create trigger audit_study_quality_assessment
after insert or update or delete on public.study_quality_assessment
for each row execute function private.audit_workbench_change();
create trigger audit_result_rob_assessment
after insert or update or delete on public.result_risk_of_bias_assessment
for each row execute function private.audit_workbench_change();
create trigger audit_assessment_domain_judgement
after insert or update or delete on public.assessment_domain_judgement
for each row execute function private.audit_workbench_change();
