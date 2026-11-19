# BMS hosting handoff

Prepared 17 November 2026 against [hosting.md](../../integration/hosting.md).
This is the BMS working record. Only the shared lead updates the shared checklist.
The implementation design is [BMS spec 0002](../../specs/bms/0002-hosting-readiness/index.md).

## Images and jobs

Each of the five processes in `welinc-backend-bms` and the separate analytics
API has a `Dockerfile.prod`. Build from that process's directory:

```sh
docker build -f Dockerfile.prod -t <app>:<sha> .
docker build -f Dockerfile.prod --target seed -t <app>-seed:<sha> .
```

The final runner uses Node 24 Alpine, production dependencies and the `node`
user. It starts compiled output without an environment file or migration.
The seed target includes source, development tools and migrations. Override
its command explicitly for a job. It also runs as `node`.

| App | Port | Entrypoint | Platform readiness |
|---|---|---|---|
| bms-gateway | 3020 | dist/main.js | /bms/health |
| bms-booking | 3021 | dist/src/main.js | /health/ready |
| bms-dispatch | 3022 | dist/src/main.js | /health/ready |
| bms-completion | 3023 | dist/src/main.js | /health/ready |
| bms-analytics-projection | 3024 locally | dist/worker.mjs | worker; no hosted ingress |
| bms-analytics | 3025 | dist/src/main.js | /health/ready |

Every owning database uses `npx prisma migrate deploy` from its seed image.
It needs only `DATABASE_URL`; use the owner login. The application login needs
row access, not DDL. The projection metadata table is created by analytics
migration `20261117000000_projection_metadata`, compatible with an existing
local table. The worker no longer creates tables at runtime. Populated
projection fields are covered by additive analytics migrations,
including `20261117030000_projection_fields` for booking number, completion
details and assignment timestamps. Saved reports
and forecasts already use the same owned PostgreSQL database, with no MySQL.
No BMS migration creates a PostgreSQL extension. No BMS service stores lasting
uploads or reports on local disk; reports/forecasts are in PostgreSQL.

## Settings to provision

The authoritative variable names and local examples are in the backend,
analytics and projection `.env.example` files. Never send environment files or
private values in a PR. The lead supplies the per-environment addresses,
database logins, suite client keys and BMS internal secrets.

| Processes | Additional settings |
|---|---|
| All Nest APIs | AUTH_ISSUER, AUTH_JWKS_URL, AUTH_INTERNAL_URL, AUTH_CLIENT_ID, AUTH_CLIENT_PRIVATE_KEY; NODE_ENV=production and PORT from the table |
| All database processes | DB_POOL_MAX=2; DATABASE_URL with sslmode=require; projection instead uses ANALYTICS_READ_MODEL_DATABASE_URL |
| Gateway | BMS_SESSION_HOST=true, SESSION_COOKIE_SECURE=true, TRUST_PROXY_HOPS=2; API_PUBLIC_URL, AUTH_PUBLIC_URL, PORTAL_URL, WEB_APP_URL, CORS_ORIGINS; BOOKING_API_URL, DISPATCH_API_URL, COMPLETION_API_URL, ANALYTICS_API_URL |
| Booking | BMS_BOOKING_HOST=true, CUSTOMER_TRACKING_SECRET, BMS_INTERNAL_SERVICE_KEY; DISPATCH_API_URL, COMPLETION_API_URL; optional webhook/provider settings below |
| Dispatch | BOOKING_API_URL, VMMS_INTERNAL_URL, BMS_INTERNAL_SERVICE_KEY; optional GOOGLE_GEOCODING_API_KEY for travel estimates |
| Completion | BOOKING_API_URL, DISPATCH_API_URL, BMS_INTERNAL_SERVICE_KEY |
| Projection | BOOKING_API_URL, DISPATCH_API_URL, COMPLETION_API_URL, BMS_INTERNAL_SERVICE_KEY; optional PROJECTION_INTERVAL_MS (default 10000) |
| Analytics | AUTH_CLIENT_ID=bms-analytics and its own AUTH_CLIENT_PRIVATE_KEY; BOOKING_API_URL, DISPATCH_API_URL, COMPLETION_API_URL; optional GROQ_API_KEY and GROQ_MODEL |

The four other Nest APIs use `AUTH_CLIENT_ID=bms`. Analytics reads only its
own environment in local Compose; it never inherits the backend's private key.
All hosted HTTP addresses must be HTTPS and non-loopback. Production boot
rejects insecure/missing required addresses. Both analytics database consumers
share one pool, so Prisma plus report storage stay inside the two-connection
budget. Readiness gives each database check at most two seconds.

