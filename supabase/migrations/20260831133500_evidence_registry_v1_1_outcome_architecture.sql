-- HRP Transfer Evidence Registry v1.1
-- Stage 4: orthogonal outcome architecture.
--
-- Scientific rule:
--
-- OUTCOME DISTANCE = how far the measurement is from the trained/intervened object
-- TIME             = when the result was observed
-- TRANSFER AXIS    = what form of portability was actually tested
-- OUTCOME ROLE     = what scientific role the result plays
-- BRIDGE EVIDENCE  = whether deployment depended on prompts/cues/context support
--
-- These dimensions remain orthogonal. In particular:
--   * delayed != transfer
--   * separate_measure != vertical transfer
--   * null effect != not measured
--   * mechanism/measurement evidence is not forced into intervention distance
--
-- This migration is additive. It preserves the historical 2026-08-23 release,
-- the existing evidence_outcome compatibility columns, and csi-evidence-v1.


-- ===========================================================================
-- 1. Controlled definitions
-- ===========================================================================

create table public.outcome_distance_definition (
  outcome_distance text primary key,
  label text not null,
  description text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

insert into public.outcome_distance_definition (
  outcome_distance, label, description
) values
  ('trained_task', 'Trained task', 'Outcome measured on the trained/practised task or essentially the same trained object.'),
  ('changed_format', 'Changed format', 'Outcome measured on a materially changed format, wrapper, stimulus arrangement or closely transformed task.'),
  ('separate_measure', 'Separate measure', 'Outcome measured with a distinct instrument or task not identical to the trained object.'),
  ('real_life_function', 'Real-life function', 'Outcome measured in an applied, naturalistic, operational, educational, occupational or otherwise real-world activity/function.')
on conflict (outcome_distance) do nothing;


create table public.outcome_time_definition (
  time_class text primary key,
  label text not null,
  description text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

insert into public.outcome_time_definition (
  time_class, label, description
) values
  ('immediate', 'Immediate', 'Concurrent, same-session or immediate test/observation.'),
  ('post_intervention', 'Post-intervention', 'Assessment after completion of the intervention/training period without a substantively delayed follow-up interval.'),
  ('delayed', 'Delayed', 'Follow-up assessment after a substantively delayed interval or later retention/portability test.')
on conflict (time_class) do nothing;


create table public.transfer_axis_definition (
  transfer_axis text primary key,
  label text not null,
  description text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

insert into public.transfer_axis_definition (
  transfer_axis, label, description
) values
  ('horizontal', 'Horizontal', 'Portability across changed surface form, wrapper, stimuli, task instantiation or closely related context while preserving the underlying level of operation.'),
  ('vertical', 'Vertical', 'Portability to a distinct cognitive operation, level, capability or function rather than merely a changed surface form.'),
  ('niche', 'Niche', 'Portability into a real-world activity, workflow, environment, role or naturalistic demand context.')
on conflict (transfer_axis) do nothing;


create table public.outcome_role_definition (
  outcome_role text primary key,
  label text not null,
  description text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

insert into public.outcome_role_definition (
  outcome_role, label, description
) values
  ('benefit', 'Benefit', 'Outcome intended to assess beneficial capability, performance, functioning or other intended intervention result; direction may still be positive, null, mixed or negative.'),
  ('harm', 'Harm', 'Outcome assessing adverse effects, worsening, trade-offs or other harmful consequences.'),
  ('target_engagement', 'Target engagement', 'Outcome assessing whether the proposed target/process was engaged or changed.'),
  ('process', 'Process', 'Process-level outcome describing how activity, learning, decision-making or task behaviour unfolded.'),
  ('adherence', 'Adherence', 'Outcome describing participation, completion, compliance or adherence to the intervention/protocol.'),
  ('implementation', 'Implementation', 'Outcome describing delivery, feasibility, uptake, burden, fidelity or implementation performance.')
on conflict (outcome_role) do nothing;


create table public.bridge_evidence_definition (
  bridge_evidence text primary key,
  label text not null,
  description text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

insert into public.bridge_evidence_definition (
  bridge_evidence, label, description
) values
  ('prompted_use', 'Prompted use', 'Deployment occurred with an explicit prompt or instruction to use the learned strategy/policy.'),
  ('cue_triggered_use', 'Cue-triggered use', 'A target cue or event triggered deployment of the learned strategy/policy.'),
  ('changed_context_use', 'Changed-context use', 'Deployment was demonstrated in a context meaningfully changed from the training context.'),
  ('unprompted_use', 'Unprompted use', 'Deployment occurred without an explicit prompt to use the learned strategy/policy.'),
  ('delayed_portability', 'Delayed portability', 'Deployment/portability was demonstrated after a delay rather than only immediately after training.')
on conflict (bridge_evidence) do nothing;


-- ===========================================================================
-- 2. Legacy rung semantic registry
-- ===========================================================================

create table public.legacy_outcome_semantic_map (
  legacy_rung text primary key,
  mapping_kind text not null check (
    mapping_kind in ('deterministic', 'interpretive', 'ambiguous', 'non_stage4_semantic')
  ),
  semantic_dimension text check (
    semantic_dimension is null or semantic_dimension in ('outcome_distance', 'time', 'evidence_role')
  ),
  canonical_value text,
  rationale text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into public.legacy_outcome_semantic_map (
  legacy_rung, mapping_kind, semantic_dimension, canonical_value, rationale
) values
  ('practice_effect', 'deterministic', 'outcome_distance', 'trained_task', 'Legacy practice-effect label denotes performance on the trained/practised object.'),
  ('changed_format', 'deterministic', 'outcome_distance', 'changed_format', 'Legacy changed-format label is an outcome-distance semantic; transfer still requires separate evidence.'),
  ('separate_measure', 'deterministic', 'outcome_distance', 'separate_measure', 'Legacy separate-measure label is an outcome-distance semantic; it does not itself establish vertical transfer.'),
  ('delayed', 'deterministic', 'time', 'delayed', 'Legacy delayed label is a timing semantic, not outcome distance or transfer.'),
  ('applied', 'interpretive', 'outcome_distance', 'real_life_function', 'Applied outcomes are candidate real-life-function outcomes, but transfer and Bridge independence must be reviewed separately.'),
  ('mechanism', 'non_stage4_semantic', 'evidence_role', null, 'Mechanism evidence is governed by evidence-role/mechanism architecture and is not forced into intervention outcome distance.'),
  ('measurement', 'non_stage4_semantic', 'evidence_role', null, 'Measurement evidence is governed by evidence-role/measurement architecture and is not forced into intervention outcome distance.'),
  ('observational_longitudinal', 'non_stage4_semantic', 'evidence_role', null, 'Observational longitudinal evidence is not an intervention outcome-distance semantic.'),
  ('practice_or_nearest_transfer', 'ambiguous', null, null, 'Legacy label mixes trained-task and nearest/changed-format interpretations and requires outcome-level review.'),
  ('practice_or_separate_measure', 'ambiguous', null, null, 'Legacy label explicitly mixes trained-task and separate-measure interpretations and requires outcome-level review.')
on conflict (legacy_rung) do nothing;


-- ===========================================================================
-- 3. Per-outcome Stage 4 classification/status row
-- ===========================================================================

create table public.outcome_stage4_classification (
  outcome_id bigint primary key
    references public.evidence_outcome(outcome_id)
    on delete cascade,

  legacy_rung_snapshot text,
  raw_timepoint_snapshot text,

  outcome_distance text
    references public.outcome_distance_definition(outcome_distance),

  distance_status text not null default 'not_yet_extracted' check (
    distance_status in (
      'not_yet_extracted', 'reviewed_mapped', 'reviewed_no_mapping',
      'not_reported', 'not_measured', 'not_applicable'
    )
  ),
  distance_mapping_source text not null default 'migration' check (
    distance_mapping_source in ('migration', 'agent_candidate', 'human_review', 'manual')
  ),
  distance_review_status text not null default 'proposed' check (
    distance_review_status in ('proposed', 'reviewed', 'approved', 'rejected')
  ),

  time_status text not null default 'not_yet_extracted' check (
    time_status in (
      'not_yet_extracted', 'reviewed_mapped', 'reviewed_no_mapping',
      'not_reported', 'not_measured', 'not_applicable'
    )
  ),
  time_mapping_source text not null default 'migration' check (
    time_mapping_source in ('migration', 'agent_candidate', 'human_review', 'manual')
  ),
  time_review_status text not null default 'proposed' check (
    time_review_status in ('proposed', 'reviewed', 'approved', 'rejected')
  ),

  transfer_status text not null default 'not_yet_extracted' check (
    transfer_status in (
      'not_yet_extracted', 'reviewed_mapped', 'reviewed_no_mapping',
      'not_reported', 'not_measured', 'not_applicable'
    )
  ),
  transfer_mapping_source text not null default 'migration' check (
    transfer_mapping_source in ('migration', 'agent_candidate', 'human_review', 'manual')
  ),
  transfer_review_status text not null default 'proposed' check (
    transfer_review_status in ('proposed', 'reviewed', 'approved', 'rejected')
  ),

  role_status text not null default 'not_yet_extracted' check (
    role_status in (
      'not_yet_extracted', 'reviewed_mapped', 'reviewed_no_mapping',
      'not_reported', 'not_measured', 'not_applicable'
    )
  ),
  role_mapping_source text not null default 'migration' check (
    role_mapping_source in ('migration', 'agent_candidate', 'human_review', 'manual')
  ),
  role_review_status text not null default 'proposed' check (
    role_review_status in ('proposed', 'reviewed', 'approved', 'rejected')
  ),

  bridge_status text not null default 'not_yet_extracted' check (
    bridge_status in (
      'not_yet_extracted', 'reviewed_mapped', 'reviewed_no_mapping',
      'not_reported', 'not_measured', 'not_applicable'
    )
  ),
  bridge_mapping_source text not null default 'migration' check (
    bridge_mapping_source in ('migration', 'agent_candidate', 'human_review', 'manual')
  ),
  bridge_review_status text not null default 'proposed' check (
    bridge_review_status in ('proposed', 'reviewed', 'approved', 'rejected')
  ),

  rationale text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  check (
    (outcome_distance is not null and distance_status = 'reviewed_mapped')
    or
    (outcome_distance is null and distance_status <> 'reviewed_mapped')
  )
);

comment on table public.outcome_stage4_classification is
'One Stage 4 status/provenance row per normalized outcome. Outcome distance is single-valued; time, transfer, role and Bridge evidence use child link tables. Each dimension has independent review authority.';


-- ===========================================================================
-- 4. Multi-valued time, transfer, role and Bridge links
-- ===========================================================================

create table public.outcome_time_link (
  outcome_id bigint not null
    references public.evidence_outcome(outcome_id)
    on delete cascade,
  time_class text not null
    references public.outcome_time_definition(time_class),
  rationale text,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration', 'agent_candidate', 'human_review', 'manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed', 'reviewed', 'approved', 'rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (outcome_id, time_class)
);

create index outcome_time_link_time_idx
  on public.outcome_time_link(time_class);


create table public.outcome_transfer_axis (
  outcome_id bigint not null
    references public.evidence_outcome(outcome_id)
    on delete cascade,
  transfer_axis text not null
    references public.transfer_axis_definition(transfer_axis),
  rationale text,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration', 'agent_candidate', 'human_review', 'manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed', 'reviewed', 'approved', 'rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (outcome_id, transfer_axis)
);

create index outcome_transfer_axis_axis_idx
  on public.outcome_transfer_axis(transfer_axis);


create table public.outcome_role_link (
  outcome_id bigint not null
    references public.evidence_outcome(outcome_id)
    on delete cascade,
  outcome_role text not null
    references public.outcome_role_definition(outcome_role),
  rationale text,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration', 'agent_candidate', 'human_review', 'manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed', 'reviewed', 'approved', 'rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (outcome_id, outcome_role)
);

create index outcome_role_link_role_idx
  on public.outcome_role_link(outcome_role);


create table public.outcome_bridge_evidence (
  outcome_id bigint not null
    references public.evidence_outcome(outcome_id)
    on delete cascade,
  bridge_evidence text not null
    references public.bridge_evidence_definition(bridge_evidence),
  rationale text,
  mapping_source text not null default 'human_review' check (
    mapping_source in ('migration', 'agent_candidate', 'human_review', 'manual')
  ),
  review_status text not null default 'proposed' check (
    review_status in ('proposed', 'reviewed', 'approved', 'rejected')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (outcome_id, bridge_evidence)
);

create index outcome_bridge_evidence_type_idx
  on public.outcome_bridge_evidence(bridge_evidence);


-- ===========================================================================
-- 5. Deterministic status-row creation for importer replay
-- ===========================================================================

create or replace function private.ensure_stage4_outcome_status()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  insert into public.outcome_stage4_classification (
    outcome_id,
    legacy_rung_snapshot,
    raw_timepoint_snapshot,
    rationale
  ) values (
    new.outcome_id,
    new.evidence_rung,
    new.timepoint,
    'Stage 4 status row created from historical normalized outcome; classification requires replayable mapping/review.'
  )
  on conflict (outcome_id) do nothing;

  return new;
end;
$$;

revoke all on function private.ensure_stage4_outcome_status() from public, anon, authenticated;


drop trigger if exists ensure_stage4_outcome_status
on public.evidence_outcome;

create trigger ensure_stage4_outcome_status
after insert
on public.evidence_outcome
for each row
execute function private.ensure_stage4_outcome_status();

-- Existing rows are included when this migration is applied to a non-empty local/dev DB.
insert into public.outcome_stage4_classification (
  outcome_id,
  legacy_rung_snapshot,
  raw_timepoint_snapshot,
  rationale
)
select
  eo.outcome_id,
  eo.evidence_rung,
  eo.timepoint,
  'Stage 4 status row created for pre-existing normalized outcome; classification requires replayable mapping/review.'
from public.evidence_outcome eo
on conflict (outcome_id) do nothing;


-- ===========================================================================
-- 6. RLS and grants
-- ===========================================================================

alter table public.outcome_distance_definition enable row level security;
alter table public.outcome_time_definition enable row level security;
alter table public.transfer_axis_definition enable row level security;
alter table public.outcome_role_definition enable row level security;
alter table public.bridge_evidence_definition enable row level security;
alter table public.legacy_outcome_semantic_map enable row level security;
alter table public.outcome_stage4_classification enable row level security;
alter table public.outcome_time_link enable row level security;
alter table public.outcome_transfer_axis enable row level security;
alter table public.outcome_role_link enable row level security;
alter table public.outcome_bridge_evidence enable row level security;

revoke all on table public.outcome_distance_definition from anon, authenticated;
revoke all on table public.outcome_time_definition from anon, authenticated;
revoke all on table public.transfer_axis_definition from anon, authenticated;
revoke all on table public.outcome_role_definition from anon, authenticated;
revoke all on table public.bridge_evidence_definition from anon, authenticated;
revoke all on table public.legacy_outcome_semantic_map from anon, authenticated;
revoke all on table public.outcome_stage4_classification from anon, authenticated;
revoke all on table public.outcome_time_link from anon, authenticated;
revoke all on table public.outcome_transfer_axis from anon, authenticated;
revoke all on table public.outcome_role_link from anon, authenticated;
revoke all on table public.outcome_bridge_evidence from anon, authenticated;

-- service_role retains server-side scientific access.
grant select, insert, update, delete on table public.outcome_distance_definition to service_role;
grant select, insert, update, delete on table public.outcome_time_definition to service_role;
grant select, insert, update, delete on table public.transfer_axis_definition to service_role;
grant select, insert, update, delete on table public.outcome_role_definition to service_role;
grant select, insert, update, delete on table public.bridge_evidence_definition to service_role;
grant select, insert, update, delete on table public.legacy_outcome_semantic_map to service_role;
grant select, insert, update, delete on table public.outcome_stage4_classification to service_role;
grant select, insert, update, delete on table public.outcome_time_link to service_role;
grant select, insert, update, delete on table public.outcome_transfer_axis to service_role;
grant select, insert, update, delete on table public.outcome_role_link to service_role;
grant select, insert, update, delete on table public.outcome_bridge_evidence to service_role;

-- Workbench browser access remains authenticated + RLS governed.
grant select on table public.outcome_distance_definition to authenticated;
grant select on table public.outcome_time_definition to authenticated;
grant select on table public.transfer_axis_definition to authenticated;
grant select on table public.outcome_role_definition to authenticated;
grant select on table public.bridge_evidence_definition to authenticated;
grant select on table public.legacy_outcome_semantic_map to authenticated;
grant select, insert, update, delete on table public.outcome_stage4_classification to authenticated;
grant select, insert, update, delete on table public.outcome_time_link to authenticated;
grant select, insert, update, delete on table public.outcome_transfer_axis to authenticated;
grant select, insert, update, delete on table public.outcome_role_link to authenticated;
grant select, insert, update, delete on table public.outcome_bridge_evidence to authenticated;


-- Viewer/editor/owner reads.
create policy outcome_distance_definition_workbench_read
on public.outcome_distance_definition
for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy outcome_time_definition_workbench_read
on public.outcome_time_definition
for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy transfer_axis_definition_workbench_read
on public.transfer_axis_definition
for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy outcome_role_definition_workbench_read
on public.outcome_role_definition
for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy bridge_evidence_definition_workbench_read
on public.bridge_evidence_definition
for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy legacy_outcome_semantic_map_workbench_read
on public.legacy_outcome_semantic_map
for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy outcome_stage4_classification_workbench_read
on public.outcome_stage4_classification
for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy outcome_time_link_workbench_read
on public.outcome_time_link
for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy outcome_transfer_axis_workbench_read
on public.outcome_transfer_axis
for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy outcome_role_link_workbench_read
on public.outcome_role_link
for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy outcome_bridge_evidence_workbench_read
on public.outcome_bridge_evidence
for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));


-- Editor/owner scientific annotation writes.
create policy outcome_stage4_classification_workbench_insert
on public.outcome_stage4_classification
for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_stage4_classification_workbench_update
on public.outcome_stage4_classification
for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_stage4_classification_workbench_delete
on public.outcome_stage4_classification
for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_time_link_workbench_insert
on public.outcome_time_link
for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_time_link_workbench_update
on public.outcome_time_link
for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_time_link_workbench_delete
on public.outcome_time_link
for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_transfer_axis_workbench_insert
on public.outcome_transfer_axis
for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_transfer_axis_workbench_update
on public.outcome_transfer_axis
for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_transfer_axis_workbench_delete
on public.outcome_transfer_axis
for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_role_link_workbench_insert
on public.outcome_role_link
for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_role_link_workbench_update
on public.outcome_role_link
for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_role_link_workbench_delete
on public.outcome_role_link
for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_bridge_evidence_workbench_insert
on public.outcome_bridge_evidence
for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_bridge_evidence_workbench_update
on public.outcome_bridge_evidence
for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy outcome_bridge_evidence_workbench_delete
on public.outcome_bridge_evidence
for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));


-- Owner-only controlled vocabulary / legacy semantic authority.
create policy outcome_distance_definition_workbench_insert
on public.outcome_distance_definition
for insert to authenticated
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy outcome_distance_definition_workbench_update
on public.outcome_distance_definition
for update to authenticated
using ((select private.has_workbench_role(array['owner']::text[])))
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy outcome_distance_definition_workbench_delete
on public.outcome_distance_definition
for delete to authenticated
using ((select private.has_workbench_role(array['owner']::text[])));

create policy outcome_time_definition_workbench_insert
on public.outcome_time_definition
for insert to authenticated
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy outcome_time_definition_workbench_update
on public.outcome_time_definition
for update to authenticated
using ((select private.has_workbench_role(array['owner']::text[])))
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy outcome_time_definition_workbench_delete
on public.outcome_time_definition
for delete to authenticated
using ((select private.has_workbench_role(array['owner']::text[])));

create policy transfer_axis_definition_workbench_insert
on public.transfer_axis_definition
for insert to authenticated
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy transfer_axis_definition_workbench_update
on public.transfer_axis_definition
for update to authenticated
using ((select private.has_workbench_role(array['owner']::text[])))
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy transfer_axis_definition_workbench_delete
on public.transfer_axis_definition
for delete to authenticated
using ((select private.has_workbench_role(array['owner']::text[])));

create policy outcome_role_definition_workbench_insert
on public.outcome_role_definition
for insert to authenticated
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy outcome_role_definition_workbench_update
on public.outcome_role_definition
for update to authenticated
using ((select private.has_workbench_role(array['owner']::text[])))
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy outcome_role_definition_workbench_delete
on public.outcome_role_definition
for delete to authenticated
using ((select private.has_workbench_role(array['owner']::text[])));

create policy bridge_evidence_definition_workbench_insert
on public.bridge_evidence_definition
for insert to authenticated
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy bridge_evidence_definition_workbench_update
on public.bridge_evidence_definition
for update to authenticated
using ((select private.has_workbench_role(array['owner']::text[])))
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy bridge_evidence_definition_workbench_delete
on public.bridge_evidence_definition
for delete to authenticated
using ((select private.has_workbench_role(array['owner']::text[])));

create policy legacy_outcome_semantic_map_workbench_insert
on public.legacy_outcome_semantic_map
for insert to authenticated
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy legacy_outcome_semantic_map_workbench_update
on public.legacy_outcome_semantic_map
for update to authenticated
using ((select private.has_workbench_role(array['owner']::text[])))
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy legacy_outcome_semantic_map_workbench_delete
on public.legacy_outcome_semantic_map
for delete to authenticated
using ((select private.has_workbench_role(array['owner']::text[])));


-- ===========================================================================
-- 7. Audit coverage
-- ===========================================================================

drop trigger if exists audit_outcome_distance_definition on public.outcome_distance_definition;
create trigger audit_outcome_distance_definition
after insert or update or delete on public.outcome_distance_definition
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_outcome_time_definition on public.outcome_time_definition;
create trigger audit_outcome_time_definition
after insert or update or delete on public.outcome_time_definition
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_transfer_axis_definition on public.transfer_axis_definition;
create trigger audit_transfer_axis_definition
after insert or update or delete on public.transfer_axis_definition
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_outcome_role_definition on public.outcome_role_definition;
create trigger audit_outcome_role_definition
after insert or update or delete on public.outcome_role_definition
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_bridge_evidence_definition on public.bridge_evidence_definition;
create trigger audit_bridge_evidence_definition
after insert or update or delete on public.bridge_evidence_definition
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_legacy_outcome_semantic_map on public.legacy_outcome_semantic_map;
create trigger audit_legacy_outcome_semantic_map
after insert or update or delete on public.legacy_outcome_semantic_map
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_outcome_stage4_classification on public.outcome_stage4_classification;
create trigger audit_outcome_stage4_classification
after insert or update or delete on public.outcome_stage4_classification
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_outcome_time_link on public.outcome_time_link;
create trigger audit_outcome_time_link
after insert or update or delete on public.outcome_time_link
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_outcome_transfer_axis on public.outcome_transfer_axis;
create trigger audit_outcome_transfer_axis
after insert or update or delete on public.outcome_transfer_axis
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_outcome_role_link on public.outcome_role_link;
create trigger audit_outcome_role_link
after insert or update or delete on public.outcome_role_link
for each row execute function private.audit_workbench_change();

drop trigger if exists audit_outcome_bridge_evidence on public.outcome_bridge_evidence;
create trigger audit_outcome_bridge_evidence
after insert or update or delete on public.outcome_bridge_evidence
for each row execute function private.audit_workbench_change();
