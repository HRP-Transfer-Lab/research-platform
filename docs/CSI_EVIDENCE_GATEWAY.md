# CSI Evidence Gateway Architecture

**Status:** v1 live backend architecture  
**Date:** 23 August 2026  
**System:** HRP Transfer Evidence Registry -> Cognitive Systems Intelligence applications

## Purpose

The CSI Evidence Gateway is the controlled read boundary through which downstream Cognitive Systems Intelligence applications use the HRP Transfer Evidence Registry.

It serves Personal CSI, Work CSI, Cognitive Support / Health CSI and future CSI verticals while preserving a strict separation among:

```text
scientific evidence
CSI domain inference
user/person data
```

The governing rule is:

> **CSI applications may read approved evidence from the Registry, but they never write user/person data back into the scientific Evidence Registry.**

## Why a Gateway rather than direct Registry access

The Evidence Registry contains scientific working data, reviewer permissions, audit history and raw extraction structures that downstream consumer/organisational/health applications do not need and should not receive.

The Gateway therefore publishes a separate, versioned projection containing only fields that have been selected for CSI use.

```text
WORKBENCH / REGISTRY
raw + normalized scientific working data
        |
        | approval + release publication
        v
CSI EVIDENCE GATEWAY
safe read projection
        |
        +--> Personal CSI rules
        +--> Work CSI rules
        +--> Health CSI pathway rules
```

The Gateway does not make a recommendation. It provides evidence to a deterministic domain-specific inference engine.

## Versioning model

Three versions are kept distinct:

```text
contract_version
CSI API/query shape

 evidence_release_id
which scientific release was available

 taxonomy_version
how intervention routes/evidence were classified
```

Current values:

```text
contract_version: csi-evidence-v1
evidence_release_id: 2026-08-23
taxonomy_version: iqm-route-v0.2
```

A CSI session/result should pin these values when the result is created. Later Registry updates do not silently change the evidence provenance of an older result.

## Stable v1 read surfaces

```text
v_csi_gateway_contract_v1
v_csi_gateway_release_v1
v_csi_gateway_evidence_v1
v_csi_gateway_claim_v1
```

The first three contain the live v1 publication; `v_csi_gateway_claim_v1` is intentionally empty until body-level syntheses/claims are human-approved.

## Evidence-card query dimensions

v1 supports deterministic filtering by:

```text
evidence_release_id
evidence_class
primary_classification
route_classes
population_tags
topic_tags
functional_domains
product_ids
evidence_rungs
peer_review_status
```

Example CSI evidence request:

```text
release = 2026-08-23
route_classes overlaps [redesign]
product_ids overlaps [h_agi]
population_tags overlaps [adults]
```

The returned cards are evidence inputs. Work CSI, Personal CSI and Health CSI may legitimately reach different recommendations from the same cards because their domain rules, permissions and user context differ.

## Claim boundary

At initial publication the Registry contains:

```text
approved sources: 18
approved syntheses: 0
approved claims: 0
quality assessments: 0
```

The v1 Gateway therefore exposes `claim_level = study_level_only` on the seed cards and supplies mandatory caveats.

Examples:

```text
Direct intervention evidence
A single study does not establish that an intervention will improve an individual CSI user or transfer to the user's valued goal.

Mechanism / measurement evidence
Do not present this as intervention-efficacy evidence.

Human-AI activity-system evidence
Interpret within the studied population and design; causal strength varies by design.
```

When the Workbench contains reviewed syntheses and approved claims, the publication process can add claim rows and link evidence cards to `approved_claim_ids` without breaking contract v1.

## Security model

The publication tables are separate from reviewer tables and contain no user/person/session data.

Security properties:

```text
RLS enabled on every Gateway table
anon + authenticated: SELECT only
no browser INSERT / UPDATE / DELETE
security_invoker views
no raw_record exposure
no Workbench membership exposure
no Workbench audit exposure
no service-role credential in clients
```

The raw Registry remains protected by the Workbench viewer/editor/owner model.

## Deterministic CSI interaction

Recommended downstream flow:

```text
1. CSI captures a valued goal / functional target.
2. Domain rules create competing constraint hypotheses.
3. Rules generate a bounded EvidenceQuery.
4. EvidenceClient pins a Gateway release and retrieves matching cards/claims.
5. Domain rules rank routes using user/context evidence + Gateway evidence.
6. CSI shows recommendation, alternatives, rationale, caveats and provenance.
7. CSI stores the Gateway versions/card IDs used in the result.
```

The Evidence Gateway must never become a hidden inference engine that turns a paper match directly into a person-level conclusion.

## Data-direction boundary

Allowed:

```text
Registry -> Gateway -> CSI application
```

Not allowed:

```text
CSI user/session/profile -> Evidence Registry
```

If CSI outcomes later form part of a research dataset, they must enter via a separately governed research pipeline with appropriate consent, protocol, extraction and human review.

## Future publication workflow

A later Evidence Workbench release control should perform:

```text
approve evidence release
-> validate eligible sources
-> create safe publication projection
-> verify caveats / approved claims
-> publish new Gateway release
-> mark new release current for new CSI sessions
-> retain earlier releases for reproducibility
```

This should remain an explicit owner/reviewer action rather than an automatic consequence of editing a study row.

## Implementation

Hosted database:

```text
Supabase project: HRP-Transfer-Evidence
project ref: dkntitdzgeemvyukfmhs
```

Tracked migrations:

```text
20260823201955_add_csi_evidence_gateway_v1.sql
20260823202036_add_csi_gateway_fk_indexes.sql
```

Canonical machine-readable query contract:

```text
components/evidence-registry/gateway/contract.v1.json
```

The next implementation layer is `csi-core`: shared TypeScript EvidenceQuery / EvidenceBundle / CSIResult types and a deterministic EvidenceClient that consumes these v1 views.
