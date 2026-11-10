# 0008. Host on Azure with GitHub Actions for CI and CD

**Date**: 2026-10-25
**Status**: In Progress
**Updated**: 2026-11-11 (staleness sweep). Facts that moved on since this was written: the gateway is `infra/gateway/` in the workspace with one template for local and Azure (`_root` spec 0008), not `welinc-auth/nginx.conf`, and `/repairs` is no longer routed; tokens are ES256 checked against `AUTH_JWKS_URL` (`_root` spec 0002), so there is no `JWT_SECRET` or `JWT_ACCESS_EXPIRY`; web-vrms reads only `VITE_API_BASE_URL` and `VITE_PORTAL_URL` (no `VITE_VRMS_URL`, no `VITE_AUTH_MODE`); VRMS ticket files also need a Blob Storage account and the `vrms-attachments` container (spec 0017 Follow-up), beside the Azure Files share for auth's profile pictures. CD, Bicep, the seed job and `staticwebapp.config.json` are not built yet.

## Summary

WeLinc will run on Azure using your free credit. The two React apps go on Azure Static Web Apps (free), the two NestJS services and the nginx gateway go on Azure Container Apps, and the data lives in one Azure PostgreSQL server holding separate databases for staging and production. GitHub Actions checks every pull request (CI) and deploys (CD): a push to `development` updates staging by itself, and production only updates when a person moves the `release` branch and clicks "Run workflow". The Azure setup is written as Bicep files (setup as code) so it can be recreated in another teammate's subscription when credit runs low. The Python analytics service is not deployed for now.

## Requirements

**User stories**:
- As a developer, I want every pull request checked automatically so that a broken build is caught before it merges.
- As a developer, I want a merge to `development` to reach staging without manual steps so that every slice can be demoed from staging.
- As the team lead, I want production to change only when a person chooses so that a bad merge cannot reach the demo system.
- As the team, we want the Azure setup recreatable so that running out of credit does not mean losing the system.

**Acceptance criteria** (the contract, each independently checkable):
- **AC-1**: Every pull request into `development` in web-vrms, web-portal, backend-vrms, auth and analytics-ai runs a CI workflow (install, lint without fixing, build, tests where the repo has them) and shows pass or fail on the PR.
- **AC-2**: CI fails the run when lint, the build or a test fails.
- **AC-3**: A push to `development` in web-vrms, web-portal, backend-vrms or auth deploys that repo to staging with no manual step. A push to `main` in the workspace repo that changes `infra/gateway/**` deploys the gateway to staging the same way.
- **AC-4**: Production deploys only from a manual "Run workflow" run on the `release` branch of that repo. A push or merge to `development` never deploys production. The `release` commit must be reachable from `development`, and for a backend its image must already exist in the registry (built by the staging deploy of that commit), otherwise the run fails.
- **AC-5**: Staging and production use separate databases (`auth_staging`, `vrms_staging`, `auth_prod`, `vrms_prod`), separate database roles and passwords, separate JWT secrets, separate allowed origins and separate API addresses. A staging service cannot connect to a production database. In production the services accept localhost origins from nobody.
- **AC-6**: Database migrations run automatically before a backend revision takes traffic. If a migration fails, or the new revision's readiness probe fails, the deploy stops and the previous revision keeps serving.
- **AC-7**: Staging and production are reached over HTTPS only, on Azure provided addresses.
- **AC-8**: Database backups are automatic with at least 14 days kept, and one restore into a scratch server has been tested before go live.
- **AC-9**: After every deploy a smoke test checks the gateway, `/auth/health`, `/vrms/health` (each confirming a database connection) and that both apps return their page. It retries for up to 3 minutes to allow cold starts. Any failure marks the deploy failed.
- **AC-10**: Running the Bicep files against empty resource groups in any subscription recreates the whole system, minus data. The one time bootstrap steps (creating the resource groups, the budget, the cross group registry permission, the Entra app registrations, the `release` branches) are listed in the runbook, which also covers moving data with `pg_dump` and restore.
- **AC-11**: No long lived Azure password is stored in GitHub, and no secret value is committed to any repo. Deploys log in to Azure with OpenID Connect (a short lived pass) using two app registrations: the staging one trusts only the `development` branch and the production one trusts only the `release` branch. Workflows default to `contents: read`.
- **AC-12**: A budget alert emails the subscription owner at 50%, 80% and 100% of the credit amount, and staging can be scaled to zero or stopped from the runbook.
- **AC-13**: Staging and production are seeded once at first deploy by a manually started seed job. The seed refuses to run when `NODE_ENV=production` unless `ALLOW_PRODUCTION_SEED=true` is set, and only that job sets it.
- **AC-14**: Profile pictures uploaded in one revision are still there after a restart, a new revision or a scale to zero.

