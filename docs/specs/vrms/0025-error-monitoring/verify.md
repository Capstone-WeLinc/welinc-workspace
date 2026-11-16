# Verify: Error monitoring · spec 0025 · updated 2026-11-17
_Steps derived from spec 0025 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Milestone 1 (backend-vrms and web-vrms, proven from the laptop)

Setup for the live steps: put the `vrms-backend` DSN in `welinc-backend-vrms/.env` with `SENTRY_ENVIRONMENT=staging` and `SENTRY_TEST_ROUTES=true`, then recreate the container (`docker compose -f docker-compose.vrms.yml up -d vrms-backend`). Put the `vrms-web` DSN in `welinc-web-vrms/.env.development.local` with `VITE_SENTRY_ENVIRONMENT=staging` and `VITE_SENTRY_TEST_ROUTES=true`, then restart `welinc_vrms_frontend`. The gateway allows `sentry-trace` and `baggage` since commit `efc94f9` (pulled forward from milestone 2), so browser API calls pass their preflight while `VITE_SENTRY_DSN` is set; restart `welinc_api_gateway` once to load it.

### UI / manual
- [ ] Signed in as `vrms.admin@welinc.com`, `POST /vrms/debug/sentry-test` → 500, and one issue in `vrms-backend` within a minute with `environment: staging`, `system: vrms`, user id only, `role: ADMIN` → AC-1, AC-16
- [ ] Same call as a mechanic (no `settings.manage`) → 403; with `SENTRY_TEST_ROUTES` blank → 404, also for a signed out caller → AC-16
- [ ] Stop welinc-auth and make a signed in call that misses the cache → 503 `AUTH_UNAVAILABLE`, and one issue arrives (the 5xx `HttpException` path) → AC-1
- [ ] A validation 400, a 401 and a 403 create no issue; a failing `/vrms/health` 503 creates none → AC-2
- [ ] Open `/debug/sentry` as the admin, press Crash this page → the sidebar and top bar stay, the crash screen shows Reload, Back to dashboard and an 8 character reference that matches the start of the Sentry event id; one issue in `vrms-web` with `system: vrms-web` and `role: ADMIN` → AC-3, AC-7, AC-16
- [ ] Click another menu item after the crash → the page loads normally → AC-7
- [ ] `/debug/sentry` as a mechanic → sent to the dashboard; in a build without the flag the address is Page not found → AC-16
- [ ] With `VITE_SENTRY_DSN` blank, crash the page again → crash screen without a reference code, nothing sent → AC-7, AC-14
- [ ] Turn the network off in DevTools and use a page → no issue; an API call (with the gateway change) carries `sentry-trace` and `baggage` → AC-9
- [ ] Open both test events in Sentry → no email, name, IP, cookie, `Authorization`, query string or request body; `request.headers` has only the user agent → AC-6
- [ ] Delete a lazy chunk from a built `dist` served locally, then click the dev or test page link → one silent reload; again in the same tab → crash screen; offline → no reload → AC-8

### Commands
- [ ] `cd welinc-backend-vrms && npm test -- src/monitoring src/config` → passes (`redact`, `beforeSend` drops 4xx and health, keeps 5xx, allowlisted request, user id only, the 5xx filter, the env rules) → AC-1, AC-2, AC-6, AC-14, AC-15
- [ ] `npm run build && SENTRY_DSN=https://k@o1.ingest.us.sentry.io/2 SENTRY_ENVIRONMENT=dev npm run env:check` → exits 1 naming `SENTRY_ENVIRONMENT` → AC-15
- [ ] `SENTRY_ENVIRONMENT=production SENTRY_TEST_ROUTES=true npm run env:check` (with a DSN) → exits 1 naming `SENTRY_TEST_ROUTES` → AC-15
- [ ] Start with `SENTRY_ENVIRONMENT=production` and no DSN → starts, logs one "Error monitoring is off" warning → AC-15
- [ ] `npm run openapi:check` → `docs/openapi.json` matches; `/vrms/debug/sentry-test` is not in it even with the switch on → spec 0026 AC-7
- [ ] `cd welinc-web-vrms && npx vitest run src/lib/monitoring` → passes (API client errors dropped, cap of 10, query stripped, VRMS role tag, reload once) → AC-6, AC-8, AC-9
- [ ] `npm run build:local && grep -rl "Sentry test crash" dist` → nothing; the same build with `VITE_SENTRY_TEST_ROUTES=true` → one `SentryTestPage-*.js` chunk → AC-16

### Value sourcing
- [ ] Backend `environment` and `release` come from `SENTRY_ENVIRONMENT` and `SENTRY_RELEASE`: set `SENTRY_RELEASE=abc123`, trigger the test route → the issue shows release `abc123`
- [ ] Browser `environment` and `release` come from `VITE_SENTRY_ENVIRONMENT` and `VITE_SENTRY_RELEASE`: set a different release in the web app → the browser issue shows that one, not the backend's
- [ ] `system` tag: backend events say `vrms`, browser events `vrms-web`
- [ ] Backend user and role come from `request.user`: sign in as a person with VRMS and VMMS roles → `role` lists only the VRMS role
- [ ] Browser user and role come from the refresh answer's `VRMS` roles entry: a person with no VRMS role entry gets no `role` tag (never the `MECHANIC` fallback)
- [ ] Reference code is the first 8 characters of the event id the boundary got back

## Acceptance-criteria coverage
- AC-1 test route issue, 503 path, unit tests · AC-2 4xx and health steps, unit tests · AC-3 test page issue (readable TypeScript stack waits for milestone 3's maps) · AC-6 event inspection, unit tests · AC-7 crash screen steps · AC-8 lazy chunk step, unit tests · AC-9 offline and trace header step (needs milestone 2's gateway CORS) · AC-14 blank DSN step · AC-15 env:check steps · AC-16 route and page steps, build search
- AC-4, AC-5, AC-10 to AC-13, AC-17, AC-18 belong to milestones 2 to 4
