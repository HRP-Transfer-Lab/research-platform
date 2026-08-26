# Local Evidence Registry Reproducibility Baseline

**Status:** VERIFIED  
**Date:** 26 August 2026  
**Branch:** `evidence-registry-v1.1`  
**Baseline replay commit:** `a54f535`  
**Durable bootstrap helper:** `components/evidence-registry/scripts/bootstrap_local_registry.py`

## Purpose

This document records the clean-room baseline established on the Ubuntu NiPoGi development node before Registry v1.1 scientific schema changes begin.

## Verified local environment

- Ubuntu development node configured.
- GitHub authentication working.
- Repository cloned at `~/hrp-lab/research-platform`.
- Branch `evidence-registry-v1.1` checked out and clean.
- Docker Engine and Docker Compose working.
- Supabase CLI `2.116.0` installed.
- `uv` installed.
- Local Supabase configured by `supabase/config.toml`.
- `auto_expose_new_tables = false` to match the hosted evidence project posture.
- Local seed execution disabled in `config.toml`; Registry release bootstrap is explicit.
- Local published Docker ports verified as bound to `127.0.0.1`.

## Replay-safety defect found and fixed

A clean local replay originally failed at migration:

`20260823230820_add_hrp_evidence_maturity_v1.sql`

Reason: the migration inserted 18 source-level EML assessments before the 18 evidence sources existed in a fresh database. Production had already loaded those sources when the migration originally ran.

The Git migration was made replay-safe while retaining the deployed migration version. The EML seed mapping now inserts only when the referenced source exists.

This follows the existing repository principle of preserving hosted migration identities while keeping the Git migration chain replayable from an empty database.

## Migration replay baseline

All 12 historical migrations replay locally:

- `20260823174214`
- `20260823174605`
- `20260823174724`
- `20260823175100`
- `20260823181717`
- `20260823181810`
- `20260823182520`
- `20260823201955`
- `20260823202036`
- `20260823230820`
- `20260823231422`
- `20260823235517`

## Deterministic local bootstrap

The durable helper:

```text
components/evidence-registry/scripts/bootstrap_local_registry.py
```

rebuilds the approved `2026-08-23` seed release into the running local Supabase/Postgres instance by:

1. validating the Git release and Gateway contract;
2. creating/updating the local evidence release row;
3. importing all 18 reviewed JSON records through `private.import_evidence_record`;
4. restoring the 18 source-level provisional EML mappings from the historical EML migration;
5. rebuilding the current CSI Gateway seed publication using the historical Gateway migration SQL;
6. projecting EML onto the Gateway cards; and
7. failing unless exact baseline counts are reproduced.

It is local-only by design. It does not call `supabase link`, `db push`, any `--linked` command, or require production credentials.

## Required verified counts

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

Existing file validators must also pass:

```text
REGISTRY VALID: 18 records; release=2026-08-23; taxonomy=iqm-route-v0.2
CSI EVIDENCE GATEWAY CONTRACT PASS
```

## Reproducibility command

With the local Supabase stack running:

```bash
python3 components/evidence-registry/scripts/bootstrap_local_registry.py
```

Expected final line:

```text
LOCAL REGISTRY BASELINE PASS
```

## Authority boundary

The local bootstrap remains:

```text
Git approved release JSON
→ local Supabase/Postgres
→ regression verification
```

It must never require:

```text
supabase link
supabase db push
--linked operations
production credentials
```

## Baseline gate decision

**Reproducibility gate: VERIFIED.**

Registry v1.1 scientific schema work may now begin, subject to the invariant that the bootstrap continues to reproduce the baseline after every relevant stage.

## Next execution checkpoint

Proceed to **Stage 1 — Freeze intervention-route semantics**.

Stage 1 is not complete unless:

- only the seven canonical intervention routes occupy the route vocabulary;
- mechanism/measurement/observational/controller categories remain representable through separate dimensions;
- the historical `2026-08-23` seed remains reconstructable;
- the current `csi-evidence-v1` public release remains backward compatible; and
- the local bootstrap still reports the exact baseline counts above.