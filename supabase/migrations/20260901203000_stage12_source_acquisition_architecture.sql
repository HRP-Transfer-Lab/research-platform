-- HRP Transfer Evidence Registry v1.1
-- Stage 12: operational source acquisition / document artifact architecture.
--
-- Acquisition state is intentionally separate from scientific authority:
-- finding, losing, or changing access to a PDF must not alter reviewed science,
-- scientific_state_revision, immutable release membership, or CSI Gateway state.

-- ===========================================================================
-- 1. Current acquisition state per reviewed source version
-- ===========================================================================

create table public.source_acquisition_status (
  source_version_id text primary key
    references public.source_version(source_version_id) on delete cascade,

  access_status text not null default 'unknown' check (
    access_status in (
      'unknown','metadata_only','abstract_only','fulltext_available',
      'fulltext_verified','blocked','retrieval_failed'
    )
  ),
  access_route text not null default 'none' check (
    access_route in (
      'none','open_access','repository','author_preprint','publisher',
      'institutional_library','user_supplied','manual_web','other'
    )
  ),
  blocker_reason text not null default 'none' check (
    blocker_reason in (
      'none','paywall','institutional_unavailable','not_found','login_required',
      'technical_failure','license_restricted','other'
    )
  ),

  fulltext_available boolean not null default false,
  fulltext_verified boolean not null default false,

  supplement_status text not null default 'unknown' check (
    supplement_status in ('unknown','not_applicable','not_found','available','verified')
  ),
  protocol_status text not null default 'unknown' check (
    protocol_status in ('unknown','not_applicable','not_found','available','verified')
  ),
  registration_status text not null default 'unknown' check (
    registration_status in ('unknown','not_applicable','not_found','available','verified')
  ),

  needs_human_access boolean not null default false,
  last_checked_at timestamptz,
  next_retry_at timestamptz,
  notes text,

  recorded_by_kind text not null default 'system' check (
    recorded_by_kind in ('system','agent','human')
  ),
  verification_status text not null default 'unverified' check (
    verification_status in ('unverified','system_verified','human_verified')
  ),

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  check (not fulltext_verified or fulltext_available),
  check (
    (fulltext_available and access_status in ('fulltext_available','fulltext_verified'))
    or
    (not fulltext_available and access_status not in ('fulltext_available','fulltext_verified'))
  ),
  check (
    (access_status in ('blocked','retrieval_failed') and blocker_reason <> 'none')
    or
    (access_status not in ('blocked','retrieval_failed'))
  ),
  check (
    access_status not in ('blocked','retrieval_failed')
    or fulltext_available is false
  )
);

comment on table public.source_acquisition_status is
'Operational current source-access state per source_version. Access availability is not scientific quality, RoB, certainty, EML, review authority, or release publication state.';

-- ===========================================================================
-- 2. Append-only acquisition attempt history
-- ===========================================================================

create table public.source_acquisition_attempt (
  acquisition_attempt_id bigserial primary key,
  source_version_id text not null
    references public.source_version(source_version_id) on delete cascade,
  attempt_key text not null,
  attempted_at timestamptz not null default now(),

  requested_artifact_kind text not null check (
    requested_artifact_kind in (
      'full_text','supplement','protocol','sap','registration','other'
    )
  ),
  channel text not null check (
    channel in (
      'crossref','openalex','unpaywall','europe_pmc','pubmed','publisher',
      'repository','institutional_library','user_upload','manual_web','other'
    )
  ),
  attempted_by_kind text not null check (
    attempted_by_kind in ('system','agent','human')
  ),
  outcome text not null check (
    outcome in (
      'metadata_only','abstract_only','fulltext_acquired','supplement_acquired',
      'protocol_acquired','registration_acquired','blocked','not_found',
      'technical_failure','no_change'
    )
  ),
  access_route text not null default 'none' check (
    access_route in (
      'none','open_access','repository','author_preprint','publisher',
      'institutional_library','user_supplied','manual_web','other'
    )
  ),
  blocker_reason text not null default 'none' check (
    blocker_reason in (
      'none','paywall','institutional_unavailable','not_found','login_required',
      'technical_failure','license_restricted','other'
    )
  ),
  resolved_url text,
  http_status integer check (http_status is null or http_status between 100 and 599),
  tool_name text,
  tool_version text,
  notes text,

  unique (source_version_id, attempt_key),
  check (
    outcome not in ('blocked','technical_failure')
    or blocker_reason <> 'none'
  )
);

create index source_acquisition_attempt_version_idx
  on public.source_acquisition_attempt(source_version_id, attempted_at desc);
create index source_acquisition_attempt_outcome_idx
  on public.source_acquisition_attempt(outcome, attempted_at desc);

comment on table public.source_acquisition_attempt is
'Append-only acquisition/retrieval history. Stores routes/outcomes but never credentials, cookies, library tokens, or publisher secrets.';

-- ===========================================================================
-- 3. Document artifact inventory
-- ===========================================================================

