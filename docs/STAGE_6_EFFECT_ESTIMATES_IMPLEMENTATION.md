# Evidence Registry v1.1 — Stage 6 First-Class Effect Estimates

**Status:** IN PROGRESS  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`

## Goal

Replace the current one-effect-per-outcome compatibility fields with a first-class quantitative result model that can support multiple legitimate estimates for the same outcome, attach estimates to the correct study contrast, preserve model/adjustment information, and become exportable for later quantitative synthesis.

The governing hierarchy is:

```text
STUDY
  ↓
STUDY CONTRAST
  ↓
EVIDENCE OUTCOME / RESULT
  ↓
EFFECT ESTIMATE(S)
```

The central invariant is:

> **Outcome != contrast != effect estimate.**

Stage 6 is additive first. Historical `evidence_outcome.effect_metric`, `effect_estimate`, `ci_lower` and `ci_upper` remain compatibility/audit fields for the immutable `2026-08-23` release.

---

## 1. Why Stage 6 is necessary

The v1.0 seed model stores at most one estimate directly on an outcome:

```text
effect_metric
effect_estimate
ci_lower
ci_upper
```

This cannot correctly represent cases such as:

```text
unadjusted + adjusted estimates
several model specifications
several contrasts for the same outcome
several follow-up estimates
raw group values plus derived comparative effect
multiple effect measures reported for one result
factorial main effects and interactions
```

Stage 5 established explicit `study_contrast` objects. Stage 6 now gives quantitative evidence the correct scientific subject.

---

## 2. Canonical Stage 6 model

Minimum target architecture:

```text
effect_estimate
```

with optional linked raw summaries where supported:

```text
arm_outcome_summary
```

A first-class effect estimate should attach to:

```text
outcome_id
+ contrast_id where a contrast is scientifically applicable
```

For within-group, single-group, correlational or otherwise non-contrast estimates, `contrast_id` may be null only when the estimate type legitimately does not require a Stage 5 contrast.

---

## 3. Effect-estimate fields

Minimum fields should support:

```text
effect_estimate_id
outcome_id
contrast_id nullable
estimate_key
estimate_type
metric
estimate_value
standard_error nullable
ci_level nullable
ci_lower nullable
ci_upper nullable
p_value nullable
n_analysed nullable
adjustment_status
model_specification nullable
time_or_model_label nullable
unit nullable
scale_direction nullable
source_reported boolean
rationale / notes
mapping_source
review_status
created_at
updated_at
```

`estimate_key` is a stable per-outcome registry identifier and not an author-facing label.

---

## 4. Supported estimate types / metrics

Stage 6 should support at least the following broad scientific estimate classes:

```text
raw_mean
raw_proportion
change_score
mean_difference
standardised_mean_difference
odds_ratio
risk_ratio
hazard_ratio
correlation
regression_coefficient
rate_ratio
other
```

Do not force all quantitative values into a single `effect_size` semantic.

The source-reported metric should be retained faithfully. Later synthesis/export code may transform supported metrics, but Stage 6 should not silently convert them during ingestion.

---

## 5. Adjustment/model semantics

Keep statistical adjustment separate from effect metric.

Initial controlled values:

```text
unadjusted
adjusted
partially_adjusted
not_applicable
unclear
```

Where relevant, retain:

```text
covariates
model family
interaction terms
baseline adjustment
cluster correction
robust SE specification
repeated-measures specification
```

as structured or free-text model metadata without pretending unextracted details are known.

---

## 6. Raw arm/group summaries

Where studies report group-level descriptive data needed for effect reconstruction, support an optional child structure:

```text
arm_outcome_summary
```

Minimum useful fields may include:

```text
arm_id
outcome_id
summary_key
n
mean
sd
se
proportion
count
change_mean
change_sd
unit
mapping_source
review_status
```

Do not fabricate missing SDs, Ns or equal allocation.

Raw summaries are not themselves contrasts and should not be stored as if they were comparative effect estimates.

---

## 7. Contrast linkage

For comparative estimates from parallel, multi-arm or factorial designs:

```text
effect_estimate.contrast_id
```

should identify the Stage 5 scientific comparison.

One outcome may legitimately have:

```text
multiple contrasts
×
multiple estimates/models per contrast
```

Stage 6 therefore must not impose uniqueness on `outcome_id` alone.

For factorial studies, the schema must support:

```text
main-effect estimates
interaction estimates
cell-pair estimates
```

without manufacturing contrasts that Stage 5 has deliberately left `not_yet_extracted`.

---

## 8. Non-contrast quantitative evidence

Not every quantitative result is a group contrast.

Examples may include:

```text
correlation
regression coefficient
single-group change
within-person association
measurement/reliability estimate
```

Such estimates may use `contrast_id = NULL` only when scientifically justified and explicitly typed.

Stage 6 must not create fake intervention-vs-control contrasts simply to satisfy the schema.

---

## 9. Confidence intervals, SEs and p-values

Store uncertainty components separately:

```text
standard_error
ci_level
ci_lower
ci_upper
p_value
```

Rules:

- a p-value is not a substitute for an effect estimate;
- absence of a CI is not a null result;
- CI level must not be assumed to be 95% unless explicitly reported or legitimately encoded by a reviewed extraction rule;
- one-sided and unusual intervals should be representable through notes/model metadata if needed.

---

## 10. Sample analysed semantics

`n_analysed` should describe the analytic sample for that estimate when actually reported.

Do not infer it from:

```text
study randomized N
study completed N
arm allocation totals
```

unless the source/review explicitly establishes equivalence.

Future meta-analysis exports should prefer estimate-specific analysed N over study-level totals when available.

---

## 11. Direction and scale orientation

The current `result_direction` field is qualitative interpretation and remains separate from the numeric effect.

Stage 6 should retain enough orientation metadata to prevent sign errors, especially when higher scores may mean worse outcomes.

At minimum support:

```text
higher_is_better
higher_is_worse
neutral_or_metric_defined
unclear
```

No automated sign reversal should occur without an explicit reviewed transformation rule.

---

## 12. Stable replay identity

The historical importer recreates numeric study/outcome IDs during clean bootstrap.

Stage 6 seed mappings therefore must resolve historical outcomes using the Stage 4 stable key:

```text
source_id
+ outcome_name
+ legacy_rung
+ raw_timepoint
```

and identify multiple estimates with a stable per-outcome `estimate_key`.

Contrast-linked estimates should resolve contrasts using:

```text
source_id + contrast_key
```

No durable seed mapping should depend only on regenerated numeric IDs.

---

## 13. Human approval boundary

As in Stages 3–5:

```text
AI / agent extraction
→ mapping_source = agent_candidate
→ review_status = proposed
```

Only human review may promote a quantitative estimate to approved scientific authority.

This is especially important for:

```text
metric interpretation
group orientation
adjusted vs unadjusted status
CI interpretation
contrast assignment
sign/orientation
sample analysed
```

---

## 14. Conservative seed backfill

Before migration, audit all 38 seed outcomes for:

```text
effect_metric
effect_estimate
ci_lower
ci_upper
outcome_json.effect
outcome_json.ci
other numeric keys in outcome_json
```

Backfill only values actually represented in the immutable seed.

Every seed outcome should receive explicit Stage 6 extraction state such as:

```text
not_yet_extracted
partially_extracted
reviewed_complete
reviewed_no_quantitative_estimate
not_reported
not_applicable
```

No silent null state.

---

## 15. Compatibility rule

Stage 6 is additive first.

Do not remove or mutate:

```text
evidence_outcome.effect_metric
evidence_outcome.effect_estimate
evidence_outcome.ci_lower
evidence_outcome.ci_upper
evidence_outcome.outcome_json
```

These fields remain compatibility/audit surfaces for the historical seed. The new effect-estimate model becomes canonical for v1.1 scientific interpretation.

The immutable `2026-08-23` release and `csi-evidence-v1` remain unchanged.

---

## 16. Workbench requirements

For each outcome/result, display separately:

```text
QUANTITATIVE EXTRACTION STATUS
EFFECT ESTIMATES
CONTRAST LINK
METRIC / TYPE
ESTIMATE
UNCERTAINTY
ANALYSED N
ADJUSTMENT / MODEL
PROVENANCE / REVIEW STATUS
```

The old one-effect compatibility fields should be visually demoted once Stage 6 review UI is available.

Reviewers should be able to approve, reject and correct candidate estimates without mutating the immutable seed JSON.

---

## 17. Validation targets

Minimum checks:

```text
38 seed outcomes
→ all have explicit quantitative extraction status

