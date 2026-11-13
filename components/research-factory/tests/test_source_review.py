"""M1b original-text source review: fictional fixture only, no model/API calls."""

from hashlib import sha256
import json
from pathlib import Path

import pytest

from hrp_research_factory.cli import main
from hrp_research_factory.contracts import PublicationContract
from hrp_research_factory.source_packets import (
    SourcePacketError, check_exact_quote, load_local_source_bundle,
)
from hrp_research_factory.source_review import SourceReviewError, run_source_review

BASE = Path(__file__).resolve().parents[1]
CONTRACT = BASE / "configs" / "TG-COMP-001.json"
SEED = BASE / "configs" / "TG-COMP-001-evidence-candidates.json"
EXACT = "In this invented test world, a controller can switch strategies when the rules change."
ALTERNATIVE = "A smooth Bayesian controller can also detect that change without invoking a cusp."

FICTIONAL = (
    "# FICTIONAL TEST SOURCE — NOT A SCIENTIFIC PUBLICATION\n\n"
    "This is an invented local demonstration. It is NOT the article identified by the "
    "candidate DOI and cannot support any real-world scientific or medical conclusions.\n\n"
    + EXACT + "\n\n" + ALTERNATIVE + "\n\n"
    "The toy model changes context when a counter changes from zero to one. "
    "The outcome is wholly constructed for software testing and is not participant data.\n"
)


@pytest.fixture()
def contract():
    return PublicationContract.from_file(CONTRACT)


@pytest.fixture()
def bundle(tmp_path):
    source = tmp_path / "SRC-004.txt"
    source.write_text(FICTIONAL, encoding="utf-8")
    manifest = {
        "schema_version": "hrp-local-source-bundle-v0.1",
        "paper_id": "TG-COMP-001",
        "sources": [{
            "source_id": "SRC-004",
            "doi": "10.1038/ncomms3521",
            "title": "FICTIONAL TEST SOURCE — NOT A PUBLICATION",
            "file": "SRC-004.txt",
            "sha256": sha256(source.read_bytes()).hexdigest(),
            "access_basis": "authorised_user_copy",
            "data_tier": "restricted_local",
            "hosted_approved": False,
        }],
    }
    path = tmp_path / "source-bundle.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def manifest_edit(path, edit):
    item = json.loads(path.read_text(encoding="utf-8"))
    edit(item)
    path.write_text(json.dumps(item), encoding="utf-8")


def test_local_packet_hash_and_quote_anchor(bundle, contract):
    docs, manifest_sha = load_local_source_bundle(contract, SEED, bundle)
    assert len(docs) == 1
    assert len(manifest_sha) == 64
    d = docs[0]
    assert d.doi == "10.1038/ncomms3521"
    assert d.safe_record()["source_identity_externally_verified"] is False
    assert "original_path" not in d.prompt_record()
    ok = check_exact_quote(d, EXACT)
    assert ok["status"] == "exact_match"
    assert d.body[ok["char_start"]:ok["char_end"]] == EXACT
    assert ok["content_relation_to_claim"] == "NOT_SEMANTICALLY_VERIFIED"
    assert check_exact_quote(d, EXACT.replace("controller", "cusp model"))["status"] == "rejected"


def test_local_packet_refuses_modified_source(bundle, contract):
    src = bundle.parent / "SRC-004.txt"
    src.write_text(FICTIONAL + "SECRET MODIFIED AFTER HASH\n")
    with pytest.raises(SourcePacketError, match="hash"):
        load_local_source_bundle(contract, SEED, bundle)


def test_source_packet_refuses_path_escapes_and_duplicate_source(bundle, contract):
    manifest_edit(bundle, lambda d: d["sources"][0].update(file="../other.txt"))
    with pytest.raises(SourcePacketError):
        load_local_source_bundle(contract, SEED, bundle)


def test_source_packet_refuses_hosted_approval_for_private_material(bundle, contract):
    manifest_edit(bundle, lambda d: d["sources"][0].update(hosted_approved=True))
    with pytest.raises(SourcePacketError):
        load_local_source_bundle(contract, SEED, bundle)


def test_default_review_is_offline_and_does_not_expose_text(bundle, contract, tmp_path, monkeypatch):
    monkeypatch.delenv("HRP_ALLOW_MODEL_CALLS", raising=False)
    folder = run_source_review(contract, SEED, bundle, tmp_path / "runs")
    inventory = json.loads((folder / "source_review" / "source_manifest.json").read_text())
    assert inventory["mode"] == "source_inventory_only"
    assert inventory["sources"][0]["sha256"]
    assert "original_path" not in str(inventory)
    assert "In this invented test world" not in str(inventory)
    quotes = json.loads((folder / "source_review" / "quote_audit.json").read_text())
    assert quotes["accepted"] == [] and quotes["human_review"] == "PENDING"
    assert "NO SCIENTIFIC APPROVAL" in (folder / "source_review" / "REVIEW.md").read_text()


