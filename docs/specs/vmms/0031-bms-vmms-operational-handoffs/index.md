# 0031. BMS–VMMS operational handoffs

**Status**: Proposed VMMS-owned contract; BMS/shared-auth review and implementation authorization pending  
**Scope**: Completed-trip odometer evidence, utilization summaries, and delivery fuel-purchase intake from BMS to VMMS

Decision history: [rationale.md](rationale.md). Verification plan: [verify.md](verify.md). Detailed flow: [BMS–VMMS operational handoffs](../../../integration/bms-vmms-operational-handoffs.md).

## Summary

Define three one-way BMS-to-VMMS handoffs while retaining VMMS ownership of vehicle master readings, maintenance schedules, and fuel records. BMS messages are evidence or input to VMMS workflows, not permission for BMS to mutate VMMS data directly.

## Sources and settled behavior

- User-requested BMS handoffs: completed-trip odometer evidence, utilization-based maintenance planning, and delivery fuel-purchase handoff.
- User decisions: odometer readings remain pending until Operations confirms them; utilization informs review-only suggestions under a VMMS-approved policy; every accepted BMS fuel purchase remains pending until Operations approves it; fuel stations require an explicit VMMS mapping.
- VMMS source requirements: FR-05.1 (Operations-owned master odometer), FR-07.* (maintenance triggers and scheduling), FR-16.2 (fuel-entry fields), and FR-23.*–FR-26.* (fuel reports), as reconciled in the [VMMS scope](../../../scope/vmms/index.md).
- Related VMMS decisions: [vehicle odometer ownership](../0003-operations-odometer-ownership/index.md), [fuel-station management](../0007-fuel-station-management/index.md), and [fuel reporting](../0020-fuel-reports-filtering-and-efficiency/index.md).
- System-to-system APIs are the only permitted integration boundary. No cross-system database access is in scope.

## Contract

### Flow D: completed-trip odometer evidence

- BMS submits an immutable completed-trip odometer reading for a VMMS vehicle.
- VMMS validates the service identity, active vehicle, trip identifier, timestamp, and reading; duplicate delivery is idempotent.
- VMMS stores the reading as pending evidence. It does not update `Vehicle.odometer`, maintenance status, or schedule thresholds on receipt.
- Operations reviews and confirms or dismisses the evidence. Confirmation calls the existing Operations-owned master-odometer update behavior, including its audit and eligible schedule refresh. A reading that is stale, lower than the current master, or otherwise invalid cannot silently lower or replace the master.
- Review states are `PENDING`, `CONFIRMED`, and `DISMISSED`; the authenticated Operations actor and decision time are retained.
- BMS trip identifiers and the minimum evidence needed for review are retained; booking, customer, route, and address details are not copied.

### Flow E: utilization-based maintenance suggestions

- BMS submits bounded per-vehicle summaries of completed-trip count/frequency and distance for an explicit period. It does not send passenger/customer, booking, or route details.
- VMMS validates and idempotently stores summaries by vehicle and period, including an explicit revision for corrections.
- VMMS may use a VMMS-approved utilization policy to produce suggestions. The policy and its thresholds are set during implementation. Suggestions explain the period and metrics used and are review-only.
- Utilization summaries and suggestions never update the master odometer, create a schedule, change an existing schedule, or trigger a work order automatically.
- Operations decides whether to bring maintenance forward through the existing scheduling workflow. Summary windows, utilization thresholds, and suggestion lifecycle require owner agreement before implementation.

### Flow F: fuel-purchase handoff

- BMS submits a completed delivery refuelling purchase with stable BMS purchase and trip identifiers, VMMS vehicle ID, purchase time, odometer, liters, unit price/currency, station identity, and an opaque receipt reference.
- VMMS accepts a valid submission into a pending-review record. No BMS purchase is written to the confirmed fuel ledger before Operations approval, even when the submitted values are otherwise valid and non-suspicious.
- Operations resolves the BMS station ID through an explicit VMMS-maintained mapping to an active VMMS station. An unmapped station remains pending until Operations resolves it; station-name similarity alone is not a mapping.
- On approval, VMMS creates the fuel transaction through its existing validation and audit path. The server calculates the total from liters and unit price. Rejected or pending submissions are excluded from confirmed fuel reports and efficiency calculations.
- Review states are `PENDING_REVIEW`, `APPROVED`, and `REJECTED`; only an authenticated Operations approval creates the VMMS fuel transaction.
- The BMS purchase identifier is the idempotency key. A byte-equivalent retry returns the prior outcome; reuse with changed content is rejected. Possible matches to manually entered fuel are flagged for review rather than silently discarded.
- Hard-invalid values are rejected with an actionable 4xx response. A missing station mapping is not a hard-invalid purchase and remains reviewable.
- The receipt reference is an opaque BMS identifier, not a URL or copied file. This contract does not add receipt retrieval or grant VMMS access to BMS files.
- The payload uses `PHP`. A missing `isFullTank` value is treated as `false`; VMMS must not infer a full tank.

## Proposed transport and security

