# 0008. Maintenance status lifecycle

**Status**: Implementation complete; integrated runtime verification pending
**Scope**: [Maintenance scheduling and alerts](../../../scope/vmms/index.md#3-maintenance-scheduling-and-alerts); [Work orders and maintenance history](../../../scope/vmms/index.md#4-work-orders-checklists-and-maintenance-history)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Define one explicit VMMS contract for user-driven, administrative, and
automatically-derived maintenance schedule status changes. This documents and
tests existing workflow boundaries; it does not merge maintenance status with
approval status or vehicle status.

## Sources and decision

- VMMS BRD/RTM modules 3 and 4: scheduling, due/overdue, work-order execution,
  chief-mechanic review, cancellation, and completed maintenance history.
- Existing lifecycle behavior in `welinc-backend-vmms` is the implementation
  baseline. The catalog must match guarded service behavior and must not add
  a new role, state, or direct status-edit path.
- The user selected coverage of work orders, schedule actions, and automated
  date/odometer status transitions.

The state names remain `PENDING`, `DUE`, `IN_PROGRESS`, `DONE`, `COMPLETED`,
`OVERDUE`, and `CANCELLED`. `MaintenanceApprovalStatus` remains a separate
review axis. `OVERDUE` may represent an in-progress work order; its
`workOrderProgress.overdueFromStatus` records that prior phase.

## Lifecycle contract

| Trigger | Permitted status effect | Actor / guard |
|---|---|---|
| Create schedule | Starts `PENDING`; Operations may create it as `DUE` or `OVERDUE`; cannot create `IN_PROGRESS`, `DONE`, `COMPLETED`, or `CANCELLED` | Operations |
| Edit an unstarted schedule | May retain or set `PENDING`, `DUE`, or `OVERDUE`; cannot set `IN_PROGRESS`, `DONE`, `COMPLETED`, or `CANCELLED` | Operations |
| Odometer evaluation | Recalculates eligible odometer schedules to `PENDING`, `DUE`, or `OVERDUE` from activation/due readings; does not change started or closed work | Vehicle master-odometer update transaction |
| Daily time evaluation | A past-due schedule in `PENDING`, `DUE`, or `IN_PROGRESS` becomes `OVERDUE`; records the prior state and evaluation time | Scheduled backend job |
| Start work | `PENDING`, `DUE`, or `OVERDUE` becomes `IN_PROGRESS`; starting an overdue job clears its saved overdue marker | Assigned mechanic |
| Save work progress | Status does not change | Assigned mechanic / chief mechanic, subject to workflow guard |
| Submit completed checklist | `IN_PROGRESS` (including overdue work represented by `OVERDUE`) becomes `DONE` | Assigned mechanic |
| Chief review | `DONE` becomes `COMPLETED` on approval, or `IN_PROGRESS` on reject/repair; rejection requires remarks | Assigned chief mechanic |
| Cancellation request | Request creation and rejection do not change schedule status; approval can set an eligible unstarted schedule to `CANCELLED` | Operations requests; Admin reviews |
| Maintenance-log void | Approved void of a completed log sets it to `CANCELLED`; an Admin cancellation records a reason and closes the log | Operations requests; Admin reviews or cancels |
| Recurrence | Approval of completed recurring work creates one separate successor using the initial cycle rules and the submitted service date/odometer; a cancelled occurrence creates no successor | System, in the approval transaction |
| Deactivation | Soft-deletes the schedule; does not rewrite status or erase its history | Admin, subject to existing restrictions |

Time-based schedules are not assigned `DUE` by an additional new timer in this
slice. The daily overdue job continues to apply the existing past-due rule.
Any future change to that rule requires its own approved behavior change.

## Acceptance criteria

1. A version-controlled lifecycle table covers each state and each identified
   API, role, odometer, date-job, review, cancellation, and recurrence trigger.
2. Service/API tests prove allowed transitions and reject direct workflow
   bypasses; derived transitions preserve optimistic concurrency checks.
3. An overdue in-progress schedule retains enough progress state to resume or
   complete work and does not appear as unstarted work.
4. Status, approval status, vehicle status, and soft deletion remain distinct.
5. Existing routes, response fields, and persisted enum values remain
   compatible; no migration is required.
6. Recurrence uses the service completion timestamp and odometer captured at
   mechanic submission, not the later review timestamp or a newer master
   reading. It preserves the cycle's trigger and interval rules.
7. Recurrence creation is idempotent and transactional; cancellation of an
   occurrence prevents a successor from being created from that occurrence.

## API, data, and security impact

- No new route, role, status enum, table, or persisted field.
- Existing schedule, work-order, cancellation, and odometer APIs keep their
  payloads and authorization.
- Status changes continue to use existing service transactions, scoped
  authorization, and compare-and-set conflict handling.
- Do not allow a web/mobile client to assert derived due/overdue state as
  authoritative.
- Store the mechanic's completion timestamp in the existing
  `workOrderProgress` JSON and use the submitted service odometer already
  persisted on the schedule. No new column or migration is required.

## Affected repositories

- `welinc-backend-vmms`: maintain the contract with focused lifecycle and API
  tests.
- `welinc-web-vmms` and `welinc-mobile-vrms_vmms`: verify labels and allowed
  actions reflect the existing API states; no UI behavior change is planned.

## Delivery status

The focused recurrence unit tests pass. Seeded-flow and integrated runtime
checks remain subject to the verification steps in [verify.md](verify.md).
