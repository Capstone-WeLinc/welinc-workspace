# 0010. Data model v2: one clean baseline with the new ticket statuses

**Date**: 2026-10-29
**Updated**: 2026-10-31 (the interim *State transitions* section is replaced by spec 0014's transition table)
**Status**: Accepted

Decision history (context, options, rationale): [rationale.md](rationale.md).

## Summary

This spec rebuilds the welinc-backend-vrms database schema once, before Slice 1, so later features stop running into breaking changes. The 18 old migrations are squashed into one clean baseline (one migration that builds the whole schema from empty). The baseline brings the WL-200 ticket statuses (with Completed renamed to Closed), a real assignment table, one audit shape for every log, and the slice 1 ticket fields (priority, reporter, verifier), and it drops everything nothing uses. Every other table slices 1 to 6 need (files, notifications, transfers, holds, outsourced shops, lookup lists) is designed here, and each one is created later by its own feature following this design. Everyone resets their local database and reseeds once; no real data exists anywhere, so nothing is lost.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As a developer, I want one clean baseline migration so that the schema history is readable and a fresh database builds in one step.
- As the team, we want the WL-200 ticket statuses in the schema now so that every Slice 1 feature builds on the same names.
- As an Admin, I want each ticket to record its priority, who reported it and who verified it so that reports and the verification queue have real data.
- As a developer, I want every log in VRMS to share one shape (one row per event, its changes as a list) so that the history timeline and later logs are built once.
- As a later feature, I want my tables already designed so that I add them without reshaping anything that exists.

**Acceptance criteria**:
- **AC-1**: `welinc-backend-vrms/prisma/migrations/` holds exactly one migration folder (the baseline) plus `migration_lock.toml`. On an empty database, `npx prisma migrate reset` builds the full schema, enables `pg_trgm`, and inserts the issue categories (Brakes to Transmission, plus General) exactly as the old knowledge base migration did. `npx prisma migrate diff` from the migrations folder to `schema.prisma` reports no difference.
- **AC-2**: `RepairStatus` has exactly these values: `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `ON_HOLD`, `FOR_VERIFICATION`, `OUTSOURCED`, `PENDING_APPROVAL`, `CLOSED`, `CANCELLED`. The ticket values `PENDING` and `COMPLETED` no longer appear in welinc-backend-vrms or welinc-web-vrms source (the account status `PENDING` on the Users page is a different thing and stays).
- **AC-3**: Creating a ticket saves it as `ASSIGNED` (the create DTO already requires at least one mechanic), and saves the `priority` the form sends. `reportedByUserId` and `reportedByName` come from the caller.
- **AC-4**: Today's forward moves keep working on the new names: `ASSIGNED` to `IN_PROGRESS`, then `FOR_VERIFICATION`, then `CLOSED`, plus cancel to `CANCELLED`. As today, mechanics and chief mechanics may only move a ticket to `IN_PROGRESS` or `FOR_VERIFICATION`, so closing and cancelling stay Admin only. The move to `CLOSED` sets `verifiedByUserId`, `verifiedByName` and `verifiedAt` from whoever closes it (Admin today). Both `CLOSED` and `CANCELLED` set `closedAt` (as `completedAt` is set today); the verifier is set only on `CLOSED`. The invalid move error message uses the new status labels. `OPEN`, `ON_HOLD`, `OUTSOURCED` and `PENDING_APPROVAL` exist, but nothing creates them or moves a ticket into them yet (feature 16 owns the transition rules). The status DTO no longer takes `failedVerificationReason`, and there is no reject move until feature 16.
- **AC-4a**: Every status set in code uses one definition: **open** is every status except `CLOSED` and `CANCELLED`, and **finished** is `CLOSED` and `CANCELLED`. The repair list default, the overdue filter, the history default and the mechanic roster's "not on an active ticket" check all read these two sets.
- **AC-5**: Mechanics are linked to tickets only through `TicketAssignment` (ticket, mechanic, `assignedAt`, `assignedByUserId`, `assignedByName`), unique per ticket and mechanic. The ticket API still answers with a `mechanics` list, so callers see the same shape as before.
- **AC-6**: Each audit event is one `AuditLog` row with `actorUserId`, `actorName`, `actorEmail`, `actorRole`, `action`, `changes` (a JSON list of `{ field, before, after }`), an optional `note`, and `createdAt`. Each action fills `changes` and `note` exactly as the *Audit events* table says. A cost update that changes parts, labor and total writes one row with three changes, not three rows. `SHOP_CHANGE` is renamed `GARAGE_CHANGE` everywhere (seed, timeline filter, web labels).
- **AC-7**: Spec 0003's audit timeline endpoint and the history page read the new shape and still show every field's before and after, newest first, with the same keyset paging (`createdAt` then `id`, both descending).
- **AC-8**: An audit row can't be removed along with its ticket: deleting a ticket that has audit rows fails at the database (foreign key `ON DELETE RESTRICT`).
- **AC-9**: `KnowledgeEntryChange` uses the same shape (one row per event, `changes` as JSON, actor fields, `note`), every knowledge write produces it, and the knowledge base's change history dialog shows each change.
- **AC-10**: `lastActivityAt` on a ticket is set whenever a person's action writes an audit row, using the same `now` value as that row's `createdAt`, in the same write. Nothing else moves it: not scheduled or sync jobs, not checklist ticks, and not an unlocked save that writes no audit row.
- **AC-11**: These are gone from the schema, the baseline, the seed and the code: the models `Booking`, `MaintenanceSchedule`, `ChecklistTemplate`, `ChecklistItem` and `ShopChangeLog`; the enums `AccountType`, `MaintenanceStatus`, `MaintenanceTriggerType` and `MaintenanceIntervalType`; the ticket columns `isArchived`, `durationDays`, `durationHours` and `failedVerificationReason`; and `prisma/seeds/vmms.seed.ts`.
- **AC-12**: `Mechanic` holds in house mechanics only: `isOutsourced` and `shopName` are gone and `authUserId` is required. The create DTO accepts mechanics by id only and no longer takes a ticket `shopName`. The repair form's mechanic picker lists in house mechanics only, with no outsourced group.
- **AC-13**: `targetDueDate` is renamed `dueAt`, with a new optional `dueAtSource` (`PRIORITY`, `ISSUE_TYPE` or `MANUAL`). Nothing writes a due date today, so both stay empty until feature 42 fills them. The overdue filter, the due date sort and every screen that shows a due date read `dueAt`.
- **AC-14**: `VehicleStatus` gains `DISABLED`, and web-vrms has a label and badge for it.
- **AC-15**: `npm run seed` builds a believable history in the new shape: tickets in every status reachable today (`ASSIGNED`, `IN_PROGRESS`, `FOR_VERIFICATION`, `CLOSED`, `CANCELLED`), every `CLOSED` ticket has a verifier, every ticket has a priority and reporter, the audit rows use the JSON shape, and each ticket's `lastActivityAt` equals its newest audit event.
- **AC-16**: In web-vrms, these all work on the new names, with no new screens: the repair list, detail, form, dashboard (its Waiting count is still `FOR_VERIFICATION`), the history page (the filter offers Closed and Cancelled), the audit timeline and the knowledge history dialog.
- **AC-17**: lint, build and test pass in welinc-backend-vrms; lint, typecheck and build pass in welinc-web-vrms. Tests that used the old names or shapes are updated, not deleted. With the whole Docker stack up after the reset, the Python analytics container may return errors, but it doesn't crash loop or stop the other services.

## Decision

**Chosen option**: Option 2: squash into one baseline with the breaking changes, and design the later tables now.

Replace the 18 migrations with one baseline that carries the v2 shape of every existing table, plus the slice 1 columns, and record the target design of every new table so each feature creates it unchanged.

**Implementation skills**: `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-cli/`) · `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`) · `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`)

## Feature design

### What the baseline holds (built by this spec)

The baseline is today's schema with the changes below. Every table and column not named here stays as it is.

**Enums**

| Enum | Values |
|---|---|
| `RepairStatus` | `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `ON_HOLD`, `FOR_VERIFICATION`, `OUTSOURCED`, `PENDING_APPROVAL`, `CLOSED`, `CANCELLED` (default `OPEN`) |
| `VehicleStatus` | `AVAILABLE`, `UNDER_REPAIR`, `UNDER_MAINTENANCE`, `DISABLED` |
| `DueAtSource` (new) | `PRIORITY`, `ISSUE_TYPE`, `MANUAL` |
| Dropped | `AccountType`, `MaintenanceStatus`, `MaintenanceTriggerType`, `MaintenanceIntervalType` |

**`RepairTicket`** (`repair_tickets`)

| Field | Type | Null | Note |
|---|---|---|---|
| `repairStatus` | `RepairStatus` | no | default `OPEN` |
| `priority` | `RepairPriority` | no | default `MEDIUM`; saved from the create input |
| `reportedByUserId` | uuid | yes | welinc-auth user id, no foreign key; empty only on seed rows written without a user |
| `reportedByName` | varchar(100) | yes | name when reported |
| `verifiedByUserId` | uuid | yes | set on the move to `CLOSED` |
| `verifiedByName` | varchar(100) | yes | |
| `verifiedAt` | timestamptz | yes | |
| `dueAt` | timestamptz | yes | renamed from `targetDueDate` |
| `dueAtSource` | `DueAtSource` | yes | set together with `dueAt` |
| `lastActivityAt` | timestamptz | no | default `now()`; see AC-10 |
| `closedAt` | timestamptz | yes | renamed from `completedAt` |
| removed | | | `isArchived`, `durationDays`, `durationHours`, `failedVerificationReason`, and the hidden `mechanics` many to many |

New indexes: `(repairStatus, lastActivityAt)` for the stuck and stale checks, `(dueAt)` for overdue lists. The existing `(repairStatus, createdAt)` and `(vehicleId)` stay.

**`TicketAssignment`** (`ticket_assignments`, new)

| Field | Type | Null | Note |
|---|---|---|---|
| `id` | uuid | no | |
| `repairTicketId` | uuid | no | foreign key, `ON DELETE CASCADE` |
| `mechanicId` | uuid | no | foreign key to `Mechanic` |
| `assignedAt` | timestamptz | no | default `now()` |
| `assignedByUserId` | uuid | yes | welinc-auth id; empty on seed rows |
| `assignedByName` | varchar(100) | yes | |

Unique `(repairTicketId, mechanicId)`. Index `(mechanicId)`, so a mechanic's open ticket count is one indexed join. Unassigning deletes the row; the audit event keeps the history. All assigned mechanics are equal (no lead).

**`Mechanic`**: `authUserId` becomes required (still unique, no foreign key). `isOutsourced` and `shopName` are removed. The relation to tickets goes through `TicketAssignment`.

**`AuditLog`** (`audit_logs`)

| Field | Type | Null | Note |
|---|---|---|---|
| `id` | uuid | no | |
| `repairTicketId` | uuid | no | foreign key, `ON DELETE RESTRICT` |
| `actorUserId` | uuid | yes | renamed from `userId`; empty only for system events |
| `actorName` | varchar(100) | yes | |
| `actorEmail` | varchar(255) | yes | renamed from `email` |
| `actorRole` | varchar(30) | yes | the caller's VRMS role (`ADMIN`, `CHIEF_MECHANIC`, `MECHANIC`), or `SYSTEM` |
| `action` | varchar(50) | no | event name from `audit-events.ts` |
| `changes` | jsonb | no | default `[]`; a list of `{ field, before, after }`, strings or null |
| `note` | text | yes | reason or comment (reject, unlock, cancel, override) |
| `createdAt` | timestamptz(3) | no | millisecond precision, kept for keyset paging |

Removed: `fieldName`, `previousValue`, `newValue`. Indexes: `(repairTicketId, createdAt)`, `(createdAt desc, id desc)`, `(actorEmail)`, `(action)`.

**`KnowledgeEntryChange`** (`knowledge_entry_changes`): same columns as `AuditLog`, except it has `entryId` and `categoryId` (both optional, as today) instead of `repairTicketId`. Indexes `(entryId, createdAt)` and `(categoryId, createdAt)`.

**`Vehicle`** and **`Driver`**: lose their `bookings` relation. No other change.

**Dropped models**: `Booking`, `MaintenanceSchedule`, `ChecklistTemplate`, `ChecklistItem`, `ShopChangeLog`.

### Audit events and their changes

Values in `changes` are raw values stored as strings (`"IN_PROGRESS"`, `"1200.00"`, `"true"`, an id or a name), or `null`. The web app formats them for display; nothing stores currency signs or labels. Field names match the API field names.

| Action | `changes` | `note` |
|---|---|---|
| `CREATED` | `[]` | none |
| `STATUS_CHANGE` | `repairStatus` (before, after) | the cancel reason on a move to `CANCELLED` (also kept in `cancellationReason`), else the optional remarks |
| `COST_UPDATE` | every one of `partsCost`, `laborCost`, `totalCost`, `isLumpSum` that changed | none |
| `UNLOCK` | `isUnlocked` (`"false"` to `"true"`) | the unlock reason (also kept in `unlockReason`) |
| `GARAGE_CHANGE` (was `SHOP_CHANGE`) | `garage` (the garage names before and after) | none |
| `KNOWLEDGE_LINK` | `knowledgeEntry` (entry names before and after), plus `issueId` (after only) so the timeline knows which issue | none |

`KnowledgeEntryChange` follows the same rule with its existing actions (`ENTRY_CREATED`, `ENTRY_UPDATED`, `ENTRY_STATUS`, `CATEGORY_CREATED`, `CATEGORY_UPDATED`, `CATEGORY_STATUS`): one row per save, with every changed field in `changes`. New actions in later features add a row to this table in their own spec.

### Later tables (designed here, created by their own feature)

Each feature adds its table in its own migration, exactly as below, unless its own spec finds a real reason to change it (then that spec says so). "Who" fields follow the same rule everywhere: a welinc-auth user id with no foreign key, plus a name copied at the time.

**`VehicleStatusChange`** (feature 25): `id`, `vehicleId` (foreign key), `fromStatus` and `toStatus` (`VehicleStatus`), `reason` (text, required for a manual change), `repairTicketId` (optional foreign key), `changedByUserId` and `changedByName` (empty for automatic changes), `createdAt`. Index `(vehicleId, createdAt)`.

**`Attachment`** (feature 20): `id`, `repairTicketId` (foreign key), `outsourcedJobId` (optional foreign key, for receipts), `kind` (new enum `AttachmentKind`: `VEHICLE_PHOTO`, `PROOF`, `RECEIPT`), `storageKey` (unique, the bytes live where feature 20 decides), `thumbnailKey` (optional), `fileName` (varchar 255), `mimeType` (varchar 100), `sizeBytes` (int), `uploadedByUserId`, `uploadedByName`, `createdAt`, `deletedAt` (optional, soft delete so audit can still point at it). Index `(repairTicketId, kind)`.

**`Notification`** (feature 28): `id`, `recipientUserId` (welinc-auth id, no foreign key), `type` (varchar 50, names in code like audit events), `repairTicketId` (optional foreign key), `message` (varchar 300), `readAt` (optional), `createdAt`. Index `(recipientUserId, readAt, createdAt desc)`. Email and push delivery records are feature 28's call.

**`LookupValue`** (feature 40): `id`, `list` (new enum `LookupList`: `TRANSFER_REASON`, `HOLD_REASON`, `CANCEL_REASON`, `OUTSOURCE_JUSTIFICATION`, `LOCATION`), `label` (varchar 100), `labelKey` (trim and lowercase), `isActive`, `sortOrder`, `createdAt`, `updatedAt`. Unique `(list, labelKey)`. Code that stores a lookup id checks it belongs to the expected list.

**`Part`** (feature 40): `id`, `name` (varchar 100), `nameKey` (unique), `defaultUnitCost` (decimal 10,2, optional), `isActive`, `sortOrder`, `createdAt`, `updatedAt`. `RepairPart` gains an optional `partId` foreign key; its typed `description` stays for parts not in the list.

**`TransferRequest`** (feature 30): `id`, `repairTicketId`, `mechanicId` (the requester's own spot), `reasonId` (`LookupValue`, list `TRANSFER_REASON`), `note` (optional), `suggestedMechanicId` (optional), `status` (new enum `TransferStatus`: `PENDING`, `APPROVED`, `REJECTED`), `decidedByUserId`, `decidedByName`, `decisionReason`, `replacementMechanicId` (all optional until decided), `createdAt`, `decidedAt`. A partial unique index (written as raw SQL in that migration) on `(repairTicketId, mechanicId) WHERE status = 'PENDING'`: one pending request per mechanic per ticket.

**`TicketHold`** and **`TicketHoldPart`** (feature 31): hold has `id`, `repairTicketId`, `reasonId` (`LookupValue`, list `HOLD_REASON`), `note`, `status` (new enum `HoldStatus`: `PENDING_VERIFICATION`, `APPROVED`, `REJECTED`), `requestedByUserId`, `requestedByName`, `verifiedByUserId`, `verifiedByName`, `verifiedAt`, `verifierComment`, `startedAt`, `endedAt` (optional). Partial unique index on `(repairTicketId) WHERE ended_at IS NULL`: one open hold per ticket. Hold part has `id`, `holdId` (foreign key, cascade), `partId` (optional `Part`), `freeText` (optional varchar 100), with at least one of the two set.

**`OutsourcedShop`** (feature 36): `id`, `name` (varchar 100), `nameKey` (unique), `contactPerson`, `phone`, `email`, `address`, `specialization` (all optional), `isActive`, `createdAt`, `updatedAt`.

**`OutsourcedJob`** (features 37 to 39): `id`, `repairTicketId`, `shopId` (foreign key), `justificationId` (`LookupValue`, list `OUTSOURCE_JUSTIFICATION`, optional when no in house option was free), `justificationNote`, `sentAt`, `expectedAt`, `quotedCost` (decimal 10,2), `finalCost` (decimal 10,2, required at close), `itemizedRepairs` (text), `approvalStatus` (new enum: `NOT_REQUIRED`, `PENDING`, `APPROVED`, `REJECTED`), `approvedByUserId`, `approvedByName`, `approvedAt`, `approvalReason`, `sentByUserId`, `sentByName`, `closedAt`, `createdAt`. Index `(repairTicketId)`. A ticket can have several jobs over time.

**`IssueCategory.defaultFixHours`** (feature 42): decimal 5,2, optional. Hours per priority live in the Settings hub (feature 52).

### State transitions

Replaced by spec 0014 ([ticket status lifecycle](../0014-ticket-status-lifecycle/index.md)), which holds the one transition table: every move, its trigger, who may make it and what it needs. This spec only fixes the nine status names. The interim list that stood here (forward moves only, Admin for the last two, nothing creates `OPEN`) no longer applies.

### API surface

No new endpoint. Existing endpoints change only in the values and fields they carry:

| Endpoint | Change |
|---|---|
| `POST /vrms/repairs` | saves `priority`; mechanics by id only; `shopName` removed from the body; answers with status `ASSIGNED` |
| `PATCH` status update | accepts and returns the new status names; the move to `CLOSED` records the verifier; `failedVerificationReason` removed from the body |
| ticket reads (list, detail, history) | `repairStatus` uses new names; `completedAt` becomes `closedAt`; `targetDueDate` becomes `dueAt`; new `priority`, `reportedByName`, `verifiedByName`, `verifiedAt`, `dueAtSource`; `mechanics` list kept, built from `TicketAssignment` |
| history query | status filter takes `CLOSED` and `CANCELLED` |
| audit timeline (spec 0003) | each item is one event with `changes`, `actorRole` and `note` instead of one field per item |
| knowledge change history | same event shape as the audit timeline |

### Value sourcing

| Action | Value | Source |
|---|---|---|
| create ticket | `repairStatus` | `ASSIGNED`, since the DTO requires at least one mechanic |
| create ticket | `priority` | `priority` in the create body (already validated today, now saved) |
| create ticket | `reportedByUserId`, `reportedByName` | `req.user.sub`, and the caller's name (rule below) |
| create ticket | `TicketAssignment.assignedBy*` | the same caller |
| create ticket | `TicketAssignment.mechanicId` | the mechanic ids in the body; `Mechanic` rows exist only through the roster sync (spec 0009), so each has an `authUserId` |
| move to `CLOSED` | `verifiedByUserId`, `verifiedByName`, `verifiedAt` | the caller (Admin today), and the server clock |
| move to `CLOSED` or `CANCELLED` | `closedAt` | the server clock |
| any audit write | `actorUserId`, `actorName`, `actorEmail` | `req.user`, as spec 0009 does today |
| every "who" name | `*ByName`, `actorName` | the caller's name from spec 0009's account check; if it is empty, the JWT email; cut to 100 characters |
| any audit write | `actorRole` | the caller's VRMS role from the JWT; `SYSTEM` for jobs |
| any audit write | `changes`, `note` | the *Audit events* table, built by the event builders in `audit-events.ts` |
| person's audit write | `lastActivityAt`, audit `createdAt` | one `new Date()` taken once in the service and written to both |
| ticket reads | `dueAt`, `dueAtSource` | stay empty; feature 42 is the first writer |
| seed | all of the above | `prisma/seeds/repairs.seed.ts`, using the seeded welinc-auth user ids |

### Key invariants

- Only one migration folder exists after this spec. Every later schema change adds a new timestamped folder on top; nobody edits the baseline.
- A ticket's mechanics live only in `TicketAssignment`; never store a mechanic name on the ticket.
- Audit rows are never updated or deleted by code, and the database refuses deleting a ticket that has them. Tickets are never deleted (no endpoint does it); cancelling is how a ticket ends.
- `COST_UPDATE` events, and any cost value inside `changes`, never reach a reader who isn't Admin. The audit endpoints are Admin only today; feature 32 (timeline for mechanics) must filter them out.
- Open and finished statuses come from one definition in code (AC-4a), never a list repeated per query.
- `changes` always holds a list, empty for events like `CREATED`. Field names inside it match the API field names.
- `lastActivityAt` only moves forward and only on a person's action.
- `dueAt` and `dueAtSource` are set and cleared together.
- Who fields never have a foreign key, because users live in welinc-auth.

### Security model

No permission changes. Every route keeps its current guards and roles. `actorRole` is copied from the verified JWT, never from the request body. Costs stay hidden from mechanics as today.

### Configuration required

None. No new environment variables. `pg_trgm` still ships with `postgres:16-alpine`.

### Critical test scenarios

- Fresh database: `migrate reset` then `npm run seed` succeeds, and a diff shows no drift, verifies **AC-1**, **AC-15**
- Create, start, send for verification, close: statuses are `ASSIGNED`, `IN_PROGRESS`, `FOR_VERIFICATION`, `CLOSED`; the closed ticket has a verifier and `closedAt`, verifies **AC-3**, **AC-4**
- A cost update on three fields writes one audit row with three changes, and the timeline shows all three, verifies **AC-6**, **AC-7**
- Deleting a ticket with audit rows fails, verifies **AC-8**
- A person's status change moves `lastActivityAt`; reading the ticket doesn't, verifies **AC-10**
- Creating a ticket with an outsourced mechanic in the body is rejected with 400, verifies **AC-12**
- A mechanic or chief mechanic trying to close or cancel gets the invalid move error with the new labels; cancelling sets `closedAt` but no verifier, verifies **AC-4**
- An `ON_HOLD` ticket (inserted directly in a test) appears in the open list and the overdue filter, not in history, verifies **AC-4a**
- A stale status update still gets the 409 from optimistic locking, verifies **AC-4**

## Build plan

Tracer Bullet, adjusted for a squash: the baseline is one piece and Prisma regenerates its client from it, so the new schema lands whole first, then one end to end ticket flow is made to work on it, then the logs, then the rest.

**Before you start**
0. Check every open branch in welinc-backend-vrms for migration folders not yet on `development` (the knowledge base and user management branches are the likely ones). Merge or rebase them first, because after the squash their migrations no longer apply. Satisfies **AC-1**

**Milestone 1: baseline and one ticket flow end to end**
1. Write the v2 `schema.prisma` (every change in *What the baseline holds*), satisfies **AC-2**, **AC-5**, **AC-6**, **AC-8**, **AC-9**, **AC-11**, **AC-12**, **AC-13**, **AC-14**
2. Delete the 18 migration folders and generate the baseline from empty (see the `prisma-cli` skill for `migrate diff`); put `CREATE EXTENSION IF NOT EXISTS pg_trgm;` first and the issue category insert last, copied from the old knowledge base migration, satisfies **AC-1**
3. `repairs.service.ts`, the DTOs and `ticket-knowledge.ts`: new status names; one `OPEN_STATUSES` and `FINISHED_STATUSES` definition used by every query; `MECHANIC_ALLOWED_TRANSITIONS` becomes `IN_PROGRESS` and `FOR_VERIFICATION`; the invalid move message on the new labels; create as `ASSIGNED`; save priority and reporter; write `TicketAssignment`; set the verifier on close and `closedAt` on close or cancel; drop `failedVerificationReason`, the outsourced branch and `shopName`; read `dueAt`. The shared ticket include becomes `assignments: { include: { mechanic: true } }`, mechanic filters become `assignments: { some: { mechanicId } }`, assignment checks read `ticket.assignments`, and the formatter keeps answering with a `mechanics` list, satisfies **AC-3**, **AC-4**, **AC-4a**, **AC-5**, **AC-12**, **AC-13**
4. `audit-events.ts`: builders return one event with `changes` and `note` per the *Audit events* table, values as raw strings; every writer sets `actorRole`, takes one `now` for both `createdAt` and `lastActivityAt`, and writes both in one transaction; rename `SHOP_CHANGE` to `GARAGE_CHANGE`, satisfies **AC-6**, **AC-10**
5. `mechanic-roster.service.ts` and `config.service.ts`: in house only, satisfies **AC-12**
6. Seed: delete `vmms.seed.ts`, update `mechanics.seed.ts`, `catalog.ts` and `repairs.seed.ts` for the new shape (a first pass is enough to create and close tickets), satisfies **AC-11**, **AC-15**
7. web-vrms thin thread: `types/index.ts`, `statusLabels.ts`, `StatusBadge.tsx`, `nextAction.ts`, `repairApi.ts`, and the repair list, detail and form (`MechanicPicker.tsx` in house only) on the new names, satisfies **AC-12**, **AC-16**

**Milestone 2: one audit shape everywhere**
8. Spec 0003's audit timeline endpoint and history queries read `changes`, keeping keyset paging, satisfies **AC-7**
9. `knowledge-changes.ts`, `knowledge-entry-editor.service.ts` and `knowledge-categories.service.ts` write the event shape, satisfies **AC-9**
10. web-vrms: the audit timeline (`features/audit-logs/`, including `GARAGE_CHANGE` in `auditEvents.ts` and `AuditEventItem.tsx`) and `ChangeHistoryDialog.tsx` render one event with its list of changes, formatting the raw values, satisfies **AC-6**, **AC-7**, **AC-9**

**Milestone 3: the rest of the app on v2**
11. web-vrms: dashboard (`attention.ts`, `MechanicDashboard.tsx`, `RepairProgressChart.tsx`), history (`HistoryFilters.tsx`, `historyFilters.ts`, `HistoryPage.tsx`), `due.ts` and `format.ts` for `dueAt`, the `DISABLED` vehicle label, and the dev UI samples. Leave the account `PENDING` in `user-management/` alone, satisfies **AC-2**, **AC-13**, **AC-14**, **AC-16**
12. Finish the seed: every reachable status, verifiers on closed tickets, JSON audit rows, `lastActivityAt` from the newest event, satisfies **AC-15**
13. Search both repos for `completedAt`, `targetDueDate`, `isOutsourced`, `shopName`, `fieldName`, `previousValue`, `SHOP_CHANGE`, `RepairStatus.PENDING`, `RepairStatus.COMPLETED`, and `'PENDING'` or `'COMPLETED'` near ticket status code, and clear every ticket related hit. The account `PENDING` in `user-management/` stays, satisfies **AC-2**, **AC-11**

**Milestone 4: close out**
14. Update the Jest tests that use the old names or shapes (`repairs.service.spec.ts`, `repairs.knowledge.spec.ts`, `audit-events.spec.ts`, `mechanic-roster.service.spec.ts`, the knowledge specs) and add the critical scenarios above, satisfies **AC-17**
15. Run lint, build and test in welinc-backend-vrms, and lint, typecheck and build in welinc-web-vrms; restart the backend container before any live check; bring the whole Docker stack up and confirm the Python analytics container doesn't crash loop, satisfies **AC-17**

## Migration plan

**Strategy**: big bang on local databases only (nothing is deployed and no real data exists).
**Phases**:
1. Land the squash and the code together in welinc-backend-vrms and welinc-web-vrms (one PR each into `development`).
2. Everyone pulls both repos, runs `npx prisma migrate reset` in welinc-backend-vrms (it asks first), then `npm run seed`.
**Rollback**: revert both PRs, then reset and reseed again.
**Risks**: a branch that still carries an old migration breaks after the squash (step 0 handles it); the Python service breaks on the renames (accepted, see Consequences).

## Consequences

**Positive**:
- One readable migration instead of 18, with no trace of the old users tables.
- Slice 1 features (16 to 25) start on final status names, a real assignment table, and the priority, reporter and verifier fields.
- Every later table is already designed, so slices 2 to 6 add tables instead of reshaping old ones.
- One audit shape for tickets and the knowledge base, which later logs (shops, lookups, settings) copy.
- Audit history can no longer vanish with a ticket.

**Negative / tradeoffs**:
- Everyone has to reset and reseed once, and open branches with migrations must be merged or rebased first.
- The repair form has no outsourced option until features 36 and 37 bring shops back.
- The audit timeline (spec 0003) and the knowledge history (spec 0007) get rewritten to read the JSON `changes`, and filtering by a single field now means a JSON query.
- `welinc-backend-vrms-analytics-ai` reads this database directly and breaks on the renames and dropped tables: status breakdown, aging and the AI vehicle history. The analytics page already falls back to sample data and the AI panel shows its error, so nothing else breaks. Feature 3 replaces it.
- Dropping the copied BMS and VMMS models now means that if feature 56 decides VRMS should hold them, they come back in a new migration.

**Neutral**:
- Which status moves are allowed (backward moves, override, holds, outsourcing) stays with feature 16.
- The account and corporation fields in the create body (`accountType`, `corporation`) are still accepted and not stored; feature 18 decides them.

## Follow-up

- [ ] Feature 16 (ticket status lifecycle) builds its transition table on these nine names.
- [ ] Each later feature (20, 25, 28, 30, 31, 36 to 40, 42) creates its table from *Later tables*, and its spec states any change it needs.
- [ ] Feature 3: record that the Python service breaks on this baseline, and that the pgvector image switch for `vrms-db` happens there.
- [ ] Feature 56: record that `Booking`, `MaintenanceSchedule`, `ChecklistTemplate` and `ChecklistItem` were dropped from VRMS on 2026-10-29, and bring them back only if the meeting decides VRMS owns them.
- [ ] New scope feature, Slice 1 after features 18 and 53: mechanic workload on the Users page (an Occupied badge when a mechanic has an `IN_PROGRESS` ticket, open counts by status, an Occupied or Free filter, a Tickets section with unassign or reassign in the user dialog, counts in the picker). The Chief Mechanic sees it read only, under the name **Mechanics**, through a feature 5 permission.
- [ ] Feature 18: decide whether `accountType` and `corporation` are stored or removed from the form.
- [ ] Features 30 and 31: Prisma may not model partial unique indexes, so a later generated migration could treat them as drift and drop them. Check the `prisma-cli` skill first; if Prisma 7 can't express them, write them as raw SQL with a `///` note on the model, and check every later migration doesn't drop them.
- [ ] Feature 25: the vehicle status change on close or cancel runs outside the status transaction today (`repairs.service.ts`, the vehicle update before the audit write), so a failed write can leave the truck marked Available. Fix it when feature 25 rewrites that code.
- [ ] Feature 32: filter `COST_UPDATE` events out of the mechanic timeline.
- [ ] Feature 16 and feature 5: decide whether the Chief Mechanic can close (verify) a ticket; until then `verifiedBy*` is the Admin who closes.
