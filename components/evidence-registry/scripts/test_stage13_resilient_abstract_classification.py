#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

import stage13_classify_csi_domain_candidates as classifier
import stage13_normalise_csi_abstract_classification as normaliser


class ResilientAbstractClassificationTests(unittest.TestCase):
    allowed = {"t000", "a001", "a002"}

    def base_include(self) -> dict:
        return {
            "screening_decision": "include",
            "psychology_intervention_relevant": True,
            "paper_role": "protocol",
            "study_design": "protocol",
            "intervention_families": ["digital_psychological_behavioural"],
            "candidate_routes": ["develop_condition"],
            "constraint_loci": ["capacity"],
            "population_summary": "Adults in a health-related population",
            "intervention_summary": "A psychology-related intervention",
            "comparator_summary": "Usual care",
            "outcome_families": ["cognitive_performance"],
            "transfer_signals": ["applied_or_functional"],
            "evidence_unit_ids": ["t000", "a001"],
            "abstract_only_confidence": 0.82,
            "fulltext_priority": "high",
            "exclusion_reason": "not_excluded",
            "missing_for_fulltext": ["risk_of_bias_information"],
            "screening_rationale": "Relevant protocol.",
            "primary_csi_domain": "health_clinical_adjacent",
            "csi_domains": ["health_clinical_adjacent"],
            "application_targets": ["health_symptom_self_management"],
            "health_scope": "clinical_intervention_research",
        }

    def test_empty_exclusion_arrays_are_canonicalised(self) -> None:
        value = self.base_include()
        value.update(
            {
                "screening_decision": "exclude",
                "psychology_intervention_relevant": False,
                "paper_role": "not_relevant",
                "intervention_families": [],
                "candidate_routes": [],
                "constraint_loci": [],
                "outcome_families": [],
                "transfer_signals": [],
                "missing_for_fulltext": [],
                "fulltext_priority": "not_applicable",
                "exclusion_reason": "not_excluded",
                "primary_csi_domain": "not_applicable",
                "csi_domains": ["not_applicable"],
                "application_targets": ["not_applicable"],
                "health_scope": "not_applicable",
            }
        )
        output, actions = normaliser.normalise_classification(
            value, allowed_unit_ids=self.allowed
        )
        self.assertEqual(
            classifier.validate_classification(
                output, allowed_unit_ids=self.allowed
            ),
            [],
        )
        self.assertEqual(output["candidate_routes"], ["not_applicable"])
        self.assertEqual(output["constraint_loci"], ["not_applicable"])
        self.assertEqual(output["outcome_families"], ["not_reported"])
        self.assertEqual(output["transfer_signals"], ["none_reported"])
        self.assertEqual(output["missing_for_fulltext"], ["none_identified"])
        self.assertEqual(output["exclusion_reason"], "not_intervention_relevant")
        self.assertTrue(actions)

    def test_health_scope_and_empty_target_are_aligned(self) -> None:
        value = self.base_include()
        value["health_scope"] = "non_health"
        value["application_targets"] = ["not_applicable"]
        output, actions = normaliser.normalise_classification(
            value, allowed_unit_ids=self.allowed
        )
        self.assertEqual(
            classifier.validate_classification(
                output, allowed_unit_ids=self.allowed
            ),
            [],
        )
        self.assertEqual(output["health_scope"], "health_clinical_adjacent")
        self.assertNotIn("not_applicable", output["application_targets"])
        self.assertTrue(any(item["field"] == "health_scope" for item in actions))
        self.assertTrue(
            any(item["field"] == "application_targets" for item in actions)
        )

    def test_duplicate_transfer_signals_are_deduplicated(self) -> None:
        value = self.base_include()
        value["transfer_signals"] = [
            "applied_or_functional",
            "applied_or_functional",
        ]
        output, _ = normaliser.normalise_classification(
            value, allowed_unit_ids=self.allowed
        )
        self.assertEqual(output["transfer_signals"], ["applied_or_functional"])
        self.assertEqual(
            classifier.validate_classification(
                output, allowed_unit_ids=self.allowed
            ),
            [],
        )

    def test_inclusion_is_never_derived_from_an_exclusion(self) -> None:
        value = self.base_include()
        value["screening_decision"] = "exclude"
        value["psychology_intervention_relevant"] = True
        output, _ = normaliser.normalise_classification(
            value, allowed_unit_ids=self.allowed
        )
        self.assertEqual(output["screening_decision"], "exclude")
        self.assertFalse(output["psychology_intervention_relevant"])
        self.assertEqual(output["primary_csi_domain"], "not_applicable")

    def test_included_record_without_any_domain_is_not_invented(self) -> None:
        value = self.base_include()
        value["primary_csi_domain"] = "not_applicable"
        value["csi_domains"] = ["not_applicable"]
        with self.assertRaisesRegex(ValueError, "no supported CSI domain"):
            normaliser.normalise_classification(
                value, allowed_unit_ids=self.allowed
            )

    def test_unknown_evidence_ids_are_removed(self) -> None:
        value = self.base_include()
        value["evidence_unit_ids"] = ["unknown", "a001", "a001"]
        output, _ = normaliser.normalise_classification(
            value, allowed_unit_ids=self.allowed
        )
        self.assertEqual(output["evidence_unit_ids"], ["a001"])

    def test_raw_input_is_not_mutated(self) -> None:
        value = self.base_include()
        value["health_scope"] = "non_health"
        before = copy.deepcopy(value)
        normaliser.normalise_classification(value, allowed_unit_ids=self.allowed)
        self.assertEqual(value, before)


if __name__ == "__main__":
    unittest.main()
