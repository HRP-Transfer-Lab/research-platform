# HRP Transfer Evidence Registry v1.1 — Canonical Implementation Plan

**Status:** Active implementation plan  
**Branch:** `evidence-registry-v1.1`  
**Repository:** `HRP-Transfer-Lab/research-platform`  
**Created:** 26 August 2026  
**Purpose:** Provide the durable machine- and chat-independent execution plan for upgrading the HRP Transfer Evidence Registry before large-scale evidence ingestion.

---

## 1. Objective

Upgrade the current approved seed Registry into a scalable, cross-domain intervention-evidence system suitable for Personal CSI, Work/Organisational CSI, education, cognitive longevity, performance, wellbeing and carefully bounded condition-related / health-adjacent applications.

The v1.1 programme must preserve the strengths of the current system while correcting the scientific units of analysis before the corpus expands from 18 records to hundreds or thousands of papers.

The target architecture is:

```text
PUBLICATION / REPORT
        ↓
CANONICAL SOURCE + SOURCE VERSION
        ↓
STUDY / EXPERIMENT
        ↓
POPULATION + STUDY ARM
        ↓
INTERVENTION COMPONENT
        ↓
ROUTE × TARGET × MECHANISM
        ↓
CONTRAST
        ↓
OUTCOME × EFFECT × TIME × TRANSFER × HARM
        ↓
RESULT-LEVEL QUALITY
        ↓
EVIDENCE PROPOSITION
        ↓
SYNTHESIS OUTCOME
        ↓
GRADE + BODY-LEVEL EML
        ↓
APPROVED CLAIM
        ↓
IMMUTABLE EVIDENCE RELEASE
        ↓
CSI EVIDENCE GATEWAY
```

Running alongside every layer:

```text
PROVENANCE
Who/what extracted this field?

REVIEW
Who verified or changed it?

VERSION
Which reviewed representation was approved?

RELEASE
Which immutable scientific state did CSI consume?
```

---

## 2. Governing scientific principles

### 2.1 Route, outcome and transfer remain separate

The canonical Transfer Route Framework governs classification:

```text
WHAT IS BEING CHANGED?
→ intervention route

WHAT WAS MEASURED?
→ outcome / evidence

DID IT TRAVEL?
→ transfer / portability
```

The seven true intervention routes are:

```text
develop_equip
develop_train
develop_condition
regulate
bridge
redesign
integrate
```

`Measure / Prove`, mechanism evidence and the Metacognitive Governor are not intervention routes.

### 2.2 EML is maturity only

EML answers:

> How far has the proposition progressed through the evidence-development pathway?

It remains separate from:

```text
risk of bias / methodological quality
body-level certainty such as GRADE
effect direction and magnitude
transfer evidence
population/context fit
```

A high-quality mechanistic study may legitimately remain EML1. A mature evidence body may establish a null effect, boundary condition or harm.

### 2.3 Product relevance is not product validation

A source may inform the design or rationale of an IQ Mindware / CSI product without validating the product itself.

### 2.4 Missingness is scientifically meaningful

The Registry must distinguish:

```text
UNKNOWN
NOT YET EXTRACTED
NOT REPORTED
NOT MEASURED
NOT APPLICABLE
MEASURED — NULL
MEASURED — HARMFUL
```

Empty fields must never silently imply negative evidence.

### 2.5 Scientific neutrality first; framework mappings second

External literature should be represented using a sufficiently neutral evidence ontology. Trident-G, APC, H-AGI and CSI interpretations should map onto that ontology rather than forcing every external construct into proprietary terminology.

### 2.6 Human approval remains the scientific gate

AI may discover, screen, pre-extract, classify and critique. AI does not independently promote evidence into approved production releases or public claims.

---

## 3. Non-negotiable compatibility rules

1. **Do not mutate the existing `2026-08-23` evidence release.** It remains an immutable seed snapshot.
2. **Do not break `csi-evidence-v1` while the Registry backend is being refactored.** Existing CSI Explorers must continue to consume the current Gateway contract until a deliberate Gateway version/release decision is made.
3. **Do not allow user/person/session data into the scientific Evidence Registry.** CSI outcome data may only enter later through a separately governed research-ingestion route.
4. **Do not delete historical source IDs, EML assessments or release provenance during migration.** Use explicit mapping/version tables.
5. **Do not let an automated agent write approved claims or body-level maturity ratings.**
6. **Do not expand the corpus substantially until the 18-source seed has been successfully backfilled into the v1.1 model and parity-tested.**

