# 0017. Fuel operations reconciliation and anomaly follow-up

**Status**: Draft for approval; implementation is not authorized
**Scope**: [Fuel expenses and anomaly handling](../../../scope/vmms/index.md#5-fuel-expenses-and-anomaly-handling)

Decision history: [rationale.md](rationale.md). Verification plan: [verify.md](verify.md).

## Summary

Propose two small web improvements to Fuel Management: a clear reconciliation
summary after a statement import, and better visibility into the age of open
fuel anomalies. These extend the existing fuel-entry, import, and escalation
flows; they do not reopen or replace the approved baseline fuel requirements.

## Source requirements and related specifications

- VMMS Module 5, BR-16 to BR-19, FR-16.* to FR-19.*, SC-10, SC-11, SC-22, and
  SC-24 to SC-26.
- Existing approved specs: [0005 Fuel receipt scanning](../0005-fuel-receipt-scanning/index.md),
  [0006 Bulk fuel statement import](../0006-bulk-fuel-statement-import/index.md),
  and [0007 Fuel station management](../0007-fuel-station-management/index.md).
- Existing report and escalation behavior remains authoritative; this proposal
  does not alter fuel calculations, anomaly thresholds, status transitions, or
  the 1/3/7-day notification schedule.

## Proposed behavior

### Import reconciliation

- After an import save, show a summary of submitted, saved, and failed rows,
  grouped by worksheet and station where that information is already available.
- Show liters and VMMS-calculated cost totals for saved rows only. Clearly
  separate failed rows; never use a workbook's printed total as an authoritative
  amount.
- Keep row-level outcomes and actionable errors available. A summary must not
  turn partial success into a success-shaped result.
- Only the Operations user who owns the import draft can see its review and
  results. Do not add a retained import-history report or store the workbook.

### Anomaly follow-up

- Add an open-anomaly table/queue that includes vehicle, efficiency, rolling
  average, severity, status, first-detected time, and age in days.
- Keep existing notes, attachments, acknowledgment, resolution, access rules,
  and escalation behavior. Age is informational and does not create a new SLA
  or trigger notifications.
- Admin and Operations may review the queue; preserve the existing role
  permissions for edits, acknowledgments, and resolution.

## Approval requested

1. Approve an import result summary that is shown only in the current import
   flow, with no persistent history or new file retention.
2. Approve anomaly age as an informational value using the existing
   Asia/Manila escalation clock; no new age thresholds or notifications.
3. Confirm that existing Admin/Operations visibility and Operations-owned
   import isolation remain the intended access rules.

## API, data, and migration impact

- Prefer the existing import row results and anomaly response fields.
- No new database table, migration, file retention, or API contract is planned.
- If existing API responses cannot support the approved view, stop and propose
  the smallest VMMS-only API addition before implementation.

## Security and failure behavior

- Enforce import ownership and existing Operations-only import authorization at
  the backend boundary.
- Do not expose one Operations user's draft or import results to another.
- Preserve explicit per-row failure results and existing anomaly role rules.
- Do not include receipt images, raw OCR text, or unrelated personal data in
  summaries or logs.

## Affected repositories

- `welinc-web-vmms`: import result presentation and anomaly queue.
- `welinc-backend-vmms`: only if a required existing response field is missing.
- No shared service, analytics, mobile, portal, gateway, or other-system change
  is included.

## Acceptance criteria

1. After an import save, the UI shows submitted, saved, and failed row counts
   consistent with row-level results.
2. Import totals include only successfully saved rows and use VMMS-calculated
   values; failed rows remain distinguishable.
3. Import review and results remain restricted to the draft-owning Operations
   user; the source workbook is not retained.
4. Open anomalies show the first-detected time and age alongside existing
   vehicle, efficiency, severity, status, and resolution context.
5. Age display does not change escalation timing, notification recipients,
   anomaly status, or acknowledgment/resolution policy.
6. Existing fuel entry, import, receipt scanning, voiding, audit, and anomaly
   workflows remain compatible.

## Verification plan and status

- Planned checks are listed in [verify.md](verify.md).
- No implementation or acceptance evidence is claimed by this draft.
- Existing completion work for specs 0005, 0006, and 0007 remains tracked in
  those specs and is not replaced by this proposal.
