# Evidence Registry v1.1 — Stage 4 Outcome Architecture

**Status:** IN PROGRESS
**Date:** 31 August 2026
**Branch:** `evidence-registry-v1.1`

## Goal

Replace the overloaded historical `evidence_rung` interpretation with orthogonal, queryable outcome dimensions while preserving the immutable `2026-08-23` release and all 38 normalized seed outcomes.

Stage 4 separates:

```text
WHAT WAS MEASURED?
→ outcome identity / functional domain

HOW FAR FROM THE TRAINED OBJECT?
→ outcome distance

WHEN WAS IT MEASURED?
→ time / follow-up

DID IT TEST PORTABILITY?
→ transfer axis

WHAT ROLE DOES THE RESULT PLAY?
→ outcome role

WAS REAL-WORLD USE SCAFFOLDED OR INDEPENDENT?
→ Bridge-specific evidence
```

These dimensions remain separate from intervention route, source evidence role, effect size, RoB/GRADE, EML, population/context and product relevance.

---

## 1. Canonical outcome dimensions

### Outcome distance

Controlled values:

```text
trained_task
changed_format
separate_measure
real_life_function
```

Outcome distance is about measurement distance from the trained/intervened object. It is not a time label and does not by itself establish far transfer.

For evidence that has no trained/intervened object at all (for example pure mechanism, measurement or observational evidence), outcome distance is not applicable. This must be represented through the dimension's explicit classification status rather than by inventing a distance value.

### Time / follow-up

Controlled high-level classes:

```text
immediate
post_intervention
delayed
```

Retain the raw reported timepoint separately, e.g. `post`, `6_months`, `next_day`, `12_weeks`.

**Seed-audit correction:** time cannot be a single-valued field at the legacy outcome-row level. Several seed rows summarise more than one assessment time, including `post_and_3_months` and `post_and_4_6_week_followup`. Stage 4 must therefore support more than one time classification per historical outcome row.

Use a child/link structure such as:

```text
outcome_timepoint
```

with at minimum:

```text
outcome_id
time_class
raw_timepoint
mapping_source
review_status
```

A compound historical row may therefore carry both:

```text
post_intervention
+
delayed
```

while the exact legacy label remains preserved.

Stage 4 does not yet pretend that a compound legacy result has been fully decomposed into separate numerical results at each timepoint. Where one historical row summarises multiple times, preserve that fact explicitly for later full result/effect extraction.

### Transfer axis

Controlled values:

```text
horizontal
vertical
niche
```

Transfer is potentially many-to-many at the result level. A result may legitimately test more than one axis.

**Do not infer transfer from distance alone.** In particular:

```text
changed_format ≠ automatically horizontal transfer
separate_measure ≠ automatically vertical transfer
real_life_function ≠ automatically niche transfer
```

The seed audit found no explicit normalized `transfer_axes` values. Stage 4 may propose transfer mappings from reviewed source interpretation later, but the legacy migration must not silently manufacture them.

### Outcome role

Controlled values:

```text
benefit
harm
target_engagement
process
adherence
implementation
```

Outcome role should not be inferred from effect direction. A null benefit outcome remains a benefit-role outcome with a null result.

For pure mechanism, measurement or observational evidence where these intervention/evaluation roles are not scientifically appropriate, role classification may be explicitly `not_applicable`. Source evidence role and Stage 3 mechanism assertions retain the scientific meaning of those records.

### Bridge-specific evidence

Controlled values:

```text
prompted_use
cue_triggered_use
changed_context_use
unprompted_use
delayed_portability
```

Bridge evidence remains separate from the generic transfer axis because it concerns dependence on prompts/cues and real-world policy recovery.

The seed audit found no explicit Bridge-evidence values in the 38 outcomes. Absence of coding must therefore remain an explicit extraction/review state rather than being interpreted as evidence that Bridge transfer did not occur.

---

## 2. Missingness and result semantics

Stage 4 must distinguish classification missingness from result direction.

Minimum classification states, applied per dimension where appropriate:

```text
not_yet_extracted
reviewed_mapped
reviewed_no_mapping
not_reported
not_measured
not_applicable
```

