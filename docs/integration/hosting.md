# Hosting VMMS and BMS on Azure

How your system goes online next to the shared services and VRMS. Everything runs in one Azure subscription that the shared services lead operates, on `welinc.app`. The decision behind it is [VRMS spec 0008](../specs/vrms/0008-hosting-and-ci-cd/index.md); you don't need to read it.

**Only staging is hosted** (since Nov 20, spec 0008 AC-24). The Azure trial refused a second database server, so production exists as code only. Staging is the demo for every defense: you deploy to staging, and there is no production run to make. Wherever this page still names production, it describes the code, not a live environment.

Read this after your move checklist ([move-vmms.md](move-vmms.md) or [move-bms.md](move-bms.md)). The move makes your system work on the shared services; this page makes it run on Azure. Most of it is a few files per service, and it's easiest to do while you're already in that code for the move.

## Dates

| When | What |
|---|---|
| Mon Nov 16 | Your move pull requests are up; tell the lead |
| Tue Nov 17 | The lead checks your move (the checker) and sets up Azure and staging. You start the checklist below and add CI |
| Wed Nov 18 | Your hosting ready pull requests are merged, and you've sent the lead what's listed in "What the lead needs from you" |
| Thu Nov 19 | The workflow files arrive here. You copy them, the lead turns your group on, and your first push to `development` deploys staging |
| Fri Nov 20 | Production is dropped: staging is the only hosted environment |
| Nov 21 to 26 | Keep building on `development`; every merge deploys staging |
| Nov 27 to the shutdown copy after Dec 5 | Every staging app stays awake (no cold starts in front of the panel) |
| Defense days: Nov 28, Dec 4, Dec 5 | Freeze: no merge to `development` in any repo from 2 hours before each defense until it ends, since every merge redeploys the demo. A fix in that window only if the lead agrees, followed by a check of staging. Migrations only add (never drop or rename) |

Until your group is turned on, your routes on the gateway (`/vmms/`, `/bms/`) answer 502 `UPSTREAM_UNAVAILABLE` and nothing else is affected. Between being turned on and your first deploy, they show Microsoft's placeholder page.

## How it fits together