---

## 4. The evidence cube to preserve across domains

The core query architecture should support:

```text
DEMAND / APPLICATION FAMILY
mental fitness | performance | learning | executive functioning |
wellbeing | longevity | condition-related support

×

INTERVENTION ROUTE
equip | train | condition | regulate | bridge | redesign | integrate

×

TARGET / MECHANISM
biological | state | cognitive | affective/motivational |
strategy/policy | coupling | niche

×

POPULATION / CONTEXT
life stage | role | health context | setting | delivery context

×

OUTCOME DISTANCE
trained task | changed format | separate measure | real-life function

×

TRANSFER
horizontal | vertical | niche

×

TIME
immediate | post-intervention | delayed/follow-up

×

OUTCOME ROLE
benefit | harm | target engagement | process | adherence | implementation

×

EVIDENCE DEVELOPMENT
study design + RoB → effect → replication → synthesis + GRADE → EML
```

Demand/application family is a use-case lens, not the intervention mechanism.

---

# 5. Fixed 12-stage implementation programme

## Stage 1 — Freeze intervention-route semantics

**Goal:** Remove category leakage before any schema expansion.

### Implement

- Canonical seven-route vocabulary only:
  - `develop_equip`
  - `develop_train`
  - `develop_condition`
  - `regulate`
  - `bridge`
  - `redesign`
  - `integrate`
- Separate controlled dimensions for:
  - `evidence_role`
  - `controller_or_overlay`
  - source/review bucket
- Move values such as `measure_prove`, `mechanism_evidence`, `state_mechanism_evidence`, `metacognitive_governor_evidence` and observational taxonomies out of the route vocabulary.
- Update validators and Workbench route selectors.
- Preserve backward mapping for the 18 seed records.

### Exit criteria

- Every intervention component either has one of the seven routes or is explicitly non-intervention evidence.
- Mechanism/measurement/observational records validate without masquerading as intervention routes.
- Existing Gateway cards still reproduce the same v1 public classifications/caveats.

**Status:** `VERIFIED`  
**Evidence:** `docs/STAGE_1_ROUTE_SEMANTICS_VERIFICATION.md`; migration `20260826212614`; implementation commit `bf639c32249b7707bd8b2f8c485f715acafe6c37`.

---

## Stage 2 — Separate canonical source identity from reviewed source versions

**Goal:** Make the same publication reusable across multiple immutable releases without duplicating scientific identity.

### Target model

```text
canonical_source
source_version
evidence_release
release_source_version
```

### Implement

- Create persistent canonical publication/report identity.
- Create reviewed/extracted `source_version` records.
- Link releases to specific source versions through a junction table.
- Preserve DOI/PMID/arXiv/URL identity and deduplication rules.
- Migrate current `evidence_source.source_id` records without destroying historical IDs.
- Define Gateway card identity separately from release-specific card/version identity.

### Exit criteria

- One canonical paper can appear in multiple releases using different reviewed versions.
- The `2026-08-23` snapshot remains reproducible exactly.
- A later correction creates a new source version rather than silently changing a historic release.

**Status:** `VERIFIED`  
**Evidence:** `docs/STAGE_2_SOURCE_IDENTITY_VERIFICATION.md`; migration `20260826215834`; implementation commit `fb9e79a80e3c222c07b246d3116a147603726464`.

---

## Stage 3 — Normalise demand family, target, target locus and mechanism

**Goal:** Build a domain-general scientific ontology beneath CSI/IQM mappings.

### Minimum target-locus families

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

### Implement

- Controlled target ontology.
- Candidate mechanism ontology / mechanism assertions.
- Target-locus mapping table(s).
- Demand/application family taxonomy:
  - mental fitness
  - performance
  - learning
  - executive functioning
  - wellbeing
  - longevity
  - condition-related support
- Optional mappings from neutral ontology nodes to APC/Trident-G/H-AGI/CSI concepts.
- Keep author-reported constructs distinct from HRP interpretation.

### Exit criteria

- All 13 current intervention components can be assigned a target locus or explicit `not_yet_extracted` state.
- Mechanism evidence can be queried independently of intervention route.
- A single intervention can legitimately map to several application families without changing its route.

**Status:** `IN PROGRESS`  
**Execution spec:** `docs/STAGE_3_TARGET_MECHANISM_APPLICATION_IMPLEMENTATION.md`.

