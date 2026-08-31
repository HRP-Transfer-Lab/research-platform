#!/usr/bin/env python3
"""Prepare governed Stage 12 human-review packets from unresolved seed candidates.

This is a compatibility bridge for the Stage 3-10 deterministic seed mappings that
predate Stage 11 first-class candidate provenance.

Safety rules:
- creates provenance run/candidate rows only; never approves normalized scientific rows;
- preserves original agent_candidate/proposed state;
- records that detailed historical model/prompt metadata is unavailable;
- packet hashes bind exact candidate values + current scientific revision;
- reruns reuse/supersede existing bridge candidates rather than deleting history.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "components/evidence-registry/review-packets/stage12-seed"
SCHEMA_VERSION = "stage12-review-packet-v1"
HISTORICAL_RELEASE = "2026-08-23"

# Exact unresolved decomposition from the Stage 12 readiness audit.
BATCH_SPECS: dict[str, dict[str, Any]] = {
    "stage3_ontology": {
        "label": "Stage 3 ontology — application family, target and mechanism",
        "expected": 53,
        "group": "source",
        "tables": {
            "source_version_application_family": None,
            "component_target": None,
            "mechanism_assertion": None,
        },
    },
    "stage5_design": {
        "label": "Stage 5 study design — arms, components and contrasts",
        "expected": 71,
        "group": "study",
        "tables": {
            "study_arm": None,
            "arm_component": None,
            "study_contrast": None,
            "contrast_arm_member": None,
        },
    },
    "stage4_outcomes": {
        "label": "Stage 4 outcome semantics — distance, time, transfer, role and Bridge",
        "expected": 260,
        "group": "outcome",
        "tables": {
            "outcome_stage4_classification": ["distance", "time", "transfer", "role", "bridge"],
            "outcome_role_link": None,
            "outcome_time_link": None,
            "outcome_transfer_axis": None,
        },
    },
    "stage6_quantitative": {
        "label": "Stage 6 quantitative extraction and effect estimates",
        "expected": 39,
        "group": "outcome",
        "tables": {
            "outcome_stage6_status": None,
            "effect_estimate": None,
        },
    },
    "stage9_context": {
        "label": "Stage 9 population, study context and delivery context",
        "expected": 121,
        "group": "source",
        "tables": {
            "study_population_context_status": None,
            "study_population_context_term": None,
            "component_delivery_context_status": None,
            "component_delivery_context_term": None,
        },
    },
    "stage10_harms_implementation": {
        "label": "Stage 10 harms, implementation, participation and support dependence",
        "expected": 23,
        "group": "source",
        "tables": {
            "boundary_condition_observation": None,
            "component_implementation_observation": None,
            "component_implementation_status": None,
            "harm_observation": None,
            "study_harms_status": None,
            "study_participation_observation": None,
            "support_dependence_observation": None,
        },
    },
}

EVIDENCE_TEXT_KEYS = (
    "evidence_basis", "rationale", "notes", "result_summary", "boundary_summary",
    "support_summary", "author_reported_text", "inclusion_reason", "source_field",
)


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=check, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|",
    ]
    result = run(cmd, input_text=sql, capture=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "<no PostgreSQL stderr>"
        stdout = result.stdout.strip()
        extra = f"\nstdout:\n{stdout}" if stdout else ""
        raise RuntimeError(f"psql failed with exit status {result.returncode}:\n{stderr}{extra}")
    return result.stdout.strip()


def sql_text(value: str | None) -> str:
    if value is None:
        return "null"
    return "'" + value.replace("'", "''") + "'"


def dollar_json(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if "$s12$" in text:
        raise ValueError("unexpected Stage 12 dollar-quote marker in JSON")
    return "$s12$" + text + "$s12$::jsonb"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def table_pk_columns(container: str, table: str) -> list[str]:
    raw = psql(container, f"""
