# Verification — 0018 Maintenance costing exports and analysis

The feature is approved and implemented. Automated evidence below is complete;
runtime deployment and interactive acceptance checks remain open. Checks are
derived from the acceptance criteria in [index.md](index.md).

## Data and period correctness

- [ ] Use a fixed set of eligible completed records and confirm fleet and
  truck totals for monthly, bimonthly, semiannual, annual, and custom periods
  → AC-2, AC-3
- [ ] Confirm records outside the period and ineligible statuses are excluded
  from KPIs, breakdowns, and exports → AC-2, AC-3
- [x] Unit tests verify preceding month, two-month block, half-year, annual,
  and same-inclusive-day custom comparison ranges → AC-3
- [x] Breakdown tests verify cost/count grouping and preserve missing type and
  garage values as unclassified; UI and workbook label current garage
  attribution accurately → AC-4

## Export and audit

- [ ] In browser, export PDF and `.xlsx`; compare summary totals, detail rows,
  flags, date range, and truck-selection scope with the screen → AC-1, AC-2
- [x] Backend workbook test verifies two sheets, selected-truck scope, totals,
  high-cost flag, completed-work detail, and exclusion of income/profit/revenue,
  repair, and fuel data → AC-2, AC-7
- [x] API/service tests verify PDF/XLSX export authorization and append-only
  audit metadata; the Admin audit endpoint maps export records without amounts
  → AC-5
- [x] Page views and background refreshes create no events by design → AC-5
- [ ] Apply the new database migration and verify export records appear in the
  deployed Admin business-audit view → AC-5

## Authorization and compatibility

- [x] Backend role tests verify Admin/Operations read and export access,
  denied mechanic roles, and Admin-only threshold updates → AC-6
- [x] Service test verifies Admin threshold updates persist and use the existing
  threshold audit path; live database acceptance remains pending → AC-6
- [ ] In browser, verify failure states do not show partial totals as
  successful output and existing PDF/drill-down remain compatible → AC-1, AC-2

## Automated evidence

- Backend: costing service/controller and audit controller tests passed
  (20 tests); backend production build and Prisma Client generation passed.
- Web: period and breakdown tests passed (5 tests); production build passed.
- Migration is authored but has not been applied. Browser/runtime acceptance
  has not been performed.

## Acceptance-criteria coverage

| AC | Evidence/status |
| --- | --- |
| AC-1–AC-2 | Automated workbook and role checks passed; browser parity pending |
| AC-3–AC-4 | Period/breakdown unit tests passed; runtime data parity pending |
| AC-5 | Audit API/service coverage passed; migration deployment pending |
| AC-6 | Role and threshold API tests passed; runtime acceptance pending |
| AC-7 | Workbook exclusion assertions passed; browser export review pending |
