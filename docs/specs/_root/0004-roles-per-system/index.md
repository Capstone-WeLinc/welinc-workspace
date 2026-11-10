# 0004. Roles per system: a role catalog in welinc-auth

**Date**: 2026-11-08
**Status**: Accepted
**Partly superseded by**: [0005](../0005-user-directory/index.md) (AC-9 and the `GET /auth/users` routes row: a `directory.read` service token no longer reads `GET /auth/users`)
**Scope row**: [S5. Roles per system](../../../scope/_root/shared-services.md#s5-roles-per-system--done)
**Builds contract sections**: [0001](../0001-shared-services-contract/index.md) sections 4 (clients gain allowed roles), 10 (`/auth/systems`, `/auth/me`), 11 (three new error codes), 13 rule 5

## Summary

Each system (VRMS, VMMS, BMS) gets its own list of roles in welinc-auth, written in a small file per system and copied into two new tables by a sync step that runs after migrations. welinc-auth then refuses a role a system doesn't have, holds every system to one role per person (a per system limit that a system can raise later), marks which role is that system's admin, and lets an app such as `vmms-mobile` accept only some roles. Today there is one shared role list that any system accepts, so nothing stops `MECHANIC` in BMS or two VRMS roles on one person. VRMS proves it first: its user form reads its roles from the new public `/auth/systems` route. BMS gains Driver and Helper. The token's `roles` claim keeps its shape, so no system changes how it reads roles.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As a system's group, I want my roles and my role rules in one place in welinc-auth, so that I don't copy them into my code and adding a role to my system touches no other system.
- As a system Admin, I want user admin to refuse a role my system doesn't have, or a second role for one person, so that accounts can't drift into states my app can't handle.
- As a mobile app owner, I want only the roles my app serves to sign in, so that someone without a use for the app gets a clear refusal at login instead of an empty screen after it.
- As a web app, I want to read my system's roles, names and order from welinc-auth, so that a new role appears in my pickers with no web change.

**Acceptance criteria** (the contract):

*Catalog and sync*
- **AC-1**: `welinc-auth/prisma/catalog/` holds one file per system (`vrms.ts`, `vmms.ts`, `bms.ts`) exporting a `SystemDefinition`: `system` (a `SystemType`), `name`, `maxRolesPerUser` (a whole number of at least 1, or `null` for no limit) and `roles`, an ordered list of `{ code, name, description, isSystemAdmin? }`. The order in the file is both the display order and the power order (first is most powerful). The starting content is the *Catalog content* table below.
- **AC-2**: `npm run catalog:sync` reads every file and, in one transaction, makes `systems` and `system_roles` match them: inserts new roles, updates `name`, `description`, `sortOrder` (the position in the file, from 0) and `isSystemAdmin`, and deletes roles the file dropped. Run twice with no file change, it writes nothing and prints `VRMS: 3 roles, no change` (and the same per system).
- **AC-3**: Before any write, the sync refuses (exit code 1, nothing written) and lists the reason when: a code is not `^[A-Z][A-Z0-9_]{1,39}$`; a code repeats within a system; a system has no role, or not exactly one `isSystemAdmin` role; `maxRolesPerUser` is below 1; a `SystemType` value has no file; a dropped role is still held by any `user_roles` row (it prints the system, role, holder count and up to 20 holder emails); a lowered `maxRolesPerUser` is below what some account already holds in that system (it prints those accounts); or the admin flag moves to a role that no active account would hold after the sync. The first sync after the AC-6 migration finds no difference, so none of these refusals can block it. The sync takes `pg_advisory_xact_lock` (one fixed key) so two syncs never run at once, and `LOCK TABLE user_roles IN SHARE ROW EXCLUSIVE MODE` so no role can be granted between the "still held" check and the delete; the check is what produces the readable message, and the foreign key (AC-8) stays the last line of defence. `--dry-run` prints the same report and writes nothing.
- **AC-4**: A role's `code` never changes once synced. A file that renames a code is a drop plus an add, so AC-3's "still held" refusal covers it.
- **AC-5**: `npm run db:deploy` runs `prisma migrate deploy` and then `catalog:sync`, and stops at the first failure. The setup guide, `welinc-auth/AGENTS.md` and the hosting release step (spec 0008, when it exists) use `db:deploy` instead of a bare `prisma migrate deploy`. The order on every deploy is: stop welinc-auth, `npm run db:deploy`, `npm run seed:clients`, then start the new version (`npm run seed` only in development). A refused sync stops the deploy before the new version serves anything. The short outage is accepted: an old copy still running would send `'ADMIN'::"UserRole"` after the migration dropped that type.

*Migration*
- **AC-6**: One migration creates `systems` and `system_roles` and inserts the AC-1 starting catalog, so a following `catalog:sync` reports no change for every system.
- **AC-7**: Before it adds the foreign key, the same migration fixes existing rows that break the new rules, writing a `RAISE NOTICE` line for each row it deletes, with the user id only and no email, since migration logs are kept (`user <id>: removed BMS MECHANIC, not a BMS role` or `user <id>: removed VRMS MECHANIC, kept VRMS ADMIN`): it deletes `user_roles` rows whose (system, role) pair is not in the catalog, then, for each account holding more roles in a system than that system's limit, keeps the most powerful (`ORDER BY sort_order, created_at, id`, first row kept) and deletes the rest. It covers every account, inactive and soft deleted ones included. An account left with no role anywhere is kept as it is (it can't sign in, `NO_SYSTEM_ACCESS`) and gets its own notice line (`user <id>: no roles left`).
- **AC-8**: The migration then turns `user_roles.role` from the `UserRole` enum into text (`varchar(40)`, keeping every value), drops the `UserRole` type, and adds a foreign key from `user_roles (system, role)` to `system_roles (system, code)` that refuses deletes and updates. No other table changes except `oauth_clients` (AC-18).

