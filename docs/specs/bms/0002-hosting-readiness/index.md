# BMS hosting readiness and default demo seeds

Approved scope: the full `docs/integration/hosting.md` checklist, analytics'
separate `bms-analytics` identity, the missing VRMS session helpers, and a private
backup refresh. The lead's current integration checklist remains authoritative
and is not edited or ticked by this implementation.

## Runtime and build

All six backend processes receive Node 24 production images with a full-source
seed target and a final non-root runner. Runtime images contain no environment
files, development dependencies or startup migrations. The web app is a static
build, with SPA fallback and narrowly scoped security headers for `welinc.app`.

Every database process defaults to `DB_POOL_MAX=2`. Analytics shares one pool
between Prisma and report storage; the setting caps the entire process. Database
readiness expires after two seconds. Projection metadata is created by an
additive analytics migration, including compatibility with the existing local
table. Gateway projection readiness is optional because Azure runs it as a
worker without ingress. Production settings reject loopback/insecure URLs and
require secure gateway session cookies.

Analytics builds run Prisma generation before Nest compilation. Analytics uses
its own key/environment as `bms-analytics`, without inheriting the `bms` key.
Shared auth source and all other groups' source stay unchanged. Its existing
key and client-seed tools may configure local runtime credentials without
displaying values. CI keeps the VRMS reference triggers/permissions/concurrency;
commands cover the actual BMS packages and fail on high/critical runtime
dependency vulnerabilities. Framework major versions stay unchanged.

## Sessions

Copy the VRMS sign-out flow and system-switch tests with BMS names and roles.
All BMS sign-out controls use one confirmation/retry/cancel flow. Keep the
existing BMS presentation and shared session semantics.

## Seeds

Per-owner baseline seeds remain usable by shared setup. A backend-root default
seed command orchestrates full demo phases, with each process writing only its
own database. Standard catalogs/crew are idempotent and preserve edits; no BMS
seed creates auth accounts. Full demo data uses actual VMMS vehicles and the
suite identities, with no fabricated fleet, notifications, external provider
calls, or destructive reset. All seed entrypoints reject production unless
`SEED_ALLOW=staging`.

The versioned demo contains 150 tagged bookings: 144 historical bookings across
90 days for the four main services and six current/future scenarios. Include
completed/cancelled work, unassigned/confirmed/distributed jobs, unpaid,
pending-verification, partial/full verified collections and linked refunds.
Booking holds/versions and operational/payment records must agree. Analytics is
populated through projection, not a second independent seed dataset.

Preflight the fleet and required services before operational demo writes. Store
the dataset anchor/resource mapping in booking-owned metadata so reruns keep
dates/identities stable, resume interruptions and preserve edited scenarios.
Add a migration to remove only the three exact untouched, unlinked and unused
historical demo helpers; retain any edited, linked or referenced record.

## Evidence and delivery

Test production images, migrations with only DATABASE_URL, restricted-role
projection, pool limits, health deadlines, environment checks, session flows,
seeds twice, partial-run recovery and preservation of existing data. Run CI
commands, integration static checks and browser regressions. Document timers,
extensions, storage, deployment variables and owner-job commands for the lead.
No Azure deploy or changes to the official repositories/PRs are authorized here.

Restore the existing private personal backup as a separate sibling checkout,
preserve its history, synchronize the current workspace BMS source and shared
reference context, exclude secrets/dependencies/generated/runtime files, then
commit, push and verify the remote commit and privacy.
