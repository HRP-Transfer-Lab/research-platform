"""M1 vertical-slice tests; operate only on temporary files, never external services."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from hrp_research_factory.cli import main
from hrp_research_factory.contracts import PublicationContract
from hrp_research_factory.evidence_pipeline import (
    EvidenceDossierError, load_candidate_seed, produce_evidence_dossier,
)
from hrp_research_factory.evidence_sources import MetadataResult
from hrp_research_factory.registry_reader import RegistrySnapshotError, inspect_public_release

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "TG-COMP-001.json"
SEED = ROOT / "configs" / "TG-COMP-001-evidence-candidates.json"


def contract():
    return PublicationContract.from_file(CONTRACT)


def seed_json():
    return json.loads(SEED.read_text(encoding="utf-8"))


def make_seed(tmp_path, item):
    target = tmp_path / "seed.json"
    target.write_text(json.dumps(item), encoding="utf-8")
    return target


def test_seed_is_candidate_only_and_scoped():
    item, digest = load_candidate_seed(SEED, contract())
    assert item["paper_id"] == "TG-COMP-001"
    assert len(item["candidate_sources"]) == 6
    assert len(digest) == 64
    assert all(source["role"] != "proves_the_claim" for source in item["candidate_sources"])


def test_seed_rejects_unsupported_claims_or_fabricated_status(tmp_path):
    item = seed_json()
    item["status"] = "full_text_verified"
    with pytest.raises(EvidenceDossierError):
        load_candidate_seed(make_seed(tmp_path, item), contract())
    item = seed_json()
    item["candidate_sources"][0]["role"] = "proof"
    with pytest.raises(EvidenceDossierError):
        load_candidate_seed(make_seed(tmp_path, item), contract())
    item = seed_json()
    item["claims"][0]["status"] = "published_fact"
    with pytest.raises(EvidenceDossierError):
        load_candidate_seed(make_seed(tmp_path, item), contract())


def test_seed_rejects_duplicate_doi_unknown_claim_and_bad_id(tmp_path):
    for mod in (
        lambda x: x["candidate_sources"][1].update(doi=x["candidate_sources"][0]["doi"]),
        lambda x: x["candidate_sources"][0].update(claim_id="TG-COMP-001-C99"),
        lambda x: x["candidate_sources"][0].update(source_id="SRC-001/../../x"),
    ):
        item = seed_json()
        mod(item)
        with pytest.raises(EvidenceDossierError):
            load_candidate_seed(make_seed(tmp_path, item), contract())


def test_offline_dossier_is_reviewable_and_never_autocertifies(tmp_path, monkeypatch):
    monkeypatch.delenv("HRP_ALLOW_PUBLIC_METADATA_LOOKUP", raising=False)
    folder = produce_evidence_dossier(contract(), SEED, tmp_path)
    m = json.loads((folder / "evidence" / "evidence_matrix.json").read_text())
    assert len(m["sources"]) == 6 and len(m["claims"]) == 3
    assert m["evidence_gate"] == "ALL_SOURCE_CLAIMS_UNRESOLVED"
    assert all(not s["original_full_text_checked"] for s in m["sources"])
    assert all(s["claim_support_status"] == "NOT_EVALUATED" for s in m["sources"])
    assert all(not c["human_approval"] for c in m["claims"])
    assert not (folder / "evidence" / "bibliography.bib").read_text().count("@article")
    assert "INSUFFICIENT EVIDENCE" in (folder / "evidence" / "unresolved_claims.md").read_text()
    manifest = json.loads((folder / "manifests" / "retrieval_and_version.json").read_text())
    assert manifest["retrieval_mode"] == "offline_candidates_only"
    assert manifest["theory_source_commit_checked_by_this_runtime"] is False
    assert manifest["independent_claim_support_verified"] is False
    assert "A03 Source Verifier" in (folder / "review" / "evidence_approval.md").read_text()


def test_offline_dossiers_keep_same_science_data_across_runs(tmp_path):
    a = produce_evidence_dossier(contract(), SEED, tmp_path)
    b = produce_evidence_dossier(contract(), SEED, tmp_path)
    assert a != b
    assert (a / "evidence" / "evidence_matrix.json").read_bytes() == (
        b / "evidence" / "evidence_matrix.json").read_bytes()
    assert (a / "evidence" / "competing_theories.md").read_bytes() == (
        b / "evidence" / "competing_theories.md").read_bytes()


def test_metadata_network_requires_explicit_flag_and_approved_data_tier(tmp_path, monkeypatch):
    monkeypatch.delenv("HRP_ALLOW_PUBLIC_METADATA_LOOKUP", raising=False)
    with pytest.raises(PermissionError):
        produce_evidence_dossier(contract(), SEED, tmp_path, live_public_metadata=True)
    assert list(tmp_path.rglob("run_manifest.json")) == []
    monkeypatch.setenv("HRP_ALLOW_PUBLIC_METADATA_LOOKUP", "YES")
    item = contract().canonical_payload()
    item["data_tier"] = "restricted_local"
    restricted = PublicationContract.from_dict(item)
    with pytest.raises(PermissionError):
        produce_evidence_dossier(restricted, SEED, tmp_path, live_public_metadata=True)
    assert list(tmp_path.rglob("run_manifest.json")) == []


def test_metadata_lookup_cannot_certify_claim_support(tmp_path, monkeypatch):
    monkeypatch.setenv("HRP_ALLOW_PUBLIC_METADATA_LOOKUP", "YES")
    def fake(provider):
        def look(doi):
            return MetadataResult(
                provider, doi, "metadata_found", "Example peer-reviewed paper",
                doi, 2015, ("A. Person",), "A Journal", "journal-article",
                "https://doi.org/" + doi, "a" * 64)
        return look
    folder = produce_evidence_dossier(contract(), SEED, tmp_path, live_public_metadata=True,
                                      crossref_lookup=fake("crossref"), openalex_lookup=fake("openalex"))
    m = json.loads((folder / "evidence" / "evidence_matrix.json").read_text())
    assert all(s["metadata_consistency"] == "doi_metadata_consistent" for s in m["sources"])
    assert all(s["claim_support_status"] == "NOT_EVALUATED" for s in m["sources"])
    assert all(s["original_passage_locator"] is None for s in m["sources"])
    assert "@article" not in (folder / "evidence" / "bibliography.bib").read_text()


def test_registry_read_only_snapshot_and_release_mismatch(tmp_path):
    release = tmp_path / "public" / "2026-08-23"
    (release / "records").mkdir(parents=True)
    (release / "manifest.json").write_text(json.dumps(
        {"release_id":"2026-08-23","status":"approved_seed","record_count":1,"taxonomy_version":"test"}))
    record = {"release_id":"2026-08-23","record_id":"rt-000","bibliography":{"doi":"10.1038/ncomms3521"}}
    (release / "records" / "one.json").write_text(json.dumps(record))
    original = (release / "records" / "one.json").read_bytes()
    info = inspect_public_release(release)
    assert info["indexed_dois_to_record_ids"]["10.1038/ncomms3521"] == "rt-000"
    folder = produce_evidence_dossier(contract(), SEED, tmp_path / "runs", registry_release=release)
    matrix = json.loads((folder / "evidence" / "evidence_matrix.json").read_text())
    moretti = next(s for s in matrix["sources"] if s["doi"] == "10.1038/ncomms3521")
    assert moretti["existing_hrp_registry_record_id"] == "rt-000"
    assert moretti["claim_support_status"] == "NOT_EVALUATED"
    assert original == (release / "records" / "one.json").read_bytes()
    (release / "manifest.json").write_text(json.dumps(
        {"release_id":"2026-08-23","status":"approved_seed","record_count":2}))
    with pytest.raises(RegistrySnapshotError):
        inspect_public_release(release)


def test_cli_evidence_dossier_offline_only(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("HRP_ALLOW_PUBLIC_METADATA_LOOKUP", raising=False)
    args = ["evidence-dossier", str(CONTRACT), "--candidates", str(SEED),
            "--out", str(tmp_path)]
    assert main(args) == 0
    assert "UNRESOLVED" in capsys.readouterr().out
    assert len(list(tmp_path.rglob("evidence_matrix.json"))) == 1
    denied = [*args, "--public-metadata"]
    assert main(denied) == 2
    assert "BLOCKED" in capsys.readouterr().err
    assert len(list(tmp_path.rglob("evidence_matrix.json"))) == 1
