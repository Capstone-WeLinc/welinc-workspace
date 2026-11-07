# Verify: Chief dashboard rework with a Team section · spec 0022 · updated 2026-11-05
_Steps derived from spec 0022 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones. They replace the steps for the removed `/mechanics` page._

Seed logins: `vrms.chief@welinc.com` and `mech.juan@welinc.com` (password `mechanic1234`), `vrms.admin@welinc.com` (`admin1234`). Restart `welinc_vrms_backend` after any backend edit.

## UI / manual
- [x] Sign in as the Chief at 375px → Dashboard shows the header (Dashboard, today's date, last updated), a summary block, then For verification · N, My work · N, Team; no tiles, no Needs attention, no pipeline → AC-5, AC-6
- [x] Network tab on the Chief dashboard → no `/vrms/repairs/history` request → AC-5
- [x] Resize to 1280px → the summary spans the full width; For verification above My work in a narrow left column, Team in a wide right column; Tab order is summary, For verification, My work, Team; no horizontal scroll → AC-6
- [x] Summary block: the count equals the full For verification queue, the oldest ticket shows plate, names and wait, Verify the oldest opens that ticket; the line reads "N working · N not started · N free" and matches the roster minus the Chief, with "N with no mechanic" only when some exist; with an empty queue it reads "Nothing waiting for verification." and has no button → AC-7
- [x] For verification rows: plate, mechanic names and the wait on line 1, the issue on line 2 (one line); at most 8; "See all" only above 8 and it opens `/repairs?status=FOR_VERIFICATION`; the Chief's own tickets are not in it → AC-8, AC-9
- [x] Wait colour: a ticket For verification for 5 hours reads muted, 30 hours amber, 50 hours red; one with no date stays muted → AC-8
- [ ] My work rows: ticket number then the due label (overdue in red, none without a due date); empty shows "Nothing assigned to you." → AC-8, AC-9
- [x] Each row is one link to `/repairs/:id`, at least 44px tall at 375px → AC-8
- [x] The Chief is not listed anywhere in Team (Busy, Free, counts) → AC-10
- [ ] People order: inactive first, then anyone with an overdue ticket, then most open tickets, then name. Press Start work as a mechanic: their row stays put and the In progress part of their bar grows. Assign them another ticket: they move up → AC-11
- [x] A Busy row: click it and it opens in place (the chevron turns); the name shows the email on hover; a small line shows "Chief mechanic" or "Inactive" when true and "On <plate>" for their In progress truck; up to 3 trucks "Plate, status, time" (overdue text in red in place of the time) → AC-12
- [x] A person with 4 tickets shows 3 trucks and "See all 4 and reassign"; the button opens the dialog; a person with 3 or fewer shows "Reassign or unassign" → AC-12, AC-14
- [ ] Two people with the same name show their emails; others do not → AC-12, AC-13
- [ ] The workload bar: segments for In progress, For verification and Not started, scaled to the busiest person; the note reads "N overdue", else "N for verification", else "Nothing started" when nothing is In progress; the key sits above the list → AC-12
- [x] Free tab: shows the count on the tab, every free person in two columns from 640px (one below), no email unless two share a name; "Nobody is free right now." when none → AC-13
- [ ] Unassign the last mechanic from an In progress ticket → it shows in the No mechanic panel above Team → AC-10
- [x] Open a person's dialog → title "<name>'s open tickets", list loads fresh; Reassign one ticket → toast, dashboard tickets and Team update within a moment, dialog stays open → AC-14
- [x] As a Chief whose `ticket.assign` is turned off in the permission matrix → the dialog lists tickets with no Reassign or Unassign → AC-14
- [x] Block `GET /vrms/mechanics/roster` (devtools request blocking) and reload → the summary, For verification and My work render, Team shows its own error with Try again, and the summary line leaves out the team numbers → AC-7, AC-15
- [x] Turn `mechanics.view` off for the Chief → no Team section, the summary line reads "N in my work", and the sections keep the same layout → AC-7, AC-15
- [x] Go to `/mechanics` → not found; the sidebar, phone tab bar, user menu and breadcrumb match `development` → AC-16
- [x] Admin dashboard (tiles, Needs attention, pipeline, spend) and the Mechanic dashboard unchanged; Users page Work column, filter and dialog Unassign and Reassign unchanged → AC-17
- [x] axe at 375px and 1280px: loaded (Busy tab and Free tab), every section empty, roster failing, dialog open → no violations from the dashboard → AC-18

## Value sourcing
- [ ] Summary and heading counts: the For verification count equals the full queue the Chief can verify, even above 8 → AC-7
- [ ] Team people come from `GET /vrms/mechanics/roster`: compare names, emails, roles and active flags with the response → AC-10, AC-12
- [ ] Viewer left out by `authUserId` equal to the signed in user's id (the token `sub`) → AC-10
- [ ] Trucks and bars join on `mechanicId`: rename a mechanic so two share a name; each still shows only their own trucks → AC-10
- [ ] "See all N" equals roster `total` → AC-12
- [ ] Time in status uses `statusChangedAt` against the fetch time: a ticket changed 3 hours ago reads "3 h", one with no date reads "time unknown" → AC-12
- [ ] Overdue text uses `dueAt` at the fetch time: set a due date yesterday → red "Overdue by 1 day", the person's note reads "1 overdue" and they move up → AC-11, AC-12
- [ ] No mechanic panel: open tickets past Assigned with `mechanicCount` 0 → AC-10
- [ ] Summary line and Free tab read roster `occupied`, `total` and `isActive` → AC-7, AC-13
- [ ] Bar groups: In progress and Outsourced count as In progress, For verification on its own, every other open status as Not started; "On <plate>" is the In progress ticket running longest → AC-12
- [ ] Wait colour limits: 24 hours amber, 48 hours red, measured to the fetch time → AC-8
- [ ] Fallback row: a ticket assigned to a mechanic not yet on the roster shows under a row named from the ticket, opens in place and has no dialog button → AC-15
- [ ] Dialog actions follow the viewer's `ticket.assign`; Team visibility follows `mechanics.view` → AC-14, AC-15

## Commands
- [x] As `mech.juan@welinc.com`: `GET /vrms/mechanics/roster` → 403 → AC-2
- [x] As the Chief: `GET /vrms/mechanics/roster` → rows carry `mechanicId` → AC-2
- [x] `npm run lint`, `npm run build`, `npm run test` in `welinc-backend-vrms`; plus `npm run typecheck` in `welinc-web-vrms` → green → all

## Acceptance-criteria coverage
- AC-1 key label, by the permission matrix and catalog tests · AC-2 Commands 1 and 2 · AC-3 built earlier, unchanged · AC-4 built earlier, unchanged · AC-5 UI 1, 2 · AC-6 UI 1, 3 · AC-7 UI 4, 19, 20, Value 1, 9 · AC-8 UI 5 to 8, Value 11 · AC-9 UI 5, 7 · AC-10 UI 9, 16, Value 2 to 4, 8 · AC-11 UI 10, Value 7 · AC-12 UI 11 to 14, Value 5, 6, 10 · AC-13 UI 13, 15 · AC-14 UI 12, 17, 18 · AC-15 UI 19, 20, Value 12 · AC-16 UI 21 · AC-17 UI 22 · AC-18 UI 23
