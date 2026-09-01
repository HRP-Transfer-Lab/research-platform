# Stage 12 Q1 — rt-2026-014 Source Resolution

**Status:** HOLD — FULL METHODS / SAP REQUIRED BEFORE FINAL RoB 2 APPRAISAL  
**Date:** 1 September 2026  
**Branch:** `evidence-registry-v1.1`

## Source

`rt-2026-014` — *Making AI Tutoring Productive: Evidence from a Mastery-Based Math Practice Experiment* (Oreopoulos, Liut, Sungu & Low, 2026).

Known public versions / identifiers:

- NBER Working Paper 35621, DOI `10.3386/w35621`;
- EdWorkingPaper 26-1552, DOI `10.26300/01qv-6c22`;
- AEA RCT Registry `AEARCTR-0018678`;
- public PDF URL previously identified by the literature radar: `https://edworkingpapers.com/sites/default/files/ai26-1552.pdf`.

## What is already established sufficiently for source routing

Public source material and the existing reviewed seed establish that this is a randomized factorial field experiment in Hamilton County Schools with more than 6,000 middle-school students using the NUMI computer-assisted-learning platform.

Students were randomized across:

```text
AI support vs CAL-only support
x
mastery vs non-mastery progression
x
one of two mathematics topics
```

The current Registry normalizes four recoverable AI × mastery policy cells and intentionally does not fabricate a privileged contrast where the earlier seed did not establish one.

Current normalized decision-relevant outcomes are:

```text
next-attempt correctness after mistakes
  during_platform_use

delayed practiced / unpracticed mathematics assessment
  approximately 1 week
```

Public reporting also establishes:

```text
initial analysis sample        6,997 students
delayed assessment sample      6,327 students
```

and the paper is explicitly registered as `AEARCTR-0018678`.

These facts are sufficient to retain the study in the Registry and to route it to RoB 2 once full appraisal evidence is available.

## Why final RoB 2 is not being created yet

The Stage 12 quality protocol requires final appraisal to use the full report / protocol / registration / SAP where available rather than infer risk-of-bias judgements from an abstract or rapid-review summary.

At the present review step the accessible evidence is sufficient to confirm design and headline sample/outcome structure, but not sufficient to close the following domains without guesswork:

### D1 — randomization process

Random assignment is explicit, but the currently retrievable material does not establish enough detail about:

```text
sequence generation
allocation implementation / concealment
stratification or blocking variables
whether the three factorial assignments were implemented independently as described
baseline-balance diagnostics relevant to the randomized factors
```

Do not infer `low` solely from the word `randomized`.

### D3 — missing outcome data / result availability

For the delayed assessment, 6,327 of the 6,997 initial-analysis students are reported as tested. Before judging the delayed result, recover:

```text
reason for delayed non-participation
whether missingness differs by randomized cell
analysis population used in the delayed models
any inverse-probability / imputation / sensitivity treatment
```

For the immediate post-error result, the result is conditional on reaching an attempt and making an error. Because AI changes progress and attempt behaviour, full methods are needed to determine whether the reported estimand is simply a descriptive process outcome or whether conditioning on post-randomization behaviour creates an important selection limitation for a causal assignment effect.

### D5 — selection of the reported result

AEA registration materially reduces concern, but the exact registration / SAP must be compared with:

```text
primary / secondary outcomes
factorial interactions
practiced vs unpracticed delayed outcomes
Exercise 1 vs harder / other material
multiple process outcomes
model specifications
multiplicity handling
```

The delayed AI × mastery evidence is described publicly as marginally significant and concentrated in practiced Exercise 1 material. That makes direct preregistration/SAP comparison particularly important; it must not be converted automatically into either `low` or `high` risk.

## Current decision

```text
DO NOT create a reviewed_complete Stage 7 appraisal yet.
DO NOT mark result_rob_status reviewed_complete.
DO NOT infer a RoB 2 overall judgement from the abstract / rapid review.
```

Keep the existing Stage 7 status for `rt-2026-014` as `not_yet_assessed` until the full working paper and registry/SAP details are recoverable for human review.

## Next source-resolution action

Recover and archive or otherwise make review-accessible:

1. full EdWorkingPaper / NBER working paper;
2. AEA RCT Registry entry `AEARCTR-0018678` including registered outcomes and analysis plan;
3. any online appendix / supplementary tables needed for attrition and factorial analysis.

Then apply the standard manifest-driven quality/RoB pipeline:

```text
source evidence
→ agent_candidate/proposed assessment
→ deterministic review packet
→ human approval
→ Stage 11 authority
```

## Governance

- No `rt-2026-014` quality/RoB candidate rows are created by this hold decision.
- The immutable `2026-08-23` release remains unchanged.
- `csi-evidence-v1` remains unchanged.
- Lack of current full-text access is not treated as evidence of study weakness; it is an appraisal-completeness boundary.
