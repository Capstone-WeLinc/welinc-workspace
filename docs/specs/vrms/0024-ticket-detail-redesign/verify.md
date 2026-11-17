# Verify: Ticket detail redesign · spec 0024 · updated 2026-11-06
_Steps derived from spec 0024 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

_Cleaned up 2026-11-08: 19 open steps were removed because a later section replaces them (Hide done steps, Expand all, the photos line, the single drop overlay, the old 375px order and Details steps). The earlier file is kept in git history. Two steps got current wording (the summary has no dot, the stored view is `{ open }`)._

## UI / manual
- [ ] Open an In progress ticket with 5 issues where issue 1 is Done → issue 2 is open, the rest closed; the summary reads "1 of 5 issues done, t of s steps ticked" → AC-4, AC-6
- [x] Tick the last step of the open issue → its row turns "Done" with a full green bar at once and stays open; the summary updates → AC-3, AC-5
- [x] Tick a step, then fold the row before the save returns; make the save fail (offline) → the step goes back when you reopen, with the error toast → AC-3
- [x] A ticket with 3 issues or fewer, In progress → every row starts open → AC-4
- [x] Open a For verification ticket as the verifier → every row closed; each line 2 shows What fixed it (or "Followed the known fix") and the hours as "2.5 h" → AC-2, AC-4
- [x] Return a ticket to the mechanic → every issue with notes shows the gold "Returned" pill with no bar → AC-3
- [ ] Issue with no steps and no known fix → "No checklist", line 2 "No known fix"; inside: the link picker and "Suggest a known fix" → AC-2, AC-3, AC-10
- [ ] Issue whose known fix has safety notes → closed row says "Safety"; open row shows one amber line above the checklist, with More only when it is cut off → AC-2, AC-8
- [ ] A known fix in Draft or Inactive → its status badge shows on line 2 and inside the row; with the knowledge module off the name is plain text → AC-2, AC-10
- [x] Open two rows, reload → the same two are open; open the ticket in a new tab → the default rule applies → AC-5
- [x] Visit `/repairs/<id>#issue-3` → issue 3 opens on top of what was open and scrolls into view below the header; `#issue-99` does nothing → AC-4
- [x] Wait through several 3 second refreshes → no row opens or closes by itself; add an issue from another tab → it appears closed → AC-5
- [ ] Edit steps dialog subtitle and the For verification dialog show issue text without "[System]" → AC-12
- [x] AI card closed reads "AI suggests {category}, High priority" or "No AI diagnosis yet" with Run; make the latest diagnosis fail → one line with Retry; module off → no card → AC-14
- [ ] Activity shows the 5 newest; Show all replaces them with 50 and pages on; no audit.view → no card → AC-15
- [ ] Notes card is in the sidebar with a 3 line preview and Show more only when cut off; Vehicle and driver sits in Details with its Edit → AC-16
- [ ] At 1280px the sidebar sits on the right; resize across 1024px → open rows and pending ticks stay → AC-18
- [ ] Keyboard: Tab to a row header, Enter and Space fold it, focus stays put; reduced motion → no fold animation → AC-1, AC-20
- [ ] axe at 375px and 1280px, rows open and closed, the loading skeleton and the empty issues state → no violations on the page (the dev only Demo data pill is excluded) → AC-19, AC-20

## Value sourcing
- [x] Issue text with a leading `[Engine] ` → shown without it everywhere → `stripSystem`
- [x] Category shows once, from `categoryName` → `issue.categoryName`
- [ ] Safety notes of only spaces → no "Safety" word → `safetyNotes` trimmed
- [x] Progress "{x} of {y}" counts a tick made on the page before the refresh → `mergedSteps` with `useTickOverrides`
- [x] Saved notes with `resolvedAt` cleared → Returned; with `resolvedAt` set → Done → `hasSavedResolution`, `resolvedAt`
- [ ] Line 2 note empty and `followedKnownFix` true → "Followed the known fix"; `hoursSpent` 0.25 → "0.25 h" → `resolutionNote`, `followedKnownFix`, `hoursSpent`
- [x] Needs what fixed it shows only In progress, never in For verification → `ticket.status`
- [ ] Open rule changes with status, never with role (same ticket as Admin and as Mechanic) → `initialOpen`
- [ ] Photo counts match the strip's Before and After groups, before and after Start work → `photoGroups(attachments, workStartedAt)`
- [ ] Blocked link targets the photo the move waits for, and not while photos upload → `ticketActions().blockedBy`
- [ ] Title model left out when `vehicleModel` is empty; first issue follows `createdAt` then `id` → `ticket.issues[0]`
- [x] AI line priority "CRITICAL" reads "Critical" → `predictedPriority` in sentence case
- [x] Notes card shows the cancellation reason on a Cancelled ticket → `ticket.cancellationReason`, `ticket.remarks`
- [x] Activity first request carries `limit=5`, Show all `limit=50` → `getAuditEvents`
- [x] sessionStorage holds `vrms.ticket.<id>.view` as `{ open }`; a 21st ticket drops the oldest; private mode still works from memory → `useTicketView`

