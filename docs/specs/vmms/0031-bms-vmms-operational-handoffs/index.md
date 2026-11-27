# 0031. BMS–VMMS operational handoffs

**Status**: Proposed VMMS-owned contract; BMS/shared-auth review and implementation authorization pending  
**Scope**: Completed-trip odometer evidence, utilization summaries, and pre-trip inspection defect intake from BMS to VMMS

Decision history: [rationale.md](rationale.md). Verification plan: [verify.md](verify.md). Detailed flow: [BMS–VMMS operational handoffs](../../../integration/bms-vmms-operational-handoffs.md).

## Summary

Define three one-way BMS-to-VMMS handoffs while retaining VMMS ownership of vehicle master readings and maintenance schedules. BMS messages are evidence or input to VMMS workflows, not permission for BMS to mutate VMMS data directly.

## Sources and current decisions

- Proposed BMS handoffs: completed-trip odometer evidence, utilization-based maintenance planning, and failed-item reports from a pre-trip checklist.
- Existing decisions: odometer readings remain pending until Operations confirms them; utilization informs review-only suggestions under a VMMS-approved policy.
- Proposed pre-trip model: the assigned driver completes the checklist in BMS, which retains the full inspection and sends only failed-item evidence to VMMS. Ownership and dispatch behavior remain pending BMS/VMMS review.
- Related VMMS requirements: FR-05.1 (Operations-owned master odometer), FR-07.* (maintenance scheduling), and FR-10.* (maintenance work-order checklists), as reconciled in the [VMMS scope](../../../scope/vmms/index.md). FR-10.* does not define a per-trip inspection; this flow is a scope extension.
- Related VMMS decision: [vehicle odometer ownership](../0003-operations-odometer-ownership/index.md).
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

### Flow F: pre-trip inspection defect handoff

- BMS presents a short, versioned checklist to the assigned driver immediately before dispatch. The driver completes the inspection; a dispatcher can view its status but does not attest on the driver's behalf.
- BMS owns the complete answers, driver identity, inspection history, attachments, and trip-dispatch decision. The full checklist is not copied into VMMS.
- If all items pass, BMS records the completed inspection and does not send an event to VMMS. If any item fails, BMS sends an immutable defect event containing stable inspection and trip IDs, the VMMS vehicle ID, checklist version, completion time, and only the failed item codes, agreed severity, and bounded notes. Customer, booking, and route data are excluded.
- BMS retains photos and other attachments. This flow does not transfer files or grant VMMS access to BMS storage.
- VMMS validates the BMS service identity and active vehicle, then stores the report as a pending Operations review. A successful response means durable receipt only; it does not mean the defect was confirmed or repaired.
- Operations may confirm or dismiss each reported defect with a reason. A confirmed defect may be handled through the existing VMMS maintenance workflow; VMMS does not automatically create a schedule or work order, change vehicle status, or update the master odometer.
- A pre-trip odometer, if recorded by BMS, remains BMS data. Flow D continues to cover final completed-trip odometer evidence; a pre-trip reading is not applied as master odometer evidence by this flow.
- Critical-failure dispatch blocking, severity definitions, and any override authority remain open for BMS/VMMS agreement before implementation. The proposed safety default is to block dispatch for a critical failure and audit any authorized override.
- BMS uses a stable `eventId` for delivery idempotency. Identical retries return the existing review state; reusing an ID with changed content is rejected.

## Proposed transport and security

- BMS calls VMMS through the suite gateway using a service token for audience `VMMS`, exact client `bms`, and narrowly scoped integration grants. Candidate scopes and routes are listed in the integration flow; shared-auth grants require owner review.
- BMS sends through a durable outbox with stable event IDs and bounded retries. VMMS atomically persists the idempotency receipt and accepted evidence, summary, or pending inspection-defect review.
- A successful intake response means the item has been durably accepted by VMMS; it does not mean an odometer was applied, a suggestion was approved, or an inspection defect was resolved.
- D, E, and F use stable `eventId` values for delivery idempotency. Same-ID/same-body retries return the existing intake state; same-ID/changed-body requests conflict. Flow E corrections use the agreed summary revision rule.
- All requests are system-to-system API calls. No cross-system database access, user-token substitution, client-selected VMMS actor, arbitrary file URL, or copied BMS operational data is allowed.
- Failures are explicit: malformed or hard-invalid payloads are not retried indefinitely; transient auth/network/service errors follow the documented retry policy; reusing an idempotency ID with changed content returns conflict.

