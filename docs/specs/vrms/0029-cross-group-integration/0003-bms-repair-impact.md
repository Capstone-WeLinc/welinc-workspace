# 0003. BMS repair impact: trips, expected return date, expedite (flow 3, BMS Flow C)

Child of [0029](index.md). Acceptance criteria AC-16 to AC-20 live in the umbrella.

## Summary

While a truck is in repair, BMS needs to know why and when it should be back, so dispatch can move bookings. VRMS sends BMS an update on every ticket change. BMS can read the current repair at any time, and it can ask VRMS to hurry (an expedite request) for a specific Job Order. A VRMS Admin accepts, which raises the priority and can set a new date, or declines with a reason. VRMS also shows the truck's upcoming trips from BMS, so the Admin sees what a repair puts at risk. BMS has built none of its side yet, so this child is also the shape BMS builds to.

## VRMS reads BMS: upcoming trips (BMS builds the route)

`GET {gateway}/bms/integrations/vrms/vehicles/:vmmsVehicleId/schedule?days=14`, audience `BMS`, client `vrms`, scope `schedule.read`, answering `Cache-Control: no-store`.

Answer `{ items: { bookingNumber, jobOrderNumber | null, serviceDate: 'YYYY-MM-DD', dispatchTime: 'HH:MM' | null, status }[] }`. The items are BMS `DispatchAssignment` rows for that `vehicleId` in state `PENDING` or `CONFIRMED`, with `serviceDate` from today (Asia/Manila) to today + `days` (1 to 31, default 14), ordered by date and time. `jobOrderNumber` comes from the active `DispatchJobOrder`. Only schedule facts cross: no client name, address or rate. The same route can serve VMMS for BMS Flow B with a `vmms` grant.

VRMS proxies it through `GET /vrms/repairs/vehicle-schedule?vehicleId=<local id>` (`ticket.create` or `TICKET_READ`). Timeout 3 s. Any failure answers 200 `{ available: false }`, and the web shows "BMS can't be reached". Nothing is stored. The web shows it on the new ticket form after a truck is picked (a compact list under the truck) and as an "Upcoming trips" card on the ticket detail page while the ticket is open.

## VRMS tells BMS: repair updates

`queueBmsRepairUpdate(tx, ticketId, changeReason)` builds the payload from the ticket's state inside the change's transaction (ticket row locked, as for VMMS) and inserts a `Delivery` (target `BMS`, kind `REPAIR_UPDATE`). The payload is frozen there: a retry resends it as stored, even if issues changed since, because a later change queues its own update. It is posted to `POST {gateway}/bms/integrations/vrms/repair-updates` with audience `BMS` and scope `repair.update.write`. BMS answers any 2xx.

It's called from the same places as `queueVmmsRepairEvent` (create, every status move, close, cancel) and from `setDueAt`.

| Field | Source |
|---|---|
| `eventId` | `Delivery.id` |
| `eventVersion` | filled in by the worker at send time, `RepairTicket.bmsEventVersion + 1`, and saved on a 2xx (as for VMMS); BMS keeps the highest it has seen and ignores lower ones |
| `vmmsVehicleId`, `vehiclePlate` | the truck's `vmmsVehicleId`, `plateNumber` |
| `repairTicketId`, `repairTicketNumber` | `id`, `repairNumber` |
| `repairStatus` | VRMS's own status (all nine values) |
| `repairStatusLabel` | VRMS's display label for it (for example "On hold") |
| `reason` | the distinct `IssueCategory.name` of the ticket's issues, in `sortOrder`, joined with ", "; "Not yet diagnosed" when none have a category |
| `expectedReturnAt` | `RepairTicket.dueAt` (ISO, UTC), or null; always null when the status is `CLOSED` or `CANCELLED` |
| `changeReason` | the reason passed in: "Repair opened", "Status changed to <label>", the due date change reason, "Repair finished", "Repair cancelled" |
| `occurredAt` | the change's time, UTC |

Dismissing a failed `REPAIR_UPDATE` on the Deliveries tab queues a fresh one with the ticket's current state (change reason "Resent after a failed delivery"), so BMS never keeps a stale return date.

BMS writes `statusReason` from `reason`, `expectedBackAt` from `expectedReturnAt` and `statusRemarks` from `changeReason` on `VehicleDispatchProfile`, and flags bookings before that date. The truck's availability itself still comes from VMMS (flow 2).

**The one due date writer.** `setDueAt(tx, ticket, { dueAt, source, reason })` is the only code that writes `RepairTicket.dueAt` and `dueAtSource`. It writes the audit row and calls `queueBmsRepairUpdate` with `reason` whenever the value changes. Slice 1 calls it only from expedite acceptance (`source: MANUAL`). Feature 42's spec must route every due date write through it.

## BMS asks VRMS: expedite requests

`POST /vrms/integrations/bms/expedite-requests`, client `bms`, scope `repair.expedite.write`.

