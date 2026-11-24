# Verify: Maintenance status lifecycle · spec 0008

Steps derived from the acceptance criteria in [index.md](index.md).

## API / automated

- [ ] Cover every row of the transition table with service/API tests; verify
  actor authorization, current-state guards, and rejected direct changes →
  AC-1, AC-2
- [ ] Start an overdue in-progress work order, submit it, and verify its
  progress data and `DONE` state are retained; test the scheduled date and
  odometer transitions with compare-and-set conflicts → AC-2, AC-3
- [ ] Verify chief approval, rejection, repair, cancellation approval,
  maintenance-log void, recurring schedule creation, and soft deletion →
  AC-1, AC-2
- [x] Focused recurrence unit tests verify submitted service date/odometer,
  cycle rules, one linked successor, and no successor from a cancelled
  occurrence → AC-6, AC-7
- [ ] Verify delayed review against persisted data and confirm recurrence
  remains transactional and idempotent under runtime retries → AC-6, AC-7
- [ ] Confirm status, approval status, vehicle status, and deletion remain
  independent; compare existing route and response contracts → AC-4, AC-5

## UI / integration

- [ ] Check web and mobile labels/actions against each status and role
- [ ] Verify odometer update, daily overdue evaluation, and review flows in an
  integrated VMMS environment

## Commands

- [x] Run focused recurrence and extension unit tests
  (`recurrence.spec.ts` and `schedule-extension.spec.ts`; 36 passed)
- [x] Re-ran recurrence and scheduling permission suites on 2026-11-24:
  - `recurrence.spec.ts`: 27 passed
  - `scheduling-permissions.spec.ts`: 43 passed
- [ ] Run the broader maintenance-schedule, work-order, cancellation, overdue,
  and vehicle-odometer test set
- [x] Build `welinc-backend-vmms`
  
## Implementation evidence

- Create/update routes reject direct `CANCELLED`, `DONE`, `COMPLETED`, and
  work-progress workflow bypasses; in-progress and done edits remain guarded.
- Odometer, overdue, start/save/submit/review, cancellation, maintenance-log
  void, recurrence, soft-delete, and status/approval/vehicle separation are
  represented in existing VMMS service code.
- Focused recurrence and extension tests pass; broader integrated lifecycle
  browser/API acceptance remains pending.

## Acceptance-criteria coverage

- AC-1 through AC-5 are covered by the lifecycle matrix, tests, client review,
  and API compatibility checks above.