Leave `ANALYTICS_PROJECTION_URL` unset on the hosted gateway: the worker has no
ingress. Local Compose sets it and includes worker readiness in gateway health.

Booking's optional integrations use GOOGLE_MAPS_API_KEY,
GOOGLE_GEOCODING_API_KEY, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM,
CUSTOMER_SUPPORT_EMAIL and CUSTOMER_SUPPORT_PHONE. Signed inbound booking uses
BMS_WELINC_BOOKING_WEBHOOK_SECRET and BMS_WELINC_WEBHOOK_API_KEY. Unconfigured
optional providers remain disabled. Provider keys must be sent privately by
the BMS group; no provider delivery or AI call was made during validation.

## Staging must keep these processes awake

Please correct the draft hosting table: booking and dispatch also run timers.

- Booking: approval/outbox delivery every five seconds.
- Dispatch: directory-based crew erasure synchronization every 24 hours.
- Analytics projection: continuous projection loop (10 seconds by default).

These three need at least one staging replica even without traffic. The other
processes can follow the lead's existing staging scale settings.

## Default seeds

Migrations run first. Per-owner baseline commands remain independent and
preserve existing edits. All seed entrypoints refuse `NODE_ENV=production`
unless the job explicitly has `SEED_ALLOW=staging`. Never set that override on
production jobs.

| Seed image | Baseline command |
|---|---|
| bms-booking-seed | npm run seed (missing catalog rows only) |
| bms-dispatch-seed | npm run seed (12 linked drivers and 20 linked helpers) |
| bms-completion-seed | npm run seed (guarded no-op) |
| bms-analytics-seed | npm run seed (guarded no-op; projection owns demo read models) |

For the full default demo on the local running stack, from the workspace:

```sh
npm --prefix welinc-backend-bms run seed
```

It preflights actual VMMS vehicles and suite directory identities, freezes the
resource map/anchor, then inserts 150 tagged demo bookings across 90 historical
days and current/future workflows. It includes completed/cancelled work,
unassigned/assigned/distributed jobs, unpaid/pending/partial/paid/refunded
collections and analytics through the real projection. It sends no customer
notifications, creates no auth accounts or trucks, and performs no reset.
Catalog and crew baselines can run without VMMS. Full demo requires the fleet
API; `FLEET_UNAVAILABLE_START_VMMS_FIRST` means restore VMMS and rerun.

The manifest and row ledger make reruns resume interrupted phases without
duplicates. The original anchor stays fixed. Edited or manually deleted demo
scenarios are excluded across owners, retaining user changes. The helper
cleanup migration removes only the exact three untouched, unlinked, unused
legacy examples; modified or referenced helpers are retained.

Hosted full-demo orchestration is an explicit ordered job sequence, after
baseline seeds, with staging permission and the relevant owner's configuration:

1. Dispatch: `node scripts/seed-resources.mjs` outputs the manifest JSON.
2. Booking: `node scripts/seed-demo.mjs plan` stores/returns it. On resume use
   `node scripts/seed-demo.mjs load` and reuse the stored manifest.
3. Each owner: `node scripts/seed-demo.mjs inspect`. Union returned booking IDs
   into manifest `excludedBookingIds` so edits stay preserved across owners.
4. Booking, then dispatch, then completion: `node scripts/seed-demo.mjs apply`.
5. Projection seed image: `npm run once`.
6. Booking: `node scripts/seed-demo.mjs complete`.

Pass manifest JSON on stdin or in the job-only `BMS_SEED_MANIFEST` setting.
`BMS_SEED_ANCHOR_DATE` optionally selects the initial Manila calendar date.
Do not put these job settings on normal production services. Resource mapping
contains suite identifiers, so keep it in the job handoff rather than public logs.

## Static web app and delivery

Build with `npm run build:prod`, VITE_API_BASE_URL set to the environment's
suite API and VITE_PORTAL_URL to its portal. VITE_GOOGLE_MAPS_API_KEY is a
browser key restricted to `bms.welinc.app` and `staging-bms.welinc.app`.
Deploy `dist/`; `public/staticwebapp.config.json` supplies SPA deep links and
security headers. Leaflet is bundled; Google Maps, Carto tiles and font hosts
are explicitly enumerated. Google's documented Maps CSP requires
`unsafe-eval`; see [Google's CSP guide](https://developers.google.com/maps/documentation/javascript/content-security-policy).

CI and Dependabot templates are included in all three BMS repositories.
Backend CI covers every subprocess; web CI builds with production mode.
The lead's deploy workflows, Azure provisioning, official development-branch
PR checks/merge and private provider-key handoff remain external delivery work.
This task updates the personal backup only; it does not deploy Azure or modify
other groups' application source.
