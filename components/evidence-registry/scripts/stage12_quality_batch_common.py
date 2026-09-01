#!/usr/bin/env python3
"""Shared registration helper for Stage 12 quality/RoB source review batches."""
from __future__ import annotations


def decision_count(manifest: dict) -> int:
    results = manifest.get("result_assessments", [])
    study_domains = manifest.get("study_assessment", {}).get("domains", [])
    result_domains = sum(len(r.get("domains", [])) for r in results)
    # one study status + one study assessment + N result statuses + N result assessments + domains
    return 2 + (2 * len(results)) + len(study_domains) + result_domains


def install(prep_module, *, batch_id: str, label: str, expected: int) -> None:
    prep_module.BATCH_SPECS[batch_id] = {
        "label": label,
        "expected": expected,
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
    if getattr(legacy, "_stage12_quality_context_installed", False):
        return

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
    legacy._stage12_quality_context_installed = True
