# 0002. Attention first dashboard for web-vrms

**Date**: 2026-10-22
**Status**: In Progress
**Updated**: 2026-11-11 (staleness sweep). Status and field names follow spec 0010 (`PENDING` is `ASSIGNED`, `COMPLETED` is `CLOSED`, `targetDueDate` is `dueAt`, `completedAt` is `closedAt`). The view is chosen by permission keys, never the role name (spec 0011 AC-14, spec 0015 AC-11). Needs attention gained a "no mechanic" tier between overdue and waiting, with the empty text "No overdue tickets, none without a mechanic, and nothing waiting for sign off." (spec 0011 AC-34, spec 0019 AC-13). The Chief view is replaced by spec 0022.

Decision history (context, options, rationale): [rationale.md](rationale.md). Verify steps: [verify.md](verify.md).

## Summary

This spec decides what the VRMS dashboard shows and in what order, for scope feature 10. Both views now open with "what needs my attention?": a row of count tiles, then a short list of the tickets behind those counts. "Waiting" means a ticket in `FOR_VERIFICATION` (the mechanic is done and it waits on an admin to sign off), and the word means that everywhere. It is a frontend only restyle on data the app already loads (no backend change), built from the spec 0001 components.

## Requirements

**User stories**:
- As an admin, I want to see at a glance how many tickets are open, overdue and waiting for my sign off, and which ones they are, so that I clear the urgent ones first.
- As a mechanic, I want my own tickets ordered by urgency, overdue first, so that I always know what to work on next.
- As an admin, I still want the workload shape and repair spend on the dashboard, so that I don't open the analytics page for a quick check.

