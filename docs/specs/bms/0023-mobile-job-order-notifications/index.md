# 0023. Mobile job order notifications for team members

**Date**: 2026-11-28
**Status**: Backend and mobile app implemented, not yet in pull requests; not yet tested on a phone
**Scope**: `welinc-mobile-bms`, and in `welinc-backend-bms` the team member notices in dispatch and the notifications list in booking. No change to `welinc-web-bms`, shared auth, portal or the suite gateway.

Decision history: [rationale.md](rationale.md). Verification plan: [verify.md](verify.md).

Follow-up to [0021. Notifications, booking actions and History view](../0021-notifications-booking-actions-history-view/index.md), which built the BMS notifications (the web bell) and the notices for drivers and helpers, and to [0022. Mobile job order and post-service sync](../0022-mobile-job-order-and-post-service-sync/index.md), which brought job orders to the mobile app.

## Summary

When a trip is assigned, changed or cancelled, the BMS backend creates a notification for each driver and helper on it, and the booking service lets them read their own (`GET /bms/notifications`). The mobile app never reads them: a real sign-in builds its Notifications tab only from account activity in shared auth (spec 0020). This spec has the app read the BMS notifications and show them in the app's own wording, adds the post-service reminder and "marked completed" notices built on the phone, opens the job order when one is tapped, and sends read state back to the server.

It also makes the notices say what really happened to each person. Today, approving a reschedule tells the whole team they are off the trip, and assigning it again tells everyone they are newly assigned, even those who stay. After this spec, dispatch compares the team before and after: people who stay on a rescheduled or retimed trip get a **schedule change**, people taken off get an **assignment change**, and only new people get **assigned**. The "job order distributed" notice is no longer sent to drivers and helpers; distribution remains a web status.

Notifications are in-app only: the list and badge update while the app is open, and nothing pops up on the phone.

## Requirements

**User stories**:
- As a driver or helper, I want to be told in the app when I am assigned to a trip, so that I don't have to keep checking Job Orders.
- As a driver or helper on a trip that was rescheduled, I want to be told the new date and time, and not that I was removed when I am still on it.
- As a driver or helper taken off a trip, I want to be told it was reassigned or cancelled.
- As a driver, I want a reminder to post the service completion for an ongoing job.
- As a driver or helper, I want to tap a notification and see that job order.
- As a driver or helper, I want a notification I have read to stay read, on the phone and on the server.

**Acceptance criteria**:
- **AC-1**: `GET /bms/notifications` returns `bookingUuid` and `bookingNo` (or null) on each item. Nothing else in the answer changes; the web bell keeps working.
- **AC-2**: When Admin approves a **reschedule**, dispatch remembers the team it releases and sends the team no notice. When Admin approves a **cancellation**, the team gets the cancelled notice, as today.
- **AC-3**: When a booking is assigned, dispatch compares the new team with the previous one (the team just released by a reschedule, or the team being replaced on an assigned booking):
  - a person on both teams gets `crew.rescheduled` if the service date or dispatch time changed, and nothing otherwise;
  - a person only on the previous team gets `crew.unassigned`;
  - a person only on the new team gets `crew.assigned`.
  With no previous team, everyone gets `crew.assigned`, as today.
- **AC-4**: Distributing a job order sends no notice to drivers or helpers. Operations' "Job order ready to distribute" notice is unchanged.
- **AC-5**: With a real sign-in, the Notifications tab shows the person's BMS notifications, the phone-built notices (AC-8) and the account notifications (spec 0020) in one list, newest first, under New and Earlier as today.
- **AC-6**: Each notice shows the wording in "Notice wording". No notice names who caused it. The avatar shows the signed-in person's initials, with the type badge. `crew.dispatched` notices already on the server are not shown.
- **AC-7**: BMS notifications are refreshed on the same triggers as job orders: sign-in, app open, back in the foreground, pull to refresh, when the phone gets internet back, and every 45 seconds while the app is in the foreground (spec 0022). If one source can't be reached, the notices already saved from it stay and the others still update.
- **AC-8**: The phone builds two notices from its job orders: a **Reminder** for each ongoing job order of a driver with no post-service record sent, and **marked completed** for each completed job order. A reminder disappears once the form is sent. Helpers never get reminders.
- **AC-9**: Tapping a notice whose job order is on the phone opens it: a reminder in Post Service Completion, the others in Job Orders, with Back returning to Notifications. A notice about a trip the person is no longer on is marked read and opens nothing.
- **AC-10**: Opening a BMS notice sends `POST /bms/notifications/:id/read`; Mark all as read also sends `POST /bms/notifications/read-all`. Offline, the read stays on the phone (`readSyncPending = 1`) and is sent on the next successful sync. A notice read on the web or another phone shows as read on the next sync.
- **AC-11**: The bell badge counts unread notices from every source. Seeder mode keeps the seeder notifications and calls no BMS route.

