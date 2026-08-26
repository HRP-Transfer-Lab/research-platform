# Trident Cloud Lab

Trident Cloud Lab is a modular research platform for computational neuroscience workflows.

It is designed to combine:
- a knowledge bank (papers, notes, concept graph)
- app telemetry ingestion and statistical analysis
- cloud-based experiment and survey delivery
- computational modeling runs
- agent-based research scouting and synthesis

The repository is structured for VSCode + Codex development, GitHub automation, Obsidian free-tier graph exploration, and citation/data integration through Zotero and OSF.

Ground-truth and protocol sources:
- Ground truth: `Trident-Cloud-Lab/Cloud-Lab-Ground-Truth`
- Protocol source: `Trident-Cloud-Lab/Trident-G-theory`

## Core capabilities

1. Knowledge bank with linked notes
- markdown-first vault for paper, concept, and dataset notes
- wiki-link graph that Obsidian can visualize
- provenance-aware note templates for evidence tracking

2. Reference and repository integrations
- Zotero sync for citations, metadata, and library organization
- OSF sync for projects, files, datasets, and preprints
- normalized metadata layer so references can be queried consistently

3. RAG-backed research querying
- semantic retrieval over notes and source documents
- citation-grounded answers with source identifiers
- priority retrieval from your curated corpus before open web sources

4. Cognitive app data pipeline
- event schema and ingestion for cognitive training/assessment apps
- validation and quality checks before analysis
- reproducible notebooks for descriptive and longitudinal analyses

5. Cloud experiment platform
- configurable online tasks and surveys
- participant/session tracking and exportable datasets
- traceable experiment versions linked to references

6. Computational modeling environment
- reproducible model runs with parameter manifests
- artifact tracking for outputs and metrics
- support for simulation and model fitting workflows

7. Agentic research intelligence
- automated paper scouting and summarization
- proposal generation for concept links and hypotheses
- review gate to prevent unverified auto-writes

## Repository map

```text
research-platform/
  README.md
  docs/
    ARCHITECTURE.md
    EVIDENCE_REGISTRY_V1_1_IMPLEMENTATION_PLAN.md
    IMPLEMENTATION_PLAN.md
  components/
    knowledge-bank/
      README.md
      obsidian-vault/
        README.md
      zotero-sync/
        README.md
      osf-sync/
        README.md
      rag/
        README.md
    data-pipeline/
      README.md
      schemas/
        README.md
      notebooks/
        README.md
    experiment-cloud/
      README.md
    computational-modeling/
      README.md
    research-intel-agents/
      README.md
  infra/
    db/
      README.md
    vector/
      README.md
    orchestration/
      README.md
  workflows/
    github-actions/
      README.md
  configs/
    env/
      README.md
```

## Operating principles

1. No citation, no claim.
2. Separate speculative hypotheses from evidence-backed conclusions.
3. Keep Obsidian as an exploration UI; keep canonical metadata in DB + git-tracked files.
4. Require human approval for publish actions and high-impact graph updates.
5. Maintain audit logs for sync jobs, retrieval runs, and agent actions.

## Where to start

1. **For the current Evidence Registry upgrade:** `docs/EVIDENCE_REGISTRY_V1_1_IMPLEMENTATION_PLAN.md`
2. Review architecture: `docs/ARCHITECTURE.md`
3. Start with general platform first steps: `docs/FIRST_STEPS_IMPLEMENTATION_PLAN.md`
4. Use the wider platform roadmap: `docs/IMPLEMENTATION_PLAN.md`
5. Review deployment placement: `docs/DUAL_MACHINE_IMPLEMENTATION.md`
6. Configure integration secrets: `configs/env/README.md`
