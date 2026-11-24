# Rationale — 0020 Fuel reports filtering and efficiency

## Context

The Fuel Reports view has fleet-wide, per-vehicle, and anomaly sections. The
page applies the selected period to fill-up data locally, but anomaly results
are loaded separately and are not visibly bound to that period. The core fuel
report API accepts date parameters, while the page currently requests the
report without them.

Fuel calculations are based on valid consecutive full-tank cycles, and voided
records are excluded from operational totals. A simple mean of per-fill-up
efficiency values can differ from total valid distance divided by total valid
fuel. Fuel report exports also need consistent filter metadata and format
coverage.

## Forces

- The core VMMS fuel service owns fuel records, void status, and access rules.
- Anomaly and fuel-entry periods need a clear date meaning; anomaly
  creation/detection can occur after the linked fill-up.
- Efficiency must preserve the existing full-tank validation and
  insufficient-data rules.
- Export contents and audit metadata must match what the user actually
  selected, including preset periods.
- Analytics remains a derived read model, not the authority for current fuel
  records or authorization.

## Options considered

1. **Use entry-date periods, linked-fill-up anomaly filtering, and
   distance/fuel-weighted efficiency (recommended).** Aligns reports to the
   fuel transaction and existing cycle-based calculation.
2. **Filter anomalies by detection date and average displayed efficiency
   values.** Simple but can show anomalies whose fuel event falls outside the
   selected period and can skew fleet efficiency.
3. **Keep all filtering client-side.** Requires no API work but transfers
   unnecessary history and makes scale and failure states harder to manage.

## Proposed decision

Submit Option 1 for approval. Use Manila calendar-date boundaries on the
linked fuel entry, report anomaly detection dates separately, and calculate
fleet efficiency from valid cycle distance and fuel. Use server-side date
filtering where the current core endpoint supports it, and keep the
authorization and source of truth in the core VMMS service.

## Tradeoffs

- **Benefits:** comparable period totals, consistent anomaly context, less
  unnecessary data transfer, and more meaningful fleet efficiency.
- **Costs/limits:** the API may need a small additive aggregate if valid-cycle
  distance and fuel totals are not currently exposed.
- **Excluded:** new anomaly escalation policy, new fuel data model, analytics
  service authority, and income/profit reporting.

## Decisions awaiting approval

- Use linked fill-up date or anomaly detection date for period membership;
  the proposal recommends linked fill-up date.
- Use distance/fuel-weighted fleet efficiency from valid full-tank cycles.
- Add CSV for each fuel report view and audit effective preset/custom ranges.
- Confirm failed date-filter requests must show an error rather than fall back
  to all-time data.
