# 0023. Rationale: mobile job order notifications

Decision record for [index.md](index.md).

## Context

After spec 0022, a driver signed in on the phone sees a newly assigned job order in Job Orders, but gets no notification about it. The backend side already works: when a trip is assigned, dispatch queues a `crew.assigned` notice for the driver and each helper (spec 0021), and the booking service stores it. In local testing on 2026-11-28, assigning DEMO-BN-0146 created "You're assigned as the driver of a trip" for the driver and the matching helper notice, both delivered from the dispatch outbox.

The gap is the app. Spec 0020 made a real sign-in build the Notifications tab from account activity in shared auth only, with a TODO to add job order notifications once the BMS backend had team member routes. The booking service's `GET /bms/notifications` already accepts `DRIVER` and `HELPER` and returns each person's own notices with per-person read state, so no new route is needed.

The app's Notifications screen already has a design, used by the seeder notifications: one sentence per notice with the key parts in bold, such as "Reminder: post your service completion for **Booking #…**", grouped under New and Earlier with a type badge. It also includes two notices the server never sends: the post-service reminder and "marked completed".

Facts that shape the design:
- The list items carry `id`, `kind`, `title`, `message`, `href`, `createdAt` and `read`, but not the booking, even though each notification row is linked to its booking.
- The server's titles and messages are written for the web bell ("You're assigned as the driver of a trip", "DEMO-BN-0146 · DEMO Client 146 — 2026-11-29").
- The app's job order id is the booking UUID (spec 0022).
- The phone's `notifications` table is replaced as a snapshot, already keeps read flags across refreshes, and has an unused `readSyncPending` column. Account notices use ids starting with `account-`.
- The server keeps notices for 60 days and returns at most 40.

## Options considered

### Where the app gets job order notifications

**Build every notice on the phone from job order changes: rejected.** The app could compare each new snapshot with the last and invent "assigned" or "cancelled" notices. It would miss changes between syncs or before the first sign-in, would disagree with the web bell, and would duplicate rules dispatch already has.

**A new team member route in dispatch: rejected.** Dispatch's notices already end up in the booking service, which owns notifications for every BMS role. A second route would mean two places holding the same notices.

**Read the existing `GET /bms/notifications`: chosen.** It already returns only the caller's notices, keeps read state per person, and is what the web bell reads, so phone and web agree on what happened and what was read.

### The wording of each notice

**Show the server's title and message as they are: rejected.** They are written for office staff on the web, repeat the client name, and don't match the app's notification design.

**Name who made the change, as the seeder did ("Admin Dela Rosa assigned you…"): rejected.** Who made the change doesn't matter to the driver, the server doesn't send it, and spec 0020 keeps office staff names off the phone.

**Write the message on the phone from the notice kind and the job order: chosen.** The phone knows the job order number, route, date and time, so a notice reads like the app's design ("You've been assigned a new job order: **Job Order #JO-2026-0001**, Pasig to Marikina.", "Schedule change: **Booking #BN-…** pickup moved to **Nov 14, 7:30 AM**."). The avatar shows the person's own initials, as in the design. An unknown kind falls back to the server's text, so a new backend notice is still seen without an app update.

### What a rescheduled or changed trip tells each person

Before this spec, approving a reschedule released the team and told everyone "Your trip was rescheduled — you're no longer assigned to it". When Operations assigned the booking again, dispatch had already forgotten the old team, so everyone got a new "You're assigned", including people who stayed on the trip, and nobody who was dropped heard about it. Changing only the dispatch time or garage on an assigned booking also re-sent "You're assigned" to everyone.

**Keep the team assigned through a reschedule: rejected.** The team's availability on the new date isn't known until Operations plots it again (leave, other trips, travel time), which is what Scheduling's re-plotting step exists for.

**Work it out on the phone from successive job order snapshots: rejected.** The phone only sees the trips it is on; between the approval and the new assignment the trip is on nobody's phone, so the phone can't tell "rescheduled with me" from "reassigned to someone else".