## Decision

Make dispatch decide, per person, whether a change is an assignment, a schedule change or an assignment change, because only dispatch knows the team before and after. Have the app read the existing BMS notifications route, and write each message from the notice `kind` and the job order on the phone. Store every notice in the same `notifications` table under an id prefix per source (`account-`, `bms-`, `local-`), and reconcile each source separately. See [rationale.md](rationale.md) for the options considered.

## Feature design

### Which notice each person gets

| What happens on the web | Stays on the trip | Taken off the trip | Newly on the trip |
|---|---|---|---|
| Operations assigns a booking for the first time | — | — | `crew.assigned` |
| Admin approves a reschedule | Nothing yet (dispatch remembers the team) | — | — |
| Operations assigns the rescheduled booking again | `crew.rescheduled` | `crew.unassigned` | `crew.assigned` |
| Operations changes the team on an assigned booking | `crew.rescheduled` if the dispatch time changed, else nothing | `crew.unassigned` | `crew.assigned` |
| Operations changes only the dispatch time | `crew.rescheduled` | — | — |
| Operations changes only the garage, truck or delivery type | Nothing | — | — |
| Admin approves a cancellation | — | `crew.trip_changed` (cancelled) | — |
| Operations distributes the job order | Nothing (web status only) | — | — |

A truck or delivery type change with the same people sends nothing: what the driver and helpers need to know (date, time, being on the trip) didn't change, and the job order card shows the new truck at the next sync.

Between an approved reschedule and the booking being assigned again, the trip is not assigned to anyone, so it is not on the team's phones. It comes back, with the schedule change notice, when Operations assigns it again.

### Notice wording

