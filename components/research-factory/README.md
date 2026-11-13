# HRP Research & Publication Factory (M0 bootstrap)

The factory sits inside the existing Trident Cloud Lab, using its G-Loop as a **research control framework**. It does not replace the operational Evidence Registry, the Trident-G theory repository, the model-validation M-series or the established private/public data boundaries.

**Current status:** implemented M0 *proposal-only bootstrap* (not a deployed or fully autonomous research team). See [development plan](../../docs/RESEARCH_PUBLICATION_FACTORY_DEVELOPMENT_PLAN_V0_1.md), [repository and agent assignment plan v0.2](../../docs/RESEARCH_FACTORY_REPOSITORY_AND_AGENT_ASSIGNMENT_PLAN_V0_2.md), and the [declarative agent-assignment manifest](configs/agent_assignments.v0.2.json).

## What is actually implemented

- Strict JSON Publication Research Contract validation with an **immutable source commit**.
- Single-primary-explanandum contracts and fair rivals/falsification fields.
- An **offline kickoff** that creates local, untracked manifest and a scope-review packet.
- A three-role Agno workflow builder (Director → Formaliser → Independent Reviewer) **without tools**, only with explicit model-call permission.
- An Agno adapter for OpenAI (hosted) or Ollama (loopback local) but **no installed model, credential or service is assumed**.
- Tests for invalid contracts, source mutability, restricted-cloud denial, opt-in permissions and publication blocks.
- GitHub Actions test job using public/synthetic test fixtures.
- A **declarative-only** 16-role / six-paper assignment plan; this is not an executable multi-agent registration or an authorisation grant.

The factory cannot publish, write to external research repositories, read private data or autonomously launch simulations. These are future gated milestones.

## Running offline (no model credentials or internet required)

From this component directory, with Python 3.12+:

    python -m pip install -e ".[dev]"
    hrp-factory validate configs/TG-COMP-001.json
    hrp-factory kickoff configs/TG-COMP-001.json --out runs
    python -m pytest -q

The kickoff prints the location of a newly created **run_manifest.json** and **review_packet.md**. The run directory is ignored by Git. It is a proposal, not a scientific result or an approval.

The sample theory source is pinned to the exact **Trident-G v0.4 draft commit**; confirm the commit remains the intended research source before starting a paper.

## Optional Agno drafting (deliberate opt-in)

Install the optional agents extra and configure a model/provider locally:

    python -m pip install -e ".[agents,dev]"

For explicitly permitted **public/synthetic** contract content, a hosted model can be enabled with local environment variables:

    export HRP_ALLOW_MODEL_CALLS=YES
    export OPENAI_API_KEY=YOUR_LOCALLY_CONFIGURED_KEY
    hrp-factory agno-draft configs/TG-COMP-001.json --provider openai --out runs

Or, after checking that Ollama and the selected model are installed locally:

    export HRP_ALLOW_MODEL_CALLS=YES
    export OLLAMA_HOST=http://127.0.0.1:11434
    hrp-factory agno-draft configs/TG-COMP-001.json --provider ollama --model YOUR_INSTALLED_MODEL_ID --out runs

These examples do not set up credentials or launch models. An Agno draft has **no access to literature/search tools** at this milestone and may not be represented as verified scholarship; its output is labelled and stored only inside the local run folder.

**Do not expose the Ollama service publicly.** For restricted-local data, the adapter blocks hosted providers entirely and permits only loopback Ollama.

## Initial paper

**TG-COMP-001 — Homeostatic Adaptive Intelligence.** Source-pinned theory v0.4; primary explanandum = adaptive intelligence. The first dossier recommends fair continuous/RL/hidden-state alternatives and falsifying tests. It must not claim explanation of psychometric g or human neural criticality from an engineering smoke test.

## M1a Evidence Bridge — first vertical slice (stacked draft PR #14)

The first **read-only evidence integration** builds on M0. It has a strict curated `TG-COMP-001` DOI seed and creates a review-ready claim/evidence dossier. Crossref/OpenAlex metadata lookups are possible **only with explicit network permission**; the existing public Evidence Registry release can be inspected locally without mutation. **No source-support claims are verified** from metadata alone, and every claim remains unresolved until original methods/results are checked.

From this folder, after installing with `pip install -e ".[dev]"`:

```bash
hrp-factory evidence-dossier configs/TG-COMP-001.json \
  --candidates configs/TG-COMP-001-evidence-candidates.json \
  --out runs
```

Optional **public metadata only**:

```bash
export HRP_ALLOW_PUBLIC_METADATA_LOOKUP=YES
hrp-factory evidence-dossier configs/TG-COMP-001.json \
  --candidates configs/TG-COMP-001-evidence-candidates.json \
  --public-metadata --out runs
```

See the [M1 implementation boundary and acceptance checklist](../../docs/M1_RESEARCH_FACTORY_EVIDENCE_BRIDGE_V0_1.md). This does not yet integrate live Agno literature-reading agents, Zotero/OSF, user records, or a publication workflow. The stacked M1 PR targets the unmerged M0 feature branch, so **neither M0 nor M1 has been merged to main**.

## M1b — source-grounded Agno roles (review branch)

See [M1b Grounded Source Review](../../docs/M1B_GROUNDED_AGNO_SOURCE_REVIEW_V0_1.md). This optional next step implements A02 Evidence Librarian, A03 Source Verifier and A04 Competing-Theory Analyst with structured Agno outputs, deterministic quote checking, and a local-only Europe PMC open-access importer. Model runs and public full-text lookups require separate explicit opt-in. No interpretation is approved automatically.

### Offline fictional smoke test

```bash
python scripts/demo_source_review.py
```

### Optional local-source inspection

```bash
hrp-factory source-review configs/TG-COMP-001.json \
  --candidates configs/TG-COMP-001-evidence-candidates.json \
  --source-bundle runs/oa-src-004/source-bundle.json --out runs
```

The provided source bundle must first be imported or authorised and pinned; the command does not magically retrieve full text. Hosted models cannot receive local-only sources. Human original-source context and DOI/rights review are still required.

## Next steps

1. Have the PI review the M0 PR and the publication contract.
2. Connect existing Evidence Registry/Zotero metadata through a read-only citation layer, with source verification gates.
3. Add a bounded Codex PR task producer and independent test/audit runner.
4. Introduce a model-run manifest and smoke/pilot workers before any confirmatory compute.
5. Add authenticated approvals and durable AgentOS orchestration only after controls and budgets pass review.
