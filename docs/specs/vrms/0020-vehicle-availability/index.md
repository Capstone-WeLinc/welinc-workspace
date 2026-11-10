# 0020. Vehicle availability: Admin status toggle and a full truck history

**Date**: 2026-11-03
**Status**: Accepted

## Summary

An Admin can now take a truck out of service (Disabled) or put it back (Available) from Settings, Vehicles, with a required reason. A truck with an open repair ticket can't be toggled, because the ticket owns its status until the ticket is closed or cancelled. Every status change, manual or caused by a ticket, writes a row to the truck's history, and a History dialog on each row shows it. It needs one small migration: a ticket link on the history table.

## Requirements

**User stories**:
- As an Admin, I want to disable a truck with a reason so that nobody dispatches or plans around a truck that is out of service.
- As an Admin, I want to make a disabled truck available again so that it rejoins the fleet.
- As an Admin, I want to see a truck's full status and type history, with who, when and why, so that I can explain where any truck stands.

**Acceptance criteria**:
- **AC-1**: With `vehicle.manage`, an Admin sets an Available truck to Disabled by giving a reason (5 to 500 characters after trimming). The truck becomes `DISABLED`, and the same transaction writes one `VehicleChange` row: `field: 'status'`, `before: "AVAILABLE"`, `after: "DISABLED"`, `note` set to the reason, the actor's id, name and email, `repairTicketId` null.
- **AC-2**: The same works the other way: a Disabled truck becomes `AVAILABLE` with a required reason and one matching history row.
- **AC-3**: The only target statuses are `AVAILABLE` and `DISABLED`; any other value is a 400. A truck whose status is `UNDER_MAINTENANCE` can't be toggled (409 `{ statusCode: 409, code: 'VEHICLE_STATUS_LOCKED', message: "This truck's status is set by maintenance." }`). A target equal to the current status is a 409 `{ code: 'STALE_VEHICLE', message: 'This truck changed. Reload and try again.' }` (the screen was out of date).
- **AC-4**: A truck with an open ticket (any status in `OPEN_STATUSES`) can't be toggled: 409 in the same body shape ticket create uses, `{ statusCode: 409, code: 'OPEN_TICKET_EXISTS', message, ticket: { id, repairNumber } }`, with the message built on the server: "This truck has an open repair, R-0123. Change its status after the repair is closed or cancelled." The check runs after taking the same vehicle row lock (`SELECT … FOR UPDATE`) that ticket create takes, so a toggle and a new ticket on the same truck can't both win.
- **AC-5**: The request carries the row's `updatedAt`. It is compared before the transaction (fast fail) and again after the row lock, against `updated_at` read under the lock (not only through an `updateMany` guard). A mismatch answers 409 `{ code: 'STALE_VEHICLE', message: 'This truck changed. Reload and try again.' }` (a new status message; the type edit keeps its own). The screen then shows the toast and reloads the list.
- **AC-5a**: The toggle checks run in this order, and the first failure answers: invalid body (400, from the global `ValidationPipe`, which runs before the handler on every route, so a bad body gets a 400 even for an unknown truck), truck not found or inactive (404), stale `updatedAt` as a fast fail (409, AC-5), then inside the transaction: take the row lock, stale again (AC-5), `UNDER_MAINTENANCE` (AC-3), open ticket (AC-4), target equal to current (AC-3).
- **AC-6**: Ticket create writes a status history row in its transaction, after the ticket insert: `before` = the status read under the lock (`priorVehicleStatus`), `after: "UNDER_REPAIR"`, `repairTicketId` = the new ticket, the creator as actor, `note` null. No row when the truck was already `UNDER_REPAIR` (a stuck truck).
- **AC-7**: The release in `applyStatusMove` (a move into Closed or Cancelled) writes a status history row in the same transaction when the status actually changes: `before` = the truck's status just before the release, `after` = `DISABLED` or `AVAILABLE` (unchanged rule from spec 0016), `repairTicketId` = the ticket, the user making the move as actor, `note` null. No row when before and after are equal.
- **AC-8**: Every vehicle row the API returns (the list, the type `PATCH` and the toggle, all through one shared `present()`) carries `openTicket: { id, repairNumber } | null`, the truck's newest open ticket. After a successful toggle it is always null.
- **AC-9**: `GET /vrms/vehicles/:id/changes?cursor=&limit=` returns the truck's history, newest first, 20 per page by default (max 50), keyset paged on `(createdAt, id)` with `decodeCursor` and `olderThan` from `audit-events.ts` (an invalid cursor is a 400, as there). It fetches `limit + 1` rows and returns `nextCursor` only when the extra row exists. Shape: `{ items: [{ id, field, before, after, note, actorName, createdAt, ticket: { id, repairNumber } | null }], nextCursor }`. It includes both `status` and `vehicleType` rows. Unknown or inactive truck: 404.
- **AC-10**: Each row in Settings, Vehicles has a row menu. Available rows offer "Disable truck", Disabled rows offer "Make available", and every row offers "History". A row with `openTicket` shows the status action disabled, and a separate menu item "Has open ticket R-0123" that links to `/repairs/:id`. An Under maintenance row shows the action disabled with "Set by maintenance". An Under repair row with no open ticket (a stuck truck) offers both actions; the server still has the final say (AC-4).
- **AC-11**: The status action opens the shared dialog: title with the plate, a required reason textarea (5 to 500, with a counter), and a confirm button that names the action. The dialog shows inline validation, locks while the save is in flight, and returns focus to the row menu on close. Success: the row updates in place and a success toast names the plate and new status. A 409 `OPEN_TICKET_EXISTS` or `VEHICLE_STATUS_LOCKED` shows the server message in the dialog, and the list reloads. A stale 409 closes the dialog, shows the stale toast and reloads the list. Any other error shows the message and keeps the typed reason.
- **AC-12**: The Vehicles section gets status filter chips (All, Available, Under repair, Disabled), kept in the address as `?status=`. Under maintenance has no chip on purpose (nothing sets it yet); those trucks show under All. Filtering runs in the browser on the loaded list, combined with the search (both must match). Search text and the page stay in local state as today, and changing the chip or the search resets to page 1. An unknown `status` value falls back to All.
- **AC-13**: "History" opens a dialog listing the truck's changes, newest first, 20 at a time with a "Load more" button. Each entry shows what changed in plain words using the labels in `statusLabels.ts` ("Status: Available → Disabled", "Type: Tractor → Rigid", a null type reads "Not set"), who (`actorName`, or "System" when null), and when (local time). Then, for status rows only: the reason, or "Ticket R-0123" linking to `/repairs/:id`, or "Ticket removed" when both `note` and the ticket are null. Type rows never show "Ticket removed". The dialog has loading, empty ("No changes recorded yet.") and error with retry states; if Load more fails, the loaded entries stay and an inline retry appears under them.
- **AC-14**: All three vehicle endpoints need `vehicle.manage` (403 without it), and the Vehicles section and its actions stay hidden without the key, as today.
- **AC-15**: Nothing else about tickets changes: a ticket can still be created on a Disabled truck, and its release still restores Disabled through `priorVehicleStatus`.
- **AC-16**: The section and both dialogs work at 375px and 1280px, use theme tokens only, and pass axe with no new findings.

