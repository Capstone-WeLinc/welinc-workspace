# 0008 rationale: Host the WeLinc suite on Azure with GitHub Actions for CI and CD

Build spec: [index.md](index.md)

## Context

> ⚠️ Premise note (2026-11-14): the first version said the credit clock "starts when resources are created". For the $200 free account the 30 days run from signup, so the signup itself is now a planned step, timed to when staging is applied. It also hosted only VRMS; contract 0001 and suite spec 0014 now need all three systems behind one gateway on one domain before the integration defense, so this is no longer a VRMS only decision.

WeLinc is three systems (VRMS, VMMS, BMS) on shared services (auth, portal, gateway). Everything runs from docker compose on laptops today. CI is built in every VRMS and shared repo; nothing is hosted.

The dates are fixed: mock defense Nov 28, integration defense Dec 4, final defense Dec 5, 2026. VMMS and BMS finish their move onto the shared services by Nov 16 (suite spec 0014), and its staging gate (AC-32) needs all three systems hosted together.

The money is an Azure free account: $200 that must be spent within 30 days of signup, plus some services free for 12 months (750 hours a month of one small PostgreSQL server). Nobody has signed up yet. The GitHub organization is on the Free plan with private repos, so it can't enforce branch protection, required checks or deploy reviewers.

The suite specs since Oct 25 changed what hosting must provide. Login rests on HttpOnly cookies that must be first party, so every web app and the gateway need one registered domain (contract 0001). Tokens are ES256 with published keys, and each backend has its own client key (suite spec 0002). New accounts and every admin sign in wait on an emailed code (suite specs 0009 and 0013), so real mail is required. Several services run work on timers: VRMS polls the user directory every 30 seconds, auth sweeps sessions and temporary grants. Auth counts sign in limits in its own memory. The full suite is about 15 container apps (the gateway, auth, VRMS, two for VMMS, six for BMS, plus jobs) and 4 web apps per environment, and 7 PostgreSQL databases per environment (auth, vrms, vmms, and four for BMS's services).

## Options considered

The platform choice (below, Options 1 to 4, from 2026-10-25) still stands. The 2026-11-14 update added four decisions on top of it.

### Option 1: Static Web Apps, Container Apps and PostgreSQL Flexible Server (chosen, kept)

The web apps on Static Web Apps, every service and the gateway on Container Apps, managed PostgreSQL, images in Azure Container Registry, Bicep for the setup, GitHub Actions for CI and CD.

**Pros**:
- Web apps are free and include HTTPS, a CDN and custom domains.
- Container Apps runs the existing images and can scale to zero.
- Managed PostgreSQL gives backups and restore.
- Bicep makes the setup recreatable in another subscription.

**Cons**:
- Many Azure parts to learn (registry, jobs, identity, Bicep).
- Always on replicas and a second database server cost real credit.

### Option 2: One Azure VM running docker compose

**Pros**:
- Closest to how the team runs things now; the lowest single price.

**Cons**:
- The team owns the operating system, certificates, restarts and backups; no isolation between environments; a single point of failure for three groups.

### Option 3: App Service for Containers with PostgreSQL Flexible Server

**Pros**:
- A simple, well known model with deployment slots.

**Cons**:
- Paid plans are always on; eleven services need several plans.

### Option 4: Vercel for frontends and Render for services

**Pros**:
- Simple dashboards and fast first deploys.

**Cons**:
- Splits the suite over several vendors while the team already has Azure; custom domain cookies across vendors add work.

### Decision A: where VMMS and BMS run

- **Same subscription, behind the one gateway (chosen).** Pros: matches contract 0001 (only the gateway is public), one domain, one setup. Cons: all cost on one credit; you operate for three groups.
- **Each group in its own subscription, proxied by the gateway.** Pros: spreads the cost. Cons: their services need public addresses, breaking the contract's network rule; three setups to keep in step.
- **Host only the shared services and VRMS.** Pros: least work. Cons: suite spec 0014 AC-32 and the integration defense can't pass.

### Decision B: how VMMS and BMS deploy

- **A template they copy, with their own scoped Azure login (chosen).** Pros: they ship their own code as you do; a broken build of theirs stays theirs. Cons: six app registrations instead of two; their secrets still pass through you.
- **You deploy them from the workspace.** Pros: nothing for them to learn. Cons: you become their release button.
- **They push images, you roll out.** Pros: middle ground. Cons: two moving parts and still your button.

### Decision C: replicas

- **Production fully warm, staging warm only where a timer runs (chosen).** Pros: no cold start during the defenses; timers never stop. Cons: about $40 to $70 a month for production containers.
- **Both environments fully warm.** Pros: no cold start anywhere. Cons: roughly doubles staging's cost for no defense benefit.
- **Production front path warm only.** Pros: cheaper. Cons: analytics and BMS inner services stall 10 to 30 seconds on a first call in a demo.

### Decision D: database servers

- **One server per environment (chosen).** Pros: ~50 connections each; staging physically can't reach production; production on the free hours. Cons: staging's server costs about $13 to $16 a month from the credit.
- **One shared server.** Pros: cheapest. Cons: 14 databases share ~50 connections; one failure takes both environments down.
- **One bigger shared server.** Pros: no connection worry. Cons: about a quarter of the credit, still shared.

## Rationale

Option 1 still fits: it runs the images every group already has, the web apps cost nothing, and managed PostgreSQL gives backups a student team shouldn't build in the last weeks.

The update is driven by the dates and the credit. A 30 day credit that starts at signup rewards doing everything that needs no Azure account first (Docker fixes, Bicep, workflows, domain, mail) and signing up only when staging is ready, which puts the credit's end about two weeks after the final defense. The engineer chose to let the subscription stop afterwards and keep a copy, so the plan ends with a shutdown copy instead of a monthly bill.

Contract 0001 settles the domain and network shape, so Decision A follows from it: VMMS and BMS inside the same environment, behind the gateway. Decision B keeps each group the owner of its own releases, which matters more than convenience when three groups deploy in the same two weeks. Decision C follows from two facts in Context: a cold start is 10 to 30 seconds and stacks across hops, and timers stop at zero replicas, which breaks the directory feed and the sweeps regardless of speed. Spending credit on production warmth is the right use of money that expires anyway. Auth is capped at one replica because its sign in limits count in memory; two replicas would double every limit. Decision D gives each environment its own connection budget and makes "staging can't touch production" a property of the network instead of a password rule.

Calls made here without a separate question: Brevo was chosen by the engineer; the budget thresholds ($50, $100, $150, $180) track a $200 credit; pools of 3 for auth and VRMS and 2 for every VMMS and BMS service keep each ~35 usable connection server under budget; storage uses the backend's managed identity because the code already supports it and it removes a secret; production gets reference data only, because the engineer chose no test people and VRMS can't work without garages and vehicles; drivers are left out of the reference seed because they are people and come with feature 44. The spec 0013 permission history export is dropped for hosting, because every hosted database starts empty.

A second independent review on another model (2026-11-14) found 25 issues, all fixed in the spec at the engineer's choice. The load bearing ones: `admin:recover` could not create the first admin on an empty database (suite spec 0013 gained AC-12b); a Bicep apply replaces a Container App's secrets, so secrets now travel as secure parameters; a deploy could "pass" on the old revision, so each revision is named after its commit and waited on; certificates need DNS first, so the apply runs in two passes; Azure Files needs an account key, so files get their own storage account; the job images lacked the source `ts-node` needs; the connection budget ignored BMS's six services; the `audit_logs` revoke can only run after migrations; and the shared registry can't stop one group overwriting another's tag (accepted and documented).

Three amendments after the Slice 2 build (2026-11-14). The picture policy first left out our own domain, which would have blocked every portal profile picture, so `img-src` now includes `https://*.welinc.tech`. The VRMS seed credited knowledge entries to seed people, and production must hold none: the engineer chose a fixed setup actor over crediting the bootstrap admin (it would claim they wrote entries they didn't, and a suite admin holds no VRMS role) and over keeping the seed editors (fake names on production). The usual way to mark imported records is a system actor, and its made up edit history and mechanic suggestions are left out for the same reason. Because the normal seed empties the database first, `--reference` fills an empty database only, so a second run can never wipe real tickets. Last, `admin:recover --create` sends no admin alert: the only suite admin to alert is the person just created, who already gets the setup code, and no one holds an admin role yet. A cross check on another model then closed eight gaps: the 0013 alert table now names the `--create` exception; `--reference` runs as one transaction, because a crash between its steps would otherwise leave rows that make every rerun refuse; `--create` exits 1 when the setup mail fails, so a failed job is visible; and five wording points (any row counts for the empty check, the setup actor has no role and is never a mailbox, `--reference` runs in any environment, the name is trimmed first). The picture wildcard stays: naming only the two API hosts is tighter, but one file serves both environments.

The 2026-10-25 independent review (13 unsourced values, uploads lost on restart, connection limits, localhost origins, cold start smoke tests, the Host header on internal ingress) remains folded in.

### Corrections from the Slice 3 build (2026-11-14)

Building the Bicep and testing `init.sql` on local PostgreSQL 16 (an admin with only `CREATEROLE` and `CREATEDB`, like Azure's) found four things the spec had wrong or left out. None changes the decision; each is the only way the decided design works.

- **`PG_TRGM` in `azure.extensions`.** Azure only lets a database create the extensions this server parameter lists. The spec named `VECTOR` alone, but the VRMS baseline migration runs `CREATE EXTENSION IF NOT EXISTS pg_trgm`, so the first VRMS deploy would have failed. welinc-auth creates no extension.
- **The VRMS seed job as `vrms_owner`.** The full seed's reset runs `ALTER TABLE audit_logs DISABLE TRIGGER USER` (spec 0021), which PostgreSQL allows only the table owner, and the app role loses `DELETE` on that table after the migration job's revoke. Keeping the app role would mean a seed that can never run. The other option, a separate reset path for hosted staging, adds code to protect a database that only holds test data; the owner role is the smaller change.
- **`DATABASE_URL` built by Bicep.** Each role password is needed twice: by `init.sql` to set it, and by the apps to connect. Storing full URLs too would put each password in two places that can drift. Bicep builds the URL from the one stored password, in the form under Connection strings.
- **`init.sql` details.** Proven on PostgreSQL 16: without `GRANT <db>_owner TO CURRENT_USER`, a non superuser admin can't run `ALTER DATABASE … OWNER TO` or `ALTER DEFAULT PRIVILEGES FOR ROLE`. Without revoking `CONNECT` from `PUBLIC`, any role on the server can open any of the seven databases; with it, one database's app role gets "permission denied" on another. Granting through default privileges only (never `ON ALL TABLES`) keeps a rerun from giving `vrms_app` back `DELETE` on `audit_logs`. The test also ran welinc-auth's `db:deploy` as `auth_owner` and its seed as `auth_app`: both work, triggers included, and its directory feed migration's own `ALTER ROLE CURRENT_USER SET idle_in_transaction_session_timeout` works for a non superuser owner (`init.sql` sets no timeout; the server parameter covers every role).

## VMMS and BMS readiness (read only check, 2026-11-14)

Read from their clones after a fetch: VMMS backend `origin/development` 44aaae5, VMMS analytics `origin/development` aa4602a3, VMMS web `origin/development` 39b8a9e, BMS backend `origin/latest-bms-backend` 367ff76, BMS web `origin/latest-bms-frontend` d2ba433, BMS analytics `origin/main` 586f2f5. Neither group can deploy to the hosted setup yet. These are the gaps their S11 moves must close; they are the groups' to fix in their own repos.

| Group | Gap | Where |
|---|---|---|
| Both | No service listens on its contract 0001 port (3010, 3011, 3020 to 3025); the code defaults are 3000 to 3005 | each service's `main.ts` or `server.mjs` |
| Both | Only the VMMS core has a production Dockerfile; VMMS analytics has only `Dockerfile.dev` (`start:dev`), BMS services and BMS analytics have none | repo roots |
| VMMS | The core has no health route (`GET /` answers a string); contract 0001 needs `GET /vmms/health` | `welinc-backend-vmms/src/` |
| VMMS | `Dockerfile.prod` runs `node dist/main`, but the build writes `dist/src/main` (likely, from the tsconfig) | `welinc-backend-vmms/Dockerfile.prod` |
| VMMS | Still reads `JWT_SECRET` (required); the suite has none since suite spec 0002 | `welinc-backend-vmms/src/` |
| VMMS | Uploads go to local disk (`uploads/`, `private-uploads/`), lost on every new revision; needs blob storage or a mounted share | `welinc-backend-vmms` |
| VMMS | Analytics keeps a DuckDB file on local disk and creates triggers on the VMMS database at boot; it needs a mounted share for the file (the triggers, next row) | `welinc-backend-vmms-analytics-ai/src/analytics/` |
| VMMS | Analytics must not create its triggers and functions at boot: they move into a VMMS migration (run as `vmms_owner` by the migration job), so analytics runs as `vmms_app` like every app | `installPostgresTriggers` in `welinc-backend-vmms-analytics-ai/src/analytics/` |
| VMMS | Analytics `GET /analytics/health` doesn't match the route `/vmms/analytics/health` and checks no database | `analytics.controller.ts` |
| VMMS | Web `Dockerfile.prod` copies an `nginx.conf` that isn't in the repo; on Static Web Apps only `npm run build` and `dist/` matter | `welinc-web-vmms` |
| BMS | `bms-gateway` binds `127.0.0.1`, so no other container can reach it | `bms-gateway/server.mjs:161` |
| BMS | `bms-gateway`, booking and BMS analytics read the auth database directly (`AUTH_DATABASE_URL`); no system reads another's database, so this must move to the directory API (contract 0001 section 9) | `auth-integration.mjs`, booking |
| BMS | Dispatch reads vehicles, drivers and garages from the old shared `welinc_db` (`BMS_PARTNER_DATABASE_URL`) | `bms-dispatch-service/src/fleet/local-fleet.provider.ts` |
| BMS | The analytics projection refuses any database host but localhost | `bms-analytics-projection/worker.mjs:3` |
| BMS | Services still read `JWT_SECRET`; BMS analytics needs it to equal the main backend's | booking, dispatch, completion, analytics |
| BMS | BMS analytics needs MySQL (`MYSQL_*`), which the hosted setup doesn't provide (it answers 503 without it) | `welinc-backend-bms-analytics-ai` |
| Both | List every PostgreSQL extension your migrations create (`pgcrypto`, `uuid-ossp` and so on), so it is allowed in `azure.extensions` and created by `init.sql` before your first deploy | each `prisma/migrations/` |
| BMS | Inner services expose `/health/live` and `/health/ready`, the gateway `/health/live`; contract 0001 needs `GET /bms/health` on `bms-gateway` | each service |

What the hosted setup already allows for: `bms-projection` is defined with no ingress (it is a worker), every inner BMS service is internal and reached only by `bms-gateway`, and a group's health path or extra settings can be changed in `groupApps` without touching the Bicep.

## References

**Project sources** (verifiable, in this repo):
- Contract 0001 (`docs/specs/_root/0001-shared-services-contract/`): addresses, port map, routes, cookies, the domain requirement.
- Suite specs 0002, 0003, 0005, 0006, 0008, 0009, 0010, 0011, 0013, 0014: keys, sessions, directory feed, seed guard, gateway settings, email codes, startup checks, activity, suite admin and recovery, the move and AC-32.
- VRMS specs 0013 (pgvector), 0017 (Blob Storage), 0019 (assignment route), 0021 (append only audit log).
- `infra/gateway/`, `docker-compose.*.yml`, `Dockerfile.prod` in auth and backend-vrms, `docs/integration/move-vmms.md` and `move-bms.md`: the services and databases that exist.
- `docs/scope/vrms/platform.md`, feature 26, and its replan notes.

**Practices & standards**:
- Build once, deploy the same image to many environments; rebuild only where configuration is baked in (the SPAs).
- Additive database migrations so a rollback stays safe; a change freeze around a release window.
- Least privilege for CI and for each team's deploy identity.
- OpenID Connect federated credentials for GitHub Actions to Azure login.
- SPF, DKIM and DMARC for transactional mail.

**Links** (web verified on 2026-10-25):
- Azure for Students: https://azure.microsoft.com/en-us/free/students
- Azure free account: https://azure.microsoft.com/en-us/free
- Azure Static Web Apps quotas: https://learn.microsoft.com/en-us/azure/static-web-apps/quotas
- Azure Container Apps billing: https://learn.microsoft.com/en-us/azure/container-apps/billing
- Container Apps with GitHub Actions: https://learn.microsoft.com/en-us/azure/container-apps/github-actions
- PostgreSQL Flexible Server backup and restore: https://learn.microsoft.com/en-us/azure/postgresql/backup-restore/concepts-backup-restore
- Azure Container Registry tiers: https://learn.microsoft.com/en-us/azure/container-registry/container-registry-skus
- GitHub Actions billing: https://docs.github.com/en/billing/concepts/product-billing/github-actions
- GitHub environments: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments

No new links were fetched on 2026-11-14. Every cost figure is an estimate until the pricing calculator check in build task 12; Brevo's free plan limits and the `.tech` offer are from memory and need a check.
