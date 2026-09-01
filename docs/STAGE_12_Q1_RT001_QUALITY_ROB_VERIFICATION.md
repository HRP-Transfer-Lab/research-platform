# Stage 12 Q1 — rt-2026-001 Quality / RoB Pilot Verification

**Status:** VERIFIED HUMAN-AUTHORITATIVE PILOT  
**Date:** 1 September 2026  
**Branch:** `evidence-registry-v1.1`

## Decision

The `rt-2026-001` Stage 7 appraisal pilot successfully completed the governed path:

```text
source evidence review
→ agent_candidate/proposed appraisal rows
→ deterministic 28-decision review packet
→ packet + scientific-decision hash validation
→ explicit human approval
→ Stage 11 adjudication / active authority
→ strict Stage 12 quality/RoB gate verification
```

No historical release or CSI Gateway object was mutated.

## Approved scientific appraisal

Study-level custom methodological appraisal:

`methodologically_adequate_with_documented_limitations`

Result-specific RoB 2 overall judgement for each current post-intervention result:

- free recall — `some_concerns`
- spatial recognition — `some_concerns`
- social problem solving — `some_concerns`

Common RoB 2 pattern:

```text
D1 randomization process                  low
D2 deviations from intended intervention  low
D3 missing outcome data                   some_concerns
D4 measurement of outcome                 low
D5 selection of reported result           some_concerns
```

Domain 3 concern reflects differential post-randomization loss from SPECTRA, including one withdrawal after exposure for lack of motivation.

Domain 5 concern reflects the fact that the public trial record prespecified the behavioural outcome families, PRE/POST timing and expected SPECTRA-specific pattern, while the detailed mixed-model/model-selection specification was not preserved in that registry and the record was first submitted after the recorded study start.

## Strict gate after approval

```text
study_quality_status
  reviewed_complete 1
  not_yet_assessed  17

result_rob_status
  reviewed_complete 3
  not_yet_assessed  35

study_quality_assessments 1
result_rob_assessments    3
domain_judgements        20
```

Governance defect metrics all remained zero:

```text
closed_study_status_without_human_authority                 0
closed_result_status_without_human_authority                0
reviewed_complete_study_without_approved_assessment         0
reviewed_complete_result_without_approved_assessment        0
completed_study_assessment_without_approved_domain          0
completed_result_assessment_without_approved_domain         0
study_not_applicable_without_rationale                      0
result_not_applicable_without_rationale                     0
```

The overall Stage 12 quality/RoB gate correctly remains OPEN solely because the other 17 study subjects and 35 result subjects have not yet reached terminal human-reviewed states.

## Reuse decision

The pilot establishes the review pattern for later source batches. Candidate application is being generalized to a manifest-driven loader; each source still receives a source-specific scientific appraisal and explicit human approval packet.
