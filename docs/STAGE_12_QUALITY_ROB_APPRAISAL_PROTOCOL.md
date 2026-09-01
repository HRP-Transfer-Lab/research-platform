# Evidence Registry v1.1 — Stage 12 Formal Quality / Risk-of-Bias Appraisal Protocol

**Status:** READY FOR APPRAISAL  
**Date:** 1 September 2026  
**Branch:** `evidence-registry-v1.1`

## Purpose

Close the remaining formal quality / risk-of-bias scientific gate for the 18-source seed without fabricating judgements from design labels or rapid-review summaries.

The governing invariant remains:

```text
STUDY / REPORT QUALITY
!=
RESULT-SPECIFIC RISK OF BIAS
!=
BODY-OF-EVIDENCE CERTAINTY
!=
IMPLEMENTATION / FIDELITY
!=
EML
```

The immutable `2026-08-23` release and `csi-evidence-v1` Gateway remain unchanged during appraisal.

## 1. Release-ready completion rule

Every normalized Stage 7 subject must finish in a human-reviewed terminal state:

```text
study_quality_status
  reviewed_complete
  OR
  not_applicable + explicit rationale

result_rob_status
  reviewed_complete
  OR
  not_applicable + explicit rationale
```

A `reviewed_complete` subject requires at least one approved, reviewed-complete typed assessment and at least one approved domain judgement.

The following remain release blockers:

```text
not_yet_assessed
assessment_in_progress
partially_assessed
insufficient_information
agent_candidate / proposed appraisal rows
```

`not_applicable` is not a shortcut. It must be human-reviewed, approved and justified.

The strict read-only gate is:

```text
python3 components/evidence-registry/scripts/audit_stage12_quality_rob_gate.py
```

## 2. Source-material rule

The rapid route-review record is sufficient for framework routing and appraisal planning, but **not** for a final RoB / methodological-quality judgement.

Final appraisal should use, where available:

```text
full article / report
supplementary methods and appendices
trial registration or protocol
prespecified statistical analysis plan
relevant parent-trial report for secondary analyses
review protocol / registration for evidence syntheses
```

If the information needed for a defensible judgement cannot be recovered, the assessment remains `insufficient_information` and the release gate stays open.

## 3. Framework baseline and version lock

Use the framework that matches the scientific subject rather than the publication label.

### Randomized trial results

```text
RoB 2
baseline version: 22 August 2019
cluster-randomized variant: 18 March 2021 where applicable
crossover variant: 18 March 2021 where applicable
```

RoB 2 is result / estimand specific. A judgement should identify the outcome, contrast and result/timepoint scope being assessed.

### Non-randomized intervention results

For v1.1 use the established:

```text
ROBINS-I 2016
```

The November 2025 ROBINS-I V2 release remains a draft subject to change and is not the default v1.1 baseline. A later registry version may add it explicitly.

### Non-randomized exposure results

```text
ROBINS-E
version: 24 March 2024
```

Do not substitute ROBINS-I merely because an exposure study is observational.

### Systematic review methodology

Where scientifically appropriate:

```text
AMSTAR 2 — 2017
ROBIS — review risk of bias
```

AMSTAR 2 is not an overall numeric score. Overall confidence follows critical-domain logic.

### Reporting completeness

Reporting guidance remains separate from methodological quality / RoB:

```text
CONSORT 2025
PRISMA 2020
PRISMA-ScR 2018
```

Reporting completeness may supplement but must not replace result-specific RoB.

### Measurement quality

```text
COSMIN — version appropriate to the measurement question; v1.1 registry baseline 2018
```

Use only where its subject matter is scientifically applicable.

### No suitable registered external framework

Use `custom` only when a standard registered framework is not scientifically appropriate. The assessment must explicitly document:

```text
scope
reason standard tool is unsuitable
domains used
judgement vocabulary
source material reviewed
limitations of the custom appraisal
```

A bespoke appraisal must not be presented as if it were a validated external RoB instrument.

## 4. Result granularity

One normalized outcome does not necessarily equal one RoB judgement.

Create separate `result_risk_of_bias_assessment` rows where risk may differ by:

```text
contrast
estimand
timepoint
measurement
analysis/model
```

For example, a normalized outcome carrying both post-intervention and delayed follow-up evidence may require separate appraisal keys when missing-data or measurement risk differs across timepoints.

Source-level synthesis estimates from Stage 6 must not be forced into trial-level RoB. Review methodology belongs at study/review level; body-level certainty belongs to Stage 8.

## 5. Seed appraisal routing worklist

The routes below are **framework-routing recommendations only**, not quality/RoB judgements.

