#!/usr/bin/env python3
"""Export a deterministic, release-build-scoped Evidence Registry v1.1 bundle.

The exporter starts from source versions pinned by a Stage 11 release build and
serializes the corresponding normalized Stage 1-11 scientific state in stable
canonical JSON. It never publishes a release and never mutates reviewed
scientific state.

By default, publication-relevant agent_candidate/proposed rows are a hard
error. Use --allow-unreviewed only for diagnostic export testing before human
review closure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_OUTPUT_ROOT = Path("components/evidence-registry/data/release-builds")


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|",
    ]
    result = subprocess.run(cmd, input=sql, text=True, check=False, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"psql failed:\n{result.stderr.strip()}\n{result.stdout.strip()}")
    return result.stdout.strip()


def q(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def base_cte(build_id: str) -> str:
    return f"""
with pinned as (
  select rb.source_version_id,rb.release_record_id as source_id,rb.release_position
  from public.release_build_source_version rb
  where rb.release_build_id={q(build_id)}
),
pinned_studies as (
  select s.study_id,s.source_id from public.study s
  join pinned p on p.source_id=s.source_id
),
pinned_components as (
  select ic.component_id,ic.study_id from public.intervention_component ic
  join pinned_studies ps on ps.study_id=ic.study_id
),
pinned_outcomes as (
  select eo.outcome_id,eo.study_id from public.evidence_outcome eo
  join pinned_studies ps on ps.study_id=eo.study_id
),
pinned_arms as (
  select sa.arm_id,sa.study_id from public.study_arm sa
  join pinned_studies ps on ps.study_id=sa.study_id
),
pinned_contrasts as (
  select sc.contrast_id,sc.study_id from public.study_contrast sc
  join pinned_studies ps on ps.study_id=sc.study_id
),
pinned_study_quality as (
  select qa.study_quality_assessment_id from public.study_quality_assessment qa
  join pinned_studies ps on ps.study_id=qa.study_id
),
pinned_result_rob as (
  select ra.result_rob_assessment_id from public.result_risk_of_bias_assessment ra
  join pinned_outcomes po on po.outcome_id=ra.outcome_id
),
pinned_propositions as (
  select distinct c.proposition_id
  from public.proposition_evidence_contribution c
  where exists(select 1 from pinned p where p.source_version_id=c.source_version_id)
     or exists(select 1 from pinned p where p.source_id=c.source_id)
     or exists(select 1 from pinned_studies ps where ps.study_id=c.study_id)
     or exists(select 1 from pinned_outcomes po where po.outcome_id=c.outcome_id)
     or exists(select 1 from pinned_contrasts pc where pc.contrast_id=c.contrast_id)
     or exists(
       select 1 from public.effect_estimate ee
       join pinned_outcomes po on po.outcome_id=ee.outcome_id
       where ee.effect_estimate_id=c.effect_estimate_id
     )
),
pinned_syntheses as (
  select bs.body_synthesis_id,bs.proposition_id
  from public.body_evidence_synthesis bs
  join pinned_propositions pp on pp.proposition_id=bs.proposition_id
),
pinned_synthesis_outcomes as (
  select so.synthesis_outcome_id,so.body_synthesis_id,so.proposition_id
  from public.synthesis_outcome so
  join pinned_syntheses ps on ps.body_synthesis_id=so.body_synthesis_id
)
"""


def fetch_rows(container: str, build_id: str, select_sql: str) -> list[dict]:
    sql = base_cte(build_id) + f"""
