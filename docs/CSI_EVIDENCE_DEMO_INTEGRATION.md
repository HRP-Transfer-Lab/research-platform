# CSI Evidence Demo Integration

This document defines the first reusable integration boundary between the **HRP Evidence Gateway** demo corpus and Personal / Work / Health CSI Explorer prototypes.

## Two evidence modes

```text
DEMO MODE
CSI Explorer prototype
    ↓
csi-demo-client.v1.js
    ↓
public.hrp_evidence_gateway_demo
    ↓
Approved + Provisional evidence with visible status labels

PRODUCTION / CLAIMS-SAFE MODE
CSI Explorer
    ↓
CSI Evidence Gateway v1
    ↓
public.v_csi_gateway_evidence_v1
    ↓
Approved release only
```

Demo mode exists to make working product demonstrations possible before the expanded corpus has completed human appraisal. It must never silently convert provisional screening records into approved claims.

## Files

```text
components/evidence-registry/gateway/
  csi-demo-client.v1.js
  csi-demo-query-contract.v1.json
  demo-recommendations.v1.json
  demo-contract.v1.json
  contract.v1.json
```

## Basic client use

Bundle or copy `csi-demo-client.v1.js` into a CSI Explorer frontend and call:

```js
import {
  queryCsiDemoEvidence,
  buildGatewayDeepLink,
} from './csi-demo-client.v1.js'

const result = await queryCsiDemoEvidence({
  domain: 'performance_work',
  q: 'AI reasoning',
  priorities: ['high'],
  limit: 8,
})

console.log(result.evidence)
console.log(result.governance)
```

The response always carries the demo governance boundary:

```json
{
  "claims_safe": false,
  "provisional_evidence_may_be_present": true,
  "production_claims_require_approved_gateway": true,
  "production_relation": "public.v_csi_gateway_evidence_v1"
}
```

## Explicit source bundles

A CSI recommendation can pin the evidence sources that informed it:

```js
const evidence = await queryCsiDemoEvidence({
  domain: 'performance_work',
  source_ids: [
    'rt-2026-014',
    'rt-2026-015',
    'rt-2026-016',
    'rt-2026-018'
  ],
  limit: 4,
})
```

When `source_ids` are supplied, the client preserves caller order. This makes CSI outputs reproducible and lets a result store the exact evidence bundle used at generation time.

## Deep links back to the Gateway

CSI prototypes can expose a **View evidence** action:

```js
const url = buildGatewayDeepLink({
  scenario: 'work',
})
```

or:

```js
const url = buildGatewayDeepLink({
  domain: 'health_clinical_adjacent',
  q: 'goal management',
  priority: 'high',
})
```

The standalone HRP Evidence Gateway understands these query parameters:

```text
scenario
q
domain
status
role
priority
sort
```

This makes the public Gateway a human-readable inspection surface for the same evidence request used by a CSI demo.

## Three versioned demo scenarios

`demo-recommendations.v1.json` currently defines:

### Personal CSI

**Situation:** self-directed learning, cognitive performance and resilience.

**Demo policy:** combine self-regulated-learning routines, targeted cognitive practice and a separate regulation component; test transfer rather than infer it.

### Work CSI

**Situation:** GenAI adoption in high-demand professional work.

**Demo policy:** keep framing, evidence judgement and final decisions human-owned; use AI as bounded support; preserve independent no-AI checks and monitor hidden workload.

### Health CSI

**Situation:** cognitive/executive support after neurological illness or acquired cognitive difficulty.

**Demo policy:** use functional goals and strategy-based rehabilitation; treat telehealth/computerisation as delivery mechanisms; measure participation and maintenance separately from trained-task gains.

These are **product demonstration recommendations**, not approved clinical or organisational guidelines.

## Recommended CSI result shape

A demo CSI result should preserve evidence provenance directly:

```json
{
  "result_id": "...",
  "domain": "performance_work",
  "recommendation": {
    "title": "...",
    "actions": ["..."]
  },
  "evidence_mode": "demo",
  "evidence_contract_version": "csi-evidence-demo-query-v1",
  "evidence_snapshot": "hrp-evidence-gateway-demo-2026-09-04",
  "evidence_source_ids": ["rt-2026-014", "rt-2026-015"],
  "contains_provisional_evidence": true,
  "human_review_required_for_claim": true
}
```

The important design rule is that CSI recommendation logic and evidence retrieval remain separate. Evidence cards inform a recommendation; they do not automatically determine one.

## Next integration step

When each CSI Explorer frontend is brought into the implementation repository, add an `EvidenceClient` adapter with two modes:

```text
demo       → csi-demo-client.v1.js / hrp_evidence_gateway_demo
production → csi-evidence-v1 / approved Gateway view
```

The domain-specific Explorer retains its own situation model and recommendation rules while recording the evidence release and source IDs used for every recommendation.
