#!/usr/bin/env python3
"""Read-only Stage 12 audit: backfill review, historical parity, and release blockers."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=False, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|",
    ]
    result = run(cmd, input_text=sql, capture=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "<no PostgreSQL stderr>"
        stdout = result.stdout.strip()
        extra = f"\nstdout:\n{stdout}" if stdout else ""
        raise RuntimeError(f"psql failed with exit status {result.returncode}:\n{stderr}{extra}")
    return result.stdout.strip()


def scalar(container: str, sql: str) -> int:
    value = psql(container, sql)
    return int(value or "0")


def qident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def print_section(title: str) -> None:
    print(f"=== {title} ===")


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Stage 12 backfill/parity/release readiness without mutation.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    print_section("HISTORICAL RELEASE / GATEWAY PARITY")
    print("release_id|status|source_versions")
    print(psql(args.container, """
select er.release_id,er.status,count(rsv.source_version_id)
from public.evidence_release er
left join public.release_source_version rsv on rsv.release_id=er.release_id
where er.release_id='2026-08-23'
group by er.release_id,er.status;
"""))
    print("sources|studies|components|outcomes|record_eml|gateway_releases|gateway_cards|gateway_claims")
    print(psql(args.container, """
select
 (select count(*) from public.evidence_source where release_id='2026-08-23'),
 (select count(*) from public.study s join public.evidence_source es on es.source_id=s.source_id where es.release_id='2026-08-23'),
 (select count(*) from public.intervention_component ic join public.study s on s.study_id=ic.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='2026-08-23'),
 (select count(*) from public.evidence_outcome eo join public.study s on s.study_id=eo.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id='2026-08-23'),
 (select count(*) from public.evidence_maturity_assessment ema join public.evidence_source es on es.source_id=ema.source_id where es.release_id='2026-08-23' and ema.scale_version='hrp-eml-v1' and ema.scope='record_contribution'),
 (select count(*) from public.csi_gateway_release where evidence_release_id='2026-08-23'),
 (select count(*) from public.csi_gateway_evidence_card where evidence_release_id='2026-08-23'),
 (select count(*) from public.csi_gateway_claim where evidence_release_id='2026-08-23');
"""))
    print("record_contribution_eml_distribution")
    print(psql(args.container, """
select maturity_level,count(*)
from public.evidence_maturity_assessment ema
join public.evidence_source es on es.source_id=ema.source_id
where es.release_id='2026-08-23' and ema.scale_version='hrp-eml-v1' and ema.scope='record_contribution'
group by maturity_level order by maturity_level;
"""))

    print_section("SOURCE VERSION IDENTITY")
    print("canonical_sources|source_versions|release_memberships")
    print(psql(args.container, """
select
 (select count(*) from public.canonical_source),
 (select count(*) from public.source_version),
 (select count(*) from public.release_source_version where release_id='2026-08-23');
"""))
    print("version_status|count")
    print(psql(args.container, "select version_status,count(*) from public.source_version group by version_status order by version_status;"))

    print_section("GENERIC AGENT-CANDIDATE REVIEW STATE")
    tables_raw = psql(args.container, """
select table_name
from information_schema.columns
where table_schema='public' and column_name in ('mapping_source','review_status')
group by table_name
having count(distinct column_name)=2
order by table_name;
""")
    tables = [x for x in tables_raw.splitlines() if x]
    unresolved_generic = 0
    print("table_name|mapping_source|review_status|count")
    for table in tables:
        ident = qident(table)
        rows = psql(args.container, f"""
select {table!r}::text,mapping_source,review_status,count(*)
from public.{ident}
where mapping_source='agent_candidate' or review_status in ('proposed','reviewed','approved','rejected')
group by mapping_source,review_status
order by mapping_source,review_status;
""")
        if rows:
            print(rows)
        unresolved_generic += scalar(
            args.container,
            f"select count(*) from public.{ident} where mapping_source='agent_candidate' and review_status='proposed';",
        )

    print_section("STAGE 4 DIMENSION-SPECIFIC REVIEW STATE")
    stage4_dims = ["distance", "time", "transfer", "role", "bridge"]
    stage4_unresolved = 0
    print("dimension|mapping_source|review_status|count")
    for dim in stage4_dims:
        rows = psql(args.container, f"""
select {dim!r}::text,{dim}_mapping_source,{dim}_review_status,count(*)
from public.outcome_stage4_classification
group by {dim}_mapping_source,{dim}_review_status
order by {dim}_mapping_source,{dim}_review_status;
""")
        if rows:
            print(rows)
        stage4_unresolved += scalar(
            args.container,
            f"select count(*) from public.outcome_stage4_classification where {dim}_mapping_source='agent_candidate' and {dim}_review_status='proposed';",
        )

    print_section("QUALITY / ROB COMPLETENESS")
    print("study_quality_assessments|result_rob_assessments|study_status_rows|result_status_rows")
    print(psql(args.container, """
