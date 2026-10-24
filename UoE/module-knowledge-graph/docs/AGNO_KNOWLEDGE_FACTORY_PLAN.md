# Agno UoE Knowledge Factory Plan

## Purpose

Extend the UoE Module Knowledge Graph Engine into an agentic, provenance-first teaching and curriculum-intelligence system orchestrated with Agno.

The system should support three initial University of Essex Online modules:

- Introduction to Cognitive Psychology
- Biological Psychology
- Health Psychology

The long-term direction is a reusable course-intelligence platform that can support lecturers, programme teams and, after academic approval of the canonical graph, student-facing learning tools.

The core architectural rule is:

> **Agents may extract, reconcile, criticise and propose. The reviewed canonical knowledge graph remains the authority layer.**

The nine teaching views are derived projections from the same canonical graph. They are not independently generated summaries.

---

## 1. System objective

The system objective is:

> Maximise pedagogically useful representation of assigned course material while preserving source fidelity, provenance, epistemic boundaries and academic review.

This differs from the Kastel commercial factories, where the principal optimisation target is sustainable profitability. Here the protected quantities are:

- source fidelity;
- provenance;
- distinction between evidence and inference;
- distinction between course content and general model knowledge;
- pedagogical usefulness;
- academic control;
- copyright and privacy boundaries.

---

## 2. High-level architecture

```text
                    UoE KNOWLEDGE SYSTEM
                            │
                            ▼
                     MODULE FACTORIES
            ┌───────────────┼────────────────┐
            ▼               ▼                ▼
     Cognitive Psych   Biological Psych   Health Psych
            │               │                │
            └───────────────┼────────────────┘
                            ▼
                       UNIT FACTORY
                            │
                            ▼
                     UNIT SUPERVISOR
                            │
         ┌──────────────────┼───────────────────┐
         ▼                  ▼                   ▼
   INGEST/STRUCTURE    EMBEDDING AGENT     EXTRACTION AGENT
      AGENT              Qwen3                LLM
         │                  │                   │
         └──────────────────┼───────────────────┘
                            ▼
                   RECONCILIATION AGENT
                            │
                            ▼
                    GRAPH CRITIC AGENT
                            │
                            ▼
                 CANDIDATE KNOWLEDGE GRAPH
                            │
                            ▼
                      REVIEW GATE
                            │
                            ▼
                  CANONICAL UNIT GRAPH
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
             VIEWS      ASSESSMENT    REVISION
```

The Agno layer orchestrates cognitive labour and tool use. It does not replace the canonical graph, schemas, provenance rules or deterministic validation layer.

---

## 3. Agent roles

### 3.1 Unit Supervisor

Responsibilities:

- loads the unit manifest;
- checks required inputs;
- sequences agent work;
- enforces model and tool permissions;
- prevents unreviewed graph writes;
- maintains processing status;
- routes uncertain cases to the review queue;
- requests regeneration of derived views after approved graph changes.

The supervisor should not invent course knowledge itself.

### 3.2 Ingest and Structure Agent

Responsibilities:

- identify source format;
- preserve document hierarchy;
- create page/section/passage records;
- retain reading id, citation id and source path;
- produce stable passage ids and hashes;
- flag extraction uncertainty.

Preferred processing order:

```text
embedded PDF/DOCX text
→ structure-preserving extraction
→ if unusable, local OCR fallback
→ passage records
```

The original source remains the ultimate evidence object.

### 3.3 Embedding Agent

Initial local model:

```text
qwen3-embedding:0.6b
via Ollama
```

Responsibilities:

- embed passages;
- embed candidate concept labels/definitions;
- identify semantic neighbours;
- propose candidate synonym/overlap clusters;
- support semantic search over the unit corpus.

Embedding similarity must never itself establish concept identity or factual relationships.

Private embeddings remain outside Git.

### 3.4 Knowledge Extraction Agent

Initial candidate model:

```text
flint:latest
```

Responsibilities:

extract constrained candidate objects:

