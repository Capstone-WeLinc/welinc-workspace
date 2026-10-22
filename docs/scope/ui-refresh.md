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
- [ ] Verify it: `/check verify dashboard refresh`
- [ ] Test it: `/test dashboard refresh`

### 11. Repair list & detail · planned · Facade
Ticket list with clear status pills and filters; ticket detail laid out around its one next action.
**Done when:** status badges follow `design.md`, the list works as cards on a phone, and every modal and confirm prompt on these screens uses the shared dialog.
- [ ] Build it: `/develop repair list & detail refresh`

### 12. Repair form · planned · Facade
The new repair form in the stakeholder approved layout (WL-201), with pickers instead of typing.
**Done when:** the form matches the approved mockup, validation is inline, and it is usable with one thumb on a phone.
- [ ] Build it: `/develop repair form refresh`

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

### 14. User management page · planned · Facade
User table and its create, edit, deactivate and reset modals.
**Done when:** every modal uses the shared dialog, destructive actions ask to confirm, and success and failure show a toast.
- [ ] Build it: `/develop user management refresh`

### 15. Knowledge base & analytics pages · planned · Facade
Knowledge articles and analytics charts on the new tokens.
**Done when:** charts use theme colors, and both pages read well on a phone and in their empty states.
- [ ] Build it: `/develop knowledge base & analytics refresh`

### 50. Portal on the design system · planned · from spec 0001
Copy the spec 0001 tokens and shared components into `welinc-web-portal` (already React 19, still Tailwind 3), so the SSO portal matches web-vrms. The portal is a shared repo, so agree on it with the other groups first.
**Done when:** the portal runs Tailwind v4, uses only theme tokens, and its login and app picker use the shared components.
- [ ] Build it: `/develop portal on the design system`
- Note (2026-10-22): the shared login, OTP and forgot password screens live here, moved from feature 9. Restyling them changes the login for every subsystem.
