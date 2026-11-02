# Verify: Admin ticket editing · spec 0019 · updated 2026-11-03
_Steps derived from spec 0019 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## UI / manual
- [x] As Admin, open an Assigned ticket → "Vehicle & driver", People and each issue show an Edit button, and Issues shows "Add issue" → AC-1, AC-20
- [x] As Chief, open the same ticket → only the People (mechanics) Edit shows; no details or issue controls → AC-1
- [x] As Mechanic, open an assigned ticket → no Edit controls at all → AC-1
- [x] As Admin, open a Closed ticket that is not unlocked → no Edit controls; unlock it → Edit controls show, and every dialog asks for a reason (5 to 500) → AC-2, AC-3
- [x] Edit dialog: swap the driver to another existing driver, save → Driver changes, "Last edit: Edited just now by <you>" shows in Details → AC-4, AC-19
- [x] Edit dialog: "Add new driver" with a license that an active driver holds → "A driver with this license exists" with "Use <name>", which switches to that driver → AC-4
- [x] Edit dialog: odometer below the previous ticket's reading → field error naming that ticket (REP-…); above a later ticket's reading → error naming the later ticket → AC-5
- [x] Edit dialog: odometer far above the floor (over `tickets.odometer_jump_warn_km`) → warning, button turns "Confirm and save", second save goes through → AC-5
- [x] Change priority, then account Online → Corporate without a corporation → "Choose a corporation."; pick one and save → Account shows "Corporate · <name>" → AC-6, AC-7
- [x] Open the dialog, change something, Cancel → "Discard changes?" prompt → AC-20
- [x] Open the same ticket as Admin in two tabs, save in tab 1, then save in tab 2 → toast "This ticket changed…", the dialog closes and the page reloads the latest → AC-18, AC-22
- [x] With a dialog open in tab 2, save a change in tab 1 → tab 2's page behind the dialog updates within 3 seconds, while its form keeps what was typed → AC-21, AC-22
- [x] People Edit on an Assigned ticket: remove the only mechanic → warning "goes back to Open", save → status Open → AC-10
- [x] People Edit on an In progress ticket: remove every mechanic → warning "stays In progress…", save → dashboard Needs attention lists it with "No mechanic" → AC-10, AC-13
- [x] On a closed ticket verified by the Chief (unlocked), add the Chief as a mechanic → "The person who verified this ticket can't be added to it." → AC-11
- [x] Add issue with a known fix and a blank description → the issue reads "[System] <root cause>: <fix name>" with the fix's steps → AC-14
- [x] Edit an issue linked to a known fix and pick another system → the dialog warns the fix and its steps go; save → the fix is gone → AC-15
- [x] Remove an issue with ticked steps and a tagged photo → the confirm names the ticked steps and the photo count; after it, the photo stays untagged → AC-16
- [x] A ticket with one issue shows no Remove for it → AC-17
- [x] As Mechanic, keep the ticket open while an Admin removes you → within 3 seconds a toast "You’re no longer assigned to REP-…" and the repair list → AC-23
- [x] As Mechanic on the repair list, an Admin assigns you a ticket → it appears within 3 seconds → AC-21 (VR-RL-12)
- [x] Audit log and ticket Activity: the new rows read "edited", "added an issue to", "edited an issue on", "removed an issue from" with one line per change ("Priority: Medium → High", "Odometer: 120,400 → 120,040 km", "Account: Online → Corporate (Acme)"); the filter has Edits and the three issue chips → AC-19b
- [x] axe at 375px and 1280px on the detail page and each dialog, as Admin, Chief and Mechanic → no violations besides the dev only Demo data pill → AC-20

## Commands
- [x] `PATCH /vrms/repairs/:id/details` as Chief → 403 `permission: ticket.edit`; same Chief `PUT /:id/assignments` → 200 → AC-1
- [x] `PATCH /details` on a locked Closed ticket → 400 `TICKET_LOCKED`; unlocked with no reason → 400 `REASON_REQUIRED` → AC-2, AC-3
- [x] Same `PATCH /details` body twice with the first `lastUpdatedAt` → 200 then 409 → AC-18
- [x] A save that changes nothing → 200 and no new audit row, `editedAt` unchanged → AC-8b
- [x] One details save of driver, odometer and priority → exactly one `TICKET_EDITED` row with three changes; `editedAt`, `editedByName`, `updatedAt` and `lastActivityAt` share one time → AC-8, AC-19
- [x] `PUT /assignments` with `[]` on Assigned → status Open and one `MECHANIC_UNASSIGNED` row carrying `repairStatus ASSIGNED → OPEN`, no `STATUS_CHANGE` row; then the old list → Assigned with one `MECHANIC_ASSIGNED` row → AC-10, AC-12
- [x] Old `POST /assignments` still adds to the current list → 200 → alias
- [x] `POST /:id/issues/:issueId/remove` on the last issue → 400 `LAST_ISSUE` → AC-17
- [x] `GET /vrms/repairs` rows carry `mechanicCount`; `GET /:id` carries `editedAt`, `editedByName`, `driverId` and `can.edit` → AC-13, AC-19
- [x] `npm run test` in welinc-backend-vrms (`ticket-edits.spec.ts`) and welinc-web-vrms (`ticketEdits.test.ts`, `visiblePoll.test.ts`, `mechanicProblem.test.ts`) → all pass

## Value sourcing
- [x] Who edited: the audit actor and `editedByName` match the signed in account, even when the body sends other names → token, never the body
- [x] Odometer floor and ceiling: on a truck with two tickets created the same second, the order still follows `(createdAt, id)` → `ticketOdometerBounds`
- [x] Odometer floor with no earlier ticket: there is no floor, so the oldest ticket on a truck can be corrected down to 0 and up to the later ticket's reading, with no jump warning → AC-5
- [x] Corporation: rename the lookup value after saving → the ticket keeps the old name (snapshot) → AC-7
- [x] Issue description: the stored text is `[System] rootCause: text`, the same as create → shared `issueDescription`
- [x] Removed toast repair number comes from the last loaded ticket → AC-23
- [x] Poll interval: 3 seconds while visible, paused while hidden, 15 seconds after three failures in a row (stop the backend to see it) → `TICKET_POLL_MS`

## Acceptance-criteria coverage
- AC-1 UI 1 to 3, Commands 1 · AC-2, AC-3 UI 4, Commands 2 · AC-4 UI 5, 6 · AC-5 UI 7, 8, Value 2, 3 · AC-6, AC-7 UI 9, Value 4 · AC-8 Commands 5 · AC-8b Commands 4 · AC-9 to AC-12 UI 13 to 15, Commands 6 · AC-13 UI 14, Commands 9 · AC-14 UI 16, Value 5 · AC-15 UI 17 · AC-16 UI 18 · AC-17 UI 19, Commands 8 · AC-18 UI 11, Commands 3 · AC-19 UI 5, Commands 5 · AC-19b UI 22 · AC-20 UI 10, 23 · AC-21 UI 12, 21, Value 7 · AC-22 UI 11, 12 · AC-23 UI 20, Value 6