select coalesce(jsonb_agg(row_json order by row_json::text),'[]'::jsonb)::text
from (
  select to_jsonb(x) as row_json
  from ({select_sql}) x
) q;
"""
    raw = psql(container, sql)
    return json.loads(raw or "[]")


# Each query is explicitly release-build scoped through the pinned CTEs above.
LAYER_QUERIES: dict[str, str] = {
    # Stage 1 / 2
    "source_evidence_role": "select r.* from public.source_evidence_role r where exists(select 1 from pinned p where p.source_id=r.source_id)",
    "source_controller_overlay": "select r.* from public.source_controller_overlay r where exists(select 1 from pinned p where p.source_id=r.source_id)",

    # Stage 3
    "source_version_application_family": "select r.* from public.source_version_application_family r where exists(select 1 from pinned p where p.source_version_id=r.source_version_id)",
    "component_target": "select r.* from public.component_target r where exists(select 1 from pinned_components pc where pc.component_id=r.component_id)",
    "component_target_extraction_status": "select r.* from public.component_target_extraction_status r where exists(select 1 from pinned_components pc where pc.component_id=r.component_id)",
    "mechanism_assertion": "select r.* from public.mechanism_assertion r where exists(select 1 from pinned p where p.source_version_id=r.source_version_id)",
    "source_version_mechanism_status": "select r.* from public.source_version_mechanism_status r where exists(select 1 from pinned p where p.source_version_id=r.source_version_id)",

    # Stage 5 design structure
    "study_arm": "select r.* from public.study_arm r where exists(select 1 from pinned_studies ps where ps.study_id=r.study_id)",
    "arm_component": "select r.* from public.arm_component r where exists(select 1 from pinned_arms pa where pa.arm_id=r.arm_id)",
    "study_contrast": "select r.* from public.study_contrast r where exists(select 1 from pinned_studies ps where ps.study_id=r.study_id)",
    "contrast_arm_member": "select r.* from public.contrast_arm_member r where exists(select 1 from pinned_contrasts pc where pc.contrast_id=r.contrast_id)",
    "arm_outcome_summary": "select r.* from public.arm_outcome_summary r where exists(select 1 from pinned_arms pa where pa.arm_id=r.arm_id)",

    # Stage 4 / 6 outcomes and effects
    "outcome_stage4_classification": "select r.* from public.outcome_stage4_classification r where exists(select 1 from pinned_outcomes po where po.outcome_id=r.outcome_id)",
    "outcome_time_link": "select r.* from public.outcome_time_link r where exists(select 1 from pinned_outcomes po where po.outcome_id=r.outcome_id)",
    "outcome_transfer_axis": "select r.* from public.outcome_transfer_axis r where exists(select 1 from pinned_outcomes po where po.outcome_id=r.outcome_id)",
    "outcome_role_link": "select r.* from public.outcome_role_link r where exists(select 1 from pinned_outcomes po where po.outcome_id=r.outcome_id)",
    "outcome_bridge_evidence": "select r.* from public.outcome_bridge_evidence r where exists(select 1 from pinned_outcomes po where po.outcome_id=r.outcome_id)",
    "outcome_stage6_status": "select r.* from public.outcome_stage6_status r where exists(select 1 from pinned_outcomes po where po.outcome_id=r.outcome_id)",
    "effect_estimate": "select r.* from public.effect_estimate r where exists(select 1 from pinned_outcomes po where po.outcome_id=r.outcome_id)",

    # Stage 7 quality / RoB
    "study_quality_status": "select r.* from public.study_quality_status r where exists(select 1 from pinned_studies ps where ps.study_id=r.study_id)",
    "study_quality_assessment": "select r.* from public.study_quality_assessment r where exists(select 1 from pinned_studies ps where ps.study_id=r.study_id)",
    "result_rob_status": "select r.* from public.result_rob_status r where exists(select 1 from pinned_outcomes po where po.outcome_id=r.outcome_id)",
    "result_risk_of_bias_assessment": "select r.* from public.result_risk_of_bias_assessment r where exists(select 1 from pinned_outcomes po where po.outcome_id=r.outcome_id)",
    "assessment_domain_judgement": "select r.* from public.assessment_domain_judgement r where exists(select 1 from pinned_study_quality psq where psq.study_quality_assessment_id=r.study_quality_assessment_id) or exists(select 1 from pinned_result_rob prr where prr.result_rob_assessment_id=r.result_rob_assessment_id)",

    # Stage 9 population / context
    "study_population_context_status": "select r.* from public.study_population_context_status r where exists(select 1 from pinned_studies ps where ps.study_id=r.study_id)",
    "study_population_context_term": "select r.* from public.study_population_context_term r where exists(select 1 from pinned_studies ps where ps.study_id=r.study_id)",
    "component_delivery_context_status": "select r.* from public.component_delivery_context_status r where exists(select 1 from pinned_components pc where pc.component_id=r.component_id)",
    "component_delivery_context_term": "select r.* from public.component_delivery_context_term r where exists(select 1 from pinned_components pc where pc.component_id=r.component_id)",
    "context_fit_assessment": "select r.* from public.context_fit_assessment r where exists(select 1 from pinned_studies ps where ps.study_id=r.study_id)",

    # Stage 10 harms / implementation / support
    "study_harms_status": "select r.* from public.study_harms_status r where exists(select 1 from pinned_studies ps where ps.study_id=r.study_id)",
    "harm_observation": "select r.* from public.harm_observation r where exists(select 1 from pinned_studies ps where ps.study_id=r.study_id)",
    "study_participation_observation": "select r.* from public.study_participation_observation r where exists(select 1 from pinned_studies ps where ps.study_id=r.study_id)",
    "component_implementation_status": "select r.* from public.component_implementation_status r where exists(select 1 from pinned_components pc where pc.component_id=r.component_id)",
    "component_implementation_observation": "select r.* from public.component_implementation_observation r where exists(select 1 from pinned_components pc where pc.component_id=r.component_id)",
    "component_reporting_assessment": "select r.* from public.component_reporting_assessment r where exists(select 1 from pinned_components pc where pc.component_id=r.component_id)",
    "support_dependence_observation": "select r.* from public.support_dependence_observation r where exists(select 1 from pinned_studies ps where ps.study_id=r.study_id)",
    "boundary_condition_observation": "select r.* from public.boundary_condition_observation r where exists(select 1 from pinned_studies ps where ps.study_id=r.study_id)",

    # Stage 8 body evidence, when a pinned source contributes to a proposition
    "evidence_proposition": "select r.* from public.evidence_proposition r where exists(select 1 from pinned_propositions pp where pp.proposition_id=r.proposition_id)",
    "proposition_evidence_contribution": "select r.* from public.proposition_evidence_contribution r where exists(select 1 from pinned_propositions pp where pp.proposition_id=r.proposition_id)",
    "body_evidence_synthesis": "select r.* from public.body_evidence_synthesis r where exists(select 1 from pinned_syntheses ps where ps.body_synthesis_id=r.body_synthesis_id)",
    "synthesis_outcome": "select r.* from public.synthesis_outcome r where exists(select 1 from pinned_synthesis_outcomes pso where pso.synthesis_outcome_id=r.synthesis_outcome_id)",
    "body_certainty_assessment": "select r.* from public.body_certainty_assessment r where exists(select 1 from pinned_synthesis_outcomes pso where pso.synthesis_outcome_id=r.synthesis_outcome_id)",
    "body_maturity_assessment": "select r.* from public.body_maturity_assessment r where exists(select 1 from pinned_synthesis_outcomes pso where pso.synthesis_outcome_id=r.synthesis_outcome_id)",
    "body_approved_claim": "select r.* from public.body_approved_claim r where exists(select 1 from pinned_propositions pp where pp.proposition_id=r.proposition_id)",

    # Historical source-contribution EML retained as a distinct layer
    "evidence_maturity_assessment": "select r.* from public.evidence_maturity_assessment r where r.scale_version='hrp-eml-v1' and r.scope='record_contribution' and exists(select 1 from pinned p where p.source_id=r.source_id)",

    # Stage 11 active authority relevant to pinned source/source-version keys.
    "scientific_field_authority": "select r.* from public.scientific_field_authority r where r.active=true and exists(select 1 from pinned p where r.subject_key::text like '%'||p.source_id||'%' or r.subject_key::text like '%'||p.source_version_id||'%')",
}


def fetch_build_meta(container: str, build_id: str) -> dict:
    raw = psql(container, f"""
