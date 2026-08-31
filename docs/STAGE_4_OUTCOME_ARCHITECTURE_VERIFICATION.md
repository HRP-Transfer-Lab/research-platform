# Evidence Registry v1.1 — Stage 4 Outcome Architecture Verification

**Stage:** 4 — Orthogonal outcome distance, time, transfer, role and Bridge evidence  
**Status:** VERIFIED  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`  
**Implementation commit:** `9d26b50828a78a323e2bae8fbdf6cfe157e6d95a`  
**Migration:** `20260831133500_evidence_registry_v1_1_outcome_architecture.sql`

## Decision

Stage 4 is verified.

The Registry no longer treats the historical `evidence_rung` value as a single scientific ladder. The v1.1 outcome model now separates:

```text
OUTCOME DISTANCE
trained_task | changed_format | separate_measure | real_life_function

TIME
immediate | post_intervention | delayed

TRANSFER
horizontal | vertical | niche

OUTCOME ROLE
benefit | harm | target_engagement | process | adherence | implementation

BRIDGE EVIDENCE
prompted_use | cue_triggered_use | changed_context_use |
unprompted_use | delayed_portability
```

The historical `evidence_rung`, raw `timepoint`, `transfer_axes` and `bridge_evidence_level` fields remain intact as compatibility/audit surfaces for the immutable `2026-08-23` seed release.

## Scientific corrections verified

Stage 4 establishes the following invariants:

```text
delayed != transfer
separate_measure != vertical transfer
applied != automatic niche transfer
not measured != null effect
not reported != evidence of no harm
mechanism/measurement evidence != intervention benefit outcome
```

Outcome distance, time, transfer and outcome role can now be queried and reviewed independently.

A result can therefore legitimately be represented as, for example:

```text
separate_measure + delayed + vertical
```

without collapsing measurement distance, follow-up interval and portability into one label.

## Implemented

- `outcome_distance_definition`
- `outcome_time_definition`
- `transfer_axis_definition`
- `outcome_role_definition`
- `bridge_evidence_definition`
- `legacy_outcome_semantic_map`
- `outcome_stage4_classification`
- `outcome_time_link`
- `outcome_transfer_axis`
- `outcome_role_link`
- `outcome_bridge_evidence`
- deterministic Stage 4 status-row trigger for importer replay
- Stage 4 stable seed identity audit
- Stage 4 candidate seed mapping manifest
- replayable Stage 4 mapping applicator
- Stage 4 mapping-manifest validator
- Stage 4 database architecture validator
- permanent Stage 4 integration in `bootstrap_local_registry.py`
- Workbench Stage 4 outcome review surface
- legacy `Evidence rung` and raw `timepoint` demoted to read-only historical compatibility metadata in the ordinary outcome card
- independent mapping/review authority per Stage 4 dimension
- RLS, Workbench editor/owner policies and audit coverage

## Stable seed identity

The Stage 4 backfill does not depend on regenerated `outcome_id` values.

The 38 seed outcomes are identified by the stable key:

```text
source_id
+ outcome_name
+ legacy_rung
+ raw_timepoint
```

Verified:

```text
historical outcomes     38
stable keys             38
duplicate stable keys    0
```

This makes Stage 4 replay-safe after the historical importer deletes and recreates study/outcome rows.

## Legacy audit findings

The 38 historical outcomes used ten distinct legacy rung values:

```text
separate_measure                 16
applied                           7
delayed                           3
mechanism                         3
changed_format                    2
measurement                       2
observational_longitudinal        2
practice_effect                   1
practice_or_nearest_transfer      1
practice_or_separate_measure      1
```

The audit confirmed that the legacy rung column mixed multiple scientific dimensions. In particular:

- `delayed` is a time semantic;
- `mechanism`, `measurement` and `observational_longitudinal` are not outcome-distance values;
- `practice_or_nearest_transfer` and `practice_or_separate_measure` are deliberately retained as ambiguous candidate cases rather than coerced;
- `applied` can inform real-life-function classification but does not automatically establish transfer or Bridge independence.

Five historical rows combine post-intervention and delayed follow-up observations in one raw timepoint, confirming that Stage 4 time classification must support multiple linked time classes for a single normalized historical outcome row.

## Candidate backfill verification

The Stage 4 candidate mapping layer passed with:

```text
seed outcomes                 38
Stage 4 classifications       38
time links                    38
transfer links                 2
outcome-role links            30
Bridge evidence links          0
legacy rung values covered    10 / 10
unknown legacy rung values     0
```

The low transfer-link count and zero Bridge links are intentional. The seed review does not justify manufacturing transfer or independent deployment claims from measurement distance alone.

The following gates passed:

```text
legacy_semantic_coverage:       PASS
orthogonal_dimension_integrity: PASS
human_approval_boundary:        PASS
```

No `agent_candidate` row was promoted to approved scientific status.

## Human approval boundary

Stage 4 candidate mappings remain:

```text
mapping_source = agent_candidate
review_status  = proposed
```

Workbench reviewers can approve, reject or correct Stage 4 dimensions. Human acceptance converts the relevant dimension/link to human-reviewed authority rather than allowing an automated candidate to self-promote.

Crucially, review authority is dimension-specific: time can be accepted while distance or transfer remains unresolved.

## Workbench verification

The Evidence Workbench now exposes Stage 4 outcome review separately from the historical outcome fields.

Reviewers can inspect/govern:

```text
Outcome distance
Time class(es) + raw historical timepoint
Transfer axis/axes
Outcome role/roles
Bridge evidence
Mapping source / review status
Result direction / summary
```

The historical `Evidence rung` and raw `timepoint` are no longer editable as if they were canonical v1.1 scientific fields.

The Workbench production build passed after the Stage 4 review UI and compatibility-field demotion were added.

## Deterministic replay / regression evidence

Stage 4 is integrated into the permanent local bootstrap after Stage 3 reconstruction.

Clean replay continues to preserve the historical Registry/Gateway baseline:

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

Stage 1 route/evidence-role semantics, Stage 2 source identity/versioning, Stage 3 target/mechanism/application ontology, the historical Registry validator and the `csi-evidence-v1` Gateway contract remain intact.

## Supabase advisor gate

The local Supabase database advisor completed with no `WARN`, `ERROR` or security findings.

Findings were `INFO / PERFORMANCE` only, consisting mainly of unused-index notices on the freshly rebuilt 18-source seed database and a small number of unindexed foreign-key observations. These are tracked as performance optimisation considerations rather than Stage 4 correctness failures.

## Compatibility decision

- `2026-08-23` remains immutable.
- Existing historical outcome fields remain recoverable.
- `evidence_rung` is retained as compatibility metadata, not v1.1 scientific authority.
- `csi-evidence-v1` remains unchanged.
- No production Supabase mutation was required for Stage 4 verification.
- AI/agent mappings remain candidate-only until human review.

## Next stage

Proceed to **Stage 5 — study arms, component membership and contrasts**.
