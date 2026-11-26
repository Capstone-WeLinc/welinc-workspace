# Repair integration (VRMS with VMMS and BMS)

How repairs cross between the three systems: VMMS refers a truck for repair, VRMS runs the repair and reports every change, and BMS plans its bookings around it. The full design is VRMS spec [0029](../specs/vrms/0029-cross-group-integration/index.md). This page is what you build to. VMMS's side is in specs vmms/0023 to vmms/0026.

**Who owns what**

| System | Owns | Never does |
|---|---|---|
| VMMS | trucks, garages, outside shops, truck status | stores repair data beyond ticket ids, numbers, status and shop |
| VRMS | repair tickets, issues, parts, costs | writes truck status or edits trucks (it keeps a read only copy) |
| BMS | bookings, dispatch, Job Orders | writes truck status, or sees repair costs and notes |

**Status today (2026-11-26):** VMMS's half of flows 1 and 2 is built. VRMS's routes and the auth grants come with the first build milestone of spec 0029, and testing flow 1 can start then. BMS has built nothing for flow 3 yet: everything under *Flow 3* below is for BMS to build.

## How every call works

- **Service tokens:** `POST /auth/token` with `grant_type=client_credentials`, the target system as `audience`, the scope, and your client assertion. The copied `src/auth/verify/service-token-client.ts` does it and caches the token.
- **Through the gateway:** call the suite gateway's internal address (`SUITE_GATEWAY_INTERNAL_URL`), for example `{gateway}/vrms/integrations/vmms/repair-referrals`.
- **Receivers check three things:** `aud` is their own system, the scope, and `client_id` is the expected caller (403 `FORBIDDEN` otherwise). Every integration answer carries `Cache-Control: no-store`.
- **Every message has an id:** `eventId` (or `referralId`, `requestId`). The same id with the same body answers success again with `duplicate: true`. The same id with a different body answers 409.
- **Events carry the full current state**, never a difference, plus an `eventVersion` per repair ticket. Times are UTC ISO 8601 ending in `Z`.

### The retry rule (every sender, every system)

| Answer | What the sender does |
|---|---|
| any 2xx | done |
| 401, 403, 408, 429, 5xx, network error, timeout (5 s) | retry after 30 s, then doubling each time up to 1 hour |
| any other 4xx | failed at once: keep the status and error code, show it to a person |
| still failing 24 hours after the first try | failed |

A failed message is shown to an Admin with a Retry button. Retry restarts the 24 hours. VRMS shows them on the Deliveries tab of its Audit Logs page. Messages about one repair ticket are sent in order, so a later one waits while an earlier one is failed.

### Auth grants (in welinc-auth, set by the lead)

| Client | Audience | Scopes |
|---|---|---|
| `vrms` | `VMMS` | `fleet.read`, `fleet.repair-status.write`, `repair.referral-status.write` |
| `vrms` | `BMS` | `schedule.read`, `repair.update.write` |
| `vmms` | `VRMS` | `repair.referral.write`, `repair.status.read`, `repair.history.read`, `fleet.change.write` |
| `vmms` | `BMS` | `fleet.availability.write`, `fleet.change.write` |
| `bms` | `VRMS` | `repair.status.read`, `repair.expedite.write` |

## The routes at a glance

| # | Caller → served by | Route | Scope | Built |
|---|---|---|---|---|
| 1 | VMMS → VRMS | `POST /vrms/integrations/vmms/repair-referrals` | `repair.referral.write` | VMMS sender yes, VRMS no |
| 2 | VRMS → VMMS | `POST /vmms/integrations/vrms/repair-events` | `fleet.repair-status.write` | VMMS yes, VRMS sender no |
| 3 | VRMS → VMMS | `POST /vmms/integrations/vrms/referral-events` | `repair.referral-status.write` | VMMS yes, VRMS sender no |
| 4 | VMMS → VRMS | `GET /vrms/integrations/vmms/repairs/:repairTicketId` | `repair.status.read` | VMMS client yes, VRMS no |
| 5 | VMMS → VRMS | `GET /vrms/integrations/vmms/vehicles/:vmmsVehicleId/repair-history` | `repair.history.read` | VMMS client yes, VRMS no |
| 6 | VMMS → VRMS | `POST /vrms/integrations/vmms/fleet-changes` | `fleet.change.write` | no (VMMS ask 4) |
| 7 | VRMS → VMMS | `GET /vmms/fleet/vehicles`, `/vehicles/:id`, `/garages` | `fleet.read` | VMMS yes |
| 8 | VRMS → VMMS | `GET /vmms/fleet/outsourced-providers` | `fleet.read` | no (VMMS ask 6) |
| 9 | VRMS → BMS | `GET /bms/integrations/vrms/vehicles/:vmmsVehicleId/schedule` | `schedule.read` | no (BMS) |
| 10 | VRMS → BMS | `POST /bms/integrations/vrms/repair-updates` | `repair.update.write` | no (BMS) |
| 11 | BMS → VRMS | `POST /vrms/integrations/bms/expedite-requests` | `repair.expedite.write` | no |
| 12 | VRMS → BMS | `POST /bms/integrations/vrms/expedite-answers` | `repair.update.write` | no (BMS) |
| 13 | BMS → VRMS | `GET /vrms/integrations/bms/vehicles/:vmmsVehicleId/active-repair` | `repair.status.read` | no |

