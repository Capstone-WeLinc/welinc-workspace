# 0018. Roles page and custom roles

**Date**: 2026-11-23
**Status**: Proposed
**Scope rows**: [S20](../../../scope/_root/shared-services.md#s20-permissions-page-redesign--planned--needs-a-decision--beta) (child 0001) and [S21](../../../scope/_root/shared-services.md#s21-custom-roles-per-system--planned--needs-a-decision--ga) (child 0002)
**Repos**: `welinc-auth`, `welinc-web-portal`, `welinc-backend-vrms`, `welinc-web-vrms`, workspace (`docs/integration/`, contract 0001)
**Design source**: boards `Roles9`, `DraftMarks` (B), `SaveBar9`, `Picks8` (RC) and `Confirm6` (DB) on the canvas "WeLinc design directions" (https://claude.ai/artifact/VFhLSMNhfpAFD4D4c2VQzp), page "Round 8". Copies live in [boards/](boards/) (`.dc.html` source, readable from any account). The look follows spec [0016](../0016-design-direction-refresh/index.md); the app shell and People routes follow spec [0017](../0017-person-page-systems/index.md).

## Summary

The portal's Permissions page is one long grid of 27 permissions by 3 roles. This spec turns it into the approved `Roles9` page: a list of roles on the left, one role on the right with Permissions, People and History tabs, switches with plain descriptions, and every change saved through the navy save bar and a review dialog. On top of that page, suite admins can make their own VRMS roles (copied from an existing one), rename them and delete them once empty. Custom roles are only offered for systems that use WeLinc permissions (VRMS today), and VRMS stops deciding things by role name: who can be assigned tickets becomes a permission.

## Structure

| Child | What it is | Decision it supports |
|---|---|---|
| [0001-roles-page.md](0001-roles-page.md) | The `Roles9` page: list, role detail, Permissions with descriptions and a filter, the multi role save bar and review, drafts, People with Add people, History, the spreadsheet download | S20: role first editing replaces the grid |
| [0002-custom-roles.md](0002-custom-roles.md) | Creating, duplicating, renaming and deleting custom roles; what tokens, contracts, the sync and VRMS change so a custom role really works | S21: custom roles for systems with permissions, behaviour by permission not by role code |

Build 0001 first (it works on today's three built in roles), then 0002 on the same page.

## Shared contract (both children build against this)

### Data model (welinc-auth)

| Table | Change |
|---|---|
| `system_roles` | Adds `is_built_in` `boolean NOT NULL DEFAULT true` (the 12 existing roles stay built in), `copied_from` `varchar(40)` null (the code of the role it was made from; no FK, history outlives the source), `created_by_id` `uuid` null (FK `users`, `ON DELETE SET NULL`), `deleted_at` `timestamptz(6)` null (archived). Partial unique index on `(system, lower(name)) WHERE deleted_at IS NULL AND NOT is_built_in` (custom names); the create and rename routes also refuse a custom name equal to a live built in name, while `catalog:sync` never checks names, so a later built in rename can't fail a deploy. CHECK `is_built_in OR NOT is_system_admin` (a custom role is never the admin role). |
| `system_permissions` | Adds `default_roles` `varchar(40)[] NOT NULL DEFAULT '{}'`: the built in roles whose catalog default is on, written only by `catalog:sync` (child 0001's Reset to defaults reads it). The migration fills it from the current catalog. |
| `role_events` (new) | Append only (a trigger refuses UPDATE and DELETE, as on `permission_changes`; erasure may blank the actor columns). `id` uuid PK · `system` `SystemType` · `role` `varchar(40)` (no FK) · `kind` enum `RoleEventKind` (`CREATED`, `RENAMED`, `DESCRIBED`, `DELETED`) · `from_value` `varchar(200)` null · `to_value` `varchar(200)` null · `actor_id` uuid null (FK `users`, set null) · `actor_name` `varchar(100)` null · `actor_email` `varchar(255)` null · `created_at` `timestamptz(3)` default now. Index `(system, role, created_at DESC, id DESC)`. |
| `permission_changes` | Adds the index `(system, role, created_at DESC, id DESC)` for a role's History and `lastChanged`. Otherwise unchanged (already keyed by role code, no FK). |

Rules the database or the service enforces:
- A live role is `deleted_at IS NULL`. Every picker, list, token and the permission poll see live roles only; history reads see all.
- At most 20 live custom roles per system (checked inside the create transaction after `SELECT … FOR UPDATE` on the `systems` row).
- A custom role's `code` is made once from its name: uppercase ASCII, every run of characters other than A to Z and 0 to 9 becomes `_`, trimmed of `_`, cut to 24 characters, prefixed with `C_`, then `_2`, `_3`… (at most `_99`) on a clash with any code the system has ever had (live, archived, or in the catalog file). So it is at most 30 characters (VRMS stores role codes in `varchar(30)` columns), matches `ROLE_CODE_RE`, is never shown in the UI, and never changes. The `C_` prefix is reserved: `catalog:sync` refuses a catalog code starting with `C_`, so a catalog code can never meet a custom one. A name that yields an empty body (no A to Z or 0 to 9, such as "!!" or only non Latin letters) is refused with 400 `VALIDATION_FAILED` "Use letters or numbers in the name." (the name itself may also hold other characters).
- **Assignment and delete never race.** Every path that gives a role (child 0001's members route, spec 0017's Change role and Add person, Temporary access) and Delete first lock the target `system_roles` row (`SELECT … FOR UPDATE`) and check `deleted_at IS NULL` in the same transaction; giving an archived role answers 400 `UNKNOWN_ROLE`.
- Delete is refused while a live holder exists: a `user_roles` row of a person who isn't soft deleted (deactivated people count), or a live temporary grant. Holders in their deletion grace period don't block: their rows stay on the archived role, and a later Restore drops any archived role from the restored person (they come back with their other roles, or none). Rows of a temporary grant past its end that the sweep hasn't removed yet don't block either; the sweep removes them. Ended temporary grants keep pointing at the archived row.

### API surface (welinc-auth, portal cookie session, `AdminSessionGuard`; writes add `PortalCsrfGuard`)

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/admin/roles/:system` | GET | none | `{ system, supportsCustomRoles, canEdit, version, roles[], groups[], cells }` (below) | suite admin, or admin of `:system` | 403 `NOT_ADMIN_OF_SYSTEM`, 404 `NOT_FOUND` |
| `/auth/admin/roles/:system/:code/history` | GET | `cursor?`, `limit?` (default 25, max 100) | `{ items[], next }`: permission changes of that role and its role events merged, newest first | same | 400 `INVALID_CURSOR`, 404 (code never existed) |
| `/auth/admin/permissions/:system` | PATCH | as today: `version`, `changes[]` (cells of any roles), `note?` | as today | suite admin | as today: 400 `NOTE_REQUIRED`, `UNKNOWN_ROLE` (now also an archived role), 409 `LOCKED_CELL`, `MATRIX_STALE` |
| `/auth/admin/roles/:system/:code/members` | POST | `userIds` (1 to 50 uuids), `reauthToken?` | `{ moved: number, skipped: number }` | suite admin, or admin of `:system` | 400 `NOT_IN_SYSTEM`, `SELF_ROLE`, `SUITE_ADMIN_NO_ROLES`, `UNKNOWN_ROLE`, `REAUTH_REQUIRED`; 404; 409 `TEMPORARY_ROLE`, `LAST_ADMIN`, `ROLE_LIMIT` (codes and statuses as in spec 0017) |
| `/auth/admin/users` (spec 0017's list) | GET | adds `excludeRole?` (needs `system`: leaves out holders of that role), `assignable?` (`true` leaves out suite admins and the caller) | as spec 0017 | as spec 0017 | as spec 0017, plus 400 `UNKNOWN_ROLE` |
| `/auth/admin/roles/:system` | POST | `name`, `description?`, `from` (a live role code) | the new role (as in `roles[]`) plus its `cells` (allowed keys) and the new `version` | suite admin | 400 `VALIDATION_FAILED`, `UNKNOWN_ROLE`; 409 `ROLE_NAME_TAKEN`, `CUSTOM_ROLE_LIMIT`, `CUSTOM_ROLES_NOT_SUPPORTED` |
| `/auth/admin/roles/:system/:code` | PATCH | `name?`, `description?` | the role | suite admin | 400 `BUILT_IN_ROLE`, `VALIDATION_FAILED`; 404; 409 `ROLE_NAME_TAKEN` |
| `/auth/admin/roles/:system/:code` | DELETE | none | `{ version }` | suite admin | 400 `BUILT_IN_ROLE`; 404; 409 `ROLE_IN_USE` (`details.count`) |
| `/auth/systems` (public, unchanged route) | GET | none | each role gains `builtIn`; archived roles left out; `Cache-Control: no-cache` with the existing ETag (was `public, max-age`), so a create, rename or delete shows on the next read | public | as today |
| `/auth/permissions/:system` (service) | GET | as today | grants for live roles only (custom ones included) | service token | as today |

`GET /auth/admin/roles/:system` answer:
- `supportsCustomRoles`: the system has at least one `system_permissions` row.
- `canEdit`: the caller is a suite admin.
- `version`: the `permission_matrices.version` (the existing ETag the PATCH needs), read through `MatrixService.version()`, which answers 1 when the system has no matrix row. The page never sends a PATCH for a system without permissions.
- `roles[]`: live roles, built in first by `sortOrder`, then custom by `lower(name)`: `{ code, name, description, builtIn, isSystemAdmin, copiedFrom: { code, name } | null, peopleCount, lastChanged: { at, byName } | null }`. `peopleCount` = `user_roles` rows for that role whose user is not deleted (`deleted_at IS NULL`), the people the People tab lists. Delete checks every row, including people in their deletion grace period, and its 409 carries that count. `copiedFrom.name` reads the source row even if archived. `lastChanged` = the newest of that role's `permission_changes` and `role_events` (`byName` = `actor_name`, "System" for the sync).
- `groups[]`: in catalog order, `{ name, permissions: [{ key, label, description, lockedRoles, defaultRoles }] }`.
- `cells`: `{ [roleCode]: string[] }`, the allowed keys of each live role.

History items: `{ at, actorName, kind, key?, label?, before?, after?, fromValue?, toValue?, note? }` where `kind` is `PERMISSION` (from `permission_changes`) or a `RoleEventKind`. The two sources merge in one order, `(created_at DESC, id DESC)` (both ids are uuids, so ties break the same way every time), and the cursor carries the last `(created_at, id)`. The cell rows a create writes (note "Created from [source]") and a delete writes (after null, same transaction as the `DELETED` event) are left out of History: the one `CREATED` or `DELETED` line stands for them. They still count for the systems' audit and for `lastChanged`.

Every write that adds, removes or changes cells (PATCH, create, delete) raises `permission_matrices.version` in the same transaction, so systems polling `/auth/permissions/:system` pick it up within their poll.

Contract 0001 gets a new minor version with a Changes line: the `builtIn` field on `/auth/systems`, role codes made at runtime (any `ROLE_CODE_RE` code may appear in tokens, `/auth/me` and the directory feed for a system that supports custom roles), and the admin routes above.

### Value sourcing

| Action | Value produced or displayed | Source |
|---|---|---|
| Role list | name, built in or custom, people in words, order | `roles[]`: `name`, `builtIn`, `peopleCount`; order as served |
| Role list | draft bubble count | the stored draft (child 0001, AC-5): changes whose `role` is that code |
| Role list | "11 roles" | `roles.length` |
| System switch | which systems | `/auth/admin/me`: `suiteAdmin`, `adminOf` |
| Role header | Built in or Custom chip, the one line help | `builtIn` |
| Role header | People, Permissions "N of [total]", Last changed | `peopleCount`; N = count of `cells[code]` (locked "Always on" cells are in it, locked "Always off" cells aren't), total = the number of keys in `groups` (28 for VRMS once `ticket.assignable` lands); `lastChanged` |
| Permission row | label, description, locked text | `groups[].permissions[]`: `label`, `description`, `lockedRoles` contains the code |
| Permission row | on or off | the draft's `to` if the draft holds that cell, else `cells[code]` contains the key |
| Group header | "allowed/total", preview names | derived from the rows above |
| Save bar | "N unsaved changes in M roles", sub line | draft length; distinct roles in the draft; their names and the sum of their `peopleCount` |
| Change list and review | faces and "Ramon, Alfredo and 6 others" | `GET /auth/admin/users?system&role=<code>&limit=3` per role in the draft, fetched when the list or dialog opens, plus `peopleCount` |
| Review dialog | note required or not | any change in the draft with `to = false` |
| Save | cells and version | the draft; `version` from the last read |
| Reset to defaults | the changes it stages | `defaultRoles` of each unlocked permission against the role's current cells |
| People tab | holders, "Since [date]", "Until [date]" | `GET /auth/admin/users?system&role=<code>` (spec 0017's list route): each item's role for that system with `temporaryUntil`; "Since" from the role row's `createdAt` (added to each `roles[]` entry by this spec) |
| Add people | candidates and their current role | `GET /auth/admin/users?system&q&excludeRole=<code>&assignable=true&sort=name` (server side, so paging holds); role names from `roles[]` |
| New role dialog, review dialog | warning that a role can manage the team or settings | the source role's cells (New role) or the role's cells after the draft (review) contain `team.manage` or `settings.manage`, on a custom role |
| History tab | rows | `/history` items |
| Spreadsheet | every role by every permission | `roles[]`, `groups[]`, `cells` (saved values, not the draft) |
| New role dialog | "Start from" choices, default | live `roles[]`; the role on screen |
| Delete dialog | holder count and names | `peopleCount` (or the 409's `details.count` when the server refuses); `GET /auth/admin/users?system&role=<code>&limit=10` |
| web-vrms role names | label of a role code | `GET /auth/systems` (child 0002, AC-35); before that ships, the code in title case ("Chief mechanic" from `CHIEF_MECHANIC`) |
| VRMS roster | who can be assigned tickets, who is a lead | VRMS's synced `role_permissions` for `ticket.assignable` (assignable) and `ticket.verify` (lead), read at recompute time, and each person's VRMS roles from the directory (child 0002, AC-33, AC-34) |

### Security model

- Reading the Roles page: suite admins (every system) and admins of that system (their systems only), as the permissions read is today (spec 0013, AC-27).
- Changing permissions, creating, renaming and deleting roles: suite admins only. Roles change what everyone in a system can do, so they stay behind the strongest admin.
- Add people is a role change, the same write as Change role in spec 0017: suite admins and that system's admins, with the existing rules (no own role, not a suite admin, not a temporary row, a password step when the target role is the system's admin role, `LAST_ADMIN`).
- A custom role can never be the system admin role, so the admin only checks (`isSystemAdmin`: account admin in welinc-auth, the admin password step) never see one. Its permission cells can still include powerful keys: copying from Admin copies `team.manage` and `settings.manage`, and a system admin can then move people into that role. That is accepted (only a suite admin can make such a role), and made visible: the New role dialog and the review dialog warn "[Role] can manage the team and change settings in [system]." whenever a custom role would hold either key.
- Every write is recorded: permission changes and role events with the actor; role moves as today's account events.

## Decision

**Chosen option**: Option 3: the `Roles9` page, plus custom roles only for systems that use WeLinc permissions, with VRMS behaviour moved from role codes to permissions.

Roles are edited one at a time on a list and detail page, custom roles are real rows in welinc-auth that every token and poll carries, and VRMS decides who is a mechanic by a permission, so a custom role works end to end.

**Implementation skills**: `nestjs-best-practices` (`.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`.claude/skills/prisma-client-api/`) · `prisma-cli` (`.claude/skills/prisma-cli/`) · `shadcn` (`.claude/skills/shadcn/`) · `react-hook-form` (`.claude/skills/react-hook-form/`) · `ask-sonner` (`.claude/skills/ask-sonner/`) · `vercel-composition-patterns` (`.claude/skills/vercel-composition-patterns/`)

## Migration plan

**Strategy**: strangler, four deploys in order.
**Phases**:
1. welinc-auth, additive: the `system_roles` columns, `default_roles`, `role_events`, the read and history routes, `createdAt` on each `roles[]` entry, `builtIn` on `/auth/systems`, the members route. Today's portal, VMMS, BMS and VRMS keep working unchanged.
2. Portal: the Roles page (child 0001) replaces `PermissionsView`; `/admin/permissions` redirects.
3. Child 0002 steps 1 and 2: welinc-auth first (`ticket.assignable`, the sync limited to built in rows with the `C_` reservation, `/auth/systems` revalidation), then VRMS (AC-32 to AC-35): permissions for every live role, the roster by `ticket.assignable`, role names from the catalog. This ships **before** custom roles can be created, so the first custom role already works in VRMS. `ticket.assignable` lands in the welinc-auth catalog in the same release as VRMS's catalog key (welinc-auth first: VRMS ignores keys it doesn't know, and the sync only adds cells).
4. welinc-auth and portal: create, rename, delete, the role locks on every assignment path, the check that VMMS and BMS tolerate an unknown VRMS role code (child 0002, AC-37), contract 0001's new version.
**Order with VRMS spec 0027** (navigation): phase 3's VRMS step (child 0002 step 2) ships before 0027's step 1, since both touch `navItems.ts`, `session.ts`, `RoleBadge` and the account menu, and 0027 reads role names and roster membership from it.
**Rollback**: each phase reverts on its own. Phase 1's columns are nullable or defaulted. Reverting phase 4 while custom roles exist leaves them in the database: tokens and VRMS still work, but nothing can edit them until it is redeployed, and `catalog:sync` ignores them (child 0002, AC-30), so deploys don't break.
**Risks**: the roster switch in phase 3 must give the same people as today before any custom role exists (a test compares both rules on the seed); deploy outside the 2 hour freeze before each defense.

## Consequences

**Positive**:
- An admin reads and changes one role at a time, with a plain description under every switch, instead of scanning 27 rows by 3 columns.
- Several roles can be changed and saved in one review, with a note required whenever something is taken away.
- VRMS gets real custom roles ("Night shift lead", "Quality checker") without a code change per role, and the role list scales because the page was built for it.
- VRMS stops deciding behaviour by role name, so a role's permissions are the whole truth about what it can do.

**Negative / tradeoffs**:
- VMMS and BMS can't have custom roles until they adopt permission keys; their Roles page is read only and shows only People.
- Built in roles can't be renamed; a garage that calls its Chief mechanic "Foreman" can't change the label.
- Four deploys across four repos, with a VRMS roster change in the middle that must match today's behaviour exactly.
- A custom role can be granted powerful permissions (`team.manage`, `settings.manage`) by a suite admin; a warning, the review step and the history are the only guards.
- Custom VRMS roles can't sign in to the shared mobile app (its client keeps MECHANIC and CHIEF_MECHANIC); a "Tire specialist" works from the browser until feature 48 decides the mobile rule.
- The full grid is gone from the screen; the spreadsheet download is the only view of every role at once.

**Neutral**:
- `catalog:sync` keeps owning built in roles; custom roles live only in the database, so a fresh database has none until someone makes them (seeds may add examples, feature 72).
- The old `GET /auth/admin/permissions/:system` stays for compatibility; the portal stops calling it.

## Follow-up

- [ ] Feature 72 (realistic demo data): seed two or three custom VRMS roles with holders (for example Night shift lead, Quality checker) so the defense shows the Custom section.
- [ ] Tell VMMS and BMS (in the next round of the 2026-11-22 handoff list): custom roles exist for systems with permission keys; adopting keys is how they get them. Nothing changes for them today.
- [ ] `/sync`: welinc-auth `AGENTS.md` gains that `system_roles` holds custom rows the sync ignores, and that VRMS reads the mechanic roster from `ticket.assignable`.
- [ ] Spec 0017's follow-up (whether custom roles show differently in a person's Access row) is settled here: a custom role uses the outlined `RoleChip` everywhere a role chip shows (spec 0016, AC-15).
- [ ] Contract 0001: write the new version and its Changes line in phase 4.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
