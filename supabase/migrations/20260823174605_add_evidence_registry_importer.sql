-- Private idempotent importer for Git-approved evidence-record JSON.
-- This file contains the corrected replayable importer definition. The following
-- migration version is retained to mirror the hosted migration history.

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;
grant usage on schema private to service_role;

create or replace function private.import_evidence_record(p_record jsonb)
returns text
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  b jsonb := p_record->'bibliography';
  r jsonb := p_record->'review';
  s jsonb := p_record->'study';
  p jsonb := p_record->'protocol';
  pop jsonb := p_record->'study'->'population';
  rid text := p_record->>'record_id';
  sid bigint;
  item jsonb;
  route_name text;
  comp_name text;
begin
  if rid is null or p_record->>'release_id' is null then
    raise exception 'record_id and release_id are required';
  end if;

  insert into public.evidence_source (
    source_id, release_id, review_bucket, title, authors, publication_year,
    publication_date, venue, source_kind, peer_review_status, doi, pmid,
    arxiv_id, source_url, review_status, method_extraction_status,
    route_rationale, raw_record
  ) values (
    rid, p_record->>'release_id', p_record->>'review_bucket', b->>'title',
    coalesce(b->'authors','[]'::jsonb), nullif(b->>'year','')::integer,
    nullif(b->>'publication_date','')::date, b->>'venue',
    coalesce(b->>'source_kind','unknown'), b->>'peer_review_status', b->>'doi',
    b->>'pmid', b->>'arxiv_id', b->>'url', coalesce(r->>'review_status','draft'),
    coalesce(r->>'method_extraction_status','not_extracted'), r->>'route_rationale', p_record
  )
  on conflict (source_id) do update set
    release_id=excluded.release_id,
    review_bucket=excluded.review_bucket,
    title=excluded.title,
    authors=excluded.authors,
    publication_year=excluded.publication_year,
    publication_date=excluded.publication_date,
    venue=excluded.venue,
    source_kind=excluded.source_kind,
    peer_review_status=excluded.peer_review_status,
    doi=excluded.doi,
    pmid=excluded.pmid,
    arxiv_id=excluded.arxiv_id,
    source_url=excluded.source_url,
    review_status=excluded.review_status,
    method_extraction_status=excluded.method_extraction_status,
    route_rationale=excluded.route_rationale,
    raw_record=excluded.raw_record;

  -- Rebuild normalized child rows so the Git record remains the release source.
  delete from public.study where source_id = rid;
  delete from public.product_relevance where source_id = rid;

  insert into public.study (
    source_id, design, setting, population_summary, population_tags,
    age_min, age_max, age_mean, sample_json, comparator_summary,
    preregistered, registration_id
  ) values (
    rid,
    s->>'design',
    s->>'setting',
    pop->>'summary',
    coalesce(array(select jsonb_array_elements_text(coalesce(pop->'tags','[]'::jsonb))), '{}'::text[]),
    nullif(pop->>'age_min','')::numeric,
    nullif(pop->>'age_max','')::numeric,
    nullif(pop->>'age_mean','')::numeric,
    coalesce(s->'sample','{}'::jsonb),
    s->>'comparator',
    case when s ? 'preregistered' then (s->>'preregistered')::boolean else null end,
    s->>'registration_id'
  ) returning study_id into sid;

  -- Component rows are reserved for actual intervention-route components.
  if jsonb_typeof(p->'components') = 'array' then
    for item in select value from jsonb_array_elements(p->'components') loop
      route_name := coalesce(item->>'route', r->>'primary_classification');
      comp_name := coalesce(item->>'name', item->>'component', route_name, 'intervention component');

      insert into public.intervention_component (
        study_id, component_name, primary_route, route, secondary_route,
        target_level, target_summary, method_summary, provider, delivery_mode,
        setting, sessions_min, sessions_max, session_minutes_min,
        session_minutes_max, weeks_min, weeks_max, frequency_per_week_min,
        frequency_per_week_max, tailoring, fidelity, prompt_status, protocol_json
      ) values (
        sid,
        comp_name,
        false,
        route_name,
        null,
        item->>'target_level',
        coalesce(item->>'target_summary', case when item ? 'targets' then (item->'targets')::text else null end),
        item->>'method_summary',
        item->>'provider',
        coalesce(item->>'delivery_mode', p->>'delivery_mode'),
        coalesce(item->>'setting', s->>'setting'),
        coalesce(nullif(item->>'sessions_min','')::numeric, nullif(item->>'sessions','')::numeric),
        coalesce(nullif(item->>'sessions_max','')::numeric, nullif(item->>'sessions','')::numeric),
        coalesce(nullif(item->>'session_minutes_min','')::numeric, nullif(item->>'session_minutes','')::numeric),
        coalesce(nullif(item->>'session_minutes_max','')::numeric, nullif(item->>'session_minutes','')::numeric),
        coalesce(nullif(item->>'weeks_min','')::numeric, nullif(item->>'weeks','')::numeric),
        coalesce(nullif(item->>'weeks_max','')::numeric, nullif(item->>'weeks','')::numeric),
        coalesce(nullif(item->>'frequency_per_week_min','')::numeric, nullif(item->>'sessions_per_week','')::numeric),
        coalesce(nullif(item->>'frequency_per_week_max','')::numeric, nullif(item->>'sessions_per_week','')::numeric),
        item->>'tailoring',
        item->>'fidelity',
        item->>'prompt_status',
        item
      );
    end loop;
  elsif (r->>'primary_classification') = any(array[
    'develop_equip','develop_train','develop_condition','regulate','bridge','redesign','integrate'
  ]) then
    route_name := r->>'primary_classification';
    comp_name := coalesce(p->>'component', route_name);

    insert into public.intervention_component (
      study_id, component_name, primary_route, route, secondary_route,
      target_level, target_summary, method_summary, provider, delivery_mode,
      setting, sessions_min, sessions_max, session_minutes_min,
      session_minutes_max, weeks_min, weeks_max, frequency_per_week_min,
      frequency_per_week_max, tailoring, fidelity, prompt_status, protocol_json
    ) values (
      sid,
      comp_name,
      true,
      route_name,
      r->>'secondary_component',
      p->>'target_level',
      case when p ? 'targets' then (p->'targets')::text else p->>'target_summary' end,
      p->>'method_summary',
      p->>'provider',
      p->>'delivery_mode',
      s->>'setting',
      coalesce(nullif(p->>'sessions_min','')::numeric, nullif(p->>'sessions','')::numeric),
      coalesce(nullif(p->>'sessions_max','')::numeric, nullif(p->>'sessions','')::numeric),
      coalesce(nullif(p->>'session_minutes_min','')::numeric, nullif(p->>'session_minutes','')::numeric),
      coalesce(nullif(p->>'session_minutes_max','')::numeric, nullif(p->>'session_minutes','')::numeric),
      coalesce(nullif(p->>'weeks_min','')::numeric, nullif(p->>'weeks','')::numeric),
      coalesce(nullif(p->>'weeks_max','')::numeric, nullif(p->>'weeks','')::numeric),
      coalesce(nullif(p->>'frequency_per_week_min','')::numeric, nullif(p->>'sessions_per_week','')::numeric),
      coalesce(nullif(p->>'frequency_per_week_max','')::numeric, nullif(p->>'sessions_per_week','')::numeric),
      p->>'tailoring',
      p->>'fidelity',
      p->>'prompt_status',
      p
    );
  end if;

  if jsonb_typeof(p_record->'outcomes') = 'array' then
    for item in select value from jsonb_array_elements(p_record->'outcomes') loop
      insert into public.evidence_outcome (
        study_id, outcome_name, measure_name, functional_domain, timepoint,
        evidence_rung, transfer_axes, bridge_evidence_level, result_direction,
        result_summary, effect_metric, effect_estimate, ci_lower, ci_upper,
        objective, outcome_json
      ) values (
        sid,
        coalesce(item->>'name','unspecified outcome'),
        item->>'measure',
        item->>'functional_domain',
        item->>'timepoint',
        item->>'rung',
        coalesce(array(select jsonb_array_elements_text(coalesce(item->'transfer_axes','[]'::jsonb))), '{}'::text[]),
        item->>'bridge_evidence_level',
        item->>'direction',
        coalesce(item->>'summary', item->>'boundary'),
        item->>'effect_metric',
        nullif(item->>'effect','')::numeric,
        case when jsonb_typeof(item->'ci')='array' then nullif(item->'ci'->>0,'')::numeric else null end,
        case when jsonb_typeof(item->'ci')='array' then nullif(item->'ci'->>1,'')::numeric else null end,
        case when item ? 'objective' then (item->>'objective')::boolean else null end,
        item
      );
    end loop;
  end if;

  if jsonb_typeof(p_record->'product_relevance') = 'array' then
    for item in select value from jsonb_array_elements(p_record->'product_relevance') loop
      insert into public.product_relevance (
        source_id, product, support_scope, match_level, direction, claim_status, rationale
      ) values (
        rid,
        item->>'product',
        item->>'scope',
        item->>'match',
        item->>'direction',
        item->>'claim_status',
        item->>'rationale'
      );
    end loop;
  end if;

  return rid;
end;
$$;

revoke all on function private.import_evidence_record(jsonb) from public, anon, authenticated;
grant execute on function private.import_evidence_record(jsonb) to service_role;

-- Add framework classification directly to the safe server-side read model without
-- treating mechanism/measurement classifications as intervention components.
drop view if exists public.v_approved_evidence;
create view public.v_approved_evidence
with (security_invoker = true) as
select
  es.source_id,
  es.release_id,
  es.review_bucket,
  es.title,
  es.publication_date,
  es.venue,
  es.source_kind,
  es.peer_review_status,
  es.doi,
  es.pmid,
  es.arxiv_id,
  es.source_url,
  es.raw_record->'review'->>'primary_classification' as primary_classification,
  es.raw_record->'review'->'evidence_rungs' as evidence_rungs,
  es.raw_record->'tags' as tags,
  es.route_rationale,
  es.raw_record
from public.evidence_source es
join public.evidence_release er on er.release_id = es.release_id
where es.review_status in ('approved_seed','approved_release')
  and er.status in ('approved_seed','approved_release');

revoke all on table public.v_approved_evidence from anon, authenticated;
grant select on table public.v_approved_evidence to service_role;
