# Repair workflow

The core loop (Jira WL-E2, plus WL-E5 and the WL-E1 role work), then the mechanic workflow around it. Mechanic screens are designed phone first at 375px and must survive a weak connection. Back to [index](index.md).

## Slice 1: Core repair loop

Admin creates and assigns a ticket, the mechanic works it from a phone with photos and proof, the Chief Mechanic verifies it, and every step is logged. The thinnest real thread through every layer.

### 16. Ticket status lifecycle · done
WL-200. One official list of statuses and who may move a ticket from which status to which, enforced by the backend. Spec: [0014](../specs/0014-ticket-status-lifecycle/index.md)
**Done when:** final status names are recorded, invalid transitions are rejected with a clear error, and existing tickets migrate without loss.
- [x] Design it (spec): `/architect ticket status lifecycle`
- [x] Build it: `/develop ticket status lifecycle` (code in `welinc-backend-vrms/src/modules/vrms/ticket-transitions.ts`, `apply-status-move.ts`; `welinc-web-vrms/src/features/repair/lib/nextAction.ts`)
  - [x] Table and thin thread: transition table, `applyStatusMove`, required stale check in the transaction, truck release inside it, unassign on the helper (AC-1 to AC-4, AC-7, AC-10 to AC-12)
  - [x] Moves to the web: `moves` and `can.verify` on the ticket, action list in `nextAction.ts`, error code handling (AC-13, AC-15, AC-19)
  - [x] Verify right: `ticket.verify` key, CASL `verify` with no self verification, route guard (AC-5, AC-6)
  - [x] Send back: reject move, backward rule, `lastRejection` banner, prefilled resend (AC-8, AC-9, AC-14, AC-16 to AC-18, AC-21)
  - [x] Existing data check and spec 0011 note (AC-20)
- [x] Verify it: `/check verify ticket status lifecycle` (2026-10-31: passed, every step run; unassign release and atomic rollback proven live)
- [x] Test it: `/test ticket status lifecycle` (2026-10-31: added `apply-status-move.spec.ts`, `dto/stale-lock.dto.spec.ts` and the `getInvalidTransition` cases; backend 703 and web 131 tests green)
- [x] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (2026-10-31: both run, all findings fixed except the "Run AI diagnosis" button at 185px, which belongs to feature 3)
- Note (2026-10-25): today the backend allows forward moves only (`updateStatus` in `repairs.service.ts`). The lifecycle has to cover moving back (reject to In Progress, WL-200 and WL-212; admin override, WL-108) and decide what a backward move does to spec 0007's ticked checklist steps and the "What fixed it" notes saved on the way to For verification (AC-31).
- Note (2026-10-29): spec 0010 fixes the nine status names (`OPEN` to `CLOSED`); this feature keeps the transition table. Also decide whether the Chief Mechanic can close (verify) a ticket, which only Admin can today, and add the optimistic lock that unlock and cancel lack (spec 0004).

### 17. Chief Mechanic role · done
WL-104. A role that sees all tickets and owns verification, following the permission matrix. Spec: [0015](../specs/0015-chief-mechanic-role/index.md)
**Done when:** Admin can assign the role, the Chief Mechanic sees every ticket and the verification queue, and the sidebar shows the badge.
- Note (2026-10-25): spec 0007 (feature 15) adds the role itself: `CHIEF_MECHANIC` in welinc-auth, welinc-backend-vrms and the web app, assignable on the Users page, with its badge, knowledge base editing, and mechanic rules on tickets for now. What's left here is widening it to every ticket and the verification queue (with feature 23), once the permission matrix (feature 5) settles the exact rights.
- Note (2026-10-29): spec 0002 asks for a Chief Mechanic dashboard (Jira VRMS-41) that reuses the dashboard tiles, with Waiting as the verification queue. Cover it here or with feature 23.
- Note (2026-11-01, replan): spec 0014 gave the Chief Mechanic the Verify and Send back moves (`ticket.verify`), without cancel or override. What is left here is the every ticket view and the dashboard.
- Note (2026-11-01): spec 0015 decided the Chief's dashboard (queue first, oldest waiting, then own work, attention, pipeline, no spend), read only costs by default, and an Admin setting to require costs before closing (off by default). The verification queue moved here from feature 23. No new page or sidebar item.
- [x] Design it (spec): `/architect chief mechanic role`
- [x] Build it: `/develop chief mechanic role`
  - [x] Thin thread: `status_changed_at` migration and backfill, the For verification sort, the Chief view with the queue section (AC-7 to AC-11, AC-14 to AC-16)
  - [x] Rest of the Chief view: tiles, My work, Needs attention, pipeline, states, fallback (AC-12, AC-13, AC-17 to AC-19)
  - [x] Read only costs: catalog default, guarded data migration, close dialog wording (AC-1 to AC-3, AC-6)
  - [x] Costs before closing setting: boolean setting type, the `costs` need and 422 on close (AC-4, AC-5)
  - [x] Sweep: tests, fixtures, axe at 375px and 1280px for all three roles, lint, typecheck, build (AC-19, AC-20)
