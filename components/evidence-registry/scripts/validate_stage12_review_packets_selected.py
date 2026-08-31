#!/usr/bin/env python3
"""Validate selected Stage 12 review packets without requiring all six batches."""
from __future__ import annotations

import argparse
import subprocess

import validate_stage12_review_packets as base


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate one or more Stage 12 governed review packets.")
    ap.add_argument("--container", default=base.DEFAULT_CONTAINER)
    ap.add_argument("--packet-dir", default=str(base.DEFAULT_PACKET_DIR))
    ap.add_argument("--batch", action="append", choices=list(base.EXPECTED), required=True)
    args = ap.parse_args()

    running = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", args.container],
        text=True,
        check=True,
        capture_output=True,
    ).stdout.strip()
    base.require(running == "true", f"Local database container {args.container!r} is not running")

    current_revision = int(base.psql(args.container, "select current_revision from public.scientific_state_revision where singleton=true;"))
    packet_dir = base.Path(args.packet_dir)

    print("STAGE 12 SELECTED REVIEW PACKET VALIDATION")
    print(f"scientific_state_revision|{current_revision}")
    print("batch_id|review_units|decisions|scientific_decision_sha256")

    total = 0
    for batch_id in args.batch:
        path = packet_dir / f"{batch_id}.json"
        base.require(path.exists(), f"Missing packet {path}")
        stable_hash, units, decisions = base.validate_packet(args.container, path, current_revision)
        base.require(decisions == base.EXPECTED[batch_id], f"{batch_id}: unexpected decision count")
        total += decisions
        print(f"{batch_id}|{units}|{decisions}|{stable_hash}")

    print(f"selected_total_decisions|{total}")
    print("normalized_scientific_rows_changed|0")
    print("STAGE 12 SELECTED REVIEW PACKETS VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
