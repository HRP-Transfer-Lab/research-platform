#!/usr/bin/env python3
from __future__ import annotations

import unittest

import stage13_health_psychology_scope as scope
import stage13_health_psychology_scope_strict as strict


class StrictHealthPrefilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = scope.load_json(scope.DEFAULT_POLICY)
        self.config = {
            "query_families": [
                {"query_id": "w", "csi_domain": "performance_work"},
                {"query_id": "p", "csi_domain": "personal"},
                {"query_id": "h", "csi_domain": "health_clinical_adjacent"},
            ]
        }

    def test_cross_domain_occupational_therapy_false_positive_is_removed(self) -> None:
        candidate = {
            "candidate_id": "kidney-ot",
            "title": (
                "Occupational Therapy Services Provided to Adults Diagnosed "
                "With Kidney Disease: A Scoping Review"
            ),
            "abstract": (
                "This scoping review describes occupational therapy services, "
                "daily activities and quality of life in kidney disease."
            ),
            "query_hits": [
                {"query_id": "w"},
                {"query_id": "p"},
                {"query_id": "h"},
            ],
            "deterministic_relevance_score": 10,
        }
        selected, excluded, counts = strict.strict_filter_candidates(
            {"candidates": [candidate]},
            config=self.config,
            policy=self.policy,
            target=1,
        )
        self.assertEqual(selected, [])
        self.assertEqual(len(excluded), 1)
        self.assertEqual(counts["general_medical_cross_domain_excluded"], 1)

    def test_explicit_psychological_health_intervention_is_retained(self) -> None:
        candidate = {
            "candidate_id": "pain-cbt",
            "title": "Cognitive behavioural therapy for chronic pain: a trial",
            "abstract": (
                "Adults with chronic pain received a psychological intervention "
                "using cognitive behavioural therapy."
            ),
            "query_hits": [{"query_id": "h"}],
            "deterministic_relevance_score": 10,
        }
        selected, excluded, counts = strict.strict_filter_candidates(
            {"candidates": [candidate]},
            config=self.config,
            policy=self.policy,
            target=1,
        )
        self.assertEqual(len(selected), 1)
        self.assertEqual(excluded, [])
        self.assertEqual(counts["health_qualified"], 1)


if __name__ == "__main__":
    unittest.main()
