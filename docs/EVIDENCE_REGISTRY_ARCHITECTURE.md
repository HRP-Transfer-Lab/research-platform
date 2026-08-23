# Evidence Registry Architecture

## General-audience overview

The **HRP Transfer Evidence Registry** is a living scientific database designed to organise research on interventions that may improve human cognition, learning, performance, resilience and real-world functioning.

Rather than functioning as a conventional bibliography, it asks a more practical question:

> **What was changed, in whom, by what method, what improved, and how far did that improvement actually travel?**

Each reviewed paper is converted into a structured evidence record. The Registry can capture:

- who took part in the study;
- what problem, cognitive function or practical capability was targeted;
- what intervention was delivered;
- the intervention route or routes involved;
- the exact protocol, including session length, frequency, programme duration and delivery method where reported;
- what outcomes were measured;
- whether benefits appeared only on the practised task or also on separate, delayed or real-world outcomes;
- the population and setting for which the finding has actually been demonstrated;
- study-quality and evidence-certainty information;
- and how the finding may inform Explorer, IQ Coach, H-AGI or CSI without being mistaken for validation of those products themselves.

The first approved seed release contains the studies reviewed in the May-August 2026 IQ Mindware intervention evidence radar. The Registry is designed to grow through future literature searches and review cycles rather than remain a static snapshot.

### Why the Registry is different from a normal literature database

A conventional reference manager can tell us that a paper exists. The Transfer Evidence Registry is intended to tell us **what the evidence means for intervention design**.

A central principle is that three questions remain separate:

```text
WHAT WAS THE INTERVENTION DESIGNED TO CHANGE?
        ↓
WHAT OUTCOME WAS ACTUALLY MEASURED?
        ↓
HOW FAR DID THE OBSERVED CHANGE TRAVEL?
```

For example, working-memory training that improves a different reasoning test remains a **Train** intervention. The new reasoning result may constitute transfer evidence, but it does not automatically turn the original intervention into a real-world **Bridge** intervention.

This prevents broad claims from being inferred simply because a study reported improvement somewhere beyond the training task.

---

## The intervention-route framework

The Registry uses the **IQ Mindware Transfer Route Framework** to classify interventions according to the main locus they are designed to change.

### Develop → Equip

Build an explicit repertoire of strategies, rules, heuristics or candidate policies.

Examples include decision rules, self-explanation strategies, source-checking rules or methods for generating alternative explanations.

### Develop → Train

Develop a cognitive operation, procedural skill or increasingly efficient execution of a learned method through structured practice.

Examples include attention-control training, working-memory practice, relational learning, predictive modelling and explicit reasoning practice.

### Develop → Condition

Improve the longer-term physiological operating substrate supporting cognition.

Examples include sustained exercise programmes, sleep restoration or other longer-term physiological interventions.

### Regulate

Change the person's current operating state so existing capabilities are more usable now.

Examples include acute exercise, paced breathing, rest, light exposure or short state-regulation procedures.

### Bridge

Connect a useful operation or strategy to the cues, actions and feedback of the real activity in which it must be used.

The canonical chain is:

```text
DIAGNOSTIC CUE
→ POLICY RECOVERY OR SELECTION
→ COGNITIVE OPERATION / PROCEDURAL SKILL
→ ACTION
→ ENVIRONMENTAL OUTCOME
→ FEEDBACK
→ POLICY UPDATE
```

Examples include implementation intentions, resumption cues, real-work practice, prompt fading and later unsupported use.

### Redesign

Change the surrounding learning, work or human-AI niche itself.

Examples include interruption structure, workload, decision rights, information architecture, AI role allocation, verification rules, incentives or feedback timing.

### Integrate

Deliberately combine two or more intervention loci.

For example:

```text
exercise
→ Develop → Condition

working-memory practice
→ Develop → Train

implementation intention
→ Bridge

whole multicomponent programme
→ Integrate
```

The overall study arm can therefore be classified as Integrate while its individual components retain their own route identities.

**Measure / Prove** and the **Metacognitive Governor** are kept separate from these intervention routes. Measure / Prove describes evidence architecture; the Governor describes cross-cutting monitoring and control.

---

## What gets recorded for a study

The Registry is designed to capture evidence at several linked levels rather than reducing a paper to a single summary sentence.

### Source and study

Typical fields include:

```text
title
authors
year
journal / source
DOI / PMID / preprint identifier
study design
comparator
preregistration / registration where available
country / setting
```

### Population

The Registry can record:

```text
age or age range
healthy / clinical / occupational / educational population
student / worker / manager / older-adult / other role
health context where relevant
baseline ability or risk group where reported
study setting
```

This helps prevent evidence from one population being presented as though it were automatically established for another.

### Functional and cognitive target

A study can be coded at several levels:

