"""Real Agno SDK construction smoke tests: no model run and no network calls."""

import pytest

from hrp_research_factory.agno_workflow import build_agno_workflow
from hrp_research_factory.contracts import PublicationContract

SAMPLE = __import__("pathlib").Path(__file__).resolve().parents[1] / "configs" / "TG-COMP-001.json"


def test_hosted_agno_workflow_construction_no_model_execution(tmp_path, monkeypatch):
    pytest.importorskip("agno")
    contract = PublicationContract.from_file(SAMPLE)
    monkeypatch.setenv("HRP_ALLOW_MODEL_CALLS", "YES")
    monkeypatch.setenv("OPENAI_API_KEY", "offline-construction-test-not-a-real-key")
    workflow = build_agno_workflow(contract, "openai", db_file=tmp_path / "state.db")
    assert "TG-COMP-001" in workflow.name
    assert len(workflow.steps) == 3
    assert all(len(agent.tools or []) == 0 for agent in workflow.steps)


def test_local_ollama_workflow_construction_needs_no_running_server(tmp_path, monkeypatch):
    pytest.importorskip("agno")
    contract = PublicationContract.from_file(SAMPLE)
    monkeypatch.setenv("HRP_ALLOW_MODEL_CALLS", "YES")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    workflow = build_agno_workflow(contract, "ollama", model_id="does-not-need-to-exist", db_file=tmp_path / "local_state.db")
    assert len(workflow.steps) == 3
    assert all(len(agent.tools or []) == 0 for agent in workflow.steps)
