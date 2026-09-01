#!/usr/bin/env python3
"""Prepare the governed Q1 rt-2026-001 quality/RoB review packet."""
from __future__ import annotations

import prepare_stage12_review_surface_packets as prep
from stage12_quality_q1_rt001_batch import install

install(prep)

if __name__ == "__main__":
    raise SystemExit(prep.main())
