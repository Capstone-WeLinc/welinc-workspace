# 0022. Retire legacy repair storage

**Status**: Implementation complete; database migration verification pending
**Scope**: [Work orders, checklists, and maintenance history](../../../scope/vmms/index.md#4-work-orders-checklists-and-maintenance-history)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Remove VMMS's legacy repair-ticket data model and its repair-only audit data.
VMMS maintenance schedules remain the only VMMS work-order system. Preserve the
active Admin audit feed for vehicle, fuel, and maintenance activity.

This spec supersedes [spec 0010](../0010-append-only-business-audit/index.md)
only for the repair-specific `audit_logs` and `shop_change_logs` tables and the
`work_order` audit category. Its protections for retained audit sources remain.

## Decision and behavior

- Drop the legacy `work_orders`, `repair_issues`, and `repair_parts` tables,
  their Prisma models and relations, the implicit mechanic join table, and the
  legacy `WorkOrderStatus` enum.
- Drop the repair-only `audit_logs` and `shop_change_logs` tables and remove
  their `work_order` category from the Admin audit feed.
- Keep `maintenance_schedules` and the VMMS maintenance workflow unchanged.
- Keep current vehicle, fuel, maintenance-schedule, and maintenance-costing
  audit sources and their existing controls.
- Stop seeding obsolete repair tickets; continue seeding the VMMS fleet and
  maintenance schedules.

## Acceptance criteria

1. A forward-only migration removes the legacy repair entity tables and enum.
2. The migration removes the repair-only `audit_logs` and `shop_change_logs`
   tables and their audit records.
3. VMMS Prisma schema and code contain no queries or seed writes to the retired
   repair entities or repair audit tables.
4. Maintenance schedules, work orders based on schedules, and all current
    audit categories remain operational.
5. The Admin audit endpoint and web filter no longer expose a repair category.

## API, data, and migration impact

- Remove the `work_order` category from the audit response category union; all
  other audit record fields and routes remain unchanged.
- Existing legacy repair operational and audit records are deleted by the
  migration.
- No VRMS API or cross-system contract is changed in this slice.

## Security and failure behavior

- Preserve Admin-only access and `no-store` behavior on the business audit
  endpoint.
- Preserve access controls and immutability protections on all retained audit
  sources.
- Apply the migration before deploying code generated from the updated Prisma
  schema.

## Affected repositories

- `welinc-backend-vmms`: Prisma schema/client, migration, seed, erasure map, and
  audit projection.
- `welinc-web-vmms`: remove the retired repair audit category from the type and
  filter.
- No mobile, analytics, shared-service, or VRMS change is required.

## Verification

See [verify.md](verify.md). Runtime database migration and audit-history
verification remain pending.
