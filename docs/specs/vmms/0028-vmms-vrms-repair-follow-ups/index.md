# 0028. VMMS and VRMS repair follow-ups

**Status**: VMMS implementation complete; partner contract review and live integration pending  
**Scope**: [Vehicles, garages, and fleet records](../../../scope/vmms/index.md#2-vehicles-garages-and-fleet-records), [Work orders, checklists, and maintenance history](../../../scope/vmms/index.md#4-work-orders-checklists-and-maintenance-history), and [Fuel expenses and anomaly handling](../../../scope/vmms/index.md#5-fuel-expenses-and-anomaly-handling)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Complete VMMS-owned implementation for VRMS beyond-repair retirement requests, repeated-repair alerts, and fuel-anomaly referrals (repair integration Flows 4–6). VMMS owns its vehicle, maintenance, anomaly, and operational decision data. VRMS remains authoritative for repair tickets and repeat-repair thresholds.

## Sources and decisions

- Shared [repair-integration checklist](../../../integration/repair-integration.md), Flows 4–6 and routes 1, 14–16.
- VMMS repair handoff and event contracts in [spec 0024](../0024-vmms-repair-handoff-and-availability/index.md), [spec 0025](../0025-vmms-vrms-repair-status/index.md), and [spec 0026](../0026-vmms-vrms-repair-referrals-and-bms-availability/index.md).
- User decisions for this slice:
  - A `FUEL_ANOMALY` referral omits both `maintenanceScheduleId` and `workOrderNumber`; it identifies the source with `fuelTransactionId`.
  - Operations cannot approve retirement while another VRMS repair remains open for the vehicle.
- The shared checklist describes proposed routes and scopes. VMMS implementation does not imply acceptance by VRMS or shared auth owners.

## Behavior

### Flow 4: beyond-repair retirement

- Receive `POST /vmms/integrations/vrms/retirement-requests` with a VRMS service token (`aud=VMMS`, `client_id=vrms`, `vehicle.retire.write`).
- Persist the request and its event receipt. An identical replay is acknowledged without a second request; reuse of an event or request ID with different data conflicts.
- Validate the request against the existing open VMMS repair state for the same vehicle and ticket. Expose pending requests, ticket number, reason, vehicle, and occurrence time to Operations.
- Operations may approve or decline once. A decline requires a non-empty reason. Decisions are persisted with an outbox event and sent to `POST /vrms/integrations/vmms/retirement-decisions` using `aud=VRMS`, `client_id=vmms`, and `retirement.decision.write`; retries reuse the same event ID.
- Approval is one transaction: lock and validate the vehicle/request/ticket, reject approval if any other VRMS repair is open for the vehicle, close the requested VMMS repair state, recompute mechanical status, deactivate the vehicle, record the fleet invalidation, and queue the decision. Any failure leaves the request pending and makes no partial change.
- Decline leaves VMMS vehicle and repair state unchanged. VRMS opens a replacement ticket before completing the declined ticket; VMMS permits this temporary overlap only when the existing open ticket has a declined retirement request. Completing the old ticket leaves the replacement repair active.

### Flow 5: repeated-repair alerts

- Receive route 15 at `POST /vmms/integrations/vrms/repeat-repairs` with `aud=VMMS`, `client_id=vrms`, and `repair.repeat.write`.
- Persist the VRMS event ID, vehicle, category, ticket numbers, threshold window, count, and occurrence time. Identical replay succeeds; reusing an event ID with a different payload conflicts.
- Show persisted VRMS alerts alongside existing maintenance repeated-failure alerts in VMMS AI Analytics. VMMS does not recalculate VRMS thresholds or treat analytics as the event source.
- Provide bounded, cursor-paginated reads to Admin and Operations. Keep the event history read-only in VMMS.

### Flow 6: fuel-anomaly referrals

- Admin and Chief Mechanic may refer an open fuel anomaly from its anomaly screen. Only this anomaly view is available to Chief Mechanic; do not expose fuel-entry, reporting, or cost controls.
- Create the referral through the existing durable VRMS referral outbox. The request uses `source: 'FUEL_ANOMALY'`, `fuelTransactionId` equal to the source fill-up UUID, an anomaly finding, and the fill-up odometer (or vehicle master odometer if no valid fill-up reading exists).
- Omit `maintenanceScheduleId` and `workOrderNumber` for this source. The existing finding shape is retained, using the anomaly UUID as the finding correlation ID. Include anomaly details and efficiency measurements, never fuel cost or unrelated fill-up fields.
- One referral is allowed per fuel transaction. Return the existing referral state on duplicate submission; do not create a second referral after delivery failure or outcome. Admin may use the existing failed-referral retry action.
- Backend authorization and response filtering remain authoritative; Chief Mechanic responses do not include fuel-cost fields.

## Acceptance criteria

1. A valid VRMS retirement request is durably stored and appears in the Operations queue with its ticket, vehicle, reason, and time.
2. Exact request replays are idempotent; conflicting event/request ID reuse is rejected without changing stored state.
3. Operations approval deactivates the vehicle, closes only the requested VMMS repair state, recomputes vehicle status, records fleet invalidation, and queues one stable route-16 decision atomically.
4. Approval is blocked without deciding the request if another VRMS repair is open for that vehicle. Operations can decline with a required reason; decline does not change vehicle/repair status and queues a stable route-16 decision. During VRMS replacement-ticket handoff, VMMS permits only the overlap with the declined ticket and retains the replacement repair after the old ticket completes.
5. Route-16 delivery uses the exact VMMS service identity and scope, is idempotent, and retries transient failures without duplicating decisions.
6. Route-15 alerts are persisted once per event ID, reject conflicting replays, and are listed with maintenance repeated failures in AI Analytics.
7. Repeated-repair alert reads are cursor-paginated, bounded, and restricted to VMMS Admin and Operations.
8. Admin and Chief Mechanic can refer an open fuel anomaly; the referral has the fuel source fields and finding but no schedule ID, work-order number, fuel cost, or unrelated fill-up data.
9. Chief Mechanic can access only the anomaly portion needed to refer; fuel-entry, reporting, and cost data remain unavailable. Fuel role checks are enforced by the backend, not only hidden in the UI.
10. A second referral attempt for the same fuel transaction returns the existing referral and creates no duplicate. Admin can retry a failed delivery using the original referral ID.
11. VMMS does not change VRMS, BMS, auth, gateway, analytics, portal, or mobile implementation. Partner implementation, service grants, migration application, and live cross-system operation remain separately verified dependencies.

## API, data, and migration impact

- Add migration-backed VRMS retirement request/event state, repeat-repair alert state, and retirement-decision outbox state.
- Make referral schedule and work-order references optional and add a unique nullable fuel-transaction reference plus source discriminator. Preserve inspection-referral constraints and existing records.
- Add service-authenticated VRMS request/event receivers, Operations decision and read endpoints, an Admin/Operations repeat-alert read endpoint, and the route-16 sender.
- Add an Admin/Chief Mechanic fuel-anomaly referral action, using the existing referral delivery outbox. Keep Chief Mechanic anomaly responses free of fuel costs.
- No shared checklist/spec, shared auth client grant, VRMS, BMS, analytics, portal, or mobile changes are included.

## Security and failure behavior

- Enforce service token type, exact client, audience, and dedicated scope on inbound requests and outbound decisions.
- Require VMMS Operations for retirement decisions and VMMS Admin/Operations for repeated-alert reads. Require VMMS Admin or Chief Mechanic for fuel referrals.
- Validate UUIDs, bounded text/list sizes, UTC timestamps, vehicle-ticket relationships, and state transitions before persistence.
- Persist each inbound event before acknowledging it. Use transactions and stable IDs for decision state/outbox; surface conflicts and delivery status explicitly.
- Do not allow service-supplied retirement requests to deactivate vehicles. Only an authorized Operations decision can do so.
- Keep fuel amount/cost and unrelated maintenance fields out of VRMS referral payloads and Chief Mechanic responses.

## Affected repositories

- `welinc-backend-vmms`: event persistence, APIs, authorization, referral creation, transaction/outbox, and migration.
- `welinc-web-vmms`: Operations retirement queue, anomaly-only Chief Mechanic view and referral action, and AI Analytics alert presentation.
- No mobile changes are required for Flows 4–6.
- VRMS and shared auth implementation/grants are external dependencies; do not edit their repositories.

## Delivery status

VMMS backend and web implementation is complete. Focused tests and builds pass; see [verify.md](verify.md). The migration is created but remains unapplied. Route compatibility, partner review, service grants, migration application, and live VRMS event delivery remain pending.
