# HRP Evidence Gateway

Public, read-only working demo of the HRP evidence corpus.

> **Public name:** HRP Evidence Gateway  
> **Descriptor:** Curated evidence for adaptive cognition, cognitive interventions and human–AI systems.

## Current demo corpus

The `hrp-evidence-gateway-demo-2026-09-04` snapshot contains **100 records**:

- 18 human-approved seed records;
- 80 assistant-adjudicated provisional screening records;
- 2 explicit boundary/excluded records.

The public UI keeps these evidence states visibly distinct. The 100-record demo corpus is **not** an approved evidence release or a systematic review.

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
100 records, status-labelled

PRODUCTION / CLAIMS-SAFE MODE
CSI Explorers
        ↓
v_csi_gateway_evidence_v1
        ↓
approved release only
```

The machine-readable contract is:

```text
components/evidence-registry/gateway/demo-contract.v1.json
```

## Local preview

From this directory:

```bash
python3 -m http.server 4173
```

Then open:

```text
http://localhost:4173
```

## Cloudflare deployment

The demo has its own Worker identity and does not replace the authenticated Evidence Workbench.

```bash
npx wrangler@4.129.0 deploy
```

Worker name:

```text
hrp-evidence-gateway-demo
```

No environment secrets are required.

## Governance

This application is designed for evidence discovery, product demonstrations and CSI prototype integration. Provisional records should not be transformed into approved scientific or clinical claims merely because they are accessible through the demo UI.
