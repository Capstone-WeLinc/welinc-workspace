# 0019. Admin ticket editing: fix a ticket after create, one section at a time

**Date**: 2026-11-03
**Status**: Accepted

## Summary

After a ticket is created, an Admin can fix its driver, odometer, priority, account type and corporation, and add, edit or remove its issues. Anyone with the assign right (Admin and Chief Mechanic by default) can change its mechanics in any open status. Each block on the repair detail page gets its own small Edit dialog, every save writes an audit row and stamps who edited last, and a stale save gets the usual 409 reload. Mechanics see reassignments within 3 seconds because the repair list, detail page and dashboard poll every 3 seconds while the tab is visible.

## Requirements

**User stories**:
- As an Admin, I want to fix the driver, odometer, priority and account details on a ticket so that a wrong intake entry does not stay wrong forever.
- As an Admin, I want to add, reword or remove issues on a ticket so that the work list matches what the truck really needs.
- As an Admin or Chief Mechanic, I want to add, remove or swap mechanics on a ticket at any open status so that work moves to whoever can do it.
- As a Mechanic, I want a reassignment to show on my phone within seconds so that I don't start work I'm no longer on, or miss work I'm now on.

**Acceptance criteria**:

Who and when
- **AC-1**: A new permission key `ticket.edit` (group Tickets, defaults Admin on, Chief Mechanic off, Mechanic off, editable in Settings like every key) guards the details and issue endpoints. The mechanics endpoint is guarded by the existing `ticket.assign` (Admin on, Chief on). A caller without the key gets 403 and sees no Edit control for that block.
- **AC-2**: Edits are allowed in every open status: `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `ON_HOLD`, `FOR_VERIFICATION`, `OUTSOURCED`, `PENDING_APPROVAL`. On `CLOSED` or `CANCELLED` they answer 400 `TICKET_LOCKED` ("Closed and Cancelled tickets are locked. An Admin must unlock this ticket first.") unless `isUnlocked` is true.
- **AC-3**: On an unlocked `CLOSED` or `CANCELLED` ticket, every edit needs a `reason` (5 to 500 characters after trimming, else 400 `REASON_REQUIRED`), saved as the audit row's note. These edits never change the status and never clear `isUnlocked` (the existing status save still relocks).

Details (driver, odometer, priority, account)
- **AC-4**: The Admin can swap the driver: pick an existing active driver, or add a new one by name and LTO license using create's rules (format `A01-23-456789`, 409 `DRIVER_EXISTS` with the owner's id and name for an active license, an inactive or deleted one is reactivated). The driver record itself is never renamed here.
- **AC-5**: The Admin can correct the odometer. "Other tickets" means the truck's non cancelled tickets except this one, ordered by `(createdAt, id)`, so tickets created at the same moment still have an order. The new reading may not be below the highest reading on the other tickets ordered before this one (when there are none there is no floor, so any reading from 0 up is allowed; the vehicle's own reading is the truck's latest, so it is never used as a floor on an edit), answered 400 `ODOMETER_BELOW_LAST` with `last` and that ticket's `repairNumber`. It may not be above the lowest reading on the other tickets ordered after this one, answered 400 `ODOMETER_ABOVE_NEXT` with `next` and that ticket's `repairNumber`; both messages name the blocking ticket. A closed floor ticket counts the same as an open one. The big jump confirm (`tickets.odometer_jump_warn_km`) applies against the floor, and is skipped when there is no floor, answered 400 `ODOMETER_JUMP_UNCONFIRMED` until `confirmOdometerJump` is sent. The floor for new tickets follows automatically, since it is computed from tickets.
- **AC-6**: The Admin can change the priority (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **AC-7**: The Admin can change the account type and corporation. `CORPORATE` needs an active corporation lookup value (400 "Choose a corporation." / "This corporation is no longer available. Choose another."); `ONLINE` clears the corporation. The stored name is a snapshot, as on create. An omitted `accountType` keeps the current one; a `corporationId` on a ticket that is (or becomes) `ONLINE` answers 400.
- **AC-8**: One details save writes one `TICKET_EDITED` audit row listing only the fields that changed, each with before and after (driver as "name (license)", corporation as name).
- **AC-8b**: On every edit endpoint (details, mechanics, issues), a save that changes nothing answers 200 with the ticket, no audit row and no stamp.

Mechanics
- **AC-9**: Holders of `ticket.assign` set the full mechanic list on a ticket in any open status (AC-2), adding, removing or swapping in one save. Each mechanic must be an active in house mechanic, listed once (400 otherwise). The list may be empty. There is no cap on how many; the picker's busy flag stays a hint.
- **AC-10**: On `OPEN`, a save that leaves at least one mechanic makes move M1 (to `ASSIGNED`). On `ASSIGNED`, a save that leaves no mechanic makes move M2 (back to `OPEN`); a swap that leaves at least one makes no move. In every other status the status never changes and an empty list is allowed. M1 and M2 are never looked up on `CLOSED` or `CANCELLED`. On an ownerless ticket, work moves that need an assignee (`ticket.work`) are open only to `ticket.administer` holders (the Admin) until someone is assigned; mechanics removed mid work keep their ticked steps and notes on record.
- **AC-11**: Whenever `verifiedByUserId` is set (closed, or reopened after verify), that person can't be added as a mechanic (400 "The person who verified this ticket can't be added to it."), so spec 0014's "never verify your own ticket" stays true.
- **AC-12**: A mechanic save writes `MECHANIC_UNASSIGNED` (names removed) and then `MECHANIC_ASSIGNED` (names added), one row each and only when that side changed, sharing one timestamp. A status move from AC-10 rides on the row of the side that triggered it (M1 on the `MECHANIC_ASSIGNED` row, M2 on the `MECHANIC_UNASSIGNED` row), with no separate `STATUS_CHANGE` row (the spec 0016 pattern).
- **AC-13**: The Admin and Chief dashboards' Needs attention list includes tickets in `IN_PROGRESS`, `ON_HOLD`, `FOR_VERIFICATION`, `OUTSOURCED` or `PENDING_APPROVAL` with no mechanic, labelled "No mechanic" and linking to the ticket. Both roles hold `ticket.view_all`, and the dashboard already reads `GET /repairs`, so the item comes from list rows' `mechanicCount`.

Issues
- **AC-14**: The Admin can add an issue with create's issue fields and rules: a system (an active `IssueCategory`), a root cause (1 to 100), a description (1 to 500 after trimming, optional only when a known fix is linked, then the entry's name is used) and an optional known fix (an Active knowledge entry, steps copied as on create). The stored `description` is built exactly as create builds it (`[System] rootCause: text`), through one shared helper. The issue's embedding is queued as on create. An `ISSUE_ADDED` audit row records the stored description.
- **AC-15**: The Admin can edit an issue's description and system. The dialog prefills the text after the leading `[System] ` prefix (root cause included, 1 to 600); the server stores `[${newSystem}] ${text}` and queues the embedding again. If the new system differs from a linked known fix's category, the link and its copied steps are cleared in the same save, and the dialog says so before saving. Relinking stays the existing action (spec 0007). An `ISSUE_EDITED` row lists the changed fields, including a cleared known fix.
- **AC-16**: The Admin can remove an issue even when work is recorded on it, after a confirm that names what goes with it (ticked steps, the "What fixed it" note) and how many photos lose their tag. Its steps and embedding go with it, while photos and knowledge suggestions stay and lose the link (existing `SetNull`). An `ISSUE_REMOVED` row keeps the system, description and any resolution note text.
- **AC-17**: A ticket always keeps at least one issue. Removing the last one answers 400 `LAST_ISSUE` ("Add the right issue first, or reword this one.").

Every save
- **AC-18**: Every edit endpoint requires `lastUpdatedAt` (ISO 8601 with milliseconds, as the ticket read returns it). A mismatch answers 409 with the existing `STALE_TICKET` message, and the web app shows its existing reload prompt. After a save, the returned ticket replaces the page's ticket and its `updatedAt` everywhere it is held.
- **AC-19**: Every save that changes something sets `editedAt`, `editedByUserId` and `editedByName` (from the token), and moves `updatedAt` and `lastActivityAt`, in the same transaction as its audit rows. The first write in that transaction is the guarded `updateMany where { id, updatedAt: loaded }` carrying the stamp (`count === 0` answers 409), so two saves at once can't both pass. The side panel shows "Edited <relative time> by <name>" when `editedAt` is set.
- **AC-19b**: The audit timeline and the ticket Activity show the new actions in plain words: `TICKET_EDITED` "Edited the ticket" with one line per change ("Driver: Juan Cruz (A01-23-456789) → …", "Odometer: 120,400 → 120,040 km", "Priority: Medium → High", "Account: Online → Corporate (Acme)"), `ISSUE_ADDED` "Added an issue", `ISSUE_EDITED` "Edited an issue", `ISSUE_REMOVED` "Removed an issue" with its text and any "What fixed it" note. A closed ticket edit's `reason` shows as the row's note. The action filter lists the new actions.
- **AC-20**: Edit controls follow the detail page's look: an Edit button per block (Vehicle & driver, Mechanics, each issue, plus Add issue) opens a dialog. Each dialog has a discard prompt for unsaved changes, works at 375px and 1280px, and passes axe.

Live updates
- **AC-21**: The repair detail page, the repair list and the dashboard refetch every 3 seconds while the tab is visible, through one shared hook that replaces the dashboard's 15 second timer and the list's refetch on focus. It pauses while hidden, refetches at once on becoming visible, skips a tick while a request is still running, and backs off to 15 seconds after three failures in a row (back to 3 on the next success). A failed background refetch keeps what is on screen. A reassignment shows on the mechanic's screen within 3 seconds (VR-RL-12).
- **AC-22**: The background refetch updates the page behind an open edit dialog but never its form, and the dialog keeps the `lastUpdatedAt` it opened with, so a change by someone else shows up as AC-18's 409.
- **AC-23**: When a background refetch of a ticket answers 403 (the mechanic was removed), the page shows a toast "You're no longer assigned to REP-…" and goes to the repair list. A 404 shows "This ticket is no longer available." and goes to the list. The first load keeps today's error screen.

## Decision

**Chosen option**: Option 1: per section endpoints and dialogs on the detail page, with 3 second polling.

The repair detail page gets one Edit dialog per block, each backed by its own endpoint with the stale check and its own audit rows. A new `ticket.edit` key covers details and issues, `ticket.assign` covers mechanics, and three ticket columns record the last edit. Live updates come from polling the existing reads every 3 seconds while visible.

**Implementation skills**: `nestjs-best-practices` (`.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`.claude/skills/prisma-client-api/`) · `prisma-cli` (`.claude/skills/prisma-cli/`) · `react-hook-form` (`.claude/skills/react-hook-form/`) · `vercel-react-best-practices` (`.claude/skills/vercel-react-best-practices/`, for the polling hook) · `ask-sonner` (`.claude/skills/ask-sonner/`, for the removed toast)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch** (one additive migration, no backfill):

