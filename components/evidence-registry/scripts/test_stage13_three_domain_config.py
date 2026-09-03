#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = (
    REPO_ROOT
    / "components/evidence-registry/config/"
    / "stage13_overnight_psychology_search.v1.json"
)


class ThreeDomainConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    def test_three_domains_are_defined(self) -> None:
        domains = {
            row["domain_id"]
            for row in self.config["csi_domains"]
        }
        self.assertEqual(
            domains,
            {
                "performance_work",
                "personal",
                "health_clinical_adjacent",
            },
        )

    def test_five_queries_are_allocated_to_each_domain(self) -> None:
        counts = Counter(
            row["csi_domain"] for row in self.config["query_families"]
        )
        self.assertEqual(
            counts,
            Counter(
                {
                    "performance_work": 5,
                    "personal": 5,
                    "health_clinical_adjacent": 5,
                }
            ),
        )

    def test_query_order_is_interleaved(self) -> None:
        domains = [
            row["csi_domain"] for row in self.config["query_families"]
        ]
        expected_cycle = [
            "performance_work",
            "personal",
            "health_clinical_adjacent",
        ]
        for index, domain in enumerate(domains):
            self.assertEqual(domain, expected_cycle[index % 3])

    def test_classification_targets_total_one_hundred(self) -> None:
        total = sum(
            int(row["classification_target"])
            for row in self.config["csi_domains"]
        )
        self.assertEqual(total, 100)
        self.assertEqual(self.config["classification_target"], 100)

    def test_full_run_shortlist_minimums_cover_sixty_candidates(self) -> None:
        minimums = self.config["domain_shortlist_minimums"]
        self.assertEqual(set(minimums.values()), {20})
        self.assertEqual(sum(minimums.values()), 60)
        self.assertLessEqual(
            sum(minimums.values()),
            self.config["domain_shortlist_target"],
        )


if __name__ == "__main__":
    unittest.main()
