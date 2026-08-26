# Evidence Registry v1.1 — Stage 2 Source Identity and Versioning

**Status:** IN PROGRESS  
**Date:** 26 August 2026  
**Branch:** `evidence-registry-v1.1`

## Goal

Separate scientific source identity from reviewed/extracted source versions and from evidence-release membership.

Stage 2 establishes the durable distinction:

```text
CANONICAL SOURCE
What publication/report is this?
        ↓
SOURCE VERSION
Which reviewed/extracted representation of it is this?
        ↓
RELEASE MEMBERSHIP
Which immutable Evidence Registry release contains that reviewed version?
```

The current `evidence_source` table remains in place during Stage 2 as a backward-compatible legacy/release snapshot surface. It is not destructively replaced.

## 1. Why this is necessary

The current v1.0 model makes `evidence_source` simultaneously carry:

- publication/report identity;
- reviewed extraction state;
- release membership; and
- historical card identity.

That works for one 18-source seed release but becomes unsafe when:

- the same paper belongs to multiple releases;
- a reviewer corrects an extraction later;
- DOI/metadata are reconciled after ingestion;
- AI-assisted re-extraction creates a candidate revision;
- a later release should contain a corrected reviewed version without mutating an earlier release.

The rule for v1.1 is:

> **A scientific publication is persistent. Its reviewed representation is versioned. A release points to a specific reviewed version.**

## 2. Target relational model

```text
canonical_source
│
├── canonical_source_identity
│   ├── doi
│   ├── pmid
│   ├── arxiv
│   ├── canonical_url
│   └── legacy_source_id
│
└── source_version
    ├── version_number
    ├── reviewed bibliographic/extraction state
    ├── review status
    ├── raw reviewed record
    └── supersedes_source_version_id
           │
           └── release_source_version
               ├── release_id
               ├── source_version_id
               └── release_record_id
```

`release_record_id` preserves the historical release-local identifier such as `rt-2026-001` without making that identifier the canonical publication identity.

## 3. Canonical source

Create:

```text
canonical_source
- canonical_source_id
- preferred_title
- source_status
- created_at
- updated_at
```

### ID policy

`canonical_source_id` is an internal stable text identifier, not a DOI and not a content hash.

For the historical seed, use deterministic compatibility IDs derived from the existing source IDs, for example:

```text
rt-2026-001 → cs-rt-2026-001
```

This makes clean local replay deterministic.

Future ingestion may allocate new internal canonical IDs before or after external identifiers are reconciled. DOI/PMID/etc. remain identities/aliases, not primary keys.

## 4. Canonical identities / aliases

Create:

```text
canonical_source_identity
- canonical_source_id
- identity_scheme
- identity_value
- normalized_value
- is_primary
- created_at
```

Initial controlled schemes:

```text
doi
pmid
arxiv
canonical_url
legacy_source_id
```

Requirements:

- globally prevent the same normalized strong identifier from silently mapping to two canonical sources;
- retain original identity text as well as normalized form;
- treat DOI matching case-insensitively and strip common DOI URL/prefix forms during ingestion code;
- do not assume URL equality alone proves scientific identity when a stronger identifier conflicts;
- preserve legacy `rt-...` IDs as aliases for reproducibility.

The database migration will backfill the already-reviewed values; richer reconciliation logic belongs in the later ingestion pipeline.

## 5. Source version

Create:

```text
source_version
- source_version_id
- canonical_source_id
- version_number
- version_status
- title
- authors
- publication_year
- publication_date
- venue
- source_kind
- peer_review_status
- doi
- pmid
- arxiv_id
- source_url
- review_status
- method_extraction_status
- route_rationale
- raw_record
- supersedes_source_version_id
- created_at
- approved_at
```

### Version invariant

```text
unique(canonical_source_id, version_number)
```

A later correction must create a new version rather than silently mutate a version already referenced by an immutable approved release.

For the seed backfill:

```text
source_version_id = sv-rt-2026-001-v1
version_number    = 1
version_status    = approved_seed
```

## 6. Release membership

Create:

```text
release_source_version
- release_id
- source_version_id
- release_record_id
- release_position
- membership_status
- added_at
```

Constraints:

```text
primary key (release_id, source_version_id)
unique (release_id, release_record_id)
```

A canonical paper can therefore appear in multiple releases, and different releases can point to different reviewed versions of the same canonical source.

## 7. Existing `evidence_source` compatibility

