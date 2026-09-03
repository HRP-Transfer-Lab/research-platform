#!/usr/bin/env python3
"""Classify psychology candidates across the three CSI intervention domains.

This is the domain-aware Stage 13 abstract-screening layer. It reuses the local
Ollama transport and core intervention schema from
``stage13_classify_psychology_candidates`` while adding explicit classification
for:

- performance, work motivation and workplace wellbeing;
- personal adaptive cognition and wellbeing; and
- health-related / clinical-adjacent support.

Every candidate is checkpointed. Outputs are abstract-screening candidates only:
no Registry, scientific, release, Gateway, machine-screened or human-authority
state is created.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import stage13_classify_psychology_candidates as base

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = (
    REPO_ROOT
    / "components/evidence-registry/config/"
    / "stage13_overnight_psychology_search.v1.json"
)
PROMPT_VERSION = "stage13-three-csi-domain-abstract-triage-v2"
SCHEMA_VERSION = "stage13-three-csi-domain-abstract-classification-v2"
RESULT_SCHEMA_VERSION = "stage13-three-csi-domain-candidate-result-v2"

CSI_DOMAINS = {
    "performance_work",
    "personal",
    "health_clinical_adjacent",
}
PRIMARY_CSI_DOMAINS = CSI_DOMAINS | {"cross_domain", "not_applicable"}
APPLICATION_TARGETS = {
    "work_cognitive_performance",
    "work_motivation_engagement",
    "work_wellbeing_resilience",
    "work_human_ai_and_workflow",
    "personal_cognitive_performance",
    "personal_learning_and_study",
    "personal_reasoning_and_decision",
    "personal_self_regulation_and_habits",
    "personal_wellbeing_and_resilience",
    "personal_cognitive_ageing",
    "health_symptom_self_management",
    "health_functional_outcomes",
    "health_adherence_and_participation",
    "health_cognitive_rehabilitation",
    "clinical_adjacent_cognitive_affective_support",
    "other",
    "not_applicable",
}
HEALTH_SCOPES = {
    "non_health",
    "health_clinical_adjacent",
    "clinical_intervention_research",
    "not_applicable",
}


def load_json(path: Path) -> dict[str, Any]:
    return base.load_json(path)


def write_json(path: Path, value: Any) -> None:
    base.write_json(path, value)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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


def query_origin_domains(
    candidate: dict[str, Any], mapping: dict[str, str]
) -> list[str]:
    domains = {
        mapping[str(hit.get("query_id"))]
        for hit in candidate.get("query_hits") or []
        if isinstance(hit, dict) and str(hit.get("query_id")) in mapping
    }
    return sorted(domains)


def extended_schema() -> dict[str, Any]:
    schema = json.loads(json.dumps(base.schema()))

    def enum(values: set[str]) -> dict[str, Any]:
        return {"type": "string", "enum": sorted(values)}

    def enum_array(values: set[str]) -> dict[str, Any]:
        return {
            "type": "array",
            "items": enum(values),
            "uniqueItems": True,
        }

    schema["properties"].update(
        {
            "primary_csi_domain": enum(PRIMARY_CSI_DOMAINS),
            "csi_domains": enum_array(CSI_DOMAINS | {"not_applicable"}),
            "application_targets": enum_array(APPLICATION_TARGETS),
            "health_scope": enum(HEALTH_SCOPES),
        }
    )
    schema["required"].extend(
        [
            "primary_csi_domain",
            "csi_domains",
            "application_targets",
            "health_scope",
        ]
    )
    return schema


def make_prompt(
    candidate: dict[str, Any],
    units: list[dict[str, str]],
    *,
    query_domains: list[str],
) -> str:
    allowed = ", ".join(unit["unit_id"] for unit in units)
    blocks = "\n\n".join(
        f"[{unit['unit_id']}] {unit['text']}" for unit in units
    )
    metadata = {
        "candidate_id": candidate.get("candidate_id"),
        "publication_year": candidate.get("publication_year"),
        "publication_types": candidate.get("publication_types") or [],
        "journal": candidate.get("journal"),
        "query_origin_domains": query_domains,
        "query_families": [
            hit.get("query_id")
            for hit in candidate.get("query_hits") or []
            if isinstance(hit, dict)
        ],
        "open_access": bool(candidate.get("is_open_access")),
    }
    return f"""Classify this title and abstract for an evidence-intelligence system
