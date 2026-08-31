# Evidence Registry v1.1 — Stage 11 Provenance, Adjudication and Release Authority

**Status:** IN PROGRESS  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`

## Goal

Make machine-assisted evidence processing auditable and make human-reviewed scientific state durable across reprocessing, while replacing ad-hoc release-row mutation with a deterministic, explicit review → release authority path.

The governing authority model is:

```text
DISCOVERY / EXTRACTION RUN
        ↓
MACHINE CANDIDATE
        ↓
HUMAN ADJUDICATION
        ↓
AUTHORITATIVE REVIEWED SCIENTIFIC STATE
        ↓
RELEASE BUILD
        ↓
VALIDATED EXPORT + HASH
        ↓
OWNER APPROVAL
        ↓
IMMUTABLE RELEASE
        ↓
CSI GATEWAY PUBLICATION
```

Stage 11 is primarily an authority/provenance layer. It must not silently change the scientific classifications established in Stages 1–10.

---

## 1. Existing architecture to preserve

The system already has useful pieces which Stage 11 should build on rather than replace:

### Workbench mutation audit

`workbench_audit_log` records:

```text
actor_user_id
table_name
action
before_row
after_row
occurred_at
```

This is a row-level mutation audit and remains valuable.

It is **not** sufficient field-level scientific provenance because it does not identify:

```text
extraction run
model/tool version
prompt/schema version
candidate confidence
source basis
review decision
candidate corrected value
release-build membership
```

### Stage 2 source/version authority

Stage 2 already establishes:

```text
canonical_source
source_version
release_source_version
```

and protects source versions pinned to approved releases from update/delete. Approved release membership is also immutable.

This remains the core scientific-version identity model.

### Mapping provenance already present

Many Stage 3–10 tables already carry coarse-grained fields such as:

```text
mapping_source
review_status
```

These remain useful operational state but are not a substitute for a first-class extraction/adjudication ledger.

---

## 2. Authority gaps Stage 11 must close

### 2.1 Machine run identity is absent

An `agent_candidate` row currently does not identify the exact run that produced it.

Stage 11 must make it possible to answer:

```text
Which run created this candidate?
Which tool/model generated it?
Which prompt/schema/taxonomy/code version was used?
What source material was used?
What confidence did the extractor report?
```

### 2.2 Human correction durability is implicit rather than first-class

A reviewer may approve, reject or correct candidate state, but there is no generic adjudication object that permanently links:

```text
machine candidate
→ reviewer decision
→ corrected/accepted value
→ authority established
```

Machine reprocessing must produce a **new candidate** rather than overwrite a human-reviewed authority record.

### 2.3 Release authority is too row-oriented

Current Workbench access historically allows an owner to insert/update/delete `evidence_release` directly.

Stage 11 should change the conceptual workflow to:

```text
prepare release build
→ validate build
→ inspect deterministic diff/manifest
→ owner approves build
→ publish/freeze release
```

An approved release should never be created merely by editing a status field.

### 2.4 Git/Supabase authority must be explicit

The intended model is:

```text
Supabase / Workbench
= active reviewed scientific state

GitHub
= schema, taxonomy, code, protocol, migrations,
  deterministic immutable release exports/manifests

CSI Gateway
= downstream publication boundary
```

Git historical seed files must never overwrite later reviewed Workbench corrections except through an explicit version/release operation.

---

## 3. Extraction / processing run model

Create a first-class run object such as:

```text
scientific_processing_run
```

Minimum fields:

```text
processing_run_id
run_kind
actor_kind
status
started_at
completed_at
created_by nullable

provider nullable
tool_name nullable
tool_version nullable
model_name nullable
model_version nullable

prompt_version nullable
extraction_schema_version nullable
taxonomy_version nullable
code_commit_sha nullable

