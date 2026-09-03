#!/usr/bin/env python3
"""Classify Stage 13 psychology-paper candidates with a local Ollama model.

Consumes a Europe PMC discovery manifest, classifies title/abstract evidence into
a constrained intervention-intelligence schema, checkpoints every candidate,
and writes ranked candidate outputs. The process is resumable and local-only.
It cannot create scientific authority, machine-screened status, release records,
or CSI Gateway content.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
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
PROMPT_VERSION = "stage13-psychology-abstract-triage-v1"
SCHEMA_VERSION = "stage13-psychology-abstract-classification-v1"

SCREENING_DECISIONS = {"include", "maybe", "exclude"}
PAPER_ROLES = {
    "direct_intervention",
    "evidence_synthesis",
    "mechanism",
    "measurement",
    "implementation_human_ai",
    "protocol",
    "not_relevant",
}
STUDY_DESIGNS = {
    "randomised_controlled_trial",
    "cluster_randomised_trial",
    "quasi_experimental",
    "controlled_experiment",
    "pre_post_intervention",
    "observational_longitudinal",
    "observational_cross_sectional",
    "systematic_review_meta_analysis",
    "systematic_review",
    "scoping_review",
    "qualitative_or_mixed_methods",
    "protocol",
    "other",
    "unclear",
}
INTERVENTION_FAMILIES = {
    "attention_cognitive_control",
    "working_memory_relational_binding",
    "reasoning_problem_solving",
    "metacognitive_learning_strategy",
    "self_regulation_goal_management",
    "stress_emotion_resilience",
    "digital_psychological_behavioural",
    "human_ai_cognitive_support",
    "workflow_organisational_redesign",
    "implementation_or_coupling_support",
    "other",
    "not_applicable",
}
ROUTES = {
    "develop_equip",
    "develop_train",
    "develop_condition",
    "regulate",
    "bridge",
    "redesign",
    "integrate",
    "measure_prove",
    "mechanism_only",
    "not_applicable",
}
CONSTRAINT_LOCI = {"capacity", "coupling", "niche", "mixed", "not_applicable"}
OUTCOME_FAMILIES = {
    "cognitive_performance",
    "learning_academic",
    "mental_health_wellbeing",
    "behaviour_functioning",
    "work_or_organisational_performance",
    "human_ai_performance_or_learning",
    "implementation_engagement_adherence",
    "harms_burden_tradeoffs",
    "other",
    "not_reported",
}
TRANSFER_SIGNALS = {
    "trained_task_or_practice_effect",
    "near_transfer",
    "separate_measure",
    "applied_or_functional",
    "real_world_niche",
    "delayed_followup",
    "independent_no_support_performance",
    "none_reported",
    "unclear",
}
FULLTEXT_PRIORITIES = {"high", "medium", "low", "not_applicable"}
EXCLUSION_REASONS = {
    "not_psychology_or_cognition",
    "not_intervention_relevant",
    "non_human_or_preclinical",
    "editorial_commentary_or_news",
    "duplicate_or_secondary_record",
    "insufficient_abstract_information",
    "other",
    "not_excluded",
}
MISSING_FIELDS = {
    "allocation_or_design_detail",
    "sample_and_attrition",
    "intervention_content_and_dose",
    "comparator_detail",
    "outcome_measure_detail",
    "effect_estimates",
    "followup_or_transfer",
    "adverse_events_or_burden",
    "implementation_context",
    "risk_of_bias_information",
    "none_identified",
}


def load_json(path: Path) -> dict[str, Any]:
    return discovery.load_json(path)


def write_json(path: Path, value: Any) -> None:
    discovery.write_json(path, value)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def safe_filename(candidate_id: str) -> str:
    prefix = re.sub(r"[^a-zA-Z0-9]+", "-", candidate_id).strip("-")[:48]
    return f"{prefix}-{sha256_text(candidate_id)[:12]}.json"


def evidence_units(title: str, abstract: str) -> list[dict[str, str]]:
    units = [{"unit_id": "t000", "text": title.strip()}]
    clean = re.sub(r"\s+", " ", abstract).strip()
    if not clean:
        return units
    sentences = re.split(
        r"(?<=[.!?])\s+(?=(?:[A-Z0-9]|\([A-Z0-9]))",
        clean,
    )
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    if len(sentences) == 1 and len(clean) > 1600:
        sentences = [
            clean[index : index + 1200].strip()
            for index in range(0, len(clean), 1200)
            if clean[index : index + 1200].strip()
        ]
    units.extend(
        {"unit_id": f"a{index:03d}", "text": sentence}
        for index, sentence in enumerate(sentences, start=1)
    )
    return units


def schema() -> dict[str, Any]:
    def enum(values: set[str]) -> dict[str, Any]:
        return {"type": "string", "enum": sorted(values)}

    def enum_array(values: set[str]) -> dict[str, Any]:
        return {
            "type": "array",
            "items": enum(values),
            "uniqueItems": True,
        }

    return {
        "type": "object",
        "properties": {
            "screening_decision": enum(SCREENING_DECISIONS),
            "psychology_intervention_relevant": {"type": "boolean"},
            "paper_role": enum(PAPER_ROLES),
            "study_design": enum(STUDY_DESIGNS),
            "intervention_families": enum_array(INTERVENTION_FAMILIES),
            "candidate_routes": enum_array(ROUTES),
            "constraint_loci": enum_array(CONSTRAINT_LOCI),
            "population_summary": {"type": "string"},
            "intervention_summary": {"type": "string"},
            "comparator_summary": {"type": "string"},
            "outcome_families": enum_array(OUTCOME_FAMILIES),
            "transfer_signals": enum_array(TRANSFER_SIGNALS),
            "evidence_unit_ids": {
                "type": "array",
                "items": {"type": "string"},
                "uniqueItems": True,
            },
            "abstract_only_confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },
            "fulltext_priority": enum(FULLTEXT_PRIORITIES),
            "exclusion_reason": enum(EXCLUSION_REASONS),
            "missing_for_fulltext": enum_array(MISSING_FIELDS),
            "screening_rationale": {"type": "string"},
        },
        "required": [
            "screening_decision",
            "psychology_intervention_relevant",
            "paper_role",
            "study_design",
            "intervention_families",
            "candidate_routes",
            "constraint_loci",
            "population_summary",
            "intervention_summary",
            "comparator_summary",
            "outcome_families",
            "transfer_signals",
            "evidence_unit_ids",
            "abstract_only_confidence",
            "fulltext_priority",
            "exclusion_reason",
            "missing_for_fulltext",
            "screening_rationale",
        ],
        "additionalProperties": False,
    }


def make_prompt(candidate: dict[str, Any], units: list[dict[str, str]]) -> str:
    allowed = ", ".join(unit["unit_id"] for unit in units)
    blocks = "\n\n".join(
        f"[{unit['unit_id']}] {unit['text']}" for unit in units
    )
    metadata = {
        "candidate_id": candidate.get("candidate_id"),
        "publication_year": candidate.get("publication_year"),
        "publication_types": candidate.get("publication_types") or [],
        "journal": candidate.get("journal"),
        "query_families": [
            hit.get("query_id")
            for hit in candidate.get("query_hits") or []
            if isinstance(hit, dict)
        ],
        "open_access": bool(candidate.get("is_open_access")),
    }
    return f"""Classify this title and abstract for an evidence-intelligence system that
