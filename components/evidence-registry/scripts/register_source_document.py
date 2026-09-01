#!/usr/bin/env python3
"""Register a locally acquired source document without copying it into Git.

Computes SHA-256/byte size (and PDF page count when pdfinfo is available), records
an append-only acquisition attempt + artifact metadata, and updates operational
acquisition status. Scientific review/authority and release/Gateway state are untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import mimetypes
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CONTAINER = "supabase_db_research-platform"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=check, capture_output=capture)


def psql(container: str, sql: str, *, capture: bool = False) -> str:
    cmd = [
        "docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|",
    ]
    out = run(cmd, input_text=sql, capture=capture)
    return out.stdout.strip() if capture else ""


def lit(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def resolve_source_version(container: str, source_id: str) -> str:
    raw = psql(container, f"""
select sv.source_version_id
from public.source_version sv
join public.canonical_source_identity csi on csi.canonical_source_id=sv.canonical_source_id
where csi.identity_scheme='legacy_source_id' and csi.normalized_value=lower({lit(source_id)})
order by sv.version_number desc;
""", capture=True)
    rows = [x for x in raw.splitlines() if x]
    if len(rows) != 1:
        raise RuntimeError(f"Expected one source version for {source_id}; got {rows!r}")
    return rows[0]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def pdf_pages(path: Path) -> int | None:
    exe = shutil.which("pdfinfo")
    if not exe:
        return None
    out = run([exe, str(path)], capture=True, check=False)
    if out.returncode != 0:
        return None
    for line in out.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Register a local source document in operational acquisition state.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--source-id", required=True)
    ap.add_argument("--file", type=Path, required=True)
    ap.add_argument("--artifact-kind", choices=["full_text","supplement","protocol","sap","registration_record","other"], default="full_text")
    ap.add_argument("--access-route", choices=["open_access","repository","author_preprint","publisher","institutional_library","user_supplied","manual_web","other"], required=True)
    ap.add_argument("--channel", choices=["crossref","openalex","unpaywall","europe_pmc","pubmed","publisher","repository","institutional_library","user_upload","manual_web","other"], default="other")
    ap.add_argument("--license-status", choices=["unknown","open","institutional_use","user_provided","publisher_access","restricted"], default="unknown")
    ap.add_argument("--storage-backend", choices=["local_corpus","supabase_storage","external_url","other"], default="local_corpus")
    ap.add_argument("--storage-locator")
    ap.add_argument("--external-url")
    ap.add_argument("--attempt-key")
    ap.add_argument("--notes")
    args = ap.parse_args()

    path = args.file.expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"File not found: {path}")
    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")
    if psql(args.container, "select to_regclass('public.source_document_artifact') is not null;", capture=True) != "t":
        raise RuntimeError("Source-acquisition architecture is not installed")

    source_version_id = resolve_source_version(args.container, args.source_id)
    digest = sha256_file(path)
    byte_size = path.stat().st_size
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    page_count = pdf_pages(path) if media_type == "application/pdf" else None
    now = datetime.now(timezone.utc).isoformat()
    attempt_key = args.attempt_key or f"local-{args.artifact_kind}-{digest[:16]}"
    artifact_key = f"{args.artifact_kind}-{digest[:16]}"
    locator = args.storage_locator or str(path)

    requested_kind = "registration" if args.artifact_kind == "registration_record" else args.artifact_kind
    outcome_map = {
        "full_text": "fulltext_acquired",
        "supplement": "supplement_acquired",
        "protocol": "protocol_acquired",
        "sap": "protocol_acquired",
        "registration_record": "registration_acquired",
        "other": "no_change",
    }
    outcome = outcome_map[args.artifact_kind]

    pre = psql(args.container, """
select
 (select current_revision from public.scientific_state_revision where singleton=true),
 (select status from public.evidence_release where release_id='2026-08-23'),
 (select count(*) from public.csi_gateway_evidence_card where evidence_release_id='2026-08-23');
