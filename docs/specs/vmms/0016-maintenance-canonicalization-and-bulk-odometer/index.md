# 0016. Maintenance canonicalization, navigation alignment, and bulk odometer API

**Status**: Implementation complete; runtime/manual verification pending
**Scope**: [Maintenance scheduling and execution](../../../scope/vmms/index.md#4-maintenance-scheduling-and-execution), [Work orders and service history](../../../scope/vmms/index.md#5-work-orders-and-service-history), [Vehicles and master data](../../../scope/vmms/index.md#2-vehicles-and-master-data), [Reports and fleet dashboard](../../../scope/vmms/index.md#7-reports-and-fleet-dashboard)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Deliver a VMMS-only hardening slice that (1) aligns frontend navigation/deep-links to supported front-end search lookup (`search`/`q`) without DB-id URL coupling, (2) reduces schedule/work-order status and due-date divergence by making core VMMS backend responses expose canonical derived due/status fields while preserving workflow-state semantics, and (3) adds a JSON bulk odometer update contract in `welinc-backend-vmms` and wires the Vehicles bulk manual update flow to it. No shared auth, portal, gateway, or cross-system contract changes.

## Sources and decisions

- VMMS scope/features: Feature 4/5 scheduling and work-order execution/status behavior, Feature 2 vehicle/odometer master data, Feature 7 dashboard/navigation context. Related prior specs: [0003-operations-odometer-ownership](../0003-operations-odometer-ownership/index.md), [0004-bulk-odometer-updates](../0004-bulk-odometer-updates/index.md), [0008-maintenance-status-lifecycle](../0008-maintenance-status-lifecycle/index.md), [0015-fleet-dashboard-enhancement](../0015-fleet-dashboard-enhancement/index.md).
- Current implementation evidence: `welinc-web-vmms` notification deep-links and schedule/work-order search prefill; `welinc-backend-vmms` `schedule-due.ts`, `maintenance-overdue.service.ts`, maintenance schedule service/controller, vehicles odometer endpoints; existing odometer import preview/save.
- User-approved direction in this session: "do all" fixes in spec-first order with backend work allowed (VMMS-owned repos only).

Key decisions for this slice:

- **Deep-links/navigation:** use `search`/`q` with front-end lookup values available to the caller (prefer `workOrderNumber ?? title ?? plate`; fall back to schedule id only when no front-end label exists in payload and target page search supports it). Do not introduce DB-id-only navigation params.
- **Canonical due/status exposure:** backend remains source of truth for stored workflow/approval fields and must continue to compute TIME due using `targetDueDate` when present, else derived TIME due from `startReferenceDate + interval` (existing `scheduleDue` behavior). Schedule list/detail API responses should include explicit derived fields needed by clients (at minimum `dueDate`/`targetDueDate`/odometer due markers as applicable and a computed presentation status for derived PENDING/DUE/OVERDUE where the workflow state permits), without mutating protected workflow states (`IN_PROGRESS`, `DONE`, `COMPLETED`, `CANCELLED`) except where existing overdue rules already apply.
- **Frontend consumption:** `welinc-web-vmms` prefers backend canonical/computed fields for display/status derivation and keeps safe fallbacks for compatibility; client-side recalculation remains a defensive fallback, not the primary source of truth when canonical fields are present.
- **Bulk odometer JSON API:** add a VMMS backend endpoint that accepts a JSON batch of per-vehicle odometer updates, validates entries, applies updates through existing vehicle/odometer domain rules, and returns per-item success/error results (partial-success semantics) so current UI can report outcomes; this complements, not replaces, existing file import endpoints.
- **No shared/cross-system changes:** auth, portal, gateway, and non-VMMS repos unchanged.

## Behavior and controls

### 1) Navigation/deep-links
- Notification and in-app maintenance/work-order deep-links navigate to supported routes with `search`/`q` prefill values resolvable by front-end lookup.
- Maintenance Scheduling/Work Orders continue to resolve records by front-end-visible identifiers/fields already supported.

### 2) Canonical status and due dates
- TIME schedules: due date is `targetDueDate` when set; otherwise computed from schedule start/reference + interval per existing backend rules.
- Overdue/derived status: computed consistently with Manila date boundary rules used by backend overdue evaluation for calendar due comparisons; odometer-derived states follow existing mileage/buffer rules. Workflow/approval states are not collapsed incorrectly.
- API responses expose canonical/computed fields so web/mobile clients do not need divergent recomputation for common cases.

### 3) Bulk odometer (JSON)
- Authorized VMMS roles permitted by existing odometer update policy can submit a batch of manual odometer readings.
- Each item is validated (vehicle identity resolvable, odometer numeric/non-negative/not less than current where domain requires, etc. per existing rules).
- Response includes per-item outcome (`success`/`error`, message, updated value/vehicle ref) and aggregate counts.
- Existing single-update and file import flows remain supported.

## API, data, and security impact

- **`welinc-backend-vmms`:** additive/behavioral API response fields for maintenance schedules/work orders as needed; new bulk odometer JSON endpoint and DTO/validation/service logic; possible internal status/due normalization helpers reused. No schema migration expected unless implementation requires persisted derived fields (avoid unless necessary).
- **`welinc-web-vmms`:** navigation/link fixes, schedule/task mapping prefers canonical fields, Vehicles bulk manual save switched to bulk endpoint contract with per-item result handling.
- **`welinc-backend-vmms-analytics-ai`:** no required changes in this slice unless schedule status/due exposure consumed by sync requires alignment (follow-up if discovered).
- **Security:** preserve existing VMMS authz/role checks for schedule and odometer operations; no new public endpoints.

## Acceptance criteria

- **AC1 (navigation):** Maintenance-related in-app deep-links (including notifications) open the correct VMMS page with `search`/`q` prefill and resolve via front-end lookup without requiring unsupported `scheduleId` URL params.
- **AC2 (canonical due/status):** For TIME schedules with `targetDueDate`, backend-derived due date/status and frontend display agree; for computed TIME schedules and odometer schedules, derived PENDING/DUE/OVERDUE presentation aligns with backend rules while workflow states remain intact.
- **AC3 (API consistency):** Schedule/work-order responses include canonical/computed due/status fields sufficient for clients to avoid divergent TIME-due interpretation in common cases.
- **AC4 (bulk odometer):** Bulk manual vehicle odometer submission via JSON endpoint updates valid entries, rejects invalid entries with per-item errors, and returns aggregate/per-item results; existing single and import odometer flows continue to work.
- **AC5 (frontend wiring):** Vehicles bulk manual update uses the bulk endpoint and reports partial successes/failures clearly.
- **AC6 (verification):** Relevant builds/tests pass for touched repos; spec verify records evidence and remaining runtime/integration checks.

## Affected repositories

- `docs/specs/vmms/0016-maintenance-canonicalization-and-bulk-odometer/` (this spec)
- `welinc-web-vmms`
- `welinc-backend-vmms`
- `docs/scope/vmms/index.md` (reconciliation if feature/status/evidence changes)

## Verification plan / implementation status

- Implemented/planned in slices: spec (this change), navigation audit/fix, backend canonicalization + tests, frontend mapping/wiring, bulk endpoint + tests + UI wiring, final verification/docs reconciliation.
- Pending at spec creation: runtime/integration evidence, full regression across roles and schedule trigger types, and any analytics-sync follow-up discovered during implementation.
