# UI refresh

Every page, modal and prompt in web-vrms rebuilt on the design system (feature 6). Built UI first (`· Facade`): pages restyle on the data they already have, and screens for features not built yet show their final layout until the slice wires them. These need no spec of their own; `design.md` and the design system spec cover them. Back to [index](index.md).

## UI refresh

### 8. App shell & role badge · done · Facade
Sidebar, header and page frame on the new tokens, with the user's name and role badge (WL-101).
**Done when:** the role badge comes from the token, shows when collapsed and on a 375px phone, and each role has its own badge color.
- [x] Build it: `/develop app shell & role badge`
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines`
- code in `welinc-web-vrms/src/components/layout/`

### 9. Login & profile pages · done · Facade
Login, OTP, forgot password and profile restyled with clear errors and loading states.
**Done when:** each screen works at 375px and 1280px, errors are inline and readable, and buttons show progress.
- [x] Build it: `/develop login & profile pages`
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (long names and emails, error text)
- code in `welinc-web-vrms/src/features/auth/`
- Note (2026-10-22): login, OTP and forgot password are the shared portal's screens, so they moved to feature 50. This feature covers what web-vrms owns: the SSO handoff screen, the standalone fallback login and the profile page.

### 10. Dashboard · in-progress · Facade
Answers "what needs my attention?" first: open, overdue and waiting tickets up top.
**Done when:** stat tiles and lists use the design system, and empty, loading and error states render.
spec [0002](../../specs/vrms/0002-dashboard-attention-first/index.md) · code in `welinc-web-vrms/src/features/dashboard/`
- [x] Design it (spec): `/architect dashboard refresh`
- [x] Build it: `/develop dashboard refresh`
  - [x] Data layer: attention helpers on one `fetchedAt`, `useDashboardData` with visible tab polling, refresh state and truncation flag, audit fetch dropped (AC-1, AC-3, AC-13, AC-14, AC-18)
  - [x] Admin view: attention tiles, Needs attention list and empty state, pipeline bar, spend cards with fixed timeframes, exports removed (AC-2 to AC-8, AC-17)
  - [x] Mechanic view: four tiles, urgency ordered work list, banner removed (AC-9 to AC-11, AC-17)
  - [x] States and sweep: skeleton, error and retry, dead widgets deleted, tokens only, 375px and 1280px with axe (AC-12, AC-15, AC-16)
- [x] Verify it: `/check verify dashboard refresh` (2026-10-25: passed; midnight and last month checks not run)
- Note (2026-11-23): picked in the S18 rounds (`Kpis13`, spec 0016 AC-14 and Follow-up): the KPI tiles become K15 `StatCard`s (caption, big mono number, a gold "Needs you" tag when hot, one context line, the whole card a link to the filtered list, no icon), and the dashboard gets a **period and garage filter** so no card says "last 7 days" (the period comes from the filter). S18's sweep restyles the tiles; the filter itself is this feature's work and still needs a ticket line for the PM. Retest after that settles.
- [ ] Test it: `/test dashboard refresh` (deferred 2026-11-02: the UI may be redone, so tests wait until it settles)
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (zero and huge counts, empty lists, long plates)

### 11. Repair list & detail · in-progress · Facade
Ticket list with clear status pills and filters; ticket detail laid out around its one next action.
**Done when:** status badges follow `design.md`, the list works as cards on a phone, and every modal and confirm prompt on these screens uses the shared dialog.
spec [0004](../../specs/vrms/0004-repair-list-detail-refresh/index.md) · code in `welinc-web-vrms/src/features/repair/`, `welinc-backend-vrms/src/modules/vrms/`
- Note (2026-10-22): the list becomes an urgent first queue of open tickets and the detail page is built around one next step button. Like feature 13, this breaks Facade on purpose: spec 0004 adds query params (no migration) in welinc-backend-vrms.
- [x] Design it (spec): `/architect repair list & detail refresh`
- [x] Build it: `/develop repair list & detail refresh`
  - [x] API: list filters, urgency order, mechanic scoping, zero costs, audit `ticketId`, 500 character limits (AC-3, AC-25 to AC-28)
  - [x] Repair list: shared helpers, URL filters, `DataTable` queue, states and refetch on focus (AC-1 to AC-11)
  - [x] Detail layout and next action: two column layout, side panel, status, cancel and unlock dialogs, bottom bar, 409 reload (AC-12 to AC-20, AC-24)
  - [x] Costs, AI and Activity: cost section with edit mode, AI restyle, ticket scoped Activity, old fields removed (AC-21 to AC-23, AC-29)
  - [x] Sweep: lint, typecheck, build, tests, 375px and 1280px with axe for both roles (AC-30)
- [x] Verify it: `/check verify repair list & detail refresh` (2026-10-25: passed; a few value sourcing steps not run)
- [ ] Test it: `/test repair list & detail refresh` (deferred 2026-11-02: the UI may be redone, so tests wait until it settles)
- Note (2026-11-06): the detail page redesign is now feature 65; this Test it waits for it.
- [ ] Polish it (optional, ask first): `impeccable` or `emil-design-eng` (one taste skill per change; motion: status, cancel and unlock dialogs, next action bar) · `web-design-guidelines` · `break-ui` (long plates and notes, 1 and 500 tickets, empty filters)

### 12. Repair form · in-progress · Facade
The new repair form in the stakeholder approved layout (WL-201), with pickers instead of typing.
**Done when:** the form matches the approved mockup, validation is inline, and it is usable with one thumb on a phone.
spec [0005](../../specs/vrms/0005-repair-form-refresh/index.md) · code in `welinc-web-vrms/src/features/repair/`, `welinc-web-vrms/src/main.tsx`, `welinc-web-vrms/src/components/ui/combobox.tsx`, `welinc-web-vrms/src/components/ui/toggle-group.tsx`
- Note (2026-10-25): no mockup exists in the repo or Jira, so the layout follows `design.md` and the current fields. Frontend only; issue types, saved priority, open ticket counts and Assigned or Open on create stay with feature 18.
- [x] Design it (spec): `/architect repair form refresh`
- [x] Build it: `/develop repair form refresh`
  - [x] Foundations: data router, `toggle-group`, extended `Combobox`, option getter, schema and the options hook (AC-5, AC-7, AC-9, AC-10, AC-12, AC-13, AC-14, AC-22)
  - [x] Form sections: header, Vehicle, Issues, Priority and assignment, Billing, with list loading and failures (AC-1 to AC-15)
  - [x] Submit flow: action bar, summary dialog, create, success and failure handling, in flight lock (AC-15 to AC-21)
  - [x] Leave guard and sweep: `useBlocker` discard prompt, `beforeunload`, legacy code removed, 375px and 1280px with axe (AC-21, AC-23 to AC-25)
- [x] Verify it: `/check verify repair form refresh` (2026-10-28: passed, every step run)
- [ ] Test it: `/test repair form refresh` (deferred 2026-11-02: the UI may be redone, so tests wait until it settles)
- [ ] Polish it (optional, ask first): `impeccable` or `emil-design-eng` (one taste skill per change; motion: summary dialog and pickers) · `web-design-guidelines` · `break-ui` (long descriptions, 10 issues, empty pickers)

### 13. History & audit log pages · done · Facade
Filters, tables and detail views restyled.
**Done when:** both pages use the shared table, filters fit a phone, and empty states explain what to do.
spec [0003](../../specs/vrms/0003-history-audit-log-refresh/index.md) · code in `welinc-web-vrms/src/features/repair/pages/HistoryPage.tsx`, `welinc-web-vrms/src/features/audit-logs/`, `welinc-backend-vrms/src/modules/vrms/`
- Note (2026-10-22): history becomes a month grouped archive and the audit log a day grouped timeline. This feature breaks Facade on purpose: spec 0003 adds a migration and API changes in welinc-backend-vrms.
- [x] Design it (spec): `/architect history & audit log refresh`
- [x] Build it: `/develop history & audit log refresh`
  - [x] Data and write paths: migration with backfills, `CREATED` rows on create, no re-dating on same status saves, detail page kept working (AC-16, AC-16b, AC-17, AC-18b)
  - [x] API: paginated structured audit endpoint and actors list, history date and garage filters with summary, fail closed scoping (AC-2, AC-3, AC-11 to AC-15, AC-18)
  - [x] History page: date range filter, month grouped `DataTable`, summary strip, archive columns and states (AC-1 to AC-8)
  - [x] Audit timeline page, old endpoint removed, 375px and 1280px with axe (AC-9 to AC-15, AC-19, AC-20)
- [x] Verify it: `/check verify history & audit log refresh`
- [ ] Test it: `/test history & audit log refresh` (skipped 2026-10-22: marked done after verify passed)
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (long actor names, empty months, many rows)

### 14. User management page · in-progress · Facade
User table and its create, edit, deactivate and reset modals.
**Done when:** every modal uses the shared dialog, destructive actions ask to confirm, and success and failure show a toast.
spec [0006](../../specs/vrms/0006-user-management-refresh/index.md) · code in `welinc-web-vrms/src/features/user-management/`, `welinc-web-vrms/src/components/shared/`, `welinc-backend-vrms/src/modules/vrms/config/`
- Note (2026-10-25): the list sorts what needs attention first, reset emails a code instead of the shared `Password123!`, and deactivating a mechanic with open tickets is blocked. Like features 11 and 13, this breaks Facade on purpose: spec 0006 adds an `email` field (no migration) to `GET /vrms/mechanics/available` in welinc-backend-vrms. welinc-auth is not changed; its gaps are in the spec's Follow-up.
- [x] Design it (spec): `/architect user management refresh`
- [x] Build it: `/develop user management refresh`
  - [x] Foundations and list: status, sort, URL filters, selectable tiles, `DataTable` with states, quiet refetch (AC-1 to AC-8)
  - [x] Create and edit dialog: schema, payloads, create mail failure recovery, email change prompt, errors, discard guard, own row locks (AC-10 to AC-14, AC-22)
  - [x] Account actions: per status menu, reset and setup codes, unlock, reactivate, deactivate, focus return (AC-9, AC-15, AC-17 to AC-21)
  - [x] Open work check: `email` on the mechanics endpoint, fresh match and block, fails closed (AC-16, AC-23)
  - [x] Cleanup and sweep: old code and `Password123!` removed, tokens only, 375px and 1280px with axe, lint, typecheck, build and tests (AC-24 to AC-26)
- Note (2026-10-25): built. welinc-backend-vrms `npm run lint` runs `eslint --fix` and already fails on `development` (203 problems without fix, none in the touched file), so AC-26's backend lint is not green yet; build and the 44 tests pass.
- Note (2026-10-28): spec 0009 shipped `setupEmailSent` and the unlock on reset in welinc-auth, so this page can drop its workaround: simplify AC-10 and merge AC-20's two calls into one. Do it with the verify pass.
- [x] Verify it: `/check verify user management refresh` (2026-10-28: passed; the repair form mechanic picker and most value sourcing steps not run; the Antonio step now uses Juan; backend lint ran as `lint:ci`, not the `--fix` script)
- [ ] Test it: `/test user management refresh` (deferred 2026-11-02: the UI may be redone, so tests wait until it settles)
- [ ] Polish it (optional, ask first): `impeccable` or `emil-design-eng` (one taste skill per change; motion: create, edit and account action dialogs) · `web-design-guidelines` · `break-ui` (long names, unbreakable emails, many users). Feature 52's milestone 3 has landed (the permissions section now lives in Settings), so this is no longer blocked

### 15. Knowledge base page · in-progress · Facade
Knowledge articles on the new tokens.
**Done when:** the page uses the design system, and it reads well on a phone and in its empty, loading and error states.
spec [0007](../../specs/vrms/0007-knowledge-base-fix-library/index.md) · code in `welinc-web-vrms/src/features/knowledge-base/`, `welinc-web-vrms/src/features/repair/`, `welinc-web-vrms/src/features/user-management/`, `welinc-backend-vrms/src/modules/knowledge/`, `welinc-backend-vrms/src/modules/vrms/`, `welinc-auth/prisma/`
- Note (2026-10-25): redesigned as a common issues library (Jira WL-704) that fills itself from repairs, instead of a restyle of the fake localStorage SOPs. It also covers feature 41's picker (WL-702) and adds the `CHIEF_MECHANIC` role (the role part of feature 17). Breaks Facade on purpose: a migration in welinc-backend-vrms and an enum change in welinc-auth. No AI; the AI rework (feature 3) builds on it.
- [x] Design it (spec): `/architect knowledge base refresh`
- [x] Build it: `/develop knowledge base refresh`
  - [x] Role and data: `CHIEF_MECHANIC` in auth, backend and web, one migration with category seed and backfill (AC-1 to AC-5)
  - [x] Library and entry pages: read API, history stats, search and filters, every state, old page removed (AC-6 to AC-15, AC-37)
  - [x] Editing: entry editor, status actions, change log, categories page, 409 handling (AC-16 to AC-23, AC-38)
  - [x] Picker and ticket: repair form picker, Known fix checklist, link and relink, "What fixed it" on send for verification (AC-24 to AC-31)
  - [x] Suggestions and sweep: grouping, create from group with backfill, mechanic suggestions, tests, axe at 375px and 1280px (AC-32 to AC-36, AC-39)
- Note (2026-10-25): built on `feat/knowledge-base-refresh` in welinc-auth, welinc-backend-vrms and welinc-web-vrms (not pushed). 73 backend tests pass (29 new); lint, typecheck and build are green in the touched files and repos; axe finds nothing at 375px and 1280px for admin, chief mechanic and mechanic. The local auth database has no migration history (built with `db push`), so its `CHIEF_MECHANIC` migration was applied with `prisma db execute`. One call made during the build: issues linked from a suggestion group are linked even when the new entry is saved as a draft (history), while the picker and the ticket link stay Active only. Verify steps in the spec's `verify.md`.
- Note (2026-10-25): follow up, not part of spec 0007. The ticket's Known fix checklist can only be ticked today. You want it to stay a helper, so each ticket should let you add, remove and reword its own copied steps without changing the knowledge base entry. Needs a small spec (`/architect per ticket checklist edits`) once feature 15 is verified.
- Note (2026-11-10, replan): follow ups from specs 0023 and 0024, none urgent. Check that typical parts and hours are easy to find on the entry page, since the ticket no longer shows them. Move the entry editor's Move up and Move down (`EntryFormSections.tsx`) to the same drag rows the ticket uses, so the two step editors match. Once real data exists, show how often an entry's steps were added to or reworded on tickets, and let a knowledge editor adopt them.
- [x] Verify it: `/check verify knowledge base refresh`
- [ ] Test it: `/test knowledge base refresh` (deferred 2026-11-02: the UI may be redone, so tests wait until it settles)
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (long entry names and steps, empty library, many suggestions)

### 50. Portal on the design system · dropped · replaced by suite S4 · from spec 0001
Copy the spec 0001 tokens and shared components into `welinc-web-portal` (already React 19, still Tailwind 3), so the SSO portal matches web-vrms. The portal is a shared repo, so agree on it with the other groups first.
**Done when:** the portal runs Tailwind v4, uses only theme tokens, and its login and app picker use the shared components.
- [ ] Design it (spec): `/architect portal on the design system`
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines`
- Note (2026-10-22): the shared login, OTP and forgot password screens live here, moved from feature 9. Restyling them changes the login for every subsystem.
- Note (2026-10-30): the portal has no app picker yet (it redirects straight to one system). Feature 60 builds it; restyle the picker here only once it exists.
- Note (2026-11-10, replan): dropped, replaced by [S4. App initiated login and launcher](../_root/shared-services.md#s4-app-initiated-login-and-launcher--in-progress). Its branch moves the portal to Tailwind v4, shadcn and tokens with a lint rule against raw colors, and builds the launcher. The login and forgot password keep their gradient and glows on purpose (spec 0007 AC-22), so no further restyle is planned. Kept here for history.

### 51. Analytics page · planned · needs a decision · Facade
Analytics charts on the new tokens. Split from feature 15.
**Done when:** charts use theme colors, and the page reads well on a phone and in its empty, loading and error states.
- Note (2026-10-29): the page silently swapped in sample numbers when any of its nine calls failed, so CSV and PDF exports could carry fake data.
- Note (2026-10-31, replan): feature 3 (spec 0013) fixed that: the sample data fallback is gone, and the page has error and empty states and a guarded export. What is left here is the token and chart restyle, and a phone check. Skip this if it looks fine to you.
- [ ] Design it (spec): `/architect analytics refresh`
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (extreme costs, empty charts, long garage names)

### 64. Audit log page redesign · planned · needs a decision · from spec 0021
You find the current Audit log page ugly, and want it redone. It should be redesigned on top of the trail from feature 24, not just restyled. No new page: it replaces `/audit-logs`.
**Done when:** the page has a new layout you signed off on, its filters come from `GET /vrms/repairs/audit-logs/catalog` (category chips, not 14 flat type chips), the busy step tick and photo rows don't bury status and cost changes, and it reads well at 375px and 1280px in its empty, loading and error states.
- Note (2026-11-04): build after feature 24 (spec 0021) ships its categories, filters and catalog. Decide the design source in the spec. Consider sharing the event renderer with feature 32 (the per ticket timeline).
- Note (2026-11-08, replan): from spec 0024. Group one checklist save's step rows in Activity (a save can write up to about 40 rows, spec 0023).
- Note (2026-11-10, replan): from spec 0023. Include its four new checklist event types in the Checklist chip.
- Note (2026-11-12, replan, from suite spec 0011): the day grouped row style built for My profile Recent activity and the Users Activity dialog can be reused here.
- Note (2026-11-23): your direction so far (carried in the handoffs since Nov 21, parked): a filterable table with a side panel for a row's changes (the GitHub, Okta and Stripe pattern), and two tabs, Timeline and **Deliveries** (feature 56's integration message record). No board exists yet: offer clickable mockups on the S18 look when this starts. Build it on spec 0016 (tables, side sheet, states).
- [ ] Design it (spec): `/architect audit log page redesign`
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (long actor names, many step ticks, long remarks, empty filters)

