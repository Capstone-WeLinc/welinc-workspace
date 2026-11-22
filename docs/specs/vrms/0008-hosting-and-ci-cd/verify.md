# Verify: hosting & CI/CD · spec 0008 · rewritten 2026-11-22

_Steps derived from spec 0008's acceptance criteria. `/check verify` runs these; `/test` locks the durable ones. Rewritten for staging only (AC-24): production lines are now checks of the code, never of a live environment. Ticks and dates carried over from the earlier runs (2026-11-14 to 2026-11-20). The retired `welinc-backend-vrms-analytics-ai` is out (feature 3, archived)._

_Run Azure commands with `~/.local/bin/az`. Any `apply.sh staging` here means `apply.sh staging --domains` (without it the gateway loses `staging-api.welinc.app`). No step here runs in the 2 hours before a defense. Staging is the demo: never merge a broken commit into `development` to prove a failure (staging logins trust only `development`, so the commit would stay there for the next deploy); failure paths are proven from pull requests, run history, or the workflow code._

## Major flows (run these first)

Until every row is built, a verify run covers these (your rule from 2026-11-17); the full list follows.

- [ ] **Deploy end to end:** merge a small change into backend-vrms `development` → the `deploy.yml` run shows `ci` green, then the migration job, then `vrms-backend-staging` gets the revision `r<sha7>-<attempt>` holding 100% of traffic, then the smoke test passes → AC-3, AC-6, AC-9, AC-22
- [ ] **Sign in across the domain:** `staging-portal.welinc.app` → sign in as a seed admin (code from the team inbox) → open VRMS → `staging-vrms.welinc.app` loads signed in; reload, still signed in → AC-7, AC-17
- [ ] **Every system behind one gateway:** `https://staging-api.welinc.app/health`, `/auth/health`, `/vrms/health`, `/bms/health` → 200 each; `/vmms/health` → 200 once VMMS is on (502 `UPSTREAM_UNAVAILABLE` until then) → AC-9, AC-19
- [ ] **Production stays code only:** a production "Run workflow" on `main` in backend-vrms with no `sha` → `target` fails with "production is not hosted: no AZURE_CLIENT_ID_PROD", `promote` and `deploy` skipped, `main` unchanged → AC-24
- [ ] **Warm for the defenses:** the day before the first defense, `warmAll` on and applied → every staging app shows min replicas 1 (`az containerapp list -g rg-welinc-staging --query "[].{n:name,min:properties.template.scale.minReplicas}"`) → AC-16

## CI on every pull request (AC-1, AC-2, AC-11)

- [ ] Open a pull request into `development` in web-vrms, web-portal, backend-vrms and auth → a `CI / ci` check (plus `db` in auth and `gitleaks` everywhere) appears and finishes green → AC-1
- [ ] On a throwaway PR in backend-vrms, add an unused variable to a `src` file → `ci` goes red at lint → AC-2
- [ ] On a throwaway PR in auth, break an expected value in a test → `ci` goes red at the test step → AC-2
- [ ] A CI log's setup-node step reports Node 24 (from `.nvmrc`) → AC-1
- [ ] Push a second commit to the same open PR quickly → the older run is cancelled → AC-1
- [ ] `npm run lint:ci` in backend-vrms and auth, then `git status --short` → exit 0, no file changed → AC-1, AC-2
- [ ] Every `ci.yml` and `deploy.yml` has `permissions: contents: read` at the top, and `id-token: write` only on the deploy job → AC-11

## Deploy guard and promotion (AC-3, AC-4, AC-22)

- [ ] Deploy guard, as code plus history (never a red merge): in each `deploy.yml` the first job is `ci: uses: ./.github/workflows/ci.yml` with `ref` set to the target commit, the deploy job has `needs: ci`, and `azure/login` appears only in the deploy job; then `gh run list --workflow deploy.yml --status failure` in backend-vrms or auth → any run whose `ci` failed shows the deploy job skipped → AC-22
- [ ] A change under `infra/gateway/` merged into the workspace `main` → `deploy-gateway.yml` deploys `api-gateway-staging` and the smoke test passes → AC-3
- [ ] A merge into web-vrms `development` → the Static Web App deploys and `staging-vrms.welinc.app` serves the new build → AC-3, AC-9
- [ ] `deploy.yml` in each service repo, read as code: the production path checks `refs/heads/main`, the `promote` job pushes a plain fast forward with the workflow token, a `sha` input must match `^[0-9a-f]{40}$` and be on `main`, and the image check runs before any update → AC-4

## Migrations and revisions (AC-6)

