# Foundations

What is already built (enrolled for context) and the ground every slice stands on. Back to [index](index.md).

## Already built

These predate the workflow. `/develop` and `/sync` leave them alone; planned features below replace or extend parts of them.

### A. Login, OTP and password reset · existing
Email and password login, mechanic OTP, forgot and reset password, profile and profile picture. Since spec 0009, `welinc-auth` owns login, OTP and users; backend-vrms only checks tokens (`src/auth/account-check.ts`). code in `welinc-auth/src/auth/`, `welinc-web-vrms/src/features/auth/`

### B. User management · existing
Admin lists, creates, edits, deactivates, unlocks and resets users. The users live in `welinc-auth`; backend-vrms keeps a synced `Mechanic` roster. code in `welinc-auth/src/auth/`, `welinc-backend-vrms/src/modules/vrms/mechanic-roster.service.ts`, `welinc-web-vrms/src/features/user-management/`

### C. Repair tickets · existing
Create, list, detail, status change (statuses since spec 0010: `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `ON_HOLD`, `FOR_VERIFICATION`, `OUTSOURCED`, `PENDING_APPROVAL`, `CLOSED`, `CANCELLED`; feature 16 builds the transitions), cost encoding, unlock a closed ticket. The form's vehicle system and root cause options are hardcoded (`lib/mockConfig`). code in `welinc-backend-vrms/src/modules/vrms/`, `welinc-web-vrms/src/features/repair/`

### D. Repair history · existing
Closed tickets with filters. code in `welinc-backend-vrms/src/modules/vrms/` (`GET history`), `welinc-web-vrms/src/features/repair/pages/HistoryPage.tsx`

### E. Audit log page · existing
Admin view of logged ticket actions. code in `welinc-web-vrms/src/features/audit-logs/`

### F. Dashboard · existing
Metrics computed from live repairs, history and audit logs. code in `welinc-web-vrms/src/features/dashboard/`

### G. AI diagnosis and knowledge base · existing
AI diagnose, feedback and issue embedding, knowledge articles, AI logs and stats; the repair detail shows an AI diagnostic panel. Since feature 3 it runs inside backend-vrms. code in `welinc-backend-vrms/src/modules/ai/`, `welinc-web-vrms/src/features/knowledge-base/`

### H. Analytics dashboards · existing
Cost trends, vehicle KPIs, issue frequency, status breakdown, garage costs, aging, velocity. Since feature 3 it runs inside backend-vrms. code in `welinc-backend-vrms/src/modules/analytics/`, `welinc-web-vrms/src/features/analytics/`

## Foundation

### 1. Coding standards & tooling · done
Capture each owned repo's real conventions so every later skill works from facts, not guesses.
**Done when:** web-vrms, backend-vrms, analytics-ai, auth and portal each have an `AGENTS.md` from `/audit`, and lint, typecheck and build run clean in each.
- [x] Capture conventions per repo: `/audit`
- Built (2026-10-25) on `feat/tooling` in web-vrms, backend-vrms, auth, portal and analytics-ai (committed, not pushed): all five have an `AGENTS.md`; lint and build are clean in the four Node repos (typecheck through build, plus `typecheck` in web-vrms). analytics-ai only compiles: it has no linter or tests and is planned to retire (feature 3), so none was added. PRs open against `development`: backend-vrms #10, auth #4, web-portal #3, web-vrms #15, analytics-ai #3. Marked done by you on 2026-10-25, with analytics-ai accepted as compile only. Node 24 is now installed on this machine. The portal login, wrong password message and 30 second inactivity sign out were run in a browser and passed.

### 2. Auth service boundary · done · GA
backend-vrms carries its own login, OTP and user endpoints while `welinc-auth` is the shared auth service. Decide which owns what before roles and OTP change.
**Done when:** one service owns login, OTP and users; the other only validates tokens; the portal and web-vrms log in through one path.
spec [0009](../specs/0009-auth-service-boundary/index.md)
- [x] Design it (spec): `/architect auth service boundary`
- Note (2026-10-25): from spec 0007's follow up. Adding a mechanic or chief mechanic on the Users page creates no VRMS `Mechanic` row (only seeds do), so new accounts can't be assigned tickets. Whichever service ends up owning users should create that row.
- Note (2026-10-27): spec 0009 decides welinc-auth owns everything; backend-vrms deletes its copy and user tables, checks each caller live, and syncs its `Mechanic` rows from welinc-auth. Crosses welinc-auth, backend-vrms and web-vrms; both databases need a reset.
- [x] Build it: `/develop auth service boundary`
  - [x] Thin thread: shared seed ids, VRMS auth copy and user tables removed, live account check with 503, mechanics and audit on the auth id (AC-1 to AC-8, AC-10, AC-22, AC-24 to AC-26)
  - [x] Mechanic list in step and one door: sync, just in time rows, repair form by mechanic id, fallback login removed (AC-9, AC-11 to AC-15, AC-27)
  - [x] welinc-auth hardening: no codes in logs, `PORTAL_URL`, reset and lock rules, admin safety guards (AC-16 to AC-19)
  - [x] Admin change record: `UserChange` table and its endpoint (AC-20, AC-21)
  - [x] Close out: lint, build, test and typecheck in all three repos (AC-23)
  - Note (2026-10-27): all code built on `feat/auth-service-boundary` in welinc-auth, backend-vrms and web-vrms (not committed). Lint, build and tests pass in all three. Thin thread and change record stay open until their migrations are applied: `20261027000000_auth_service_boundary` (backend-vrms) and `20261027000000_user_changes` (auth) are written but both databases still need the reset and reseed.
- code in `welinc-backend-vrms/src/auth/`, `welinc-backend-vrms/src/modules/vrms/mechanic-roster.service.ts`, `welinc-auth/src/auth/`, `welinc-web-vrms/src/lib/api/axios.ts`
- Note (2026-10-27): both databases reset and reseeded, migrations applied, committed on `feat/auth-service-boundary` (not pushed). Verify found one bug, fixed in web-vrms: the mechanic sync sent a `null` body and the API answered 400. A new welinc-auth migration, `20261027000100_drop_unused_domain_tables`, drops the repair, booking and maintenance tables the early schema left in the auth database. The last admin race held over 30 rounds. Eight verify steps stay unticked and are left to `/test`: dashboard single call, `AUTH_SERVICE_URL` unset, HTML or 429 from auth, failing just in time write, `PORTAL_URL` in production, dead SMTP, the 409 shown in the UI, and the extra files in `src/auth/`.
- [x] Verify it: `/check verify auth service boundary`
- [x] Test it: `/test auth service boundary`
- [x] Review it (fresh model): `/check review auth service boundary`
- [x] Document it: `/document auth service boundary`

### 3. Analytics & AI service boundary · done
Decide whether analytics-ai stays its own service or merges into the main VRMS repos, and record its store choices (pgvector, DuckDB, Redis, MongoDB).
**Done when:** a spec records the service boundary and every store it keeps, with MongoDB justified or removed.
- Note (2026-10-25): direction chosen by you during spec 0007: the AI and the analytics both move into welinc-backend-vrms and are rebuilt from scratch, retiring welinc-backend-vrms-analytics-ai. AI ideas picked so far: triage while typing grounded on the knowledge base, search by meaning, cleaning "What fixed it" notes, AI drafted knowledge entries, duplicate ticket warnings. The spec also decides replacing spec 0007's `pg_trgm` grouping with embeddings and removing `autoEmbedIssues`.
- Note (2026-10-29): spec 0010 (data model v2) renames ticket statuses and drops tables, so the Python service breaks on its status breakdown, aging and AI vehicle history until this feature replaces it. The `vrms-db` image also needs pgvector here (today only the separate analytics database has it), and the analytics page's silent sample data fallback must not carry over.
- Note (2026-10-29): until this feature replaces it, `welinc-backend-vrms-analytics-ai` got a small patch (PR 5, `feat/analytics-v2-columns`) so its sync reads `closed_at` and `CLOSED`; it runs again on the v2 database. Retire the patch with the service.
- Note (2026-10-30): from spec 0012's follow up. Embed each issue once on save and store the vector (never re-embed in a loop), add an `ai.embed_catchup_days` setting so turning AI back on embeds only the missing issues, declare `module.ai` as requiring `module.knowledge`, and remove the Python service's `app_settings` read when it retires.
- Note (2026-10-30): spec 0013 moves analytics and AI into backend-vrms (`src/modules/analytics/`, `src/modules/ai/`) on the VRMS database with pgvector, uses Gemini behind an `AiProvider` adapter, and retires the Python service with MongoDB, Redis, DuckDB and the separate analytics database. It is a move, not a redesign: the new AI ideas and knowledge base grounding go to feature 47, so `module.ai` does not require `module.knowledge` yet. Two numbers change meaning: cancelled tickets leave spend, and months follow Manila time. "Run AI review" on closed tickets goes away (confirm in Jira).
spec [0013](../specs/0013-analytics-ai-into-backend/index.md) · code in `welinc-backend-vrms/src/modules/analytics/`, `welinc-backend-vrms/src/modules/ai/`, `welinc-web-vrms/src/features/analytics/`, `welinc-web-vrms/src/features/repair/components/AiDiagnosisSection.tsx`
- Note (2026-10-31, replan): the `/sync` that note 76 left open has landed (the AGENTS.md sync PRs are merged in the workspace, backend-vrms and web-vrms). Open follow ups from spec 0013 that stay out of this feature: confirm in Jira that dropping "Run AI review" is fine (a question for the PM), and the retention limit for `ai_diagnoses` and the paid Gemini tier before go live (both already noted on feature 26).
- [x] Design it (spec): `/architect analytics & AI service boundary`
- Note (2026-10-31): milestones 1 to 3 are built and checked live with a real Gemini key (a diagnosis in about 2 seconds, similarity up to 100% on matching issues, `AI_BUSY` on parallel runs, 429 on the 21st run, AI off gives 403 `MODULE_DISABLED`, embed on save). Two things the spec did not know: `gemini-embedding-2` needs one content object per text (a plain string array returns a single combined vector, fixed in `gemini.provider.ts`), and a batch of 100 texts hit the free tier 429 while 50 passed, so a batch counts per text against the 100 a minute limit. `ai:embed-all` (milestone 4) should send 50 at a time with a pause, not 100. Local `vrms-db` is `pgvector/pgvector:pg16` (data kept, reindexed).
- Note (2026-10-31): milestone 4 is mostly built. Done: `ai.embed_catchup_days`, the 10 minute catch up job with its advisory lock, `npm run ai:embed-all` (50 at a time, 31 second pause, one retry), the analytics compose file, the `clone-all.sh` entry, README and `AI_SERVICE_URL` removed. Still open: the `/ai` and `/analytics` routes in `welinc-auth/nginx.conf` (shared repo, its own PR), archiving the Python repo on GitHub after the PRs merge, a live run of `ai:embed-all`, and `/sync` for the root AGENTS.md.
- Note (2026-10-31): milestone 5 is done. New unit tests cover the diagnosis service on the fake provider (success, cost hiding, 404, `TICKET_CLOSED`, `AI_BUSY`, `AI_RATE_LIMITED`, timeout, bad reply, no key) and the analytics rules (cancelled tickets excluded, Manila months, cost nulling and ordering). Backend-vrms: lint, build and 587 tests pass. Web-vrms: lint, typecheck, build and 126 tests pass. Milestone 4 stays open on four items that need you: the `/ai` and `/analytics` routes in `welinc-auth/nginx.conf` (shared repo, own branch and PR), archiving the Python repo after the PRs merge, a live `npm run ai:embed-all`, and `/sync`.
- Note (2026-10-31): milestone 4 update. The gateway routes are removed on `feat/retire-ai-analytics-gateway-routes` in welinc-auth (`nginx -t` passes, not committed or pushed yet, needs its own PR). `npm run ai:embed-all` ran on the local database and exits 0 with 556 of 556 issues embedded and none missing. Still open: push and merge the welinc-auth PR, archive the Python repo after the PRs merge, and `/sync`.
- Note (2026-10-31): the build is finished. All four PRs are merged (backend 24, web 27, auth 14, workspace 5), the local Python containers, volumes and images are removed, and the Python repo is archived. Left for later steps: `/sync` for the root and backend `AGENTS.md`, then `Verify it` and `Test it`.
- [x] Build it: `/develop analytics & AI service boundary`
  - [x] Thin thread: pgvector migration and the three tables, `summary` with cost masking, `AiProvider` with embed on create, one diagnosis run end to end in the panel (AC-1, AC-2, AC-3, AC-5, AC-7, AC-9, AC-14, AC-20)
  - [x] All analytics, no sample data: the other seven endpoints on the metric rules, sample fallback removed, error and empty states, export guarded (AC-3 to AC-6)
  - [x] Complete the AI: part prices and confidence, latest diagnosis, errors and limits, feedback, AI stats from tables, `ai.use` on the server (AC-8 to AC-13, AC-17)
  - [x] Embedding upkeep and retirement: `ai.embed_catchup_days`, the catch up job, `ai:embed-all`, then remove the analytics compose file, gateway routes and `AI_SERVICE_URL`, and archive the repo (AC-15, AC-16, AC-18, AC-19)
  - [x] Close out: unit tests, route table test, lint, typecheck, build and test in backend-vrms and web-vrms (AC-21)
- [x] Verify it: `/check verify analytics & AI service boundary`
- [x] Test it: `/test analytics & AI service boundary`
- [ ] Extra skills (optional, ask first): `docker-patterns` (compose and `vrms-db` image change) · `web-design-guidelines` (analytics error and empty states)

### 4. Data model v2 · done
One schema change that the Jira backlog needs: Chief Mechanic role, the new ticket statuses, verifier fields, attachments, notifications, outsourced shops, lookup lists. Also settle who owns the `Booking` and maintenance models copied into backend-vrms.
**Done when:** the schema supports slices 1 to 6 without another breaking migration, and existing tickets migrate with no data loss.
spec [0010](../specs/0010-data-model-v2/index.md)
code in `welinc-backend-vrms/prisma/`, `welinc-backend-vrms/src/modules/vrms/`, `welinc-backend-vrms/src/modules/knowledge/`, `welinc-web-vrms/src/` (branch `feat/data-model-v2` in both)
- Note (2026-10-25): spec 0007 lands part of this early: `CHIEF_MECHANIC`, `RepairPriority`, issue categories, and the knowledge base tables with new `RepairIssue` columns. Build on its migration rather than redoing them.
- Note (2026-10-29): do the VRMS tables now. Who owns the copied Booking and maintenance models waits for feature 56.
- Note (2026-10-29): spec 0010 squashes the 18 migrations into one baseline (everyone resets and reseeds; no real data exists, so "migrate with no data loss" holds trivially). You chose to drop the copied Booking and maintenance models now instead of waiting for feature 56. New tables (files, notifications, transfers, holds, shops, lookups) are designed in the spec and created by their own features. Crosses backend-vrms and web-vrms; the Python analytics service is left broken until feature 3.
- Note (2026-10-29): checked the open branches before the squash. backend-vrms has no branch carrying a migration that is not already on `development`, so the build's first step is clear.
- Note (2026-10-29): code built and green in both repos (backend lint, build, 136 tests; web lint, typecheck, build). Later the same day the baseline was applied locally (reset and seed), the database checks passed, and the backend container needed `prisma generate` inside it before it started clean. Both repos are committed on `feat/data-model-v2`, not pushed. History summary is now `finished`, `closed`, `cancelled`, `spend`. The repair form lost its Repair shop field and outsourced mechanics (back with features 36 and 37).
- Note (2026-10-29): verified in the running stack: reset from empty, shadow database diff, reseed, API status flow, audit shape, and the UI pages. Verify found two gaps, both fixed uncommitted: no Disabled badge in the repair form vehicle picker (web-vrms), and the old Python analytics queries still read `completed_at` and the `COMPLETED` status (now `closed_at` and `CLOSED`, so the sync runs again; feature 3 still replaces the service).
- [x] Design it (spec): `/architect data model v2`
- [x] Build it: `/develop data model v2`
  - [x] Baseline and one ticket flow end to end: open branches cleared, v2 schema, squashed baseline, repairs service on new statuses and assignments, first seed pass, web list, detail and form (AC-1 to AC-5, AC-4a, AC-8, AC-10 to AC-14)
  - [x] One audit shape everywhere: timeline endpoint, knowledge change log, web timeline and history dialog (AC-6, AC-7, AC-9)
  - [x] The rest of the app on v2: dashboard, history, due dates, vehicle label, full seed, leftover search (AC-2, AC-11, AC-13 to AC-16)
  - [x] Close out: tests updated, lint, typecheck and build in both repos, Docker stack check (AC-17)
- [x] Verify it: `/check verify data model v2` (2026-10-29: passed, every step run; one gap found and fixed, the Disabled badge in the vehicle picker)
- [x] Test it: `/test data model v2` (2026-10-29: backend suite 167 passed, 31 new; web-vrms got Vitest for pure logic, 42 passed)

### 5. Permission matrix & enforcement · done · GA
WL-109. One matrix of role against action, enforced on the server, mirrored in the UI.
**Done when:** every protected endpoint returns 403 for a forbidden role, the matrix lives in one place, and the UI hides what the server blocks.
- Note (2026-10-25): spec 0007 uses interim "Readers" and "Editors" role lists for the knowledge base; the matrix should take them over.
- Note (2026-10-28): spec 0009 leaves two pieces here. Scope welinc-auth's user list and `GET /auth/users/:id/changes` by system (today any ADMIN reads any user's change record). Also decide whether welinc-auth ever needs token refresh or whether its unused `RefreshToken` table is dropped (talk to the other groups first).
- Note (2026-10-29): you chose an Admin editable matrix. The fixed roles stay, but each role's permissions are stored in the database and an Admin turns them on or off from the Settings hub (feature 52). Some rights stay locked (for example Admin keeps user management) so nobody locks themselves out, and every change is audit logged. No custom roles. This feature builds the stored matrix and the server checks; the editing screen lands with feature 52.
spec [0011](../specs/0011-permission-matrix/index.md) · code in `welinc-backend-vrms/src/auth/permissions`, `welinc-web-vrms/src/lib/permissions`
- Note (2026-10-29): spec 0011 enforces the matrix with CASL in backend-vrms and web-vrms only (other groups may copy the pattern). Chief Mechanic gets `ticket.view_all` now (read only, no costs). It also scopes welinc-auth admin endpoints by system (a shared repo change, so it goes on the feature 55 list), adds shared account rules and the WeLinc account picker on Add user, and replaces spec 0006 AC-16's deactivate block with "move tickets back to the queue or keep them". `RefreshToken` is deferred to feature 56.
- [x] Design it (spec): `/architect permission matrix`
- [x] Build it: `/develop permission matrix`
  - [x] Thin thread: CASL compatibility check, matrix tables, catalog, backfill, per request version check, global guards, ticket reads on `accessibleBy`, `/permissions/me`, web ability and repairs routes (AC-1 to AC-6, AC-9, AC-10, AC-14, AC-16, AC-20, AC-21, AC-23)
  - Note (2026-10-29): thin thread built. `@casl/prisma` needs the relation operator spelled out, so the ownership condition is `assignments.some.mechanic.is.authUserId` (same meaning). The `analytics.view` key was added in the next chunk, and the browser pass of the shell states was done at `/check verify`.
  - [x] Every route and screen on the matrix: route mapping, costs, work vs administer, ticket `can` flags, knowledge, old role checks removed, route and e2e tests, matrix API, web `<Can>`, 403 handling, read only matrix section, the `analytics.view` key (AC-4, AC-7, AC-8, AC-11 to AC-13, AC-15, AC-17 to AC-19, AC-22, AC-22a, AC-24, AC-25)
  - Note (2026-10-29): built and checked live. Hidden cost fields now come back as `null` (AC-11) instead of being left out. On phones the tab bar shows when every nav item fits in it, else the sheet menu, read from the nav instead of the role. A PATCH that names the same cell twice gets 400. The route table test runs inside `npm run test` (no database), not `test:e2e`. `analytics.view` gates the screen only until feature 3.
  - [x] welinc-auth scoped by system: user list and changes, role edits, shared account rules, lookup, attach existing account (AC-26 to AC-30)
  - Note (2026-10-29): built and checked live on `feat/permission-matrix` in welinc-auth. Rules live in `src/auth/user-scope.ts`; the caller's system rides on the actor. Create also refuses another system's role (403), like role edits. The lookup limit counts per replica, in memory. In the seed data nearly every VRMS mechanic also holds a VMMS role, so they are all shared accounts: Delete answers 403 for them until the next milestone hides it.
  - [x] Open work: roster ignores lock, open work and release endpoints, ticket badges, Users page confirms and Add user picker (AC-31 to AC-36)
  - Note (2026-10-29): open work built and checked in a browser at `/check verify`. The email and Set password lock for an account that is ADMIN elsewhere shows only after welinc-auth refuses (the list sends system names, not roles). The Users page has no Delete action, so there is nothing to hide. Changing a mechanic to Admin in the edit dialog also asks about open tickets (reason ROLE_REMOVED). Release also leaves OUTSOURCED and PENDING_APPROVAL tickets alone, as the spec says "FOR_VERIFICATION and later".
  - [x] Close out: lint, build, tests and typecheck in all three repos (AC-37)
- [x] Verify it: `/check verify permission matrix`
- [x] Test it: `/test permission matrix`
- [ ] Review it (fresh model): `/check review permission matrix`
- [x] Document it: `/document permission matrix`

### 6. Design system & UI foundation · done
Turn `design.md` into real tokens and shared components (buttons, inputs, dialogs, confirm prompts, toasts, tables, empty and error states) so every page and modal looks the same. Includes the Tailwind v4 upgrade.
**Done when:** web-vrms uses only theme tokens (no raw hex), shared dialog, confirm and toast components exist, and base components meet WCAG AA contrast with visible focus and keyboard use.
spec [0001](../specs/0001-design-system-ui-foundation/index.md) · code in `welinc-web-vrms/src`
- [x] Design it (spec): `/architect design system & UI foundation`
- [x] Build it: `/develop design system & UI foundation`
  - [x] Thin thread: React 19, Tailwind v4, tokens and aliases, light only, Inter, Button on `/dev/ui` with axe and lint (AC-1 to AC-6, AC-14, AC-18)
  - [x] Feedback and overlays: sonner toasts, `confirm()`, ResponsiveDialog, menus, tooltip; ConfirmModal removed (AC-7 to AC-10)
  - [x] Forms and data display: Field with react-hook-form and zod, inputs, badges, DataTable, empty and error states, KPI card (AC-11 to AC-13, AC-15, AC-16)
  - [x] Enforcement sweep: palette reset, every page on tokens, lint errors everywhere, `design.md` updated (AC-2 to AC-4, AC-17)
- [ ] Verify it: `/check verify design system & UI foundation` (skipped)
- [ ] Test it: `/test design system & UI foundation` (skipped)
- [ ] Polish it (optional, ask first): `emil-design-eng` (toasts, confirm, dialogs, menus, tooltip) · `web-design-guidelines`

### 7. Language support (English + Filipino) · planned · needs a decision
Let users switch the UI between English and Filipino. Set up during the UI refresh so pages are not touched twice.
**Done when:** every UI string comes from a translation file, a language switch persists per user, and dates and money format for the Philippines.
- [ ] Design it (spec): `/architect language support`
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (long Filipino strings, peso amounts, dates)

### 52. Configurable settings & modules · done · from spec 0007
Admin managed settings stored in the database instead of code constants, and VRMS modules that can be switched on or off (for example the AI features). Replaces `KNOWLEDGE_SETTINGS` from spec 0007 first.
**Done when:** an admin changes a threshold or turns a module off without a deploy, every change is audit logged, and code reads settings from one place.
- Note (2026-10-29): you chose one Admin Settings hub. This feature owns it, with sections for lookup lists (feature 40), thresholds, modules, and role permissions (feature 5). Done also means every section lives in that one hub.
- Note (2026-10-29): moved from Release to right after the foundations, so the permission screen (feature 5) and lookup lists (feature 40) have a home before Slice 1. It is VRMS only, so it is safe before the integration meeting.
spec [0012](../specs/0012-configurable-settings-modules/index.md) · code in `welinc-backend-vrms/src/settings/`, `welinc-backend-vrms/src/auth/permissions/`, `welinc-backend-vrms/src/modules/knowledge/`, `welinc-web-vrms/src/features/settings/`, `welinc-backend-vrms-analytics-ai/main.py`, `welinc-backend-vrms-analytics-ai/sync_service.py`
- Note (2026-10-30): spec 0012 decided a code catalog with only changed values stored, switches for AI, Analytics and Knowledge base that remove their permission keys, and the Python service reading the AI and Analytics switches itself. Issue categories move to `config.read` and a new `lookups.manage`. Three new keys: `settings.manage`, `lookups.manage`, `ai.use`.
- [x] Design it (spec): `/architect configurable settings & modules`
- Note (2026-10-30): milestones 1 and 2 built. Two pieces of milestone 3 landed early because the knowledge switch needed them: the category routes now read with `config.read` and write with `lookups.manage`, and the web route `/knowledge-base/categories` needs `lookups.manage`. The hub shows only Modules and Thresholds until milestone 3 adds the other three sections, so its nav item follows `settings.manage` for now.
- Note (2026-10-30): break-ui on the hub found Recent changes reading the newest 100 changes in the browser, so a section could say it had none while its changes sat further back. Spec 0012 was updated with AC-31 (a `keys` filter on the changes endpoint) and AC-26 (change rows with units, the reset value, and removed keys named). Build, Verify and Test are open again for that milestone only.
- [x] Build it: `/develop configurable settings & modules`
  - [x] Thin thread: migration, settings catalog and service, combined version read, settings API with the change log, knowledge thresholds from the service, `/settings` shell and the Thresholds section (AC-1 to AC-7, AC-18, AC-21, AC-23, AC-27)
  - [x] Modules end to end: key removal and `MODULE_DISABLED` on the server, dependencies, the Modules section and hiding in the web app, the Python service switch and sync steps (AC-8 to AC-17, AC-22)
  - [x] Roles, lookup lists and change history: editable matrix, categories moved with the new keys, merged history (AC-19, AC-20, AC-24 to AC-26)
    - [x] Optional: look at `/settings` once in the browser with Playwright (looked at by hand instead, 2026-10-30) (a new page; the hub was never opened in a browser during milestones 1 and 2)
  - [x] Close out: seed, `settings:prune`, tests, states and keyboard pass, lint, typecheck, build and `py_compile` (AC-28 to AC-30)
    - Note (2026-10-30): seed reset, `settings:prune`, tests, lint, typecheck, build and `py_compile` are done and green. The hub was looked at by hand in the browser; a keyboard only pass was not run, so `/check verify` should cover it.
  - [x] Recent changes by key: `keys` on `GET /vrms/settings/changes` in backend-vrms, Recent changes asking per section in web-vrms, the dev datasets honouring it (AC-26, AC-31)
- [x] Verify it: `/check verify configurable settings & modules` (the new items at the end of `verify.md`)
- [x] Test it: `/test configurable settings & modules`
- [x] Polish it (optional, ask first): `impeccable` or `emil-design-eng` (one taste skill per change; motion: module confirm dialog and switches) · `web-design-guidelines` · `break-ui` (long names, notes and emails in Change history, an empty list, 20+ rows)
  - Note (2026-10-30): `impeccable` critique scored 27/40 and its fixes landed in web-vrms: a review step before saving permission changes (a reason is required when a right is removed), gold edited cells, phone cards for the matrix, section headings and descriptions, tidier thresholds and recent changes. Merged: web-vrms #25, backend-vrms #22. The review dialog now has its own steps at the end of `verify.md` and unit tests; one step is still open (saving a removal for real, which changes live permissions).
