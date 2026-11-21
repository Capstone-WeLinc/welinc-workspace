# 0006. Bulk fuel statement import

**Status**: Approved for implementation
**Scope**: [Module 5: Fuel expenses and anomaly handling](../../../scope/vmms/index.md)

## Summary

Operations can import a multi-row fuel billing workbook, review and edit each
proposed fill-up, then save valid rows with explicit row-level results. The
existing single fill-up and optional single-receipt scanning flows remain
available.

## Decisions

- Import `.xlsx` workbooks; do not infer multiple fill-ups from the existing
  single-receipt OCR flow.
- Support multiple worksheets with different column layouts. Match recognized
  columns by header labels and show unsupported or absent values as fields that
  need review.
- Map each worksheet to an active registered fuel station during review.
- Match vehicle plates to active registered vehicles; require users to correct
  unmatched plates before saving.
- Let reviewers add manual rows and remove unsaved draft rows. Manual rows use a
  separate worksheet mapping so they still require an active registered fuel
  station; saved fill-ups cannot be removed from the import review.
- Persist import and manual-entry drafts on the backend, grouped by source file
  and worksheet, and scope each draft to the Operations user who created it.
  Keep partially submitted drafts available with per-row results until all rows
  are saved or the owner deletes the draft; the workbook itself is not retained.
- Require the reviewer to provide or confirm odometer, full-tank, station, and
  all other required values for each row.
- Allow `filledBy` to be blank for imported rows; ordinary single fuel entries
  continue to require it.
- Retain optional PO number, SI number, and product on each fill-up. Do not
  persist statement remarks or printed total. VMMS calculates the saved total
  from liters and unit price.
- Permit historical rows only when their odometer reading fits the vehicle's
  date-ordered fuel history. Never lower or overwrite the vehicle master
  odometer.
- Apply valid rows independently. A failed row must not roll back other
  successful rows; return a result for each submitted row.

## Import and review flow

1. Operations selects an `.xlsx` workbook from Fuel Management.
2. VMMS reads recognized transaction columns from each worksheet and returns
   candidate rows without writing data.
3. The reviewer maps each worksheet to a registered station, selects an active
   registered vehicle by plate for each row, and fills or confirms required
   values, including the full-tank flag. The filled-by name is optional for
   imports. Pagination shows the visible row range and current page; adding a
   manual row opens and highlights its page. The reviewer can remove unsaved
   rows; saved rows remain read-only.
4. The preview identifies malformed, incomplete, duplicate, or inconsistent
   rows. The reviewer can edit candidate values before explicit submission.
   Changes are saved to a private, resumable draft grouped by source file and
   worksheet; Operations can reopen or delete their own drafts. Deleting a
   draft never deletes fuel fill-ups already saved from it.
5. On save, the backend revalidates every row against current vehicles,
   stations, existing fuel history, and other submitted rows. Each valid row
   is committed with the existing fuel audit and anomaly behavior. VMMS
   returns saved or failed status per row.
6. Existing single-entry JSON creation and optional single-receipt scanning
   continue to work unchanged.

## Workbook mapping

Recognize date, plate number, PO number, odometer, SI number, product, liters,
and unit price when present. Header aliases are case-insensitive and ignore
punctuation and spacing. Interpret text dates in `DD/MM/YYYY` order, and reject
invalid calendar dates for manual correction. Skip blank rows and summary rows
such as total amount, amount to be paid, subtotal, and grand total; report rows
that appear to contain a transaction but are malformed. List populated
worksheets without supported transaction headers so staff can see when a sheet
was skipped. Validate values against their mapped field types and require
transaction-shaped evidence (a plausible plate with a date or numeric
measurement, or a valid date with both positive fuel amounts) before including
a row; arbitrary footer text and isolated numeric totals are not transactions.
Printed total is not authoritative and is not stored. Any source value the
parser cannot interpret must remain editable or visibly require manual entry.

## API and data impact

- Add Operations-only workbook preview and row-save endpoints under `/fuel`.
- Preview performs no persistence. The save endpoint accepts reviewed data,
  revalidates it, and returns per-row results rather than treating partial
  failure as success.
- Preview remains read-only; the client creates a draft from its result.
- Import drafts persist reviewed row data and per-sheet station mappings, but
  never the source workbook. Only the creating Operations user can list, read,
  update, or delete a draft. Partial imports retain saved/failed row results;
  completed drafts are removed, while deleting a draft never affects saved
  fuel records.
- Bound JSON request bodies to 2 MiB to support the reviewed 1,000-row import
  limit; retain the existing 100 KiB limit for URL-encoded request bodies.
- Add nullable `po_number`, `si_number`, and `product` columns to
  `fuel_fill_ups` through an additive Prisma migration.
- Include these fields in fuel responses and relevant fuel-log details and
  exports. Existing records remain valid with null values.
- Use the existing fuel create, audit, storage, and anomaly boundaries where
  applicable; imports do not attach or retain the source workbook.
- The backend continues to calculate total cost. No analytics, mobile, shared
  auth, portal, gateway, or cross-system contract change is required.

## Security and failure behavior

- Only Operations can preview and save workbook imports.
- Restrict the upload to bounded `.xlsx` files, validate the ZIP/workbook
  structure using the existing ExcelJS dependency, and cap transaction rows.
- Never trust workbook vehicle/station names, client totals, or preview
  validation during save.
- Reject unknown/inactive vehicles and stations, incomplete fields, duplicate
  rows, invalid values, and odometer sequences that conflict with existing or
  newly submitted entries.
- Keep row errors explicit and actionable. Do not persist the workbook.
- Preserve the current no-lower-odometer rule for ordinary single-entry saves.

## Acceptance criteria

1. Operations can preview an `.xlsx` workbook with multiple sheets and varied
   supported header layouts without creating fuel entries.
2. Each sheet can be mapped to an active registered station; vehicle plates
   resolve only to active registered vehicles.
3. All required fuel fields are visible and editable per row. Missing or
   unmatched values block that row until corrected.
4. PO number, SI number, and product are retained; printed total and remarks
   are not persisted, and VMMS calculates total cost.
5. Save revalidates rows, permits only date-consistent historical odometer
   readings, and does not change the vehicle master odometer.
6. Valid rows save independently with fuel audit and existing anomaly
   behavior. Invalid rows return row-specific errors without rolling back
   unrelated rows.
7. Re-importing duplicate transactions does not create silent duplicate
   fill-ups.
8. Operations can close and reopen their own import drafts, including drafts
   with partial save results; another Operations user cannot access them.
9. Imported rows may omit filled-by; other required fields still block saving.
   Existing manual fuel entry, receipt scanning, reporting, authorization, and
   fuel history behavior remain compatible.

## Affected repositories

- `welinc-backend-vmms`: workbook parsing and validation, Operations-only
  preview/save APIs, historical sequence checks, additive fields migration,
  and response mapping.
- `welinc-web-vmms`: workbook selection, editable row review, station mapping,
  row validation/results, and fuel-log display/export of retained fields.

## Verification plan

- Verify varied header layouts and malformed workbook/row handling.
- Verify no writes during preview, row edit propagation, per-sheet station
  mapping, active vehicle matching, and Operations-only authorization.
- Verify current and historical odometer sequence cases, duplicate imports,
  partial success, audit/anomaly effects, and unchanged vehicle master
  odometer.
- Verify manual entry, receipt scanning, fuel history, detail view, and
  exports continue to work.
