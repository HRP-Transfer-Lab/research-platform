"""Read-only M1 evidence-dossier generator. Metadata is NOT evidence of claim support."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Callable

from .contracts import PublicationContract
from .evidence_sources import (
    MetadataResult, SourceMetadataError, compare_metadata, crossref_metadata,
    normalise_doi, openalex_metadata, require_network_opt_in,
)
from .pipeline import write_run
from .registry_reader import inspect_public_release

SEED_SCHEMA = "hrp-evidence-candidates-v0.1"
ROLES = {"competing_account", "theoretical_neighbour", "empirical_context", "boundary_or_counterevidence"}
SOURCE_KEYS = {"source_id", "doi", "claim_id", "role", "reason"}
CLAIM_KEYS = {"claim_id", "text", "status"}


class EvidenceDossierError(ValueError):
    """A candidate evidence seed is invalid or claims excessive verification."""


def load_candidate_seed(path: str | Path, contract: PublicationContract) -> tuple[dict, str]:
    raw = Path(path).read_bytes()
    try:
        seed = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceDossierError("Seed is not valid JSON.") from exc
    if not isinstance(seed, dict) or set(seed) != {
        "schema_version", "paper_id", "status", "claims", "candidate_sources", "caveat"
    }:
        raise EvidenceDossierError("Seed must use the exact candidate-only evidence schema.")
    if seed["schema_version"] != SEED_SCHEMA or seed["paper_id"] != contract.paper_id:
        raise EvidenceDossierError("Seed schema/paper ID disagrees with contract.")
    if seed["status"] != "candidate_identifiers_only_no_original_full_text_review":
        raise EvidenceDossierError("Seed must not assert its sources are verified.")
    if not isinstance(seed["caveat"], str) or not seed["caveat"].strip():
        raise EvidenceDossierError("Seed requires an explicit evidence boundary.")
    claims, sources = seed["claims"], seed["candidate_sources"]
    if not isinstance(claims, list) or not claims or not isinstance(sources, list) or not sources:
        raise EvidenceDossierError("Claims and candidate sources are required.")
    claim_ids: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != CLAIM_KEYS:
            raise EvidenceDossierError("Invalid claim fields.")
        cid = claim["claim_id"]
        if not isinstance(cid, str) or not re.fullmatch(re.escape(contract.paper_id) + r"-C[0-9]{2}", cid):
            raise EvidenceDossierError("Claim ID does not belong to this paper.")
        if cid in claim_ids:
            raise EvidenceDossierError("Duplicate claim ID.")
        if not isinstance(claim["text"], str) or len(claim["text"].strip()) < 15:
            raise EvidenceDossierError("Claim is too vague.")
        state = claim["status"]
        if not isinstance(state, str) or not any(t in state.lower() for t in ("unproven", "hypothesis", "unestablished")):
            raise EvidenceDossierError("Claims must be explicitly marked as unproven.")
        claim_ids.add(cid)
    seen_ids: set[str] = set()
    seen_dois: set[str] = set()
    for source in sources:
        if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
            raise EvidenceDossierError("Invalid candidate source fields.")
        sid, cid = source["source_id"], source["claim_id"]
        if not isinstance(sid, str) or not re.fullmatch(r"SRC-[0-9]{3}", sid):
            raise EvidenceDossierError("Invalid source ID.")
        if sid in seen_ids or cid not in claim_ids:
            raise EvidenceDossierError("Duplicate source ID or unknown claim.")
        if source["role"] not in ROLES:
            raise EvidenceDossierError("Source role cannot pre-certify scientific support.")
        if not isinstance(source["reason"], str) or len(source["reason"].strip()) < 10:
            raise EvidenceDossierError("Explain candidate source relevance.")
        try:
            doi = normalise_doi(source["doi"])
        except SourceMetadataError as exc:
            raise EvidenceDossierError(str(exc)) from exc
        if doi in seen_dois:
            raise EvidenceDossierError("Duplicate DOI in candidate seed.")
        seen_ids.add(sid)
        seen_dois.add(doi)
    return seed, sha256(raw).hexdigest()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def produce_evidence_dossier(
    contract: PublicationContract,
    candidates_path: str | Path,
    output_root: str | Path,
    *,
    live_public_metadata: bool = False,
    registry_release: str | Path | None = None,
    crossref_lookup: Callable[[str], MetadataResult] | None = None,
    openalex_lookup: Callable[[str], MetadataResult] | None = None,
) -> Path:
    """Create a candidate-only dossier with an explicit unresolved evidence gate."""
    seed, seed_sha = load_candidate_seed(candidates_path, contract)
    if live_public_metadata:
        require_network_opt_in()  # fail BEFORE any files or outbound requests
        if contract.data_tier == "restricted_local":
            raise PermissionError("Restricted-local contract cannot use public lookup.")
    registry = inspect_public_release(registry_release) if registry_release else None
    cr = crossref_lookup or crossref_metadata
    oa = openalex_lookup or openalex_metadata
    records = []
    for candidate in sorted(seed["candidate_sources"], key=lambda v: v["source_id"]):
        doi = normalise_doi(candidate["doi"])
        if live_public_metadata:
            try:
                cr_result, oa_result = cr(doi), oa(doi)
                if not isinstance(cr_result, MetadataResult) or not isinstance(oa_result, MetadataResult):
                    raise EvidenceDossierError("Provider returned an unexpected result.")
            except (SourceMetadataError, OSError, ValueError):
                cr_result = MetadataResult("crossref", doi, "unresolved", None, None, None, (), None, None, None, None, "lookup unavailable")
                oa_result = MetadataResult("openalex", doi, "unresolved", None, None, None, (), None, None, None, None, "lookup unavailable")
            metadata = [cr_result.to_dict(), oa_result.to_dict()]
            consistency = compare_metadata(cr_result, oa_result)
        else:
            metadata, consistency = [], "not_looked_up_offline"
        registry_id = registry["indexed_dois_to_record_ids"].get(doi) if registry else None
        records.append({
            "source_id": candidate["source_id"],
            "claim_id": candidate["claim_id"],
            "doi": doi,
            "role": candidate["role"],
            "reason_for_retrieval": candidate["reason"],
            "metadata_records": metadata,
            "metadata_consistency": consistency,
            "existing_hrp_registry_record_id": registry_id,
            "original_full_text_checked": False,
            "original_passage_locator": None,
            "claim_support_status": "NOT_EVALUATED",
            "review_status": "AWAITING_INDEPENDENT_SOURCE_READING",
            "confidence_in_theory_claim": None,
        })
    claims = [{
        "claim_id": claim["claim_id"], "statement": claim["text"],
        "original_status": claim["status"], "review_status": "UNRESOLVED",
        "source_ids": [r["source_id"] for r in records if r["claim_id"] == claim["claim_id"]],
        "source_support_assessed": False, "human_approval": False,
    } for claim in sorted(seed["claims"], key=lambda v: v["claim_id"])]

    folder = write_run(contract, output_root)
    _write_json(folder / "contract.json", contract.canonical_payload())
    _write_json(folder / "evidence" / "evidence_matrix.json", {
        "schema_version": "hrp-evidence-matrix-v0.1",
        "paper_id": contract.paper_id,
        "contract_sha256": contract.fingerprint(),
        "evidence_gate": "ALL_SOURCE_CLAIMS_UNRESOLVED",
        "claims": claims, "sources": records,
    })
    _write_json(folder / "evidence" / "candidate_seed.json", seed)
    _write_json(folder / "evidence" / "existing_registry_summary.json",
                registry or {"status": "not_inspected", "read_only": True})
    (folder / "evidence" / "bibliography.bib").write_text(
        "% No approved references yet. DOI metadata alone cannot verify source content.\n"
        "% Human review of original sources is required for bibliography promotion.\n",
        encoding="utf-8",
    )
    rivals = [r for r in records if r["role"] in {"competing_account", "theoretical_neighbour", "boundary_or_counterevidence"}]
    (folder / "evidence" / "competing_theories.md").write_text(
        "# Candidate competing theories and boundary cases — NOT independently verified\n\n"
        + "\n".join(f"- **{r['source_id']}** DOI {r['doi']}: {r['reason_for_retrieval']} "
                    f"({r['role']}). **Original paper not assessed.**" for r in rivals) + "\n",
        encoding="utf-8",
    )
    (folder / "evidence" / "unresolved_claims.md").write_text(
        "# Unresolved claims — no claims certified by metadata lookup\n\n"
        + "\n".join(f"- [ ] **{c['claim_id']}** — {c['statement']} "
                    "Original study methods/results, limitations and source passages still required."
                    for c in claims)
        + "\n\n**Scientific status: INSUFFICIENT EVIDENCE for endorsement.**\n",
        encoding="utf-8",
    )
    review_path = folder / "review" / "evidence_approval.md"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(
        "# Evidence gate — PENDING HUMAN REVIEW\n\n"
        "A02 Evidence Librarian: candidate identifiers collected, not study findings.\n\n"
        "A03 Source Verifier: DOI metadata may have been checked; original methods/results NOT CHECKED.\n\n"
        "A04 Competing-Theory Analyst: candidate rivals listed; no comparative adjudication.\n\n"
        "A06 Independent Reviewer: source-level claim support and contradictions require review.\n\n"
        "- [ ] Reviewer confirms original paper identities and passages.\n"
        "- [ ] Reviewer evaluates methods, limitations and competing evidence.\n"
        "- [ ] PI approves further scoped protocol development.\n\n"
        "**No empirical claim, preprint or publication approval granted.**\n",
        encoding="utf-8",
    )
    _write_json(folder / "manifests" / "retrieval_and_version.json", {
        "schema_version": "hrp-evidence-retrieval-manifest-v0.1",
        "paper_id": contract.paper_id,
        "contract_sha256": contract.fingerprint(),
        "theory_source_commit": contract.source_commit,
        "theory_source_commit_checked_by_this_runtime": False,
        "seed_sha256": seed_sha,
        "retrieval_mode": "live_public_metadata_only" if live_public_metadata else "offline_candidates_only",
        "metadata_providers": ["crossref", "openalex"] if live_public_metadata else [],
        "original_full_text_checked": False,
        "independent_claim_support_verified": False,
        "bibliography_approved": False,
        "existing_registry": {
            "release_id": registry["release_id"],
            "manifest_sha256": registry["manifest_sha256"],
        } if registry else None,
        "data_tier": contract.data_tier,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    return folder
