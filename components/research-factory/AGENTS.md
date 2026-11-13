# Codex and agent rules — HRP research factory (M0)

Applies to everything under this folder; also read:
- ../../docs/RESEARCH_PUBLICATION_FACTORY_DEVELOPMENT_PLAN_V0_1.md
- ../../docs/RESEARCH_FACTORY_REPOSITORY_AND_AGENT_ASSIGNMENT_PLAN_V0_2.md
- configs/agent_assignments.v0.2.json (declarative assignment plan; no runtime permission)
- ../../docs/G_LOOP_ADAPTIVE_LEARNING_KERNEL.md
- ../../docs/DUAL_MACHINE_IMPLEMENTATION.md
- HRP-Transfer-Lab/trident-control-architecture-validation/AGENTS.md before touching its code.

## Non-negotiables

1. Treat all theory claims as **hypotheses** until a reviewer verifies original evidence.
2. Use source-pinned publication contracts; do not alter canonical theory or frozen M-series from here.
3. No autonomous preprint submission, journal submission, emails, external data release or public evidence claim.
4. Never commit secrets, private PDFs, participant-identifiable data, embeddings of private material, or raw private telemetry.
5. Work locally and offline by default. Hosted model calls require explicit opt-in and a permissible data tier.
6. No model gets shell, GitHub write, secret, remote publication or unrestricted web tools in M0.
7. Keep evidence and proposal records separate. Preserve negative results and contradictions.
8. Show tests and exact reproducibility metadata; no numerical result without a run manifest.
9. Submit proposals and code on a review branch/PR. A human PI approves scientific protocols and publication.
10. Do not silently revise the scope, rival models, primary outcome, seeds or stopping rules after inspection.

Roles listed in the v0.2 agent plan remain **planned** unless the M0 workflow constructor and tests actually implement them. The manifest must not be interpreted as granting tool access or approval.

## M0 implementation boundary

Allowed: publication-contract validation, offline review dossiers, optional non-tool-using Agno drafting, tests, documentation and CI.

Not yet allowed: AgentOS internet deployment, automated citation verification, unsupervised Codex shell execution, public scholarly submissions, computational confirmatory jobs or arbitrary database mutations.

## M1a evidence bridge boundary (stacked feature branch)

Allowed: a strict curated DOI/claim seed; **fixed-host, read-only Crossref/OpenAlex metadata** with explicit `HRP_ALLOW_PUBLIC_METADATA_LOOKUP=YES`; an approved *public-release* Evidence Registry snapshot inspector; source identity consistency checks; a candidate-only evidence dossier and local human review packet; synthetic/fixture-based tests.

**No original scientific claim is verified by metadata.** Full-text methods/results, contradiction adjudication, Zotero/OSF access and agent-based scholarly reading are outside this first slice. The Evidence Registry remains operationally authoritative for its own intervention data; never overwrite it or interpret its approved routes as validation of a Trident-G causal claim.

All text intended for human publication must pass actual source and claim review. Local run artefacts (including downloaded public metadata if enabled) remain under Git-ignored runs/. The CI artefact is public/synthetic candidate material and must be clearly labelled *UNVERIFIED*.

## Handover contract

A work order must record the paper ID, pinned source commit, primary explanandum, competing accounts, failure conditions, provenance, data tier, code/compute budget and human review gate.