## Decision

**Chosen option**: Option 1: Azure Static Web Apps, Container Apps and PostgreSQL Flexible Server, deployed by GitHub Actions and described in Bicep.

The two SPAs run on Static Web Apps; auth, backend-vrms and the nginx gateway run on Container Apps from images in Azure Container Registry; both environments share one PostgreSQL Flexible Server with separate databases; CI runs on every pull request and CD runs from per repo `deploy.yml` files, with production behind a manual run on the `release` branch. (basis: your existing `Dockerfile.prod` files, the Azure credit, and the Azure free tier limits in References)

**Implementation skills**: `azure-container-apps` (`microsoftdocs/agent-skills`, `.claude/skills/azure-container-apps/`) · `azure-container-registry` (`microsoftdocs/agent-skills`, `.claude/skills/azure-container-registry/`) · `azure-static-web-apps` (`microsoftdocs/agent-skills`, `.claude/skills/azure-static-web-apps/`) · `azure-validate` (`microsoft/azure-skills`, `.claude/skills/azure-validate/`) · `azure-deployment-preflight` (`github/awesome-copilot`, `.claude/skills/azure-deployment-preflight/`)

## Proposed stack

| Layer | Choice | Reason |
|---|---|---|
| Frontends | Azure Static Web Apps, Free plan, one app per SPA per environment (four apps) | Free, HTTPS and CDN included, your apps are plain Vite builds. The Free plan allows 10 apps per subscription. |
| Services | Azure Container Apps, Consumption plan, one environment per WeLinc environment, single revision mode with readiness probes | Runs the existing `Dockerfile.prod` images, HTTPS included, scale to zero, monthly free usage grant. Single revision mode keeps the old revision serving until the new one is ready. |
| Gateway | The nginx gateway as its own Container App | Keeps one API address for the frontends. Reuses the routing in `welinc-auth/nginx.conf`, changed to read its upstreams from environment values. |
| Database | Azure Database for PostgreSQL Flexible Server, Burstable, PostgreSQL 16, one shared server | Managed backups and restore. Version matches local Postgres 16. |
| Uploads | Azure Files share mounted into auth at `/app/uploads` | Profile pictures are written to local disk today and would be lost on every restart. A mounted share needs no code change. |
| Registry | Azure Container Registry, Basic | 10 GiB included, Container Apps pulls with a managed identity (no stored password). |
| CI | GitHub Actions `ci.yml` in each of the five repos | Free minutes cover it (2,000 a month on the Free plan). |
| CD | GitHub Actions `deploy.yml` in each deployable repo, plus the gateway workflow in the workspace repo | Each repo ships itself. Production uses `workflow_dispatch` on `release`. |
| Azure login | OpenID Connect with federated credentials, two app registrations, no client secret | Microsoft's recommended approach. Without GitHub environments the trust can only be set per branch, so production gets its own `release` branch. |
| Setup as code | Bicep in `infra/` of the workspace repo, applied by hand with small scripts | Recreatable in another subscription. |
| Secrets | A private file per environment, kept by the subscription owner and never committed, applied by a script that sets Container Apps secrets | Bicep never carries app secret values, so a repeat apply cannot wipe them. GitHub Free cannot scope secrets to environments on private repos, so deploy workflows hold none. |
| Addresses | Azure default hostnames with automatic HTTPS | No cost. A custom domain can come later. |
| Not deployed | analytics-ai, MongoDB, pgvector database, both Redis containers | Feature 3 retires analytics-ai. Neither NestJS service uses Redis in code. |

## Design

**Environments**

| Item | Staging | Production |
|---|---|---|
| Resource group | `rg-welinc-staging` | `rg-welinc-prod` |
| Shared resource group | `rg-welinc-shared` holds the registry and the PostgreSQL server | same |
| Databases on the shared server | `auth_staging`, `vrms_staging` | `auth_prod`, `vrms_prod` |
| Database roles | one role per database, owning only that database | same |
| `NODE_ENV` | `production` | `production` |
| Container Apps minimum replicas | 0 (scale to zero, saves credit) | 1 for gateway, auth and backend-vrms (avoids slow first requests) |
| Maximum replicas | 2 | 2 |
| Deploy trigger | push to `development` | manual `workflow_dispatch` on the `release` branch |
| Seed | manual seed job, once at first deploy | manual seed job, once at first deploy, then guarded |

