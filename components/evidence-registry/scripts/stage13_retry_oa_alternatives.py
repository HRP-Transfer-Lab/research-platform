#!/usr/bin/env python3
"""Retry failed Stage 13 OA acquisitions through alternative direct-PDF routes.

The script reads a previous Stage 13 acquisition run manifest, selects only
failed sources, and rotates through all other direct-PDF locations already
recorded by Unpaywall or Europe PMC. Downloads are identity-checked before
registration. If all lawful alternatives fail, an append-only operational
failure attempt is recorded without changing scientific authority, releases,
or the CSI Gateway.

Default mode is PLAN. Use --apply to download/register.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import register_source_document as registry
import stage13_acquire_oa_calibration_set as acquisition


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RECORDS_DIR = (
    REPO_ROOT
    / "components/evidence-registry/data/releases/2026-08-23/records"
)
DEFAULT_CORPUS_ROOT = Path.home() / "hrp-lab/source-corpus"
DEFAULT_CONTAINER = "supabase_db_research-platform"


def candidate_key(candidate: dict[str, Any]) -> str:
    return str(candidate.get("url") or "").strip()


def is_direct_pdf_hint(url: str) -> bool:
    parsed = acquisition.urllib.parse.urlparse(url)
    path = parsed.path.casefold()
    query = parsed.query.casefold()
    return (
        path.endswith(".pdf")
        or "/pdf/" in path
        or "pdf=" in query
        or "download=pdf" in query
        or "format=pdf" in query
    )


def collect_alternative_candidates(
    discovery: dict[str, Any],
    *,
    failed_url: str | None,
    include_original: bool,
) -> list[dict[str, Any]]:
    """Collect unique HTTPS direct-PDF candidates from the discovery record."""
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(candidate: dict[str, Any]) -> None:
        url = candidate_key(candidate)
        if not url or not url.startswith("https://"):
            return
        if not include_original and failed_url and url == failed_url:
            return
        if url in seen:
            return
        seen.add(url)
        candidates.append(candidate)

    epmc = discovery.get("europe_pmc") or {}
    for row in epmc.get("full_text_urls") or []:
        if not isinstance(row, dict):
            continue
        url = row.get("url")
        style = str(row.get("document_style") or "").casefold()
        if isinstance(url, str) and (style == "pdf" or is_direct_pdf_hint(url)):
            add(
                {
                    "provider": "europe_pmc",
                    "url": url,
                    "landing_page": None,
                    "host_type": "repository",
                    "version": None,
                    "license": None,
                    "is_best": True,
                }
            )

    unpaywall = discovery.get("unpaywall") or {}
    for row in unpaywall.get("locations") or []:
        if not isinstance(row, dict):
            continue
        url = row.get("url_for_pdf")
        if isinstance(url, str):
            add(
                {
                    "provider": "unpaywall",
                    "url": url,
                    "landing_page": row.get("url_for_landing_page") or row.get("url"),
                    "host_type": row.get("host_type"),
                    "version": row.get("version"),
                    "license": row.get("license"),
                    "is_best": row.get("is_best"),
                }
            )

    preferred = discovery.get("preferred_candidate")
    if include_original and isinstance(preferred, dict):
        add(dict(preferred))

    version_rank = {
        "publishedVersion": 0,
        "acceptedVersion": 1,
        "submittedVersion": 2,
        None: 3,
    }
    candidates.sort(
        key=lambda row: (
            0 if row.get("provider") == "europe_pmc" else 1,
            0 if str(row.get("host_type") or "").casefold() == "repository" else 1,
            version_rank.get(row.get("version"), 4),
            0 if row.get("license") else 1,
            candidate_key(row),
        )
    )
    return candidates


def snapshot(container: str) -> str:
    return registry.psql(
        container,
        """
select
 (select current_revision from public.scientific_state_revision where singleton=true),
 (select status from public.evidence_release where release_id='2026-08-23'),
 (select count(*) from public.csi_gateway_evidence_card where evidence_release_id='2026-08-23');
""",
        capture=True,
    )


def record_operational_failure(
    *,
    container: str,
    source_id: str,
    run_manifest_sha: str,
    candidate: dict[str, Any] | None,
    errors: list[dict[str, Any]],
    retry_days: int,
) -> None:
    """Record one idempotent operational failure attempt and current status."""
    source_version_id = registry.resolve_source_version(container, source_id)
    candidate = candidate or {}
    access_route, channel, _licence = acquisition.candidate_access(candidate)
    last_url = str(candidate.get("url") or "") or None
    attempted_at = datetime.now(timezone.utc).isoformat()
    attempt_key = f"stage13-alt-retry-{run_manifest_sha[:16]}"
    error_summary = "; ".join(
        f"{row.get('provider')}:{row.get('error')}" for row in errors
    )[:4000]
    notes = (
        "Stage 13 alternative OA retrieval exhausted without a verified PDF. "
        f"Attempts={len(errors)}. {error_summary}"
    )
    pre = snapshot(container)
    sql = f"""
