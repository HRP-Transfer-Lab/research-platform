#!/usr/bin/env python3
"""Audit legacy outcome semantics before Stage 4 normalization.

Read-only against the local Supabase database. This script does not mutate data.
It inventories the 38 historical seed outcomes so Stage 4 mappings can be locked
before an additive migration is written.
"""

from __future__ import annotations

import argparse
import subprocess

DEFAULT_CONTAINER = "supabase_db_research-platform"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container,
        "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres",
        "-A", "-t", "-F", "|",
    ]
    return run(cmd, input_text=sql, capture=True).stdout.strip()


def print_section(title: str, body: str) -> None:
    print(f"\n=== {title} ===")
    print(body or "(none)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Stage 4 legacy outcome semantics.")
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--expected-outcomes", type=int, default=38)
    args = parser.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running.")

    total = int(psql(args.container, "select count(*) from public.evidence_outcome;"))
    if total != args.expected_outcomes:
        raise SystemExit(f"STAGE 4 AUDIT ABORT: expected {args.expected_outcomes} outcomes, found {total}")

    print(f"STAGE 4 OUTCOME AUDIT: {total} historical outcomes")

    print_section(
        "LEGACY EVIDENCE RUNG COUNTS",
        psql(
            args.container,
            """
select coalesce(evidence_rung, '<NULL>'), count(*)
from public.evidence_outcome
group by evidence_rung
order by count(*) desc, coalesce(evidence_rung, '<NULL>');
""",
        ),
    )

    print_section(
        "RAW TIMEPOINT COUNTS",
        psql(
            args.container,
            """
select coalesce(timepoint, '<NULL>'), count(*)
from public.evidence_outcome
group by timepoint
order by count(*) desc, coalesce(timepoint, '<NULL>');
""",
        ),
    )

    print_section(
        "LEGACY TRANSFER AXIS COUNTS",
        psql(
            args.container,
            """
select axis, count(*)
from public.evidence_outcome eo
cross join lateral unnest(eo.transfer_axes) as axis
group by axis
order by count(*) desc, axis;
""",
        ),
    )

    print_section(
        "BRIDGE EVIDENCE COUNTS",
        psql(
            args.container,
            """
select coalesce(bridge_evidence_level, '<NULL>'), count(*)
from public.evidence_outcome
group by bridge_evidence_level
order by count(*) desc, coalesce(bridge_evidence_level, '<NULL>');
""",
        ),
    )

    print_section(
        "RESULT DIRECTION COUNTS",
        psql(
            args.container,
            """
select coalesce(result_direction, '<NULL>'), count(*)
from public.evidence_outcome
group by result_direction
order by count(*) desc, coalesce(result_direction, '<NULL>');
""",
        ),
    )

    parity = psql(
        args.container,
        """
select
  count(*) filter (
    where evidence_rung is distinct from nullif(outcome_json->>'rung','')
  ),
  count(*) filter (
    where timepoint is distinct from nullif(outcome_json->>'timepoint','')
  ),
  count(*) filter (
    where bridge_evidence_level is distinct from nullif(outcome_json->>'bridge_evidence_level','')
  ),
  count(*) filter (
    where result_direction is distinct from nullif(outcome_json->>'direction','')
  )
from public.evidence_outcome;
""",
    )
    print_section("LEGACY JSON ↔ NORMALIZED FIELD MISMATCHES (rung|time|bridge|direction)", parity)

    print_section(
        "OUTCOME-BY-OUTCOME AUDIT",
        psql(
            args.container,
            """
select
  es.source_id,
  eo.outcome_id,
  replace(eo.outcome_name, '|', '/'),
  coalesce(eo.evidence_rung, '<NULL>'),
  coalesce(eo.timepoint, '<NULL>'),
  case when cardinality(eo.transfer_axes)=0 then '<NONE>' else array_to_string(eo.transfer_axes, ',') end,
  coalesce(eo.bridge_evidence_level, '<NULL>'),
  coalesce(eo.result_direction, '<NULL>'),
  coalesce(eo.objective::text, '<NULL>'),
  coalesce(replace(eo.outcome_json->>'boundary', '|', '/'), replace(eo.outcome_json->>'summary', '|', '/'), '')
from public.evidence_outcome eo
join public.study s on s.study_id=eo.study_id
join public.evidence_source es on es.source_id=s.source_id
order by es.source_id, eo.outcome_id;
""",
        ),
    )

    print("\nSTAGE 4 AUDIT PASS: read-only inventory complete; no mappings have been applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
