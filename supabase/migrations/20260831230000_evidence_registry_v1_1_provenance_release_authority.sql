-- HRP Transfer Evidence Registry v1.1
-- Stage 11: processing provenance, field adjudication/authority, and governed release builds.
--
-- Authority rules:
--   machine candidate != human adjudication != authoritative reviewed value
--   row audit != scientific provenance
--   release build != immutable evidence release
--   validation != approval != publication
--
-- Historical compatibility:
--   * release 2026-08-23 remains unchanged and reproducible.
--   * csi-evidence-v1 remains unchanged.
--   * local postgres bootstrap may reconstruct the historical seed only.

-- ===========================================================================
-- 1. Scientific processing-run identity
-- ===========================================================================

create table public.scientific_processing_run (
  processing_run_id bigserial primary key,
  run_kind text not null check (run_kind in (
    'discovery','screening','pre_extraction','classification','re_extraction',
    'validation','manual_import','release_export'
  )),
  actor_kind text not null check (actor_kind in ('agent','human','system','hybrid')),
  run_status text not null default 'started' check (run_status in ('started','completed','failed','cancelled')),
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  created_by uuid,
  provider text,
  tool_name text,
  tool_version text,
  model_name text,
  model_version text,
  prompt_version text,
  extraction_schema_version text,
  taxonomy_version text,
  code_commit_sha text,
  input_manifest_sha256 text check (input_manifest_sha256 is null or input_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  output_manifest_sha256 text check (output_manifest_sha256 is null or output_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  parameters_json jsonb not null default '{}'::jsonb,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check ((run_status='started' and completed_at is null) or run_status<>'started')
);

comment on table public.scientific_processing_run is
'Identity and tool/model/schema provenance for discovery, extraction, validation and export runs. A run never confers scientific approval.';

-- ===========================================================================
-- 2. Candidate field ledger
-- ===========================================================================

create table public.scientific_field_candidate (
  field_candidate_id bigserial primary key,
  processing_run_id bigint not null references public.scientific_processing_run(processing_run_id) on delete restrict,
  subject_kind text not null check (subject_kind in (
    'canonical_source','source_version','study','study_arm','intervention_component',
    'study_contrast','outcome','effect_estimate','quality_assessment','population_context',
    'proposition','synthesis_outcome','body_certainty','body_eml','harm_observation',
    'implementation_observation','support_dependence','boundary_condition','other_scientific_object'
  )),
  subject_key jsonb not null,
  field_path text not null check (btrim(field_path) <> ''),
  candidate_value_json jsonb not null,
  source_basis text not null check (btrim(source_basis) <> ''),
  confidence numeric check (confidence is null or (confidence >= 0 and confidence <= 1)),
  candidate_status text not null default 'proposed' check (candidate_status in ('proposed','accepted','rejected','superseded','withdrawn')),
  supersedes_candidate_id bigint references public.scientific_field_candidate(field_candidate_id) on delete restrict,
  created_at timestamptz not null default now()
);

create index scientific_field_candidate_run_idx on public.scientific_field_candidate(processing_run_id);
create index scientific_field_candidate_subject_idx on public.scientific_field_candidate(subject_kind, field_path);
create index scientific_field_candidate_status_idx on public.scientific_field_candidate(candidate_status);

comment on table public.scientific_field_candidate is
'Append-oriented machine/human proposal ledger. Candidate values are not authoritative scientific state until human adjudication establishes authority.';

-- ===========================================================================
-- 3. Human adjudication and durable field authority
-- ===========================================================================

create table public.scientific_field_adjudication (
  adjudication_id bigserial primary key,
  field_candidate_id bigint not null references public.scientific_field_candidate(field_candidate_id) on delete restrict,
  reviewer_user_id uuid not null,
  review_decision text not null check (review_decision in ('accept','reject','correct','defer')),
  reviewed_value_json jsonb,
  rationale text,
  is_final boolean not null default true,
  reviewed_at timestamptz not null default now(),
  check (review_decision <> 'correct' or reviewed_value_json is not null),
  check ((review_decision='defer' and is_final=false) or (review_decision<>'defer' and is_final=true))
);

create unique index scientific_field_adjudication_final_idx
  on public.scientific_field_adjudication(field_candidate_id)
  where is_final is true;

create index scientific_field_adjudication_candidate_idx on public.scientific_field_adjudication(field_candidate_id);

create table public.scientific_field_authority (
  authority_id bigserial primary key,
  subject_kind text not null,
  subject_key jsonb not null,
  field_path text not null,
  authoritative_value_json jsonb not null,
  source_adjudication_id bigint references public.scientific_field_adjudication(adjudication_id) on delete restrict,
  authority_kind text not null check (authority_kind in ('human_review','manual','approved_import','release_snapshot')),
  approved_by uuid,
  approved_at timestamptz not null default now(),
  superseded_by_authority_id bigint references public.scientific_field_authority(authority_id) on delete restrict,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create unique index scientific_field_authority_active_idx
  on public.scientific_field_authority(subject_kind, subject_key, field_path)
  where active is true;

create index scientific_field_authority_subject_idx
  on public.scientific_field_authority(subject_kind, field_path, active);

comment on table public.scientific_field_authority is
'Durable ledger of the reviewed value that currently governs a scientific field. Later machine candidates may challenge but cannot overwrite active human authority.';

-- ===========================================================================
-- 4. Release build / deterministic hash ledger
-- ===========================================================================

create table public.evidence_release_build (
  release_build_id text primary key,
  target_release_id text not null,
  build_status text not null default 'draft' check (build_status in (
    'draft','prepared','validated','approval_pending','approved','published','failed','cancelled'
  )),
  selection_policy text not null default 'latest_reviewed_per_canonical_source' check (
    selection_policy in ('latest_reviewed_per_canonical_source','explicit_source_versions')
  ),
  schema_version text not null,
  taxonomy_version text not null,
  gateway_contract_version text not null,
  source_review_document text not null,
  source_review_section text,
  requested_by uuid not null,
  requested_at timestamptz not null default now(),
  prepared_at timestamptz,
  validated_at timestamptz,
  prepared_revision bigint,
  validated_revision bigint,
  scientific_state_sha256 text check (scientific_state_sha256 is null or scientific_state_sha256 ~ '^[0-9a-f]{64}$'),
  export_manifest_sha256 text check (export_manifest_sha256 is null or export_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  export_manifest_json jsonb,
  validation_report_json jsonb,
  git_commit_sha text,
  approved_by uuid,
  approved_at timestamptz,
  published_at timestamptz,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index evidence_release_build_one_published_target_idx
  on public.evidence_release_build(target_release_id)
  where build_status='published';

create index evidence_release_build_status_idx on public.evidence_release_build(build_status);

create table public.release_build_source_version (
  release_build_id text not null references public.evidence_release_build(release_build_id) on delete cascade,
  source_version_id text not null references public.source_version(source_version_id) on delete restrict,
  release_record_id text not null,
  release_position integer not null check (release_position > 0),
  source_state_sha256 text check (source_state_sha256 is null or source_state_sha256 ~ '^[0-9a-f]{64}$'),
  added_at timestamptz not null default now(),
  primary key (release_build_id, source_version_id),
  unique (release_build_id, release_record_id),
  unique (release_build_id, release_position)
);

create index release_build_source_version_version_idx on public.release_build_source_version(source_version_id);

create table public.release_export_artifact (
  release_export_artifact_id bigserial primary key,
  release_build_id text not null references public.evidence_release_build(release_build_id) on delete cascade,
  artifact_kind text not null check (artifact_kind in ('scientific_state','manifest','export_bundle','validation_report')),
  artifact_sha256 text not null check (artifact_sha256 ~ '^[0-9a-f]{64}$'),
  byte_length bigint check (byte_length is null or byte_length >= 0),
  relative_path text,
  artifact_json jsonb,
  processing_run_id bigint references public.scientific_processing_run(processing_run_id) on delete restrict,
  created_at timestamptz not null default now(),
  unique (release_build_id, artifact_kind, artifact_sha256)
);

comment on table public.evidence_release_build is
'Governed pre-publication build object. Validation/approval/publication are explicit state transitions; editing evidence_release.status is not the release workflow.';

-- ===========================================================================
-- 5. Scientific-state revision clock
-- ===========================================================================

create table public.scientific_state_revision (
  singleton boolean primary key default true check (singleton),
  current_revision bigint not null default 0 check (current_revision >= 0),
  updated_at timestamptz not null default now()
);

insert into public.scientific_state_revision(singleton,current_revision)
values(true,0)
on conflict(singleton) do nothing;

create or replace function private.bump_scientific_state_revision()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  update public.scientific_state_revision
  set current_revision=current_revision+1, updated_at=now()
  where singleton=true;
  if tg_op='DELETE' then return old; end if;
  return new;
end;
$$;

revoke all on function private.bump_scientific_state_revision() from public, anon, authenticated;

-- ===========================================================================
-- 6. Controlled-write guards
-- ===========================================================================

create or replace function private.guard_stage11_candidate_mutation()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if tg_op='INSERT' then
    if new.candidate_status <> 'proposed' then
      raise exception 'Scientific field candidates must be inserted as proposed';
    end if;
    return new;
  end if;

  if current_setting('hrp.stage11_controlled_write', true) is distinct from 'on' then
    raise exception 'Scientific field candidate history is immutable outside controlled adjudication';
  end if;

  if tg_op='DELETE' then
    raise exception 'Scientific field candidate history cannot be deleted';
  end if;

  if new.processing_run_id is distinct from old.processing_run_id
     or new.subject_kind is distinct from old.subject_kind
     or new.subject_key is distinct from old.subject_key
     or new.field_path is distinct from old.field_path
     or new.candidate_value_json is distinct from old.candidate_value_json
     or new.source_basis is distinct from old.source_basis
     or new.confidence is distinct from old.confidence
     or new.supersedes_candidate_id is distinct from old.supersedes_candidate_id
     or new.created_at is distinct from old.created_at then
    raise exception 'Candidate payload/provenance is immutable; only controlled status transitions are allowed';
  end if;
  return new;
end;
$$;

revoke all on function private.guard_stage11_candidate_mutation() from public, anon, authenticated;
create trigger guard_stage11_candidate_mutation
before insert or update or delete on public.scientific_field_candidate
for each row execute function private.guard_stage11_candidate_mutation();

create or replace function private.guard_stage11_adjudication_mutation()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if current_setting('hrp.stage11_controlled_write', true) is distinct from 'on' then
    raise exception 'Scientific adjudications may only be created by controlled human review';
  end if;
  if tg_op <> 'INSERT' then
    raise exception 'Scientific adjudication history is append-only';
  end if;
  return new;
end;
$$;

revoke all on function private.guard_stage11_adjudication_mutation() from public, anon, authenticated;
create trigger guard_stage11_adjudication_mutation
before insert or update or delete on public.scientific_field_adjudication
for each row execute function private.guard_stage11_adjudication_mutation();

create or replace function private.guard_stage11_authority_mutation()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if current_setting('hrp.stage11_controlled_write', true) is distinct from 'on' then
    raise exception 'Scientific field authority may only change through controlled adjudication';
  end if;
  if tg_op='DELETE' then
    raise exception 'Scientific field authority history cannot be deleted';
  end if;
  if tg_op='UPDATE' and (
    new.subject_kind is distinct from old.subject_kind
    or new.subject_key is distinct from old.subject_key
    or new.field_path is distinct from old.field_path
    or new.authoritative_value_json is distinct from old.authoritative_value_json
    or new.source_adjudication_id is distinct from old.source_adjudication_id
    or new.authority_kind is distinct from old.authority_kind
    or new.approved_by is distinct from old.approved_by
    or new.approved_at is distinct from old.approved_at
    or new.created_at is distinct from old.created_at
  ) then
    raise exception 'Authority payload is immutable; supersession must create a later authority record';
  end if;
  return new;
end;
$$;

revoke all on function private.guard_stage11_authority_mutation() from public, anon, authenticated;
create trigger guard_stage11_authority_mutation
before insert or update or delete on public.scientific_field_authority
for each row execute function private.guard_stage11_authority_mutation();

create or replace function private.guard_stage11_release_build_mutation()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  allowed boolean := false;
begin
  if current_setting('hrp.stage11_controlled_write', true) is distinct from 'on' then
    raise exception 'Release builds may only change through controlled Stage 11 operations';
  end if;

  if tg_op='INSERT' then
    if new.build_status <> 'draft' then raise exception 'New release builds must begin in draft state'; end if;
    return new;
  elsif tg_op='DELETE' then
    if old.build_status not in ('draft','failed','cancelled') then
      raise exception 'Prepared/validated/approved/published release-build history cannot be deleted';
    end if;
    return old;
  end if;

  if new.build_status=old.build_status then
    allowed := true;
  elsif old.build_status='draft' and new.build_status in ('prepared','cancelled','failed') then
    allowed := true;
  elsif old.build_status='prepared' and new.build_status in ('validated','failed','cancelled') then
    allowed := true;
  elsif old.build_status='validated' and new.build_status in ('approval_pending','approved','failed','cancelled') then
    allowed := true;
  elsif old.build_status='approval_pending' and new.build_status in ('approved','failed','cancelled') then
    allowed := true;
  elsif old.build_status='approved' and new.build_status='published' then
    allowed := true;
  end if;

  if not allowed then
    raise exception 'Invalid release-build transition % -> %', old.build_status, new.build_status;
  end if;
  return new;
end;
$$;

revoke all on function private.guard_stage11_release_build_mutation() from public, anon, authenticated;
create trigger guard_stage11_release_build_mutation
before insert or update or delete on public.evidence_release_build
for each row execute function private.guard_stage11_release_build_mutation();

create or replace function private.guard_stage11_release_membership_mutation()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if current_setting('hrp.stage11_controlled_write', true) is distinct from 'on' then
    raise exception 'Release-build membership may only change through controlled Stage 11 operations';
  end if;
  return case when tg_op='DELETE' then old else new end;
end;
$$;

revoke all on function private.guard_stage11_release_membership_mutation() from public, anon, authenticated;
create trigger guard_stage11_release_membership_mutation
before insert or update or delete on public.release_build_source_version
for each row execute function private.guard_stage11_release_membership_mutation();
create trigger guard_stage11_release_artifact_mutation
before insert or update or delete on public.release_export_artifact
for each row execute function private.guard_stage11_release_membership_mutation();

-- Govern evidence_release itself. The only compatibility exception is local postgres
-- reconstruction of the immutable historical seed release.
create or replace function private.guard_stage11_evidence_release_mutation()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_release_id text := case when tg_op='DELETE' then old.release_id else new.release_id end;
begin
  if v_release_id='2026-08-23' and current_user='postgres' then
    return case when tg_op='DELETE' then old else new end;
  end if;

  if current_setting('hrp.stage11_release_write', true) is distinct from 'on' then
    raise exception 'Evidence releases may only be published through the governed release-build authority path';
  end if;

  if tg_op in ('UPDATE','DELETE') and old.status in ('approved_seed','approved_release') then
    raise exception 'Approved evidence release % is immutable', old.release_id;
  end if;
  return case when tg_op='DELETE' then old else new end;
end;
$$;

revoke all on function private.guard_stage11_evidence_release_mutation() from public, anon, authenticated;
drop trigger if exists guard_stage11_evidence_release_mutation on public.evidence_release;
create trigger guard_stage11_evidence_release_mutation
before insert or update or delete on public.evidence_release
for each row execute function private.guard_stage11_evidence_release_mutation();

create or replace function private.guard_stage11_release_source_version_insert()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if new.release_id='2026-08-23' and current_user='postgres' then return new; end if;
  if current_setting('hrp.stage11_release_write', true) is distinct from 'on' then
    raise exception 'Release source-version membership may only be created through governed publication';
  end if;
  return new;
end;
$$;

revoke all on function private.guard_stage11_release_source_version_insert() from public, anon, authenticated;
drop trigger if exists guard_stage11_release_source_version_insert on public.release_source_version;
create trigger guard_stage11_release_source_version_insert
before insert on public.release_source_version
for each row execute function private.guard_stage11_release_source_version_insert();

-- ===========================================================================
-- 7. Core adjudication logic and human wrapper
-- ===========================================================================

create or replace function private.apply_scientific_adjudication_core(
  p_field_candidate_id bigint,
  p_reviewer_user_id uuid,
  p_review_decision text,
  p_reviewed_value_json jsonb default null,
  p_rationale text default null
)
returns bigint
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  c public.scientific_field_candidate%rowtype;
  v_adjudication_id bigint;
  v_value jsonb;
  v_old_authority_id bigint;
  v_new_authority_id bigint;
begin
  if p_review_decision not in ('accept','reject','correct','defer') then
    raise exception 'Unsupported review decision %', p_review_decision;
  end if;
  if p_review_decision='correct' and p_reviewed_value_json is null then
    raise exception 'Correct decision requires reviewed_value_json';
  end if;

  select * into c
  from public.scientific_field_candidate
  where field_candidate_id=p_field_candidate_id
  for update;
  if not found then raise exception 'Candidate % not found', p_field_candidate_id; end if;
  if c.candidate_status <> 'proposed' then
    raise exception 'Candidate % is %, not proposed', p_field_candidate_id, c.candidate_status;
  end if;

  perform set_config('hrp.stage11_controlled_write','on',true);

  insert into public.scientific_field_adjudication(
    field_candidate_id,reviewer_user_id,review_decision,reviewed_value_json,rationale,is_final
  ) values (
    p_field_candidate_id,p_reviewer_user_id,p_review_decision,p_reviewed_value_json,p_rationale,p_review_decision<>'defer'
  ) returning adjudication_id into v_adjudication_id;

  if p_review_decision='defer' then
    return v_adjudication_id;
  elsif p_review_decision='reject' then
    update public.scientific_field_candidate
    set candidate_status='rejected'
    where field_candidate_id=p_field_candidate_id;
    return v_adjudication_id;
  end if;

  v_value := case when p_review_decision='correct' then p_reviewed_value_json else c.candidate_value_json end;

  select authority_id into v_old_authority_id
  from public.scientific_field_authority
  where subject_kind=c.subject_kind and subject_key=c.subject_key and field_path=c.field_path and active=true
  for update;

  if v_old_authority_id is not null then
    update public.scientific_field_authority
    set active=false
    where authority_id=v_old_authority_id;
  end if;

  insert into public.scientific_field_authority(
    subject_kind,subject_key,field_path,authoritative_value_json,source_adjudication_id,
    authority_kind,approved_by,approved_at,active
  ) values (
    c.subject_kind,c.subject_key,c.field_path,v_value,v_adjudication_id,
    'human_review',p_reviewer_user_id,now(),true
  ) returning authority_id into v_new_authority_id;

  if v_old_authority_id is not null then
    update public.scientific_field_authority
    set superseded_by_authority_id=v_new_authority_id
    where authority_id=v_old_authority_id;
  end if;

  update public.scientific_field_candidate
  set candidate_status='accepted'
  where field_candidate_id=p_field_candidate_id;

  return v_adjudication_id;
end;
$$;

revoke all on function private.apply_scientific_adjudication_core(bigint,uuid,text,jsonb,text)
from public, anon, authenticated, service_role;

create or replace function public.adjudicate_scientific_field_candidate(
  p_field_candidate_id bigint,
  p_review_decision text,
  p_reviewed_value_json jsonb default null,
  p_rationale text default null
)
returns bigint
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_user uuid := auth.uid();
begin
  if v_user is null or not private.has_workbench_role(array['editor','owner']::text[]) then
    raise exception 'Editor or owner human authority required';
  end if;
  return private.apply_scientific_adjudication_core(
    p_field_candidate_id,v_user,p_review_decision,p_reviewed_value_json,p_rationale
  );
end;
$$;

revoke all on function public.adjudicate_scientific_field_candidate(bigint,text,jsonb,text) from public, anon, service_role;
grant execute on function public.adjudicate_scientific_field_candidate(bigint,text,jsonb,text) to authenticated;

-- ===========================================================================
-- 8. Release-build core operations
-- ===========================================================================

create or replace function private.stage11_create_release_build_core(
  p_release_build_id text,
  p_target_release_id text,
  p_schema_version text,
  p_taxonomy_version text,
  p_gateway_contract_version text,
  p_source_review_document text,
  p_source_review_section text,
  p_requested_by uuid,
  p_notes text default null
)
returns text
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if exists(select 1 from public.evidence_release where release_id=p_target_release_id) then
    raise exception 'Target evidence release % already exists', p_target_release_id;
  end if;
  perform set_config('hrp.stage11_controlled_write','on',true);
  insert into public.evidence_release_build(
    release_build_id,target_release_id,build_status,schema_version,taxonomy_version,gateway_contract_version,
    source_review_document,source_review_section,requested_by,notes
  ) values (
    p_release_build_id,p_target_release_id,'draft',p_schema_version,p_taxonomy_version,p_gateway_contract_version,
    p_source_review_document,p_source_review_section,p_requested_by,p_notes
  );
  return p_release_build_id;
end;
$$;

revoke all on function private.stage11_create_release_build_core(text,text,text,text,text,text,text,uuid,text)
from public, anon, authenticated, service_role;

create or replace function public.create_evidence_release_build(
  p_release_build_id text,
  p_target_release_id text,
  p_schema_version text,
  p_taxonomy_version text,
  p_gateway_contract_version text,
  p_source_review_document text,
  p_source_review_section text default null,
  p_notes text default null
)
returns text
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_user uuid := auth.uid();
begin
  if v_user is null or not private.has_workbench_role(array['owner']::text[]) then
    raise exception 'Owner authority required to create a release build';
  end if;
  return private.stage11_create_release_build_core(
    p_release_build_id,p_target_release_id,p_schema_version,p_taxonomy_version,p_gateway_contract_version,
    p_source_review_document,p_source_review_section,v_user,p_notes
  );
end;
$$;

revoke all on function public.create_evidence_release_build(text,text,text,text,text,text,text,text) from public, anon, service_role;
grant execute on function public.create_evidence_release_build(text,text,text,text,text,text,text,text) to authenticated;

create or replace function private.stage11_prepare_release_build_core(p_release_build_id text)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  b public.evidence_release_build%rowtype;
  v_revision bigint;
  v_count integer;
begin
  select * into b from public.evidence_release_build where release_build_id=p_release_build_id for update;
  if not found then raise exception 'Release build % not found', p_release_build_id; end if;
  if b.build_status <> 'draft' then raise exception 'Release build % must be draft to prepare', p_release_build_id; end if;

  select current_revision into v_revision from public.scientific_state_revision where singleton=true;
  perform set_config('hrp.stage11_controlled_write','on',true);

  delete from public.release_build_source_version where release_build_id=p_release_build_id;

  with ranked as (
    select sv.*,
           row_number() over(partition by sv.canonical_source_id order by sv.version_number desc,sv.source_version_id desc) as rn
    from public.source_version sv
    where sv.version_status in ('reviewed','approved_seed','approved_release')
  ), selected as (
    select * from ranked where rn=1
  ), identified as (
    select s.*,
           coalesce(
             (select csi.identity_value from public.canonical_source_identity csi
              where csi.canonical_source_id=s.canonical_source_id and csi.identity_scheme='legacy_source_id'
              order by csi.identity_value limit 1),
             s.source_version_id
           ) as release_record_id
    from selected s
  )
  insert into public.release_build_source_version(
    release_build_id,source_version_id,release_record_id,release_position
  )
  select p_release_build_id,source_version_id,release_record_id,
         row_number() over(order by canonical_source_id,version_number,source_version_id)::integer
  from identified
  order by canonical_source_id,version_number,source_version_id;

  get diagnostics v_count=row_count;
  if v_count=0 then raise exception 'Release build % has no reviewed/approved source versions', p_release_build_id; end if;

  update public.evidence_release_build
  set build_status='prepared',prepared_at=now(),prepared_revision=v_revision,
      scientific_state_sha256=null,export_manifest_sha256=null,export_manifest_json=null,
      validation_report_json=null,validated_revision=null,validated_at=null,updated_at=now()
  where release_build_id=p_release_build_id;
end;
$$;

revoke all on function private.stage11_prepare_release_build_core(text) from public, anon, authenticated, service_role;

create or replace function public.prepare_evidence_release_build(p_release_build_id text)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if auth.uid() is null or not private.has_workbench_role(array['owner']::text[]) then
    raise exception 'Owner authority required to prepare a release build';
  end if;
  perform private.stage11_prepare_release_build_core(p_release_build_id);
end;
$$;

revoke all on function public.prepare_evidence_release_build(text) from public, anon, service_role;
grant execute on function public.prepare_evidence_release_build(text) to authenticated;

create or replace function private.stage11_record_release_validation_core(
  p_release_build_id text,
  p_scientific_state_sha256 text,
  p_export_manifest_sha256 text,
  p_export_manifest_json jsonb,
  p_validation_report_json jsonb,
  p_git_commit_sha text default null,
  p_processing_run_id bigint default null
)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  b public.evidence_release_build%rowtype;
  v_revision bigint;
  v_manifest_count integer;
  v_member_count integer;
  item jsonb;
begin
  if p_scientific_state_sha256 !~ '^[0-9a-f]{64}$' or p_export_manifest_sha256 !~ '^[0-9a-f]{64}$' then
    raise exception 'Validation requires canonical lowercase SHA-256 hashes';
  end if;
  if jsonb_typeof(p_export_manifest_json->'sources') <> 'array' then
    raise exception 'Export manifest must contain a sources array';
  end if;

  select * into b from public.evidence_release_build where release_build_id=p_release_build_id for update;
  if not found then raise exception 'Release build % not found', p_release_build_id; end if;
  if b.build_status <> 'prepared' then raise exception 'Release build % must be prepared before validation', p_release_build_id; end if;

  select current_revision into v_revision from public.scientific_state_revision where singleton=true;
  if b.prepared_revision is distinct from v_revision then
    raise exception 'Scientific state drifted since build preparation (% -> %)', b.prepared_revision, v_revision;
  end if;

  select count(*) into v_member_count from public.release_build_source_version where release_build_id=p_release_build_id;
  select jsonb_array_length(p_export_manifest_json->'sources') into v_manifest_count;
  if v_member_count <> v_manifest_count then
    raise exception 'Manifest source count % does not match build membership %', v_manifest_count, v_member_count;
  end if;

  perform set_config('hrp.stage11_controlled_write','on',true);

  for item in select value from jsonb_array_elements(p_export_manifest_json->'sources')
  loop
    if coalesce(item->>'source_state_sha256','') !~ '^[0-9a-f]{64}$' then
      raise exception 'Manifest source % has invalid source_state_sha256', item->>'source_version_id';
    end if;
    update public.release_build_source_version
    set source_state_sha256=item->>'source_state_sha256'
    where release_build_id=p_release_build_id
      and source_version_id=item->>'source_version_id';
    if not found then
      raise exception 'Manifest source_version_id % is not pinned to build %', item->>'source_version_id', p_release_build_id;
    end if;
  end loop;

  if exists(select 1 from public.release_build_source_version where release_build_id=p_release_build_id and source_state_sha256 is null) then
    raise exception 'Every pinned source version requires a deterministic source-state hash';
  end if;

  update public.evidence_release_build
  set build_status='validated',validated_at=now(),validated_revision=v_revision,
      scientific_state_sha256=p_scientific_state_sha256,
      export_manifest_sha256=p_export_manifest_sha256,
      export_manifest_json=p_export_manifest_json,
      validation_report_json=p_validation_report_json,
      git_commit_sha=p_git_commit_sha,
      updated_at=now()
  where release_build_id=p_release_build_id;

  insert into public.release_export_artifact(
    release_build_id,artifact_kind,artifact_sha256,byte_length,artifact_json,processing_run_id
  ) values (
    p_release_build_id,'manifest',p_export_manifest_sha256,
    octet_length(convert_to(p_export_manifest_json::text,'UTF8')),
    p_export_manifest_json,p_processing_run_id
  ) on conflict (release_build_id,artifact_kind,artifact_sha256) do nothing;
end;
$$;

revoke all on function private.stage11_record_release_validation_core(text,text,text,jsonb,jsonb,text,bigint)
from public, anon, authenticated, service_role;

create or replace function public.record_evidence_release_build_validation(
  p_release_build_id text,
  p_scientific_state_sha256 text,
  p_export_manifest_sha256 text,
  p_export_manifest_json jsonb,
  p_validation_report_json jsonb,
  p_git_commit_sha text default null,
  p_processing_run_id bigint default null
)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if coalesce(auth.role(),'') <> 'service_role'
     and (auth.uid() is null or not private.has_workbench_role(array['owner']::text[])) then
    raise exception 'Owner or service validation authority required';
  end if;
  perform private.stage11_record_release_validation_core(
    p_release_build_id,p_scientific_state_sha256,p_export_manifest_sha256,p_export_manifest_json,
    p_validation_report_json,p_git_commit_sha,p_processing_run_id
  );
end;
$$;

revoke all on function public.record_evidence_release_build_validation(text,text,text,jsonb,jsonb,text,bigint) from public, anon;
grant execute on function public.record_evidence_release_build_validation(text,text,text,jsonb,jsonb,text,bigint) to authenticated, service_role;

create or replace function private.assert_stage11_build_current(p_release_build_id text)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  b public.evidence_release_build%rowtype;
  v_revision bigint;
begin
  select * into b from public.evidence_release_build where release_build_id=p_release_build_id;
  if not found then raise exception 'Release build % not found', p_release_build_id; end if;
  select current_revision into v_revision from public.scientific_state_revision where singleton=true;
  if b.validated_revision is null or b.validated_revision is distinct from v_revision then
    raise exception 'Scientific state drift: build validated at revision %, current revision %', b.validated_revision, v_revision;
  end if;
end;
$$;

revoke all on function private.assert_stage11_build_current(text) from public, anon, authenticated, service_role;

create or replace function private.stage11_approve_release_build_core(p_release_build_id text,p_approved_by uuid)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare b public.evidence_release_build%rowtype;
begin
  select * into b from public.evidence_release_build where release_build_id=p_release_build_id for update;
  if not found then raise exception 'Release build % not found', p_release_build_id; end if;
  if b.build_status <> 'validated' then raise exception 'Release build % must be validated before approval', p_release_build_id; end if;
  if b.scientific_state_sha256 is null or b.export_manifest_sha256 is null or b.export_manifest_json is null then
    raise exception 'Validated build lacks deterministic export hashes/manifest';
  end if;
  perform private.assert_stage11_build_current(p_release_build_id);
  perform set_config('hrp.stage11_controlled_write','on',true);
  update public.evidence_release_build
  set build_status='approved',approved_by=p_approved_by,approved_at=now(),updated_at=now()
  where release_build_id=p_release_build_id;
end;
$$;

revoke all on function private.stage11_approve_release_build_core(text,uuid) from public, anon, authenticated, service_role;

create or replace function public.approve_evidence_release_build(p_release_build_id text)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare v_user uuid := auth.uid();
begin
  if v_user is null or not private.has_workbench_role(array['owner']::text[]) then
    raise exception 'Human owner authority required to approve a release build';
  end if;
  perform private.stage11_approve_release_build_core(p_release_build_id,v_user);
end;
$$;

revoke all on function public.approve_evidence_release_build(text) from public, anon, service_role;
grant execute on function public.approve_evidence_release_build(text) to authenticated;

create or replace function private.stage11_publish_release_build_core(p_release_build_id text,p_published_by uuid)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare b public.evidence_release_build%rowtype;
begin
  select * into b from public.evidence_release_build where release_build_id=p_release_build_id for update;
  if not found then raise exception 'Release build % not found', p_release_build_id; end if;
  if b.build_status <> 'approved' then raise exception 'Release build % must be approved before publication', p_release_build_id; end if;
  perform private.assert_stage11_build_current(p_release_build_id);
  if exists(select 1 from public.evidence_release where release_id=b.target_release_id) then
    raise exception 'Target evidence release % already exists', b.target_release_id;
  end if;
  if exists(
    select 1 from public.release_build_source_version rb
    join public.source_version sv on sv.source_version_id=rb.source_version_id
    where rb.release_build_id=p_release_build_id
      and sv.version_status not in ('reviewed','approved_seed','approved_release')
  ) then
    raise exception 'Release build contains an unreviewed source version';
  end if;
  if exists(select 1 from public.release_build_source_version where release_build_id=p_release_build_id and source_state_sha256 is null) then
    raise exception 'Release build contains unhashed source-version state';
  end if;

  perform set_config('hrp.stage11_controlled_write','on',true);
  perform set_config('hrp.stage11_release_write','on',true);

  insert into public.evidence_release(
    release_id,released_on,schema_version,taxonomy_version,source_review_document,source_review_section,status,notes
  ) values (
    b.target_release_id,current_date,b.schema_version,b.taxonomy_version,b.source_review_document,b.source_review_section,
    'approved_release',coalesce(b.notes,'Published from governed Evidence Registry v1.1 release build '||b.release_build_id)
  );

  insert into public.release_source_version(
    release_id,source_version_id,release_record_id,release_position,membership_status
  )
  select b.target_release_id,source_version_id,release_record_id,release_position,'approved_release'
  from public.release_build_source_version
  where release_build_id=p_release_build_id
  order by release_position;

  update public.evidence_release_build
  set build_status='published',published_at=now(),updated_at=now()
  where release_build_id=p_release_build_id;
end;
$$;

revoke all on function private.stage11_publish_release_build_core(text,uuid) from public, anon, authenticated, service_role;

create or replace function public.publish_evidence_release_build(p_release_build_id text)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare v_user uuid := auth.uid();
begin
  if v_user is null or not private.has_workbench_role(array['owner']::text[]) then
    raise exception 'Human owner authority required to publish a release build';
  end if;
  perform private.stage11_publish_release_build_core(p_release_build_id,v_user);
end;
$$;

revoke all on function public.publish_evidence_release_build(text) from public, anon, service_role;
grant execute on function public.publish_evidence_release_build(text) to authenticated;

-- ===========================================================================
-- 9. Browser/service direct release-write boundary
-- ===========================================================================

drop policy if exists evidence_release_workbench_insert on public.evidence_release;
drop policy if exists evidence_release_workbench_update on public.evidence_release;
drop policy if exists evidence_release_workbench_delete on public.evidence_release;

revoke insert,update,delete on table public.evidence_release from authenticated, service_role;
grant select on table public.evidence_release to authenticated, service_role;

-- New release_source_version membership is controlled by publish operation.
revoke insert,update,delete on table public.release_source_version from authenticated, service_role;
grant select on table public.release_source_version to authenticated, service_role;

-- ===========================================================================
-- 10. RLS / grants for Stage 11 objects
-- ===========================================================================

alter table public.scientific_processing_run enable row level security;
alter table public.scientific_field_candidate enable row level security;
alter table public.scientific_field_adjudication enable row level security;
alter table public.scientific_field_authority enable row level security;
alter table public.evidence_release_build enable row level security;
alter table public.release_build_source_version enable row level security;
alter table public.release_export_artifact enable row level security;
alter table public.scientific_state_revision enable row level security;

revoke all on table public.scientific_processing_run from anon, authenticated;
revoke all on table public.scientific_field_candidate from anon, authenticated;
revoke all on table public.scientific_field_adjudication from anon, authenticated;
revoke all on table public.scientific_field_authority from anon, authenticated;
revoke all on table public.evidence_release_build from anon, authenticated;
revoke all on table public.release_build_source_version from anon, authenticated;
revoke all on table public.release_export_artifact from anon, authenticated;
revoke all on table public.scientific_state_revision from anon, authenticated;

-- Reviewers may read provenance/build state.
grant select on table public.scientific_processing_run,public.scientific_field_candidate,
  public.scientific_field_adjudication,public.scientific_field_authority,
  public.evidence_release_build,public.release_build_source_version,public.release_export_artifact,
  public.scientific_state_revision to authenticated, service_role;

-- Machines may create/update run metadata and create proposed candidates only.
grant insert,update on table public.scientific_processing_run to authenticated, service_role;
grant insert on table public.scientific_field_candidate to authenticated, service_role;

grant usage,select on sequence public.scientific_processing_run_processing_run_id_seq to authenticated,service_role;
grant usage,select on sequence public.scientific_field_candidate_field_candidate_id_seq to authenticated,service_role;
grant usage,select on sequence public.scientific_field_adjudication_adjudication_id_seq to authenticated,service_role;
grant usage,select on sequence public.scientific_field_authority_authority_id_seq to authenticated,service_role;
grant usage,select on sequence public.release_export_artifact_release_export_artifact_id_seq to authenticated,service_role;

create policy scientific_processing_run_read on public.scientific_processing_run for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy scientific_field_candidate_read on public.scientific_field_candidate for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy scientific_field_adjudication_read on public.scientific_field_adjudication for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy scientific_field_authority_read on public.scientific_field_authority for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy evidence_release_build_read on public.evidence_release_build for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy release_build_source_version_read on public.release_build_source_version for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy release_export_artifact_read on public.release_export_artifact for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy scientific_state_revision_read on public.scientific_state_revision for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy scientific_processing_run_insert on public.scientific_processing_run for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy scientific_processing_run_update on public.scientific_processing_run for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy scientific_field_candidate_insert on public.scientific_field_candidate for insert to authenticated
with check (
  candidate_status='proposed'
  and (select private.has_workbench_role(array['editor','owner']::text[]))
);

-- ===========================================================================
-- 11. Audit coverage for Stage 11 ledgers
-- ===========================================================================

create trigger audit_scientific_processing_run after insert or update or delete on public.scientific_processing_run
for each row execute function private.audit_workbench_change();
create trigger audit_scientific_field_candidate after insert or update or delete on public.scientific_field_candidate
for each row execute function private.audit_workbench_change();
create trigger audit_scientific_field_adjudication after insert or update or delete on public.scientific_field_adjudication
for each row execute function private.audit_workbench_change();
create trigger audit_scientific_field_authority after insert or update or delete on public.scientific_field_authority
for each row execute function private.audit_workbench_change();
create trigger audit_evidence_release_build after insert or update or delete on public.evidence_release_build
for each row execute function private.audit_workbench_change();
create trigger audit_release_build_source_version after insert or update or delete on public.release_build_source_version
for each row execute function private.audit_workbench_change();
create trigger audit_release_export_artifact after insert or update or delete on public.release_export_artifact
for each row execute function private.audit_workbench_change();

-- ===========================================================================
-- 12. Scientific revision triggers on audited scientific-state tables
--
-- Release/provenance/governance objects are deliberately excluded. Candidate and
-- adjudication activity does not change scientific state until authority changes.
-- ===========================================================================

do $$
declare
  t text;
begin
  for t in
    select distinct c.relname
    from pg_trigger tr
    join pg_class c on c.oid=tr.tgrelid
    join pg_namespace n on n.oid=c.relnamespace
    where n.nspname='public'
      and not tr.tgisinternal
      and tr.tgname like 'audit_%'
      and c.relkind='r'
      and c.relname not in (
        'workbench_member','evidence_release','release_source_version','workbench_audit_log',
        'scientific_processing_run','scientific_field_candidate','scientific_field_adjudication',
        'evidence_release_build','release_build_source_version','release_export_artifact',
        'scientific_state_revision'
      )
  loop
    execute format('drop trigger if exists stage11_state_revision on public.%I',t);
    execute format(
      'create trigger stage11_state_revision after insert or update or delete on public.%I for each row execute function private.bump_scientific_state_revision()',
      t
    );
  end loop;
end $$;

comment on table public.scientific_state_revision is
'Conservative mutation clock used to invalidate release-build validation when reviewed scientific state changes. Release/provenance/build metadata itself does not advance this clock.';
