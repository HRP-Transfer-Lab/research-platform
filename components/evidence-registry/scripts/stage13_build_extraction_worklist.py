#!/usr/bin/env python3
"""Build the canonical Stage 13 mixed-source extraction worklist.

Combines the parse-quality batch with any successful parse-control repair batch,
validates the selected parsed text and parser-owned span manifests, attaches
release-record metadata, and writes one immutable local worklist for the
mixed-source model calibration.

This script makes no Ollama calls and mutates no PostgreSQL, scientific,
release, Gateway, or machine-screened state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RECORDS_DIR = (
    REPO_ROOT
    / "components/evidence-registry/data/releases/2026-08-23/records"
)
DEFAULT_CORPUS_ROOT = Path.home() / "hrp-lab/source-corpus"
ALLOWED_C0 = {"\n", "\t", "\f", "\r"}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def latest(corpus_root: Path, pattern: str) -> Path:
    candidates = sorted((corpus_root / "_parsing").glob(pattern))
    if not candidates:
        raise SystemExit(
            f"No file matching {pattern!r} under {corpus_root / '_parsing'}"
        )
    return candidates[-1]


def source_family(source_kind: str) -> str:
    mapping = {
        "systematic_review_meta_analysis": "evidence_synthesis_meta_analysis",
        "systematic_review": "evidence_synthesis_systematic_review",
        "scoping_review": "evidence_synthesis_scoping_review",
        "meta_analysis": "evidence_synthesis_meta_analysis",
    }
    return mapping.get(source_kind, "primary_empirical")


def unexpected_controls(text: str) -> list[str]:
    return sorted(
        {
            f"U+{ord(character):04X}"
            for character in text
            if ord(character) < 32 and character not in ALLOWED_C0
        }
    )


def parsed_page_count(text: str) -> int:
    pages = text.split("\f")
    while pages and not pages[-1].strip():
        pages.pop()
    return len(pages)


def load_and_validate_spans(path: Path, *, page_count: int) -> tuple[int, list[str]]:
    seen: set[str] = set()
    errors: list[str] = []
    count = 0
    try:
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    except FileNotFoundError as exc:
        raise RuntimeError(f"Span manifest missing: {path}") from exc

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        count += 1
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line_{line_number}:invalid_json:{exc.msg}")
            continue
        if not isinstance(row, dict):
            errors.append(f"line_{line_number}:not_object")
            continue
        span_id = row.get("span_id")
        text = row.get("text")
        text_hash = row.get("text_sha256")
        page = row.get("pdf_page")
        if not isinstance(span_id, str) or not span_id:
            errors.append(f"line_{line_number}:bad_span_id")
        elif span_id in seen:
            errors.append(f"line_{line_number}:duplicate_span_id:{span_id}")
        else:
            seen.add(span_id)
        if not isinstance(text, str) or not text.strip():
            errors.append(f"line_{line_number}:bad_text")
        elif not isinstance(text_hash, str) or sha256_bytes(
            text.encode("utf-8")
        ) != text_hash:
            errors.append(f"line_{line_number}:text_hash_mismatch")
        if (
            not isinstance(page, int)
            or isinstance(page, bool)
            or page < 1
            or page > page_count
        ):
            errors.append(f"line_{line_number}:bad_pdf_page:{page!r}")

    if count == 0:
        errors.append("no_spans")
    return count, errors


def release_records(records_dir: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(records_dir.glob("*.json")):
        record = load_json(path)
        source_id = str(record.get("record_id") or path.stem)
        records[source_id] = record
    return records


def repair_by_source(repair_batch: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = repair_batch.get("sources")
    if not isinstance(rows, list):
        raise SystemExit("Repair batch must contain sources[]")
    return {
        str(row["source_id"]): row
        for row in rows
        if isinstance(row, dict) and row.get("source_id")
    }


def select_derivative(
    parse_row: dict[str, Any],
    repair_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_id = str(parse_row["source_id"])
    if parse_row.get("extraction_eligible") is True:
        return {
            "derivative_kind": "raw_parse",
            "parsed_text_path": parse_row["parsed_text_path"],
            "span_manifest_path": parse_row["span_manifest_path"],
            "repair_manifest_path": None,
            "expected_page_count": int(
                (parse_row.get("metrics") or {}).get("parsed_page_count") or 0
            ),
            "expected_span_count": int(
                (parse_row.get("metrics") or {}).get("span_count") or 0
            ),
        }

    repair = repair_rows.get(source_id)
    if not repair or repair.get("extraction_eligible_after_repair") is not True:
        raise RuntimeError(
            f"{source_id}: source is neither parse-eligible nor successfully repaired"
        )
    return {
        "derivative_kind": "canonical_repair",
        "parsed_text_path": repair["canonical_text_path"],
        "span_manifest_path": repair["canonical_span_manifest_path"],
        "repair_manifest_path": repair.get("source_manifest_path"),
        "expected_page_count": int(repair.get("canonical_page_count") or 0),
        "expected_span_count": int(repair.get("canonical_span_count") or 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a validated mixed-source extraction worklist."
    )
    parser.add_argument("--parse-batch", type=Path)
    parser.add_argument("--repair-batch", type=Path)
    parser.add_argument("--records-dir", type=Path, default=DEFAULT_RECORDS_DIR)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument("--source-id", action="append", dest="source_ids")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    corpus_root = args.corpus_root.expanduser().resolve()
    parse_path = (
        args.parse_batch.expanduser().resolve()
        if args.parse_batch
        else latest(corpus_root, "stage13-parse-quality-batch-*.json")
    )
    repair_path = (
        args.repair_batch.expanduser().resolve()
        if args.repair_batch
        else latest(corpus_root, "stage13-parse-control-repair-*.json")
    )
    records_dir = args.records_dir.expanduser().resolve()
    parse_batch = load_json(parse_path)
    repair_batch = load_json(repair_path)
    if parse_batch.get("schema_version") != "stage13-parse-quality-batch-v1":
        raise SystemExit("Unsupported parse-batch schema")
    if (
        repair_batch.get("schema_version")
        != "stage13-parse-control-repair-batch-v1"
    ):
        raise SystemExit("Unsupported repair-batch schema")

    rows = [
        row
        for row in parse_batch.get("sources", [])
        if isinstance(row, dict) and row.get("source_id")
    ]
    requested = set(args.source_ids) if args.source_ids else None
    if requested:
        rows = [row for row in rows if str(row["source_id"]) in requested]
        found = {str(row["source_id"]) for row in rows}
        missing = sorted(requested - found)
        if missing:
            raise SystemExit(
                "Requested sources are absent from parse batch: "
                + ", ".join(missing)
            )
    if not rows:
        raise SystemExit("No parse-batch sources selected")

    repairs = repair_by_source(repair_batch)
    records = release_records(records_dir)
    output_rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    print("=== STAGE 13 EXTRACTION WORKLIST ===")
    print(f"parse_batch|{parse_path}")
    print(f"repair_batch|{repair_path}")
    print(f"sources_selected|{len(rows)}")

    for row in rows:
        source_id = str(row["source_id"])
        try:
            derivative = select_derivative(row, repairs)
            text_path = Path(
                str(derivative["parsed_text_path"])
            ).expanduser().resolve()
            spans_path = Path(
                str(derivative["span_manifest_path"])
            ).expanduser().resolve()
            if not text_path.is_file():
                raise RuntimeError(f"parsed text missing: {text_path}")
            if not spans_path.is_file():
                raise RuntimeError(f"span manifest missing: {spans_path}")

            text = text_path.read_text(encoding="utf-8", errors="strict")
            controls = unexpected_controls(text)
            if controls:
                raise RuntimeError(
                    "unexpected control characters remain: " + ",".join(controls)
                )
            pages = parsed_page_count(text)
            expected_pages = int(derivative["expected_page_count"])
            if pages != expected_pages:
                raise RuntimeError(
                    f"page count mismatch: expected {expected_pages}; found {pages}"
                )
            span_count, span_errors = load_and_validate_spans(
                spans_path, page_count=pages
            )
            if span_errors:
                raise RuntimeError("span validation: " + ";".join(span_errors))
            expected_spans = int(derivative["expected_span_count"])
            if span_count != expected_spans:
                raise RuntimeError(
                    f"span count mismatch: expected {expected_spans}; found {span_count}"
                )

            record = records.get(source_id)
            if not record:
                raise RuntimeError("release record missing")
            bibliography = record.get("bibliography") or {}
            review = record.get("review") or {}
            parse_manifest_path = Path(
                str(row["parse_quality_manifest"])
            ).expanduser().resolve()
            parse_manifest = load_json(parse_manifest_path)
            if parse_manifest.get("source_id") != source_id:
                raise RuntimeError("parse-quality manifest source mismatch")

            output_rows.append(
                {
                    "source_id": source_id,
                    "source_version_id": parse_manifest.get("source_version_id"),
                    "title": bibliography.get("title"),
                    "authors": bibliography.get("authors"),
                    "year": bibliography.get("year"),
                    "venue": bibliography.get("venue"),
                    "doi": bibliography.get("doi"),
                    "source_kind": bibliography.get("source_kind"),
                    "source_family": source_family(
                        str(bibliography.get("source_kind") or "")
                    ),
                    "peer_review_status": bibliography.get(
                        "peer_review_status"
                    ),
                    "review_bucket": record.get("review_bucket"),
                    "derivative_kind": derivative["derivative_kind"],
                    "parsed_text_path": str(text_path),
                    "parsed_text_sha256": sha256_file(text_path),
                    "span_manifest_path": str(spans_path),
                    "span_manifest_sha256": sha256_file(spans_path),
                    "page_count": pages,
                    "span_count": span_count,
                    "parse_quality_manifest": str(parse_manifest_path),
                    "repair_manifest_path": derivative[
                        "repair_manifest_path"
                    ],
                    "legacy_reference": {
                        "release_id": record.get("release_id"),
                        "review_status": review.get("review_status"),
                        "method_extraction_status": review.get(
                            "method_extraction_status"
                        ),
                        "primary_classification": review.get(
                            "primary_classification"
                        ),
                        "evidence_rungs": review.get("evidence_rungs") or [],
                        "record_path": str(
                            records_dir / f"{source_id}.json"
                        ),
                    },
                }
            )
            print(
                f"source_worklisted|{source_id}|"
                f"family={output_rows[-1]['source_family']}|"
                f"derivative={derivative['derivative_kind']}|"
                f"pages={pages}|spans={span_count}|controls=0"
            )
        except Exception as exc:
            failures.append({"source_id": source_id, "error": str(exc)})
            print(f"source_blocked|{source_id}|{exc}")

    timestamp = datetime.now(timezone.utc)
    output_path = (
        args.output.expanduser().resolve()
        if args.output
        else corpus_root
        / "_extraction"
        / (
            "stage13-mixed-source-worklist-"
            f"{timestamp.strftime('%Y%m%d-%H%M%S')}.json"
        )
    )
    payload = {
        "schema_version": "stage13-mixed-source-worklist-v1",
        "generated_at": timestamp.isoformat(),
        "parse_batch_path": str(parse_path),
        "parse_batch_sha256": sha256_file(parse_path),
        "repair_batch_path": str(repair_path),
        "repair_batch_sha256": sha256_file(repair_path),
        "records_dir": str(records_dir),
        "summary": {
            "selected": len(rows),
            "ready": len(output_rows),
            "blocked": len(failures),
            "primary_empirical": sum(
                1
                for row in output_rows
                if row["source_family"] == "primary_empirical"
            ),
            "evidence_synthesis": sum(
                1
                for row in output_rows
                if row["source_family"] != "primary_empirical"
            ),
            "canonical_repair": sum(
                1
                for row in output_rows
                if row["derivative_kind"] == "canonical_repair"
            ),
        },
        "sources": output_rows,
        "blocked_sources": failures,
        "governance": {
            "ollama_calls": 0,
            "registry_mutated": False,
            "scientific_state_mutated": False,
            "historical_release_mutated": False,
            "csi_gateway_mutated": False,
            "machine_screened_status_created": False,
            "human_authority_created": False,
        },
    }
    write_json(output_path, payload)

    print(f"worklist_ready|{len(output_rows)}")
    print(f"worklist_blocked|{len(failures)}")
    print(
        "primary_empirical|"
        f"{payload['summary']['primary_empirical']}"
    )
    print(
        "evidence_synthesis|"
        f"{payload['summary']['evidence_synthesis']}"
    )
    print(
        "canonical_repair_sources|"
        f"{payload['summary']['canonical_repair']}"
    )
    print(f"worklist_path|{output_path}")
    print("OLLAMA_CALLS|0")
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print("MACHINE_SCREENED_STATUS_CREATED|0")

    status = "PASS" if not failures and len(output_rows) == len(rows) else "REVIEW"
    print(f"STAGE 13 EXTRACTION WORKLIST|{status}")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
