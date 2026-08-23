# Supabase deployment — HRP Transfer Evidence Registry

This directory mirrors the migration history of the hosted **HRP-Transfer-Evidence** PostgreSQL database used by the HRP Transfer Evidence Registry.

## Hosted environment

- Supabase project: `HRP-Transfer-Evidence`
- Region: EU West (Ireland)
- PostgreSQL: Supabase-managed Postgres 17
- Data API: enabled
- automatic exposure of new tables: disabled

Do **not** commit the database password, service-role key, secret API keys, or other credentials to this repository.

## Migration history

The production database currently contains these tracked migrations:

```text
20260823174214  create_evidence_registry_core
20260823174605  add_evidence_registry_importer
20260823174724  fix_evidence_registry_importer_targets
20260823175100  add_evidence_registry_fk_indexes
```

The third file is intentionally a replay no-op: the transient importer target-cast bug found during initial seed loading is already corrected in the preceding importer definition in Git. Keeping the version preserves alignment with the hosted migration ledger while ensuring a fresh replay never installs the faulty function.

## Security posture

At bootstrap:

- every raw evidence table in `public` has Row Level Security enabled;
- `anon` and `authenticated` have no table/view grants on Registry objects;
- no browser-facing raw-table policies exist yet;
- the private JSON importer is not available to browser roles;
- approved read views are `security_invoker = true`;
- the views are currently service-side only;
- default privileges are configured so future public tables/functions/sequences are not automatically exposed to Data API roles.

This is deliberately restrictive. The Evidence Workbench should add explicit reviewer policies after its authentication/role model is defined. Explorer/IQ Coach/H-AGI clients should use a separate approved read surface rather than gaining access to reviewer tables.

## Seed release loaded

The hosted database contains the approved Git release `2026-08-23`:

```text
18 evidence sources
18 study rows
13 intervention-component rows
38 outcome rows
35 product-relevance links
```

Buckets:

```text
7  A_direct_intervention
6  B_measurement_mechanism
5  C_human_ai_activity_system
```

The authoritative seed records remain under:

`components/evidence-registry/data/releases/2026-08-23/records/`

The private importer decomposes each approved JSON record into normalized relational rows and is idempotent per source, allowing a corrected Git record to be re-imported without duplicating its child rows.

## Advisors

After deployment, Supabase security and performance advisors were run.

- No high-severity security issue was reported.
- `rls_enabled_no_policy` INFO notices are intentional while browser access is disabled.
- Two initially reported unindexed foreign keys were fixed in `20260823175100_add_evidence_registry_fk_indexes.sql`.
- Remaining unused-index notices are expected on a newly populated small database and should be reassessed after real Workbench/Explorer query traffic exists.
- The default Auth connection allocation notice does not require action at the current micro compute size; revisit it if Auth load or compute scale increases.

## Next step

Build the Evidence Workbench against this database, then add explicit reviewer authentication/RLS and a separately controlled approved evidence API/read model.
