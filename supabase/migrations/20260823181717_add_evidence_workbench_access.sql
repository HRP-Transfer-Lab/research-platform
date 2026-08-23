create table if not exists public.workbench_member (
  user_id uuid primary key references auth.users(id) on delete cascade,
  role text not null check (role in ('viewer','editor','owner')),
  active boolean not null default true,
  display_name text,
  created_at timestamptz not null default now(),
  created_by uuid references auth.users(id)
);

alter table public.workbench_member enable row level security;

create schema if not exists private;

create or replace function private.has_workbench_role(allowed_roles text[])
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.workbench_member wm
    where wm.user_id = (select auth.uid())
      and wm.active is true
      and wm.role = any(allowed_roles)
  );
$$;

revoke all on function private.has_workbench_role(text[]) from public;
grant usage on schema private to authenticated, service_role;
grant execute on function private.has_workbench_role(text[]) to authenticated, service_role;

revoke all on public.workbench_member from anon;
grant select, insert, update, delete on public.workbench_member to authenticated, service_role;

create policy workbench_member_read
on public.workbench_member for select
to authenticated
using (
  user_id = (select auth.uid())
  or (select private.has_workbench_role(array['owner']::text[]))
);

create policy workbench_member_insert
on public.workbench_member for insert
to authenticated
with check ((select private.has_workbench_role(array['owner']::text[])));

create policy workbench_member_update
on public.workbench_member for update
to authenticated
using ((select private.has_workbench_role(array['owner']::text[])))
with check ((select private.has_workbench_role(array['owner']::text[])));

create policy workbench_member_delete
on public.workbench_member for delete
to authenticated
using ((select private.has_workbench_role(array['owner']::text[])));

grant select, insert, update, delete on
  public.evidence_source,
  public.study,
  public.intervention_component,
  public.evidence_outcome,
  public.product_relevance,
  public.quality_assessment,
  public.evidence_synthesis,
  public.synthesis_source
  to authenticated;

grant select, insert, update, delete on
  public.evidence_release,
  public.approved_claim
  to authenticated;

grant usage, select on all sequences in schema public to authenticated;
grant select on public.v_approved_evidence, public.v_product_evidence to authenticated;
revoke all on public.v_approved_evidence, public.v_product_evidence from anon;

do $$
declare
  t text;
begin
  foreach t in array array[
    'evidence_release','evidence_source','study','intervention_component','evidence_outcome',
    'product_relevance','quality_assessment','evidence_synthesis','synthesis_source','approved_claim'
  ]
  loop
    execute format(
      'create policy %I on public.%I for select to authenticated using ((select private.has_workbench_role(array[''viewer'',''editor'',''owner'']::text[])))',
      t || '_workbench_read', t
    );
  end loop;
end $$;

do $$
declare
  t text;
begin
  foreach t in array array[
    'evidence_source','study','intervention_component','evidence_outcome',
    'product_relevance','quality_assessment','evidence_synthesis','synthesis_source'
  ]
  loop
    execute format(
      'create policy %I on public.%I for insert to authenticated with check ((select private.has_workbench_role(array[''editor'',''owner'']::text[])))',
      t || '_workbench_insert', t
    );
    execute format(
      'create policy %I on public.%I for update to authenticated using ((select private.has_workbench_role(array[''editor'',''owner'']::text[]))) with check ((select private.has_workbench_role(array[''editor'',''owner'']::text[])))',
      t || '_workbench_update', t
    );
    execute format(
      'create policy %I on public.%I for delete to authenticated using ((select private.has_workbench_role(array[''editor'',''owner'']::text[])))',
      t || '_workbench_delete', t
    );
  end loop;
end $$;

create policy evidence_release_workbench_insert
on public.evidence_release for insert to authenticated
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy evidence_release_workbench_update
on public.evidence_release for update to authenticated
using ((select private.has_workbench_role(array['owner']::text[])))
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy evidence_release_workbench_delete
on public.evidence_release for delete to authenticated
using ((select private.has_workbench_role(array['owner']::text[])));

create policy approved_claim_workbench_insert
on public.approved_claim for insert to authenticated
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy approved_claim_workbench_update
on public.approved_claim for update to authenticated
using ((select private.has_workbench_role(array['owner']::text[])))
with check ((select private.has_workbench_role(array['owner']::text[])));
create policy approved_claim_workbench_delete
on public.approved_claim for delete to authenticated
using ((select private.has_workbench_role(array['owner']::text[])));

comment on table public.workbench_member is 'Explicit Evidence Workbench membership. Browser access to registry tables is denied unless an authenticated user has an active viewer/editor/owner membership.';
comment on function private.has_workbench_role(text[]) is 'RLS helper for Evidence Workbench role checks; kept in private non-exposed schema.';