| Entity | Change |
|---|---|
| `RepairTicket` | add `editedAt DateTime? @db.Timestamptz(6)`, `editedByUserId String? @db.Uuid` (welinc-auth User.id, no FK), `editedByName String? @db.VarChar(100)` |
| `RepairTicket` (existing) | `driverId`, `odometer`, `priority`, `accountType`, `corporation` written by the details save |
| `TicketAssignment` (existing) | rows created and deleted by the mechanics save; `@@unique([repairTicketId, mechanicId])` unchanged |
| `RepairIssue`, `RepairIssueStep` (existing) | created, updated, deleted by the issue saves; steps and `IssueEmbedding` cascade on delete |
| `Attachment.issueId`, `KnowledgeSuggestion.repairIssueId` (existing) | `SetNull` on issue delete, unchanged |
| `AuditLog` (existing) | new action values `TICKET_EDITED`, `ISSUE_ADDED`, `ISSUE_EDITED`, `ISSUE_REMOVED` in `AUDIT_ACTIONS`; the column is a string, so no migration |

**State transitions**: only M1 (`OPEN` → `ASSIGNED`, first mechanic added) and M2 (`ASSIGNED` → `OPEN`, last mechanic removed), both already in `TICKET_MOVES` with trigger `assignment`, applied through `applyStatusMove`. No other edit changes the status.

