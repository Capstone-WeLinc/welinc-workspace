# 0009. welinc-auth owns every account; VRMS only checks who is calling

**Date**: 2026-10-27
**Status**: In Progress

## Summary

welinc-auth already handles every real sign in, but backend-vrms still carries a copied login module and its own `users` table, with different ids for the same people. This spec deletes that copy, so welinc-auth is the one owner of accounts, passwords, codes and roles. VRMS keeps only the token check, and now also asks welinc-auth every 30 seconds whether the caller is still active. VRMS links its mechanics and audit rows to the welinc-auth user id, and a self healing sync keeps the mechanic list in step, so a mechanic added on the Users page can be assigned straight away. welinc-auth also gets the hardening spec 0006 deferred: no codes in logs, saner reset and lock rules, admin safety guards, and a record of every admin change to a user.

## Rationale

Reasoning, options and the current state inventory: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As an admin, I want a mechanic I add on the Users page to show up in the assign picker, so that I can give them a ticket right away.
- As an admin, I want a deactivated or locked person to lose VRMS access within seconds, so that nobody I removed can still change tickets.
- As an admin, I want the server to stop me from deactivating myself or removing the last admin, so that nobody locks the team out by mistake.
- As an admin, I want a record of who changed which account and how, so that account changes can be traced.
- As the team, we want one sign in path and one account store, so that Admin OTP (WL-102) and reCAPTCHA (WL-103) land in exactly one place.

**Acceptance criteria**:

*One owner*

- **AC-1**: backend-vrms has no `/auth` routes. `AuthController`, `AuthService` and the 13 DTOs under `src/auth/dto/` are deleted, and `POST localhost:3002/auth/login` returns 404. `src/auth/` keeps only `JwtAuthGuard`, `RolesGuard`, `@Roles()`, the JWT strategy, the new account check (AC-4) and `roles.ts` (AC-2).
- **AC-2**: The backend-vrms Prisma schema has no `User`, `UserRoleAssignment`, `PasswordResetToken` or `RefreshToken` model and no `UserRole` or `SystemType` enum. Code imports `UserRole` and `SystemType` from `src/auth/roles.ts`, a `const` object with the same member names, so call sites change only their import path.
- **AC-3**: No code in backend-vrms reads or writes a password, an OTP, a reset token or a role assignment. Every login, OTP, reset, user admin and profile call from the portal and web-vrms goes to welinc-auth through the gateway's `/auth` route (unchanged).

*Account check on every VRMS request*

- **AC-4**: After `JwtAuthGuard` verifies the token's signature, every protected VRMS route confirms the account by calling welinc-auth `GET {AUTH_SERVICE_URL}/auth/me?system=VRMS`. The call sends only the caller's own `Authorization` header (no `Origin`, no `Referer`), using the built in `fetch` with `AbortSignal.timeout(3000)`. A 200 is cached per token for 30 seconds, or until the token's own `exp` if that comes sooner. Checks for the same token that are already in flight share one call. `req.user` is then built from that response, not from the token's claims: `sub` = `id`, `email`, `name`, `system` = `VRMS`, `roles` = the response's roles where `system` is `VRMS`. The check runs inside `JwtAuthGuard`, so it runs before `RolesGuard` and never runs on routes without `JwtAuthGuard`. backend-vrms refuses to start when `AUTH_SERVICE_URL` is missing.
- **AC-24**: In welinc-auth's JWT strategy, a valid `?system=` query value takes priority over a `system` claim in the token, `Origin`, `Referer` and the path. Every other caller behaves as today (additive).
- **AC-25**: VRMS maps welinc-auth's answer like this, and nothing else:

  | welinc-auth answer | VRMS returns |
  |---|---|
  | 200 with at least one VRMS role | runs the request |
  | 200 with no VRMS role | 401 "User does not have access to this system" |
  | 401 | 401 with welinc-auth's message |
  | 403 | 403 with welinc-auth's message |
  | timeout, connection error, 429, any 5xx, any other status, or a body it can't parse | 503 (AC-6) |