select a.attname
from pg_index i
join pg_class c on c.oid=i.indrelid
join pg_namespace n on n.oid=c.relnamespace
join unnest(i.indkey) with ordinality k(attnum,ord) on true
join pg_attribute a on a.attrelid=c.oid and a.attnum=k.attnum
where n.nspname='public' and c.relname={sql_text(table)} and i.indisprimary
order by k.ord;
""")
    cols = [x for x in raw.splitlines() if x]
    if not cols:
        raise RuntimeError(f"No primary key found for public.{table}")
    return cols


def unresolved_rows(container: str, table: str, dimension: str | None) -> list[dict[str, Any]]:
    if dimension is None:
        sql = f"select to_jsonb(t)::text from public.\"{table}\" t where mapping_source='agent_candidate' and review_status='proposed' order by to_jsonb(t)::text;"
    else:
        sql = f"select to_jsonb(t)::text from public.\"{table}\" t where {dimension}_mapping_source='agent_candidate' and {dimension}_review_status='proposed' order by to_jsonb(t)::text;"
    raw = psql(container, sql)
    return [json.loads(line) for line in raw.splitlines() if line]


def scientific_value(row: dict[str, Any], dimension: str | None) -> dict[str, Any]:
    if dimension is not None:
        prefix = dimension + "_"
        keep = {
            k: v for k, v in row.items()
            if k.startswith(prefix)
            and k not in {f"{dimension}_mapping_source", f"{dimension}_review_status"}
        }
        keep["outcome_id"] = row.get("outcome_id")
        return keep
    excluded = {"mapping_source", "review_status", "created_at", "updated_at"}
    return {k: v for k, v in row.items() if k not in excluded}


def evidence_basis(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in EVIDENCE_TEXT_KEYS:
        value = row.get(key)
        if value is not None and str(value).strip():
            parts.append(f"{key}: {value}")
    return " | ".join(parts) if parts else "No separate evidence-basis text field; review the complete proposed row snapshot and linked source context."


def resolve_source_context(container: str, row: dict[str, Any]) -> dict[str, Any]:
    source_id = row.get("source_id")
    study_id = row.get("study_id")
    component_id = row.get("component_id")
    outcome_id = row.get("outcome_id")
    arm_id = row.get("arm_id")
    contrast_id = row.get("contrast_id")
    source_version_id = row.get("source_version_id")

    if not source_id and source_version_id:
        source_id = psql(container, f"""
select identity_value from public.canonical_source_identity csi
join public.source_version sv on sv.canonical_source_id=csi.canonical_source_id
where sv.source_version_id={sql_text(str(source_version_id))} and csi.identity_scheme='legacy_source_id'
order by identity_value limit 1;
""") or None

    if not study_id and component_id is not None:
        x = psql(container, f"select study_id from public.intervention_component where component_id={int(component_id)};")
        study_id = int(x) if x else None
    if not study_id and outcome_id is not None:
        x = psql(container, f"select study_id from public.evidence_outcome where outcome_id={int(outcome_id)};")
        study_id = int(x) if x else None
    if not study_id and arm_id is not None:
        x = psql(container, f"select study_id from public.study_arm where arm_id={int(arm_id)};")
        study_id = int(x) if x else None
    if not study_id and contrast_id is not None:
        x = psql(container, f"select study_id from public.study_contrast where contrast_id={int(contrast_id)};")
        study_id = int(x) if x else None
    if not source_id and study_id is not None:
        source_id = psql(container, f"select source_id from public.study where study_id={int(study_id)};") or None

    title = None
    if source_id:
        title = psql(container, f"select title from public.evidence_source where source_id={sql_text(str(source_id))};") or None

    component_name = None
    if component_id is not None:
        component_name = psql(container, f"select component_name from public.intervention_component where component_id={int(component_id)};") or None
    outcome_name = None
    if outcome_id is not None:
        outcome_name = psql(container, f"select outcome_name from public.evidence_outcome where outcome_id={int(outcome_id)};") or None

    return {
        "source_id": source_id,
        "source_title": title,
        "study_id": study_id,
        "component_id": component_id,
        "component_name": component_name,
        "outcome_id": outcome_id,
        "outcome_name": outcome_name,
    }


def group_key(group: str, context: dict[str, Any], decision: dict[str, Any]) -> str:
    if group == "outcome" and context.get("outcome_id") is not None:
        return f"outcome:{context['outcome_id']}"
    if group == "study" and context.get("study_id") is not None:
        return f"study:{context['study_id']}"
    if context.get("source_id"):
        return f"source:{context['source_id']}"
    return f"decision:{decision['table_name']}:{sha256_json(decision['primary_key'])[:12]}"


def group_label(context: dict[str, Any], key: str) -> str:
    bits = []
    if context.get("source_id"):
        bits.append(str(context["source_id"]))
    if context.get("outcome_name"):
        bits.append(str(context["outcome_name"]))
    elif context.get("component_name"):
        bits.append(str(context["component_name"]))
    elif context.get("source_title"):
        bits.append(str(context["source_title"]))
    return " — ".join(bits) if bits else key


def ensure_bridge_run(container: str, git_sha: str) -> int:
    existing = psql(container, f"""
