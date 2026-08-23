create table public.csi_gateway_contract (
  contract_version text primary key,
  schema_version text not null,
  status text not null check (status in ('active','retired')),
  description text not null,
  query_contract jsonb not null,
  created_at timestamptz not null default now()
);

create table public.csi_gateway_release (
  evidence_release_id text primary key,
  contract_version text not null references public.csi_gateway_contract(contract_version),
  evidence_schema_version text not null,
  taxonomy_version text not null,
  source_release_status text not null,
  released_on date not null,
  published_at timestamptz not null default now(),
  source_record_count integer not null check (source_record_count >= 0),
  claim_count integer not null default 0 check (claim_count >= 0),
  status text not null check (status in ('published','retired')),
  is_current boolean not null default false,
  notes text
);

create table public.csi_gateway_evidence_card (
  card_id text primary key,
  evidence_release_id text not null references public.csi_gateway_release(evidence_release_id) on delete restrict,
  contract_version text not null references public.csi_gateway_contract(contract_version),
  status text not null check (status in ('published','retired')),
  evidence_class text not null check (evidence_class in ('direct_intervention','measurement_mechanism','human_ai_activity_system','other')),
  primary_classification text,
  secondary_component text,
  title text not null,
  authors jsonb not null default '[]'::jsonb,
  publication_year integer,
  publication_date date,
  venue text,
  source_kind text,
  peer_review_status text,
  doi text,
  pmid text,
  arxiv_id text,
  source_url text,
  study_design text,
  study_setting text,
  population_summary text,
  population_tags text[] not null default '{}'::text[],
  route_classes text[] not null default '{}'::text[],
  topic_tags text[] not null default '{}'::text[],
  functional_domains text[] not null default '{}'::text[],
  evidence_rungs text[] not null default '{}'::text[],
  transfer_axes text[] not null default '{}'::text[],
  product_ids text[] not null default '{}'::text[],
  component_summaries jsonb not null default '[]'::jsonb,
  outcome_summaries jsonb not null default '[]'::jsonb,
  product_relevance jsonb not null default '[]'::jsonb,
  route_rationale text,
  claim_level text not null check (claim_level in ('study_level_only','approved_synthesis_available')),
  approved_claim_ids text[] not null default '{}'::text[],
  required_caveats text[] not null default '{}'::text[],
  published_at timestamptz not null default now()
);

create table public.csi_gateway_claim (
  claim_id text primary key,
  evidence_release_id text not null references public.csi_gateway_release(evidence_release_id) on delete restrict,
  contract_version text not null references public.csi_gateway_contract(contract_version),
  status text not null check (status in ('published','retired')),
  product text,
  route_scope text,
  population_scope text,
  claim_text text not null,
  required_caveat text,
  certainty_judgement text,
  claim_version text not null,
  source_synthesis_id text,
  published_at timestamptz not null default now()
);

comment on table public.csi_gateway_contract is 'Versioned, read-only contract metadata for CSI evidence consumers. Contains no person/user data.';
comment on table public.csi_gateway_release is 'Published evidence release metadata for CSI applications. Separate from reviewer/workbench state.';
comment on table public.csi_gateway_evidence_card is 'Claims-safe study-level publication surface for CSI applications. No raw extraction JSON, reviewer notes, audit data, or person/user data.';
comment on table public.csi_gateway_claim is 'Future body-level approved claims for CSI applications. Empty until syntheses/claims are human-approved.';

insert into public.csi_gateway_contract (
  contract_version,
  schema_version,
  status,
  description,
  query_contract
) values (
  'csi-evidence-v1',
  '1.0.0',
  'active',
  'Read-only, release-pinned evidence contract for Personal, Work, Health and future CSI applications. CSI apps may read approved scientific evidence but never write user/person data into the Evidence Registry.',
  jsonb_build_object(
    'release_view','v_csi_gateway_release_v1',
    'evidence_view','v_csi_gateway_evidence_v1',
    'claim_view','v_csi_gateway_claim_v1',
    'contract_view','v_csi_gateway_contract_v1',
    'filters', jsonb_build_object(
      'evidence_release_id','eq',
      'evidence_class','eq|in',
      'primary_classification','eq|in',
      'route_classes','overlap',
      'population_tags','overlap',
      'topic_tags','overlap',
      'functional_domains','overlap',
      'product_ids','overlap',
      'evidence_rungs','overlap',
      'peer_review_status','eq|in'
    ),
    'recommended_order', jsonb_build_array('publication_date.desc','card_id.asc'),
    'guarantees', jsonb_build_array(
      'read_only',
      'approved_release_only',
      'release_pinned',
      'no_person_data',
      'no_workbench_or_audit_data',
      'no_raw_extraction_json',
      'study_level_claim_boundary_until_approved_synthesis'
    )
  )
);