### 65. Ticket detail redesign · in-progress · Facade · from feature 11
A ticket can carry 10 issues with up to 20 steps each, and today every issue shows fully open, so one issue fills a laptop screen. Redesign the detail page around the work: issues as rows that open and close, the checklist first, and less reference clutter. It should look plain and dense like a shop work order, not generated. No new page: it replaces the layout of `/repairs/:id`.
**Done when:** each issue is a row that opens and closes, showing its progress and a state (Not started, In progress, Done, Returned) when closed; the checklist comes first inside a row; typical parts and typical hours are gone from the ticket; the safety note is one line and never hidden; photos fold to one line; vehicle and notes sit in the sidebar; AI diagnosis sits inside its issue; Activity shows the latest 5 with Show all; the category shows once; Cancel ticket is no longer beside the main action; on phones the issues come first, as `docs/context/vrms/design.md` orders; and it reads well at 375px and 1280px.
- Note (2026-11-06): asked for while building feature 58. Decide in the spec which rows start open per role and status, the issue states, where photos and the safety note go, and the look (no boxes inside boxes, no icon labels, colour only for status, overdue, safety and destructive actions). No API or data change is expected: progress and state come from fields the ticket already sends.
spec [0024](../../specs/vrms/0024-ticket-detail-redesign/index.md) · code in `welinc-web-vrms/src/features/repair/`
- Note (2026-11-06): spec 0024 decided it. Issues become foldable rows (shadcn Accordion) with a state derived from ticks (Not started, In progress, Done, No checklist, Returned); rows open by ticket status (first unfinished while work is ongoing, all closed for the verifier and finished tickets), remembered per tab, with `#issue-N` links. Safety is one line above the checklist, photos and AI fold to one line each, Activity shows the 5 newest, Notes and Vehicle move to the sidebar, the title becomes plate, model and first issue, and Cancel goes into a `⋮` menu. Web only, plus one backend test that locks the issue order.
- [x] Design it (spec): `/architect ticket detail redesign`
- Note (2026-11-06): spec 0024 updated after the first build with six refinements (build task 5), cross checked and accepted.
- Note (2026-11-07): spec 0024 updated again (build task 6), cross checked and accepted: photos become their own card after Issues with one add tile in the group photos land in (this replaces "photos fold to one line" above), the summary line keeps only Hide done steps, no dot separators anywhere on the page, hover labels on the badges and menus, rows stay foldable.
- Note (2026-11-07): spec 0024 updated a third time (build task 7), cross checked and accepted: Hide done steps removed, the drop hint shows only during a file drag, Activity folds like AI with the newest entry on its line, one due line in the Status card with Return to mechanic as a plain button, the garage out of the header, and Before and After side by side only when the card fits.
- Note (2026-11-07): spec 0024 updated a fourth time (build task 8), cross checked and accepted: Status card with badges and due on one row and Return beside the primary, the row menu on the header line, one block resolution, a repeated root cause shown once, photo drop zones per group (a new optional upload `group`), thumbnail drag between groups, and Before protection only for photos uploaded before work started (amends spec 0018).
- Note (2026-11-07): spec 0024 updated after the task 8 build: Plate and Model stay in Details (AC-16), and the AC-12 whole word example is fixed to match its rule. The code already matched; nothing to rebuild.
- Note (2026-11-07): spec 0024 updated a fifth time (build task 9, already built in `welinc-web-vrms` `1ddf82f`): the Status card as Status, Priority and Due rows with the overdue count under the date and no icon, Copy ticket link in its `⋮` menu, a shared `MoreMenu` that stops the tooltip reopening, icons in the issue row menu, a late Before photo tile with a warning notice, and sentence case pills with a hairline ring on every VRMS screen. Verify it is still open.
- Note (2026-11-07): spec 0024 updated a sixth time (build task 10), cross checked and accepted, after `/check verify` measured the phone rows at 375px (title column about 62px, line 2 cut to nothing): below 768px the fixed progress column goes, the progress becomes the first part of line 2 with its bar as a strip under it, and line 2 may wrap. Nothing changes from 768px. Build it is open again for this one task.
- [x] Build it: `/develop ticket detail redesign`
  - [x] Pure rules: `issueRow.ts` (state, open rule, counts, prefix strip), `useTicketView` and `useTickOverrides`, their tests, the issue order test (AC-3 to AC-6, AC-12)
  - [x] Issue rows: the Accordion, closed and open rows, summary line, Hide done steps, parts and hours removed (AC-1 to AC-10, AC-12)
  - [x] Page frame: title, sidebar Notes and Vehicle, the `⋮` menu, phone order, photos line and blocked link, AI card, Activity (AC-11, AC-13 to AC-18)
  - [x] Sweep: skeleton, axe at 375px and 1280px, keyboard, reduced motion, lint, typecheck, build, tests (AC-19, AC-20)
  - [x] Refinements: row ⋮ menu, one Hide done steps switch, folded photos line with the needed hint, Status card with priority and due, Details in Vehicle and Record, title and step row sizes (AC-2, AC-5 to AC-7, AC-9, AC-10, AC-13, AC-16 to AC-18)
  - [x] Second refinements: Photos card after Issues with the add tile and "+N more", only Hide done steps on the summary line, no dot separators (AC-2, AC-6, AC-11, AC-13, AC-14, AC-16 to AC-19)
  - [x] Third refinements: no Hide done steps, drop overlay, folded Activity with a shared `FoldCard`, one due line and a plain Return button, no garage in the header (AC-5, AC-6, AC-9, AC-11, AC-13 to AC-15, AC-17, AC-18)
  - [x] Fourth refinements: upload `group` and narrowed Before protection (backend), drop zones and thumbnail drag, Status card row and side by side buttons, row menu on the header, one block resolution, `issueDisplayText` (AC-2, AC-3, AC-7, AC-12, AC-13, AC-17, AC-21, AC-22)
  - [x] Fifth refinements: Status card rows and `dueValue`, shared `MoreMenu` with Copy ticket link, late Before tile with the warning notice, softer pills everywhere (AC-7, AC-13, AC-17 to AC-20)
  - [x] Sixth refinements: progress as the first part of line 2 with a bar strip below 768px, wrapping line 2, no change from 768px (AC-2, AC-3, AC-20)