input_manifest_sha256 nullable
output_manifest_sha256 nullable
parameters_json
notes nullable
```

Controlled `run_kind` should support at least:

```text
discovery
screening
pre_extraction
classification
re_extraction
validation
manual_import
release_export
```

Controlled `actor_kind`:

```text
agent
human
system
hybrid
```

Controlled `status`:

```text
started
completed
failed
cancelled
```

An automated run must never itself confer scientific approval.

---

## 4. Candidate-field provenance

Create a generic candidate ledger such as:

```text
scientific_field_candidate
```

The candidate ledger records **proposals**, not authoritative values.

Minimum fields:

```text
field_candidate_id
processing_run_id
subject_kind
subject_key
field_path
candidate_value_json
source_basis
confidence nullable
candidate_status
created_at
supersedes_candidate_id nullable
```

Controlled `subject_kind` should cover scientifically consequential units, for example:

```text
canonical_source
source_version
study
study_arm
intervention_component
study_contrast
outcome
effect_estimate
quality_assessment
proposition
synthesis_outcome
body_certainty
body_eml
harm_observation
support_dependence
boundary_condition
```

`subject_key` should be a stable JSON object or canonical text identity, not an unstable array position.

Examples:

```json
{"source_id":"rt-2026-015"}
{"source_id":"rt-2026-015","component_name":"integrate"}
{"source_id":"rt-2026-015","outcome_name":"independent no-AI writing quality"}
```

Controlled `candidate_status`:

```text
proposed
accepted
rejected
superseded
withdrawn
```

A later run may supersede an older candidate but must not delete scientific history.

---

## 5. Adjudication ledger

Create:

```text
scientific_field_adjudication
```

Minimum fields:

```text
adjudication_id
field_candidate_id
reviewer_user_id
review_decision
reviewed_value_json nullable
rationale nullable
reviewed_at
```

Controlled decisions:

```text
accept
reject
correct
defer
```

Rules:

- `accept` adopts the candidate value.
- `correct` explicitly records a reviewer-supplied corrected value.
- `reject` leaves the current authoritative state unchanged.
- `defer` does not establish authority.

Only authenticated human reviewers may create final adjudications.

---

## 6. Reviewed-field authority / correction protection

Create a durable authority ledger such as:

```text
scientific_field_authority
```

Minimum fields:

```text
authority_id
subject_kind
subject_key
field_path
authoritative_value_json
source_adjudication_id nullable
authority_kind
approved_by nullable
approved_at
superseded_by_authority_id nullable
active
```

Controlled `authority_kind`:

```text
human_review
manual
approved_import
release_snapshot
```

Core invariant:

> A machine run may create a new candidate for a field with active human authority, but it cannot silently overwrite or deactivate that authority.

A correction to authoritative reviewed data creates a later authority record and supersedes the earlier authority record; it does not erase history.

For v1.1, the authority ledger may operate alongside the normalized scientific tables rather than replacing them. The normalized tables remain the queryable scientific state; the authority ledger records why their reviewed value is authoritative.

---

## 7. Applying an adjudicated candidate

Create a controlled server-side apply operation rather than allowing machine clients to write approved scientific rows directly.

Conceptually:

```text
private.apply_scientific_adjudication(...)
```

The operation should:

1. require editor/owner human authority;
2. verify candidate is still `proposed`;
3. record adjudication;
4. apply accepted/corrected value to the appropriate normalized scientific object through a controlled mapping;
5. create/update `scientific_field_authority`;
6. mark candidate accepted/rejected as appropriate;
7. leave full Workbench audit history.

Stage 11 does **not** need to genericise every existing Workbench edit immediately. The critical requirement is that future automated ingestion uses this candidate/adjudication path for scientifically consequential fields.

---

## 8. Protected reviewed state

Machine/service-role ingestion should be governed by a simple rule:

```text
MACHINE
→ may write processing runs
→ may write proposed candidates
→ may write staging/import objects explicitly designated machine-writable
→ may not approve candidates
→ may not supersede human authority
→ may not publish/freeze a release
```

Existing seed-replay scripts remain local deterministic test fixtures, not production machine-ingestion authority.

---

## 9. Release-build state machine

Create a release-build object separate from `evidence_release`, for example:

```text
evidence_release_build
```

Minimum fields:

```text
release_build_id
target_release_id
build_status
schema_version
taxonomy_version
gateway_contract_version
requested_by
requested_at

scientific_state_sha256 nullable
export_manifest_sha256 nullable
export_manifest_json nullable
validation_report_json nullable