**Acceptance criteria**:
- **AC-1**: "Waiting" means status `FOR_VERIFICATION` everywhere on the dashboard (tiles, list labels, copy). "Overdue" means a ticket in `PENDING`, `IN_PROGRESS` or `FOR_VERIFICATION` whose `targetDueDate` is set and earlier than now. A ticket whose `targetDueDate` is `null`, missing or unparsable is never overdue. "Open" means status `PENDING`, `IN_PROGRESS` or `FOR_VERIFICATION`. Every time based rule (overdue, this month, day counts) is measured against `fetchedAt`, the time of the last successful fetch, not a fresh clock read, so tiles and lists always agree.
- **AC-2**: The admin view opens with four `KpiCard` tiles in this order: **Open** (`ClipboardList`), **Overdue** (`AlertTriangle`), **Waiting for sign off** (`ShieldCheck`), **Done this month** (`CheckCircle2`), with no context line. Done this month counts `COMPLETED` tickets whose `completedAt` falls in the current calendar month in the browser's local time. Overdue uses `tone="destructive"` only when its count is above 0 (default tone at 0), Done this month uses `tone="success"`, the others use the default tone. Four in a row from 1024px up, two by two below.
- **AC-3**: A ticket that is both overdue and waiting counts in both the Overdue and the Waiting tile. So the Needs attention list holds Overdue plus (Waiting minus the tickets in both), capped at 8, and its length is not expected to equal Overdue plus Waiting.
- **AC-4**: Below the tiles, the admin view shows a **Needs attention** list: overdue tickets first (oldest `targetDueDate` first), then waiting tickets that are not overdue (oldest `updatedAt` first). Each ticket appears once. At most 8 rows show. Columns: **Repair #** (`mobile: 'title'`), **Vehicle** plate (`mobile: 'subtitle'`), **Status** `StatusBadge` (`mobile: 'badge'`), **Due** context text (`mobile: 'field'`): the overdue text for overdue rows, the updated text for waiting rows (see *Text and formatting rules*). Clicking a row opens `/repairs/:id`. It renders with `DataTable` (cards below 768px). A "View all repairs" link to `/repairs` sits below the table and always shows.
- **AC-5**: When the Needs attention list is empty, it shows an `EmptyState` with the `CheckCircle2` icon, the title "Nothing needs your attention", and the description "No overdue tickets and nothing waiting for sign off." The "View all repairs" link below the table still shows. `DataTable`'s `empty` prop gains an optional `icon` that it passes to `EmptyState`.
- **AC-6**: Below the attention section, the admin view shows the **pipeline bar** under the heading "Pipeline" and the caption "Open tickets and this month's completions" (Assigned, In progress, For verification, Closed; cancelled left out). Segment widths are each count over the sum of those four. A zero count segment is not drawn, but its legend item still shows with 0. Each segment and legend item uses its `status-*-fg` token, and every legend item shows its label and count as text, so color is never the only signal. The bar has `role="img"` and an `aria-label` that lists every status and count. With all four at 0, the track is empty and reads "Nothing open and nothing closed this month".
- **AC-7**: Below the pipeline, the admin view shows two spend `KpiCard`s, **Total repair cost** and **Average cost**, with a `Tabs` timeframe switch (`ui/tabs.tsx`, `aria-label="Spend timeframe"`) labeled **This month** (default), **Last 90 days**, **Last 365 days**, **All time**. Filtering stays by `createdAt` (this month = current calendar month in local time; 90 and 365 days back from `fetchedAt`; all time = no filter). Spend covers active and `COMPLETED` tickets and leaves out `CANCELLED`. A null or missing `totalCost` counts as 0. Average is the rounded mean over tickets with `totalCost > 0`, and ₱0 when there are none. Amounts are formatted per *Text and formatting rules* with `tabular-nums`.
- **AC-8**: The Excel and PDF export buttons are removed from the dashboard, and the dashboard no longer imports `xlsx`, `jspdf` or `jspdf-autotable`. The packages stay in `package.json` (the analytics page's `export.ts` still uses `jspdf`; check `xlsx` with a search before removing it).
- **AC-9**: The mechanic view shows four tiles for the mechanic's own tickets: **To start** (`PENDING`, `Clock`), **In progress** (`Wrench`), **Overdue** (`AlertTriangle`, destructive tone above 0), **Waiting for sign off** (`FOR_VERIFICATION`, `ShieldCheck`), with no context line. For mechanics, Overdue counts only overdue `PENDING` and `IN_PROGRESS` tickets (the ones in their list), so the tile always matches the overdue rows they see. The overdue banner is gone (the tile replaces it).
- **AC-10**: Below the tiles, the mechanic view lists their `PENDING` and `IN_PROGRESS` tickets: overdue first, then by `targetDueDate` soonest first (no due date last), then by `updatedAt` newest first. Every row is shown (no cap), via `DataTable` with the same columns as AC-4. The **Due** column shows the overdue text, the due soon text, or nothing when there is no due date. Rows open `/repairs/:id`. Empty: `EmptyState` with the default icon, "No active repairs assigned to you right now.", and no action. The "View all repairs" link sits below the table.
- **AC-11**: Tiles are not clickable (no link, no hover affordance).
- **AC-12**: On the first load both views show one `DashboardSkeleton` (built from `ui/skeleton.tsx`) in the shape of the tiles, the list, and for admins the pipeline and spend cards. On a first load failure they show an `ErrorState` with a working "Try again", which goes back to the skeleton and fetches again.
- **AC-13**: The dashboard refreshes quietly every 3 seconds while the browser tab is visible; it pauses while the tab is hidden and fetches once when it becomes visible again. A tick is skipped while a fetch is still in flight. Polling doesn't run while the first load error is showing. Under the page header a `role="status"` line reads "Last updated 10:42 AM" (local time, 12 hour). If a background refresh fails after a successful load (for admins, either of the two fetches failing counts as a failure), the data stays on screen, the line reads "Couldn't refresh, showing data from 10:42 AM" in `text-destructive`, and no toast appears. The next successful refresh returns it to normal.
- **AC-14**: The dashboard no longer fetches audit logs. `AuditTrailWidget.tsx` and `RecentRepairsTable.tsx` are deleted.
- **AC-15**: The dashboard files use only spec 0001 components and theme tokens: no inline `style` except for a value computed at run time that a class can't hold (a bar's width, as in `TeamSection`), no legacy classes (`premium-card`, `summary-card`, `stat-card-*`, `timeframe-pill*`, `spend-metric-card`, `download-card`, `pipeline-stage-card`, `dashboard-grid`, `alert`), and lint passes with the token rules.
- **AC-16**: Both views work at 375px and 1280px with no horizontal scroll, and axe reports no serious or critical issues on `/dashboard` for each role (signed in with the seeded admin and mechanic accounts from `welinc-auth/prisma/seeds/users.seed.ts`).
- **AC-17**: The `PageHeader` title is "Dashboard" with the `LayoutDashboard` icon. Admin subtitle: "Welcome back, {name}. Here's what needs your attention." Mechanic subtitle: "Welcome back, {name}. Here's your work, most urgent first." `{name}` is `user.name`; when it is missing or empty the greeting reads "Welcome back." with no name. No hardcoded fallback name ("Victor Ramos" is removed).
- **AC-18**: If the API's `total` for either list is larger than the rows it returned, a muted line under the tiles reads "Showing the first {rows} tickets, so counts may be low." so a truncated count never looks complete.

