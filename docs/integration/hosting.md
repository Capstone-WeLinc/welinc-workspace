# Hosting VMMS and BMS on Azure

How your system goes online next to the shared services and VRMS. Everything runs in one Azure subscription that the shared services lead operates, on `welinc.tech`. The decision behind it is [VRMS spec 0008](../specs/vrms/0008-hosting-and-ci-cd/index.md); you don't need to read it.

Read this after your move checklist ([move-vmms.md](move-vmms.md) or [move-bms.md](move-bms.md)). The move makes your system work on the shared services; this page makes it run on Azure. Most of it is a few files per service, and it's easiest to do while you're already in that code for the move.

## Dates

| When | What |
|---|---|
| Mon Nov 16 | Your move pull requests are up; tell the lead |
| Tue Nov 17 | The lead checks your move (the checker) and sets up Azure and staging. You start the checklist below and add CI |
| Wed Nov 18 | Your hosting ready pull requests are merged, and you've sent the lead what's listed in "What the lead needs from you" |
| Thu Nov 19 | The workflow files arrive here. You copy them, the lead turns your group on, and your first push to `development` deploys staging |
| Fri Nov 20 | Production goes live: you create `release` and run the production workflow once |
| Nov 21 to 27 | Keep building on `development` (staging); promote to production when it's stable |
| Nov 28 to Dec 5 | Freeze: production changes only for fixes, and only migrations that add (never drop or rename) |

Until your group is turned on, your routes on the gateway (`/vmms/`, `/bms/`) answer 502 `UPSTREAM_UNAVAILABLE` and nothing else is affected. Between being turned on and your first deploy, they show Microsoft's placeholder page.

## How it fits together

- **Addresses.** Production: `api.`, `portal.`, `vrms.`, `vmms.` and `bms.welinc.tech`. Staging: the same names with `staging-` in front (`staging-api.welinc.tech`). Your web app calls `https://<api>/vmms/` or `https://<api>/bms/`, as locally it calls `http://localhost:3000`.
- **Services.** Each backend process is a Container App. Only the suite gateway is public; your services are internal, reached through the gateway's route or by each other.
- **Internal addresses.** One service calls another at `https://<app name>.internal.<environment domain>`, on port 443, with no port in the address (for example `https://bms-booking.internal.<domain>`, not `:3021`). The lead fills these into your settings, so you only need to read them from the environment, which your code already does.
- **Databases.** Each environment has one PostgreSQL 16 server, holding your databases next to ours: `vmms`; `bms_booking`, `bms_dispatch`, `bms_completion`, `bms_analytics`. They are created when staging is first set up (Nov 18 to 19) and start empty. Each has two logins: `<db>_owner` runs your migrations and owns every table, and `<db>_app` is what your service connects as (read and write rows, nothing else). A database's logins can't open any other database.
- **Web apps.** Each web app is a Static Web App, built once per environment.
- **Mobile.** The VMMS app calls `https://api.welinc.tech` (staging: `https://staging-api.welinc.tech`).
- **Images.** One shared registry. Your deploy workflow will push `<app name>:<commit sha>` for the service and `<app name>-seed:<commit sha>` for its jobs.

## Your apps

These are in the setup as code, named exactly like this, the same as the Docker service names in your compose file (contract 0001 section 2, and *Ports and names* in [move-bms.md](move-bms.md#ports-and-names)). Each gets 0.25 CPU and 0.5 GB of memory; tell the lead if one needs more.

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

"Stays on in staging: no" means the app sleeps when nobody calls it, and the first call after a while may answer 504 while it wakes (about 10 to 30 seconds). Production keeps every app awake. If one of your apps runs anything on a timer, it must stay on: tell the lead.

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

You send only keys from outside providers, which only your accounts can issue: Gemini (VMMS analytics), Groq (BMS analytics), Google Maps and Geocoding (BMS). One key per provider is fine for both environments. Restrict the browser Maps key to `bms.welinc.tech` and `staging-bms.welinc.tech`.

- [ ] Send them privately, in a direct message. Never put one in a repo, an issue, a pull request or the group chat.
- [ ] A changed secret reaches a running app only after a restart; the lead does both.

## Deploying

- **Branches.** Every repo deploys from `development` (staging) and `release` (production). Create `release` from `development` once in each repo. BMS: `welinc-backend-bms` and `welinc-backend-bms-analytics-ai` have no `development` yet (you work on `latest-bms-backend` and `main`), so create it there; your move pull requests go into it anyway.
- **Staging:** a push to `development` deploys that repo by itself, the same as VRMS: build both images, run the migration job, switch to the new version only once its health route answers, then a smoke test. If a migration or the health check fails, the old version keeps serving.
- **Production:** only a manual "Run workflow" on your `release` branch, whose commit must already be on `development` with its image built by the staging deploy.
- **Your Azure login** is your group's own, separate for staging and production. It can update and start only your group's apps and jobs; it can't touch VRMS, the shared services or the other group.
- **Workflow files.** Two files to copy into your repos (one for backends, one for the web app) and the repo variables to set will be added here once ours deploy staging by themselves (Nov 19). Until then there is nothing to copy.

## When something is wrong

Ask the shared services lead: they can read your app's logs and its last deploy. `GET https://<api>/vmms/health` (or `/bms/health`) tells you at once whether the gateway reaches your service.
