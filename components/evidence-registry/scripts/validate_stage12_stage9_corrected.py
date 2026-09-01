#!/usr/bin/env python3
"""Validate the governed corrected Stage 9 review packet."""
from __future__ import annotations

import prepare_stage12_review_surface_packets as prep
from stage12_stage9_post_correction import install

install(prep)

import validate_stage12_review_surface_packet as validator


if __name__ == "__main__":
    raise SystemExit(validator.main())
