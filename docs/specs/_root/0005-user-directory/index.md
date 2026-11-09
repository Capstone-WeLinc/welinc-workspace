# 0005. User directory for systems: a change feed written by Postgres

**Date**: 2026-11-09
**Status**: Accepted
**Scope row**: [S6. User directory for systems](../../../scope/_root/shared-services.md#s6-user-directory-for-systems--in-progress)
**Builds contract sections**: [0001](../0001-shared-services-contract/index.md) section 9 (the directory), 10 (`/auth/users` back to admins only), 12 (the directory limit)

## Summary

Systems need to know about the people their records point to (names, emails, roles, active or not) without reading the auth database. welinc-auth gets three read routes for system backends: a full list for the first copy, a lookup by id, and a change feed (a numbered list of "what changed about whom" that a system reads from where it last stopped). Postgres itself writes each feed row through a trigger (a rule stored in the database that runs on every change), so no code path can forget to record a change. VRMS is the first reader: a 30 second timer keeps its mechanic roster current from the feed, a save on the Users page refreshes that one person at once, and VRMS stops downloading every user on page loads.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As a system's backend, I want to learn about created, changed, deactivated and deleted people in my system without polling every user, so that my local copy stays current cheaply.
- As a system's backend, I want to look up many people by id in one call, so that records pointing to people show the right names, even people who have since left my system.
- As a VRMS admin, I want the mechanic picker to reflect a change I just made at once, and changes made elsewhere (the portal, a profile edit) within about a minute.
- As the owner of welinc-auth, I want every change to a person recorded no matter which code path made it, so that no system silently misses one.

**Acceptance criteria** (the contract):

*The feed in welinc-auth*
- **AC-1**: One hand written SQL migration (Prisma can't express triggers or `xid8`), in one transaction and in this order: creates `directory_feed` with its single row and a new random `epoch`, creates `directory_changes` (see *Data model sketch*), backfills one `created` row for every existing user who holds at least one role (soft deleted ones included, with `deleted` set in the snapshot), then creates the triggers. `schema.prisma` declares both tables (`txid` as `Unsupported("xid8")`, the GIN index with `type: Gin`) so later `migrate dev` runs don't try to drop them.
- **AC-2**: Deferred triggers (they run at commit, so they see the final state of the transaction) on `users` (insert, update, delete) and `user_roles` (insert, update, delete) call one function that, for the affected user: builds the snapshot of their state at commit; reads their latest earlier feed row (highest `(txid, seq)` from another transaction); and writes **at most one row per user per transaction** (upsert on `(txid, user_id)`, so later firings in the same transaction just rebuild it). If the new snapshot equals the previous one ignoring `updatedAt`, no row is written (or the transaction's row is removed). Otherwise `systems` is the systems in the new snapshot's roles plus the systems in the previous snapshot's roles, and `type`, compared with the previous snapshot, is: no previous row → `created`; `deletedAt` became set → `deleted`; `isActive` true to false → `deactivated`; false to true → `activated`; roles differ → `roles_changed`; otherwise → `updated` (first match wins). A hard delete of a user writes a `deleted` row built from the old row. Changes to `password_hash`, `failed_login_attempts`, `locked_at`, `email_verified` or `updated_at` alone leave the snapshot equal, so they write nothing. A rolled back transaction writes nothing. The function has no exception handler: if it fails, the user write fails.
- **AC-3**: Each write path produces exactly one feed row for the person it changes: admin create (with roles), admin edit (fields, roles, or both in one save), activate, deactivate, delete, own profile edit, own picture upload, and the seed script (each seeded person and their roles in one transaction). Saving values equal to the current ones, a password change, a reset, a lock, an unlock and a failed login produce none.

*The routes*
- **AC-4**: `GET /auth/directory/users?cursor&limit` returns the users who currently hold a role in the caller's system, ordered by `id`, `limit` 100 by default and at most 500, with `next` (an opaque page cursor, `null` on the last page). Every page carries `changesCursor`: the safe point (*Decided calls*) taken in a statement before that page's scan, across the whole feed (not filtered by system), so a reader that starts the feed from the first page's `changesCursor` misses nothing (it may see a change twice, which is harmless). A bad page cursor gives 400 `INVALID_CURSOR`.
- **AC-5**: `GET /auth/directory/changes?after&limit` returns, ordered by `(txid, seq)`, the rows after `after` (from the very first row when `after` is missing) that are below the safe point and whose `systems` include the caller's system, `limit` 100 by default, as `{ changes, next, hasMore }`. It fetches `limit + 1` matching rows to set `hasMore`. `next` is the cursor of the last row returned; when fewer than `limit` rows match, `next` is the safe point instead, so a system with few people doesn't scan the same rows again. A slow transaction that commits late is never skipped. A cursor welinc-auth did not issue, or one from another `epoch` (a restored or rebuilt database), gives 400 `INVALID_CURSOR`. `limit` below 1 or above 500 gives 400 `VALIDATION_FAILED` on every directory route.
- **AC-6**: `POST /auth/directory/users/lookup` with `{ ids }` (1 to 200 uuids, no repeats, else 400 `VALIDATION_FAILED`) returns `{ users, missing }`. `users` holds every id that holds, or ever held, a role in the caller's system (a `user_roles` row for that system now, or a `directory_changes` row whose `systems` include it), with `roles` empty if they hold none now and `deleted: true` if soft deleted. Every other id, including unknown and hard deleted ones, is in `missing`. It reads current state, not the feed, so it has no lag.
- **AC-7**: Every route returns `DirectoryUser` exactly as contract section 9 defines it: `roles` holds only the caller's system's role codes, `phone` is the user's `contact` as stored only when the caller's token holds `directory.contact` and `null` otherwise, `phoneVerified` is `false` until S8 adds phone verification, `picture` is `profile_picture` as stored (an `/uploads` address, unchanged), `deleted` is `deleted_at` being set. In the feed, `at` is the row's `created_at`.
- **AC-8**: The three routes accept only a service token (a backend's own token from the client credentials grant) whose `aud` is `AUTH` and whose `scope` holds `directory.read`. The caller's system is the `system` of the token's client in `oauth_clients`, read on each request. No token or a bad one gives 401. A person's token (an admin's included), a service token without `directory.read`, or a client with no system gives 403 `FORBIDDEN`. More than 120 calls a minute from one client (counted by `client_id`, after the token check) gives 429 `RATE_LIMITED` with `Retry-After`.
- **AC-9**: `GET /auth/users` accepts system admins only. A service token, `directory.read` or not, gets 403.
- **AC-10**: Contract 0001 is amended: section 9 (the safe point replaces "older than 5 s", one change per user per transaction and none when nothing visible changed, the backfill, `INVALID_CURSOR` after a restore means "read everything again", `phoneVerified` false until S8), section 10 (`/auth/users` for admins only), and the gap map line for VRMS's mechanic sync.

*VRMS, the first reader*
- **AC-11**: A migration in welinc-backend-vrms creates `directory_sync_state` and inserts its single row `id = 'auth'`, `cursor` null.
- **AC-12**: Every 30 s (a constant, `DIRECTORY_POLL_MS`, not a setting) the poll job claims the lease (AC-16). With no cursor it runs the full read: one routine shared with the recovery sync (AC-17) that pages `/auth/directory/users`, applies every user, sets inactive every active mechanic row whose person did not appear, and only after the last page saves the first page's `changesCursor` (a crash halfway leaves the cursor null, so the next tick starts the full read again). With a cursor it reads `/auth/directory/changes` from it, up to 10 pages a tick, and applies each change in order from its snapshot (the `type` is informational). Each change is applied and the cursor moved past it in one database transaction. When the page has no changes but a new `next`, the cursor moves to it. A 400 `INVALID_CURSOR` sets the cursor to null and logs one warning, so the next tick runs the full read.
- **AC-13**: Applying a user (from the full read or a change's snapshot) follows today's roster rules: holding the VRMS `MECHANIC` or `CHIEF_MECHANIC` role and not deleted means the `mechanics` row is created or updated with name, lower case email, `isActive` and role; no mechanic role, or deleted, means an existing row is set inactive and keeps its last role; a person with no mechanic role and no row is ignored. Applying the same user twice changes nothing.
- **AC-14**: When applying a change throws, the job logs the error with the change's cursor and stops that tick. The cursor stays at the last change applied, and the next tick tries the same change again. No change is ever skipped.
- **AC-15**: When welinc-auth can't be reached or answers 5xx or 429, the job logs one warning and sets `failing_since`, logs nothing on later failing ticks, and on the first good tick logs one line saying how long it was failing and clears `failing_since`. Requests to VRMS are not affected; the picker shows the last known roster.
- **AC-16**: Only one VRMS copy works the feed at a time. A tick or a recovery sync claims the lease with one `UPDATE` that sets `lease_owner` to a new uuid and `lease_until` to now plus 2 minutes, only when `lease_until` is empty or past. The holder renews `lease_until` after each page. Every cursor write and the release (both fields back to null) carry `WHERE lease_owner = <mine>`; when that matches no row, the holder lost the lease and stops at once without writing. A tick that can't claim does nothing and logs nothing.
- **AC-17**: `POST /vrms/mechanics/sync` (permission `users.manage`) is the recovery path: it claims the lease (409 `SYNC_RUNNING` when another copy holds it), runs the full read of AC-12, saves the new `changesCursor`, and returns `{ created, updated, deactivated }` counted by that routine.
- **AC-18**: `POST /vrms/mechanics/:authUserId/refresh` (permission `users.manage`) looks the person up through `/auth/directory/users/lookup` and applies them by AC-13 at once. A person in `missing`, or returned with no mechanic role or `deleted: true`, has their existing row set inactive. It returns `{ mechanicId, isActive }`, or `{ mechanicId: null }` when there is no row and nothing to create. welinc-auth down gives 503 `AUTH_UNAVAILABLE`. `refreshOne` (used by mechanic work, spec 0011 AC-33) uses the same lookup instead of listing every user. A later poll may briefly apply an older change over a refreshed row; the next change for that person corrects it.
- **AC-19**: The just in time update of a mechanic's own row on each request (spec 0009 AC-13) stays as it is.
- **AC-20**: web-vrms no longer calls `/vrms/mechanics/sync` when the Users page or the New repair form opens. After a Users page save (create, edit, activate, deactivate, delete) it calls the refresh route for that person, using the id from the create response or the id of the row acted on otherwise; any failure shows the warning toast "Saved, but VRMS couldn't update its mechanic list. It will catch up within a minute." and never undoes the save.
- **AC-21**: welinc-backend-vrms no longer calls `GET /auth/users`; every read of people goes through the directory.

## Decision

**Chosen option**: Option 1: a feed table written by deferred Postgres triggers, read in transaction order, with snapshots.

welinc-auth records every change to a person in `directory_changes` through triggers, serves it to system backends through three service only routes, and VRMS keeps its roster from it with a leased 30 second poll plus an instant refresh after its own saves.

**Implementation skills**: `nestjs-best-practices` (`.claude/skills/nestjs-best-practices/`) · `prisma-cli` (`.claude/skills/prisma-cli/`) · `prisma-client-api` (`.claude/skills/prisma-client-api/`)

### Decided calls (made at write time)

- **Read order is the transaction id, not the sequence number.** Each row stores `txid` (`pg_current_xact_id()`, the id Postgres gives a writing transaction). The feed serves only rows whose `txid` is below `pg_snapshot_xmin(pg_current_snapshot())` (the oldest transaction still running), ordered by `(txid, seq)`, compared as a row tuple `(txid, seq) > ($1, $2)`. Every transaction below that point is finished, and every later one has a higher id, so nothing can ever land behind a cursor. The contract's "older than 5 s" rule could still skip a transaction that ran longer than 5 s. Runner up: the 5 s rule, simpler but not airtight. Read queries run as plain statements, never inside an interactive transaction at repeatable read (an old snapshot only delays the feed).
- **The safe point** is `SELECT txid, seq FROM directory_changes WHERE txid < pg_snapshot_xmin(pg_current_snapshot()) ORDER BY txid DESC, seq DESC LIMIT 1`, across all systems; an empty result is `(0, 0)`. `txid` is cast to text in raw SQL and parsed as a bigint.
- **Type and systems come from comparing snapshots**, not from tracking each table change: simpler SQL, it skips saves that change nothing, and it needs no record of removed roles (the previous snapshot has them). Runner up: per change tracking with a rank table, more SQL and noisy rows.
- **One row per user per transaction.** The trigger upserts on `(txid, user_id)`, so a role change (a delete plus an insert) arrives as one change.
- **Cursor format:** base64url of `v1.<epoch>.<txid>.<seq>`, where `epoch` is `directory_feed.epoch`; anything else, or another epoch, is `INVALID_CURSOR`. The page cursor of `/directory/users` is base64url of `v1.<last id>`. The epoch makes a database restore visible instead of silently wrong.
- **No foreign key from feed rows to `users`**, so a hard delete (tests, a future erase) works and leaves its `deleted` row.
- **Backfill at migration** so "once held a role" (AC-6) has history from day one and a reader starting from the beginning gets everyone.
- **A lease with an owner, not a database lock**, for one VRMS copy at a time (AC-16): applying changes commits one by one, so a lock held in one long transaction can't express "done up to #104", and the owner check stops a copy that lost its lease from moving the cursor. This adds `lease_until` and `lease_owner` to the confirmed model.
- **10 pages a tick** keeps one tick short after a long outage; the next tick continues.
- **`idle_in_transaction_session_timeout` of 60 s** on the auth database role, so a forgotten open transaction can't hold the safe point back for long.

## Feature design

**Data model sketch**:

welinc-auth, new table `directory_feed` (one row):

| Column | Type | Rules |
|---|---|---|
| `id` | `boolean` | primary key, always `true` (check constraint) |
| `epoch` | `uuid` | required, random at creation; a new database gets a new one |

welinc-auth, new table `directory_changes`:

| Column | Type | Rules |
|---|---|---|
| `seq` | `bigint`, identity | primary key |
| `txid` | `xid8` | required, `pg_current_xact_id()` at the trigger |
| `user_id` | `uuid` | required, no foreign key (a hard delete must not fail or lose its row) |
| `type` | `text` | required, one of `created`, `updated`, `roles_changed`, `activated`, `deactivated`, `deleted` (check constraint) |
| `systems` | `"SystemType"[]` | required, may be empty for a user who holds no role before or after (such rows are never served) |
| `snapshot` | `jsonb` | required: `{ id, name, email, contact, profilePicture, isActive, deletedAt, updatedAt, roles: [{ system, role }] }`, roles sorted by system then role so equal states compare equal |
| `created_at` | `timestamptz(3)` | required, default `now()` (the transaction's start time) |

Unique `(txid, user_id)`. Index `(txid, seq)` for the feed read, index `(user_id, txid, seq)` for the previous row and lookup, GIN index on `systems`. Kept forever.

welinc-backend-vrms, new table `directory_sync_state`:

| Column | Type | Rules |
|---|---|---|
| `id` | `text` | primary key, always `'auth'` (check constraint) |
| `cursor` | `text` | nullable; null means "do a full read first" |
| `lease_until` | `timestamptz` | nullable; when the current claim runs out |
| `lease_owner` | `uuid` | nullable; the id of the current claim |
| `failing_since` | `timestamptz` | nullable; set while welinc-auth is failing |
| `updated_at` | `timestamptz` | last successful tick |

No change to `users`, `user_roles` or VRMS's `mechanics`.

**State transitions**: none on a stored entity. The poll job's own loop: no cursor → full read → cursor set → read changes each tick; recovery sync → full read again → cursor reset.

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/directory/users` | GET | `cursor?`, `limit?` (1 to 500) | `users`, `next`, `changesCursor` | service token, `directory.read` | 400 `INVALID_CURSOR`, 400 `VALIDATION_FAILED`, 401, 403 `FORBIDDEN`, 429 `RATE_LIMITED` |
| `/auth/directory/changes` | GET | `after?`, `limit?` (1 to 500) | `changes`, `next`, `hasMore` | service token, `directory.read` | 400 `INVALID_CURSOR`, 400 `VALIDATION_FAILED`, 401, 403 `FORBIDDEN`, 429 `RATE_LIMITED` |
| `/auth/directory/users/lookup` | POST | `ids: uuid[]` (1 to 200, no repeats) | `users`, `missing` | service token, `directory.read` | 400 `VALIDATION_FAILED`, 401, 403 `FORBIDDEN`, 429 `RATE_LIMITED` |
| `/auth/users` | GET | as today | as today | system admin only (service access removed; `/auth/users/lookup` and `/auth/users/:id` are already admin only) | 403 for service tokens |
| `/vrms/mechanics/sync` | POST | none | `created`, `updated`, `deactivated` | `users.manage` | 409 `SYNC_RUNNING`, 503 `AUTH_UNAVAILABLE` |
| `/vrms/mechanics/:authUserId/refresh` | POST | `authUserId: uuid` | `mechanicId`, `isActive` | `users.manage` | 400 bad id, 503 `AUTH_UNAVAILABLE` |

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| Any directory route | caller's system | `oauth_clients.system` of the token's `client_id` |
| Any directory route | may see phone | `directory.contact` in the token's `scope` |
| Feed row | `snapshot` | `users` and `user_roles` rows at commit, read inside the trigger; for a hard delete, the trigger's `OLD` row and the previous snapshot's roles |
| Feed row | previous snapshot | the user's row with the highest `(txid, seq)` from another transaction |
| Feed row | `systems` | systems in the new snapshot's roles plus systems in the previous snapshot's roles |
| Feed row | `type` | compared with the previous snapshot, first match: none → `created`; `deletedAt` set → `deleted`; `isActive` to false → `deactivated`; to true → `activated`; roles differ → `roles_changed`; else `updated` |
| Cursor | `epoch` | `directory_feed.epoch` |
| `/directory/changes` | which rows are safe | `txid < pg_snapshot_xmin(pg_current_snapshot())` |
| `/directory/changes` | `next` on a short page | the safe point |
| `/directory/users` | `changesCursor` | the safe point query, run before the page's scan |
| `/lookup` | "once held a role" | a `directory_changes` row for that user whose `systems` include the caller's |
| VRMS lease | `lease_owner` | a uuid made by the claiming tick |
| `DirectoryUser.phoneVerified` | `false` | decided here until S8 |
| `DirectoryUser.updatedAt` | `users.updated_at` (`snapshot.updatedAt` in the feed) | column |
| VRMS poll | the cursor | `directory_sync_state.cursor` |
| VRMS poll | mechanic role | `roleOf(roles)` on the snapshot's VRMS roles (Chief Mechanic wins, spec 0022 AC-4) |
| web-vrms after save | whose row to refresh | the `id` in welinc-auth's save response |

**Key invariants**:
- No change to a watched field or a role commits without its feed row in the same transaction (the trigger), and no feed row exists for a rolled back change.
- A reader that applies every change after its cursor, in order, ends with the same copy as one that did a full read now.
- A cursor never moves backwards in VRMS: it is written only in the same transaction as the change it passes, and only while `lease_owner` still matches.
- Two consecutive feed rows for one user never carry equal snapshots (ignoring `updatedAt`).
- Writes that skip triggers (`TRUNCATE`, `COPY`, `session_replication_role = replica`) are never used on `users` or `user_roles`.
- No system reads another system's roles or a phone it wasn't granted; filtering happens in welinc-auth before the response.
- Rows with empty `systems` are not served to anyone.

**Security model**: Only system backends read the directory, each through its own service token, and each sees only people tied to its own system and only that system's roles. Phones need the separate `directory.contact` scope; VRMS's client keeps only `directory.read`. People, admins included, can't call the directory; admin screens keep `/auth/users`, which no longer accepts service tokens. The feed holds personal data (names, emails, phones) forever; it lives only in welinc-auth's database, behind those routes. Security never depends on the feed: a removed user loses access through the session check (spec 0003), not through a system's copy.

**Configuration required**: no new env variables. `directory.read` is already in each system client's `serviceScopes`; `DIRECTORY_POLL_MS` is a code constant. The auth database role gets `idle_in_transaction_session_timeout = 60s` (set in the migration with `ALTER ROLE CURRENT_USER`, and noted for spec 0008's hosted database).

**Critical test scenarios**:
- Happy path: an admin gives Juan the VRMS Mechanic role in the portal; within one tick plus the safe point he appears active in VRMS's picker, verifies **AC-2**, **AC-5**, **AC-12**, **AC-13**
- Every door: each write path in AC-3 produces exactly one row with the right type; a password change produces none, verifies **AC-2**, **AC-3**
- Late commit: transaction A writes Juan and stays open; B writes Ana and commits; the feed serves neither A nor B's row until A ends, then both in `txid` order, verifies **AC-5**
- Lost last role: Ana loses her only VRMS role; VRMS gets one `roles_changed` with `roles: []` and sets her inactive; later changes to her name don't reach VRMS, verifies **AC-2**, **AC-5**, **AC-13**
- Apply failure: the apply of one change throws; the cursor stays before it and the next tick retries it, verifies **AC-14**
- No change: the seed script runs twice; the second run writes no feed rows, verifies **AC-2**, **AC-3**
- Two copies: two ticks at once; only one applies changes; a holder whose lease expired and was taken stops without writing, verifies **AC-16**
- Restore: a cursor from another epoch gives `INVALID_CURSOR`, and VRMS runs the full read on the next tick, verifies **AC-5**, **AC-12**
- Auth down: three failing ticks log one warning; recovery logs one line, verifies **AC-15**
- Auth/permission: an admin's token on `/auth/directory/changes` gets 403; a service token on `/auth/users` gets 403; a VRMS token gets `phone: null`, verifies **AC-7**, **AC-8**, **AC-9**

## Build plan

Tracer Bullet: the first milestone carries one role change from the portal into VRMS's picker through the trigger, the feed and the poll; the next ones thicken it.

1. **Thin thread.** welinc-auth hand written migration: `directory_feed`, `directory_changes`, the backfill, then the trigger function and deferred triggers, the idle timeout; `schema.prisma` declarations · the seed script saves each person in one transaction · `GET /auth/directory/changes` and `GET /auth/directory/users` with the service only guard, the per client 120 a minute limit and the `DirectoryUser` mapping · backend-vrms migration `directory_sync_state` · the poll job (lease, full read, change loop) applying through the existing roster write, satisfies **AC-1**, **AC-2**, **AC-4**, **AC-5**, **AC-7**, **AC-8**, **AC-11**, **AC-12**, **AC-13**, **AC-16**
2. **Lookup and instant refresh.** `POST /auth/directory/users/lookup` · `refreshOne` on lookup · `POST /vrms/mechanics/:authUserId/refresh` · web-vrms: drop the two page open syncs, refresh after each Users page save, the new toast text, satisfies **AC-6**, **AC-18**, **AC-19**, **AC-20**
3. **Hardening and the switch.** Stop on apply failure, warn once while auth is down, `INVALID_CURSOR` back to a full read · the lease owner check and renewal · recovery sync with `SYNC_RUNNING` · remove service access from `GET /auth/users` and VRMS's last `/auth/users` call · the every write path test suite and the late commit test, satisfies **AC-3**, **AC-9**, **AC-14**, **AC-15**, **AC-17**, **AC-21**
4. **Contract and docs.** Contract 0001 amendments · welinc-auth README directory section and `src/auth/` notes for the trigger · tests owed by the milestones above, satisfies **AC-10**

## Migration plan

**Strategy**: hard switch, as for S2 to S5. welinc-auth, welinc-backend-vrms and welinc-web-vrms merge together; only VRMS reads people today.
**Order**: stop welinc-auth, `npm run db:deploy` (creates the table, triggers and backfill), start it · then backend-vrms (its migration, then the poll job does its first full read on its own) · then web-vrms.
**Rollback**: revert the three PRs; the down migration drops the triggers, `directory_changes` and `directory_feed`. VRMS's roster rows are unaffected. If the feed is created again later it gets a new epoch, so VRMS's old cursor gives `INVALID_CURSOR` and it runs a full read.
**Risks**: a trigger bug blocks every user write (the trigger runs inside the write). The every write path tests in milestone 3 and the rollback above cover it. The backfill is one `INSERT ... SELECT`, fine at suite size (hundreds of people).

## Consequences

**Positive**:
- No code path in welinc-auth can change a person without the other systems hearing about it, including ones written later.
- VRMS stops downloading every user on two page loads and every save; the roster stays current on its own within about a minute.
- VMMS and BMS get a tested reader to copy for S11, and the BMS gateway gets a way off the auth database.
- Reading in transaction order makes "never skipped" a guarantee, not a timing bet.

**Negative / tradeoffs**:
- The trigger logic lives in SQL in a migration, where someone reading only TypeScript won't see it. Changing a watched field or adding a role table means changing the trigger, and the welinc-auth `AGENTS.md` must say so (`/sync`).
- Every user write now does a little more work at commit (one snapshot read, one upsert). Fine at suite scale; it is the first thing to look at if user writes ever get slow.
- Snapshots keep names, emails and phones forever, including for deleted people. A real deletion (erasing personal data) would also have to clean their feed rows.
- The safe point is held back by any long open transaction on the Postgres server (transaction ids are shared across its databases), so a stuck transaction delays the feed for every system until it ends. The idle timeout limits it; the welinc-auth `AGENTS.md` note must say "a stuck feed means look for an open transaction".
- A change made elsewhere takes up to about 30 s to reach VRMS (the instant refresh covers only VRMS's own saves).

**Neutral**:
- `user_changes` (the admin audit trail) stays as it is; the feed is not an audit log and has no actor.
- VRMS's Sync route stays but is no longer called by the app; it's a recovery tool.
- The webhook nudge in contract section 9 stays reserved; adding it later changes nothing here.

## Follow-up

- [ ] S11 migration guide: the VRMS poll job (`directory_sync_state`, the lease, stop on failure) as the reference reader for VMMS and BMS; BMS's gateway moves off `users`, `user_roles` and `user_activity_logs`.
- [ ] S8: add the phone verified column, put it in the snapshot and map it to `phoneVerified`.
- [ ] Spec 0008 (hosting): set `idle_in_transaction_session_timeout` on the hosted auth database too.
- [ ] S7 or a later privacy row: when a deletion request erases personal data, also clear the person's feed snapshots.
- [ ] `/sync` after the build: welinc-auth `AGENTS.md` notes the trigger and that new watched fields or role tables must update it; backend-vrms `AGENTS.md` notes the poll job.
