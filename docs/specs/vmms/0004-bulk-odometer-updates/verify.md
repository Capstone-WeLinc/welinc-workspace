# Verify: Bulk odometer updates and schedule refresh · spec 0004

Steps derived from the acceptance criteria in [index.md](index.md).

## API / automated

- [ ] Update a vehicle master reading → confirm all eligible odometer schedules
  are reevaluated without rewriting their configured values → AC-1, AC-2
- [ ] Verify `PENDING`, `DUE`, `OVERDUE`, and preserved workflow states at
  activation/due/overdue boundaries → AC-3
- [ ] Preview a multi-vehicle workbook → confirm matched vehicles and proposed
  readings are displayed without database writes → AC-4
- [ ] Test unknown, duplicate, inactive, invalid, lower, and stale rows plus
  valid rows; confirm independent row-level results → AC-5
- [ ] Test changed-row transactions for vehicle, audit, and schedule state;
  confirm one row failure does not roll back another row → AC-6
- [ ] Submit equal readings → confirm no audit, schedule, or notification
  duplicate is created → AC-7
- [ ] Confirm Admin, Chief Mechanic, and Mechanic cannot use update/import
  endpoints; confirm old per-schedule odometer and threshold actions are absent
  → AC-8
- [ ] Confirm analytics and mobile consume refreshed existing API snapshots
  and expose no independent odometer write path → AC-9

## Database / deployment

- [ ] Apply `20261119000100_vehicle_maintenance_defaults` before backend
  deployment
- [ ] Run migration verification and confirm existing schedules retain their
  saved interval, buffer, threshold, and reference values

## Commands

- [x] Build `welinc-backend-vmms`
- [x] Run backend tests: 407 tests across 30 schedule/vehicle suites
- [x] Run changed-file backend lint
- [x] Build `welinc-web-vmms`
- [x] Run changed-file web lint
- [ ] Complete browser interaction acceptance for single and bulk odometer flows
- [ ] Verify analytics refresh and mobile snapshot reconciliation in runtime
- [ ] Verify default/override behavior across vehicle and category boundaries

## Acceptance-criteria coverage

- AC-1 through AC-9 by the API, state, spreadsheet, role, analytics, and mobile
  checks above.
