#!/usr/bin/env python3
"""Strict no-inference V4 rescore for the rt-014 local extraction calibration.

V4 reuses the frozen V2 Qwen semantic extraction. Explicit participant counts
are resolved only from configured main-table headings and repeated observation
rows; the trial identifier is resolved by the existing unique-regex rule.

This script makes no Ollama calls and does not mutate PostgreSQL, scientific
authority, historical releases or the CSI Gateway.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import stage13_calibrate_local_extraction as v1
import stage13_calibrate_local_extraction_v2 as v2
import stage13_deterministic_extraction as deterministic
import stage13_rescore_local_extraction_v3 as v3
import stage13_table_count_extraction as table_counts


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROFILE = (
    REPO_ROOT
    / "components/evidence-registry/config/stage13_calibration_rt014.v4.json"
)
DEFAULT_V2_DIR = (
    Path.home()
    / "hrp-lab/source-corpus/rt-2026-014/manifests/stage13-local-calibration-v2"
)
DEFAULT_MODELS = ("qwen3.5:4b",)


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Strictly rescore frozen V2 extraction using table-aware deterministic fields."
    )
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--v2-dir", type=Path, default=DEFAULT_V2_DIR)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    args = parser.parse_args()

    profile_path = args.profile.expanduser().resolve()
    v2_dir = args.v2_dir.expanduser().resolve()
    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else v2_dir.parent / "stage13-local-calibration-v4"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    profile, base_profile_path = v3.load_profile(profile_path)
    source_id = str(profile["source_id"])
    spans_path = v2_dir / "spans.jsonl"
    if not spans_path.is_file():
        raise SystemExit(f"V2 span manifest not found: {spans_path}")
    spans = v3.load_spans(spans_path)
    span_by_id = {span.span_id: span for span in spans}

    regex_candidates, regex_diagnostics = deterministic.unique_regex_candidates(
        spans, profile.get("deterministic_fields", {})
    )
    table_candidates, table_diagnostics = table_counts.table_scoped_integer_candidates(
        spans, profile.get("table_deterministic_fields", {})
    )
    candidates = {**regex_candidates, **table_candidates}

    deterministic_names = [
        str(value) for value in profile["deterministic_field_names"]
    ]
    deterministic_extraction = {
        field: candidates.get(field, v3.unresolved_field())
        for field in deterministic_names
    }

    generated_at = datetime.now(timezone.utc).isoformat()
    candidate_path = output_dir / "deterministic-candidates.json"
    v2.write_json(candidate_path, {
        "schema_version": "stage13-deterministic-candidates-v2",
        "source_id": source_id,
        "profile_id": profile["profile_id"],
        "candidates": deterministic_extraction,
        "diagnostics": {
            "unique_regex": regex_diagnostics,
            "table_scoped_integer": table_diagnostics,
        },
        "generated_at": generated_at,
    })

    print("=== STAGE 13 LOCAL EXTRACTION CALIBRATION V4 RESCORE ===")
    print(f"source_id|{source_id}")
    print("ollama_calls|0")
    print(f"parser_owned_spans|{len(spans)}")
    print("deterministic_fields|" + ",".join(deterministic_names))

    for field in ("week1_platform_entrants", "delayed_assessment_completers"):
        diagnostic = table_diagnostics.get(field, {})
        print(
            f"table_resolver|{field}|selected={int(bool(diagnostic.get('selected')))}|"
            f"value={'' if diagnostic.get('selected_value') is None else diagnostic.get('selected_value')}|"
            f"page={'' if diagnostic.get('selected_page') is None else diagnostic.get('selected_page')}|"
            f"ambiguous={int(bool(diagnostic.get('ambiguous')))}"
        )
        for row in diagnostic.get("page_candidates", []):
            print(
                f"table_candidate|{field}|page={row.get('pdf_page')}|"
                f"excluded={int(bool(row.get('excluded')))}|"
                f"qualifies={int(bool(row.get('qualifies')))}|"
                f"selected_value={'' if row.get('selected_value') is None else row.get('selected_value')}|"
                f"frequency={row.get('selected_frequency')}|"
                f"margin={row.get('frequency_margin')}|"
                f"heading={compact(row.get('heading_matches', []))}"
            )

    gold: dict[str, Any] = profile["gold"]
    support_rules: dict[str, Any] = profile["support_rules"]
    thresholds: dict[str, Any] = profile["thresholds"]
    model_fields = [str(value) for value in profile["model_fields"]]
    summaries: list[dict[str, Any]] = []

    for model in args.models:
        source_result_path = v2_dir / f"{v1.model_filename(model)}.v2.json"
        if not source_result_path.is_file():
            raise SystemExit(f"Frozen V2 model result not found: {source_result_path}")
        source_result = v1.load_json(source_result_path)
        full_v2_model_extraction = source_result.get("model_extraction")
        if not isinstance(full_v2_model_extraction, dict):
            raise SystemExit(f"No model_extraction object in {source_result_path}")

        semantic_extraction = {
            field: full_v2_model_extraction.get(field, v3.unresolved_field())
            for field in model_fields
        }
        hybrid = {**semantic_extraction, **deterministic_extraction}

        semantic_gold = {field: gold[field] for field in model_fields}
        deterministic_gold = {field: gold[field] for field in deterministic_names}
        semantic_results, semantic_matches = v2.score_fields(
            semantic_extraction, semantic_gold
        )
        deterministic_results, deterministic_matches = v2.score_fields(
            deterministic_extraction, deterministic_gold
        )
        hybrid_results, hybrid_matches = v2.score_fields(hybrid, gold)
        reference_checks, reference_valid, reference_attempted = v2.span_reference_checks(
            hybrid, span_by_id
        )
        support_checks, supported_matches = v2.semantic_support_checks(
            hybrid, gold, support_rules, span_by_id
        )

        semantic_total = len(semantic_gold)
        deterministic_total = len(deterministic_gold)
        total = len(gold)
        semantic_accuracy = semantic_matches / semantic_total if semantic_total else 1.0
        deterministic_accuracy = (
            deterministic_matches / deterministic_total if deterministic_total else 1.0
        )
        hybrid_accuracy = hybrid_matches / total if total else 1.0
        reference_rate = (
            reference_valid / reference_attempted if reference_attempted else 1.0
        )
        supported_accuracy = supported_matches / total if total else 1.0
        schema_errors = v2.validate_structure(hybrid, list(gold))
        schema_valid = not schema_errors

        passed = (
            schema_valid
            and semantic_accuracy
            >= float(thresholds["minimum_semantic_model_field_accuracy"])
            and deterministic_accuracy
            >= float(thresholds["minimum_deterministic_field_accuracy"])
            and hybrid_accuracy
            >= float(thresholds["minimum_hybrid_field_accuracy"])
            and reference_rate
            >= float(thresholds["minimum_span_reference_validity"])
            and supported_accuracy
            >= float(thresholds["minimum_supported_field_accuracy"])
        )
        single_source_candidate = (
            schema_valid
            and semantic_accuracy
            >= float(thresholds["single_source_candidate_semantic_field_accuracy"])
            and deterministic_accuracy
            >= float(thresholds["single_source_candidate_deterministic_field_accuracy"])
            and hybrid_accuracy
            >= float(thresholds["single_source_candidate_hybrid_field_accuracy"])
            and reference_rate
            >= float(thresholds["single_source_candidate_span_reference_validity"])
            and supported_accuracy
            >= float(thresholds["single_source_candidate_supported_field_accuracy"])
        )

        result_path = output_dir / f"{v1.model_filename(model)}.v4-rescore.json"
        v2.write_json(result_path, {
            "schema_version": "stage13-local-calibration-result-v4",
            "source_id": source_id,
            "profile_id": profile["profile_id"],
            "profile_path": str(profile_path),
            "base_profile_path": str(base_profile_path) if base_profile_path else None,
            "model": model,
            "model_inference_reused": True,
            "source_v2_result_path": str(source_result_path),
            "source_v2_result_sha256": v1.sha256_file(source_result_path),
            "span_manifest_path": str(spans_path),
            "span_manifest_sha256": v1.sha256_file(spans_path),
            "semantic_model_extraction": semantic_extraction,
            "deterministic_extraction": deterministic_extraction,
            "hybrid_extraction": hybrid,
            "validation": {
                "schema_valid": schema_valid,
                "structure_errors": schema_errors,
                "semantic_model_field_results": semantic_results,
                "deterministic_field_results": deterministic_results,
                "hybrid_field_results": hybrid_results,
                "span_reference_checks": reference_checks,
                "semantic_support_checks": support_checks,
                "passed": passed,
                "single_source_pipeline_candidate": single_source_candidate,
                "production_scale_ready": False,
            },
            "deterministic_candidate_diagnostics_path": str(candidate_path),
            "generated_at": generated_at,
            "governance": {
                "same_source_engineering_rescore": True,
                "independent_validation": False,
                "ollama_calls": 0,
                "registry_mutated": False,
                "scientific_state_mutated": False,
                "historical_release_mutated": False,
                "csi_gateway_mutated": False,
                "may_create_human_authority": False,
                "production_scale_ready": False,
                "next_gate": "mixed-source calibration",
            },
        })

        summary = {
            "model": model,
            "semantic_model_field_matches": semantic_matches,
            "semantic_model_field_total": semantic_total,
            "semantic_model_field_accuracy": semantic_accuracy,
            "deterministic_field_matches": deterministic_matches,
            "deterministic_field_total": deterministic_total,
            "deterministic_field_accuracy": deterministic_accuracy,
            "hybrid_field_matches": hybrid_matches,
            "hybrid_field_total": total,
            "hybrid_field_accuracy": hybrid_accuracy,
            "span_reference_valid": reference_valid,
            "span_reference_attempted": reference_attempted,
            "span_reference_validity": reference_rate,
            "supported_field_matches": supported_matches,
            "supported_field_total": total,
            "supported_field_accuracy": supported_accuracy,
            "schema_valid": schema_valid,
            "passed": passed,
            "single_source_pipeline_candidate": single_source_candidate,
            "production_scale_ready": False,
            "result_path": str(result_path),
        }
        summaries.append(summary)

        print(f"model|{model}")
        print("model_inference_reused|1")
        print(
            f"semantic_model_field_accuracy|{semantic_matches}/{semantic_total}|"
            f"{semantic_accuracy:.3f}"
        )
        print(
            f"deterministic_field_accuracy|{deterministic_matches}/"
            f"{deterministic_total}|{deterministic_accuracy:.3f}"
        )
        print(
            f"hybrid_field_accuracy|{hybrid_matches}/{total}|"
            f"{hybrid_accuracy:.3f}"
        )
        print(
            f"span_reference_validity|{reference_valid}/{reference_attempted}|"
            f"{reference_rate:.3f}"
        )
        print(
            f"supported_field_accuracy|{supported_matches}/{total}|"
            f"{supported_accuracy:.3f}"
        )
        print(f"schema_valid|{int(schema_valid)}")

        for row in hybrid_results:
            if not row["match"]:
                print(
                    f"hybrid_field_mismatch|{row['field']}|"
                    f"expected={compact(row['expected'])}|"
                    f"observed={compact(row['observed'])}"
                )
        for row in support_checks:
            if row["value_correct"] and row["span_ids_valid"] and row["support_rule_valid"]:
                continue
            print(
                f"support_failure|{row['field']}|"
                f"value_correct={int(bool(row['value_correct']))}|"
                f"span_ids_valid={int(bool(row['span_ids_valid']))}|"
                f"support_rule_valid={int(bool(row['support_rule_valid']))}|"
                f"failed_groups={compact(row['failed_support_groups'])}|"
                f"ids={compact(row['evidence_span_ids'])}"
            )

        print(f"calibration_pass|{int(passed)}")
        print(f"single_source_pipeline_candidate|{int(single_source_candidate)}")
        print("production_scale_ready|0")
        print("next_gate|mixed-source calibration")

    summary_path = output_dir / "summary.json"
    v2.write_json(summary_path, {
        "schema_version": "stage13-local-calibration-summary-v4",
        "source_id": source_id,
        "profile_id": profile["profile_id"],
        "profile_path": str(profile_path),
        "profile_sha256": v1.sha256_file(profile_path),
        "base_profile_path": str(base_profile_path) if base_profile_path else None,
        "base_profile_sha256": (
            v1.sha256_file(base_profile_path) if base_profile_path else None
        ),
        "models": summaries,
        "generated_at": generated_at,
        "ollama_calls": 0,
        "registry_mutated": False,
        "scientific_state_mutated": False,
        "historical_release_mutated": False,
        "csi_gateway_mutated": False,
        "independent_validation": False,
        "production_scale_ready": False,
        "next_gate": "mixed-source calibration",
    })

    passed_models = [row["model"] for row in summaries if row["passed"]]
    candidates_out = [
        row["model"]
        for row in summaries
        if row["single_source_pipeline_candidate"]
    ]
    print("passed_models|" + ",".join(passed_models))
    print("single_source_pipeline_candidates|" + ",".join(candidates_out))
    print(f"summary_path|{summary_path}")
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print(
        "STAGE 13 LOCAL EXTRACTION CALIBRATION V4 RESCORE|"
        + ("PASS" if passed_models else "REVIEW")
    )
    return 0 if passed_models else 2


if __name__ == "__main__":
    raise SystemExit(main())
