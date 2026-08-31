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

These dimensions remain separate from intervention route, effect size, RoB/GRADE, EML, population/context and product relevance.

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

### Time / follow-up

Controlled high-level classes:

```text
immediate
post_intervention
delayed
```

Retain the raw reported timepoint separately, e.g. `post`, `6_months`, `next_day`, `12_weeks`.

### Transfer axis

Controlled values:

```text
horizontal
vertical
niche
```

Transfer is potentially many-to-many at the result level. A result may legitimately test more than one axis.

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

---

## 2. Missingness and result semantics

Stage 4 must distinguish classification missingness from result direction.

Minimum classification states:

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

## 4. Proposed database shape

Final table names may be adjusted after the seed audit, but the target shape is:

```text
outcome_distance_definition
outcome_time_definition
transfer_axis_definition
outcome_role_definition
bridge_evidence_definition

outcome_stage4_classification
outcome_transfer_axis
outcome_role_link
outcome_bridge_evidence
legacy_outcome_semantic_map
```

`outcome_stage4_classification` should hold the single-valued outcome-distance and high-level time classification plus explicit extraction/review state and provenance.

Many-to-many dimensions should use link tables rather than encoded comma-separated strings.

All scientifically consequential mappings require `mapping_source` and `review_status` fields consistent with the Stage 3 human-approval boundary.

---

## 5. Legacy audit before migration

Before writing the Stage 4 migration, audit all 38 seed outcomes for:

```text
distinct evidence_rung values
distinct raw timepoint values
distinct transfer-axis values
distinct Bridge evidence values
legacy JSON ↔ normalized-column parity
source/outcome combinations requiring interpretive review
```

The audit must identify which legacy mappings are deterministic and which require source-level human review.

No schema backfill should be approved until every legacy rung has a documented treatment.

---

## 6. Bootstrap/replay rule

The historical importer deletes and recreates `study` and child `evidence_outcome` rows on every clean bootstrap.

Therefore Stage 4 normalized mappings must be replayable after the historical importer, analogous to Stage 3 candidate mappings.

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

Stage 4 must never depend on unstable `outcome_id` values alone if those IDs can be regenerated. Seed mapping identity should be based on stable source/study/outcome characteristics and validated for uniqueness.

---

## 7. Workbench requirements

The Workbench outcome card should stop presenting one `Evidence rung` field as scientific authority.

Display separately:

```text
Outcome distance
Time class + raw timepoint
Transfer axis/axes
Outcome role/roles
Bridge evidence, where applicable
Result direction
Effect summary
Mapping source / review status
```

Editors should be able to approve, reject or correct candidate mappings. AI/automated legacy mappings must never self-promote to human-approved status.

---

## 8. Validation targets

Stage 4 validator must prove at minimum:

```text
seed outcomes                                      38
outcomes with explicit Stage 4 classification     38
unknown legacy rung values                          0
orphan transfer-axis links                          0
orphan outcome-role links                           0
invalid controlled vocabulary values                0
legacy-vs-normalized identity loss                   0
agent/automated candidates approved                 0
```

It must also verify that a result can represent, for example:

```text
separate_measure + delayed + vertical
```

without collapsing those dimensions.

---

## 9. Stage 4 implementation sequence

1. Audit the 38 historical outcomes and legacy vocabulary.
2. Lock deterministic versus interpretive legacy mappings.
3. Generate an additive Supabase migration.
4. Add controlled definition tables and normalized outcome structures.
5. Add explicit missingness/review/provenance fields.
6. Add a deterministic/candidate seed backfill that survives clean bootstrap.
7. Add Stage 4 validator and integrate it into permanent bootstrap.
8. Update Workbench outcome review UI.
9. Run clean `supabase db reset` + full bootstrap.
10. Run Stage 1–4, Registry and Gateway regression validators.
11. Build the Workbench.
12. Run local Supabase security/performance advisors.
13. Record Stage 4 verification evidence and mark the canonical plan VERIFIED.

---

## Exit criteria

Stage 4 is VERIFIED only when:

- outcome distance, time, transfer and outcome role are represented independently;
- Bridge-specific evidence is separately representable;
- classification missingness cannot be confused with null or harmful results;
- all 38 seed outcomes migrate/replay without loss;
- all legacy `evidence_rung` values have explicit reviewed treatment;
- Workbench reviewers can see and govern the new dimensions separately;
- the `2026-08-23` release and `csi-evidence-v1` remain unchanged; and
- all earlier Stage 1–3 invariants continue to pass.
