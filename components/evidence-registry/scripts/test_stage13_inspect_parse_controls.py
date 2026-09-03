#!/usr/bin/env python3
from __future__ import annotations

import unittest

import stage13_inspect_parse_controls as diagnostic


class ParseControlDiagnosticsTests(unittest.TestCase):
    def test_allowed_layout_controls_are_not_flagged(self) -> None:
        text = "page one\n\trow\r\n\fpage two"
        result = diagnostic.inspect_text(
            text, context_radius=10, max_contexts=2
        )
        self.assertEqual(result["unexpected_control_count"], 0)
        self.assertEqual(result["disposition"], "no_unexpected_controls")

    def test_separator_control_is_normalisation_candidate(self) -> None:
        result = diagnostic.inspect_text(
            "alpha \x0b beta", context_radius=10, max_contexts=2
        )
        self.assertEqual(result["unexpected_control_count"], 1)
        self.assertEqual(result["inside_alphanumeric_token_count"], 0)
        self.assertEqual(
            result["disposition"], "separator_normalisation_candidate"
        )
        self.assertEqual(result["codepoints"][0]["codepoint"], "U+000B")

    def test_control_inside_word_requires_context_review(self) -> None:
        result = diagnostic.inspect_text(
            "evi\x0bdence", context_radius=10, max_contexts=2
        )
        self.assertEqual(result["inside_alphanumeric_token_count"], 1)
        self.assertEqual(
            result["disposition"], "inspect_before_normalisation"
        )

    def test_null_requires_manual_reparse(self) -> None:
        result = diagnostic.inspect_text(
            "alpha\x00beta", context_radius=10, max_contexts=2
        )
        self.assertTrue(result["contains_null"])
        self.assertEqual(result["disposition"], "manual_reparse_required")

    def test_source_position_tracks_pages_and_lines(self) -> None:
        text = "one\ntwo\fthree\nfour\x0b"
        index = text.index("\x0b")
        self.assertEqual(diagnostic.source_position(text, index), (2, 2))

    def test_default_row_selection_uses_control_flag(self) -> None:
        batch = {
            "sources": [
                {
                    "source_id": "a",
                    "quarantine_reasons": ["unexpected_control_characters"],
                },
                {"source_id": "b", "quarantine_reasons": []},
            ]
        }
        rows = diagnostic.select_rows(batch, None)
        self.assertEqual([row["source_id"] for row in rows], ["a"])


if __name__ == "__main__":
    unittest.main()
