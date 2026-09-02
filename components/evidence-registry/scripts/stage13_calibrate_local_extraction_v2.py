#!/usr/bin/env python3
"""Stage 13 V2 calibration: parser-owned evidence spans and task-sized prompts.

Read-only with respect to PostgreSQL, scientific state, releases and the CSI
Gateway. Local artefacts are written beside the source corpus.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import stage13_calibrate_local_extraction as v1

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROFILE = REPO_ROOT / "components/evidence-registry/config/stage13_calibration_rt014.v2.json"
DEFAULT_MODELS = ("qwen3.5:4b",)
PROMPT_VERSION = "stage13-core-study-extraction-v2-span-ids"
SCHEMA_VERSION = "stage13-core-study-extraction-v2"


@dataclass(frozen=True)
class Span:
    span_id: str
    pdf_page: int
    ordinal: int
    text: str
    text_sha256: str


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def clean_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", value)
    value = re.sub(r"[ \t]+\n", "\n", value)
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def split_long(block: str, limit: int) -> list[str]:
    if len(block) <= limit:
        return [block] if block else []
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", block)
    output: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > limit:
            output.append(current)
            current = sentence
        elif len(sentence) > limit:
            if current:
                output.append(current)
                current = ""
            output.extend(sentence[i:i + limit].strip() for i in range(0, len(sentence), limit))
        else:
            current = candidate
    if current:
        output.append(current)
    return [item for item in output if item]


def build_spans(pages: list[str], config: dict[str, Any]) -> list[Span]:
    target = int(config.get("target_characters", 900))
    maximum = int(config.get("maximum_characters", 1400))
    minimum = int(config.get("minimum_characters", 180))
    output: list[Span] = []

    for page_number, raw_page in enumerate(pages, start=1):
        page = clean_text(raw_page)
        if not page:
            continue
        blocks: list[str] = []
        for raw in re.split(r"\n\s*\n", page):
            block = re.sub(r"\s*\n\s*", " ", raw).strip()
            blocks.extend(split_long(block, maximum))

        grouped: list[str] = []
        current = ""
        for block in blocks:
            candidate = f"{current}\n{block}".strip()
            if current and len(candidate) > target:
                grouped.append(current)
                current = block
            else:
                current = candidate
        if current:
            grouped.append(current)
        if len(grouped) >= 2 and len(grouped[-1]) < minimum:
            merged = f"{grouped[-2]}\n{grouped[-1]}".strip()
            if len(merged) <= maximum:
                grouped[-2:] = [merged]

        for ordinal, text in enumerate(grouped, start=1):
            output.append(Span(
                span_id=f"p{page_number:03d}-s{ordinal:03d}",
                pdf_page=page_number,
                ordinal=ordinal,
                text=text,
                text_sha256=v1.sha256_bytes(text.encode("utf-8")),
            ))
    return output


def normalise(value: str) -> str:
    value = value.casefold().replace("–", "-").replace("—", "-")
    value = re.sub(r"(?<=\w)-\s+(?=\w)", "", value)
    value = re.sub(r"[^a-z0-9%+\-.]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def score_text(text: str, phrases: Iterable[str]) -> int:
    haystack = normalise(text)
    score = 0
    for phrase in phrases:
        needle = normalise(str(phrase))
        if not needle:
            continue
        count = haystack.count(needle)
        if count:
            score += count * (20 + 3 * min(len(needle.split()), 10))
        else:
            score += sum(1 for word in needle.split() if len(word) > 2 and word in haystack)
    return score


def retrieve(spans: list[Span], task: dict[str, Any]) -> list[Span]:
    phrases = task.get("retrieval_phrases", [])
    maximum = int(task.get("maximum_spans", 12))
    char_limit = int(task.get("maximum_characters", 9000))
    per_page = int(task.get("maximum_spans_per_page", 3))
    ranked = sorted(
        ((score_text(span.text, phrases), span) for span in spans),
        key=lambda item: (-item[0], item[1].pdf_page, item[1].ordinal),
    )
    selected: list[Span] = []
    page_counts: dict[int, int] = {}
    characters = 0
    for score, span in ranked:
        if score <= 0 or page_counts.get(span.pdf_page, 0) >= per_page:
            continue
        addition = len(span.text) + len(span.span_id) + 20
        if selected and characters + addition > char_limit:
            continue
        selected.append(span)
        page_counts[span.pdf_page] = page_counts.get(span.pdf_page, 0) + 1
        characters += addition
        if len(selected) >= maximum:
            break
    if not selected:
        raise RuntimeError(f"No spans selected for {task['task_id']}")
    return sorted(selected, key=lambda span: (span.pdf_page, span.ordinal))


def evidence_schema(value_schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "value": value_schema,
            "status": {"type": "string", "enum": ["extracted", "inferred", "not_reported", "unresolved"]},
            "evidence_span_ids": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["value", "status", "evidence_span_ids", "confidence"],
        "additionalProperties": False,
    }


def value_schemas() -> dict[str, dict[str, Any]]:
    def enum(values: list[str]) -> dict[str, Any]:
        return {"type": "string", "enum": values}

    def array(values: list[str]) -> dict[str, Any]:
        return {"type": "array", "items": enum(values), "uniqueItems": True}

    return {
        "study_design": enum(["randomised_field_experiment", "randomised_controlled_trial", "quasi_experimental", "observational", "unclear"]),
        "randomisation_unit": enum(["individual_student", "classroom", "school", "other", "unclear"]),
        "randomised_factors": array(["topic_assignment", "ai_support", "mastery_progression", "other"]),
        "assignment_probability": enum(["equal", "unequal", "not_reported", "unclear"]),
        "analysis_approaches": array(["intent_to_treat", "event_conditioned", "per_protocol", "other", "unclear"]),
        "week1_platform_entrants": {"type": ["integer", "null"], "minimum": 0},
        "delayed_assessment_completers": {"type": ["integer", "null"], "minimum": 0},
        "registration_id": {"type": ["string", "null"]},
        "delayed_assessment_timepoint": enum(["one_week", "other", "unclear"]),
        "reported_outcomes": array(["next_attempt_correctness_after_mistakes", "delayed_practised_unpractised_math_assessment", "other"]),
    }


def task_schema(fields: list[str]) -> dict[str, Any]:
    schemas = value_schemas()
    properties = {field: evidence_schema(schemas[field]) for field in fields}
    return {"type": "object", "properties": properties, "required": fields, "additionalProperties": False}


def make_prompt(source_id: str, task: dict[str, Any], spans: list[Span]) -> str:
    notes = "\n".join(
        f"- {field}: {task.get('field_notes', {}).get(field, 'Extract only what the spans support.')}"
        for field in task["fields"]
    )
    blocks = "\n\n".join(
        f"[SPAN {span.span_id} | PDF_PAGE {span.pdf_page}]\n{span.text}\n[/SPAN {span.span_id}]"
        for span in spans
    )
    allowed = ", ".join(span.span_id for span in spans)
    return f"""You are performing source-grounded scientific evidence extraction.

