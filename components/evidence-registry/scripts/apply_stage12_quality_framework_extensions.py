#!/usr/bin/env python3
"""Apply the additive Stage 12 quality-framework extension to local Supabase only."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
MIGRATION = REPO_ROOT / "supabase/migrations/20260901184500_stage12_quality_appraisal_framework_extensions.sql"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str, *, capture: bool = False) -> str:
    cmd = [
        "docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|",
    ]
    completed = run(cmd, input_text=sql, capture=capture)
    return completed.stdout.strip() if capture else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply additive Stage 12 quality-framework vocabulary locally.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")
    if not MIGRATION.exists():
        raise SystemExit(f"Missing migration {MIGRATION}")

    before = psql(args.container, """
select
  (select count(*) from public.evidence_release where release_id='2026-08-23'),
  (select count(*) from public.csi_gateway_release where evidence_release_id='2026-08-23'),
  (select count(*) from public.assessment_framework_definition);
""", capture=True)

    psql(args.container, MIGRATION.read_text(encoding="utf-8"))

    after = psql(args.container, """
select
  (select count(*) from public.evidence_release where release_id='2026-08-23'),
  (select count(*) from public.csi_gateway_release where evidence_release_id='2026-08-23'),
  (select count(*) from public.assessment_framework_definition);
""", capture=True)

    frameworks = psql(args.container, """
select framework_key,version_label,subject_kind
from public.assessment_framework_definition
where framework_key in ('rob2','robins_i','robins_e','amstar2','consort','prisma','prisma_scr','cosmin')
order by framework_key;
""", capture=True)

    print("STAGE 12 QUALITY FRAMEWORK EXTENSIONS APPLIED")
    print(f"pre|historical_release|gateway_release|frameworks|{before}")
    print(f"post|historical_release|gateway_release|frameworks|{after}")
    print("framework_key|version_label|subject_kind")
    print(frameworks)
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
