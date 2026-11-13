"""Opt-in Agno drafting workflow; model outputs are unverified proposals.

No GitHub, shell, browser, publication, email or data-access tools are granted.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

from .contracts import PublicationContract

ALLOWED_PROVIDERS = ("openai", "ollama")


def assert_model_calls_permitted(contract: PublicationContract, provider: str) -> None:
    if os.getenv("HRP_ALLOW_MODEL_CALLS", "NO") != "YES":
        raise PermissionError("Model calls are disabled. Set HRP_ALLOW_MODEL_CALLS=YES explicitly.")
    if provider not in ALLOWED_PROVIDERS:
        raise ValueError("Provider must be openai or ollama.")
    if contract.data_tier == "restricted_local" and provider != "ollama":
        raise PermissionError("Restricted-local sources must not be sent to hosted providers.")
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        raise PermissionError("Hosted inference requires an explicitly configured OPENAI_API_KEY.")
    if provider == "ollama":
        host = urlparse(os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).hostname
        if host not in {"localhost", "127.0.0.1", "::1"}:
            raise PermissionError("M0 local Ollama must use a loopback address.")


def build_agno_workflow(
    contract: PublicationContract,
    provider: str,
    model_id: str | None = None,
    db_file: str | Path = "runs/agno_drafts.db",
):
    """Build a three-role Agno workflow; callers must separately opt in to .run()."""
    assert_model_calls_permitted(contract, provider)
    try:
        from agno.agent import Agent
        from agno.db.sqlite import SqliteDb
        from agno.workflow import Workflow
        if provider == "ollama":
            from agno.models.ollama import Ollama
            model = Ollama(
                id=model_id or os.getenv("HRP_LOCAL_MODEL_ID", "gemma4:e2b-it-q4_K_M"),
                host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
                api_key=None,
            )
        else:
            from agno.models.openai import OpenAIResponses
            model = OpenAIResponses(id=model_id or "gpt-5.5")
    except ImportError as exc:
        raise RuntimeError("Install the optional agents extra: pip install -e '.[agents]'") from exc

    db_file = Path(db_file)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    db = SqliteDb(db_file=str(db_file))
    # No tools means no write, fetch or publication effects; sources are NOT verified.
    scope = Agent(
        name="Research Director (scope only)",
        model=model,
        instructions=[
            "Produce a narrow publication proposal based only on the supplied contract.",
            "Treat Trident-G as a hypothesis bank, never as proof.",
            "Identify the primary explanandum and what evidence would disconfirm the claim.",
            "Do not invent DOI, citations, experiments or results.",
            "You have no permission to publish, edit code or change frozen protocols.",
        ],
    )
    formal = Agent(
        name="Formaliser (proposal only)",
        model=model,
        instructions=[
            "State the minimum executable or arguable mechanism and fair rivals.",
            "For philosophical projects, make an explicit argument map and counterarguments.",
            "For computational projects, distinguish synthetic identifiability from real human validity.",
            "Do not assert that evidence was fetched or model code run.",
        ],
    )
    reviewer = Agent(
        name="Independent Critical Reviewer (proposal only)",
        model=model,
        instructions=[
            "Critique assumptions and ambiguous claims; specify rival theories and failure conditions.",
            "Flag every unverified citation as 'verification needed'.",
            "Do not certify or approve any result; request PI decision at the end.",
        ],
    )
    return Workflow(
        name=f"HRP {contract.paper_id} research draft (unverified)",
        steps=[scope, formal, reviewer],
        db=db,
    )


def run_unverified_draft(
    contract: PublicationContract,
    provider: str,
    model_id: str | None = None,
    db_file: str | Path = "runs/agno_drafts.db",
) -> str:
    """Actually invoke an optional model only following explicit environment opt-in."""
    workflow = build_agno_workflow(contract, provider, model_id, db_file=db_file)
    prompt = (
        "UNVERIFIED RESEARCH PROPOSAL; DO NOT CITE OR SUBMIT AS AN EMPIRICAL RESULT.\n"
        + str(contract.canonical_payload())
        + "\nReturn a concise plan with rival explanations, explicit uncertainties and PI approval gates."
    )
    response = workflow.run(input=prompt)
    return str(getattr(response, "content", response))
