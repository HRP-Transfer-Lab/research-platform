# Cloudflare Pages deployment — HRP Transfer Evidence Workbench

The Evidence Workbench is intended to run as a **static Cloudflare Pages site** backed by the separate `HRP-Transfer-Evidence` Supabase project.

It does not require Pages Functions, Workers, KV, R2 or a server-side API for the MVP.

## 1. Create the Pages project

In Cloudflare Dashboard:

```text
Workers & Pages
→ Create application
→ Pages
→ Import an existing Git repository
```

Select:

```text
HRP-Transfer-Lab/research-platform
```

Use:

```text
Project name
hrp-transfer-evidence-workbench

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

Do not configure a Pages Function.

## 2. Environment variables

No secret database credential is required.

The frontend uses only:

```text
VITE_SUPABASE_URL
VITE_SUPABASE_PUBLISHABLE_KEY
```

These are public browser values and are already available as zero-config defaults in the app source / `.env.example`.

You may set them in Cloudflare Pages as explicit deployment variables if preferred, but do not add a Supabase service-role or secret key.

## 3. SPA routing

`public/_redirects` contains:

```text
/* /index.html 200
```

Vite copies this to `dist/_redirects`. Cloudflare Pages then serves `index.html` for client-side application routes instead of returning a 404.

## 4. Response headers

`public/_headers` is copied into the final Pages artifact and sets baseline browser protections plus caching rules.

The hashed `/assets/*` output is cacheable for a long period, while `/index.html` is marked `no-store` so a new deployment is not hidden behind a stale shell document.

## 5. Supabase Auth redirect

After Cloudflare creates the first deployment, note the generated origin, for example:

```text
https://hrp-transfer-evidence-workbench.pages.dev
```

Add the real origin to:

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
3. Return to the Workbench through the approved Cloudflare redirect URL.
4. The pending-access screen displays the authenticated Supabase user UUID.
5. Add that UUID to `public.workbench_member` with role `owner` through a trusted database-admin path.
6. Reload the Workbench.
7. The owner can thereafter manage viewer/editor/owner access in the Workbench itself.

## 7. Deployment model

```text
GitHub main
        ↓
Cloudflare Pages build
        ↓
Static Vite frontend
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

A publicly reachable Pages URL does not make the scientific records public.

## 8. Custom domain — optional

A custom domain can be added later, for example a research subdomain controlled in Cloudflare DNS. This is optional; the `pages.dev` origin is sufficient for the MVP.

Whenever the production origin changes, keep the Supabase Auth redirect allow-list in sync.
