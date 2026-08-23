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

## Hosted backend status

The operational PostgreSQL backend is now provisioned in the dedicated Supabase project **HRP-Transfer-Evidence**.

Current hosted release:

- region: **EU West (Ireland)**;
- release: `2026-08-23`;
- taxonomy: `iqm-route-v0.2`;
- approved sources: **18**;
- normalized study rows: **18**;
- intervention-component rows: **13**;
- outcome rows: **38**;
- product-relevance links: **35**.

The source buckets remain exactly:

- **A — direct intervention / transfer:** 7;
- **B — measurement / mechanism:** 6;
- **C — human-AI / activity system:** 5.

Raw reviewer/scientific tables have RLS enabled and no `anon` or `authenticated` grants at bootstrap. Approved read views are `security_invoker` views and are currently service-side only. Browser-facing reviewer and Explorer policies must be added deliberately as part of the Evidence Workbench/API implementation.

The deployed database migration history is mirrored in `supabase/migrations/`. No credentials, database password, service-role key or other project secret belongs in Git.

## Seed release

`data/releases/2026-08-23/` contains the 18 records reviewed in Section 19 of:

`Mindware-Lab/trident-g-ground-truth/July_2026/TRANSFER_ROUTE_FRAMEWORK.md`

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

supabase/
  README.md
  migrations/
    20260823174214_create_evidence_registry_core.sql
    20260823174605_add_evidence_registry_importer.sql
    20260823174724_fix_evidence_registry_importer_targets.sql
    20260823175100_add_evidence_registry_fk_indexes.sql
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

## Operational authority model

During bootstrap, Git contains the approved scientific seed release and the migration history; Supabase contains the operational normalized database.

The intended Workbench-era flow is:

```text
Evidence Workbench
→ operational Postgres records
→ human review / approval
→ versioned evidence release
→ Git release snapshot
→ approved read model
→ Explorer / IQ Coach / H-AGI / CSI
```

Git remains the immutable audit/release record. Postgres becomes the working scientific database once the Workbench is live.

## Next implementation layer

Build the **Evidence Workbench** directly on the hosted backend. The first version should add authenticated reviewer access, Evidence Library and Study Record screens, component/outcome/product-relevance editing, review/approval status, and release management. Explorer-facing read access should remain separate from reviewer write access.
