# 0029. Cross group integration: repair handoff with VMMS, repair impact with BMS

**Date**: 2026-11-26
**Status**: Proposed

## Summary

VRMS starts talking to the other two systems. VMMS sends VRMS a referral when maintenance finds a defect, VRMS turns it into a repair ticket, and every ticket change goes back to VMMS so it can set the truck's status. BMS sees how long a truck will be in repair, can ask VRMS to hurry, and VRMS shows the truck's upcoming trips on the ticket. VRMS stops owning trucks: it keeps a read only copy of VMMS's trucks and garages. Every message that leaves VRMS is written to a table in the same database save as the change it reports (an outbox), so nothing is lost when another system is down, and a background job keeps retrying it for 24 hours.

Rationale: reasoning and options are in [rationale.md](rationale.md).

## Structure

| Child | What it is | Decision it supports |
|---|---|---|
| [0001-fleet-copy.md](0001-fleet-copy.md) | VRMS's trucks and garages become a copy of VMMS's, kept current by change messages plus an hourly full read; a one time script links the old rows or archives them | VMMS owns trucks and garages |
| [0002-vmms-repair-handoff.md](0002-vmms-repair-handoff.md) | Flows 1 and 2: referrals in, repair events out, the status and history reads VMMS calls | VRMS owns repairs; VMMS alone writes truck status |
| [0003-bms-repair-impact.md](0003-bms-repair-impact.md) | Flow 3 (BMS Flow C): upcoming trips read, repair updates with the expected return date, expedite requests and answers, the active repair read | BMS plans around repairs without owning them |
| [0004-deliveries.md](0004-deliveries.md) | The plumbing: the `Delivery` outbox, the worker and its retry rule, inbound duplicate handling, the Deliveries tab | Every message is retried, never lost, and visible |
| [0005-next-slice.md](0005-next-slice.md) | Slice 2: flows 4 to 7 (retire a truck, repeat repair alert, fuel anomaly referral, odometer readings) and the register request for a truck VMMS doesn't have | Spec all seven flows, build 1 to 3 first |

Flows 1 to 3 are slice 1 and the main thread of the integration defense. VMMS was asked for flows 4 to 7 at the same time (2026-11-26), so its side is built in parallel, and VRMS builds slice 2 right after slice 1. The register request is asked later. Feature 42 (due dates) gets its own spec next, bound by the due date rule in child 0003.

## Requirements

**User stories**:
- As a VRMS Admin, I want VMMS's repair referrals in a list beside my tickets, so I can open a ticket from one, add it to the truck's open ticket, or send it back with a reason.
- As a VMMS Chief Mechanic, I want to know what VRMS did with my referral and see the truck's past repairs, so I can follow up without phoning the garage.
- As VMMS, I want to hear about every repair start, change and end, so I set the truck's status and BMS learns it from one owner.
- As a BMS Operations or Customer Support person, I want to know when a truck in repair is expected back and why, and ask for it sooner, so I can protect bookings.
- As a VRMS Admin, I want to see a truck's upcoming trips while I set a ticket's priority, and answer an expedite request with a new priority and date.
- As the VRMS team, we want every message that failed to be visible with a retry button, so an outage never silently loses a handoff.

