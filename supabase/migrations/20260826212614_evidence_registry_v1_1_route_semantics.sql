-- HRP Transfer Evidence Registry v1.1
-- Stage 1: separate canonical intervention routes from evidence roles and
-- controller/overlay classifications.
--
-- This migration is additive and backward compatible.
-- It does not modify the immutable 2026-08-23 release JSON or CSI Gateway v1.

-- ---------------------------------------------------------------------------
-- 1. Controlled evidence-role vocabulary
-- ---------------------------------------------------------------------------

create table public.evidence_role_definition (
  evidence_role text primary key,
  label text not null,
  description text not null,
  active boolean not null default true
);

insert into public.evidence_role_definition (
  evidence_role,
  label,
  description
) values
(
  'direct_intervention',
  'Direct intervention',
  'Direct empirical evidence involving an intervention, manipulation, programme, policy, or activity-system change.'
),
(
  'mechanism',
  'Mechanism',
  'Evidence informing a mechanism, cognitive process, causal pathway, target-engagement hypothesis, or intervention rationale without itself establishing the target intervention claim.'
),
(
  'measurement',
  'Measurement',
  'Evidence informing measurement validity, reliability, construct representation, assessment design, or interpretation.'
),
(
  'observational',
  'Observational',
  'Non-interventional evidence describing associations, trajectories, naturally occurring behaviour, activity-system coupling, or other observational patterns.'
),
(
  'synthesis',
  'Synthesis',
  'Evidence contribution that synthesises multiple studies, including systematic reviews, meta-analyses, and other reviewed evidence syntheses.'
);

comment on table public.evidence_role_definition is
'Controlled v1.1 evidence-role vocabulary. Evidence role describes the evidential contribution and is independent of intervention route.';


-- ---------------------------------------------------------------------------
-- 2. Controlled controller / overlay vocabulary
-- ---------------------------------------------------------------------------

create table public.controller_overlay_definition (
  controller_overlay text primary key,
  label text not null,
  description text not null,
  active boolean not null default true
);

insert into public.controller_overlay_definition (
  controller_overlay,
  label,
  description
) values
(
  'metacognitive_governor',
  'Metacognitive governor',
  'Cross-cutting monitoring, evaluation, strategy selection, confidence regulation, or control structure. It is not an intervention route.'
),
(
  'adaptive_controller',
  'Adaptive controller',
  'A controller that changes task, intervention, policy, difficulty, or support contingent on observed state or performance.'
),
(
  'external_scaffold',
  'External scaffold',
  'An external aid, prompt, checklist, cue, workflow support, or other scaffold that structures deployment without itself defining the intervention route.'
),
(
  'other_controller_or_overlay',
  'Other controller or overlay',
  'A controller, supervisory structure, or overlay not represented by another controlled value.'
);

comment on table public.controller_overlay_definition is
'Controlled controller/overlay vocabulary. Controller semantics must never be stored as intervention routes.';


-- ---------------------------------------------------------------------------
-- 3. Explicit legacy-classification compatibility resolver
-- ---------------------------------------------------------------------------

create table public.legacy_classification_semantic_map (
  legacy_classification text primary key,
  canonical_route text,
  default_evidence_role text references public.evidence_role_definition(evidence_role),
  default_controller_overlay text references public.controller_overlay_definition(controller_overlay),
  review_required boolean not null default false,
  notes text,
  constraint legacy_semantic_map_route_check check (
    canonical_route is null
    or canonical_route in (
      'develop_equip',
      'develop_train',
      'develop_condition',
      'regulate',
      'bridge',
      'redesign',
      'integrate'
    )
  )
);

insert into public.legacy_classification_semantic_map (
  legacy_classification,
  canonical_route,
  default_evidence_role,
  default_controller_overlay,
  review_required,
  notes
) values