insert into public.csi_gateway_release (
  evidence_release_id,
  contract_version,
  evidence_schema_version,
  taxonomy_version,
  source_release_status,
  released_on,
  source_record_count,
  claim_count,
  status,
  is_current,
  notes
)
select
  er.release_id,
  'csi-evidence-v1',
  er.schema_version,
  er.taxonomy_version,
  er.status,
  er.released_on,
  count(es.source_id)::integer,
  0,
  'published',
  true,
  'Initial CSI Gateway publication. Study-level evidence only; no approved body-level synthesis/claim rows existed at publication.'
from public.evidence_release er
join public.evidence_source es on es.release_id = er.release_id
where er.release_id = '2026-08-23'
  and er.status in ('approved_seed','approved_release')
  and es.review_status in ('approved_seed','approved_release')
group by er.release_id, er.schema_version, er.taxonomy_version, er.status, er.released_on;

insert into public.csi_gateway_evidence_card (
  card_id, evidence_release_id, contract_version, status, evidence_class,
  primary_classification, secondary_component, title, authors, publication_year,
  publication_date, venue, source_kind, peer_review_status, doi, pmid, arxiv_id,
  source_url, study_design, study_setting, population_summary, population_tags,
  route_classes, topic_tags, functional_domains, evidence_rungs, transfer_axes,
  product_ids, component_summaries, outcome_summaries, product_relevance,
  route_rationale, claim_level, approved_claim_ids, required_caveats
)
select
  es.source_id,
  es.release_id,
  'csi-evidence-v1',
  'published',
  case es.review_bucket
    when 'A_direct_intervention' then 'direct_intervention'
    when 'B_measurement_mechanism' then 'measurement_mechanism'
    when 'C_human_ai_activity_system' then 'human_ai_activity_system'
    else 'other'
  end,
  es.raw_record->'review'->>'primary_classification',
  es.raw_record->'review'->>'secondary_component',
  es.title,
  coalesce(es.authors,'[]'::jsonb),
  es.publication_year,
  es.publication_date,
  es.venue,
  es.source_kind,
  es.peer_review_status,
  es.doi,
  es.pmid,
  es.arxiv_id,
  es.source_url,
  s.design,
  s.setting,
  s.population_summary,
  coalesce(s.population_tags,'{}'::text[]),
  coalesce((select array_agg(distinct ic.route order by ic.route) from public.intervention_component ic where ic.study_id=s.study_id and ic.route is not null),'{}'::text[]),
  coalesce((select array_agg(tag order by tag) from jsonb_array_elements_text(coalesce(es.raw_record->'tags','[]'::jsonb)) tag),'{}'::text[]),
  coalesce((select array_agg(distinct eo.functional_domain order by eo.functional_domain) from public.evidence_outcome eo where eo.study_id=s.study_id and eo.functional_domain is not null),'{}'::text[]),
  coalesce((select array_agg(distinct eo.evidence_rung order by eo.evidence_rung) from public.evidence_outcome eo where eo.study_id=s.study_id and eo.evidence_rung is not null),'{}'::text[]),
  coalesce((select array_agg(distinct axis order by axis) from public.evidence_outcome eo cross join lateral unnest(eo.transfer_axes) axis where eo.study_id=s.study_id),'{}'::text[]),
  coalesce((select array_agg(distinct pr.product order by pr.product) from public.product_relevance pr where pr.source_id=es.source_id and pr.product is not null),'{}'::text[]),
  coalesce((select jsonb_agg(jsonb_strip_nulls(jsonb_build_object(
    'component_name',ic.component_name,
    'primary_route',ic.primary_route,
    'route',ic.route,
    'secondary_route',ic.secondary_route,
    'target_level',ic.target_level,
    'target_summary',ic.target_summary,
    'method_summary',ic.method_summary,
    'provider',ic.provider,
    'delivery_mode',ic.delivery_mode,
    'setting',ic.setting,
    'sessions_min',ic.sessions_min,
    'sessions_max',ic.sessions_max,
    'session_minutes_min',ic.session_minutes_min,
    'session_minutes_max',ic.session_minutes_max,
    'weeks_min',ic.weeks_min,
    'weeks_max',ic.weeks_max,
    'frequency_per_week_min',ic.frequency_per_week_min,
    'frequency_per_week_max',ic.frequency_per_week_max,
    'tailoring',ic.tailoring,
    'fidelity',ic.fidelity,
    'prompt_status',ic.prompt_status
  )) order by ic.component_id) from public.intervention_component ic where ic.study_id=s.study_id),'[]'::jsonb),
  coalesce((select jsonb_agg(jsonb_strip_nulls(jsonb_build_object(
    'outcome_name',eo.outcome_name,
    'measure_name',eo.measure_name,
    'functional_domain',eo.functional_domain,
    'timepoint',eo.timepoint,
    'evidence_rung',eo.evidence_rung,
    'transfer_axes',eo.transfer_axes,
    'bridge_evidence_level',eo.bridge_evidence_level,
    'result_direction',eo.result_direction,
    'result_summary',eo.result_summary,
    'effect_metric',eo.effect_metric,
    'effect_estimate',eo.effect_estimate,
    'ci_lower',eo.ci_lower,
    'ci_upper',eo.ci_upper,
    'objective',eo.objective
  )) order by eo.outcome_id) from public.evidence_outcome eo where eo.study_id=s.study_id),'[]'::jsonb),
  coalesce((select jsonb_agg(jsonb_strip_nulls(jsonb_build_object(
    'product',pr.product,
    'support_scope',pr.support_scope,
    'match_level',pr.match_level,
    'direction',pr.direction,
    'claim_status',pr.claim_status,
    'rationale',pr.rationale
  )) order by pr.product_relevance_id) from public.product_relevance pr where pr.source_id=es.source_id),'[]'::jsonb),
  es.route_rationale,
  'study_level_only',
  '{}'::text[],
  case es.review_bucket
    when 'B_measurement_mechanism' then array[
      'Study-level evidence card; no approved body-level synthesis or claim is available yet.',
      'Mechanism/measurement evidence should not be presented as intervention-efficacy evidence.'
    ]::text[]
    when 'C_human_ai_activity_system' then array[
      'Study-level evidence card; no approved body-level synthesis or claim is available yet.',
      'Human-AI activity-system findings must be interpreted within the design and population studied; causal strength varies by study design.'
    ]::text[]
    else array[
      'Study-level evidence card; no approved body-level synthesis or claim is available yet.',
      'A single study does not establish that the intervention will improve an individual CSI user or that gains will transfer to the user''s valued real-world goal.'
    ]::text[]
  end
