# Verification — 0021 Analytics data readiness and evidence-backed AI

All checks are pending approval and implementation. They are derived from
the acceptance criteria in [index.md](index.md).

## Migration, sync, and source parity

- [ ] Run migrations against an empty analytics store and verify the
  expected DuckDB tables and pgvector structures are initialized → AC-1
- [ ] Run migrations against a populated store twice; verify existing
  analytics data remains valid and the second run is repeatable → AC-1
- [ ] Sync the same fixed core-VMMS snapshot more than once and compare
  vehicle/schedule counts, key statuses, and report aggregates against the
  agreed source result and tolerance → AC-2
- [ ] Interrupt or fail a migration/sync/validation run and confirm no
  partial snapshot is reported as current → AC-1, AC-5, AC-8

## Embeddings and semantic search

- [ ] Compare eligible source records with indexed records and report
  coverage using the approved minimum → AC-3
- [ ] Run the approved fixed query set and confirm expected relevant records
  appear within the agreed relevance criteria → AC-3
- [ ] Verify missing or invalid vector data produces an explicit validation
  failure, not a successful coverage result → AC-3, AC-8

## Data health and AI evidence

- [ ] Verify the page distinguishes current, stale, unavailable, and valid
  empty data, showing generated time, source update time, and age → AC-4,
  AC-5
- [ ] Remove or invalidate the snapshot and confirm the API/UI reports
  unavailable rather than generated-at-now zero values → AC-5
- [ ] Verify each aggregate AI insight's period, snapshot, metric references,
  and limitations resolve to the underlying snapshot → AC-6
- [ ] Confirm `aiSummary` remains available to existing callers while the
  page renders additive evidence → AC-6
- [ ] With stale data, verify the existing insight is labeled stale and new
  generation is blocked; with missing/invalid data, verify no insight is
  generated → AC-7
- [ ] Simulate AI provider error, quota response, and malformed structured
  output; verify explicit failure behavior and no invented metrics or writes
  → AC-8

## Authorization and performance

- [ ] Confirm Admin and Operations retain fleet read access, sync remains
  Admin-only, and assigned-work-order checks remain unchanged → AC-9
- [ ] Measure page and representative API latency under the agreed runtime
  dataset; record environment, dataset size, and results against the approved
  target → approval decision 4

## Acceptance-criteria coverage

| AC | Planned evidence |
| --- | --- |
| AC-1–AC-2 | Migration repeatability, sync behavior, and source parity |
| AC-3 | Embedding coverage and semantic-search query results |
| AC-4–AC-5 | Fresh/stale/unavailable/empty states and missing-snapshot behavior |
| AC-6–AC-8 | Insight evidence, compatibility, stale handling, and failures |
| AC-9 | Role and assignment regression checks |

## Implementation evidence

No implementation or runtime verification has been performed for this
proposal.
