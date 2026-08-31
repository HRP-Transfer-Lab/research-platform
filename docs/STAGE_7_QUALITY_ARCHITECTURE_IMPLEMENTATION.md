# Evidence Registry v1.1 — Stage 7 Quality and Risk-of-Bias Architecture

**Status:** IN PROGRESS  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`

## Goal

Replace the current source-linked `quality_assessment` compatibility model with a scientifically typed quality architecture in which methodological/reporting appraisal, result-specific risk of bias, body-level certainty and implementation/fidelity are not collapsed into one generic assessment object.

The governing distinction is:

```text
STUDY / REPORT
    ↓
study methodological / reporting assessment

OUTCOME × CONTRAST / RESULT
    ↓
result-specific risk of bias

PROPOSITION / SYNTHESIS OUTCOME
    ↓
body-level certainty (Stage 8 subject)

INTERVENTION DELIVERY
    ↓
fidelity / implementation assessment (expanded in Stage 10)
```

The central invariant is:

> **Study/reporting quality != result-specific risk of bias != body-level certainty != implementation/fidelity.**

Stage 7 is additive first. Historical `quality_assessment` rows remain compatibility/audit records. No quality or certainty judgement is generated merely because a study exists.

---

## 1. Why Stage 7 is necessary

The current compatibility table is source-linked:

```text
quality_assessment
  source_id
  assessment_level
  tool
  judgement
  notes
