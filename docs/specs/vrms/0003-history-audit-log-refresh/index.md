# 0003. Repair history as an archive, audit log as a timeline

**Date**: 2026-10-22
**Status**: Accepted
**Updated**: 2026-11-11 (staleness sweep). Spec 0010 renamed the statuses (`COMPLETED` is `CLOSED`), gave every log one audit shape (`actorUserId`, `actorEmail`, `actorName`, a `changes` JSON list), dropped `shop_change_logs` (`SHOP_CHANGE` is `GARAGE_CHANGE`, chip "Garage") and squashed the migrations into one baseline, so the backfill of AC-17 no longer exists as its own migration. The history summary is `{ finished, closed, cancelled, spend }` (finished = closed + cancelled) with tiles Finished, Closed, Cancelled, Total spend. `/audit-logs` is gated by `audit.view`, not the Admin role (spec 0011). The API wrapper is `src/lib/api/auditApi.ts`. On the ticket page an event names the ticket "this ticket" (spec 0024 AC-15).

## Summary

Today the Repair history and Audit log pages look like copies of the repair ticket list. This spec gives each page its own job: history becomes an archive of closed repairs (a summary strip, month headings, outcome, duration and cost), and the audit log becomes a timeline of who changed what, grouped by day, with each change shown as a before and after. The audit log needs data the API doesn't send yet, so this feature includes a small backend change in welinc-backend-vrms: a paginated audit endpoint that sends structured fields, history filters by date and garage with totals, and one data migration. This is the cross repo spec `AGENTS.md` asks for.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As an admin, I want closed repairs grouped by month with their outcome, duration and cost, so that I can look back at past work without it looking like my open queue.
- As an admin, I want totals for whatever range and filters I pick, so that I can answer "how many did we close and what did it cost" in one look.
- As a mechanic, I want to look up my own closed repairs by date and garage, so that I can find a past job quickly.
- As an admin, I want a timeline of every change to repair tickets (who, what, when, before and after), so that I can trace how a ticket ended up where it is.
- As an admin, I want to filter that timeline by event type, person, date and ticket, and keep loading older events, so that no change is ever out of reach.

**Acceptance criteria**:

*Repair history (`/history`, admins and mechanics)*