-- Seven true routes.
(
  'develop_equip',
  'develop_equip',
  'direct_intervention',
  null,
  false,
  'Canonical intervention route.'
),
(
  'develop_train',
  'develop_train',
  'direct_intervention',
  null,
  false,
  'Canonical intervention route.'
),
(
  'develop_condition',
  'develop_condition',
  'direct_intervention',
  null,
  false,
  'Canonical intervention route.'
),
(
  'regulate',
  'regulate',
  'direct_intervention',
  null,
  false,
  'Canonical intervention route.'
),
(
  'bridge',
  'bridge',
  'direct_intervention',
  null,
  false,
  'Canonical intervention route.'
),
(
  'redesign',
  'redesign',
  'direct_intervention',
  null,
  false,
  'Canonical intervention route.'
),
(
  'integrate',
  'integrate',
  'direct_intervention',
  null,
  false,
  'Canonical intervention route.'
),

-- Historical non-route classifications.
(
  'measure_prove',
  null,
  'measurement',
  null,
  false,
  'Historical Measure / Prove classification. Measurement/evidence architecture is not an intervention route.'
),
(
  'mechanism_evidence',
  null,
  'mechanism',
  null,
  false,
  'Historical mechanism-evidence classification; intentionally has no canonical intervention route.'
),
(
  'mechanism_and_training_design_evidence',
  null,
  'mechanism',
  null,
  false,
  'Mechanism and training-design evidence; does not by itself define an intervention route.'
),
(
  'metacognitive_governor_evidence',
  null,
  'mechanism',
  'metacognitive_governor',
  false,
  'Metacognitive Governor evidence. Governor is a cross-cutting controller, not an intervention route.'
),
(
  'state_mechanism_evidence',
  null,
  'mechanism',
  null,
  false,
  'State-mechanism evidence. A Regulate intervention must not be inferred merely from mechanistic state evidence.'
),
(
  'negative_metacognitive_overlay_evidence',
  null,
  'mechanism',
  'metacognitive_governor',
  true,
  'Negative or boundary evidence involving a metacognitive overlay. Requires substantive review before inferring intervention implications.'
),
(
  'observational_human_ai_coupling_taxonomy',
  null,
  'observational',
  null,
  false,
  'Observational human-AI coupling evidence; intentionally has no intervention route.'
);

comment on table public.legacy_classification_semantic_map is
'Compatibility resolver for historical raw_record.review.primary_classification values. Historical JSON remains unchanged.';


-- ---------------------------------------------------------------------------
-- 4. Many-to-many source evidence-role links
-- ---------------------------------------------------------------------------

