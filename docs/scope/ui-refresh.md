# UI refresh

Every page, modal and prompt in web-vrms rebuilt on the design system (feature 6). Built UI first (`· Facade`): pages restyle on the data they already have, and screens for features not built yet show their final layout until the slice wires them. These need no spec of their own; `design.md` and the design system spec cover them. Back to [index](index.md).

## UI refresh

### 8. App shell & role badge · done · Facade
Sidebar, header and page frame on the new tokens, with the user's name and role badge (WL-101).
**Done when:** the role badge comes from the token, shows when collapsed and on a 375px phone, and each role has its own badge color.
- [x] Build it: `/develop app shell & role badge`
- code in `welinc-web-vrms/src/components/layout/`

### 9. Login & profile pages · done · Facade
Login, OTP, forgot password and profile restyled with clear errors and loading states.
**Done when:** each screen works at 375px and 1280px, errors are inline and readable, and buttons show progress.
- [x] Build it: `/develop login & profile pages`
- code in `welinc-web-vrms/src/features/auth/`
- Note (2026-10-22): login, OTP and forgot password are the shared portal's screens, so they moved to feature 50. This feature covers what web-vrms owns: the SSO handoff screen, the standalone fallback login and the profile page.

### 10. Dashboard · in-progress · Facade
Answers "what needs my attention?" first: open, overdue and waiting tickets up top.
**Done when:** stat tiles and lists use the design system, and empty, loading and error states render.
spec [0002](../specs/0002-dashboard-attention-first/index.md) · code in `welinc-web-vrms/src/features/dashboard/`
- [x] Design it (spec): `/architect dashboard refresh`
- [x] Build it: `/develop dashboard refresh`
  - [x] Data layer: attention helpers on one `fetchedAt`, `useDashboardData` with visible tab polling, refresh state and truncation flag, audit fetch dropped (AC-1, AC-3, AC-13, AC-14, AC-18)
  - [x] Admin view: attention tiles, Needs attention list and empty state, pipeline bar, spend cards with fixed timeframes, exports removed (AC-2 to AC-8, AC-17)
  - [x] Mechanic view: four tiles, urgency ordered work list, banner removed (AC-9 to AC-11, AC-17)
  - [x] States and sweep: skeleton, error and retry, dead widgets deleted, tokens only, 375px and 1280px with axe (AC-12, AC-15, AC-16)
- [x] Verify it: `/check verify dashboard refresh` (2026-10-25: passed; midnight and last month checks not run)
- [ ] Test it: `/test dashboard refresh`

### 11. Repair list & detail · in-progress · Facade
Ticket list with clear status pills and filters; ticket detail laid out around its one next action.
**Done when:** status badges follow `design.md`, the list works as cards on a phone, and every modal and confirm prompt on these screens uses the shared dialog.
spec [0004](../specs/0004-repair-list-detail-refresh/index.md) · code in `welinc-web-vrms/src/features/repair/`, `welinc-backend-vrms/src/modules/vrms/`
- Note (2026-10-22): the list becomes an urgent first queue of open tickets and the detail page is built around one next step button. Like feature 13, this breaks Facade on purpose: spec 0004 adds query params (no migration) in welinc-backend-vrms.
- [x] Design it (spec): `/architect repair list & detail refresh`
- [x] Build it: `/develop repair list & detail refresh`
  - [x] API: list filters, urgency order, mechanic scoping, zero costs, audit `ticketId`, 500 character limits (AC-3, AC-25 to AC-28)
  - [x] Repair list: shared helpers, URL filters, `DataTable` queue, states and refetch on focus (AC-1 to AC-11)
  - [x] Detail layout and next action: two column layout, side panel, status, cancel and unlock dialogs, bottom bar, 409 reload (AC-12 to AC-20, AC-24)
  - [x] Costs, AI and Activity: cost section with edit mode, AI restyle, ticket scoped Activity, old fields removed (AC-21 to AC-23, AC-29)
  - [x] Sweep: lint, typecheck, build, tests, 375px and 1280px with axe for both roles (AC-30)
- [x] Verify it: `/check verify repair list & detail refresh` (2026-10-25: passed; a few value sourcing steps not run)
- [ ] Test it: `/test repair list & detail refresh`