- [ ] Verify it: `/check verify ticket detail redesign`
  - Note (2026-11-17, replan): partial pass, 12 more steps ticked in `verify.md` (row states, Returned, open rows kept on reload and refresh, `#issue-N`, the AI card). Still open among the major flows: the default open rule on an In progress ticket (AC-4, AC-6), Activity's 5 newest and Show all (AC-15), keyboard folding (AC-1), and axe (AC-19, AC-20). The other open steps wait for the full verify run after the build out.
- [ ] Test it: `/test ticket detail redesign`
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (10 issues with 20 steps each, long issue text, no known fix, returned issues)

### 70. Navigation redesign · in-progress
Rework the VRMS sidebar (and the portal Admin sidebar to match): a system switcher dropdown at the top, folding sections, a primary New repair button, queue counts, and an account menu at the bottom, instead of today's flat list.
**Done when:** the chosen sidebar ships in web-vrms and the portal Admin, keeps the permission gating of `navItems.ts`, folds to icons on desktop, and still becomes the tab bar or sheet on phones.
- Note (2026-11-18): raised by you: the sidebar is too plain. Four options are mocked up (N1 to N4 on the design directions canvas). Build it on the S18 design direction; the portal Admin half rides with S19 and S20.
- Note (2026-11-23): the sidebar's look is settled by `Sidebars8` (canvas "WeLinc design directions", page "Round 8") and spec 0016 *Layout and navigation*: section labels with lines between them and **no folding** (only a page with pages under it, such as Repair tickets and Knowledge base, opens), section names Work, Fleet, Insights and Admin, counts as mono bubbles (gold only when hot), and the icon collapse. So "folding sections" in the intent above is out of date. What's left for this feature's `/architect` is which pages each role sees, the New repair button, and the phone tab bar or sheet (spec 0016 AC-16 leaves those here).
- Note (2026-11-23, board check): also open, since `Sidebars8` doesn't draw them: what the system switcher and the account menu hold, the "Back to the portal" link, and the phone layout (only round 1's `BPhone` drew one; spec 0016 says a bottom tab bar for roles with at most 5 items, a sheet otherwise). Settled in round 6: no Inbox, Settings without a dropdown, Audit logs uses the ScrollText icon and Settings a cog.
- Note (2026-11-23, `/architect`): decided: sections Work, Insights, Admin (no Fleet: VMMS owns the trucks, feature 56); sub pages as `view` presets of the repair list with live counts from `GET /vrms/nav/counts` (On hold waits for feature 31); New repair at the top of the sidebar, in page headers on phones; the switcher keeps spec 0007's rule (two or more systems, or a VRMS Admin) and opens systems through the launcher's new `?open=`; Profile moves to the account menu; the portal Admin sidebar gets the same frame with a Deletion requests count. Builds after S18's milestone 3 and suite spec 0018's VRMS step.
spec [0027](../../specs/vrms/0027-navigation-redesign/index.md) · code in `welinc-web-vrms/src/components/layout/`, `welinc-backend-vrms/src/modules/vrms/`, `welinc-web-portal/src/pages/admin/AdminShell.tsx`
- [x] Design it (spec): `/architect navigation redesign`
- [ ] Build it: `/develop navigation redesign` (after S18's milestone 3 and S21's VRMS milestone)
  - [ ] Sidebar UI on today's data: sections, sub pages, open state, switcher, New repair, account menu (AC-1 to AC-3, AC-8 to AC-10)
  - [ ] Backend: `sent_back_at`, `view` on the repair list, `inRoster`, `/vrms/nav/counts` (AC-2, AC-4, AC-5)
  - [ ] Counts in the sidebar, hot rule, collapsed dots, phones (AC-5 to AC-7, AC-11)
  - [ ] Portal Admin frame, `pendingDeletionRequests`, the launcher's `open`, then the sweep and board comparison (AC-12 to AC-15)
