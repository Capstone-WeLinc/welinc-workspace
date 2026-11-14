# 0008. Host the WeLinc suite on Azure with GitHub Actions for CI and CD

**Date**: 2026-10-25
**Status**: In Progress
**Updated**: 2026-11-14 (suite rework, `/architect`, cross checked on another model, 25 fixes applied). This version hosts the whole suite, not only VRMS: the shared services, VRMS, VMMS and BMS in one subscription, on the custom domain contract 0001 requires, timed to the defense dates. It folds in what the suite specs decided since: ES256 keys (`_root` 0002), sessions and cookies (0003), the role catalog (0004), the seed (0006), the gateway in `infra/gateway/` (0008), email codes (0009), startup checks (0010), account activity (0011), the suite admin (0013, whose AC-12b this spec added) and the move kit (0014). Slice 1 (CI) is built and verified. Amended the same day after the Slice 2 build: the picture policy allows our own domain, `--reference` credits the knowledge base to a setup actor and fills an empty database only, and `admin:recover --create` sends no admin alert.

## Summary

The whole WeLinc suite goes on Azure, paid from a $200 free account that you sign up for on the day staging is first applied (around Nov 18 to 19), so the 30 days of credit last past the final defense on Dec 5. Every web app is a free Static Web App, every service runs on Azure Container Apps behind the one gateway, and each environment (staging and production) gets its own small PostgreSQL server. Everything lives on `welinc.tech` (the addresses in contract 0001), mail goes out through Brevo, and production keeps every app warm so the defenses never wait on a cold start. VMMS and BMS deploy into the same setup with a workflow template you give them; production must be live before the mock defense on Nov 28, and nothing risky changes between Nov 28 and Dec 5.

## Requirements

**User stories**:
- As a developer, I want every pull request checked automatically so that a broken build is caught before it merges.
- As a developer of any WeLinc group, I want a merge to `development` to reach staging without manual steps so that each system can be tested together before the integration defense.
- As the team lead, I want production to change only when a person chooses so that a bad merge cannot reach the defense system.
- As a panel member, I want every screen to answer quickly on the first click so that the demo looks like a working product.
- As the team, we want the whole setup recreatable and the data copyable so that losing the subscription does not mean losing the system.

