# Evidence Registry v1.1 — Stage 6 First-Class Effect Estimates Verification

**Stage:** 6 — First-class quantitative effect estimates  
**Status:** VERIFIED  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`  
**Implementation commit:** `97dc9378e4dd21d133f7df7e819c8512bf0935c3`  
**Migration:** `20260831194000_evidence_registry_v1_1_effect_estimates.sql`

## Decision

Stage 6 is verified.

The Registry no longer relies on the historical one-effect-per-outcome compatibility fields as the canonical quantitative model. Quantitative evidence is now represented as first-class child records with explicit scientific scope, estimate type, metric, uncertainty, model/adjustment metadata, provenance and review state.

The governing invariant is:

> **Outcome != contrast != effect estimate.**

Stage 6 also distinguishes raw arm/group summaries from comparative effect estimates.

## Implemented

Stage 6 adds:

- `outcome_stage6_status`
- `effect_estimate`
- `arm_outcome_summary`
- explicit per-outcome quantitative extraction state
- controlled estimate-scope vocabulary
- controlled estimate-type vocabulary
- controlled adjustment-status vocabulary
- controlled scale-direction vocabulary
- cross-study contrast/outcome integrity guard
- cross-study arm/outcome-summary integrity guard
- deterministic Stage 6 status-row creation after historical importer replay
- Stage 6 quantitative seed audit
- conservative Stage 6 seed mapping manifest
- Stage 6 manifest validator
- replayable Stage 6 seed mapper
- Stage 6 database architecture validator
- permanent Stage 6 integration in `bootstrap_local_registry.py`
- Workbench quantitative-review surface
- historical `evidence_outcome.effect_metric`, `effect_estimate`, `ci_lower` and `ci_upper` demoted to explicit historical compatibility metadata
- RLS, editor/owner Workbench policies and audit coverage

## Seed quantitative audit

A read-only audit of all 38 historical outcomes was completed before migration.

Only one seed outcome contained a quantitative estimate:

```text
source                 rt-2026-007
outcome                overall post-training working memory
metric                 Hedges_g
estimate               0.191
CI lower               0.062
CI upper               0.32
```

The audit found:

```text
compatibility_metric_rows              1
compatibility_effect_estimate_rows     1
compatibility_ci_rows                  1
outcome_json_effect_rows               1
outcome_json_ci_rows                   1
outcomes_with_any_numeric_json_scalar  1
outcomes_without_numeric_json_scalar  37
```

No other quantitative values were present in the rapid-review seed outcome JSON.

## Scientific scope correction

The lone historical Hedges' g is a pooled meta-analytic estimate from `rt-2026-007`, not a trial-level Stage 5 contrast.

Stage 6 therefore preserves it as:

```text
estimate_scope      source_level_synthesis
estimate_type       standardised_mean_difference
metric              Hedges_g
estimate_value      0.191
contrast_id         NULL
ci_lower            0.062
ci_upper            0.32
ci_level            NULL
standard_error      NULL
p_value             NULL
n_analysed          NULL
adjustment_status   not_applicable
```

This prevents a false trial contrast from being manufactured simply to satisfy the new quantitative schema.

Formal synthesis/proposition linkage for such pooled estimates is deliberately deferred to Stage 8.

## Candidate mapping verification

The Stage 6 seed manifest passed with:

```text
seed outcomes             38
partially_extracted         1
not_yet_extracted          37
first-class effects         1
source-level synthesis      1
study-contrast effects      0
arm outcome summaries       0
```

The following gates passed:

```text
stable_outcome_identity:              PASS
controlled_quantitative_semantics:    PASS
contrast_scope_integrity:             PASS
legacy_effect_conservation:           PASS
no_fabricated_quantitative_fields:    PASS
human_approval_boundary:              PASS
```

The historical Hedges' g and CI were conserved exactly:

```text
Hedges_g = 0.191
CI       = 0.062 .. 0.32
```

The seed does not state the CI level, analysed N, standard error or p value for this rapid-review row, so Stage 6 correctly leaves those fields unknown rather than inferring them.

## Database verification

After migration and replay, the Stage 6 database validator passed:

```text
STAGE 6 EFFECT ARCHITECTURE VALID
outcomes=38
status_rows=38
effects=1
arm_summaries=0
```

Status distribution:

```text
partially_extracted = 1
not_yet_extracted   = 37
```

Structural/integrity gates passed:

```text
estimate_scope_integrity:          PASS
cross_study_link_integrity:        PASS
legacy_effect_conservation:        PASS
no_fabricated_quantitative_fields: PASS
human_approval_boundary:           PASS
```

The database reported:

```text
source_level_synthesis = 1
study_contrast         = 0
agent candidates promoted = 0
```

## Missingness / extraction semantics

All 38 seed outcomes now have explicit Stage 6 quantitative extraction state.

The schema supports:

```text
not_yet_extracted
partially_extracted
reviewed_complete
reviewed_no_quantitative_estimate
not_reported
not_applicable
```

This is scientifically important because absence of a quantitative value in the rapid-review seed does not imply that the original paper reported no quantitative result.

The 37 non-numeric seed outcomes therefore remain `not_yet_extracted`, not `reviewed_no_quantitative_estimate`.

## Effect-estimate model

First-class effect estimates can now represent, where available:

```text
raw means / proportions
change scores
mean differences
standardised mean differences
odds ratios
risk ratios
hazard ratios
correlations
regression coefficients
rate ratios
other reported metrics
```

Each estimate may separately retain:

```text
estimate scope
Stage 5 contrast where scientifically applicable
standard error
confidence interval + level
p value
analysed N
adjustment status
model specification
time/model label
unit
scale direction
source-reported status
provenance / review status
```

Multiple estimates or model specifications can attach to the same outcome without overwriting one another.

## Raw arm-summary model

`arm_outcome_summary` supports future extraction of source-reported raw/descriptive information such as:

```text
n
mean
SD
SE
proportion
count
change mean
change SD
unit
```

Raw summaries remain scientifically distinct from comparative effect estimates.

No raw arm summaries were fabricated for the current seed.

## Human approval boundary

All Stage 6 seed mappings remain:

```text
mapping_source = agent_candidate
review_status  = proposed
```

Database validation confirmed:

```text
0 agent candidates promoted
```

Workbench reviewers can approve, reject or correct quantitative extraction status and individual effect estimates. Automated extraction does not self-promote quantitative evidence into approved scientific authority.

## Workbench verification

The Evidence Workbench now exposes Stage 6 quantitative review separately from the historical outcome fields.

Reviewers can inspect/govern:

```text
quantitative extraction status
effect estimate scope
Stage 5 contrast linkage
estimate type / metric
estimate value
SE / CI / CI level / p value
analysed N
adjustment status
model specification
scale direction
source-reported status
provenance / review status
raw arm summaries where present
```

The old one-effect compatibility display is explicitly labelled historical compatibility metadata rather than canonical v1.1 quantitative authority.

The Workbench production build passed after the Stage 6 quantitative reviewer and compatibility-field demotion were added.

## Deterministic replay / regression evidence

Stage 6 is integrated into the permanent local bootstrap after Stage 5 reconstruction.

Clean bootstrap automatically runs:

```text
Stage 6 candidate quantitative mapping
Stage 6 effect-architecture validation
Stage 6 seed-mapping validation
```

and finished with:

```text
LOCAL REGISTRY BASELINE PASS
```

The Stage 6 replay output confirmed:

```text
outcomes       38
effects         1
arm_summaries   0
```

while preserving the historical Registry/Gateway baseline and Stages 1–5 invariants.

## Supabase advisor gate

The final Stage 6 closure workflow included the local Supabase advisor gate before the final implementation commit. No blocking correctness or security issue was reported; remaining observations were non-blocking performance/maintenance notices of the same class previously recorded for the small freshly rebuilt seed database.

## Compatibility decision

- The immutable `2026-08-23` release remains unchanged.
- Historical `evidence_outcome` effect fields remain recoverable as compatibility metadata.
- The lone historical Hedges' g is preserved losslessly.
- No unsupported CI level, N, SE, p value or trial contrast is invented.
- Stage 6 structures are additive.
- `csi-evidence-v1` remains unchanged.
- No production Supabase mutation was required for Stage 6 verification.
- AI/agent quantitative mappings remain candidate-only until human review.

## Next stage

Proceed to **Stage 7 — quality appraisal at the correct scientific unit**.

Stage 7 should separate:

```text
study/reporting quality
result/outcome-specific risk of bias
body-of-evidence certainty
implementation/fidelity assessment
```

and prevent source-level `quality_assessment` records from standing in for result-level RoB or body-level GRADE.