- [x] Verify it: `/check verify chief mechanic role`
- [x] Test it: `/test chief mechanic role` (2026-11-01: added two AC-16 edge cases to `nextAction.test.ts`; web 141 tests green)
- [x] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (empty and long queues, long names, clock skew) (2026-11-01: ran `break-ui` only, fixes applied; the other two skipped)

### 18. New repair ticket & assignment · done
WL-201, WL-202, and the ordering half of WL-401. Create a ticket with pickers and auto-filled vehicle and reporter details, then assign in house mechanics first, showing each one's open ticket count. Spec: [0016](../specs/0016-new-ticket-assignment/index.md)
**Done when:** a ticket is created as Assigned or Open, vehicle details fill in within a second, in house options list first, and the mechanic is notified once notifications exist.
- Note (2026-10-29): spec 0010 already stores priority and the reporter on the ticket. Still to decide here: whether `accountType` and `corporation` are stored or dropped from the form, and whether the server blocks a second open ticket on an `UNDER_REPAIR` truck (today only a warning).
- Note (2026-11-01, replan): from spec 0014. Switch on its moves M1 and M2 (assignment changes the status) when assignment is built here. Applies to features 53 and 57 too.
- Note (2026-11-01): spec 0016 decided it. Create is one locked transaction with one open ticket per truck (409), tickets may start Open and get an Assign action (M1, new `ticket.assign` key), account type and corporation are stored, drivers are keyed by LTO license, and there are new generic lookup lists (vehicle types, corporations) plus a Settings Vehicles section (new `vehicle.manage` key). Its Follow-up carries notes for features 25, 28, 36, 40, 53, 56 and 57.
- [x] Design it (spec): `/architect new repair ticket & assignment`
- [x] Build it: `/develop new repair ticket & assignment` (code in `welinc-backend-vrms/src/modules/vrms/`, `welinc-web-vrms/src/features/repair/`, `welinc-web-vrms/src/features/settings/`)
  - [x] Thin thread, safe create: migration, locked transaction, Open or Assigned, one open ticket per truck, Disabled restore, form handling (AC-1 to AC-3, AC-9, AC-15)
  - [x] Form data: account type and corporation, description fallback, driver by license, odometer floor and jump (AC-4 to AC-8, AC-13)
  - [x] Vehicle facts and picker: vehicle summary card, driver prefill, open counts and Busy (AC-10 to AC-12, AC-14)
  - [x] Assign later: `ticket.assign`, the assignments endpoint through M1, Assign mechanic dialog (AC-16 to AC-18)
  - [x] Settings and sweep: lookup lists, Vehicles section with `vehicle.manage`, Change history, tests, axe, lint, typecheck, build (AC-19 to AC-22). The axe pass at 375px and 1280px is not run yet, left for `/check verify`
- [x] Verify it: `/check verify new repair ticket & assignment` (2026-11-01: passed after the seed; the picker contrast and popup name were fixed in `819f8dc`)
- [x] Test it: `/test new repair ticket & assignment` (2026-11-01: 18 tests added in backend-vrms; 812 backend and 159 web tests pass)
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (long plates and names, no free mechanics, many issues)

