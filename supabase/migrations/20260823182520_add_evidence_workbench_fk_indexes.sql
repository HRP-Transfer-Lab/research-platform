create index if not exists workbench_audit_log_actor_idx
  on public.workbench_audit_log(actor_user_id);

create index if not exists workbench_member_created_by_idx
  on public.workbench_member(created_by);
