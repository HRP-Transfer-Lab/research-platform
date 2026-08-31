#!/usr/bin/env python3
"""Validate Stage 4 seed outcome mapping manifest against the local Registry.

Read-only. Proves stable-key parity, controlled vocabularies, explicit status values,
and the human-approval boundary before any Stage 4 migration/backfill is applied.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage4_seed_mappings.v1.json"

DISTANCES = {"trained_task", "changed_format", "separate_measure", "real_life_function"}
TIMES = {"immediate", "post_intervention", "delayed"}
TRANSFERS = {"horizontal", "vertical", "niche"}
ROLES = {"benefit", "harm", "target_engagement", "process", "adherence", "implementation"}
BRIDGE = {"prompted_use", "cue_triggered_use", "changed_context_use", "unprompted_use", "delayed_portability"}
STATUSES = {"not_yet_extracted", "reviewed_mapped", "reviewed_no_mapping", "not_reported", "not_measured", "not_applicable"}


def run_psql(container: str, sql: str) -> str:
    proc = subprocess.run(
        ["docker", "exec", "-i", container, "psql", "-U", "postgres", "-d", "postgres", "-At", "-F", "|", "-c", sql],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout.strip()


def norm(v):
    return "" if v is None else str(v)


def key_from_mapping(row: dict) -> tuple[str, str, str, str]:
    return (
        norm(row.get("source_id")),
        norm(row.get("outcome_name")),
        norm(row.get("legacy_rung")),
        norm(row.get("raw_timepoint")),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--container", default="supabase_db_research-platform")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    mappings = manifest.get("mappings", [])

    if manifest.get("status") != "agent_candidate":
        raise SystemExit("Manifest status must remain agent_candidate before human review.")
    if len(mappings) != 38:
        raise SystemExit(f"Expected 38 manifest mappings, found {len(mappings)}")

    manifest_keys = [key_from_mapping(row) for row in mappings]
    if len(set(manifest_keys)) != 38:
        raise SystemExit("Duplicate stable keys found in Stage 4 manifest.")

    sql = r"""
select
  s.source_id,
  o.outcome_name,
  coalesce(o.evidence_rung,''),
  coalesce(o.timepoint,'')
from public.evidence_outcome o
join public.study s on s.study_id = o.study_id
order by s.source_id, o.outcome_id;
"""
    db_lines = run_psql(args.container, sql).splitlines()
    db_keys = []
    for line in db_lines:
        parts = line.split("|", 3)
        if len(parts) != 4:
            raise SystemExit(f"Unexpected database row: {line}")
        db_keys.append(tuple(parts))

    if len(db_keys) != 38:
        raise SystemExit(f"Expected 38 database outcomes, found {len(db_keys)}")

    missing = sorted(set(db_keys) - set(manifest_keys))
    extra = sorted(set(manifest_keys) - set(db_keys))
    if missing or extra:
        print("Missing manifest keys:", missing)
        print("Extra manifest keys:", extra)
        raise SystemExit("Stage 4 manifest/database stable-key parity failed.")

    invalid = []
    ambiguous_distance = 0
    no_transfer_mapping = 0
    multi_time = 0
    nonapp_role = 0

    for row in mappings:
        key = key_from_mapping(row)
        distance = row.get("outcome_distance")
        if distance is not None and distance not in DISTANCES:
            invalid.append((key, "outcome_distance", distance))
        for value in row.get("time_classes", []):
            if value not in TIMES:
                invalid.append((key, "time_class", value))
        for value in row.get("transfer_axes", []):
            if value not in TRANSFERS:
                invalid.append((key, "transfer_axis", value))
        for value in row.get("outcome_roles", []):
            if value not in ROLES:
                invalid.append((key, "outcome_role", value))
        for value in row.get("bridge_evidence", []):
            if value not in BRIDGE:
                invalid.append((key, "bridge_evidence", value))
        for field in ("distance_status", "time_status", "transfer_status", "role_status", "bridge_status"):
            if row.get(field) not in STATUSES:
                invalid.append((key, field, row.get(field)))

        if row.get("distance_status") == "not_yet_extracted":
            ambiguous_distance += 1
        if row.get("transfer_status") in {"not_yet_extracted", "reviewed_no_mapping", "not_applicable"} and not row.get("transfer_axes"):
            no_transfer_mapping += 1
        if len(row.get("time_classes", [])) > 1:
            multi_time += 1
        if row.get("role_status") == "not_applicable":
            nonapp_role += 1

    if invalid:
        for item in invalid:
            print("INVALID:", item)
        raise SystemExit(f"Found {len(invalid)} invalid Stage 4 manifest values.")

    print("STAGE 4 SEED MAPPINGS VALID: outcomes=38; manifest_keys=38; database_keys=38")
    print(f"ambiguous_distance_rows={ambiguous_distance}; multi_time_rows={multi_time}; no_transfer_mapping_rows={no_transfer_mapping}; nonapp_role_rows={nonapp_role}")
    print("controlled_vocabularies: PASS")
    print("stable_key_parity: PASS")
    print("human_approval_boundary: PASS (manifest remains agent_candidate; no approval has occurred)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
