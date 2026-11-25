# Verification

## Automated and schema checks

- [x] `npm run build` validates the Prisma schema, generates the client, and
  compiles the VMMS backend.
- [ ] Run focused service/controller checks for authorization, event ordering,
  idempotency, link validation, return-to-review, cancellation, recurrence,
  and status precedence.

## Integrated acceptance

- [ ] Obtain a `vrms` service token for VMMS with
  `fleet.repair-status.write`.
- [ ] Have VRMS send `OPENED`, link multiple accepted VMMS schedules, then send
  `COMPLETED`; verify all linked schedules return as `DONE` / `UNVERIFIED`
  with inspection items reset, no successors are created yet, and vehicle
  status remains `UNDER_MAINTENANCE` pending final verification.
- [ ] Complete the final Chief Mechanic inspection in VMMS; verify normal VMMS
  approval completes the schedules and creates eligible recurring successors.
- [ ] Include `OVERDUE` schedules whose saved prior state is `IN_PROGRESS` and
  verify the linked repair completion returns them to final verification.
- [ ] Repeat with `CANCELLED`; verify schedules remain open and VMMS fleet
  status reflects active maintenance.
- [ ] Replay and reorder events; verify idempotency and explicit conflict
  responses.

Focused tests, migration application, and integrated runtime checks remain
pending. The auth grant and VRMS sender are outside this slice.
