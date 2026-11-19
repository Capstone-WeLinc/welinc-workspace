# Verify: hosting & CI/CD · spec 0008 · updated 2026-11-14
_Steps derived from spec 0008 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones. The CI milestone, Slice 2 (make the apps deployable) and Slice 3 (setup as code) are written so far; `/develop` adds the steps for each later milestone when it lands._

## UI / manual
- [ ] Open a pull request into `development` in each of web-vrms, web-portal, backend-vrms, auth and analytics-ai → a check named `CI / ci` appears on the PR and finishes green → AC-1
- [ ] On a throwaway PR in backend-vrms, add an unused variable to any `src` file → the `CI / ci` check goes red at the lint step and the PR shows a failed check → AC-2
- [ ] On a throwaway PR in auth, make an existing test fail (for example change an expected value in `app.controller.spec.ts`) → the check goes red at the test step → AC-2
- [ ] In a CI run log for a Node repo, open the setup-node step → it reports Node 24 (from `.nvmrc`) → AC-1
- [ ] Push a second commit to the same open PR quickly → the older run is cancelled and only the newest run finishes → AC-1
- [ ] Merge a PR into `development` → a run starts for the push on `development` and finishes green → AC-1

## Commands
- [ ] `npm run lint:ci` in `welinc-backend-vrms` and `welinc-auth`, then `git status --short` → lint exits 0 and no file changed (it must not fix files) → AC-1, AC-2
- [ ] In a clean clone of each Node repo on Node 24: the commands in its `ci.yml` run in order and all exit 0 → AC-1, AC-2
- [ ] `python -m py_compile $(git ls-files '*.py')` in `welinc-backend-vrms-analytics-ai` → exits 0 → AC-1
- [ ] Open each `.github/workflows/ci.yml` → it contains `permissions:` with only `contents: read` and no secrets are referenced → AC-11

## Commands: Slice 2, make the apps deployable (added 2026-11-14)
- [ ] In welinc-auth and welinc-backend-vrms: `docker build -f Dockerfile.prod .` and `docker build -f Dockerfile.prod --target seed .` → both build; the runner's `CMD` is `node dist/src/main`, it runs as `node` and `PORT` is 3001 or 3002 → AC-6
- [ ] Start either runner with `NODE_ENV` left at `production` and local `http://localhost` origins → it stops at boot with "Environment check failed" listing the https, cookie, proxy hop and SMTP rules → AC-5
- [ ] Start the auth runner in development mode on `welinc-network` with a throwaway key → `/auth/health` answers `{"status":"ok","checks":{"database":"ok"}}`, `geo/` holds both DB-IP files, `uploads/` is owned by `node` → AC-6, AC-14
- [ ] Upload a profile picture locally, then open `/uploads/profiles/<file>` through the gateway → the image loads (the static route reads the same `uploads/` the upload writes) → AC-14
- [ ] On a throwaway VRMS database, from the seed image: `npx prisma migrate deploy`, then `npm run seed` with no `SEED_ALLOW` → exits 1 with "Seeding is off in production…" and writes nothing → AC-13
- [ ] Same database: `npm run seed -- --reference` → exits 0; garages 3, vehicles 70, knowledge entries 23 all by `setup@welinc.app` ("WeLinc setup"), and 0 tickets, mechanics, drivers and suggestions → AC-15
- [ ] Run `npm run seed -- --reference` again → exits 1 with "--reference fills an empty database only…", nothing written → AC-15
- [ ] Same database with `SEED_ALLOW=staging`: `npm run seed` → "Database seeded successfully!" → AC-13
- [ ] `DB_POOL_MAX=3` set on either service → `SELECT count(*) FROM pg_stat_activity WHERE usename = '<role>'` never passes 3 under load; leaving it blank uses 5; `0` or `51` fails the boot check → AC-21
- [ ] `npm run admin:recover -- --create --email <x> --name "<n>" --reason "<10+ chars>"` on a database that has a suite admin → "Refused, nothing was written: a suite admin exists already…", exit 1 → AC-15
- [ ] `docker exec welinc_auth_service npm run test:db` → `admin-recover-create.db-spec.ts` passes (first suite admin with no roles, no password, `ADMIN_RECOVERY` and `SUITE_ADMIN_ACTIONED`, the setup code sent; refusals for a short reason, a bad domain, an existing admin and an existing email) → AC-15
- [ ] `npm run build:local` in web-vrms and web-portal → `dist/staticwebapp.config.json` exists with the fallback to `/index.html` and the CSP, `nosniff` and referrer headers; `dist/index.html` has no inline `<script>` → AC-3, AC-14