## Acceptance criteria

1. A BMS trip reading is stored as pending evidence and never changes the VMMS master odometer until Operations confirms it.
2. Confirmation uses the existing Operations authorization, vehicle audit, odometer validation, and maintenance-schedule refresh behavior; stale/lower readings cannot silently overwrite the master.
3. Utilization summaries are scoped to a VMMS vehicle and period, versioned/idempotent, and contain only the agreed aggregates.
4. Utilization suggestions explain their evidence, follow the approved VMMS policy, and do not mutate vehicle, schedule, or work-order state without an Operations action.
5. The assigned BMS driver completes and attests to the versioned pre-trip checklist; BMS retains the full inspection, actor identity, and attachments.
6. Passing inspections remain in BMS. Failed inspections send only the agreed failed-item evidence to VMMS; customer, booking, route, and attachment data are not copied.
7. VMMS validates the exact BMS service identity, stores failed-item reports idempotently as pending Operations review, and returns a durable-acceptance response.
8. Operations can confirm or dismiss a reported defect with an audit reason; confirmation does not automatically create a schedule/work order or change vehicle status.
9. BMS remains the authority for trip dispatch readiness. Critical-failure blocking, severity mapping, and override behavior are agreed by both owners before implementation.
10. Pre-trip odometer values do not update `Vehicle.odometer`; completed-trip odometer evidence continues through Flow D.
11. Retries, duplicate IDs, changed payloads, unknown/inactive vehicles, malformed findings, and partial failures have explicit outcomes.
12. Existing manual fuel entry, Operations odometer ownership, maintenance workflow, audit behavior, and reports remain compatible; no BMS fuel-purchase handoff is included.

## Data and API impact

- Add VMMS service-only receivers and durable idempotency receipts for the three handoffs.
- Add an Operations review record and decision path for BMS-reported pre-trip defects. Do not copy complete inspections or attachments into VMMS.
- Add a utilization-summary and suggestion path; preserve the distinction between BMS trip aggregates and VMMS master-odometer audit history.
- Add migration-backed source/event/trip/inspection identifiers, failed-item evidence, review states, and decision audit data where needed.
- Do not apply migrations, add shared-auth grants, or change gateway routes as part of this proposal.

## Implementation gates

- BMS and VMMS must agree stable identifiers, correction/version rules, retention, payload bounds, exact route and response shapes.
- The VMMS utilization policy, thresholds, suggestion lifecycle, and Operations presentation must be defined before suggestions are enabled.
- BMS and VMMS must agree checklist ownership, template versioning, failure codes/severity, dispatch blocking and override rules, retention, and the minimum defect payload.
- BMS and VMMS must approve the Operations review lifecycle and authenticated service scopes with the shared-auth owner.
- Delivery retries use 30 seconds with exponential backoff capped at one hour, fail after 24 hours, and may be restarted by a BMS Admin. Rate limits and failure notifications must be agreed before implementation.
- Attachment viewing is out of scope. Any future viewer requires a separately authenticated BMS read API; this contract does not authorize one.

## Affected systems

- BMS: driver-facing pre-trip checklist, trip readiness decision, full inspection record, stable defect event IDs, durable outbox, and agreed utilization summaries.
- `welinc-backend-vmms`: authenticated receivers, idempotency, odometer evidence/review, utilization summaries, and pending inspection-defect review.
- `welinc-web-vmms`: Operations review and suggestion surfaces, including pre-trip defect review.
- VMMS analytics/report consumers: only if required to display approved BMS-derived data, without becoming an authority. No mobile change is currently in scope.
- Shared auth/gateway: proposed scopes/routes only after review and approval.

## Delivery status

The VMMS behavior boundaries are recorded as a proposal; this is not partner acceptance or implementation authorization. No application code, schema, auth grant, gateway route, or other-system implementation is authorized. The shared flow is recorded in [the integration guide](../../../integration/bms-vmms-operational-handoffs.md).
