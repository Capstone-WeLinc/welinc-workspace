# Hosting on Azure (staging)

How VMMS and BMS run online next to the shared services and VRMS. Everything runs in one Azure subscription that the lead operates. **Staging is the only hosted environment** and the demo for every defense.

## Dates

| When | What |
|---|---|
| Now | Every merge into `development` deploys staging |
| From the day before the first defense until the final one | Every staging app stays awake (no cold starts in front of the panel) |
| Each defense day (dates moving; the final is by Dec 20 at the latest) | **Freeze:** no merge to `development` in any repo from 2 hours before each defense until it ends. A fix in that window only if the lead agrees |

## How it fits together

- **Addresses:** `staging-api`, `staging-portal`, `staging-vrms`, `staging-vmms` and `staging-bms`, all on `welinc.app`. Your web app calls `https://staging-api.welinc.app/vmms/` (or `/bms/`), like it calls `http://localhost:3000` locally.
- **Backends:** each process is a Container App. Only the suite gateway is public; yours are internal.
- **Names:** every app and job in Azure ends in `-staging` (`bms-booking-staging`). Your code and compose file keep the plain names.
- **Calls between your own services:** `https://<app>-staging.internal.<environment domain>`, port 443, no port in the address. The lead sets these in your settings; your code just reads them.
- **Databases:** one PostgreSQL 16 server holds every database (`vmms`, `bms_booking`, `bms_dispatch`, `bms_completion`, `bms_analytics`). Each has an `<db>_owner` login (migrations) and an `<db>_app` login (your service: rows only).
- **Web apps:** Static Web Apps.
- **Mobile:** the VMMS app calls `https://staging-api.welinc.app`.

## Your apps

0.25 CPU and 0.5 GB each. Tell the lead if one needs more, or if a health path is different.

| App | Port | Health route | Database | Max copies |
|---|---|---|---|---|
| `vmms-backend` | 3010 | `/vmms/health` | `vmms` | 2 |
| `vmms-analytics` | 3011 | `/vmms/analytics/health` | `vmms` | 1 |
| `bms-gateway` | 3020 | `/bms/health` | none | 1 |
| `bms-booking` | 3021 | `/health/ready` | `bms_booking` | 1 |
| `bms-dispatch` | 3022 | `/health/ready` | `bms_dispatch` | 1 |
| `bms-completion` | 3023 | `/health/ready` | `bms_completion` | 1 |
| `bms-analytics-projection` | 3024 | none (a worker) | `bms_analytics` | 1 |
| `bms-analytics` | 3025 | `/health/ready` | `bms_analytics` | 1 |

Migration jobs: `vmms-migrate`, `vmms-analytics-migrate`, `bms-booking-migrate`, `bms-dispatch-migrate`, `bms-completion-migrate`, `bms-analytics-migrate`. Your deploy starts them.

Until the day before the first defense, an app with no traffic sleeps, and the first call may take 10 to 30 seconds (or answer 504) while it wakes. Apps that run timers or loops (`vmms-backend`, `vmms-analytics`, `bms-booking`, `bms-dispatch`, `bms-analytics-projection`) never sleep. If another app runs something on a timer, tell the lead.

## Make your service hosting ready

### Every backend

- [x] A `Dockerfile.prod` on `node:24-alpine`, copied from `welinc-backend-vrms/Dockerfile.prod`. Last stage runs the built app as the `node` user with production dependencies only; a `seed` stage holds the full source for migration jobs. No `.env` file in the image.
- [x] Listen on `0.0.0.0` and `PORT`.
- [x] Pool size from `DB_POOL_MAX` (2 for you), across every pool in the process. The server only has about 35 connections for everyone.
- [x] The health route answers 200 only when the database answers (2 second timeout), 503 otherwise, with no token. Copy `welinc-backend-vrms/src/health/`.
- [x] No lasting files on local disk: it's wiped on every deploy. Uploaded files go to blob storage (ask the lead).
- [ ] Every table, trigger, function and extension comes from a migration, never from the app at boot. *(BMS done. VMMS: the vector line in analytics, below.)*
- [x] Your migration command needs only `DATABASE_URL` (Prisma: `npx prisma migrate deploy`).
- [x] Your seed refuses `NODE_ENV=production` unless `SEED_ALLOW=staging` is set.
- [ ] With `NODE_ENV=production`, startup refuses `http://` and `localhost` addresses. *(BMS done. VMMS: both backends leave `AUTH_INTERNAL_URL` out of the check.)*

### VMMS only