supporting three related but distinct CSI domains.

CSI DOMAIN DEFINITIONS

performance_work
- work and professional cognitive performance;
- motivation, engagement, autonomy and participation;
- workplace wellbeing, resilience, stress and recovery;
- workload, interruption, workflow, decision systems and human-AI activity.

personal
- self-directed cognitive performance and cognitive ageing;
- learning, study, reasoning and decision-making;
- habits, self-regulation, goal management and everyday functioning;
- non-clinical personal wellbeing and resilience.

health_clinical_adjacent
- psychological, cognitive, behavioural, rehabilitative or digital support in
  health-related populations or pathways;
- symptom self-management, functioning, adherence, participation and quality of
  life;
- clinical-adjacent evidence that may inform governed health interventions.

A paper may fit more than one domain. Use cross_domain as the primary domain
when relevance is genuinely distributed across domains; otherwise choose the
strongest primary domain and list every supported domain in csi_domains.

METADATA
{json.dumps(metadata, ensure_ascii=False, sort_keys=True)}

BOUNDARY RULES
- Use only the title/abstract evidence units below.
- Query origin is a retrieval hint, not proof of domain fit.
- This is abstract screening, not full-text appraisal.
- Include direct psychological, cognitive or behavioural interventions;
  relevant evidence syntheses; intervention-relevant mechanisms or measurement
  papers; and human-AI/workflow studies that can inform intervention design.
- Health inclusion requires a psychological, cognitive, behavioural,
  rehabilitative, self-management, adherence, functioning or digital-support
  component. Exclude drug-, surgery- or device-only treatment evidence unless a
  psychologically or cognitively meaningful intervention component is evaluated.
- Work-domain inclusion may concern performance, motivation/engagement,
  wellbeing/recovery, workflow or human-AI work; it need not be cognitive
  training.
- Personal-domain inclusion may concern learning, reasoning, self-regulation,
  habits, resilience, personal wellbeing or cognitive ageing.
- A mechanism or measurement paper can be included without testing an
  intervention, but label its paper_role and candidate route accordingly.
- Candidate routes describe plausible intervention relevance; they do not
  establish efficacy. Use measure_prove or mechanism_only where appropriate.
- Do not infer randomisation, effects, transfer, delay, clinical effectiveness or
  real-world function unless an evidence unit states it.
- An intervention outcome is not automatically far transfer.
- clinical_intervention_research means the study evaluates an intervention in a
  clinical population or service. It does not authorise a clinical claim.
