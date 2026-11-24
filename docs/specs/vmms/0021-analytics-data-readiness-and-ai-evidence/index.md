# 0021. Analytics data readiness and evidence-backed AI

**Status**: Draft for approval; implementation is not authorized
**Scope**: [Analytics, mobile synchronization, and release readiness](../../../scope/vmms/index.md#8-analytics-mobile-synchronization-and-release-readiness)

Decision history: [rationale.md](rationale.md). Verification plan: [verify.md](verify.md).

## Summary

Complete VMMS analytics runtime readiness and improve the trustworthiness of
AI-generated fleet insights. Validate the DuckDB reporting mart and pgvector
semantic-search index against core VMMS sources, make data freshness and
coverage visible, and attach source metrics and limitations to AI insights.
Analytics remains a derived, read-only view rather than an operational source
of truth.

## Source requirements and related decisions

- VMMS cross-cutting FR-27.8: semantic maintenance search and embeddings.
- VMMS cross-cutting FR-27.9: contextual work-order advisory and
  recommendations.
- VMMS cross-cutting FR-27.11: generated time, source update time, data age,
  and stale status.
- VMMS cross-cutting FR-27.12: data-mart migrations and validation.
- VMMS success criteria SC-16 and SC-17.
- Preserve the approved Admin/Operations access and API fleet-role guard in
  [spec 0001](../0001-ai-analytics-admin-access/index.md).
- Predictive maintenance remains bounded by
  [spec 0013](../0013-predictive-maintenance-readiness/index.md) and the VMMS
  non-goals; this proposal does not add advanced mechanical-failure
  prediction or telemetry.

## Proposed behavior

### Runtime data readiness

- Run the existing DuckDB migrations and validators against both a clean
  analytics store and an already-populated store. Repeated migration and sync
  runs must be safe and must not silently lose valid data.
- Compare a fixed core-VMMS source snapshot with the derived mart for agreed
  vehicle and schedule counts, key statuses, and report aggregates. Record
  the comparison inputs, results, and any approved tolerance.
- Verify semantic embedding coverage for eligible source records and run a
  repeatable set of semantic-search queries whose relevant results are known.
- Do not publish a partial or failed refresh as a current, validated
  snapshot.

### Data health and freshness

- Show Admin and Operations a concise Analytics data-health state: current,
  stale, or unavailable; generated time; source update time; and data age.
- Reuse existing source metadata and the configured stale threshold rather
  than introducing a second freshness rule.
- Include safe source-coverage and semantic-index validation summaries. Do
  not expose raw stack traces, secrets, or provider credentials in the UI.
- Treat a missing snapshot, invalid timestamp, or failed validation as
  unavailable. Do not present synthetic zero-valued data as a fresh,
  successful result.
- Keep health display read-only. Manual sync remains Admin-only under the
  existing API policy.

### Evidence-backed AI insights

- Add a backward-compatible, structured evidence object to aggregate AI
  insights while retaining the existing `aiSummary` field for callers.
- Each displayed insight must identify its reporting period and analytics
  snapshot, cite the supporting metric labels and values, and state material
  limitations. Validate cited metrics against the snapshot before display.
- Mark insights based on stale data as stale. Do not generate or refresh
  insights from a missing, invalid, or failed snapshot.
- Keep insights advisory. Do not create or update work orders, maintenance
  schedules, alerts, or operational records from generated content.
- Preserve the current response shape for work-order advisory endpoints and
  their assignment checks; those endpoints are not part of this response
  change unless approval identifies a required compatibility update.

## Approval requested

1. Approve the runtime migration, sync, source-parity, and embedding
   validation work as a prerequisite to further predictive features.
2. Approve a read-only data-health summary for Admin and Operations, reusing
   the existing stale threshold and metadata.
3. Approve a backward-compatible evidence object for aggregate AI insights
   while retaining `aiSummary`.
4. Confirm acceptance thresholds for source/target reconciliation,
   embedding coverage/search quality, stale-data handling, and measured page
   or endpoint performance before implementation begins.
5. Confirm that stale insights may remain visible with an explicit stale
   label, while refresh/generation is blocked until a valid fresh snapshot is
   available.

## API, data, and migration impact

- Analytics remains a derived read model over core VMMS data. Core VMMS
  records remain authoritative.
- Reuse existing `generatedAt`, `sourceMaxUpdatedAt`, age, and stale
  metadata. An additive aggregate-insight response field may be needed; keep
  `aiSummary` available to existing callers.
- Migration and validation changes are limited to the analytics DuckDB and
  pgvector data. No core VMMS schema change is proposed.
- No shared auth, portal, gateway, mobile, or cross-system API change is
  included.

## Security and failure behavior

- Preserve Admin/Operations access to fleet analytics and the server-side
  fleet-role guard from spec 0001. Keep sync Admin-only and preserve
  assignment-scoped work-order access.
- Do not treat analytics as authoritative for authorization, assignment, or
  current operational state.
- On migration, sync, validation, or provider failure, surface an explicit
  unavailable/error state. Never turn failure into a fresh zero report or
  unsupported AI claim.
- Keep generated insights advisory and validate every referenced value
  against the reporting snapshot.

## Affected repositories

- `welinc-backend-vmms-analytics-ai`: runtime migration/sync validation,
  embedding coverage checks, data-health metadata, and the additive insight
  evidence response.
- `welinc-web-vmms`: visible data-health state and evidence/limitations for
  aggregate AI insights.
- `docs/scope/vmms` and `docs/specs/vmms`: acceptance traceability and
  implementation/verification evidence.

## Acceptance criteria

1. Migrations are repeatable on clean and populated analytics stores, and
   failures do not publish partial data as a current validated snapshot.
2. For an agreed fixed source snapshot, vehicle/schedule counts, key status
   totals, and report aggregates reconcile within approved tolerances.
3. Embedding coverage and a repeatable semantic-search query set are
   validated against an agreed eligible-record set and expected results.
4. Admin and Operations can distinguish current, stale, and unavailable
   analytics and can see the snapshot/source times and age.
5. Missing or invalid snapshots and failed validation never appear as a fresh
   all-zero report.
6. Aggregate AI insights retain the `aiSummary` field and include a validated
   reporting period, snapshot, supporting metrics, and limitations.
7. Stale insights are visibly marked, and new AI generation is blocked when
   the snapshot is stale, missing, invalid, or failed.
8. AI/provider failures are explicit and never result in invented metrics or
   operational writes.
9. Existing Admin/Operations fleet access, Admin-only sync, and
   assignment-scoped work-order policies remain unchanged.

## Verification plan and status

Planned evidence is listed in [verify.md](verify.md). No implementation or
runtime acceptance is claimed by this draft.