def test_model_run_denied_without_optin_and_hosted_private_blocked(bundle, contract, tmp_path, monkeypatch):
    monkeypatch.delenv("HRP_ALLOW_MODEL_CALLS", raising=False)
    with pytest.raises(PermissionError):
        run_source_review(contract, SEED, bundle, tmp_path / "runs", run_agents=True)
    assert not list((tmp_path / "runs").rglob("run_manifest.json"))
    monkeypatch.setenv("HRP_ALLOW_MODEL_CALLS", "YES")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-no-execution")
    with pytest.raises(PermissionError):
        run_source_review(contract, SEED, bundle, tmp_path / "runs",
                          run_agents=True, provider="openai")
    assert not list((tmp_path / "runs").rglob("run_manifest.json"))


def _proposer(role, payload):
    if role == "A02":
        assert payload["sources"][0]["text"].startswith("# FICTIONAL")
        return {"source_ids": ["SRC-004"], "coverage_gaps": ["Only fictional text was supplied."]}
    if role == "A03":
        return {"passages": [
            {"source_id": "SRC-004", "claim_id": "TG-COMP-001-C02",
             "quote": EXACT, "interpretation": "A toy controller can switch.",
             "proposed_relation": "contextualises"},
            {"source_id": "SRC-004", "claim_id": "TG-COMP-001-C02",
             "quote": "An invented quote that does not exist in the provided source.",
             "interpretation": "Fabricated statement must be rejected.",
             "proposed_relation": "supports"},
        ]}
    if role == "A04":
        assert len(payload["exact_quote_candidates"]) == 1
        assert payload["exact_quote_candidates"][0]["passage_id"] == "Q001"
        return {"comments": [
            {"claim_id": "TG-COMP-001-C02", "passage_ids": ["Q001"],
             "alternative_explanation": "A smooth controller is a rival.",
             "assessment": "This toy case cannot distinguish models."}
        ], "unaddressed_questions": ["Where is the real experimental evidence?"]}
    raise AssertionError("Unknown role")


def test_three_step_agent_sequence_is_quote_gated(bundle, contract, tmp_path, monkeypatch):
    monkeypatch.setenv("HRP_ALLOW_MODEL_CALLS", "YES")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    folder = run_source_review(contract, SEED, bundle, tmp_path / "runs",
                               run_agents=True, provider="ollama", runner=_proposer)
    checks = json.loads((folder / "source_review" / "quote_audit.json").read_text())
    assert len(checks["accepted"]) == 1
    assert len(checks["rejected"]) == 1
    assert checks["accepted"][0]["quote"] == EXACT
    assert checks["accepted"][0]["human_review"] == "PENDING"
    rival = json.loads((folder / "source_review" / "rival_analysis.json").read_text())
    assert len(rival["comments"]) == 1
    assert rival["status"] == "UNVERIFIED_MODEL_INTERPRETATION"
    assert rival["human_review"] == "PENDING"
    assert (folder / "source_review" / "run_provenance.json").is_file()


def test_model_cannot_invent_passage_reference(bundle, contract, tmp_path, monkeypatch):
    monkeypatch.setenv("HRP_ALLOW_MODEL_CALLS", "YES")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    def injected(role, payload):
        if role == "A04":
            return {"comments": [
                {"claim_id":"TG-COMP-001-C02","passage_ids":["Q999"],
                 "alternative_explanation":"A rival","assessment":"Cannot cite missing quote"}
            ]}
        return _proposer(role, payload)
    with pytest.raises(SourceReviewError, match="invented or misattributed"):
        run_source_review(contract, SEED, bundle, tmp_path / "runs",
                          run_agents=True, provider="ollama", runner=injected)
    assert not list((tmp_path / "runs").rglob("run_manifest.json"))


def test_fabricated_quotes_are_not_sent_to_rival_analyst(bundle, contract, tmp_path, monkeypatch):
    monkeypatch.setenv("HRP_ALLOW_MODEL_CALLS", "YES")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    roles = []
    def bogus(role, payload):
        roles.append(role)
        if role == "A03":
            return {"passages": [
                {"source_id": "SRC-004", "claim_id": "TG-COMP-001-C02",
                 "quote": "A fabricated quote invented by the language model without source basis.",
                 "interpretation": "Bogus finding",
                 "proposed_relation": "supports"}
            ]}
        return _proposer(role, payload)
    folder = run_source_review(contract, SEED, bundle, tmp_path / "runs",
                               run_agents=True, provider="ollama", runner=bogus)
    assert roles == ["A02", "A03"]
    review = json.loads((folder / "source_review" / "rival_analysis.json").read_text())
    assert review["comments"] == []
    assert any("No agent-proposed passage" in line for line in review["coverage_gaps"])


def test_cli_default_source_review_is_offline(bundle, tmp_path, capsys):
    args = ["source-review", str(CONTRACT), "--candidates", str(SEED),
            "--source-bundle", str(bundle), "--out", str(tmp_path / "out")]
    assert main(args) == 0
    assert "PENDING" in capsys.readouterr().out
    assert len(list((tmp_path / "out").rglob("source_manifest.json"))) == 1
