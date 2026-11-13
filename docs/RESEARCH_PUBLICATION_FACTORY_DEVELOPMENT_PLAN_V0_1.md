# HRP Research & Publication Factory — Development Plan v0.1

**Status:** proposed architecture; Milestone 0 implementation underway.  
**Owner and scientific approval:** Mark Ashton Smith (human principal investigator).  
**Date:** 13 November 2026.  
**Location:** HRP Transfer Lab / research-platform.  
**Purpose:** Turn versioned Trident-G hypotheses into *independently challengeable* computational, empirical, developmental and philosophical publications, without confusing an AI-produced manuscript with a verified scholarly result.

## 1. Decision and inherited architecture

The factory is a component of **research-platform**, not a new competing lab stack. Its programme control follows the existing G-Loop Adaptive Learning Kernel and the research platform's three-way separation of theory/protocol, runtime and evidence. The existing Cloud Lab dual-machine plan governs private/public execution.

### Canonical existing repositories and obligations

| Source | Role | Status at audit |
|---|---|---|
| HRP-Transfer-Lab/Trident-G-theory | Theory, papers and publication hypotheses | Existing paper plan; v0.4 currently on a draft PR branch |
| HRP-Transfer-Lab/Cloud-Lab-Ground-Truth | Component, scope and claims boundaries | Existing canonical specification |
| HRP-Transfer-Lab/research-platform | Runtime, evidence registry, knowledge bank, models and orchestration | Existing system; factory belongs here |
| HRP-Transfer-Lab/trident-control-architecture-validation | M-series model tournaments and independent AO stream | Frozen M2.6 result, M2.6b gate and non-negotiable Codex protocols |
| HRP-Transfer-Lab/trident-learnability-transfer | Longitudinal learnability and transfer modelling | Python package and synthetic demonstration already exist |
| HRP-Transfer-Lab/trident-g-open-methods-and-ethics | AI-use, ethics, claims, provenance and publication governance | Human review mandatory |

Do not duplicate the operational Evidence Registry or create a parallel competing G-Loop controller. Do not alter the validated M-series definitions, milestones, frozen results, seeds or model-selection thresholds from this programme. **New work receives its own stream identifier, research contract and output location.**

### Factory scope

- Accept a *pinned theory or research source commit* and a narrow proposed paper claim.
- Open a paper-specific **Publication Research Contract** with one primary explanandum.
- Gather independently verified literature and competing accounts, preserving disagreements.
- Generate and review a formal computational plan, experimental protocol or philosophical argument map.
- Delegate **bounded** implementation to Codex and independently verify tests and results.
- Produce draft manuscripts with explicit claims, citations, model/analysis provenance, null findings and limitations.
- Return an evidence-and-approval packet to the human PI. **Never submit, publish, send or release claims autonomously.**

The source theory is a hypothesis bank, **not** authoritative proof that its mechanisms are true.

## 2. Paper production lines

| Track | First paper / focus | Required evidence or argument | Release gate |
|---|---|---|---|
| **TG-COMP-001** | Homeostatic Adaptive Intelligence: switching, recovery and viable control | Competing models, held-out performance, reproducible simulations, honest failures | Model-review + scientific interpretation + PI sign-off |
| **TG-NEURO-001** | FPCN-A/B internal/external × search/constraint architecture | Neural literature audit, orthogonal factorial task, pilot, approved analysis/preregistration | Neuroscience review + ethics/registration decision |
| **TG-TRANSFER-001** | Learnability, Gf→Gc banking and cross-construct transfer | Independent test batteries, longitudinal analyses, delayed or held-out transfer | Data/ethics + preregistered statistics + PI |
| **TG-SHARED-001** | Shared Intentionality_A → R through cross-perspectival invariance | Multi-agent experiment with novel referents, repair and independent grounding | Formal-model review + philosophical adequacy + PI |
| **TG-PHIL-001** | Public normativity and recursive synthetic reality | Original thesis, textual source checks, argument maps, strongest objections and replies | Philosophical review + provenance + PI |
| **TG-PSYCH-001** (conditional) | From adaptive dynamics to psychometric g | Positive-manifold/individual-differences predictions beyond adaptivity | Psychometric review and independent data |

