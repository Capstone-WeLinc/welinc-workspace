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

### 17. Chief Mechanic role · planned
WL-104. A role that sees all tickets and owns verification, following the permission matrix.
**Done when:** Admin can assign the role, the Chief Mechanic sees every ticket and the verification queue, and the sidebar shows the badge.
- Note (2026-10-25): spec 0007 (feature 15) adds the role itself: `CHIEF_MECHANIC` in welinc-auth, welinc-backend-vrms and the web app, assignable on the Users page, with its badge, knowledge base editing, and mechanic rules on tickets for now. What's left here is widening it to every ticket and the verification queue (with feature 23), once the permission matrix (feature 5) settles the exact rights.
- Note (2026-10-29): spec 0002 asks for a Chief Mechanic dashboard (Jira VRMS-41) that reuses the dashboard tiles, with Waiting as the verification queue. Cover it here or with feature 23.
- [ ] Build it: `/develop chief mechanic role`
- [ ] Polish it (optional, ask first): `web-design-guidelines`

### 18. New repair ticket & assignment · planned · needs a decision
WL-201, WL-202, and the ordering half of WL-401. Create a ticket with pickers and auto-filled vehicle and reporter details, then assign in house mechanics first, showing each one's open ticket count.
**Done when:** a ticket is created as Assigned or Open, vehicle details fill in within a second, in house options list first, and the mechanic is notified once notifications exist.
- Note (2026-10-29): spec 0010 already stores priority and the reporter on the ticket. Still to decide here: whether `accountType` and `corporation` are stored or dropped from the form, and whether the server blocks a second open ticket on an `UNDER_REPAIR` truck (today only a warning).
- [ ] Design it (spec): `/architect new repair ticket & assignment`
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (long plates and names, no free mechanics, many issues)

### 53. Admin ticket editing · planned · needs a decision
No Jira ticket yet. After a ticket is created, Admin can fix its driver, assigned mechanics and issues (add, remove, edit). Today nothing on a ticket can change except status, costs, the known fix link and step ticks. Design it together with feature 18, after feature 16.
**Done when:** Admin can edit the driver, mechanics and issues on an open ticket, each change writes an audit row with before and after, a mechanic sees a reassignment within 3 seconds (VR-RL-12), and a stale edit is rejected with the existing 409 reload.
- [ ] Design it (spec): `/architect admin ticket editing`
- [ ] Polish it (optional, ask first): `emil-design-eng` (edit dialogs) · `web-design-guidelines` · `break-ui` (long issue text, many mechanics)

### 19. Mechanic status updates · planned
WL-107. Mechanics move their own tickets forward from a phone.
**Done when:** only the assigned mechanic sees the control, only allowed transitions show, the server rejects anyone else, and each change is logged.
- [ ] Build it: `/develop mechanic status updates`
- [ ] Polish it (optional, ask first): `impeccable` or `emil-design-eng` (one taste skill per change; motion: status change on a phone, bottom sheets) · `web-design-guidelines`

### 20. File upload & storage · planned · needs a decision · GA
WL-218. One private upload service for vehicle photos, proof and receipts.
**Done when:** JPG, PNG, HEIC and PDF up to a set size are accepted, files open only through authorized links, and each file records ticket, type, uploader and time.
- [ ] Design it (spec): `/architect file upload & storage`
- [ ] Extra skills (optional, ask first): `docker-patterns`

### 21. Vehicle photos · planned
WL-209 and WL-210. Mechanics snap photos from the phone camera; reviewers see thumbnails and a full size viewer.
**Done when:** up to 5 photos per ticket upload with progress and retry, thumbnails show in Issue Details, and a mechanic can remove their own until the ticket closes.
- [ ] Build it: `/develop vehicle photos`
- [ ] Polish it (optional, ask first): `impeccable` or `emil-design-eng` (one taste skill per change; motion: photo viewer) · `web-design-guidelines` · `break-ui` (huge photos, many photos, failed uploads)

### 22. Proof of completion · planned
WL-211. No ticket is marked done without evidence.
**Done when:** Mark as Complete stays disabled without a proof file, the server rejects completion without one, and proof shows on the verification screen.
- [ ] Build it: `/develop proof of completion`
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (missing files, many attachments)

### 23. Chief Mechanic verification · planned
WL-212. Verify or reject finished work, with the verifier recorded.
**Done when:** finished tickets land in a verification queue, Verify closes and Reject returns to In Progress with a required comment, and the verifier's name and time are on the ticket and in reports.
- [ ] Build it: `/develop chief mechanic verification`
- [ ] Polish it (optional, ask first): `emil-design-eng` (verify and reject dialogs) · `web-design-guidelines`
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
- [ ] Build it: `/develop vehicle availability`
- [ ] Polish it (optional, ask first): `web-design-guidelines`

### 57. Mechanic workload on the Users page · planned · from spec 0010
See who is busy before assigning. Build after features 18 and 53, since it reuses their counts and the unassign endpoint.
**Done when:** mechanic rows show an Occupied badge (at least one In Progress ticket) and open counts by status, an Occupied or Free filter stays in the address, the user dialog lists the mechanic's open tickets with links and Unassign or Reassign (each audit logged, with the 409 stale check), the assignment picker shows the same counts, and the Chief Mechanic sees it read only under the name Mechanics (a feature 5 permission). No new page.
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
- [ ] Design it (spec): `/architect in-app notifications`
- [ ] Polish it (optional, ask first): `emil-design-eng` (notification popover and toasts) · `web-design-guidelines`

### 29. Notification badge & queue counts · planned
WL-301. Unread count on the bell and counts on queue menus.
**Done when:** the bell shows the unread count (99+ above 99) updating without a refresh, and sidebar queues show their pending counts.
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
- [ ] Build it: `/develop admin status override`
- [ ] Polish it (optional, ask first): `web-design-guidelines`
- Note (2026-10-25): this is how you move a ticket back. Follow feature 16's rule for the spec 0007 checklist and "What fixed it" notes on any backward move.
