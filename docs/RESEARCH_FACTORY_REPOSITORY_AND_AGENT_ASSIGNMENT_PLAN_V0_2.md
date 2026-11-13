# HRP Research Factory — Repository Structure and Agent Assignment Plan v0.2

**Status:** architecture and assignment specification for review; **not** a claim that planned agents or connectors are deployed.  
**Date:** 13 November 2026  
**Scientific owner / principal investigator:** Mark Ashton Smith  
**Factory repository:** `HRP-Transfer-Lab/research-platform`  
**Baseline:** [Factory development plan v0.1](RESEARCH_PUBLICATION_FACTORY_DEVELOPMENT_PLAN_V0_1.md), [Cloud Lab architecture](ARCHITECTURE.md), [G-Loop kernel](G_LOOP_ADAPTIVE_LEARNING_KERNEL.md), [red/blue deployment policy](DUAL_MACHINE_IMPLEMENTATION.md).  
**Current change:** Research Factory M0 is on [draft PR #13](https://github.com/HRP-Transfer-Lab/research-platform/pull/13); it is not merged into `main`.

## 1. Architectural decision

**One orchestrator, one evidence system, several independently governed research programmes.** The research factory coordinates publication workflows; it does not replace the Evidence Registry, become a new canonical theory source, or overwrite registered experiments.

The distinction among **research programme**, **testable theory** and **empirical model** is preserved. The master Trident-G theory is a *version-pinned hypothesis source*, **not** evidence that the hypotheses are true.

```text
Human PI: scientific direction, protocol approval and publication decision
                         |
                         v
research-platform / research-factory
  Agno workflow controller + G-Loop research decision rules
  publication contracts + review queue + read-only evidence retrieval
                         |
        +----------------+------------------+
        |                |                  |
        v                v                  v
Scientific track   Philosophical track   Empirical track
models + code      arguments + texts     task + statistics
        |                |                  |
        v                v                  v
independent audit / adversarial review / source verification
                         |
                         v
approved research packages → author-reviewed manuscript
                         |
                         v
HUMAN PUBLICATION GATE (no automatic external submission)
```

**No new GitHub repository is needed for M1.** New publication programmes are logical workspaces with IDs and manifests. They may receive distinct repositories **only after** the PI approves a genuine need for access isolation, independent release/versioning or a separate collaborator team.

## 2. GitHub organisation — canonical ownership

The following are **existing** repositories; proposed folder paths are explicitly labelled below. The companion [machine-readable role and paper manifest](../components/research-factory/configs/agent_assignments.v0.2.json) records 16 proposed role definitions, the current three M0 agent constructors, six track assignments and human-only release gates. It is **documentation, not runtime permissions**.

| Existing repository | Exclusive or primary ownership | Factory access | Forbidden from the factory |
|---|---|---|---|
| [`research-platform`](https://github.com/HRP-Transfer-Lab/research-platform) | Agno orchestration, evidence infrastructure, data and compute integration, manifests, queues | Work only on isolated factory branches, then PR | Unreviewed direct changes to evidence releases or private data |
| [`Trident-G-theory`](https://github.com/HRP-Transfer-Lab/Trident-G-theory) | Master theory, conceptual claims, references, scholarly manuscript **source** | Read by exact commit; manuscript proposals via reviewable PR | Autonomous edits to canonical theory, publication or rewriting assumptions |
| [`Cloud-Lab-Ground-Truth`](https://github.com/HRP-Transfer-Lab/Cloud-Lab-Ground-Truth) | Lab vocabulary, component boundaries and evidence/claim limits | Read-only reference | Duplicating its source-of-truth role |
| [`trident-control-architecture-validation`](https://github.com/HRP-Transfer-Lab/trident-control-architecture-validation) | Existing M-series validation and parallel AO programme | Pinned reading; future **approved** independent code streams | Retuning frozen M2.6, bypassing M2.6b, modifying pre-registered model rules |
| [`trident-learnability-transfer`](https://github.com/HRP-Transfer-Lab/trident-learnability-transfer) | Longitudinal learnability and cross-construct transfer models | Read-only at M1; future approved PRs | Importing private participant data to public Git |
| [`trident-g-open-methods-and-ethics`](https://github.com/HRP-Transfer-Lab/trident-g-open-methods-and-ethics) | AI-use, consent, claims, reproducibility and publication governance | Read-only policy constraints | Autonomous public research releases |

**Theory version note:** The Trident-G v0.4 revision is currently on a **draft branch** in `Trident-G-theory`, not automatically the version on `main`. A publication contract must hold the exact validated source commit, never just `v0.4` or a mutable branch label. Updating a paper's theoretical baseline is a *new documented contract version*.

### 2.1 Source locations versus proposed manuscript locations

**Already in the theory repository:** `theory-nov-2026/Trident-G-Theory.md`, `papers/publication_plan.md`, and `papers/computational_theory_1.md`.

**Proposed, not yet created:**

```text
HRP-Transfer-Lab/Trident-G-theory/
  theory-nov-2026/           existing master theory
  papers/
    publication_plan.md     existing
    computational_theory_1.md  existing
    TG-COMP-001/            proposed manuscript and source bibliography
    TG-NEURO-001/           proposed design/preregistration manuscript
    TG-TRANSFER-001/        proposed learnability/psychometrics manuscript
    TG-SHARED-001/          proposed joint reference / developmental paper
    TG-PHIL-001/            proposed philosophical argument/manuscript
    TG-PSYCH-001/           conditional, if mechanism-to-g work warrants it
```

For each future paper, manuscript **source** (text, BibTeX and approved figures) may be versioned in `Trident-G-theory/papers/<paper_id>`. **Raw data, private PDF extracts, intermediate model results or unreviewed runs do not belong there.** Large artefacts belong in access-controlled object storage with content hashes; public reproducibility archives should contain only approved non-identifiable outputs.

## 3. Research-platform folder map: current and planned

```text
research-platform/
  docs/
    ARCHITECTURE.md                              EXISTS
    G_LOOP_ADAPTIVE_LEARNING_KERNEL.md           EXISTS
    DUAL_MACHINE_IMPLEMENTATION.md               EXISTS
    RESEARCH_PUBLICATION_FACTORY_DEVELOPMENT_PLAN_V0_1.md  M0 DRAFT
    RESEARCH_FACTORY_REPOSITORY_AND_AGENT_ASSIGNMENT_PLAN_V0_2.md  THIS PLAN

  components/
    research-factory/                            M0 DRAFT
      AGENTS.md, README.md, pyproject.toml
      configs/
        TG-COMP-001.json                        EXISTS on M0 branch
        agent_assignments.v0.2.json             EXISTS: planning-only; not executable
        model_routing.yaml                      PLANNED M2/M5
      src/hrp_research_factory/
        contracts.py, pipeline.py, cli.py       EXISTS on M0 branch
        agno_workflow.py                        EXISTS: opt-in, no tools
        agents/                                 PLANNED M1–M4
        workflows/                              PLANNED M1–M4
        connectors/                             PLANNED M1 (read-only first)
        knowledge/                              PLANNED M1 claim/source ledger
        compute/                                PLANNED M2 Codex/worker adapters
        models/                                 PLANNED M2/M5 provider router
        approvals/                              PLANNED M5 authenticated gates
      tests/                                    EXISTS; extend each milestone
      docs/                                     PLANNED technical module docs

    evidence-registry/                          EXISTS, operational evidence system
    knowledge-bank/                             EXISTS, partial foundation
    computational-modeling/                     EXISTS, component boundary
    data-pipeline/                              EXISTS
    experiment-cloud/                           EXISTS

  infra/
    orchestration/                              EXISTS (first-pass directory)
    db/, vector/                                EXISTS
  .github/workflows/
    research-factory-validate.yml               M0 DRAFT, passing
```

**Ownership rule:** `research-factory` owns orchestration contracts, agent definitions and reviewable research packets. `evidence-registry` continues to own scientific evidence release and approval. Existing specialised scientific repositories remain the owners of their own analysis code, registered protocols and frozen outputs. Publication manuscripts are **not** the factory's authoritative empirical records.

## 4. Agents, team organisation and implementation status

A *research role in a dossier* is not necessarily an executing agent. Current M0 has three **opt-in, no-tool Agno agent constructors**: Research Director, Formaliser and Independent Reviewer. The dossier may name additional roles but has no implementation of their research tools. It does not fetch sources, invoke Codex or run a scientific model.

### 4.1 Core coordination and evidence team

| ID and role | Stage | Inputs → output | Tools / access | Approval and restrictions |
|---|---|---|---|---|
| **A01 Research Director** | **M0 constructor**; durable coordination planned | Contract → scoped work order, approval queue, dependency map | Contract and run manifest; later Agno workflow/DB | Propose only; PI alone approves scope or publication |
| **A02 Evidence Librarian** | **M1 planned** | Pinned claims + literature question → source dossier with counterevidence | Read-only Crossref/OpenAlex/PubMed, existing Evidence Registry, approved Zotero/OSF metadata | No guessed references, citation laundering or unreviewed release |
| **A03 Source & Citation Verifier** | **M1 planned** | DOI/URL + original source → claim-specific verification record | Stable metadata resolvers, exact source passages when accessible, provenance ledger | Must say *unverified* when full text inaccessible; no automatic certification |
| **A04 Competing-Theory Analyst** | **M1 planned** | Claim + studies → rival accounts, discriminators, evidence gaps | Curated literature and pinned theory passages, read-only | Cannot suppress negative or competing evidence |
| **A05 Theoretical Formaliser** | **M0 constructor**; stronger tools later | Claim + rivals → equations/design assumptions, falsification conditions | Model reasoning, paper contract, later scientific specs | Mathematical proposals remain untested until code/analysis verifies them |
| **A06 Independent Adversarial Reviewer** | **M0 constructor**; expanded M1+ | Claim/evidence/protocol/draft → contradiction and blocking-issue report | Separately retrieved evidence, critique templates | No paper approval; no same-agent self-certification |

### 4.2 Computational and empirical science team

| ID and role | Stage | Inputs → output | Tools / access | Approval and restrictions |
|---|---|---|---|---|
| **A07 Experimental Designer** | M2 planned | Formal hypothesis → simulated worlds/experimental design and frozen analysis proposal | Config/manifest tools, approved numerical design tools | PI must approve confirmatory designs before results are seen |
| **A08 Computational Engineer (Codex)** | M2 planned | Approved coding work order → isolated Git branch + tests + PR | Codex in sandbox, allowlisted repo path, Python tooling | No autonomous merges, changed hypotheses, publication or raw private data |
| **A09 Statistical Auditor** | M2 planned | Code/results/manifests → independent replication, model fit and leakage report | Python, pinned run data, tests; separate from implementation agent | Must preserve failed/null/ambiguous results and frozen definitions |
| **A10 Neuroscience Specialist** | M4 planned | Neural hypothesis → empirical evidence analysis and task design | Primary neuroscience literature, approved experiment specifications | FPCN and criticality measures cannot be asserted directly from behaviour |
| **A11 Psychometric / Learnability Specialist** | M4 planned | Latent-g / transfer hypothesis → measurement and longitudinal model plan | Independent batteries, preregistered datasets, psychometrics | Distinguish adaptivity, developmental change and psychometric g |

### 4.3 Philosophy and publication team

| ID and role | Stage | Inputs → output | Tools / access | Approval and restrictions |
|---|---|---|---|---|
| **A12 Philosophical Scholar** | M4 planned | Thesis → original source/context dossier and novelty map | Original texts, philosophical literature, verified quotations | No invented interpretation or unverified quotation |
| **A13 Conceptual / Argument Analyst** | M4 planned | Thesis → definitions, premise–conclusion graph, objections | Structured argument records, source corpus | Distinguish conceptual entailment from scientific evidence |
| **A14 Philosophical Counterargument Reviewer** | M4 planned | Argument map → strongest objections, alternative philosophies | Independently retrieved original sources | May block novelty/adequacy claims; cannot adjudicate alone |
| **A15 Publication Editor** | M3 planned | Approved evidence/argument results → coherent manuscript and references | Markdown/LaTeX and citation/figure tooling | No new empirical findings, inferred DOIs or automatic submission |
| **A16 Publication Integrity Reviewer** | M3 planned | Manuscript + claim ledger → sourced audit and unresolved-claim report | Read-only claim/source/manifests | Must separate human approval, empirical facts, philosophical claims and synthetic model outcomes |

**Human PI (not an agent):** controls scientific objectives, normative commitments, permission to use data, protocol freezes, claims interpretation and all external releases. Some specialist tasks may initially be a **prompted workflow stage**, not a persistent autonomous process; add real agents only after a measurable benefit over a simpler process.

### 4.4 Agno team boundaries

- **Coordination and Evidence:** A01–A06; first M1 build is A02/A03/A04, with A01/A05/A06 acting as bounded reviewers.
- **Scientific Computation:** A05 and A07–A11; Codex writes code, Python produces numerical output, A09 independently audits.
- **Philosophical Research:** A12–A14 with A05 for formal connections and A06 for independent critique.
- **Editorial & Integrity:** A15–A16; cannot create missing evidence or approve their own claims.

Agno **Workflows** enforce stage gates; Agno **Teams** are for bounded delegation inside a stage. No free-form team has authority to publish. M0 supports only an opt-in construction/smoke-tested three-role workflow with no external tools; the team descriptions above are a **target architecture**.

## 5. Agent-to-paper assignment matrix

| Publication | Scientific lead / primary agent | Evidence role | Implementation or analysis | Independent challenge | Publication output |
|---|---|---|---|---|---|
| **TG-COMP-001** cusp/regulated reconfiguration | A05 Formaliser + A07 Designer | A02–A04 | A08 Codex and numerical workers; A09 auditor | A06 | Reproducible simulation + focused computational paper |
| **TG-NEURO-001** FPCN-A/B × search/constraint | A10 Neuroscience Specialist | A02–A04 | A07 task design; A08 implementation; A09 analyses | A06 and independent neuro reviewer | Pilot-ready factorial study / potential Stage-1 Registered Report |
| **TG-TRANSFER-001** learning and invariant banking | A11 Learnability Specialist | A02–A04 | A08/A09; existing transfer repository | A06 | Longitudinal modelling and delayed-transfer manuscript |
| **TG-SHARED-001** shared intentionality A→R | A05 + A13 Conceptual Analyst | A02/A03/A12 | A08 multi-agent simulation and A09 audit | A06/A14 | Generative developmental theory + test programme |
| **TG-PHIL-001** public normativity / recursive models | A13 Argument Analyst + A12 Scholar | A02/A03 | Argument map and critical comparison; computational cross-checks only when appropriate | A14/A16 | Philosophical paper with strongest objections and responses |
| **TG-PSYCH-001** conditional emergence of g | A11 Psychometric Specialist | A02/A03 | A09/A08 and independent datasets | A06 | Psychometric developmental test after earlier gates |

**Approval convention:** The lead role proposes; the independent reviewer challenges; the **PI decides**. No two agent opinions constitute independent scientific verification unless they examine *independent source records or reproducible analyses*.

### 5.1 Responsibility / approval matrix

| Transition | Responsible worker | Evidence required | Who approves? |
|---|---|---|---|
| Select the paper's explanandum and primary claim | A01 + A05 | Source-pinned research contract | **PI** |
| Admit source to scholarly evidence ledger | A02 + A03 | DOI/URL, original passage, method, limits and contradiction flags | Human evidence reviewer / delegated authorised editor |
| Freeze confirmatory test/model comparisons | A05 + A07 + A09 | Protocol, rivals, outcome definitions, seeds, cost budget | **PI** |
| Dispatch Codex or cloud compute | A08 / orchestration service | Approved work order, data classification and compute policy | Authorised scientific/compute approval |
| Label results as scientific findings | A09 + A06 | Reproducible manifest, negative outcomes, independent review | **PI** |
| Produce a draft manuscript | A15 | Verified evidence or defended argument and provenance | Author/editor review |
| Release preprint, publication or identifiable data | **No agent** | Final ethics, AI-use, journal and claims checks | **PI only** |

## 6. Code, compute and model assignment

### 6.1 Runtime/code

| Layer | Code owner | Runtime | Current status |
|---|---|---|---|
| Contract schema, manifest, offline dossier | `research-factory/contracts.py`, `pipeline.py`, `cli.py` | Python 3.12 on workstation or isolated CI | **M0 implemented/tested** |
| Agno orchestration/drafting | `research-factory/agno_workflow.py` | Python, opt-in OpenAI or loopback Ollama | **Construction-tested; no live agent run verified** |
| Scholarly connectors and source verifier | Proposed `connectors/`, `knowledge/` | Read-only public-source access; private material on red node | **M1 planned** |
| Codex job composer/sandbox adapter | Proposed `compute/codex_adapter.py` | Workstation/container with repo allowlist | **M2 planned** |
| Numerical simulation and fitting | **Research-specific** repos | NumPy/SciPy/pandas/statsmodels; PyMC/JAX/PyTorch only when needed | Existing work in validation/transfer repos; *not part of M0 factory* |
| Independent audit | Proposed A09 with reproducibility runner | Separate process, pinned inputs and seeds | **M2 planned** |
| Persistent knowledge/approval service | Existing Postgres/Evidence Registry plus approved extension | Local red rail or approved hosted tenancy with RLS | **M1 read-only; authenticated writable layer deferred** |
| Manuscripts | `Trident-G-theory/papers/<paper_id>/` (proposed) | GitHub Markdown/LaTeX | **Planned** |

### 6.2 Model routing and boundaries

| Kind of work | Preferred worker | Alternative | Guardrail |
|---|---|---|---|
| Metadata, document labelling, bounded extraction | **Local Gemma via Ollama**, after quality test | Lightweight hosted model for public texts | Must preserve source quotes and extraction uncertainty |
| Verification of disputed support/contradictions | Hosted strong reasoning model **plus deterministic source access** | Human specialist | No model can verify a paper it has not retrieved |
| Difficult formal mathematical specification | Hosted frontier reasoning model | Human mathematician or independent model | Equations remain proposals until testable |
| Git/file code edits, tests and simulations | **Codex** in isolated branch; Python numerical runtime | Local development | No change to registered science without protocol amendment |
| Long Monte Carlo/fitting | Python workers on workstation or approved cloud CPU/GPU | Local trusted worker | Smoke/pilot/confirmatory; clean run manifests, cost limits |
| Philosophy and conceptual reconstruction | Hosted strong reasoning model with original primary texts | Specialist human reviewer | Clearly distinguish quotations, conceptual argument and empirical evidence |
| Flint locally | **Unverified optional challenger** | Gemma | Do not assume model ID, installation or competence |

**No live integration should presume installed Flint/Gemma or a running Ollama server.** Inspect `ollama list` and run a small human-labelled extraction benchmark before selecting a default. M0 does not make model API calls without explicit environment opt-in.

### 6.3 Where tasks and data run

```text
RED (trusted local)                     BLUE (public / approved)
private PDFs, raw participant data      GitHub code and synthetic test fixtures
private embeddings + redaction         GitHub Actions lint + deterministic unit tests
private approved statistics            public literature metadata, open simulations
local Ollama on loopback               approved cloud parameter sweeps
         |                                      |
         +-------- approved, redacted ----------+
                            |
                            v
                    HUMAN REVIEW GATE
                            |
                  public paper/figure release
```

Workstation: VS Code/Codex development, synthetic testing and review. Trusted red node: restricted research data and documents. Cloud workers: *only* approved public/synthetic or appropriately classified workloads. Object storage should persist run artefacts with checksums, retention and source commits; CI logs are not a permanent data archive.

**Implementation status note:** the initial metadata/claim-dossier *deterministic* slice is underway on [M1 PR #14](https://github.com/HRP-Transfer-Lab/research-platform/pull/14). Source-level reading, Zotero/OSF connections and actual A02/A03/A04 agent execution remain proposed, not implemented. See [M1 technical instructions](M1_RESEARCH_FACTORY_EVIDENCE_BRIDGE_V0_1.md).

## 7. M1 Evidence Bridge — exact first delivery

**First paper:** `TG-COMP-001` (Homeostatic Adaptive Intelligence). M1 creates a *reviewable evidence dossier*, **not** a claim that the cusp mechanism has been demonstrated.

**First tasks by role:**

1. **A01 Director** confirms contract SHA, paper scope, evidence questions and review queue.
2. **A02 Librarian** discovers rival accounts (network neuroscience, process overlap, mutualism, active inference, standard RL and recent criticality theories), and stores bibliographic IDs.
3. **A03 Source Verifier** checks metadata and actual relevant source text; attaches uncertainty where inaccessible.
4. **A04 Competing-Theory Analyst** records alternative explanations and distinct predictions, including evidence favouring rivals.
5. **A05 Formaliser** proposes a minimum computable model and failure conditions, without executing confirmatory analyses.
6. **A06 Independent Reviewer** examines original-source and scope gaps and returns a PI-ready decision packet.

**Proposed per-paper M1 dossier layout (not currently implemented):**

```text
TG-COMP-001/
  contract.json                   source-pinned research question
  evidence/
    bibliography.bib              source-verified entries only
    evidence_matrix.json          claim → primary-source relation and evidence level
    competing_theories.md         strongest alternatives and limits
    unresolved_claims.md          missing text, inconsistent findings, weak support
  design/
    proposed_formal_hypotheses.md
    competing_model_spec.md
    falsification_criteria.md
  review/
    evidence_approval.md          explicit human decision record
  manifests/
    retrieval_and_version.json    hashes, timestamps, source/license/access states
```

Until authenticated publishing/approval infrastructure exists, generated packets live in **untracked local run directories or a review-only branch**. The factory does not update the canonical Evidence Registry, theory or manuscript by side effect.

### M1 acceptance checklist

- [ ] Resolve and verify **one pinned** `TG-COMP-001` source commit; record checksums and version changes.
- [ ] Read-only bibliographic metadata lookup: Crossref/OpenAlex/PubMed; validate returned IDs and licence/access.
- [ ] Existing Evidence Registry and Zotero/OSF **read-only adapter** (do not duplicate releases).
- [ ] Store claim/source links with location, support status, reliability and clear *not checked* flags.
- [ ] Detect at least one **contradictory or rival** source for relevant principal claims where available.
- [ ] Reject invented DOI, unsupported claims, inaccessible original papers labelled as verified, or unapproved data routes.
- [ ] Produce deterministic evidence packets and save retrieval logs with provenance and data tier.
- [ ] Separate evidence from argument: philosophical texts use interpretation provenance, not experimental-effect labels.
- [ ] Run automated tests and independent review with deliberately missing, contradictory and malformed sources.
- [ ] Demonstrate that the factory can conclude **insufficient evidence**, with no pressure to publish.
- [ ] PI reviews scope, source permissions and the M1 bridge before any public scientific claims.

**M1 exit gate:** An independent reviewer can trace every substantial claim to its verified original source or a conspicuous unresolved status, see credible competitors, and approve or reject the proposed experiment. This is a stricter requirement than formatting a bibliography.

**M1b implementation note (13 November 2026):** [Grounded Agno Source Review v0.1](M1B_GROUNDED_AGNO_SOURCE_REVIEW_V0_1.md) implements A02/A03/A04 with opt-in local source text, a deterministic exact-quote gate and an optional Europe PMC OA import. These are executable bounded roles, **not** independent human source verification. Original context and semantic claim-support review remain pending.

## 8. Implementation sequence and stop rules

| Milestone | Priority | Delivery | Cannot advance before |
|---|---|---|---|
| **M0** | Complete as draft | Contract validator, offline dossier, opt-in three-role Agno constructor, 19 CI checks | PI reviews PR #13; do not merge automatically |
| **M1** | **Next** | Read-only scholarly evidence connector, verification ledger, A02–A04 role workflows | No evidence release without reviewer |
| **M2** | After M1 design gate | Codex task adapter, safe worker, formal simulations and statistics | No confirmatory compute without frozen contract |
| **M3** | After evidence+results | Publication Editor, citation/figure audit, manuscript packaging | No automatic preprint or journal submit |
| **M4** | Parallel once M1 is stable | Neuro, psychometrics, shared-intentionality and philosophical specialists | Distinct claims standards for each track |
| **M5** | After operational proof | Durable authenticated approvals, local-model benchmarks, optional AgentOS, approved cloud batch | No public endpoints or unrestricted tools by default |

**Stop rules:** unverifiable citations, source mismatches, unapproved sensitive-data access, model output presented as observed evidence, modified confirmatory analyses after results, and missing human approval must **block** the next stage. Negative and null results are first-class output.

## 9. Governance and unresolved design choices

This plan is a reviewed **target architecture** and assignment contract, not proof that a software agent implements each role. Before implementation, the PI should approve:

- Whether manuscript **source** for all tracks belongs in the current theory repository or whether future philosophical work merits a separately governed repository.
- Whether to adopt the existing Evidence Registry's authorised read-only views for scholarly papers or add a sibling research-reference index with the same provenance standards.
- Which red-node machine and secrets manager host private corpus access; **no private connector tokens in Git**.
- Whether to run the M1 source-verification pipeline without an LLM initially (recommended), then add A02–A04 through bounded Agno tasks.
- Which cloud provider, compute budget and local Ollama model IDs are actually available; defer purchase/provisioning decisions until an M2 workload is benchmarked.

### Related sources

- [M0 factory code and development plan — PR #13](https://github.com/HRP-Transfer-Lab/research-platform/pull/13)
- [HRP Evidence Registry](https://github.com/HRP-Transfer-Lab/research-platform/tree/main/components/evidence-registry)
- [Cloud Lab Ground Truth](https://github.com/HRP-Transfer-Lab/Cloud-Lab-Ground-Truth/blob/main/CLOUD_LAB_GROUND_TRUTH.md)
- [Computational-validation AGENTS rules](https://github.com/HRP-Transfer-Lab/trident-control-architecture-validation/blob/main/AGENTS.md)
- [Trident-G current draft theory — PR #1](https://github.com/HRP-Transfer-Lab/Trident-G-theory/pull/1)
