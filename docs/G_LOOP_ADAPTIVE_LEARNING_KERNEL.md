# HRP Transfer Lab — Adaptive G-Loop Learning Kernel

**Version:** 1.1  
**Date:** 8 October 2026  
**Status:** canonical high-level learning-loop description for the HRP Transfer Lab  
**Scope:** research design, intervention development, computational modelling, evidence synthesis and protocol optimisation

## 1. Purpose

The HRP Transfer Lab G-Loop is not simply an observe → test → learn workflow.

It treats each research or intervention programme as an **adaptive trajectory**. The system should exploit a method while it is still producing worthwhile gains, tune it while identifiable improvements remain, reopen the search space when returns flatten or the model stops fitting the evidence, validate alternatives under changed conditions, and bank only bounded structure that survives appropriate tests.

The core principle is:

> **Stabilise what works without stabilising the whole system.**

The loop therefore aims to preserve reliable structure while maintaining enough controlled variability to discover better representations, strategies or protocols when the current one reaches a local ceiling.

## 2. Canonical loop

```text
SENSE
→ LOCATE
→ RECALL
→ GENERATE / SELECT CANDIDATES
→ FORECAST FUTURES
→ EVALUATE VALUE / COST / RISK / OPTIONALITY
→ COMMIT
→ PREDICT
→ ACT / TEST
→ COMPARE
→ ADAPT
→ BANK
↺
```

### SENSE
Collect the smallest sufficient set of observations needed to understand the current research or intervention state.

### LOCATE
Determine where the current method sits on its trajectory, at the relevant timescale.

### RECALL
Retrieve previously banked methods, rules, invariants or failure signatures that may apply to the present situation.

### GENERATE / SELECT CANDIDATES
Identify feasible candidate methods after recall and hard constraints.

### FORECAST FUTURES
Represent the plausible successor outcomes that matter for each serious candidate over the relevant horizon.

### EVALUATE VALUE / COST / RISK / OPTIONALITY
Compare candidates using expected benefit, resource cost, downside severity, reversibility, viability, learning value and the effect on future experimental or intervention options.

### COMMIT
Select a proportionate next move. Cheap, reversible, information-rich tests can justify action under more uncertainty than high-downside or hard-to-reverse changes.

### PREDICT
State prospectively what observable result should follow if the committed method is approximately right.

### ACT / TEST
Run a bounded intervention, model comparison, experiment, wrapper swap, simulation or evidence probe.

### COMPARE
Compare the observed result with the prospective prediction and identify the scale of mismatch.

### ADAPT
Continue, tune, transfer-test, reopen, switch, abandon or revert according to the evidence.

### BANK
Retain only structure whose context, evidence status, boundary conditions and reopening trigger remain explicit.

BANK is not the endpoint. Banked structure changes the starting point of future search.

## 3. Adaptive trajectory states

The same six-state grammar used in the wider Trident-G/Kastel work can be applied to research and intervention development.

| State | Research meaning |
| --- | --- |
| **GROWING** | The present model/protocol is still producing worthwhile gains in the target outcome or evidence quality. |
| **TUNING** | The model/protocol still appears basically right, but a parameter, implementation detail or identifiable bottleneck remains improvable. |
| **PLATEAU** | Marginal gains have fallen after adequate opportunity for local tuning; a local optimum or exhausted representation is plausible. |
| **REOPENING** | Controlled entropy is introduced by changing a meaningful dimension of the search space, representation, protocol or hypothesis set. |
| **VALIDATING** | Candidate alternatives are narrowed using prospective prediction, discriminating evidence, changed-condition tests, replication and boundary checks. |
| **BANKED** | A method, invariant or rule is currently reliable under known conditions and may be reused cheaply until its reopening trigger is met. |

The developmental trajectory is:

```text
GROWING
→ TUNING
→ PLATEAU
→ REOPENING
→ VALIDATING
→ BANKED
→ richer future search
```

A large prediction mismatch can bypass a long plateau and trigger diagnosis or reopening earlier.

## 4. Local tuning versus reopening

The critical decision is whether the expected value of further local optimisation remains higher than the expected value of testing a materially different alternative.

### Local tuning

Local tuning changes parameters inside the present representation or protocol.

