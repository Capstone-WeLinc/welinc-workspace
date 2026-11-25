# Rationale

Decision record for [index.md](index.md).

## Context

VMMS already collects mechanic work, checklist results, service odometer readings, and Chief Mechanic review decisions. The `REPAIR` review decision changes the VMMS approval state but currently has no durable path to VRMS. VMMS previously removed its legacy repair storage so it must read repair history from VRMS rather than recreate a repair domain.

The existing VMMS integration receiver handles repair lifecycle events and final verification, but it does not yet support outgoing referrals, rejection/acceptance metadata, VRMS history reads, or BMS availability delivery. The related external APIs and auth grants are not currently implemented as service contracts.

Flow A adds a VMMS-owned fleet read path for BMS, a fresh availability check before dispatch, and notifications when VMMS fleet master data changes. BMS still owns trip state such as `ON_DELIVERY`; VMMS owns mechanical availability and fleet records.

## Options considered

### Add VRMS repair models back into VMMS

**Rejected**: contradicts repair ownership and the retirement of VMMS's legacy repair tables.

### Synchronously call VRMS from the Chief Mechanic action

**Rejected**: a VRMS outage would fail the VMMS work-order decision and there would be no durable retry or Admin recovery path.

### Persist a VMMS referral outbox and deliver asynchronously (chosen)

Store the VMMS referral payload and delivery state locally. Keep retry and manual recovery separate from the Chief Mechanic's workflow. Consume VRMS decisions through authenticated events and read repair history directly from VRMS.

**Advantages**:

- A work-order decision and its outbound message are committed together.
- Retries are durable and idempotent.
- VMMS preserves ownership boundaries and does not duplicate VRMS history.
- BMS events can be retried without holding up VMMS vehicle status updates.

**Tradeoff**: cross-system paths remain pending until proposed endpoint and auth contracts are accepted and implemented by their owners.

### Publish full vehicle and garage snapshots on every change

**Rejected**: duplicating full VMMS records in the event stream makes retries and out-of-order delivery capable of overwriting newer BMS data.

### Publish a durable invalidation and let BMS read canonical VMMS data (chosen)

VMMS sends a small, idempotent fleet-change event. BMS refreshes the service-authenticated VMMS fleet reads rather than treating an event payload as a fleet snapshot. Before dispatch, BMS checks the specific vehicle's current availability again.

**Tradeoff**: a VMMS read failure blocks dispatch until the source can confirm availability; this favors safety over dispatch continuity.

## Decisions

- The user authorized proposed cross-system contracts and VMMS-only implementation.
- The user chose to return VRMS-rejected work orders to the assigned mechanic as `REJECTED` with the VRMS reason.
- Use the saved work-order odometer; if absent, use the current VMMS master odometer. Send failed inspection items and Chief Mechanic remarks as findings.
- A referral remains pending until VRMS confirms acceptance or rejection. Delivery acceptance (`202`) is distinct from VRMS Admin acceptance.
- On VRMS rejection, the existing work-order restart path returns to the assigned mechanic. On cancellation, retain active `FOR_REPAIR` state and show the reason to the Chief Mechanic. On completion, retain the established final-verification path in spec 0023.
- The existing cost boundary applies to VRMS history: Mechanic does not receive repair cost.
- VMMS owns provider mapping; unmatched shop values must not silently create or mutate the VMMS catalog.
- BMS publication is an outbox side effect of a committed VMMS status change. Event delivery retries in order and never blocks the status transition.
- BMS reads active garages and vehicles through the existing VMMS `fleet.read` service routes. A pre-dispatch read reports `isAssignable` only when the vehicle is active and `AVAILABLE`; non-successful reads must block dispatch.
- Preserve the fleet detail endpoint's existing `404` for inactive, deleted, or unknown vehicle IDs; BMS treats any non-success as unassignable. This avoids changing established route semantics.
- Vehicle/garage creation, material update, deactivation, and soft deletion create durable fleet-change invalidations in the same database transaction. Availability changes continue through the ordered availability outbox; BMS owns `ON_DELIVERY` and other trip states.
- A repair event during an active delivery does not change BMS trip state or silently cancel the trip. BMS flags it for Operations resolution and blocks subsequent assignments.
- Shared API details are proposals only. No partner group's acceptance or delivery is claimed.
