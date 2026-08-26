# Evidence Registry v1.1 — Stage 2 Verification

**Stage:** 2 — Canonical source identity, reviewed source versions and release membership  
**Status:** VERIFIED  
**Date:** 26 August 2026  
**Branch:** `evidence-registry-v1.1`  
**Implementation commit:** `fb9e79a80e3c222c07b246d3116a147603726464`  
**Migration:** `20260826215834_evidence_registry_v1_1_source_identity.sql`

## Decision

Stage 2 is verified.

The Registry now separates:

```text
CANONICAL SOURCE
what publication/report is this?
        ↓
SOURCE VERSION
which reviewed/extracted representation is this?
        ↓
RELEASE MEMBERSHIP
which immutable evidence release contains that reviewed version?
```

The historical `evidence_source` table remains as a backward-compatible release/snapshot surface during the v1.1 migration programme.

## Implemented

- `canonical_source`
- `canonical_source_identity`
- `source_version`
- `release_source_version`
- deterministic legacy ID mapping
- DOI / PMID / arXiv / canonical URL / legacy-source aliases
- identifier normalisation helper
- insert-time compatibility sync for clean replay
- approved source-version immutability guard
- approved release-membership immutability guard
- Workbench-readable RLS policies with no new anonymous exposure
- audit coverage
- `validate_stage2_identity.py`
- Stage 2 validation integrated into `bootstrap_local_registry.py`

## Seed mapping invariant

For the historical seed:

```text
rt-2026-001
      ↓
cs-rt-2026-001
      ↓
sv-rt-2026-001-v1
      ↓
release 2026-08-23
```

The same deterministic rule applies across all 18 seed sources.

## Verified counts

```text
canonical sources        18
source versions          18
release memberships      18
legacy source aliases    18
```

All historical `evidence_source` records map to exactly one seed canonical source/version/release membership.

## Identity integrity

Verified:

```text
sources without canonical identity             0
canonical sources without a version             0
canonical sources without exactly one seed v1   0
invalid seed version identity                    0
invalid release-record mapping                   0
duplicate external identities                    0
release-membership / legacy-alias mismatch       0
```

The identifier uniqueness rule prevents a DOI/PMID/arXiv/normalised URL identity from silently belonging to two canonical sources.

## Immutability verification

Both guards passed explicit mutation tests:

```text
approved source version mutation       BLOCKED
approved release membership mutation   BLOCKED
```

A correction to a released source must therefore create a later source version rather than silently modifying the reviewed version pinned to the historical release.

## Regression evidence

The deterministic local bootstrap continued to pass and now includes Stage 2 identity validation.

The following earlier guarantees remain intact:

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

Stage 1 semantics remain valid, the historical `2026-08-23` Registry validator remains valid, the CSI Gateway v1 contract remains valid, and the Evidence Workbench production build remains successful.

## Compatibility decision

- `2026-08-23` remains immutable.
- Existing `rt-2026-*` source IDs remain recoverable.
- `evidence_source` is not destructively replaced in Stage 2.
- `csi-evidence-v1` remains unchanged.
- No production Supabase mutation was required for local Stage 2 verification.

## Next stage

Proceed to **Stage 3 — normalise Demand/Application Family, target, target locus and mechanism**.
