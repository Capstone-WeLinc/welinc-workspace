# 0002. VMMS repair handoff: referrals in, repair events out (flows 1 and 2)

Child of [0029](index.md). Acceptance criteria AC-6 to AC-15 live in the umbrella.

## Summary

When a VMMS inspection ends "For Repair", VMMS sends VRMS a referral with the failed checklist findings. A VRMS Admin opens a ticket from it, adds it to the truck's open ticket, or rejects it with a reason. From then on, every ticket change is sent back to VMMS, which alone sets the truck's status and tells BMS. VMMS can also read one ticket's status and a truck's repair history whenever it needs them. This builds to the shapes VMMS already merged (specs vmms/0023 to vmms/0026).

## Referral intake

`POST /vrms/integrations/vmms/repair-referrals`, audience `VRMS`, client `vmms`, scope `repair.referral.write`, header `Idempotency-Key` equal to `referralId`.

| Field | Type | Rule |
|---|---|---|
| `referralId` | uuid | required |
| `vmmsVehicleId` | uuid | required |
| `vehiclePlate` | string | 1 to 20 |
| `maintenanceScheduleId` | uuid | required |
| `workOrderNumber` | string | 1 to 40 |
| `odometerReading` | int | 0 or more |
| `findings` | `{ checklistItemId: string, label: string, note: string or null }[]` | 1 to 100 items |
| `chiefMechanicRemarks` | string or null | any length |

**Lenient on text, strict on ids.** VMMS never retries a 4xx, so a refused referral is lost. Ids, the odometer and the findings count are validated (400 on failure). Text is trimmed and cut to the stored length rather than refused:
- `label` is cut to 200 characters, and an empty label becomes "Finding"
- `note` is cut to 2000 characters, and an empty note becomes null
- `chiefMechanicRemarks` is cut to 4000 characters, and empty becomes null
- `workOrderNumber` is cut to 40 characters and `vehiclePlate` to 20

The hash is taken over the body as received, before any cutting.

Steps, in one transaction:
1. Hash the canonical body (sorted keys, SHA 256), giving `payloadHash`.
2. If a `Referral` with this id exists: the same hash answers 202 `{ referralId, status, duplicate: true }`, and a different hash answers 409 `REFERRAL_ID_REUSED`.
3. Find the local truck by `vmmsVehicleId`. If it's missing, read it fresh (child 0001), and if VMMS still doesn't have it, answer 422 `VEHICLE_NOT_FOUND`.
4. Insert `Referral` with status `WAITING` and `receivedAt` now, and answer 202 `{ referralId, status: 'WAITING', duplicate: false }`.

202 is the exact code VMMS's sender expects.

## Deciding a referral (web and person routes)

