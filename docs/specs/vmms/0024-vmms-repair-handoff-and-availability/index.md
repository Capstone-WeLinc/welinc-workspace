# 0024. VMMS repair handoff and fleet availability

**Status**: VMMS implementation in progress; proposed shared contract pending review and live integration pending
**Scope**: [Vehicles, garages, and fleet records](../../../scope/vmms/index.md#2-vehicles-garages-and-fleet-records); [Work orders, checklists, and maintenance history](../../../scope/vmms/index.md#4-work-orders-checklists-and-maintenance-history)

Cross-system contract proposal: [spec 0026](../0026-vmms-vrms-repair-referrals-and-bms-availability/index.md). Existing repair-status receiver: [spec 0023](../0023-vrms-repair-status-receiver/index.md); lifecycle contract: [spec 0025](../0025-vmms-vrms-repair-status/index.md).
Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Complete VMMS-owned behavior for sending a Chief Mechanic's `For Repair` work order to VRMS, tracking its outcome, showing VRMS repair history, and publishing vehicle availability and fleet-change updates to BMS. Serve BMS's fleet and pre-dispatch availability reads from VMMS. Do not edit VRMS, BMS, shared auth, gateway, analytics, or portal implementation.

## Requirements and behavior

- When the Chief Mechanic chooses `For Repair`, VMMS records a durable referral request containing the VMMS vehicle, work order, failed inspection findings, remarks, and odometer.
- VMMS retries temporary VRMS delivery failures with increasing delays for at most a configurable 24-hour window. The failed state is explicit (`Couldn't reach VRMS`); a VMMS Admin can manually retry using the original idempotency key.
- VRMS acceptance links a ticket ID/number to the referring VMMS work order. Referral rejection returns the work order to its assigned mechanic as `IN_PROGRESS` / `REJECTED` and displays the VRMS reason. VRMS cancellation leaves it open in `FOR_REPAIR`; VRMS completion returns it to Chief Mechanic final verification per spec 0023.
- VMMS shows current VRMS ticket status and reads repair history from VRMS on demand. VMMS does not store a repair-history copy.
- VMMS maps outsourced shop names to its active provider catalog and shows the catalog name.
- Every actual VMMS vehicle status change creates a durable, ordered BMS availability event. Repair status precedence remains `UNDER_REPAIR`, then `UNDER_MAINTENANCE`, then `AVAILABLE`.
- BMS reads VMMS garages and active vehicles using the VMMS service fleet API. The pre-dispatch vehicle read returns the current status, availability version, and whether the vehicle is assignable (`isActive` and `AVAILABLE`).
- VMMS emits durable fleet-change invalidation events when a vehicle or garage is created, materially updated, deactivated, or soft-deleted. BMS refreshes the canonical fleet read after an event; VMMS remains the only fleet-data writer.
- BMS fails closed for a dispatch check if VMMS cannot confirm the current vehicle state. BMS owns dispatch state such as `ON_DELIVERY`; it is not a VMMS vehicle status.
- If a repair starts while a delivery is active, BMS preserves the active trip state, flags the assignment for Operations follow-up, and prevents new assignments. The event does not silently cancel or reassign a vehicle already on the road.
- Existing VMMS role and cost access rules remain enforced in the backend; hidden UI controls are not authorization.

## Acceptance criteria

1. A Chief Mechanic `REPAIR` review creates one durable referral, and retries do not duplicate it.
2. Temporary delivery failures retry with growing delays to the configured limit; an Admin can manually retry a failed referral.
3. Acceptance links the repair number/status; rejection returns the work order to the assigned mechanic with the reason; cancellation leaves it open for Chief follow-up; completion returns it for final verification.
4. Work-order and mobile views expose referral/ticket status; the VMMS vehicle page exposes paged VRMS repair history without persisting it locally.
5. Mechanics do not receive repair-cost fields; existing Admin, Operations, and Chief Mechanic cost visibility is preserved.
6. An outsourced shop is displayed only through a matching active VMMS provider entry.
7. VMMS vehicle changes publish durable, idempotent, ordered status events to BMS; failed deliveries remain retryable and do not block VMMS status writes.
8. No VRMS, BMS, auth, gateway, analytics, or portal implementation is changed by this slice.
9. A BMS service token can read active garages and vehicles; a user token, wrong audience, or missing `fleet.read` scope is denied.
10. The pre-dispatch read for an active vehicle returns current status, availability version, and `isAssignable`, true only when status is `AVAILABLE`. Inactive, deleted, or unknown vehicle IDs retain the existing `404` behavior and cannot be assigned.
11. Actual vehicle and garage master-data changes create durable BMS fleet-change events; no-op updates do not. BMS can refresh its list from VMMS after receiving an event.
12. If VMMS cannot answer a pre-dispatch read, BMS must block the assignment rather than treating cached availability as current.

## API, data, and migration impact

- Add a VMMS referral retry/review API and service-side VRMS status/history reads under `/vmms/integrations/vrms`.
- Extend the VMMS VRMS event receiver for referral outcomes and live status updates.
- Expose the service-authenticated `GET /fleet/garages`, `GET /fleet/vehicles`, and `GET /fleet/vehicles/:id` reads to BMS under `fleet.read`; active vehicle responses include `availabilityVersion` and `isAssignable`. Preserve the existing `404` response for inactive, deleted, or unknown detail IDs.
- Add a durable VMMS BMS fleet-change outbox for vehicle/garage master-data invalidations. The proposed sender posts `{eventId, entityType, entityId, changeType, occurredAt}` to `POST /bms/integrations/vmms/fleet-changes` using a BMS service token with the proposed `fleet.change.write` scope; BMS refreshes canonical VMMS reads.
- Add migration-backed VMMS referral delivery, BMS availability outbox/version, and BMS fleet-change outbox state. Do not persist VRMS repair-history payloads.
- Add the configured referral retry window to `welinc-backend-vmms/.env.example`; do not add secrets or browser-exposed credentials.
- Add additive repair-referral metadata to VMMS work-order responses and mobile's local snapshot schema.

## Security and failure behavior

- Enforce service scopes and exact `client_id`/audience on inbound/outbound service calls.
- Allow BMS fleet reads only through a service token with `aud=VMMS`, `client_id=bms`, and `fleet.read`. Require a fresh VMMS read before assignment; any unavailable/error response must block BMS dispatch.
- Publish master-data invalidations with a stable event ID. The event prompts BMS to refresh current VMMS fleet data; it is not an authoritative snapshot and must not overwrite newer reads.
- Enforce VMMS Admin role for manual retry. Keep assignment checks on Chief/Mechanic work-order actions.
- Preserve existing maintenance-cost role filtering for VRMS history.
- Validate callback referral, vehicle, schedule, ticket, status, and provider associations before committing.
- Persist referral and BMS outbox state before network delivery; use stable IDs and idempotent requests.
- Show explicit `pending`, `failed`, and integration-unavailable states. Do not silently substitute stale repair status/history.
- Keep migration unapplied unless separately authorized.

## Affected repositories

- `welinc-backend-vmms`: referral/event/history integrations, vehicle status outbox, API, and migration.
- VMMS vehicle and garage write paths: durable fleet-change event creation in the same transaction as the master-data change.
- `welinc-web-vmms`: Admin retry and vehicle repair-history presentation.
- `welinc-mobile-vrms_vmms`: VMMS-only work-order referral/status presentation and offline snapshot metadata.
- No analytics changes; analytics remains a derived view.
- VRMS, BMS, auth, gateway, and portal changes are external dependencies, not part of this implementation.

## Delivery status

The VMMS fleet reads, transactional vehicle/garage invalidation outbox, and sender are implemented in `welinc-backend-vmms`; they have not been build- or runtime-verified. Overall implementation is not complete until each affected VMMS repository meets its acceptance criteria. The sender path, payload, and auth scope remain a proposal pending BMS/auth-owner review. Migration application, BMS fleet-change receiver and dispatch checks, auth grants, and live cross-system operation are pending.
