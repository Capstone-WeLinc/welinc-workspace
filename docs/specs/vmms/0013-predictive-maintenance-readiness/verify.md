# Verify: Predictive maintenance readiness · spec 0012

Steps derived from the acceptance criteria in [index.md](index.md).

## Seed data

- [ ] Run the seed twice against an empty development database; confirm the
  same fixtures exist without duplicate schedules, checklist items, or
  odometer audit rows → AC-6, AC-7
- [ ] Run the seed against a populated development database; confirm existing
  vehicle, schedule, checklist, and audit values are not deleted, overwritten,
  or reactivated → AC-6
- [ ] Verify every seeded schedule's plate and garage value match a registered
  vehicle, and linked work-order, mechanic, checklist, and recurrence records
  resolve through existing schema fields → AC-6
- [ ] Seed on an empty development database and confirm maintenance dates are
  relative to the Manila seed day, fixture IDs remain stable, completion
  snapshots anchor successors, and cancelled occurrences have no successor
  → AC-6, AC-9

## Schedule form

- [ ] Create an odometer/manual schedule and confirm Due Date is the only
  editable top-level date; verify internal `startDate` is the Manila creation
  day → AC-1
- [ ] Create a time schedule and verify internal `startReferenceDate`
  derives from Due Date and the chosen interval, including month-end dates
  → AC-2
- [ ] Edit a schedule and confirm its internal `startDate` remains unchanged;
  confirm due-date audit and recurrence behavior remain intact → AC-1, AC-2

## Predictions

- [ ] Verify Admin, Chief Mechanic, and Mechanic are denied while Operations
  can retrieve predictions → AC-3
- [ ] Verify history with fewer than three readings, less than 30 days'
  span, an out-of-window reading, a stale latest reading, or non-increasing
  values yields no prediction → AC-4
- [ ] Verify median-rate calculations, due distances, Manila dates, the
  zero-to-30-day horizon, and omission of already-due/overdue or closed
  schedules → AC-3, AC-4
- [ ] Verify the web panel links to the existing schedule and causes no
  writes, status changes, or notifications → AC-5
- [ ] Verify single and bulk vehicle master-reading changes still refresh
  schedule status transactionally, without a new polling writer → AC-8

## Commands and runtime

- [x] Backend `npm run build` passed; targeted TypeScript checking of Prisma
  seed modules passed. No database seed was executed.
- [x] Web `npm run build` passed, including TypeScript project checks and
  production bundle generation. Vite reported the existing large-chunk
  advisory.
- [x] Impeccable mechanical UI detector returned no findings for the changed
  schedule screens.
- [ ] Run the focused prediction and seed behavior checks. They were not run
  under the VMMS repository's test policy.
- [x] Re-ran focused prediction service checks on 2026-11-24:
  `npx jest src/modules/vmms/maintenance-schedules/maintenance-predictions.spec.ts --runInBand`
  passed with 5 tests covering valid median estimate, stale history,
  non-increasing history, insufficient history, and malformed readings.
- [ ] Verify the Operations panel and schedule form in an authenticated local
  VMMS. The local web app loaded, but the shared sign-in service was
  unreachable, so the protected screen could not be opened.
- [ ] Verify API authorization and prediction output in a local integrated VMMS
  environment; do not use production.

## Acceptance-criteria coverage

- AC-1–2: schedule form, date derivation, audit, and recurrence checks.
- AC-3–5: API role, prediction rules, and read-only web behavior.
- AC-6–7: repeatable, relationally consistent synthetic seed.
- AC-8: existing transactional status-refresh regression checks.
