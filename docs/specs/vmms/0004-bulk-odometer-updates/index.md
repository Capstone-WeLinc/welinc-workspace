# 0004. Bulk odometer updates and schedule refresh

**Date**: 2026-11-19
**Status**: Backend and web implemented; migration applied to local Docker; interactive acceptance pending
**Scope**: [Module 2: Vehicles, garages, and fleet records](../../../scope/vmms/index.md); [Module 3: Maintenance scheduling and alerts](../../../scope/vmms/index.md)

Decision history (context, options, rationale): [rationale.md](rationale.md). Verification steps: [verify.md](verify.md).

## Summary

Operations should record a truck's actual odometer once on the vehicle master,
not edit the odometer fields on each maintenance schedule. After a master
reading changes, VMMS recalculates the state of all eligible odometer-based
schedules for that truck from the same authoritative reading while preserving
each schedule's configured trigger, interval, and buffer.

For fleet-wide catch-up, Operations can upload readings for multiple vehicles
through a preview-and-save spreadsheet flow. Valid rows are applied
independently; invalid or stale rows are returned as row-level errors without
blocking other valid rows.

## Problem and ownership

- `Vehicle.odometer` is the current master reading and Operations owns its
  updates, as recorded in [spec 0003](../0003-operations-odometer-ownership/index.md).
- `MaintenanceSchedule.odometerReading` and
  `startingReferenceReadingKm` are schedule-specific reference values, not
  another place to record the truck's latest reading.
- The per-schedule odometer-reading shortcut and Admin-only threshold editor
  have been removed. Operations can still configure schedule-specific
  references, intervals, and buffers in the full schedule editor; these values
  are not the vehicle's current master reading.
- A master reading change should affect schedule state automatically. It must
  not rewrite schedule reference readings, intervals, buffers, or due
  thresholds.

## Approved follow-on design: vehicle maintenance defaults

The user approved a vehicle-level base interval and buffer, with optional
overrides by VMMS maintenance category and a per-schedule **Custom** option.
Use the existing configurable Checklist Templates as the category source;
Operations manages vehicle defaults and template-specific overrides from the
vehicle page. Do not introduce a hard-coded list or a separate category
catalog.

- Resolve defaults in this order: schedule custom value, vehicle/category
  override, then vehicle base default.
- If an odometer schedule has no applicable default, Operations must enter
  custom interval and buffer values before saving.
- A schedule using defaults copies the resolved interval and buffer onto the
  schedule when it is created.
- Changing a vehicle base default or category override affects future
  schedules only; existing schedules retain their saved interval, buffer, and
  due threshold.
- The schedule's starting reference remains an interval anchor, not the live
  vehicle odometer. Recurring odometer schedules continue to anchor the next
  interval to the completed service reading.
- Operations can manage the base pair and template-specific overrides from the
  vehicle page. If neither provides a pair, an odometer schedule requires
  custom interval and buffer values.
- Existing schedules retain their saved values; updating defaults does not
  recalculate or rewrite their thresholds.

## Behavior

### Single-vehicle update

- Operations updates the active vehicle through the existing vehicle odometer
  action.
- The backend saves the master reading and its audit record, then reevaluates
  that vehicle's active odometer-triggered schedules using the existing
  activation and due thresholds.
- For eligible `PENDING`, `DUE`, and `OVERDUE` schedules, status is derived from
  the new master reading:
  - `PENDING`: below `dueOdometer - bufferDistanceKm`
  - `DUE`: from the activation point through `dueOdometer`
  - `OVERDUE`: above `dueOdometer`
- Preserve `IN_PROGRESS`, `DONE`, `COMPLETED`, and `CANCELLED` workflow states.
  Do not create a replacement schedule or move a threshold just because a
  reading crosses it; Operations and Mechanics use the existing due work order.
- A no-op reading does not create an audit event or repeat schedule
  notifications. State changes use the existing schedule notification rules.

### Bulk vehicle readings

- Add an Operations-only **Bulk update odometers** action to the Vehicles page.
- Reuse the existing `.xlsx` preview-and-save interaction where practical. The
  columns are `Plate Number` and `Odometer Reading (km)`, with a
  1,000-row limit matching the current vehicle import flow.
- Preview is read-only and shows the matched vehicle, current reading,
  proposed reading, and any row errors.
- Reject duplicate plate rows, unknown or inactive vehicles, non-positive or
  non-integer readings, and readings lower than the latest master value.
  Equal readings are valid no-ops.
- Saving revalidates every row against current database state. Apply each valid
  row independently; return successes and row-specific failures together.
- Preview rows report `READY`, `UNCHANGED`, or `ERROR`; save rows report
  `UPDATED`, `UNCHANGED`, or `ERROR`, with an error reason where applicable.
- For each changed row, updating the vehicle master, its audit record, and the
  affected schedule states is one transaction. A failure for one row does not
  roll back successful rows for other vehicles.
- Do not allow bulk input to change maintenance thresholds or schedule
  baselines.

## API, data, and audit impact

- Keep `PATCH /vehicles/:id/odometer` as the single-vehicle write operation and
  make its schedule refresh part of the owning backend service.