- [ ] Two cross check fixes: `npm run seed -- --reference` on a fresh migrated VRMS database where `seedVehicles` throws (rename the `vehicle_type` lookup values) → exits 1 and garages, vehicles and knowledge entries all count 0; fix the names, rerun → 3, 70, 23 → AC-15
- [ ] `admin:recover --create` when the setup code can't be sent (SMTP pointed at a closed port) → prints "could not be sent", exits 1, and the account plus its suite admin row exist; a second `--create` refuses → AC-15

## Commands: Slice 3, setup as code (added 2026-11-14)
- [ ] `bicep build` on `infra/env.bicep`, `shared.bicep`, `subscription.bicep` and every `infra/modules/*.bicep` → no errors, no warnings → AC-10
- [ ] On local PostgreSQL 16, as an admin with only `CREATEROLE` and `CREATEDB`: create a database, run `infra/db/init.sql` twice → both runs exit 0 and the database's owner is `<db>_owner` → AC-5
- [ ] Same database: migrations as `<db>_owner`, then the `audit_logs` revoke → every table is owned by `<db>_owner`; `<db>_app` can insert and select but gets "permission denied" on `DELETE FROM audit_logs`, `DROP TABLE` and `CREATE TABLE` → AC-5
- [ ] Two databases set up by `init.sql` → one database's app role can't connect to the other ("permission denied for database") → AC-5
- [ ] welinc-auth: `npm run db:deploy` as `auth_owner` and `npm run seed` as `auth_app` on a database set up by `init.sql` → both succeed → AC-6, AC-13
- [ ] After signup: `infra/scripts/apply.sh shared`, `apply.sh budget`, then `apply.sh staging --what-if` → the preview lists the server, seven databases, two storage accounts, the environment, three apps, four jobs and four Static Web Apps, and no VMMS or BMS app → AC-10, AC-19
- [ ] `apply.sh staging` → finishes, `db-init.sh` reports "database roles ready", and the temporary firewall rule is gone afterwards (`az postgres flexible-server firewall-rule list`) → AC-5, AC-10
- [ ] `az postgres flexible-server parameter show --name azure.extensions` and `idle_in_transaction_session_timeout` on each server → `VECTOR,PG_TRGM` and `60000`; backup retention 14 days → AC-8, AC-21
- [ ] `dns-records.sh staging`, add the records, `dns-records.sh staging --check` → every line `ok`; then `apply.sh staging --domains` → `https://staging-api.welinc.app/health` answers 200 with a valid certificate, and the four web names open their Static Web Apps → AC-7
- [ ] `apply.sh staging --domains` again → the gateway keeps its certificate the whole time (curl the health route in a loop during the run), and `--what-if` before it shows no changes to images or secrets → AC-7, AC-10
- [ ] Any app on staging other than the gateway: `az containerapp show --query properties.configuration.ingress.external` → `false`; the gateway's `GET /vmms/health` → 502 `UPSTREAM_UNAVAILABLE` while VMMS is off → AC-19
- [ ] Replica settings: production every app min 1; staging the gateway, `auth-service` and `vrms-backend` min 1, the rest 0; `auth-service` max 1 → AC-16
- [ ] Budget: Cost Management shows `welinc-credit` with alerts at 25, 50, 75 and 90 percent of $200 → AC-12
- [ ] With a VMMS login filled in `env/logins.json` and `vmms` enabled: as that login, `az containerapp update -n vrms-backend` → AuthorizationFailed; `az containerapp update -n vmms-backend` → succeeds → AC-11
- [ ] `vrms-backend` reads and signs a blob link (open a ticket photo on staging) with no connection string set → the photo loads → AC-14

## Acceptance-criteria coverage
- AC-1 … covered by steps 1, 4, 5, 6 and the first, second and third commands · AC-2 … covered by steps 2, 3 and the first two commands · AC-11 … covered by the last command (the OpenID login part comes with the Azure milestones)
- Slice 2 … AC-5, AC-6, AC-13, AC-14, AC-15, AC-21 partly covered by the Slice 2 commands (their hosted halves come with the Azure milestones)
- Slice 3 … AC-5, AC-7, AC-8, AC-10, AC-11, AC-12, AC-16, AC-19 covered by the Slice 3 commands (most need the subscription; the init.sql and compile steps run now)
- AC-3, AC-4, AC-9, AC-17, AC-18, AC-20 … not written yet, they belong to later milestones

