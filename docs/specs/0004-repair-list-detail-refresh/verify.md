# Verify: Repair list & detail · spec 0004 · updated 2026-10-22
_Steps derived from spec 0004 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Seed logins: `vrms.admin@welinc.com` (admin), `mech.juan@welinc.com` (mechanic, assigned to every seed ticket), `mech.pedro@welinc.com` (mechanic, assigned to none). Open `/login?token=<jwt>` to skip the portal.

## UI / manual

### Repair list (`/repairs`)
- [x] As admin, open `/repairs` → title "Repair tickets", subtitle "Open repair tickets across every garage.", a "New repair ticket" button → AC-1
- [x] As a mechanic → subtitle "Open repair tickets assigned to you.", no header button, no Mechanic filter → AC-1, AC-4
- [x] No Completed or Cancelled ticket appears, on any page → AC-2
- [x] Rows run from the earliest due date to the latest, tickets with no due date last; the order holds across pages and after a reload → AC-3
- [x] Type a plate in Search → one request about 300ms after typing stops, the URL gains `q=`, the page resets to 1 → AC-4, AC-5
- [x] Change Status, Garage, Mechanic and Overdue only one at a time → each narrows the list from the server, goes back to page 1, and writes `status`, `garage`, `mechanic`, `overdue=1` to the URL → AC-4, AC-5
- [x] Filter, go to page 2, then use the browser back button → you leave the list in one step (filter changes replace history) → AC-5
- [x] Open `/repairs?status=NOPE&garage=bad&page=99` → All open, All garages, and the last page, with the URL corrected → AC-5, AC-8
- [ ] As a mechanic, open `/repairs?mechanic=<any uuid>` → the param is ignored and dropped → AC-5
- [x] At 1280px the table has no horizontal scroll; the Issue cell is one line with the full text in a tooltip (also on keyboard focus) → AC-6
- [x] An overdue row shows "Overdue by N days" in red with a warning icon named "Overdue"; a future due date shows "Due in N days"; no due date shows "—" → AC-6, AC-11
- [x] Click a row → `/repairs/:id`; the ⋮ menu offers View details (`?mode=readonly`) and Edit ticket → AC-7
- [x] Search for text that matches nothing → "No tickets match these filters" with "Clear filters", which resets every filter and the search box → AC-9
- [x] As `mech.pedro` → "No repair tickets assigned to you" → AC-9
- [x] Switch to another tab and back → one refetch of the same params, rows stay on screen with no skeleton → AC-10
- [x] At 375px the filters wrap, rows become cards, the repair number wraps at most once, no page scroll sideways → AC-4, AC-30

### Repair detail (`/repairs/:id`)
- [x] Open a ticket from a filtered list, press "Back to repairs" → the same filters and page → AC-12
- [x] Paste a ticket URL directly → "Back to repairs" goes to plain `/repairs`; on a closed ticket the link reads "Back to history" → AC-12
- [x] From 1024px: main column and a sticky side panel (Status, Details, People); below 1024px the side panel comes first → AC-13
- [x] As admin on a Pending ticket: "Start work" and "Cancel ticket"; In progress: "Send for verification"; For verification: "Mark completed" → AC-14
- [x] As `mech.juan` on a For verification ticket → "Waiting for an admin to sign off.", no button; on a closed ticket "This ticket is closed." → AC-14
- [x] `?mode=readonly` → "View only" plus "Open editable view", no action, cancel, Edit costs or bottom bar → AC-14
- [x] Press the next action, add a remark, confirm → spinner, toast "{REP} moved to {status}.", the new next action shows, Notes shows the remark → AC-15
- [x] Try to type 501 characters in the remark → the field stops at 500 → AC-15, AC-28
- [x] As admin, Start work on a ticket with no mechanic → the "No mechanic is assigned yet." warning, and confirm still works → AC-15
- [x] Cancel ticket with a blank reason → "Enter a reason for cancelling."; "Keep ticket" closes; with a reason the ticket closes → AC-16
- [x] Unlock a completed ticket with a blank reason → "Enter a reason for unlocking."; with a reason → toast "{REP} is unlocked.", badge "Unlocked for editing" → AC-17
- [x] Mark completed on a ticket with no costs (a newly created one) → the no costs warning with "Go to costs", which closes the dialog and moves focus to Costs → AC-18
- [x] Open one ticket in two tabs, move it in one, press the next action in the other → toast "This ticket changed since you opened it. We loaded the latest version.", the dialog closes, the new next action shows → AC-19
- [x] Same with costs: edit costs in both tabs, save in one, then the other → the form stays with your values and shows "Costs changed since you opened this…"; a second save goes through → AC-19
- [x] As a mechanic at 375px → the next action bar sits just above the tab bar and the last section is fully visible above it; no bar on a ticket with no button → AC-20
- [x] As admin at 375px and at 800px → the bar sits at the bottom edge; at 800px the button is on the right, clear of the sidebar → AC-20
- [x] On a For verification ticket: Edit costs → Itemized, leave a description empty → inline error; fill it, add a row, watch the live total, save → toast "Costs saved." and the itemized table → AC-21
- [x] On an unlocked completed ticket, save costs → the prompt "Save costs and lock {REP}?", then the ticket shows Locked → AC-21
- [x] A ticket with ₱0 labor shows ₱0.00, not "—" → AC-25b
- [x] Run AI diagnosis → result, similar cases, the rating; each star is a button named "Rate N out of 5"; stop the AI container and run again → the error shows inside the section only → AC-22
- [x] As admin, Show Activity → events grouped by day, rendered like the audit log page, the repair number as plain text; Load older appears past 50 events → AC-23
- [x] As a mechanic → no Costs and no Activity section → AC-21, AC-23
- [x] `/repairs/00000000-0000-4000-8000-000000000009` → "Repair ticket not found"; as `mech.pedro` on a seed ticket → "This ticket isn't assigned to you" → AC-24
- [x] axe on `/repairs` and `/repairs/:id` at 375px and 1280px, as admin and as a mechanic, with a dialog open → no serious or critical issues → AC-30

