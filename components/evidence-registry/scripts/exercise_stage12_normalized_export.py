#!/usr/bin/env python3
"""Exercise the Stage 12 normalized release exporter without publishing anything.

The exercise proves:
- a prepared Stage 11 build pins the 18 source versions;
- the Stage 12 exporter blocks unresolved agent candidates by default;
- diagnostic export captures the normalized scientific layers;
- two exports of unchanged state are byte-identical;
- the temporary release build and files are cleaned up.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid

DEFAULT_CONTAINER = "supabase_db_research-platform"
REPO_ROOT = Path(__file__).resolve().parents[3]
EXPORTER = REPO_ROOT / "components/evidence-registry/scripts/export_stage12_release_bundle.py"
TEST_REVIEWER = "11111111-1111-1111-1111-111111111111"
REQUIRED_LAYERS = {
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
}


def run(cmd: list[str], *, input_text: str | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=check, capture_output=True)


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|",
    ]
    result = run(cmd, input_text=sql, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"psql failed:\n{result.stderr.strip()}\n{result.stdout.strip()}")
    return result.stdout.strip()


def q(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def create_prepared_build(container: str, build_id: str, target_release: str) -> None:
    psql(container, f"""
select private.stage11_create_release_build_core(
  {q(build_id)},{q(target_release)},'registry-v1.1','iqm-route-v0.2','csi-evidence-v1',
  'docs/STAGE_12_BACKFILL_PARITY_RELEASE_IMPLEMENTATION.md','Stage 12 normalized export exercise',
  '{TEST_REVIEWER}'::uuid,'Temporary local Stage 12 export exercise; never published.'
);
select private.stage11_prepare_release_build_core({q(build_id)});
""")


def cleanup_build(container: str, build_id: str) -> None:
    psql(container, f"""
select set_config('hrp.stage11_controlled_write','on',false);
update public.evidence_release_build
set build_status='cancelled',updated_at=now()
where release_build_id={q(build_id)} and build_status in ('draft','prepared','validated');
delete from public.evidence_release_build where release_build_id={q(build_id)};
""")


def export(build_id: str, container: str, output_root: Path, *, allow_unreviewed: bool) -> subprocess.CompletedProcess[str]:
    cmd = [
        "python3", str(EXPORTER), build_id,
        "--container", container,
        "--output-root", str(output_root),
    ]
    if allow_unreviewed:
        cmd.append("--allow-unreviewed")
    return run(cmd, check=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container]).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    token = uuid.uuid4().hex[:12]
    build_id = f"stage12-export-{token}"
    target_release = f"stage12-export-release-{token}"
    temp_root = Path(tempfile.mkdtemp(prefix="stage12-export-exercise-"))
    first_root = temp_root / "first"
    second_root = temp_root / "second"

    try:
        create_prepared_build(args.container, build_id, target_release)

        member_count = int(psql(args.container, f"select count(*) from public.release_build_source_version where release_build_id={q(build_id)};") or "0")
        if member_count != 18:
            raise RuntimeError(f"expected 18 pinned source versions, got {member_count}")

        blocked = export(build_id, args.container, first_root, allow_unreviewed=False)
        if blocked.returncode == 0:
            raise RuntimeError("publication-mode normalized exporter unexpectedly accepted unresolved agent candidates")
        combined = (blocked.stdout + "\n" + blocked.stderr).lower()
        if "release export blocked" not in combined or "agent_candidate/proposed" not in combined:
            raise RuntimeError(f"exporter failed for an unexpected reason:\n{blocked.stdout}\n{blocked.stderr}")

        first = export(build_id, args.container, first_root, allow_unreviewed=True)
        if first.returncode != 0:
            raise RuntimeError(f"first diagnostic export failed:\n{first.stdout}\n{first.stderr}")
        second = export(build_id, args.container, second_root, allow_unreviewed=True)
        if second.returncode != 0:
            raise RuntimeError(f"second diagnostic export failed:\n{second.stdout}\n{second.stderr}")

        state1 = (first_root / build_id / "scientific_state.json").read_bytes()
        state2 = (second_root / build_id / "scientific_state.json").read_bytes()
        manifest1_bytes = (first_root / build_id / "manifest.json").read_bytes()
        manifest2_bytes = (second_root / build_id / "manifest.json").read_bytes()
        if state1 != state2 or manifest1_bytes != manifest2_bytes:
            raise RuntimeError("unchanged normalized state did not export byte-identically twice")

        state = json.loads(state1)
        manifest = json.loads(manifest1_bytes)
        layer_names = set(state.get("layers", {}))
        missing = sorted(REQUIRED_LAYERS - layer_names)
        if missing:
            raise RuntimeError(f"normalized export missing required layers: {missing}")
        if manifest.get("source_version_count") != 18:
            raise RuntimeError(f"manifest expected 18 source versions; got {manifest.get('source_version_count')!r}")
        unresolved = int(manifest.get("unresolved_agent_candidate_decisions", -1))
        if unresolved <= 0:
            raise RuntimeError("diagnostic export should expose unresolved candidate decisions before review closure")
        if not manifest.get("diagnostic_allow_unreviewed"):
            raise RuntimeError("diagnostic manifest did not record allow-unreviewed mode")

        print("STAGE 12 NORMALIZED EXPORT EXERCISE PASS")
        print(f"source_versions|{member_count}")
        print(f"required_normalized_layers|{len(REQUIRED_LAYERS)}/{len(REQUIRED_LAYERS)}")
        print(f"unresolved_agent_candidate_decisions|{unresolved}")
        print(f"scientific_state_sha256|{manifest['scientific_state_sha256']}")
        print(f"export_manifest_sha256|{manifest['export_manifest_sha256']}")
        print("publication_mode_unreviewed_gate|PASS")
        print("diagnostic_repeat_export|BYTE_IDENTICAL")
    finally:
        try:
            cleanup_build(args.container, build_id)
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)

    if psql(args.container, f"select count(*) from public.evidence_release_build where release_build_id={q(build_id)};") != "0":
        raise RuntimeError("temporary Stage 12 release build persisted unexpectedly")
    if psql(args.container, f"select count(*) from public.evidence_release where release_id={q(target_release)};") != "0":
        raise RuntimeError("Stage 12 export exercise published a release unexpectedly")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
