# Verify: Ticket detail redesign · spec 0024 · updated 2026-11-06
_Steps derived from spec 0024 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## UI / manual
- [ ] Open an In progress ticket with 5 issues where issue 1 is Done → issue 2 is open, the rest closed; the summary reads "1 of 5 issues done · t of s steps" → AC-4, AC-6
- [ ] Tick the last step of the open issue → its row turns "Done" with a full green bar at once and stays open; the summary updates → AC-3, AC-5
- [ ] Tick a step, then fold the row before the save returns; make the save fail (offline) → the step goes back when you reopen, with the error toast → AC-3
- [ ] A ticket with 3 issues or fewer, In progress → every row starts open → AC-4
- [ ] Open a For verification ticket as the verifier → every row closed; each line 2 shows What fixed it (or "Followed the known fix") and the hours as "2.5 h" → AC-2, AC-4
- [ ] Return a ticket to the mechanic → every issue with notes shows the gold "Returned" pill with no bar → AC-3
- [ ] Issue with no steps and no known fix → "No checklist", line 2 "No known fix"; inside: the link picker and "Suggest a known fix" → AC-2, AC-3, AC-10
- [ ] Issue whose known fix has safety notes → closed row says "Safety"; open row shows one amber line above the checklist, with More only when it is cut off → AC-2, AC-8
- [ ] A known fix in Draft or Inactive → its status badge shows on line 2 and inside the row; with the knowledge module off the name is plain text → AC-2, AC-10
- [ ] Inside an open row: safety, checklist (done steps dimmed, no strikethrough), the actions line (Edit steps, Hide done steps, Edit issue, Remove issue), the known fix with Change, then What fixed it → AC-7, AC-9, AC-10
- [ ] Turn on Hide done steps → "k done steps hidden" shows in their place; reload → still on → AC-5, AC-9
- [ ] Open two rows, reload → the same two are open; open the ticket in a new tab → the default rule applies → AC-5
- [ ] Visit `/repairs/<id>#issue-3` → issue 3 opens on top of what was open and scrolls into view below the header; `#issue-99` does nothing → AC-4
- [ ] Wait through several 3 second refreshes → no row opens or closes by itself; add an issue from another tab → it appears closed → AC-5
- [ ] Expand all and Collapse all work; with one issue they are hidden → AC-6
- [ ] Title: plate chip, model, then the first issue on one line without "[System]"; the ID and garage below, the ID never breaking → AC-11, AC-12
- [ ] Edit steps dialog subtitle and the For verification dialog show issue text without "[System]" → AC-12
- [ ] Photos line reads "Photos · b before · a after"; it starts open with any photo or a photo blocking the next move; Add photos opens the file picker → AC-13
- [ ] A Send for verification blocked by an after photo → the reason in the Status card is a link; it scrolls to Photos, opens it and focuses the add button. A costs reason stays plain text → AC-13
- [ ] AI card closed reads "AI suggests {category}, High priority" or "No AI diagnosis yet" with Run; make the latest diagnosis fail → one line with Retry; module off → no card → AC-14
- [ ] Activity shows the 5 newest; Show all replaces them with 50 and pages on; no audit.view → no card → AC-15
- [ ] Notes card is in the sidebar with a 3 line preview and Show more only when cut off; Vehicle and driver sits in Details with its Edit → AC-16
- [ ] Cancel ticket lives only in the ⋮ menu beside the status badge, in red, opening the cancel dialog; no cancel move → no ⋮ → AC-17
- [ ] At 375px: status line (badge, ⋮, blocked reason), Notes, Issues, AI, Costs, People, Details, Activity; the main button only in the bottom bar, never covering Activity → AC-18
- [ ] At 1280px the sidebar sits on the right; resize across 1024px → open rows and pending ticks stay → AC-18
- [ ] Keyboard: Tab to a row header, Enter and Space fold it, focus stays put; reduced motion → no fold animation → AC-1, AC-20
- [ ] axe at 375px and 1280px, rows open and closed, the loading skeleton and the empty issues state → no violations on the page (the dev only Demo data pill is excluded) → AC-19, AC-20