Examples:
- difficulty or timing;
- threshold values;
- block length;
- probe frequency;
- model hyperparameters;
- wrapper details;
- sampling density.

### Reopening

Reopening changes the effective search neighbourhood.

Examples:
- alternative representation;
- different task wrapper;
- different context or domain;
- new hypothesis family;
- different intervention mechanism;
- different model class;
- different causal explanation.

Reopening must be **controlled**, not random. It should name:
- the changed dimension;
- what is held constant;
- why this opens a genuinely different search region;
- the prospective prediction;
- the stopping or rejection condition.

## 5. Expected futures, cost, risk and learning value

Alternative generation answers **what could be tried**. It is not sufficient for choosing what should be tried.

For serious candidates, the G-Loop should represent the futures that matter:

- expected benefit or improvement;
- probability or confidence where defensible;
- financial, computational, participant, staff and time costs;
- downside severity;
- reversibility;
- viability / safety / ethics constraints;
- information or learning value;
- effect on future research or intervention options.

Unknown values remain unknown.

Costs operate twice:

1. as feasibility constraints that can rule out an alternative before deeper comparison;
2. as trade-off variables when comparing feasible alternatives.

Expected value alone is insufficient where downside severity, irreversibility or viability risk differs materially.

The evidence threshold for commitment should rise with downside severity, irreversibility, viability threat and uncertainty.

Conversely, a cheap reversible experiment can be rational even when its immediate payoff is modest if it has high **learning value**: it distinguishes hypotheses, reduces important uncertainty, or changes which future experiments are worth running.

Optionality also matters. A method may improve the immediate target while narrowing later possibilities through technical, sample, theoretical or resource lock-in. This should remain visible rather than being hidden inside one scalar objective.

The v1 research kernel therefore uses an explicit decision profile rather than one opaque utility score:

```text
candidate
→ plausible futures
→ expected benefit
→ costs
→ downside / risk
→ reversibility
→ viability / ethics
→ learning value
→ optionality
→ proportionate commitment
```

## 5. Entropy and constraint

The G-Loop uses a recurrent rhythm:

```text
OPEN
generate credible alternatives
↓
CONSTRAIN
use discriminating evidence to identify what matters
↓
COMMIT / TEST
run the next informative action
↓
REOPEN
only when mismatch, plateau or changed conditions justify it
```

Entropy is not an end state. Its role is to preserve or restore access to alternatives.

Constraint is not mere exploitation. It is the process of identifying which dimensions of the expanded space are informative for the current target.

The desired regime is **structured variability**: enough entropy for alternative trajectories to remain reachable, with enough evidence-based constraint for learning to converge.

## 6. Multi-timescale learning

A research programme can occupy different trajectory states at different timescales.

Canonical levels are:

- **event / trial** — individual observations, model runs or probes;
- **session / block** — repeated performance under one local protocol;
- **study / experiment** — a bounded empirical or modelling programme;
- **programme / developmental** — accumulation of validated methods and portable structure across studies.

A short-timescale improvement must not overwrite a longer-timescale plateau.

Likewise, a single failed trial must not be treated as evidence that the entire theoretical model has failed.

The scale of the update must match the scale of the evidence.

## 7. What counts as growth

Growth is multidimensional.

Relevant dimensions may include:

- target performance;
- information gained;
- prediction accuracy;
- evidence quality;
- robustness or recovery;
- portability across wrappers or contexts;
- reduced uncertainty;
- computational or implementation efficiency;
- optionality — the number of viable next tests or intervention paths remaining.

These should remain explicit rather than being collapsed into one opaque score unless a validated composite is later justified.

## 8. Context-sensitive recall of banked structure

BANKED knowledge is active memory, not archive.

Before reopening search, the system should ask:

> **Does the present situation instantiate conditions under which a previously banked method, invariant, rule or failure signature may be relevant?**

Applicability should consider:

- objective match;
- task/intervention family;
- population or sample;
- representation / wrapper;
- context and domain;
- bottleneck or failure signature;
- time horizon;
- evidence strength;
- known boundary conditions;
- recency and environmental change;
- contradictory evidence.

A retrieved item is classified as:

