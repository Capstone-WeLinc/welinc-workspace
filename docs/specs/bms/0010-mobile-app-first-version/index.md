# Mobile app for drivers and helpers: first version

Status: merged into `development` in `welinc-mobile-bms` (pull request #1).

The first working version of the BMS mobile app for drivers and helpers (team
members). Until now `welinc-mobile-bms` was a blank Expo scaffold. Touches only
`welinc-mobile-bms`. No change to `welinc-backend-bms`, `welinc-web-bms`, shared
auth, portal or the suite gateway. The app uses routes they already have.

The sign-in and forgot password flow follows the VRMS/VMMS mobile app
(`welinc-mobile-vrms_vmms`), which was only read, never changed.

## What the app does

| Tab | What a team member sees |
|---|---|
| Home | Greeting, today's and upcoming bookings; tapping one opens it in Job Orders |
| Set Availability | Weekly availability and leave requests |
| Job Orders | Assigned job orders with filters, and each one's details |
| Post Service Completion | The completion form for a finished job order (**drivers only**) |
| Notifications | New assignments and reminders, with an unread badge on the tab |
| Profile | Name, mobile number, change password, sign out |

Helpers see the same app without the Post Service Completion tab.

## Sign-in (shared auth, through the gateway)

The app talks to the suite gateway on port 3000 (`EXPO_PUBLIC_API_BASE_URL`):
`/auth/*` goes to shared auth and `/bms/*` to the BMS backend.

- Signs in with `POST /auth/mobile/login` using the `bms-mobile` client, which
  only admits `DRIVER` and `HELPER` accounts. Any other role is refused with
  "This app is for Driver and Helper accounts."
- An unverified email first gets a 6 digit code
  (`/auth/mobile/login/verify-email`, `.../resend`). Resend waits 60 seconds.
- Tokens are kept in the phone's SecureStore. A `401` refreshes them once
  through `POST /auth/token` (refresh token, client `bms-mobile`, audience
  `BMS`) and retries the request.
- The session is cleared only when shared auth refuses the refresh. Being
  offline, rate limited (`429`) or a server error (`5xx`) keeps the team member
  signed in.
- Opening the app again restores the saved session.
- Sign out ends the session on the server (`POST /auth/logout`).
- **Forgot password**: email → 6 digit code → new password, using
  `/auth/forgot-password`, `/auth/verify-otp` and `/auth/reset-password`. The
  new password needs 8 or more characters with upper and lower case, a number
  and a symbol, the same rule as shared auth.
- **Profile**: `GET /auth/me`, `PATCH /auth/profile` (name, mobile number) and
  `PATCH /auth/profile/password`. The email can't be changed in the app.

## Offline database (SQLite)

The app keeps its data in `bms_mobile.db` (Expo SQLite), so it works without
signal. Details are in `OFFLINE_DATABASE.md` in the repo.

| Table | Holds |
|---|---|
| `job_orders` | The team member's assigned job orders (server snapshot) |
| `post_service_records` | Completion forms, with a "waiting to send" flag |
| `weekly_availability` | Weekly availability |
| `leave_requests` | Leave requests |
| `notifications` | Notifications and their read state |
| `sync_metadata` | Last sync time and which user the data belongs to |

- Local data is kept on sign out, so unsent forms survive until the same
  person signs in again.
- When a **different** team member signs in on the same phone, the previous
  person's data is cleared first.

## Sync with the BMS backend

`SyncService` runs on sign-in, pull to refresh, when the app comes back to the
foreground and right after a completion form is saved:

1. **Send**: every completion form waiting to send is uploaded. If the server
   refuses one, it stays queued for the next sync.
2. **Download**: the team member's job orders replace the local snapshot.

**Switched off for now.** The BMS backend has no driver/helper routes for job
orders and post-service yet. `TEAM_JOB_ORDER_ROUTES_READY` in
`services/SyncService.ts` is `false`, so the sync sends and downloads nothing:
saved forms stay on the phone, and a real account sees no job orders. The
planned routes are `GET /bms/job-orders/mine` and
`POST /bms/job-orders/:id/post-service`. They need their own spec in
`welinc-backend-bms` first.

## What is connected and what is still on the phone

| Connected to the server | Still on the phone only |
|---|---|
| Sign-in, email code, forgot password, sign out | Job orders and post-service (waiting for the BMS routes above) |
| Profile name, mobile number, change password | Weekly availability |
| | Leave requests. Dispatch already has `/bms/crew-leave/self` (spec 0005), but the app's leave types don't match it yet |
| | Notifications (built on the phone from job orders) |

## Seeder mode

For testing without the backend, `EXPO_PUBLIC_USE_SEEDER_AUTH="true"` signs in
with the seeder accounts in `seeders/user.ts` and loads the seeder job orders.
Nothing is synced in this mode. `.env.example` has it set to `"false"`, and it
must never be `"true"` in a release build.

## Before release

- `app_released` for the `bms-mobile` client is still `false` in shared auth.
  It is turned on when the app ships, which is a shared auth change.

## Testing

- The app type-checks (`npx tsc --noEmit`).
- Checked by hand on a phone in seeder mode: sign-in, all tabs, the
  completion form and sign out. <!-- TODO: confirm, or remove this line -->

- Not yet tested against the running gateway and shared auth: sign-in with a
  real driver or helper, the email code, forgot password and profile updates.
- The repo has no CI or automated tests yet.

## Deploy notes

- App only, so it doesn't depend on any backend or web merge.
- Testing on a phone with Expo Go: set `EXPO_PUBLIC_API_BASE_URL` to the
  computer's Wi-Fi IP on port 3000 and allow that port through Windows
  Firewall.
