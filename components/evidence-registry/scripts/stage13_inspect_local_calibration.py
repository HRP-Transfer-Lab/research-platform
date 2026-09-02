#!/usr/bin/env python3
"""Inspect Stage 13 local calibration errors without rerunning an LLM.

Reads the local calibration artefacts, prints field mismatches and diagnoses why
model-supplied quotation anchors failed. This script is read-only with respect to
PostgreSQL, the scientific Registry, releases and the CSI Gateway.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return value


def compact(value: Any, limit: int = 180) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def canonical_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = value.replace("ﬁ", "fi").replace("ﬂ", "fl")
    value = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", value)
    value = re.sub(r"[\u2010-\u2015]", "-", value)
    value = re.sub(r"[\u2018\u2019]", "'", value)
    value = re.sub(r"[\u201c\u201d]", '"', value)
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def word_windows(text: str, target_words: int) -> list[str]:
    words = canonical_text(text).split()
    if not words:
        return []
    width = max(4, min(len(words), target_words))
    if len(words) <= width:
        return [" ".join(words)]
    step = max(1, width // 4)
    windows = [" ".join(words[i : i + width]) for i in range(0, len(words) - width + 1, step)]
    if windows[-1] != " ".join(words[-width:]):
        windows.append(" ".join(words[-width:]))
    return windows


def closest_match(quote: str, pages: list[str], candidate_pages: list[int]) -> tuple[int | None, float, str]:
    target = canonical_text(quote)
    if not target:
        return None, 0.0, ""
    target_words = max(4, len(target.split()))
    best_page: int | None = None
    best_ratio = 0.0
    best_window = ""
    for page_no in candidate_pages:
        if not 1 <= page_no <= len(pages):
            continue
        for window in word_windows(pages[page_no - 1], target_words):
            ratio = difflib.SequenceMatcher(None, target, window, autojunk=False).ratio()
            if ratio > best_ratio:
                best_page = page_no
                best_ratio = ratio
                best_window = window
    return best_page, best_ratio, best_window


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect existing Stage 13 local calibration artefacts.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path.home()
        / "hrp-lab/source-corpus/rt-2026-014/manifests/stage13-local-calibration",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.expanduser().resolve()
    summary_path = input_dir / "summary.json"
    parse_path = input_dir / "parse-manifest.json"
    if not summary_path.is_file() or not parse_path.is_file():
        raise SystemExit(f"Calibration artefacts not found in {input_dir}")

    summary = load_json(summary_path)
    parse_manifest = load_json(parse_path)
    parsed_text_path = Path(str(parse_manifest["parsed_text_path"])).expanduser()
    if not parsed_text_path.is_file():
        raise SystemExit(f"Parsed text not found: {parsed_text_path}")
    pages = parsed_text_path.read_text(encoding="utf-8", errors="replace").split("\f")
    while pages and not pages[-1].strip():
        pages.pop()
    selected_pages = [int(value) for value in parse_manifest.get("selected_pdf_pages", [])]

    print("=== STAGE 13 LOCAL CALIBRATION DIAGNOSTICS ===")
    print(f"source_id|{summary.get('source_id', '')}")
    print("selected_pdf_pages|" + ",".join(str(value) for value in selected_pages))

    for model_summary in summary.get("models", []):
        result_path = Path(str(model_summary.get("result_path", ""))).expanduser()
        if not result_path.is_file():
            print(f"model|{model_summary.get('model', '')}")
            print(f"error|result file missing: {result_path}")
            continue
        result = load_json(result_path)
        extraction = result.get("extraction", {})
        validation = result.get("validation", {})

        print(f"model|{result.get('model', model_summary.get('model', ''))}")
        print(
            "field_score|"
            f"{validation.get('field_matches', 0)}/{validation.get('field_total', 0)}"
        )
        for item in validation.get("field_results", []):
            if item.get("match"):
                continue
            print(
                "field_mismatch|"
                f"{item.get('field_path', '')}|expected={compact(item.get('expected'))}"
                f"|observed={compact(item.get('observed'))}"
            )

        exact_count = 0
        canonical_count = 0
        close_count = 0
        for field, item in sorted(extraction.items()):
            if not isinstance(item, dict):
                continue
            page = item.get("pdf_page")
            quote = item.get("supporting_text", "")
            status = item.get("status")
            if status in {"not_reported", "unresolved"} and not quote:
                print(f"anchor|{field}|not_required")
                continue

            exact = False
            canonical = False
            if isinstance(page, int) and 1 <= page <= len(pages) and isinstance(quote, str):
                exact = re.sub(r"\s+", " ", quote).strip().casefold() in re.sub(
                    r"\s+", " ", pages[page - 1]
                ).strip().casefold()
                canonical = canonical_text(quote) in canonical_text(pages[page - 1])
            if exact:
                exact_count += 1
            if canonical:
                canonical_count += 1

            candidate_pages = selected_pages or list(range(1, len(pages) + 1))
            best_page, ratio, best_window = closest_match(str(quote), pages, candidate_pages)
            if ratio >= 0.90:
                close_count += 1
            print(
                "anchor|"
                f"{field}|reported_page={page}|exact={int(exact)}|canonical={int(canonical)}"
                f"|best_page={best_page}|similarity={ratio:.3f}"
                f"|quote={compact(quote, 140)}|closest={compact(best_window, 140)}"
            )

        print(f"anchor_exact_count|{exact_count}")
        print(f"anchor_canonical_count|{canonical_count}")
        print(f"anchor_similarity_ge_0.90_count|{close_count}")

    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
