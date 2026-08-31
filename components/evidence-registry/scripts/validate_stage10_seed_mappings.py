#!/usr/bin/env python3
"""Validate conservative Stage 10 seed mappings before database application."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage10_seed_mappings.v1.json"
SOURCE_IDS = {f"rt-2026-{i:03d}" for i in range(1, 19)}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"STAGE 10 SEED MAPPINGS INVALID: {message}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()
    p = json.loads(args.manifest.read_text(encoding="utf-8"))

    require(p.get("schema_version") == "stage10-harms-implementation-v1", "unexpected schema_version")
    require(p.get("mapping_source") == "agent_candidate", "seed must remain agent_candidate")
    require(p.get("review_status") == "proposed", "seed must remain proposed")

    harms_status = p.get("harms_status_overrides", [])
    harms = p.get("harm_observations", [])
    participation = p.get("participation_observations", [])
    implementation = p.get("implementation_observations", [])
    support = p.get("support_dependence_observations", [])
    boundaries = p.get("boundary_observations", [])
    reporting = p.get("component_reporting_assessments", [])

    require(len(harms_status) == 1, "expected one harms-status candidate override")
    require(len(harms) == 1, "expected one explicit harm observation")
    require(len(participation) == 8, "expected eight participation-flow facts")
    require(len(implementation) == 4, "expected four implementation observations")
    require(len(support) == 1, "expected one support-dependence observation")
    require(len(boundaries) == 3, "expected three boundary observations")
    require(reporting == [], "seed must not fabricate TIDieR/component reporting assessments")

    for collection in (harms_status, harms, participation, implementation, support, boundaries):
        for row in collection:
            require(row.get("source_id") in SOURCE_IDS, f"unknown source_id {row.get('source_id')!r}")

    h = harms[0]
    require(h["source_id"] == "rt-2026-013", "only explicit seed harm should be rt-2026-013")
    require(h["harm_type"] == "performance_tradeoff", "rt-013 signal must remain performance trade-off")
    require(h.get("event_count") is None, "must not invent event_count")
    require(h.get("participant_count") is None, "must not invent participant_count")
    require(h.get("systematically_assessed") is False, "must not portray rt-013 as systematic adverse-event surveillance")
    require(h.get("withdrawal_due_to_harm") is None, "withdrawal due to harm must remain unknown when not reported")
    require(h.get("serious") is None, "seriousness must remain unknown when not established")

    flow_sources = {(r["source_id"], r["flow_kind"], r["participant_count"]) for r in participation}
    required_flows = {
        ("rt-2026-001","randomized",54), ("rt-2026-001","analysed",51),
        ("rt-2026-006","randomized",162), ("rt-2026-006","completed",138),
        ("rt-2026-009","enrolled",23), ("rt-2026-009","followup_assessed",22),
        ("rt-2026-015","entered",180), ("rt-2026-015","completed",168),
    }
    require(flow_sources == required_flows, "participation-flow facts changed")

    impl_dims = [(r["source_id"], r["dimension"]) for r in implementation]
    require(impl_dims.count(("rt-2026-001","delivery_mode")) == 1, "rt-001 delivery mode missing")
    require(impl_dims.count(("rt-2026-003","delivery_mode")) == 1, "rt-003 delivery mode missing")
    require(impl_dims.count(("rt-2026-004","delivery_mode")) == 1, "rt-004 delivery mode missing")
    require(impl_dims.count(("rt-2026-015","materials_procedures")) == 1, "rt-015 procedure observation missing")
    require(all(r["dimension"] not in {"fidelity","adherence","cost_resources","implementation_burden"} for r in implementation), "unsupported fidelity/adherence/cost/burden mapping present")

    s = support[0]
    require(s["source_id"] == "rt-2026-015", "unsupported/no-AI test signal must be rt-015")
    require(s["support_type"] == "ai_assistance" and s["support_presence"] == "absent", "rt-015 support condition changed")
    require(s["support_requirement"] == "absent_at_test" and s["autonomy_status"] == "unsupported_demonstrated", "rt-015 independent-test semantics changed")

    bmap = {(r["source_id"],r["boundary_direction"]) for r in boundaries}
    require(("rt-2026-015","independence_not_demonstrated") in bmap, "rt-015 Bridge boundary missing")
    require(("rt-2026-016","effect_dissociation") in bmap, "rt-016 speed/effort dissociation missing")
    require(("rt-2026-018","observational_association") in bmap, "rt-018 observational dependence boundary missing")

    notes = " ".join(p.get("notes", [])).lower()
    require("no zero-harm conclusion" in notes, "zero-harm noninference note missing")
    require("not treated as adherence" in notes, "participation/adherence separation note missing")
    require("do not auto-create stage 4 bridge evidence" in notes, "Bridge non-promotion note missing")

    print("STAGE 10 SEED MAPPINGS VALID: harms=1; participation=8; implementation=4; support=1; boundaries=3; component_reporting=0")
    print("no_harm_noninference: PASS")
    print("harm_attribute_missingness: PASS (seriousness / harm-withdrawal remain unknown when not established)")
    print("participation_vs_adherence_boundary: PASS")
    print("support_vs_bridge_boundary: PASS")
    print("observational_vs_causal_boundary: PASS")
    print("human_approval_boundary: PASS (agent_candidate / proposed only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