During Stage 2:

- do not drop `evidence_source`;
- do not change the historical `source_id` values;
- do not alter the existing Gateway card IDs;
- do not mutate `2026-08-23` JSON;
- do not make the Workbench suddenly depend on the new tables before parity is established.

The old table becomes a compatibility/release snapshot while the new identity model is introduced alongside it.

A future stage may deliberately move operational review authority from `evidence_source` to `source_version`; Stage 2 only creates the correct identity foundation.

## 8. Backfill strategy

The Stage 2 migration must work in both environments:

### Hosted existing-data environment

The 18 `evidence_source` rows already exist when the migration runs.

The migration should backfill all 18 immediately.

### Clean local replay

The Stage 2 migration runs before `bootstrap_local_registry.py` imports the 18 sources.

Therefore Stage 2 must provide a deterministic local compatibility sync function and an insert-time trigger so later imported historical rows create:

```text
18 canonical_source rows
18 source_version rows
18 release_source_version rows
identity aliases/identifiers
```

The compatibility function must be idempotent.

It must not rewrite already released source versions on ordinary later `evidence_source` updates.

## 9. Identity backfill rules for the 18-source seed

For each legacy `evidence_source`:

```text
canonical_source_id = 'cs-' || source_id
source_version_id   = 'sv-' || source_id || '-v1'
version_number      = 1
release_record_id   = source_id
```

Backfill available identities:

- always `legacy_source_id`;
- DOI when present;
- PMID when present;
- arXiv ID when present;
- canonical/source URL.

No probabilistic title/author deduplication is performed by the migration.

## 10. Immutability guard

Stage 2 should make it difficult to mutate a version already linked to an approved release.

Preferred initial rule:

- source versions referenced by `approved_seed` / `approved_release` release membership are treated as immutable reviewed snapshots;
- corrections create a new `source_version` row;
- the old release membership remains pinned to its original source version.

The exact enforcement mechanism may be a trigger/function plus Workbench restrictions, but must remain compatible with the historical bootstrap.

## 11. RLS / Workbench policy

All new public-schema tables require RLS.

Workbench access model:

```text
viewer  → read canonical source/version/membership
editor  → create/review candidate source versions where allowed
owner   → identity reconciliation / release membership administration
```

Stage 2 may initially expose the new tables read-only in the Workbench while write workflow is designed more fully in Stage 11.

No `anon` access is required.

## 12. Gateway compatibility

`csi-evidence-v1` remains unchanged during Stage 2.

Gateway evidence cards continue to use their current historical/release-local IDs.

The new identity model lives behind the Gateway until a future contract deliberately exposes canonical source/version identity.

## 13. Stage 2 verification targets

After migration + bootstrap:

```text
canonical sources            18
source versions              18
release memberships          18
legacy_source_id aliases     18
```

Also verify:

- each `evidence_source` maps to exactly one seed canonical source;
- each seed canonical source has exactly one v1 source version;
- each seed source version belongs to release `2026-08-23`;
- DOI/PMID/arXiv duplicates are not introduced;
- historical Gateway remains 18 cards / 0 claims;
- existing Stage 1 semantic distributions remain unchanged;
- deterministic local bootstrap still passes;
- historical Registry validator still passes;
- Stage 1 semantic validator still passes;
- Workbench still builds.

## 14. Stage 2 implementation sequence

1. Generate migration with Supabase CLI.
2. Add canonical source, identity, source-version and release-membership tables.
3. Add RLS/grants/audit coverage.
4. Add deterministic legacy backfill/sync helper.
5. Add insert-time compatibility trigger for clean replay.
6. Backfill existing hosted/local rows idempotently.
7. Add Stage 2 identity validator.
8. Reset/replay local database and bootstrap seed.
9. Verify exact 18/18/18 identity counts and identifier integrity.
10. Verify Stage 1 and Gateway parity.
11. Build Workbench.
12. Commit and record Stage 2 verification evidence.

## Exit criteria

Stage 2 is `VERIFIED` only when:

- publication identity, reviewed version and release membership are separate database objects;
- the same canonical source can support more than one reviewed version;
- releases point to explicit source versions;
- existing 18 source IDs remain recoverable as release-local/legacy identities;
- the historical `2026-08-23` release and `csi-evidence-v1` remain unchanged;
- clean replay plus deterministic bootstrap creates the new identity layer correctly; and
- no large-scale ingestion begins before the identity model is proven.
