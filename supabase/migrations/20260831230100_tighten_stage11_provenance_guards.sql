-- HRP Transfer Evidence Registry v1.1
-- Stage 11 guard tightening.

-- Processing-run identity/provenance is immutable after creation. A run may only
-- advance status/completion/output metadata; it may not be rewritten to claim a
-- different model, prompt, taxonomy, input manifest or code version.
create or replace function private.guard_stage11_processing_run_mutation()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if tg_op='DELETE' then
    raise exception 'Scientific processing-run history cannot be deleted';
  end if;
  if tg_op='INSERT' then
    return new;
  end if;

  if new.run_kind is distinct from old.run_kind
     or new.actor_kind is distinct from old.actor_kind
     or new.started_at is distinct from old.started_at
     or new.created_by is distinct from old.created_by
     or new.provider is distinct from old.provider
     or new.tool_name is distinct from old.tool_name
     or new.tool_version is distinct from old.tool_version
     or new.model_name is distinct from old.model_name
     or new.model_version is distinct from old.model_version
     or new.prompt_version is distinct from old.prompt_version
     or new.extraction_schema_version is distinct from old.extraction_schema_version
     or new.taxonomy_version is distinct from old.taxonomy_version
     or new.code_commit_sha is distinct from old.code_commit_sha
     or new.input_manifest_sha256 is distinct from old.input_manifest_sha256
     or new.parameters_json is distinct from old.parameters_json
     or new.created_at is distinct from old.created_at then
    raise exception 'Processing-run identity/provenance is immutable; create a new run instead';
  end if;

  if old.run_status in ('completed','failed','cancelled')
     and (new.run_status is distinct from old.run_status
          or new.completed_at is distinct from old.completed_at
          or new.output_manifest_sha256 is distinct from old.output_manifest_sha256) then
    raise exception 'Completed/failed/cancelled processing runs are terminal';
  end if;

  if new.run_status='started' and new.completed_at is not null then
    raise exception 'Started processing run cannot have completed_at';
  end if;
  if new.run_status<>'started' and new.completed_at is null then
    raise exception 'Terminal processing-run status requires completed_at';
  end if;

  new.updated_at := now();
  return new;
end;
$$;

revoke all on function private.guard_stage11_processing_run_mutation() from public, anon, authenticated;
drop trigger if exists guard_stage11_processing_run_mutation on public.scientific_processing_run;
create trigger guard_stage11_processing_run_mutation
before insert or update or delete on public.scientific_processing_run
for each row execute function private.guard_stage11_processing_run_mutation();

-- Explicit record returns avoid polymorphic CASE ambiguity in trigger functions.
create or replace function private.guard_stage11_release_membership_mutation()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if current_setting('hrp.stage11_controlled_write', true) is distinct from 'on' then
    raise exception 'Release-build membership/artifacts may only change through controlled Stage 11 operations';
  end if;
  if tg_op='DELETE' then
    return old;
  end if;
  return new;
end;
$$;

revoke all on function private.guard_stage11_release_membership_mutation() from public, anon, authenticated;

create or replace function private.guard_stage11_evidence_release_mutation()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_release_id text;
begin
  if tg_op='DELETE' then v_release_id := old.release_id; else v_release_id := new.release_id; end if;

  if v_release_id='2026-08-23' and current_user='postgres' then
    if tg_op='DELETE' then return old; end if;
    return new;
  end if;

  if current_setting('hrp.stage11_release_write', true) is distinct from 'on' then
    raise exception 'Evidence releases may only be published through the governed release-build authority path';
  end if;

  if tg_op in ('UPDATE','DELETE') and old.status in ('approved_seed','approved_release') then
    raise exception 'Approved evidence release % is immutable', old.release_id;
  end if;

  if tg_op='DELETE' then return old; end if;
  return new;
end;
$$;

revoke all on function private.guard_stage11_evidence_release_mutation() from public, anon, authenticated;