from public.evidence_source es
join public.evidence_release er on er.release_id=es.release_id
left join public.study s on s.source_id=es.source_id
where es.release_id='2026-08-23'
  and es.review_status in ('approved_seed','approved_release')
  and er.status in ('approved_seed','approved_release');

alter table public.csi_gateway_contract enable row level security;
alter table public.csi_gateway_release enable row level security;
alter table public.csi_gateway_evidence_card enable row level security;
alter table public.csi_gateway_claim enable row level security;

create policy csi_gateway_contract_public_read on public.csi_gateway_contract for select to anon, authenticated using (status='active');
create policy csi_gateway_release_public_read on public.csi_gateway_release for select to anon, authenticated using (status='published');
create policy csi_gateway_evidence_public_read on public.csi_gateway_evidence_card for select to anon, authenticated using (status='published');
create policy csi_gateway_claim_public_read on public.csi_gateway_claim for select to anon, authenticated using (status='published');

revoke all on table public.csi_gateway_contract from anon, authenticated;
revoke all on table public.csi_gateway_release from anon, authenticated;
revoke all on table public.csi_gateway_evidence_card from anon, authenticated;
revoke all on table public.csi_gateway_claim from anon, authenticated;

grant select on table public.csi_gateway_contract to anon, authenticated;
grant select on table public.csi_gateway_release to anon, authenticated;
grant select on table public.csi_gateway_evidence_card to anon, authenticated;
grant select on table public.csi_gateway_claim to anon, authenticated;