- [ ] Locally, from the backend-vrms `seed` image with one required setting left out: `npm run db:deploy:job` → `env:check` exits 1 before `prisma migrate deploy` runs → AC-6
- [ ] Revision wait, as code plus history: `deploy.yml` polls `latestReadyRevisionName` for the `r<sha7>-<attempt>` revision at 100% traffic with a 6 minute limit and runs the smoke test only after it, and a timeout exits 1 before the smoke step; if any `deploy.yml` run in our repos or a group's ever failed at that wait (`gh run list --workflow deploy.yml --status failure`), its log shows the old revision still at 100% → AC-6, AC-9

## Setup as code (AC-5, AC-8, AC-10, AC-12, AC-21, AC-23)

- [ ] `bicep build` on `infra/env.bicep`, `shared.bicep`, `subscription.bicep` and every `infra/modules/*.bicep` → no errors, no warnings → AC-10
- [ ] `WHATIF_ARGS="--result-format ResourceIdOnly" bash infra/scripts/apply.sh staging --what-if --domains` → no image or secret change and nothing deleted → AC-10
- [x] `apply.sh staging --domains` again → the gateway keeps its certificate throughout, images kept → AC-7, AC-10 (2026-11-20: 204 of 204 health calls 200)
- [x] `azure.extensions` is `VECTOR,PG_TRGM`, `idle_in_transaction_session_timeout` is `60000`, backup retention 14 days on `psql-welinc-staging` → AC-8, AC-21 (2026-11-20)
- [x] Restore drill → AC-8 (2026-11-20: point in time restore refused, `SkuNotAvailable`; the `pg_dump` fallback matched every table, `auth` 737 rows, `vrms` 19,263)
- [x] Budget `welinc-credit` with alerts at 25, 50, 75 and 90 percent of $200 → AC-12 (2026-11-20)
- [x] Connection count under load stays inside the budget → AC-21 (2026-11-20: `auth_app` and `vrms_app` each peaked at 3, 7 client connections in all)
- [ ] Again once VMMS is on, with every app awake (`warmAll`): `SELECT count(*) FROM pg_stat_activity` on `psql-welinc-staging` stays under 35 → AC-21
- [x] Every app and job in `rg-welinc-staging` ends in `-staging`, no bare name; a second `apply.sh staging` changes nothing → AC-23 (2026-11-20)
- [ ] Workspace CI's name check on a branch that adds a 33 character name → red → AC-23
- [x] Runbook covers bootstrap, records, firewall, rollback, stopping staging in one command, the lock, secrets, moving, production later, the freeze and the shutdown copy; credit end date recorded (Dec 18) → AC-10, AC-12, AC-20 (2026-11-20)
- [ ] Alerts: `az monitor metrics alert list -g rg-welinc-staging --query "[].{n:name,on:enabled}" -o table` → `alert-db-storage-staging`, `alert-db-cpu-staging` and one `alert-restarts-<app>` per staging app (VMMS's two included once it is on), all enabled; `az monitor action-group show -g rg-welinc-staging -n ag-welinc-staging` mails the `alertEmail` address → Value sourcing (Azure alerts)
- [ ] On local PostgreSQL 16 with a non superuser admin: `infra/db/init.sql` twice → both exit 0; `<db>_app` gets "permission denied" on `DELETE FROM audit_logs`, `DROP TABLE` and on another database → AC-5

## Staging only (AC-24)

- [ ] First: `az group exists -n rg-welinc-prod` → `false`; `az resource list -g rg-welinc-staging --query "[?contains(name,'prod')]"` → empty; `az lock list -g rg-welinc-staging` → only `keep-cae-welinc-staging` → AC-24
- [ ] Then: `WHATIF_ARGS="--result-format ResourceIdOnly" bash infra/scripts/apply.sh prod --what-if` → runs and lists production's resources with `-prod` names and the `api.`, `portal.`, `vrms.welinc.app` hosts. `apply.sh` creates the empty `rg-welinc-prod` before the what if, so remove it only while it is empty: `[ -z "$(az resource list -g rg-welinc-prod --query '[].id' -o tsv)" ] && az group delete -n rg-welinc-prod --yes`, then `az group exists -n rg-welinc-prod` → `false` again → AC-5, AC-7, AC-23, AC-24
- [x] The production guard in backend-vrms → AC-24 (2026-11-20: `target` failed with the guard message, `main` unchanged)
- [x] `docs/integration/links.md` and `hosting.md` show no production address as live → AC-24

## Domain, mail and addresses (AC-7, AC-17, AC-18)

- [ ] `dns-records.sh staging --check` → every line `ok`; `staging-api.welinc.app` has a valid managed certificate; the four web names open their Static Web Apps → AC-7
- [x] A setup code on staging reaches a real Gmail inbox, not spam, within 2 minutes → AC-17 (2026-11-20)
- [x] Two sign ins from two networks show two public addresses in `account_events` → AC-18 (2026-11-20: home broadband and mobile data)

## Files, seeds and replicas (AC-13, AC-14, AC-16)

- [x] `vrms-backend` reads and signs a blob link (open a ticket photo on staging) with no connection string set → the photo loads → AC-14 (2026-11-20: a 255 KB JPEG opened full size; the app's only storage settings are `STORAGE_ACCOUNT_URL`, `STORAGE_CONTAINER`, `STORAGE_PUBLIC_URL`)
- [x] A ticket photo and a picture on the `auth-uploads` share load before and after restarting `auth-service-staging` and `vrms-backend-staging` → AC-14 (2026-11-20)
- [ ] `NODE_ENV=production npm run seed` in either service without `SEED_ALLOW=staging` (local, throwaway database) → exits 1 and writes nothing → AC-13
- [x] Replica settings outside the defense window: the gateway, `auth-service-staging` and `vrms-backend-staging` min 1, `auth-service-staging` max 1 → AC-16 (2026-11-20)
- [x] Timers on staging keep running with nobody signed in (session sweep hourly, matrix sync within a minute) → AC-16 (2026-11-19 to 20)
- [ ] With `warmAll` on (on in `staging.parameters.json` since 2026-11-20) and after 30 minutes with nobody using staging: the first VRMS page answers in under 2 seconds → AC-16. Run it at least 2 hours before a defense, like every step here

## Error monitoring on staging (spec 0025, Value sourcing)

- [ ] `az containerapp show -n vrms-backend-staging` and `auth-service-staging` → `SENTRY_DSN` set, `SENTRY_ENVIRONMENT=staging`, no `SENTRY_TEST_ROUTES`; `curl -X POST https://staging-api.welinc.app/vrms/debug/sentry-test` with no sign in answers 404 (the route isn't registered at all, so no token is needed to see that) → Value sourcing, task 19a step 3
- [ ] A web deploy's log shows the source map upload, then "Remove source maps", and the smoke test's `.map` URL answers 404 → Value sourcing (spec 0025 AC-17)
- [ ] In Sentry, the newest staging event's release equals the deployed commit SHA → Value sourcing

## VMMS and BMS on staging (AC-3, AC-9, AC-11, AC-19)

- [x] Every staging app other than the gateway: `az containerapp show --query properties.configuration.ingress.external` → `false` → AC-19 (2026-11-20; run again for the two VMMS apps once they exist)
- [x] BMS: `/bms/health` and `staging-bms.welinc.app` answer 200; a merge into a BMS repo's `development` deploys by itself; `check-system.mjs bms` on staging passes all but the fleet check (2026-11-21)
- [ ] VMMS: `/vmms/health`, `/vmms/analytics/health` and `staging-vmms.welinc.app` answer 200; a merge into `welinc-backend-vmms` `development` deploys by itself → AC-3, AC-9, AC-19
- [ ] As the VMMS deploy login: `az containerapp update -n vrms-backend-staging` → AuthorizationFailed; `az containerapp update -n vmms-backend-staging` → succeeds → AC-11
- [ ] `node scripts/check-system.mjs vmms` and `bms` against staging → exit 0 (the BMS fleet check green once VMMS is on) → AC-19, suite spec 0014 AC-32
- [ ] A VMMS fuel receipt scan on staging reads through Document Intelligence with no key set → AC-14 (Value sourcing)

## Shutdown (AC-20)

- [ ] After the final defense and before Dec 18: the runbook's *Shutdown copy* ran, every staging database dumped and every blob container and the file share copied to your machine and one teammate's, and the runbook records the date → AC-20

## Acceptance criteria coverage

- AC-1, AC-2: CI section · AC-3: Major flows, Deploy guard, VMMS and BMS · AC-4: Deploy guard (as code) · AC-5: Setup as code (`init.sql`), Staging only (what if) · AC-6: Major flows, Migrations · AC-7: Major flows, Domain · AC-8: Setup as code · AC-9: Major flows · AC-10: Setup as code · AC-11: CI, VMMS and BMS · AC-12: Setup as code · AC-13: Files and seeds · AC-14: Files, VMMS · AC-15: production only, covered by the seed and recovery tests in the two repos (code) · AC-16: Major flows, Files and replicas · AC-17, AC-18: Domain · AC-19: Major flows, VMMS and BMS · AC-20: Shutdown · AC-21: Setup as code · AC-22: Major flows, Deploy guard · AC-23: Setup as code, Staging only · AC-24: Major flows, Staging only
