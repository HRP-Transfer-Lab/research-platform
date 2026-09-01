#!/usr/bin/env python3
"""Apply the additive Stage 12 source-acquisition architecture to local Supabase only."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
MIGRATION = REPO_ROOT / "supabase/migrations/20260901203000_stage12_source_acquisition_architecture.sql"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str, *, capture: bool = False) -> str:
    cmd = [
        "docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|",
    ]
    out = run(cmd, input_text=sql, capture=capture)
    return out.stdout.strip() if capture else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Stage 12 operational source-acquisition architecture locally.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")
    if not MIGRATION.exists():
        raise SystemExit(f"Missing migration {MIGRATION}")

    historical_before = psql(args.container, """
select
  (select status from public.evidence_release where release_id='2026-08-23'),
  (select count(*) from public.release_source_version where release_id='2026-08-23'),
  (select count(*) from public.csi_gateway_evidence_card where evidence_release_id='2026-08-23'),
  (select count(*) from public.csi_gateway_claim where evidence_release_id='2026-08-23'),
  (select current_revision from public.scientific_state_revision where singleton=true);
""", capture=True)

    exists = psql(args.container, "select to_regclass('public.source_acquisition_status') is not null;", capture=True)
    if exists != "t":
        psql(args.container, MIGRATION.read_text(encoding="utf-8"))

    historical_after = psql(args.container, """
select
  (select status from public.evidence_release where release_id='2026-08-23'),
  (select count(*) from public.release_source_version where release_id='2026-08-23'),
  (select count(*) from public.csi_gateway_evidence_card where evidence_release_id='2026-08-23'),
  (select count(*) from public.csi_gateway_claim where evidence_release_id='2026-08-23'),
  (select current_revision from public.scientific_state_revision where singleton=true);
""", capture=True)
    if historical_before != historical_after:
        raise RuntimeError(f"Historical/scientific parity changed unexpectedly: {historical_before!r} -> {historical_after!r}")

    counts = psql(args.container, """
select
  (select count(*) from public.source_version),
  (select count(*) from public.source_acquisition_status),
  (select count(*) from public.source_acquisition_attempt),
  (select count(*) from public.source_document_artifact);
""", capture=True)
    default_unknown = psql(args.container, "select count(*) from public.source_acquisition_status where access_status='unknown';", capture=True)

    print("STAGE 12 SOURCE ACQUISITION ARCHITECTURE READY")
    print("source_versions|acquisition_status_rows|attempts|artifacts")
    print(counts)
    print(f"unknown_status_rows|{default_unknown}")
    print("SCIENTIFIC_STATE_REVISION_CHANGED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
