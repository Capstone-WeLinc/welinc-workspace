# Verify: full ticket audit trail · spec 0021 · updated 2026-11-04
_Steps derived from spec 0021 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## UI / manual
- [x] As Admin, unlock a Closed ticket with a reason, change the parts cost and the remarks, save → the ticket's Activity shows, newest first, "locked REP again", "edited REP" with "Remarks: old → new", and "updated the costs of REP"; the edit and cost rows show the unlock reason, the locked row shows none → AC-1, AC-2, AC-3, AC-15
- [x] Same ticket: unlock again and save with nothing changed → only one "locked REP again" row is added → AC-3
- [x] Unlock a Cancelled ticket, change the cancel reason, save → "Cancel reason: old → new" under the edit row, clamped to 2 lines, full text in the tooltip on hover and keyboard focus → AC-2, AC-15
- [x] Unlock a ticket, send a blank remark (spaces only), save → stored remarks unchanged, no edit row, only the locked row → AC-2
- [x] Open the ticket in two tabs, unlock and save in one, save in the other → 409, and no new rows from the second save → AC-3
- [x] As a mechanic on an In progress ticket, tick a checklist step → Activity shows "ticked a step on REP" with "2. <step text>" as a muted line; untick it → "unticked a step on REP" → AC-4, AC-15
- [x] Tick a step that is already ticked (stale screen in a second tab) → no new row, and the step comes back as it is → AC-5
- [x] After a tick, the ticket's last activity moves, its "updated" time does not, and a later save with the old lastUpdatedAt still works → AC-4
- [x] Create a ticket with two mechanics → Activity shows "created REP", then "assigned a mechanic to REP" with "Assigned: A, B." 1 ms later; create one with no mechanic → only "created REP" → AC-5b, AC-3b
- [x] On the Audit log page, every older chip (Created, Status, Costs, Unlocks, Garage, Edits, Issue chips) still filters as before → AC-10 (`type` alias)

## Commands
- [x] `GET /vrms/repairs/audit-logs/catalog` as Admin → 7 categories in order STATUS, ASSIGNMENT, EDITS, COSTS, FILES, CHECKLIST, KNOWLEDGE, each with its types → AC-7, AC-11
- [x] The same call as a user with `audit.view` but no `ticket.costs.view` → no COSTS entry → AC-11, AC-12
- [x] `GET /vrms/repairs/audit-logs` → every event has `category`; a row with an action outside the catalog has `category: null` → AC-8
- [x] `?categories=CHECKLIST&types=COST_UPDATE` → only step ticks and cost rows → AC-9
- [x] `?actorRole=SYSTEM` → only rows with no actor (`actor: null`); `?actorRole=CHIEF_MECHANIC` → only rows with that role → AC-9
- [x] `?types=NOPE`, `?categories=checklist`, `?actorRole=admin` → 400 naming the parameter; `?categories=,` → 200, no filter; 31 types → 400 → AC-10
- [x] `?type=UNLOCK&types=LOCKED` → both types → AC-10
- [x] As a caller without `ticket.costs.view`: `?categories=COSTS` → 200 with an empty list, and no COST_UPDATE, receipt or other document rows in any list → AC-10, AC-12
- [x] In psql: `UPDATE audit_logs SET note='x'`, `DELETE FROM audit_logs ...`, `TRUNCATE audit_logs CASCADE` → each fails with `audit_logs is append only`; an INSERT works → AC-13
- [x] `npx prisma migrate diff --from-config-datasource --to-schema prisma/schema.prisma` → "No difference detected", and `pg_trigger` still lists `audit_logs_no_change` and `audit_logs_no_truncate` → AC-13
- [x] `npm run seed` (wipes dev data) → succeeds, and afterwards both triggers are enabled (`tgenabled = 'O'`) → AC-14
- [x] `npx jest src/modules/vrms/audit-append-only src/modules/vrms/audit-coverage` → pass; adding `tx.auditLog.update(` to any non test file under `src/` fails the guard → AC-6, AC-14

## Value sourcing
- [x] COST_UPDATE before values match the ticket as loaded; after values are what the save wrote, with an unsent field keeping its stored value, and totalCost as the save computed it → AC-1
- [x] A Chief without `ticket.costs.edit` saving an unlocked ticket with costs in the body → no COST_UPDATE (costs ignored), still LOCKED → AC-1
- [x] Notes come from the ticket's stored `unlockReason`, not from anything in the save body → AC-1, AC-2
- [x] Actor fields on every new row are the signed in user from the token (name, email, role), never a body value → AC-6
- [x] Rows from one action: times are now, now+1 ms, now+2 ms in write order; the ticket's `lastActivityAt` equals the newest one; `updatedAt` equals now → AC-3b
- [x] Mechanic names on the create row are the picked mechanics' names in the order picked → AC-5b
- [x] Step text and position come from the copied step row ("4. Clean and grease ..."), ids from the route → AC-4
- [x] Two simultaneous ticks of one step (two tabs, or two requests at once) → exactly one STEP_CHECKED row → AC-5

## Acceptance-criteria coverage
- AC-1, AC-2, AC-3 · UI steps 1 to 5, value sourcing 1 to 3
- AC-3b · UI step 9, value sourcing 5
- AC-4, AC-5 · UI steps 6 to 8, value sourcing 7 and 8
- AC-5b · UI step 9, value sourcing 6
- AC-6 · command 12, value sourcing 4
- AC-7, AC-8 · commands 1 and 3
- AC-9, AC-10 · commands 4 to 8, UI step 10
- AC-11, AC-12 · commands 1, 2 and 8
- AC-13, AC-14 · commands 9 to 12
- AC-15 · UI steps 1, 3 and 6
