# Verify: cross group integration · spec 0029 · updated 2026-11-27
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
