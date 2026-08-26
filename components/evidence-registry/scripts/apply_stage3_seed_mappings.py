#!/usr/bin/env python3
"""Apply Stage 3 candidate application/target/mechanism mappings to local Registry.

The mapping manifest is deliberately external to the immutable 2026-08-23 release.
Candidate mappings are inserted as agent_candidate/proposed annotations and never
overwrite human-reviewed/approved mappings or extraction states.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage3_seed_mappings.v1.json"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str, *, tuples_only: bool = False) -> str:
    cmd = ["docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres"]
    if tuples_only:
        cmd.extend(["-A", "-t", "-F", "|"])
    result = run(cmd, input_text=sql, capture=tuples_only)
    return result.stdout.strip() if tuples_only else ""


def lit(value: str | None) -> str:
    if value is None:
        return "null"
    return "'" + value.replace("'", "''") + "'"


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply Stage 3 candidate seed mappings to local Supabase.")
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    release_id = manifest["release_id"]

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running.")

    print(f"Applying Stage 3 candidate mappings: {manifest['mapping_version']} ({release_id})")

    source_count = 0
    family_count = 0
    target_count = 0
    mechanism_count = 0

    for source_id, source in manifest["sources"].items():
        source_count += 1
        sv_id = f"sv-{source_id}-v1"

        exists = psql(
            args.container,
            f"""
select count(*)
from public.release_source_version
where release_id={lit(release_id)}
  and source_version_id={lit(sv_id)}
  and release_record_id={lit(source_id)};
""",
            tuples_only=True,
        )
        if exists != "1":
            raise SystemExit(f"Missing Stage 2 source-version membership for {source_id}: {sv_id}")

        for af in source.get("application_families", []):
            psql(
                args.container,
                f"""
insert into public.source_version_application_family (
  source_version_id, application_family, relevance_level, rationale,
  mapping_source, review_status
) values (
  {lit(sv_id)},
  {lit(af['application_family'])},
  {lit(af['relevance_level'])},
  {lit(af.get('rationale'))},
  'agent_candidate',
  'proposed'
)
on conflict (source_version_id, application_family) do nothing;
""",
            )
            family_count += 1

        for comp in source.get("components", []):
            component_name = comp["component_name"]
            component_id = psql(
                args.container,
                f"""
select ic.component_id
from public.intervention_component ic
join public.study s on s.study_id=ic.study_id
where s.source_id={lit(source_id)}
  and ic.component_name={lit(component_name)}
order by ic.component_id;
""",
                tuples_only=True,
            )
            rows = [r for r in component_id.splitlines() if r.strip()]
            if len(rows) != 1:
                raise SystemExit(
                    f"Expected exactly one component for {source_id}/{component_name!r}; got {rows!r}"
                )
            cid = rows[0].strip()

            for target in comp.get("targets", []):
                psql(
                    args.container,
                    f"""
insert into public.component_target (
  component_id, target_id, relationship, rationale, mapping_source, review_status
) values (
  {cid},
  {lit(target['target_id'])},
  {lit(target['relationship'])},
  {lit(target.get('rationale'))},
  'agent_candidate',
  'proposed'
)
on conflict (component_id, target_id, relationship) do nothing;
""",
                )
                target_count += 1

            psql(
                args.container,
                f"""
update public.component_target_extraction_status
set extraction_status='partially_extracted',
    notes=coalesce(notes, 'Stage 3 candidate mapping manifest applied; human review required.'),
    mapping_source='agent_candidate',
    updated_at=now()
where component_id={cid}
  and extraction_status='not_yet_extracted'
  and mapping_source='migration';
""",
            )

        if source.get("mechanisms"):
            study_id = psql(
                args.container,
                f"select study_id from public.study where source_id={lit(source_id)} order by study_id;",
                tuples_only=True,
            )
            study_rows = [r for r in study_id.splitlines() if r.strip()]
            if len(study_rows) != 1:
                raise SystemExit(f"Expected exactly one study for {source_id}; got {study_rows!r}")
            sid = study_rows[0].strip()

            for mech in source["mechanisms"]:
                duplicate = psql(
                    args.container,
                    f"""
select count(*)
from public.mechanism_assertion
where source_version_id={lit(sv_id)}
  and mechanism_id={lit(mech['mechanism_id'])}
  and assertion_type={lit(mech['assertion_type'])}
  and mapping_source='agent_candidate';
""",
                    tuples_only=True,
                )
                if duplicate == "0":
                    psql(
                        args.container,
                        f"""
insert into public.mechanism_assertion (
  source_version_id, mechanism_id, study_id, component_id,
  assertion_type, assertion_direction, support_summary,
  mapping_source, review_status
) values (
  {lit(sv_id)},
  {lit(mech['mechanism_id'])},
  {sid},
  null,
  {lit(mech['assertion_type'])},
  {lit(mech['assertion_direction'])},
  {lit(mech.get('support_summary'))},
  'agent_candidate',
  'proposed'
);
""",
                    )
                mechanism_count += 1

            psql(
                args.container,
                f"""
update public.source_version_mechanism_status
set extraction_status='partially_extracted',
    notes=coalesce(notes, 'Stage 3 candidate mechanism mapping applied; human review required.'),
    mapping_source='agent_candidate',
    updated_at=now()
where source_version_id={lit(sv_id)}
  and extraction_status='not_yet_extracted'
  and mapping_source='migration';
""",
            )

    print(
        f"STAGE 3 CANDIDATE MAPPINGS APPLIED: sources={source_count}; "
        f"application_links={family_count}; target_links={target_count}; "
        f"mechanism_assertions={mechanism_count}"
    )
    print("All inserted scientific mappings remain review_status=proposed / mapping_source=agent_candidate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
