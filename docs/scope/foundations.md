# Foundations

What is already built (enrolled for context) and the ground every slice stands on. Back to [index](index.md).

## Already built

These predate the workflow. `/develop` and `/sync` leave them alone; planned features below replace or extend parts of them.

### A. Login, OTP and password reset · existing
Email and password login, mechanic OTP, forgot and reset password, profile and profile picture. Note: backend-vrms has its own auth module next to `welinc-auth` (feature 2 decides which one owns this). code in `welinc-backend-vrms/src/auth/`, `welinc-web-vrms/src/features/auth/`

### B. User management · existing
Admin lists, creates, edits, deactivates, unlocks and resets users. code in `welinc-backend-vrms/src/auth/`, `welinc-web-vrms/src/features/user-management/`

### C. Repair tickets · existing
Create, list, detail, status change (`PENDING → IN_PROGRESS → FOR_VERIFICATION → COMPLETED`, plus `CANCELLED`), cost encoding, unlock a closed ticket. The form's vehicle system and root cause options are hardcoded (`lib/mockConfig`). code in `welinc-backend-vrms/src/modules/vrms/`, `welinc-web-vrms/src/features/repair/`

### D. Repair history · existing
Closed tickets with filters. code in `welinc-backend-vrms/src/modules/vrms/` (`GET history`), `welinc-web-vrms/src/features/repair/pages/HistoryPage.tsx`

### E. Audit log page · existing
Admin view of logged ticket actions. code in `welinc-web-vrms/src/features/audit-logs/`

### F. Dashboard · existing
Metrics computed from live repairs, history and audit logs. code in `welinc-web-vrms/src/features/dashboard/`

### G. AI diagnosis and knowledge base · existing
AI diagnose, feedback and issue embedding, knowledge articles, AI logs and stats; the repair detail shows an AI diagnostic panel. code in `welinc-backend-vrms-analytics-ai/ai_service.py`, `welinc-web-vrms/src/features/knowledge-base/`

### H. Analytics dashboards · existing
Cost trends, vehicle KPIs, issue frequency, status breakdown, garage costs, aging, velocity. code in `welinc-backend-vrms-analytics-ai/analytics_service.py`, `welinc-web-vrms/src/features/analytics/`

## Foundation

### 1. Coding standards & tooling · planned
Capture each owned repo's real conventions so every later skill works from facts, not guesses.
**Done when:** web-vrms, backend-vrms, analytics-ai, auth and portal each have an `AGENTS.md` from `/audit`, and lint, typecheck and build run clean in each.
- [ ] Capture conventions per repo: `/audit`

### 2. Auth service boundary · planned · needs a decision · GA
backend-vrms carries its own login, OTP and user endpoints while `welinc-auth` is the shared auth service. Decide which owns what before roles and OTP change.
**Done when:** one service owns login, OTP and users; the other only validates tokens; the portal and web-vrms log in through one path.
- [ ] Design it (spec): `/architect auth service boundary`
- Note (2026-10-25): from spec 0007's follow up. Adding a mechanic or chief mechanic on the Users page creates no VRMS `Mechanic` row (only seeds do), so new accounts can't be assigned tickets. Whichever service ends up owning users should create that row.

### 3. Analytics & AI service boundary · planned · needs a decision
Decide whether analytics-ai stays its own service or merges into the main VRMS repos, and record its store choices (pgvector, DuckDB, Redis, MongoDB).
**Done when:** a spec records the service boundary and every store it keeps, with MongoDB justified or removed.
- Note (2026-10-25): direction chosen by you during spec 0007: the AI and the analytics both move into welinc-backend-vrms and are rebuilt from scratch, retiring welinc-backend-vrms-analytics-ai. AI ideas picked so far: triage while typing grounded on the knowledge base, search by meaning, cleaning "What fixed it" notes, AI drafted knowledge entries, duplicate ticket warnings. The spec also decides replacing spec 0007's `pg_trgm` grouping with embeddings and removing `autoEmbedIssues`.
- [ ] Design it (spec): `/architect analytics & AI service boundary`

### 4. Data model v2 · planned · needs a decision
One schema change that the Jira backlog needs: Chief Mechanic role, the new ticket statuses, verifier fields, attachments, notifications, outsourced shops, lookup lists. Also settle who owns the `Booking` and maintenance models copied into backend-vrms.
**Done when:** the schema supports slices 1 to 6 without another breaking migration, and existing tickets migrate with no data loss.
- Note (2026-10-25): spec 0007 lands part of this early: `CHIEF_MECHANIC`, `RepairPriority`, issue categories, and the knowledge base tables with new `RepairIssue` columns. Build on its migration rather than redoing them.
- [ ] Design it (spec): `/architect data model v2`

### 5. Permission matrix & enforcement · planned · needs a decision · GA
WL-109. One matrix of role against action, enforced on the server, mirrored in the UI.
**Done when:** every protected endpoint returns 403 for a forbidden role, the matrix lives in one place, and the UI hides what the server blocks.
- Note (2026-10-25): spec 0007 uses interim "Readers" and "Editors" role lists for the knowledge base; the matrix should take them over.
- [ ] Design it (spec): `/architect permission matrix`

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

### 7. Language support (English + Filipino) · planned · needs a decision
Let users switch the UI between English and Filipino. Set up during the UI refresh so pages are not touched twice.
**Done when:** every UI string comes from a translation file, a language switch persists per user, and dates and money format for the Philippines.
- [ ] Design it (spec): `/architect language support`
