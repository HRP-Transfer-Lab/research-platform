-- HRP Transfer Evidence Registry v1.0.0
-- Hosted Supabase core schema. Applied to HRP-Transfer-Evidence on 2026-08-23.
-- Raw scientific/reviewer tables are closed to browser roles at bootstrap.

alter default privileges for role postgres in schema public
  revoke select, insert, update, delete on tables from anon, authenticated, service_role;
alter default privileges for role postgres in schema public
  revoke execute on functions from anon, authenticated, service_role;
alter default privileges for role postgres in schema public
  revoke usage, select on sequences from anon, authenticated, service_role;
alter default privileges for role postgres in schema public
  revoke execute on functions from public;

create table if not exists public.evidence_release (
  release_id text primary key,
  released_on date not null,
  schema_version text not null,
  taxonomy_version text not null,
  source_review_document text not null,
  source_review_section text,
  source_window_start date,
  source_window_end date,
  status text not null check (status in ('draft','approved_seed','approved_release','retired')),
  notes text
);

create table if not exists public.evidence_source (
  source_id text primary key,
  release_id text not null references public.evidence_release(release_id),
  review_bucket text not null check (review_bucket in ('A_direct_intervention','B_measurement_mechanism','C_human_ai_activity_system')),
  title text not null,
  authors jsonb not null default '[]'::jsonb,
  publication_year integer,
  publication_date date,
  venue text,
  source_kind text not null,
  peer_review_status text,
  doi text,
  pmid text,
  arxiv_id text,
  source_url text not null,
  review_status text not null,
  method_extraction_status text not null,
  route_rationale text,
  raw_record jsonb not null,
  unique (release_id, source_url)
);
create index if not exists evidence_source_release_idx on public.evidence_source(release_id);
create index if not exists evidence_source_bucket_idx on public.evidence_source(review_bucket);
create index if not exists evidence_source_doi_idx on public.evidence_source(doi) where doi is not null;

create table if not exists public.study (
  study_id bigserial primary key,
  source_id text not null references public.evidence_source(source_id) on delete cascade,
  design text,
  setting text,
  population_summary text,
  population_tags text[] not null default '{}',
  age_min numeric,
  age_max numeric,
  age_mean numeric,
  sample_json jsonb not null default '{}'::jsonb,
  comparator_summary text,
  preregistered boolean,
  registration_id text
);
create index if not exists study_source_idx on public.study(source_id);

create table if not exists public.intervention_component (
  component_id bigserial primary key,
  study_id bigint not null references public.study(study_id) on delete cascade,
  component_name text not null,
  primary_route boolean not null default false,
  route text not null,
  secondary_route text,
  target_level text,
  target_summary text,
  method_summary text,
  provider text,
  delivery_mode text,
  setting text,
  sessions_min numeric,
  sessions_max numeric,
  session_minutes_min numeric,
  session_minutes_max numeric,
  weeks_min numeric,
  weeks_max numeric,
  frequency_per_week_min numeric,
  frequency_per_week_max numeric,
  tailoring text,
  fidelity text,
  prompt_status text,
  protocol_json jsonb not null default '{}'::jsonb
);
create index if not exists intervention_component_study_idx on public.intervention_component(study_id);
create index if not exists intervention_component_route_idx on public.intervention_component(route);

create table if not exists public.evidence_outcome (
  outcome_id bigserial primary key,
  study_id bigint not null references public.study(study_id) on delete cascade,
  outcome_name text not null,
  measure_name text,
  functional_domain text,
  timepoint text,
  evidence_rung text,
  transfer_axes text[] not null default '{}',
  bridge_evidence_level text,
  result_direction text,
  result_summary text,
  effect_metric text,
  effect_estimate numeric,
  ci_lower numeric,
  ci_upper numeric,
  objective boolean,
  outcome_json jsonb not null default '{}'::jsonb
);
create index if not exists evidence_outcome_study_idx on public.evidence_outcome(study_id);
create index if not exists evidence_outcome_rung_idx on public.evidence_outcome(evidence_rung);

create table if not exists public.product_relevance (
  product_relevance_id bigserial primary key,
  source_id text not null references public.evidence_source(source_id) on delete cascade,
  product text not null,
  support_scope text,
  match_level text,
  direction text,
  claim_status text,
  rationale text,
  unique(source_id, product, support_scope)
);
create index if not exists product_relevance_source_idx on public.product_relevance(source_id);
create index if not exists product_relevance_product_idx on public.product_relevance(product);

