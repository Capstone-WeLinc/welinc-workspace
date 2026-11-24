# Verification

## Contract acceptance

- [ ] A `vrms` service token for VMMS with `fleet.repair-status.write` is
  accepted; user tokens, another service client, wrong audience, and missing
  scope are refused.
- [ ] `OPENED` marks the matching VMMS vehicle `UNDER_REPAIR`.
- [ ] A maintenance update cannot overwrite an open repair's status.
- [ ] `LINKS_UPDATED` accepts only additional active `IN_PROGRESS` /
  `FOR_REPAIR` schedules (or `OVERDUE` schedules whose saved prior state is
  `IN_PROGRESS`) belonging to that VMMS vehicle.
- [ ] `COMPLETED` returns all and only linked schedules to `DONE` /
  `UNVERIFIED`, with inspection items reset for a fresh Chief Mechanic review;
  no schedule is completed and no recurring successor is created by the event.
- [ ] Chief Mechanic approval through the normal VMMS workflow completes the
  work orders and creates eligible recurring successors.
- [ ] `CANCELLED` keeps linked schedules open and recomputes the vehicle to
  `UNDER_MAINTENANCE` when those schedules remain active, including schedules
  overdue from `IN_PROGRESS`.
- [ ] Vehicle status remains `UNDER_REPAIR` while any other repair is open,
  then becomes `UNDER_MAINTENANCE` if VMMS work remains, else `AVAILABLE`.
- [ ] Replaying the same event is idempotent; stale, skipped, conflicting, or
  invalid-transition versions change nothing.
- [ ] VMMS never reads VRMS tables or stores repair costs, parts, or issue
  details.

## Delivery status

- [x] VMMS backend build and Prisma Client generation.
- [ ] Focused VMMS service/controller checks.
- [ ] welinc-auth client grant for `vrms` and `VMMS` audience.
- [ ] VRMS event sender and propagation of accepted VMMS schedule IDs.
- [ ] Integrated test: create repair, link multiple VMMS schedules, close or
  cancel the ticket, and observe VMMS final-review state and vehicle status;
  verify the usual Chief Mechanic approval flow completes the work.

No runtime integration evidence is claimed until the external auth grant and
VRMS sender exist.
