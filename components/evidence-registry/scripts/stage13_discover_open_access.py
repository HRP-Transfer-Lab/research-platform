#!/usr/bin/env python3
"""Discover lawful open-access candidates for Registry sources.

This script is deliberately read-only with respect to PostgreSQL and Git-tracked
scientific state. It reads the release records, checks Unpaywall and (where a
PMID/DOI is available) Europe PMC, and writes a local discovery manifest. It
never downloads a paper, never follows institutional-login routes and never
changes scientific authority, releases or the CSI Gateway.

Unpaywall requires a contact email. Supply --email or UNPAYWALL_EMAIL.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RECORDS_DIR = (
    REPO_ROOT
    / "components/evidence-registry/data/releases/2026-08-23/records"
)
DEFAULT_OUTPUT_ROOT = Path.home() / "hrp-lab/source-corpus/_discovery"
DEFAULT_CONTAINER = "supabase_db_research-platform"
USER_AGENT = "HRP-Transfer-Lab-Stage13/1.0"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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


def request_json(url: str, *, timeout: int, email: str) -> dict[str, Any]:
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
    except urllib.error.HTTPError as exc:
        detail = exc.read(1000).decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid JSON response from {url}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object from {url}")
    return value


def load_records(records_dir: Path, source_ids: set[str] | None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(records_dir.glob("*.json")):
        record = load_json(path)
        source_id = str(record.get("record_id") or path.stem)
        if source_ids and source_id not in source_ids:
            continue
        bibliography = record.get("bibliography") or {}
        if not isinstance(bibliography, dict):
            bibliography = {}
        records.append(
            {
                "source_id": source_id,
                "record_path": str(path),
                "title": bibliography.get("title"),
                "doi": bibliography.get("doi"),
                "pmid": bibliography.get("pmid"),
                "source_kind": bibliography.get("source_kind"),
                "peer_review_status": bibliography.get("peer_review_status"),
                "year": bibliography.get("year"),
            }
        )
    if source_ids:
        found = {str(row["source_id"]) for row in records}
        missing = sorted(source_ids - found)
        if missing:
            raise SystemExit("Unknown source IDs: " + ", ".join(missing))
    if not records:
        raise SystemExit(f"No source records found in {records_dir}")
    return records


def acquisition_status(container: str) -> tuple[dict[str, dict[str, Any]], str | None]:
    """Read current acquisition state when the local Supabase container exists."""
    try:
        running = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container],
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return {}, "docker_not_found"
    if running.returncode != 0 or running.stdout.strip() != "true":
        return {}, "database_container_not_running"

    sql = """
select
  source_id,
  access_status,
  access_route,
  blocker_reason,
  fulltext_available,
  fulltext_verified,
  needs_human_access