### 53. Admin ticket editing · done
No Jira ticket yet. After a ticket is created, Admin can fix its driver, assigned mechanics and issues (add, remove, edit). Today nothing on a ticket can change except status, costs, the known fix link and step ticks. Design it together with feature 18, after feature 16.
**Done when:** Admin can edit the driver, mechanics and issues on an open ticket, each change writes an audit row with before and after, a mechanic sees a reassignment within 3 seconds (VR-RL-12), and a stale edit is rejected with the existing 409 reload.
- Note (2026-11-01, replan): from spec 0015. When this adds its permission key, default the Chief Mechanic to reassign **on**.
- Note (2026-11-01, replan): from spec 0016. Reuse `ticket.assign` for reassign. Let an Admin correct a ticket's odometer (the floor follows it). Add mechanics to Assigned or In Progress tickets.
spec [0019](../specs/0019-admin-ticket-editing/index.md)
- Note (2026-11-03): spec 0019 decided per section Edit dialogs on the detail page, a new `ticket.edit` key (Admin) beside `ticket.assign` (Admin and Chief), priority and account type with corporation added to the editable fields, edits in every open status and on unlocked closed tickets with a reason, an empty mechanic list allowed (Assigned goes back to Open, later statuses get a "No mechanic" flag), at least one issue always, an `edited*` stamp on the ticket, and 3 second polling while visible for VR-RL-12.
- [x] Design it (spec): `/architect admin ticket editing`
- [x] Build it: `/develop admin ticket editing` (2026-11-03: branch `feat/admin-ticket-editing` in backend-vrms and web-vrms; 1114 backend and 262 web tests pass; axe at 375px and 1280px as Admin, only the dev only Demo data pill flagged)
  - code in `welinc-backend-vrms/src/modules/vrms/ticket-edits.service.ts`, `welinc-web-vrms/src/features/repair/components/edit/`
  - [x] Thin thread: migration, `ticket.edit`, priority edit end to end with stamp, audit row, lock rules and 409 (AC-1 to AC-3, AC-6, AC-8, AC-18 to AC-20)
  - [x] Live updates: shared 3 second visible poll on detail, list and dashboard, removed mechanic toast (AC-21 to AC-23)
  - [x] Rest of details: driver swap, odometer floor and ceiling, account type and corporation (AC-4, AC-5, AC-7, AC-8)
  - [x] Mechanics: PUT assignments with M1/M2, verifier block, audit rows, "No mechanic" attention item (AC-8b to AC-13)
  - [x] Issues and sweep: add, edit, remove, audit labels, tests, axe at 375px and 1280px (AC-14 to AC-17, AC-19b, AC-20)