- **AC-1**: The `PageHeader` reads "Repair history" with the `History` icon and the subtitle "Finished repairs, closed and cancelled." There is no primary action button on the page.
- **AC-2**: A summary strip of `KpiCard`s sits under the header: **Closed** (`Archive`), **Completed** (`CheckCircle2`, success tone), **Cancelled** (`XCircle`), and for admins only **Total spend** (`PhilippinePeso`). The values come from the response's `summary` and cover every row that matches the current filters (search, outcome, garage, date range), not just the current page. Mechanics see three tiles; the API never sends them spend. Four in a row from 1024px up, two by two below.
- **AC-3**: Filters: a search box (repair #, plate or driver, as today), **Outcome** (All, Completed, Cancelled), **Garage** (All garages, then the list from `getGarages()`), and **Date range** with presets All time (default), This month, Last 90 days, This year, and Custom. Custom shows two date inputs (from and to, both inclusive, in the browser's local time); both are required, and no request is sent until both are set. If "from" is after "to", an inline error reads "Start date must be on or before the end date." and no request is sent. Changing any filter goes back to page 1. At 375px the filters wrap with no horizontal scroll.
- **AC-4**: The list uses `DataTable` with these columns: **Repair #** (`mobile: 'title'`), with a lock icon (accessible name "Locked") when the ticket is locked, or an "Unlocked" badge when `isUnlocked` is true, for admins and mechanics alike (the API now sends `isUnlocked` to both); **Vehicle** plate (`mobile: 'subtitle'`); **Outcome** `StatusBadge` (`mobile: 'badge'`), and for cancelled tickets the cancellation reason as one muted line below it, cut off at one line with the full text in a tooltip; **Duration** (completed tickets: "Same day", "1 day" or "N days", see *Text and formatting rules*; cancelled: "—"); **Garage**; **Cost** (admins only, end aligned, `tabular-nums`); **Closed** (date). Rows are sorted by `closedAt`, newest first.
- **AC-5**: Rows sit under month headings ("October 2026") by `closedAt` in the browser's local time: a full width heading row in the table, a heading between cards on phones. Headings are per page, so a month that carries over from the previous page shows its heading again.
- **AC-6**: Clicking a row opens `/repairs/:id?mode=readonly`. The row menu keeps **View details** for everyone and **Edit ticket** (`/repairs/:id`) for admins, as today.
- **AC-7**: 20 rows per page, with the `DataTable` pagination.
- **AC-8**: States: while loading, the summary tiles and the table show skeletons. On a load failure, an `ErrorState` with "Try again" replaces the table and the tiles. With no closed repairs at all: `EmptyState` (`Archive` icon) "No closed repairs yet" / "Completed and cancelled repairs show up here." With filters that match nothing: "No repairs match these filters" with a "Clear filters" button that resets every filter to its default.

*Audit log (`/audit-logs`, admins only)*

- **AC-9**: The `PageHeader` reads "Audit log" with the `ClipboardList` icon and the subtitle "Every change to repair tickets: who made it and when." The route stays admin only.
- **AC-10**: Events show as a vertical timeline grouped by local day, under headings "Today", "Yesterday", or a date like "Mon, Oct 18" (with the year added when it isn't the current year). Each event shows: an icon for its type in a tinted circle, the time ("10:42 AM", with the full date and time in a tooltip), the actor's initials avatar and name (their email in a tooltip and in screen reader text), the sentence for its type (AC-11), and the repair number as a link to `/repairs/:id`. An event with no actor shows no avatar and uses the no actor wording.
- **AC-11**: Each event type reads as follows:
  - `CREATED`: "{name} created {REP}", or with no actor, "{REP} was created".
  - `STATUS_CHANGE`: "{name} changed the status of {REP}", then the old and new `StatusBadge`s with an arrow between them. With no old value, only the new badge shows.
  - `COST_UPDATE`: "{name} updated the costs of {REP}", then "₱4,000 → ₱5,200 total", then a muted line "Parts ₱3,000 → ₱3,500 · Labor ₱1,000 → ₱1,700". A missing parts or labor amount counts as ₱0 (old rows stored ₱0 as null), so "₱0 → ₱5,200 total" is a valid line. When the new cost is a lump sum, the muted line reads "Lump sum" instead. If the stored values can't be read at all, only the sentence shows.
  - `UNLOCK`: "{name} unlocked {REP}", then the reason in quotes.
  - `SHOP_CHANGE`: "{name} moved {REP} to a different garage", then "old garage → new garage".
  - Any other type: "{name} {raw action} on {REP}", with a generic icon. These show only under the All chip.
  - `{name}` is the actor's name, else their email.
- **AC-12**: Filters: event type chips (All, Created, Status, Costs, Unlocks, Shop; one active at a time, All by default), **Person** (All people, then everyone who appears in the log, from `GET /vrms/repairs/audit-logs/actors`), **Date range** (the same presets and Custom rules as AC-3), and a **Repair #** search (partial match, sent 300ms after typing stops). Filtering happens on the server. Changing a filter reloads the timeline from the newest event.
- **AC-13**: The first load shows the newest 50 events. While older events exist, a "Load older events" button sits at the bottom and fetches the next 50 by cursor (a bookmark that says where the last batch ended); it shows progress while loading. If that fetch fails, an inline message "Couldn't load older events." with "Try again" appears, and the events already shown stay. When nothing older remains, the bottom reads "You've reached the start of the log."
- **AC-14**: States: a timeline shaped skeleton while loading; `ErrorState` with "Try again" on a first load failure; with no events at all, `EmptyState` "No activity yet" / "Changes to repair tickets show up here."; with filters that match nothing, "No events match these filters" with a "Clear filters" button.
- **AC-15**: Every audit row can be reached (the 50 row cap is gone). Events are ordered newest first by time, then by id. Across "Load older events", no event shows twice, and no event that was recorded before the first load is skipped. Events recorded after the first load appear after a filter change or a reload.

*Backend and data (welinc-backend-vrms)*

- **AC-16**: Creating a ticket also writes a `CREATED` audit row with the creator's `userId` and email, as a nested create inside the same `repairTicket.create` call, so the ticket and its row are saved together or not at all.
- **AC-16b**: Saving a closed ticket (after an unlock) without changing its status keeps its `completedAt` and writes no status audit row. `completedAt` is set only when the status changes into `COMPLETED` or `CANCELLED` (moving an unlocked completed ticket to cancelled sets it again, to the cancel time).
- **AC-17**: After the migration: every `COMPLETED` or `CANCELLED` ticket has a non null `completedAt`; every ticket that existed before has exactly one `CREATED` audit row (with no actor) at its `createdAt`; every `shop_change_logs` row has a matching `SHOP_CHANGE` audit row. Running the backfill a second time adds nothing.
- **AC-18**: `GET /vrms/repairs/audit-logs` and `GET /vrms/repairs/audit-logs/actors` answer only admins (a mechanic gets 403). `GET /vrms/repairs/history` keeps today's scoping: mechanics get only tickets they are assigned to, with no costs and `summary.spend: null`. A mechanic account with no linked mechanic record gets an empty list and a zero summary (today it sees every closed ticket).
- **AC-18b**: The ticket detail page keeps working after the migration: its audit list still contains only `STATUS_CHANGE`, `COST_UPDATE` and `UNLOCK` rows (no backfilled `CREATED` rows, no copied `SHOP_CHANGE` duplicates), and a null email reads as "Unknown". Feature 11 replaces this panel later.
- **AC-19**: `GET /vrms/repairs/audit-logs/all`, `getAuditLogs()` and the `AuditEntry` type are removed, and nothing references them.

*Both pages*

- **AC-20**: Both pages use only spec 0001 components and theme tokens (no inline `style`, no legacy classes, no hex values), and lint passes with the token rules. Both work at 375px and 1280px with no horizontal scroll, and axe reports no serious or critical issues on `/history` (admin and mechanic) and `/audit-logs` (admin).

## Decision

**Chosen option**: Option 3: Give each page its own layout, backed by a small API change

History becomes a month grouped archive with server computed totals and date and garage filters, the audit log becomes a day grouped timeline fed by a paginated, structured audit endpoint, and one data migration backfills close dates, creation events and shop changes.

**Implementation skills**: `shadcn` (`shadcn-ui/ui`, `.claude/skills/shadcn/`) · `vercel-react-best-practices` (`vercel-labs/agent-skills`, `.claude/skills/vercel-react-best-practices/`) · `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`) · `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-cli/`)

