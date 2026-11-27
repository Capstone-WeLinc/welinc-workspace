# VMMS scope

**Source:** VMMS Business Requirements Document and Requirements Traceability Matrix supplied by the project owner.

**Status note:** Every functional requirement row in the RTM is marked `Not Executed`. The feature statuses below are provisional project tracking states, not claims that the code is absent or complete. Reconcile implementation and acceptance evidence before changing them.

The RTM summary reports 102 requirements. Its body contains 102 requirements across Modules 1 to 7 plus 15 Cross-Cutting requirements, for 117 rows total. Confirm whether the summary intentionally excludes Cross-Cutting requirements or needs correction before reporting an overall execution percentage.

## Scope boundaries and source conflicts

- The BRD assigns account creation and role assignment to VMMS Admin. The suite architecture places account ownership in `welinc-auth`. VMMS scope covers consuming authenticated identities, VMMS roles, and session state; account CRUD remains in the shared auth and portal services.
- BRD assumption A-03 describes VRMS and BMS reading VMMS-owned vehicle tables through foreign keys. The suite architecture prohibits cross-system database reads. VMMS remains the source of fleet data, and other systems consume it through documented APIs.
- BRD assumption A-14 says VMMS may reference VRMS repair costs read-only. Keep repair-ticket and repair-cost ownership in VRMS; any integration must use its API and a spec.
- **Resolved (2026-11-25):** Admin and Operations may access the VMMS AI/Analytics page and fleet analytics read endpoints, aligning FR-27.10 with the BRD role descriptions for Operations fleet dashboards and reports. Preserve the API's Admin/Operations fleet-role guard. Manual analytics sync remains Admin-only, and existing assigned-work-order policies remain unchanged. See [spec 0001](../../specs/vmms/0001-ai-analytics-admin-access/index.md).
- Explicit non-goals include GPS/telemetry, advanced mechanical-failure prediction, supplier/shop automation, vendor price estimation, payroll/HR, income or profit calculations, and VRMS repair-ticket administration or duplicate repair storage. The VMMS-owned referral, status, and history integration is a scope extension; VRMS `UNDER_REPAIR` status takes precedence over VMMS maintenance status.
- Proposed VMMS-owned BMS handoffs—Operations-reviewed trip odometer evidence, policy-driven utilization suggestions, and Operations-approved fuel purchases—are specified in [spec 0031](../../specs/vmms/0031-bms-vmms-operational-handoffs/index.md). Partner contract review and explicit implementation authorization remain pending.

| # | Feature | Phase | Status |
|---:|---|---|---|
| 1 | Login, roles, and session controls | Foundation | in-progress |
| 2 | Vehicles, garages, and fleet records | Foundation | in-progress |
| 3 | Maintenance scheduling and alerts | Maintenance workflow | in-progress |
| 4 | Work orders, checklists, and maintenance history | Maintenance workflow | in-progress |
| 5 | Fuel expenses and anomaly handling | Cost and reporting | done |
| 6 | Maintenance costing | Cost and reporting | in-progress |
| 7 | Reports and fleet dashboard | Cost and reporting | in-progress |
| 8 | Analytics, mobile synchronization, and release readiness | Cross-cutting | in-progress |

## Foundation

### 1. Login, roles, and session controls

Secure sign-in and session handling for four roles, with web access for Admin and Operations and mobile access for Chief Mechanic and Mechanic.

Done when: account protection, role restrictions, role-appropriate routing, session behavior, account changes, and login audit requirements are reconciled against the implementation and their acceptance criteria.

Requirements: BR-01 to BR-03; FR-01.* to FR-03.*; SC-01, SC-02, SC-16.

