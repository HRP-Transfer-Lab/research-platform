#!/usr/bin/env python3
"""Build canonical draft Evidence Registry records from Stage 13 adjudication JSONL.

This script does not mutate Postgres, scientific state, releases or the CSI Gateway.
It creates a draft/provisional Git-style record bundle that can be reviewed before
importing into the operational Evidence Registry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def parse_label_path(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--model-run must be LABEL=PATH")
    label, raw_path = value.split("=", 1)
    if not label.strip():
        raise argparse.ArgumentTypeError("Model-run label cannot be empty")
    return label.strip(), Path(raw_path).expanduser().resolve()


def candidate_id(row: dict[str, Any]) -> str:
    return str(row.get("candidate_id") or (row.get("candidate") or {}).get("candidate_id") or "")


def normalise_authors(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            output.append(item.strip())
        elif isinstance(item, dict):
            name = item.get("name") or item.get("display_name") or item.get("full_name")
            if isinstance(name, str) and name.strip():
                output.append(name.strip())
    return output


def doi_from(reference: dict[str, Any], candidate: dict[str, Any]) -> str | None:
    raw = candidate.get("doi")
    if isinstance(raw, str) and raw.strip():
        return raw.strip().removeprefix("https://doi.org/")
    cid = str(reference.get("candidate_id") or "")
    if cid.startswith("doi:"):
        return cid[4:]
    return None


def publication_year(candidate: dict[str, Any]) -> int | None:
    for key in ("publication_year", "year"):
        value = candidate.get(key)
        try:
            return int(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            continue
    return None


def publication_date(candidate: dict[str, Any]) -> str | None:
    for key in ("publication_date", "published", "published_at", "date"):
        value = candidate.get(key)
        if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value[:10]):
            return value[:10]
    return None


def source_url(candidate: dict[str, Any], doi: str | None) -> str:
    for key in ("source_url", "url", "landing_page_url", "primary_url"):
        value = candidate.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    if doi:
        return f"https://doi.org/{doi}"
    cid = str(candidate.get("candidate_id") or "")
    if cid.startswith(("http://", "https://")):
        return cid
    raise ValueError(f"No source URL available for {cid!r}")


def review_bucket(reference: dict[str, Any]) -> str:
    title = str(reference.get("title") or "").lower()
    note = str(reference.get("adjudication_note") or "").lower()
    role = str(reference.get("expected_paper_role") or "")
    if "artificial intelligence" in title or "human-ai" in note or "human–ai" in note:
        return "C_human_ai_activity_system"
    if role in {"mechanism", "measurement"}:
        return "B_measurement_mechanism"
    return "A_direct_intervention"


def model_judgement(label: str, row: dict[str, Any]) -> dict[str, Any]:
    classification = row.get("classification") or {}
    return {
        "label": label,
        "model": row.get("model"),
        "decision": classification.get("screening_decision"),
        "paper_role": classification.get("paper_role"),
        "study_design": classification.get("study_design"),
        "primary_domain": classification.get("primary_csi_domain"),
        "domains": classification.get("csi_domains") or [],
        "health_scope": classification.get("health_scope"),
        "priority": classification.get("fulltext_priority"),
        "confidence": classification.get("abstract_only_confidence"),
    }


def deterministic_record_id(reference: dict[str, Any]) -> str:
    cid = str(reference["candidate_id"])
    digest = hashlib.sha256(cid.encode("utf-8")).hexdigest()[:12]
    return f"stage13-{digest}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--discovery", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-run", action="append", type=parse_label_path, default=[])
    parser.add_argument("--generated-on", default=date.today().isoformat())
    args = parser.parse_args()

    reference_path = args.reference.expanduser().resolve()
    discovery_path = args.discovery.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    records_dir = output_dir / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    references = load_jsonl(reference_path)
    discovery = load_json(discovery_path)
    candidates = {
        str(row.get("candidate_id")): row
        for row in discovery.get("candidates") or []
        if isinstance(row, dict) and row.get("candidate_id")
    }

    model_runs: dict[str, dict[str, dict[str, Any]]] = {}
    for label, path in args.model_run:
        rows = load_jsonl(path)
        model_runs[label] = {candidate_id(row): row for row in rows if candidate_id(row)}

    missing = [row["candidate_id"] for row in references if row["candidate_id"] not in candidates]
    if missing:
        raise SystemExit(f"Reference candidates missing from discovery manifest: {missing}")

    bucket_counts: Counter[str] = Counter()
    record_ids: list[str] = []

    for reference in references:
        cid = str(reference["candidate_id"])
        candidate = candidates[cid]
        doi = doi_from(reference, candidate)
        record_id = deterministic_record_id(reference)
        record_ids.append(record_id)
        bucket = review_bucket(reference)
        bucket_counts[bucket] += 1

        model_rows = []
        for label, indexed in model_runs.items():
            row = indexed.get(cid)
            if row:
                model_rows.append(model_judgement(label, row))

        abstract = str(candidate.get("abstract") or "").strip()
        expected_domains = list(reference.get("expected_csi_domains") or [])
        decision = str(reference.get("expected_screening_decision") or "")
        role = str(reference.get("expected_paper_role") or "")

        record = {
            "record_id": record_id,
            "release_id": args.release_id,
            "review_bucket": bucket,
            "bibliography": {
                "title": reference.get("title") or candidate.get("title"),
                "authors": normalise_authors(candidate.get("authors")),
                "year": publication_year(candidate),
                "publication_date": publication_date(candidate),
                "venue": candidate.get("journal") or candidate.get("venue"),
                "source_kind": candidate.get("source_kind") or "journal_article",
                "peer_review_status": candidate.get("peer_review_status"),
                "doi": doi,
                "pmid": candidate.get("pmid"),
                "arxiv_id": candidate.get("arxiv_id"),
                "url": source_url(candidate, doi),
            },
            "review": {
                "primary_classification": "unclassified",
                "secondary_component": None,
                "evidence_rungs": [],
                "route_rationale": reference.get("adjudication_note"),
                "review_status": "reviewing",
                "method_extraction_status": "screening_only",
                "taxonomy_version": "iqm-route-v0.2",
                "source_review_document": "ChatGPT Pro interactive Stage 13 adjudication",
                "source_review_section": "Next-20 provisional reference set",
                "authority": reference.get("reference_status") or "assistant_adjudicated_not_human_approved",
                "screening": {
                    "decision": decision,
                    "paper_role": role,
                    "study_design_label": reference.get("expected_study_design_label"),
                    "primary_csi_domain": reference.get("expected_primary_csi_domain"),
                    "csi_domains": expected_domains,
                    "health_scope": reference.get("expected_health_scope"),
                    "fulltext_priority": reference.get("expected_fulltext_priority"),
                    "reference_confidence": reference.get("reference_confidence"),
                    "adjudication_note": reference.get("adjudication_note"),
                    "abstract": abstract,
                    "model_judgements": model_rows,
                },
            },
            "study": {
                "design": reference.get("expected_study_design_label"),
                "population": {"summary": None, "tags": []},
                "sample": {},
                "setting": None,
                "comparator": None,
            },
            "protocol": {},
            "outcomes": [],
            "product_relevance": [],
            "tags": [
                "provisional_screening",
                f"screening_{decision}" if decision else "screening_unresolved",
                f"paper_role_{role}" if role else "paper_role_unresolved",
                *[f"csi_{domain}" for domain in expected_domains],
            ],
        }

        path = records_dir / f"{record_id}.json"
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = {
        "release_id": args.release_id,
        "schema_version": "1.0.0",
        "taxonomy_version": "iqm-route-v0.2",
        "source_review_document": "ChatGPT Pro interactive Stage 13 adjudication",
        "source_review_section": "Next-20 provisional reference set",
        "record_count": len(references),
        "buckets": dict(sorted(bucket_counts.items())),
        "corpus_basis": "Stage 13 discovery candidates joined to an assistant-adjudicated reference set for reviewer workflow and model benchmarking.",
        "status": "draft",
        "generated_on": args.generated_on,
        "limitations": [
            "Assistant-adjudicated benchmark; not human-approved Registry truth.",
            "Screening-only records may lack population, protocol, outcome, quality and product-relevance extraction.",
            "Model judgements are comparison evidence, not scientific authority.",
            "Draft/provisional records must not be published through the CSI Evidence Gateway until human review and an approved release.",
        ],
        "record_ids": record_ids,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"output_dir|{output_dir}")
    print(f"records|{len(references)}")
    for bucket, count in sorted(bucket_counts.items()):
        print(f"bucket|{bucket}|{count}")
    print(f"model_runs|{len(model_runs)}")
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print("PROVISIONAL_REVIEW_BUNDLE|PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
