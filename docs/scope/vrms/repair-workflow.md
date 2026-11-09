# Repair workflow

The core loop (Jira WL-E2, plus WL-E5 and the WL-E1 role work), then the mechanic workflow around it. Mechanic screens are designed phone first at 375px and must survive a weak connection. Back to [index](index.md).

## Slice 1: Core repair loop

Admin creates and assigns a ticket, the mechanic works it from a phone with photos and proof, the Chief Mechanic verifies it, and every step is logged. The thinnest real thread through every layer.

### 16. Ticket status lifecycle · done
WL-200. One official list of statuses and who may move a ticket from which status to which, enforced by the backend. Spec: [0014](../../specs/vrms/0014-ticket-status-lifecycle/index.md)
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
WL-104. A role that sees all tickets and owns verification, following the permission matrix. Spec: [0015](../../specs/vrms/0015-chief-mechanic-role/index.md)
**Done when:** Admin can assign the role, the Chief Mechanic sees every ticket and the verification queue, and the sidebar shows the badge.
- Note (2026-10-25): spec 0007 (feature 15) adds the role itself: `CHIEF_MECHANIC` in welinc-auth, welinc-backend-vrms and the web app, assignable on the Users page, with its badge, knowledge base editing, and mechanic rules on tickets for now. What's left here is widening it to every ticket and the verification queue (with feature 23), once the permission matrix (feature 5) settles the exact rights.
- Note (2026-10-29): spec 0002 asks for a Chief Mechanic dashboard (Jira VRMS-41) that reuses the dashboard tiles, with Waiting as the verification queue. Cover it here or with feature 23.
- Note (2026-11-01, replan): spec 0014 gave the Chief Mechanic the Verify and Send back moves (`ticket.verify`), without cancel or override. What is left here is the every ticket view and the dashboard.
- Note (2026-11-01): spec 0015 decided the Chief's dashboard (queue first, oldest waiting, then own work, attention, pipeline, no spend), read only costs by default, and an Admin setting to require costs before closing (off by default). The verification queue moved here from feature 23. No new page or sidebar item.
- Note (2026-11-05, replan): spec 0022 (feature 63) replaced the Chief view this built: the tiles, Needs attention and the pipeline are gone, and the dashboard is now a summary band, For verification, My work and Team. The sign off queue rules and the costs rules from spec 0015 stay.
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
WL-201, WL-202, and the ordering half of WL-401. Create a ticket with pickers and auto-filled vehicle and reporter details, then assign in house mechanics first, showing each one's open ticket count. Spec: [0016](../../specs/vrms/0016-new-ticket-assignment/index.md)
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
spec [0019](../../specs/vrms/0019-admin-ticket-editing/index.md)
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
WL-218, plus WL-209 and WL-210 (feature 21 folded in). One private upload service for vehicle photos, proof, receipts and other documents, and the vehicle photos screens on top of it. Spec: [0017](../../specs/vrms/0017-file-upload-storage/index.md)
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
WL-211. No ticket is marked done without evidence. Spec: [0018](../../specs/vrms/0018-before-after-photos/index.md) · code in `welinc-backend-vrms/src/modules/attachments/`, `welinc-web-vrms/src/features/repair/`
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

### 24. Full ticket audit trail · done
WL-219. Every ticket event logged in one consistent shape, so history and reports can trust it.
**Done when:** every event type in WL-219 writes actor, role, time, before and after, and note, and no entry can be edited or deleted from the UI.
- Note (2026-10-29): spec 0010 gives the audit log one shape (one row per event, its changes as a JSON list). Remarks and mechanic assignments are still not audited; decide whether they join the timeline.
- Note (2026-11-03, replan): from spec 0019. Mechanic assignments and the new edit actions (driver, odometer, priority, account, issues) already write audit rows and join the timeline. Remarks are the main gap left.
spec [0021](../../specs/vrms/0021-full-ticket-audit-trail/index.md)
- Note (2026-11-04): spec 0021 decided it. It closes four gaps: relocking saves (costs, remarks and cancel reason after an unlock, plus a `LOCKED` row), step ticks (`STEP_CHECKED`, `STEP_UNCHECKED`), and `MECHANIC_ASSIGNED` on create. Every type gets one of seven categories, and the API filters by categories, types and role, with a `catalog` endpoint. Cost rows are hidden without `ticket.costs.view`. A trigger makes `audit_logs` append only, and grants follow with feature 26. `STATUS_OVERRIDE` and `TRANSFER_*` are reserved for features 33 and 30. The Audit log page redesign is feature 64.
- [x] Design it (spec): `/architect full ticket audit trail`
- [x] Build it: `/develop full ticket audit trail`
  - [x] Thin thread, relocking saves: catalog and categories, `COST_UPDATE`, `TICKET_EDITED` and `LOCKED` with the unlock reason, write order stamps, `category` on events, `MECHANIC_ASSIGNED` on create, web sentences (AC-1 to AC-3b, AC-5b, AC-7, AC-8, AC-15)
  - [x] Step ticks: one transaction with the checks, conditional update, `STEP_CHECKED` and `STEP_UNCHECKED`, `lastActivityAt` (AC-4, AC-5, AC-15)
  - [x] Filters and catalog: `categories`, `types`, `actorRole`, the `type` alias, 400s, `GET audit-logs/catalog`, cost rows hidden (AC-9 to AC-12)
  - [x] Append only: trigger migration, seed disable and enable, guard test (AC-13, AC-14)
  - [x] Coverage and sweep: coverage test over every ticket action, lint, build, tests, live check of the new rows (AC-6, AC-15)
