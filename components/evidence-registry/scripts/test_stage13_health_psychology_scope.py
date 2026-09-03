#!/usr/bin/env python3
from __future__ import annotations

import unittest

import stage13_enforce_psychology_health_classifications as enforce
import stage13_health_psychology_scope as scope


class HealthPsychologyScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = scope.load_json(scope.DEFAULT_POLICY)

    def test_general_kidney_occupational_therapy_review_is_excluded(self) -> None:
        candidate = {
            "title": (
                "Occupational Therapy Services Provided to Adults Diagnosed "
                "With Kidney Disease: A Scoping Review"
            ),
            "abstract": (
                "This review maps occupational therapy services, participation, "
                "functioning and quality of life for adults with kidney disease."
            ),
        }
        result = scope.assess_candidate(candidate, self.policy)
        self.assertFalse(result["qualifies_for_health_clinical_adjacent"])
        self.assertIn(
            "occupational therapy services",
            result["general_medical_service_title_hits"],
        )

    def test_cbt_for_chronic_pain_qualifies(self) -> None:
        candidate = {
            "title": "Cognitive behavioural therapy for chronic primary pain",
            "abstract": "A randomised trial evaluated a psychological intervention.",
        }
        result = scope.assess_candidate(candidate, self.policy)
        self.assertTrue(result["qualifies_for_health_clinical_adjacent"])
        self.assertTrue(result["specific_title_hits"])

    def test_cognitive_rehabilitation_qualifies(self) -> None:
        candidate = {
            "title": "Cognitive rehabilitation after traumatic brain injury",
            "abstract": "The programme trained memory and executive strategies.",
        }
        result = scope.assess_candidate(candidate, self.policy)
        self.assertTrue(result["qualifies_for_health_clinical_adjacent"])

    def test_health_outcomes_alone_do_not_qualify(self) -> None:
        candidate = {
            "title": "Improving quality of life and adherence in dialysis",
            "abstract": (
                "A service programme examined participation, adherence, "
                "functioning and wellbeing."
            ),
        }
        result = scope.assess_candidate(candidate, self.policy)
        self.assertFalse(result["qualifies_for_health_clinical_adjacent"])

    def test_failed_health_hit_is_removed_from_cross_domain_candidate(self) -> None:
        config = {
            "query_families": [
                {
                    "query_id": "work",
                    "csi_domain": "performance_work",
                },
                {
                    "query_id": "health",
                    "csi_domain": "health_clinical_adjacent",
                },
                {
                    "query_id": "personal",
                    "csi_domain": "personal",
                },
            ]
        }
        manifest = {
            "candidates": [
                {
                    "candidate_id": "x",
                    "title": "General kidney service redesign",
                    "abstract": "Workflow and service delivery evaluation.",
                    "query_hits": [
                        {"query_id": "work"},
                        {"query_id": "health"},
                    ],
                }
            ]
        }
        selected, excluded, counts = scope.filter_candidates(
            manifest,
            config=config,
            policy=self.policy,
            target=1,
        )
        self.assertEqual(len(selected), 1)
        self.assertEqual(excluded, [])
        self.assertEqual(
            [hit["query_id"] for hit in selected[0]["query_hits"]],
            ["work"],
        )
        self.assertEqual(
            counts["health_query_hits_removed_from_cross_domain"], 1
        )

    def test_enforcement_excludes_health_only_nonpsychology_candidate(self) -> None:
        row = {
            "candidate_id": "kidney-ot",
            "candidate": {
                "candidate_id": "kidney-ot",
                "title": (
                    "Occupational Therapy Services Provided to Adults Diagnosed "
                    "With Kidney Disease: A Scoping Review"
                ),
                "abstract": "A review of services, participation and functioning.",
            },
            "evidence_units": [
                {
                    "unit_id": "t000",
                    "text": "Occupational Therapy Services Provided to Adults Diagnosed With Kidney Disease",
                }
            ],
            "classification": self._classification(
                domains=["health_clinical_adjacent"],
                primary="health_clinical_adjacent",
                targets=["health_functional_outcomes"],
                health_scope="health_clinical_adjacent",
            ),
            "ranking_score": 10.0,
        }
        result, action, _assessment = enforce.enforce_row(row, self.policy)
        self.assertEqual(action, "excluded_non_psychology_health_candidate")
        self.assertEqual(result["classification"]["screening_decision"], "exclude")
        self.assertEqual(result["classification"]["csi_domains"], ["not_applicable"])

    def test_enforcement_retains_explicit_psychological_intervention(self) -> None:
        row = {
            "candidate_id": "cbt-pain",
            "candidate": {
                "candidate_id": "cbt-pain",
                "title": "Cognitive behavioural therapy for chronic primary pain",
                "abstract": "A randomised trial of a psychological intervention.",
            },
            "evidence_units": [
                {"unit_id": "t000", "text": "Cognitive behavioural therapy for chronic primary pain"}
            ],
            "classification": self._classification(
                domains=["health_clinical_adjacent"],
                primary="health_clinical_adjacent",
                targets=["health_symptom_self_management"],
                health_scope="clinical_intervention_research",
            ),
            "ranking_score": 10.0,
        }
        result, action, _assessment = enforce.enforce_row(row, self.policy)
        self.assertEqual(action, "retained")
        self.assertIn(
            "health_clinical_adjacent",
            result["classification"]["csi_domains"],
        )

    @staticmethod
    def _classification(
        *,
        domains: list[str],
        primary: str,
        targets: list[str],
        health_scope: str,
    ) -> dict[str, object]:
        return {
            "screening_decision": "include",
            "psychology_intervention_relevant": True,
            "paper_role": "direct_intervention",
            "study_design": "randomised_controlled_trial",
            "intervention_families": ["digital_psychological_behavioural"],
            "candidate_routes": ["regulate"],
            "constraint_loci": ["capacity"],
            "population_summary": "Adults",
            "intervention_summary": "Intervention",
            "comparator_summary": "Comparator",
            "outcome_families": ["mental_health_wellbeing"],
            "transfer_signals": ["none_reported"],
            "evidence_unit_ids": ["t000"],
            "abstract_only_confidence": 0.8,
            "fulltext_priority": "high",
            "exclusion_reason": "not_excluded",
            "missing_for_fulltext": ["risk_of_bias_information"],
            "screening_rationale": "Relevant intervention.",
            "primary_csi_domain": primary,
            "csi_domains": domains,
            "application_targets": targets,
            "health_scope": health_scope,
        }


if __name__ == "__main__":
    unittest.main()
