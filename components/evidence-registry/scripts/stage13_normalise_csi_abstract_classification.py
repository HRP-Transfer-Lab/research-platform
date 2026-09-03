#!/usr/bin/env python3
"""Conservative normalisation for Stage 13 local abstract classifications.

Qwen 3.5 4B usually returns the requested JSON object, but may leave controlled
arrays empty on exclusions, duplicate array values, or pair a health CSI domain
with ``non_health`` and ``not_applicable`` targets. These are representation and
cross-field consistency failures rather than reasons to spend a second model
call on the same prompt.

This module repairs only those bounded structural inconsistencies. It never
upgrades an exclusion to inclusion. Raw model output and every repair action are
preserved by the resilient classifier wrapper.
"""
from __future__ import annotations

import json
from typing import Any

import stage13_classify_psychology_candidates as base
import stage13_classify_csi_domain_candidates as domains

NORMALISATION_VERSION = "stage13-three-domain-normalisation-v1"

ARRAY_FIELDS: dict[str, set[str]] = {
    "intervention_families": base.INTERVENTION_FAMILIES,
    "candidate_routes": base.ROUTES,
    "constraint_loci": base.CONSTRAINT_LOCI,
    "outcome_families": base.OUTCOME_FAMILIES,
    "transfer_signals": base.TRANSFER_SIGNALS,
    "missing_for_fulltext": base.MISSING_FIELDS,
    "csi_domains": domains.CSI_DOMAINS | {"not_applicable"},
    "application_targets": domains.APPLICATION_TARGETS,
}


def dedupe_valid(values: Any, allowed: set[str]) -> list[str]:
    if not isinstance(values, list):
        return []
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str) or value not in allowed or value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def record_action(
    actions: list[dict[str, Any]],
    *,
    field: str,
    action: str,
    before: Any,
    after: Any,
) -> None:
    if before == after:
        return
    actions.append(
        {
            "field": field,
            "action": action,
            "before": before,
            "after": after,
        }
    )


def replace(
    output: dict[str, Any],
    actions: list[dict[str, Any]],
    field: str,
    value: Any,
    action: str,
) -> None:
    before = output.get(field)
    output[field] = value
    record_action(actions, field=field, action=action, before=before, after=value)


def default_route(role: str) -> str:
    if role == "measurement":
        return "measure_prove"
    if role == "mechanism":
        return "mechanism_only"
    return "not_applicable"


def default_application_target(
    supported_domains: list[str], intervention_families: list[str]
) -> str:
    families = set(intervention_families)
    if "health_clinical_adjacent" in supported_domains:
        if families & {
            "attention_cognitive_control",
            "working_memory_relational_binding",
            "reasoning_problem_solving",
        }:
            return "health_cognitive_rehabilitation"
        if "implementation_or_coupling_support" in families:
            return "health_adherence_and_participation"
        if families & {
            "self_regulation_goal_management",
            "digital_psychological_behavioural",
        }:
            return "health_symptom_self_management"
        return "clinical_adjacent_cognitive_affective_support"
    if "performance_work" in supported_domains:
        if families & {
            "human_ai_cognitive_support",
            "workflow_organisational_redesign",
            "implementation_or_coupling_support",
        }:
            return "work_human_ai_and_workflow"
        if "stress_emotion_resilience" in families:
            return "work_wellbeing_resilience"
        if "self_regulation_goal_management" in families:
            return "work_motivation_engagement"
        return "work_cognitive_performance"
    if "personal" in supported_domains:
        if "metacognitive_learning_strategy" in families:
            return "personal_learning_and_study"
        if "reasoning_problem_solving" in families:
            return "personal_reasoning_and_decision"
        if "self_regulation_goal_management" in families:
            return "personal_self_regulation_and_habits"
        if families & {
            "stress_emotion_resilience",
            "digital_psychological_behavioural",
        }:
            return "personal_wellbeing_and_resilience"
        return "personal_cognitive_performance"
    return "other"


