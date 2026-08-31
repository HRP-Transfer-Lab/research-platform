# Evidence Registry v1.1 — Stage 8 Propositions, Synthesis Outcomes, Body Certainty and Claims

**Status:** IN PROGRESS  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`

## Goal

Give body-level evidence maturity, GRADE/body certainty and approved claims the correct scientific subject.

The governing hierarchy is:

```text
EVIDENCE PROPOSITION
  ↓
RESULT / SOURCE CONTRIBUTIONS
  ↓
EVIDENCE SYNTHESIS
  ↓
SYNTHESIS OUTCOME
  ├── pooled / narrative result
  ├── body-level certainty (e.g. GRADE)
  └── body-level EML
  ↓
APPROVED CLAIM
```

The central invariant is:

> **Source contribution != evidence proposition != synthesis outcome != body certainty != body-level EML != approved claim.**

Stage 8 is additive first. The historical `evidence_synthesis`, `synthesis_source` and `approved_claim` tables remain compatibility surfaces unless explicitly migrated into the v1.1 authority model.

---

## 1. Why Stage 8 is necessary

The current seed architecture contains source-level evidence records and provisional source-contribution EML ratings, but no reviewed body-level proposition object.

The legacy synthesis model is too coarse:

```text
evidence_synthesis
  pico_or_question
  conclusion
  certainty_framework
  certainty_judgement

synthesis_source
  synthesis_id
  source_id

approved_claim
  synthesis_id
  claim_text
  certainty_judgement
```

This cannot safely represent:

```text
one source contributing differently to several propositions
one synthesis producing different conclusions for different outcomes
one proposition containing supportive, null, harmful or boundary-condition results
result-level inclusion rather than paper-level inclusion only
GRADE at a specific synthesis outcome
body-level EML at a specific proposition/synthesis outcome
claims whose scope is narrower than the source paper or synthesis as a whole
```

---

## 2. Proposition as the body-level scientific question

Create a first-class `evidence_proposition`.

A proposition should specify enough scope to identify what is actually being evaluated without prematurely forcing Stage 9 population/context normalization.

Minimum fields:

```text
proposition_id
proposition_key
label
intervention_or_exposure
comparator_scope
population_scope
context_scope
target_or_outcome_scope
timeframe_scope
route_scope nullable
proposition_text
status
mapping_source
review_status
created_at
updated_at
```

`proposition_text` is the human-readable scientific statement/question.

Stage 9 may later replace or augment free-text population/context facets with normalized identifiers. Stage 8 should not block on that later ontology work.

---

## 3. Contributions to a proposition

Create a result-aware contribution layer such as:

```text
proposition_evidence_contribution
```

A contribution may identify:

```text
source_version_id or source_id compatibility identity
study_id nullable
outcome_id nullable
contrast_id nullable
effect_estimate_id nullable
```

At minimum, Stage 8 must support both:

```text
source-level synthesis/review contribution
result-level primary-study contribution
```

Fields should include:

```text
contribution_id
proposition_id
source_id
study_id nullable
outcome_id nullable
contrast_id nullable
effect_estimate_id nullable
contribution_role
result_direction nullable
inclusion_status
inclusion_reason
mapping_source
review_status
created_at
updated_at
```

Controlled contribution roles should support at least:

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
other
```

A contribution role is not a quality judgement and does not determine certainty by itself.

---

## 4. Contribution integrity

The contribution layer must enforce:

```text
if outcome_id is present:
  outcome.study_id == study_id (or study_id can be resolved from outcome)

if contrast_id is present:
  contrast.study_id == outcome.study_id

if effect_estimate_id is present:
  effect.outcome_id == outcome_id
  effect.contrast_id matches contrast_id where applicable
```

A source-level synthesis estimate such as the Stage 6 pooled Hedges g must remain representable without manufacturing a Stage 5 contrast.

One source may contribute more than once to one proposition only when the contributions identify scientifically distinct results/roles.

---

## 5. Evidence synthesis

The v1.1 authority should create a typed synthesis object rather than rely on the legacy generic row.

Recommended table:

```text
body_evidence_synthesis
```

Minimum fields:

```text
body_synthesis_id
synthesis_key
proposition_id
title
synthesis_kind
method_summary
search_or_selection_basis nullable
status
version
mapping_source
review_status
created_at
updated_at
```

Controlled synthesis kinds:

```text
systematic_review_meta_analysis
systematic_review_narrative
rapid_review
scoping_review
structured_internal_synthesis
living_synthesis
other
```

