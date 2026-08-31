-- HRP Transfer Evidence Registry v1.1
-- Stage 11 processing-run consistency constraints.

alter table public.scientific_processing_run
  add constraint stage11_processing_run_completion_consistency
  check (
    (run_status='started' and completed_at is null)
    or
    (run_status<>'started' and completed_at is not null)
  );

alter table public.scientific_processing_run
  add constraint stage11_agent_run_identity_required
  check (
    actor_kind not in ('agent','hybrid')
    or tool_name is not null
    or model_name is not null
  );

create or replace function private.guard_stage11_candidate_mutation()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_run_status text;
begin
  if tg_op='INSERT' then
    if new.candidate_status <> 'proposed' then
      raise exception 'Scientific field candidates must be inserted as proposed';
    end if;
    select run_status into v_run_status
    from public.scientific_processing_run
    where processing_run_id=new.processing_run_id;
    if v_run_status in ('failed','cancelled') then
      raise exception 'Failed/cancelled processing run % cannot create scientific candidates',new.processing_run_id;
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
