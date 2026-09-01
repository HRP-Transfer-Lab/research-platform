#!/usr/bin/env python3
"""Install the governed Q1 rt-2026-001 quality/RoB review batch."""
from __future__ import annotations


def install(prep_module) -> None:
    prep_module.BATCH_SPECS["quality_q1_rt001"] = {
        "label": "Q1 rt-2026-001 study quality and result-specific RoB 2 appraisal",
        "expected": 28,
        "group": "source",
        "surfaces": [
            {"mode": "ordinary", "table": "study_quality_status"},
            {"mode": "ordinary", "table": "result_rob_status"},
            {"mode": "ordinary", "table": "study_quality_assessment"},
            {"mode": "ordinary", "table": "result_risk_of_bias_assessment"},
            {"mode": "ordinary", "table": "assessment_domain_judgement"},
        ],
    }

    legacy = prep_module.legacy
    original = legacy.resolve_source_context

    def quality_context(container: str, row: dict):
        enriched = dict(row)
        if enriched.get("study_id") is None and enriched.get("outcome_id") is None:
            study_assessment_id = enriched.get("study_quality_assessment_id")
            result_assessment_id = enriched.get("result_rob_assessment_id")
            if study_assessment_id is not None:
                value = prep_module.psql(
                    container,
                    f"select study_id from public.study_quality_assessment where study_quality_assessment_id={int(study_assessment_id)};",
                )
                if value:
                    enriched["study_id"] = int(value)
            elif result_assessment_id is not None:
                value = prep_module.psql(
                    container,
                    f"select outcome_id from public.result_risk_of_bias_assessment where result_rob_assessment_id={int(result_assessment_id)};",
                )
                if value:
                    enriched["outcome_id"] = int(value)
        return original(container, enriched)

    legacy.resolve_source_context = quality_context
