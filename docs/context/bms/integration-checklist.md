# BMS integration working checklist

Updated 17 November 2026. Requirements: [move-bms.md](../../integration/move-bms.md)
and [hosting.md](../../integration/hosting.md). Implementation design:
[BMS spec 0001](../../specs/bms/0001-shared-services-integration/index.md) and
[hosting/seeds spec 0002](../../specs/bms/0002-hosting-readiness/index.md).
See the [verification record](verification.md) and [hosting handoff](hosting-handoff.md).

Only the shared lead ticks the shared integration checklist. These are BMS
working notes, not an Azure deployment or new official PR acceptance.

## Shared integration

The current lead-authored move guide reports **login 16/16, fleet 5/5 and a
clean scan on the coordinated PR branches**, dated 17 November. It also marks
the fleet and three development-branch PR boxes complete. This supersedes the
older local 15/16 result and fleet-pending status from 16 November. We did not
rerun that cross-system acceptance here; this local VMMS checkout still lacks
the fleet routes. The lead's reported PR-stack result and local prerequisites
are separate evidence.

| Area | BMS implementation |
|---|---|
| Stack / ownership | Five backend processes plus standalone analytics, four owned PostgreSQL databases, shared network and gateway routing |
| Identity | bms for gateway/booking/dispatch/completion; distinct bms-analytics key/environment for analytics |
| Gateway | Nest sessions, exact route ownership, raw streamed forwarding, 10 MB bodies, request IDs and optional worker readiness |
| Tokens / sessions | Copied VRMS verification, PKCE/CSRF/cookies, directory/account checks, shared refresh/idle/tab behavior |
| Accounts / activity | Shared profile and account feeds, BMS work activity, admin confirmation, one-use deletion reauthentication |
| Fleet / crew | Actual VMMS API consumer, fresh assignment checks, outage/maintenance responses, local linked crew/profiles and erasure sync |
| Analytics | Owned PostgreSQL read model and report storage; owner API reads and unchanged bearer forwarding; no foreign DB mappings |
| Web | Portal login, deep links, memory-only tokens, shared confirmation/retry sign-out and system switching |
| People | Exact suite manifest copies; crew profiles only, no auth account creation |

## Cross-check of the move guide

The entries below reflect the local workspace and the lead's recorded checks.
The GitHub session could not resolve the official repositories, so current PR
contents, review status and remote archival could not be confirmed.

| Move guide item | What the evidence supports |
|---|---|
| Step 1: Compose and PR #42 | `docker-compose.bms.yml` exists, passes Compose validation and gives analytics its own environment file. The old note about analytics still needing the Compose update is stale locally. The current contents of PR #42 are unverified. |
| Step 1: `setup.sh bms` | The equivalent local key registration, Compose startup, four owner migrations and baseline seeds were completed. All five upstream health checks returned 200 through BMS. The full shared setup script was not run end to end on these source copies. |
| Step 1: hosting readiness | The box is checked in the current local guide. The old note beneath it is stale: all six production Dockerfiles exist, database pools are capped at two, projection tables and fields come from analytics migrations, and analytics builds run `prisma generate`. See the [hosting handoff](hosting-handoff.md) for the rest of the hosting evidence. |
| Step 2: analytics identity and Groq | Analytics uses `bms-analytics` with its own environment file. Local shared auth granted that client a `directory.read` token. The running container has the `GROQ_API_KEY` and `GROQ_MODEL` fields. Groq API access was not tested. |
| Step 9: web session helpers | `signOutFlow.ts` is wired into sign-out and `switchSystem.test.ts` is present. All 18 web session tests passed on rerun. The shared leftover scan passed for all three repos. |
| Step 11: checker | The lead records login 16/16, fleet 5/5 and a clean scan on the earlier PR stack. The local static scan and BMS route checks passed on rerun. Local VMMS is unavailable, so live fleet parity could not be repeated here. |
| Step 12: sign-off and archive | The local BMS Compose config and current source pass checks for legacy database references. Written sign-off and the suite login/fleet ticks remain open in the guide and shared scope sheet. The old GitHub repository's archive status is unverified. |

## Hosting and default seeders

- [x] Dockerfile.prod for all six backend processes: Node 24, full-source seed
  target, non-root final runner, compiled entrypoint and production dependencies.
- [x] DB_POOL_MAX defaults to 2; analytics Prisma and report SQL share one pool.
- [x] Bounded database readiness and production HTTPS/non-loopback/SSL validation.
- [x] Projection metadata is migration-owned; runtime DDL and localhost-only
  restriction removed. Saved reports/forecasts use PostgreSQL.
- [x] Analytics build includes prisma generate; its own environment/client key
  replaces the prior backend-root identity override.
- [x] CI and Dependabot templates included in each BMS repo. Backend CI covers
  every subprocess; analytics includes auth/hosting and report tests.
- [x] Production web build, SPA fallback and explicit Maps/tiles/font CSP hosts;
  bundled Leaflet fallback and shared session helper regressions.
- [x] Missing-only catalogs, linked crew defaults, exact untouched legacy-helper
  cleanup migration and production seed guard.
- [x] Full versioned 150-scenario demo orchestration, real fleet/directory
  preflight, owner-only writes, restart/resume, edit preservation and projection.
- [x] BMS hosting handoff records settings, migration/seed jobs, extensions,
  storage and background timers requiring awake staging replicas.

## Delivery gates

- [ ] Shared lead reviews these new hosting changes on the official repository
  development PRs and observes green CI before merging.
- [ ] Lead keeps booking, dispatch and projection awake in staging; provisions
  the per-environment client keys, internal addresses/logins and BMS secrets.
- [ ] BMS group sends provider keys privately; lead configures/restarts apps.
- [ ] Stage runs migrations, baseline seeds and optionally full demo jobs with
  real VMMS available, then validates actual Azure routing and Maps key policy.
- [ ] Shared lead records final scope ticks; BMS group lead confirms in writing.
  The shared checklist still owns those decisions and the old remote archive.

Source changes are confined to BMS applications, BMS Compose and BMS-owned
context/specs. Shared setup tools were used for local runtime configuration,
but other groups' application source and docs/integration were not edited in
this hosting change. Official repositories and Azure were not pushed/deployed.
The separate personal backup preserves the current BMS source and shared
reference context, excluding secrets, dependencies and runtime data.