- [x] Reconcile the 14 Module 1 RTM rows with current auth, web, and mobile behavior.

  Reconciliation evidence as of 2026-11-19:
  - Confirmed: VMMS has exactly four allowed role assignments (`ADMIN`, `OPERATIONS`, `CHIEF_MECHANIC`, `MECHANIC`) in the core backend.
  - Confirmed: the VMMS web app uses shared SSO-backed session start, refresh, status polling and logout routes; non-`ADMIN`/`OPERATIONS` accounts are blocked from web routes.
  - Confirmed: the mobile app uses `vmms-mobile` login, email verification, refresh rotation, session restoration and logout through the shared auth service.
  - Confirmed: mobile login is role-limited to Mechanic and Chief Mechanic behavior, while Operations and Admin are routed to the web app.
  - Confirmed: account creation, role assignment, account deactivation, account deletion and login audit ownership remain in `welinc-auth` and the portal. VMMS has no duplicate account store or account CRUD implementation.
  - FR-01.1: Shared portal/auth validates active-account credentials; VMMS web starts the shared SSO flow and VMMS mobile uses the shared mobile login. End-to-end credential acceptance remains unexecuted.
  - FR-01.2–01.5: Generic failed-login messaging, five-attempt lockout, Admin unlock, and account-name validation are shared auth/portal responsibilities; no duplicate VMMS implementation. Verify these in the owning shared services.
  - FR-02.1: VMMS accepts only its four defined roles; account assignment itself is owned by shared auth.
  - FR-02.2: VMMS web routes admit Admin and Operations; the mobile flow is for Mechanic and Chief Mechanic, with Admin/Operations sent to web.
  - FR-02.3: Web session refresh hydrates the in-memory auth store and role-based navigation immediately; mobile role state is applied at login. Runtime acceptance remains unexecuted.
  - FR-02.4: The shared web login returns users to their requested VMMS address, and the VMMS root/fallback routes to `/dashboard`; mobile routes users by role. A distinct role-specific web dashboard is not evidenced.
  - FR-02.5: Deactivation is owned by shared auth. VMMS consumes shared session status and ends a revoked session at its next check; immediate cross-platform cutoff timing needs integration verification.
  - FR-02.6: VMMS web now pings activity only on trusted input (at most once per minute), checks the server cutoff, warns before idle or 12-hour max-age expiry, offers stay/keep-working and logout actions, and broadcasts refresh/activity/end events to same-origin tabs. It uses existing VMMS session routes; session authority remains `welinc-auth`.
  - FR-03.1–03.3: Login-event audit and Admin account/activity screens are shared auth/portal responsibilities. VMMS links to portal account management and reads the shared activity feed; verify audit timing, fields, and immediate account-change propagation in integration acceptance.
  - All 14 RTM execution statuses remain **Not Executed**; this checkbox records code/ownership reconciliation only, not acceptance completion. Feature status remains **in progress** pending shared-service and end-to-end verification.

### 2. Vehicles, garages, and fleet records

Maintain vehicle records, odometer and status data, branch, and the fleet reference data used by other modules.

Done when: vehicle lifecycle, role permissions, import, odometer handling, and cross-system vehicle status rules meet the BRD acceptance criteria.

Requirements: BR-04 to BR-06; FR-04.* to FR-06.*; SC-03, SC-04.

- [x] Reconcile the 12 Module 2 RTM rows with the core API, web, and VMMS mobile flows.

  Reconciliation evidence as of 2026-11-22:
  - FR-04.1: Implemented for required Plate Number, Make, Model, Garage Branch and Odometer Baseline; valid records start at `AVAILABLE`. The vehicle form and API also require year, engine type and truck size/category.
  - FR-04.2: Implemented. Plate numbers are unique in the database and imports and create/update paths return duplicate-plate errors.
  - FR-04.3: Implemented in the API. Vehicle updates run in a transaction and write previous/new values, actor identity and timestamp for changed fields.
  - FR-04.4: Implemented. Vehicle delete is a soft delete with `isActive=false`; active-vehicle API queries exclude archived records and the web/mobile read filtering prevents active dropdown use. The original BRD/RTM execution status remains `Not Executed`.
  - FR-05.1: Single-vehicle and bulk master-odometer updates are implemented in backend and Operations web, with per-vehicle audit and schedule refresh in [spec 0004](../../specs/vmms/0004-bulk-odometer-updates/index.md); runtime acceptance pending. [Spec 0016](../../specs/vmms/0016-maintenance-canonicalization-and-bulk-odometer/index.md) adds a JSON bulk odometer API and wires the Vehicles bulk manual flow to it with partial-success results. Operations owns all writes to the vehicle master odometer through the dedicated Vehicles action, including readings originating from work orders. Generic vehicle edits, mechanic work-order submission, and schedule completion do not update the master; work-order readings remain evidence. Vehicle creation/import may establish the initial baseline. This user decision overrides the RTM's Mechanic/mobile actor; reconcile the RTM before acceptance.
  - FR-05.2: Implemented. Prisma and API DTO validation restrict status to `AVAILABLE`, `UNDER_MAINTENANCE`, or `UNDER_REPAIR`; no custom status is accepted.
  - FR-05.3: Implemented. VMMS uses `UPDATE ... status != UNDER_REPAIR`, so an existing or concurrently changed repair status cannot be overwritten.
  - VMMS vehicle availability integration is documented in [spec 0024](../../specs/vmms/0024-vmms-repair-handoff-and-availability/index.md). VMMS remains the status writer; BMS event receipt and shared auth grants are proposed external contracts in [spec 0026](../../specs/vmms/0026-vmms-vrms-repair-referrals-and-bms-availability/index.md).
  - Flow A VMMS slice: serve BMS fleet/availability reads and publish durable vehicle/garage master-data invalidations. VMMS implementation and BMS integration remain in progress under [spec 0024](../../specs/vmms/0024-vmms-repair-handoff-and-availability/index.md).
  - FR-06.1: Implemented for maintenance schedules. Outsourced providers are Operations-managed, active provider names are the only accepted outsourced value, and Admin has view-only access. Per [spec 0013](../../specs/vmms/0013-outsourced-provider-lifecycle/index.md), unreferenced providers can be renamed or deleted; referenced providers retain their name and may only be activated or deactivated.
  - FR-06.2: Removed from VMMS scope by user decision (2026-11-26). Do not add the Online/Corporate account classification or an Operations-managed account-type catalog. The existing maintenance-schedule `IN_HOUSE`/`OUTSOURCED` field remains unchanged.
  - FR-06.3: Implemented. A vehicle's registered Garage assignment represents its branch; seeded Garage records include Marikina, Sta. Rosa and Pulilan. No separate vehicle-branch field is needed.
  - FR-06.4: Implemented. The vehicle list has a default Garage Branch column, branch filter and ascending/descending branch sort.
  - FR-06.5: Implemented. `.xlsx` preview validates all rows, duplicate plates and active garage names, then saves valid rows and returns row-specific errors for invalid rows; the limit is 1,000 rows.
  - Mobile: implemented as an offline vehicle snapshot source, but the local vehicle model omits garage branch and web-only make/year/engine/truck-size fields.
  - Acceptance evidence: unit coverage exists for vehicle audit, import, active garages and repair precedence, but runtime browser/mobile and cross-system acceptance have not been recorded. Feature status remains **in progress**.

