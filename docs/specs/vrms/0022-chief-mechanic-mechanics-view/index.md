# 0022. Chief dashboard rework: a Team section in place of tiles, three tables and the pipeline

**Date**: 2026-11-04
**Updated**: 2026-11-05 (design review: the `/mechanics` page is replaced by a Team section on a reworked Chief dashboard; second pass the same day: a verification summary on top, a Team roster with workload bars and a Busy and Free switch)
**Status**: Accepted

## Summary

The Chief Mechanic's dashboard leads with one summary: how many repairs wait for verification, the oldest one, and a button to start verifying it. Below it sit the For verification queue, the Chief's own work, and a **Team** roster that shows, person by person, how loaded each mechanic is, which truck they are on, and what is overdue. It serves the three real moments of a shop foreman's day: the morning lineup, covering for an absent mechanic (Reassign and Unassign from a person's open list), and spotting stuck or piled up work. The four count tiles, the Needs attention table and the pipeline bar are gone, and the other numbers shrink to one quiet line. The separate `/mechanics` page built first is removed, so the nav and phone tab bar stay as they were.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As a Chief Mechanic at the morning lineup, I want to see each mechanic's trucks and their status on my phone, so I can run through the day person by person.
- As a Chief Mechanic covering for an absent mechanic, I want to open that person's tickets and move each one to someone with room, without opening every ticket.
- As a Chief Mechanic, I want overdue and long waiting work to stand out, and the busiest people at the top, so stuck work gets noticed.
- As a Chief Mechanic, I want my dashboard to lead with what needs my verification and say each thing once, so I know where to look first.
- As an Admin, I want to choose who sees the team view through the permission matrix.

**Acceptance criteria**:

*Permission and reads (backend; AC-1, AC-3 and AC-4 are built)*
- **AC-1**: `catalog.ts` has the key `mechanics.view` (Admin on, Chief Mechanic on, Mechanic off), label "See the team's workload", description "See the Team section on the dashboard: who holds which tickets, and their open tickets.", mirrored in web `keys.ts`. The startup backfill adds its rows.
- **AC-2**: `GET /vrms/mechanics/roster` accepts `mechanics.view` or `users.manage` and returns every active roster person plus every inactive one holding at least one open ticket. Each row has `authUserId`, `mechanicId` (the `mechanics.id` that ticket assignments use), `name`, `email`, `role`, `isActive`, `occupied`, `total` and `byStatus`. A caller with neither key gets 403.
- **AC-3**: `GET /vrms/mechanics/:authUserId/open-tickets` also accepts `mechanics.view`. `workload`, `open-work`, `release-tickets` and `sync` stay `users.manage` only.
- **AC-4**: `mechanics.role` (`MECHANIC`, `CHIEF_MECHANIC` or empty, CHECK in the database) is written by `ensure`, `sync` and `refreshOne` from the welinc-auth VRMS role; a person who loses VRMS access keeps their last known role.