**Network**: the gateway has public ingress. Auth and backend-vrms have internal ingress. The database server allows connections from Azure services only, with SSL required (`sslmode=require`).

**Gateway rules**: the nginx template reads `AUTH_UPSTREAM`, `VRMS_UPSTREAM` and `ALLOWED_ORIGINS` from environment values. Inside Container Apps, internal ingress routes by the Host header, so for each upstream it sets `Host` to that upstream's own name (the local config passes the gateway's host) and uses the container's own DNS resolver (the local `127.0.0.11` line only works under Docker). Routes: `/auth` and `/uploads` to auth, `/vrms` to backend-vrms (`/repairs` was dropped by `_root` spec 0008). `/ai` and `/analytics` are not routed. It answers CORS preflight only for the two app origins of that environment, not for any origin as the local config does.

**Revisions and probes**: single revision mode. Readiness probes call `/auth/health` and `/vrms/health` with a generous startup delay. They are readiness probes, not liveness probes, so a database outage does not restart loop the apps.

**Database connections**: the smallest Burstable server allows a few dozen connections. The services read `DB_POOL_MAX` (default 5) for the `pg` pool, and each app runs at most 2 replicas, so the total stays under the limit with room for the migration and seed jobs.

**CI (`ci.yml`, every repo)**: runs on `pull_request` into `development` and on `push` to `development`. Node comes from `.nvmrc` (24). Steps by repo:
- web-vrms: `npm ci`, `npm run lint`, `npm run typecheck`, `npm run build`.
- web-portal: `npm ci`, `npm run lint`, `npm run build`.
- backend-vrms and auth: `npm ci`, `npx prisma generate`, `npm run lint:ci` (the new non fixing script), `npm run build`, `npm test`.
- analytics-ai: `python -m py_compile` on the Python files.
It sets `permissions: contents: read`, cancels older runs of the same pull request (a push run to a branch is never cancelled, so every merge keeps its result), caches npm and times out at 15 minutes.

**CD for a backend (`deploy.yml`)**: on push to `development` (staging) or `workflow_dispatch` on `release` (production):
1. Log in with OIDC using that environment's app registration.
2. Staging: build the image from `Dockerfile.prod` tagged with the commit SHA and push it. Production: check the commit is reachable from `development` and that the SHA tagged image exists in the registry (`az acr repository show-tags`); fail if either is false.
3. Point the environment's migration job at the image (`az containerapp job update --image`), start it, and wait until it reaches a final state, with a 10 minute timeout. The job runs `npx prisma migrate deploy` with the same `DATABASE_URL` secret as the app. Stop if it fails.
4. Update the Container App to the image. With single revision mode and readiness probes, a revision that never becomes ready never takes traffic.
5. Run the smoke test.
It never runs a down migration.

**CD for a frontend (`deploy.yml`)**: log in with OIDC, build with that environment's `VITE_*` values (they are baked in at build time), read the Static Web App deployment token at run time with `az staticwebapp secrets list`, deploy with the Static Web Apps action, run the smoke test. Production first checks that the `release` commit is reachable from `development`.

**Gateway CD (workspace repo)**: staging deploys on a push to `main` that changes `infra/gateway/**` (the workspace repo has only `main`). Production is a manual run on its `release` branch. The image is tagged with the commit SHA.

**Seed job**: a third Container Apps job per environment, started manually, using the image's `seed` target. It runs `npm run seed` and sets `ALLOW_PRODUCTION_SEED=true` for that run only. The runner copies `tsconfig.json` so `ts-node -r tsconfig-paths` works (`ts-node` itself is already in the copied `node_modules`).

**Value sourcing** (where each value comes from):

