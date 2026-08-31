#!/usr/bin/env python3
"""Incremental, visible wrapper for Stage 12 review-packet preparation.

Adds three operational safeguards around the legacy packet generator:
- filters psql command-tag lines such as ``INSERT 0 1``;
- allows one or more scientific batches to be generated independently;
- prints progress while reusing previously-created bridge candidates idempotently.

No normalized scientific row is approved or modified by packet preparation.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

import prepare_stage12_review_packets as legacy

_COMMAND_TAG = re.compile(r"^(?:INSERT\s+\d+\s+\d+|UPDATE\s+\d+|DELETE\s+\d+|SELECT\s+\d+)$")
_original_psql = legacy.psql
_original_ensure_candidate = legacy.ensure_candidate

_cache: dict[tuple[str, str], str] = {}
_progress_done = 0
_progress_total = 0
_progress_every = 5


def cleaned_psql(container: str, sql: str) -> str:
    """Remove psql command tags and cache only static context SELECTs."""
    normalized = sql.strip()
    lower = normalized.lower()
    mutable_tokens = (
        "scientific_field_candidate",
        "scientific_processing_run",
        "scientific_state_revision",
    )
    cacheable = lower.startswith("select") and not any(token in lower for token in mutable_tokens)
    key = (container, normalized)
    if cacheable and key in _cache:
        return _cache[key]

    raw = _original_psql(container, sql)
    lines = [line for line in raw.splitlines() if line and not _COMMAND_TAG.match(line)]
    cleaned = "\n".join(lines)
    if cacheable:
        _cache[key] = cleaned
    return cleaned


def visible_ensure_candidate(*args, **kwargs):
    global _progress_done
    result = _original_ensure_candidate(*args, **kwargs)
    _progress_done += 1
    if _progress_done == 1 or _progress_done % _progress_every == 0 or _progress_done == _progress_total:
        print(f"review-packet progress|{_progress_done}/{_progress_total}", flush=True)
    return result


legacy.psql = cleaned_psql
legacy.ensure_candidate = visible_ensure_candidate


def main() -> int:
    global _progress_total, _progress_every

    ap = argparse.ArgumentParser(description="Prepare Stage 12 review packets incrementally with visible progress.")
    ap.add_argument("--container", default=legacy.DEFAULT_CONTAINER)
    ap.add_argument("--output-dir", type=Path, default=legacy.DEFAULT_OUTPUT_DIR)
    ap.add_argument(
        "--batch",
        action="append",
        choices=list(legacy.BATCH_SPECS),
        help="Batch to prepare. Repeat for multiple batches. Default: all batches.",
    )
    ap.add_argument("--progress-every", type=int, default=5)
    args = ap.parse_args()

    running = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", args.container],
        text=True,
        check=True,
        capture_output=True,
    ).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    selected = args.batch or list(legacy.BATCH_SPECS)
    legacy.BATCH_SPECS = {key: legacy.BATCH_SPECS[key] for key in selected}
    _progress_total = sum(int(spec["expected"]) for spec in legacy.BATCH_SPECS.values())
    _progress_every = max(1, args.progress_every)

    print("STAGE 12 INCREMENTAL REVIEW PACKET PREPARATION", flush=True)
    print(f"batches|{','.join(selected)}", flush=True)
    print(f"decisions_to_prepare|{_progress_total}", flush=True)
    print("normalized_scientific_rows_will_change|0", flush=True)

    legacy.build_packets(args.container, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