create table public.source_evidence_role (
  source_id text not null references public.evidence_source(source_id) on delete cascade,
  evidence_role text not null references public.evidence_role_definition(evidence_role),
  primary_role boolean not null default false,
  rationale text,
  mapping_source text not null default 'human_review'
    check (mapping_source in ('legacy_resolver','human_review','manual','migration')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (source_id, evidence_role)
);

create unique index source_evidence_role_one_primary_idx
  on public.source_evidence_role(source_id)
  where primary_role is true;

create index source_evidence_role_role_idx
  on public.source_evidence_role(evidence_role);

comment on table public.source_evidence_role is
'Many-to-many source evidence-role classification. A source may make several evidential contributions; one may be marked primary.';


-- ---------------------------------------------------------------------------
-- 5. Source/component-aware controller / overlay links
-- ---------------------------------------------------------------------------

create table public.source_controller_overlay (
  source_controller_overlay_id bigint generated always as identity primary key,
  source_id text not null references public.evidence_source(source_id) on delete cascade,
  component_id bigint references public.intervention_component(component_id) on delete cascade,
  controller_overlay text not null references public.controller_overlay_definition(controller_overlay),
  rationale text,
  mapping_source text not null default 'human_review'
    check (mapping_source in ('legacy_resolver','human_review','manual','migration')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index source_controller_overlay_source_unique_idx
  on public.source_controller_overlay(source_id, controller_overlay)
  where component_id is null;

create unique index source_controller_overlay_component_unique_idx
  on public.source_controller_overlay(source_id, component_id, controller_overlay)
  where component_id is not null;

create index source_controller_overlay_source_idx
  on public.source_controller_overlay(source_id);

create index source_controller_overlay_component_idx
  on public.source_controller_overlay(component_id)
  where component_id is not null;

comment on table public.source_controller_overlay is
'Controller/overlay classification linked at source level and optionally component level. Controller semantics remain orthogonal to intervention route.';


-- ---------------------------------------------------------------------------
-- 6. Enforce the seven true routes in normalized intervention components
-- ---------------------------------------------------------------------------

alter table public.intervention_component
  add constraint intervention_component_route_canonical_v1_1_check
  check (
    route in (
      'develop_equip',
      'develop_train',
      'develop_condition',
      'regulate',
      'bridge',
      'redesign',
      'integrate'
    )
  )
  not valid;

-- Existing normalized seed components are expected to satisfy the new rule.
alter table public.intervention_component
  validate constraint intervention_component_route_canonical_v1_1_check;

comment on constraint intervention_component_route_canonical_v1_1_check
on public.intervention_component is
'Registry v1.1: intervention_component.route is restricted to the seven canonical Transfer Route Framework routes.';


-- ---------------------------------------------------------------------------
-- 7. RLS and Workbench permissions
-- ---------------------------------------------------------------------------

alter table public.evidence_role_definition enable row level security;
alter table public.controller_overlay_definition enable row level security;
alter table public.legacy_classification_semantic_map enable row level security;
alter table public.source_evidence_role enable row level security;
alter table public.source_controller_overlay enable row level security;

revoke all on table public.evidence_role_definition from anon, authenticated;
revoke all on table public.controller_overlay_definition from anon, authenticated;
revoke all on table public.legacy_classification_semantic_map from anon, authenticated;
revoke all on table public.source_evidence_role from anon, authenticated;
revoke all on table public.source_controller_overlay from anon, authenticated;

grant select, insert, update, delete
  on table public.evidence_role_definition
  to authenticated, service_role;

grant select, insert, update, delete
  on table public.controller_overlay_definition
  to authenticated, service_role;

grant select, insert, update, delete
  on table public.legacy_classification_semantic_map
  to authenticated, service_role;

grant select, insert, update, delete
  on table public.source_evidence_role
  to authenticated, service_role;

grant select, insert, update, delete
  on table public.source_controller_overlay
  to authenticated, service_role;

grant usage, select
  on sequence public.source_controller_overlay_source_controller_overlay_id_seq
  to authenticated, service_role;


-- Definitions / resolver: all Workbench members may read; owners may edit.

create policy evidence_role_definition_workbench_read
on public.evidence_role_definition
for select
to authenticated
using (
  (select private.has_workbench_role(array['viewer','editor','owner']::text[]))
);

create policy evidence_role_definition_workbench_insert
on public.evidence_role_definition
for insert
to authenticated
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy evidence_role_definition_workbench_update
on public.evidence_role_definition
for update
to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
)
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy evidence_role_definition_workbench_delete
on public.evidence_role_definition
for delete
to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
);


create policy controller_overlay_definition_workbench_read
on public.controller_overlay_definition
for select
to authenticated
using (
  (select private.has_workbench_role(array['viewer','editor','owner']::text[]))
);

create policy controller_overlay_definition_workbench_insert
on public.controller_overlay_definition
for insert
to authenticated
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy controller_overlay_definition_workbench_update
on public.controller_overlay_definition
for update
to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
)
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy controller_overlay_definition_workbench_delete
on public.controller_overlay_definition
for delete
to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
);


create policy legacy_semantic_map_workbench_read
on public.legacy_classification_semantic_map
for select
to authenticated
using (
  (select private.has_workbench_role(array['viewer','editor','owner']::text[]))
);

create policy legacy_semantic_map_workbench_insert
on public.legacy_classification_semantic_map
for insert
to authenticated
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy legacy_semantic_map_workbench_update
on public.legacy_classification_semantic_map
for update
to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
)
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy legacy_semantic_map_workbench_delete
on public.legacy_classification_semantic_map
for delete
to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
);


