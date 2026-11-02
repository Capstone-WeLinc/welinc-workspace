# Verify: Dashboard · spec 0002 · updated 2026-10-22
_Steps derived from spec 0002 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Sign in through the portal (`http://localhost:8000/login`) with `vrms.admin@welinc.com` (admin) or `mech.juan@welinc.com` (mechanic), passwords in `welinc-auth/prisma/seeds/users.seed.ts`.

> **Differs from the spec (owed to `/architect`):** the pipeline was changed during the build at the engineer's request. AC-6 in `index.md` still says "All tickets" with `status-*-fg` colors. As built: open tickets plus `COMPLETED` this month, caption "Open tickets and this month's completions", `chart-*` colors, hover tooltips and legend highlighting. The AC-6 steps below check what was built.

## UI / manual

### Admin
- [x] Open `/dashboard` as admin → title "Dashboard", subtitle "Welcome back, {name}. Here's what needs your attention." → AC-17
- [x] Clear `name` on the stored user (or use an account without one) → the subtitle reads "Welcome back. Here's what needs your attention.", with no "Victor Ramos" fallback → AC-17
- [x] Tiles read Open, Overdue, Waiting for sign off, Done this month, in that order, with no context line. Four in a row at 1280px, two by two at 375px → AC-2
- [x] Open = the number of tickets on `/repairs` (statuses PENDING, IN_PROGRESS, FOR_VERIFICATION) → AC-1, AC-2 (Value sourcing: Open tile)
- [x] Overdue tile is red when above 0. Set every open ticket's `targetDueDate` in the future or null → it reads 0 in the default navy tone → AC-2 (Value sourcing: Overdue tile)
- [x] A ticket with `targetDueDate: null` never counts as overdue; one due 5 hours ago counts and reads "Due today" → AC-1
- [x] Waiting = the number of FOR_VERIFICATION tickets. A FOR_VERIFICATION ticket that is also overdue counts in both Overdue and Waiting → AC-1, AC-3 (Value sourcing: Waiting tile)
- [ ] Complete a ticket now → Done this month goes up by 1 after the next refresh. A ticket completed last month does not count. Check near midnight on the 1st in a different browser timezone: the month follows browser local time → AC-2 (Value sourcing: Done this month)
- [x] Needs attention: overdue rows first (oldest due date first), then waiting rows that are not overdue (oldest `updatedAt` first), at most 8, each ticket once → AC-3, AC-4 (Value sourcing: Needs attention list)
- [x] Due column: overdue rows read "Overdue by N days" (or "Due today") in red, waiting rows read "Updated today", "Updated 1 day ago" or "Updated N days ago" → AC-4 (Value sourcing: Row Due column)
- [x] Click a row → opens `/repairs/:id`. At 375px the rows are cards and the card opens the ticket → AC-4
- [x] "View all repairs" sits below the table and goes to `/repairs` → AC-4
- [x] With nothing overdue or waiting → the check circle empty state "Nothing needs your attention" / "No overdue tickets and nothing waiting for sign off.", with "View all repairs" still below → AC-5
- [x] Pipeline: heading "Pipeline", caption "Open tickets and this month's completions". Segments for Pending, In progress, For verification, and Completed this month; widths match the counts; a 0 segment is not drawn but its legend item shows 0 and 0% → AC-6 (as built) (Value sourcing: Pipeline bar)
- [x] Hover a segment → a tooltip "Label: N (P%)", and the other segments and legend items fade. Hover a legend item → its segment stays bright and the rest fade → AC-6 (as built)
- [x] The pipeline's accessible name (role img) lists every status and count; with all four at 0 the track is empty and reads "Nothing open and nothing completed this month" → AC-6 (as built)
- [x] Spend: tabs "This month" (default), "Last 90 days", "Last 365 days", "All time" with `aria-label="Spend timeframe"`. Totals change as you switch. At 375px the tabs sit 2 by 2 inside the gray list, with no scrollbar → AC-7
- [x] Spend values: a CANCELLED ticket with a cost never adds to the total; a ticket with a null cost adds 0 and is left out of the average; amounts read like "₱2,033,059" → AC-7 (Value sourcing: Spend cards)
- [x] No Excel or PDF export buttons on the dashboard → AC-8
- [x] Tiles have no link, pointer cursor or hover change → AC-11

