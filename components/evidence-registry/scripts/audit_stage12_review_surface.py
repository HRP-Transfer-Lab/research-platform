#!/usr/bin/env python3
"""Read-only audit of every Stage 12 scientific review/provenance surface.

Discovers three patterns dynamically from public schema metadata:
1. generic mapping_source + review_status;
2. dimension-specific <x>_mapping_source + <x>_review_status;
3. provenance-only mapping_source tables with no review_status column.

The third pattern matters for explicit extraction/completeness state where the
schema records who established the state but has no separate approval field.
No rows are mutated.
"""
from __future__ import annotations

import argparse
import subprocess

DEFAULT_CONTAINER = "supabase_db_research-platform"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=False, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|",
    ]
    result = run(cmd, input_text=sql, capture=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "<no PostgreSQL stderr>"
        stdout = result.stdout.strip()
        extra = f"\nstdout:\n{stdout}" if stdout else ""
        raise RuntimeError(f"psql failed with exit status {result.returncode}:\n{stderr}{extra}")
    return result.stdout.strip()


def qident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit all Stage 12 review/provenance surfaces without mutation.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    print("=== GENERIC REVIEW SURFACES ===")
    generic_raw = psql(args.container, """
select table_name
from information_schema.columns
where table_schema='public' and column_name in ('mapping_source','review_status')
group by table_name
having count(distinct column_name)=2
order by table_name;
""")
    generic_tables = [x for x in generic_raw.splitlines() if x]
    generic_unresolved = 0
    print("table_name|mapping_source|review_status|count")
    for table in generic_tables:
        ident = qident(table)
        rows = psql(args.container, f"""
select {table!r}::text,mapping_source,review_status,count(*)
from public.{ident}
group by mapping_source,review_status
order by mapping_source,review_status;
""")
        if rows:
            print(rows)
        count = psql(args.container, f"select count(*) from public.{ident} where mapping_source='agent_candidate' and review_status='proposed';")
        generic_unresolved += int(count or "0")

    print("=== DIMENSION-SPECIFIC REVIEW SURFACES ===")
    dim_raw = psql(args.container, """
with ms as (
  select table_name, column_name, regexp_replace(column_name, '_mapping_source$', '') as dimension
  from information_schema.columns
  where table_schema='public' and column_name like '%\\_mapping_source' escape '\\'
), rs as (
  select table_name, column_name, regexp_replace(column_name, '_review_status$', '') as dimension
  from information_schema.columns
  where table_schema='public' and column_name like '%\\_review_status' escape '\\'
)
select ms.table_name||'|'||ms.dimension
from ms join rs using (table_name,dimension)
order by ms.table_name,ms.dimension;
""")
    dimension_pairs = [tuple(line.split("|", 1)) for line in dim_raw.splitlines() if line]
    dim_unresolved = 0
    print("table_name|dimension|mapping_source|review_status|count")
    for table, dim in dimension_pairs:
        ident = qident(table)
        ms = qident(dim + "_mapping_source")
        rs = qident(dim + "_review_status")
        rows = psql(args.container, f"""
select {table!r}::text,{dim!r}::text,{ms},{rs},count(*)
from public.{ident}
group by {ms},{rs}
order by {ms},{rs};
""")
        if rows:
            print(rows)
        count = psql(args.container, f"select count(*) from public.{ident} where {ms}='agent_candidate' and {rs}='proposed';")
        dim_unresolved += int(count or "0")

    print("=== PROVENANCE-ONLY STATUS SURFACES ===")
    lone_raw = psql(args.container, """
select c.table_name
from information_schema.columns c
where c.table_schema='public' and c.column_name='mapping_source'
  and not exists (
    select 1 from information_schema.columns r
    where r.table_schema='public' and r.table_name=c.table_name and r.column_name='review_status'
  )
order by c.table_name;
""")
    lone_tables = [x for x in lone_raw.splitlines() if x]
    lone_unresolved = 0
    print("table_name|mapping_source|count")
    for table in lone_tables:
        ident = qident(table)
        rows = psql(args.container, f"""
select {table!r}::text,mapping_source,count(*)
from public.{ident}
group by mapping_source
order by mapping_source;
""")
        if rows:
            print(rows)
        count = psql(args.container, f"select count(*) from public.{ident} where mapping_source='agent_candidate';")
        lone_unresolved += int(count or "0")

    total = generic_unresolved + dim_unresolved + lone_unresolved
    print("=== REVIEW SURFACE SUMMARY ===")
    print(f"generic_agent_candidate_proposed|{generic_unresolved}")
    print(f"dimension_agent_candidate_proposed|{dim_unresolved}")
    print(f"provenance_only_agent_candidate|{lone_unresolved}")
    print(f"total_unresolved_review_surface|{total}")
    print("STAGE 12 REVIEW SURFACE AUDIT PASS: read-only schema-driven inventory completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
