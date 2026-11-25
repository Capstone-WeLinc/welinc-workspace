# Rationale

Decision record for [index.md](index.md), implementing the suite interface in
[spec 0025](../0025-vmms-vrms-repair-status/index.md).

## Context

VMMS already treats `UNDER_REPAIR` as higher precedence than its
maintenance-derived vehicle status, but it does not receive VRMS ticket
updates. The VMMS work order's `For Repair` state is still a VMMS
`IN_PROGRESS` schedule; it is not itself a VRMS ticket or a ticket link.

The user authorized the shared contract and VMMS implementation while
excluding VRMS sender and shared-auth code changes from this implementation.

## Options

1. Read VRMS data directly: rejected by suite data ownership rules.
2. Poll a VRMS API: no suitable API is currently documented, and polling
   freshness would be an additional dependency.
3. Receive authenticated versioned events: chosen. VMMS owns the receiver and
   remains the authority for its vehicles and schedules.

## Decisions

- The event must include VMMS vehicle and schedule IDs; never infer a work
  order from a vehicle plate or complete all work on that vehicle.
- Ticket events carry the full accepted schedule-link set. Links can be added
  while the ticket is open but not removed after acceptance.
- VRMS completion returns linked schedules to `DONE` / `UNVERIFIED` and resets
  the inspection items for a fresh Chief Mechanic review. It does not complete
  the VMMS work order or create a recurring successor.
- The Chief Mechanic completes the work order through the normal VMMS approval
  path, which then applies existing recurrence rules.
- Cancellation does not cancel the VMMS maintenance work; VMMS leaves it open
  for follow-up and restores the vehicle to its active maintenance state.
- The database stores only integration state needed for delivery, ordering,
  and linkage, not a duplicate VRMS repair domain.
- Live integration is blocked until auth grants the new service scope and
  VRMS implements the sender.
