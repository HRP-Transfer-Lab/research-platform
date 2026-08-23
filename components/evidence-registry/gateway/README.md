# CSI Evidence Gateway

The **CSI Evidence Gateway** is the publication boundary between the HRP Transfer Evidence Registry and downstream Cognitive Systems Intelligence (CSI) applications.

It exists so Personal CSI, Work CSI, Cognitive Support / Health CSI and future CSI verticals can use approved scientific evidence without receiving reviewer tables, raw extraction JSON, audit data or user/person data.

## Core rule

> **CSI applications may read approved evidence from the Registry, but they never write user/person data back into the scientific Evidence Registry.**

User/session/outcome data belong in each CSI vertical's own governed data store. If CSI outcomes later become research evidence, they must enter the Registry through an explicit research-ingestion and human-review workflow.

## Architecture

```text
Evidence Workbench / Registry
reviewer and scientific working data
        |
        | human-approved release
        v
CSI Evidence Gateway
read-only + versioned + claims-safe
        |
        +--> Personal CSI
        +--> Work CSI
        +--> Health CSI
        +--> future CSI verticals
```

## Live Supabase project

```text
Project: HRP-Transfer-Evidence
Project ref: dkntitdzgeemvyukfmhs
```

## Contract v1

Canonical contract file:

```text
components/evidence-registry/gateway/contract.v1.json
```

Database contract version:

```text
csi-evidence-v1
```

Stable read views:

```text
v_csi_gateway_contract_v1
v_csi_gateway_release_v1
v_csi_gateway_evidence_v1
v_csi_gateway_claim_v1
```

The underlying publication tables are:

```text
csi_gateway_contract
csi_gateway_release
csi_gateway_evidence_card
csi_gateway_claim
```

They are deliberately separate from the Workbench/Registry source tables.

## Current release

```text
evidence_release_id: 2026-08-23
taxonomy_version: iqm-route-v0.2
evidence cards: 18
approved body-level claims: 0
```

The current Gateway is therefore **study-level evidence only**. Every evidence card carries a `claim_level` and `required_caveats` field. Mechanism/measurement records explicitly state that they are not intervention-efficacy evidence.

When reviewed syntheses and approved claims are added in the Evidence Workbench, `v_csi_gateway_claim_v1` can publish them without changing the basic v1 query shape.

## Safe evidence-card fields

The public evidence surface contains reviewed fields such as:

```text
bibliographic metadata
study design / setting
population summary + population tags
route classifications
reviewed topic tags
functional domains where coded
evidence rungs / transfer axes
product relevance
safe intervention-component summaries
safe outcome summaries
route rationale
claim level
required caveats
release + contract versions
```

It does **not** expose:

```text
raw_record
reviewer notes
Workbench roles
Workbench audit log
private extraction state
person/user/session data
service-role credentials
```

## Query semantics

CSI consumers should always pin a release for a session or result.

Example conceptual query:

```text
release = 2026-08-23
route_classes overlaps [redesign]
product_ids overlaps [h_agi]
population_tags overlaps [adults]
```

The client should store at least:

```text
contract_version
evidence_release_id
taxonomy_version
returned card_ids
```

in the CSI result provenance so an older result remains reproducible after a later evidence release is published.

Supported filters are defined in `contract.v1.json` and in `v_csi_gateway_contract_v1`.

## Deterministic-first rule

The Gateway returns evidence. It does **not** make the CSI recommendation.

Canonical sequence:

```text
CSI goal/context
-> domain mapping rules
-> competing hypotheses
-> candidate routes
-> Evidence Gateway query
-> approved evidence bundle
-> deterministic domain recommendation rules
-> recommendation + alternatives + provenance
```

This keeps domain inference separate from scientific evidence publication.

## Security model

The publication tables have RLS enabled. `anon` and `authenticated` receive **SELECT only** on published rows. No browser role receives insert/update/delete privileges.

The stable views use `security_invoker = true`.

The raw Workbench/Registry tables retain their separate reviewer-role RLS model.

## Publication lifecycle

For each future evidence release:

```text
DISCOVER / EXTRACT / REVIEW
-> approve Registry evidence release
-> prepare CSI-safe publication cards
-> verify claim boundaries
-> publish Gateway release
-> mark one release current for new CSI sessions
-> preserve older release for reproducibility
```

Do not make a CSI session silently follow whatever happens to be newest midway through the session. Pin the evidence release when the CSI session/result is created.

## Hosted migrations

The v1 Gateway is created by:

```text
supabase/migrations/20260823201955_add_csi_evidence_gateway_v1.sql
supabase/migrations/20260823202036_add_csi_gateway_fk_indexes.sql
```

These migration versions match the hosted `HRP-Transfer-Evidence` project migration history.
