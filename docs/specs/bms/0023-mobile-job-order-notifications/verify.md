# Verify: mobile job order notifications · spec 0023

Steps derived from [spec 0023 acceptance criteria](index.md). The backend has unit tests and local build checks; the mobile wording was checked by running the notice code on sample data. Nothing has been run through the gateway or on a phone yet.

## Build

- [x] Backend `npm run typecheck`, `npm run lint:ci`, `npm run build` and `npm test` pass locally (2026-11-28).
- [ ] Backend CI is green on the pull request.
- [x] The dispatch migration applies on the local database with existing assignments; the local dispatch service starts with 0 errors (2026-11-28).
- [ ] The dispatch migration applies on a fresh database.
- [x] `npx tsc --noEmit` passes in `welinc-mobile-bms`, and `npx expo export --platform android` bundles the app (2026-11-28).

## Unit tests (in-memory, no database)

- [x] Dispatch, `dispatch-notices.spec.ts`: first assignment; same team after a reschedule (schedule change only); one helper swapped; team changed without a new time; only garage or truck changed (no notice); a whole new team; helper moved to driver; dedupe keys stable per command; reschedule approval remembers the team and sends nothing; cancel approval tells the team and remembers nothing.
- [x] Booking, `notifications.spec.ts`: list items carry `bookingUuid` and `bookingNo`, null without a booking.
- [x] Mobile wording (compiled and run on sample notices, 2026-11-28): every row of "Notice wording" matches, `crew.dispatched` is hidden, nobody is named, the avatar is the person's own, an assignment before its job order falls back to the booking number, helpers get no reminder.

## Backend: who gets which notice (AC-2, AC-3, AC-4)

- [ ] First assignment: the driver and each helper get `crew.assigned`.
- [ ] Admin approves a reschedule: the team gets no notice, and `released_driver_id` / `released_helper_ids` hold the team.
- [ ] Operations assigns the rescheduled booking to the same team: each gets `crew.rescheduled` only; the released team columns are cleared.
- [ ] Assigned again with one helper swapped: the kept people get `crew.rescheduled`, the dropped helper `crew.unassigned`, the new helper `crew.assigned`.
- [ ] On an assigned booking, Operations changes only the dispatch time: each person gets `crew.rescheduled`.
- [ ] On an assigned booking, Operations changes only the garage or truck: nobody gets a notice.
- [ ] Admin approves a cancellation: each person gets `crew.trip_changed` (cancelled).
- [ ] Distributing the job order sends no notice to the team; Operations' "Job order ready to distribute" still appears.
- [ ] Retrying an assignment command sends no duplicate notices.

## Backend: list (AC-1)

- [ ] `GET /bms/notifications` with a driver's token returns `bookingUuid` and `bookingNo` on a team notice, and null for a notice without a booking.
- [ ] The web bell still lists and marks notifications as before.

## Phone: list and wording (AC-5, AC-6, AC-11)

- [ ] Assign a booking to the signed-in driver: "You've been assigned a new job order: **Job Order #…**, {pickup} to {delivery}." with the blue badge and the driver's own initials.
- [ ] The same for a helper: "You've been assigned as a helper on **Job Order #…**, …".
- [ ] Reschedule with the same team: "Schedule change: **Booking #…** pickup moved to **{date, time}**."
- [ ] Reassign to another team: the dropped person sees "Assignment change: **Booking #…** was reassigned. You're no longer assigned to it."
- [ ] Cancel: "**Booking #…** was cancelled. You're no longer assigned to it."
- [ ] No "distributed" notice appears, including ones stored before this change.
- [ ] No notice names who made the change.
- [ ] Account notifications (spec 0020) are still in the list, in time order with the others.
- [ ] The bell badge counts unread notices from every source.
- [ ] Seeder mode still shows the seeder notifications.

## Phone: refresh (AC-7)

- [ ] With the app open, a new assignment appears within about 45 seconds without any tap.
- [ ] With the BMS backend stopped, the saved BMS notices stay and account notices still update; with shared auth stopped, the reverse.
- [ ] Offline: the saved list stays.

## Phone: built on the phone (AC-8)

- [ ] A driver with an ongoing job order sees "**Reminder:** post your service completion for **Booking #…**."; it disappears after the form is sent.
- [ ] A helper on the same job order gets no reminder.
- [ ] A completed job order shows "**Booking #…** was marked completed. Thank you for your service!".
- [ ] These keep their time across syncs (they don't jump back to the top).

## Phone: opening and reading (AC-9, AC-10)

- [ ] Tapping an assigned or schedule change notice opens that job order; Back returns to Notifications.
- [ ] Tapping a reminder opens that job's post-service form.
- [ ] Tapping an assignment change or cancelled notice marks it read and opens nothing.
- [ ] A tapped notice shows as read on the web bell for the same account after the next sync.
- [ ] Mark all as read on the phone marks them read on the server.
- [ ] Offline: tap a notice, go online; it is read on the server after the next sync and never comes back unread.
- [ ] A notice read on another device shows as read on the phone after the next sync.
