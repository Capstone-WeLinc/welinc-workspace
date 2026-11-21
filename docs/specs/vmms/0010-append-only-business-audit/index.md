# 0010. Append-only business audit

**Status**: Approved for implementation
**Scope**: [Work orders and maintenance history](../../../scope/vmms/index.md#4-work-orders-checklists-and-maintenance-history); [Reports and fleet dashboard](../../../scope/vmms/index.md#7-reports-and-fleet-dashboard)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Protect existing immutable VMMS business-event tables against ordinary
updates/deletes at the PostgreSQL layer, preserve the current table layout,
retain identity-erasure rewriting, and categorize the Admin unified audit
feed. Mutable cancellation and unlock workflow records remain workflow state,
not immutable event rows.

## Sources and decisions

- Existing work-order, shop, vehicle, fuel, threshold, and maintenance-log
  edit audit models, plus the Admin business-audit feed.
- `welinc-backend-vmms` already rewrites stored actor names/emails to erased
  markers when a directory identity is removed.
- User selected existing-table protection and categorized unified reads rather
  than migration to one canonical event store.

Protected immutable event tables:

- `audit_logs`
- `shop_change_logs`
- `vehicle_audit_logs`
- `fuel_audit_logs`
- `fuel_anomaly_threshold_audits`
- `maintenance_costing_threshold_audit`
- `maintenance_log_edit_audits`

The mutable `maintenance_schedule_cancellations` and
`maintenance_log_edit_unlocks` records are explicitly excluded from the
immutability trigger because they represent requests whose review/consumption
state changes. Their current visibility in the audit feed is retained, with a
workflow category; they are not represented as immutable event evidence.

## Behavior and controls

- Add PostgreSQL triggers that reject `DELETE` and reject `UPDATE` except an
  identity-erasure-only change that replaces actor name/email with the
  existing erased markers. No event facts, references, timestamps, or
  before/after values may change.
- Change only the immutable-event foreign keys that currently cascade-delete
  their audit rows to `RESTRICT`, so deleting a parent cannot erase protected
  history. Preserve soft-delete behavior.
- Keep existing inserts, API feed limits/order, and record shape; add a
  stable `category` field to each unified record (`work_order`, `vehicle`,
  `fuel`, `maintenance_schedule`, or `maintenance_costing`).
- Preserve Admin-only access and `no-store` cache behavior.
- The feed remains a read projection from existing tables, not a second
  writeable event store.

## Acceptance criteria

1. Inserts into protected event tables continue to work.
2. Direct SQL and ORM attempts to change or delete immutable event facts fail;
   FK cascades cannot remove those events.
3. The approved identity-erasure routine can redact only actor display name
   and/or email to the existing erased form; all other changes remain blocked.
4. Existing work-order/vehicle soft deletion and normal business updates
   continue to work; attempts to hard-delete a referenced parent fail
   explicitly rather than erase audit history.
5. The Admin unified feed continues to include existing records and returns a
   stable category for every record; web audit rows display/filter by category.
6. Non-Admin access remains denied and responses remain non-cacheable.
7. Mutable cancellation/unlock state continues to function and is visibly
   categorized as workflow state, not misrepresented as append-only history.

## Data, security, and migration impact

- Add a forward-only PostgreSQL migration for triggers and restrictive
  relations; no backfill or canonical event migration.
- Existing history remains in its current tables.
- The trigger is the enforcement boundary, not a client-side convention.
- Erasure remains a narrow, explicit exception; retain the stable actor ID as
  existing behavior does.
- Failure to apply the migration must block deployment; do not silently run
  without the protection.

## Affected repositories

- `welinc-backend-vmms`: Prisma relation metadata, migration, erasure
  compatibility, Admin feed category, and tests.
- `welinc-web-vmms`: category display/filter in Audit Logs.

## Delivery status

The current feed, event tables, foreign-key behavior, and identity-erasure
routine were reviewed. Migration and end-to-end verification remain.