begin;
set local lock_timeout='5s';
set local statement_timeout='120s';

insert into public.source_acquisition_attempt(
 source_version_id, attempt_key, attempted_at, requested_artifact_kind,
 channel, attempted_by_kind, outcome, access_route, blocker_reason,
 resolved_url, tool_name, tool_version, notes
) values (
 {registry.lit(source_version_id)}, {registry.lit(attempt_key)},
 {registry.lit(attempted_at)}::timestamptz, 'full_text',
 {registry.lit(channel)}, 'system', 'technical_failure',
 {registry.lit(access_route)}, 'technical_failure',
 {registry.lit(last_url)}, 'stage13_retry_oa_alternatives.py', '1',
 {registry.lit(notes)}
)
on conflict (source_version_id, attempt_key) do nothing;

update public.source_acquisition_status
set access_status='retrieval_failed',
    access_route={registry.lit(access_route)},
    blocker_reason='technical_failure',
    fulltext_available=false,
    fulltext_verified=false,
    needs_human_access=false,
    last_checked_at={registry.lit(attempted_at)}::timestamptz,
    next_retry_at=({registry.lit(attempted_at)}::timestamptz
                   + interval '{retry_days} days'),
    notes={registry.lit(notes)},
    recorded_by_kind='system',
    verification_status='system_verified',
    updated_at=now()
where source_version_id={registry.lit(source_version_id)}
  and fulltext_verified=false;
