# 0015. Fleet dashboard enhancement and completion

**Status**: Implemented (initial slice; runtime/performance evidence pending)
**Scope**: [Reports and fleet dashboard](../../../scope/vmms/index.md#7-reports-and-fleet-dashboard)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Enhance the VMMS web fleet dashboard (`/dashboard`) to provide a clearer operations overview: current fleet state versus period activity, URL-backed filters, attention queues, and role-aware panels, without changing shared services or cross-system contracts. This slice improves FR-23.1 usability/completeness on the frontend but does not by itself prove the `<3s` load or real-time accuracy targets.

## Sources and decisions

- VMMS scope: [Feature 7 — Reports and fleet dashboard](../../../scope/vmms/index.md#7-reports-and-fleet-dashboard), BR-23/FR-23.* (dashboard/KPIs/refresh); related costing/reporting context in FR-20.3/21.4/25/26 remains separate.
- Current implementation: `welinc-web-vmms/src/pages/Dashboard/Dashboard.tsx`, `welinc-web-vmms/src/lib/api/dashboardService.ts`.
- User-approved implementation direction in this session: apply a frontend enhancement/completion slice with spec-first documentation; no shared auth/portal/gateway changes.

Key recorded decisions/constraints for this slice:

- **No cross-system/shared changes.** Data remains sourced from existing VMMS web APIs/services (`getMaintenanceSchedules`, `getVehicles`, `getGarages`, `getFuelAnomalies`); no schema or gateway contract changes.
- **Current state vs period activity are separated in UI semantics.** Current operational cards/queues are scoped to visible entities and live statuses; period controls affect period-activity metrics derived from available work-order date fields (`date`/`startReferenceDate`) and must be labeled as date-based where exact completion timestamps are unavailable.
- **No false deep-link claims.** Queue actions link to existing routes only; no unsupported query-param pre-filtering is introduced.
- **Role handling follows VMMS helpers.** Admin/Ops-only panels (open fuel anomalies, sensitive ops views) use VMMS-resolved role helpers (`canEditWorkOrderPriority` / existing permissions utilities) rather than raw role string checks.
- **Mechanic scope remains best-effort client-side in this slice** (matching assigned mechanic identifiers/email/name as available) and must be enforced server-side in follow-up work.
- **Accurate period completion/cost attribution may require backend support.** Schedule payloads in web normalization do not currently expose a guaranteed `completedAt`; this slice does not claim true completion-timestamp accounting.
- **FR-23.1 performance/SLA not claimed complete.** 30s/focus refresh and manual refresh remain; load-time and real-time correctness evidence is pending.

## Behavior and controls

- **Filters:** `All records`, `Today (Manila)`, `This month (Manila)`, and `Custom range` (date inputs). Filter state is reflected in URL search params for share/restore (`range`, `from`, `to`). Invalid/partial custom ranges fall back safely to all-records behavior for period metrics.
- **Current operational section (entity/scope-bound, not period-bound):** total vehicles, vehicles under maintenance, active work orders, due, overdue, open fuel anomalies (Admin/Ops only), and related operational queues.
- **Period activity section (date-bounded, by recorded work-order date):** counts/cost for work orders whose recorded date (`date` or `startReferenceDate`) falls in the selected period, including completed-status items in that period; labels/subtitles indicate date-based attribution.
- **Attention queues:** overdue maintenance, due maintenance, due soon (next 7 days, when computable from due/target/start/reference dates and not already overdue/completed/cancelled/awaiting review), awaiting review (`DONE`), and open fuel anomalies (Admin/Ops). Rows link to supported pages.
- **Status breakdown:** distribution of visible work orders by maintenance status (excluding cancelled in summary visualization consistent with prior dashboard intent).
- **Garage workload / recent work orders:** active workload grouped by garage and latest visible work orders by recorded date.
- **States:** loading, error with retry, and empty states per panel/queue. Manual refresh and periodic/focus refresh preserve last successful data on transient refresh failure where possible and show last-updated time.
- **Access/visibility:** dashboard remains within existing VMMS web navigation/route access; anomaly panels and anomaly fetch are limited to Admin/Ops. Mechanic users see only scoped work where client filtering applies.

## API, data, and security impact

- **API/data:** no backend or database changes in this slice. Frontend continues using existing VMMS endpoints through `vmmsApi`/`fuelService`/`dashboardService`.
- **Security:** no auth/session changes. Role checks are client-side UI gating aligned to VMMS role helpers; server-side authorization and mechanic scoping remain authoritative and are required for complete enforcement.
- **Migration:** none.

## Acceptance criteria

- **AC1 (filters):** User can switch between All/Today (Manila)/This month (Manila)/Custom range; URL updates and restores the selected filter; invalid custom range does not break the dashboard.
- **AC2 (current vs period):** Dashboard visibly distinguishes current operational metrics/queues from period-activity metrics; period metrics state they are based on recorded work-order dates when exact completion timestamps are unavailable.
- **AC3 (queues):** Overdue, due, due-soon (computable cases), awaiting-review, and open-fuel-anomaly (Admin/Ops) queues render with empty states and navigation to supported pages.
- **AC4 (operational insight):** Status breakdown, garage workload, and recent work orders reflect the same scoped dataset shown to the user.
- **AC5 (refresh/resilience):** Manual and background refresh update data; last-updated time is shown; refresh failure surfaces a recoverable error without discarding last good data unnecessarily.
- **AC6 (role awareness):** Admin/Ops-only anomaly data/panels are not shown/fetched for unauthorized roles; mechanic view remains scoped to assigned work in client logic.

## Affected repositories

- `welinc-web-vmms` (dashboard page/model/service)
- `docs/specs/vmms/0015-fleet-dashboard-enhancement/` (this spec)
- `docs/scope/vmms/index.md` (reconciliation note/status context for Feature 7)

## Verification plan / implementation status

- **Implemented in code (this change):** AC1–AC6 frontend slice in `welinc-web-vmms` dashboard files.
- **Pending runtime verification:** browser/manual validation of filters, queues, role views, empty/error states, and refresh behavior in an integrated environment.
- **Pending performance/accuracy evidence:** FR-23.1 `<3s` load and real-time accuracy remain unproven; a server-side dashboard aggregate may be required for full completion.
- **Follow-ups:** backend aggregate contract, true completion-date/cost period attribution, server-enforced mechanic scoping, deep-link filters on target pages, and audit/access evidence per FR-26.5/SC requirements as applicable.