**Acceptance criteria** (slice 1, including AC-35 and AC-36, which the cross check added; slice 2's are AC-28 to AC-34 in [0005](0005-next-slice.md)):

*Fleet copy ([0001](0001-fleet-copy.md))*
- **AC-1**: `Vehicle.vmmsVehicleId` and `Garage.vmmsGarageId` exist and are unique. A one time script, `npm run fleet:link`, links VRMS trucks to VMMS by plate and garages by name (both trimmed, case insensitive). Without `--confirm` it only prints the plan. If two VRMS rows would claim one VMMS id, it lists them and stops. With `--confirm`, it archives every unmatched truck and garage (`isActive` false, VMMS id left null), which hides them from every picker. Their tickets and history stay. Nothing is deleted. It is run once locally and once on staging, before the sync is switched on.
- **AC-2**: `POST /vrms/integrations/vmms/fleet-changes` answers 202 and then reads that truck or garage fresh from the VMMS fleet API. The copy changes within one minute. A 404 from VMMS sets the local row `isActive` false and never deletes it.
- **AC-3**: Every `fleet.reconcileMinutes` (setting, default 60), VRMS reads VMMS's full garage and truck lists, upserts them by VMMS id, and sets rows VMMS no longer lists to `isActive` false. It never deactivates anything when a list comes back empty or would deactivate more than 20% of the active rows; it reports that instead. A change to plate, model, make, capacity, size, status, garage or active writes one `VehicleChange` row per field with actor VMMS. Odometer is copied but not logged. A plate or garage name that clashes with another local row is skipped and reported, and the other fields still apply.
- **AC-4**: Only the sync writes a truck's plate, model, make, capacity, size, type, status, garage, odometer and active flag. The Admin status toggle (`POST /vrms/vehicles/:id/status`) and type edit (`PATCH /vrms/vehicles/:id`) are removed. Settings, Vehicles is read only and says "Managed in VMMS". Its history dialog still opens. `DISABLED` no longer exists. Ticket create and release no longer touch `Vehicle.status`.
- **AC-5**: The new ticket form lists only active, linked trucks. A search with no match says "Not in VMMS yet. Ask VMMS Operations to add it." Create reads the chosen truck fresh from VMMS. A truck VMMS doesn't have answers 422 `VEHICLE_NOT_IN_VMMS`. If VMMS can't be reached, create uses the copy and the form shows "VMMS can't be reached, using the last copy". A truck under maintenance no longer blocks a new ticket. One open ticket per truck is still enforced (409 `OPEN_TICKET_EXISTS`).
- **AC-35**: When the sync deactivates a truck that has an open ticket, the ticket shows "Truck removed in VMMS" on its detail page and in the list, and the Admin dashboard lists it. The Admin cancels the ticket, or VMMS reactivates the truck, which clears the flag on the next sync. Deliveries VMMS refuses for it stay visible as `FAILED`.

*VMMS repair handoff, flows 1 and 2 ([0002](0002-vmms-repair-handoff.md))*
- **AC-6**: `POST /vrms/integrations/vmms/repair-referrals` stores a valid referral as `WAITING` and answers 202 `{ referralId, status, duplicate: false }`. The same `referralId` with the same body answers 202 with `duplicate: true` and the current status. The same id with a different body answers 409 `REFERRAL_ID_REUSED`. An `Idempotency-Key` header that differs from `referralId` answers 400. A truck VMMS doesn't know, even after a fresh read, answers 422 `VEHICLE_NOT_FOUND`. Over long text is cut to the column's length, not refused, and empty notes and remarks are accepted, because VMMS never retries a 4xx.
- **AC-7**: The Repairs page has a Referrals tab at `/repairs?view=referrals`. It shows a count of waiting referrals and lists them (received, plate, WO number, findings count, status), filtered to Waiting by default. A side panel shows the findings, the Chief Mechanic's remarks, the odometer and the WO number. Holders of `integration.respond` see the tab and an Admin dashboard card, "Referrals waiting (n)", that links to it.
- **AC-8**: For a truck with no open ticket, "Open a ticket" opens the new ticket form at `/repairs/new?referral=<id>`. The form is prefilled with the truck, its garage, the referral's odometer, and one issue line per finding. No driver is needed. The Admin completes the form's required fields and saves. That creates the ticket, links the referral and sets it to `OPENED_TICKET`, all in one transaction. A referral no longer `WAITING` answers 409 `REFERRAL_ALREADY_DECIDED`.
- **AC-9**: For a truck with an open ticket, the action reads "Add to REP-…". It opens a dialog on that ticket with one prefilled issue line per finding. Confirming adds the issues through spec 0019's issue edit rules for the ticket's status, links the referral and sets it to `ADDED_TO_TICKET`, in one transaction.
- **AC-10**: "Reject" needs a reason (5 to 500 characters). It sets the referral to `REJECTED` and queues a `REJECTED` referral event to VMMS in the same transaction.
- **AC-11**: Only holders of the new `integration.respond` permission (Admin by default, in welinc-auth's VRMS catalog) may open, add or reject a referral or answer an expedite request. Anyone else gets 403 and sees no action buttons.
- **AC-12**: A ticket opened from a referral shows "From VMMS WO-…" on its detail page and in the ticket list. Its driver shows "None (from VMMS)".
- **AC-13**: In the same transaction as each change, with the ticket row locked, VRMS queues one repair event to VMMS. That happens on create, on every status move, when a referral is added, on close and on cancel. Each event carries the full set of linked maintenance schedule ids and accepted referral ids, `occurredAt` taken inside that transaction, and the status mapped per child 0002. `PENDING_APPROVAL` is sent as `OUTSOURCED`, and both carry the ticket's outside shop name. The worker assigns `eventVersion` when it sends (one above the last version VMMS accepted), so a dismissed message never leaves a gap. A ticket created as `ASSIGNED` sends `OPENED` with `OPEN`, then `STATUS_UPDATED` with `ASSIGNED`. Adding a referral sends `LINKS_UPDATED` only when it brings a new schedule, and otherwise sends `STATUS_UPDATED` with the new referral id.
- **AC-36**: Moving a ticket to `OUTSOURCED` needs an outside shop picked from VMMS's active provider list, read through `GET /vmms/fleet/outsourced-providers`. VRMS stores the shop's VMMS id and name on the ticket and keeps them through `PENDING_APPROVAL`. When VMMS can't be reached, the picker uses the last list read in the past 24 hours. With none, the move is refused with 503 `VMMS_UNAVAILABLE` and "VMMS can't be reached, try again". An outsourced ticket with no shop (from before this spec) shows "Pick the outside shop", and picking one queues a `STATUS_UPDATED`.
- **AC-14**: `GET /vrms/integrations/vmms/repairs/:repairTicketId` answers `{ repairTicketId, repairTicketNumber, status, outsideShopName }`, with the status and shop as in AC-13. An unknown id answers 404 `REPAIR_NOT_FOUND`.
- **AC-15**: `GET /vrms/integrations/vmms/vehicles/:vmmsVehicleId/repair-history?limit&cursor` returns the truck's closed tickets plus its open one, never cancelled ones, newest first. `limit` is 1 to 100 (default 50) and the cursor is opaque. Each item holds the issue lines, parts as text with quantities and no prices, mechanic names, the provider, and `totalRepairCost`. A truck VRMS has never repaired answers 200 with no items.

*BMS repair impact, flow 3 ([0003](0003-bms-repair-impact.md))*
- **AC-16**: After a truck is picked on the new ticket form, and on the ticket detail page as an "Upcoming trips" card, VRMS shows the truck's upcoming trips and Job Orders. They are read live from BMS and never stored. When BMS can't be reached, the card says "BMS can't be reached" and saving still works.
- **AC-17**: In the same transaction as each change, VRMS queues a repair update to BMS. That happens on create, on every status move, on every `dueAt` change (with its change reason), on close and on cancel. The update carries the ticket number, status, the issue categories as the reason, the expected return date (`dueAt`), and an `eventVersion` per ticket.
- **AC-18**: `POST /vrms/integrations/bms/expedite-requests` stores a request as `WAITING` against the truck's open ticket and answers 202. Several requests per ticket are kept, each with its JO number and reason. A truck with no open ticket answers 404 `NO_OPEN_REPAIR`. A reused `requestId` with a different body answers 409 `REQUEST_ID_REUSED`. The ticket shows a banner listing waiting requests, and the Admin dashboard shows "Expedite requests (n)".
- **AC-19**: Accepting a request opens a dialog. Priority defaults to one step up (capped at Critical), and a new due date is optional. Saving changes the ticket with the reason "Expedite JO-…", writes the audit row, and queues the answer, plus a repair update when the date changed. Declining needs a reason (5 to 500 characters) and queues the answer. Closing or cancelling a ticket declines its waiting requests, with the reason "Repair finished" or "Repair cancelled".
- **AC-20**: `GET /vrms/integrations/bms/vehicles/:vmmsVehicleId/active-repair` answers the open ticket's number, status, reason, issues resolved of total, expected return date and opened time, or `{ repair: null }`. It never includes costs, notes or people.

*Plumbing ([0004](0004-deliveries.md))*
- **AC-21**: A worker sends due `Delivery` rows every 15 seconds and counts any 2xx as sent. It retries 401, 403, 408, 429, 5xx, network errors and timeouts (5 seconds), waiting 30 seconds and doubling each time up to 1 hour, until `integration.retryWindowHours` (setting, default 24) after the first attempt. Then the row is `FAILED`. Any other 4xx fails at once and keeps the other system's status and error code. For one ticket and one target, only the oldest unsent row is ever claimed, so a later row waits while an earlier one is not yet sent or dismissed. Payloads are sent as stored; only `eventVersion` is filled in at send time.
- **AC-22**: The Audit Logs page has a Deliveries tab for `audit.view` holders. It is filterable by status, target and kind, and a side panel shows the payload, each attempt, and the last error. A row still retrying after 3 attempts shows a warning with its last status code. Holders of `integration.respond` can Retry a failed row, which restarts its window, or Dismiss it with a reason. Dismissing a BMS repair update queues a fresh one with the ticket's current state. Both actions are audited.
- **AC-23**: A nightly job deletes `SENT` and `DISMISSED` rows older than `integration.deliveryRetentionDays` (setting, default 90). `PENDING` and `FAILED` rows are never deleted.
- **AC-24**: Every `/vrms/integrations/*` route accepts only a service token with audience `VRMS`, the named scope, and the named `client_id` (403 otherwise). Every one answers `Cache-Control: no-store` and is documented in VRMS's OpenAPI with its error codes (spec 0026).
- **AC-25**: A message from another system that changes a ticket or creates a waiting item (expedite received, auto decline) writes an audit row with actor role `SYSTEM` and actor name `VMMS` or `BMS`.

*Shared setup*
- **AC-26**: welinc-auth's client registry grants exactly the scopes in *Auth grants* below, and its VRMS catalog has `integration.respond`. `npm run seed:clients` and `catalog:sync` apply them locally and on staging.
- **AC-27**: `docs/integration/repair-integration.md` documents every route, payload, scope, status mapping and the retry rule for the VMMS and BMS groups, plus the asks below, in the style of `fleet-api.md`.

## Decision

**Chosen option**: Option 2: Transactional outbox with service token HTTP calls, plus live reads.

Each system keeps its own data. Changes cross as short HTTP messages written to an outbox in the same transaction, and retried by a worker for 24 hours. Facts another system needs at the moment it shows them are read live. VRMS builds to VMMS's merged shapes and sends VMMS eight small asks.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`) · `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-cli/`) · `react-hook-form` (`.claude/skills/react-hook-form/`) for the prefilled forms and dialogs

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Cross child contract

### Data model (the target; each child owns its part)

| Entity | Key | New or changed fields | Links | Child |
|---|---|---|---|---|
| `Vehicle` (changed) | `id` | `vmmsVehicleId` uuid unique nullable (null only until `fleet:link` runs), `make` varchar(100)?, `truckSizeCategory` varchar(50)?, `garageId` uuid?, `syncedAt` timestamptz?. Plate, model, capacity, status, odometer and `isActive` are copies. `VehicleStatus` loses `DISABLED` | N:1 `Garage` | 0001 |
| `Garage` (changed) | `id` | `vmmsGarageId` uuid unique nullable, `syncedAt` timestamptz?. `name` and `isActive` are copies | 1:N `Vehicle` | 0001 |
| `VehicleChange` (kept) | `id` | sync rows: actor name `VMMS`, actor id null | N:1 `Vehicle` | 0001 |
| `RepairTicket` (changed) | `id` | `driverId` becomes nullable (null only on a ticket opened from a referral), `vmmsEventVersion` int default 0 (the last version VMMS accepted), `bmsEventVersion` int default 0 (the last version sent to BMS), `vmmsProviderId` uuid? and `outsideShopName` varchar(150)? (set on the move to `OUTSOURCED`). `priorVehicleStatus` is no longer written (dropped in a later cleanup) | 1:N `Referral`, `ExpediteRequest`, `Delivery` | 0002, 0003 |
| `Referral` (new) | `id` uuid = VMMS `referralId` | `vehicleId` FK, `vmmsVehicleId`, `vehiclePlate`, `maintenanceScheduleId` uuid, `workOrderNumber` varchar(40), `odometerReading` int, `findings` jsonb, `chiefMechanicRemarks` text?, `status` `ReferralStatus`, `rejectionReason` text?, `decidedByUserId`?, `decidedByName`?, `decidedAt`?, `repairTicketId` FK?, `receivedAt`, `payloadHash` char(64) | N:1 `Vehicle`, N:1 `RepairTicket` | 0002 |
| `ExpediteRequest` (new) | `id` uuid = BMS `requestId` | `repairTicketId` FK, `jobOrderNumber` varchar(40), `reason` text, `neededBy` date?, `status` `ExpediteStatus`, `responseReason` text?, `newPriority`?, `newDueAt`?, `decidedByUserId`?, `decidedByName`?, `decidedAt`?, `receivedAt`, `payloadHash` | N:1 `RepairTicket` | 0003 |
| `Delivery` (new) | `id` uuid = the `eventId` sent | `seq` bigserial unique (stable send order, even for two rows from one save), `target` (`VMMS`, `BMS`), `kind`, `payload` jsonb, `status` `DeliveryStatus`, `attempts`, `firstAttemptAt`?, `nextAttemptAt`, `lastAttemptAt`?, `lastStatusCode`?, `lastError`?, `sentAt`?, `manualRetryCount`, `dismissReason`?, `createdAt`; `repairTicketId` FK? (SetNull), `referralId` FK?, `expediteRequestId` FK?; index (`status`, `nextAttemptAt`), index (`target`, `repairTicketId`, `createdAt`) | N:1 each, nullable | 0004 |

Enums: `ReferralStatus` = `WAITING`, `OPENED_TICKET`, `ADDED_TO_TICKET`, `REJECTED`. `ExpediteStatus` = `WAITING`, `ACCEPTED`, `DECLINED`. `DeliveryStatus` = `PENDING`, `SENT`, `FAILED`, `DISMISSED`.

The `driverId` change is the one addition to the model confirmed in the design talk: it follows from "referral tickets need no driver", because the column is required today.

### Auth grants (welinc-auth `prisma/seeds/clients.seed.ts`, slice 1)

| Client | Audience | Scopes added | Why |
|---|---|---|---|
| `vrms` | `VMMS` | `fleet.read`, `fleet.repair-status.write`, `repair.referral-status.write` | fleet copy; repair events; referral rejections |
| `vrms` | `BMS` | `schedule.read`, `repair.update.write` | upcoming trips; repair updates and expedite answers |
| `vmms` | `VRMS` | `repair.referral.write`, `repair.status.read`, `repair.history.read`, `fleet.change.write` | referrals; status read; history read; fleet change messages |
| `vmms` | `BMS` | `fleet.availability.write`, `fleet.change.write` | VMMS's own senders to BMS (spec vmms/0026), granted here because the registry is shared |
| `bms` | `VRMS` | `repair.status.read`, `repair.expedite.write` | active repair read; expedite requests |

VRMS catalog (`prisma/catalog/vrms.ts`): `integration.respond`, label "Answer other systems", group Tickets, description "Accept or reject VMMS referrals, answer BMS expedite requests, and retry failed deliveries.", `defaults(true, false, false)`. Add the same key to backend-vrms's `permissions.fake.ts`.

### Inbound guard

`@ServiceRoute(scope)` gains a client list: `@ServiceRoute('repair.referral.write', { clients: ['vmms'] })`. It checks `token_use: service`, `aud: VRMS` (already), the scope (already), and the `client_id` claim (new; 403 `FORBIDDEN`). VMMS's fleet routes skip the client check, and this spec doesn't repeat that gap.

### Outbound calls

VRMS calls VMMS and BMS through the suite gateway's internal address, `SUITE_GATEWAY_INTERNAL_URL`, the same variable VMMS's senders use. That is the architecture rule (calls between systems go through the gateway), and it means one URL. Service tokens come from the existing `service-token-client.ts`, one client per audience and scope set.

### Settings (backend-vrms `src/settings/catalog.ts`)

| Key | Default | Range | Used by |
|---|---|---|---|
| `integration.retryWindowHours` | 24 | 1 to 168 | 0004 |
| `integration.deliveryRetentionDays` | 90 | 7 to 365 | 0004 |
| `fleet.reconcileMinutes` | 60 | 15 to 1440 | 0001 |

### Asks of VMMS (they go in AC-27's doc; VMMS's specs say "pending VRMS review"). Until each lands, VRMS works with VMMS as built, as noted per ask.

Slice 1:
1. **Accept any `eventVersion` above the last one**, not exactly +1, and ignore lower ones as stale. Every event carries the full current state, so a skipped version loses nothing. VRMS already numbers at send time so it never skips (AC-13), which makes this a safety net, not a blocker.
2. **Send referrals only from the every minute job**, not inside the Chief Mechanic's request (`maintenance-schedules.service.ts` awaits `deliverOne` today, which adds up to 5 s). VMMS's own spec 0024 says the workflow must not depend on VRMS.
3. **Retry 401 and 403 within the 24 hour window**, like 5xx. On a new setup they usually mean a grant or key still being fixed.
4. **Add VRMS as a `fleet-changes` recipient**: the same body VMMS sends BMS, to `POST {gateway}/vrms/integrations/vmms/fleet-changes` with audience `VRMS` and scope `fleet.change.write`.
5. **Let `LINKS_UPDATED` add only referrals**: a second referral for a schedule that's already linked adds no new schedule, and today that answers 409. Until then, VRMS sends `STATUS_UPDATED` carrying the new referral id (AC-13).
6. **Serve the outside shop list to services**: `GET /vmms/fleet/outsourced-providers` behind the existing `fleet.read`, answering `{ providers: { id, name }[] }` (active only, ordered by name, `no-store`). Today `GET /vmms/config/outsourced-providers` takes people only. Needed for AC-36, and features 36 to 39 reuse it.
7. **Refuse to deactivate a truck that has an open VRMS repair** (a `VrmsRepairEventReceipt` whose last status is open), with a message naming the ticket. Otherwise every later event for that ticket answers 404 (AC-35).
8. **Check a maintenance schedule's state only when it is first linked**, not on every later event. Today a Chief Mechanic who changes the work order after the referral makes every later event for that ticket answer 409. Until then, such a row fails and blocks the ticket until an Admin dismisses it.

Noted for them, not chased (between VMMS and BMS): the BMS availability sender retries a 400 forever and blocks that truck's later events; the fleet routes don't check `client_id === 'bms'`; the mobile "For Repair" suggestion still needs more failed than passed items instead of any failed item.

Slice 2 asks are in [0005](0005-next-slice.md).

### Asks of BMS (nothing for Flow C is built in BMS yet)

1. A service route, `GET /bms/integrations/vrms/vehicles/:vmmsVehicleId/schedule`, behind `schedule.read` for client `vrms`. The shape is in child 0003. It is also the read their Flow B gives VMMS.
2. A receiver, `POST /bms/integrations/vrms/repair-updates`, that writes `VehicleDispatchProfile.statusReason`, `expectedBackAt` and `statusRemarks` (nothing writes them today) and flags the affected bookings.
3. A receiver, `POST /bms/integrations/vrms/expedite-answers`, plus the expedite request sender with their own retry and a BMS Admin retry button.
4. The active repair read on their booking and truck pages.
5. Routes in their own gateway (`bms-gateway/src/routes.ts`) for `/bms/integrations/vrms/*`.

## Feature design

The data model is above. Each child holds its own routes, **Value sourcing** table, invariants and test scenarios. This section holds what spans them.

**Security model**:
- **Service routes:** every `/vrms/integrations/*` route takes a service token only (audience `VRMS`, its scope, its `client_id`). A person's token gets 403 `WRONG_TOKEN_USE`. No route takes a cookie.
- **What VMMS sees:** ticket numbers, statuses, the outside shop name, issue text, parts as text, mechanic names and the ticket total. It never sees part prices, notes, remarks, drivers or photos.
- **What BMS sees:** ticket number, status, issue category names, issue counts, dates. It never sees costs, notes or people.
- **People:** acting on referrals, expedites and failed deliveries needs `integration.respond`. Seeing deliveries needs `audit.view`. Opening a ticket from a referral also needs `ticket.create`.
- **Audit:** every decision a person makes and every system change to a ticket writes an audit row (AC-25).
- **Secrets:** no new secrets. Calls use VRMS's existing client key (`AUTH_CLIENT_PRIVATE_KEY`). Request bodies are logged by id only, never in full, except in `Delivery.payload`, which holds no personal data beyond mechanic names.

**Configuration required**:
- `SUITE_GATEWAY_INTERNAL_URL`: the gateway's address inside the network, for VRMS's calls to VMMS and BMS. Locally it is the gateway container on `welinc-network`, and on staging the gateway app's internal address, set in Bicep. It goes in backend-vrms's `src/config/env.ts` and `.env.example` together.
- The three settings above, through Settings, not the environment.

**Critical test scenarios** (beyond each child's):
- Happy path: on local stacks, a VMMS Chief Mechanic marks a job For Repair, the VRMS Admin opens a ticket, and VMMS shows the truck Under Repair and the linked ticket on its work order. Verifies **AC-6**, **AC-8**, **AC-13**.
- Failure: VMMS is stopped while the Admin closes the ticket. The close succeeds, the delivery retries, and once VMMS is back the truck turns Available. Verifies **AC-21**.
- Fleet: VMMS renames a plate, VRMS shows the new plate within a minute, and the truck's history shows the change by VMMS. Verifies **AC-2**, **AC-3**.
- Auth: a BMS token calling the referral intake gets 403, and a person's token calling any integration route gets 403. Verifies **AC-24**.
- Cleanup: `fleet:link` without `--confirm` changes nothing, stops on a double claim, and with it archives exactly the listed trucks and garages, leaving their tickets readable. Verifies **AC-1**.

## Build plan

Tracer Bullet: the first thread runs one referral end to end (VMMS → VRMS → ticket → event back to VMMS) on real local stacks before anything thickens. BMS's half comes last because BMS has built nothing yet; VRMS's side of flow 3 is built against a local stub until their routes land.

**Slice 1**

1. welinc-auth (branch from `development`): the client grants and `integration.respond` above; seed and catalog tests. Satisfies **AC-26**, **AC-11**
2. backend-vrms migration 1: the `Vehicle` and `Garage` fields, the `Referral` and `Delivery` tables, and on `RepairTicket` a nullable `driverId`, `vmmsEventVersion`, `vmmsProviderId` and `outsideShopName`. Show "None (from VMMS)" wherever a driver is read (ticket list, detail, history, analytics, exports). Add the settings keys and `SUITE_GATEWAY_INTERNAL_URL` (env schema, `.env.example`, compose, Bicep). Satisfies **AC-1**, **AC-6**, **AC-13**, **AC-21**
3. The client check on `@ServiceRoute` and the `/vrms/integrations` module skeleton with `no-store`. Satisfies **AC-24**
4. The fleet client and `fleet:link` (dry run, double claim stop, `--confirm` archive); run it locally. Satisfies **AC-1**
5. The outbox write helper and the worker with the retry rule and per ticket order (no UI yet). Satisfies **AC-21**
6. **Thread:** referral intake route → the Referrals tab (list and side panel) → "Open a ticket" prefilled form → the `OPENED` repair event → VMMS's receiver marks the truck Under Repair. Check it on local stacks with VMMS's `development`. Satisfies **AC-6**, **AC-7**, **AC-8**, **AC-11**, **AC-12**, **AC-13**
7. The fleet change receiver, the reconcile job with its guard, the fresh read on ticket create, removing the vehicle status writes, toggle and type edit, the read only Settings, Vehicles screen, the "Truck removed in VMMS" flag, and the migration that drops `DISABLED`. Satisfies **AC-2**, **AC-3**, **AC-4**, **AC-5**, **AC-35**
8. Every other repair event (each status move, close, cancel), "Add to REP-…", Reject, and the status and history reads. Then the outside shop picker on the outsource move (`vmmsProviderId`, `outsideShopName`), with a local stub until VMMS serves the list. Satisfies **AC-9**, **AC-10**, **AC-13**, **AC-14**, **AC-15**, **AC-36**
9. The Deliveries tab with Retry and Dismiss, the retention job, and the system actor audit rows. Satisfies **AC-22**, **AC-23**, **AC-25**
10. backend-vrms migration 2: `ExpediteRequest`, `bmsEventVersion`. Then the BMS repair updates (through the one due date writer in child 0003), expedite intake, the banner, the accept and decline dialogs, auto decline, the active repair read, and the Upcoming trips card and form panel against a local BMS stub. Satisfies **AC-16**, **AC-17**, **AC-18**, **AC-19**, **AC-20**, **AC-25**
11. `docs/integration/repair-integration.md` with the asks, the OpenAPI replies for every integration route, and links from `docs/integration/README.md`. Satisfies **AC-27**, **AC-24**
12. Staging: `seed:clients` and `catalog:sync` in auth, `fleet:link --confirm` as a one off job, then turn on the reconcile job. Check flows 1 and 2 against VMMS staging, and flow 3 once BMS ships. Satisfies **AC-1**, **AC-26**

**Slice 2**: the tasks are in [0005](0005-next-slice.md), built after slice 1 (VMMS builds its side in parallel).

## Consequences

**Positive**:
- Trucks have one owner. VRMS, VMMS and BMS can no longer disagree on a plate or a status for more than one sync.
- No handoff is lost to an outage. Every message is in a table, retried for a day, and then shown with a retry button.
- VMMS's merged half works as soon as VRMS ships. Eight small asks, none of which changes a payload VMMS already sends.
- The defense shows reads, events and commands in both directions across all three systems.

**Negative / tradeoffs**:
- Archived Capstone 1 trucks and their tickets stay in the database, hidden from pickers but still in history and analytics, until the realistic reseed (feature 47) replaces the data.
- Outsourcing a ticket now depends on VMMS's shop list. If VMMS has been unreachable for over 24 hours, the move waits.
- VRMS can't repair a truck VMMS hasn't registered until slice 2's register request, and VRMS Admins depend on VMMS Operations for that.
- More moving parts in VRMS: two jobs (sync and worker), one more table to watch, and a new failure mode (a failed delivery) that someone must look at.
- Flow 3 is only half real until BMS builds four things. The VRMS side is tested against a stub.
- The 15 second worker means VMMS sees a status change up to about 15 seconds late in the normal case.

**Neutral**:
- `Vehicle.status` becomes VMMS's value. Spec 0020's toggle and its `VEHICLE_STATUS_LOCKED` rule are retired, and spec 0020 needs an "Updated" line.
- `RepairTicket.priorVehicleStatus` stops being written. Drop the column in a later cleanup migration.
- The Settings, Vehicles screen keeps its history dialog, now fed by the sync.

## Follow-up

- [ ] Run `/architect` for feature 42 (due dates) next. It must write `dueAt` only through child 0003's `setDueAt` so BMS hears every change.
- [ ] Send VMMS and BMS the link to `docs/integration/repair-integration.md` (written 2026-11-26 as checklists, flows 4 to 7 included). Ask the register request later.
- [ ] Mark spec 0020 updated: no toggle, no `DISABLED`, status copied from VMMS (AC-4).
- [ ] Feature 47 (realistic reseed): VRMS's seed must stop creating trucks and garages and run `fleet:link` and the sync after VMMS's seed. Design it with this in mind.
- [ ] Feature 28 (notifications): turn the referral and expedite dashboard cards into bell notifications once it exists.
- [ ] Feature 36 to 39 (outsourcing): build on AC-36's shop picker and VMMS's provider route instead of a directory of their own.
- [ ] Papers: name the outbox, the retry rule and the three message styles (read, event, command). The BMS breakdown flow stays future work.