---

## Stage 4 — Refactor outcome architecture into orthogonal dimensions

**Goal:** Remove hybrid `evidence_rung` semantics.

### Separate dimensions

```text
OUTCOME DISTANCE
trained_task
changed_format
separate_measure
real_life_function

TIME / FOLLOW-UP
immediate
post_intervention
delayed

TRANSFER TEST
horizontal
vertical
niche

OUTCOME ROLE
benefit
harm
target_engagement
process
adherence
implementation
```

Bridge-specific evidence remains separately coded:

```text
prompted_use
cue_triggered_use
changed_context_use
unprompted_use
delayed_portability
```

### Implement

- Replace ambiguous hybrid rung labels with decomposed fields/tables.
- Preserve legacy rung values through explicit migration mapping.
- Add missingness/status semantics.
- Keep delayed timing distinct from outcome distance.

### Exit criteria

- A result can simultaneously be coded `separate_measure + delayed + vertical`.
- `not measured` cannot be mistaken for `null effect`.
- Current 38 outcomes migrate losslessly.

**Status:** `NOT STARTED`

---

## Stage 5 — Add study arms, component membership and contrasts

**Goal:** Represent trials, factorial studies and multicomponent programmes correctly.

### Target hierarchy

```text
study
├── study_arm
│   └── arm_component
└── study_contrast
```

### Implement

- `study_arm`
- `arm_component`
- `study_contrast`
- comparator/control-arm metadata
- randomisation/allocation fields where appropriate
- support for factorial and dismantling designs

### Exit criteria

- Combined exercise + cognitive-training studies can be represented without flattening components.
- Active control, waitlist, treatment-as-usual and alternative interventions are explicit arms/contrasts.
- Existing studies without detailed arm extraction remain valid using explicit completeness status.

**Status:** `NOT STARTED`

---

## Stage 6 — Make effect estimates first-class records

**Goal:** Support quantitative synthesis rather than only direction summaries.

### Implement

Create child effect-estimate records supporting, where applicable:

```text
raw group values
change scores
mean differences
standardised mean differences
odds ratios
risk ratios
hazard ratios
correlations
regression coefficients
adjusted / unadjusted estimates
standard errors
confidence intervals
sample analysed
p values where useful
model specification
```

Effects should attach to the relevant contrast + outcome/result, not merely to a paper.

### Exit criteria

- One outcome may contain multiple legitimate estimates without overwriting one another.
- Meta-analysis-ready effect data can be exported for supported studies.
- The existing single effect estimate is migrated without loss.

**Status:** `NOT STARTED`

---

## Stage 7 — Rebuild quality appraisal around the correct scientific unit

**Goal:** Correct the current source-linked quality model before formal RoB/GRADE work begins.

### Distinguish

```text
study/reporting quality
result/outcome-specific risk of bias
body-of-evidence certainty
implementation/fidelity assessment
```

### Implement

- Result/outcome-level RoB subject references.
- Study/reporting assessment subject references.
- Synthesis-outcome/body-level certainty assessment references.
- Support RoB 2, ROBINS-I and other justified tools.
- Keep TIDieR/reporting completeness distinct from risk of bias.
- Keep GRADE at body/outcome level only.

### Exit criteria

- RoB can target the actual result being interpreted.
- GRADE cannot accidentally be attached to one source as if it were body certainty.
- Workbench can review the relevant assessment unit explicitly.

**Status:** `NOT STARTED`

---

## Stage 8 — Add evidence propositions and synthesis outcomes

**Goal:** Give EML and approved claims the correct body-level object.

### Evidence proposition

A proposition should specify enough context to identify what is actually being claimed, for example:

```text
intervention/exposure
population
context
comparator
target/outcome
timeframe
```

### Implement

- `evidence_proposition`
- source/result contributions to proposition
- `evidence_synthesis`
- `synthesis_outcome` / proposition-specific synthesis result
- pooled effect / heterogeneity fields where applicable
- body-level GRADE
- body-level EML
- approved claim generated from a reviewed proposition/synthesis outcome

### Exit criteria

- One source can contribute differently to multiple propositions.
- One synthesis can have different conclusions/certainty for different outcomes.
- EML3 replication evidence can be evaluated at proposition level.
- Body-level EML no longer depends on the highest source-level EML.

**Status:** `NOT STARTED`

---

## Stage 9 — Normalise population, context and application lenses

**Goal:** Enable defensible cross-domain matching.