## Maintenance workflow

### 3. Maintenance scheduling and alerts

Create and monitor schedules using odometer, time, and dual triggers, with due and overdue states, calendar dates, rescheduling, cancellation, and escalation.

Done when: the whichever-comes-first rule, due-date and odometer alerts, status colors and legends, staged notifications, and cancellation audit trail meet their acceptance criteria.

Requirements: BR-07 to BR-11; FR-07.* to FR-11.*; SC-05 to SC-07, SC-18, SC-19, SC-21, SC-23.

- [x] Reconcile the 25 Module 3 RTM rows with the scheduler, notification flows, and web and mobile views.

  Reconciliation evidence as of 2026-11-22:
  - FR-07.1–07.3: Partial. The API models odometer, time and dual triggers and computes due date/odometer states. Existing eligible odometer schedule statuses refresh transactionally when the master reading changes; analytics and mobile consume those persisted statuses through existing refresh/snapshot paths. Schedule creation remains Operations-managed: threshold crossings update existing schedule state and do not generate replacement schedules, as specified in [spec 0004](../../specs/vmms/0004-bulk-odometer-updates/index.md). Runtime/integration acceptance remains pending.
  - Predictive maintenance: Implemented in backend and web code; Operations-facing due-window suggestions use recent odometer audit history. Initial schedule creation remains manual, and predictions do not create or modify work orders. Runtime/API verification remains pending in [spec 0012](../../specs/vmms/0012-predictive-maintenance-readiness/index.md).
  - FR-07.4: Implemented. Operations can create schedules for a specific truck with mechanic, checklist, trigger, Due Date, account/provider and notes; the web provides create/edit flows.
  - FR-07.5: Implemented. Due Date is the only user-entered schedule date; the internal start date is the Manila creation day on create and remains unchanged on edit.
  - FR-07.6: Implemented. New schedules use the Manila current day internally; users cannot set a past start date, and edits preserve the stored start date.
  - FR-07.7: Implemented. Server and web paths block duplicate Pending schedules for the same truck and maintenance type.
  - FR-08.1: Implemented. Web has a monthly calendar using start/due dates and displays truck/type/status cells.
  - FR-08.2: Partial. Web list/calendar views include status, priority, vehicle, Garage Branch, Maintenance Type, search and date filters, with sorting by date, priority, Garage Branch and Maintenance Type. Runtime acceptance remains pending.
  - FR-08.3–08.5: Implemented in code. Web and VMMS mobile use Pending green, Due orange, Overdue red, In Progress blue, Done/awaiting review amber, and closed muted; schedule, work-order, dashboard, and notification surfaces include status guidance. Visual and integrated runtime acceptance remain pending.
  - FR-08.6: Implemented. Priority defaults to Medium and create/update/permissions tests cover Admin/Operations control.
  - FR-08.7: Implemented in code. Web registered-option selectors are searchable without creating or activating records; Parts Used remains free text with prior-name suggestions on web and mobile. Keyboard, focus, empty-result, and inactive-option acceptance remain pending.
  - FR-09.1: Semaphore SMS is explicitly excluded from the approved VMMS implementation by [spec 0012](../../specs/vmms/0012-maintenance-scheduling-completion/index.md) until separately approved. Existing in-app maintenance notifications and the schedule evaluation cron remain in scope; do not treat SMS as an implementation gap.
  - FR-09.2: Implemented in code for +1 Chief Mechanic, +3 Admin/Operations and +7 critical escalation, with a daily Manila-time cron and deduplicated notifications.
  - FR-10.1: Implemented in the adjacent checklist module. Admin can create and duplicate checklist templates; copies persist independently.
  - FR-10.2: Implemented in API/mobile scope. Mechanics receive only assigned work; scope checks protect reassigned work.
  - FR-10.3: Implemented. Submission validation lists incomplete checklist items and blocks 100%-incomplete submissions.
  - FR-10.4: Implemented in code. Chief Mechanic approval creates one recurring successor from the submitted service date/odometer and original cycle rules; cancelled occurrences do not continue the chain. Focused recurrence unit tests pass; seeded-flow and integrated runtime verification remain pending in [spec 0008](../../specs/vmms/0008-maintenance-status-lifecycle/index.md) and [spec 0012](../../specs/vmms/0012-predictive-maintenance-readiness/index.md).
  - FR-11.1: Implemented in code. Date edits and approved extensions record prior/new dates, actor, source, and timestamp transactionally; integrated database acceptance remains pending.
  - FR-11.2: Implemented in code. Assigned Mechanics can submit up to two eligible extension requests and Admin can approve/reject them with required review history. Focused service tests pass; the migration is not applied and runtime acceptance remains pending.
  - FR-11.3: Implemented. Operations must submit a reasoned cancellation; work cannot be cancelled after work starts, and the record is retained through Admin review.
  - FR-11.4: Implemented. Outsourced providers are resolved against active registered providers.
  - FR-11.5: Implemented for completed maintenance logs/history, with searchable per-truck web views and status/type/vehicle filtering.
  - Runtime evidence: existing unit coverage covers duplicate schedules, trigger rules, overdue escalation, cancellation and workflow. New focused extension-service and mobile date/status-filter tests pass; backend build, mobile type/lint checks, and web build pass. [Spec 0008](../../specs/vmms/0008-maintenance-status-lifecycle/index.md) documents and tests the existing lifecycle boundaries; integrated browser/API verification remains pending. Spec 0016 also adds canonical `dueDate`/`dueOdometer` and additive `computedStatus` fields to key schedule API responses and aligns maintenance deep-links to supported search prefill. No end-to-end RTM, browser, or mobile-device acceptance is recorded. The migration remains unapplied; feature status remains **in progress**.

