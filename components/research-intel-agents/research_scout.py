#!/usr/bin/env python3
"""Shared HRP research discovery scout.

Discovery only. It never writes to the Evidence Registry or Evidence Gateway.
Candidates must pass the Evidence Workbench review lifecycle before becoming
approved evidence or downstream claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_CONFIG = HERE / "scout-config.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_config(path: Path = DEFAULT_CONFIG) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("scout config must be an object")
    return value


def _norm(value: str) -> str:
    return " ".join(str(value or "").lower().replace("-", " ").split())


def title_anchor_matches(title: str, topic: dict) -> list[str]:
    text = _norm(title)
    return [a for a in topic.get("anchors", []) if _norm(a) in text]


def title_relevant(title: str, topic: dict) -> bool:
    return bool(title_anchor_matches(title, topic))


def _json_get(url: str, headers: dict | None = None, retries: int = 4, base_delay: float = 1.0) -> Any:
    last = None
    for attempt in range(retries + 1):
        request = Request(url, headers=headers or {})
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last = RuntimeError(f"HTTP {exc.code} from {url}: {body[:400]}")
            if exc.code != 429 or attempt >= retries:
                raise last from exc
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            delay = base_delay * (2 ** attempt)
            if retry_after:
                try:
                    delay = max(delay, float(retry_after))
                except ValueError:
                    pass
            time.sleep(delay)
        except URLError as exc:
            raise RuntimeError(f"Request failed for {url}: {exc}") from exc
    raise last or RuntimeError("request failed")


def _candidate_id(source: str, external_id: str | None, title: str) -> str:
    raw = f"{source}:{external_id or _norm(title)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _candidate(
    *,
    source: str,
    title: str,
    topic_id: str,
    topic: dict,
    external_id: str | None = None,
    doi: str | None = None,
    pmid: str | None = None,
    published: str | None = None,
    venue: str | None = None,
    url: str | None = None,
) -> dict:
    return {
        "candidate_id": _candidate_id(source, external_id or doi or pmid, title),
        "source": source,
        "title": title,
        "identifiers": {"external_id": external_id, "doi": doi, "pmid": pmid},
        "published": published,
        "venue": venue,
        "url": url,
        "topic_family": topic_id,
        "consumers": topic.get("consumers", []),
        "relevance_terms": title_anchor_matches(title, topic),
        "discovery_status": "DISCOVERED_UNSCREENED",
        "claim_status": "NO_PUBLIC_CLAIM",
        "human_review_required": True,
        "next_gate": "SCREEN_IN_EVIDENCE_WORKBENCH",
    }


def scan_crossref(cfg: dict, start_date: str, rows: int) -> list[dict]:
    source = cfg["sources"].get("crossref", {})
    if not source.get("enabled"):
        return []
    base = str(source.get("api_base") or "https://api.crossref.org").rstrip("/")
    email = os.environ.get(str(source.get("contact_email_env") or "HRP_RESEARCH_CONTACT_EMAIL"))
    headers = {"Accept": "application/json", "User-Agent": "HRPResearchScout/0.1"}
    if email:
        headers["User-Agent"] = f"HRPResearchScout/0.1 (mailto:{email})"
    delay = 0.40 if email else 1.10
    first = True
    out = []
    for topic_id, topic in cfg.get("topic_families", {}).items():
        for query in topic.get("queries", []):
            params = {
                "query.title": query,
                "filter": f"from-pub-date:{start_date},type:journal-article",
                "rows": rows,
                "select": "DOI,title,published,URL,type,container-title",
                "sort": "published",
                "order": "desc",
            }
            if email:
                params["mailto"] = email
            if not first:
                time.sleep(delay)
            first = False
            body = _json_get(f"{base}/works?{urlencode(params)}", headers, retries=4, base_delay=2.0)
            items = (((body or {}).get("message") or {}).get("items") or [])
            for item in items:
                title = str((item.get("title") or [""])[0]).strip()
                if not title or not title_relevant(title, topic):
                    continue
                parts = (((item.get("published") or {}).get("date-parts")) or [[]])
                published = "-".join(str(x).zfill(2) for x in (parts[0] if parts else [])) or None
                out.append(_candidate(
                    source="CROSSREF",
                    title=title,
                    topic_id=topic_id,
                    topic=topic,
                    external_id=item.get("DOI"),
                    doi=item.get("DOI"),
                    published=published,
                    venue=((item.get("container-title") or [None])[0]),
                    url=item.get("URL"),
                ))
    return out


def scan_pubmed(cfg: dict, lookback_days: int, rows: int) -> list[dict]:
    source = cfg["sources"].get("pubmed", {})
    if not source.get("enabled"):
        return []
    base = str(source.get("api_base") or "https://eutils.ncbi.nlm.nih.gov/entrez/eutils").rstrip("/")
    email = os.environ.get(str(source.get("contact_email_env") or "PUBMED_EMAIL"))
    headers = {"Accept": "application/json", "User-Agent": "HRPResearchScout/0.1"}
    last_request = 0.0

    def get(url: str) -> Any:
        nonlocal last_request
        elapsed = time.monotonic() - last_request
        if elapsed < 0.40:
            time.sleep(0.40 - elapsed)
        value = _json_get(url, headers, retries=4, base_delay=1.0)
        last_request = time.monotonic()
        return value

    out = []
    for topic_id, topic in cfg.get("topic_families", {}).items():
        for query in topic.get("queries", []):
            params = {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": rows,
                "sort": "pub date",
                "reldate": lookback_days,
                "datetype": "pdat",
            }
            if email:
                params["email"] = email
            search = get(f"{base}/esearch.fcgi?{urlencode(params)}")
            ids = (((search or {}).get("esearchresult") or {}).get("idlist") or [])
            if not ids:
                continue
            summary = get(f"{base}/esummary.fcgi?{urlencode({'db':'pubmed','id':','.join(ids),'retmode':'json'})}")
            result = (summary or {}).get("result") or {}
            for pmid in ids:
                item = result.get(str(pmid)) or {}
                title = str(item.get("title") or "").strip()
                if not title or not title_relevant(title, topic):
                    continue
                doi = None
                for article_id in item.get("articleids") or []:
                    if str(article_id.get("idtype") or "").lower() == "doi":
                        doi = article_id.get("value")
                        break
                out.append(_candidate(
                    source="PUBMED",
                    title=title,
                    topic_id=topic_id,
                    topic=topic,
                    external_id=str(pmid),
                    doi=doi,
                    pmid=str(pmid),
                    published=item.get("pubdate"),
                    venue=item.get("fulljournalname") or item.get("source"),
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                ))
    return out


def dedupe(candidates: list[dict]) -> list[dict]:
    seen, out = set(), []
    for item in candidates:
        ids = item.get("identifiers") or {}
        key = str(ids.get("doi") or ids.get("pmid") or item.get("candidate_id")).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def scan(config_path: Path = DEFAULT_CONFIG) -> dict:
    cfg = load_config(config_path)
    cadence = cfg.get("cadence") or {}
    lookback = int(cadence.get("lookback_days") or 21)
    rows = int(cadence.get("max_results_per_query") or 5)
    start = (date.today() - timedelta(days=lookback)).isoformat()
    candidates = dedupe(scan_crossref(cfg, start, rows) + scan_pubmed(cfg, lookback, rows))
    candidates = candidates[: int(cadence.get("max_candidates_per_scan") or 120)]
    return {
        "schema_version": "0.1",
        "scout_id": cfg.get("scout_id"),
        "generated_at": now_iso(),
        "lookback_days": lookback,
        "candidate_count": len(candidates),
        "review_policy": {
            "canonical_write_enabled": False,
            "human_review_required": True,
            "next_gate": "SCREEN_IN_EVIDENCE_WORKBENCH",
        },
        "candidates": candidates,
    }


def write_review_queue(result: dict, config_path: Path = DEFAULT_CONFIG) -> Path:
    cfg = load_config(config_path)
    raw = str((cfg.get("policy") or {}).get("output_path") or ".local/research-intel-agents/review-queue-latest.json")
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Shared HRP research discovery scout")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan")
    sub.add_parser("status")
    args = parser.parse_args(argv)

    if args.cmd == "status":
        cfg = load_config(args.config)
        print(json.dumps({
            "scout_id": cfg.get("scout_id"),
            "discovery_only": (cfg.get("policy") or {}).get("discovery_only"),
            "canonical_write_enabled": (cfg.get("policy") or {}).get("canonical_write_enabled"),
            "enabled_sources": [k for k, v in (cfg.get("sources") or {}).items() if v.get("enabled")],
            "topic_families": list((cfg.get("topic_families") or {}).keys()),
        }, indent=2))
        return 0

    result = scan(args.config)
    path = write_review_queue(result, args.config)
    print(json.dumps({
        "status": "OK",
        "candidate_count": result["candidate_count"],
        "review_queue": str(path),
        "next_gate": result["review_policy"]["next_gate"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
