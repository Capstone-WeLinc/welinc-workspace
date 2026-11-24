# Rationale

Decision record for [index.md](index.md).

## Context

VMMS owns fleet vehicles and vehicle status; VRMS owns repair tickets. VMMS
already protects `UNDER_REPAIR` from maintenance-schedule updates, but no
event currently sets or clears that state from an actual VRMS repair. The user
initially asked that VRMS completion complete a linked VMMS work order. The
later, detailed handoff flow supersedes that behavior: VRMS closure returns
the job to the VMMS Chief Mechanic for a final inspection.

The planned referral flow allows accepted VMMS schedules to be added to an
existing VRMS ticket. A vehicle match alone is therefore not enough to decide
which VMMS work orders to complete.

## Options considered

### Read the VRMS database

VMMS could query VRMS ticket tables directly.

**Rejected**: the suite architecture gives every system its own database and
requires cross-system access through APIs.

### Poll a VRMS API

VMMS could periodically query a VRMS ticket endpoint.

**Rejected for this slice**: no suitable read API or polling contract is
currently documented, and it would make VMMS depend on VRMS availability and
polling freshness.

### Receive versioned VRMS events (chosen)

VRMS sends authenticated lifecycle events to a VMMS-owned endpoint. The event
includes the VMMS vehicle ID and the full set of explicitly linked VMMS
schedule IDs.

**Advantages**:

- VMMS remains the only writer of fleet status.
- A service token with a dedicated write scope identifies the caller and
  avoids reusing BMS's read-only `fleet.read` permission.
- Explicit schedule IDs avoid completing unrelated work on the same vehicle.
- Event IDs and versions make retries safe and reject out-of-order transitions.

**Tradeoff**: this VMMS-only slice defines and builds the receiver, but actual
events remain unavailable until welinc-auth grants the scope and VRMS sends
the contract.

## Decisions

- `OPENED` marks the vehicle `UNDER_REPAIR`; maintenance code continues to
  preserve repair precedence.
- A VRMS ticket may link multiple VMMS schedules. Completion applies only to
  the explicitly linked schedules.
- A completion event returns linked VMMS work orders to `DONE` /
  `UNVERIFIED`, resets their inspection checklist for a fresh final review,
  and does not set `completedAt` or create recurring successors.
- The assigned Chief Mechanic must approve the final inspection through the
  normal VMMS workflow. That approval completes the work order and applies the
  existing recurrence rules.
- A cancelled VRMS ticket does not cancel the VMMS schedules. They retain
  their active `IN_PROGRESS` / `FOR_REPAIR` state (or saved overdue state) for
  VMMS follow-up.
- VMMS recomputes status after a ticket closes: another open repair wins,
  otherwise active VMMS maintenance wins, otherwise the vehicle is available.
- An optional VRMS completion odometer remains in the event receipt only; it
  does not complete or update the VMMS work order or master odometer.
- Integration state is not a second repair-ticket store: VMMS persists only
  event delivery/version state and IDs needed to correlate its own schedules.
