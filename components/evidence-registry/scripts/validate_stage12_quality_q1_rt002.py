#!/usr/bin/env python3
"""Validate the governed Q1 rt-2026-002 quality/RoB review packet."""
from __future__ import annotations

import prepare_stage12_review_surface_packets as prep
from stage12_quality_q1_rt002_batch import install

install(prep)

import validate_stage12_review_surface_packet as validator

if __name__ == "__main__":
    raise SystemExit(validator.main())
