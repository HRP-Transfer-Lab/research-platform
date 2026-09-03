#!/usr/bin/env python3
from __future__ import annotations

import unittest

import stage13_repair_parse_controls as repair


class ParseControlRepairTests(unittest.TestCase):
    def test_running_header_backspace_is_removed_when_context_matches(self) -> None:
        raw = "frontiersin.org\n\fWang et al.\x08                    Article"
        policy = {
            "rules": [
                {
                    "rule_id": "header",
                    "codepoint": "U+0008",
                    "replacement": "",
                    "expected_count": 1,
                    "previous_context_regex": r"Wang et al\.$",
                    "following_context_regex": r"^\s",
                }
            ]
        }
        canonical, results = repair.apply_source_policy(
            source_id="rt-2026-007", raw_text=raw, source_policy=policy
        )
        self.assertEqual(canonical, raw.replace("\x08", ""))
        self.assertEqual(results[0]["replacement_count"], 1)
        self.assertEqual(repair.unexpected_control_counts(canonical), {})

    def test_mediation_control_is_mapped_to_prime(self) -> None:
        raw = "Paths a, b, c, and c\x02 paths; c\x02 (SE); pc\x02 = .995"
        policy = {
            "rules": [
                {
                    "rule_id": "c-prime",
                    "codepoint": "U+0002",
                    "replacement": "′",
                    "expected_count": 3,
                    "previous_context_regex": r"c$",
                    "following_context_regex": r"^(?:\s|\()",
                }
            ]
        }
        canonical, _ = repair.apply_source_policy(
            source_id="rt-2026-015", raw_text=raw, source_policy=policy
        )
        self.assertIn("c′ paths", canonical)
        self.assertIn("c′ (SE)", canonical)
        self.assertIn("pc′ =", canonical)

    def test_model_comparison_control_is_mapped_to_delta(self) -> None:
        raw = "\x04χ 2 = 726.53, \x04df = 10"
        policy = {
            "rules": [
                {
                    "rule_id": "delta",
                    "codepoint": "U+0004",
                    "replacement": "Δ",
                    "expected_count": 2,
                    "previous_context_regex": r".*$",
                    "following_context_regex": r"^(?:χ|df)",
                }
            ]
        }
        canonical, _ = repair.apply_source_policy(
            source_id="rt-2026-018", raw_text=raw, source_policy=policy
        )
        self.assertEqual(canonical, "Δχ 2 = 726.53, Δdf = 10")

    def test_count_mismatch_is_rejected(self) -> None:
        raw = "c\x02 path"
        policy = {
            "rules": [
                {
                    "rule_id": "c-prime",
                    "codepoint": "U+0002",
                    "replacement": "′",
                    "expected_count": 2,
                    "previous_context_regex": r"c$",
                    "following_context_regex": r"^\s",
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, "expected 2 occurrence"):
            repair.apply_source_policy(
                source_id="test", raw_text=raw, source_policy=policy
            )

    def test_context_mismatch_is_rejected(self) -> None:
        raw = "x\x02 path"
        policy = {
            "rules": [
                {
                    "rule_id": "c-prime",
                    "codepoint": "U+0002",
                    "replacement": "′",
                    "expected_count": 1,
                    "previous_context_regex": r"c$",
                    "following_context_regex": r"^\s",
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, "failed the context guard"):
            repair.apply_source_policy(
                source_id="test", raw_text=raw, source_policy=policy
            )

    def test_unregistered_control_codepoint_is_rejected(self) -> None:
        raw = "c\x02 path and unknown \x03 artefact"
        policy = {
            "rules": [
                {
                    "rule_id": "c-prime",
                    "codepoint": "U+0002",
                    "replacement": "′",
                    "expected_count": 1,
                    "previous_context_regex": r"c$",
                    "following_context_regex": r"^\s",
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, "lack an explicit policy"):
            repair.apply_source_policy(
                source_id="test", raw_text=raw, source_policy=policy
            )

    def test_page_splitting_preserves_physical_pages(self) -> None:
        self.assertEqual(repair.split_pages("one\ftwo\f"), ["one", "two"])


if __name__ == "__main__":
    unittest.main()