*Enforcing the rules*
- **AC-9**: Every input that names a role (create user, edit user, the list filter on `GET /auth/users`) checks the (system, role) pair against the catalog. The list filter checks against the token's system (`aud`), for an admin and a `directory.read` service token alike. *Superseded in part by [0005](../0005-user-directory/index.md) AC-9 (2026-11-09): `GET /auth/users` is admin only now, so the list filter only ever checks an admin's system.* An unknown pair answers 400 `UNKNOWN_ROLE` with a message naming the system's valid roles: "BMS has no role 'MECHANIC'. Its roles are Admin, Operations, Customer Support, Driver, Helper."
- **AC-10**: A create or edit whose result gives an account more roles in a system than its `maxRolesPerUser` answers 409 `ROLE_LIMIT`: "VRMS allows one role per person." With a limit of 1, a request carrying two roles for one system is refused, never trimmed. The limit counts roles in one system only. Checks run in this order: today's 400 for an empty list or a duplicate row (`normalizeRoleAssignments`), the 403 for another system's role, AC-9's `UNKNOWN_ROLE`, then `ROLE_LIMIT`.
- **AC-11**: Editing a user's roles (`PATCH /auth/users/:id` with `roleAssignments`) replaces the caller's system roles in one step, as today, so changing Mechanic to Chief Mechanic is one request. Attaching a role to an existing account (create with `attachExisting`) still refuses an account that already holds a role in the caller's system (today's 409), so an attach can never change someone's role.
- **AC-12**: A caller can't change their own roles: editing your own `roleAssignments` keeps today's 409 "You can't change your own role.", and attaching to your own account is refused by AC-11's rule (you already hold a role in your system). A test covers both, so the S10 no self grants rule builds on a tested base.
- **AC-13**: Every role write on an existing account (attach, edit, delete of an account's roles) locks the account row (`SELECT ... FOR UPDATE` on `users`) as the first statement of its transaction, then reads the account's current roles (edit reads them again after the lock instead of trusting the read made before the transaction), then checks AC-9 and AC-10. Lock order is always the account row first, then any `user_roles` rows (the `assertAnotherAdmin` lock), so the two can't deadlock. Creating a brand new account needs no row lock: the unique email already stops a second create. Two admins editing one account at once can't leave it with two roles in a system.

*Admin role*
- **AC-14**: The user admin routes now guarded by `@Roles(UserRole.ADMIN)` are guarded by `@SystemAdmin()`: the caller holds the role marked `isSystemAdmin` in the token's system (`aud`). Every other place that tests for `ADMIN` asks the catalog instead, including the raw SQL in `assertAnotherAdmin` (`user-changes.ts`, today `role = 'ADMIN'::"UserRole" ... FOR UPDATE`, which becomes a join to `system_roles` on `is_system_admin`). The files that use `UserRole` today and change: `user-changes.ts`, `user-scope.ts` (`otherAdminSystems`, `assertNotAdminElsewhere`), `auth.service.ts` (the role types, the last admin check, `adminSystems()`, the admin reset in forgot password), `sessions/sessions.controller.ts`, `guards/request-authenticator.ts`, `guards/roles.guard.ts`, `decorators/roles.decorator.ts`, `dto/role-assignment.dto.ts`, `dto/list-users.query.dto.ts`, `prisma/seeds/users.seed.ts`, and every spec file using `UserRole.*`. `@Roles` and `RolesGuard` are deleted once nothing uses them. A build gate fails on any `UserRole` import from `@prisma/client` or `"UserRole"` in raw SQL under `src/` and `prisma/seeds/`. With today's catalog (`ADMIN` is every system's admin role) behaviour is unchanged.
- **AC-15**: The last admin rule keeps working through the flag: an edit or deactivation that would leave a system with no active holder of its admin role answers today's 409.

*Reading the catalog*
- **AC-16**: `GET /auth/systems` needs no token and answers `{ systems: SystemView[] }` in `SystemType` order, each `{ code, name, webAddress, maxRolesPerUser, roles: [{ code, name, description, isSystemAdmin }] }` with roles in file order. `webAddress` is the `web_address` of the system's active confidential client (`kind = CONFIDENTIAL`, `is_active`, `system = code`; the lowest `id` if several, `null` if none). It sends `Cache-Control: public, max-age=60` and an `ETag`, and answers 304 to a matching `If-None-Match`. It is reached through the gateway's existing `/auth` route, with that route's CORS list and rate limit; no new gateway rule.
- **AC-17**: `GET /auth/me` returns only the roles for the token's `aud`; a `?system=` that differs from `aud` answers 403 `WRONG_AUDIENCE` (the request authenticator checks it before the route runs, as contract 0001 section 10 records). Its only caller today is web-vrms's `authApi.ts` (backend-vrms's account check moved to `GET /auth/session` with spec 0003), always with a VRMS token, so they see the same roles. This narrows what a route returns, so contract 0001 records it as a behaviour change, not only an addition.

*Allowed apps*
- **AC-18**: `oauth_clients` gains `allowed_roles` (`jsonb`, default `{}`): `{ "<SYSTEM>": ["<code>", ...] }`. A system missing from the object means every role of that system may use the client. `seed:clients` sets `vmms-mobile` to `{ "VMMS": ["MECHANIC", "CHIEF_MECHANIC"], "VRMS": ["MECHANIC", "CHIEF_MECHANIC"] }` and adds a `bms-mobile` row (public native, grants `mobile_login` and `refresh_token`, audience `BMS`) with `{ "BMS": ["DRIVER", "HELPER"] }`. The seed runs after `db:deploy`, refuses a code the catalog doesn't have for that system, and refuses with "Run npm run db:deploy first." when the catalog is empty. The file is authoritative: a rerun overwrites a hand edited `allowed_roles`. Mobile login always uses the client's default system (`vmms-mobile`: VMMS); its `VRMS` entry applies when the app refreshes with `audience=VRMS`, as spec 0003 already allows.
- **AC-19**: Every user token grant (authorization code, refresh, mobile login) keeps only the roles the client allows for that audience. `rolesFor` returns both the roles held in the audience and the allowed ones. No role held there answers today's 403 `NO_SYSTEM_ACCESS`; roles held but none allowed on this client answers 403 `APP_NOT_ALLOWED` ("This app is for Mechanic and Chief Mechanic accounts."). Both are checked before any write, so the session is not changed. The portal's password login (`pickLoginSystem`) has no client limit and is unchanged. A role change reaches a signed in phone at its next refresh, within one access token lifetime.

*VRMS proves it*
- **AC-20**: The VRMS user form's role dropdown and the Users page role filter list the VRMS roles from `GET /auth/systems` (names, descriptions under each option, file order), not from `ROLE_OPTIONS`. While the catalog loads the dropdown is disabled; if the request fails the form shows "We couldn't load the roles." with Retry and can't be saved. The roles come from one `useVrmsRoles()` hook in `features/user-management/hooks/`, called once in `UsersPage` and passed down to the form and the filter (the page's existing plain hook pattern, like `useUsers`), with the request in a new `getSystems()` in `lib/api/authApi.ts`, so the page makes one request. A role code missing from the catalog can't occur after AC-8's foreign key; the existing "a role this page can't edit yet" lock stays as a fallback.

*Seed and BMS roles*
- **AC-21**: `npm run seed` writes role codes as text and passes the new rules unchanged (today's seed already does). BMS has `DRIVER` and `HELPER` in its catalog; seed people for them are S12's job.

### Catalog content (the starting files)

| System | Name | Limit | Roles in order (code, name, description); the first is the admin role |
|---|---|---|---|
| VRMS | Vehicle Repair Management System | 1 | `ADMIN` Admin: manages VRMS users, settings and every ticket · `CHIEF_MECHANIC` Chief Mechanic: assigns work and verifies finished repairs · `MECHANIC` Mechanic: works the repair tickets assigned to them |
| VMMS | Vehicle Maintenance Management System | 1 | `ADMIN` Admin: manages VMMS users and settings · `OPERATIONS` Operations: runs maintenance planning and schedules · `CHIEF_MECHANIC` Chief Mechanic: leads the maintenance mechanics · `MECHANIC` Mechanic: does scheduled maintenance work |
| BMS | Booking Management System | 1 | `ADMIN` Admin: manages BMS users and settings · `OPERATIONS` Operations: plans trips and dispatch · `CUSTOMER_SUPPORT` Customer Support: handles bookings and customers · `DRIVER` Driver: drives assigned trips (BMS mobile) · `HELPER` Helper: assists drivers on trips (BMS mobile) |

The VMMS and BMS descriptions are a first draft from their code; each group can reword its own file.

## Decision

**Chosen option**: Option 2: a catalog in tables, synced from one reviewed file per system.

welinc-auth keeps two new tables (`systems`, `system_roles`) that the database ties every role assignment to, filled only by `catalog:sync` from per system files in the repo; the shared `UserRole` enum goes away, while the `SystemType` enum stays.

**Implementation skills**: `prisma-cli` (`.claude/skills/prisma-cli/`) for the hand edited migration · `prisma-client-api` (`.claude/skills/prisma-client-api/`) for the composite relation and the row lock · `nestjs-best-practices` (`.claude/skills/nestjs-best-practices/`) for the `@SystemAdmin()` guard and the catalog service · `react-hook-form` (`.claude/skills/react-hook-form/`) for the VRMS role field

### Decided calls (made at write time)

- **Allowed apps live on the client, per audience** (`oauth_clients.allowed_roles`), not on each role. A client with no entry allows every role, so a new web client needs no role edits, and `vmms-mobile` serves two audiences (VMMS, and VRMS for its tab), which a per role list can't express. Runner up: an `allowedClients` list on each role.
- **"Most powerful" is the file order**, so no separate rank field exists. Admin is first in every system. Runner up: an explicit `rank` number.
- **Exactly one admin role per system is checked by the sync, not by a database index.** The sync is the only writer of `system_roles`, and a partial unique index is raw SQL that Prisma would drop on a later generated migration. Runner up: the partial index.
- **The migration's fixes are logged as `RAISE NOTICE` lines, not `user_changes` rows.** `user_changes.actor_id` must name a real user, and no user makes this change. Only seed accounts exist today, so a notice in the migration log is enough. Runner up: make `actor_id` nullable for system changes, which every reader of the change history would then have to handle.
- **`bms-mobile` is seeded now** (contract 0001 says it becomes a client like `vmms-mobile`), so allowed apps are tested on both mobile clients. Runner up: leave the row to S11.
- **No server side cache of the catalog.** The admin guard and every role write read `system_roles` directly (a primary key lookup of a few rows), so someone who loses admin through a sync loses it on their next request. Only `/auth/systems` is cached, through HTTP headers (AC-16). Runner up: an in memory cache with a short expiry, which would let a former admin keep admin routes until it expires.

## Feature design

**Data model sketch**:

| Table | Column | Type | Rules |
|---|---|---|---|
| `systems` (new) | `code` | `SystemType` | primary key |
| | `name` | `varchar(100)` | required |
| | `max_roles_per_user` | `int` | nullable (no limit); at least 1 when set |
| | `created_at`, `updated_at` | `timestamptz(6)` | |
| `system_roles` (new) | `system` | `SystemType` | primary key part 1; foreign key to `systems.code` |
| | `code` | `varchar(40)` | primary key part 2; `^[A-Z][A-Z0-9_]{1,39}$` |
| | `name` | `varchar(60)` | required |
| | `description` | `varchar(200)` | required |
| | `sort_order` | `int` | required; position in the file |
| | `is_system_admin` | `boolean` | default false; exactly one true per system (sync checked) |
| | `created_at`, `updated_at` | `timestamptz(6)` | |
| `user_roles` (changed) | `role` | `varchar(40)` (was enum `UserRole`) | foreign key `(system, role)` to `system_roles (system, code)`, on delete and update restrict; existing unique `(user_id, role, system)` kept |
| `oauth_clients` (changed) | `allowed_roles` | `jsonb` | default `{}` |

Relationships: `systems` 1:N `system_roles`; `system_roles` 1:N `user_roles`. Prisma: `SystemRole` with `@@id([system, code])`; `UserRoleAssignment` gets `systemRole SystemRole @relation(fields: [system, role], references: [system, code], onDelete: Restrict, onUpdate: Restrict)`. The `UserRole` enum is removed from `schema.prisma`; code that used it imports a `RoleCode` string type.

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/systems` | GET | `If-None-Match?` | `{ systems: SystemView[] }`, `ETag`, `Cache-Control` | none | 304 |
| `/auth/me` | GET | none (`?system=` ignored) | today's body, `roles` for `aud` only | user token | 401 |
| `/auth/users` | POST | `roleAssignments: { role: string, system }[]`, `attachExisting?` | today's body | system admin (`@SystemAdmin()`) | 400 `UNKNOWN_ROLE`, 409 `ROLE_LIMIT`, 409 `ACCOUNT_EXISTS`, 403 other system |
| `/auth/users/:id` | PATCH | `roleAssignments?` | today's body | system admin | 400 `UNKNOWN_ROLE`, 409 `ROLE_LIMIT`, 409 own role, 409 last admin |
| `/auth/users` | GET | `role?` (validated against the caller's system) | today's body | system admin (a `directory.read` service token no longer, [0005](../0005-user-directory/index.md) AC-9) | 400 `UNKNOWN_ROLE` |
| other `/auth/users*` admin routes | as today | as today | as today | system admin (was `@Roles(ADMIN)`) | as today |
| `/auth/token` (code, refresh), `/auth/mobile/login` | POST | as today | as today, `roles` filtered by the client's allowed roles | client | 403 `APP_NOT_ALLOWED` |

`RoleAssignmentDto.role` becomes `@IsString() @Matches(/^[A-Z][A-Z0-9_]{1,39}$/)`; `system` stays `@IsEnum(SystemType)`. The catalog check (AC-9) runs in the service, since a DTO can't read the database.

**Value sourcing**:

| Action | Value produced or displayed | Source |
|---|---|---|
| `/auth/systems` | `code`, `name`, `maxRolesPerUser` | `systems` row |
| `/auth/systems` | `webAddress` | `oauth_clients.web_address` of the row with `kind = CONFIDENTIAL` and `system = code` (seeded from `CLIENT_<ID>_WEB_ADDRESS`) |
| `/auth/systems` | roles, their order, admin flag | `system_roles` ordered by `sort_order` |
| `/auth/systems` | `ETag` | a hash of the response body |
| `UNKNOWN_ROLE` message | the system's valid role names | `system_roles.name` for that system, in order |
| `ROLE_LIMIT` message | the limit, as "one role" or "N roles" | `systems.max_roles_per_user` |
| `@SystemAdmin()` | the system to check | the token's `aud` (`caller.system`) |
| `@SystemAdmin()` | which role is admin | `system_roles.is_system_admin`, read per request |
| Token grants | roles in the token | `user_roles` for `aud`, filtered by `oauth_clients.allowed_roles[aud]` when present |
| `APP_NOT_ALLOWED` message | the allowed role names | `system_roles.name` for each code in `allowed_roles[aud]` |
| Migration fix | which role is kept | lowest `sort_order` in the inserted catalog |
| Sync refusal | holders of a dropped role | `user_roles` joined to `users.email`, up to 20 |
| VRMS role dropdown | options, order, descriptions | `GET /auth/systems`, the `VRMS` entry |

**Key invariants**:
- Every `user_roles` row names a role its system has (database foreign key).
- No account holds more roles in a system than `systems.max_roles_per_user` (service check under the account row lock).
- Each system has exactly one admin role, and an active holder of it (sync check plus the last admin rule).
- A role code never changes; `system_roles` is written only by `catalog:sync` (and the AC-6 migration).
- The token's `roles` claim keeps the shape `[{ role, system }]` and holds only `aud` roles the client allows.

**Security model**:
- `/auth/systems` is public on purpose: role names and descriptions are not secret, and the S4 launcher and every app's pickers need them before or without a session. It carries no user data and no permission list.
- Only a holder of the system's admin role (for the token's `aud`) may call the user admin routes, and only for that system's roles (today's `assertOwnSystemRoles`). Service tokens keep their `directory.read` path.
- Nobody changes their own roles (AC-12). The catalog changes only through a reviewed pull request to `welinc-auth` and the deploy step; no route edits it.
- `APP_NOT_ALLOWED` happens at the token grant, so a refused role never gets an access token for that app.

**Configuration required**: none. No new environment variables.

**Critical test scenarios**:
- Happy path: sync the starting catalog, open VRMS Users, create a Mechanic, change them to Chief Mechanic in one edit; the dropdown lists Admin, Chief Mechanic, Mechanic with descriptions. Verifies **AC-2**, **AC-11**, **AC-16**, **AC-20**.
- Unknown role: a VRMS admin sends `{ role: "DRIVER", system: "VRMS" }`, gets 400 `UNKNOWN_ROLE` naming the three VRMS roles. Verifies **AC-9**.
- Role limit: an edit carrying Admin and Mechanic for VRMS gets 409 `ROLE_LIMIT`; two concurrent edits on one account end with exactly one VRMS role. Verifies **AC-10**, **AC-13**.
- Sync refusal: drop `HELPER` from `bms.ts` while a seeded account holds it; the sync exits 1, lists the holder and writes nothing. Verifies **AC-3**.
- Migration fix: a database with a user holding VRMS `ADMIN` and VRMS `MECHANIC`, and one holding BMS `MECHANIC`, migrates to VRMS `ADMIN` only and no BMS role, with a notice per removed row. Verifies **AC-7**, **AC-8**.
- Allowed apps: a VMMS Operations account logs in on `vmms-mobile` and gets 403 `APP_NOT_ALLOWED`; a mechanic signed in on the phone is changed to Operations and their next refresh gets the same 403. Verifies **AC-18**, **AC-19**.
- Admin flag: with the flag moved to `OPERATIONS` in a test catalog, an Operations account can call `GET /auth/users` and an `ADMIN` account gets 403. Verifies **AC-14**.
- Own roles: a VRMS admin editing their own role gets 409, and attaching a role to their own email is refused. Verifies **AC-12**.

## Build plan

Tracer Bullet: the first task runs one role check end to end, from the files through the database and the API to the VRMS form; the later tasks widen it.

1. **Thin thread: catalog to VRMS form.** Catalog files and `SystemDefinition` type; `catalog:sync` with the AC-2 upsert and the AC-3 checks; `db:deploy`; the migration (tables, starting catalog, the AC-7 fixes, enum to text, foreign key; hand edit Prisma's generated enum change to `ALTER ... TYPE varchar(40) USING role::text` and `DROP TYPE "UserRole"` so no value is lost, then confirm with `prisma migrate diff` that the schema and migrations show no drift); Prisma models and `RoleCode` (a `string` type in `src/auth/roles/`, validated by the DTOs' `@Matches`); the catalog service (no cache) and a fake of it for unit tests; DTO change and the AC-9 and AC-10 checks under the row lock in create, attach and edit; `GET /auth/systems`; the VRMS dropdown and filter on it. Satisfies **AC-1** to **AC-11**, **AC-13**, **AC-16**, **AC-20**.
2. **Admin flag and `/auth/me`.** `@SystemAdmin()` replaces `@Roles(UserRole.ADMIN)`; every AC-14 file moves off `UserRole`, `assertAnotherAdmin`'s raw SQL included; `@Roles` and `RolesGuard` deleted; the grep gate; `/auth/me` filters to `aud`; the own role tests. Satisfies **AC-12**, **AC-14**, **AC-15**, **AC-17**.
3. **Allowed apps.** `allowed_roles` column (its own small migration), `seed:clients` values and the `bms-mobile` row with the catalog check, the filter in `rolesFor` for every grant, `APP_NOT_ALLOWED` before any write. Satisfies **AC-18**, **AC-19**.
4. **Seed, docs and the contract.** Seed writes codes as text; `welinc-auth/AGENTS.md`, the setup guide and the README use `db:deploy`; contract 0001 gains the `/auth/systems` shape in section 10, the three codes in section 11 and `allowed_roles` in section 4 (additive, same change), plus a note in section 10 that `/auth/me` now returns `aud` roles only (a narrowing; VRMS is its only caller); unit tests for the sync checks, the migration fix SQL against a fixture database, and the grant filter; lint, typecheck, build in welinc-auth and web-vrms. Satisfies **AC-5**, **AC-21**, and the test scenarios above.

## Migration plan

**Strategy**: no dual run. One migration converts the data in place; welinc-auth deploys first, then web-vrms. The API keeps its shapes (a role is still a string in JSON), so backend-vrms, the portal and the VMMS and BMS apps need no change.
**Phases**:
1. welinc-auth: back up the auth database, stop welinc-auth, `npm run db:deploy` (migration, then sync), `npm run seed:clients`, then start the new version (AC-5). Its routes answer the same bodies.
2. web-vrms: the dropdown reads `/auth/systems`. Deployed after phase 1, since the route must exist.
**Rollback**: restore the backup together with the previous welinc-auth image (the old code needs the `UserRole` type back, so neither works alone). Everything written to the auth database after the backup is lost: sessions (everyone signs in again) and any account or role change. The migration's fixes can't be reversed by a down migration, which is acceptable while only seed accounts exist.
**Risks**: Prisma generating a drop and recreate for the enum column (data loss) if the migration isn't hand edited; an old welinc-auth copy left running during the migration (stopped first, AC-5); the sync and the migration's starting catalog drifting (AC-6's "no change" test guards it).

## Consequences

**Positive**:
- A wrong role can't be stored at all; the database refuses it, not just the screen.
- Adding a role to one system is one line in that system's file and a deploy, with no change to the other systems or the token.
- VMMS's one role rule, BMS's Driver and Helper, and both mobile apps' role limits live in welinc-auth, which is what contract 0001 rule 5 promised.
- `/auth/systems` gives S4's launcher, S10's portal admin and every app's pickers one source of role names.

**Negative / tradeoffs**:
- A role change needs a pull request to the shared `welinc-auth` repo and a deploy, not a click. That's on purpose (reviewed changes), but it's slower than an admin screen.
- The starting catalog exists twice for one moment (in the migration and in the files); AC-6's test is the only guard.
- The migration deletes rows to fix bad data, and only a notice records it. Fine for seed data, wrong for real data without a backup first.
- `/auth/systems` is cached for up to 60 seconds in browsers, so a new role can take a minute to show in a picker.

**Neutral**:
- The `SystemType` enum stays, so a fourth system still needs a migration (alongside its clients, gateway routes and ports).
- Every file that imported `UserRole` from `@prisma/client` in welinc-auth changes to `RoleCode`.
- S10 adds permissions to `/auth/systems` later as an optional field (an additive contract change).

## Follow-up

- [ ] Confirm the role lists with VMMS and BMS (their message is out, 2026-11-08): BMS Driver and Helper, one role per person in both, any role they plan before the deadline, and whether the VMMS Admin still manages VMMS users (if not, the admin flag moves to another VMMS role in `vmms.ts`).
- [ ] S10: no self grants with the temporary access exception, central permissions and the portal user admin build on AC-12, AC-14 and `/auth/systems` (scope notes on 2026-11-08).
- [ ] S12: seed people for every role, Driver and Helper included.
- [ ] S11 migration guide: tell VMMS to drop its client side `getMobileAccessRole` check once `vmms-mobile` moves to welinc-auth (AC-19 does it on the server), and BMS to read role names from `/auth/systems`.
- [ ] Spec 0008 (hosting): the release step runs `npm run db:deploy` for welinc-auth.