- **DIRECT_REUSE** — conditions are sufficiently close to prior validation;
- **TRANSFER_CANDIDATE** — structurally similar, but meaningful conditions differ;
- **ADAPT_CANDIDATE** — relevant but requires bounded modification;
- **RECOMBINATION_CANDIDATE** — two or more banked structures may be combined into a new testable candidate;
- **NOT_APPLICABLE** — important boundary conditions conflict.

The governing rule is:

> **Recall before reopening, but validate before generalising.**

Semantic similarity alone is not evidence of transfer.

## 9. Banked structure

A banked item should retain:

```text
WHAT WORKS
FOR WHICH TASK / POPULATION / DOMAIN
UNDER WHICH CONDITIONS
EXPECTED EFFECT OR DIRECTION
EVIDENCE STATUS
KNOWN FAILURE CONDITIONS
BOUNDARY CONDITIONS
TRANSFER STATUS
LAST VALIDATED
REVIEW / EXPIRY CONDITION
REOPEN TRIGGER
```

Banked structure may include:

- a protocol;
- a control policy;
- a transfer invariant;
- a model component;
- a diagnostic failure signature;
- an intervention rule;
- a reusable analysis procedure;
- a bounded explanatory schema.

A banked item can return to TUNING, VALIDATING or REOPENING if the evidence changes.

## 10. Relationship to local and global optimisation

A learning curve can improve within a local strategy while remaining constrained by that strategy's representation.

The G-Loop therefore distinguishes:

1. **parameter optimisation** — improve within the current model;
2. **strategy/protocol optimisation** — test a different policy or protocol;
3. **model/landscape revision** — change the representation, hypothesis family or problem formulation.

Repeated failure at one level does not automatically justify revision at the next.

The purpose of plateau detection is not to force novelty. It is to recognise when further local optimisation has diminishing expected value.

## 11. Relation to the current executable far-transfer protocol

`protocols/config/baseline_protocol.yaml` already implements an earlier operational subset of this logic:

- Ψ-state gating;
- plateau + low-drift versus plateau + high-drift routing;
- wrapper swaps;
- entropy-then-MI capture;
- diagnostic probes;
- portability tests;
- delayed re-checks;
- conservative banking.

This document generalises that logic into the broader HRP Transfer Lab research architecture.

The executable protocol remains authoritative for its own thresholds and operators. This high-level document does **not** silently change those numerical thresholds.

## 12. Criticality / Trident-G interpretation

At the theoretical level, Trident-G proposes that adaptive cognition depends on preserving access to a near-critical, reconfigurable regime from which the system can use stable automatised structure when conditions are regular and reopen higher-gain search when existing structure becomes insufficient.

For the Transfer Lab, this is used as a **design hypothesis and organising principle**, not as a claim that every experimental plateau is a direct neural criticality measurement.

Operationally:

```text
stable validated structure
→ efficient reuse
→ mismatch / plateau / changed conditions
→ controlled reopening
→ discriminating evidence
→ validated new structure
→ conservative banking
```

## 13. Implementation invariants

1. No plateau from a single flat observation.
2. No reopening without a named changed dimension.
3. No architectural revision from weak local evidence.
4. No prospective prediction written after the outcome.
5. No banked rule from one unreplicated success.
6. No transfer claim without a changed-condition test.
7. No semantic similarity treated as evidence of transfer.
8. No recombination of banked strategies treated as already validated.
9. No banked rule treated as permanently true.
10. No large revision before checking data quality, execution failure and temporary shocks.
11. No automatic inference that a behavioural plateau is a neural criticality transition.
12. Preserve provenance, counter-evidence and failed tests.

## 14. Final compression

The HRP Transfer Lab G-Loop is:

> **Exploit what is still producing informative growth. Tune while the current representation remains productive. Diagnose diminishing returns before reopening. Reopen the search space deliberately when the current model becomes limiting. Constrain alternatives with discriminating evidence. Validate under changed conditions. Bank only bounded structure that survives, and recall that structure when future situations make it relevant.**

In compact form:

```text
SENSE
→ LOCATE
→ RECALL
→ TUNE OR REOPEN
→ FORECAST FUTURES
→ EVALUATE VALUE / COST / RISK / OPTIONALITY
→ COMMIT
→ PREDICT
→ TEST
→ COMPARE
→ VALIDATE
→ BANK
→ START THE NEXT SEARCH RICHER
```
