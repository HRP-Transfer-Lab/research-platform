# HRP Transfer Evidence Registry

A versioned, provenance-aware evidence layer for **Explorer → IQ Coach → H-AGI / CSI**.

This component converts reviewed intervention literature into structured records that keep separate:

1. **intervention route** — what the intervention is designed to change;
2. **target** — operation, strategy, meta-function, state, policy, or niche condition;
3. **protocol** — what was actually delivered, to whom, how often and for how long;
4. **outcome / proof** — what was measured and at what timepoint;
5. **transfer** — where portability was tested;
6. **product relevance** — how the evidence informs G Track, CCC, Reasoning Coach, H-AGI, Explorer or CSI;
7. **quality / certainty** — study-level bias and later body-of-evidence certainty.

## Seed release

`data/releases/2026-08-23/` contains the 18 records reviewed in Section 19 of:

`Mindware-Lab/trident-g-ground-truth/July_2026/TRANSFER_ROUTE_FRAMEWORK.md`

Buckets are intentionally preserved:

- **A — direct intervention / transfer**: 7 records
- **B — measurement / mechanism**: 6 records
- **C — human-AI / activity system**: 5 records

Mechanistic and observational records are **not counted as intervention-efficacy evidence** merely because they inform a route.

## Route rule

The registry follows the IQ Mindware route framework:

- `develop_equip`
- `develop_train`
- `develop_condition`
- `regulate`
- `bridge`
- `redesign`
- `integrate`

`measure_prove`, mechanism/controller evidence and observational taxonomies are recorded distinctly rather than forced into an intervention route.

## Files

```text
components/evidence-registry/
  README.md
  schema/
    001_evidence_registry.sql
    taxonomy.v1.json
  data/releases/2026-08-23/
    manifest.json
    records/
  scripts/
    validate_registry.py
    query_registry.py
```

Each reviewed source has its own JSON file so scientific corrections and re-classifications receive an independent Git diff/history.

## Validate

```bash
python components/evidence-registry/scripts/validate_registry.py \
  components/evidence-registry/data/releases/2026-08-23/records \
  --taxonomy components/evidence-registry/schema/taxonomy.v1.json \
  --manifest components/evidence-registry/data/releases/2026-08-23/manifest.json
```

## Query examples

All Reasoning Coach-relevant records:

```bash
python components/evidence-registry/scripts/query_registry.py \
  components/evidence-registry/data/releases/2026-08-23/records/ \
  --product reasoning_coach --compact
```

Human-AI redesign evidence:

```bash
python components/evidence-registry/scripts/query_registry.py \
  components/evidence-registry/data/releases/2026-08-23/records/ \
  --route redesign --compact
```

Older-adult evidence:

```bash
python components/evidence-registry/scripts/query_registry.py \
  components/evidence-registry/data/releases/2026-08-23/records/ \
  --population older --compact
```

## Review lifecycle

```text
DISCOVER
→ SCREEN
→ PRE-EXTRACT
→ HUMAN VERIFY
→ ROUTE CLASSIFY
→ APPRAISE
→ APPROVE
→ SYNTHESISE
→ RELEASE
```

Production Explorer/IQ Coach/H-AGI systems should query **approved release/read views**, not raw newly discovered papers.

## Next implementation layer

The SQL schema is PostgreSQL-compatible and is intended to be loaded into the research-platform canonical DB. A later web workbench can add DOI/PubMed/OpenAlex import, screening, extraction forms, RoB 2/ROBINS-I appraisal, synthesis/GRADE, release management and read-only APIs for Explorer apps.
