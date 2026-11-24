# Verify: Error monitoring · spec 0025 · updated 2026-11-17
_Steps derived from spec 0025 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Milestone 1 (backend-vrms and web-vrms, proven from the laptop)

Setup for the live steps: put the `vrms-backend` DSN in `welinc-backend-vrms/.env` with `SENTRY_ENVIRONMENT=staging` and `SENTRY_TEST_ROUTES=true`, then recreate the container (`docker compose -f docker-compose.vrms.yml up -d vrms-backend`). Put the `vrms-web` DSN in `welinc-web-vrms/.env.development.local` with `VITE_SENTRY_ENVIRONMENT=staging` and `VITE_SENTRY_TEST_ROUTES=true`, then restart `welinc_vrms_frontend`. The gateway allows `sentry-trace` and `baggage` since commit `efc94f9` (pulled forward from milestone 2), so browser API calls pass their preflight while `VITE_SENTRY_DSN` is set; restart `welinc_api_gateway` once to load it.

### UI / manual
- [ ] Signed in as `vrms.admin@welinc.com`, `POST /vrms/debug/sentry-test` → 500, and one issue in `vrms-backend` within a minute with `environment: staging`, `system: vrms`, user id only, `role: ADMIN` → AC-1, AC-16
- [ ] Same call as a mechanic (no `settings.manage`) → 403; with `SENTRY_TEST_ROUTES` blank → 404, also for a signed out caller → AC-16
- [ ] Stop welinc-auth and make a signed in call that misses the cache → 503 `AUTH_UNAVAILABLE`, and one issue arrives (the 5xx `HttpException` path) → AC-1
- [ ] A validation 400, a 401 and a 403 create no issue; a failing `/vrms/health` 503 creates none → AC-2
- [ ] Open `/debug/sentry` as the admin, press Crash this page → the sidebar and top bar stay, the crash screen shows Reload, Back to dashboard and an 8 character reference that matches the start of the Sentry event id (since 2026-11-25 an admin sees it as the `Code:` line in the details box instead, AC-7a); one issue in `vrms-web` with `system: vrms-web` and `role: ADMIN` → AC-3, AC-7, AC-16
- [ ] Click another menu item after the crash → the page loads normally → AC-7
- [ ] `/debug/sentry` as a mechanic → sent to the dashboard; in a build without the flag the address is Page not found → AC-16
- [ ] With `VITE_SENTRY_DSN` blank, crash the page again → crash screen without a reference code, nothing sent → AC-7, AC-14
- [ ] Turn the network off in DevTools and use a page → no issue; an API call (with the gateway change) carries `sentry-trace` and `baggage` → AC-9
- [ ] Open both test events in Sentry → no email, name, IP, cookie, `Authorization`, query string or request body; `request.headers` has only the user agent; `user.geo` shows `[Filtered]` for country, city and region → AC-6
- [ ] Delete a lazy chunk from a built `dist` served locally, then click the dev or test page link → one silent reload; again in the same tab → crash screen; offline → no reload → AC-8

### Commands
- [x] `cd welinc-backend-vrms && npm test -- src/monitoring src/config` → passes (`redact`, `beforeSend` drops 4xx and health, keeps 5xx, allowlisted request, user id only, the 5xx filter, the env rules) → AC-1, AC-2, AC-6, AC-14, AC-15
- [x] `npm run build && SENTRY_DSN=https://k@o1.ingest.us.sentry.io/2 SENTRY_ENVIRONMENT=dev npm run env:check` → exits 1 naming `SENTRY_ENVIRONMENT` → AC-15
- [x] `SENTRY_ENVIRONMENT=production SENTRY_TEST_ROUTES=true npm run env:check` (with a DSN) → exits 1 naming `SENTRY_TEST_ROUTES` → AC-15
- [ ] Start with `SENTRY_ENVIRONMENT=production` and no DSN → starts, logs one "Error monitoring is off" warning → AC-15
- [x] `npm run openapi:check` → `docs/openapi.json` matches; `/vrms/debug/sentry-test` is not in it even with the switch on → spec 0026 AC-7
- [x] `cd welinc-web-vrms && npx vitest run src/lib/monitoring` → passes (API client errors dropped, cap of 10, query stripped, VRMS role tag, reload once) → AC-6, AC-8, AC-9
- [x] `npm run build:local && grep -rl "Sentry test crash" dist` → nothing; the same build with `VITE_SENTRY_TEST_ROUTES=true` → one `SentryTestPage-*.js` chunk → AC-16

