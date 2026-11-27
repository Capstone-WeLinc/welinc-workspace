# Rationale

Decision record for [index.md](index.md).

## Context

The shared repair integration checklist defines three remaining VMMS flows: fuel-anomaly referrals (Flow 6), repeated-repair event intake (Flow 5), and beyond-repair retirement requests/decisions (Flow 4). Existing VMMS code supports schedule-based referrals and repair lifecycle events but does not model these event types or their UI.

These are cross-system interfaces. VMMS can implement its own durable state and callers, but cannot claim VRMS/auth acceptance or change their repositories. Existing VMMS rules also require fuel-cost filtering, transaction-safe vehicle changes, and preserving repair-ticket ownership in VRMS.

## Options considered

### Keep fuel anomaly referrals attached to a maintenance schedule

**Rejected**: fuel anomalies have a fuel transaction as their source and may have no maintenance schedule. Fabricating a schedule or work-order number would misstate ownership and could create an invalid VRMS link.

### Use a source-specific, schedule-free fuel referral (chosen)

Store `source` and the fuel transaction reference, omit maintenance/work-order identifiers, and keep the existing durable referral delivery path. Use the anomaly UUID in the existing finding correlation field.

**Tradeoff**: VRMS must accept the documented source-specific payload extension; this remains a partner contract dependency.

### Treat retirement receipt as authorization to deactivate

**Rejected**: a service event is a request from VRMS, not a VMMS user decision. Direct deactivation would bypass Operations review and the existing repair-open guard.

### Require an explicit Operations decision with an atomic retirement transaction (chosen)

Persist the request, require Operations approval/decline, and send a durable decision event. Approval closes only the requested repair and deactivates the vehicle in one transaction. If another repair remains open, keep the request pending and refuse approval.

**Tradeoff**: Operations must resolve other open repair requests before approving retirement.

### Recompute repeat-repair thresholds in VMMS

**Rejected**: VRMS owns repair tickets and the configured category/window threshold. VMMS stores the event as supplied and presents it beside its maintenance-derived alerts.

### Keep VRMS alerts in the core VMMS service and render them in AI Analytics (chosen)

Persist the canonical inbound event in `welinc-backend-vmms` and read it through a bounded API. AI Analytics remains a presentation surface, not the source of the alert.

## Decisions

- Use the exact route payloads and scopes from the shared repair integration checklist; partner review and service grants remain pending.
- Event ID replay with the same payload is idempotent; an ID reused for different content is a conflict.
- One fuel referral is allowed per fuel transaction. The source anomaly must still be open when the referral is created.
- Chief Mechanic access is limited to the fuel-anomaly view and referral action; no fuel entry, reports, or costs are exposed.
- Operations approval is blocked if any other VRMS repair state is open for the vehicle. Decline requires a reason.
- Retirement approval closes the requested repair, recomputes VMMS vehicle status, deactivates the vehicle, and emits fleet invalidation plus route-16 delivery in one transaction.
- After a decline, VRMS may open a replacement ticket before completing the declined ticket. VMMS permits that temporary overlap only when the existing open ticket has a declined retirement request; completion of the old ticket leaves the replacement repair active.
- No counterpart, shared auth, gateway, analytics-service, or mobile code is part of this VMMS implementation.
