# Verification

## Automated and schema checks

- [x] Prisma Client generation succeeds as part of `npm run build`.
- [x] VMMS backend builds after removing the legacy Prisma models (`npm run build`).
- [x] Search confirms no code or seed references to the legacy `WorkOrder`,
  `RepairIssue`, `RepairPart`, `AuditLog`, `ShopChangeLog`, or
  `WorkOrderStatus` models.

## Database acceptance

- [ ] Apply the migration to a database with legacy work orders and audit rows.
- [ ] Confirm `work_orders`, `repair_issues`, `repair_parts`,
  `_WorkOrderMechanics`, and `WorkOrderStatus` are absent.
- [ ] Confirm `audit_logs` and `shop_change_logs` are absent after migration.
- [ ] Confirm the Admin audit feed and category filter omit repair entries but
  retain vehicle, fuel, maintenance-schedule, and maintenance-costing events.
- [ ] Confirm VMMS maintenance schedules and seeded maintenance workflows
  continue to work.

## Acceptance coverage

| Criterion | Evidence |
|---|---|
| AC-1: Legacy repair tables and enum removed | Migration inspection and database check |
| AC-2: Repair audit data removed | Migration inspection and database check |
| AC-3: No retired-model code or seed references | Repository search |
| AC-4: Current maintenance workflow and audit categories unaffected | Backend build and seeded-flow check |
| AC-5: Repair category removed from audit clients | Endpoint response and web filter check |

No runtime migration or acceptance evidence is claimed yet.
