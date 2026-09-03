#!/usr/bin/env python3
"""Enforce psychology-only health scope on Stage 13 classifications.

This is the second half of the health-scope guard. It consumes raw local-model
classifications and rechecks every record assigned to health/clinical-adjacent
against the versioned psychology-scope policy. Unsupported health labels are
removed when another CSI domain remains; otherwise the record is deterministically
excluded from the strict full-text portfolio.

Raw model outputs are preserved in their original directory. Strict outputs are
written separately. No Registry, scientific, release, Gateway, machine-screened
or human-authority state is created.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import stage13_classify_csi_domain_candidates as classifier
import stage13_classify_psychology_candidates as base
import stage13_health_psychology_scope as scope

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = (
    REPO_ROOT
    / "components/evidence-registry/config/"
    / "stage13_overnight_psychology_search.v1.json"
)
DEFAULT_POLICY = (
    REPO_ROOT
    / "components/evidence-registry/config/"
    / "stage13_health_psychology_scope_policy.v1.json"
)
HEALTH_DOMAIN = "health_clinical_adjacent"
HEALTH_TARGET_PREFIXES = ("health_", "clinical_adjacent_")


def load_json(path: Path) -> dict[str, Any]:
    return classifier.load_json(path)


def write_json(path: Path, value: Any) -> None:
    classifier.write_json(path, value)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise SystemExit(f"Raw classified JSONL not found: {path}")
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSONL at {path}:{number}: {exc}") from exc
        if not isinstance(value, dict):
            raise SystemExit(f"Expected object at {path}:{number}")
        rows.append(value)
    return rows


def non_health_default_target(domains: list[str]) -> str:
    if "performance_work" in domains:
        return "work_cognitive_performance"
    if "personal" in domains:
        return "personal_cognitive_performance"
    return "other"


def deterministic_exclusion(
    classification: dict[str, Any],
    *,
    evidence_units: list[dict[str, Any]],
    reason: str,
) -> dict[str, Any]:
    output = json.loads(json.dumps(classification))
    allowed_ids = [
        str(unit.get("unit_id"))
        for unit in evidence_units
        if isinstance(unit, dict) and unit.get("unit_id")
    ]
    cited = [
        value
        for value in output.get("evidence_unit_ids") or []
        if value in set(allowed_ids)
    ]
    if not cited and allowed_ids:
        cited = [allowed_ids[0]]
    output.update(
        {
            "screening_decision": "exclude",
            "psychology_intervention_relevant": False,
            "paper_role": "not_relevant",
            "intervention_families": ["not_applicable"],
            "candidate_routes": ["not_applicable"],
            "constraint_loci": ["not_applicable"],
            "outcome_families": ["other"],
            "transfer_signals": ["none_reported"],
            "evidence_unit_ids": cited,
            "abstract_only_confidence": max(
                0.9, float(output.get("abstract_only_confidence") or 0)
            ),
            "fulltext_priority": "not_applicable",
            "exclusion_reason": "not_intervention_relevant",
            "missing_for_fulltext": ["none_identified"],
            "screening_rationale": reason,
            "primary_csi_domain": "not_applicable",
            "csi_domains": ["not_applicable"],
            "application_targets": ["not_applicable"],
            "health_scope": "not_applicable",
        }
    )
    return output


def enforce_row(
    row: dict[str, Any], policy: dict[str, Any]
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    output = json.loads(json.dumps(row))
    candidate = output.get("candidate") or {}
    classification = output.get("classification") or {}
    if not isinstance(candidate, dict) or not isinstance(classification, dict):
        raise ValueError("Classification row lacks candidate/classification objects")

    assessment = scope.assess_candidate(candidate, policy)
    domains = [
        value
        for value in classification.get("csi_domains") or []
        if value in classifier.CSI_DOMAINS
    ]
    if HEALTH_DOMAIN not in domains:
        output["health_psychology_enforcement"] = {
            "policy_id": policy.get("policy_id"),
            "health_domain_assigned": False,
            "action": "not_applicable",
            "assessment": assessment,
        }
        return output, "not_applicable", assessment

    if assessment["qualifies_for_health_clinical_adjacent"]:
        output["health_psychology_enforcement"] = {
            "policy_id": policy.get("policy_id"),
            "health_domain_assigned": True,
            "action": "retained_psychology_related_health_domain",
            "assessment": assessment,
        }
        return output, "retained", assessment

    remaining = [value for value in domains if value != HEALTH_DOMAIN]
    if remaining:
        classification["csi_domains"] = remaining
        classification["health_scope"] = "non_health"
        classification["application_targets"] = [
            value
            for value in classification.get("application_targets") or []
            if not str(value).startswith(HEALTH_TARGET_PREFIXES)
        ]
        if not classification["application_targets"]:
            classification["application_targets"] = [
                non_health_default_target(remaining)
            ]
        classification["primary_csi_domain"] = (
            remaining[0] if len(remaining) == 1 else "cross_domain"
        )
        classification["screening_rationale"] = (
            str(classification.get("screening_rationale") or "").strip()
            + " Health/clinical-adjacent scope removed: the abstract does not "
            "make a psychology-related intervention component explicit."
        ).strip()
        action = "removed_unsupported_health_domain"
    else:
        classification = deterministic_exclusion(
            classification,
            evidence_units=output.get("evidence_units") or [],
            reason=(
                "Excluded by the Stage 13 psychology-only health scope gate: "
                "the paper concerns a health population, medical/rehabilitation "
                "service or health outcome without an explicit central "
                "psychological, cognitive, behavioural, motivational, "
                "self-regulatory, psychosocial or neuropsychological "
                "intervention component in the title/abstract."
            ),
        )
        action = "excluded_non_psychology_health_candidate"

    output["classification"] = classification
    output["ranking_score"] = classifier.ranking_score(candidate, classification)
    output["health_psychology_enforcement"] = {
        "policy_id": policy.get("policy_id"),
        "health_domain_assigned": True,
        "action": action,
        "assessment": assessment,
    }
    return output, action, assessment


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Enforce psychology-only scope on raw three-domain classifications."
    )
    parser.add_argument("--raw-output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    raw_dir = args.raw_output_dir.expanduser().resolve()
    manifest_path = args.manifest.expanduser().resolve()
    config_path = args.config.expanduser().resolve()
    policy_path = args.policy.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_json(config_path)
    policy = load_json(policy_path)
    if policy.get("schema_version") != "stage13-health-psychology-scope-policy-v1":
        raise SystemExit("Unsupported health psychology policy schema")

    raw_rows = load_jsonl(raw_dir / "classified-candidates.jsonl")
    raw_summary_path = raw_dir / "summary.json"
    raw_summary = load_json(raw_summary_path) if raw_summary_path.is_file() else {}
    raw_failures = raw_summary.get("failures") or []
    model = str(raw_summary.get("model") or (config.get("classification") or {}).get("model") or "qwen3.5:4b")

    adjusted: list[dict[str, Any]] = []
    validation_failures: list[dict[str, Any]] = []
    counts = {
        "raw_classified": len(raw_rows),
        "health_assignments_before_enforcement": 0,
        "health_assignments_retained": 0,
        "unsupported_health_domains_removed": 0,
        "non_psychology_health_candidates_excluded": 0,
        "not_applicable": 0,
    }

    print("=== STAGE 13 PSYCHOLOGY-ONLY HEALTH CLASSIFICATION ENFORCEMENT ===")
    print(f"raw_output_dir|{raw_dir}")
    print(f"policy|{policy_path}")
    print(f"raw_classified|{len(raw_rows)}")

    for row in raw_rows:
        before_domains = (row.get("classification") or {}).get("csi_domains") or []
        if HEALTH_DOMAIN in before_domains:
            counts["health_assignments_before_enforcement"] += 1
        try:
            enforced, action, assessment = enforce_row(row, policy)
            units = enforced.get("evidence_units") or []
            allowed = {
                str(unit.get("unit_id"))
                for unit in units
                if isinstance(unit, dict) and unit.get("unit_id")
            }
            errors = classifier.validate_classification(
                enforced["classification"], allowed_unit_ids=allowed
            )
            if errors:
                raise ValueError(";".join(errors))
            adjusted.append(enforced)
            if action == "retained":
                counts["health_assignments_retained"] += 1
            elif action == "removed_unsupported_health_domain":
                counts["unsupported_health_domains_removed"] += 1
            elif action == "excluded_non_psychology_health_candidate":
                counts["non_psychology_health_candidates_excluded"] += 1
                print(
                    "candidate_excluded_after_llm|"
                    f"{enforced.get('candidate_id')}|"
                    f"title={json.dumps(str((enforced.get('candidate') or {}).get('title') or '')[:160])}"
                )
            else:
                counts["not_applicable"] += 1
        except Exception as exc:
            validation_failures.append(
                {
                    "candidate_id": row.get("candidate_id"),
                    "title": (row.get("candidate") or {}).get("title"),
                    "error": str(exc),
                }
            )

    items_dir = output_dir / "items"
    items_dir.mkdir(parents=True, exist_ok=True)
    for row in adjusted:
        candidate_id = str(row.get("candidate_id") or "candidate")
        write_json(items_dir / base.safe_filename(candidate_id), row)

    generated_at = datetime.now(timezone.utc)
    combined_failures = list(raw_failures) + validation_failures
    strict_summary = classifier.write_outputs(
        output_dir=output_dir,
        discovery_manifest=manifest_path,
        config_path=config_path,
        config=config,
        model=model,
        results=adjusted,
        failures=combined_failures,
        generated_at=generated_at,
    )
    strict_summary["source_raw_output_dir"] = str(raw_dir)
    strict_summary["health_psychology_enforcement"] = {
        "policy_id": policy.get("policy_id"),
        "policy_path": str(policy_path),
        "policy_sha256": scope.discovery.sha256_text(
            scope.discovery.canonical_json(policy)
        ),
        "counts": counts,
        "validation_failures": validation_failures,
    }
    write_json(output_dir / "summary.json", strict_summary)

    violations = 0
    for row in adjusted:
        classification = row.get("classification") or {}
        if HEALTH_DOMAIN not in (classification.get("csi_domains") or []):
            continue
        assessment = (row.get("health_psychology_enforcement") or {}).get("assessment") or {}
        if not assessment.get("qualifies_for_health_clinical_adjacent"):
            violations += 1

    for key, value in counts.items():
        print(f"{key}|{value}")
    print(f"validation_failures|{len(validation_failures)}")
    print(f"health_scope_violations|{violations}")
    print(f"strict_summary|{output_dir / 'summary.json'}")
    print(f"strict_ranked_csv|{output_dir / 'ranked-candidates.csv'}")
    print(
        "strict_domain_balanced_portfolio|"
        f"{output_dir / 'domain-balanced-fulltext-portfolio.json'}"
    )
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print("MACHINE_SCREENED_STATUS_CREATED|0")
    print("HUMAN_AUTHORITY_CREATED|0")

    domain_gate = bool((strict_summary.get("summary") or {}).get("domain_gate_pass"))
    if adjusted and not validation_failures and violations == 0 and domain_gate:
        status = "PASS"
        code = 0
    elif adjusted and violations == 0:
        status = "PARTIAL"
        code = 2
    else:
        status = "FAIL"
        code = 1
    print(f"STAGE 13 PSYCHOLOGY-ONLY HEALTH ENFORCEMENT|{status}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