### Population facets

At minimum support:

```text
life stage
role
health/condition context
baseline cognitive status
education level
setting
country/region where relevant
delivery context
inclusion criteria
```

### Implement

- Controlled population/context identifiers with retained free-text summaries.
- Separate role from health status and life stage.
- Keep application/demand family as a separate many-to-many lens.
- Add explicit context-fit/boundary metadata for later CSI matching.

### Exit criteria

- `healthy university students` cannot collapse simply to `adults`.
- Evidence can be filtered across education, work, healthy ageing, longevity and condition-related contexts without overgeneralisation.

**Status:** `NOT STARTED`

---

## Stage 10 — Add harms, fidelity, Bridge dependence, boundaries and implementation

**Goal:** Support EML5–EML7 and safe expansion into near-clinical / health-adjacent evidence.

### Harms / adverse outcomes

Support where applicable:

```text
harm_type
severity
systematic_assessment
withdrawal_due_to_harm
serious_adverse_event
performance_tradeoff
psychological_worsening
fatigue_or_burden
loss_of_autonomy_or_dependency
```

### Implementation / boundaries

Support:

```text
protocol fidelity
adherence
provider
materials/procedures
delivery mode
tailoring
modifications
prompt dependence
boundary conditions
implementation burden
cost/resources where relevant
```

### Exit criteria

- EML6/7 requirements can be represented structurally rather than buried in notes.
- Absence of harms reporting is distinguishable from evidence of no harm.
- Bridge evidence can distinguish scaffolded from unsupported real-world use.

**Status:** `NOT STARTED`

---

## Stage 11 — Add extraction/adjudication provenance and deterministic review→release authority

**Goal:** Make large-scale AI-assisted evidence processing auditable and prevent Git/Postgres authority drift.

### Scientific lifecycle

```text
DISCOVERED
→ SCREENED
→ STAGED
→ MACHINE / AI PRE-EXTRACTED
→ HUMAN REVIEWED
→ APPROVED SOURCE VERSION
→ RELEASE EXPORT
→ GIT DIFF + MANIFEST
→ IMMUTABLE RELEASE
→ CSI GATEWAY PUBLICATION
```

### Field-level provenance for scientifically consequential coding

Track, where justified:

```text
value
extraction_method
model/tool version
prompt/schema version
extracted_on
confidence
reviewer
review decision
corrected value
approval state
```

Priority fields:

- route;
- target;
- mechanism;
- population/context;
- comparator;
- outcome;
- effect estimate;
- transfer;
- harm;
- risk of bias;
- Bridge independence;
- EML contribution;
- synthesis inclusion/exclusion.

### Authority model

```text
Supabase / Workbench
= active reviewed scientific state

GitHub
= schema, taxonomy, code, protocols, migration history,
  deterministic approved release exports and immutable audit snapshots

CSI Gateway
= downstream approved publication boundary
```

A historical Git seed file must never be able to overwrite a later approved Workbench correction without an explicit version/release operation.

### Exit criteria

- Every automated extraction can be traced to tool/model/schema version.
- Reviewer corrections survive future reprocessing.
- Approved release export is deterministic and reproducible.
- Agent runs can write only to staging/proposal state by default.

**Status:** `NOT STARTED`

---

## Stage 12 — Backfill the 18-source seed, parity-test and publish the first v1.1 release

**Goal:** Prove the new model before scaling ingestion.

### Implement

- Map all 18 current sources into canonical source/version structure.
- Backfill target/mechanism/population/outcome fields as far as source evidence permits.
- Add explicit extraction-completeness/missingness states.
- Encode arms/contrasts where needed.
- Populate transfer/delay/Bridge fields where legitimately supported.
- Add effect estimates where extractable.
- Conduct initial formal quality appraisal on priority direct-intervention studies.
- Create at least one test evidence proposition/synthesis workflow without overstating maturity.
- Export a new immutable evidence release.
- Keep `2026-08-23` unchanged.

### Required parity tests

For current CSI consumers:

```text
same seed source set remains reconstructable
same current Gateway release remains available
same claim boundary remains study_level_only
same EML record-contribution semantics remain recoverable
same route/product relevance caveats remain reproducible
```

### Exit criteria

- All v1.1 validators pass.
- Workbench supports all mandatory scientific fields.
- Supabase security/performance advisors reviewed.
- Existing CSI Gateway v1 consumers remain operational.
- New release has an immutable manifest + schema/taxonomy versions + source-version membership.
- Only after this gate may large-scale ingestion begin.

