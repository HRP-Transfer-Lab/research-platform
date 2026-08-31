-- Tighten Stage 8 body-level EML approval and EML3+ convergence guards.

alter table public.body_maturity_assessment
  add constraint body_maturity_approved_review_check
  check (assessment_status <> 'approved' or review_status = 'approved');

create or replace function private.validate_stage8_body_maturity()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  outcome_review_status text;
  outcome_status text;
  body_synthesis_id bigint;
  synthesis_review_status text;
  synthesis_status text;
  included_studies integer;
begin
  if new.maturity_level >= 3 then
    if coalesce(new.direct_study_count, 0) < 2 then
      raise exception 'Body EML3+ requires at least two direct contributing studies';
    end if;
    if coalesce(new.genuine_replication_count, 0) < 1 then
      raise exception 'Body EML3+ requires at least one genuine replication';
    end if;
    if nullif(btrim(coalesce(new.replication_basis, '')), '') is null then
      raise exception 'Body EML3+ requires an explicit replication_basis';
    end if;
    if coalesce(new.consistency_pattern, '') not in ('consistent','mixed_but_convergent') then
      raise exception 'Body EML3+ requires a reviewed convergent direction pattern; got %', new.consistency_pattern;
    end if;
  end if;

  if new.independent_replication_count is not null
     and new.genuine_replication_count is not null
     and new.independent_replication_count > new.genuine_replication_count then
    raise exception 'Independent replication count cannot exceed genuine replication count';
  end if;

  select so.review_status, so.status, so.body_synthesis_id, so.included_study_count
    into outcome_review_status, outcome_status, body_synthesis_id, included_studies
  from public.synthesis_outcome so
  where so.synthesis_outcome_id = new.synthesis_outcome_id;

  if new.review_status = 'approved' or new.assessment_status = 'approved' then
    if outcome_review_status <> 'approved' or outcome_status <> 'approved' then
      raise exception 'Approved body EML requires an approved synthesis outcome';
    end if;

    select bes.review_status, bes.status into synthesis_review_status, synthesis_status
    from public.body_evidence_synthesis bes
    where bes.body_synthesis_id = body_synthesis_id;

    if synthesis_review_status <> 'approved' or synthesis_status <> 'approved' then
      raise exception 'Approved body EML requires an approved body synthesis';
    end if;

    if new.maturity_level >= 4 and coalesce(included_studies, 0) < 2 then
      raise exception 'Approved body EML4+ requires a multi-study synthesis outcome';
    end if;
  end if;

  return new;
end;
$$;

revoke all on function private.validate_stage8_body_maturity() from public, anon, authenticated;
