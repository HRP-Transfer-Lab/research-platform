#!/usr/bin/env python3
"""Validate one complete Stage 12 review-surface packet against local Registry state."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import prepare_stage12_review_surface_packets as prep


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def qident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


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


def stable_projection(packet: dict[str, Any]) -> dict[str, Any]:
    decisions = []
    for unit in packet["units"]:
        for d in unit["decisions"]:
            decisions.append({
                "surface_mode": d["surface_mode"],
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
        d["table_name"],
        json.dumps(d["primary_key"], sort_keys=True),
        d.get("dimension") or "",
        d["surface_mode"],
        d["field_path"],
    ))
    return {
        "schema_version": packet["schema_version"],
        "batch_id": packet["batch_id"],
        "historical_release_id": packet["historical_release_id"],
        "scientific_state_revision": packet["scientific_state_revision"],
        "decision_count": packet["decision_count"],
        "decisions": decisions,
    }


def candidate_snapshot(container: str, candidate_id: int) -> dict[str, Any]:
    raw = prep.psql(container, f"""
select json_build_object(
  'candidate_status',candidate_status,
  'candidate_value_json',candidate_value_json,
  'subject_key',subject_key,
  'field_path',field_path
)::text
from public.scientific_field_candidate
where field_candidate_id={candidate_id};
""")
    require(bool(raw), f"Stage 11 candidate {candidate_id} missing")
    require("\n" not in raw, f"Stage 11 candidate {candidate_id} resolved non-uniquely")
    return json.loads(raw)


def validate_packet(container: str, path: Path) -> tuple[dict[str, Any], str]:
    packet = json.loads(path.read_text(encoding="utf-8"))
    batch_id = packet.get("batch_id")
    require(packet.get("schema_version") == prep.SCHEMA_VERSION, f"{batch_id}: wrong schema_version")
    require(batch_id in prep.BATCH_SPECS, f"Unknown batch_id {batch_id!r}")

    stored_hash = packet.get("packet_sha256")
    unhashed = dict(packet)
    unhashed.pop("packet_sha256", None)
    require(sha256_json(unhashed) == stored_hash, f"{batch_id}: packet_sha256 mismatch")

    current_revision = int(prep.psql(container, "select current_revision from public.scientific_state_revision where singleton=true;"))
    require(packet["scientific_state_revision"] == current_revision,
            f"{batch_id}: scientific revision changed ({packet['scientific_state_revision']} -> {current_revision}); regenerate packet")

    decisions = [d for unit in packet["units"] for d in unit["decisions"]]
    expected = int(prep.BATCH_SPECS[batch_id]["expected"])
    require(len(decisions) == expected, f"{batch_id}: expected {expected} decisions, got {len(decisions)}")
    require(packet.get("decision_count") == expected, f"{batch_id}: decision_count mismatch")

    seen: set[tuple[str, str, str, str]] = set()
    for d in decisions:
        table = d["table_name"]
        pk = d["primary_key"]
        dimension = d.get("dimension")
        mode = d["surface_mode"]
        identity = (table, json.dumps(pk, sort_keys=True), dimension or "", mode)
        require(identity not in seen, f"{batch_id}: duplicate decision {identity}")
        seen.add(identity)

        row_raw = prep.psql(container, f"select to_jsonb(t)::text from public.{qident(table)} t where {pk_where(pk)};")
        require(bool(row_raw), f"{batch_id}: row missing {table} {pk}")
        require("\n" not in row_raw, f"{batch_id}: non-unique primary key {table} {pk}")
        row = json.loads(row_raw)
        require(sha256_json(row) == d["row_snapshot_sha256"], f"{batch_id}: row snapshot drift {table} {pk} {dimension or ''}")

        if mode == "ordinary":
            require(row.get("mapping_source") == "agent_candidate" and row.get("review_status") == "proposed",
                    f"{batch_id}: ordinary row no longer agent_candidate/proposed {table} {pk}")
        elif mode == "dimension":
            require(bool(dimension), f"{batch_id}: dimension decision missing dimension")
            require(row.get(f"{dimension}_mapping_source") == "agent_candidate" and row.get(f"{dimension}_review_status") == "proposed",
                    f"{batch_id}: dimension row no longer agent_candidate/proposed {table} {pk} {dimension}")
        elif mode == "provenance_only":
            require(row.get("mapping_source") == "agent_candidate",
                    f"{batch_id}: provenance-only row no longer agent_candidate {table} {pk}")
        else:
            raise RuntimeError(f"{batch_id}: unknown surface_mode {mode!r}")

        c = candidate_snapshot(container, int(d["candidate_id"]))
        require(c["candidate_status"] == "proposed", f"{batch_id}: candidate {d['candidate_id']} not proposed")
        require(c["candidate_value_json"] == d["candidate_value"], f"{batch_id}: candidate value drift {d['candidate_id']}")
        subject = c["subject_key"]
        require(subject.get("stage12_legacy") is True and subject.get("table") == table and subject.get("primary_key") == pk,
                f"{batch_id}: candidate subject mismatch {d['candidate_id']}")
        if dimension:
            require(subject.get("dimension") == dimension, f"{batch_id}: candidate dimension mismatch {d['candidate_id']}")
        require(c["field_path"] == d["field_path"], f"{batch_id}: candidate field path mismatch {d['candidate_id']}")

    stable_hash = sha256_json(stable_projection(packet))
    return packet, stable_hash


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate one Stage 12 review-surface packet.")
    ap.add_argument("--container", default=prep.DEFAULT_CONTAINER)
    ap.add_argument("--packet-dir", type=Path, default=prep.DEFAULT_OUTPUT_DIR)
    ap.add_argument("--batch", choices=list(prep.BATCH_SPECS), required=True)
    args = ap.parse_args()

    running = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", args.container],
        text=True, check=True, capture_output=True,
    ).stdout.strip()
    require(running == "true", f"Local database container {args.container!r} is not running")

    path = args.packet_dir / f"{args.batch}.json"
    require(path.exists(), f"Missing packet {path}")
    packet, stable_hash = validate_packet(args.container, path)
    print("STAGE 12 REVIEW-SURFACE PACKET VALID")
    print(f"batch_id|{args.batch}")
    print(f"scientific_state_revision|{packet['scientific_state_revision']}")
    print(f"review_units|{packet['review_unit_count']}")
    print(f"decisions|{packet['decision_count']}")
    print(f"packet_sha256|{packet['packet_sha256']}")
    print(f"scientific_decision_sha256|{stable_hash}")
    print("normalized_scientific_rows_changed|0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
