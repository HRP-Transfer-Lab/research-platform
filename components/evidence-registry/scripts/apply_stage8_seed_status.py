#!/usr/bin/env python3
"""Apply Stage 8 zero-body curation status to local Supabase.

The immutable seed contains no curated proposition/synthesis/certainty/body-EML
or claim. This helper therefore restores only the explicit not_yet_curated
programme status and verifies that no body-level objects are manufactured.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage8_seed_status.v1.json"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str, *, tuples_only: bool = False) -> str:
    cmd = ["docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres"]
    if tuples_only:
        cmd.extend(["-A", "-t", "-F", "|"])
    result = run(cmd, input_text=sql, capture=tuples_only)
    return result.stdout.strip() if tuples_only else ""


def lit(value) -> str:
    if value is None:
        return "null"
    return "'" + str(value).replace("'", "''") + "'"


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Stage 8 zero-body seed status to local Supabase.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("mapping_source") != "migration" or manifest.get("review_status") != "proposed":
        raise SystemExit("Stage 8 zero-body manifest must remain migration/proposed.")

    backfill = manifest.get("body_backfill") or {}
    if any(backfill.get(key) for key in backfill):
        raise SystemExit("Stage 8 immutable seed must not contain body-level backfill objects.")

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running.")

    curation = manifest["body_curation_status"]
    psql(args.container, f"""
insert into public.body_evidence_stage8_status (
  scope_key, curation_status, mapping_source, review_status, notes
) values (
  {lit(curation['scope_key'])}, {lit(curation['status'])}, 'migration', 'proposed', {lit(curation.get('notes'))}
)
on conflict (scope_key) do update set
  curation_status = excluded.curation_status,
  mapping_source = 'migration',
  review_status = 'proposed',
  notes = excluded.notes,
  updated_at = now()
where public.body_evidence_stage8_status.mapping_source in ('migration','agent_candidate')
  and public.body_evidence_stage8_status.review_status <> 'approved';
""")

    counts = psql(args.container, """
select
  (select count(*) from public.evidence_proposition),
  (select count(*) from public.proposition_evidence_contribution),
  (select count(*) from public.body_evidence_synthesis),
  (select count(*) from public.synthesis_outcome),
  (select count(*) from public.body_certainty_assessment),
  (select count(*) from public.body_maturity_assessment),
  (select count(*) from public.body_approved_claim);
""", tuples_only=True)
    if counts != "0|0|0|0|0|0|0":
        raise SystemExit(f"Stage 8 zero-body replay found unexpected body objects: {counts}")

    print("STAGE 8 ZERO-BODY STATUS APPLIED: curation_status=not_yet_curated")
    print("body_objects: propositions=0; contributions=0; syntheses=0; synthesis_outcomes=0; body_certainty=0; body_eml=0; body_claims=0")
    print("No proposition, GRADE, body EML or approved claim was inferred from the immutable seed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