### 4. Work orders, checklists, and maintenance history

Support assigned work, checklist completion, parts and labor details, mechanic submission, Chief Mechanic review, and searchable per-vehicle maintenance history.

Done when: assigned-work access, complete-checklist submission, approval and rejection, cost visibility by role, history, and next-service calculations meet their acceptance criteria.

Requirements: BR-12 to BR-15; FR-12.* to FR-15.*; SC-08, SC-09, SC-20.

- VMMS-to-VRMS repair referrals, referral outcomes, ticket status, and VRMS-owned repair-history reads are a scope extension in [spec 0024](../../specs/vmms/0024-vmms-repair-handoff-and-availability/index.md). The cross-system API proposal is pending review in [spec 0026](../../specs/vmms/0026-vmms-vrms-repair-referrals-and-bms-availability/index.md); VRMS and auth implementation are outside VMMS ownership.
- VMMS in-app notification delivery and the unified web/mobile inbox are an approved scope extension under [spec 0029](../../specs/vmms/0029-notification-enhancement-and-completion/index.md), aligned with proposed VMMS notification contract [spec 0030](../../specs/vmms/0030-vmms-notification-contract/index.md). VMMS implementation is complete; migration deployment and browser/device acceptance remain pending. Other system adoption remains with their owners.
- VMMS-owned follow-ups for beyond-repair retirement, repeated-repair alerts, and fuel-anomaly referrals (repair integration Flows 4–6) are implemented in backend and web under [spec 0028](../../specs/vmms/0028-vmms-vrms-repair-follow-ups/index.md). Partner contract review, auth grants, migration application, and live integration remain pending.

