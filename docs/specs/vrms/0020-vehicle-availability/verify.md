# Verify: vehicle availability · spec 0020 · updated 2026-11-03
_Steps derived from spec 0020 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Sign in as the seed Admin (`vrms.admin@welinc.com`) unless a step says otherwise. Restart `welinc_vrms_backend` first if the backend changed.

## UI / manual
- [x] Settings, Vehicles: open the row menu of an Available truck → it shows "Disable truck" and "History" → AC-10
- [x] Choose Disable truck → the dialog title names the plate, the reason has a counter, and the confirm stays off with "ab" typed → AC-11
- [x] Type "  Brakes failed inspection  " and confirm → the row shows Disabled in place, the toast reads "<plate> is now Disabled.", focus is back on that row's menu button → AC-1, AC-11
- [x] Open History for that truck → the newest entry is "Status: Available → Disabled", by Victor Ramos, with the local time and "Reason: Brakes failed inspection" (trimmed) → AC-1, AC-13
- [x] Make it available again with a reason → the row shows Available and a second history row appears → AC-2
- [x] A row with an open ticket: the menu shows "Disable truck" greyed out, then "Has open ticket REP-…", which opens `/repairs/:id` → AC-10
- [x] A truck with no history yet → History shows "No changes recorded yet." → AC-13
- [x] A truck with more than 20 changes → History shows 20 and "Load more"; stop the backend and press it → the 20 stay and an inline error with "Try again" appears; start it again and retry → the next page appends → AC-9, AC-13
- [x] Two tabs on Vehicles: disable a truck in tab one, then try it in tab two → tab two's dialog closes, the toast reads "This truck changed. Reload and try again.", and the list reloads → AC-5, AC-11
- [x] Open the dialog on an Available truck, then create a ticket for it in another tab, then confirm → the stale rule answers first (a ticket create changes the truck row, AC-5a): the dialog closes, the stale toast shows, and after the reload the row menu shows "Has open ticket REP-…". The open repair message itself needs a fixture: with the dialog open, point an open ticket at that truck in the database (`update repair_tickets set vehicle_id = <truck id> where id = <ticket id>`, which leaves `vehicles.updated_at` alone), then confirm → the dialog shows the server's open repair message, keeps the typed reason, and the list reloads with the hint. Point the ticket back and cancel it afterwards → AC-4, AC-5, AC-11
- [x] Chips: pick Disabled → the address gets `?status=DISABLED`, only Disabled trucks show, and the page goes back to 1; type a search too → both must match → AC-12
- [x] Open `/settings/vehicles?status=bogus` → All is selected and every truck shows, Under maintenance ones included → AC-12
- [x] Full cycle on a Disabled truck: create a ticket on it → History shows "Status: Disabled → Under repair" with "Ticket REP-…"; cancel the ticket → "Status: Under repair → Disabled" with the same ticket, and the truck is Disabled → AC-6, AC-7, AC-15
- [x] Close a ticket on an Available truck → History shows "Under repair → Available" with the ticket, by the person who closed it → AC-7
- [x] A type change shows as "Type: Not set → 6 wheeler" with no "Ticket removed" line → AC-13
- [x] Sign in as a Mechanic → the Vehicles section is not in Settings → AC-14
- [x] 375px and 1280px: the list, both dialogs (a bottom sheet on phones) and the chips fit with no sideways page scroll, and axe has no new findings (the dev only Demo data pill and the Settings nav description fail contrast already) → AC-16

