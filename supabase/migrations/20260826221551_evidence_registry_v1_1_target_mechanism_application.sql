-- HRP Transfer Evidence Registry v1.1
-- Stage 3: Demand/Application Family, Target Locus, Target and Mechanism ontology.
--
-- Scientific rule:
--
-- APPLICATION FAMILY = where evidence may be useful
-- TARGET LOCUS       = level at which change is attempted/observed
-- TARGET             = specific process/capacity/state/policy/system property
-- MECHANISM          = proposed/tested process producing an effect
-- ROUTE              = how/where an intervention acts
--
-- These dimensions remain orthogonal.
--
-- This migration is additive and preserves:
--   * historical 2026-08-23 release
--   * evidence_source compatibility surface
--   * Stage 1 route/evidence-role semantics
--   * Stage 2 source identity/versioning
--   * csi-evidence-v1


-- ===========================================================================
-- 1. Demand / Application Family
-- ===========================================================================

create table public.application_family_definition (
  application_family text primary key,
  label text not null,
  description text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

insert into public.application_family_definition (
  application_family,
  label,
  description
) values
(
  'mental_fitness',
  'Mental fitness',
  'General maintenance, development or deployment of cognitive-affective capability outside a condition-specific treatment claim.'
),
(
  'performance',
  'Performance',
  'Evidence relevant to effective performance in demanding real-world, professional, operational or skilled activity.'
),
(
  'learning',
  'Learning',
  'Evidence relevant to acquisition, retention, retrieval, generalisation or effective use of knowledge and skills.'
),
(
  'executive_functioning',
  'Executive functioning',
  'Evidence relevant to executive control, working memory, attentional control, inhibition, cognitive flexibility or related control functions.'
),
(
  'wellbeing',
  'Wellbeing',
  'Evidence relevant to sustainable psychological functioning, stress burden, affective regulation or quality of functioning.'
),
(
  'longevity',
  'Longevity',
  'Evidence relevant to maintaining cognitive or cognitive-affective functioning across ageing and longer-term health trajectories.'
),
(
  'condition_related_support',
  'Condition-related support',
  'Evidence relevant to carefully bounded support in a defined health, rehabilitation or condition-related context without implying unreviewed clinical efficacy.'
);

comment on table public.application_family_definition is
'Broad use-case lens for evidence. Application family is not an intervention route, target, mechanism, population, outcome, or product-validation claim.';


create table public.source_version_application_family (
  source_version_id text not null
    references public.source_version(source_version_id)
    on delete cascade,

  application_family text not null
    references public.application_family_definition(application_family),

  relevance_level text not null
    check (
      relevance_level in (
        'primary',
        'secondary',
        'adjacent'
      )
    ),

  rationale text,

  mapping_source text not null default 'human_review'
    check (
      mapping_source in (
        'human_review',
        'manual',
        'migration',
        'agent_candidate'
      )
    ),

  review_status text not null default 'proposed'
    check (
      review_status in (
        'proposed',
        'reviewed',
        'approved',
        'rejected'
      )
    ),

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  primary key (
    source_version_id,
    application_family
  )
);

create index source_version_application_family_family_idx
  on public.source_version_application_family(application_family);

comment on table public.source_version_application_family is
'Many-to-many reviewed mapping from a source version to broad application families. Does not imply product validation or intervention efficacy.';


-- ===========================================================================
-- 2. Target locus
-- ===========================================================================

create table public.target_locus_definition (
  target_locus text primary key,
  label text not null,
  description text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

insert into public.target_locus_definition (
  target_locus,
  label,
  description
) values
(
  'biological_or_physiological_substrate',
  'Biological or physiological substrate',
  'Longer-lived biological or physiological substrate, capacity or operating-envelope property.'
),
(
  'current_operating_state',
  'Current operating state',
  'Acute or relatively short-lived state in which existing capability operates.'
),
(
  'cognitive_operation',
  'Cognitive operation',
  'Information-processing, cognitive-control or representational operation.'
),
(
  'affective_or_motivational_process',
  'Affective or motivational process',
  'Affective, motivational, valuation or appraisal process influencing cognition or action.'
),
(
  'explicit_strategy_or_policy',
  'Explicit strategy or policy',
  'Explicitly available strategy, rule, heuristic, implementation policy or metacognitive procedure.'
),
(
  'person_niche_coupling',
  'Person–niche coupling',
  'Connection between person-level policy/capability and cues, opportunities, actions or feedback in a target activity.'
),
(
  'niche_or_activity_system',
  'Niche or activity system',
  'Task, learning, work or human–AI activity-system structure, workflow, information flow, authority, affordances or contingencies.'
);

comment on table public.target_locus_definition is
'High-level scientific target-locus taxonomy. Target locus is related to but not synonymous with intervention route.';


-- ===========================================================================
-- 3. Neutral target ontology
-- ===========================================================================

create table public.target_definition (
  target_id text primary key,

  canonical_label text not null unique,

  target_locus text not null
    references public.target_locus_definition(target_locus),

  description text not null,

  ontology_status text not null default 'provisional'
    check (
      ontology_status in (
        'provisional',
        'reviewed',
        'active',
        'retired'
      )
    ),

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.target_definition is
'Scientifically neutral target construct ontology. Product/module-specific concepts belong in framework mapping tables rather than target identity.';


-- Small seed ontology only: grows from reviewed evidence.

insert into public.target_definition (
  target_id,
  canonical_label,
  target_locus,
  description,
  ontology_status
) values
(
  'target_working_memory_updating',
  'working_memory_updating',
  'cognitive_operation',
  'Updating and maintaining task-relevant working-memory contents.',
  'provisional'
),
(
  'target_relational_integration',
  'relational_integration',
  'cognitive_operation',
  'Integration of multiple relations or relational representations into a coherent structure.',
  'provisional'
),
(
  'target_attentional_selection',
  'attentional_selection',
  'cognitive_operation',
  'Selection and prioritisation of task-relevant information under competing input.',
  'provisional'
),
(
  'target_evidence_accumulation',
  'evidence_accumulation',
  'cognitive_operation',
  'Accumulation and weighting of evidence toward judgement or action.',
  'provisional'
),
(
  'target_response_inhibition',
  'response_inhibition',
  'cognitive_operation',
  'Suppression or withholding of a prepotent or no-longer-appropriate response.',
  'provisional'
),
(
  'target_acute_stress_state',
  'acute_stress_state',
  'current_operating_state',
  'Acute stress-related operating state affecting cognition, prediction or action.',
  'provisional'
),
(
  'target_metacognitive_monitoring_strategy',
  'metacognitive_monitoring_strategy',
  'explicit_strategy_or_policy',
  'Explicit monitoring or metacognitive strategy used to evaluate learning, confidence or control.',
  'provisional'
),
(
  'target_cue_triggered_strategy_deployment',
  'cue_triggered_strategy_deployment',
  'person_niche_coupling',
  'Recognition of contextual cues that trigger deployment of a learned strategy or policy.',
  'provisional'
),
(
  'target_human_ai_task_allocation',
  'human_ai_task_allocation',
  'niche_or_activity_system',
  'Allocation and sequencing of cognitive work between human and AI actors within an activity system.',
  'provisional'
),
(
  'target_cardiorespiratory_fitness',
  'cardiorespiratory_fitness',
  'biological_or_physiological_substrate',
  'Cardiorespiratory capacity as a physiological substrate relevant to cognitive functioning.',
  'provisional'
),
(
  'target_threat_appraisal',
  'threat_appraisal',
  'affective_or_motivational_process',
  'Appraisal of threat, challenge or risk influencing cognition, affect and action.',
  'provisional'
);


-- ===========================================================================
-- 4. Target aliases / author terminology
-- ===========================================================================

create table public.target_alias (
  target_alias_id bigint generated always as identity primary key,

  target_id text not null
    references public.target_definition(target_id)
    on delete cascade,

  alias_text text not null,

  alias_type text not null
    check (
      alias_type in (
        'author_term',
        'synonym',
        'legacy_hrp_term',
        'external_ontology_term'
      )
    ),

  source_version_id text
    references public.source_version(source_version_id)
    on delete cascade,

  created_at timestamptz not null default now()
);

create unique index target_alias_general_unique_idx
  on public.target_alias(
    target_id,
    lower(alias_text),
    alias_type
  )
  where source_version_id is null;

create unique index target_alias_source_unique_idx
  on public.target_alias(
    target_id,
    lower(alias_text),
    alias_type,
    source_version_id
  )
  where source_version_id is not null;

create index target_alias_target_idx
  on public.target_alias(target_id);

create index target_alias_source_version_idx
  on public.target_alias(source_version_id)
  where source_version_id is not null;

comment on table public.target_alias is
'Preserves author-reported, synonym, legacy or external ontology terminology without replacing the neutral target identity.';


-- ===========================================================================
-- 5. Intervention component → target mapping
-- ===========================================================================

create table public.component_target (
  component_id bigint not null
    references public.intervention_component(component_id)
    on delete cascade,

  target_id text not null
    references public.target_definition(target_id)
    on delete restrict,

  relationship text not null
    check (
      relationship in (
        'primary_target',
        'secondary_target',
        'target_engagement_only'
      )
    ),

  rationale text,

  mapping_source text not null default 'human_review'
    check (
      mapping_source in (
        'human_review',
        'manual',
        'migration',
        'agent_candidate'
      )
    ),

  review_status text not null default 'proposed'
    check (
      review_status in (
        'proposed',
        'reviewed',
        'approved',
        'rejected'
      )
    ),

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  primary key (
    component_id,
    target_id,
    relationship
  )
);

create index component_target_target_idx
  on public.component_target(target_id);

comment on table public.component_target is
'Reviewed mapping between an intervention component and neutral target constructs. Route and target remain separate scientific dimensions.';


-- ===========================================================================
-- 6. Explicit component-target extraction status
--
-- No component may rely on silent NULL to mean "no target".
-- ===========================================================================

create table public.component_target_extraction_status (
  component_id bigint primary key
    references public.intervention_component(component_id)
    on delete cascade,

  extraction_status text not null
    check (
      extraction_status in (
        'not_yet_extracted',
        'partially_extracted',
        'reviewed_complete',
        'not_reported',
        'not_applicable',
        'reviewed_no_mapping',
        'reviewed_mapped'
      )
    ),

  notes text,

  mapping_source text not null default 'migration'
    check (
      mapping_source in (
        'migration',
        'human_review',
        'manual',
        'agent_candidate'
      )
    ),

  updated_at timestamptz not null default now()
);

comment on table public.component_target_extraction_status is
'Explicit target-extraction completeness state. Missing target coding must never silently imply no target or negative evidence.';


-- Insert-time default for fresh imports / importer rebuilds.

create or replace function private.ensure_component_target_extraction_status()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin

  insert into public.component_target_extraction_status (
    component_id,
    extraction_status,
    mapping_source
  )
  values (
    new.component_id,
    'not_yet_extracted',
    'migration'
  )
  on conflict (component_id)
  do nothing;

  return new;
end;
$$;

revoke all on function private.ensure_component_target_extraction_status()
from public, anon, authenticated;


drop trigger if exists ensure_component_target_extraction_status
on public.intervention_component;

create trigger ensure_component_target_extraction_status
after insert
on public.intervention_component
for each row
execute function private.ensure_component_target_extraction_status();


-- Backfill components already present when migration is applied.

insert into public.component_target_extraction_status (
  component_id,
  extraction_status,
  mapping_source
)
select
  component_id,
  'not_yet_extracted',
  'migration'
from public.intervention_component
on conflict (component_id)
do nothing;


-- ===========================================================================
-- 7. Neutral mechanism ontology
-- ===========================================================================

create table public.mechanism_definition (
  mechanism_id text primary key,

  canonical_label text not null unique,

  description text not null,

  mechanism_status text not null default 'provisional'
    check (
      mechanism_status in (
        'provisional',
        'reviewed',
        'active',
        'retired'
      )
    ),

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.mechanism_definition is
'Scientifically neutral mechanism ontology. Mechanism describes a proposed/tested process pathway and is distinct from route and target.';


insert into public.mechanism_definition (
  mechanism_id,
  canonical_label,
  description,
  mechanism_status
) values
(
  'mechanism_error_driven_updating',
  'error_driven_updating',
  'Behavioural or representational updating driven by prediction or performance error.',
  'provisional'
),
(
  'mechanism_attentional_reweighting',
  'attentional_reweighting',
  'Change in the weighting or prioritisation of information during selection.',
  'provisional'
),
(
  'mechanism_stress_induced_prediction_shift',
  'stress_induced_prediction_shift',
  'Stress-related shift in reliance on statistical, predictive or other information-processing strategies.',
  'provisional'
),
(
  'mechanism_retrieval_practice_strengthening',
  'retrieval_practice_strengthening',
  'Strengthening of later accessibility or retention through active retrieval.',
  'provisional'
),
(
  'mechanism_cue_dependent_policy_activation',
  'cue_dependent_policy_activation',
  'Activation of a learned strategy or policy in response to contextual cues.',
  'provisional'
),
(
  'mechanism_offloading_induced_practice_reduction',
  'offloading_induced_practice_reduction',
  'Reduced human cognitive practice or engagement produced by externalisation or AI offloading.',
  'provisional'
),
(
  'mechanism_feedback_contingency_learning',
  'feedback_contingency_learning',
  'Learning driven by relationships between actions, outcomes and feedback contingencies.',
  'provisional'
);


-- ===========================================================================
-- 8. Mechanism assertions
--
-- Valid for intervention AND non-intervention evidence.
-- No synthetic intervention component is required.
-- ===========================================================================

create table public.mechanism_assertion (
  mechanism_assertion_id bigint generated always as identity primary key,

  source_version_id text not null
    references public.source_version(source_version_id)
    on delete cascade,

  mechanism_id text not null
    references public.mechanism_definition(mechanism_id)
    on delete restrict,

  study_id bigint
    references public.study(study_id)
    on delete cascade,

  component_id bigint
    references public.intervention_component(component_id)
    on delete cascade,

  assertion_type text not null
    check (
      assertion_type in (
        'author_proposed',
        'hrp_candidate',
        'experimentally_manipulated',
        'target_engagement_supported',
        'mediator_tested',
        'mediator_supported',
        'mediator_not_supported',
        'boundary_condition'
      )
    ),

  assertion_direction text not null
    check (
      assertion_direction in (
        'supports',
        'mixed',
        'null',
        'contradicts',
        'unclear',
        'not_applicable'
      )
    ),

  support_summary text,
  author_reported_text text,

  mapping_source text not null default 'human_review'
    check (
      mapping_source in (
        'human_review',
        'manual',
        'migration',
        'agent_candidate'
      )
    ),

  review_status text not null default 'proposed'
    check (
      review_status in (
        'proposed',
        'reviewed',
        'approved',
        'rejected'
      )
    ),

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index mechanism_assertion_source_version_idx
  on public.mechanism_assertion(source_version_id);

create index mechanism_assertion_mechanism_idx
  on public.mechanism_assertion(mechanism_id);

create index mechanism_assertion_study_idx
  on public.mechanism_assertion(study_id)
  where study_id is not null;

create index mechanism_assertion_component_idx
  on public.mechanism_assertion(component_id)
  where component_id is not null;

comment on table public.mechanism_assertion is
'Source-version-level mechanism assertion with optional study/component specificity. Supports positive, null, contradictory and boundary evidence without requiring an intervention route.';


-- ===========================================================================
-- 9. Explicit mechanism extraction status
-- ===========================================================================

create table public.source_version_mechanism_status (
  source_version_id text primary key
    references public.source_version(source_version_id)
    on delete cascade,

  extraction_status text not null
    check (
      extraction_status in (
        'not_yet_extracted',
        'partially_extracted',
        'not_reported',
        'not_applicable',
        'reviewed_no_mapping',
        'reviewed_mapped',
        'reviewed_complete'
      )
    ),

  notes text,

  mapping_source text not null default 'migration'
    check (
      mapping_source in (
        'migration',
        'human_review',
        'manual',
        'agent_candidate'
      )
    ),

  updated_at timestamptz not null default now()
);

comment on table public.source_version_mechanism_status is
'Explicit mechanism-extraction state for a reviewed source version. Absence of a mechanism assertion must not silently imply no mechanism or a null effect.';


create or replace function private.ensure_source_version_mechanism_status()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin

  insert into public.source_version_mechanism_status (
    source_version_id,
    extraction_status,
    mapping_source
  )
  values (
    new.source_version_id,
    'not_yet_extracted',
    'migration'
  )
  on conflict (source_version_id)
  do nothing;

  return new;
end;
$$;

revoke all on function private.ensure_source_version_mechanism_status()
from public, anon, authenticated;


drop trigger if exists ensure_source_version_mechanism_status
on public.source_version;

create trigger ensure_source_version_mechanism_status
after insert
on public.source_version
for each row
execute function private.ensure_source_version_mechanism_status();


insert into public.source_version_mechanism_status (
  source_version_id,
  extraction_status,
  mapping_source
)
select
  source_version_id,
  'not_yet_extracted',
  'migration'
from public.source_version
on conflict (source_version_id)
do nothing;


-- ===========================================================================
-- 10. Optional neutral → framework mappings
-- ===========================================================================

create table public.target_framework_mapping (
  target_id text not null
    references public.target_definition(target_id)
    on delete cascade,

  framework text not null
    check (
      framework in (
        'trident_g',
        'apc',
        'h_agi',
        'csi',
        'iqm_product_architecture'
      )
    ),

  framework_concept text not null,

  mapping_relation text not null
    check (
      mapping_relation in (
        'exact',
        'close',
        'broader',
        'narrower',
        'related'
      )
    ),

  rationale text,

  review_status text not null default 'proposed'
    check (
      review_status in (
        'proposed',
        'reviewed',
        'approved',
        'rejected'
      )
    ),

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  primary key (
    target_id,
    framework,
    framework_concept
  )
);

comment on table public.target_framework_mapping is
'Optional mapping from neutral scientific target constructs into HRP/IQM frameworks. Mapping does not imply author terminology.';


create table public.mechanism_framework_mapping (
  mechanism_id text not null
    references public.mechanism_definition(mechanism_id)
    on delete cascade,

  framework text not null
    check (
      framework in (
        'trident_g',
        'apc',
        'h_agi',
        'csi',
        'iqm_product_architecture'
      )
    ),

  framework_concept text not null,

  mapping_relation text not null
    check (
      mapping_relation in (
        'exact',
        'close',
        'broader',
        'narrower',
        'related'
      )
    ),

  rationale text,

  review_status text not null default 'proposed'
    check (
      review_status in (
        'proposed',
        'reviewed',
        'approved',
        'rejected'
      )
    ),

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  primary key (
    mechanism_id,
    framework,
    framework_concept
  )
);

comment on table public.mechanism_framework_mapping is
'Optional mapping from neutral scientific mechanisms into HRP/IQM frameworks. Mapping does not imply author terminology.';


-- ===========================================================================
-- 11. RLS
-- ===========================================================================

alter table public.application_family_definition enable row level security;
alter table public.source_version_application_family enable row level security;
alter table public.target_locus_definition enable row level security;
alter table public.target_definition enable row level security;
alter table public.target_alias enable row level security;
alter table public.component_target enable row level security;
alter table public.component_target_extraction_status enable row level security;
alter table public.mechanism_definition enable row level security;
alter table public.mechanism_assertion enable row level security;
alter table public.source_version_mechanism_status enable row level security;
alter table public.target_framework_mapping enable row level security;
alter table public.mechanism_framework_mapping enable row level security;


-- No anonymous access.

revoke all on table public.application_family_definition
from anon, authenticated;

revoke all on table public.source_version_application_family
from anon, authenticated;

revoke all on table public.target_locus_definition
from anon, authenticated;

revoke all on table public.target_definition
from anon, authenticated;

revoke all on table public.target_alias
from anon, authenticated;

revoke all on table public.component_target
from anon, authenticated;

revoke all on table public.component_target_extraction_status
from anon, authenticated;

revoke all on table public.mechanism_definition
from anon, authenticated;

revoke all on table public.mechanism_assertion
from anon, authenticated;

revoke all on table public.source_version_mechanism_status
from anon, authenticated;

revoke all on table public.target_framework_mapping
from anon, authenticated;

revoke all on table public.mechanism_framework_mapping
from anon, authenticated;


-- Workbench members can read all Stage 3 scientific structures.

grant select on table public.application_family_definition
to authenticated, service_role;

grant select on table public.source_version_application_family
to authenticated, service_role;

grant select on table public.target_locus_definition
to authenticated, service_role;

grant select on table public.target_definition
to authenticated, service_role;

grant select on table public.target_alias
to authenticated, service_role;

grant select on table public.component_target
to authenticated, service_role;

grant select on table public.component_target_extraction_status
to authenticated, service_role;

grant select on table public.mechanism_definition
to authenticated, service_role;

grant select on table public.mechanism_assertion
to authenticated, service_role;

grant select on table public.source_version_mechanism_status
to authenticated, service_role;

grant select on table public.target_framework_mapping
to authenticated, service_role;

grant select on table public.mechanism_framework_mapping
to authenticated, service_role;


-- Editors may review evidence annotations.

grant insert, update, delete
on table public.source_version_application_family
to authenticated, service_role;

grant insert, update, delete
on table public.target_alias
to authenticated, service_role;

grant insert, update, delete
on table public.component_target
to authenticated, service_role;

grant insert, update, delete
on table public.component_target_extraction_status
to authenticated, service_role;

grant insert, update, delete
on table public.mechanism_assertion
to authenticated, service_role;

grant insert, update, delete
on table public.source_version_mechanism_status
to authenticated, service_role;


-- Controlled ontology/framework definitions are owner-managed in browser,
-- while service_role retains maintenance rights.

grant insert, update, delete
on table public.application_family_definition
to authenticated, service_role;

grant insert, update, delete
on table public.target_locus_definition
to authenticated, service_role;

grant insert, update, delete
on table public.target_definition
to authenticated, service_role;

grant insert, update, delete
on table public.mechanism_definition
to authenticated, service_role;

grant insert, update, delete
on table public.target_framework_mapping
to authenticated, service_role;

grant insert, update, delete
on table public.mechanism_framework_mapping
to authenticated, service_role;


grant usage, select
on sequence public.target_alias_target_alias_id_seq
to authenticated, service_role;

grant usage, select
on sequence public.mechanism_assertion_mechanism_assertion_id_seq
to authenticated, service_role;


-- ===========================================================================
-- 12. Read policies
-- ===========================================================================

create policy application_family_definition_workbench_read
on public.application_family_definition
for select to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);

create policy source_version_application_family_workbench_read
on public.source_version_application_family
for select to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);

create policy target_locus_definition_workbench_read
on public.target_locus_definition
for select to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);

create policy target_definition_workbench_read
on public.target_definition
for select to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);

create policy target_alias_workbench_read
on public.target_alias
for select to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);

