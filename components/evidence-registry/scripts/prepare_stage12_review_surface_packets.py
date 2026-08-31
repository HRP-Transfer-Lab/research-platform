#!/usr/bin/env python3
"""Prepare complete Stage 12 governed review-surface packets.

This v2 generator covers all candidate-provenance shapes discovered by the
schema-driven review-surface audit:
- ordinary mapping_source + review_status rows;
- dimension-specific <dimension>_mapping_source + <dimension>_review_status rows;
- provenance-only mapping_source status rows.

Packet preparation creates/reuses Stage 11 compatibility candidate provenance
only. It never approves normalized scientific state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

import prepare_stage12_review_packets as legacy

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = legacy.DEFAULT_CONTAINER
DEFAULT_OUTPUT_DIR = legacy.DEFAULT_OUTPUT_DIR
SCHEMA_VERSION = "stage12-review-surface-v2"
HISTORICAL_RELEASE = "2026-08-23"

_COMMAND_TAG = re.compile(r"^(?:INSERT\s+\d+\s+\d+|UPDATE\s+\d+|DELETE\s+\d+|SELECT\s+\d+)$")
_ORIGINAL_PSQL = legacy.psql


def cleaned_psql(container: str, sql: str) -> str:
    raw = _ORIGINAL_PSQL(container, sql)
    lines = [line for line in raw.splitlines() if line and not _COMMAND_TAG.match(line)]
    return "\n".join(lines)


legacy.psql = cleaned_psql
psql = cleaned_psql

BATCH_SPECS: dict[str, dict[str, Any]] = {
    "stage3_extraction_status": {
        "label": "Stage 3 extraction status — target and mechanism completeness",
        "expected": 17,
        "group": "source",
        "surfaces": [
            {"mode": "provenance_only", "table": "component_target_extraction_status"},
            {"mode": "provenance_only", "table": "source_version_mechanism_status"},
        ],
    },
    "stage5_complete": {
        "label": "Stage 5 complete study design — arms, components, contrasts and extraction status",
        "expected": 107,
        "group": "study",
        "surfaces": [
            {"mode": "ordinary", "table": "study_arm"},
            {"mode": "ordinary", "table": "arm_component"},
            {"mode": "ordinary", "table": "study_contrast"},
            {"mode": "ordinary", "table": "contrast_arm_member"},
            {"mode": "dimension", "table": "study_stage5_status", "dimension": "arm"},
            {"mode": "dimension", "table": "study_stage5_status", "dimension": "contrast"},
        ],
    },
    "stage4_outcomes": {
        "label": "Stage 4 outcome semantics — distance, time, transfer, role and Bridge",
        "expected": 260,
        "group": "outcome",
        "surfaces": [
            *[
                {"mode": "dimension", "table": "outcome_stage4_classification", "dimension": dim}
                for dim in ("distance", "time", "transfer", "role", "bridge")
            ],
            {"mode": "ordinary", "table": "outcome_role_link"},
            {"mode": "ordinary", "table": "outcome_time_link"},
            {"mode": "ordinary", "table": "outcome_transfer_axis"},
        ],
    },
    "stage6_quantitative": {
        "label": "Stage 6 quantitative extraction and effect estimates",
        "expected": 39,
        "group": "outcome",
        "surfaces": [
            {"mode": "ordinary", "table": "outcome_stage6_status"},
            {"mode": "ordinary", "table": "effect_estimate"},
        ],
    },
    "stage9_context": {
        "label": "Stage 9 population, study context and delivery context",
        "expected": 121,
        "group": "source",
        "surfaces": [
            {"mode": "ordinary", "table": "study_population_context_status"},
            {"mode": "ordinary", "table": "study_population_context_term"},
            {"mode": "ordinary", "table": "component_delivery_context_status"},
            {"mode": "ordinary", "table": "component_delivery_context_term"},
        ],
    },
    "stage10_harms_implementation": {
        "label": "Stage 10 harms, implementation, participation and support dependence",
        "expected": 23,
        "group": "source",
        "surfaces": [
            {"mode": "ordinary", "table": "boundary_condition_observation"},
            {"mode": "ordinary", "table": "component_implementation_observation"},
            {"mode": "ordinary", "table": "component_implementation_status"},
            {"mode": "ordinary", "table": "harm_observation"},
            {"mode": "ordinary", "table": "study_harms_status"},
            {"mode": "ordinary", "table": "study_participation_observation"},
            {"mode": "ordinary", "table": "support_dependence_observation"},
        ],
    },
}

EVIDENCE_TEXT_KEYS = legacy.EVIDENCE_TEXT_KEYS


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def unresolved_rows(container: str, surface: dict[str, Any]) -> list[dict[str, Any]]:
    table = surface["table"]
    mode = surface["mode"]
    if mode == "ordinary":
        where = "mapping_source='agent_candidate' and review_status='proposed'"
    elif mode == "dimension":
        dim = surface["dimension"]
        where = f"{dim}_mapping_source='agent_candidate' and {dim}_review_status='proposed'"
    elif mode == "provenance_only":
        where = "mapping_source='agent_candidate'"
    else:
        raise RuntimeError(f"Unknown review surface mode {mode!r}")
    raw = psql(
        container,
        f'select to_jsonb(t)::text from public."{table}" t where {where} order by to_jsonb(t)::text;',
    )
    return [json.loads(line) for line in raw.splitlines() if line]


def scientific_value(row: dict[str, Any], surface: dict[str, Any], pk: dict[str, Any]) -> dict[str, Any]:
    mode = surface["mode"]
    if mode == "dimension":
        dim = surface["dimension"]
        prefix = dim + "_"
        value = {
            k: v for k, v in row.items()
            if k.startswith(prefix) and k not in {f"{dim}_mapping_source", f"{dim}_review_status"}
        }
        # Stage 4 outcome distance is the one single-valued Stage 4 dimension whose
        # scientific value lives on the classification row but does not use the
        # ``distance_`` prefix. Bind it explicitly so human adjudication/authority
        # covers the actual distance classification as well as its extraction state.
        if (
            surface.get("table") == "outcome_stage4_classification"
            and dim == "distance"
        ):
            value["outcome_distance"] = row.get("outcome_distance")
        value.update(pk)
        return value
    excluded = {"mapping_source", "review_status", "created_at", "updated_at"}
    return {k: v for k, v in row.items() if k not in excluded}


def evidence_basis(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in EVIDENCE_TEXT_KEYS:
        value = row.get(key)
        if value is not None and str(value).strip():
            parts.append(f"{key}: {value}")
    return " | ".join(parts) if parts else "No separate evidence-basis text field; review the complete proposed row snapshot and linked source context."


def bridge_candidate(
    container: str,
    run_id: int,
    table: str,
    pk: dict[str, Any],
    dimension: str | None,
    value: dict[str, Any],
    basis: str,
) -> int:
    return legacy.ensure_candidate(container, run_id, table, pk, dimension, value, basis)


def stable_sort_key(decision: dict[str, Any]) -> tuple[Any, ...]:
    context = decision["context"]
    return (
        context.get("source_id") or "",
        context.get("study_id") or -1,
        context.get("outcome_id") or -1,
        decision["table_name"],
        json.dumps(decision["primary_key"], sort_keys=True),
        decision.get("dimension") or "",
        decision["surface_mode"],
    )


def build_batch(container: str, output_dir: Path, batch_id: str, progress_every: int) -> dict[str, Any]:
    spec = BATCH_SPECS[batch_id]
    output_dir.mkdir(parents=True, exist_ok=True)
    git_sha = subprocess.run(["git", "rev-parse", "HEAD"], text=True, check=True, capture_output=True).stdout.strip()
    revision = int(psql(container, "select current_revision from public.scientific_state_revision where singleton=true;"))
    run_id = legacy.ensure_bridge_run(container, git_sha)

    decisions: list[dict[str, Any]] = []
    pk_cache: dict[str, list[str]] = {}
    done = 0
    for surface in spec["surfaces"]:
        table = surface["table"]
        pk_cols = pk_cache.setdefault(table, legacy.table_pk_columns(container, table))
        for row in unresolved_rows(container, surface):
            pk = {col: row.get(col) for col in pk_cols}
            if any(v is None for v in pk.values()):
                raise RuntimeError(f"Missing primary-key value for {table}: {pk}")
            value = scientific_value(row, surface, pk)
            basis = evidence_basis(row)
            dimension = surface.get("dimension")
            candidate_id = bridge_candidate(container, run_id, table, pk, dimension, value, basis)
            context = legacy.resolve_source_context(container, row)
            decision = {
                "candidate_id": candidate_id,
                "surface_mode": surface["mode"],
                "table_name": table,
                "primary_key": pk,
                "dimension": dimension,
                "field_path": f"legacy_seed_review.{table}" + (f".{dimension}" if dimension else ""),
                "candidate_value": value,
                "evidence_basis": basis,
                "context": context,
                "row_snapshot_sha256": sha256_json(row),
                "proposed_action": "approve",
            }
            decisions.append(decision)
            done += 1
            if done == 1 or done % max(1, progress_every) == 0 or done == spec["expected"]:
                print(f"review-surface progress|{done}/{spec['expected']}", flush=True)

    decisions.sort(key=stable_sort_key)
    if len(decisions) != spec["expected"]:
        raise RuntimeError(f"{batch_id}: expected {spec['expected']} unresolved decisions, found {len(decisions)}")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    contexts: dict[str, dict[str, Any]] = {}
    for d in decisions:
        key = legacy.group_key(spec["group"], d["context"], d)
        grouped[key].append(d)
        contexts.setdefault(key, d["context"])

    units = [
        {
            "unit_key": key,
            "label": legacy.group_label(contexts[key], key),
            "context": contexts[key],
            "decisions": grouped[key],
        }
        for key in sorted(grouped)
    ]

    payload = {
        "schema_version": SCHEMA_VERSION,
        "batch_id": batch_id,
        "batch_label": spec["label"],
        "historical_release_id": HISTORICAL_RELEASE,
        "scientific_state_revision": revision,
        "bridge_processing_run_id": run_id,
        "generated_from_git_commit": git_sha,
        "decision_count": len(decisions),
        "review_unit_count": len(units),
        "units": units,
        "governance_notes": [
            "Packet preparation does not approve scientific state.",
            "Detailed historical model/prompt metadata for pre-Stage-11 candidates is unavailable and has not been fabricated.",
            "Packet includes ordinary, dimension-specific or provenance-only candidate status surfaces as declared per decision.",
            "Approval must verify the exact packet hash, stable scientific-decision hash and unchanged scientific revision.",
        ],
    }
    packet_hash = sha256_json(payload)
    packet = dict(payload)
    packet["packet_sha256"] = packet_hash

    json_path = output_dir / f"{batch_id}.json"
    md_path = output_dir / f"{batch_id}.md"
    json_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        f"# Stage 12 review packet — {spec['label']}",
        "",
        f"- Packet: `{batch_id}`",
        f"- SHA-256: `{packet_hash}`",
        f"- Scientific revision: `{revision}`",
        f"- Decisions: **{len(decisions)}**",
        f"- Review units: **{len(units)}**",
        "",
        "> No item in this packet is approved by packet generation. Human review is required.",
        "",
    ]
    for unit in units:
        lines.extend([f"## {unit['label']}", ""])
        for d in unit["decisions"]:
            identity = json.dumps(d["primary_key"], ensure_ascii=False, sort_keys=True)
            suffix = f" / {d['dimension']}" if d["dimension"] else ""
            value_text = json.dumps(d["candidate_value"], ensure_ascii=False, sort_keys=True)
            lines.extend([
                f"### `{d['table_name']}`{suffix}",
                "",
                f"- Surface mode: `{d['surface_mode']}`",
                f"- Key: `{identity}`",
                f"- Stage 11 candidate: `{d['candidate_id']}`",
                f"- Proposed value: `{value_text}`",
                f"- Evidence basis: {d['evidence_basis']}",
                f"- Row snapshot: `{d['row_snapshot_sha256']}`",
                "",
            ])
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print("STAGE 12 REVIEW-SURFACE PACKET PREPARED")
    print(f"batch_id|{batch_id}")
    print(f"scientific_state_revision|{revision}")
    print(f"review_units|{len(units)}")
    print(f"decisions|{len(decisions)}")
    print(f"packet_sha256|{packet_hash}")
    print("normalized_scientific_rows_changed|0")
    return packet


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare complete Stage 12 review-surface packets without approval.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    ap.add_argument("--batch", action="append", choices=list(BATCH_SPECS), required=True)
    ap.add_argument("--progress-every", type=int, default=10)
    args = ap.parse_args()

    running = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", args.container],
        text=True, check=True, capture_output=True,
    ).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    for batch_id in args.batch:
        build_batch(args.container, args.output_dir, batch_id, args.progress_every)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