## Commands
- [x] `POST /vrms/vehicles/:id/status` with `{ status: 'UNDER_REPAIR', reason: 'Not allowed', updatedAt }` → 400 → AC-3
- [x] Same call with `reason: '   ab '` → 400 "Reason must be 5 to 500 characters." → AC-1
- [x] Same call on a truck with an open ticket → 409 `{ code: 'OPEN_TICKET_EXISTS', message: 'This truck has an open repair, REP-…. Change its status after the repair is closed or cancelled.', ticket: { id, repairNumber } }` → AC-4
- [x] Same call with the current status as the target (and a fresh `updatedAt`) → 409 `STALE_VEHICLE` → AC-3
- [x] Same call with an old `updatedAt` → 409 `STALE_VEHICLE`, nothing written → AC-5
- [x] Toggle an unknown truck id (a valid uuid that is not a truck) with a bad body, such as `reason: 'ab'` → 400, not 404, because body validation runs first; the same unknown id with a valid body → 404 → AC-5a
- [x] Set a truck's status to `UNDER_MAINTENANCE` in the database, then toggle it → 409 `VEHICLE_STATUS_LOCKED` "This truck's status is set by maintenance."; put it back afterwards → AC-3, AC-5a
- [x] Race: both orders end consistent. Toggle first, then a ticket create on the same truck → both succeed (a ticket may go on a Disabled truck, AC-15) and history reads Available → Disabled, then Disabled → Under repair with the ticket. Ticket first, then the toggle → the toggle gets 409 and writes nothing. To force the second order, hold the truck row lock in a database session (`begin; select id from vehicles where id = … for update;`), send the ticket create, then the toggle, then commit → AC-4
- [x] `GET /vrms/vehicles` → every row has `openTicket` (`{ id, repairNumber }` or null); after a successful toggle the returned row has `openTicket: null` → AC-8
- [x] `GET /vrms/vehicles/:id/changes?limit=2` twice, passing `nextCursor` → no row repeats, the order is newest first, the last page has `nextCursor: null`; `?cursor=bad` → 400; an unknown id → 404 → AC-9
- [x] As a Mechanic, call all three vehicle endpoints → 403 → AC-14
- [x] `select field, before, after, note, repair_ticket_id from vehicle_changes order by created_at desc` after the full cycle → one row per status change, `note` only on manual rows, `repair_ticket_id` only on create and release rows → AC-1, AC-6, AC-7

## Value sourcing
- [x] toggle target status: send `DISABLED` then `AVAILABLE` → the stored `after` matches the input each time
- [x] toggle reason: send padded text → `note` holds it trimmed
- [x] toggle before: change the truck in the database between page load and save → the stale check refuses it rather than writing a wrong `before`
- [x] toggle open ticket block: a ticket in each open status (Open, On hold, Pending approval) blocks; a Closed or Cancelled one does not
- [x] toggle actor: `actor_name` and `actor_email` come from the signed in user, never from the body (send an extra `actorName` field → 400, whitelisted body)
- [x] toggle stale check: an `updatedAt` written in another ISO form of the same instant (for example `+00:00` in place of `Z`) is still accepted
- [x] toggle reason length: 4 characters after trimming fails, 5 passes, 500 passes, 501 fails
- [x] create before and after: a ticket on a Disabled truck writes `before: "DISABLED"`; on a stuck Under repair truck with no open ticket it writes no row
- [x] create actor: the reporter of the ticket is the history actor
- [x] create repairTicketId: the row's `repair_ticket_id` equals the new ticket's id
- [x] release before: the row's `before` is the truck's status just before the release (Under repair)
- [x] release after: Disabled when `prior_vehicle_status` was Disabled, else Available
- [x] release actor: the person who closed or cancelled is the actor, not the ticket's reporter
- [x] list openTicket: a truck with an open ticket shows it; after it closes, the next list shows null
- [x] history ticket number: delete a test ticket (or set `repair_ticket_id` null) → the entry reads "Ticket removed"
- [x] history type names: a type row shows names, "Not set" for null
- [x] history status words: every status reads with the `statusLabels.ts` label (Under repair, Under maintenance)
- [x] history who: a row with a null `actor_name` reads "System"
- [x] links: every ticket link goes to `/repairs/:id`
- [x] history local time: change the browser time zone (Asia/Manila to UTC) → the shown time moves with it
- [x] filter chip: `?status=AVAILABLE`, `UNDER_REPAIR`, `DISABLED` pick their chip; anything else (including `UNDER_MAINTENANCE`) means All

## Acceptance criteria coverage
- AC-1: UI steps 3, 4; commands 2, 12; value sourcing reason rows · AC-2: UI step 5 · AC-3: commands 1, 4, 7 · AC-4: UI step 10; commands 3, 8 · AC-5: UI step 9; command 5 · AC-5a: commands 6 and 7 plus the order tests in `vehicles.status.spec.ts` · AC-6: UI step 13; command 12 · AC-7: UI steps 13, 14 · AC-8: command 9 · AC-9: UI step 8; command 10 · AC-10: UI steps 1, 6 · AC-11: UI steps 2, 3, 9, 10 · AC-12: UI steps 11, 12 · AC-13: UI steps 4, 7, 8, 15 · AC-14: UI step 16; command 11 · AC-15: UI step 13 · AC-16: UI step 17