select jsonb_build_object(
  'release_build_id',release_build_id,
  'target_release_id',target_release_id,
  'build_status',build_status,
  'schema_version',schema_version,
  'taxonomy_version',taxonomy_version,
  'gateway_contract_version',gateway_contract_version,
  'source_review_document',source_review_document,
  'source_review_section',source_review_section,
  'prepared_revision',prepared_revision,
  'validated_revision',validated_revision
)::text
from public.evidence_release_build
where release_build_id={q(build_id)};
""")
    if not raw:
        raise SystemExit(f"Release build {build_id!r} not found")
    return json.loads(raw)


def fetch_source_versions(container: str, build_id: str) -> list[dict]:
    raw = psql(container, f"""
select coalesce(jsonb_agg(row_json order by (row_json->>'release_position')::int),'[]'::jsonb)::text
from (
  select jsonb_build_object(
    'release_position',rb.release_position,
    'release_record_id',rb.release_record_id,
    'source_state_sha256',rb.source_state_sha256,
    'source_version',to_jsonb(sv)
  ) as row_json
  from public.release_build_source_version rb
  join public.source_version sv on sv.source_version_id=rb.source_version_id
  where rb.release_build_id={q(build_id)}
) q;
""")
    return json.loads(raw or "[]")


def unresolved_candidate_count(layers: dict[str, list[dict]]) -> tuple[int, list[tuple[str, int]]]:
    total = 0
    detail: list[tuple[str, int]] = []
    for name, rows in layers.items():
        count = 0
        for row in rows:
            if row.get("mapping_source") == "agent_candidate" and row.get("review_status") == "proposed":
                count += 1
            if name == "outcome_stage4_classification":
                for dim in ("distance", "time", "transfer", "role", "bridge"):
                    if row.get(f"{dim}_mapping_source") == "agent_candidate" and row.get(f"{dim}_review_status") == "proposed":
                        count += 1
        if count:
            detail.append((name, count))
            total += count
    return total, detail


def main() -> int:
    ap = argparse.ArgumentParser(description="Export canonical normalized v1.1 scientific state for a Stage 11 release build.")
    ap.add_argument("release_build_id")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    ap.add_argument("--allow-unreviewed", action="store_true", help="Diagnostic only: permit agent_candidate/proposed rows in exported state.")
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    meta = fetch_build_meta(args.container, args.release_build_id)
    if meta["build_status"] not in {"prepared", "validated", "approval_pending", "approved"}:
        raise SystemExit(f"Release build must be prepared/validated before export; got {meta['build_status']!r}")

    source_versions = fetch_source_versions(args.container, args.release_build_id)
    if not source_versions:
        raise SystemExit("Release build contains no pinned source versions")

    layers = {name: fetch_rows(args.container, args.release_build_id, query) for name, query in LAYER_QUERIES.items()}
    unresolved, unresolved_detail = unresolved_candidate_count(layers)
    if unresolved and not args.allow_unreviewed:
        detail = ", ".join(f"{name}={count}" for name, count in unresolved_detail)
        raise SystemExit(
            "Release export blocked: publication-relevant agent_candidate/proposed state remains "
            f"({unresolved} candidate/dimension decisions; {detail}). Use --allow-unreviewed only for diagnostic testing."
        )

    bundle = {
        "snapshot_schema_version": "registry-v1.1-normalized-snapshot-v1",
        "release_build": meta,
        "source_versions": source_versions,
        "layers": layers,
    }
    state_bytes = canonical_bytes(bundle)
    state_sha = sha256_bytes(state_bytes)

    manifest_layers = {
        name: {"count": len(rows), "sha256": sha256_bytes(canonical_bytes(rows))}
        for name, rows in sorted(layers.items())
    }
    manifest_core = {
        "snapshot_schema_version": bundle["snapshot_schema_version"],
        "release_build_id": meta["release_build_id"],
        "target_release_id": meta["target_release_id"],
        "schema_version": meta["schema_version"],
        "taxonomy_version": meta["taxonomy_version"],
        "gateway_contract_version": meta["gateway_contract_version"],
        "prepared_revision": meta["prepared_revision"],
        "source_version_count": len(source_versions),
        "source_versions_sha256": sha256_bytes(canonical_bytes(source_versions)),
        "scientific_state_sha256": state_sha,
        "layers": manifest_layers,
        "unresolved_agent_candidate_decisions": unresolved,
        "diagnostic_allow_unreviewed": bool(args.allow_unreviewed),
    }
    manifest_sha = sha256_bytes(canonical_bytes(manifest_core))
    manifest = dict(manifest_core)
    manifest["export_manifest_sha256"] = manifest_sha

    output_dir = args.output_root / args.release_build_id
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "scientific_state.json"
    manifest_path = output_dir / "manifest.json"
    state_path.write_bytes(state_bytes + b"\n")
    manifest_path.write_bytes(canonical_bytes(manifest) + b"\n")

    print("STAGE 12 NORMALIZED RELEASE EXPORT PASS")
    print(f"release_build_id|{args.release_build_id}")
    print(f"source_versions|{len(source_versions)}")
    print(f"normalized_layers|{len(layers)}")
    print(f"unresolved_agent_candidate_decisions|{unresolved}")
    print(f"scientific_state_sha256|{state_sha}")
    print(f"export_manifest_sha256|{manifest_sha}")
    print(f"scientific_state_path|{state_path}")
    print(f"manifest_path|{manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
