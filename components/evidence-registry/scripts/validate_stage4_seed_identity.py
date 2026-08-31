#!/usr/bin/env python3
"""Validate stable lookup identity for the 38 Stage 4 seed outcomes.

Stage 4 mappings must survive clean bootstrap even though evidence_outcome.outcome_id
is regenerated. The stable seed lookup key is therefore:

    source_id + outcome_name + legacy evidence_rung + raw timepoint

This validator proves that key is unique across the current immutable 2026-08-23
seed and reports compound/missing timepoint cases that Stage 4 must preserve.
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Stage 4 stable seed outcome identity.")
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--expected", type=int, default=38)
    args = parser.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running.")

    summary_sql = """
with seed as (
  select
    s.source_id,
    eo.outcome_id,
    eo.outcome_name,
    coalesce(eo.evidence_rung, '<NULL>') as evidence_rung,
    coalesce(eo.timepoint, '<NULL>') as timepoint
  from public.evidence_outcome eo
  join public.study s on s.study_id = eo.study_id
  join public.evidence_source es on es.source_id = s.source_id
  where es.release_id = '2026-08-23'
), keys as (
  select
    source_id,
    outcome_name,
    evidence_rung,
    timepoint,
    count(*) as n
  from seed
  group by source_id, outcome_name, evidence_rung, timepoint
)
select
  (select count(*) from seed),
  (select count(*) from keys),
  (select count(*) from keys where n > 1),
  (select count(*) from seed where timepoint = '<NULL>'),
  (select count(*) from seed where timepoint like 'post_and_%');
"""
    raw = psql(args.container, summary_sql).split("|")
    if len(raw) != 5 or any(v == "" for v in raw):
        raise SystemExit(f"STAGE 4 SEED IDENTITY INVALID: unexpected database output {raw!r}")

    total, unique_keys, duplicate_keys, null_timepoints, compound_post_timepoints = map(int, raw)

    errors: list[str] = []
    if total != args.expected:
        errors.append(f"seed outcomes: expected {args.expected}, got {total}")
    if unique_keys != total:
        errors.append(f"unique stable keys: expected {total}, got {unique_keys}")
    if duplicate_keys != 0:
        errors.append(f"duplicate stable keys: expected 0, got {duplicate_keys}")

    if errors:
        print("STAGE 4 SEED IDENTITY INVALID")
        for error in errors:
            print("-", error)

        duplicates = psql(
            args.container,
            """
select
  s.source_id,
  eo.outcome_name,
  coalesce(eo.evidence_rung, '<NULL>'),
  coalesce(eo.timepoint, '<NULL>'),
  count(*)
from public.evidence_outcome eo
join public.study s on s.study_id = eo.study_id
join public.evidence_source es on es.source_id = s.source_id
where es.release_id = '2026-08-23'
group by s.source_id, eo.outcome_name, eo.evidence_rung, eo.timepoint
having count(*) > 1
order by s.source_id, eo.outcome_name;
""",
        )
        if duplicates:
            print("duplicate keys:")
            print(duplicates)
        return 1

    print(
        "STAGE 4 SEED IDENTITY VALID: "
        f"outcomes={total}; stable_keys={unique_keys}; duplicate_keys={duplicate_keys}"
    )
    print(
        f"raw_timepoint_null={null_timepoints}; "
        f"compound_post_followup_rows={compound_post_timepoints}"
    )
    print("stable_key = source_id + outcome_name + legacy_rung + raw_timepoint")
    print("STAGE 4 IDENTITY PASS: mapping manifest may use the stable seed key.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