- concept;
- construct;
- theory;
- claim;
- mechanism;
- study;
- measure;
- finding;
- limitation;
- method;
- debate.

and candidate edges using the controlled ontology.

Requirements:

- use source passage only unless explicitly performing synthesis;
- return structured JSON;
- retain provenance;
- do not silently use outside knowledge;
- mark all extracted graph content as `candidate`.

### 3.5 Semantic Reconciliation Agent

Inputs:

- candidate nodes;
- embedding-neighbour proposals;
- source passages;
- cross-reading metadata.

Responsibilities:

classify candidate relationships as:

- SAME_CONCEPT;
- RELATED_BUT_DISTINCT;
- BROADER_THAN;
- NARROWER_THAN;
- UNCERTAIN.

It should also identify:

- terminology variation;
- competing theories;
- directly linked readings;
- duplicated claims;
- apparently conflicting claims;
- construct/measure confusion.

No automatic merge enters the canonical graph without review during the initial implementation.

### 3.6 Graph Critic Agent

Purpose:

Act as an adversarial quality-control layer.

Checks:

- unsupported nodes or edges;
- source mismatch;
- missing provenance;
- over-generalisation;
- correlation represented as causation;
- construct conflated with measure;
- method conflated with result;
- duplicate concepts;
- accidental consensus generated from debate;
- missing limitations;
- E1/E2/E3 misclassification;
- source claims expanded using model background knowledge;
- relationships whose confidence exceeds source support.

Output:

```text
review queue
not silent mutation
```

### 3.7 Pedagogy/View Agent

The Pedagogy Agent queries the reviewed canonical graph and generates the nine views.

It does not independently reinterpret the original readings unless explicitly asked to resolve a missing graph relation.

---

## 4. Canonical graph as authority layer

The canonical graph stores reviewed course knowledge.

```text
SOURCE MATERIAL
      ↓
candidate extraction
      ↓
candidate graph
      ↓
review
      ↓
CANONICAL GRAPH
      ↓
derived views
```

The following must remain distinct:

```text
source truth
≠
model synthesis
≠
pedagogical organisation
```

The current epistemic statuses remain:

### E1_EXPLICIT

The source explicitly states the relationship.

### E2_SYNTHESISED

The relationship is justified by combining source material.

### E3_PEDAGOGICAL

The relationship is useful for teaching organisation but is not itself a claim made by the source.

### UNRESOLVED

The system cannot yet justify the relationship strongly enough.

---

## 5. The nine derived views

The views should be graph projections rather than separate free-form generations.

### Core-concept tree

Primary graph inputs:

- concept;
- construct;
- IS_A;
- PART_OF;
- BROADER_THAN;
- NARROWER_THAN;
- importance.

Purpose:

What students fundamentally need to understand.

### Prerequisite graph

Primary edges:

- REQUIRES;
- BUILDS_ON;
- NEEDED_TO_UNDERSTAND;
- PRECEDES.

Purpose:

What needs to be understood before what.

### Theory map

Primary objects:

- theory;
- mechanism;
- claim.

Primary edges:

- EXPLAINS;
- PREDICTS;
- EXTENDS;
- CONTRASTS_WITH;
- CHALLENGES;
- SUPPORTS.

### Evidence graph

Canonical pattern:

```text
claim
→ study
→ method
→ finding
→ limitation
```

Purpose:

Show what evidence supports, qualifies or challenges a claim.

### Construct map

Canonical pattern:

```text
construct
→ operationalisation
→ measure
→ observed result
```

The system must preserve these distinctions.

### Debate map

Primary edges:

- CHALLENGES;
- QUALIFIES;
- CONTRASTS_WITH;
- ALTERNATIVE_EXPLANATION;
- FAILS_TO_REPLICATE;
- COMMENTS_ON.

Purpose:

Represent genuine disagreement and criticism without collapsing material into false consensus.

### Assessment map

Additional inputs:

- learning outcomes;
- assessment instructions;
- assessment criteria;
- seminar material.