## Feature design

**Data model sketch** (one migration, no new tables):

| Table | Change |
|---|---|
| `audit_logs` | `user_id` and `email` become nullable (old `CREATED` rows have no actor). `created_at` becomes `Timestamptz(3)` (millisecond precision, the same as a JavaScript `Date`, so a cursor built from it matches the stored value exactly). New indexes: `(created_at DESC, id DESC)` for keyset paging (paging by a "last seen" bookmark instead of an offset), `(email)` for the Person filter and actor lookup, `(action)`. `action` gains the values `CREATED` and `SHOP_CHANGE` (it is already a free `VarChar(100)`, so no type change). |
| `repair_tickets` | No column change. `completed_at` now means "closed at" for both outcomes (the status update code already sets it on cancel); the backfill fills the old null rows. |
| `users` | No change. Audit actors match it by email, compared case insensitively (`users.email` is already unique, so a match finds at most one user; no foreign key exists or is added). `audit_logs.user_id` holds the auth service's user id (the JWT `sub`), which never equals the VRMS `users.id`, because the two services keep separate databases; it is still written, as a record only, but never joined or indexed. |
| `shop_change_logs` | No change. Its rows are copied into `audit_logs` once. |

**Backfill** (SQL appended by hand to the generated `migration.sql`, after the schema changes; each insert uses `gen_random_uuid()` for `id` and sets `created_at` explicitly, because the uuid and time defaults live in Prisma, not the database; each statement is guarded by `WHERE ... IS NULL` or `NOT EXISTS`, so running the SQL again by hand adds nothing):
1. `UPDATE repair_tickets SET completed_at = COALESCE((SELECT MAX(created_at) FROM audit_logs a WHERE a.repair_ticket_id = t.id AND a.action = 'STATUS_CHANGE' AND a.new_value = t.repair_status::text), t.updated_at) WHERE repair_status IN ('COMPLETED','CANCELLED') AND completed_at IS NULL`.
2. Insert one `CREATED` row (`user_id NULL`, `email NULL`, `created_at = ticket.created_at`) for every ticket with no `CREATED` row.
3. Insert one `SHOP_CHANGE` row per `shop_change_logs` row (`user_id = changed_by_user_id`, `email NULL`, `field_name = 'garage'`, old and new values, `created_at = changed_at`) where no `SHOP_CHANGE` row with the same ticket, time and values exists. `changed_at` keeps microseconds and `created_at` keeps milliseconds, so the guard compares `created_at = changed_at::timestamptz(3)`. These rows have no email, so they show no actor (see Value sourcing).

