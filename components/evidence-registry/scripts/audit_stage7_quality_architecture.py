#!/usr/bin/env python3
"""Read-only Stage 7 audit of current quality / RoB architecture.

This script does not create or modify quality assessments. It inventories the
historical compatibility table and the seed's study/result structure so Stage 7
can be implemented without fabricating risk-of-bias, reporting or certainty
judgements.
"""
from __future__ import annotations

import argparse
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


def scalar(container: str, sql: str) -> int:
    raw = run_psql(container, sql).strip()
    return int(raw or "0")


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Stage 7 quality / risk-of-bias architecture in the local seed Registry.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--release", default=DEFAULT_RELEASE)
    args = ap.parse_args()

    release = args.release.replace("'", "''")

    quality_rows = run_psql(args.container, """
select
  qa.quality_assessment_id,
  qa.source_id,
  qa.assessment_level,
  qa.tool,
  coalesce(qa.judgement,''),
  coalesce(qa.assessor,''),
  coalesce(qa.assessed_on::text,'')
from public.quality_assessment qa
order by qa.quality_assessment_id;
""")

    quality_count = 0
    levels = Counter()
    tools = Counter()
    if quality_rows:
        for line in quality_rows.splitlines():
            parts = line.split("\t")
            if len(parts) != 7:
                raise SystemExit(f"Unexpected quality_assessment row: {parts!r}")
            quality_count += 1
            levels[parts[2]] += 1
            tools[parts[3]] += 1

    structure_sql = f"""
select
  (select count(*) from public.evidence_source es where es.release_id='{release}'),
  (select count(*) from public.study s join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}'),
  (select count(*) from public.evidence_outcome eo join public.study s on s.study_id=eo.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}'),
  (select count(*) from public.effect_estimate ee join public.evidence_outcome eo on eo.outcome_id=ee.outcome_id join public.study s on s.study_id=eo.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}'),
  (select count(*) from public.study_contrast sc join public.study s on s.study_id=sc.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}'),
  (select count(*) from public.intervention_component ic join public.study s on s.study_id=ic.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='{release}'),
  (select count(*) from public.evidence_synthesis),
  (select count(*) from public.approved_claim);
"""
    structure = run_psql(args.container, structure_sql)
    parts = structure.split("\t") if structure else []
    if len(parts) != 8:
        raise SystemExit(f"Unexpected structure count row: {structure!r}")

    sources, studies, outcomes, effects, contrasts, components, syntheses, claims = map(int, parts)

    design_rows = run_psql(args.container, f"""
select
  es.source_id,
  coalesce(s.design,''),
  coalesce((
    select string_agg(ser.evidence_role, ',' order by ser.primary_role desc, ser.evidence_role)
    from public.source_evidence_role ser
    where ser.source_id=es.source_id
  ),'')
from public.study s
join public.evidence_source es on es.source_id=s.source_id
where es.release_id='{release}'
order by es.source_id;
""")

    family_counts = Counter()
    role_counts = Counter()
    study_inventory = []

    for line in design_rows.splitlines() if design_rows else []:
        parts = line.split("\t")
        while len(parts) < 3:
            parts.append("")
        source_id, design, roles_raw = parts[:3]
        d = design.lower()
        roles = [r for r in roles_raw.split(",") if r]
        for role in roles:
            role_counts[role] += 1

        families = []
        if "systematic review" in d or "meta-analysis" in d or "scoping review" in d:
            families.append("review_or_synthesis")
        if "random" in d:
            families.append("randomized")
        if "quasi" in d:
            families.append("nonrandomized_or_quasi")
        if "survey" in d or "observational" in d or "time-lagged" in d:
            families.append("observational")
        if "experiment" in d and "random" not in d and "quasi" not in d:
            families.append("experimental_nonrandomized_or_unclear")
        if "fMRI".lower() in d or "mechanism" in roles:
            families.append("mechanism_or_neuroscience")
        if "measurement" in roles:
            families.append("measurement")
        if not families:
            families.append("other_or_unclear")

        for family in set(families):
            family_counts[family] += 1
        study_inventory.append((source_id, design, roles, sorted(set(families))))

    print(f"STAGE 7 QUALITY ARCHITECTURE AUDIT: release={args.release}")
    print()
    print("=== CURRENT COMPATIBILITY QUALITY TABLE ===")
    print(f"quality_assessment_rows|{quality_count}")
    if levels:
        for key in sorted(levels):
            print(f"assessment_level:{key}|{levels[key]}")
    else:
        print("assessment_level:<NONE>|0")
    if tools:
        for key in sorted(tools):
            print(f"tool:{key}|{tools[key]}")
    else:
        print("tool:<NONE>|0")
    print()

    print("=== SCIENTIFIC SUBJECT COUNTS ===")
    print(f"sources|{sources}")
    print(f"studies|{studies}")
    print(f"outcomes|{outcomes}")
    print(f"first_class_effect_estimates|{effects}")
    print(f"study_contrasts|{contrasts}")
    print(f"intervention_components|{components}")
    print(f"evidence_syntheses|{syntheses}")
    print(f"approved_claims|{claims}")
    print()

    print("=== EVIDENCE ROLE COUNTS ===")
    for key in sorted(role_counts):
        print(f"{key}|{role_counts[key]}")
    print()

    print("=== DESIGN FAMILY SIGNALS (AUDIT ONLY; NOT TOOL ASSIGNMENTS) ===")
    for key in sorted(family_counts):
        print(f"{key}|{family_counts[key]}")
    print()

    print("=== STUDY INVENTORY ===")
    for source_id, design, roles, families in study_inventory:
        print(f"{source_id}|roles={','.join(roles) or '<NONE>'}|families={','.join(families)}|design={design or '<NULL>'}")
    print()

    if quality_count == 0:
        print("SEED QUALITY JUDGEMENT BOUNDARY: PASS (0 formal quality/RoB rows; Stage 7 must create status only, not inferred judgements)")
    else:
        print("SEED QUALITY JUDGEMENT BOUNDARY: REVIEW REQUIRED (formal compatibility quality rows exist and must be conserved/mapped)")

    if syntheses == 0:
        print("BODY CERTAINTY BOUNDARY: PASS (0 synthesis subjects; GRADE/body certainty must remain deferred to Stage 8)")
    else:
        print("BODY CERTAINTY BOUNDARY: REVIEW REQUIRED (existing synthesis rows need explicit handling before Stage 8)")

    print("STAGE 7 AUDIT PASS: read-only inventory complete; no quality, RoB or certainty judgement has been created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
