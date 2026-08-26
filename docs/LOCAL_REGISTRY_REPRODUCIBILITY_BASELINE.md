# Local Evidence Registry Reproducibility Baseline

**Status:** PASS  
**Date:** 26 August 2026  
**Branch:** `evidence-registry-v1.1`  
**Baseline commit before this document:** `a54f535`  

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
- Local seed execution disabled in `config.toml` until the Registry release bootstrap is made explicit.
- Local published Docker ports verified as bound to `127.0.0.1`.

## Replay-safety defect found and fixed

A clean local replay originally failed at migration:

`20260823230820_add_hrp_evidence_maturity_v1.sql`

Reason: the migration inserted 18 source-level EML assessments before the 18 evidence sources existed in a fresh database. Production had already loaded those sources when the migration originally ran.

The Git migration was made replay-safe while retaining the deployed migration version. The EML seed mapping now inserts only when the referenced source exists.

This follows the existing repository principle of preserving hosted migration identities while keeping the Git migration chain replayable from an empty database.

## Migration replay baseline

All 12 historical migrations now replay locally:

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

## Approved seed corpus baseline

The approved `2026-08-23` release was then loaded into local Postgres through the existing private importer.

Verified counts:

```text
sources          18
studies          18
components       13
outcomes         38
EML assessments  18
```

Existing file validators also pass:

```text
REGISTRY VALID: 18 records; release=2026-08-23; taxonomy=iqm-route-v0.2
CSI EVIDENCE GATEWAY CONTRACT PASS
```

## Important additional reproducibility requirement

On a clean migration replay, the CSI Gateway schema is created before the 18 source records are loaded. Therefore the original Gateway publication statements do not create the 18 local evidence cards during migration replay.

Before Stage 1 is considered fully regression-ready, the local bootstrap must also recreate and verify:

```text
CSI Gateway releases   1
CSI Gateway cards      18
CSI Gateway claims      0
```

and project the 18 source-level EML mappings onto those local Gateway cards.

## Authority boundary

The local bootstrap must remain local-only:

```text
Git approved release JSON
→ local Supabase/Postgres
→ regression verification
```

It must not require:

```text
supabase link
supabase db push
--linked operations
production credentials
```

## Next execution checkpoint

1. Add a durable `bootstrap_local_registry.py` helper under `components/evidence-registry/scripts/`.
2. Make it load the approved release, import the 18 records, restore EML mappings, rebuild the local Gateway seed publication, and verify exact counts.
3. Run it successfully on the NiPoGi.
4. Commit and push the bootstrap helper.
5. Mark the reproducibility baseline complete.
6. Begin **Stage 1 — Freeze intervention-route semantics** in `docs/EVIDENCE_REGISTRY_V1_1_IMPLEMENTATION_PLAN.md`.

## Stage 1 governing regression rule

Stage 1 must not be accepted unless the existing `2026-08-23` evidence release remains reproducible and the current `csi-evidence-v1` public contract remains backward compatible while non-route evidence categories are separated from the seven true intervention routes.