Canonical path:

```text
learning outcome
→ required concept/theory
→ supporting evidence
→ seminar/activity
→ assessment criterion
```

### Reading map

Purpose:

Show which readings are central to which concepts, theories, claims and debates.

The map may distinguish:

- mentioned;
- substantively discussed;
- central to argument.

### Student revision map

A deliberately compressed projection of the reviewed graph.

Typical contents:

- 10–15 core concepts;
- 5–8 important relationships;
- 3–5 major theories;
- key studies/evidence;
- major debates;
- common misconceptions;
- questions students should be able to answer.

Student-facing views should only use reviewed graph content.

---

## 6. Module factories and unit factories

Each module is a persistent Agno factory sharing the same underlying engine.

```text
MODULE FACTORY
     │
     ├── Unit 1 factory
     ├── Unit 2 factory
     ├── Unit 3 factory
     └── ...
```

Each unit gets its own canonical graph first.

A later module-level reconciliation stage builds:

```text
unit graphs
→ cross-unit reconciliation
→ module graph
```

The module graph can then detect:

- concepts assumed before introduction;
- unnecessary duplication;
- missing prerequisites;
- contradictory terminology across units;
- under-covered learning outcomes;
- over-assessed but under-taught concepts;
- evidence imbalance across theories;
- poor progression from descriptive to evaluative learning.

This creates a course-design audit capability beyond simple concept mapping.

---

## 7. Recommended local tool allocation

| Function | Initial tool |
|---|---|
| PDF/DOCX parsing | deterministic local parser |
| OCR fallback | local OCR engine |
| Embeddings | Qwen3 Embedding 0.6B via Ollama |
| Semantic retrieval | vector similarity / pgvector |
| Candidate extraction | Flint |
| Relation classification | Flint |
| Reconciliation | Flint + Qwen candidate neighbours |
| Graph criticism | Flint |
| Graph operations | Python / NetworkX |
| Validation | JSON Schema + deterministic checks |
| Agent orchestration | Agno |
| Long-term vector storage | PostgreSQL + pgvector |
| Human review | lecturer/reviewer |

Cloud models may later be added as optional, explicitly authorised adapters for difficult extraction/reconciliation tasks.

---

## 8. Agent authority model

Initial autonomy should be conservative.

| Level | Capability | Authority |
|---|---|---|
| A0 | Read local authorised sources | automatic |
| A1 | Extract candidate objects | automatic |
| A2 | Propose relations/merges | automatic |
| A3 | Generate candidate views | automatic |
| A4 | Modify canonical graph | human approval |
| A5 | Change ontology, learning objectives or assessment interpretation | explicit owner control |

The key rule is:

> A model-generated instruction is never sufficient authority to alter reviewed academic truth.

---

## 9. Data and copyright boundary

Original licensed readings should remain local or within an authorised institutional environment unless redistribution rights are clear.

Preferred pattern:

```text
licensed reading
→ local processing
→ passage ids / hashes / citation metadata
→ reviewed derived graph
→ pedagogical views
```

Do not commit by default:

- copyrighted source PDFs;
- full extracted copyrighted text;
- private embeddings;
- student submissions;
- identifiable student data.

Git may contain:

- schemas;
- manifests;
- citation metadata;
- ontology;
- code;
- reviewed graph structures;
- provenance-safe short excerpts where lawful;
- derived teaching views.

---

## 10. Commercialisation-ready design principles

The prototype should preserve commercial optionality without prematurely building a SaaS product.

Design now for:

### Multi-level tenancy

```text
institution
→ programme
→ module
→ unit
→ reading
```

### Model independence

Embedding and reasoning models must remain swappable.

### Provenance

Every substantive graph claim must remain traceable.

### Human approval

AI proposes; academics govern canonical course truth.

### Shared canonical graph

All teaching, assessment and student views derive from one reviewed representation.

### Private processing option

The architecture should support local/on-premise processing for universities that cannot send licensed course materials to external model providers.

---

