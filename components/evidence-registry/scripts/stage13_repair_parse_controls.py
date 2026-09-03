#!/usr/bin/env python3
"""Create canonical parsed-text derivatives for known PDF font artefacts.

The Stage 13 parse-quality gate quarantines unexpected C0 control characters.
This utility applies only versioned, source-specific and count-locked mappings.
It never rewrites the raw ``pdftotext`` output. In APPLY mode it writes a
canonical text derivative, regenerates parser-owned spans and records a local
repair manifest. PostgreSQL, scientific authority, releases and the CSI Gateway
remain untouched.

Default mode is PLAN. Supply ``--apply`` only after the plan passes.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import stage13_calibrate_local_extraction as common
import stage13_calibrate_local_extraction_v2 as spanlib
import stage13_inspect_parse_controls as diagnostics

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY = (
    REPO_ROOT
    / "components/evidence-registry/config/"
    / "stage13_parse_control_repair_policy.v1.json"
)
DEFAULT_PARSE_POLICY = (
    REPO_ROOT
    / "components/evidence-registry/config/"
    / "stage13_parse_quality_policy.v1.json"
)
DEFAULT_CORPUS_ROOT = Path.home() / "hrp-lab/source-corpus"


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


def write_json_idempotent(path: Path, value: Any) -> None:
    content = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    write_text_idempotent(path, content)


def write_text_idempotent(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="strict")
        if existing != content:
            raise RuntimeError(
                f"Existing derivative differs from proposed content: {path}"
            )
        return
    path.write_text(content, encoding="utf-8")


def latest_batch(corpus_root: Path) -> Path:
    candidates = sorted(
        (corpus_root / "_parsing").glob("stage13-parse-quality-batch-*.json")
    )
    if not candidates:
        raise SystemExit(
            f"No Stage 13 parse-quality batch under {corpus_root / '_parsing'}"
        )
    return candidates[-1]


def parse_codepoint(value: str) -> str:
    match = re.fullmatch(r"U\+([0-9A-Fa-f]{4,6})", value.strip())
    if not match:
        raise ValueError(f"Invalid codepoint label: {value!r}")
    codepoint = int(match.group(1), 16)
    if codepoint < 0 or codepoint > 0x10FFFF:
        raise ValueError(f"Codepoint out of range: {value!r}")
    return chr(codepoint)


def unexpected_control_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for character in text:
        if diagnostics.is_unexpected_control(character):
            label = f"U+{ord(character):04X}"
            counts[label] = counts.get(label, 0) + 1
    return counts


def occurrence_indices(text: str, character: str) -> list[int]:
    return [index for index, value in enumerate(text) if value == character]


def context_matches(
    text: str,
    index: int,
    *,
    previous_regex: str | None,
    following_regex: str | None,
    radius: int,
) -> tuple[bool, str, str]:
    previous = text[max(0, index - radius) : index]
    following = text[index + 1 : min(len(text), index + 1 + radius)]
    previous_ok = (
        True
        if not previous_regex
        else re.search(previous_regex, previous, flags=re.DOTALL) is not None
    )
    following_ok = (
        True
        if not following_regex
        else re.search(following_regex, following, flags=re.DOTALL) is not None
    )
    return previous_ok and following_ok, previous, following


def apply_source_policy(
    *,
    source_id: str,
    raw_text: str,
    source_policy: dict[str, Any],
    context_radius: int = 160,
) -> tuple[str, list[dict[str, Any]]]:
    """Validate and apply one source's explicit control-character mappings."""
    rules = source_policy.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError(f"{source_id}: policy has no rules")

    raw_counts = unexpected_control_counts(raw_text)
    policy_codepoints: set[str] = set()
    results: list[dict[str, Any]] = []
    canonical = raw_text

    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError(f"{source_id}: every rule must be an object")
        rule_id = str(rule.get("rule_id") or "")
        label = str(rule.get("codepoint") or "")
        if not rule_id or not label:
            raise ValueError(f"{source_id}: rule_id and codepoint are required")
        if label in policy_codepoints:
            raise ValueError(
                f"{source_id}: duplicate rule for codepoint {label}"
            )
        policy_codepoints.add(label)
        character = parse_codepoint(label)
        expected = int(rule.get("expected_count", -1))
        indices = occurrence_indices(raw_text, character)
        if len(indices) != expected:
            raise ValueError(
                f"{source_id}:{rule_id}: expected {expected} occurrence(s) of "
                f"{label}; found {len(indices)}"
            )

        context_failures: list[dict[str, Any]] = []
        for index in indices:
            matched, previous, following = context_matches(
                raw_text,
                index,
                previous_regex=(
                    str(rule["previous_context_regex"])
                    if rule.get("previous_context_regex") is not None
                    else None
                ),
                following_regex=(
                    str(rule["following_context_regex"])
                    if rule.get("following_context_regex") is not None
                    else None
                ),
                radius=context_radius,
            )
            if not matched:
                context_failures.append(
                    {
                        "index": index,
                        "previous": previous[-80:].encode(
                            "unicode_escape", errors="backslashreplace"
                        ).decode("ascii"),
                        "following": following[:80].encode(
                            "unicode_escape", errors="backslashreplace"
                        ).decode("ascii"),
                    }
                )
        if context_failures:
            raise ValueError(
                f"{source_id}:{rule_id}: {len(context_failures)} occurrence(s) "
                f"failed the context guard: {context_failures}"
            )

        replacement = str(rule.get("replacement", ""))
        canonical = canonical.replace(character, replacement)
        results.append(
            {
                "rule_id": rule_id,
                "codepoint": label,
                "replacement": replacement,
                "replacement_label": rule.get("replacement_label"),
                "replacement_count": len(indices),
                "interpretation": rule.get("interpretation"),
            }
        )

    ungoverned = sorted(set(raw_counts) - policy_codepoints)
    if ungoverned:
        raise ValueError(
            f"{source_id}: unexpected controls lack an explicit policy: "
            + ", ".join(ungoverned)
        )
    remaining = unexpected_control_counts(canonical)
    if remaining:
        raise ValueError(
            f"{source_id}: unexpected controls remain after repair: {remaining}"
        )
    return canonical, results


