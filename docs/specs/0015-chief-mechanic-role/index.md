# 0015. Chief Mechanic role: oversight dashboard, verification queue and cost visibility

**Date**: 2026-11-01
**Status**: In Progress

## Summary

The Chief Mechanic gets their own dashboard. It opens with the tickets waiting for their sign off (oldest first), then their own assigned work, then what needs attention across all garages, then the pipeline. They can now see costs (read only), the way a real shop foreman sees parts and labor but leaves the money to the manager. Closing a ticket that has no costs stays allowed, as in most shops, but an Admin can require costs first with a new setting. To sort the queue fairly, each ticket starts recording when its status last changed. No new page and no new sidebar item.

## Requirements

**User stories**:
- As a Chief Mechanic, I want the tickets waiting for my sign off at the top of my first screen, oldest first, so that finished trucks don't sit waiting.
- As a Chief Mechanic, I want to see my own assigned work and what needs attention across every garage, so that I can run the work floor.
- As a Chief Mechanic, I want to see a ticket's costs without editing them, so that I can spot a wrong cost when I verify.
- As an Admin, I want to choose whether a ticket may close without costs, so that VRMS follows how our garages handle paperwork.

**Acceptance criteria**:

*Cost visibility*
- **AC-1**: In `catalog.ts`, `ticket.costs.view` defaults to on for `CHIEF_MECHANIC`. A database with no row for it gets the row on through the existing startup backfill. `ticket.costs.edit` and `analytics.view` stay off for the Chief.
- **AC-2**: A one off data migration turns the Chief's existing `ticket.costs.view` row on only when it is off and no person ever changed it (no `permission_changes` row for that role and key with a non null `actor_user_id`). When it flips the row, it writes one `permission_changes` row (`before` false, `after` true, actor fields null so the history shows System, `note` = `Spec 0015: new Chief Mechanic default`) and bumps `permission_matrix.version`, in one statement serialised with the matrix editor. A row a person changed is left as it is. Running it again changes nothing.
- **AC-3**: With `ticket.costs.view` on and `ticket.costs.edit` off, a Chief Mechanic sees costs wherever the key already shows them (ticket detail, repair list rows, Repair history rows and its spend summary, AI part cost estimates). They get no cost editing control, and `PATCH /vrms/repairs/:id/costs` returns 403 for them. When an Admin turns the key off in Settings, every cost field disappears again on the next request (spec 0011 behavior, unchanged).

*Closing without costs*
- **AC-4**: A new setting `tickets.require_costs_to_close` (group `Tickets`, label "Require costs before closing", yes or no, default **off**) appears on the Settings page as a switch, editable with `settings.manage`, and its change is logged like other settings (spec 0012).
- **AC-5**: With the setting on, the move to `CLOSED` from For verification is refused while the ticket has no costs (`partsCost`, `laborCost` and `totalCost` all null and no `repairParts` rows): the status endpoint returns 422 with code `COSTS_REQUIRED` and the message "Add the costs before closing this ticket.", and the ticket's `moves` entry for `CLOSED` carries `needs: 'costs'`. The web disables Verify and close with that reason when `needs` is `costs` and the ticket has no costs. With the setting off, nothing changes on the server.
- **AC-6**: In the close dialog, a caller with `can.editCosts` keeps today's "No costs are recorded yet" note with the Go to costs link. A caller without it (the Chief) sees instead: "No costs recorded yet. An Admin will need to unlock this ticket to add them." The note shows only when the caller can see costs and the ticket has none.

*When a status last changed*
- **AC-7**: `repair_tickets.status_changed_at` (not null) holds the time of the ticket's last status change. Ticket creation sets it to the create call's `now`. `applyStatusMove` sets it to the move's `now` in the same conditional update as `repairStatus`, so every move writes it, the unassign release included. The demo seed sets it from each seeded ticket's last status audit row (else its creation time). No other path writes it.
- **AC-8**: The migration backfills every existing ticket with the `created_at` of its newest `audit_logs` row whose `changes` contains `{"field":"repairStatus"}`. A ticket with no such row gets its `CREATED` row's time, else its own `created_at`. No ticket is left null.
- **AC-9**: `GET /vrms/repairs` with `status=FOR_VERIFICATION` orders rows by `statusChangedAt` ascending, then `id` ascending, whatever other filters are set, for every caller. Every request without that status keeps today's urgency order. Paging stays stable.
- **AC-10**: List rows and the single ticket response include `statusChangedAt` (ISO string). The web `RepairTicket` type marks it required.

