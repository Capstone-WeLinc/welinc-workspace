# 0011. Permission matrix: Admin editable grants, enforced with CASL

**Date**: 2026-10-29
**Updated**: 2026-10-31 (AC-12 narrowed by spec 0014 AC-6: `ticket.administer` no longer closes a ticket, closing and sending back need the new `ticket.verify`; the status route guard gains `ticket.verify`) · 2026-10-30 (AC-25 replaced by spec 0012 AC-24: the matrix is read and edited in the Settings hub)
**Status**: Accepted

## Summary

VRMS gets one list of everything a user can do (a permission catalog), and the database stores which role may do each thing. An Admin can switch rights on or off per role, except a few locked ones, and every change is logged. The server checks every request against that list through CASL (a JavaScript authorization library), and the web app reads the server's answers (which rights you hold, and what you may do on each ticket) so it hides exactly what the server blocks. The spec also scopes welinc-auth's user management by system, handles accounts shared with BMS or VMMS, and stops a deactivated mechanic's open tickets from being forgotten.

## Requirements

**User stories**:
- As an Admin, I want each role's rights stored in one place that I can change without a deploy, so that the system follows how the garages actually work.
- As any user, I want to see only the buttons and pages I may use, so that I never hit an action that fails.
- As the system owner, I want every request checked on the server and every denial answered with 403, so that hiding a button is never the only protection (WL-109).
- As a Chief Mechanic, I want to see every ticket, so that I can oversee the garage (WL-104).
- As a VRMS Admin, I want to manage only VRMS users and add an existing WeLinc account to VRMS, so that I never change another group's users by accident.
- As an Admin deactivating a mechanic, I want their open tickets either moved back to the queue or kept, so that no repair is silently stranded.

**Acceptance criteria**:

*The catalog and the stored matrix*
- **AC-1**: `src/auth/permissions/catalog.ts` in backend-vrms is the one definition of permission keys. Each entry has `key`, `label`, `group`, `description`, a default per matrix role (`ADMIN`, `CHIEF_MECHANIC`, `MECHANIC`) and an optional lock per role. It holds exactly the 16 keys in *Permission catalog* below, with those defaults and locks.
- **AC-2**: The database holds one `RolePermission` row per matrix role and catalog key (48 rows today), each with `allowed` true or false.
- **AC-3**: On startup the API, holding a Postgres advisory lock so two booting replicas never both insert, inserts every missing role and key row from the catalog defaults and never updates or deletes a row. An Admin's edit survives any number of restarts, deploys and rollbacks. A `PermissionChange` row with a null actor (shown as System) is written only for rows actually inserted, and the matrix version goes up by one when any row was inserted. Rows whose key is no longer in the catalog stay and are ignored (they deny, AC-6); `npm run permissions:prune` deletes them on purpose, logging each.
- **AC-4**: Locked cells can't be changed: `users.manage` and `permissions.manage` are locked on for `ADMIN` and locked off for `CHIEF_MECHANIC` and `MECHANIC`. A PATCH touching a locked cell is rejected with 400 and changes nothing. The ability factory takes a locked cell's value from the catalog and ignores its database row, so a hand edit in the database can't flip it.
- **AC-5**: A user's rights are the union of the grants of every VRMS role they hold. `CUSTOMER_SUPPORT`, `OPERATIONS` and any role outside the matrix grant nothing.
- **AC-6**: A missing row, an unknown key, or a role outside the matrix denies. Nothing falls back to allowing.

