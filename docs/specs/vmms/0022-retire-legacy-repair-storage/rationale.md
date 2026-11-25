# Rationale

VMMS now owns fleet and maintenance scheduling, while VRMS owns repair tickets.
The old VMMS `WorkOrder`, `RepairIssue`, and `RepairPart` models are a second,
unused repair store. Its `audit_logs` and `shop_change_logs` tables only record
events against that legacy repair store. The Admin audit feed also contains
independent vehicle, fuel, and maintenance audit sources that remain active.

## Options

1. Keep the legacy repair entities and audit tables. This avoids migration risk
   but leaves VMMS with a duplicate repair model and inactive audit category.
2. Drop the legacy repair entities and their repair-specific audit tables,
   retaining the independent VMMS audit sources. This removes duplicate repair
   data while keeping the current Admin audit experience useful.

## Decision

Use option 2. Drop `audit_logs` and `shop_change_logs` along with the old repair
entities and remove the `work_order` audit category. Current vehicle, fuel, and
maintenance audit behavior and controls remain unchanged. Current maintenance
schedules and their work-order lifecycle are outside this change.

VRMS completion callbacks, repair handoff behavior, and vehicle-status
ownership remain a separate cross-system contract and are not implemented here.