Code in `welinc-backend-vrms/src/modules/vrms/audit-events.ts` (catalog, builders, filters), `repairs.service.ts` (`saveUnlocked`, `updateCosts`, `checkStep`, `findAuditEvents`, `findAuditCatalog`), `prisma/migrations/20261104120000_audit_logs_append_only/`, `welinc-web-vrms/src/features/audit-logs/` (sentences and lines)
- Note (2026-11-04, verify): the mechanics save (spec 0019) shared one time for its removed and added rows; fixed so they are stamped in write order like the other multi row actions. Two wording gaps in spec 0021 (AC-6 actor of the deactivation unassign, AC-9 unknown stored actions) were fixed by `/architect` on 2026-11-04. `attachments/AGENTS.md` still names `hideDocumentEvents`, now `hiddenAuditEvents` (`/sync`).
- [x] Verify it: `/check verify full ticket audit trail`
- [x] Test it: `/test full ticket audit trail`

### 25. Vehicle availability · done
WL-501, built on Jira's proposed rules. A truck under repair can't be dispatched.
**Done when:** a vehicle turns Under Repair when its ticket is created, returns to Available when it closes, Admin can toggle it with a reason, and the history is kept per vehicle.
- Note (2026-10-29): safe to build before the integration meeting, but feature 56 (integration contract) may change it: vehicle status is shared with VMMS (`UNDER_REPAIR` and `UNDER_MAINTENANCE` on the same vehicle).
- Note (2026-10-29): spec 0010 adds `DISABLED` to the vehicle statuses and designs the `VehicleStatusChange` history table for this feature to create. Also fix the vehicle status change on close or cancel, which runs outside the status transaction today, so a failed write can leave the truck marked Available.
- Note (2026-11-01, replan): that close and cancel fix shipped in spec 0014 (the truck release now runs inside the status transaction). What is left is the history table, the Admin toggle and Under Repair on create.
- Note (2026-11-01, replan): from spec 0016. Under Repair on create now ships in feature 18, with `VehicleChange` (`field: 'status'`) as the history table. What is left: the Admin status toggle in the Settings Vehicles section, behind `vehicle.manage`. A ticket's release restores the stored `priorVehicleStatus`, so the toggle must not be overwritten by it while a ticket is open.
spec [0020](../../specs/vrms/0020-vehicle-availability/index.md)
- Note (2026-11-03): spec 0020 decided the Admin toggles Available and Disabled only, with a reason (5 to 500); the toggle is blocked while the truck has an open ticket; create and release also write `VehicleChange` status rows, linked by a new `repairTicketId` column; Settings, Vehicles gets a row menu, status filter chips in `?status=` and a History dialog.
- Note (2026-11-03, replan): open follow-up from spec 0020, only if needed: "Disable after repair" (the toggle on an open ticket saves the choice to `priorVehicleStatus`), for the gap between close and the Admin's Disable click. Not enrolled as a row until it bites.
- [x] Design it (spec): `/architect vehicle availability`
- [x] Build it: `/develop vehicle availability`
  - [x] Thin thread: migration, `POST /vrms/vehicles/:id/status` with lock, check order and history row, row menu and reason dialog (AC-1 to AC-5a, AC-10, AC-11, AC-14)
  - [x] Automatic history: create and release rows through `vehicleStatusChange` (AC-6, AC-7, AC-15)
  - [x] List hints and filter: `openTicket` on every row, disabled action hints, status chips (AC-8, AC-10, AC-12)
  - [x] History dialog: keyset paged changes endpoint and dialog with Load more (AC-9, AC-13)
  - [x] Sweep: lint, typecheck, build, tests, 375px and 1280px with axe (AC-16)
  - code in `welinc-backend-vrms/src/modules/vrms/vehicles/` (`vehicle-status.ts` is the one status writer), `welinc-web-vrms/src/features/settings/` (`VehiclesSection.tsx`, `VehicleHistoryDialog.tsx`, `lib/vehicleStatus.ts`)
