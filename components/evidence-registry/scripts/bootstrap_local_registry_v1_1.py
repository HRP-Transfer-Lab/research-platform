#!/usr/bin/env python3
"""Run the deterministic local Evidence Registry v1.1 replay through Stage 10.

This wrapper deliberately leaves the proven Stage 1-9 bootstrap unchanged. It
runs that baseline first, then applies and validates the Stage 10 conservative
harms/fidelity/implementation layer. Local-only by design.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_RELEASE = "2026-08-23"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay the local HRP Evidence Registry v1.1 through Stage 10.")
    parser.add_argument("--release", default=DEFAULT_RELEASE)
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    args = parser.parse_args()

    scripts = REPO_ROOT / "components/evidence-registry/scripts"

    print("Running verified Stage 1-9 local registry bootstrap...")
    run([
        sys.executable,
        str(scripts / "bootstrap_local_registry.py"),
        "--release", args.release,
        "--container", args.container,
    ])

    print("Validating Stage 10 conservative seed manifest...")
    run([sys.executable, str(scripts / "validate_stage10_seed_mappings.py")])

    print("Applying Stage 10 conservative harms/implementation mappings...")
    run([
        sys.executable,
        str(scripts / "apply_stage10_seed_mappings.py"),
        "--container", args.container,
    ])

    print("Validating Stage 10 harms/fidelity/support-dependence architecture...")
    run([
        sys.executable,
        str(scripts / "validate_stage10_harms_implementation.py"),
        "--container", args.container,
    ])

    print("LOCAL REGISTRY V1.1 STAGES 1-10 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
