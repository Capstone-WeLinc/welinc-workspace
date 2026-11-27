# 0027. Complete VMMS development seed

**Status**: Implemented; full runtime verification pending  
**Scope**: [Analytics, mobile synchronization, and release readiness](../../../scope/vmms/index.md#8-analytics-mobile-synchronization-and-release-readiness)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Provide a synthetic development dataset for VMMS models that are not already
covered by manual integration testing or private file uploads. Refresh
seed-owned mutable fixtures by deterministic ID while leaving unrelated
operational data, protected audit history, and manual-upload metadata intact.

## Sources and decisions

- VMMS requirements for vehicle management, maintenance scheduling/work
  orders, fuel operations, maintenance costing, reports, and cross-cutting
  release readiness.
- Existing seed and data rules in [spec 0012](../0012-maintenance-scheduling-completion/index.md),
  append-only events in [spec 0010](../0010-append-only-business-audit/index.md),
  global settings in [spec 0009](../0009-settings-catalog/index.md),
  fuel receipt handling in [spec 0005](../0005-fuel-receipt-scanning/index.md),
  fuel import in [spec 0006](../0006-bulk-fuel-statement-import/index.md),
  costing in [spec 0018](../0018-maintenance-costing-exports-and-analysis/index.md),
  and the proposed cross-system boundary in
  [spec 0026](../0026-vmms-vrms-repair-referrals-and-bms-availability/index.md).
- User decisions on 2026-11-27:
  - Cover the current VMMS model landscape with synthetic records and complete
    relationships where seeding is appropriate.
  - Refresh seed-owned synthetic fixtures and reset the two global demo
    thresholds on every development seed run; do not overwrite unrelated
    operational records or manually tested integration data.
  - Keep append-only audit rows immutable and preserve directory-sync state,
    other configuration, and manual-upload metadata.
  - Do not write attachment objects from the seed. Provide the
    [synthetic PNG receipt](synthetic-demo-fuel-receipt.png) for the user to
    upload manually through the application.
  - Exclude all six VRMS/BMS integration model fixtures from the comprehensive
    seed; those are exercised manually. Do not delete existing integration
    test rows.

## Coverage

The seed covers these schema models:

| Area                         | Models                                                                                                                                                                                                                                                                                                                                   |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identity and fleet           | `DirectorySyncState`, `VmmsPerson`, `Garage`, `Vehicle`, `Mechanic`, `OutsourcedProvider`, `VehicleAuditLog`                                                                                                                                                                                                                             |
| Maintenance                  | `ChecklistTemplate`, `ChecklistItem`, `VehicleMaintenanceDefault`, `MaintenanceSchedule`, `MaintenanceScheduleCancellation`, `MaintenanceScheduleExtension`, `MaintenanceScheduleExtensionAudit`, `MaintenanceScheduleRescheduleAudit`, `MaintenanceLogEditUnlock`, `MaintenanceLogEditAudit`, `MaintenanceNotification`, `Notification` |
| Fuel                         | `FuelStation`, `FuelAnomalySetting`, `FuelAnomalyThresholdAudit`, `FuelImportDraft`, `FuelFillUp`, `FuelAnomaly`, `FuelAnomalyAttachment`, `FuelReceiptAttachment`, `FuelAuditLog`                                                                                                                                                       |
| Costing and reports          | `MaintenanceCostingSetting`, `MaintenanceCostingThresholdAudit`, `MaintenanceCostingExportAudit`, `ScheduledFleetReport`                                                                                                                                                                                                                 |
| Manually tested integrations | `VrmsRepairIntegrationState`, `VrmsRepairEventReceipt`, `VmmsRepairReferral`, `VrmsRepairReferralEventReceipt`, `BmsVehicleAvailabilityEvent`, `BmsFleetChangeEvent`                                                                                                                                                                     |

The six integration models are covered through the existing manual test
workflow, not this seed. Attachment metadata is created only when the user
manually uploads the provided synthetic file through the fuel receipt and
anomaly attachment flows. Neither workflow should be replaced by synthetic
rows from this seed.

## Behavior and invariants

- `npm run seed` creates or refreshes mutable synthetic fixtures by their
  deterministic IDs. It does not delete fixture rows, unrelated operational
  rows, or manual-upload metadata.
- Generated work-order and log numbers remain stable when their seed-owned
  maintenance fixtures are refreshed.
- Insert append-only audit records once; never update or delete existing audit
  history.
- Reset the global fuel anomaly threshold to 20% and maintenance costing
  threshold to PHP 4,000 on each development seed run. Append an audit record
  only when either value actually changes.
- Preserve directory-sync state and other singleton configuration. Surface
  unique-key conflicts rather than treating an unrelated record as
  seed-owned.
- If an existing pending maintenance schedule uses the same vehicle/title
  identity, keep the existing schedule and report the skipped fixture.
- Resolve foreign keys to the seeded or existing registered parent records.
  Also validate logical links that are not database foreign keys, including
  schedule plate-to-vehicle and schedule-garage-to-vehicle values, actor IDs,
  work-order progress, and recurrence successors.
- Seed user/person snapshots only from the repository's existing synthetic
  source. Do not query another system's database or create shared-auth
  accounts.
- Seed completed maintenance history as verified so it appears in the
  approved maintenance-costing dataset.
- Use the persisted fuel anomaly threshold when deciding whether the synthetic
  fuel fixture is an anomaly.
- Do not seed VRMS/BMS integration state, receipts, referrals, or outbox rows.
  The existing manual integration tests own those records.
- Keep fuel readings, totals, anomalies, and maintenance costs consistent with
  their source records and existing business rules. Do not lower a vehicle's
  master odometer.
- The seed remains development-only under the existing production guard.

## API, data, and security impact

- No schema migration or API contract change.
- Only `welinc-backend-vmms` seeding code and this VMMS-owned specification
  are in scope. No other repository or shared service is changed.
- Audit fixtures are synthetic test data; stable IDs and synthetic actor labels
  must make their origin clear without modifying real history.
- Private file storage is not written by seeding. The user uploads the
  supplied placeholder through existing authorized flows.

## Acceptance criteria

1. The seed inserts fixtures for its 30 in-scope models. The six VRMS/BMS
   integration models remain covered by manual integration testing, and the
   two attachment models are populated only by authorized manual uploads.
2. Running the seed twice creates no duplicate fixture rows or relationship
   records, and refreshes mutable seed-owned fixtures to their defined values.
3. Running the seed against a populated database refreshes deterministic
   seed-owned mutable fixtures and the two demo thresholds; unrelated records,
   append-only audit rows, other configuration, and manual-upload metadata
   remain unchanged.
4. Every seeded foreign-key relation resolves, and every declared logical link
   (vehicle, garage, mechanic/person, checklist, schedule progress, recurrence,
   and fuel source) is consistent.
5. Maintenance schedules retain valid status, trigger, odometer, checklist,
   provider, recurrence, and pending-uniqueness semantics.
6. Fuel fill-ups have valid vehicle/station links, chronological odometer
   readings, calculated totals, and anomaly relationships consistent with the
   persisted fuel threshold.
7. Seeded audit records are inserted idempotently and are never updated or
   deleted. VRMS/BMS integration records are not created by this seed.
8. The supplied synthetic PNG can be manually uploaded as both a receipt and
   anomaly attachment through authorized application flows, creating valid
   metadata-to-blob links.
9. The demo threshold values appear in Settings; the fuel anomaly and verified
   routine maintenance cost fixtures demonstrate the thresholds' effects, and
   threshold changes are audited only when values change.

## Verification plan and status

See [verify.md](verify.md). The backend build passes. Full-schema database
fixture-refresh/protected-data checks and manual attachment-upload evidence remain
pending.