**Status:** `NOT STARTED`

---

# 6. Workbench development rule

The scientific schema governs the Workbench, not vice versa.

The intended reviewer hierarchy should eventually make this visible:

```text
SOURCE
│
├── STUDY
│
├── POPULATION
│
├── ARM A
│   ├── component
│   ├── route
│   ├── target
│   └── mechanism
│
├── ARM B
│
├── CONTRAST
│   └── OUTCOME
│       ├── effect
│       ├── transfer
│       ├── time
│       └── harm
│
├── QUALITY
│
└── PROPOSITIONS CONTRIBUTED TO
```

Free-text entry should be retained for nuance, but controlled scientific dimensions should use validated identifiers/selectors wherever possible.

---

# 7. NiPoGi / Ubuntu execution model

The NiPoGi should function as the persistent **HRP Transfer Lab orchestration node**, not as the sole source of truth.

```text
WINDOWS WORKSTATION
interactive development + review
        │
        │ GitHub
        ▼
UBUNTU NiPoGi
persistent orchestration
literature discovery
screening / deduplication
pre-extraction
validation
scheduled research agents
local cache / restricted corpus where appropriate
        │
        ▼
SUPABASE HRP-TRANSFER-EVIDENCE
active reviewed scientific Registry
        │
        ▼
APPROVED RELEASE EXPORT
        │
        ├── Git immutable snapshot / manifest
        └── CSI Evidence Gateway
```

### NiPoGi setup principle

Start lean:

```text
Ubuntu
Git + GitHub CLI
Python 3 + uv
Node.js
Docker + Docker Compose
PostgreSQL client
Supabase CLI
tmux
systemd timers/services
research-platform repo
```

Do not introduce Kubernetes/Airflow or a heavyweight agent framework until the simple orchestration model is demonstrably inadequate.

### OpenAI API boundary

An OpenAI API key is **not required** to implement Stages 1–12 of the Registry schema itself.

It becomes useful for the later automated pipeline:

```text
screening
semantic classification
structured pre-extraction
scientific critique
```

LLM output remains candidate evidence until human review.

---

# 8. Migration and deployment policy

1. Design and test schema changes on the `evidence-registry-v1.1` branch.
2. Do not hand-edit historical production migration files.
3. Create new migration(s) for v1.1 changes.
4. Prefer additive/backwards-compatible migration stages before destructive cleanup.
5. Verify RLS/grants/views/functions after each DDL stage.
6. Run Supabase security and performance advisors after DDL changes.
7. Preserve `security_invoker` on exposed views.
8. Keep raw Registry tables unavailable to ordinary CSI browser clients.
9. Verify the Gateway against its machine-readable contract after every relevant change.
10. Do not publish a new evidence release automatically merely because schema migration succeeds.

---

# 9. Validation gates after every stage

Every stage should record:

```text
implementation commit
schema/taxonomy version
migration ID(s), if any
tests run
seed-data parity result
Gateway compatibility result
Workbench result
security/advisor result
remaining known gaps
next stage
```

A stage is not complete merely because code compiles.

Where relevant verify:

- migration replay on a clean database;
- deterministic seed transformation;
- duplicate prevention;
- foreign-key integrity;
- controlled taxonomy validation;
- missingness semantics;
- RLS and permissions;
- Workbench typecheck/build;
- Registry validators;
- CSI Gateway validator;
- release immutability.

---

# 10. Progress tracker

Update this table as implementation proceeds.

| Stage | Description | Status | Evidence / commit |
| --- | --- | --- | --- |
| 1 | Freeze route semantics | VERIFIED | `docs/STAGE_1_ROUTE_SEMANTICS_VERIFICATION.md`; `bf639c3`; migration `20260826212614` |
| 2 | Canonical source/version/release identity | VERIFIED | `docs/STAGE_2_SOURCE_IDENTITY_VERIFICATION.md`; `fb9e79a`; migration `20260826215834` |
| 3 | Demand/target/mechanism ontology | IN PROGRESS | `docs/STAGE_3_TARGET_MECHANISM_APPLICATION_IMPLEMENTATION.md` |
| 4 | Orthogonal outcome/transfer/time architecture | NOT STARTED | — |
| 5 | Study arms and contrasts | NOT STARTED | — |
| 6 | First-class effect estimates | NOT STARTED | — |
| 7 | Correct quality/RoB/GRADE units | NOT STARTED | — |
| 8 | Evidence propositions and synthesis outcomes | NOT STARTED | — |
| 9 | Normalised population/context | NOT STARTED | — |
| 10 | Harms/fidelity/boundaries/implementation | NOT STARTED | — |
| 11 | Provenance + deterministic review/release pipeline | NOT STARTED | — |
| 12 | 18-source backfill + parity + v1.1 release | NOT STARTED | — |

