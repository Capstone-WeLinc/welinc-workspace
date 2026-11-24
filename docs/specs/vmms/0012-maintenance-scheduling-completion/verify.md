# Verify: Maintenance scheduling completion · spec 0011

Steps derived from the acceptance criteria in [index.md](index.md).

## API / database

- [ ] Verify assigned Mechanic, unassigned Mechanic, Admin, Operations, and
  closed-schedule access for request and review routes → AC-3–5, AC-7
- [ ] Verify later-date validation, required reasons, two total requests,
  one-pending-request rule, and concurrent duplicate submission behavior →
  AC-4
- [ ] Verify rejection leaves the schedule unchanged; approval changes only
  the target due date and records reviewer and decision → AC-5
- [ ] Verify approval for an overdue in-progress schedule both before and
  after Manila today; confirm progress restoration/retention → AC-6
- [ ] Verify manual start/due date edits and approved extensions record old/new
  values, actor, source, and timestamp atomically → AC-2, AC-5
- [ ] Verify request and decision audit events are append-only and covered by
  the existing audit protection/identity-erasure behavior → AC-7
- [ ] Verify schedule creation, odometer threshold refresh, cancellation,
  in-app notification, and staged escalation behavior remain unchanged →
  AC-1, AC-10

## Implementation evidence

- Extension request, pending-list, review, history, reschedule audit, and
  append-only audit tables/models are implemented.
- The migration includes a partial unique index for one pending request per
  schedule and append-only triggers for extension/reschedule audit tables.
- Focused service tests pass, and the service enforces assignment, request
  limits, dates/reasons, overdue restoration, and rejection/approval behavior.
- Web/mobile status and selector work is present, but migration application,
  integrated API/browser/device, and concurrency acceptance remain pending.

## Web / mobile

- [ ] Verify Admin can find, inspect, approve, and reject pending extension
  requests through the 50-item cursor-paginated queue, with clear validation
  and server errors → AC-5, AC-7
- [ ] Verify assigned Mechanic can request and review extension history;
  another Mechanic cannot see or change that schedule's requests → AC-3,
  AC-7
- [ ] Inspect list, calendar, work-order, notification, and mobile statuses
  for the approved colors and a visible Red/Orange/Green legend → AC-8
- [ ] Search each applicable registered-option selector by partial text;
  verify keyboard access, empty/loading states, and inactive-option exclusion
  → AC-9; verify schedule garage is read-only and matches the selected
  vehicle's garage assignment; verify Parts Used suggests prior values
  without restricting new free-text names
- [ ] Verify the existing FR-08.2 filters/sorting remain intact and use a
  browser acceptance path for schedule creation/edit/review → AC-1, AC-8,
  AC-9

## Commands / runtime

- [x] Run focused maintenance-schedule extension service tests (9 passed),
  covering request limits, date/assignment eligibility, approval/rejection,
  and authorized history response
- [x] Re-ran the focused extension suite on 2026-11-24:
  `npx jest src/modules/vmms/maintenance-schedules/schedule-extension.spec.ts --runInBand`
  passed with 9 tests.
- [x] Re-ran recurrence and scheduling permission suites on 2026-11-24:
  - `recurrence.spec.ts`: 27 passed
  - `scheduling-permissions.spec.ts`: 43 passed
- [ ] Run focused maintenance-schedule controller and integrated API tests
- [ ] Validate Prisma schema and generate the client; do not apply the
  migration
- [x] Run backend build, mobile typecheck/lint and targeted tests, and web
  production build
- [ ] Run browser acceptance; the web repository has no Playwright setup, so
  no browser test or additional tooling was added
- [ ] Verify due-date, odometer, in-app notification, and escalation behavior
  in an integrated VMMS environment; SMS is excluded

## Acceptance-criteria coverage

- AC-1 through AC-10 are covered by the API/database, client, and runtime
  checks above. A build alone is not runtime acceptance.