create index csi_gateway_evidence_release_idx on public.csi_gateway_evidence_card(evidence_release_id);
create index csi_gateway_evidence_class_idx on public.csi_gateway_evidence_card(evidence_class);
create index csi_gateway_evidence_primary_class_idx on public.csi_gateway_evidence_card(primary_classification);
create index csi_gateway_evidence_publication_date_idx on public.csi_gateway_evidence_card(publication_date desc);
create index csi_gateway_evidence_routes_gin on public.csi_gateway_evidence_card using gin(route_classes);
create index csi_gateway_evidence_population_gin on public.csi_gateway_evidence_card using gin(population_tags);
create index csi_gateway_evidence_topics_gin on public.csi_gateway_evidence_card using gin(topic_tags);
create index csi_gateway_evidence_functional_domains_gin on public.csi_gateway_evidence_card using gin(functional_domains);
create index csi_gateway_evidence_products_gin on public.csi_gateway_evidence_card using gin(product_ids);
create index csi_gateway_evidence_rungs_gin on public.csi_gateway_evidence_card using gin(evidence_rungs);

create view public.v_csi_gateway_contract_v1 with (security_invoker=true) as
select contract_version, schema_version, description, query_contract, created_at
from public.csi_gateway_contract where status='active';

create view public.v_csi_gateway_release_v1 with (security_invoker=true) as
select evidence_release_id, contract_version, evidence_schema_version, taxonomy_version,
       source_release_status, released_on, published_at, source_record_count, claim_count,
       is_current, notes
from public.csi_gateway_release where status='published';

create view public.v_csi_gateway_evidence_v1 with (security_invoker=true) as
select card_id, evidence_release_id, contract_version, evidence_class,
       primary_classification, secondary_component, title, authors,
       publication_year, publication_date, venue, source_kind, peer_review_status,
       doi, pmid, arxiv_id, source_url, study_design, study_setting,
       population_summary, population_tags, route_classes, topic_tags,
       functional_domains, evidence_rungs, transfer_axes, product_ids,
       component_summaries, outcome_summaries, product_relevance, route_rationale,
       claim_level, approved_claim_ids, required_caveats, published_at
from public.csi_gateway_evidence_card where status='published';

create view public.v_csi_gateway_claim_v1 with (security_invoker=true) as
select claim_id, evidence_release_id, contract_version, product, route_scope,
       population_scope, claim_text, required_caveat, certainty_judgement,
       claim_version, source_synthesis_id, published_at
from public.csi_gateway_claim where status='published';

revoke all on table public.v_csi_gateway_contract_v1 from anon, authenticated;
revoke all on table public.v_csi_gateway_release_v1 from anon, authenticated;
revoke all on table public.v_csi_gateway_evidence_v1 from anon, authenticated;
revoke all on table public.v_csi_gateway_claim_v1 from anon, authenticated;

grant select on table public.v_csi_gateway_contract_v1 to anon, authenticated;
grant select on table public.v_csi_gateway_release_v1 to anon, authenticated;
grant select on table public.v_csi_gateway_evidence_v1 to anon, authenticated;
grant select on table public.v_csi_gateway_claim_v1 to anon, authenticated;

comment on view public.v_csi_gateway_contract_v1 is 'CSI Evidence Gateway v1 contract metadata. Public read-only.';
comment on view public.v_csi_gateway_release_v1 is 'CSI Evidence Gateway v1 published release metadata. Public read-only.';
comment on view public.v_csi_gateway_evidence_v1 is 'CSI Evidence Gateway v1 safe evidence cards. Public read-only; no raw Registry/Workbench data.';
comment on view public.v_csi_gateway_claim_v1 is 'CSI Evidence Gateway v1 approved claims. Empty until body-level claims are human-approved.';
