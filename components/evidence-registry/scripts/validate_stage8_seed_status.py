#!/usr/bin/env python3
"""Validate the Stage 8 zero-body seed manifest.

The immutable seed contains source/result evidence only. This validator ensures
Stage 8 does not fabricate propositions, syntheses, GRADE, body EML or claims.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage8_seed_status.v1.json"


def fail(message: str) -> None:
    raise SystemExit(f"STAGE 8 SEED STATUS INVALID: {message}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Stage 8 zero-body seed status manifest.")
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("manifest_version") != "stage8-seed-v1":
        fail("unexpected manifest_version")
    if manifest.get("release_id") != "2026-08-23":
        fail("unexpected release_id")
    if manifest.get("mapping_source") != "migration":
        fail("zero-body seed state must use mapping_source=migration")
    if manifest.get("review_status") != "proposed":
        fail("zero-body seed state must remain review_status=proposed")

    curation = manifest.get("body_curation_status") or {}
    if curation.get("scope_key") != "seed_body_curation" or curation.get("status") != "not_yet_curated":
        fail("body curation status must be seed_body_curation/not_yet_curated")

    legacy = manifest.get("legacy_expectations") or {}
    if legacy != {
        "evidence_synthesis_rows": 0,
        "synthesis_source_rows": 0,
        "approved_claim_rows": 0,
    }:
        fail(f"legacy zero-row expectations changed: {legacy!r}")

    maturity = manifest.get("maturity_expectations") or {}
    if maturity.get("source_record_contribution_eml") != 18:
        fail("expected 18 source record-contribution EML rows")
    for key in ("body_of_evidence_eml", "synthesis_subject_eml", "claim_subject_eml"):
        if maturity.get(key) != 0:
            fail(f"{key} must remain zero in immutable seed")

    effect = manifest.get("source_level_synthesis_effects") or {}
    expected_effect = {
        "expected_count": 1,
        "source_id": "rt-2026-007",
        "outcome_name": "overall post-training working memory",
        "estimate_scope": "source_level_synthesis",
        "estimate_type": "standardised_mean_difference",
        "metric": "Hedges_g",
        "estimate_value": 0.191,
        "ci_lower": 0.062,
        "ci_upper": 0.32,
    }
    for key, value in expected_effect.items():
        if effect.get(key) != value:
            fail(f"source-level synthesis effect {key} mismatch: {effect.get(key)!r} != {value!r}")

    backfill = manifest.get("body_backfill") or {}
    expected_lists = (
        "propositions",
        "contributions",
        "body_syntheses",
        "synthesis_outcomes",
        "body_certainty_assessments",
        "body_maturity_assessments",
        "body_approved_claims",
    )
    for key in expected_lists:
        if backfill.get(key) != []:
            fail(f"immutable seed must not contain Stage 8 {key}")

    grade_boundary = str(manifest.get("grade_boundary", ""))
    eml_boundary = str(manifest.get("eml_boundary", ""))
    claim_boundary = str(manifest.get("claim_boundary", ""))
    if "synthesis_outcome" not in grade_boundary or "No GRADE" not in grade_boundary:
        fail("GRADE body-subject boundary missing")
    if "not inferred" not in eml_boundary.lower() or "source-level EML" not in eml_boundary:
        fail("source/body EML separation boundary missing")
    if "No approved claim" not in claim_boundary:
        fail("claim non-fabrication boundary missing")

    print("STAGE 8 SEED STATUS VALID: propositions=0; contributions=0; body_syntheses=0; synthesis_outcomes=0; body_certainty=0; body_eml=0; body_claims=0")
    print("body_curation_status: PASS (not_yet_curated)")
    print("legacy_body_tables_boundary: PASS (0 synthesis / 0 synthesis_source / 0 approved_claim)")
    print("source_eml_boundary: PASS (18 record-contribution EML; 0 body EML)")
    print("source_level_synthesis_effect_boundary: PASS (1 Hedges_g pooled estimate retained without fake contrast)")
    print("grade_boundary: PASS (GRADE only on future synthesis_outcome)")
    print("no_fabricated_body_objects_or_claims: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
