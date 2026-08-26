-- HRP Transfer Evidence Registry v1.1
-- Stage 2: separate canonical scientific source identity from reviewed source
-- versions and immutable evidence-release membership.
--
-- Backward compatibility:
--   * public.evidence_source remains in place.
--   * historical rt-2026-* source IDs remain unchanged.
--   * the 2026-08-23 release JSON remains unchanged.
--   * csi-evidence-v1 remains unchanged.

-- ===========================================================================
-- 1. Canonical scientific source
-- ===========================================================================

create table public.canonical_source (
  canonical_source_id text primary key,
  preferred_title text not null,
  source_status text not null default 'active'
    check (source_status in ('active','merged','retired')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.canonical_source is
'Persistent scientific publication/report identity. Independent of reviewed source version and evidence-release membership.';


-- ===========================================================================
-- 2. Canonical identifiers / aliases
-- ===========================================================================

create table public.canonical_source_identity (
  canonical_source_id text not null
    references public.canonical_source(canonical_source_id)
    on delete cascade,

  identity_scheme text not null
    check (
      identity_scheme in (
        'doi',
        'pmid',
        'arxiv',
        'canonical_url',
        'legacy_source_id'
      )
    ),

  identity_value text not null,
  normalized_value text not null,
  is_primary boolean not null default false,
  created_at timestamptz not null default now(),

  primary key (
    canonical_source_id,
    identity_scheme,
    normalized_value
  ),

  -- One external identity must never silently identify two canonical sources.
  unique (identity_scheme, normalized_value)
);

create unique index canonical_source_identity_primary_idx
  on public.canonical_source_identity(canonical_source_id)
  where is_primary is true;

create index canonical_source_identity_source_idx
  on public.canonical_source_identity(canonical_source_id);

comment on table public.canonical_source_identity is
'External identifiers and compatibility aliases for canonical scientific sources. DOI/PMID/arXiv/URL are identities, not primary keys.';


-- ===========================================================================
-- 3. Reviewed / extracted source version
-- ===========================================================================

create table public.source_version (
  source_version_id text primary key,

  canonical_source_id text not null
    references public.canonical_source(canonical_source_id)
    on delete restrict,

  version_number integer not null
    check (version_number > 0),

  version_status text not null
    check (
      version_status in (
        'candidate',
        'reviewed',
        'approved_seed',
        'approved_release',
        'superseded',
        'retired'
      )
    ),

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

  supersedes_source_version_id text
    references public.source_version(source_version_id)
    on delete restrict,

  created_at timestamptz not null default now(),
  approved_at timestamptz,

  unique (canonical_source_id, version_number)
);

create index source_version_canonical_source_idx
  on public.source_version(canonical_source_id);

create index source_version_status_idx
  on public.source_version(version_status);

create index source_version_doi_idx
  on public.source_version(doi)
  where doi is not null;

comment on table public.source_version is
'Versioned reviewed/extracted representation of a canonical source. Corrections to released evidence create a later version rather than rewriting the released version.';


-- ===========================================================================
-- 4. Evidence-release membership
-- ===========================================================================

create table public.release_source_version (
  release_id text not null
    references public.evidence_release(release_id)
    on delete restrict,

  source_version_id text not null
    references public.source_version(source_version_id)
    on delete restrict,

  release_record_id text not null,
  release_position integer,

  membership_status text not null
    check (
      membership_status in (
        'draft',
        'approved_seed',
        'approved_release',
        'retired'
      )
    ),

  added_at timestamptz not null default now(),

  primary key (release_id, source_version_id),
  unique (release_id, release_record_id)
);

create index release_source_version_version_idx
  on public.release_source_version(source_version_id);

comment on table public.release_source_version is
'Pins an evidence release to a specific reviewed source version while retaining the historical release-local source ID.';


-- ===========================================================================
-- 5. Identity normalisation helper
-- ===========================================================================

create or replace function private.normalize_source_identity(
  p_scheme text,
  p_value text
)
returns text
language plpgsql
immutable
security invoker
set search_path = public, pg_temp
as $$
declare
  v text;
begin
  if p_value is null or btrim(p_value) = '' then
    return null;
  end if;

  v := btrim(p_value);

  case p_scheme

    when 'doi' then
      v := lower(v);
      v := regexp_replace(
        v,
        '^(https?://(dx\.)?doi\.org/|doi:[[:space:]]*)',
        '',
        'i'
      );

    when 'pmid' then
      v := lower(v);
      v := regexp_replace(v, '^pmid:[[:space:]]*', '', 'i');

    when 'arxiv' then
      v := lower(v);
      v := regexp_replace(v, '^arxiv:[[:space:]]*', '', 'i');

    when 'canonical_url' then
      v := lower(v);
      v := regexp_replace(v, '/+$', '');

    when 'legacy_source_id' then
      v := lower(v);

    else
      raise exception 'Unsupported source identity scheme: %', p_scheme;

  end case;

  return v;
end;
$$;

revoke all on function private.normalize_source_identity(text,text)
from public, anon, authenticated;

grant execute on function private.normalize_source_identity(text,text)
to service_role;


-- ===========================================================================
-- 6. Deterministic compatibility sync from legacy evidence_source
--
-- Hosted database:
--   existing 18 evidence_source rows are backfilled below.
--
-- Fresh replay:
--   migration runs first; later bootstrap inserts evidence_source rows and
--   AFTER INSERT trigger creates the new identity/version layer.
--
-- IMPORTANT:
--   this function creates v1 if it does not exist.
--   It NEVER updates an existing source_version.
-- ===========================================================================

create or replace function private.sync_legacy_source_identity(
  p_source_id text
)
returns void
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  src record;

  v_canonical_source_id text;
  v_source_version_id text;

  v_release_position integer;

  v_primary_scheme text;

  v_norm_legacy text;
  v_norm_doi text;
  v_norm_pmid text;
  v_norm_arxiv text;
  v_norm_url text;
begin

  select
    es.*,
    er.status as release_status,
    er.released_on
  into src
  from public.evidence_source es
  join public.evidence_release er
    on er.release_id = es.release_id
  where es.source_id = p_source_id;

  if not found then
    return;
  end if;


  -- Deterministic compatibility IDs for the historical/source-snapshot layer.

  v_canonical_source_id := 'cs-' || src.source_id;
  v_source_version_id := 'sv-' || src.source_id || '-v1';


  -- Seed release ordering where source IDs terminate in a numeric sequence.
  if src.source_id ~ '[0-9]+$' then
    v_release_position :=
      substring(src.source_id from '([0-9]+)$')::integer;
  else
    v_release_position := null;
  end if;


  -- Normalise external identities.

  v_norm_legacy :=
    private.normalize_source_identity(
      'legacy_source_id',
      src.source_id
    );

  v_norm_doi :=
    private.normalize_source_identity(
      'doi',
      src.doi
    );

  v_norm_pmid :=
    private.normalize_source_identity(
      'pmid',
      src.pmid
    );

  v_norm_arxiv :=
    private.normalize_source_identity(
      'arxiv',
      src.arxiv_id
    );

  v_norm_url :=
    private.normalize_source_identity(
      'canonical_url',
      src.source_url
    );


  -- Preferred identity hierarchy.
  if v_norm_doi is not null then
    v_primary_scheme := 'doi';

  elsif v_norm_pmid is not null then
    v_primary_scheme := 'pmid';

  elsif v_norm_arxiv is not null then
    v_primary_scheme := 'arxiv';

  elsif v_norm_url is not null then
    v_primary_scheme := 'canonical_url';

  else
    v_primary_scheme := 'legacy_source_id';
  end if;


  -- -----------------------------------------------------------------------
  -- Canonical source
  -- -----------------------------------------------------------------------

  insert into public.canonical_source (
    canonical_source_id,
    preferred_title,
    source_status
  )
  values (
    v_canonical_source_id,
    src.title,
    'active'
  )
  on conflict (canonical_source_id)
  do nothing;


  -- -----------------------------------------------------------------------
  -- Identity aliases
  --
  -- Conflict handling deliberately targets the per-source primary key only.
  -- If the SAME DOI/PMID/etc. already belongs to ANOTHER canonical source,
  -- the global unique constraint raises an error rather than silently
  -- creating duplicate scientific identity.
  -- -----------------------------------------------------------------------

  insert into public.canonical_source_identity (
    canonical_source_id,
    identity_scheme,
    identity_value,
    normalized_value,
    is_primary
  )
  values (
    v_canonical_source_id,
    'legacy_source_id',
    src.source_id,
    v_norm_legacy,
    v_primary_scheme = 'legacy_source_id'
  )
  on conflict (
    canonical_source_id,
    identity_scheme,
    normalized_value
  )
  do nothing;


  if v_norm_doi is not null then

    insert into public.canonical_source_identity (
      canonical_source_id,
      identity_scheme,
      identity_value,
      normalized_value,
      is_primary
    )
    values (
      v_canonical_source_id,
      'doi',
      src.doi,
      v_norm_doi,
      v_primary_scheme = 'doi'
    )
    on conflict (
      canonical_source_id,
      identity_scheme,
      normalized_value
    )
    do nothing;

  end if;


  if v_norm_pmid is not null then

    insert into public.canonical_source_identity (
      canonical_source_id,
      identity_scheme,
      identity_value,
      normalized_value,
      is_primary
    )
    values (
      v_canonical_source_id,
      'pmid',
      src.pmid,
      v_norm_pmid,
      v_primary_scheme = 'pmid'
    )
    on conflict (
      canonical_source_id,
      identity_scheme,
      normalized_value
    )
    do nothing;

  end if;


  if v_norm_arxiv is not null then

    insert into public.canonical_source_identity (
      canonical_source_id,
      identity_scheme,
      identity_value,
      normalized_value,
      is_primary
    )
    values (
      v_canonical_source_id,
      'arxiv',
      src.arxiv_id,
      v_norm_arxiv,
      v_primary_scheme = 'arxiv'
    )
    on conflict (
      canonical_source_id,
      identity_scheme,
      normalized_value
    )
    do nothing;

  end if;


  if v_norm_url is not null then

    insert into public.canonical_source_identity (
      canonical_source_id,
      identity_scheme,
      identity_value,
      normalized_value,
      is_primary
    )
    values (
      v_canonical_source_id,
      'canonical_url',
      src.source_url,
      v_norm_url,
      v_primary_scheme = 'canonical_url'
    )
    on conflict (
      canonical_source_id,
      identity_scheme,
      normalized_value
    )
    do nothing;

  end if;


  -- -----------------------------------------------------------------------
  -- Reviewed source version v1
  --
  -- Critical immutability rule:
  -- existing versions are NOT updated by this compatibility sync.
  -- -----------------------------------------------------------------------

  insert into public.source_version (
    source_version_id,
    canonical_source_id,
    version_number,
    version_status,

    title,
    authors,
    publication_year,
    publication_date,
    venue,
    source_kind,
    peer_review_status,

    doi,
    pmid,
    arxiv_id,
    source_url,

    review_status,
    method_extraction_status,
    route_rationale,
    raw_record,

    supersedes_source_version_id,
    approved_at
  )
  values (
    v_source_version_id,
    v_canonical_source_id,
    1,

    case src.release_status
      when 'approved_seed' then 'approved_seed'
      when 'approved_release' then 'approved_release'
      else 'reviewed'
    end,

    src.title,
    src.authors,
    src.publication_year,
    src.publication_date,
    src.venue,
    src.source_kind,
    src.peer_review_status,

    src.doi,
    src.pmid,
    src.arxiv_id,
    src.source_url,

    src.review_status,
    src.method_extraction_status,
    src.route_rationale,
    src.raw_record,

    null,

    case
      when src.release_status in ('approved_seed','approved_release')
      then src.released_on::timestamptz
      else null
    end
  )
  on conflict (source_version_id)
  do nothing;


  -- -----------------------------------------------------------------------
  -- Release membership
  -- -----------------------------------------------------------------------

  insert into public.release_source_version (
    release_id,
    source_version_id,
    release_record_id,
    release_position,
    membership_status
  )
  values (
    src.release_id,
    v_source_version_id,
    src.source_id,
    v_release_position,

    case src.release_status
      when 'approved_seed' then 'approved_seed'
      when 'approved_release' then 'approved_release'
      when 'retired' then 'retired'
      else 'draft'
    end
  )
  on conflict (release_id, source_version_id)
  do nothing;

end;
$$;

revoke all on function private.sync_legacy_source_identity(text)
from public, anon, authenticated;

grant execute on function private.sync_legacy_source_identity(text)
to service_role;


-- ===========================================================================
-- 7. Insert-only compatibility trigger
--
-- Deliberately NOT an UPDATE trigger.
--
-- Existing legacy evidence_source upserts must not silently rewrite a source
-- version already pinned to an approved release.
-- ===========================================================================

create or replace function private.sync_legacy_source_identity_trigger()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
  perform private.sync_legacy_source_identity(new.source_id);
  return new;
end;
$$;

revoke all on function private.sync_legacy_source_identity_trigger()
from public, anon, authenticated;


drop trigger if exists sync_legacy_evidence_source_identity
on public.evidence_source;

create trigger sync_legacy_evidence_source_identity
after insert
on public.evidence_source
for each row
execute function private.sync_legacy_source_identity_trigger();


-- ===========================================================================
-- 8. Backfill any evidence_source rows already present when migration runs
-- ===========================================================================

do $$
declare
  r record;
begin
  for r in
    select source_id
    from public.evidence_source
    order by source_id
  loop
    perform private.sync_legacy_source_identity(r.source_id);
  end loop;
end;
$$;


-- ===========================================================================
-- 9. Released source-version immutability guard
-- ===========================================================================

create or replace function private.guard_released_source_version_mutation()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin

  if exists (
    select 1
    from public.release_source_version rsv
    join public.evidence_release er
      on er.release_id = rsv.release_id
    where rsv.source_version_id = old.source_version_id
      and er.status in ('approved_seed','approved_release')
  ) then

    raise exception
      'Source version % is pinned to an approved evidence release and is immutable; create a new source version instead.',
      old.source_version_id;

  end if;

  if tg_op = 'DELETE' then
    return old;
  end if;

  return new;
end;
$$;

revoke all on function private.guard_released_source_version_mutation()
from public, anon, authenticated;


drop trigger if exists guard_released_source_version_mutation
on public.source_version;

create trigger guard_released_source_version_mutation
before update or delete
on public.source_version
for each row
execute function private.guard_released_source_version_mutation();


-- ===========================================================================
-- 10. Approved release-membership immutability guard
-- ===========================================================================

create or replace function private.guard_approved_release_membership_mutation()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin

  if exists (
    select 1
    from public.evidence_release er
    where er.release_id = old.release_id
      and er.status in ('approved_seed','approved_release')
  ) then

    raise exception
      'Release membership for approved release % is immutable.',
      old.release_id;

  end if;

  if tg_op = 'DELETE' then
    return old;
  end if;

  return new;
end;
$$;

revoke all on function private.guard_approved_release_membership_mutation()
from public, anon, authenticated;


drop trigger if exists guard_approved_release_membership_mutation
on public.release_source_version;

create trigger guard_approved_release_membership_mutation
before update or delete
on public.release_source_version
for each row
execute function private.guard_approved_release_membership_mutation();


-- ===========================================================================
-- 11. RLS and grants
--
-- Stage 2 is intentionally read-only in the browser Workbench.
-- Candidate-version write workflows will be formalised later.
-- ===========================================================================

alter table public.canonical_source enable row level security;
alter table public.canonical_source_identity enable row level security;
alter table public.source_version enable row level security;
alter table public.release_source_version enable row level security;


revoke all on table public.canonical_source
from anon, authenticated;

revoke all on table public.canonical_source_identity
from anon, authenticated;

revoke all on table public.source_version
from anon, authenticated;

revoke all on table public.release_source_version
from anon, authenticated;


grant select on table public.canonical_source
to authenticated, service_role;

grant select on table public.canonical_source_identity
to authenticated, service_role;

grant select on table public.source_version
to authenticated, service_role;

grant select on table public.release_source_version
to authenticated, service_role;


grant insert, update, delete on table public.canonical_source
to service_role;

grant insert, update, delete on table public.canonical_source_identity
to service_role;

grant insert, update, delete on table public.source_version
to service_role;

grant insert, update, delete on table public.release_source_version
to service_role;


create policy canonical_source_workbench_read
on public.canonical_source
for select
to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);


create policy canonical_source_identity_workbench_read
on public.canonical_source_identity
for select
to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);


create policy source_version_workbench_read
on public.source_version
for select
to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);


create policy release_source_version_workbench_read
on public.release_source_version
for select
to authenticated
using (
  (select private.has_workbench_role(
    array['viewer','editor','owner']::text[]
  ))
);


-- ===========================================================================
-- 12. Audit coverage
-- ===========================================================================

drop trigger if exists audit_canonical_source
on public.canonical_source;

create trigger audit_canonical_source
after insert or update or delete
on public.canonical_source
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_canonical_source_identity
on public.canonical_source_identity;

create trigger audit_canonical_source_identity
after insert or update or delete
on public.canonical_source_identity
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_source_version
on public.source_version;

create trigger audit_source_version
after insert or update or delete
on public.source_version
for each row
execute function private.audit_workbench_change();


drop trigger if exists audit_release_source_version
on public.release_source_version;

create trigger audit_release_source_version
after insert or update or delete
on public.release_source_version
for each row
execute function private.audit_workbench_change();