## Commands
- [x] `cd welinc-web-vrms && npm run lint && npm run typecheck && npm run build && npm run test` → all green (430 tests) → AC-19
- [x] `cd welinc-backend-vrms && npm run build && npm test -- ticket-knowledge` → the issue order test passes → AC-4

## Acceptance-criteria coverage
- AC-1 keyboard step · AC-2 verifier, no known fix, safety, Draft steps · AC-3 tick, Returned, offline steps · AC-4 5 issue, 3 issue, verifier, hash steps · AC-5 reload, refresh, Hide done steps · AC-6 summary, Expand all · AC-7 to AC-10 open row steps · AC-11, AC-12 title and dialog steps · AC-13 photos and blocked link · AC-14 AI · AC-15 Activity · AC-16 Notes and Details · AC-17 ⋮ menu · AC-18 375px · the fifth refinements section covers AC-7, AC-13, AC-17, AC-18, AC-19 and AC-20 again and 1280px · AC-19, AC-20 axe, keyboard, commands

## Refinements (build task 5) · added 2026-11-06
_These replace the older steps above where they disagree._
- [ ] Open an issue → safety, checklist, one "Edit steps"; the row ⋮ ("More actions for issue N") holds Edit issue, Remove issue (not with one issue), Change known fix (only when relinking is allowed), Open known fix (only with the knowledge module on) → AC-7, AC-10
- [x] No separate known fix line in an open row; an issue with no known fix still shows the picker and Suggest a known fix → AC-10
- [x] Issue title semibold and a step larger from 768px; step rows 36px from 768px and 44px on phones → AC-2, AC-9
- [x] Closed row with a saved resolution shows only What fixed it and hours on line 2 → AC-2
- [x] Both ⋮ menus: Enter or Space opens, arrows move, Escape closes with focus back on the trigger → AC-20
- [ ] axe at 375px and 1280px with a row menu open and closed → AC-20

## Second refinements (2026-11-07, task 6)
_These replace the older photos line and summary steps above where they disagree._
- [x] A Photos card sits right after Issues and before AI; there is no photos line inside Issues and no fold → AC-13, AC-14
- [x] Before is always left (top on phones) and After right (below); start work on a ticket and the columns do not swap → AC-13
- [ ] Click the tile → the file picker opens in the same click; on a phone it offers camera or gallery; the photo lands in the tile's group → AC-13
- [ ] A group with 5 photos shows 2 thumbnails and "+3 more"; clicking it opens the viewer on that group's third photo; closing returns focus to the tile → AC-13
- [x] Fill After to its limit (count queued uploads) → the tile becomes "After photos full (10 of 10)" → AC-13
- [x] Blocked Send for verification with no after photo → "After photo needed" at the card's top right; the Status card reason link scrolls to the card (not under the sticky header) and focuses the tile → AC-13, AC-17
- [x] Closed ticket, or a viewer who can't add: no tile, no limit text; no card at all when there are no photos → AC-13
- [x] Reload the page: skeleton squares only on the first load; the 3 second refresh never flashes skeletons → AC-13
- [ ] No `·` anywhere on the ticket page, its dialogs or the photo viewer: row line 2 ("Cooling   Known fix: …   Safety"), title metadata, due line with overdue on its own line, account "Corporate, …", step tooltip "Ticked by … on …", Documents rows, AI run line, viewer caption on three lines → AC-2, AC-11, AC-16, AC-17, AC-19
- [ ] 375px order: status line, Notes, Issues, Photos, AI, Costs, People, Details, Activity → AC-18
- [ ] `npm run test` includes the check that no `·` is left in the ticket page code → AC-19
- [ ] axe at 375px and 1280px with the Photos card full, empty and loading → AC-20

