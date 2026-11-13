# Account screens on welinc-auth

The reference behind the profile, activity and admin items in [move-vmms.md](move-vmms.md) and [move-bms.md](move-bms.md). Open the section a checklist item links to; you don't need to read this page top to bottom.

Every route here goes through the gateway at `/auth` with the signed in person's own user token. A service token gets 403 `WRONG_TOKEN_USE`. The full route list is in contract [0001](../specs/_root/0001-shared-services-contract/index.md), sections 10 and 10a. The specs behind this page are suite specs [0011](../specs/_root/0011-account-activity-audit/index.md) (activity), [0012](../specs/_root/0012-profile-extras/index.md) (deletion) and [0013](../specs/_root/0013-suite-admin-model/index.md) (the portal admin section).

| Part of your app | After the move | Section |
|---|---|---|
| Users page (accounts) | Deleted; the menu item opens the portal's admin section | [Admin pages](#admin-pages-move-to-the-portal) |
| Admin calls (`/auth/activity` and the rest) | May answer 403 `ADMIN_CODE_REQUIRED` | [The admin code answer](#the-admin-code-answer) |
| Pick lists (mechanics, drivers, helpers) | Skip temporary roles | [Temporary roles](#temporary-roles-in-pick-lists) |
| Profile: recent activity | `GET /auth/profile/activity` | [Activity](#activity) |
| Admin audit or activity page | Your own rows plus `GET /auth/activity` | [Activity](#activity) |
| Profile: delete account | Password recheck, then a deletion request | [Account deletion](#account-deletion) |
| Names copied from the directory | Rewritten when a person is erased | [After an erasure](#after-an-erasure) |

## Admin pages move to the portal

Account management lives in one place: the portal's admin section (`<portal>/admin`). A system admin there sees only their own system's people and gives only their own system's roles. Above them sit 1 to 3 **suite admins**, who manage every account but hold no system role, so they see none of your data. A suite admin who needs to look inside your system gives themselves one of your roles for 1 to 8 hours with a written reason, and your admins get an email.

### Your menu item

| | Menu item today | Becomes |
|---|---|---|
| VMMS | "User Management" (`/users`) in `src/components/Sidebar/Sidebar.tsx` | a link to `<VITE_PORTAL_URL>/admin/people?system=VMMS`, opened in a new tab |
| BMS | "User Accounts" (`/admin/users`) in the Administration section of `src/lib/auth.ts` | a link to `<VITE_PORTAL_URL>/admin/people?system=BMS`, opened in a new tab |

Deep links that work: `/admin/people?system=<SYS>` (the list), `/admin/people/<id>?system=<SYS>` (one person and every action on them), `/admin/people/new?system=<SYS>` (add someone). An admin of two or more systems gets a system switcher. `VITE_PORTAL_URL` (local default `http://localhost:8000`) goes in your web app's `.env.example`; it is an address, never a secret.

### What to delete

The portal does everything your Users page does: create (including attaching an existing person), edit name, email and roles, deactivate, unlock, send a setup or reset code, see and end sessions, activity, delete, restore, and the deletion requests.

- **VMMS:** delete `src/pages/UserManagement/UserManagement.tsx` and its `/users` route in `src/App.tsx`. In `src/lib/api/userService.ts`, keep `getUsers()` until `CreateSchedule.tsx` reads mechanics from your directory copy (move step 5), then remove it with the other account helpers (`createUser`, `updateUser`, `updateUserRole`, `updateUserStatus`, `unlockUser`, `resetUserPassword`, `getLoginActivity`).
- **BMS:** `src/pages/admin/UserManagement.tsx` does two jobs. The account half (the `/auth/users*` calls in `src/lib/api/userService.ts`) goes. The crew half (drivers and helpers through `src/lib/api/crewService.ts`) is BMS work data, so **keep it** on its own page (for example "Crew") before you delete the account half. Then point the `/admin/users` route in `src/App.tsx` at the crew page or remove it.

Rule of thumb: anything about the work a person does stays in your system; anything about their account moves to the portal. Your profile pages stay: they use the person's own routes below.

### The admin code answer

Every admin confirms each portal sign in with an emailed code. Until they do, any admin call (`/auth/activity`, sessions, deletion requests) answers **403 `ADMIN_CODE_REQUIRED`**. Show "Confirm your sign in in the portal" with a link to `<portal>/admin`; once the code is entered there, the same tokens work again with no new sign in.

Handle it once, where every request passes:

- **VMMS:** `apiRequest` in `src/lib/api/httpClient.ts`, next to the 401 handling. The `ApiError` it throws carries `data.code`.
- **BMS:** the response interceptor in `src/lib/api.ts`, before the final `Promise.reject`. The code is at `error.response.data.code`.

VRMS shows the same message on its team page if you want something to copy. `/auth/login` can also answer `{ status: "SIGN_IN_CODE_REQUIRED" }`, but after the move your app never calls `/auth/login` (the portal does), so you don't handle it.

### Temporary roles in pick lists

A suite admin with temporary access looks like anyone holding that role. The directory names those codes: `DirectoryUser.temporaryRoles` lists the codes in `roles` that come from a live temporary grant (empty for everyone else). Wherever a role makes someone pickable for work (VMMS mechanics on a schedule, BMS drivers and helpers on a dispatch), leave out the codes in `temporaryRoles`, so a suite admin looking around is never given a job. When the grant ends, a `roles_changed` change removes the role.

### The central permission matrix (optional)

You may keep checking roles in your own code. If you want role to permission rules that a suite admin edits in the portal, do it the way VRMS does:

1. Your code still declares the permission keys and runs every check itself.
2. Add a `permissions` list (key, label, group, description, defaults per role, optional locked roles) to `welinc-auth/prisma/catalog/<system>.ts` through a pull request.
3. Your backend's client row gets the `permissions.read` scope (`welinc-auth/prisma/seeds/clients.seed.ts`).
4. Your backend polls `GET /auth/permissions/<SYS>` about every 60 s with `If-None-Match`, replaces its copy on a 200, keeps it on a failure, and refuses a copy that grants nothing to anyone. Permissions never go in the token.

The job to copy is `welinc-backend-vrms/src/auth/permissions/sync/`.

### What admins will notice

- An emailed code at each portal sign in. Locally, set `ADMIN_SIGN_IN_CODE=false` in welinc-auth's `.env`, or leave `SMTP_*` blank and read the code from the auth log.
- Adding an admin role, or acting on another admin's account, asks for their own password first.
- An email whenever someone gains or loses admin in their system, a suite admin steps in with temporary access, or the matrix is edited.
- Nobody can change their own roles or admin standing.

## Activity

welinc-auth records every sign in, session, emailed code and account change in one log. Your backend never reads it for itself; your web app calls it with the person's token.

| Route | Who | What it answers |
|---|---|---|
| `GET /auth/profile/activity` | anyone signed in | Their own events from every system |
| `GET /auth/activity` | your system's admin | Your system's feed: your system's events for anyone (former members too), plus account wide events of your current members. 60 calls a minute per admin |
| `GET /auth/activity/catalog` | anyone, no token | English labels for every category, type and reason. Cache it 5 minutes (it sends `Cache-Control` and an `ETag`). Never hard code labels |

**Paging.** Every list answers `{ data, nextCursor }`, newest first. Pass `nextCursor` back as `cursor`; `null` means the end. `limit` is 1 to 100 (default 50). There are no totals or page numbers, so a "Showing N of M" footer or numbered pages become a Show more button.

**Filters.** `category` and `type` take comma lists (at most 20 values). `from` and `to` are `YYYY-MM-DD` Manila days, both inclusive. The feed also takes `userId`, `q` (2 or more characters of name or email) and `address` (one exact IP). Bad values answer 400 `VALIDATION_FAILED`; a cursor you didn't get from these routes answers 400 `INVALID_CURSOR`.

### One event

```json
{
  "id": "…", "category": "SIGN_IN", "type": "SIGN_IN_FAILED", "reason": "WRONG_PASSWORD",
  "system": null, "sessionId": null, "client": null,
  "field": null, "oldValue": null, "newValue": null, "attemptsLeft": 3,
  "address": "112.198.0.1", "localNetwork": false,
  "device": "Chrome on Windows", "userAgent": "Mozilla/5.0 …",
  "country": "PH", "network": "Globe Telecom",
  "createdAt": "2026-11-12T01:19:53.301Z",
  "actor": { "kind": "SYSTEM" }
}
```

- `category` is `SIGN_IN`, `SESSION`, `CODE` or `ACCOUNT`; the catalog lists every `type`.
- `system` is the system the event belongs to; `null` means account wide.
- `actor.kind` is `SELF`, `ADMIN` or `SYSTEM` (nobody, such as an idle timeout). On the feed the actor also has `id` and `name`, and each event has `user: { id, name, email }`. On the person's own route an admin shows only as "An admin": use the catalog's `labelAdmin`.
- `country` and `network` are filled only when hosted. Locally every row is `localNetwork: true` (show "Local network"). Wherever you show a place, credit "IP data by DB-IP" linking to `https://db-ip.com`.

### VMMS

| Today | Becomes |
|---|---|
| `GET /auth/me/login-activity` on Profile (last 10) | `GET /auth/profile/activity?limit=5` |
| `GET /auth/audit-logs?source=login` (the "Logins" choice) | `GET /auth/activity?category=SIGN_IN`, for VMMS Admins only |
| `GET /auth/audit-logs?source=all` | Your own vehicle, work order, schedule and fuel rows, plus `GET /auth/activity`. Simplest: show "Accounts" as its own tab, since two cursors don't merge cleanly |

| VMMS field | welinc-auth |
|---|---|
| `event` `SUCCESSFUL_LOGIN` | `type` `SIGNED_IN` |
| `event` `FAILED_LOGIN` | `type` `SIGN_IN_FAILED`, `reason` `WRONG_PASSWORD`, `ACCOUNT_INACTIVE` or `ACCOUNT_LOCKED` (`attemptsLeft` is new) |
| `event` `ACCOUNT_LOCKOUT` | `type` `LOCKED_OUT`, written once, on the 5th wrong password |
| `event` `PLATFORM_ACCESS_DENIED` | `type` `SIGN_IN_FAILED`, `reason` `NO_SYSTEM_ACCESS` or `APP_NOT_ALLOWED` |
| `event` `LOGOUT` | `type` `SIGNED_OUT` (other session ends are `SESSION_ENDED` with a `reason`) |
| `ipAddress` | `address` |
| `deviceType` (Desktop, Mobile, Tablet) | `device` ("Chrome on Windows", or the phone's name) |
| `email`, audit `actor` | the feed's `user.email`, `actor.name` |
| audit `action`, `entity`, `details` | the catalog label for `type`, plus `device` and `address` |

A failed sign in for an email with no account is never stored. Account changes (`CREATED`, `ROLE_CHANGED`, `UNLOCKED` and the rest) come for free now.

### BMS

| Today | Becomes |
|---|---|
| `GET /auth/profile/activity`, answered by `bms-gateway` from `user_activity_logs` | the same path, served by welinc-auth: remove the gateway route and its SQL. The body changes, see below |
| `GET /activity-logs` (service audits merged with SQL on the auth database) | Your service audits plus `GET /auth/activity`, for BMS Admins only. No system reads the auth database |

| BMS field | welinc-auth |
|---|---|
| `action` `LOGIN` | `type` `SIGNED_IN` |
| `action` `PASSWORD_CHANGE` | `type` `PASSWORD_CHANGED` |
| `action` `LOGOUT_ALL` | `type` `SESSIONS_ENDED` |
| `action` `PROFILE_UPDATE` | `type` `UPDATED` with `field`, `oldValue`, `newValue` |
| `action` `DELETION_REQUEST` | `type` `DELETION_REQUESTED` |
| `deviceInfo` (raw user agent) | `userAgent`, or `device` for the label |
| `location` (free text) | `country` and `network` ("Philippines · Globe Telecom", or "Local network") |
| `ipAddress` | `address` |
| "Current session started" | the `SIGNED_IN` whose `sessionId` is your session's `sid` |
| `userName`, `email` | the feed's `user.name`, `user.email` |
| `role` | not on events: look it up from the directory, or drop the column |
| `search`, `from`, `to` | `q`, `from`, `to` |
| `action` filter chips | `category` and `type`. Today's "Logins" chip sends `Logged in`, which never matches, so use `type=SIGNED_IN` |
| `page`, `pageSize`, `total` | `cursor`, `limit`, Show more |

## Account deletion

1. The person types their password again. `POST /auth/profile/verify-password` answers a reauth token: 5 minutes, one use, same session only.
2. They send the request with it. Their account keeps working while it waits.
3. Any admin of a system they hold a role in approves or rejects it in the portal. A reject needs a note the person sees.
4. Approval closes the account at once: deleted, every session ended.
5. After 30 days (`ACCOUNT_ERASURE_GRACE_DAYS`) welinc-auth erases their name, email, phone and picture. Until then an admin can restore it; a restored account comes back turned off.

| Step | Call | Answer | Errors to handle |
|---|---|---|---|
| Recheck the password | `POST /auth/profile/verify-password` `{ password, purpose: "ACCOUNT_DELETION" }` | 200 `{ reauthToken, expiresAt }` | 400 `WRONG_PASSWORD` with `attemptsLeft`; 403 `ACCOUNT_LOCKED` (the 5th wrong try, same counter as sign in); 429 `RATE_LIMITED` |
| Ask for deletion | `POST /auth/profile/deletion-request` `{ reauthToken, reason? }` (up to 500 characters) | 201, the request with `status: "PENDING"` | 403 `REAUTH_REQUIRED` (recheck again); 409 `DELETION_PENDING`; 409 `LAST_ADMIN` |
| Show the state | `GET /auth/profile/deletion-request` | `{ request }`, the latest or `null` | none |
| Cancel | `DELETE /auth/profile/deletion-request` | 204 | none |

`request` is `{ id, status, reason, requestedAt, decidedAt, decisionNote, eraseAfter }`. Show `PENDING` with a Cancel button and `REJECTED` with `decisionNote` and an Ask again button; after `CANCELLED` or `RESTORED` the person may ask again.

The email change (`POST /auth/profile/email`) and password change (`PATCH /auth/profile/password`) answer a wrong current password the same way: 400 `WRONG_PASSWORD` with `attemptsLeft`, then 403 `ACCOUNT_LOCKED`.

Admins approve, reject and restore in the portal, so your app builds no admin deletion screens.

**What each profile page changes:**

- **BMS** (`ProfilePage.tsx`): add `purpose: "ACCOUNT_DELETION"` to the verify call and keep `reauthToken` from the answer instead of reading `{ valid }`. Send `{ reauthToken, reason }` to the deletion request. Read the state from `GET /auth/profile/deletion-request` instead of `deletionRequestStatus`.
- **VMMS** (`Profile.tsx`): wire the existing delete dialog to the calls above. Remove the phone verification calls and the Semaphore code: no system sends SMS, and the phone is a plain field saved through `PATCH /auth/profile`.

## After an erasure

The directory (`/auth/directory/*`) marks an erased person with `DirectoryUser.erased: true`, sent as one `updated` change; key on the flags (`deleted`, `isActive`, `erased`), never on the change type. Wherever you copied a name or email for that user id, rewrite it: names become `Deleted user` and emails `deleted-<id>@erased.invalid`. VRMS does it in `welinc-backend-vrms/src/modules/vrms/directory/erasure-rewrite.ts`. The directory has no `phoneVerified` any more.

## Test accounts

- `suite.admin@welinc.com` (`admin1234`): the suite admin. No system roles, so the portal shows the no systems screen with **Admin** in the top bar.
- Your system's admins and the `multi.*` people: [seed-accounts.md](seed-accounts.md).
- Local mail is real when `SMTP_*` is set, so don't trigger codes, resets or deletion emails to real addresses in tests.
