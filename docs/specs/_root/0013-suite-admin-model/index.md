# 0013. Suite admin model: suite admins, temporary access, portal admin and central permissions

**Date**: 2026-11-12
**Status**: In Progress
**Scope row**: [S10. Suite admin model](../../../scope/_root/shared-services.md#s10-suite-admin-model--in-progress--ga)
**Builds contract sections**: [0001](../0001-shared-services-contract/index.md) version 7 (breaking): the login answer, the admin code gate on admin routes, the new `/auth/admin/*` and `/auth/permissions/:system` routes, the removed VRMS matrix routes
**Related**: [0004](../0004-roles-per-system/index.md) (catalog, `isSystemAdmin`), [0005](../0005-user-directory/index.md) (directory feed), [0006](../0006-suite-seed-accounts/index.md) (seed manifest), [0007](../0007-app-initiated-login-launcher/index.md) (launcher top bar), [0009](../0009-email-verification/index.md) (sign in code), [0011](../0011-account-activity-audit/index.md) (events, scope), [0012](../0012-profile-extras/index.md) (reauth token, deletion), VRMS spec 0011 (permission matrix)

## Summary

welinc-auth gets a suite admin: at most three people (never fewer than one) who manage every account and grant each system's roles, but who hold no system role and so see no system's data. When they really need to look inside a system, they give themselves a role for 1 to 8 hours with a written reason, and that system's admins get an email. Every admin, suite or system, now confirms each portal sign in with an emailed code, and all account actions move to a new admin section in the portal, where each admin sees only their own system's people. The role permission matrix moves from VRMS into welinc-auth, where only suite admins edit it and each system reads a cached copy.

## Requirements

**User stories**:
- As a suite admin, I want to manage every account and every system's roles from one place, without being able to read any system's work data by default, so that nobody holds a hidden everyday superuser account.
- As a suite admin, I want to give myself a system role for a few hours with a reason when something is broken, so that I can help without a permanent grant and with everyone able to see that I did.
- As a system admin, I want my system's people in the portal, scoped to my system, so that VMMS and BMS stop keeping their own user pages.
- As a system admin, I want an email whenever someone gains or loses admin in my system, or a suite admin steps in, so that a quiet takeover is visible.
- As a suite admin, I want a landing page that shows who holds admin where and since when, what needs attention, and the latest admin changes, so that I can answer "who can do what" at a glance.
- As a suite admin, I want to edit each system's role permission matrix centrally, so that one small, code protected group controls what each role can do.
- As a Chief Mechanic, I want to see which tickets were released because someone left, so that nothing waits on a person who is gone.
- As whoever runs the server, I want a recovery script, so that the suite never ends up with no suite admin who can sign in.

**Acceptance criteria**:

*Suite admins*
- **AC-1**: `GET /auth/admin/suite-admins` (a suite admin) lists every suite admin with `id`, `name`, `email`, `grantedAt`, `grantedBy` (`{ id, name }` or null for the seed or the recovery script) and `reason`. `POST /auth/admin/suite-admins` with `{ userId, reason, reauthToken }` (reason 10 to 500 characters, trimmed) adds one. It answers 409 `SUITE_ADMIN_LIMIT` when 3 exist, 409 `ALREADY_SUITE_ADMIN`, 409 `HOLDS_SYSTEM_ROLES` when the person holds any `user_roles` row, 409 `NOT_ELIGIBLE` when the person is inactive, deleted, locked or has `emailVerified` false, 404 for an unknown id, and 403 `REAUTH_REQUIRED` per AC-14. The order is `pg_advisory_xact_lock(hashtext('suite_admins'))`, then the target `users` row `FOR UPDATE`, then the checks, so two grants at once can't make 4 and a role written at the same moment can't slip past `HOLDS_SYSTEM_ROLES`.
- **AC-2**: `POST /auth/admin/suite-admins/:userId/remove` with `{ reason, reauthToken }` removes one (a `POST`, since some clients drop `DELETE` bodies), under the same advisory lock. Removing yourself answers 409 `SELF_ROLE`; removing the last answers 409 `LAST_SUITE_ADMIN` (same advisory lock). It ends that person's live temporary grants with `SUITE_ADMIN_REMOVED` (AC-9 steps).
- **AC-3**: A suite admin never holds a permanent system role. Every write path that would add a non temporary `user_roles` row for a suite admin (`POST /auth/users` and `/auth/admin/users`, `attachExisting`, a roles `PATCH` on either route family, the seed) answers 409 `SUITE_ADMIN_NO_ROLES`. The database enforces it too: a deferred constraint trigger on `user_roles` raises on any committed row with `temporary_grant_id` null whose user is in `suite_admins`, and the service maps that error to the same 409, so a race or a future write path can't break the rule. A suite admin can't be deactivated or deleted while they are one: 409 `IS_SUITE_ADMIN` (remove the suite admin row first). A suite admin's own deletion request (`POST /auth/profile/deletion-request`) answers 409 `IS_SUITE_ADMIN` as well, before the reauth token is used.
- **AC-4**: Each grant and removal writes `SUITE_ADMIN_ACTIONED` or `SUITE_ADMIN_REMOVED` (category `ACCOUNT`, `system` null, the actor, the reason) in the same transaction, and sends the AC-12 alert.

*Admin sign in code*
- **AC-5**: `POST /auth/login` with the right password, for an active account whose email is verified and who is a suite admin or holds any `isSystemAdmin` role, answers 200 `{ status: "SIGN_IN_CODE_REQUIRED", challengeId, email, resendAfter }` (the spec 0009 body, a new status value) and sets no cookie. `POST /auth/login/verify-email` and its resend finish it exactly as for an unverified email, and the session it creates gets `sessions.sign_in_code_at` = now. An unverified account still answers `EMAIL_VERIFICATION_REQUIRED` (one code only, even for an unverified admin). Any login finished through the code step sets `sign_in_code_at`, admin or not; the ticket carries no admin flag. A suite admin holds no system, so the launcher answer for a suite admin is a 200 with an empty `systems` list, never 403 `NO_SYSTEM_ACCESS`, on `/auth/login`, `/auth/login/verify-email` and `/auth/sso`; `/auth/authorize` for a system they hold no live grant in keeps today's error. Code lifetime, 5 wrong tries and send limits are spec 0009's (they replace VRMS feature 34's 5 minutes and 15 minute lock). `/auth/mobile/login` is unchanged: the mobile clients take no admin role.
- **AC-6**: Admin powers need a session that passed the code. Every `/auth/admin/*` route except `GET /auth/admin/me`, `POST /auth/admin/code` and `POST /auth/admin/code/verify`, and every `@SystemAdmin()` bearer route, answers 403 `ADMIN_CODE_REQUIRED` when the caller's session (the cookie session, or the token's `sid`) has `sign_in_code_at` null. The gate reads the session row by `sid` on every request (no token is issued again), and refresh and code exchange keep the `sid`, so a step up works at once for tokens already issued for that session. This covers someone made admin mid session and sessions from before this ships.
- **AC-7**: `POST /auth/admin/code` (cookie, an admin or suite admin) sends a `SIGN_IN` code to the caller and answers `{ challengeId, email, resendAfter }`; `POST /auth/admin/code/verify` with `{ challengeId, code }` sets `sign_in_code_at` on the cookie session and answers 204. Both follow spec 0009's errors (`INVALID_CODE` with `attemptsLeft`, `CODE_EXPIRED`, 429 `CODE_SEND_LIMIT`). When the session already passed, `POST /auth/admin/code` answers 200 `{ passed: true }` and sends nothing. When `ADMIN_SIGN_IN_CODE` is off, both answer 409 `CODE_NOT_REQUIRED`. Passing the code at login or here writes `ADMIN_CODE_PASSED` (category `SIGN_IN`).
- **AC-8**: `ADMIN_SIGN_IN_CODE` (default `true`, read through `ConfigService` at request time). When `false`, AC-5 asks no code, AC-6 checks nothing, `sign_in_code_at` stays null, no `ADMIN_CODE_PASSED` is written and `GET /auth/admin/me` shows `codeRequired: false`. Production refuses `false` at boot (spec 0010 rules).

*Temporary access*
- **AC-9**: `POST /auth/admin/temporary-grants` with `{ system, role, hours?, reason, reauthToken }` (a suite admin, for themselves only; `hours` a whole number 1 to 8, default 4; reason 10 to 500 characters) creates a `temporary_grants` row and a `user_roles` row pointing to it in one transaction, writes `TEMP_ACCESS_STARTED` (`system`, `role` in `newValue`, the reason, `expiresAt`), and answers 201 with the grant. Any role in the system's catalog is allowed. It answers 400 `UNKNOWN_ROLE`, 409 `GRANT_ACTIVE` (one live grant per person and system, the partial unique index), and 403 `REAUTH_REQUIRED`. Inside the transaction it reads the caller's `suite_admins` row `FOR SHARE` (a suite admin removed a moment earlier gets 403 `NOT_SUITE_ADMIN`). Tokens are built from the current roles, so the holder's next code exchange or refresh for that system carries the role (opening the system from the launcher does this).
- **AC-10**: A grant ends when it expires (a sweep every minute ends every live grant with `expiresAt` at or before now: `EXPIRED`) or by `DELETE /auth/admin/temporary-grants/:id` (the holder, any suite admin, or an admin of that system: `ENDED_EARLY`, with `endedById`). Ending locks the grant row `FOR UPDATE`; if `ended_at` is already set (the sweep and a `DELETE` at once, or a repeat) it answers 204 and writes nothing. Otherwise it deletes the `user_roles` row, sets `endedAt` and `endReason`, writes `TEMP_ACCESS_ENDED` (`newValue` holds the end reason; actor null for the sweep), and ends every live session of the holder whose `audiences` holds the system with the new reason `TEMP_ACCESS_ENDED`, all in one transaction. The directory feed sends `roles_changed` through its trigger. Expiry is also checked lazily: building a token (code exchange or refresh) leaves out a role whose grant has `expires_at` at or before now, so a stopped sweep never keeps a role alive.
- **AC-11**: While live, the holder shows in that system's user lists (both route families) with `temporaryUntil` set. A system admin can't edit or remove that role through a roles `PATCH` (409 `TEMPORARY_ROLE`); they end the grant instead. The directory snapshot marks each role `temporary: true|false` (a migration changes `directory_snapshot()`), and the VRMS roster skips temporary roles, so a temporary `MECHANIC` grant never becomes a pickable mechanic. `GET /auth/admin/temporary-grants?state=live|all` (a suite admin: every system; a system admin: their system) lists grants newest first, keyset paged.

*Recovery*
- **AC-12**: `npm run admin:recover -- --email <address> --reason "<text>"` (run in the auth container shell, any environment) unlocks the account (clears `lockedAt` and `failedLoginAttempts`) and makes it a suite admin with `grantedById` null, in one transaction that ends the account's live sessions (reason `ADMIN_ENDED`) and writes `ADMIN_RECOVERY` (the reason, plus the host name and OS user in `newValue`) and `SUITE_ADMIN_ACTIONED`. It refuses (exit 1, nothing written) for an unknown, inactive, deleted or unverified account, one that holds a system role, or when 3 suite admins exist and the person isn't one. It prints no password or code; the person uses Forgot password if needed. It sends the AC-13 alert.

*Alerts*
- **AC-13**: These changes send an alert email after commit to every suite admin and to the admins of the system concerned (active, not deleted; the actor too, so they have a record). A failed email is logged and never blocks:

  | Change | Systems whose admins get it |
  |---|---|
  | an `isSystemAdmin` role added to or removed from someone (create, attach, roles `PATCH`, delete, restore) | that system |
  | suite admin added or removed, recovery script run | every system |
  | temporary access started, or ended early | that system |
  | permission matrix edited (AC-27) | that system |
  | email edit, reset or setup code, unlock or sessions ended on an admin account (AC-14b) | each system where the target is admin (every system for a suite admin target) |
  | any role given, or account created, by a suite admin (AC-14c) | that system |

  Each email names who, what, when (Asia/Manila), the actor and the reason, and links to the portal admin section. One save sends one email per recipient, listing every admin level change in it; recipients are deduplicated; a removed suite admin also gets the email about their own removal. Expiry (`EXPIRED`), the seed and `catalog:sync` send none. Other role changes send no alert; they show in the report.

*Portal admin routes*
- **AC-14**: `/auth/admin/*` routes are authenticated by the `welinc_sso` cookie (the live web session it points to), never a bearer token; every non `GET` runs `PortalCsrfGuard`. No cookie or an ended session answers 401 `NOT_SIGNED_IN`. `POST /auth/admin/verify-password` with `{ password, purpose }` (`ADMIN_ACTION` or `TEMPORARY_ACCESS`) gives a spec 0012 reauth token bound to the cookie session (same `WRONG_PASSWORD` counting and lockout). A reauth token works once (spec 0012 AC-3) and is required by AC-1, AC-2 (`ADMIN_ACTION`), AC-9 (`TEMPORARY_ACCESS`, suite admins only, else 403 `NOT_SUITE_ADMIN`) and AC-14a (`ADMIN_ACTION`). It isn't bound to the target person. A caller who isn't an admin gets 403 `NOT_AN_ADMIN`.
- **AC-14a**: Adding an `isSystemAdmin` role to anyone (create, `attachExisting` or a roles edit, by a system admin or a suite admin, on either route family) needs a reauth token with purpose `ADMIN_ACTION` in the body (`reauthToken`), else 403 `REAUTH_REQUIRED`. The bearer routes take it from `POST /auth/profile/verify-password`, which accepts `ADMIN_ACTION` for an admin's token.
- **AC-14b**: Actions on an admin account need the actor's own password recheck. When the target holds any `isSystemAdmin` role or is a suite admin, these need a reauth token with purpose `ADMIN_ACTION` from whoever acts (system admin or suite admin), on either route family, else 403 `REAUTH_REQUIRED`: an email edit, sending a reset or setup code, unlock, and ending their sessions. Each sends the AC-13 alert. A suite admin's email is changed only by that person through the profile email flow (spec 0009 code); anyone else's edit answers 403 `SUITE_ADMIN_SELF_ONLY`.
- **AC-14c**: Every role a suite admin gives (create, `attachExisting`, a roles edit, any role, admin or not) and every account a suite admin creates needs the suite admin's reauth token with purpose `ADMIN_ACTION` (403 `REAUTH_REQUIRED`) and sends the AC-13 alert to that system's admins. There is no separate list; the events stay in Activity like any other.
- **AC-15**: `GET /auth/admin/me` answers `{ user, suiteAdmin: boolean, adminOf: SystemType[], codeRequired, codePassed }`. `adminOf` counts permanent roles only; a temporary admin grant works inside that system's own app, not in the portal admin section (a suite admin already has suite scope there). Anyone else gets 403 `NOT_AN_ADMIN` on every other `/auth/admin/*` route.
- **AC-16**: The account routes take `system` (query or body). A system admin must pass a system where they hold `isSystemAdmin` (else 403 `NOT_ADMIN_OF_SYSTEM`) and gets exactly today's `/auth/users*` behavior for that system: the same scope rules (`user-scope.ts`), self rules, last admin rules, shared account rules, events and errors. The routes are: list, lookup, create (with `attachExisting`), edit (name, email, roles, active), status, unlock, send reset or setup code, sessions list and end, activity, delete, restore, deletion requests (pending and grace), approve, reject. One service layer serves both route families; the controller only resolves the scope (`{ system, actorId, suite }`).
- **AC-17**: A suite admin may pass any system, or none on list, activity and deletion requests (then every person, including people with no role anywhere). On top of AC-16 a suite admin can delete and restore a shared account (no `assertNotShared`), grant any system's roles to someone else (including that system's admin role), and approve or reject any pending deletion request (`decidedSystem` null). Every other suite admin write needs `system` (400 `VALIDATION_FAILED`); delete, restore and deletion decisions don't. The last active admin rule still holds per system, so deleting a shared account that holds a system's last admin role answers 409 `LAST_ADMIN` until someone else is made admin there. In suite scope, list items carry every system's `roles` and no `otherSystems`; a person with no role anywhere is found (200, not 404).
- **AC-18**: The bearer `/auth/users*`, `/auth/activity`, deletion request and sessions routes keep working for system admins unchanged, plus AC-3, AC-6 and AC-11. Contract 0001 marks them deprecated; a later spec removes them after S11.

