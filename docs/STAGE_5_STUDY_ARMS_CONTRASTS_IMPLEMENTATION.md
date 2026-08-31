# Evidence Registry v1.1 — Stage 5 Study Arms, Component Membership and Contrasts

**Status:** IN PROGRESS
**Date:** 31 August 2026
**Branch:** `evidence-registry-v1.1`

## Goal

Replace the current study-level flattening of intervention and comparator information with an explicit design model that can represent parallel trials, active controls, multi-arm studies, factorial designs, quasi-experimental conditions and within-subject conditions without changing the scientific meaning of intervention components.

Stage 5 separates:

```text
STUDY
What experiment / investigation is this?

ARM / CONDITION
What condition or group was assigned, exposed or observed?

COMPONENT MEMBERSHIP
Which normalized intervention components are present in an arm?

CONTRAST
Which arms/conditions are being compared for a scientific question?
```

These remain separate from:

```text
intervention route
target / mechanism
outcome distance / time / transfer / role
effect estimate
risk of bias / GRADE
EML
population / context
```

The governing rule is:

> **An intervention component is not an arm, and an arm is not a contrast.**

---

## 1. Why Stage 5 is necessary

The historical v1.0 seed model stores:

```text
study.comparator_summary
intervention_component
```

but does not represent the actual experimental groups/conditions.

This is insufficient for several seed designs.

### 2×2 factorial example

The Baduanjin + cognitive-training study contains four cells:

```text
control
Baduanjin only
cognitive training only
Baduanjin + cognitive training
```

but only two reusable intervention components:

```text
Baduanjin
cognitive training
```

Therefore:

```text
COMPONENT != ARM
```

and factorial main effects require comparisons across groups of arms rather than one simple intervention arm versus one comparator arm.

### Multi-condition AI example

The AI-writing study contains:

```text
no AI
bounded AI + compulsory reflection
open AI collaboration
```

plus a later supervised no-AI follow-up task.

Those conditions must be represented independently from any Trident-G/H-AGI interpretation of their components.

---

## 2. Canonical Stage 5 hierarchy

Target architecture:

```text
study
├── study_arm
│   └── arm_component
│
└── study_contrast
    └── contrast_arm_member
```

A future Stage 6 effect estimate will attach to:

```text
study_contrast × evidence_outcome/result
```

rather than merely to a paper or study.

---

## 3. Study arm / condition

Create:

```text
study_arm
```

Minimum fields:

```text
arm_id
study_id
arm_key
arm_label
author_arm_label
arm_role
assignment_structure
arm_description
sample_json
mapping_source
review_status
created_at
updated_at
```

`arm_key` is a stable registry identifier unique within a study. It is not an author-facing label.

Examples:

```text
control
active_control
executive_function_training
baduanjin_only
cognitive_training_only
combined_baduanjin_cognitive
bounded_ai_reflection
open_ai
no_ai
```

### Arm role

Initial controlled roles should support at least:

```text
intervention
active_control
passive_control
waitlist
treatment_as_usual
alternative_intervention
reference
observational_exposure
unclear
```

Role describes how the arm functions in the study. It does not specify intervention route.

### Assignment structure

Keep design structure separate from arm role.

Initial controlled values:

```text
parallel_group
cluster_group
factorial_cell
within_subject_condition
single_group
observational_group
unclear
```

Examples:

```text
active-control training arm
→ arm_role = active_control
→ assignment_structure = parallel_group

combined cell in a 2×2 trial
→ arm_role = intervention
→ assignment_structure = factorial_cell
```

---

## 4. Component membership

Create:

```text
arm_component
```

Minimum fields:

```text
arm_id
component_id
membership_role
rationale
mapping_source
review_status
```

Initial membership roles:

```text
defining
shared
add_on
background
unclear
```

The same normalized intervention component may appear in several arms.

For the 2×2 example:

```text
Baduanjin component
→ Baduanjin-only arm
→ combined arm

cognitive-training component
→ cognitive-training-only arm
→ combined arm
```

No duplicate component identity should be created simply because the same component appears in multiple arms.

### Comparator components

Stage 5 does not require invented normalized components for comparator conditions when the rapid-review seed only provides a comparator label/description.

An active-control arm may therefore legitimately exist with:

