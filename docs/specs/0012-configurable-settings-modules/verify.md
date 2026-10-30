# Verify: configurable settings and modules · spec 0012 · drafted 2026-10-30
_Steps derived from spec 0012 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## UI / manual
- [x] Sign in as Admin → a Settings nav item; `/settings` on desktop opens Modules beside a list of five sections; on a phone width `/settings` shows the list and each section opens full width with a back link → AC-21
- [x] Thresholds: change repeat threshold to 3 → Save bar says 1 change; Save → Custom badge shows; Reset to default then Save → badge gone → AC-5, AC-23
- [x] Thresholds: type 0 in Min samples → inline error, Save blocked → AC-6, AC-23
- [x] Open Thresholds in two tabs, save in one, then save in the other → toast "Someone else saved settings…", edits dropped, values reloaded → AC-7, AC-27
- [x] Edit a value and click another section → asked to discard → AC-27
- [x] Modules: switch Knowledge base off → dialog lists what it hides and needs a reason; Cancel leaves it on; confirm with a reason → saved → AC-22, AC-8
- [x] With Knowledge base off, as Mechanic (focus the tab) → no Knowledge base nav item; `/knowledge-base` by URL shows "This module is turned off by your Admin"; repair form System list still loads; no known fix picker → AC-12, AC-15, AC-19
- [x] With Knowledge base off, move an In progress ticket to For verification → no "What fixed it" step, the move succeeds; a ticket with an already linked issue shows the entry name as plain text → AC-15
- [x] Thresholds with Knowledge base off → the knowledge group shows the "is off" note and stays editable → AC-23
- [x] Turn AI off → repair detail has no AI panel; turn Analytics off → no Analytics nav item, `/analytics` shows the module off page, never sample charts → AC-13, AC-14
- [x] Turn every module back on → everything is back with its data → AC-16
- [x] Roles and permissions: toggle a cell, Save with a note → saved; locked cells can't be clicked; with Knowledge base off its keys show "Module off" → AC-24
- [x] Users page → no read only matrix section; `/knowledge-base/categories` redirects to `/settings/lookups`, where categories can be created and renamed → AC-20, AC-25
- [x] Change history: settings and permission rows merged newest first; filter Settings and Permissions; Load more after 20; System shows for a null actor; each section shows its last 5 → AC-26
- [x] Sign in as Chief Mechanic → Settings shows only Lookup lists; `/settings/modules` by URL shows the 403 page → AC-18, AC-21
- [x] Keyboard only through the hub: every switch, input and dialog reachable, focus visible; loading and error states use the shared components → AC-28

