#!/usr/bin/env python3
"""Apply Stage 5 candidate study-arm/component/contrast mappings locally.

All inserted scientific mappings remain agent_candidate/proposed. Existing
human-reviewed rows/statuses are never overwritten by this replay helper.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage5_seed_mappings.v1.json"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str, *, tuples_only: bool = False) -> str:
    cmd = ["docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres"]
    if tuples_only:
        cmd.extend(["-A", "-t", "-F", "|"])
    result = run(cmd, input_text=sql, capture=tuples_only)
    return result.stdout.strip() if tuples_only else ""


def lit(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def json_lit(value) -> str:
    payload = json.dumps(value or {}, ensure_ascii=False, separators=(",", ":"))
    return lit(payload) + "::jsonb"


def one(rows: str, label: str) -> str:
    values = [r.strip() for r in rows.splitlines() if r.strip()]
    if len(values) != 1:
        raise SystemExit(f"Expected exactly one {label}; got {values!r}")
    return values[0]


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Stage 5 candidate seed mappings to local Supabase.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("mapping_source") != "agent_candidate" or manifest.get("review_status") != "proposed":
        raise SystemExit("Stage 5 seed manifest must remain agent_candidate/proposed.")

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running.")

    print(f"Applying Stage 5 candidate mappings: {manifest['mapping_version']} ({manifest['release_id']})")

    study_count = arm_count = component_count = contrast_count = member_count = 0

    for source_id, spec in manifest["studies"].items():
        study_count += 1
        study_id = one(
            psql(args.container, f"select study_id from public.study where source_id={lit(source_id)} order by study_id;", tuples_only=True),
            f"study for {source_id}",
        )

        psql(args.container, f"""
update public.study_stage5_status
set arm_extraction_status={lit(spec['arm_extraction_status'])},
    arm_mapping_source='agent_candidate',
    arm_review_status='proposed',
    contrast_extraction_status={lit(spec['contrast_extraction_status'])},
    contrast_mapping_source='agent_candidate',
    contrast_review_status='proposed',
    notes={lit(spec.get('notes'))},
    updated_at=now()
where study_id={study_id}
  and arm_mapping_source in ('migration','agent_candidate')
  and contrast_mapping_source in ('migration','agent_candidate')
  and arm_review_status <> 'approved'
  and contrast_review_status <> 'approved';
""")

        arm_ids: dict[str, str] = {}
        for arm in spec.get("arms", []):
            psql(args.container, f"""
insert into public.study_arm (
  study_id, arm_key, arm_label, author_arm_label, arm_role,
  assignment_structure, arm_description, sample_json, mapping_source, review_status
) values (
  {study_id}, {lit(arm['arm_key'])}, {lit(arm['arm_label'])},
  {lit(arm.get('author_arm_label'))}, {lit(arm['arm_role'])},
  {lit(arm['assignment_structure'])}, {lit(arm.get('arm_description'))},
  {json_lit(arm.get('sample', {}))}, 'agent_candidate', 'proposed'
)
on conflict (study_id, arm_key) do nothing;
""")
            arm_id = one(
                psql(args.container, f"select arm_id from public.study_arm where study_id={study_id} and arm_key={lit(arm['arm_key'])};", tuples_only=True),
                f"arm {source_id}/{arm['arm_key']}",
            )
            arm_ids[arm["arm_key"]] = arm_id
            arm_count += 1

            for comp in arm.get("components", []):
                component_id = one(
                    psql(args.container, f"""
select ic.component_id
from public.intervention_component ic
where ic.study_id={study_id}
  and ic.component_name={lit(comp['component_name'])}
order by ic.component_id;
""", tuples_only=True),
                    f"component {source_id}/{comp['component_name']}",
                )
                psql(args.container, f"""
insert into public.arm_component (
  arm_id, component_id, membership_role, rationale, mapping_source, review_status
) values (
  {arm_id}, {component_id}, {lit(comp['membership_role'])},
  {lit(comp.get('rationale'))}, 'agent_candidate', 'proposed'
)
on conflict (arm_id, component_id) do nothing;
""")
                component_count += 1

        for contrast in spec.get("contrasts", []):
            psql(args.container, f"""
insert into public.study_contrast (
  study_id, contrast_key, contrast_label, contrast_type,
  estimand_summary, mapping_source, review_status
) values (
  {study_id}, {lit(contrast['contrast_key'])}, {lit(contrast['contrast_label'])},
  {lit(contrast['contrast_type'])}, {lit(contrast.get('estimand_summary'))},
  'agent_candidate', 'proposed'
)
on conflict (study_id, contrast_key) do nothing;
""")
            contrast_id = one(
                psql(args.container, f"select contrast_id from public.study_contrast where study_id={study_id} and contrast_key={lit(contrast['contrast_key'])};", tuples_only=True),
                f"contrast {source_id}/{contrast['contrast_key']}",
            )
            contrast_count += 1

            for member in contrast.get("members", []):
                arm_id = arm_ids.get(member["arm_key"])
                if not arm_id:
                    arm_id = one(
                        psql(args.container, f"select arm_id from public.study_arm where study_id={study_id} and arm_key={lit(member['arm_key'])};", tuples_only=True),
                        f"contrast arm {source_id}/{member['arm_key']}",
                    )
                psql(args.container, f"""
insert into public.contrast_arm_member (
  contrast_id, arm_id, contrast_side, contrast_coefficient,
  rationale, mapping_source, review_status
) values (
  {contrast_id}, {arm_id}, {lit(member['contrast_side'])},
  {lit(member.get('contrast_coefficient'))}, {lit(member.get('rationale'))},
  'agent_candidate', 'proposed'
)
on conflict (contrast_id, arm_id) do nothing;
""")
                member_count += 1

    print(
        f"STAGE 5 CANDIDATE MAPPINGS APPLIED: studies={study_count}; arms={arm_count}; "
        f"component_links={component_count}; contrasts={contrast_count}; contrast_members={member_count}"
    )
    print("All Stage 5 candidate mappings remain review_status=proposed / mapping_source=agent_candidate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
