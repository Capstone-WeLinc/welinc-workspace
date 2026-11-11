# 0011. Account activity and audit

**Date**: 2026-11-11
**Status**: In Progress

## Summary

welinc-auth starts recording everything that happens to an account in one table: sign ins and failed tries, lockouts, which systems a session opened, sign outs and session ends, emailed codes, and account changes by admins or by the person. It replaces `user_changes`, so there is one timeline per person. Each person can read their own, and each system's admins can read their system's people, through the three routes contract 0001 already reserved. VRMS shows it on My profile and in a new Activity dialog on the Users page, and the VMMS and BMS screens move onto the same routes in S11.

## Requirements

**User stories**:
- As anyone with an account, I want to see my recent sign ins, devices and account changes so that I can spot activity that wasn't me.
- As a system Admin, I want one person's activity and a feed for my whole system so that I can answer "who signed in, failed, got locked or changed what, from where".
- As the VMMS and BMS groups, we want the activity routes our screens already call to exist in welinc-auth so that we can delete our own copies.

**Acceptance criteria**:

*Recording sign ins*
- **AC-1**: Every sign in attempt for an existing account writes one event. `SIGNED_IN` when a session is created (`/auth/login`, `/auth/login/verify-email`, `/auth/mobile/login` and its verify step). `SIGN_IN_FAILED` with a `reason`: `WRONG_PASSWORD` (with `attempts_left`), `ACCOUNT_LOCKED`, `ACCOUNT_INACTIVE`, `NO_SYSTEM_ACCESS` or `APP_NOT_ALLOWED`. The 5th wrong password writes one `LOCKED_OUT` row and no `SIGN_IN_FAILED`. An `EMAIL_VERIFICATION_REQUIRED` answer writes no sign in row (the code step writes `CODE_SENT`, AC-5); the `SIGNED_IN` comes when the code is used. Every failure goes through one `recordFail()` called from each place that refuses a sign in (see Write points). `ACCOUNT_LOCKED` and `ACCOUNT_INACTIVE` are decided before the password is checked, as today. A soft deleted account (`deleted_at` set) counts as no account (AC-2).
- **AC-1b**: The failed try counter moves in one atomic `UPDATE users SET failed_login_attempts = failed_login_attempts + 1 … RETURNING`, in one transaction with the event. `attempts_left` and the lock decision come from the returned value, so parallel wrong passwords never write two `LOCKED_OUT` rows or a wrong `attempts_left`.
- **AC-2**: A sign in with an email that has no account writes no row. It writes one log line with the address and only the email's domain (`@gmail.com`), never the email or a hash of it.
- **AC-3**: Every event carries the real client address (`ip`), the device label (`device`, from `deviceLabel()`) and the raw `User-Agent` (`user_agent`, cut to 512 characters), sourced as in the Value sourcing table. Behind the gateway the stored address is the browser's, never a container address. On a call from a system backend without a valid assertion and `X-WeLinc-User-Address`, the address is stored as null, never the backend's `req.ip`.

*Recording sessions and codes*
- **AC-4**: The first access token for a system in a session writes one `SYSTEM_OPENED` (with `system`), also when two refreshes race: `addAudience` returns its update count and the event is written only when it is 1. A session created with its first audience already set (mobile create, and any create path that sets `audiences`) writes `SYSTEM_OPENED` in the same transaction. Every session end writes exactly one row: `SIGNED_OUT` for `LOGOUT`, `SESSION_ENDED` with the end reason for the other ten. `SessionService.end()` writes the event in the same transaction as its update (opening its own `$transaction` when handed the bare client), and only when the update count is 1, so ending an already ended session writes nothing. Plain refreshes write nothing.
- **AC-5**: Emailed codes write `CODE_SENT`, `CODE_MAIL_FAILED`, `CODE_USED` and `CODE_RETIRED` (killed by the 5th wrong try) from `code.service.ts`, with `reason` holding the purpose (`PASSWORD_SETUP`, `PASSWORD_RESET`, `SIGN_IN`, `EMAIL_CHANGE`). `CODE_SENT` is written in its own transaction after the mail succeeds (a crash between the mail and the row loses that row, accepted). `CODE_MAIL_FAILED` is written in its own transaction after `undoIssue`. `CODE_RETIRED` commits with the tries update before the 400 is thrown. `CODE_USED` is written in the transaction that uses the code. A code an admin sent has the admin as actor; `CODE_SENT` replaces `RESET_SENT`.

