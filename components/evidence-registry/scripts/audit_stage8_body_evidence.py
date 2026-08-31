#!/usr/bin/env python3
"""Read-only audit for Stage 8 proposition/synthesis/body-certainty architecture."""
from __future__ import annotations

import argparse
import subprocess

DEFAULT_CONTAINER = "supabase_db_research-platform"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", container,
        "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres",
        "-A", "-t", "-F", "|",
    ]
    return run(cmd, input_text=sql, capture=True).stdout.strip()


def scalar(container: str, sql: str) -> int:
    raw = psql(container, sql)
    try:
        return int(raw or "0")
    except ValueError as exc:
        raise SystemExit(f"Expected integer SQL result, got {raw!r}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"STAGE 8 AUDIT INVALID: {message}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit current body-evidence/synthesis state before Stage 8 migration.")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()

    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    require(running == "true", f"local database container {args.container!r} is not running")

    legacy_syntheses = scalar(args.container, "select count(*) from public.evidence_synthesis;")
    legacy_synthesis_sources = scalar(args.container, "select count(*) from public.synthesis_source;")
    legacy_claims = scalar(args.container, "select count(*) from public.approved_claim;")

    source_eml = scalar(args.container, "select count(*) from public.evidence_maturity_assessment where scope='record_contribution' and source_id is not null;")
    body_eml = scalar(args.container, "select count(*) from public.evidence_maturity_assessment where scope='body_of_evidence';")
    synthesis_eml = scalar(args.container, "select count(*) from public.evidence_maturity_assessment where synthesis_id is not null;")
    claim_eml = scalar(args.container, "select count(*) from public.evidence_maturity_assessment where claim_id is not null;")

    stage6_effects = scalar(args.container, "select count(*) from public.effect_estimate;")
    source_level_synthesis_effects = scalar(args.container, "select count(*) from public.effect_estimate where estimate_scope='source_level_synthesis';")

    studies = scalar(args.container, "select count(*) from public.study;")
    outcomes = scalar(args.container, "select count(*) from public.evidence_outcome;")
    contrasts = scalar(args.container, "select count(*) from public.study_contrast;")
    effects = scalar(args.container, "select count(*) from public.effect_estimate;")

    print("=== LEGACY BODY-EVIDENCE TABLES ===")
    print(f"evidence_synthesis_rows|{legacy_syntheses}")
    print(f"synthesis_source_rows|{legacy_synthesis_sources}")
    print(f"approved_claim_rows|{legacy_claims}")

    print("=== EML SUBJECTS ===")
    print(f"source_record_contribution_eml|{source_eml}")
    print(f"body_of_evidence_eml|{body_eml}")
    print(f"synthesis_subject_eml|{synthesis_eml}")
    print(f"claim_subject_eml|{claim_eml}")

    print("=== RESULT / CONTRIBUTION SUBJECT INVENTORY ===")
    print(f"studies|{studies}")
    print(f"outcomes|{outcomes}")
    print(f"contrasts|{contrasts}")
    print(f"effect_estimates|{effects}")

    print("=== STAGE 6 SOURCE-LEVEL SYNTHESIS EFFECTS ===")
    if source_level_synthesis_effects:
        rows = psql(args.container, """
select es.source_id,
       eo.outcome_name,
       ee.estimate_type,
       ee.metric,
       ee.estimate_value,
       ee.ci_lower,
       ee.ci_upper,
       coalesce(ee.ci_level::text,'NULL'),
       ee.estimate_scope
from public.effect_estimate ee
join public.evidence_outcome eo on eo.outcome_id=ee.outcome_id
join public.study s on s.study_id=eo.study_id
join public.evidence_source es on es.source_id=s.source_id
where ee.estimate_scope='source_level_synthesis'
order by ee.effect_estimate_id;
""")
        print(rows)
    else:
        print("none")

    # The current immutable seed is expected to contain no body-level synthesis/claim authority.
    require(legacy_syntheses == 0, f"expected 0 legacy evidence_synthesis rows in seed; got {legacy_syntheses}")
    require(legacy_synthesis_sources == 0, f"expected 0 legacy synthesis_source rows in seed; got {legacy_synthesis_sources}")
    require(legacy_claims == 0, f"expected 0 legacy approved_claim rows in seed; got {legacy_claims}")
    require(body_eml == 0, f"expected 0 body-of-evidence EML rows before Stage 8; got {body_eml}")
    require(synthesis_eml == 0, f"expected 0 synthesis-subject EML rows before Stage 8; got {synthesis_eml}")
    require(claim_eml == 0, f"expected 0 claim-subject EML rows before Stage 8; got {claim_eml}")
    require(source_eml == 18, f"expected 18 source record-contribution EML rows; got {source_eml}")
    require(stage6_effects == 1, f"expected 1 Stage 6 first-class seed effect; got {stage6_effects}")
    require(source_level_synthesis_effects == 1, f"expected exactly 1 source-level synthesis effect; got {source_level_synthesis_effects}")

    print("BODY AUTHORITY BOUNDARY: PASS (0 propositions/syntheses/claims/body EML currently exist)")
    print("SOURCE EML BOUNDARY: PASS (18 record-contribution EML rows remain source-level only)")
    print("SYNTHESIS EFFECT BOUNDARY: PASS (1 source-level pooled effect must remain representable without fake Stage 5 contrast)")
    print("STAGE 8 AUDIT PASS: read-only body-evidence inventory complete; no proposition, GRADE, body EML or approved claim has been created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