*Enforcement on the server*
- **AC-7**: Every backend-vrms route carries exactly one of `@RequirePermission(key)`, `@Authenticated()` or `@Public()`, as listed in *Route to key mapping*. Only `GET /` (health) is `@Public` and only `GET /vrms/permissions/me` is `@Authenticated`. A global guard denies (403) any route that has none. A unit test lists every controller route and fails if one lacks a decorator.
- **AC-8**: A request whose user lacks the route's key gets 403 `{ statusCode: 403, message: 'You do not have permission to do that.', permission: '<key>' }`. A structured warn log line records user id, roles, key, method and route path. No database row is written for a denial.
- **AC-9**: `RolesGuard`, `@Roles()`, `KNOWLEDGE_READERS`, `KNOWLEDGE_EDITORS`, `isKnowledgeEditor()` and `RepairsService.isMechanic()` are gone from backend-vrms. Every check they made now goes through the CASL ability (`PermissionsService.abilityFor(user)`). Only the granted key set is cached (per sorted role set and matrix version); the ability itself is built per request, because its ownership conditions carry the caller's own id. A test proves two mechanics with the same role never see each other's tickets.
- **AC-10**: Ticket reads (list, detail, history, dashboard summary) are scoped by the ability. `ticket.view` gives tickets assigned to the caller; `ticket.view_all` gives every ticket. List, history and summary filter in the query (`accessibleBy`); a detail request outside scope gets 403 `You are not assigned to this repair ticket` (as today).
- **AC-11**: Cost fields (`partsCost`, `laborCost`, `totalCost`) are returned only with `ticket.costs.view`, through `permittedFieldsOf`; the summary's `spend`, an aggregate, is nulled by the same key. Without it they are `null`, exactly as a mechanic sees them today. `PATCH :id/costs` needs `ticket.costs.edit`; cost fields sent on a status change without `ticket.costs.edit` are ignored, as today.
- **AC-12**: Status moves, checklist steps and knowledge links follow two keys. `ticket.work` allows `MECHANIC_ALLOWED_TRANSITIONS` (unchanged from today's code) on tickets assigned to the caller. `ticket.administer` allows every valid transition (close and cancel included) on any ticket. A caller with both acts as administer. Anyone else gets 403 `You are not assigned to this repair ticket` or today's transition message. A Chief Mechanic with `ticket.view_all` but no `ticket.administer` sees other mechanics' tickets read only.
- **AC-12a**: Ticket list and detail responses carry `can: { work, administer, editCosts, unlock }`, computed on the server from the caller's ability for that ticket. The web app shows ticket actions from these flags only.
- **AC-13**: Knowledge readers (`knowledge.view`) see only `ACTIVE` entries and get 404 for any other (as today). `knowledge.edit` sees drafts and inactive entries, typical costs and recent tickets, and may write. `knowledge.suggest` may post suggestions.
- **AC-14**: With the default matrix, every role sees the same as before this feature, with one exception: a Chief Mechanic now sees every ticket (read only, no costs).
- **AC-15**: A Jest e2e table test walks every route against every matrix role under the default matrix. It expects 403 when the role lacks the route's key and anything but 403 when it has it. A new route or key is covered without writing a new test.

*Matrix API, cache and history*
- **AC-16**: `GET /vrms/permissions/me` (any signed in VRMS user) returns `{ keys, version }`: the caller's granted keys and the matrix version. No CASL rules are sent; the server is the only place rules with conditions are evaluated.
- **AC-17**: `GET /vrms/permissions` (`permissions.manage`) returns the three roles with their display labels, every catalog key grouped, each role's `allowed` and lock, and the matrix `version`.
- **AC-18**: `PATCH /vrms/permissions` (`permissions.manage`) takes `{ changes: [{ role, permission, allowed }], note?, version }`. Inside one transaction it locks the `permission_matrix` row (`SELECT … FOR UPDATE`), compares `version`, applies every change, and adds one to the version; all or nothing. An unknown role or key, a locked cell, more than 100 changes, or a note over 500 characters gets 400. A `version` that differs gets 409 `The permissions were changed by someone else. Reload to see the latest.` A change to the value a cell already has is skipped and not logged; if every change is skipped, the answer is 200 and the version stays.
- **AC-19**: Each applied cell writes one `PermissionChange` row (role, key, before, after, actor id, name, email, note, time). The note is trimmed and stored as null when empty. `GET /vrms/permissions/changes?cursor=&limit=` (`permissions.manage`) returns them newest first, `limit` 50 by default and at most 100, keyset paged on `(createdAt, id)` with the same cursor format as spec 0009's `/auth/users/:id/changes`; a bad cursor gets 400. Rows are kept forever.
- **AC-20**: Each request that needs a check reads the one row `permission_matrix.version` (a primary key lookup). When it differs from the replica's cached version, the replica reloads the grants before answering. An edit applies on the very next request on every replica.
- **AC-21**: If that read or a reload fails, the replica keeps using the last matrix it loaded and logs a warning. A replica that has never loaded one answers 503, and its readiness probe fails until it loads, so no traffic is routed to it.

*The web app*
- **AC-22a**: The Analytics page (`/analytics`) and its nav item are shown only with `analytics.view`; by default that is Admin only, as today. A user without the key who opens `/analytics` by URL is sent to the dashboard. The nav group title reads "Analytics & AI" with the key and "Knowledge base" without it. Until feature 3 moves analytics into backend-vrms, this key gates the screen only: the analytics service does not check the JWT, so its API stays open to anyone who can reach the gateway (see *Consequences*).
- **AC-22**: web-vrms builds one CASL ability (`@casl/ability`, `@casl/react`) from the keys in `/vrms/permissions/me` and uses it with `<Can>` for every route guard, nav item and page level button; ticket level buttons use the ticket's `can` flags (AC-12a). `RequireRole`, `KNOWLEDGE_EDITOR_ROLES`, `isKnowledgeEditor`, `isMechanicRole` and the role switch in `navItems.ts` are gone.
- **AC-23**: The web app fetches `/vrms/permissions/me` after sign in, again when the window regains focus, every 60 seconds, and right after any 403. Until the first answer arrives, it shows the shell loading state and no guarded item. If that first fetch fails, it shows an error state with Retry instead of loading forever. A 401 follows the existing sign out flow. A user whose `keys` are empty sees a "No VRMS access" screen with Sign out.
- **AC-24**: On a 403 the web app shows the toast `You no longer have permission to do that.` (this fixed text, whatever the body says; at most one such toast per 5 seconds), refetches the permissions, and sends the user to the dashboard if the current page needs a key they no longer hold.
- **AC-25** (replaced by spec 0012, AC-24, 2026-10-30; the Users page no longer has this section, and the matrix is read and edited in Settings, Roles and permissions): The Users page had a read only "Roles and permissions" section, shown only with `permissions.manage`. It read `GET /vrms/permissions` and `GET /vrms/permissions/changes?limit=10`: a table of keys (grouped, with labels) against the three role labels, showing allowed, not allowed and locked, plus the last 10 changes (a null actor shows as System; a null before shows as Added, a null after as Removed). Editing waited for feature 52.

*welinc-auth: users scoped by system*
- **AC-26**: Every admin user endpoint in welinc-auth acts only on users who hold a role in the caller's system (the request's resolved system, spec 0009 AC-24). The user list ignores a `system` query that differs and returns only those users; each user's `roles` holds only the caller's system roles, plus `otherSystems` (system names only, empty when none). Any other user answers 404, including `GET /auth/users/:id/changes`.
- **AC-27**: A role edit may only add, change or remove roles of the caller's system. Sending another system's role gets 403. Roles in other systems are always kept.
- **AC-28**: A shared account is one that also holds a role in another system. On a shared account a VRMS admin may edit the name, change or remove its VRMS roles (an empty role list removes it from VRMS), deactivate, send a reset code and unlock. They may also set a password and change the email, unless the account is `ADMIN` in another system: then those two answer 403 `This account is an admin in <systems>. Send a reset code instead.` Delete answers 403 `This account is shared with <systems>. Remove its VRMS role instead.` An empty role list on an account with no other system's role gets 400 (use deactivate).
- **AC-29**: `GET /auth/users/lookup?q=` (ADMIN) returns at most 10 active, not deleted accounts whose name or email contains `q` (2 characters at least, case insensitive) and that hold no role in the caller's system: `[{ id, name, email, systems }]` (system names) and nothing else. Each admin may call it at most 30 times a minute; more gets 429.
- **AC-30**: `POST /auth/users` with an email that already belongs to an account answers 409 `{ code: 'ACCOUNT_EXISTS', id, name, systems }` when that account is active and has no role in the caller's system. Sent again with `attachExisting: true`, it adds only the given roles of the caller's system to that account (password, name and other roles untouched) and writes a `ROLE_CHANGED` UserChange row. A deactivated or deleted account, or one already in the caller's system, still gets the plain 409.