*The Chief dashboard*
- **AC-5**: The Chief view is still chosen as in spec 0015 AC-11 and AC-12. It shows a plain header ("Dashboard", today's date and the last updated line), one summary block (AC-7), then three sections: **For verification**, **My work** and **Team**. It has no count tiles, no Needs attention section and no pipeline, and it no longer fetches repair history. The Admin and Mechanic dashboards are unchanged.
- **AC-6**: The summary block spans the full width above the sections. Below 1280px the sections stack in the order For verification, My work, Team. From 1280px there are two columns: a narrow left column (two fifths) with For verification above My work, and a wide right column (three fifths) with Team. The reading and tab order is summary, For verification, My work, Team at every width.
- **AC-7**: The summary block says, in this order: the full count of the For verification queue (the tickets with `can.verify`, before the cut to 8) in large type with "repairs waiting for verification" ("repair" for 1); under it the oldest ticket's `PlateChip`, its mechanics' names and "waiting <time>" (`signOffNames`, `timeInStatus`); a **Verify the oldest** button that opens that ticket; and, after a hairline, one quiet line of numbers: "N working · N not started · N free", counted over roster rows minus the viewer (working is `occupied`; not started is `total > 0` and not `occupied`; free is `isActive` and `total` 0), then "N with no mechanic" when some open tickets have none. While the roster has not loaded the three team numbers are left out. A Chief without `mechanics.view` sees "N in my work" instead. With nothing in the queue the block reads "Nothing waiting for verification." with a check icon and no button. The For verification heading carries the full queue count when it is above 0, My work carries its length when above 0, and Team carries its counts on the Busy and Free tabs (AC-10). The No mechanic group and fallback rows (AC-15) are not counted in the line. The big number is the text color; only overdue work and long waits use red or amber.
- **AC-8**: My work, the Team "No mechanic" group and the person dialog's links keep one shared ticket row: line 1 is the `PlateChip` and the `StatusBadge`; line 2, in muted text, is the ticket number, then the facts (the due label, or nothing when `dueLabel` returns none). An overdue ticket shows the overdue text in the destructive color. The For verification rows are their own denser row: line 1 is the `PlateChip`, the mechanics' names (`signOffNames`: two names then "+N more", or "No mechanic") and the wait time at the right (`timeInStatus`); line 2, in muted text and cut to one line, is the ticket's `issueDescription`. The wait time is muted under 24 hours, amber and medium weight from 24 hours, and destructive from 48 hours (`waitTone`; a missing or unreadable date stays muted). The ticket number and the full names are in the row's hover title. Every row is one link to `/repairs/:id`, at least 44px tall on phones.
- **AC-9**: For verification keeps spec 0015's rules (AC-14 to AC-16: tickets with `can.verify`, oldest wait first, at most 8, the Chief's own tickets left out), and "See all" to `/repairs?status=FOR_VERIFICATION` shows only when the queue is longer than 8. My work keeps AC-17's list and order. An empty section shows one muted line ("Nothing to verify." / "Nothing assigned to you."), not the large empty block.

