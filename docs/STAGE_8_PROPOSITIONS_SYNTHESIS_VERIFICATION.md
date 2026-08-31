# Evidence Registry v1.1 — Stage 8 Propositions, Synthesis Outcomes, Body Certainty and Claims Verification

**Stage:** 8 — Evidence propositions, body synthesis, synthesis outcomes, GRADE/body certainty, body-level EML and governed claims  
**Status:** VERIFIED  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`  
**Implementation commit:** `e0ee2777adfee090142c5c11e6689a33e8425a34`  
**Migrations:** `20260831211000_evidence_registry_v1_1_body_evidence_architecture.sql`; `20260831211010_tighten_stage8_body_maturity_guards.sql`; `20260831211100_evidence_registry_v1_1_body_compatibility_readonly.sql`

## Decision

Stage 8 is verified.

The Registry now has a first-class body-level evidence architecture in which scientific propositions, evidence contributions, synthesis outcomes, body certainty, body maturity and approved claims are separate governed objects.

```text
EVIDENCE PROPOSITION
        ↓
SOURCE / RESULT CONTRIBUTIONS
        ↓
BODY EVIDENCE SYNTHESIS
        ↓
SYNTHESIS OUTCOME
   ├── conclusion / pooled result
   ├── body certainty (e.g. GRADE)
   └── body-level EML
        ↓
