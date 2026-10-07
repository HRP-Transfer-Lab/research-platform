# Architecture

## Product goal

Mindware Lab is a single research workspace with five integrated modules:
1. Knowledge bank (notes, papers, concept graph)
2. Cognitive app data pipeline and statistical analysis
3. Cloud experiment and survey builder
4. Computational modeling environment
5. Agentic research intelligence

These modules are coordinated by the canonical adaptive learning kernel described in:

- `docs/G_LOOP_ADAPTIVE_LEARNING_KERNEL.md`

The G-Loop is the cross-cutting research-control layer. It treats each programme as an adaptive trajectory rather than a static workflow:

```text
SENSE
→ LOCATE
→ RECALL / GENERATE
→ BOUNDED HYPOTHESIS WORKSPACE
→ FORECAST COUNTERFACTUAL FUTURES
→ EVALUATE
→ COMMIT / PREDICT
→ ACT / TEST
→ COMPARE
→ ADAPT
→ BANK
↺
```

It distinguishes productive local tuning from deliberate reopening of the search space when returns flatten, the model stops fitting, or changed conditions invalidate a previously reliable strategy. Banked methods remain context-bounded and can be recalled, adapted, recombined or revalidated when structurally similar situations arise.

Between long-term banked memory and commitment, the architecture includes a **bounded hypothesis workspace**. This is a temporary coordination layer that holds a small set of live candidate methods or explanations, keeps each candidate bound to the current goal and assumptions, forecasts counterfactual consequences, and compares candidates under evidence, cost, risk, reversibility, viability, learning value and optionality constraints. It is functionally analogous to a working-memory workspace, but no claim is made that the software literally instantiates human working memory.

## Shared data backbone

Use one canonical storage layer:
- relational store: PostgreSQL
- vector store: pgvector (same Postgres) or dedicated vector DB
- object storage: PDFs, experiment exports, model artifacts

Core entities:
- `paper`
- `concept`
- `concept_link`
- `note`
- `zotero_item`
- `osf_node`
- `osf_file`
- `osf_preprint`
- `app_event`
- `session`
- `participant`
- `experiment`
- `model_run`
- `agent_run`

As the G-Loop layer is implemented, the canonical data model should additionally support stable references for:
- current programme / protocol state;
- trajectory horizon and state;
- prospective predictions;
- interventions/tests;
- outcomes and prediction errors;
- bounded lessons / banked rules;
- applicability conditions and failure boundaries;
- changed-condition transfer tests;
- strategy recall/applicability judgements;
- bounded hypothesis-workspace records;
- candidate source: recalled / adapted / recombined / newly generated;
- candidate assumptions and supporting/conflicting evidence;
- forecasted counterfactual futures;
- cost, risk, reversibility, learning-value and optionality fields;
- candidate status: live / rejected / selected / deferred;
- discriminating observations or tests used to compare candidates.

A learned causal graph is not required for the first implementation. The platform should remain graph-ready without representing sparse observational associations as causal facts.

## Integration boundaries

- Obsidian free tier reads and edits markdown in `components/knowledge-bank/obsidian-vault`.
- Zotero sync writes normalized citation metadata to `zotero_item` and a markdown citation index.
- OSF sync writes normalized project/file/preprint metadata to `osf_node`, `osf_file`, and `osf_preprint`.
- RAG retrieval uses chunks derived from notes and PDFs, joined to citation ids and OSF provenance references.
- Agent outputs are proposals until they pass review rules.
- G-Loop strategy recall proposes potentially relevant prior methods; retrieval or semantic similarity does not itself establish transfer or authorise reuse.
- Reopening proposals must name the dimension being changed and remain prospective/testable.
- The live hypothesis workspace must remain bounded and reviewable; more alternatives are not automatically better.
- Counterfactual forecasts remain distinct from observed evidence.
- Candidate selection should be explicit about the current objective, hard constraints, cost, downside, reversibility and information value.

## Adaptive learning boundary

The research platform should preserve a clear distinction among three levels of change:

1. **Parameter tuning** — optimise within the present model or protocol.
2. **Strategy/protocol optimisation** — test a materially different policy or implementation.
3. **Model/landscape revision** — change the representation, hypothesis family or problem formulation.

The scale of revision must match the scale of the evidence.

The canonical trajectory grammar is:

```text
GROWING
→ TUNING
→ PLATEAU
→ REOPENING
→ VALIDATING
→ BANKED
→ richer future search
```

A large prospective prediction mismatch may trigger earlier diagnosis/reopening without requiring a long plateau.

## Guardrails

- No silent overwrites of manually edited notes.
- Evidence and speculative notes use different templates.
- Participant data workflows require explicit privacy checks and retention policy.
- OSF publish or preprint update flows are always human-approved actions.
- No plateau from one flat observation.
- No prospective prediction written after the outcome.
- No banking from one unreplicated success.
- No transfer claim without a changed-condition test.
- No semantic similarity treated as evidence of transfer.
- No automatic inference that a behavioural plateau is a neural criticality transition.
- Preserve provenance, counter-evidence, failed tests and reopening triggers.
- No unbounded hypothesis proliferation.
- No candidate selected merely because it was recalled first or generated most fluently.
- No counterfactual forecast represented as an observed result.