Allowed status values:

```text
NOT STARTED
IN PROGRESS
BLOCKED
IMPLEMENTED
VERIFIED
```

Use `VERIFIED` only after the stage exit criteria and relevant validation gates pass.

---

# 11. Current baseline to preserve

Current approved seed baseline:

```text
release_id: 2026-08-23
taxonomy: iqm-route-v0.2
sources: 18
studies: 18
intervention components: 13
outcomes: 38
EML assessments: 18 provisional record contributions
quality assessments: 0
syntheses: 0
approved claims: 0
Gateway contract: csi-evidence-v1
body-level claim boundary: study_level_only
```

Verified v1.1 layers now also preserve:

```text
Stage 1 canonical route semantics: VERIFIED
canonical sources: 18
source versions: 18
release source-version memberships: 18
legacy source aliases: 18
```

Known baseline gaps that v1.1 is designed to address:

```text
target_level: 0/13
transfer axes: 0/38
Bridge evidence level: 0/38
prompt status: 0/13
functional domain: 0/38
effect estimate: 1/38
formal quality appraisal: 0
evidence synthesis: 0
approved claims: 0
```

These zeros are not negative scientific findings; in most cases they reflect incomplete extraction/structure.

---

# 12. Resume-here instructions for a new machine or new ChatGPT/Codex session

When resuming this work:

```bash
git clone https://github.com/HRP-Transfer-Lab/research-platform.git
cd research-platform
git fetch --all
git checkout evidence-registry-v1.1
git pull
```

Then read, in this order:

```text
1. docs/EVIDENCE_REGISTRY_V1_1_IMPLEMENTATION_PLAN.md   ← this file
2. docs/STAGE_1_ROUTE_SEMANTICS_VERIFICATION.md
3. docs/STAGE_2_SOURCE_IDENTITY_VERIFICATION.md
4. docs/STAGE_3_TARGET_MECHANISM_APPLICATION_IMPLEMENTATION.md
5. docs/EVIDENCE_REGISTRY_ARCHITECTURE.md
6. docs/EVIDENCE_MATURITY_LEVELS.md
7. docs/CSI_EVIDENCE_GATEWAY.md
8. components/evidence-registry/schema/taxonomy.v1.1.json
9. supabase/migrations/ latest migration files
```

Before making changes:

1. Inspect the progress tracker in this document.
2. Inspect the latest commits on `evidence-registry-v1.1`.
3. Do not repeat a stage marked `VERIFIED` unless a regression is found.
4. Continue from the first `NOT STARTED`, `IN PROGRESS` or `BLOCKED` stage.
5. Preserve the non-negotiable compatibility rules above.

### Immediate next action

The active implementation task is:

> **Stage 3 — create the neutral Demand/Application Family × target locus × target construct × mechanism ontology, with explicit missingness and optional Trident-G/APC/H-AGI/CSI mappings, while preserving Stage 1, Stage 2 and `csi-evidence-v1` invariants.**

---

# 13. Definition of v1.1 programme completion

The v1.1 programme is complete when:

- the 12 stages above are `VERIFIED`;
- the full 18-source seed is represented in the new model without loss of provenance;
- route, outcome, transfer, timing and evidence role are orthogonal;
- arms, contrasts and effect estimates support quantitative evidence extraction;
- quality appraisal attaches to the correct result/body units;
- EML is proposition/body-aware while preserving source-contribution ratings;
- population/context matching is structured enough for diverse CSI verticals;
- harms, fidelity, Bridge independence and implementation boundaries are representable;
- automated extraction has auditable provenance and cannot self-approve;
- the Workbench can review the mandatory v1.1 fields;
- release export is deterministic and immutable;
- current CSI Gateway consumers remain reproducible;
- a new v1.1 evidence release can be approved and published without mutating the historical `2026-08-23` seed;
- the system is ready for controlled expansion toward a much larger literature corpus.

The governing rule remains:

> **Build the evidence architecture before scaling the evidence volume.**
