#!/usr/bin/env python3
"""Rebuild the approved HRP seed release into the local Supabase database.

Local-only by design: this script talks directly to the running local Postgres
container via `docker exec`. It never calls `supabase link`, `db push`, or any
`--linked` command, and it does not require production credentials.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RELEASE = "2026-08-23"
DEFAULT_CONTAINER = "supabase_db_research-platform"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        check=True,
        capture_output=capture,
    )


def sql_literal(value: object | None) -> str:
    if value is None:
        return "null"
    return "'" + str(value).replace("'", "''") + "'"


def psql(container: str, sql: str, *, tuples_only: bool = False) -> str:
    cmd = ["docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres"]
    if tuples_only:
        cmd.extend(["-A", "-t", "-F", "|"])
    completed = run(cmd, input_text=sql, capture=tuples_only)
    return completed.stdout.strip() if tuples_only else ""


def extract_block(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]


def assert_local_container(container: str) -> None:
    try:
        out = run(["docker", "inspect", "-f", "{{.State.Running}}", container], capture=True).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"Local database container {container!r} is not available. Run `supabase start --network-id local-network` first."
        ) from exc
    if out != "true":
        raise SystemExit(f"Local database container {container!r} is not running.")


def validate_files(release_dir: Path) -> None:
    records_dir = release_dir / "records"
    manifest = release_dir / "manifest.json"
    taxonomy = REPO_ROOT / "components/evidence-registry/schema/taxonomy.v1.json"
    run([
        sys.executable,
        str(REPO_ROOT / "components/evidence-registry/scripts/validate_registry.py"),
        str(records_dir),
        "--taxonomy",
        str(taxonomy),
        "--manifest",
        str(manifest),
    ])
    run([sys.executable, str(REPO_ROOT / "components/evidence-registry/scripts/validate_csi_gateway.py")])


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap the approved HRP Registry release into local Supabase only.")
    parser.add_argument("--release", default=DEFAULT_RELEASE)
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    args = parser.parse_args()

    release_dir = REPO_ROOT / "components/evidence-registry/data/releases" / args.release
    manifest_path = release_dir / "manifest.json"
    records_dir = release_dir / "records"
    if not manifest_path.exists() or not records_dir.exists():
        raise SystemExit(f"Release files not found: {release_dir}")

    assert_local_container(args.container)
    validate_files(release_dir)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("release_id") != args.release:
        raise SystemExit("Manifest release_id does not match requested release.")

    print(f"Bootstrapping approved local release {args.release}...")

    release_sql = f"""
insert into public.evidence_release (
  release_id, released_on, schema_version, taxonomy_version,
  source_review_document, source_review_section, status, notes
) values (
  {sql_literal(manifest['release_id'])},
  {sql_literal(manifest['generated_on'])}::date,
  {sql_literal(manifest['schema_version'])},
  {sql_literal(manifest['taxonomy_version'])},
  {sql_literal(manifest['source_review_document'])},
  {sql_literal(manifest.get('source_review_section'))},
  {sql_literal(manifest['status'])},
  {sql_literal(manifest.get('corpus_basis'))}
)
on conflict (release_id) do update set
  released_on = excluded.released_on,
  schema_version = excluded.schema_version,
  taxonomy_version = excluded.taxonomy_version,
  source_review_document = excluded.source_review_document,
  source_review_section = excluded.source_review_section,
  status = excluded.status,
  notes = excluded.notes;
"""
    psql(args.container, release_sql)

    record_files = sorted(records_dir.glob("*.json"))
    expected_records = int(manifest["record_count"])
    if len(record_files) != expected_records:
        raise SystemExit(f"Manifest expects {expected_records} records; found {len(record_files)}.")

    print(f"Importing {len(record_files)} reviewed evidence records...")
    for record_path in record_files:
        payload = record_path.read_text(encoding="utf-8")
        psql(
            args.container,
            "select private.import_evidence_record($hrp_record$\n"
            + payload
            + "\n$hrp_record$::jsonb);",
        )

    eml_path = REPO_ROOT / "supabase/migrations/20260823230820_add_hrp_evidence_maturity_v1.sql"
    eml_text = eml_path.read_text(encoding="utf-8")
    eml_seed = extract_block(
        eml_text,
        "insert into public.evidence_maturity_assessment (",
        "\nalter table public.evidence_maturity_level_definition enable row level security;",
    )

    print("Restoring source-level EML mappings...")
    psql(
        args.container,
        f"""
delete from public.evidence_maturity_assessment
where scale_version = 'hrp-eml-v1'
  and scope = 'record_contribution'
  and source_id in (
    select source_id from public.evidence_source where release_id = {sql_literal(args.release)}
  );