create policy component_target_workbench_read
on public.component_target
for select to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);

create policy component_target_status_workbench_read
on public.component_target_extraction_status
for select to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);

create policy mechanism_definition_workbench_read
on public.mechanism_definition
for select to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);

create policy mechanism_assertion_workbench_read
on public.mechanism_assertion
for select to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);

create policy source_version_mechanism_status_workbench_read
on public.source_version_mechanism_status
for select to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);

create policy target_framework_mapping_workbench_read
on public.target_framework_mapping
for select to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);

create policy mechanism_framework_mapping_workbench_read
on public.mechanism_framework_mapping
for select to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);


-- ===========================================================================
-- 13. Editor annotation policies
-- ===========================================================================

create policy source_version_application_family_workbench_insert
on public.source_version_application_family
for insert to authenticated
with check (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);

create policy source_version_application_family_workbench_update
on public.source_version_application_family
for update to authenticated
using (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
)
with check (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);

create policy source_version_application_family_workbench_delete
on public.source_version_application_family
for delete to authenticated
using (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);


create policy target_alias_workbench_insert
on public.target_alias
for insert to authenticated
with check (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);

create policy target_alias_workbench_update
on public.target_alias
for update to authenticated
using (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
)
with check (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);

create policy target_alias_workbench_delete
on public.target_alias
for delete to authenticated
using (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);