git_commit_sha nullable
approved_by nullable
approved_at nullable
published_at nullable
notes nullable
```

Controlled build status:

```text
draft
prepared
validated
approval_pending
approved
published
failed
cancelled
```

Release build state must move forward through controlled functions rather than arbitrary table updates.

---

## 10. Deterministic release snapshot

Create a DB-side snapshot membership layer or manifest object such as:

```text
release_build_source_version
```

Minimum fields:

```text
release_build_id
source_version_id
release_record_id
release_position
source_state_sha256
```

The release build must pin specific `source_version` IDs before approval.

A deterministic exporter in Stage 11/12 should serialize approved scientific state using:

```text
stable ordering
canonical JSON formatting
explicit schema version
taxonomy version
source-version membership
per-record/content hashes
manifest hash
```

Running the exporter twice against unchanged approved state must produce identical hashes/content.

---

## 11. Release authority functions

Use explicit server-side operations conceptually equivalent to:

```text
prepare_release_build
validate_release_build
approve_release_build
publish_release_build
```

### Prepare

May be initiated by owner; captures approved scientific state and source-version membership.

### Validate

Runs structural/integrity validators and records a report. Validation does not publish.

### Approve

Requires human owner authority and a valid prepared/validated build.

### Publish

Creates/finalises the immutable `evidence_release` and `release_source_version` memberships from the approved build.

Publication must reject:

```text
unreviewed source versions
agent-approved scientific candidates
changed scientific-state hash since validation
missing manifest/hash
already-published target release ID
```

Gateway publication should remain a separate downstream step or explicit sub-step, never an accidental effect of saving scientific data.

---

## 12. Direct release-row mutation boundary

Stage 11 should remove ordinary browser CRUD as the conceptual release-authority interface.

Preferred target:

- Workbench users may read `evidence_release`.
- Owners operate release builds through controlled RPC/functions.
- Approved/published releases are immutable.
- Direct update/delete of approved releases is blocked at the database layer.
- Draft historical compatibility may remain readable, but new releases use the governed build path.

The existing `2026-08-23` release remains untouched.

---

## 13. Workbench Stage 11 surfaces

### Provenance / adjudication

For scientifically consequential candidate mappings, display:

```text
candidate value
run kind
model/tool
prompt/schema version
confidence
source basis
human review decision
corrected value where applicable
authoritative current value
```

### Release page

Replace/edit the release workflow with a release-build cockpit:

```text
Build ID
Target release ID
Source versions pinned
Validation state
Scientific-state hash
Manifest hash
Approval state
Git export commit
Publication state
```

Only owners should see approval/publish controls.

---

## 14. Audit strategy

Keep `workbench_audit_log` as the low-level mutation trail.

Stage 11 adds scientific provenance above it:

```text
workbench_audit_log
= who changed which row

scientific_processing_run
= which machine/human process generated proposals

scientific_field_candidate
= what was proposed

scientific_field_adjudication
= how a human reviewed it

scientific_field_authority
= which reviewed value currently governs

release_build
= which approved scientific state was prepared for publication
```

These layers are complementary rather than redundant.

---

## 15. Conservative 18-source seed boundary

The historical seed predates first-class Stage 11 extraction-run provenance.

Do **not** fabricate model/prompt/confidence records for those historical records.

Stage 11 may create a single explicit compatibility provenance marker such as:

```text
run_kind = manual_import
actor_kind = system
notes = historical approved seed; detailed extraction-run metadata not available
```

but only if it is clearly labelled as migration/compatibility provenance.

Existing approved seed source versions remain immutable.

No Stage 11 candidate/adjudication rows need be manufactured for already-reviewed seed classifications.

---

## 16. Validation gates

Stage 11 is not verified until all of the following pass:

### Processing provenance

- processing runs record tool/model/schema identity where applicable;
- machine runs cannot mark candidates approved;
- machine runs cannot create human adjudications;
- historical seed does not receive fabricated model/prompt metadata.

### Correction durability

- a human-reviewed authority value survives a later machine run;
- reprocessing creates a new proposed candidate instead of overwriting authority;
- corrected values retain both original candidate and reviewer correction.

### Release authority

- direct publication by status-field edit is blocked;
- only owner-controlled release-build functions can approve/publish;
- source-version membership is frozen at build approval;
- approved/published builds are immutable;
- changed scientific state invalidates a previously validated build.

### Determinism

- unchanged approved state exports byte-equivalent canonical JSON/manifest;
- manifest/content hashes reproduce exactly;
- release membership ordering is deterministic.

### Compatibility

- `2026-08-23` remains unchanged;
- `csi-evidence-v1` remains operational;
- Stages 1–10 validators remain passing;
- Workbench builds;
- Supabase advisor gate reviewed.

---

## 17. Stage 11 exit criteria

Stage 11 is complete when:

1. every future automated extraction can be traced to a processing run/tool/model/schema identity;
2. candidate values are distinct from human-approved values;
3. reviewer corrections survive later reprocessing;
4. human adjudication establishes durable field authority;
5. automated agents cannot self-approve or supersede human authority;
6. release creation is mediated by an explicit release-build state machine;
7. an approved release build pins source versions and deterministic scientific-state hashes;
8. publication cannot occur when scientific state has drifted since validation;
9. approved releases are immutable;
10. deterministic export produces reproducible manifest/content hashes;
11. Workbench exposes provenance and release-build status clearly;
12. historical seed and Gateway v1 compatibility remain intact.

The next stage after verification is:

**Stage 12 — final 18-source parity/backfill review and publication of the first immutable v1.1 evidence release.**