- [x] Verify it: `/check verify admin ticket editing` (2026-11-03: all 40 steps passed. Fixed on the way: axe `button-name` on dropdowns and step checkboxes, and a duplicate license 409 shown as a stale ticket. Spec change: no odometer floor for a truck's oldest ticket)
- [x] Test it: `/test admin ticket editing` (2026-11-03: 367 backend and 264 web tests pass; added the list row test for `mechanicCount` and the edit stamp, AC-13 and AC-19; UI only criteria stay with the verify steps)
- [ ] Polish it (optional, ask first): `emil-design-eng` (edit dialogs) · `web-design-guidelines` · `break-ui` (long issue text, many mechanics)

### 19. Mechanic status updates · done
WL-107. Mechanics move their own tickets forward from a phone.
**Done when:** only the assigned mechanic sees the control, only allowed transitions show, the server rejects anyone else, and each change is logged.
- Note (2026-11-01, replan): most of the server work landed in spec 0014 (transition table, `moves` on the ticket, `nextAction.ts`). What is left is the phone UI at 375px.
- Note (2026-11-01, develop): checked the code against the four Done when points. Spec 0014 already built and verified them, including the bottom action bar at 375px (`NextActionBar.tsx`, AC-15). Nothing is left to build, so Build it is skipped and the feature goes straight to verify as the Mechanic at 375px.
- [~] Build it: `/develop mechanic status updates` (skipped, covered by spec 0014)
- [x] Verify it: `/check verify mechanic status updates` (2026-11-01: passed as the seed Mechanic. API and a 375px browser pass, every Done when point shown)
- [~] Test it: `/test mechanic status updates` (skipped 2026-11-01: spec 0014 tests already lock the behavior)
- [ ] Polish it (optional, ask first): `impeccable` or `emil-design-eng` (one taste skill per change; motion: status change on a phone, bottom sheets) · `web-design-guidelines`

### 20. File upload & storage · done · GA
WL-218, plus WL-209 and WL-210 (feature 21 folded in). One private upload service for vehicle photos, proof, receipts and other documents, and the vehicle photos screens on top of it. Spec: [0017](../specs/0017-file-upload-storage/index.md)
**Done when:** JPG, PNG, HEIC and PDF up to a set size are accepted, files open only through authorized links, and each file records ticket, type, uploader and time. Up to 5 photos per ticket upload with progress and retry, thumbnails show in Issue Details, and a mechanic can remove their own until the ticket closes.
- Note (2026-11-01): spec 0017 decided it. Files go in private Azure Blob Storage (Azurite locally) and open through 10 to 20 minute signed links. Every upload goes through backend-vrms, which sniffs the type, converts HEIC, shrinks photos and rebuilds PDFs without scripts. Three settings (size 10 MB, 5 photos, 20 documents), three permission keys (`ticket.files.add`, `ticket.documents.add`, `ticket.files.remove_any`), receipts and other documents hidden without `ticket.costs.view`, soft delete with a 30 day purge. Feature 21 (vehicle photos) is built here. Crosses backend-vrms, web-vrms, the workspace compose file and `welinc-auth/nginx.conf`.
- Note (2026-11-01): from spec 0017, carried to other features: 26 (spec 0008 Bicep gets the storage account, container, managed identity role, `STORAGE_*` settings and the gateway body size), 22 (a proof cap, and `proof` on move M4), 38 (`outsourcedJobId` on `Attachment` and the receipt upload), 49 (persist the upload queue).
- [x] Design it (spec): `/architect file upload & storage`
- [x] Build it: `/develop file upload & storage`
  - [x] Thin thread: Azurite, the `Attachment` migration, `FileStore` with signed links, one JPEG or PNG photo end to end into Issue Details, `/uploads/` route removed (AC-1, AC-2, AC-6, AC-15, AC-20)
  - [x] Upload rules: access guard, sniffing, size and pixel caps, HEIC, duplicates, caps under the lock, error order, rate limit, gateway limits (AC-3 to AC-14, AC-12a, AC-12b)
  - [x] Permissions, remove and audit: three keys and CASL actions, document visibility, delete, audit events and their filter (AC-15 to AC-18)
  - [x] Phone photo UX: Take photo and Choose photos, browser shrink, upload queue with retries, lightbox viewer, remove, link refresh (AC-21 to AC-26)
  - [x] Documents and retention: PDF disarm and rebuild, Documents card, purge and orphan sweep, tests and axe at 375px and 1280px (AC-4, AC-7, AC-19, AC-27, AC-28)
- [x] Verify it: `/check verify file upload & storage`
- [x] Test it: `/test file upload & storage`
- [ ] Review it (fresh model): `/check review file upload & storage`
- [x] Document it: `/document file upload & storage`
- [x] Polish it / Extra skills (optional, ask first): `docker-patterns` (Azurite service) · `azure-blob-storage` once installed · `impeccable` or `emil-design-eng` (one taste skill per change; motion: photo viewer) · `web-design-guidelines` · `break-ui` (huge photos, many photos, failed uploads, long file names) (2026-11-01: ran `web-design-guidelines` and `break-ui`, all findings fixed; the rest skipped; axe on AC-28 still owed)

### 21. Vehicle photos · dropped
WL-209 and WL-210. Folded into feature 20 on 2026-11-01 (spec 0017 builds the photo screens with the upload service). Kept for history.

### 22. Proof of completion · done
WL-211. No ticket is marked done without evidence. Spec: [0018](../specs/0018-before-after-photos/index.md) · code in `welinc-backend-vrms/src/modules/attachments/`, `welinc-web-vrms/src/features/repair/`
**Done when:** Mark as Complete stays disabled without a proof file, the server rejects completion without one, and proof shows on the verification screen.
- Note (2026-11-01, replan): from spec 0014. Add `proof` to the needs of move M4 (to For verification) in the transition table.
- Note (2026-11-02): spec 0018 makes this before and after photos on one strip, labelled by whether work has started, with Admin switches for Start work, Send for verification and Close. It also renames "Send back" to "Return to mechanic".
- [x] Design it (spec): `/architect proof of completion`
- [x] Build it: `/develop proof of completion`
  - [x] Thin thread: the migration (`workStartedAt`, `takenAt`, one duplicate pool), the derived Before or After label, the After limit, and one photo strip with two groups (AC-1 to AC-3, AC-16, AC-17, AC-21)
  - [x] Photo rules on the moves: the three switches, `photoNeedUnmet()` in `applyStatusMove`, `blockedBy`, disabled buttons with reasons, wait for uploads (AC-4 to AC-8, AC-20)
  - [x] Move and protect: the PATCH move, Before protection, `canMove` and `canRemove`, the audit event and Before and After wording (AC-9 to AC-11, AC-18)
  - [x] Evidence signals: exifr `takenAt`, the "Taken before work started" flag for verifiers, "Added after return", and the "Return to mechanic" wording (AC-12 to AC-15)
  - [x] Hardening: axe at 375px and 1280px, the race and release tests, and the unit tests (AC-7, AC-19)
- [x] Verify it: `/check verify proof of completion`
- [x] Test it: `/test proof of completion`
- [x] Polish it (optional, ask first): `emil-design-eng` (photo viewer menu) · `web-design-guidelines` · `break-ui` (missing photos, full groups, many photos, long uploader names)

### 23. Chief Mechanic verification · done
WL-212. Verify or reject finished work, with the verifier recorded.
**Done when:** finished tickets land in a verification queue, Verify closes and Reject returns to In Progress with a required comment, and the verifier's name and time are on the ticket and in reports.
- Note (2026-11-01, replan): the Verify and Send back moves already exist (spec 0014, with the `lastRejection` banner and prefilled resend). What is left is the verification queue page and the proof files.
- Note (2026-11-01): the verification queue moved to feature 17 (spec 0015, the Chief's dashboard plus the filtered repair list). What is left here is showing proof files at verification and the verifier in reports.
- Note (2026-11-02): feature 22 (spec 0018) now builds the proof view at verification, and renames Send back to "Return to mechanic". What is left here is the verifier's name and time in reports.
- Note (2026-11-03): with the reports module (feature 45) not built yet, History stands in as the report: a "Verified by" column and filter, plus the verified time on the ticket side panel.
- [x] Build it: `/develop chief mechanic verification`
- [x] Verify it: `/check verify chief mechanic verification`
- [x] Test it: `/test chief mechanic verification`
- [x] Polish it (optional, ask first): `emil-design-eng` (verify and reject dialogs, skipped) · `web-design-guidelines` (skipped) · `break-ui` (long verifier names, many verifiers in the filter, ran 2026-11-03)
Code in `welinc-backend-vrms/src/modules/vrms/repairs.service.ts` (`findHistory`), `welinc-web-vrms/src/features/repair/` (History page and filters, `TicketSidePanel`)
- Note (2026-10-25): Reject is the first backward move. Follow feature 16's rule for the spec 0007 checklist and "What fixed it" notes when a ticket goes back to In Progress.

### 24. Full ticket audit trail · planned · needs a decision
WL-219. Every ticket event logged in one consistent shape, so history and reports can trust it.
**Done when:** every event type in WL-219 writes actor, role, time, before and after, and note, and no entry can be edited or deleted from the UI.
- Note (2026-10-29): spec 0010 gives the audit log one shape (one row per event, its changes as a JSON list). Remarks and mechanic assignments are still not audited; decide whether they join the timeline.
- [ ] Design it (spec): `/architect full ticket audit trail`

### 25. Vehicle availability · planned
WL-501, built on Jira's proposed rules. A truck under repair can't be dispatched.
**Done when:** a vehicle turns Under Repair when its ticket is created, returns to Available when it closes, Admin can toggle it with a reason, and the history is kept per vehicle.
- Note (2026-10-29): safe to build before the integration meeting, but feature 56 (integration contract) may change it: vehicle status is shared with VMMS (`UNDER_REPAIR` and `UNDER_MAINTENANCE` on the same vehicle).
- Note (2026-10-29): spec 0010 adds `DISABLED` to the vehicle statuses and designs the `VehicleStatusChange` history table for this feature to create. Also fix the vehicle status change on close or cancel, which runs outside the status transaction today, so a failed write can leave the truck marked Available.
- Note (2026-11-01, replan): that close and cancel fix shipped in spec 0014 (the truck release now runs inside the status transaction). What is left is the history table, the Admin toggle and Under Repair on create.
- Note (2026-11-01, replan): from spec 0016. Under Repair on create now ships in feature 18, with `VehicleChange` (`field: 'status'`) as the history table. What is left: the Admin status toggle in the Settings Vehicles section, behind `vehicle.manage`. A ticket's release restores the stored `priorVehicleStatus`, so the toggle must not be overwritten by it while a ticket is open.
- [ ] Build it: `/develop vehicle availability`
- [ ] Polish it (optional, ask first): `web-design-guidelines`

### 57. Mechanic workload on the Users page · planned · from spec 0010
See who is busy before assigning. Build after features 18 and 53, since it reuses their counts and the unassign endpoint.
**Done when:** mechanic rows show an Occupied badge (at least one In Progress ticket) and open counts by status, an Occupied or Free filter stays in the address, the user dialog lists the mechanic's open tickets with links and Unassign or Reassign (each audit logged, with the 409 stale check), the assignment picker shows the same counts, and the Chief Mechanic sees it read only under the name Mechanics (a feature 5 permission). No new page.
- Note (2026-11-01, replan): from spec 0016. Reuse `openCount` and `busy` from the assignment picker, and `ticket.assign` for Unassign and Reassign.
- [ ] Build it: `/develop mechanic workload`
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (busy and idle mechanics, huge counts)

### 58. Per ticket checklist edits · planned · needs a decision · from spec 0007
The Known fix checklist on a ticket can only be ticked today. You want it to stay a helper, so each ticket lets you add, remove and reword its own copied steps without changing the knowledge base entry.
**Done when:** on a ticket, a user working it can add, remove and reword its copied steps, the knowledge base entry stays unchanged, and the edits survive a reload.
- Note (2026-10-29): held back until feature 15 was verified, which it now is. A small spec: the copied steps already exist (`RepairIssueStep`), so the open points are who may edit them and what happens to ticked steps when one is removed.
- [ ] Design it (spec): `/architect per ticket checklist edits`
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (long step text, many steps, empty checklist)

## Slice 2: Mechanic workflow & notifications

Adds the alerts and hand offs around the core loop.

### 28. In-app notifications · planned · needs a decision
WL-304. The shared notification service every alert uses, across in app, email and push to the mobile app.
**Done when:** assignments, transfers, holds, verifications and deadline alerts create notifications, clicking one opens the ticket, new ones appear without a reload, and each alert also goes out by email or push where its rule says so.
- Note (2026-10-29): channels are in app, email and push to the mobile app. SMS is out of scope: it costs money per message (about 0.56 pesos a text at Semaphore, double for OTP) and in app plus push already reach mechanics. Today only welinc-auth sends email (OTP, reset, setup codes), and VMMS and BMS each run their own mail sender. Email goes through Brevo over SMTP, subject to change at the integration meeting or in the spec (it needs only new `SMTP_*` values). Today welinc-auth sends through a personal Gmail account, which is fine for development but must move to Brevo with a sender address you control before staging. The spec decides which alert goes on which channel. Feature 56 may turn this into one notification service for all three systems.
- Note (2026-11-01, replan): from spec 0014. Notify the mechanic on Send back and on Verify (WL-212).
- Note (2026-11-01, replan): from spec 0016. Notify the mechanic on create with mechanics and on assign (WL-201, VRMS-67).
- [ ] Design it (spec): `/architect in-app notifications`
- [ ] Polish it (optional, ask first): `emil-design-eng` (notification popover and toasts) · `web-design-guidelines`

### 29. Notification badge & queue counts · planned
WL-301. Unread count on the bell and counts on queue menus.
**Done when:** the bell shows the unread count (99+ above 99) updating without a refresh, and sidebar queues show their pending counts.
- Note (2026-11-01, replan): from spec 0015. The verification queue has no sidebar item, so its count lives on the Waiting for you tile of the Chief's dashboard. Reconsider a badge there.
- [ ] Build it: `/develop notification badge`
- [ ] Polish it (optional, ask first): `emil-design-eng` (badge changes) · `web-design-guidelines` · `break-ui` (0, 99 and 1000+ counts)

### 30. Transfer requests · planned
WL-204. A mechanic asks to hand off a ticket; Admin approves or rejects.
**Done when:** a mechanic can request with a reason, only one request is pending per ticket, Admin approves with a new mechanic or rejects with a reason, and everyone involved is notified.
- Note (2026-10-29): the `TransferRequest` table is designed in spec 0010, including a partial unique index (raw SQL) for one pending request per mechanic per ticket. Prisma may not model it, so check the `prisma-cli` skill first and make sure later generated migrations do not drop it.
- [ ] Build it: `/develop transfer requests`
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (long reasons, many pending requests)

### 31. On hold for parts · planned · needs a decision
WL-208, built on proposed defaults. Pause a ticket for missing parts with the reason verified.
**Done when:** a mechanic sets the hold with parts and reason, a verifier approves or rejects it, hold time is tracked for reports, and held tickets stand out in lists.
- Note (2026-10-29): `TicketHold` is designed in spec 0010 with a partial unique index (raw SQL) for one open hold per ticket. Same Prisma drift risk as feature 30: check the `prisma-cli` skill and make sure later generated migrations do not drop it.
- Note (2026-11-01, replan): from spec 0014. The hold moves (M7 to M13 in its table) are written but off; switch them on through `applyStatusMove` with this feature's trigger. Same for features 37, 38 and 39.
- Note (2026-11-01, replan): from spec 0015. Default the Chief Mechanic's "approve a parts hold" key to **on**.
- [ ] Design it (spec): `/architect on hold for parts`
- [ ] Polish it (optional, ask first): `web-design-guidelines`

### 32. Repair history timeline · planned
WL-205. A clickable timeline inside the ticket view, linked from My Repairs.
**Done when:** the timeline is built from the audit trail, entries expand to show details and files, it filters by event type, and mechanics see only their own tickets' history.
- Note (2026-10-29): filter `COST_UPDATE` events out of the mechanic view, since mechanics must never see costs (spec 0010).
- [ ] Build it: `/develop repair history timeline`
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (long timelines, events with long notes)

### 33. Admin status override · planned
WL-108, built on Jira's proposed rules. Admin fixes a wrong status with a reason.
**Done when:** Admin can set any valid status with a required reason, the entry is marked Override in the timeline, and the mechanic is notified.
- Note (2026-11-01, replan): from spec 0014. Build this as the one bypass of the transition table, reusing the `applyStatusMove` effects and its finished field clearing. Until it ships, a ticket closed by mistake can't be reopened in the app.
- [ ] Build it: `/develop admin status override`
- [ ] Polish it (optional, ask first): `web-design-guidelines`
- Note (2026-10-25): this is how you move a ticket back. Follow feature 16's rule for the spec 0007 checklist and "What fixed it" notes on any backward move.

### 62. Costs after close · planned · needs a decision · from spec 0015
Let an Admin add or fix costs on a closed ticket without unlocking it, the way shops post parts invoices and receipts after the truck has left (a separate financial close).
**Done when:** an Admin can add or change costs on a closed ticket with no unlock, each change writes an audit row with before and after, the ticket stays closed, and reports pick up the new totals.
- Note (2026-11-01): from spec 0015. Today a ticket closed without costs needs an Admin unlock to fix. This changes the closed ticket lock from specs 0004 and 0014, so it needs a spec.
- [ ] Design it (spec): `/architect costs after close`
- [ ] Polish it (optional, ask first): `web-design-guidelines`
