#!/usr/bin/env python3
"""Validate application of Stage 3 candidate seed mappings.

Expected counts are derived from the versioned mapping manifest. The validator
also enforces the human-approval boundary: agent candidates must remain proposed
and must not silently become approved scientific mappings.
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


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container,
        "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres",
        "-A", "-t", "-F", "|",
    ]
    return run(cmd, input_text=sql, capture=True).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Stage 3 candidate seed mappings.")
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    sources = manifest["sources"]

    expected_sources = len(sources)
    expected_application_links = sum(len(v.get("application_families", [])) for v in sources.values())
    expected_target_links = sum(
        len(component.get("targets", []))
        for source in sources.values()
        for component in source.get("components", [])
    )
    expected_target_components = sum(
        1
        for source in sources.values()
        for component in source.get("components", [])
        if component.get("targets")
    )
    expected_mechanisms = sum(len(v.get("mechanisms", [])) for v in sources.values())
    expected_mechanism_sources = sum(1 for v in sources.values() if v.get("mechanisms"))

    sql = """
select
  (select count(*) from public.source_version_application_family
    where mapping_source='agent_candidate' and review_status='proposed'),
  (select count(distinct source_version_id) from public.source_version_application_family
    where mapping_source='agent_candidate' and review_status='proposed'),
  (select count(*) from public.component_target
    where mapping_source='agent_candidate' and review_status='proposed'),
  (select count(distinct component_id) from public.component_target
    where mapping_source='agent_candidate' and review_status='proposed'),
  (select count(*) from public.mechanism_assertion
    where mapping_source='agent_candidate' and review_status='proposed'),
  (select count(distinct source_version_id) from public.mechanism_assertion
    where mapping_source='agent_candidate' and review_status='proposed'),
  (select count(*) from public.component_target_extraction_status
    where mapping_source='agent_candidate' and extraction_status='partially_extracted'),
  (select count(*) from public.source_version_mechanism_status
    where mapping_source='agent_candidate' and extraction_status='partially_extracted'),
  (
    (select count(*) from public.source_version_application_family
      where mapping_source='agent_candidate' and review_status='approved') +
    (select count(*) from public.component_target
      where mapping_source='agent_candidate' and review_status='approved') +
    (select count(*) from public.mechanism_assertion
      where mapping_source='agent_candidate' and review_status='approved')
  );
"""
    raw = psql(args.container, sql).split("|")
    if len(raw) != 9 or any(v == "" for v in raw):
        raise SystemExit(f"STAGE 3 SEED MAPPINGS INVALID: unexpected database output {raw!r}")

    (
        application_links,
        application_sources,
        target_links,
        target_components,
        mechanism_assertions,
        mechanism_sources,
        partial_target_statuses,
        partial_mechanism_statuses,
        agent_approved_rows,
    ) = map(int, raw)

    expected = {
        "application_links": expected_application_links,
        "application_sources": expected_sources,
        "target_links": expected_target_links,
        "target_components": expected_target_components,
        "mechanism_assertions": expected_mechanisms,
        "mechanism_sources": expected_mechanism_sources,
        "partial_target_statuses": expected_target_components,
        "partial_mechanism_statuses": expected_mechanism_sources,
        "agent_approved_rows": 0,
    }
    actual = {
        "application_links": application_links,
        "application_sources": application_sources,
        "target_links": target_links,
        "target_components": target_components,
        "mechanism_assertions": mechanism_assertions,
        "mechanism_sources": mechanism_sources,
        "partial_target_statuses": partial_target_statuses,
        "partial_mechanism_statuses": partial_mechanism_statuses,
        "agent_approved_rows": agent_approved_rows,
    }

    errors = [f"{key}: expected {expected[key]}, got {value}" for key, value in actual.items() if value != expected[key]]

    # Every manifest source must have at least one candidate application-family link.
    release_id = manifest["release_id"].replace("'", "''")
    missing_sources = psql(
        args.container,
        f"""
select count(*)
from public.release_source_version rsv
where rsv.release_id='{release_id}'
  and not exists (
    select 1 from public.source_version_application_family svaf
    where svaf.source_version_id=rsv.source_version_id
      and svaf.mapping_source='agent_candidate'
      and svaf.review_status='proposed'
  );
""",
    )
    if missing_sources != "0":
        errors.append(f"release source versions without candidate application mapping: {missing_sources}")

    if errors:
        print("STAGE 3 SEED MAPPINGS INVALID")
        for error in errors:
            print("-", error)
        return 1

    print(
        "STAGE 3 SEED MAPPINGS VALID: "
        f"sources={expected_sources}; application_links={expected_application_links}; "
        f"target_links={expected_target_links}; mechanism_assertions={expected_mechanisms}"
    )
    print(
        f"candidate_target_components={expected_target_components}; "
        f"candidate_mechanism_sources={expected_mechanism_sources}"
    )
    print("human_approval_boundary: PASS (0 agent candidates approved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