select
 (select count(*) from public.study_quality_assessment),
 (select count(*) from public.result_risk_of_bias_assessment),
 (select count(*) from public.study_quality_status),
 (select count(*) from public.result_rob_status);
"""))
    print("study_quality_status")
    print(psql(args.container, "select assessment_status,count(*) from public.study_quality_status group by assessment_status order by assessment_status;"))
    print("result_rob_status")
    print(psql(args.container, "select assessment_status,count(*) from public.result_rob_status group by assessment_status order by assessment_status;"))

    print_section("STAGE 8 BODY EVIDENCE")
    print("propositions|contributions|body_syntheses|synthesis_outcomes|body_certainty|body_eml|body_claims")
    print(psql(args.container, """
select
 (select count(*) from public.evidence_proposition),
 (select count(*) from public.proposition_evidence_contribution),
 (select count(*) from public.body_evidence_synthesis),
 (select count(*) from public.synthesis_outcome),
 (select count(*) from public.body_certainty_assessment),
 (select count(*) from public.body_maturity_assessment),
 (select count(*) from public.body_approved_claim);
"""))

    print_section("STAGE 11 AUTHORITY / RELEASE BUILDS")
    print("processing_runs|field_candidates|adjudications|active_authorities|release_builds|published_builds")
    print(psql(args.container, """
select
 (select count(*) from public.scientific_processing_run),
 (select count(*) from public.scientific_field_candidate),
 (select count(*) from public.scientific_field_adjudication),
 (select count(*) from public.scientific_field_authority where active=true),
 (select count(*) from public.evidence_release_build),
 (select count(*) from public.evidence_release_build where build_status='published');
"""))
    print("release_id|status")
    print(psql(args.container, "select release_id,status from public.evidence_release order by released_on,release_id;"))

    print_section("NORMALIZED RELEASE EXPORT COVERAGE")
    exporter_path = REPO_ROOT / "components/evidence-registry/scripts/export_stage12_release_bundle.py"
    exporter_text = exporter_path.read_text(encoding="utf-8") if exporter_path.exists() else ""
    required_tokens = [
        "source_evidence_role",
        "source_version_application_family",
        "component_target",
        "mechanism_assertion",
        "study_arm",
        "study_contrast",
        "outcome_stage4_classification",
        "effect_estimate",
        "study_quality_status",
        "result_rob_status",
        "study_population_context_term",
        "harm_observation",
        "component_implementation_observation",
        "support_dependence_observation",
        "boundary_condition_observation",
        "evidence_maturity_assessment",
    ]
    covered = [token for token in required_tokens if token in exporter_text]
    missing = [token for token in required_tokens if token not in exporter_text]
    print(f"normalized_release_export_coverage|{len(covered)}/{len(required_tokens)}")
    print("covered_tokens|" + (",".join(covered) if covered else "<none>"))
    print("missing_tokens|" + (",".join(missing) if missing else "<none>"))

    print_section("STAGE 12 PUBLICATION BLOCKERS")
    blockers: list[str] = []
    if unresolved_generic:
        blockers.append(f"unresolved_agent_candidate_proposed_rows={unresolved_generic}")
    if stage4_unresolved:
        blockers.append(f"unresolved_stage4_dimension_candidates={stage4_unresolved}")
    study_quality = scalar(args.container, "select count(*) from public.study_quality_assessment;")
    result_rob = scalar(args.container, "select count(*) from public.result_risk_of_bias_assessment;")
    if study_quality == 0 and result_rob == 0:
        blockers.append("initial_formal_quality_rob_appraisal_pending")
    propositions = scalar(args.container, "select count(*) from public.evidence_proposition;")
    syntheses = scalar(args.container, "select count(*) from public.body_evidence_synthesis;")
    if propositions == 0 or syntheses == 0:
        blockers.append("bounded_stage8_proposition_synthesis_proof_pending")
    if missing:
        blockers.append(f"normalized_release_export_incomplete={len(missing)}_required_tokens_missing")
    if scalar(args.container, "select count(*) from public.evidence_release where release_id<>'2026-08-23';") != 0:
        blockers.append("unexpected_nonhistorical_release_already_present")

    print("blocker|status")
    if blockers:
        for blocker in blockers:
            print(f"{blocker}|OPEN")
    else:
        print("none|READY_FOR_GOVERNED_RELEASE_BUILD")

    print("STAGE 12 AUDIT PASS: read-only backfill/parity/release-readiness inventory completed; no review or publication mutation performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
