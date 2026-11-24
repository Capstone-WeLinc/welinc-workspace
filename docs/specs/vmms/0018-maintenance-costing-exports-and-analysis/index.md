# 0018. Maintenance costing exports and analysis

**Status**: Draft for approval; implementation is not authorized
**Scope**: [Maintenance costing](../../../scope/vmms/index.md#6-maintenance-costing)

Decision history: [rationale.md](rationale.md). Verification plan: [verify.md](verify.md).

## Summary

Propose completing costing exports and audit evidence, then adding period and
category analysis to the existing read-only Maintenance Costing dashboard.
Existing rules for eligible completed work, threshold management, role access,
and exclusion of income/profit remain unchanged.

## Source requirements and related specifications

- VMMS Module 6, BR-20 to BR-22, FR-20.* to FR-22.*, SC-12, and SC-13.
- Existing [0009 Settings Catalog](../0009-settings-catalog/index.md) remains
  the source for the Admin-managed costing threshold.
- Existing append-only audit requirements remain authoritative; do not create
  a second audit store.

## Proposed behavior

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
- Do not record each background refresh as a report-view event. Whether to
  audit intentional report-page access is an approval decision.
- Admin and Operations retain report read access; only Admin can change the
  threshold. Backend authorization remains authoritative.

## Approval requested

1. Approve the two-sheet `.xlsx` export while retaining the existing PDF.
   Confirm whether CSV is also required.
2. Approve equivalent-period comparison and type/garage breakdowns, including
   the custom-range comparison rule and current-garage labeling when historical
   attribution is unavailable.
3. Approve audit events for completed exports; decide whether intentional
   report-page access should also be audited. Background refreshes are excluded.
4. Confirm existing Admin/Operations read access and Admin-only threshold
   changes.

## API, data, and migration impact

- Reuse the existing maintenance costing API and its eligible completed-work
  dataset where it contains the fields needed for the proposed breakdowns.
- If data or audit fields are missing, prefer additive VMMS-only service/API
  changes that preserve existing response contracts.
- No schema migration is planned unless approval and implementation discovery
  demonstrate that required historical breakdown data cannot be derived.
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

- `welinc-web-vmms`: Excel export, monthly trend, and type/garage breakdown UI.
- `welinc-backend-vmms`: only if existing costing data or audit capabilities
  cannot support the approved behavior.
- VMMS-owned specs; update the VMMS scope status only after approval and
  evidence-based implementation.

## Acceptance criteria

1. Admin and Operations can export the current selected costing period to PDF
   and `.xlsx`; CSV behavior follows the approval decision.
2. The workbook summary and detail rows match the dashboard's period,
   eligibility rules, totals, and flags; truck selection scopes both sheets.
3. Period comparison uses the approved preceding-period rule and the same
   eligible completed-cost definition as the selected dashboard period.
   Type/garage breakdowns match the selected period.
4. Missing categories remain represented as unclassified; garage attribution
   is labeled accurately and is not presented as historical without source
   data.
5. Export events are recorded with approved metadata in the existing audit
   system; page-view auditing follows the approval decision.
6. Admin/Operations read access, Admin-only threshold changes, and threshold
   audit behavior remain intact.
7. No income, profit, revenue, VRMS repair, or fuel costs are included.

## Verification plan and status

- Planned checks are listed in [verify.md](verify.md).
- No implementation or acceptance evidence is claimed by this draft.
- Existing costing correctness and role tests remain applicable; this proposal
  adds export parity, breakdown accuracy, and audit checks.