## Flows 1 and 2: VMMS ↔ VRMS

**The story.** A VMMS Chief Mechanic ends an inspection "For Repair" in the mobile app. VMMS sends VRMS a referral (route 1). It shows on the Referrals tab of VRMS's Repairs page, and a VRMS Admin does one of three things:
- **Opens a ticket from it:** VRMS sends `OPENED` with the referral id (route 2).
- **Adds it to the truck's open ticket:** VRMS sends `LINKS_UPDATED`, or `STATUS_UPDATED` when the schedule is already linked.
- **Rejects it with a reason:** VRMS sends `REJECTED` (route 3), and VMMS returns the job to its mechanic.

From then on, every ticket change reaches VMMS (route 2). VMMS sets the truck's status and tells BMS. When the ticket closes, VMMS gets `COMPLETED` and runs its final check.

### Route 1: referral (VMMS sends, as built)

Header `Idempotency-Key: <referralId>`. Body:

```ts
{
  referralId: string;            // uuid, VMMS's id; the duplicate key
  vmmsVehicleId: string;         // uuid
  vehiclePlate: string;
  maintenanceScheduleId: string; // uuid
  workOrderNumber: string;       // WO-…
  odometerReading: number;
  findings: { checklistItemId: string; label: string; note: string | null }[]; // the failed items, 1 to 100
  chiefMechanicRemarks: string | null;
}
```

| VRMS answers | When |
|---|---|
| 202 `{ referralId, status: 'WAITING', duplicate: false }` | stored |
| 202 `{ referralId, status, duplicate: true }` | the same referral again |
| 409 `REFERRAL_ID_REUSED` | the same id with a different body |
| 422 `VEHICLE_NOT_FOUND` | VMMS itself doesn't have the truck (VRMS reads it fresh first) |
| 400 | a bad id, odometer or findings count, or `Idempotency-Key` not equal to `referralId` |

VRMS trims long text and doesn't refuse it, so a long note never loses a referral.

### Route 2: repair events (VRMS sends, VMMS built the receiver)

```ts
{
  eventId: string;                 // uuid
  repairTicketId: string;          // uuid, never changes for a ticket
  repairTicketNumber: string;      // REP-YYYYMMDD-XXXX
  eventVersion: number;            // 1, 2, 3 … per ticket, no gaps
  eventType: 'OPENED' | 'LINKS_UPDATED' | 'STATUS_UPDATED' | 'COMPLETED' | 'CANCELLED';
  repairStatus: 'OPEN' | 'ASSIGNED' | 'IN_PROGRESS' | 'ON_HOLD' | 'OUTSOURCED' | 'FOR_VERIFICATION' | 'CLOSED' | 'CANCELLED';
  vmmsVehicleId: string;
  maintenanceScheduleIds: string[]; // every schedule linked so far, only grows
  acceptedReferralIds: string[];    // every referral accepted so far, only grows
  outsideShopName?: string;         // only with OUTSOURCED, an active VMMS outside shop
  occurredAt: string;
}
```

| VRMS ticket event | `eventType` | `repairStatus` |
|---|---|---|
| ticket created | `OPENED` | `OPEN` (a ticket created as Assigned sends `STATUS_UPDATED` `ASSIGNED` right after) |
| referral added, new schedule | `LINKS_UPDATED` | current |
| referral added, schedule already linked | `STATUS_UPDATED` | current |
| any move to an open status | `STATUS_UPDATED` | the new status |
| VRMS's Pending approval | `STATUS_UPDATED` | `OUTSOURCED`, with the same shop |
| verified and closed | `COMPLETED` | `CLOSED` |
| cancelled | `CANCELLED` | `CANCELLED` |

