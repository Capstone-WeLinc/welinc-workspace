# Verify: Bulk fuel statement import · spec 0006

Steps derived from the acceptance criteria in [index.md](index.md).

## Workbook / UI

- [ ] Preview an `.xlsx` workbook with multiple sheets and varied supported
  header layouts; confirm preview creates no fuel entries → AC-1
- [ ] Map sheets to active registered stations and resolve vehicle plates only
  to active vehicles → AC-2
- [ ] Correct or fill required values for every row; confirm missing or unmatched
  values block only the affected row → AC-3
- [ ] Confirm PO number, SI number, and product are retained; printed total and
  remarks are not; saved totals use liters multiplied by unit price → AC-4
- [ ] Test current and historical odometer sequences, duplicate rows, stale
  vehicle/station state, and re-import behavior → AC-5, AC-7
- [ ] Confirm valid rows save independently and return per-row audit/anomaly
  effects; invalid rows return actionable failures → AC-6
- [ ] Close and reopen an Operations user's draft, including partial-save
  results; confirm another Operations user cannot access it → AC-8
- [ ] Confirm imported rows may omit filled-by, existing manual entry and
  receipt scanning remain compatible, and history/detail/export still work →
  AC-9

## API / security

- [ ] Confirm only Operations can preview or save workbook imports
- [ ] Reject malformed ZIP/workbooks, unsupported structures, oversized files,
  and requests above the import limits
- [ ] Confirm preview performs no persistence and save never trusts preview
  validation or client totals
- [ ] Confirm delete-draft affects only the draft and never saved fill-ups

## Commands

- [ ] Build and test `welinc-backend-vmms`
- [ ] Build and test `welinc-web-vmms`
- [ ] Run targeted parser, mapping, draft, and partial-save tests
- [ ] Run a representative workbook matrix covering supported and malformed
  sheets

## Acceptance-criteria coverage

- AC-1 through AC-9 by the workbook, review, persistence, security, and
  compatibility checks above.