| Action | Value | Source |
|---|---|---|
| Frontend build | `VITE_API_BASE_URL` | Gateway address, a Bicep output written to the repo variable `STAGING_API_URL` or `PROD_API_URL` |
| Frontend build | `VITE_PORTAL_URL`, `VITE_VRMS_URL` | Static Web Apps addresses, Bicep outputs written to `STAGING_PORTAL_URL`, `STAGING_VRMS_URL`, `PROD_PORTAL_URL`, `PROD_VRMS_URL` |
| Frontend build | `VITE_AUTH_MODE` | `portal`, fixed in the workflow |
| Gateway start | `AUTH_UPSTREAM`, `VRMS_UPSTREAM` | The internal app names of that environment, set by Bicep |
| Gateway start | `ALLOWED_ORIGINS` | The two Static Web Apps addresses of that environment, set by Bicep from their `defaultHostname` |
| Backend start | `CORS_ORIGINS` | The same two addresses, set by Bicep |
| Backend start | `NODE_ENV` | `production`, set by Bicep |
| Backend start | `PORT` | 3001 for auth, 3002 for backend-vrms, equal to the ingress target port, set by Bicep |
| Backend start | `JWT_ACCESS_EXPIRY` | `15m`, set by Bicep (the code reads this name; the local compose files use a different one) |
| Backend start | `DB_POOL_MAX` | `5`, set by Bicep |
| Backend start | `DATABASE_URL` (includes `sslmode=require`) | Container Apps secret, set by `set-secrets.sh` from the environment's private file |
| Backend start | `JWT_SECRET` | One value per environment, the same on auth and backend-vrms of that environment, from the private file via `set-secrets.sh` |
| Backend start | `SMTP_*` | From the private file via `set-secrets.sh`. The SMTP account is an open decision (Follow-up); blank means codes are only logged |
| Database setup | admin password and the four role passwords | Secure parameters from the private file, used by the Bicep apply and by `init.sql` |
| Image deploy | image tag | `github.sha` of the commit being deployed |
| Production deploy | version to release | the commit the `release` branch points to |
| Deploy steps | names and ids | repo variables written by `set-repo-variables.sh` from the Bicep outputs: `AZURE_CLIENT_ID_STAGING`, `AZURE_CLIENT_ID_PROD`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `ACR_NAME`, `STAGING_RG`, `PROD_RG`, `STAGING_APP`, `PROD_APP`, `STAGING_MIGRATE_JOB`, `PROD_MIGRATE_JOB`, `STAGING_SWA`, `PROD_SWA` (only those a repo needs) |
| Smoke test | URLs to call | `STAGING_API_URL` or `PROD_API_URL`, and the two app addresses |
| Budget | credit amount and owner email | Parameters of the subscription level Bicep file |

**Key invariants**:
- A migration that ships with a backend must work with the previous revision too (additive first), because a rollback never undoes the database.
- Staging deploys never touch production resources. The staging app registration has no rights on the production resource group.
- The seed never runs against production unless `ALLOW_PRODUCTION_SEED=true`, which only the manual seed job sets.
- Rollback: move `release` back to an older commit and rerun the production workflow. Its image must still exist. No down migration runs.
- The private secrets files are listed in `.gitignore` of the workspace repo.

**Security model**: anyone with write access to a repo can move its `release` branch and run the production workflow, since GitHub Free cannot protect branches or require a reviewer on private repos. What the setup does enforce is separation: the staging login can only be obtained from `development`, the production login only from `release`, and each is a role on its own resource groups (Contributor) plus the registry rights it needs. The database firewall admits any Azure service, including other customers' resources, so role passwords must be strong and unique. In production the services no longer accept localhost origins. Compliance scope: the system holds staff names, emails and phone numbers. HTTPS, the firewalled database and Container Apps secrets are the controls. No regulated data (payments, health) is involved.

**Configuration required**:
- `ALLOW_PRODUCTION_SEED`: guard for the seed, unset by default (auth and backend-vrms).
- `DB_POOL_MAX`: size of the database pool, default 5 (auth and backend-vrms).
- `NODE_ENV`, `PORT`, `JWT_ACCESS_EXPIRY`, `CORS_ORIGINS`, `SMTP_*`: already read by the services, now set per environment.
- Gateway: `AUTH_UPSTREAM`, `VRMS_UPSTREAM`, `ALLOWED_ORIGINS`.
- Repo variables listed under Value sourcing. New variables the services read go in `.env.example` only.

