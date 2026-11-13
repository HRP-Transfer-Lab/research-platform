"""Actual Agno A02/A03/A04 constructor checks without making inference calls."""

from pathlib import Path

import pytest

from hrp_research_factory.contracts import PublicationContract
from hrp_research_factory.grounded_agents import make_grounded_agno_agents

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("provider", ["openai", "ollama"])
def test_three_grounded_agents_construct_without_tools(provider, monkeypatch):
    pytest.importorskip("agno")
    c = PublicationContract.from_file(ROOT / "configs" / "TG-COMP-001.json")
    monkeypatch.setenv("HRP_ALLOW_MODEL_CALLS", "YES")
    monkeypatch.setenv("OPENAI_API_KEY", "construction-only-do-not-send")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    agents = make_grounded_agno_agents(c, provider, model_id="not-executed-test-model")
    assert set(agents) == {"A02", "A03", "A04"}
    assert len({a.name for a in agents.values()}) == 3
    for agent in agents.values():
        assert not agent.tools
        assert agent.output_schema is not None
        assert agent.retries == 0
