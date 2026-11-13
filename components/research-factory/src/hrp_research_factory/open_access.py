"""Optional Europe PMC *open-access* source importer, disabled by default.

By DOI, resolve a PMC record with isOpenAccess=Y and inEPMC=Y, then fetch its
bounded JATS fullTextXML from the single fixed EMBL-EBI host. Store a local,
checksum-bound text selection; never upload it to a hosted model automatically.
"""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
import xml.etree.ElementTree as ET

from .contracts import PublicationContract
from .evidence_pipeline import load_candidate_seed
from .evidence_sources import normalise_doi
from .source_packets import MAX_SOURCE_BYTES

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
PMCID_RE = re.compile(r"^PMC[0-9]{4,12}$")
MAX_XML_BYTES = 3_000_000


class OpenAccessError(ValueError):
    pass


def require_open_access_opt_in() -> None:
    if os.getenv("HRP_ALLOW_PUBLIC_FULLTEXT_LOOKUP") != "YES":
        raise PermissionError("Open-access full-text retrieval requires HRP_ALLOW_PUBLIC_FULLTEXT_LOOKUP=YES.")


def _fetch(url: str, *, max_bytes: int = MAX_XML_BYTES) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "www.ebi.ac.uk" or not parsed.path.startswith("/europepmc/webservices/rest/"):
        raise OpenAccessError("Only fixed Europe PMC REST endpoints are permitted.")
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    try:
        request = Request(url, headers={"Accept": "application/xml, application/json",
                                        "User-Agent": "HRP-ResearchFactory/0.1 (open-access only)"})
        with build_opener(NoRedirect).open(request, timeout=12) as response:
            payload = response.read(max_bytes + 1)
    except (HTTPError, URLError, OSError, TimeoutError) as exc:
        raise OpenAccessError("Europe PMC did not provide an accessible open-access response.") from exc
    if len(payload) > max_bytes:
        raise OpenAccessError("Europe PMC payload exceeds the configured limit.")
    return payload


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _element_text(node: ET.Element | None) -> str:
    return " ".join("".join(node.itertext()).split()) if node is not None else ""


def _jats_article(xml_data: bytes, requested_doi: str) -> tuple[str, str, str]:
    if b"<!DOCTYPE" in xml_data.upper() or b"<!ENTITY" in xml_data.upper():
        raise OpenAccessError("Unsafe XML entity/DOCTYPE encountered.")
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as exc:
        raise OpenAccessError("Malformed JATS full text.") from exc
    if _local(root.tag) != "article":
        raise OpenAccessError("Full text is not a JATS article.")
    ids = [_element_text(x) for x in root.iter() if _local(x.tag) == "article-id"
           and x.attrib.get("pub-id-type", "").lower() == "doi"]
    if not ids or requested_doi not in [normalise_doi(i) for i in ids]:
        raise OpenAccessError("Full-text article DOI does not match the selected candidate.")
    names = [_element_text(x) for x in root.iter() if _local(x.tag) == "article-title"]
    title = next((x for x in names if x), "")
    if not title:
        raise OpenAccessError("Full text has no usable title.")
    licences = [_element_text(x) for x in root.iter() if _local(x.tag) == "license"]
    licence_note = next((x for x in licences if x), "Licence terms not supplied in extracted JATS; review required.")
    bodies = [x for x in root.iter() if _local(x.tag) == "body"]
    if not bodies:
        raise OpenAccessError("Full text contains no article body.")
    # Extract article-body sections and paragraphs, not references.
    sections = []
    for node in bodies[0].iter():
        if _local(node.tag) in {"title", "p"}:
            txt = _element_text(node)
            if txt:
                sections.append(txt)
    body = "\n\n".join(sections)
    if len(body) < 80:
        raise OpenAccessError("Full-text body is too short for interpretation.")
    # Protect local prompts and storage: retain a bounded extract only.
    prefix = f"# {title}\n\nDOI: {requested_doi}\n\n"
    raw = (prefix + body).encode("utf-8")[:MAX_SOURCE_BYTES]
    trimmed = raw.decode("utf-8", errors="ignore")
    return title, trimmed, licence_note[:1200]


def import_europepmc_source(
    contract: PublicationContract, candidates_path: str | Path, source_id: str,
    out_dir: str | Path, *, fetch=None,
) -> Path:
    """Return a new local source bundle manifest; never publish or upload text."""
    require_open_access_opt_in()
    seed, _ = load_candidate_seed(candidates_path, contract)
    matches = [x for x in seed["candidate_sources"] if x["source_id"] == source_id]
    if len(matches) != 1:
        raise OpenAccessError("Select one known candidate source ID.")
    doi = normalise_doi(matches[0]["doi"])
    getter = fetch or _fetch
    url = BASE + "search?" + urlencode({
        "query": 'DOI:"' + doi + '"',
        "format": "json", "resultType": "core", "pageSize": "5",
    })
    try:
        data = json.loads(getter(url, max_bytes=300_000))
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
        raise OpenAccessError("Europe PMC search response is not JSON.") from exc
    hits = (data.get("resultList") or {}).get("result") if isinstance(data, dict) else None
    if not isinstance(hits, list):
        raise OpenAccessError("Search result list missing.")
    eligible = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        try:
            matching = normalise_doi(hit.get("doi", "")) == doi
        except ValueError:
            matching = False
        if (matching and hit.get("inEPMC") == "Y" and hit.get("isOpenAccess") == "Y"
                and hit.get("isRetracted", "N") != "Y"
                and isinstance(hit.get("pmcid"), str) and PMCID_RE.fullmatch(hit["pmcid"])):
            eligible.append(hit)
    if len(eligible) != 1:
        raise OpenAccessError("No unique eligible non-retracted Europe PMC open-access article.")
    pmcid = eligible[0]["pmcid"]
    xml = getter(BASE + pmcid + "/fullTextXML", max_bytes=MAX_XML_BYTES)
    title, text, licence = _jats_article(xml, doi)
    root = Path(out_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    dest = root / (source_id + ".txt")
    manifest = root / "source-bundle.json"
    if dest.exists() or manifest.exists():
        raise OpenAccessError("Refusing to overwrite an existing source bundle.")
    raw = text.encode("utf-8")
    dest.write_bytes(raw)
    obj = {
        "schema_version": "hrp-local-source-bundle-v0.1",
        "paper_id": contract.paper_id,
        "sources": [{
            "source_id": source_id,
            "doi": doi,
            "title": title,
            "file": dest.name,
            "sha256": sha256(raw).hexdigest(),
            "access_basis": "europe_pmc_open_access",
            "data_tier": "restricted_local",
            "hosted_approved": False,
        }],
    }
    manifest.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    # Local provenance only: never expose private/full source to GitHub Actions.
    (root / "source-import-notes.json").write_text(json.dumps({
        "provider": "Europe PMC",
        "pmcid": pmcid,
        "doi": doi,
        "fulltext_xml_sha256": sha256(xml).hexdigest(),
        "source_excerpt_sha256": sha256(raw).hexdigest(),
        "licence_note_unverified": licence,
        "rights_status": "human_review_required_before_hosted_use_or_public_release",
    }, indent=2) + "\n", encoding="utf-8")
    return manifest