""", capture=True)

    status_updates = []
    if args.artifact_kind == "full_text":
        status_updates += [
            "access_status='fulltext_verified'",
            f"access_route={lit(args.access_route)}",
            "blocker_reason='none'",
            "fulltext_available=true",
            "fulltext_verified=true",
            "needs_human_access=false",
        ]
    elif args.artifact_kind == "supplement":
        status_updates.append("supplement_status='verified'")
    elif args.artifact_kind in ("protocol", "sap"):
        status_updates.append("protocol_status='verified'")
    elif args.artifact_kind == "registration_record":
        status_updates.append("registration_status='verified'")
    status_updates += [
        f"last_checked_at={lit(now)}::timestamptz",
        "recorded_by_kind='system'",
        "verification_status='system_verified'",
        "updated_at=now()",
    ]

    sql = f"""
begin;
set local lock_timeout='5s';
set local statement_timeout='120s';

insert into public.source_acquisition_attempt(
 source_version_id,attempt_key,attempted_at,requested_artifact_kind,channel,
 attempted_by_kind,outcome,access_route,blocker_reason,resolved_url,tool_name,tool_version,notes
) values (
 {lit(source_version_id)},{lit(attempt_key)},{lit(now)}::timestamptz,{lit(requested_kind)},
 {lit(args.channel)},'system',{lit(outcome)},{lit(args.access_route)},'none',{lit(args.external_url)},
 'register_source_document.py','1',{lit(args.notes)}
)
on conflict (source_version_id,attempt_key) do nothing;

insert into public.source_document_artifact(
 source_version_id,acquisition_attempt_id,artifact_key,artifact_kind,artifact_status,
 access_route,content_sha256,media_type,byte_size,page_count,filename,external_url,
 storage_backend,storage_locator,license_status,notes,verified_at
) values (
 {lit(source_version_id)},
 (select acquisition_attempt_id from public.source_acquisition_attempt where source_version_id={lit(source_version_id)} and attempt_key={lit(attempt_key)}),
 {lit(artifact_key)},{lit(args.artifact_kind)},'verified',{lit(args.access_route)},{lit(digest)},
 {lit(media_type)},{byte_size},{lit(page_count)},{lit(path.name)},{lit(args.external_url)},
 {lit(args.storage_backend)},{lit(locator)},{lit(args.license_status)},{lit(args.notes)},{lit(now)}::timestamptz
)
on conflict (source_version_id,artifact_key) do update set
 acquisition_attempt_id=excluded.acquisition_attempt_id,
 artifact_status='verified', access_route=excluded.access_route,
 content_sha256=excluded.content_sha256, media_type=excluded.media_type,
 byte_size=excluded.byte_size, page_count=excluded.page_count, filename=excluded.filename,
 external_url=excluded.external_url, storage_backend=excluded.storage_backend,
 storage_locator=excluded.storage_locator, license_status=excluded.license_status,
 notes=excluded.notes, verified_at=excluded.verified_at;

update public.source_acquisition_status
set {', '.join(status_updates)}
where source_version_id={lit(source_version_id)};
commit;
"""
    psql(args.container, sql)

    post = psql(args.container, """
select
 (select current_revision from public.scientific_state_revision where singleton=true),
 (select status from public.evidence_release where release_id='2026-08-23'),
 (select count(*) from public.csi_gateway_evidence_card where evidence_release_id='2026-08-23');
""", capture=True)
    if pre != post:
        raise RuntimeError(f"Scientific/release/Gateway parity changed unexpectedly: {pre!r} -> {post!r}")

    print("SOURCE DOCUMENT REGISTERED")
    print(f"source_id|{args.source_id}")
    print(f"source_version_id|{source_version_id}")
    print(f"artifact_kind|{args.artifact_kind}")
    print(f"content_sha256|{digest}")
    print(f"byte_size|{byte_size}")
    print(f"page_count|{page_count if page_count is not None else ''}")
    print(f"storage_backend|{args.storage_backend}")
    print("SCIENTIFIC_STATE_REVISION_CHANGED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
