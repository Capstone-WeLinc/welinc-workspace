# Repair workflow

The core loop (Jira WL-E2, plus WL-E5 and the WL-E1 role work), then the mechanic workflow around it. Mechanic screens are designed phone first at 375px and must survive a weak connection. Back to [index](index.md).

## Slice 1: Core repair loop

Admin creates and assigns a ticket, the mechanic works it from a phone with photos and proof, the Chief Mechanic verifies it, and every step is logged. The thinnest real thread through every layer.

### 16. Ticket status lifecycle · planned · needs a decision
WL-200. One official list of statuses and who may move a ticket from which status to which, enforced by the backend.
**Done when:** final status names are recorded, invalid transitions are rejected with a clear error, and existing tickets migrate without loss.
- [ ] Design it (spec): `/architect ticket status lifecycle`
- Note (2026-10-25): today the backend allows forward moves only (`updateStatus` in `repairs.service.ts`). The lifecycle has to cover moving back (reject to In Progress, WL-200 and WL-212; admin override, WL-108) and decide what a backward move does to spec 0007's ticked checklist steps and the "What fixed it" notes saved on the way to For verification (AC-31).

### 17. Chief Mechanic role · planned
WL-104. A role that sees all tickets and owns verification, following the permission matrix.
**Done when:** Admin can assign the role, the Chief Mechanic sees every ticket and the verification queue, and the sidebar shows the badge.
- Note (2026-10-25): spec 0007 (feature 15) adds the role itself: `CHIEF_MECHANIC` in welinc-auth, welinc-backend-vrms and the web app, assignable on the Users page, with its badge, knowledge base editing, and mechanic rules on tickets for now. What's left here is widening it to every ticket and the verification queue (with feature 23), once the permission matrix (feature 5) settles the exact rights.
- [ ] Build it: `/develop chief mechanic role`

### 18. New repair ticket & assignment · planned · needs a decision
WL-201, WL-202, and the ordering half of WL-401. Create a ticket with pickers and auto-filled vehicle and reporter details, then assign in house mechanics first, showing each one's open ticket count.
**Done when:** a ticket is created as Assigned or Open, vehicle details fill in within a second, in house options list first, and the mechanic is notified once notifications exist.
- [ ] Design it (spec): `/architect new repair ticket & assignment`

### 53. Admin ticket editing · planned · needs a decision
No Jira ticket yet. After a ticket is created, Admin can fix its driver, assigned mechanics and issues (add, remove, edit). Today nothing on a ticket can change except status, costs, the known fix link and step ticks. Design it together with feature 18, after feature 16.
**Done when:** Admin can edit the driver, mechanics and issues on an open ticket, each change writes an audit row with before and after, a mechanic sees a reassignment within 3 seconds (VR-RL-12), and a stale edit is rejected with the existing 409 reload.
- [ ] Design it (spec): `/architect admin ticket editing`

### 19. Mechanic status updates · planned
WL-107. Mechanics move their own tickets forward from a phone.
**Done when:** only the assigned mechanic sees the control, only allowed transitions show, the server rejects anyone else, and each change is logged.
- [ ] Build it: `/develop mechanic status updates`

### 20. File upload & storage · planned · needs a decision · GA
WL-218. One private upload service for vehicle photos, proof and receipts.
**Done when:** JPG, PNG, HEIC and PDF up to a set size are accepted, files open only through authorized links, and each file records ticket, type, uploader and time.
- [ ] Design it (spec): `/architect file upload & storage`

### 21. Vehicle photos · planned
WL-209 and WL-210. Mechanics snap photos from the phone camera; reviewers see thumbnails and a full size viewer.
**Done when:** up to 5 photos per ticket upload with progress and retry, thumbnails show in Issue Details, and a mechanic can remove their own until the ticket closes.
- [ ] Build it: `/develop vehicle photos`

### 22. Proof of completion · planned
WL-211. No ticket is marked done without evidence.
**Done when:** Mark as Complete stays disabled without a proof file, the server rejects completion without one, and proof shows on the verification screen.
- [ ] Build it: `/develop proof of completion`

### 23. Chief Mechanic verification · planned
WL-212. Verify or reject finished work, with the verifier recorded.
**Done when:** finished tickets land in a verification queue, Verify closes and Reject returns to In Progress with a required comment, and the verifier's name and time are on the ticket and in reports.
- [ ] Build it: `/develop chief mechanic verification`
- Note (2026-10-25): Reject is the first backward move. Follow feature 16's rule for the spec 0007 checklist and "What fixed it" notes when a ticket goes back to In Progress.

### 24. Full ticket audit trail · planned · needs a decision
WL-219. Every ticket event logged in one consistent shape, so history and reports can trust it.
**Done when:** every event type in WL-219 writes actor, role, time, before and after, and note, and no entry can be edited or deleted from the UI.
- [ ] Design it (spec): `/architect full ticket audit trail`

### 25. Vehicle availability · planned
WL-501, built on Jira's proposed rules. A truck under repair can't be dispatched.
**Done when:** a vehicle turns Under Repair when its ticket is created, returns to Available when it closes, Admin can toggle it with a reason, and the history is kept per vehicle.
- [ ] Build it: `/develop vehicle availability`

## Slice 2: Mechanic workflow & notifications

Adds the alerts and hand offs around the core loop.

### 28. In-app notifications · planned · needs a decision
WL-304. The shared notification service every alert uses.
**Done when:** assignments, transfers, holds, verifications and deadline alerts create notifications, clicking one opens the ticket, and new ones appear without a reload.
- [ ] Design it (spec): `/architect in-app notifications`

### 29. Notification badge & queue counts · planned
WL-301. Unread count on the bell and counts on queue menus.
**Done when:** the bell shows the unread count (99+ above 99) updating without a refresh, and sidebar queues show their pending counts.
- [ ] Build it: `/develop notification badge`

### 30. Transfer requests · planned
WL-204. A mechanic asks to hand off a ticket; Admin approves or rejects.
**Done when:** a mechanic can request with a reason, only one request is pending per ticket, Admin approves with a new mechanic or rejects with a reason, and everyone involved is notified.
- [ ] Build it: `/develop transfer requests`

### 31. On hold for parts · planned · needs a decision
WL-208, built on proposed defaults. Pause a ticket for missing parts with the reason verified.
**Done when:** a mechanic sets the hold with parts and reason, a verifier approves or rejects it, hold time is tracked for reports, and held tickets stand out in lists.
- [ ] Design it (spec): `/architect on hold for parts`

### 32. Repair history timeline · planned
WL-205. A clickable timeline inside the ticket view, linked from My Repairs.
**Done when:** the timeline is built from the audit trail, entries expand to show details and files, it filters by event type, and mechanics see only their own tickets' history.
- [ ] Build it: `/develop repair history timeline`

### 33. Admin status override · planned
WL-108, built on Jira's proposed rules. Admin fixes a wrong status with a reason.
**Done when:** Admin can set any valid status with a required reason, the entry is marked Override in the timeline, and the mechanic is notified.
- [ ] Build it: `/develop admin status override`
- Note (2026-10-25): this is how you move a ticket back. Follow feature 16's rule for the spec 0007 checklist and "What fixed it" notes on any backward move.