- [x] Reconcile the 14 Module 4 RTM rows with API workflow rules, admin views, and VMMS mobile screens.

  Reconciliation evidence as of 2026-11-19:
  - FR-12.1: Implemented. Submitted work generates `MLG-YYYYMMDD-XXXX` from a PostgreSQL sequence in the work-order transaction, and work submission enters Done/DONE after checklist completion.
  - FR-12.2: Implemented. Submission requires plate, positive service odometer, assigned mechanic, maintenance class, maintenance remarks and non-negative labor cost; the mobile form also exposes the required work fields.
  - FR-12.3: Implemented. Work orders support `REPAIR` and `PREVENTIVE` maintenance classes and persist the class in work-order progress.
  - FR-12.4: Implemented. Work start/submit status transitions set vehicle status to `UNDER_MAINTENANCE`, protected against an existing `UNDER_REPAIR` status.
  - FR-13.1: Implemented. Parts cost is calculated from changed-item entries and labor cost is submitted separately; the backend normalizes and computes maintenance totals rather than trusting a manually edited aggregate.
  - FR-13.2: Partial. Priority exists on schedules/work orders and defaults to Medium, with Admin/Operations control and mobile read-only display. Maintenance-log creation and every role-visible surface need end-to-end acceptance verification.
  - FR-14.1: Implemented. The workflow permits assigned Mechanic Start/Save/Submit and assigned Chief Mechanic Approve/Reject/Repair review; approval sets Completed, rejection returns In Progress with remarks, and approval locks the final workflow stage.
  - FR-14.2: Implemented. Completed maintenance logs can be cancelled only by Admin with a mandatory reason; cancellation retains the audit record and locks the log.
  - FR-14.3: Implemented. Completed/Cancelled logs are closed, Operations can request an unlock, Admin approves it, and consumed unlock state re-locks after editing.
  - FR-14.4: Implemented in code. Maintenance-log edits record field, previous value, new value, actor and timestamp, and the edit service runs the controlled unlock flow.
  - FR-14.5: Implemented. A Manila-midnight cron marks eligible Pending, Due or In Progress work overdue and increments dashboard/report-derived overdue views.
  - Append-only business audit: Spec 0010 adds database triggers for immutable audit tables, restrictive work-order/vehicle audit relations, feed categories, and web category filtering. Migration and runtime verification remain pending.
  - FR-15.1: Implemented. API `scheduleScope` limits Mechanics to `assignedMechanicId`; mobile loads and updates only locally synchronized assigned work.
  - FR-15.2: Implemented. Admin has the delete/cancel-log exception; Operations uses void/cancellation requests and cannot delete log records.
  - FR-15.3: Implemented. Web maintenance history has plate/log/work-order search and status/date filtering; vehicle-specific API/history views are also present.
  - Mobile scroll acceptance: the full work-order list, including search/filter controls and pagination, scrolls as one area; detail-step content scrolls beneath fixed step/actions, returns to the top when changing step/order, and adjusts for the keyboard. Device-level acceptance remains pending.
  - Mobile PDF export acceptance: the saved work-order PDF contains both Details and Execution content regardless of the currently selected step. Android saves to the user-granted folder (initially opening Downloads); iOS saves to the app's Documents folder exposed in Files. Device-level save acceptance remains pending.
  - Runtime evidence: unit coverage exists for checklist submission, assignment, approval/rejection, closed-log locks, unlock/audit, cancellation and overdue daily evaluation. Spec 0016 also preserves workflow states while exposing canonical schedule due/status fields and adds the JSON bulk odometer contract used by the Vehicles UI. Browser/mobile/runtime acceptance remains unexecuted, so status stays **in progress**.

## Cost and reporting

### 5. Fuel expenses and anomaly handling

Record receipt-based fuel entries, calculate cost and efficiency, detect anomalies from full-tank history, and manage notes, acknowledgments, resolution, and escalation.

Done when: fuel calculations, insufficient-data behavior, anomaly detection and notifications, audit history, and staged resolution rules meet their acceptance criteria.

Requirements: BR-16 to BR-19; FR-16.* to FR-19.*; SC-10, SC-11, SC-22, SC-24 to SC-26.

