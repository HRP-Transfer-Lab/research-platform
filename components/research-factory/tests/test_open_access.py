"""Fictional Europe PMC API fixtures. No HTTP requests or real article text."""

import json
from pathlib import Path

import pytest

from hrp_research_factory.contracts import PublicationContract
from hrp_research_factory.open_access import (
    OpenAccessError, _fetch, import_europepmc_source,
)
from hrp_research_factory.source_packets import load_local_source_bundle

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "TG-COMP-001.json"
SEED = ROOT / "configs" / "TG-COMP-001-evidence-candidates.json"
DOI = "10.1038/ncomms3521"

XML = b"""<?xml version="1.0" encoding="utf-8"?>
<article><front><article-meta>
<article-id pub-id-type="doi">10.1038/ncomms3521</article-id>
<title-group><article-title>Fictional open-access test article</article-title></title-group>
<permissions><license><license-p>This is only a synthetic licence fixture.</license-p></license></permissions>
</article-meta></front><body><sec><title>Test methods</title>
<p>In this completely synthetic test, virtual agents switch between states without any real participant data being collected.</p>
<p>In a second synthetic paragraph, a smooth control rule also identifies a change in the environment and no claim about people is warranted.</p>
</sec></body></article>"""


def contract():
    return PublicationContract.from_file(CONTRACT)


def fake_fetch(url, *, max_bytes):
    if "/search?" in url:
        return json.dumps({
            "resultList": {"result": [{
                "doi": DOI,
                "pmcid": "PMC12345678",
                "isOpenAccess": "Y",
                "inEPMC": "Y",
                "isRetracted": "N",
            }]}
        }).encode()
    if "/PMC12345678/fullTextXML" in url:
        return XML
    raise AssertionError(f"Unexpected URL: {url}")


def test_open_access_requires_network_opt_in(tmp_path, monkeypatch):
    monkeypatch.delenv("HRP_ALLOW_PUBLIC_FULLTEXT_LOOKUP", raising=False)
    with pytest.raises(PermissionError):
        import_europepmc_source(contract(), SEED, "SRC-004", tmp_path, fetch=fake_fetch)
    assert not list(tmp_path.glob("source-bundle.json"))


def test_imports_original_text_locally_without_hosted_permission(tmp_path, monkeypatch):
    monkeypatch.setenv("HRP_ALLOW_PUBLIC_FULLTEXT_LOOKUP", "YES")
    folder = tmp_path / "imports"
    manifest = import_europepmc_source(contract(), SEED, "SRC-004", folder, fetch=fake_fetch)
    obj = json.loads(manifest.read_text())
    assert len(obj["sources"]) == 1
    assert obj["sources"][0]["hosted_approved"] is False
    assert obj["sources"][0]["data_tier"] == "restricted_local"
    docs, _ = load_local_source_bundle(contract(), SEED, manifest)
    assert "Test methods" in docs[0].body
    assert docs[0].sha256 == obj["sources"][0]["sha256"]
    notes = json.loads((folder / "source-import-notes.json").read_text())
    assert notes["pmcid"] == "PMC12345678"
    assert notes["rights_status"].startswith("human_review_required")
    with pytest.raises(OpenAccessError, match="overwrite"):
        import_europepmc_source(contract(), SEED, "SRC-004", folder, fetch=fake_fetch)


def test_disallows_missing_oa_or_retracted_or_wrong_doi(tmp_path, monkeypatch):
    monkeypatch.setenv("HRP_ALLOW_PUBLIC_FULLTEXT_LOOKUP", "YES")
    for update in ({"isOpenAccess": "N"}, {"isRetracted": "Y"}, {"doi": "10.1000/not-same"}):
        def altered(url, *, max_bytes):
            if "/search?" not in url:
                raise AssertionError("Must refuse before fulltext.")
            item = {"doi": DOI, "pmcid": "PMC12345678", "isOpenAccess": "Y", "inEPMC": "Y"}
            item.update(update)
            return json.dumps({"resultList": {"result": [item]}}).encode()
        with pytest.raises(OpenAccessError, match="unique eligible"):
            import_europepmc_source(contract(), SEED, "SRC-004", tmp_path / "x", fetch=altered)


def test_rejects_wrong_xml_article_doi(tmp_path, monkeypatch):
    monkeypatch.setenv("HRP_ALLOW_PUBLIC_FULLTEXT_LOOKUP", "YES")
    def wrong(url, *, max_bytes):
        return XML.replace(b"10.1038/ncomms3521", b"10.0000/wrong") if "/fullTextXML" in url else fake_fetch(url, max_bytes=max_bytes)
    with pytest.raises(OpenAccessError, match="does not match"):
        import_europepmc_source(contract(), SEED, "SRC-004", tmp_path / "wrong", fetch=wrong)


def test_disallows_doctype_and_external_hosts():
    with pytest.raises(OpenAccessError, match="host"):
        _fetch("https://example.com/articles/fullTextXML")
    from hrp_research_factory.open_access import _jats_article
    with pytest.raises(OpenAccessError, match="DOCTYPE"):
        _jats_article(b"<!DOCTYPE foo><article></article>", DOI)