## Commands
- [x] Fresh migrate → `settings_state` has one row (id 1, version 1); `app_settings` empty; `lookups.manage` rows match each role's `knowledge.edit`, with `PermissionChange` rows noted "Copied from knowledge.edit (spec 0012)" → AC-2, AC-18
- [x] `GET /vrms/settings` as Admin → 7 entries, all `isDefault: true` → AC-1
- [x] PATCH with an unknown key, a duplicate key, `2.5` for an int, `true` for an int, 0 for min samples, both `value` and `reset`, 51 changes → each 400, nothing written → AC-6
- [x] PATCH a module change without a note → 400; with a 4 character note → 400; with 5 → 200 → AC-8
- [x] PATCH the current value → 200, version unchanged, no log row → AC-5
- [x] Run two backends; PATCH on one, then call the other → it uses the new value on its first request → AC-4
- [x] Stop the DB on a warm backend → requests keep the last settings and a warning is logged; restart a cold backend with the DB down → 503 → AC-4
- [x] Knowledge off: `GET /vrms/knowledge/entries` as Admin and as Mechanic → 403 `MODULE_DISABLED` with `module: 'knowledge'`; `PATCH /vrms/repairs/:id/issues/:issueId/knowledge` → 403 `MODULE_DISABLED`; `GET /vrms/knowledge/categories` → 200 → AC-11, AC-15, AC-19
- [x] `GET /vrms/permissions/me` with knowledge off → no `knowledge.*` keys, `modules.knowledge: false`; `role_permissions` rows unchanged → AC-10, AC-12
- [x] AI off: create a ticket → no `/ai/embed-issue` call in the logs; `POST /ai/diagnose` → 403 `MODULE_DISABLED`; next sync logs the embedding step skipped; `/health` → 200 → AC-13, AC-14, AC-17
- [x] Analytics off: `GET /analytics/summary` → 403 flat `{ detail, code }`; AI and Analytics both off → the sync does nothing; AI off only → sync logs steps 1, 2 and 4, the old vector table is unchanged → AC-14
- [x] AI off, Analytics on → the Analytics page loads without its AI stats block → AC-13
- [x] Stop the VRMS database during a sync → the sync logs the error and runs again on the next cycle (thread still alive) → AC-17
- [x] Turn Knowledge base off with keys unchanged for a role (e.g. a role without knowledge keys) → `/me` modules update in the tab after focus → AC-12
- [x] Two concurrent PATCHes with the same version → one 200, one 409; the log shows one change → AC-7
- [x] Delete the `module.ai` row → Python treats AI as on within 5 seconds → AC-17
- [x] Insert an `app_settings` row with an unknown key → ignored; `npm run settings:prune` deletes it and logs a `RESET` by System → AC-2
- [x] Insert `knowledge.min_samples` = 0 by hand and bump the version → the default 3 applies and a warning is logged → AC-3
- [x] `npm run seed` → `app_settings` and `setting_changes` empty, version bumped → AC-29
- [x] `GET /vrms/settings/changes?kind=permission` as a caller without `permissions.manage` → no permission rows → AC-26
- [x] Unit tests for the catalog, save rules, dependencies and key removal pass; route table test green; lint, typecheck and build in backend-vrms and web-vrms; `python -m py_compile *.py` in analytics-ai → AC-9, AC-30

## Milestones 1 and 2 · added by /develop 2026-10-30
_Until milestone 3 lands, the hub has two sections (Modules, Thresholds), its nav item follows `settings.manage` only, and a Chief Mechanic sees no Settings item. The five section and Chief Mechanic steps above wait for milestone 3._

### Already checked during the build (local Docker stack, API only)
- [x] Migration applied: three tables live, `settings_state_one_row` constraint, `lookups.manage` copied with three System rows; the startup backfill added `settings.manage` and `ai.use` → AC-2, AC-18
- [x] Validation: 0, 2.5 and `true` for min samples, an unknown key, value plus reset, a module change with no note → each 400 naming the key and rule; a stale version → 409 with `version` → AC-6, AC-7, AC-8
- [x] Set repeat threshold to 3 with a note → version bumps, `updatedBy` set, one SET row; the same value again → no bump; reset → row deleted, RESET row → AC-5
- [x] Knowledge off → its three keys leave `/me`, `modules.knowledge` false; entries → 403 `MODULE_DISABLED`; categories → 200; knowledge link → 403 `MODULE_DISABLED` → AC-10, AC-11, AC-15, AC-19
- [x] AI off → `/ai/stats`, `/ai/logs`, `/ai/diagnose` → flat 403 `{ detail, code, module }`; `/analytics/summary` and `/health` → 200; next sync ran steps 1, 2 and 4 → AC-13, AC-14, AC-17
- [x] Analytics off → `/analytics/summary` → 403; `analytics.view` leaves `/me`; next sync ran steps 1 and 3 → AC-14
- [x] Backend: 436 Jest tests (new: save rules, dependencies on a test catalog, key removal, module before role in the guard); web: 94 Vitest tests; lint, typecheck and build green in both; `py_compile` green → AC-9, AC-30 (partial)