- [x] Reconcile the 16 Module 5 RTM rows with fuel API, admin screens, notification behavior, and audit records.

  Reconciliation evidence as of 2026-11-19:
  - FR-16.1: Implemented. Only Operations can create or void fuel entries and manage stations; Admin can monitor/report, while Chief Mechanic and Mechanic are excluded from submission.
  - FR-16.2: Implemented. The API and web form require vehicle, date, station, price, liters, odometer and filled-by data.
  - FR-16.3: Implemented in code. Operations can add, rename, deactivate, and reactivate stations; deactivation preserves history, and fill-ups retain their recorded station name. The snapshot migration still needs deployment. See [Spec 0007](../../specs/vmms/0007-fuel-station-management/index.md).
  - FR-16.4: Implemented. Liters and price per liter require positive values with at most two decimal places.
  - FR-16.5: Implemented. Fuel submission rejects odometer readings below the truck baseline or latest non-voided fill-up.
  - FR-16.6: Implemented. The backend calculates `liters * pricePerLiter`; the web total is read-only and the API DTO does not accept a client total.
  - FR-16.7: Implemented. Web fuel values use the Philippine Peso symbol, and exported headers identify PHP costs.
  - Spec 0009 backend catalog: implemented `GET /settings/catalog` and Admin-only catalog updates delegating to the existing fuel anomaly and maintenance costing domain services. Web UI and runtime acceptance remain pending.
  - FR-17.1: Implemented. Fuel history is ordered by entry date descending, then creation date descending.
  - FR-17.2: Implemented. Fuel entries are retained and voided with reason, actor and audit; voided entries are excluded from report totals and efficiency.
  - FR-17.3: Implemented. Web filtering supports vehicle, date and station and updates filtered fuel KPI cards.
  - FR-18.1: Implemented. Efficiency uses consecutive full-tank cycles, excludes partial/voided entries, and remains `Insufficient Data` until three full tanks exist.
  - FR-18.2: Implemented. Fill-ups are classified Normal, Below Average or Anomaly; configured threshold deviation and Admin/Operations in-app anomaly notifications are supported.
  - FR-19.1: Implemented in code. Midnight escalation records Day 1 Chief Mechanic, Day 3 Admin/Operations, and Day 7 all-role critical notifications, with resolution notes and attachments included. A missing-recipient case now leaves the stage eligible for a later retry.
  - FR-19.2: Implemented. Operations resolve open anomalies, voiding the source auto-resolves it, and Critical resolution requires Chief Mechanic/Admin acknowledgment.
  - FR-19.3: Implemented. Fuel KPIs cover fill-ups, liters, cost and average efficiency and exclude voided entries.
  - FR-19.4: Verified. Per-truck/fleet views, filtered PDF/XLSX content, and local-calendar XLSX filenames are covered by web tests and runtime checks. The browser opened a PDF report popup with the expected title, columns, and vehicle row; the native print dialog was also observed. Its preview is unsupported in this environment, so no PDF file was saved.
  - Acceptance evidence as of 2026-11-21: backend fuel tests passed (32 tests), web fuel-data tests passed (5), web fuel UI tests passed (19), and mobile critical-approval tests passed (32); backend and web production builds passed. In local Docker, all three escalation stages delivered notifications to eligible roles; the temporary anomaly, fill-up, and notifications were removed. The local web app rendered fleet and per-vehicle reports, generated XLSX workbooks containing expected rows, and rendered the PDF popup report. After manual sign-in through the shared portal at `http://localhost:8000`, the browser redirected to VMMS and the Fuel Management page rendered its summary, fill-up table, views, and reports. The earlier fresh-session limitation was due to the browser not being signed in; no application or shared-service code change was needed. Fuel module status is **done**. Receipt scanning is implemented as an approved extension and now also suggests product and SI number; runtime OCR accuracy on representative Caltex/Petron receipts and migration deployment remain unverified pending Azure configuration and a receipt pilot.
  - [Spec 0006](../../specs/vmms/0006-bulk-fuel-statement-import/index.md) adds an Operations workbook import with editable per-row review for billing statements. Backend and web implementation is present; code verification and migration deployment remain pending.
  - Approved and implemented [spec 0017](../../specs/vmms/0017-fuel-operations-reconciliation/index.md) adds a transient import reconciliation summary and informational age for open anomalies without changing existing fuel rules. Runtime and cross-user acceptance remain pending.
  - Fuel-anomaly referral UI and Chief Mechanic anomaly-only access are implemented as part of the VRMS follow-up slice in [spec 0028](../../specs/vmms/0028-vmms-vrms-repair-follow-ups/index.md); partner contract and live integration checks remain pending.

### 6. Maintenance costing

Aggregate completed maintenance costs per vehicle and flag high-cost vehicles using the configured threshold, without income or profit data.

Done when: cost totals use eligible completed records, threshold changes are authorized and audited, and cost fields follow the BRD role boundaries.

Requirements: BR-20 to BR-22; FR-20.* to FR-22.*; SC-12, SC-13.

