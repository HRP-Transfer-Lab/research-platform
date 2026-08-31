#!/usr/bin/env python3
"""Apply an explicitly human-approved Stage 12 governed review packet locally.

This tool is intentionally strict. It:
- re-validates the packet, current scientific revision, row snapshots and Stage 11 candidate bridges;
- requires exact packet SHA + stable scientific-decision SHA supplied by the human operator;
- requires an explicit batch-specific confirmation phrase;
- uses the single active Workbench owner as reviewer identity, or requires --reviewer-user-id;
- creates Stage 11 human adjudication/authority for every accepted candidate;
- changes only normalized mapping/review provenance fields, never candidate scientific values;
- runs as one PostgreSQL transaction and rolls back on any mismatch.

It is local-only: no hosted Supabase or CSI Gateway operation is performed.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from pathlib import Path
from typing import Any

import validate_stage12_review_packets as base

DEFAULT_CONTAINER = base.DEFAULT_CONTAINER
DEFAULT_PACKET_DIR = base.DEFAULT_PACKET_DIR


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


def pk_where(pk: dict[str, Any]) -> str:
    return base.pk_where(pk)


def discover_reviewer(container: str, supplied: str | None) -> str:
    if supplied:
        try:
            return str(uuid.UUID(supplied))
        except ValueError as exc:
            raise RuntimeError("--reviewer-user-id must be a UUID") from exc

    raw = psql(container, """
