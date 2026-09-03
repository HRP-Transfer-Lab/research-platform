#!/usr/bin/env python3
"""Parse and quality-gate verified local full-text PDFs for Stage 13.

This script is deliberately local-manifest-only. It reads the operational
source-acquisition inventory, verifies each registered local PDF against its
stored hash and page count, creates page-preserving text and parser-owned spans,
and routes each document to extraction eligibility or quarantine.

It makes no Ollama calls and does not alter scientific authority, the immutable
historical release, the approved CSI Gateway, or machine-screened state.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import register_source_document as registry
import stage13_acquire_oa_calibration_set as acquisition
import stage13_calibrate_local_extraction as common
import stage13_calibrate_local_extraction_v2 as spanlib

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY = (
    REPO_ROOT
    / "components/evidence-registry/config/stage13_parse_quality_policy.v1.json"
)
DEFAULT_CORPUS_ROOT = Path.home() / "hrp-lab/source-corpus"
DEFAULT_CONTAINER = "supabase_db_research-platform"


def load_policy(path: Path) -> dict[str, Any]:
    policy = common.load_json(path)
    if policy.get("schema_version") != "stage13-parse-quality-policy-v1":
        raise SystemExit("Unsupported parse-quality policy schema")
    return policy


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def database_is_ready(container: str) -> None:
    running = registry.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", container],
        capture=True,
    ).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {container!r} is not running")
    architecture = registry.psql(
        container,
        "select to_regclass('public.source_document_artifact') is not null;",
        capture=True,
    )
    if architecture != "t":
        raise SystemExit("Source-acquisition architecture is not installed")


def verified_local_sources(container: str) -> list[dict[str, Any]]:
    """Return one latest verified local full-text artifact per source."""
    raw = registry.psql(
        container,
        """
