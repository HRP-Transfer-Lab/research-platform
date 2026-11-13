"""Deterministic scholarly API tests; no real HTTP access."""

import pytest

from hrp_research_factory.evidence_sources import (
    MetadataResult, SourceMetadataError, _bounded_json_http, compare_metadata,
    crossref_metadata, normalise_doi, openalex_metadata, require_network_opt_in,
)


def test_doi_normalisation_and_safe_rejection():
    assert normalise_doi("https://doi.org/10.1016/j.TiCS.2017.10.001") == "10.1016/j.tics.2017.10.001"
    assert normalise_doi("DOI:10.1038/ncomms3521") == "10.1038/ncomms3521"
    for bad in ["main", "https://evil.com/x", "10.1016/foo?api_key=SECRET", "10.1234/a b", "10.1234/../../a", ""]:
        with pytest.raises(SourceMetadataError):
            normalise_doi(bad)


def test_m1_default_blocks_public_metadata_network(monkeypatch):
    monkeypatch.delenv("HRP_ALLOW_PUBLIC_METADATA_LOOKUP", raising=False)
    with pytest.raises(PermissionError):
        require_network_opt_in()
    monkeypatch.setenv("HRP_ALLOW_PUBLIC_METADATA_LOOKUP", "True")
    with pytest.raises(PermissionError):
        require_network_opt_in()
    monkeypatch.setenv("HRP_ALLOW_PUBLIC_METADATA_LOOKUP", "YES")
    require_network_opt_in()


def test_crossref_matches_doi_and_preserves_bounded_metadata():
    def fake_fetch(url, headers):
        assert url.startswith("https://api.crossref.org/works/")
        assert headers["Accept"] == "application/json"
        return {
            "message": {
                "DOI": "10.1038/ncomms3521",
                "title": ["Griffiths phases and the stretching of criticality in brain networks"],
                "author": [{"given": "Paolo", "family": "Moretti"}],
                "published": {"date-parts": [[2013, 10, 3]]},
                "container-title": ["Nature Communications"],
                "type": "journal-article",
                "URL": "https://doi.org/10.1038/ncomms3521",
            }
        }, "b" * 64

    result = crossref_metadata("10.1038/ncomms3521", fetch=fake_fetch)
    assert result.status == "metadata_found"
    assert result.year == 2013 and result.authors == ("Paolo Moretti",)
    assert result.to_dict()["claim_support_verified"] is False
    assert result.to_dict()["original_full_text_checked"] is False


def test_openalex_metadata_doi_cross_check_and_no_key_exposure(monkeypatch):
    monkeypatch.setenv("OPENALEX_API_KEY", "SECRET_API_KEY_MUST_NOT_PERSIST")
    def fake_fetch(url, headers):
        assert url.startswith("https://api.openalex.org/works/https://doi.org/")
        assert "SECRET_API_KEY_MUST_NOT_PERSIST" not in url
        assert headers["Authorization"] == "Bearer SECRET_API_KEY_MUST_NOT_PERSIST"
        return {
            "doi": "https://doi.org/10.1038/ncomms3521",
            "title": "Griffiths phases and the stretching of criticality in brain networks",
            "publication_year": 2013,
            "authorships": [{"author": {"display_name": "Paolo Moretti"}}],
            "primary_location": {"source": {"display_name": "Nature Communications"}},
            "type": "article",
        }, "a" * 64
    result = openalex_metadata("10.1038/ncomms3521", fetch=fake_fetch)
    assert result.status == "metadata_found"
    assert "SECRET_API_KEY_MUST_NOT_PERSIST" not in str(result.to_dict())
    assert result.venue == "Nature Communications"


def test_mismatched_metadata_fails_closed():
    bad = crossref_metadata("10.1038/ncomms3521", fetch=lambda *_: (
        {"message": {"DOI": "10.5555/another-record", "title": ["False identity"]}}, "x" * 64))
    assert bad.status == "unresolved"
    assert bad.title is None
    assert "different DOI" in (bad.error or "")


def test_comparison_never_proves_theoretical_support():
    good = MetadataResult("crossref", "10.1234/test", "metadata_found", "Trial result",
                          "10.1234/test", 2025, (), None, None, None, "a" * 64)
    also = MetadataResult("openalex", "10.1234/test", "metadata_found", "Trial result!",
                          "10.1234/test", 2025, (), None, None, None, "b" * 64)
    assert compare_metadata(good, also) == "doi_metadata_consistent"
    changed = MetadataResult("openalex", "10.1234/test", "metadata_found", "Entirely different",
                             "10.1234/test", 2025, (), None, None, None, "b" * 64)
    assert compare_metadata(good, changed) == "title_needs_human_check"
    unresolved = MetadataResult("openalex", "10.1234/test", "unresolved", None,
                                None, None, (), None, None, None, None)
    assert compare_metadata(good, unresolved) == "not_cross_checked"


def test_metadata_clients_do_not_fetch_arbitrary_urls():
    with pytest.raises(SourceMetadataError):
        _bounded_json_http("https://example.com/data", {})
    with pytest.raises(SourceMetadataError):
        _bounded_json_http("http://api.crossref.org/works/10.1234/x", {})
    with pytest.raises(SourceMetadataError):
        _bounded_json_http("https://api.crossref.org.evil.org/works/10.1234/x", {})