- [ ] Verify it: `/check verify navigation redesign`
- [ ] Test it: `/test navigation redesign`

### 73. Error scenes · planned · needs a decision
Give every error state in web-vrms its own drawn road and depot scene in place of the small icon, and reuse the scenes in the portal. The crash copy from spec 0025 (AC-7, AC-7a) stays; only the picture changes.
**Done when:** each picked scene ships in web-vrms (crash inside the app, page didn't load, record not found, no access, module turned off, full page crash, permissions didn't load, small errors in cards and dialogs), a crash inside the shell keeps the sidebar and top bar with a 720 px scene panel, motion loops and respects reduced motion, and the portal's copies can't drift from web-vrms's without a check failing.
- Note (2026-11-25, replan): enrolled from the 2026-11-25 handoff's item 2. Every scene is picked (canvas rounds 38 to 43); the picked boards, the rules from your notes and the inventory are in [`docs/context/vrms/error-scene-boards/`](../../context/vrms/error-scene-boards/README.md), so the build needs neither the canvas nor the codesamtm account. The 404 and "No VRMS access" reuse the portal's Round 34 barrier and gate scenes; the offline banner stays a banner.
- Note (2026-11-25, your call): one VRMS row and one spec; the portal reuse is a note here and on S22, not a suite row. For `/architect`: how the two apps share the scene components (recommended in the handoff: copies under `src/components/brand/scenes/` plus a checker like `check-design-tokens.mjs`; a shared package is too much setup this close to the deadline), and the start points on the portal's `feat/portal-redesign` (`LiveryTruck.tsx`, `NotFound.tsx`, the `--scene-*` and `--livery-*` tokens, `scene-blink`). Order: after S22, before feature 56.
- [ ] Design it (spec): `/architect error scenes`
- [ ] Polish it (optional, ask first): `emil-design-eng` (looping motion, reduced motion) · `web-design-guidelines`
