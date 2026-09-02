#!/usr/bin/env python3
"""Acquire, verify and register the Stage 13 open-access calibration set.

The default mode is a read-only plan. Supplying ``--apply`` downloads only the
source IDs listed in a versioned selection file and only from HTTPS direct-PDF
candidates already recorded by the Stage 13 discovery manifest.

Every download is staged to a temporary file, checked for PDF structure, parsed
with Poppler, and matched to the expected DOI or title before it can enter the
local source corpus. Registration uses ``register_source_document.py`` so the
operational acquisition ledger is updated without changing scientific authority,
historical releases or the CSI Gateway.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SELECTION = (
    REPO_ROOT
    / "components/evidence-registry/config/stage13_mixed_calibration_set.v1.json"
)
DEFAULT_RECORDS_DIR = (
    REPO_ROOT
    / "components/evidence-registry/data/releases/2026-08-23/records"
)
DEFAULT_CORPUS_ROOT = Path.home() / "hrp-lab/source-corpus"
DEFAULT_CONTAINER = "supabase_db_research-platform"
REGISTER_SCRIPT = (
    REPO_ROOT
    / "components/evidence-registry/scripts/register_source_document.py"
)
USER_AGENT = "HRP-Transfer-Lab-Stage13-Acquisition/1.0"
STOP_WORDS = {
    "about", "after", "among", "based", "between", "combined", "during",
    "effects", "from", "into", "not", "over", "study", "that", "the",
    "their", "through", "using", "with", "without", "and", "for", "of",
    "on", "in", "to", "a", "an", "is", "are", "by", "as", "at",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalise_doi(value: str | None) -> str | None:
    if not value:
        return None
    value = urllib.parse.unquote(str(value)).casefold().strip()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi\s*:\s*", "", value)
    value = re.sub(r"\s+", "", value)
    return value.rstrip(".,;)") or None


def normalise_text(value: str) -> str:
    value = value.casefold().replace("–", "-").replace("—", "-")
    value = re.sub(r"(?<=\w)-\s+(?=\w)", "", value)
    value = re.sub(r"[^a-z0-9./:+-]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def title_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.casefold())
        if len(token) >= 4 and token not in STOP_WORDS
    }


def identity_check(
    *,
    text: str,
    expected_title: str,
    expected_doi: str | None,
    minimum_title_coverage: float,
) -> dict[str, Any]:
    normalised = normalise_text(text)
    doi = normalise_doi(expected_doi)
    compact_text = re.sub(r"\s+", "", normalised)
    doi_match = bool(doi and doi in compact_text)

    expected_tokens = title_tokens(expected_title)
    observed_tokens = set(re.findall(r"[a-z0-9]+", normalised))
    matched_tokens = sorted(expected_tokens & observed_tokens)
    coverage = (
        len(matched_tokens) / len(expected_tokens) if expected_tokens else 0.0
    )
    enough_title_tokens = len(expected_tokens) >= 4 and len(matched_tokens) >= 4
    title_match = bool(enough_title_tokens and coverage >= minimum_title_coverage)
    return {
        "passed": doi_match or title_match,
        "doi_match": doi_match,
        "normalised_expected_doi": doi,
        "title_match": title_match,
        "title_token_coverage": round(coverage, 6),
        "expected_title_tokens": sorted(expected_tokens),
        "matched_title_tokens": matched_tokens,
        "minimum_title_coverage": minimum_title_coverage,
    }


def pdf_page_count(path: Path) -> int:
    executable = shutil.which("pdfinfo")
    if not executable:
        raise RuntimeError("pdfinfo is required (install poppler-utils)")
    result = subprocess.run(
        [executable, str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdfinfo failed: {result.stderr.strip()}")
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            pages = int(line.split(":", 1)[1].strip())
            if pages < 1:
                raise RuntimeError("PDF has no pages")
            return pages
    raise RuntimeError("pdfinfo did not report a page count")


def extract_identity_text(path: Path, *, page_limit: int) -> str:
    executable = shutil.which("pdftotext")
    if not executable:
        raise RuntimeError("pdftotext is required (install poppler-utils)")
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as handle:
        output = Path(handle.name)
    try:
        result = subprocess.run(
            [
                executable,
                "-f", "1",
                "-l", str(page_limit),
                "-layout",
                "-enc", "UTF-8",
                str(path),
                str(output),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"pdftotext failed: {result.stderr.strip()}")
        return output.read_text(encoding="utf-8", errors="replace")
    finally:
        output.unlink(missing_ok=True)


def candidate_access(candidate: dict[str, Any]) -> tuple[str, str, str]:
    provider = str(candidate.get("provider") or "other")
    host_type = str(candidate.get("host_type") or "").casefold()
    access_route = (
        "repository"
        if provider == "europe_pmc" or host_type == "repository"
        else "open_access"
    )
    channel = provider if provider in {"unpaywall", "europe_pmc"} else "other"
    licence = str(candidate.get("license") or "").casefold().strip()
    licence_status = (
        "open"
        if licence.startswith("cc-")
        or licence in {"public-domain", "public domain", "pd"}
        else "unknown"
    )
    return access_route, channel, licence_status


def download_pdf(
    *,
    url: str,
    destination: Path,
    email: str,
    timeout: int,
    maximum_bytes: int,
    retries: int,
) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("Only absolute HTTPS candidate URLs are permitted")

    last_error: Exception | None = None
    for attempt in range(1, retries + 2):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.1",
                "User-Agent": f"{USER_AGENT} (mailto:{email})",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                final_url = response.geturl()
                final = urllib.parse.urlparse(final_url)
                if final.scheme != "https":
                    raise RuntimeError("Download redirected to a non-HTTPS URL")
                content_type = response.headers.get_content_type()
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > maximum_bytes:
                    raise RuntimeError(
                        f"Content-Length {content_length} exceeds limit {maximum_bytes}"
                    )
                total = 0
                with destination.open("wb") as output:
                    while True:
                        block = response.read(1024 * 1024)
                        if not block:
                            break
                        total += len(block)
                        if total > maximum_bytes:
                            raise RuntimeError(
                                f"Download exceeded maximum size {maximum_bytes} bytes"
                            )
                        output.write(block)
                if total == 0:
                    raise RuntimeError("Downloaded file is empty")
                with destination.open("rb") as handle:
                    header = handle.read(1024)
                if b"%PDF-" not in header:
                    raise RuntimeError(
                        f"Downloaded content is not a PDF (Content-Type {content_type})"
                    )
                return {
                    "requested_url": url,
                    "final_url": final_url,
                    "content_type": content_type,
                    "bytes": total,
                    "attempt": attempt,
                }
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            OSError,
            ValueError,
            RuntimeError,
        ) as exc:
            last_error = exc
            destination.unlink(missing_ok=True)
            if attempt <= retries:
                time.sleep(min(2 ** (attempt - 1), 5))
                continue
            break
    raise RuntimeError(f"Download failed after {retries + 1} attempt(s): {last_error}")


def load_records(records_dir: Path) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for path in records_dir.glob("*.json"):
        record = load_json(path)
        source_id = str(record.get("record_id") or path.stem)
        output[source_id] = record
    return output


def selected_ids(selection: dict[str, Any], only: set[str] | None) -> list[str]:
    rows = selection.get("acquisition_targets")
    if not isinstance(rows, list):
        raise SystemExit("Selection must contain acquisition_targets[]")
    values: list[str] = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("source_id"):
            raise SystemExit("Every acquisition target requires source_id")
        source_id = str(row["source_id"])
        if only and source_id not in only:
            continue
        values.append(source_id)
    if only:
        missing = sorted(only - set(values))
        if missing:
            raise SystemExit(
                "Requested source IDs are not acquisition targets: "
                + ", ".join(missing)
            )
    return values


def discovery_by_source(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if manifest.get("schema_version") != "stage13-open-access-discovery-v1":
        raise SystemExit("Unsupported discovery manifest schema")
    rows = manifest.get("sources")
    if not isinstance(rows, list):
        raise SystemExit("Discovery manifest must contain sources[]")
    return {
        str(row["source_id"]): row
        for row in rows
        if isinstance(row, dict) and row.get("source_id")
    }


def register_document(
    *,
    source_id: str,
    path: Path,
    candidate: dict[str, Any],
    container: str,
    notes: str,
) -> str:
    access_route, channel, licence_status = candidate_access(candidate)
    command = [
        sys.executable,
        "-u",
        str(REGISTER_SCRIPT),
        "--container", container,
        "--source-id", source_id,
        "--file", str(path),
        "--artifact-kind", "full_text",
        "--access-route", access_route,
        "--channel", channel,
        "--license-status", licence_status,
        "--storage-backend", "local_corpus",
        "--storage-locator", str(path),
        "--external-url", str(candidate["url"]),
        "--notes", notes,
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Registration failed: {detail}")
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Acquire, verify and optionally register selected OA calibration PDFs."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--records-dir", type=Path, default=DEFAULT_RECORDS_DIR)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--email", default=os.environ.get("UNPAYWALL_EMAIL"))
    parser.add_argument("--source-id", action="append", dest="source_ids")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--maximum-bytes", type=int, default=100 * 1024 * 1024)
    parser.add_argument("--identity-pages", type=int, default=8)
    parser.add_argument("--minimum-title-coverage", type=float, default=0.60)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--without-register", action="store_true")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    if not args.email or "@" not in args.email:
        raise SystemExit("Supply a valid contact email with --email or UNPAYWALL_EMAIL")
    if not 0 < args.minimum_title_coverage <= 1:
        raise SystemExit("--minimum-title-coverage must be in (0, 1]")
    if args.identity_pages < 1:
        raise SystemExit("--identity-pages must be positive")

    manifest_path = args.manifest.expanduser().resolve()
    selection_path = args.selection.expanduser().resolve()
    records_dir = args.records_dir.expanduser().resolve()
    corpus_root = args.corpus_root.expanduser().resolve()
    manifest = load_json(manifest_path)
    selection = load_json(selection_path)
    if selection.get("schema_version") != "stage13-mixed-calibration-set-v1":
        raise SystemExit("Unsupported selection schema")
    if selection.get("release_id") != manifest.get("release_id"):
        raise SystemExit("Selection and discovery manifest release IDs differ")

    only = set(args.source_ids) if args.source_ids else None
    source_ids = selected_ids(selection, only)
    records = load_records(records_dir)
    discovered = discovery_by_source(manifest)

    preflight_errors: list[str] = []
    plans: list[dict[str, Any]] = []
    for source_id in source_ids:
        record = records.get(source_id)
        discovery = discovered.get(source_id)
        if not record:
            preflight_errors.append(f"{source_id}: release record missing")
            continue
        if not discovery:
            preflight_errors.append(f"{source_id}: discovery row missing")
            continue
        candidate = discovery.get("preferred_candidate")
        if not isinstance(candidate, dict) or not candidate.get("url"):
            preflight_errors.append(f"{source_id}: no direct-PDF candidate")
            continue
        bibliography = record.get("bibliography") or {}
        plans.append({
            "source_id": source_id,
            "title": bibliography.get("title"),
            "doi": bibliography.get("doi"),
            "review_bucket": record.get("review_bucket"),
            "source_kind": bibliography.get("source_kind"),
            "candidate": candidate,
        })

    print("=== STAGE 13 OA CALIBRATION ACQUISITION ===")
    print(f"mode|{'APPLY' if args.apply else 'PLAN'}")
    print(f"manifest|{manifest_path}")
    print(f"selection|{selection_path}")
    print(f"targets_requested|{len(source_ids)}")
    print(f"targets_ready|{len(plans)}")
    for plan in plans:
        candidate = plan["candidate"]
        print(
            f"plan|{plan['source_id']}|bucket={plan['review_bucket']}|"
            f"kind={plan['source_kind']}|provider={candidate.get('provider')}|"
            f"host={candidate.get('host_type')}|version={candidate.get('version')}"
        )
    for error in preflight_errors:
        print(f"preflight_error|{error}")
    if preflight_errors:
        print("DOWNLOADS_PERFORMED|0")
        print("REGISTRY_MUTATED|0")
        print("STAGE 13 OA CALIBRATION ACQUISITION|PREFLIGHT_FAILED")
        return 2
    if not args.apply:
        print("DOWNLOADS_PERFORMED|0")
        print("REGISTRY_MUTATED|0")
        print("SCIENTIFIC_STATE_MUTATED|0")
        print("HISTORICAL_RELEASE_MUTATED|0")
        print("CSI_GATEWAY_MUTATED|0")
        print("STAGE 13 OA CALIBRATION ACQUISITION|PLAN_READY")
        return 0

    results: list[dict[str, Any]] = []
    succeeded = failed = registered = 0
    for index, plan in enumerate(plans, start=1):
        source_id = str(plan["source_id"])
        candidate = plan["candidate"]
        destination_dir = corpus_root / source_id / "original"
        destination = destination_dir / f"{source_id}.pdf"
        source_manifest = (
            corpus_root / source_id / "manifests" / "stage13-acquisition.json"
        )
        print(f"source_start|{index}/{len(plans)}|{source_id}", flush=True)
        row: dict[str, Any] = {
            "source_id": source_id,
            "title": plan["title"],
            "doi": plan["doi"],
            "candidate": candidate,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "destination": str(destination),
            "status": "failed",
        }
        try:
            destination_dir.mkdir(parents=True, exist_ok=True)
            if destination.exists() and not args.replace:
                pages = pdf_page_count(destination)
                identity_text = extract_identity_text(
                    destination,
                    page_limit=min(args.identity_pages, pages),
                )
                identity = identity_check(
                    text=identity_text,
                    expected_title=str(plan["title"] or ""),
                    expected_doi=str(plan["doi"]) if plan["doi"] else None,
                    minimum_title_coverage=args.minimum_title_coverage,
                )
                if not identity["passed"]:
                    raise RuntimeError(
                        "Existing destination failed identity validation; use --replace only after inspection"
                    )
                download = {
                    "skipped_existing": True,
                    "requested_url": candidate["url"],
                    "final_url": None,
                    "content_type": "application/pdf",
                    "bytes": destination.stat().st_size,
                    "attempt": 0,
                }
            else:
                with tempfile.NamedTemporaryFile(
                    prefix=f"{source_id}-",
                    suffix=".pdf.part",
                    dir=destination_dir,
                    delete=False,
                ) as handle:
                    temporary = Path(handle.name)
                try:
                    download = download_pdf(
                        url=str(candidate["url"]),
                        destination=temporary,
                        email=args.email,
                        timeout=args.timeout,
                        maximum_bytes=args.maximum_bytes,
                        retries=args.retries,
                    )
                    pages = pdf_page_count(temporary)
                    identity_text = extract_identity_text(
                        temporary,
                        page_limit=min(args.identity_pages, pages),
                    )
                    identity = identity_check(
                        text=identity_text,
                        expected_title=str(plan["title"] or ""),
                        expected_doi=str(plan["doi"]) if plan["doi"] else None,
                        minimum_title_coverage=args.minimum_title_coverage,
                    )
                    if not identity["passed"]:
                        raise RuntimeError(
                            "PDF identity check failed: neither DOI nor title threshold matched"
                        )
                    if destination.exists() and args.replace:
                        backup = destination.with_suffix(
                            f".replaced-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf"
                        )
                        destination.replace(backup)
                        row["replaced_backup"] = str(backup)
                    temporary.replace(destination)
                finally:
                    temporary.unlink(missing_ok=True)

            digest = sha256_file(destination)
            pages = pdf_page_count(destination)
            row.update({
                "status": "verified",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "download": download,
                "identity": identity,
                "content_sha256": digest,
                "byte_size": destination.stat().st_size,
                "page_count": pages,
            })

            if not args.without_register:
                notes = (
                    "Stage 13 lawful open-access calibration acquisition; "
                    f"provider={candidate.get('provider')}; "
                    f"version={candidate.get('version')}; "
                    f"identity_doi_match={identity['doi_match']}; "
                    f"title_coverage={identity['title_token_coverage']}."
                )
                row["registration_output"] = register_document(
                    source_id=source_id,
                    path=destination,
                    candidate=candidate,
                    container=args.container,
                    notes=notes,
                )
                row["registered"] = True
                registered += 1
            else:
                row["registered"] = False
            succeeded += 1
            print(
                f"source_verified|{source_id}|pages={pages}|"
                f"bytes={row['byte_size']}|sha256={digest}|"
                f"doi_match={int(identity['doi_match'])}|"
                f"title_coverage={identity['title_token_coverage']:.3f}|"
                f"registered={int(row['registered'])}"
            )
        except Exception as exc:
            failed += 1
            row["error"] = str(exc)
            row["completed_at"] = datetime.now(timezone.utc).isoformat()
            print(f"source_failed|{source_id}|{exc}")
        write_json(source_manifest, row)
        results.append(row)

    run_manifest = (
        corpus_root
        / "_acquisition"
        / f"stage13-mixed-calibration-acquisition-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    )
    write_json(run_manifest, {
        "schema_version": "stage13-mixed-calibration-acquisition-v1",
        "selection_id": selection.get("calibration_set_id"),
        "selection_path": str(selection_path),
        "selection_sha256": sha256_file(selection_path),
        "discovery_manifest_path": str(manifest_path),
        "discovery_manifest_sha256": sha256_file(manifest_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "targets": len(plans),
            "verified": succeeded,
            "failed": failed,
            "registered": registered,
        },
        "sources": results,
        "governance": {
            "scientific_authority_created": False,
            "historical_release_mutated": False,
            "csi_gateway_mutated": False,
            "licensed_credentials_used": False,
        },
    })

    print(f"verified_documents|{succeeded}")
    print(f"failed_documents|{failed}")
    print(f"registered_documents|{registered}")
    print(f"run_manifest|{run_manifest}")
    print(f"DOWNLOADS_PERFORMED|{succeeded}")
    print(f"OPERATIONAL_ACQUISITION_ROWS_UPDATED|{registered}")
    print("SCIENTIFIC_STATE_MUTATED|0")
    print("HISTORICAL_RELEASE_MUTATED|0")
    print("CSI_GATEWAY_MUTATED|0")
    status = "PASS" if failed == 0 and succeeded == len(plans) else "PARTIAL"
    print(f"STAGE 13 OA CALIBRATION ACQUISITION|{status}")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
