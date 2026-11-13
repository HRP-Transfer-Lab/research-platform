"""M0 workflow is deterministic, auditable and blocked from publication."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from hrp_research_factory.cli import main
from hrp_research_factory.contracts import ContractError, PublicationContract
from hrp_research_factory.agno_workflow import assert_model_calls_permitted
from hrp_research_factory.pipeline import FORBIDDEN, build_dossier, write_run

SAMPLE = Path(__file__).resolve().parents[1] / "configs" / "TG-COMP-001.json"


def sample_contract():
    return PublicationContract.from_file(SAMPLE)


def test_dossier_is_stable_and_requires_scope_review():
    c = sample_contract()
    a = build_dossier(c)
    b = build_dossier(c)
    assert a == b
    assert a["status"] == "awaiting_scope_approval"
    assert a["model_calls_enabled"] is False
    assert a["agent_permission"] == "propose_only"
    assert a["claim_status"] == "hypothesis"
    assert a["contract_sha256"] == c.fingerprint()
    assert set(FORBIDDEN).issubset(a["forbidden_actions"])


def test_write_run_does_not_publish_or_change_sources(tmp_path):
    c = sample_contract()
    folder = write_run(c, tmp_path)
    manifest = json.loads((folder / "run_manifest.json").read_text())
    packet = (folder / "review_packet.md").read_text()
    assert manifest["pinned_source"]["commit"] == c.source_commit
    assert manifest["pending_approval"].startswith("Human PI")
    assert manifest["status"] == "awaiting_scope_approval"
    assert "UNVERIFIED PROPOSAL" in packet
    assert c.primary_hypothesis in packet
    assert "model_free_reinforcement_learning" in packet
    assert len(list(folder.glob("*"))) == 2


def test_two_runs_are_separate_and_stable_in_scientific_fields(tmp_path):
    c = sample_contract()
    a = write_run(c, tmp_path)
    b = write_run(c, tmp_path)
    assert a != b
    ja = json.loads((a / "run_manifest.json").read_text())
    jb = json.loads((b / "run_manifest.json").read_text())
    for transient in ("run_id", "created_at_utc"):
        ja.pop(transient)
        jb.pop(transient)
    assert ja == jb


def test_cli_validates_and_kicks_off_offline(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("HRP_ALLOW_MODEL_CALLS", raising=False)
    assert main(["validate", str(SAMPLE)]) == 0
    assert "VALID" in capsys.readouterr().out
    assert main(["kickoff", str(SAMPLE), "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "PROPOSAL ONLY" in out
    assert len(list(tmp_path.glob("TG-COMP-001/*/run_manifest.json"))) == 1


def test_live_agno_is_denied_before_any_optional_import(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("HRP_ALLOW_MODEL_CALLS", raising=False)
    assert main(["agno-draft", str(SAMPLE), "--out", str(tmp_path)]) == 2
    assert "BLOCKED" in capsys.readouterr().err
    assert list(tmp_path.rglob("*.db")) == []
    assert list(tmp_path.rglob("run_manifest.json")) == []


def test_hosted_calls_require_nonrestricted_data_and_key(monkeypatch):
    c = sample_contract()
    monkeypatch.setenv("HRP_ALLOW_MODEL_CALLS", "YES")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(PermissionError):
        assert_model_calls_permitted(c, "openai")
    item = deepcopy(c.canonical_payload())
    item["data_tier"] = "restricted_local"
    restricted = PublicationContract.from_dict(item)
    monkeypatch.setenv("OPENAI_API_KEY", "this_is_not_a_real_key")
    with pytest.raises(PermissionError):
        assert_model_calls_permitted(restricted, "openai")
    monkeypatch.setenv("OLLAMA_HOST", "http://example.com:11434")
    with pytest.raises(PermissionError):
        assert_model_calls_permitted(restricted, "ollama")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    assert_model_calls_permitted(restricted, "ollama")


def test_no_model_calls_when_flag_is_not_exactly_yes(monkeypatch):
    monkeypatch.setenv("HRP_ALLOW_MODEL_CALLS", "True")
    with pytest.raises(PermissionError):
        assert_model_calls_permitted(sample_contract(), "ollama")
