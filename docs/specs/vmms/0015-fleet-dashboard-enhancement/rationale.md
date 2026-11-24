# Rationale — 0015 Fleet dashboard enhancement and completion

## Context

The existing VMMS fleet dashboard ([Dashboard.tsx](../../../../welinc-web-vmms/src/pages/Dashboard/Dashboard.tsx), [dashboardService.ts](../../../../welinc-web-vmms/src/lib/api/dashboardService.ts)) provided core KPIs and a basic status/overdue/recent view but mixed current operational state with period-filtered activity, offered limited filters (`All records` / `This month`), had no explicit attention queues (e.g. due soon, awaiting review, anomalies), and performed all aggregation client-side over full schedule/vehicle/garage datasets. VMMS scope marks Feature 7 / FR-23.1 as partial/in-progress and requires reconciliation against implemented behavior.

The user requested enhancement/completion suggestions and proposal implementations, then explicitly approved applying them to the repository.

## Forces

- **Spec-first and VMMS ownership:** VMMS context requires a spec before changing VMMS behavior; changes must stay within VMMS-owned repos/docs and avoid shared services/contracts.
- **Correctness vs available data:** schedule payloads available to the web client do not reliably expose completion timestamps (`completedAt`) needed for exact “completed in period” accounting; costing APIs do expose completion dates but are separate. Mislabeling approximations as exact completion metrics would be misleading.
- **Role and security boundaries:** VMMS uses multi-system role assignments; UI gating must follow VMMS-resolved role helpers. Mechanic scoping in the dashboard is currently client-filtered and must not be presented as sufficient authorization.
- **Existing conventions:** other pages use `MaintenanceStatusBadge`, permissions helpers, and Manila-time formatting in reporting contexts; deep-link query params are not consistently implemented on target pages.
- **Performance:** FR-23.1 targets (`<3s`, real-time accuracy) cannot be credibly closed by client-side aggregation over growing datasets alone.

## Options considered

1. **Frontend-only enhancement (chosen for this slice).** Add model/UI structure, filters, queues, and clearer semantics on top of existing APIs. Fast, no contract/migration risk, but limited by payload fidelity and client aggregation scale.
2. **Backend dashboard aggregate endpoint + frontend redesign.** Best path to correctness/performance (role-aware, server-computed KPIs/queues/periods aligned with costing semantics) but requires API/design work, broader verification, and likely a follow-on spec/contract.
3. **Minimal cosmetic refresh only.** Low risk but would not materially improve operational usefulness or FR-23.1 completeness.

## Decision

Implement **Option 1** now as an approved initial slice: introduce a dashboard view-model, URL-backed filters (including Manila day/month presets), separated current-vs-period sections, attention queues, garage workload, recent activity, and improved states/refresh UX, while explicitly documenting data/role/performance limitations. Treat server aggregation and true completion-period attribution as follow-up work.

## Tradeoffs

- **Gains:** clearer operations picture, actionable queues, better filter/shareability, improved resilience/refresh feedback, and alignment with existing UI/status conventions.
- **Costs/limits:** period activity remains date-based approximation for schedules; client still loads full datasets; mechanic scoping and full audit/SLA evidence remain incomplete.

## Smaller implementation decisions

- Use `canEditWorkOrderPriority` (VMMS-resolved Admin/Ops) for anomaly fetch/panels in this slice.
- Reuse `MaintenanceStatusBadge` for maintenance status display; render simple labels for fuel anomaly statuses where appropriate.
- Use plain route links for queue drill-through (no invented query params).
- Derive “due soon” only from computable future due/reference dates within 7 days, excluding overdue/completed/cancelled/awaiting-review/due-now items as separate concerns.
- Keep `dashboardService` API shape stable; add `dashboardModel.ts` for derivations to isolate logic from rendering.
- Update VMMS scope notes to reflect this enhancement while keeping Feature 7 in-progress pending runtime/perf/audit evidence.
