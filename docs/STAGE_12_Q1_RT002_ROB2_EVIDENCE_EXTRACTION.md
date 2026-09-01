# Stage 12 Q1 — rt-2026-002 RoB 2 evidence extraction

**Status:** PROVISIONAL HUMAN-REVIEW MATERIAL — NOT AN APPROVED RoB JUDGEMENT  
**Date:** 1 September 2026  
**Framework:** RoB 2, parallel-group randomized trial, 22 August 2019  
**Source:** `rt-2026-002` — executive-function training and prospective memory in children with learning difficulties

## Result scope

The Registry currently carries two decision-relevant prospective-memory outcomes:

- prospective memory, post-training;
- prospective memory, six-month follow-up.

The normalized Stage 5 seed has the three randomized arms but no approved contrast because the rapid-review seed did not establish a sufficiently safe contrast. The full article now clarifies CT, BT and control groups, but this quality appraisal does not silently rewrite approved Stage 5 structure. Result-specific RoB can therefore remain outcome-scoped with `contrast_id = NULL` until a separately governed Stage 5 enrichment is made.

## Source material reviewed

- full 2026 BMC Psychology accepted manuscript / article-in-press PDF;
- published methods, analysis, participant-flow and outcome sections;
- ethics and data-availability statements.

No trial registration or prospective analysis-plan identifier was located in the full article.

## Domain 1 — bias arising from the randomization process

### Evidence

- 96 children were initially recruited; three were excluded before randomization.
- The remaining 93 were described as randomly allocated to CT, BT and control, 31 per group.
- The report does not describe the random-sequence generation method or allocation-concealment mechanism.
- No clear evidence of a problematic baseline imbalance was identified in the material reviewed.

### Provisional judgement

`some_concerns`

### Rationale

Random allocation is stated, but the absence of sequence-generation and concealment detail prevents a low-risk judgement.

## Domain 2 — bias due to deviations from intended interventions

### Evidence

- CT and BT were delivered as distinct six-week training programmes; control received no corresponding training programme.
- Pre-, post- and follow-up research assistants were not involved in intervention execution and were blinded to group assignment.
- Primary data analysts were also blinded to group assignment/intervention protocol.
- No trial-context crossover or systematic intervention contamination was identified in the report.

### Provisional judgement

`low`

### Rationale

For an effect-of-assignment interpretation, no source-supported trial-context deviations were identified that would materially compromise the randomized comparison.

## Domain 3 — bias due to missing outcome data

### Evidence

- All 93 randomized participants were retained in the primary analyses through multiple imputation.
- Little's MCAR test was significant, indicating the missingness was not consistent with MCAR.
- Twenty imputations were used under a MAR assumption; the imputation model included all dependent variables plus age, sex and IQ.
- The report does not provide a complete outcome-by-timepoint missingness table or a sensitivity analysis for departures from MAR.

### Provisional judgement

`some_concerns`

### Rationale

The authors used a transparent and substantially better-than-complete-case missing-data strategy, but the observed data reject MCAR and the identifying MAR assumption is not stress-tested. This is particularly relevant to the six-month result.

## Domain 4 — bias in measurement of the outcome

### Evidence

- PM was assessed with a standardized computerized dual-task paradigm.
- Post-training and follow-up assessments replicated the pre-training assessment procedure.
- Research assistants administering assessments were blinded to randomized group.
- Objective accuracy and response-time indices were recorded.

### Provisional judgement

`low`

### Rationale

Outcome ascertainment was standardized, objective and assessor-blinded, with no evidence of differential measurement across groups.

## Domain 5 — bias in selection of the reported result

### Evidence

- The article prospectively frames PM and EF outcomes and describes the three assessment timepoints and the planned mixed-design analysis.
- The analysis section specifies LMM fixed effects, participant random intercepts, compound-symmetry covariance, IQ covariate, Rubin pooling and Bonferroni pairwise correction.
- Multiple PM/ongoing/EF outcomes, accuracy/RT endpoints and timepoints were available for analysis.
- No trial registration or preserved prospective statistical-analysis plan was identified.

### Provisional judgement

`some_concerns`

### Rationale

The reported analysis is comparatively explicit, but without a preserved prospective protocol/SAP the possibility of selection among eligible outcomes, timepoints and model specifications cannot be ruled out.

## Provisional RoB 2 pattern

```text
D1 randomization process                  some concerns
D2 deviations from intended intervention  low
D3 missing outcome data                   some concerns
D4 measurement of outcome                 low
D5 selection of reported result           some concerns
```

**Provisional overall for both Registry PM results:** `some_concerns`

The delayed result should retain the same overall category, with Domain 3 rationale explicitly noting the greater importance of the unverified MAR assumption at six months.

## Study-level methodological appraisal

A custom study-level appraisal may be used only as a complement to the result-specific RoB 2 records. Proposed pattern:

```text
randomization documentation          minor_concern
masking / assessment separation      strong
missing-data strategy                minor_concern
outcome measurement documentation   strong
analysis / registration transparency minor_concern
```

Proposed overall study-level descriptor: `methodologically_adequate_with_documented_limitations`.

## Governance

- No quality/RoB row is approved by this extraction.
- No Stage 5 arm/contrast row is altered here.
- Do not mutate release `2026-08-23`.
- Do not mutate `csi-evidence-v1`.
