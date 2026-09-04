# HRP Evidence Gateway

Public, read-only research evidence surface for HRP Transfer Lab and IQ Mindware Cognitive Systems Intelligence.

> **Public name:** HRP Evidence Gateway  
> **Descriptor:** Curated evidence for adaptive cognition, cognitive interventions and human–AI systems.

## Current research snapshot

The `hrp-evidence-gateway-demo-2026-09-04` research snapshot contains **258 records**:

- 18 human-approved seed records;
- 238 assistant-researched or assistant-adjudicated research-watchlist records;
- 2 explicit boundary/excluded records.

Approximate current domain coverage:

- 89 health / clinical-adjacent records;
- 75 performance / work records;
- 74 personal records;
- 18 approved legacy seed records not yet backfilled with Stage 13 CSI-domain labels;
- 2 explicit not-applicable boundary records.

The public UI keeps authority and maturity visible. The expanded snapshot is **not** an approved evidence release or a systematic review.

## Role in the CSI product family

```text
HRP TRANSFER LAB GOVERNED REGISTRY
        ↓ human review / release gate
HRP EVIDENCE GATEWAY
        ├── Personal CSI
        ├── Work / Organisational CSI
        └── authorised Health pathways
```

The Gateway is Flow 1 — **Shared Evidence Intelligence**. Personal, employee, service-user and operational pathway data do not enter the scientific Registry merely because a CSI application queries the Gateway.

## Evidence lifecycle

The public product now exposes the intended evidence lifecycle:

```text
DISCOVER & SCREEN
→ RETRIEVE & STRUCTURED EXTRACTION
→ APPRAISE & SYNTHESISE
→ HUMAN APPROVE & RELEASE
```

A paper can therefore be useful for research discovery without being claims-safe.

## Two independent evidence signals

Do not collapse **record authority** and **effectiveness evidence**.

### 1. Record authority / status

- **Human approved** — belongs to an approved seed/release state.
- **Research watchlist** — screening-level research lead awaiting further verification/extraction/appraisal.
- **Boundary / excluded** — retained to make scope decisions transparent.

### 2. HRP Evidence Maturity Level (EML v1)

EML describes the maturity of evidence relevant to an intervention/effectiveness proposition:

| EML | Label | Public colour |
|---:|---|---|
| 0 | Rationale only | Grey / neutral |
| 1 | Mechanism / paradigm support | Blue |
| 2 | Initial direct demonstration | Indigo |
| 3 | Replicated direct evidence | Teal |
| 4 | Convergent body | Emerald |
| 5 | Transfer & durability | Green |
| 6 | Real-world effectiveness | Lime |
| 7 | Generalised / scale-ready | Gold |

### Screening-only rule

For the current research-watchlist corpus, screening metadata can support only a conservative **provisional source-contribution EML**:

```text
protocol                 → provisional EML 0
mechanism / measurement  → provisional EML 1
direct intervention      → provisional EML 2
evidence synthesis       → body-level EML pending appraisal
```

A systematic-review/scoping-review label does **not** automatically create EML 4. EML 3–7 require structured extraction and appraisal demonstrating replication, convergence, transfer/durability, real-world effectiveness or generalisation/scale readiness.

The core rule is:

> **A source-contribution EML is not a body-level effectiveness rating.**

## Public-safe data boundary

The browser reads only:

```text
public.hrp_evidence_gateway_demo
```

This relation contains bibliographic and screening/display fields only. It does not expose:

- raw Registry extraction JSON;
- Workbench membership;
- reviewer identity;
- audit history;
- unrestricted scientific tables;
- service-role or secret credentials.

The browser uses a Supabase publishable key constrained by the database grants/RLS model.

## Research-preview versus claims-safe consumers

```text
RESEARCH PREVIEW / EARLY-ACCESS CSI
        ↓
public.hrp_evidence_gateway_demo
        ↓
258 status-labelled records

PRODUCTION / CLAIMS-SAFE CSI
        ↓
csi-evidence-v1
        ↓
public.v_csi_gateway_evidence_v1
        ↓
human-approved release only
```

## CSI integration

Reusable research-preview assets remain in:

```text
components/evidence-registry/gateway/
  csi-demo-client.v1.js
  csi-demo-query-contract.v1.json
  demo-recommendations.v1.json
  demo-contract.v1.json
  contract.v1.json
```

See `docs/CSI_EVIDENCE_DEMO_INTEGRATION.md` for query/provenance examples.

The public Gateway understands:

```text
scenario
q
domain
status
role
priority
sort
```

This lets a CSI result expose a human-readable **View evidence** route while separately recording the exact evidence source IDs and release/snapshot used.

## Local build

```bash
npm install
npm run build
python3 -m http.server 4173 --directory dist
```

## Standalone Worker preview

```bash
npm run deploy
```

Worker identity remains `hrp-evidence-gateway-demo` as an engineering preview/fallback. The intended business-facing route is:

```text
https://www.iqmindware.com/evidence/
```

## Governance

The Gateway supports evidence discovery, research prioritisation, product development and CSI evidence retrieval. Visibility in the Gateway does not make a source an approved scientific, organisational or clinical claim. Human approval remains required for claims-safe releases and consequential use.
