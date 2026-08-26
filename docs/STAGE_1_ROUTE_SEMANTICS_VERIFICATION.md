# Evidence Registry v1.1 — Stage 1 Verification

**Stage:** 1 — Freeze intervention-route semantics  
**Status:** VERIFIED  
**Date:** 26 August 2026  
**Branch:** `evidence-registry-v1.1`  
**Implementation commit:** `bf639c32249b7707bd8b2f8c485f715acafe6c37`  
**Migration:** `20260826212614_evidence_registry_v1_1_route_semantics.sql`

## Decision

Stage 1 is verified.

The Registry now structurally separates:

```text
INTERVENTION ROUTE
what locus is being changed

EVIDENCE ROLE
what kind of evidential contribution is being made

REVIEW STREAM
how the source entered the review workflow

CONTROLLER / OVERLAY
cross-cutting monitoring, scaffolding or adaptive control
```

Only the seven canonical intervention routes are permitted in normalized intervention-component route fields:

```text
develop_equip
develop_train
develop_condition
regulate
bridge
redesign
integrate
```

Historical non-route classifications remain recoverable through the legacy semantic resolver and are not rewritten in the immutable `2026-08-23` release.

## Implemented

- `evidence_role_definition`
- `controller_overlay_definition`
- `legacy_classification_semantic_map`
- `source_evidence_role`
- `source_controller_overlay`
- seven-route database constraint on `intervention_component.route`
- deterministic semantic resolver/trigger for clean replay and later imports
- Workbench RLS/grants/audit integration
- `taxonomy.v1.1.json`
- `validate_stage1_semantics.py`
- Workbench route options restricted to seven routes
- separate Workbench review-stream, evidence-role and intervention-route filtering
- source semantics review/edit surface
- local Workbench build artefact ignore rules

## Verified semantic distribution for the 18-source seed

Primary evidence roles:

```text
direct_intervention  10
measurement           1
mechanism             5
observational         1
synthesis             1
```

All evidence-role links:

```text
direct_intervention  11
measurement           1
mechanism             5
observational         1
synthesis             2
```

Controller / overlay links:

```text
metacognitive_governor  2
```

Normalized intervention components:

```text
develop_condition  1
develop_train      5
integrate          3
redesign           4
```

## Integrity checks

All returned zero failures:

```text
sources_without_role                       0
sources_without_exactly_one_primary_role   0
illegal_intervention_routes                0
nonroute_legacy_labels_in_component_route  0
```

## Validation evidence

```text
STAGE 1 SEMANTICS VALID: 18 historical records resolve into v1.1 semantics
REGISTRY VALID: 18 records; release=2026-08-23; taxonomy=iqm-route-v0.2
CSI EVIDENCE GATEWAY CONTRACT PASS
```

Evidence Workbench production build also passed:

```text
tsc --noEmit -p tsconfig.app.json
tsc --noEmit -p tsconfig.node.json
vite build
```

The deterministic local bootstrap continued to preserve the baseline contract during Stage 1 development:

```text
Registry sources              18
Registry studies              18
Intervention components       13
Evidence outcomes             38
Source EML assessments        18
CSI Gateway releases           1
CSI Gateway evidence cards    18
CSI Gateway claims             0
Gateway cards with EML        18
```

## Compatibility decision

- Historical release `2026-08-23` remains immutable.
- Historical taxonomy `iqm-route-v0.2` remains valid for that release.
- `csi-evidence-v1` remains backward compatible.
- No production Supabase mutation was required for local Stage 1 verification.

## Next stage

Proceed to **Stage 2 — Separate canonical source identity from reviewed source versions and release membership**.
