# 0004. Repair list as an urgent queue, repair detail around its next action

**Date**: 2026-10-22
**Status**: Proposed

## Summary

This spec rebuilds the Repair tickets list and the repair detail page on the spec 0001 components, for scope feature 11. The list becomes a queue of open tickets, most urgent first, with filters for status, garage, mechanic and overdue that stay in the URL. The detail page gets a main column and a side panel, and that panel holds one button for the ticket's next step ("Start work", "Send for verification", "Mark completed"), which matches the forward only rule the server already enforces. It needs a small backend change in welinc-backend-vrms (new query params, no migration), so like spec 0003 it is the cross repo spec `AGENTS.md` asks for.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As an admin, I want every open ticket in one list, overdue first, so that I clear the urgent ones before they slip further.
- As an admin, I want to narrow the list by status, garage, mechanic and overdue, and come back from a ticket to the same view, so that I can work through one queue at a time.
- As a mechanic, I want my assigned tickets ordered by due date on my phone, so that I always know which truck to work on next.
- As a mechanic, I want one clear button for the next step on a ticket, within thumb reach, so that I can move my work forward without guessing which status is allowed.
- As an admin, I want a ticket's costs, notes and full activity in one place, so that I can sign off on it without opening other pages.

**Acceptance criteria**:

*Repair list (`/repairs`, admins and mechanics)*

