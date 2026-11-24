# 0011. Maintenance scheduling completion

**Status**: Implementation complete; migration and runtime acceptance pending
**Scope**: [Maintenance scheduling and alerts](../../../scope/vmms/index.md#3-maintenance-scheduling-and-alerts)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Close the identified Module 3 implementation gaps without changing the
Operations-owned schedule-creation policy or the lifecycle in [Spec 0008](../0008-maintenance-status-lifecycle/index.md).
Add an auditable reschedule and Admin-reviewed extension workflow, align
schedule status colors, and make the relevant reference selectors searchable.

## Sources and decisions

- VMMS BRD/RTM Module 3 requirements FR-07 through FR-11.
- Existing schedule lifecycle and date/odometer behavior in Specs 0004 and
  0008.
- User-approved decisions:
  - Schedule creation remains Operations-managed. Odometer threshold
    crossings update existing schedules and never create replacements.
  - Assigned Mechanics may submit at most two extension requests per
    schedule while work is in progress. Every submitted request counts,
    including rejected requests; only one request may be pending at a time.
  - Admin approves or rejects requests. The target due date changes only on
    approval.
  - A request date must be later than the current target due date. No
    arbitrary maximum extension duration is imposed.
  - A non-empty request reason and a non-empty Admin rejection reason are
    required.
  - An `OVERDUE` schedule is eligible only when
    `workOrderProgress.overdueFromStatus` is `IN_PROGRESS`.
  - A schedule's garage is inherited from its selected vehicle's garage
    assignment; it is not independently selectable in schedule creation or
    editing.
  - Pending is green, Due is orange, and Overdue is red. In Progress remains
    blue, Done/awaiting review amber, and Completed/Cancelled muted.
  - Parts Used remains free text, with searchable suggestions from previously
    entered part names. Do not introduce a parts catalog.
  - Semaphore SMS delivery is excluded. Existing in-app notifications and
    escalation behavior are verified but not replaced.

## Behavior and controls

### Date changes and audit

- Operations may edit dates only through the existing schedule update route.
- If an update changes the schedule start date or target due date, write one
  reschedule audit record in the same transaction. Record both old/new date
  pairs, actor ID and display identity, source, and timestamp. Do not write an
  audit record when neither date changes.
- On extension approval, update only the target due date and write the same
  reschedule audit record with source `EXTENSION_APPROVAL`.
- Store audit timestamps as timezone-aware database timestamps. Responses and
  history displays retain date, hour, minute, and second; UI displays use
  Manila time.
- Reschedule and extension audit events are append-only under
  [Spec 0010](../0010-append-only-business-audit/index.md). Mutable extension
  request status remains workflow state and is not treated as immutable event
  evidence.

### Extension requests

- Add an extension request only for the schedule's assigned Mechanic when
  status is `IN_PROGRESS`, or when status is `OVERDUE` with saved prior state
  `IN_PROGRESS`.
- Require a trimmed request reason of 1–2000 characters and a proposed
  target due date strictly later than the current target due date. Compare
  date-only values; the proposal need not be later than today's date.
- Reject requests for closed schedules, schedules not assigned to the caller,
  schedules with a pending request, or schedules that already have two
  submitted requests.
- Admin may approve or reject a pending request. Reject decisions require a
  trimmed reason of 1–2000 characters. Persist requester and reviewer
  identity, request/decision timestamps, reasons, and decision.
- Approval changes the target due date only. If an overdue schedule's
  approved target due date is today or later in Manila time, restore
  `IN_PROGRESS` and clear its saved overdue marker. If it remains before
  today, keep `OVERDUE` and preserve the marker.
- Rejection and request creation do not change schedule dates or status.
- Keep requests and decision events available in authorized schedule history.
  Admin receives a pending-review list; no unrelated schedule is exposed.

### Status colors and searchable selectors

- Use the approved status mapping consistently in schedule list, calendar,
  work-order details, notification summaries, and mobile schedule/work-order
  views: Pending green, Due orange, Overdue red, In Progress blue,
  Done/awaiting review amber, and Completed/Cancelled muted.
- Include a visible legend where schedule statuses are presented together.
- In schedule creation and editing, derive the garage from the selected
  vehicle's registered garage assignment and display it read-only; do not
  offer a separate garage choice in the form.
- Where Module 3 forms select a registered vehicle, provider, or mechanic,
  allow typing to filter the existing allowed options. Search does not create
  records, broaden authorization, or make inactive records newly selectable.
- Keep work-order Parts Used as free text. Offer matching, case-insensitive
  suggestions from part names already present in loaded work-order history;
  selecting a suggestion is optional and a new part name remains valid.
- Preserve keyboard, focus, empty-result, loading, and validation behavior;
  keep existing API values and selection semantics.

## API, data, and security impact

- Add authenticated VMMS routes for assigned Mechanic request creation and
  authorized extension history, plus Admin pending-list and review actions.
  The Admin list is cursor-paginated in pages of 50.
- Enforce assignment, role, request-count, pending-request, date, and reason
  rules in the backend, not only in clients.
- Add migration-backed extension workflow and append-only audit persistence.
  Add a partial unique database index for one pending extension per schedule.
- Use a transaction for request creation plus request-audit insertion and for
  review, schedule update, date-audit insertion, and decision-audit insertion.
- Do not apply migrations or deploy without explicit authorization.
- No shared auth, gateway, portal, cross-system API, or analytics ownership
  change is in scope.

## Acceptance criteria

1. Operations can create and edit schedules under Specs 0004/0008; threshold
   crossings update existing eligible schedules without creating replacements.
2. Date edits record previous/new start and target dates, actor, source, and a
   timestamp displayed to the second; schedule update and audit commit or fail
   together.
3. Only the assigned Mechanic can request an extension while `IN_PROGRESS`
   or while `OVERDUE` with saved prior state `IN_PROGRESS`.
4. The API rejects invalid dates, missing/invalid reasons, a third request,
   a second pending request, unassigned callers, and closed or ineligible
   schedules.
5. Only Admin can review. Approval updates the target due date and records
   decision and reschedule audits atomically; rejection requires a reason and
   changes neither the schedule date nor status.
6. Overdue work is restored to `IN_PROGRESS` only when the approved date is
   today or later in Manila time; otherwise its overdue state is retained.
7. Request and decision history is visible only to authorized users; audit
   events cannot be updated or deleted through the database.
8. Web and mobile use the same status color mapping and clearly explain the
   Red/Orange/Green urgency states.
9. Applicable Module 3 registered-option selectors are searchable without
   allowing unregistered or inactive choices; a schedule's garage matches
   the selected vehicle's registered assignment and is not independently
   editable. Parts Used offers prior values as suggestions while still
   accepting new free text.
10. Existing in-app notification and staged escalation behavior remains
    intact. Semaphore SMS remains explicitly unimplemented.

## Affected repositories

- `welinc-backend-vmms`: request/review API, validation, transaction-backed
  persistence, append-only audit, migration, and tests.
- `welinc-web-vmms`: Admin review flow, searchable schedule selectors, and
  consistent status colors/legend.
- `welinc-mobile-vrms_vmms`: assigned Mechanic extension request/history and
  consistent status colors/legend, limited to VMMS screens.

## Delivery status

The API, web, and VMMS mobile implementation is present. Focused service and
mobile tests, backend build, mobile type/lint checks, and web build passed.
Integrated runtime, browser, and mobile-device acceptance remain pending.
The migration remains unapplied; migration application and deployment are
not authorized by this spec.