## Decision

**Chosen option**: Option 2: Attention first rework on existing data (Facade)

Both dashboard views open with attention tiles and a list built on the client from the existing repair and history endpoints, with "waiting" defined as `FOR_VERIFICATION`, and the admin view keeps the pipeline and spend below.

**Implementation skills**: `shadcn` (`shadcn-ui/ui`, `.claude/skills/shadcn/`) · `vercel-react-best-practices` (`vercel-labs/agent-skills`, `.claude/skills/vercel-react-best-practices/`)

## Feature design

**Data model sketch**: no change. Reads the existing `RepairTicket` fields: `status`, `targetDueDate` (nullable), `updatedAt`, `completedAt` (nullable), `createdAt`, `totalCost` (admin only), `repairNumber`, `vehiclePlate`, `id`.

**API surface** (existing, unchanged):
| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/repairs` via `getRepairs` | GET | `page=1`, `limit=10000` (admin); none (mechanic) | `{ data: RepairTicket[], total }`, active statuses, mechanic scoped | bearer | 401 (logout via axios) |
| `/vrms/repairs/history` via `getRepairHistory` | GET | `page=1`, `limit=10000` | `{ data, total }`, completed and cancelled | bearer | 401 |

The admin view calls both. The mechanic view calls only `getRepairs` with no page or limit, and the backend then returns every assigned active ticket (no skip or take). History isn't needed for the mechanic tiles or list. `getAuditLogs` is no longer called from the dashboard. Both endpoints return `targetDueDate` raw from a nullable `timestamptz` column, so it arrives as an ISO timestamp or `null`; `RepairTicket.targetDueDate` is retyped to `string | null`.

**Text and formatting rules** (shared by both views):
- Day counts are whole 24 hour blocks between `fetchedAt` and the timestamp, rounded down.
- Overdue text: 0 days late gives "Due today", 1 gives "Overdue by 1 day", N gives "Overdue by N days".
- Due soon text (mechanic list, future due date): 0 days away gives "Due today", 1 gives "Due in 1 day", N gives "Due in N days".
- Updated text (waiting rows): 0 days gives "Updated today", 1 gives "Updated 1 day ago", N gives "Updated N days ago".
- Money: `₱` plus `new Intl.NumberFormat('en-PH', { maximumFractionDigits: 0 })`.
- Times: `toLocaleTimeString('en-PH', { hour: 'numeric', minute: '2-digit', hour12: true })`.

**Value sourcing**:
| Action | Value produced / displayed | Source |
|---|---|---|
| Open tile | Count | Active list length (`getRepairs`, statuses `PENDING`, `IN_PROGRESS`, `FOR_VERIFICATION`) |
| Overdue tile (admin) | Count | Active tickets with a parsable `targetDueDate` `< fetchedAt` |
| Overdue tile (mechanic) | Count | Mechanic's `PENDING` and `IN_PROGRESS` tickets with a parsable `targetDueDate` `< fetchedAt` |
| `fetchedAt` | Reference time | Client clock captured by the hook when a fetch succeeds |
| Truncation warning | Shown or not | `total > data.length` on either list response |
| Header subtitle | Text | Role from `authStore` plus `user.name` (AC-17 strings) |
| Waiting tile | Count | Active tickets with `status === 'FOR_VERIFICATION'` |
| Done this month tile | Count | History tickets with `status === 'COMPLETED'` and `completedAt` in the current month (browser local time) |
| Mechanic To start / In progress tiles | Counts | Mechanic's active list by `status` |
| Needs attention list | Rows and order | Derived from the active list: overdue sorted by `targetDueDate` ascending, then non overdue waiting sorted by `updatedAt` ascending, first 8 |
| Mechanic list | Rows and order | Mechanic's active list filtered to `PENDING` and `IN_PROGRESS`, sorted overdue first, then `targetDueDate` ascending (nulls last), then `updatedAt` descending |
| Row Due column | Overdue, due soon or updated text | `targetDueDate` or `updatedAt` against `fetchedAt`, per *Text and formatting rules* |
| Pipeline bar | Counts per status | Active plus history lists by `status` (cancelled left out, as today) |
| Spend cards | Total and average | Active plus `COMPLETED` history `totalCost` (null as 0, `CANCELLED` left out), filtered by `createdAt` against the selected timeframe and `fetchedAt` |
| Last updated line | Time | Client clock at the last successful fetch |
| Refresh failed state | Boolean | Last background fetch rejected after one success |
| Greeting | Name | `authStore` `user.name` |
| Which view | Admin or mechanic | `authStore` `user.role === 'MECHANIC'` → mechanic view, anything else → admin view (unchanged) |
| Colors | Every color | Spec 0001 tokens (`status-*`, `destructive`, `success`, `primary`) |

**Key invariants**:
- "Waiting" never means anything but `FOR_VERIFICATION` on this page.
- A ticket appears at most once in the Needs attention list.
- Counts are always computed from the same fetch and the same `fetchedAt` as the list beside them, so a tile and its list never disagree.
- No helper or component reads the clock during render; only the hook captures `fetchedAt`.
- Role routing reads the active `user.role` only, not `user.roles[]`, as today.
- A failed background refresh never replaces shown data with an error or with zeros.
- No hex, inline style or legacy class in `src/features/dashboard/`.

**Security model**: no change. The backend scopes a mechanic to their own tickets and strips costs for mechanics. Role routing stays as today: `MECHANIC` gets the mechanic view, every other role gets the admin view with spend. Who may see costs is feature 5's decision (see Follow-up).

**Failure and edge cases**:
- No `targetDueDate`: never overdue, sorted last in the mechanic list, no due line.
- Due less than one day ago: "Due today", still counted overdue.
- History fetch fails but the active fetch works (admin): the whole first load shows `ErrorState`. Both are fetched together, so a half drawn dashboard never looks complete.
- Zero tickets at all: tiles show 0, the list shows the positive empty state, the pipeline shows an empty track with "No tickets yet", and spend shows ₱0.
- Unknown status value: `StatusBadge` renders it in slate with its raw text (spec 0001); it is left out of the pipeline.
- Clock skew between browser and server: overdue may be off by minutes; accepted.

**Configuration required**: none.

**Critical test scenarios**:
- Happy path: seed tickets that are overdue, waiting, both, and completed this month; as admin, the tiles show the right counts (the both ticket in two tiles) and the list shows overdue then waiting, with each ticket once. Verifies **AC-1**, **AC-2**, **AC-3**, **AC-4**
- Mechanic: as a mechanic, only their tickets count; the list is overdue first, then by due date, and has no `FOR_VERIFICATION` rows. Verifies **AC-9**, **AC-10**
- Empty: with nothing overdue or waiting, the positive empty state shows. Verifies **AC-5**
- Failure: block the network after the first load; the data stays and the line turns to "Couldn't refresh"; block it before the first load and `ErrorState` shows, and "Try again" recovers. Verifies **AC-12**, **AC-13**
- Spend: switch through the four timeframes; the labels read correctly and the totals change. Verifies **AC-7**
- Network panel: no `audit-logs` request from `/dashboard`. Verifies **AC-14**
- Refresh: hide the tab and no requests fire; show it and one fetch runs. Verifies **AC-13**
- Edge text: tickets due in 5 hours, 5 hours late, and updated an hour ago read "Due today", "Due today" (counted overdue) and "Updated today"; a ticket with `targetDueDate: null` is never overdue. Verifies **AC-1**, **AC-10**
- Mechanic overdue: an overdue `FOR_VERIFICATION` ticket counts in Waiting but not in the mechanic's Overdue tile. Verifies **AC-9**
- 375px and 1280px for both roles, with axe. Verifies **AC-15**, **AC-16**

## Build plan

Facade: UI only, on the existing endpoints, one view at a time so each lands working.

1. Retype `RepairTicket.targetDueDate` as `string | null`, and add an optional `icon` to `DataTable`'s `empty` prop (passed to `EmptyState`). Satisfies **AC-1**, **AC-5**
2. Add `src/features/dashboard/lib/attention.ts` with pure helpers that all take `now` (the hook's `fetchedAt`), never reading the clock: `isOpen`, `isOverdue(ticket, now)`, `isWaiting`, `wholeDays`, `attentionList(active, now, limit)`, `mechanicWorkList(active, now)`, `completedThisMonth(history, now)`, `spendFor(tickets, timeframe, now)`, and the text and money formatters. Satisfies **AC-1**, **AC-3**, **AC-4**, **AC-7**, **AC-9**, **AC-10**
3. Rewrite `useDashboardMetrics` as `useDashboardData({ includeHistory })`: fetch active (and history for admins) together, drop the audit fetch, poll every 3 seconds while the tab is visible and no fetch is in flight, and return `{ active, history, totals, state: 'loading' | 'error' | 'ready', fetchedAt, refreshFailed, truncated, retry }`. Keep the React Compiler rules (no sync `setState` in effects; set state in `.then` with a `cancelled` flag). Satisfies **AC-12**, **AC-13**, **AC-14**, **AC-18**
4. Build shared dashboard pieces: `AttentionTiles` (a `KpiCard` grid), `TicketAttentionTable` (`DataTable` with the AC-4 columns and mobile mapping, `onRowClick` to detail, "View all repairs" below), `LastUpdated` status line, `TruncationNote`, and `DashboardSkeleton`. Satisfies **AC-2**, **AC-4**, **AC-11**, **AC-12**, **AC-13**, **AC-18**
5. Rebuild `AdminDashboard`: header, `LastUpdated`, four tiles, Needs attention list with its empty state and "View all repairs". Satisfies **AC-2**, **AC-4**, **AC-5**, **AC-17**
6. Restyle `RepairProgressChart` as the token based pipeline bar with its heading, caption, text legend and `role="img"` label, and rebuild the spend section as two `KpiCard`s with the `Tabs` timeframe switch. Remove the exports and their imports. Satisfies **AC-6**, **AC-7**, **AC-8**
7. Rebuild `MechanicDashboard` on the same hook and pieces: header, four tiles, the urgency ordered work list, empty state, banner removed. Satisfies **AC-9**, **AC-10**, **AC-11**, **AC-17**
8. Delete `AuditTrailWidget.tsx` and `RecentRepairsTable.tsx`. AC-15 binds the dashboard files; removing now unused legacy classes from `index.css` is best effort, and only for classes nothing else uses. Satisfies **AC-14**, **AC-15**
9. Run lint, typecheck and build, then check both roles at 375px and 1280px in Playwright with axe. Satisfies **AC-15**, **AC-16**

## Consequences

**Positive**:
- The first screen shows the urgent work for both roles, and "waiting" has one meaning.
- Mechanics see overdue work at the top of their list, not in a banner they scroll past.
- Less traffic every 3 seconds (no audit log), fewer heavy libraries in the dashboard bundle, and two dead files gone.
- The spend label bug is fixed.

**Negative / tradeoffs**:
- Counts are computed in the browser from up to 10000 rows per list, every 3 seconds. That works at fleet scale today, but it will need a summary endpoint as history grows.
- "Waiting" order is approximate (`updatedAt`), so a waiting ticket that gets a remark jumps back in the queue.
- Exports leave the dashboard. Admins who used them must use the analytics PDF report until feature 15 decides on an Excel export.
- Tiles aren't clickable yet, so a count can't open its exact set until feature 11 adds URL filters.
- `CUSTOMER_SUPPORT` and `OPERATIONS` still see costs on the dashboard until feature 5 decides otherwise.

**Neutral**:
- No backend, API or env change; no migration.
- Spend still filters by `createdAt`, so its meaning is unchanged from today.

## Follow-up

- [ ] Feature 11 (repair list refresh): add URL filters (`?status=`, `?overdue=1`) so the dashboard tiles can become links.
- [ ] Feature 15 (analytics refresh): decide whether an Excel repair export belongs on the analytics page, now that the dashboard exports are gone.
- [ ] Feature 5 (permission matrix): decide whether `CUSTOMER_SUPPORT` and `OPERATIONS` see repair costs; the dashboard spend section should follow it.
- [ ] When history grows or the 3 second poll shows up in profiling, spec a `GET /vrms/repairs/summary` endpoint (and a `verificationRequestedAt` column for exact waiting times). Needs its own cross repo spec.
- [ ] Priority isn't stored in the database, so the dashboard can't sort or count by it. Revisit the attention order once priority is persisted.
- [ ] VRMS-41 (Chief Mechanic dashboard) should reuse these tiles and the attention list, with "waiting" as its verification queue.
