# Notifications from the backend, Booking view-only actions, History details fix, Approvals panel note

Status: pushed, not yet in a pull request. Backend branch: `BMS/notifications-and-admin-fixes` in `welinc-backend-bms` (into `development`); web branch: `BMS/notifications-and-admin-fixes` in `welinc-web-bms` (into `development`); workspace branch: `docs/bms-notifications-and-admin-fixes` (into `main`).

Decision history: [rationale.md](rationale.md). Review checklist: [verify.md](verify.md).

Touches `welinc-backend-bms` (booking, dispatch and completion services, and the BMS gateway's routes) and `welinc-web-bms` (the notification bell, the Admin Booking page, the Approvals side panel). Three new database migrations, one per service. `welinc-mobile-bms` is not changed.

## 1. Notifications are written by the backend

**Problem:** the bell had no backend. Every 15 seconds the browser downloaded the same lists the pages use (bookings, approvals, schedules, job orders and so on), compared them with a copy it kept in `localStorage`, and guessed what was new. Read and unread lived in one browser only, nothing was kept while the app was closed, two changes between checks showed as one, the rules for who gets what lived in the web app, and drivers and helpers had nothing real (the mobile app shows sample data).

**What it does:**

- The **booking service owns the notifications**. A new `notifications` table holds each one, for a role (everyone with that role) or for one person. `notification_reads` records who has read which, so read state follows the person to any browser or device.
- A notification is written **in the same database transaction** as the change it describes, so it exists exactly when the change does.
- **Dispatch and Completion** have their own databases, so each gets a small `notification_outbox` table. They write the notification there in the same transaction, and a timer delivers it to the booking service every 5 seconds. If Booking is down, delivery is retried (10 s, 20 s, 40 s … at most every 10 minutes). Each notification has a fixed key, so a repeated delivery never adds a duplicate.
- The person who caused a notification doesn't see it (an Admin who approves something isn't told they approved it).
- Notifications are kept 60 days. One whose booking is deleted goes with it.

**Who is told what:**

| Who | When | Opens |
|---|---|---|
| Admin | New booking received from WeLinc | Booking |
| Admin | A WeLinc change arrived for a booking already dispatched, paid or closed | Booking |
| Admin | Reschedule or cancellation needs review | Approvals → Bookings |
| Admin | Collection needs review | Approvals → Collections |
| Admin | Refund needs review | Approvals → Refunds |
| Admin | Leave request / emergency leave needs review | Approvals → Crew leave |
| The CS user who asked | Their reschedule, cancellation, collection or refund was approved, verified or rejected (with the reason) | My Submissions |
| Customer Service | Post-Service details ready to verify | Post-Service |
| Operations | A new booking needs team assignment | Scheduling |
| Operations | A rescheduled booking needs team assignment again | Scheduling |
| Operations | A booking was cancelled | Scheduling |
| Operations | Job order ready to distribute | Job Order |
| Operations | Crew conflict: someone on leave still holds a trip that day | Scheduling |
| The driver or helper | Assigned to a trip, removed from a trip (reassignment), job order distributed, their trip cancelled or rescheduled, their leave approved / confirmed / rejected | (mobile app, later) |

**API (through the gateway, `/bms/notifications`, booking service):**

