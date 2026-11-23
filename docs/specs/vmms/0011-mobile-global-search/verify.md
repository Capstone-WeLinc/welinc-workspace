# Verify: Mobile global search · spec 0011

Steps derived from the acceptance criteria in [index.md](index.md).

## Automated

- [x] Build search records from assigned schedules, chief-supervised schedules,
  associated vehicles, and user notifications; confirm unrelated users'
  schedules are excluded → AC-1, AC-2
- [x] Match mixed-case queries with leading/trailing whitespace against
  work-order and vehicle fields and notification content; blank queries return
  no results → AC-3
- [x] Map work-order and scheduled-notification results to Work Orders and
  general-notification results to Notifications; verify deep-link access uses
  the role's existing assignment/supervision rule → AC-4
- [x] De-duplicate submitted query history, move repeated queries to the top,
  ignore blank submissions, and cap history at 10 entries → AC-7
- [ ] Confirm blank query, no matches, loading, and local-data failure render
  distinct states → AC-5

## Device / manual

- [ ] Submit a query from each search surface, restart the app, and confirm the
  two histories persist separately for the signed-in account; selecting an
  entry should re-run its query → AC-7
- [ ] Clear history on each surface and verify only that surface's saved
  history is removed; use the input clear control and verify it clears only
  current text → AC-7
- [ ] As a Mechanic, search assigned and unassigned work orders; only assigned
  results should appear, and an assigned result should open its work-order
  detail → AC-1, AC-2, AC-4
- [ ] As a Chief Mechanic, search supervised work orders and verify the
  matching work-order detail opens without exposing another chief's records →
  AC-2, AC-4
- [ ] Search a vehicle plate/model and a current notification; confirm each
  opens the associated existing workflow → AC-1, AC-4
- [ ] Disable connectivity after data synchronization; confirm cached
  work-order search remains available and notification results reflect only
  loaded notifications → AC-1, AC-5
- [ ] Force a local data-read failure and verify an explicit error appears
  instead of sample or success-shaped results → AC-5

## Commands

- [x] `npm exec -- jest --runInBand --runTestsByPath tests/globalSearch.integration.test.ts tests/searchHistory.integration.test.ts`
  — passed (6 tests)
- [x] `npm exec -- tsc --noEmit` — passed
- [x] `npm exec -- eslint -- App.tsx screens/WorkOrderScreen.tsx services/searchHistory.ts services/useSearchHistory.ts tests/searchHistory.integration.test.ts`
  — passed
- [ ] Run the documented mobile test suite

## Acceptance-criteria coverage

- Automated checks cover AC-1 through AC-4 and the history ordering/cap logic
  in AC-7. AC-5 UI-state and AC-7 persistence/control acceptance, plus
  device-level online/offline evidence, remain pending until exercised on a
  device.
