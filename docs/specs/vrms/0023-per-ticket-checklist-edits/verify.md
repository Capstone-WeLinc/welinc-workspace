# Verify: per ticket checklist edits · spec 0023 · 2026-11-06
_Steps derived from spec 0023 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## UI / manual
- [x] As the assigned Mechanic on an Assigned ticket with a linked known fix, open Edit steps, reword step 2, move step 4 up to the top, add a step, save → the checklist shows the new order, "Edited" on step 2's new place, "Added" on the new step; the Activity shows one reworded, one moved and one added row, 1 ms apart → AC-4, AC-6, AC-8, AC-10, AC-13
- [x] Same ticket: the ticket's "updated" time did not move; an Admin edit opened before the save still saves → AC-6
- [x] Open Edit steps and save with nothing changed → no new Activity rows → AC-11
- [x] On an In progress ticket, tick steps 1 and 3; open Edit steps, remove step 1, reword step 3, save → the prompt says "1 ticked step will be removed. 1 ticked step will lose its tick."; after save step 3 is unticked, and the removed row shows who ticked step 1 and when → AC-8, AC-9, AC-10
- [ ] Open Edit steps in two tabs, save in one, save in the other → 409, the dialog closes, the ticket reloads and the stale toast shows → AC-6, AC-17
- [ ] Open Edit steps, tick a step in a second tab, then save the dialog without touching that step → the tick is still there → AC-8, AC-15
- [ ] Open Edit steps, then in a second tab relink the known fix → saving the dialog gives 409 → AC-6, AC-14
- [ ] Open Edit steps on an issue, then in a second tab dismiss a knowledge suggestion on it (or move the ticket back to In progress) → the dialog still saves → AC-6
- [ ] Open Edit steps on an In progress ticket, send the ticket for verification in a second tab, then save → 400 status message, nothing saved → AC-3
- [ ] On a linked issue, remove every step and save → the link stays, the block shows "Add steps" → AC-5
- [ ] On an issue with no known fix and no steps, use Add steps to write three steps → saved as Added; then link a known fix → the prompt counts 3 steps added on this ticket; confirm → the known fix steps replace them → AC-4, AC-14
- [ ] Try 21 steps, a 2 character step, and a step of 301 characters → field messages and Save refused; Add step is disabled at 20 → AC-5
- [ ] As the Chief on a ticket they are not assigned to → Edit steps shows and saves; as a Mechanic not assigned to it → no button; turn the key off for Mechanic in the matrix → the assigned mechanic loses the button → AC-1, AC-2
- [ ] Switch the knowledge module off → Edit steps still shows and saves → AC-16
- [ ] On a For verification ticket → no Edit steps button → AC-2
- [ ] Rows show handle, number, a borderless field (border on hover or focus), a tick mark on ticked steps and Remove; no Move up or Move down buttons → AC-4
- [ ] Drag step 6 above step 5 with the mouse, save → the Activity shows one moved row, "Step 6 → step 5"; swap steps 1 and 2 → "Step 2 → step 1" → AC-4a, AC-10
- [ ] At 375px, touch drag a step by its handle → it reorders, with a preview under the finger; swipe on the text → the sheet scrolls, no drag starts → AC-4a
- [ ] By keyboard, Tab to a handle, Space, Down, Down, Space → the step moved two places, focus stays on its handle; Space, Down, Escape → back in place and the sheet is still open; a screen reader hears the instructions and each sentence → AC-4a, AC-18
- [ ] At 375px with 20 steps, drag the last step to the top → the sheet scrolls while dragging; the preview shows the number and text at the row's width → AC-4a
- [ ] In step 2 press Enter → an empty step 3 appears with the cursor in it; Enter again → nothing; Backspace → it is gone and the cursor is at the end of step 2; hold Backspace in step 2 → its text is deleted but the step stays; at 20 rows Enter does nothing; type 301 characters → the field stops at 300 → AC-4b
- [ ] With a Japanese or Chinese input method, type in a step and press Enter to commit the text → no new step is added → AC-4b
- [ ] Start a mouse drag on a handle, press Escape mid drag → the step goes back to its place, the sheet stays open, focus is on that handle → AC-4a, AC-18
- [ ] Approve a knowledge suggestion that links an issue which already has its own steps → its steps stay, an open Edit steps dialog on it still saves; one that links an issue with no steps → the entry's steps appear → AC-14
- [ ] At 375px the dialog is a bottom sheet; remove a step by keyboard → focus lands on the row that took its place; remove the last one → focus on Add step; axe clean at 375px and 1280px with the dialog and the prompt open → AC-4, AC-18

## Commands
- [x] `PUT /vrms/repairs/:id/issues/:issueId/steps` on a Closed ticket → 400 with the status message → AC-3
- [x] Same call as a Mechanic not assigned → 403; with an issue id from another ticket → 404 → AC-3
- [x] Same call with a step id from another issue, or one id twice → 400 → AC-7
- [x] Same call with an old `checklistVersion` → 409 `STALE_CHECKLIST` → AC-6
- [x] Same call with a 2 character step at index 3 → 400 with `fieldErrors: [{ index: 3, … }]` → AC-5
- [x] Same call with "  Torque   the bolts " for a step stored as "Torque the bolts" → no change, no row → AC-8, AC-11
- [ ] `GET /vrms/repairs/:id` and the repair list → issues carry `checklistVersion`, steps carry `origin` and `editedAt`, `can.editChecklist` is set → AC-2, AC-12
- [ ] `GET /vrms/repairs/audit-logs/catalog` → `STEP_ADDED`, `STEP_REMOVED`, `STEP_EDITED`, `STEP_MOVED` under `CHECKLIST` → AC-10
- [ ] Move step 5 of 5 to the top and save → exactly one `STEP_MOVED` row; swap steps 1 and 2 → one row; reword and move one step → a `STEP_EDITED` and a `STEP_MOVED` row → AC-10
- [ ] Backend and web lint, typecheck, build and tests green → AC-18