**Critical test scenarios**:
- Happy path: merge a change to backend-vrms `development`, staging updates itself, the smoke test passes, verifies **AC-3**, **AC-9**.
- Failure case: a migration that errors stops the deploy and the old revision keeps answering, verifies **AC-6**.
- Failure case: a revision that fails its readiness probe never takes traffic, verifies **AC-6**.
- Failure case: a PR with a lint error shows a red check, verifies **AC-1**, **AC-2**.
- Permission: a push to `development` cannot log in with the production app registration, verifies **AC-4**, **AC-11**.
- Permission: running the production workflow on a commit that is not on `development`, or has no image, fails, verifies **AC-4**.
- Isolation: a staging connection string cannot open `auth_prod`, verifies **AC-5**.
- Recovery: restore the latest backup to a scratch server and compare row counts, verifies **AC-8**.
- Safety: `NODE_ENV=production npm run seed` without the override exits without touching data, verifies **AC-13**.
- Persistence: upload a profile picture, restart the auth app, the picture still loads, verifies **AC-14**.

## Build plan

Order follows Tracer Bullet: CI first because it needs nothing from Azure, then the changes that make the apps deployable, then one thin staging thread end to end, then production. Target dates: Slice 1 this week, Slices 2 and 3 in the first week of November, Slice 4 in the second week, Slice 5 before the 20th.

**Slice 1: CI (no Azure needed)**
1. Add a `lint:ci` script (eslint without `--fix`) to backend-vrms and auth, satisfies **AC-1**, **AC-2**
2. Add `.github/workflows/ci.yml` to the five repos as described in Design, satisfies **AC-1**, **AC-2**, **AC-11**

**Slice 2: make the apps deployable**
3. Fix `Dockerfile.prod` in auth and backend-vrms: expose and read `PORT`, copy `prisma.config.ts` and `tsconfig.json` into the runner stage, run as a non root user, add a `seed` build target, satisfies **AC-6**, **AC-13**
4. Add public `GET /auth/health` (auth) and `GET /vrms/health` (backend-vrms) that run `SELECT 1` and return 200 or 503, satisfies **AC-6**, **AC-9**
5. In both services: guard the seed with `ALLOW_PRODUCTION_SEED`, read `DB_POOL_MAX` for the `pg` pool, and accept localhost origins only when `NODE_ENV` is not `production`, satisfies **AC-5**, **AC-13**
6. Add `staticwebapp.config.json` (fall back to `index.html` for every route, same as the nginx `try_files`) to web-vrms and web-portal, satisfies **AC-3**
7. Create `infra/gateway/` in the workspace repo: Dockerfile and nginx template as described under Gateway rules, satisfies **AC-3**, **AC-5**

**Slice 3: setup as code and staging**
8. Write the Bicep in `infra/`: shared (registry, PostgreSQL server with 14 day backups, four databases) and per environment (Log Analytics, Container Apps environment in single revision mode with readiness probes, gateway, auth with the Azure Files mount, backend-vrms, migration and seed jobs, two Static Web Apps, max 2 replicas), satisfies **AC-5**, **AC-6**, **AC-7**, **AC-8**, **AC-10**, **AC-14**
9. Write the subscription level Bicep file for the budget alerts (credit amount and owner email as parameters), and the bootstrap commands for resource groups and the cross group registry permission, satisfies **AC-10**, **AC-12**
10. Write `infra/scripts/`: `apply.sh`, `set-secrets.sh` and `set-repo-variables.sh`, plus the `.gitignore` entry and an example of the private file with fake values, satisfies **AC-5**, **AC-10**, **AC-11**
11. Check the credit type first (portal, Cost Management, Credits). Run `azure-validate` and the preflight what if, apply `shared` and `staging`, run `infra/db/init.sql` through Cloud Shell or a temporary firewall rule (owner owns each database), run `set-secrets.sh` and `set-repo-variables.sh`, satisfies **AC-5**, **AC-10**
12. Create the two Entra app registrations with their federated credentials, and the `release` branch in web-vrms, web-portal, backend-vrms, auth and the workspace repo, satisfies **AC-4**, **AC-11**

**Slice 4: CD to staging**
13. Add `deploy.yml` to auth and backend-vrms: build, push, migrate, update revision, smoke, satisfies **AC-3**, **AC-4**, **AC-6**, **AC-9**
14. Add `deploy.yml` to web-vrms and web-portal: build with environment values, fetch the deployment token at run time, deploy, smoke, satisfies **AC-3**, **AC-4**, **AC-9**
15. Add the gateway deploy workflow in the workspace repo, satisfies **AC-3**, **AC-4**
16. First end to end staging deploy of all four repos and the gateway, then start the seed job and run the smoke test. Upload a profile picture, restart auth, confirm it survives, satisfies **AC-3**, **AC-9**, **AC-13**, **AC-14**

