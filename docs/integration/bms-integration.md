# BMS integration (BMS with VMMS and VRMS)

How BMS works with the trucks system and the repair system: VMMS owns the trucks and plans maintenance, VRMS runs repairs, and BMS plans bookings and Job Orders around both. Three flows: **A**, the fleet list and truck availability (VMMS > BMS); **B**, maintenance dates that avoid booked trips (VMMS <> BMS); and **C**, repair dates and Job Orders (BMS <> VRMS). Your checklist is first. The exact routes and payloads are in the [reference](#reference) below. Flow C is the BMS side of [repair-integration.md](repair-integration.md) flow 3: the two must match, and that file has its payloads.

## BMS checklist

Flow A's reads already work (see [fleet-api.md](fleet-api.md)). Everything else below is new.

**Flow A, fleet and availability:**

- [ ] **Route your gateway:** add `/bms/integrations/vmms/*` and `/bms/integrations/vrms/*` to `bms-gateway/src/routes.ts`.
- [ ] **Receive truck status changes** ([route A2](#route-a2-truck-status-vmms-sends-bms-receives)). VMMS's sender is built and queues one event per status change, but none can be delivered yet: welinc-auth doesn't grant `vmms` the scopes ([auth grants](#auth-grants)), and BMS has no receiver (its gateway routes only the `welinc` and `wix` integrations).
- [ ] **Receive fleet changes** ([route A3](#route-a3-fleet-change-vmms-sends-bms-receives)) and read the record fresh (route A1), like VRMS does.
- [ ] **Flag affected work:** when a truck turns unavailable or is deactivated, flag its upcoming bookings and Job Orders "Needs update" and notify Operations and Customer Support.
- [ ] **Update the availability page right away**, with no refresh.
- [ ] **Filter by garage and truck type**, next to the status filter. For example: "Available trucks in the Valenzuela garage".
- [ ] **Show "Managed in VMMS"** on the truck page instead of edit buttons.
- [ ] **Keep the last fleet list** and show it with "VMMS offline, last updated Nov 21, 9:40 AM" when VMMS can't be reached. Assigning still reads fresh and refuses ([open question 1](#open-questions)).

**Flow B, maintenance:**

- [ ] **Serve the truck's upcoming schedule** to VMMS ([route B1](#route-b1-upcoming-schedule-bms-serves)): the same answer as repair route 9.
- [ ] **Serve the date check** ([route B2](#route-b2-date-check-bms-serves)): conflicts plus the nearest free days.
- [ ] **Receive maintenance events** ([route B3](#route-b3-maintenance-event-vmms-sends-bms-receives)): block the truck on those dates and show "Maintenance scheduled (VMMS WO-…)" on the calendar. Flag clashing work when VMMS confirmed anyway.
- [ ] **Refuse assignment on a blocked date**, naming the WO, so the dispatcher picks another truck.

**Flow C, repairs:** the BMS checklist in [repair-integration.md](repair-integration.md#bms-checklist).

- [ ] **Test flows A, B and C** with VMMS and VRMS once both sides are in ([When you can test](#when-you-can-test)).

## VMMS checklist

Flow A's senders and fleet reads are already built. Flow B is new.

- [ ] **Flow A:** nothing new. Keep sending routes A2 and A3. Your fixes toward BMS are in [repair-integration.md](repair-integration.md#vmms-checklist) (stop retrying a 400 forever, check `client_id === 'bms'` on the fleet routes).
- [ ] **Flow B, read the schedule:** when maintenance comes due, read the truck's upcoming trips (route B1) and check the proposed dates (route B2) before booking it.
- [ ] **Flow B, let staff decide:** move the maintenance to a free day, or confirm it anyway when it can't wait (for example an overdue safety item).
- [ ] **Flow B, tell BMS:** send route B3 when the maintenance is confirmed, moved or cancelled, from your every-minute outbox, with the [retry rule](#the-retry-rule) and a VMMS Admin retry button.

## VRMS checklist

All in [repair-integration.md](repair-integration.md#vrms-checklist-ours-so-you-know-when-to-test), flow 3: routes C1 to C5 below are its routes 9 to 13.

## When you can test

**Flow A** (once BMS has routes A2 and A3 and the `vmms` grants are applied; local stacks with shared, VMMS and BMS up and migrated):
1. In VMMS, set a truck that has a confirmed Job Order tomorrow to Under Maintenance.
2. Within a minute, BMS's availability page shows it Under Maintenance without a refresh, the Job Order shows "Needs update", and Operations gets a notification.
3. Add a truck in VMMS. It appears in BMS's list.
4. Stop BMS, change a truck's status, and start BMS again. The event arrives within a minute (VMMS retries).

**Flow B:** in VMMS, plan maintenance on a day the truck has a Job Order. The check names the JO and suggests free days. Confirm it anyway: BMS blocks the date, flags the JO, and refuses a new assignment on that day with the WO number.

**Flow C:** as in [repair-integration.md](repair-integration.md#when-you-can-test).

---

# Reference

## Who owns what

| System | Owns | Never does |
|---|---|---|
| VMMS | trucks, garages, truck status, maintenance plans and dates | stores bookings, clients or Job Orders |
| VRMS | repair tickets, issues, parts, costs, expected return dates | writes truck status |
| BMS | bookings, dispatch, Job Orders, crew | edits trucks or truck status, books maintenance, sees repair costs and notes |

BMS shares only schedule details with the others: booking and JO numbers, dates, times and status. Client names, addresses and rates stay in BMS.

## How every call works

The same as [repair-integration.md](repair-integration.md#how-every-call-works):

- **Tokens:** a service token from `POST /auth/token` (`client_credentials`, the target system as `audience`, the scope). The copied `service-token-client.ts` does it.
- **Gateway:** call through the suite gateway's internal address, `SUITE_GATEWAY_INTERNAL_URL`. The one exception is route A1, which BMS already calls on the internal network at `VMMS_INTERNAL_URL` ([fleet-api.md](fleet-api.md)).
- **Receivers check:** `aud` is their own system, the scope, and the caller's `client_id` (403 `FORBIDDEN` otherwise). Every answer carries `Cache-Control: no-store`.
- **Duplicates:** every message has an id (`eventId`). The same id with the same body answers success again with `duplicate: true`. The same id with a different body answers 409.
- **Full state:** events carry the full current state plus an `eventVersion` (per truck for A2, per work order for B3). Keep the highest, ignore lower ones. Times are UTC ISO 8601 ending in `Z`; plain dates are `YYYY-MM-DD` in Asia/Manila.

### The retry rule

| Answer | Sender does |
|---|---|
| any 2xx | done |
| 401, 403, 408, 429, 5xx, network error, timeout (5 s) | retry after 30 s, doubling up to 1 hour |
| any other 4xx | failed at once; keep the code and show it to an Admin |
| still failing 24 hours after the first try | failed |

A failed message gets a Retry button for the sender's Admin (VMMS for A and B, VRMS or BMS for C), and Retry restarts the 24 hours. Messages for one truck (A2) or one work order (B3) go in order: a later one waits while an earlier one is failed.

**Today's VMMS senders (A2, A3) differ:** they retry every failure, 400s included, starting at 30 s and doubling up to 1 hour, with no 24-hour limit and no Admin retry. A2 already keeps one truck's events in order (a later one waits while an earlier one is failing). A3 sends in time order but holds nothing back, so a later fleet change can arrive before an earlier one that is still retrying. That is harmless for BMS, which reads the record fresh on every A3. [repair-integration.md](repair-integration.md#vmms-checklist) asks VMMS to stop retrying a 400.

### Auth grants

| Client | Audience | Scopes | For | Granted in welinc-auth today |
|---|---|---|---|---|
| `bms` | `VMMS` | `fleet.read` | route A1 | yes |
| `vmms` | `BMS` | `fleet.availability.write`, `fleet.change.write` | routes A2, A3 | yes (since 2026-11-27, VRMS spec 0029) |
| `vmms` | `BMS` | `schedule.read`, `maintenance.write` | routes B1, B2, B3 | no, and new |
| `vrms` | `BMS` | `schedule.read`, `repair.update.write` | routes C1, C2, C4 | yes (since 2026-11-27) |
| `bms` | `VRMS` | `repair.status.read`, `repair.expedite.write` | routes C3, C5 | yes (since 2026-11-27) |

"Today" means `welinc-auth/prisma/seeds/clients.seed.ts`, applied locally and on staging on 2026-11-27. Only Flow B's scopes are still missing; ask the shared services lead to add them once the Flow B shapes are agreed. Until then those calls are refused at the token request.

## Routes

| # | Caller → served by | Route | Scope | Built |
|---|---|---|---|---|
| A1 | BMS → VMMS | `GET /vmms/fleet/vehicles`, `/vehicles/:id`, `/garages` | `fleet.read` | yes, both |
| A2 | VMMS → BMS | `POST /bms/integrations/vmms/vehicle-availability` | `fleet.availability.write` | VMMS sender yes; grant no; BMS no |
| A3 | VMMS → BMS | `POST /bms/integrations/vmms/fleet-changes` | `fleet.change.write` | VMMS sender yes; grant no; BMS no |
| B1 | VMMS → BMS | `GET /bms/integrations/vmms/vehicles/:vmmsVehicleId/schedule` | `schedule.read` | no |
| B2 | VMMS → BMS | `GET /bms/integrations/vmms/vehicles/:vmmsVehicleId/maintenance-check` | `schedule.read` | no |
| B3 | VMMS → BMS | `POST /bms/integrations/vmms/maintenance-events` | `maintenance.write` | no |
| C1 | VRMS → BMS | `GET /bms/integrations/vrms/vehicles/:vmmsVehicleId/schedule` (repair route 9) | `schedule.read` | no |
| C2 | VRMS → BMS | `POST /bms/integrations/vrms/repair-updates` (repair route 10) | `repair.update.write` | no |
| C3 | BMS → VRMS | `POST /vrms/integrations/bms/expedite-requests` (repair route 11) | `repair.expedite.write` | no |
| C4 | VRMS → BMS | `POST /bms/integrations/vrms/expedite-answers` (repair route 12) | `repair.update.write` | no |
| C5 | BMS → VRMS | `GET /vrms/integrations/bms/vehicles/:vmmsVehicleId/active-repair` (repair route 13) | `repair.status.read` | no |

## Flow A: fleet list and availability (VMMS > BMS)

BMS shows VMMS's garages and trucks with their live status, so Admin and Operations see which trucks can be assigned. BMS never edits fleet records.

1. **BMS loads the fleet** (route A1): garages, and each truck's plate, type, capacity, garage and status. Read only; the truck page shows "Managed in VMMS".
2. **BMS adds its own side:** a truck VMMS marks Available that has a Job Order today shows "Assigned" with the JO number. Filters: garage, status, truck type.
3. **VMMS tells BMS when the fleet changes** (routes A2 and A3): status changes, and trucks or garages added, edited, moved or deactivated.
4. **BMS updates and flags:** the page updates right away, and upcoming bookings and Job Orders on a truck that turned unavailable or was deactivated are flagged "Needs update", with Operations and Customer Support notified.
5. **BMS checks again before assigning:** it reads the one truck fresh from VMMS (the list is cached 30 s, this read never is) and refuses anything but Available (409 `VEHICLE_UNAVAILABLE`), even when the list on screen is a few minutes old. This is built.

### Route A1: fleet reads (BMS reads, as built)

See [fleet-api.md](fleet-api.md): `FleetVehicle` with `status` `AVAILABLE`, `UNDER_REPAIR` or `UNDER_MAINTENANCE`.

### Route A2: truck status (VMMS sends, BMS receives)

As VMMS's sender builds it (`bms-availability.service.ts`), one per status change:

```ts
{
  eventId: string;
  eventVersion: number;          // per truck: VMMS vehicles.availabilityVersion; keep the highest, ignore lower
  vmmsVehicleId: string;
  vehiclePlate: string;
  status: 'AVAILABLE' | 'UNDER_REPAIR' | 'UNDER_MAINTENANCE';
  occurredAt: string;
}
```

| BMS answers (proposed) | When |
|---|---|
| 202 `{ eventId, duplicate: false }` | applied, or ignored because a higher version is already in |
| 202 `{ …, duplicate: true }` | the same event again |
| 409 `EVENT_ID_REUSED` | the same id with a different body |
| 400 | a bad id, version or status |

VMMS treats only 200 and 202 as done. BMS never answers 4xx for a truck it doesn't know: it stores the status and reads the truck on the next list.

### Route A3: fleet change (VMMS sends, BMS receives)

```ts
{
  eventId: string;
  entityType: 'VEHICLE' | 'GARAGE';
  entityId: string;              // VMMS vehicles.id or garages.id
  changeType: 'VEHICLE_CREATED' | 'VEHICLE_IMPORTED' | 'VEHICLE_UPDATED' | 'VEHICLE_DELETED' | 'ODOMETER_UPDATED'
            | 'GARAGE_CREATED' | 'GARAGE_UPDATED' | 'GARAGE_DELETED';
  occurredAt: string;
}
```

As VMMS's sender builds it (`bms-fleet-changes.service.ts`); the change types are every value VMMS records today. BMS answers 202 and reads the record fresh (route A1). It never uses the message's fields beyond the ids. `VEHICLE_DELETED` is VMMS's soft delete (`deletedAt` set, `isActive` false), its only way to deactivate a truck: it flags that truck's upcoming work "Needs update". A move to another garage arrives as `VEHICLE_UPDATED`. `ODOMETER_UPDATED` needs nothing in BMS.

## Flow B: maintenance dates (VMMS <> BMS)

Before VMMS books preventive maintenance, it checks the truck's trips in BMS, so maintenance lands on days the truck isn't needed.

1. **VMMS plans maintenance:** it comes due by date or distance. VMMS proposes a start date and length, for example "Nov 26, 1 day".
2. **VMMS reads the truck's upcoming schedule** (route B1).
3. **VMMS checks the proposed dates** (route B2). Nothing is booked or blocked yet.
4. **VMMS moves the maintenance to a free day, or confirms it anyway** when it can't wait.
5. **VMMS tells BMS** (route B3). BMS blocks the truck on those dates, shows "Maintenance scheduled (VMMS WO-…)", and if VMMS confirmed despite a conflict, flags the clashing work and notifies Operations and Customer Support.
6. **BMS refuses assignment on a blocked date**, naming the WO.
7. **VMMS moves or cancels the maintenance** (route B3 again). BMS moves or removes the block and checks its bookings again. When the maintenance starts, the truck turns Under Maintenance through route A2.

### Route B1: upcoming schedule (BMS serves)

`GET …/schedule?days=14` (1 to 31). The same answer as [repair route 9](repair-integration.md#route-9-upcoming-trips-bms-serves):

```ts
{ items: {
  bookingNumber: string;           // BN-…
  jobOrderNumber: string | null;   // JO-…
  serviceDate: string;             // YYYY-MM-DD
  dispatchTime: string | null;     // HH:MM
  status: string;
}[] }
```

`DispatchAssignment` rows for that `vehicleId` in `PENDING` or `CONFIRMED`, from today (Asia/Manila), ordered by date and time. No client name, address or rate. Subcon rows have no `vehicleId`, so they never appear.

### Route B2: date check (BMS serves)

`GET …/maintenance-check?start=YYYY-MM-DD&days=1` (`days` 1 to 14):

```ts
{
  conflict: boolean;
  conflicts: { bookingNumber: string; jobOrderNumber: string | null; serviceDate: string; dispatchTime: string | null; status: string }[];
  nearestFreeStarts: string[];     // up to 3 start dates (YYYY-MM-DD) within 30 days with no trip for `days` days; empty if none
}
```

Read only: nothing is held. A date already blocked by another work order counts as a conflict and is listed with `jobOrderNumber: null` and `status: 'MAINTENANCE WO-…'`.

### Route B3: maintenance event (VMMS sends, BMS receives)

```ts
{
  eventId: string;
  eventVersion: number;              // per work order; keep the highest, ignore lower
  eventType: 'CONFIRMED' | 'MOVED' | 'CANCELLED';
  vmmsVehicleId: string;
  vehiclePlate: string;
  maintenanceScheduleId: string;
  workOrderNumber: string;           // WO-…
  startDate: string;                 // YYYY-MM-DD, first blocked day
  endDate: string;                   // YYYY-MM-DD, last blocked day, inclusive
  confirmedDespiteConflict: boolean; // VMMS staff confirmed after a B2 conflict
  occurredAt: string;
}
```

| BMS answers | When |
|---|---|
| 202 `{ eventId, duplicate: false }` | stored: block set, moved or removed |
| 202 `{ …, duplicate: true }` | the same event again |
| 409 `EVENT_ID_REUSED` | the same id with a different body |
| 400 | bad dates (`endDate` before `startDate`, more than 14 days) or ids |

## Flow C: repairs and Job Orders (BMS <> VRMS)

The BMS side of [repair-integration.md](repair-integration.md) flow 3. Routes C1 to C5 are its routes 9 to 13, with their payloads there.

1. **VRMS reads the truck's upcoming trips** (C1) when a ticket opens, to set its priority.
2. **VRMS tells BMS when the truck should be back** (C2): ticket number, reason, status, expected return date.
3. **BMS flags affected work:** fills in the truck's repair reason and expected date (`VehicleDispatchProfile.statusReason`, `expectedBackAt`, `statusRemarks`), flags bookings and Job Orders before that date "Affected by repair REP-…", and notifies Operations and Customer Support. Operations reassigns an Available truck (Flow A step 5) or reschedules; the flag clears once handled.
4. **BMS asks for a faster repair** (C3): one request per Job Order, with a reason, under the retry rule with a BMS Admin retry button.
5. **VRMS answers** (C4): accepted (new priority, maybe a new date) or declined with a reason.
6. **The expected date changes** (C2 again): BMS flags newly affected work and clears work that is now safe.
7. **BMS follows the repair** (C5) on booking and truck pages: status, issues done of total, expected return.
8. **The repair ends:** VMMS sets the truck's status and tells BMS through route A2. Once it's Available, BMS clears any flags left.

## One flag for affected work

Flows A, B and C all flag bookings and Job Orders. BMS keeps one flag per booking with its cause, so Operations has one list to work through:

| Cause | Label | Clears when |
|---|---|---|
| Truck unavailable or deactivated (A) | "Needs update" | reassigned, rescheduled, or the truck is Available again |
| Maintenance confirmed on that date (B) | "Clashes with maintenance WO-…" | reassigned, rescheduled, or the maintenance moves or is cancelled |
| Repair expected after that date (C) | "Affected by repair REP-…" | reassigned, rescheduled, or the expected date moves before it |

## Open questions

1. **The offline list.** Flow A asks BMS to show the last list with "VMMS offline, last updated …" when VMMS is down. [fleet-api.md](fleet-api.md#bms-rules) says today that the list answers 503 `FLEET_UNAVAILABLE` and no stale list is served. Proposal: the list may show the last copy with the banner, and assignment keeps reading fresh and refusing (503), so nothing is dispatched on a stale status. fleet-api.md would change with it.
2. **New scopes for Flow B.** `schedule.read` and `maintenance.write` for client `vmms` on audience `BMS` need the welinc-auth owners and the VMMS group to agree.
3. **Flow B route shapes** are a BMS proposal for VMMS to review before either side builds them.
