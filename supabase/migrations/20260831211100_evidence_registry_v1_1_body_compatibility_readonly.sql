-- Stage 8 compatibility boundary.
-- Historical body-evidence tables remain readable for audit/provenance but
-- authenticated Workbench users must use the typed v1.1 Stage 8 surfaces.

revoke insert, update, delete on table public.evidence_synthesis from authenticated;
revoke insert, update, delete on table public.synthesis_source from authenticated;
revoke insert, update, delete on table public.approved_claim from authenticated;

grant select on table public.evidence_synthesis to authenticated;
grant select on table public.synthesis_source to authenticated;
grant select on table public.approved_claim to authenticated;

create policy evidence_synthesis_compatibility_read
on public.evidence_synthesis for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy synthesis_source_compatibility_read
on public.synthesis_source for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));

create policy approved_claim_compatibility_read
on public.approved_claim for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