commit;
"""
    registry.psql(container, sql)
    post = snapshot(container)
    if pre != post:
        raise RuntimeError(
            f"Scientific/release/Gateway parity changed unexpectedly: {pre!r} -> {post!r}"
        )


def failed_sources(
    run_manifest: dict[str, Any], requested: set[str] | None
) -> list[dict[str, Any]]:
    rows = [
        row
        for row in run_manifest.get("sources") or []
        if isinstance(row, dict) and row.get("status") == "failed"
    ]
    if requested:
        found = {str(row.get("source_id")) for row in rows}
        missing = sorted(requested - found)
        if missing:
            raise SystemExit(
                "Requested source IDs are not failed rows in the run manifest: "
                + ", ".join(missing)
            )
        rows = [row for row in rows if str(row.get("source_id")) in requested]
    if not rows:
        raise SystemExit("No failed acquisition rows selected")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Retry failed OA acquisitions through alternative direct-PDF routes."
    )
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--discovery-manifest", type=Path)
    parser.add_argument("--records-dir", type=Path, default=DEFAULT_RECORDS_DIR)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--email", required=True)
    parser.add_argument("--source-id", action="append", dest="source_ids")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--maximum-bytes", type=int, default=100 * 1024 * 1024)
    parser.add_argument("--identity-pages", type=int, default=8)
    parser.add_argument("--minimum-title-coverage", type=float, default=0.60)
    parser.add_argument("--retries", type=int, default=0)
    parser.add_argument("--retry-days", type=int, default=14)
    parser.add_argument("--include-original", action="store_true")
    parser.add_argument("--without-register", action="store_true")
    parser.add_argument("--without-failure-status", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if "@" not in args.email:
        raise SystemExit("Supply a valid contact email")
    if args.retry_days < 1:
        raise SystemExit("--retry-days must be positive")

    run_path = args.run_manifest.expanduser().resolve()
    run_manifest = acquisition.load_json(run_path)
    if run_manifest.get("schema_version") != "stage13-mixed-calibration-acquisition-v1":
        raise SystemExit("Unsupported acquisition run-manifest schema")

    discovery_path = (
        args.discovery_manifest.expanduser().resolve()
        if args.discovery_manifest
        else Path(str(run_manifest["discovery_manifest_path"])).expanduser().resolve()
    )
    discovery_manifest = acquisition.load_json(discovery_path)
    discovered = acquisition.discovery_by_source(discovery_manifest)
    records = acquisition.load_records(args.records_dir.expanduser().resolve())
    corpus_root = args.corpus_root.expanduser().resolve()
    requested = set(args.source_ids) if args.source_ids else None
    failures = failed_sources(run_manifest, requested)
    run_hash = acquisition.sha256_file(run_path)

    plans: list[dict[str, Any]] = []
    for failed in failures:
        source_id = str(failed["source_id"])
        discovery = discovered.get(source_id)
        record = records.get(source_id)
        if not discovery or not record:
            raise SystemExit(f"Missing discovery or release record for {source_id}")
        failed_url = str((failed.get("candidate") or {}).get("url") or "") or None
        candidates = collect_alternative_candidates(
            discovery,
            failed_url=failed_url,
            include_original=args.include_original,
        )
        bibliography = record.get("bibliography") or {}
        plans.append(
            {
                "source_id": source_id,
                "title": bibliography.get("title"),
                "doi": bibliography.get("doi"),
                "review_bucket": record.get("review_bucket"),
                "source_kind": bibliography.get("source_kind"),
                "failed_url": failed_url,
                "candidates": candidates,
            }
        )

    print("=== STAGE 13 ALTERNATIVE OA RETRY ===")
    print(f"mode|{'APPLY' if args.apply else 'PLAN'}")
    print(f"run_manifest|{run_path}")
    print(f"discovery_manifest|{discovery_path}")
    print(f"failed_sources_selected|{len(plans)}")
    for plan in plans:
        print(
            f"source_plan|{plan['source_id']}|"
            f"alternative_candidates={len(plan['candidates'])}|"
            f"bucket={plan['review_bucket']}|kind={plan['source_kind']}"
        )
        for index, candidate in enumerate(plan["candidates"], start=1):
            domain = acquisition.urllib.parse.urlparse(
                str(candidate["url"])
            ).netloc
            print(
                f"candidate|{plan['source_id']}|rank={index}|"
                f"provider={candidate.get('provider')}|"
                f"host={candidate.get('host_type')}|"
                f"version={candidate.get('version')}|domain={domain}"
            )

    if not args.apply:
        print("DOWNLOADS_PERFORMED|0")
        print("REGISTRY_MUTATED|0")
        print("SCIENTIFIC_STATE_MUTATED|0")
        print("HISTORICAL_RELEASE_MUTATED|0")
        print("CSI_GATEWAY_MUTATED|0")
        print("STAGE 13 ALTERNATIVE OA RETRY|PLAN_READY")
        return 0

    results: list[dict[str, Any]] = []
    succeeded = unresolved = registered = failure_rows = 0

    for source_index, plan in enumerate(plans, start=1):
        source_id = str(plan["source_id"])
        print(
            f"source_start|{source_index}/{len(plans)}|{source_id}",
            flush=True,
        )
        destination_dir = corpus_root / source_id / "original"
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / f"{source_id}.pdf"
        source_manifest_path = (
            corpus_root
            / source_id
            / "manifests"
            / "stage13-acquisition-retry.json"
        )
        row: dict[str, Any] = {
            "source_id": source_id,
            "title": plan["title"],
            "doi": plan["doi"],
            "source_run_manifest": str(run_path),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
            "attempts": [],
            "destination": str(destination),
        }

        selected_candidate: dict[str, Any] | None = None
        verified: dict[str, Any] | None = None

        if destination.exists():
            try:
                pages = acquisition.pdf_page_count(destination)
                identity_text = acquisition.extract_identity_text(
                    destination, page_limit=min(args.identity_pages, pages)
                )
                identity = acquisition.identity_check(
                    text=identity_text,
                    expected_title=str(plan["title"] or ""),
                    expected_doi=str(plan["doi"]) if plan["doi"] else None,
                    minimum_title_coverage=args.minimum_title_coverage,
                )
                if identity["passed"]:
                    verified = {
                        "skipped_existing": True,
                        "pages": pages,
                        "identity": identity,
                        "content_sha256": acquisition.sha256_file(destination),
                        "byte_size": destination.stat().st_size,
                    }
                else:
                    raise RuntimeError("Existing PDF failed identity validation")
            except Exception as exc:
                row["attempts"].append(
                    {
                        "provider": "local_corpus",
                        "url": None,
                        "error": str(exc),
                    }
                )

        for candidate_index, candidate in enumerate(plan["candidates"], start=1):
            if verified:
                break
            print(
                f"candidate_start|{source_id}|"
                f"{candidate_index}/{len(plan['candidates'])}|"
                f"provider={candidate.get('provider')}|"
                f"host={candidate.get('host_type')}",
                flush=True,
            )
            with tempfile.NamedTemporaryFile(
                prefix=f"{source_id}-alternative-",
                suffix=".pdf.part",
                dir=destination_dir,
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
            try:
                download = acquisition.download_pdf(
                    url=str(candidate["url"]),
                    destination=temporary,
                    email=args.email,
                    timeout=args.timeout,
                    maximum_bytes=args.maximum_bytes,
                    retries=args.retries,
                )
                pages = acquisition.pdf_page_count(temporary)
                identity_text = acquisition.extract_identity_text(
                    temporary, page_limit=min(args.identity_pages, pages)
                )
                identity = acquisition.identity_check(
                    text=identity_text,
                    expected_title=str(plan["title"] or ""),
                    expected_doi=str(plan["doi"]) if plan["doi"] else None,
                    minimum_title_coverage=args.minimum_title_coverage,
                )
                if not identity["passed"]:
                    raise RuntimeError(
                        "PDF identity check failed: neither DOI nor title threshold matched"
                    )
                if destination.exists():
                    backup = destination.with_suffix(
                        f".pre-retry-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf"
                    )
                    destination.replace(backup)
                    row["replaced_backup"] = str(backup)
                temporary.replace(destination)
                selected_candidate = candidate
                verified = {
                    "skipped_existing": False,
                    "download": download,
                    "pages": pages,
                    "identity": identity,
                    "content_sha256": acquisition.sha256_file(destination),
                    "byte_size": destination.stat().st_size,
                }
                row["attempts"].append(
                    {
                        "provider": candidate.get("provider"),
                        "url": candidate.get("url"),
                        "status": "verified",
                    }
                )
                print(
                    f"candidate_verified|{source_id}|"
                    f"provider={candidate.get('provider')}|pages={pages}|"
                    f"doi_match={int(identity['doi_match'])}|"
                    f"title_coverage={identity['title_token_coverage']:.3f}"
                )
            except Exception as exc:
                row["attempts"].append(
                    {
                        "provider": candidate.get("provider"),
                        "url": candidate.get("url"),
                        "error": str(exc),
                    }
                )
                print(
                    f"candidate_failed|{source_id}|"
                    f"provider={candidate.get('provider')}|{exc}"
                )
            finally:
                temporary.unlink(missing_ok=True)

        if verified:
            candidate_for_registration = selected_candidate or (
                plan["candidates"][0] if plan["candidates"] else {}
            )
            row.update(
                {
                    "status": "verified",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "selected_candidate": selected_candidate,
                    **verified,
                }
            )
            if not args.without_register:
                notes = (
                    "Stage 13 alternative lawful OA acquisition; "
                    f"source_run={run_path.name}; "
                    f"provider={candidate_for_registration.get('provider')}; "
                    f"version={candidate_for_registration.get('version')}; "
                    f"identity_doi_match={verified['identity']['doi_match']}; "
                    f"title_coverage={verified['identity']['title_token_coverage']}."
                )
                row["registration_output"] = acquisition.register_document(
                    source_id=source_id,
                    path=destination,
                    candidate=candidate_for_registration,
                    container=args.container,
                    notes=notes,
                )
                row["registered"] = True
                registered += 1
            else:
                row["registered"] = False
            succeeded += 1
            print(
                f"source_verified|{source_id}|pages={verified['pages']}|"
                f"bytes={verified['byte_size']}|"
                f"sha256={verified['content_sha256']}|"
                f"registered={int(row['registered'])}"
            )
        else:
            unresolved += 1
            row["completed_at"] = datetime.now(timezone.utc).isoformat()
            if not args.without_failure_status:
                last_candidate = (
                    plan["candidates"][-1]
                    if plan["candidates"]
                    else ({"provider": "other", "host_type": "other"})
                )
                record_operational_failure(
                    container=args.container,
                    source_id=source_id,
                    run_manifest_sha=run_hash,
                    candidate=last_candidate,
                    errors=row["attempts"],
                    retry_days=args.retry_days,
                )
                row["failure_status_recorded"] = True
                failure_rows += 1
            else:
                row["failure_status_recorded"] = False
            print(
                f"source_unresolved|{source_id}|"
                f"attempts={len(row['attempts'])}|"
                f"failure_status_recorded={int(row['failure_status_recorded'])}"
            )

        acquisition.write_json(source_manifest_path, row)
        results.append(row)

    output_path = (
        corpus_root
        / "_acquisition"
        / f"stage13-alternative-oa-retry-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    )
    acquisition.write_json(
        output_path,
        {
            "schema_version": "stage13-alternative-oa-retry-v1",
            "source_run_manifest": str(run_path),
            "source_run_manifest_sha256": run_hash,
            "discovery_manifest": str(discovery_path),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "sources": len(plans),
                "verified": succeeded,
                "unresolved": unresolved,
                "registered": registered,
                "failure_status_rows": failure_rows,
            },
            "sources": results,
            "governance": {
                "scientific_authority_created": False,
                "historical_release_mutated": False,
                "csi_gateway_mutated": False,
                "licensed_credentials_used": False,
            },
        },
    )

    print(f"verified_documents|{succeeded}")
    print(f"unresolved_documents|{unresolved}")
    print(f"registered_documents|{registered}")
    print(f"operational_failure_rows|{failure_rows}")
    print(f"run_manifest|{output_path}")
    print(f"DOWNLOADS_PERFORMED|{succeeded}")
    print(
        f"OPERATIONAL_ACQUISITION_ROWS_UPDATED|"
        f"{registered + failure_rows}"
    )
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    status = "PASS" if unresolved == 0 else "PARTIAL"
    print(f"STAGE 13 ALTERNATIVE OA RETRY|{status}")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
