#!/usr/bin/env python3
"""Validate a governed Stage 4 review slice."""
from __future__ import annotations

import prepare_stage12_review_surface_packets as prep
from stage12_stage4_slices import install

install(prep)

import validate_stage12_review_surface_packet as validator


if __name__ == "__main__":
    raise SystemExit(validator.main())