Result direction remains a separate scientific dimension, including where supported:

```text
positive
null
negative_or_harmful
mixed
unclear
```

Therefore:

```text
NOT MEASURED ≠ NULL EFFECT
NOT REPORTED ≠ NO HARM
DELAYED ≠ FAR TRANSFER
SEPARATE MEASURE ≠ AUTOMATIC VERTICAL TRANSFER
NON-INTERVENTION EVIDENCE ≠ TRAINED-TASK DISTANCE
```

---

## 3. Compatibility rule

Stage 4 is additive first.

Do not initially drop or rewrite the historical columns:

```text
evidence_outcome.evidence_rung
evidence_outcome.timepoint
evidence_outcome.transfer_axes
evidence_outcome.bridge_evidence_level
```

They remain a compatibility/audit surface for the `2026-08-23` seed while new normalized Stage 4 structures become canonical for v1.1 review.

Legacy values must map through an explicit reviewed mapping/backfill process. Ambiguous labels must not be silently coerced.

---

## 4. Seed-audit findings and locked legacy treatment

The read-only 38-outcome audit produced these legacy rung counts:

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

It also found:

```text
legacy transfer-axis links        0
legacy Bridge-evidence links       0
JSON ↔ normalized mismatches       0
```

### Deterministic legacy semantics

These mappings are safe at the semantic-label level:

```text
practice_effect
→ outcome distance: trained_task

changed_format
→ outcome distance: changed_format

separate_measure
→ outcome distance: separate_measure

delayed
→ time class: delayed

mechanism
→ outcome-distance status: not_applicable
→ outcome-role status: not_applicable
→ preserve/use Stage 1 mechanism evidence role and Stage 3 mechanism assertion

measurement
→ outcome-distance status: not_applicable
→ outcome-role status: not_applicable
→ preserve/use Stage 1 measurement evidence role

observational_longitudinal
→ outcome-distance status: not_applicable
→ intervention outcome-role status: not_applicable
→ preserve/use Stage 1 observational evidence role
```

### Candidate / interpretive legacy semantics

These must remain reviewable rather than auto-approved:

```text
applied
→ candidate outcome distance: real_life_function

practice_or_nearest_transfer
→ candidate outcome distance requires outcome/source interpretation

practice_or_separate_measure
→ candidate outcome distance requires outcome/source interpretation
```

Likewise, a `delayed` legacy rung does not specify outcome distance. The distance must be recovered from the outcome/source context.

### Time-class treatment from raw timepoints

Raw timepoint labels are preserved. High-level time classes can be proposed conservatively:

```text
immediate | immediate_test
→ immediate

post | after_training | week_8
→ post_intervention

6_months | 1_week | subsequent_test | second_scan
→ delayed candidate where the source context supports a follow-up interpretation

post_and_3_months | post_and_4_6_week_followup
→ post_intervention + delayed
```

Labels such as:

```text
during_intervention
during_platform_use
during_stress
T2
T3
varied
```

must be handled from source context rather than through a global string substitution.

---

## 5. Proposed database shape

Use additive controlled definition tables plus per-dimension mappings/status.

Target shape:

```text
outcome_distance_definition
outcome_time_definition
transfer_axis_definition
outcome_role_definition
bridge_evidence_definition

outcome_stage4_status
outcome_distance_mapping
outcome_timepoint
outcome_transfer_axis
outcome_role_link
outcome_bridge_evidence
legacy_outcome_semantic_map
```

### `outcome_stage4_status`

One row per historical/normalized outcome, carrying explicit review/completeness states for each dimension, for example:

```text
outcome_id
outcome_distance_status
time_status
transfer_status
outcome_role_status
bridge_status
notes
mapping_source
updated_at
```

This avoids a single omnibus status hiding which dimension has actually been reviewed.

### Mapping/link provenance

Every scientifically consequential mapping must contain:

```text
mapping_source
review_status
rationale where interpretive
```

consistent with the Stage 3 human-approval boundary.

Many-to-many dimensions use link tables rather than encoded comma-separated strings.

---

## 6. Stable identity for seed replay

The historical importer deletes and recreates `study` and child `evidence_outcome` rows on every clean bootstrap. Seed backfill must therefore not depend on `outcome_id` alone.

