# Verify: proof of completion · spec 0018 · updated 2026-11-02
_Steps derived from spec 0018 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Restart `welinc_vrms_backend` first (the container misses Windows edits).

## Milestone 2: photo rules on the moves

### UI / manual
- [ ] As a mechanic, open an Assigned ticket with no Before photo → Start work is disabled and reads "Add a before photo first." in the status card and (below 1024px) the bottom bar → AC-4, AC-19
- [ ] Add a Before photo → once it lands, Start work turns on without a page reload → AC-4 (ticket reload on file change)
- [ ] Pick a photo on an Assigned ticket and watch the queue → while it is waiting or uploading, Start work reads "Photos still uploading." → AC-20
- [ ] On an In progress ticket with only Before photos → Send for verification is disabled with "Add an after photo first." → AC-5
- [ ] Remove the last After photo on a For verification ticket → the status stays For verification (no rule runs on remove) → AC-7
- [ ] As Admin, turn on "Require an after photo to close" in Settings → Tickets → a For verification ticket with no After photo shows Verify and close disabled with "Add an after photo before closing." → AC-6, AC-17
- [ ] With "Require costs before closing" also on and no costs → the photo reason shows first (fixed outside the dialog) → AC-7 (web order)
- [ ] Settings hub shows the three new switches in the Tickets group (defaults: on, on, off), and a change appears in the settings log → AC-17
- [ ] Open the Start work dialog, then remove the Before photo in another tab and confirm → the dialog closes, a toast says "Add a before photo first.", and the ticket reloads → AC-4 (race handling)

### Commands
- [ ] `PATCH /vrms/repairs/:id/status` to `IN_PROGRESS` on a ticket with no live Before photo → 400 `{ code: "BEFORE_PHOTO_REQUIRED" }`, status unchanged, no audit row → AC-4, AC-7
- [ ] Same with `tickets.require_before_photo_to_start` off → 200 → AC-4
- [ ] `PATCH …/status` to `FOR_VERIFICATION` with a missing "What fixed it" and no After photo → the resolutions 400 answers, not the photo one → AC-7
- [ ] `PATCH …/status` to `CLOSED` with costs required, no costs and the close switch on → 422 `COSTS_REQUIRED` first → AC-7
- [ ] Soft deleted photos don't count: remove the only After photo, then send → 400 `AFTER_PHOTO_REQUIRED` → AC-7 (live rows only)
- [ ] `GET /vrms/repairs/:id` → each `moves[]` entry has `blockedBy` (`beforePhoto`, `afterPhoto` or null) matching the server check → AC-4 to AC-6
- [ ] Cancel (M14) and the mechanic release (M2) on a ticket with no photos → both succeed → AC-8
- [ ] An `ASSIGNED` ticket created before release with no Before photo → Start work is blocked like any other → AC-8
- [ ] `npm run test` in welinc-backend-vrms (photo-rules.spec, repairs.status.spec "photo rules on the moves") → green → AC-4 to AC-8
- [ ] `npx vitest run` in welinc-web-vrms (nextAction.test, photoUpload.test) → green → AC-4 to AC-6, AC-20

### Value sourcing rows (this milestone)
- [ ] status move / `moves`, rule on or off: flip each `tickets.require_*` switch and recheck `blockedBy` and the 400 without a restart → per request settings read
- [ ] `moves[].blockedBy`, need unmet: same ticket, same switches → `blockedBy` and the status endpoint agree in every case (one shared `photoNeedUnmet()`)
- [ ] status move, photo present: count only `deletedAt` null rows of the needed kind (a Before photo never satisfies Send for verification)
- [ ] web next action, reason text: `blockedBy` maps to the AC-4 to AC-6 strings; "Photos still uploading." comes from this ticket's queue only

