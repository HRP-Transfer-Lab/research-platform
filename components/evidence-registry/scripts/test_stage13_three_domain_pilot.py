#!/usr/bin/env python3
from __future__ import annotations

import unittest

import stage13_classify_csi_domain_candidates as domains


class ThreeDomainClassifierTests(unittest.TestCase):
    def valid_record(self) -> dict:
        return {
            "screening_decision": "include",
            "psychology_intervention_relevant": True,
            "paper_role": "direct_intervention",
            "study_design": "randomised_controlled_trial",
            "intervention_families": ["stress_emotion_resilience"],
            "candidate_routes": ["regulate"],
            "constraint_loci": ["capacity", "coupling"],
            "population_summary": "Employees",
            "intervention_summary": "A workplace resilience intervention",
            "comparator_summary": "Usual practice",
            "outcome_families": [
                "mental_health_wellbeing",
                "work_or_organisational_performance",
            ],
            "transfer_signals": ["real_world_niche"],
            "evidence_unit_ids": ["t000", "a001"],
            "abstract_only_confidence": 0.82,
            "fulltext_priority": "high",
            "exclusion_reason": "not_excluded",
            "missing_for_fulltext": ["risk_of_bias_information"],
            "screening_rationale": "Relevant workplace intervention.",
            "primary_csi_domain": "performance_work",
            "csi_domains": ["performance_work"],
            "application_targets": [
                "work_wellbeing_resilience",
                "work_motivation_engagement",
            ],
            "health_scope": "non_health",
        }

    def test_query_domain_map_covers_configured_queries(self) -> None:
        config = {
            "query_families": [
                {"query_id": "w", "csi_domain": "performance_work"},
                {"query_id": "p", "csi_domain": "personal"},
                {
                    "query_id": "h",
                    "csi_domain": "health_clinical_adjacent",
                },
            ]
        }
        self.assertEqual(
            set(domains.query_domain_map(config).values()),
            domains.CSI_DOMAINS,
        )

    def test_query_origin_domains_are_deduplicated(self) -> None:
        candidate = {
            "query_hits": [
                {"query_id": "w1"},
                {"query_id": "w2"},
                {"query_id": "h1"},
            ]
        }
        mapping = {
            "w1": "performance_work",
            "w2": "performance_work",
            "h1": "health_clinical_adjacent",
        }
        self.assertEqual(
            domains.query_origin_domains(candidate, mapping),
            ["health_clinical_adjacent", "performance_work"],
        )

    def test_valid_work_record_passes(self) -> None:
        errors = domains.validate_classification(
            self.valid_record(),
            allowed_unit_ids={"t000", "a001"},
        )
        self.assertEqual(errors, [])

    def test_health_domain_requires_health_scope(self) -> None:
        value = self.valid_record()
        value["primary_csi_domain"] = "health_clinical_adjacent"
        value["csi_domains"] = ["health_clinical_adjacent"]
        errors = domains.validate_classification(
            value,
            allowed_unit_ids={"t000", "a001"},
        )
        self.assertIn("health_domain_requires_health_scope", errors)

    def test_cross_domain_requires_two_domains(self) -> None:
        value = self.valid_record()
        value["primary_csi_domain"] = "cross_domain"
        errors = domains.validate_classification(
            value,
            allowed_unit_ids={"t000", "a001"},
        )
        self.assertIn("cross_domain_requires_multiple_domains", errors)

    def test_excluded_record_uses_not_applicable_domain_fields(self) -> None:
        value = self.valid_record()
        value.update(
            {
                "screening_decision": "exclude",
                "psychology_intervention_relevant": False,
                "paper_role": "not_relevant",
                "fulltext_priority": "not_applicable",
                "exclusion_reason": "not_intervention_relevant",
                "primary_csi_domain": "not_applicable",
                "csi_domains": ["not_applicable"],
                "application_targets": ["not_applicable"],
                "health_scope": "not_applicable",
            }
        )
        errors = domains.validate_classification(
            value,
            allowed_unit_ids={"t000", "a001"},
        )
        self.assertEqual(errors, [])

    def test_scaled_minimums_make_smoke_test_three_domain(self) -> None:
        minimums = domains.scaled_minimums(
            {
                "performance_work": 20,
                "personal": 20,
                "health_clinical_adjacent": 20,
            },
            classified_count=3,
            configured_classification_target=100,
        )
        self.assertEqual(
            minimums,
            {
                "health_clinical_adjacent": 1,
                "performance_work": 1,
                "personal": 1,
            },
        )

    def test_balanced_portfolio_assigns_each_domain(self) -> None:
        rows = []
        for index, domain in enumerate(
            ["performance_work", "personal", "health_clinical_adjacent"],
            start=1,
        ):
            value = self.valid_record()
            value["primary_csi_domain"] = domain
            value["csi_domains"] = [domain]
            value["health_scope"] = (
                "health_clinical_adjacent"
                if domain == "health_clinical_adjacent"
                else "non_health"
            )
            rows.append(
                {
                    "ranking_score": 100 - index,
                    "candidate": {"candidate_id": f"c{index}"},
                    "classification": value,
                }
            )
        portfolio, assigned = domains.balanced_domain_portfolio(
            rows,
            target=3,
            minimums={domain: 1 for domain in domains.CSI_DOMAINS},
        )
        self.assertEqual(len(portfolio), 3)
        self.assertEqual(set(assigned.values()), {1})


if __name__ == "__main__":
    unittest.main()
