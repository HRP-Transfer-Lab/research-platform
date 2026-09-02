#!/usr/bin/env python3
"""Calibrate local Ollama extraction models against a reviewed source.

The script is deliberately read-only with respect to PostgreSQL and Git-tracked
scientific state. It:

1. hashes and deterministically parses a PDF with pdftotext;
2. retrieves a small set of relevant PDF pages from a versioned profile;
3. requests schema-constrained extraction from one or more local Ollama models;
4. validates the returned structure and source anchors;
5. compares selected fields with a calibration gold record; and
6. writes parse/extraction/validation artefacts beside the local source corpus.

Licensed PDF bytes and parsed full text remain outside Git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROFILE = (
    REPO_ROOT
    / "components/evidence-registry/config/stage13_calibration_rt014.v1.json"
)
DEFAULT_MODELS = ("qwen3.5:4b", "qwen3.5:9b")
PROMPT_VERSION = "stage13-core-study-extraction-v1"
SCHEMA_VERSION = "stage13-core-study-extraction-v1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(
    command: list[str],
    *,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        text=True,
        capture_output=capture,
        check=check,
    )


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Configuration file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Expected a JSON object in {path}")
    return value


def pdf_page_count(path: Path) -> int:
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        raise SystemExit("pdfinfo is required (install package poppler-utils)")
    result = run([pdfinfo, str(path)], capture=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"pdfinfo failed for {path}:\n{result.stderr.strip()}")
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise SystemExit(f"Could not determine PDF page count for {path}")


def parse_pdf(path: Path, output_path: Path) -> list[str]:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise SystemExit("pdftotext is required (install package poppler-utils)")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = run(
        [pdftotext, "-layout", "-enc", "UTF-8", str(path), str(output_path)],
        capture=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"pdftotext failed for {path}:\n{result.stderr.strip()}")
    text = output_path.read_text(encoding="utf-8", errors="replace")
    pages = text.split("\f")
    while pages and not pages[-1].strip():
        pages.pop()
    return pages


def normalise_search_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def page_score(page: str, phrases: Iterable[str]) -> int:
    haystack = normalise_search_text(page)
    score = 0
    for phrase in phrases:
        needle = normalise_search_text(str(phrase))
        if not needle:
            continue
        occurrences = haystack.count(needle)
        if occurrences:
            score += occurrences * (8 + min(len(needle.split()), 8))
        else:
            words = [word for word in re.findall(r"[a-z0-9]+", needle) if len(word) > 2]
            score += sum(1 for word in words if word in haystack)
    return score


def select_pages(
    pages: list[str],
    groups: list[dict[str, Any]],
    *,
    maximum_pages: int,
    maximum_characters: int,
) -> tuple[list[int], str]:
    selected: set[int] = set()

    for group in groups:
        phrases = [str(value) for value in group.get("phrases", [])]
        take = max(1, int(group.get("max_pages", 1)))
        scored = [
            (page_score(page, phrases), index)
            for index, page in enumerate(pages, start=1)
        ]
        positive = [(score, index) for score, index in scored if score > 0]
        positive.sort(key=lambda item: (-item[0], item[1]))
        for _score, index in positive[:take]:
            selected.add(index)

    if not selected:
        raise RuntimeError("No relevant pages were selected from the calibration profile")

    ranked = sorted(
        selected,
        key=lambda index: (
            -max(
                page_score(pages[index - 1], group.get("phrases", []))
                for group in groups
            ),
            index,
        ),
    )[:maximum_pages]
    ranked.sort()

    chunks: list[str] = []
    used: list[int] = []
    total = 0
    for index in ranked:
        page_text = pages[index - 1].strip()
        block = f"[PDF_PAGE {index}]\n{page_text}\n[/PDF_PAGE {index}]"
        if chunks and total + len(block) > maximum_characters:
            continue
        chunks.append(block)
        used.append(index)
        total += len(block)

    if not chunks:
        raise RuntimeError("Selected pages exceeded the configured context limit")
    return used, "\n\n".join(chunks)


def evidence_object_schema(value_schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "value": value_schema,
            "status": {
                "type": "string",
                "enum": ["extracted", "inferred", "not_reported", "unresolved"],
            },
            "pdf_page": {"type": ["integer", "null"]},
            "supporting_text": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": [
            "value",
            "status",
            "pdf_page",
            "supporting_text",
            "confidence",
        ],
        "additionalProperties": False,
    }


def extraction_schema() -> dict[str, Any]:
    def enum(values: list[str]) -> dict[str, Any]:
        return {"type": "string", "enum": values}

    def array_enum(values: list[str]) -> dict[str, Any]:
        return {
            "type": "array",
            "items": enum(values),
            "uniqueItems": True,
        }

    properties = {
        "study_design": evidence_object_schema(
            enum(
                [
                    "randomised_field_experiment",
                    "randomised_controlled_trial",
                    "quasi_experimental",
                    "observational",
                    "unclear",
                ]
            )
        ),
        "randomisation_unit": evidence_object_schema(
            enum(
                [
                    "individual_student",
                    "classroom",
                    "school",
                    "other",
                    "unclear",
                ]
            )
        ),
        "randomised_factors": evidence_object_schema(
            array_enum(
                [
                    "topic_assignment",
                    "ai_support",
                    "mastery_progression",
                    "other",
                ]
            )
        ),
        "assignment_probability": evidence_object_schema(
            enum(["equal", "unequal", "not_reported", "unclear"])
        ),
        "analysis_approaches": evidence_object_schema(
            array_enum(
                [
                    "intent_to_treat",
                    "event_conditioned",
                    "per_protocol",
                    "other",
                    "unclear",
                ]
            )
        ),
        "week1_platform_entrants": evidence_object_schema(
            {"type": ["integer", "null"], "minimum": 0}
        ),
        "delayed_assessment_completers": evidence_object_schema(
            {"type": ["integer", "null"], "minimum": 0}
        ),
        "registration_id": evidence_object_schema({"type": ["string", "null"]}),
        "delayed_assessment_timepoint": evidence_object_schema(
            enum(["one_week", "other", "unclear"])
        ),
        "reported_outcomes": evidence_object_schema(
            array_enum(
                [
                    "next_attempt_correctness_after_mistakes",
                    "delayed_practised_unpractised_math_assessment",
                    "other",
                ]
            )
        ),
    }
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def prompt_text(source_id: str, excerpt: str) -> str:
    return f"""You are performing source-grounded scientific evidence extraction.