select json_build_object(
  'source_id', d.source_id,
  'source_version_id', d.source_version_id,
  'title', d.title,
  'doi', d.doi,
  'source_kind', d.source_kind,
  'artifact_id', a.source_document_artifact_id,
  'storage_locator', a.storage_locator,
  'content_sha256', a.content_sha256,
  'page_count', a.page_count,
  'filename', a.filename,
  'access_route', a.access_route,
  'license_status', a.license_status,
  'verified_at', a.verified_at
)::text
from public.v_source_acquisition_dashboard d
join lateral (
  select sda.*
  from public.source_document_artifact sda
  where sda.source_version_id=d.source_version_id
    and sda.artifact_kind='full_text'
    and sda.artifact_status='verified'
    and sda.storage_backend='local_corpus'
    and sda.storage_locator is not null
  order by sda.verified_at desc nulls last,
           sda.source_document_artifact_id desc
  limit 1
) a on true
where d.fulltext_verified=true
order by d.source_id;
""",
        capture=True,
    )
    rows: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise RuntimeError("Expected JSON object from acquisition query")
        rows.append(value)
    return rows


def select_sources(
    rows: list[dict[str, Any]], requested: set[str] | None
) -> list[dict[str, Any]]:
    if not requested:
        return rows
    selected = [row for row in rows if str(row.get("source_id")) in requested]
    found = {str(row.get("source_id")) for row in selected}
    missing = sorted(requested - found)
    if missing:
        raise SystemExit(
            "Requested sources are not verified local full texts: "
            + ", ".join(missing)
        )
    return selected


def pdf_information(path: Path) -> dict[str, str]:
    executable = shutil.which("pdfinfo")
    if not executable:
        raise RuntimeError("pdfinfo is required (install poppler-utils)")
    result = subprocess.run(
        [executable, str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdfinfo failed: {result.stderr.strip()}")
    output: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        output[key.strip()] = value.strip()
    return output


def parse_pdf(path: Path, output_path: Path) -> tuple[list[str], str]:
    executable = shutil.which("pdftotext")
    if not executable:
        raise RuntimeError("pdftotext is required (install poppler-utils)")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            executable,
            "-layout",
            "-enc",
            "UTF-8",
            str(path),
            str(output_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdftotext failed: {result.stderr.strip()}")
    text = output_path.read_text(encoding="utf-8", errors="replace")
    pages = text.split("\f")
    while pages and not pages[-1].strip():
        pages.pop()
    return pages, result.stderr.strip()


def visible_character_count(text: str) -> int:
    return sum(1 for character in text if not character.isspace())


def parse_metrics(
    *,
    pages: list[str],
    full_text: str,
    spans: list[spanlib.Span],
    minimum_page_characters: int,
) -> dict[str, Any]:
    page_characters = [len(re.sub(r"\s+", " ", page).strip()) for page in pages]
    nonempty = sum(1 for count in page_characters if count > 0)
    low_text = sum(1 for count in page_characters if count < minimum_page_characters)
    total = len(full_text)
    visible = visible_character_count(full_text)
    alphabetic = sum(1 for character in full_text if character.isalpha())
    replacement = full_text.count("\ufffd")
    control = sum(
        1
        for character in full_text
        if ord(character) < 32 and character not in "\n\t\f\r"
    )
    span_lengths = [len(span.text) for span in spans]
    return {
        "parsed_page_count": len(pages),
        "nonempty_page_count": nonempty,
        "nonempty_page_ratio": nonempty / len(pages) if pages else 0.0,
        "low_text_page_count": low_text,
        "low_text_page_ratio": low_text / len(pages) if pages else 1.0,
        "total_text_characters": total,
        "visible_characters": visible,
        "median_page_characters": statistics.median(page_characters)
        if page_characters
        else 0,
        "minimum_page_characters_observed": min(page_characters)
        if page_characters
        else 0,
        "maximum_page_characters_observed": max(page_characters)
        if page_characters
        else 0,
        "alphabetic_character_ratio": alphabetic / visible if visible else 0.0,
        "replacement_character_count": replacement,
        "replacement_character_rate": replacement / total if total else 1.0,
        "unexpected_control_character_count": control,
        "span_count": len(spans),
        "median_span_characters": statistics.median(span_lengths)
        if span_lengths
        else 0,
        "maximum_span_characters": max(span_lengths) if span_lengths else 0,
    }


def assess_quality(
    *,
    metrics: dict[str, Any],
    checks: dict[str, Any],
    pdf_info: dict[str, str],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Apply hard integrity checks and softer parse-quality thresholds."""
    thresholds = policy["thresholds"]
    failures: list[str] = []
    reviews: list[str] = []

    if thresholds.get("require_database_hash_match", True) and not checks.get(
        "database_hash_match", False
    ):
        failures.append("database_hash_mismatch")
    if thresholds.get("require_database_page_count_match", True) and not checks.get(
        "database_page_count_match", False
    ):
        failures.append("database_page_count_mismatch")
    if thresholds.get("require_physical_page_alignment", True) and not checks.get(
        "physical_page_alignment", False
    ):
        failures.append("physical_page_alignment_failed")

    if thresholds.get("require_identity_match_for_admission", True) and not checks.get(
        "identity_match", False
    ):
        reviews.append("parsed_identity_not_confirmed")

    if metrics["nonempty_page_ratio"] < float(
        thresholds["minimum_nonempty_page_ratio"]
    ):
        reviews.append("low_nonempty_page_ratio")
    if metrics["low_text_page_ratio"] > float(
        thresholds["maximum_low_text_page_ratio"]
    ):
        reviews.append("too_many_low_text_pages")
    if metrics["total_text_characters"] < int(
        thresholds["minimum_total_text_characters"]
    ):
        reviews.append("insufficient_total_text")
    if metrics["median_page_characters"] < int(
        thresholds["minimum_median_page_characters"]
    ):
        reviews.append("low_median_page_text")
    if metrics["replacement_character_rate"] > float(
        thresholds["maximum_replacement_character_rate"]
    ):
        reviews.append("high_replacement_character_rate")
    if metrics["alphabetic_character_ratio"] < float(
        thresholds["minimum_alphabetic_character_ratio"]
    ):
        reviews.append("low_alphabetic_character_ratio")
    if metrics["unexpected_control_character_count"] > 0:
        reviews.append("unexpected_control_characters")
    if pdf_info.get("Encrypted", "no").casefold().startswith("yes"):
        reviews.append("encrypted_pdf")
    if metrics["span_count"] == 0:
        failures.append("no_parser_owned_spans")

    if failures:
        status = "fail"
    elif reviews:
        status = "review"
    else:
        status = "pass"

    ocr_candidate = (
        metrics["nonempty_page_ratio"] < 0.5
        or metrics["median_page_characters"] < 80
    )
    return {
        "status": status,
        "extraction_eligible": status == "pass",
        "failure_reasons": failures,
        "review_reasons": reviews,
        "quarantine_reasons": failures + reviews,
        "ocr_candidate": ocr_candidate,
        "parser_fallback_candidate": status != "pass",
    }