- [x] Verify it: `/check verify vehicle availability` (2026-11-03: passed; AC-11 counter fixed during the run, two verify steps reworded)
- [x] Test it: `/test vehicle availability` (2026-11-03: 5 backend spec files added or extended, 1170 backend tests pass; the dialog counter is a component and web-vrms has no component tests)
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (long plates and reasons, many history entries)

### 57. Mechanic workload on the Users page · done · from spec 0010
See who is busy before assigning. Build after features 18 and 53, since it reuses their counts and the unassign endpoint.
**Done when:** mechanic rows show an Occupied badge (at least one In Progress ticket) and open counts by status, an Occupied or Free filter stays in the address, the user dialog lists the mechanic's open tickets with links and Unassign or Reassign (each audit logged, with the 409 stale check), the assignment picker shows the same counts, and the Chief Mechanic sees it read only under the name Mechanics (a feature 5 permission). No new page.
- Note (2026-11-01, replan): from spec 0016. Reuse `openCount` and `busy` from the assignment picker, and `ticket.assign` for Unassign and Reassign.
- Note (2026-11-03, replan): from spec 0019. Unassign and Reassign should call `PUT /repairs/:id/assignments` (it already runs M1 and M2, the verifier block and the audit rows), not a new endpoint.
- Note (2026-11-03, develop): built the Admin side only, no spec (no decision owed). The Chief Mechanic's read only "Mechanics" view is held back: the Users page reads `GET /auth/users` from welinc-auth, which only Admin may call, so the Chief view needs a new permission key and its own VRMS data source. That is a decision for `/architect` (or `/scope` can split it into its own row). The picker's "Busy" badge now reads "Occupied", the same rule (`isOccupied` in `mechanic-workload.ts`).
- [x] Build it: `/develop mechanic workload` (2026-11-03: branch `feat/mechanic-workload` in backend-vrms and web-vrms; lint, typecheck, build and tests green, 417 backend vrms module tests and 290 web tests)
  - code in `welinc-backend-vrms/src/modules/vrms/mechanic-workload.ts`, `mechanic-work.service.ts` (`workload`, `openTickets`); `welinc-web-vrms/src/features/user-management/` (`lib/workload.ts`, `hooks/useWorkload.ts`, `components/UserWorkCell.tsx`, `components/MechanicOpenTickets.tsx`, `components/ReassignDialog.tsx`)
  - [x] Server reads: `GET /vrms/mechanics/workload` and `GET /vrms/mechanics/:authUserId/open-tickets` behind `users.manage`, one Occupied rule shared with the picker
  - [x] Users page: Work column (Occupied or Free plus counts by status), Work filter in `?work=`
  - [x] User dialog: open tickets with links, Unassign and Reassign through `PUT /repairs/:id/assignments` (audit rows, M1 and M2, 409 stale check)
    - Note (2026-11-03): the first `/check verify` found the Reassign prompt ran off the screen (67 radios, buttons out of view on desktop and phone). Fixed: Reassign is now a searchable dialog (a sheet on phones) in the Assign dialog's order. Steps 1 to 8 were rechecked live after the fix.
  - [~] Chief Mechanic read only "Mechanics" view (moved to feature 63 on 2026-11-03)
- [x] Verify it: `/check verify mechanic workload` (2026-11-03: passed on the second run. The first run failed on the Reassign prompt running off the screen; fixed in `96ec6cc`. Server reads, guards, Work column, filter, dialog, Unassign, Reassign, stale 409, Occupied wording and 375px all shown live. Chief Mechanic view and an axe scan not run)
- [x] Test it: `/test mechanic workload` (2026-11-03: extended `mechanic-workload.spec.ts` and `workload.test.ts`; backend 1191 and web 307 tests pass. The dialogs have no component tests, since web-vrms tests pure logic only)
- [x] Polish it (optional, ask first): `web-design-guidelines` (2026-11-03: ran, 7 findings fixed: live regions, focus after Unassign and Reassign, a real disclosure for co-workers and Show all, the ellipsis, the dash text. Left: the filter result count) · `break-ui` (2026-11-03: ran, 8 of 9 findings fixed. Left on purpose: the 1,284 option Reassign picker is not virtualized, since a real roster is about 70. Fixture in `welinc-web-vrms/src/features/dev-ui/worst-case/usersData.ts`, `?data=worst` on `/users`)

