#!/usr/bin/env python3
"""Discover psychology-intervention candidates for the Stage 13 overnight pilot.

Searches Europe PMC using versioned thematic queries, excludes sources already
present in the immutable seed release, deduplicates by DOI/PMID/title, and writes
a balanced local candidate manifest. It downloads no PDFs, calls no LLM, and
mutates no Registry, scientific, release, Gateway, or machine-screened state.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = (
    REPO_ROOT
    / "components/evidence-registry/config/"
    / "stage13_overnight_psychology_search.v1.json"
)
DEFAULT_RECORDS_DIR = (
    REPO_ROOT
    / "components/evidence-registry/data/releases/2026-08-23/records"
)
DEFAULT_OUTPUT_ROOT = Path.home() / "hrp-lab/source-corpus/_overnight"
USER_AGENT = "HRP-Transfer-Lab-Stage13-Psychology-Discovery/1.0"

INTERVENTION_TERMS = {
    "intervention", "training", "trial", "randomized", "randomised",
    "program", "programme", "therapy", "treatment", "coaching",
    "practice", "curriculum", "redesign", "implementation",
}
METHOD_TERMS = {
    "randomized", "randomised", "controlled", "trial", "experiment",
    "quasi-experimental", "systematic review", "meta-analysis",
    "meta analysis", "scoping review", "longitudinal",
}
PSYCHOLOGY_TERMS = {
    "cognitive", "psychological", "attention", "memory", "reasoning",
    "metacognitive", "self-regulation", "self regulation", "emotion",
    "stress", "learning", "decision", "behaviour", "behavior",
    "executive function", "wellbeing", "resilience",
}
STOP_WORDS = {
    "about", "after", "among", "based", "between", "during", "from",
    "into", "over", "that", "the", "their", "through", "using", "with",
    "without", "and", "for", "of", "on", "in", "to", "a", "an", "is",
    "are", "by", "as", "at", "study", "effect", "effects",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalise_doi(value: str | None) -> str | None:
    if not value:
        return None
    value = urllib.parse.unquote(str(value)).casefold().strip()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi\s*:\s*", "", value)
    value = re.sub(r"\s+", "", value)
    return value.rstrip(".,;)") or None


def clean_markup(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def title_key(value: str | None) -> str:
    text = clean_markup(value).casefold()
    return re.sub(r"[^a-z0-9]+", "", text)


def title_tokens(value: str | None) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", clean_markup(value).casefold())
        if len(token) >= 4 and token not in STOP_WORDS
    }


def flatten_pub_types(value: Any) -> list[str]:
    if isinstance(value, dict):
        value = value.get("pubType")
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return sorted({str(item) for item in value if item})
    return []


def direct_pdf_urls(row: dict[str, Any]) -> list[str]:
    output: list[str] = []
    full_text = row.get("fullTextUrlList") or {}
    urls = full_text.get("fullTextUrl") if isinstance(full_text, dict) else None
    if not isinstance(urls, list):
        return output
    for item in urls:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        style = str(item.get("documentStyle") or "").casefold()
        if isinstance(url, str) and url.startswith("https://") and (
            style == "pdf" or url.casefold().split("?", 1)[0].endswith(".pdf")
        ):
            output.append(url)
    return sorted(set(output))


def request_json(
    url: str,
    *,
    email: str,
    timeout: int,
    retries: int = 3,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": f"{USER_AGENT} (mailto:{email})",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
            value = json.loads(data.decode("utf-8"))
            if not isinstance(value, dict):
                raise RuntimeError("Expected a JSON object")
            return value
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            RuntimeError,
        ) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(f"Request failed after {retries} attempts: {last_error}")


def existing_identities(records_dir: Path) -> tuple[set[str], set[str]]:
    dois: set[str] = set()
    titles: set[str] = set()
    for path in sorted(records_dir.glob("*.json")):
        record = load_json(path)
        bibliography = record.get("bibliography") or {}
        if not isinstance(bibliography, dict):
            continue
        doi = normalise_doi(bibliography.get("doi"))
        if doi:
            dois.add(doi)
        key = title_key(bibliography.get("title"))
        if key:
            titles.add(key)
    return dois, titles


def candidate_key(row: dict[str, Any]) -> str:
    doi = normalise_doi(row.get("doi"))
    if doi:
        return f"doi:{doi}"
    pmid = str(row.get("pmid") or "").strip()
    if pmid:
        return f"pmid:{pmid}"
    return "title:" + sha256_text(title_key(row.get("title")))[:24]


def lexical_score(row: dict[str, Any]) -> float:
    title = clean_markup(row.get("title")).casefold()
    abstract = clean_markup(row.get("abstract")).casefold()
    combined = f"{title} {abstract}"
    score = 0.0
    score += 4.0 * len(row.get("query_hits") or [])
    score += 1.5 * sum(term in title for term in INTERVENTION_TERMS)
    score += 0.4 * sum(term in abstract for term in INTERVENTION_TERMS)
    score += 1.0 * sum(term in combined for term in METHOD_TERMS)
    score += 0.5 * sum(term in combined for term in PSYCHOLOGY_TERMS)
    score += 2.0 if row.get("is_open_access") else 0.0
    score += 1.0 if row.get("direct_pdf_urls") else 0.0
    score += min(len(abstract) / 4000.0, 1.5)
    cited = row.get("cited_by_count")
    if isinstance(cited, int) and cited > 0:
        score += min(cited / 50.0, 1.0)
    return round(score, 6)


def convert_result(
    raw: dict[str, Any],
    *,
    query_id: str,
    query_label: str,
    rank: int,
) -> dict[str, Any]:
    title = clean_markup(raw.get("title"))
    abstract = clean_markup(raw.get("abstractText"))
    pmid = str(raw.get("pmid") or "").strip() or None
    pmcid = str(raw.get("pmcid") or "").strip() or None
    doi = normalise_doi(raw.get("doi"))
    source = str(raw.get("source") or "").strip() or None
    identifier = str(raw.get("id") or "").strip() or None
    row: dict[str, Any] = {
        "provider": "europe_pmc",
        "provider_id": identifier,
        "source": source,
        "pmid": pmid,
        "pmcid": pmcid,
        "doi": doi,
        "title": title,
        "author_string": clean_markup(raw.get("authorString")),
        "journal": clean_markup(raw.get("journalTitle")),
        "publication_year": raw.get("pubYear"),
        "first_publication_date": raw.get("firstPublicationDate"),
        "publication_types": flatten_pub_types(raw.get("pubTypeList")),
        "abstract": abstract,
        "abstract_sha256": sha256_text(abstract),
        "is_open_access": str(raw.get("isOpenAccess") or "").upper() == "Y",
        "in_europe_pmc": str(raw.get("inEPMC") or "").upper() == "Y",
        "in_pmc": str(raw.get("inPMC") or "").upper() == "Y",
        "cited_by_count": raw.get("citedByCount"),
        "direct_pdf_urls": direct_pdf_urls(raw),
        "query_hits": [
            {
                "query_id": query_id,
                "query_label": query_label,
                "rank": rank,
            }
        ],
    }
    row["candidate_id"] = candidate_key(row)
    return row


def merge_candidate(target: dict[str, Any], incoming: dict[str, Any]) -> None:
    existing_hits = {
        str(hit.get("query_id"))
        for hit in target.get("query_hits") or []
        if isinstance(hit, dict)
    }
    for hit in incoming.get("query_hits") or []:
        if isinstance(hit, dict) and str(hit.get("query_id")) not in existing_hits:
            target.setdefault("query_hits", []).append(hit)
            existing_hits.add(str(hit.get("query_id")))
    target["direct_pdf_urls"] = sorted(
        set(target.get("direct_pdf_urls") or [])
        | set(incoming.get("direct_pdf_urls") or [])
    )
    target["is_open_access"] = bool(
        target.get("is_open_access") or incoming.get("is_open_access")
    )
    if len(str(incoming.get("abstract") or "")) > len(
        str(target.get("abstract") or "")
    ):
        target["abstract"] = incoming["abstract"]
        target["abstract_sha256"] = incoming["abstract_sha256"]


def balanced_selection(
    candidates: dict[str, dict[str, Any]],
    query_ids: list[str],
    target: int,
) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates.values():
        row["deterministic_relevance_score"] = lexical_score(row)
        for hit in row.get("query_hits") or []:
            if isinstance(hit, dict) and hit.get("query_id"):
                buckets[str(hit["query_id"])].append(row)
    for query_id in query_ids:
        buckets[query_id].sort(
            key=lambda row: (
                -float(row["deterministic_relevance_score"]),
                str(row.get("first_publication_date") or ""),
                str(row["candidate_id"]),
            )
        )

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    cursor = {query_id: 0 for query_id in query_ids}
    made_progress = True
    while len(selected) < target and made_progress:
        made_progress = False
        for query_id in query_ids:
            rows = buckets.get(query_id, [])
            while cursor[query_id] < len(rows):
                row = rows[cursor[query_id]]
                cursor[query_id] += 1
                candidate_id = str(row["candidate_id"])
                if candidate_id in seen:
                    continue
                selected.append(row)
                seen.add(candidate_id)
                made_progress = True
                break
            if len(selected) >= target:
                break

    if len(selected) < target:
        remaining = sorted(
            (
                row
                for row in candidates.values()
                if str(row["candidate_id"]) not in seen
            ),
            key=lambda row: (
                -float(row["deterministic_relevance_score"]),
                str(row["candidate_id"]),
            ),
        )
        selected.extend(remaining[: target - len(selected)])

    for rank, row in enumerate(selected, start=1):
        row["selection_rank"] = rank
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover psychology-intervention candidates through Europe PMC."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--records-dir", type=Path, default=DEFAULT_RECORDS_DIR)
    parser.add_argument("--email", default=os.environ.get("EUROPE_PMC_EMAIL"))
    parser.add_argument("--target-candidates", type=int)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--sleep", type=float, default=0.25)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if not args.email or "@" not in args.email:
        raise SystemExit("Supply a valid contact email with --email")
    if args.timeout < 5:
        raise SystemExit("--timeout must be at least 5 seconds")
    if args.sleep < 0:
        raise SystemExit("--sleep cannot be negative")

    config_path = args.config.expanduser().resolve()
    records_dir = args.records_dir.expanduser().resolve()
    config = load_json(config_path)
    if config.get("schema_version") != "stage13-overnight-psychology-search-v1":
        raise SystemExit("Unsupported search configuration schema")
    query_families = config.get("query_families")
    if not isinstance(query_families, list) or not query_families:
        raise SystemExit("Configuration must contain query_families[]")

    target = int(args.target_candidates or config["candidate_target"])
    if target < 1:
        raise SystemExit("Candidate target must be positive")
    minimum_abstract = int(config.get("minimum_abstract_characters", 300))
    maximum_results = int(config.get("maximum_results_per_query", 40))
    if maximum_results < 1 or maximum_results > 1000:
        raise SystemExit("maximum_results_per_query must be between 1 and 1000")

    existing_dois, existing_titles = existing_identities(records_dir)
    candidates: dict[str, dict[str, Any]] = {}
    query_summaries: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    date_from = str(config["date_from"])
    date_to = str(config["date_to"])

    print("=== STAGE 13 PSYCHOLOGY INTERVENTION DISCOVERY ===")
    print("provider|europe_pmc")
    print(f"query_families|{len(query_families)}")
    print(f"candidate_target|{target}")
    print(f"date_range|{date_from}|{date_to}")

    for index, family in enumerate(query_families, start=1):
        if not isinstance(family, dict):
            continue
        query_id = str(family.get("query_id") or f"query_{index}")
        query_label = str(family.get("label") or query_id)
        base_query = str(family.get("query") or "").strip()
        if not base_query:
            errors.append({"query_id": query_id, "error": "empty_query"})
            continue
        full_query = (
            f"({base_query}) AND FIRST_PDATE:[{date_from} TO {date_to}] "
            "AND HAS_ABSTRACT:Y sort_date:y"
        )
        params = urllib.parse.urlencode(
            {
                "query": full_query,
                "format": "json",
                "resultType": "core",
                "pageSize": str(maximum_results),
                "email": args.email,
            }
        )
        url = (
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
            + params
        )
        print(f"query_start|{index}/{len(query_families)}|{query_id}", flush=True)
        try:
            raw = request_json(
                url,
                email=args.email,
                timeout=args.timeout,
            )
            result_list = raw.get("resultList") or {}
            results = (
                result_list.get("result")
                if isinstance(result_list, dict)
                else None
            )
            if not isinstance(results, list):
                results = []
            accepted = excluded_existing = excluded_short = 0
            for rank, item in enumerate(results, start=1):
                if not isinstance(item, dict):
                    continue
                row = convert_result(
                    item,
                    query_id=query_id,
                    query_label=query_label,
                    rank=rank,
                )
                if len(str(row.get("abstract") or "")) < minimum_abstract:
                    excluded_short += 1
                    continue
                doi = normalise_doi(row.get("doi"))
                tkey = title_key(row.get("title"))
                if (doi and doi in existing_dois) or (
                    tkey and tkey in existing_titles
                ):
                    excluded_existing += 1
                    continue
                key = str(row["candidate_id"])
                if key in candidates:
                    merge_candidate(candidates[key], row)
                else:
                    candidates[key] = row
                accepted += 1
            summary = {
                "query_id": query_id,
                "label": query_label,
                "query": full_query,
                "provider_hit_count": raw.get("hitCount"),
                "returned": len(results),
                "accepted_before_deduplication": accepted,
                "excluded_existing": excluded_existing,
                "excluded_short_abstract": excluded_short,
            }
            query_summaries.append(summary)
            print(
                f"query_complete|{query_id}|returned={len(results)}|"
                f"accepted={accepted}|existing={excluded_existing}|"
                f"short_abstract={excluded_short}"
            )
        except Exception as exc:
            errors.append({"query_id": query_id, "error": str(exc)})
            print(f"query_failed|{query_id}|{exc}")
        if args.sleep:
            time.sleep(args.sleep)

    query_ids = [
        str(family.get("query_id"))
        for family in query_families
        if isinstance(family, dict) and family.get("query_id")
    ]
    selected = balanced_selection(candidates, query_ids, target)
    timestamp = datetime.now(timezone.utc)
    output_path = (
        args.output.expanduser().resolve()
        if args.output
        else DEFAULT_OUTPUT_ROOT
        / f"psychology-{timestamp.strftime('%Y%m%d-%H%M%S')}"
        / "discovery.json"
    )
    payload = {
        "schema_version": "stage13-psychology-candidate-discovery-v1",
        "search_id": config.get("search_id"),
        "generated_at": timestamp.isoformat(),
        "provider": "europe_pmc",
        "config_path": str(config_path),
        "config_sha256": sha256_text(canonical_json(config)),
        "records_dir": str(records_dir),
        "date_from": date_from,
        "date_to": date_to,
        "candidate_target": target,
        "summary": {
            "queries": len(query_families),
            "queries_succeeded": len(query_summaries),
            "queries_failed": len(errors),
            "unique_candidates_before_cap": len(candidates),
            "selected_candidates": len(selected),
            "open_access_selected": sum(
                1 for row in selected if row.get("is_open_access")
            ),
            "direct_pdf_selected": sum(
                1 for row in selected if row.get("direct_pdf_urls")
            ),
        },
        "query_summaries": query_summaries,
        "query_errors": errors,
        "candidates": selected,
        "governance": {
            "pdf_downloads": 0,
            "ollama_calls": 0,
            "registry_mutated": False,
            "scientific_state_mutated": False,
            "historical_release_mutated": False,
            "csi_gateway_mutated": False,
            "machine_screened_status_created": False,
            "human_authority_created": False,
        },
    }
    write_json(output_path, payload)

    print(f"unique_candidates_before_cap|{len(candidates)}")
    print(f"selected_candidates|{len(selected)}")
    print(f"open_access_selected|{payload['summary']['open_access_selected']}")
    print(f"direct_pdf_selected|{payload['summary']['direct_pdf_selected']}")
    print(f"query_errors|{len(errors)}")
    print(f"manifest_path|{output_path}")
    print("PDF_DOWNLOADS|0")
    print("OLLAMA_CALLS|0")
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print("MACHINE_SCREENED_STATUS_CREATED|0")

    minimum_success = min(target, 50)
    if len(selected) >= minimum_success:
        status = "PASS"
        exit_code = 0
    elif selected:
        status = "PARTIAL"
        exit_code = 2
    else:
        status = "FAIL"
        exit_code = 1
    print(f"STAGE 13 PSYCHOLOGY INTERVENTION DISCOVERY|{status}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
