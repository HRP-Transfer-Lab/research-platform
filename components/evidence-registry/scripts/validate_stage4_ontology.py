#!/usr/bin/env python3
"""Validate the Stage 4 orthogonal outcome architecture in local Supabase."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage4_seed_mappings.v1.json"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container, "psql",
        "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres",
        "-A", "-t", "-F", "|",
    ]
    return run(cmd, input_text=sql, capture=True).stdout.strip()


def scalar(container: str, sql: str) -> int:
    raw = psql(container, sql)
    try:
        return int(raw)
    except ValueError as exc:
        raise SystemExit(f"Expected integer query result, got {raw!r} for SQL: {sql}") from exc


def require_zero(label: str, value: int) -> None:
    if value != 0:
        raise SystemExit(f"STAGE 4 VALIDATION FAIL: {label}={value}, expected 0")


def require_equal(label: str, value: int, expected: int) -> None:
    if value != expected:
        raise SystemExit(f"STAGE 4 VALIDATION FAIL: {label}={value}, expected {expected}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Stage 4 outcome architecture in local Supabase.")
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--expected-outcomes", type=int, default=38)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    mappings = manifest["mappings"]

    running = run(
        ["docker", "inspect", "-f", "{{.State.Running}}", args.container],
        capture=True,
    ).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running.")

    expected_time_links = sum(len(m.get("time_classes", [])) for m in mappings)
    expected_transfer_links = sum(len(m.get("transfer_axes", [])) for m in mappings)
    expected_role_links = sum(len(m.get("outcome_roles", [])) for m in mappings)
    expected_bridge_links = sum(len(m.get("bridge_evidence", [])) for m in mappings)

    # Controlled vocabularies.
    require_equal("outcome_distance_definitions", scalar(args.container, "select count(*) from public.outcome_distance_definition;"), 4)
    require_equal("outcome_time_definitions", scalar(args.container, "select count(*) from public.outcome_time_definition;"), 3)
    require_equal("transfer_axis_definitions", scalar(args.container, "select count(*) from public.transfer_axis_definition;"), 3)
    require_equal("outcome_role_definitions", scalar(args.container, "select count(*) from public.outcome_role_definition;"), 6)
    require_equal("bridge_evidence_definitions", scalar(args.container, "select count(*) from public.bridge_evidence_definition;"), 5)
    require_equal("legacy_outcome_semantics", scalar(args.container, "select count(*) from public.legacy_outcome_semantic_map;"), 10)

    # Seed coverage and compatibility identity.
    outcomes = scalar(args.container, "select count(*) from public.evidence_outcome;")
    classifications = scalar(args.container, "select count(*) from public.outcome_stage4_classification;")
    require_equal("seed_outcomes", outcomes, args.expected_outcomes)
    require_equal("stage4_classifications", classifications, args.expected_outcomes)

    require_zero(
        "outcomes_without_stage4_status",
        scalar(
            args.container,
            """
select count(*)
from public.evidence_outcome eo
left join public.outcome_stage4_classification c on c.outcome_id=eo.outcome_id
where c.outcome_id is null;
""",
        ),
    )

    require_zero(
        "legacy_snapshot_mismatch",
        scalar(
            args.container,
            """
select count(*)
from public.evidence_outcome eo
join public.outcome_stage4_classification c on c.outcome_id=eo.outcome_id
where c.legacy_rung_snapshot is distinct from eo.evidence_rung
   or c.raw_timepoint_snapshot is distinct from eo.timepoint;
""",
        ),
    )

    require_zero(
        "unknown_legacy_rungs",
        scalar(
            args.container,
            """
select count(*)
from public.evidence_outcome eo
left join public.legacy_outcome_semantic_map m on m.legacy_rung=eo.evidence_rung
where eo.evidence_rung is not null
  and m.legacy_rung is null;
