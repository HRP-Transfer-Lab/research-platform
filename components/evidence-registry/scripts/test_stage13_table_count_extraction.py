#!/usr/bin/env python3
"""Unit tests for Stage 13 table-scoped deterministic count extraction."""
from __future__ import annotations

import unittest

import stage13_table_count_extraction as subject


class TableScopedIntegerExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spans = [
            {
                "span_id": "p036-s001",
                "pdf_page": 36,
                "ordinal": 1,
                "text": "Table 4: Exercise 1 and Exercise 2 Outcomes by Mastery Status and AI Assignment",
            },
            {
                "span_id": "p036-s002",
                "pdf_page": 36,
                "ordinal": 2,
                "text": "Panel A. Exercise 1 Observations 6,997 6,997 6,997 6,997 Panel B. Exercise 2 Observations 6,997 6,997 6,997 6,997",
            },
            {
                "span_id": "p036-s003",
                "pdf_page": 36,
                "ordinal": 3,
                "text": "The sample was recorded as logging into the week-1 NUMI activity and forms the final week-1 analysis sample.",
            },
            {
                "span_id": "p038-s001",
                "pdf_page": 38,
                "ordinal": 1,
                "text": "Table 5: Main Delayed-Test Learning Effects",
            },
            {
                "span_id": "p038-s002",
                "pdf_page": 38,
                "ordinal": 2,
                "text": "Observations 6,327 6,327 6,327 6,327 6,327",
            },
            {
                "span_id": "p038-s003",
                "pdf_page": 38,
                "ordinal": 3,
                "text": "The sample includes students taking the week-2 delayed assessment and is the delayed-test outcome analysis sample.",
            },
            {
                "span_id": "p063-s001",
                "pdf_page": 63,
                "ordinal": 1,
                "text": "Table A13: Robustness of Attempt-by-Attempt AI Effects on Mistakes Among Mastery Students",
            },
            {
                "span_id": "p063-s002",
                "pdf_page": 63,
                "ordinal": 2,
                "text": "Panel C. Demographic + test-score sample Observations 2,503 2,503 2,503 2,503 2,503",
            },
            {
                "span_id": "p063-s003",
                "pdf_page": 63,
                "ordinal": 3,
                "text": "These are robustness checks in a restricted mastery and test-score sample.",
            },
        ]

    def test_main_week1_table_beats_appendix_subgroup(self) -> None:
        rules = {
            "week1_platform_entrants": {
                "rule_id": "main-week1-itt-table-observations-v1",
                "table_heading_phrases": [
                    "Table 4: Exercise 1 and Exercise 2 Outcomes by Mastery Status and AI Assignment"
                ],
                "row_labels": ["Observations"],
                "evidence_context_phrases": ["week-1 NUMI activity"],
                "minimum_value": 1000,
                "maximum_value": 20000,
                "minimum_repetitions": 3,
                "minimum_frequency_margin": 2,
                "maximum_evidence_spans": 5,
            }
        }
        candidates, diagnostics = subject.table_scoped_integer_candidates(
            self.spans, rules
        )
        self.assertEqual(candidates["week1_platform_entrants"]["value"], 6997)
        self.assertEqual(
            diagnostics["week1_platform_entrants"]["selected_page"], 36
        )
        self.assertIn(
            "p036-s003",
            candidates["week1_platform_entrants"]["evidence_span_ids"],
        )

    def test_main_delayed_table_resolves_complete_case_count(self) -> None:
        rules = {
            "delayed_assessment_completers": {
                "rule_id": "main-delayed-test-table-observations-v1",
                "table_heading_phrases": [
                    "Table 5: Main Delayed-Test Learning Effects"
                ],
                "row_labels": ["Observations"],
                "evidence_context_phrases": ["week-2 delayed assessment"],
                "minimum_value": 1000,
                "maximum_value": 20000,
                "minimum_repetitions": 3,
                "minimum_frequency_margin": 2,
                "maximum_evidence_spans": 5,
            }
        }
        candidates, diagnostics = subject.table_scoped_integer_candidates(
            self.spans, rules
        )
        self.assertEqual(
            candidates["delayed_assessment_completers"]["value"], 6327
        )
        self.assertEqual(
            diagnostics["delayed_assessment_completers"]["selected_page"], 38
        )
        self.assertIn(
            "p038-s003",
            candidates["delayed_assessment_completers"]["evidence_span_ids"],
        )

    def test_subgroup_table_cannot_qualify_without_allowed_heading(self) -> None:
        rules = {
            "week1_platform_entrants": {
                "table_heading_phrases": ["Table 4: Missing Main Table"],
                "row_labels": ["Observations"],
                "minimum_value": 1000,
                "maximum_value": 20000,
                "minimum_repetitions": 3,
                "minimum_frequency_margin": 2,
            }
        }
        candidates, diagnostics = subject.table_scoped_integer_candidates(
            self.spans, rules
        )
        self.assertNotIn("week1_platform_entrants", candidates)
        self.assertFalse(diagnostics["week1_platform_entrants"]["selected"])


if __name__ == "__main__":
    unittest.main()
