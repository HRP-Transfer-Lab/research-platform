#!/usr/bin/env python3
"""Validate that corrected Stage 9 review surface differs only by the geography fix."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import prepare_stage12_review_surface_packets as prep

DEFAULT_ORIGINAL = prep.DEFAULT_OUTPUT_DIR / "stage9_context.json"
DEFAULT_CORRECTED = prep.DEFAULT_OUTPUT_DIR / "stage9_context_corrected.json"
EXPECTED_ORIGINAL_SHA = "af21c00c7e71c1271a24625c1b02f858e25c17cca23b883a7cdfc4e1917dc3bc"


def decisions(packet: dict) -> list[dict]:
    return [d for unit in packet["units"] for d in unit["decisions"]]


def key(d: dict) -> str:
    payload = {
        "surface_mode": d["surface_mode"],
        "table_name": d["table_name"],
        "primary_key": d["primary_key"],
        "dimension": d.get("dimension"),
        "field_path": d["field_path"],
        "candidate_value": d["candidate_value"],
        "evidence_basis": d["evidence_basis"],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def is_removed_geography_decision(d: dict) -> bool:
    if d["table_name"] == "study_population_context_status":
        return d["primary_key"] == {"facet_kind": "geography", "study_id": 15}
    if d["table_name"] == "study_population_context_term":
        return d["primary_key"] == {
            "relationship": "entire_sample", "study_id": 15, "term_id": "pc_geo_china"
        }
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Stage 9 original-to-corrected packet delta.")
    ap.add_argument("--original", type=Path, default=DEFAULT_ORIGINAL)
    ap.add_argument("--corrected", type=Path, default=DEFAULT_CORRECTED)
    args = ap.parse_args()

    original = json.loads(args.original.read_text(encoding="utf-8"))
    corrected = json.loads(args.corrected.read_text(encoding="utf-8"))

    if original.get("packet_sha256") != EXPECTED_ORIGINAL_SHA:
        raise RuntimeError("Original Stage 9 packet SHA does not match reviewed 121-decision packet")
    if original.get("decision_count") != 121:
        raise RuntimeError("Original Stage 9 packet must contain 121 decisions")
    if corrected.get("batch_id") != "stage9_context_corrected":
        raise RuntimeError("Corrected packet has unexpected batch id")
    if corrected.get("decision_count") != 119:
        raise RuntimeError("Corrected Stage 9 packet must contain 119 decisions")
    if corrected.get("scientific_state_revision", 0) <= original.get("scientific_state_revision", 0):
        raise RuntimeError("Corrected packet must be bound to a later scientific revision")

    original_decisions = decisions(original)
    removed = [d for d in original_decisions if is_removed_geography_decision(d)]
    if len(removed) != 2:
        raise RuntimeError(f"Expected exactly two geography decisions in original packet, found {len(removed)}")

    expected = sorted(key(d) for d in original_decisions if not is_removed_geography_decision(d))
    actual = sorted(key(d) for d in decisions(corrected))
    if expected != actual:
        expected_set, actual_set = set(expected), set(actual)
        missing = len(expected_set - actual_set)
        added = len(actual_set - expected_set)
        raise RuntimeError(
            f"Corrected Stage 9 packet contains scientific drift beyond geography correction: missing={missing}, added={added}"
        )

    print("STAGE 12 STAGE 9 CORRECTION DELTA VALID")
    print(f"original_packet_sha256|{original['packet_sha256']}")
    print(f"original_scientific_revision|{original['scientific_state_revision']}")
    print(f"corrected_packet_sha256|{corrected['packet_sha256']}")
    print(f"corrected_scientific_revision|{corrected['scientific_state_revision']}")
    print("original_decisions|121")
    print("removed_geography_decisions|2")
    print("corrected_decisions|119")
    print("other_scientific_value_drift|0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
