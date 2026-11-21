# 0003. Operations ownership of vehicle odometer updates

**Date**: 2026-11-19
**Status**: Single-vehicle ownership flow implemented; runtime acceptance pending
**Scope**: [Module 2: Vehicles, garages, and fleet records](../../../scope/vmms/index.md)

Decision history (context, options, rationale): [rationale.md](rationale.md). Verification steps: [verify.md](verify.md).

## Summary

Operations owns all changes to a vehicle's master odometer reading. The update
workflow lives in the VMMS web Vehicles page and is separate from vehicle
creation and general vehicle-detail editing.

This decision replaces the Mechanic/mobile actor in RTM FR-05.1 for master
odometer updates. Mechanics may still submit service odometer readings as
work-order evidence, but those submissions must not directly change
`Vehicle.odometer`. Operations reviews and applies a reading through the
dedicated vehicle workflow.

## Requirements and decision

- **RTM FR-05.1** requires positive numeric readings at or above the last
  recorded vehicle odometer, but its user story and acceptance scenario name a
  Mechanic using mobile.
- **User decision (2026-11-19)**: Operations, not Mechanics, owns all writes to
  the vehicle master odometer, including readings originating from work orders.
- This VMMS decision supersedes the actor and surface in FR-05.1. The source RTM
  remains unchanged until it can be reconciled through the project requirements
  process.

## Behavior

- Operations selects an active vehicle in the VMMS web Vehicles page and opens a
  dedicated **Update odometer** action.
- The form displays the current master reading and accepts a positive whole
  number greater than or equal to that reading.
- A lower reading is rejected with a clear error. Re-submitting the current
  value is an accepted no-op and does not create a duplicate audit event.
- The web client provides immediate validation, but the backend is authoritative.
- Operations can update only through the dedicated odometer operation. The
  general vehicle update API and form do not accept changes to the master
  odometer. Vehicle creation may still set the initial baseline.
- Admin, Chief Mechanic, and Mechanic cannot update the master odometer.
- A Mechanic may submit a service odometer as work-order evidence. That value
  remains attached to its work-order/service record and does not update the
  vehicle master. Recurring schedule creation uses the Operations-confirmed
  master reading; refreshing all existing schedules after a master update is
  proposed separately in [spec 0004](../0004-bulk-odometer-updates/index.md).
- The mobile app remains a read-only consumer of the master vehicle snapshot;
  no odometer write is queued offline.

## API, data, and audit impact

- Add an Operations-only `PATCH /vehicles/:id/odometer` operation with an
  `odometer` request field.
- Route all master-odometer writes through one VMMS service operation that
  validates the latest reading and updates the vehicle and its audit record in
  one transaction.
- Handle stale concurrent submissions without lowering the latest reading; the
  client must receive an explicit conflict/validation error.
- Reuse `VehicleAuditLog` to record the actor and previous/new values. No new
  table or migration is expected.
- Remove `odometer` from the general vehicle update payload so it cannot bypass
  the dedicated rule.

## Acceptance criteria

1. Operations can update an active vehicle's master reading from the web
   Vehicles page.
2. The API accepts only positive whole-number readings at or above the latest
   saved value; lower readings are rejected.
3. Admin, Chief Mechanic, and Mechanic cannot change the master reading through
   any general or dedicated vehicle update endpoint.
4. Work-order completion can retain a Mechanic's service odometer evidence
   without changing the vehicle master reading.
5. Each changed master reading and its audit record commit atomically and
   identify the Operations actor; unchanged readings create no duplicate event.
6. Mobile continues to receive master readings through the existing authenticated
   vehicle snapshot sync and does not queue odometer writes offline.
7. Vehicle creation can still establish an initial odometer baseline.

## Security and failure behavior

The backend role guard and service validation are authoritative. Client-side
validation is supplemental. A stale or lower reading must never be treated as a
successful update; failures use the established VMMS error response rather than
a success-shaped fallback.

## Affected repositories

- `welinc-backend-vmms`: Operations-only endpoint, domain validation, atomic
  update/audit, removal of odometer writes from generic vehicle edits,
  work-order submission, and schedule completion.
- `welinc-web-vmms`: dedicated Operations update action, client-side
  validation, and creation-only initial baseline.
- `welinc-mobile-vrms_vmms`: no write UI; verify synchronization remains
  read-only for vehicle master data.
- VMMS-owned scope and requirements documentation: record this policy override
  and reconcile FR-05.1.

## Verification plan

- Test the Operations/other-role authorization matrix at the API boundary.
- Test positive, equal, lower, and concurrent readings at the service boundary,
  including audit atomicity.
- Verify general vehicle edits cannot mutate odometer while creation can set a
  baseline.
- Build and lint the backend and web app; exercise the Operations flow and
  mechanic work-order evidence path in runtime acceptance.

Backend targeted tests (116 tests across vehicle service/controller, work-order
submission, and recurrence) and the backend build pass. Changed backend and web
files pass targeted lint, and the web production build passes. Runtime
browser/mobile acceptance and RTM reconciliation remain open.