select processing_run_id
from public.scientific_processing_run
where tool_name='stage12-legacy-candidate-bridge'
  and extraction_schema_version={sql_text(SCHEMA_VERSION)}
  and run_status='completed'
order by processing_run_id limit 1;
""")
    if existing:
        return int(existing)
    created = psql(container, f"""
insert into public.scientific_processing_run(
  run_kind,actor_kind,run_status,completed_at,provider,tool_name,tool_version,
  extraction_schema_version,taxonomy_version,code_commit_sha,parameters_json,notes
) values (
  'manual_import','system','completed',now(),'HRP Transfer Lab','stage12-legacy-candidate-bridge','1',
  {sql_text(SCHEMA_VERSION)},'iqm-route-v0.2',{sql_text(git_sha)},
  '{{"historical_release":"2026-08-23","purpose":"bridge_pre_stage11_candidates"}}'::jsonb,
  'Compatibility provenance for Stage 3-10 deterministic agent_candidate rows created before Stage 11. Original detailed model/prompt metadata is not available and is not fabricated.'
) returning processing_run_id;
""")
    return int(created)


def ensure_candidate(
    container: str,
    run_id: int,
    table: str,
    pk: dict[str, Any],
    dimension: str | None,
    value: dict[str, Any],
    basis: str,
) -> int:
    subject_key = {"stage12_legacy": True, "table": table, "primary_key": pk}
    if dimension:
        subject_key["dimension"] = dimension
    field_path = f"legacy_seed_review.{table}" + (f".{dimension}" if dimension else "")

    existing_raw = psql(container, f"""
select field_candidate_id,candidate_value_json::text
from public.scientific_field_candidate
where subject_kind='other_scientific_object'
  and subject_key={dollar_json(subject_key)}
  and field_path={sql_text(field_path)}
order by field_candidate_id desc limit 1;
""")
    supersedes = None
    if existing_raw:
        cid_s, value_s = existing_raw.split("|", 1)
        if json.loads(value_s) == value:
            return int(cid_s)
        supersedes = int(cid_s)

    inserted = psql(container, f"""
