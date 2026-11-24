# Rationale — 0018 Maintenance costing exports and analysis

## Context

VMMS scope marks Maintenance Costing in progress. The current web page supports
period selection, fleet KPIs, truck-level completed-work drill-down, PDF
export, and an Admin-only high-cost threshold form. The scope reconciliation
records fleet Excel export/runtime evidence and append-only dashboard/export
audit coverage as partial.

The existing costing domain is intended to aggregate eligible completed
maintenance records. The settings catalog retains the costing threshold's
existing domain source of truth. This proposal completes export/audit evidence
and adds analysis to the same costing dataset without expanding into
income/profit or cross-system repair data.

## Forces

- Report totals and exports must use the same completed/verified record set and
  period as the existing dashboard.
- Admin and Operations may view costing; only Admin may edit the threshold.
- Exported costs are sensitive management data; access and export actions need
  auditable metadata without duplicating report contents.
- Historical garage attribution may not be available on completed records.
- Trends and breakdowns must not imply unsupported historical or causal
  conclusions.

## Options considered

1. **Complete exports and add bounded analysis on the current costing dataset
   (recommended).** Reuse the existing period and eligible records; add an
   Excel workbook and derived views. Minimal contract impact if data is
   available.
2. **Replace the costing service with a new analytics/reporting model.**
   Could support broader reporting but increases data freshness, authorization,
   and cross-service complexity unnecessarily for this slice.
3. **Add only Excel export.** Closes the clearest output gap but leaves
   breakdown needs and report-audit questions unresolved.

## Proposed decision

Submit Option 1 for approval. Retain the current PDF, add a two-sheet Excel
export, compare the selected period with the immediately preceding equivalent
period, and add maintenance-type/garage breakdowns from eligible completed
records. Record completed exports in the existing append-only audit path; do
not audit background refreshes.

## Tradeoffs

- **Benefits:** stronger operational cost visibility, portable detail, and
  clearer export accountability without changing cost ownership.
- **Costs/limits:** the Excel output and breakdowns require parity testing; if
  historical garage or type data is absent, the UI must disclose that limit.
- **Excluded:** CSV unless separately approved, per-refresh audit events,
  profit/income calculations, VRMS repair costs, and fuel costs.

## Decisions awaiting approval

- Excel-only addition versus adding CSV as well.
- Preceding-period comparison rule and breakdown grouping by maintenance type
  and garage.
- Whether garage grouping may use current vehicle assignment when no
  historical garage-at-completion value exists; the proposal recommends clear
  labeling rather than historical claims.
- Whether to audit intentional report-page access in addition to exports and
  threshold changes.
- Confirm that only export metadata, not report values, belongs in audit
  details.