- BMS calls VMMS through the suite gateway using a service token for audience `VMMS`, exact client `bms`, and narrowly scoped integration grants. Candidate scopes and routes are listed in the integration flow; shared-auth grants require owner review.
- BMS sends through a durable outbox with stable event IDs and bounded retries. VMMS atomically persists the idempotency receipt and accepted evidence, summary, or pending fuel-review record.
- A successful intake response means the item has been durably accepted by VMMS; it does not mean an odometer was applied or a fuel transaction was approved.
- D and E use stable `eventId` values for delivery idempotency. F uses the immutable BMS `purchaseId` as its business idempotency key and also retains the stable delivery `eventId`. Same-ID/same-body retries return the existing intake state; same-ID/changed-body requests conflict.
- All requests are system-to-system API calls. No cross-system database access, user-token substitution, client-selected VMMS actor, arbitrary receipt URL, or copied BMS operational data is allowed.
- Failures are explicit: malformed or hard-invalid payloads are not retried indefinitely; transient auth/network/service errors follow the documented retry policy; reusing an idempotency ID with changed content returns conflict.

## Acceptance criteria

1. A BMS trip reading is stored as pending evidence and never changes the VMMS master odometer until Operations confirms it.
2. Confirmation uses the existing Operations authorization, vehicle audit, odometer validation, and maintenance-schedule refresh behavior; stale/lower readings cannot silently overwrite the master.
3. Utilization summaries are scoped to a VMMS vehicle and period, versioned/idempotent, and contain only the agreed aggregates.
4. Utilization suggestions explain their evidence, follow the approved VMMS policy, and do not mutate vehicle, schedule, or work-order state without an Operations action.
5. Every accepted BMS fuel purchase is persisted as pending review; it cannot create a confirmed fuel transaction or appear in confirmed reports/efficiency before Operations approval.
6. Operations can resolve a BMS station identifier only through an explicit mapping to an active VMMS station; unresolved submissions remain pending.
7. Approving a purchase uses existing VMMS fuel validation and audit behavior, computes totals server-side, and attributes the approval to the actual Operations user. Rejected/pending items remain outside confirmed reports and efficiency.
8. Hard-invalid fuel data returns an explicit error. Possible manual duplicates remain reviewable and are not silently discarded.
9. Receipt references are opaque identifiers only; VMMS neither follows arbitrary URLs nor reads BMS storage directly.
10. Every route requires the exact BMS service identity, VMMS audience, and dedicated scope. BMS cannot supply a VMMS user or actor identity.
11. Retries, duplicate IDs, changed payloads, corrections, unknown/inactive vehicles, unmapped stations, and partial failures have explicit outcomes.
12. Existing manual fuel entry, Operations odometer ownership, maintenance workflow, audit behavior, and reports remain compatible.

## Data and API impact

- Add VMMS service-only receivers and durable idempotency receipts for the three handoffs.
- Add an Operations review record and decision path for trip-odometer evidence and all accepted BMS fuel purchases. Fuel approval creates the VMMS fuel transaction through the existing domain service.
- Add a utilization-summary and suggestion path; preserve the distinction between BMS trip aggregates and VMMS master-odometer audit history.
- Add migration-backed source/event/trip/purchase identifiers, review states, decision audit data, station mapping, and opaque receipt reference where needed.
- Do not apply migrations, add shared-auth grants, or change gateway routes as part of this proposal.

## Implementation gates

- BMS and VMMS must agree stable identifiers, correction/version rules, retention, payload bounds, exact route and response shapes.
- The VMMS utilization policy, thresholds, suggestion lifecycle, and Operations presentation must be defined before suggestions are enabled.
- BMS and VMMS must approve the station mapping lifecycle and authenticated service scopes with the shared-auth owner.
- Confirm BMS can provide the required purchase timestamp and PHP amounts; if full-tank state is absent, VMMS treats it as false.
- Delivery retries use 30 seconds with exponential backoff capped at one hour, fail after 24 hours, and may be restarted by a BMS Admin. Rate limits and failure notifications must be agreed before implementation.
- Receipt viewing is out of scope. Any future viewer requires a separately authenticated BMS read API; this contract does not authorize one.

## Affected systems

- BMS: trip completion and fuel purchase event production, stable IDs, durable outbox, and agreed utilization summaries.
- `welinc-backend-vmms`: authenticated receivers, idempotency, evidence/review, utilization summaries, fuel validation/audit/report integration, station mapping, and migrations.
- `welinc-web-vmms`: Operations review and suggestion surfaces.
- VMMS analytics/report consumers: only if required to display approved BMS-derived data, without becoming an authority. No mobile change is currently in scope.
- Shared auth/gateway: proposed scopes/routes only after review and approval.

## Delivery status

The VMMS behavior boundaries are recorded as a proposal; this is not partner acceptance or implementation authorization. No application code, schema, auth grant, gateway route, or other-system implementation is authorized. The shared flow is recorded in [the integration guide](../../../integration/bms-vmms-operational-handoffs.md).
