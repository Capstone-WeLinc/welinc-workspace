# Verification — 0021 Analytics data readiness and evidence-backed AI

The application builds passed. Runtime database, provider, migration
repeatability, and interactive UI acceptance have not been run; implementation
status is not runtime acceptance.

## Migration, sync, and source parity

- [ ] Run migration against an empty analytics store and verify the expected
  DuckDB tables and pgvector structures initialize → AC-1
- [ ] Run migration against a populated store twice; verify existing
  analytics data remains valid and the second run is repeatable → AC-1
- [ ] Sync the same fixed core-VMMS snapshot more than once. Compare vehicle
  and schedule counts, every status, and maintenance-cost aggregate against
  source (exact parity; cost delta less than 0.01) → AC-1, AC-2
- [ ] Interrupt a sync during mart replacement and confirm transaction
  rollback preserves the previously committed snapshot → AC-1, AC-5
- [ ] Run `npm run validate` with configured PostgreSQL, DuckDB, and pgvector;
  confirm source/target parity, orphan-free alerts, exact embedding coverage,
  and all fixed vector fixtures → AC-2, AC-3

## Embeddings and semantic search

- [ ] Confirm every non-deleted schedule and each checklist template with
  eligible text has exactly one embedding, with no missing, extra, or
  duplicate source identities → AC-3
- [ ] Confirm the three synthetic 1536-dimensional pgvector queries return
  their expected fixture document within the top three → AC-3
- [ ] Confirm missing extension/table or invalid index data is reported as a
  validation failure, never as successful zero coverage → AC-3, AC-8
- [ ] Record that this fixture check does not validate natural-language
  relevance over real VMMS records and does not provide user-facing
  semantic retrieval → scope boundary

## Data health and AI evidence

- [ ] Confirm `/analytics/data-health` is available only to Admin/Operations
  and reports current, stale, unavailable, source parity, and semantic-index
  coverage → AC-4, AC-9
- [ ] Verify the UI shows generated/source timestamps and age, exact source
  coverage, and the semantic-index state → AC-4
- [ ] Remove or invalidate the snapshot and confirm the API/UI reports
  unavailable instead of a fresh all-zero report → AC-5
- [ ] Confirm aggregate insight evidence uses snapshot-backed metrics,
  reporting period, snapshot key/timestamp, and limitations; retain
  `aiSummary` compatibility → AC-6
- [ ] With stale or invalid health, confirm new AI generation is blocked and
  any previously generated insight is visibly labeled stale → AC-7
- [ ] Simulate AI provider failure; confirm an explicit error or labeled
  prior insight is shown without blocking the rest of the analytics page
  → AC-8
- [ ] Confirm deterministic analytics reads and page refreshes do not invoke
  the AI provider; the insight read endpoint returns only the saved result
  → AC-6, AC-8
- [ ] Confirm a validated source revision is persisted as a pending job,
  rapid changes replace the pending revision, and generation starts only
  after the 30-second quiet window → AC-10
- [ ] Confirm the read-only status endpoint reports current, queued,
  generating, failed, waiting, and blocked states without exposing provider
  errors or invoking generation → AC-10
- [ ] Restart with a queued and a running job; confirm pending work remains
  durable, a saved matching insight completes the running job, and an
  interrupted job without a saved result is marked failed without a duplicate
  provider call → AC-10
- [ ] Confirm the UI shows saved stale evidence during queued/generating
  states, polls only while queued/generating, and stops after completion or
  failure → AC-10
- [ ] Confirm a validated source revision triggers at most one generation
  attempt, repeated syncs and service restarts for that revision do not retry,
  and a changed revision allows one new attempt → AC-6, AC-8
- [ ] Confirm failed provider attempts do not fail analytics sync and the
  prior insight remains visibly stale until a later source revision succeeds
  → AC-7, AC-8

## Authorization and performance

- [x] Automated HTTP checks confirm Admin/Operations fleet access, Admin-only
  sync, and unchanged assigned-work-order checks → AC-9
- [ ] Record page and representative API latency with runtime, dataset size,
  and results. No pass/fail latency threshold is defined yet → baseline
  only

## Checks run

| Check | Result |
| --- | --- |
| Analytics service `npm run build` | Passed |
| Prisma Client generation and `DONE` enum availability during build | Passed; build pre-hook regenerated the client before TypeScript compilation |
| VMMS web `npm run build` | Passed |
| Analytics validator TypeScript check | Passed |
| Analytics `npm run test:auth` | Passed; all 8 authorization/response-boundary cases |
| Analytics AI revision-cache and queue tests | Passed; source fingerprinting, unchanged revision reuse, changed revision regeneration, failed-attempt deduplication, latest-revision coalescing, interrupted-job recovery, and legacy-attempt migration |
| DuckDB source-revision schema smoke test | Passed; initialization is repeatable and the revision column is writable |
| VMMS AI Analytics focused Vitest | Passed; existing repeated-repair flow, queued-status presentation, and polling through completion |
| ESLint on changed VMMS analytics UI files | Passed |
| Impeccable detector on AI Analytics JSX | Passed; no layout findings |
| `git diff --check` in changed repositories | Passed |
| Database-backed `npm run validate` | Not run; requires configured PostgreSQL, DuckDB, and pgvector data |
| Provider-backed AI acceptance | Not run; requires an authorized provider/runtime environment |
| Interactive UI acceptance | Not completed; the local page redirects to sign-in and the shared sign-in service is unavailable |
| Authorization acceptance | Automated HTTP coverage passed; live deployment acceptance remains pending |

## Acceptance-criteria coverage

| AC | Required evidence |
| --- | --- |
| AC-1–AC-2 | Migration repeatability, atomic sync, and exact source parity |
| AC-3 | 100% embedding source coverage and three fixed pgvector fixtures |
| AC-4–AC-5 | Current/stale/unavailable states and missing-snapshot behavior |
| AC-6–AC-8 | Snapshot-backed evidence, compatibility, stale handling, and provider failures |
| AC-9 | Automated role, sync, and assignment regression checks passed; live deployment acceptance remains pending |