SOURCE: {source_id}

Use only the supplied PDF excerpts. Do not use outside knowledge. Do not fill
missing information from plausibility. If a field is not explicit, use the
schema's not_reported, unresolved, unclear or null value as appropriate.

For every field:
- pdf_page must be the physical page number in a [PDF_PAGE N] label;
- supporting_text must be a short exact quotation copied from that page;
- do not use ellipses or paraphrase in supporting_text;
- keep supporting_text to no more than 35 words;
- confidence is confidence that the excerpt supports the extracted value, not
  confidence in the study's scientific quality.

Classification rules:
- randomised_field_experiment: individually or cluster randomised intervention
  delivered in a natural educational/work/service setting;
- randomised_controlled_trial: randomised intervention not better described as
  a naturalistic field experiment;
- intent_to_treat: analysis by original random assignment;
- event_conditioned: analysis restricted to a post-randomisation event or
  subgroup, such as observed mistake events;
- delayed_practised_unpractised_math_assessment: delayed assessment comparing
  material that was and was not practised under the randomised topic condition.

Return only the JSON object required by the schema.

PDF EXCERPTS
{excerpt}
"""


def request_ollama(
    *,
    base_url: str,
    model: str,
    prompt: str,
    schema: dict[str, Any],
    context_size: int,
    timeout_seconds: int,
) -> tuple[dict[str, Any], dict[str, Any], float]:
    payload = {
        "model": model,
        "stream": False,
        "think": False,
        "messages": [{"role": "user", "content": prompt}],
        "format": schema,
        "options": {
            "temperature": 0,
            "seed": 42,
            "num_ctx": context_size,
        },
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = json.load(response)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama request failed for {model}: {exc}") from exc
    elapsed = time.perf_counter() - started

    content = raw.get("message", {}).get("content")
    if not isinstance(content, str):
        raise RuntimeError(f"Ollama response for {model} has no message.content")
    try:
        extracted = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Ollama returned invalid JSON content for {model}: {exc}\n{content[:1000]}"
        ) from exc
    if not isinstance(extracted, dict):
        raise RuntimeError(f"Ollama extraction for {model} is not a JSON object")
    return extracted, raw, elapsed


def value_at_path(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(path)
        current = current[part]
    return current


def comparable(value: Any) -> Any:
    if isinstance(value, list):
        return sorted(value)
    return value


def normalise_quote(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[\u2018\u2019]", "'", value)
    value = re.sub(r"[\u201c\u201d]", '"', value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def validate_structure(
    extracted: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    expected = set(schema["properties"])
    actual = set(extracted)
    missing = expected - actual
    extra = actual - expected
    if missing:
        errors.append(f"missing_fields:{','.join(sorted(missing))}")
    if extra:
        errors.append(f"extra_fields:{','.join(sorted(extra))}")

    for field in sorted(expected & actual):
        item = extracted[field]
        if not isinstance(item, dict):
            errors.append(f"{field}:not_object")
            continue
        required = {
            "value",
            "status",
            "pdf_page",
            "supporting_text",
            "confidence",
        }
        absent = required - set(item)
        if absent:
            errors.append(f"{field}:missing:{','.join(sorted(absent))}")
        if item.get("status") not in {
            "extracted",
            "inferred",
            "not_reported",
            "unresolved",
        }:
            errors.append(f"{field}:invalid_status")
        page = item.get("pdf_page")
        if page is not None and (not isinstance(page, int) or isinstance(page, bool)):
            errors.append(f"{field}:invalid_pdf_page")
        quote = item.get("supporting_text")
        if not isinstance(quote, str):
            errors.append(f"{field}:invalid_supporting_text")
        confidence = item.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            errors.append(f"{field}:invalid_confidence")
        elif not 0 <= float(confidence) <= 1:
            errors.append(f"{field}:confidence_out_of_range")
    return errors


def validate_anchors(
    extracted: dict[str, Any],
    pages: list[str],
) -> tuple[list[dict[str, Any]], int, int]:
    checks: list[dict[str, Any]] = []
    valid = 0
    attempted = 0
    for field, item in sorted(extracted.items()):
        if not isinstance(item, dict):
            continue
        page = item.get("pdf_page")
        quote = item.get("supporting_text", "")
        status = item.get("status")
        if status in {"not_reported", "unresolved"} and not quote:
            checks.append(
                {
                    "field": field,
                    "attempted": False,
                    "valid": True,
                    "reason": "no_anchor_required_for_unresolved_field",
                }
            )
            continue
        attempted += 1
        reason = "valid"
        is_valid = True
        if not isinstance(page, int) or not 1 <= page <= len(pages):
            is_valid = False
            reason = "page_out_of_range"
        elif not isinstance(quote, str) or not quote.strip():
            is_valid = False
            reason = "missing_supporting_text"
        elif normalise_quote(quote) not in normalise_quote(pages[page - 1]):
            is_valid = False
            reason = "quote_not_found_on_page"
        if is_valid:
            valid += 1
        checks.append(
            {
                "field": field,
                "attempted": True,
                "valid": is_valid,
                "reason": reason,
                "pdf_page": page,
            }
        )
    return checks, valid, attempted


def score_gold(
    extracted: dict[str, Any],
    gold: dict[str, Any],
) -> tuple[list[dict[str, Any]], int, int]:
    results: list[dict[str, Any]] = []
    matches = 0
    for path, expected in gold.items():
        try:
            observed = value_at_path(extracted, path)
            matched = comparable(observed) == comparable(expected)
        except KeyError:
            observed = None
            matched = False
        if matched:
            matches += 1
        results.append(
            {
                "field_path": path,
                "expected": expected,
                "observed": observed,
                "match": matched,
            }
        )
    return results, matches, len(gold)


def ns_to_seconds(value: Any) -> float:
    if not isinstance(value, (int, float)):
        return 0.0
    return float(value) / 1_000_000_000


def model_filename(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Calibrate local Ollama extraction models on a reviewed source."
    )
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--context", type=int, default=8192)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    pdf = args.pdf.expanduser().resolve()
    profile_path = args.profile.expanduser().resolve()
    if not pdf.is_file():
        raise SystemExit(f"PDF not found: {pdf}")
    if args.context < 4096:
        raise SystemExit("--context must be at least 4096")
    profile = load_json(profile_path)
    source_id = str(profile["source_id"])

    page_count = pdf_page_count(pdf)
    expected_pages = profile.get("expected_pdf_pages")
    if expected_pages is not None and page_count != int(expected_pages):
        raise SystemExit(
            f"Expected {expected_pages} PDF pages for {source_id}; found {page_count}"
        )

    corpus_root = pdf.parent
    parsed_dir = corpus_root / "parsed"
    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else corpus_root / "manifests" / "stage13-local-calibration"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    parsed_path = parsed_dir / f"{pdf.stem}.layout.txt"

    pages = parse_pdf(pdf, parsed_path)
    if len(pages) != page_count:
        raise SystemExit(
            f"Parsed page count mismatch: pdfinfo={page_count}, pdftotext={len(pages)}"
        )

    retrieval = profile["retrieval"]
    selected_pages, excerpt = select_pages(
        pages,
        list(retrieval["groups"]),
        maximum_pages=int(retrieval.get("maximum_pages", 10)),
        maximum_characters=int(retrieval.get("maximum_characters", 32000)),
    )
    prompt = prompt_text(source_id, excerpt)
    schema = extraction_schema()
    pdf_hash = sha256_file(pdf)
    parsed_hash = sha256_file(parsed_path)
    excerpt_hash = sha256_bytes(excerpt.encode("utf-8"))
    prompt_hash = sha256_bytes(prompt.encode("utf-8"))
    generated_at = datetime.now(timezone.utc).isoformat()

    parse_manifest = {
        "schema_version": "stage13-pdf-parse-manifest-v1",
        "source_id": source_id,
        "pdf_path": str(pdf),
        "pdf_sha256": pdf_hash,
        "pdf_bytes": pdf.stat().st_size,
        "pdf_pages": page_count,
        "parser": "pdftotext",
        "parser_mode": "layout",
        "parsed_text_path": str(parsed_path),
        "parsed_text_sha256": parsed_hash,
        "selected_pdf_pages": selected_pages,
        "excerpt_sha256": excerpt_hash,
        "generated_at": generated_at,
    }
    (output_dir / "parse-manifest.json").write_text(
        json.dumps(parse_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    gold = profile["gold"]
    thresholds = profile["thresholds"]
    summaries: list[dict[str, Any]] = []

    print("=== STAGE 13 LOCAL EXTRACTION CALIBRATION ===")
    print(f"source_id|{source_id}")
    print(f"pdf_sha256|{pdf_hash}")
    print(f"pdf_pages|{page_count}")
    print("selected_pdf_pages|" + ",".join(str(value) for value in selected_pages))
    print(f"prompt_characters|{len(prompt)}")

    for model in args.models:
        print(f"model_start|{model}", flush=True)
        try:
            extracted, raw, elapsed = request_ollama(
                base_url=args.ollama_url,
                model=model,
                prompt=prompt,
                schema=schema,
                context_size=args.context,
                timeout_seconds=args.timeout,
            )
            structure_errors = validate_structure(extracted, schema)
            anchor_checks, anchor_valid, anchor_attempted = validate_anchors(
                extracted, pages
            )
            field_results, field_matches, field_total = score_gold(extracted, gold)
            field_accuracy = field_matches / field_total if field_total else 0.0
            anchor_rate = (
                anchor_valid / anchor_attempted if anchor_attempted else 1.0
            )
            schema_valid = not structure_errors
            passed = (
                schema_valid
                and field_accuracy >= float(thresholds["minimum_field_accuracy"])
                and anchor_rate >= float(thresholds["minimum_anchor_validity"])
            )

            prompt_seconds = ns_to_seconds(raw.get("prompt_eval_duration"))
            output_seconds = ns_to_seconds(raw.get("eval_duration"))
            prompt_tokens = int(raw.get("prompt_eval_count") or 0)
            output_tokens = int(raw.get("eval_count") or 0)
            result = {
                "schema_version": "stage13-local-calibration-result-v1",
                "source_id": source_id,
                "model": model,
                "prompt_version": PROMPT_VERSION,
                "extraction_schema_version": SCHEMA_VERSION,
                "context_size": args.context,
                "pdf_sha256": pdf_hash,
                "selected_pdf_pages": selected_pages,
                "excerpt_sha256": excerpt_hash,
                "prompt_sha256": prompt_hash,
                "generated_at": generated_at,
                "extraction": extracted,
                "validation": {
                    "schema_valid": schema_valid,
                    "structure_errors": structure_errors,
                    "field_results": field_results,
                    "field_matches": field_matches,
                    "field_total": field_total,
                    "field_accuracy": field_accuracy,
                    "anchor_checks": anchor_checks,
                    "anchor_valid": anchor_valid,
                    "anchor_attempted": anchor_attempted,
                    "anchor_validity": anchor_rate,
                    "passed": passed,
                },
                "performance": {
                    "wall_seconds": elapsed,
                    "load_seconds": ns_to_seconds(raw.get("load_duration")),
                    "prompt_tokens": prompt_tokens,
                    "prompt_seconds": prompt_seconds,
                    "prompt_tokens_per_second": (
                        prompt_tokens / prompt_seconds if prompt_seconds else 0.0
                    ),
                    "output_tokens": output_tokens,
                    "output_seconds": output_seconds,
                    "output_tokens_per_second": (
                        output_tokens / output_seconds if output_seconds else 0.0
                    ),
                    "total_duration_seconds": ns_to_seconds(raw.get("total_duration")),
                },
                "ollama_response_metadata": {
                    key: raw.get(key)
                    for key in (
                        "model",
                        "created_at",
                        "done",
                        "done_reason",
                        "total_duration",
                        "load_duration",
                        "prompt_eval_count",
                        "prompt_eval_duration",
                        "eval_count",
                        "eval_duration",
                    )
                },
            }
            filename = output_dir / f"{model_filename(model)}.json"
            filename.write_text(
                json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            summary = {
                "model": model,
                "schema_valid": schema_valid,
                "field_matches": field_matches,
                "field_total": field_total,
                "field_accuracy": round(field_accuracy, 6),
                "anchor_valid": anchor_valid,
                "anchor_attempted": anchor_attempted,
                "anchor_validity": round(anchor_rate, 6),
                "wall_seconds": round(elapsed, 3),
                "prompt_tokens_per_second": round(
                    result["performance"]["prompt_tokens_per_second"], 3
                ),
                "output_tokens_per_second": round(
                    result["performance"]["output_tokens_per_second"], 3
                ),
                "passed": passed,
                "result_path": str(filename),
            }
            summaries.append(summary)
        except Exception as exc:
            summary = {
                "model": model,
                "schema_valid": False,
                "field_matches": 0,
                "field_total": len(gold),
                "field_accuracy": 0.0,
                "anchor_valid": 0,
                "anchor_attempted": 0,
                "anchor_validity": 0.0,
                "wall_seconds": None,
                "prompt_tokens_per_second": 0.0,
                "output_tokens_per_second": 0.0,
                "passed": False,
                "error": str(exc),
            }
            summaries.append(summary)

        summary = summaries[-1]
        print(f"model|{summary['model']}")
        print(f"schema_valid|{1 if summary['schema_valid'] else 0}")
        print(
            f"field_accuracy|{summary['field_matches']}/{summary['field_total']}"
            f"|{summary['field_accuracy']:.3f}"
        )
        print(
            f"anchor_validity|{summary['anchor_valid']}/"
            f"{summary['anchor_attempted']}|{summary['anchor_validity']:.3f}"
        )
        if summary["wall_seconds"] is not None:
            print(f"wall_seconds|{summary['wall_seconds']:.2f}")
            print(
                "prompt_tokens_per_second|"
                f"{summary['prompt_tokens_per_second']:.2f}"
            )
            print(
                "output_tokens_per_second|"
                f"{summary['output_tokens_per_second']:.2f}"
            )
        if "error" in summary:
            print(f"error|{summary['error']}")
        print(f"calibration_pass|{1 if summary['passed'] else 0}")

    summary_manifest = {
        "schema_version": "stage13-local-calibration-summary-v1",
        "source_id": source_id,
        "profile_path": str(profile_path),
        "profile_sha256": sha256_file(profile_path),
        "pdf_sha256": pdf_hash,
        "selected_pdf_pages": selected_pages,
        "prompt_version": PROMPT_VERSION,
        "extraction_schema_version": SCHEMA_VERSION,
        "thresholds": thresholds,
        "models": summaries,
        "generated_at": generated_at,
        "registry_mutated": False,
        "scientific_state_mutated": False,
        "historical_release_mutated": False,
        "csi_gateway_mutated": False,
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    passed_models = [item["model"] for item in summaries if item["passed"]]
    print(f"passed_models|{','.join(passed_models)}")
    print(f"summary_path|{summary_path}")
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print(
        "STAGE 13 LOCAL EXTRACTION CALIBRATION|"
        + ("PASS" if passed_models else "REVIEW")
    )
    return 0 if passed_models else 2


if __name__ == "__main__":
    raise SystemExit(main())
