# 0018. Maintenance costing exports and analysis

**Status**: Approved and implemented; migration deployment and runtime acceptance pending
**Scope**: [Maintenance costing](../../../scope/vmms/index.md#6-maintenance-costing)

Decision history: [rationale.md](rationale.md). Verification plan: [verify.md](verify.md).

## Summary

Complete costing exports and audit evidence, and add period and category
analysis to the existing read-only Maintenance Costing dashboard.
Existing rules for eligible completed work, threshold management, role access,
and exclusion of income/profit remain unchanged.

## Source requirements and related specifications

- VMMS Module 6, BR-20 to BR-22, FR-20.* to FR-22.*, SC-12, and SC-13.
- Existing [0009 Settings Catalog](../0009-settings-catalog/index.md) remains
  the source for the Admin-managed costing threshold.
- Existing append-only audit requirements remain authoritative; do not create
  a second audit store.

## Approved behavior

### Exports

- Keep the existing PDF export and add an `.xlsx` export for the selected
  period.
- The workbook contains a fleet summary and eligible completed-work detail;
  when a truck is selected, both sheets are limited to that truck.
- Exported rows, totals, flags, and period match the current dashboard data.
- Include the selected period and generation timestamp. Do not include income,
  profit, or revenue fields.

### Period and category analysis

- Compare the selected period with the immediately preceding equivalent
  period: previous calendar month, two-month block, half-year, or year for
  standard periods; for a custom range, use the immediately preceding range
  with the same inclusive number of Manila calendar days.
- Add breakdowns by maintenance type and garage for the selected period,
  using the same eligible completed records as the costing dashboard.
- Show total cost and completed-record count; preserve the existing truck
  drill-down and high-cost/recurring-candidate flags.
- Identify unavailable or unclassified categories rather than silently
  dropping their costs.
- If historical garage-at-completion data is unavailable, label the grouping
  as current garage assignment; do not imply historical attribution.

### Audit and access

- Continue to audit threshold changes through the existing domain audit path.
- Record each completed export with actor, export format, date range, and
  selected truck scope using the existing append-only VMMS audit mechanism.
- Do not audit intentional report-page access or background refreshes.
- CSV is not included.
- Admin and Operations retain report read access; only Admin can change the
  threshold. Backend authorization remains authoritative.

## Approval record

Approved by the user on 2026-11-26: retain PDF and add two-sheet `.xlsx`;
exclude CSV; use the stated preceding-equivalent-period rule and type/garage
breakdowns; label garage groups as current assignments; audit completed exports
and threshold changes but not page views or background refreshes; retain
Admin/Operations read access and Admin-only threshold changes.

An additive export-audit migration was separately approved because the
existing append-only costing audit records threshold changes only.

## API, data, and migration impact

- Reuse the existing maintenance costing API and its eligible completed-work
  dataset where it contains the fields needed for the proposed breakdowns.
- If data or audit fields are missing, prefer additive VMMS-only service/API
  changes that preserve existing response contracts.
- Add `maintenance_costing_export_audit` for approved export metadata and
  protect it with the existing append-only database trigger. No historical
  garage snapshot is added; garage analysis uses and labels current assignments.
- No shared auth, portal, gateway, analytics service, mobile, or cross-system
  change is included.

## Security and failure behavior

- Keep Admin/Operations read authorization and Admin-only threshold mutation
  enforced by the backend.
- Export only the rows authorized and visible for the selected period/scope.
- Audit metadata only; do not copy costs or full report contents into audit
  detail fields.
- Surface export and analysis failures explicitly; do not present partial
  totals as complete.

## Affected repositories

- `welinc-web-vmms`: Excel export, period comparison, and type/garage breakdown UI.
- `welinc-backend-vmms`: XLSX generation, export auditing, and the additive
  export-audit migration.
- VMMS-owned specs; update the VMMS scope status only after approval and
  evidence-based implementation.

## Acceptance criteria

1. Admin and Operations can export the current selected costing period to PDF
   and `.xlsx`; CSV is excluded.
2. The workbook summary and detail rows match the dashboard's period,
   eligibility rules, totals, and flags; truck selection scopes both sheets.
3. Period comparison uses the approved preceding-period rule and the same
   eligible completed-cost definition as the selected dashboard period.
   Type/garage breakdowns match the selected period.
4. Missing categories remain represented as unclassified; garage attribution
   is labeled accurately and is not presented as historical without source
   data.
5. Export events are recorded with approved metadata in the existing
   append-only audit mechanism; page views and background refreshes are not
   audited.
6. Admin/Operations read access, Admin-only threshold changes, and threshold
   audit behavior remain intact.
7. No income, profit, revenue, VRMS repair, or fuel costs are included.

## Verification plan and status

- Verification status and remaining runtime checks are listed in
  [verify.md](verify.md).
- Backend and web implementation is complete. Automated verification passed;
  database migration deployment and interactive acceptance remain pending.
