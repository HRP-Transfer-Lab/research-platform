#!/usr/bin/env python3
"""Stage 4 non-overlapping review-slice definitions for Stage 12.

The five slices partition the complete 260-decision Stage 4 review surface:
  distance = 38 classification decisions
  time     = 38 classification + 38 time-link decisions
  transfer = 38 classification + 2 transfer-axis decisions
  role     = 38 classification + 30 role-link decisions
  bridge   = 38 classification decisions

They are intentionally reviewed and approved sequentially so each packet is
bound to the scientific revision current at the time of review.
"""
from __future__ import annotations

from typing import Any


STAGE4_SLICE_SPECS: dict[str, dict[str, Any]] = {
    "stage4_distance": {
        "label": "Stage 4 outcome distance",
        "expected": 38,
        "group": "outcome",
        "surfaces": [
            {"mode": "dimension", "table": "outcome_stage4_classification", "dimension": "distance"},
        ],
    },
    "stage4_time": {
        "label": "Stage 4 outcome time",
        "expected": 76,
        "group": "outcome",
        "surfaces": [
            {"mode": "dimension", "table": "outcome_stage4_classification", "dimension": "time"},
            {"mode": "ordinary", "table": "outcome_time_link"},
        ],
    },
    "stage4_transfer": {
        "label": "Stage 4 transfer classification",
        "expected": 40,
        "group": "outcome",
        "surfaces": [
            {"mode": "dimension", "table": "outcome_stage4_classification", "dimension": "transfer"},
            {"mode": "ordinary", "table": "outcome_transfer_axis"},
        ],
    },
    "stage4_role": {
        "label": "Stage 4 outcome role",
        "expected": 68,
        "group": "outcome",
        "surfaces": [
            {"mode": "dimension", "table": "outcome_stage4_classification", "dimension": "role"},
            {"mode": "ordinary", "table": "outcome_role_link"},
        ],
    },
    "stage4_bridge": {
        "label": "Stage 4 Bridge evidence",
        "expected": 38,
        "group": "outcome",
        "surfaces": [
            {"mode": "dimension", "table": "outcome_stage4_classification", "dimension": "bridge"},
        ],
    },
}


def install(prep_module) -> None:
    """Install Stage 4 slice specs into the shared review-surface module."""
    prep_module.BATCH_SPECS.update(STAGE4_SLICE_SPECS)