create table if not exists public.quality_assessment (
  quality_assessment_id bigserial primary key,
  source_id text not null references public.evidence_source(source_id) on delete cascade,
  assessment_level text not null check (assessment_level in ('study','outcome','body_of_evidence','reporting')),
  tool text not null,
  judgement text,
  notes text,
  assessed_on date,
  assessor text
);
create index if not exists quality_assessment_source_idx on public.quality_assessment(source_id);

create table if not exists public.evidence_synthesis (
  synthesis_id text primary key,
  title text not null,
  pico_or_question text not null,
  route_filter text[],
  population_filter text[],
  target_filter text[],
  conclusion text,
  certainty_framework text,
  certainty_judgement text,
  status text not null default 'draft',
  version text not null,
  released_on date
);

create table if not exists public.synthesis_source (
  synthesis_id text not null references public.evidence_synthesis(synthesis_id) on delete cascade,
  source_id text not null references public.evidence_source(source_id) on delete cascade,
  inclusion_note text,
  primary key (synthesis_id, source_id)
);

create table if not exists public.approved_claim (
  claim_id text primary key,
  synthesis_id text references public.evidence_synthesis(synthesis_id),
  product text,
  claim_text text not null,
  required_caveat text,
  population_scope text,
  route_scope text,
  certainty_judgement text,
  status text not null check (status in ('draft','approved_internal','approved_public','retired')),
  version text not null
);

alter table public.evidence_release enable row level security;
alter table public.evidence_source enable row level security;
alter table public.study enable row level security;
alter table public.intervention_component enable row level security;
alter table public.evidence_outcome enable row level security;
alter table public.product_relevance enable row level security;
alter table public.quality_assessment enable row level security;
alter table public.evidence_synthesis enable row level security;
alter table public.synthesis_source enable row level security;
alter table public.approved_claim enable row level security;

revoke all on table public.evidence_release from anon, authenticated;
revoke all on table public.evidence_source from anon, authenticated;
revoke all on table public.study from anon, authenticated;
revoke all on table public.intervention_component from anon, authenticated;
revoke all on table public.evidence_outcome from anon, authenticated;
revoke all on table public.product_relevance from anon, authenticated;
revoke all on table public.quality_assessment from anon, authenticated;
revoke all on table public.evidence_synthesis from anon, authenticated;
revoke all on table public.synthesis_source from anon, authenticated;
revoke all on table public.approved_claim from anon, authenticated;

grant select, insert, update, delete on table public.evidence_release to service_role;
grant select, insert, update, delete on table public.evidence_source to service_role;
grant select, insert, update, delete on table public.study to service_role;
grant select, insert, update, delete on table public.intervention_component to service_role;
grant select, insert, update, delete on table public.evidence_outcome to service_role;
grant select, insert, update, delete on table public.product_relevance to service_role;
grant select, insert, update, delete on table public.quality_assessment to service_role;
grant select, insert, update, delete on table public.evidence_synthesis to service_role;
grant select, insert, update, delete on table public.synthesis_source to service_role;
grant select, insert, update, delete on table public.approved_claim to service_role;
grant usage, select on all sequences in schema public to service_role;

create or replace view public.v_approved_evidence
with (security_invoker = true) as
select
  es.source_id, es.release_id, es.review_bucket, es.title, es.publication_date,
  es.venue, es.source_kind, es.peer_review_status, es.doi, es.pmid, es.arxiv_id,
  es.source_url, es.route_rationale, es.raw_record
from public.evidence_source es
join public.evidence_release er on er.release_id = es.release_id
where es.review_status in ('approved_seed','approved_release')
  and er.status in ('approved_seed','approved_release');

create or replace view public.v_product_evidence
with (security_invoker = true) as
select
  es.source_id, es.title, es.review_bucket, pr.product, pr.support_scope,
  pr.match_level, pr.direction, pr.claim_status, pr.rationale
from public.evidence_source es
join public.product_relevance pr on pr.source_id = es.source_id
where es.review_status in ('approved_seed','approved_release');

revoke all on table public.v_approved_evidence from anon, authenticated;
revoke all on table public.v_product_evidence from anon, authenticated;
grant select on table public.v_approved_evidence to service_role;
grant select on table public.v_product_evidence to service_role;

comment on table public.evidence_source is 'One reviewed report/source. Route efficacy is never inferred from source_kind alone.';
comment on table public.intervention_component is 'Component-level route coding. Multicomponent arms can contain Train, Equip, Condition, Bridge, Redesign, etc. separately.';
comment on table public.evidence_outcome is 'Outcome-level proof coding. Evidence rung and transfer axis are separate from intervention route.';
comment on table public.quality_assessment is 'Study/outcome risk of bias and body-of-evidence certainty are stored separately; do not assign GRADE to an individual study.';
