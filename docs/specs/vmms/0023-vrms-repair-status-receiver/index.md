# 0023. VRMS repair status receiver

**Status**: VMMS backend receiver implemented; migration application and external integration pending
**Scope**: [Vehicles, garages, and fleet records](../../../scope/vmms/index.md#2-vehicles-garages-and-fleet-records); [Work orders and maintenance history](../../../scope/vmms/index.md#4-work-orders-checklists-and-maintenance-history)

VMMS contract: [spec 0025](../0025-vmms-vrms-repair-status/index.md).
Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Add a VMMS-authenticated receiver for VRMS repair-ticket lifecycle events.
VMMS uses events to set fleet vehicles `UNDER_REPAIR`, return explicitly
linked maintenance schedules to the Chief Mechanic for final verification
when VRMS completes a ticket, and restore the correct VMMS vehicle state after
completion or cancellation.

## Requirements and behavior

- Implement the VMMS half of suite spec 0020 only. Do not edit VRMS, welinc-auth,
  analytics, web, mobile, or gateway code.
- Use a dedicated `fleet.repair-status.write` service scope and require
  `client_id=vrms`; do not reuse `fleet.read`.
- Accept versioned `OPENED`, `LINKS_UPDATED`, `COMPLETED`, and `CANCELLED`
  events. Persist only delivery/version state and the VMMS IDs required to
  process linked schedules.
- Validate each linked schedule is on the referenced vehicle and in
  `IN_PROGRESS` / `FOR_REPAIR`, or overdue with saved prior state `IN_PROGRESS`
  and `FOR_REPAIR` approval, before linking or handing it back for review.
- On VRMS completion, return every linked schedule to `DONE` / `UNVERIFIED`
  for a fresh Chief Mechanic inspection. The normal VMMS approval flow
  completes the job and applies recurrence rules. Keep linked schedules open
  on VRMS cancellation.
- Recompute vehicle status with precedence `UNDER_REPAIR`, then
  `UNDER_MAINTENANCE`, then `AVAILABLE`.
- Use one transaction for event state, schedule handoff, and vehicle status.

## Acceptance criteria

1. The endpoint requires the exact service client, audience, and dedicated
   scope; a user token or another client is refused.
2. An open event sets the VMMS vehicle to `UNDER_REPAIR`, and maintenance
   status synchronization cannot overwrite it.
3. Explicit links are validated and unrelated schedules on the same vehicle
   are never completed.
4. A completion event returns every linked schedule to Chief Mechanic
   verification without completing it or creating recurring successors.
   Normal Chief Mechanic approval completes the job and creates any eligible
   recurring successor.
5. A cancellation leaves linked schedules in their current active state for
   VMMS follow-up.
6. Event retries are idempotent, event order is enforced, and concurrent
   duplicate delivery cannot apply side effects twice.
7. No VRMS repair issue, part, cost, or full ticket is copied into VMMS.

## API, data, and migration impact

- Add `POST /vmms/integrations/vrms/repair-events`.
- Add migration-backed event/integration state needed for event idempotency
  and schedule correlation.
- No existing VMMS route or response shape changes.
- The endpoint remains unable to receive live VRMS traffic until the
  `fleet.repair-status.write` auth grant and VRMS sender are delivered.

## Security and failure behavior

- Validate service-token use, audience, client ID, and the dedicated scope.
- Reject invalid vehicle/schedule associations and stale or skipped event
  versions explicitly.
- Roll back all changes on schedule handoff or status validation failure.
- Do not update master odometer from the service event.

## Affected repositories

- `welinc-backend-vmms` only for code and migration.
- Shared suite spec 0020 defines the cross-system contract; auth and VRMS
  implementation remain pending.

## Verification

See [verify.md](verify.md).
