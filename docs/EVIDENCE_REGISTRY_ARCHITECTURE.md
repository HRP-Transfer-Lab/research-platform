# Evidence Registry Architecture

## Purpose

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

## Product support is not product validation

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
