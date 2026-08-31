#!/usr/bin/env python3
"""Validate Stage 11 provenance/adjudication/release authority in local Supabase."""
from __future__ import annotations

import argparse
import subprocess

DEFAULT_CONTAINER = "supabase_db_research-platform"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=check, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd = ["docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|"]
    return run(cmd, input_text=sql, capture=True).stdout.strip()


def scalar(container: str, sql: str) -> int:
    value = psql(container, sql)
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"Expected integer SQL result; got {value!r}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"STAGE 11 PROVENANCE/RELEASE INVALID: {message}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    require(running == "true", f"local database container {args.container!r} is not running")

    expected_tables = [
        "scientific_processing_run",
        "scientific_field_candidate",
        "scientific_field_adjudication",
        "scientific_field_authority",
        "evidence_release_build",
        "release_build_source_version",
        "release_export_artifact",
        "scientific_state_revision",
    ]
    table_list = ",".join("'" + t + "'" for t in expected_tables)
    present = scalar(args.container, f"select count(*) from information_schema.tables where table_schema='public' and table_name in ({table_list});")
    require(present == len(expected_tables), f"expected {len(expected_tables)} Stage 11 tables; got {present}")

    seed = psql(args.container, """
select er.release_id||'|'||er.status||'|'||count(rsv.source_version_id)::text
from public.evidence_release er
left join public.release_source_version rsv on rsv.release_id=er.release_id
where er.release_id='2026-08-23'
group by er.release_id,er.status;
""")
    require(seed == "2026-08-23|approved_seed|18", f"historical seed release changed: {seed!r}")
    require(scalar(args.container, "select count(*) from public.source_version;") == 18, "expected 18 seed source versions")

    # Historical records predate first-class run provenance; do not fabricate it.
    require(scalar(args.container, "select count(*) from public.scientific_processing_run;") == 0, "historical seed must not receive fabricated processing-run metadata")
    require(scalar(args.container, "select count(*) from public.scientific_field_candidate;") == 0, "historical seed must not receive fabricated field candidates")
    require(scalar(args.container, "select count(*) from public.scientific_field_adjudication;") == 0, "historical seed must not receive fabricated adjudications")
    require(scalar(args.container, "select count(*) from public.scientific_field_authority;") == 0, "historical seed must not receive fabricated field-authority rows")

    # Browser and service-role release CRUD must be gone.
    write_policies = scalar(args.container, """
select count(*) from pg_policies
where schemaname='public' and tablename='evidence_release' and cmd in ('INSERT','UPDATE','DELETE');
""")
    require(write_policies == 0, f"direct evidence_release write policies remain={write_policies}")

    write_grants = scalar(args.container, """
select count(*) from information_schema.role_table_grants
where table_schema='public' and table_name='evidence_release'
  and grantee in ('authenticated','service_role')
  and privilege_type in ('INSERT','UPDATE','DELETE');
""")
    require(write_grants == 0, f"authenticated/service direct evidence_release write grants remain={write_grants}")

    membership_write_grants = scalar(args.container, """
select count(*) from information_schema.role_table_grants
where table_schema='public' and table_name='release_source_version'
  and grantee in ('authenticated','service_role')
  and privilege_type in ('INSERT','UPDATE','DELETE');
""")
    require(membership_write_grants == 0, f"direct release_source_version write grants remain={membership_write_grants}")

    guards = psql(args.container, """
select string_agg(tgname,',' order by tgname)
from pg_trigger
where not tgisinternal and tgname in (
 'guard_stage11_processing_run_mutation','guard_stage11_candidate_mutation',
 'guard_stage11_adjudication_mutation','guard_stage11_authority_mutation',
 'guard_stage11_release_build_mutation','guard_stage11_release_membership_mutation',
 'guard_stage11_release_artifact_mutation','guard_stage11_evidence_release_mutation',
 'guard_stage11_release_source_version_insert','guard_released_source_version_mutation',
 'guard_approved_release_membership_mutation'
);
""")
    require(guards.count(",") + (1 if guards else 0) == 11, f"expected 11 Stage 2/11 authority guards; got {guards!r}")

    function_names = [
        "adjudicate_scientific_field_candidate",
        "create_evidence_release_build",
        "prepare_evidence_release_build",
        "record_evidence_release_build_validation",
        "approve_evidence_release_build",
        "publish_evidence_release_build",
    ]
    functions = scalar(args.container, """
select count(distinct p.proname)
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname in (
 'adjudicate_scientific_field_candidate','create_evidence_release_build','prepare_evidence_release_build',
 'record_evidence_release_build_validation','approve_evidence_release_build','publish_evidence_release_build'
);
""")
    require(functions == len(function_names), f"expected {len(function_names)} governed public operations; got {functions}")

    service_privs = psql(args.container, """
select
 has_function_privilege('service_role','public.record_evidence_release_build_validation(text,text,text,jsonb,jsonb,text,bigint)','EXECUTE'),
 has_function_privilege('service_role','public.approve_evidence_release_build(text)','EXECUTE'),
 has_function_privilege('service_role','public.publish_evidence_release_build(text)','EXECUTE'),
 has_function_privilege('service_role','public.adjudicate_scientific_field_candidate(bigint,text,jsonb,text)','EXECUTE');
""")
    require(service_privs == "t|f|f|f", f"service-role authority boundary changed: {service_privs!r}")

    candidate_grants = psql(args.container, """
select
 has_table_privilege('service_role','public.scientific_field_candidate','INSERT'),
 has_table_privilege('service_role','public.scientific_field_adjudication','INSERT'),
 has_table_privilege('service_role','public.scientific_field_authority','INSERT');
""")
    require(candidate_grants == "t|f|f", f"machine candidate/adjudication/authority grant boundary changed: {candidate_grants!r}")

    rls = scalar(args.container, """
select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' and c.relname in (
 'scientific_processing_run','scientific_field_candidate','scientific_field_adjudication','scientific_field_authority',
 'evidence_release_build','release_build_source_version','release_export_artifact','scientific_state_revision'
) and c.relrowsecurity;
""")
    require(rls == 8, f"expected RLS on all 8 Stage 11 tables; got {rls}")

    revision = scalar(args.container, "select current_revision from public.scientific_state_revision where singleton=true;")
    require(revision >= 0, "scientific state revision clock missing")
    revision_triggers = scalar(args.container, "select count(*) from pg_trigger where not tgisinternal and tgname='stage11_state_revision';")
    require(revision_triggers >= 60, f"scientific-state revision coverage unexpectedly low={revision_triggers}")

    # No release build should be manufactured by seed replay.
    require(scalar(args.container, "select count(*) from public.evidence_release_build;") == 0, "seed replay must not manufacture release builds")
    require(scalar(args.container, "select count(*) from public.release_export_artifact;") == 0, "seed replay must not manufacture export artifacts")

    print(
        "STAGE 11 PROVENANCE/RELEASE VALID: "
        f"tables=8; seed_release=2026-08-23/18; revision={revision}; revision_triggers={revision_triggers}; "
        "processing_runs=0; candidates=0; adjudications=0; authorities=0; builds=0"
    )
    print("historical_provenance_nonfabrication: PASS")
    print("machine_candidate_vs_human_authority: PASS (service INSERT candidate only)")
    print("direct_release_crud_removed: PASS (authenticated + service_role)")
    print("owner_release_build_rpc_boundary: PASS")
    print("service_validation_not_approval: PASS")
    print("released_source_version_immutability: PASS")
    print("scientific_state_revision_clock: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