Every VRMS ticket is sent, not only referral tickets: VMMS sets every truck's status from them. A ticket a person opened has empty id lists. Outsourcing a ticket in VRMS requires picking a shop from VMMS's list (route 8), so `outsideShopName` always matches.

### Route 3: referral rejected (VRMS sends, VMMS built the receiver)

`{ eventId, referralId, eventType: 'REJECTED', reason, occurredAt }`. The reason is 5 to 500 characters.

### Routes 4 and 5: reads VMMS makes (VMMS built the clients)

- **Route 4** answers `{ repairTicketId, repairTicketNumber, status, outsideShopName }`, with the status as in route 2 and the shop only when outsourced. An unknown id answers 404 `REPAIR_NOT_FOUND`.
- **Route 5**, `?limit=1..100` (default 50) `&cursor=<opaque>`, answers `{ items, nextCursor }`, newest first. It lists closed tickets and the open one, never cancelled ones. Each item:

```ts
{
  repairTicketId: string; repairTicketNumber: string;
  openedAt: string; closedAt: string | null; status: string;
  issues: string[];          // "Brakes: grinding front left"
  partsUsed: string[];       // "Brake pad set x2", never a price
  repairPersonnel: string[]; // mechanic names
  provider: string | null;   // the outside shop
  totalRepairCost: string | null; // the ticket total, decimal string
}
```

A truck VRMS never repaired answers 200 with no items.

### Routes 6 to 8: VRMS's copy of the fleet

VRMS keeps a read only copy of VMMS's trucks and garages:
- **On change:** VMMS sends route 6 on every truck or garage change, with the same body it sends BMS (`{ eventId, entityType, entityId, changeType, occurredAt }`). VRMS answers 202 and reads that record fresh (route 7). It never trusts the message's fields.
- **Hourly:** VRMS reads the full lists (route 7) to fix anything a lost message missed.
- **Outside shops:** VRMS reads them from route 8 when an Admin outsources a ticket.

## Flow 3: VRMS ↔ BMS (BMS Flow C; BMS builds its side)

**The story.** While a truck is in repair, VRMS sends BMS an update on every ticket change (route 10): why the truck is in repair, the status, and when it's expected back. BMS fills the truck's `VehicleDispatchProfile` (`statusReason`, `expectedBackAt`, `statusRemarks`) and flags the bookings before that date. BMS pages can read the current repair at any time (route 13). Operations can ask VRMS to hurry for a Job Order (route 11). A VRMS Admin accepts, which raises the priority and can set a new date, or declines with a reason, and the answer comes back on route 12. VRMS shows the truck's upcoming trips on the new ticket form and the ticket (route 9). The truck's availability still comes from VMMS only (flow 2).

### Route 9: upcoming trips (BMS serves)

`GET /bms/integrations/vrms/vehicles/:vmmsVehicleId/schedule?days=14` (1 to 31) answers:

```ts
{ items: {
  bookingNumber: string;            // BN-…
  jobOrderNumber: string | null;    // JO-…
  serviceDate: string;              // YYYY-MM-DD
  dispatchTime: string | null;      // HH:MM
  status: string;
}[] }
```

The items are `DispatchAssignment` rows for that `vehicleId` in `PENDING` or `CONFIRMED`, from today (Asia/Manila) for `days` days, ordered by date and time. Only schedule facts cross: no client name, address or rate. Subcon assignments have no `vehicleId`, so they never appear. The same route can serve VMMS for BMS Flow B with a grant for `vmms`. VRMS waits 3 s at most and shows "BMS can't be reached" otherwise.

### Route 10: repair update (VRMS sends, BMS receives)

```ts
{
  eventId: string;
  eventVersion: number;             // per ticket; keep the highest, ignore lower
  vmmsVehicleId: string; vehiclePlate: string;
  repairTicketId: string; repairTicketNumber: string;
  repairStatus: string;             // VRMS's own status, any of nine
  repairStatusLabel: string;        // "On hold"
  reason: string;                   // issue categories, "Brakes, Electrical", or "Not yet diagnosed"
  expectedReturnAt: string | null;  // null when unknown, and always null once closed or cancelled
  changeReason: string;             // "Repair opened", "Status changed to On hold", "Expedite JO-…", "Repair finished"
  occurredAt: string;
}
```

It's sent when a repair opens, on every status change, on every expected date change, and when it closes or is cancelled. Answer any 2xx. Never send costs, notes or people to BMS staff screens; this body holds none.

