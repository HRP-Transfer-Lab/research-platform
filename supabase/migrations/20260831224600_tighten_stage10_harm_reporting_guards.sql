-- HRP Transfer Evidence Registry v1.1
-- Stage 10 guard tightening: absence of reported harm must never become evidence of no harm.

create or replace function private.validate_stage10_harms_status_semantics()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if new.extraction_status = 'reviewed_no_harm_observed' then
    if not (
      new.assessment_mode = 'systematic'
      and new.systematic_assessment is true
      and new.mapping_source in ('human_review','manual')
      and new.review_status = 'approved'
    ) then
      raise exception 'reviewed_no_harm_observed requires systematic assessment and human-approved authority';
    end if;
  end if;

  if new.assessment_mode = 'systematic' and new.systematic_assessment is distinct from true then
    raise exception 'systematic harms assessment_mode requires systematic_assessment=true';
  end if;

  if new.systematic_assessment is true and new.assessment_mode <> 'systematic' then
    raise exception 'systematic_assessment=true requires assessment_mode=systematic';
  end if;

  if new.extraction_status = 'not_systematically_assessed' and new.systematic_assessment is true then
    raise exception 'not_systematically_assessed cannot coexist with systematic_assessment=true';
  end if;

  return new;
end;
$$;

revoke all on function private.validate_stage10_harms_status_semantics() from public, anon, authenticated;

drop trigger if exists validate_stage10_harms_status_semantics on public.study_harms_status;
create trigger validate_stage10_harms_status_semantics
before insert or update on public.study_harms_status
for each row execute function private.validate_stage10_harms_status_semantics();

create or replace function private.validate_stage10_harm_observation_missingness()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if new.event_count = 0 and new.systematically_assessed is distinct from true then
    raise exception 'event_count=0 is only valid when a systematic harms assessment is explicitly established';
  end if;
  return new;
end;
$$;

revoke all on function private.validate_stage10_harm_observation_missingness() from public, anon, authenticated;

drop trigger if exists validate_stage10_harm_observation_missingness on public.harm_observation;
create trigger validate_stage10_harm_observation_missingness
before insert or update on public.harm_observation
for each row execute function private.validate_stage10_harm_observation_missingness();
