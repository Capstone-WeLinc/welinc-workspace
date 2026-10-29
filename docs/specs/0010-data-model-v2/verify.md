# Verify: Data model v2 · spec 0010 · updated 2026-10-29
_Steps derived from spec 0010 acceptance criteria and its Value sourcing table. `/check verify` runs these; `/test` locks the durable ones._

## Commands
- [ ] `ls welinc-backend-vrms/prisma/migrations` → only `20261029000000_baseline` and `migration_lock.toml` → AC-1
- [ ] `npx prisma migrate reset --force` in welinc-backend-vrms → succeeds on an empty database; `issue_categories` holds Brakes, Engine, Electrical, Suspension, Cooling, Transmission and General; `SELECT extname FROM pg_extension` lists `pg_trgm` → AC-1
- [ ] With a shadow database set, `npx prisma migrate diff --from-migrations prisma/migrations --to-schema prisma/schema.prisma` → no difference → AC-1
- [ ] `npm run seed` → succeeds; its summary prints closed, cancelled, assigned, in progress and for verification counts, all above 0 → AC-15
- [ ] SQL: every `CLOSED` ticket has `verified_by_user_id`, `verified_by_name` and `verified_at`; every ticket has `priority` and `reported_by_name`; every ticket's `last_activity_at` equals `max(created_at)` of its `audit_logs` rows → AC-15, AC-10
- [ ] SQL: `audit_logs.changes` is a JSON list on every row, `[]` on `CREATED`; no `SHOP_CHANGE` rows, `GARAGE_CHANGE` rows show `garage` before and after → AC-6, AC-15
- [ ] SQL: `DELETE FROM repair_tickets WHERE id = '<a ticket with audit rows>'` → fails with a foreign key violation → AC-8
- [ ] SQL: tables `bookings`, `maintenance_schedules`, `checklist_templates`, `checklist_items`, `shop_change_logs` and `_RepairTicketMechanics` do not exist; `mechanics` has no `is_outsourced` or `shop_name`, and `auth_user_id` is `NOT NULL` → AC-11, AC-12
- [ ] Search both repos for `completedAt`, `targetDueDate`, `isOutsourced`, `shopName`, `fieldName`, `previousValue`, `SHOP_CHANGE`, `RepairStatus.PENDING`, `RepairStatus.COMPLETED` → no ticket related hit (the outsourced rejection test is expected) → AC-2, AC-11
- [ ] welinc-backend-vrms: `npm run lint`, `npm run build`, `npm run test` pass; welinc-web-vrms: `npm run lint`, `npm run typecheck`, `npm run build` pass → AC-17
- [ ] With the whole Docker stack up after the reset, `docker ps` shows `welinc_vrms_analytics_ai` up (not restarting) even if its endpoints answer errors, and every other service is up → AC-17

## API
- [ ] As Admin, `POST /vrms/repairs` with one mechanic id and priority `HIGH` → `status: ASSIGNED`, `priority: HIGH`, `reportedByName` = the admin's name, `mechanics` lists the mechanic → AC-3, AC-5
- [ ] Same call with `mechanics: [{ "name": "Shop Guy", "isOutsourced": true }]` or a `shopName` field → 400 → AC-12
- [ ] Move that ticket `IN_PROGRESS` (as its mechanic), `FOR_VERIFICATION` (with resolutions), then `CLOSED` (as Admin) → statuses follow; the closed ticket has `verifiedByName` = the admin, `verifiedAt` and `closedAt` set → AC-4
- [ ] As a mechanic or chief mechanic, try `CLOSED` or `CANCELLED` on an assigned ticket → 403 naming "In progress, For verification" → AC-4
- [ ] As Admin, `ASSIGNED` to `CLOSED` directly → 400 "Cannot change status from 'Assigned' to 'Closed'" → AC-4
- [ ] Cancel an open ticket with a reason → `closedAt` set, no verifier, the audit event's `note` is the reason → AC-4, AC-6
- [ ] Send a status update with an old `lastUpdatedAt` → 409 → AC-4
- [ ] Save costs changing parts, labor and total in one go → `GET /vrms/repairs/audit-logs?ticketId=` shows one `COST_UPDATE` event with three `changes` → AC-6, AC-7
- [ ] Insert a ticket with `repair_status = 'ON_HOLD'` and a past `due_at` by SQL → it appears in `GET /vrms/repairs` (default) and with `overdue=true`, and not in `GET /vrms/repairs/history` → AC-4a
- [ ] `GET /vrms/repairs/history?status=CLOSED` works; `status=COMPLETED` → 400 → AC-16

