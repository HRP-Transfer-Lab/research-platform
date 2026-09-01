# Stage 12 Q1 — rt-2026-001 RoB 2 evidence extraction

**Status:** PROVISIONAL HUMAN-REVIEW MATERIAL — NOT AN APPROVED RoB JUDGEMENT  
**Date:** 1 September 2026  
**Framework:** RoB 2, parallel-group randomized trial, 22 August 2019  
**Source:** `rt-2026-001` — SPECTRA episodic-specificity training versus ASSO active control

## Result scope

The Registry currently carries three decision-relevant post-intervention outcomes for this study:

- free recall;
- spatial recognition;
- social problem solving.

Stage 5 contrast: `spectra_vs_asso`.

The same randomization, intervention-deviation and missing-data structure applies across these three reported post-intervention outcomes unless outcome-specific evidence shows otherwise. Outcome-measurement and selective-reporting judgements remain result-specific.

## Source material reviewed

- full 2026 Memory article;
- ClinicalTrials.gov registration `NCT06110234` as described in the report and public registry mirrors;
- published CONSORT flow information;
- published transparency/open-science statement;
- article-reported OSF materials/data record `CWTFP`.

The report states that the study design and analysis plan were preregistered and that data, code and materials are open. A final selective-reporting judgement should still compare the preserved preregistration/materials against the exact reported analysis where possible.

## Domain 1 — bias arising from the randomization process

### Evidence

- 54 participants randomized.
- Independent research-team member, not involved in other study aspects, generated assignment.
- Randomization tool used with blocks of four.
- Group-allocation correspondence sheet accessible only to the two intervention providers.
- Recruitment and assessment staff were blinded to assignment.
- Participants were blinded to whether their memory-training condition was the active comparator.
- Reported baseline characteristics showed no material group imbalance.

### Provisional judgement

`low`

### Rationale

The sequence-generation and allocation process are explicitly described and separated from recruitment/assessment, with no evidence of baseline imbalance suggesting a randomization problem.

## Domain 2 — bias due to deviations from intended interventions

### Evidence

- Participants were blinded to training condition purpose.
- Intervention providers necessarily knew the delivered program.
- Both programs had matched six-session training structures and psychoeducational framing.
- Four make-up sessions were provided within the same week for unexpected scheduling conflicts.
- No source-supported evidence of systematic cross-over, contamination or trial-context deviations affecting outcomes.
- Statistical analyses were conducted blinded to training and induction labels.

### Provisional judgement

`low`

### Rationale

For an effect-of-assignment interpretation, the report provides no indication that deviations caused by the trial context materially compromised the randomized comparison. Post-randomization absence of outcome data is handled under Domain 3 rather than being converted automatically into a Domain 2 penalty.

## Domain 3 — bias due to missing outcome data

### Evidence

- 54 randomized; 51 analysed.
- All three losses occurred in the SPECTRA arm.
- Two withdrew before intervention: one for health reasons and one for lack of availability.
- One withdrew after one session because of lack of motivation.
- The remaining 51 completed the reported intervention/outcome pathway and were analysed.
- The report does not establish outcome values for the three randomized participants who were not analysed.

### Provisional judgement

`some_concerns`

### Rationale

Overall missingness is small (3/54), but it is differential by randomized arm and one reason — lack of motivation after exposure to SPECTRA — could plausibly relate to intervention experience. A sensitivity analysis demonstrating robustness to the missing outcomes was not identified in the material reviewed. This should not be labelled high risk on the available evidence, but an automatic low-risk judgement would be too strong.

## Domain 4 — bias in measurement of the outcome

### Evidence

- Recruitment/assessment researchers were blinded to assigned intervention.
- Participants were blinded to which training program was the active comparator.
- Assessments used standardized programmed tasks with distinct pre/post materials and counterbalancing.
- Free recall and problem-solving verbal output were recorded and scored according to defined procedures; recognition used programmed performance measures.
- No evidence was identified that outcome measurement differed systematically between randomized groups.

### Provisional judgement

`low`

### Rationale

Outcome assessment procedures were standardized and the assessment team was blinded to randomized assignment. The social-problem-solving and recall outcomes involve scoring of recorded verbal output, but the available report does not indicate differential measurement by arm.

## Domain 5 — bias in selection of the reported result

### Evidence

- Trial registered as `NCT06110234`.
- Report states design and analysis plan were preregistered.
- Article states all data exclusions, manipulations and measures are reported.
- Data, code and materials are reported as openly available via OSF.
- The article reports the three major behavioral outcome families represented in the Registry.
- Reported analysis involved model comparison/model selection among nested mixed models, and non-significant order-of-induction models were not reported in detail.

### Provisional judgement

`some_concerns_pending_preregistration_comparison`

### Rationale

Prospective registration and open materials reduce selective-reporting risk substantially, but a final low-risk judgement requires direct comparison of the preserved analysis plan with the exact model-selection/reporting procedure. Until that comparison is completed, the existence of multiple eligible mixed-model specifications means low risk should not be assumed solely from the registration badge.

## Provisional overall RoB 2 pattern

```text
D1 randomization process                 low
D2 deviations from intended intervention low
D3 missing outcome data                  some concerns
D4 measurement of outcome                low
D5 selection of reported result          some concerns pending prereg comparison
```

**Provisional overall:** `some_concerns`

This is an appraisal candidate for human scientific review, not an approved Registry value.

## Required close-out before Registry approval

1. Compare `NCT06110234` / preserved preregistration materials with the exact reported behavioral analysis specification, especially model-selection rules and outcome/timepoint definitions.
2. Confirm whether any outcome-specific scoring information changes Domain 4 for free recall or social problem solving.
3. If no additional evidence changes Domains 3 or 5, retain overall `some_concerns` for the three current post-intervention Registry outcomes.

## Governance

- Do not mutate release `2026-08-23`.
- Do not mutate `csi-evidence-v1`.
- This document does not change `study_quality_status` or `result_rob_status`.
- No Stage 7 assessment/domain row is approved by this extraction.
