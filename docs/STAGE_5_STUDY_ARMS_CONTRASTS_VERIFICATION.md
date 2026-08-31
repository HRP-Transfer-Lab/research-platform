# Evidence Registry v1.1 — Stage 5 Study Arms, Component Membership and Contrasts Verification

**Stage:** 5 — Study arms/conditions, component membership and contrasts  
**Status:** VERIFIED  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`  
**Implementation commit:** `0d76ee5da93a8362a761d5c4c5ae680ba815c292`  
**Migration:** `20260831141000_evidence_registry_v1_1_study_arms_contrasts.sql`

## Decision

Stage 5 is verified.

The Registry now represents experimental groups/conditions independently from reusable intervention components and from scientific contrasts:

```text
STUDY
├── STUDY ARM / CONDITION
│   └── ARM → COMPONENT MEMBERSHIP
└── STUDY CONTRAST
    └── CONTRAST → ARM MEMBERS
```

The governing invariant is:

> **Study != arm/condition != intervention component != contrast.**

This corrects the historical v1.0 flattening in which `study.comparator_summary` and study-level intervention components had to carry design information that properly belongs to separate scientific objects.

## Implemented

Stage 5 adds:

- `study_stage5_status`
- `study_arm`
- `arm_component`
- `study_contrast`
- `contrast_arm_member`
- explicit arm-extraction and contrast-extraction completeness states
- controlled arm-role vocabulary
- controlled assignment-structure vocabulary
- controlled contrast-type vocabulary
- stable candidate mapping manifest for all 18 seed studies
- replayable Stage 5 seed mapper
- Stage 5 manifest validator
- Stage 5 database architecture validator
- automatic Stage 5 reconstruction in `bootstrap_local_registry.py`
- Workbench Arms / Conditions / Component Membership / Contrasts review UI
- historical `study.comparator_summary` demoted to read-only compatibility metadata
- RLS, Workbench editor/owner policies and audit coverage

## Controlled semantics

### Arm / condition role

The Stage 5 model supports:

```text
intervention
active_control
passive_control
waitlist
treatment_as_usual
alternative_intervention
reference
observational_exposure
experimental_condition
measurement_condition
unclear
```

The neutral `experimental_condition` and `measurement_condition` roles prevent non-intervention experimental/task conditions from being misclassified as intervention arms.

### Assignment structure

```text
parallel_group
cluster_group
factorial_cell
within_subject_condition
single_group
observational_group
unclear
```

Assignment structure is deliberately separate from arm role. A quasi-experimental classroom condition is therefore not silently treated as randomized, and a factorial cell is not flattened into a simple parallel treatment arm.

### Contrast type

```text
pairwise
multiarm_pairwise
factorial_main_effect
factorial_interaction
within_subject
observational
other
```

A contrast may contain multiple arm members on either side, so the schema can represent factorial estimands without reducing them to one arm versus one arm.

## Seed-design audit

A read-only audit of all 18 historical studies was completed before schema backfill.

The audit demonstrated that the seed contains materially different design structures, including:

- randomized active-control trials;
- randomized three-group studies;
- a randomized 2×2 factorial trial;
- a large factorial AI-support × mastery-progression field experiment;
- quasi-experimental multi-condition classroom data;
- between-subject AI-support-stage conditions;
- mechanism experiments with incompletely extracted conditions;
- systematic reviews/meta-analyses that must not be turned into synthetic source-level trial arms;
- continuous observational human-AI data without discrete assigned groups.

This confirmed that a simple `intervention arm -> comparator arm` model would be scientifically insufficient.

## Candidate mapping verification

The Stage 5 seed manifest passed with:

```text
seed studies             18
mapped studies           10
not_yet_extracted         4
not_applicable            4
study arms/conditions    29
arm-component links      18
study contrasts           8
contrast-arm members     16
```

The manifest-level gates passed:

```text
controlled_vocabularies:       PASS
source_and_component_identity: PASS
arm_and_contrast_integrity:    PASS
no_fabricated_equal_allocation: PASS
human_approval_boundary:       PASS
```

No per-arm sample sizes were inferred by equal allocation from study-level totals.

## Database verification

After the Stage 5 migration and replayable seed mapper were applied locally, the database validator passed:

```text
STAGE 5 STUDY-ARM ARCHITECTURE VALID
studies=18
status_rows=18
arms=29
component_links=18
contrasts=8
contrast_members=16
```

Explicit status distribution:

```text
arms:
  partially_extracted = 10
  not_yet_extracted   = 4
  not_applicable      = 4

