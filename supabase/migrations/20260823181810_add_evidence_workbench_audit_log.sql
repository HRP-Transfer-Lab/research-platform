create table if not exists public.workbench_audit_log (
  audit_id bigserial primary key,
  occurred_at timestamptz not null default now(),
  actor_user_id uuid references auth.users(id),
  table_name text not null,
  action text not null check (action in ('INSERT','UPDATE','DELETE')),
  before_row jsonb,
  after_row jsonb
);

alter table public.workbench_audit_log enable row level security;
revoke all on public.workbench_audit_log from anon;
grant select on public.workbench_audit_log to authenticated, service_role;
grant all on public.workbench_audit_log to service_role;
grant usage, select on sequence public.workbench_audit_log_audit_id_seq to service_role;

create policy workbench_audit_read
on public.workbench_audit_log for select
to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create or replace function private.audit_workbench_change()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.workbench_audit_log (
    actor_user_id,
    table_name,
    action,
    before_row,
    after_row
  ) values (
    (select auth.uid()),
    tg_table_name,
    tg_op,
    case when tg_op in ('UPDATE','DELETE') then to_jsonb(old) else null end,
    case when tg_op in ('INSERT','UPDATE') then to_jsonb(new) else null end
  );

  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

revoke all on function private.audit_workbench_change() from public;

do $$
declare
  t text;
begin
  foreach t in array array[
    'evidence_release','evidence_source','study','intervention_component','evidence_outcome',
    'product_relevance','quality_assessment','evidence_synthesis','synthesis_source',
    'approved_claim','workbench_member'
  ]
  loop
    execute format('drop trigger if exists %I on public.%I', 'audit_' || t, t);
    execute format(
      'create trigger %I after insert or update or delete on public.%I for each row execute function private.audit_workbench_change()',
      'audit_' || t,
      t
    );
  end loop;
end $$;

comment on table public.workbench_audit_log is 'Append-only audit trail for Evidence Workbench mutations. Browser clients can read it only as editor/owner and cannot write it directly.';
