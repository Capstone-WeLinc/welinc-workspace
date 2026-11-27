# Verification

Checks below derive from the acceptance criteria in [index.md](index.md). They distinguish code-level evidence from migration, browser, device, and live integration evidence.

## Backend

- [x] Unit tests cover stable ordering across timestamp ties, per-source keyset continuation, and a page dominated by one source → AC-2–3.
- [x] DTO/service tests reject malformed cursors, limits, categories, read filters, sources, and UUIDs → AC-3–4.
- [x] Unit tests verify user-scoped list/count/read operations and require current maintenance assignment and a non-deleted schedule → AC-1, AC-4.
- [ ] Verify mark-one-read and read-all are idempotent and legacy routes retain their response shapes → AC-4.
- [ ] Verify producer categories, action metadata, recipient selection, and stable dedupe for maintenance, fuel, and reports; preserve day 1/3/7 stages → AC-5–6.
- [x] Validate Prisma schema and generate the client; inspect the migration without applying it → AC-10.

## Web

- [x] Unit tests cover server unread counts, mark-all, per-item retry, and cursor continuation → AC-2, AC-4, AC-7.
- [x] Unit tests verify category/read filters reset pagination and do not reuse the previous cursor → AC-2–3, AC-7.
- [ ] Verify loading, empty, error/retry, retained-data-on-error, and successful refresh behavior → AC-7.
- [x] Unit tests verify known fuel/report actions route locally and unknown action types do not navigate → AC-6–7.
- [x] Unit tests verify a previous account's items and pending responses are hidden after an account switch → AC-1, AC-7.

## Mobile

- [x] Focused service/screen tests cover the unified inbox contract, counts, refresh controls, continuation, and read/read-all actions → AC-2, AC-4, AC-8.
- [x] Hook tests verify stale responses do not leak across account changes and mark-read failures can be retried successfully → AC-8.
- [ ] Verify work-order actions still open only role-authorized VMMS work and critical fuel acknowledgment remains separate → AC-8–9.
- [ ] Verify VRMS screens and behavior remain unchanged → AC-10.

## Runtime and release

- [x] Run focused backend, web, and mobile tests and production/type builds as documented by each repository; see automated evidence below.
- [ ] Browser-check the web inbox and device-check mobile refresh/navigation with an authorized local test account.
- [ ] Apply migration only in an explicitly authorized test environment; no production migration or deployment is included.
- [ ] Confirm no SMS or push notification was delivered or configured → AC-10.

## Automated verification completed

- Backend: `npx prisma validate`, `npm run build`, and focused inbox/fuel/maintenance Jest suites passed (5 suites, 21 tests). Inbox tests cover timestamp ties, uneven-source continuation, filters/validation, user and assignment scoping, and read retries. The migration was inspected but not applied.
- Web: the focused Navbar inbox Vitest suite passed (7 tests), `npm run build` passed, and ESLint passed for the changed Navbar files.
- Mobile: focused notification/search Jest suites passed (4 suites, 40 tests), `npx tsc --noEmit` passed, and ESLint passed for the account-isolation hook and its tests.
- Backend changed-file ESLint passed for the inbox, DTO, controller, maintenance, fuel-escalation, and reports files. `fuel.service.ts` still reports 42 Prettier findings outside the notification changes; that file was not reformatted to avoid unrelated churn.
- `git diff --check` passed in the backend, web, and mobile repositories.

These are code-level checks, not full acceptance evidence. The unmarked checks above still require additional automated cases or authorized browser/device/runtime verification.

## Acceptance-criteria coverage

AC-1–AC-10 are mapped to the checks above. A passing build is not proof of runtime inbox behavior. Migration application and live/device acceptance remain pending until performed in an authorized environment.
