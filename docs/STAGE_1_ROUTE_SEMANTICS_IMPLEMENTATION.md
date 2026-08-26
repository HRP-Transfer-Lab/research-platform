# Evidence Registry v1.1 — Stage 1 Route Semantics

**Status:** IN PROGRESS  
**Date:** 26 August 2026  
**Branch:** `evidence-registry-v1.1`  
**Governing framework:** `Mindware-Lab/trident-g-ground-truth/July_2026/TRANSFER_ROUTE_FRAMEWORK.md`

## Goal

Remove semantic category leakage before wider Registry v1.1 schema expansion.

Stage 1 establishes one hard rule:

> **An intervention route describes the locus being changed. Evidence role, review stream and controller/overlay are separate dimensions.**

The historical `2026-08-23` release remains immutable and `csi-evidence-v1` remains backward compatible.

## 1. Canonical intervention routes

Only these seven values are valid intervention routes:

```text
develop_equip
develop_train
develop_condition
regulate
bridge
redesign
integrate
```

No mechanism, measurement, observational or controller label may occupy the canonical route vocabulary.

## 2. Evidence role is a separate axis

Stage 1 introduces a controlled evidence-role vocabulary independent of route:

```text
direct_intervention
mechanism
measurement
observational
synthesis
```

A source can contribute to more than one role when scientifically justified, but one role may be marked primary for filtering/display.

The role answers:

> **What kind of evidential contribution does this source/result make?**

It does not answer what intervention route was used.

## 3. Review stream remains separate

The historical review buckets remain source-ingestion/review-stream metadata:

```text
A_direct_intervention
B_measurement_mechanism
C_human_ai_activity_system
```

They are not intervention routes and are not the final scientific evidence-role ontology.

`C_human_ai_activity_system`, in particular, may contain experimental, observational or redesign evidence and therefore must not be treated as a single scientific role.

## 4. Controller / overlay remains separate

Controller or supervisory structure is not a route.

Initial controlled values:

```text
metacognitive_governor
adaptive_controller
external_scaffold
other_controller_or_overlay
```

Absence of a controller/overlay is represented by no linked value rather than a synthetic `none` scientific entity.

A controller/overlay may be implemented through a true route. For example:

```text
metacognitive rule taught explicitly     → develop_equip
repeated application practice             → develop_train
cue-linked deployment in real activity    → bridge
external decision gate/checklist          → redesign
```

## 5. Legacy classification compatibility

Historical release JSON is not rewritten merely to make v1.1 semantics cleaner.

The following legacy `primary_classification` values are treated as non-route classifications in v1.1:

```text
measure_prove
mechanism_evidence
mechanism_and_training_design_evidence
metacognitive_governor_evidence
state_mechanism_evidence
negative_metacognitive_overlay_evidence
observational_human_ai_coupling_taxonomy
```

Compatibility resolver:

| Legacy value | Canonical route | Evidence-role guidance | Controller/overlay guidance |
| --- | --- | --- | --- |
| `measure_prove` | null | `measurement` | — |
| `mechanism_evidence` | null | `mechanism` | — |
| `mechanism_and_training_design_evidence` | null | `mechanism` | — |
| `metacognitive_governor_evidence` | null | usually `mechanism` | `metacognitive_governor` |
| `state_mechanism_evidence` | null | `mechanism` | — |
| `negative_metacognitive_overlay_evidence` | null | review source; do not infer route from label alone | `metacognitive_governor` where justified |
| `observational_human_ai_coupling_taxonomy` | null | `observational` | — |

For the seven canonical route labels, the route can be preserved. Evidence role must still be coded independently from design/review evidence rather than inferred blindly from route.

## 6. Stage 1 database design

Stage 1 should be additive and backward compatible.

### Controlled vocabulary tables

Create:

```text
evidence_role_definition
controller_overlay_definition
```

### Source evidence-role links

Create a many-to-many source link:

```text
source_evidence_role
- source_id
- evidence_role
- primary_role
- rationale
```

Reason: a paper can legitimately contain more than one evidential contribution.

### Controller/overlay links

Create a source/component-aware link that can later migrate cleanly into the Stage 2 source-version model. The Stage 1 migration should avoid embedding controller semantics into `intervention_component.route`.

### Route constraint

Add a database constraint or equivalent validated rule so new `intervention_component.route` values are restricted to the seven canonical routes.

Existing 13 normalized components already use true intervention routes, so this should not require destructive recoding of component rows.

## 7. Taxonomy files

Do not mutate the meaning of the historical `taxonomy.v1.json` in a way that makes the immutable `2026-08-23` manifest unreconstructable.

Add a new v1.1 taxonomy/resolver representation containing at minimum:

```text
canonical_routes
evidence_roles
controller_overlays
legacy_classification_map
```

The historical release continues to pin `iqm-route-v0.2`.

## 8. Validator changes

Validators must distinguish:

```text
historical release validation
vs
v1.1 canonical semantic validation
```

Required behaviour:

- the historical 18-record release still validates exactly as released;
- v1.1 code must never treat a legacy non-route classification as a canonical intervention route;
- intervention components must validate against the seven-route set;
- evidence roles/controllers validate against their own controlled vocabularies;
- missing route for mechanism/measurement/observational evidence is valid.

## 9. Workbench changes

The Workbench route selector must contain only the seven canonical intervention routes.

The current `routeOptions` list still includes non-routes and must be corrected.

Add separate display/edit surfaces for evidence role and controller/overlay only after the underlying controlled data model exists.

Do not use the current historical `raw_record.review.primary_classification` as the long-term route authority.

## 10. CSI Gateway compatibility rule

`csi-evidence-v1` must not break during Stage 1.

The current Gateway can continue exposing historical fields such as `primary_classification` for the pinned `2026-08-23` release while the Registry gains cleaner internal semantics.

Stage 1 must not silently rewrite historical Gateway cards or change the current public release.

A future Gateway contract/version can expose the orthogonal route/evidence-role model deliberately.

## 11. Regression gate

After Stage 1 changes, run:

```text
clean local migration replay
bootstrap_local_registry.py
Registry validator
CSI Gateway validator
Workbench typecheck/build
Git diff check
```

The local bootstrap must still reproduce:

```text
sources                       18
studies                       18
components                    13
outcomes                      38
source EML assessments        18
Gateway releases               1
Gateway cards                 18
Gateway claims                 0
Gateway cards with EML        18
```

## 12. Stage 1 implementation sequence

1. Generate a new Supabase migration with the CLI: `supabase migration new evidence_registry_v1_1_route_semantics`.
2. Add the controlled role/controller vocabulary and links.
3. Add/enforce seven-route validation for normalized intervention components.
4. Add the v1.1 taxonomy/resolver file.
5. Add a Stage 1 semantic validator or extend validation without breaking historical release validation.
6. Update Workbench `routeOptions` to seven routes only.
7. Backfill the 18 current sources into evidence-role/controller links conservatively.
8. Replay/reset locally and run the deterministic bootstrap.
9. Verify Gateway v1 parity.
10. Commit Stage 1 implementation and record evidence in the canonical progress tracker.

## Exit criteria

Stage 1 is `VERIFIED` only when:

- the canonical route vocabulary contains exactly seven values;
- non-route evidence categories remain representable without route masquerading;
- the 13 normalized intervention components use only true routes;
- Workbench route editing cannot introduce a non-route value;
- the historical `2026-08-23` release remains immutable and reproducible;
- the local baseline bootstrap passes exact counts;
- `csi-evidence-v1` remains backward compatible; and
- no production Supabase changes have been made during local verification.