### Value sourcing
- [ ] Backend `environment` and `release` come from `SENTRY_ENVIRONMENT` and `SENTRY_RELEASE`: set `SENTRY_RELEASE=abc123`, trigger the test route → the issue shows release `abc123`
- [ ] Browser `environment` and `release` come from `VITE_SENTRY_ENVIRONMENT` and `VITE_SENTRY_RELEASE`: set a different release in the web app → the browser issue shows that one, not the backend's
- [ ] `system` tag: backend events say `vrms`, browser events `vrms-web`
- [ ] Backend user and role come from `request.user`: sign in as a person with VRMS and VMMS roles → `role` lists only the VRMS role
- [ ] Browser user and role come from the refresh answer's `VRMS` roles entry: a person with no VRMS role entry gets no `role` tag (never the `MECHANIC` fallback)
- [ ] Reference code is the first 8 characters of the event id the boundary got back

## Milestone 2, task 7a (the gateway's envelope DSN check)

### Commands
- [x] `node infra/gateway/test/check-routes.mjs` → every check passes (164 on 2026-11-17), the S-AC4 and S-AC5 tunnel cases included → AC-4, AC-5
- [ ] In that run, each of these answers 403 `TUNNEL_REJECTED` with CORS and never reaches the stand in: another project on the same host, another organization's host, the other route's DSN, a different key, an uppercase key, a port, a trailing slash, a trailing newline, a password, `http`, a duplicate `dsn`, an escaped `dsn`, no `dsn`, a `dsn` that isn't a string, an array header, no newline in the first 8 KB, a header that isn't JSON, an empty body, and a gzip body → AC-5
- [ ] In that run, a binary envelope and a body just under 1 MB arrive byte for byte, Sentry's `Retry-After` and `X-Sentry-Rate-Limits` come back, a forwarded and a refused report each log exactly one line with nothing from the body, refused reports count against the tunnel limit, and `/_tunnel/*` answers 404 from outside → AC-5
- [ ] In that run, `SENTRY_DSN_VRMS_WEB` or `SENTRY_DSN_PORTAL` set alone, or malformed (uppercase, port, slash, extra path, query, `http`, password, foreign host, project 0, short key), stops the start and names the setting → AC-5

### Live (from your laptop, real `welinc` org)
- [ ] Start the gateway image with both real DSNs, then post an envelope with the `vrms-web` DSN to `/monitoring/vrms-web` with `environment: development` → 200, and exactly one event lands in `vrms-web` (done 2026-11-17, event `b8a42313`) → AC-4, AC-5
- [ ] Post the portal DSN to `/monitoring/vrms-web` and the `vrms-web` DSN to `/monitoring/portal` → both 403 `TUNNEL_REJECTED`, and a Sentry search for their messages finds nothing (done 2026-11-17) → AC-5
- [ ] On staging (after milestone 3), repeat the cross project post against the hosted gateway → 403 → AC-5

## Acceptance-criteria coverage
- AC-1 test route issue, 503 path, unit tests · AC-2 4xx and health steps, unit tests · AC-3 test page issue (readable TypeScript stack waits for milestone 3's maps) · AC-6 event inspection, unit tests · AC-7 crash screen steps · AC-8 lazy chunk step, unit tests · AC-9 offline and trace header step (needs milestone 2's gateway CORS) · AC-14 blank DSN step · AC-15 env:check steps · AC-16 route and page steps, build search
- AC-4, AC-5 the task 7a harness and live steps (the staging repeat waits for milestone 3)
- AC-10 to AC-13, AC-17, AC-18 belong to milestones 3 and 4