```text
UNDERLYING OPERATION
attention control
working memory
binding
prediction
reasoning

EXPLICIT STRATEGY / POLICY
implementation intention
decision rule
self-explanation
reappraisal strategy

H-AGI META-FUNCTION
sensemaking
argumentation
decision-making
strategic action
negotiation
learning / transfer
reappraisal / resilience

APPLIED FUNCTION
learning
work performance
task resumption
prospective memory
decision quality
stress resilience
human-AI performance
```

These levels remain distinguishable because an intervention can affect a task operation without establishing improvement in a broader real-world function.

### Protocol and dose

Where the source provides enough information, the Registry records:

```text
intervention components
materials / activities
provider or facilitator
delivery mode
setting
session duration
number of sessions
frequency
total programme duration
tailoring / adaptation
home practice
adherence / fidelity
```

This makes it possible to ask not merely **whether** an intervention worked, but **what was actually done**.

### Outcomes and transfer

Results are stored at outcome level wherever possible:

```text
outcome
measure
timepoint
effect direction / estimate where available
evidence rung
transfer axis
```

The Registry distinguishes evidence such as:

```text
PRACTICE EFFECT
performance improves on the practised exercise

CHANGED-FORMAT EVIDENCE
the operation survives an altered wrapper or surface

SEPARATE-MEASURE EVIDENCE
change appears on an independent measure

DELAYED EVIDENCE
change remains detectable after a later interval

APPLIED OUTCOME
performance changes in a defined work, study or everyday activity
```

The Trident-G transfer axes are recorded separately:

```text
HORIZONTAL
same operation or relation under a changed surface

VERTICAL
recovery across cognitive layers

NICHE
recovery in a real activity with real cues and feedback

DELAYED
recovery after time
```

For Bridge research, the Registry can additionally distinguish:

```text
prompted use
→ cue-triggered use
→ changed-context use
→ unprompted use
→ delayed unsupported use
```

---

## Relationship to Explorer, IQ Coach and H-AGI

The Registry sits underneath the wider platform:

```text
SCIENTIFIC LITERATURE
        ↓
HRP TRANSFER EVIDENCE REGISTRY
        ↓
HUMAN-APPROVED / VERSIONED EVIDENCE RELEASE
        ↓
────────────────────────────────────────────
        ↓              ↓              ↓
   EXPLORERS        IQ COACH       H-AGI / CSI
```

The intended roles are different.

### Explorer

Explorer applications can combine a candidate bottleneck or constraint with Registry filters such as route, population, context and functional target.

For example:

```text
candidate constraint:
task-resumption failure

candidate routes:
Bridge + Redesign

population:
working adults

context:
AI-assisted workflow

        ↓

query approved evidence
```

The Registry returns relevant evidence, protocol information and limitations. Explorer remains responsible for user-specific routing.

### Cognitive Control Coach

Relevant evidence may concern:

```text
attention control
selected-state maintenance
interference control
decision timing
FIND / HOLD / UPDATE / ACT deployment
Bridge methods
```

### Reasoning Coach

Relevant evidence may concern:

```text
relational learning
working-memory binding
prediction
explicit inference
reasoning strategies
strategy transfer
```

### H-AGI

Relevant evidence may concern higher-order methods for:

```text
sensemaking
argumentation
decision-making
strategic action
negotiation
learning
reappraisal
human-AI cognitive collaboration
```

### CSI

CSI can make particular use of **Redesign** and **Integrate** evidence where the operative problem lies in workflow, authority, interruptions, incentives, information structure or AI configuration rather than only in the individual.

---

## Product relevance is not product validation

The Registry deliberately separates **relevance to an IQ Mindware product** from evidence that the product itself has been validated.

A record may therefore say:

```text
product:
cognitive_control_coach

support_scope:
Bridge method

match_level:
close

direction:
supportive

claim_status:
design_informing
```

This means that a finding is useful for the design or scientific rationale of Cognitive Control Coach. It does **not** mean that the study tested Cognitive Control Coach itself.

Exact implementation validation, external validation and product-level efficacy remain separate claims.

---

## Scientific protocols and review standards

The Registry combines the HRP / IQ Mindware intervention architecture with established scientific-review and intervention-reporting standards.

### Internal protocols

The main internal frameworks are:

- **IQ Mindware Transfer Route Framework** — classifies Equip, Train, Condition, Regulate, Bridge, Redesign and Integrate;
- **Trident-G Far Transfer Protocol** — distinguishes horizontal, vertical, niche and delayed portability;
- **IQ Mindware Two-App Cognitive System Specification** — maps evidence onto Cognitive Control Coach, Reasoning Coach and the separate G Track Measure / Prove layer;
- **SPACE-PACE / H-AGI** — distinguishes underlying capacities, explicit strategies, higher-order meta-functions and real-world deployment;
- **CSI constraint architecture** — distinguishes capacity, coupling, niche and mixed constraints at the wider activity-system level.