*Open work when someone leaves VRMS*
- **AC-31**: The mechanic roster marks a `Mechanic` inactive only when the account is deactivated or loses its VRMS mechanic role, never because the account is locked.
- **AC-32**: `GET /vrms/mechanics/:authUserId/open-work` (`users.manage`) returns `{ total, byStatus }` for tickets in `OPEN_STATUSES` (from `ticket-statuses.ts`) assigned to that person. `byStatus` is an object with every open status as a key, zeros included. A person with no `Mechanic` row gets `{ total: 0 }` with all zeros.
- **AC-33**: `POST /vrms/mechanics/:authUserId/release-tickets` (`users.manage`) with `{ reason: 'DEACTIVATED' | 'ROLE_REMOVED' }` first refreshes that person's `Mechanic` row from welinc-auth. It answers 404 if there is no `Mechanic` row and 409 `They still have access to VRMS.` if the person is still an active VRMS mechanic. Otherwise it ends their assignment on every open ticket in one transaction and returns `{ released, reopened }` (tickets changed, and how many of those went back to `OPEN`). Calling it again releases 0. An `ASSIGNED` ticket with no mechanic left goes back to `OPEN`. `IN_PROGRESS` and `ON_HOLD` tickets keep their status. `FOR_VERIFICATION` and later statuses are not touched. Each changed ticket gets one `MECHANIC_UNASSIGNED` audit event, with the caller as actor and the note `Account deactivated` or `VRMS role removed`.
- **AC-34**: Ticket list and detail responses carry `hasInactiveMechanic` (an open ticket assigned to an inactive mechanic) and `needsMechanic` (`IN_PROGRESS` or `ON_HOLD` with no assignment to an active `Mechanic`; every `Mechanic` row is in house). Both are computed in the list query, with no extra query per row. The repair list shows an "Inactive mechanic" or "Needs a mechanic" badge, and the dashboard's attention list includes both.
- **AC-35**: On the Users page, deactivating someone or removing their VRMS role first checks open work. With open tickets, the confirm shows the count by status and the choice "Move them back to the queue" (default) or "Keep them assigned". It never blocks. This replaces spec 0006 AC-16's "Reassign first" block. On a shared account the confirm also says `This also blocks their <systems> sign in.` (deactivate) and the release runs after the welinc-auth call succeeds; if it fails, a toast offers Retry.
- **AC-36**: Add user offers "New account" or "Existing WeLinc account". The existing path searches `/auth/users/lookup` and attaches a VRMS role. Typing an email that answers `ACCOUNT_EXISTS` in the new path shows `This email already has a WeLinc account (in <systems>). Add the <role> role in VRMS to it? They keep their current password.` and attaches on confirm. Editing a shared account notes that a new email changes their sign in for every system; on an account that is an admin elsewhere, the email field and Set password are read only. Delete is hidden for any shared account.

*Close out*
- **AC-37**: Lint, build and tests pass in welinc-backend-vrms, welinc-web-vrms and welinc-auth, plus typecheck in web-vrms.

## Decision

**Chosen option**: Option 3: a code catalog with database grants, enforced through CASL.

