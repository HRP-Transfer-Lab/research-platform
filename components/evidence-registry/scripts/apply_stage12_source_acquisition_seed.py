#!/usr/bin/env python3
"""Apply known Stage 12 source-acquisition facts to local Supabase.

Operational only: no scientific review/authority state, historical release membership,
or CSI Gateway publication is mutated.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage12_source_acquisition_seed.v1.json"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


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


def one(raw: str, label: str) -> str:
    rows = [x for x in raw.splitlines() if x]
    if len(rows) != 1:
        raise RuntimeError(f"Expected one {label}; got {rows!r}")
    return rows[0]


def resolve_source_version(container: str, source_id: str) -> str:
    raw = psql(container, f"""
select sv.source_version_id
from public.source_version sv
join public.canonical_source_identity csi
  on csi.canonical_source_id=sv.canonical_source_id
where csi.identity_scheme='legacy_source_id'
  and csi.normalized_value=lower({lit(source_id)})
order by sv.version_number desc;
""", capture=True)
    return one(raw, f"source_version for {source_id}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply deterministic Stage 12 source-acquisition seed facts locally.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")
    if psql(args.container, "select to_regclass('public.source_acquisition_status') is not null;", capture=True) != "t":
        raise RuntimeError("Source-acquisition architecture is not installed; run apply_stage12_source_acquisition_architecture.py first")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "stage12-source-acquisition-seed-v1":
        raise RuntimeError("Unexpected source-acquisition seed schema_version")

    pre = psql(args.container, """
select
  (select status from public.evidence_release where release_id='2026-08-23'),
  (select count(*) from public.release_source_version where release_id='2026-08-23'),
  (select count(*) from public.csi_gateway_evidence_card where evidence_release_id='2026-08-23'),
  (select count(*) from public.csi_gateway_claim where evidence_release_id='2026-08-23'),
  (select current_revision from public.scientific_state_revision where singleton=true);
""", capture=True)

    sql: list[str] = ["begin;", "set local lock_timeout='5s';", "set local statement_timeout='120s';"]
    sources = attempts = artifacts = 0

    for record in manifest.get("records", []):
        source_id = str(record["source_id"])
        source_version_id = resolve_source_version(args.container, source_id)
        sources += 1

        for a in record.get("attempts", []):
            sql.append(f"""
insert into public.source_acquisition_attempt(
  source_version_id,attempt_key,attempted_at,requested_artifact_kind,channel,
  attempted_by_kind,outcome,access_route,blocker_reason,resolved_url,http_status,
  tool_name,tool_version,notes
) values (
  {lit(source_version_id)},{lit(a['attempt_key'])},{lit(a['attempted_at'])}::timestamptz,
  {lit(a['requested_artifact_kind'])},{lit(a['channel'])},{lit(a['attempted_by_kind'])},
  {lit(a['outcome'])},{lit(a.get('access_route','none'))},{lit(a.get('blocker_reason','none'))},
  {lit(a.get('resolved_url'))},{lit(a.get('http_status'))},{lit(a.get('tool_name'))},
  {lit(a.get('tool_version'))},{lit(a.get('notes'))}
)
on conflict (source_version_id,attempt_key) do nothing;
""")
            attempts += 1

        for art in record.get("artifacts", []):
            attempt_key = art.get("attempt_key")
            attempt_expr = "null"
            if attempt_key:
                attempt_expr = f"(select acquisition_attempt_id from public.source_acquisition_attempt where source_version_id={lit(source_version_id)} and attempt_key={lit(attempt_key)})"
            sql.append(f"""
insert into public.source_document_artifact(
  source_version_id,acquisition_attempt_id,artifact_key,artifact_kind,artifact_status,
  access_route,content_sha256,media_type,byte_size,page_count,filename,external_url,
  storage_backend,storage_locator,license_status,notes
) values (
  {lit(source_version_id)},{attempt_expr},{lit(art['artifact_key'])},{lit(art['artifact_kind'])},
  {lit(art.get('artifact_status','available'))},{lit(art['access_route'])},{lit(art.get('content_sha256'))},
  {lit(art.get('media_type'))},{lit(art.get('byte_size'))},{lit(art.get('page_count'))},
  {lit(art.get('filename'))},{lit(art.get('external_url'))},{lit(art.get('storage_backend','none'))},
  {lit(art.get('storage_locator'))},{lit(art.get('license_status','unknown'))},{lit(art.get('notes'))}
)
on conflict (source_version_id,artifact_key) do update set
  acquisition_attempt_id=excluded.acquisition_attempt_id,
  artifact_kind=excluded.artifact_kind,
  artifact_status=excluded.artifact_status,
  access_route=excluded.access_route,
  content_sha256=excluded.content_sha256,
  media_type=excluded.media_type,
  byte_size=excluded.byte_size,
  page_count=excluded.page_count,
  filename=excluded.filename,
  external_url=excluded.external_url,
  storage_backend=excluded.storage_backend,
  storage_locator=excluded.storage_locator,
  license_status=excluded.license_status,
  notes=excluded.notes;
""")
            artifacts += 1

        s = record["status"]
        sql.append(f"""
update public.source_acquisition_status
set access_status={lit(s['access_status'])},
    access_route={lit(s['access_route'])},
    blocker_reason={lit(s.get('blocker_reason','none'))},
    fulltext_available={lit(s.get('fulltext_available',False))},
    fulltext_verified={lit(s.get('fulltext_verified',False))},
    supplement_status={lit(s.get('supplement_status','unknown'))},
    protocol_status={lit(s.get('protocol_status','unknown'))},
    registration_status={lit(s.get('registration_status','unknown'))},
    needs_human_access={lit(s.get('needs_human_access',False))},
    last_checked_at={lit(s.get('last_checked_at'))}::timestamptz,
    next_retry_at={lit(s.get('next_retry_at'))}::timestamptz,
    notes={lit(s.get('notes'))},
    recorded_by_kind={lit(s.get('recorded_by_kind','system'))},
    verification_status={lit(s.get('verification_status','unverified'))},
    updated_at=now()
where source_version_id={lit(source_version_id)};
""")

    sql.append("commit;")
    psql(args.container, "\n".join(sql))

    post = psql(args.container, """
select
  (select status from public.evidence_release where release_id='2026-08-23'),
  (select count(*) from public.release_source_version where release_id='2026-08-23'),
  (select count(*) from public.csi_gateway_evidence_card where evidence_release_id='2026-08-23'),
  (select count(*) from public.csi_gateway_claim where evidence_release_id='2026-08-23'),
  (select current_revision from public.scientific_state_revision where singleton=true);
""", capture=True)
    if pre != post:
        raise RuntimeError(f"Scientific/release/Gateway parity changed unexpectedly: {pre!r} -> {post!r}")

    print("STAGE 12 SOURCE ACQUISITION SEED APPLIED")
    print(f"source_status_updates|{sources}")
    print(f"attempt_manifest_rows|{attempts}")
    print(f"artifact_manifest_rows|{artifacts}")
    print("SCIENTIFIC_STATE_REVISION_CHANGED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