from public.v_source_acquisition_dashboard
order by source_id;
"""
    result = subprocess.run(
        [
            "docker", "exec", "-i", container,
            "psql", "-U", "postgres", "-d", "postgres",
            "-A", "-t", "-F", "|", "-v", "ON_ERROR_STOP=1",
        ],
        input=sql,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return {}, "acquisition_dashboard_unavailable"

    output: dict[str, dict[str, Any]] = {}
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        fields = line.split("|")
        if len(fields) != 7:
            continue
        source_id, status, route, blocker, available, verified, human = fields
        output[source_id] = {
            "access_status": status,
            "access_route": route,
            "blocker_reason": blocker,
            "fulltext_available": available == "t",
            "fulltext_verified": verified == "t",
            "needs_human_access": human == "t",
        }
    return output, None


def unpaywall_lookup(doi: str, *, email: str, timeout: int) -> dict[str, Any]:
    encoded_doi = urllib.parse.quote(doi.strip(), safe="")
    query = urllib.parse.urlencode({"email": email})
    url = f"https://api.unpaywall.org/v2/{encoded_doi}?{query}"
    raw = request_json(url, timeout=timeout, email=email)

    locations: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    candidates: list[dict[str, Any]] = []
    best = raw.get("best_oa_location")
    raw_locations = []
    if isinstance(best, dict):
        raw_locations.append((True, best))
    for location in raw.get("oa_locations") or []:
        if isinstance(location, dict):
            raw_locations.append((False, location))

    for is_best, location in raw_locations:
        row = {
            "is_best": bool(is_best or location.get("is_best")),
            "host_type": location.get("host_type"),
            "version": location.get("version"),
            "license": location.get("license"),
            "url": location.get("url"),
            "url_for_pdf": location.get("url_for_pdf"),
            "url_for_landing_page": location.get("url_for_landing_page"),
            "evidence": location.get("evidence"),
            "repository_institution": location.get("repository_institution"),
        }
        key = (
            row["url_for_pdf"], row["url"], row["url_for_landing_page"],
            row["host_type"], row["version"], row["license"],
        )
        if key in seen:
            continue
        seen.add(key)
        locations.append(row)
        pdf_url = row.get("url_for_pdf")
        if isinstance(pdf_url, str) and pdf_url.startswith("https://"):
            candidates.append(row)

    candidates.sort(
        key=lambda row: (
            not bool(row.get("is_best")),
            row.get("host_type") != "publisher",
            row.get("version") != "publishedVersion",
            not bool(row.get("license")),
            str(row.get("url_for_pdf")),
        )
    )
    preferred = candidates[0] if candidates else None

    return {
        "queried": True,
        "doi": raw.get("doi") or doi,
        "is_oa": bool(raw.get("is_oa")),
        "oa_status": raw.get("oa_status"),
        "journal_is_oa": raw.get("journal_is_oa"),
        "journal_is_in_doaj": raw.get("journal_is_in_doaj"),
        "has_repository_copy": bool(raw.get("has_repository_copy")),
        "locations": locations,
        "preferred_direct_pdf": preferred,
    }


def europe_pmc_lookup(
    *, doi: str | None, pmid: str | None, email: str, timeout: int
) -> dict[str, Any]:
    if pmid:
        query_text = f"EXT_ID:{pmid} AND SRC:MED"
    elif doi:
        escaped = doi.replace('"', "")
        query_text = f'DOI:"{escaped}"'
    else:
        return {"queried": False}

    query = urllib.parse.urlencode(
        {
            "query": query_text,
            "format": "json",
            "resultType": "core",
            "pageSize": "5",
        }
    )
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?{query}"
    raw = request_json(url, timeout=timeout, email=email)
    result_list = raw.get("resultList") or {}
    rows = result_list.get("result") if isinstance(result_list, dict) else None
    if not isinstance(rows, list) or not rows:
        return {"queried": True, "found": False}

    normalised_doi = doi.casefold() if isinstance(doi, str) else None
    selected: dict[str, Any] | None = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_doi = row.get("doi")
        if pmid and str(row.get("pmid") or row.get("id") or "") == str(pmid):
            selected = row
            break
        if normalised_doi and isinstance(row_doi, str) and row_doi.casefold() == normalised_doi:
            selected = row
            break
    if selected is None:
        selected = next((row for row in rows if isinstance(row, dict)), None)
    if selected is None:
        return {"queried": True, "found": False}

    urls: list[dict[str, Any]] = []
    full_text = selected.get("fullTextUrlList") or {}
    raw_urls = full_text.get("fullTextUrl") if isinstance(full_text, dict) else None
    if isinstance(raw_urls, list):
        for row in raw_urls:
            if not isinstance(row, dict):
                continue
            url_value = row.get("url")
            if isinstance(url_value, str) and url_value.startswith("https://"):
                urls.append(
                    {
                        "url": url_value,
                        "document_style": row.get("documentStyle"),
                        "availability": row.get("availability"),
                        "site": row.get("site"),
                    }
                )

    pdf_urls = [
        row for row in urls
        if str(row.get("document_style") or "").casefold() == "pdf"
    ]
    return {
        "queried": True,
        "found": True,
        "id": selected.get("id"),
        "source": selected.get("source"),
        "pmid": selected.get("pmid"),
        "pmcid": selected.get("pmcid"),
        "doi": selected.get("doi"),
        "is_open_access": str(selected.get("isOpenAccess") or "").upper() == "Y",
        "in_epmc": str(selected.get("inEPMC") or "").upper() == "Y",
        "in_pmc": str(selected.get("inPMC") or "").upper() == "Y",
        "full_text_urls": urls,
        "preferred_direct_pdf": pdf_urls[0] if pdf_urls else None,
    }


def choose_candidate(unpaywall: dict[str, Any], epmc: dict[str, Any]) -> dict[str, Any] | None:
    preferred = unpaywall.get("preferred_direct_pdf")
    if isinstance(preferred, dict) and preferred.get("url_for_pdf"):
        return {
            "provider": "unpaywall",
            "url": preferred["url_for_pdf"],
            "landing_page": preferred.get("url_for_landing_page") or preferred.get("url"),
            "host_type": preferred.get("host_type"),
            "version": preferred.get("version"),
            "license": preferred.get("license"),
            "is_best": preferred.get("is_best"),
        }
    epmc_pdf = epmc.get("preferred_direct_pdf")
    if isinstance(epmc_pdf, dict) and epmc_pdf.get("url"):
        return {
            "provider": "europe_pmc",
            "url": epmc_pdf["url"],
            "landing_page": None,
            "host_type": "repository",
            "version": None,
            "license": None,
            "is_best": True,
        }
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover open-access source candidates without downloading or mutating the Registry."
    )
    parser.add_argument("--records-dir", type=Path, default=DEFAULT_RECORDS_DIR)
    parser.add_argument("--source-id", action="append", dest="source_ids")
    parser.add_argument("--email", default=os.environ.get("UNPAYWALL_EMAIL"))
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--sleep", type=float, default=0.15)
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--without-db", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if not args.email or "@" not in args.email:
        raise SystemExit("Supply a valid contact email with --email or UNPAYWALL_EMAIL")
    records_dir = args.records_dir.expanduser().resolve()
    source_ids = set(args.source_ids) if args.source_ids else None
    records = load_records(records_dir, source_ids)

    statuses: dict[str, dict[str, Any]] = {}
    status_warning: str | None = None
    if not args.without_db:
        statuses, status_warning = acquisition_status(args.container)

    generated_at = datetime.now(timezone.utc).isoformat()
    output_root = DEFAULT_OUTPUT_ROOT
    output_root.mkdir(parents=True, exist_ok=True)
    output_path = (
        args.output.expanduser().resolve()
        if args.output
        else output_root / f"stage13-oa-discovery-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    print("=== STAGE 13 OPEN-ACCESS DISCOVERY ===")
    print(f"records_dir|{records_dir}")
    print(f"records_considered|{len(records)}")
    print(f"database_status_available|{int(bool(statuses))}")
    if status_warning:
        print(f"database_status_warning|{status_warning}")

    for index, record in enumerate(records, start=1):
        source_id = str(record["source_id"])
        doi = str(record["doi"]).strip() if record.get("doi") else None
        pmid = str(record["pmid"]).strip() if record.get("pmid") else None
        current = statuses.get(source_id, {})
        row: dict[str, Any] = {
            **record,
            "current_acquisition": current or None,
            "unpaywall": {"queried": False},
            "europe_pmc": {"queried": False},
            "preferred_candidate": None,
            "errors": [],
        }

        if doi:
            try:
                row["unpaywall"] = unpaywall_lookup(
                    doi, email=args.email, timeout=args.timeout
                )
            except Exception as exc:
                row["errors"].append(f"unpaywall:{exc}")
        else:
            row["errors"].append("unpaywall:no_doi")

        if doi or pmid:
            try:
                row["europe_pmc"] = europe_pmc_lookup(
                    doi=doi, pmid=pmid, email=args.email, timeout=args.timeout
                )
            except Exception as exc:
                row["errors"].append(f"europe_pmc:{exc}")

        row["preferred_candidate"] = choose_candidate(
            row["unpaywall"], row["europe_pmc"]
        )
        rows.append(row)

        unpaywall_status = row["unpaywall"].get("oa_status") or "unknown"
        candidate = row["preferred_candidate"]
        current_status = current.get("access_status", "unknown") if current else "unknown"
        print(
            f"source|{index}/{len(records)}|{source_id}|current={current_status}|"
            f"unpaywall={unpaywall_status}|direct_pdf={int(bool(candidate))}|"
            f"errors={len(row['errors'])}"
        )
        if args.sleep > 0 and index < len(records):
            time.sleep(args.sleep)

    summary = {
        "records_considered": len(rows),
        "already_fulltext_verified": sum(
            1
            for row in rows
            if (row.get("current_acquisition") or {}).get("fulltext_verified")
        ),
        "unpaywall_open_access": sum(
            1 for row in rows if row["unpaywall"].get("is_oa")
        ),
        "direct_pdf_candidates": sum(
            1 for row in rows if row.get("preferred_candidate")
        ),
        "europe_pmc_open_access": sum(
            1 for row in rows if row["europe_pmc"].get("is_open_access")
        ),
        "records_with_errors": sum(1 for row in rows if row["errors"]),
        "blocked_currently": sum(
            1
            for row in rows
            if (row.get("current_acquisition") or {}).get("access_status") == "blocked"
        ),
    }
    manifest = {
        "schema_version": "stage13-open-access-discovery-v1",
        "generated_at": generated_at,
        "release_id": "2026-08-23",
        "records_dir": str(records_dir),
        "providers": {
            "unpaywall": "v2 DOI API",
            "europe_pmc": "REST search resultType=core",
        },
        "contact_email_stored": False,
        "database_status_warning": status_warning,
        "summary": summary,
        "sources": rows,
        "governance": {
            "discovery_only": True,
            "downloads_performed": 0,
            "registry_mutated": False,
            "scientific_state_mutated": False,
            "historical_release_mutated": False,
            "csi_gateway_mutated": False,
            "institutional_credentials_used": False,
        },
    }
    output_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"already_fulltext_verified|{summary['already_fulltext_verified']}")
    print(f"unpaywall_open_access|{summary['unpaywall_open_access']}")
    print(f"europe_pmc_open_access|{summary['europe_pmc_open_access']}")
    print(f"direct_pdf_candidates|{summary['direct_pdf_candidates']}")
    print(f"records_with_errors|{summary['records_with_errors']}")
    print(f"manifest_path|{output_path}")
    print("DOWNLOADS_PERFORMED|0")
    print("REGISTRY_MUTATED|0")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    print("STAGE 13 OPEN-ACCESS DISCOVERY|PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
