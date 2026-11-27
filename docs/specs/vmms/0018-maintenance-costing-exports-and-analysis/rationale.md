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

## Approved decision

On 2026-11-26, the user approved Option 1. Retain the current PDF, add a two-sheet Excel
export, compare the selected period with the immediately preceding equivalent
period, and add maintenance-type/garage breakdowns from eligible completed
records. Record completed exports in the existing append-only audit path; do
not audit background refreshes.

The user also decided not to audit page views and not to add CSV. Because the
existing costing audit model only stores threshold changes, the user approved
an additive VMMS export-audit table protected by the same append-only database
trigger. No historical garage-at-completion data is added; garage breakdowns
are explicitly labeled as current vehicle assignments.

## Tradeoffs

- **Benefits:** stronger operational cost visibility, portable detail, and
  clearer export accountability without changing cost ownership.
- **Costs/limits:** the Excel output and breakdowns require parity testing;
  the garage breakdown is a current-assignment view, not historical
  attribution.
- **Excluded:** CSV unless separately approved, per-refresh audit events,
  profit/income calculations, VRMS repair costs, and fuel costs.

## Implementation decisions

- CSV remains excluded; no page-view or background-refresh audit is written.
- Export metadata stores actor, format, date range, and optional truck ID/plate;
  it never stores report costs or row contents.
- The database migration is additive and uses the existing append-only audit
  trigger. It has not yet been applied to a runtime database.