- **AC-1**: The `PageHeader` reads "Repair tickets" with the `Wrench` icon. Admin subtitle: "Open repair tickets across every garage." Mechanic subtitle: "Open repair tickets assigned to you." Admins get a primary `Button` "New repair ticket" (`Plus` icon) linking to `/repairs/new`; mechanics get no action.
- **AC-2**: The list holds open tickets only: `PENDING`, `IN_PROGRESS` and `FOR_VERIFICATION`. Completed and cancelled tickets live on History (spec 0003) and never appear here.
- **AC-3**: Rows are ordered by the server: `targetDueDate` earliest first (so overdue tickets come first), tickets with no due date last, then `createdAt` newest first, then `id` descending. The order is the same on every page and after a refetch.
- **AC-4**: Filters: a search box (repair #, plate or driver, as today, sent 300ms after typing stops); **Status** (All open (default), Pending, In progress, For verification); **Garage** (All garages, then the list from `getGarages()`); **Mechanic**, admins only (All mechanics, then the list from `GET /vrms/mechanics/available`); and an **Overdue only** toggle. Filtering runs on the server. Changing any filter goes back to page 1. At 375px the filters wrap with no horizontal scroll.
- **AC-5**: The filters and page live in the URL: `q`, `status`, `garage`, `overdue=1`, `mechanic`, `page`. Default values are left out of the URL. Filter and page changes replace the current history entry (no extra back button steps). Opening `/repairs` with these params shows that view, and coming back from a ticket (the back link or the browser back button) shows the same filters and page. An unknown or malformed value falls back to its default. A mechanic's UI ignores `mechanic`.
- **AC-6**: The list uses `DataTable` with these columns: **Repair #** (`mobile: 'title'`); **Vehicle** plate (`mobile: 'subtitle'`); **Status** `StatusBadge` (`mobile: 'badge'`); **Due** (`mobile: 'field'`); **Issue** (`mobile: 'field'`), cut off at one line with the full text in a tooltip; **Garage** (`mobile: 'field'`). The Due cell shows the overdue text in `destructive` with an `AlertTriangle` icon (accessible name "Overdue") for an overdue ticket, the due soon text for a future due date, and `"—"` with no due date (see *Text and formatting rules*). There is no horizontal scroll at 1280px.
- **AC-7**: Clicking a row (or card) opens `/repairs/:id`. The `⋮` row menu holds **View details** (`/repairs/:id?mode=readonly`) and **Edit ticket** (`/repairs/:id`), for admins and mechanics alike.
- **AC-8**: 20 rows per page with the `DataTable` pagination. If the URL asks for a page past the last one (say, after tickets closed), the list moves to the last page and updates the URL.
- **AC-9**: States: skeleton rows while loading. On a load failure, `ErrorState` with "Try again". With no open tickets at all: admins see `EmptyState` (`ClipboardList`) "No open repair tickets" / "New tickets show up here." with the "New repair ticket" button; mechanics see "No repair tickets assigned to you" / "Tickets an admin assigns to you show up here." With filters that match nothing: "No tickets match these filters" with a "Clear filters" button that resets every filter to its default. "No open tickets at all" means an empty result while every filter is at its default, search included; an empty result with any filter or search set is the filtered state.
- **AC-10**: When the browser tab becomes visible again, the list refetches the same filters and page (using the search text already sent, not text still inside the 300ms wait). While it refetches, the current rows stay on screen (no skeleton). If the refetch shows the page is now past the last one, AC-8 applies. If that refetch fails, the rows already shown stay and nothing else changes; the next visibility change tries again.
- **AC-11**: The due text and the overdue mark are measured against `fetchedAt`, the time of the last successful fetch, as in spec 0002, so a row never changes its label without new data. "Overdue" means the spec 0002 rule: an open ticket with a parsable `targetDueDate` earlier than that time. `targetDueDate` is an exact moment (`Timestamptz`), not a calendar day, so the client and the server's Overdue only filter compare the same kind of value.

*Repair detail (`/repairs/:id`, admins and mechanics)*

- **AC-12**: The `PageHeader` title is the repair number, with the `Wrench` icon and the subtitle "{plate} · {model}" (just the plate when there is no model). Above it, a back link: for an open ticket "Back to repairs", which returns to the list view the user came from (same filters and page), or plain `/repairs` when they arrived some other way (the dashboard, a pasted link); for a closed ticket "Back to history", linking to plain `/history` (History's filters are not restored; accepted).
- **AC-13**: From 1024px up, the page has two columns: a main column (about two thirds) and a side panel (about one third) that stays in view while the main column scrolls. Below 1024px it is one column with the side panel first. The **side panel** holds, in order: the status card (`StatusBadge`, for admins a "Locked" or "Unlocked for editing" badge on closed tickets (the API sends `isUnlocked` to admins only, so mechanics see no lock badge), the next action from AC-14, and Cancel ticket from AC-16), then **Details** (Due date with its due text, Garage, Created, Updated, and Closed for closed tickets), then **People** (Driver, with "Verified" or "Not verified" for admins, and the assigned mechanics, with "Outsourced" and the shop name where it applies). The **main column** holds, in order: **Notes** (only when one exists: cancellation reason and failed verification reason as `destructive` callouts, then **Latest remark**), **Vehicle** (plate, model, odometer), **Issues** (numbered), **AI diagnosis**, **Costs** (admins only), and **Activity** (admins only).
- **AC-14**: The next action depends on the status, the role and the lock state:

  | Status | Admin | Mechanic (always one assigned to the ticket) |
  |---|---|---|
  | `PENDING` | "Start work" (to `IN_PROGRESS`) | "Start work" |
  | `IN_PROGRESS` | "Send for verification" (to `FOR_VERIFICATION`) | "Send for verification" |
  | `FOR_VERIFICATION` | "Mark completed" (to `COMPLETED`) | No button; text "Waiting for an admin to sign off." |
  | `COMPLETED` or `CANCELLED`, locked | "Unlock ticket" (AC-17) | No button; text "This ticket is closed." |
  | `COMPLETED` or `CANCELLED`, unlocked | No button; text "Unlocked for editing. Saving costs locks it again." | No button; text "This ticket is closed." |

  The page never offers a status move the server rejects (no going back a step, no skipping one). With `?mode=readonly`, no action, Cancel ticket, Edit costs or bottom bar shows; the status card reads "View only" with a link "Open editable view" to `/repairs/:id`, shown only when the table above would give this user a button.
- **AC-15**: Pressing a status button opens a `ResponsiveDialog`: the title is "{action} on {REP}?" ("Start work on REP-0012?"), with an optional **Remarks** field (up to 500 characters) and the confirm button labeled with the action. The confirm button shows a spinner and is disabled while saving. On success the dialog closes, the page shows the ticket the API returned (new status, new next action), and a success toast reads "{REP} moved to {status label}." On a 409 see AC-19. On any other error (a 403 included), a `FormAlert` inside the dialog shows the message from `getApiErrorMessage`, and the dialog and the typed note stay. The note clears after a success or a 409. The note is saved as the ticket's latest remark only: the server writes no audit row for it, so Activity never shows it, and an empty note leaves the previous remark in place. When an admin presses "Start work" or "Send for verification" on a ticket with no assigned mechanics, the dialog also shows a warning callout "No mechanic is assigned yet." and the confirm button still works.
- **AC-16**: Admins see **Cancel ticket** (a `destructive` outline button) under the next action on open tickets only. It opens a `ResponsiveDialog` "Cancel {REP}?" with a required **Cancellation reason** field (up to 500 characters; an empty or blank reason shows the inline error "Enter a reason for cancelling."), a `destructive` confirm button "Cancel ticket" and a "Keep ticket" button. Success and errors behave as in AC-15. Mechanics never see it.
- **AC-17**: "Unlock ticket" opens a `ResponsiveDialog` "Unlock {REP}?" with the description "Unlocking lets you edit costs. Saving costs locks it again." and a required **Reason** field (up to 500 characters, inline error "Enter a reason for unlocking."). On success the dialog closes, the page shows the returned ticket and a toast reads "{REP} is unlocked." Unlock sends no `lastUpdatedAt`, so it has no 409; instead, on a 400 (another admin unlocked it first, or it is no longer closed) the dialog closes, an error toast shows the server's message, and the page reloads the ticket. Any other error shows in a `FormAlert` inside the dialog. `UnlockTicketModal` is deleted.
- **AC-18**: When an admin presses "Mark completed" and the ticket has no costs (parts, labor and total all empty, and no itemized parts), the dialog also shows a warning callout: "No costs are recorded yet. Once completed, the ticket locks, and costs can only be added after an unlock." with a "Go to costs" link that closes the dialog and scrolls to the Costs section. The confirm button still works.
- **AC-19**: If a status change or cancel returns 409 (the ticket changed since it was loaded), the dialog closes, an error toast reads "This ticket changed since you opened it. We loaded the latest version.", and the page reloads the ticket from the API and shows its current next action. If a cost save returns 409, the cost form stays open with the values the admin typed, the page reloads the ticket underneath (so the next save sends the new `lastUpdatedAt`), and a `FormAlert` in the form reads "Costs changed since you opened this. Check the current values before saving again." If the reloaded ticket no longer allows editing costs (AC-21), the form closes and the same toast as above shows. Nothing is retried automatically.
- **AC-20**: Below 1024px, the next action button (only that button, never Cancel ticket) also shows in a bar fixed to the bottom of the screen: directly above the `MobileTabBar` below 768px (offset by the tab bar's height including its safe area padding, and stacked below the tab bar's `z-40`), at the bottom edge with safe area padding from 768px to 1023px. The page adds bottom padding equal to the bar's height on top of the shell's own `pb-24`, so nothing hides behind the bar. The bar shows only when AC-14 gives the user a button. From 1024px up there is no bar.
- **AC-21**: The **Costs** section (admins only) shows Parts, Labor and Total, plus the itemized parts table (description, unit cost, quantity, subtotal) when the costs are itemized, or "No costs recorded yet." An **Edit costs** button shows only when the ticket is `FOR_VERIFICATION`, or closed and unlocked, and not in read only mode. Edit turns the section into a form: Lump sum or Itemized, parts cost or item rows (add and remove; description and unit cost required, quantity a whole number of at least 1), labor cost, all amounts 0 or more, with a live total. Validation errors show inline under each field. Save sends the existing `UpdateCostsPayload` (`isLumpSum`, `laborCost`, `lastUpdatedAt`, plus `partsCost` for lump sum or `parts: { description, unitCost, quantity }[]` for itemized, only the active mode's field), as `CostEncodingPanel` does today. Save shows a spinner; Cancel restores the saved values. On an unlocked closed ticket, Save first asks through `confirm()` "Save costs and lock {REP}?". On success the section returns to the summary with the returned values and a toast reads "Costs saved." Mechanics never see this section (the API never sends them costs).
- **AC-22**: The **AI diagnosis** section keeps today's behavior for both roles (run the diagnosis on the ticket's issues, show the result, the similar cases and the rating), rebuilt on spec 0001 components and tokens: no inline styles, no purple or glowing "AI" styling, no emoji, and the rating stars are buttons with accessible names ("Rate 1 out of 5").
- **AC-23**: The **Activity** section (admins only) starts collapsed. On first expand it loads the ticket's newest 50 events from `GET /vrms/repairs/audit-logs?ticketId=…` and renders each with `AuditEventItem`, without the repair number link. While older events exist, "Load older events" fetches the next 50. With no events it reads "No activity recorded yet."; on a load failure it shows "Couldn't load activity." with "Try again". The shop change and audit blocks of today's page, and `AuditLogCollapsible`, are gone.
- **AC-24**: States: a skeleton shaped like the two column layout while loading. A 404 shows `EmptyState` "Repair ticket not found" with a "Back to repairs" button. A 403 (a mechanic opening a ticket not assigned to them, which also covers a mechanic account with no linked record) shows `EmptyState` "This ticket isn't assigned to you" with the same button. Any other failure shows `ErrorState` with "Try again".

*Backend (welinc-backend-vrms)*

- **AC-25**: `GET /vrms/repairs` takes its query through a request DTO (replacing the raw `parseInt` calls): `search?`, `status?`, `garageId?` (uuid), `mechanicId?` (uuid), `overdue?` (`true` or `false`), `page?`, `limit?` (integers of at least 1, no upper cap, so the dashboard's call keeps working). Bad values return 400. `overdue=true` keeps open tickets whose `target_due_date` is set and earlier than the server's current time. `mechanicId` keeps tickets that mechanic is assigned to; an unknown id returns an empty list. `status` still accepts any `RepairStatus` (as today), and `overdue=true` only ever matches open tickets, so `overdue=true&status=COMPLETED` returns an empty list. Rows are ordered as AC-3. With neither `page` nor `limit`, every matching row is returned, as today; with only one of them, the other defaults (page 1, limit 20).
- **AC-25b**: The ticket response sends a stored cost of 0 as `0`, not `null`: `formatTicket` checks `partsCost`, `laborCost` and `totalCost` with `!= null` instead of truthiness. So a ₱0 labor cost counts as recorded for AC-18 and shows as ₱0.00.
- **AC-26**: A mechanic's `GET /vrms/repairs` always returns only tickets they are assigned to: `mechanicId` is ignored for mechanics, and a mechanic account with no linked mechanic record gets an empty list with `total: 0` (today it gets every open ticket).
- **AC-27**: `GET /vrms/repairs/audit-logs` accepts `ticketId?` (uuid) and then returns only that ticket's events, with the same paging, shape and admin only access as spec 0003. An unknown id returns an empty list.
- **AC-28**: `PATCH /vrms/repairs/:id/status` rejects a `remarks` or `cancellationReason` longer than 500 characters with 400, matching the unlock reason's limit.
- **AC-29**: The ticket response no longer carries `auditLog` or `shopChangeLog` (Activity now reads the audit endpoint), and nothing in web-vrms reads them.

*Both pages*

- **AC-30**: Both pages, and every component they render from `src/features/repair/components/`, use only spec 0001 components and theme tokens: no inline `style`, no legacy classes, no `LegacyButton`, no hex values. Lint passes with the token rules. Both work at 375px and 1280px with no horizontal scroll, and axe reports no serious or critical issues on `/repairs` and `/repairs/:id` for an admin and a mechanic.

## Decision

**Chosen option**: Option 3: Rework both pages, backed by a few new query params

The list becomes a server sorted, server filtered queue of open tickets with its state in the URL, and the detail page becomes a main column plus a side panel built around one next action, with costs, AI diagnosis and a ticket scoped Activity in the main column.

**Implementation skills**: `shadcn` (`shadcn-ui/ui`, `.claude/skills/shadcn/`) · `react-hook-form` (`pproenca/dot-skills`, `.claude/skills/react-hook-form/`, the status, cancel, unlock and cost forms, `useFieldArray` for item rows) · `ask-sonner` (`emilkowalski/skills`, `.claude/skills/ask-sonner/`) · `vercel-react-best-practices` (`vercel-labs/agent-skills`, `.claude/skills/vercel-react-best-practices/`) · `vercel-composition-patterns` (`vercel-labs/agent-skills`, `.claude/skills/vercel-composition-patterns/`) · `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`)

**Calls made in this spec** (each with the runner up):
- **Activity reads the audit endpoint with a new `ticketId` filter**, not today's `auditLog` and `shopChangeLog` fields. Spec 0003 already copied shop changes into `audit_logs`, so one source gives created, status, cost, unlock and shop events in the shape `AuditEventItem` renders. Runner up: merge the two old arrays on the client, which keeps two shapes and misses `CREATED` rows.
- **Cancel ticket only on open tickets.** The server also allows cancelling an unlocked completed ticket, but unlocking exists to fix costs, and cancelling finished work is a status override (feature 33). Runner up: offer it on unlocked closed tickets too.
- **Remarks and reasons capped at 500 characters on both sides**, matching the existing unlock reason. Runner up: no limit, as today.
- **Mechanics with no linked record get an empty list** (fail closed), the same fix spec 0003 made for history. Runner up: leave it, which shows every open ticket to a misconfigured mechanic account.
- **The mechanic filter lists in house mechanics only**, from the existing endpoint. Runner up: a new endpoint including outsourced mechanics (see Follow-up).
- **Search waits 300ms after typing stops**, as the audit log's repair # search does. Runner up: a request on every keystroke, as today.
- **Detail money keeps centavos**: a `formatPesoExact` helper (two decimals) beside spec 0003's `formatPeso` in `src/lib/utils/format.ts`, because cost entry is exact. Runner up: whole pesos everywhere.

## Feature design

**Data model**: no change. No migration, no new column. (Priority was considered and left out: it is not stored today; see Follow-up.)

**State transitions** (unchanged on the server, now mirrored in the UI):
`PENDING` → `IN_PROGRESS` → `FOR_VERIFICATION` → `COMPLETED`, and an admin may cancel any open ticket (→ `CANCELLED`). Mechanics may make the first two moves on their own tickets. Closed tickets are locked until an admin unlocks them; saving costs locks them again. The UI derives its one next action from this chain (AC-14).

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/repairs` (changed) | GET | `search?`, `status?` (`RepairStatus`), `garageId?` (uuid), `mechanicId?` (uuid, ignored for mechanics), `overdue?` (`true`/`false`), `page?`, `limit?` (int ≥ 1, no cap) | `{ data: RepairTicket[], total }`, ordered `targetDueDate asc nulls last, createdAt desc, id desc`; without `status`, open statuses only (as today) | bearer, ADMIN or MECHANIC | 400 bad uuid, status, boolean or number; 401 |
| `/vrms/repairs/:id` (changed) | GET | `id` | `RepairTicket` without `auditLog` and `shopChangeLog` | bearer, ADMIN or assigned MECHANIC | 401, 403, 404 |
| `/vrms/repairs/:id/status` (changed) | PATCH | `status`, `remarks?` (≤ 500), `cancellationReason?` (≤ 500, required for `CANCELLED`), `lastUpdatedAt` | updated `RepairTicket` | as today | 400 (also over 500 characters), 403, 404, 409 |
| `/vrms/repairs/audit-logs` (changed) | GET | spec 0003's params plus `ticketId?` (uuid) | `{ data: AuditEvent[], nextCursor }` | bearer, ADMIN | 400, 401, 403 |
| `/vrms/repairs/:id/costs` | PATCH | unchanged | | | 409 handled per AC-19 |
| `/vrms/repairs/:id/unlock` | PATCH | unchanged (reason ≤ 500) | | | |
| `/vrms/config/garages`, `/vrms/mechanics/available` | GET | unchanged, read for filter options | | | |

The request DTO is `FindRepairsQueryDto` in `src/modules/vrms/dto/find-repairs-query.dto.ts`, in the style of `history-query.dto.ts` (`@Type(() => Number)` for numbers, a `@Transform` for the boolean). `getRepairs()` in `src/lib/api/repairApi.ts` changes to take one params object (`{ search, status, garageId, mechanicId, overdue, page, limit }`); the dashboard's two calls move to it with the same values.

**Text and formatting rules** (client):
- Due text: the spec 0002 helpers in `src/features/dashboard/lib/attention.ts` (`isOverdue`, `overdueText`, `dueSoonText`), moved to `src/lib/utils/due.ts` so both features import them. Overdue gives "Due today" or "Overdue by N days"; future gives "Due today" or "Due in N days".
- Dates: `Oct 22, 2026` (the existing `formatShortDate`; `formatDate` adds the time and is not used here).
- Money on the detail page: `formatPesoExact`, `₱` plus `Intl.NumberFormat('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })`.
- Status labels in toasts and dialogs: the `StatusBadge` sentence case labels ("In progress"), read from one exported map, not retyped.

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| List | Rows, total | `GET /vrms/repairs` with the URL filters |
| List | Order | Server `orderBy` (AC-3) |
| List | Due text, overdue mark | `targetDueDate` against the client's `fetchedAt` (time of the last successful fetch) |
| List | Overdue only filter | Server: `target_due_date < now()` on open tickets. It can differ from the client's mark for a ticket that came due in the seconds between the server query and render; accepted |
| List | Issue summary | `issueDescription` (the server joins issue descriptions with ", ") |
| List | Garage | `garageLocation` |
| List filters | Garage options | `getGarages()` (`GET /vrms/config/garages`), sent as `garageId` |
| List filters | Mechanic options | `GET /vrms/mechanics/available` (active in house mechanics), sent as `mechanicId` |
| List filters | Role (show Mechanic filter, header action) | `user.role` from `authStore` |
| List | Filter and page state | URL search params (AC-5) |
| Detail | Back link target | `location.state.from` (the list's pathname plus search), set by the list when it navigates; else `/repairs` for open, `/history` for closed |
| Detail | Next action | Derived from `status`, `user.role`, `isUnlocked` and `?mode=readonly` (AC-14). Assignment needs no check: the API only returns a ticket to a mechanic who is assigned (403 otherwise) |
| Detail | Due text | `targetDueDate` against the time the ticket loaded |
| Detail | "No costs" warning | `partsCost`, `laborCost` and `totalCost` all null, and `repairParts` empty |
| Detail | Driver verified mark | `driverIsVerified` (sent to admins only) |
| Detail | Notes | `cancellationReason`, `failedVerificationReason`, `remarks` (the latest non empty remark a status update stored; not audited) |
| Detail | Lock badge | `isUnlocked` with a closed status, admins only (mechanics never receive `isUnlocked`) |
| Status dialog | "No mechanic" warning | `mechanics` empty on the loaded ticket |
| Costs | Recorded or not | `partsCost`, `laborCost`, `totalCost` (0 sent as 0 after AC-25b) and `repairParts` |
| Status change | `lastUpdatedAt` | The loaded ticket's `updatedAt` (optimistic locking, as today) |
| Status change | Stale detection | HTTP 409, read with `getApiErrorStatus` |
| Status change | Toast status label | The exported `StatusBadge` label map |
| Activity | Events | `GET /vrms/repairs/audit-logs?ticketId=<ticket id>` |
| Not found vs not assigned | Which empty state | `getApiErrorStatus`: 404 or 403 |

**Key invariants**:
- The UI never offers a status move the server rejects: one forward move per status, cancel for admins on open tickets.
- The list and the dashboard use the same overdue rule and the same due text helpers.
- A mechanic can never widen their list: the server scopes it, ignores `mechanicId`, and returns nothing for a mechanic with no linked record.
- Costs never reach a mechanic, enforced by the server (unchanged), not just hidden.
- Every status, cancel and cost write sends `lastUpdatedAt`; a stale write never overwrites newer data.
- One audit source: the detail Activity and the audit log page read the same endpoint and render with the same component.
- No inline style, hex value, legacy class or `LegacyButton` in `src/features/repair/pages/RepairListPage.tsx`, `src/features/repair/pages/RepairDetailPage.tsx` or the components they render.

**Security model**: unchanged roles. Admins see every open ticket; mechanics see only tickets they are assigned to, on the list and the detail page (403 otherwise). Only admins can complete, cancel, unlock, see costs and read Activity (the audit endpoint stays admin only). The new `ticketId` filter is behind the same admin guard. No new personal data is stored or sent.

**Failure and edge cases**:
- Garage or mechanic options fail to load: that filter shows only its "All" option and the list still works.
- A URL with a `garage` or `mechanic` id that no longer exists: the server returns an empty list and the "No tickets match these filters" state offers Clear filters.
- A ticket closes or reassigns while the list is open: it leaves the list on the next refetch (tab focus or filter change).
- A mechanic presses a button on a ticket an admin just reassigned: the server returns 403, shown in the dialog's `FormAlert`.
- Two people act on one ticket: the second gets 409 and the reload in AC-19.
- The AI service is down: the AI section shows its own error and the rest of the page works.
- A double tap on confirm: the button is disabled while saving, so only one request goes out.
- A ticket whose `targetDueDate` is unparsable: never overdue, Due shows `"—"` (spec 0002 rule).

**Configuration required**: none.

**Critical test scenarios**:
- List queue: as admin, with tickets overdue, due later and without a due date across two pages, the order holds across pages, and Overdue only, Garage, Mechanic and Status each narrow it on the server. Verifies **AC-3**, **AC-4**, **AC-25**
- URL state: filter by garage and page 2, open a ticket, press Back to repairs; the same view returns. Paste a URL with a bad `status`; it falls back to All open. Verifies **AC-5**, **AC-12**
- Mechanic scope: as a mechanic, only assigned tickets show, there is no Mechanic filter, and a request with `mechanicId` still returns only their tickets. A mechanic account with no linked record gets an empty list. Verifies **AC-26**
- Next action walk: as a mechanic, Start work then Send for verification, each through the dialog with a note; then, as admin, Mark completed with no costs shows the warning; the ticket locks and shows Unlock ticket. Verifies **AC-14**, **AC-15**, **AC-18**
- Cancel: as admin, Cancel ticket with a blank reason shows the inline error; with a reason the ticket closes and the back link reads Back to history. Verifies **AC-16**, **AC-12**
- Stale write: open a ticket in two tabs, move it in one, press the next action in the other; the toast shows and the page reloads with the new next action. Verifies **AC-19**
- Costs: on a For verification ticket, switch to Itemized, add rows, leave a description empty (inline error), save; the summary shows the itemized table. Unlock a completed ticket, edit costs, confirm the lock prompt; it locks again. Verifies **AC-21**, **AC-17**
- Activity: as admin, expand Activity on a ticket with created, status, cost and unlock events; each renders like the audit log page, without the repair link. As a mechanic, the section is absent and the audit endpoint returns 403. Verifies **AC-23**, **AC-27**
- Phone: at 375px as a mechanic, the next action bar sits above the tab bar and nothing hides behind it; the read only view shows no bar. Verifies **AC-20**, **AC-14**
- Detail states: an unknown id shows Repair ticket not found; a mechanic opening another mechanic's ticket sees This ticket isn't assigned to you. Verifies **AC-24**
- Limits: a 501 character remark returns 400 from the API and the dialog blocks it first. Verifies **AC-28**, **AC-15**
- Cleanup: searching web-vrms for `auditLog`, `shopChangeLog`, `AuditLogCollapsible`, `UnlockTicketModal` and `LegacyButton` under `features/repair` finds nothing. Verifies **AC-29**, **AC-30**
- 375px and 1280px with axe on both pages, both roles. Verifies **AC-30**

## Migration plan

**Strategy**: no data migration. Additive API changes first, removals last.
**Phases**:
1. Backend: the new list params, order and mechanic scoping, `ticketId` on the audit endpoint, the 500 character limits. All additive, so the current frontend keeps working (it sends none of the new params; the new order only changes which rows it shows first).
2. Frontend: both pages.
3. Backend cleanup: drop `auditLog` and `shopChangeLog` from the ticket response, deployed with or after phase 2, never before (the old detail page reads them).
**Rollback**: revert the frontend commit; phase 1 can stay. If phase 3 shipped, revert it with the frontend.
**Risks**: the 500 character limit rejects longer remarks that the old frontend could send between phases 1 and 2; nothing stored is affected.

## Build plan

The scope tags this feature `· Facade`, but it needs server side sorting and filtering, so like spec 0003 it is built end to end: the API first, then the list on top of it, then the detail page in slices that each leave the page working.

1. Backend list query: `FindRepairsQueryDto`; `garageId`, `mechanicId`, `overdue` filters; the AC-3 `orderBy`; the page and limit defaults; mechanic scoping that ignores `mechanicId` and fails closed with no linked record; the `!= null` cost checks in `formatTicket`. Add Jest tests for the order with null due dates, each filter, both mechanic cases and a 0 cost. Satisfies **AC-3**, **AC-25**, **AC-25b**, **AC-26**
2. Backend small changes: `ticketId` on `AuditEventsQueryDto` and its `where`; `@MaxLength(500)` on `remarks` and `cancellationReason` in `UpdateRepairStatusDto`. Add Jest tests for the `ticketId` filter and the length limit. Satisfies **AC-27**, **AC-28**
3. Shared frontend pieces: move the due helpers to `src/lib/utils/due.ts` (dashboard imports updated); add `formatPesoExact`; export the `StatusBadge` label map; change `getRepairs()` to a params object and update the dashboard's calls; add `ticketId` to `getAuditEvents()`; give `AuditEventItem` an optional `showTicket` prop (default true). Satisfies **AC-6**, **AC-11**, **AC-15**, **AC-23**
4. Rebuild `RepairListPage`: a `useRepairListFilters` hook that reads and writes the URL params; the filter bar; `DataTable` with the AC-6 columns, row click, row menu and pagination; the empty and error states; refetch on visibility; the last page correction. Satisfies **AC-1** to **AC-11**
5. Detail layout and read paths: the two column layout and side panel, PageHeader and back link (the list passes `state.from`), Details, People, Notes, Vehicle, Issues, the loading, 404, 403 and error states. The old status controls stay until step 6 so the page keeps working. Satisfies **AC-12**, **AC-13**, **AC-24**
6. Next action: derive the action from AC-14; the status dialog (react-hook-form, zod, `Field`), the cancel dialog, the unlock dialog replacing `UnlockTicketModal`, the no costs warning, the 409 reload, the bottom bar below 1024px, read only mode. Remove the old dropdown. Satisfies **AC-14** to **AC-20**
7. Costs section: one component with summary and edit modes (react-hook-form with `useFieldArray`, zod), the lock confirm on unlocked tickets, 409 handling; replaces the summary block and `CostEncodingPanel`. Satisfies **AC-19**, **AC-21**
8. AI diagnosis restyle on spec 0001 components, same behavior; route its feedback call through a wrapper in `src/lib/api/aiApi.ts` instead of the raw axios instance import. Satisfies **AC-22**
9. Activity section with the ticket scoped audit fetch and load older; delete `AuditLogCollapsible`; then remove `auditLog` and `shopChangeLog` (and the now dead `DETAIL_AUDIT_ACTIONS`) from `formatTicket`, `ticketInclude()` where only they need it, and the `RepairTicket` type, after confirming nothing else reads them. Satisfies **AC-23**, **AC-29**
10. Run lint, typecheck and build in both repos and `npm run test` in the backend; check both pages at 375px and 1280px in Playwright with axe, as admin and mechanic, including the dialogs and the bottom bar; open the dashboard and History to confirm they still load. Satisfies **AC-30**

## Consequences

**Positive**:
- The list answers "what next?" on every page, the same way the dashboard does, and its filters run on the server.
- The detail page can no longer offer a status move that fails, and a mechanic acts with one tap from a phone.
- Back from a ticket keeps your place, and filtered views can be shared as links.
- One audit source and one renderer for a ticket's history, ready for feature 32 to grow into the full timeline.
- The last legacy styles and the hand built modal on these screens are gone.

**Negative / tradeoffs**:
- Like spec 0003, this breaks the UI refresh's Facade rule: it needs a backend deploy, not just a frontend one.
- The list's Overdue only filter uses the server clock while the Due text uses the browser's last fetch time, so the two can disagree for a few seconds around a deadline.
- There is no priority badge or filter until priority is stored somewhere.
- Outsourced mechanics can't be picked in the mechanic filter.
- Admins see a "Mark completed" warning, not a block, so tickets can still close with no costs.
- The list response still carries the full ticket include (issues, mechanics, parts for admins), which is heavier than the row needs.
- Feature 16 (status lifecycle) will likely rename statuses and add moves, so the AC-14 table will change with it.

**Neutral**:
- The detail page keeps serving closed tickets opened from History.
- The status dialog keeps sending remarks; the ticket still stores only the latest one.

## Follow-up

- [ ] Priority: the create form sends it and `create-repair.dto.ts` accepts it, but nothing stores it. Data model v2 (feature 4) or the issue templates work should own it; then add the badge and filter to this list.
- [ ] Remarks are stored only as the ticket's latest value and never audited, so earlier notes are lost (same open item as spec 0003's follow up). Decide whether status notes belong in the timeline, likely with feature 24 (full audit trail).
- [ ] Unlock and cancel after an unlock have no optimistic lock (no `lastUpdatedAt`), so two admins acting at once is last writer wins. Revisit with feature 16 or 33.
- [ ] Mechanic filter: decide whether outsourced mechanics belong in it (needs an endpoint that lists them).
- [ ] List payload: consider a slim `select` for `GET /vrms/repairs` rows, as spec 0003 did for history, once the dashboard's needs are checked.
- [ ] Feature 16 (status lifecycle), 19 (mechanic status updates), 23 (verification) and 33 (admin override): update the AC-14 table when they change the moves. Features 21 (photos) and 22 (proof) add their sections to the main column after Issues.
- [ ] `welinc-web-vrms/AGENTS.md` still says React 18 and Tailwind 3 and describes the old toast context; `/sync` should refresh it.
- [ ] Before building, `welinc-web-vrms` is on `feat/history-audit-log-refresh` and `welinc-backend-vrms` is on `fix/prisma-config-fallback` with an uncommitted seed change; settle those branches first.
