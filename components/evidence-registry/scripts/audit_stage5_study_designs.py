#!/usr/bin/env python3
"""Read-only Stage 5 audit of seed study-design/arm/contrast signals.

This script does not create arms, contrasts, components or review decisions.
It inventories the 18-source seed so Stage 5 can be designed/backfilled from
what the reviewed records actually contain rather than from assumptions.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter

DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_RELEASE = "2026-08-23"


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


def safe_json(value: str, fallback):
    try:
        return json.loads(value) if value else fallback
    except json.JSONDecodeError:
        return fallback


def compact(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Stage 5 study-arm/contrast signals in local seed Registry.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--release", default=DEFAULT_RELEASE)
    args = ap.parse_args()

    sql = f"""
select
  es.source_id,
  s.study_id,
  coalesce(s.design, ''),
  coalesce(s.comparator_summary, ''),
  s.sample_json::text,
  es.raw_record->'protocol'::text,
  coalesce((
    select string_agg(ser.evidence_role, ',' order by ser.primary_role desc, ser.evidence_role)
    from public.source_evidence_role ser
    where ser.source_id = es.source_id
  ), ''),
  coalesce((
    select string_agg(ic.component_name || ' [' || ic.route || ']', '; ' order by ic.component_id)
    from public.intervention_component ic
    where ic.study_id = s.study_id
  ), '')
from public.study s
join public.evidence_source es on es.source_id = s.source_id
where es.release_id = '{args.release.replace("'", "''")}'
order by es.source_id;
"""

    raw = run_psql(args.container, sql)
    rows = [line.split("\t", 7) for line in raw.splitlines() if line.strip()]

    if len(rows) != 18:
        raise SystemExit(f"Expected 18 seed studies, found {len(rows)}")

    design_flags = Counter()
    role_counts = Counter()
    explicit_condition_studies = 0
    explicit_active_control_studies = 0
    multi_component_studies = 0
    comparator_present = 0

    print(f"STAGE 5 STUDY-DESIGN AUDIT: {len(rows)} historical studies")
    print()

    print("=== STUDY-BY-STUDY DESIGN INVENTORY ===")
    for parts in rows:
        if len(parts) != 8:
            raise SystemExit(f"Unexpected database row with {len(parts)} fields: {parts!r}")

        source_id, study_id, design, comparator, sample_raw, protocol_raw, roles_raw, components_raw = parts
        sample = safe_json(sample_raw, {})
        protocol = safe_json(protocol_raw, {})
        roles = [r for r in roles_raw.split(",") if r]

        for role in roles:
            role_counts[role] += 1

        d = design.lower()
        flags = []
        for token, label in [
            ("random", "randomized_signal"),
            ("quasi", "quasi_signal"),
            ("factorial", "factorial_signal"),
            ("three-group", "three_group_signal"),
            ("three group", "three_group_signal"),
            ("longitudinal", "longitudinal_signal"),
            ("within-subject", "within_subject_signal"),
            ("within subject", "within_subject_signal"),
            ("crossover", "crossover_signal"),
            ("cross-over", "crossover_signal"),
            ("review", "review_signal"),
            ("observational", "observational_signal"),
        ]:
            if token in d and label not in flags:
                flags.append(label)
                design_flags[label] += 1

        conditions = protocol.get("conditions") if isinstance(protocol, dict) else None
        if isinstance(conditions, list) and conditions:
            explicit_condition_studies += 1

        active_control = protocol.get("active_control") if isinstance(protocol, dict) else None
        if active_control:
            explicit_active_control_studies += 1

        protocol_components = protocol.get("components") if isinstance(protocol, dict) else None
        if isinstance(protocol_components, list) and len(protocol_components) > 1:
            multi_component_studies += 1

        if comparator:
            comparator_present += 1

        protocol_keys = sorted(protocol.keys()) if isinstance(protocol, dict) else []

        print(f"{source_id}|study_id={study_id}")
        print(f"  roles={','.join(roles) or '<NONE>'}")
        print(f"  design={design or '<NULL>'}")
        print(f"  lexical_design_flags={','.join(flags) or '<NONE>'}")
        print(f"  comparator={comparator or '<NULL>'}")
        print(f"  sample={compact(sample)}")
        print(f"  normalized_components={components_raw or '<NONE>'}")
        print(f"  protocol_keys={','.join(protocol_keys) or '<NONE>'}")
        print(f"  explicit_conditions={compact(conditions) if isinstance(conditions, list) else '<NONE>'}")
        print(f"  explicit_active_control={active_control or '<NONE>'}")
        if isinstance(protocol_components, list):
            names = []
            for item in protocol_components:
                if isinstance(item, dict):
                    names.append(item.get("name") or item.get("component") or "<unnamed>")
                else:
                    names.append(str(item))
            print(f"  protocol_component_names={compact(names)}")
        else:
            print("  protocol_component_names=<NONE>")
        print()

    print("=== EVIDENCE ROLE COUNTS ===")
    for key in sorted(role_counts):
        print(f"{key}|{role_counts[key]}")
    print()

    print("=== DESIGN SIGNAL COUNTS ===")
    for key in sorted(design_flags):
        print(f"{key}|{design_flags[key]}")
    print(f"comparator_summary_present|{comparator_present}")
    print(f"explicit_protocol_conditions|{explicit_condition_studies}")
    print(f"explicit_protocol_active_control|{explicit_active_control_studies}")
    print(f"multi_component_protocols|{multi_component_studies}")
    print()

    print("STAGE 5 AUDIT PASS: read-only inventory complete; no arms or contrasts have been created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
