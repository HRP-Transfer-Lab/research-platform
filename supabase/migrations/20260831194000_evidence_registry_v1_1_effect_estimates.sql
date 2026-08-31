-- HRP Transfer Evidence Registry v1.1
-- Stage 6: first-class quantitative effect estimates and raw arm summaries.
--
-- Scientific rules:
--   OUTCOME != CONTRAST != EFFECT ESTIMATE
--   raw arm/group summary != comparative effect estimate
--   absence of a quantitative extraction != null effect
--
-- This migration is additive. Historical evidence_outcome effect fields and
-- the immutable 2026-08-23 release remain unchanged.

-- ===========================================================================
-- 1. Per-outcome quantitative extraction/review state
-- ===========================================================================

create table public.outcome_stage6_status (
  outcome_id bigint primary key
    references public.evidence_outcome(outcome_id) on delete cascade,

  quantitative_extraction_status text not null default 'not_yet_extracted' check (
    quantitative_extraction_status in (
      'not_yet_extracted','partially_extracted','reviewed_complete',
      'reviewed_no_quantitative_estimate','not_reported','not_applicable'
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

comment on table public.outcome_stage6_status is
'Explicit Stage 6 quantitative extraction/provenance state per normalized outcome. Missing quantitative rows must not imply no reported effect.';

-- ===========================================================================
-- 2. First-class effect estimates
-- ===========================================================================

create table public.effect_estimate (
  effect_estimate_id bigserial primary key,
  outcome_id bigint not null
    references public.evidence_outcome(outcome_id) on delete cascade,
  contrast_id bigint
    references public.study_contrast(contrast_id) on delete cascade,

  estimate_key text not null,
  estimate_scope text not null check (
    estimate_scope in (
      'study_contrast','within_group','single_group','association',
      'measurement','source_level_synthesis','other'
    )
  ),
  estimate_type text not null check (
    estimate_type in (
      'raw_mean','raw_proportion','change_score','mean_difference',
      'standardised_mean_difference','odds_ratio','risk_ratio','hazard_ratio',
      'correlation','regression_coefficient','rate_ratio','other'
    )
  ),
  metric text not null,
  estimate_value numeric not null,

  standard_error numeric,
  ci_level numeric check (ci_level is null or (ci_level > 0 and ci_level <= 1)),
  ci_lower numeric,
  ci_upper numeric,
  p_value numeric check (p_value is null or (p_value >= 0 and p_value <= 1)),
  n_analysed bigint check (n_analysed is null or n_analysed >= 0),

  adjustment_status text not null check (
    adjustment_status in (
      'unadjusted','adjusted','partially_adjusted','not_applicable','unclear'
    )
  ),
  model_specification text,
  time_or_model_label text,
  unit text,
  scale_direction text not null check (
    scale_direction in (
      'higher_is_better','higher_is_worse','neutral_or_metric_defined','unclear'
    )
  ),
  source_reported boolean not null default true,
  rationale text,

  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (outcome_id, estimate_key),
  check (ci_lower is null or ci_upper is null or ci_lower <= ci_upper),
  check (
    (estimate_scope = 'study_contrast' and contrast_id is not null)
    or
    (estimate_scope <> 'study_contrast' and contrast_id is null)
  )
);

create index effect_estimate_outcome_idx on public.effect_estimate(outcome_id);
create index effect_estimate_contrast_idx on public.effect_estimate(contrast_id);
create index effect_estimate_type_idx on public.effect_estimate(estimate_type);
create index effect_estimate_scope_idx on public.effect_estimate(estimate_scope);

comment on table public.effect_estimate is
'First-class quantitative estimate linked to a normalized outcome and, when scientifically applicable, a Stage 5 contrast. Multiple estimates/models per outcome are supported.';

-- ===========================================================================
-- 3. Optional raw arm/group summaries
-- ===========================================================================

create table public.arm_outcome_summary (
  arm_outcome_summary_id bigserial primary key,
  outcome_id bigint not null
    references public.evidence_outcome(outcome_id) on delete cascade,
  arm_id bigint not null
    references public.study_arm(arm_id) on delete cascade,
  summary_key text not null,

  n_analysed bigint check (n_analysed is null or n_analysed >= 0),
  mean numeric,
  sd numeric check (sd is null or sd >= 0),
  se numeric check (se is null or se >= 0),
  proportion numeric check (proportion is null or (proportion >= 0 and proportion <= 1)),
  count bigint check (count is null or count >= 0),
  change_mean numeric,
  change_sd numeric check (change_sd is null or change_sd >= 0),
  unit text,
  source_reported boolean not null default true,
  rationale text,

  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (outcome_id, arm_id, summary_key),
  check (
    n_analysed is not null or mean is not null or sd is not null or se is not null
    or proportion is not null or count is not null or change_mean is not null
    or change_sd is not null
  )
);

create index arm_outcome_summary_outcome_idx on public.arm_outcome_summary(outcome_id);
create index arm_outcome_summary_arm_idx on public.arm_outcome_summary(arm_id);

comment on table public.arm_outcome_summary is
'Raw/descriptive outcome summary for a Stage 5 arm. Raw summaries are not scientific contrasts and are not stored as comparative effect estimates.';

-- ===========================================================================
-- 4. Cross-study scientific-integrity guards
-- ===========================================================================

create or replace function private.validate_stage6_effect_link()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  outcome_study_id bigint;
  contrast_study_id bigint;
begin
  if new.contrast_id is null then
    return new;
  end if;

  select eo.study_id into outcome_study_id
  from public.evidence_outcome eo
  where eo.outcome_id = new.outcome_id;

  select sc.study_id into contrast_study_id
  from public.study_contrast sc
  where sc.contrast_id = new.contrast_id;

  if outcome_study_id is distinct from contrast_study_id then
    raise exception 'Stage 6 contrast/outcome cross-study mismatch: outcome % study %, contrast % study %',
      new.outcome_id, outcome_study_id, new.contrast_id, contrast_study_id;
  end if;

  return new;
end;
$$;

revoke all on function private.validate_stage6_effect_link() from public, anon, authenticated;

drop trigger if exists validate_stage6_effect_link on public.effect_estimate;
create trigger validate_stage6_effect_link
before insert or update on public.effect_estimate
for each row execute function private.validate_stage6_effect_link();


create or replace function private.validate_stage6_arm_summary_link()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  outcome_study_id bigint;
  arm_study_id bigint;
begin
  select eo.study_id into outcome_study_id
  from public.evidence_outcome eo
  where eo.outcome_id = new.outcome_id;

  select sa.study_id into arm_study_id
  from public.study_arm sa
  where sa.arm_id = new.arm_id;

  if outcome_study_id is distinct from arm_study_id then
    raise exception 'Stage 6 arm/outcome cross-study mismatch: outcome % study %, arm % study %',
      new.outcome_id, outcome_study_id, new.arm_id, arm_study_id;
  end if;

  return new;
end;
$$;

revoke all on function private.validate_stage6_arm_summary_link() from public, anon, authenticated;

drop trigger if exists validate_stage6_arm_summary_link on public.arm_outcome_summary;
create trigger validate_stage6_arm_summary_link
before insert or update on public.arm_outcome_summary
for each row execute function private.validate_stage6_arm_summary_link();

-- ===========================================================================
-- 5. Deterministic status-row creation after historical importer replay
-- ===========================================================================

create or replace function private.ensure_stage6_outcome_status()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  insert into public.outcome_stage6_status (outcome_id, notes)
  values (
    new.outcome_id,
    'Stage 6 status row created from normalized outcome; quantitative structure requires replayable mapping or human review.'
  )
  on conflict (outcome_id) do nothing;
  return new;
end;
$$;

revoke all on function private.ensure_stage6_outcome_status() from public, anon, authenticated;

drop trigger if exists ensure_stage6_outcome_status on public.evidence_outcome;
create trigger ensure_stage6_outcome_status
after insert on public.evidence_outcome
for each row execute function private.ensure_stage6_outcome_status();

insert into public.outcome_stage6_status (outcome_id, notes)
select
  eo.outcome_id,
  'Stage 6 status row created for pre-existing normalized outcome; quantitative structure requires replayable mapping or human review.'
from public.evidence_outcome eo
on conflict (outcome_id) do nothing;

-- ===========================================================================
-- 6. RLS and grants
-- ===========================================================================

alter table public.outcome_stage6_status enable row level security;
alter table public.effect_estimate enable row level security;
alter table public.arm_outcome_summary enable row level security;

revoke all on table public.outcome_stage6_status from anon, authenticated;
revoke all on table public.effect_estimate from anon, authenticated;
revoke all on table public.arm_outcome_summary from anon, authenticated;

-- Server-side scientific access.
grant select, insert, update, delete on table public.outcome_stage6_status to service_role;
grant select, insert, update, delete on table public.effect_estimate to service_role;
grant select, insert, update, delete on table public.arm_outcome_summary to service_role;
grant usage, select on sequence public.effect_estimate_effect_estimate_id_seq to service_role;
grant usage, select on sequence public.arm_outcome_summary_arm_outcome_summary_id_seq to service_role;

-- Workbench browser access, governed by RLS.
grant select, insert, update, delete on table public.outcome_stage6_status to authenticated;
grant select, insert, update, delete on table public.effect_estimate to authenticated;
grant select, insert, update, delete on table public.arm_outcome_summary to authenticated;
grant usage, select on sequence public.effect_estimate_effect_estimate_id_seq to authenticated;
grant usage, select on sequence public.arm_outcome_summary_arm_outcome_summary_id_seq to authenticated;

-- Viewer/editor/owner reads.
create policy outcome_stage6_status_workbench_read
on public.outcome_stage6_status for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy effect_estimate_workbench_read
on public.effect_estimate for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy arm_outcome_summary_workbench_read
on public.arm_outcome_summary for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

-- Editor/owner writes.
create policy outcome_stage6_status_workbench_insert
on public.outcome_stage6_status for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy outcome_stage6_status_workbench_update
on public.outcome_stage6_status for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy outcome_stage6_status_workbench_delete
on public.outcome_stage6_status for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy effect_estimate_workbench_insert
on public.effect_estimate for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy effect_estimate_workbench_update
on public.effect_estimate for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy effect_estimate_workbench_delete
on public.effect_estimate for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy arm_outcome_summary_workbench_insert
on public.arm_outcome_summary for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy arm_outcome_summary_workbench_update
on public.arm_outcome_summary for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy arm_outcome_summary_workbench_delete
on public.arm_outcome_summary for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

-- ===========================================================================
-- 7. Audit coverage
-- ===========================================================================

drop trigger if exists audit_outcome_stage6_status on public.outcome_stage6_status;
create trigger audit_outcome_stage6_status
after insert or update or delete on public.outcome_stage6_status
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_effect_estimate on public.effect_estimate;
create trigger audit_effect_estimate
after insert or update or delete on public.effect_estimate
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_arm_outcome_summary on public.arm_outcome_summary;
create trigger audit_arm_outcome_summary
after insert or update or delete on public.arm_outcome_summary
for each row execute function private.audit_workbench_change();