## Value sourcing
- [ ] Create a ticket as a user whose welinc-auth name is empty → `reportedByName`, `assignedByName` and the `CREATED` row's `actor_name` hold the email, cut to 100 characters → Value sourcing (who names)
- [ ] Create a ticket as a chief mechanic holding both `MECHANIC` and `CHIEF_MECHANIC` in VRMS → the audit row's `actor_role` is `CHIEF_MECHANIC`; sending `actorRole` in a body is rejected by the ValidationPipe → Value sourcing (actorRole), Security model
- [ ] Every `TicketAssignment` row of a new ticket has `assigned_by_user_id` = the caller's `sub` → Value sourcing (assignedBy)
- [ ] After a status move, `repair_tickets.last_activity_at` equals the new audit row's `created_at` to the millisecond; after `GET` of the ticket and after ticking a checklist step it does not move → AC-10
- [ ] Link a known fix on a ticket → one `KNOWLEDGE_LINK` row with `knowledgeEntry` and `issueId` in `changes`, and the ticket's `last_activity_at` moves with it; a backfill link from the knowledge editor moves each linked ticket's `last_activity_at` too → AC-6, AC-10
- [ ] Every ticket read returns `dueAt: null` and `dueAtSource: null` (nothing writes them until feature 42) → AC-13

## UI / manual
- [ ] Repair list: default shows open tickets; the Status filter offers Assigned, In progress, For verification; badges read Assigned, In progress, For verification → AC-16
- [ ] Repair detail: next action reads Start work, Send for verification, Verify and close; People shows Reported by, and Verified by once closed; Details shows Closed date → AC-16
- [ ] Repair form: the mechanic picker lists in house mechanics only (no "Add as outsourced"), and there is no Repair shop field → AC-12
- [ ] Dashboard: the Waiting count still counts `FOR_VERIFICATION`; the pipeline reads Assigned, In progress, For verification, Closed → AC-16
- [ ] History page: Outcome filter offers Closed and Cancelled; tiles read Finished, Closed, Cancelled (and Total spend for admins) → AC-16
- [ ] Audit logs page: the Garage chip filters `GARAGE_CHANGE`; a cost event shows the total line and the parts and labor that changed; a cancel or unlock shows its reason → AC-6, AC-7
- [ ] Knowledge base entry: the change history dialog shows each save, with every changed field's before and after → AC-9
- [ ] A vehicle with status `DISABLED` (set by SQL) shows a Disabled badge where the vehicle status is shown → AC-14

## Acceptance criteria coverage
- AC-1 commands 1 to 3 · AC-2 leftover search · AC-3 API 1 · AC-4 API 3 to 7 · AC-4a API 9 · AC-5 API 1 · AC-6 API 8, Value sourcing 5, UI audit logs · AC-7 API 8, UI audit logs · AC-8 SQL delete · AC-9 UI knowledge · AC-10 SQL last activity, Value sourcing 4 and 5 · AC-11 SQL tables, leftover search · AC-12 API 2, UI form · AC-13 Value sourcing 6 · AC-14 UI vehicle · AC-15 seed and SQL checks · AC-16 UI section, history query · AC-17 lint, build, test and Docker