- [x] Reconcile the 10 Module 6 RTM rows with costing calculations, threshold controls, and role-filtered views.

  Reconciliation evidence as of 2026-11-19:
  - FR-20.1: Implemented. Costing queries only `COMPLETED` and `VERIFIED` schedules, derives parts/labor/total cost, and provides no manual costing write endpoint.
  - FR-20.2: Implemented by data source boundaries. Costing reads only VMMS maintenance schedules and does not include VRMS repair or fuel data.
  - FR-20.3: Implemented. The dashboard exposes maintenance-cost KPIs and truck cost detail only, with no income, profit or revenue fields.
  - FR-21.1: Implemented. Selecting a truck shows completed work in the selected period with work-order number, type, mechanic, completion date and cost.
  - FR-21.2: Implemented. Admin configures a positive PHP threshold; totals above the threshold are visually flagged.
  - Spec 0009 backend catalog: the existing maintenance-cost threshold remains the source of truth and is exposed/updated through the VMMS settings catalog API. Web UI and runtime acceptance remain pending.
  - FR-21.3: Implemented. The backend marks recurring-high-cost candidates when monthly totals exceed the threshold in the latest three consecutive Manila months.
  - FR-21.4: Implemented. The dashboard defaults to the current Manila month and supports custom and common period types, truck selection and cost detail updates.
  - FR-22.1: Implemented. API and web costing access is limited to Admin and Operations.
  - FR-22.2: Implemented in code under approved [spec 0018](../../specs/vmms/0018-maintenance-costing-exports-and-analysis/index.md). PDF remains; the new two-sheet `.xlsx` export includes summary/detail, period, generation timestamp, totals and flags, and scopes both sheets to a selected truck. CSV is excluded. Runtime export verification remains pending.
  - FR-22.3: Threshold changes retain the existing audit path. Completed PDF/XLSX exports now append actor, format, date range and optional truck scope to the VMMS business audit; page views and refreshes are not audited. The additive migration is not yet applied, and runtime audit verification remains pending.
  - Cost analysis: The web dashboard compares the selected period with the approved preceding equivalent range and groups eligible completed costs by maintenance type and current garage assignment. Missing categories remain unclassified; garage attribution is explicitly current, not historical.
  - Role visibility: Mobile does not expose the aggregate costing dashboard, while submitted work can show individual cost data subject to its existing role restrictions.
  - Acceptance evidence: backend costing/export/audit tests (20) and web period/breakdown tests (5) pass; backend and web production builds pass. Migration deployment, browser export parity, and runtime audit acceptance remain unexecuted. Feature status remains **in progress**.

### 7. Reports and fleet dashboard

Present fleet status and management reports for upcoming and completed maintenance, frequency, costs, downtime, fuel, efficiency, and flagged vehicles.

Done when: required dashboards and report outputs are accurate, exportable, and generated on the daily and monthly schedule described in the BRD.

Requirements: BR-23 to BR-26; FR-23.* to FR-26.*; SC-14, SC-15.

- [x] Reconcile the 11 Module 7 RTM rows with admin web, analytics API, generated reports, and export behavior.

  Reconciliation evidence as of 2026-11-19 (dashboard updated 2026-11-24, [spec 0015](../../specs/vmms/0015-fleet-dashboard-enhancement/index.md)):
  - FR-23.1: Partial (enhanced). The fleet dashboard now adds URL-backed filters (All/Today Manila/This month Manila/Custom), separated current operational vs period-activity (recorded-date) metrics, attention queues (overdue/due/due soon/awaiting review/open fuel anomalies for Admin/Ops), status breakdown, garage workload, recent work orders, role-aware panels, and manual/30s/focus refresh with last-updated/error handling. Period completion/cost remain date-based approximations where schedule completion timestamps are unavailable. Required `<3s` load and real-time accuracy are not runtime-measured.
  - FR-23.2: Implemented in the maintenance reports view. Upcoming schedules are listed, sorted and filtered by urgency/date/vehicle/mechanic.
  - FR-23.3: Partial. Completed maintenance, maintenance/fuel cost summaries, downtime, fuel efficiency and flagged/recurring views are present. The full source-to-report suite and cross-report accuracy need runtime validation.
  - FR-24.1: Partial. Reports support time, truck, mechanic, status, date and search filtering; some report implementations include garage/type filters, but the exact common 3-second filter SLA is not measured.
  - FR-25.1: Implemented in code. A Manila 07:00 daily cron persists overdue, under-maintenance and open-anomaly counts and notifies Admin/Operations.
  - FR-25.2: Implemented in code. A Manila 07:00 daily cron creates a previous-month fleet maintenance/fuel cost summary on the 1st of each month and notifies management.
  - FR-26.1: Partial. PDF/Excel/CSV report exports use filtered page data, and filtered fuel exports have audit calls. Runtime confirmation of timestamp, exact filter parity and no-profit columns is not recorded.
  - FR-26.2: Implemented for table exports. Maintenance and fuel report PDF utilities render report titles and tabular data rather than full-page UI.
  - FR-26.3: Implemented. Cost fields use Philippine Peso and reports contain maintenance/fuel cost and efficiency, not income/profit/net revenue.
  - FR-26.4: Implemented. Reports and dashboard routes are management-facing; API report/cost routes restrict access to Admin/Operations.
  - FR-26.5: Partial. Fuel report exports call `recordFuelReportExport`; dashboard/report access and maintenance report export access are not confirmed in a general append-only audit trail.
  - Business audit logs: Admin-only access is implemented in the web route/navigation and backend role guard under [VMMS spec 0002](../../specs/vmms/0002-business-audit-admin-only/index.md). The API role-matrix test, web navigation-permission test, and both production builds pass; interactive route and shared-portal acceptance remain pending. The shared integration guide still needs alignment through its review process.
  - Acceptance evidence: scheduled-report unit coverage and web/fuel export tests exist; spec 0015 frontend dashboard slice implemented in `welinc-web-vmms` (pending integrated/manual verification and build/typecheck evidence in this session where applicable). Fleet-dashboard load timing, print output, full report-source accuracy, and report/dashboard audit coverage remain unexecuted. Feature status remains **in progress**.

