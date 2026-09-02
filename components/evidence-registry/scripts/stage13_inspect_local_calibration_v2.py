#!/usr/bin/env python3
"""Inspect Stage 13 V2 calibration artefacts without calling a model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return value


def load_spans(path: Path) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        output[str(row["span_id"])] = row
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect V2 local extraction calibration.")
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path.home() / "hrp-lab/source-corpus/rt-2026-014/manifests/stage13-local-calibration-v2",
    )
    args = parser.parse_args()
    root = args.dir.expanduser().resolve()
    summary = load_json(root / "summary.json")
    spans = load_spans(root / "spans.jsonl")

    print("=== STAGE 13 LOCAL CALIBRATION V2 DIAGNOSTICS ===")
    print(f"source_id|{summary.get('source_id')}")
    for model_summary in summary.get("models", []):
        model = str(model_summary["model"])
        result_path = Path(str(model_summary.get("result_path", "")))
        if not result_path.is_file():
            print(f"model|{model}")
            print(f"result_missing|{result_path}")
            if model_summary.get("error"):
                print(f"error|{model_summary['error']}")
            continue
        result = load_json(result_path)
        validation = result["validation"]
        print(f"model|{model}")
        print(
            f"model_field_score|{model_summary['model_field_matches']}/"
            f"{model_summary['field_total']}"
        )
        print(
            f"hybrid_field_score|{model_summary['hybrid_field_matches']}/"
            f"{model_summary['field_total']}"
        )
        print(
            "deterministic_overrides|"
            + ",".join(validation.get("deterministic_overrides", []))
        )

        for row in validation.get("model_field_results", []):
            if not row.get("match"):
                print(
                    f"model_field_mismatch|{row['field']}|"
                    f"expected={compact(row.get('expected'))}|"
                    f"observed={compact(row.get('observed'))}"
                )
        for row in validation.get("hybrid_field_results", []):
            if not row.get("match"):
                print(
                    f"hybrid_field_mismatch|{row['field']}|"
                    f"expected={compact(row.get('expected'))}|"
                    f"observed={compact(row.get('observed'))}"
                )

        for row in validation.get("span_reference_checks", []):
            if not row.get("valid"):
                print(
                    f"span_reference_failure|{row['field']}|"
                    f"reason={row.get('reason')}|ids={compact(row.get('ids'))}"
                )

        for row in validation.get("semantic_support_checks", []):
            if row.get("value_correct") and row.get("span_ids_valid") and row.get("support_rule_valid"):
                continue
            ids = row.get("evidence_span_ids", [])
            print(
                f"support_failure|{row['field']}|"
                f"value_correct={int(bool(row.get('value_correct')))}|"
                f"span_ids_valid={int(bool(row.get('span_ids_valid')))}|"
                f"support_rule_valid={int(bool(row.get('support_rule_valid')))}|"
                f"failed_groups={compact(row.get('failed_support_groups'))}|"
                f"ids={compact(ids)}"
            )
            for span_id in ids:
                span = spans.get(span_id)
                if not span:
                    continue
                text = " ".join(str(span.get("text", "")).split())
                print(
                    f"support_span|{row['field']}|{span_id}|"
                    f"page={span.get('pdf_page')}|text={compact(text[:420])}"
                )

    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