create policy component_target_workbench_insert
on public.component_target
for insert to authenticated
with check (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);

create policy component_target_workbench_update
on public.component_target
for update to authenticated
using (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
)
with check (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);

create policy component_target_workbench_delete
on public.component_target
for delete to authenticated
using (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);


create policy component_target_status_workbench_insert
on public.component_target_extraction_status
for insert to authenticated
with check (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);

create policy component_target_status_workbench_update
on public.component_target_extraction_status
for update to authenticated
using (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
)
with check (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);

create policy component_target_status_workbench_delete
on public.component_target_extraction_status
for delete to authenticated
using (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);


create policy mechanism_assertion_workbench_insert
on public.mechanism_assertion
for insert to authenticated
with check (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);

create policy mechanism_assertion_workbench_update
on public.mechanism_assertion
for update to authenticated
using (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
)
with check (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);

create policy mechanism_assertion_workbench_delete
on public.mechanism_assertion
for delete to authenticated
using (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);


create policy source_version_mechanism_status_workbench_insert
on public.source_version_mechanism_status
for insert to authenticated
with check (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);

create policy source_version_mechanism_status_workbench_update
on public.source_version_mechanism_status
for update to authenticated
using (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
)
with check (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);

create policy source_version_mechanism_status_workbench_delete
on public.source_version_mechanism_status
for delete to authenticated
using (
  (select private.has_workbench_role(
    array['editor','owner']::text[]
  ))
);


