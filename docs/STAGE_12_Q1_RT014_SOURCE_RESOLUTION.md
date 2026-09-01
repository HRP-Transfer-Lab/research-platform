# Stage 12 Q1 — rt-2026-014 Source Resolution

**Status:** FULL-TEXT HOLD RESOLVED — READY FOR DETAILED RoB 2 EXTRACTION  
**Date:** 1 September 2026  
**Branch:** `evidence-registry-v1.1`

## Source

`rt-2026-014` — *Making AI Tutoring Productive: Evidence from a Mastery-Based Math Practice Experiment* (Oreopoulos, Liut, Sungu & Low, 2026).

Identifiers / versions represented in the Registry work:

- EdWorkingPaper 26-1552, DOI `10.26300/01qv-6c22`;
- AEA RCT Registry `AEARCTR-0018678`;
- full August 2026 EdWorkingPaper supplied by the user on 1 September 2026.

## Resolution

The earlier source-resolution hold was created because only public summaries/headline material were available during the first appraisal pass. That hold is now superseded.

The user supplied the complete 73-page August 2026 working-paper PDF. The full report includes the main methods, results and online appendix material needed to perform a detailed RoB 2 extraction.

The paper establishes, among other things:

```text
individual randomization at initial registration
independent topic × AI × mastery randomization
2 × 2 × 2 factorial design
teachers/students unaware of assignment in advance
explicit intent-to-treat regression specification
week-1 analysis sample: 6,997
week-2 delayed-test sample: 6,327
baseline-balance tables
progression/attrition information
multiple robustness analyses
AEA RCT Registry trial AEARCTR-0018678
```

The delayed-test analysis is restricted to students taking the week-2 assessment, with missing item responses coded incorrect among delayed-test takers. The paper also explicitly notes that treatment changes progression/exposure and treats post-mistake analyses as mechanism evidence rather than the primary causal learning estimate.

## Remaining appraisal task

Source acquisition is no longer the blocker. The remaining work is scientific appraisal:

1. map the paper's randomization/implementation evidence to RoB 2 Domain 1;
2. distinguish the week-1 process result from the delayed-test result, especially where conditioning on post-randomization mistakes/exposure affects interpretation;
3. assess delayed-test missingness/selection using the 6,997 → 6,327 participation structure and balance/robustness information;
4. compare the paper's registered hypotheses/outcomes/analysis choices with the available AEA registry information for Domain 5;
5. create agent-candidate Stage 7 assessments only after that extraction is complete;
6. route the candidate through the standard deterministic review packet and human authority process.

The full paper does not by itself imply `low` RoB. It removes the access/completeness barrier that previously prevented a defensible appraisal.

## Acquisition-state consequence

The Stage 12 source-acquisition seed now records:

```text
access_status        fulltext_available
access_route         user_supplied
fulltext_available   true
fulltext_verified    false
page_count           73
```

`fulltext_verified=false` is intentional until a locally persisted copy on the ingestion host is SHA-256 hashed and registered. The PDF itself is not stored in Git.

## Governance

- Source acquisition remains separate from scientific quality/RoB authority.
- No `rt-2026-014` Stage 7 appraisal is approved by this source-resolution update.
- The immutable `2026-08-23` release remains unchanged.
- `csi-evidence-v1` remains unchanged.