A single master document must **not** be submitted as six theories in one. Each paper must identify one main explanatory target and one primary claim.

## 3. Human-governed agent structure

The factory begins with five bounded responsibilities, with later optional specialists.

| Role | Responsibility | Authority |
|---|---|---|
| **Research Director** | Paper scoping; stage routing; resource and approval requests | Propose only |
| **Evidence Librarian** | Read curated sources, verify bibliographic details, cite counterevidence | Propose only; cannot certify unexamined papers |
| **Theoretical Formaliser** | Define one computable mechanism and fair rivals or make an explicit conceptual argument | Draft only |
| **Computational Engineer (Codex)** | Make isolated PRs for models and tests; never redefine registered hypotheses | Code changes only in an approved sandbox/branch |
| **Independent Adversarial Reviewer** | Inspect citation claims, identification, alternatives, failures and leakage | Block or request revision; cannot publish |
| Later: **Statistical Auditor** | Independently reproduce results and check model selection | Report only |
| Later: **Neuroscience Specialist** | FPCN/DMN/DAN/HPC substrate and physiological inference | Evidence critique |
| Later: **Philosophy Specialist** | Define referents, claims, normativity and argumentative entailment | Argument critique |
| Later: **Publication Editor** | Journal-constrained coherent prose, tables and bibliography | Manuscript proposal only |

No free-roaming agents with unbounded write tools. Roles receive the minimum repository paths and tools necessary for one task. Evidence, implementation and independent adjudication should not use the same unreviewed model output as their only source.

## 4. Orchestration and durable objects

The **G-Loop** controls research decisions: SENSE → LOCATE → RECALL → BOUNDED CANDIDATES → FORECAST → EVALUATE → COMMIT/PREDICT → TEST → COMPARE → ADAPT → BANK. Its application to a paper is implemented as a staged workflow with explicit gates.

The first durable research records are:

1. **Publication Research Contract:** immutable-ish source revision, primary explanandum, claim, rivals, intended test, forbidden claims and approval requirements.
2. **Factory run manifest:** unique run ID, contract hash, selected track, explicit state, event timestamps and worker assignments.
3. **Review queue:** proposed tasks and decisions requiring PI approval.
4. **Evidence ledger (later):** exact DOI/URL, verified passage, method, evidence status, supporting and contradicting claims, reviewer outcome.
5. **Reproducibility manifest (later):** git SHA, model versions, configs, dataset eligibility, random seeds, software, result checksums, failed runs.
6. **Paper package (later):** claim–evidence matrix, author-reviewed manuscript, figures, bibliography, limitations and disclosure.

Control states for the first implementation: **draft → awaiting_scope_approval → scoped → evidence_review → protocol_review → analysis_review → manuscript_review → awaiting_publication_approval**. Every irreversible transition must be reviewed and all external publishing actions remain forbidden to the runtime.

For the first milestone, statuses are *not* treated as authentication or proof of scientific approval; there is no autonomous gate crossing. A future authenticated review API may record real human decisions.

## 5. Deployment: local red rail, workstation and cloud blue rail

| Placement | Permitted work | Not permitted by default |
|---|---|---|
| **Engineering workstation** | VS Code/Codex, human review, synthetic fixtures, Git PRs, manuscript drafts | Repository secrets in code |
| **Trusted local red rail** | Private PDFs, restricted Zotero attachments, private embeddings, approved participant exports, locally hosted Ollama | Unapproved public/cloud forwarding |
| **Blue/cloud workers** | Public research, approved public data, synthetic parameter sweeps, lint/tests and non-sensitive papers | Raw identifiers, restricted PDFs, private vectors |
| **Publication boundary** | Human-approved preprints and journal submission packages | Automatic submission or speculative result laundering |

