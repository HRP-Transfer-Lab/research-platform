#!/usr/bin/env python3
"""Rescore frozen V2 model output with V3 deterministic participant-flow extraction.

This script makes no Ollama calls. It reuses the frozen semantic extraction from
Stage 13 V2, replaces explicitly machine-resolvable fields with deterministic
candidates, validates parser-owned evidence spans, and writes a separate V3
calibration result. PostgreSQL, scientific authority, releases and the CSI
Gateway are untouched.
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


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROFILE = (
    REPO_ROOT
    / "components/evidence-registry/config/stage13_calibration_rt014.v3.json"
)
DEFAULT_V2_DIR = (
    Path.home()
    / "hrp-lab/source-corpus/rt-2026-014/manifests/stage13-local-calibration-v2"
)
DEFAULT_MODELS = ("qwen3.5:4b",)


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_profile(path: Path) -> tuple[dict[str, Any], Path | None]:
    override = v1.load_json(path)
    base_name = override.get("base_profile")
    if not base_name:
        return override, None
    base_path = path.parent / str(base_name)
    base = v1.load_json(base_path)
    merged = {**base, **override}
    # Top-level V3 keys intentionally replace inherited V2 keys, while fields
    # not mentioned in V3 (gold, support_rules, deterministic_fields) remain.
    return merged, base_path


def load_spans(path: Path) -> list[v2.Span]:
    output: list[v2.Span] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        try:
            output.append(v2.Span(
                span_id=str(row["span_id"]),
                pdf_page=int(row["pdf_page"]),
                ordinal=int(row["ordinal"]),
                text=str(row["text"]),
                text_sha256=str(row["text_sha256"]),
            ))
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit(f"Invalid span row at {path}:{line_number}: {exc}") from exc
    if not output:
        raise SystemExit(f"No spans found in {path}")
    return output


def unresolved_field() -> dict[str, Any]:
    return {
        "value": None,
        "status": "unresolved",
        "evidence_span_ids": [],
        "confidence": 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rescore frozen V2 local extraction using V3 deterministic fields."
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
        else v2_dir.parent / "stage13-local-calibration-v3"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    profile, base_profile_path = load_profile(profile_path)
    source_id = str(profile["source_id"])
    spans_path = v2_dir / "spans.jsonl"
    if not spans_path.is_file():
        raise SystemExit(f"V2 span manifest not found: {spans_path}")
    spans = load_spans(spans_path)
    span_by_id = {span.span_id: span for span in spans}

    candidates, candidate_diagnostics = deterministic.extract_deterministic_candidates(
        spans, profile
    )
    deterministic_names = [str(value) for value in profile["deterministic_field_names"]]
    deterministic_extraction = {
        field: candidates.get(field, unresolved_field())
        for field in deterministic_names
    }

    generated_at = datetime.now(timezone.utc).isoformat()
    candidate_path = output_dir / "deterministic-candidates.json"
    v2.write_json(candidate_path, {
        "schema_version": "stage13-deterministic-candidates-v1",
        "source_id": source_id,
        "profile_id": profile["profile_id"],
        "candidates": deterministic_extraction,
        "diagnostics": candidate_diagnostics,
        "generated_at": generated_at,
    })

    print("=== STAGE 13 LOCAL EXTRACTION CALIBRATION V3 RESCORE ===")
    print(f"source_id|{source_id}")
    print("ollama_calls|0")
    print(f"parser_owned_spans|{len(spans)}")
    print("deterministic_fields|" + ",".join(deterministic_names))

    contextual = candidate_diagnostics.get("contextual_integer", {})
    for field in ("week1_platform_entrants", "delayed_assessment_completers"):
        diagnostic = contextual.get(field, {})
        for row in diagnostic.get("ranked_candidates", [])[:5]:
            print(
                f"candidate|{field}|rank={row['rank']}|value={row['value']}|"
                f"score={row['score']}|page={row['pdf_page']}|span={row['span_id']}"
            )
        selected = diagnostic.get("selected_value")
        print(
            f"deterministic_selected|{field}|"
            f"value={'' if selected is None else selected}|"
            f"score={diagnostic.get('selected_score')}|"
            f"margin={diagnostic.get('score_margin')}"
        )

    for guard in candidate_diagnostics.get("cross_field_guards", []):
        print(
            f"cross_field_guard|{guard['guard']}|valid={int(bool(guard['valid']))}|"
            f"entrants={guard['week1_platform_entrants']}|"
            f"completers={guard['delayed_assessment_completers']}"
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
            field: full_v2_model_extraction.get(field, unresolved_field())
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

        total = len(gold)
        semantic_accuracy = semantic_matches / len(semantic_gold) if semantic_gold else 1.0
        deterministic_accuracy = (
            deterministic_matches / len(deterministic_gold)
            if deterministic_gold else 1.0
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
            and hybrid_accuracy >= float(thresholds["minimum_hybrid_field_accuracy"])
            and reference_rate >= float(thresholds["minimum_span_reference_validity"])
            and supported_accuracy >= float(thresholds["minimum_supported_field_accuracy"])
        )
        workhorse_candidate = (
            schema_valid
            and hybrid_accuracy
            >= float(thresholds["automatic_workhorse_candidate_hybrid_field_accuracy"])
            and reference_rate
            >= float(thresholds["automatic_workhorse_candidate_span_reference_validity"])
            and supported_accuracy
            >= float(thresholds["automatic_workhorse_candidate_supported_field_accuracy"])
        )

        result_path = output_dir / f"{v1.model_filename(model)}.v3-rescore.json"
        result = {
            "schema_version": "stage13-local-calibration-result-v3",
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
                "single_source_workhorse_candidate": workhorse_candidate,
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
            },
        }
        v2.write_json(result_path, result)

        summary = {
            "model": model,
            "semantic_model_field_matches": semantic_matches,
            "semantic_model_field_total": len(semantic_gold),
            "semantic_model_field_accuracy": semantic_accuracy,
            "deterministic_field_matches": deterministic_matches,
            "deterministic_field_total": len(deterministic_gold),
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
            "single_source_workhorse_candidate": workhorse_candidate,
            "result_path": str(result_path),
        }
        summaries.append(summary)

        print(f"model|{model}")
        print("model_inference_reused|1")
        print(
            f"semantic_model_field_accuracy|{semantic_matches}/"
            f"{len(semantic_gold)}|{semantic_accuracy:.3f}"
        )
        print(
            f"deterministic_field_accuracy|{deterministic_matches}/"
            f"{len(deterministic_gold)}|{deterministic_accuracy:.3f}"
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
        print(f"single_source_workhorse_candidate|{int(workhorse_candidate)}")

    summary_path = output_dir / "summary.json"
    v2.write_json(summary_path, {
        "schema_version": "stage13-local-calibration-summary-v3",
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
    })

    passed_models = [row["model"] for row in summaries if row["passed"]]
    workhorse_candidates = [
        row["model"]
        for row in summaries
        if row["single_source_workhorse_candidate"]
    ]
    print("passed_models|" + ",".join(passed_models))
    print("single_source_workhorse_candidates|" + ",".join(workhorse_candidates))
    print(f"summary_path|{summary_path}")
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print(
        "STAGE 13 LOCAL EXTRACTION CALIBRATION V3 RESCORE|"
        + ("PASS" if passed_models else "REVIEW")
    )
    return 0 if passed_models else 2


if __name__ == "__main__":
    raise SystemExit(main())