-- ===========================================================================
-- 14. Owner ontology-definition policies
-- ===========================================================================

create policy application_family_definition_workbench_insert
on public.application_family_definition
for insert to authenticated
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy application_family_definition_workbench_update
on public.application_family_definition
for update to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
)
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy application_family_definition_workbench_delete
on public.application_family_definition
for delete to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
);


create policy target_locus_definition_workbench_insert
on public.target_locus_definition
for insert to authenticated
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy target_locus_definition_workbench_update
on public.target_locus_definition
for update to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
)
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy target_locus_definition_workbench_delete
on public.target_locus_definition
for delete to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
);


create policy target_definition_workbench_insert
on public.target_definition
for insert to authenticated
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy target_definition_workbench_update
on public.target_definition
for update to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
)
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy target_definition_workbench_delete
on public.target_definition
for delete to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
);


create policy mechanism_definition_workbench_insert
on public.mechanism_definition
for insert to authenticated
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy mechanism_definition_workbench_update
on public.mechanism_definition
for update to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
)
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy mechanism_definition_workbench_delete
on public.mechanism_definition
for delete to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
);


create policy target_framework_mapping_workbench_insert
on public.target_framework_mapping
for insert to authenticated
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy target_framework_mapping_workbench_update
on public.target_framework_mapping
for update to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
)
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy target_framework_mapping_workbench_delete
on public.target_framework_mapping
for delete to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
);