## Cross-cutting

### 8. Analytics, mobile synchronization, and release readiness

Keep analytics as a derived read model, synchronize VMMS data safely to the shared mobile app, and close integration, performance, audit, and deployment criteria.

Done when: analytics refresh and validation, role-gated dashboards and advisories, atomic mobile synchronization, audit coverage, and desktop/mobile readiness meet the cross-cutting requirements and applicable success criteria.

Requirements: BR-27 and BR-28; FR-27.1 to FR-27.12 and FR-28.1 to FR-28.3; SC-16, SC-17.

- [ ] Provide an idempotent, relationally complete synthetic development seed across the current VMMS schema; see [spec 0027](../../specs/vmms/0027-complete-vmms-demo-seed/index.md).
- [x] Reconcile the 15 Cross-Cutting RTM rows with the analytics service and VMMS flows in `welinc-mobile-vrms_vmms`.
- [ ] Confirm the final integration and deployment evidence for the applicable success criteria.

  Reconciliation evidence (code review 2026-11-19; access decision updated 2026-11-25):
  - FR-27.1: Implemented. The analytics sync extracts core PostgreSQL vehicle, schedule and checklist source records without changing operational rows.
  - FR-27.2: Implemented. The DuckDB sync prepares snapshot, status, trend, vehicle KPI, alert, summary and schedule tables.
  - FR-27.3: Implemented. Health, overview, vehicles, alerts, report, AI, work-order and legacy alias endpoints are exposed.
  - FR-27.4: Implemented in the web Analytics page. It loads KPI, status, trend, vehicle metrics and alert/report views from the analytics API.
  - FR-27.5: Implemented. Vehicle analytics produces plate/model/risk/score/reason/action-style ranked maintenance-risk results.
  - FR-27.6: Implemented. Alerts include predictive risk/severity and vehicle threshold data, with below-threshold vehicles excluded by the alert/KPI logic.
  - FR-27.7: Implemented. Forecast logic supplies 7/30/90-day information and AI overview/trend/anomaly context.
  - FR-27.8: Partial. Semantic maintenance search and embeddings exist in the service, but runtime embedding coverage/vector validation is not recorded.
  - FR-27.9: Implemented in code. Work-order advisory/recommendation routes provide contextual safety, tools/parts, execution and quality guidance with fallback behavior.
  - FR-27.10: Implemented in code; runtime role acceptance remains pending. Admin and Operations can use the web Analytics navigation and direct route, and fleet-read APIs enforce the Admin/Operations guard. Manual sync remains Admin-only; mobile roles cannot access fleet analytics.
  - FR-27.11: Implemented. Overview/report responses include generatedAt, source update time, data age and stale status metadata.
  - FR-27.12: Partial. Migration/validation code exists for data-mart tables and embeddings, but source/target runtime validation evidence is not recorded.
  - FR-28.1: Implemented. Mobile sync retrieves `/vehicles`, `/maintenance-schedules` and `/checklists` and stores records in SQLite.
  - FR-28.2: Implemented. Snapshot reconciliation occurs inside an SQLite exclusive transaction; partial HTTP failures occur before cache replacement and retain the last successful cache.
  - FR-28.3: Implemented. Checklist state is preserved across reconciliation, `lastSuccessfulSyncAt` is written only after success, and network reconnection starts automatic sync.
  - Mobile global search is an approved scope extension: search role-visible cached work orders/schedules (including associated vehicle plate/model) and current-user notifications, then open the existing workflow. Global Search and Work Orders search also maintain separate per-account recent query histories. See [spec 0011](../../specs/vmms/0011-mobile-global-search/index.md); device acceptance remains pending.
  - Additional gaps:
  - Mobile staging currently contains the offline-sync continuation and revision guards, but no mobile test/build run confirms them.
  - Analytics HTTP authorization tests exist, but DuckDB/pgvector runtime migration, validation and source consistency are not executed.
  - Proposed analytics runtime readiness, data-health visibility, and evidence-backed AI work is documented in draft [spec 0021](../../specs/vmms/0021-analytics-data-readiness-and-ai-evidence/index.md); it is not approved or authorized for implementation.
  - Deployment evidence for shared services, gateway routes, VMMS containers, web/mobile readiness and final environment configuration is not complete.
  - Cross-cutting reconciliation remains **in progress** until runtime integration and deployment evidence are recorded.