## Acceptance-criteria coverage (milestone 2)
- AC-4: manual 1, 2, 9 · commands 1, 2, 6
- AC-5: manual 4 · commands 6
- AC-6: manual 6 · commands 6
- AC-7: manual 5, 7 · commands 3, 4, 5
- AC-8: commands 7, 8
- AC-17: manual 6, 8
- AC-20: manual 3

## Milestone 3: move and protect

### UI / manual
- [ ] As the mechanic who uploaded it, open your own After photo in the viewer → a "Move to Before" button sits in the toolbar, reachable with Tab and read by its text → AC-9, AC-19
- [ ] Press it → the toast says "Photo moved to Before.", the photo shows in the Before group, the viewer stays on it, and the ticket's Start work state updates if that was the missing photo → AC-9, AC-16
- [ ] As that mechanic, after Start work, open your own Before photo → no Move button and no Remove button on the thumbnail → AC-10, AC-11
- [ ] As a Chief Mechanic on the same ticket → the Before photo shows both Move to After and Remove → AC-10
- [ ] As Admin, turn off "Protect before photos once work starts" → the mechanic's own Before photo offers Move and Remove again → AC-10, AC-17
- [ ] Before work starts, the mechanic's own Before photo can be moved and removed → AC-10
- [ ] Someone else's photo never offers Move to a mechanic → AC-9, AC-11
- [ ] With the Before group full, move an After photo to Before → a toast says the before photo limit is reached, and the photo stays in After → AC-3, AC-9
- [ ] On a Closed ticket, no photo offers Move → AC-9, AC-11
- [ ] Ticket Activity and the Audit log show "{name} moved a photo on REP-…" with "Moved a photo from After to Before" and the file name → AC-18
- [ ] Added and removed photo events read "Before photo: …" or "After photo: …", including rows written before this change ("Vehicle photo", "Proof of completion") → AC-18

### Commands
- [ ] `PATCH /vrms/repairs/:id/attachments/:attachmentId` `{ "kind": "VEHICLE_PHOTO" }` on your own After photo → 200 with the view, `kind` VEHICLE_PHOTO, and one `ATTACHMENT_MOVED` audit row whose `changes` hold `kind` PROOF → VEHICLE_PHOTO → AC-9, AC-18
- [ ] Same call again → 200, no second audit row → AC-9
- [ ] `{ "kind": "RECEIPT" }`, or a move of a receipt → 400 `NOT_A_PHOTO`; an id that is not on the ticket → 404 first → AC-9
- [ ] Someone else's photo without `ticket.files.remove_any` → 403 `NOT_YOUR_FILE` ("You can only move photos you added yourself.") → AC-9
- [ ] Your own Before photo to PROOF after Start work → 403 `BEFORE_PHOTO_PROTECTED`; `DELETE` on it → the same 403; as Chief → 200 and 204 → AC-10
- [ ] Release the ticket back to Open after Start work → `workStartedAt` stays, Before photos stay protected → AC-10 (release row)
- [ ] Move on a Closed ticket → 409 `TICKET_FINISHED` → AC-9
- [ ] Move into a full group → 409 `PHOTO_LIMIT_REACHED` with that group's limit → AC-3, AC-9
- [ ] `GET …/attachments` → each row has `canRemove` and `canMove` matching the rules above for the caller → AC-11
- [ ] `npm run test` in welinc-backend-vrms (attachments.service.spec move and Before protection, attachment-rules.spec canMove) → green → AC-9 to AC-11
- [ ] `npx vitest run` in welinc-web-vrms (auditEvents.test) → green → AC-18

### Value sourcing rows (this milestone)
- [ ] list, `canMove` and `canRemove`: change each input (caller id, `ticket.files.add`, `ticket.files.remove_any`, the protect switch, work started) and confirm both flags follow
- [ ] audit timeline, move text: the line comes from the `kind` change's before and after, labelled Before and After in the web

## Acceptance-criteria coverage (milestone 3)
- AC-9: manual 1, 2, 7, 8, 9 · commands 1 to 4, 7, 8
- AC-10: manual 3 to 6 · commands 5, 6
- AC-11: manual 3, 7, 9 · commands 9
- AC-18: manual 10, 11 · commands 1, 11