- Every include/maybe classification requires at least one evidence_unit_id.
- Select evidence IDs only from this exact list: {allowed}
- For excluded records, primary_csi_domain and csi_domains must be
  not_applicable, application_targets must contain only not_applicable, and
  health_scope must be not_applicable.
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
    expected = set(extended_schema()["required"])
    actual = set(value)
    if actual != expected:
        if expected - actual:
            errors.append("missing:" + ",".join(sorted(expected - actual)))
        if actual - expected:
            errors.append("extra:" + ",".join(sorted(actual - expected)))

    base_required = set(base.schema()["required"])
    base_value = {key: value.get(key) for key in base_required}
    errors.extend(
        base.validate_classification(
            base_value,
            allowed_unit_ids=allowed_unit_ids,
        )
    )

    primary = value.get("primary_csi_domain")
    domains = value.get("csi_domains")
    targets = value.get("application_targets")
    health_scope = value.get("health_scope")
    decision = value.get("screening_decision")

    if primary not in PRIMARY_CSI_DOMAINS:
        errors.append("primary_csi_domain:invalid")
    if (
        not isinstance(domains, list)
        or not domains
        or any(item not in CSI_DOMAINS | {"not_applicable"} for item in domains)
        or len(domains) != len(set(domains))
    ):
        errors.append("csi_domains:invalid")
    if (
        not isinstance(targets, list)
        or not targets
        or any(item not in APPLICATION_TARGETS for item in targets)
        or len(targets) != len(set(targets))
    ):
        errors.append("application_targets:invalid")
    if health_scope not in HEALTH_SCOPES:
        errors.append("health_scope:invalid")

    if decision == "exclude":
        if primary != "not_applicable":
            errors.append("excluded_primary_domain_must_be_not_applicable")
        if domains != ["not_applicable"]:
            errors.append("excluded_domains_must_be_not_applicable")
        if targets != ["not_applicable"]:
            errors.append("excluded_targets_must_be_not_applicable")
        if health_scope != "not_applicable":
            errors.append("excluded_health_scope_must_be_not_applicable")
    else:
        if primary == "not_applicable":
            errors.append("included_primary_domain_cannot_be_not_applicable")
        if "not_applicable" in (domains or []):
            errors.append("included_domains_cannot_contain_not_applicable")
        if "not_applicable" in (targets or []):
            errors.append("included_targets_cannot_contain_not_applicable")
        supported_domains = set(domains or []) & CSI_DOMAINS
        if not supported_domains:
            errors.append("included_record_requires_csi_domain")
        if primary in CSI_DOMAINS and primary not in supported_domains:
            errors.append("primary_domain_missing_from_csi_domains")
        if primary == "cross_domain" and len(supported_domains) < 2:
            errors.append("cross_domain_requires_multiple_domains")
        if "health_clinical_adjacent" in supported_domains and health_scope not in {
            "health_clinical_adjacent",
            "clinical_intervention_research",
        }:
            errors.append("health_domain_requires_health_scope")
        if "health_clinical_adjacent" not in supported_domains and health_scope not in {
            "non_health",
        }:
            errors.append("non_health_domain_requires_non_health_scope")
    return sorted(set(errors))


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
        value.get("schema_version") != RESULT_SCHEMA_VERSION
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
    score = base.ranking_score(candidate, classification)
    domains = [
        item for item in classification.get("csi_domains") or [] if item in CSI_DOMAINS
    ]
    targets = [
        item
        for item in classification.get("application_targets") or []
        if item != "not_applicable"
    ]
    score += min(len(domains), 3) * 1.5
    score += min(len(targets), 3) * 0.5
    return round(score, 6)


def scaled_minimums(
    configured: dict[str, Any],
    *,
    classified_count: int,
    configured_classification_target: int,
) -> dict[str, int]:
    if classified_count <= 0:
        return {domain: 0 for domain in sorted(CSI_DOMAINS)}
    scale = min(1.0, classified_count / max(configured_classification_target, 1))
    output: dict[str, int] = {}
    for domain in sorted(CSI_DOMAINS):
        configured_value = int(configured.get(domain, 0))
        output[domain] = max(1, round(configured_value * scale))
    return output


