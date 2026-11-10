# 0012. Configurable settings and modules: one Admin Settings hub on a code catalog

**Date**: 2026-10-30
**Updated**: 2026-10-30 (Recent changes asked by key, AC-31; change rows read with units and the reset value, AC-26; AC-24 review step and a required reason when a right is removed)
**Updated**: 2026-11-01 (spec 0016 adds generic lookup lists, a Vehicles section and one threshold; see Follow-up)
**Updated**: 2026-11-11 (staleness sweep: the catalog holds 18 settings now, not AC-1's 7, added by specs 0013, 0015, 0016, 0017 and 0018; `/settings` has six sections with Vehicles; the Python service parts of AC-13 to AC-15 and AC-17 moved into backend-vrms with spec 0013, which reads the module switches itself)
**Status**: Accepted

## Summary

VRMS gets one Settings hub where an Admin changes thresholds and switches whole modules (AI, Analytics, Knowledge base) on or off without a deploy. Each setting is defined once in code (a settings catalog with its type, default and allowed range); the database stores only the values an Admin changed, and every change is logged with who, when, before, after and why. A module that is off disappears for everyone, its API calls are refused, and its background work stops, while its data stays for when it comes back. The hub also becomes the home of the permission matrix editor (spec 0011) and the lookup lists, starting with issue categories.

## Requirements

**User stories**:
- As an Admin, I want to change a threshold or turn a module off without a developer or a deploy, so that VRMS follows how the garages work.
- As an Admin, I want every settings and permission change logged with a reason, so that I can see who changed what and why.
- As any user, I want a switched off module to vanish cleanly, so that I never hit a button that fails.
- As the system owner, I want a switched off module refused on the server and its background work stopped, so that "off" really saves AI spend and is never only a hidden button.
- As a developer, I want code to read every setting from one place, so that a new tunable is one catalog line, not a hunt for constants.

**Acceptance criteria**:

*Catalog and storage*
- **AC-1**: `src/settings/catalog.ts` in backend-vrms is the one definition of settings. Each entry has `key`, `kind` (`module` or `value`), `group`, `label`, `description`, `type` (`int` or `boolean`; a `decimal` type is added by the first setting that needs one) and `default`. A value entry also has `min`, `max`, `unit` and an optional `module` (the module it belongs to); a module entry also has `hides` (a plain list of what turns off) and an optional `requires` (module keys it needs). It holds exactly the 7 entries in *Settings catalog* below.
- **AC-2**: `app_settings` holds a row only for a key an Admin set; no row means the catalog default. Nothing inserts rows at startup. A row whose key left the catalog is ignored; `npm run settings:prune` deletes such rows, logging each as a `RESET` by System.
- **AC-3**: Code reads every setting through `SettingsService.get(key)`, typed by key. `KNOWLEDGE_SETTINGS` is gone: the four business values come from the service, and the knowledge helpers take them as required parameters (no default parameter values). The three tuning constants (`GROUP_SIMILARITY`, `SEARCH_SIMILARITY`, `GROUP_CANDIDATE_LIMIT`) and `ENTRIES_PAGE_SIZE` stay in code as `KNOWLEDGE_TUNING` in `knowledge.tuning.ts`.
- **AC-4**: A save applies on the next request on every replica. The per request freshness check (`PermissionsService.ensureFresh`) reads `permission_matrix.version` and `settings_state.version` in one query and reloads whichever moved. A replica that has never loaded settings answers 503 like the matrix; a warm replica keeps its last settings when the read fails, and logs a warning.

*Saving*
- **AC-5**: `PATCH /vrms/settings` with `{ version, changes, note? }` writes the changed rows, one `SettingChange` per key whose effective value changed (`SET`, or `RESET` back to default, which deletes the row), and bumps `settings_state.version` by one, all in one transaction. A change equal to the current effective value is skipped and not logged; a save where nothing changed returns 200 with no bump.
- **AC-6**: The save is refused with 400 and writes nothing for: an unknown key, the same key twice, a value of the wrong type, a non integer for an `int`, a value outside `min` and `max`, a change with both or neither of `value` and `reset`, or more than 50 changes. The message names the key and the rule.
- **AC-7**: A save whose `version` is not the current one gets 409 `{ statusCode: 409, message: 'Settings changed since you loaded them. Reload and try again.', version: <current> }` and writes nothing.
- **AC-8**: A save that changes any module key needs a `note` of 5 to 500 characters (400 otherwise). A save of values only takes an optional note of up to 500 characters.
- **AC-9**: Module dependencies: turning a module on while a module it `requires` is off is refused with 400 naming the missing module. Turning a module off also turns off every module that requires it (transitively) in the same save, each logged as its own `SettingChange` with the same note. No real module requires another today; unit tests prove both rules on a test catalog.

*Modules*
- **AC-10**: Each permission catalog entry may name a `module`: `knowledge.view`, `knowledge.suggest` and `knowledge.edit` belong to `knowledge`; `analytics.view` to `analytics`; the new `ai.use` to `ai`. When a module is off, its keys are removed from every user's key set, from the CASL ability on the server and from `/vrms/permissions/me`, whatever the matrix says. Matrix rows are untouched, so turning the module back on restores the same grants.
- **AC-11**: A request to a route whose key belongs to an off module gets 403 `{ statusCode: 403, code: 'MODULE_DISABLED', module: '<name>', message: 'This module is turned off by your Admin.' }`. The guard runs after `ensureFresh` and checks the module (`catalogEntry(key).module` for the route's key) before the role, so the answer is the same for every role. A route whose key has no module but whose action belongs to one checks the module in its service and throws the same body: today only `linkKnowledge` (AC-15).
- **AC-12**: `GET /vrms/permissions/me` also returns `modules: { ai, analytics, knowledge }` (booleans). The web app hides every nav item, page, panel and button of an off module. A bookmarked URL of an off module shows a "This module is turned off by your Admin" page with a link to the dashboard. The change reaches an open tab through the existing refetch (focus, every 60 seconds, after any 403); `PermissionsProvider` compares `modules` as well as keys, so a modules only change still updates. Route guards check the module first and the key second, so an off module's URL shows the module off page, not the 403 page.
- **AC-13**: AI off: backend-vrms skips `autoEmbedIssues`; the repair detail hides the AI diagnosis panel (shown with `ai.use`); the Analytics page hides its AI stats block (`/ai/stats`) while the rest of the page works; the Python service answers 403 `MODULE_DISABLED` on every `/ai/*` route (`/ai/diagnose`, `/ai/feedback`, `/ai/embed-issue`, `/ai/knowledge/articles`, `/ai/logs`, `/ai/stats`) and its sync skips the embedding step.
- **AC-14**: Analytics off: the Analytics page and nav item hide (its sample data fallback never shows); the Python service answers 403 `MODULE_DISABLED` on every `/analytics/*` route and its sync skips its analytics steps. Sync steps per switch (step numbers as in `sync_service.py`): both on, steps 1 to 4; AI off, steps 1, 2 and 4 (step 3 skipped, the old `repair_issue_embeddings` table left untouched, the Mongo audit records 0 vectors); Analytics off, steps 1 and 3; both off, nothing runs. Each step reads the switch when it starts. `/health` always answers.
- **AC-15**: Knowledge base off: the knowledge pages, suggestions, and the repair form's knowledge picker and auto fill hide. `PATCH /vrms/repairs/:id/issues/:issueId/knowledge` answers 403 `MODULE_DISABLED`. The move to For verification skips the "What fixed it" rule (`checkResolutions` does not run and any resolutions in the body are ignored). An issue already linked shows its entry name as plain text, not a link. Issue categories keep working (AC-19).
- **AC-16**: Turning a module back on brings everything back with its data, and nothing is backfilled (the Python sync embeds again on its next run).
- **AC-17**: The Python service reads `module.ai` and `module.analytics` from `app_settings` through `VRMS_DB_URL`, cached in memory for 5 seconds behind a lock (the sync thread and request threads share it), each read on a connection with a 2 second connect timeout. The `jsonb` value arrives as a Python bool. No row means on. A failed read keeps the last known value (on if never read) and logs a warning. The 403 is a flat `JSONResponse` `{ detail, code: 'MODULE_DISABLED' }` from a router level dependency on the `/ai` and `/analytics` routers, so `/health` is never gated. The Python side can lag a change by up to 5 seconds (backend-vrms applies it on the next request). The sync's `sys.exit(1)` calls become raised exceptions the worker catches, so a database error no longer kills the sync thread.

*Permission keys and lookup lists*
- **AC-18**: Three new permission keys: `settings.manage` (group Admin; Admin on and locked on, Chief Mechanic and Mechanic off and editable; no module), `lookups.manage` (group Admin; Admin and Chief Mechanic on, Mechanic off, editable; no module) and `ai.use` (group Tickets; all three roles on, editable; module `ai`). The migration copies each role's stored `knowledge.edit` value to `lookups.manage`, logs a `PermissionChange` per row with a null actor and the note `Copied from knowledge.edit (spec 0012)`, and bumps the matrix version.
- **AC-19**: `GET /vrms/knowledge/categories` needs `config.read`, so the repair form's System list works with the knowledge module off; `KnowledgeCategoriesService.list` keeps its `(query, ability)` signature and still shows inactive categories only to callers who can edit them, which is now `lookups.manage`. An issue already linked keeps returning its entry name in the ticket detail while the module is off (AC-15), on purpose. `POST` and `PATCH /vrms/knowledge/categories` need `lookups.manage`. The `knowledge.edit` description no longer mentions categories.
- **AC-20**: With every setting at its default, every role sees and can do what it did before this feature, except: issue categories moved into Settings, and the Users page's read only matrix section (spec 0011, AC-25) is replaced by the Roles and permissions section in Settings.

*The Settings hub*
- **AC-21**: `/settings` holds five sections, each at its own URL and shown only with its key: Modules (`/settings/modules`, `settings.manage`), Thresholds (`/settings/thresholds`, `settings.manage`), Roles and permissions (`/settings/roles`, `permissions.manage`), Lookup lists (`/settings/lookups`, `lookups.manage`) and Change history (`/settings/history`, `settings.manage`). A section URL without its key shows the 403 page. A Settings nav item shows when the caller holds any of the three keys. Desktop: a section list beside the content, `/settings` opening the first allowed section. Phone: `/settings` is the section list and each section opens full width with a back link.
- **AC-22**: Modules section: one row per module with label, description and an on or off switch. Flipping the switch opens a confirm dialog listing what it hides (`hides`), any modules that will turn off with it (AC-9), and a required reason (5 to 500 characters). Confirm saves at once; Cancel leaves the switch as it was.
- **AC-23**: Thresholds section: values grouped by catalog `group`. Each value shows label, description, a number input with its unit, the allowed range, the default, a Custom badge when it differs from the default, and Reset to default. Edits collect into a Save and Discard bar showing how many values changed, with an optional note. An invalid value blocks Save inline with the same rules as the server. When a group's module is off, the group shows "Knowledge base is off. These apply when it is turned back on." and stays editable.
- **AC-24**: Roles and permissions section: the spec 0011 matrix as an editable table (keys grouped, three role columns). Locked cells show a lock and can't be clicked; keys of an off module are marked "Module off" and stay editable (each key's `module` comes from `GET /vrms/permissions`, the on or off state from `modules` on `/me`). Edited cells are marked, and the bar's Review and save opens a dialog listing each role's gains and losses before anything is sent; on phones the table becomes one card per permission. The note is optional when rights are only added and required (5 to 500 characters, like a module switch) when any right is taken away. The server enforces it too: `PATCH /vrms/permissions` answers 400 "Taking a right away needs a reason of 5 to 500 characters." and writes nothing when a change turns an allowed cell off and the note is missing or too short. Turning on a cell, or turning off a cell that was already not allowed, needs no note, and a stale version still answers 409 first. Saved through `PATCH /vrms/permissions`.
- **AC-25**: Lookup lists section: issue categories, moved from `/knowledge-base/categories` with the same create, rename and deactivate actions. `/knowledge-base/categories` redirects to `/settings/lookups`.
- **AC-26**: Change history section: setting and permission changes merged newest first, a filter (All, Settings, Permissions), 20 per page with Load more, and no total count. Each row shows when, who (System for a null actor), what (the label, plus the role for a permission; a key gone from both catalogs reads `Removed setting (<key>)` or `Removed permission (<key>)`), before and after, and the note. A number shows with thousands separators and its setting's unit (`365 days → 1,095 days`, singular for 1: `1 repair`). A reset shows the default it went back to (`20 repairs → 3 repairs (default)`, `Off → On (default)`). A null permission side reads Added or Removed. A note keeps its line breaks and starts at two lines with Show more when it is over 160 characters or has a line break. Modules, Thresholds and Roles and permissions each show their last 5 changes with a link to the full history.
- **AC-27**: A save answered 409 (settings or matrix) reloads the section, drops the unsaved edits and shows the toast "Someone else saved settings. The latest values are loaded, please make your change again." Leaving a section with unsaved edits asks to discard them.
- **AC-28**: Loading, empty and error states use the design system's shared components. Every switch and input has a label, focus is visible, and the whole hub works by keyboard (WCAG AA).

*Close out*
- **AC-29**: `npm run seed` deletes every `app_settings` and `setting_changes` row and bumps `settings_state.version`, so a seeded database runs on catalog defaults.
- **AC-30**: Unit tests cover catalog validation, the save rules (types, ranges, notes, 409, dependencies) and module key removal; the route table test from spec 0011 stays green with the new routes. Lint, typecheck and build pass in backend-vrms and web-vrms, and `python -m py_compile *.py` passes in analytics-ai.

*Recent changes by key (update, 2026-10-30)*
- **AC-31**: `GET /vrms/settings/changes` takes an optional `keys`: one comma separated string of 1 to 50 distinct keys, each 1 to 60 characters of `a` to `z`, `0` to `9`, `_` and `.` (every catalog key fits today). It keeps only rows whose `key` is in the list, in the same query, after the `kind` filter and before the limit, so paging and `nextCursor` work as before. A key need not be in a catalog (a removed key's history stays readable). Parsing: split on commas with no trimming; duplicates are dropped and the cap counts distinct keys; an empty `keys`, an empty piece (`a,,b`, a trailing comma), the parameter given twice (`keys=a&keys=b`), a 51st distinct key or a key breaking the pattern is a 400 naming the rule. `keys` filters both kinds; the `permissions.manage` rule still runs first, so without it no permission row comes back whatever `keys` holds. The cursor is not tied to the filter, so a client sends the same `kind` and `keys` on every page. The Modules section asks for its module keys and Thresholds for its value keys, each with `kind=setting&limit=5`, so the section shows its own 5 newest changes however many other changes came after them. When the answer is empty, or the section has no keys (then no request is made), it says "No changes yet." The Roles and permissions section keeps reading spec 0011's `/vrms/permissions/changes`.

## Decision

**Chosen option**: Option 1: a code catalog plus a key and value table holding only the changed values, with module switches as settings that remove permission keys.

Settings follow the permission matrix pattern of spec 0011 (catalog in code, stored values, a version row read on every checked request, a change table kept forever), and a switched off module works by removing its keys from every ability, so the existing guards, `<Can>` and nav do the hiding and refusing.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`) · `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-cli/`) · `fastapi` (`fastapi/fastapi`, `.claude/skills/fastapi/`) · `react-hook-form` (`.claude/skills/react-hook-form/`) · `shadcn` (`.claude/skills/shadcn/`) · `vercel-react-best-practices` (`.claude/skills/vercel-react-best-practices/`)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Settings catalog** (AC-1):

| Key | Kind | Group | Type | Default | Range | Unit | Notes |
|---|---|---|---|---|---|---|---|
| `module.ai` | module | Modules | boolean | `true` | | | hides: AI diagnosis panel on repair tickets, AI feedback, issue embedding |
| `module.analytics` | module | Modules | boolean | `true` | | | hides: Analytics page and its charts, the analytics data refresh |
| `module.knowledge` | module | Modules | boolean | `true` | | | hides: Knowledge base pages, suggestions, the repair form's known fix picker and auto fill, the "What fixed it" step |
| `knowledge.min_samples` | value | Knowledge base | int | 3 | 1 to 20 | repairs | Repairs needed before the typical time and cost replace the estimate (spec 0007, AC-13) |
| `knowledge.repeat_threshold` | value | Knowledge base | int | 2 | 2 to 10 | repairs | Linked repairs on one vehicle that make it "keeps coming back" (spec 0007, AC-14) |
| `knowledge.repeat_window_days` | value | Knowledge base | int | 365 | 30 to 1095 | days | Window for the repeat count |
| `knowledge.group_min_size` | value | Knowledge base | int | 3 | 2 to 20 | issues | Smallest group of similar unlinked issues shown as a suggestion (spec 0007, AC-32) |

Every module defaults to on, and the Python service relies on that (AC-17). The knowledge values belong to `module.knowledge` for the hub's "module is off" note (AC-23). Later features add their own entries (features 42 and 43: durations and thresholds; feature 3: an AI catch up window).

**Data model sketch** (one migration, after the baseline):

| Entity | Field | Type | Notes |
|---|---|---|---|
| `AppSetting` (`app_settings`) | `key` PK | varchar(60) | a catalog key |
| | `value` | Json | a number or a boolean, checked against the catalog on save |
| | `updatedAt` | timestamptz(3) | `@updatedAt` |
| | `updatedByUserId` | uuid, nullable | welinc-auth user id, no foreign key |
| `SettingsState` (`settings_state`) | `id` PK | smallint | always 1, kept by a check constraint (raw SQL in the migration, like `permission_matrix`); the migration inserts the row |
| | `version` | int, default 1 | bumped once per save that changed something |
| | `updatedAt` | timestamptz(3) | |
| `SettingChange` (`setting_changes`) | `id` PK | uuid | one row per changed key, kept forever, never updated |
| | `key` | varchar(60) | index |
| | `before`, `after` | Json | the effective value on each side, never null |
| | `action` | varchar(10) | `SET` or `RESET` |
| | `actorUserId` | uuid, nullable | null is System |
| | `actorName`, `actorEmail` | varchar(100), varchar(255), nullable | |
| | `note` | text, nullable | |
| | `createdAt` | timestamptz(3) | index `(createdAt desc, id desc)` for paging |

No foreign keys: keys are code constants, like `role_permissions`. The same migration inserts the `lookups.manage` rows copied from `knowledge.edit`, with their `PermissionChange` rows and the matrix version bump (AC-18).

**State transitions**: a module is on or off. Off to on is refused while a required module is off (AC-9). On to off cascades to the modules that require it.

**API surface** (backend-vrms unless noted):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/permissions/me` | GET | | `keys` (module keys removed), `version`, `modules: { ai, analytics, knowledge }` | `@Authenticated` | 503 cold replica |
| `/vrms/settings` | GET | | `version`, `settings[]`: `key, kind, group, label, description, type, unit, min, max, default, value, isDefault, hides, requires, module, updatedAt, updatedBy { name, email } \| null` | `settings.manage` | 403 |
| `/vrms/settings` | PATCH | `version: int` (req), `changes: { key, value?: number \| boolean, reset?: true }[]` (1 to 50), `note?: string` (≤500; 5 to 500 when a module changes) | the same body as GET, after the save | `settings.manage` | 400 rule (AC-6, AC-8, AC-9), 409 stale |
| `/vrms/settings/changes` | GET | `limit?` (1 to 100, default 20), `cursor?`, `kind?` (`all` \| `setting` \| `permission`), `keys?` (comma separated, 1 to 50 keys of `[a-z0-9_.]{1,60}`, AC-31) | `data[]`: `id, kind, key, label, role?, before, after, action, actor { name, email } \| null, note, createdAt`; `nextCursor` (the same envelope as spec 0011's changes) | `settings.manage`; permission rows only when the caller also holds `permissions.manage` (else `kind=permission` returns an empty list) | 400 bad cursor, 400 bad `keys` |
| `/vrms/permissions` | GET | unchanged | adds `module` (or null) to each key | `permissions.manage` | |
| `/vrms/permissions` | PATCH | unchanged (spec 0011) | | `permissions.manage` | 400, 409 |
| `/vrms/knowledge/categories` | GET | unchanged | unchanged | `config.read` (was `knowledge.view`) | |
| `/vrms/knowledge/categories`, `/:id` | POST, PATCH | unchanged | unchanged | `lookups.manage` (was `knowledge.edit`) | |
| `/vrms/repairs/:id/issues/:issueId/knowledge` | PATCH | unchanged | unchanged | `ticket.work` or `ticket.administer` | 403 `MODULE_DISABLED` when knowledge is off |
| analytics-ai `/ai/*`, `/analytics/*` | any | unchanged | unchanged | none (no JWT, as today) | 403 flat `{ detail, code: 'MODULE_DISABLED' }` when off |

The changes list merges `setting_changes` and `permission_changes` with one `UNION ALL` that projects the same columns from both (`kind` as a literal, `role` null for settings, permission `before` and `after` cast to `jsonb`), filters by `kind` and then by `keys` (`AND c.key IN (...)` through `Prisma.join`, only when `keys` is given) before the limit, and orders by `(createdAt desc, id desc)`; the cursor encodes that pair. Labels are added in code after the query. No new index: `setting_changes(key)` already has one, and with `kind=setting` the permission branch matches nothing. Postgres sorts the matching rows for the `ORDER BY`, which is fine at this log size; a `(key, created_at desc, id desc)` index waits until a measured need. Validation order: the DTO checks `limit`, `kind` and `keys` (a `@Transform` splits `keys` before the validators, so the 400 names the rule) before the service decodes the cursor, so a request with a bad `keys` and a bad cursor reports the `keys` 400.

**Implementation contract** (settled here so the build invents nothing):
- **Freshness**: `ensureFresh` reads both versions with one `$queryRaw`: `SELECT (SELECT version FROM permission_matrix WHERE id = 1) AS matrix, (SELECT version FROM settings_state WHERE id = 1) AS settings`. `SettingsService` owns the settings cache and version and depends on nothing but `PrismaService`; `PermissionsService` depends on it (no cycle). `SettingsService.get` is synchronous, reading the cache the guard keeps fresh. A settings reload clears `keyCache` too. Both loads stay single flight. Readiness (the 503 on a cold replica) covers settings as well as the matrix.
- **Saving**: inside one transaction, `SELECT version FROM settings_state WHERE id = 1 FOR UPDATE`, compare it with the body's version (409 on mismatch), read the stored rows for the touched keys under that lock, and compute `before` from those rows and the catalog, never from a replica's cache.
- **Validation order**: body shape (DTO, 400), then version (409), then rules (400: catalog type and range, notes, dependencies). A note is required only when a module's effective value changes. Cascaded modules don't count toward the 50 change limit. Dependency rules are checked on the state after the save, so one save may turn A off and B on only if B doesn't require A. A reset of a key with no stored row is a no op; a reset of a key whose stored row is invalid deletes the row and logs `RESET`.
- **Invalid stored values**: ignored for the default, with a warning logged once per key per settings version (never on every request).
- **Migration**: one folder after the baseline creates the three tables, the `settings_state` row and its check constraint, then copies the grant: `INSERT INTO role_permissions (role, permission, allowed, updated_at) SELECT role, 'lookups.manage', allowed, now() FROM role_permissions WHERE permission = 'knowledge.edit' ON CONFLICT DO NOTHING`, a `permission_changes` row per inserted row, and one matrix version bump only when rows were inserted. `settings.manage` and `ai.use` rows come from the existing startup backfill (System, no note, its own version bump). `npm run seed` runs after migrations and keeps the matrix reset it does today, which writes `lookups.manage` from the catalog defaults.
- **Rolling deploy**: replicas on the old build ignore settings until they are replaced; a module turned off during a deploy is enforced only on new replicas. Accepted.

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Any knowledge read | the four thresholds | `SettingsService.get(key)`: the `app_settings` row, else the catalog default |
| Any checked request | whether the cache is stale | `permission_matrix.version` and `settings_state.version`, one query in `ensureFresh` |
| Guard, `/me` | a user's keys | matrix grants (spec 0011) minus keys whose catalog `module` is off |
| Guard 403 | `module` in the body | the route key's catalog `module` |
| `/me` | `modules` | effective `module.*` values from `SettingsService` |
| PATCH | `before` in each log row | the stored row (else the catalog default) read under the `FOR UPDATE` lock in the save transaction |
| PATCH | actor | `req.user` (`sub`, name, email), as the matrix does |
| PATCH | dependents to turn off | catalog `requires`, walked transitively |
| GET settings | `isDefault` | no stored row (or an invalid one) |
| GET settings | `updatedAt`, `updatedBy` | the latest `SettingChange` for that key (its `createdAt`, actor name and email); null when the key never changed |
| Analytics page | whether to show the AI stats block | `modules.ai` from `/me` |
| Roles section | each key's module | `module` on each key from `GET /vrms/permissions` |
| Module confirm dialog | what it hides, dependents | catalog `hides` and `requires`, from GET settings |
| Thresholds | range, unit, default | catalog `min`, `max`, `unit`, `default`, from GET settings |
| Thresholds "module is off" note | which module a group belongs to | catalog `module` on the value entries |
| Change history | label for a key | settings catalog label; permission catalog label; the raw key when it left both catalogs, which the web shows as `Removed setting (<key>)` or `Removed permission (<key>)` (it reads a label equal to the key as removed) |
| Change history | unit beside a number | `unit` of that key in `GET /vrms/settings` (the History section loads it; a row shows no unit when that load fails) |
| Change history | the value after a reset | the row's `after`, which holds the effective default the key went back to |
| Modules, Thresholds recent changes | which keys to ask for | the section's own catalog keys from `GET /vrms/settings` (`kind` `module` or `value`), sorted and joined with commas by `getSettingChanges` (`keys?: string[]` in, one string out; axios would otherwise send `keys[]=`) |
| Modules, Thresholds recent changes | when to load again | the load key `recent:<settings version>:<sorted keys>`; the section passes `data.version` from its `useSettings`, which moves after its own save (`replace`) and after a reload |
| Modules, Thresholds recent changes | how many rows | `limit=RECENT_COUNT` (5) on the request; no filtering or slicing in the browser |
| Change history | role on a permission row | `permission_changes.role` mapped through `ROLE_LABELS` |
| Python `/ai`, `/analytics` | on or off | `app_settings.value` for `module.ai` or `module.analytics`, 5 second cache; no row means on |
| Repair detail | plain text knowledge name when off | the issue's existing `knowledgeEntry` include (`issueInclude`) |

**Key invariants**:
- The catalog is the only place a setting's type, default and range live; the database holds values only.
- A stored value always passes its catalog rules; the service never writes one that fails them. A stored value that fails later rules (a range narrowed in code) is ignored, the default applies, and a warning is logged.
- `settings_state` has exactly one row, id 1.
- Every effective value change writes exactly one `SettingChange`, in the same transaction as the value and the version bump.
- A module key change always carries a note.
- A module that is off removes its keys everywhere; matrix rows never change because of a module.
- No module can be on while a module it requires is off.
- Issue categories never depend on the knowledge module.

**Security model**:
- `settings.manage` reads and changes settings and modules and reads the change history; Admin always holds it (locked), so no matrix edit can lock everyone out of Settings.
- `permissions.manage` stays the only key that changes the matrix; the hub's Roles section uses spec 0011's endpoints unchanged.
- `lookups.manage` edits lookup lists; reading them stays `config.read`.
- Permission change rows in the history show only to callers holding `permissions.manage`.
- The Python service still checks no JWT (feature 3 retires it); the module switch limits what it does, not who can call it.
- `ai.use` is enforced only in the web app (it hides the AI panel), because the AI routes live in the Python service, which checks no token. Its catalog description says so ("Shows the AI panel; the AI service itself is not yet locked by role"). Feature 3 makes it a real server check.
- No regulated data. Every change is audited (Done when).

**Configuration required**: none. No new environment variables; the Python service already has `VRMS_DB_URL`.

**Critical test scenarios**:
- Happy path: Admin sets `knowledge.repeat_threshold` to 3 with a note; the next request on a second replica uses 3; history shows the change; Reset to default removes the row and logs `RESET`. Verifies **AC-3**, **AC-4**, **AC-5**, **AC-23**, **AC-26**.
- Module off: Admin turns Knowledge base off with a reason; a Mechanic's next `GET /vrms/knowledge/entries` gets 403 `MODULE_DISABLED`, the nav item is gone after focus, the repair form's System list still loads, and moving a ticket to For verification needs no resolution. Verifies **AC-10**, **AC-11**, **AC-12**, **AC-15**, **AC-19**.
- AI off: creating a ticket makes no embed call, `/ai/diagnose` answers 403, and the next sync logs that embedding was skipped. Verifies **AC-13**, **AC-17**.
- Failure: two Admins load Thresholds; the second save gets 409 and the hub reloads with the toast. Verifies **AC-7**, **AC-27**.
- Validation: `knowledge.min_samples` set to 0, 2.5 or `true` each get 400 naming the rule; a module change with no note gets 400. Verifies **AC-6**, **AC-8**.
- Dependencies (test catalog): turning off a required module turns its dependent off too, with two log rows. Verifies **AC-9**.
- Auth: a Chief Mechanic without `settings.manage` gets 403 on `GET /vrms/settings` and sees no Modules or Thresholds sections, but sees Lookup lists through `lookups.manage`. Verifies **AC-18**, **AC-21**.
- Recent changes by key: turn AI off, then save 101 threshold changes; Modules still lists the AI change, and `keys=module.ai&kind=setting&limit=5` returns it; page 2 of a `keys` query holds only matching rows. `keys=` (empty), `keys=a,,b`, `keys=a,` (trailing comma), `keys=a&keys=b`, 51 distinct keys, a 61 character key and `keys=Module.AI` each get 400; `keys=module.ai,module.ai` counts once and returns the same rows as one. `kind=permission&keys=ticket.view` without `permissions.manage` returns an empty list. A catalog unit test keeps each section (module keys, value keys) at 50 keys or fewer. Verifies **AC-31**.

## Build plan

Tracer Bullet: one threshold end to end first, then modules through every layer, then the remaining sections.

1. **Thin thread, one threshold end to end**: the migration (all three tables, the `settings_state` row and check constraint, the `settings.manage`, `lookups.manage` and `ai.use` keys with the `lookups.manage` copy); the settings catalog with its 7 entries; `SettingsService` with `get`; the combined version read in `ensureFresh`; `GET` and `PATCH /vrms/settings` with validation, notes, 409 and the change log; the knowledge helpers read the four values from the service, with `KNOWLEDGE_TUNING` for the rest; web `/settings` shell with the section list, the Settings nav item and the Thresholds section with its Save and Discard bar and 409 handling. Satisfies **AC-1** to **AC-7**, **AC-18**, **AC-21**, **AC-23**, **AC-27**.
2. **Modules on the server**: module tags in the permission catalog, key removal in `keysFor` and the ability (the key cache keyed by both versions), the `MODULE_DISABLED` 403 in the guard, `modules` on `/me`, the dependency rules (the first thing to cut if time runs short, since no module needs them yet), `autoEmbedIssues` skipped, link refused and the "What fixed it" rule skipped when knowledge is off. Satisfies **AC-8** to **AC-11**, **AC-13** (backend part), **AC-15** (server part), **AC-16**.
3. **Modules in the web app**: Modules section with the confirm dialog, `modules` in the permissions context, the AI panel on `ai.use`, the analytics and knowledge screens hidden, the module off page, linked entries as plain text. Satisfies **AC-12**, **AC-13** (panel), **AC-14** (web), **AC-15** (web), **AC-22**.
4. **Python service** (welinc-backend-vrms-analytics-ai): the cached flag read, the router level 403 on `/ai/*` and `/analytics/*`, the sync steps per switch, and `sys.exit(1)` replaced so errors no longer kill the sync thread. Satisfies **AC-13**, **AC-14**, **AC-17**.
5. **Roles and lookup lists**: editable matrix section, the read only Users page section removed, issue categories moved with the redirect, the category routes on `config.read` and `lookups.manage`. Satisfies **AC-19**, **AC-20**, **AC-24**, **AC-25**.
6. **Change history**: `GET /vrms/settings/changes` with the merged cursor, the History section with filter and Load more, the last 5 changes on each section. Satisfies **AC-26**.
7. **Close out**: seed reset, `settings:prune`, unit tests and the route table test, empty, loading and error states and the keyboard pass, then lint, typecheck, build and `py_compile`. Satisfies **AC-28** to **AC-30**.
8. **Offered polish (ask first)**: one `impeccable` critique of the hub against `design.md`, applying only the findings you accept. Satisfies **AC-28**.
9. **Recent changes by key (update)**, one thin slice through both repos: backend-vrms adds `keys` to `ListChangesQueryDto` (split on commas, then the count and pattern checks) and the `IN` filter in `SettingsAdminService.changes`, with unit tests for the filter, paging with `keys`, each 400, and a catalog test that module keys and value keys each stay at 50 or fewer; web-vrms gives `getSettingChanges` a `keys?: string[]` that it sorts and joins with commas, and `RecentChanges` asks for `kind=setting&limit=RECENT_COUNT` with its keys (load key per Value sourcing) instead of fetching 100 and filtering, skips the request when it has no keys, and says "No changes yet." when empty. The dev only `?data=` datasets (`src/features/dev-ui/worst-case/`) apply `keys`, then `kind`, then `limit`, without validating, and the 1,284 row set gains a module change more than 100 rows back so the old bug can be seen. The change row rendering in AC-26 is already built (break-ui, 2026-10-30). Satisfies **AC-26**, **AC-31**.

## Consequences

**Positive**:
- Features 40, 42 and 43 get a home: a new list or tunable is a catalog line plus, for a list, one section.
- Turning AI off ends the Python sync's embedding loop, which today re-embeds every issue every 30 seconds.
- One audit trail for every admin change, settings and permissions together.
- Reuses the matrix pattern the team already built, so nothing new to learn or operate.

**Negative / tradeoffs**:
- Module checks now ride on permission keys: a new route in a module must use a key tagged with that module, or the switch won't cover it. The route table test catches untagged routes only if a reviewer checks the catalog.
- Values are Json in Postgres, so the database can't enforce types or ranges; the service is the only gate, and a hand edit in the database can store nonsense (ignored with a warning).
- The Python service now reads a VRMS table, a small new coupling across repos that feature 3 must remember to remove.
- Moving issue categories and the matrix screen changes two URLs people may have bookmarked (one redirects; the Users page section just disappears).
- Module dependency support is built and tested with no real dependency yet.
- During a rolling deploy, old replicas don't enforce module switches until they are replaced.
- `ai.use` hides the AI panel but doesn't lock the Python AI routes until feature 3.

**Neutral**:
- `KNOWLEDGE_SETTINGS` and its stale "scope feature 46" comment go away; `knowledge.tuning.ts` keeps the technical constants.
- `knowledge.edit` stops covering categories; the migration copies its grants to `lookups.manage`, so nobody loses access.
- Spec 0011's AC-25 (read only matrix on the Users page) is replaced by AC-24 here.
- Change history shows no total count (AC-26). Load more is enough while the log is small; a total would need a count over the merged query on every page. Revisit if people page far back.

## Follow-up

- [ ] Feature 3 (analytics and AI boundary): switch to incremental embedding (embed each issue once on save and store the vector, never re-embed in a loop), then add an `ai.embed_catchup_days` setting to this catalog so turning AI back on embeds only the missing issues from that window. Declare `module.ai` `requires: ['module.knowledge']` once AI is grounded on the knowledge base, and remove the Python service's `app_settings` read when it retires.
- [ ] Feature 40 (lookup lists): add parts, reasons and locations to the Lookup lists section on `lookups.manage`. Spec 0016 already added the generic `LookupValue` table for this: add a list to the code catalog (`lookup-lists.ts`) and it appears.
- [x] Spec 0016 widened the Lookup lists section (AC-25) with two generic lists beside Issue categories, `vehicle_type` (Vehicle types) and `corporation` (Corporations), behind `lookups.manage`. Their changes join Change history (AC-26) as another source with the actions Added, Renamed, Deactivated and Reactivated.
- [x] Spec 0016 added a Vehicles section at `/settings/vehicles` (a type per truck), shown only with `vehicle.manage`, so the hub now has six sections where AC-21 says five.
- [x] Spec 0016 added the threshold `tickets.odometer_jump_warn_km` (default 20000, min 1000, max 200000, unit km) to Thresholds (AC-23). A new ticket reading above the truck's last one by more than this needs confirming.
- [ ] Features 42 and 43: add their durations and stuck or stale thresholds as catalog entries, not constants.
- [x] Spec 0007: tick its follow-up "the future configurable settings spec replaces `KNOWLEDGE_SETTINGS`" when this ships.
- [x] Spec 0011: note that AC-25 is replaced by this spec's AC-24, and tick its feature 52 follow-up when this ships.
- [x] `/sync` after the build: backend-vrms `AGENTS.md` (settings catalog and service, the combined version read, module tags on keys), analytics-ai `AGENTS.md` (it reads `app_settings`), web-vrms `AGENTS.md` (the Settings hub and `modules`, and the dev only `?data=` datasets for the hub).
- [x] `PATCH /vrms/permissions` refuses a removal without a reason, so the rule holds for every caller and not only the web app (backend-vrms, `PermissionMatrixService.update`, with tests).