## Commands
- [x] `curl -H "Authorization: Bearer <admin>" "localhost:3000/vrms/repairs?overdue=yes"` → 400; `?garageId=abc` → 400 → AC-25
- [x] `?overdue=true&status=COMPLETED` → `{ data: [], total: 0 }` → AC-25
- [x] `GET /vrms/repairs` with no page or limit → every open row (the dashboard's call) → AC-25
- [x] As `mech.juan`, `GET /vrms/repairs?mechanicId=<someone else>` → still only Juan's tickets; as a mechanic with no linked record → `total: 0` → AC-26
- [x] As admin, `GET /vrms/repairs/audit-logs?ticketId=<id>` → only that ticket's events; as a mechanic → 403 → AC-27
- [x] `PATCH /vrms/repairs/:id/status` with a 501 character `remarks` → 400 → AC-28
- [x] `GET /vrms/repairs/:id` → no `auditLog` and no `shopChangeLog` keys → AC-29
- [x] `grep -rn "auditLog\|shopChangeLog\|AuditLogCollapsible\|UnlockTicketModal" welinc-web-vrms/src` → nothing → AC-29
- [x] `npm run lint && npm run build` in welinc-web-vrms; `npx tsc --noEmit && npm run test && npm run build` in welinc-backend-vrms → all pass → AC-30

## Value sourcing
- [x] Order: compare page 1 against a direct API call sorted by `target_due_date asc nulls last, created_at desc, id desc`
- [ ] Due text: set a ticket's `target_due_date` to now plus 1 hour → "Due today"; to 3 days ago → "Overdue by 3 days"; the text only changes after a refetch, never on its own
- [ ] Overdue only filter: a ticket due one minute from now is excluded, then included after it passes and the list refetches
- [ ] Garage and Mechanic options: block `/vrms/config/garages` → only "All garages", list still works
- [x] Back link: `location.state.from` from the list wins; with no state, open → `/repairs`, closed → `/history`
- [ ] Next action: walk Pending → In progress → For verification → Completed as admin and as `mech.juan`, matching the AC-14 table at each step
- [x] No costs warning: costs null versus costs 0 (0 counts as recorded)
- [x] Driver verified mark and lock badge: present for admins, absent for mechanics
- [x] `lastUpdatedAt`: every status, cancel and cost write sends the loaded `updatedAt` (check the request body)
- [ ] Activity: the ticket's events equal the audit log page filtered to the same repair number

## Acceptance-criteria coverage
- AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11: Repair list steps
- AC-12 to AC-24: Repair detail steps
- AC-25, AC-25b, AC-26, AC-27, AC-28, AC-29: Commands, plus the ₱0 detail step
- AC-30: the axe step, the 375px steps and the last command
