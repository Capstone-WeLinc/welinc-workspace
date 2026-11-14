# Verify: hosting & CI/CD · spec 0008 · updated 2026-11-14
_Steps derived from spec 0008 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones. The CI milestone and Slice 2 (make the apps deployable) are written so far; `/develop` adds the steps for each later milestone when it lands._

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
- [ ] Same database: `npm run seed -- --reference` → exits 0; garages 3, vehicles 70, knowledge entries 23 all by `setup@welinc.tech` ("WeLinc setup"), and 0 tickets, mechanics, drivers and suggestions → AC-15
- [ ] Run `npm run seed -- --reference` again → exits 1 with "--reference fills an empty database only…", nothing written → AC-15
- [ ] Same database with `SEED_ALLOW=staging`: `npm run seed` → "Database seeded successfully!" → AC-13
- [ ] `DB_POOL_MAX=3` set on either service → `SELECT count(*) FROM pg_stat_activity WHERE usename = '<role>'` never passes 3 under load; leaving it blank uses 5; `0` or `51` fails the boot check → AC-21
- [ ] `npm run admin:recover -- --create --email <x> --name "<n>" --reason "<10+ chars>"` on a database that has a suite admin → "Refused, nothing was written: a suite admin exists already…", exit 1 → AC-15
- [ ] `docker exec welinc_auth_service npm run test:db` → `admin-recover-create.db-spec.ts` passes (first suite admin with no roles, no password, `ADMIN_RECOVERY` and `SUITE_ADMIN_ACTIONED`, the setup code sent; refusals for a short reason, a bad domain, an existing admin and an existing email) → AC-15
- [ ] `npm run build:local` in web-vrms and web-portal → `dist/staticwebapp.config.json` exists with the fallback to `/index.html` and the CSP, `nosniff` and referrer headers; `dist/index.html` has no inline `<script>` → AC-3, AC-14

## Acceptance-criteria coverage
- AC-1 … covered by steps 1, 4, 5, 6 and the first, second and third commands · AC-2 … covered by steps 2, 3 and the first two commands · AC-11 … covered by the last command (the OpenID login part comes with the Azure milestones)
- Slice 2 … AC-5, AC-6, AC-13, AC-14, AC-15, AC-21 partly covered by the Slice 2 commands (their hosted halves come with the Azure milestones)
- AC-3, AC-4, AC-7 to AC-10, AC-12, AC-16 to AC-20 … not written yet, they belong to later milestones
