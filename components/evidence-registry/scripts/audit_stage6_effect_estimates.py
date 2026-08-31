#!/usr/bin/env python3
"""Read-only Stage 6 audit of historical quantitative outcome/effect fields.

Inventories the 38 seed outcomes before first-class effect-estimate migration.
No database writes are performed.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from collections import Counter

DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_RELEASE = "2026-08-23"

NUMERIC_STRING = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def run_psql(container: str, sql: str) -> str:
    proc = subprocess.run(
        [
            "docker", "exec", "-i", container,
            "psql", "-U", "postgres", "-d", "postgres",
            "-At", "-F", "\t", "-c", sql,
        ],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout.strip()


def safe_json(value: str):
    try:
        return json.loads(value) if value else {}
    except json.JSONDecodeError:
        return {}


def numeric_paths(value, prefix: str = "") -> list[tuple[str, object]]:
    found: list[tuple[str, object]] = []
    if isinstance(value, bool) or value is None:
        return found
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return found
        found.append((prefix or "$", value))
        return found
    if isinstance(value, str) and NUMERIC_STRING.match(value.strip()):
        found.append((prefix or "$", value))
        return found
    if isinstance(value, list):
        for i, item in enumerate(value):
            child = f"{prefix}[{i}]" if prefix else f"[{i}]"
            found.extend(numeric_paths(item, child))
    elif isinstance(value, dict):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else key
            found.extend(numeric_paths(item, child))
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Stage 6 historical quantitative effect fields.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--release", default=DEFAULT_RELEASE)
    args = ap.parse_args()

    release = args.release.replace("'", "''")
    sql = f"""
select
  es.source_id,
  eo.outcome_id,
  eo.outcome_name,
  coalesce(eo.evidence_rung,''),
  coalesce(eo.timepoint,''),
  coalesce(eo.effect_metric,''),
  coalesce(eo.effect_estimate::text,''),
  coalesce(eo.ci_lower::text,''),
  coalesce(eo.ci_upper::text,''),
  eo.outcome_json::text
from public.evidence_outcome eo
join public.study s on s.study_id = eo.study_id
join public.evidence_source es on es.source_id = s.source_id
where es.release_id = '{release}'
order by es.source_id, eo.outcome_id;
"""

    raw = run_psql(args.container, sql)
    rows = [line.split("\t", 9) for line in raw.splitlines() if line.strip()]
    if len(rows) != 38:
        raise SystemExit(f"Expected 38 historical outcomes, found {len(rows)}")

    current_effect_rows = 0
    current_metric_rows = 0
    current_ci_rows = 0
    json_effect_rows = 0
    json_ci_rows = 0
    any_numeric_json_rows = 0
    numeric_key_paths = Counter()

    print(f"STAGE 6 EFFECT AUDIT: {len(rows)} historical outcomes")
    print()
    print("=== OUTCOMES WITH QUANTITATIVE SIGNALS ===")

    signalled = 0
    for parts in rows:
        if len(parts) < 10:
            parts += [""] * (10 - len(parts))
        if len(parts) != 10:
            raise SystemExit(f"Unexpected database row with {len(parts)} fields: {parts!r}")

        source_id, outcome_id, name, rung, timepoint, metric, estimate, ci_low, ci_high, outcome_raw = parts
        payload = safe_json(outcome_raw)
        paths = numeric_paths(payload)

        if metric:
            current_metric_rows += 1
        if estimate:
            current_effect_rows += 1
        if ci_low or ci_high:
            current_ci_rows += 1
        if isinstance(payload, dict) and payload.get("effect") is not None:
            json_effect_rows += 1
        if isinstance(payload, dict) and payload.get("ci") is not None:
            json_ci_rows += 1
        if paths:
            any_numeric_json_rows += 1
            for path, _ in paths:
                numeric_key_paths[path] += 1

        has_signal = bool(metric or estimate or ci_low or ci_high or paths)
        if not has_signal:
            continue

        signalled += 1
        print(f"{source_id}|outcome_id={outcome_id}")
        print(f"  outcome={name}")
        print(f"  stable_key={source_id} + {name} + {rung or '<NULL>'} + {timepoint or '<NULL>'}")
        print(f"  compatibility_effect_metric={metric or '<NULL>'}")
        print(f"  compatibility_effect_estimate={estimate or '<NULL>'}")
        print(f"  compatibility_ci={ci_low or '<NULL>'}|{ci_high or '<NULL>'}")
        if paths:
            print("  outcome_json_numeric_paths=" + "; ".join(f"{p}={v}" for p, v in paths))
        else:
            print("  outcome_json_numeric_paths=<NONE>")
        print()

    if signalled == 0:
        print("<NONE>")
        print()

    print("=== SUMMARY ===")
    print(f"compatibility_metric_rows|{current_metric_rows}")
    print(f"compatibility_effect_estimate_rows|{current_effect_rows}")
    print(f"compatibility_ci_rows|{current_ci_rows}")
    print(f"outcome_json_effect_rows|{json_effect_rows}")
    print(f"outcome_json_ci_rows|{json_ci_rows}")
    print(f"outcomes_with_any_numeric_json_scalar|{any_numeric_json_rows}")
    print(f"outcomes_without_numeric_json_scalar|{38 - any_numeric_json_rows}")
    print()

    print("=== NUMERIC JSON PATH COUNTS ===")
    if numeric_key_paths:
        for path, count in sorted(numeric_key_paths.items(), key=lambda item: (-item[1], item[0])):
            print(f"{path}|{count}")
    else:
        print("<NONE>")
    print()

    print("STAGE 6 AUDIT PASS: read-only quantitative inventory complete; no effect records have been created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
