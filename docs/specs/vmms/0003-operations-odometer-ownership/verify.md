# Verify: Operations ownership of vehicle odometer updates · spec 0003

Steps derived from the acceptance criteria in [index.md](index.md).

## API / automated

- [ ] Operations can call `PATCH /vehicles/:id/odometer` with a positive integer
  at or above the latest reading → AC-1, AC-2
- [ ] Lower, zero, negative, fractional, and stale readings are rejected
  without changing the vehicle or audit state → AC-2
- [ ] Admin, Chief Mechanic, and Mechanic receive authorization denial from the
  dedicated endpoint and cannot mutate odometer through generic vehicle edit →
  AC-3
- [ ] Complete or submit work-order evidence containing a service odometer →
  confirm the evidence is retained and `Vehicle.odometer` is unchanged → AC-4
- [ ] Update a master reading and verify the vehicle and audit commit atomically
  with the Operations actor; submit the same reading again and confirm no
  duplicate audit event → AC-5
- [ ] Confirm vehicle creation can set an initial reading and general vehicle
  updates cannot accept an odometer field → AC-7

## Mobile / manual

- [ ] Confirm mobile reads the master vehicle snapshot and does not expose,
  queue, or submit an odometer write action → AC-6

## Commands

- [x] Run the targeted VMMS vehicle, work-order, and recurrence tests
- [x] Build `welinc-backend-vmms`
- [x] Run changed-file lint for backend and web
- [x] Build `welinc-web-vmms`
- [ ] Exercise the complete web and mobile runtime acceptance flow
- [ ] Reconcile RTM FR-05.1 actor and surface wording

## Acceptance-criteria coverage

- AC-1, AC-2, AC-3, AC-5, AC-7 by API and service tests
- AC-4 by work-order evidence verification
- AC-6 by mobile read-only verification
