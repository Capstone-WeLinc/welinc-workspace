# Rationale

Decision record for [index.md](index.md).

## Context

The VMMS work-order workflow already lets a Chief Mechanic mark a submitted job `For Repair`, but VMMS has no referral delivery state, VRMS history service contract, or BMS availability-event contract. VRMS repair data belongs to VRMS; VMMS owns vehicle status and maintenance work orders; BMS owns trip reassignment and customer notifications.

The existing suite architecture prohibits cross-system database access. The current VRMS repair-history route is protected by user permissions and is not a service-to-service contract for VMMS. The current VMMS event receiver contract covers repair lifecycle status only and does not define the referral command, referral outcomes, history reads, or BMS event delivery.

## Options considered

### Duplicate VRMS repair details in VMMS

**Rejected**: creates a second repair record owner and requires ongoing synchronization of issues, parts, personnel, and costs.

### Pass a VMMS user token through to VRMS

**Rejected**: couples VMMS role access to VRMS user permissions and does not provide a stable backend service identity for all VMMS roles.

### Proposed service APIs and durable VMMS delivery state (chosen)

Use narrowly scoped service-to-service endpoints. Persist VMMS referral requests and BMS availability events only as durable delivery records. Read repair history from VRMS on demand. Continue using versioned VRMS lifecycle events for repair-to-vehicle status.

**Advantages**:

- Preserves system data ownership and supports retries without duplicate referrals.
- Lets VMMS enforce its own work-order assignment and cost-visibility rules.
- Keeps BMS impact processing outside VMMS.
- Allows the VMMS-only code to be developed while counterpart work remains independently reviewable.

**Tradeoff**: no live end-to-end behavior exists until VRMS, BMS, and shared auth implement and approve the proposed interfaces.

## Decisions

- The existing Chief Mechanic `REPAIR` review action creates a VMMS referral outbox row atomically with the work-order transition.
- The referral includes failed inspection findings, Chief Mechanic remarks, and the work-order odometer reading; when none is saved, the current VMMS vehicle master odometer is the fallback.
- Delivery is retried with a stable referral ID. The 24-hour limit is configurable, after which an Admin can retry manually.
- VRMS rejection reopens the existing work order to its assigned mechanic as `REJECTED`, with the VRMS reason. It does not create a VMMS repair record.
- VRMS cancellation leaves the work order active in `FOR_REPAIR` and displays the reason to the Chief Mechanic. VRMS completion returns the schedule to Chief Mechanic final verification through the existing receiver behavior.
- Detailed ticket status is refreshed from VRMS when needed; the VMMS UI also displays the latest lifecycle status received by VMMS.
- Repair history is requested from VRMS on demand and is not cached or copied into VMMS persistence.
- Cost fields follow existing VMMS visibility: Admin, Operations, and Chief Mechanic may see them; Mechanic may not.
- Shop names must match an active VMMS outsourced-provider entry. VMMS never creates a provider from a VRMS event.
- VMMS emits BMS availability outbox rows only when the VMMS vehicle status actually changes. Each vehicle's outbox versions are delivered in order and retried until acknowledged.
- The user authorized a proposal and VMMS-only implementation, not partner-group approval. All shared interface details remain pending review.
