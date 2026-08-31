#!/usr/bin/env python3
"""Safe transactional wrapper for governed Stage 12 batch approval.

Keeps the approval interface from ``approve_stage12_review_batch.py`` but moves
the Stage 11 adjudication, normalized-row update, and row-count assertion into
the same PL/pgSQL block. Any mismatch therefore aborts and rolls back the whole
batch.
"""
from __future__ import annotations

from typing import Any

import approve_stage12_review_batch as base


def safe_build_apply_sql(packet: dict[str, Any], reviewer_id: str, stable_hash: str) -> str:
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
        where = base.pk_where(pk)
        rationale = (
            f"Stage 12 governed human batch approval; batch={packet['batch_id']}; "
            f"packet_sha256={packet['packet_sha256']}; scientific_decision_sha256={stable_hash}."
        )

        if dimension:
            update_sql = (
                f"update public.{base.qident(table)} set "
                f"{base.qident(dimension + '_mapping_source')}='human_review', "
                f"{base.qident(dimension + '_review_status')}='approved' "
                f"where {where} "
                f"and {base.qident(dimension + '_mapping_source')}='agent_candidate' "
                f"and {base.qident(dimension + '_review_status')}='proposed'"
            )
        else:
            update_sql = (
                f"update public.{base.qident(table)} set mapping_source='human_review', review_status='approved' "
                f"where {where} and mapping_source='agent_candidate' and review_status='proposed'"
            )

        error_text = (
            f"Stage 12 normalized row update expected exactly one row: "
            f"batch={packet['batch_id']} table={table} candidate={candidate_id}"
        )

        statements.append(
            "do $s12row$\n"
            "declare v_rows integer;\n"
            "begin\n"
            f"  perform private.apply_scientific_adjudication_core({candidate_id},{base.sql_text(reviewer_id)}::uuid,'accept',null,{base.sql_text(rationale)});\n"
            f"  {update_sql};\n"
            "  get diagnostics v_rows = row_count;\n"
            "  if v_rows <> 1 then\n"
            f"    raise exception {base.sql_text(error_text)};\n"
            "  end if;\n"
            "end\n"
            "$s12row$;"
        )

    statements.append("commit;")
    return "\n".join(statements) + "\n"


base.build_apply_sql = safe_build_apply_sql


if __name__ == "__main__":
    raise SystemExit(base.main())
