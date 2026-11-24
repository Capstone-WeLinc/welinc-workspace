# 0020. Fuel reports filtering and efficiency

**Status**: Draft for approval; implementation is not authorized
**Scope**: [Reports and fleet dashboard](../../../scope/vmms/index.md#7-reports-and-fleet-dashboard)

Decision history: [rationale.md](rationale.md). Verification plan: [verify.md](verify.md).

## Summary

Propose making Fuel Reports period filters, anomaly results, efficiency
summaries, exports, and visible data states consistent. Keep the existing
fleet-wide, per-vehicle, and anomaly report views and use the core VMMS fuel
service as the authority for fuel records and access.

## Source requirements and related specifications

- VMMS Module 7, BR-23 to BR-26, FR-23.* to FR-26.*, SC-14, and SC-15.
- Fuel calculation, voiding, and role behavior from [Module 5](../../../scope/vmms/index.md#5-fuel-expenses-and-anomaly-handling)
  and [0005 Fuel receipt scanning](../0005-fuel-receipt-scanning/index.md).
- Existing scheduled summaries remain defined by the
  [scheduled reports specification](../../../../welinc-backend-vmms/docs/specs/vmms/scheduled-reports-and-escalations/index.md).

## Proposed behavior

### Period filters and data states

- Interpret the selected report period as Manila calendar dates on fuel-entry
  date. Use the existing core `/fuel/report` date parameters where supported
  rather than downloading the full history for client-side filtering.
- Apply the effective period to fleet-wide totals, per-vehicle summaries,
  anomaly results, and exports.
- For anomaly results, use the linked fill-up entry date for period membership;
  display the anomaly's detected date separately.
- Show the effective period, loading state, visible recoverable errors, and
  empty state. Do not show an empty report when the source request failed.

### Efficiency

- Exclude voided entries and use only efficiency values produced by the
  existing full-tank-cycle calculation.
- Define fleet efficiency as total valid distance divided by total valid fuel
  for eligible cycles, not a simple average of per-fill-up km/L values.
- Preserve `Insufficient Data` when the required full-tank history is absent.
  Show the valid cycle count and clearly label km/L.

### Exports and audit

- Add CSV export for fleet-wide, per-vehicle, and anomaly report views, while
  retaining existing PDF/Excel formats where available.
- Match export rows and totals to the visible report, including date range,
  void exclusion, vehicle filters, and anomaly state filters.
- Record the effective date range for preset and custom periods, report view,
  format, and actor in the existing fuel report export audit event.
- Do not add a new audit store or log report data values.

## Approval requested

1. Approve Manila fuel-entry-date filtering for report periods and linked
   fill-up-date filtering for anomalies.
2. Approve distance/fuel-weighted fleet efficiency based on valid full-tank
   cycles, with insufficient-data handling retained.
3. Approve CSV export for all three report views and parity with existing
   PDF/Excel output.
4. Confirm export audit records should include effective preset/custom dates,
   report view, format, and actor.

## API, data, and migration impact

- Prefer existing core VMMS fuel report date parameters and anomaly/fill-up
  response fields.
- Additive response or query changes may be needed only if the current API
  cannot return valid-cycle totals or filter anomaly results by linked
  fill-up date.
- No new schema or migration is planned. Do not move current fuel-record
  authority to the analytics service.

## Security and failure behavior

- Preserve Admin/Operations report access and backend authorization.
- Keep voided records out of operational totals and exports.
- Surface invalid date ranges and API failures explicitly; do not silently
  substitute all-time results.
- Export only authorized, filtered fields; exclude income/profit data.

## Affected repositories

- `welinc-web-vmms`: period state, report summaries, CSV export, error/empty
  states, and export metadata.
- `welinc-backend-vmms`: only if a required date-filter or valid-cycle
  aggregate is unavailable from existing routes.
- No shared service, portal, gateway, analytics authority, mobile, or
  cross-system change is included.

## Acceptance criteria

1. Period filtering uses Manila entry-date boundaries and applies to all report
   views and exports.
2. Anomaly rows are filtered by linked fill-up date and separately show their
   detection date.
3. Fuel summaries exclude voided records and aggregate valid full-tank-cycle
   distance and fuel consistently; insufficient data remains explicit.
4. CSV/PDF/Excel results match the visible filtered report and selected view.
5. Export audit events record the approved effective period, view, format, and
   actor without storing report contents.
6. Loading, error, empty, and invalid-range states are distinguishable; API
   failure never appears as a successful empty report.
7. Admin/Operations access and existing fuel-entry, voiding, anomaly, and
   escalation rules remain unchanged.

## Verification plan and status

- Planned checks are listed in [verify.md](verify.md).
- No implementation or acceptance evidence is claimed by this draft.
- Scope status must only be reconciled after approval and verified evidence.
