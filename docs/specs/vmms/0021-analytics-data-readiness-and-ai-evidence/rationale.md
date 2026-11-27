# Rationale — 0021 Analytics data readiness and evidence-backed AI

## Context

VMMS scope records the analytics service as in progress. DuckDB migration and
validation code exists, while source consistency and runtime evidence remain
outstanding. The analytics service generates pgvector embeddings, but the
inspected VMMS API and analytics service do not expose a vector-retrieval
consumer; the existing schedule search is text-based.

Responses already carry generated time, source update time, age, and stale
status, but the web page does not provide a consistent data-health summary.
Aggregate AI insights are returned as an `aiSummary` string without a
structured set of source metrics and limitations. The analytics service can
also synthesize a fresh-looking zero snapshot when no snapshot row exists.

This implementation builds on the approved Admin/Operations analytics policy
in spec 0001 and does not change it.

## Forces

- Core VMMS is authoritative for operational vehicles, schedules, and
  maintenance state; analytics is derived.
- A successful migration does not prove that the derived snapshot matches
  source records or that eligible embedding records are covered.
- Users need to distinguish current, stale, unavailable, and valid empty
  data.
- AI output should be traceable to a defined reporting snapshot and its
  source metrics, not presented as an unsupported fact or operational
  decision.
- Existing `aiSummary` callers and assigned-work-order policies must remain
  compatible.
- There is no agreed page or endpoint performance target or target runtime.

## Options considered

1. **Runtime verification only.** Closes the immediate deployment and
   consistency gap but leaves users unable to see freshness and evidence.
2. **Data-health UI only.** Improves visibility but can make an inconsistent
   mart look acceptable without source-parity evidence.
3. **Runtime validation, visible health, and evidence-backed AI.** Closes
   operational readiness first, then exposes trustworthy state and
   provenance to users while keeping predictive scope bounded.

## Settled decisions

- Source vehicle/schedule counts and every schedule-status total require
  exact parity. The aggregate maintenance-cost tolerance is less than 0.01
  to accommodate numeric representation.
- Eligible embedding coverage must be exactly 100%. Eligibility follows
  current migration behavior: every non-deleted schedule and each checklist
  template with non-empty type or item text.
- The validator runs three fixed synthetic 1536-dimensional pgvector
  retrieval queries. Every expected fixture must appear within the top three
  results. This validates the vector-ranking operator, not natural-language
  relevance over real maintenance records.
- No public semantic-search endpoint or UI is added in this slice. An actual
  user-facing semantic retrieval feature requires separate product scope.
- Record a performance baseline with environment and dataset size. Do not
  make it a release gate until an owner sets the target environment and
  threshold.
- A previously generated insight may remain visible with an explicit stale
  label. Block new generation on stale, missing, invalid, or source-to-mart
  invalid data.
- Deterministic analytics endpoints and page refreshes must not invoke the AI
  provider. After a validated sync, the optional AI narrative is generated
  only when its stable source revision changes. The revision fingerprints
  every active vehicle and maintenance-schedule identity with its update
  timestamp, rather than relying only on the latest timestamp. Saved insights
  and attempted revisions persist in DuckDB across service restarts. A
  provider failure does not fail sync and is not retried for the same
  revision. A durable latest-revision job coalesces changes behind a
  30-second quiet window; the read-only status endpoint and UI communicate
  queued, generating, completed, failed, waiting, and blocked states without
  triggering generation.
- On restart, a job left running is marked completed if its matching insight
  was saved; otherwise it is marked failed. This avoids repeating a provider
  request whose outcome may be uncertain.

## Tradeoffs

- **Benefits:** safer refreshes, explicit parity and embedding coverage,
  visible freshness, and AI evidence values derived from the reporting
  snapshot.
- **Costs:** analytics API and web changes, repeatable fixture data, and
  runtime validation against configured databases.
- **Compatibility:** retaining `aiSummary` avoids requiring every existing
  caller to migrate immediately; new UI behavior consumes additive evidence.
- **Operational impact:** blocking new AI generation for stale or invalid
  data may reduce availability when sync is delayed, but avoids presenting
  stale analysis as current.
- **AI cost control:** the read endpoint returns the saved narrative without
  provider calls. Successful and failed generation attempts are revision-
  keyed, and rapid source changes coalesce before generation. Page navigation,
  repeated reads, unchanged scheduled syncs, and service restarts do not
  repeat a provider call for the same revision.
- **Queue tradeoff:** a single DuckDB job is sufficient because only the
  latest analytics revision matters. It intentionally serializes generation;
  no external queue service or automatic retry policy is introduced.
- **Validation limitation:** synthetic vector fixtures prove deterministic
  pgvector ranking behavior only. They do not prove semantic relevance for
  the live corpus or add a search consumer.
- **Performance limitation:** measurement is recorded as baseline evidence
  only until the target dataset and environment are agreed.

## Excluded

- A public semantic-search API or UI, advanced mechanical-failure
  prediction, telemetry/GPS, supplier automation, income/profit analytics,
  automated operational writes, a new AI provider, changes to role access,
  and changes to shared services.
