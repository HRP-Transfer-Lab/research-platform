#!/usr/bin/env python3
"""Install the post-correction Stage 9 review batch.

After governed removal of the unsupported rt-2026-015 China geography inference,
the remaining unresolved Stage 9 surface contains 119 valid candidate decisions.
The original 121-decision ``stage9_context`` packet remains an audit artefact and
must not be approved.
"""
from __future__ import annotations


def install(prep_module) -> None:
    prep_module.BATCH_SPECS["stage9_context_corrected"] = {
        "label": "Stage 9 population, study context and delivery context — corrected review surface",
        "expected": 119,
        "group": "source",
        "surfaces": [
            {"mode": "ordinary", "table": "study_population_context_status"},
            {"mode": "ordinary", "table": "study_population_context_term"},
            {"mode": "ordinary", "table": "component_delivery_context_status"},
            {"mode": "ordinary", "table": "component_delivery_context_term"},
        ],
    }