create policy mechanism_framework_mapping_workbench_insert
on public.mechanism_framework_mapping
for insert to authenticated
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy mechanism_framework_mapping_workbench_update
on public.mechanism_framework_mapping
for update to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
)
with check (
  (select private.has_workbench_role(array['owner']::text[]))
);

create policy mechanism_framework_mapping_workbench_delete
on public.mechanism_framework_mapping
for delete to authenticated
using (
  (select private.has_workbench_role(array['owner']::text[]))
);


-- ===========================================================================
-- 15. Audit coverage
-- ===========================================================================

drop trigger if exists audit_application_family_definition
on public.application_family_definition;

create trigger audit_application_family_definition
after insert or update or delete
on public.application_family_definition
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_source_version_application_family
on public.source_version_application_family;

create trigger audit_source_version_application_family
after insert or update or delete
on public.source_version_application_family
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_target_locus_definition
on public.target_locus_definition;

create trigger audit_target_locus_definition
after insert or update or delete
on public.target_locus_definition
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_target_definition
on public.target_definition;

create trigger audit_target_definition
after insert or update or delete
on public.target_definition
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_target_alias
on public.target_alias;

create trigger audit_target_alias
after insert or update or delete
on public.target_alias
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_component_target
on public.component_target;

create trigger audit_component_target
after insert or update or delete
on public.component_target
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_component_target_extraction_status
on public.component_target_extraction_status;