*Recording account changes*
- **AC-6**: Every write that today makes a `user_changes` row makes an `ACCOUNT` event in the same transaction instead, with the same actor, field and values. New ones: `PASSWORD_CHANGED` (profile password, setup code, reset code), `UPDATED` with `field: name` for your own rename, and `PICTURE_CHANGED`. `ROLE_CHANGED` writes one row per system whose roles changed, with `system` set and `old_value` and `new_value` listing only that system's roles in `rolesKey()` form (null for an empty side: system newly granted or fully removed). Creating an account writes `CREATED` plus one `ROLE_CHANGED` per system granted. A password change intentionally writes `PASSWORD_CHANGED`, plus `CODE_USED` when a code was used, plus one `SESSION_ENDED` (`PASSWORD_CHANGED`) per other session it ends.
- **AC-7**: An event is written in the same database transaction as the action it records. If the event can't be written, the action fails. Refusals are the exception that must not roll back: a failed sign in's row (with its counter update) and a `CODE_RETIRED` row commit first, and the 401, 403 or 400 is thrown after the commit; a test proves the row survives the error answer.

*Storage rules*
- **AC-8**: `account_events` is append only, enforced by a trigger: `UPDATE` always raises; `DELETE` raises for `ACCOUNT` rows always, and for other rows unless `current_setting('welinc.event_sweep', true) = 'on'` (an unset setting reads as null, never an error). `TRUNCATE` stays allowed (it skips row triggers); only the local seed `--reset` uses it, truncating `account_events` before `users`.
- **AC-9**: The hourly sweep deletes non `ACCOUNT` rows older than `ACCOUNT_EVENT_RETENTION_DAYS` (default 365), 1000 at a time, each batch its own transaction that first runs `SELECT set_config('welinc.event_sweep', 'on', true)`, until a batch deletes fewer than 1000. `ACCOUNT` rows are never deleted.
- **AC-10**: The migration copies every `user_changes` row into `account_events` (user, actor, field, values and time). `RESET_SENT` becomes `CODE_SENT` with reason `PASSWORD_RESET`. `ROLE_CHANGED` rows are split in SQL: `string_to_array` the old and new keys, take each entry's system with `split_part(x, '@', 2)`, `string_agg` the sorted entries per system, and emit a row only for a system whose two sides differ (null for an empty side). A row that isn't split, and the first split row of each (by system order), keep the old id; the others get `gen_random_uuid()`. Then it drops `user_changes` and `UserChangeAction`. The new count equals the old count plus the extra split rows.

