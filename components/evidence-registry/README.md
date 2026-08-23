# HRP Transfer Evidence Registry

A versioned, provenance-aware evidence layer for **CSI / Explorer → IQ Coach → H-AGI**.

This component converts reviewed intervention literature into structured records that keep separate:

1. **intervention route** — what the intervention is designed to change;
2. **target** — operation, strategy, meta-function, state, policy, or niche condition;
3. **protocol** — what was actually delivered, to whom, how often and for how long;
4. **outcome / proof** — what was measured and at what timepoint;
5. **transfer** — where portability was tested;
6. **product relevance** — how the evidence informs G Track, CCC, Reasoning Coach, H-AGI, Explorer or CSI;
7. **quality / certainty** — study-level bias and later body-of-evidence certainty.

## Hosted backend status

The operational PostgreSQL backend is provisioned in the dedicated Supabase project **HRP-Transfer-Evidence**.

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

Raw reviewer/scientific tables have RLS enabled and are protected by the Workbench `viewer` / `editor` / `owner` role model. Browser-facing CSI applications do **not** read those tables directly.

The deployed database migration history is mirrored in `supabase/migrations/`. No credentials, database password, service-role key or other project secret belongs in Git.

## Evidence Workbench

The live Evidence Workbench is the reviewer/maintenance surface for the operational Registry. It supports study inspection/editing, route/outcome/product relevance, quality appraisal, release controls, reviewer access and mutation auditing.

Workbench edits affect the operational scientific database; versioned Git releases remain explicit release/audit snapshots rather than being silently rewritten.

## CSI Evidence Gateway

The CSI Evidence Gateway is the public/read-only publication boundary for Personal CSI, Work CSI, Cognitive Support / Health CSI and future CSI verticals.

Core rule:

> **CSI applications may read approved evidence from the Registry, but they never write user/person data back into the scientific Evidence Registry.**

Current contract:

```text
contract_version: csi-evidence-v1
evidence_release_id: 2026-08-23
taxonomy_version: iqm-route-v0.2
evidence cards: 18
approved body-level claims: 0
```

Stable read views:

```text
v_csi_gateway_contract_v1
v_csi_gateway_release_v1
v_csi_gateway_evidence_v1
v_csi_gateway_claim_v1
```

The Gateway is release-pinned, read-only and claims-safe. It exposes no raw extraction JSON, Workbench membership, audit records or person/session data. The initial release is explicitly `study_level_only` until human-reviewed syntheses and approved claims exist.

See:

```text
components/evidence-registry/gateway/README.md
components/evidence-registry/gateway/contract.v1.json
docs/CSI_EVIDENCE_GATEWAY.md
```

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
  gateway/
    README.md
    contract.v1.json
  data/releases/2026-08-23/
    manifest.json
    records/
  scripts/
    validate_registry.py
    validate_csi_gateway.py
    query_registry.py

supabase/
  README.md
  migrations/
    20260823174214_create_evidence_registry_core.sql
    20260823174605_add_evidence_registry_importer.sql
    20260823174724_fix_evidence_registry_importer_targets.sql
    20260823175100_add_evidence_registry_fk_indexes.sql
    20260823181717_add_evidence_workbench_access.sql
    20260823181810_add_evidence_workbench_audit_log.sql
    20260823182520_add_evidence_workbench_fk_indexes.sql
    20260823201955_add_csi_evidence_gateway_v1.sql
    20260823202036_add_csi_gateway_fk_indexes.sql
```

Each reviewed source has its own JSON file so scientific corrections and re-classifications receive an independent Git diff/history.

## Validate

```bash
python components/evidence-registry/scripts/validate_registry.py \
  components/evidence-registry/data/releases/2026-08-23/records \
  --taxonomy components/evidence-registry/schema/taxonomy.v1.json \
  --manifest components/evidence-registry/data/releases/2026-08-23/manifest.json

python components/evidence-registry/scripts/validate_csi_gateway.py
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
→ CSI-SAFE PUBLICATION
```

Production CSI/IQ Coach/H-AGI systems should query **approved Gateway release/read views**, not raw newly discovered papers or reviewer tables.

## Operational authority model

```text
Evidence Workbench
→ operational Postgres records
→ human review / approval
→ versioned evidence release
→ Git release snapshot
→ CSI Evidence Gateway publication
→ Personal / Work / Health CSI
```

Git remains the immutable audit/release record. Postgres is the working scientific database. The Gateway is the downstream publication boundary.

## Next implementation layer

Build **`csi-core`**: shared TypeScript evidence/query/result types and a deterministic `EvidenceClient` that consumes `csi-evidence-v1`, pins an evidence release per CSI result and keeps evidence retrieval separate from domain-specific recommendation rules.