### External standards

The database structure is intended to support established review practices including:

- **TIDieR** for intervention-description fields such as materials, procedures, provider, delivery mode, setting, dose, tailoring and fidelity;
- **PRISMA / PRISMA-S** for documenting searches, screening, selection and literature-update procedures;
- **RoB 2** for risk-of-bias appraisal of randomised trials;
- **ROBINS-I** where appropriate for non-randomised intervention studies;
- **GRADE** for evaluating certainty in a body of evidence supporting an outcome.

Study-level risk of bias and body-of-evidence certainty are deliberately stored separately. A GRADE certainty rating should not simply be attached to an individual paper.

---

## Human approval and living updates

The Registry is designed as a **living scientific system** rather than an automatically populated recommendation engine.

New papers can enter a pipeline such as:

```text
DISCOVER
→ SCREEN
→ PRE-EXTRACT
→ HUMAN VERIFY
→ ROUTE CLASSIFY
→ APPRAISE
→ APPROVE
→ SYNTHESISE
→ RELEASE
```

AI or automated services may help discover, deduplicate or pre-extract papers. They should not independently promote new evidence into production recommendations.

Production systems should query only **approved, versioned evidence releases**.

This allows an Explorer or other application to retain provenance such as:

```text
evidence_release_id: 2026-08-23
taxonomy_version: iqm-route-v0.2
```

so a later audit can reconstruct which evidence and classification system informed the result.

---

## One-sentence description

> **The HRP Transfer Evidence Registry is a continuously updated scientific map linking interventions to the people they were tested on, the methods used, the functions targeted, the outcomes demonstrated, the strength and portability of the evidence, and the parts of the Explorer–IQ Coach–H-AGI system that evidence can legitimately inform.**

---

## Technical purpose

The HRP Transfer Evidence Registry is the evidence infrastructure layer beneath the broader platform:

```text
SCIENTIFIC LITERATURE
        ↓
HRP TRANSFER EVIDENCE REGISTRY
        ↓
APPROVED / VERSIONED EVIDENCE RELEASE
        ↓
Explorer ─ IQ Coach ─ H-AGI / CSI
```

The registry is not a bibliography and is not a generative recommender. It records what was studied, what was done, to whom, what changed, how far the result travelled, and what the result can legitimately inform.

## Canonical unit of interpretation

A **report** is not automatically one intervention and an **intervention arm** is not automatically one route.

Multicomponent interventions should be decomposed at component level:

```text
exercise → Develop → Condition
working-memory practice → Develop → Train
implementation intention → Bridge
workflow change → Redesign
```

The overall arm may then be coded `Integrate` if distinct loci were deliberately combined.

## Main query dimensions

Explorer and H-AGI should be able to query by:

- route;
- population / age / role / health context;
- cognitive operation;
- explicit strategy or policy;
- H-AGI meta-function;
- applied functional target;
- delivery mode, dose and setting;
- outcome and measurement type;
- evidence rung;
- Trident-G transfer axis;
- Bridge prompt/independence level;
- product relevance;
- study design / peer-review status;
- risk of bias / evidence certainty;
- evidence release/version.

## Technical product-support fields

`product_relevance` is deliberately multidimensional:

```text
product
support_scope
match_level
support_direction
claim_status
rationale
```

A paper can be highly relevant to the design of CCC without validating CCC itself. Exact implementation validation must remain a separate claim.

## App interaction

The first production integration should expose read-only approved views, for example:

```text
v_approved_evidence
v_product_evidence
v_route_population_evidence    # later
v_protocol_evidence            # later
v_transfer_evidence            # later
approved_claim                 # synthesis-backed only
```

Explorer should combine its candidate constraint with evidence filters. Example:

```text
candidate constraint: task-resumption failure
route candidates: Bridge + Redesign
population: working adults
context: AI-assisted workflow

query approved evidence where:
route in (bridge, redesign)
and population matches working adults
and target includes interruption/resumption
```

The evidence layer returns supported options and boundaries. Explorer remains responsible for user-specific routing.

## Quality architecture

Keep separate:

- **study/outcome risk of bias**: RoB 2 for randomized trials; ROBINS-I where appropriate;
- **reporting completeness / replicability**: TIDieR-style protocol fields;
- **body-of-evidence certainty**: synthesis-level assessment such as GRADE;
- **claims approval**: internal/public claim review.

Do not attach a GRADE certainty label to a single study.

## Living-update model

Each evidence stream should have a search protocol and cadence. New papers enter as proposals and cannot change production recommendations until human-approved and included in a new evidence release.

```text
raw discovery
→ reviewed source
→ approved record
→ synthesis
→ versioned release
→ production read model
```

This preserves reproducibility: an Explorer output can record the exact `evidence_release_id` and `taxonomy_version` that generated it.
