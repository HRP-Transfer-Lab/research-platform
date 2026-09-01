#!/usr/bin/env python3
"""Apply an explicitly approved corrected Stage 9 review packet locally."""
from __future__ import annotations

import prepare_stage12_review_surface_packets as prep
from stage12_stage9_post_correction import install

install(prep)

import approve_stage12_review_surface_packet as approval


if __name__ == "__main__":
    raise SystemExit(approval.main())