*Report and suite views*
- **AC-19**: `GET /auth/admin/report` (a suite admin) answers: `suiteAdmins` (as AC-1); `systems`, each with `admins` (`id`, `name`, `email`, `since`, `grantedBy`) and live `temporaryGrants` (`holder`, `role`, `reason`, `startedAt`, `expiresAt`); `attention` counts and the first 10 of each, oldest first, active and not deleted accounts only for the first three: locked (`lockedAt` set), setup pending (`passwordSet` false), email not verified (`emailVerified` false), deletion requests pending (with `orphan`), accounts in grace (with `eraseAfter`); `systemsWithoutAdmin` (a system whose admin role no active person holds); and `recentAdminChanges`, the newest 20 of: `SUITE_ADMIN_ACTIONED`, `SUITE_ADMIN_REMOVED`, `TEMP_ACCESS_STARTED`, `TEMP_ACCESS_ENDED`, `ADMIN_RECOVERY`, and `CREATED`, `ROLE_CHANGED`, `DELETED` or `RESTORED` rows whose old or new value holds an `isSystemAdmin` role (matched against the catalog at read time). A `grantedBy` whose account was erased shows "Deleted user".
- **AC-20**: `GET /auth/admin/activity` without `system` (a suite admin) lists every person's events, former members included, with spec 0011's filters, paging and field visibility for admins.
- **AC-21**: `GET /auth/admin/deletion-requests?view=pending|grace` without `system` (a suite admin) lists every request or account in grace, each with `orphan: true` when no active admin of any system the person holds is someone other than the person, or the person holds no role now. Orphans sort first.

