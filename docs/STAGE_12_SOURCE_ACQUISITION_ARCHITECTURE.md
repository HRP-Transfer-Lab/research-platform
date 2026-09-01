# Stage 12 — Source Acquisition and Document Artifact Architecture

**Status:** IMPLEMENTED — local verification pending  
**Date:** 1 September 2026  
**Branch:** `evidence-registry-v1.1`

## Purpose

Make source access/retrieval a first-class part of the Registry ingestion pipeline without confusing access with scientific evidence quality.

The governing separation is:

```text
SOURCE IDENTITY / VERSION
        ↓
SOURCE ACQUISITION
        ↓
DOCUMENT ARTIFACT
        ↓
DETERMINISTIC PARSING
        ↓
AI CANDIDATE EXTRACTION
        ↓
HUMAN SCIENTIFIC REVIEW / AUTHORITY
        ↓
RELEASE
```

Acquisition state is operational. It is **not**:

```text
study quality
risk of bias
GRADE/body certainty
EML
scientific authority
claim approval
release publication
CSI Gateway state
```

A paywall or unavailable university-library copy says nothing about scientific quality. Conversely, possessing a PDF does not approve any extracted scientific claim.

## Scientific identity boundary

Acquisition attaches to `source_version`, not `evidence_source` and not directly to a public release card.

This preserves the v1.1 identity model:

```text
canonical_source
    ↓
source_version
    ↓
source acquisition / document artifacts
```

A later author manuscript, publisher version or corrected report may therefore have its own acquisition history without rewriting the canonical publication identity.

## First-class operational objects

### `source_acquisition_status`

One current acquisition snapshot per `source_version`.

Controlled access states:

```text
unknown
metadata_only
abstract_only
fulltext_available
fulltext_verified
blocked
retrieval_failed
```

Routes include:

```text
open_access
repository
author_preprint
publisher
institutional_library
user_supplied
manual_web
other
```

Blockers include:

```text
paywall
institutional_unavailable
not_found
login_required
technical_failure
license_restricted
other
```

The row also records whether full text has been verified, whether supplement/protocol/registration material is available, whether human access help is required, retry timing and operational notes.

### `source_acquisition_attempt`

Append-only attempt history. Each attempt has a deterministic `attempt_key`, requested artifact, channel, outcome, access route and blocker where relevant.

No authenticated update/delete path is exposed. A later retry is a new attempt rather than a rewrite of the earlier event.

The table must never contain:

```text
university passwords
session cookies
publisher credentials
API secrets
library proxy tokens
```

### `source_document_artifact`

Inventory of acquired source material:

```text
full_text
supplement
protocol
sap
registration_record
other
```

Where the binary is locally persisted, the artifact can carry SHA-256, byte size, media type and page count. Storage metadata points to the controlled corpus location; it does not place licensed PDFs in Git.

## Current seed acquisition facts

The deterministic Stage 12 acquisition seed records three facts already established during appraisal work:

```text
rt-2026-004  blocked / institutional_library / institutional_unavailable
rt-2026-005  blocked / institutional_library / institutional_unavailable
rt-2026-014  fulltext_available / user_supplied
```

For `rt-2026-014`, the user-supplied August 2026 EdWorkingPaper PDF is 73 pages and identifies AEA RCT Registry trial `AEARCTR-0018678`. The artifact is registered as available, but it remains `fulltext_verified=false` until the binary is persisted on the ingestion host and SHA-256 registered.

The other 15 seed source versions remain `unknown` until an explicit acquisition check is recorded. We deliberately do not infer full-text availability from the fact that earlier rapid review could access abstracts, web pages or snippets.

## NiPoGi / local ingestion workflow

The acquisition layer is designed to support a low-cost local pipeline:

```text
Crossref / OpenAlex / PubMed metadata
        ↓
Unpaywall / Europe PMC / repository resolution
        ↓
source_acquisition_attempt
        ↓
source_acquisition_status
        ↓
PDF / supplement / protocol artifact
        ↓
SHA-256 + artifact metadata
        ↓
GROBID / Docling / deterministic parser
        ↓
local LLM candidate extraction
        ↓
schema / consistency validation
        ↓
human or high-capability-cloud escalation where required
        ↓
scientific_field_candidate / adjudication / authority
```

Deterministic services should handle DOI resolution, deduplication, OA lookup, file hashing and parsing where possible. Local LLM inference should be reserved for semantic extraction/classification rather than used as an expensive substitute for metadata APIs.

## Local document registration

When a source binary is placed on the ingestion machine, use:

```text
components/evidence-registry/scripts/register_source_document.py
```

The utility:

1. resolves the reviewed `source_version` from the legacy source ID;
2. computes SHA-256 and byte size;
3. obtains PDF page count via `pdfinfo` when available;
4. appends an acquisition attempt;
5. registers/updates the artifact metadata;
6. marks full text verified when `artifact_kind=full_text`;
7. verifies that scientific revision, historical release and CSI Gateway state did not change.

It does **not** copy the document into Git.

## Workbench security

- Acquisition tables use RLS and existing Workbench roles.
- viewers can read;
- editors/owners can update current status and artifacts;
- attempts are append-only for authenticated users;
- `v_source_acquisition_dashboard` uses `security_invoker=true` so caller RLS is preserved.
- access/licensing/storage metadata is internal Workbench state and is not projected automatically into the CSI Gateway.

## Scale metrics enabled by this layer

At 100–1,000 sources we can measure:

```text
full text acquisition rate
open-access resolution rate
institutional/manual escalation rate
retrieval failure rate
mean acquisition attempts per source
percentage with supplement/protocol/registration
percentage locally hashed/verified
papers ready for semantic extraction
papers blocked awaiting human access
```

This makes sourcing effort visible and allows the system to prioritize manual library work only where automated/open routes fail.

## Release boundary

Acquisition metadata is not a reason to mutate the immutable `2026-08-23` release or `csi-evidence-v1`.

For v1.1, source acquisition is primarily an internal Workbench/ingestion concern. Any future release export of acquisition metadata should be explicitly designed and redacted so institutional routes, local storage paths and licensing information are not exposed through public CSI contracts.
