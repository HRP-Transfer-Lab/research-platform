"""Read-only scholarly metadata clients. Metadata alone NEVER verifies claim support.

M1 security boundary:
- Fixed Crossref/OpenAlex hosts only; no arbitrary URL fetching or DOI redirects.
- Explicit user opt-in before network calls.
- Bounded response/time, no API tokens in URLs or persisted responses.
- 404/429/5xx and parsing failures are exposed as unresolved, not forged citations.
- No full-text PDFs are fetched or stored by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
import re
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

DOI_PATTERN = re.compile(r"^10\.[0-9]{4,9}/[-._;()/:a-z0-9]+$", re.IGNORECASE)
MAX_JSON_BYTES = 1_000_000
ALLOWED_HOSTS = {"api.crossref.org", "api.openalex.org"}


class SourceMetadataError(ValueError):
    """Metadata lookup was blocked, malformed or unavailable."""


def normalise_doi(value: str) -> str:
    if not isinstance(value, str):
        raise SourceMetadataError("DOI must be a string.")
    doi = value.strip()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.I)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.I).lower()
    if not DOI_PATTERN.fullmatch(doi):
        raise SourceMetadataError("Invalid DOI; rejecting unsafe/ambiguous identifier.")
    return doi


@dataclass(frozen=True)
class MetadataResult:
    provider: str
    query_doi: str
    status: str
    title: str | None
    doi: str | None
    year: int | None
    authors: tuple[str, ...]
    venue: str | None
    work_type: str | None
    url: str | None
    response_sha256: str | None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "query_doi": self.query_doi,
            "status": self.status,
            "title": self.title,
            "doi": self.doi,
            "year": self.year,
            "authors": list(self.authors),
            "venue": self.venue,
            "work_type": self.work_type,
            "url": self.url,
            "response_sha256": self.response_sha256,
            "error": self.error,
            "original_full_text_checked": False,
            "claim_support_verified": False,
        }


def _bounded_json_http(url: str, headers: dict[str, str], *, timeout: float = 8) -> tuple[dict, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in ALLOWED_HOSTS or parsed.username or parsed.password:
        raise SourceMetadataError("Metadata request host/scheme is not allowed.")
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            # Followed redirects could create an unsafe destination: reject if host changed.
            resolved = urlparse(response.geturl())
            if resolved.scheme != "https" or resolved.netloc not in ALLOWED_HOSTS:
                raise SourceMetadataError("Metadata endpoint redirected to an unapproved host.")
            raw = response.read(MAX_JSON_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        code = getattr(exc, "code", None)
        raise SourceMetadataError(f"Metadata request unavailable (HTTP {code or 'network_error'}).") from exc
    if len(raw) > MAX_JSON_BYTES:
        raise SourceMetadataError("Metadata response exceeds byte limit.")
    try:
        doc = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceMetadataError("Metadata endpoint returned invalid JSON.") from exc
    if not isinstance(doc, dict):
        raise SourceMetadataError("Metadata response must be a JSON object.")
    return doc, sha256(raw).hexdigest()


def _text(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    return None


def _first_text(value: Any) -> str | None:
    if isinstance(value, list):
        return next((_text(v) for v in value if _text(v)), None)
    return _text(value)


def _year(value: Any) -> int | None:
    try:
        year = int(value)
        return year if 1600 <= year <= 2200 else None
    except (TypeError, ValueError):
        return None


def _author_name(item: dict) -> str | None:
    parts = [item.get("given"), item.get("family")]
    s = " ".join(x.strip() for x in parts if isinstance(x, str) and x.strip())
    return s or _text(item.get("name"))


def crossref_metadata(doi: str, *, fetch: Callable | None = None) -> MetadataResult:
    """Resolve one DOI through Crossref's /works/{doi}, without interpreting the paper."""
    doi = normalise_doi(doi)
    url = "https://api.crossref.org/works/" + quote(doi, safe="/")
    headers = {"User-Agent": "HRP-ResearchFactory/0.1 (read-only scholarly metadata)", "Accept": "application/json"}
    getter = fetch or _bounded_json_http
    try:
        doc, digest = getter(url, headers)
        m = doc.get("message")
        if not isinstance(m, dict):
            raise SourceMetadataError("Crossref message is not a JSON object.")
        received = normalise_doi(m.get("DOI", ""))
        if received != doi:
            raise SourceMetadataError("Crossref returned a different DOI.")
        date = m.get("published", {}) if isinstance(m.get("published"), dict) else {}
        parts = date.get("date-parts", [])
        dates = parts[0] if isinstance(parts, list) and parts and isinstance(parts[0], list) else []
        authors = tuple(x for a in m.get("author", []) if isinstance(a, dict) if (x := _author_name(a)))
        return MetadataResult("crossref", doi, "metadata_found", _first_text(m.get("title")), received,
                              _year(dates[0] if dates else None), authors, _first_text(m.get("container-title")),
                              _text(m.get("type")), _text(m.get("URL")), digest)
    except SourceMetadataError as exc:
        return MetadataResult("crossref", doi, "unresolved", None, None, None, (), None, None, None, None, str(exc))


def openalex_metadata(doi: str, *, fetch: Callable | None = None) -> MetadataResult:
    """Independent metadata cross-check; key is passed in a header and never logged."""
    doi = normalise_doi(doi)
    url = "https://api.openalex.org/works/" + quote("https://doi.org/" + doi, safe="/:")
    headers = {"User-Agent": "HRP-ResearchFactory/0.1 (read-only scholarly metadata)", "Accept": "application/json"}
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    getter = fetch or _bounded_json_http
    try:
        m, digest = getter(url, headers)
        ids = m.get("ids")
        candidate = (ids.get("doi") if isinstance(ids, dict) else None) or m.get("doi", "")
        received = normalise_doi(candidate)
        if received != doi:
            raise SourceMetadataError("OpenAlex returned a different DOI.")
        authorships = m.get("authorships", [])
        names = tuple(name for a in authorships if isinstance(a, dict)
                      if isinstance(a.get("author"), dict)
                      if (name := _text(a["author"].get("display_name"))))
        source = m.get("primary_location", {})
        source = source.get("source", {}) if isinstance(source, dict) else {}
        venue = _text(source.get("display_name")) if isinstance(source, dict) else None
        return MetadataResult("openalex", doi, "metadata_found", _text(m.get("title")), received,
                              _year(m.get("publication_year")), names, venue,
                              _text(m.get("type")), _text(m.get("doi")), digest)
    except SourceMetadataError as exc:
        return MetadataResult("openalex", doi, "unresolved", None, None, None, (), None, None, None, None, str(exc))


def require_network_opt_in() -> None:
    if os.environ.get("HRP_ALLOW_PUBLIC_METADATA_LOOKUP") != "YES":
        raise PermissionError("Public metadata network access is OFF. Set HRP_ALLOW_PUBLIC_METADATA_LOOKUP=YES explicitly.")


def compare_metadata(crossref: MetadataResult, openalex: MetadataResult) -> str:
    if crossref.status != "metadata_found" or openalex.status != "metadata_found":
        return "not_cross_checked"
    if crossref.doi != openalex.doi:
        return "identifier_conflict"
    # Title differences can indicate a preprint/title correction, not necessarily a false citation.
    normalise = lambda s: re.sub(r"[^a-z0-9]+", "", (s or "").lower())
    if normalise(crossref.title) and normalise(openalex.title) and normalise(crossref.title) != normalise(openalex.title):
        return "title_needs_human_check"
    return "doi_metadata_consistent"
