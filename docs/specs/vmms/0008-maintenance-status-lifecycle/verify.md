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
- [ ] Confirm status, approval status, vehicle status, and deletion remain
  independent; compare existing route and response contracts → AC-4, AC-5

## UI / integration

- [ ] Check web and mobile labels/actions against each status and role
- [ ] Verify odometer update, daily overdue evaluation, and review flows in an
  integrated VMMS environment

## Commands

- [ ] Run focused maintenance-schedule, work-order, cancellation, overdue, and
  vehicle-odometer tests
- [ ] Build `welinc-backend-vmms`

## Acceptance-criteria coverage

- AC-1 through AC-5 are covered by the lifecycle matrix, tests, client review,
  and API compatibility checks above.