## 11. Potential commercial layers

### Layer 1 — Lecturer Course Intelligence

Inputs:

- module specification;
- learning outcomes;
- readings;
- seminar materials;
- assessment instructions;
- marking criteria.

Outputs:

- the nine views;
- alignment and coverage warnings;
- unit/module graph.

### Layer 2 — Programme Curriculum Intelligence

Cross-module functions:

- progression;
- prerequisite coverage;
- duplication;
- curriculum gaps;
- graduate-outcome mapping;
- accreditation evidence.

### Layer 3 — Student Learning Interface

Only from academically reviewed graph content:

- revision maps;
- evidence-grounded explanations;
- theory comparison;
- adaptive remediation;
- quizzes;
- source-traceable tutoring.

The initial commercial position should be closer to:

> **Evidence-grounded course intelligence**

than a generic AI tutor.

---

## 12. Implementation stages

### Stage 1 — deterministic substrate

Already begun:

- module/unit folder structure;
- unit manifests;
- graph schema;
- controlled ontology;
- provenance model;
- basic CLI.

### Stage 2 — local ingestion

Add:

- PDF/DOCX parser;
- local OCR fallback;
- structured passage store;
- extraction quality flags.

### Stage 3 — local semantic layer

Add:

- Ollama/Qwen embedding adapter;
- vector store;
- semantic neighbour search;
- candidate concept clusters.

### Stage 4 — Agno extraction factory

Add:

- Unit Supervisor;
- Knowledge Extraction Agent;
- Semantic Reconciliation Agent;
- Graph Critic Agent;
- processing state and review queue.

### Stage 5 — nine view generators

Generate all views from reviewed graph queries.

### Stage 6 — module-level intelligence

Reconcile unit graphs into module graph and add course-design audit rules.

### Stage 7 — multi-module pilot

Pilot:

- Introduction to Cognitive Psychology;
- Biological Psychology;
- Health Psychology.

### Stage 8 — productisation study

Evaluate:

- lecturer usefulness;
- graph accuracy;
- review burden;
- time saved;
- pedagogical quality;
- privacy/copyright deployment models;
- institutional value.

---

## 13. Immediate pilot datasets

### Biological Psychology

Use the Chapter 1 extract as the first single-document test because it contains:

- explicit learning outcomes;
- proximate and ultimate explanations;
- methodological categories;
- imaging/electrophysiological trade-offs;
- critical-thinking activities;
- assessment questions.

This tests both source extraction and pedagogical structure extraction.

### Introduction to Cognitive Psychology — Unit 3

Use the four specified core readings as the first multi-reading reconciliation/debate test.

Important explicit relationship:

```text
Chatterjee (2005)
    → COMMENTS_ON
Fellows et al. (2005)
```

This unit is suitable for testing:

- methodological concepts;
- competing/critical perspectives;
- evidence relationships;
- reading-to-reading commentary;
- debate-map generation.

---

## 14. Success criteria for the first end-to-end pilot

A successful first pilot should demonstrate that the system can:

1. preserve accurate page/section provenance;
2. extract useful concepts without uncontrolled proliferation;
3. distinguish theories, constructs, methods, measures, claims and findings;
4. identify semantically overlapping concepts without over-merging them;
5. preserve disagreements between readings;
6. generate an evidence graph without turning association into causation;
7. generate the nine views from one canonical graph;
8. identify which edges are E1, E2 or E3;
9. surface uncertainty rather than fabricate missing relationships;
10. regenerate all views reproducibly after graph review.

---

## 15. Architectural principle

The long-term system should remain:

```text
Agno
= orchestration and agent teamwork

Qwen embeddings
= semantic neighbourhood and retrieval

Flint / other LLM
= constrained reasoning and extraction

Python / NetworkX
= deterministic graph operations

Postgres / pgvector
= durable semantic and relational storage

Canonical graph
= reviewed knowledge authority

Human academic
= final epistemic authority
```

That division should remain stable even if individual models or agent frameworks are later replaced.
