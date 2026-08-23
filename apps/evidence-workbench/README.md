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

## Deployment — Cloudflare Workers Static Assets

Cloudflare Workers Static Assets is the canonical frontend host for this app. The Workbench remains a static Vite SPA: there is no Worker application code and no KV, R2, D1 or server-side API requirement for the MVP.

Import this **app subdirectory**, rather than the whole research-platform monorepo:

```text
https://github.com/HRP-Transfer-Lab/research-platform/tree/main/apps/evidence-workbench
```

The app contains `wrangler.jsonc`, which is the Cloudflare deployment source of truth:

```text
Worker name
hrp-evidence-workbench

Production branch
main

Deploy command
npx wrangler deploy
```

Wrangler runs `npm run build` and publishes `dist/` as static assets. SPA fallback is configured directly with `assets.not_found_handling = "single-page-application"`; a separate `_redirects` rewrite is not required.

`public/_headers` is retained and copied into `dist/` by Vite so Workers Static Assets can apply the browser-security and caching headers.

No secret/service-role Supabase credential belongs in Cloudflare. The app only uses the public Supabase project URL and publishable key documented in `.env.example`; deployment environment variables are optional overrides.

After the first deployment, add the generated `https://<worker>.<subdomain>.workers.dev` origin to Supabase **Authentication → URL Configuration → Redirect URLs** so passwordless sign-in can return to the Workbench. If a custom domain is later attached, add that origin as well.

See `CLOUDFLARE_WORKERS.md` for the complete deployment and first-owner checklist.

## Local development

```bash
npm install
npm run dev
```

Vite runs on `http://localhost:3000` to align with a conventional Supabase local Site URL. Add that origin to the Supabase redirect allow-list when testing passwordless sign-in locally.

## Configuration

`.env.example` documents the optional Vite variables. The source includes the same project URL and a publishable browser key as zero-config defaults; both are intentionally public frontend values and can be overridden by deployment environment variables.
