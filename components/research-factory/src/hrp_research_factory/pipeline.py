"""Offline, proposal-only research dossiers. This module has no publishing tools."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

from .contracts import PublicationContract

ROLES = {
    "computational": ["Research Director", "Evidence Librarian", "Theoretical Formaliser", "Computational Engineer", "Independent Reviewer"],
    "empirical_neuroscience": ["Research Director", "Evidence Librarian", "Neuroscience Specialist", "Statistical Auditor", "Independent Reviewer"],
    "learnability_transfer": ["Research Director", "Evidence Librarian", "Statistical Auditor", "Computational Engineer", "Independent Reviewer"],
    "shared_intentionality": ["Research Director", "Evidence Librarian", "Theoretical Formaliser", "Philosophical Reviewer", "Independent Reviewer"],
    "philosophical": ["Research Director", "Evidence Librarian", "Philosophy Specialist", "Adversarial Philosophical Reviewer", "Publication Editor"],
    "psychometric": ["Research Director", "Evidence Librarian", "Psychometric Specialist", "Statistical Auditor", "Independent Reviewer"],
}

FORBIDDEN = (
    "submit_preprint", "submit_journal", "publish_evidence",
    "push_to_canonical_theory", "modify_registered_protocol",
    "release_restricted_data", "send_email",
)


def build_dossier(contract: PublicationContract) -> dict:
    """Construct stable, inspectable workflow proposals; never call a model."""
    return {
        "schema_version": "hrp-factory-run-v0.1",
        "paper_id": contract.paper_id,
        "track": contract.track,
        "contract_sha256": contract.fingerprint(),
        "pinned_source": {
            "repository": contract.source_repo,
            "file": contract.source_path,
            "commit": contract.source_commit,
        },
        "primary_explanandum": contract.explanandum,
        "claim_status": contract.claim_status,
        "status": "awaiting_scope_approval",
        "agent_permission": "propose_only",
        "model_calls_enabled": False,
        "forbidden_actions": list(FORBIDDEN),
        "assigned_roles": ROLES[contract.track],
        "research_questions": [
            contract.primary_hypothesis,
            *contract.falsification_tests,
        ],
        "competing_models": list(contract.rival_models),
        "human_review_gates": [
            "scope", "evidence", "protocol_and_analyses",
            "interpretation", "manuscript", "publication",
        ],
        "pending_approval": "Human PI must approve the scoped claim before any experiment or publication action.",
        "next_proposals": [
            "Verify the pinned theory source and relevant rival accounts.",
            "Create a claim-to-original-source evidence matrix, including contradictions.",
            "Propose a versioned minimal research design with explicit failure conditions.",
            "Ask for PI approval before execution of confirmatory analyses.",
        ],
    }


def render_review_packet(contract: PublicationContract, dossier: dict) -> str:
    rivals = "\n".join("- " + item for item in contract.rival_models)
    failures = "\n".join("- " + item for item in contract.falsification_tests)
    roles = "\n".join("- " + item for item in dossier["assigned_roles"])
    return (
        f"# Research dossier — {contract.paper_id}\n\n"
        "**UNVERIFIED PROPOSAL — NO SCIENTIFIC OR PUBLICATION APPROVAL**\n\n"
        f"## Primary question\n\n{contract.primary_hypothesis}\n\n"
        f"**Explanandum:** {contract.explanandum}\n\n"
        f"**Source:** {contract.source_repo}/{contract.source_path}\n\n"
        f"**Source commit:** {contract.source_commit}\n\n"
        f"**Contract hash:** {contract.fingerprint()}\n\n"
        f"## Rival models / accounts\n\n{rivals}\n\n"
        f"## Conditions for disconfirmation\n\n{failures}\n\n"
        f"## Assigned reviewer roles (proposals only)\n\n{roles}\n\n"
        "## Human decisions\n\n"
        "- [ ] Approve the paper scope and pinned source.\n"
        "- [ ] Authorise relevant reading or data access within its existing classification.\n"
        "- [ ] Approve any confirmatory model/protocol freeze before running it.\n"
        "- [ ] Independently review results, contradictory evidence and interpretation.\n"
        "- [ ] Approve manuscript and any external release separately.\n\n"
        "## First work order for a Codex engineer\n\n"
        "Propose an implementation plan only. Read the validation programme's AGENTS.md, "
        "frozen M-series and V2.1 scientific rules. Do not modify those programmes. "
        "Design independent alternative models, known-truth synthetic null worlds, "
        "held-out evaluation and repeatability tests. Return a branch/PR proposal; "
        "do not execute confirmatory jobs or update canonical theory.\n"
    )


def write_run(contract: PublicationContract, root: str | Path) -> Path:
    """Create a new local run directory with a manifest and human review packet."""
    base = Path(root).expanduser().resolve()
    run_dir = base / contract.paper_id / uuid4().hex
    run_dir.mkdir(parents=True, exist_ok=False)
    report = build_dossier(contract)
    report.update({
        "run_id": run_dir.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    (run_dir / "run_manifest.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (run_dir / "review_packet.md").write_text(
        render_review_packet(contract, report), encoding="utf-8"
    )
    return run_dir