*Portal UI*
- **AC-22**: The launcher top bar shows an **Admin** entry for anyone `GET /auth/admin/me` says is an admin, also on the no systems screen (a suite admin holds none). The portal login and the step up screen handle `SIGN_IN_CODE_REQUIRED` with spec 0009's code screen, worded "Confirm it's you". Any `ADMIN_CODE_REQUIRED` answer opens the step up dialog, then retries the request once.
- **AC-23**: `/admin` has these views. **Overview** (suite admins; the landing page) shows the AC-19 report in this order: admins per system with live temporary grants, the attention list, recent admin changes. **People** (everyone admin; system switcher when the admin holds two or more systems, and an "All people" choice for a suite admin) lists people with status badges (Locked, Setup pending, Email not verified, Active, Inactive, Pending deletion, Temporary until `<time>`) and opens a person page with every AC-16 action. **Deletion requests**, **Activity** (suite admins see a Suite wide tab), **Temporary access**, **Suite admins** and **Permissions** (AC-27). Deep links work: `/admin/people/:id?system=VRMS` and `/admin/people/new?system=VRMS`.
- **AC-24**: A suite admin's **Temporary access** button opens a dialog (system, role, hours 1 to 8 with 4 picked, reason with a counter, password). While a grant is live, a top bar banner shows the system, role and end time with **End now** and **Open `<system>`**. End now warns first that it signs you out everywhere (AC-10 ends the web session), then returns to the login screen. Every write that needs a reauth token asks for the password in the same dialog.

