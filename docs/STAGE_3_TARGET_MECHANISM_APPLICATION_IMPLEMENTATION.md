# Evidence Registry v1.1 — Stage 3 Target, Mechanism and Application Ontology

**Status:** IN PROGRESS  
**Date:** 26 August 2026  
**Branch:** `evidence-registry-v1.1`

## Goal

Build a scientifically neutral, cross-domain ontology for:

```text
DEMAND / APPLICATION FAMILY
Where might this evidence be useful?

TARGET LOCUS
At what level is change being attempted or observed?

TARGET CONSTRUCT
What process, capacity, state, policy or system property is being targeted?

MECHANISM
What causal/process pathway is proposed or tested?
```

These dimensions must remain separate from:

```text
intervention route
evidence role
outcome / transfer
population / context
product relevance
EML / RoB / GRADE
```

The governing principle is:

> **Represent the external science neutrally first; map to IQ Mindware / Trident-G / H-AGI / CSI concepts second.**

---

## 1. Demand / Application Family is a use-case lens

Initial controlled families:

```text
mental_fitness
performance
learning
executive_functioning
wellbeing
longevity
condition_related_support
```

These answer:

> **In what broad human-demand domain could this evidence be relevant?**

They do **not** specify:

- what intervention route was used;
- what cognitive/affective/physiological target changed;
- what mechanism caused an effect;
- which CSI product is validated.

A source/version may legitimately map to several application families.

Example:

```text
working-memory intervention evidence
→ executive_functioning
→ performance
→ learning
```

without changing its route or target construct.

### Database model

Create:

```text
application_family_definition
source_version_application_family
```

`source_version_application_family` should contain at minimum:

```text
source_version_id
application_family
relevance_level
rationale
mapping_source
review_status
```

Suggested `relevance_level`:

```text
primary
secondary
adjacent
```

The mapping is versioned scientific interpretation and therefore should attach to `source_version`, not to canonical publication identity.

---

## 2. Target locus

Stage 3 introduces eight high-level target-locus families:

```text
biological_or_physiological_substrate
current_operating_state
cognitive_operation
affective_or_motivational_process
knowledge_or_mental_representation
explicit_strategy_or_policy
person_niche_coupling
niche_or_activity_system
```

### Meanings

#### biological_or_physiological_substrate

Longer-lived biological or physiological capacity / operating-envelope substrates.

Examples:

```text
cardiorespiratory fitness
sleep restoration / sleep architecture
neural excitability
metabolic support
```

This locus is compatible with Develop → Condition interventions but is not synonymous with that route.

#### current_operating_state

Acute or relatively short-lived state in which existing capacities operate.

Examples:

```text
acute stress
arousal
fatigue
alertness
acute affective state
```

This locus is compatible with Regulate interventions but mechanistic state evidence must not automatically be coded as a Regulate intervention.

#### cognitive_operation

Information-processing operations or cognitive control processes.

Examples:

```text
working-memory updating
relational integration
attentional selection
response inhibition
evidence accumulation
```

#### affective_or_motivational_process

Affective, motivational or valuation processes that influence cognition/action.

Examples:

```text
threat appraisal
self-efficacy
reward valuation
avoidance motivation
emotion regulation processes
```


#### knowledge_or_mental_representation

Learned or stored knowledge, conceptual content, schemas and structured
mental representations that are distinct from the cognitive operations
acting upon them.

Examples include numerical knowledge, conceptual knowledge, abstract
relational maps and learned task representations.

This distinction prevents domain learning from being forced into
`cognitive_operation`.

#### explicit_strategy_or_policy

Explicitly available rules, heuristics, strategies, decision policies or metacognitive procedures.

Examples:

```text
implementation intention
argument-evaluation heuristic
decision threshold rule
metacognitive monitoring strategy
```

#### person_niche_coupling

The connection between person-level policy/capability and cues, opportunities, actions and feedback in a target activity.

Examples:

```text
cue-triggered strategy deployment
transfer cue recognition
policy-to-action coupling
feedback-guided real-world deployment
```

#### niche_or_activity_system

The task/work/learning/activity system itself: structure, workflow, authority, information flow, affordances, prompts, contingencies or human-AI organisation.

Examples:

```text
workflow interruption structure
AI support stage
feedback architecture
decision authority
information visibility
```

---

## 3. Target construct ontology

A target construct is more specific than target locus.

Create:

```text
target_definition
```

Minimum fields:

```text
target_id
canonical_label
target_locus
description
ontology_status
created_at
updated_at
```

Suggested `ontology_status`:

```text
provisional
reviewed
active
retired
```

### Neutral ontology rule

Target names should describe constructs represented in the scientific evidence rather than product modules.

Prefer:

```text
working_memory_updating
relational_integration
evidence_accumulation
acute_stress_state
implementation_intention
human_ai_task_allocation
```