Bold parts are shown in **bold**. `{JO}` is the job order number and `{BN}` the booking number (from the job order on the phone, else from the server's `bookingNo`). `{route}` is "{pickup} to {delivery}", each the area (landmark) when there is one, else the address; it is left out with its comma when both are empty. `{when}` is the service date and pickup time as "Nov 14, 7:30 AM" (the dispatch time when there is no pickup time; only the date when there is neither).

| Source and `kind` | App type and badge | Message | Opens |
|---|---|---|---|
| Server `crew.assigned`, driver | `ASSIGNMENT` (blue list) | You've been assigned a new job order: **Job Order #{JO}**, {route}. | Job order |
| Server `crew.assigned`, helper | `ASSIGNMENT` (blue list) | You've been assigned as a helper on **Job Order #{JO}**, {route}. | Job order |
| Server `crew.rescheduled` | `SCHEDULE_CHANGE` (amber clock) | Schedule change: **Booking #{BN}** pickup moved to **{when}**. | Job order |
| Server `crew.unassigned` | `SCHEDULE_CHANGE` (amber clock) | Assignment change: **Booking #{BN}** was reassigned. You're no longer assigned to it. | Nothing |
| Server `crew.trip_changed`, cancelled | `SCHEDULE_CHANGE` (amber clock) | **Booking #{BN}** was cancelled. You're no longer assigned to it. | Nothing |
| Server `crew.trip_changed`, rescheduled (sent before this spec) | `SCHEDULE_CHANGE` (amber clock) | Assignment change: **Booking #{BN}** was rescheduled. You're no longer assigned to it. | Nothing |
| Server `crew.dispatched` (sent before this spec) | Not shown | — | — |
| Server, any other kind | `ASSIGNMENT` (blue list) | **{title}** {message}, as the server sends them | Job order, if on the phone |
| Phone, ongoing job without a sent form (drivers) | `REMINDER` (red bell) | **Reminder:** post your service completion for **Booking #{BN}**. | Post Service Completion form |
| Phone, completed job order | `COMPLETED` (blue check) | **Booking #{BN}** was marked completed. Thank you for your service! | Job order |

- Driver or helper for `crew.assigned`: the server's title says which ("…as the driver of a trip" / "…as a helper on a trip").
- Cancelled or rescheduled for `crew.trip_changed`: from the server's title.
- When `{JO}` isn't on the phone yet, "Job Order #{JO}" becomes "**Booking #{BN}**".
- The message is written again at every sync, from the job order as it is on the phone then. An assignment that arrives before its job order reaches the phone shows "**Booking #{BN}**" and opens nothing; the next sync rewrites it with the job order number and makes it open.

### Backend: dispatch

- **Remember the released team.** New nullable columns on `dispatch_assignments`: `released_driver_id` (uuid) and `released_helper_ids` (text[], default empty). The reschedule approval effect (`POST /internal/dispatch/approvals/:eventId`, type `reschedule`) copies the confirmed team into them before releasing the assignment, and sends no team notice. A cancellation sends `crew.trip_changed` (cancelled) as today and remembers nothing.
- **Compare on assignment.** `confirmAssignment` takes the previous team from the confirmed assignment being replaced, or else from `released_*`. It sends the notices in "Which notice each person gets", then clears `released_*`. A schedule change is detected by comparing the service date and dispatch time with the previous assignment's.
- **New kind** `crew.rescheduled`: title "Your trip has a new schedule", message `{bookingNo} — {date}, dispatch at {time}`, linked to the booking.
- **`crew.unassigned`** keeps its kind; its title becomes "Your trip was reassigned".
- **`distributedNotices`** is removed; distributing a job order queues no team notice.
- Each notice keeps a dedupe key per person and assignment command, as today, so a retried command never sends twice.

### Backend: booking

`NotificationsService.list` reads each row's booking (the `booking_uuid` relation from spec 0021) and adds `bookingUuid` and `bookingNo` to the item. Both are null for a notice without a booking. The web bell ignores the extra fields.

### Where each notice comes from (phone)

| Source | Id | `createdAt` | Read state |
|---|---|---|---|
| Account activity (spec 0020) | `account-<event id>` | Server time | Phone only, as today |
| BMS notifications | `bms-<server id>` | Server time | Phone and server (AC-10) |
| Built on the phone | `local-reminder-<job order id>`, `local-completed-<job order id>` | The first time the phone built it; kept on later syncs | Phone only |

A phone-built notice is removed when its condition ends (the form was sent, or the job order left the phone).

### Sync (phone)

`stores/notificationsStore.ts`, for a real sign-in:

1. **Send pending reads first.** Each `bms-` notice with `readSyncPending = 1` is sent to `POST /bms/notifications/:id/read`. A 2xx or 404 (the notice is gone) clears the flag; anything else keeps it for the next sync.
2. **Read both server lists**, in parallel: account activity (as today) and `GET /bms/notifications`.
3. **Build the phone notices** from the job orders and post-service records on the phone.
4. **Reconcile per source**, in one transaction: each source replaces only rows with its own id prefix. A server source that failed is skipped, so its saved rows stay.
5. Read state: `read = MAX(phone, server)`, as today.

The notifications refresh first refreshes the job orders, then runs the steps above, so phone-built notices and the wording use the newest job orders. `App.tsx` calls it on the foreground, the reconnect and the 45-second timer, and the Notifications tab on pull to refresh. Concurrent refreshes share one run.

The server answers at most 40 notices from the last 60 days (spec 0021). Older ones drop off the phone at the next sync, the same as on the web bell.

### Read state (phone)

| Action | Phone | Server |
|---|---|---|
| Tap a `bms-` notice | `read = 1`, `readSyncPending = 1` | `POST /bms/notifications/:id/read`; on success `readSyncPending = 0` |
| Mark all as read | All `read = 1`; `bms-` ones `readSyncPending = 1` | `POST /bms/notifications/read-all`; on success all `readSyncPending = 0` |
| Offline | Same as above | Sent on the next sync (step 1) |
| `account-` and `local-` notices | `read = 1` | No server read state; stays on the phone |

## API and data impact

| Service | Change |
|---|---|
| dispatch | `dispatch_assignments.released_driver_id`, `released_helper_ids` (one migration); new kind `crew.rescheduled`; `crew.unassigned` title; no `crew.dispatched`; no team notice on reschedule approval |
| booking | `GET /bms/notifications` items gain `bookingUuid` and `bookingNo` |
| mobile | Reads `GET /bms/notifications`; sends `POST /bms/notifications/:id/read` and `POST /bms/notifications/read-all` |

The phone's `notifications` table already has every column needed (`type`, `message`, `jobOrderId`, `driversOnly`, `readSyncPending`); `DATABASE_VERSION` stays 5.

## Security and failure behavior

- The routes take the person only from the verified token; the app sends no user id. The server already limits the list to the caller's own and role notices (spec 0021).
- Team notices are queued in the same transaction as the assignment change, through the existing dispatch outbox, so a notice is never sent for a change that didn't happen.
- A 401 after token refresh signs the person out, as for the other syncs.
- A failed list read leaves that source's saved notices as they are (AC-7).
- When a different user signs in on the phone, the previous user's notifications are cleared, as today (spec 0010).

## Affected repositories

| Repo | File | Change |
|---|---|---|
| backend | `bms-dispatch-service/prisma/schema.prisma`, `prisma/migrations/20261128150000_released_team` | `released_driver_id`, `released_helper_ids` |
| backend | `bms-dispatch-service/src/notifications/dispatch-notices.ts` | Per-person assigned / rescheduled / unassigned notices; `crew.unassigned` title; `distributedNotices` removed |
| backend | `bms-dispatch-service/src/notifications/dispatch-notices.spec.ts` | New: each row of "Which notice each person gets", role change, dedupe keys, reschedule and cancel approval effects |
| backend | `bms-dispatch-service/src/dispatch/dispatch.service.ts` | Previous team from the confirmed or released assignment; schedule change detection; clears the released team; no notice on distribution |
| backend | `bms-dispatch-service/src/dispatch/internal-dispatch.controller.ts` | Reschedule approval remembers the team and sends no team notice |
| backend | `bms-booking-service/src/notifications/notifications.service.ts`, `notifications.spec.ts` | `bookingUuid` and `bookingNo` on list items, with a test |
| mobile | `services/BmsNotificationsService.ts` | New: reads the BMS list, writes the messages (table above), sends reads |
| mobile | `utils/jobOrderNotices.ts` | New: builds the reminder and completed notices from job orders |
| mobile | `stores/notificationsStore.ts` | All three sources, pending reads first, read calls on tap and Mark all as read; refresh syncs job orders first |
| mobile | `repositories/NotificationRepository.ts` | Reconcile one source at a time (by id prefix), keep the first `createdAt` of phone-built notices, list and clear pending reads |
| mobile | `App.tsx` | Foreground, reconnect and 45-second triggers call the notifications refresh |
| mobile | `services/AccountNotificationsService.ts`, `seeders/notifications.ts` | Comments only |

The avatar uses the signed-in person's name as `actorName`, and a notice without a job order to open was already only marked read, so `screens/NotificationsScreen.tsx` needs no change.

## Deploy notes

- Merge and deploy the backend first, and run the dispatch migration (`prisma migrate deploy`) before starting the new dispatch service. Until the backend is live, the app still shows the BMS notices, but with the server's own text, and tapping one can't open its job order.
- In the local Docker setup, after pulling the backend: `docker exec welinc_bms_dispatch npx prisma migrate deploy`, `docker exec welinc_bms_dispatch npx prisma generate`, then `docker restart welinc_bms_dispatch`.
- A reschedule approved before this change has already released its team without remembering it; when it is assigned again, everyone gets `crew.assigned`.
- No phone database change and no new native module, so a Metro reload is enough on a phone that already has the spec 0022 development build.
