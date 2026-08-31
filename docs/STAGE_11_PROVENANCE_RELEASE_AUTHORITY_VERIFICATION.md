# Evidence Registry v1.1 — Stage 11 Verification

**Status:** VERIFIED  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`  
**Verified implementation tip:** `5672acefe4a94e026ed1dae020ad2df5bdf30875`

## Scope

Stage 11 establishes the governed authority path for AI-assisted scientific processing:

```text
PROCESSING RUN
→ FIELD CANDIDATE
→ HUMAN ADJUDICATION
→ DURABLE FIELD AUTHORITY
→ RELEASE BUILD
→ DETERMINISTIC VALIDATION + HASHES
→ OWNER APPROVAL
→ GOVERNED PUBLICATION
→ IMMUTABLE RELEASE
```

This layer complements, rather than replaces, the existing normalized scientific tables and `workbench_audit_log`.

## Existing architecture retained

The Stage 11 audit confirmed that the pre-existing Registry already had:

- 78 audited tables;
- 40 tables carrying coarse `mapping_source` / `review_status` provenance;
- immutable released source versions;
- immutable approved release memberships;
- the historical `2026-08-23` approved seed release with 18 source versions.

Stage 11 therefore adds missing authority/provenance objects rather than rebuilding the Registry.

## Migrations

Stage 11 is implemented through:

- `20260831230000_evidence_registry_v1_1_provenance_release_authority.sql`
- `20260831230100_tighten_stage11_authority_guards.sql`
- `20260831230200_tighten_stage11_processing_run_constraints.sql`

## First-class Stage 11 objects

The architecture adds:

- `scientific_processing_run`
- `scientific_field_candidate`
- `scientific_field_adjudication`
- `scientific_field_authority`
- `evidence_release_build`
- `release_build_source_version`
- `release_export_artifact`
- `scientific_state_revision`

## Processing-run provenance

Future machine-assisted extraction can record:

```text
run kind
actor kind
tool/provider/version
model/version
prompt version
extraction schema version
taxonomy version
code commit
input/output manifest hashes
parameters
start/completion state
```

Agent/hybrid runs must identify a tool or model. Terminal run states require `completed_at`.

The historical 18-source seed receives no fabricated model, prompt or confidence metadata.

## Candidate versus authority boundary

A scientific candidate is an append-oriented proposal, not an authoritative value.

Candidates:

- must begin as `proposed`;
- retain immutable payload/provenance;
- cannot be directly converted into scientific authority by an agent;
- can be accepted, rejected, corrected or deferred only through controlled adjudication.

Human adjudication creates durable `scientific_field_authority` records. A later machine run may create a competing candidate but cannot overwrite the active human-reviewed authority.

The local transactional exercise verified:

```text
agent candidate A
→ human correction = authoritative value
→ later agent candidate B
→ authority remains human-corrected value
→ candidate B rejected
→ authority still unchanged
```

This proves reviewer corrections survive later reprocessing.

## Release authority

Stage 11 removes direct release-row mutation as the publication workflow.

Authenticated browser users and `service_role` no longer receive direct insert/update/delete authority over:

- `evidence_release`
- `release_source_version`

New release publication must pass through controlled release-build operations.

The Workbench owner path is:

```text
create build
→ prepare
→ deterministic export / validation
→ approve
→ publish
```

Validation may be performed by service automation, but approval/publication require human owner authority.

The local PostgreSQL compatibility exception is restricted to reconstruction of the historical `2026-08-23` seed release.

## Release-build snapshot

A prepared build pins explicit source-version membership before approval.

The Stage 11 exercise verified:

- 18 source versions pinned;
- stable release positions;
- per-source state hashes;
- scientific-state SHA-256;
- manifest SHA-256;
- deterministic canonical JSON export.

Running the exporter twice against unchanged state produced byte-identical output and identical hashes.

## Scientific-state drift protection

`scientific_state_revision` is advanced by changes to audited scientific-state tables while excluding provenance/build metadata itself.

A release build records the revision used for preparation/validation.

The transactional exercise deliberately changed scientific state after validation and confirmed the build was rejected as stale.

Therefore a validated build cannot be approved/published if the scientific state has changed since validation.

## Transactional publication exercise

The Stage 11 exercise tested the full authority path inside a transaction:

```text
validated build
→ controlled owner approval
→ controlled publication
→ approved release with 18 memberships
→ transaction rollback
```

The test release did not persist.

This proves the publication path without creating a real v1.1 evidence release before Stage 12.

## Direct-write protection

The exercise verified direct `evidence_release` insertion is blocked for both:

- authenticated browser role;
- service role.

Approved release/source-version immutability from Stage 2 remains intact.

## Workbench

Stage 11 updates the Workbench with:

- a release-build cockpit replacing the direct owner release-status selector;
- source-level provenance/candidate review surfaces;
- candidate run/tool/model/prompt/schema metadata;
- accept/reject/correct adjudication controls;
- visibility of current authoritative values.

The Workbench production build passed after these changes.

## Validation results

The Stage 11 schema validator passed with:

```text
STAGE 11 PROVENANCE/RELEASE VALID
historical_provenance_nonfabrication: PASS
machine_candidate_vs_human_authority: PASS
 direct_release_crud_removed: PASS
owner_release_build_rpc_boundary: PASS
service_validation_not_approval: PASS
released_source_version_immutability: PASS
scientific_state_revision_clock: PASS
```

The transactional authority/release exercise passed after the harness JSONB aggregate fix at commit `5672ace`.

The final closure sequence also passed:

- clean local Stage 11 migrations;
- verified Stages 1–10 bootstrap baseline;
- Stage 11 provenance/release validator;
- correction-durability exercise;
- deterministic export/hash exercise;
- drift invalidation test;
- transactional controlled publication test;
- Workbench production build;
- local Supabase advisor gate with `--fail-on error`.

## Compatibility

Stage 11 does not mutate or publish over:

- immutable release `2026-08-23`;
- its 18 source-version memberships;
- source-level record-contribution EML;
- Stage 1–10 scientific classifications;
- `csi-evidence-v1`.

No real new evidence release is published in Stage 11.

## Verification decision

**Stage 11 is VERIFIED.**

The Registry now has a durable distinction between machine proposals, human-reviewed authority, validated release builds and immutable publication.

The remaining programme stage is:

**Stage 12 — final 18-source backfill/parity review and publication of the first immutable v1.1 evidence release.**
