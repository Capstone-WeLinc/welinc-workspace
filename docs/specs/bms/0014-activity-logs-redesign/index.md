# Activity logs redesign

Status: in progress. Web branch: `BMS/activity-logs-redesign`; workspace branch: `docs/bms-activity-logs-redesign`.

Decision history: [rationale.md](rationale.md). Review checklist: [verify.md](verify.md).

Redesigns the BMS Activity Logs page to match the supplied reference. The header date-range filter keeps its existing component, placement and behavior. Account activity remains accessible from its existing tab.

## Page layout

- Keep the Activity Logs title and date-range filter in the header. Use the subtitle “Review system activity performed by all WeLinc users.” and a horizontal divider below the header.
- Keep the existing BMS work and Accounts tabs so the account audit log remains available.
- The BMS work toolbar has a user search field, an **All Roles** dropdown and an **All Actions** dropdown. Keep the controls responsive and aligned to opposite sides on wide screens.
- Display the work log in a white, full-width table with a navy header and these columns: **User**, **Role**, **Action Performed**, **Date**, **Time**.
- Show a user's name in semibold and their email below it. Format date and time in Asia/Manila as before.
- Keep loading, empty, error, retry, pagination, search and date-range behavior.
- In the Accounts tab, keep its existing category and event filters and account activity data, using the same table presentation. Account IP addresses remain available through the event data but are not displayed in the redesigned table.

## Scope

Changes are limited to `welinc-web-bms` Activity Logs UI and this BMS spec in `welinc-workspace`. No API or backend changes are required. The header date filter is intentionally unchanged.
