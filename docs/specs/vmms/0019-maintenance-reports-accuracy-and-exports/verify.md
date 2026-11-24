# Verification — 0019 Maintenance report accuracy and exports

All checks are pending approval and implementation. They are derived from the
acceptance criteria in [index.md](index.md).

## Cost and period correctness

- [ ] Use a fixed set of eligible completed/verified records with known parts
  and labor costs; compare KPI, detail, and export totals → AC-1, AC-4
- [ ] Include due, overdue, in-progress, cancelled, and unverified records and
  confirm they are not counted as completed costs → AC-1, AC-2
- [ ] Test records on both boundaries of a selected Manila date range and
  confirm identical filtering in the UI and all export formats → AC-4

## Downtime and metric semantics

- [ ] Confirm no active-order count is converted to actual downtime hours
  without source duration data → AC-3
- [ ] Verify in-progress counts and any availability estimate follow the
  approved status definition and visible label → AC-3
- [ ] Confirm the report does not imply VRMS repair state or total fleet
  roadworthiness → AC-3, AC-6

## States, roles, and regression

- [ ] Verify loading, empty, source error, retry, and refresh behavior; failed
  data is not exported as complete → AC-5
- [ ] Verify Admin/Operations access and existing cost-field restrictions
  remain enforced → AC-6
- [ ] Confirm scheduled snapshots and upcoming maintenance views remain
  available and unchanged → AC-6

## Acceptance-criteria coverage

| AC | Planned evidence |
| --- | --- |
| AC-1–AC-2 | Canonical eligible completed-cost calculation |
| AC-3 | Downtime and availability definition checks |
| AC-4 | Date boundary and export parity checks |
| AC-5 | Loading, error, empty, retry, and export failure checks |
| AC-6 | Role and existing-view regression checks |

## Implementation evidence

No implementation or verification has been performed for this proposal.
