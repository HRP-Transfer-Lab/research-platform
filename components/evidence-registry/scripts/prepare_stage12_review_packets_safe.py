#!/usr/bin/env python3
"""Compatibility wrapper for Stage 12 review-packet preparation.

Filters psql command-tag lines (for example ``INSERT 0 1``) from the legacy
packet generator while preserving actual tuple output. This keeps packet
preparation idempotent after partial prior runs.
"""
from __future__ import annotations

import re

import prepare_stage12_review_packets as legacy

_COMMAND_TAG = re.compile(r"^(?:INSERT\s+\d+\s+\d+|UPDATE\s+\d+|DELETE\s+\d+|SELECT\s+\d+)$")
_original_psql = legacy.psql


def cleaned_psql(container: str, sql: str) -> str:
    raw = _original_psql(container, sql)
    lines = [line for line in raw.splitlines() if line and not _COMMAND_TAG.match(line)]
    return "\n".join(lines)


legacy.psql = cleaned_psql


if __name__ == "__main__":
    raise SystemExit(legacy.main())