*Permissions*
- **AC-25**: `prisma/catalog/vrms.ts` gains `permissions`: an ordered list of `{ key, label, group, description, defaults: Record<role, boolean>, lockedRoles? }`, holding today's VRMS `PERMISSION_CATALOG` content minus `users.manage` and `permissions.manage`, plus `team.manage` (Admin on, the others off). `catalog:sync` writes `system_permissions`, inserts missing `role_permissions` cells with their defaults, never overwrites an existing unlocked cell, sets every locked cell to its default (one `permission_changes` row each when it differed), deletes cells of dropped keys (one `permission_changes` row each, `after` null), and bumps that system's `permission_matrices.version` (`version = version + 1`) when anything changed. Its rows have actor null and `actor_name` "Catalog sync". It refuses a default or lock naming a role the system doesn't have. VMMS and BMS files get no permissions yet; their matrix is empty.
- **AC-26**: `GET /auth/permissions/:system` (a service token with scope `permissions.read`, only for its own system: else 403 `WRONG_SYSTEM`) answers `{ system, version, permissions: [{ key, lockedRoles }], grants: { <role>: [key, …] } }` with `ETag: "v<version>"`; `If-None-Match` with the current tag answers 304. 120 calls a minute per client, like the directory.
- **AC-27**: `GET /auth/admin/permissions/:system` (a suite admin, or an admin of that system, read only) answers the matrix with labels, groups, locked cells and `version`. `PATCH` (suite admins only, 403 `NOT_SUITE_ADMIN` otherwise) with `{ version, changes: [{ role, key, allowed }], note? }` applies every change in one transaction: 409 `MATRIX_STALE` when `version` isn't current, 409 `LOCKED_CELL` for a locked cell, 400 `UNKNOWN_PERMISSION` or `UNKNOWN_ROLE`, 400 `NOTE_REQUIRED` when any change takes a right away and the note isn't 5 to 500 characters. An empty list, or the same (`role`, `key`) twice, answers 400 `VALIDATION_FAILED`. It writes one `permission_changes` row per changed cell (unchanged cells write none), bumps the version with `version = version + 1` and sends the AC-13 alert. A save where every cell already had that value answers 200 with no bump, no row and no alert. `GET /auth/admin/permissions/:system/changes` pages the history newest first, imported rows included.
- **AC-28**: One time move. `npm run permissions:export -- <file>` in backend-vrms writes its `role_permissions` cells and every `permission_changes` row to a JSON file. `npm run permissions:import -- VRMS <file>` in welinc-auth, in one transaction, sets each cell whose key and role exist, except locked cells (others skipped and listed), copies each role's `users.manage` value onto `team.manage` (so a role that had it keeps it), inserts the history with `imported` true and the original `createdAt`, actor name and email (`actorId` kept only when that user exists), and bumps the version. It refuses when the system already has a non imported change other than `Catalog sync` rows. Rollout order, locally and on staging: `catalog:sync` (AC-25), then the import, then deploy the VRMS sync (AC-29), then the VRMS removals and drop migration (AC-30).

*VRMS*
- **AC-29**: backend-vrms runs a matrix sync every 60 s (one copy at a time, like the directory poll): `GET /auth/permissions/VRMS` with `If-None-Match`; on 200 it replaces `role_permissions` and bumps `permission_matrix.version` in one transaction, so every replica reloads on its next request as today. On failure it keeps the last copy, sets `permission_sync_state.failing_since` and warns once. It refuses (keeps its copy, warns) a 200 whose `grants` is empty for every role, so an empty matrix in welinc-auth can't lock everyone out; any other change of ETag is applied, newer or not (a restore from backup counts). A key welinc-auth sends that VRMS code doesn't know is ignored; a key VRMS checks that welinc-auth lacks counts as off; each drift warns once. With no copy yet, checked requests answer 503 as today.
- **AC-30**: backend-vrms removes `PATCH /vrms/permissions`, `GET /vrms/permissions/changes`, the startup backfill, `permissions:prune` and the labels and defaults in `catalog.ts` (the keys, modules and CASL rules stay). Its `permission_changes` table is dropped by a migration that ships after the import ran. Routes behind `users.manage` move to `team.manage`. web-vrms removes the Settings permissions screen and shows a one line "Permissions are edited in the portal" link in its place for admins.
- **AC-31**: The VRMS Users page becomes a team and work view: name, role, status, Work column, open tickets, Unassign and Reassign stay; Edit, reset or setup code, unlock, sessions, activity, deactivate, delete and the Deletion requests chip are replaced by one **Manage account** link (`<VITE_PORTAL_URL>/admin/people/<id>?system=VRMS`, new tab) per row, and **Add user** opens `/admin/people/new?system=VRMS`. The page is behind `team.manage`. A VRMS call answered 403 `ADMIN_CODE_REQUIRED` shows "Confirm your sign in in the portal" with a link to `<VITE_PORTAL_URL>/admin`.
- **AC-32**: The Chief Mechanic dashboard gets a **Released after account changes** notice listing tickets the feed released in the last 7 days (from `MECHANIC_UNASSIGNED` audit rows with the `SYSTEM` actor): ticket, person, reason (deleted, deactivated, role removed), when. It hides when the list is empty.