def split_pages(text: str) -> list[str]:
    pages = text.split("\f")
    while pages and not pages[-1].strip():
        pages.pop()
    return pages


def selected_rows(
    batch: dict[str, Any],
    policy: dict[str, Any],
    requested: set[str] | None,
) -> list[dict[str, Any]]:
    sources_policy = policy.get("sources")
    if not isinstance(sources_policy, dict):
        raise SystemExit("Repair policy must contain a sources object")
    rows = [row for row in batch.get("sources", []) if isinstance(row, dict)]
    if requested:
        missing_policy = sorted(requested - set(sources_policy))
        if missing_policy:
            raise SystemExit(
                "Requested sources lack a repair policy: "
                + ", ".join(missing_policy)
            )
        selected = [
            row for row in rows if str(row.get("source_id")) in requested
        ]
        found = {str(row.get("source_id")) for row in selected}
        missing_batch = sorted(requested - found)
        if missing_batch:
            raise SystemExit(
                "Requested sources are absent from the parse batch: "
                + ", ".join(missing_batch)
            )
        return selected
    return [
        row
        for row in rows
        if str(row.get("source_id")) in sources_policy
        and "unexpected_control_characters"
        in (row.get("quarantine_reasons") or [])
    ]


def derivative_paths(
    *, source_id: str, raw_path: Path, corpus_root: Path
) -> dict[str, Path]:
    source_root = corpus_root / source_id
    manifest_root = source_root / "manifests" / "stage13-parse-control-repair-v1"
    return {
        "canonical_text": raw_path.with_name(
            f"{raw_path.stem}.canonical-v1{raw_path.suffix}"
        ),
        "spans": manifest_root / "spans.canonical-v1.jsonl",
        "source_manifest": manifest_root / "repair-manifest.json",
    }


