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
    source = sub.add_parser(
        "source-review", help="M1b: audit selected local source texts; optionally run bounded A02/A03/A04 Agno agents.",
    )
    source.add_argument("contract")
    source.add_argument("--candidates", required=True)
    source.add_argument("--source-bundle", required=True,
                        help="Local source-bundle JSON (with hashed authorised source files beside it).")
    source.add_argument("--out", default=os.getenv("HRP_FACTORY_RUN_ROOT", "runs"))
    source.add_argument("--run-agents", action="store_true",
                        help="Requires exact HRP_ALLOW_MODEL_CALLS=YES and approved source-exposure route.")
    source.add_argument("--provider", choices=("ollama", "openai"), default="ollama")
    source.add_argument("--model", default=None)
    oa = sub.add_parser(
        "import-open-access", help="M1b: optional Europe PMC open-access article retrieval into local bundle.",
    )
    oa.add_argument("contract")
    oa.add_argument("--candidates", required=True)
    oa.add_argument("--source-id", required=True)
    oa.add_argument("--out", required=True, help="New local, untracked source-bundle directory.")
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
        if args.command == "source-review":
            from .source_review import run_source_review
            folder = run_source_review(
                contract, args.candidates, args.source_bundle, args.out,
                run_agents=args.run_agents,
                provider=args.provider, model_id=args.model,
            )
            print(f"LOCAL SOURCE REVIEW: {folder / 'source_review' / 'REVIEW.md'}")
            print("Exact quotations are text-matched ONLY; scientific interpretation/approval remains PENDING.")
            return 0
        if args.command == "import-open-access":
            from .open_access import import_europepmc_source
            target = import_europepmc_source(
                contract, args.candidates, args.source_id, args.out,
            )
            print(f"LOCAL ONLY OPEN-ACCESS SOURCE BUNDLE: {target}")
            print("Review source rights and original identity before any hosted or public use.")
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