Use a stable lookup identity derived from the immutable seed record, validated for uniqueness, such as:

```text
source_id
+ outcome_name
+ legacy evidence_rung
+ raw timepoint
```

Where duplicate combinations exist or emerge in later releases, add an explicit release-record outcome ordinal/key rather than relying on regenerated database IDs.

The Stage 4 mapper must fail closed if a manifest outcome resolves to zero or multiple normalized rows.

---

## 7. Bootstrap/replay rule

Stage 4 normalized mappings must be replayable after the historical importer, analogous to Stage 3 candidate mappings.

The permanent clean replay will eventually become:

```text
historical seed import
→ Stage 2 source identity validation
→ Stage 3 candidate mappings + validation
→ Stage 4 outcome semantic backfill
→ Stage 4 validator
→ Registry/Gateway validation
→ LOCAL REGISTRY BASELINE PASS
```

---

## 8. Workbench requirements

The Workbench outcome card should stop presenting one `Evidence rung` field as scientific authority.

Display separately:

```text
Outcome distance
Time class(es) + raw timepoint
Transfer axis/axes
Outcome role/roles
Bridge evidence, where applicable
Result direction
Effect summary
Mapping source / review status
```

Editors should be able to approve, reject or correct candidate mappings. AI/automated legacy mappings must never self-promote to human-approved status.

For non-intervention mechanism/measurement/observational records, the UI should display a normal explicit state such as:

```text
Outcome distance: Not applicable
Outcome role: Not applicable
Evidence contribution: Mechanism / Measurement / Observational
```

rather than forcing the row into an intervention-transfer ladder.

Compound historical time rows should be visibly flagged until full result-level extraction separates their time-specific findings.

---

## 9. Validation targets

Stage 4 validator must prove at minimum:

```text
seed outcomes                                      38
outcomes with explicit Stage 4 status              38
unknown legacy rung values                          0
orphan distance mappings                            0
orphan timepoint links                              0
orphan transfer-axis links                          0
orphan outcome-role links                           0
invalid controlled vocabulary values                0
legacy-vs-normalized identity loss                   0
automated/agent candidates approved                 0
```

It must also verify that the model can represent, for example:

```text
separate_measure
+ post_intervention
+ delayed
```

for a compound historical row, and independently:

```text
separate_measure
+ delayed
+ vertical
```

when a later reviewed result genuinely establishes all three dimensions.

---

## 10. Stage 4 implementation sequence

1. Audit the 38 historical outcomes and legacy vocabulary. **DONE.**
2. Lock deterministic versus interpretive legacy mappings. **DONE at semantic-rule level; individual candidate manifest next.**
3. Validate stable outcome lookup identity across the 38 seed rows.
4. Create the reviewed/candidate Stage 4 seed mapping manifest.
5. Generate an additive Supabase migration.
6. Add controlled definition tables and normalized outcome structures.
7. Add explicit per-dimension missingness/review/provenance fields.
8. Add deterministic/candidate seed backfill that survives clean bootstrap.
9. Add Stage 4 validator and integrate it into permanent bootstrap.
10. Update Workbench outcome review UI.
11. Run clean `supabase db reset` + full bootstrap.
12. Run Stage 1–4, Registry and Gateway regression validators.
13. Build the Workbench.
14. Run local Supabase security/performance advisors.
15. Record Stage 4 verification evidence and mark the canonical plan VERIFIED.

---

## Exit criteria

Stage 4 is VERIFIED only when:

- outcome distance, time, transfer and outcome role are represented independently;
- time supports compound post-intervention + delayed historical rows without information loss;
- Bridge-specific evidence is separately representable;
- classification missingness cannot be confused with null or harmful results;
- non-intervention mechanism/measurement/observational evidence is not forced into intervention-distance semantics;
- all 38 seed outcomes migrate/replay without loss;
- all legacy `evidence_rung` values have explicit reviewed treatment;
- Workbench reviewers can see and govern the new dimensions separately;
- the `2026-08-23` release and `csi-evidence-v1` remain unchanged; and
- all earlier Stage 1–3 invariants continue to pass.
