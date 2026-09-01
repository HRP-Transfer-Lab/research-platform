#!/usr/bin/env python3
"""Install the governed Q1 rt-2026-002 quality/RoB review batch."""
from __future__ import annotations

from stage12_quality_batch_common import install as install_common


def install(prep_module) -> None:
    install_common(
        prep_module,
        batch_id="quality_q1_rt002",
        label="Q1 rt-2026-002 study quality and result-specific RoB 2 appraisal",
        expected=21,
    )