create trigger audit_component_target_extraction_status
after insert or update or delete
on public.component_target_extraction_status
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_mechanism_definition
on public.mechanism_definition;

create trigger audit_mechanism_definition
after insert or update or delete
on public.mechanism_definition
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_mechanism_assertion
on public.mechanism_assertion;

create trigger audit_mechanism_assertion
after insert or update or delete
on public.mechanism_assertion
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_source_version_mechanism_status
on public.source_version_mechanism_status;

create trigger audit_source_version_mechanism_status
after insert or update or delete
on public.source_version_mechanism_status
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_target_framework_mapping
on public.target_framework_mapping;

create trigger audit_target_framework_mapping
after insert or update or delete
on public.target_framework_mapping
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_mechanism_framework_mapping
on public.mechanism_framework_mapping;

create trigger audit_mechanism_framework_mapping
after insert or update or delete
on public.mechanism_framework_mapping
for each row
execute function private.audit_workbench_change();


-- ===========================================================================
-- STAGE 3 REVIEWED-SEED ONTOLOGY EXTENSION
--
-- Added after review of the 18-source regression corpus.
-- Knowledge / learned representation must remain distinct from cognitive
-- operation. This prevents numerical knowledge, conceptual structure and
-- relational representations being forced into a processing-operation locus.
-- ===========================================================================

