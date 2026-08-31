# Evidence Registry v1.1 — Stage 9 Population, Context and Application Lenses

**Status:** IN PROGRESS  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`

## Goal

Enable defensible cross-domain evidence matching without collapsing distinct population and context properties into broad labels.

The governing principle is:

```text
POPULATION IDENTITY / DESCRIPTION
  != LIFE STAGE
  != ROLE
  != HEALTH / CONDITION CONTEXT
  != BASELINE COGNITIVE STATUS
  != EDUCATION LEVEL
  != STUDY SETTING
  != DELIVERY CONTEXT
  != GEOGRAPHY
  != APPLICATION / DEMAND FAMILY
  != CONTEXT FIT
```

The original author-reported `study.population_summary`, `study.population_tags`, age fields and `study.setting` remain compatibility/source-description fields. Stage 9 adds reviewed normalized facets rather than overwriting them.

---

## 1. Scientific unit

Population/context coding is primarily **study-level** because one publication may contain more than one study or population.

Stage 8 propositions retain their scoped free-text population/context fields. Stage 9 does not retrospectively manufacture proposition scope from study tags. Later proposition curation may use reviewed Stage 9 facets as evidence inputs.

Intervention-component delivery fields such as `provider`, `delivery_mode` and component `setting` remain intervention-delivery properties; Stage 9 may map them into a study/context lens but must not erase the component-level source fields.

---

## 2. Controlled facet architecture

Use a domain-general vocabulary table such as:

```text
population_context_term
```

with:

```text
term_id
facet_kind
term_key
label
description
parent_term_id nullable
active
```

Supported `facet_kind` values at minimum:

```text
life_stage
role
health_context
baseline_cognitive_status
education_level
study_setting
delivery_context
country
region
```

Do not create composite terms such as:

```text
healthy_university_students
older_workers_with_pain
```

Those are represented by combinations of independent facets.

---

## 3. Study-to-facet links

Create:

```text
study_population_context_term
```

with:

```text
study_id
term_id
assertion_status
source_text nullable
notes nullable
mapping_source
review_status
created_at
updated_at
```

`assertion_status` should support:

```text
present
mixed
unclear
not_applicable
```

Missingness/extraction state belongs in a separate study-level status row rather than being represented as a fake vocabulary term.

---

## 4. Study population/context extraction status

Create:

```text
study_population_context_status
```

one row per study, with independent extraction state for the main dimensions where useful.

Minimum overall state:

```text
not_yet_extracted
partially_extracted
reviewed_complete
not_applicable
```

The seed should begin conservatively. Candidate mappings may be proposed from explicit source text, but no candidate becomes approved without human review.

---

## 5. Life stage

Initial neutral vocabulary should support at least:

```text
child
adolescent
young_adult
adult
midlife
older_adult
mixed_life_stage
```

Life stage must not be inferred solely from a vague label if age information contradicts it. Numeric age fields remain authoritative source data where available.

A study may legitimately have more than one life-stage facet when the sample spans groups.

---

## 6. Role

Initial role vocabulary should support at least:

```text
student
worker_employee
manager_leader
educator
healthcare_professional
caregiver
retired_person
general_community_member
mixed_roles
```

Role is distinct from health status. `patient` should not be used as a substitute for a diagnosed condition; where useful it may later be represented as a service/participation role while health condition remains separately coded.

---

## 7. Health / condition context

Initial neutral vocabulary should support broad context states without pretending to encode every diagnosis in Stage 9:

```text
healthy_or_no_condition_specified
diagnosed_condition
symptom_elevated_or_subclinical
at_risk_population
rehabilitation_or_recovery
mixed_health_context
```

A separate retained text field/link note should preserve the named condition or health context where reported.

Do not infer `healthy` merely because no diagnosis appears in a short study summary. If the source is silent, leave the facet unassigned and retain `not_yet_extracted`/`unclear` state.

---

## 8. Baseline cognitive status

Support at least:

```text
typical_or_unselected
selected_low_baseline
selected_high_baseline
cognitive_impairment_or_decline
mixed_baseline_status
```

This dimension is only assigned when selection or baseline status is actually reported or defensibly extracted.

---

## 9. Education level

Support at least:

```text
primary_school
secondary_school
further_education
undergraduate
postgraduate
adult_or_continuing_education
mixed_education_levels
not_education_bound
```

`student` is a role; `undergraduate` is an education level. They must remain separate.

---

## 10. Study setting

Support at least:

```text
laboratory
university_or_higher_education
school
workplace
clinical_or_health_service
community
home
online_or_remote
field_or_real_world
mixed_setting
```

Setting is not automatically equivalent to application family. A laboratory study may inform workplace performance but remains a laboratory study.

---

## 11. Delivery context

Support at least:

```text
in_person
remote_synchronous
remote_asynchronous
digital_self_guided
blended
provider_led
self_administered
mixed_delivery
```

Delivery context can be linked to study-level evidence while preserving more detailed component-level `delivery_mode`, `provider`, protocol and setting fields.

---

## 12. Geography

Where explicitly reported, preserve:

```text
country
region/subnational context
multicountry
```

Use stable country keys (preferably ISO-style keys) where feasible. Do not infer country from author affiliation unless the study location itself is established.

---

## 13. Application / demand family boundary

Stage 3 already provides the separate application-family lens:

```text
mental_fitness
performance
learning
executive_functioning
wellbeing
longevity
condition_related_support
```

Stage 9 must not duplicate these as population/context facets.

Example:

```text
ROLE: worker_employee
SETTING: workplace
APPLICATION FAMILY: performance + wellbeing
```

These are separate facts and may vary independently.

---

## 14. Context fit and boundary metadata

Add an explicit reviewed matching/boundary layer, preferably proposition-aware where possible, such as:

```text
context_fit_assessment
```

Minimum fields:

```text
context_fit_assessment_id
proposition_id nullable
contribution_id nullable
study_id
fit_dimension
fit_judgement
basis
mapping_source
review_status
```

Controlled fit dimensions:

```text
population
role
health_context
education
setting
delivery
geography
overall_context
```

Controlled fit judgements:

```text
direct_match
close_match
partial_match
boundary_condition
mismatch
insufficient_information
not_applicable
```

This is an evidence-matching judgement, not a quality/RoB/GRADE/EML judgement.

Stage 8 currently has zero curated propositions/contributions, so the immutable seed should contain zero proposition-specific fit assessments unless a human explicitly curates them.

---

## 15. Legacy compatibility and missingness

Retain read-only/source-description compatibility for:

```text
study.population_summary
study.population_tags
study.age_min
study.age_max
study.age_mean
study.setting
component.provider
component.delivery_mode
component.setting
```

Do not erase or rewrite those fields to normalized vocabulary labels.

Distinguish:

```text
not_yet_extracted
reviewed_no_mapping / unclear
not_applicable
```

from absence of a facet link.

---

## 16. Seed backfill principle

Audit all 18 studies first.

Candidate mappings are acceptable only where supported by explicit seed text/structured fields. They must remain:

```text
mapping_source = agent_candidate
review_status = proposed
```

Do not fabricate precise age/life-stage, health, role, geography or delivery classifications from weak cues.

The seed must retain all 18 studies even if several dimensions remain `not_yet_extracted`.

---

## 17. Workbench

Add a Stage 9 Population & Context review section showing:

```text
AUTHOR-REPORTED POPULATION
  summary / tags / age