*Which dashboard*
- **AC-11**: The dashboard shows the Chief view when the caller holds `ticket.work`, `ticket.verify` and `ticket.view_all` and not `ticket.administer`. Otherwise today's rule holds: `ticket.work` without `ticket.administer` gets the mechanic view, everyone else the admin view. The choice reads permissions, never the role name.
- **AC-12**: A Chief Mechanic whose `ticket.verify` or `ticket.view_all` is turned off gets the mechanic view; one given `ticket.administer` gets the admin view.

*The Chief view*
- **AC-13**: Four tiles on top: **Waiting for you** (section 1's full count before the limit), **My open work** (the length of `mechanicWorkList` over tickets with `can.work`), **Overdue** (all open tickets past `dueAt`), **Open** (all open tickets).
- **AC-14**: Section 1, **Waiting for your sign off**: open tickets in For verification with `can.verify` true, sorted by `statusChangedAt` ascending then `id` ascending, at most 8, in a new `VerificationQueueTable` built on `DataTable`. Columns: plate (`PlateChip`), ticket number, mechanics' names, garage, wait time. At 375px the plate is the row title, the ticket number the subtitle, and the wait time a field. A row opens the ticket, where Verify and Send back already live (spec 0014). A "See all" link to `/repairs?status=FOR_VERIFICATION` shows whenever the section has a row. Empty state: "Nothing waiting for your sign off".
- **AC-15**: The wait time reads "Waiting under an hour" below 60 minutes, "Waiting N h" below 24 hours, else "Waiting N days" (whole units, rounded down), measured from `statusChangedAt` to the snapshot's `fetchedAt`. A negative difference (clock skew) counts as 0. It renders in a `<time dateTime=…>` element.
- **AC-16**: The Chief's own tickets in For verification (`can.verify` false because they are assigned) are left out of section 1 and its tile. They still show in section 3 as waiting, in the filtered repair list, and their detail page shows the existing "Someone else must verify work on a ticket you're assigned to." reason.
- **AC-17**: Section 2, **My work**: `mechanicWorkList` over open tickets with `can.work` true (Assigned and In progress, in its order). Empty state: "Nothing assigned to you".
- **AC-18**: Section 3, **Needs attention**: the admin view's attention list across every garage, computed with no limit, minus the tickets in section 1 (all of them, not just the 8 shown), then cut to 8. Section 4: the pipeline bar (`RepairProgressChart`). No spend section, even with `ticket.costs.view` on.
- **AC-19**: The Chief view has the same loading skeleton, error with retry, last updated line, truncation note and visible tab polling as the admin view (it fetches history too, for the pipeline). It works at 375px and 1280px, uses theme tokens only, and axe finds nothing.

*Navigation*
- **AC-20**: No new page and no new sidebar or tab bar item. The sidebar is unchanged for the Chief (Dashboard, Repair tickets, Repair history, Knowledge base, Profile).

## Decision

**Chosen option**: Option 1: a permission based Chief view on the existing dashboard, with the queue as its first section and the existing repair list as the full queue.

Add a third dashboard view chosen from permissions, record `status_changed_at` on every ticket for a first come first verified queue, turn on read only costs for the Chief through a guarded one off data migration, and add an Admin setting for whether a ticket may close without costs (off by default).

**Implementation skills**: `prisma-cli` (`.claude/skills/prisma-cli/`) · `prisma-client-api` (`.claude/skills/prisma-client-api/`) · `nestjs-best-practices` (`.claude/skills/nestjs-best-practices/`) · `vercel-react-best-practices` (`.claude/skills/vercel-react-best-practices/`)

## Feature design

**Data model sketch** (changes only):

| Where | Change | Notes |
|---|---|---|
| `repair_tickets` | add `status_changed_at timestamptz(6)`, not null after backfill, default `now()` | Prisma `statusChangedAt`, `@map("status_changed_at")` |
| `repair_tickets` | add index `(repair_status, status_changed_at)` | `@@index([repairStatus, statusChangedAt])`, serves the For verification sort |
| `role_permissions` | data only: the Chief's `ticket.costs.view` row | guarded update (AC-2) |
| `permission_changes`, `permission_matrix` | data only: one System row, version + 1 | only when the row flips |
| `src/settings/catalog.ts` | new entry type `kind: 'value', type: 'boolean'` (a `ToggleEntry` in the `SettingEntry` union, no min, max or unit) and the `tickets.require_costs_to_close` entry | spec 0012 catalog; the settings rows are delivered the way spec 0012 delivers any new key; the web Settings page renders a boolean value as a switch |

Two migrations, in this order:
1. `20261101120000_ticket_status_changed_at`: add the column nullable, backfill (AC-8), set `NOT NULL` and the default, add the index. One SQL file, one transaction.
2. `20261101120100_chief_mechanic_costs_view`: the guarded data update (AC-2), hand written in an empty migration (`prisma migrate dev --create-only`), shaped like `20261030120000_settings`: one statement with CTEs that locks or updates `permission_matrix`, updates `role_permissions ... RETURNING`, inserts the `permission_changes` row from what was returned, and bumps the version only when a row was returned. On a fresh database the row doesn't exist yet, so it does nothing and the startup backfill inserts it on from the catalog (AC-1).

Backfill query shape (AC-8):
```sql
UPDATE repair_tickets t SET status_changed_at = COALESCE(
  (SELECT a.created_at FROM audit_logs a
    WHERE a.repair_ticket_id = t.id
      AND a.changes @> '[{"field":"repairStatus"}]'
    ORDER BY a.created_at DESC LIMIT 1),
  (SELECT a.created_at FROM audit_logs a
    WHERE a.repair_ticket_id = t.id AND a.action = 'CREATED'
    ORDER BY a.created_at ASC LIMIT 1),
  t.created_at);
```

**State transitions**: spec 0014's table, unchanged except that the move to `CLOSED` from For verification gains the need `costs` while `tickets.require_costs_to_close` is on (AC-5). The need is checked in the status endpoint before `applyStatusMove`, like the other needs.

**API surface**:

| Endpoint | Method | Change | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/repairs` | GET | with `status=FOR_VERIFICATION`, order `statusChangedAt asc, id asc` | rows gain `statusChangedAt` | unchanged | unchanged |
| `/vrms/repairs/:id` | GET | `moves` entry for `CLOSED` may carry `needs: 'costs'` | gains `statusChangedAt` | unchanged | unchanged |
| `/vrms/repairs/:id/status` | PATCH | close refused without costs when the setting is on | | unchanged (`ticket.verify` for close) | 422 `COSTS_REQUIRED` |
| `/vrms/repairs/:id/costs` | PATCH | none | | `ticket.costs.edit` (Chief: off) | 403 for the Chief |
| settings endpoints (spec 0012) | GET, PATCH | new key `tickets.require_costs_to_close` | boolean value | `settings.manage` to change | unchanged |

No new endpoint. The Chief view reuses `useDashboardData({ includeHistory: true })`.

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Pick the dashboard view | which view | `useCan` for `ticket.work`, `ticket.verify`, `ticket.view_all`, `ticket.administer` |
| Section 1 rows and tile | tickets | open list rows with `status === 'FOR_VERIFICATION'` and `can.verify` (server, spec 0014) |
| Section 1 order | oldest first | `statusChangedAt` ascending, then `id` ascending (same as AC-9) |
| Section 1 row | plate, ticket number, mechanics, garage | list row fields `vehiclePlate`, `repairNumber`, `mechanics[].name`, `garageLocation` |
| Section 1 row | wait time | `fetchedAt` minus `statusChangedAt`, clamped at 0, AC-15 format, new helper `waitingText` in `attention.ts` |
| My open work tile, section 2 | tickets | `mechanicWorkList(active.filter(t => t.can.work), fetchedAt)` |
| Section 3 | tickets | `attentionList(active, fetchedAt, Infinity)` minus every section 1 id, then the first 8 |
| Section 4 | status counts | `pipelineCounts(active, history, fetchedAt)` |
| Overdue, Open tiles | counts | `isOverdue(t, fetchedAt)` over `active`; `active.length` |
| `statusChangedAt` on create | time | the `now` already in scope in the create call (not the database default) |
| `statusChangedAt` on a move | time | `now` passed into `applyStatusMove` |
| `statusChangedAt` in the seed | time | each seeded ticket's last status audit row, else its creation time |
| Backfilled `statusChangedAt` | time | AC-8 query |
| Migration guard | "no person changed it" | `permission_changes` rows for (`CHIEF_MECHANIC`, `ticket.costs.view`) with `actor_user_id IS NOT NULL` |
| Close refused | "ticket has no costs" | server: the three cost columns null and no `repairParts`; web: `hasCosts(ticket)` in `nextAction.ts` (same rule) |
| Close refused | the rule is on | `settings.get('tickets.require_costs_to_close')` |
| Close dialog note | which wording | `can.editCosts` on the ticket |
| Cost fields for the Chief | values | existing cost record, gated by `ticket.costs.view` (spec 0011) |

**Key invariants**:
- `status_changed_at` is written only by ticket creation, `applyStatusMove` and the seed, and always together with `repair_status`.
- The dashboard view comes from permissions only. No `role === 'CHIEF_MECHANIC'` check anywhere.
- Section 1 never lists a ticket the caller can't verify; the server's `can.verify` is the only source.
- The data migration never turns a right off and never overrides a person's choice.
- With `tickets.require_costs_to_close` off, the close move behaves exactly as in spec 0014.

**Security model**:
- No new permission and no change to server scoping. The Chief reads every ticket through `ticket.view_all` (spec 0011) and verifies through `ticket.verify` with no self verification (spec 0014).
- New exposure: the Chief sees costs on every ticket in every garage. Editing, spend on the dashboard and the analytics page stay Admin only. Admin can turn the key off in Settings; the change is logged.
- The costs rule is enforced on the server; the web only mirrors it.

**Configuration required**: none (the new setting lives in the database, spec 0012).

**Critical test scenarios**:
- Happy path: a mechanic sends a ticket for verification; the Chief's dashboard shows it in section 1 with its wait time; an older waiting ticket sits above it; "See all" opens the list in the same order. Verifies **AC-7**, **AC-9**, **AC-13**, **AC-14**, **AC-15**
- Self verification: the Chief sends their own assigned ticket for verification; it is missing from section 1 and the tile, shows in section 3 and the filtered list, and its detail page shows the reason. Verifies **AC-16**, **AC-18**
- Fallback: an Admin turns off the Chief's `ticket.verify`; after the matrix refetch the Chief sees the mechanic view; turning on `ticket.administer` gives the admin view. Verifies **AC-11**, **AC-12**
- Migration guard: where an Admin once changed the Chief's `ticket.costs.view`, the migration leaves it and writes nothing; on an untouched copy it turns on with one System history row; a second run changes nothing. Verifies **AC-2**
- Costs read only: the Chief sees costs on detail and History, sees no edit control, gets 403 from `PATCH :id/costs`, and sees the Admin unlock wording in the close dialog. Verifies **AC-3**, **AC-6**
- Costs required: with the setting on, closing a ticket with no costs returns 422 `COSTS_REQUIRED` and Verify is disabled with the reason; adding one part makes it pass; with the setting off it closes. Verifies **AC-4**, **AC-5**
- Backfill: a ticket moved twice gets the second move's time; a ticket with only a `CREATED` row gets that time. Verifies **AC-8**
- Admin list: Admin filters to For verification plus a garage and gets oldest waiting first; with no status filter the urgency order is unchanged. Verifies **AC-9**

## Build plan

Tracer Bullet: the first task runs one thin thread from the database to the Chief's screen (the queue), then the view thickens, then costs.

1. **Thin thread: the queue end to end.** Migration 1 with the backfill; `statusChangedAt` in `schema.prisma`, set on create, in `applyStatusMove` and in the seed; in the list row and single ticket response; the For verification sort. Web: `statusChangedAt` on the ticket type and in `ticketFixture.ts`; the view choice in `DashboardPage.tsx`; a `ChiefDashboard` with section 1 only (`VerificationQueueTable`, `waitingText`, See all, empty state); a `verificationQueue` helper in `attention.ts`. Satisfies **AC-7** to **AC-11**, **AC-14** to **AC-16**
2. **The rest of the Chief view.** Tiles, My work, Needs attention minus section 1, pipeline, no spend; loading, error, refresh and truncation states; the fallback rule. Satisfies **AC-12**, **AC-13**, **AC-17** to **AC-19**
3. **Read only costs.** The catalog default; migration 2; check the cost surfaces the key already gates and the 403 on cost edits; the close dialog wording by `can.editCosts`; update the `/me` per role and catalog tests. Satisfies **AC-1** to **AC-3**, **AC-6**
4. **Costs before closing setting.** The boolean value entry type and the key in the settings catalog, its switch on the Settings page; the `costs` need on the close move, the 422 in the status endpoint, `needs: 'costs'` in `movesOut`, the disabled Verify reason in `nextAction.ts`. Satisfies **AC-4**, **AC-5**
5. **Sweep.** Unit tests for `verificationQueue`, `waitingText` (including clock skew), the view choice and the costs need; backend specs that mock `formatTicket` or `applyStatusMove` updated; the backfill and guard SQL run against the dev database; nav unchanged; 375px and 1280px with axe for Chief, Admin and Mechanic; lint, typecheck, build in both repos. Satisfies **AC-19**, **AC-20**

## Migration plan

**Strategy**: no flag; two ordered migrations in one release. Nothing is deployed yet (spec 0008), so only dev databases and the first staging load hold existing data.
**Phases**:
1. Migration 1 adds `status_changed_at` nullable, backfills it (AC-8), then sets `NOT NULL` and the default, in one transaction. The code that writes it ships in the same release.
2. Migration 2 runs the guarded permission update (AC-2). The startup backfill then fills any missing row from the new catalog default, and the version bump makes running servers reload the matrix on their next request.
**Rollback**: revert the release. To undo migration 1, drop the column and index. To undo migration 2, turn the key off in Settings (a person's logged change, which also keeps migration 2 from flipping it again).
**Risks**: a ticket whose status audit rows were lost gets `created_at`, so it may look older in the queue than it is. During a rolling deploy, an old server still running after migration 1 doesn't update `status_changed_at` on moves; harmless before go live, worth a single replica deploy later.

## Consequences

**Positive**:
- The Chief's first screen is the work only they can do, in fair order, without a new page.
- `status_changed_at` is a reusable fact: features 42 (deadlines) and 43 (stale ticket alerts) can measure time in status without reading the audit log.
- The view choice stays permission based, so Admin's matrix edits change the dashboard with no code.
- Each garage chooses how strict closing is, without a code change.

**Negative / tradeoffs**:
- A third dashboard view to maintain alongside admin and mechanic.
- The Chief view fetches every open and history row (up to `ADMIN_LIMIT`), heavier than the mechanic view.
- The Chief now sees costs across every garage, a wider money exposure; the History spend total comes with it.
- Admins also get the new For verification order.
- A data migration that edits a permission row is unusual; it is guarded and logged, but it is one more place permissions change.
- Spec 0012's settings catalog gains a third entry type (a yes or no value), which its Settings page and validation must handle.
- With the costs rule off, closed tickets without costs still need an Admin unlock to fix, until the follow up below.
- Until feature 59, a Chief at one garage sees the other two garages' queues too.

**Neutral**:
- Two migrations; no API shape removed, two fields and one error code added.
- Spec 0011's AC-14 ("Chief sees every ticket, read only, no costs") is narrowed: the Chief now sees costs by default.
- Spec 0002's note about a Chief Mechanic dashboard (Jira VRMS-41) is resolved here.

## Follow-up

- [ ] Scope feature 23: the verification queue moved here; what's left there is proof files at verification and the verifier in reports.
- [ ] New scope feature (from spec 0015): **costs after close**. Let an Admin add or fix costs on a closed ticket without unlocking it (a separate financial close, the way shops post invoices after the truck leaves). Changes the closed ticket lock from specs 0004 and 0014; needs a decision.
- [ ] Spec 0011: add an `Updated` line noting AC-14 is narrowed by spec 0015 AC-1 (the Chief sees costs by default).
- [ ] Spec 0012: note the new yes or no value entry type and the `tickets.require_costs_to_close` key.
- [ ] Spec 0014: note the `costs` need on the move to `CLOSED`, gated by the setting.
- [ ] Spec 0010: note the new `repair_tickets.status_changed_at` column and index.
- [ ] `docs/context/roles-and-users.md`: the Chief row gains read only costs and the verification queue dashboard.
- [ ] Chief defaults for later features, decided here (real world shop foreman split). When each feature adds its key, default the Chief to: feature 53 reassign **on**; feature 31 approve a parts hold **on**; features 37 and 38 record an outsourced transfer and close it **on**; feature 39 approve outsourced spend **off** (management); feature 42 set fix time estimates **on**.
- [ ] Feature 29 (badges): the queue has no sidebar item, so its count lives on the Waiting for you tile; reconsider a badge there.
- [ ] Features 42 and 43: reuse `status_changed_at` for time in status.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
