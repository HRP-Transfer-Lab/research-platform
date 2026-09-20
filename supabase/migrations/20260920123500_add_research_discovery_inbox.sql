create table if not exists public.research_candidate (
  candidate_id text primary key,
  source text not null,
  title text not null,
  identifiers jsonb not null default '{}'::jsonb,
  published_raw text,
  venue text,
  source_url text,
  topic_family text not null,
  consumers text[] not null default '{}',
  relevance_terms text[] not null default '{}',
  discovery_status text not null default 'discovered_unscreened'
    check (discovery_status in ('discovered_unscreened','screening','include_for_review','exclude','duplicate')),
  claim_status text not null default 'no_public_claim'
    check (claim_status = 'no_public_claim'),
  exclusion_reason text,
  raw_candidate jsonb not null default '{}'::jsonb,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  screened_at timestamptz,
  screened_by uuid references auth.users(id)
);

create index if not exists research_candidate_status_idx
  on public.research_candidate(discovery_status);

create index if not exists research_candidate_topic_idx
  on public.research_candidate(topic_family);

alter table public.research_candidate enable row level security;

revoke all on public.research_candidate from anon;
grant select, insert, update, delete on public.research_candidate to authenticated, service_role;

create policy research_candidate_workbench_read
on public.research_candidate for select
to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy research_candidate_workbench_insert
on public.research_candidate for insert
to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy research_candidate_workbench_update
on public.research_candidate for update
to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy research_candidate_workbench_delete
on public.research_candidate for delete
to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

drop trigger if exists audit_research_candidate on public.research_candidate;
create trigger audit_research_candidate
after insert or update or delete on public.research_candidate
for each row execute function private.audit_workbench_change();

comment on table public.research_candidate is
'Discovery-only literature inbox. Rows are not Evidence Registry sources and cannot support public claims until separately screened, extracted, reviewed and released.';