Avoid product-specific targets such as:

```text
ccc_capacity
g_track_score
reasoning_coach_skill
```

Product/framework mappings belong in separate mapping tables.

---

## 4. Author-reported terms versus HRP normalisation

Do not erase original terminology.

Create:

```text
target_alias
```

Minimum fields:

```text
target_id
alias_text
alias_type
source_version_id nullable
```

Suggested `alias_type`:

```text
author_term
synonym
legacy_hrp_term
external_ontology_term
```

This supports the distinction:

```text
AUTHOR TERM
"working-memory capacity"
        ↓ mapped to
HRP NEUTRAL TARGET
working_memory_updating / storage_binding / etc.
```

without pretending the authors used HRP terminology.

---

## 5. Component → target mapping

Create:

```text
component_target
```

Minimum fields:

```text
component_id
target_id
relationship
rationale
mapping_source
review_status
```

Suggested `relationship`:

```text
primary_target
secondary_target
target_engagement_only
```

A component can target several constructs.

Example:

```text
structured relational training
→ relational_integration       primary_target
→ working_memory_control       secondary_target
```

### Explicit completeness state

Every intervention component must also have a target-extraction state.

Add either a dedicated one-to-one status table or a controlled field supporting:

```text
not_yet_extracted
partially_extracted
reviewed_complete
not_applicable
```

Stage 3 must not convert absence of target coding into a negative scientific statement.

---

## 6. Mechanism ontology

Mechanism is separate from target.

A target answers:

> What is being changed or engaged?

A mechanism answers:

> Through what process/pathway is the observed or hypothesised effect produced?

Create:

```text
mechanism_definition
mechanism_assertion
```

### mechanism_definition

Minimum fields:

```text
mechanism_id
canonical_label
description
mechanism_status
created_at
updated_at
```

Mechanisms should remain neutral and reusable across domains.

Examples:

```text
error_driven_updating
attentional_reweighting
stress_induced_prediction_shift
retrieval_practice_strengthening
cue_dependent_policy_activation
offloading_induced_practice_reduction
feedback_contingency_learning
```

### mechanism_assertion

Minimum fields:

```text
mechanism_assertion_id
source_version_id
mechanism_id
study_id nullable
component_id nullable
assertion_type
assertion_direction
support_summary
author_reported_text
mapping_source
review_status
```

Suggested `assertion_type`:

```text
author_proposed
hrp_candidate
experimentally_manipulated
target_engagement_supported
mediator_tested
mediator_supported
mediator_not_supported
boundary_condition
```

Suggested `assertion_direction`:

```text
supports
mixed
null
contradicts
unclear
not_applicable
```

The Registry must be able to represent mechanism **failure** or boundary evidence as naturally as positive support.

---

## 7. Mechanism assertions for non-intervention evidence

Stage 1 already allows mechanism evidence to exist without an intervention route.

Stage 3 must preserve this.

For a pure mechanism study:

```text
source_version
→ mechanism_assertion
```

is sufficient.

No synthetic `intervention_component` should be created merely to hold a mechanism.

This is critical for records such as:

```text
mechanism_evidence
state_mechanism_evidence
metacognitive_governor_evidence
```

from the historical taxonomy.

---

## 8. Framework mappings are optional second-order interpretations

Create separate mappings rather than contaminating neutral target/mechanism entities.

Preferred initial tables:

```text
target_framework_mapping
mechanism_framework_mapping
```

Minimum fields:

```text
neutral_entity_id
framework
framework_concept
mapping_relation
rationale
review_status
```

Controlled `framework` values may initially include:

```text
trident_g
apc
h_agi
csi
iqm_product_architecture
```

Suggested `mapping_relation`:

```text
exact
close
broader
narrower
related
```

Example:

```text
neutral target: relational_integration
→ H-AGI: argumentation / reasoning support          related
→ Trident-G: vertical cognitive-operation layer     related
```

This mapping must never be presented as author terminology.

---

## 9. Versioning / authority rule

Because Stage 2 introduced `source_version`, Stage 3 scientific interpretations that describe a reviewed source should preferentially attach to `source_version`.

Use:

```text
source_version_application_family
mechanism_assertion.source_version_id
```

Component-target mappings currently attach to legacy normalized `intervention_component` rows because study/component versioning has not yet been refactored. That compatibility link can be migrated later once study/result version authority is formalised.

Historical released `source_version` rows are immutable. Stage 3 annotation tables can add reviewed interpretation around them without mutating the source-version snapshot itself.

---

## 10. Seed ontology policy

Stage 3 should create a **small, controlled initial ontology**, not attempt to pre-invent hundreds of constructs before literature ingestion.

Seed only constructs clearly needed by the 18-source regression corpus plus high-level loci/families.

Principle:

> **Ontology grows from reviewed evidence, not from speculative completeness.**

A new target/mechanism can enter as `provisional`, then become `active` after review/reuse.

