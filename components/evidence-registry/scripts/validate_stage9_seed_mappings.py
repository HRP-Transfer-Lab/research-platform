#!/usr/bin/env python3
"""Validate conservative Stage 9 population/context seed mappings before DB application."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = REPO_ROOT / "components/evidence-registry/data/stage9_seed_mappings.v1.json"

FACETS = {
    "life_stage",
    "role",
    "health_condition_context",
    "baseline_cognitive_status",
    "education_level",
    "study_setting",
    "delivery_context",
    "geography",
}
RELATIONSHIPS = {"entire_sample", "includes_subgroup", "study_context", "unclear_scope"}
SOURCE_IDS = {f"rt-2026-{i:03d}" for i in range(1, 19)}

TERM_FACETS = {
    "pc_life_child": "life_stage",
    "pc_life_young_adult": "life_stage",
    "pc_life_adult": "life_stage",
    "pc_life_older_adult": "life_stage",
    "pc_role_student": "role",
    "pc_role_university_student": "role",
    "pc_role_school_student": "role",
    "pc_role_early_career_knowledge_worker": "role",
    "pc_health_healthy_nonclinical": "health_condition_context",
    "pc_health_learning_difficulties": "health_condition_context",
    "pc_cog_cognitively_normal": "baseline_cognitive_status",
    "pc_edu_kindergarten": "education_level",
    "pc_edu_school": "education_level",
    "pc_edu_middle_school": "education_level",
    "pc_edu_higher": "education_level",
    "pc_setting_research_training": "study_setting",
    "pc_setting_controlled_research": "study_setting",
    "pc_setting_school": "study_setting",
    "pc_setting_university_classroom": "study_setting",
    "pc_setting_community": "study_setting",
    "pc_setting_online": "study_setting",
    "pc_setting_lab": "study_setting",
    "pc_setting_evidence_synthesis": "study_setting",
    "pc_delivery_guided_training": "delivery_context",
    "pc_delivery_researcher_facilitated": "delivery_context",
    "pc_delivery_tablet_game": "delivery_context",
    "pc_delivery_structured_task_training": "delivery_context",
    "pc_geo_china": "geography",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"STAGE 9 SEED MAPPINGS INVALID: {message}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Stage 9 candidate population/context manifest.")
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()

    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    require(payload.get("schema_version") == "stage9-population-context-v1", "unexpected schema_version")
    require(payload.get("mapping_source") == "agent_candidate", "seed mappings must remain agent_candidate")
    require(payload.get("review_status") == "proposed", "seed mappings must remain proposed")

    study_rows = payload.get("study_mappings", [])
    delivery_rows = payload.get("component_delivery_mappings", [])
    fit_rows = payload.get("context_fit_assessments", [])
    require(isinstance(study_rows, list) and study_rows, "study_mappings must be a non-empty list")
    require(isinstance(delivery_rows, list), "component_delivery_mappings must be a list")
    require(fit_rows == [], "immutable seed must not manufacture context-fit judgements")

    seen_study = set()
    facets_by_source: dict[str, set[str]] = defaultdict(set)
    relation_counts = Counter()
    facet_counts = Counter()
    for row in study_rows:
        source_id = row.get("source_id")
        term_id = row.get("term_id")
        relationship = row.get("relationship")
        basis = (row.get("evidence_basis") or "").strip()
        require(source_id in SOURCE_IDS, f"unknown source_id {source_id!r}")
        require(term_id in TERM_FACETS, f"unknown term_id {term_id!r}")
        facet = TERM_FACETS[term_id]
        require(facet != "delivery_context", f"delivery-context term {term_id} cannot be study mapping")
        require(relationship in RELATIONSHIPS, f"invalid relationship {relationship!r}")
        require(bool(basis), f"missing evidence_basis for {source_id}/{term_id}")
        key = (source_id, term_id, relationship)
        require(key not in seen_study, f"duplicate study mapping {key}")
        seen_study.add(key)
        facets_by_source[source_id].add(facet)
        relation_counts[relationship] += 1
        facet_counts[facet] += 1

    seen_delivery = set()
    for row in delivery_rows:
        source_id = row.get("source_id")
        component_name = (row.get("component_name") or "").strip()
        term_id = row.get("term_id")
        basis = (row.get("evidence_basis") or "").strip()
        require(source_id in SOURCE_IDS, f"unknown delivery source_id {source_id!r}")
        require(bool(component_name), f"missing component_name for delivery mapping on {source_id}")
        require(TERM_FACETS.get(term_id) == "delivery_context", f"delivery mapping requires delivery_context term; got {term_id!r}")
        require(bool(basis), f"missing delivery evidence_basis for {source_id}/{component_name}/{term_id}")
        key = (source_id, component_name, term_id)
        require(key not in seen_delivery, f"duplicate delivery mapping {key}")
        seen_delivery.add(key)

    mapped_sources = set(facets_by_source)
    require(mapped_sources == SOURCE_IDS, f"all 18 seed studies should have at least one conservative mapping; missing={sorted(SOURCE_IDS-mapped_sources)}")

    # Scientific guardrails against common over-generalisation mistakes.
    rt004_terms = {term for source, term, _ in seen_study if source == "rt-2026-004"}
    require({"pc_life_young_adult","pc_role_university_student","pc_health_healthy_nonclinical","pc_edu_higher"}.issubset(rt004_terms), "rt-2026-004 must retain distinct young-adult/student/healthy/higher-education facets")
    require("pc_life_adult" not in rt004_terms, "rt-2026-004 must not collapse young adults to generic adult in seed mapping")

    rt005_life = {(term, rel) for source, term, rel in seen_study if source == "rt-2026-005" and TERM_FACETS[term] == "life_stage"}
    require(("pc_life_young_adult","includes_subgroup") in rt005_life and ("pc_life_older_adult","includes_subgroup") in rt005_life, "mixed-age rt-2026-005 must preserve both subgroups")

    rt018_roles = {(term, rel) for source, term, rel in seen_study if source == "rt-2026-018" and TERM_FACETS[term] == "role"}
    require(("pc_role_university_student","includes_subgroup") in rt018_roles and ("pc_role_early_career_knowledge_worker","includes_subgroup") in rt018_roles, "rt-2026-018 mixed roles must remain subgroup-scoped")

    geography_rows = [row for row in study_rows if TERM_FACETS[row["term_id"]] == "geography"]
    require(len(geography_rows) == 1 and geography_rows[0]["source_id"] == "rt-2026-015" and geography_rows[0]["term_id"] == "pc_geo_china", "geography seed should remain limited to the one explicit China mapping")

    print(
        "STAGE 9 SEED MAPPINGS VALID: "
        f"study_links={len(study_rows)}; mapped_sources={len(mapped_sources)}; "
        f"delivery_links={len(delivery_rows)}; context_fit=0"
    )
    print("facet_counts: " + ", ".join(f"{k}={facet_counts[k]}" for k in sorted(facet_counts)))
    print("relationship_counts: " + ", ".join(f"{k}={relation_counts[k]}" for k in sorted(relation_counts)))
    print("orthogonal_population_boundary: PASS")
    print("mixed_population_subgroup_boundary: PASS")
    print("delivery_setting_separation: PASS")
    print("geography_noninference_boundary: PASS")
    print("context_fit_nonfabrication: PASS")
    print("human_approval_boundary: PASS (agent_candidate / proposed only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
