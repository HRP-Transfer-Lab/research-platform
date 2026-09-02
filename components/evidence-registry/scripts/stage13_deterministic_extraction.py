#!/usr/bin/env python3
"""Deterministic extraction helpers for Stage 13 evidence ingestion.

The module handles values that ordinary software can resolve more reliably than
an LLM, including explicit identifiers and context-labelled cohort counts. It
never creates scientific authority; callers decide how candidates are used.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable


DEFAULT_INTEGER_REGEX = (
    r"(?<![A-Za-z0-9_.-])"
    r"(?:[1-9]\d{0,2}(?:[ ,]\d{3})+|[1-9]\d{3,5})"
    r"(?![A-Za-z0-9_.-])"
)


@dataclass(frozen=True)
class NumericOccurrence:
    value: int
    score: int
    span_id: str
    pdf_page: int
    start: int
    end: int
    local_context: str
    matched_strong: tuple[str, ...]
    matched_positive: tuple[str, ...]
    matched_negative: tuple[str, ...]
    matched_labels: tuple[str, ...]


def _get(span: Any, field: str) -> Any:
    if isinstance(span, dict):
        return span[field]
    return getattr(span, field)


def normalise(value: str) -> str:
    value = value.casefold().replace("–", "-").replace("—", "-")
    value = re.sub(r"(?<=\w)-\s+(?=\w)", "", value)
    value = re.sub(r"[^a-z0-9%+\-.]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _phrase_matches(text: str, phrases: Iterable[str]) -> tuple[str, ...]:
    haystack = normalise(text)
    return tuple(
        str(phrase)
        for phrase in phrases
        if normalise(str(phrase)) and normalise(str(phrase)) in haystack
    )


def _integer(value: str) -> int:
    return int(re.sub(r"[ ,]", "", value))


def _page_index(spans: list[Any]) -> dict[int, list[Any]]:
    pages: dict[int, list[Any]] = defaultdict(list)
    for span in spans:
        pages[int(_get(span, "pdf_page"))].append(span)
    for rows in pages.values():
        rows.sort(key=lambda row: int(_get(row, "ordinal")))
    return dict(pages)


def unique_regex_candidates(
    spans: list[Any],
    rules: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    diagnostics: dict[str, Any] = {}
    for field, rule in rules.items():
        pattern = re.compile(str(rule["regex"]), re.IGNORECASE)
        matches: list[tuple[str, Any]] = []
        for span in spans:
            found = pattern.search(str(_get(span, "text")))
            if found:
                matches.append((found.group(int(rule.get("group", 0))), span))
        values = sorted({value for value, _ in matches})
        diagnostics[field] = {
            "strategy": "unique_regex",
            "rule_id": rule.get("rule_id"),
            "values": values,
            "matches": [
                {
                    "value": value,
                    "span_id": str(_get(span, "span_id")),
                    "pdf_page": int(_get(span, "pdf_page")),
                }
                for value, span in matches
            ],
        }
        if len(values) != 1:
            continue
        value = values[0]
        output[field] = {
            "value": value,
            "status": "extracted",
            "evidence_span_ids": [
                str(_get(span, "span_id"))
                for matched, span in matches
                if matched == value
            ][: int(rule.get("maximum_evidence_spans", 2))],
            "confidence": 1.0,
        }
        diagnostics[field]["selected_value"] = value
    return output, diagnostics


def contextual_integer_candidates(
    spans: list[Any],
    rules: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Resolve explicit cohort counts using labelled context, not gold values.

    Candidate values are found with a generic integer pattern. The selected
    value is determined from source wording around the number and on the same
    physical PDF page. Rules may prefer the larger value only after contextual
    scoring, which helps distinguish full samples from subgroup tables.
    """
    output: dict[str, dict[str, Any]] = {}
    diagnostics: dict[str, Any] = {}
    pages = _page_index(spans)

    for field, rule in rules.items():
        pattern = re.compile(str(rule.get("number_regex", DEFAULT_INTEGER_REGEX)))
        minimum = int(rule.get("minimum_value", 1))
        maximum = int(rule.get("maximum_value", 10**9))
        exclude_years = bool(rule.get("exclude_years", True))
        window = int(rule.get("local_window_characters", 240))
        strong_weight = int(rule.get("strong_phrase_weight", 18))
        positive_weight = int(rule.get("positive_phrase_weight", 5))
        local_positive_bonus = int(rule.get("local_positive_bonus", 7))
        label_weight = int(rule.get("local_label_weight", 12))
        negative_weight = int(rule.get("negative_phrase_weight", 8))
        local_negative_bonus = int(rule.get("local_negative_bonus", 10))
        min_score = int(rule.get("minimum_score", 10))
        min_margin = int(rule.get("minimum_score_margin", 1))
        prefer_largest = bool(rule.get("prefer_largest_on_tie", True))

        strong_phrases = [str(value) for value in rule.get("strong_positive_phrases", [])]
        positive_phrases = [str(value) for value in rule.get("positive_phrases", [])]
        negative_phrases = [str(value) for value in rule.get("negative_phrases", [])]
        local_labels = [str(value) for value in rule.get("local_count_labels", [])]

        occurrences: list[NumericOccurrence] = []
        for span in spans:
            text = str(_get(span, "text"))
            page = int(_get(span, "pdf_page"))
            page_rows = pages[page]
            page_text = "\n".join(str(_get(row, "text")) for row in page_rows)
            page_strong = _phrase_matches(page_text, strong_phrases)
            page_positive = _phrase_matches(page_text, positive_phrases)
            page_negative = _phrase_matches(page_text, negative_phrases)

            for match in pattern.finditer(text):
                value = _integer(match.group(0))
                if not minimum <= value <= maximum:
                    continue
                if exclude_years and 1900 <= value <= 2100:
                    continue
                start = max(0, match.start() - window)
                end = min(len(text), match.end() + window)
                local = text[start:end]
                local_positive = _phrase_matches(local, positive_phrases)
                local_negative = _phrase_matches(local, negative_phrases)
                local_label_matches = _phrase_matches(local, local_labels)

                score = 0
                score += strong_weight * len(page_strong)
                score += positive_weight * len(page_positive)
                score += local_positive_bonus * len(local_positive)
                score += label_weight * len(local_label_matches)
                score -= negative_weight * len(page_negative)
                score -= local_negative_bonus * len(local_negative)

                # Narrative cohort statements are generally more reliable than
                # an isolated table number. This does not encode any expected
                # sample value.
                narrative = normalise(local)
                if any(token in narrative for token in (
                    "students", "participants", "logged into", "completed",
                    "took the", "taking the", "analysis sample", "sample contained",
                )):
                    score += int(rule.get("narrative_bonus", 8))
                if "observations" in narrative:
                    score += int(rule.get("observations_label_bonus", 4))

                occurrences.append(NumericOccurrence(
                    value=value,
                    score=score,
                    span_id=str(_get(span, "span_id")),
                    pdf_page=page,
                    start=match.start(),
                    end=match.end(),
                    local_context=re.sub(r"\s+", " ", local).strip(),
                    matched_strong=page_strong,
                    matched_positive=tuple(sorted(set(page_positive + local_positive))),
                    matched_negative=tuple(sorted(set(page_negative + local_negative))),
                    matched_labels=local_label_matches,
                ))

        # Retain the best occurrence for each distinct numeric value. Repetition
        # across table columns is deliberately not rewarded.
        best_by_value: dict[int, NumericOccurrence] = {}
        for occurrence in occurrences:
            current = best_by_value.get(occurrence.value)
            key = (
                occurrence.score,
                occurrence.value if prefer_largest else -occurrence.value,
                -occurrence.pdf_page,
            )
            current_key = (
                current.score,
                current.value if prefer_largest else -current.value,
                -current.pdf_page,
            ) if current else None
            if current is None or key > current_key:
                best_by_value[occurrence.value] = occurrence

        ranked = sorted(
            best_by_value.values(),
            key=lambda row: (
                -row.score,
                -row.value if prefer_largest else row.value,
                row.pdf_page,
                row.span_id,
            ),
        )
        top = ranked[0] if ranked else None
        second = ranked[1] if len(ranked) > 1 else None
        margin = top.score - second.score if top and second else None
        selected = bool(
            top
            and top.score >= min_score
            and (second is None or margin is not None and margin >= min_margin)
        )

        diagnostic_rows = [
            {
                "rank": index,
                "value": row.value,
                "score": row.score,
                "span_id": row.span_id,
                "pdf_page": row.pdf_page,
                "matched_strong": list(row.matched_strong),
                "matched_positive": list(row.matched_positive),
                "matched_negative": list(row.matched_negative),
                "matched_labels": list(row.matched_labels),
                "local_context": row.local_context[:700],
            }
            for index, row in enumerate(ranked[: int(rule.get("diagnostic_limit", 12))], start=1)
        ]
        diagnostics[field] = {
            "strategy": "contextual_integer",
            "rule_id": rule.get("rule_id"),
            "minimum_score": min_score,
            "minimum_score_margin": min_margin,
            "prefer_largest_on_tie": prefer_largest,
            "ranked_candidates": diagnostic_rows,
            "selected": selected,
            "selected_value": top.value if selected and top else None,
            "selected_score": top.score if selected and top else None,
            "runner_up_score": second.score if second else None,
            "score_margin": margin,
        }
        if not selected or top is None:
            continue

        evidence_ids = [top.span_id]
        # Add same-page context spans containing strong/positive terminology so
        # support remains inspectable even when a table row and title are split.
        context_ranked = sorted(
            pages[top.pdf_page],
            key=lambda span: (
                -len(_phrase_matches(str(_get(span, "text")), strong_phrases)),
                -len(_phrase_matches(str(_get(span, "text")), positive_phrases)),
                int(_get(span, "ordinal")),
            ),
        )
        for span in context_ranked:
            span_id = str(_get(span, "span_id"))
            if span_id in evidence_ids:
                continue
            text = str(_get(span, "text"))
            if not (
                _phrase_matches(text, strong_phrases)
                or _phrase_matches(text, positive_phrases)
            ):
                continue
            evidence_ids.append(span_id)
            if len(evidence_ids) >= int(rule.get("maximum_evidence_spans", 3)):
                break

        output[field] = {
            "value": top.value,
            "status": "extracted",
            "evidence_span_ids": evidence_ids,
            "confidence": float(rule.get("confidence", 0.98)),
        }
        diagnostics[field]["selected_evidence_span_ids"] = evidence_ids

    return output, diagnostics


def extract_deterministic_candidates(
    spans: list[Any],
    profile: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    regex_candidates, regex_diagnostics = unique_regex_candidates(
        spans, profile.get("deterministic_fields", {})
    )
    numeric_candidates, numeric_diagnostics = contextual_integer_candidates(
        spans, profile.get("contextual_deterministic_fields", {})
    )
    candidates = {**regex_candidates, **numeric_candidates}

    guards: list[dict[str, Any]] = []
    entrants = candidates.get("week1_platform_entrants", {}).get("value")
    completers = candidates.get("delayed_assessment_completers", {}).get("value")
    if isinstance(entrants, int) and isinstance(completers, int):
        valid = 0 <= completers <= entrants
        guards.append({
            "guard": "delayed_completers_not_greater_than_week1_entrants",
            "valid": valid,
            "week1_platform_entrants": entrants,
            "delayed_assessment_completers": completers,
        })
        if not valid:
            candidates.pop("delayed_assessment_completers", None)

    return candidates, {
        "unique_regex": regex_diagnostics,
        "contextual_integer": numeric_diagnostics,
        "cross_field_guards": guards,
    }
