# BMS verification record

Updated 17 November 2026. Node 24.13, npm, Docker Desktop, the shared stack
and BMS Compose. This is local evidence, distinct from lead acceptance and
deployment. See the [hosting handoff](hosting-handoff.md).

## Lead-reported acceptance

The current [move guide](../../integration/move-bms.md) records a 17 November
PR-stack run with VMMS: **login 16/16, fleet 5/5, clean static scan**. It marks
fleet acceptance and coordinated PR creation complete. This supersedes the
16 November local 15/16 result, which lacked VRMS. We did not repeat that
cross-system run here. Only the shared lead ticks the shared checklist.

## Local checks

| Check | Result |
|---|---|
| Backend subprocess builds, typecheck, lint | Passed |
| Six production runner/seed image pairs | Built and inspected: non-root, compiled entrypoints, no environment files; runners exclude development/optional CLI tools |
| Gateway auth/session/proxy/hosting | 110 tests passed |
| Booking auth/webhook/tracking/payment-method/hosting | 78 tests passed |
| Dispatch auth/fleet/hosting | 78 tests passed |
| Existing dispatch timing/assignment contracts | 35 tests passed |
| Completion auth/hosting | 72 tests passed |
| Root demo and seed guard contracts | 3 tests passed |
| Projection hosted-address/pool configuration | 2 tests passed |
| Analytics build with Prisma generation, typecheck, lint | Passed |
| Analytics auth/hosting/shared-pool | 73 tests passed |
| Analytics forecast/report logic | 24 tests passed |
| Real PostgreSQL saved-report storage and cleanup | Passed on isolated and local owned databases |
| Web typecheck/lint/production build | Passed; 32 lint warnings and Vite bundle/dependency warnings remain |
| Web session helpers / report calculations | 18 / 20 tests passed |
| Browser UI with controlled APIs | 24 tests passed, including failed sign-out retry/Stay here |
| Production assets under shipped SPA/security headers | 1 browser test passed; deep link restored, no CSP violations |
| Real portal login, BMS deep link and shared sign-out | 1 browser test passed after dependency refresh |
| Runtime dependency audits at high/critical threshold | All seven packages passed; web retains two moderate ExcelJS/UUID advisories |
| Shared static checker | 3 repositories ok, 0 failed |
| Official suite people manifest checker | Matches people.json |
| Compose validation and four owner migration/baseline jobs | Passed |

Nodemailer moved to the patched 10.x release because no patched 9.x release was
available. Its JSON transport contract and booking suites passed; no provider
email was sent. Nest, React and Prisma framework major versions are retained.

## Full demo and populated projection

`npm --prefix welinc-backend-bms run test:seed:integration` passed using four
isolated real PostgreSQL databases and actual booking, dispatch, completion
and analytics APIs. Auth and VMMS were controlled upstream contract fixtures,
not live other-group services. The test verifies:

- Fresh owner migrations using seed images with only DATABASE_URL.
- Only untouched/unlinked/unused legacy helpers are removed; edited, linked
  and referenced helpers survive. Baseline creates 12 drivers and 20 helpers.
- Production seed refusal and fleet outage preflight before operational writes.
- 150 deterministic scenarios, repeat runs without duplicates, and recovery
  after interruption between dispatch and completion.
- Operational reports with 138 non-cancelled bookings and 133 completed jobs;
  the Operations API refuses a vehicle under maintenance.
- Saved-report JSON storage and projection twice using a login with DML but no
  DDL permission; all 150 rows and correct net paid totals are projected.
- Runtime connection budgets; manually changed customer/payment data and a
  manually deleted demo booking survive reruns.

The populated test exposed missing projection fields that empty-data checks
could not cover. Additive analytics migration `20261117030000_projection_fields`
creates them. No migration present before this task was rewritten. Task test
databases, the temporary role and child services were cleaned up.

## Running local stack

BMS dependency volumes were refreshed with current Linux packages. Analytics
was recreated with its own bms-analytics environment. Four owner migrations and
baseline jobs applied without resetting database volumes. Gateway health
returned 200 with all five upstream checks healthy. Live BMS route/role/crew
checks and saved-report storage passed.

The local VMMS checkout still lacks its fleet endpoint. The full root seed
stops with FLEET_UNAVAILABLE_START_VMMS_FIRST and leaves local bookings at zero.
Catalogs and linked crew are seeded. Actual VMMS is required to populate the
local full demo; no fallback trucks were inserted. This local prerequisite is
separate from the lead's successful PR-stack run.

Validation initially exhausted C: cache space. Task output/caches moved to D:
and affected checks were rerun. Playwright browser cache paths use junctions to
`D:/repos/CAPSTONE-bms/.bms-task-cache/playwright`. No user database volume or
unrelated project was reset. Real account erasure, provider delivery and Azure
deployment were outside this validation.

## Reproduce

Follow [setup.md](setup.md). Backend root: bootstrap:ci, audit:ci, typecheck,
lint:ci, build, test. Analytics: build, typecheck, lint:ci, test:auth, test.
Web: lint, typecheck, test, build:prod, test:ui. For test:hosting, configure the
production/staging HTTPS VITE_API_BASE_URL and VITE_PORTAL_URL first.

Build hosting-check runner/seed tags for all six Dockerfile.prod files before
test:seed:integration; the four BMS database containers must run. The test
creates/drops only its own bms_hosting_test_* databases and loads no project
environment file.

```sh
node scripts/check-system.mjs bms --static-only
node welinc-backend-bms/scripts/check-live.mjs
npm --prefix welinc-auth run seed:check -- ../welinc-backend-bms/bms-dispatch-service/prisma/seeds/people.json
```

Official green hosting PRs, provider-key handoff, Azure deployment and written
sign-off remain the leads' work; see [integration-checklist.md](integration-checklist.md).