select user_id::text
from public.workbench_member
where active=true and role='owner'
order by user_id;
""")
    owners = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(owners) == 1:
        return owners[0]
    if not owners:
        raise RuntimeError(
            "No active local Workbench owner found. Re-run with --reviewer-user-id <your Supabase/Workbench owner UUID>; "
            "the tool will not fabricate a reviewer identity."
        )
    raise RuntimeError(
        "Multiple active Workbench owners found. Re-run with --reviewer-user-id <UUID> to identify the human reviewer explicitly."
    )


def confirmation_phrase(batch_id: str, decisions: int) -> str:
    return f"I_APPROVE_{batch_id.upper()}_{decisions}"


def build_apply_sql(packet: dict[str, Any], reviewer_id: str, stable_hash: str) -> str:
    statements: list[str] = [
        "begin;",
        "set local lock_timeout='5s';",
        "set local statement_timeout='120s';",
    ]
    decisions = [d for unit in packet["units"] for d in unit["decisions"]]

    for d in decisions:
        if d.get("proposed_action") != "approve":
            raise RuntimeError(
                f"Batch apply currently supports approve decisions only; found {d.get('proposed_action')!r} "
                f"for {d['table_name']} {d['primary_key']}"
            )

        candidate_id = int(d["candidate_id"])
        table = d["table_name"]
        pk = d["primary_key"]
        dimension = d.get("dimension")
        where = pk_where(pk)
        rationale = (
            f"Stage 12 governed human batch approval; batch={packet['batch_id']}; "
            f"packet_sha256={packet['packet_sha256']}; scientific_decision_sha256={stable_hash}."
        )

        statements.append(
            "select private.apply_scientific_adjudication_core("
            f"{candidate_id},{sql_text(reviewer_id)}::uuid,'accept',null,{sql_text(rationale)});"
        )

        if dimension:
            statements.append(
                f"update public.{qident(table)} set "
                f"{qident(dimension + '_mapping_source')}='human_review', "
                f"{qident(dimension + '_review_status')}='approved' "
                f"where {where} "
                f"and {qident(dimension + '_mapping_source')}='agent_candidate' "
                f"and {qident(dimension + '_review_status')}='proposed';"
            )
        else:
            statements.append(
                f"update public.{qident(table)} set mapping_source='human_review', review_status='approved' "
                f"where {where} and mapping_source='agent_candidate' and review_status='proposed';"
            )
        statements.append(
            "do $$ begin if not found then raise exception 'Stage 12 normalized row update affected zero rows'; end if; end $$;"
        )

    statements.extend([
        "commit;",
    ])
    return "\n".join(statements) + "\n"


def verify_post_apply(container: str, packet: dict[str, Any]) -> None:
    decisions = [d for unit in packet["units"] for d in unit["decisions"]]
    for d in decisions:
        table = d["table_name"]
        pk = d["primary_key"]
        dimension = d.get("dimension")
        where = pk_where(pk)
        if dimension:
            raw = psql(
                container,
                f"select {qident(dimension + '_mapping_source')}||'|'||{qident(dimension + '_review_status')} "
                f"from public.{qident(table)} where {where};",
            )
        else:
            raw = psql(
                container,
                f"select mapping_source||'|'||review_status from public.{qident(table)} where {where};",
            )
        if raw != "human_review|approved":
            raise RuntimeError(f"Post-apply review state mismatch for {table} {pk} {dimension or ''}: {raw!r}")

        cid = int(d["candidate_id"])
        candidate_state = psql(
            container,
            f"select candidate_status from public.scientific_field_candidate where field_candidate_id={cid};",
        )
        if candidate_state != "accepted":
            raise RuntimeError(f"Post-apply Stage 11 candidate {cid} is {candidate_state!r}, expected accepted")

        authority_count = int(psql(
            container,
            f"select count(*) from public.scientific_field_authority a "
            f"join public.scientific_field_adjudication j on j.adjudication_id=a.source_adjudication_id "
            f"where j.field_candidate_id={cid} and a.active=true;",
        ) or "0")
        if authority_count != 1:
            raise RuntimeError(f"Post-apply candidate {cid} has {authority_count} active authority rows, expected 1")


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply an explicitly human-approved Stage 12 review batch locally.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
    ap.add_argument("--batch", choices=list(base.EXPECTED), required=True)
    ap.add_argument("--packet-sha", required=True)
    ap.add_argument("--scientific-decision-sha", required=True)
    ap.add_argument("--confirm", required=True)
    ap.add_argument("--reviewer-user-id")
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container]).stdout.strip()
    base.require(running == "true", f"Local database container {args.container!r} is not running")

    path = args.packet_dir / f"{args.batch}.json"
    base.require(path.exists(), f"Missing packet {path}")
    packet = json.loads(path.read_text(encoding="utf-8"))
    current_revision = int(psql(args.container, "select current_revision from public.scientific_state_revision where singleton=true;"))
    stable_hash, units, decisions = base.validate_packet(args.container, path, current_revision)

    expected_packet_sha = packet.get("packet_sha256")
    if args.packet_sha != expected_packet_sha:
        raise RuntimeError(f"Packet SHA mismatch: supplied {args.packet_sha}, packet contains {expected_packet_sha}")
    if args.scientific_decision_sha != stable_hash:
        raise RuntimeError(
            f"Scientific-decision SHA mismatch: supplied {args.scientific_decision_sha}, current validated packet is {stable_hash}"
        )

    phrase = confirmation_phrase(args.batch, decisions)
    if args.confirm != phrase:
        raise RuntimeError(f"Explicit human confirmation required. Exact phrase: {phrase}")

    reviewer_id = discover_reviewer(args.container, args.reviewer_user_id)

    print("STAGE 12 GOVERNED BATCH APPROVAL")
    print(f"batch_id|{args.batch}")
    print(f"review_units|{units}")
    print(f"decisions|{decisions}")
    print(f"packet_sha256|{expected_packet_sha}")
    print(f"scientific_decision_sha256|{stable_hash}")
    print(f"reviewer_user_id|{reviewer_id}")
    print(f"pre_apply_scientific_revision|{current_revision}")

    sql = build_apply_sql(packet, reviewer_id, stable_hash)
    psql(args.container, sql)
    verify_post_apply(args.container, packet)

    post_revision = int(psql(args.container, "select current_revision from public.scientific_state_revision where singleton=true;"))
    print(f"post_apply_scientific_revision|{post_revision}")
    print("normalized_scientific_values_changed|0")
    print(f"human_review_approved_rows|{decisions}")
    print(f"stage11_candidates_accepted|{decisions}")
    print(f"stage11_active_authorities_established|{decisions}")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print("STAGE 12 GOVERNED BATCH APPROVAL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
