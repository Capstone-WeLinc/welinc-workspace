# Repair integration (VRMS with VMMS and BMS)

Repairs across the three systems: VMMS refers trucks for repair, VRMS runs the repair, and BMS plans bookings around it. Your checklist is first. The exact routes and payloads are in the [reference](#reference) below. Full design: VRMS spec [0029](../specs/vrms/0029-cross-group-integration/index.md). Every route VRMS serves, with each answer and error code, is in VRMS's API docs: `http://localhost:3000/vrms/docs` (or `https://staging-api.welinc.app/vrms/docs`), under *Integrations: VMMS* and *Integrations: BMS*.

## VMMS checklist

Your referral sender already works with VRMS (checked on local stacks on 2026-11-27). One fix blocks the rest of flows 1 and 2; the others make them sturdier.

- [ ] **Fix the advisory locks in your two VRMS receivers (blocks every repair event).** `vrms-repair-events.service.ts` (around line 101) and the referral event receiver (around line 377) run `SELECT pg_advisory_xact_lock(...)` through `$queryRaw`. That function returns `void`, which Prisma 7's Postgres adapter can't read, so every call answers 500 (`UnsupportedNativeDataType`). Use `$executeRaw` for those lines. VRMS keeps each event and retries it for 24 hours, so nothing is lost while you fix it.
- [ ] **Send referrals from your every minute job only**, not inside the Chief Mechanic's request (`maintenance-schedules.service.ts` awaits `deliverOne`, so the tap waits up to 5 s on VRMS).
- [ ] **Check a maintenance schedule's state only when it is first linked**, not on every event. Today, if a work order changes after its referral, every later event for that ticket answers 409.
- [ ] **Refuse to deactivate a truck that has an open VRMS repair**, and name the ticket. Otherwise every later event for it answers 404.
- [ ] **Serve the outside shop list to services**: `GET /vmms/fleet/outsourced-providers` behind `fleet.read`, answering `{ providers: { id, name }[] }`, active only, ordered by name. VRMS needs it to outsource a ticket ([route 8](#routes)).
- [ ] **Send `fleet-changes` to VRMS too** ([route 6](#routes)): the same body you send BMS, with audience `VRMS`.
- [ ] **Retry 401 and 403 within the 24 hours**, like 5xx (your referral sender fails them for good today).
- [ ] **Accept any `eventVersion` above the last one**, not only +1, and ignore lower ones. A safety net: VRMS never skips.
- [ ] **Let `LINKS_UPDATED` add only referrals**, without a new schedule. Until then VRMS sends `STATUS_UPDATED` for that case.
- [ ] **Mobile:** allow "For Repair" when any checklist item fails (today it needs more failed than passed).
- [ ] **Your own fixes toward BMS:** stop retrying a 400 forever in the availability sender (it blocks that truck's later events), and check `client_id === 'bms'` on the fleet routes.
- [ ] **Test flows 1 and 2 with us.** VRMS's side is built (see [When you can test](#when-you-can-test)); your receiver fix above comes first.

**Flows 4 to 7** (build these alongside, smallest first; shapes in [Flows 4 to 7](#flows-4-to-7-vmms-and-vrms)):

- [ ] **Flow 7, odometer:** accept `serviceOdometerReading` on `OPENED` (the reading when the repair starts). Treat the one on `COMPLETED` as a pending reading for Operations to confirm, as your odometer rule already works.
- [ ] **Flow 6, fuel anomaly:** add "Refer for repair" on the fuel anomaly screen for the Admin and Chief Mechanic. It sends a referral (route 1) with `source: 'FUEL_ANOMALY'`, `fuelTransactionId`, the anomaly as the finding, and no `maintenanceScheduleId`.
- [ ] **Flow 5, repeat repair:** receive route 15 and add each alert to your repeated failures list beside the maintenance ones.
- [ ] **Flow 4, retire a truck:**
  - receive route 14 and show Operations the request with its ticket and reason
  - approving deactivates the truck (`isActive` false) and closes your record of that repair, since VRMS sends no `COMPLETED` for it
  - declining needs a reason
  - send the decision on route 16

**Later, not yet:** a register request, for VRMS to ask you to add a truck you don't have.

## BMS checklist

Nothing for repairs is built in BMS yet. All of it is new. VRMS's side is built and was checked against a stand in for your routes, so your shapes below are the ones VRMS already sends and reads.

- [ ] **Route your gateway:** add `/bms/integrations/vrms/*` and `/bms/integrations/vmms/*` to `bms-gateway/src/routes.ts`.
- [ ] **Serve the truck's upcoming trips** ([route 9](#route-9-upcoming-trips-bms-serves)) behind `schedule.read` for client `vrms`.
- [ ] **Receive repair updates** ([route 10](#route-10-repair-update-vrms-sends-bms-receives)): write `VehicleDispatchProfile.statusReason`, `expectedBackAt` and `statusRemarks`, and flag bookings before `expectedReturnAt` as "Affected by repair REP-…" for Operations and Customer Support.
- [ ] **Send expedite requests** ([route 11](#route-11-expedite-request-bms-sends-vrms-serves)), one per affected Job Order, with the [retry rule](#the-retry-rule) and a BMS Admin retry button.
- [ ] **Receive expedite answers** ([route 12](#route-12-expedite-answer-vrms-sends-bms-receives)) and show them to Operations.
- [ ] **Show the active repair** ([route 13](#route-13-active-repair-vrms-serves)) on your booking and truck pages: status, issues done of total, expected back.
- [ ] **Receive VMMS's availability and fleet change events** (spec vmms/0026). Your grants come with this change.
- [ ] **Test flow 3 with us** once both sides are in.

## VRMS checklist (ours, so you know when to test)

- [x] **welinc-auth grants** for all three clients ([table](#auth-grants)). Your token requests are refused until this is on staging.
- [x] **Referral intake, the Referrals tab, and repair events back to VMMS** (routes 1, 2, 3). VMMS can test flow 1 from here.
- [x] **Status and history reads, the outside shop picker, the fleet copy** (routes 4 to 8). Until route 8 exists, VRMS shows four stand in shops.
- [x] **Flow 3:** trips card, repair updates, expedite requests and answers, the active repair read (routes 9 to 13), against a stand in for BMS. Checked against BMS once your routes land.
- [ ] **Flows 7, 6, 5, 4**, in that order: the opening and closing odometer, fuel anomaly referrals, the "Repeat repair" mark, "Close as beyond repair" (routes 14 to 16).
- [ ] **On staging**: grants applied, fleet linked, all flows checked.

## When you can test

**VMMS, flow 1** (once VRMS's second box is ticked; local stacks with shared, VRMS and VMMS up and migrated):
1. As a VMMS Chief Mechanic in the mobile app, mark an inspection with a failed item "For Repair".
2. As `vrms.admin@welinc.com`, open Repairs, then Referrals, then "Open a ticket", and save. The work order shows the ticket number, and the truck shows Under Repair in VMMS (and in BMS's fleet list).
3. Close the ticket in VRMS. VMMS starts its final check, and once that passes the truck is Available again.
4. Stop VMMS, change a ticket's status, and start VMMS again. The event arrives within a minute, and VRMS's Deliveries tab (Audit Logs page) shows the retries.

**BMS, flow 3:** open a ticket on a truck with a confirmed Job Order. VRMS shows the trip, and BMS flags the booking. Send an expedite request, accept it in VRMS with a new date, and BMS gets the answer and the new date.

---

# Reference

## Who owns what

| System | Owns | Never does |
|---|---|---|
| VMMS | trucks, garages, outside shops, truck status | stores repair data beyond ticket ids, numbers, status and shop |
| VRMS | repair tickets, issues, parts, costs | writes truck status or edits trucks (it keeps a read only copy) |
| BMS | bookings, dispatch, Job Orders | writes truck status, or sees repair costs and notes |

## How every call works

- **Tokens:** a service token from `POST /auth/token` (`client_credentials`, the target system as `audience`, the scope). The copied `service-token-client.ts` does it.
- **Gateway:** call through the suite gateway's internal address, `SUITE_GATEWAY_INTERNAL_URL`.
- **Receivers check:** the token is a service token (403 `WRONG_TOKEN_USE` for a person's), `aud` is their own system (401 `WRONG_AUDIENCE`), and the scope and the caller's `client_id` match (403 `FORBIDDEN`). An expired token is 401 `TOKEN_EXPIRED`; when the receiver can't reach welinc-auth's keys it answers 503 `AUTH_UNAVAILABLE`. Every answer carries `Cache-Control: no-store`.
- **Duplicates:** every message has an id (`eventId`, `referralId`, `requestId`). The same id with the same body answers success again with `duplicate: true`. The same id with a different body answers 409.
- **Full state:** events carry the full current state plus an `eventVersion` per ticket. Times are UTC ISO 8601 ending in `Z`.

### The retry rule

| Answer | Sender does |
|---|---|
| any 2xx | done |
| 401, 403, 408, 429, 5xx, network error, timeout (5 s) | retry after 30 s, doubling up to 1 hour |
| any other 4xx | failed at once; keep the code and show it to an Admin |
| still failing 24 hours after the first try | failed (VRMS marks it on the first failed answer after that) |

A failed message gets a Retry button for an Admin, and Retry restarts the 24 hours. Messages for one repair ticket go in order: a later one waits while an earlier one is failed.

### Auth grants

| Client | Audience | Scopes |
|---|---|---|
| `vrms` | `VMMS` | `fleet.read`, `fleet.repair-status.write`, `repair.referral-status.write` |
| `vrms` | `BMS` | `schedule.read`, `repair.update.write` |
| `vmms` | `VRMS` | `repair.referral.write`, `repair.status.read`, `repair.history.read`, `fleet.change.write` |
| `vmms` | `BMS` | `fleet.availability.write`, `fleet.change.write` |
| `bms` | `VRMS` | `repair.status.read`, `repair.expedite.write` |

Flows 4 and 5 add `vrms` on `VMMS`: `vehicle.retire.write` and `repair.repeat.write`; and `vmms` on `VRMS`: `retirement.decision.write`.

## Routes

| # | Caller → served by | Route | Scope | Built |
|---|---|---|---|---|
| 1 | VMMS → VRMS | `POST /vrms/integrations/vmms/repair-referrals` | `repair.referral.write` | both |
| 2 | VRMS → VMMS | `POST /vmms/integrations/vrms/repair-events` | `fleet.repair-status.write` | both (VMMS answers 500, see your checklist) |
| 3 | VRMS → VMMS | `POST /vmms/integrations/vrms/referral-events` | `repair.referral-status.write` | both (VMMS answers 500, same fix) |
| 4 | VMMS → VRMS | `GET /vrms/integrations/vmms/repairs/:repairTicketId` | `repair.status.read` | both |
| 5 | VMMS → VRMS | `GET /vrms/integrations/vmms/vehicles/:vmmsVehicleId/repair-history` | `repair.history.read` | both |
| 6 | VMMS → VRMS | `POST /vrms/integrations/vmms/fleet-changes` | `fleet.change.write` | VRMS yes, VMMS sender no |
| 7 | VRMS → VMMS | `GET /vmms/fleet/vehicles`, `/vehicles/:id`, `/garages` | `fleet.read` | both |
| 8 | VRMS → VMMS | `GET /vmms/fleet/outsourced-providers` | `fleet.read` | VRMS reader yes, VMMS no |
| 9 | VRMS → BMS | `GET /bms/integrations/vrms/vehicles/:vmmsVehicleId/schedule` | `schedule.read` | VRMS reader yes, BMS no |
| 10 | VRMS → BMS | `POST /bms/integrations/vrms/repair-updates` | `repair.update.write` | VRMS sender yes, BMS no |
| 11 | BMS → VRMS | `POST /vrms/integrations/bms/expedite-requests` | `repair.expedite.write` | VRMS yes, BMS sender no |
| 12 | VRMS → BMS | `POST /bms/integrations/vrms/expedite-answers` | `repair.update.write` | VRMS sender yes, BMS no |
| 13 | BMS → VRMS | `GET /vrms/integrations/bms/vehicles/:vmmsVehicleId/active-repair` | `repair.status.read` | VRMS yes, BMS client no |
| 14 | VRMS → VMMS | `POST /vmms/integrations/vrms/retirement-requests` | `vehicle.retire.write` | no |
| 15 | VRMS → VMMS | `POST /vmms/integrations/vrms/repeat-repairs` | `repair.repeat.write` | no |
| 16 | VMMS → VRMS | `POST /vrms/integrations/vmms/retirement-decisions` | `retirement.decision.write` | no |

## Flows 1 and 2: VMMS and VRMS

A Chief Mechanic's "For Repair" sends a referral (route 1). A VRMS Admin opens a ticket from it, adds it to the truck's open ticket, or rejects it (route 3). Every ticket change then goes to VMMS (route 2), and VMMS sets the truck's status and tells BMS.

### Route 1: referral (VMMS sends, as built)

Header `Idempotency-Key: <referralId>`.

```ts
{
  referralId: string;            // uuid, the duplicate key
  vmmsVehicleId: string;
  vehiclePlate: string;
  maintenanceScheduleId: string;
  workOrderNumber: string;       // WO-…
  odometerReading: number;       // whole number, 0 or more
  findings: { checklistItemId: string; label: string; note: string | null }[]; // failed items, 1 to 100
  chiefMechanicRemarks: string | null;
}
```

| VRMS answers | When |
|---|---|
| 202 `{ referralId, status: 'WAITING', duplicate: false }` | stored |
| 202 `{ …, duplicate: true }` | the same referral again |
| 409 `REFERRAL_ID_REUSED` | the same id with a different body |
| 422 `VEHICLE_NOT_FOUND` | VMMS itself doesn't have the truck |
| 400 `IDEMPOTENCY_KEY_MISMATCH` | `Idempotency-Key` not equal to `referralId` |
| 400 | a bad id, odometer or findings count |
| 503 `VMMS_UNAVAILABLE` | VRMS doesn't know the truck yet and couldn't read it from you within 3 s; retry |

Long text is cut, never refused: the plate at 20 characters, the work order number at 40, a finding's label at 200 and note at 2,000, the remarks at 4,000.

### Route 2: repair events (VRMS sends, VMMS receives, as built)

```ts
{
  eventId: string;
  repairTicketId: string;           // never changes for a ticket
  repairTicketNumber: string;       // REP-YYYYMMDD-XXXX
  eventVersion: number;             // 1, 2, 3 … per ticket, no gaps
  eventType: 'OPENED' | 'LINKS_UPDATED' | 'STATUS_UPDATED' | 'COMPLETED' | 'CANCELLED';
  repairStatus: 'OPEN' | 'ASSIGNED' | 'IN_PROGRESS' | 'ON_HOLD' | 'OUTSOURCED' | 'FOR_VERIFICATION' | 'CLOSED' | 'CANCELLED';
  vmmsVehicleId: string;
  maintenanceScheduleIds: string[]; // all linked so far, only grows
  acceptedReferralIds: string[];    // all accepted so far, only grows
  outsideShopName?: string;         // only with OUTSOURCED, the shop the Admin picked from your list (route 8)
  occurredAt: string;
}
```

| VRMS ticket event | `eventType` | `repairStatus` |
|---|---|---|
| created | `OPENED` | `OPEN` (created as Assigned: `STATUS_UPDATED` `ASSIGNED` right after) |
| referral added, new schedule | `LINKS_UPDATED` | current |
| referral added, schedule already linked | `STATUS_UPDATED` | current |
| any move to an open status | `STATUS_UPDATED` | the new one |
| VRMS's Pending approval | `STATUS_UPDATED` | `OUTSOURCED`, same shop |
| verified and closed | `COMPLETED` | `CLOSED` |
| cancelled | `CANCELLED` | `CANCELLED` |

Every VRMS ticket is sent, not only referral ones. A ticket a person opened has empty id lists.

### Route 3: referral rejected (VRMS sends)

`{ eventId, referralId, eventType: 'REJECTED', reason /* 5 to 500 */, occurredAt }`

### Routes 4 and 5: VMMS reads

- **Route 4** answers `{ repairTicketId, repairTicketNumber, status, outsideShopName }`, with the status as in route 2 and the shop only while `OUTSOURCED` (else null). An unknown id answers 404 `REPAIR_NOT_FOUND`.
- **Route 5**, `?limit=1..100` (default 50) `&cursor=<opaque>`, answers `{ items, nextCursor }`, newest first: closed tickets plus the open one, never cancelled ones. A truck VRMS has no tickets for answers no items, not 404. A cursor VRMS didn't make answers 400 `INVALID_CURSOR`; `nextCursor` is null on the last page.

```ts
{
  repairTicketId: string; repairTicketNumber: string;
  openedAt: string; closedAt: string | null; status: string;
  issues: string[];               // "Brakes: grinding front left"
  partsUsed: string[];            // "Brake pad set x2", never a price
  repairPersonnel: string[];      // mechanic names
  provider: string | null;        // the outside shop
  totalRepairCost: string | null; // decimal string
}
```

### Routes 6 to 8: VRMS's fleet copy

- **Route 6:** the same body you send BMS, `{ eventId, entityType: 'VEHICLE' | 'GARAGE', entityId, changeType, occurredAt }`. VRMS answers 202 `{ accepted: true }` at once, then reads the record fresh (route 7). It never uses the message's other fields.
- **Hourly:** VRMS reads the full lists to catch anything missed (`fleet.reconcileMinutes`, a VRMS setting). It skips a run when your list comes back empty or would archive more than 20% of the trucks, and reports it instead.
- **Route 8:** feeds the outside shop picker when an Admin outsources a ticket. VRMS keeps the last good list for 24 hours. Until you serve it, a 404 there makes VRMS show four stand in shops.

## Flows 4 to 7: VMMS and VRMS

**Flow 7, odometer.**
- **On `OPENED`:** route 2 adds `serviceOdometerReading` (int), the reading when the repair starts. VRMS starts it from your last reading and refuses a lower one.
- **On `COMPLETED`:** it carries the closing reading, which VRMS asks for at verification.

**Flow 6, fuel anomaly.** Route 1 takes two more fields:

```ts
{
  source?: 'INSPECTION' | 'FUEL_ANOMALY'; // default INSPECTION
  fuelTransactionId?: string;             // uuid, required with FUEL_ANOMALY
  maintenanceScheduleId?: string;         // required with INSPECTION, left out with FUEL_ANOMALY
}
```

The anomaly goes in `findings` (one item, the anomaly as `label`, the details as `note`). You hear back as for any referral: route 2 lists it in `acceptedReferralIds`, with no schedule id, or route 3 rejects it.

**Flow 5, repeat repair (route 15).** When a ticket closes and an issue category has hit the set count on that truck within the set window (VRMS settings, default 3 within 90 days), VRMS sends this once per category per window:

```ts
{ eventId: string; vmmsVehicleId: string; category: string; repairTicketNumbers: string[]; windowDays: number; count: number; occurredAt: string }
```

**Flow 4, retire a truck (routes 14 and 16).** A VRMS Admin closes a ticket "Beyond repair" with a reason.
- **The request:** VRMS sends route 14 instead of `COMPLETED`, so the truck stays Under Repair.

```ts
// route 14, VRMS → VMMS
{ eventId: string; requestId: string; vmmsVehicleId: string; repairTicketId: string; repairTicketNumber: string; reason: string; occurredAt: string }
// route 16, VMMS → VRMS
{ eventId: string; requestId: string; decision: 'APPROVED' | 'DECLINED'; reason?: string /* required when declined */; occurredAt: string }
```

- **Approved:** you deactivate the truck and close your record of that repair. VRMS sends nothing more for it.
- **Declined:** VRMS opens a new ticket on the truck, linked to the old one, and sends its `OPENED` first, then `COMPLETED` for the old one. That way the truck never shows without an open repair.
- **Route 16 answers:** 202, with the usual duplicate rule on `eventId`.

## Flow 3: BMS and VRMS (BMS Flow C)

VRMS sends BMS an update on every ticket change (route 10). BMS can read the current repair (route 13) and ask to hurry for a Job Order (route 11), and VRMS answers on route 12. VRMS shows the truck's upcoming trips from route 9. Truck availability still comes from VMMS only.

### Route 9: upcoming trips (BMS serves)

`GET …/schedule?days=14` (accept 1 to 31; VRMS always asks for 14):

```ts
{ items: {
  bookingNumber: string;           // BN-…
  jobOrderNumber: string | null;   // JO-…
  serviceDate: string;             // YYYY-MM-DD
  dispatchTime: string | null;     // HH:MM
  status: string;
}[] }
```

The items are `DispatchAssignment` rows for that `vehicleId` in `PENDING` or `CONFIRMED`, from today (Asia/Manila), ordered by date and time. They hold no client name, address or rate. Subcon rows have no `vehicleId`, so they never appear. VRMS waits 3 s at most.

### Route 10: repair update (VRMS sends, BMS receives)

```ts
{
  eventId: string;
  eventVersion: number;            // per ticket; keep the highest, ignore lower
  vmmsVehicleId: string; vehiclePlate: string;
  repairTicketId: string; repairTicketNumber: string;
  repairStatus: string; repairStatusLabel: string;  // VRMS's own status (all nine, not route 2's mapping) and its label, "On hold"
  reason: string;                  // issue categories, "Brakes, Electrical", or "Not yet diagnosed"
  expectedReturnAt: string | null; // null when unknown and once closed or cancelled
  changeReason: string;            // "Repair opened", "Status changed to On hold", "Expedite JO-…", "Issues added from VMMS WO-…",
                                   // "Repair finished", "Repair cancelled", "Resent after a failed delivery"
  occurredAt: string;
}
```

It's sent on open, every status change, every expected date change, a referral that adds issues, close and cancel. When a VRMS Admin dismisses a failed update, VRMS sends a fresh one with the ticket's current state. It holds no costs, notes or people.

### Route 11: expedite request (BMS sends, VRMS serves)

Header `Idempotency-Key: <requestId>`.

`{ requestId, vmmsVehicleId, jobOrderNumber /* 1 to 40 */, reason /* 5 to 1000, trimmed */, neededBy? /* YYYY-MM-DD, a real date */ }`

| VRMS answers | When |
|---|---|
| 202 `{ requestId, status: 'WAITING', repairTicketNumber, duplicate: false }` | stored on the truck's open ticket |
| 202 `{ …, duplicate: true }` | the same request again; `status` is where it stands now (`WAITING`, `ACCEPTED` or `DECLINED`) |
| 404 `NO_OPEN_REPAIR` | no open repair; don't retry |
| 409 `REQUEST_ID_REUSED` | the same id with a different body |
| 400 `IDEMPOTENCY_KEY_MISMATCH` | `Idempotency-Key` not equal to `requestId` |
| 400 | a bad id, length or date |

### Route 12: expedite answer (VRMS sends, BMS receives)

```ts
{
  eventId: string; requestId: string; repairTicketNumber: string;
  decision: 'ACCEPTED' | 'DECLINED';
  reason: string | null;           // why declined, or "Repair finished" / "Repair cancelled"
  priority: string | null;         // new priority when accepted
  expectedReturnAt: string | null; // new date when accepted with one
  occurredAt: string;
}
```

An accepted answer with a new date is followed by a route 10 update with that date.

### Route 13: active repair (VRMS serves)

`{ repair: null }` when there's no open repair (or VRMS doesn't know the truck), otherwise:

```ts
{ repair: {
  repairTicketId: string; repairTicketNumber: string;
  repairStatus: string; repairStatusLabel: string;
  reason: string;
  issuesResolved: number; issuesTotal: number;
  expectedReturnAt: string | null;
  openedAt: string;
} }
```