-- Source semantic links: viewers may read; editors/owners may review them.

create policy source_evidence_role_workbench_read
on public.source_evidence_role
for select
to authenticated
using (
  (select private.has_workbench_role(array['viewer','editor','owner']::text[]))
);

create policy source_evidence_role_workbench_insert
on public.source_evidence_role
for insert
to authenticated
with check (
  (select private.has_workbench_role(array['editor','owner']::text[]))
);

create policy source_evidence_role_workbench_update
on public.source_evidence_role
for update
to authenticated
using (
  (select private.has_workbench_role(array['editor','owner']::text[]))
)
with check (
  (select private.has_workbench_role(array['editor','owner']::text[]))
);

create policy source_evidence_role_workbench_delete
on public.source_evidence_role
for delete
to authenticated
using (
  (select private.has_workbench_role(array['editor','owner']::text[]))
);


create policy source_controller_overlay_workbench_read
on public.source_controller_overlay
for select
to authenticated
using (
  (select private.has_workbench_role(array['viewer','editor','owner']::text[]))
);

create policy source_controller_overlay_workbench_insert
on public.source_controller_overlay
for insert
to authenticated
with check (
  (select private.has_workbench_role(array['editor','owner']::text[]))
);

create policy source_controller_overlay_workbench_update
on public.source_controller_overlay
for update
to authenticated
using (
  (select private.has_workbench_role(array['editor','owner']::text[]))
)
with check (
  (select private.has_workbench_role(array['editor','owner']::text[]))
);

create policy source_controller_overlay_workbench_delete
on public.source_controller_overlay
for delete
to authenticated
using (
  (select private.has_workbench_role(array['editor','owner']::text[]))
);


-- ---------------------------------------------------------------------------
-- 8. Deterministic legacy resolver
--
-- This is necessary because on a clean replay the migration is applied before
-- bootstrap_local_registry.py loads the 18 historical sources.
--
-- Human-reviewed/manual semantic rows take precedence over resolver rows.
-- ---------------------------------------------------------------------------

create or replace function private.sync_source_semantics(p_source_id text)
returns void
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  v_classification text;
  v_source_kind text;
  v_role text;
  v_overlay text;
  v_review_required boolean;
  v_has_reviewed_roles boolean;
  v_has_reviewed_overlays boolean;
  v_rationale text;