insert into public.target_locus_definition (
  target_locus,
  label,
  description
) values (
  'knowledge_or_mental_representation',
  'Knowledge or mental representation',
  'Learned, stored or structured knowledge, conceptual content, schemas, relational representations or other representational states distinct from the operations acting upon them.'
)
on conflict (target_locus) do nothing;


insert into public.target_definition (
  target_id,
  canonical_label,
  target_locus,
  description,
  ontology_status
) values

(
  'target_episodic_retrieval_specificity',
  'episodic_retrieval_specificity',
  'cognitive_operation',
  'Specific reconstruction and retrieval of episodic detail.',
  'provisional'
),

(
  'target_working_memory_function',
  'working_memory_function',
  'cognitive_operation',
  'Working-memory maintenance, manipulation or control at a level broader than a specific updating operation.',
  'provisional'
),

(
  'target_cognitive_flexibility',
  'cognitive_flexibility',
  'cognitive_operation',
  'Flexible switching or reconfiguration of cognitive rules, representations or task sets.',
  'provisional'
),

(
  'target_numerical_knowledge',
  'numerical_knowledge',
  'knowledge_or_mental_representation',
  'Domain-specific numerical knowledge or learned numerical representation.',
  'provisional'
),

(
  'target_multi_domain_executive_control',
  'multi_domain_executive_control',
  'cognitive_operation',
  'Coordinated executive-function capability spanning more than one executive operation.',
  'provisional'
),