```

and the current Workbench form permits broad levels such as:

```text
study
outcome
reporting
body_of_evidence
```

while still attaching the row to `source_id`.

This is scientifically unsafe for v1.1 because:

- RoB 2 concerns a specific result/estimand, not a paper in the abstract;
- ROBINS-I likewise concerns a result/causal effect and its bias domains;
- reporting completeness is not the same construct as risk of bias;
- TIDieR-style intervention reporting is not a study RoB judgement;
- GRADE is a body-of-evidence certainty framework and must not be attached to a single source;
- different outcomes/contrasts within one study may have different risk-of-bias judgements;
- a study can be well reported yet still have important bias risks, or vice versa.

---

## 2. Stage 7 scope boundary

Stage 7 will implement the quality subjects that already exist in the Registry:

```text
study
outcome / contrast / effect estimate
intervention component
```

Stage 8 will create the correct body-level subjects:

```text
evidence proposition
synthesis outcome
```

Therefore Stage 7 must **not** create or approve a GRADE/body-certainty record against a source or generic study merely to satisfy the schema.

Instead:

```text
body-level certainty
→ explicitly reserved / deferred to Stage 8
```

The Stage 7 architecture should make this impossible to confuse with source/study appraisal.

---

## 3. Compatibility decision

Retain the historical table:

```text
quality_assessment
```

as compatibility metadata.

Do not use it as v1.1 scientific authority after Stage 7.

Do not delete or rewrite historical rows if any are later present.

The immutable `2026-08-23` release and `csi-evidence-v1` remain unchanged.

---

## 4. Assessment framework registry

Create a controlled framework registry such as:

```text
assessment_framework_definition
```

Minimum fields:

```text
framework_key
label
framework_family
subject_kind
version_label nullable
publisher_or_owner nullable
description
active
created_at
```

Initial subject kinds:

```text
study_methodological_quality
study_reporting_completeness
result_risk_of_bias
component_reporting_or_fidelity
body_certainty_reserved
custom
```

The framework registry identifies what a tool is for. It does **not** assign the tool to a study automatically.

Candidate built-in framework definitions may include, where appropriate:

```text
rob2
robins_i
robis
amstar2
tidier
consort
prisma
cosmin
custom
```

No tool should be treated as universally appropriate.

GRADE may be registered only as:

```text
subject_kind = body_certainty_reserved
```

and Stage 7 must not provide a source/study/result write path that can use it as if it were study quality.

---

## 5. Study methodological / reporting assessments

Create a first-class typed table such as:

```text
study_quality_assessment
```

Minimum fields:

```text
study_quality_assessment_id
study_id
assessment_kind
framework_key
framework_version nullable
overall_judgement nullable
assessment_status
notes nullable
assessor nullable
assessed_on nullable
mapping_source
review_status
created_at
updated_at
```

Initial `assessment_kind`:

```text
methodological_quality
reporting_completeness
review_methodology
measurement_quality
other
```

This table is not the home for result-specific RoB 2/ROBINS-I judgements unless a framework genuinely operates at study/report level.

### Explicit study-level assessment state

Every seed study should have explicit quality-review state in a companion status layer, for example:

```text
study_quality_status
```

with values such as:

```text
not_yet_assessed
assessment_in_progress
partially_assessed
reviewed_complete
not_applicable
```

No assessment row must be generated simply to populate the status table.

---

## 6. Result-specific risk of bias

Create:

```text
result_risk_of_bias_assessment
```

A result-level RoB assessment should attach to the scientific result represented by:

```text
outcome_id
+ contrast_id nullable
+ effect_estimate_id nullable
```

Minimum fields:

```text
result_rob_assessment_id
outcome_id
contrast_id nullable
effect_estimate_id nullable
framework_key
framework_version nullable
estimand_or_result_scope nullable
overall_judgement nullable
assessment_status
notes nullable
assessor nullable
assessed_on nullable
mapping_source
review_status
created_at
updated_at
```

Rules:

1. `outcome_id` is required.
2. If `contrast_id` is present, it must belong to the same study as the outcome.
3. If `effect_estimate_id` is present, it must belong to the same outcome and be compatible with the selected contrast.
4. A source-level synthesis estimate from Stage 6 must not be forced into a trial-level RoB 2 subject.
5. The same study may legitimately have different RoB assessments for different outcomes/contrasts.

### Explicit result-level RoB state

Create per-outcome/result assessment state sufficient to distinguish:

```text
not_yet_assessed
assessment_in_progress
partially_assessed
reviewed_complete
not_applicable
```

The 38 seed outcomes should therefore not rely on the absence of RoB rows to communicate status.

---

## 7. Domain-level judgements

Quality tools frequently contain multiple domains.

Support child rows such as:

```text
assessment_domain_judgement
```

A domain judgement should retain:

```text
assessment_subject_type
assessment_id
domain_key
domain_label
judgement
supporting_text nullable
notes nullable
order_index nullable
mapping_source
review_status
```

Do not hard-code one global judgement vocabulary across all frameworks. RoB 2, ROBINS-I, AMSTAR 2 and reporting checklists use different semantics.

Where practical, framework-specific judgement definitions may be registered separately.

---

## 8. Result-level tool semantics

### RoB 2

RoB 2 should be treated as result-specific and estimand-aware.

A Stage 7 record should be able to retain whether the assessment concerns, for example:

```text
effect of assignment to intervention
effect of adhering to intervention
other prespecified result scope
```

without assuming the same judgement applies to every result in the trial.

### ROBINS-I

ROBINS-I should likewise be attachable to the relevant non-randomized result rather than to a paper as a whole.

### Reviews / meta-analyses

Review-level methodology/risk tools such as ROBIS/AMSTAR 2 belong to the review study/report subject, not to each included trial represented only indirectly by the review source.

### Measurement evidence

Measurement-focused sources may use justified frameworks such as COSMIN without forcing their appraisal into intervention RoB semantics.

---

## 9. Reporting completeness is separate

Reporting frameworks/checklists such as:

```text
TIDieR
CONSORT
PRISMA
```

should be represented as reporting-completeness assessments, not as direct substitutes for risk of bias.

A TIDieR-complete intervention description does not imply low RoB.

A poorly reported study does not automatically imply that every result is high RoB without tool-specific justification.

---

## 10. Component fidelity / implementation boundary

Stage 7 should keep implementation/fidelity conceptually separate from study/result quality.

Where necessary, allow a component-linked assessment subject or reserved status layer so that Stage 10 can later expand:

```text
fidelity
adherence
provider competence
implementation burden
protocol deviation
prompt dependence
```

Do not turn implementation/fidelity into a generic study-quality score.

---

## 11. Body-level certainty boundary

GRADE answers a body-level certainty question.

Stage 7 must enforce:

```text
GRADE != source quality
GRADE != one study's RoB
GRADE != one effect estimate's precision
```

Because the correct Stage 8 `evidence_proposition` / `synthesis_outcome` subjects do not yet exist, body-certainty records should remain structurally reserved rather than attached to the wrong object.

Stage 8 will add the actual body-level certainty table/reference and may reuse the framework registry created here.

---

## 12. Missingness and non-assessment states

Stage 7 must distinguish:

```text
not_yet_assessed
assessment_in_progress
partially_assessed
reviewed_complete
not_applicable
```

and, where useful:

```text
framework_not_selected
insufficient_information
```

`no assessment row` is not a scientific conclusion.

`not_yet_assessed` is not the same as low risk of bias.

---

## 13. Stable replay identity

The historical importer recreates numeric study/outcome IDs.

Seed status backfill should therefore resolve studies by:

```text
source_id
```

and outcomes using the Stage 4 stable key:

```text
source_id
+ outcome_name
+ legacy_rung
+ raw_timepoint
```

Stage 7 seed backfill should contain **status only** unless the immutable seed already contains a formal quality assessment.

No RoB/quality judgement should be inferred from study design labels alone.

---

## 14. Human approval boundary

As in Stages 3–6:

```text
AI / agent
→ may suggest framework applicability or pre-extract domains
→ mapping_source = agent_candidate
→ review_status = proposed
```

Only human review may approve:

```text
framework selection
domain judgements
overall risk-of-bias judgement
methodological-quality judgement
reporting-completeness judgement
```

An agent must never infer `low risk` or `high quality` simply from a design string such as `randomized`.

---

## 15. Conservative seed backfill

Before migration, audit:

```text
quality_assessment row count
assessment-level distribution
tool distribution
study-design distribution
evidence-role distribution
existing synthesis rows
existing effect/result structures
```

The expected seed principle is:

```text
if formal quality rows = 0
→ create status rows only
→ do not manufacture tool assignments or judgements
```

All 18 studies and all 38 outcomes should end Stage 7 with explicit assessment state.

---

## 16. Workbench requirements

Replace the current generic source-level quality form with typed sections:

```text
STUDY / REPORT QUALITY
RESULT RISK OF BIAS
BODY CERTAINTY — deferred to Stage 8
IMPLEMENTATION / FIDELITY — separate / Stage 10 expansion
```

For study/report quality show:

```text
assessment kind
framework
framework version
judgement/status
notes
provenance/review status
```

For result RoB show:

```text
outcome
contrast / effect estimate where applicable
framework
estimand/result scope
domain judgements
overall judgement
provenance/review status
```

The historical source-linked `quality_assessment` rows should be displayed only as compatibility metadata once Stage 7 is active.

Do not offer GRADE as a source/study/outcome form option.

---

## 17. Validation targets

Minimum structural checks:

```text
18 seed studies
→ 18 explicit study-quality status rows