def bounded_confidence(value: Any, default: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return default
    return min(1.0, max(0.0, float(value)))


def canonical_exclusion(
    value: dict[str, Any],
    *,
    allowed_unit_ids: set[str],
    actions: list[dict[str, Any]],
) -> dict[str, Any]:
    specific_reason = value.get("exclusion_reason")
    if specific_reason not in base.EXCLUSION_REASONS - {"not_excluded"}:
        specific_reason = "not_intervention_relevant"

    canonical = {
        "screening_decision": "exclude",
        "psychology_intervention_relevant": False,
        "paper_role": "not_relevant",
        "study_design": (
            value.get("study_design")
            if value.get("study_design") in base.STUDY_DESIGNS
            else "unclear"
        ),
        "intervention_families": ["not_applicable"],
        "candidate_routes": ["not_applicable"],
        "constraint_loci": ["not_applicable"],
        "population_summary": str(value.get("population_summary") or ""),
        "intervention_summary": str(value.get("intervention_summary") or ""),
        "comparator_summary": str(value.get("comparator_summary") or ""),
        "outcome_families": ["not_reported"],
        "transfer_signals": ["none_reported"],
        "evidence_unit_ids": dedupe_valid(
            value.get("evidence_unit_ids"), allowed_unit_ids
        ),
        "abstract_only_confidence": bounded_confidence(
            value.get("abstract_only_confidence"), 0.8
        ),
        "fulltext_priority": "not_applicable",
        "exclusion_reason": specific_reason,
        "missing_for_fulltext": ["none_identified"],
        "screening_rationale": (
            str(value.get("screening_rationale") or "").strip()
            or "Excluded at abstract screening because no relevant psychology intervention basis was established."
        ),
        "primary_csi_domain": "not_applicable",
        "csi_domains": ["not_applicable"],
        "application_targets": ["not_applicable"],
        "health_scope": "not_applicable",
    }
    for field, after in canonical.items():
        record_action(
            actions,
            field=field,
            action="canonicalise_exclusion",
            before=value.get(field),
            after=after,
        )
    return canonical


def normalise_classification(
    value: dict[str, Any],
    *,
    allowed_unit_ids: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return a validly shaped candidate or raise on unrepairable semantics.

    Repairs are conservative:

    - exclusions are canonicalised and never upgraded;
    - duplicate/invalid controlled-array values are removed;
    - empty non-semantic arrays receive explicit unknown/not-applicable values;
    - health scope and application-target fields are aligned with an already
      selected CSI-domain classification;
    - contradictory inclusion/relevance output is resolved to exclusion.

    The psychology-only health gate still runs independently before and after
    this step. This function does not decide whether a health paper is in scope.
    """

    if not isinstance(value, dict):
        raise ValueError("classification must be an object")

    expected_fields = set(domains.extended_schema()["required"])
    output = {
        key: json.loads(json.dumps(item))
        for key, item in value.items()
        if key in expected_fields
    }
    actions: list[dict[str, Any]] = []
    for key in sorted(set(value) - expected_fields):
        record_action(
            actions,
            field=key,
            action="drop_unregistered_field",
            before=value.get(key),
            after=None,
        )

    decision = output.get("screening_decision")
    if decision not in base.SCREENING_DECISIONS:
        raise ValueError("screening_decision is invalid and cannot be normalised")

    if (
        decision == "exclude"
        or output.get("paper_role") == "not_relevant"
        or output.get("psychology_intervention_relevant") is False
    ):
        return canonical_exclusion(
            output,
            allowed_unit_ids=allowed_unit_ids,
            actions=actions,
        ), actions

    replace(
        output,
        actions,
        "psychology_intervention_relevant",
        True,
        "align_inclusion_relevance",
    )
    replace(
        output,
        actions,
        "exclusion_reason",
        "not_excluded",
        "align_inclusion_exclusion_reason",
    )

    role = str(output.get("paper_role") or "")
    if role not in base.PAPER_ROLES - {"not_relevant"}:
        raise ValueError("included record has no usable paper_role")
    if output.get("study_design") not in base.STUDY_DESIGNS:
        replace(
            output,
            actions,
            "study_design",
            "unclear",
            "default_invalid_study_design",
        )

    for field, allowed in ARRAY_FIELDS.items():
        before = output.get(field)
        after = dedupe_valid(before, allowed)
        if len(after) > 1 and "not_applicable" in after:
            after = [item for item in after if item != "not_applicable"]
        if before != after:
            replace(
                output,
                actions,
                field,
                after,
                "filter_and_deduplicate_controlled_array",
            )

    families = output.get("intervention_families") or []
    if not families:
        families = ["other"]
        replace(
            output,
            actions,
            "intervention_families",
            families,
            "default_empty_intervention_family",
        )
    if not output.get("candidate_routes"):
        replace(
            output,
            actions,
            "candidate_routes",
            [default_route(role)],
            "default_empty_candidate_route",
        )
    if not output.get("constraint_loci"):
        replace(
            output,
            actions,
            "constraint_loci",
            ["not_applicable"],
            "default_empty_constraint_locus",
        )
    if not output.get("outcome_families"):
        replace(
            output,
            actions,
            "outcome_families",
            ["not_reported"],
            "default_empty_outcome_family",
        )
    if not output.get("transfer_signals"):
        replace(
            output,
            actions,
            "transfer_signals",
            ["none_reported"],
            "default_empty_transfer_signal",
        )
    if not output.get("missing_for_fulltext"):
        replace(
            output,
            actions,
            "missing_for_fulltext",
            ["risk_of_bias_information"],
            "default_empty_fulltext_missingness",
        )

    supported_domains = [
        item
        for item in (output.get("csi_domains") or [])
        if item in domains.CSI_DOMAINS
    ]
    primary = output.get("primary_csi_domain")
    if primary in domains.CSI_DOMAINS and primary not in supported_domains:
        supported_domains.append(primary)
    if not supported_domains:
        raise ValueError("included record has no supported CSI domain")
    replace(
        output,
        actions,
        "csi_domains",
        supported_domains,
        "align_supported_domain_list",
    )

    primary = output.get("primary_csi_domain")
    if primary not in domains.PRIMARY_CSI_DOMAINS or primary == "not_applicable":
        replace(
            output,
            actions,
            "primary_csi_domain",
            supported_domains[0] if len(supported_domains) == 1 else "cross_domain",
            "derive_primary_domain_from_supported_domains",
        )
    elif primary == "cross_domain" and len(supported_domains) < 2:
        replace(
            output,
            actions,
            "primary_csi_domain",
            supported_domains[0],
            "collapse_single_domain_cross_domain_label",
        )

    health_present = "health_clinical_adjacent" in supported_domains
    if health_present and output.get("health_scope") not in {
        "health_clinical_adjacent",
        "clinical_intervention_research",
    }:
        replace(
            output,
            actions,
            "health_scope",
            "health_clinical_adjacent",
            "align_health_scope_with_health_domain",
        )
    elif not health_present and output.get("health_scope") != "non_health":
        replace(
            output,
            actions,
            "health_scope",
            "non_health",
            "align_non_health_scope",
        )

    targets = [
        item
        for item in (output.get("application_targets") or [])
        if item in domains.APPLICATION_TARGETS and item != "not_applicable"
    ]
    if not targets:
        targets = [default_application_target(supported_domains, families)]
        replace(
            output,
            actions,
            "application_targets",
            targets,
            "derive_empty_application_target",
        )
    else:
        replace(
            output,
            actions,
            "application_targets",
            targets,
            "remove_not_applicable_from_included_targets",
        )

    ids = dedupe_valid(output.get("evidence_unit_ids"), allowed_unit_ids)
    if not ids and allowed_unit_ids:
        ids = ["t000" if "t000" in allowed_unit_ids else sorted(allowed_unit_ids)[0]]
        replace(
            output,
            actions,
            "evidence_unit_ids",
            ids,
            "default_missing_evidence_reference_to_title",
        )
    else:
        replace(
            output,
            actions,
            "evidence_unit_ids",
            ids,
            "filter_and_deduplicate_evidence_ids",
        )

    for field in (
        "population_summary",
        "intervention_summary",
        "comparator_summary",
        "screening_rationale",
    ):
        if not isinstance(output.get(field), str):
            replace(
                output,
                actions,
                field,
                str(output.get(field) or ""),
                "coerce_summary_to_string",
            )

    replace(
        output,
        actions,
        "abstract_only_confidence",
        bounded_confidence(output.get("abstract_only_confidence"), 0.5),
        "bound_or_default_confidence",
    )
    if output.get("fulltext_priority") not in base.FULLTEXT_PRIORITIES - {
        "not_applicable"
    }:
        replace(
            output,
            actions,
            "fulltext_priority",
            "medium",
            "default_included_fulltext_priority",
        )

    return output, actions
