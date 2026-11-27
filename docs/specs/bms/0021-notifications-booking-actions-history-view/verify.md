# Verify: notifications, Booking view-only actions, History details, Approvals panel note · spec 0021

Steps derived from [index.md](index.md). Ticked items were checked on 2026-11-27 against the local stack (`docker-compose.shared.yml`, `docker-compose.bms.yml`, VMMS running) with the seed accounts, through the real gateway and services. Test bookings used `@example.com` customer addresses.

## Notifications: who gets what (live)

Booking service:

- [x] CS creates a booking → Operations: "Booking needs team assignment". Customer Service (who created it) and Admin don't get it
- [x] CS requests a cancellation → both Admins: "Cancellation needs review"
- [x] Admin approves it → CS: "Your cancellation request was approved", Operations: "Booking cancelled"
- [x] CS requests a reschedule, Admin rejects it → CS: "Your reschedule request was rejected", with the reason
- [x] WeLinc `booking.created` → Admin: "New booking received from WeLinc", Operations: "Booking needs team assignment"
- [x] WeLinc date change → Operations: "Rescheduled booking needs team assignment"
- [x] WeLinc cancellation → Operations: "Booking cancelled"
- [x] A WeLinc change after the booking is cancelled → Admin: "WeLinc booking change needs review"

Dispatch (through its outbox):

- [x] Operations assigns a team → the other Operations user: "Job order ready to distribute" (not the one who assigned it); the driver: "You're assigned as the driver of a trip"; the helper: "You're assigned as a helper on a trip"
- [x] Operations swaps a helper → the old helper: "You were removed from a trip"; the new one: assigned
- [x] Operations distributes the job order → the driver: "Job order distributed"
- [x] Admin approves a cancellation of an assigned trip → the driver and helper: "Your trip was cancelled"
- [x] A helper files an emergency covering their trip → Admin: "Emergency leave needs review"; Operations: "Crew conflict: reassign trip", naming the booking and helper
- [x] Admin rejects the emergency → the helper: "Your emergency leave was rejected", with the reason
- [x] A driver files leave → Admin: "Leave request needs review"; Admin rejects it → the driver: "Your leave was rejected", with the reason

Completion (through its outbox):

- [x] CS completes post-service → the other CS user: "Post-Service details ready to verify"
- [x] CS records a collection → Admin: "Collection needs review"; Admin verifies it → CS: "Your collection was verified"
- [x] CS requests a refund → Admin: "Refund needs review"; Admin rejects it → CS: "Your refund request was rejected", with the reason
- [x] Completion's `notification_outbox` rows end as `DELIVERED`

## Read state and privacy (live)

- [x] `POST /bms/notifications/:id/read` saves read for that person only and lowers their count by one; marking someone else's answers 404
- [x] `POST /bms/notifications/read-all` leaves nothing unread
- [x] Drivers see only their own notifications (through the gateway, with a `bms-mobile` token); CS sees nothing meant for Admin; Operations sees nothing meant for CS

## Customer emails (live, SMTP on)

- [x] Every email for the test bookings was queued and sent on the first try: confirmation, two "team assigned" (assign and reassign), "in transit", "delivered", "rescheduled" and "cancelled" (10 emails, all `SENT`)
- [ ] Retry when SMTP is down: covered by unit tests only (retry after a wait, `FAILED` after 8 tries, `SKIPPED` without SMTP)

## Web, in a browser (Edge, through the portal sign in)

- [x] The badge shows the server's unread count
- [x] A notification that arrives while the app is open pops a toast and raises the badge by one
- [x] The open bell lists it as unread; clicking it opens Approvals → Crew leave and marks it read on the server
- [x] Nothing about notifications is kept in `localStorage`
- [x] A second browser for the same person shows the same unread count; **Mark all read** there clears it, and the first browser shows 0 after a reload
- [ ] Admin → Booking: each row shows only the eye button (no ⋮), with a "View" tooltip; it opens the booking details. Served page checked; please look in the browser
- [x] Admin → Approvals → History: every row's View opens, including an approved cancellation (107 rows; before the fix the cancellation answered 409 "Approval item not found")

- [x] Approvals side panel: the served page no longer contains the notes (checked the module the web container serves after a restart)
- [ ] Approvals → Needs action: select a collection, a refund and a cancellation; no grey note above Reject and Verify / Approve. Please look in the browser

## Database

- [x] `prisma migrate deploy` applies the new migration in booking (`notifications`, `notification_reads`, `customer_emails`), dispatch and completion (`notification_outbox`)
- [x] Each migration only adds tables (checked with `prisma migrate diff` against the previous schema)

## Mobile

- [ ] Not in scope: the app still shows sample notifications (see rationale). The backend side it needs works: a driver's `bms-mobile` token reads `GET /bms/notifications`

## Commands

- [x] `welinc-backend-bms`: `npm run lint:ci`, `npm run typecheck`, `npm run build`, `npm test`: all pass (gateway 112, booking 114, dispatch 113, completion 99 tests)
- [x] `welinc-web-bms`: `npm run lint` (0 errors, 30 warnings, the same count spec bms/0019 recorded as already on `development`), `npm run typecheck`, `npm run build:prod` with the CI `VITE_*` values
- [ ] `welinc-web-bms`: `npm test` fails locally on unchanged `development` too (all 4 session test files: "Cannot read properties of undefined (reading 'config')"), so it says nothing about this change. Check it in CI.

## Test data left in the local database

- Bookings BN-20261127-00002 (cancelled), BN-20261127-00003 (completed and paid) and BN-20261127-00004 (WeLinc import, cancelled), all named "Spec 0020 check".
- Rejected requests: a reschedule on BN-20261125-00001, a ₱1 refund on DEMO-BN-0140, and leave and emergency requests for Edgardo Santos and Allan Domingo.