Permission keys, labels, locks and defaults live in typed code; each role's on or off lives in Postgres; a CASL ability built from a user's granted keys answers every check on the server; the browser builds its own CASL ability from the same keys, and ticket level answers come from the server as per ticket flags.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`) · `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-cli/`) · `vercel-react-best-practices` (`.claude/skills/vercel-react-best-practices/`)

**Decisions made in the spec (with the runner up):**
- **Status and step rights split into `ticket.work` (own tickets, mechanic transitions) and `ticket.administer` (any ticket, every transition).** That is exactly today's `isMechanic` split, so defaults change nothing. Runner up: one `ticket.status.update` key with the split hardcoded per role, which leaves a role rule in code.
- **`mechanics/sync` and the open work endpoints use `users.manage`**, since they only ever run from the Users page. Runner up: their own key, an extra checkbox nobody would set differently.
- **Matrix version is an integer in a one row `permission_matrix` table**, locked and bumped in the PATCH transaction, and read on every checked request. Runner up: the newest `updatedAt`, which collides at the millisecond and moves backwards on deletes; and a 30 second cache, which leaves revoked rights live on the other replica.
- **The granted key set is cached per (sorted role set, matrix version); the ability is built per request**, since its conditions hold the caller's id. Runner up: caching whole abilities per role set, which would leak one user's ticket scope to another.
- **The browser gets keys plus per ticket flags, not packed rules.** CASL conditions here are Prisma shaped (`assignments.some.mechanic.authUserId`) and don't match the ticket JSON, so a browser copy would answer wrongly without an error. Runner up: packed rules with a JSON shaped mirror of each condition, a second copy to keep in step.
- **Startup never deletes rows**, so rolling deploys and rollbacks can't fight over keys. Runner up: delete unknown keys at boot, which resets Admin edits when an old and new image run side by side.
- **CASL action names avoid `manage`**, which CASL reserves for "any action".
- **Release runs after deactivate, not before**, because cutting access is the urgent part; the "Inactive mechanic" badge covers a failed release.
- **`npm run seed` resets the matrix to the catalog defaults**, so a local reset starts clean; production never runs it.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

### Permission catalog

Defaults: ✓ allowed, ✗ not allowed, 🔒 locked. Every key the code has today, nothing for future features (AC-1, AC-14).

| Group | Key | Label | Admin | Chief Mechanic | Mechanic | Today's equivalent |
|---|---|---|---|---|---|---|
| Tickets | `ticket.view` | See tickets assigned to you | ✓ | ✓ | ✓ | every ticket route's role list |
| Tickets | `ticket.view_all` | See every ticket | ✓ | ✓ (new) | ✗ | `!isMechanic` in list, detail, history, summary |
| Tickets | `ticket.create` | Create tickets and pick mechanics | ✓ | ✗ | ✗ | `POST /repairs`, `GET available-mechanics` |
| Tickets | `ticket.work` | Work your assigned tickets (status, steps, knowledge link) | ✗ | ✓ | ✓ | `isMechanic` branch of `updateStatus`, `assertCanWork` |
| Tickets | `ticket.administer` | Move any ticket to any valid status, including close and cancel | ✓ | ✗ | ✗ | `!isMechanic` branch of the same |
| Tickets | `ticket.costs.view` | See costs | ✓ | ✗ | ✗ | `formatTicket(t, isMechanic)`, summary `spend` |
| Tickets | `ticket.costs.edit` | Encode costs | ✓ | ✗ | ✗ | `PATCH :id/costs`, cost fields on status |
| Tickets | `ticket.unlock` | Unlock closed tickets | ✓ | ✗ | ✗ | `PATCH :id/unlock` |
| Records | `audit.view` | See the audit log | ✓ | ✗ | ✗ | `GET audit-logs`, `audit-logs/actors` |
| Records | `analytics.view` | See the Analytics page | ✓ | ✗ | ✗ | `RequireRole role="ADMIN"` on `/analytics`, `analytics` flag in `navItems.ts` |
| Records | `config.read` | Read garages, vehicles, drivers and mechanics | ✓ | ✓ | ✓ | `GET config/*`, `mechanics/available` |
| Knowledge | `knowledge.view` | Read the fix library | ✓ | ✓ | ✓ | `KNOWLEDGE_READERS` |
| Knowledge | `knowledge.suggest` | Suggest a fix library entry | ✓ | ✓ | ✓ | `POST suggestions` |
| Knowledge | `knowledge.edit` | Edit the fix library and review suggestions | ✓ | ✓ | ✗ | `KNOWLEDGE_EDITORS` |
| Admin | `users.manage` | Manage users | ✓🔒 | ✗🔒 | ✗🔒 | `@Roles(ADMIN)` in welinc-auth, `mechanics/sync` |
| Admin | `permissions.manage` | View and change permissions | ✓🔒 | ✗🔒 | ✗🔒 | new |

**Rule for later features**: a feature that adds an action adds its key to the catalog with a default of ✓ for Admin and ✗ for the other roles, unless its own spec says otherwise, plus its CASL rule and its `@RequirePermission`. The startup backfill delivers the rows (AC-3).

### CASL rules per key

The ability factory (`src/auth/permissions/ability.factory.ts`) turns granted keys into rules. Subjects are Prisma model names through `@casl/prisma`'s `PrismaQuery` typing.

| Key | Rule |
|---|---|
| `ticket.view` | `can('read', 'RepairTicket', { assignments: { some: { mechanic: { authUserId: user.sub } } } })` |
| `ticket.view_all` | `can('read', 'RepairTicket')` |
| `ticket.create` | `can('create', 'RepairTicket')` |
| `ticket.work` | `can('work', 'RepairTicket', { assignments: { some: { mechanic: { authUserId: user.sub } } } })` |
| `ticket.administer` | `can('administer', 'RepairTicket')` |
| `ticket.costs.view` | without it: `cannot('read', 'RepairTicket', ['partsCost', 'laborCost', 'totalCost'])`, added after every `can` rule (in CASL a later rule wins) |
| `ticket.costs.edit` | `can('editCosts', 'RepairTicket')` |
| `ticket.unlock` | `can('unlock', 'RepairTicket')` |
| `knowledge.view` | `can('read', 'KnowledgeEntry', { status: 'ACTIVE' })` |
| `knowledge.edit` | `can('read', 'KnowledgeEntry')`, `can('edit', 'KnowledgeEntry')`, `can('edit', 'IssueCategory')`, `can('review', 'KnowledgeSuggestion')` |
| `knowledge.suggest` | `can('create', 'KnowledgeSuggestion')` |
| the rest | `can('<key>', 'Permission')`, a plain flag checked by the guard |

Every key also yields the flag rule `can(key, 'Permission')`, which is what `@RequirePermission(key)` checks. Services use `accessibleBy(ability, 'read').RepairTicket` for queries, `ability.can('work', subject('RepairTicket', ticket))` for single rows (the ticket loaded with `assignments.mechanic` so the condition can match), and `permittedFieldsOf` to null hidden fields. Locked cells come from the catalog, never the database row (AC-4). The browser builds only flag rules (`can(key, 'Permission')`) from `/me`'s keys.

### Route to key mapping

| Route | Decorator |
|---|---|
| `GET /` | `@Public()` |
| `GET /vrms/permissions/me` | `@Authenticated()` |
| `GET /vrms/permissions`, `PATCH /vrms/permissions`, `GET /vrms/permissions/changes` | `permissions.manage` |
| `POST /vrms/repairs`, `GET /vrms/repairs/available-mechanics` | `ticket.create` |
| `GET /vrms/repairs`, `GET /vrms/repairs/history`, `GET /vrms/repairs/:id` | `ticket.view` or `ticket.view_all` (either; scope from the ability) |
| `PATCH /vrms/repairs/:id/status` | `ticket.work`, `ticket.administer` or `ticket.verify` (any; each move's own right is checked in the service, spec 0014 AC-5, AC-6) |
| `PATCH …/issues/:issueId/knowledge`, `PATCH …/issues/:issueId/steps/:stepId` | `ticket.work` or `ticket.administer` (either; ownership from the ability) |
| `PATCH /vrms/repairs/:id/costs` | `ticket.costs.edit` |
| `PATCH /vrms/repairs/:id/unlock` | `ticket.unlock` |
| `GET /vrms/repairs/audit-logs`, `GET /vrms/repairs/audit-logs/actors` | `audit.view` |
| `GET /vrms/config/garages`, `config/vehicles`, `config/drivers`, `GET /vrms/mechanics/available` | `config.read` |
| `POST /vrms/mechanics/sync`, `GET /vrms/mechanics/:authUserId/open-work`, `POST /vrms/mechanics/:authUserId/release-tickets` | `users.manage` |
| `GET /vrms/knowledge/categories`, `entries`, `entries/options`, `entries/:id` | `knowledge.view` (editor extras from the ability) |
| `POST /vrms/knowledge/suggestions` | `knowledge.suggest` |
| `POST`/`PATCH /vrms/knowledge/categories…`, `POST`/`PATCH entries…`, `PATCH entries/:id/status`, `GET entries/:id/changes`, `GET suggestions`, `GET suggestions/count`, `POST suggestions/dismiss-group`, `PATCH suggestions/:id` | `knowledge.edit` |

`analytics.view` has no backend-vrms route yet: the analytics endpoints live in the Python service, which has no auth, so today the key is read by the web app only. When feature 3 rebuilds analytics inside backend-vrms, every analytics route there carries `@RequirePermission('analytics.view')` (and the AC-15 table covers it with no new test).

`@RequirePermission` takes one key or a list meaning "any of these". The dashboard reads `GET /vrms/repairs` and its summary; there is no other route. No config write route exists today.

### Data model sketch

`RolePermission` (`role_permissions`), backend-vrms:

| Field | Type | Null | Notes |
|---|---|---|---|
| `role` | `varchar(30)` | no | PK part; `ADMIN`, `CHIEF_MECHANIC`, `MECHANIC` |
| `permission` | `varchar(60)` | no | PK part; a catalog key |
| `allowed` | `boolean` | no | |
| `updatedAt` | `timestamptz(3)` | no | `@updatedAt` |
| `updatedByUserId` | `uuid` | yes | welinc-auth user id, no foreign key; null for System |

Primary key `(role, permission)`. No foreign keys: roles and keys are code constants.

`PermissionMatrix` (`permission_matrix`), backend-vrms: one row, created by the migration.

| Field | Type | Null | Notes |
|---|---|---|---|
| `id` | `smallint` | no | PK, always `1` (a check constraint keeps it one row) |
| `version` | `integer` | no | starts at `1`; plus one per PATCH that changed something and per backfill that inserted rows |
| `updatedAt` | `timestamptz(3)` | no | `@updatedAt` |

`PermissionChange` (`permission_changes`), backend-vrms:

| Field | Type | Null | Notes |
|---|---|---|---|
| `id` | `uuid` | no | PK |
| `role` | `varchar(30)` | no | |
| `permission` | `varchar(60)` | no | |
| `before` | `boolean` | yes | null when the row was created |
| `after` | `boolean` | yes | null when the row was removed |
| `actorUserId` | `uuid` | yes | null for System |
| `actorName` | `varchar(100)` | yes | |
| `actorEmail` | `varchar(255)` | yes | |
| `note` | `text` | yes | at most 500 characters |
| `createdAt` | `timestamptz(3)` | no | |

Index `(createdAt desc, id desc)`. Kept forever.

No schema change in welinc-auth. `AUDIT_ACTIONS` gains `MECHANIC_UNASSIGNED`. `hasInactiveMechanic` and `needsMechanic` are derived at read time, not stored.

### API surface

| Endpoint | Service | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|---|
| `/vrms/permissions/me` | backend-vrms | GET | none | `{ keys, version }` | `@Authenticated` | 401, 503 |
| `/vrms/permissions` | backend-vrms | GET | none | `{ roles: [{ role, label }], groups: [{ name, keys: [{ key, label, description, grants: { [role]: { allowed, locked } } }] }], version }` | `permissions.manage` | 403 |
| `/vrms/permissions` | backend-vrms | PATCH | `changes[]` (req, 1 to 100), `note?`, `version` (req) | same as GET | `permissions.manage` | 400, 403, 409 |
| `/vrms/permissions/changes` | backend-vrms | GET | `cursor?`, `limit?` | `{ data: [{ id, role, permission, before, after, actorName, actorEmail, note, createdAt }], nextCursor }` | `permissions.manage` | 400, 403 |
| `/vrms/mechanics/:authUserId/open-work` | backend-vrms | GET | path id | `{ total, byStatus }` | `users.manage` | 403 |
| `/vrms/mechanics/:authUserId/release-tickets` | backend-vrms | POST | `reason` (req) | `{ released, reopened }` | `users.manage` | 400, 403, 404, 409, 503 |
| every existing backend-vrms route | backend-vrms | | | unchanged; ticket list and detail add `hasInactiveMechanic`, `needsMechanic`, `can` | per *Route to key mapping* | 403 |
| `/auth/users/lookup` | welinc-auth | GET | `q` (req, 2+ chars) | `[{ id, name, email, systems }]` (max 10) | ADMIN | 400, 429 |
| `/auth/users` | welinc-auth | POST | existing body, `attachExisting?` | user | ADMIN | 409 `ACCOUNT_EXISTS` |
| `/auth/users` | welinc-auth | GET | unchanged | each user's caller system `roles` plus `otherSystems` | ADMIN | |
| `/auth/users/:id/*` | welinc-auth | all | unchanged | scoped to the caller's system | ADMIN | 403 shared rules, 404 out of scope |

### Value sourcing

| Action | Value | Source |
|---|---|---|
| any check | the caller's roles | the welinc-auth account check (`req.user.roles`, VRMS system only), already cached 30 s |
| any check | each role's grants | the replica's matrix cache, loaded from `role_permissions`, reloaded when `permission_matrix.version` moves; locked cells from `catalog.ts` |
| `/permissions/me` | `keys` | union of granted keys over the caller's matrix roles |
| `/permissions/me`, GET, PATCH | `version` | `permission_matrix.version` |
| ticket list and detail | `can.work`, `can.administer`, `can.editCosts`, `can.unlock` | `ability.can(action, subject('RepairTicket', ticket))` for that caller |
| GET matrix | `label`, `group`, `description`, `locked`, role `label` | `catalog.ts` (role labels `Admin`, `Chief Mechanic`, `Mechanic`) |
| PATCH | change rows' actor | the JWT (`sub`, `name`, `email`), never the body |
| PATCH | `before` | the row's `allowed` read inside the transaction |
| startup backfill | default `allowed` | `catalog.ts` defaults |
| open work, release | the person's tickets | `TicketAssignment` joined to `Mechanic.authUserId` |
| release | new status | `ASSIGNED` with no assignment left → `OPEN`; others unchanged |
| release audit | `note` | the `reason` input mapped to `Account deactivated` or `VRMS role removed` |
| ticket flags | `hasInactiveMechanic` | any assignment whose `Mechanic.isActive` is false, ticket in `OPEN_STATUSES` |
| ticket flags | `needsMechanic` | status `IN_PROGRESS` or `ON_HOLD` and no assignment to an active `Mechanic` |
| welinc-auth scoping | the caller's system | the request's resolved system (`req.user.system`, spec 0009 AC-24) |
| welinc-auth shared check | the account's other systems, and whether it is `ADMIN` in one | its `UserRoleAssignment` rows whose system differs |
| release | whether the person still has VRMS access | the roster refresh of that one `Mechanic` row from welinc-auth, done inside the call |
| confirm copy | `<systems>` | `otherSystems` from the list response, or `systems` from 409 or lookup |

### Key invariants

- No request is allowed by default: no decorator, no row, unknown key or unknown role all deny (AC-6, AC-7).
- A locked cell always has its locked value (AC-4).
- The startup backfill only inserts, never updates or deletes (AC-3).
- Every applied matrix change has exactly one `PermissionChange` row and bumps `permission_matrix.version`, in the same transaction (AC-18, AC-19).
- Rules with conditions are evaluated only on the server; the browser sees keys and per ticket flags the server computed (AC-12a, AC-16, AC-22).
- An ability is never shared between users (AC-9).
- A VRMS admin never changes another system's roles, never deletes a shared account, and never sets the password or email of another system's admin (AC-27, AC-28).

### Security model

- **Authentication** stays as spec 0009: JWT plus the live welinc-auth account check. Permissions never come from the token or the body.
- **Authorization**: the catalog keys per *Permission catalog*, enforced by the global guard and by CASL in services. Ownership ("assigned to me") is a rule condition, not a role check.
- **Admin rights can't be lost**: `users.manage` and `permissions.manage` are locked to Admin. welinc-auth keeps its own `ADMIN` check, which matches the lock.
- **Cross system**: welinc-auth admin endpoints are scoped by system; shared accounts can't be deleted from VRMS; another system's admin can't have their password or email changed from VRMS; lookup reveals only name, email and systems, to admins only, rate limited; release refuses while the person still has VRMS access.
- **Audit**: every permission change is logged with actor; every release writes ticket audit events; every account change still writes `UserChange`; denials go to the log, not the database.

### Configuration required

None. The 60 second web refetch, the 5 second toast window and the lookup limit are constants (`PERMISSIONS_REFETCH_MS`, `DENIED_TOAST_MS`, `LOOKUP_PER_MINUTE`).

### Critical test scenarios

- Happy path: an Admin turns `knowledge.edit` off for Chief Mechanic; the Chief's next PATCH to an entry, on either replica, gets 403 and the Edit button disappears after the refetch, verifies **AC-18**, **AC-20**, **AC-23**, **AC-24**
- Backfill keeps edits: set a cell to the opposite of its default, restart, the cell keeps the edit; add a key in code, start two instances at once, its three rows exist once with defaults and exactly three System change rows; remove the key from code and restart, its rows stay and deny, verifies **AC-3**
- Locked cell: PATCH `users.manage` off for Admin gets 400 and nothing changes; set it false by hand in the database, the Admin still has it, verifies **AC-4**
- Stale save: two concurrent PATCHes with the same `version`, exactly one succeeds and the other gets 409, verifies **AC-18**
- No shared ability: two mechanics hit the list in turn on one replica, each sees only their own tickets, verifies **AC-9**
- Ticket flags: a Chief's response for another mechanic's ticket has `can.work` false; for their own, true, verifies **AC-12a**
- Route coverage: a controller method without a decorator fails the route listing test and answers 403 at runtime, verifies **AC-7**
- Ownership: a Mechanic reading another mechanic's ticket gets 403; a Chief reads it but a status PATCH gets 403, verifies **AC-10**, **AC-12**
- Costs: a Chief's ticket response has null costs; an Admin's has values, verifies **AC-11**
- Generated table: every route and role under the default matrix, verifies **AC-15**
- DB down: with the cache warm, requests keep their answers; a cold replica gets 503 and fails readiness; the web app shows the error state with Retry, verifies **AC-21**, **AC-23**
- Multi role: an account with Mechanic and Admin in VRMS gets the union, verifies **AC-5**
- Auth scoping: a VRMS admin asks for a BMS only user's changes and gets 404; sends a BMS role and gets 403; deletes a shared account and gets 403; sets the password of an account that is ADMIN in BMS and gets 403, verifies **AC-26**, **AC-27**, **AC-28**
- Release guard: release for a mechanic who is still active gets 409; after deactivation it releases, and a second call releases 0, verifies **AC-33**
- Attach: create with a BMS user's email gives `ACCOUNT_EXISTS`; again with `attachExisting` adds only the VRMS role and their password still works, verifies **AC-30**
- Locked is not inactive: a mechanic locked by wrong passwords stays assignable and their tickets show no badge, verifies **AC-31**, **AC-34**
- Release: a mechanic with one `ASSIGNED` and one `IN_PROGRESS` ticket is deactivated with "Move back": the first is `OPEN`, the second keeps its status and shows "Needs a mechanic", each has a `MECHANIC_UNASSIGNED` event, verifies **AC-33**, **AC-34**, **AC-35**

## Build plan

Tracer Bullet: the first slice runs one strand (ticket reads) through every layer, from table to button, before the rest is converted.

1. Compatibility check: install `@casl/ability` and `@casl/prisma` in backend-vrms and prove `accessibleBy` with the nested `assignments.some.mechanic.authUserId` condition against the Prisma 7 client (the README documents the Prisma 7 `prisma-client` generator path; confirm the version's peer range). If it fails, use plain `@casl/ability` and keep a hand written `where` per rule; note the outcome in this spec. satisfies **AC-9**, **AC-10**
2. Thin thread, ticket reads end to end: migration for `role_permissions`, `permission_matrix` and `permission_changes`; `catalog.ts`; startup backfill under the advisory lock; matrix cache with the per request version read and last known fallback; readiness probe waits for the first load; ability factory (key set cached, ability per request, locks from the catalog); global `JwtAuthGuard` and `PermissionsGuard` with `@RequirePermission`, `@Authenticated`, `@Public`; ticket list, detail, history and summary on `accessibleBy`; `GET /vrms/permissions/me`; in web-vrms `@casl/ability` and `@casl/react`, the ability context from keys, fetch, refetch, error state and No VRMS access screen, and the repairs routes and nav on it. satisfies **AC-1**, **AC-2**, **AC-3**, **AC-4**, **AC-5**, **AC-6**, **AC-9**, **AC-10**, **AC-14**, **AC-16**, **AC-20**, **AC-21**, **AC-23**
3. Rest of backend-vrms on the matrix: every route per *Route to key mapping*; costs through `permittedFieldsOf` and `spend` by key; `ticket.work` and `ticket.administer` in status, steps and knowledge link; the `can` flags on ticket responses; knowledge visibility and editing; remove `RolesGuard`, `@Roles`, the knowledge role lists and `isMechanic`; denial log line; route listing test; generated e2e table. satisfies **AC-7**, **AC-8**, **AC-9**, **AC-11**, **AC-12**, **AC-12a**, **AC-13**, **AC-14**, **AC-15**
4. Matrix API: `GET` and `PATCH /vrms/permissions` with locks, row locked version check and change rows; `GET /vrms/permissions/changes`; `npm run permissions:prune`; seed resets the matrix. satisfies **AC-3**, **AC-4**, **AC-17**, **AC-18**, **AC-19**
5. Rest of web-vrms: replace every role check (App routes, header, shell, sidebar, user menu, shell actions, dashboard, knowledge pages, history, repair detail, form, list, Users page) with `<Can>` on keys and the ticket `can` flags; 403 interceptor with the deduplicated toast, refetch and redirect; the read only "Roles and permissions" section on the Users page; the Analytics route and nav item on `analytics.view` (the catalog entry is added in slice 2's `catalog.ts`; the next startup backfill inserts its three rows and three System change rows on its own). satisfies **AC-12a**, **AC-22**, **AC-22a**, **AC-24**, **AC-25**
6. welinc-auth: system scoping on every admin user endpoint, `otherSystems` on the list; role edits limited to the caller's system and empty list removal; shared account rules, including the other system admin block on password and email; `GET /auth/users/lookup` with its rate limit; `ACCOUNT_EXISTS` and `attachExisting` on create. satisfies **AC-26**, **AC-27**, **AC-28**, **AC-29**, **AC-30**
7. Open work: roster ignores lock; open work and release endpoints (with the access check and idempotence); `MECHANIC_UNASSIGNED`; ticket flags, badges and dashboard attention; Users page deactivate and remove role confirms with the choice (replacing the AC-16 block), Add user with the two paths and the attach confirm, shared account notes and hidden Delete. satisfies **AC-31**, **AC-32**, **AC-33**, **AC-34**, **AC-35**, **AC-36**
8. Close out: lint, build and tests in all three repos, typecheck in web-vrms. satisfies **AC-37**

## Consequences

**Positive**:
- One place answers "who may do what", and an Admin changes it without a deploy.
- The UI and the server can't drift: the browser reads the server's keys and the server's per ticket answers.
- An Admin's edit applies on the next request on every replica, so a revoked right stops working at once.
- Ownership, hidden fields and later rules (features 19, 21, 23, 30) are one CASL rule each instead of new `if` blocks.
- Forgetting a decorator is safe: the route is closed, and a test catches it.
- Spec 0009's leftovers are closed: welinc-auth admin endpoints are scoped by system.

**Negative / tradeoffs**:
- The team learns CASL: rule order (a later `cannot` overrides an earlier `can`), subjects, `accessibleBy` and `permittedFieldsOf`.
- Every checked request adds one primary key read of `permission_matrix`.
- A browser tab can show a stale button for up to 60 seconds (or until focus); the server still refuses, and the 403 refetches.
- Ticket responses grow by four booleans, computed per ticket.
- Admin rights can be narrowed except the two locked keys, so an Admin can switch off something the BRD expects (for example, giving mechanics `ticket.costs.view`). The change log is the guard, not a lock.
- Scoping welinc-auth by system changes behavior for VMMS and BMS admins too: they will only see their own system's users.
- `analytics.view` hides the Analytics screen but does not protect its data: the Python analytics service checks no JWT, so anyone who can reach `/analytics/*` through the gateway can read it. Feature 3 closes this by moving analytics behind the guard.
- A shared account can be deactivated from VRMS, which blocks the person in every system. The confirm says so, but the other group is not told.

**Neutral**:
- This replaces the deactivate block from spec 0006 AC-16 with a warning and a choice.
- Three new tables and four new npm packages (`@casl/ability`, `@casl/prisma` in the backend, `@casl/ability`, `@casl/react` in the web app).
- A Chief Mechanic sees every ticket from go live (pulled forward from feature 17).
- Admins edit the matrix in the Settings hub (feature 52, spec 0012, AC-24). Saving goes through `PATCH /vrms/permissions`, and the hub asks for a review and, when a right is taken away, a reason (the web app asks for it and `PATCH /vrms/permissions` answers 400 without one).

## Migration plan

**Strategy**: strangler inside each repo. The new guard and the old `@Roles` lists can't both run on one route, so each controller moves whole, in the order of the build plan; the default matrix equals today's rules, so each moved controller behaves the same.
**Phases**:
1. Tables and backfill deploy first; nothing reads them yet.
2. Ticket reads move (slice 2), then every other controller (slice 3); web follows in slice 5.
3. welinc-auth scoping deploys on its own (slice 6).
**Rollback**: revert the backend-vrms commit; the three tables are only read by the new code, so they can stay, and startup never deletes rows, so rolling back and forward keeps every Admin edit. welinc-auth scoping reverts on its own.
**Risks**: a key with a wrong default opens or closes a route. The generated e2e table (AC-15) against the default matrix catches it before merge.

## Follow-up

- [ ] Feature 3 (analytics and AI boundary): put every analytics route behind `@RequirePermission('analytics.view')` in backend-vrms, and make the gateway stop passing `/analytics/*` straight to the unauthenticated Python service.
- [x] Feature 52 (Settings hub): the editing screen for the matrix, on `PATCH /vrms/permissions`, plus the change history view (built in spec 0012, AC-24 and AC-26; merged in web-vrms #25 and backend-vrms #22).
- [ ] Feature 28 (in-app notifications): push a "permissions changed" event so open browser tabs refetch at once instead of within 60 seconds.
- [ ] Feature 27 (error monitoring): alert on a spike of 403 log lines from one user.
- [ ] Feature 17 (Chief Mechanic): this spec turns `ticket.view_all` on for the Chief; what's left is the verification queue and dashboard.
- [ ] Features 19, 21, 23, 30, 33, 57: each adds its keys and CASL rules (for example 23: a Chief can't verify a ticket they worked on).
- [ ] Feature 56 (integration): how each system finds and hands off a deactivated person's open work; whether `RefreshToken` stays or goes; whether the groups want a shared permission package or a cross system super admin; tell VMMS and BMS that welinc-auth admin endpoints are now scoped by system.
- [ ] Feature 55 (kickoff prep): add the welinc-auth scoping change to the list of changes to the shared repos.
- [x] Mechanic home garage (branch): enrolled as scope feature 59 in Operations.
- [ ] CASL Agent Skill skipped for now (only community skills found: `tuannguyen151/foxdemon-plugins` `casl-authorization`, `ramziddin/ccplugins` `authorization`). Revisit if an official one appears.
- [ ] Update `docs/context/roles-and-users.md`: Chief Mechanic sees all tickets, and the matrix lives in `catalog.ts` plus `role_permissions`.
