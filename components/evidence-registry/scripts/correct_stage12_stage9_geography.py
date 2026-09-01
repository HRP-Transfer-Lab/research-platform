#!/usr/bin/env python3
"""Governed Stage 12 correction for the rt-2026-015 geography over-inference.

The original Stage 9 candidate mapped ``pc_geo_china`` because the reviewed
population was described as "Chinese undergraduates". That is a population
nationality/ethnicity descriptor, not evidence that the study occurred in
China. Stage 9 explicitly forbids unsupported geography inference.

This one-time correction:
- validates the original 121-decision Stage 9 packet at its bound revision;
- rejects the erroneous geography-term candidate and removes that normalized row;
- corrects the geography facet status to human-reviewed ``not_yet_extracted``;
- establishes Stage 11 authority for the corrected status;
- surgically removes the bad mapping from the local Stage 9 seed manifest so
  future replay cannot recreate it.

It does not mutate the historical release or CSI Gateway.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import approve_stage12_review_surface_packet as approval
import prepare_stage12_review_surface_packets as prep
import validate_stage12_review_surface_packet as validator

EXPECTED_BATCH = "stage9_context"
EXPECTED_PACKET_SHA = "af21c00c7e71c1271a24625c1b02f858e25c17cca23b883a7cdfc4e1917dc3bc"
EXPECTED_REVISION = 2631
EXPECTED_DECISIONS = 121
CONFIRMATION = "I_CORRECT_STAGE9_RT_2026_015_GEOGRAPHY"
DEFAULT_PACKET = prep.DEFAULT_OUTPUT_DIR / "stage9_context.json"
DEFAULT_MANIFEST = prep.REPO_ROOT / "components/evidence-registry/data/stage9_seed_mappings.v1.json"

BAD_MANIFEST_LINE = (
    '    {"source_id":"rt-2026-015","term_id":"pc_geo_china","relationship":"entire_sample",'
    '"evidence_basis":"Population explicitly described as Chinese undergraduates; no finer geographic inference made."},\n'
)
GEOGRAPHY_PRINCIPLE = '    "Population nationality or ethnicity does not establish study geography.",\n'
INSERT_AFTER = '    "Do not infer geography from institution names unless geography is explicit.",\n'

CORRECTED_NOTE = (
    "Human review: study geography is not established by the reviewed seed; "
    "'Chinese undergraduates' is a population descriptor, not study-location evidence."
)


def dollar_json(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if "$s9geo$" in text:
        raise RuntimeError("Unexpected dollar-quote marker in JSON")
    return "$s9geo$" + text + "$s9geo$::jsonb"


def all_decisions(packet: dict) -> list[dict]:
    return [d for unit in packet["units"] for d in unit["decisions"]]


def exactly_one(decisions: list[dict], predicate, label: str) -> dict:
    matches = [d for d in decisions if predicate(d)]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {label} decision, found {len(matches)}")
    return matches[0]


def validate_manifest_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.count(BAD_MANIFEST_LINE) != 1:
        raise RuntimeError("Expected exactly one pc_geo_china Stage 9 manifest mapping")
    if INSERT_AFTER not in text:
        raise RuntimeError("Expected Stage 9 geography principle anchor not found")
    return text


def corrected_manifest_text(text: str) -> str:
    text = text.replace(BAD_MANIFEST_LINE, "", 1)
    if GEOGRAPHY_PRINCIPLE not in text:
        text = text.replace(INSERT_AFTER, INSERT_AFTER + GEOGRAPHY_PRINCIPLE, 1)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply governed correction for Stage 9 rt-2026-015 geography inference.")
    ap.add_argument("--container", default=prep.DEFAULT_CONTAINER)
    ap.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    ap.add_argument("--packet-sha", required=True)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--reviewer-user-id")
    ap.add_argument("--confirm", required=True)
    args = ap.parse_args()

    if args.confirm != CONFIRMATION:
        raise RuntimeError(f"Explicit human confirmation required. Exact phrase: {CONFIRMATION}")
    if args.packet_sha != EXPECTED_PACKET_SHA:
        raise RuntimeError("Supplied packet SHA does not match the reviewed Stage 9 packet")

    manifest_before = validate_manifest_text(args.manifest)
    packet, stable_hash = validator.validate_packet(args.container, args.packet)
    if packet["batch_id"] != EXPECTED_BATCH:
        raise RuntimeError(f"Expected batch {EXPECTED_BATCH}, got {packet['batch_id']}")
    if packet["packet_sha256"] != EXPECTED_PACKET_SHA:
        raise RuntimeError("Validated packet SHA differs from expected reviewed packet")
    if packet["scientific_state_revision"] != EXPECTED_REVISION:
        raise RuntimeError("Original Stage 9 packet is not bound to expected scientific revision 2631")
    if packet["decision_count"] != EXPECTED_DECISIONS:
        raise RuntimeError("Original Stage 9 packet does not contain 121 decisions")

    decisions = all_decisions(packet)
    status_decision = exactly_one(
        decisions,
        lambda d: d["table_name"] == "study_population_context_status"
        and d["primary_key"] == {"facet_kind": "geography", "study_id": 15},
        "study 15 geography status",
    )
    term_decision = exactly_one(
        decisions,
        lambda d: d["table_name"] == "study_population_context_term"
        and d["primary_key"] == {
            "relationship": "entire_sample", "study_id": 15, "term_id": "pc_geo_china"
        },
        "study 15 pc_geo_china term",
    )

    reviewer_id = approval.discover_reviewer(args.container, args.reviewer_user_id)
    pre_revision = int(approval.psql(
        args.container,
        "select current_revision from public.scientific_state_revision where singleton=true;",
    ))
    if pre_revision != EXPECTED_REVISION:
        raise RuntimeError(f"Scientific revision moved: expected {EXPECTED_REVISION}, found {pre_revision}")

    status_candidate = int(status_decision["candidate_id"])
    term_candidate = int(term_decision["candidate_id"])
    corrected_value = {
        "extraction_status": "not_yet_extracted",
        "facet_kind": "geography",
        "notes": CORRECTED_NOTE,
        "study_id": 15,
    }
    rationale = (
        "Stage 12 human correction: population descriptor 'Chinese undergraduates' does not establish "
        "study geography. Remove pc_geo_china and retain geography as not_yet_extracted. "
        f"Original packet={EXPECTED_PACKET_SHA}; scientific_decision_sha256={stable_hash}."
    )

    sql = f"""