- [x] Work order and fuel attachments move from `private-uploads/` to blob storage, like VRMS's ticket files. Your container is `vmms-attachments`, and only `vmms-backend` can read or write it, using its own identity (no key). On staging the app gets `STORAGE_ACCOUNT_URL`, `STORAGE_PUBLIC_URL` and `STORAGE_CONTAINER`; locally, point the same code at Azurite. Copy `welinc-backend-vrms/src/modules/attachments/blob-file-store.ts` for the client and the signed links.
- [ ] Fuel receipt scanning: staging has an Azure AI Document Intelligence resource (free tier, prebuilt receipt model). The app gets `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` and no key, so it calls the service with its own identity: when no key is set, get a token from `DefaultAzureCredential` for `https://cognitiveservices.azure.com/.default` and send `Authorization: Bearer <token>` instead of `Ocp-Apim-Subscription-Key` (your blob storage code already uses the same credential). Accept the endpoint without a key in `env.ts`. *(Still to do: the code reads a key.)* For local testing, ask the lead for a key and keep it in your `.env` only. Keep scanning optional: if it's off or fails, staff type the receipt by hand.
- [ ] Analytics: `CREATE EXTENSION vector` and the `notify_vmms_table_change()` triggers live in a migration. Write the extension as `DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN CREATE EXTENSION vector; END IF; END $$;` (Azure refuses the plain `IF NOT EXISTS` form). *(Triggers done; line 1 of `scripts/migrations/0001-hosting-infrastructure.sql` still uses the plain form, and it blocks hosting.)*

### BMS only

- [x] `bms-analytics-projection`: drop the localhost only database check, and move its `CREATE TABLE IF NOT EXISTS` tables into a migration.
- [x] `bms-gateway` reaches the inner services through `BOOKING_API_URL` and the others.
- [x] BMS analytics: no MySQL hosted. Saved reports and forecasts move into `bms_analytics` (PostgreSQL).

### CI

- [x] Copy `.github/workflows/ci.yml` and `.github/dependabot.yml` from `welinc-backend-vrms` (backends) and `welinc-web-vrms` (web app). Change only the commands to your own scripts.
- [x] Pull requests into `development` merge only on a green `CI / ci` check.

### Web app

- [x] Builds with `VITE_API_BASE_URL` and `VITE_PORTAL_URL` (BMS also `VITE_GOOGLE_MAPS_API_KEY`), output in `dist/`.
- [ ] Copy `welinc-web-vrms/public/staticwebapp.config.json` into `public/`. If your app loads from another site (BMS: Google Maps), add exactly those hosts to its `Content-Security-Policy`. *(VMMS: yours is missing HSTS, the 404 page and a few headers from ours. BMS: drop `'unsafe-eval'` if the map works without it.)*

## Settings

**The lead sets these for every app:** `NODE_ENV`, `PORT`, `DB_POOL_MAX`, `DATABASE_URL`, `AUTH_ISSUER`, `AUTH_PUBLIC_URL`, `AUTH_INTERNAL_URL`, `AUTH_JWKS_URL`, `API_PUBLIC_URL`, `PORTAL_URL`, `WEB_APP_URL`, `SESSION_COOKIE_SECURE`, `TRUST_PROXY_HOPS`, your client key, and the keys shared between your own services.

**Send the lead** (in a direct message, never in a repo or the group chat):
- every other setting your services read, with its staging value (`AUTH_CLIENT_ID`, `CORS_ORIGINS`, your service addresses, plain values);
- keys only your accounts can make: Gemini (VMMS analytics), Groq (BMS analytics), Google Maps and Geocoding (BMS; restrict the browser key to `staging-bms.welinc.app`);
- every PostgreSQL extension your migrations create;
- your migration command and your seed command;
- any app that runs a timer, and any files you store.

A changed setting reaches a running app only after a restart; the lead does both.

## Deploying

- **Branches:** work on feature branches from `development` and merge back by pull request. `development` is your default branch. **Never touch `main`**, and never press "Run workflow".
- **A merge into `development` deploys staging:** CI runs first; then both images build, the migration job runs, and the new version takes traffic only once its health route answers. If anything fails, the old version keeps serving.
- **Migrations only add.** Never drop or rename a column or table, so older code still runs on the newer database.
- **Rollback:** revert the bad change with a pull request into `development`.
- **Your Azure login** can update and start only your group's apps and jobs.
- **Workflow files:** copy [`deploy-templates/deploy-backend.yml`](deploy-templates/deploy-backend.yml) into each backend repo and [`deploy-templates/deploy-web.yml`](deploy-templates/deploy-web.yml) into your web repo, as `.github/workflows/deploy.yml`. In the backend file, keep only your repo's `services` lines (the comments list them). Each runs after your `CI` passes on a push to `development`. The lead sets the repo variables when your group is turned on; BMS adds `VITE_GOOGLE_MAPS_API_KEY` as a repo secret in `welinc-web-bms`.
- **First deploy of each app:** it fails at "Wait for the revision", because a new app starts on a placeholder image. Tell the lead; one rerun of the setup fixes the port and probes, then rerun the deploy.

## When something is wrong

`https://staging-api.welinc.app/vmms/health` (or `/bms/health`) tells you whether the gateway reaches your service. For logs or a failed deploy, ask the lead.
