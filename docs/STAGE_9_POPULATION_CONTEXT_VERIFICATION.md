# Evidence Registry v1.1 — Stage 9 Population and Context Verification

**Status:** VERIFIED  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`  
**Implementation tip:** `9a1b1631caff236c99cc1bcc8fc5e503911d38e7`

## Scope

Stage 9 normalises population, role, health/condition context, baseline cognitive status, education level, study setting, delivery context and geography while retaining original free-text population/setting fields and keeping Stage 3 application family as a separate many-to-many lens.

The governing scientific distinction is:

```text
life stage
!= role
!= health / condition context
!= baseline cognitive status
!= education level
!= study setting
!= delivery context
!= geography
!= application family
!= proposition-relative context fit
```

This prevents broad labels such as `adult`, `student`, `healthy` or `education` from swallowing scientifically important population/context differences.

## Implementation evidence

### Execution specification

- `docs/STAGE_9_POPULATION_CONTEXT_IMPLEMENTATION.md`

### Migration

- `supabase/migrations/20260831223000_evidence_registry_v1_1_population_context.sql`

### Audit and seed assets

- `components/evidence-registry/scripts/audit_stage9_population_context.py`
- `components/evidence-registry/data/stage9_seed_mappings.v1.json`
- `components/evidence-registry/scripts/validate_stage9_seed_mappings.py`
- `components/evidence-registry/scripts/apply_stage9_seed_mappings.py`
- `components/evidence-registry/scripts/validate_stage9_population_context.py`

### Workbench

- `apps/evidence-workbench/src/Stage9PopulationContextReview.tsx`
- wired through `apps/evidence-workbench/src/SourceDetailWithMaturity.tsx`

### Deterministic replay

- `components/evidence-registry/scripts/bootstrap_local_registry.py` applies and validates Stage 9 after Stages 1–8.

## Controlled ontology

Stage 9 defines **28 controlled population/context terms** across eight orthogonal facets:

```text
life_stage                  4
role                        4
health_condition_context    2
baseline_cognitive_status   1
education_level             4
study_setting               8
delivery_context            4
geography                   1
```

Population/context terms are scientifically neutral evidence descriptors rather than CSI product claims.

## Seed mapping verification

The immutable 18-source seed produces:

```text
studies                       18
study facet status rows       126
study population/context links 59
intervention components       13
component delivery links       4
context-fit assessments        0
```

All seed mappings remain:

```text
mapping_source = agent_candidate
review_status = proposed
```

No agent candidate is promoted automatically.

## Scientific boundary checks

### Orthogonal population facets — PASS

The model preserves distinct facets instead of collapsing them into a generic population label. For example, the healthy university-undergraduate study remains separately representable as:

```text
young adult
university student
healthy/nonclinical
higher education
```

### Mixed-sample subgroup preservation — PASS

Mixed samples remain subgroup-scoped rather than flattened. The younger/older adult study retains both age groups as `includes_subgroup`, and the mixed university-student / early-career-knowledge-worker sample retains both roles as subgroups.

### Explicit missingness — PASS

Each study receives an explicit extraction status for seven study-level facets. Unmapped facets remain `not_yet_extracted` rather than being interpreted as absence of a characteristic.

Each intervention component receives an explicit delivery-context extraction status.

### Study setting vs delivery context — PASS

Study setting and intervention delivery are separate subjects. A school or university classroom is a study setting; researcher-facilitated or guided training is delivery context.

### Geography non-inference — PASS

Geography is not inferred from broad contextual language. The seed maps geography only where explicitly supported by the reviewed record (China for the Chinese-undergraduate study).

### Application-family separation — PASS

Stage 3 remains unchanged:

```text
application-family definitions  7
seed application links          32
source versions represented     18
distinct families used by seed   6
```

Application family remains a use-case lens and is not converted into population/context identity.

### Context-fit non-fabrication — PASS

`context_fit_assessment` contains **0 rows** in the seed.

Context fit is proposition-relative and must not be inferred merely because a study has structured population/context metadata.

### Human approval boundary — PASS

No `agent_candidate` Stage 9 term, status or context-fit row is automatically approved.

## Workbench verification

The Workbench includes a Stage 9 Population & Context reviewer that:

- displays the original population and setting text alongside normalised facets;
- shows extraction status for each study-level facet;
- displays and allows review of candidate population/context mappings;
- separates component delivery-context review from study setting;
- exposes proposition-relative context-fit rows where they exist;
- does not manufacture context-fit scores from descriptive metadata;
- keeps application family separate from population/context coding.

The Workbench build passed after Stage 9 integration.

## Regression / replay verification

A complete local deterministic bootstrap through Stage 9 passed, preserving all previously verified Stage 1–8 invariants and ending with:

```text
LOCAL REGISTRY BASELINE PASS
```

Stage 9 database validation passed with:

```text
STAGE 9 POPULATION/CONTEXT VALID:
terms=28;
studies=18;
study_status_rows=126;
study_links=59;
components=13;
delivery_links=4;
context_fit=0
```

The final local Supabase advisor gate contained no blocking error/security finding; non-blocking INFO/performance notices do not alter Stage 9 scientific correctness.

## Immutable-release boundary

Stage 9 is additive. It does not mutate:

- immutable evidence release `2026-08-23`;
- historical release JSON records;
- CSI Gateway contract `csi-evidence-v1`;
- source-level EML mappings;
- Stage 8 body-level proposition/certainty/maturity semantics.

## Exit criteria

Stage 9 exit criteria are satisfied:

- `healthy university students` cannot collapse simply to `adults`;
- evidence can be filtered using orthogonal life-stage, role, health, cognitive-status, education, setting, delivery and geography lenses;
- application family remains separate;
- mixed populations are preserved;
- missing facets remain explicit;
- context-fit/boundary judgements have a first-class proposition-relative subject without being fabricated for the seed;
- AI candidate mappings remain human-review gated;
- deterministic replay and Workbench build pass;
- the immutable release and Gateway remain unchanged.

**Stage 9 is VERIFIED.**