contrasts:
  partially_extracted = 6
  not_yet_extracted   = 8
  not_applicable      = 4
```

Structural integrity gates passed:

```text
factorial_component_reuse:    PASS
arm_component_integrity:      PASS
contrast_membership_integrity: PASS
human_approval_boundary:      PASS
```

The factorial reuse test specifically confirmed:

```text
reused_components    = 6
multi_component_arms = 2
```

This proves both required many-to-many behaviours:

- one normalized component can legitimately occur in multiple arms; and
- one arm can legitimately contain multiple normalized components.

## Factorial integrity

The Baduanjin × cognitive-training study is now representable as four factorial cells:

```text
control
Baduanjin only
cognitive training only
Baduanjin + cognitive training
```

while retaining only two reusable normalized intervention components:

```text
Baduanjin
cognitive_training
```

Likewise, the AI-tutoring × mastery-progression study can represent the recoverable policy cells without duplicating component identity or manufacturing unsupported factorial estimands.

Stage 5 deliberately does not auto-generate every statistically possible factorial contrast. Contrast extraction remains evidence-driven and reviewable.

## Missingness / completeness semantics

Every seed study now has explicit Stage 5 state rather than silent nulls.

The schema distinguishes:

```text
not_yet_extracted
partially_extracted
reviewed_complete
reviewed_no_arms / reviewed_no_contrasts
not_reported
not_applicable
```

This allows mechanism studies with incompletely extracted conditions to remain `not_yet_extracted`, while aggregate reviews and continuous observational records can legitimately be `not_applicable` at the source-study arm level.

## Human approval boundary

All Stage 5 candidate structures remain:

```text
mapping_source = agent_candidate
review_status  = proposed
```

The local database verification confirmed:

```text
0 agent candidates promoted
```

Workbench reviewers can approve, reject or correct arm roles, assignment structures, component memberships and contrasts. Automated candidate extraction therefore remains distinct from scientific approval.

## Workbench verification

The Evidence Workbench now displays Stage 5 separately from the historical study summary.

Reviewers can inspect and govern:

```text
study-level extraction status
arms / conditions
arm role
assignment structure
arm sample information where actually extracted
component membership
contrast type
contrast arm membership
mapping source / review status
```

The historical `study.comparator_summary` remains visible for provenance/compatibility but is no longer editable as if it were the canonical v1.1 contrast representation.

The Workbench production build passed after the Stage 5 reviewer UI and comparator-field demotion were added.

## Deterministic replay / regression evidence

Stage 5 is integrated into the permanent local bootstrap after Stage 4 reconstruction.

Clean replay deterministically reconstructs the candidate Stage 5 state while preserving the historical Registry/Gateway baseline:

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

Stages 1–4 validators, the historical Registry validator and the `csi-evidence-v1` Gateway contract remain intact.

## Supabase advisor gate

The final local Supabase advisor gate completed successfully with no blocking correctness or security findings. Remaining observations were non-blocking `INFO / PERFORMANCE` items of the same class previously observed on the small freshly rebuilt seed database, including unused-index and unindexed-foreign-key optimisation notices.

These are tracked as performance/maintenance considerations rather than Stage 5 scientific or structural failures.

## Compatibility decision

- The immutable `2026-08-23` release remains unchanged.
- `study.comparator_summary` is retained as historical compatibility metadata.
- Historical normalized `intervention_component` rows remain unchanged.
- Stage 5 structures are additive.
- `csi-evidence-v1` remains unchanged.
- No production Supabase mutation was required for Stage 5 verification.
- AI/agent arm and contrast mappings remain candidate-only until human review.

## Next stage

Proceed to **Stage 6 — first-class effect estimates**.

Stage 6 should attach quantitative estimates to the appropriate scientific comparison and outcome/result rather than treating a single effect field on `evidence_outcome` as sufficient:

```text
STUDY CONTRAST × OUTCOME / RESULT
        ↓
EFFECT ESTIMATE(S)
```
