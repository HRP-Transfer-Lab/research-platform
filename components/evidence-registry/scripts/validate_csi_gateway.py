#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "gateway" / "contract.v1.json"


def main() -> None:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert data["contract_version"] == "csi-evidence-v1"
    assert data["schema_version"] == "1.0.0"
    assert data["status"] == "active"

    views = data["views"]
    assert views == {
        "contract": "v_csi_gateway_contract_v1",
        "release": "v_csi_gateway_release_v1",
        "evidence": "v_csi_gateway_evidence_v1",
        "claim": "v_csi_gateway_claim_v1",
    }

    required_guarantees = {
        "read_only",
        "approved_release_only",
        "release_pinned",
        "no_person_data",
        "no_workbench_or_audit_data",
        "no_raw_extraction_json",
        "study_level_claim_boundary_until_approved_synthesis",
    }
    assert required_guarantees.issubset(set(data["guarantees"]))

    filters = data["filters"]
    for required_filter in (
        "evidence_release_id",
        "evidence_class",
        "primary_classification",
        "route_classes",
        "population_tags",
        "topic_tags",
        "functional_domains",
        "product_ids",
        "evidence_rungs",
        "peer_review_status",
    ):
        assert required_filter in filters

    current = data["current_release"]
    assert current["evidence_release_id"] == "2026-08-23"
    assert current["taxonomy_version"] == "iqm-route-v0.2"
    assert current["source_record_count"] == 18
    assert current["approved_claim_count"] == 0
    assert current["claim_boundary"] == "study_level_only"

    assert "never write user/person data" in data["consumer_rule"]

    print("CSI EVIDENCE GATEWAY CONTRACT PASS")


if __name__ == "__main__":
    main()