(
  'target_physical_conditioning',
  'physical_conditioning',
  'biological_or_physiological_substrate',
  'Longer-term physical or physiological conditioning without presuming a more specific unmeasured biological mediator.',
  'provisional'
),

(
  'target_multi_domain_cognitive_function',
  'multi_domain_cognitive_function',
  'cognitive_operation',
  'Broad cognitive functioning spanning several trained cognitive domains.',
  'provisional'
),

(
  'target_feedback_architecture',
  'feedback_architecture',
  'niche_or_activity_system',
  'Structure by which task errors, information or performance feedback are delivered within an activity system.',
  'provisional'
),

(
  'target_mastery_progression_policy',
  'mastery_progression_policy',
  'niche_or_activity_system',
  'Progression rule governing when a learner advances, repeats or receives additional practice.',
  'provisional'
)

on conflict (target_id) do nothing;


insert into public.mechanism_definition (
  mechanism_id,
  canonical_label,
  description,
  mechanism_status
) values

(
  'mechanism_relational_structure_consolidation',
  'relational_structure_consolidation',
  'Emergence or strengthening over time of an abstract, stimulus-independent relational representation following learning.',
  'provisional'
),

(
  'mechanism_temporal_integration_generalization',
  'temporal_integration_generalization',
  'Relationship by which longer temporal integration or serial dependence supports generalisation across changed task instances or locations.',
  'provisional'
),

(
  'mechanism_confidence_gated_error_learning',
  'confidence_gated_error_learning',
  'Error-driven learning whose effect or processing pathway is moderated by confidence or metacognitive state.',
  'provisional'
)

on conflict (mechanism_id) do nothing;