## Run on 2026-11-20 (`/check verify error monitoring`)
Result: **passed, with 5 behaviors blocked by design** (accepted by the lead). Staging's test routes are off (spec 0008 AC-24, task 19a step 3) and local Sentry stays off, so these can't be produced on purpose:
- AC-1 `release` tag on a hosted event, and AC-3 readable TypeScript stack from a hosted build: the first real error on staging shows both.
- AC-7 and AC-8 on a live page: unit tests only.
- AC-10 job exception tagged with its job name: not triggered.
- The AC-11 and AC-12 emails: the monitor and rule exist and fired, but arrival wasn't read.

Proven live: gateway tunnel (164 of 164 checks; on staging OPTIONS 204, GET 405, foreign DSN 403 `TUNNEL_REJECTED`), test routes 404 on staging, `.map` files 404 on both web sites, cron monitor `ok`, uptime monitor `ok`, the new issue rule fired at 01:00 UTC, five Azure alerts to `ag-welinc-staging`, no email, name or IP in two real events.

## Crash screen by standing · task 13 · added 2026-11-25
_Locally, with `VITE_SENTRY_TEST_ROUTES=true` in each app's `.env.development.local` (never the committed `.env.development`). Seed logins in `docs/integration/seed-accounts.md`._

### UI / manual
- [ ] web-vrms, signed in as `vrms.admin@welinc.com`, `VITE_SENTRY_DSN` blank: open `/debug/sentry?x=1`, press Crash this page → sidebar and top bar stay; the line reads "Try reloading. Copy the details below into your bug report."; the details box shows `Error: …`, `Page: /debug/sentry` (no `?x=1`), `Time: YYYY-MM-DD HH:mm:ss (…Z)`, `App: web-vrms local`, and no `Code:` line → AC-7a
- [ ] Press Copy details and paste into a text field → exactly the box text; the button reads "Copied" for about 2 seconds, then "Copy details" again → AC-7a
- [ ] Set `VITE_SENTRY_DSN` in `.env.development.local`, crash again as the admin → a `Code:` line joins the box and matches the first 8 characters of the event id in `vrms-web`; no separate Reference line → AC-7a
- [ ] Open web-vrms through the LAN address over http (for example `http://<your LAN IP>:8001`, a page that isn't secure, so there is no clipboard API), crash as the admin, press Copy details → the button reads "Select and copy the text above" and the box text can still be selected → AC-7a
- [ ] Portal, signed in as a suite admin, at `/debug/sentry` → the same admin version with `App: web-portal local` and Back to apps; Copy details works as above → AC-7a
- [ ] Staff version without a code: in the portal's permission matrix give a non admin VRMS role `settings.manage` for the test, sign in as that person in web-vrms with the DSN blank, crash `/debug/sentry` → "Try reloading. If it keeps happening, tell your admin what you were doing.", no code line, no details box; then with the DSN set → "…send this code to your admin." and the Reference code. Take the permission back after → AC-7
- [ ] One accessibility snapshot of the admin version (`browser_snapshot`) → the `alert` holds only the title and the line; the details box (`Crash details`) and the buttons sit outside it → AC-7a
- [ ] Sign out of web-vrms as the admin and sign in as a mechanic in the same tab, then crash any page (staff with `settings.manage` from the step above) → staff version, never the admin one → AC-7a

### Commands
- [x] `npm test` in welinc-web-vrms (599 passing) and welinc-web-portal (366 passing) → `crashDetails`, `copyText`, the three `CrashScreen` versions, the Code line joining, the copy labels and the standing flag pass → AC-7, AC-7a

### Acceptance-criteria coverage
- AC-7 staff steps with and without a code, unit tests · AC-7a admin steps in both apps, the copy and fallback steps, the accessibility snapshot, the sign out step, unit tests (system admin standing and demotion in the portal are unit tests only)