begin
  select
    es.raw_record->'review'->>'primary_classification',
    es.source_kind
  into
    v_classification,
    v_source_kind
  from public.evidence_source es
  where es.source_id = p_source_id;

  if not found then
    return;
  end if;

  -- Remove only machine-derived compatibility rows.
  -- Human-reviewed/manual classifications are never overwritten.
  delete from public.source_evidence_role
  where source_id = p_source_id
    and mapping_source = 'legacy_resolver';

  delete from public.source_controller_overlay
  where source_id = p_source_id
    and mapping_source = 'legacy_resolver';

  select exists (
    select 1
    from public.source_evidence_role
    where source_id = p_source_id
      and mapping_source <> 'legacy_resolver'
  )
  into v_has_reviewed_roles;

  select exists (
    select 1
    from public.source_controller_overlay
    where source_id = p_source_id
      and mapping_source <> 'legacy_resolver'
  )
  into v_has_reviewed_overlays;

  select
    m.default_evidence_role,
    m.default_controller_overlay,
    m.review_required
  into
    v_role,
    v_overlay,
    v_review_required
  from public.legacy_classification_semantic_map m
  where m.legacy_classification = v_classification;

  v_rationale :=
    'Stage 1 compatibility resolver from historical primary_classification='
    || coalesce(v_classification, '[missing]')
    || '. Historical release JSON is unchanged.'
    || case
         when coalesce(v_review_required, false)
           then ' Substantive human review is required before stronger interpretation.'
         else ''
       end;

  if not v_has_reviewed_roles then

    -- A systematic review/meta-analysis is primarily a synthesis contribution.
    -- It may additionally concern a direct-intervention route.
    if v_source_kind = 'systematic_review_meta_analysis' then

      insert into public.source_evidence_role (
        source_id,
        evidence_role,
        primary_role,
        rationale,
        mapping_source
      ) values (
        p_source_id,
        'synthesis',
        true,
        'Source kind is systematic_review_meta_analysis. ' || v_rationale,
        'legacy_resolver'
      );

      if v_role is not null and v_role <> 'synthesis' then
        insert into public.source_evidence_role (
          source_id,
          evidence_role,
          primary_role,
          rationale,
          mapping_source
        ) values (
          p_source_id,
          v_role,
          false,
          v_rationale,
          'legacy_resolver'
        );
      end if;

    -- A scoping review can primarily serve measurement/mechanism purposes while
    -- also being explicitly identifiable as a synthesis-type source.
    elsif v_source_kind = 'scoping_review' then

      if v_role is not null then
        insert into public.source_evidence_role (
          source_id,
          evidence_role,
          primary_role,
          rationale,
          mapping_source
        ) values (
          p_source_id,
          v_role,
          true,
          v_rationale,
          'legacy_resolver'
        );
      end if;

      insert into public.source_evidence_role (
        source_id,
        evidence_role,
        primary_role,
        rationale,
        mapping_source
      ) values (
        p_source_id,
        'synthesis',
        v_role is null,
        'Source kind is scoping_review. ' || v_rationale,
        'legacy_resolver'
      );

    elsif v_role is not null then

      insert into public.source_evidence_role (
        source_id,
        evidence_role,
        primary_role,
        rationale,
        mapping_source
      ) values (
        p_source_id,
        v_role,
        true,
        v_rationale,
        'legacy_resolver'
      );

    end if;
  end if;

  if not v_has_reviewed_overlays and v_overlay is not null then
    insert into public.source_controller_overlay (
      source_id,
      component_id,
      controller_overlay,
      rationale,
      mapping_source
    ) values (
      p_source_id,
      null,
      v_overlay,
      v_rationale,
      'legacy_resolver'
    );
  end if;
end;
$$;

revoke all on function private.sync_source_semantics(text)
from public, anon;

grant execute on function private.sync_source_semantics(text)
to authenticated, service_role;


create or replace function private.sync_source_semantics_trigger()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
  perform private.sync_source_semantics(new.source_id);
  return new;
end;
$$;

revoke all on function private.sync_source_semantics_trigger()
from public, anon, authenticated;


drop trigger if exists sync_evidence_source_semantics
on public.evidence_source;

create trigger sync_evidence_source_semantics
after insert or update of raw_record, review_bucket, source_kind
on public.evidence_source
for each row
execute function private.sync_source_semantics_trigger();


-- Backfill any rows that already exist when this migration is applied.
-- On a clean local replay this is a no-op; the trigger handles later bootstrap.

do $$
declare
  r record;
begin
  for r in
    select source_id
    from public.evidence_source
    order by source_id
  loop
    perform private.sync_source_semantics(r.source_id);
  end loop;
end;
$$;


-- ---------------------------------------------------------------------------
-- 9. Audit the new Workbench-editable scientific dimensions
-- ---------------------------------------------------------------------------

drop trigger if exists audit_evidence_role_definition
on public.evidence_role_definition;

create trigger audit_evidence_role_definition
after insert or update or delete
on public.evidence_role_definition
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_controller_overlay_definition
on public.controller_overlay_definition;

create trigger audit_controller_overlay_definition
after insert or update or delete
on public.controller_overlay_definition
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_legacy_classification_semantic_map
on public.legacy_classification_semantic_map;

create trigger audit_legacy_classification_semantic_map
after insert or update or delete
on public.legacy_classification_semantic_map
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_source_evidence_role
on public.source_evidence_role;

create trigger audit_source_evidence_role
after insert or update or delete
on public.source_evidence_role
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_source_controller_overlay
on public.source_controller_overlay;

create trigger audit_source_controller_overlay
after insert or update or delete
on public.source_controller_overlay
for each row
execute function private.audit_workbench_change();