**API surface** (all under the `/repairs` gateway route, bearer JWT):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/repairs/:id/details` | PATCH | `lastUpdatedAt` (req), any of `driverId` \| `newDriver {name, licenseNumber}`, `odometerReading`, `confirmOdometerJump`, `priority`, `accountType`, `corporationId`; `reason` on closed | the ticket as `GET /repairs/:id` returns it | `ticket.edit` | 400 `TICKET_LOCKED`, `REASON_REQUIRED`, `ODOMETER_BELOW_LAST`, `ODOMETER_ABOVE_NEXT`, `ODOMETER_JUMP_UNCONFIRMED`, both driver fields; 404; 409 `STALE_TICKET`, `DRIVER_EXISTS` |
| `/repairs/:id/assignments` | PUT | `lastUpdatedAt` (req), `mechanics: [{id}]` (may be empty), `reason` on closed | the ticket | `ticket.assign` | 400 `TICKET_LOCKED`, `REASON_REQUIRED`, duplicate or inactive mechanic, verifier added; 404; 409 |
| `/repairs/:id/issues` | POST | `lastUpdatedAt`, `categoryId`, `rootCause`, `description?` (required without an entry), `knowledgeEntryId?`, `reason` on closed | the ticket | `ticket.edit` | 400 inactive category or entry, `TICKET_LOCKED`, `REASON_REQUIRED`; 404; 409 |
| `/repairs/:id/issues/:issueId` | PATCH | `lastUpdatedAt`, `categoryId`, `text` (the description after its `[System] ` prefix, 1 to 600, prefilled), `reason` on closed | the ticket | `ticket.edit` | as above; 404 issue not on ticket |
| `/repairs/:id/issues/:issueId/remove` | POST | `lastUpdatedAt`, `reason` on closed (a POST, since proxies may drop a DELETE body) | the ticket | `ticket.edit` | 400 `LAST_ISSUE`, `TICKET_LOCKED`, `REASON_REQUIRED`; 404; 409 |
| `/repairs/:id/assignments` | POST | (existing, spec 0016) | | `ticket.assign` | kept as a thin alias that adds to the current list and calls the PUT logic, so an older web build keeps working; removal is a Follow-up |
| `GET /repairs/:id`, `GET /repairs` | GET | unchanged | adds `editedAt`, `editedByName`, and on list rows `mechanicCount` | unchanged | 403 for a mechanic no longer assigned (used by AC-23) |

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Any edit | who edited, `editedByUserId`, `editedByName`, audit actor | verified token (`sub`, `whoName(user)`), never the body |
| Any edit | `editedAt`, audit `createdAt`, `updatedAt`, `lastActivityAt` | one server `now` per save |
| Any edit | stale check | body `lastUpdatedAt` vs `RepairTicket.updatedAt` |
| Any edit on closed | audit note | body `reason` |
| Details | driver before/after in audit | `Driver.name` and `licenseNumber` of old and new driver |
| Details | odometer floor | max `odometer` of the truck's non cancelled tickets other than this one ordered before it by `(createdAt, id)`, else none (no floor, decided 2026-11-03 after `/check verify` found the oldest ticket on a truck could not be corrected when the floor fell back to `Vehicle.odometer`); a new helper in `odometer.ts`, never `vehicleOdometerFloor` (it includes this ticket) |
| Details | odometer ceiling | min `odometer` of those tickets ordered after it by `(createdAt, id)`; none means no ceiling |
| Details | blocking ticket in errors | `repairNumber` of the floor or ceiling ticket |
| Issue add | stored description | shared helper extracted from create: `[${category.name}] ${rootCause}: ${description \|\| entry.name}` |
| Issue edit | stored description | `[${newCategory.name}] ${text}`; the dialog's prefill is the stored description with its leading `[…] ` removed (root cause has no column of its own) |
| Details | jump threshold | setting `tickets.odometer_jump_warn_km` (spec 0012) |
| Details | corporation name | active `LookupValue` in the corporation list by `corporationId` (spec 0016 `corporationFor`) |
| Mechanics | which move | `findMove(status, target)` with trigger `assignment`: M1 when the list goes from empty to non empty on `OPEN`, M2 when it goes empty on `ASSIGNED` |
| Mechanics | audit names | `Mechanic.name` of removed and added rows |
| Mechanics | verifier block | `RepairTicket.verifiedByUserId` vs `Mechanic.authUserId` |
| Mechanics picker | open count and busy | existing `openCount` and `busy` from the assignment picker (spec 0016) |
| "No mechanic" flag | ownerless | list row `mechanicCount === 0` and status in `IN_PROGRESS`, `ON_HOLD`, `FOR_VERIFICATION`, `OUTSOURCED`, `PENDING_APPROVAL` |
| Issue add | copied steps | `KnowledgeEntry.steps` at save time (spec 0007 copy) |
| Issue remove | confirm text | the issue's `steps` with `checkedAt` and its `resolutionNote`, already in the ticket read |
| Removed toast | repair number | the last loaded ticket on the page |
| Polling | interval | `TICKET_POLL_MS = 3000` constant in web-vrms (not a setting) |

**Key invariants**:
- Every ticket keeps at least one issue (AC-17).
- `ASSIGNED` always has at least one mechanic; `OPEN` never has one after a mechanics save (M1/M2).
- A closed ticket's status never changes from these endpoints, and its verifier is never one of its mechanics.
- Each save is one transaction whose first write is the optimistic `updateMany where { id, updatedAt }` with the stamp; `count === 0` answers 409.
- Mechanics save order: guarded stamp write, then delete removed and create added `TicketAssignment` rows, then (only when M1 or M2 applies) `applyStatusMove(tx, ticket, move, user, null, now, { audit: <the triggering side's event> })` with the other side's audit row written separately with the same `now`; with no move, both rows are written directly. `applyStatusMove` itself does not stamp `edited*`, so the stamp comes only from the first write.
- Audit rows are written only for real changes, with actor fields from the token.

**Security model**:
- `ticket.edit` (Admin default) for details and issues; `ticket.assign` (Admin and Chief default) for mechanics; checked by the route guard and again on the ticket (ability `read` on the subject, so a caller only edits tickets they can see).
- Mechanics never edit; they only see the result.
- Inputs are validated with DTOs (class-validator, trimmed strings, UUIDs, enums, length limits matching create).
- Costs are untouched, so the mechanic cost hiding rules (spec 0010) are unchanged. `TICKET_EDITED` rows carry no cost fields.

**Configuration required**: none (no new env vars). One new catalog key `ticket.edit` in `src/auth/permissions/catalog.ts`.

**Critical test scenarios**:
- Happy path: the Admin swaps the driver, corrects the odometer and raises priority in one save, and one `TICKET_EDITED` row lists three changes with the stamp set. Verifies **AC-4**, **AC-5**, **AC-6**, **AC-8**, **AC-19**.
- Mechanics: removing the only mechanic on `ASSIGNED` returns it to `OPEN` with one `MECHANIC_UNASSIGNED` row carrying the status change. The same save on `IN_PROGRESS` keeps the status and the dashboard shows "No mechanic". Verifies **AC-10**, **AC-12**, **AC-13**.
- Concurrency: two Admins open the same dialog, and the second save gets 409 and the reload prompt. Verifies **AC-18**, **AC-22**.
- Odometer: a reading below the previous ticket's answers `ODOMETER_BELOW_LAST`, and one above a later ticket's answers `ODOMETER_ABOVE_NEXT`. Verifies **AC-5**.
- Last issue: deleting the only issue answers `LAST_ISSUE`. Deleting an issue with ticked steps keeps its photos on the ticket with no issue tag. Verifies **AC-16**, **AC-17**.
- Locked: editing a closed, not unlocked ticket answers `TICKET_LOCKED`. On an unlocked one with no reason it answers `REASON_REQUIRED`. Adding the verifier answers 400. Verifies **AC-2**, **AC-3**, **AC-11**.
- Auth: a Chief calling `PATCH /details` gets 403, while the same Chief's PUT assignments succeeds. A Mechanic gets 403 on both. Verifies **AC-1**.
- Live: a mechanic on the detail page is removed, and within 3 seconds sees the toast and lands on the list. A mechanic newly assigned sees the ticket on their list within 3 seconds. Verifies **AC-21**, **AC-23**.

## Build plan

Tracer Bullet: the first milestone carries one thin edit (priority) through every layer, with the migration, the stamp, the audit row, the 409 and polling, then each later milestone thickens one block.

1. **Thin thread: priority edit end to end.**
   - Migration for the three `edited*` columns. Add `ticket.edit` to the catalog and the ability factory, and `TICKET_EDITED` to `AUDIT_ACTIONS` with a builder.
   - `PATCH /repairs/:id/details` with priority only, covering the stale check, the lock and reason rules, and the stamp.
   - `editedAt` and `editedByName` in the ticket read.
   - Web: `editTicketDetails` API call, the Vehicle & driver block's Edit dialog with priority only, the 409 reload, and "Edited … by …" in the side panel.
   - Satisfies **AC-1**, **AC-2**, **AC-3**, **AC-6**, **AC-8**, **AC-18**, **AC-19**, **AC-20**.
2. **Live updates.**
   - A shared `useVisiblePoll` hook (3 seconds, paused while hidden, keeps data on failure), used by `useRepairTicket`, `useRepairList` and `useDashboardData` (replacing its 15 second poll).
   - Dialogs keep their opened `lastUpdatedAt`.
   - A 403 or 404 on a background refetch shows the toast and navigates to the list.
   - Satisfies **AC-21**, **AC-22**, **AC-23**.
3. **Rest of details.**
   - Driver swap (existing or new by license, reusing `driverFor` and the create form's driver picker), odometer floor and ceiling helper with jump confirm, account type and corporation.
   - Audit before and after per field.
   - Satisfies **AC-4**, **AC-5**, **AC-7**, **AC-8**.
4. **Mechanics.**
   - `PUT /repairs/:id/assignments` with the diff, M1/M2 through `applyStatusMove`, the verifier block, and the unassign then assign audit rows.
   - The Mechanics block Edit dialog reuses the assign picker (open count, busy).
   - The Open ticket Assign action moves to PUT; the POST route stays as a thin alias.
   - `mechanicCount` on list rows and the "No mechanic" attention item.
   - Satisfies **AC-8b**, **AC-9**, **AC-10**, **AC-11**, **AC-12**, **AC-13**.
5. **Issues and sweep.**
   - Add, edit and remove issue endpoints with `ISSUE_ADDED`, `ISSUE_EDITED` and `ISSUE_REMOVED`, the shared description helper, the step copy and embedding queue, the known fix clear on a system change, the last issue guard, and the remove confirm naming what is lost.
   - The audit timeline and the ticket Activity labels and action filter for the new actions.
   - Backend and web tests, lint, typecheck, build, and axe at 375px and 1280px for Admin, Chief and Mechanic.
   - Satisfies **AC-14**, **AC-15**, **AC-16**, **AC-17**, **AC-19b**, **AC-20**.

## Consequences

**Positive**:
- Intake mistakes become fixable without a database edit, and every fix is traceable (audit row plus last edit stamp).
- The Chief can rebalance work at any stage, as spec 0015 intended.
- 3 second polling meets VR-RL-12 with no new infrastructure before hosting.
- No new table. The migration is three nullable columns.

**Negative / tradeoffs**:
- Polling three screens every 3 seconds is roughly 7 requests a second at about 20 users, which is fine at this size. It grows with users, and SSE should replace it if that ever matters (see Follow-up).
- An In progress ticket can sit with no mechanic. Only the attention flag guards it.
- Removing an issue loses its ticked steps and embedding for good. Only the audit row's text remains.
- The odometer ceiling can block a legitimate fix when a later ticket also holds a wrong reading. That ticket must be fixed first.
- Two assign routes live side by side until the POST alias is removed.
- A system change can clear a linked known fix and its ticked steps without a separate relink step.
- The dashboard poll moves from 15 seconds to 3 seconds, so its spec 0002 note (AC-13) is now out of date.

**Neutral**:
- `editedAt` duplicates what the audit rows already know. It is a convenience read, never the source of truth.
- Changing priority does not touch `dueAt`. Due dates belong to feature 42.

## Follow-up

- [ ] Remove the `POST /repairs/:id/assignments` alias once every deployed web build uses the PUT.
- [ ] If polling load ever matters (phones on mobile data), add a light `GET /repairs/:id/version` check so a full fetch runs only on change.
- [ ] Feature 28 (notifications): consider replacing the 3 second poll with SSE (server sent events) once a push channel exists, and notify a mechanic when added or removed here.
- [ ] Feature 57 (mechanic workload): Unassign and Reassign there should call `PUT /repairs/:id/assignments`.
- [ ] Feature 33 (admin status override): an ownerless ticket can still be moved by `ticket.administer`. Keep that path working.
- [ ] Feature 42 (deadlines): decide whether a priority change recomputes a `PRIORITY` sourced `dueAt`.
- [ ] Feature 24 (full ticket audit trail): the new actions already join the timeline. Remarks are still not audited.
- [ ] Spec 0002: update its poll interval note to 3 seconds (via /sync).
- [x] `/develop`: `ticketOdometerBounds` in `odometer.ts` returns a `null` floor when no earlier ticket exists (it currently falls back to `Vehicle.odometer`); skip the below check and the jump confirm for a `null` floor, add a unit test with no earlier ticket, then re-run the "no earlier ticket" step in `verify.md`.
- [ ] Consider a `verify.md` for this spec before `/check verify`.
- [ ] /sync: record `ticket.edit`, the new audit actions, the `edited*` stamp and `useVisiblePoll` in `welinc-backend-vrms/AGENTS.md` and `welinc-web-vrms/AGENTS.md`.