**Model routing:** Agno Workflows for orchestration; optional Agno agents for research drafting; Codex for isolated code changes; Python/numerical libraries for actual simulation; Gemma via local Ollama for bounded extraction after benchmarking; Flint as an optional, *unverified* local model; hosted reasoning models only under explicit opt-in and approved data classification. No assumption is made that a particular Ollama model is currently installed or operational.

**Compute profiles:** inherit the model-validation programme's smoke → pilot → confirmatory discipline. Smoke runs validate plumbing only; pilot runs inspect failure modes; confirmatory runs require prior registered definitions, deterministic seeds, progress, checkpoint/restart, results manifest and independent review. Cloud jobs are queued only after data classification and budget review.

## 6. Milestones and check-off plan

### M0 — Repo audit and safe bootstrapping (this PR)

- [x] Audit existing HRP organisation and avoid parallel platform construction.
- [x] Identify source-of-truth, red/blue and evidence-governance contracts.
- [x] Identify the existing M-series recovery results and protect them from silent changes.
- [x] Draft this plan and create an isolated review branch.
- [x] Add a self-contained **research-factory** Python component and offline-first CLI.
- [x] Add strict publication-contract validation and an example pinned TG-COMP-001 contract.
- [x] Implement deterministic *proposals only* run creation and auditable local manifest.
- [x] Add an opt-in Agno agent-workflow adapter with **no autonomous tools**.
- [x] Add tests for invalid sources/claims, reproducibility and publish-denial.
- [x] Run tests, add CI and open a draft PR.
- [ ] PI reviews and approves M1 scope; do **not** merge automatically.

**M0 verification:** The first public/synthetic-only Python 3.12 CI run passed **17 offline tests** (GitHub Actions run 43445312256). A second CI validation successfully **constructed both OpenAI and local-Ollama Agno workflows (2 passing smoke tests)**, without any model calls (GitHub Actions run 43446444748). This verifies SDK construction, **not** actual model quality, external execution, scholarly accuracy, or deployment. No participant data, model credentials or publication actions are involved.

**M0 definition of done:** from a clean checkout, a user can validate a pinned contract, produce a reviewable run dossier **without network/model credentials**, and run an isolated test suite. The factory cannot publish or alter theory or external research programmes.

### M1 — Evidence and literature bridge

- [ ] Review access to the existing Evidence Registry; add claim-to-source reading with scoped permissions.
- [ ] Implement Zotero/OSF metadata synchronisation using existing components, not new duplicate tables.
- [ ] Record verification method, DOI, original passage, study type, caveats and contradiction status.
- [ ] Add citations and provenance integrity tests; never create plausible references from memory.
- [ ] Introduce the librarian and adversarial critic under an explicit review gate.
- [ ] Pilot a **TG-COMP-001** literature dossier before indexing other tracks.

**Gate:** reviewer can trace each central claim to a verifiable original paper and see competing evidence.

### M2 — First computational paper and Codex delegation

- [ ] Freeze paper scope and competing model assumptions in a versioned research contract.
- [ ] Generate a Codex work order with repository allowlists, scientific invariants and tests.
- [ ] Implement minimal cusp and fair smooth/RL/hidden-state competitors **in a separate stream**.
- [ ] Run synthetic recovery and null worlds with reproducible seeds; avoid self-generated-only confirmation.
- [ ] Register held-out predictions, secondary metrics, failure conditions and model penalties.
- [ ] Enable bounded local/cloud batch execution, checkpoint/resume and results manifests.
- [ ] Independent statistical review and human approval before manuscript results claims.

**Gate:** another researcher can independently reproduce tables and negative findings from a frozen manifest.

### M3 — Manuscript production and adversarial review

- [ ] Create Markdown/LaTeX paper templates for computational, empirical and philosophical submissions.
- [ ] Enforce claim–evidence–result traceability in every draft paragraph.
- [ ] Independently verify bibliography, original sources and AI-use disclosure requirements.
- [ ] Generate reviewer objections and require substantive responses, not stylistic polish alone.
- [ ] Check figure provenance and accessibility and run final citation integrity checks.
- [ ] PI approves any preprint or journal release manually.