## Task 6 build notes (2026-11-07, /develop)
_Added by the build. The side by side rule changed during the build (your call): the groups sit side by side only when the card is wide enough, so the "Before always left" step above holds only on a wide card._
- [ ] Card width rule: at 1280px with the app sidebar open, Before and After stack (Before on top); at about 1400px and wider, or 1280px with the sidebar collapsed, they sit side by side; a group's 4 slots never wrap at any width, 375px included → AC-13 (container query `@2xl`, 672px inside the card)
- [ ] Viewer walk: open the first Before thumbnail and press the right arrow through every photo → Before then After, also on an In progress ticket (the order no longer flips once work starts) → AC-13, value sourcing: Photos card
- [ ] Group with exactly 3 photos → 3 thumbnails, no "+N more"; with 4 → 2 thumbnails and "+2 more"; Before has 4 and After has 4, "+2 more" in After opens on After's third photo (index 6 in the walk) → AC-13, value sourcing: "+N more" and viewer index
- [x] Tile label tracks `workStartedAt`: press Start work on an Assigned ticket → the tile moves from Before to After without a reload → AC-13, value sourcing: which group gets the tile
- [ ] Blocked link with After full → focus lands on the card's "Photos" heading, not a tile → AC-13
- [ ] Block the attachments call (devtools) and reload → the card shows the error with Try again; Try again reloads the file list only, the issues stay as they were → AC-13
- [ ] A viewer who can't add sees no "2 of 5" counts on the group headings → AC-13
- [x] Row line 2 at 375px with a long known fix name → the name ends in an ellipsis, while the category, the Draft or Inactive badge and "Safety" stay whole → AC-2
- [x] AI run line reads "Ran 2 hours ago with {model}, high confidence" → AC-19

## Third refinements (2026-11-07, task 7)
_These replace the older Hide done steps, drop hint, Activity, due line and title steps above where they disagree._
- [ ] No Hide done steps switch anywhere; the summary line has no controls; done steps show dimmed in every open row → AC-6, AC-9
- [x] A stored view from before the update (`{ open, hideDone }`) loads with its open rows kept and no error; the next write stores `{ open }` only → AC-5
- [ ] Drag selected text or a link over the card → no overlay → AC-13
- [x] Hover or focus the target group's add tile → "Add after photo, or drop files on this card"; its accessible name stays "Add after photo" → AC-13
- [x] Activity starts closed with the newest entry and its time on one line (no ticket ID); open → 5 entries grouped by day and no new network request; Show all → 50 → AC-15
- [ ] Header: the line under the title shows the ticket ID only, no garage; the garage still shows in Details under Record → AC-11, AC-16
- [ ] axe at 375px and 1280px with Activity closed and open, and with the drop overlay showing → AC-20

## Task 7 build notes (2026-11-07, /develop)
_Added by the build: two calls made in the build, so you can disagree._
- [x] Activity's closed line reads "{actor} {verb} this ticket, {day}, {time}" (for example "Victor Ramos updated the costs of this ticket, Wed, Nov 4, 2:49 PM"). The audit sentence could not sit inside the fold button as it was (its name is a focusable tooltip, and dropping the ticket ID broke "updated the costs of"), so the wording moved into one table in `auditEvents.ts` (`eventPhrase`, `eventText`) that both the Audit log sentence and this line use → AC-15
- [ ] The Audit logs page still reads every event the same as before the table move (spot check created, status change, costs, step ticked, an event with no actor) → AC-15

