# Evidence Registry v1.1 — Stage 3 Verification

**Stage:** 3 — Demand/Application Family, target locus, target and mechanism ontology  
**Status:** VERIFIED  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`  
**Implementation commit:** `0b3f14a75c3e48965c86792c19837f4d959694d6`  
**Migration:** `20260826221551_evidence_registry_v1_1_target_mechanism_application.sql`

## Decision

Stage 3 is verified.

The Registry now separates four scientific dimensions that were previously liable to collapse into one another:

```text
APPLICATION FAMILY
Where may this evidence be useful?
        +
TARGET LOCUS / TARGET
What process, state, representation, policy, coupling or activity-system property is being changed or studied?
        +
MECHANISM
What proposed or tested process may produce the effect?
        +
INTERVENTION ROUTE
How or where does the intervention act?
```

These dimensions remain orthogonal. Application family does not imply product validation; target does not determine route; mechanism evidence does not require an intervention component; and proprietary framework mappings remain separate from neutral scientific ontology identity.

## Implemented

### Application-family layer

- `application_family_definition`
- `source_version_application_family`
- seven broad application families:
  - `mental_fitness`
  - `performance`
  - `learning`
  - `executive_functioning`
  - `wellbeing`
  - `longevity`
  - `condition_related_support`
- many-to-many application mappings with relevance level, rationale, provenance and review status

### Target ontology

- `target_locus_definition`
- `target_definition`
- `target_alias`
- `component_target`
- `component_target_extraction_status`
- explicit target relationship types
- explicit extraction-state semantics
- neutral target identities kept distinct from author terminology and proprietary framework mappings

### Target-locus model

Stage 3 validates eight high-level target loci:

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

The eighth locus, `knowledge_or_mental_representation`, was added after testing the initial ontology against the 18-record seed. Numerical knowledge and abstract relational representations could not be represented cleanly as cognitive operations without category distortion.

### Mechanism layer

- `mechanism_definition`
- `mechanism_assertion`
- `source_version_mechanism_status`
- mechanism assertion types and directions
- mechanism evidence permitted without an intervention component
- mechanism extraction completeness represented explicitly

### Framework-mapping layer

- target and mechanism framework mapping structures
- neutral scientific ontology retained as primary identity
- Trident-G / APC / H-AGI / CSI mappings treated as secondary interpretations rather than external-author terminology

### Review and governance layer

Stage 3 rows support:

```text
mapping_source
review_status
rationale / support summary
updated_at
```

AI candidate annotations use:

```text
mapping_source = agent_candidate
review_status = proposed
```

Human review changes accepted/rejected annotations to:

```text
mapping_source = human_review
review_status = approved | rejected
```

This preserves the invariant that an AI-generated scientific mapping cannot silently approve itself.

## Candidate seed mapping layer

Versioned candidate mapping manifest:

`components/evidence-registry/data/stage3_seed_mappings.v1.json`

Applicator:

`components/evidence-registry/scripts/apply_stage3_seed_mappings.py`

Validator:

`components/evidence-registry/scripts/validate_stage3_seed_mappings.py`

The manifest is deliberately external to the immutable `2026-08-23` release. It is a candidate annotation layer for human review, not a rewritten historical release.

Verified candidate counts:

```text
source versions with application-family proposals   18
application-family links                            32
intervention components with target proposals       13 / 13
component-target links                              17
sources with candidate mechanism assertions          4
mechanism assertions                                 4
agent candidates approved                            0
```

The four conservative mechanism proposals are attached only where the approved seed review explicitly supports a mechanism relationship.

## Ontology counts

The deterministic Stage 3 ontology validator reports:

```text
application families                                 7
target loci                                           8
target definitions                                   20
mechanism definitions                                10
explicit component target status rows                13
explicit source mechanism status rows                18
```

Integrity checks returned zero failures, including the rule that mechanism evidence may legitimately exist without an intervention component.

## Seed mapping verification

The deterministic seed validator reports:

```text
STAGE 3 SEED MAPPINGS VALID
sources=18
application_links=32
target_links=17
mechanism_assertions=4
candidate_target_components=13
candidate_mechanism_sources=4
human_approval_boundary: PASS (0 agent candidates approved)
```

## Permanent replay integration

The local deterministic bootstrap now executes Stage 3 in the following order:

```text
historical seed import
→ Stage 2 identity validation
→ Stage 3 candidate mapping applicator
→ Stage 3 ontology validation
→ Stage 3 seed-mapping / approval-boundary validation
→ LOCAL REGISTRY BASELINE PASS
```

This ordering is required because the historical importer recreates study/component rows during clean replay. Candidate component mappings are therefore reapplied deterministically after import rather than relying on mutable local state.

The final replay passed with:

```text
STAGE 3 CANDIDATE MAPPINGS APPLIED: sources=18; application_links=32; target_links=17; mechanism_assertions=4
STAGE 3 ONTOLOGY VALID: 7 application families / 8 target loci / 13 explicit component target states / 18 explicit source mechanism states
STAGE 3 SEED MAPPINGS VALID: sources=18; application_links=32; target_links=17; mechanism_assertions=4
human_approval_boundary: PASS (0 agent candidates approved)
LOCAL REGISTRY BASELINE PASS
```

## Evidence Workbench review surface

Workbench implementation commits:

- `0e186a401ac5117db24e9ad9ba6549cb1a34ed12` — add Stage 3 ontology review UI
- `0142539a61244d840ef25e5ff409a2bded4584bb` — show Stage 3 ontology review in source detail

The Workbench now exposes separate review surfaces for:

```text
Application Families
Targets / Target Loci
Mechanism Assertions
Extraction Status
Mapping Provenance / Review Status
```

Human reviewers can approve or reject agent proposals or add corrected human-reviewed mappings. Non-intervention / mechanism-only evidence is a valid state and does not require a synthetic route or intervention component.

The local Evidence Workbench production build completed as part of the Stage 3 verification sequence.

## Supabase advisor gate

Local-only advisor command:

```text
supabase db advisors --local --type all --level info --fail-on error
```

Result:

- no `ERROR` findings
- no `WARN` findings
- INFO-level performance observations only
- several foreign-key/index optimisation suggestions
- multiple `unused_index` notices on the freshly rebuilt small local seed database

These INFO findings do not block Stage 3. Unused-index notices are not grounds for deleting indexes from an 18-record freshly reset test database. The unindexed foreign-key observations are retained as future performance-hardening items rather than being folded into the scientific Stage 3 scope.

## Regression evidence

The historical Registry/Gateway baseline remains intact:

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

Stage 1 route/evidence-role semantics remain valid. Stage 2 canonical identity/versioning remains valid. The historical `2026-08-23` release remains reproducible and unchanged.

## Compatibility decision

- `2026-08-23` remains immutable.
- Existing `rt-2026-*` release records remain recoverable.
- Stage 3 is additive to the Registry model.
- `csi-evidence-v1` remains unchanged.
- AI candidate mappings are outside the immutable historical release until human-reviewed and deliberately included in a later release.
- No user/person/session data enter the scientific Registry.
- No production Supabase mutation was required for local Stage 3 verification.

## Stage 3 exit criteria

### All current intervention components can be assigned a target locus or explicit extraction state

**PASS.** All 13 intervention components have explicit target extraction-state rows; the reviewed seed candidate layer supplies target proposals for all 13 components.

### Mechanism evidence can be queried independently of intervention route

**PASS.** Mechanism definitions/assertions and source-version mechanism status are first-class structures. Mechanism-only evidence is valid without an intervention component.

### A single intervention/source can map to several application families without changing route

**PASS.** Application family is many-to-many at source-version level and is independent of intervention-route semantics.

### AI cannot self-approve scientific mappings

**PASS.** Candidate seed validation explicitly confirms `0 agent candidates approved`; Workbench acceptance/rejection changes provenance to `human_review`.

## Next stage

Proceed to **Stage 4 — refactor outcome architecture into orthogonal outcome-distance, time, transfer and outcome-role dimensions**.

Stage 4 should remove the overloaded historical `evidence_rung` semantics while preserving all 38 seed outcomes losslessly and maintaining explicit missingness.
