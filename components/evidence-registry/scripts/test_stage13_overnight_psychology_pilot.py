#!/usr/bin/env python3
from __future__ import annotations

import unittest

import stage13_classify_psychology_candidates as classify
import stage13_discover_psychology_interventions as discover


class PsychologyDiscoveryTests(unittest.TestCase):
    def test_normalise_doi(self) -> None:
        self.assertEqual(
            discover.normalise_doi("https://doi.org/10.1000/ABC.1 "),
            "10.1000/abc.1",
        )

    def test_clean_markup(self) -> None:
        self.assertEqual(
            discover.clean_markup("A <b>controlled</b> &amp; useful trial."),
            "A controlled & useful trial.",
        )

    def test_candidate_key_prefers_doi(self) -> None:
        self.assertEqual(
            discover.candidate_key(
                {"doi": "10.1000/test", "pmid": "123", "title": "Title"}
            ),
            "doi:10.1000/test",
        )

    def test_merge_candidate_combines_query_hits(self) -> None:
        target = {
            "query_hits": [{"query_id": "a"}],
            "direct_pdf_urls": [],
            "is_open_access": False,
            "abstract": "short",
        }
        incoming = {
            "query_hits": [{"query_id": "b"}],
            "direct_pdf_urls": ["https://example.org/paper.pdf"],
            "is_open_access": True,
            "abstract": "a much longer abstract",
            "abstract_sha256": "x",
        }
        discover.merge_candidate(target, incoming)
        self.assertEqual(
            {row["query_id"] for row in target["query_hits"]}, {"a", "b"}
        )
        self.assertTrue(target["is_open_access"])
        self.assertEqual(target["abstract"], "a much longer abstract")

    def test_balanced_selection_deduplicates(self) -> None:
        candidates = {
            "one": {
                "candidate_id": "one",
                "title": "Cognitive training intervention trial",
                "abstract": "Randomized cognitive training intervention.",
                "query_hits": [{"query_id": "a"}, {"query_id": "b"}],
                "is_open_access": True,
                "direct_pdf_urls": [],
            },
            "two": {
                "candidate_id": "two",
                "title": "Reasoning training trial",
                "abstract": "Controlled reasoning training experiment.",
                "query_hits": [{"query_id": "b"}],
                "is_open_access": False,
                "direct_pdf_urls": [],
            },
        }
        selected = discover.balanced_selection(candidates, ["a", "b"], 2)
        self.assertEqual(len(selected), 2)
        self.assertEqual(len({row["candidate_id"] for row in selected}), 2)


class PsychologyClassificationTests(unittest.TestCase):
    def valid_classification(self) -> dict:
        return {
            "screening_decision": "include",
            "psychology_intervention_relevant": True,
            "paper_role": "direct_intervention",
            "study_design": "randomised_controlled_trial",
            "intervention_families": ["attention_cognitive_control"],
            "candidate_routes": ["develop_train"],
            "constraint_loci": ["capacity"],
            "population_summary": "Adults",
            "intervention_summary": "Attention training",
            "comparator_summary": "Active control",
            "outcome_families": ["cognitive_performance"],
            "transfer_signals": ["separate_measure"],
            "evidence_unit_ids": ["t000", "a001"],
            "abstract_only_confidence": 0.8,
            "fulltext_priority": "high",
            "exclusion_reason": "not_excluded",
            "missing_for_fulltext": ["risk_of_bias_information"],
            "screening_rationale": "Relevant intervention trial.",
        }

    def test_evidence_units_include_title_and_abstract(self) -> None:
        units = classify.evidence_units(
            "A trial", "Participants trained attention. Outcomes improved."
        )
        self.assertEqual(units[0]["unit_id"], "t000")
        self.assertGreaterEqual(len(units), 3)

    def test_validate_classification_accepts_valid_record(self) -> None:
        errors = classify.validate_classification(
            self.valid_classification(),
            allowed_unit_ids={"t000", "a001"},
        )
        self.assertEqual(errors, [])

    def test_validate_classification_rejects_unknown_anchor(self) -> None:
        value = self.valid_classification()
        value["evidence_unit_ids"] = ["a999"]
        errors = classify.validate_classification(
            value,
            allowed_unit_ids={"t000", "a001"},
        )
        self.assertTrue(
            any(error.startswith("evidence_unit_ids:unknown") for error in errors)
        )

    def test_validate_classification_requires_exclusion_reason(self) -> None:
        value = self.valid_classification()
        value["screening_decision"] = "exclude"
        value["psychology_intervention_relevant"] = False
        value["paper_role"] = "not_relevant"
        errors = classify.validate_classification(
            value,
            allowed_unit_ids={"t000", "a001"},
        )
        self.assertIn("exclusion_reason:required", errors)

    def test_safe_filename_is_stable(self) -> None:
        first = classify.safe_filename("doi:10.1000/a/b")
        second = classify.safe_filename("doi:10.1000/a/b")
        self.assertEqual(first, second)
        self.assertTrue(first.endswith(".json"))
        self.assertNotIn("/", first)

    def test_ranking_prefers_include_and_open_access(self) -> None:
        candidate = {
            "deterministic_relevance_score": 10,
            "is_open_access": True,
            "direct_pdf_urls": ["https://example.org/a.pdf"],
        }
        include = self.valid_classification()
        exclude = self.valid_classification()
        exclude.update(
            {
                "screening_decision": "exclude",
                "psychology_intervention_relevant": False,
                "paper_role": "not_relevant",
                "fulltext_priority": "not_applicable",
                "exclusion_reason": "not_intervention_relevant",
            }
        )
        self.assertGreater(
            classify.ranking_score(candidate, include),
            classify.ranking_score(candidate, exclude),
        )


if __name__ == "__main__":
    unittest.main()