GOVERNED BODY CLAIM
```

The governing invariant is:

> **Source contribution != proposition != synthesis outcome != body certainty != body-level EML != approved claim.**

This prevents source-level maturity, statistical significance, effect direction or one paper's quality from being treated as body-level scientific authority.

## Implemented

Stage 8 adds:

- `body_evidence_stage8_status`
- `evidence_proposition`
- `proposition_evidence_contribution`
- `body_evidence_synthesis`
- `synthesis_outcome`
- `body_certainty_assessment`
- `body_maturity_assessment`
- `body_approved_claim`
- result/source contribution integrity guards
- proposition/synthesis-outcome consistency guards
- GRADE/body-certainty subject guards
- body-EML replication and approval guards
- governed claim approval guards
- agent self-approval prevention across all Stage 8 authority objects
- RLS, Workbench editor/owner policies and audit coverage
- legacy `evidence_synthesis`, `synthesis_source` and `approved_claim` compatibility surfaces made read-only to authenticated Workbench users
- conservative zero-body seed manifest
- zero-body seed validator
- replayable Stage 8 curation-status helper
- Stage 8 database architecture validator
- permanent Stage 8 integration in `bootstrap_local_registry.py`
- Workbench Stage 8 body-evidence review surface

## Proposition and contribution model

A proposition defines the body-level scientific question/claim scope independently from any one publication.

It can retain:

```text
intervention / exposure
comparator
population
context
target / outcome
timeframe
route scope
proposition text
```

Evidence contributions can then identify source- or result-specific support using, where available:

```text
source_version
source compatibility identity
study
outcome
contrast
effect estimate
```

with explicit contribution roles such as:

```text
direct_support
direct_null
direct_harm
boundary_condition
mechanism_support
measurement_support
implementation_support
synthesis_support
contradictory
contextual
```

A source may therefore contribute differently to several propositions, and several distinct results from one source may be represented without collapsing them into a paper-level vote.

## Contribution integrity

Database guards enforce the scientific identity chain.

Verified rules include:

```text
outcome.study == contribution study
contrast.study == result study
effect.outcome == contribution outcome
effect contrast matches contribution contrast where applicable
```

The Stage 6 source-level pooled Hedges' g remains representable without manufacturing a Stage 5 trial contrast.

## Synthesis and synthesis-outcome separation

`body_evidence_synthesis` represents the synthesis process/body assembly.

`synthesis_outcome` represents an outcome-specific conclusion within that body.

A single synthesis can therefore contain several synthesis outcomes with different:

```text
conclusion directions
pooled estimates
uncertainty
heterogeneity
certainty
body-level EML
```

This corrects the legacy model in which one synthesis row had to carry one generic conclusion/certainty value for the entire body.

## GRADE / body-certainty boundary

Stage 7 registered GRADE as:

```text
framework_key = grade
subject_kind  = body_certainty_reserved
```

Stage 8 now provides the legitimate write subject: `synthesis_outcome`.

Verified:

```text
GRADE on source/study/result subjects = 0
GRADE may attach only through body_certainty_assessment -> synthesis_outcome
```

For GRADE, the Stage 8 guard restricts the overall certainty judgement to:

```text
high
moderate
low
very_low
```

No GRADE value is inferred from randomisation, RoB, significance, EML or number of studies.

## Body-level EML boundary

Stage 8 uses a dedicated `body_maturity_assessment` keyed to `synthesis_outcome`.

This deliberately leaves the historical `evidence_maturity_assessment` source rows untouched.

Verified source maturity baseline:

```text
record-contribution EML rows = 18
EML distribution             = 1:7 / 2:10 / 4:1
legacy body-level EML rows   = 0
```

Thus:

```text
source EML != body EML
```

and body EML is not computed as the maximum EML among contributing sources.

## EML3 replication guard

Body-level EML3+ requires proposition-level replication evidence rather than simply counting source EML2 records.

The database guard requires at least:

```text
direct_study_count >= 2
genuine_replication_count >= 1
explicit replication_basis
consistency_pattern = consistent OR mixed_but_convergent
```

Independent-replication count cannot exceed genuine-replication count.

Approval of a body-maturity row also requires an approved synthesis outcome and approved body synthesis. Approved EML4+ additionally requires a multi-study synthesis outcome.

This preserves the tightened HRP EML3 rule established earlier in the v1.1 programme.

## Claim governance

`body_approved_claim` provides a typed claim lifecycle:

```text
draft
reviewing
approved_internal
approved_public
retired
```

A claim entering an approved lifecycle state must reference:

```text
an approved proposition
+
an approved synthesis outcome
+
a human-approved review state
```

Agent candidates cannot self-promote to approved claims.

Certainty summaries remain projections of linked body-certainty evidence rather than substitutes for the underlying certainty assessment.

## Zero-body seed boundary

The immutable `2026-08-23` seed contains no curated body-level proposition, synthesis, certainty, maturity or approved claim.

The Stage 8 seed manifest therefore intentionally creates no scientific body object.

Verified seed state:

```text
propositions          0
contributions         0
body syntheses        0
synthesis outcomes    0
body certainty        0
body EML              0
body claims           0
```

The singleton curation state is:

```text
seed_body_curation | not_yet_curated | migration | proposed
```

This is an explicit workflow state, not a negative scientific conclusion.

## Historical body compatibility

The legacy tables remain intact:

```text
evidence_synthesis
synthesis_source
approved_claim
```

The seed contains zero rows in all three.

Authenticated Workbench privileges are read-only:

```text
approved_claim     SELECT only
evidence_synthesis SELECT only
synthesis_source   SELECT only
```

This prevents the old coarse model from bypassing the typed Stage 8 authority layer.

## Source-level pooled-effect conservation

The lone quantitative source-level synthesis value remains exactly conserved:

```text
source       rt-2026-007
outcome      overall post-training working memory
scope        source_level_synthesis
metric       Hedges_g
estimate     0.191
CI           0.062 to 0.32
contrast     NULL
```

It remains available for later reviewed proposition/synthesis curation without being silently promoted into a body-level conclusion.

## Human-approval boundary

Stage 8 prevents `agent_candidate` rows from self-promoting to `review_status = approved` across:

```text
evidence propositions
contributions
body syntheses
synthesis outcomes
body certainty
body EML
body claims
```

Local validation confirmed:

```text
0 agent candidates promoted
```

## Workbench verification

The Evidence Workbench now exposes Stage 8 as a cross-source body-evidence layer.

For a selected source, reviewers can see body-level propositions to which that source contributes while proposition/synthesis objects remain globally reusable.

The Workbench exposes the conceptual chain:

```text
PROPOSITION
CONTRIBUTIONS
SYNTHESIS
SYNTHESIS OUTCOME
BODY CERTAINTY
BODY EML
APPROVED CLAIM
```

and visibly preserves the distinctions:

```text
GRADE != EML
certainty != effect magnitude
effect direction != maturity
source EML != body EML
```

The Workbench production build passed after the Stage 8 reviewer was added.

## Deterministic replay / regression evidence

Stage 8 is integrated into `bootstrap_local_registry.py` after Stage 7.

The full local bootstrap restores the immutable seed and Stages 1–8, then runs:

```text
Stage 8 zero-body curation replay
Stage 8 body-evidence architecture validator
Stage 8 zero-body seed validator
```

before reporting:

```text
LOCAL REGISTRY BASELINE PASS
```

Historical baseline remains intact:

```text
Registry sources              18
Registry studies              18
Intervention components       13
Evidence outcomes             38
Source EML assessments        18
CSI Gateway releases           1
CSI Gateway evidence cards    18
CSI Gateway claims             0
Gateway cards with EML        18
```

The immutable `2026-08-23` release and `csi-evidence-v1` contract remain unchanged.

## Database validation

The Stage 8 database validator passed with:

```text
STAGE 8 BODY EVIDENCE ARCHITECTURE VALID
propositions=0
contributions=0
body_syntheses=0
synthesis_outcomes=0
body_certainty=0
body_eml=0
body_claims=0
```

and:

```text
body_curation_status: PASS
legacy_body_compatibility: PASS
source_eml_boundary: PASS
source_level_synthesis_effect_boundary: PASS
grade_subject_boundary: PASS
body_eml_subject_and_replication_guards: PASS
claim_approval_boundary: PASS
human_approval_boundary: PASS
no_fabricated_body_objects_or_judgements: PASS
```

## Supabase advisor gate

The final local Supabase advisor gate completed successfully with no blocking correctness or security findings. Remaining observations were non-blocking `INFO / PERFORMANCE` items consistent with the fresh small seed database and are maintenance/optimisation concerns rather than Stage 8 scientific or structural failures.

## Compatibility decision

- `2026-08-23` remains immutable.
- `csi-evidence-v1` remains unchanged.
- Existing source-contribution EML remains untouched.
- Legacy synthesis/claim tables remain recoverable but read-only to Workbench users.
- No proposition, GRADE rating, body EML or approved claim was manufactured from the seed.
- The source-level pooled Hedges' g remains conserved without a fabricated contrast.
- AI/agent body-level outputs remain human-review gated.

## Next stage

Proceed to **Stage 9 — normalise population, context and application lenses**.
