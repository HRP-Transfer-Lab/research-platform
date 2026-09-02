#!/usr/bin/env python3
"""Table-scoped deterministic integer extraction for Stage 13.

This module resolves explicit counts only when a configured table heading and
row label are present on the same physical PDF page. It is designed to avoid a
common evidence-extraction error: selecting a plausible subgroup N from an
appendix or robustness table instead of the study-level analysis population.

Rules contain semantic table/row labels, never expected numeric answers. The
module creates candidates only; it cannot create human authority or mutate the
Registry.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any


DEFAULT_INTEGER_REGEX = (
    r"(?<![A-Za-z0-9_.-])"
    r"(?:[1-9]\d{0,2}(?:[ ,]\d{3})+|[1-9]\d{3,5})"
    r"(?![A-Za-z0-9_.-])"
)


def _get(span: Any, field: str) -> Any:
    if isinstance(span, dict):
        return span[field]
    return getattr(span, field)


def normalise(value: str) -> str:
    value = value.casefold().replace("–", "-").replace("—", "-")
    value = re.sub(r"(?<=\w)-\s+(?=\w)", "", value)
    value = re.sub(r"[^a-z0-9%+\-.]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _integer(value: str) -> int:
    return int(re.sub(r"[ ,]", "", value))


def _page_index(spans: list[Any]) -> dict[int, list[Any]]:
    pages: dict[int, list[Any]] = defaultdict(list)
    for span in spans:
        pages[int(_get(span, "pdf_page"))].append(span)
    for rows in pages.values():
        rows.sort(key=lambda row: int(_get(row, "ordinal")))
    return dict(pages)


def _contains_phrase(text: str, phrase: str) -> bool:
    needle = normalise(phrase)
    return bool(needle and needle in normalise(text))


def _value_forms(value: int) -> tuple[str, ...]:
    return (str(value), f"{value:,}", f"{value:,}".replace(",", " "))


def table_scoped_integer_candidates(
    spans: list[Any],
    rules: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Resolve counts from heading-scoped table rows.

    A candidate is emitted only when:

    * the physical PDF page contains an allowed table heading;
    * a configured row label occurs after that heading;
    * one integer dominates the row window with the required repetition; and
    * any configured exclusion phrase is absent from the heading page.

    The configured headings describe the semantic role of the table, not the
    expected count. This keeps the resolver inspectable without leaking gold
    numeric values into candidate generation.
    """
    pages = _page_index(spans)
    output: dict[str, dict[str, Any]] = {}
    diagnostics: dict[str, Any] = {}

    for field, rule in rules.items():
        headings = [str(value) for value in rule.get("table_heading_phrases", [])]
        row_labels = [str(value) for value in rule.get("row_labels", ["observations"])]
        exclusions = [str(value) for value in rule.get("exclude_page_phrases", [])]
        number_pattern = re.compile(str(rule.get("number_regex", DEFAULT_INTEGER_REGEX)))
        minimum = int(rule.get("minimum_value", 1))
        maximum = int(rule.get("maximum_value", 10**9))
        exclude_years = bool(rule.get("exclude_years", True))
        row_window = int(rule.get("row_window_characters", 500))
        minimum_repetitions = int(rule.get("minimum_repetitions", 2))
        minimum_margin = int(rule.get("minimum_frequency_margin", 1))
        maximum_evidence_spans = int(rule.get("maximum_evidence_spans", 4))

        page_candidates: list[dict[str, Any]] = []
        for page_number, page_spans in pages.items():
            page_text = "\n".join(str(_get(span, "text")) for span in page_spans)
            normalised_page = normalise(page_text)
            heading_matches = [
                heading for heading in headings if _contains_phrase(page_text, heading)
            ]
            if not heading_matches:
                continue
            exclusion_matches = [
                phrase for phrase in exclusions if _contains_phrase(page_text, phrase)
            ]
            if exclusion_matches:
                page_candidates.append({
                    "pdf_page": page_number,
                    "heading_matches": heading_matches,
                    "excluded": True,
                    "exclusion_matches": exclusion_matches,
                })
                continue

            for row_label in row_labels:
                normalised_label = normalise(row_label)
                start = 0
                while True:
                    label_index = normalised_page.find(normalised_label, start)
                    if label_index < 0:
                        break
                    row_text = normalised_page[
                        label_index + len(normalised_label):
                        label_index + len(normalised_label) + row_window
                    ]
                    values: list[int] = []
                    for match in number_pattern.finditer(row_text):
                        value = _integer(match.group(0))
                        if not minimum <= value <= maximum:
                            continue
                        if exclude_years and 1900 <= value <= 2100:
                            continue
                        values.append(value)
                    frequencies = Counter(values)
                    ranked = sorted(
                        frequencies.items(), key=lambda item: (-item[1], -item[0])
                    )
                    top_value, top_frequency = ranked[0] if ranked else (None, 0)
                    second_frequency = ranked[1][1] if len(ranked) > 1 else 0
                    frequency_margin = top_frequency - second_frequency
                    qualifies = bool(
                        top_value is not None
                        and top_frequency >= minimum_repetitions
                        and frequency_margin >= minimum_margin
                    )
                    page_candidates.append({
                        "pdf_page": page_number,
                        "heading_matches": heading_matches,
                        "excluded": False,
                        "row_label": row_label,
                        "row_values": values,
                        "ranked_frequencies": [
                            {"value": value, "frequency": frequency}
                            for value, frequency in ranked[:10]
                        ],
                        "selected_value": top_value if qualifies else None,
                        "selected_frequency": top_frequency,
                        "runner_up_frequency": second_frequency,
                        "frequency_margin": frequency_margin,
                        "qualifies": qualifies,
                    })
                    start = label_index + len(normalised_label)

        qualifying = [row for row in page_candidates if row.get("qualifies")]
        qualifying.sort(
            key=lambda row: (
                -len(row.get("heading_matches", [])),
                -int(row.get("selected_frequency", 0)),
                -int(row.get("frequency_margin", 0)),
                int(row.get("pdf_page", 0)),
            )
        )

        selected_row = qualifying[0] if qualifying else None
        ambiguous = bool(
            len(qualifying) > 1
            and qualifying[0].get("selected_value")
            != qualifying[1].get("selected_value")
            and (
                len(qualifying[0].get("heading_matches", [])),
                qualifying[0].get("selected_frequency"),
                qualifying[0].get("frequency_margin"),
            )
            == (
                len(qualifying[1].get("heading_matches", [])),
                qualifying[1].get("selected_frequency"),
                qualifying[1].get("frequency_margin"),
            )
        )

        diagnostics[field] = {
            "strategy": "table_scoped_repeated_integer",
            "rule_id": rule.get("rule_id"),
            "minimum_repetitions": minimum_repetitions,
            "minimum_frequency_margin": minimum_margin,
            "page_candidates": page_candidates,
            "selected": bool(selected_row and not ambiguous),
            "ambiguous": ambiguous,
            "selected_value": (
                selected_row.get("selected_value")
                if selected_row and not ambiguous
                else None
            ),
            "selected_page": (
                selected_row.get("pdf_page")
                if selected_row and not ambiguous
                else None
            ),
        }
        if not selected_row or ambiguous:
            continue

        selected_value = int(selected_row["selected_value"])
        selected_page = int(selected_row["pdf_page"])
        page_spans = pages[selected_page]
        evidence_ids: list[str] = []

        # Prefer spans carrying the table heading, row label and selected value.
        for span in page_spans:
            text = str(_get(span, "text"))
            carries_heading = any(_contains_phrase(text, phrase) for phrase in headings)
            carries_label = any(_contains_phrase(text, label) for label in row_labels)
            carries_value = any(form in text for form in _value_forms(selected_value))
            if carries_heading or carries_label or carries_value:
                evidence_ids.append(str(_get(span, "span_id")))
            if len(evidence_ids) >= maximum_evidence_spans:
                break

        # The candidate is not admissible without inspectable parser-owned spans.
        if not evidence_ids:
            diagnostics[field]["selected"] = False
            diagnostics[field]["reason"] = "no_evidence_spans"
            continue

        output[field] = {
            "value": selected_value,
            "status": "extracted",
            "evidence_span_ids": evidence_ids,
            "confidence": float(rule.get("confidence", 0.995)),
        }
        diagnostics[field]["selected_evidence_span_ids"] = evidence_ids

    return output, diagnostics