create table public.source_document_artifact (
  source_document_artifact_id bigserial primary key,
  source_version_id text not null
    references public.source_version(source_version_id) on delete cascade,
  acquisition_attempt_id bigint
    references public.source_acquisition_attempt(acquisition_attempt_id) on delete set null,

  artifact_key text not null,
  artifact_kind text not null check (
    artifact_kind in (
      'full_text','supplement','protocol','sap','registration_record','other'
    )
  ),
  artifact_status text not null default 'available' check (
    artifact_status in ('available','verified','superseded','withdrawn')
  ),
  access_route text not null check (
    access_route in (
      'open_access','repository','author_preprint','publisher',
      'institutional_library','user_supplied','manual_web','other'
    )
  ),

  content_sha256 text,
  media_type text,
  byte_size bigint check (byte_size is null or byte_size >= 0),
  page_count integer check (page_count is null or page_count > 0),
  filename text,
  external_url text,

  storage_backend text not null default 'none' check (
    storage_backend in ('none','local_corpus','supabase_storage','external_url','other')
  ),
  storage_locator text,
  license_status text not null default 'unknown' check (
    license_status in (
      'unknown','open','institutional_use','user_provided','publisher_access','restricted'
    )
  ),
  notes text,
  created_at timestamptz not null default now(),
  verified_at timestamptz,

  unique (source_version_id, artifact_key),
  check (content_sha256 is null or content_sha256 ~ '^[0-9a-f]{64}$'),
  check (storage_backend <> 'none' or storage_locator is null)
);

create unique index source_document_artifact_hash_unique_idx
  on public.source_document_artifact(source_version_id, artifact_kind, content_sha256)
  where content_sha256 is not null;
create index source_document_artifact_version_idx
  on public.source_document_artifact(source_version_id, artifact_kind, artifact_status);

comment on table public.source_document_artifact is
'Inventory of acquired source documents. Git stores metadata/manifests, not licensed PDF bytes. storage_locator must never contain credentials.';

-- ===========================================================================
-- 4. Default status for every source version
-- ===========================================================================

create or replace function private.ensure_source_acquisition_status()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
  insert into public.source_acquisition_status(source_version_id)
  values (new.source_version_id)
  on conflict (source_version_id) do nothing;
  return new;
end;
$$;

revoke all on function private.ensure_source_acquisition_status()
from public, anon, authenticated;

create trigger ensure_source_acquisition_status
after insert on public.source_version
for each row execute function private.ensure_source_acquisition_status();

insert into public.source_acquisition_status(source_version_id)
select source_version_id from public.source_version
on conflict (source_version_id) do nothing;

-- ===========================================================================
-- 5. Workbench dashboard view
-- ===========================================================================

create or replace view public.v_source_acquisition_dashboard as
select
  sv.source_version_id,
  coalesce(rsv.release_record_id, csi.identity_value) as source_id,
  sv.title,
  sv.doi,
  sv.source_kind,
  sas.access_status,
  sas.access_route,
  sas.blocker_reason,
  sas.fulltext_available,
  sas.fulltext_verified,
  sas.supplement_status,
  sas.protocol_status,
  sas.registration_status,
  sas.needs_human_access,
  sas.last_checked_at,
  sas.next_retry_at,
  sas.verification_status,
  (select count(*) from public.source_acquisition_attempt saa where saa.source_version_id=sv.source_version_id) as acquisition_attempts,
  (select count(*) from public.source_document_artifact sda where sda.source_version_id=sv.source_version_id and sda.artifact_status in ('available','verified')) as available_artifacts
from public.source_version sv
left join public.release_source_version rsv
  on rsv.source_version_id=sv.source_version_id and rsv.release_id='2026-08-23'
left join public.canonical_source_identity csi
  on csi.canonical_source_id=sv.canonical_source_id
 and csi.identity_scheme='legacy_source_id'
join public.source_acquisition_status sas
  on sas.source_version_id=sv.source_version_id;

comment on view public.v_source_acquisition_dashboard is
'Internal Workbench acquisition dashboard. Operational access/licensing metadata is not projected automatically into CSI Gateway publications.';

-- ===========================================================================
-- 6. RLS / Workbench permissions
-- ===========================================================================

alter table public.source_acquisition_status enable row level security;
alter table public.source_acquisition_attempt enable row level security;
alter table public.source_document_artifact enable row level security;

revoke all on table public.source_acquisition_status from anon, authenticated;
revoke all on table public.source_acquisition_attempt from anon, authenticated;
revoke all on table public.source_document_artifact from anon, authenticated;
revoke all on public.v_source_acquisition_dashboard from anon, authenticated;

grant select, insert, update on table public.source_acquisition_status to authenticated, service_role;
grant select, insert on table public.source_acquisition_attempt to authenticated, service_role;
grant select, insert, update on table public.source_document_artifact to authenticated, service_role;
grant usage, select on sequence public.source_acquisition_attempt_acquisition_attempt_id_seq to authenticated, service_role;
grant usage, select on sequence public.source_document_artifact_source_document_artifact_id_seq to authenticated, service_role;
grant select on public.v_source_acquisition_dashboard to authenticated, service_role;

create policy source_acquisition_status_read
on public.source_acquisition_status for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy source_acquisition_status_insert
on public.source_acquisition_status for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy source_acquisition_status_update
on public.source_acquisition_status for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

create policy source_acquisition_attempt_read
on public.source_acquisition_attempt for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy source_acquisition_attempt_insert
on public.source_acquisition_attempt for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
-- Deliberately no authenticated UPDATE/DELETE policy: acquisition attempts are append-only.

create policy source_document_artifact_read
on public.source_document_artifact for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy source_document_artifact_insert
on public.source_document_artifact for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy source_document_artifact_update
on public.source_document_artifact for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));

-- Audit mutable operational state/artifact metadata. The attempt table itself is append-only.
create trigger audit_source_acquisition_status
after insert or update or delete on public.source_acquisition_status
for each row execute function private.audit_workbench_change();
create trigger audit_source_document_artifact
after insert or update or delete on public.source_document_artifact
for each row execute function private.audit_workbench_change();
