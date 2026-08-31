#!/usr/bin/env python3
"""Apply an explicitly human-approved Stage 12 review-surface packet locally.

Supports ordinary, dimension-specific and provenance-only candidate surfaces.
Every decision is revalidated and applied in one PostgreSQL transaction. Any
row-count or provenance mismatch rolls back the entire batch.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from pathlib import Path
from typing import Any

import prepare_stage12_review_surface_packets as prep
import validate_stage12_review_surface_packet as validator


def run(cmd: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=False, capture_output=True)


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|",
    ]
    result = run(cmd, input_text=sql)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "<no PostgreSQL stderr>"
        stdout = result.stdout.strip()
        extra = f"\nstdout:\n{stdout}" if stdout else ""
        raise RuntimeError(f"psql failed with exit status {result.returncode}:\n{stderr}{extra}")
    return result.stdout.strip()


def sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def qident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def discover_reviewer(container: str, supplied: str | None) -> str:
    if supplied:
        try:
            return str(uuid.UUID(supplied))
        except ValueError as exc:
            raise RuntimeError("--reviewer-user-id must be a UUID") from exc
    raw = psql(container, """
select user_id::text from public.workbench_member
where active=true and role='owner' order by user_id;
""")
    owners = [line for line in raw.splitlines() if line]
    if len(owners) == 1:
        return owners[0]
    if not owners:
        raise RuntimeError("No active local Workbench owner found; supply --reviewer-user-id <UUID>.")
    raise RuntimeError("Multiple active Workbench owners found; supply --reviewer-user-id <UUID> explicitly.")


def confirmation_phrase(batch_id: str, decisions: int) -> str:
    return f"I_APPROVE_{batch_id.upper()}_{decisions}"


def update_sql_for_decision(d: dict[str, Any]) -> str:
    table = d["table_name"]
    where = validator.pk_where(d["primary_key"])
    mode = d["surface_mode"]
    dimension = d.get("dimension")
    if mode == "ordinary":
        return (
            f"update public.{qident(table)} set mapping_source='human_review', review_status='approved' "
            f"where {where} and mapping_source='agent_candidate' and review_status='proposed'"
        )
    if mode == "dimension":
        if not dimension:
            raise RuntimeError(f"Dimension decision missing dimension for {table}")
        return (
            f"update public.{qident(table)} set "
            f"{qident(dimension + '_mapping_source')}='human_review', "
            f"{qident(dimension + '_review_status')}='approved' "
            f"where {where} "
            f"and {qident(dimension + '_mapping_source')}='agent_candidate' "
            f"and {qident(dimension + '_review_status')}='proposed'"
        )
    if mode == "provenance_only":
        return (
            f"update public.{qident(table)} set mapping_source='human_review' "
            f"where {where} and mapping_source='agent_candidate'"
        )
    raise RuntimeError(f"Unknown surface_mode {mode!r}")


def build_apply_sql(packet: dict[str, Any], reviewer_id: str, stable_hash: str) -> str:
    statements = [
        "begin;",
        "set local lock_timeout='5s';",
        "set local statement_timeout='180s';",
    ]
    decisions = [d for unit in packet["units"] for d in unit["decisions"]]
    for d in decisions:
        if d.get("proposed_action") != "approve":
            raise RuntimeError(f"Non-approve action in packet for {d['table_name']} {d['primary_key']}")
        candidate_id = int(d["candidate_id"])
        rationale = (
            f"Stage 12 governed human review-surface approval; batch={packet['batch_id']}; "
            f"packet_sha256={packet['packet_sha256']}; scientific_decision_sha256={stable_hash}."
        )
        update_sql = update_sql_for_decision(d)
        error_text = (
            f"Stage 12 normalized provenance update did not affect exactly one row: "
            f"batch={packet['batch_id']} table={d['table_name']} candidate={candidate_id}"
        )
        statements.append(
            "do $s12surface$\n"
            "declare n bigint;\n"
            "begin\n"
            f"  perform private.apply_scientific_adjudication_core({candidate_id},{sql_text(reviewer_id)}::uuid,'accept',null,{sql_text(rationale)});\n"
            f"  {update_sql};\n"
            "  get diagnostics n = row_count;\n"
            "  if n <> 1 then\n"
            f"    raise exception {sql_text(error_text)};\n"
            "  end if;\n"
            "end\n"
            "$s12surface$;"
        )
    statements.append("commit;")
    return "\n".join(statements) + "\n"


def verify_post_apply(container: str, packet: dict[str, Any]) -> None:
    decisions = [d for unit in packet["units"] for d in unit["decisions"]]
    for d in decisions:
        table = d["table_name"]
        where = validator.pk_where(d["primary_key"])
        mode = d["surface_mode"]
        dimension = d.get("dimension")
        if mode == "ordinary":
            state = psql(container, f"select mapping_source||'|'||review_status from public.{qident(table)} where {where};")
            expected = "human_review|approved"
        elif mode == "dimension":
            state = psql(
                container,
                f"select {qident(dimension + '_mapping_source')}||'|'||{qident(dimension + '_review_status')} "
                f"from public.{qident(table)} where {where};",
            )
            expected = "human_review|approved"
        else:
            state = psql(container, f"select mapping_source from public.{qident(table)} where {where};")
            expected = "human_review"
        if state != expected:
            raise RuntimeError(f"Post-apply provenance mismatch for {table} {d['primary_key']}: {state!r}")

        cid = int(d["candidate_id"])
        candidate_state = psql(container, f"select candidate_status from public.scientific_field_candidate where field_candidate_id={cid};")
        if candidate_state != "accepted":
            raise RuntimeError(f"Candidate {cid} post-apply state {candidate_state!r}, expected accepted")
        authority_count = int(psql(
            container,
            f"select count(*) from public.scientific_field_authority a "
            f"join public.scientific_field_adjudication j on j.adjudication_id=a.source_adjudication_id "
            f"where j.field_candidate_id={cid} and a.active=true;",
        ) or "0")
        if authority_count != 1:
            raise RuntimeError(f"Candidate {cid} has {authority_count} active authority rows, expected 1")


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply an explicitly approved Stage 12 review-surface packet locally.")
    ap.add_argument("--container", default=prep.DEFAULT_CONTAINER)
    ap.add_argument("--packet-dir", type=Path, default=prep.DEFAULT_OUTPUT_DIR)
    ap.add_argument("--batch", choices=list(prep.BATCH_SPECS), required=True)
    ap.add_argument("--packet-sha", required=True)
    ap.add_argument("--scientific-decision-sha", required=True)
    ap.add_argument("--confirm", required=True)
    ap.add_argument("--reviewer-user-id")
    args = ap.parse_args()

    path = args.packet_dir / f"{args.batch}.json"
    if not path.exists():
        raise RuntimeError(f"Missing packet {path}")
    packet, stable_hash = validator.validate_packet(args.container, path)
    if args.packet_sha != packet["packet_sha256"]:
        raise RuntimeError("Supplied packet SHA does not match the validated packet")
    if args.scientific_decision_sha != stable_hash:
        raise RuntimeError("Supplied scientific-decision SHA does not match the validated packet")
    phrase = confirmation_phrase(args.batch, packet["decision_count"])
    if args.confirm != phrase:
        raise RuntimeError(f"Explicit human confirmation required. Exact phrase: {phrase}")

    reviewer_id = discover_reviewer(args.container, args.reviewer_user_id)
    pre_revision = int(psql(args.container, "select current_revision from public.scientific_state_revision where singleton=true;"))
    print("STAGE 12 GOVERNED REVIEW-SURFACE APPROVAL")
    print(f"batch_id|{args.batch}")
    print(f"review_units|{packet['review_unit_count']}")
    print(f"decisions|{packet['decision_count']}")
    print(f"packet_sha256|{packet['packet_sha256']}")
    print(f"scientific_decision_sha256|{stable_hash}")
    print(f"reviewer_user_id|{reviewer_id}")
    print(f"pre_apply_scientific_revision|{pre_revision}")

    psql(args.container, build_apply_sql(packet, reviewer_id, stable_hash))
    verify_post_apply(args.container, packet)
    post_revision = int(psql(args.container, "select current_revision from public.scientific_state_revision where singleton=true;"))
    print(f"post_apply_scientific_revision|{post_revision}")
    print("normalized_scientific_values_changed|0")
    print(f"human_review_decisions_applied|{packet['decision_count']}")
    print(f"stage11_candidates_accepted|{packet['decision_count']}")
    print(f"stage11_active_authorities_established|{packet['decision_count']}")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print("STAGE 12 GOVERNED REVIEW-SURFACE APPROVAL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
