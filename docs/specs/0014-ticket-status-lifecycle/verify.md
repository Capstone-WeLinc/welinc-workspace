# Verify: ticket status lifecycle · spec 0014 · updated 2026-10-31
_Steps derived from spec 0014 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Before you start: run `docker restart welinc_vrms_backend` and wait for "Nest application successfully started", because the container does not see edits made from Windows. Seed logins are in `welinc-auth/prisma/seeds/users.seed.ts` (Admin `vrms.admin@welinc.com`, a Chief Mechanic, a Mechanic). Open `/login?token=<jwt>` to skip the portal.

## UI / manual

- [x] As Admin, open an Assigned ticket assigned to a mechanic → the status card shows "Start work" and "Cancel ticket"; no "Verify and close" anywhere → AC-13, AC-15
- [x] As that Mechanic, Start work, then Send for verification with "What fixed it" filled → ticket is For verification, the page reads "Waiting for verification." with no button → AC-11, AC-15
- [x] As a Chief Mechanic not assigned to that ticket, open it → "Verify and close" and "Send back" side by side on desktop; on a 375px phone, "Verify and close" full width in the bottom bar with "Send back" under it → AC-6, AC-15
- [x] Chief clicks Verify and close with no costs entered → ticket Closed, People card shows the Chief under "Verified by", the truck shows Available on the vehicle list → AC-6, AC-7
- [x] On another For verification ticket, Chief clicks Send back, types "abc" → submit stays disabled; types "Rear pads still squeal" → submit enables → AC-16
- [x] Submit the Send back → ticket In progress; a warning banner near the top reads "Sent back by {Chief}, {n} minutes ago" with the comment; readable at 375px with no horizontal scroll → AC-8, AC-14, AC-17
- [x] On that ticket, each issue still shows its "What fixed it" note and hours with the tag "Sent back, not resent yet"; ticked steps are still ticked → AC-9, AC-21
- [x] The "Latest remark" in Notes is not the Send back comment (it stays whatever it was before) → AC-8
- [x] As the Mechanic, open Send for verification again → each issue's note, hours and "Followed the known fix" are prefilled; a linked issue with no saved choice shows the box ticked → AC-18
- [x] Resend → banner gone, tag gone (issues resolved again) → AC-14, AC-21
- [x] Assign a Chief Mechanic to a ticket, move it to For verification, open it as that Chief → no Verify or Send back; the card reads "Waiting for verification." → AC-6, AC-13
- [x] As Admin, open Settings, Roles and permissions → a "Verify or send back finished work" row exists (Admin and Chief on, Mechanic off); `ticket.administer` reads "Cancel tickets and make work moves on any ticket" → AC-5
- [x] Turn off `ticket.verify` for Admin, reload a For verification ticket as Admin → no Verify or Send back, Cancel still there; turn it back on → AC-5, AC-6
- [x] Open the same For verification ticket as Admin in two tabs; verify in tab A, then click Verify in tab B → toast "This ticket changed since you opened it…" and the page reloads as Closed → AC-12, AC-19
- [x] Two tabs on a closed ticket as Admin: unlock in tab A, then unlock in tab B → stale toast and reload, not a second unlock → AC-12, AC-19
- [x] Two tabs at For verification as Admin: save costs in tab A, then in tab B → the stale flow, typed values kept → AC-12, AC-19

## Commands

Use a token per role (from the portal or `/login?token=`), `T` a ticket id, `AT` its current `updatedAt`.

