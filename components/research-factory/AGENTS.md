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

## Handover contract

A work order must record the paper ID, pinned source commit, primary explanandum, competing accounts, failure conditions, provenance, data tier, code/compute budget and human review gate.