*The Team section*
- **AC-10**: Team shows, in this order: (1) a **No mechanic** panel above the Team panel, only when some open ticket has no mechanic assigned (`hasNoMechanic`), listing those tickets as rows (AC-8); (2) the **Team** panel, whose header holds a Busy and Free switch (tabs) with a count on each, Busy selected at first. Busy lists one row per roster person with `total > 0` (AC-12); Free lists roster people with `isActive` and `total` 0 (AC-13). An inactive person with `total` 0 shows nowhere. The viewer (the roster row whose `authUserId` equals the auth store's `user.id`, which `features/auth/lib/session.ts` sets from the token `sub`) is left out everywhere. The sort and the number on each row come from the roster row; a person's trucks and workload bar come from the dashboard's open tickets whose `mechanics[].id` includes that person's `mechanicId`.
- **AC-11**: People are sorted inactive first, then anyone with an overdue chip ticket (`isOverdue` at the snapshot's `fetchedAt`), then highest roster `total`, then name (`localeCompare`). Occupied is never a sort key, so starting or pausing work never moves a row. The order is worked out again on every refresh.
- **AC-12**: A Busy row is one button that opens and closes the person's trucks in place (`aria-expanded`); the row is not a link. It shows, left to right: a chevron and the name (hover `title` is the email), with a small line under the name made of "Not on the roster yet" for a fallback row, "Inactive" when `isActive` is false or "Chief mechanic" when `role` is `CHIEF_MECHANIC`, then the email only when two people on the list share a name (`sharedNames`), then "On <plate>" for the truck they have In progress (the one running longest, "+N" when there are more, `onNowOf`); a workload bar; the roster `total`; and one note. The bar has one segment per group of the person's open tickets (`mixOf`): In progress including Outsourced (`primary`), For verification (`chart-4`) and Not started, the rest (a light tint of `primary`), all scaled to the busiest person on the list so rows compare, with a one line key above the list and the counts as hidden text for screen readers. The note is the first that applies: "N overdue" (destructive color), "N for verification" (violet text), "Nothing started" when nothing is In progress, else empty. There is no Occupied, Waiting or Free word and no pill; the bar says it. Opened, the row lists up to 3 trucks, each a link to the ticket showing the `PlateChip`, the status and the time in that status ("On hold" and "4 days"), with the overdue text in the destructive color in place of the time when overdue. The time text comes from the `timeInStatus` helper (under an hour, N h, N days, or "time unknown" when `statusChangedAt` is missing or unreadable), measured to `fetchedAt`; `waitingText` is built on it so both share one set of thresholds. Trucks go overdue first, then by `openStatusRank` (the Users page dialog's order), then oldest `statusChangedAt`, a missing date last. Under the trucks a link style button opens the dialog (AC-14): "See all N and reassign" when the roster `total` is above 3, else "Reassign or unassign"; a fallback row has no such button. Focus order in a row: the row button, its trucks, then the dialog button; each at least 44px tall on phones.
- **AC-13**: The Free tab lists the free people sorted by `localeCompare`, in two columns from 640px (one below), each with a small green dot and the name (a name two people share shows its email under it, `sharedNames`), all of them with no cut off. With no free people it shows "Nobody is free right now."; with no one in Busy it shows "Nobody has open work."; with nobody on the roster but the viewer, Team shows "No mechanics yet." and no tabs.
- **AC-14**: The dialog button in an opened person row (AC-12) opens a dialog (a sheet on phones) titled "<name>'s open tickets" with the Users page open tickets list (`MechanicOpenTickets user={{ id: authUserId, name }}`, not read only), loaded fresh from `open-tickets`, which wins over the chips if they briefly differ: its Reassign and Unassign show when the viewer holds `ticket.assign` and save through `PUT /vrms/repairs/:id/assignments` with the stale check. Its `onChanged` refreshes both the dashboard tickets and the roster at once. The dialog keeps the person it opened with, so it stays open if they drop off the list.
- **AC-15**: Team refreshes with the rest of the dashboard (every 3 seconds while visible). If the roster fails to load, Team shows its own error with Try again and the other sections still render; a failed refresh with rows on screen keeps them. A ticket whose mechanic is missing from the roster (a sync lag) still shows its trucks under a fallback row named from the ticket's `mechanics[].name`, opening in place like the others but with no dialog button, placed after the roster people. Team shows only on the Chief view (spec 0015 AC-11), so a Mechanic granted `mechanics.view` sees no Team on the Mechanic dashboard.

*Removed and unchanged*
- **AC-16**: The `/mechanics` route, page, filters, "Sort again", its sidebar item and the phone nav changes made for it (the tab cap, Knowledge base in the user menu, the hidden breadcrumb entry) are removed; the nav, tab bar, user menu and breadcrumb behave exactly as before feature 63.
- **AC-17**: Admin's Users page (Work column, filter, Open tickets with Unassign and Reassign), the Admin dashboard and the Mechanic dashboard behave exactly as before.
- **AC-18**: The Chief dashboard passes axe at 375px and 1280px in its loaded state, with every section empty, with the roster failing, and with the dialog open, on both the Busy and Free tabs, using theme tokens only.

## Decision

**Chosen option**: Option 1: rework the Chief dashboard into three sections, with a Team section built from the dashboard's open tickets joined to the VRMS roster, and remove the `/mechanics` page.

The backend from the first build stays (the key, the roster read, the role column, `open-tickets` widened); the roster gains `mechanicId`. The web replaces the tiles, three tables and pipeline with one shared ticket row and a Team section, and deletes the `/mechanics` page and its nav changes.

**Implementation skills**: `vercel-react-best-practices` (`vercel-labs/agent-skills`, `.claude/skills/vercel-react-best-practices/`) · `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) for the one roster field

## Feature design

**Screens and states** (Chief dashboard only):

| Section | Shows | Empty | Error |
|---|---|---|---|
| Header | "Dashboard", today's date, last updated line, truncation note | n/a | dashboard error with Try again (as today) |
| Summary block | verification count, the oldest ticket, Verify the oldest, one line of team numbers | "Nothing waiting for verification." | with the dashboard |
| For verification · N | up to 8 rows with the issue line, "See all" above 8 | one muted line | with the dashboard |
| My work · N | ticket rows | one muted line | with the dashboard |
| Team · Busy N and Free N | No mechanic panel, then Busy rows or the Free list | "No mechanics yet." | its own error with Try again |
| Person dialog | `MechanicOpenTickets` with actions by `ticket.assign` | its existing copy | its existing copy |

**Data model**: no change beyond the built `mechanics.role` column.

**API surface**:

| Endpoint | Method | Change | Auth |
|---|---|---|---|
| `/vrms/mechanics/roster` | GET | add `mechanicId` to each row | `mechanics.view` or `users.manage` |
| `/vrms/mechanics/:authUserId/open-tickets` | GET | none (built) | `users.manage` or `mechanics.view` |
| `/vrms/repairs/:id/assignments` | PUT | none; the dialog's Reassign and Unassign use it | as today (`ticket.assign` on the server) |

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| For verification rows, wait time, issue line | as spec 0015 AC-14 and AC-15, plus the issue | `verificationQueue`, `timeInStatus`, the ticket's `issueDescription` |
| My work rows, due label | as spec 0015 AC-17 | `mechanicWorkList`, `dueLabel` |
| Summary and heading counts | numbers | length of the full lists (For verification before the 8 cut) |
| Summary, the oldest ticket | plate, names, wait, link target | first of `verificationQueue`; names from `signOffNames` |
| Wait colour | muted, amber or red | `waitTone` on `statusChangedAt` at `fetchedAt` (fixed 24 and 48 hours) |
| Team people | name, email, role, active, Occupied, `total` | roster rows (`GET /vrms/mechanics/roster`) |
| Team, who is the viewer | the row to leave out | roster `authUserId` equal to `useAuthStore` `user.id` (set from the token `sub` in `features/auth/lib/session.ts`) |
| Team, a person's trucks | plate, status, ticket id | dashboard open tickets (`active`) whose `mechanics[].id` includes the person's `mechanicId` |
| "See all N and reassign" | N | roster `total` |
| Workload bar | segment sizes | `mixOf` over the person's joined open tickets: In progress and Outsourced, For verification, the rest; scaled to the largest person total on the list |
| "On <plate>" | plate | `onNowOf`: the person's In progress tickets, longest running first |
| Person note | overdue, for verification, nothing started | `mixOf` counts (`overdue` from `isOverdue` at `fetchedAt`) |
| Ticket chip, time in status | "On hold · 4 days" | new `timeInStatus(statusChangedAt, fetchedAt)`; `waitingText` reuses it |
| Chip order | order | overdue, then `openStatusRank`, then `statusChangedAt` |
| Ticket chip, overdue | overdue text | `isOverdue` and `overdueText` from `lib/utils/due` with `fetchedAt` |
| No mechanic group | tickets | open tickets where `hasNoMechanic` is true |
| Sort | order | AC-11: roster `isActive`, overdue chips at `fetchedAt`, roster `total`, name |
| Summary line | working, not started, free | roster `occupied`, `total` and `isActive`, minus the viewer |
| Free tab | names | roster rows with `isActive` and `total` 0, minus the viewer |
| Missing roster person | name on a fallback row | the ticket's `mechanics[].name` |
| Dialog actions | Reassign, Unassign | `MechanicOpenTickets`' own `useCan('ticket.assign')` |
| Team visible at all | section shown | `useCan('mechanics.view')` |

**Key invariants**:
- Occupied still comes only from `isOccupied` (via the roster row), never worked out again in the browser.
- The Team join uses `mechanicId`, never the name.
- Two row components on the Chief dashboard: the shared ticket row (My work, No mechanic) and the For verification row; no new table. Each number is said once: the summary line holds the team counts and the tabs hold the people counts.
- The Team section shows only with `mechanics.view`; without it the Chief view has the summary, For verification and My work only, laid out the same way.
- No role name check: the Chief badge reads the row's `role` as data, and visibility reads keys.

**Security model**: `mechanics.view` exposes names, emails and the plates and statuses of open tickets, all of which the Chief already sees through `ticket.view_all`. Reassign and Unassign are checked on the server (`ticket.assign`), the UI only hides them. A Mechanic gets 403 on the roster and never sees Team.

**Recommended internal choices** (made here, with the runner up):
- Roster loading: reuse the built `useMechanicRoster` hook (its own poll and refresh failure handling), moved into `features/dashboard/`, rather than adding the roster to `useDashboardData`'s `Promise.all`. A roster failure then never blanks the dashboard. Runner up: one combined fetch, simpler but all or nothing.
- The join, groups, order, summary and chip text live in a pure `features/dashboard/lib/team.ts` with Vitest cases, like `attention.ts`. Counts come from the roster rather than the join, so a truncated ticket list or poll lag only changes which chips show, never who counts as busy or free.
- `useMechanicRoster` moves with its wording updated, and any tests move with it.
- The ticket row is a new `DashboardTicketRow` in `features/dashboard/components/`; `VerificationQueueTable` and `TicketAttentionTable` stay for the Admin dashboard only (`VerificationQueueTable` is deleted if nothing else uses it).
- 3 trucks per opened person; the Free tab shows everyone, because a sentence of up to 46 names read as a wall of text.
- The wait colours use fixed limits in code (`SIGN_OFF_STALE_HOURS` 24 and `SIGN_OFF_LATE_HOURS` 48), not the Admin Settings thresholds. Runner up: read them from Thresholds; left for follow up so this needs no new setting.
- `RepairProgressChart` and history fetching stay for the Admin dashboard; the Chief view passes `includeHistory: false`.

**Critical test scenarios**:
- Lineup: the seed Chief opens the dashboard at 375px; Team lists people with a workload bar and the truck each is on, the Chief is not in it, the Free tab lists the rest. Verifies **AC-6**, **AC-10**, **AC-12**, **AC-13**.
- Absent mechanic: open a person row with 4 tickets, see 3 trucks and "See all 4 and reassign", open the dialog, Reassign one ticket; the dashboard refreshes and the counts move. Verifies **AC-12**, **AC-14**.
- Steady order: a mechanic presses Start work; their row stays put and turns Occupied. Assigning them a new ticket moves them up. Verifies **AC-11**.
- Stuck work: a ticket past its due date puts its person above people with more tickets and shows red overdue text. Verifies **AC-11**, **AC-12**.
- Verification wait: a ticket For verification for 30 hours reads amber and one for 50 hours reads red; the summary names the oldest and Verify the oldest opens it. Verifies **AC-7**, **AC-8**.
- No mechanic: unassign the last mechanic from an In progress ticket; it shows in the No mechanic group. Verifies **AC-10**.
- Roster down: block the roster read; the summary, For verification and My work render, Team shows Try again. Verifies **AC-15**.
- Regression: the Admin and Mechanic dashboards and the Users page are unchanged; `/mechanics` is gone and the nav matches before. Verifies **AC-16**, **AC-17**.

## Build plan

Tracer Bullet, starting from the first build (backend kept, the `/mechanics` web code removed).

Steps 2 and 3 describe the first layout; step 6 replaces their layout details.

1. **Clear the ground**: delete `features/mechanics/` except the roster hook (move `useMechanicRoster` to `features/dashboard/hooks/`), the `/mechanics` route, the sidebar item, the tab cap, `getPhoneMenuItems`, the user menu item and `HIDDEN_TRAILS`, with their tests; drop the `readOnly` prop from `MechanicOpenTickets` if nothing uses it. Backend: `mechanicId` in `rosterWithOpenStatuses`' select, `RosterRow` and the web `MechanicRosterRow`, plus the new key label. Satisfies **AC-1**, **AC-2**, **AC-16**.
2. **Thin thread, the new layout**: `DashboardTicketRow`; Chief view without tiles, Needs attention, pipeline and history; Sign off and My work on the shared row with counts in the headings and one line empty states; the two column layout with a Team placeholder fed by the roster join (names only). Satisfies **AC-5** to **AC-9**.
3. **The Team section**: `timeInStatus` (with `waitingText` rebuilt on it) and `lib/team.ts` (join with fallback rows, No mechanic group, sort, summary, chip order and text, free names) with Vitest cases; person rows with chips, "+N more", the Free line, Team's loading and error states. Satisfies **AC-7**, **AC-10** to **AC-13**, **AC-15**.
4. **Act from the list**: the person dialog with `MechanicOpenTickets` and its actions, refreshing the dashboard after a change. Satisfies **AC-14**.
5. **Sweep**: update the dashboard tests that assumed tiles, Needs attention or the pipeline on the Chief view; check the Admin and Mechanic dashboards and the Users page; axe at 375px and 1280px in the AC-18 states; lint, typecheck, build and tests in both repos. Satisfies **AC-17**, **AC-18**.
6. **Design review pass (2026-11-05)**: replace the first layout with the verification summary; the For verification row with the issue line and `waitTone`; and a Team roster (rows with the `mixOf` workload bar and `onNowOf`, opening in place, Busy and Free tabs), with Vitest cases for `waitTone`, `mixOf` and `onNowOf`. Satisfies **AC-5** to **AC-9**, **AC-12**, **AC-13**.

## Consequences

**Positive**:
- The Chief's dashboard answers the foreman's real questions (who holds which truck, what is stuck, who is free) in one place, on a phone.
- Covering for an absent mechanic takes two taps per ticket instead of opening each ticket.
- Fewer things on screen, each said once, in one row style that follows design.md (plate first).
- No new page or nav item, so the phone nav question for Settings never comes up.

**Negative / tradeoffs**:
- A large share of the first build's web code is thrown away (the page, filters, Sort again, phone nav changes).
- The Chief loses the pipeline bar and the Open and Overdue totals as numbers; trends stay on Analytics, which is Admin only by default.
- Two pollers on the dashboard (tickets and roster), so for up to 3 seconds a new assignment can show under a fallback row before the roster catches up.
- The Chief dashboard and the Admin dashboard now differ more, so a shared change touches two layouts.
- Spec 0015's AC-13, AC-14 (table form), AC-18 and AC-19 (history fetch) no longer describe the Chief view.
- The workload bar counts the dashboard's joined open tickets while the number beside it is the roster `total`, so for a few seconds after a change they can differ, and a truncated ticket list shortens the bar.
- The 24 and 48 hour wait colours are fixed in code until the Admin thresholds can hold them.
- The Free people are one tap away instead of on the page, so a Chief looking for someone with room must open the Free tab.

**Neutral**:
- No migration beyond the built `mechanics.role` column.
- `mechanics.view` keeps its name; only its label and description change, and the startup backfill needs nothing new.

## Follow-up

- [ ] **Spec 0015**: an `Updated` line notes that AC-13, AC-14's table form, AC-18 and AC-19's history fetch are replaced by this spec for the Chief view (added with this update).
- [ ] **`/sync`**: record in `welinc-web-vrms/AGENTS.md` that the Chief dashboard uses `DashboardTicketRow` and `lib/team.ts`, and that `mechanics.view` gates the Team section; in `welinc-backend-vrms/AGENTS.md` that `mechanics.role` is written only by the roster writers.
- [ ] **Polish (ask first)**: `break-ui` on Team (many people, long names, a person with 20 tickets, no free people) and `web-design-guidelines` after the build.
- [ ] **Thresholds**: decide whether the 24 and 48 hour wait limits move into the Admin Settings thresholds.
- [ ] **Axe after the second pass**: AC-18 ran on the first layout; run it again at 375px and 1280px on the new one (both tabs, the dialog, the empty and roster failing states). `verify.md` is rewritten for the new layout.
- [ ] **For the PM (Jira)**: no ticket yet; this replaces the Chief half of feature 57 and reworks the Chief dashboard from spec 0015.