- [x] `PATCH /vrms/repairs/T/status {"status":"IN_PROGRESS","lastUpdatedAt":AT}` on a Closed ticket (locked, then unlocked) → 400 `{ code: "INVALID_TRANSITION", message: "Can't move a ticket from 'Closed' to 'In progress'.", allowed: [] }` → AC-3, AC-4
- [x] Same on an In progress ticket with `"status":"ON_HOLD"` → 400 with message "A ticket goes On hold when a hold is filed, not from here." and `allowed` listing only what this caller may make → AC-3
- [x] On an Assigned ticket as Admin, `"status":"CLOSED"` → 400, `allowed: ["IN_PROGRESS","CANCELLED"]` → AC-3
- [x] Status body without `lastUpdatedAt`, and with `"lastUpdatedAt":"yesterday"` → 400 validation on `lastUpdatedAt` (not 409) → AC-12
- [x] Same for `PATCH /vrms/repairs/T/unlock` and `PATCH /vrms/repairs/T/costs` with no `lastUpdatedAt` → 400 → AC-12
- [x] Stale `lastUpdatedAt` on a Closed ticket asking for `IN_PROGRESS` → 409, not 400 (stale is checked first) → AC-3a
- [x] As Mechanic, Verify (`CLOSED`) or Cancel on their own For verification ticket → 403 "You can't make this move on this ticket." → AC-6
- [x] As a Chief assigned to the ticket, Verify → 403 "Someone else must verify work on a ticket you're assigned to." → AC-6
- [x] Send back with `"remarks":"ok"` → 400 "Say what needs fixing."; Cancel with no `cancellationReason` → 400 "A cancellation reason is required" → AC-3a, AC-8, AC-10
- [x] Race: send two Verify requests with the same `lastUpdatedAt` at once (two terminals, or `Promise.all` in the console) → one 200, one 409, and only one `STATUS_CHANGE` row for that move in `GET /vrms/repairs/audit-logs?ticketId=T` → AC-12
- [x] Cancel an In progress ticket → `closedAt` set, no verifier, vehicle `AVAILABLE` with its odometer unchanged → AC-10
- [x] Verify a ticket whose odometer is higher than the vehicle's → vehicle odometer equals the ticket's; lower → vehicle odometer unchanged → AC-7
- [x] `GET /vrms/repairs/T` as each role → `moves` matches what the role may make now; Send for verification carries `needs: "resolutions"` with the knowledge module on and `null` with it off; a finished ticket has `moves: []` → AC-13
- [x] `GET /vrms/repairs` (list) → rows carry `can.verify` but neither `moves` nor `lastRejection` → AC-13, AC-14
- [x] Send back, then put the ticket On hold through the database or a later feature, then `GET` → `lastRejection` still set; move it to For verification → `lastRejection: null` → AC-14
- [x] `GET /vrms/permissions/me` as Admin, Chief Mechanic and Mechanic → equals the catalog defaults; `ticket.verify` for Admin and Chief only → AC-5
- [x] Deactivate a mechanic who is the only one on an Assigned ticket, then release their work → ticket Open with one `MECHANIC_UNASSIGNED` row recording `repairStatus ASSIGNED → OPEN` and no extra `STATUS_CHANGE` row → AC-1
- [x] `docker exec welinc_vrms_db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT repair_status, count(*) FROM repair_tickets GROUP BY 1;"'` → only the nine statuses; every open status present has a move out (2026-10-31: Assigned 4, In progress 5, For verification 2, Closed 385, Cancelled 26) → AC-20
- [x] `... -c "SELECT count(*), count(DISTINCT permission) FROM role_permissions;"` → 60 rows, 20 keys after a restart (2026-10-31: "Permission backfill inserted 3 rows") → AC-5
- [x] `npx jest` in welinc-backend-vrms → green, including `ticket-transitions.spec.ts` (every open status has a move out, finished have none) → AC-1, AC-2
- [x] Atomic: in a scratch test, make `tx.auditLog.create` throw during Verify → the ticket, its issues and the vehicle are unchanged → AC-7, AC-12

## Value sourcing checks

- [x] Allowed move: try every status pair on the status endpoint as Admin; only M3, M4, M5, M6, M14 succeed, from their own from status → `findMove` + table
- [x] Caller rights: the same ticket as an assigned Mechanic, an unassigned Chief, an assigned Chief and Admin gives four different `moves` lists → CASL on the loaded assignments
- [x] Status labels in errors match the badges in the app (`STATUS_LABELS`)
- [x] Verifier fields: `verifiedByName` is the caller's account name (email when the name is empty), `verifiedAt` equals `closedAt` equals the audit row's time → JWT `sub`, `whoName`, one `now`
- [x] Send back note: the audit row's note is the trimmed comment; `ticket.remarks` is unchanged → `dto.remarks` trimmed
- [x] Unassign release: the `MECHANIC_UNASSIGNED` row's actor is the Admin who released → existing row kept
- [x] Issues after Send back: `resolvedAt` null on every issue, notes, hours and followed kept → backward rule
- [x] `lastRejection.byName` falls back to the email when the actor had no name; `at` is the audit row's time → newest first scan
- [x] Banner relative time changes with the page's load time, not the server's clock → browser formatting

## Acceptance-criteria coverage

- AC-1 table test, unassign release step · AC-2 table test, data check · AC-3 three INVALID_TRANSITION commands · AC-3a stale first, needs last · AC-4 Closed to In progress (locked and unlocked)
- AC-5 settings row, `/me`, backfill count · AC-6 Chief verify, self verification, Mechanic 403, Admin without verify
- AC-7 verify UI, odometer command · AC-8 Send back UI, remarks command, Latest remark · AC-9 kept ticks and notes · AC-10 cancel command · AC-11 resend with resolutions
- AC-12 missing and malformed `lastUpdatedAt`, race, two tab steps on move, unlock and costs · AC-13 `moves` per role and on lists · AC-14 banner, On hold, resend clears it
- AC-15 desktop side by side, phone stack, "Waiting for verification." · AC-16 disabled submit · AC-17 banner at 375px · AC-18 prefilled resend · AC-19 stale and invalid toasts · AC-20 status count · AC-21 "Sent back, not resent yet" tag