## Value sourcing
- [ ] Issue text with a leading `[Engine] ` → shown without it everywhere → `stripSystem`
- [ ] Category shows once, from `categoryName` → `issue.categoryName`
- [ ] Safety notes of only spaces → no "Safety" word → `safetyNotes` trimmed
- [ ] Progress "{x} of {y}" counts a tick made on the page before the refresh → `mergedSteps` with `useTickOverrides`
- [ ] Saved notes with `resolvedAt` cleared → Returned; with `resolvedAt` set → Done → `hasSavedResolution`, `resolvedAt`
- [ ] Line 2 note empty and `followedKnownFix` true → "Followed the known fix"; `hoursSpent` 0.25 → "0.25 h" → `resolutionNote`, `followedKnownFix`, `hoursSpent`
- [ ] Needs what fixed it shows only In progress, never in For verification → `ticket.status`
- [ ] Open rule changes with status, never with role (same ticket as Admin and as Mechanic) → `initialOpen`
- [ ] Photo counts match the strip's Before and After groups, before and after Start work → `photoGroups(attachments, workStartedAt)`
- [ ] Blocked link targets the photo the move waits for, and not while photos upload → `ticketActions().blockedBy`
- [ ] Title model left out when `vehicleModel` is empty; first issue follows `createdAt` then `id` → `ticket.issues[0]`
- [ ] AI line priority "CRITICAL" reads "Critical" → `predictedPriority` in sentence case
- [ ] Notes card shows the cancellation reason on a Cancelled ticket → `ticket.cancellationReason`, `ticket.remarks`
- [ ] Activity first request carries `limit=5`, Show all `limit=50` → `getAuditEvents`
- [ ] sessionStorage holds `vrms.ticket.<id>.view` as `{ open, hideDone }`; a 21st ticket drops the oldest; private mode still works from memory → `useTicketView`

## Commands
- [ ] `cd welinc-web-vrms && npm run lint && npm run typecheck && npm run build && npm run test` → all green (402 tests) → AC-19
- [ ] `cd welinc-backend-vrms && npm run build && npm test -- ticket-knowledge` → the issue order test passes → AC-4

## Acceptance-criteria coverage
- AC-1 keyboard step · AC-2 verifier, no known fix, safety, Draft steps · AC-3 tick, Returned, offline steps · AC-4 5 issue, 3 issue, verifier, hash steps · AC-5 reload, refresh, Hide done steps · AC-6 summary, Expand all · AC-7 to AC-10 open row steps · AC-11, AC-12 title and dialog steps · AC-13 photos and blocked link · AC-14 AI · AC-15 Activity · AC-16 Notes and Details · AC-17 ⋮ menu · AC-18 375px and 1280px · AC-19, AC-20 axe, keyboard, commands

## Refinements (build task 5) · added 2026-11-06
_These replace the older steps above where they disagree._
- [ ] Open an issue → safety, checklist, one "Edit steps"; the row ⋮ ("More actions for issue N") holds Edit issue, Remove issue (not with one issue), Change known fix (only when relinking is allowed), Open known fix (only with the knowledge module on) → AC-7, AC-10
- [ ] No separate known fix line in an open row; an issue with no known fix still shows the picker and Suggest a known fix → AC-10
- [ ] Hide done steps sits beside Expand all, hidden until a step is ticked; turning it on shows "{k} done steps hidden" in every open row ("1 done step hidden" singular); reload keeps it → AC-5, AC-6, AC-9
- [ ] A saved view from before the update (hideDone as a list) loads with the switch off → AC-5
- [ ] No photos and an after photo blocks Send for verification → the line stays folded and ends "· After photo needed"; open it → one "No photos yet" line with the add controls → AC-13
- [ ] Status card: no heading; badge, priority and ⋮ on the first row; the due line under it (no overdue text on a Closed ticket); the reason under the primary button → AC-17
- [ ] 375px: the status line carries priority and the due line; the bottom bar still shows the reason → AC-13, AC-18
- [ ] Details: no Plate, Model, Priority or Due; Vehicle and Record headings with a divider; Closed only once set → AC-16
- [ ] Issue title semibold and a step larger from 768px; step rows 36px from 768px and 44px on phones → AC-2, AC-9
- [ ] Closed row with a saved resolution shows only What fixed it and hours on line 2 → AC-2
- [ ] Both ⋮ menus: Enter or Space opens, arrows move, Escape closes with focus back on the trigger → AC-20
- [ ] axe at 375px and 1280px with a row menu open and closed → AC-20