A synthesis is the process/body assembly; it is not itself the outcome-specific conclusion.

---

## 6. Synthesis outcome

Create:

```text
synthesis_outcome
```

This is the core Stage 8 scientific subject.

Minimum fields:

```text
synthesis_outcome_id
body_synthesis_id
proposition_id
outcome_key
outcome_label
conclusion_direction
conclusion_summary
estimate_type nullable
metric nullable
pooled_estimate nullable
standard_error nullable
ci_level nullable
ci_lower nullable
ci_upper nullable
p_value nullable
heterogeneity_metric nullable
heterogeneity_value nullable
included_study_count nullable
included_result_count nullable
status
mapping_source
review_status
created_at
updated_at
```

A synthesis can legitimately contain several synthesis outcomes with different:

```text
conclusions
pooled effects
heterogeneity
certainty
EML
```

Therefore body certainty and EML must not attach only to `body_synthesis_id` if the interpretation is outcome-specific.

---

## 7. Body-level certainty / GRADE

Stage 7 registered:

```text
grade → subject_kind = body_certainty_reserved
```

Stage 8 now creates the legitimate body-certainty subject.

Create:

```text
body_certainty_assessment
```

Minimum fields:

```text
body_certainty_assessment_id
synthesis_outcome_id
framework_key
framework_version nullable
certainty_judgement
assessment_status
basis
assessor nullable
assessed_on nullable
mapping_source
review_status
created_at
updated_at
```

For GRADE, controlled overall judgements should support:

```text
high
moderate
low
very_low
```

Do not infer GRADE certainty from:

```text
study design alone
RoB alone
statistical significance
EML
number of studies alone
```

Domain-level certainty judgements may later be added using a typed child table if needed. The minimum Stage 8 requirement is that GRADE can only attach to `synthesis_outcome`.

---

## 8. Body-level EML

The existing EML 0–7 definitions remain authoritative:

```text
0 rationale
1 mechanism/paradigm support
2 initial direct demonstration
3 replicated efficacy
4 convergent body
5 transfer & durability
6 real-world effectiveness
7 generalised / scale-ready
```

Stage 8 must create body-level EML at the proposition/synthesis-outcome level, not derive it from the maximum source-level EML.

Preferred approach:

- retain historical `evidence_maturity_assessment` source rows as `record_contribution` compatibility/state;
- add an explicit `synthesis_outcome_id` subject to the maturity architecture, or create a typed body-level maturity table if altering the historical polymorphic table would be unsafe;
- enforce `scope = body_of_evidence` for synthesis-outcome maturity;
- retain basis, assessor, status and scale version;
- do not auto-promote a candidate body EML from source-level contributions.

### EML3 replication rule

Body-level EML3 requires proposition-level evidence of replicated direct effect, not merely two records with EML2 labels.

The body assessment must be able to record:

```text
number of direct contributing studies
independence / replication relationship
consistency/direction pattern
unresolved contradictions/boundaries
```

### EML4+

EML4 requires a reviewed convergent multi-study body/synthesis.

EML5 requires cumulative transfer and/or durability evidence relevant to the proposition.

EML6 requires authentic/routine-setting effectiveness evidence.

EML7 requires generalisation/scale evidence plus implementation/boundary/harms/cost considerations. Stage 10 will strengthen the structured inputs for these higher levels.

---

## 9. Approved claims

Create a typed v1.1 claim table such as:

```text
body_approved_claim
```

Minimum fields:

```text
body_claim_id
claim_key
proposition_id
synthesis_outcome_id
product nullable
claim_text
required_caveat nullable
population_scope
context_scope nullable
route_scope nullable
certainty_summary nullable
status
version
mapping_source
review_status
created_at
updated_at
```

Allowed lifecycle:

```text
draft
reviewing
approved_internal
approved_public
retired
```

Rules:

- approved claims must reference a reviewed proposition and synthesis outcome;
- a claim cannot be broader than the proposition scope without an explicit reviewed override process;
- certainty text is a projection/summary, not a substitute for the linked `body_certainty_assessment`;
- body-level EML is a maturity dimension, not claim strength or effect direction;
- agent candidates cannot self-promote to approved claims.

---

## 10. Legacy compatibility boundary

Historical tables remain:

```text
evidence_synthesis
synthesis_source
approved_claim
```

Stage 8 should make them read-only to authenticated Workbench users once the typed v1.1 surfaces are active.

The existing seed contains no synthesis or approved-claim rows, so the conservative Stage 8 seed backfill should not manufacture any.

The immutable `2026-08-23` release remains unchanged.