SOURCE: {source_id}
TASK: {task['task_id']}

Use only the parser-owned spans below. Cite evidence by selecting exact span IDs
from this allowed list; do not retype quotations or invent page numbers:

{allowed}

Rules:
- Every extracted or inferred non-null value requires at least one supporting
  evidence_span_id from the allowed list.
- Use multiple span IDs when an array needs support from more than one passage.
- Use an empty evidence_span_ids array only for not_reported or unresolved.
- extracted = directly stated; inferred = classification from explicit facts.
- A working-paper number, DOI or report identifier is not a trial registration.
- Do not omit a second analysis or outcome family when another span supports it.
- Return only the JSON object required by the supplied schema.

Field rules:
{notes}

PARSER-OWNED SPANS
{blocks}
"""


def validate_structure(extracted: dict[str, Any], fields: list[str]) -> list[str]:
    errors: list[str] = []
    expected = set(fields)
    actual = set(extracted)
    if expected - actual:
        errors.append("missing:" + ",".join(sorted(expected - actual)))
    if actual - expected:
        errors.append("extra:" + ",".join(sorted(actual - expected)))
    for field in sorted(expected & actual):
        item = extracted[field]
        if not isinstance(item, dict):
            errors.append(f"{field}:not_object")
            continue
        required = {"value", "status", "evidence_span_ids", "confidence"}
        if required - set(item):
            errors.append(f"{field}:missing_keys")
        if set(item) - required:
            errors.append(f"{field}:extra_keys")
        if item.get("status") not in {"extracted", "inferred", "not_reported", "unresolved"}:
            errors.append(f"{field}:bad_status")
        ids = item.get("evidence_span_ids")
        if not isinstance(ids, list) or any(not isinstance(value, str) for value in ids):
            errors.append(f"{field}:bad_span_ids")
        confidence = item.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= float(confidence) <= 1:
            errors.append(f"{field}:bad_confidence")
    return errors


def comparable(value: Any) -> Any:
    return sorted(value) if isinstance(value, list) else value


def score_fields(extracted: dict[str, Any], gold: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    output: list[dict[str, Any]] = []
    matches = 0
    for field, expected in gold.items():
        item = extracted.get(field)
        observed = item.get("value") if isinstance(item, dict) else None
        match = comparable(observed) == comparable(expected)
        matches += int(match)
        output.append({"field": field, "expected": expected, "observed": observed, "match": match})
    return output, matches


def deterministic_candidates(spans: list[Span], rules: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for field, rule in rules.items():
        pattern = re.compile(str(rule["regex"]), re.IGNORECASE)
        matches: list[tuple[str, Span]] = []
        for span in spans:
            found = pattern.search(span.text)
            if found:
                matches.append((found.group(int(rule.get("group", 0))), span))
        values = sorted({value for value, _ in matches})
        if len(values) == 1:
            value = values[0]
            output[field] = {
                "value": value,
                "status": "extracted",
                "evidence_span_ids": [
                    span.span_id for matched, span in matches if matched == value
                ][:int(rule.get("maximum_evidence_spans", 2))],
                "confidence": 1.0,
            }
    return output


def merge_hybrid(model: dict[str, Any], deterministic: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    merged = json.loads(json.dumps(model))
    overrides: list[str] = []
    for field, candidate in deterministic.items():
        if merged.get(field) != candidate:
            overrides.append(field)
        merged[field] = candidate
    return merged, overrides


def span_reference_checks(extracted: dict[str, Any], span_by_id: dict[str, Span]) -> tuple[list[dict[str, Any]], int, int]:
    output: list[dict[str, Any]] = []
    valid = attempted = 0
    for field, item in sorted(extracted.items()):
        ids = item.get("evidence_span_ids") if isinstance(item, dict) else None
        status = item.get("status") if isinstance(item, dict) else None
        value = item.get("value") if isinstance(item, dict) else None
        required = status in {"extracted", "inferred"} and value is not None and value not in ("not_reported", "unclear")
        if not required and ids == []:
            output.append({"field": field, "valid": True, "reason": "not_required", "ids": []})
            continue
        attempted += 1
        missing = [span_id for span_id in ids or [] if span_id not in span_by_id]
        passed = isinstance(ids, list) and bool(ids) and not missing
        valid += int(passed)
        output.append({
            "field": field,
            "valid": passed,
            "reason": "valid" if passed else ("missing:" + ",".join(missing) if missing else "empty_or_invalid"),
            "ids": ids,
        })
    return output, valid, attempted


def rule_passes(text: str, rule: dict[str, Any]) -> tuple[bool, list[str]]:
    haystack = normalise(text)
    failed: list[str] = []
    for index, alternatives in enumerate(rule.get("all_groups", []), start=1):
        needles = [normalise(str(value)) for value in alternatives]
        if not any(needle and needle in haystack for needle in needles):
            failed.append(f"group_{index}")
    return not failed, failed


def semantic_support_checks(
    extracted: dict[str, Any],
    gold: dict[str, Any],
    rules: dict[str, Any],
    span_by_id: dict[str, Span],
) -> tuple[list[dict[str, Any]], int]:
    output: list[dict[str, Any]] = []
    valid = 0
    for field, expected in gold.items():
        item = extracted.get(field)
        observed = item.get("value") if isinstance(item, dict) else None
        ids = item.get("evidence_span_ids", []) if isinstance(item, dict) else []
        value_correct = comparable(observed) == comparable(expected)
        ids_valid = isinstance(ids, list) and bool(ids) and all(span_id in span_by_id for span_id in ids)
        text = "\n".join(span_by_id[span_id].text for span_id in ids if span_id in span_by_id)
        support_valid, failed = rule_passes(text, rules.get(field, {}))
        passed = value_correct and ids_valid and support_valid
        valid += int(passed)
        output.append({
            "field": field,
            "value_correct": value_correct,
            "span_ids_valid": ids_valid,
            "support_rule_valid": support_valid,
            "failed_support_groups": failed,
            "evidence_span_ids": ids,
        })
    return output, valid


def main() -> int:
    parser = argparse.ArgumentParser(description="Run span-grounded local extraction calibration.")
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
    profile = v1.load_json(profile_path)
    source_id = str(profile["source_id"])
    page_count = v1.pdf_page_count(pdf)
    if page_count != int(profile["expected_pdf_pages"]):
        raise SystemExit(f"Expected {profile['expected_pdf_pages']} pages; found {page_count}")

    corpus_root = pdf.parent
    parsed_path = corpus_root / "parsed" / f"{pdf.stem}.layout.txt"
    output_dir = args.output_dir.expanduser().resolve() if args.output_dir else corpus_root / "manifests" / "stage13-local-calibration-v2"
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = v1.parse_pdf(pdf, parsed_path)
    if len(pages) != page_count:
        raise SystemExit(f"Parsed page mismatch: pdfinfo={page_count}, pdftotext={len(pages)}")

    spans = build_spans(pages, profile.get("span_generation", {}))
    span_by_id = {span.span_id: span for span in spans}
    spans_path = output_dir / "spans.jsonl"
    with spans_path.open("w", encoding="utf-8") as handle:
        for span in spans:
            handle.write(v1.canonical_json({
                "span_id": span.span_id,
                "pdf_page": span.pdf_page,
                "ordinal": span.ordinal,
                "text": span.text,
                "text_sha256": span.text_sha256,
            }) + "\n")

    task_payloads: list[tuple[dict[str, Any], list[Span], dict[str, Any], str]] = []
    retrieval_rows: list[dict[str, Any]] = []
    for task in profile["tasks"]:
        selected = retrieve(spans, task)
        schema = task_schema(list(task["fields"]))
        prompt = make_prompt(source_id, task, selected)
        task_payloads.append((task, selected, schema, prompt))
        retrieval_rows.append({
            "task_id": task["task_id"],
            "fields": task["fields"],
            "selected_span_ids": [span.span_id for span in selected],
            "selected_pdf_pages": sorted({span.pdf_page for span in selected}),
            "prompt_characters": len(prompt),
            "prompt_sha256": v1.sha256_bytes(prompt.encode("utf-8")),
        })

    generated_at = datetime.now(timezone.utc).isoformat()
    pdf_hash = v1.sha256_file(pdf)
    deterministic = deterministic_candidates(spans, profile.get("deterministic_fields", {}))
    write_json(output_dir / "parse-manifest.json", {
        "schema_version": "stage13-pdf-parse-span-manifest-v2",
        "source_id": source_id,
        "pdf_path": str(pdf),
        "pdf_sha256": pdf_hash,
        "pdf_pages": page_count,
        "parsed_text_path": str(parsed_path),
        "parsed_text_sha256": v1.sha256_file(parsed_path),
        "span_manifest_path": str(spans_path),
        "span_count": len(spans),
        "generated_at": generated_at,
    })
    write_json(output_dir / "retrieval-manifest.json", {
        "schema_version": "stage13-span-retrieval-manifest-v2",
        "source_id": source_id,
        "tasks": retrieval_rows,
        "generated_at": generated_at,
    })
    write_json(output_dir / "deterministic-candidates.json", deterministic)

    gold = profile["gold"]
    rules = profile["support_rules"]
    thresholds = profile["thresholds"]
    summaries: list[dict[str, Any]] = []

    print("=== STAGE 13 LOCAL EXTRACTION CALIBRATION V2 ===")
    print(f"source_id|{source_id}")
    print(f"pdf_sha256|{pdf_hash}")
    print(f"pdf_pages|{page_count}")
    print(f"parser_owned_spans|{len(spans)}")
    print("deterministic_fields|" + ",".join(sorted(deterministic)))
    for row in retrieval_rows:
        print(f"task|{row['task_id']}")
        print(f"task_selected_pages|{row['task_id']}|" + ",".join(map(str, row["selected_pdf_pages"])))
        print(f"task_selected_spans|{row['task_id']}|" + ",".join(row["selected_span_ids"]))
        print(f"task_prompt_characters|{row['task_id']}|{row['prompt_characters']}")

    for model in args.models:
        print(f"model_start|{model}", flush=True)
        started = time.perf_counter()
        combined: dict[str, Any] = {}
        task_results: list[dict[str, Any]] = []
        totals = {"prompt_tokens": 0, "prompt_seconds": 0.0, "output_tokens": 0, "output_seconds": 0.0}
        error: str | None = None

        for task, selected, schema, prompt in task_payloads:
            task_id = task["task_id"]
            print(f"task_start|{model}|{task_id}", flush=True)
            try:
                extracted, raw, elapsed = v1.request_ollama(
                    base_url=args.ollama_url,
                    model=model,
                    prompt=prompt,
                    schema=schema,
                    context_size=args.context,
                    timeout_seconds=args.timeout,
                )
                structure_errors = validate_structure(extracted, list(task["fields"]))
                if structure_errors:
                    raise RuntimeError(str(structure_errors))
                overlap = set(combined) & set(extracted)
                if overlap:
                    raise RuntimeError(f"duplicate fields: {sorted(overlap)}")
                combined.update(extracted)
                prompt_seconds = v1.ns_to_seconds(raw.get("prompt_eval_duration"))
                output_seconds = v1.ns_to_seconds(raw.get("eval_duration"))
                prompt_tokens = int(raw.get("prompt_eval_count") or 0)
                output_tokens = int(raw.get("eval_count") or 0)
                totals["prompt_tokens"] += prompt_tokens
                totals["prompt_seconds"] += prompt_seconds
                totals["output_tokens"] += output_tokens
                totals["output_seconds"] += output_seconds
                task_results.append({
                    "task_id": task_id,
                    "selected_span_ids": [span.span_id for span in selected],
                    "selected_pdf_pages": sorted({span.pdf_page for span in selected}),
                    "extraction": extracted,
                    "performance": {
                        "wall_seconds": elapsed,
                        "prompt_tokens": prompt_tokens,
                        "prompt_tokens_per_second": prompt_tokens / prompt_seconds if prompt_seconds else 0,
                        "output_tokens": output_tokens,
                        "output_tokens_per_second": output_tokens / output_seconds if output_seconds else 0,
                    },
                })
                print(f"task_complete|{model}|{task_id}|{elapsed:.2f}s", flush=True)
            except Exception as exc:
                error = f"{task_id}: {exc}"
                print(f"task_error|{model}|{error}", flush=True)
                break

        wall = time.perf_counter() - started
        if error:
            summary = {
                "model": model, "schema_valid": False, "field_total": len(gold),
                "model_field_matches": 0, "model_field_accuracy": 0.0,
                "hybrid_field_matches": 0, "hybrid_field_accuracy": 0.0,
                "span_reference_valid": 0, "span_reference_attempted": 0, "span_reference_validity": 0.0,
                "supported_field_matches": 0, "supported_field_total": len(gold), "supported_field_accuracy": 0.0,
                "wall_seconds": wall, "passed": False, "workhorse_candidate": False, "error": error,
            }
        else:
            structure_errors = validate_structure(combined, list(gold))
            model_results, model_matches = score_fields(combined, gold)
            hybrid, overrides = merge_hybrid(combined, deterministic)
            hybrid_results, hybrid_matches = score_fields(hybrid, gold)
            reference_checks, reference_valid, reference_attempted = span_reference_checks(hybrid, span_by_id)
            support_checks, supported_matches = semantic_support_checks(hybrid, gold, rules, span_by_id)
            total = len(gold)
            model_accuracy = model_matches / total
            hybrid_accuracy = hybrid_matches / total
            reference_rate = reference_valid / reference_attempted if reference_attempted else 1.0
            supported_accuracy = supported_matches / total
            schema_valid = not structure_errors
            passed = (
                schema_valid
                and hybrid_accuracy >= float(thresholds["minimum_hybrid_field_accuracy"])
                and reference_rate >= float(thresholds["minimum_span_reference_validity"])
                and supported_accuracy >= float(thresholds["minimum_supported_field_accuracy"])
            )
            workhorse = (
                schema_valid
                and hybrid_accuracy >= float(thresholds["automatic_workhorse_candidate_hybrid_field_accuracy"])
                and reference_rate >= float(thresholds["automatic_workhorse_candidate_span_reference_validity"])
                and supported_accuracy >= float(thresholds["automatic_workhorse_candidate_supported_field_accuracy"])
            )
            result_path = output_dir / f"{v1.model_filename(model)}.v2.json"
            write_json(result_path, {
                "schema_version": "stage13-local-calibration-result-v2",
                "source_id": source_id,
                "model": model,
                "prompt_version": PROMPT_VERSION,
                "extraction_schema_version": SCHEMA_VERSION,
                "pdf_sha256": pdf_hash,
                "tasks": task_results,
                "model_extraction": combined,
                "deterministic_candidates": deterministic,
                "hybrid_extraction": hybrid,
                "validation": {
                    "schema_valid": schema_valid,
                    "structure_errors": structure_errors,
                    "model_field_results": model_results,
                    "hybrid_field_results": hybrid_results,
                    "deterministic_overrides": overrides,
                    "span_reference_checks": reference_checks,
                    "semantic_support_checks": support_checks,
                    "passed": passed,
                    "workhorse_candidate": workhorse,
                },
                "performance": {
                    "wall_seconds": wall,
                    "prompt_tokens": totals["prompt_tokens"],
                    "prompt_tokens_per_second": totals["prompt_tokens"] / totals["prompt_seconds"] if totals["prompt_seconds"] else 0,
                    "output_tokens": totals["output_tokens"],
                    "output_tokens_per_second": totals["output_tokens"] / totals["output_seconds"] if totals["output_seconds"] else 0,
                },
                "governance": {
                    "registry_mutated": False,
                    "scientific_state_mutated": False,
                    "historical_release_mutated": False,
                    "csi_gateway_mutated": False,
                    "may_create_human_authority": False,
                },
            })
            summary = {
                "model": model, "schema_valid": schema_valid, "field_total": total,
                "model_field_matches": model_matches, "model_field_accuracy": model_accuracy,
                "hybrid_field_matches": hybrid_matches, "hybrid_field_accuracy": hybrid_accuracy,
                "deterministic_overrides": overrides,
                "span_reference_valid": reference_valid, "span_reference_attempted": reference_attempted,
                "span_reference_validity": reference_rate,
                "supported_field_matches": supported_matches, "supported_field_total": total,
                "supported_field_accuracy": supported_accuracy,
                "wall_seconds": wall,
                "prompt_tokens_per_second": totals["prompt_tokens"] / totals["prompt_seconds"] if totals["prompt_seconds"] else 0,
                "output_tokens_per_second": totals["output_tokens"] / totals["output_seconds"] if totals["output_seconds"] else 0,
                "passed": passed, "workhorse_candidate": workhorse,
                "result_path": str(result_path),
            }
        summaries.append(summary)

        print(f"model|{model}")
        print(f"schema_valid|{int(summary['schema_valid'])}")
        print(f"model_field_accuracy|{summary['model_field_matches']}/{summary['field_total']}|{summary['model_field_accuracy']:.3f}")
        print(f"hybrid_field_accuracy|{summary['hybrid_field_matches']}/{summary['field_total']}|{summary['hybrid_field_accuracy']:.3f}")
        print("deterministic_overrides|" + ",".join(summary.get("deterministic_overrides", [])))
        print(f"span_reference_validity|{summary['span_reference_valid']}/{summary['span_reference_attempted']}|{summary['span_reference_validity']:.3f}")
        print(f"supported_field_accuracy|{summary['supported_field_matches']}/{summary['supported_field_total']}|{summary['supported_field_accuracy']:.3f}")
        print(f"wall_seconds|{summary['wall_seconds']:.2f}")
        if "error" in summary:
            print(f"error|{summary['error']}")
        else:
            print(f"prompt_tokens_per_second|{summary['prompt_tokens_per_second']:.2f}")
            print(f"output_tokens_per_second|{summary['output_tokens_per_second']:.2f}")
        print(f"calibration_pass|{int(summary['passed'])}")
        print(f"workhorse_candidate|{int(summary['workhorse_candidate'])}")

    summary_path = output_dir / "summary.json"
    write_json(summary_path, {
        "schema_version": "stage13-local-calibration-summary-v2",
        "source_id": source_id,
        "profile_path": str(profile_path),
        "profile_sha256": v1.sha256_file(profile_path),
        "pdf_sha256": pdf_hash,
        "prompt_version": PROMPT_VERSION,
        "extraction_schema_version": SCHEMA_VERSION,
        "thresholds": thresholds,
        "models": summaries,
        "generated_at": generated_at,
        "registry_mutated": False,
        "scientific_state_mutated": False,
        "historical_release_mutated": False,
        "csi_gateway_mutated": False,
    })
    passed_models = [row["model"] for row in summaries if row["passed"]]
    workhorses = [row["model"] for row in summaries if row["workhorse_candidate"]]
    print("passed_models|" + ",".join(passed_models))
    print("workhorse_candidates|" + ",".join(workhorses))
    print(f"summary_path|{summary_path}")
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print("STAGE 13 LOCAL EXTRACTION CALIBRATION V2|" + ("PASS" if passed_models else "REVIEW"))
    return 0 if passed_models else 2


if __name__ == "__main__":
    raise SystemExit(main())
