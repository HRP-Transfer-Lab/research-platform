"""CLI to validate contracts, create offline research dossiers and opt-in Agno drafts."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from .contracts import ContractError, PublicationContract
from .pipeline import write_run


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hrp-factory", description="HRP publication factory (offline-first).")
    sub = p.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="Validate a pinned publication research contract without network calls.")
    validate.add_argument("contract")
    kickoff = sub.add_parser("kickoff", help="Generate a local run manifest and scope-review dossier; no AI calls.")
    kickoff.add_argument("contract")
    kickoff.add_argument("--out", default=os.getenv("HRP_FACTORY_RUN_ROOT", "runs"))
    evidence = sub.add_parser(
        "evidence-dossier",
        help="M1: generate candidate-only evidence review packet; offline unless explicitly opted in.",
    )
    evidence.add_argument("contract")
    evidence.add_argument("--candidates", required=True, help="Strict candidate DOI/claim seed JSON.")
    evidence.add_argument("--out", default=os.getenv("HRP_FACTORY_RUN_ROOT", "runs"))
    evidence.add_argument("--public-metadata", action="store_true",
                          help="Allow Crossref/OpenAlex public metadata GETs after separate env opt-in.")
    evidence.add_argument("--registry-release", default=None,
                          help="Optional local path to an existing approved public registry snapshot.")
    draft = sub.add_parser("agno-draft", help="OPT-IN unverified agent drafting; never publishes or edits GitHub.")
    draft.add_argument("contract")
    draft.add_argument("--provider", choices=("openai", "ollama"), default="openai")
    draft.add_argument("--model", default=None)
    draft.add_argument("--out", default=os.getenv("HRP_FACTORY_RUN_ROOT", "runs"))
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        contract = PublicationContract.from_file(args.contract)
        if args.command == "validate":
            print(f"VALID {contract.paper_id} | pinned {contract.source_commit} | {contract.fingerprint()}")
            return 0
        if args.command == "kickoff":
            dest = write_run(contract, args.out)
            print(f"PROPOSAL ONLY: {dest / 'review_packet.md'}")
            print("Status: awaiting_scope_approval; no model or network calls.")
            return 0
        if args.command == "evidence-dossier":
            from .evidence_pipeline import EvidenceDossierError, produce_evidence_dossier
            folder = produce_evidence_dossier(
                contract, args.candidates, args.out,
                live_public_metadata=args.public_metadata,
                registry_release=args.registry_release,
            )
            print(f"M1 EVIDENCE CANDIDATES: {folder / 'evidence' / 'evidence_matrix.json'}")
            print("All original claim-support checks remain UNRESOLVED; review/approval required.")
            return 0
        if args.command == "agno-draft":
            # Refuse before creating a run, importing Agno, or making a model call.
            from .agno_workflow import assert_model_calls_permitted, run_unverified_draft
            assert_model_calls_permitted(contract, args.provider)
            dest = write_run(contract, args.out)
            output = run_unverified_draft(
                contract, args.provider, args.model, db_file=dest / "agno_drafts.db"
            )
            (dest / "unverified_model_draft.md").write_text(
                "# MODEL-GENERATED PROPOSAL: ALL EVIDENCE REQUIRES INDEPENDENT VERIFICATION\n\n"
                + output + "\n",
                encoding="utf-8",
            )
            print(f"UNVERIFIED DRAFT: {dest / 'unverified_model_draft.md'}")
            print("No public claim, repository change or publication approval granted.")
            return 0
    except (ContractError, PermissionError, RuntimeError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