`csi-evidence-v1` remains unchanged until a deliberate future Gateway publication/version decision.

---

## 11. Seed backfill boundary

Audit before migration:

```text
legacy evidence_synthesis rows
legacy synthesis_source rows
legacy approved_claim rows
source-level EML assessments
Stage 6 source-level synthesis effects
study/result contribution candidates
```

Expected seed principle:

```text
if synthesis/claim rows = 0:
  create no proposition, synthesis, certainty, body EML or claim judgement automatically
```

Stage 8 may create explicit programme-level status rows such as:

```text
proposition_backfill_status = not_yet_curated
```

but must not infer proposition definitions from source titles or product relevance merely to populate the database.

---

## 12. Human approval boundary

AI may propose:

```text
candidate proposition text
candidate result contributions
candidate synthesis inclusion/exclusion
candidate synthesis summaries
candidate GRADE domain evidence
candidate EML basis
candidate claim wording
```

but all remain:

```text
mapping_source = agent_candidate
review_status = proposed
```

Only human review may approve:

```text
proposition scope
contribution inclusion
synthesis outcome conclusion
GRADE/body certainty
body-level EML
approved claim
```

No agent-generated claim may enter `approved_internal` or `approved_public` without human review.

---

## 13. Workbench requirements

Add a body-level evidence workspace showing:

```text
PROPOSITION
  scope + review state

CONTRIBUTIONS
  source/result identity
  role/direction
  inclusion status
  RoB/quality linkage where available

SYNTHESIS
  synthesis method/version

SYNTHESIS OUTCOME
  conclusion + quantitative result where available

BODY CERTAINTY
  GRADE or other body-level framework

BODY EML
  maturity 0–7 + basis

APPROVED CLAIM
  claim text + caveat + lifecycle
```

The Workbench should visibly state:

```text
GRADE != EML
certainty != effect magnitude
effect direction != maturity
source EML != body EML
```

---

## 14. Validation targets

Minimum structural gates:

```text
legacy synthesis rows conserved
legacy synthesis-source rows conserved
legacy approved claims conserved

orphan propositions                         0
orphan contributions                        0
cross-study contribution links              0
cross-outcome effect links                   0
orphan synthesis outcomes                    0
certainty without synthesis outcome          0
GRADE on source/study/result                 0
body EML without body subject                0
approved claim without reviewed body subject 0
agent candidates self-approved               0
```

Seed-specific expectation if audit confirms no body-level rows:

```text
propositions             0
body syntheses            0
synthesis outcomes        0
body certainty            0
body-level EML            0
approved body claims      0
```

Regression gates:

```text
Stages 1–7 validators PASS
historical Registry validator PASS
CSI Gateway validator PASS
clean bootstrap PASS
Workbench build PASS
Supabase advisor gate PASS
```

---

## 15. Stage 8 implementation sequence

1. Audit legacy synthesis/source/claim tables and body-level EML state.
2. Confirm Stage 6 source-level synthesis estimates that must remain representable.
3. Lock proposition and contribution semantics.
4. Create typed proposition, contribution, body synthesis and synthesis-outcome schema.
5. Create synthesis-outcome body certainty with GRADE-only-on-body enforcement.
6. Create body-level EML subject architecture and replication-rule checks.
7. Create typed approved-claim lifecycle.
8. Make legacy synthesis/claim write paths compatibility-only.
9. Add RLS, grants and audit coverage.
10. Add conservative zero-judgement seed/status manifest and validator.
11. Add replay/bootstrap integration.
12. Add Workbench body-evidence reviewer.
13. Clean reset + deterministic replay.
14. Run Stages 1–8 regressions, Workbench build and Supabase advisors.
15. Record Stage 8 verification and mark the canonical tracker VERIFIED.

---

## Exit criteria

Stage 8 is VERIFIED only when:

- propositions are first-class scientific objects;
- sources/results can contribute differently to multiple propositions;
- syntheses can contain multiple outcome-specific conclusions;
- GRADE/body certainty attaches only to synthesis outcomes;
- body-level EML is proposition/synthesis-outcome specific and not derived from the highest source EML;
- EML3 replication logic can be evaluated at proposition level;
- approved claims reference reviewed body-level subjects;
- legacy synthesis/claim surfaces cannot bypass the typed v1.1 model;
- the seed does not fabricate body-level judgements;
- AI/agent body-level outputs remain human-review gated;
- deterministic replay and Stage 1–7 regressions pass;
- the immutable `2026-08-23` release and `csi-evidence-v1` remain unchanged.
