#!/usr/bin/env python3
"""Validate Stage 12 governed review packets against the current local Registry.

The validator checks both:
- packet_sha256: exact review-instance hash, including Stage 11 candidate ids/run metadata;
- scientific_decision_sha256: stable scientific hash excluding transient ids.

No scientific or provenance rows are mutated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_PACKET_DIR = REPO_ROOT / "components/evidence-registry/review-packets/stage12-seed"
SCHEMA_VERSION = "stage12-review-packet-v1"
EXPECTED = {
    "stage3_ontology": 53,
    "stage5_design": 71,
    "stage4_outcomes": 260,
    "stage6_quantitative": 39,
    "stage9_context": 121,
    "stage10_harms_implementation": 23,
}


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


def sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def dollar_json(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if "$s12v$" in text:
        raise ValueError("unexpected dollar-quote marker")
    return "$s12v$" + text + "$s12v$::jsonb"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def qident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def pk_where(pk: dict[str, Any]) -> str:
    clauses = []
    for key, value in sorted(pk.items()):
        ident = qident(key)
        if value is None:
            clauses.append(f"{ident} is null")
        elif isinstance(value, bool):
            clauses.append(f"{ident}={'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            clauses.append(f"{ident}={value}")
        else:
            clauses.append(f"{ident}={sql_text(str(value))}")
    return " and ".join(clauses)


def stable_decision_projection(packet: dict[str, Any]) -> dict[str, Any]:
    decisions = []
    for unit in packet["units"]:
        for d in unit["decisions"]:
            decisions.append({
                "table_name": d["table_name"],
                "primary_key": d["primary_key"],
                "dimension": d.get("dimension"),
                "field_path": d["field_path"],
                "candidate_value": d["candidate_value"],
                "evidence_basis": d["evidence_basis"],
                "row_snapshot_sha256": d["row_snapshot_sha256"],
                "proposed_action": d["proposed_action"],
            })
    decisions.sort(key=lambda d: (
        d["table_name"], json.dumps(d["primary_key"], sort_keys=True), d.get("dimension") or "", d["field_path"]
    ))
    return {
        "schema_version": packet["schema_version"],
        "batch_id": packet["batch_id"],
        "historical_release_id": packet["historical_release_id"],
        "scientific_state_revision": packet["scientific_state_revision"],
        "decision_count": packet["decision_count"],
        "decisions": decisions,
    }


def validate_packet(container: str, path: Path, current_revision: int) -> tuple[str, int, int]:
    packet = json.loads(path.read_text(encoding="utf-8"))
    require(packet.get("schema_version") == SCHEMA_VERSION, f"{path.name}: wrong schema_version")
    batch_id = packet.get("batch_id")
    require(batch_id in EXPECTED, f"{path.name}: unknown batch_id {batch_id!r}")

    stored_packet_hash = packet.get("packet_sha256")
    unhashed = dict(packet)
    unhashed.pop("packet_sha256", None)
    require(sha256_json(unhashed) == stored_packet_hash, f"{batch_id}: packet_sha256 mismatch")
    require(packet.get("scientific_state_revision") == current_revision,
            f"{batch_id}: scientific revision changed ({packet.get('scientific_state_revision')} -> {current_revision}); regenerate packets")

    flat = [d for unit in packet.get("units", []) for d in unit.get("decisions", [])]
    require(len(flat) == EXPECTED[batch_id], f"{batch_id}: expected {EXPECTED[batch_id]} decisions, got {len(flat)}")
    require(packet.get("decision_count") == len(flat), f"{batch_id}: decision_count mismatch")

    seen: set[tuple[str, str, str]] = set()
    for d in flat:
        table = d["table_name"]
        pk = d["primary_key"]
        dimension = d.get("dimension")
        identity = (table, json.dumps(pk, sort_keys=True), dimension or "")
        require(identity not in seen, f"{batch_id}: duplicate decision {identity}")
        seen.add(identity)

        where = pk_where(pk)
        row_raw = psql(container, f"select to_jsonb(t)::text from public.{qident(table)} t where {where};")
        require(bool(row_raw), f"{batch_id}: row missing {table} {pk}")
        require("\n" not in row_raw, f"{batch_id}: non-unique primary key resolution {table} {pk}")
        row = json.loads(row_raw)
        require(sha256_json(row) == d["row_snapshot_sha256"], f"{batch_id}: row snapshot drift {table} {pk} {dimension or ''}")

        if dimension:
            require(row.get(f"{dimension}_mapping_source") == "agent_candidate" and row.get(f"{dimension}_review_status") == "proposed",
                    f"{batch_id}: Stage 4 dimension no longer agent_candidate/proposed {table} {pk} {dimension}")
        else:
            require(row.get("mapping_source") == "agent_candidate" and row.get("review_status") == "proposed",
                    f"{batch_id}: row no longer agent_candidate/proposed {table} {pk}")

        cid = int(d["candidate_id"])
        candidate_raw = psql(container, f"""
select candidate_status||'|'||candidate_value_json::text||'|'||subject_key::text||'|'||field_path
from public.scientific_field_candidate where field_candidate_id={cid};
""")
        require(bool(candidate_raw), f"{batch_id}: Stage 11 candidate {cid} missing")
        parts = candidate_raw.split("|", 3)
        require(parts[0] == "proposed", f"{batch_id}: Stage 11 candidate {cid} is {parts[0]}, not proposed")
        require(json.loads(parts[1]) == d["candidate_value"], f"{batch_id}: candidate value drift for {cid}")
        subject_key = json.loads(parts[2])
        require(subject_key.get("stage12_legacy") is True and subject_key.get("table") == table and subject_key.get("primary_key") == pk,
                f"{batch_id}: candidate subject key mismatch for {cid}")
        if dimension:
            require(subject_key.get("dimension") == dimension, f"{batch_id}: candidate dimension mismatch for {cid}")
        require(parts[3] == d["field_path"], f"{batch_id}: candidate field_path mismatch for {cid}")

    stable_hash = sha256_json(stable_decision_projection(packet))
    return stable_hash, len(packet.get("units", [])), len(flat)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Stage 12 review packets against the current local Registry.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    require(running == "true", f"Local database container {args.container!r} is not running")
    current_revision = int(psql(args.container, "select current_revision from public.scientific_state_revision where singleton=true;"))

    print("STAGE 12 REVIEW PACKET VALIDATION")
    print(f"scientific_state_revision|{current_revision}")
    print("batch_id|review_units|decisions|scientific_decision_sha256")
    total = 0
    for batch_id in EXPECTED:
        path = args.packet_dir / f"{batch_id}.json"
        require(path.exists(), f"Missing packet {path}")
        stable_hash, units, decisions = validate_packet(args.container, path, current_revision)
        total += decisions
        print(f"{batch_id}|{units}|{decisions}|{stable_hash}")
    require(total == 567, f"Expected 567 total decisions, got {total}")
    print("total_decisions|567")
    print("normalized_scientific_rows_changed|0")
    print("STAGE 12 REVIEW PACKETS VALID: exact packet hashes, stable scientific hashes, DB snapshots and Stage 11 candidate bridges all match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
