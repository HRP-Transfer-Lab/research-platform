#!/usr/bin/env python3
"""Validate the Stage 7 status-only seed manifest.

This validator deliberately checks that the immutable seed backfill contains no
quality/RoB/GRADE judgements or inferred framework assignments.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage7_seed_status.v1.json"

ALLOWED_STATUS = {
    "not_yet_assessed",
    "assessment_in_progress",
    "partially_assessed",
    "reviewed_complete",
    "not_applicable",
}


def fail(message: str) -> None:
    raise SystemExit(f"STAGE 7 SEED STATUS INVALID: {message}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Stage 7 status-only seed manifest.")
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("manifest_version") != "stage7-seed-v1":
        fail("unexpected manifest_version")
    if manifest.get("release_id") != "2026-08-23":
        fail("unexpected release_id")
    if manifest.get("mapping_source") != "migration":
        fail("status-only seed backfill must use mapping_source=migration")
    if manifest.get("review_status") != "proposed":
        fail("status-only seed backfill must remain review_status=proposed")

    study = manifest.get("study_identity") or {}
    source_ids = study.get("source_ids") or []
    if len(source_ids) != 18 or len(set(source_ids)) != 18:
        fail(f"expected 18 unique study source_ids; got {len(source_ids)}")
    expected_source_ids = [f"rt-2026-{i:03d}" for i in range(1, 19)]
    if source_ids != expected_source_ids:
        fail("study source_ids do not exactly match the 18 immutable seed records")
    if study.get("status") not in ALLOWED_STATUS or study.get("status") != "not_yet_assessed":
        fail("all seed study-quality statuses must be not_yet_assessed")

    result = manifest.get("result_identity") or {}
    identity_path = REPO_ROOT / str(result.get("identity_manifest", ""))
    if not identity_path.exists():
        fail(f"result identity manifest not found: {identity_path}")
    stage4 = json.loads(identity_path.read_text(encoding="utf-8"))
    mappings = stage4.get("mappings") or []
    expected_outcomes = int(result.get("expected_outcomes", -1))
    if expected_outcomes != 38 or len(mappings) != 38:
        fail(f"expected 38 Stage 4 stable outcome identities; manifest={expected_outcomes}, stage4={len(mappings)}")
    if result.get("status") not in ALLOWED_STATUS or result.get("status") != "not_yet_assessed":
        fail("all seed result-RoB statuses must be not_yet_assessed")

    key_fields = result.get("key_fields") or []
    if key_fields != ["source_id", "outcome_name", "legacy_rung", "raw_timepoint"]:
        fail("result stable key must reuse the Stage 4 outcome identity")
    stable_keys = [
        (
            item.get("source_id"),
            item.get("outcome_name"),
            item.get("legacy_rung"),
            item.get("raw_timepoint"),
        )
        for item in mappings
    ]
    if len(set(stable_keys)) != 38:
        fail("Stage 4 outcome stable identities are not unique")
    if {key[0] for key in stable_keys} - set(source_ids):
        fail("Stage 4 outcome identity references a source outside the seed study set")

    backfill = manifest.get("assessment_backfill") or {}
    study_assessments = backfill.get("study_quality_assessments") or []
    result_assessments = backfill.get("result_risk_of_bias_assessments") or []
    domains = backfill.get("domain_judgements") or []
    if study_assessments or result_assessments or domains:
        fail("seed must not contain fabricated study-quality, result-RoB or domain judgements")

    body = manifest.get("body_certainty") or {}
    if body.get("status") != "deferred_to_stage8":
        fail("body certainty must remain deferred_to_stage8")
    if body.get("assessments"):
        fail("Stage 7 seed must not contain GRADE/body-certainty assessments")

    print("STAGE 7 SEED STATUS VALID: studies=18; results=38; study_assessments=0; result_rob_assessments=0; domain_judgements=0")
    print("stable_study_identity: PASS")
    print("stable_result_identity: PASS (Stage 4 outcome key reused)")
    print("status_only_boundary: PASS (18 + 38 all not_yet_assessed)")
    print("no_inferred_framework_assignments: PASS")
    print("no_fabricated_quality_or_rob_judgements: PASS")
    print("body_certainty_boundary: PASS (GRADE deferred to Stage 8)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