| Field | Type | Rule |
|---|---|---|
| `requestId` | uuid | required; the duplicate key |
| `vmmsVehicleId` | uuid | required |
| `jobOrderNumber` | string | 1 to 40 |
| `reason` | string | 5 to 1000 |
| `neededBy` | `YYYY-MM-DD` | optional |

In one transaction: hash the body. An existing id with the same hash answers 202 duplicate, and with a different hash answers 409 `REQUEST_ID_REUSED`. Then find the truck's open ticket, answering 404 `NO_OPEN_REPAIR` when there is none (BMS should not retry). Insert `ExpediteRequest` `WAITING`, write an audit row on the ticket (actor `SYSTEM`, name `BMS`, action `EXPEDITE_REQUESTED`), and answer 202 `{ requestId, status: 'WAITING', repairTicketNumber }`. Each request is its own row, so several JOs may ask about one repair.

**Answering (person routes, `integration.respond`)**

| Route | Method | Inputs | Errors |
|---|---|---|---|
| `/vrms/expedite-requests/:id/accept` | POST | `priority` (`LOW` to `CRITICAL`, required, defaults in the web to one step above the ticket's; a `CRITICAL` ticket stays `CRITICAL`, and `newPriority` records `CRITICAL`), `dueAt` ISO (opt), `updatedAt` of the ticket | 409 `EXPEDITE_ALREADY_DECIDED`, 409 `STALE` |

A request can be answered while its ticket is in any open status, including `OUTSOURCED`, `PENDING_APPROVAL` and `FOR_VERIFICATION`. The priority change uses the spec 0019 edit path, and only fails where that path refuses.
| `/vrms/expedite-requests/:id/decline` | POST | `reason` 5 to 500 | 409 `EXPEDITE_ALREADY_DECIDED` |

Accept, in one transaction: lock the request (`FOR UPDATE`, must be `WAITING`). Set the ticket priority through the spec 0019 edit path with the reason "Expedite <JO>". If `dueAt` is set, call `setDueAt(…, { source: MANUAL, reason: 'Expedite <JO>' })`. Set the request to `ACCEPTED` with `newPriority`, `newDueAt` and the decider, then queue the answer.

Decline sets `DECLINED` with `responseReason` and queues the answer.

On the ticket's move to `CLOSED` or `CANCELLED`, every `WAITING` request on it becomes `DECLINED` with "Repair finished" or "Repair cancelled", audited with actor `SYSTEM` (name `VRMS`), and each answer is queued after the close's own repair update in the same transaction. `seq` order then puts the update first.

**The answer**: a `Delivery` (target `BMS`, kind `EXPEDITE_ANSWER`, `expediteRequestId` set) to `POST {gateway}/bms/integrations/vrms/expedite-answers`, scope `repair.update.write`. Body: `{ eventId, requestId, repairTicketNumber, decision: 'ACCEPTED' | 'DECLINED', reason: string | null, priority: string | null, expectedReturnAt: string | null, occurredAt }`. It carries the ticket id, so it waits behind earlier BMS deliveries for that ticket.

**UI**: on the ticket detail page, a banner lists each waiting request (JO, reason, needed by, received). Accept opens a dialog with the priority select and an optional due date, and Decline opens a reason dialog. The Admin dashboard card reads "Expedite requests (n)" and lists them with links.

## BMS reads VRMS: the active repair

`GET /vrms/integrations/bms/vehicles/:vmmsVehicleId/active-repair`, client `bms`, scope `repair.status.read`.

| Field | Source |
|---|---|
| `repair` | null when the truck has no open ticket (200, not 404) |
| `repairTicketId`, `repairTicketNumber` | the open ticket |
| `repairStatus`, `repairStatusLabel` | as in the update |
| `reason` | as in the update |
| `issuesResolved`, `issuesTotal` | count of the ticket's `RepairIssue` with `resolvedAt` set, and all of them |
| `expectedReturnAt` | `dueAt` or null |
| `openedAt` | `createdAt` |

## Invariants

- Only `setDueAt` writes `dueAt`, and every change reaches BMS.
- BMS never receives costs, notes, people or mechanic text: the reason is category names only.
- An expedite request leaves `WAITING` exactly once.

## Critical test scenarios

- Happy path: BMS asks for JO-2026-0142, the Admin accepts with High and a date, and BMS gets the answer and an update with the new `expectedReturnAt`. Verifies **AC-18**, **AC-19**, **AC-17**.
- Failure: BMS is down while the Admin opens the form, the card says so, the ticket saves, and the update is retried. Verifies **AC-16**, **AC-21**.
- Edge: a request for a truck with no open ticket gets 404 `NO_OPEN_REPAIR`. Closing a ticket declines its two waiting requests. Verifies **AC-18**, **AC-19**.
- Privacy: the active repair answer and the update hold no cost or note fields. Verifies **AC-20**, **AC-17**.

**Inline rationale**: BMS already has empty columns and a dashboard waiting for exactly these facts (`VehicleDispatchProfile`). Sending them as updates fills those, and the live read covers a page that opens while an update is still retrying. The schedule is read live, not copied, because dispatch changes all day, and a stale list of trips is worse than "BMS can't be reached".
