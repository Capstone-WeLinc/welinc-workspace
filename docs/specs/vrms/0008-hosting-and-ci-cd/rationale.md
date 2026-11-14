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
