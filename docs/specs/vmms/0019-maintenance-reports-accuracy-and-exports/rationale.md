# Rationale — 0019 Maintenance report accuracy and exports

## Context

The current Maintenance Reports page combines schedule data, client-derived
KPIs, scheduled snapshots, and exports. The scope marks the report feature
in-progress: upcoming maintenance is implemented, while cross-report accuracy,
filter/export parity, and audit evidence remain partial or unverified.

The costing domain already has a canonical completed/verified cost
aggregation. The report page should consume that source rather than recreate a
parts-only total from schedule progress payloads. Its current downtime chart
multiplies active orders by a fixed eight hours, and its Fleet Performance
percentage is based on active maintenance statuses; neither establishes actual
downtime or total fleet availability.

## Forces

- Cost and completion-date attribution must match the costing domain and
  scheduled monthly summary.
- Due or overdue status does not by itself prove a vehicle is unavailable.
- VMMS has no authority over VRMS repair state and must not imply complete
  fleet roadworthiness without that data.
- Exports must match what the user selected and what the UI displays.
- Reports should remain useful when exact duration data is unavailable without
  inventing hours.

## Options considered

1. **Use canonical cost data and honest operational counts (recommended).**
   Reuse the costing source; remove synthetic downtime hours and show clearly
   labeled in-progress counts.
2. **Keep the existing estimates with stronger labels.** Lowest effort, but
   the eight-hour constant and availability denominator remain difficult to
   interpret or compare.
3. **Add actual downtime tracking.** More accurate but requires a settled
   definition and reliable start/end data, potentially involving changes to
   maintenance workflow capture.

## Proposed decision

Submit Option 1 for approval. Attribute completed costs by completion date,
include parts and labor from the costing domain, and do not claim actual
downtime until explicit duration data exists. Use a VMMS-only maintenance
availability estimate only with the proposed definition; otherwise omit the
percentage.

## Tradeoffs

- **Benefits:** report figures can be reconciled to costing records and
  exports, with fewer misleading estimates.
- **Limitations:** no actual duration trend is available until the workflow
  records reliable downtime start/end events.
- **Excluded:** VRMS repair-state integration, income/profit, predictive
  failure claims, and new downtime persistence.

## Decisions awaiting approval

- Completion-date cost attribution and the eligible completed/verified status
  set.
- Removal of the synthetic eight-hour chart.
- Keep the VMMS-only availability estimate with the proposed `IN_PROGRESS`
  definition, or omit the percentage.
- Manila calendar-date behavior for selected date ranges and exports.