**Slice 5: production and safety**
17. Apply the `prod` Bicep, deploy production once from `release`, start the seed job once, satisfies **AC-4**, **AC-7**, **AC-13**
18. Restore drill: restore the latest backup to a scratch server, compare row counts, delete the server, satisfies **AC-8**
19. Write `infra/RUNBOOK.md`: the bootstrap steps, rollback, moving to another subscription with `pg_dump` and restore, scaling staging to zero, rotating secrets and the JWT secret, satisfies **AC-10**, **AC-12**

## Consequences

**Positive**:
- Broken builds stop at the pull request, and staging updates itself, so every slice can be demoed.
- Frontends cost nothing, idle staging costs almost nothing, and the database has real backups.
- The whole setup is code, so losing a subscription does not mean losing the system.
- Staging can never obtain production rights, even though GitHub Free has no environment protection.

**Negative / tradeoffs**:
- Production approval is only a person moving `release` and clicking, not an enforced second reviewer, and the Free plan cannot enforce branch protection or required checks. CI is a warning light, not a gate.
- Every deployable repo gets one more long lived branch (`release`) that the team must keep tidy.
- The shared database server means a server level problem affects staging and production together, and it is the biggest single cost.
- With analytics-ai not deployed, `/analytics` and `/ai` return nothing and the web app shows its hardcoded sample numbers on the analytics page, which looks like real data in a demo. This needs fixing before the demo (see Follow-up).
- Production keeps three apps running all the time. A rough monthly estimate for production plus staging is $40 to $70, which is fine for one month on $100 of credit and tight beyond it. The real prices were not confirmed (the Azure pricing pages did not load), so check the Azure pricing calculator in task 11.
- Frontends are rebuilt per environment, because the API address is baked in at build time, so staging and production do not run the same build.
- Secrets live in a private file on the subscription owner's machine. If that person is unavailable, nobody else can re-apply secrets. The runbook must say where a backup copy is kept.

**Neutral**:
- The local docker compose files stay as they are for development.
- Static Web Apps gives each app a random looking default hostname, so the CORS list and repo variables come from Bicep outputs. Bicep can create the apps first and use their `defaultHostname`, so there is no circular dependency.
- Credit use and the 12 month or 30 day limit start when resources are created, so apply the Bicep close to when you need it.
- backend-vrms also carries a copy of the auth controller that the gateway hides behind auth's `/auth`. It is harmless and unreachable.

## Follow-up

- [ ] Confirm which Azure credit you have (Students: $100 over 12 months, no card; standard free account: $200 over 30 days with a card) before creating resources. The 30 day type means the clock starts at task 11.
- [ ] Credit rotation: use one subscription and add teammates as members. Azure for Students is one account per person and the page does not say credit can be shared, so rotating accounts is not documented as allowed. Plan the move (task 19) before credit hits zero, because a disabled subscription disables its resources.
- [ ] Decide the email provider for OTP and password reset (`SMTP_*`). With it blank, codes are only logged and password reset cannot work in Azure. The Semaphore SMS key has the same question.
- [ ] Analytics page in production: hide it or label the sample data before the demo, until feature 3 puts real analytics in backend-vrms.
- [ ] Scope row 26: replace "Vercel for frontends, Render for services" with Azure, replace "pushing to main deploys to staging" with `development`, and "production deploys need approval" with the `release` branch run.
- [ ] Confirm the PostgreSQL 12 month free offer applies to your subscription type (it is listed for the standard free account, unconfirmed for students).
- [ ] Add the Azure skills to the `## Agent skills` section of `AGENTS.md` (`/sync` or `/audit` owns that). `azure-prepare` and `azure-deploy` assume the Azure Developer CLI (azd), which this spec does not use, so prefer the five skills named in Decision.
- [ ] MCP servers you chose: connect the Azure MCP server and the GitHub MCP server in your own MCP settings, with read only roles where possible. They are used automatically once connected.
- [ ] Revisit the GitHub plan if anyone pushes straight to `development` or moves `release` carelessly, since only a paid plan can enforce reviews and required checks.
- [ ] Feature 27 (error monitoring) will decide Application Insights or similar. This spec only creates a Log Analytics workspace per environment.
- [ ] Both NestJS services ship a Redis container locally that no code uses. Remove it from the compose files when convenient.
- [ ] The Azure Container Apps path based routing feature could replace the nginx gateway (one fewer image). Check whether it is generally available in your region before choosing it over nginx.

## Rationale

Reasoning, options and sources: see [rationale.md](rationale.md).