### 58. Per ticket checklist edits · in-progress · from spec 0007
The Known fix checklist on a ticket can only be ticked today. You want it to stay a helper, so each ticket lets you add, remove and reword its own copied steps without changing the knowledge base entry.
**Done when:** on a ticket, a user working it can add, remove and reword its copied steps, the knowledge base entry stays unchanged, and the edits survive a reload.
- Note (2026-10-29): held back until feature 15 was verified, which it now is. A small spec: the copied steps already exist (`RepairIssueStep`), so the open points are who may edit them and what happens to ticked steps when one is removed.
spec [0023](../../specs/vrms/0023-per-ticket-checklist-edits/index.md) · code in `welinc-backend-vrms/src/modules/vrms/checklist-edits*.ts`, `welinc-web-vrms/src/features/repair/components/edit/ChecklistEditDialog.tsx`, `welinc-web-vrms/src/features/repair/lib/checklist.ts`
- Note (2026-11-06): spec 0023 decided it. An Edit steps dialog per issue (Add steps on an issue with none, linked or not) saves the full ordered list while the ticket is Assigned or In progress, behind a new `ticket.checklist.edit` key (all three roles on; without `ticket.view_all`, only on assigned tickets). The lock is a new `checklistVersion` on the issue, so checklist saves never make other ticket edits stale; relink, the `clearsFix` issue edit and approved suggestions raise it too. Removing a ticked step asks first, rewording one clears its tick, steps carry Added and Edited tags, and each changed step writes `STEP_ADDED`, `STEP_REMOVED`, `STEP_EDITED` or `STEP_MOVED`. The knowledge base entry never changes; feeding edits back to it is a later follow up.
- Note (2026-11-06, update): spec 0023 updated in place. The Edit steps sheet becomes inline borderless rows with a drag handle (`@dnd-kit/sortable`, handle only, keyboard Space, arrows, Space, spoken sentences); Move up and Move down go; Enter adds a step below and Backspace removes an empty one. The moved set tie rule changes to the run through the lowest old positions ("Step 6 → step 5" when dragging 6 above 5), and an approved suggestion keeps an issue's own steps. Build slice 5 holds the rework.
- [x] Design it (spec): `/architect per ticket checklist edits` (updated 2026-11-06)
- [x] Build it: `/develop per ticket checklist edits` (2026-11-06: built in backend `e54eebe` and web `719a9a3` on `feat/per-ticket-checklist-edits`; one live pass shown: reword, move, add, the ticked step prompt, tags, audit rows, ticket `updatedAt` unchanged. Slice 5 in backend `143993a` and web `e7bb119`; no live pass yet, since Playwright did not connect)
  - [x] Thin thread, reword and add: migration, key and `can.editChecklist`, the `PUT` with `checklistVersion` lock and write order, `STEP_EDITED` and `STEP_ADDED`, the dialog, the tags (AC-1 to AC-6, AC-8, AC-10 to AC-13, AC-17)
  - [x] Remove and reorder: offset reorder, the moved set, `STEP_REMOVED` and `STEP_MOVED`, the ticked step prompt, focus rules (AC-7 to AC-10, AC-18)
  - [x] Own checklists and the shared lock: Add steps, the 0 step save, the version bump on relink, issue edit and approved suggestions, the relink prompt, knowledge switch (AC-4, AC-5, AC-7, AC-14, AC-16)
  - [x] Sweep: diff and service tests, catalog tests, web logic tests, axe at 375px and 1280px, lint, typecheck, build (AC-3, AC-6 to AC-11, AC-14, AC-15, AC-18) (axe at 375px and 1280px not run yet; left for `/check verify`)
  - [x] Lighter sheet with drag: the `longestRun` tie rule and its tests, the suggestion keeps own steps test, the four `@dnd-kit` packages, inline rows with handle, `DragOverlay`, announcements, Enter and Backspace, Move up and Move down removed (AC-4, AC-4a, AC-4b, AC-10, AC-14, AC-18) (2026-11-06: the suggestion test already existed from slice 3; the packages add about 18 KB gzipped; axe with a drag in progress and the touch checks left for `/check verify`)