### Route 11: expedite request (BMS sends, VRMS serves)

```ts
{ requestId: string; vmmsVehicleId: string; jobOrderNumber: string; reason: string /* 5 to 1000 */; neededBy?: string /* YYYY-MM-DD */ }
```

| VRMS answers | When |
|---|---|
| 202 `{ requestId, status: 'WAITING', repairTicketNumber }` | stored against the truck's open ticket |
| 202 with `duplicate: true` | the same request again |
| 404 `NO_OPEN_REPAIR` | the truck has no open repair; don't retry |
| 409 `REQUEST_ID_REUSED` | the same id with a different body |

Send one request per affected Job Order. VRMS lists each separately.

### Route 12: expedite answer (VRMS sends, BMS receives)

```ts
{
  eventId: string; requestId: string; repairTicketNumber: string;
  decision: 'ACCEPTED' | 'DECLINED';
  reason: string | null;            // why declined; "Repair finished" or "Repair cancelled" when the ticket ended first
  priority: string | null;          // the new priority when accepted
  expectedReturnAt: string | null;  // the new date when accepted with one
  occurredAt: string;
}
```

An accepted answer with a new date is followed by a route 10 update with the same date.

### Route 13: active repair (VRMS serves)

It answers `{ repair: null }` when the truck has no open repair, otherwise:

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

## Asks

### VMMS

What you built works as is: VRMS sends versions with no gaps and a shop name with every outsourced ticket. These make it sturdier.

1. **Accept any `eventVersion` above the last one**, not only +1, and ignore lower ones. A safety net; VRMS never skips.
2. **Send referrals only from your every minute job**, not inside the Chief Mechanic's request. Today the tap waits up to 5 s on VRMS (`maintenance-schedules.service.ts` awaits `deliverOne`).
3. **Retry 401 and 403 within the 24 hours**, like 5xx. On a new setup they mean a grant or key still being fixed.
4. **Send `fleet-changes` to VRMS too** (route 6), with audience `VRMS` and the same body you send BMS.
5. **Let `LINKS_UPDATED` add only referrals**, without a new schedule. Until then VRMS sends `STATUS_UPDATED` for that case.
6. **Serve the outside shop list to services**: `GET /vmms/fleet/outsourced-providers` behind `fleet.read`, answering `{ providers: { id, name }[] }`, active only, ordered by name.
7. **Refuse to deactivate a truck with an open VRMS repair**, and name the ticket. Otherwise every later event for it answers 404.
8. **Check a maintenance schedule's state only when it is first linked**, not on every event. Today, if a work order changes after its referral, every later event for that ticket answers 409 until an Admin dismisses one.

Noted, between VMMS and BMS:
- Your BMS availability sender retries a 400 forever, which blocks that truck's later events.
- Your fleet routes don't check `client_id`.
- The mobile "For Repair" suggestion should allow any failed item, not only more failed than passed.

**Later (flows 4 to 7, spec 0029 child 0005):**
- odometer readings on `OPENED` and `COMPLETED`
- a retirement request and decision for a truck beyond repair
- a repeat repair alert into your repeated failures list
- "Refer for repair" from a fuel anomaly
- a register request for a truck VMMS doesn't have yet

### BMS

1. **Serve route 9** behind `schedule.read` for client `vrms`.
2. **Receive route 10:** write `VehicleDispatchProfile` and flag the bookings before `expectedReturnAt`, with "Affected by repair REP-…", for Operations and Customer Support.
3. **Send route 11 and receive route 12**, with the retry rule and a BMS Admin retry button.
4. **Show route 13** on your booking and truck pages.
5. **Add `/bms/integrations/vrms/*`** to your gateway service (`bms-gateway/src/routes.ts`).
6. **Receive VMMS's availability and fleet change events** (spec vmms/0026; their grants come with this change).

## Proving it

On local stacks (shared, VRMS and VMMS up, both migrated):
1. As a VMMS Chief Mechanic in the mobile app, mark an inspection with a failed item "For Repair".
2. As `vrms.admin@`, open Repairs, then Referrals, then "Open a ticket", and save. The VMMS work order shows the ticket number, and the truck shows Under Repair in VMMS and in BMS's fleet list.
3. Close the ticket in VRMS. VMMS starts its final check, and once that passes the truck is Available again.
4. Stop VMMS, change a ticket's status, and start VMMS again. The event arrives within a minute, and VRMS's Deliveries tab shows the retries.
