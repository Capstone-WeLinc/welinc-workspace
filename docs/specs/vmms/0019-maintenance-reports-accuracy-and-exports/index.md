# 0019. Maintenance report accuracy and exports

**Status**: Draft for approval; implementation is not authorized
**Scope**: [Reports and fleet dashboard](../../../scope/vmms/index.md#7-reports-and-fleet-dashboard)

Decision history: [rationale.md](rationale.md). Verification plan: [verify.md](verify.md).

## Summary

Propose making maintenance report costs, time attribution, downtime, and exports
consistent with the VMMS costing source of truth. Keep the existing upcoming
maintenance and scheduled snapshot views; do not present client-side estimates
as verified historical results.

## Source requirements and related specifications

- VMMS Module 7, BR-23 to BR-26, FR-23.* to FR-26.*, SC-14, and SC-15.
- Cost eligibility and role rules from [Module 6](../../../scope/vmms/index.md#6-maintenance-costing).
- Related proposals: [0015 Fleet dashboard enhancement](../0015-fleet-dashboard-enhancement/index.md)
  and [0018 Maintenance costing exports and analysis](../0018-maintenance-costing-exports-and-analysis/index.md).
- Scheduled daily/monthly reports continue to follow the approved
  [scheduled reports specification](../../../../welinc-backend-vmms/docs/specs/vmms/scheduled-reports-and-escalations/index.md).

## Proposed behavior

### Cost and time attribution

- Use the canonical VMMS maintenance-costing data for completed-cost KPIs and
  exports. Include eligible completed/verified work with parts and labor, and
  attribute it by completion date.
- Keep upcoming and active maintenance in its operational schedule view; do
  not count those records as completed maintenance expense.
- Apply the selected period consistently to maintenance costs and export rows,
  using Manila calendar-date boundaries.

### Downtime and fleet metric

- Remove the synthetic conversion of active work-order counts into downtime
  hours. Until valid start/end duration data is available, show a labeled
  count of VMMS maintenance work in progress instead of claiming actual
  downtime hours.
- Replace or rename the ambiguous Fleet Performance percentage. The proposed
  interim metric is **VMMS Maintenance Availability Estimate**, with only
  active vehicles on an `IN_PROGRESS` VMMS maintenance order counted as
  unavailable. It is not total fleet roadworthiness and does not include VRMS
  repair state.
- If an approved definition or reliable duration data is unavailable, omit the
  percentage and duration trend rather than present them as exact.

### Exports and states

- Keep PDF, CSV, and Excel exports, but make maintenance outputs contain only
  maintenance report rows and the selected period's data.
- Ensure displayed cost totals, row-level costs, date filters, and exports use
  the same canonical source and eligibility rules.
- Show loading, visible error/retry, and empty states for maintenance report
  data; show when data was last refreshed where available.

## Approval requested

1. Approve completion-date attribution and canonical parts-plus-labor costs
   from eligible completed/verified records.
2. Approve replacing synthetic downtime hours with an in-progress work count
   until actual duration data is available.
3. Approve the proposed VMMS-only availability estimate definition, or choose
   to remove the percentage until a full availability definition is settled.
4. Confirm the selected report period uses Manila calendar dates and applies
   consistently to summary values and exports.

## API, data, and migration impact

- Prefer the existing VMMS costing service/API, which is the authority for
  eligible completed costs and completion dates.
- If the maintenance report client cannot obtain the necessary completion
  fields or aggregation, add an additive VMMS-core API response or endpoint;
  do not make analytics the authority for operational or access state.
- No migration is planned unless an approved metric requires missing source
  data. Do not infer completion time or downtime duration from due dates.

## Security and failure behavior

- Preserve Admin/Operations report access and backend authorization.
- Keep cost fields within existing role boundaries and exclude income, profit,
  revenue, VRMS repair costs, and fuel costs.
- On a source failure, show an explicit error and do not export partial or
  stale data as though it were complete.

## Affected repositories

- `welinc-web-vmms`: maintenance report calculations, semantics, states, and
  exports.
- `welinc-backend-vmms`: only if a required canonical cost or completion-date
  field is unavailable from the existing costing API.
- No shared service, portal, gateway, analytics authority, mobile, or
  cross-system change is included.

## Acceptance criteria

1. Completed-cost KPIs and exports use the canonical eligible completed/
   verified set, include parts and labor, and use completion-date filtering.
2. Upcoming and active work does not inflate completed-maintenance costs.
3. No synthetic eight-hour downtime value is presented as actual downtime;
   work-in-progress counts and any availability estimate follow the approved
   labels and definitions.
4. The selected period and Manila date boundaries match across summaries,
   details, and PDF/CSV/Excel exports.
5. Loading, error/retry, and empty states are visible and do not produce
   success-shaped partial results.
6. Existing roles, scheduled snapshot history, and no-profit boundaries remain
   unchanged.

## Verification plan and status

- Planned checks are listed in [verify.md](verify.md).
- No implementation or acceptance evidence is claimed by this draft.
- Scope status must only be reconciled after approval and verified evidence.
