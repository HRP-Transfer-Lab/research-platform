-- HRP Transfer Evidence Registry v1.1
-- Stage 8: propositions, result/source contributions, synthesis outcomes,
-- body certainty, body-level EML and governed approved claims.
--
-- Scientific rules:
--   source contribution != proposition != synthesis outcome
--   GRADE/body certainty != EML
--   effect direction/magnitude != maturity
--   source EML != body EML
--   source-level pooled estimate != fabricated Stage 5 contrast
--
-- Additive only. Historical evidence_synthesis/synthesis_source/approved_claim
-- and source-level evidence_maturity_assessment rows remain unchanged.

-- ===========================================================================
-- 1. Explicit Stage 8 body-curation state
-- ===========================================================================

create table public.body_evidence_stage8_status (
  scope_key text primary key,
  curation_status text not null check (
    curation_status in ('not_yet_curated','curation_in_progress','partially_curated','reviewed_complete')
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

insert into public.body_evidence_stage8_status (
  scope_key, curation_status, mapping_source, review_status, notes
) values (
  'seed_body_curation',
  'not_yet_curated',
  'migration',
  'proposed',
  'The immutable 2026-08-23 seed contains no curated body-level proposition, synthesis, certainty, EML or claim; none is inferred.'
)
on conflict (scope_key) do nothing;

-- ===========================================================================
-- 2. First-class evidence proposition
-- ===========================================================================

create table public.evidence_proposition (
  proposition_id bigserial primary key,
  proposition_key text not null unique,
  label text not null,
  intervention_or_exposure text not null,
  comparator_scope text,
  population_scope text not null,
  context_scope text,
  target_or_outcome_scope text not null,
  timeframe_scope text,
  route_scope text[] not null default '{}',
  proposition_text text not null,
  status text not null default 'draft' check (
    status in ('draft','reviewing','reviewed','approved','retired')
  ),
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.evidence_proposition is
'Body-level scientific question/claim scope. Proposition scope is distinct from source identity, synthesis result, certainty and maturity.';

-- ===========================================================================
-- 3. Result/source contribution to proposition
-- ===========================================================================

create table public.proposition_evidence_contribution (
  contribution_id bigserial primary key,
  proposition_id bigint not null references public.evidence_proposition(proposition_id) on delete cascade,
  contribution_key text not null,

  source_version_id text references public.source_version(source_version_id) on delete restrict,
  source_id text references public.evidence_source(source_id) on delete restrict,
  study_id bigint references public.study(study_id) on delete restrict,
  outcome_id bigint references public.evidence_outcome(outcome_id) on delete restrict,
  contrast_id bigint references public.study_contrast(contrast_id) on delete restrict,
  effect_estimate_id bigint references public.effect_estimate(effect_estimate_id) on delete restrict,

  contribution_role text not null check (
    contribution_role in (
      'direct_support','direct_null','direct_harm','boundary_condition',
      'mechanism_support','measurement_support','implementation_support',
      'synthesis_support','contradictory','contextual','other'
    )
  ),
  result_direction text check (
    result_direction is null or result_direction in (
      'supportive','null','harmful','mixed','uncertain','not_applicable'
    )
  ),
  inclusion_status text not null default 'candidate' check (
    inclusion_status in ('candidate','included','excluded','deferred')
  ),
  inclusion_reason text,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (proposition_id, contribution_key),
  check (num_nonnulls(source_version_id, source_id) >= 1),
  check (contrast_id is null or outcome_id is not null),
  check (effect_estimate_id is null or outcome_id is not null)
);

create index proposition_contribution_proposition_idx on public.proposition_evidence_contribution(proposition_id);
create index proposition_contribution_source_version_idx on public.proposition_evidence_contribution(source_version_id) where source_version_id is not null;
create index proposition_contribution_source_idx on public.proposition_evidence_contribution(source_id) where source_id is not null;
create index proposition_contribution_study_idx on public.proposition_evidence_contribution(study_id) where study_id is not null;
create index proposition_contribution_outcome_idx on public.proposition_evidence_contribution(outcome_id) where outcome_id is not null;
create index proposition_contribution_contrast_idx on public.proposition_evidence_contribution(contrast_id) where contrast_id is not null;
create index proposition_contribution_effect_idx on public.proposition_evidence_contribution(effect_estimate_id) where effect_estimate_id is not null;

-- ===========================================================================
-- 4. Body synthesis process / assembly
-- ===========================================================================

create table public.body_evidence_synthesis (
  body_synthesis_id bigserial primary key,
  synthesis_key text not null unique,
  proposition_id bigint not null references public.evidence_proposition(proposition_id) on delete cascade,
  title text not null,
  synthesis_kind text not null check (
    synthesis_kind in (
      'systematic_review_meta_analysis','systematic_review_narrative','rapid_review',
      'scoping_review','structured_internal_synthesis','living_synthesis','other'
    )
  ),
  method_summary text not null,
  search_or_selection_basis text,
  status text not null default 'draft' check (
    status in ('draft','reviewing','reviewed','approved','retired')
  ),
  version text not null,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index body_synthesis_proposition_idx on public.body_evidence_synthesis(proposition_id);

-- ===========================================================================
-- 5. Outcome-specific synthesis conclusion
-- ===========================================================================

create table public.synthesis_outcome (
  synthesis_outcome_id bigserial primary key,
  body_synthesis_id bigint not null references public.body_evidence_synthesis(body_synthesis_id) on delete cascade,
  proposition_id bigint not null references public.evidence_proposition(proposition_id) on delete cascade,
  outcome_key text not null,
  outcome_label text not null,
  conclusion_direction text not null check (
    conclusion_direction in ('supportive','null','harmful','mixed','uncertain','not_applicable')
  ),
  conclusion_summary text not null,

  estimate_type text check (
    estimate_type is null or estimate_type in (
      'raw_mean','raw_proportion','change_score','mean_difference',
      'standardised_mean_difference','odds_ratio','risk_ratio','hazard_ratio',
      'correlation','regression_coefficient','rate_ratio','other'
    )
  ),
  metric text,
  pooled_estimate numeric,
  standard_error numeric,
  ci_level numeric check (ci_level is null or (ci_level > 0 and ci_level <= 1)),
  ci_lower numeric,
  ci_upper numeric,
  p_value numeric check (p_value is null or (p_value >= 0 and p_value <= 1)),
  heterogeneity_metric text,
  heterogeneity_value numeric,
  included_study_count integer check (included_study_count is null or included_study_count >= 0),
  included_result_count integer check (included_result_count is null or included_result_count >= 0),

  status text not null default 'draft' check (
    status in ('draft','reviewing','reviewed','approved','retired')
  ),
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (body_synthesis_id, outcome_key),
  check (ci_lower is null or ci_upper is null or ci_lower <= ci_upper),
  check (pooled_estimate is not null or metric is null),
  check (pooled_estimate is not null or estimate_type is null)
);

create index synthesis_outcome_body_synthesis_idx on public.synthesis_outcome(body_synthesis_id);
create index synthesis_outcome_proposition_idx on public.synthesis_outcome(proposition_id);
create index synthesis_outcome_direction_idx on public.synthesis_outcome(conclusion_direction);

-- ===========================================================================
-- 6. Body-level certainty (GRADE and future body frameworks)
-- ===========================================================================

create table public.body_certainty_assessment (
  body_certainty_assessment_id bigserial primary key,
  synthesis_outcome_id bigint not null references public.synthesis_outcome(synthesis_outcome_id) on delete cascade,
  framework_key text not null references public.assessment_framework_definition(framework_key),
  framework_version text,
  certainty_judgement text not null,
  assessment_status text not null default 'assessment_in_progress' check (
    assessment_status in (
      'assessment_in_progress','partially_assessed','reviewed_complete',
      'insufficient_information','not_applicable'
    )
  ),
  basis text not null,
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
  unique (synthesis_outcome_id, framework_key)
);

create index body_certainty_synthesis_outcome_idx on public.body_certainty_assessment(synthesis_outcome_id);
create index body_certainty_framework_idx on public.body_certainty_assessment(framework_key);

-- ===========================================================================
-- 7. Typed body-level EML; source-contribution EML remains untouched
-- ===========================================================================

create table public.body_maturity_assessment (
  body_maturity_assessment_id bigserial primary key,
  synthesis_outcome_id bigint not null references public.synthesis_outcome(synthesis_outcome_id) on delete cascade,
  scale_version text not null default 'hrp-eml-v1',
  maturity_level smallint not null,
  assessment_status text not null default 'provisional' check (
    assessment_status in ('provisional','reviewed','approved')
  ),
  basis text not null,

  direct_study_count integer check (direct_study_count is null or direct_study_count >= 0),
  genuine_replication_count integer check (genuine_replication_count is null or genuine_replication_count >= 0),
  independent_replication_count integer check (independent_replication_count is null or independent_replication_count >= 0),
  replication_basis text,
  consistency_pattern text check (
    consistency_pattern is null or consistency_pattern in (
      'consistent','mixed_but_convergent','mixed','contradictory','unclear','not_assessed'
    )
  ),
  unresolved_boundaries text,

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

  unique (synthesis_outcome_id, scale_version),
  constraint body_maturity_level_fk foreign key (scale_version, maturity_level)
    references public.evidence_maturity_level_definition(scale_version, maturity_level)
);

create index body_maturity_synthesis_outcome_idx on public.body_maturity_assessment(synthesis_outcome_id);
create index body_maturity_level_idx on public.body_maturity_assessment(scale_version, maturity_level);

comment on table public.body_maturity_assessment is
'Body-level EML attached only to a Stage 8 synthesis outcome. It is not derived from maximum source-level EML and remains separate from GRADE/body certainty.';

-- ===========================================================================
-- 8. Typed governed claim lifecycle
-- ===========================================================================

create table public.body_approved_claim (
  body_claim_id bigserial primary key,
  claim_key text not null unique,
  proposition_id bigint not null references public.evidence_proposition(proposition_id) on delete restrict,
  synthesis_outcome_id bigint not null references public.synthesis_outcome(synthesis_outcome_id) on delete restrict,
  product text,
  claim_text text not null,
  required_caveat text,
  population_scope text not null,
  context_scope text,
  route_scope text[] not null default '{}',
  certainty_summary text,
  status text not null default 'draft' check (
    status in ('draft','reviewing','approved_internal','approved_public','retired')
  ),
  version text not null,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index body_claim_proposition_idx on public.body_approved_claim(proposition_id);
create index body_claim_synthesis_outcome_idx on public.body_approved_claim(synthesis_outcome_id);
create index body_claim_status_idx on public.body_approved_claim(status);

-- ===========================================================================
-- 9. Scientific-integrity guards
-- ===========================================================================

create or replace function private.validate_stage8_contribution_link()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  resolved_study_id bigint;
  study_source_id text;
  outcome_study_id bigint;
  outcome_source_id text;
  contrast_study_id bigint;
  effect_outcome_id bigint;
  effect_contrast_id bigint;
  effect_scope text;
begin
  if new.study_id is not null then
    select s.source_id into study_source_id from public.study s where s.study_id = new.study_id;
    if study_source_id is null then
      raise exception 'Unknown Stage 8 contribution study %', new.study_id;
    end if;
    resolved_study_id := new.study_id;
    if new.source_id is not null and new.source_id <> study_source_id then
      raise exception 'Stage 8 contribution study/source mismatch: study %, source %', new.study_id, new.source_id;
    end if;
  end if;

  if new.outcome_id is not null then
    select eo.study_id, s.source_id into outcome_study_id, outcome_source_id
    from public.evidence_outcome eo
    join public.study s on s.study_id = eo.study_id
    where eo.outcome_id = new.outcome_id;
    if outcome_study_id is null then
      raise exception 'Unknown Stage 8 contribution outcome %', new.outcome_id;
    end if;
    if resolved_study_id is not null and resolved_study_id <> outcome_study_id then
      raise exception 'Stage 8 contribution outcome/study mismatch: outcome %, study %', new.outcome_id, new.study_id;
    end if;
    resolved_study_id := outcome_study_id;
    if new.source_id is not null and new.source_id <> outcome_source_id then
      raise exception 'Stage 8 contribution outcome/source mismatch: outcome %, source %', new.outcome_id, new.source_id;
    end if;
  end if;

  if new.contrast_id is not null then
    select sc.study_id into contrast_study_id from public.study_contrast sc where sc.contrast_id = new.contrast_id;
    if contrast_study_id is null or resolved_study_id is null or contrast_study_id <> resolved_study_id then
      raise exception 'Stage 8 contribution contrast/result cross-study mismatch: contrast %, resolved study %', new.contrast_id, resolved_study_id;
    end if;
  end if;

  if new.effect_estimate_id is not null then
    select ee.outcome_id, ee.contrast_id, ee.estimate_scope
      into effect_outcome_id, effect_contrast_id, effect_scope
    from public.effect_estimate ee
    where ee.effect_estimate_id = new.effect_estimate_id;

    if effect_outcome_id is null or effect_outcome_id <> new.outcome_id then
      raise exception 'Stage 8 contribution effect/outcome mismatch: effect %, outcome %', new.effect_estimate_id, new.outcome_id;
    end if;
    if effect_contrast_id is not null and new.contrast_id is distinct from effect_contrast_id then
      raise exception 'Stage 8 contribution effect/contrast mismatch: effect %, contribution contrast %', new.effect_estimate_id, new.contrast_id;
    end if;
    if effect_scope = 'source_level_synthesis' and new.contrast_id is not null then
      raise exception 'Stage 8 source-level synthesis effect % cannot be assigned a fabricated Stage 5 contrast', new.effect_estimate_id;
    end if;
  end if;

  return new;
end;
$$;

revoke all on function private.validate_stage8_contribution_link() from public, anon, authenticated;
create trigger validate_stage8_contribution_link
before insert or update on public.proposition_evidence_contribution
for each row execute function private.validate_stage8_contribution_link();


create or replace function private.validate_stage8_synthesis_outcome()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  parent_proposition_id bigint;
begin
  select bes.proposition_id into parent_proposition_id
  from public.body_evidence_synthesis bes
  where bes.body_synthesis_id = new.body_synthesis_id;

  if parent_proposition_id is null or parent_proposition_id <> new.proposition_id then
    raise exception 'Stage 8 synthesis outcome proposition mismatch: synthesis %, proposition %', new.body_synthesis_id, new.proposition_id;
  end if;
  return new;
end;
$$;

revoke all on function private.validate_stage8_synthesis_outcome() from public, anon, authenticated;
create trigger validate_stage8_synthesis_outcome
before insert or update on public.synthesis_outcome
for each row execute function private.validate_stage8_synthesis_outcome();


create or replace function private.validate_stage8_body_certainty()
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

  if subject not in ('body_certainty_reserved','custom') then
    raise exception 'Framework % with subject_kind % cannot be attached to body certainty', new.framework_key, subject;
  end if;

  if new.framework_key = 'grade' and new.certainty_judgement not in ('high','moderate','low','very_low') then
    raise exception 'GRADE certainty must be high, moderate, low or very_low; got %', new.certainty_judgement;
  end if;

  return new;
end;
$$;

revoke all on function private.validate_stage8_body_certainty() from public, anon, authenticated;
create trigger validate_stage8_body_certainty
before insert or update on public.body_certainty_assessment
for each row execute function private.validate_stage8_body_certainty();


create or replace function private.validate_stage8_body_maturity()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  outcome_review_status text;
  outcome_status text;
  body_synthesis_id bigint;
  synthesis_review_status text;
  synthesis_status text;
  included_studies integer;
begin
  if new.maturity_level >= 3 then
    if coalesce(new.direct_study_count, 0) < 2 then
      raise exception 'Body EML3+ requires at least two direct contributing studies';
    end if;
    if coalesce(new.genuine_replication_count, 0) < 1 then
      raise exception 'Body EML3+ requires at least one genuine replication';
    end if;
    if nullif(btrim(coalesce(new.replication_basis, '')), '') is null then
      raise exception 'Body EML3+ requires an explicit replication_basis';
    end if;
    if new.consistency_pattern not in ('consistent','mixed_but_convergent') then
      raise exception 'Body EML3+ requires a reviewed convergent direction pattern; got %', new.consistency_pattern;
    end if;
  end if;

  if new.independent_replication_count is not null
     and new.genuine_replication_count is not null
     and new.independent_replication_count > new.genuine_replication_count then
    raise exception 'Independent replication count cannot exceed genuine replication count';
  end if;

  select so.review_status, so.status, so.body_synthesis_id, so.included_study_count
    into outcome_review_status, outcome_status, body_synthesis_id, included_studies
  from public.synthesis_outcome so
  where so.synthesis_outcome_id = new.synthesis_outcome_id;

  if new.review_status = 'approved' or new.assessment_status = 'approved' then
    if outcome_review_status <> 'approved' or outcome_status <> 'approved' then
      raise exception 'Approved body EML requires an approved synthesis outcome';
    end if;

    select bes.review_status, bes.status into synthesis_review_status, synthesis_status
    from public.body_evidence_synthesis bes
    where bes.body_synthesis_id = body_synthesis_id;

    if synthesis_review_status <> 'approved' or synthesis_status <> 'approved' then
      raise exception 'Approved body EML requires an approved body synthesis';
    end if;

    if new.maturity_level >= 4 and coalesce(included_studies, 0) < 2 then
      raise exception 'Approved body EML4+ requires a multi-study synthesis outcome';
    end if;
  end if;

  return new;
end;
$$;

revoke all on function private.validate_stage8_body_maturity() from public, anon, authenticated;
create trigger validate_stage8_body_maturity
before insert or update on public.body_maturity_assessment
for each row execute function private.validate_stage8_body_maturity();


create or replace function private.validate_stage8_body_claim()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  outcome_proposition_id bigint;
  outcome_status text;
  outcome_review_status text;
  proposition_status text;
  proposition_review_status text;
begin
  select so.proposition_id, so.status, so.review_status
    into outcome_proposition_id, outcome_status, outcome_review_status
  from public.synthesis_outcome so
  where so.synthesis_outcome_id = new.synthesis_outcome_id;

  if outcome_proposition_id is null or outcome_proposition_id <> new.proposition_id then
    raise exception 'Stage 8 body claim proposition/synthesis-outcome mismatch';
  end if;

  if new.status in ('approved_internal','approved_public') then
    select ep.status, ep.review_status into proposition_status, proposition_review_status
    from public.evidence_proposition ep
    where ep.proposition_id = new.proposition_id;

    if proposition_status <> 'approved' or proposition_review_status <> 'approved' then
      raise exception 'Approved body claim requires an approved proposition';
    end if;
    if outcome_status <> 'approved' or outcome_review_status <> 'approved' then
      raise exception 'Approved body claim requires an approved synthesis outcome';
    end if;
    if new.mapping_source = 'agent_candidate' or new.review_status <> 'approved' then
      raise exception 'Agent candidate / unapproved review state cannot enter approved claim lifecycle';
    end if;
  end if;

  return new;
end;
$$;

revoke all on function private.validate_stage8_body_claim() from public, anon, authenticated;
create trigger validate_stage8_body_claim
before insert or update on public.body_approved_claim
for each row execute function private.validate_stage8_body_claim();


create or replace function private.prevent_stage8_agent_self_approval()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if new.mapping_source = 'agent_candidate' and new.review_status = 'approved' then
    raise exception 'Stage 8 agent_candidate rows cannot self-promote to approved review status';
  end if;
  return new;
end;
$$;

revoke all on function private.prevent_stage8_agent_self_approval() from public, anon, authenticated;

create trigger prevent_stage8_agent_proposition_approval
before insert or update on public.evidence_proposition
for each row execute function private.prevent_stage8_agent_self_approval();
create trigger prevent_stage8_agent_contribution_approval
before insert or update on public.proposition_evidence_contribution
for each row execute function private.prevent_stage8_agent_self_approval();
create trigger prevent_stage8_agent_synthesis_approval
before insert or update on public.body_evidence_synthesis
for each row execute function private.prevent_stage8_agent_self_approval();
create trigger prevent_stage8_agent_outcome_approval
before insert or update on public.synthesis_outcome
for each row execute function private.prevent_stage8_agent_self_approval();
create trigger prevent_stage8_agent_certainty_approval
before insert or update on public.body_certainty_assessment
for each row execute function private.prevent_stage8_agent_self_approval();
create trigger prevent_stage8_agent_maturity_approval
before insert or update on public.body_maturity_assessment
for each row execute function private.prevent_stage8_agent_self_approval();
create trigger prevent_stage8_agent_claim_approval
before insert or update on public.body_approved_claim
for each row execute function private.prevent_stage8_agent_self_approval();

-- ===========================================================================
-- 10. RLS, Workbench grants and audit coverage
-- ===========================================================================

alter table public.body_evidence_stage8_status enable row level security;
alter table public.evidence_proposition enable row level security;
alter table public.proposition_evidence_contribution enable row level security;
alter table public.body_evidence_synthesis enable row level security;
alter table public.synthesis_outcome enable row level security;
alter table public.body_certainty_assessment enable row level security;
alter table public.body_maturity_assessment enable row level security;
alter table public.body_approved_claim enable row level security;

revoke all on table public.body_evidence_stage8_status from anon, authenticated;
revoke all on table public.evidence_proposition from anon, authenticated;
revoke all on table public.proposition_evidence_contribution from anon, authenticated;
revoke all on table public.body_evidence_synthesis from anon, authenticated;
revoke all on table public.synthesis_outcome from anon, authenticated;
revoke all on table public.body_certainty_assessment from anon, authenticated;
revoke all on table public.body_maturity_assessment from anon, authenticated;
revoke all on table public.body_approved_claim from anon, authenticated;

grant select, insert, update, delete on table public.body_evidence_stage8_status to service_role, authenticated;
grant select, insert, update, delete on table public.evidence_proposition to service_role, authenticated;
grant select, insert, update, delete on table public.proposition_evidence_contribution to service_role, authenticated;
grant select, insert, update, delete on table public.body_evidence_synthesis to service_role, authenticated;
grant select, insert, update, delete on table public.synthesis_outcome to service_role, authenticated;
grant select, insert, update, delete on table public.body_certainty_assessment to service_role, authenticated;
grant select, insert, update, delete on table public.body_maturity_assessment to service_role, authenticated;
grant select, insert, update, delete on table public.body_approved_claim to service_role, authenticated;

grant usage, select on sequence public.evidence_proposition_proposition_id_seq to service_role, authenticated;
grant usage, select on sequence public.proposition_evidence_contribution_contribution_id_seq to service_role, authenticated;
grant usage, select on sequence public.body_evidence_synthesis_body_synthesis_id_seq to service_role, authenticated;
grant usage, select on sequence public.synthesis_outcome_synthesis_outcome_id_seq to service_role, authenticated;
grant usage, select on sequence public.body_certainty_assessment_body_certainty_assessment_id_seq to service_role, authenticated;
grant usage, select on sequence public.body_maturity_assessment_body_maturity_assessment_id_seq to service_role, authenticated;
grant usage, select on sequence public.body_approved_claim_body_claim_id_seq to service_role, authenticated;

create policy stage8_status_workbench_read on public.body_evidence_stage8_status
for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy stage8_status_workbench_update on public.body_evidence_stage8_status
for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy evidence_proposition_workbench_read on public.evidence_proposition
for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy evidence_proposition_workbench_insert on public.evidence_proposition
for insert to authenticated with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy evidence_proposition_workbench_update on public.evidence_proposition
for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy evidence_proposition_workbench_delete on public.evidence_proposition
for delete to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy proposition_contribution_workbench_read on public.proposition_evidence_contribution
for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy proposition_contribution_workbench_insert on public.proposition_evidence_contribution
for insert to authenticated with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy proposition_contribution_workbench_update on public.proposition_evidence_contribution
for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy proposition_contribution_workbench_delete on public.proposition_evidence_contribution
for delete to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy body_synthesis_workbench_read on public.body_evidence_synthesis
for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy body_synthesis_workbench_insert on public.body_evidence_synthesis
for insert to authenticated with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy body_synthesis_workbench_update on public.body_evidence_synthesis
for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy body_synthesis_workbench_delete on public.body_evidence_synthesis
for delete to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy synthesis_outcome_workbench_read on public.synthesis_outcome
for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy synthesis_outcome_workbench_insert on public.synthesis_outcome
for insert to authenticated with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy synthesis_outcome_workbench_update on public.synthesis_outcome
for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy synthesis_outcome_workbench_delete on public.synthesis_outcome
for delete to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy body_certainty_workbench_read on public.body_certainty_assessment
for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy body_certainty_workbench_insert on public.body_certainty_assessment
for insert to authenticated with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy body_certainty_workbench_update on public.body_certainty_assessment
for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy body_certainty_workbench_delete on public.body_certainty_assessment
for delete to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy body_maturity_workbench_read on public.body_maturity_assessment
for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy body_maturity_workbench_insert on public.body_maturity_assessment
for insert to authenticated with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy body_maturity_workbench_update on public.body_maturity_assessment
for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy body_maturity_workbench_delete on public.body_maturity_assessment
for delete to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy body_claim_workbench_read on public.body_approved_claim
for select to authenticated using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy body_claim_workbench_insert on public.body_approved_claim
for insert to authenticated with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy body_claim_workbench_update on public.body_approved_claim
for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy body_claim_workbench_delete on public.body_approved_claim
for delete to authenticated using ((select private.has_workbench_role(array['editor','owner']::text[])));

create trigger audit_stage8_status after insert or update or delete on public.body_evidence_stage8_status
for each row execute function private.audit_workbench_change();
create trigger audit_evidence_proposition after insert or update or delete on public.evidence_proposition
for each row execute function private.audit_workbench_change();
create trigger audit_proposition_contribution after insert or update or delete on public.proposition_evidence_contribution
for each row execute function private.audit_workbench_change();
create trigger audit_body_evidence_synthesis after insert or update or delete on public.body_evidence_synthesis
for each row execute function private.audit_workbench_change();
create trigger audit_synthesis_outcome after insert or update or delete on public.synthesis_outcome
for each row execute function private.audit_workbench_change();
create trigger audit_body_certainty_assessment after insert or update or delete on public.body_certainty_assessment
for each row execute function private.audit_workbench_change();
create trigger audit_body_maturity_assessment after insert or update or delete on public.body_maturity_assessment
for each row execute function private.audit_workbench_change();
create trigger audit_body_approved_claim after insert or update or delete on public.body_approved_claim
for each row execute function private.audit_workbench_change();
