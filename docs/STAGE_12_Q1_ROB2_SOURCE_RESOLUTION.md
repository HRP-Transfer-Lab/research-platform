# Stage 12 Q1 RoB 2 source-resolution record

**Status:** SOURCE RESOLUTION IN PROGRESS  
**Date:** 1 September 2026  
**Branch:** `evidence-registry-v1.1`

## Purpose

Resolve whether the six Q1 randomized sources have enough recoverable source material for defensible result-specific RoB 2 appraisal before any risk-of-bias judgement is created.

Rapid Registry seed summaries are not sufficient by themselves for final RoB 2 appraisal.

## Q1 sources

### rt-2026-001 — SPECTRA episodic-specificity training

**Resolution:** READY FOR FULL RoB 2 EXTRACTION.

Recoverable material includes:

- full journal article;
- supplementary material;
- ClinicalTrials.gov registration `NCT06110234`;
- OSF open-data/materials record `CWTFP`;
- published report explicitly describes a double-blind randomized two-arm study;
- 54 randomized; 51 analysed after three withdrawals from the SPECTRA arm;
- article states that the design and analysis plan were preregistered.

Final appraisal must compare the relevant result scope against the preregistration and assess missing-result-data implications of the three post-randomization withdrawals rather than treating the small amount of attrition as automatically low risk.

### rt-2026-002 — executive-function training and prospective memory

**Resolution:** READY FOR FULL RoB 2 EXTRACTION, WITH REPORTING LIMITATIONS TO RESOLVE.

Recoverable material includes an open full accepted-manuscript PDF. The report states:

- 93 participants randomly allocated equally to CT, BT and control;
- all 93 included in the primary analyses after multiple imputation;
- post-training and six-month follow-up result scopes;
- a priori power analysis and explicit eligibility/exclusion process.

The currently resolved material does not yet establish a trial-registration / prespecified-analysis-plan record or enough information to assume allocation concealment or outcome-assessor blinding. Those fields must remain unresolved unless supported by the full report or linked registration/materials.

### rt-2026-004 — relational-frame training

**Resolution:** FULL TEXT REQUIRED BEFORE FINAL RoB 2.

The publisher preview establishes:

- N=119;
- random assignment to standard relational training, enhanced relational training and yoked control;
- baseline group comparability;
- downstream analogical-transfer outcomes.

However the currently recoverable publisher material is preview/abstract-level rather than the complete methods/report. This is insufficient for defensible judgements on allocation concealment, deviations from intended intervention, missing outcome data, outcome measurement and selective reporting.

Do not create a final RoB 2 judgement until the full article and any supplementary/preregistration material are available.

### rt-2026-005 — video-game executive-function training

**Resolution:** FULL TEXT REQUIRED BEFORE FINAL RoB 2.

The publisher preview establishes:

- randomized active-control design;
- 70 younger and 70 older adults;
- custom cognitive-game training versus perceptual-matched gameplay-video observation;
- post-training and three-month follow-up outcomes.

The preview is insufficient for final RoB 2 domain judgements. Full methods, attrition/missing-data handling, outcome-assessor procedures and prespecified analysis/reporting information are required.

### rt-2026-006 — Baduanjin plus cognitive training

**Resolution:** READY FOR FULL RoB 2 EXTRACTION.

The full open-access Frontiers report establishes:

- 2 x 2 randomized controlled factorial design;
- 162 randomized using computer-generated random numbers;
- blinded outcome assessors and separate intervention/assessment staff;
- 138 completed;
- dropout reasons reported as voluntary withdrawal, loss to follow-up or health-related reasons;
- baseline and immediate post-intervention outcome assessment;
- factorial main-effect, interaction and simple-effect analyses.

Final appraisal must still assess whether missing outcome data and analysis/reporting choices could bias each result scope; design labels and blinded assessment alone do not determine the overall judgement.

### rt-2026-014 — AI tutoring x mastery field experiment

**Resolution:** READY FOR FULL RoB 2 EXTRACTION, CONDITIONAL ON FULL WORKING PAPER / REGISTRY DETAIL.

Recoverable public records establish:

- randomized field experiment with >6,000 middle-school students;
- factorial assignment to AI vs CAL-only, mastery vs non-mastery, and math topic;
- delayed assessment one week later;
- AEA RCT Registry entry `AEARCTR-0018678`;
- NBER Working Paper 35621 / SSRN record.

The trial registry materially strengthens selective-reporting resolution, but final RoB 2 appraisal should use the full working paper and registry record to establish randomization details, missing delayed-assessment data, prespecified outcomes/analyses and any analysis exclusions.

## Q1 source-resolution conclusion

Current source-material state:

```text
READY FOR FULL RoB 2 EXTRACTION
  rt-2026-001
  rt-2026-002
  rt-2026-006
  rt-2026-014

FULL TEXT REQUIRED
  rt-2026-004
  rt-2026-005
```

No source is assigned a final risk-of-bias judgement by this document.

The next scientific step is to create governed, result-specific RoB 2 candidate assessments for the four source-resolved studies while leaving `rt-2026-004` and `rt-2026-005` explicitly unresolved until full source material is obtained.

## Governance

- Do not mutate release `2026-08-23`.
- Do not mutate `csi-evidence-v1`.
- Candidate appraisal != human approval.
- RoB 2 applies to a specific randomized-trial result/estimand, not the paper in the abstract.
- Missing source material must remain explicit rather than being converted into a favourable judgement.
