# Research Factory M1 — First Evidence Bridge Implementation v0.1

**Status:** M1a vertical slice implemented and CI-validated; **pending PI review** (13 November 2026).  
**Parent:** Research Factory M0 draft PR #13.  
**Initial paper:** `TG-COMP-001` — *Homeostatic Adaptive Intelligence*.  
**Scientific authority:** Human PI and verified original studies, **not** the agent-generated dossier.

## 1. Implemented versus still planned

| Capability | Implementation status | Important boundary |
|---|---|---|
| Pinned TG-COMP-001 contract | Inherited and tested from M0 | The source SHA is validated syntactically; this runtime does not independently re-fetch the Git commit |
| Candidate claim/DOI seed | **Implemented** | Includes competing theories and counterexamples; this is **not** a completed bibliography |
| DOI normalisation / source identity | **Implemented** | Rejects malformed/unsafe IDs and provider DOI mismatches |
| Crossref metadata client | **Implemented, read-only, explicit opt-in** | Metadata only, not methods or claim verification |
| OpenAlex cross-check | **Implemented, read-only, explicit opt-in** | Optional local key; conflicting titles flagged for human examination |
| Read-only public Evidence Registry release inspection | **Implemented** | Existing release metadata and DOI identifiers; **no** reviewer table mutations or theoretical inference |
| Evidence matrix, rival-source list, unresolved claims, PI review packet | **Implemented** | All source claims remain `NOT_EVALUATED`, including when APIs return metadata |
| Zotero/OSF metadata | **Not integrated** | Reuse existing lab connector and permissions later |
| Original paper methods, passages, figures and claims support | **Not verified automatically** | Require source-specific reading and human review |
| Agno Evidence Librarian, Source Verifier and Rival-Theory agents | **Roles specified, not executing** | M0 opt-in three-agent constructor remains proposal-only |
| Author-approved bibliography and publication | **Not implemented** | No automatic promotion to approved evidence |

This implementation intentionally makes a clear distinction between **identifying a paper** and **determining whether the paper supports an assertion**. A matching DOI and consistent Crossref/OpenAlex metadata do not validate a Trident-G claim.

## 2. Files and ownership

```text
components/research-factory/
  configs/
    TG-COMP-001.json                         existing M0 source-pinned contract
    TG-COMP-001-evidence-candidates.json     M1 candidate claim/DOI seed
  src/hrp_research_factory/
    evidence_sources.py                      Crossref/OpenAlex read-only clients
    registry_reader.py                       public Evidence Registry snapshot reader
    evidence_pipeline.py                     candidate dossier and provenance
    cli.py                                   evidence-dossier command
  tests/
    test_evidence_sources.py
    test_evidence_pipeline.py
```

All real run outputs go to local `runs/` (Git-ignored). No new Supabase tables or new evidence releases are created.

## 3. First paper candidate set

The DOI seed covers **Barbey's Network Neuroscience Theory, Kovacs and Conway's Process Overlap Theory, van der Maas and colleagues' Mutualism Theory, Moretti and Muñoz's hierarchical-modular Griffiths model, Ezaki and colleagues' fluid-intelligence/criticality association, and Priesemann and colleagues' slightly-subcritical network evidence**. These identifiers and relevance labels provide a defensible *research starting point*.

The candidate set is **not exhaustive**, and it should not be presented as a completed literature review. Standard reinforcement learning, active-inference accounts and recent field-theory proposals need additional source screening; a single paper may support some claims while challenging others. The factory deliberately does not assign support status from titles or metadata.

## 4. Usage

In a clean checkout of the **M1 feature branch**, from `components/research-factory/`, using Python 3.12+:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
hrp-factory validate configs/TG-COMP-001.json

# Fully offline: creates an unverified, review-ready dossier.
hrp-factory evidence-dossier configs/TG-COMP-001.json \
  --candidates configs/TG-COMP-001-evidence-candidates.json \
  --out runs
```

To inspect an **already public and approved** HRP Evidence Registry snapshot without mutating it, supply:

```bash
hrp-factory evidence-dossier configs/TG-COMP-001.json \
  --candidates configs/TG-COMP-001-evidence-candidates.json \
  --registry-release ../evidence-registry/data/releases/2026-08-23 \
  --out runs