## Commands: staging only, AC-24 (added 2026-11-20)
- [ ] `az group exists -n rg-welinc-prod` → `false`; `az resource list -g rg-welinc-staging --query "[?contains(name,'prod')]"` → empty; `az lock list -g rg-welinc-staging` → only `keep-cae-welinc-staging`; `az role definition list --custom-role-only true` → no `WeLinc environment joiner` → AC-24
- [ ] Run this check before the first line above, then that line again: `WHATIF_ARGS="--result-format ResourceIdOnly" bash infra/scripts/apply.sh prod --what-if` → runs and lists production's resources with `-prod` names and the `api.`, `portal.`, `vrms.welinc.app` hosts; it recreates the empty `rg-welinc-prod`, so `az group delete -n rg-welinc-prod --yes` right after → AC-5, AC-7, AC-23, AC-24
- [ ] Only after task 19a step 1 is merged: a production "Run workflow" on `main` in backend-vrms with no `sha` → the `target` job fails with "production is not hosted: no AZURE_CLIENT_ID_PROD"; `promote` and `deploy` are skipped; `git ls-remote origin main` shows the same commit as before; no Azure change. Before that merge, never press it without `sha` (the promote job would move `main`) → AC-24
- [ ] From Nov 27: every staging app shows min replicas 1 (`az containerapp list -g rg-welinc-staging --query "[].{n:name,min:properties.template.scale.minReplicas}"`) → AC-16
- [ ] `docs/integration/links.md` and `hosting.md` show no production address as live → AC-24

## Commands: shared environment, task 18a (added 2026-11-19)
On hold since 2026-11-20 (AC-24): every line below that names production (`-prod`, `rg-welinc-prod`, `api.welinc.app`, the production login, the production locks) runs only if production is hosted again. The staging lines (`apply.sh staging --what-if`, after steps 5 and 6) still apply if you run task 18a steps 4 to 6.
- [ ] `apply.sh prod --what-if` → no `Microsoft.App/managedEnvironments` and no Log Analytics workspace to create; every app and job to create ends in `-prod`; the storage `auth-uploads-prod` and certificate `cert-api-prod` go to `cae-welinc-staging` → AC-23
- [ ] `apply.sh staging --what-if` (task 18a step 4, before applying) → only creates: the `-staging` apps, jobs and `auth-uploads-staging`; nothing deleted; the workspace cap changes → AC-23
- [ ] After task 18a step 6 (staging rebuilt): `az containerapp list -g rg-welinc-staging --query [].name` and `az containerapp job list -g rg-welinc-staging --query [].name` → every name ends in `-staging`, no bare name left; a second `apply.sh staging` changes nothing → AC-23
- [ ] After step 5: `https://staging-api.welinc.app/health` → 200, and a picture uploaded before the rebuild still loads (same file share) → AC-14, AC-23
- [ ] After production's pass 1: `az containerapp show -g rg-welinc-prod -n api-gateway-prod --query "properties.template.containers[0].env[?ends_with(name,'_UPSTREAM')].value"` → every value names a `-prod` app → AC-23
- [ ] Merge a change to backend-vrms `development` → staging's `vrms-backend-staging` gets a new revision, `vrms-backend-prod`'s `latestReadyRevisionName` is unchanged → AC-23
- [ ] Signed in as the production deploy login: `az containerapp env update -g rg-welinc-staging -n cae-welinc-staging --tags x=y` → AuthorizationFailed → AC-11, AC-23
- [ ] Sign in on `staging-portal.welinc.app`, copy the access token, call `https://api.welinc.app/vrms/me` (or any guarded route) with it → 401 → AC-5
- [ ] Signed in as the production deploy login before the first production deploy: `az containerapp update -g rg-welinc-prod -n auth-service-prod --set-env-vars PROBE=1` then remove it → both succeed → AC-11, AC-23
- [ ] `az lock list -g rg-welinc-staging` → `CanNotDelete` on `cae-welinc-staging`, `cert-api-prod`, `auth-uploads-prod` → AC-23
- [ ] Workspace CI's name check on a branch that adds a 33 character name → red → AC-23