def span_jsonl(spans: list[spanlib.Span]) -> str:
    return "".join(
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
        for span in spans
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply source-specific semantic repairs to parsed controls."
    )
    parser.add_argument("--batch-manifest", type=Path)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument(
        "--parse-policy", type=Path, default=DEFAULT_PARSE_POLICY
    )
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument("--source-id", action="append", dest="source_ids")
    parser.add_argument("--context-radius", type=int, default=160)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if args.context_radius < 40:
        raise SystemExit("--context-radius must be at least 40")

    corpus_root = args.corpus_root.expanduser().resolve()
    batch_path = (
        args.batch_manifest.expanduser().resolve()
        if args.batch_manifest
        else latest_batch(corpus_root)
    )
    policy_path = args.policy.expanduser().resolve()
    parse_policy_path = args.parse_policy.expanduser().resolve()
    batch = load_json(batch_path)
    policy = load_json(policy_path)
    parse_policy = load_json(parse_policy_path)
    if batch.get("schema_version") != "stage13-parse-quality-batch-v1":
        raise SystemExit("Unsupported parse-quality batch schema")
    if (
        policy.get("schema_version")
        != "stage13-parse-control-repair-policy-v1"
    ):
        raise SystemExit("Unsupported repair-policy schema")
    if parse_policy.get("schema_version") != "stage13-parse-quality-policy-v1":
        raise SystemExit("Unsupported parse-quality policy schema")

    requested = set(args.source_ids) if args.source_ids else None
    rows = selected_rows(batch, policy, requested)
    if not rows:
        raise SystemExit("No parse-control repair sources selected")

    print("=== STAGE 13 PARSE CONTROL REPAIR ===")
    print(f"mode|{'APPLY' if args.apply else 'PLAN'}")
    print(f"batch_manifest|{batch_path}")
    print(f"repair_policy|{policy_path}")
    print(f"sources_selected|{len(rows)}")

    results: list[dict[str, Any]] = []
    blocked = 0
    written = 0
    spans_written = 0
    policy_sources = policy["sources"]

    for row in rows:
        source_id = str(row["source_id"])
        raw_path = Path(str(row["parsed_text_path"])).expanduser().resolve()
        paths = derivative_paths(
            source_id=source_id, raw_path=raw_path, corpus_root=corpus_root
        )
        result: dict[str, Any] = {
            "source_id": source_id,
            "raw_parsed_text_path": str(raw_path),
            "canonical_text_path": str(paths["canonical_text"]),
            "canonical_span_manifest_path": str(paths["spans"]),
            "status": "blocked",
        }
        try:
            if not raw_path.is_file():
                raise RuntimeError(f"Raw parsed text missing: {raw_path}")
            other_reasons = [
                reason
                for reason in (row.get("quarantine_reasons") or [])
                if reason != "unexpected_control_characters"
            ]
            if other_reasons:
                raise RuntimeError(
                    "Other quarantine reasons remain: " + ", ".join(other_reasons)
                )

            raw_hash_before = common.sha256_file(raw_path)
            raw_text = raw_path.read_text(encoding="utf-8", errors="strict")
            canonical, mapping_results = apply_source_policy(
                source_id=source_id,
                raw_text=raw_text,
                source_policy=policy_sources[source_id],
                context_radius=args.context_radius,
            )
            pages = split_pages(canonical)
            expected_pages = int(
                (row.get("metrics") or {}).get("parsed_page_count") or 0
            )
            if len(pages) != expected_pages:
                raise RuntimeError(
                    f"Canonical page count changed: expected {expected_pages}; "
                    f"found {len(pages)}"
                )
            spans = spanlib.build_spans(
                pages, parse_policy.get("span_generation", {})
            )
            if not spans:
                raise RuntimeError("Canonical derivative produced no spans")

            canonical_hash = common.sha256_bytes(canonical.encode("utf-8"))
            result.update(
                {
                    "status": "repairable",
                    "raw_sha256": raw_hash_before,
                    "canonical_sha256": canonical_hash,
                    "raw_unexpected_controls": unexpected_control_counts(raw_text),
                    "remaining_unexpected_controls": unexpected_control_counts(
                        canonical
                    ),
                    "mappings": mapping_results,
                    "canonical_page_count": len(pages),
                    "canonical_span_count": len(spans),
                    "extraction_eligible_after_repair": True,
                }
            )

            print(
                f"source_plan|{source_id}|status=repairable|"
                f"raw_controls={sum(result['raw_unexpected_controls'].values())}|"
                f"remaining_controls=0|pages={len(pages)}|spans={len(spans)}"
            )
            for mapping in mapping_results:
                replacement_label = mapping.get("replacement_label") or "TEXT"
                print(
                    f"mapping|{source_id}|rule={mapping['rule_id']}|"
                    f"codepoint={mapping['codepoint']}|"
                    f"replacement={replacement_label}|"
                    f"count={mapping['replacement_count']}"
                )

            if args.apply:
                write_text_idempotent(paths["canonical_text"], canonical)
                write_text_idempotent(paths["spans"], span_jsonl(spans))
                raw_hash_after = common.sha256_file(raw_path)
                if raw_hash_after != raw_hash_before:
                    raise RuntimeError("Raw parsed text changed during repair")
                source_manifest = {
                    "schema_version": "stage13-parse-control-repair-result-v1",
                    "policy_id": policy.get("policy_id"),
                    "policy_path": str(policy_path),
                    "policy_sha256": common.sha256_file(policy_path),
                    "source_parse_batch": str(batch_path),
                    "source_id": source_id,
                    "raw_parsed_text_path": str(raw_path),
                    "raw_sha256": raw_hash_before,
                    "canonical_text_path": str(paths["canonical_text"]),
                    "canonical_sha256": canonical_hash,
                    "canonical_span_manifest_path": str(paths["spans"]),
                    "canonical_page_count": len(pages),
                    "canonical_span_count": len(spans),
                    "mappings": mapping_results,
                    "remaining_unexpected_controls": {},
                    "extraction_eligible_after_repair": True,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "governance": {
                        "raw_parsed_text_rewritten": False,
                        "ollama_calls": 0,
                        "registry_mutated": False,
                        "scientific_state_mutated": False,
                        "historical_release_mutated": False,
                        "csi_gateway_mutated": False,
                        "machine_screened_status_created": False,
                        "human_authority_created": False,
                    },
                }
                write_json_idempotent(paths["source_manifest"], source_manifest)
                result["source_manifest_path"] = str(paths["source_manifest"])
                written += 1
                spans_written += 1
        except Exception as exc:
            blocked += 1
            result["error"] = str(exc)
            result["extraction_eligible_after_repair"] = False
            print(f"source_blocked|{source_id}|{exc}")
        results.append(result)

    original_eligible = sum(
        1
        for row in batch.get("sources", [])
        if isinstance(row, dict) and row.get("extraction_eligible") is True
    )
    repaired_eligible = sum(
        1
        for result in results
        if result.get("extraction_eligible_after_repair") is True
    )
    total_eligible = original_eligible + repaired_eligible

    batch_output: Path | None = None
    if args.apply and blocked == 0:
        timestamp = datetime.now(timezone.utc)
        batch_output = (
            corpus_root
            / "_parsing"
            / f"stage13-parse-control-repair-"
            f"{timestamp.strftime('%Y%m%d-%H%M%S')}.json"
        )
        write_json_idempotent(
            batch_output,
            {
                "schema_version": "stage13-parse-control-repair-batch-v1",
                "policy_id": policy.get("policy_id"),
                "policy_path": str(policy_path),
                "policy_sha256": common.sha256_file(policy_path),
                "source_parse_batch": str(batch_path),
                "source_parse_batch_sha256": common.sha256_file(batch_path),
                "generated_at": timestamp.isoformat(),
                "summary": {
                    "selected": len(rows),
                    "repaired": repaired_eligible,
                    "blocked": blocked,
                    "original_extraction_eligible": original_eligible,
                    "total_extraction_eligible_after_repair": total_eligible,
                },
                "sources": results,
                "governance": {
                    "raw_parsed_text_rewritten": False,
                    "ollama_calls": 0,
                    "registry_mutated": False,
                    "scientific_state_mutated": False,
                    "historical_release_mutated": False,
                    "csi_gateway_mutated": False,
                    "machine_screened_status_created": False,
                    "human_authority_created": False,
                },
            },
        )

    print(f"repairable_sources|{repaired_eligible}")
    print(f"blocked_sources|{blocked}")
    print(f"original_extraction_eligible|{original_eligible}")
    print(f"total_extraction_eligible_after_repair|{total_eligible}")
    if batch_output:
        print(f"repair_batch_manifest|{batch_output}")
    print(f"CANONICAL_DERIVATIVES_WRITTEN|{written}")
    print(f"CANONICAL_SPAN_MANIFESTS_WRITTEN|{spans_written}")
    print("RAW_PARSED_TEXT_REWRITTEN|0")
    print("OLLAMA_CALLS|0")
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")

    if blocked:
        status = "REVIEW"
        exit_code = 2
    elif args.apply:
        status = "PASS"
        exit_code = 0
    else:
        status = "PLAN_READY"
        exit_code = 0
    print(f"STAGE 13 PARSE CONTROL REPAIR|{status}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
