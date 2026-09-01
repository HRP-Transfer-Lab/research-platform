#!/usr/bin/env python3
"""Apply an explicitly human-approved Q1 rt-2026-002 quality/RoB packet locally."""
from __future__ import annotations

import prepare_stage12_review_surface_packets as prep
from stage12_quality_q1_rt002_batch import install

install(prep)

import approve_stage12_review_surface_packet as approval

if __name__ == "__main__":
    raise SystemExit(approval.main())