### Still to run (UI, not driven in this build)
- [x] `/settings` on desktop opens Modules; on a phone width it shows the list, each section full width with "All settings" → AC-21
- [x] Turn a module off in one tab → that tab's nav updates at once (no wait for focus); the switch only moves after Confirm → AC-12, AC-22
- [x] AI off → Analytics page has no AI Insights tab, the other tabs show live data, the CSV export has no AI section → AC-13
- [x] Knowledge off → a ticket's "Suggest an entry" and "Link a known fix" are gone; "Add issue" on the repair form focuses Vehicle system → AC-15

### Value sourcing
- [x] Knowledge read: set min samples to 1 → an entry with one closed repair now shows a typical time; reset → it falls back to the estimate → Value sourcing (knowledge thresholds)
- [x] Repeat window: set it to 30 days → an entry's repeat vehicles drop the ones whose linked repairs are older than 30 days → Value sourcing (knowledge thresholds)
- [x] Group min size: set it to 2 → suggestions list pairs of similar unlinked issues → Value sourcing (knowledge thresholds)
- [x] `GET /vrms/settings` `updatedBy` after an Admin save shows that Admin's name and email; after a reset it still shows the last change → Value sourcing (`updatedAt`, `updatedBy`)
- [x] Python lag: turn AI off and call `/ai/stats` at once → may answer 200 for up to 5 seconds, then 403 → Value sourcing (Python 5 second cache)

## Update 2026-10-30 · Recent changes by key (AC-31) and change row reading (AC-26)
- [x] Turn AI off with a reason, then save 101 threshold changes → Modules' Recent changes still lists the AI change; Thresholds lists its own 5 newest → AC-31
- [x] `GET /vrms/settings/changes?kind=setting&keys=module.ai&limit=5` → only `module.ai` rows; with a `cursor` from page one → the next rows for that key only → AC-31
- [x] `keys=` (empty), `keys=a,,b`, a trailing comma, `keys=a&keys=b`, 51 distinct keys, `keys=Module.AI` and a 61 character key → each 400 naming the rule; `keys=module.ai,module.ai` → same rows as one key → AC-31
- [x] `kind=permission&keys=ticket.view` as a caller without `permissions.manage` → empty list → AC-31
- [x] `?data=huge` in the browser → Modules' Recent changes shows the module change that sits more than 100 rows back → AC-31
- [x] A section with no changes for its keys → "No changes yet." → AC-31
- [x] History rows: `365 days → 1,095 days`; a reset reads `20 repairs → 3 repairs (default)`; a key gone from the catalog reads `Removed permission (<key>) for <role>`; a 500 character note starts at two lines with Show more → AC-26
- [x] Unit tests for the `keys` parsing, the filter and each 400 pass; lint, typecheck and build in backend-vrms and web-vrms → AC-30, AC-31

## Update 2026-10-30 · Review step for permission changes (added after the impeccable polish, beyond AC-24)
- [x] Roles: untick an allowed right, choose Review and save → dialog "Save 1 permission change?" lists the role and "Loses <right>", the field reads "Reason *", Save changes is red → AC-24
- [x] Same dialog, Save changes with no reason → stays open with "Give a reason of at least 5 characters." → AC-8
- [x] Back to the matrix → the edit and the "1 permission changed" bar are still there; Esc also closes the dialog; Discard clears the bar → AC-27
- [x] Roles: tick a right that was off, Review and save → "Gains <right>", the field reads "Note (optional)", Save changes is the normal navy → AC-24
- [x] Unit tests for `reviewGrants` and `removesAny` pass; lint and typecheck in web-vrms → AC-30
- [x] Roles: save a removal with a reason → history row shows the change with the reason as "Note:" (run 2026-10-30 on "Edit lookup lists" for Chief Mechanic, then put back; the history shows "Allowed → Not allowed" with the note). Not run: a Chief Mechanic session making a request after the removal → AC-24, AC-26
- [x] API: `PATCH /vrms/permissions` with a removal and no `note` answers 400 "Taking a right away needs a reason of 5 to 500 characters." and the matrix version does not change; an addition with no note saves → AC-24