**Acceptance criteria** (the contract, each independently checkable):
- **AC-1**: Every pull request into `development` in web-vrms, web-portal, backend-vrms, auth and analytics-ai runs a CI workflow (install, lint without fixing, build, tests where the repo has them) and shows pass or fail on the PR.
- **AC-2**: CI fails the run when lint, the build or a test fails.
- **AC-3**: A push to `development` in web-vrms, web-portal, backend-vrms or auth deploys that repo to staging with no manual step. A push to `main` in the workspace repo that changes `infra/gateway/**` deploys the gateway to staging the same way. A VMMS or BMS repo that adds the template from `docs/integration/hosting.md` gets the same behavior for its own apps.
- **AC-4**: Production deploys only from a manual "Run workflow" run on the `release` branch of that repo. A push or merge to `development` never deploys production. The `release` commit must be reachable from `development` (from `main` for the workspace repo), and for a backend its image must already exist in the registry (built by the staging deploy of that commit), otherwise the run fails. The VMMS and BMS template works the same way.
- **AC-5**: Staging and production are fully separate: their own PostgreSQL server, databases, database roles and passwords, signing keys (`AUTH_SIGNING_KEYS`), client keys, mail credentials, Gemini key, allowed origins and addresses. A staging service cannot reach the production server (different server, different firewall). In production no service accepts a localhost origin, and every production URL setting refuses localhost at boot (spec 0010).
- **AC-6**: Database migrations run automatically before a backend revision takes traffic, after `npm run env:check` passes in the same job. If the check, a migration, or the new revision's startup or readiness probe fails, the deploy fails and the previous revision keeps serving. The deploy succeeds only once the revision named after its commit is ready and holds 100% of traffic.
- **AC-7**: Every address any client or setting uses is HTTPS on `welinc.tech`, exactly as contract 0001 section 1 lists them: `portal.`, `vrms.`, `vmms.`, `bms.` and `api.welinc.tech` for production, and the same names with a `staging-` prefix for staging. Certificates are Azure managed and renew on their own. The default Azure hostnames stay reachable (Azure can't turn them off) but no setting, client row or document uses them.
- **AC-8**: Database backups are automatic on both servers with at least 14 days kept, and one restore of the production server into a scratch server has been tested before Nov 26.
- **AC-9**: After every deploy a smoke test checks `https://<api>/health`, `/auth/health`, `/vrms/health` (each confirming a database connection), and that the portal and VRMS web return their page. It runs only after AC-6's revision check, retries for up to 3 minutes, and any failure marks the deploy failed. The VMMS and BMS template does the same for their health route and web app.
- **AC-10**: Running the Bicep files against empty resource groups in any subscription recreates the whole system, minus data. The runbook lists the one time steps (resource providers, resource groups, budget, Entra app registrations, `release` branches, DNS records, Brevo domain records) and covers moving data with `pg_dump` and restore and copying blobs and the file share.
- **AC-11**: No long lived Azure password is stored in GitHub, and no secret value is committed to any repo. Deploys log in with OpenID Connect (a short lived pass). Each deploying repo family has its own app registration per environment: ours (shared services, VRMS, gateway), VMMS's and BMS's. A staging login trusts only `development` (`main` for the workspace), a production login only `release`, and the VMMS and BMS logins can update and start only their own group's apps and jobs. The shared registry is the one exception: any group's push right covers every image in it (accepted, see Security model). Workflows default to `contents: read`.
- **AC-12**: A budget on the subscription emails you at $50, $100, $150 and $180 of spend. The runbook says how to stop staging (scale to zero and stop its PostgreSQL server) in one command.
- **AC-13**: The seed guards hold on Azure: welinc-auth's seed refuses production and runs on staging only with `SEED_ALLOW=staging` (spec 0006), and backend-vrms's seed gets the same guard. Staging is seeded once at first deploy by a manually started seed job, with the public test passwords from `docs/integration/seed-accounts.md`.
- **AC-14**: Files survive restarts: profile pictures uploaded to auth (Azure Files share at `/app/uploads`) and ticket files in VRMS (Blob Storage, `vrms-attachments` container, spec 0017) are still there after a restart, a new revision or a scale to zero.
- **AC-15**: Production starts with no seed people. The migration job runs `npm run db:deploy` (migrations plus `catalog:sync`). Then auth's seed job runs `npm run seed:clients` with the production `CLIENT_*` values, then `npm run admin:recover -- --create --email <you> --name "<your name>" --reason "<text>"` (suite spec 0013 AC-12b), which creates the first suite admin and mails the setup code (if the mail fails, the job exits 1 and the person uses Forgot password once mail works). VRMS production gets reference data only (`npm run seed -- --reference`: garages, vehicles, knowledge base, settings), never mechanics, drivers, tickets or knowledge suggestions. Every knowledge entry is credited to a fixed setup actor (name `WeLinc setup`, email `setup@welinc.tech`, no user id, no role), dated at seed time with one `ENTRY_CREATED` history row. `setup@welinc.tech` is only a label: it is never created as a mailbox, or its owner would appear to be the setup actor. `--reference` runs in any environment (no `SEED_ALLOW`); its only guard is that it refuses (exit 1, nothing written) when the database already holds any garage, vehicle or knowledge entry, whatever its status. The whole run is one transaction, so a failure leaves nothing behind and a rerun works. Everyone else is invited from the portal with a setup code.
- **AC-16**: Replicas follow one rule. Production: every app keeps at least 1 replica. Staging: the gateway and every app that runs work on a timer (welinc-auth, backend-vrms, and any VMMS or BMS service its group marks as timed) keep 1 replica; every other staging app scales to zero, and a first call to it may answer 504 while it wakes. welinc-auth is set to at most 1 replica (its sign in limits count in its own memory; during a deploy the old and new revision overlap for a moment, which is accepted). BMS's inner services (booking, dispatch, completion, projection, analytics) run at most 1. Every other app runs at most 2.
- **AC-17**: Mail works before anyone is invited: welinc-auth sends through Brevo SMTP from `noreply@welinc.tech`, the domain carries Brevo's SPF and DKIM records and a DMARC record, and a code sent on staging to a real Gmail inbox arrives in the inbox (not spam) within 2 minutes.
- **AC-18**: The real client address reaches the services: on staging, two sign ins from two different networks show two different addresses in `account_events`, with the gateway at `TRUST_EDGE_PROXY=1` and the services at `TRUST_PROXY_HOPS=2` (suite spec 0008 follow up).
- **AC-19**: The VMMS and BMS services run inside the same Container Apps environment on internal ingress, reachable only through the gateway's `/vmms/` and `/bms/` routes, each with its own databases on its environment's server (`vmms`, and `bms_booking`, `bms_dispatch`, `bms_completion`, `bms_analytics`). Until a group deploys, its routes answer 502 `UPSTREAM_UNAVAILABLE` and nothing else breaks.
- **AC-20**: A shutdown copy exists before the credit ends: on or after Dec 6 (after the final defense) and before the credit end date, every production database is dumped with `pg_dump`, the blob container and file share are copied, and the copies sit on your machine and one teammate's. The runbook step records the date it ran.
- **AC-21**: Each PostgreSQL server's connections stay inside its budget (the table in Design) at full scale plus one deploy overlap: every service caps its pool with `DB_POOL_MAX`, and the sum never exceeds 35.

## Decision

**Chosen option**: Option 1 kept and widened: Azure Static Web Apps, Container Apps and PostgreSQL Flexible Server, deployed by GitHub Actions and described in Bicep, now for the whole suite on `welinc.tech`, with one PostgreSQL server per environment and a deploy template for VMMS and BMS.

Every web app (portal, VRMS, VMMS, BMS) runs on a Static Web App per environment (8 of the 10 the Free plan allows). Every service, the gateway included, runs on Container Apps from images in one Azure Container Registry. Each environment has its own Burstable PostgreSQL server holding that environment's seven databases. Production is fully warm; staging is warm only for the gateway and where a timer must keep running. Each group deploys its own apps with its own scoped Azure login.

**Implementation skills**: `azure-container-apps` (`microsoftdocs/agent-skills`, `.claude/skills/azure-container-apps/`) · `azure-container-registry` (`microsoftdocs/agent-skills`, `.claude/skills/azure-container-registry/`) · `azure-static-web-apps` (`microsoftdocs/agent-skills`, `.claude/skills/azure-static-web-apps/`) · `azure-blob-storage` (`microsoftdocs/agent-skills`, `.claude/skills/azure-blob-storage/`) · `azure-deployment-preflight` (`github/awesome-copilot`, `.claude/skills/azure-deployment-preflight/`) · `docker-patterns` (`.claude/skills/docker-patterns/`, its examples use Node 22; we run 24). Never `azure-prepare` or `azure-deploy` (they assume azd).

## Proposed stack

| Layer | Choice | Reason |
|---|---|---|
| Subscription | One Azure free account ($200, 30 days from signup), signed up the day staging is first applied | The credit window then covers the mock (Nov 28), integration (Dec 4) and final (Dec 5) defenses with two weeks to spare. |
| Frontends | Static Web Apps, Free plan: portal, VRMS, VMMS and BMS web, per environment (8 apps) | Free, HTTPS and CDN, custom domains with managed certificates included. |
| Services | Container Apps, Consumption plan, one Container Apps environment per WeLinc environment, single revision mode, startup and readiness probes | Runs every group's `Dockerfile.prod`. Single revision keeps the old revision serving until the new one is ready. About 15 apps per environment. |
| Replicas | Production: min 1 on every app. Staging: min 1 on the gateway and timed apps, the rest 0. Auth max 1, BMS inner services max 1, others max 2 | A cold start costs 10 to 30 seconds per app, and timers stop at zero (VRMS's directory poll, auth's session sweeper and temporary grant sweep). |
| Gateway | `infra/gateway/` image (suite spec 0008) as its own Container App, the only public ingress | One template for local and hosted; the routes for every system already exist. |
| Database | Two PostgreSQL Flexible Servers, Burstable B1ms, PostgreSQL 16: one production (on the free 750 hours), one staging (paid from credit, stoppable) | Each server has its own ~50 connections (about 35 usable) for its seven databases, and staging can never reach production. |
| Uploads | Two storage accounts per environment. Files account (shared key on): the Azure Files share auth mounts at `/app/uploads`. Blob account (shared key off): the `vrms-attachments` container, reached with backend-vrms's system assigned managed identity | Container Apps mounts Azure Files only with an account key; Blob works with an identity and the code already supports it (spec 0017). |
| Registry | One Azure Container Registry, Basic (10 GB), shared by both environments and every group, with a weekly purge of old tags | Build once on staging, promote the same image to production. |
| Domain and DNS | `welinc.tech` (GitHub Student Developer Pack offer), DNS kept at the registrar | Contract 0001 needs one registered domain for the cookies; registrar DNS is free and only needs CNAME and TXT records. |
| Mail | Brevo SMTP (free plan, about 300 mails a day), sender `noreply@welinc.tech` with SPF, DKIM and DMARC | Only the `SMTP_*` values change; domain records keep codes out of spam. |
| AI | Gemini free tier, a separate key per environment | Defense traffic stays far below the free caps, and VRMS works without the AI if a cap is hit. |
| Logs | One Log Analytics workspace per environment, 30 day retention, a daily cap | Keeps logs inside the free ingestion amount. Error monitoring stays with feature 27. |
| CI | GitHub Actions `ci.yml` in each repo (built) | Free minutes cover it. |
| CD | `deploy.yml` per deployable repo, a gateway workflow in the workspace, and a copyable template for VMMS and BMS | Each repo ships itself; production uses `workflow_dispatch` on `release`. |
| Azure login | OpenID Connect, six app registrations (ours, VMMS's, BMS's; staging and production each), no client secret | A group's login can only touch that group's apps (the registry aside). |
| Setup as code | Bicep in `infra/` of the workspace repo, applied by `apply.sh` in two passes (without, then with custom domains) | Recreatable in another subscription; certificates need the DNS records first. |
| Secrets | A private file per environment, kept by you, passed by `apply.sh` into Bicep as secure parameters; `rotate-secret.sh` for changing one value | A Container App's secret list is replaced on every apply, so the apply must carry them. |
| Not deployed | `welinc-backend-vrms-analytics-ai` (retired by feature 3), Redis, MongoDB, Azurite | Nothing in the hosted path uses them. |

**Free plan and subscription limits to respect**: Static Web Apps Free allows 10 apps per subscription (8 used), 2 custom domains per app, 100 GB of bandwidth a month and 250 MB per app, with no uptime promise. The free 750 PostgreSQL hours cover one B1ms (production). GitHub Free gives the whole organization 2,000 Actions minutes a month on private repos, shared by every group's builds. A new free subscription has low regional vCPU quotas, and not every region offers B1ms to trial accounts, so the region is picked after the quota check in task 12.

## Design

**Timeline** (the defense dates set it):

| Date | What is true |
|---|---|
| By Nov 18 | Slice 2 done and the Bicep written, all without an Azure account. Domain registered, Brevo set up. |
| Nov 18 to 19 | You sign up for the free account and apply staging (both passes). The credit ends about Dec 18 to 19. |
| By Nov 22 | Shared services and VRMS deploy to staging by themselves; mail, login and files proven there. |
| From Nov 17 | VMMS and BMS add the template once their S11 moves merge; their apps land on staging. |
| By Nov 26 | Production applied, bootstrapped and smoke tested; restore drill done. |
| Nov 28 to Dec 5 | Freeze: no infrastructure change, no account move, no migration that isn't additive. Production deploys only for fixes. |
| Dec 6 to before the credit ends | Shutdown copy (AC-20), then let the subscription stop. Nothing is billed to a card. |

**Environments**

| Item | Staging | Production |
|---|---|---|
| Resource group | `rg-welinc-staging` | `rg-welinc-prod` |
| Shared resource group | `rg-welinc-shared` holds the registry | same |
| PostgreSQL server | `psql-welinc-staging` (B1ms, paid, stoppable) | `psql-welinc-prod` (B1ms, free hours) |
| Databases | `auth`, `vrms`, `vmms`, `bms_booking`, `bms_dispatch`, `bms_completion`, `bms_analytics` | same names on its own server |
| Database roles | per database: an owner role that runs migrations, and an app role the service connects as | same |
| Addresses | `staging-api.`, `staging-portal.`, `staging-vrms.`, `staging-vmms.`, `staging-bms.welinc.tech` | `api.`, `portal.`, `vrms.`, `vmms.`, `bms.welinc.tech` |
| `NODE_ENV` | `production` | `production` |
| Replicas | min 1 on the gateway and timed apps, 0 elsewhere | min 1 everywhere |
| Deploy trigger | push to `development` (`main` for the gateway) | manual `workflow_dispatch` on `release` |
| People | the suite seed, public test passwords | none seeded; `admin:recover --create`, then invites |

**Network**: the gateway has public ingress with a custom domain. Every other app has internal ingress with `allowInsecure` off, so every internal call is HTTPS on port 443 and the ingress `targetPort` equals the app's `PORT` (gateway 3000, auth 3001, backend-vrms 3002, VMMS and BMS from contract 0001 section 2). Each PostgreSQL server allows Azure services only, SSL required. Work from a laptop (`init.sql`, dumps, the restore drill) goes through a temporary firewall rule for your address that `apply.sh` and the runbook commands add and remove. The blob account allows backend-vrms's identity only, and the browser gets signed links (spec 0017); its CORS rules allow the VRMS web origin for `GET`.

**Internal addresses**: `https://<app name>.internal.<environment default domain>`, where the domain is the Container Apps environment's `properties.defaultDomain`, a Bicep output. Every `*_UPSTREAM`, `AUTH_INTERNAL_URL` and `AUTH_JWKS_URL` uses this form (nginx ignores search domains, and `AUTH_JWKS_URL` must be HTTPS because the startup check refuses anything else in production).

**Gateway on Azure**: the same image as local, with hosted settings: each `*_UPSTREAM` is the internal address above, `ALLOWED_ORIGINS` the four web origins of that environment, `TRUST_EDGE_PROXY=1`, `GATEWAY_HSTS=max-age=86400`, rate 20 and burst 40. An upstream that isn't deployed yet answers 502 on its own routes only.

**Cookies and the domain**: every web app and the gateway share `welinc.tech`, so the refresh and SSO cookies are first party (contract 0001 section 7). Hosted, the cookies carry `Secure` and the `__Secure-` prefix (`SSO_COOKIE_SECURE=true` on auth, `SESSION_COOKIE_SECURE=true` on backend-vrms).

**Custom domains in two passes**: certificates can only be issued once the DNS records exist, so `apply.sh` runs twice per environment. Pass 1 (`bindDomains=false`) creates everything with default hostnames. `dns-records.sh` then prints, from the Bicep outputs, a CNAME per name (to its Static Web App or the gateway's default hostname), the `asuid.<name>` TXT record holding the environment's `customDomainVerificationId`, and any TXT record a Static Web App asks for. You add them at the registrar and wait until `dig` shows them. Pass 2 (`bindDomains=true`) adds the Static Web App custom domains (CNAME validation) and, for the gateway, binds the hostname with `bindingType: Disabled`, creates the managed certificate, then switches the binding to `SniEnabled`.

**Revisions and probes**: single revision mode. Each deploy sets `revisionSuffix` to the short commit SHA. A startup probe on the health route allows up to 240 seconds (failure threshold times period) for boot and migration warm up; a readiness probe on the same route follows. Neither is a liveness probe, so a database outage does not restart loop the apps. `/health` routes may add the commit SHA later; not required.

**Database connections** (each B1ms allows about 50, about 35 usable after Azure's reserved ones):

| Clients on one server | Pool | Replicas at most | Connections |
|---|---|---|---|
| welinc-auth | 3 | 1 (2 during a deploy) | 6 |
| backend-vrms | 3 | 2 | 6 |
| VMMS backend and analytics | 2 each | 2 and 1 | 6 |
| BMS gateway, booking, dispatch, completion, projection, analytics (those with a pool) | 2 each | 1 each | 12 |
| One migration or seed job at a time | 2 | 1 | 2 |
| **Total** | | | **32** |

Today neither service sets a pool size (`pg.Pool` defaults to 10), so `DB_POOL_MAX` is a code change in both, and `hosting.md` asks VMMS and BMS to read the same setting. Server parameters on both: `idle_in_transaction_session_timeout=60000` (a transaction left open holds back the directory feed, suite spec 0005), and `azure.extensions` includes `VECTOR` (pgvector, spec 0013).

**Connection strings**: `postgresql://<role>:<password>@<server>.postgres.database.azure.com:5432/<db>?sslmode=require&uselibpqcompat=true`. The last flag keeps `sslmode=require` meaning "encrypted" in node postgres instead of full certificate checking. Role passwords are 32 random hex characters, so they never need escaping in a URL.

**Database roles** (`infra/db/init.sql`, run as the server admin once per database, before the first migration): create `<db>_owner` and `<db>_app`; make `<db>_owner` own the database and its `public` schema (PostgreSQL 16 lets only the owner create there); `ALTER DEFAULT PRIVILEGES FOR ROLE <db>_owner` granting `<db>_app` `SELECT, INSERT, UPDATE, DELETE` on tables and `USAGE, SELECT` on sequences, so tables made by later migrations are covered; on `vrms`, `CREATE EXTENSION IF NOT EXISTS vector` as the admin. The append only rule on `audit_logs` (spec 0021) runs after migrations, because the table doesn't exist when `init.sql` runs: backend-vrms's migration job ends with `REVOKE UPDATE, DELETE, TRUNCATE ON audit_logs FROM vrms_app` (idempotent, safe on every deploy).

**Fresh databases, no history to move**: every hosted database starts empty and runs all migrations in order on first deploy. The spec 0013 AC-28 export before the drop of VRMS `permission_changes` only matters for a database that already holds rows, so it does not apply here. The permission matrix lives in welinc-auth from the first `catalog:sync`.

**CI (`ci.yml`, every repo)**: built (Slice 1). Runs on `pull_request` into `development` and on `push` to `development`, Node from `.nvmrc` (24), `permissions: contents: read`, cancels older runs of the same PR, caches npm, times out at 15 minutes.

**CD for a backend (`deploy.yml`)**: on push to `development` (staging) or `workflow_dispatch` on `release` (production):
1. Log in with OIDC using that environment's app registration.
2. Staging: build `Dockerfile.prod` (the runner image) and its `seed` target, tag both with the commit SHA, push them. Production: check out with full history, check the commit is reachable from `development` (`git merge-base --is-ancestor`) and the SHA tagged image exists in the registry; fail if either is false.
3. Point the migration job at the `seed` image of that SHA, start it with `az containerapp job start`, and poll `az containerapp job execution show` until it ends (`replicaTimeout` 600, `replicaRetryLimit` 0). The job runs `npm run env:check`, then `npm run db:deploy` (auth) or `npx prisma migrate deploy` plus the `audit_logs` revoke (backend-vrms), connected as the owner role. On failure, print the job's logs and stop.
4. Update the Container App to the runner image with `revisionSuffix` set to the short SHA.
5. Poll until `latestReadyRevisionName` is the new revision and it holds 100% of traffic, up to 6 minutes; on timeout, fail (the old revision keeps serving).
6. Run the smoke test.
It never runs a down migration.

**CD for a frontend (`deploy.yml`)**: log in with OIDC, build with that environment's `VITE_*` values as build settings (a plain `npm run build` refuses missing or localhost values, spec 0010), read the Static Web App deployment token at run time with `az staticwebapp secrets list`, deploy with the Static Web Apps action, run the smoke test. Production first checks the `release` commit is reachable from `development`.

**Gateway CD (workspace repo)**: staging on a push to `main` that changes `infra/gateway/**`; production by a manual run on the workspace's `release` branch, which must be reachable from `main`; image tagged with the commit SHA; same revision wait as a backend.

**OIDC trust**: each app registration holds one federated credential per repo it deploys. Staging subjects are `repo:<org>/<repo>:ref:refs/heads/development` (`main` for the workspace); production subjects are `repo:<org>/<repo>:ref:refs/heads/release`, because a manual run on `release` carries that ref. Ours covers five repos (auth, backend-vrms, web-vrms, web-portal, workspace); VMMS's and BMS's cover theirs.

**Azure rights per login**: ours is Contributor on its environment's resource group and `AcrPush` on the registry. A group's login gets a custom role on its own apps and jobs only (Container App write, job start and write, Static Web App `listSecrets`), `Microsoft.App/managedEnvironments/join/action` on the environment, and `AcrPush` on the registry. No group login has any right on `rg-welinc-prod` from staging, or on another group's apps.

**VMMS and BMS template** (`docs/integration/hosting.md`): one page per group listing its apps, jobs and databases as Bicep already created them; for each app its `PORT`, health route, `DB_POOL_MAX` (2), whether it is timed, `TRUST_PROXY_HOPS=2` for services that receive traffic through the suite gateway (hops inside BMS, such as `bms-gateway` to booking, are BMS's call); the repo variables to set; and two workflow files to copy (`deploy-backend.yml`, `deploy-web.yml`) that work exactly like ours. Secrets have one path: the group sends each secret privately (client private key, internal keys such as `BMS_INTERNAL_SERVICE_KEY` and `CUSTOMER_TRACKING_SECRET`, Gemini or other provider keys), you put it in that group's section of the private file, and `apply.sh` applies it. Their database URLs and roles come from `init.sql` like ours. They never get rights on the shared services or VRMS.

**Seed and bootstrap jobs**: every job runs from the service's `seed` image, a full source image (it carries `src/`, `scripts/`, `prisma/`, `tsconfig.json` and `prisma.config.ts`, since `ts-node` needs them) with the same settings and secrets as its app. Commands are given at start with `az containerapp job start --command --args`.
- Migration job (owner role): `db:deploy` or `migrate deploy`, as in CD.
- Auth seed job (app role): staging runs `npm run seed:clients`, then `npm run seed` with `SEED_ALLOW=staging`. Production runs `npm run seed:clients`, then `npm run admin:recover -- --create --email <you> --name "<your name>" --reason "<text>"`. `admin:recover` boots the whole app, so the job needs `AUTH_SIGNING_KEYS` and the SMTP settings. `seed:clients` is run again whenever a group sends its client key, because a row's `jwks` changes only when its value is set.
- VRMS seed job (app role): staging `npm run seed` with `SEED_ALLOW=staging`; production `npm run seed -- --reference` (AC-15: the setup actor, empty database only, one transaction). `--reference` needs no `SEED_ALLOW`.
- Then each group seeds its own copy of `people.json` on staging (S11 guides). No `SEED_ALLOW` on production, ever.

**Value sourcing** (where each value comes from; `<api>`, `<portal>`, `<vrms>`, `<vmms>`, `<bms>` are that environment's names from contract 0001 section 1; every origin is bare, no trailing slash):

| Action | Value | Source |
|---|---|---|
| Frontend build | `VITE_API_BASE_URL` | `https://<api>`, repo variable `PROD_API_URL` or `STAGING_API_URL` |
| Frontend build | `VITE_PORTAL_URL` | `https://<portal>`, repo variable `PROD_PORTAL_URL` or `STAGING_PORTAL_URL` |
| Gateway start | `AUTH_UPSTREAM`, `VRMS_UPSTREAM`, `VMMS_UPSTREAM`, `VMMS_ANALYTICS_UPSTREAM`, `BMS_UPSTREAM` | the internal addresses, set by Bicep |
| Gateway start | `ALLOWED_ORIGINS` | `https://<portal>,https://<vrms>,https://<vmms>,https://<bms>`, set by Bicep from the domain parameter |
| Gateway start | `TRUST_EDGE_PROXY`, `GATEWAY_HSTS`, `GATEWAY_RATE_PER_SECOND`, `GATEWAY_RATE_BURST` | `1`, `max-age=86400`, `20`, `40`, set by Bicep |
| Auth start | `AUTH_ISSUER` | `https://<api>/auth`, set by Bicep |
| Auth start | `PORTAL_URL` | `https://<portal>`, set by Bicep |
| Auth start | `CORS_ORIGINS` | the four web origins, set by Bicep |
| Auth start | `AUTH_SIGNING_KEYS` | a fresh key set per environment made with `npm run keys:rotate`, in the private file, passed by `apply.sh` |
| Auth start | `SSO_COOKIE_SECURE`, `TRUST_PROXY_HOPS`, `NODE_ENV`, `PORT`, `DB_POOL_MAX`, `ADMIN_SIGN_IN_CODE` | `true`, `2`, `production`, `3001`, `3`, on; set by Bicep |
| Auth start | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` | `smtp-relay.brevo.com`, `587`, the Brevo SMTP login, the Brevo SMTP key per environment, `WeLinc <noreply@welinc.tech>`; the key from the private file, the rest set by Bicep |
| Auth start | `GEOIP_COUNTRY_FILE`, `GEOIP_ASN_FILE` | paths inside the image, filled by `npm run geo:fetch` in the image build (rebuild monthly; the DB-IP credit goes in the hosted docs) |
| Auth start | `DATABASE_URL` | the app role URL above, private file |
| Auth seed job | `API_PUBLIC_URL` | `https://<api>`, set on the job by Bicep (read by `seed:clients` to build each callback; not part of auth's boot schema) |
| Auth seed job | `CLIENT_VRMS_WEB_ADDRESS`, `CLIENT_VMMS_WEB_ADDRESS`, `CLIENT_BMS_WEB_ADDRESS` | `https://<vrms>`, `https://<vmms>`, `https://<bms>`, set on the job by Bicep (the portal's address comes from `PORTAL_URL`) |
| Auth seed job | `CLIENT_VRMS_JWKS`, `CLIENT_VMMS_JWKS`, `CLIENT_BMS_JWKS`, `CLIENT_VMMS_ANALYTICS_JWKS`, `CLIENT_BMS_ANALYTICS_JWKS` | each client's public key set from `npm run keys:client` per environment (VRMS's made by you, the others sent by their groups), private file. The mobile clients take none |
| Auth seed job | `SEED_ALLOW` | `staging` on the staging job only; never on production |
| Auth seed job | `admin:recover` email, name and reason | your email and name, and a reason such as "Production bootstrap", typed in the job start command |
| VRMS start | `AUTH_CLIENT_ID`, `AUTH_CLIENT_PRIVATE_KEY` | `vrms`, and the private key from `keys:client` per environment (private file) |
| VRMS start | `AUTH_INTERNAL_URL`, `AUTH_JWKS_URL` | `https://<auth internal address>`, and the same plus `/auth/.well-known/jwks.json`, set by Bicep |
| VRMS start | `AUTH_ISSUER`, `AUTH_PUBLIC_URL` | both `https://<api>/auth`, set by Bicep |
| VRMS start | `API_PUBLIC_URL`, `WEB_APP_URL`, `PORTAL_URL` | `https://<api>`, `https://<vrms>`, `https://<portal>`, set by Bicep |
| VRMS start | `CORS_ORIGINS` | `https://<vrms>` only, set by Bicep |
| VRMS start | `SESSION_COOKIE_SECURE`, `TRUST_PROXY_HOPS`, `NODE_ENV`, `PORT`, `DB_POOL_MAX` | `true`, `2`, `production`, `3002`, `3`, set by Bicep |
| VRMS start | `STORAGE_ACCOUNT_URL`, `STORAGE_PUBLIC_URL`, `STORAGE_CONTAINER` | the blob account's endpoint (`https://<account>.blob.core.windows.net`) for both, and `vrms-attachments`; set by Bicep. No connection string: the system assigned identity holds Storage Blob Data Contributor |
| VRMS start | `GEMINI_API_KEY` | a free tier key per environment, private file |
| VRMS start | `DATABASE_URL` | the app role URL, private file |
| Migration job | `DATABASE_URL` | the owner role URL, private file, set on the job only |
| Auth file share | storage account key | read by Bicep with `listKeys()` from the files account and given to the environment's storage definition; never in the private file |
| Database setup | admin password, owner and app role passwords | 32 hex characters each, in the private file, passed as secure parameters to Bicep and `init.sql` |
| First apply | app images | Microsoft's public quickstart image on pass 1 of a new environment; afterwards `apply.sh` reads each app's current image with `az containerapp show` and passes it back, so an apply never rolls an app back |
| Image deploy | image tag, revision suffix | `github.sha`, and its first 7 characters |
| Production deploy | version to release | the commit the `release` branch points to |
| Deploy steps | names and ids | repo variables written by `set-repo-variables.sh` from the Bicep outputs (`AZURE_CLIENT_ID_STAGING`, `AZURE_CLIENT_ID_PROD`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `ACR_NAME`, the resource groups, app, job and Static Web App names a repo needs) |
| DNS records | names, targets, verification id | `dns-records.sh` from the Bicep outputs |
| Smoke test | URLs to call | the environment's addresses above |
| Budget | thresholds and email | parameters of the subscription level Bicep file ($50, $100, $150, $180; your email) |
| Shutdown copy | when | the runbook step, on or after Dec 6 and before the credit end date you note at signup |

**Web security headers** (`staticwebapp.config.json`, one file for both environments): every route falls back to `index.html`; `Content-Security-Policy: default-src 'self'; connect-src 'self' https://*.welinc.tech; img-src 'self' data: blob: https://*.welinc.tech https://*.blob.core.windows.net; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'`, plus `X-Content-Type-Options: nosniff` and `Referrer-Policy: strict-origin-when-cross-origin`. Using wildcards on our own domain and the blob host lets one file serve both environments. `img-src` needs our own domain because the portal loads profile pictures from welinc-auth's `/uploads/` on `<api>`; VRMS photos come from the blob host and its documents open as plain links, which the policy doesn't govern.

**Key invariants**:
- A migration that ships with a backend must work with the previous revision too (additive first), because a rollback never undoes the database. Between Nov 28 and Dec 5 only additive migrations ship.
- Staging deploys never touch production resources. No staging login has any right on `rg-welinc-prod`, and no group's login has rights outside its own apps (the shared registry aside).
- No seed people ever exist on production.
- welinc-auth is set to 1 replica; the only overlap is the few seconds of a revision change, when sign in limits reset and its sweepers may run twice (they are idempotent updates; task 5 confirms it).
- A service with a timer never scales to zero.
- The sum of pools on a server never exceeds 35.
- Rollback: move `release` back to an older commit and rerun the production workflow. Its image must still exist (the purge keeps the last 15 tags per image). No down migration runs.
- The private secrets files are in the workspace `.gitignore`, and a copy lives somewhere a teammate can reach (the runbook names where).

**Security model**: anyone with write access to a repo can move its `release` branch and run its production workflow; GitHub Free can't require a reviewer on private repos. What the setup enforces is separation: staging logins only from `development`, production logins only from `release`, each group only on its own apps. The registry is shared and its push right covers every image, so a group could overwrite another group's tag; accepted for the defense window instead of a custom registry permission model, and reduced by deploying immutable SHA tags only. Each PostgreSQL firewall admits any Azure service, other customers' included, so every role password is long, random and unique. App roles can't alter tables, and VRMS's can't edit or delete its audit log. Hosted cookies are `Secure`, `HttpOnly`, `SameSite=Lax`, host only, with the `__Secure-` prefix. Compliance scope: staff names, emails and phone numbers; no payments or health data. HTTPS, the firewalled servers, Container Apps secrets, managed identity for blobs and the account activity log (spec 0011) are the controls.

**Configuration required**:
- New in both services: `DB_POOL_MAX` (default 5, read into the `pg.Pool` `max`). In backend-vrms: `SEED_ALLOW` for its new seed guard, and the `--reference` seed flag. In welinc-auth: the `admin:recover --create` mode (suite spec 0013 AC-12b). Document the new names in `.env.example`.
- Everything else in the Value sourcing table is already read by the apps; this spec sets it per environment.

**Critical test scenarios**:
- Happy path: merge a change to backend-vrms `development`, staging updates itself, the revision named after the commit takes 100% of traffic, the smoke test passes, verifies **AC-3**, **AC-6**, **AC-9**.
- Happy path: sign in on `staging-portal.welinc.tech`, land in `staging-vrms.welinc.tech`, reload, still signed in (the refresh cookie works on the domain), verifies **AC-7**.
- Failure case: a migration that errors stops the deploy and the old revision keeps answering, verifies **AC-6**.
- Failure case: a missing required setting fails `env:check` in the migration job before any migration runs, verifies **AC-6**.
- Failure case: a revision that never passes its startup probe fails the deploy at the revision wait, and the smoke test never runs, verifies **AC-6**, **AC-9**.
- Permission: a push to `development` can't log in with a production app registration; the VMMS login can't update `vrms-backend`, verifies **AC-4**, **AC-11**.
- Isolation: the staging `DATABASE_URL` can't open the production server, verifies **AC-5**.
- Cold start: on production after 30 minutes idle, the first VRMS page answers in under 2 seconds, verifies **AC-16**.
- Timer: on staging, with nobody signed in for an hour, a role change in the portal shows on the VRMS Users page within a minute, verifies **AC-16**.
- Mail: a setup code on staging reaches a Gmail inbox, not spam, verifies **AC-17**.
- Address: two networks give two addresses in the activity log, verifies **AC-18**.
- Bootstrap: production has exactly one person after the bootstrap jobs (the suite admin, who sets a password from the mailed code and signs in), and VRMS has garages and vehicles but no tickets, verifies **AC-15**.
- Safety: `NODE_ENV=production npm run seed` in either service without `SEED_ALLOW=staging` exits without touching data, verifies **AC-13**.
- Persistence: upload a profile picture and a ticket file, restart both apps, both still load, verifies **AC-14**.
- Re-apply: run `apply.sh` again on staging; every app keeps its current image and secrets and still answers, verifies **AC-10**.
- Suite: with VMMS not yet deployed, `/vmms/health` answers 502 and `/vrms/health` answers 200, verifies **AC-19**.
- Budget: with every app at its maximum, `SELECT count(*) FROM pg_stat_activity` on each server stays under 35, verifies **AC-21**.
- Recovery: restore the production server to a scratch server and compare row counts, verifies **AC-8**.

## Build plan

Order follows Tracer Bullet: CI first (built), then everything that needs no Azure account, so the 30 day credit starts only when staging is applied; then one thin staging thread through shared services and VRMS, then the other groups on staging, then production before the mock defense.

**Slice 1: CI (built)**
1. [x] `lint:ci` in backend-vrms and auth, satisfies **AC-1**, **AC-2**
2. [x] `.github/workflows/ci.yml` in the five repos, satisfies **AC-1**, **AC-2**, **AC-11**

**Slice 2: make the apps deployable (no Azure; by Nov 18)**
3. [x] Fix `Dockerfile.prod` in auth and backend-vrms: `EXPOSE` and read `PORT` (3001, 3002), copy `prisma.config.ts` into the runner, run as a non root user, run `npm run geo:fetch` in the auth build, and add a `seed` target that is a full source image (`src/`, `scripts/`, `prisma/`, `tsconfig.json`, `prisma.config.ts`) for every job, satisfies **AC-6**, **AC-13**, **AC-15**
4. [x] `/auth/health` and `/vrms/health` (built in suite spec 0008), satisfies **AC-6**, **AC-9**
5. [ ] In both services read `DB_POOL_MAX` into the `pg.Pool` `max`, confirm localhost origins are refused when `NODE_ENV=production`, and confirm auth's session and temporary grant sweeps are safe to run twice at once. In backend-vrms add the seed guard (same message and rule as welinc-auth) and the `--reference` mode (garages, vehicles, knowledge base, settings only), satisfies **AC-5**, **AC-13**, **AC-15**, **AC-16**, **AC-21** (built 2026-11-14 except one change from the cross check: run `--reference` as one transaction)
6. [ ] In welinc-auth add `admin:recover --create` (suite spec 0013 AC-12b) with its tests, satisfies **AC-15** (built 2026-11-14 except one change from the cross check: exit 1 when the setup code can't be sent)
7. [x] Add `staticwebapp.config.json` to web-vrms and web-portal with the fallback and the headers in Design, satisfies **AC-3**, **AC-14**
8. [x] `infra/gateway/` with every system's routes (suite spec 0008), satisfies **AC-3**, **AC-19**

**Slice 3: setup as code, domain and mail (Bicep written by Nov 18; applied Nov 18 to 19)**
9. Write the Bicep in `infra/`: shared (registry with the purge task), and per environment (PostgreSQL server with 14 day backups, its seven databases and server parameters, the files and blob storage accounts with the share, container and blob CORS, Log Analytics with retention and cap, the Container Apps environment with its file share storage from `listKeys()`, every app of every group with ports, probes, the replica rule and secure secret parameters, migration and seed jobs, four Static Web Apps, custom domains behind `bindDomains`), with a domain parameter, satisfies **AC-5** to **AC-8**, **AC-10**, **AC-14**, **AC-16**, **AC-19**, **AC-21**
10. Write the subscription level Bicep for the budget alerts, satisfies **AC-10**, **AC-12**
11. Write `infra/scripts/`: `apply.sh` (register the resource providers `Microsoft.App`, `Microsoft.OperationalInsights`, `Microsoft.ContainerRegistry`, `Microsoft.DBforPostgreSQL`, `Microsoft.Web`, `Microsoft.Storage`; pass the private file as secure parameters; read back current images; the temporary firewall rule; both passes), `rotate-secret.sh`, `set-repo-variables.sh`, `dns-records.sh`, the private file example with fake values, and `infra/db/init.sql` (roles, ownership, default privileges, `vector`), satisfies **AC-5**, **AC-10**, **AC-11**
12. Register `welinc.tech`, create the Brevo account, add the SPF, DKIM and DMARC records, satisfies **AC-7**, **AC-17**
13. Sign up for the free account and note the credit end date. Check prices in the pricing calculator and the regional quotas, pick the region. Run `azure-deployment-preflight` and a what if, apply `shared` and `staging` pass 1, run `init.sql`, make staging's keys (`keys:rotate`, `keys:client`), add the DNS records, apply pass 2, run `set-repo-variables.sh`, create the six app registrations with their federated credentials and the `release` branches in our repos and the workspace, satisfies **AC-5**, **AC-7**, **AC-10**, **AC-11**

**Slice 4: CD to staging, the thin thread (by Nov 22)**
14. `deploy.yml` in auth and backend-vrms (build both images, push, migration job, revision update, revision wait, smoke), satisfies **AC-3**, **AC-4**, **AC-6**, **AC-9**
15. `deploy.yml` in web-vrms and web-portal, satisfies **AC-3**, **AC-4**, **AC-9**
16. The gateway workflow in the workspace repo, satisfies **AC-3**, **AC-4**
17. First staging deploy end to end, the staging seed jobs, then prove it: sign in across the domain, a mailed code arrives, two client addresses, a picture and a ticket file survive a restart, the timer check, a second `apply.sh` changes nothing, the connection count, and the spec 0002 key rotation (its AC-24 and AC-26), satisfies **AC-3**, **AC-7**, **AC-9**, **AC-10**, **AC-13**, **AC-14**, **AC-16** to **AC-18**, **AC-21**

**Slice 5: VMMS and BMS on staging (from Nov 17, as their moves merge; before Dec 3)**
18. Write `docs/integration/hosting.md` and the two workflow templates; create their app registrations and custom roles, add their secrets and client keys to the private file, rerun `seed:clients`, and send them the page. As each group deploys, run suite spec 0014's staging steps (its AC-32), satisfies **AC-3**, **AC-4**, **AC-9**, **AC-11**, **AC-19**, **AC-21**

**Slice 6: production and safety (by Nov 26)**
19. Make production's keys and private file, apply `prod` pass 1, run `init.sql`, add the production DNS records, apply pass 2, deploy every repo once from `release`, run the production bootstrap jobs, set your password from the mailed code, smoke test, satisfies **AC-4**, **AC-5**, **AC-7**, **AC-15**, **AC-16**
20. Restore drill on the production server, satisfies **AC-8**
21. Write `infra/RUNBOOK.md`: bootstrap steps, DNS and Brevo records, the firewall rule for laptop work, rollback, stopping staging, rotating keys and secrets (a secret change needs a revision restart), moving to another subscription (`pg_dump`, restore, blob and share copies, DNS switch), the freeze rule, and the shutdown copy, satisfies **AC-10**, **AC-12**, **AC-20**
22. After Dec 5: take the shutdown copy and record its date, satisfies **AC-20**

## Migration plan

**Strategy**: no live migration. Nothing is hosted today; every hosted database starts empty.
**Phases**:
1. Staging first (Slices 3 and 4), then the other groups onto it (Slice 5), then production (Slice 6).
2. Production is new, so there is no cutover from an old host.
**Rollback**: per deploy, move `release` back and rerun. For the setup itself, the Bicep can be applied again or into another subscription.
**Risks**: DNS records or certificate checks taking hours (add the records the day staging is applied); Brevo domain approval delays (start in task 12); a group's move landing late (their routes answer 502 and nothing else breaks); a trial subscription's low quota in the chosen region (checked in task 13).

## Consequences

**Positive**:
- The whole suite runs on one address, so the integration defense shows three systems behind one login.
- Every merge reaches staging by itself, for every group, and production changes only when someone chooses.
- Production never waits on a cold start, and the timers keep running everywhere.
- Staging and production can't touch each other's data.
- The setup is code and the data can be copied, so a lost subscription is a few hours of work, not a lost system.

**Negative / tradeoffs**:
- The credit is a hard end date, not just an amount. After about Dec 18 to 19 the subscription stops unless someone upgrades it with a card; the system goes offline after the defenses by design.
- Production approval is only a person moving `release` and clicking. GitHub Free can't enforce a second reviewer or required checks.
- You become the operator for three groups: their app registrations, roles, secrets and client keys go through you, and their deploy problems land in your inbox.
- Any group can overwrite another group's image tag in the shared registry.
- Every pool is small (2 or 3); a slow query holds a scarce connection, and a group that ignores the pool setting can starve the others.
- Estimated spend is $75 to $125 for the month the credit lasts, under the $200 (unconfirmed until task 13's pricing check), which leaves little room for mistakes like a noisy log or a forgotten scratch server.
- GitHub's 2,000 free minutes are shared by every group's builds; a busy week of Docker builds can use them up.
- Frontends are rebuilt per environment, so staging and production don't run the same build.
- A cold staging app answers 504 on its first call while it wakes.
- The domain's free year ends; renewal is a paid step if the suite outlives the course.

**Neutral**:
- The local docker compose files stay as they are for development.
- Mobile apps (the VMMS Expo app) point at `https://api.welinc.tech`; building and sharing the app stays with VMMS.
- The default Azure hostnames stay reachable but unused.
- backend-vrms carries a copy of the auth controller the gateway hides; harmless and unreachable.

## Follow-up

- [ ] At signup, write the credit end date into the runbook and into the shutdown step (AC-20).
- [ ] Ask one teammate to keep their Azure for Students account empty and ready as the backup subscription; don't create a second free account for yourself (the offer is one per person).
- [ ] Confirm the GitHub Student Developer Pack still offers a free year of `.tech`; if not, buy the name and note the renewal date.
- [ ] The analytics page: feature 3 moved analytics into backend-vrms, so check before the mock defense that no screen still shows sample numbers.
- [ ] Feature 27 (error monitoring) decides Application Insights or similar; this spec only creates Log Analytics.
- [ ] Revisit the GitHub plan if anyone pushes straight to `development` or moves `release` carelessly.
- [ ] Spec 0019 note: once every deployed web build uses `PUT /repairs/:id/assignments`, remove the old `POST` alias in backend-vrms.
- [ ] Auth's profile pictures could move from the file share to Blob Storage later (a welinc-auth decision); the share works for now.
- [ ] Container Apps path based routing could replace the nginx gateway one day; not before the defenses.
- [ ] Add the Azure skills in Decision to the VRMS `AGENTS.md` skill list if missing (`/sync` owns that).

## Rationale

Reasoning, options and sources: see [rationale.md](rationale.md).