```

The relative public-release path above is relative to the shell working directory (`components/research-factory`); do not point at the private Supabase reviewer database. The existing approved release has 18 records. Its intervention classifications are not a measure of support for Trident-G's computational theory.

**Optional public metadata only** (explicitly permits requests to the two fixed API hosts; does not access arbitrary URLs or full-text PDFs):

```bash
export HRP_ALLOW_PUBLIC_METADATA_LOOKUP=YES
# Optional: export OPENALEX_API_KEY via a private secret manager, not a git file.
hrp-factory evidence-dossier configs/TG-COMP-001.json \
  --candidates configs/TG-COMP-001-evidence-candidates.json \
  --public-metadata --out runs
```

Without the exact environment setting `YES`, `--public-metadata` **fails before making any request**. When an API is unavailable or returns conflicting data, the relevant record is marked unresolved. The CLI does not submit, approve, email, merge, run scientific simulations or publish.

### Output

```text
runs/TG-COMP-001/<run_id>/
  run_manifest.json
  review_packet.md
  contract.json
  evidence/
    candidate_seed.json
    evidence_matrix.json
    existing_registry_summary.json
    bibliography.bib            # intentionally contains NO approved entries
    competing_theories.md
    unresolved_claims.md
  manifests/
    retrieval_and_version.json
  review/
    evidence_approval.md        # pending human review
```

**Determinism:** with the same contract, candidate seed and metadata responses, scientific dossier fields are repeatable; timestamps/run IDs differ. Source hashes are recorded. No original scientific claim is promoted to `verified` automatically.

## 5. Assigned roles in this limited vertical slice

- **A01 Director:** the already validated publication contract supplies scope and primary explanandum.
- **A02 Evidence Librarian:** the fixed seed supplies candidate identifiers and competing-model targets; no autonomous discovery or paper-reading agent yet.
- **A03 Source Verifier:** validates DOI syntax and optional registry/API metadata; original claims remain unexamined.
- **A04 Competing-Theory Analyst:** a structured competing-source packet is generated from proposed candidate roles, without pretending full-text comparison has occurred.
- **A06 Independent Reviewer:** receives the unresolved claim report and an explicit human evidence-approval checklist.

The current code implements **deterministic role-aligned steps**, not a multi-agent team performing independent research.

## 5a. Tested reference output and reproducibility status

The first GitHub Actions run using the M1a branch succeeded:
[**CI run 43455335139**](https://github.com/HRP-Transfer-Lab/research-platform/actions/runs/43455335139).

- **37 offline tests passed; 2 optional Agno tests skipped in the offline job** (the SDK is deliberately not installed there).
- **2 separate Agno workflow-construction smoke tests passed**; they do not invoke a model.
- The workflow generated an **offline, unverified TG-COMP-001 review packet** and uploaded it as the short-lived Actions artifact named `TG-COMP-001-M1a-unverified-evidence-packet` (7-day retention).
- The packet contains a candidate evidence matrix, source/review status, list of rival models, empty approved bibliography, unresolved claims, and a human approval checklist. It contains no reviewed original source passages and makes **no claim of empirical support**.

These tests validate code and fail-closed status handling. They are **not tests of full-text scholarly interpretation**, actual provider availability, agent reasoning quality or human scientific agreement. A live Crossref/OpenAlex lookup remains optional and is not part of the default CI job.

## 6. M1 next steps and stop/go gate

- [x] Create DOI/source seed linked to discrete TG-COMP-001 theoretical claims.
- [x] Write read-only metadata clients and separate metadata from scientific claim verification.
- [x] Add approved-public-release inspection without changing operational evidence records.
- [x] Generate offline evidence, rival, provenance and human review packets.
- [ ] Verify actual pinned theory content from the exact commit in the factory runtime (read-only).
- [ ] Retrieve original paper methods/results and record stable locations or content hashes.
- [ ] Add read-only Zotero/OSF interfaces through existing permissions and lab components.
- [ ] Implement A02/A03/A04 bounded Agno tasks with independent source/claim evidence.
- [ ] Demonstrate real source-level support and **genuine contradiction** adjudication.
- [ ] Add conflict-resolution and human-approved bibliography promotion.
- [ ] Pilot an independently reviewed TG-COMP-001 literature dossier.
- [ ] Obtain PI decision before moving to model design or a publication claim.

**Gate:** M1 is **not complete** until original-source verification, contradictory evidence analysis and human review have actually occurred. API identity lookups and the present dossier are an intentionally safe first step.
