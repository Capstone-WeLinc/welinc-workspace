# 0026. VMMS repair referrals and fleet availability

**Status**: Proposed cross-system contract; pending VMMS, VRMS, and BMS group review
**Scope**: VMMS sends maintenance-to-repair referrals to VRMS, consumes VRMS repair outcomes and history, and publishes vehicle availability to BMS.

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Define API boundaries for the VMMS-owned side of maintenance-to-repair handoff and fleet availability. VMMS remains the authority for maintenance schedules and vehicle status; VRMS remains the authority for repair tickets and repair history; BMS consumes availability events to coordinate dispatch.

This proposal does not authorize or implement changes in VRMS, BMS, welinc-auth, the gateway, or the portal. The existing VRMS-to-VMMS event receiver remains described by [spec 0025](../0025-vmms-vrms-repair-status/index.md).

## Sources and decisions

- User-provided Flow 1 and Flow 2: VMMS referral and repair-history read; VRMS repair lifecycle; VMMS vehicle status; VMMS availability notification to BMS.
- User decision: implement only VMMS application code against proposed contracts; external contract review and counterpart implementations remain pending.
- User decision: after VRMS rejects a referral, return the work order to its assigned mechanic as `REJECTED`, with the VRMS reason.
- VMMS service-to-service API and auth patterns; VMMS work-order access and maintenance-cost visibility rules.

## Proposed contract

### VMMS to VRMS: submit a referral

- `POST /vrms/integrations/vmms/repair-referrals`
- Service token: `aud=VRMS`, `client_id=vmms`, scope `repair.referral.write`.
- Return `202 Accepted` with `{ "referralId": "<uuid>", "status": "PENDING" }`.
- `referralId` is the stable idempotency key. Retrying the same referral ID and body must not create another VRMS referral.
- Request body:

```json
{
  "referralId": "uuid",
  "vmmsVehicleId": "uuid",
  "vehiclePlate": "ABC123",
  "maintenanceScheduleId": "uuid",
  "workOrderNumber": "WO-20261125-000001",
  "odometerReading": 12345,
  "findings": [{ "checklistItemId": "uuid", "label": "Brake inspection", "note": "Wear beyond maintenance limits" }],
  "chiefMechanicRemarks": "Refer to repair"
}
```

- VMMS sends failed inspection checklist findings and Chief Mechanic remarks, not VMMS attachments, internal costs, or unrelated work-order fields.
- The odometer comes from the work-order service reading; if the work order has no reading, VMMS uses the current vehicle master reading.
- VRMS owns the referral queue and ticket creation. A pending or rejected referral is not itself a repair ticket.

### VRMS to VMMS: referral outcome and ticket lifecycle

- `POST /vmms/integrations/vrms/referral-events`, service token `aud=VMMS`, `client_id=vrms`, scope `repair.referral-status.write`.
- `REJECTED` includes the referral ID and a non-empty reason and creates no ticket. Acceptance is correlated through the repair lifecycle event stream in spec 0025.
- Opening a new ticket emits `OPENED`; adding a referral to an existing ticket emits `LINKS_UPDATED`. Both carry the complete accepted schedule-link set, ticket number, accepted referral IDs, and current ticket status. VMMS marks each matching referral accepted atomically with the lifecycle event.
- Extend the lifecycle stream with `STATUS_UPDATED` for `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `ON_HOLD`, `OUTSOURCED`, and `FOR_VERIFICATION`. The event includes the current status and, for `OUTSOURCED`, the canonical shop name. `COMPLETED` and `CANCELLED` remain terminal.
- All events are idempotent and ordered per ticket. Rejection events are idempotent per referral. VMMS validates that accepted referral and schedule identities match its pending referral record.
- VMMS matches an outside shop case-insensitively to its own active outsourced-provider catalog. An unmapped shop is a conflict; VRMS may retry after Operations adds the provider.
- A rejected referral returns its VMMS work order to `IN_PROGRESS` / `REJECTED`, clears the mechanic-submitted state, and exposes the VRMS reason to the assigned mechanic. A cancelled VRMS ticket leaves the linked VMMS work order open in `FOR_REPAIR` for Chief Mechanic follow-up.
- A completed ticket returns only explicitly linked VMMS work orders to Chief Mechanic final verification, as defined in spec 0025.

### VMMS to VRMS: repair status and history reads

- `GET /vrms/integrations/vmms/repairs/:repairTicketId`, service token `aud=VRMS`, `client_id=vmms`, scope `repair.status.read`.
- `GET /vrms/integrations/vmms/vehicles/:vmmsVehicleId/repair-history?cursor=<opaque>&limit=50`, service token scope `repair.history.read`, maximum page size 100.
- Status reads return ticket ID/number and current status. History entries return ticket number, opened/closed dates, issues, parts used, repair personnel/provider, and total repair cost, with a stable pagination cursor.
- VRMS remains the source of repair history. VMMS must not persist a history copy. VMMS may retain only the ticket linkage and event state needed by its work orders and vehicle-status rules.
- VMMS server-side authorization preserves existing maintenance-cost visibility: Admin, Operations, and Chief Mechanic may receive cost fields; Mechanic responses omit them.

### VMMS to BMS: vehicle availability event

- `POST /bms/integrations/vmms/vehicle-availability`, service token `aud=BMS`, `client_id=vmms`, scope `fleet.availability.write`.
- Each event includes a stable event UUID, VMMS vehicle UUID, plate, status (`AVAILABLE`, `UNDER_MAINTENANCE`, or `UNDER_REPAIR`), monotonically increasing per-vehicle version, and UTC occurrence time.
- VMMS creates a durable outbox event in the same transaction as each vehicle-status change. Delivery is idempotent and ordered per vehicle, with exponential retries capped at one hour until acknowledged.
- BMS owns the resulting trip/job-order review and notifications. It must not write VMMS vehicle status.

## Retry and failure behavior

- VMMS retries referral delivery after network errors, timeouts, 5xx, 429, and temporary authorization failures, using exponential backoff capped at one hour. `VMMS_REPAIR_REFERRAL_MAX_AGE_HOURS` defaults to 24. After that age, the referral becomes failed and an Admin may manually retry using the same referral ID.
- A non-retryable referral validation response is surfaced as an explicit failure; VMMS does not retry malformed requests.
- A failed VRMS or BMS read returns an explicit integration-unavailable response. VMMS does not return stale success-shaped data.
- BMS status events remain in the durable outbox and continue retrying until acknowledged; later versions for a vehicle must not overtake an earlier undelivered version.
- No request, event, or log contains service tokens or secret values.

## Affected repositories and pending dependencies

- `welinc-backend-vmms`, `welinc-web-vmms`, and the VMMS flows in `welinc-mobile-vrms_vmms`: implementation boundary for this task.
- Shared auth: proposed service-client scopes and grants for `vmms` and `vrms`; not changed here.
- VRMS: proposed referral command, outcome events, service status/history reads, and lifecycle event extensions; not changed here.
- BMS: proposed availability event receiver and booking-resolution behavior; not changed here.
- Workspace gateway: existing service paths must route to VRMS and BMS; no gateway route change is proposed.

This spec is a proposal, not evidence that the partner groups accepted the routes, payloads, scopes, retry policy, or status mapping. Live cross-system operation requires their review, auth grants, counterpart implementations, and deployment.
