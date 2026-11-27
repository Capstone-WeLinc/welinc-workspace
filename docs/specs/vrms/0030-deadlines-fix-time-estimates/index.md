# 0030. Due dates from priority, issue types and history

**Date**: 2026-11-27
**Status**: Proposed

## Summary

Every repair ticket gets a due date the moment it is created, worked out from its priority and from how long its issues usually take (the knowledge base first, then each issue type's set hours). The later of the two wins, so the date is never earlier than the work can really take, which matters because BMS plans bookings on it as the truck's expected return date. Admins and Chief Mechanics can change it by hand with a reason, or put it back to automatic, and tickets show Overdue and Due soon (the warning before the deadline) on the lists and dashboards. It builds on columns and a writer (`setDueAt`, spec 0029) that already exist, so the work is the rules, two small routes, settings and the screens.

## Requirements

**User stories**:
- As an Admin, I want each ticket to show when the truck should be back from the moment it is created, so that I know when to expect it on the road (WL-206).
- As an Admin, I want that date worked out from the kind of repair, so that nobody has to set it by hand (WL-207).
- As an Admin or Chief Mechanic, I want to change a due date with a reason, or put it back to automatic, so that the date stays honest when plans change.
- As a mechanic, I want to see which of my tickets are due soon or overdue, so that I finish the right job first.
- As BMS, I want every due date change, so that I can flag the bookings it affects (spec 0029, flow 3).

**Acceptance criteria**:
- **AC-1**: Every new ticket gets a due date on create: `createdAt` plus the larger of its priority hours and its issue hours. `dueAtSource` is `ISSUE_TYPE` when the issue hours are larger, else `PRIORITY` (a tie goes to `PRIORITY`).
- **AC-2**: Priority hours come from four Admin settings, by default Critical 8 h, High 24 h, Medium 72 h, Low 168 h. Hours count on the calendar (nights and Sundays included).
- **AC-3**: Issue hours are the sum over the ticket's issues. Each issue counts, in this order: its linked known fix's typical hours when that fix has at least `knowledge.min_samples` closed repairs, else that fix's `estimatedHours`, else its category's `fixHours`, else 0. With the knowledge module off, only the category's `fixHours` counts. The total is capped at 2160 h (90 days).
- **AC-4**: Each issue category has an optional "Fix time (hours)" (0.25 to 720) that the Admin edits on the existing categories page. The seven starting categories get realistic values from the migration.
- **AC-5**: An automatic due date (`PRIORITY` or `ISSUE_TYPE`) on an open ticket is worked out again, from `createdAt`, when the priority changes (the edit form or an accepted expedite) and when an issue is added (by hand or from a VMMS referral), removed, given another category, or linked, relinked or unlinked to a known fix on the ticket. A `MANUAL` date is never worked out again by these, and neither is a closed or cancelled ticket (an unlocked one included). The Knowledge page's bulk link (`linkIssueIds`) does not recompute, on purpose, like AC-7.
- **AC-6**: When the worked out date would be earlier than now, the date becomes now plus the priority hours, with source `PRIORITY`, and the audit note says the ticket was escalated past its original time.
- **AC-7**: Changing a settings value (priority hours, a category's fix time, the due soon window) never moves an existing ticket's date. Only new tickets and tickets worked out again under AC-5 use the new values.
- **AC-8**: A user with the new permission `ticket.due_date.edit` (Admin and Chief Mechanic on by default, Mechanic off) can set a ticket's due date by hand on an open ticket: later than now, at most 90 days from now, with a required reason of 5 to 500 characters. The source becomes `MANUAL`.
- **AC-9**: The same user can put a `MANUAL` date back to automatic with a required reason (5 to 500 characters). The dialog shows about the date it would set before saving; the saved value is worked out again on save (AC-6 included) and wins. Nobody can clear a due date to empty.
- **AC-10**: Every due date write goes through `setDueAt`: it writes one audit row (the before and after date, the reason, and for automatic dates which rule set it and the hours) and sends BMS a repair update with the reason as `changeReason`. A write that does not change the date writes nothing and sends nothing.
- **AC-11**: A ticket is Due soon when it is open, not overdue, and less than its window is left. The window is the smaller of `tickets.due_soon_hours` (24 h by default, 1 to 168) and half the time from `createdAt` to `dueAt`. This holds for every priority.
- **AC-12**: Overdue and Due soon show on the repair list rows, the ticket side panel and detail page, and the dashboards. The mechanic's dashboard shows their Due soon tickets as their own group after Overdue. Under 24 h left the text says hours ("Due in 5 h"); otherwise days.
- **AC-13**: A one time command `npm run due:backfill` gives every open ticket with no due date an automatic one through `setDueAt` (AC-1, AC-3, AC-6), and is safe to run again (it skips tickets that have a date).
- **AC-14**: Closed and cancelled tickets keep their last due date for the record, cannot be changed by hand (409 `TICKET_NOT_OPEN`) or worked out again, and are never Overdue or Due soon. A ticket reopened after an unlock keeps its old date (and may show Overdue). Open means every status outside `FINISHED_STATUSES`, so On hold and Outsourced tickets can go Overdue (feature 31 decides about time on hold).
- **AC-15**: Two people changing one ticket at once: the second save answers 409 `STALE` (the ticket's `updatedAt` check, as spec 0019), and nothing is written.

## Decision

**Chosen option**: Option 2, one pure due date calculator on the backend, called at fixed moments and written only through `setDueAt`.

A function `computeDueAt(ticket, issues, settings, knowledgeStats, now)` returns `{ dueAt, source, priorityHours, issueHours, escalated }`. It runs inside the transactions of create, the priority edit, the issue edits and the knowledge link routes, and only when the ticket's source is not `MANUAL`. Its result goes to `setDueAt`. Nothing works out a date on read.

**Implementation skills**: `prisma-client-api` (`.claude/skills/prisma-client-api/`) · `nestjs-best-practices` (`.claude/skills/nestjs-best-practices/`) · `react-hook-form` (`.claude/skills/react-hook-form/`, the change dialog)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch** (one migration):

| Table | Change | Notes |
|---|---|---|
| `issue_categories` | add `fix_hours Decimal(5,2) NULL` | "Fix time (hours)", 0.25 to 720; null adds nothing |
| `repair_tickets` | none | `due_at`, `due_at_source` (`PRIORITY`, `ISSUE_TYPE`, `MANUAL`) and the `due_at` index already exist (spec 0010); `created_at` is the anchor |
| `knowledge_entries` | none, read only | `estimated_hours`, plus the typical hours from `knowledge-stats.ts` (median `hoursSpent`, null under `knowledge.min_samples`) |
| `audit_logs` | none | `dueDateEvent` rows (`TICKET_EDITED`, one `dueAt` change line) |

Settings catalog (`src/settings/catalog.ts`), group `Due dates`, all `int`, unit `hours`:

| Key | Default | Min | Max |
|---|---|---|---|
| `tickets.due_hours_critical` | 8 | 1 | 720 |
| `tickets.due_hours_high` | 24 | 1 | 720 |
| `tickets.due_hours_medium` | 72 | 1 | 720 |
| `tickets.due_hours_low` | 168 | 1 | 720 |
| `tickets.due_soon_hours` | 24 | 1 | 168 |

Permission, in both `welinc-auth/prisma/catalog/vrms.ts` and `welinc-backend-vrms/src/auth/permissions/catalog.ts`: `ticket.due_date.edit`, label "Change due dates", group Tickets, description "Set a ticket's due date by hand, or put it back to the automatic date.", `defaults(true, true, false)` (Admin, Chief Mechanic, Mechanic).

Starting category hours (hours of shop work, typical for a light and medium truck shop). The seven categories come from the baseline migration, so the new migration sets them by `name_key`, only where `fix_hours` is still null: Brakes 6, Engine 48, Electrical 8, Suspension 12, Cooling 8, Transmission 24, General 4. `prisma/seeds/repairs.seed.ts` drops its own `DUE_HOURS` table and calls `computeDueAt` with the catalog defaults, so seeded dates follow the same rules.

**The rule, step by step** (`src/modules/vrms/due-dates.ts`):
1. `priorityHours` = the setting for the ticket's priority.
2. `issueHours` = the sum over issues per AC-3, capped at 2160.
3. `hours` = max of the two; `source` = `ISSUE_TYPE` if `issueHours > priorityHours`, else `PRIORITY`.
4. `dueAt` = `createdAt + hours`. If `dueAt < now`: `dueAt = now + priorityHours`, `source = PRIORITY`, `escalated = true`.
5. The audit reason (also BMS's `changeReason`), from these templates only, cut to 500 characters. They name categories and counts, never an issue's description (spec 0029 sends BMS no issue text):
   - priority won: `Due date from <Priority> priority (<h> h)`
   - issues won: `Due date from issue times (<h> h: <Category> <h> h, …)`, with ` from <n> past repairs` after a category whose hours came from the knowledge base; an issue with no category reads `Other`
   - escalated: `Raised to <Priority> after its time had passed: due <h> h from now`
   - prefix on a recompute, by trigger: `Priority changed. `, `Issue added. `, `Issue removed. `, `Issue changed. `, `Known fix changed. `, `Issues added from VMMS. `, `Expedite <JO>. `, `Back to the automatic date: <their reason>. `
   - backfill: `Due date set by the new rules. ` before the rule text

Numbers: `fixHours` and `estimatedHours` are Prisma `Decimal`, converted with `Number()`; the issue sum is rounded to 2 places; `dueAt` keeps whole milliseconds. `loadStats` (`knowledge-stats.ts`) is widened to take any client with `$queryRaw` (the transaction client included) and is called once per calculation with the ticket's distinct known fix ids; archived fixes still count. `module.knowledge` is read with `SettingsService.get`.

**Where it is called** (all inside the existing transaction that holds the ticket row lock):

| Path | File | When |
|---|---|---|
| Create | `repairs.service.ts` `create` | always: right after `tx.repairTicket.create` and before create's own `queueBmsRepairUpdate` (which reads `dueAt` at queue time), anchored on the returned `createdAt`, with `skipBmsUpdate: true`; its audit row is stamped 1 ms after the `CREATED` row |
| Priority edit | `ticket-edits.service.ts` `editDetails` | priority changed, ticket open, source not `MANUAL` |
| Issue add, edit, remove | `ticket-edits.service.ts` `addIssue`, `editIssue` (category change or `clearsFix`), `removeIssue` | ticket open, source not `MANUAL` |
| Known fix link, relink, unlink | `repairs.service.ts` (the link route near line 1211) | ticket open, source not `MANUAL` |
| Referral added to a ticket | `referral-decisions.service.ts` (the add to ticket path, `tx.repairIssue.create`) | ticket open, source not `MANUAL`; its BMS update then carries the new date, so this call passes `skipBmsUpdate: true` and runs before that update |
| Expedite accept | `expedite-decisions.service.ts` (priority through `stampEdit`) | one write only: a given `dueAt` as `MANUAL`; otherwise, when the priority changed and the source is not `MANUAL`, the recomputed date (read the ticket inside the transaction, not before it) |
| Knowledge bulk link | `knowledge-entry-editor.service.ts` `linkIssueIds` | never (AC-5) |
| Hand change, reset | new routes below | open tickets only |
| Backfill | `prisma/due-backfill.ts` | open tickets with `dueAt` null; one transaction per ticket with the row lock, 50 tickets per batch, the System actor; a ticket with a source but no date is treated as automatic |

Every write here runs inside the path's `stampEdit` (the `updatedAt` stale check, `updatedAt` and `lastActivityAt` moved), except create and the backfill, which hold the row lock themselves. A recompute's audit row is stamped 1 ms after the path's own audit rows (the `stampedAt(now, i)` order). An edit that changes nothing else but would change the date still writes the date.

`setDueAt` gains one optional flag, `{ skipBmsUpdate?: boolean }`, used only where the path queues its own BMS update right after (create and the referral add to ticket path). It keeps being the only writer of `dueAt` and `dueAtSource`.

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/repairs/:id/due-date` | PUT | `dueAt` ISO with an offset (req; no offset is 400), `reason` string 5 to 500 (req), `updatedAt` ISO (req) | the ticket detail; the same date answers 200 and writes nothing | `ticket.due_date.edit` and can see the ticket | 400 `DUE_DATE_OUT_OF_RANGE` (not later than the request's `now`, or over 90 days from it), 404, 409 `TICKET_NOT_OPEN`, 409 `STALE` |
| `/vrms/repairs/:id/due-date/automatic` | GET | none | `{ dueAt, source, priorityHours, issueHours, escalated, issues: { id, description, hours, from: 'KNOWLEDGE' \| 'ESTIMATE' \| 'CATEGORY' \| 'NONE' }[] }` | `ticket.due_date.edit` and can see the ticket | 404, 409 `TICKET_NOT_OPEN` |
| `/vrms/repairs/:id/due-date/automatic` | POST | `reason` 5 to 500 (req), `updatedAt` (req) | the ticket detail | same | 404, 409 `TICKET_NOT_OPEN`, 409 `STALE`, 409 `NOT_MANUAL` (already automatic) |
| Ticket list and detail | GET (existing) | none | add `dueSoonAt` ISO or null | as today | none |
| Issue category create and update (existing, `knowledge.controller.ts`) | POST, PATCH | add `fixHours` number or null (0.25 to 720) | the category with `fixHours` | `lookups.manage` (as today) | 400 |
| Settings (existing) | GET, PATCH | the five new keys | as today | `settings.manage` | 400 per spec 0012 |

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| Create, recompute | priority hours | catalog keys `tickets.due_hours_*` through `SettingsService.get` |
| Create, recompute | each issue's hours | known fix typical hours (`knowledge-stats.ts`, `resolveStats` with `knowledge.min_samples`), else `knowledge_entries.estimated_hours`, else `issue_categories.fix_hours`, else 0; the knowledge part only when `module.knowledge` is on |
| Create, recompute | anchor | `repair_tickets.created_at` |
| Recompute (AC-6) | now | the request transaction's `now` (the same `at` passed to `setDueAt`) |
| Hand change | the date | `dueAt` input, checked against now and now + 90 days |
| All writes | reason | input `reason` for hand change and reset; the generated rule text (step 5) for automatic writes |
| BMS update | `expectedReturnAt`, `changeReason` | `dueAt` and the reason, through `queueBmsRepairUpdate` (spec 0029 child 0003) |
| List, detail (every response that carries `dueAt`: the repair list, the ticket detail and side panel, and the dashboard lists, which use the repair list) | `dueSoonAt` | derived on the backend in the response mapper (`repairs.service.ts` near line 1814): `dueAt` minus the smaller of `tickets.due_soon_hours` and half of (`dueAt` minus `createdAt`); null when the ticket is closed, cancelled or has no date. The browser can't read settings (they need `settings.manage`), so it compares `dueSoonAt` with its fetch time |
| Dialog | the automatic date preview | the GET `automatic` route |
| Label text | hours or days left | the browser, from `dueAt` and its fetch time (`src/lib/utils/due.ts`, extended for hours under 24 h) |
| Mechanic dashboard Due soon group | which tickets | the browser, from each row's `dueSoonAt` against its fetch time; no new filter or count route |
| Backfill | each ticket's date | `computeDueAt` with the run's `now`; old tickets mostly take AC-6 (now plus priority hours), as intended. Trucks not linked to VMMS send BMS nothing (`queueBmsRepairUpdate` skips them) |

**Key invariants**:
- Only `setDueAt` writes `dueAt` and `dueAtSource`; every write that changes the date writes one audit row and (except inside create) one BMS update.
- Nothing works out a date on read; a stored date only changes at the moments in AC-5, AC-8, AC-9, AC-13 and expedite acceptance.
- A `MANUAL` date changes only by hand, by reset, or by an accepted expedite with a date.
- An open ticket always has a due date once the backfill has run; nobody can clear it.

**Security model**: anyone who can see a ticket sees its due date, `dueSoonAt` and the due date audit rows. Only `ticket.due_date.edit` changes or resets it, and only on tickets the caller can see (the same ticket visibility check as spec 0019 edits). Category hours stay on `lookups.manage`, the settings on `settings.manage`. No personal data is involved.

**Configuration required**: none (no new environment variables).

**Critical test scenarios**:
- Happy path: create a High ticket with Brakes (6 h) and Engine (48 h): due `createdAt + 54 h`, source `ISSUE_TYPE`, one audit row, one BMS update with that `expectedReturnAt`. Verifies **AC-1**, **AC-3**, **AC-10**.
- Knowledge first: an issue linked to a known fix with 5 closed repairs (median 3 h) and category Engine (48 h) counts 3 h; with 2 repairs and the minimum at 3 it counts the fix's estimate, else 48 h; with the knowledge module off it counts 48 h. Verifies **AC-3**.
- Recompute: change Medium to Critical on a 3 day old automatic ticket: the date becomes now + 8 h with the escalated note. Change priority on a `MANUAL` ticket: the date stays. Add an issue to an unlocked closed ticket: the date stays. Add a VMMS referral to an open ticket: the date moves and BMS gets one update. Accept an expedite with no date on an automatic ticket: the date follows the new priority. Verifies **AC-5**, **AC-6**, **AC-14**.
- Settings change: raise High to 48 h; existing High tickets keep their date, a new one uses 48 h. Verifies **AC-7**.
- Hand change: a Chief Mechanic sets a date 3 days out with a reason, source `MANUAL`, BMS gets the reason; a date in the past or 91 days out answers 400; a Mechanic gets 403; a closed ticket answers 409 `TICKET_NOT_OPEN`. Verifies **AC-8**, **AC-14**.
- Reset: the dialog shows the automatic date, and saving sets it with source `PRIORITY` or `ISSUE_TYPE`; resetting an automatic ticket answers 409 `NOT_MANUAL`. Verifies **AC-9**.
- Due soon: an 8 h ticket turns Due soon at 4 h left; a 168 h ticket at 24 h left; a closed ticket never. Verifies **AC-11**, **AC-12**.
- Concurrency: two hand changes with the same `updatedAt`: the second answers 409 `STALE`. Verifies **AC-15**.
- Backfill: run twice; the second run changes nothing. Verifies **AC-13**.

## Build plan

Tracer Bullet: the first milestone runs one priority date end to end (create, ticket, BMS) before the issue hours, the hand change and the screens thicken it.

1. **Priority dates end to end.** The five settings in the catalog; `due-dates.ts` with `computeDueAt` (priority hours only at first, AC-6 included); call it in `create` through `setDueAt` with the new `skipBmsUpdate` flag; `dueSoonAt` on the list and detail responses; the web due helpers read `dueSoonAt` and show hours under 24 h. Satisfies **AC-1**, **AC-2**, **AC-6**, **AC-10**, **AC-11**.
2. **Issue hours.** The migration for `issue_categories.fix_hours` with the starting hours; `fixHours` on the category routes (`knowledge-categories.service.ts`, kept on rename and deactivate) and the categories page; `loadStats` widened to the transaction client; the knowledge first sum in `computeDueAt` (AC-3 order, module switch, cap, rounding); the recompute calls in `editDetails`, `addIssue`, `editIssue`, `removeIssue`, the known fix link route, the referral add to ticket path and the expedite accept, open tickets only and skipped for `MANUAL`; the seed's category hours and its switch to `computeDueAt`. Satisfies **AC-3**, **AC-4**, **AC-5**, **AC-7**.
3. **Hand change and reset.** `ticket.due_date.edit` in both catalogs (run `catalog:sync` locally); the PUT route, the GET and POST `automatic` routes with their errors and the `updatedAt` check; the "Change" action on the Due row of the ticket detail page with the dialog (date and time, reason, "Use the automatic date" showing the preview). Satisfies **AC-8**, **AC-9**, **AC-14**, **AC-15**.
4. **Due soon on screens, and the backfill.** The Due soon chip on list rows, side panel, detail and dashboards; the mechanic dashboard's Due soon group after Overdue; `prisma/due-backfill.ts` with `npm run due:backfill`, run locally and once on staging after the deploy. Satisfies **AC-12**, **AC-13**.

## Migration plan

**Strategy**: no flag; additive migration, then a one time backfill.
**Phases**:
1. Deploy milestones 1 to 3: the nullable `fix_hours` column with its starting hours, and the rules for new and edited tickets. Old open tickets keep no date until phase 2.
2. After the deploy, run `npm run due:backfill` once on staging (as `fleet:link` was run) and run `catalog:sync` in welinc-auth for the new permission.
**Rollback**: revert the code commits; the `fix_hours` column and the written dates can stay (the old code ignores the column and already reads `dueAt`).
**Risks**: the backfill sends BMS one update per open ticket at once; BMS receives them like any update, and VRMS's outbox retries failures.

## Consequences

**Positive**:
- BMS gets a real expected return date for every open ticket, so flow 3 of the integration works on real data, not only on expedites.
- One calculator and one writer: the rules live in one tested place, and every change is audited and reaches BMS.
- Dates get better as history grows, without drifting on their own: the knowledge base feeds new and reworked tickets only.

**Negative / tradeoffs**:
- Calendar hours ignore shop opening times, so a Friday evening Critical ticket can show Overdue on Saturday when the shop is closed. Admins can only soften this with longer priority hours.
- Summing issue hours assumes one crew works the issues one after another; a big ticket worked by several mechanics at once gets a later date than reality.
- The "later of the two" rule makes priority hours a floor: a 2 h Low job waits a week in the date. That matches how shops queue low priority work, but it has to be explained.
- Raising a priority can move the date earlier (AC-6), so BMS may see a return date jump forward on escalation.
- The seed's dates change (Critical 24 h becomes 8 h), so seeded tickets show more Overdue on staging until feature 72 reseeds.

**Neutral**:
- `setDueAt` gains a `skipBmsUpdate` flag; spec 0029 child 0003's "only writer" rule is unchanged.
- One new permission needs `catalog:sync` in welinc-auth on every environment (local and staging).
- The backfill sends BMS one update per open ticket on staging, once.

## Follow-up

- [ ] Feature 40 (lookup lists): when the reasons list exists, the due date dialog gets a reason picker plus an optional note; the picked label becomes the reason text.
- [ ] Feature 45 (reports): add due date, Overdue, and on time versus late to the reports and their export (WL-207's "shown in reports").
- [ ] Feature 28 (notifications): turn Due soon into a bell notification for the assigned mechanics (WL-207's 24 h notice).
- [ ] Feature 31 (on hold for parts): decide whether time on hold extends the due date.
- [ ] Feature 72 (realistic demo data): reseed with these rules so staging shows a realistic mix of on time, Due soon and Overdue tickets.
- [ ] Spec 0029 child 0003: note the `skipBmsUpdate` flag used by create.
