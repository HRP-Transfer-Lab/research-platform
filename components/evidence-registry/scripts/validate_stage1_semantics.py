#!/usr/bin/env python3
"""Validate Registry v1.1 Stage 1 route/evidence-role semantics.

This validator deliberately leaves the historical 2026-08-23 release JSON and
its taxonomy.v1.json untouched. It checks that every historical classification
can be resolved into the orthogonal v1.1 model and that protocol components use
only canonical intervention routes.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

EXPECTED_ROUTES = {
    "develop_equip",
    "develop_train",
    "develop_condition",
    "regulate",
    "bridge",
    "redesign",
    "integrate",
}
EXPECTED_EVIDENCE_ROLES = {
    "direct_intervention",
    "mechanism",
    "measurement",
    "observational",
    "synthesis",
}
EXPECTED_CONTROLLER_OVERLAYS = {
    "metacognitive_governor",
    "adaptive_controller",
    "external_scaffold",
    "other_controller_or_overlay",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_records(path: Path):
    if path.is_dir():
        for item in sorted(path.glob("*.json")):
            yield item.name, load_json(item)
        return
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            yield f"line {lineno}", json.loads(line)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate v1.1 Stage 1 semantic resolution.")
    parser.add_argument("records")
    parser.add_argument("--taxonomy", required=True)
    args = parser.parse_args()

    taxonomy = load_json(Path(args.taxonomy))
    records = list(iter_records(Path(args.records)))
    errors: list[str] = []

    routes = set(taxonomy.get("canonical_routes", []))
    roles = set(taxonomy.get("evidence_roles", []))
    overlays = set(taxonomy.get("controller_overlays", []))
    resolver = taxonomy.get("legacy_classification_map", {})
    synthesis_kinds = set(taxonomy.get("synthesis_source_kinds", []))

    if routes != EXPECTED_ROUTES:
        errors.append(f"canonical_routes must be exactly {sorted(EXPECTED_ROUTES)}; got {sorted(routes)}")
    if roles != EXPECTED_EVIDENCE_ROLES:
        errors.append(f"evidence_roles must be exactly {sorted(EXPECTED_EVIDENCE_ROLES)}; got {sorted(roles)}")
    if overlays != EXPECTED_CONTROLLER_OVERLAYS:
        errors.append(f"controller_overlays must be exactly {sorted(EXPECTED_CONTROLLER_OVERLAYS)}; got {sorted(overlays)}")

    role_counts: Counter[str] = Counter()
    primary_role_counts: Counter[str] = Counter()
    overlay_counts: Counter[str] = Counter()
    component_route_counts: Counter[str] = Counter()

    for location, record in records:
        source_id = record.get("record_id", location)
        classification = record.get("review", {}).get("primary_classification")
        mapping = resolver.get(classification)
        if mapping is None:
            errors.append(f"{location}: no v1.1 resolver mapping for {classification!r}")
            continue

        canonical_route = mapping.get("canonical_route")
        role = mapping.get("default_evidence_role")
        overlay = mapping.get("default_controller_overlay")

        if canonical_route is not None and canonical_route not in routes:
            errors.append(f"{location}: resolver produced illegal canonical route {canonical_route!r}")
        if role not in roles:
            errors.append(f"{location}: resolver produced unknown evidence role {role!r}")
        if overlay is not None and overlay not in overlays:
            errors.append(f"{location}: resolver produced unknown controller overlay {overlay!r}")

        primary_role = role
        source_kind = record.get("bibliography", {}).get("source_kind")
        if source_kind == "systematic_review_meta_analysis":
            primary_role = "synthesis"
            role_counts["synthesis"] += 1
            if role != "synthesis":
                role_counts[role] += 1
        elif source_kind == "scoping_review":
            role_counts[role] += 1
            role_counts["synthesis"] += 1
        else:
            role_counts[role] += 1

        primary_role_counts[primary_role] += 1
        if overlay:
            overlay_counts[overlay] += 1

        protocol = record.get("protocol") or {}
        components = protocol.get("components")
        if isinstance(components, list):
            for index, component in enumerate(components):
                component_route = component.get("route") or classification
                if component_route not in routes:
                    errors.append(
                        f"{location}: protocol component {index + 1} has non-canonical route {component_route!r}"
                    )
                else:
                    component_route_counts[component_route] += 1
        elif classification in routes:
            component_route_counts[classification] += 1

        if classification not in routes and canonical_route is not None:
            errors.append(f"{location}: legacy non-route classification unexpectedly resolves to a route")

    if sum(primary_role_counts.values()) != len(records):
        errors.append(
            f"expected exactly one primary evidence role per source; got {sum(primary_role_counts.values())} for {len(records)} records"
        )

    if errors:
        print("STAGE 1 SEMANTICS INVALID")
        for error in errors:
            print("-", error)
        return 1

    print(f"STAGE 1 SEMANTICS VALID: {len(records)} historical records resolve into v1.1 semantics")
    print("canonical_routes:", ", ".join(sorted(routes)))
    print("primary_evidence_roles:", dict(sorted(primary_role_counts.items())))
    print("evidence_role_links:", dict(sorted(role_counts.items())))
    print("controller_overlays:", dict(sorted(overlay_counts.items())))
    print("protocol_component_routes:", dict(sorted(component_route_counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
