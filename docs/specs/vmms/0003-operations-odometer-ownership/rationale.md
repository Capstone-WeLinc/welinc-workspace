# 0003. Operations ownership of vehicle odometer updates: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

RTM FR-05.1 describes a positive numeric odometer reading but names a Mechanic
as the actor and leaves the required surface ambiguous. VMMS has a shared
vehicle master reading and separate Mechanic service readings associated with
work orders.

Allowing both operational surfaces to mutate the same master reading creates
conflicting ownership and stale updates. Operations already owns fleet planning
and is the approved actor for confirmed vehicle master readings.

## Options considered

### Option 1: Allow all roles to update the master reading

Keep a general vehicle edit or work-order action that writes
`Vehicle.odometer`.

**Pros**:
- Requires little UI or API restructuring.
- Lets Mechanics enter readings immediately.

**Cons**:
- No single authority owns the master reading.
- Lower or stale readings can overwrite confirmed data.
- Work-order evidence is conflated with fleet master state.

### Option 2: Dedicated Operations-only master update (chosen)

Add a dedicated Operations endpoint and web action. Keep Mechanic readings as
work-order evidence that does not mutate the vehicle master.

**Pros**:
- Creates one authoritative write path.
- Allows shared validation and an atomic vehicle/audit update.
- Prevents generic vehicle editing from bypassing odometer rules.

**Cons**:
- Mechanics must submit readings through the work-order flow instead of editing
  the vehicle directly.
- Existing RTM wording and integration documentation require reconciliation.

## Rationale

Option 2 separates confirmed fleet data from service evidence. Backend
authorization and validation are authoritative; the web UI is only a workflow
convenience.

The same domain operation validates the latest reading and updates the vehicle
and audit record atomically. Lower readings and stale concurrent submissions
fail explicitly, unchanged readings do not create duplicate audit events, and
mobile remains read-only.
