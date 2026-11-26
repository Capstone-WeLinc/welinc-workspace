# 0005. Slice 2: flows 4 to 7 and the register request

Child of [0029](index.md). Flows 4 to 7 were asked of VMMS on 2026-11-26 (in `docs/integration/repair-integration.md`), so VMMS builds its side while VRMS builds slice 1. VRMS builds them after slice 1. The register request is not asked yet. VMMS has no code for any of these yet.

## Summary

Four more flows and one request finish the seven agreed flows:

- **Flow 4:** a truck beyond repair becomes a retirement request to VMMS.
- **Flow 5:** a repair that keeps coming back is flagged and sent to VMMS's repeated failures list.
- **Flow 6:** a VMMS fuel anomaly can be referred for repair like an inspection finding.
- **Flow 7:** odometer readings travel with the repair messages.
- **Register request:** VRMS can ask VMMS to register a truck it doesn't know.

All of them reuse slice 1's plumbing (child 0004), so each is a payload, a route and a screen change.

## Acceptance criteria

- **AC-28 (flow 4)**: verifying a ticket offers "Close as beyond repair" with a required reason (5 to 500 characters). It closes the ticket but sends no `COMPLETED`. It queues a retirement request to VMMS instead, so the truck stays Under Repair. VMMS's decision comes back through `POST /vrms/integrations/vmms/retirement-decisions`. On `APPROVED` (VMMS deactivated the truck), VRMS sends no `COMPLETED`, because VMMS would answer 404 for an inactive truck. VMMS's approval closes its own record of the repair (part of ask 2), and the sync marks the truck inactive. On `DECLINED` (with a reason), VRMS opens a new `OPEN` ticket on the truck that links the old one, with no driver, and the Admin is shown the reason. The new ticket's `OPENED` is queued first and the old ticket's `COMPLETED` second, so VMMS never sees the truck without an open repair.
- **AC-29 (flow 5)**: on every close, VRMS counts the truck's tickets closed within `repairs.repeatWindowDays` (setting, default 90) that share an issue category with this one. When a category reaches `repairs.repeatCount` (setting, default 3), the ticket shows a "Repeat repair" chip and VRMS queues a repeat repair alert to VMMS. The alert is sent once per category per window.
- **AC-30 (flow 6)**: the referral intake accepts `source: 'FUEL_ANOMALY'` with `fuelTransactionId` and no `maintenanceScheduleId`. The Referrals tab and the prefill treat it like an inspection referral, and its chip reads "From VMMS fuel anomaly". It is listed in `acceptedReferralIds` but adds no schedule id.
- **AC-31 (flow 7)**: the new ticket form's odometer starts at the truck's VMMS odometer (fresh read). A lower value is refused with 422 `ODOMETER_BELOW_VMMS`. `OPENED` carries the opening reading. Verifying a ticket asks for the closing odometer (at least the opening one), stored as `RepairTicket.closingOdometer`, and `COMPLETED` carries it as `serviceOdometerReading`.
- **AC-32 (register request)**: when a truck search has no match, the new ticket form offers "Ask VMMS to add it". It sends a register request (plate, model, optional garage, a note, the requester's name) and lists the request as Waiting on the form. When a truck with that plate arrives through the sync, the request turns Ready and the truck becomes selectable. A second request for the same plate while one waits is refused with 409 `REGISTER_REQUEST_PENDING`.
- **AC-33**: the new client grants: `vrms` on `VMMS` gets `vehicle.retire.write`, `repair.repeat.write` and `vehicle.register.write`; `vmms` on `VRMS` gets `retirement.decision.write`.
- **AC-34**: `docs/integration/repair-integration.md` gains these routes and payloads.

## Data model additions

- `RepairTicket`: `closeOutcome` (`REPAIRED`, `BEYOND_REPAIR`, default `REPAIRED`), `closingOdometer` int?, `previousTicketId` uuid? (FK self, set on the ticket opened after a declined retirement), `isRepeatRepair` boolean default false (an event that happened at close, not a value worked out on read).
- `RetirementRequest` (new): `id` uuid, `repairTicketId` FK, `reason`, `status` (`WAITING`, `APPROVED`, `DECLINED`), `decisionReason`?, `decidedAt`?, `receivedPayloadHash`?.
- `RepeatAlert` (new): `id`, `vehicleId`, `categoryId`, `repairTicketIds` uuid[], `windowStart`, `sentAt`. Unique (`vehicleId`, `categoryId`, `windowStart`).
- `RegisterRequest` (new): `id`, `plateNumber`, `model`, `garageId`?, `note`?, `requestedByUserId`, `requestedByName`, `status` (`WAITING`, `READY`), `vehicleId`?, `createdAt`. A partial unique index on `lower(plateNumber)` where status is `WAITING`.
- `Referral`: `source` (`INSPECTION`, `FUEL_ANOMALY`, default `INSPECTION`), `fuelTransactionId` uuid?, `maintenanceScheduleId` becomes nullable (required when the source is `INSPECTION`).
- Settings: `repairs.repeatCount` (3, 2 to 10), `repairs.repeatWindowDays` (90, 7 to 365).

## Messages (new `Delivery` kinds and routes)

| Kind or route | Direction | Path | Body |
|---|---|---|---|
| `RETIREMENT_REQUEST` | VRMS → VMMS | `/vmms/integrations/vrms/retirement-requests` | `{ eventId, requestId, vmmsVehicleId, repairTicketId, repairTicketNumber, reason, occurredAt }` |
| retirement decision | VMMS → VRMS | `POST /vrms/integrations/vmms/retirement-decisions` (scope `retirement.decision.write`) | `{ eventId, requestId, decision: 'APPROVED' \| 'DECLINED', reason?, occurredAt }`; duplicates by `eventId` hash |
| `REPEAT_REPAIR` | VRMS → VMMS | `/vmms/integrations/vrms/repeat-repairs` | `{ eventId, vmmsVehicleId, category, repairTicketNumbers[], windowDays, count, occurredAt }` |
| fuel anomaly referral | VMMS → VRMS | the slice 1 intake | `source: 'FUEL_ANOMALY'`, `fuelTransactionId`, findings with the anomaly text, no `maintenanceScheduleId` |
| `REGISTER_REQUEST` | VRMS → VMMS | `/vmms/integrations/vrms/vehicle-register-requests` | `{ eventId, requestId, plateNumber, model, vmmsGarageId?, note?, requestedByName, occurredAt }` |
| odometer | VRMS → VMMS | slice 1 repair events | `serviceOdometerReading` on `OPENED` and `COMPLETED` |

## Asks of VMMS for slice 2

1. Accept `serviceOdometerReading` on `OPENED`. Treat the `COMPLETED` one as a pending reading for Operations to confirm, which keeps their odometer ownership rule.
2. Build the retirement request receiver and the decision sender. Approving is deactivating the truck (`isActive`), since VMMS has no Retired status.
3. Build the repeat repair receiver, and add its alerts to the existing repeated failures list (today it counts maintenance jobs only).
4. Add "Refer for repair" on the fuel anomaly screen for the VMMS Admin and Chief Mechanic, sending the referral above.
5. Later, not asked yet: build the register request receiver, and show waiting requests in the truck list for Operations to complete.

## Build plan (slice 2)

1. welinc-auth grants (AC-33). Satisfies **AC-33**
2. Migration with the additions above. Satisfies **AC-28** to **AC-32**
3. Flow 7 (smallest; it rides on existing events). Satisfies **AC-31**
4. Flow 6 (intake change only). Satisfies **AC-30**
5. Register request. Satisfies **AC-32**
6. Flow 5. Satisfies **AC-29**
7. Flow 4 (the most states). Satisfies **AC-28**
8. The doc (AC-34). Satisfies **AC-34**

**Inline rationale**: every slice 2 flow needs VMMS to build something first, so building them before slice 1 works end to end would leave VRMS code that nothing calls. The order runs smallest and least dependent first.
