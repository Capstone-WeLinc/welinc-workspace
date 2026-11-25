# Rationale — 0021 Analytics data readiness and evidence-backed AI

## Context

VMMS scope records the analytics service as in progress. Semantic search and
embeddings exist, but runtime coverage and vector validation are not recorded.
DuckDB migration and validation code exists, while source consistency and
runtime evidence remain outstanding. Responses already carry generated time,
source update time, age, and stale status, but the web page does not provide a
consistent data-health summary.

Aggregate AI insights are currently returned as an `aiSummary` string. The
page renders that text without a structured set of source metrics and
limitations alongside it. In addition, the analytics service can synthesize
an empty snapshot with zero values when no snapshot row exists, which can
appear like valid current data unless missing-source behavior is explicit.

This proposal builds on the approved Admin/Operations analytics policy in
spec 0001 and does not change it.

## Forces

- Core VMMS is authoritative for operational vehicles, schedules, and
  maintenance state; analytics is derived.
- A successful migration does not prove that the derived snapshot matches
  source records or that semantic search has usable coverage.
- Users need to distinguish current, stale, unavailable, and empty data.
- AI output should be traceable to a defined reporting snapshot and existing
  metrics, not presented as an unsupported fact or operational decision.
- Existing `aiSummary` callers and assigned-work-order policies must remain
  compatible.
- The project has not specified numeric thresholds for reconciliation,
  embedding quality, or response performance.

## Options considered

1. **Runtime verification only.** Closes the immediate deployment and
   consistency gap but leaves users unable to see freshness and evidence in
   the page.
2. **Data-health UI only.** Improves visibility but can make a broken or
   inconsistent mart look acceptable without source-parity and embedding
   evidence.
3. **Runtime validation, visible health, and evidence-backed AI (recommended).**
   Closes operational readiness first, then exposes trustworthy state and
   provenance to users. Keeps predictive scope bounded.

## Proposed decision

Approve Option 3 as a draft implementation slice:

- Validate migrations, repeatable sync, source-to-mart reconciliation, and
  embedding/search quality on fixed, reproducible data.
- Reuse the service's existing freshness metadata and show current, stale, or
  unavailable status to Admin and Operations.
- Reject missing/invalid snapshots as unavailable rather than generating
  fresh-looking zero values.
- Add an additive, schema-validated evidence object to aggregate AI
  responses while retaining `aiSummary`.
- Mark stale insights and block new AI generation until a valid fresh
  snapshot is available.

Do not begin implementation until approval resolves measurement thresholds
and stale-insight display behavior.

## Tradeoffs

- **Benefits:** better confidence in analytics correctness, visible data
  freshness, repeatable embedding checks, and AI statements that can be
  checked against source metrics.
- **Costs:** analytics API and web changes, repeatable fixture data, and
  ongoing validation of a structured AI response.
- **Compatibility:** retaining `aiSummary` avoids requiring every existing
  caller to migrate immediately; new UI behavior consumes the additive
  evidence fields.
- **Operational impact:** blocking new AI generation for stale data may
  reduce availability when sync is delayed, but avoids presenting stale
  analysis as current.

## Decisions awaiting approval

- Reconciliation tolerances and the record set used for parity evidence.
- Minimum acceptable embedding coverage and semantic-search relevance
  criteria.
- Page/endpoint performance targets and the required measurement environment.
- Whether stale insights may remain visible with a stale label while refresh
  is blocked; this proposal recommends that behavior.

## Excluded

- Advanced mechanical-failure prediction, telemetry/GPS, supplier automation,
  income/profit analytics, automated operational writes, a new AI provider,
  changes to role access, and changes to shared services.
