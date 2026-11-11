# 0011. Account activity and audit: rationale

## Context

Three systems share one account service, and none of them can answer "what happened to this account". welinc-auth records admin edits in `user_changes` (9 actions) but no sign ins: a wrong password only bumps `failed_login_attempts`, and the 5th sets `locked_at` with no row. Sessions keep an address, device and end reason, but the sweep deletes them 90 days after they end.

Meanwhile the other systems built their own. VMMS keeps `login_activities` (successes, failures, lockouts, denied access, logouts) and serves the last 10 rows with no paging, plus a 500 row audit page mixing logins with its work data. BMS reads `user_activity_logs` straight from the auth database through its gateway, a table nothing writes, so its profile and admin activity screens show nothing real. Both must move onto welinc-auth in S11 without their screens breaking, and the contract already reserved `/auth/profile/activity`, `/auth/users/:id/activity` and `/auth/activity`.

Forces: one person can hold roles in several systems, so a VRMS admin must not learn about BMS business. The trail must be trustworthy enough for S10's access report. Addresses must be the browser's, not the gateway's (a bug seen in a similar suite). The deadline is the end of November, and the auth container should stay small enough for the cheapest hosted size.

## Options considered

### Option 1: A new events table beside `user_changes`, merged on read

A sign in and session events table, while account changes stay where they are; the activity routes merge both.

**Pros**: no change to existing writers or specs 0003 to 0005.
**Cons**: one cursor across two differently shaped tables, two triggers, two retention rules, two filter sets.

### Option 2: One `account_events` table replacing `user_changes` (chosen)

Every account event goes to one table; the `change()` helper is repointed and old rows copied.

**Pros**: one timeline, one cursor, one trigger, one index plan. Cheap in practice: all writes pass through one helper, and no app calls `/changes`.
**Cons**: a copy migration, the seed reset and four test files change; retention must differ by category.

### Option 3: New table, separate reads

Sign in events in a new table, account changes on their own route; apps call both.

**Pros**: the simplest server.
**Cons**: every screen merges two lists itself, as VMMS does today, and three apps drift.

## Rationale

Option 2 won once the cost was counted: one helper, one reader with no callers, four test files. Option 1's hard part is the merged read, which is more new code than moving a helper. One table also gives S10 a single source for its access report.

Smaller calls made in the design talk:
- **Refreshes**: one `SYSTEM_OPENED` per system per session instead of a row per refresh (about 50 a day per open tab); reuse is already a session end.
- **Unknown emails**: a log line with the address and the email's domain only. Typed emails are often typos of real ones, and no admin can be scoped to see them. The cross check suggested a keyed hash; the domain alone is enough to spot password spraying, needs no new secret, and can't be reversed by guessing common addresses the way a plain hash can.
- **Cross check (2026-11-11, another model)**: 22 gaps and 6 small points, all applied: transactions and races on the lock counter and session end, commit before throw for refusals, every write point named, the role split in SQL, the sweep setting, the feed query shape, list filters, field visibility, admin tagged ends, null address on backend calls without the header, IPv6 local ranges, `geo:fetch` details, the catalog ETag and `labelAdmin`.
- **Retention**: a year for sign in, session and code rows (a setting), forever for account changes, since "admin since when" must survive.
- **Admin scope**: the event's `system` tag decides ownership. A system's own history stays visible after a person leaves; account wide events stop with membership; other systems' events never show. This needs no role history table. Showing everything was rejected (leaks BMS business); current members only for everything was rejected (a leaver's VRMS trail would vanish).
- **Actor**: id only, names joined at read time; emails stay out of a forever log. The person sees only "An admin".
- **Location**: identity providers show it (Okta, Entra ID, Google, Clerk); Keycloak shows only the address. City from an in memory file costs about 130 MB of RAM; a city table in Postgres costs an import job. Country plus network provider costs about 15 to 20 MB, is never wrong about the provider, and flags cloud and VPN sign ins, the usual attack path. DB-IP Lite over MaxMind GeoLite2: no account, no license key, CC BY 4.0.
- **Wording**: codes plus a catalog route, so VRMS, VMMS, BMS and the portal show the same words.
- **No export and no alerts** in S7: S10 owns admin alerts and fits an export next to the access report; local mail is real Gmail.

### Evidence: what the other systems call today (read only, 2026-11-11)

| System | Route | Shape today | Moves to |
|---|---|---|---|
| VMMS | `GET /auth/me/login-activity` | last 10, `{ id, event, email, ipAddress, deviceType, createdAt }` | `/auth/profile/activity` |
| VMMS | `GET /auth/users/:id/login-activity` | last 10, same | `/auth/users/:id/activity` |
| VMMS | `GET /auth/audit-logs?source=` | up to 500 merged rows | `/auth/activity` for logins and accounts; its work sources stay in VMMS |
| BMS | `GET /auth/profile/activity` (gateway, raw SQL) | last 50, `{ id, action, deviceInfo, location, ipAddress, createdAt }` | `/auth/profile/activity` |
| BMS | `GET /activity-logs` (gateway) | page, search, action prefix, Manila dates; `{ items, total, page, pageSize }` | `/auth/activity` for account events; its booking, dispatch and completion audits stay in BMS |
