# Verify: cross group integration · spec 0029 · updated 2026-11-28
_Steps derived from spec 0029 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones. Milestone 1 (shared setup and plumbing) below; later milestones append their own sections._

## Milestone 1: shared setup and plumbing

### Commands
- [ ] In welinc-auth, `npm run catalog:sync -- --dry-run` after a sync says "VRMS permissions: no changes" → AC-26
- [ ] `oauth_clients.service_scopes` for `vrms`, `vmms` and `bms` holds exactly the scopes in the umbrella's *Auth grants* table, nothing more → AC-26
- [ ] `POST /auth/token` (client credentials) as `vrms` for audience `VMMS`, scope `fleet.repair-status.write` answers a token; as `vrms` for audience `VRMS` answers `invalid_target` → AC-26
- [ ] As `bms`, ask for audience `VRMS` scope `repair.referral.write`: refused `invalid_scope` (only `vmms` holds it) → AC-26
- [ ] The portal's Roles page lists "Answer other systems" under Tickets for VRMS, on for Admin, off for Chief Mechanic and Mechanic → AC-11
- [ ] `docker exec welinc_vrms_backend npx prisma migrate status` says up to date, and `\d referrals`, `\d deliveries` show the tables; `repair_tickets.driver_id` is nullable with its foreign key still `ON DELETE RESTRICT` → AC-1, AC-6, AC-13, AC-21
- [ ] `curl -i http://localhost:3000/vrms/integrations/anything` answers with `Cache-Control: no-store`, also on a 401 or 403 once a route exists → AC-24
- [ ] With `SUITE_GATEWAY_INTERNAL_URL` unset, backend-vrms refuses to start with "SUITE_GATEWAY_INTERNAL_URL: is required" → AC-21
- [ ] Settings, Integration shows "Keep retrying a message for" (24 hours, 1 to 168), "Keep sent messages for" (90 days, 7 to 365) and "Full truck and garage check every" (60 minutes, 15 to 1440) → AC-3, AC-21, AC-23

### Worker, live (VMMS stopped locally, so the gateway answers 502)
- [ ] Insert a `REPAIR_EVENT` delivery for a real ticket: within 15 s it is `PENDING` with `attempts` 1, `last_status_code` 502, `last_error` `UPSTREAM_UNAVAILABLE`, next attempt 30 s after the last → AC-21
- [ ] Set `integration.retryWindowHours` to 1 and backdate `first_attempt_at` by 2 hours: the next attempt makes the row `FAILED` → AC-21 (value source: the setting, not a constant)
- [ ] Insert a second row for the same ticket: it stays at `attempts` 0 while the first is `PENDING`, and while it is `FAILED`; once the first is `DISMISSED` the second is sent → AC-21
- [ ] Two rows inserted in one transaction for one ticket are sent in `seq` order → AC-21
- [ ] With VMMS running and accepting, a sent `REPAIR_EVENT` carries `eventVersion` one above the ticket's `vmms_event_version`, the row ends `SENT`, and the ticket's `vmms_event_version` moves while its `updated_at` does not → AC-13, AC-21
- [ ] Stop welinc-auth: a due row stays `PENDING` with `last_error` `AUTH_UNAVAILABLE` and no status code, and nothing is posted → AC-21

### Guard (once the first `/vrms/integrations` route lands in milestone 2)
- [ ] A person's token answers 403 `WRONG_TOKEN_USE`; a `bms` service token on a `vmms` only route answers 403 `FORBIDDEN` "This route does not accept calls from this service" → AC-24

