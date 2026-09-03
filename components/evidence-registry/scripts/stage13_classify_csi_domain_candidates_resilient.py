#!/usr/bin/env python3
"""Resilient entry point for Stage 13 three-domain abstract screening.

This wrapper preserves the established classifier/output contract while adding:

- explicit non-empty-array constraints to the Ollama JSON schema;
- clearer exclusion and inclusion consistency instructions;
- conservative normalisation before validation;
- side-by-side preservation of raw and normalised model output;
- a version bump so earlier cached results cannot be confused with this run.

It is a calibration-stage compatibility layer. It creates no Registry,
scientific, release, Gateway, machine-screened or human-authority state.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import stage13_classify_csi_domain_candidates as classifier
import stage13_normalise_csi_abstract_classification as normaliser

classifier.PROMPT_VERSION = "stage13-three-csi-domain-abstract-triage-v3"
classifier.SCHEMA_VERSION = "stage13-three-csi-domain-abstract-classification-v3"
classifier.RESULT_SCHEMA_VERSION = "stage13-three-csi-domain-candidate-result-v3"

_original_schema = classifier.extended_schema
_original_prompt = classifier.make_prompt
_original_validate = classifier.validate_classification
_original_write_json = classifier.write_json
_original_write_outputs = classifier.write_outputs

# Object identity remains stable from validation through result assembly in the
# established classifier loop. This records provenance without adding
# unregistered fields inside the constrained classification object.
_normalisation_by_object_id: dict[int, dict[str, Any]] = {}


def resilient_schema() -> dict[str, Any]:
    schema = copy.deepcopy(_original_schema())
    for field in (
        "intervention_families",
        "candidate_routes",
        "constraint_loci",
        "outcome_families",
        "transfer_signals",
        "missing_for_fulltext",
        "csi_domains",
        "application_targets",
    ):
        property_schema = schema.get("properties", {}).get(field)
        if isinstance(property_schema, dict):
            property_schema["minItems"] = 1
            property_schema["uniqueItems"] = True
    return schema


def resilient_prompt(
    candidate: dict[str, Any],
    units: list[dict[str, str]],
    *,
    query_domains: list[str],
) -> str:
    prompt = _original_prompt(
        candidate,
        units,
        query_domains=query_domains,
    )
    return prompt + """

STRICT OUTPUT CONSISTENCY ADDENDUM
- Every controlled array must contain at least one value and no duplicates.
- Never return an empty array.
- If screening_decision=exclude, use:
  intervention_families=[not_applicable];
  candidate_routes=[not_applicable];
  constraint_loci=[not_applicable];
  outcome_families=[not_reported];
  transfer_signals=[none_reported];
  missing_for_fulltext=[none_identified];
  primary_csi_domain=not_applicable;
  csi_domains=[not_applicable];
  application_targets=[not_applicable];
  health_scope=not_applicable;
  and choose a specific exclusion_reason other than not_excluded.
- If screening_decision is include or maybe, set exclusion_reason=not_excluded,
  do not mix not_applicable into csi_domains/application_targets, and make
  health_scope agree with whether health_clinical_adjacent is assigned.
- Health/clinical-adjacent means psychology-related health support. A medical
  population, occupational therapy service, physical rehabilitation, general
  disease management, adherence outcome, functioning outcome or quality-of-life
  outcome is not enough without an explicit central psychological, cognitive,
  behavioural, motivational, self-regulatory, psychosocial or
  neuropsychological intervention component.
- Return only the schema-conforming JSON object.
"""


def resilient_validate(
    value: dict[str, Any],
    *,
    allowed_unit_ids: set[str],
) -> list[str]:
    raw_value = copy.deepcopy(value)
    normalised, actions = normaliser.normalise_classification(
        value,
        allowed_unit_ids=allowed_unit_ids,
    )
    value.clear()
    value.update(normalised)
    _normalisation_by_object_id[id(value)] = {
        "version": normaliser.NORMALISATION_VERSION,
        "applied": bool(actions),
        "actions": actions,
        "raw": raw_value,
    }
    return _original_validate(value, allowed_unit_ids=allowed_unit_ids)


def resilient_write_json(path: Path, value: Any) -> None:
    if (
        isinstance(value, dict)
        and value.get("schema_version") == classifier.RESULT_SCHEMA_VERSION
        and isinstance(value.get("classification"), dict)
    ):
        record = _normalisation_by_object_id.get(id(value["classification"]))
        if record:
            value.setdefault("classification_raw", record["raw"])
            value.setdefault(
                "classification_normalisation",
                {
                    "version": record["version"],
                    "applied": record["applied"],
                    "actions": record["actions"],
                },
            )
            value.setdefault("normalisation_version", record["version"])
            governance = value.setdefault("governance", {})
            if isinstance(governance, dict):
                governance["raw_model_output_preserved"] = True
                governance["normalisation_actions_recorded"] = True
    _original_write_json(path, value)


def resilient_write_outputs(*args: Any, **kwargs: Any) -> dict[str, Any]:
    summary = _original_write_outputs(*args, **kwargs)
    results = kwargs.get("results")
    output_dir = kwargs.get("output_dir")
    if not isinstance(results, list):
        results = []

    counts = summary.setdefault("summary", {})
    counts["normalised_candidates"] = sum(
        1
        for row in results
        if (row.get("classification_normalisation") or {}).get("actions")
    )
    counts["normalisation_actions"] = sum(
        len((row.get("classification_normalisation") or {}).get("actions") or [])
        for row in results
    )

    # An empty or all-excluded set cannot satisfy a meaningful domain gate even
    # when scaled numerical minima happen to be zero.
    if not results or int(counts.get("portfolio_selected") or 0) == 0:
        counts["domain_gate_pass"] = False

    summary["schema_version"] = (
        "stage13-three-csi-domain-classification-summary-v2"
    )
    summary["normalisation_version"] = normaliser.NORMALISATION_VERSION
    governance = summary.setdefault("governance", {})
    if isinstance(governance, dict):
        governance["raw_model_output_preserved"] = True
        governance["normalisation_actions_recorded"] = True

    if isinstance(output_dir, Path):
        portfolio_path = output_dir / "domain-balanced-fulltext-portfolio.json"
        if portfolio_path.is_file() and not counts.get("domain_gate_pass"):
            portfolio = classifier.load_json(portfolio_path)
            portfolio["domain_gate_pass"] = False
            _original_write_json(portfolio_path, portfolio)
        _original_write_json(output_dir / "summary.json", summary)
    return summary


classifier.extended_schema = resilient_schema
classifier.make_prompt = resilient_prompt
classifier.validate_classification = resilient_validate
classifier.write_json = resilient_write_json
classifier.write_outputs = resilient_write_outputs


if __name__ == "__main__":
    raise SystemExit(classifier.main())