""",
        ),
    )

    # Candidate link parity with the manifest.
    require_equal(
        "candidate_time_links",
        scalar(args.container, "select count(*) from public.outcome_time_link where mapping_source='agent_candidate' and review_status='proposed';"),
        expected_time_links,
    )
    require_equal(
        "candidate_transfer_links",
        scalar(args.container, "select count(*) from public.outcome_transfer_axis where mapping_source='agent_candidate' and review_status='proposed';"),
        expected_transfer_links,
    )
    require_equal(
        "candidate_role_links",
        scalar(args.container, "select count(*) from public.outcome_role_link where mapping_source='agent_candidate' and review_status='proposed';"),
        expected_role_links,
    )
    require_equal(
        "candidate_bridge_links",
        scalar(args.container, "select count(*) from public.outcome_bridge_evidence where mapping_source='agent_candidate' and review_status='proposed';"),
        expected_bridge_links,
    )

    # A mapped dimension must have a live, non-rejected link. A non-mapped
    # dimension must not silently carry candidate links.
    for dimension, table in (
        ("time", "outcome_time_link"),
        ("transfer", "outcome_transfer_axis"),
        ("role", "outcome_role_link"),
        ("bridge", "outcome_bridge_evidence"),
    ):
        require_zero(
            f"{dimension}_mapped_without_link",
            scalar(
                args.container,
                f"""
select count(*)
from public.outcome_stage4_classification c
where c.{dimension}_status='reviewed_mapped'
  and not exists (
    select 1 from public.{table} l
    where l.outcome_id=c.outcome_id
      and l.review_status <> 'rejected'
  );
""",
            ),
        )
        require_zero(
            f"{dimension}_candidate_link_without_mapped_status",
            scalar(
                args.container,
                f"""
select count(*)
from public.{table} l
join public.outcome_stage4_classification c on c.outcome_id=l.outcome_id
where l.mapping_source='agent_candidate'
  and l.review_status='proposed'
  and c.{dimension}_status <> 'reviewed_mapped';
""",
            ),
        )

    require_zero(
        "distance_value_status_inconsistency",
        scalar(
            args.container,
            """
select count(*)
from public.outcome_stage4_classification
where (outcome_distance is null and distance_status='reviewed_mapped')
   or (outcome_distance is not null and distance_status<>'reviewed_mapped');
""",
        ),
    )

    # Agent candidates must remain candidates. Human review must change the
    # provenance before a value can become reviewed/approved/rejected.
    classification_boundary = scalar(
        args.container,
        """
select count(*)
from public.outcome_stage4_classification
where (distance_mapping_source='agent_candidate' and distance_review_status<>'proposed')
   or (time_mapping_source='agent_candidate' and time_review_status<>'proposed')
   or (transfer_mapping_source='agent_candidate' and transfer_review_status<>'proposed')
   or (role_mapping_source='agent_candidate' and role_review_status<>'proposed')
   or (bridge_mapping_source='agent_candidate' and bridge_review_status<>'proposed');
""",
    )
    link_boundary = scalar(
        args.container,
        """
select
  (select count(*) from public.outcome_time_link where mapping_source='agent_candidate' and review_status<>'proposed') +
  (select count(*) from public.outcome_transfer_axis where mapping_source='agent_candidate' and review_status<>'proposed') +
  (select count(*) from public.outcome_role_link where mapping_source='agent_candidate' and review_status<>'proposed') +
  (select count(*) from public.outcome_bridge_evidence where mapping_source='agent_candidate' and review_status<>'proposed');
""",
    )
    require_zero("candidate_classification_review_boundary_failures", classification_boundary)
    require_zero("candidate_link_review_boundary_failures", link_boundary)

    print(
        "STAGE 4 OUTCOME ARCHITECTURE VALID: "
        "4 distances / 3 time classes / 3 transfer axes / 6 roles / 5 Bridge evidence levels"
    )
    print(
        f"seed_outcomes={outcomes}; classifications={classifications}; "
        f"time_links={expected_time_links}; transfer_links={expected_transfer_links}; "
        f"role_links={expected_role_links}; bridge_links={expected_bridge_links}"
    )
    print("legacy_semantic_coverage: PASS (10 legacy rung values; 0 unknown)")
    print("orthogonal_dimension_integrity: PASS")
    print("human_approval_boundary: PASS (0 agent candidates promoted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