| Route | Method | Inputs | Output | Auth | Errors |
|---|---|---|---|---|---|
| `/vrms/referrals?status&cursor&limit` | GET | status filter (default `WAITING`), limit 1 to 100 (default 25) | `{ items, nextCursor, waitingCount }` | `integration.respond` | 403 |
| `/vrms/referrals/:id` | GET | | the referral, its truck (plate, garage, open ticket number if any) | `integration.respond` | 404 `REFERRAL_NOT_FOUND` |
| `/vrms/repairs` | POST | the existing create body plus `referralId` uuid (opt); `driver` becomes optional when `referralId` is set | the ticket | `ticket.create` and `integration.respond` when `referralId` is set | 409 `REFERRAL_ALREADY_DECIDED`, 409 `OPEN_TICKET_EXISTS`, 422 `REFERRAL_VEHICLE_MISMATCH` (body truck differs from the referral's) |
| `/vrms/referrals/:id/add-to-ticket` | POST | `issues: { description, categoryId }[]` (1 to 100), `updatedAt` of the open ticket | the ticket | `integration.respond` | 409 `REFERRAL_ALREADY_DECIDED`, 409 `NO_OPEN_TICKET`, 409 `STALE` (ticket changed), spec 0019's issue edit refusals for the ticket's status |
| `/vrms/referrals/:id/reject` | POST | `reason` 5 to 500 | the referral | `integration.respond` | 409 `REFERRAL_ALREADY_DECIDED` |

Every decision locks the referral row (`FOR UPDATE`) and checks `status = WAITING` first, so two Admins can't both decide it. Opening a ticket sets `driverId` null only when `referralId` is set. Otherwise the existing driver rule stands.

**Driver shown as none.** Every place that reads a ticket's driver shows "None (from VMMS)" when `driverId` is null: the ticket list, detail, history, analytics (driver counts skip these tickets), and exports.

**Prefill** (web, from `GET /vrms/referrals/:id`): truck = referral's truck; garage = truck's `garageId`, and when that is null the garage field is empty and required as usual; odometer = `odometerReading`; one issue line per finding, with description `label` plus `": " + note` when there's a note, and category left for the Admin. The form shows a "From VMMS WO-…" header with the remarks.

**UI**: the Repairs page tabs are Tickets and Referrals (`?view=referrals`), with the waiting count on the Referrals tab. Rows open a side panel with the findings, remarks, odometer and WO number. Its buttons are "Open a ticket" or "Add to REP-…" (picked by whether the truck has an open ticket), and "Reject". Admin dashboard card: "Referrals waiting (n)", linking to the tab. Ticket detail and list: a "From VMMS WO-…" chip on tickets whose referral status is `OPENED_TICKET`.

## Repair events to VMMS

Written by one function, `queueVmmsRepairEvent(tx, ticketId, eventType)`, called from `create`, `applyStatusMove`, `add-to-ticket`, the referral link in create, and the late shop pick (AC-36). The caller has already locked the ticket row (`SELECT … FOR UPDATE`): `applyStatusMove` and the edit paths take that lock first, so two changes on one ticket queue in commit order. The function builds the payload from the ticket's state inside that `tx` and inserts a `Delivery` (target `VMMS`, kind `REPAIR_EVENT`). It assigns no version. The worker posts it to `POST {gateway}/vmms/integrations/vrms/repair-events` with audience `VMMS` and scope `fleet.repair-status.write`.

| Field | Source |
|---|---|
| `eventId` | the `Delivery.id` |
| `repairTicketId` | `RepairTicket.id` |
| `repairTicketNumber` | `RepairTicket.repairNumber` |
| `eventVersion` | filled in by the worker at send time: `RepairTicket.vmmsEventVersion + 1`. On a 2xx, the worker sets `vmmsEventVersion` to it. A failed or dismissed row never uses up a number, so VMMS's exact +1 rule always holds |
| `eventType` | `OPENED` on create. On adding a referral, `LINKS_UPDATED` when its schedule isn't linked yet, otherwise `STATUS_UPDATED` (VMMS refuses a `LINKS_UPDATED` that adds no schedule, ask 5). `STATUS_UPDATED` on any move to an open status and on the late shop pick, `COMPLETED` on the move to `CLOSED`, `CANCELLED` on the move to `CANCELLED` |
| `repairStatus` | mapped below; `OPENED` always sends `OPEN` |
| `vmmsVehicleId` | the truck's `vmmsVehicleId` |
| `maintenanceScheduleIds` | the distinct `maintenanceScheduleId` of the ticket's referrals in `OPENED_TICKET` or `ADDED_TO_TICKET`; empty for a ticket a person opened |
| `acceptedReferralIds` | the ids of those referrals |
| `occurredAt` | `now()` read inside the transaction after the ticket row is locked, UTC with `Z`. Locked commits on one ticket are serial, so times never go backwards, which VMMS checks |
| `outsideShopName` | `RepairTicket.outsideShopName` when the mapped status is `OUTSOURCED`, otherwise omitted. VMMS requires it there and refuses it elsewhere |
| `serviceOdometerReading` | omitted in slice 1 (flow 7, child 0005) |

Status mapping (VRMS → VMMS): `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `ON_HOLD`, `OUTSOURCED`, `FOR_VERIFICATION`, `CLOSED` and `CANCELLED` map to themselves, and `PENDING_APPROVAL` maps to `OUTSOURCED` (the truck is still at the outside shop), with the same shop.

**Known permanent refusals until VMMS's asks land.** These are VMMS answers that fail a row, block that ticket's later VMMS rows, and wait for an Admin to dismiss them on the Deliveries tab:
- 409 `INVALID_REPAIR_EVENT` when a linked schedule left `IN_PROGRESS` and `FOR_REPAIR` after the referral (ask 8)
- 404 `VEHICLE_NOT_FOUND` for a truck VMMS deactivated (ask 7, AC-35)
- 409 when VMMS deactivated the outside shop between pick and send

Dismissing one doesn't break the version count, because numbers are assigned at send.

## Outside shop (AC-36)

The outsource move (M9, to `OUTSOURCED`) gains a required `vmmsProviderId`. The dialog's picker reads `GET /vrms/config/outside-shops`, which proxies `GET {gateway}/vmms/fleet/outsourced-providers` (audience `VMMS`, `fleet.read`, 3 s timeout) and answers `{ shops: { id, name }[], stale: boolean }`. The last good list is kept in memory for 24 hours. When VMMS fails, the route answers that list with `stale: true`, or 503 `VMMS_UNAVAILABLE` when there is none. The move stores `vmmsProviderId` and `outsideShopName` (the name at pick time). Both stay through `PENDING_APPROVAL` and back. An outsourced ticket without a shop (data from before this spec) shows "Pick the outside shop". Picking one runs the same store, plus a `STATUS_UPDATED`. Until VMMS serves the route (ask 6), the build uses a local stub with VMMS's seed shop names.

A ticket created as `ASSIGNED` queues two events in the same `tx`: `OPENED` with `OPEN`, then `STATUS_UPDATED` with `ASSIGNED`. VMMS's receiver requires `OPENED` to carry `OPEN`.

Referral rejection: `queueReferralRejected(tx, referral)` inserts a `Delivery` (target `VMMS`, kind `REFERRAL_REJECTED`, `referralId` set) posted to `/vmms/integrations/vrms/referral-events` with scope `repair.referral-status.write`. Body: `{ eventId, referralId, eventType: 'REJECTED', reason, occurredAt }`. Not tied to a ticket, so it has no ordering wait.

## Reads VMMS calls

**Status**: `GET /vrms/integrations/vmms/repairs/:repairTicketId`, client `vmms`, scope `repair.status.read`. It answers `{ repairTicketId, repairTicketNumber, status, outsideShopName }`, with the status mapped as above and the shop name only when the mapped status is `OUTSOURCED` (null otherwise). An unknown id answers 404 `REPAIR_NOT_FOUND`.

**History**: `GET /vrms/integrations/vmms/vehicles/:vmmsVehicleId/repair-history?limit=50&cursor=`, client `vmms`, scope `repair.history.read`. Tickets on that truck with status not `CANCELLED`, ordered by `createdAt` descending then `id`. The cursor is base64url of `{ createdAt, id }`. Answer `{ items, nextCursor }` (null on the last page). An unknown truck answers 200 `{ items: [], nextCursor: null }`.

| Item field | Source |
|---|---|
| `repairTicketId`, `repairTicketNumber` | `id`, `repairNumber` |
| `openedAt`, `closedAt` | `createdAt`, `closedAt` (null while open) |
| `status` | mapped as above |
| `issues` | each `RepairIssue`: `"<category name>: <description>"`, or the description alone without a category |
| `partsUsed` | each `RepairPart`: `"<description> x<quantity>"`, no price |
| `repairPersonnel` | the distinct `Mechanic.name` of the ticket's `TicketAssignment` rows |
| `provider` | `RepairTicket.outsideShopName`, or null for a ticket never outsourced |
| `totalRepairCost` | `RepairTicket.totalCost` as a decimal string, or null |

VMMS hides the cost from its own mechanics at its boundary. VRMS sends it to the `vmms` client only.

## Invariants

- A referral leaves `WAITING` exactly once, by a person with `integration.respond`.
- A ticket's `maintenanceScheduleIds` and `acceptedReferralIds` only grow, which matches VMMS's 409 on removal.
- `vmmsEventVersion` is the last version VMMS accepted. It rises by exactly 1 per sent event, and only the worker writes it.
- Every VMMS event is queued with the ticket row locked, in the change's own transaction.
- A ticket in `OUTSOURCED` or `PENDING_APPROVAL` has an outside shop, except tickets from before this spec, which show "Pick the outside shop".
- `driverId` is null only when a referral with `OPENED_TICKET` points at the ticket.

## Critical test scenarios

- Happy path: a referral comes in, the Admin opens a ticket from the prefilled form, and VMMS gets `OPENED` with the referral and schedule ids. Verifies **AC-6**, **AC-8**, **AC-13**.
- Concurrency: two Admins decide the same referral at once, and one gets 409 `REFERRAL_ALREADY_DECIDED`. Verifies **AC-8**, **AC-10**.
- Duplicate: VMMS resends the same referral and gets 202 `duplicate: true` with no second row. A changed body gets 409. Verifies **AC-6**.
- Permission: a Chief Mechanic without `integration.respond` gets 403 on reject and sees no buttons. Verifies **AC-11**.
- History: 120 tickets with one cancelled page as 50, 50, 19, with no prices and no cancelled ticket. Verifies **AC-15**.

**Inline rationale**: building to VMMS's merged shapes costs VRMS nothing extra and keeps their work. The asks in the umbrella change behaviour or add read routes; none changes a payload VMMS already accepts. Acceptance is carried by the repair events (`acceptedReferralIds`) instead of a separate "accepted" message, as VMMS built it, so VMMS learns the ticket and the acceptance in one ordered stream.
