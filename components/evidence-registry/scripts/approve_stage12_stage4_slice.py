#!/usr/bin/env python3
"""Apply an explicitly human-approved governed Stage 4 review slice locally."""
from __future__ import annotations

import prepare_stage12_review_surface_packets as prep
from stage12_stage4_slices import install

install(prep)

import approve_stage12_review_surface_packet as approval


if __name__ == "__main__":
    raise SystemExit(approval.main())
