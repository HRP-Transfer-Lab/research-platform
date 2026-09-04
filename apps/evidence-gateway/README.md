# HRP Evidence Gateway

Public, read-only working demo of the HRP evidence corpus.

> **Public name:** HRP Evidence Gateway  
> **Descriptor:** Curated evidence for adaptive cognition, cognitive interventions and human–AI systems.

## Current demo corpus

The `hrp-evidence-gateway-demo-2026-09-04` snapshot contains **258 records**:

- 18 human-approved seed records;
- 238 assistant-researched or assistant-adjudicated provisional screening records;
- 2 explicit boundary/excluded records.

The provisional corpus is currently distributed across the principal CSI demo domains approximately as follows:

- 89 health / clinical-adjacent records;
- 75 performance / work records;
- 74 personal records;
- 18 approved legacy seed records not yet backfilled with Stage 13 CSI-domain labels;
- 2 explicit not-applicable boundary records.

The public UI keeps these evidence states visibly distinct. The demo corpus is **not** an approved evidence release or a systematic review.

## Demo pathways

The standalone Gateway now includes three one-click evidence-backed product demonstrations:

```text
Personal CSI
Work CSI
Health CSI
```

Each pathway:

1. applies a real Gateway evidence filter;
2. produces a bounded demo recommendation;
3. shows the exact evidence records used;
4. displays Approved versus Provisional status beside each source;
5. exposes a machine-readable CSI demo query;
6. supports deep links back into the filtered Gateway.

The scenario definitions are versioned in:

```text
apps/evidence-gateway/demo-recommendations.v1.json
components/evidence-registry/gateway/demo-recommendations.v1.json
```

They are product-development demonstrations, not approved scientific, organisational or clinical guidelines.

## CSI Explorer integration

A reusable browser-safe demo client is available at:

```text
components/evidence-registry/gateway/csi-demo-client.v1.js
```

and its query contract at:

```text
components/evidence-registry/gateway/csi-demo-query-contract.v1.json
```

See:

```text
docs/CSI_EVIDENCE_DEMO_INTEGRATION.md
```

for sample queries, deep links and the recommended CSI result provenance shape.

The intended integration boundary is:

```text
CSI Explorer demo
        ↓
csi-demo-client.v1.js
        ↓
public.hrp_evidence_gateway_demo
        ↓
Approved + Provisional evidence with status labels

Production / claims-safe CSI
        ↓
csi-evidence-v1
        ↓
public.v_csi_gateway_evidence_v1
        ↓
Approved release only
```

## Data boundary

The browser reads only:

```text
public.hrp_evidence_gateway_demo
```

This is a public-safe snapshot containing bibliographic and screening/display fields only. It does not expose:

- raw Registry extraction JSON;
- Workbench membership;
- reviewer identity;
- audit history;
- unrestricted scientific tables;
- service-role or secret credentials.

The browser uses the Supabase publishable key, which is intentionally safe for public client code and remains constrained by Postgres grants and RLS.

## Demo versus production consumers

```text
DEMO MODE
HRP Evidence Gateway / CSI Explorer demos
        ↓
hrp_evidence_gateway_demo
        ↓
258 records, status-labelled

PRODUCTION / CLAIMS-SAFE MODE
CSI Explorers
        ↓
v_csi_gateway_evidence_v1
        ↓
18 human-approved records in the current approved release
```

The machine-readable contract is:

```text
components/evidence-registry/gateway/demo-contract.v1.json
```

## Shareable deep links

The Gateway understands these query parameters:

```text
scenario
q
domain
status
role
priority
sort
```

Examples after deployment:

```text
?scenario=personal
?scenario=work
?scenario=health
?domain=performance_work&q=AI&priority=high
```

This lets CSI prototypes expose a **View evidence** link that opens the same human-readable evidence request.

## Local preview

From this directory:

```bash
npm install
npm run build
python3 -m http.server 4173 --directory dist
```

Then open:

```text
http://localhost:4173
```

## Cloudflare deployment

The demo has its own Worker identity and does not replace the authenticated Evidence Workbench.

```bash
npm install
npm run deploy
```

Worker name:

```text
hrp-evidence-gateway-demo
```

No environment secrets are required.

## Governance

This application is designed for evidence discovery, product demonstrations and CSI prototype integration. Provisional records should not be transformed into approved scientific or clinical claims merely because they are accessible through the demo UI.