### Mechanic
- [x] Open `/dashboard` as a mechanic → subtitle "Welcome back, {name}. Here's your work, most urgent first." → AC-17
- [x] Tiles: To start, In progress, Overdue, Waiting for sign off. Overdue counts only overdue PENDING and IN_PROGRESS tickets, so an overdue FOR_VERIFICATION ticket counts in Waiting but not in Overdue → AC-9 (Value sourcing: Overdue tile, mechanic)
- [x] No overdue banner → AC-9
- [x] My work lists only PENDING and IN_PROGRESS tickets (no FOR_VERIFICATION rows), no cap: overdue first, then due date soonest (none last), then newest update → AC-10 (Value sourcing: Mechanic list)
- [x] Due column: "Overdue by N days", "Due today", "Due in 1 day", "Due in N days", or empty without a due date → AC-10
- [x] With no PENDING or IN_PROGRESS tickets → empty state "No active repairs assigned to you right now." with no action → AC-10
- [x] Only the mechanic's own tickets count (compare with a second mechanic). During the build, `mech.juan` saw all 102 active tickets; check whether that's the seed or missing backend scoping → AC-9 (Value sourcing: Mechanic tiles)

### Both views: states and refresh
- [x] Throttle the network → one skeleton shaped like the tiles and list (plus pipeline and spend for admins), not a spinner → AC-12
- [x] Block `**/vrms/repairs**` and reload → error state with "Try again"; unblock and click it → skeleton, then data → AC-12
- [x] Under the header, a status line reads "Last updated 10:42 AM" style (12 hour, local) → AC-13 (Value sourcing: Last updated line)
- [x] After a load, block `**/vrms/repairs**` and wait 3s → the line turns red: "Couldn't refresh, showing data from …", the data stays, no toast. Unblock → it returns to "Last updated" on the next tick → AC-13 (Value sourcing: Refresh failed state)
- [x] As admin, block only `**/vrms/repairs/history**` after a load → the same "Couldn't refresh" line (either fetch failing counts) → AC-13
- [x] Hide the tab (switch tabs) for 30s → no `/vrms/repairs` requests. Show it → exactly one fetch right away, then every 3s → AC-13
- [x] Network panel on `/dashboard` → no `audit-logs` request → AC-14
- [x] When an API `total` is larger than the rows returned (for example, lower the admin limit locally), "Showing the first {rows} tickets, so counts may be low." appears under the tiles → AC-18 (Value sourcing: Truncation warning)
- [ ] Every time based value (overdue, day counts, this month) uses the fetch time: leave the page open across midnight; the tiles and Due text change only when the next fetch lands, and always agree with each other → AC-1 (Value sourcing: fetchedAt)
- [x] Both roles at 375px and 1280px: no horizontal scroll; axe reports no serious or critical issues → AC-16

## Commands
- [x] `npm run lint` in `welinc-web-vrms` → passes with the token rules → AC-15
- [x] `npm run typecheck` and `npm run build` in `welinc-web-vrms` → pass → AC-15
- [x] `grep -rn "style=\|premium-card\|summary-card\|stat-card\|timeframe-pill\|dashboard-grid" welinc-web-vrms/src/features/dashboard` → no matches → AC-15
- [x] `ls welinc-web-vrms/src/features/dashboard/components` → no `AuditTrailWidget.tsx` or `RecentRepairsTable.tsx` → AC-14
- [x] `grep -rn "xlsx\|jspdf" welinc-web-vrms/src/features/dashboard` → no matches → AC-8

## Acceptance-criteria coverage
- AC-1: admin overdue and null due steps, fetchedAt step · AC-2: admin tiles steps · AC-3: waiting and Needs attention steps · AC-4: Needs attention, Due column, row click, View all steps · AC-5: empty state step · AC-6 (as built, differs from spec): three pipeline steps · AC-7: two spend steps · AC-8: no exports step, xlsx/jspdf grep · AC-9: mechanic tiles, banner, scoping steps · AC-10: mechanic list, Due, empty steps · AC-11: tiles step · AC-12: skeleton and error steps · AC-13: status line, refresh failure, history failure, hidden tab steps · AC-14: network step, ls command · AC-15: lint, build, grep commands · AC-16: 375/1280 axe step · AC-17: subtitle steps · AC-18: truncation step