orphan effect estimates                 0
invalid outcome references              0
invalid contrast references             0
cross-study contrast/outcome mismatch   0
invalid estimate types                  0
invalid adjustment statuses             0
invalid scale orientation               0
impossible CI ordering                   0
agent candidates approved               0
```

Where an estimate is contrast-linked:

```text
contrast.study_id == outcome.study_id
```

must hold.

Regression gates:

```text
Stage 1–5 validators PASS
historical Registry validator PASS
CSI Gateway validator PASS
clean bootstrap PASS
Workbench build PASS
Supabase advisor gate PASS
```

---

## 18. Stage 6 implementation sequence

1. Audit all 38 historical outcome effect fields and raw JSON quantitative keys.
2. Identify the exact seed quantitative backfill surface and missingness pattern.
3. Lock effect-type, adjustment-status and scale-orientation vocabularies.
4. Generate additive Stage 6 migration.
5. Add first-class effect estimate and optional arm-summary structures.
6. Add explicit per-outcome Stage 6 extraction status.
7. Add RLS, grants and audit coverage.
8. Create conservative seed mapping manifest using Stage 4 stable outcome keys.
9. Add replayable Stage 6 mapper.
10. Add Stage 6 validators and permanent bootstrap integration.
11. Add Workbench quantitative review UI.
12. Demote historical one-effect fields to compatibility metadata in UI.
13. Clean reset + deterministic replay.
14. Run Stage 1–6 regressions, Registry/Gateway checks, Workbench build and Supabase advisors.
15. Record Stage 6 verification evidence and mark canonical tracker VERIFIED.

---

## Exit criteria

Stage 6 is VERIFIED only when:

- quantitative estimates are first-class child records rather than one overwriteable outcome field;
- comparative estimates can attach to the correct Stage 5 contrast;
- multiple estimates/models per outcome/contrast are supported;
- non-contrast quantitative results remain representable without fake contrasts;
- uncertainty, analysed N, adjustment and model metadata are distinct fields;
- raw group summaries can be represented without being confused with comparative estimates;
- all 38 seed outcomes have explicit Stage 6 extraction state;
- the historical seed effect fields are preserved losslessly;
- AI/agent quantitative extraction remains human-review gated;
- clean bootstrap deterministically reconstructs Stage 6;
- the `2026-08-23` release and `csi-evidence-v1` remain unchanged; and
- all Stage 1–5 invariants continue to pass.
