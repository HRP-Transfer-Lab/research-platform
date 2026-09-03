#!/usr/bin/env python3
"""Enforce psychology-only scope for Stage 13 health candidates.

The gate is deliberately applied before local LLM classification. A health or
clinical-adjacent query hit is not enough: the title/abstract must make the
psychological, cognitive, behavioural, motivational, self-regulatory,
psychosocial or neuropsychological intervention component explicit.

General medical, nursing, occupational-therapy, physical-rehabilitation,
pharmacological, surgical or disease-service papers are excluded when health is
their only CSI query origin. For candidates also retrieved by performance/work
or personal queries, failed health query hits are removed while the remaining
non-health candidate may continue.

This script writes a filtered local discovery manifest only. It downloads no
PDFs, calls no LLM and mutates no Registry, release or Gateway state.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import stage13_discover_psychology_interventions as discovery

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

CSI_DOMAINS = {
    "performance_work",
    "personal",
    "health_clinical_adjacent",
}
HEALTH_DOMAIN = "health_clinical_adjacent"


def load_json(path: Path) -> dict[str, Any]:
    return discovery.load_json(path)


def write_json(path: Path, value: Any) -> None:
    discovery.write_json(path, value)


def normalise(value: str | None) -> str:
    text = discovery.clean_markup(value).casefold()
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


def phrase_present(text: str, phrase: str) -> bool:
    phrase = normalise(phrase)
    if not phrase:
        return False
    pattern = re.escape(phrase).replace(r"\ ", r"\s+")
    return re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", text) is not None


def phrase_hits(text: str, phrases: list[Any]) -> list[str]:
    return sorted(
        {
            str(phrase)
            for phrase in phrases
            if isinstance(phrase, str) and phrase_present(text, phrase)
        }
    )


def query_domain_map(config: dict[str, Any]) -> dict[str, str]:
    output: dict[str, str] = {}
    for row in config.get("query_families") or []:
        if not isinstance(row, dict):
            continue
        query_id = str(row.get("query_id") or "")
        domain = str(row.get("csi_domain") or "")
        if query_id and domain in CSI_DOMAINS:
            output[query_id] = domain
    return output


def candidate_origin_domains(
    candidate: dict[str, Any], mapping: dict[str, str]
) -> list[str]:
    return sorted(
        {
            mapping[str(hit.get("query_id"))]
            for hit in candidate.get("query_hits") or []
            if isinstance(hit, dict)
            and str(hit.get("query_id") or "") in mapping
        }
    )


def assess_candidate(
    candidate: dict[str, Any], policy: dict[str, Any]
) -> dict[str, Any]:
    """Assess whether health-domain use is explicitly psychology-related."""
    title = normalise(str(candidate.get("title") or ""))
    abstract = normalise(str(candidate.get("abstract") or ""))

    specific_phrases = policy.get("specific_psychology_intervention_phrases") or []
    generic_terms = policy.get("generic_psychology_terms") or []
    action_terms = policy.get("intervention_action_terms") or []
    medical_title_phrases = policy.get("general_medical_service_title_phrases") or []
    rules = policy.get("rules") or {}

    specific_title = phrase_hits(title, specific_phrases)
    specific_abstract = phrase_hits(abstract, specific_phrases)
    generic_title = phrase_hits(title, generic_terms)
    generic_abstract = phrase_hits(abstract, generic_terms)
    action_title = phrase_hits(title, action_terms)
    action_abstract = phrase_hits(abstract, action_terms)
    medical_title = phrase_hits(title, medical_title_phrases)

    minimum_generic_abstract = int(
        rules.get("generic_abstract_only_requires_distinct_psychology_terms", 2)
    )

    qualifying_basis: list[str] = []
    if rules.get("specific_phrase_in_title_qualifies", True) and specific_title:
        qualifying_basis.append("specific_psychology_intervention_phrase_in_title")
    if rules.get("specific_phrase_in_abstract_qualifies", True) and specific_abstract:
        qualifying_basis.append("specific_psychology_intervention_phrase_in_abstract")
    if (
        rules.get("generic_psychology_and_intervention_terms_in_title_qualify", True)
        and generic_title
        and action_title
    ):
        qualifying_basis.append("psychology_and_intervention_terms_in_title")
    if (
        len(generic_abstract) >= minimum_generic_abstract
        and (
            not rules.get("generic_abstract_only_requires_intervention_action", True)
            or bool(action_abstract)
        )
        and not medical_title
    ):
        qualifying_basis.append("multiple_psychology_terms_linked_to_intervention_in_abstract")

    qualifies = bool(qualifying_basis)
    if (
        medical_title
        and rules.get(
            "general_medical_service_title_requires_specific_psychology_phrase", True
        )
        and not specific_title
        and not specific_abstract
    ):
        qualifies = False
        qualifying_basis = []
        reason = "general_medical_or_rehabilitation_service_without_specific_psychology_intervention"
    elif qualifies:
        reason = "explicit_psychology_related_intervention_basis"
    else:
        reason = "no_explicit_psychology_related_intervention_basis"

    return {
        "policy_id": policy.get("policy_id"),
        "qualifies_for_health_clinical_adjacent": qualifies,
        "reason": reason,
        "qualifying_basis": qualifying_basis,
        "specific_title_hits": specific_title,
        "specific_abstract_hits": specific_abstract,
        "generic_title_hits": generic_title,
        "generic_abstract_hits": generic_abstract,
        "intervention_title_hits": action_title,
        "intervention_abstract_hits": action_abstract,
        "general_medical_service_title_hits": medical_title,
    }


def filter_candidates(
    manifest: dict[str, Any],
    *,
    config: dict[str, Any],
    policy: dict[str, Any],
    target: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    mapping = query_domain_map(config)
    if set(mapping.values()) != CSI_DOMAINS:
        raise SystemExit("Search configuration must cover all three CSI domains")

    kept: dict[str, dict[str, Any]] = {}
    excluded: list[dict[str, Any]] = []
    counts = {
        "input_candidates": 0,
        "health_candidates_evaluated": 0,
        "health_qualified": 0,
        "health_only_excluded": 0,
        "health_query_hits_removed_from_cross_domain": 0,
        "general_medical_service_excluded": 0,
    }

    for original in manifest.get("candidates") or []:
        if not isinstance(original, dict):
            continue
        counts["input_candidates"] += 1
        candidate = json.loads(json.dumps(original))
        origins = candidate_origin_domains(candidate, mapping)
        if HEALTH_DOMAIN not in origins:
            candidate["health_psychology_gate"] = {
                "applicable": False,
                "origin_domains": origins,
                "qualifies_for_health_clinical_adjacent": None,
                "policy_id": policy.get("policy_id"),
            }
            kept[str(candidate["candidate_id"])] = candidate
            continue

        counts["health_candidates_evaluated"] += 1
        assessment = assess_candidate(candidate, policy)
        assessment["applicable"] = True
        assessment["origin_domains_before_gate"] = origins
        candidate["health_psychology_gate"] = assessment

        if assessment["qualifies_for_health_clinical_adjacent"]:
            counts["health_qualified"] += 1
            kept[str(candidate["candidate_id"])] = candidate
            continue

        if assessment["general_medical_service_title_hits"]:
            counts["general_medical_service_excluded"] += 1

        retained_hits = [
            hit
            for hit in candidate.get("query_hits") or []
            if not (
                isinstance(hit, dict)
                and mapping.get(str(hit.get("query_id") or "")) == HEALTH_DOMAIN
            )
        ]
        if retained_hits:
            candidate["query_hits"] = retained_hits
            candidate["health_psychology_gate"][
                "health_query_hits_removed"
            ] = True
            candidate["health_psychology_gate"][
                "origin_domains_after_gate"
            ] = candidate_origin_domains(candidate, mapping)
            counts["health_query_hits_removed_from_cross_domain"] += 1
            kept[str(candidate["candidate_id"])] = candidate
        else:
            counts["health_only_excluded"] += 1
            excluded.append(
                {
                    "candidate_id": candidate.get("candidate_id"),
                    "title": candidate.get("title"),
                    "reason": assessment["reason"],
                    "assessment": assessment,
                }
            )

    query_ids = [
        str(row.get("query_id"))
        for row in config.get("query_families") or []
        if isinstance(row, dict) and row.get("query_id")
    ]
    selected = discovery.balanced_selection(kept, query_ids, target)
    counts["eligible_after_health_gate"] = len(kept)
    counts["selected_after_health_gate"] = len(selected)
    return selected, excluded, counts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply the psychology-only health scope gate to discovery candidates."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--target-candidates", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest_path = args.manifest.expanduser().resolve()
    config_path = args.config.expanduser().resolve()
    policy_path = args.policy.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    manifest = load_json(manifest_path)
    config = load_json(config_path)
    policy = load_json(policy_path)

    if manifest.get("schema_version") != "stage13-psychology-candidate-discovery-v1":
        raise SystemExit("Unsupported discovery manifest schema")
    if config.get("schema_version") != "stage13-overnight-psychology-search-v1":
        raise SystemExit("Unsupported search configuration schema")
    if policy.get("schema_version") != "stage13-health-psychology-scope-policy-v1":
        raise SystemExit("Unsupported health psychology policy schema")

    target = int(
        args.target_candidates
        or manifest.get("candidate_target")
        or config.get("candidate_target")
        or 100
    )
    if target < 1:
        raise SystemExit("--target-candidates must be positive")

    selected, excluded, counts = filter_candidates(
        manifest,
        config=config,
        policy=policy,
        target=target,
    )
    payload = json.loads(json.dumps(manifest))
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    payload["source_discovery_manifest"] = str(manifest_path)
    payload["candidate_target"] = target
    payload["candidates"] = selected
    summary = dict(payload.get("summary") or {})
    summary["raw_selected_candidates"] = summary.get("selected_candidates")
    summary["selected_candidates"] = len(selected)
    summary["health_psychology_gate"] = counts
    payload["summary"] = summary
    payload["health_psychology_gate"] = {
        "policy_id": policy.get("policy_id"),
        "policy_path": str(policy_path),
        "policy_sha256": discovery.sha256_text(discovery.canonical_json(policy)),
        "excluded_candidates": excluded,
        "counts": counts,
    }
    governance = dict(payload.get("governance") or {})
    governance.update(
        {
            "pdf_downloads": 0,
            "ollama_calls": 0,
            "registry_mutated": False,
            "scientific_state_mutated": False,
            "historical_release_mutated": False,
            "csi_gateway_mutated": False,
            "machine_screened_status_created": False,
            "human_authority_created": False,
        }
    )
    payload["governance"] = governance
    write_json(output_path, payload)

    print("=== STAGE 13 HEALTH PSYCHOLOGY SCOPE GATE ===")
    print(f"input_manifest|{manifest_path}")
    print(f"policy|{policy_path}")
    print(f"input_candidates|{counts['input_candidates']}")
    print(f"health_candidates_evaluated|{counts['health_candidates_evaluated']}")
    print(f"health_qualified|{counts['health_qualified']}")
    print(f"health_only_excluded|{counts['health_only_excluded']}")
    print(
        "health_query_hits_removed_from_cross_domain|"
        f"{counts['health_query_hits_removed_from_cross_domain']}"
    )
    print(
        "general_medical_service_excluded|"
        f"{counts['general_medical_service_excluded']}"
    )
    for row in excluded[:20]:
        print(
            "candidate_excluded_before_llm|"
            f"{row.get('candidate_id')}|reason={row.get('reason')}|"
            f"title={json.dumps(str(row.get('title') or '')[:160])}"
        )
    print(f"selected_candidates|{len(selected)}")
    print(f"filtered_manifest|{output_path}")
    print("PDF_DOWNLOADS|0")
    print("OLLAMA_CALLS|0")
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print("MACHINE_SCREENED_STATUS_CREATED|0")
    print("HUMAN_AUTHORITY_CREATED|0")
    status = "PASS" if len(selected) >= min(target, 3) else "PARTIAL"
    print(f"STAGE 13 HEALTH PSYCHOLOGY SCOPE GATE|{status}")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