insert into public.scientific_field_candidate(
  processing_run_id,subject_kind,subject_key,field_path,candidate_value_json,source_basis,confidence,candidate_status,supersedes_candidate_id
) values (
  {run_id},'other_scientific_object',{dollar_json(subject_key)},{sql_text(field_path)},
  {dollar_json(value)},{sql_text(basis)},null,'proposed',{str(supersedes) if supersedes is not None else 'null'}
) returning field_candidate_id;
""")
    return int(inserted)


def build_packets(container: str, output_dir: Path) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    git_sha = run(["git", "rev-parse", "HEAD"], capture=True).stdout.strip()
    revision = int(psql(container, "select current_revision from public.scientific_state_revision where singleton=true;"))
    run_id = ensure_bridge_run(container, git_sha)
    summaries: list[dict[str, Any]] = []

    for batch_id, spec in BATCH_SPECS.items():
        decisions: list[dict[str, Any]] = []
        pk_cache: dict[str, list[str]] = {}
        for table, dims in spec["tables"].items():
            pk_cols = pk_cache.setdefault(table, table_pk_columns(container, table))
            dimensions = dims if dims is not None else [None]
            for dimension in dimensions:
                for row in unresolved_rows(container, table, dimension):
                    pk = {col: row.get(col) for col in pk_cols}
                    if any(value is None for value in pk.values()):
                        raise RuntimeError(f"Missing primary-key value for {table}: {pk}")
                    value = scientific_value(row, dimension)
                    basis = evidence_basis(row)
                    candidate_id = ensure_candidate(container, run_id, table, pk, dimension, value, basis)
                    context = resolve_source_context(container, row)
                    decision = {
                        "candidate_id": candidate_id,
                        "table_name": table,
                        "primary_key": pk,
                        "dimension": dimension,
                        "field_path": f"legacy_seed_review.{table}" + (f".{dimension}" if dimension else ""),
                        "candidate_value": value,
                        "evidence_basis": basis,
                        "context": context,
                        "row_snapshot_sha256": sha256_json(row),
                        "proposed_action": "approve",
                    }
                    decisions.append(decision)

        decisions.sort(key=lambda d: (d["context"].get("source_id") or "", d["context"].get("outcome_id") or -1, d["table_name"], json.dumps(d["primary_key"], sort_keys=True), d.get("dimension") or ""))
        if len(decisions) != spec["expected"]:
            raise RuntimeError(f"{batch_id}: expected {spec['expected']} unresolved decisions, found {len(decisions)}")

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        contexts: dict[str, dict[str, Any]] = {}
        for d in decisions:
            key = group_key(spec["group"], d["context"], d)
            grouped[key].append(d)
            contexts.setdefault(key, d["context"])

        units = []
        for key in sorted(grouped):
            units.append({
                "unit_key": key,
                "label": group_label(contexts[key], key),
                "context": contexts[key],
                "decisions": grouped[key],
            })

        payload = {
            "schema_version": SCHEMA_VERSION,
            "batch_id": batch_id,
            "batch_label": spec["label"],
            "historical_release_id": HISTORICAL_RELEASE,
            "scientific_state_revision": revision,
            "bridge_processing_run_id": run_id,
            "generated_from_git_commit": git_sha,
            "decision_count": len(decisions),
            "review_unit_count": len(units),
            "units": units,
            "governance_notes": [
                "Packet preparation does not approve scientific state.",
                "Detailed historical model/prompt metadata for pre-Stage-11 candidates is unavailable and has not been fabricated.",
                "Approval must verify this packet hash and the unchanged scientific_state_revision.",
                "Every accepted legacy candidate should establish Stage 11 human adjudication/authority before normalized review_status becomes approved.",
            ],
        }
        packet_hash = sha256_json(payload)
        packet = dict(payload)
        packet["packet_sha256"] = packet_hash

        json_path = output_dir / f"{batch_id}.json"
        md_path = output_dir / f"{batch_id}.md"
        json_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

        lines = [
            f"# Stage 12 review packet — {spec['label']}",
            "",
            f"- Packet: `{batch_id}`",
            f"- SHA-256: `{packet_hash}`",
            f"- Scientific revision: `{revision}`",
            f"- Decisions: **{len(decisions)}**",
            f"- Review units: **{len(units)}**",
            "",
            "> No item in this packet is approved by packet generation. Human review is required.",
            "",
        ]
        for unit in units:
            lines.extend([f"## {unit['label']}", ""])
            for d in unit["decisions"]:
                identity = json.dumps(d["primary_key"], ensure_ascii=False, sort_keys=True)
                suffix = f" / {d['dimension']}" if d["dimension"] else ""
                value_text = json.dumps(d["candidate_value"], ensure_ascii=False, sort_keys=True)
                lines.extend([
                    f"### `{d['table_name']}`{suffix}",
                    "",
                    f"- Key: `{identity}`",
                    f"- Stage 11 candidate: `{d['candidate_id']}`",
                    f"- Proposed value: `{value_text}`",
                    f"- Evidence basis: {d['evidence_basis']}",
                    f"- Row snapshot: `{d['row_snapshot_sha256']}`",
                    "",
                ])
        md_path.write_text("\n".join(lines), encoding="utf-8")

        summaries.append({
            "batch_id": batch_id,
            "packet_sha256": packet_hash,
            "decisions": len(decisions),
            "review_units": len(units),
            "json": str(json_path.relative_to(REPO_ROOT)),
            "markdown": str(md_path.relative_to(REPO_ROOT)),
        })

    index_payload = {
        "schema_version": SCHEMA_VERSION,
        "historical_release_id": HISTORICAL_RELEASE,
        "scientific_state_revision": revision,
        "bridge_processing_run_id": run_id,
        "generated_from_git_commit": git_sha,
        "total_decisions": sum(x["decisions"] for x in summaries),
        "batches": summaries,
    }
    index_payload["index_sha256"] = sha256_json(index_payload)
    (output_dir / "index.json").write_text(json.dumps(index_payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    print("STAGE 12 REVIEW PACKETS PREPARED")
    print(f"scientific_state_revision|{revision}")
    print(f"bridge_processing_run_id|{run_id}")
    print(f"total_decisions|{index_payload['total_decisions']}")
    print("batch_id|review_units|decisions|packet_sha256")
    for x in summaries:
        print(f"{x['batch_id']}|{x['review_units']}|{x['decisions']}|{x['packet_sha256']}")
    print(f"index_sha256|{index_payload['index_sha256']}")
    print(f"output_dir|{output_dir}")
    print("NORMALIZED SCIENTIFIC ROWS CHANGED|0")
    return summaries


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare deterministic Stage 12 review packets without approving scientific state.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    build_packets(args.container, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
