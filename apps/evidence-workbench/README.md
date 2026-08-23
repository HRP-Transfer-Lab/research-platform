# HRP Transfer Evidence Workbench

Internal reviewer UI for the hosted **HRP Transfer Evidence Registry**.

## MVP capabilities

- Supabase passwordless authentication.
- Explicit `viewer` / `editor` / `owner` membership enforced by PostgreSQL RLS.
- Evidence library with search and filters for evidence class, route and product relevance.
- Study/population, intervention/protocol, outcome/transfer and IQM product-relevance inspection.
- Editor/owner updates to normalized evidence records.
- Add study/reporting/body-of-evidence quality assessments.
- Owner evidence-release status control.
- Owner Workbench membership management by Supabase user UUID.
- Editor/owner audit trail for all Workbench scientific-data mutations.

## Security model

The frontend uses only the Supabase **publishable** browser key. It contains no secret/service-role key. Authentication alone does not grant database access: the authenticated user must also have an active row in `public.workbench_member`. RLS checks membership on every Registry table operation.

The first owner is bootstrapped manually after their first Supabase Auth sign-in:

1. Sign in to the Workbench once.
2. Copy the UUID shown on the `Workbench access pending` screen.
3. Add that UUID to `public.workbench_member` as role `owner` using a trusted database-admin path.
4. Thereafter the owner can add/manage other reviewers from the Workbench itself.

## Deployment — Cloudflare Pages

Cloudflare Pages is the canonical frontend host for this app. The Workbench is a static Vite application and does **not** require Pages Functions or a server-side runtime.

Create a Pages project from the Git repository with these settings:

```text
Repository
HRP-Transfer-Lab/research-platform

Production branch
main

Root directory
apps/evidence-workbench

Framework preset
Vite

Build command
npm run build

Build output directory
dist
```

Cloudflare should then rebuild and deploy the Workbench whenever `main` changes. Pull-request preview deployments can be used for UI review before merge.

The app includes Cloudflare Pages deployment assets under `public/`:

- `_redirects` provides the SPA fallback to `index.html`.
- `_headers` adds baseline browser security headers, prevents stale caching of `index.html`, and gives hashed Vite assets long immutable caching.

No secret/service-role Supabase credential belongs in Cloudflare. The app only needs the public Supabase project URL and publishable key already documented in `.env.example`; deployment environment variables are optional overrides.

After the first Pages deployment, add the generated `https://<project>.pages.dev` origin to Supabase **Authentication → URL Configuration → Redirect URLs** so passwordless sign-in can return to the Workbench. If a custom domain is later attached, add that origin as well.

See `CLOUDFLARE_PAGES.md` for the complete deployment checklist.

## Local development

```bash
npm install
npm run dev
```

Vite runs on `http://localhost:3000` to align with a conventional Supabase local Site URL. Add that origin to the Supabase redirect allow-list when testing passwordless sign-in locally.

## Configuration

`.env.example` documents the optional Vite variables. The source includes the same project URL and a publishable browser key as zero-config defaults; both are intentionally public frontend values and can be overridden by deployment environment variables.
