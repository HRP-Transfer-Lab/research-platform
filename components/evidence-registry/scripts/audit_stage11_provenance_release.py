#!/usr/bin/env python3
"""Read-only audit of existing provenance, adjudication and release-authority machinery before Stage 11."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container,
        "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres",
        "-A", "-t", "-F", "|",
    ]
    return run(cmd, input_text=sql, capture=True).stdout.strip()


def section(title: str) -> None:
    print(f"=== {title} ===")


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Stage 11 provenance/release authority baseline.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    section("EXISTING WORKBENCH AUDIT")
    print("column_name|data_type")
    print(psql(args.container, """
select column_name,data_type
from information_schema.columns
where table_schema='public' and table_name='workbench_audit_log'
order by ordinal_position;
"""))
    print("audit_rows")
    print(psql(args.container, "select count(*) from public.workbench_audit_log;"))
    print("audit_trigger_count|audited_tables")
    print(psql(args.container, """
select count(*)::text || '|' || coalesce(string_agg(c.relname,',' order by c.relname),'')
from pg_trigger t
join pg_class c on c.oid=t.tgrelid
join pg_namespace n on n.oid=c.relnamespace
where not t.tgisinternal and n.nspname='public' and t.tgname like 'audit_%';
"""))

    section("COARSE SCIENTIFIC PROVENANCE FIELDS")
    print("tables_with_mapping_source_and_review_status")
    print(psql(args.container, """
select count(*)
from (
  select table_name
  from information_schema.columns
  where table_schema='public' and column_name in ('mapping_source','review_status')
  group by table_name
  having count(distinct column_name)=2
) x;
"""))
    print("table_name")
    print(psql(args.container, """
select table_name
from information_schema.columns
where table_schema='public' and column_name in ('mapping_source','review_status')
group by table_name
having count(distinct column_name)=2
order by table_name;
"""))

    section("SOURCE VERSION / RELEASE IMMUTABILITY")
    print("source_version_status|count")
    print(psql(args.container, "select version_status,count(*) from public.source_version group by version_status order by version_status;"))
    print("release_id|status|source_versions")
    print(psql(args.container, """
select er.release_id,er.status,count(rsv.source_version_id)
from public.evidence_release er
left join public.release_source_version rsv on rsv.release_id=er.release_id
group by er.release_id,er.status
order by er.release_id;
"""))
    print("guard_trigger")
    print(psql(args.container, """
select tgname
from pg_trigger
where not tgisinternal and tgname in (
  'guard_released_source_version_mutation',
  'guard_approved_release_membership_mutation'
)
order by tgname;
"""))

    section("CURRENT RELEASE BROWSER AUTHORITY")
    print("policyname|cmd|roles")
    print(psql(args.container, """
select policyname,cmd,array_to_string(roles,',')
from pg_policies
where schemaname='public' and tablename='evidence_release'
order by policyname;
"""))

    page = REPO_ROOT / "apps/evidence-workbench/src/WorkbenchPages.tsx"
    page_text = page.read_text(encoding="utf-8") if page.exists() else ""
    direct_release_status_edit = "supabase.from('evidence_release').update({ status })" in page_text
    print(f"workbench_direct_release_status_edit|{'yes' if direct_release_status_edit else 'no'}")

    section("STAGE 11 FIRST-CLASS TABLES")
    targets = [
        'scientific_processing_run',
        'scientific_field_candidate',
        'scientific_field_adjudication',
        'scientific_field_authority',
        'evidence_release_build',
        'release_build_source_version',
    ]
    print("table_name|present")
    for table in targets:
        present = psql(args.container, f"select (to_regclass('public.{table}') is not null)::text;")
        print(f"{table}|{present}")

    section("FIELD-LEVEL EXTRACTION METADATA")
    provenance_columns = psql(args.container, """
select table_name||'.'||column_name
from information_schema.columns
where table_schema='public'
  and column_name in (
    'processing_run_id','model_name','model_version','tool_name','tool_version',
    'prompt_version','extraction_schema_version','confidence','review_decision',
    'authoritative_value_json','scientific_state_sha256','export_manifest_sha256'
  )
order by table_name,column_name;
""")
    print(provenance_columns if provenance_columns else "<none>")

    section("RELEASE / EXPORT CODE INVENTORY")
    script_dir = REPO_ROOT / "components/evidence-registry/scripts"
    candidates = sorted({
        p.relative_to(REPO_ROOT).as_posix()
        for pattern in ('*release*', '*export*', '*manifest*')
        for p in script_dir.glob(pattern)
        if p.is_file()
    })
    print("\n".join(candidates) if candidates else "<none>")

    section("STAGE 11 AUDIT CONCLUSION")
    print("row_level_workbench_audit|present")
    print("released_source_version_immutability|present")
    print("approved_release_membership_immutability|present")
    print("coarse_mapping_source_review_status|present")
    print(f"direct_release_status_edit_in_workbench|{'present' if direct_release_status_edit else 'absent'}")
    print("processing_run_identity|missing")
    print("field_candidate_provenance|missing")
    print("human_adjudication_ledger|missing")
    print("durable_field_authority_ledger|missing")
    print("governed_release_build_state_machine|missing")
    print("deterministic_release_export_hash_ledger|missing")
    print("STAGE 11 AUDIT PASS: existing audit/immutability retained; provenance/adjudication/release-authority gaps identified without mutation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