- **AC-5**: A user who is deactivated, locked, soft deleted, or left with no VRMS role in welinc-auth gets 401 from VRMS (403 when locked, carrying welinc-auth's message) within 30 seconds of the change, on reads and writes alike. A role change (for example MECHANIC to ADMIN) also applies within 30 seconds.
- **AC-6**: When welinc-auth gives no answer within 3 seconds, or answers 5xx, and the token has no fresh cache entry, VRMS returns 503 with `{ message: 'Sign in service unavailable. Try again in a moment.' }` and runs nothing. web-vrms shows that message as an error toast (at most one per 10 seconds) and does not sign the user out.
- **AC-7**: Only 200 answers are cached. A 401, 403 or 5xx is never cached, so the next request asks again.
- **AC-26**: In web-vrms, a 401, or a 403 whose message starts with "Account is locked", signs the user out and sends them to `{VITE_PORTAL_URL}/login`, showing the server's message there when the portal supports it and as a toast before leaving otherwise. Any other 403 (a wrong role) shows the message as a toast and keeps the user signed in.

*VRMS data keyed on the welinc-auth id*

- **AC-8**: `Mechanic` gains `authUserId` (uuid, unique, null for outsourced) and `email`, and loses `userId` and its relation. Every "which mechanic is calling" lookup uses `authUserId = req.user.sub`; none matches by email or name.
- **AC-9**: `GET /vrms/mechanics/available` returns `authUserId` and `email` from the `Mechanic` row. The Users page's deactivate open work check (spec 0006, AC-16) matches a user to a mechanic by `authUserId === user.id` only. The email and name fallbacks are removed.
- **AC-10**: Every new `AuditLog` row stores `userId = req.user.sub`, `email = req.user.email` and `actorName = req.user.name`. The audit timeline and history show `actorName`, or the email when it is null. The Person filter's `actorId` is a welinc-auth user id matched against `AuditLog.userId`. `GET /vrms/repairs/audit-logs/actors` is built from audit rows only. Rows with a null `userId` (backfilled `CREATED` rows, seeded knowledge rows) are left out. There is one entry per distinct `userId`, with the `actorName` and `email` of that user's newest row (ordered by `createdAt desc, id desc`). The VRMS users lookup (`findUsersByEmail`) is deleted. `actorName` is `varchar(100)`, the same limit as welinc-auth's `User.name`.

*Mechanic list kept in step*

- **AC-11**: `POST /vrms/mechanics/sync` (ADMIN) reads `GET {AUTH_SERVICE_URL}/auth/users?system=VRMS` with the caller's token. That list holds every non deleted user with a VRMS role, including inactive and locked ones. The sync then makes the in house `Mechanic` rows match:
  - each user holding a VRMS `MECHANIC` or `CHIEF_MECHANIC` role has a row with that `authUserId` (created when missing), with `name` copied, `email` copied in lowercase, and `isActive` = `user.isActive && !user.isLocked` (a locked mechanic leaves the picker until unlocked);
  - every in house row whose `authUserId` is not in that set (a deleted user, or a user with no VRMS mechanic role) is set `isActive = false`;
  - outsourced rows are never touched.
  Each row is compared before writing and written with an `upsert` on `authUserId`. A unique violation is retried once. The counts in `{ created, updated, deactivated }` include only rows that actually changed, so a second call straight after the first returns all zeros. Two concurrent calls, or a call racing a just in time check, leave one row per `authUserId` and never answer 500.
- **AC-12**: web-vrms calls the sync (a) after each successful create, edit, deactivate and reactivate on the Users page, and (b) once when an admin opens `/users` or `/repairs/new`. A failed sync after a save shows a warning toast: "Saved, but VRMS couldn't update its mechanic list. It will catch up next time this page opens." A failed sync on page open is silent. Neither one blocks the page or rolls back the save.
- **AC-13**: Just in time fallback. When the account check (AC-4) runs on a cache miss for a user holding a VRMS `MECHANIC` or `CHIEF_MECHANIC` role, VRMS makes sure an active `Mechanic` row with that `authUserId` exists, with the current `name` and lowercased `email`, before the request runs. It reads the row first (`findUnique` on `authUserId`) and writes only when the row is missing, inactive, or has a different name or email. The write sits outside any request transaction. A failed write is logged and never fails the request. Two first requests at once still end with exactly one row: a unique violation is caught and the row is read again.
- **AC-27**: Repair create takes in house mechanics by `id`. The DTO item for an in house mechanic carries `id` (uuid) instead of `name`, and the server rejects an unknown or inactive id with 400 "In house mechanic not found". Outsourced mechanics keep the name and shop flow. web-vrms's repair form sends the picker's `id`.
- **AC-14**: A `Mechanic` row with `isActive = false` is offered for no new assignment (both available lists already filter on it), and its past tickets and audit rows still show its name.

*One sign in door*

- **AC-15**: web-vrms's `StandaloneLoginForm` is deleted. `/login?token=…` runs the existing `SsoHandoff`. `/login` with no token redirects to `{VITE_PORTAL_URL}/login`. The axios interceptor no longer special cases `/auth/login`.

*welinc-auth hardening (from spec 0006's Follow-up)*

- **AC-16**: No OTP, reset code or request body is logged: the `console.log` calls in `forgotPassword` and `updateUser` are removed. Setup and reset emails link to `{PORTAL_URL}/forgot-password`. When `PORTAL_URL` is missing it falls back to `http://localhost:8000`, unless `NODE_ENV=production`, in which case the service refuses to start.
- **AC-17**: Completing a reset or setup code also clears `lockedAt` and sets `failedLoginAttempts` to 0. `forgot-password` for an inactive or deleted user sends nothing and returns the same generic message. Issuing a new code sets `usedAt` on that user's older unused codes, so only the newest code works.
- **AC-18**: `POST /auth/users` saves the user and returns 201 with the user plus `setupEmailSent: boolean`. A mail failure sets it to `false` and logs the failure without the code. It never answers 5xx for a saved user.
- **AC-19**: welinc-auth answers 409 with these messages. Each is checked inside the same transaction as the write. The last admin check first locks that system's `ADMIN` role rows (`SELECT … FOR UPDATE`), so two admins demoting or deactivating each other at once can't both pass. `updateUser`, `updateUserStatus` and `deleteUser` receive the acting admin's id from the token.
  - deactivating yourself: "You can't deactivate your own account."
  - changing your own roles: "You can't change your own role."
  - deleting yourself: "You can't delete your own account."
  - deactivating, deleting, or removing `ADMIN` from the last active, non deleted `ADMIN` of a system: "This is the last {system} admin."
  web-vrms shows the server's message as is.

*Admin change record*

- **AC-20**: Every admin write to a user writes `UserChange` rows in the same transaction as the change. The actor is the admin from the token.
  - `CREATED`: one row, `field` null.
  - `UPDATED`: one row per changed field (`name`, `email`, `contact`), with old and new values.
  - `ROLE_CHANGED`: field `roles`; old and new values are the sorted `ROLE@SYSTEM` list, comma separated.
  - `ACTIVATED` / `DEACTIVATED`, `UNLOCKED`, `DELETED`: one row each.
  - `RESET_SENT`: written when `forgot-password` carries a valid bearer token of an `ADMIN` of one of the target user's systems.
  A save that changes nothing writes no row. No password, hash or code is ever stored. A user editing their own profile writes no row.
- **AC-21**: `GET /auth/users/:id/changes?cursor=&limit=` (ADMIN) returns `{ data: [{ id, action, field, oldValue, newValue, actorId, actorEmail, createdAt }], nextCursor }`, newest first, `limit` defaults to 50 with a max of 100, keyset paged on `(createdAt, id)`. It returns 404 for an unknown user.

*Seeds and quality*

- **AC-22**: The welinc-auth seed and the backend-vrms seed give every shared person the same fixed UUID. After a `migrate reset` and seed in both repos, every seeded in house mechanic's `authUserId` equals their welinc-auth id, and a seeded mechanic signing in through the portal sees and updates only their own tickets.
- **AC-23**: `npm run lint`, `npm run build` and `npm run test` pass in welinc-auth and welinc-backend-vrms; `npm run lint`, `npm run typecheck` and `npm run build` pass in welinc-web-vrms. welinc-web-portal and the gateway config are unchanged.

## Decision

**Chosen option**: Option 2: welinc-auth owns every account; VRMS keeps a token check plus a live account check, and keys its data on the welinc-auth id.

The copied auth module and user tables leave backend-vrms. VRMS confirms each caller with welinc-auth (cached 30 seconds, fails closed). Mechanic rows are synced from welinc-auth by the Users page and the repair form, with a just in time fallback. welinc-auth gains the deferred hardening and an admin change record.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`) · `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-cli/`)

**Calls made in this spec** (each with the runner up):
- **`name` comes from the `/auth/me` answer, not a new token claim.** The account check already returns it, it is always current, and the shared token stays as it is for VMMS and BMS. This replaces the "add `name` to the token" line from the design conversation; the data model is otherwise unchanged. Runner up: a `name` claim, which goes stale until the next sign in and touches every group's token.
- **The cache is in memory, in each backend-vrms process.** It is keyed by the SHA 256 of the token (the raw token is never kept), holds 200 answers only, expires each entry after 30 seconds or at the token's `exp` (whichever comes first), and is capped at 5,000 entries (oldest dropped first). A second map of in flight promises makes concurrent checks for one token share a single call. With welinc-auth down, every uncached request waits up to the 3 second timeout; there is no negative cache, by AC-7. One container today; with more replicas each keeps its own cache, which is still correct. Runner up: Redis, which adds an operated store for no measured need.
- **VRMS calls welinc-auth directly on the internal network** (`AUTH_SERVICE_URL`, `http://auth-service:3001` in Docker), not through the gateway: one hop fewer, and the gateway stays a public entry only. Runner up: through the gateway, which adds a hop and couples to its routing.
- **The sync reuses `GET /auth/users?system=VRMS`.** It already returns inactive users with their roles, so welinc-auth needs no new read endpoint. Runner up: a new `GET /auth/users/:id` per person.
- **Role names move to `src/auth/roles.ts` as a `const` object** with the Prisma enum's member names and a matching type, so the change is an import path swap. Runner up: keep the unused Prisma enums in the schema, which leaves user concepts in the VRMS database.
- **Fixed seed ids are listed in both repos' seeds**, each with a comment naming the other file. Runner up: a shared package, which is too heavy for seed data.
- **`RESET_SENT` uses an optional bearer token on the public `forgot-password`**, through a small `OptionalJwtAuthGuard` that never rejects. The public flow is unchanged. Runner up: a separate admin reset endpoint, which changes spec 0006's calls.
- **`GET /auth/profile/summary` is not ported to VRMS.** web-vrms never calls it, and welinc-auth's copy returns zeros. It stays as is in welinc-auth for the other groups.
- **Port 3002 stays published in `docker-compose.vrms.yml`** for local debugging. With the auth routes gone, it exposes nothing that the gateway doesn't.

## Feature design

**Data model sketch**:

backend-vrms (one migration, then a reseed; nothing is deployed):
- `Mechanic`: add `authUserId` `uuid?` `@unique` (`auth_user_id`, null for outsourced, no foreign key) and `email` `varchar(255)?`. Drop `userId` and the `user` relation.
- `AuditLog`: add `actorName` `varchar(100)?` (`actor_name`). `userId` (already the welinc-auth id) and `email` stay.
- Drop `User`, `UserRoleAssignment`, `PasswordResetToken`, `RefreshToken` and the `UserRole` and `SystemType` enums.

welinc-auth (one additive migration):
- `UserChange` (`user_changes`): `id` uuid PK · `userId` uuid FK → `User` (the person changed; users are soft deleted only) · `actorId` uuid FK → `User` (the admin) · `actorEmail` `varchar(255)` · `action` enum `UserChangeAction` (`CREATED`, `UPDATED`, `ROLE_CHANGED`, `ACTIVATED`, `DEACTIVATED`, `UNLOCKED`, `RESET_SENT`, `DELETED`) · `field` `varchar(50)?` · `oldValue` `text?` · `newValue` `text?` · `createdAt` `timestamptz(3)`. Index `(userId, createdAt desc, id desc)`. Kept forever.

Links across databases (no foreign keys, by design): `Mechanic.authUserId` → welinc-auth `User.id` (1:1 when set), `AuditLog.userId` → welinc-auth `User.id` (N:1).

**State transitions**: a synced `Mechanic` row is `active` while its welinc-auth user is active and holds a VRMS mechanic role, and `inactive` otherwise. It moves only through the sync (AC-11) or the just in time check (AC-13, which only creates or reactivates). Rows are never deleted.

**API surface**:

| Endpoint | Service | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|---|
| `/auth/*` (17 routes) | backend-vrms | any | | removed | | 404 |
| every protected `/vrms/*` route | backend-vrms | any | bearer token | as today | JWT + account check | 401, 403, 503 |
| `/vrms/mechanics/sync` | backend-vrms | POST | none | `{ created, updated, deactivated }` | ADMIN | 401, 403, 503 |
| `/vrms/mechanics/available` | backend-vrms | GET | | `{ id, name, isAvailable, email, authUserId }[]` | ADMIN or MECHANIC (unchanged) | 401, 403 |
| `/vrms/repairs/audit-logs?actorId=` | backend-vrms | GET | `actorId` = welinc-auth id | as today, names from `actorName` | unchanged | 401, 403 |
| `/vrms/repairs/audit-logs/actors` | backend-vrms | GET | | `{ id, name, email }[]` from audit rows | unchanged | 401, 403 |
| `/auth/me?system=VRMS` | welinc-auth | GET | bearer | `ManagedUser` (existing) | JWT | 401, 403 |
| `/auth/users?system=VRMS` | welinc-auth | GET | bearer | `ManagedUser[]` (existing) | ADMIN | 401, 403 |
| `/auth/users` | welinc-auth | POST | as today | `ManagedUser` + `setupEmailSent` | ADMIN | 400, 409 |
| `/auth/users/:id`, `/:id/status`, `DELETE /:id` | welinc-auth | PATCH, DELETE | as today | as today | ADMIN | 404, 409 (AC-19) |
| `/auth/forgot-password` | welinc-auth | POST | `email`, optional bearer | generic message | public | 400 |
| `/auth/users/:id/changes` | welinc-auth | GET | `cursor?`, `limit?` | `{ data, nextCursor }` | ADMIN | 400, 404 |

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| account check | is the caller active, with which roles | welinc-auth `/auth/me?system=VRMS` answer (its strategy rejects inactive, locked, deleted and no VRMS role) |
| account check | the system welinc-auth checks | the `?system=VRMS` query, which wins over claims and headers (AC-24) |
| account check | VRMS status code and message | the AC-25 table |
| account check | cache entry lifetime | the smaller of 30 seconds and the token's `exp` claim |
| sync, just in time | `Mechanic.isActive` | `user.isActive && !user.isLocked` from the welinc-auth user |
| repair create | in house mechanic | the picker's `Mechanic.id` (AC-27) |
| audit actors list | name and email per person | the newest audit row per non null `userId` |
| web 401/403 handling | sign out or toast | status plus the "Account is locked" message prefix (AC-26) |
| account check | `req.user.name` | `/auth/me` answer `name` |
| account check | `req.user.roles` | `/auth/me` answer `roles`, filtered to `system = VRMS` |
| account check | cache key | SHA 256 of the bearer token |
| account check | timeout and TTL | constants in `src/auth/account-check.ts`: 3 seconds, 30 seconds, 5,000 entries |
| which mechanic is calling | `Mechanic` row | `Mechanic.authUserId = req.user.sub` |
| audit write | `actorName` | `req.user.name` |
| sync | users and roles | welinc-auth `GET /auth/users?system=VRMS` with the admin's bearer |
| sync, just in time | `Mechanic.name`, `email`, `isActive` | the welinc-auth user's `name`, `email`, `isActive` |
| sync | "is a mechanic" | holds a role `MECHANIC` or `CHIEF_MECHANIC` with `system = VRMS` |
| open work check (web) | user to mechanic match | `mechanic.authUserId === user.id` |
| last admin guard | other active admins | count of `User` with `isActive`, `deletedAt` null, a role `ADMIN` for that system, `id` ≠ target |
| `UserChange` | actor | the admin's token `sub` and `email` |
| `RESET_SENT` | actor | the optional bearer on `forgot-password`, kept only when it is an `ADMIN` of one of the target user's systems |
| email links | portal address | `PORTAL_URL` (welinc-auth env) |
| seeds | shared ids | fixed UUID table in each repo's seed |

**Key invariants**:
- welinc-auth is the only writer of accounts, passwords, codes and role assignments in the VRMS stack.
- No VRMS request runs on a session that welinc-auth has not confirmed within the last 30 seconds (fails closed).
- At most one `Mechanic` row per `authUserId` (database unique).
- The sync and the just in time check never delete a row and never touch an outsourced one.
- A `UserChange` row exists for every admin write, written in the same transaction; it never holds a secret.
- Every system always keeps at least one active admin, and no admin can deactivate, delete or demote themselves.

**Security model**:
- welinc-auth authenticates (password, OTP, lockout) and authorizes the account itself (active, not locked, holds a role in the requested system). VRMS authorizes actions with `RolesGuard` on the roles from the account check.
- VRMS forwards the caller's own token to welinc-auth. It holds no service credential and can never act as anyone other than the caller.
- `JWT_SECRET` still has to match, because VRMS verifies the signature before it calls welinc-auth (cheap rejection of forged tokens).
- Sync and the changes endpoint are ADMIN only. Any ADMIN may read any user's changes until feature 5 (permission matrix) scopes it by system.
- Tokens are never logged or stored. The cache holds only a hash of each token.

**Configuration required**:
- `AUTH_SERVICE_URL` (welinc-backend-vrms): internal base URL of welinc-auth, `http://auth-service:3001` in Docker, `http://localhost:3001` locally. Add it to `.env.example` and `docker-compose.vrms.yml`.
- `PORTAL_URL` (welinc-auth): the portal's public base URL for email links. Add it to `.env.example` and `docker-compose.auth.yml`. Required in production.

**Critical test scenarios**:
- Happy path: add mechanic Pedro on the Users page; the sync runs; Pedro is in the `/repairs/new` picker; he signs in through the portal and sees only his tickets; verifies **AC-11**, **AC-12**, **AC-8**, **AC-22**.
- Revocation: deactivate a signed in mechanic; within 30 seconds their next VRMS read returns 401; verifies **AC-5**, **AC-7**.
- Auth down: stop `welinc_auth_service`; a fresh token gets 503 and the toast, a cached one keeps working until its 30 seconds end; nothing is written; verifies **AC-6**.
- Sync failure: make the sync fail after a create; the warning toast shows; reopening `/users` fixes the row; verifies **AC-12**.
- Just in time: create a mechanic straight in welinc-auth (no sync); their first VRMS request creates the row; two parallel first requests leave one row; verifies **AC-13**.
- Old door closed: `POST localhost:3002/auth/login` returns 404; `/login` with no token lands on the portal; verifies **AC-1**, **AC-15**.
- Guards: the only VRMS admin tries to deactivate themselves and to demote themselves, and gets 409 each time; verifies **AC-19**.
- Change record: edit a user's name and role; two `UserChange` rows appear with the right old and new values; a no change save writes none; verifies **AC-20**, **AC-21**.

## Build plan

Tracer Bullet: slice 1 is one thin thread through every layer (a seeded mechanic signs in through the portal and works a ticket on the new identity model). Each later slice thickens one part. Work one repo at a time within a slice: welinc-auth, then backend-vrms, then web-vrms.

**Slice 1: thin thread, one identity end to end**
1. welinc-auth: fixed UUIDs in `prisma/seeds/users.seed.ts`; an explicit `?system=` wins in `jwt.strategy.ts`; `migrate reset` and seed locally, satisfies **AC-22**, **AC-24**
2. backend-vrms: `src/auth/roles.ts`; swap every `UserRole`/`SystemType` import from `@prisma/client`, found by a search at build time (today at least `roles.guard.ts`, `roles.decorator.ts`, `jwt.strategy.ts`, `knowledge-actor.ts`, `config.controller.ts`, `repairs.controller.ts`, `repairs.service.ts` and the two `repairs.*.spec.ts`), satisfies **AC-2**
3. backend-vrms: delete `auth.controller.ts`, `auth.service.ts`, `src/auth/dto/`; slim `auth.module.ts` to the guards and strategy, satisfies **AC-1**, **AC-3**
4. backend-vrms: migration (Mechanic `authUserId`/`email`, AuditLog `actorName`, drop the four user models and two enums); seeds: delete `prisma/seeds/users.seed.ts`, drop the `deleteMany` calls on the removed models in `prisma/seed.ts`, and set `authUserId` and `email` from the shared UUID table wherever a seed creates an in house `Mechanic` (including `repairs.seed.ts`), satisfies **AC-2**, **AC-8**, **AC-22**
5. backend-vrms: `src/auth/account-check.ts` (native `fetch`, 3 second timeout, cache with `exp` cap, in flight sharing, the AC-25 mapping) called from `JwtAuthGuard`; startup check for `AUTH_SERVICE_URL`, which also goes in `.env.example` and compose; an `AccountCheck` fake for unit and e2e tests, satisfies **AC-4**, **AC-5**, **AC-6**, **AC-7**, **AC-25**
6. backend-vrms: replace every use of the removed `User` model:
   - `getMechanicForUser` on `authUserId`;
   - the `actorId` filter's `prisma.user.findUnique` replaced by `AuditLog.userId`;
   - `findAuditActors` rebuilt per AC-10, and `findUsersByEmail` deleted;
   - `toAuditEvent` drops its `usersByEmail` argument and reads `actorName` (update `audit-events.spec.ts` fixtures);
   - `config.service.ts` selects `Mechanic.email` and `authUserId`;
   - audit writes set `actorName`;
   - `repairs.service.spec.ts` and `repairs.knowledge.spec.ts` mocks drop `prisma.user`.
   Satisfies **AC-8**, **AC-10**
7. web-vrms: in the axios interceptor, a 503 shows the toast without signing out; a 401 or a "locked" 403 signs out to the portal; any other 403 shows a toast, satisfies **AC-6**, **AC-26**

**Slice 2: mechanic list kept in step, one door**
8. backend-vrms: `POST /vrms/mechanics/sync` and the just in time ensure in the account check; `authUserId` and `email` on `mechanics/available`, satisfies **AC-9**, **AC-11**, **AC-13**, **AC-14**
9. web-vrms: sync calls after Users page saves and on opening `/users` and `/repairs/new`; open work match by `authUserId`, satisfies **AC-9**, **AC-12**
10. web-vrms: delete `StandaloneLoginForm`; `/login` with no token redirects to the portal; drop the `/auth/login` special case, satisfies **AC-15**
11. backend-vrms and web-vrms: repair create takes in house mechanics by `id` (DTO, `repairs.service.ts` lookup, repair form payload), satisfies **AC-27**

**Slice 3: welinc-auth hardening**
12. Remove the two `console.log`s; `PORTAL_URL` for email links with the production start check, satisfies **AC-16**
13. Reset clears the lock; no codes for inactive users; a new code retires older ones; `setupEmailSent` on create, satisfies **AC-17**, **AC-18**
14. Pass the acting admin's id into `updateUser`, `updateUserStatus`, `deleteUser`; self and last admin guards inside the write transactions, with `SELECT … FOR UPDATE` on the system's admin role rows, satisfies **AC-19**

**Slice 4: admin change record**
15. welinc-auth migration for `UserChange`; writes in every admin path; `OptionalJwtAuthGuard` on `forgot-password`, satisfies **AC-20**
16. `GET /auth/users/:id/changes`, satisfies **AC-21**

**Slice 5: close out**
17. Lint, build, test and typecheck in all three repos; restart `welinc_vrms_backend` and `welinc_auth_service` before the live checks, satisfies **AC-23**

## Migration plan

**Strategy**: big bang per repo. Nothing is deployed and both databases hold only seed data, so there is no live data to move.
**Phases**:
1. welinc-auth seed ids (slice 1, task 1), then `npx prisma migrate reset` in welinc-auth.
2. backend-vrms migration plus the new seed, then `npx prisma migrate reset` in backend-vrms. Both repos must be on the slice 1 code before anyone signs in, or the mechanic ids won't match.
3. welinc-auth's `UserChange` migration (slice 4) is additive and independent.
**Rollback**: revert the branch in each repo and reset both databases again.
**Risks**: a teammate with an old local database sees "In house mechanic not found" style errors until they reset both. Say so in each PR description.

## Consequences

**Positive**:
- One account store and one sign in door; WL-102 and WL-103 land once, in the portal and welinc-auth.
- The open `:3002/auth/login` and about 900 lines of drifting copy are gone.
- New mechanics are assignable at once, and name or email edits flow to VRMS. This closes spec 0006's two gaps.
- Deactivation, lock and role changes take effect in VRMS within 30 seconds.

**Negative / tradeoffs**:
- VRMS now depends on welinc-auth being up. If welinc-auth is down, VRMS returns 503 once the cached answers run out.
- One extra internal call per active token every 30 seconds, plus a first request that is slower by one round trip.
- `actorName` is a snapshot. Renaming a person doesn't rename their old audit rows.
- Any ADMIN can read any user's change record until feature 5 scopes it.
- The sync is pull based. A change made in welinc-auth by another tool shows up in the picker only after the next sync or that mechanic's next request.

**Neutral**:
- The backend-vrms `src/auth/` folder shrinks to guards; its `AGENTS.md` and the foundations rows A and B need their code paths updated (`/sync` owns that).
- welinc-auth's API stays backward compatible: one additive response field, one new endpoint, an explicit `?system=` that now wins, and 409s on paths that used to succeed wrongly.
- The repair create DTO changes shape for in house mechanics (`id` instead of `name`). web-vrms is its only client.

## Follow-up

- [ ] Tell the VMMS and BMS groups that their backends carry the same copied auth module and `users` table, and that the `:3002` style direct login hole likely exists there too. Their repos; not ours to edit.
- [ ] Once `setupEmailSent` and the unlock on reset ship, simplify spec 0006's AC-10 workaround and AC-20's two calls into one.
- [ ] A "Changes" view for `GET /auth/users/:id/changes` on the Users page, later (reports work).
- [ ] Feature 5 (permission matrix): scope the changes endpoint and the user list by system.
- [ ] welinc-auth has a `RefreshToken` table but no refresh endpoint. Decide whether refresh is ever needed or drop the table (talk to the other groups first).
- [ ] Update `welinc-backend-vrms/AGENTS.md` and `welinc-auth/AGENTS.md` (new env vars, the account check, the sync), and the foundations rows A and B code paths, through `/sync`.
