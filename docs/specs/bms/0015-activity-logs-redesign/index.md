# Activity logs redesign

Status: pushed, not yet in a pull request. Web branch: `BMS/activity-logs-redesign` (into `development`); workspace branch: `docs/bms-activity-logs-redesign` (into `main`).

Decision history: [rationale.md](rationale.md). Review checklist: [verify.md](verify.md).

Redesigns the BMS Activity Logs page to match the supplied reference. The header date-range filter keeps its existing component, placement and behavior. The page shows only the BMS work log: the Accounts tab is removed.

## Page layout

- Keep the Activity Logs title and date-range filter in the header. Use the subtitle “Review system activity performed by all WeLinc users.” and a single horizontal divider below the header: the one `PageHeader` already draws. The page must not add a border of its own around the header (an earlier version did, which showed two lines).
- No tabs: the BMS work and Accounts tabs are removed, and the toolbar sits directly under the header divider, as in the reference.
- The BMS work toolbar has a user search field, an **All Roles** dropdown and an **All Actions** dropdown. Keep the controls responsive and aligned to opposite sides on wide screens.
- Display the work log in a white, full-width table with a navy header and these columns: **User**, **Role**, **Action Performed**, **Date**, **Time**.
- Show a user's name in semibold and their email below it. Format date and time in Asia/Manila as before.
- Keep loading, empty, error, retry, pagination, search and date-range behavior.

## Scope

Changes are limited to `welinc-web-bms` Activity Logs UI and this BMS spec in `welinc-workspace`. No API or backend changes are required. The header date filter is intentionally unchanged.

## Removed

- The **Accounts** tab: account sign-in and security events from Auth (`GET /auth/activity` and `/auth/activity/catalog`), with its category and event filters, server-side search, "load more" paging, the "confirm your sign-in in the portal" error and its Open portal link. BMS no longer calls these Auth endpoints; the endpoints themselves are Auth's and are unchanged.
- `src/lib/account-activity.ts`: only the Accounts tab used it.
- The BMS work / Accounts tab switcher.

## Testing

- `welinc-web-bms`: the full CI sequence passes locally (`npm audit --omit=dev --audit-level=high`, `lint`, `typecheck`, `test`, `build:prod` with the CI's `VITE_*` values). Lint has no errors; its 30 warnings are all in other files and already on `development`. Unit tests pass (20).
- The branch includes the latest `development` (merged in, no conflicts), so it also carries spec bms/0014's Approvals changes.
- Not yet checked by hand in the running app.

## Deploy notes

- Web only; deploy `welinc-web-bms`. Nothing else changes.