38 seed outcomes
→ 38 explicit result-RoB status rows

legacy quality rows conserved                 PASS
orphan study assessments                       0
orphan result assessments                      0
cross-study outcome/contrast links              0
cross-outcome effect links                      0
GRADE attached to source/study/result            0
agent candidates approved                       0
```

Seed-specific expectation if the audit confirms no formal quality rows:

```text
study assessment judgements = 0
result RoB judgements       = 0
all status rows             = not_yet_assessed
```

Regression gates:

```text
Stage 1–6 validators PASS
historical Registry validator PASS
CSI Gateway validator PASS
clean bootstrap PASS
Workbench build PASS
Supabase advisor gate PASS
```

---

## 18. Stage 7 implementation sequence

1. Audit current `quality_assessment`, study designs, evidence roles and existing synthesis/result structures.
2. Confirm whether the seed contains any formal quality/RoB judgements.
3. Lock typed assessment subjects and framework semantics.
4. Generate additive Stage 7 migration.
5. Add framework registry, study-quality status, result-RoB status and typed assessment tables.
6. Add cross-study/result integrity guards.
7. Add RLS, grants and audit coverage.
8. Create conservative Stage 7 seed status manifest using stable identities.
9. Add replayable Stage 7 mapper and validators.
10. Integrate Stage 7 into permanent bootstrap.
11. Replace generic Workbench source-level quality form with typed study/report and result-RoB review surfaces.
12. Demote historical `quality_assessment` to compatibility metadata.
13. Clean reset + deterministic replay.
14. Run Stage 1–7 regressions, Registry/Gateway checks, Workbench build and Supabase advisors.
15. Record Stage 7 verification evidence and mark canonical tracker VERIFIED.

---

## Exit criteria

Stage 7 is VERIFIED only when:

- study/reporting appraisal and result-specific RoB are separate first-class subjects;
- result RoB can target outcome + contrast/effect where scientifically applicable;
- reporting completeness cannot masquerade as RoB;
- GRADE cannot be attached to a source, study or result;
- body-level certainty is explicitly reserved for Stage 8 proposition/synthesis-outcome subjects;
- all 18 seed studies and 38 seed outcomes have explicit quality/RoB assessment state;
- no seed quality judgement is fabricated where none was formally reviewed;
- AI/agent quality extraction remains human-review gated;
- clean bootstrap deterministically reconstructs Stage 7 status/assessment state;
- the `2026-08-23` release and `csi-evidence-v1` remain unchanged; and
- all Stage 1–6 invariants continue to pass.
