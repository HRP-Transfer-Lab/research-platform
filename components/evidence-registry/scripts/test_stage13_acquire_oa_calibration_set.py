#!/usr/bin/env python3
from __future__ import annotations

import unittest

import stage13_acquire_oa_calibration_set as acquire


class Stage13AcquisitionGuardTests(unittest.TestCase):
    def test_normalises_doi_url(self) -> None:
        self.assertEqual(
            acquire.normalise_doi(
                "https://doi.org/10.3389/FPSYG.2026.1903040"
            ),
            "10.3389/fpsyg.2026.1903040",
        )

    def test_identity_accepts_exact_doi(self) -> None:
        result = acquire.identity_check(
            text="Published as doi: 10.3389/fpsyg.2026.1903040",
            expected_title="Completely different title",
            expected_doi="10.3389/fpsyg.2026.1903040",
            minimum_title_coverage=0.6,
        )
        self.assertTrue(result["passed"])
        self.assertTrue(result["doi_match"])

    def test_identity_accepts_sufficient_title_coverage(self) -> None:
        title = (
            "Stress drives the hippocampus to prioritize statistical "
            "prediction over episodic encoding"
        )
        result = acquire.identity_check(
            text=(
                "STRESS DRIVES THE HIPPOCAMPUS TO PRIORITIZE STATISTICAL "
                "PREDICTION OVER EPISODIC ENCODING"
            ),
            expected_title=title,
            expected_doi="10.0000/not-present",
            minimum_title_coverage=0.6,
        )
        self.assertTrue(result["passed"])
        self.assertTrue(result["title_match"])

    def test_identity_rejects_unrelated_document(self) -> None:
        result = acquire.identity_check(
            text="An unrelated article about coastal geology and weather systems.",
            expected_title=(
                "Stress drives the hippocampus to prioritize statistical "
                "prediction over episodic encoding"
            ),
            expected_doi="10.1098/rstb.2025.0238",
            minimum_title_coverage=0.6,
        )
        self.assertFalse(result["passed"])

    def test_repository_candidate_mapping(self) -> None:
        route, channel, licence = acquire.candidate_access(
            {
                "provider": "europe_pmc",
                "host_type": "repository",
                "license": None,
            }
        )
        self.assertEqual(
            (route, channel, licence),
            ("repository", "europe_pmc", "unknown"),
        )

    def test_publisher_cc_candidate_mapping(self) -> None:
        route, channel, licence = acquire.candidate_access(
            {
                "provider": "unpaywall",
                "host_type": "publisher",
                "license": "cc-by",
            }
        )
        self.assertEqual(
            (route, channel, licence),
            ("open_access", "unpaywall", "open"),
        )

    def test_non_cc_free_to_read_candidate_does_not_claim_open_licence(self) -> None:
        route, channel, licence = acquire.candidate_access(
            {
                "provider": "unpaywall",
                "host_type": "publisher",
                "license": "other-oa",
            }
        )
        self.assertEqual(
            (route, channel, licence),
            ("open_access", "unpaywall", "unknown"),
        )


if __name__ == "__main__":
    unittest.main()