**Dispatch remembers the released team and compares on the next assignment: chosen.** Dispatch is the only place that knows both teams. It stores the released driver and helpers on the assignment, and when the booking is assigned again it sends each person the notice that matches what happened to them: a schedule change for those who stay, an assignment change for those taken off, and an assignment for those added. The same comparison now also covers a team or time change on an assigned booking.

**Tradeoff accepted:** between the approval and the new assignment, the trip isn't on anyone's phone and no notice explains why. Telling the team "rescheduled, waiting to be assigned again" would mean a second notice a few minutes before the real one for most reschedules.

### "Job order distributed" for the team

**Keep sending it: rejected.** Distribution is how the office marks on the web that the job order has gone out to the assigned team; for the driver and helpers it adds nothing to the assignment notice they already got. Drivers and helpers were its only recipients, so dispatch stops creating it, and the phone hides those already stored.

### How the app knows which booking a notice is about

**Parse the booking number out of the server's message: rejected.** Fragile, and the message text is meant for people.

**Add `bookingUuid` and `bookingNo` to each list item: chosen.** Both come from the booking the notice is already linked to. `bookingUuid` opens the job order; `bookingNo` names the trip in notices about trips the person was taken off, when the job order is no longer on the phone. The web bell ignores both.

### Reminder and "marked completed"

**Leave them out: rejected.** They are part of the app's notification design, and the reminder is the only nudge a driver gets to send the post-service form.

**Have the backend send them: rejected for now.** It would need a scheduler in dispatch or completion for reminders, more than this spec needs.

**Build them on the phone from job order state: chosen.** Unlike assignments, they depend only on the current state (an ongoing job without a sent form; a completed job), which the phone always has. The same logic already exists for seeder accounts. They keep the time they first appeared, so they don't jump back to the top on every sync.

### Storing several sources in one list

**Replace the whole list with every source each time: rejected.** If shared auth or the booking service is down, a snapshot without it would delete that source's saved notices from the phone.

**Separate tables per source: rejected.** The screen, badge and read handling would all need to merge tables.

**One table, reconciled per source by id prefix: chosen.** `account-`, `bms-` and `local-` rows are replaced independently, and a source that failed is skipped.

### Phone pop-ups while the app is closed

**Push notifications (Expo push or Firebase): out of scope.** Notifications are in-app only, like VMMS. Push would need a push service, device tokens on the server and native setup. The 45-second refresh from spec 0022 keeps the in-app list close to live while the app is open.

## Decisions and tradeoffs

- **Notices about trips the person left open nothing.** After `crew.unassigned` or `crew.trip_changed`, the job order is no longer on the phone. Tapping only marks it read.
- **A schedule change only when date or time changed.** A new truck or garage with the same people sends nothing; the card shows it at the next sync. Date and time are what the driver and helpers plan around.
- **Two columns for the released team, not a new assignment state.** A separate state (such as `RESCHEDULED`) would have to be added to every query that lists active or released assignments, including analytics. Two nullable columns are read in one place and cleared after use.
- **Notices sent before this spec are worded safely.** A stored "rescheduled — no longer assigned" notice reads as an assignment change, which is what it meant then, and stored "distributed" notices are hidden.
- **Messages use the job order as it is now.** If a job order's route changes after the notice, the notice shows the new route. This keeps the message consistent with what opens when it is tapped.
- **Pending reads are sent before reading the list.** Otherwise a notice read offline could come back unread for one sync. The phone also keeps `read = MAX(phone, server)`, so it never flips back to unread.
- **A 404 on a read clears it.** The notice was removed on the server (past 60 days, or its booking was deleted); retrying would never succeed.
- **Account and phone-built notices keep phone-only read state.** Shared auth has no read state for account activity, and phone-built notices don't exist on the server.
- **Same triggers as job orders, after them.** A notice is created when a job order changes, so refreshing both together makes them appear at the same time, and the phone-built notices use the newest job orders.
