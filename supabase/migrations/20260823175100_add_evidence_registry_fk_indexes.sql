create index if not exists approved_claim_synthesis_idx
  on public.approved_claim(synthesis_id)
  where synthesis_id is not null;

create index if not exists synthesis_source_source_idx
  on public.synthesis_source(source_id);