**State transitions**: unchanged. Closed tickets (`COMPLETED`, `CANCELLED`) stay closed; unlocking allows edits but does not change status or `completedAt`. `updateStatus` changes so that `completedAt` is set only on a real change into a closed status, and the `STATUS_CHANGE` audit row is written only when the status actually changes (AC-16b). Saving costs or status still re-locks the ticket (`isUnlocked: false`), as today.

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/repairs/history` (changed) | GET | `search?`, `status?` (`COMPLETED`/`CANCELLED`), `garageId?` (uuid), `from?`, `to?` (ISO instants; `from` inclusive, `to` exclusive, on `completedAt`), `page?`, `limit?` (no cap: the dashboard asks for 10000; both absent returns every row, as today) | `{ data: RepairTicket[] (each with closedAt, and isUnlocked for every role), total, summary: { closed, completed, cancelled, spend: number \| null } }`. `summary.closed` equals `total`. `spend` sums `totalCost` of matching `COMPLETED` rows (null cost counts as 0; 0 under the Cancelled filter) and is `null` only for mechanics | bearer, ADMIN or MECHANIC | 400 bad date, uuid or status, or `from >= to`; 401 |
| `/vrms/repairs/audit-logs` (new) | GET | `limit?` (default 50, max 100), `cursor?` (opaque), `type?` (one action), `actorId?` (uuid: a VRMS `users.id` from the actors list; the server looks up that user's email and keeps rows whose `audit_logs.email` equals it, case insensitive; an unknown id, or a user with no rows, returns an empty list, not a 400), `from?`, `to?` (ISO, on `created_at`), `repairNumber?` (partial, case insensitive, ignored under 2 characters). The client sends the same filters with every cursor; the cursor is only a position | `{ data: AuditEvent[], nextCursor: string \| null }` | bearer, ADMIN | 400 bad cursor, date or uuid; 401; 403 |
| `/vrms/repairs/audit-logs/actors` (new) | GET | none | `{ id, name, email }[]` (VRMS `users` fields), every VRMS user whose email (case insensitive) appears on at least one audit row, once each, sorted by name. Inactive and soft deleted users are included (their rows still exist and their changes are real); an audit email that no VRMS user has is not listed and cannot be picked as a filter | bearer, ADMIN | 401; 403 |
| `/vrms/repairs/audit-logs/all` | GET | removed | | | |

Both new routes are declared before `:id` in `repairs.controller.ts` (where `audit-logs/all` sits today), so `audit-logs` is never parsed as a ticket id. Query params are validated with request DTO classes in `src/modules/vrms/dto/`, in the style of the existing DTOs, replacing the raw `parseInt` calls on these two routes.

**Query shapes**:
- History list, count and summary share one `where` (filters plus mechanic scope). The summary is one `groupBy` on `repairStatus` with `_count` and `_sum.totalCost`. The list uses a slim `select` (the row fields only, not the full `ticketInclude()` with every audit row and part) and sorts by `completedAt desc` with `nulls: 'last'`, then `id desc`, so offset paging never repeats or skips rows that share a time.
- Audit keyset: order by `createdAt desc, id desc`; the next page uses `OR: [{ createdAt: { lt: t } }, { createdAt: t, id: { lt: id } }]` combined with the filters.
- Audit actors: `audit_logs` has no relation to `users`, so after loading a page the server runs one batched `users.findMany` matching the page's distinct non empty emails case insensitively (`equals` with `mode: 'insensitive'`), and maps each row's email to its user by lowercased email. The actors list does the same over the distinct audit emails.

`AuditEvent`:
```ts
{
  id: string;
  type: 'CREATED' | 'STATUS_CHANGE' | 'COST_UPDATE' | 'UNLOCK' | 'SHOP_CHANGE' | string;
  at: string;                                   // created_at, ISO
  actor: { id: string | null; name: string | null; email: string | null } | null; // id: VRMS users.id matched by email, only for preselecting the Person filter; the UI never depends on it
  ticket: { id: string; repairNumber: string };
  status?: { from: string | null; to: string };                 // STATUS_CHANGE
  cost?: { from: CostSnapshot | null; to: CostSnapshot | null }; // COST_UPDATE, null when unreadable
  unlockReason?: string;                                        // UNLOCK
  garage?: { from: string | null; to: string | null };          // SHOP_CHANGE
  rawAction: string;                                            // the stored action, for unknown types
}
CostSnapshot = { partsCost: number | null; laborCost: number | null; total: number | null; isLumpSum: boolean }
```

**Text and formatting rules** (client):
- Money: `₱` plus `Intl.NumberFormat('en-PH', { maximumFractionDigits: 0 })`, the same helper as spec 0002 (move `formatPeso` to a shared `src/lib/utils/format.ts`).
- Duration: whole days from `createdAt` to `closedAt`, rounded down: 0 gives "Same day", 1 gives "1 day", N gives "N days".
- Closed date: `Oct 22, 2026`. Event time: `10:42 AM` (12 hour, local).
- Month heading: `October 2026`. Day heading: "Today", "Yesterday", else `Mon, Oct 18`, plus `, 2025` when not the current year.
- Date presets turn into `from` and `to` in the browser's local time: This month = the 1st at 00:00 to the 1st of next month; Last 90 days = today's 00:00 minus 89 days to tomorrow's 00:00; This year = Jan 1 to next Jan 1; Custom = the from day's 00:00 to the day after "to" at 00:00. All time sends neither.

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| History summary | Closed, Completed, Cancelled counts | Server `count` over the same `where` as the list (all filters), grouped by `repairStatus` |
| History summary | Total spend | Server `SUM(total_cost)` over matching `COMPLETED` rows; `null` for mechanics (role from the JWT) |
| History row | `closedAt` | `repair_tickets.completed_at` (backfilled for old rows) |
| History row | Duration | Derived on the client: `closedAt` minus `createdAt`, whole days, completed tickets only |
| History row | Cancellation reason | `repair_tickets.cancellation_reason` (already returned) |
| History row | Locked / Unlocked | Closed status and `isUnlocked` (today admin only; the history response now sends it to every role) |
| History row | Cost | `totalCost` (already returned to admins only) |
| History filters | Garage options | `GET /vrms/config/garages` (`getGarages()`) |
| History filters | `from`, `to` | Browser local time, per *Text and formatting rules* |
| History grouping | Month heading | `closedAt` in the browser's local time zone |
| Audit event | Type, time, ticket | `audit_logs.action`, `created_at`, `repair_ticket_id` joined to `repair_tickets.repair_number` |
| Audit event | Actor name | Server: `users.name` of the user whose email equals `audit_logs.email`, case insensitive (soft deleted users included), `null` if no user matches. Client shows the name, else the email |
| Audit event | Actor id | `users.id` of that same email match, else `null` |
| Audit event | Actor email | `audit_logs.email` as stored (not lowercased), else `null` |
| Audit event | `actor` itself | `null` when `audit_logs.email` is null or empty (backfilled `CREATED` and `SHOP_CHANGE` rows), so those use the no actor wording |
| Audit event | Status before and after | `previous_value`, `new_value` on `STATUS_CHANGE` rows |
| Audit event | Cost before and after | `previous_value` and `new_value` JSON on `COST_UPDATE` rows, parsed on the server. A null parts or labor value is 0 (the writer stores ₱0 as null). Previous `total` = parts + labor (the old JSON has no total); previous `isLumpSum` = `false` (never stored). New `total` from `totalCost`, new `isLumpSum` from the JSON |
| Audit event | Unlock reason | `new_value` on `UNLOCK` rows |
| Audit event | Garage before and after | `previous_value`, `new_value` on `SHOP_CHANGE` rows |
| Audit event | `CREATED` actor | `user_id` and `email` from the JWT, stored as is, written at ticket creation (AC-16); `null` for backfilled rows |
| Audit paging | `nextCursor` | Base64 of the last returned row's `created_at` and `id`; the next page is rows strictly older than that pair |
| Audit filters | Person options | `GET /vrms/repairs/audit-logs/actors`: distinct non empty `audit_logs.email`, matched to `users` by email case insensitively |
| Audit filters | Person filter match | `actorId` resolved to that user's `users.email`, compared with `audit_logs.email` case insensitively |
| Audit grouping | Day heading | Event `at` in the browser's local time zone, compared with the client clock at render time |

**Key invariants**:
- Audit actors are identified by email, compared case insensitively, the one identity the auth service and VRMS share (as `getMechanicForUser` already does). `audit_logs.user_id` is the auth service's id and is never joined to VRMS `users`.
- One audit table feeds the timeline. Anything that should appear in it writes to `audit_logs` (shop changes included, from now on).
- Keyset paging orders by `(created_at DESC, id DESC)` and the cursor compares on both, so ties never skip or repeat a row.
- History totals and history rows always use the same `where`, so a tile never disagrees with the list under the same filters.
- Spend and costs never reach a mechanic, enforced on the server, not hidden in the UI.
- `completedAt` is the close time for both outcomes. It changes only when the status changes into a closed status, and nothing sets it back to null.
- A `STATUS_CHANGE` row always has different old and new values.
- A mechanic with no linked mechanic record sees nothing in history (fail closed).
- No inline style, hex value or legacy class in `src/features/repair/pages/HistoryPage.tsx` or `src/features/audit-logs/`.

**Security model**: audit endpoints are `@Roles(UserRole.ADMIN)`, the same as today. History keeps its current scoping: a mechanic sees only tickets they are assigned to, costs are stripped, and `summary.spend` is `null`. The actors list exposes names and emails of people who changed tickets, admins only. No new personal data is stored; the backfill writes no personal data (null actors).

**Failure and edge cases**:
- An actor whose user row is gone, or whose email no VRMS user has: show the stored email as the name; with no stored email, use the no actor wording.
- A user whose email changes in the auth service while the VRMS `users` row keeps the old one: from then on their new events don't match a name or the Person filter, and their older events stop matching once the VRMS row is updated. If an email is later reused by someone else, the new owner's name shows on the old events. Accepted; emails rarely change here.
- Unreadable cost JSON: `cost` is `null` and only the sentence shows (AC-11).
- A new event recorded while you read: it appears only after a filter change or reload; "Load older events" never repeats or skips rows (AC-15).
- A malformed `cursor`, a bad date, or `from >= to`: 400 from the API, shown as the inline load error.
- Garage list fails to load: the Garage filter shows only "All garages" and the page still works.
- A ticket deleted later: its audit rows are deleted with it (existing cascade), so it never shows a dead link.
- Repair # search with under 2 characters: the client sends no filter, and the server ignores it if sent.
- An audit row committed late with an earlier timestamp than rows already loaded: it shows after a reload, not via "Load older events" (AC-15).
- Costs edited after a ticket closed (after an unlock): history cost and spend show the current values; the timeline shows the change.
- Presets and Custom compute day boundaries with calendar math in local time (not "plus 24 hours"), so daylight saving changes never shift a boundary.

**Configuration required**: none.

**Critical test scenarios**:
- History happy path: as admin, pick This month and Completed; the tiles match the count and spend of the rows, rows sit under month headings, duration and cost read correctly. Verifies **AC-2**, **AC-3**, **AC-4**, **AC-5**
- History mechanic: as a mechanic, only assigned tickets show, there are three tiles, no Cost column, and the API response has `spend: null` and no costs. Verifies **AC-2**, **AC-18**
- History custom range: from after to shows the inline error and no request; a range across two pages repeats the month heading. Verifies **AC-3**, **AC-5**
- Audit timeline: change a ticket's status, costs and unlock it; each event shows the right sentence, badges, peso amounts and reason, under "Today". Verifies **AC-10**, **AC-11**
- Audit paging: with 120 events, several sharing one timestamp, load twice to reach the start; no event repeats or goes missing. Verifies **AC-13**, **AC-15**
- Same status save: unlock a completed ticket and save it without changing status; `completedAt` stays and no status event appears. Verifies **AC-16b**
- Mechanic with no record: a mechanic login with no linked mechanic gets an empty history and zero summary. Verifies **AC-18**
- Detail page: after the migration, an old ticket's detail page still loads its audit panel without `CREATED` or duplicate shop rows. Verifies **AC-18b**
- Audit filters: each type chip, a person, a date range and a repair # narrow the list on the server; "Clear filters" restores it. Verifies **AC-12**, **AC-14**
- Create event: a new ticket shows "{name} created {REP}"; an old ticket shows "{REP} was created". Verifies **AC-11**, **AC-16**, **AC-17**
- Migration: run on a copy of the seed database; no closed ticket has a null `completedAt`; running the backfill again adds nothing. Verifies **AC-17**
- Auth: a mechanic calling either audit endpoint gets 403. Verifies **AC-18**
- Cleanup: searching for `audit-logs/all` and `getAuditLogs` finds nothing. Verifies **AC-19**
- 375px and 1280px with axe on both pages and roles. Verifies **AC-20**

## Migration plan

**Strategy**: one Prisma migration (schema change plus backfill SQL), deployed before or with the backend code. The changes are additive, so the old frontend keeps working until the new one ships.
**Phases**:
1. Migration: make `audit_logs.user_id` and `email` nullable, add the indexes, then run the three backfill statements.
2. Backend: write `CREATED` rows, add the new endpoints, extend history. The old `audit-logs/all` stays until step 3 lands.
3. Frontend: ship both pages, then remove `audit-logs/all` and `getAuditLogs` in the same change.
**Rollback**: revert the backend and frontend commits. The migration can stay: nullable columns and extra rows break nothing once the detail page filter (AC-18b) is in. To remove the backfilled rows if ever needed: `DELETE FROM audit_logs WHERE action = 'CREATED' AND user_id IS NULL AND email IS NULL`, and `DELETE FROM audit_logs a USING shop_change_logs s WHERE a.action = 'SHOP_CHANGE' AND a.repair_ticket_id = s.repair_ticket_id AND a.created_at = s.changed_at::timestamptz(3) AND a.new_value = s.new_value`.
**Risks**:
- The `completed_at` backfill guesses close times for old cancelled tickets from `updated_at` when no audit row exists; those dates may be late. Accepted for seed and legacy data.
- Between the migration and the new frontend, the old audit page shows backfilled `CREATED` rows with an empty user. Ship steps 1 to 3 close together.
- The new indexes are built inside Prisma's migration transaction, so not `CONCURRENTLY`; `audit_logs` is small, so the brief write lock is accepted.

## Build plan

The scope tags this feature `· Facade`, but the engineer chose a backend change for it, so it is built end to end: data first, then the API, then the UI that binds to it, one page at a time so each lands working.

1. Migration in welinc-backend-vrms: nullable actor columns, `created_at` to millisecond precision, indexes, then the three idempotent backfills appended to `migration.sql`. Apply it to the local database and confirm the columns, indexes and backfilled rows exist; run the backfill SQL a second time by hand and confirm it adds nothing. Satisfies **AC-17**
2. Write paths: `create` adds the `CREATED` row as a nested create in `repairTicket.create`; `updateStatus` sets `completedAt` and writes the status row only on a real status change; `formatTicket`'s detail audit list keeps only the three original actions and maps a null email to "Unknown". Satisfies **AC-16**, **AC-16b**, **AC-18b**
3. `GET /vrms/repairs/audit-logs` with keyset paging, filters, actor join and the parsed `AuditEvent` shape, plus `GET /vrms/repairs/audit-logs/actors`; both admin only, declared before `:id`, with request DTOs. Add Jest tests for the cursor (no repeats or gaps on equal times), the cost parsing (null as 0, unreadable JSON) and the 403. Satisfies **AC-11**, **AC-12**, **AC-13**, **AC-15**, **AC-18**
4. Extend `findHistory`: a request DTO; `garageId`, `from`, `to`; slim `select`; `closedAt` and `isUnlocked` on every row; sort `completedAt desc nulls last, id desc`; the `summary` block from one `groupBy` (spend `null` for mechanics); fail closed for a mechanic with no record. Keep `limit` uncapped so the dashboard's call still works. Add Jest tests for the summary matching the filtered rows, the mechanic case and the no record case. Satisfies **AC-2**, **AC-3**, **AC-4**, **AC-18**
5. Shared frontend pieces: `formatPeso` and the date and duration helpers in `src/lib/utils/format.ts`; a `DateRangeFilter` component (presets plus Custom with its inline error); `DataTable` gains an optional `groupBy: (row) => { key: string; label: string }` that renders heading rows on desktop and headings between cards on phones. Satisfies **AC-3**, **AC-5**, **AC-12**
6. Rebuild `HistoryPage`: header, summary tiles, filters, grouped `DataTable` with the AC-4 columns, row menu, pagination and all states. Update `getRepairHistory` for the new params and response. Satisfies **AC-1** to **AC-8**
7. Build the audit timeline in `src/features/audit-logs/`: an `auditApi.ts` wrapper, a `useAuditEvents` hook (filters, cursor, load more, errors), `AuditTimeline`, `AuditEventItem` (one renderer per type) and the filters bar, then rebuild `AuditLogsPage` with its states. Satisfies **AC-9** to **AC-15**
8. Remove `audit-logs/all`, `findAllAuditLogs`, `formatAuditAction`, `getAuditLogs` and `AuditEntry`, and confirm nothing references them. Satisfies **AC-19**
9. Run lint, typecheck and build in both repos (and `npm run test` in the backend), then check both pages at 375px and 1280px in Playwright with axe, for both roles on history. Open a ticket detail page and the dashboard to confirm both still load. Satisfies **AC-18b**, **AC-20**

## Consequences

**Positive**:
- The three pages now look like their jobs: a queue, an archive and a timeline.
- Every audit event is reachable (no 50 row cap), and filters run on the server, so they stay fast as the log grows.
- History totals are exact for any range, not added up from one page.
- Every ticket's story starts at its creation, and new tickets record who created them.
- The dashboard's old audit endpoint and the sentence formatter are gone.

**Negative / tradeoffs**:
- This feature breaks the UI refresh's Facade rule: a migration and API changes in welinc-backend-vrms, so it needs a backend deploy, not just a frontend one.
- Old tickets show "{REP} was created" with no name, and old cancelled tickets may show a close date taken from their last update.
- The Shop chip shows nothing until a garage change feature writes `SHOP_CHANGE` rows.
- Day and month headings use the browser's time zone, so two admins in different zones can see an event under different days.
- `DataTable` gains grouping, which every table now carries as an option.
- Costs can still be edited after a ticket closes (after an unlock), so past spend totals can change after the fact.
- Two small behavior fixes ride along in `updateStatus` (no re-dating on a same status save, no empty status rows) and one in history scoping (fail closed), so this feature changes more than its two pages.

**Neutral**:
- `completedAt` officially means "closed at" for both outcomes; the API also exposes it as `closedAt`.
- The ticket detail page's audit panel (feature 11) can reuse `AuditEventItem` later.

## Follow-up

- [ ] Whatever feature lets a ticket change garage must write a `SHOP_CHANGE` row to `audit_logs` (not only `shop_change_logs`), so the Shop chip fills.
- [ ] Feature 11 (repair list and detail): replace `AuditLogCollapsible` on the detail page with `AuditEventItem`, so a ticket's own history reads the same as the log.
- [ ] Seed data: have the welinc-backend-vrms ticket seed write `CREATED` rows for seeded tickets, so a fresh database starts with the same history the migration produces.
- [ ] Remarks and mechanic assignments are not audited today. Decide whether they belong in the timeline.
- [ ] Scope row 13 is tagged `· Facade`; consider changing it to reflect the backend work, or note the exception there.