""",
    )
    psql(args.container, eml_seed)

    gateway_path = REPO_ROOT / "supabase/migrations/20260823201955_add_csi_evidence_gateway_v1.sql"
    gateway_text = gateway_path.read_text(encoding="utf-8")
    gateway_publication = extract_block(
        gateway_text,
        "insert into public.csi_gateway_release (",
        "\nalter table public.csi_gateway_contract enable row level security;",
    )

    print("Rebuilding local CSI Gateway seed publication...")
    psql(
        args.container,
        f"""
delete from public.csi_gateway_claim where evidence_release_id = {sql_literal(args.release)};
delete from public.csi_gateway_evidence_card where evidence_release_id = {sql_literal(args.release)};
delete from public.csi_gateway_release where evidence_release_id = {sql_literal(args.release)};
""",
    )
    psql(args.container, gateway_publication)

    eml_projection = extract_block(
        eml_text,
        "update public.csi_gateway_evidence_card card",
        "\ncreate index csi_gateway_evidence_maturity_idx",
    )
    psql(args.container, eml_projection)

    counts_sql = f"""
select
  (select count(*) from public.evidence_source where release_id = {sql_literal(args.release)}),
  (select count(*) from public.study s join public.evidence_source es on es.source_id=s.source_id where es.release_id = {sql_literal(args.release)}),
  (select count(*) from public.intervention_component ic join public.study s on s.study_id=ic.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id = {sql_literal(args.release)}),
  (select count(*) from public.evidence_outcome eo join public.study s on s.study_id=eo.study_id join public.evidence_source es on es.source_id=s.source_id where es.release_id = {sql_literal(args.release)}),
  (select count(*) from public.evidence_maturity_assessment ema join public.evidence_source es on es.source_id=ema.source_id where es.release_id = {sql_literal(args.release)} and ema.scale_version='hrp-eml-v1' and ema.scope='record_contribution'),
  (select count(*) from public.csi_gateway_release where evidence_release_id = {sql_literal(args.release)}),
  (select count(*) from public.csi_gateway_evidence_card where evidence_release_id = {sql_literal(args.release)}),
  (select count(*) from public.csi_gateway_claim where evidence_release_id = {sql_literal(args.release)}),
  (select count(*) from public.csi_gateway_evidence_card where evidence_release_id = {sql_literal(args.release)} and maturity_level is not null);
