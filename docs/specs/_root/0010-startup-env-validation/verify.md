# Verify: environment checked at startup · spec 0010 · updated 2026-11-11
_Steps derived from spec 0010 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Branches: `feat/startup-env-validation` in welinc-auth, welinc-backend-vrms, welinc-web-vrms and welinc-web-portal; the workspace part is on `docs/startup-env-validation-spec`. Never print a `.env` value while checking: use `docker exec -e NAME=...` overrides, not edits to a real `.env`.

## Commands

### Backends (run each in welinc-auth and welinc-backend-vrms)
- [x] `npm run lint:ci`, `npm run build`, `npx jest src/config` → all pass → AC-1 to AC-6, AC-10
- [x] `npx jest` with no `.env` present (CI, or a fresh clone) → every suite that builds Nest modules passes through the `testEnv` fixture → AC-9
- [x] Add `const x = process.env.FOO;` to any file under `src/` (not `src/config/`, not a spec), run `npm run lint:ci` → `no-restricted-properties` error naming `ConfigService<Env, true>`; then remove it → AC-11
- [x] `docker exec -e AUTH_ISSUER= -e PORT=99999 welinc_auth_service npm run env:check` → exit 1, lists `PORT: must be a whole number from 1 to 65535` and `AUTH_ISSUER: is required`, no values → AC-1, AC-2
- [x] Same in backend-vrms: `docker exec -e AUTH_ISSUER= -e CORS_ORIGINS=https://a.test/ welinc_vrms_backend npm run env:check` → both names listed, no values → AC-1, AC-2
- [x] `docker exec -e NODE_ENV=production welinc_auth_service npm run env:check` → lists `SSO_COOKIE_SECURE: must be true in production`, `PORTAL_URL: must use https in production`, `CORS_ORIGINS: each entry must use https in production` (plus `TRUST_PROXY_HOPS` if it is 0 locally); SMTP lines only if SMTP is unset → AC-3, AC-4
- [x] `docker exec -e NODE_ENV=production welinc_vrms_backend npm run env:check` → lists `SESSION_COOKIE_SECURE`, the http and localhost URLs, and storage if unset; `AUTH_INTERNAL_URL` and `STORAGE_PUBLIC_URL` are not listed → AC-3, AC-4
- [x] `docker exec -e WEB_SESSION_IDLE_MINUTES=90 -e WEB_SESSION_MAX_HOURS=1 welinc_auth_service npm run env:check` → `WEB_SESSION_IDLE_MINUTES: must be at most WEB_SESSION_MAX_HOURS × 60` → spec table cross checks
- [x] `docker exec welinc_auth_service npm run env:check` and the same for `welinc_vrms_backend` → `Environment check passed` with your normal `.env` → AC-8

### Frontends (run in welinc-web-vrms and welinc-web-portal)
- [x] `npm run lint`, `npm test` (the drift test included) → pass → AC-10
- [x] `npm run build:local` → builds with the committed `.env.development`, no extra setup → AC-8
- [x] `npm run build` with no `VITE_*` set → stops with `Environment check failed (mode production)` and each name as `is required` → AC-7
- [x] `VITE_API_BASE_URL=http://localhost:3000 npm run build` (web-vrms: also `VITE_PORTAL_URL`) → `must use https in production`; with `https://localhost` → `must not point at localhost in production` → AC-4
- [x] `VITE_API_BASE_URL=https://api.welinc.test npm run build` (web-vrms: both names) → builds → AC-4, AC-7
- [x] `grep -rn "localhost" src --include=*.ts --include=*.tsx` in both frontends → no address fallback left in app code → AC-7

### Workspace
- [x] `node --test scripts/test/sync-env.test.mjs` → 5 pass → AC-12
- [x] Copy `welinc-backend-vrms/.env` to a scratch folder with its `.env.example`, delete two names from the copy, run `node scripts/sync-env.mjs <scratch folder>` → prints `added <folder>: NAME, NAME` only; the copy keeps every old line and gains the two under `# Added by sync-env on <date>`; a second run prints the `ok` line → AC-12

## UI / manual
- [x] Restart `welinc_auth_service` and `welinc_vrms_backend`, then read their logs → `[Env] Environment: development`; backend-vrms warns once per service that is off (AI without `GEMINI_API_KEY`, storage if unset); auth warns about mail only if SMTP is unset or partly set (naming the missing names) → AC-5
- [x] The auth log still shows `[SigningKeys] signing key <kid> is current`, and backend-vrms still self tests its client key at boot → AC-13
- [x] Sign in through the portal at `http://localhost:8000` as `vrms.admin@` and land in VRMS → the whole login still works with every app reading its checked config → AC-8
- [x] On a scratch copy of the stack (not your real `.env`): remove `AUTH_ISSUER` from `welinc-backend-vrms/.env`, restart the container → it stops, and its log has the `Environment check failed` list → AC-1
- [x] `sh scripts/setup.sh vrms` on a machine with an older `.env` → the Environment files step prints the added names, and the stack starts clean → AC-8, AC-12

## Value sourcing
- [x] Backends, local: the values come from `.env` plus the compose `environment` block → the `env:check` passes above prove it
- [x] Backends, hosted: `Dockerfile.prod` in both backends sets `ENV NODE_ENV=production` → `grep -n NODE_ENV Dockerfile.prod`
- [x] Backends, Jest and CI: `testEnv` through `setupFiles` → `package.json` `jest.setupFiles` points at `config/test-env.setup.ts`
- [x] Frontends, CI build: `env:` values in each `ci.yml` → `npm run build` step carries `https://*.ci.example.test` values
- [x] Frontends, production build: `ARG VITE_*` in each `Dockerfile.prod` → the build argument names match the schema
- [x] Drift test: the names in `.env.example` (`NAME=` and `# NAME=`) → a name added to only one side fails the test

## Acceptance-criteria coverage
- AC-1 env:check runs, sentinel tests, scratch stack removal · AC-2 env:check malformed runs, Jest tables · AC-3 production env:check runs · AC-4 production env:check runs, frontend http and localhost builds · AC-5 boot logs · AC-6 Jest defaults test · AC-7 frontend builds, no fallback grep · AC-8 build:local, env:check pass, login, setup · AC-9 Jest without `.env` · AC-10 drift tests · AC-11 lint step · AC-12 sync-env test, scratch run, setup · AC-13 boot logs
