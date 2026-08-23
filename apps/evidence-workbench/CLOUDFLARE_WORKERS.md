# Cloudflare Workers deployment — HRP Transfer Evidence Workbench

The Evidence Workbench is deployed as a **static Vite single-page application on Cloudflare Workers Static Assets** backed by the separate `HRP-Transfer-Evidence` Supabase project.

It does not require Worker application code, Pages Functions, KV, R2, D1 or another server-side runtime for the MVP.

## 1. Import the app subdirectory

In the Cloudflare Dashboard use the Workers Git import flow and enter the app subdirectory directly:

```text
https://github.com/HRP-Transfer-Lab/research-platform/tree/main/apps/evidence-workbench
```

The app directory now contains an explicit `wrangler.jsonc`, so Cloudflare should not need to auto-configure the whole monorepo.

Use the Worker name:

```text
hrp-evidence-workbench
```

The production branch is:

```text
main
```

Workers Builds defaults to:

```text
Deploy command
npx wrangler deploy
```

The Wrangler configuration itself runs:

```text
npm run build
```

before deployment and publishes the generated:

```text
dist/
```

folder as static assets.

## 2. Wrangler configuration

`wrangler.jsonc` is the deployment source of truth:

```jsonc
{
  "name": "hrp-evidence-workbench",
  "compatibility_date": "2026-08-23",
  "workers_dev": true,
  "build": {
    "command": "npm run build"
  },
  "assets": {
    "directory": "./dist",
    "not_found_handling": "single-page-application"
  }
}
```

`not_found_handling: "single-page-application"` makes unmatched navigation routes return the built `index.html`, so the React client router works without a separate redirect rule.

## 3. Response headers

`public/_headers` is copied by Vite into `dist/_headers` and is supported by Workers Static Assets.

It provides baseline browser protections and caching rules. Hashed Vite assets may be cached for a long period while `index.html` is kept fresh across deployments.

## 4. Environment variables

No secret database credential is required.

The frontend only uses:

```text
VITE_SUPABASE_URL
VITE_SUPABASE_PUBLISHABLE_KEY
```

These are browser-safe public values and already have zero-config defaults in the app source / `.env.example`.

Do **not** add a Supabase service-role key or database password to Cloudflare.

## 5. Supabase Auth redirect

After the first successful deployment, note the generated Worker URL, for example:

```text
https://hrp-evidence-workbench.<your-workers-subdomain>.workers.dev
```

Add the actual origin to:

```text
Supabase
HRP-Transfer-Evidence
→ Authentication
→ URL Configuration
→ Redirect URLs
```

If a custom domain is attached later, add that origin too.

## 6. First owner bootstrap

The Workbench intentionally starts with zero members.

1. Open the deployed Workbench.
2. Request the passwordless sign-in link.
3. Return through the approved Cloudflare Worker redirect URL.
4. The pending-access screen displays the authenticated Supabase user UUID.
5. Add that UUID to `public.workbench_member` with role `owner` through a trusted database-admin path.
6. Reload the Workbench.
7. The owner can thereafter manage viewer/editor/owner access inside the Workbench.

## 7. Deployment model

```text
GitHub main
        ↓
Cloudflare Workers Builds
        ↓
npx wrangler deploy
        ↓
npm run build
        ↓
Workers Static Assets (dist/)
        ↓
Supabase Auth + Data API
        ↓
Postgres RLS
        ↓
HRP Transfer Evidence Registry
```

Browser access is therefore protected at two levels:

```text
valid Supabase authentication
        +
active workbench_member role
```

A publicly reachable `workers.dev` URL does not make the scientific records public.

## 8. Custom domain — optional

A custom domain can be added later if its DNS is managed by Cloudflare. This is optional; the generated `workers.dev` origin is sufficient for the MVP.

Whenever the production origin changes, keep the Supabase Auth redirect allow-list in sync.