*Reading*
- **AC-11**: `GET /auth/profile/activity` (any user token) lists the caller's own events from every system, newest first, keyset paged (`limit` 1 to 100, default 50), optional `category`. The actor is only a kind: `SELF`, `ADMIN` or `SYSTEM`. No admin id, name or email reaches the person. Other fields follow the Field visibility table.
- **AC-12**: `GET /auth/users/:id/activity` (a system admin of the token's `aud`) answers 404 unless the person holds a role in that system now. It lists that person's events whose `system` is the `aud` or null, with filters `category`, `type`, `from`, `to`. The actor carries `id` and `name`.
- **AC-13**: `GET /auth/activity` (a system admin) lists events where `system` is the `aud` (any person, current or former member), or `system` is null and the person holds a role in the `aud` now. Filters: `category`, `type`, `userId`, `q` (at least 2 characters, the person's name or email, case insensitive), `from`, `to` (`YYYY-MM-DD`, Asia/Manila days, inclusive) and `address` (exact). Each event carries `user: { id, name, email }`. A `userId` outside that scope gives an empty page, never 404. 60 calls a minute per user (the existing throttler keyed by `sub`, counted per container), then 429 `RATE_LIMITED`. Account wide rows (a `SIGNED_IN` at the portal, say) are visible to every system the person is a member of: that is the rule, not a leak.
- **AC-14**: `category` and `type` take comma separated lists (at most 20 values, duplicates dropped). A bad value, a `type` that belongs to none of the given categories, a `userId` that isn't a UUID, a bad date, `from` after `to`, a bad `address` or `limit` answers 400 `VALIDATION_FAILED`; a bad cursor answers 400 `INVALID_CURSOR`. A service token on any of the three routes answers 403 `WRONG_TOKEN_USE`.
- **AC-15**: `GET /auth/activity/catalog` (no token) lists the categories, types (each with its category, a `label` and a `labelAdmin` for the person's view of an admin's action, e.g. "An admin changed your role") and reasons, each with an English label. It sends `Cache-Control: public, max-age=300` and a strong `ETag` (sha256 of the body, computed at boot), and answers 304 to a matching `If-None-Match`, reusing the `/auth/systems` handling (lists and `W/` included).
- **AC-16**: `GET /auth/users/:id/changes` is deleted from the controller (Nest's default 404). Contract 0001 moves to version 5 with the new routes, codes and limits.

*Location*
- **AC-17**: When the offline files are present, each event with a public address stores `country`, `network` and `asn`, looked up once at write time on the normalised address (an IPv4 mapped `::ffff:` address as IPv4). Private, loopback, link local and shared addresses (`10/8`, `172.16/12`, `192.168/16`, `127/8`, `169.254/16`, `100.64/10`, `::1`, `fc00::/7`, `fe80::/10`) store none, and the read answer marks them `localNetwork: true`. A null address answers `localNetwork: false` and shows no place. Missing or unreadable files log one warning at boot; location stays empty and everything else works.
- **AC-18**: `npm run geo:fetch` in welinc-auth downloads `dbip-country-lite-YYYY-MM.mmdb.gz` and `dbip-asn-lite-YYYY-MM.mmdb.gz` from DB-IP's free download folder (`download.db-ip.com/free/`), this month in UTC and last month's on a 404, gunzips each to a temp file and renames it to `geo/dbip-country-lite.mmdb` and `geo/dbip-asn-lite.mmdb` (`geo/` git ignored). Any failure exits non zero, or warns and exits 0 with `--soft`. The Docker build runs it with `--soft`; `scripts/setup.sh` runs it with `--soft`. `maxmind` is pinned to an exact version. Every screen that shows a place credits "IP data by DB-IP" with a link (CC BY 4.0).

*VRMS screens*
- **AC-19**: My profile gets a Recent activity card under Signed in devices: the newest 10 events grouped by Asia/Manila day, and Show more loads the next page in place. Each row shows the catalog label (`labelAdmin` when the actor kind is `ADMIN`), the device, the address, the place ("Philippines · Globe Telecom", or "Local network") and the time. Role values show role names from `GET /auth/systems`. The catalog is fetched once and cached 5 minutes. It has loading, empty and error states.
- **AC-20**: Each row menu on the Users page gets an **Activity** item (also on your own row) opening an Activity dialog for that person: category chips from the catalog, newest first, Show more, the same row format plus the actor's name. It reads well at 375px and 1280px.

*Safety*
- **AC-21**: No event, log line or answer holds a password, a code or its hash, a token, a challenge id or an SSO handle. Unknown emails are never stored.

## Decision

**Chosen option**: Option 2: one `account_events` table that replaces `user_changes`.

All account history (sign in, session, code and account change events) lives in one append only table in welinc-auth, read through three scoped routes and a label catalog, with optional offline country and network lookup from DB-IP Lite.

**Implementation skills**: `prisma-client-api` and `prisma-cli` (`.claude/skills/`), for the migration, the raw SQL trigger and the keyset queries · `nestjs-best-practices` (`.claude/skills/`), for the events module and guards · `shadcn` and `vercel-react-best-practices` (`.claude/skills/`), for the two VRMS views.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch**:

`account_events` (replaces `user_changes`)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | uuid | no | PK |
| `user_id` | uuid | no | FK `users`, `ON DELETE RESTRICT` (users are only soft deleted) |
| `actor_id` | uuid | yes | FK `users`, restrict. Null: nobody acted (idle end, automatic lock). Equal to `user_id`: the person did it |
| `category` | `AccountEventCategory` | no | `SIGN_IN`, `SESSION`, `CODE`, `ACCOUNT` |
| `type` | `AccountEventType` | no | list below |
| `reason` | varchar(40) | yes | fail reason, session end reason, or code purpose |
| `system` | `SystemType` | yes | the system the event belongs to; null means account wide |
| `session_id` | uuid | yes | plain `sid`, no FK (sessions are purged after 90 days) |
| `client_id` | text | yes | the login client, plain value |
| `field` | varchar(50) | yes | account changes |
| `old_value`, `new_value` | text | yes | account changes |
| `attempts_left` | smallint | yes | `WRONG_PASSWORD` only |
| `ip` | inet | yes | |
| `device` | varchar(100) | yes | |
| `user_agent` | varchar(512) | yes | |
| `country` | char(2) | yes | ISO code |
| `network` | varchar(120) | yes | provider name from the ASN file |
| `asn` | integer | yes | |
| `created_at` | timestamptz(3) | no | default `now()` |

Indexes: `(user_id, created_at desc, id desc)`, `(system, created_at desc, id desc)`, `(created_at desc, id desc)`, `(ip, created_at desc)`. No `type` index: every read is scoped and time ordered, and each index costs every sign in a write.

Types by category (`type` → `category` is defined once, as a map in the events module; the migration's `CHECK` constraint is written from it, and a unit test checks that the map, the catalog and the Prisma enums agree):
- `SIGN_IN`: `SIGNED_IN`, `SIGN_IN_FAILED`, `LOCKED_OUT`
- `SESSION`: `SYSTEM_OPENED`, `SIGNED_OUT`, `SESSION_ENDED`
- `CODE`: `CODE_SENT`, `CODE_MAIL_FAILED`, `CODE_USED`, `CODE_RETIRED`
- `ACCOUNT`: `CREATED`, `UPDATED`, `ROLE_CHANGED`, `ACTIVATED`, `DEACTIVATED`, `UNLOCKED`, `DELETED`, `SESSIONS_ENDED`, `PASSWORD_CHANGED`, `PICTURE_CHANGED`

`System` tag per type: `SYSTEM_OPENED` and `ROLE_CHANGED` carry the system. A `SESSION_ENDED` for `ADMIN_ENDED`, `DEACTIVATED` or `DELETED` carries the admin's `aud`. A `SIGN_IN_FAILED` for `APP_NOT_ALLOWED` carries the app's system (its client's audience). Everything else is null (account wide), including `NO_SYSTEM_ACCESS`, so a person with no role anywhere is seen by no system admin.

**Write points** (where each event is written; names, not line numbers):

| Code | Events |
|---|---|
| `AuthService.checkCredentials` (portal and mobile) | `SIGN_IN_FAILED` (`WRONG_PASSWORD`, `ACCOUNT_LOCKED`, `ACCOUNT_INACTIVE`), `LOCKED_OUT`, through `recordFail()` |
| `assertCanSignIn` (both verify email steps) | `SIGN_IN_FAILED` (`ACCOUNT_LOCKED`, `ACCOUNT_INACTIVE`) |
| `launcher.ts` and the `user-grants.service.ts` pre check | `SIGN_IN_FAILED` (`NO_SYSTEM_ACCESS`, `APP_NOT_ALLOWED`) |
| `SessionService.createWeb`, mobile create | `SIGNED_IN`; `SYSTEM_OPENED` when created with an audience |
| `SessionService.addAudience` (grants, code exchange, refresh) | `SYSTEM_OPENED` |
| `SessionService.end` | `SIGNED_OUT`, `SESSION_ENDED` |
| `code.service.ts` (`issue`, `undoIssue`, `check`, `consume`) | `CODE_SENT`, `CODE_MAIL_FAILED`, `CODE_RETIRED`, `CODE_USED` |
| `change()` callers in `auth.service.ts`: `createUser`, the role grant, `updateUser`, `updateUserStatus`, `unlockUser`, `deleteUser`, the admin reset send, the self email change | `CREATED`, `ROLE_CHANGED`, `UPDATED`, `ACTIVATED`, `DEACTIVATED`, `UNLOCKED`, `DELETED`, `CODE_SENT` (was `RESET_SENT`), `UPDATED` (email) |
| `sessions.controller.ts` end all | `SESSIONS_ENDED` |
| `PATCH /auth/profile`, `/profile/password`, `/profile/picture`, setup and reset completion | `UPDATED` (name), `PASSWORD_CHANGED`, `PICTURE_CHANGED` |

**Query rules** (all three reads):
- Keyset on `(created_at desc, id desc)`: fetch `limit + 1` rows, the extra one only sets `nextCursor`. Cursor: base64url of the row's millisecond ISO `created_at` plus `|` plus `id` (safe because the column is `timestamptz(3)`); condition `(created_at, id) < (cursor time, cursor id)`.
- The feed is a `UNION ALL` of its two scope branches (`system = aud`; `system IS NULL AND user_id IN members of aud`), each ordered and limited to `limit + 1`, then merged and cut. Filters are ANDed inside each branch; `from` and `to` bound `created_at` alongside the cursor.

**Field visibility**:

| Field | Person (own) | Admin, per person | Admin, feed |
|---|---|---|---|
| `actor` | `{ kind }` only | `{ kind, id, name }` | `{ kind, id, name }` |
| `client` | yes | only on rows tagged with the admin's system | same |
| address, place, device, `userAgent` | yes | yes | yes |
| `field`, `oldValue`, `newValue`, `reason` | yes (their own data; the reason names an admin action without naming the admin) | yes | yes |
| `user` | no | no | `{ id, name, email }` |

Actor per session end: the user for `LOGOUT`, `USER_ENDED`, `PASSWORD_CHANGED`; the admin for `ADMIN_ENDED`, `DEACTIVATED`, `DELETED`; null for `IDLE`, `MAX_AGE`, `MAX_SESSIONS`, `REFRESH_REUSE`, `CODE_REUSE`.

Gone: `user_changes`, `UserChangeAction` (with `RESET_SENT`), and `actor_email`.

**State transitions**: none. Rows are written once and never change (AC-8).

**API surface** (all through the gateway's `/auth` route):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/profile/activity` | GET | `cursor`, `limit`, `category` (opt) | `{ data: EventView[], nextCursor }` with `actor: { kind }` | user token, any `aud` | 400 `VALIDATION_FAILED`, `INVALID_CURSOR`; 403 `WRONG_TOKEN_USE` |
| `/auth/users/:id/activity` | GET | `cursor`, `limit`, `category`, `type`, `from`, `to` (all opt) | `{ data: EventView[], nextCursor }` with `actor: { kind, id, name }` | `@SystemAdmin()` | 404 not a member now; 400s as above; 403 |
| `/auth/activity` | GET | as above plus `userId`, `q`, `address` | `{ data: (EventView & { user })[], nextCursor }` | `@SystemAdmin()` | 400s; 403; 429 `RATE_LIMITED` |
| `/auth/activity/catalog` | GET | none | `{ categories: [{ code, label }], types: [{ code, category, label, labelAdmin }], reasons: [{ code, label }] }` | none | 304 |
| `/auth/users/:id/changes` | GET | | removed | | 404 |

`EventView`: `{ id, category, type, reason, system, sessionId, client, field, oldValue, newValue, attemptsLeft, address, localNetwork, device, userAgent, country, network, createdAt, actor }`, narrowed per route by the Field visibility table. Cursor and paging per the Query rules.

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| Portal or mobile sign in | `ip` | `req.ip` under `TRUST_PROXY_HOPS` (1 behind the gateway) |
| Portal or mobile sign in | `device`, `user_agent` | the request's `User-Agent` and the mobile `deviceName`, through `deviceLabel()` |
| Sign in, any outcome | `user_id`, `attempts_left` | the account row `checkCredentials` loaded; `MAX_FAILED_ATTEMPTS` minus the new counter |
| `SYSTEM_OPENED` | `system`, `session_id` | the token's `aud` and `sid`, written when `addAudience` updates a row (it returns the count) |
| `SYSTEM_OPENED`, refresh or exchange from a system backend | `ip` | `X-WeLinc-User-Address` after a valid assertion (`userAddressOf()`), else null (never the backend's `req.ip`) |
| `SYSTEM_OPENED` at mobile create | `ip` | `req.ip` |
| Unknown email log line | domain | the part after `@` of the typed email |
| Any event tied to a session but raised by a backend or the sweeper | `device`, `user_agent` | copied from the `sessions` row (`device_name`, `user_agent`) |
| Session end by the sweeper | `ip` | null |
| Session end | `type`, `reason`, `actor_id` | `SessionService.end()`'s reason and `endedById`, mapped as above, written only when its update count is 1 |
| Code events | `reason`, `actor_id` | the code's `purpose`; the admin for admin sends, else the user |
| Account changes | `actor_id`, `field`, values | the `Actor` passed to `change()` today |
| `ROLE_CHANGED` | `system`, values | the caller's `aud`; `rolesKey()` filtered to that system |
| Any event | `country`, `network`, `asn` | the `GeoService` lookup of `ip` at write time |
| Reads | `localNetwork` | derived from `address` (private, loopback, link local, `100.64.0.0/10`) |
| Reads | `actor.name`, `user.name`, `user.email` | joined from `users` at read time |
| Admin reads | which system | the token's `aud` |
| Date filters | day bounds | `from` 00:00 and `to` 24:00 in Asia/Manila (+08:00), fixed |
| Catalog | labels | a constant in the events module |

**Key invariants**:
- No action without its event; no event for an action that rolled back (AC-7).
- Rows never change; `ACCOUNT` rows are never deleted (AC-8).
- One event per session end and one `SYSTEM_OPENED` per system per session (conditional updates, AC-4).
- `type` always matches `category` (`CHECK`).
- A person's own view never reveals which admin acted (AC-11).

**Security model**:
- The person: their own events, every system, with address, place and device; actors reduced to a kind.
- A system admin (the catalog's `isSystemAdmin` for the token's `aud`, checked on every request): their system's tagged events for anyone, and account wide events only of current members. Events tagged with another system are never shown. The per person route keeps the usual 404 for non members.
- Service tokens: refused (403). Systems learn about people through the directory, not this log.
- The suite admin (S10) will add a view over everyone; nothing here blocks it.
- Personal data kept: addresses, devices and emails inside email change values. Sign in, session and code rows go after a year; account changes are kept as the audit trail. A `DELETED` account keeps its rows (the audit trail is the reason to keep them); erasure on request belongs to S8. Unknown emails are never stored.

**Configuration required**:
- `ACCOUNT_EVENT_RETENTION_DAYS`: days to keep non `ACCOUNT` events, whole number 30 to 3650, default 365.
- `GEOIP_COUNTRY_FILE`, `GEOIP_ASN_FILE`: optional paths to the DB-IP Lite `.mmdb` files, defaults `geo/dbip-country-lite.mmdb` and `geo/dbip-asn-lite.mmdb`. Missing files are allowed.
- All in the env schema (spec 0010) and `.env.example`. No secrets; DB-IP Lite needs no key.

**Critical test scenarios**:
- Happy path: sign in on the portal, open VRMS, sign out; My profile shows Signed in, Opened VRMS and Signed out with the browser's address and device, verifies **AC-1**, **AC-3**, **AC-4**, **AC-19**
- Failure case: 5 wrong passwords give 4 `SIGN_IN_FAILED` with 4 to 1 tries left, then one `LOCKED_OUT`; a 6th try gives `ACCOUNT_LOCKED`; 5 sent in parallel still give exactly one `LOCKED_OUT`; each row exists after its 401, verifies **AC-1**, **AC-1b**, **AC-7**
- Failure case: a database error on the event insert rolls back a role change, verifies **AC-7**
- Concurrency: two refreshes at once for a new system write one `SYSTEM_OPENED`; logout twice writes one `SIGNED_OUT`, verifies **AC-4**
- Auth/permission: a VRMS admin asking for a BMS only person gets 404 per person and sees only that person's VRMS tagged rows in the feed; the person sees "An admin", verifies **AC-11** to **AC-13**
- Storage: an `UPDATE` and a plain `DELETE` on `account_events` both raise, verifies **AC-8**

## Build plan

Tracer Bullet: one thin thread through the table, a writer, a reader and a VRMS screen, then widen.

1. **Thin thread.** The migration (enums, table, indexes, `CHECK`, the append only trigger, the copy from `user_changes` with the per system split, the drop). An events module with `record()` and the catalog constant; `change()` in `user-changes.ts` repointed to `account_events` (no `actor_email`). Sign in events at every refusal point and the session create paths through `recordFail()`, the atomic counter, commit before throw, and the unknown email log line. `GET /auth/profile/activity` and `GET /auth/activity/catalog` (with `labelAdmin` and the ETag). The VRMS Recent activity card on My profile (without places yet). The seed `--reset` truncates `account_events` before `users`. Satisfies **AC-1**, **AC-1b**, **AC-2**, **AC-3**, **AC-6** (repointed writes), **AC-7**, **AC-8**, **AC-10**, **AC-11**, **AC-15**, **AC-19**, **AC-21**
2. **Sessions, codes and self edits.** `SessionService.end()` (own transaction when given the bare client) and `addAudience` (returning its count) write their events; creates with an audience write their first `SYSTEM_OPENED`; null address on backend calls without the header. Code service events (`RESET_SENT` writer becomes `CODE_SENT`). `PASSWORD_CHANGED`, the self rename and `PICTURE_CHANGED`; `ROLE_CHANGED` per system and on create. Satisfies **AC-4**, **AC-5**, **AC-6**
3. **Admin reads.** `GET /auth/users/:id/activity` and `GET /auth/activity` with the scoping rule (the `UNION ALL` feed), list filters, validation, field visibility and the 60 a minute limit; remove `/auth/users/:id/changes`. The VRMS Activity item and dialog. Satisfies **AC-12**, **AC-13**, **AC-14**, **AC-16**, **AC-20**
4. **Location.** `maxmind` package, a `GeoService` loaded at boot, lookups in `record()`, `localNetwork` on reads, `geo:fetch`, the Dockerfile step, the `setup.sh` call, env names, places and the DB-IP credit on both VRMS views. Satisfies **AC-17**, **AC-18**, **AC-19**, **AC-20**
5. **Retention and handover.** The sweep in `SessionSweeper.hourly`; contract 0001 version 5 (sections 10 to 12, the gap map row "welinc-auth records no login activity" closed); a section in `docs/integration/` mapping VMMS `me/login-activity`, `users/:id/login-activity`, `audit-logs` and BMS `profile/activity`, `/activity-logs` to the new routes and fields. Satisfies **AC-9**, **AC-16**

## Consequences

**Positive**:
- One place answers "what happened to this account" for all three systems; VMMS's table and BMS's direct database reads can go in S11.
- Failed sign ins and lockouts become visible for the first time, with the real address and network.
- The append only trigger and the same transaction rule make the trail trustworthy enough for S10's access report.

**Negative / tradeoffs**:
- Every sign in, session end and code now does one more insert, and the table grows by roughly a row per sign in, system opened and session end. Fine at WeLinc's size; the sweep bounds it.
- Breaking for anyone reading `user_changes` or `/changes` (nobody does today) and for the seed reset.
- VMMS and BMS screens must change field names in S11: BMS loses its `location` text (it shows country and network instead), and VMMS's 500 row mixed audit page must page through two sources.
- The geo files must be refreshed (a rebuild each month); stale files only make places less accurate.
- Admins can't see a former member's sign ins; that waits for the S10 suite admin.

**Neutral**:
- `REFRESH_REUSED` from the design talk is not a separate type: the session end with reason `REFRESH_REUSE` already records it once.
- Places appear only when hosted; locally every row reads "Local network".

## Follow-up

- [ ] Hosting (VRMS spec 0008): run `geo:fetch` in the image build and rebuild monthly; credit DB-IP in the hosted docs.
- [ ] S11 guide: the route and field map from build task 5; BMS's "Logins" filter matching becomes a `type` filter.
- [ ] S10: a suite admin view over every person's events (former members included) and the access report built on `ACCOUNT` rows.
- [ ] S8: phone, verify password and deletion request events join this table (new `ACCOUNT` types).
- [ ] Feature 64 (VRMS audit log page redesign) can share the day grouped row style.
- [ ] `/sync`: welinc-auth `AGENTS.md` (`account_events`, the trigger and the sweep setting); record `maxmind` as the geo reader and the declined Agent Skill search for it.