supports psychology intervention discovery and later CSI recommendation work.

METADATA
{json.dumps(metadata, ensure_ascii=False, sort_keys=True)}

BOUNDARY RULES
- Use only the title/abstract evidence units below.
- This is abstract screening, not full-text appraisal.
- Include direct psychological/cognitive/behavioural interventions, evidence
  syntheses, intervention-relevant mechanisms or measurement papers, and
  human-AI/workflow studies that can inform intervention design.
- Exclude clearly irrelevant, non-human/preclinical, editorial or purely
  biomedical treatment papers without a psychological, cognitive, behavioural,
  learning, work-system or human-AI intervention relevance.
- A mechanism or measurement paper can be included even if it does not test an
  intervention, but label its paper_role and route accordingly.
- Candidate routes describe the likely intervention locus; they do not establish
  efficacy. Use measure_prove or mechanism_only when appropriate.
- Do not infer randomisation, effects, transfer, delay or real-world function
  unless an evidence unit states it.
- An intervention outcome is not automatically far transfer.
- screening_decision=include means clearly relevant to the intended evidence
  system. maybe means plausible but full text is needed to resolve relevance.
- Every include/maybe classification requires at least one evidence_unit_id.
- For exclude, evidence_unit_ids may identify the exclusion evidence.
- Select IDs only from this exact allowed list: {allowed}
- exclusion_reason must be not_excluded unless screening_decision=exclude.
- Return only the JSON object required by the supplied schema.