- Add Operations-only `POST /vehicles/odometer/import/preview` and
  `POST /vehicles/odometer/import` endpoints for bulk odometer rows.
- Bulk save calls the same validation and update logic as a single-vehicle
  update; it must not create a second master-odometer write path.
- Record each changed vehicle's old and new master readings, actor, and time in
  `VehicleAuditLog`. No new persistence table is expected.
- Use the existing maintenance schedule status and notification mechanisms.
  No schedule threshold or reference fields are changed by an odometer update.
- No shared-service, gateway, auth, or cross-system API change is required.

## Security, validation, and failure behavior

- Only a VMMS Operations role can preview or save master odometer changes.
- Backend authorization and validation remain authoritative; UI visibility is
  not access control.
- Preview performs no writes. Save rechecks active status and the latest
  odometer to reject stale lower readings.
- Partial success is explicit: every row reports saved, unchanged, or failed
  with a reason; the response must not present a partially failed batch as an
  all-success result.
- Vehicle update plus audit and schedule-state changes are atomic per vehicle.

## Acceptance criteria

1. Updating a vehicle's master odometer once reevaluates all eligible
   odometer-based schedules for that vehicle without editing them individually.
2. Schedule thresholds, intervals, buffers, and reference readings remain
   unchanged by a master reading update.
3. Schedule status follows the existing activation, due, and overdue thresholds
   using `Vehicle.odometer`; in-progress and terminal workflow states are
   preserved.
4. Operations can preview a spreadsheet containing readings for multiple
   vehicles before saving.
5. Unknown, duplicate, inactive, invalid, lower, or stale rows are rejected
   with row-level errors; valid rows can still be saved.
6. Each changed row updates the vehicle, audit record, and affected schedule
   states atomically; an error on one row does not roll back other rows.
7. Equal readings are no-ops and do not duplicate audits or notifications.
8. Admin, Chief Mechanic, and Mechanic cannot use the master odometer update or
   bulk import paths. Scheduling no longer exposes per-schedule odometer update
   or Admin threshold-edit actions; Operations retains full schedule planning.
9. Analytics and mobile consumers display refreshed master readings and
   schedule state through existing VMMS APIs/sync; neither becomes an odometer
   write authority.

## Affected repositories

- `welinc-backend-vmms`: central schedule-state recalculation, bulk preview and
  partial-save endpoints, row validation, transaction/audit behavior, and
  vehicle maintenance defaults with schedule-time resolution.
- `welinc-web-vmms`: Operations bulk upload preview, row errors, and explicit
  save flow; no per-schedule odometer edit workflow for recording actual
  readings. Operations also manages vehicle defaults and chooses defaults or
  custom mileage values when scheduling.
- `welinc-backend-vmms-analytics-ai`: verify refreshed schedule state appears
  after its normal source-data refresh; no independent odometer writes.
- `welinc-mobile-vrms_vmms`: verify read-only vehicle snapshots and schedule
  state reflect the refreshed master reading; no odometer write changes.

## Risks and verification

- A large odometer jump can move multiple schedules into `DUE` or `OVERDUE`.
  Preserve their configured thresholds and use existing work orders rather than
  silently shifting maintenance plans.
- Bulk preview can become stale before save; save-time revalidation and
  per-row transactions are required.
- Verify single and bulk updates against vehicles with multiple schedules,
  mixed schedule states, duplicate/unmatched rows, stale concurrent updates,
  and schedule thresholds crossed by a reading.
- Verify authorization, audit contents, notification deduplication, analytics
  refresh, and mobile read-only sync.
- The additive vehicle maintenance-default migration must be applied before
  deploying the backend.

## Implementation and verification

- Implemented in `welinc-backend-vmms`: Operations-only preview/save endpoints,
  row-level partial results, per-vehicle transactional audit and schedule
  refresh, and schedule-state derivation from the master odometer.
- Implemented in `welinc-web-vmms`: editable spreadsheet preview and explicit
  save flow with current readings and per-row results; removed the
  per-schedule odometer update shortcut and Admin threshold editor while
  retaining Operations schedule configuration. Vehicle defaults can be
  managed from the vehicle page; schedule creation resolves defaults or
  requires custom mileage values.
- Implemented in `welinc-backend-vmms`: Operations-only default read/write
  endpoints, base settings on vehicles, checklist-template overrides, and
  schedule-time resolution that snapshots the selected interval and buffer.
- Applied `20261119000100_vehicle_maintenance_defaults` to the local Docker
  database. Backend and web containers were rebuilt and are running; Prisma
  reports the schema up to date, `/vmms/health` and the web root return 200,
  and the protected defaults route rejects unauthenticated access.
- Analytics statically reads the vehicle master odometer and persisted schedule
  statuses during its existing refresh. Mobile statically consumes the vehicle
  and schedule API snapshots and reconciles the refreshed schedule status;
  neither adds an odometer write path.
- Verification completed: backend build, 407 tests across 30 schedule/vehicle
  suites, changed-file backend lint, web production build, and changed-file
  web lint. Browser interaction and analytics/mobile refresh acceptance remain
  pending.