"""
    actual = psql(args.container, counts_sql, tuples_only=True)
    expected = f"{expected_records}|{expected_records}|13|38|{expected_records}|1|{expected_records}|0|{expected_records}"

    print("sources|studies|components|outcomes|eml|gateway_releases|gateway_cards|gateway_claims|gateway_cards_with_eml")
    print(actual)
    if actual != expected:
        raise SystemExit(f"LOCAL REGISTRY BASELINE FAIL: expected {expected}, got {actual}")

    stage2_validator = REPO_ROOT / "components/evidence-registry/scripts/validate_stage2_identity.py"
    if stage2_validator.exists():
        print("Validating Stage 2 canonical source identity/version layer...")
        run([
            sys.executable,
            str(stage2_validator),
            "--container", args.container,
            "--release", args.release,
            "--expected", str(expected_records),
        ])

    stage3_mapper = REPO_ROOT / "components/evidence-registry/scripts/apply_stage3_seed_mappings.py"
    if stage3_mapper.exists():
        print("Applying Stage 3 candidate application/target/mechanism mappings...")
        run([
            sys.executable,
            str(stage3_mapper),
            "--container", args.container,
        ])

    stage3_validator = REPO_ROOT / "components/evidence-registry/scripts/validate_stage3_ontology.py"
    if stage3_validator.exists():
        print("Validating Stage 3 application/target/mechanism ontology layer...")
        run([
            sys.executable,
            str(stage3_validator),
            "--container", args.container,
            "--release", args.release,
            "--expected-sources", str(expected_records),
            "--expected-components", "13",
        ])

    stage3_seed_validator = REPO_ROOT / "components/evidence-registry/scripts/validate_stage3_seed_mappings.py"
    if stage3_seed_validator.exists():
        print("Validating Stage 3 candidate seed mappings and human-approval boundary...")
        run([
            sys.executable,
            str(stage3_seed_validator),
            "--container", args.container,
        ])

    stage4_mapper = REPO_ROOT / "components/evidence-registry/scripts/apply_stage4_seed_mappings.py"
    if stage4_mapper.exists():
        print("Applying Stage 4 candidate outcome mappings...")
        run([
            sys.executable,
            str(stage4_mapper),
            "--container", args.container,
        ])

    stage4_validator = REPO_ROOT / "components/evidence-registry/scripts/validate_stage4_ontology.py"
    if stage4_validator.exists():
        print("Validating Stage 4 orthogonal outcome architecture...")
        run([
            sys.executable,
            str(stage4_validator),
            "--container", args.container,
        ])

    stage4_seed_validator = REPO_ROOT / "components/evidence-registry/scripts/validate_stage4_seed_mappings.py"
    if stage4_seed_validator.exists():
        print("Validating Stage 4 seed identity, controlled vocabularies and human-approval boundary...")
        run([
            sys.executable,
            str(stage4_seed_validator),
            "--container", args.container,
        ])

    stage5_mapper = REPO_ROOT / "components/evidence-registry/scripts/apply_stage5_seed_mappings.py"
    if stage5_mapper.exists():
        print("Applying Stage 5 candidate study arm/contrast mappings...")
        run([
            sys.executable,
            str(stage5_mapper),
            "--container", args.container,
        ])

    stage5_validator = REPO_ROOT / "components/evidence-registry/scripts/validate_stage5_ontology.py"
    if stage5_validator.exists():
        print("Validating Stage 5 study arm/component/contrast architecture...")
        run([
            sys.executable,
            str(stage5_validator),
            "--container", args.container,
        ])

    stage5_seed_validator = REPO_ROOT / "components/evidence-registry/scripts/validate_stage5_seed_mappings.py"
    if stage5_seed_validator.exists():
        print("Validating Stage 5 seed mappings and human-approval boundary...")
        run([
            sys.executable,
            str(stage5_seed_validator),
            "--container", args.container,
        ])

    stage6_mapper = REPO_ROOT / "components/evidence-registry/scripts/apply_stage6_seed_mappings.py"
    if stage6_mapper.exists():
        print("Applying Stage 6 candidate quantitative mappings...")
        run([
            sys.executable,
            str(stage6_mapper),
            "--container", args.container,
        ])

    stage6_validator = REPO_ROOT / "components/evidence-registry/scripts/validate_stage6_ontology.py"
    if stage6_validator.exists():
        print("Validating Stage 6 first-class effect architecture...")
        run([
            sys.executable,
            str(stage6_validator),
            "--container", args.container,
        ])

    stage6_seed_validator = REPO_ROOT / "components/evidence-registry/scripts/validate_stage6_seed_mappings.py"
    if stage6_seed_validator.exists():
        print("Validating Stage 6 seed mappings and human-approval boundary...")
        run([
            sys.executable,
            str(stage6_seed_validator),
            "--container", args.container,
        ])

    stage7_mapper = REPO_ROOT / "components/evidence-registry/scripts/apply_stage7_seed_status.py"
    if stage7_mapper.exists():
        print("Applying Stage 7 status-only quality/RoB seed backfill...")
        run([
            sys.executable,
            str(stage7_mapper),
            "--container", args.container,
        ])

    stage7_validator = REPO_ROOT / "components/evidence-registry/scripts/validate_stage7_quality_architecture.py"
    if stage7_validator.exists():
        print("Validating Stage 7 typed quality and result-RoB architecture...")
        run([
            sys.executable,
            str(stage7_validator),
            "--container", args.container,
        ])

    stage7_seed_validator = REPO_ROOT / "components/evidence-registry/scripts/validate_stage7_seed_status.py"
    if stage7_seed_validator.exists():
        print("Validating Stage 7 status-only seed boundary and GRADE deferral...")
        run([
            sys.executable,
            str(stage7_seed_validator),
        ])

    stage8_mapper = REPO_ROOT / "components/evidence-registry/scripts/apply_stage8_seed_status.py"
    if stage8_mapper.exists():
        print("Applying Stage 8 zero-body curation status...")
        run([
            sys.executable,
            str(stage8_mapper),
            "--container", args.container,
        ])

    stage8_validator = REPO_ROOT / "components/evidence-registry/scripts/validate_stage8_body_evidence.py"
    if stage8_validator.exists():
        print("Validating Stage 8 proposition/synthesis/body-evidence architecture...")
        run([
            sys.executable,
            str(stage8_validator),
            "--container", args.container,
        ])

    stage8_seed_validator = REPO_ROOT / "components/evidence-registry/scripts/validate_stage8_seed_status.py"
    if stage8_seed_validator.exists():
        print("Validating Stage 8 zero-body seed boundary...")
        run([
            sys.executable,
            str(stage8_seed_validator),
        ])

    print("LOCAL REGISTRY BASELINE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