## Second refinements (2026-11-07, task 6)
_These replace the older photos line and summary steps above where they disagree._
- [ ] A Photos card sits right after Issues and before AI; there is no photos line inside Issues and no fold → AC-13, AC-14
- [ ] Before is always left (top on phones) and After right (below); start work on a ticket and the columns do not swap → AC-13
- [ ] Assigned ticket: "+ Add before photo" tile only in Before; In progress ticket: "+ Add after photo" only in After; the other group says "None yet" when empty → AC-13
- [ ] Click the tile → the file picker opens in the same click; on a phone it offers camera or gallery; the photo lands in the tile's group → AC-13
- [ ] A group with 5 photos shows 2 thumbnails and "+3 more"; clicking it opens the viewer on that group's third photo; closing returns focus to the tile → AC-13
- [ ] Fill After to its limit (count queued uploads) → the tile becomes "After photos full (10 of 10)" → AC-13
- [ ] Blocked Send for verification with no after photo → "After photo needed" at the card's top right; the Status card reason link scrolls to the card (not under the sticky header) and focuses the tile → AC-13, AC-17
- [ ] Closed ticket, or a viewer who can't add: no tile, no limit text; no card at all when there are no photos → AC-13
- [ ] Reload the page: skeleton squares only on the first load; the 3 second refresh never flashes skeletons → AC-13
- [ ] The summary line reads "0 of 2 issues done, 2 of 6 steps ticked"; only Hide done steps on its right; no Expand all or Collapse all → AC-6
- [ ] No `·` anywhere on the ticket page, its dialogs or the photo viewer: row line 2 ("Cooling   Known fix: …   Safety"), title metadata, due line with overdue on its own line, account "Corporate, …", step tooltip "Ticked by … on …", Documents rows, AI run line, viewer caption on three lines → AC-2, AC-11, AC-16, AC-17, AC-19
- [ ] Hover the status badge, priority badge and both ⋮ buttons → "Ticket status", "Priority", "More actions" → AC-7, AC-17
- [ ] 375px order: status line, Notes, Issues, Photos, AI, Costs, People, Details, Activity → AC-18
- [ ] `npm run test` includes the check that no `·` is left in the ticket page code → AC-19
- [ ] axe at 375px and 1280px with the Photos card full, empty and loading → AC-20

## Task 6 build notes (2026-11-07, /develop)
_Added by the build. The side by side rule changed during the build (your call): the groups sit side by side only when the card is wide enough, so the "Before always left" step above holds only on a wide card._
- [ ] Card width rule: at 1280px with the app sidebar open, Before and After stack (Before on top); at about 1400px and wider, or 1280px with the sidebar collapsed, they sit side by side; a group's 4 slots never wrap at any width, 375px included → AC-13 (container query `@2xl`, 672px inside the card)
- [ ] On a mouse device, drag files over the card → the whole card shows the ring; drop → they upload into the tile's group; a full group shows no ring and no drop hint → AC-13
- [ ] On a pointer device the card says "Or drop {before|after} photos anywhere on this card"; on a phone that line is gone → AC-13
- [ ] Viewer walk: open the first Before thumbnail and press the right arrow through every photo → Before then After, also on an In progress ticket (the order no longer flips once work starts) → AC-13, value sourcing: Photos card
- [ ] Group with exactly 3 photos → 3 thumbnails, no "+N more"; with 4 → 2 thumbnails and "+2 more"; Before has 4 and After has 4, "+2 more" in After opens on After's third photo (index 6 in the walk) → AC-13, value sourcing: "+N more" and viewer index
- [ ] Tile label tracks `workStartedAt`: press Start work on an Assigned ticket → the tile moves from Before to After without a reload → AC-13, value sourcing: which group gets the tile
- [ ] Blocked link with After full → focus lands on the card's "Photos" heading, not a tile → AC-13
- [ ] Block the attachments call (devtools) and reload → the card shows the error with Try again; Try again reloads the file list only, the issues stay as they were → AC-13
- [ ] A viewer who can't add sees no "2 of 5" counts on the group headings → AC-13
- [ ] Row line 2 at 375px with a long known fix name → the name ends in an ellipsis, while the category, the Draft or Inactive badge and "Safety" stay whole → AC-2
- [ ] AI run line reads "Ran 2 hours ago with {model}, high confidence" → AC-19
