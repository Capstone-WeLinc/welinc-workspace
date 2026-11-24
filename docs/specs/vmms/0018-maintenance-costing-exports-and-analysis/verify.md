# Verification — 0018 Maintenance costing exports and analysis

All checks are pending approval and implementation. They are derived from the
acceptance criteria in [index.md](index.md).

## Data and period correctness

- [ ] Use a fixed set of eligible completed records and confirm fleet and
  truck totals for monthly, bimonthly, semiannual, annual, and custom periods
  → AC-2, AC-3
- [ ] Confirm records outside the period and ineligible statuses are excluded
  from KPIs, breakdowns, and exports → AC-2, AC-3
- [ ] Confirm comparison periods follow the approved standard/custom range
  rule, use Manila date boundaries, and use the same eligible-cost definition
  as the dashboard → AC-3
- [ ] Verify missing type/garage values are represented as unclassified and
  current-garage attribution is labeled accurately → AC-4

## Export and audit

- [ ] Export PDF and `.xlsx`; compare summary totals, detail rows, flags, date
  range, and truck-selection scope with the screen → AC-1, AC-2
- [ ] Confirm income, profit, revenue, VRMS repair, and fuel fields are absent
  → AC-7
- [ ] Confirm each completed export records the approved actor, format, period,
  and scope metadata without report amounts → AC-5
- [ ] Verify intentional report-page access behavior and ensure background
  refreshes do not create view events → AC-5

## Authorization and compatibility

- [ ] Admin and Operations can read costing; Operations cannot update the
  threshold; non-authorized roles are denied by the API → AC-6
- [ ] Confirm Admin threshold updates still persist and use the existing audit
  path → AC-6
- [ ] Confirm failure states do not show partial totals as successful output
  and the existing PDF and drill-down remain compatible → AC-1, AC-2

## Acceptance-criteria coverage

| AC | Planned evidence |
| --- | --- |
| AC-1–AC-2 | PDF/Excel output and dashboard data-parity checks |
| AC-3–AC-4 | Period trend, category breakdown, and attribution checks |
| AC-5 | Append-only audit metadata and view-event policy checks |
| AC-6 | Admin, Operations, and denied-role API checks |
| AC-7 | Export-field and data-source review |

## Implementation evidence

No implementation or verification has been performed for this proposal.
