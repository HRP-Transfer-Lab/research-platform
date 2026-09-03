#!/usr/bin/env python3
"""Run the strict three-domain pilot with resilient local-model validation."""
from __future__ import annotations

from pathlib import Path

import stage13_run_overnight_three_domain_pilot as pilot

pilot.CLASSIFY_SCRIPT = (
    Path(__file__).resolve().parent
    / "stage13_classify_csi_domain_candidates_resilient.py"
)

if __name__ == "__main__":
    raise SystemExit(pilot.main())
