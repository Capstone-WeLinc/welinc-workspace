# Account activity: moving VMMS and BMS onto welinc-auth

For the VMMS and BMS groups, at S11. Since suite spec [0011](../specs/_root/0011-account-activity-audit/index.md) (contract [0001](../specs/_root/0001-shared-services-contract/index.md) version 5), welinc-auth records every sign in, session, emailed code and account change in one table, and serves it through four routes. This guide maps your current activity screens onto them. Nothing changes for you until you move; then your own login activity tables and the BMS gateway's reads of the auth database can go.

What we read (2026-11-12): `welinc-backend-vmms`, `welinc-web-vmms` and `welinc-mobile-vrms_vmms` on `development` (2026-11-11), `welinc-backend-bms` on `latest-bms-backend` and `welinc-web-bms` on `latest-bms-frontend` (2026-11-06). Tell us if your newer work changes any of this.

## The routes

All four go through the gateway at `/auth`. The first three take a **user token** (a person's own, from your login flow); a service token gets 403 `WRONG_TOKEN_USE`. Your backend never reads this log for itself.

| Route | Who | What it answers |
|---|---|---|
| `GET /auth/profile/activity` | anyone signed in | Your own events from every system |
| `GET /auth/users/:id/activity` | your system's admin | One person's events tagged with your system or account wide. 404 unless they hold a role in your system now |
| `GET /auth/activity` | your system's admin | Your system's feed: your system's events for anyone (former members too), plus account wide events of your current members. 60 calls a minute per admin |
| `GET /auth/activity/catalog` | anyone, no token | English labels for every category, type and reason. Cache it 5 minutes (it sends `Cache-Control` and an `ETag`) |

**Paging.** Every list answers `{ data, nextCursor }`, newest first. Pass `nextCursor` back as `cursor` for the next page; `null` means the end. `limit` is 1 to 100 (default 50). There is no total count and no page numbers, so a "Showing N of M" footer or numbered pages become a Show more button.

**Filters.**
- `category` and `type`: comma lists, at most 20 values. A type that belongs to none of the given categories answers 400.
- `from` and `to` (admin routes): `YYYY-MM-DD`, Asia/Manila days, both inclusive.
- `userId`, `q` (2 or more characters of name or email, any case) and `address` (one exact IP): the feed only.

Bad values answer 400 `VALIDATION_FAILED`; a cursor you didn't get from these routes answers 400 `INVALID_CURSOR`.

## One event

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

- `category` is one of `SIGN_IN`, `SESSION`, `CODE`, `ACCOUNT`. `type` is one of 20 (the catalog lists them with labels).
- `system` is the system the event belongs to (`SYSTEM_OPENED`, `ROLE_CHANGED`, and an admin ending a session); `null` means account wide.
- `actor.kind` is `SELF`, `ADMIN` or `SYSTEM` (nobody, such as an idle timeout). On the admin routes the actor also has `id` and `name`. On your own route an admin's action shows only as "An admin": use the catalog's `labelAdmin` there.
- The feed adds `user: { id, name, email }` to each event.
- `country` and `network` are filled only when hosted and the location files are present. Locally every row is `localNetwork: true` (show "Local network"). Wherever you show a place, credit it: "IP data by DB-IP" linking to `https://db-ip.com` (CC BY 4.0).

## VMMS

| Today | Becomes | Notes |
|---|---|---|
| `GET /auth/me/login-activity` (bare array, last 10) on Profile | `GET /auth/profile/activity?limit=5` | Profile shows 5 rows; ask for 5 |
| `GET /auth/users/:id/login-activity` (bare array, last 10) in the User management modal | `GET /auth/users/:id/activity?category=SIGN_IN,SESSION` | Add Show more if you want past 10 |
| `GET /auth/audit-logs?source=login` (the "Logins" choice) | `GET /auth/activity?category=SIGN_IN` | Server side paging and search replace the 500 row cap |
| `GET /auth/audit-logs?source=all` | Your own vehicle, work order, schedule and fuel feed, plus `GET /auth/activity` | Merge in the client by `createdAt`, or show "Accounts" as its own tab (simpler: two cursors don't merge cleanly) |

Field by field:

| VMMS field | welinc-auth | Notes |
|---|---|---|
| `event` `SUCCESSFUL_LOGIN` | `type` `SIGNED_IN` | |
| `event` `FAILED_LOGIN` | `type` `SIGN_IN_FAILED`, `reason` `WRONG_PASSWORD`, `ACCOUNT_INACTIVE` or `ACCOUNT_LOCKED` | `attemptsLeft` is new |
| `event` `ACCOUNT_LOCKOUT` | `type` `LOCKED_OUT` | written once, on the 5th wrong password |
| `event` `PLATFORM_ACCESS_DENIED` | `type` `SIGN_IN_FAILED`, `reason` `NO_SYSTEM_ACCESS` or `APP_NOT_ALLOWED` | |
| `event` `LOGOUT` | `type` `SIGNED_OUT` | other session ends are `SESSION_ENDED` with a `reason` |
| `ipAddress` | `address` | null when unknown |
| `deviceType` (Desktop, Mobile, Tablet) | `device` ("Chrome on Windows", or the phone's reported name) | a real label now, not a guess |
| `email` | the feed's `user.email` | not on the person routes (it is their own) |
| audit `actor` (email) | `actor.name`, or `user.email` for whose account it is | |
| audit `action`, `entity`, `details` | the catalog label for `type`, plus `device`, `address` | build the line from the label table |

Not carried over: a failed sign in for an email that has no account is never stored (only logged, with the domain), so the feed has no row for it. VMMS never recorded account changes; they come for free now (`CREATED`, `ROLE_CHANGED`, `UNLOCKED` and the rest). The mobile app needs no change: its `POST /auth/logout` already writes `SIGNED_OUT`.

## BMS

| Today | Becomes | Notes |
|---|---|---|
| `GET /auth/profile/activity` (gateway SQL on `user_activity_logs`, last 50) | the same path, now served by welinc-auth itself | Remove the gateway route and the SQL so the call reaches welinc-auth; the body changes, see below |
| `GET /activity-logs` (gateway merges service audits with SQL on `user_activity_logs`, `users`, `user_roles`) | Your service audits, plus `GET /auth/activity` | Drop `auth-integration.mjs`'s SQL: no system reads the auth database (section 13 of the contract) |

Field by field:

| BMS field | welinc-auth | Notes |
|---|---|---|
| `action` `LOGIN` | `type` `SIGNED_IN` | |
| `action` `PASSWORD_CHANGE` | `type` `PASSWORD_CHANGED` | |
| `action` `LOGOUT_ALL` | `type` `SESSIONS_ENDED` | |
| `action` `PROFILE_UPDATE` | `type` `UPDATED` with `field`, `oldValue`, `newValue` | |
| `action` `DELETION_REQUEST` | none yet | comes with S8 (profile extras) |
| `deviceInfo` (raw user agent) | `userAgent` for the raw text, `device` for the label | no need to parse it yourself |
| `location` (free text) | `country` and `network` | show "Philippines · Globe Telecom", or "Local network" |
| `ipAddress` | `address` | |
| "Current session started" (the first `LOGIN` row) | the `SIGNED_IN` whose `sessionId` is your session's `sid` | exact instead of a guess |
| `userName`, `email` | the feed's `user.name`, `user.email` | |
| `role` (first BMS role) | not on events | look it up from the directory, or drop the column |
| `search` | `q` | |
| `from`, `to` | `from`, `to` | already Manila days |
| `action` verbs (the filter chips) | `category` and `type` | The "Logins" chip sends `Logged in`, which never matches a stored `LOGIN`, so it shows no logins today. Use `type=SIGNED_IN` |
| `page`, `pageSize`, `total`, `pageSize=all` | `cursor`, `limit`, Show more | no totals |

## Order of work at S11

1. Read the catalog once and keep a label table; never hard code labels.
2. Move your Profile view to `/auth/profile/activity`.
3. Move your admin views to `/auth/users/:id/activity` and `/auth/activity`.
4. Remove your own login activity writes and tables (VMMS `loginActivity`; BMS's gateway SQL and the `user_activity_logs` mapping in `welinc-backend-bms-analytics-ai`).
5. Ask the shared services owner before anything else in welinc-auth needs to change.