---

## 11. Conservative seed backfill

The 18-source corpus should be backfilled only where the reviewed record clearly supports the mapping.

Do not infer a target or mechanism merely from:

```text
product relevance
paper title alone
route alone
review bucket alone
```

Useful inputs include:

```text
author construct terminology
protocol description
study design
outcome interpretation
existing route rationale
review tags
```

### Component target completeness target

All 13 current normalized intervention components must end Stage 3 with either:

```text
≥1 reviewed/provisional target mapping
```

or explicit:

```text
not_yet_extracted
```

No silent null state.

### Mechanism records

The five current primary mechanism-role sources should support source-version-level mechanism assertions where the rapid review actually establishes a mechanism claim; otherwise they receive an explicit extraction status rather than invented mechanism coding.

---

## 12. Application-family seed mapping

Application families are intentionally broad and many-to-many.

For the seed corpus, mappings may be proposed from the reviewed evidence but should remain reviewable.

Examples of legitimate cross-family mapping:

```text
working-memory training
→ executive_functioning
→ learning
→ performance

acute stress mechanism evidence
→ performance
→ wellbeing

AI activity-system evidence
→ performance
→ learning
```

Do not map `condition_related_support` unless the population/question genuinely concerns a condition/health-related context.

---

## 13. Missingness / extraction status

Stage 3 must distinguish at least:

```text
not_yet_extracted
not_reported
not_applicable
reviewed_no_mapping
reviewed_mapped
```

For targets/mechanisms, `reviewed_no_mapping` means the reviewer has determined that this dimension does not legitimately apply or cannot be supported from the evidence available. It does not mean a null intervention effect.

---

## 14. RLS / Workbench model

All new public-schema tables require RLS.

Suggested access during Stage 3:

```text
viewer  → read ontology and mappings
editor  → review source/application, component/target and mechanism assertions
owner   → manage controlled definitions and framework mappings
```

Definitions and cross-framework ontology changes should be more restricted than ordinary evidence annotation.

No anonymous access is required.

All scientifically consequential edits should be audit logged.

---

## 15. Workbench changes

After database model exists, the Workbench should display separately:

```text
APPLICATION FAMILIES
TARGET LOCUS / TARGETS
MECHANISMS
FRAMEWORK MAPPINGS
```

Do not replace the existing source detail with one overloaded free-text field.

For intervention components:

```text
Route
Target locus
Target construct(s)
Mechanism assertion(s)
```

must remain visibly distinct.

For mechanism-only sources:

```text
Evidence role: Mechanism
Intervention route: —
Mechanism assertions: ...
```

must be a valid and normal UI state.

---

## 16. Stage 3 validation targets

Minimum structural checks:

```text
application family definitions            7
target locus definitions                  7
invalid application-family mappings       0
invalid target-locus mappings             0
invalid framework identifiers             0
orphan target mappings                    0
orphan mechanism assertions               0
```

Seed completeness checks:

```text
13 intervention components
→ all have target extraction status
→ no silent target null state
```

Mechanism evidence checks:

```text
mechanism-role sources can carry mechanism assertions with zero intervention components
```

Regression checks:

```text
Stage 1 validator PASS
Stage 2 validator PASS
historical Registry validator PASS
CSI Gateway validator PASS
bootstrap baseline PASS
Workbench build PASS
```

---

## 17. Stage 3 implementation sequence

1. Generate a new Supabase migration with the CLI.
2. Add application-family definitions and source-version mappings.
3. Add target-locus definitions.
4. Add target definitions/aliases and component-target mappings.
5. Add explicit target extraction status.
6. Add mechanism definitions/assertions and mechanism extraction status.
7. Add optional neutral→framework mappings.
8. Add RLS, grants and audit coverage.
9. Add deterministic conservative seed backfill/resolver suitable for clean replay.
10. Add Stage 3 validator.
11. Extend permanent bootstrap validation.
12. Add Workbench application/target/mechanism surfaces.
13. Reset/replay local database and bootstrap.
14. Verify Stage 1 + Stage 2 + Gateway parity.
15. Build Workbench.
16. Commit and record Stage 3 verification evidence.

---

## Exit criteria

Stage 3 is `VERIFIED` only when:

- Demand/Application Family is represented as a separate many-to-many use-case lens;
- seven target-locus families are controlled and distinct from routes;
- targets are represented using neutral scientific constructs;
- author-reported terms remain traceable;
- all 13 current intervention components have explicit target extraction state;
- mechanism assertions can exist independently of intervention components/routes;
- neutral target/mechanism concepts can optionally map to Trident-G/APC/H-AGI/CSI without rewriting external science;
- missingness cannot be mistaken for negative evidence;
- the 18-source seed remains reproducible;
- Stage 1 and Stage 2 invariants remain intact; and
- `csi-evidence-v1` remains backward compatible.
