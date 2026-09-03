#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import stage13_build_extraction_worklist as worklist


class ExtractionWorklistTests(unittest.TestCase):
    def test_source_family_maps_syntheses(self) -> None:
        self.assertEqual(
            worklist.source_family("systematic_review_meta_analysis"),
            "evidence_synthesis_meta_analysis",
        )
        self.assertEqual(
            worklist.source_family("scoping_review"),
            "evidence_synthesis_scoping_review",
        )
        self.assertEqual(
            worklist.source_family("journal_article"),
            "primary_empirical",
        )

    def test_unexpected_controls_allow_layout_controls(self) -> None:
        self.assertEqual(
            worklist.unexpected_controls("one\n\ttwo\r\n\fthree"),
            [],
        )
        self.assertEqual(
            worklist.unexpected_controls("one\x02two"),
            ["U+0002"],
        )

    def test_parsed_page_count_drops_trailing_empty_page(self) -> None:
        self.assertEqual(worklist.parsed_page_count("one\f two\f"), 2)

    def test_select_raw_derivative(self) -> None:
        row = {
            "source_id": "rt-1",
            "extraction_eligible": True,
            "parsed_text_path": "/tmp/raw.txt",
            "span_manifest_path": "/tmp/spans.jsonl",
            "metrics": {"parsed_page_count": 3, "span_count": 7},
        }
        selected = worklist.select_derivative(row, {})
        self.assertEqual(selected["derivative_kind"], "raw_parse")
        self.assertEqual(selected["expected_page_count"], 3)

    def test_select_repaired_derivative(self) -> None:
        row = {"source_id": "rt-1", "extraction_eligible": False}
        repairs = {
            "rt-1": {
                "extraction_eligible_after_repair": True,
                "canonical_text_path": "/tmp/canonical.txt",
                "canonical_span_manifest_path": "/tmp/spans.jsonl",
                "source_manifest_path": "/tmp/repair.json",
                "canonical_page_count": 2,
                "canonical_span_count": 5,
            }
        }
        selected = worklist.select_derivative(row, repairs)
        self.assertEqual(selected["derivative_kind"], "canonical_repair")
        self.assertEqual(selected["expected_span_count"], 5)

    def test_select_derivative_rejects_unresolved_source(self) -> None:
        with self.assertRaises(RuntimeError):
            worklist.select_derivative(
                {"source_id": "rt-1", "extraction_eligible": False},
                {},
            )

    def test_span_manifest_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spans.jsonl"
            text = "Supported evidence."
            row = {
                "span_id": "p001-s001",
                "pdf_page": 1,
                "ordinal": 1,
                "text": text,
                "text_sha256": hashlib.sha256(
                    text.encode("utf-8")
                ).hexdigest(),
            }
            path.write_text(
                json.dumps(row) + "\n",
                encoding="utf-8",
            )
            count, errors = worklist.load_and_validate_spans(
                path, page_count=1
            )
            self.assertEqual(count, 1)
            self.assertEqual(errors, [])

    def test_span_manifest_rejects_bad_hash_and_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spans.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "span_id": "p002-s001",
                        "pdf_page": 2,
                        "ordinal": 1,
                        "text": "Evidence.",
                        "text_sha256": "0" * 64,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            count, errors = worklist.load_and_validate_spans(
                path, page_count=1
            )
            self.assertEqual(count, 1)
            self.assertIn("line_1:text_hash_mismatch", errors)
            self.assertIn("line_1:bad_pdf_page:2", errors)


if __name__ == "__main__":
    unittest.main()
