#!/usr/bin/env python3
from __future__ import annotations

import unittest

import stage13_parse_quality_batch as parseq


POLICY = {
    "thresholds": {
        "minimum_nonempty_page_ratio": 0.8,
        "maximum_low_text_page_ratio": 0.45,
        "minimum_total_text_characters": 4000,
        "minimum_median_page_characters": 200,
        "maximum_replacement_character_rate": 0.002,
        "minimum_alphabetic_character_ratio": 0.25,
        "require_database_hash_match": True,
        "require_database_page_count_match": True,
        "require_physical_page_alignment": True,
        "require_identity_match_for_admission": True,
    }
}


def good_metrics() -> dict[str, object]:
    return {
        "parsed_page_count": 20,
        "nonempty_page_count": 20,
        "nonempty_page_ratio": 1.0,
        "low_text_page_count": 1,
        "low_text_page_ratio": 0.05,
        "total_text_characters": 50000,
        "visible_characters": 42000,
        "median_page_characters": 1800,
        "minimum_page_characters_observed": 40,
        "maximum_page_characters_observed": 5000,
        "alphabetic_character_ratio": 0.72,
        "replacement_character_count": 0,
        "replacement_character_rate": 0.0,
        "unexpected_control_character_count": 0,
        "span_count": 80,
        "median_span_characters": 850,
        "maximum_span_characters": 1390,
    }


def good_checks() -> dict[str, bool]:
    return {
        "database_hash_match": True,
        "database_page_count_match": True,
        "physical_page_alignment": True,
        "identity_match": True,
    }


class ParseQualityAdmissionTests(unittest.TestCase):
    def test_good_born_digital_parse_passes(self) -> None:
        result = parseq.assess_quality(
            metrics=good_metrics(),
            checks=good_checks(),
            pdf_info={"Encrypted": "no"},
            policy=POLICY,
        )
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["extraction_eligible"])
        self.assertEqual(result["quarantine_reasons"], [])

    def test_hash_mismatch_is_hard_failure(self) -> None:
        checks = good_checks()
        checks["database_hash_match"] = False
        result = parseq.assess_quality(
            metrics=good_metrics(),
            checks=checks,
            pdf_info={"Encrypted": "no"},
            policy=POLICY,
        )
        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["extraction_eligible"])
        self.assertIn("database_hash_mismatch", result["failure_reasons"])

    def test_physical_page_misalignment_is_hard_failure(self) -> None:
        checks = good_checks()
        checks["physical_page_alignment"] = False
        result = parseq.assess_quality(
            metrics=good_metrics(),
            checks=checks,
            pdf_info={"Encrypted": "no"},
            policy=POLICY,
        )
        self.assertEqual(result["status"], "fail")
        self.assertIn(
            "physical_page_alignment_failed", result["failure_reasons"]
        )

    def test_identity_failure_is_quarantined_for_review(self) -> None:
        checks = good_checks()
        checks["identity_match"] = False
        result = parseq.assess_quality(
            metrics=good_metrics(),
            checks=checks,
            pdf_info={"Encrypted": "no"},
            policy=POLICY,
        )
        self.assertEqual(result["status"], "review")
        self.assertFalse(result["extraction_eligible"])
        self.assertIn(
            "parsed_identity_not_confirmed", result["review_reasons"]
        )

    def test_low_text_parse_is_ocr_candidate(self) -> None:
        metrics = good_metrics()
        metrics.update(
            {
                "nonempty_page_ratio": 0.4,
                "low_text_page_ratio": 0.8,
                "total_text_characters": 1000,
                "median_page_characters": 50,
                "span_count": 3,
            }
        )
        result = parseq.assess_quality(
            metrics=metrics,
            checks=good_checks(),
            pdf_info={"Encrypted": "no"},
            policy=POLICY,
        )
        self.assertEqual(result["status"], "review")
        self.assertTrue(result["ocr_candidate"])
        self.assertFalse(result["extraction_eligible"])

    def test_replacement_character_damage_is_reviewed(self) -> None:
        metrics = good_metrics()
        metrics["replacement_character_rate"] = 0.01
        result = parseq.assess_quality(
            metrics=metrics,
            checks=good_checks(),
            pdf_info={"Encrypted": "no"},
            policy=POLICY,
        )
        self.assertEqual(result["status"], "review")
        self.assertIn(
            "high_replacement_character_rate", result["review_reasons"]
        )

    def test_requested_source_filter_rejects_unverified_source(self) -> None:
        rows = [{"source_id": "rt-2026-009"}]
        with self.assertRaises(SystemExit):
            parseq.select_sources(rows, {"rt-2026-006"})


if __name__ == "__main__":
    unittest.main()