NORMALIZED FACETS
  life stage
  role
  health context
  baseline cognitive status
  education level
  setting
  delivery context
  geography

APPLICATION FAMILY
  shown separately from Stage 3

CONTEXT FIT / BOUNDARIES
  only where a proposition/contribution subject exists
```

The UI should make explicit that:

```text
role != health status
life stage != age number
setting != application family
absence of a tag != evidence of absence
context fit != study quality
```

---

## 18. Validation targets

Minimum structural gates:

```text
studies                                      18
study population/context status rows         18
orphan facet links                            0
wrong-facet vocabulary links                  0
duplicate study/term links                    0
agent candidates self-approved                0
legacy population summaries conserved        18
```

Semantic gates:

```text
no composite population terms
role separated from health context
student separated from education level
setting separated from application family
health not inferred from silence
geography not inferred from affiliation alone
context fit not treated as RoB/GRADE/EML
```

Regression gates:

```text
Stages 1–8 validators PASS
historical Registry validator PASS
CSI Gateway validator PASS
clean bootstrap PASS
Workbench build PASS
Supabase advisor gate PASS
```

The immutable `2026-08-23` release and `csi-evidence-v1` remain unchanged.

---

## 19. Implementation sequence

1. Audit current population summaries/tags, age, study setting and component delivery fields.
2. Lock controlled facet vocabulary and missingness semantics.
3. Create population/context term and study-link schema.
4. Add per-study extraction status.
5. Add proposition/contribution-aware context-fit architecture without fabricating seed fit rows.
6. Create conservative candidate seed mappings only from explicit evidence.
7. Add validators for ontology, identity, missingness and human-review boundaries.
8. Add replay/bootstrap integration.
9. Add Workbench Stage 9 reviewer.
10. Clean reset + deterministic replay.
11. Run Stage 1–9 regressions, build and advisors.
12. Record verification and mark Stage 9 VERIFIED.

---

## Exit criteria

Stage 9 is VERIFIED only when:

- population/context dimensions are orthogonal and queryable;
- original author-reported population/setting text is retained;
- `healthy university students` cannot collapse to a single generic `adult` label;
- role, health status, life stage, education and setting are not conflated;
- application family remains a separate Stage 3 lens;
- context-fit/boundary judgements have an explicit subject and cannot masquerade as quality/certainty/maturity;
- missingness is explicit;
- agent candidates remain human-review gated;
- deterministic replay and Stage 1–8 regressions pass;
- the immutable release and CSI Gateway contract remain unchanged.
