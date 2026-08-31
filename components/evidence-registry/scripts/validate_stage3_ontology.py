#!/usr/bin/env python3
"""Validate Evidence Registry v1.1 Stage 3 ontology and extraction-state invariants.

Local-only by default: queries the running local Supabase Postgres container via
`docker exec`. It does not link to or modify hosted Supabase projects.
"""

from __future__ import annotations

import argparse
import subprocess

DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_RELEASE = "2026-08-23"
DEFAULT_EXPECTED_SOURCES = 18
DEFAULT_EXPECTED_COMPONENTS = 13

EXPECTED_APPLICATION_FAMILIES = {
    "mental_fitness",
    "performance",
    "learning",
    "executive_functioning",
    "wellbeing",
    "longevity",
    "condition_related_support",
}

EXPECTED_TARGET_LOCI = {
    "biological_or_physiological_substrate",
    "current_operating_state",
    "cognitive_operation",
    "affective_or_motivational_process",
    "knowledge_or_mental_representation",
    "explicit_strategy_or_policy",
    "person_niche_coupling",
    "niche_or_activity_system",
}


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str, *, tuples_only: bool = False) -> str:
    cmd = [
        "docker", "exec", "-i", container,
        "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres",
    ]
    if tuples_only:
        cmd.extend(["-A", "-t", "-F", "|"])
    result = run(cmd, input_text=sql, capture=tuples_only)
    return result.stdout.strip() if tuples_only else ""


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def parse_set(raw: str) -> set[str]:
    if not raw.strip():
        return set()
    return {line.strip() for line in raw.splitlines() if line.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Registry v1.1 Stage 3 ontology invariants.")
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--release", default=DEFAULT_RELEASE)
    parser.add_argument("--expected-sources", type=int, default=DEFAULT_EXPECTED_SOURCES)
    parser.add_argument("--expected-components", type=int, default=DEFAULT_EXPECTED_COMPONENTS)
    args = parser.parse_args()

    try:
        running = run(
            ["docker", "inspect", "-f", "{{.State.Running}}", args.container],
            capture=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Local database container {args.container!r} is unavailable.") from exc

    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running.")

    release = sql_literal(args.release)
    errors: list[str] = []

    application_families = parse_set(psql(
        args.container,
        "select application_family from public.application_family_definition order by application_family;",
        tuples_only=True,
    ))
    if application_families != EXPECTED_APPLICATION_FAMILIES:
        errors.append(
            "application family vocabulary mismatch: "
            f"expected {sorted(EXPECTED_APPLICATION_FAMILIES)}, got {sorted(application_families)}"
        )

    target_loci = parse_set(psql(
        args.container,
        "select target_locus from public.target_locus_definition order by target_locus;",
        tuples_only=True,
    ))
    if target_loci != EXPECTED_TARGET_LOCI:
        errors.append(
            "target locus vocabulary mismatch: "
            f"expected {sorted(EXPECTED_TARGET_LOCI)}, got {sorted(target_loci)}"
        )

    counts_sql = f"""
select
  (select count(*)
     from public.source_version sv
     join public.release_source_version rsv on rsv.source_version_id=sv.source_version_id
    where rsv.release_id={release}),
  (select count(*)
     from public.intervention_component ic
     join public.study s on s.study_id=ic.study_id
     join public.evidence_source es on es.source_id=s.source_id
    where es.release_id={release}),
  (select count(*) from public.target_definition),
  (select count(*) from public.mechanism_definition),
  (select count(*)
     from public.component_target_extraction_status ctes
     join public.intervention_component ic on ic.component_id=ctes.component_id
     join public.study s on s.study_id=ic.study_id
     join public.evidence_source es on es.source_id=s.source_id
    where es.release_id={release}),
  (select count(*)
     from public.source_version_mechanism_status svms
     join public.release_source_version rsv on rsv.source_version_id=svms.source_version_id
    where rsv.release_id={release});
"""
    raw_counts = psql(args.container, counts_sql, tuples_only=True).split("|")
    if len(raw_counts) != 6 or any(v == "" for v in raw_counts):
        raise SystemExit(f"STAGE 3 ONTOLOGY INVALID: unexpected count output {raw_counts!r}")

    (
        source_versions,
        intervention_components,
        target_definitions,
        mechanism_definitions,
        component_target_statuses,
        source_mechanism_statuses,
    ) = map(int, raw_counts)

    if source_versions != args.expected_sources:
        errors.append(f"source_versions: expected {args.expected_sources}, got {source_versions}")
    if intervention_components != args.expected_components:
        errors.append(f"intervention_components: expected {args.expected_components}, got {intervention_components}")
    if component_target_statuses != args.expected_components:
        errors.append(
            f"component_target_statuses: expected {args.expected_components}, got {component_target_statuses}"
        )
    if source_mechanism_statuses != args.expected_sources:
        errors.append(
            f"source_mechanism_statuses: expected {args.expected_sources}, got {source_mechanism_statuses}"
        )
    if target_definitions < 1:
        errors.append("target ontology is empty")
    if mechanism_definitions < 1:
        errors.append("mechanism ontology is empty")

    integrity_sql = f"""
select
  (select count(*)
     from public.intervention_component ic
     join public.study s on s.study_id=ic.study_id
     join public.evidence_source es on es.source_id=s.source_id
    where es.release_id={release}
      and not exists (
        select 1 from public.component_target_extraction_status ctes
         where ctes.component_id=ic.component_id
      )),

  (select count(*)
     from public.source_version sv
     join public.release_source_version rsv on rsv.source_version_id=sv.source_version_id
    where rsv.release_id={release}
      and not exists (
        select 1 from public.source_version_mechanism_status svms
         where svms.source_version_id=sv.source_version_id
      )),

  (select count(*)
     from public.component_target_extraction_status ctes
    where ctes.extraction_status='reviewed_mapped'
      and not exists (
        select 1 from public.component_target ct
         where ct.component_id=ctes.component_id
           and ct.review_status <> 'rejected'
      )),

  (select count(*)
     from public.component_target_extraction_status ctes
    where ctes.extraction_status='reviewed_no_mapping'
      and exists (
        select 1 from public.component_target ct
         where ct.component_id=ctes.component_id
           and ct.review_status <> 'rejected'
      )),

  (select count(*)
     from public.source_version_mechanism_status svms
    where svms.extraction_status in ('reviewed_mapped','reviewed_complete')
      and not exists (
        select 1 from public.mechanism_assertion ma
         where ma.source_version_id=svms.source_version_id
           and ma.review_status <> 'rejected'
      )),

  (select count(*)
     from public.source_version_mechanism_status svms
    where svms.extraction_status='reviewed_no_mapping'
      and exists (
        select 1 from public.mechanism_assertion ma
         where ma.source_version_id=svms.source_version_id
           and ma.review_status <> 'rejected'
      )),

  (select count(*)
     from public.mechanism_assertion ma
     join public.intervention_component ic on ic.component_id=ma.component_id
     join public.study s on s.study_id=ic.study_id
     join public.evidence_source es on es.source_id=s.source_id
     join public.canonical_source_identity csi
       on csi.identity_scheme='legacy_source_id'
      and csi.normalized_value=lower(es.source_id)
     join public.source_version sv on sv.canonical_source_id=csi.canonical_source_id
    where ma.component_id is not null
      and ma.source_version_id <> sv.source_version_id),

  (select count(*)
     from public.source_version_application_family svaf
     left join public.release_source_version rsv on rsv.source_version_id=svaf.source_version_id
    where rsv.source_version_id is null),

  (select count(*)
     from public.target_definition td
     left join public.target_locus_definition tld on tld.target_locus=td.target_locus
    where tld.target_locus is null),

  (select count(*)
     from public.target_framework_mapping tfm
    where tfm.framework not in ('trident_g','apc','h_agi','csi','iqm_product_architecture')),

  (select count(*)
     from public.mechanism_framework_mapping mfm
    where mfm.framework not in ('trident_g','apc','h_agi','csi','iqm_product_architecture'));
"""
    raw_integrity = psql(args.container, integrity_sql, tuples_only=True).split("|")
    labels = [
        "components_without_target_status",
        "source_versions_without_mechanism_status",
        "reviewed_mapped_targets_without_mapping",
        "reviewed_no_mapping_targets_with_mapping",
        "reviewed_mapped_mechanisms_without_assertion",
        "reviewed_no_mapping_mechanisms_with_assertion",
        "mechanism_component_source_mismatch",
        "application_family_mapping_without_release_membership",
        "invalid_target_locus_reference",
        "invalid_target_framework_identifier",
        "invalid_mechanism_framework_identifier",
    ]
    if len(raw_integrity) != len(labels) or any(v == "" for v in raw_integrity):
        raise SystemExit(f"STAGE 3 ONTOLOGY INVALID: unexpected integrity output {raw_integrity!r}")

    integrity = dict(zip(labels, map(int, raw_integrity)))
    errors.extend(f"{name}: {value} failures" for name, value in integrity.items() if value != 0)

    # Prove that Stage 1 mechanism-only evidence can be represented without
    # manufacturing an intervention component. The transaction is rolled back,
    # including any audit rows produced by the insert.
    mechanism_only_sql = f"""
begin;

with candidate as (
  select sv.source_version_id
    from public.source_evidence_role ser
    join public.canonical_source_identity csi
      on csi.identity_scheme='legacy_source_id'
     and csi.normalized_value=lower(ser.source_id)
    join public.source_version sv
      on sv.canonical_source_id=csi.canonical_source_id
    join public.release_source_version rsv
      on rsv.source_version_id=sv.source_version_id
   where ser.evidence_role='mechanism'
     and rsv.release_id={release}
   order by ser.source_id
   limit 1
), mechanism as (
  select mechanism_id
    from public.mechanism_definition
   order by mechanism_id
   limit 1
)
insert into public.mechanism_assertion (
  source_version_id,
  mechanism_id,
  study_id,
  component_id,
  assertion_type,
  assertion_direction,
  support_summary,
  mapping_source,
  review_status
)
select
  candidate.source_version_id,
  mechanism.mechanism_id,
  null,
  null,
  'hrp_candidate',
  'unclear',
  'Stage 3 validator rollback-only mechanism-only representation test.',
  'migration',
  'proposed'
from candidate cross join mechanism;

select case when count(*)=1 then 1 else 0 end
from public.mechanism_assertion
where support_summary='Stage 3 validator rollback-only mechanism-only representation test.'
  and study_id is null
  and component_id is null;

rollback;
"""
    try:
        mechanism_only_result = psql(args.container, mechanism_only_sql, tuples_only=True)
        # psql may include command-status lines around the SELECT; require the
        # transactional SELECT result to contain a standalone 1.
        if "1" not in {line.strip() for line in mechanism_only_result.splitlines()}:
            errors.append("mechanism-only assertion representation test did not produce exactly one rollback-only row")
    except subprocess.CalledProcessError as exc:
        errors.append(f"mechanism-only assertion representation test failed: {exc}")

    if errors:
        print("STAGE 3 ONTOLOGY INVALID")
        for error in errors:
            print("-", error)
        return 1

    print(
        "STAGE 3 ONTOLOGY VALID: "
        f"{len(application_families)} application families / "
        f"{len(target_loci)} target loci / "
        f"{args.expected_components} explicit component target states / "
        f"{args.expected_sources} explicit source mechanism states"
    )
    print(f"target_definitions={target_definitions}; mechanism_definitions={mechanism_definitions}")
    print("ontology_integrity: all zero failures")
    print("mechanism_without_intervention_component: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