### 12. Repair form · in-progress · Facade
The new repair form in the stakeholder approved layout (WL-201), with pickers instead of typing.
**Done when:** the form matches the approved mockup, validation is inline, and it is usable with one thumb on a phone.
spec [0005](../specs/0005-repair-form-refresh/index.md) · code in `welinc-web-vrms/src/features/repair/`, `welinc-web-vrms/src/main.tsx`, `welinc-web-vrms/src/components/ui/combobox.tsx`, `welinc-web-vrms/src/components/ui/toggle-group.tsx`
- Note (2026-10-25): no mockup exists in the repo or Jira, so the layout follows `design.md` and the current fields. Frontend only; issue types, saved priority, open ticket counts and Assigned or Open on create stay with feature 18.
- [x] Design it (spec): `/architect repair form refresh`
- [x] Build it: `/develop repair form refresh`
  - [x] Foundations: data router, `toggle-group`, extended `Combobox`, option getter, schema and the options hook (AC-5, AC-7, AC-9, AC-10, AC-12, AC-13, AC-14, AC-22)
  - [x] Form sections: header, Vehicle, Issues, Priority and assignment, Billing, with list loading and failures (AC-1 to AC-15)
  - [x] Submit flow: action bar, summary dialog, create, success and failure handling, in flight lock (AC-15 to AC-21)
  - [x] Leave guard and sweep: `useBlocker` discard prompt, `beforeunload`, legacy code removed, 375px and 1280px with axe (AC-21, AC-23 to AC-25)
- [ ] Verify it: `/check verify repair form refresh`
- [ ] Test it: `/test repair form refresh`

### 13. History & audit log pages · done · Facade
Filters, tables and detail views restyled.
**Done when:** both pages use the shared table, filters fit a phone, and empty states explain what to do.
spec [0003](../specs/0003-history-audit-log-refresh/index.md) · code in `welinc-web-vrms/src/features/repair/pages/HistoryPage.tsx`, `welinc-web-vrms/src/features/audit-logs/`, `welinc-backend-vrms/src/modules/vrms/`
- Note (2026-10-22): history becomes a month grouped archive and the audit log a day grouped timeline. This feature breaks Facade on purpose: spec 0003 adds a migration and API changes in welinc-backend-vrms.
- [x] Design it (spec): `/architect history & audit log refresh`
- [x] Build it: `/develop history & audit log refresh`
  - [x] Data and write paths: migration with backfills, `CREATED` rows on create, no re-dating on same status saves, detail page kept working (AC-16, AC-16b, AC-17, AC-18b)
  - [x] API: paginated structured audit endpoint and actors list, history date and garage filters with summary, fail closed scoping (AC-2, AC-3, AC-11 to AC-15, AC-18)
  - [x] History page: date range filter, month grouped `DataTable`, summary strip, archive columns and states (AC-1 to AC-8)
  - [x] Audit timeline page, old endpoint removed, 375px and 1280px with axe (AC-9 to AC-15, AC-19, AC-20)
- [x] Verify it: `/check verify history & audit log refresh`
- [ ] Test it: `/test history & audit log refresh` (skipped 2026-10-22: marked done after verify passed)

### 14. User management page · planned · needs a decision · Facade
User table and its create, edit, deactivate and reset modals.
**Done when:** every modal uses the shared dialog, destructive actions ask to confirm, and success and failure show a toast.
- [ ] Design it (spec): `/architect user management refresh`

### 15. Knowledge base page · planned · needs a decision · Facade
Knowledge articles on the new tokens.
**Done when:** the page uses the design system, and it reads well on a phone and in its empty, loading and error states.
- [ ] Design it (spec): `/architect knowledge base refresh`

### 50. Portal on the design system · planned · needs a decision · from spec 0001
Copy the spec 0001 tokens and shared components into `welinc-web-portal` (already React 19, still Tailwind 3), so the SSO portal matches web-vrms. The portal is a shared repo, so agree on it with the other groups first.
**Done when:** the portal runs Tailwind v4, uses only theme tokens, and its login and app picker use the shared components.
- [ ] Design it (spec): `/architect portal on the design system`
- Note (2026-10-22): the shared login, OTP and forgot password screens live here, moved from feature 9. Restyling them changes the login for every subsystem.

### 51. Analytics page · planned · needs a decision · Facade
Analytics charts on the new tokens. Split from feature 15.
**Done when:** charts use theme colors, and the page reads well on a phone and in its empty, loading and error states.
- [ ] Design it (spec): `/architect analytics refresh`