**Gate:** paper package is scientifically interpretable independently of the entire master theory.

### M4 — Parallel neuroscience and philosophical streams

- [ ] TG-NEURO: internal/external × search/constraint factorial pilot and Stage-1 registration feasibility.
- [ ] TG-SHARED: generative joint-action → reference transition with matched control agents.
- [ ] TG-PHIL: premises/objections/novelty map and critical comparison with existing public-reason accounts.
- [ ] TG-TRANSFER: longitudinal transfer beyond trained tasks.
- [ ] Reuse only *verified, approved* outputs as cross-paper evidence.

**Gate:** each track has a distinct explanandum, primary model/argument and evidence standard.

### M5 — Operationalisation and governance hardening

- [ ] Pin dependency versions and add software-bill-of-materials/security checks.
- [ ] Move job state to approved Postgres; implement a durable queue and authenticated human-in-the-loop.
- [ ] Add review dashboards, retries, audit exports, redaction and opt-in logging.
- [ ] Benchmark local Gemma/Flint against a small human-labelled extraction set.
- [ ] Add token/compute budgets, caching and intervention-safe scheduler policies.
- [ ] Introduce cloud batch workers only for approved data tiers.
- [ ] Run a publication dry-run without sending or submitting anything.

**Gate:** an authorised PI can inspect exactly what was done, on which data, with which models and costs.

## 7. Security and integrity acceptance tests

- **No publication action** exists in the initial code; GitHub/OSF/arXiv/journal release cannot occur through a model prompt.
- Contract sources must be immutable commit hashes, not mutable branch names alone.
- Unapproved data classes cannot be routed to cloud agents or jobs.
- A generated result cannot be labelled *empirical finding* without a linked analysis/evidence record.
- Agent proposals and private research material never overwrite canonical source files.
- Null, contradictory, incomplete and failed results remain first-class artefacts.
- Confirmatory analyses must never be redesigned silently after results inspection.
- No individual-level data in public Git; .env files and local runs are ignored.
- If future authenticated approval is unavailable, the workflow **stops** at the human gate.
- Existing research protocols and M-series frozen outcomes remain untouched.

## 8. First paper to implement

**TG-COMP-001: Homeostatic Adaptive Intelligence**. First task: verify that a cusp-like switching controller and alternative continuous controllers can be simulated under matched changing demands, then test when the mechanisms are distinguishable. Do not claim that a simulation demonstrates human neural criticality or psychometric g.

The first factory output should be a **research dossier**, not an automatically written journal article: one narrow claim, rival hypotheses, falsification criteria, evidence-to-review tasks, a computational work order and a human decision queue.

## 9. Source documents

- [Research-platform architecture](../docs/ARCHITECTURE.md)
- [Adaptive G-Loop learning kernel](../docs/G_LOOP_ADAPTIVE_LEARNING_KERNEL.md)
- [Dual-machine implementation](../docs/DUAL_MACHINE_IMPLEMENTATION.md)
- [Cloud Lab Ground Truth](https://github.com/HRP-Transfer-Lab/Cloud-Lab-Ground-Truth/blob/main/CLOUD_LAB_GROUND_TRUTH.md)
- [Trident-G theory and publication plans](https://github.com/HRP-Transfer-Lab/Trident-G-theory/tree/main/papers)
- [Current v0.4 theory development branch](https://github.com/HRP-Transfer-Lab/Trident-G-theory/pull/1)
- [Computational-validation scientific rules](https://github.com/HRP-Transfer-Lab/trident-control-architecture-validation/blob/main/AGENTS.md)
- [Research Programme V2.1 amendment](https://github.com/HRP-Transfer-Lab/trident-control-architecture-validation/blob/main/research-program/RESEARCH_PROGRAM_V2_1_AMENDMENT.md)
- [Human oversight and AI use](https://github.com/HRP-Transfer-Lab/trident-g-open-methods-and-ethics/blob/main/governance/AI_USE_AND_HUMAN_OVERSIGHT.md)
- [Agno workflow documentation](https://docs.agno.com/workflows/building-workflows)
