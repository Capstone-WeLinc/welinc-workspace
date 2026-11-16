# BMS verification record

Date: 16 November 2026. Environment: Node 24.13, npm, Docker Desktop,
shared auth/portal/gateway and the BMS Compose stack. This records local evidence;
it is not the shared services lead's final acceptance or written sign-off.

## Build and automated checks

All five NestJS APIs build successfully. Frontend TypeScript checking and Vite
build pass. The web build still emits dependency `use client` and bundle-size
warnings; bundle optimization was outside this integration change.

| Component / check | Result |
|---|---|
| Gateway verifier, account/session, route and streaming proxy tests | 106 passed |
| Booking verifier/account and webhook/tracking tests | 73 passed |
| Dispatch verifier/account and VMMS consumer tests | 74 passed |
| Dispatch existing fleet, timing and assignment contracts, plus optional helper fields | 35 passed |
| Completion verifier/account tests | 68 passed |
| Analytics verifier/account tests | 68 passed |
| Analytics forecast and operational report logic | 24 passed |
| Live PostgreSQL saved-report storage contract | 1 passed; own fixture removed |
| Frontend reference session timing/boot helpers | 11 passed |
| Frontend report calculations | 20 passed |
| Browser UI suite with mocked APIs | 23 passed |
| Real portal → BMS deep-link → shared sign-out browser check | 1 passed |
| Official BMS static leftover scan | 3 repositories ok, 0 failed |
| Official people manifest check | Matches people.json |
| Compose validation, migrations, repeated seeds | Passed |
| Projection two successive one-shot cycles | Passed on empty booking/assignment data |

The byte-preserving proxy test sends 5 MB with deliberate raw JSON whitespace;
webhook tests verify signatures over exact raw bytes and refuse changed/stale
payloads. The tracking tests bind capabilities to a booking and require their
dedicated secret. Verifier tests refuse legacy signing algorithms and wrong
audiences. VMMS consumer tests cover caching, fresh assignment reads, outages,
missing/unavailable vehicles, temporary roles, and a retry only for TOKEN_EXPIRED.

## Live local behavior

`welinc-backend-bms/scripts/check-live.mjs` passed for booking and catalog lists,
saved reports, the analytics booking read-model route, the shared profile cursor
feed, 12 linked drivers and 20 linked helpers, and BMS role restrictions. With
VMMS unavailable, vehicles correctly return `503 FLEET_UNAVAILABLE`.
Tokens stay in memory and the test signs out its sessions.

`GET http://localhost:3000/bms/health` returned 200 with healthy booking,
dispatch, completion, analytics and projection checks. The shared auth readiness
and published signing-key endpoints also answered successfully.

The unchanged shared checker's local login slice was run:

```sh
node scripts/check-system.mjs bms --live-only --login
```

Result: **15 passed, 1 failed**. BMS health, portal sign-in, PKCE/callback cookie,
Origin/CSRF rejection, BMS refresh token audience, protected requests,
missing/tampered-token rejection, mobile-only account denial, the 5 MB validation
request, logout, old-refresh rejection and ended-session enforcement passed.
The final access-token check observed `SESSION_ENDED` within the 31-second limit.

The failed case needs a live VRMS session to obtain another system's user token.
The checker's request to `/vrms/session/start` returned 502 because that backend
is not running. It did not reach the BMS wrong-audience assertion. BMS wrong
audiences pass verifier unit tests, but this live acceptance line remains open.
No shared checker code or other group's runtime was changed to bypass it.

## Reproduce the local checks

From the workspace:

```sh
docker compose -f docker-compose.bms.yml config --quiet
node scripts/check-system.mjs bms --static-only
node welinc-backend-bms/scripts/check-live.mjs
npm --prefix welinc-auth run seed:check -- welinc-backend-bms/bms-dispatch-service/prisma/seeds/people.json
docker compose -f docker-compose.bms.yml exec -T bms-analytics node --test test/storage-contract.cjs
docker compose -f docker-compose.bms.yml exec -T bms-analytics-projection npm run once
```

Inside gateway: `npm run build` and `npm test`.
Inside booking: `npm run build` and `npx jest --runInBand`.
Inside dispatch: `npm test` and `npx jest --runInBand`.
Inside completion: `npm run build` and `npm run test:auth`.
Inside analytics: `npm run build`, `npm run test:auth` and `npm test`.
Inside the web app, with its documented browser API/portal configuration:

```sh
npx tsc --noEmit -p tsconfig.app.json
npm run build
npm run test:session
npm run test:unit
npm run test:ui
npx playwright test --project=chromium tests/integration-session.spec.ts --reporter=list
```

## Limits and handoff

The VMMS source available here does not yet implement the documented fleet API.
There is no live fleet parity result, no completed vehicle-assignment acceptance,
and no full real booking/dispatch/completion/payment test against VMMS. No real
account erasure or irreversible account-deletion flow was executed; those UI/API
contracts were checked with controlled responses. Projection cycles currently
verify startup/API/database access on empty operational data, not populated
workflow totals. AI provider calls were not part of verification.

Follow the remaining gates in [integration-checklist.md](integration-checklist.md).
The leads must arrange repository/PR delivery, run the complete unchanged suite
checker once dependencies are available, review the hard switch together, and
record separate login/fleet acceptance. These BMS local copies have no Git
metadata, as requested; no PR was opened and no remote repository was archived.