| Source | Design / role | Initial appraisal route |
|---|---|---|
| rt-2026-001 | Randomized active-control trial | RoB 2 for decision-relevant trial results; study-level reporting appraisal optional/separate |
| rt-2026-002 | Randomized three-group longitudinal training study | RoB 2; delayed result assessed separately if risk differs |
| rt-2026-003 | Secondary analysis integrating three randomized intervention studies | Full-text resolution first; use RoB 2 only if the result retains a clear randomized-assignment estimand and required parent-trial information is available; otherwise explicit custom secondary-analysis appraisal |
| rt-2026-004 | Randomized three-group experimental training study | RoB 2 |
| rt-2026-005 | Randomized active-control longitudinal trial | RoB 2; distinguish post and 3-month result scopes where required |
| rt-2026-006 | Randomized 2×2 factorial controlled trial | RoB 2 for the relevant factorial contrasts/results |
| rt-2026-007 | Systematic review + robust-variance meta-analysis of RCTs | Study/review appraisal with AMSTAR 2 and/or ROBIS; normalized review outcomes are not trial-result RoB subjects; body certainty later in Stage 8 |
| rt-2026-008 | PRISMA-ScR / COSMIN-informed scoping review | PRISMA-ScR reporting appraisal; measurement/review methodology assessed only with a scientifically appropriate COSMIN/custom scope; review findings are not trial-result RoB subjects |
| rt-2026-009 | Within-participant mechanistic graph-learning + fMRI study | Full-text framework resolution; do not force RoB 2 unless a randomized causal result is actually being assessed; otherwise explicit custom methodological/result appraisal or justified result-RoB `not_applicable` |
| rt-2026-010 | Secondary analysis of prior perceptual-learning data | Custom secondary-analysis / observational-result appraisal unless a standard exposure framework is demonstrably appropriate |
| rt-2026-011 | Behavioral retrieval-practice + fMRI mechanism experiment | Full-text framework resolution; RoB 2 only for a genuine randomized causal result; otherwise custom appraisal / justified result-RoB `not_applicable` |
| rt-2026-012 | Acute-stress experimental fMRI study | Confirm allocation from full text; RoB 2 if randomized, otherwise appropriate non-randomized/custom result appraisal |
| rt-2026-013 | Three controlled JOL experiments | Confirm allocation from full text; RoB 2 if randomized, otherwise custom result appraisal |
| rt-2026-014 | Large randomized factorial field experiment | RoB 2; assess decision-relevant factorial contrasts and delayed result separately where necessary |
| rt-2026-015 | Eight-week quasi-experimental classroom intervention | ROBINS-I 2016 for intervention-effect results |
| rt-2026-016 | Preregistered large-scale behavioral human–AI experiment | Confirm random allocation from full text; RoB 2 if randomized, otherwise custom/non-randomized appraisal as justified |
| rt-2026-017 | Between-subjects AI-writing experiment | Confirm random allocation from full text; RoB 2 if randomized, otherwise custom/non-randomized appraisal as justified |
| rt-2026-018 | Three-wave observational AI-offloading exposure study | ROBINS-E 2024 for the exposure-result question; preserve non-causal interpretation |

## 6. Appraisal batches

To keep scientific review manageable and auditable, appraise in four batches.

### Q1 — straightforward randomized intervention evidence

```text
rt-2026-001
rt-2026-002
rt-2026-004
rt-2026-005
rt-2026-006
rt-2026-014
```

Primary framework: RoB 2.

### Q2 — non-randomized / human–AI intervention and exposure evidence

```text
rt-2026-015
rt-2026-016
rt-2026-017
rt-2026-018
```

Primary frameworks: ROBINS-I / ROBINS-E / RoB 2 where randomization is confirmed.

### Q3 — systematic / scoping review evidence

```text
rt-2026-007
rt-2026-008
```

Primary frameworks: AMSTAR 2 / ROBIS / PRISMA-ScR / justified measurement appraisal.

### Q4 — secondary-analysis and mechanism evidence

```text
rt-2026-003
rt-2026-009
rt-2026-010
rt-2026-011
rt-2026-012
rt-2026-013
```

Framework applicability must be resolved from the full methods before assessment. Do not force an intervention RoB instrument onto a mechanism or associative result.

## 7. AI and human authority

AI may:

```text
locate source material
pre-extract signalling-question evidence
suggest framework applicability
prepare candidate domain judgements with citations/source basis
flag missing or contradictory information
```

AI must not self-approve:

```text
framework selection
domain judgement
overall judgement
terminal assessment status
not_applicable rationale
```

The final approved scientific state requires human adjudication/authority consistent with Stage 11.

## 8. Appraisal record requirements

Every formal assessment should record at minimum:

```text
framework key + exact version
assessment key
scientific subject / result scope
source material reviewed
domain judgements
supporting basis for each domain
overall judgement where the framework defines one
limitations / unresolved information
assessor / date
human review status
```

Do not copy long copyrighted tool text into the Registry. Store concise domain identifiers/judgements and source-grounded rationale.

## 9. Completion and Stage 8 handoff

The quality/RoB phase is closed only when:

```text
18/18 study_quality_status terminal + human approved
38/38 result_rob_status terminal + human approved
0 reviewed_complete subjects without approved assessments
0 completed assessments without approved domain evidence
0 unreviewed agent appraisal candidates
strict quality/RoB gate PASS
historical release unchanged
CSI Gateway unchanged
```

Only then proceed to the bounded Stage 8 proposition/synthesis proof and later deterministic release-build/parity work.

No new evidence release is published during this phase.