```text
arm_description = author/review description
arm_component extraction = not_yet_extracted
```

rather than fabricating a route-coded comparator component.

---

## 5. Explicit arm/component extraction state

Create study-level and/or arm-level completeness status sufficient to distinguish:

```text
not_yet_extracted
partially_extracted
reviewed_complete
reviewed_no_arms
not_reported
not_applicable
```

Non-intervention evidence must not receive synthetic trial arms merely to satisfy the schema.

For example:

```text
measurement review
mechanism-only study
observational evidence
```

may have Stage 5 status `not_applicable` or may use observational groups/conditions only when scientifically justified.

---

## 6. Study contrasts

Create:

```text
study_contrast
contrast_arm_member
```

### study_contrast

Minimum fields:

```text
contrast_id
study_id
contrast_key
contrast_label
contrast_type
estimand_summary
mapping_source
review_status
created_at
updated_at
```

Initial `contrast_type` values:

```text
pairwise
multiarm_pairwise
factorial_main_effect
factorial_interaction
within_subject
observational
other
```

A contrast is a scientific comparison, not merely a textual comparator field.

### contrast_arm_member

Minimum fields:

```text
contrast_id
arm_id
contrast_side
contrast_coefficient nullable
rationale
```

Initial `contrast_side`:

```text
focal
comparator
```

The optional coefficient allows factorial/interaction contrasts to be represented without forcing them into a single-arm-versus-single-arm structure.

For a simple pairwise contrast:

```text
intervention   +1
control        -1
```

For a factorial main effect, several cells can contribute to each side.

The coefficient is structural metadata for the intended comparison; quantitative effect estimates are Stage 6.

---

## 7. Factorial designs are first-class

Stage 5 must explicitly support factorial cells.

For the 2×2 Baduanjin × cognitive-training example:

```text
ARM 1 control
ARM 2 Baduanjin only
ARM 3 cognitive training only
ARM 4 combined
```

Component membership:

```text
ARM 1 → no normalized intervention component
ARM 2 → Baduanjin
ARM 3 → cognitive training
ARM 4 → Baduanjin + cognitive training
```

Possible contrasts include:

```text
Baduanjin main effect
cognitive-training main effect
Baduanjin × cognitive-training interaction
combined vs control
```

The seed backfill should only propose contrasts explicitly recoverable from the rapid-review record; it must not manufacture all statistically possible factorial contrasts.

---

## 8. Multi-arm and quasi-experimental studies

Three-arm and multi-condition studies should create one arm/condition per clearly described assigned condition.

Examples from the seed may include:

```text
training
behavioral training
control
```

or:

```text
no AI
bounded AI + reflection
open AI
```

Assignment structure should reflect the study design rather than assume randomisation.

A quasi-experimental classroom condition is not automatically a randomized arm.

---

## 9. Within-subject conditions

If a seed study exposes the same participants to multiple experimental conditions, Stage 5 may represent them as:

```text
assignment_structure = within_subject_condition
```

This prevents a forced parallel-group interpretation.

The audit/backfill must determine whether any of the 18 seed records require this representation.

---

## 10. Sample-size semantics

Do not infer per-arm sample sizes from total randomized/analysed counts unless explicitly supported.

Retain study-level historical sample metadata.

`study_arm.sample_json` may store, where actually reported:

```text
randomized
assigned
analysed
completed
cluster_count
```

Missing arm-level counts remain missing.

No equal-allocation arithmetic should be used to fabricate arm sample sizes.

---

## 11. Compatibility rule

Stage 5 is additive first.

Do not remove or rewrite:

```text
study.comparator_summary
intervention_component
historical raw_record JSON
```

The existing comparator summary remains a historical compatibility/audit field while the normalized arm/contrast model becomes canonical for v1.1 scientific interpretation.

The immutable `2026-08-23` release and `csi-evidence-v1` must remain unchanged.

---

## 12. Stable replay identity

The historical importer deletes and recreates `study` and its child rows during clean bootstrap.

Stage 5 therefore must not depend on regenerated numeric IDs alone.

Candidate seed mappings should resolve studies using stable source identity:

```text
source_id
```

and arms/contrasts using stable per-study keys:

```text
source_id + arm_key
source_id + contrast_key
```

Component membership should resolve normalized components using:

```text
source_id + component_name
```

with uniqueness validation.

---

## 13. Human approval boundary

As in Stages 3–4:

```text
AI / agent
→ candidate extraction only
→ mapping_source = agent_candidate
→ review_status = proposed
```

Only a Workbench human review may convert scientific mappings to:

```text
mapping_source = human_review
review_status = approved
```

A deterministic parser may identify an explicitly enumerated condition list, but that still does not self-approve scientific arm roles or contrasts.

---

## 14. Conservative seed backfill

Use only information actually represented in the reviewed seed, including:

```text
study.design
study.comparator
study.sample
protocol.component(s)
protocol.conditions
protocol.active_control
raw-record descriptions
```

Do not infer arm structure from:

```text
paper title alone
product relevance
outcome direction
route classification alone
```

### Backfill categories

Every one of the 18 seed studies should end Stage 5 with explicit state:

```text
candidate arms/contrasts mapped
or
not_yet_extracted
or
not_applicable
```

No silent null state.

---

## 15. Workbench requirements

For each study, display separately:

```text
STUDY DESIGN
ARMS / CONDITIONS
COMPONENT MEMBERSHIP
CONTRASTS
```

Each arm should show:

```text
label
role
assignment structure
sample information if available
component memberships
mapping source / review status
```

Each contrast should show its participating arms and whether it is pairwise, factorial, within-subject or observational.

Editors should be able to approve, reject and correct agent candidates without editing the immutable seed JSON.

The existing free-text comparator summary should be visually demoted to historical compatibility metadata once Stage 5 review UI is available.

---

## 16. Validation targets

Minimum structural checks:

```text
18 seed studies
→ all have explicit arm extraction status
→ all have explicit contrast extraction status

orphan study arms                         0
orphan arm-component links               0
orphan contrast-arm links                0
invalid arm roles                        0
invalid assignment structures            0
invalid contrast types                   0
cross-study arm membership               0
cross-study contrast membership          0
agent candidates approved                0
```

Factorial integrity test:

```text
one component can belong to multiple arms
one arm can contain multiple components
one contrast can contain multiple arms per side
```

Regression checks:

```text
Stage 1 validator PASS
Stage 2 validator PASS
Stage 3 validators PASS
Stage 4 validators PASS
historical Registry validator PASS
CSI Gateway validator PASS
bootstrap baseline PASS
Workbench build PASS
Supabase advisor gate PASS
```

---

## 17. Stage 5 implementation sequence

1. Audit all 18 seed study designs, comparator summaries, protocol components/conditions and sample metadata.
2. Classify which seed studies have explicitly recoverable arms/conditions and which remain not-yet-extracted/not-applicable.
3. Lock controlled arm-role, assignment-structure and contrast-type vocabularies.
4. Generate an additive Supabase migration.
5. Add `study_arm`, `arm_component`, `study_contrast`, `contrast_arm_member` and explicit extraction-status structures.
6. Add RLS, grants and audit coverage.
7. Create a conservative Stage 5 candidate mapping manifest using stable keys.
8. Add replayable Stage 5 mapper.
9. Add Stage 5 validators and integrate into permanent bootstrap.
10. Add Workbench arm/component/contrast review UI.
11. Demote historical `comparator_summary` to compatibility metadata in the UI.
12. Clean reset + full deterministic bootstrap.
13. Run Stage 1–5 and Registry/Gateway regressions.
14. Build Workbench and run Supabase advisors.
15. Record Stage 5 verification evidence and mark the canonical tracker VERIFIED.

---

## Exit criteria

Stage 5 is VERIFIED only when:

- study arms/conditions are represented independently from intervention components;
- the same component can belong to multiple arms without duplicated component identity;
- active controls, passive controls, waitlists, TAU and alternative interventions can be represented explicitly;
- factorial cells and multi-arm contrasts can be represented without flattening;
- within-subject conditions can be represented without pretending they are parallel groups;
- all 18 seed studies have explicit Stage 5 extraction state;
- no per-arm sample size is fabricated from study totals;
- candidate arm/contrast mappings remain human-review gated;
- clean bootstrap deterministically reconstructs Stage 5;
- the `2026-08-23` release and `csi-evidence-v1` remain unchanged; and
- all Stage 1–4 invariants continue to pass.
