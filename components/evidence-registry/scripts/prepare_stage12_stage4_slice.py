#!/usr/bin/env python3
"""Prepare one or more governed Stage 4 review slices."""
from __future__ import annotations

import prepare_stage12_review_surface_packets as prep
from stage12_stage4_slices import install

install(prep)


if __name__ == "__main__":
    raise SystemExit(prep.main())
