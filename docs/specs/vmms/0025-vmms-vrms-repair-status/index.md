# 0025. VRMS repair status events to VMMS

**Status**: VMMS receiver implemented; proposed shared contract pending group
review; migration application, auth grant, and VRMS sender pending

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

VRMS reports repair-ticket lifecycle events to VMMS. VMMS remains the only
writer of fleet vehicle status and applies repair precedence to its own vehicle
and maintenance records. A completed VRMS ticket returns every explicitly
linked VMMS maintenance schedule to the Chief Mechanic for final verification.
VMMS completes the work order through its normal approval workflow; a
cancelled VRMS ticket leaves linked schedules open for follow-up.

This contract does not copy VRMS repair issues, parts, costs, or ticket details
into VMMS.

## Sources and decisions

- Suite architecture: systems exchange data through service APIs and never
  read another system's database.
- VMMS scope FR-05.2/05.3: VMMS owns `VehicleStatus` and preserves
  `UNDER_REPAIR` over maintenance status.
- VMMS scope FR-12.4: VMMS work-order execution affects vehicle maintenance
  status.
- VMMS-owned [spec 0023](../0023-vrms-repair-status-receiver/index.md):
  VMMS receiver implementation.
- User decision (2026-11-25): implement the receiver in VMMS only; leave the
  VRMS event sender out of this implementation. VRMS completion returns every
  explicitly linked VMMS schedule to the Chief Mechanic for a final check.
  VRMS cancellation leaves linked schedules open for VMMS follow-up.

## Contract

### Event endpoint and authorization

- `POST /vmms/integrations/vrms/repair-events`
- The caller uses the internal VMMS service address.
- Require a service access token with `aud: VMMS`, `token_use: service`,
  `client_id: vrms`, and `fleet.repair-status.write`.
- The shared auth client registry must grant this scope to `vrms` for audience
  `VMMS`; no other client receives it. This auth change is not part of the
  VMMS-only implementation.
- User tokens, other service clients, missing scopes, and wrong audiences are
  refused. The endpoint never reads VRMS data directly.

### Request

```json
{
  "eventId": "uuid",
  "repairTicketId": "uuid",
  "eventVersion": 1,
  "eventType": "OPENED",
  "vmmsVehicleId": "uuid",
  "maintenanceScheduleIds": ["uuid"],
  "occurredAt": "2026-11-25T00:00:00.000Z",
  "serviceOdometerReading": 12345
}
```

- `eventId` is unique per delivery. A retry uses the same ID and body.
- `eventVersion` starts at 1 and increases by exactly one for every event for
  the ticket.
- `vmmsVehicleId` is the UUID returned by the VMMS fleet API and is immutable
  for the ticket.
- `maintenanceScheduleIds` is the complete set of VMMS schedules accepted onto
  this ticket at that event. It may be empty. `LINKS_UPDATED` may add IDs but
  may not remove accepted IDs; it contains at most 100 unique UUIDs. A linked
  schedule must belong to this vehicle and be active in VMMS `IN_PROGRESS` /
  `FOR_REPAIR` state, or `OVERDUE` with `overdueFromStatus=IN_PROGRESS` and
  `FOR_REPAIR` approval.
- `serviceOdometerReading` is optional on `COMPLETED`. If present, it is
  retained with the event receipt only; it does not complete a VMMS schedule
  or update the VMMS master odometer.
- `occurredAt` is the VRMS event time in ISO 8601 UTC.

### Event behavior

| Event | Required prior state | VMMS behavior |
|---|---|---|
| `OPENED` | No prior event; version 1 | Record ticket state and set the VMMS vehicle to `UNDER_REPAIR`. Validate any linked schedules. |
| `LINKS_UPDATED` | Ticket open | Validate the added linked schedules and retain the complete link set. Vehicle remains `UNDER_REPAIR`. |
| `COMPLETED` | Ticket open | Return every linked VMMS schedule to `DONE` / `UNVERIFIED` for a fresh Chief Mechanic inspection. Do not mark the schedule completed or create a recurring successor yet. Recalculate vehicle status; pending final verification keeps it `UNDER_MAINTENANCE` unless another repair takes precedence. |
| `CANCELLED` | Ticket open | Do not complete or cancel linked schedules. Leave them in their current active `IN_PROGRESS` / `FOR_REPAIR` state (or saved overdue state), then recalculate vehicle status so active VMMS work remains `UNDER_MAINTENANCE`. |

Vehicle status precedence after a terminal event is:

1. `UNDER_REPAIR` if another VRMS repair remains open for the vehicle.
2. `UNDER_MAINTENANCE` if an active VMMS schedule requires maintenance.
3. `AVAILABLE` otherwise.

The VRMS completion event does not complete VMMS work orders. The Chief
Mechanic must perform the final inspection and approve completion through the
normal VMMS workflow; only that approval creates eligible recurring successors.

### Idempotency, ordering, and errors

- The event receipt, ticket state, linked-schedule handoff, and vehicle status
  update commit atomically.
- Replaying an identical `eventId` and body returns success without repeating
  side effects. Reusing an ID with a different body is a conflict.
- Duplicate/stale versions, skipped versions, invalid lifecycle transitions,
  backwards event timestamps, changed vehicle identity, removed schedule
  links, or invalid schedule state return `409` and make no changes. The sender
  retries the same event after correcting delivery order or the underlying
  VMMS condition.
- Invalid payloads return `400`; unknown/deleted VMMS vehicles or schedules
  return `404`; invalid service identity returns `401` or `403`.

## Data, API, and migration impact

- Add a VMMS integration event/state store for event idempotency, version
  ordering, the VMMS vehicle ID, and the explicitly linked schedule IDs. It
  must not store VRMS repair costs, parts, issues, or ticket workflow details.
- Add the service route and migration in `welinc-backend-vmms`.
- Amend the shared auth service-client contract to grant
  `fleet.repair-status.write` to VRMS for VMMS. No auth code or client seed is
  changed in this implementation.
- The existing VMMS fleet API remains read-only and unchanged. BMS continues
  to read the resulting status from it.

## Security and failure behavior

- Enforce `client_id`, audience, service-token use, and the dedicated write
  scope server-side.
- Validate the VMMS vehicle and all schedule-to-vehicle associations before
  applying any event.
- Do not accept client-supplied VMMS status values; event type determines the
  allowed state transition.
- Do not partially apply an event. An invalid schedule handoff leaves the
  ticket event version, work orders, and vehicle status unchanged.

## Affected repositories

- `welinc-backend-vmms`: event endpoint, authorization, persistence, status
  recomputation, return-to-review handoff, and migration.
- Workspace shared contract: this spec and the future auth-client grant.
- `welinc-auth`: required future scope/client grant; not edited in this slice.
- VRMS: required future event producer and referral-ID propagation; not edited
  in this slice.

## Delivery status

The VMMS-only receiver is implemented. Its migration has not been applied, and
the receiver cannot accept real VRMS events until the shared contract is
reviewed, the auth client grant and VRMS sender are implemented, and the changes
are deployed. See [verify.md](verify.md) for completed and pending evidence.
