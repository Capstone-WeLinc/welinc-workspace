# Refresh button on the dashboards

Status: pushed, not yet in a pull request. Branch `BMS/dashboard-refresh` in
`welinc-web-bms`, into `development`.

Adds a **Refresh** button to the Administrator, Customer Service and
Operations dashboards. It works like the one on the VMMS dashboard
(`welinc-web-vmms`, `src/pages/Dashboard/Dashboard.tsx`). Touches only
`welinc-web-bms`. No backend change, no database migrations, and no change to
shared auth, portal or the suite gateway. `welinc-web-vmms` was only read,
never changed.

## Problem

The dashboards already reload on their own every 15 seconds and when you come
back to the browser tab. But there was no way to reload right away, for
example after a teammate says they just added a booking.

## What it does

Files: `src/components/shared/RefreshButton.tsx` (new),
`src/pages/admin/AdminDashboard.tsx`,
`src/pages/customerservice/CsDashboard.tsx`,
`src/pages/operations/OperationsDashboard.tsx`

- A **Refresh** button sits on the right of each dashboard's header, across
  from the title.
- Clicking it reloads all of that dashboard's numbers and lists straight away.
- While it loads, the icon spins and the button can't be clicked again.
- It uses the dashboard's existing load, so it reads the same data as the
  automatic reload. If the load fails, the dashboard shows its usual "Live data
  couldn't be loaded" message with **Retry**, and keeps the last numbers on
  screen.
- The look follows VMMS: a white button with a light border, a refresh icon
  and the word "Refresh". Its border turns BMS navy `#1a1f6e` on hover.

All three dashboards share the one button component, so they look and behave
the same.

## Unchanged

- The automatic reload every 15 seconds and when the tab regains focus.
- On the Administrator dashboard, the reload when a booking's status changes.
- What each dashboard shows.

## Not copied from VMMS

The VMMS dashboard's header also has a date range picker (Today, This month,
Custom range). It wasn't asked for, so BMS doesn't get it.

## Testing

- The web app type-checks (`npm run typecheck`). The changed files lint with
  no errors. The two warnings in `AdminDashboard.tsx` were already there.
- Unit tests pass (`npm test`, 20 tests).
- The running app at `http://localhost:8003` serves the new code after a
  container restart. Not yet checked by hand for each role.

## Deploy notes

- No backend or database changes, so it can merge on its own.
- Merging into `development` triggers the staging deploy.