- **Addresses.** Staging: `staging-api.`, `staging-portal.`, `staging-vrms.`, `staging-vmms.` and `staging-bms.welinc.app`. Production's names (the same without `staging-`) are not live. Your web app calls `https://<api>/vmms/` or `https://<api>/bms/`, as locally it calls `http://localhost:3000`.
- **Services.** Each backend process is a Container App. Only the suite gateway is public; your services are internal, reached through the gateway's route or by each other.
- **Names end in `-staging`.** Every app and job in Azure has its environment at the end of its name: `bms-booking-staging`, `vmms-migrate-staging` (production's would end in `-prod`). Your code, your compose file and contract 0001 keep the plain names; the ending exists only in Azure.
- **Internal addresses.** One service calls another at `https://<app name with its ending>.internal.<environment domain>`, on port 443, with no port in the address (for example `https://bms-booking-staging.internal.<domain>`, not `:3021`). An address without the ending reaches nothing. The lead fills these into your settings, so you only need to read them from the environment, which your code already does.
- **Databases.** Each environment has one PostgreSQL 16 server, holding your databases next to ours: `vmms`; `bms_booking`, `bms_dispatch`, `bms_completion`, `bms_analytics`. They are created when staging is first set up (Nov 18 to 19) and start empty. Each has two logins: `<db>_owner` runs your migrations and owns every table, and `<db>_app` is what your service connects as (read and write rows, nothing else). A database's logins can't open any other database.
- **Web apps.** Each web app is a Static Web App, built once per environment.
- **Mobile.** The VMMS app calls `https://staging-api.welinc.app`.
- **Images.** One shared registry. Your deploy workflow will push `<app name>:<commit sha>` for the service and `<app name>-seed:<commit sha>` for its jobs, with the plain name (no ending).

## Your apps

These are in the setup as code, named like this plus `-staging` or `-prod` in Azure, the same as the Docker service names in your compose file (contract 0001 section 2, and *Ports and names* in [move-bms.md](move-bms.md#ports-and-names)). Each gets 0.25 CPU and 0.5 GB of memory; tell the lead if one needs more.

| App | Port | Health route the platform checks | Database | Stays on in staging | At most |
|---|---|---|---|---|---|
| `vmms-backend` | 3010 | `/vmms/health` | `vmms` | yes (it runs timers) | 2 |
| `vmms-analytics` | 3011 | `/vmms/analytics/health` | `vmms` | yes (sync loop) | 1 |
| `bms-gateway` | 3020 | `/bms/health` | none | no | 1 |
| `bms-booking` | 3021 | `/health/ready` | `bms_booking` | no | 1 |
| `bms-dispatch` | 3022 | `/health/ready` | `bms_dispatch` | no | 1 |
| `bms-completion` | 3023 | `/health/ready` | `bms_completion` | no | 1 |
| `bms-analytics-projection` | 3024 | none (a worker, no web traffic) | `bms_analytics` | yes (projection loop) | 1 |
| `bms-analytics` | 3025 | `/health/ready` | `bms_analytics` | no | 1 |

Jobs (started by your deploy workflow, never on a timer): `vmms-migrate`, and `bms-booking-migrate`, `bms-dispatch-migrate`, `bms-completion-migrate`, `bms-analytics-migrate`. Each runs your seed image as the database's owner login.

"Stays on in staging: no" means the app sleeps when nobody calls it, and the first call after a while may answer 504 while it wakes (about 10 to 30 seconds). From Nov 27 until the shutdown copy after Dec 5, every staging app stays awake anyway, because staging is the demo. If one of your apps runs anything on a timer, it must stay on: tell the lead.

A different health path or an app this table misses is a one line change on our side, so just tell the lead.

## Make it hosting ready

Tick these in your move pull requests.

### Every backend process

- [ ] A `Dockerfile.prod` on `node:24-alpine` with two targets, copied from `welinc-backend-vrms/Dockerfile.prod` (on its `development`). The default last stage is the **runner**: built `dist/`, production dependencies only, `NODE_ENV=production`, runs as the `node` user, `CMD` starts the built app. Check the path really exists in your build output (`dist/main` and `dist/src/main` differ by tsconfig). Never start with `node --env-file=.env`: hosted, every setting comes from the environment and the image holds no `.env` file. The `seed` target is the full source image (source, `prisma/`, scripts, `tsconfig.json`) that migration and seed jobs run from.
- [ ] Listen on all interfaces (`0.0.0.0`) and on `PORT`. Nest's `app.listen(port)` already does; a plain `server.listen(port, '127.0.0.1')` can't be reached.
- [ ] Read `DB_POOL_MAX` into your pool size (`pg.Pool` `max`, or the Prisma adapter's pool). It is 2 for you. One server holds all seven databases with about 35 connections in total, so an uncapped pool (the default is 10) starves everyone else. It caps the whole process: a process with two pools (Prisma plus a raw `pg.Pool`) or a `LISTEN` connection keeps their total at 2 (VMMS analytics has all three today).
- [ ] The health route answers 200 only when the database answers (each check gives up after 2 seconds), and 503 otherwise, needing no token. The platform sends traffic to a new version only once it answers 200, and allows 240 seconds for boot. Copy `welinc-backend-vrms/src/health/`.
- [ ] Nothing lasting on local disk. A container's disk is wiped on every deploy and restart. Anything you only cache and can rebuild (a cache file, a DuckDB datamart rebuilt at boot) is fine. Uploaded files are not: tell the lead what you store, so your group gets its own blob container.
- [ ] Every table, trigger, function and extension comes from a migration, never from the app at boot. The app login can't create them. (VMMS analytics: `installPostgresTriggers` moves into a VMMS migration.)
- [ ] Tell the lead every PostgreSQL extension your migrations create (`pgcrypto`, `uuid-ossp` and so on), before your first deploy. Azure allows only the extensions on its list, and VRMS's `vector` and `pg_trgm` are on it already.
- [ ] Your migration command, run from the seed image, needs nothing but `DATABASE_URL` (for Prisma: `npx prisma migrate deploy`). Tell the lead which command it is.
- [ ] Make your seed refuse when `NODE_ENV=production` unless `SEED_ALLOW=staging` is set, as welinc-auth's and VRMS's do, so seed people never reach production. Your migration jobs carry `SEED_ALLOW=staging` on staging only: the lead starts each once with your seed command (tell the lead which one) to seed staging.
- [ ] Booting with `NODE_ENV=production` refuses `http://` and `localhost` addresses, the way welinc-auth's and VRMS's startup checks do (suite spec 0010). This catches a missing setting at deploy time instead of on the first sign in.

### VMMS only

- [ ] Work order and fuel anomaly attachments (`private-uploads/`) can't stay on disk. Tell the lead, and they move to a blob container the way VRMS's ticket files did (spec 0017 in our backend: the browser gets signed links).
- [ ] VMMS analytics: its `CREATE EXTENSION vector` and its `notify_vmms_table_change()` triggers move into a migration that `npm run migrate` runs, not into the app at boot.
- [ ] VMMS analytics: Azure refuses `CREATE EXTENSION IF NOT EXISTS vector` for your migration login even when the extension already exists (the lead creates it for you). Write it as `DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN CREATE EXTENSION vector; END IF; END $$;` instead. VRMS hit this on its first deploy.

### BMS only

- [ ] `bms-analytics-projection`: drop the check that refuses any database host but localhost. Hosted, the database is `psql-welinc-<env>.postgres.database.azure.com`. Its `CREATE TABLE IF NOT EXISTS` read model tables move into a migration too.
- [ ] `bms-gateway` reaches the inner services through `BOOKING_API_URL` and the others, which the lead sets to the internal addresses.
- [ ] BMS analytics keeps saved reports and forecasts in MySQL. There is no MySQL in the hosted setup: move those tables into its PostgreSQL database `bms_analytics` (a Prisma migration), or tell the lead now if that can't land by Nov 18.

### CI

- [ ] Copy `.github/workflows/ci.yml` from `welinc-backend-vrms` into each backend repo, and from `welinc-web-vrms` into the web app. Change only the commands to the scripts your `package.json` has (lint that checks without fixing, typecheck, test, build). Keep the triggers, `permissions` and `concurrency` as they are.
- [ ] Copy `.github/dependabot.yml` from the same repos.
- [ ] Open your pull requests into `development` and wait for the green `CI / ci` check before you merge. Once the deploy workflow lands, it deploys only after this check passes.

### Web app

- [ ] `npm run build` (BMS: `build:prod`) with `VITE_API_BASE_URL` and `VITE_PORTAL_URL` set (BMS also `VITE_GOOGLE_MAPS_API_KEY`, a browser key limited to your two web addresses), output in `dist/`. No Dockerfile is needed for hosting.
- [ ] Copy `welinc-web-vrms/public/staticwebapp.config.json` into your `public/`. It sends every path to `index.html` and sets the security headers. Its `Content-Security-Policy` allows only our own sites. If your app loads anything from another site (BMS: Google Maps), add exactly those hosts to `script-src`, `img-src` and `connect-src`, and nothing broader.

## What the lead sets for you

Every app gets these without asking, for its environment:

| Setting | Value |
|---|---|
| `NODE_ENV`, `PORT`, `DB_POOL_MAX` | `production`, the port above, `2` |
| `DATABASE_URL` | the `<db>_app` login of its database (jobs: the `<db>_owner` login), with `sslmode=require` |
| `AUTH_ISSUER`, `AUTH_PUBLIC_URL` | `https://<api>/auth` |
| `AUTH_INTERNAL_URL`, `AUTH_JWKS_URL` | welinc-auth's internal address, and the same plus `/auth/.well-known/jwks.json` |
| `API_PUBLIC_URL`, `PORTAL_URL`, `WEB_APP_URL` | `https://<api>`, `https://<portal>`, your web app's address |
| `SESSION_COOKIE_SECURE` | `true` |
| `TRUST_PROXY_HOPS` | `2` on `vmms-backend`, `vmms-analytics` and `bms-gateway` (they sit behind Azure's edge and the suite gateway); hops inside BMS are yours to set |

Anything else your service reads, send the lead its name and value per environment. That includes `AUTH_CLIENT_ID` (your client id: `vmms`, `vmms-analytics`, `bms`, `bms-analytics`), `CORS_ORIGINS` (your web app's address), the addresses between your own services (`VMMS_API_BASE_URL`, `BOOKING_API_URL` and so on, which the lead turns into internal addresses), and plain values such as `CUSTOMER_SUPPORT_EMAIL`.

## What the lead needs from you

By Nov 18. The lead has a first draft from reading your repos; check it and correct what's wrong.

| What | Why |
|---|---|
| Every PostgreSQL extension your migrations create | Azure refuses any extension not switched on for the server beforehand, so the migration fails |
| Your migration command, and your seed command for staging | Your migration job runs exactly this command; nothing else runs your migrations hosted |
| Which apps run something on a timer or a loop | On staging an app with no traffic sleeps, and its timers stop with it |
| What files you store | A container's disk is wiped on every deploy; lasting files need a blob container |
| Every other setting your services read, with its staging and production value | The lead sets every setting; the image holds no `.env` |
| Your outside provider keys (see Secrets) | Only your accounts can issue them |

## Secrets

The lead makes every key that only our own services use, once per environment (staging and production differ, so a leaked staging key can't open production):

- your client keys (`keys:client` in welinc-auth): the private key goes on your app, the public half into auth;
- internal keys shared between your own services (`BMS_INTERNAL_SERVICE_KEY`, `CUSTOMER_TRACKING_SECRET`, the inbound booking webhook secret and API key). Where an outside sender needs one of these, the lead gives it to you directly.

You send only keys from outside providers, which only your accounts can issue: Gemini (VMMS analytics), Groq (BMS analytics), Google Maps and Geocoding (BMS). One key per provider is fine for both environments. Restrict the browser Maps key to `bms.welinc.app` and `staging-bms.welinc.app`.

- [ ] Send them privately, in a direct message. Never put one in a repo, an issue, a pull request or the group chat.
- [ ] A changed secret reaches a running app only after a restart; the lead does both.

## Deploying

- **Branches.** Every repo has two long lived branches: `development` (your daily branch, deploys staging) and `main` (production's branch, unused while production is not hosted). Feature branches come off `development` and go back into it by pull request. `staging` is an environment, not a branch: delete any old `staging` branch. Set `development` as each repo's default branch (Settings, General), so pull requests and Dependabot target it.
- **Never touch `main`.** No pull requests into it, no commits, no pushes. While production is not hosted, nothing needs `main`, so the one time cleanup below is no longer needed; leave `main` as it is unless the lead says production is coming back.
- **One time branch cleanup** (on hold since Nov 20, only if production is hosted again).
  - VMMS: in every repo but one, `main` is just behind `development`, so once your deploy workflow is on `development`, bring `main` up once before your first production run: `git push origin origin/development:main` (a fast forward, not a force push; the fast forward is what carries the workflow file to `main`). A manual run uses the workflow file on `main`, and `main` has none until then; after that the production workflow moves `main` for you. The exception is `welinc-web-vmms`: its `main` holds only GitHub's "Initial commit" README from May, which `development` doesn't have. Replace it once: `git push --force-with-lease origin origin/development:main`. Delete the old `staging` branches.
  - BMS: `welinc-backend-bms` and `welinc-backend-bms-analytics-ai` have no `development` yet, and `welinc-web-bms`'s is from May. Create or refresh them from your newest work (your move pull requests go into them). Your `main` is behind that work in all three, so once your deploy workflow is on `development`, bring `main` up once the same way (`git push origin origin/development:main`) before your first production run.
- **Staging:** a push to `development` deploys that repo by itself, the same as VRMS: build both images, run the migration job, switch to the new version only once its health route answers, then a smoke test. If a migration or the health check fails, the old version keeps serving.
- **CI first, always.** Every deploy runs your `ci.yml` on the commit first and deploys only if it passes. A push straight to `development` with a red check deploys nothing. Still, always go through a pull request.
- **Production:** not hosted. Don't press "Run workflow". In our repos the deploy workflow stops at once with "production is not hosted", and the workflow files you copy from ours carry the same check.
- **Rollback on staging:** revert the bad change with a pull request into `development`, which deploys the fix. Migrations only add, never drop or rename, so older code still runs on the newer database.
- **Your Azure login** is your group's own staging login. It can update and start only your group's apps and jobs; it can't touch VRMS, the shared services or the other group.
- **Workflow files.** Two files to copy into your repos (one for backends, one for the web app) and the repo variables to set will be added here once ours deploy staging by themselves (Nov 19). Until then there is nothing to copy. Their names follow ours: `IMAGE_REPO` is the plain app name (the image), `CONTAINER_APP_STAGING` and `CONTAINER_APP_PROD` the app with its ending, `MIGRATE_JOB_STAGING` and `MIGRATE_JOB_PROD` the job with its ending, and each workflow picks the pair for the environment it deploys. The production half of each file stays unused while production is not hosted.

## When something is wrong

Ask the shared services lead: they can read your app's logs and its last deploy. `GET https://<api>/vmms/health` (or `/bms/health`) tells you at once whether the gateway reaches your service.