## Milestone 4: evidence signals

### UI / manual
- [ ] Upload a phone JPEG that carries EXIF to an In progress ticket → `attachments.taken_at` equals the photo's capture time in UTC → AC-12
- [ ] Upload a screenshot (no EXIF), then POST with `takenAt=garbage` and with `takenAt=2099-01-01` → each upload succeeds with `taken_at` null → AC-12
- [ ] As Chief, open a ticket with an After photo whose `taken_at` is 10 minutes before `work_started_at` → the thumbnail chip and the viewer line read "Taken before work started"; at 2 minutes before, nothing shows → AC-13
- [ ] As the assigned Mechanic, GET the attachments list → no `takenAt` or `takenBeforeWork` keys, and no flag in the UI → AC-13
- [ ] Return to mechanic, add an After photo, resend → the new photo shows "Added after return" and, in the viewer, "Added after the ticket was returned to the mechanic"; older photos show neither; the mark stays after the resend → AC-14
- [ ] At For verification the second button reads "Return to mechanic"; after returning, the banner reads "Returned by {name}, {relative time}" and the issue pill reads "Returned, not resent yet" → AC-15

### Commands
- [ ] `npm run test` in welinc-backend-vrms and welinc-web-vrms → green (nextAction.test uses the "Return to mechanic" label) → AC-15

### Value sourcing rows (this milestone)
- [ ] upload, `takenAt`: a HEIC the desktop browser can't shrink still sends `takenAt`, read from the original file → AC-12
- [ ] list, `takenBeforeWork`: only a `PROOF` row is flagged, never a Before photo with an old time → AC-13
- [ ] list, `returnedAfter`: on a ticket returned, resent and returned again, the latest return is the one compared → AC-14
- [ ] list, flag visibility: a Chief assigned to the ticket still sees the flag (the role level verify check, not the per ticket rule) → AC-13

## Acceptance-criteria coverage (milestone 4)
- AC-12: manual 1, 2 · value sourcing 1
- AC-13: manual 3, 4 · value sourcing 2, 4
- AC-14: manual 5 · value sourcing 3
- AC-15: manual 6 · commands 1

## Milestone 5: hardening

### UI / manual
- [ ] Race: on an In progress ticket with work started, upload one After photo, then send its DELETE and the Send for verification PATCH at the same moment (for example `Promise.all` from a small script), about 15 rounds, returning the ticket as Chief between rounds → each round is either "remove 204, move 400 AFTER_PHOTO_REQUIRED, still In progress" or "move 200 For verification, remove 204", never a 500 or a stale 409 → AC-7
- [ ] Release: release a mechanic after Start work so the ticket goes back to Open → a new photo lands in After, and the uploader removing their own Before photo gets 403 BEFORE_PHOTO_PROTECTED → AC-1, AC-10
- [ ] axe (wcag2a, wcag2aa, wcag21a, wcag21aa, best practice) on the ticket detail page at 375px and 1280px, on a ticket with a flagged and returned After photo and a returned issue → no violations outside the dev only dataset switch → AC-19
- [ ] Open a photo from its thumbnail with Enter, press Tab once → "Move to Before" or "Move to After" has focus → AC-19
- [ ] The thumbnail's name reads "… Taken before work started. Added after return", and the viewer caption shows each mark on its own line → AC-19

### Commands
- [ ] `npm run test` in welinc-backend-vrms (apply-status-move.spec photo rules under the row lock and the release, audit-events.spec lastReturnAt, attachments.service.spec evidence signals) → green → AC-7, AC-12 to AC-14
- [ ] `npm run test` in welinc-web-vrms (takenAt.test, photoCaption.test) → green → AC-12 to AC-14

## Acceptance-criteria coverage (milestone 5)
- AC-7: manual 1 · commands 1
- AC-19: manual 3, 4, 5