*Seed and contract*
- **AC-33**: `seeds/people.json` adds `suite.admin@welinc.com` (id 9001, verified, no roles, `suiteAdmin: true`); `checkManifest` refuses roles on a suite admin and more than 3; the seed writes its `suite_admins` row (`grantedById` and `reason` null). The VRMS copy is updated and `seed:check` passes.
- **AC-34**: Contract 0001 becomes version 7 (breaking): the `SIGN_IN_CODE_REQUIRED` login answer, `ADMIN_CODE_REQUIRED` on admin routes, `SUITE_ADMIN_NO_ROLES`, `TEMP_ACCESS_ENDED` session ends, the `/auth/admin/*` and `/auth/permissions/:system` routes, the bearer admin routes marked deprecated, and the VRMS matrix routes removed. `docs/integration/suite-admin.md` tells VMMS and BMS to delete their user pages, link their sidebar item to `<portal>/admin/people?system=<SYS>`, handle the two new answers, and that joining the central matrix is optional.

## Decision

**Chosen option**: Option 3: a dedicated suite admin with no system roles, temporary self grants with a reason, an emailed code for every admin, one portal admin section scoped by who is looking, and the permission matrix in welinc-auth.

Suite admins live in their own table, are capped at three, and only another suite admin (or the recovery script) adds one. Account actions move to cookie authenticated `/auth/admin/*` routes the portal calls, sharing one service layer with the bearer routes. Each system's backend reads its matrix from welinc-auth with an ETag and keeps a cached copy.

**Implementation skills**: `prisma-client-api` and `prisma-cli` (`prisma/skills`, `.claude/skills/`), for the migrations, partial indexes and the import transaction · `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/`), for the admin module, cookie guard and scheduled sweep · `shadcn`, `react-hook-form`, `vercel-react-best-practices` and `tailwind-4-docs` (`.claude/skills/`), for the portal admin section and the VRMS page changes.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch** (welinc-auth):

`suite_admins` (new)

| Field | Type | Notes |
|---|---|---|
| `user_id` | uuid PK, FK `users`, Restrict | |
| `granted_by_id` | uuid null, FK `users`, SetNull | null: seed or recovery script |
| `granted_at` | timestamptz | default now |
| `reason` | varchar(500) null | null only for the seed |

`temporary_grants` (new)

| Field | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `user_id` | uuid, FK `users`, Restrict | the suite admin holding it |
| `system`, `role` | `SystemType`, varchar(40) | FK (`system`, `role`) to `system_roles`, Restrict |
| `reason` | varchar(500) | |
| `started_at`, `expires_at` | timestamptz | `expires_at` 1 to 8 hours after start (CHECK) |
| `ended_at` | timestamptz null | |
| `end_reason` | enum `TemporaryGrantEnd` null | `EXPIRED`, `ENDED_EARLY`, `SUITE_ADMIN_REMOVED` |
| `ended_by_id` | uuid null, FK `users`, SetNull | |

Partial unique index on (`user_id`, `system`) where `ended_at` is null. Index on `expires_at` where `ended_at` is null (the sweep).

`system_permissions` (new, written only by `catalog:sync`): PK (`system`, `key` varchar(60)), `label` varchar(100), `group` varchar(40), `description` varchar(300), `sort_order` int, `locked_roles` text[]. FK `system` to `systems`.

`role_permissions` (new): PK (`system`, `role`, `key`), `allowed` boolean, `updated_at`, `updated_by_id` uuid null (FK `users`, SetNull). FK (`system`, `role`) to `system_roles` and (`system`, `key`) to `system_permissions`, both Cascade, so `catalog:sync` dropping a key or role removes its cells (it logs them first).

`permission_matrices` (new): PK `system` (FK `systems`), `version` int default 1, `updated_at`.

`permission_changes` (new, append only by trigger like `account_events`): `id` uuid PK, `system`, `role`, `key` (no FK, history outlives the catalog), `before` boolean null (null when the cell was created), `after` boolean null (null when removed), `actor_id` uuid null (FK `users`, SetNull), `actor_name` varchar(100) (`Catalog sync` when the sync wrote it), `actor_email` varchar(255) null, `note` varchar(500) null, `imported` boolean default false, `created_at`. Index on (`system`, `created_at` desc, `id` desc). Erasure (spec 0012) blanks `actor_name` and `actor_email` for the erased person (the trigger allows that update under `welinc.erasure`, as for events).

Changed:
- `user_roles.temporary_grant_id` uuid null unique, FK `temporary_grants`, Restrict. A deferred constraint trigger (migration SQL only) raises `suite_admin_no_roles` when a row with `temporary_grant_id` null belongs to a user in `suite_admins` (checked on `user_roles` insert and update and on `suite_admins` insert).
- `directory_snapshot()` gives each role `temporary` (true when `temporary_grant_id` is set); `DirectoryUser` roles gain `temporary: boolean`.
- `sessions.sign_in_code_at` timestamptz null.
- `SessionEndReason` adds `TEMP_ACCESS_ENDED`. `ReauthPurpose` adds `ADMIN_ACTION`, `TEMPORARY_ACCESS`.
- `AccountEventType` adds `SUITE_ADMIN_ACTIONED`, `SUITE_ADMIN_REMOVED`, `TEMP_ACCESS_STARTED`, `TEMP_ACCESS_ENDED`, `ADMIN_RECOVERY` (category `ACCOUNT`, kept forever) and `ADMIN_CODE_PASSED` (category `SIGN_IN`). Each gets a catalog `label` and `labelAdmin`; the `CHECK` is rebuilt from the type map.
- `people.json` person shape adds optional `suiteAdmin: boolean`.

welinc-backend-vrms: `role_permissions` and `permission_matrix` stay, written only by the sync job. New `permission_sync_state` (one row, id `auth`): `etag` varchar(40) null, `synced_at` timestamptz null, `failing_since` timestamptz null, `lease_until`, `lease_owner` (as `directory_sync_state`). `permission_changes` is dropped (AC-30).

**State transitions**:

