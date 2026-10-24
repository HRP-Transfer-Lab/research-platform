# Module Knowledge Graph Engine

## Purpose

Build one canonical, provenance-aware knowledge graph for each teaching unit/week from approximately 3–4 core readings plus optional learning outcomes, assessment instructions and seminar notes.

The canonical graph is the source for multiple derived teaching views:

1. Core-concept tree
2. Prerequisite graph
3. Theory map
4. Evidence graph
5. Construct map
6. Debate map
7. Assessment map
8. Reading map
9. Student revision map

These views must be projections of the same reviewed graph, not nine independent LLM summaries.

## Pipeline

```text
source readings
→ structure-preserving extraction
→ source passages with provenance
→ embeddings
→ candidate semantic clusters
→ constrained concept/claim/relation extraction
→ cross-reading reconciliation
→ reviewed canonical graph
→ derived teaching views
```

## Canonical object types

- concept
- construct
- theory
- claim
- mechanism
- study
- measure
- finding
- limitation
- method
- debate
- learning_outcome
- assessment_criterion
- reading
- passage

## Epistemic status

Every substantive graph edge carries one of three statuses:

- `E1_EXPLICIT` — the source explicitly states the relationship.
- `E2_SYNTHESISED` — the relationship is a source-grounded synthesis across passages/readings.
- `E3_PEDAGOGICAL` — the relationship is useful for teaching organisation but is not itself asserted by the source.

A fourth state, `UNRESOLVED`, is available for candidates requiring review.

## Provenance rule

No substantive node or edge should enter the reviewed graph without provenance. At minimum retain:

- reading id
- source filename or citation id
- section/heading
- page when available
- passage id
- supporting text span or stable text hash
- extraction/review status

The existing HRP Transfer Lab rule still applies: semantic similarity is a retrieval/reconciliation aid, not evidence that two constructs are identical or that a relationship is true.

## Recommended local inference

Initial local setup:

- embeddings: `qwen3-embedding:0.6b` through Ollama
- extraction/reconciliation: configurable LLM adapter
- graph operations: NetworkX
- durable semantic store later: PostgreSQL + pgvector

The graph JSON format is model-independent.

## Repository layout

```text
UoE/module-knowledge-graph/
  config/
    ontology.yaml
    models.example.yaml
  schemas/
    unit_manifest.schema.json
    knowledge_graph.schema.json
  src/
    module_graph.py
  examples/
    unit-template/
      unit.yaml
      readings/
        README.md
  outputs/
    README.md
```

## First milestone

The first milestone is intentionally modest:

1. define a unit and its readings;
2. ingest already-extracted UTF-8 text/markdown;
3. create stable passage records;
4. validate candidate graph JSON against the schema;
5. export graph projections once reviewed.

PDF/DOCX extraction, Ollama embedding calls, automatic clustering and LLM extraction are subsequent adapters rather than assumptions embedded in the core schema.
