# Research Intel Agents Component

This component now contains the shared **HRP Research Scout** used to discover
candidate literature for IQ Mindware, SWI/CSI and other HRP products.

## Boundary

The scout is a **discovery layer**, not an evidence authority.

```text
PubMed / Crossref / later OpenAlex, arXiv, bioRxiv, Semantic Scholar
        ↓
shared metadata candidates
        ↓
SCREEN IN EVIDENCE WORKBENCH
        ↓
human verify / classify / appraise
        ↓
approved Evidence Registry release
        ↓
CSI Evidence Gateway / downstream product adapters
```

The scout never writes directly to the Evidence Registry or Gateway. Metadata
matches do not establish efficacy, transfer, causality or product validity.

## Current MVP

Implemented adapters:

- PubMed E-utilities
- Crossref REST API

Reserved adapters:

- Semantic Scholar
- arXiv
- bioRxiv
- OpenAlex

The current scan is deliberately title-anchor filtered to reduce generic
keyword noise. Output is a local review queue at:

```text
.local/research-intel-agents/review-queue-latest.json
```

Each candidate is tagged with:

- source and identifiers
- title / publication metadata
- topic family
- intended downstream consumers
- matched relevance anchors
- `DISCOVERED_UNSCREENED`
- `NO_PUBLIC_CLAIM`
- `SCREEN_IN_EVIDENCE_WORKBENCH`

## Run

```bash
python3 components/research-intel-agents/research_scout.py status
python3 components/research-intel-agents/research_scout.py scan
```

Optional contact variables:

```text
HRP_RESEARCH_CONTACT_EMAIL
PUBMED_EMAIL
```

These identify the client to scholarly APIs and do not contain scientific or
participant data.

## Tests

```bash
python3 -m unittest components/research-intel-agents/test_research_scout.py
```

## Agent policy

- all discoveries remain proposed inputs until reviewed
- apply the Evidence Workbench review gate before canonical scientific writes
- keep discovery signals distinct from approved evidence and speculative hypotheses
- no citation, no claim
