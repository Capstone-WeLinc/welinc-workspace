# Verification — 0017 Fuel operations reconciliation and anomaly follow-up

Checks are derived from the acceptance criteria in [index.md](index.md).
Automated implementation evidence is recorded below; live runtime and
cross-user acceptance remain pending.

## Import reconciliation

- [ ] Save an import with all rows valid and confirm submitted/saved counts and
  saved liters/cost match backend results → AC-1, AC-2
- [ ] Confirm each successful row's response `totalCost` equals its persisted
  VMMS fill-up total; worksheet/station summaries use saved rows only → AC-1,
  AC-2
- [ ] Save a partially valid import and confirm failed rows remain visible with
  their row-level errors and are excluded from saved totals → AC-1, AC-2
- [ ] Include duplicate and invalid rows; confirm they are not counted as saved
  and workbook printed totals are not used → AC-2
- [ ] Confirm another Operations user cannot view the draft or its results and
  that no workbook is retained → AC-3

## Anomaly follow-up

- [x] Confirm open anomalies show first-detected time and age using the
  elapsed-24-hour convention and existing escalation thresholds → AC-4
- [x] Test just below and at the 1-, 3-, and 7-day elapsed thresholds,
  including timestamps around Manila midnight → AC-4, AC-5
- [ ] Confirm severity, status, vehicle, efficiency, rolling average, notes,
  and existing attachments remain accurate → AC-4
- [ ] Confirm age display causes no new alerts and does not alter existing
  escalation, acknowledgment, or resolution behavior → AC-5
- [ ] Verify Admin/Operations visibility and existing mutation permissions;
  verify other roles remain denied → AC-4, AC-5

## Regression and coverage

- [ ] Verify existing fuel entry, import, receipt, void, audit, and anomaly
  workflows remain compatible → AC-6
- [x] Run focused web and backend tests/builds for the changed surfaces; see
  implementation evidence below. Live API/database runtime evidence remains
  pending.

## Acceptance-criteria coverage

| AC | Planned evidence |
| --- | --- |
| AC-1–AC-3 | Import result counts, totals, partial failure, and ownership checks |
| AC-4–AC-5 | Anomaly age display and unchanged role/escalation behavior |
| AC-6 | Existing fuel-flow regression checks |

## Implementation evidence

Implemented the additive backend row total and transient web reconciliation
summary, plus first-detected time and elapsed-day age for open anomalies.

Focused automated checks:

- Backend `npm test -- --runInBand src/modules/vmms/fuel/fuel.service.spec.ts`:
  1 suite, 6 tests passed. This includes a successful import row receiving a
  `totalCost` from the mocked `create()` return value that differs from
  workbook arithmetic.
- Backend `npm run build`: passed.
- Backend `npx eslint src/modules/vmms/fuel/fuel.service.spec.ts`: passed.
  ESLint on the changed service and test also reported 44 existing
  `prettier/prettier` formatting findings in `fuel.service.ts`; no broad
  formatting changes were made.
- Web focused Vitest command
  (`npx vitest run src/pages/FuelManagement/components/ImportFuelStatement.test.tsx src/pages/FuelManagement/FuelManagement.test.tsx`):
  2 files, 25 tests passed. Coverage includes all-success and partial-success
  summaries, worksheet/station grouping, failed-row error visibility and
  exclusion from totals, anomaly display, and elapsed 1/3/7-day boundaries.
- Web `npm run build` and targeted ESLint on all changed web files: passed.

The UI tests use mocked API responses. Live API/database persistence,
cross-Operations-user draft isolation, browser acceptance, and runtime
notification/escalation behavior have not been reverified by this change.