begin;
set local lock_timeout='5s';
set local statement_timeout='60s';

select private.apply_scientific_adjudication_core(
  {term_candidate}, {approval.sql_text(reviewer_id)}::uuid, 'reject', null, {approval.sql_text(rationale)}
);

do $s9term$
declare n bigint;
begin
  delete from public.study_population_context_term
  where study_id=15 and term_id='pc_geo_china' and relationship='entire_sample'
    and mapping_source='agent_candidate' and review_status='proposed';
  get diagnostics n = row_count;
  if n <> 1 then
    raise exception 'Expected to delete exactly one proposed pc_geo_china normalized term, deleted %', n;
  end if;
end
$s9term$;

select private.apply_scientific_adjudication_core(
  {status_candidate}, {approval.sql_text(reviewer_id)}::uuid, 'correct', {dollar_json(corrected_value)},
  {approval.sql_text(rationale)}
);

do $s9status$
declare n bigint;
begin
  update public.study_population_context_status
  set extraction_status='not_yet_extracted',
      mapping_source='human_review',
      review_status='approved',
      notes={approval.sql_text(CORRECTED_NOTE)},
      updated_at=now()
  where study_id=15 and facet_kind='geography'
    and mapping_source='agent_candidate' and review_status='proposed';
  get diagnostics n = row_count;
  if n <> 1 then
    raise exception 'Expected to correct exactly one study 15 geography status row, updated %', n;
  end if;
end
$s9status$;

commit;
"""
    approval.psql(args.container, sql)

    term_state = approval.psql(
        args.container,
        "select candidate_status from public.scientific_field_candidate "
        f"where field_candidate_id={term_candidate};",
    )
    status_state = approval.psql(
        args.container,
        "select candidate_status from public.scientific_field_candidate "
        f"where field_candidate_id={status_candidate};",
    )
    normalized_term_count = int(approval.psql(
        args.container,
        "select count(*) from public.study_population_context_term "
        "where study_id=15 and term_id='pc_geo_china' and relationship='entire_sample';",
    ) or "0")
    normalized_status = approval.psql(
        args.container,
        "select extraction_status||'|'||mapping_source||'|'||review_status "
        "from public.study_population_context_status where study_id=15 and facet_kind='geography';",
    )
    authority_count = int(approval.psql(
        args.container,
        "select count(*) from public.scientific_field_authority a "
        "join public.scientific_field_adjudication j on j.adjudication_id=a.source_adjudication_id "
        f"where j.field_candidate_id={status_candidate} and a.active=true;",
    ) or "0")
    post_revision = int(approval.psql(
        args.container,
        "select current_revision from public.scientific_state_revision where singleton=true;",
    ))

    if term_state != "rejected":
        raise RuntimeError(f"Term candidate post-state {term_state!r}, expected rejected")
    if status_state != "accepted":
        raise RuntimeError(f"Status candidate post-state {status_state!r}, expected accepted after correction")
    if normalized_term_count != 0:
        raise RuntimeError("pc_geo_china normalized term still exists after correction")
    if normalized_status != "not_yet_extracted|human_review|approved":
        raise RuntimeError(f"Unexpected corrected geography status: {normalized_status!r}")
    if authority_count != 1:
        raise RuntimeError(f"Corrected geography status has {authority_count} active authority rows, expected 1")

    args.manifest.write_text(corrected_manifest_text(manifest_before), encoding="utf-8")

    print("STAGE 12 STAGE 9 GEOGRAPHY CORRECTION PASS")
    print(f"original_packet_sha256|{packet['packet_sha256']}")
    print(f"original_scientific_decision_sha256|{stable_hash}")
    print(f"reviewer_user_id|{reviewer_id}")
    print(f"term_candidate_rejected|{term_candidate}")
    print(f"status_candidate_corrected|{status_candidate}")
    print("normalized_pc_geo_china_rows|0")
    print("geography_status|not_yet_extracted|human_review|approved")
    print(f"pre_apply_scientific_revision|{pre_revision}")
    print(f"post_apply_scientific_revision|{post_revision}")
    print("historical_release_mutation_attempted|0")
    print("csi_gateway_mutation_attempted|0")
    print(f"manifest_updated|{args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