`temporary_grants`: live (`ended_at` null) → ended by `EXPIRED` (minute sweep), `ENDED_EARLY` (holder, a suite admin, or that system's admin) or `SUITE_ADMIN_REMOVED` (AC-2). Ended never comes back; a new grant is a new row.

`sessions.sign_in_code_at`: null → set (login code, or step up). Never cleared; an ended session stays ended.

**API surface** (welinc-auth; "cookie" is the `welinc_sso` session plus `PortalCsrfGuard` on writes, and every cookie route but `me` and the code routes needs `sign_in_code_at`):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/login` | POST | email, password | launcher list, or `SIGN_IN_CODE_REQUIRED` body | public, CSRF | as spec 0009 |
| `/auth/admin/me` | GET | | user, suiteAdmin, adminOf, codeRequired, codePassed | cookie | 401 `NOT_SIGNED_IN` |
| `/auth/admin/code` | POST | | challengeId, email, resendAfter; or `{ passed: true }` | cookie, admin | 429 `CODE_SEND_LIMIT`, 409 `CODE_NOT_REQUIRED` |
| `/auth/admin/code/verify` | POST | challengeId, code | 204 | cookie, admin | 400 `INVALID_CODE`, `CODE_EXPIRED`, 409 `CODE_NOT_REQUIRED` |
| `/auth/admin/verify-password` | POST | password, purpose | reauthToken, expiresAt | cookie, admin | 400 `WRONG_PASSWORD`, 403 `ACCOUNT_LOCKED` |
| `/auth/admin/users` | GET | system?, q?, status?, cursor, limit | items with roles, otherSystems, temporaryUntil, pendingDeletion, next | cookie, admin of system / suite | 403 `NOT_ADMIN_OF_SYSTEM` |
| `/auth/admin/users/lookup` | GET | system, q | id, name, email, systems | cookie, admin | 429 |
| `/auth/admin/users` | POST | system, name, email, roles, attachExisting?, reauthToken? (admin role) | user | cookie, admin | 409 `ACCOUNT_EXISTS`, `SUITE_ADMIN_NO_ROLES`, 403 `REAUTH_REQUIRED` |
| `/auth/admin/users/:id` | PATCH | system, name?, email?, roles?, isActive?, reauthToken? (admin role) | user | cookie, admin | 409 `SELF_ROLE`, `LAST_ADMIN`, `TEMPORARY_ROLE`, `SUITE_ADMIN_NO_ROLES`, 403 `REAUTH_REQUIRED` |
| `/auth/admin/users/:id/status` | PATCH | system, isActive | user | cookie, admin | 409 `LAST_ADMIN`, `IS_SUITE_ADMIN` |
| `/auth/admin/users/:id/unlock` | PATCH | system | user | cookie, admin | 404 |
| `/auth/admin/users/:id/reset-code` | POST | system | 204 | cookie, admin | 429 `CODE_SEND_LIMIT` |
| `/auth/admin/users/:id/sessions` | GET, DELETE | system | sessions / 204 | cookie, admin | 404 |
| `/auth/admin/users/:id/activity` | GET | system?, filters, cursor | events | cookie, admin | 404 |
| `/auth/admin/users/:id` | DELETE | system? | 204 | cookie, admin | 403 shared (system admin only), 409 `LAST_ADMIN`, `IS_SUITE_ADMIN` |
| `/auth/admin/users/:id/restore` | POST | system? | user | cookie, admin | 409 `NOT_RESTORABLE` |
| `/auth/admin/activity` | GET | system?, filters, cursor | events | cookie, admin (no system: suite) | 403 |
| `/auth/admin/deletion-requests` | GET | view, system?, cursor | items with orphan | cookie, admin | 400 `INVALID_CURSOR` |
| `/auth/admin/deletion-requests/:id/approve`, `/reject` | POST | system?, note (reject) | request | cookie, admin | 409 `NOT_PENDING`, 403 `SELF_DECISION` |
| `/auth/admin/suite-admins` | GET, POST | userId, reason, reauthToken | list / row | cookie, suite | 409 per AC-1, 403 `REAUTH_REQUIRED` |
| `/auth/admin/suite-admins/:userId/remove` | POST | reason, reauthToken | 204 | cookie, suite | 409 `SELF_ROLE`, `LAST_SUITE_ADMIN` |
| `/auth/admin/temporary-grants` | GET | state, system?, cursor | grants | cookie, admin | |
| `/auth/admin/temporary-grants` | POST | system, role, hours?, reason, reauthToken | grant | cookie, suite | 409 `GRANT_ACTIVE`, 400 `UNKNOWN_ROLE` |
| `/auth/admin/temporary-grants/:id` | DELETE | | 204 | cookie, holder / suite / that system's admin | 404 |
| `/auth/admin/report` | GET | | AC-19 body | cookie, suite | 403 `NOT_SUITE_ADMIN` |
| `/auth/admin/permissions/:system` | GET | | matrix, version | cookie, suite or that system's admin | 404 unknown system |
| `/auth/admin/permissions/:system` | PATCH | version, changes, note? | matrix | cookie, suite | 409 `MATRIX_STALE`, `LOCKED_CELL`, 400 `NOTE_REQUIRED` |
| `/auth/admin/permissions/:system/changes` | GET | cursor, limit | changes | cookie, suite or that system's admin | |
| `/auth/permissions/:system` | GET | If-None-Match | AC-26 body, ETag / 304 | service token `permissions.read` | 403 `WRONG_SYSTEM` |

Bearer `/auth/users*` and the other `@SystemAdmin()` routes: unchanged shapes, plus 403 `ADMIN_CODE_REQUIRED`, 409 `SUITE_ADMIN_NO_ROLES`, 409 `TEMPORARY_ROLE`, `reauthToken` when adding an admin role (403 `REAUTH_REQUIRED`), and `temporaryUntil` on user items. `POST /auth/profile/verify-password` accepts purpose `ADMIN_ACTION` from an admin's token (403 `NOT_AN_ADMIN` otherwise). `POST /auth/profile/deletion-request` answers 409 `IS_SUITE_ADMIN` for a suite admin.

backend-vrms: `PATCH /vrms/permissions` and `GET /vrms/permissions/changes` removed; `GET /vrms/permissions/me` and `GET /vrms/permissions` (read) stay.

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| any cookie route | the caller | `welinc_sso` cookie → `sessions.sso_handle_hash` → live session → `users` |
| any cookie route | which system the admin acts in | `system` input, checked against the caller's `isSystemAdmin` roles (`catalog.adminRoles`) or `suite_admins` |
| admin gate | code passed | `sessions.sign_in_code_at` (cookie session, or the bearer token's `sid`) |
| login | whether to ask the code | `suite_admins` row or any `user_roles` row whose role `isSystemAdmin`, plus `ADMIN_SIGN_IN_CODE` |
| report, admins | `since` | `user_roles.created_at` of the admin role row |
| report, admins | `grantedBy` | actor of the newest `ACCOUNT` event for that person and system whose `newValue` holds that role; none found (seed) shows null |
| report, suite admins | `grantedAt`, `grantedBy`, `reason` | `suite_admins` columns |
| temporary grant | `expiresAt` | `started_at` + `hours` input (default 4) |
| user lists | `temporaryUntil` | `temporary_grants.expires_at` through `user_roles.temporary_grant_id` |
| deletion lists | `orphan` | derived: the person's current `user_roles` systems, and whether any other active, not deleted person holds that system's admin role |
| alert email | recipients | `suite_admins` plus the active admins of the system concerned (`catalog.adminRoles`) |
| alert email | time | event time shown in Asia/Manila (as spec 0012) |
| alert email, VRMS links | portal address | `PORTAL_URL` (auth), `VITE_PORTAL_URL` (web-vrms) |
| matrix read | ETag | `permission_matrices.version` |
| matrix import | history actor | the export file's `actor_name` and `actor_email`; `actorId` only when `users` has that id |
| VRMS sync | matrix | `GET /auth/permissions/VRMS` with VRMS's service token (needs scope `permissions.read` on the `vrms-backend` client) |
| Chief notice | released tickets | VRMS `audit_logs` rows `MECHANIC_UNASSIGNED`, actor `SYSTEM`, last 7 days |

**Key invariants**:
- 1 to 3 rows in `suite_admins` at all times after the seed; never fewer than 1 through any route.
- A suite admin holds no permanent role: each of their `user_roles` rows has `temporary_grant_id` set (database trigger, AC-3).
- At most one live temporary grant per person and system; a live grant always has its `user_roles` row, an ended one never does.
- Nobody changes their own admin standing: no self grant of suite admin, no self removal, no self role change (spec 0011 rules stand), and the only self grant is the temporary one.
- Every admin power needs a session with `sign_in_code_at` (when `ADMIN_SIGN_IN_CODE` is on).
- Each system's last active admin rule holds on every path, suite admin paths included.
- `permission_changes` and the new `ACCOUNT` events are append only.
- A locked matrix cell always equals its catalog default.

**Security model**:
- Suite admin: every account and every system's roles, the report, suite activity, all deletion requests, the matrix. No system data unless a live temporary grant gives a role, and then only through that system's own checks.
- System admin: their system's people and roles only (spec 0011 scope), through the portal or the deprecated bearer routes; reads their system's matrix and ends temporary grants in their system.
- Everyone else: no `/auth/admin/*` access (403 `NOT_AN_ADMIN`).
- Escalation needs a second person or a loud trail: adding a suite admin needs another suite admin plus a password recheck; granting any system's admin role needs a password recheck and alerts; temporary access needs a reason, a password recheck, alerts the system's admins and ends on its own; the recovery script needs the server shell and alerts everyone.
- Taking over another admin's account needs the actor's password and alerts that system's admins (AC-14b); a suite admin's email changes only through their own inbox.
- Residual risk, accepted: a suite admin can still create a second account with an email they control and give it a system role. AC-14c makes that loud (password recheck, an alert to that system's admins, the event in Activity), not impossible, since suite admins legitimately create accounts for new staff.
- A mobile login never gets the code step, which is safe because mobile tokens carry no admin role (`allowed_roles`) and every admin route checks the session's `sign_in_code_at`.
- Cookie routes keep tokens out of page scripts (contract 0001) and use the CSRF guard. Matrix reads by systems need a service token for that system only.
- Every change in this spec is logged (events or `permission_changes`); access control changes are audit scope, so these logs are not optional.

**Configuration required**:
- `ADMIN_SIGN_IN_CODE`: `true` by default; `false` turns off the admin code locally (refused in production). Goes in `src/config/env.ts` and `.env.example` together.
- The `vrms-backend` client in `clients.seed.ts` gains scope `permissions.read`.
- No new variables in backend-vrms or the portal (`VITE_PORTAL_URL` and `AUTH_INTERNAL_URL` exist).

**Critical test scenarios**:
- Happy path: a suite admin signs in with the code, opens Overview, gives themselves VRMS Admin for 2 hours with a reason, VRMS admins get the email, the grant ends early, the VRMS session ends: verifies AC-5, AC-9, AC-10, AC-13, AC-19.
- Failure case: two suite admins add a fourth at once; exactly one wins, the other gets `SUITE_ADMIN_LIMIT`: verifies AC-1.
- Failure case: a grant expires while the holder works in VRMS; within a minute the role is gone and their VRMS requests answer 401 `SESSION_ENDED` within 30 s: verifies AC-10.
- Failure case: a stale matrix `PATCH` answers `MATRIX_STALE`; welinc-auth down keeps VRMS on its last copy: verifies AC-27, AC-29.
- Auth/permission: a VRMS admin asks for BMS people (403 `NOT_ADMIN_OF_SYSTEM`), edits the matrix (403 `NOT_SUITE_ADMIN`), changes their own roles (409 `SELF_ROLE`); a VRMS admin session from before this ships gets 403 `ADMIN_CODE_REQUIRED` until the step up: verifies AC-6, AC-16, AC-27.
- Auth/permission: granting a permanent VRMS role to a suite admin answers `SUITE_ADMIN_NO_ROLES` on both route families: verifies AC-3.

## Build plan

Tracer Bullet: the first slice is a thin thread through auth, portal and VRMS (a suite admin can sign in with the code and reach an admin shell), then each slice thickens it end to end. The matrix is the last slice so it can be cut without touching the rest (the Nov 11 rule: cut permission editing first).

*Slice 1: the thread (admin identity and the code)*
1. Migration A: `suite_admins`, `sessions.sign_in_code_at`, the enum values (`ReauthPurpose`, `SessionEndReason`, the six event types and their catalog labels, the rebuilt `CHECK`), satisfies **AC-1**, **AC-4**, **AC-5**
2. `ADMIN_SIGN_IN_CODE` in `env.ts` and `.env.example` with the production rule, satisfies **AC-8**
3. Login asks the code for admins, `sign_in_code_at` on any code finish, `ADMIN_CODE_PASSED`, and the empty launcher for suite admins, satisfies **AC-5**, **AC-7**
4. The cookie admin guard (`NOT_SIGNED_IN`, `NOT_AN_ADMIN`, the code gate), `GET /auth/admin/me`, the step up routes, and the gate on `@SystemAdmin()`, satisfies **AC-6**, **AC-7**, **AC-14**, **AC-15**
5. Seed: `suiteAdmin` in the manifest, `checkManifest` rules, the `suite_admins` row, the VRMS copy, satisfies **AC-33**
6. `admin:recover` script, satisfies **AC-12**
7. Portal: login and step up code screens, the Admin top bar entry (also with no systems), an empty `/admin` shell, satisfies **AC-22**

*Slice 2: system admins in the portal, VRMS switches*
8. Refactor the user, sessions, activity and deletion services to take a scope instead of `aud`; bearer controllers resolve it from the token, satisfies **AC-16**, **AC-18**
9. Cookie account routes under `/auth/admin/users*`, activity and deletion requests for system admins, `POST /auth/admin/verify-password`, the `ADMIN_ACTION` recheck for adding an admin role and for actions on admin accounts on both route families, `SUITE_ADMIN_SELF_ONLY`, and their alerts, satisfies **AC-14**, **AC-16**, **AC-14a**, **AC-14b**
10. Portal People view, person page with every action, Add person, Deletion requests, Activity, deep links, system switcher, satisfies **AC-23**
11. VRMS: Users page as a team view with Manage account and Add user links, the `team.manage` key (added to backend-vrms `catalog.ts` here; slice 5 moves its label and defaults to welinc-auth's `vrms.ts`), the `ADMIN_CODE_REQUIRED` message, satisfies **AC-31**

*Slice 3: suite admin powers*
12. Suite admin routes (list, add, remove) with the advisory lock and reauth, the `SUITE_ADMIN_NO_ROLES` and `IS_SUITE_ADMIN` rules on every write path plus the deferred trigger, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-4**
13. Suite scope on the account routes: all people, shared account delete and restore, any deletion request, orphans, suite activity, the recheck and alert on every suite admin role grant or account creation, satisfies **AC-14c**, **AC-17**, **AC-20**, **AC-21**
14. Migration B: `temporary_grants`, `user_roles.temporary_grant_id`, the `temporary` flag in `directory_snapshot()`; grant and end routes, the minute sweep (advisory lock), the lazy expiry check in token building, session ends, `temporaryUntil` and `TEMPORARY_ROLE`; the VRMS roster skips temporary roles, satisfies **AC-9**, **AC-10**, **AC-11**
15. Alert emails for every AC-13 change, satisfies **AC-13**
16. `GET /auth/admin/report`, satisfies **AC-19**
17. Portal Overview, Suite admins, Temporary access dialog and banner, suite views of People, Activity and Deletion requests, satisfies **AC-23**, **AC-24**

*Slice 4: VRMS leavers*
18. Chief dashboard Released after account changes notice, satisfies **AC-32**

*Slice 5: central permissions (cut first if time runs short)*
19. Migration C: `system_permissions`, `role_permissions`, `permission_matrices`, `permission_changes` with its append only trigger and erasure allowance; `permissions` in `vrms.ts` and `catalog:sync`, satisfies **AC-25**
20. `GET /auth/permissions/:system` with ETag, the `permissions.read` scope on the VRMS client, satisfies **AC-26**
21. Matrix read, edit and history routes, alerts; portal Permissions view (read only for system admins), satisfies **AC-27**, **AC-13**
22. `permissions:export` (VRMS) and `permissions:import` (auth) with the `users.manage` to `team.manage` copy, run once locally in the AC-28 order and noted for staging, satisfies **AC-28**
23. VRMS matrix sync job and `permission_sync_state`, satisfies **AC-29**
24. VRMS removals: edit and history routes, backfill, prune, labels and defaults, the Settings screen; `users.manage` routes to `team.manage`; the drop migration for `permission_changes` after the import, satisfies **AC-30**

*Slice 6: contract and guide*
25. Contract 0001 version 7 and `docs/integration/suite-admin.md`, satisfies **AC-34**

## Consequences

**Positive**:
- No everyday superuser: the most powerful accounts can't read system data without a visible, expiring, reasoned grant.
- VMMS and BMS delete about 1,450 lines of user pages instead of porting them in S11.
- Every admin sign in is confirmed by a second step, and every admin level change emails the people who would care.
- One matrix editor group and one history, and other systems can join the matrix without new auth code.

**Negative / tradeoffs**:
- The email code is half a second factor: whoever owns an admin's inbox can reset the password and read the code. TOTP is the fix (Follow-up).
- Every admin portal sign in now sends a real email, also locally with `SMTP_*` set; seed admin addresses can't receive mail, so local admins need `ADMIN_SIGN_IN_CODE=false` or blank SMTP.
- Ending a temporary grant ends the holder's whole web session (portal included), since sessions span systems.
- Two admin route families live side by side until S11 finishes; both must keep the same rules (one service layer is what keeps that true).
- A matrix edit reaches VRMS within about a minute, not instantly; VRMS depends on welinc-auth for a fresh copy (but keeps the last one).
- People with both jobs need two accounts.
- A large spec: six slices across four repos before the end of November.

**Neutral**:
- VRMS feature 34 (Admin OTP) is covered by AC-5 to AC-8 with spec 0009's code rules; its row should be marked replaced.
- The VRMS `permission_changes` table moves to welinc-auth in one export and import; staging needs the same two commands once.
- VRMS `users.manage` and `permissions.manage` go away; the work routes they guarded move to `team.manage`.

## Follow-up

- [ ] Optional TOTP (authenticator app) for admins, later for anyone who wants it: enrolment, encrypted secret, recovery codes, a suite admin resets a lost phone. You'll bring it to the groups when ready.
- [ ] A later spec removes the bearer admin routes once VMMS and BMS have moved (S11).
- [ ] VMMS and BMS join the central matrix when they move to permission checks (VMMS planned it); their catalog files then get `permissions`.
- [ ] Mark VRMS feature 34 as replaced by S10 (spec 0013, AC-5 to AC-8) in `docs/scope/vrms/platform.md`.
- [ ] S12's last Done when item (the platform admin seed account) closes with AC-33.
- [ ] Break glass account: dropped in favour of the recovery script (AC-12); revisit only if the suite grows past one small team.