| Route | What it does |
|---|---|
| `GET /notifications` | The signed-in person's last 40 notifications, newest first, each with `read`, plus the `unread` count |
| `POST /notifications/:id/read` | Marks one as read for this person (404 if it isn't theirs) |
| `POST /notifications/read-all` | Marks all of theirs as read |
| `POST /internal/notifications` | Service key only, not reachable through the gateway: Dispatch and Completion deliver here |

Admin, Customer Service, Operations, Driver and Helper may call the three public routes, so the mobile app can use them later. Reading notifications is not written to the Activity Logs.

**The web bell:**

- Looks the same. It now asks `GET /notifications` every 15 seconds while the tab is visible, and when the window gets focus.
- Clicking a notification marks it read on the server and opens its page. **Mark all read** is saved on the server too.
- A toast still pops up for notifications that arrive while the app is open.
- Nothing about notifications is stored in `localStorage` any more.

**Not changed:** the mobile app. Spec [bms/0020](../0020-mobile-profile-notifications-and-availability/index.md) shows account notifications there (from shared auth's activity) and notes that job order notifications need BMS routes. `GET /bms/notifications` is that route: it already accepts a `bms-mobile` driver or helper token. Showing these in the app, and phone push, are left for a later spec.

## 2. Customer emails are queued and retried

**Problem:** a customer email (booking received, rescheduled, cancelled, team assigned, in transit, delivered) was sent once, during the request. If SMTP failed, the email was only logged and lost.

**What it does:**

- Each email is rendered and saved in a new `customer_emails` table, then sent by a timer (every 30 seconds, and straight away after it is queued).
- A failed send is retried after 1, 2, 4, 8 … minutes (at most an hour apart), up to 8 tries, then marked `FAILED` with the last error.
- With SMTP not configured, emails are marked `SKIPPED` instead of piling up.
- Each email is leased while it is being sent, so two copies of the service never send the same one.
- Sent, skipped and failed rows are deleted after 30 days.
- What the emails say is unchanged.

## 3. Admin Booking: View only

**Problem:** the Actions menu (⋮) on the Admin Booking page offered View, Edit, Reschedule and Cancel. Admin should only view bookings here.

**What it does:**

- Each row shows only the **View** (eye) button. Because there is a single action, the ⋮ menu is gone, following spec [bms/0016](../0016-scheduling-filter-actions-subcon/index.md) ("one action, no ellipsis"): the same button style, a tooltip and a screen-reader label.
- The Edit, Reschedule and Cancel dialogs and their code are removed from this page.

## 4. Approvals History: View details failed to load

**Problem:** on Admin → Approvals → History, the View icon on some rows showed "Unable to load approval details." The backend refused to show an Admin any booking request whose booking is now Cancelled. That rule was meant to hide pending requests on bookings that were cancelled another way, but it also caught every approved cancellation (approving it cancels the booking) and any other decided request whose booking was later cancelled.

**What it does:**

- Only a **pending** request on a cancelled booking is refused (as before, it isn't in the Needs action list either). Decided requests always open from History.
- Collections, refunds and crew leave already opened correctly and are unchanged.

## 5. Approvals side panel: no note above the buttons

**Problem:** on Admin → Approvals → Needs action, the side panel showed a line of small grey text above the Reject and Verify / Approve buttons, such as "Verify confirms this payment and includes it in Daily Sales."

**What it does:**

- The note is gone for every request type that had one: collections ("Verify confirms this payment and includes it in Daily Sales."), refunds ("Approval creates the linked reversal against the original payment.") and cancellations ("Cancelling withdraws pending collections. Any verified payment creates a refund request for review.").
- The buttons, what they do, and the rejection reason step are unchanged.

## Removed

- The bell's browser-side snapshots and its `localStorage` key (`welinc_notifications_v1_*`).
- `GET /integrations/welinc/notifications` and `GET /integrations/welinc/notifications/deleted` (only the old bell used them).
- Edit, Reschedule and Cancel on the Admin Booking page.
- The note above the decision buttons in the Approvals side panel.

## Testing

- `welinc-backend-bms`: new tests for the notification input checks, who sees what, reading and mark-all, the booking notices, the customer email queue (send, retry, give up, skipped), the outbox (deliver, retry, one refused item), crew leave and refund notifications, the gateway route, and opening an approved cancellation from History. All suites pass in booking, dispatch, completion and the gateway.
- Live check against the local stack: see [verify.md](verify.md).

## Deploy notes

- Run `npx prisma migrate deploy` in `bms-booking-service`, `bms-dispatch-service` and `bms-completion-service` (the hosted migration jobs do this). Each migration only adds tables.
- No new settings. Dispatch and Completion use the `BOOKING_API_URL` and `BMS_INTERNAL_SERVICE_KEY` they already have.
- After the deploy the bell starts empty: older activity is not copied in.
