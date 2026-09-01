#!/usr/bin/env python3
"""Read-only audit of Stage 12 source acquisition/readiness state."""
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
    out = run(cmd, input_text=sql, capture=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or out.stdout.strip())
    return out.stdout.strip()


def scalar(container: str, sql: str) -> int:
    return int(psql(container, sql) or "0")


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit source acquisition/readiness without mutation.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")
    if psql(args.container, "select to_regclass('public.source_acquisition_status') is not null;") != "t":
        raise SystemExit("SOURCE ACQUISITION AUDIT INVALID: architecture not installed")

    print("=== STAGE 12 SOURCE ACQUISITION ===")
    print("source_versions|status_rows|attempts|artifacts")
    print(psql(args.container, """
select
 (select count(*) from public.source_version),
 (select count(*) from public.source_acquisition_status),
 (select count(*) from public.source_acquisition_attempt),
 (select count(*) from public.source_document_artifact);
"""))

    print("access_status|count")
    print(psql(args.container, "select access_status,count(*) from public.source_acquisition_status group by access_status order by access_status;"))
    print("access_route|count")
    print(psql(args.container, "select access_route,count(*) from public.source_acquisition_status group by access_route order by access_route;"))
    print("blocker_reason|count")
    print(psql(args.container, "select blocker_reason,count(*) from public.source_acquisition_status group by blocker_reason order by blocker_reason;"))

    print("source_id|access_status|access_route|blocker_reason|fulltext_available|fulltext_verified|needs_human_access|attempts|artifacts")
    print(psql(args.container, """
select source_id,access_status,access_route,blocker_reason,fulltext_available,fulltext_verified,
       needs_human_access,acquisition_attempts,available_artifacts
from public.v_source_acquisition_dashboard
where source_id in ('rt-2026-004','rt-2026-005','rt-2026-014')
order by source_id;
"""))

    missing_status = scalar(args.container, """
select count(*) from public.source_version sv
where not exists(select 1 from public.source_acquisition_status s where s.source_version_id=sv.source_version_id);
""")
    bad_verified = scalar(args.container, "select count(*) from public.source_acquisition_status where fulltext_verified and not fulltext_available;")
    orphan_attempts = scalar(args.container, """
select count(*) from public.source_acquisition_attempt a
where not exists(select 1 from public.source_version sv where sv.source_version_id=a.source_version_id);
""")
    orphan_artifacts = scalar(args.container, """
select count(*) from public.source_document_artifact a
where not exists(select 1 from public.source_version sv where sv.source_version_id=a.source_version_id);
""")
    scientific_surface_columns = scalar(args.container, """
select count(*) from information_schema.columns
where table_schema='public'
  and table_name in ('source_acquisition_status','source_acquisition_attempt','source_document_artifact')
  and column_name in ('mapping_source','review_status');
""")

    rt004_bad = scalar(args.container, """
select count(*) from public.v_source_acquisition_dashboard
where source_id='rt-2026-004'
  and not (access_status='blocked' and access_route='institutional_library'
           and blocker_reason='institutional_unavailable' and not fulltext_available);
""")
    rt005_bad = scalar(args.container, """
select count(*) from public.v_source_acquisition_dashboard
where source_id='rt-2026-005'
  and not (access_status='blocked' and access_route='institutional_library'
           and blocker_reason='institutional_unavailable' and not fulltext_available);
""")
    rt014_bad = scalar(args.container, """
select count(*) from public.v_source_acquisition_dashboard
where source_id='rt-2026-014'
  and not (access_status in ('fulltext_available','fulltext_verified')
           and access_route='user_supplied' and fulltext_available);
""")
    rt014_artifact_bad = scalar(args.container, """
select count(*) from public.source_document_artifact a
join public.source_version sv on sv.source_version_id=a.source_version_id
join public.canonical_source_identity csi on csi.canonical_source_id=sv.canonical_source_id
where csi.identity_scheme='legacy_source_id' and csi.normalized_value='rt-2026-014'
  and a.artifact_key='fulltext-user-2026-09-01'
  and not (a.artifact_kind='full_text' and a.media_type='application/pdf' and a.page_count=73
           and a.access_route='user_supplied');
""")

    errors = {
        "source_versions_without_status": missing_status,
        "invalid_fulltext_verified_state": bad_verified,
        "orphan_acquisition_attempts": orphan_attempts,
        "orphan_document_artifacts": orphan_artifacts,
        "acquisition_rows_accidentally_on_scientific_review_surface": scientific_surface_columns,
        "rt004_seed_mismatch": rt004_bad,
        "rt005_seed_mismatch": rt005_bad,
        "rt014_seed_mismatch": rt014_bad,
        "rt014_artifact_mismatch": rt014_artifact_bad,
    }
    print("integrity_metric|count")
    for key, value in errors.items():
        print(f"{key}|{value}")

    if any(errors.values()):
        print("STAGE 12 SOURCE ACQUISITION AUDIT|INVALID")
        return 1

    open_sources = scalar(args.container, """
select count(*) from public.source_acquisition_status
where access_status in ('unknown','metadata_only','abstract_only','blocked','retrieval_failed');
""")
    print(f"sources_without_fulltext_ready_state|{open_sources}")
    print("SOURCE ACQUISITION READINESS|" + ("PARTIAL" if open_sources else "FULLTEXT_READY"))
    print("STAGE 12 SOURCE ACQUISITION AUDIT|PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