def source_output_paths(
    source_id: str, pdf: Path, corpus_root: Path
) -> dict[str, Path]:
    source_root = corpus_root / source_id
    manifest_root = source_root / "manifests" / "stage13-parse-quality"
    return {
        "parsed_text": source_root / "parsed" / f"{pdf.stem}.layout.txt",
        "manifest_root": manifest_root,
        "spans": manifest_root / "spans.jsonl",
        "parse_quality": manifest_root / "parse-quality.json",
    }


def process_source(
    *,
    row: dict[str, Any],
    corpus_root: Path,
    policy: dict[str, Any],
) -> dict[str, Any]:
    source_id = str(row["source_id"])
    pdf = Path(str(row["storage_locator"])).expanduser().resolve()
    paths = source_output_paths(source_id, pdf, corpus_root)
    started_at = datetime.now(timezone.utc).isoformat()

    if not pdf.is_file():
        raise RuntimeError(f"registered local PDF is missing: {pdf}")

    observed_hash = common.sha256_file(pdf)
    expected_hash = str(row.get("content_sha256") or "")
    info = pdf_information(pdf)
    observed_pages = int(info.get("Pages", "0") or 0)
    expected_pages = int(row.get("page_count") or 0)
    pages, parser_stderr = parse_pdf(pdf, paths["parsed_text"])
    full_text = paths["parsed_text"].read_text(
        encoding="utf-8", errors="replace"
    )
    spans = spanlib.build_spans(pages, policy.get("span_generation", {}))

    paths["manifest_root"].mkdir(parents=True, exist_ok=True)
    with paths["spans"].open("w", encoding="utf-8") as handle:
        for span in spans:
            handle.write(
                common.canonical_json(
                    {
                        "span_id": span.span_id,
                        "pdf_page": span.pdf_page,
                        "ordinal": span.ordinal,
                        "text": span.text,
                        "text_sha256": span.text_sha256,
                    }
                )
                + "\n"
            )

    identity_text = "\n".join(
        pages[: min(int(policy.get("identity_pages", 8)), len(pages))]
    )
    identity = acquisition.identity_check(
        text=identity_text,
        expected_title=str(row.get("title") or ""),
        expected_doi=str(row.get("doi")) if row.get("doi") else None,
        minimum_title_coverage=0.60,
    )
    metrics = parse_metrics(
        pages=pages,
        full_text=full_text,
        spans=spans,
        minimum_page_characters=int(policy.get("minimum_page_characters", 80)),
    )
    checks = {
        "database_hash_match": bool(expected_hash and observed_hash == expected_hash),
        "database_page_count_match": bool(
            expected_pages and observed_pages == expected_pages
        ),
        "physical_page_alignment": observed_pages == len(pages),
        "identity_match": bool(identity["passed"]),
    }
    quality = assess_quality(
        metrics=metrics,
        checks=checks,
        pdf_info=info,
        policy=policy,
    )

    result = {
        "schema_version": "stage13-parse-quality-result-v1",
        "source_id": source_id,
        "source_version_id": row.get("source_version_id"),
        "title": row.get("title"),
        "doi": row.get("doi"),
        "source_kind": row.get("source_kind"),
        "artifact": {
            "source_document_artifact_id": row.get("artifact_id"),
            "path": str(pdf),
            "filename": pdf.name,
            "database_sha256": expected_hash,
            "observed_sha256": observed_hash,
            "database_page_count": expected_pages,
            "observed_page_count": observed_pages,
            "access_route": row.get("access_route"),
            "license_status": row.get("license_status"),
        },
        "parse": {
            "parser": "poppler-pdftotext-layout",
            "parser_version": info.get("PDF version"),
            "parsed_text_path": str(paths["parsed_text"]),
            "parsed_text_sha256": common.sha256_file(paths["parsed_text"]),
            "span_manifest_path": str(paths["spans"]),
            "parser_stderr": parser_stderr,
            "pdfinfo": info,
        },
        "identity": identity,
        "checks": checks,
        "metrics": metrics,
        "quality": quality,
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
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
    write_json(paths["parse_quality"], result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse and quality-gate verified Stage 13 local PDFs."
    )
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--source-id", action="append", dest="source_ids")
    args = parser.parse_args()

    corpus_root = args.corpus_root.expanduser().resolve()
    policy_path = args.policy.expanduser().resolve()
    policy = load_policy(policy_path)
    database_is_ready(args.container)
    requested = set(args.source_ids) if args.source_ids else None
    rows = select_sources(verified_local_sources(args.container), requested)
    if not rows:
        raise SystemExit("No verified local full-text artifacts selected")

    print("=== STAGE 13 MIXED-SOURCE PARSE QUALITY ===")
    print("mode|LOCAL_MANIFEST_ONLY")
    print(f"policy|{policy_path}")
    print(f"verified_sources_selected|{len(rows)}")

    results: list[dict[str, Any]] = []
    fatal_errors: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        source_id = str(row["source_id"])
        print(f"source_start|{index}/{len(rows)}|{source_id}", flush=True)
        try:
            result = process_source(
                row=row,
                corpus_root=corpus_root,
                policy=policy,
            )
            results.append(result)
            metrics = result["metrics"]
            quality = result["quality"]
            checks = result["checks"]
            print(
                f"source_parsed|{source_id}|status={quality['status']}|"
                f"pages={metrics['parsed_page_count']}|"
                f"spans={metrics['span_count']}|"
                f"text_chars={metrics['total_text_characters']}|"
                f"nonempty_page_ratio={metrics['nonempty_page_ratio']:.3f}|"
                f"identity={int(checks['identity_match'])}|"
                f"hash={int(checks['database_hash_match'])}|"
                f"page_alignment={int(checks['physical_page_alignment'])}"
            )
            for reason in quality["quarantine_reasons"]:
                print(f"source_quality_flag|{source_id}|{reason}")
        except Exception as exc:
            fatal_errors.append({"source_id": source_id, "error": str(exc)})
            print(f"source_error|{source_id}|{exc}")

    pass_count = sum(
        1 for result in results if result["quality"]["status"] == "pass"
    )
    review_count = sum(
        1 for result in results if result["quality"]["status"] == "review"
    )
    fail_count = sum(
        1 for result in results if result["quality"]["status"] == "fail"
    )
    eligible = sum(
        1 for result in results if result["quality"]["extraction_eligible"]
    )
    quarantined = len(results) - eligible + len(fatal_errors)
    generated_at = datetime.now(timezone.utc)
    batch_path = (
        corpus_root
        / "_parsing"
        / f"stage13-parse-quality-batch-{generated_at.strftime('%Y%m%d-%H%M%S')}.json"
    )
    batch = {
        "schema_version": "stage13-parse-quality-batch-v1",
        "policy_id": policy.get("policy_id"),
        "policy_path": str(policy_path),
        "policy_sha256": common.sha256_file(policy_path),
        "generated_at": generated_at.isoformat(),
        "summary": {
            "selected": len(rows),
            "processed": len(results),
            "pass": pass_count,
            "review": review_count,
            "fail": fail_count,
            "fatal_errors": len(fatal_errors),
            "extraction_eligible": eligible,
            "quarantined": quarantined,
        },
        "sources": [
            {
                "source_id": result["source_id"],
                "source_kind": result.get("source_kind"),
                "status": result["quality"]["status"],
                "extraction_eligible": result["quality"]["extraction_eligible"],
                "quarantine_reasons": result["quality"]["quarantine_reasons"],
                "parse_quality_manifest": str(
                    source_output_paths(
                        result["source_id"],
                        Path(result["artifact"]["path"]),
                        corpus_root,
                    )["parse_quality"]
                ),
                "parsed_text_path": result["parse"]["parsed_text_path"],
                "span_manifest_path": result["parse"]["span_manifest_path"],
                "metrics": result["metrics"],
            }
            for result in results
        ],
        "fatal_errors": fatal_errors,
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
    write_json(batch_path, batch)

    print(f"parse_pass|{pass_count}")
    print(f"parse_review|{review_count}")
    print(f"parse_fail|{fail_count}")
    print(f"fatal_errors|{len(fatal_errors)}")
    print(f"extraction_eligible|{eligible}")
    print(f"quarantined|{quarantined}")
    print(f"batch_manifest|{batch_path}")
    print("OLLAMA_CALLS|0")
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")

    if eligible == len(rows) and not fatal_errors:
        status = "PASS"
        exit_code = 0
    elif eligible > 0:
        status = "PARTIAL"
        exit_code = 2
    else:
        status = "FAIL"
        exit_code = 1
    print(f"STAGE 13 MIXED-SOURCE PARSE QUALITY|{status}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