## Acceptance criteria coverage (milestone 1)
- AC-11: the Roles page step (the route checks come with milestone 2)
- AC-21: the worker steps and the env check
- AC-24: the no-store step and the guard step
- AC-26: the catalog, registry and token steps (staging's `seed:clients` and `catalog:sync` are milestone 5)

## Milestone 2, part 1: fleet link and the referral thread (tasks 4 and 6)

### Commands
- [ ] `npm run fleet:link` (in the backend container) prints the plan and changes nothing; a second run after `--confirm` plans "link N, archive 0, add 0" → AC-1
- [ ] Two VRMS trucks whose plates differ only in case stop the run with "STOP: 2 VRMS rows match VMMS …" and exit 1, nothing changed → AC-1
- [ ] After `--confirm`, archived trucks have `is_active` false and a null VMMS id, their tickets still open, and each has one `vehicle_changes` row by `VMMS` → AC-1
- [ ] `fleet:link --confirm` with `SENTRY_ENVIRONMENT=production` refuses → AC-1

### Referral intake (routes VMMS calls)
- [ ] VMMS's sender delivers a queued referral: VMMS marks it `SENT`, VRMS stores it `WAITING` with empty notes as null and the empty checklist id kept → AC-6
- [ ] The same body again answers 202 `duplicate: true` and writes no row; a changed body answers 409 `REFERRAL_ID_REUSED` → AC-6
- [ ] An `Idempotency-Key` that differs from `referralId` answers 400 `IDEMPOTENCY_KEY_MISMATCH` → AC-6
- [ ] A `vmmsVehicleId` VMMS doesn't have answers 422 `VEHICLE_NOT_FOUND`; with VMMS stopped, an unknown truck answers 503 `VMMS_UNAVAILABLE` → AC-6
- [ ] No token answers 401 with `Cache-Control: no-store`; a `bms` token answers 403 `FORBIDDEN`; a person's token answers 403 `WRONG_TOKEN_USE` → AC-24

### UI
- [ ] As `vrms.admin@`, Repair tickets shows Tickets and Referrals with the waiting count; `/repairs?view=referrals` lists the referral (plate chip, WO, findings, received) → AC-7
- [ ] As `vrms.chief@` (no `integration.respond`), there is no Referrals switch, and `GET /vrms/referrals` answers 403 → AC-11
- [ ] The dashboard shows "Referrals waiting" linking to the tab → AC-7
- [ ] A row opens the side sheet with the findings, remarks, odometer and WO, and "Open a ticket" → AC-7
- [ ] "Open a ticket" fills the truck, its garage, the odometer and one issue per finding; the driver is optional; saving creates the ticket and the referral turns "Ticket opened" → AC-8
- [ ] The new ticket shows "From VMMS WO-…" in its header and in the list, Driver "None (from VMMS)", and the Activity line "opened … from a VMMS referral" → AC-12
- [ ] Two Admins opening a ticket from one referral: the second gets 409 `REFERRAL_ALREADY_DECIDED` → AC-8
- [ ] A truck with an open ticket shows "Open REP-…" in the sheet instead of "Open a ticket" (Add to ticket comes with milestone 3) → AC-9

### Events to VMMS
- [ ] Creating a ticket queues one `REPAIR_EVENT` (`OPENED`, `OPEN`); creating it Assigned queues `OPENED` then `STATUS_UPDATED` (`ASSIGNED`) → AC-13
- [ ] Once VMMS fixes its advisory locks, the `OPENED` event is accepted, VMMS shows the truck Under Repair and the ticket on its work order, and the ticket's `vmms_event_version` is 1 → AC-13 (blocked: VMMS answers 500 today)

### Staging order (from this run)
- [ ] Deploy backend-vrms with the new key before running welinc-auth's `catalog:sync`, or clear `permission_sync_state.etag` once after; otherwise VRMS never pulls the `integration.respond` cells → AC-26

## Milestone 2, part 2: fleet copy kept current, read only trucks (task 7)

### Commands
- [ ] `docker exec welinc_vrms_backend npx prisma migrate status` is up to date, and `select enum_range(null::"VehicleStatus")` answers `{AVAILABLE,UNDER_REPAIR,UNDER_MAINTENANCE}` with no row left on `DISABLED` → AC-4
- [ ] `curl -i -X POST http://localhost:3000/vrms/integrations/vmms/fleet-changes` with no token answers 401 with `Cache-Control: no-store`; a person's token answers 403 `WRONG_TOKEN_USE`; a `bms` service token answers 403 `FORBIDDEN` → AC-24
- [ ] `POST /vrms/vehicles/:id/status` and `PATCH /vrms/vehicles/:id` answer 404 (the routes are gone), and `/vrms/docs` lists neither → AC-4

### Change messages (once VMMS sends to VRMS, ask 4)
- [ ] VMMS renames a plate: the receiver answers 202 `{ accepted: true }` at once, and within a minute Settings, Vehicles shows the new plate, with a History row "Plate ... by VMMS" → AC-2
- [ ] VMMS deletes a truck: the next message deactivates it (`is_active` false, never deleted) and its History says "In VMMS: In the fleet → Removed in VMMS" → AC-2
- [ ] A message for a truck while VMMS is stopped: still 202, the backend logs "left for the reconcile", nothing changes → AC-2

### Reconcile (value source: `fleet.reconcileMinutes`, not a constant)
- [ ] After a backend restart the log shows "Fleet reconcile: N trucks and M garages read, 0 deactivated" within a minute, then not again until the setting's minutes pass; set it to 15 in Settings, Integration and see the next run 15 minutes later → AC-3
- [ ] Set a linked truck `is_active` false in VRMS's database: the next reconcile sets it back and writes a History row by VMMS → AC-3, AC-35
- [ ] With two of six linked trucks missing from VMMS's list (more than 20%), the run deactivates nothing and reports "Deactivated nothing: 2 of 6 active trucks..." to Sentry under `fleet-reconcile`; with one missing, that one is deactivated → AC-3
- [ ] VMMS answers an empty truck list: nothing is deactivated, garages still apply, and the failure is reported → AC-3
- [ ] A VMMS plate that clashes with another local row's plate: the plate is skipped, the other fields apply, and Sentry gets "Fleet sync skipped: truck ..." → AC-3
- [ ] On a database where `fleet:link` has never linked a truck, the job runs nothing → AC-1, AC-3

### Ticket create
- [ ] Create a ticket for a linked truck VMMS shows Under maintenance: it saves (no lock), and the truck keeps VMMS's status (no "Under repair" written by VRMS, no new History row) → AC-4, AC-5
- [ ] Stop VMMS and create a ticket: it saves and a warning toast says "VMMS can't be reached, using the last copy"; the reply carries `fleetStale: true` → AC-5
- [ ] A truck VMMS no longer has (404 on the fresh read) answers 422 `VEHICLE_NOT_IN_VMMS` and writes nothing → AC-5
- [ ] The truck picker lists only active linked trucks; a search with no match says "Not in VMMS yet. Ask VMMS Operations to add it." → AC-5
- [ ] Close or cancel a ticket: the truck's status and odometer stay as VMMS has them, and no History row is written → AC-4

### UI
- [ ] Settings, Vehicles says "Managed in VMMS. To add or change a truck, ask VMMS Operations. Last update from VMMS …", shows Truck (plate chip, make and model without the make twice), Size, Garage, Status, Open ticket, chips All, Available, Under repair, Under maintenance, and only History (plus Open REP-…) in the row menu → AC-4
- [ ] The History dialog words sync rows: Plate, Garage, Capacity in kg, Size, Status with no "Ticket removed", and "In VMMS" → AC-3, AC-4
- [ ] With a linked truck inactive, its open ticket shows "Truck removed in VMMS" as a chip in the list and a warning banner on the detail page; the Admin dashboard shows "Trucks removed in VMMS (n)" linking to `/repairs?removed=1`, where the "Truck removed in VMMS only" switch is on → AC-35
- [ ] The flag clears on the next sync once VMMS lists the truck again, and the card disappears at 0 → AC-35

## Acceptance criteria coverage (milestone 2, part 2)
- AC-2: the change message steps (blocked until VMMS adds VRMS as a recipient)
- AC-3: the reconcile steps and the History wording
- AC-4: the migration, removed routes, ticket create and close, and Settings, Vehicles
- AC-5: the ticket create steps and the picker
- AC-35: the UI flag steps and the reconcile reactivation

## Milestone 3: rest of flows 1 and 2 (tasks 8 and 9)

### Commands
- [ ] In welinc-backend-vrms: `npm run lint`, `npm run build`, `npm run openapi:check`, `npx jest` all pass → AC-24
- [ ] `audit_logs.repair_ticket_id` is nullable after `prisma migrate deploy` (`20261127180000_audit_without_ticket`) → AC-10, AC-22
- [ ] In welinc-web-vrms: `npm run lint`, `npm run typecheck`, `npm run build:local`, `npx vitest run` all pass

### Referral decisions (as `vrms.admin@`, Repairs, Referrals tab)
- [ ] A waiting referral for a truck with an open ticket shows "Add to REP-…", "Open REP-…" and "Reject"; one with no open ticket shows "Open a ticket" and "Reject" → AC-9
- [ ] "Add to REP-…" lists one line per finding, text "label: note" prefilled, system empty and required; saving adds the issues as `[System] text`, sets the referral `ADDED_TO_TICKET`, and writes `REFERRAL_ADDED` then one `ISSUE_ADDED` per line, 1 ms apart → AC-9
- [ ] The same Add, with the ticket changed in another tab first, answers 409 `STALE` in the dialog and changes nothing → AC-9
- [ ] Add queues `LINKS_UPDATED` with the new schedule and referral ids; a second referral for a schedule already on the ticket queues `STATUS_UPDATED` instead (ask 5) → AC-13
- [ ] "Reject" needs 5 to 500 characters; saving sets `REJECTED`, writes `REFERRAL_REJECTED` with no ticket, and queues a `REFERRAL_REJECTED` delivery with `{ eventId, referralId, eventType: 'REJECTED', reason, occurredAt }` → AC-10
- [ ] Two Admins deciding one referral at once: the second gets 409 `REFERRAL_ALREADY_DECIDED` → AC-8, AC-10
- [ ] A Chief Mechanic (no `integration.respond`) gets 403 on add and reject, and sees no Referrals tab → AC-11

### Repair events (one per change, ticket row locked)
- [ ] Start work, Send for verification, Return to mechanic, Close, Cancel, and the mechanic add (M1) and last remove (M2) each queue one `REPAIR_EVENT` in the same transaction: `STATUS_UPDATED`, `COMPLETED` on Close, `CANCELLED` on Cancel → AC-13
- [ ] A stale status move queues nothing → AC-13
- [ ] The rows for one ticket go out in `seq` order: a later row waits while an earlier one is retrying (seen live: `LINKS_UPDATED` behind the failing `OPENED`) → AC-13, AC-21

### Reads VMMS calls (needs a `vmms` service token, minted by VMMS or on staging)
- [ ] `GET /vrms/integrations/vmms/repairs/<id>` answers `{ repairTicketId, repairTicketNumber, status, outsideShopName }`; `PENDING_APPROVAL` reads `OUTSOURCED` with the shop; an unknown id answers 404 `REPAIR_NOT_FOUND`; `Cache-Control: no-store` → AC-14, AC-24
- [ ] `GET /vrms/integrations/vmms/vehicles/<vmmsVehicleId>/repair-history?limit=50` lists the truck's tickets newest first, never cancelled ones, with issue lines "System: text", parts "description xN" and no prices, distinct mechanic names, the provider and `totalRepairCost` as a string; `nextCursor` pages on; an unknown truck answers 200 with no items → AC-15
- [ ] A `bms` token on either read answers 403 `FORBIDDEN`; a person's token answers 403 `WRONG_TOKEN_USE` → AC-24

### Outside shop
- [ ] `GET /vrms/config/outside-shops` answers VMMS's list; with VMMS's route missing (404, ask 6) it answers the four stub shops; with VMMS stopped after one good read it answers the kept list with `stale: true`; with none kept, 503 `VMMS_UNAVAILABLE` → AC-36
- [ ] An Outsourced or Pending approval ticket with no shop shows "Pick the outside shop"; picking one shows "At <shop>" in the header, writes `TICKET_EDITED` (field `outsideShop`) and queues `STATUS_UPDATED` carrying `outsideShopName` → AC-36
- [ ] Picking again answers 409 `SHOP_ALREADY_SET`; on an open ticket not outsourced, 409 `NOT_OUTSOURCED` → AC-36
- [ ] Code check until feature 37: `applyStatusMove` refuses M9 without `vmmsProviderId` (unit test) → AC-36

### Deliveries (Audit logs, Deliveries tab)
- [ ] An `audit.view` holder sees the tab; failed rows list first; the tab shows the failed count; filters by status, system and message → AC-22
- [ ] A `PENDING` row with 3 or more attempts shows the warning and its last status code → AC-22
- [ ] The side panel shows the payload, the attempt times and the last error; Retry on a failed row sets it `PENDING` with attempts 0 and a fresh window, and the worker sends it within 15 s; Dismiss needs a reason, sets `DISMISSED`, and lets the ticket's later rows go → AC-21, AC-22
- [ ] Retry and Dismiss write `DELIVERY_RETRIED` and `DELIVERY_DISMISSED`, with the ticket when the row has one; on a row that isn't failed they answer 409 `NOT_FAILED` → AC-22, AC-25
- [ ] The Activity tab reads a rejection as "sent back VMMS referral WO-…" and a dismissed rejection message as "dismissed a failed message for a VMMS referral" → AC-25
- [ ] Without `integration.respond`, the panel has no Retry or Dismiss → AC-11, AC-22

### Retention (value source: `integration.deliveryRetentionDays`, not a constant)
- [ ] Set the setting to 7, run `DeliveryRetentionJob.run()`: `SENT` and `DISMISSED` rows older than 7 days go; `PENDING` and `FAILED` rows of any age stay → AC-23

### Local test data from this run
- Two referrals were inserted by hand: `WO-20261127-000101` (CAK 9043, added to REP-20261126-7J6W) and `WO-20261127-000102` (NRE 471, rejected, its message marked `FAILED` by hand and then dismissed). Their deliveries and audit rows stay; the referral rows can be deleted with `DELETE FROM referrals WHERE work_order_number IN ('WO-20261127-000101','WO-20261127-000102')` once the deliveries pointing at them are gone or set aside.

## Acceptance criteria coverage (milestone 3)
- AC-8: concurrent decisions · AC-9: Add steps · AC-10: Reject steps · AC-11: permission steps · AC-13: repair event steps · AC-14, AC-15: the two reads · AC-21: per ticket order, Retry · AC-22: Deliveries steps · AC-23: retention · AC-24: token and `no-store` steps · AC-25: audit rows for decisions and deliveries (system actor rows come with flow 3) · AC-36: outside shop steps (M9 itself with feature 37)

## Milestone 4: flow 3 against a BMS stub (task 10)

Start the stand in for BMS first (the BMS stack must be stopped, it uses the same name): `docker run -d --rm --name vrms-bms-stub --network welinc-network --network-alias bms-gateway -v "$PWD/welinc-backend-vrms/scripts:/stub:ro" node:24-alpine node /stub/bms-stub.mjs`. Its log (`docker logs vrms-bms-stub`) shows every call and body. Once BMS ships its routes, run the same steps against BMS's `development` instead.

### UI / manual
- [ ] As `vrms.admin@`, open New repair and pick a linked truck → "Upcoming trips in BMS" lists the stub's three trips under the truck, the JO and booking numbers in mono, "Confirmed" or "Pending" on the right → AC-16
- [ ] Stop the stub, pick another truck → "BMS can't be reached." with Retry; the form still saves. Start the stub, press Retry → the trips appear → AC-16
- [ ] Open an open ticket on a linked truck → an "Upcoming trips" card sits under Details ("From BMS, the next 14 days"); a closed ticket has no card; the 3 s refresh never calls the schedule again (Network tab) → AC-16
- [ ] Create a ticket on a linked truck, then move it once → two `REPAIR_UPDATE` rows on the Deliveries tab, "Repair opened" then "Status changed to …", sent with `eventVersion` 1 then 2 (stub log), and `repair_tickets.bms_event_version` ends at 2 → AC-17
- [ ] A ticket with a waiting expedite request shows the banner ("BMS asks to speed up this repair"), each JO with its reason, "needed by" date and received time; a Mechanic sees the banner with no buttons → AC-18, AC-11
- [ ] Accept on a High ticket → the dialog starts at Critical; set a new expected return and save → priority Critical, the due date moved, Activity shows "accepted a BMS expedite request", "Priority: High → Critical" and "Due: … → …" (note "Expedite JO-…"), and the stub receives the repair update (changeReason "Expedite JO-…", the new `expectedReturnAt`) before the `ACCEPTED` answer → AC-19, AC-17
- [ ] Add a VMMS referral with a new system (for example Brakes) to an open ticket → the stub receives a repair update with changeReason "Issues added from VMMS WO-…" and the new category in `reason` → AC-17
- [ ] Accept again without touching the date → no `dueAt` row and no repair update, only the answer → AC-19
- [ ] Decline with a reason under 5 characters → the button stays disabled; with a real reason → the stub receives `DECLINED` with that reason → AC-19
- [ ] Two Admins answer the same request → the second sees "JO-… was already answered." and the page reloads → AC-19
- [ ] Close (or cancel) a ticket with two waiting requests → both become Declined ("Repair finished" or "Repair cancelled"), Activity names VRMS as the actor, and the stub gets the closing update, then the two answers → AC-19, AC-25
- [ ] The Admin dashboard shows "Expedite requests" (Needs you) while any wait, and the list under it links to each ticket; the tile jumps to the list → AC-18
- [ ] On the Deliveries tab, fail a `REPAIR_UPDATE` (stop the stub until it fails, or mark it by hand), then Dismiss it → a fresh update with "Resent after a failed delivery" is queued with the ticket's current state → AC-22

### Commands
- [ ] `POST {gateway}/vrms/integrations/bms/expedite-requests` with a `bms` service token (scope `repair.expedite.write`) for a truck with an open ticket → 202 `{ requestId, status: 'WAITING', repairTicketNumber, duplicate: false }` and an `EXPEDITE_REQUESTED` row with actor BMS; the same body again → `duplicate: true`; a changed body → 409 `REQUEST_ID_REUSED`; a truck with no open ticket → 404 `NO_OPEN_REPAIR` → AC-18, AC-25
- [ ] The same route with a `vmms` token or a person's token → 403 → AC-24
- [ ] `GET {gateway}/vrms/integrations/bms/vehicles/<vmmsVehicleId>/active-repair` with a `bms` token → the ticket number, status and label, reason (category names only), issues resolved of total, `expectedReturnAt` and `openedAt`, nothing else; a truck with no open ticket → `{ "repair": null }`; `Cache-Control: no-store` → AC-20, AC-24
- [ ] `npx jest src/modules/integrations/bms src/modules/vrms/expedite-decisions.service.spec.ts src/modules/vrms/apply-status-move.spec.ts` in welinc-backend-vrms → all pass → AC-16 to AC-20

### Value sourcing (child 0003)
- [ ] `reason`: a ticket with Brakes and Electrical issues (Electrical twice) sends "Brakes, Electrical" in category order; a ticket with no categorized issue sends "Not yet diagnosed"
- [ ] `expectedReturnAt`: equals `dueAt` while open, null once Closed or Cancelled, null when no due date
- [ ] `repairStatus` and `repairStatusLabel`: VRMS's own value and label, Pending approval included (not mapped to Outsourced as for VMMS)
- [ ] `eventVersion`: one above `bms_event_version`, independent of `vmms_event_version`
- [ ] `serviceDate` on the trips card: a trip on `2026-12-01` shows "Tue, Dec 1" in every browser time zone (it is a calendar day, never shifted)
- [ ] The accept dialog's date: 5:00 PM entered in Manila is stored and sent as 09:00Z

### Local test data from this run
- Three expedite requests were inserted by hand: `JO-2026-0142` (accepted, REP-20261114-KO7E is now Critical with a due date of Nov 30, 5:00 PM), `JO-2026-0157` (declined) and `JO-2026-0161` (still waiting on REP-20261126-7J6W). One `EXPEDITE_REQUESTED` audit row says "Inserted for the local live check".

## Acceptance criteria coverage (milestone 4)
- AC-16: trips steps (form, card, BMS down) · AC-17: update steps and value sourcing · AC-18: banner, intake and dashboard steps · AC-19: accept, decline, race and auto decline steps · AC-20: active repair command · AC-22: dismiss resend · AC-24: token and `no-store` · AC-25: BMS and VRMS as named actors