## Fourth refinements (2026-11-07, task 8)
_These replace the single drop overlay, the borderless Return and the open row's line 2 steps above where they disagree._
- [ ] A ticket with only one action shows it full width → AC-17
- [ ] Issue row with no steps: the `⋮` sits on the header line next to the chevron, not on its own line; it opens with Enter and does not fold the row → AC-7, AC-20
- [ ] Open a resolved row: line 2 shows the category and known fix; below, "What fixed it" with "3.5 h" on the right and the note under it; an issue with no hours shows no hours and no dash → AC-2, AC-7
- [x] "Aircon not cooling: Aircon not cooling, blows warm air." shows as "Aircon not cooling: blows warm air." in the row and the title; the Edit issue dialog still shows the stored text → AC-12
- [ ] Rows with No checklist, Not started, 2 of 5 and Done: the state words line up on the right edge → AC-3
- [ ] Drag an image file over the Photos card on an In progress ticket: two zones (Before, After) with counts; the zone under the pointer rings; drop on Before → the photo lands in Before with the "Added after work started" badge; drop on After → After → AC-13, AC-21, AC-22
- [x] The uploader removes that late Before photo with no 403; a Before photo from before Start work still answers 403 for a mechanic → AC-22
- [x] A full group's zone reads "Before photos full (5 of 5)" and a drop there adds nothing → AC-13
- [x] Drag an After thumbnail onto Before with the mouse → it moves, the audit row says "moved a photo"; a short click on a thumbnail still opens the viewer → AC-13
- [x] Keyboard: focus a thumbnail, Space to pick up, arrow to the other group, Space to drop → moved and announced; Escape cancels → AC-13
- [ ] A thumbnail without `canMove` (someone else's, or protected) does not drag → AC-13
- [x] Hover a marked thumbnail → its tooltip lists the marks; the viewer caption shows them on their own lines → AC-13
- [x] `cd welinc-backend-vrms && npm run build && npm test -- attachments` → green, including the `group` and protection cases → AC-21, AC-22
- [ ] axe at 375px and 1280px with the drop zones showing and a thumbnail drag in progress → AC-20

## Task 8 build notes (2026-11-07, /develop)
_Added by the build: calls made in the build, so you can disagree._
- [ ] Details card, Vehicle group: Plate and Model show side by side first (Model "—" when unset), even though the title has them (AC-16, updated 2026-11-07) → AC-16, value sourcing: Details card
- [ ] Keyboard drag: focus a movable thumbnail, Space picks it up, any arrow key jumps it over the other group (a second arrow takes it back), Space drops it, Escape cancels. Enter still opens the viewer, and the Space that drops never opens it → AC-13
- [ ] After a drag move the moved thumbnail gets focus; if it lands behind "+N more", focus stays where it was → AC-13
- [x] A file drop on the gap between the two zones adds nothing → AC-13, AC-21
- [x] AC-12 whole word rule (example settled 2026-11-07): "Aircon: Aircon cooling weak" reads "Aircon: cooling weak"; "Air: Aircon cooling weak" stays unchanged → AC-12
- [ ] A row with no menu keeps an empty space where the `⋮` would be, so its state words line up with rows that have one → AC-3
- [ ] Open a resolved row that has both a note and "followed the known fix": only the note shows under What fixed it (the extra "Followed the known fix" line is gone, as AC-7 words it) → AC-7

## Fifth refinements (2026-11-07, task 9)
_These replace the Status card, due line, `⋮` menu and pill steps above where they disagree._
- [ ] Status card on an overdue For verification ticket: rows Status, Priority and Due, the `⋮` at the top right; Due reads "Nov 2" with "4 days overdue" in red under it, no icon, nothing trailing to the right of the date → AC-17
- [ ] Due later reads the date with "in 2 days" in muted text under it; within the same 24 hours it reads "Today"; a few hours late reads "Today" with "Past due" in red; a Closed ticket shows the date alone → AC-17
- [ ] No priority means no Priority row; no due date means no Due row → AC-17
- [x] Status card `⋮`: Copy ticket link, a divider, Cancel ticket in red, each with an icon. Copy shows "Ticket link copied" and the clipboard holds the page address; a read only view, or a ticket with no cancel action, shows only Copy ticket link and no divider → AC-17
- [ ] After a menu closes (Escape, or after choosing Copy) the "More actions" tooltip stays hidden until the pointer moves over the button again, or focus leaves it and comes back; same on an issue row's `⋮` → AC-7, AC-20
- [ ] Issue row menu: icons on every item, a divider before Remove issue only when another item shows, Open known fix in normal text colour → AC-7
- [ ] 375px: the slim status line shows the same Status, Priority and Due rows, and every `⋮` is a 44px target → AC-18
- [ ] Pills: the status, priority, lock and mechanic badges, Returned and Unlocked read in sentence case with a thin ring; High is a soft gold tint, Critical stays solid red. Same look on the repair list, dashboard, Users page, History and the top bar role pill → AC-19
- [ ] Started ticket, Before empty, as someone who can add: Before shows a dashed add tile with the tooltip "Add before photo (work already started)" → AC-13
- [x] Tap Before's tile: the dialog "Work has already started" with a soft amber icon, Cancel and "Add anyway". Cancel and Escape open no picker and focus returns to the tile; "Add anyway" opens the picker, the photo lands in Before with the "Added after work started" badge, and the next tap on the same page view opens the picker at once; a reload asks again → AC-13, AC-21, AC-22, AC-20
- [ ] Before work starts: Before has the tile and After shows "None yet" with no tile; a viewer who can't add sees "None yet" in a group with no photos → AC-13
- [ ] Blocked Send for verification: the reason link focuses After's tile when an After photo is needed, and Before's when a Before photo is needed → AC-13
- [ ] axe at 375px and 1280px with the warning dialog open, and with the Status card menu open → AC-20
- [x] `dueValue` unit tests pass (overdue, today a few hours late and not yet late, later, next year, Closed, no due date) → AC-17
- [ ] Hover a status or priority pill: no tooltip (the row labels say what they are); hover and focus on both `⋮` buttons still show "More actions" → AC-7, AC-17
- [ ] On a real iPhone (Safari): tap Before's tile on a started ticket, then "Add anyway" → the picker opens. If it does not, the notice moves to a plain line under the tile (AC-13) → AC-13
- [ ] Open the app on plain http outside localhost (or block clipboard access), then choose Copy ticket link → the error toast "Couldn’t copy the link. Copy it from the address bar.", and no console error → AC-17
- [x] A file dropped on the Before zone of a started ticket, and a thumbnail dragged into Before → both skip the notice, and the photo shows the "Added after work started" badge → AC-13, AC-22
- [ ] Due "Today" within 24 hours of the last fetch in either direction; a Closed ticket never reads "Today" → AC-17


### Task 9 follow-up (2026-11-07, `welinc-web-vrms` `2d34f9b`)
- [ ] Status card `⋮`: Copy ticket link shows the copy icon (two stacked squares), not a chain link → AC-17
- [ ] A ticket due tomorrow reads its date with "in 1 day" under it; one due yesterday reads "1 day overdue" in red (the `dueValue` singular test covers both) → AC-17

## Sixth refinements (2026-11-07, task 10)
_Replace the phone progress column of the first verify run. Found by `/check verify` at 375px: the title column was about 62px and line 2 collapsed._
- [x] 375px, a 3 issue ticket with a long first issue: the title column is about 170px wide, a closed row's title shows at most 2 lines with an ellipsis, and an open row shows the whole title in a handful of lines, not one word per line → AC-2
- [x] 375px, closed row: line 2 starts with the progress ("3 of 4", "Not started", "Done" in green, "Returned" in the gold pill, or "No checklist"), then the category, then "Known fix: {name}" or "No known fix", then Safety when set; no part is cut to nothing, and a part that does not fit moves to a second line whole → AC-2, AC-3
- [x] 375px: the 4px bar is a strip under line 2 across the text column (hidden for Returned and No checklist); the right edge of the row holds only the `⋮` and the chevron, both 44px → AC-3, AC-1
- [x] 375px open row: the same progress and bar still show on the row header → AC-3
- [x] A resolved closed row at 375px: progress first, then "What fixed it" and the hours → AC-2, AC-3
- [x] 767px and 768px: below 768px the progress is on line 2; from 768px it is back in the fixed right column with the state words lined up and the bar the column's full width → AC-3
- [ ] 1280px: the rows look exactly as before this task; the progress text is read once by a screen reader (check the row button's accessible name has the progress once) → AC-3, AC-20
- [x] axe at 375px and 1280px again, rows open and closed → AC-20
- [x] 375px with a Draft or Inactive known fix, a long note, and a long unbroken category word: each ends in an ellipsis on its own line or stays whole, nothing is clipped without one, the status badge is never cut, and nothing scrolls sideways → AC-2
- [x] 375px with a Returned row: the pill sits first on line 2, then the note; the row is a little taller than a plain one and still reads cleanly → AC-2, AC-3
- [x] Playwright snapshot of a row at 375px: the button's name reads in order with spaces between the parts ("Issue 1: {title}", then the progress, then the category), and the progress appears once, not twice → AC-3, AC-20
- [ ] 1280px: an open row still shows its whole title on every line, and a closed row cuts it to 1 line → AC-2