- [ ] Verify it: `/check verify per ticket checklist edits`
- [ ] Test it: `/test per ticket checklist edits`
- [ ] Polish it (optional, ask first): `emil-design-eng` (the edit sheet) · `web-design-guidelines` · `break-ui` (long step text, 20 steps, empty checklist)

### 63. Chief dashboard rework with a Team section · done · from feature 57
Split from feature 57 on 2026-11-03; reworked on 2026-11-05 after a design review. The Chief's dashboard becomes three sections (Sign off, My work, Team) in one ticket row style. Team shows each mechanic's trucks, time in status and overdue work for the morning lineup, covering an absent mechanic (Reassign and Unassign from a person's list) and spotting stuck work. Tiles, Needs attention and the pipeline go; no new page.
**Done when:** the Chief's dashboard shows Sign off, My work and Team (two columns from 1280px), Team lists people with their plates, time in status and overdue marks with free people collapsed, the Chief can Reassign or Unassign from a person's list, `/mechanics` and its nav changes are gone, a mechanic gets 403 on the roster, and the Admin and Mechanic dashboards and the Users page stay as they are.
- Note (2026-11-03): the open decision is the permission key (its name and defaults, Chief on and Mechanic off) and where the list comes from. The Users page reads `GET /auth/users` from welinc-auth, which only Admin may call, so the Chief's list needs a VRMS source (the mechanic roster in backend-vrms, plus `GET /vrms/mechanics/workload` and `.../open-tickets`, today behind `users.manage`). Also decide whether Unassign and Reassign show for a Chief who holds `ticket.assign`.
spec [0022](../../specs/vrms/0022-chief-mechanic-mechanics-view/index.md)
- Note (2026-11-04): spec 0022 decided a read only `/mechanics` route (sidebar item for `mechanics.view` without `users.manage`) on a new `GET /vrms/mechanics/roster`, a new `mechanics.view` key (Admin and Chief on), `open-tickets` widened to it, a nullable `role` column on `mechanics` for a Chief badge, links only (no Unassign or Reassign), a load order fixed at load with "Sort again", a 3 second poll, and Mechanics replacing Knowledge base in the Chief's phone tab bar.
- Note (2026-11-04, build): the first version (`/mechanics` page) was built on branch `feat/chief-mechanic-mechanics-view`. Kept from it: the `mechanics.view` key, `GET /vrms/mechanics/roster`, the `mechanics.role` column (migration `20261104150000_mechanic_role`, applied) and `open-tickets` widened. The page, filters, Sort again and phone nav changes are removed by the rework.
- Note (2026-11-05, design review): spec 0022 rewritten in place. The page did not serve the Chief's real moments (lineup, absent mechanic, stuck work) and the Chief dashboard itself was confusing (tiles repeating lists, three tables, a mixed pipeline). It also replaces spec 0015's Chief view AC-13, AC-14 (table form), AC-18 and AC-19 (history). The old `verify.md` steps describe the removed page and need replacing at the next `/develop`.
- [x] Design it (spec): `/architect chief mechanic mechanics view` (reworked 2026-11-05)
- [x] Build it: `/develop chief dashboard team` (2026-11-05: branch `feat/chief-mechanic-mechanics-view` in backend-vrms and web-vrms; lint, typecheck, build and tests green, 917 backend vrms and auth tests and 347 web tests)
  - code in `welinc-web-vrms/src/features/dashboard/` (`components/ChiefDashboard.tsx`, `components/DashboardTicketRow.tsx`, `components/TeamSection.tsx`, `lib/team.ts`, `hooks/useMechanicRoster.ts`, `timeInStatus` in `lib/attention.ts`); `welinc-backend-vrms/src/modules/vrms/mechanic-work.service.ts` (`listRoster` gains `mechanicId`)
  - [x] Clear the ground: remove `/mechanics` and its nav changes, `mechanicId` on the roster, key label (AC-1, AC-2, AC-16)
  - [x] New layout: shared ticket row, Sign off and My work with counts, two columns, no tiles, Needs attention or pipeline (AC-5 to AC-9)
  - [x] Team section: `timeInStatus`, `lib/team.ts`, person rows with chips, No mechanic group, Free line, states (AC-7, AC-10 to AC-13, AC-15)
  - [x] Act from the list: person dialog with Reassign and Unassign, refresh after a change (AC-14)
  - [x] Sweep: dashboard tests, Admin and Mechanic dashboards and Users page unchanged, axe at 375px and 1280px (AC-17, AC-18)
    - Note (2026-11-05, develop): axe ran clean on the loaded Chief dashboard at 375px and 1280px and with the person dialog open (the only finding was the dev only Dataset toggle). The every section empty and roster failing states were not reached on seed data; `/check verify` should cover them. Choices made in the build: an inactive person shows the Inactive tag without Occupied or Free (Free would say they can take work); the No mechanic group's rows show the due label; the person dialog reuses the Users page list as is, so its rows keep their own layout rather than `DashboardTicketRow`.
  - Note (2026-11-05, impeccable): restyled after the first look read too plain. Each section is now a panel with an icon header and its count, the Team summary is a strip of three counts, and each person has an initials avatar and a workload bar by status (the Admin pipeline's chart colors, scaled to the busiest person) with matching dots on the chips. No tiles, Needs attention or pipeline came back.
  - Note (2026-11-05, design review with the engineer): the build now differs from spec 0022 on purpose, and `/architect chief mechanic mechanics view: record the design review` should bring the spec in line before `/check verify`. (1) A band of four numbers at the top (Ready to verify, Mechanics working, Work waiting, Free mechanics), each said only there, so the Sign off heading count and the Team summary line are gone (AC-7). (2) "Waiting for your sign off" is now "Ready to verify", empty "Nothing to verify." (AC-5, AC-8, AC-9). (3) Team is a grid of person cards instead of rows (AC-12). (4) A person card shows Occupied or Waiting; Free is used only for people with no tickets (AC-12). (5) Second pass: the numbers are one scoreboard strip with no icons, panel headers have no icon squares, person cards are job sheets (state in words, trucks as a ledger with the time right aligned, no avatars or pills), and Ready to verify rows show the mechanic's name on line 1 instead of the For verification badge every row shared (AC-8). `verify.md` needs the same wording changes.
  - Note (2026-11-05, architect): spec 0022 and its `verify.md` now record the design review and a second pass the same day: a verification summary on top, For verification rows with the issue and a wait colour, and a Team roster with workload bars and a Busy and Free switch. `/check verify` can run against them. Open follow ups: axe again on the new layout, and whether the 24 and 48 hour wait limits move into the Admin thresholds.
  - Note (2026-11-05, seed): the VRMS seed now has a 70 truck fleet, about half the working fleet in the shop today, mechanics holding up to 4 open jobs with one In progress at a time (the Chief and demo logins at least 2), and due dates from priority, so overdue work shows.
  - Note (2026-11-05, replan): open follow ups from spec 0022, none blocking `done`: record `DashboardTicketRow`, `lib/team.ts` and the `mechanics.view` gate in `welinc-web-vrms/AGENTS.md` and `mechanics.role` in `welinc-backend-vrms/AGENTS.md` (`/sync`), and give the PM a Jira line, since there is no ticket for the Chief dashboard rework. The 24 and 48 hour wait colours are fixed in code: feature 43 decides whether they join the Admin thresholds.
- [x] Verify it: `/check verify chief dashboard team`
  - Note (2026-11-05, verify): ran against the live stack. Passed with evidence: roster 403 and 200, layout at 375px and 1280px, summary, For verification, My work, Team rows, dialog Reassign (moved a ticket and back), `mechanics.view` and `ticket.assign` toggles, roster failure, `/mechanics` gone, Admin and Mechanic dashboards and Users page unchanged, backend and web lint, build and tests green. One failure found and fixed: the Team tab counts had 4.34 contrast (now `text-muted-strong`, axe clean). Not reached in the browser (logic covered by Vitest only): red wait colour, same name emails, No mechanic panel, fallback row, empty sections, phone nav comparison.
- [x] Test it: `/test chief dashboard team`
  - Note (2026-11-05, test): no new tests; `team.test.ts` and `attention.test.ts` already cover the Team logic (351 web and 1275 backend tests green). Contrast and layout stay manual checks.
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (many people, long names, a person with 20 tickets, no free people)

## Slice 2: Mechanic workflow & notifications

Adds the alerts and hand offs around the core loop.

### 66. Workflow review against real shops · planned · needs a decision · from the 2026-11-06 workflow topics
Check the repair loop against how real truck shops work (write up, inspect and diagnose, estimate and approval, waiting on parts, labor, a quality check by someone else, close out) and decide which changes VRMS takes on. Do it before feature 67, since the write up shape feeds that picker.
**Done when:** a spec records which candidates are in, later or out, each one in is a scope row (or a change to an existing row), and the ticket flow change is clear enough to build.
- Note (2026-11-08, replan): candidates, none decided yet. The 3 Cs (Complaint at write up, Cause after diagnosis, Correction at send for verification; the strongest one). A reason on On hold (parts, approval, tech away) shown on the dashboard, which reshapes feature 31. Start and Pause per issue so labor hours are recorded, not typed. Let the Chief create tickets (today `ticket.create` is Admin only by default). An approval step above a cost limit (maybe later). Prefill "What fixed it" from the checklist, and a "Suggest these steps for the entry" button at verification. Per issue verification (sign off or return one issue, close when all are signed off; spec 0024's closed row leaves room for an Approved mark). Preventive maintenance stays with VMMS; VRMS takes in their tickets.
- [ ] Design it (spec): `/architect workflow review against real shops`

### 67. Describe first issue picker · planned · needs a decision · from the 2026-11-06 workflow topics
On the repair form, you type what is wrong first and known fixes are suggested from it, with a shorter list to pick from. It must work with the AI module off. Builds on the spec 0007 fix library (feature 15), the old feature 41 picker, and the `issue_embeddings` already linked to known fixes.
**Done when:** typing a description shows suggested known fixes, picking one fills the issue, a browse path still reaches every fix, and it works the same with the AI module off (text match only) or on.
- Note (2026-11-08, replan): open questions with the recommended pick first. Write up shape: describe, then confirm (system filled from the pick, root cause Unknown) · full 3 Cs now · only add suggestions. AI on: hybrid (past issue embeddings ranked by fix plus a text match on fix name and symptoms) · embed the fixes · ask the model to pick. AI off: `pg_trgm` text match · browse only · hide it. Display: top 3 fix cards plus "Browse known fixes" · a ranked dropdown · chips only. Settle the write up shape in feature 66 first.
- [ ] Design it (spec): `/architect describe first issue picker`
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (long descriptions, no matches, many matches)

### 28. In-app notifications · planned · needs a decision
WL-304. The shared notification service every alert uses, across in app, email and push to the mobile app.
**Done when:** assignments, transfers, holds, verifications and deadline alerts create notifications, clicking one opens the ticket, new ones appear without a reload, and each alert also goes out by email or push where its rule says so.
- Note (2026-10-29): channels are in app, email and push to the mobile app. SMS is out of scope: it costs money per message (about 0.56 pesos a text at Semaphore, double for OTP) and in app plus push already reach mechanics. Today only welinc-auth sends email (OTP, reset, setup codes), and VMMS and BMS each run their own mail sender. Email goes through Brevo over SMTP, subject to change at the integration meeting or in the spec (it needs only new `SMTP_*` values). Today welinc-auth sends through a personal Gmail account, which is fine for development but must move to Brevo with a sender address you control before staging. The spec decides which alert goes on which channel. Feature 56 may turn this into one notification service for all three systems.
- Note (2026-11-01, replan): from spec 0014. Notify the mechanic on Send back and on Verify (WL-212).
- Note (2026-11-01, replan): from spec 0016. Notify the mechanic on create with mechanics and on assign (WL-201, VRMS-67).
- Note (2026-11-03, replan): from spec 0019. Notify a mechanic when added to or removed from a ticket by an edit. Once a push channel exists, consider replacing the 3 second visible poll (`useVisiblePoll`) with SSE, or at least a light `GET /repairs/:id/version` check so phones on mobile data fetch only on change.
- [ ] Design it (spec): `/architect in-app notifications`
- [ ] Polish it (optional, ask first): `emil-design-eng` (notification popover and toasts) · `web-design-guidelines`

### 29. Notification badge & queue counts · planned
WL-301. Unread count on the bell and counts on queue menus.
**Done when:** the bell shows the unread count (99+ above 99) updating without a refresh, and sidebar queues show their pending counts.
- Note (2026-11-01, replan): from spec 0015. The verification queue has no sidebar item, so its count lives in the summary band and the For verification section of the Chief's dashboard (the tiles are gone, spec 0022). Reconsider a badge there.
- [ ] Build it: `/develop notification badge`
- [ ] Polish it (optional, ask first): `emil-design-eng` (badge changes) · `web-design-guidelines` · `break-ui` (0, 99 and 1000+ counts)

### 30. Transfer requests · planned
WL-204. A mechanic asks to hand off a ticket; Admin approves or rejects.
**Done when:** a mechanic can request with a reason, only one request is pending per ticket, Admin approves with a new mechanic or rejects with a reason, and everyone involved is notified.
- Note (2026-10-29): the `TransferRequest` table is designed in spec 0010, including a partial unique index (raw SQL) for one pending request per mechanic per ticket. Prisma may not model it, so check the `prisma-cli` skill first and make sure later generated migrations do not drop it.
- Note (2026-11-04, replan): from spec 0021. Write the `TRANSFER_*` audit types per its contract (builders and categories are reserved), and decide whether a requester may withdraw (`TRANSFER_CANCELLED`).
- [ ] Build it: `/develop transfer requests`
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (long reasons, many pending requests)

### 31. On hold for parts · planned · needs a decision
WL-208, built on proposed defaults. Pause a ticket for missing parts with the reason verified.
**Done when:** a mechanic sets the hold with parts and reason, a verifier approves or rejects it, hold time is tracked for reports, and held tickets stand out in lists.
- Note (2026-10-29): `TicketHold` is designed in spec 0010 with a partial unique index (raw SQL) for one open hold per ticket. Same Prisma drift risk as feature 30: check the `prisma-cli` skill and make sure later generated migrations do not drop it.
- Note (2026-11-01, replan): from spec 0014. The hold moves (M7 to M13 in its table) are written but off; switch them on through `applyStatusMove` with this feature's trigger. Same for features 37, 38 and 39.
- Note (2026-11-01, replan): from spec 0015. Default the Chief Mechanic's "approve a parts hold" key to **on**.
- Note (2026-11-08, replan): feature 66 may widen this to a hold with a reason (parts, approval, tech away) shown on the dashboard. Design it after feature 66.
- [ ] Design it (spec): `/architect on hold for parts`
- [ ] Polish it (optional, ask first): `web-design-guidelines`

### 32. Repair history timeline · planned
WL-205. A clickable timeline inside the ticket view, linked from My Repairs.
**Done when:** the timeline is built from the audit trail, entries expand to show details and files, it filters by event type, and mechanics see only their own tickets' history.
- Note (2026-10-29): filter `COST_UPDATE` events out of the mechanic view, since mechanics must never see costs (spec 0010).
- Note (2026-11-04, replan): from spec 0021. Filter by the seven categories from `GET audit-logs/catalog`. Cost events are already hidden for anyone without `ticket.costs.view` (`hiddenAuditEvents`), so the mechanic rule above is covered. Share the event renderer with feature 64.
- Note (2026-11-10, replan): from spec 0023. Render its four new checklist event types with the shared event renderer.
- [ ] Build it: `/develop repair history timeline`
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (long timelines, events with long notes)

### 33. Admin status override · planned
WL-108, built on Jira's proposed rules. Admin fixes a wrong status with a reason.
**Done when:** Admin can set any valid status with a required reason, the entry is marked Override in the timeline, and the mechanic is notified.
- Note (2026-11-01, replan): from spec 0014. Build this as the one bypass of the transition table, reusing the `applyStatusMove` effects and its finished field clearing. Until it ships, a ticket closed by mistake can't be reopened in the app.
- Note (2026-11-03, replan): from spec 0019. A ticket can now be In progress with no mechanic. Today only `ticket.administer` can move such an ownerless ticket; keep that path working here.
- Note (2026-11-04, replan): from spec 0021. Write `STATUS_OVERRIDE` per its contract and set `statusChangedAt` yourself. Readers of status history (`lastRejectionFrom`, `lastReturnAt`, analytics) must decide on purpose whether to include it.
- [ ] Build it: `/develop admin status override`
- [ ] Polish it (optional, ask first): `web-design-guidelines`
- Note (2026-10-25): this is how you move a ticket back. Follow feature 16's rule for the spec 0007 checklist and "What fixed it" notes on any backward move.

### 62. Costs after close · planned · needs a decision · from spec 0015
Let an Admin add or fix costs on a closed ticket without unlocking it, the way shops post parts invoices and receipts after the truck has left (a separate financial close).
**Done when:** an Admin can add or change costs on a closed ticket with no unlock, each change writes an audit row with before and after, the ticket stays closed, and reports pick up the new totals.
- Note (2026-11-01): from spec 0015. Today a ticket closed without costs needs an Admin unlock to fix. This changes the closed ticket lock from specs 0004 and 0014, so it needs a spec.
- Note (2026-11-04, replan): from spec 0021. A cost change on a closed ticket writes `COST_UPDATE` with no unlock, so its own note is the reason, not an unlock reason.
- [ ] Design it (spec): `/architect costs after close`
- [ ] Polish it (optional, ask first): `web-design-guidelines`
