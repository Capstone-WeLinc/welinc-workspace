# Verification — 0017 Fuel operations reconciliation and anomaly follow-up

All checks are pending approval and implementation. They are derived from the
acceptance criteria in [index.md](index.md).

## Import reconciliation

- [ ] Save an import with all rows valid and confirm submitted/saved counts and
  saved liters/cost match backend results → AC-1, AC-2
- [ ] Save a partially valid import and confirm failed rows remain visible with
  their row-level errors and are excluded from saved totals → AC-1, AC-2
- [ ] Include duplicate and invalid rows; confirm they are not counted as saved
  and workbook printed totals are not used → AC-2
- [ ] Confirm another Operations user cannot view the draft or its results and
  that no workbook is retained → AC-3

## Anomaly follow-up

- [ ] Confirm open anomalies show first-detected time and age using the
  approved timezone/age convention → AC-4
- [ ] Confirm severity, status, vehicle, efficiency, rolling average, notes,
  and existing attachments remain accurate → AC-4
- [ ] Confirm age display causes no new alerts and does not alter existing
  escalation, acknowledgment, or resolution behavior → AC-5
- [ ] Verify Admin/Operations visibility and existing mutation permissions;
  verify other roles remain denied → AC-4, AC-5

## Regression and coverage

- [ ] Verify existing fuel entry, import, receipt, void, audit, and anomaly
  workflows remain compatible → AC-6
- [ ] Run focused web and backend checks for the changed surfaces and record
  runtime evidence.

## Acceptance-criteria coverage

| AC | Planned evidence |
| --- | --- |
| AC-1–AC-3 | Import result counts, totals, partial failure, and ownership checks |
| AC-4–AC-5 | Anomaly age display and unchanged role/escalation behavior |
| AC-6 | Existing fuel-flow regression checks |

## Implementation evidence

No implementation or verification has been performed for this proposal.
