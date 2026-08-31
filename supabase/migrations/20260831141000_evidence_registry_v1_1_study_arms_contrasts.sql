-- HRP Transfer Evidence Registry v1.1
-- Stage 5: study arms/conditions, component membership and contrasts.
--
-- Scientific rule:
--   STUDY != ARM/CONDITION != COMPONENT != CONTRAST
--
-- This migration is additive. It preserves the historical 2026-08-23 release,
-- study.comparator_summary, normalized intervention_component rows, and
-- csi-evidence-v1.

-- ===========================================================================
-- 1. Study-level Stage 5 extraction/review state
-- ===========================================================================

create table public.study_stage5_status (
  study_id bigint primary key
    references public.study(study_id) on delete cascade,

  arm_extraction_status text not null default 'not_yet_extracted' check (
    arm_extraction_status in (
      'not_yet_extracted','partially_extracted','reviewed_complete',
      'reviewed_no_arms','not_reported','not_applicable'
    )
  ),
  arm_mapping_source text not null default 'migration' check (
    arm_mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  arm_review_status text not null default 'proposed' check (
    arm_review_status in ('proposed','reviewed','approved','rejected')
  ),

  contrast_extraction_status text not null default 'not_yet_extracted' check (
    contrast_extraction_status in (
      'not_yet_extracted','partially_extracted','reviewed_complete',
      'reviewed_no_contrasts','not_reported','not_applicable'
    )
  ),
  contrast_mapping_source text not null default 'migration' check (
    contrast_mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  contrast_review_status text not null default 'proposed' check (
    contrast_review_status in ('proposed','reviewed','approved','rejected')
  ),

  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.study_stage5_status is
'Explicit Stage 5 completeness/provenance state for arm/condition and contrast extraction. Absence of rows must not imply no arms or no contrasts.';

-- ===========================================================================
-- 2. Study arms / conditions
-- ===========================================================================

create table public.study_arm (
  arm_id bigserial primary key,
  study_id bigint not null
    references public.study(study_id) on delete cascade,
  arm_key text not null,
  arm_label text not null,
  author_arm_label text,
  arm_role text not null check (
    arm_role in (
      'intervention','active_control','passive_control','waitlist',
      'treatment_as_usual','alternative_intervention','reference',
      'observational_exposure','experimental_condition',
      'measurement_condition','unclear'
    )
  ),
  assignment_structure text not null check (
    assignment_structure in (
      'parallel_group','cluster_group','factorial_cell',
      'within_subject_condition','single_group','observational_group','unclear'
    )
  ),
  arm_description text,
  sample_json jsonb not null default '{}'::jsonb,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (study_id, arm_key)
);

create index study_arm_study_idx on public.study_arm(study_id);
create index study_arm_role_idx on public.study_arm(arm_role);

comment on table public.study_arm is
'Assigned, exposed or observed study group/condition. Arm role is not intervention route; experimental/measurement conditions may be non-intervention conditions.';

-- ===========================================================================
-- 3. Arm -> normalized intervention component membership
-- ===========================================================================

create table public.arm_component (
  arm_id bigint not null
    references public.study_arm(arm_id) on delete cascade,
  component_id bigint not null
    references public.intervention_component(component_id) on delete cascade,
  membership_role text not null check (
    membership_role in ('defining','shared','add_on','background','unclear')
  ),
  rationale text,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (arm_id, component_id)
);

create index arm_component_component_idx on public.arm_component(component_id);

comment on table public.arm_component is
'Many-to-many membership between study arms and reusable normalized intervention components. The same component may legitimately appear in multiple arms.';

-- ===========================================================================
-- 4. Study contrasts and contrast membership
-- ===========================================================================

create table public.study_contrast (
  contrast_id bigserial primary key,
  study_id bigint not null
    references public.study(study_id) on delete cascade,
  contrast_key text not null,
  contrast_label text not null,
  contrast_type text not null check (
    contrast_type in (
      'pairwise','multiarm_pairwise','factorial_main_effect',
      'factorial_interaction','within_subject','observational','other'
    )
  ),
  estimand_summary text,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (study_id, contrast_key)
);

create index study_contrast_study_idx on public.study_contrast(study_id);
create index study_contrast_type_idx on public.study_contrast(contrast_type);

create table public.contrast_arm_member (
  contrast_id bigint not null
    references public.study_contrast(contrast_id) on delete cascade,
  arm_id bigint not null
    references public.study_arm(arm_id) on delete cascade,
  contrast_side text not null check (contrast_side in ('focal','comparator')),
  contrast_coefficient numeric,
  rationale text,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration','agent_candidate','human_review','manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed','reviewed','approved','rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (contrast_id, arm_id)
);

create index contrast_arm_member_arm_idx on public.contrast_arm_member(arm_id);

comment on table public.study_contrast is
'Scientific comparison within a study. A contrast may contain multiple arms on either side, supporting factorial main effects/interactions without reducing them to one arm versus one arm.';

-- ===========================================================================
-- 5. Deterministic status-row creation after importer replay
-- ===========================================================================

create or replace function private.ensure_stage5_study_status()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  insert into public.study_stage5_status (study_id, notes)
  values (
    new.study_id,
    'Stage 5 status row created from normalized study; arm/contrast structure requires replayable mapping or human review.'
  )
  on conflict (study_id) do nothing;
  return new;
end;
$$;

revoke all on function private.ensure_stage5_study_status() from public, anon, authenticated;

drop trigger if exists ensure_stage5_study_status on public.study;
create trigger ensure_stage5_study_status
after insert on public.study
for each row execute function private.ensure_stage5_study_status();

insert into public.study_stage5_status (study_id, notes)
select
  s.study_id,
  'Stage 5 status row created for pre-existing normalized study; arm/contrast structure requires replayable mapping or human review.'
from public.study s
on conflict (study_id) do nothing;

-- ===========================================================================
-- 6. RLS and grants
-- ===========================================================================

alter table public.study_stage5_status enable row level security;
alter table public.study_arm enable row level security;
alter table public.arm_component enable row level security;
alter table public.study_contrast enable row level security;
alter table public.contrast_arm_member enable row level security;

revoke all on table public.study_stage5_status from anon, authenticated;
revoke all on table public.study_arm from anon, authenticated;
revoke all on table public.arm_component from anon, authenticated;
revoke all on table public.study_contrast from anon, authenticated;
revoke all on table public.contrast_arm_member from anon, authenticated;

-- Server-side scientific access.
grant select, insert, update, delete on table public.study_stage5_status to service_role;
grant select, insert, update, delete on table public.study_arm to service_role;
grant select, insert, update, delete on table public.arm_component to service_role;
grant select, insert, update, delete on table public.study_contrast to service_role;
grant select, insert, update, delete on table public.contrast_arm_member to service_role;
grant usage, select on all sequences in schema public to service_role;

-- Workbench access, governed by RLS.
grant select, insert, update, delete on table public.study_stage5_status to authenticated;
grant select, insert, update, delete on table public.study_arm to authenticated;
grant select, insert, update, delete on table public.arm_component to authenticated;
grant select, insert, update, delete on table public.study_contrast to authenticated;
grant select, insert, update, delete on table public.contrast_arm_member to authenticated;
grant usage, select on sequence public.study_arm_arm_id_seq to authenticated;
grant usage, select on sequence public.study_contrast_contrast_id_seq to authenticated;

-- Viewer/editor/owner reads.
create policy study_stage5_status_workbench_read
on public.study_stage5_status for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy study_arm_workbench_read
on public.study_arm for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy arm_component_workbench_read
on public.arm_component for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy study_contrast_workbench_read
on public.study_contrast for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy contrast_arm_member_workbench_read
on public.contrast_arm_member for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

-- Editor/owner writes.
create policy study_stage5_status_workbench_insert
on public.study_stage5_status for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy study_stage5_status_workbench_update
on public.study_stage5_status for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy study_stage5_status_workbench_delete
on public.study_stage5_status for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy study_arm_workbench_insert
on public.study_arm for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy study_arm_workbench_update
on public.study_arm for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy study_arm_workbench_delete
on public.study_arm for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy arm_component_workbench_insert
on public.arm_component for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy arm_component_workbench_update
on public.arm_component for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy arm_component_workbench_delete
on public.arm_component for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy study_contrast_workbench_insert
on public.study_contrast for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy study_contrast_workbench_update
on public.study_contrast for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy study_contrast_workbench_delete
on public.study_contrast for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy contrast_arm_member_workbench_insert
on public.contrast_arm_member for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy contrast_arm_member_workbench_update
on public.contrast_arm_member for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy contrast_arm_member_workbench_delete
on public.contrast_arm_member for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

-- ===========================================================================
-- 7. Audit coverage
-- ===========================================================================

drop trigger if exists audit_study_stage5_status on public.study_stage5_status;
create trigger audit_study_stage5_status
after insert or update or delete on public.study_stage5_status
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_study_arm on public.study_arm;
create trigger audit_study_arm
after insert or update or delete on public.study_arm
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_arm_component on public.arm_component;
create trigger audit_arm_component
after insert or update or delete on public.arm_component
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_study_contrast on public.study_contrast;
create trigger audit_study_contrast
after insert or update or delete on public.study_contrast
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_contrast_arm_member on public.contrast_arm_member;
create trigger audit_contrast_arm_member
after insert or update or delete on public.contrast_arm_member
for each row execute function private.audit_workbench_change();
