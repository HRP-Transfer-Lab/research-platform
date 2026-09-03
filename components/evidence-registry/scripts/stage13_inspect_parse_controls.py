#!/usr/bin/env python3
"""Inspect control characters that triggered the Stage 13 parse-quality gate.

The parse-quality gate deliberately quarantines a document when ``pdftotext``
produces any C0 control character other than tab, newline, form feed or carriage
return. This utility identifies the exact code points and contexts so a later
normalisation step can be evidence-based rather than silently weakening the
quality gate.

The script is read-only. It does not rewrite parsed text or spans, call Ollama,
update PostgreSQL, create machine-screened state, or mutate releases/Gateway
state.
"""
from __future__ import annotations

import argparse
import json
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CORPUS_ROOT = Path.home() / "hrp-lab/source-corpus"
ALLOWED_C0 = {"\n", "\t", "\f", "\r"}
C0_NAMES = {
    0x00: "NULL",
    0x01: "START OF HEADING",
    0x02: "START OF TEXT",
    0x03: "END OF TEXT",
    0x04: "END OF TRANSMISSION",
    0x05: "ENQUIRY",
    0x06: "ACKNOWLEDGE",
    0x07: "BELL",
    0x08: "BACKSPACE",
    0x09: "CHARACTER TABULATION",
    0x0A: "LINE FEED",
    0x0B: "LINE TABULATION",
    0x0C: "FORM FEED",
    0x0D: "CARRIAGE RETURN",
    0x0E: "SHIFT OUT",
    0x0F: "SHIFT IN",
    0x10: "DATA LINK ESCAPE",
    0x11: "DEVICE CONTROL ONE",
    0x12: "DEVICE CONTROL TWO",
    0x13: "DEVICE CONTROL THREE",
    0x14: "DEVICE CONTROL FOUR",
    0x15: "NEGATIVE ACKNOWLEDGE",
    0x16: "SYNCHRONOUS IDLE",
    0x17: "END OF TRANSMISSION BLOCK",
    0x18: "CANCEL",
    0x19: "END OF MEDIUM",
    0x1A: "SUBSTITUTE",
    0x1B: "ESCAPE",
    0x1C: "INFORMATION SEPARATOR FOUR",
    0x1D: "INFORMATION SEPARATOR THREE",
    0x1E: "INFORMATION SEPARATOR TWO",
    0x1F: "INFORMATION SEPARATOR ONE",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def latest_batch(corpus_root: Path) -> Path:
    candidates = sorted(
        (corpus_root / "_parsing").glob("stage13-parse-quality-batch-*.json")
    )
    if not candidates:
        raise SystemExit(
            f"No Stage 13 parse-quality batch manifests under "
            f"{corpus_root / '_parsing'}"
        )
    return candidates[-1]


def is_unexpected_control(character: str) -> bool:
    return ord(character) < 32 and character not in ALLOWED_C0


def control_name(codepoint: int) -> str:
    return C0_NAMES.get(
        codepoint,
        unicodedata.name(chr(codepoint), "UNNAMED CONTROL"),
    )


def source_position(text: str, index: int) -> tuple[int, int]:
    page = text.count("\f", 0, index) + 1
    page_start = text.rfind("\f", 0, index) + 1
    line = text.count("\n", page_start, index) + 1
    return page, line


def escaped_context(text: str, index: int, radius: int) -> str:
    start = max(0, index - radius)
    end = min(len(text), index + radius + 1)
    fragment = text[start:end]
    return fragment.encode("unicode_escape", errors="backslashreplace").decode(
        "ascii"
    )


def inspect_text(text: str, *, context_radius: int, max_contexts: int) -> dict[str, Any]:
    occurrences: list[dict[str, Any]] = []
    counts: Counter[int] = Counter()
    pages_by_code: dict[int, set[int]] = defaultdict(set)
    inside_token_by_code: Counter[int] = Counter()
    contexts_by_code: Counter[int] = Counter()

    for index, character in enumerate(text):
        if not is_unexpected_control(character):
            continue
        codepoint = ord(character)
        previous = text[index - 1] if index > 0 else ""
        following = text[index + 1] if index + 1 < len(text) else ""
        inside_token = bool(
            previous
            and following
            and previous.isalnum()
            and following.isalnum()
        )
        page, line = source_position(text, index)
        counts[codepoint] += 1
        pages_by_code[codepoint].add(page)
        inside_token_by_code[codepoint] += int(inside_token)
        if contexts_by_code[codepoint] < max_contexts:
            occurrences.append(
                {
                    "codepoint": f"U+{codepoint:04X}",
                    "integer": codepoint,
                    "name": control_name(codepoint),
                    "character_index": index,
                    "pdf_page": page,
                    "page_line": line,
                    "inside_alphanumeric_token": inside_token,
                    "context": escaped_context(text, index, context_radius),
                }
            )
            contexts_by_code[codepoint] += 1

    codepoints = [
        {
            "codepoint": f"U+{codepoint:04X}",
            "integer": codepoint,
            "name": control_name(codepoint),
            "count": count,
            "pages": sorted(pages_by_code[codepoint]),
            "inside_alphanumeric_token_count": inside_token_by_code[codepoint],
        }
        for codepoint, count in sorted(counts.items())
    ]

    total = sum(counts.values())
    has_null = counts.get(0, 0) > 0
    inside_token = sum(inside_token_by_code.values())
    if total == 0:
        disposition = "no_unexpected_controls"
    elif has_null:
        disposition = "manual_reparse_required"
    elif inside_token > 0:
        disposition = "inspect_before_normalisation"
    else:
        disposition = "separator_normalisation_candidate"

    return {
        "unexpected_control_count": total,
        "distinct_control_codepoints": len(counts),
        "inside_alphanumeric_token_count": inside_token,
        "contains_null": has_null,
        "disposition": disposition,
        "codepoints": codepoints,
        "sample_occurrences": occurrences,
    }


def select_rows(
    batch: dict[str, Any], requested: set[str] | None
) -> list[dict[str, Any]]:
    rows = [row for row in batch.get("sources", []) if isinstance(row, dict)]
    if requested:
        selected = [
            row for row in rows if str(row.get("source_id")) in requested
        ]
        found = {str(row.get("source_id")) for row in selected}
        missing = sorted(requested - found)
        if missing:
            raise SystemExit(
                "Requested sources are absent from the batch: "
                + ", ".join(missing)
            )
        return selected
    return [
        row
        for row in rows
        if "unexpected_control_characters"
        in (row.get("quarantine_reasons") or [])
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect control characters in a Stage 13 parse-quality batch."
    )
    parser.add_argument("--batch-manifest", type=Path)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument("--source-id", action="append", dest="source_ids")
    parser.add_argument("--context-radius", type=int, default=60)
    parser.add_argument("--max-contexts", type=int, default=3)
    args = parser.parse_args()

    if args.context_radius < 1:
        raise SystemExit("--context-radius must be positive")
    if args.max_contexts < 1:
        raise SystemExit("--max-contexts must be positive")

    corpus_root = args.corpus_root.expanduser().resolve()
    batch_path = (
        args.batch_manifest.expanduser().resolve()
        if args.batch_manifest
        else latest_batch(corpus_root)
    )
    batch = load_json(batch_path)
    if batch.get("schema_version") != "stage13-parse-quality-batch-v1":
        raise SystemExit("Unsupported parse-quality batch schema")

    requested = set(args.source_ids) if args.source_ids else None
    rows = select_rows(batch, requested)
    if not rows:
        raise SystemExit("No control-character review sources selected")

    print("=== STAGE 13 PARSE CONTROL-CHARACTER DIAGNOSTICS ===")
    print(f"batch_manifest|{batch_path}")
    print(f"sources_selected|{len(rows)}")

    results: list[dict[str, Any]] = []
    for row in rows:
        source_id = str(row["source_id"])
        parsed_path = Path(str(row["parsed_text_path"])).expanduser().resolve()
        if not parsed_path.is_file():
            raise SystemExit(f"Parsed text missing for {source_id}: {parsed_path}")
        text = parsed_path.read_text(encoding="utf-8", errors="strict")
        diagnostic = inspect_text(
            text,
            context_radius=args.context_radius,
            max_contexts=args.max_contexts,
        )
        result = {
            "source_id": source_id,
            "parsed_text_path": str(parsed_path),
            **diagnostic,
        }
        results.append(result)
        print(
            f"source|{source_id}|unexpected_controls="
            f"{diagnostic['unexpected_control_count']}|distinct="
            f"{diagnostic['distinct_control_codepoints']}|inside_token="
            f"{diagnostic['inside_alphanumeric_token_count']}|contains_null="
            f"{int(diagnostic['contains_null'])}|disposition="
            f"{diagnostic['disposition']}"
        )
        for item in diagnostic["codepoints"]:
            print(
                f"control|{source_id}|{item['codepoint']}|"
                f"name={item['name']}|count={item['count']}|"
                f"inside_token={item['inside_alphanumeric_token_count']}|"
                f"pages={','.join(map(str, item['pages']))}"
            )
        for item in diagnostic["sample_occurrences"]:
            print(
                f"context|{source_id}|{item['codepoint']}|"
                f"page={item['pdf_page']}|line={item['page_line']}|"
                f"inside_token={int(item['inside_alphanumeric_token'])}|"
                f"text={json.dumps(item['context'])}"
            )

    output_path = (
        corpus_root
        / "_parsing"
        / f"stage13-parse-control-diagnostics-"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    )
    write_json(
        output_path,
        {
            "schema_version": "stage13-parse-control-diagnostics-v1",
            "source_batch_manifest": str(batch_path),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": results,
            "governance": {
                "parsed_text_rewritten": False,
                "spans_rewritten": False,
                "ollama_calls": 0,
                "registry_mutated": False,
                "scientific_state_mutated": False,
                "historical_release_mutated": False,
                "csi_gateway_mutated": False,
            },
        },
    )

    candidates = sum(
        1
        for result in results
        if result["disposition"] == "separator_normalisation_candidate"
    )
    manual = len(results) - candidates
    print(f"separator_normalisation_candidates|{candidates}")
    print(f"manual_or_context_review_required|{manual}")
    print(f"diagnostic_manifest|{output_path}")
    print("PARSED_TEXT_REWRITTEN|0")
    print("SPANS_REWRITTEN|0")
    print("OLLAMA_CALLS|0")
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    status = "NORMALISATION_CANDIDATES" if manual == 0 else "REVIEW"
    print(f"STAGE 13 PARSE CONTROL DIAGNOSTICS|{status}")
    return 0 if manual == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