def balanced_domain_portfolio(
    rows: list[dict[str, Any]],
    *,
    target: int,
    minimums: dict[str, int],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    eligible = [
        row
        for row in sorted(
            rows,
            key=lambda item: (
                -float(item["ranking_score"]),
                str(item["candidate"].get("candidate_id")),
            ),
        )
        if row["classification"]["screening_decision"] in {"include", "maybe"}
    ]
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    assigned: Counter[str] = Counter()

    for domain in ("performance_work", "personal", "health_clinical_adjacent"):
        for row in eligible:
            if assigned[domain] >= int(minimums.get(domain, 0)):
                break
            candidate_id = str(row["candidate"].get("candidate_id"))
            if candidate_id in selected_ids:
                continue
            if domain not in row["classification"].get("csi_domains", []):
                continue
            copy = json.loads(json.dumps(row))
            copy["assigned_portfolio_domain"] = domain
            selected.append(copy)
            selected_ids.add(candidate_id)
            assigned[domain] += 1

    domain_order = ["performance_work", "personal", "health_clinical_adjacent"]
    while len(selected) < target:
        made_progress = False
        domain_order.sort(key=lambda domain: (assigned[domain], domain))
        for domain in domain_order:
            for row in eligible:
                candidate_id = str(row["candidate"].get("candidate_id"))
                if candidate_id in selected_ids:
                    continue
                if domain not in row["classification"].get("csi_domains", []):
                    continue
                copy = json.loads(json.dumps(row))
                copy["assigned_portfolio_domain"] = domain
                selected.append(copy)
                selected_ids.add(candidate_id)
                assigned[domain] += 1
                made_progress = True
                break
            if len(selected) >= target:
                break
        if not made_progress:
            break

    for row in eligible:
        if len(selected) >= target:
            break
        candidate_id = str(row["candidate"].get("candidate_id"))
        if candidate_id in selected_ids:
            continue
        domains = [
            domain
            for domain in row["classification"].get("csi_domains", [])
            if domain in CSI_DOMAINS
        ]
        domain = min(domains, key=lambda item: assigned[item]) if domains else "personal"
        copy = json.loads(json.dumps(row))
        copy["assigned_portfolio_domain"] = domain
        selected.append(copy)
        selected_ids.add(candidate_id)
        assigned[domain] += 1

    return selected, {domain: assigned[domain] for domain in sorted(CSI_DOMAINS)}


def write_outputs(
    *,
    output_dir: Path,
    discovery_manifest: Path,
    config_path: Path,
    config: dict[str, Any],
    model: str,
    results: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    generated_at: datetime,
) -> dict[str, Any]:
    ranked = sorted(
        results,
        key=lambda row: (
            -float(row["ranking_score"]),
            int(row["candidate"].get("selection_rank") or 999999),
            str(row["candidate"].get("candidate_id")),
        ),
    )
    jsonl_path = output_dir / "classified-candidates.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in ranked:
            handle.write(canonical_json(row) + "\n")

    configured_target = int(config.get("classification_target") or len(ranked) or 1)
    configured_minimums = config.get("domain_shortlist_minimums") or {}
    effective_minimums = scaled_minimums(
        configured_minimums,
        classified_count=len(ranked),
        configured_classification_target=configured_target,
    )
    configured_shortlist = int(config.get("domain_shortlist_target") or len(ranked))
    effective_target = min(
        configured_shortlist,
        max(3, round(configured_shortlist * min(1.0, len(ranked) / configured_target))),
        len(ranked),
    )
    portfolio, assigned_counts = balanced_domain_portfolio(
        ranked,
        target=effective_target,
        minimums=effective_minimums,
    )
    domain_gate_pass = all(
        assigned_counts.get(domain, 0) >= minimum
        for domain, minimum in effective_minimums.items()
    )

    portfolio_path = output_dir / "domain-balanced-fulltext-portfolio.json"
    write_json(
        portfolio_path,
        {
            "schema_version": "stage13-three-csi-domain-portfolio-v1",
            "generated_at": generated_at.isoformat(),
            "source_discovery_manifest": str(discovery_manifest),
            "model": model,
            "target": effective_target,
            "effective_minimums": effective_minimums,
            "assigned_counts": assigned_counts,
            "domain_gate_pass": domain_gate_pass,
            "candidates": portfolio,
            "governance": {
                "abstract_screening_only": True,
                "creates_scientific_authority": False,
                "creates_machine_screened_status": False,
            },
        },
    )

    csv_path = output_dir / "ranked-candidates.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "rank",
            "candidate_id",
            "title",
            "year",
            "journal",
            "doi",
            "pmid",
            "open_access",
            "direct_pdf",
            "query_origin_domains",
            "screening_decision",
            "paper_role",
            "study_design",
            "primary_csi_domain",
            "csi_domains",
            "application_targets",
            "health_scope",
            "fulltext_priority",
            "confidence",
            "ranking_score",
            "intervention_families",
            "candidate_routes",
            "constraint_loci",
            "transfer_signals",
            "rationale",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
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
                    "query_origin_domains": ";".join(row.get("query_origin_domains") or []),
                    "screening_decision": classification.get("screening_decision"),
                    "paper_role": classification.get("paper_role"),
                    "study_design": classification.get("study_design"),
                    "primary_csi_domain": classification.get("primary_csi_domain"),
                    "csi_domains": ";".join(classification.get("csi_domains") or []),
                    "application_targets": ";".join(
                        classification.get("application_targets") or []
                    ),
                    "health_scope": classification.get("health_scope"),
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

    decisions = Counter(
        row["classification"]["screening_decision"] for row in results
    )
    primary_domains = Counter(
        row["classification"]["primary_csi_domain"] for row in results
    )
    semantic_domain_counts = {
        domain: sum(
            1
            for row in results
            if domain in row["classification"].get("csi_domains", [])
        )
        for domain in sorted(CSI_DOMAINS)
    }
    summary = {
        "schema_version": "stage13-three-csi-domain-classification-summary-v1",
        "generated_at": generated_at.isoformat(),
        "discovery_manifest": str(discovery_manifest),
        "config_path": str(config_path),
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "classification_schema_version": SCHEMA_VERSION,
        "summary": {
            "classified": len(results),
            "failures": len(failures),
            "decisions": dict(sorted(decisions.items())),
            "primary_csi_domains": dict(sorted(primary_domains.items())),
            "semantic_domain_counts": semantic_domain_counts,
            "portfolio_target": effective_target,
            "portfolio_selected": len(portfolio),
            "portfolio_assigned_counts": assigned_counts,
            "portfolio_effective_minimums": effective_minimums,
            "domain_gate_pass": domain_gate_pass,
        },
        "failures": failures,
        "outputs": {
            "classified_jsonl": str(jsonl_path),
            "ranked_csv": str(csv_path),
            "domain_balanced_portfolio": str(portfolio_path),
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
        description="Classify candidates across three CSI intervention domains."
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

    mapping = query_domain_map(config)
    if set(mapping.values()) != CSI_DOMAINS:
        raise SystemExit("Search configuration must cover all three CSI domains")
    classification_config = config.get("classification") or {}
    model = str(args.model or classification_config.get("model") or "qwen3.5:4b")
    context = int(classification_config.get("context", 8192))
    timeout = int(args.timeout or classification_config.get("timeout_seconds", 900))
    temperature = float(classification_config.get("temperature", 0))
    seed = int(classification_config.get("seed", 42))
    maximum_abstract_characters = int(
        classification_config.get("maximum_abstract_characters", 12000)
    )
    candidates = [
        row for row in manifest.get("candidates") or [] if isinstance(row, dict)
    ]
    limit = int(args.max_items or config.get("classification_target") or len(candidates))
    if limit < 1:
        raise SystemExit("--max-items must be positive")
    candidates = candidates[:limit]
    if not candidates:
        raise SystemExit("Discovery manifest has no candidates")
    if not base.model_available(args.ollama_url, model, min(timeout, 30)):
        raise SystemExit(
            f"Ollama model {model!r} is not available at {args.ollama_url}"
        )

    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else manifest_path.parent / "classification-three-domains"
    )
    items_dir = output_dir / "items"
    items_dir.mkdir(parents=True, exist_ok=True)
    config_sha = sha256_text(canonical_json(config))
    output_schema = extended_schema()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    ollama_calls = 0
    reused = 0

    print("=== STAGE 13 THREE-DOMAIN PSYCHOLOGY ABSTRACT CLASSIFICATION ===")
    print(f"manifest|{manifest_path}")
    print(f"model|{model}")
    print(f"candidates_selected|{len(candidates)}")
    print("domains|performance_work,personal,health_clinical_adjacent")
    print(f"output_dir|{output_dir}")
    print("mode|LOCAL_RESUMABLE_ABSTRACT_SCREENING")

    for index, candidate in enumerate(candidates, start=1):
        candidate_id = str(candidate.get("candidate_id") or f"candidate-{index}")
        title = str(candidate.get("title") or "").strip()
        abstract = str(candidate.get("abstract") or "").strip()[
            :maximum_abstract_characters
        ]
        units = base.evidence_units(title, abstract)
        allowed = {unit["unit_id"] for unit in units}
        origin_domains = query_origin_domains(candidate, mapping)
        prompt = make_prompt(candidate, units, query_domains=origin_domains)
        fingerprint = input_fingerprint(
            candidate,
            model=model,
            config_sha=config_sha,
        )
        item_path = items_dir / base.safe_filename(candidate_id)
        cached = None if args.force else valid_cached_result(
            item_path,
            fingerprint=fingerprint,
            model=model,
        )
        if cached is not None:
            reused += 1
            results.append(cached)
            classification = cached["classification"]
            print(
                f"candidate_reused|{index}/{len(candidates)}|{candidate_id}|"
                f"decision={classification['screening_decision']}|"
                f"domain={classification['primary_csi_domain']}"
            )
            continue

        print(
            f"candidate_start|{index}/{len(candidates)}|{candidate_id}|"
            f"origin={','.join(origin_domains) or 'unresolved'}|"
            f"title={json.dumps(title[:120])}",
            flush=True,
        )
        attempt_errors: list[str] = []
        classification: dict[str, Any] | None = None
        raw: dict[str, Any] | None = None
        elapsed = 0.0
        for attempt in range(1, args.retries + 2):
            try:
                classification, raw, elapsed = base.request_ollama(
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
                    "query_origin_domains": origin_domains,
                    "errors": attempt_errors,
                }
            )
            print(
                f"candidate_failed|{index}/{len(candidates)}|{candidate_id}|"
                f"errors={len(attempt_errors)}"
            )
            continue

        score = ranking_score(candidate, classification)
        prompt_seconds = float(raw.get("prompt_eval_duration") or 0) / 1e9
        output_seconds = float(raw.get("eval_duration") or 0) / 1e9
        result = {
            "schema_version": RESULT_SCHEMA_VERSION,
            "candidate_id": candidate_id,
            "model": model,
            "prompt_version": PROMPT_VERSION,
            "classification_schema_version": SCHEMA_VERSION,
            "input_fingerprint": fingerprint,
            "candidate": candidate,
            "query_origin_domains": origin_domains,
            "evidence_units": units,
            "classification": classification,
            "ranking_score": score,
            "performance": {
                "wall_seconds": elapsed,
                "prompt_tokens": int(raw.get("prompt_eval_count") or 0),
                "prompt_tokens_per_second": (
                    int(raw.get("prompt_eval_count") or 0) / prompt_seconds
                    if prompt_seconds
                    else 0
                ),
                "output_tokens": int(raw.get("eval_count") or 0),
                "output_tokens_per_second": (
                    int(raw.get("eval_count") or 0) / output_seconds
                    if output_seconds
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
            f"domain={classification['primary_csi_domain']}|"
            f"domains={','.join(classification['csi_domains'])}|"
            f"priority={classification['fulltext_priority']}|"
            f"confidence={float(classification['abstract_only_confidence']):.2f}|"
            f"seconds={elapsed:.2f}"
        )

    generated_at = datetime.now(timezone.utc)
    summary = write_outputs(
        output_dir=output_dir,
        discovery_manifest=manifest_path,
        config_path=config_path,
        config=config,
        model=model,
        results=results,
        failures=failures,
        generated_at=generated_at,
    )
    counts = summary["summary"]
    print(f"classified_candidates|{counts['classified']}")
    print(f"classification_failures|{counts['failures']}")
    print(f"cached_results_reused|{reused}")
    print(f"ollama_calls|{ollama_calls}")
    for decision, count in sorted(counts["decisions"].items()):
        print(f"screening_decision|{decision}|{count}")
    for domain, count in sorted(counts["semantic_domain_counts"].items()):
        print(f"semantic_domain_coverage|{domain}|{count}")
    for domain, count in sorted(counts["portfolio_assigned_counts"].items()):
        minimum = counts["portfolio_effective_minimums"].get(domain, 0)
        print(f"portfolio_domain|{domain}|selected={count}|minimum={minimum}")
    print(f"domain_gate_pass|{int(bool(counts['domain_gate_pass']))}")
    print(f"summary_path|{output_dir / 'summary.json'}")
    print(f"ranked_csv|{output_dir / 'ranked-candidates.csv'}")
    print(
        "domain_balanced_portfolio|"
        f"{output_dir / 'domain-balanced-fulltext-portfolio.json'}"
    )
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print("MACHINE_SCREENED_STATUS_CREATED|0")
    print("HUMAN_AUTHORITY_CREATED|0")

    if results and not failures and counts["domain_gate_pass"]:
        status = "PASS"
        exit_code = 0
    elif results:
        status = "PARTIAL"
        exit_code = 2
    else:
        status = "FAIL"
        exit_code = 1
    print(f"STAGE 13 THREE-DOMAIN ABSTRACT CLASSIFICATION|{status}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