## Decision

**Chosen option**: Option 1: Admin toggles Available and Disabled only, blocked while a ticket is open, and every status change (manual and automatic) is written to `VehicleChange`, which gains a `repairTicketId` link.

The ticket owns a truck's status from create to release; outside that window the Admin owns it, and the truck's history records both.

**Implementation skills**: `nestjs-best-practices` (`.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`.claude/skills/prisma-client-api/`) · `prisma-cli` (`.claude/skills/prisma-cli/`, for the migration) · `react-hook-form` (`.claude/skills/react-hook-form/`, for the reason dialog) · `shadcn` (`.claude/skills/shadcn/`, row menu and dialogs)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch** (one additive migration, no backfill):

| Entity | Change | Fields |
|---|---|---|
| `VehicleChange` (`vehicle_changes`) | add column | `repairTicketId` (`repair_ticket_id`) uuid, nullable, foreign key to `RepairTicket`, `onDelete: SetNull`; index `(repairTicketId)` |
| `RepairTicket` | back relation only | `vehicleChanges VehicleChange[]` |
| `VehicleChange` status rows | new row kind, no schema change | `field: 'status'`; `before` and `after` are the status as a JSON string; `note` = reason on manual rows, null on automatic ones; `repairTicketId` set only on automatic rows |

Unchanged: `Vehicle.status` (`AVAILABLE`, `UNDER_REPAIR`, `UNDER_MAINTENANCE`, `DISABLED`), `Vehicle.updatedAt` (stale check), `RepairTicket.priorVehicleStatus` (release rule). Existing `vehicleType` rows stay as they are. Migration name: `<timestamp>_vehicle_change_ticket`.

**State transitions** (truck status):

| From | To | Trigger | History row |
|---|---|---|---|
| any | `UNDER_REPAIR` | ticket create | yes, with ticket (AC-6) |
| `UNDER_REPAIR` | `DISABLED` if `priorVehicleStatus` is `DISABLED`, else `AVAILABLE` | move into Closed or Cancelled | yes, with ticket, when it changed (AC-7) |
| `AVAILABLE`, or `UNDER_REPAIR` with no open ticket | `DISABLED` | Admin toggle | yes, with reason (AC-1) |
| `DISABLED`, or `UNDER_REPAIR` with no open ticket | `AVAILABLE` | Admin toggle | yes, with reason (AC-2) |
| `UNDER_MAINTENANCE` | anything by toggle | refused, 409 `VEHICLE_STATUS_LOCKED` | none |
| any, with an open ticket | anything by toggle | refused, 409 `OPEN_TICKET_EXISTS` | none |

Unlocking a closed ticket does not touch the truck (as today).

**API surface** (under the `/vrms` gateway route, bearer JWT):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/vehicles` | GET | none | `[{ id, plateNumber, model, status, type, updatedAt, openTicket }]` | `vehicle.manage` | 403 |
| `/vrms/vehicles/:id/status` | POST | `status: 'AVAILABLE' \| 'DISABLED'`, `reason: string` (5 to 500 trimmed), `updatedAt: ISO string` | the row (same shape as the list) | `vehicle.manage` | 400 invalid body, 403, 404, 409 `STALE_VEHICLE`, 409 `OPEN_TICKET_EXISTS`, 409 `VEHICLE_STATUS_LOCKED` |
| `/vrms/vehicles/:id/changes` | GET | `cursor?` (opaque), `limit?` (1 to 50, default 20) | `{ items, nextCursor }` | `vehicle.manage` | 400 bad cursor, 403, 404 |
| `/vrms/vehicles/:id` | PATCH | unchanged (type) | row now includes `openTicket` | `vehicle.manage` | unchanged |

**Value sourcing**:

| Action | Value produced or displayed | Source |
|---|---|---|
| toggle | target status | input `status` |
| toggle | reason | input `reason`, trimmed, stored in `VehicleChange.note` |
| toggle | `before` | `vehicles.status` read under the row lock |
| toggle | open ticket block | `RepairTicket` with this `vehicleId` and `repairStatus` in `OPEN_STATUSES`, read after the lock |
| toggle | actor id, name, email | the JWT user (`sub`, `whoName(user)`, `email`), as the type edit does |
| toggle | stale check | input `updatedAt` against `vehicles.updated_at` |
| toggle | reason length | `@Transform` trim, then 5 to 500 (a blank reason fails) |
| create | `before` / `after` | `priorVehicleStatus` read under the lock / the constant `UNDER_REPAIR` (no row when equal) |
| create | actor | the creating user (`user` in `RepairsService.create`) |
| create | `repairTicketId` | the id of the ticket just created in the same transaction |
| release | `before` | `vehicles.status` read in the release step (already reads the row for the odometer; add `status`). Read without a lock on purpose: the toggle is blocked while this ticket is open, and the ticket row is already locked by the move, so nothing else can change the truck in between |
| release | `after` | `ticket.priorVehicleStatus` rule (spec 0016) |
| release | actor | the `actor` passed to `applyStatusMove` |
| list | `openTicket` | newest `RepairTicket` per vehicle with `repairStatus` in `OPEN_STATUSES` (`id`, `repairNumber`) |
| history | `ticket.repairNumber` | join `VehicleChange.repairTicketId` to `RepairTicket` |
| history | "Ticket removed" | `field = 'status'`, `note` null and `repairTicketId` null (never on `vehicleType` rows) |
| history | type names | `before.name` / `after.name` of `vehicleType` rows (null shows "Not set") |
| history | status words | `statusLabels.ts` in web-vrms |
| history | who | `VehicleChange.actorName`, "System" when null |
| links | ticket path | the web route `/repairs/:id` |
| history | local time | `createdAt` formatted in the browser with the existing date helpers |
| filter | active status chip | URL param `status` (`AVAILABLE`, `UNDER_REPAIR`, `DISABLED`; anything else means All) |

**Key invariants**:
- Only a ticket moves a truck into or out of `UNDER_REPAIR` while the ticket is open; the toggle never runs while one is open.
- Every write to `Vehicle.status` in app code writes exactly one `VehicleChange` status row in the same transaction, and none when the status did not change. All three writers (toggle, create, release) go through one helper, `vehicleStatusChange(tx, …)`. Seeds (`prisma/seeds/vehicles.seed.ts`, `repairs.seed.ts`) are exempt and write no history.
- The toggle and ticket create take the same `FOR UPDATE` lock on the vehicle row before reading status or open tickets.
- `VehicleChange` rows are never edited or deleted by the app.
- Toggling never touches `priorVehicleStatus` on any ticket.

**Security model**: `vehicle.manage` (Admin on by default, others off, grantable in Settings, Roles) guards all four vehicle endpoints, checked on the server by `@RequirePermission`. The reason is plain text, rendered as text (no HTML). Mechanics and Chief Mechanics without the key get 403 and never see the section. No PII beyond the actor's name and email, which `VehicleChange` already stores.

**Configuration required**: none (no new env vars or permission keys).

**Critical test scenarios**:
- Happy path: disable an Available truck with a reason; the row shows Disabled, History lists "Status: Available → Disabled" with the reason; make it available again. Verifies **AC-1**, **AC-2**, **AC-13**.
- Open ticket: create a ticket on a truck, then try to toggle it; the action is disabled with the ticket hint, and a direct API call gets 409 `OPEN_TICKET_EXISTS`. Verifies **AC-4**, **AC-10**.
- Race: a toggle and a ticket create on the same truck at once; exactly one wins and the other gets 409. Verifies **AC-4**.
- Full cycle on a Disabled truck: create a ticket (history: Disabled → Under repair, ticket link), close it (history: Under repair → Disabled, ticket link). Verifies **AC-6**, **AC-7**, **AC-15**.
- Stale: two Admin tabs; the second save gets the stale toast and the list reloads. Verifies **AC-5**, **AC-11**.
- Permission: a Mechanic calls all three endpoints and gets 403. Verifies **AC-14**.
- Filter: `?status=DISABLED` with a search term shows only matching disabled trucks; `?status=bogus` shows All. Verifies **AC-12**.

## Build plan

Tracer Bullet: the first milestone ships one end to end toggle, then the strand thickens.

1. Migration `vehicle_change_ticket`: `repairTicketId` on `VehicleChange` with `SetNull` and its index, plus the back relation on `RepairTicket`. Satisfies **AC-1**.
2. `SetVehicleStatusDto` (`status` in `AVAILABLE`/`DISABLED`, `reason` with `@Transform` trim then 5 to 500, `updatedAt`) and `VehiclesService.setStatus` with the checks in the AC-5a order, the status write and history row through a new `vehicleStatusChange(tx, …)` helper. `POST /vrms/vehicles/:id/status` behind `vehicle.manage`. Unit tests for each refusal and the order. Satisfies **AC-1** to **AC-5a**, **AC-14**.
3. web-vrms: `setVehicleStatus` in `vehiclesApi.ts`, the row menu (Disable truck, Make available), the reason dialog on the shared dialog with `react-hook-form`, success and error handling. Satisfies **AC-10** (actions), **AC-11**.
4. Automatic history: use the same `vehicleStatusChange(tx, …)` helper in create (after the ticket insert, no row for a stuck truck) and in the release in `applyStatusMove` (read `status` with the odometer, write only when changed). Tests for both, including the Disabled truck cycle and the stuck truck. Satisfies **AC-6**, **AC-7**, **AC-15**.
5. `openTicket` on the list and the PATCH row, and the disabled action with the ticket hint and the "Set by maintenance" hint; status filter chips in `?status=`. Satisfies **AC-8**, **AC-10**, **AC-12**.
6. `GET /vrms/vehicles/:id/changes` with keyset paging (reuse the audit timeline cursor pattern), and the History dialog with Load more and its states. Satisfies **AC-9**, **AC-13**.
7. Sweep: lint, typecheck, build and tests in both repos, 375px and 1280px with axe as Admin, tokens only. Satisfies **AC-16**.

Milestones for the scope: thin thread (tasks 1 to 3), automatic history (task 4), list hints and filter (task 5), history dialog (task 6), sweep (task 7).

## Consequences

**Positive**:
- Admins can take a truck out of service, as Jira WL-501 asks, without touching tickets.
- The truck history explains every status the truck ever had, with the ticket or the reason.
- No pending hidden state: what the row shows is what the truck is.
- One small additive migration; no backfill, nothing to roll back but a nullable column.

**Negative / tradeoffs**:
- Between a ticket's close and the Admin's Disable click, a truck meant to be retired shows Available and could be dispatched. Accepted; see Follow-up.
- Trucks repaired before this ships have no status history rows for those repairs. Only the ticket audit log covers them.
- The list query adds an open ticket lookup per page load. Fine at fleet size (one indexed query on `vehicleId` and status).
- Release now writes one more row inside the status transaction, so every close and cancel touches one more table.
- Seeded trucks and tickets have no status history, so a fresh dev database shows empty History dialogs until real changes happen.

**Neutral**:
- `VehicleChange.before` and `after` hold a string for status rows and an object for type rows; the history reader switches on `field`.
- `UNDER_MAINTENANCE` stays read only in VRMS until feature 56 decides who owns it.

## Follow-up

- [ ] If the gap between close and disable bites, add "Disable after repair": the toggle on an open ticket saves the choice to `priorVehicleStatus` and the row shows it (the option set aside here).
- [ ] Feature 56 (integration contract): agree with VMMS who writes `UNDER_MAINTENANCE` and whether a VMMS change writes `VehicleChange` rows through a VRMS API.
- [ ] Feature 45 (reports): availability reports can join `vehicle_changes` on `repair_ticket_id`.
- [ ] Jira WL-501 (VRMS-195): tell the PM the proposed rules are now decided here (Admin toggle with reason, blocked while a ticket is open), so they can update the ticket. Don't edit Jira.
- [ ] /sync: record the status history rule (every `Vehicle.status` write writes a `VehicleChange` row) in `welinc-backend-vrms/AGENTS.md`.