EVIDENCE UNITS
{blocks}
"""


def validate_classification(
    value: dict[str, Any],
    *,
    allowed_unit_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    expected = set(schema()["required"])
    if set(value) != expected:
        missing = expected - set(value)
        extra = set(value) - expected
        if missing:
            errors.append("missing:" + ",".join(sorted(missing)))
        if extra:
            errors.append("extra:" + ",".join(sorted(extra)))

    scalar_enums = {
        "screening_decision": SCREENING_DECISIONS,
        "paper_role": PAPER_ROLES,
        "study_design": STUDY_DESIGNS,
        "fulltext_priority": FULLTEXT_PRIORITIES,
        "exclusion_reason": EXCLUSION_REASONS,
    }
    array_enums = {
        "intervention_families": INTERVENTION_FAMILIES,
        "candidate_routes": ROUTES,
        "constraint_loci": CONSTRAINT_LOCI,
        "outcome_families": OUTCOME_FAMILIES,
        "transfer_signals": TRANSFER_SIGNALS,
        "missing_for_fulltext": MISSING_FIELDS,
    }
    for field, values in scalar_enums.items():
        if value.get(field) not in values:
            errors.append(f"{field}:invalid")
    for field, values in array_enums.items():
        items = value.get(field)
        if not isinstance(items, list) or not items:
            errors.append(f"{field}:empty_or_not_array")
        elif any(item not in values for item in items):
            errors.append(f"{field}:invalid_value")
        elif len(items) != len(set(items)):
            errors.append(f"{field}:duplicate")

    if not isinstance(value.get("psychology_intervention_relevant"), bool):
        errors.append("psychology_intervention_relevant:not_boolean")
    confidence = value.get("abstract_only_confidence")
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not 0 <= float(confidence) <= 1
    ):
        errors.append("abstract_only_confidence:invalid")
    for field in (
        "population_summary",
        "intervention_summary",
        "comparator_summary",
        "screening_rationale",
    ):
        if not isinstance(value.get(field), str):
            errors.append(f"{field}:not_string")

    ids = value.get("evidence_unit_ids")
    if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids):
        errors.append("evidence_unit_ids:invalid")
    else:
        unknown = sorted(set(ids) - allowed_unit_ids)
        if unknown:
            errors.append("evidence_unit_ids:unknown:" + ",".join(unknown))
        if value.get("screening_decision") in {"include", "maybe"} and not ids:
            errors.append("evidence_unit_ids:required_for_include_or_maybe")

    decision = value.get("screening_decision")
    exclusion = value.get("exclusion_reason")
    if decision == "exclude" and exclusion == "not_excluded":
        errors.append("exclusion_reason:required")
    if decision != "exclude" and exclusion != "not_excluded":
        errors.append("exclusion_reason:must_be_not_excluded")
    if decision == "exclude" and value.get("psychology_intervention_relevant") is True:
        errors.append("exclude_cannot_be_relevant")
    if value.get("paper_role") == "not_relevant" and decision != "exclude":
        errors.append("not_relevant_role_requires_exclude")
    return errors


def request_ollama(
    *,
    base_url: str,
    model: str,
    prompt: str,
    output_schema: dict[str, Any],
    context: int,
    timeout: int,
    temperature: float,
    seed: int,
) -> tuple[dict[str, Any], dict[str, Any], float]:
    payload = {
        "model": model,
        "stream": False,
        "think": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a conservative scientific abstract screener. "
                    "Distinguish direct evidence, mechanism, measurement and "
                    "implementation relevance. Never promote abstract evidence "
                    "to scientific authority."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "format": output_schema,
        "options": {
            "temperature": temperature,
            "seed": seed,
            "num_ctx": context,
            "num_predict": 1000,
        },
        "keep_alive": "10m",
    }
    request = urllib.request.Request(
        base_url.rstrip("/") + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read(2000).decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc
    elapsed = time.perf_counter() - started
    if not isinstance(raw, dict):
        raise RuntimeError("Ollama returned a non-object response")
    message = raw.get("message") or {}
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        raise RuntimeError("Ollama response did not contain message.content")
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Ollama content was not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("Ollama classification was not a JSON object")
    return value, raw, elapsed


def model_available(base_url: str, model: str, timeout: int) -> bool:
    request = urllib.request.Request(base_url.rstrip("/") + "/api/tags")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            value = json.load(response)
    except Exception:
        return False
    names = {
        str(item.get("name") or item.get("model") or "")
        for item in value.get("models") or []
        if isinstance(item, dict)
    }
    return model in names


def input_fingerprint(
    candidate: dict[str, Any],
    *,
    model: str,
    config_sha: str,
) -> str:
    payload = {
        "candidate_id": candidate.get("candidate_id"),
        "title": candidate.get("title"),
        "abstract_sha256": candidate.get("abstract_sha256"),
        "publication_types": candidate.get("publication_types") or [],
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "config_sha256": config_sha,
    }
    return sha256_text(canonical_json(payload))


def valid_cached_result(
    path: Path,
    *,
    fingerprint: str,
    model: str,
) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = load_json(path)
    except SystemExit:
        return None
    if (
        value.get("schema_version") != "stage13-psychology-candidate-result-v1"
        or value.get("input_fingerprint") != fingerprint
        or value.get("model") != model
        or not isinstance(value.get("classification"), dict)
    ):
        return None
    units = value.get("evidence_units") or []
    allowed = {
        str(unit.get("unit_id"))
        for unit in units
        if isinstance(unit, dict) and unit.get("unit_id")
    }
    if validate_classification(value["classification"], allowed_unit_ids=allowed):
        return None
    return value


def ranking_score(candidate: dict[str, Any], classification: dict[str, Any]) -> float:
    decision_weight = {"include": 40, "maybe": 18, "exclude": 0}
    role_weight = {
        "direct_intervention": 14,
        "evidence_synthesis": 13,
        "implementation_human_ai": 11,
        "mechanism": 8,
        "measurement": 7,
        "protocol": 3,
        "not_relevant": 0,
    }
    priority_weight = {"high": 8, "medium": 4, "low": 1, "not_applicable": 0}
    score = float(candidate.get("deterministic_relevance_score") or 0)
    score += decision_weight.get(str(classification.get("screening_decision")), 0)
    score += role_weight.get(str(classification.get("paper_role")), 0)
    score += priority_weight.get(str(classification.get("fulltext_priority")), 0)
    score += 6 * float(classification.get("abstract_only_confidence") or 0)
    score += 3 if candidate.get("is_open_access") else 0
    score += 2 if candidate.get("direct_pdf_urls") else 0
    score += min(len(classification.get("candidate_routes") or []), 2)
    score += min(len(classification.get("transfer_signals") or []), 2)
    return round(score, 6)


def write_outputs(
    *,
    output_dir: Path,
    discovery_manifest: Path,
    config_path: Path,
    model: str,
    results: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    generated_at: datetime,
    minimum_include_confidence: float,
) -> dict[str, Any]:
    ranked = sorted(
        results,
        key=lambda row: (
            -float(row["ranking_score"]),
            int(row["candidate"].get("selection_rank") or 999999),
            str(row["candidate"].get("candidate_id")),
        ),
    )
    selected = [
        row
        for row in ranked
        if row["classification"]["screening_decision"] == "include"
        and float(row["classification"]["abstract_only_confidence"])
        >= minimum_include_confidence
    ]
    maybes = [
        row
        for row in ranked
        if row["classification"]["screening_decision"] == "maybe"
    ]

    jsonl_path = output_dir / "classified-candidates.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in ranked:
            handle.write(canonical_json(row) + "\n")

    selected_path = output_dir / "selected-for-fulltext-screening.json"
    write_json(
        selected_path,
        {
            "schema_version": "stage13-selected-psychology-candidates-v1",
            "generated_at": generated_at.isoformat(),
            "source_discovery_manifest": str(discovery_manifest),
            "model": model,
            "minimum_include_confidence": minimum_include_confidence,
            "selected": selected,
            "maybe": maybes,
            "governance": {
                "abstract_screening_only": True,
                "creates_scientific_authority": False,
                "creates_machine_screened_status": False,
            },
        },
    )

    csv_path = output_dir / "ranked-candidates.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "rank",
            "candidate_id",
            "title",
            "year",
            "journal",
            "doi",
            "pmid",
            "open_access",
            "direct_pdf",
            "screening_decision",
            "paper_role",
            "study_design",
            "fulltext_priority",
            "confidence",
            "ranking_score",
            "intervention_families",
            "candidate_routes",
            "constraint_loci",
            "transfer_signals",
            "rationale",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, row in enumerate(ranked, start=1):
            candidate = row["candidate"]
            classification = row["classification"]
            writer.writerow(
                {
                    "rank": rank,
                    "candidate_id": candidate.get("candidate_id"),
                    "title": candidate.get("title"),
                    "year": candidate.get("publication_year"),
                    "journal": candidate.get("journal"),
                    "doi": candidate.get("doi"),
                    "pmid": candidate.get("pmid"),
                    "open_access": int(bool(candidate.get("is_open_access"))),
                    "direct_pdf": int(bool(candidate.get("direct_pdf_urls"))),
                    "screening_decision": classification.get("screening_decision"),
                    "paper_role": classification.get("paper_role"),
                    "study_design": classification.get("study_design"),
                    "fulltext_priority": classification.get("fulltext_priority"),
                    "confidence": classification.get("abstract_only_confidence"),
                    "ranking_score": row["ranking_score"],
                    "intervention_families": ";".join(
                        classification.get("intervention_families") or []
                    ),
                    "candidate_routes": ";".join(
                        classification.get("candidate_routes") or []
                    ),
                    "constraint_loci": ";".join(
                        classification.get("constraint_loci") or []
                    ),
                    "transfer_signals": ";".join(
                        classification.get("transfer_signals") or []
                    ),
                    "rationale": classification.get("screening_rationale"),
                }
            )

    decisions = {
        decision: sum(
            1
            for row in results
            if row["classification"]["screening_decision"] == decision
        )
        for decision in sorted(SCREENING_DECISIONS)
    }
    roles = {
        role: sum(
            1
            for row in results
            if row["classification"]["paper_role"] == role
        )
        for role in sorted(PAPER_ROLES)
    }
    summary = {
        "schema_version": "stage13-psychology-classification-summary-v1",
        "generated_at": generated_at.isoformat(),
        "discovery_manifest": str(discovery_manifest),
        "config_path": str(config_path),
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "classification_schema_version": SCHEMA_VERSION,
        "summary": {
            "classified": len(results),
            "failures": len(failures),
            "decisions": decisions,
            "paper_roles": roles,
            "selected_for_fulltext_screening": len(selected),
            "maybe_for_fulltext_screening": len(maybes),
            "open_access_selected": sum(
                1 for row in selected if row["candidate"].get("is_open_access")
            ),
            "direct_pdf_selected": sum(
                1 for row in selected if row["candidate"].get("direct_pdf_urls")
            ),
        },
        "failures": failures,
        "outputs": {
            "classified_jsonl": str(jsonl_path),
            "selected_json": str(selected_path),
            "ranked_csv": str(csv_path),
        },
        "governance": {
            "abstract_screening_only": True,
            "registry_mutated": False,
            "scientific_state_mutated": False,
            "historical_release_mutated": False,
            "csi_gateway_mutated": False,
            "machine_screened_status_created": False,
            "human_authority_created": False,
        },
    }
    write_json(output_dir / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify psychology-paper candidates with local Ollama."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--model")
    parser.add_argument("--max-items", type=int)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    manifest_path = args.manifest.expanduser().resolve()
    config_path = args.config.expanduser().resolve()
    manifest = load_json(manifest_path)
    config = load_json(config_path)
    if manifest.get("schema_version") != "stage13-psychology-candidate-discovery-v1":
        raise SystemExit("Unsupported discovery-manifest schema")
    if config.get("schema_version") != "stage13-overnight-psychology-search-v1":
        raise SystemExit("Unsupported classification configuration schema")

    classification_config = config.get("classification") or {}
    model = str(args.model or classification_config.get("model") or "qwen3.5:4b")
    context = int(classification_config.get("context", 8192))
    timeout = int(args.timeout or classification_config.get("timeout_seconds", 900))
    temperature = float(classification_config.get("temperature", 0))
    seed = int(classification_config.get("seed", 42))
    minimum_include_confidence = float(
        classification_config.get("minimum_include_confidence", 0.6)
    )
    maximum_abstract_characters = int(
        classification_config.get("maximum_abstract_characters", 12000)
    )
    candidates = [
        row for row in manifest.get("candidates") or [] if isinstance(row, dict)
    ]
    limit = int(
        args.max_items
        or config.get("classification_target")
        or len(candidates)
    )
    if limit < 1:
        raise SystemExit("--max-items must be positive")
    candidates = candidates[:limit]
    if not candidates:
        raise SystemExit("Discovery manifest has no candidates")
    if not model_available(args.ollama_url, model, min(timeout, 30)):
        raise SystemExit(
            f"Ollama model {model!r} is not available at {args.ollama_url}"
        )

    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else manifest_path.parent / "classification"
    )
    items_dir = output_dir / "items"
    items_dir.mkdir(parents=True, exist_ok=True)
    config_sha = sha256_text(canonical_json(config))
    output_schema = schema()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    ollama_calls = 0
    reused = 0

    print("=== STAGE 13 PSYCHOLOGY ABSTRACT CLASSIFICATION ===")
    print(f"manifest|{manifest_path}")
    print(f"model|{model}")
    print(f"candidates_selected|{len(candidates)}")
    print(f"output_dir|{output_dir}")
    print("mode|LOCAL_RESUMABLE_ABSTRACT_SCREENING")

    for index, candidate in enumerate(candidates, start=1):
        candidate_id = str(candidate.get("candidate_id") or f"candidate-{index}")
        title = str(candidate.get("title") or "").strip()
        abstract = str(candidate.get("abstract") or "").strip()[
            :maximum_abstract_characters
        ]
        units = evidence_units(title, abstract)
        allowed = {unit["unit_id"] for unit in units}
        prompt = make_prompt(candidate, units)
        fingerprint = input_fingerprint(
            candidate,
            model=model,
            config_sha=config_sha,
        )
        item_path = items_dir / safe_filename(candidate_id)
        cached = None if args.force else valid_cached_result(
            item_path,
            fingerprint=fingerprint,
            model=model,
        )
        if cached is not None:
            reused += 1
            result = cached
            results.append(result)
            classification = result["classification"]
            print(
                f"candidate_reused|{index}/{len(candidates)}|{candidate_id}|"
                f"decision={classification['screening_decision']}|"
                f"role={classification['paper_role']}"
            )
            continue

        print(
            f"candidate_start|{index}/{len(candidates)}|{candidate_id}|"
            f"title={json.dumps(title[:120])}",
            flush=True,
        )
        attempt_errors: list[str] = []
        classification: dict[str, Any] | None = None
        raw: dict[str, Any] | None = None
        elapsed = 0.0
        for attempt in range(1, args.retries + 2):
            try:
                classification, raw, elapsed = request_ollama(
                    base_url=args.ollama_url,
                    model=model,
                    prompt=prompt,
                    output_schema=output_schema,
                    context=context,
                    timeout=timeout,
                    temperature=temperature,
                    seed=seed,
                )
                ollama_calls += 1
                errors = validate_classification(
                    classification,
                    allowed_unit_ids=allowed,
                )
                if errors:
                    raise RuntimeError(";".join(errors))
                break
            except Exception as exc:
                attempt_errors.append(f"attempt_{attempt}:{exc}")
                classification = None
                if attempt <= args.retries:
                    time.sleep(min(2 ** (attempt - 1), 5))
        if classification is None or raw is None:
            failures.append(
                {
                    "candidate_id": candidate_id,
                    "title": title,
                    "errors": attempt_errors,
                }
            )
            print(
                f"candidate_failed|{index}/{len(candidates)}|{candidate_id}|"
                f"errors={len(attempt_errors)}"
            )
            continue

        score = ranking_score(candidate, classification)
        raw_prompt_seconds = float(raw.get("prompt_eval_duration") or 0) / 1e9
        raw_output_seconds = float(raw.get("eval_duration") or 0) / 1e9
        result = {
            "schema_version": "stage13-psychology-candidate-result-v1",
            "candidate_id": candidate_id,
            "model": model,
            "prompt_version": PROMPT_VERSION,
            "classification_schema_version": SCHEMA_VERSION,
            "input_fingerprint": fingerprint,
            "candidate": candidate,
            "evidence_units": units,
            "classification": classification,
            "ranking_score": score,
            "performance": {
                "wall_seconds": elapsed,
                "prompt_tokens": int(raw.get("prompt_eval_count") or 0),
                "prompt_tokens_per_second": (
                    int(raw.get("prompt_eval_count") or 0) / raw_prompt_seconds
                    if raw_prompt_seconds
                    else 0
                ),
                "output_tokens": int(raw.get("eval_count") or 0),
                "output_tokens_per_second": (
                    int(raw.get("eval_count") or 0) / raw_output_seconds
                    if raw_output_seconds
                    else 0
                ),
                "attempts": len(attempt_errors) + 1,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "governance": {
                "abstract_screening_only": True,
                "registry_mutated": False,
                "scientific_state_mutated": False,
                "historical_release_mutated": False,
                "csi_gateway_mutated": False,
                "machine_screened_status_created": False,
                "human_authority_created": False,
            },
        }
        write_json(item_path, result)
        results.append(result)
        print(
            f"candidate_classified|{index}/{len(candidates)}|{candidate_id}|"
            f"decision={classification['screening_decision']}|"
            f"role={classification['paper_role']}|"
            f"priority={classification['fulltext_priority']}|"
            f"confidence={float(classification['abstract_only_confidence']):.2f}|"
            f"seconds={elapsed:.2f}"
        )

    generated_at = datetime.now(timezone.utc)
    summary = write_outputs(
        output_dir=output_dir,
        discovery_manifest=manifest_path,
        config_path=config_path,
        model=model,
        results=results,
        failures=failures,
        generated_at=generated_at,
        minimum_include_confidence=minimum_include_confidence,
    )
    counts = summary["summary"]
    print(f"classified_candidates|{counts['classified']}")
    print(f"classification_failures|{counts['failures']}")
    print(f"cached_results_reused|{reused}")
    print(f"ollama_calls|{ollama_calls}")
    for decision, count in sorted(counts["decisions"].items()):
        print(f"screening_decision|{decision}|{count}")
    print(
        "selected_for_fulltext_screening|"
        f"{counts['selected_for_fulltext_screening']}"
    )
    print(
        "maybe_for_fulltext_screening|"
        f"{counts['maybe_for_fulltext_screening']}"
    )
    print(f"summary_path|{output_dir / 'summary.json'}")
    print(f"ranked_csv|{output_dir / 'ranked-candidates.csv'}")
    print(
        "selected_manifest|"
        f"{output_dir / 'selected-for-fulltext-screening.json'}"
    )
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print("MACHINE_SCREENED_STATUS_CREATED|0")
    print("HUMAN_AUTHORITY_CREATED|0")

    if results and not failures:
        status = "PASS"
        exit_code = 0
    elif results:
        status = "PARTIAL"
        exit_code = 2
    else:
        status = "FAIL"
        exit_code = 1
    print(f"STAGE 13 PSYCHOLOGY ABSTRACT CLASSIFICATION|{status}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
