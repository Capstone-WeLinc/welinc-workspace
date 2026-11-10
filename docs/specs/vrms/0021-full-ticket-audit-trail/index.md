# 0021. Full ticket audit trail: close the gaps, filter by category, append only in the database

**Date**: 2026-11-04
**Status**: Accepted

## Summary

The audit log already records most ticket actions in one shape (spec 0010). This spec closes the last gaps: saves on an unlocked closed ticket, the relock after them, checklist step ticks, and the mechanics picked when a ticket is created. It groups every event type into seven categories, so readers can filter the busy types (ticks, photos) away from the important ones, and it fixes the event names that later features (transfers, status override) will use. A database trigger makes the log append only (rows can be added, never changed or deleted), and restricted database grants follow when hosting is built. The Audit log page itself is not redesigned here; that is a separate piece of work that will build on these filters.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As an Admin, I want every ticket action in the audit log, including changes made after an unlock, so that the repair history is complete and I can trust it (WL-219).
- As an Admin, I want to see who ticked or unticked each checklist step and when, so that I can tell whether a fix was really followed.
- As an Admin, I want to filter the log by category, event type and role, so that step ticks and photos don't bury status moves and cost changes.
- As the team, we want the database itself to refuse edits and deletes on audit rows, so that the trail holds even if a code path goes wrong.

**Acceptance criteria**:

*Gaps closed (backend-vrms)*

Two paths relock an unlocked closed ticket without a status move: the save through the status endpoint without a status change (`saveUnlocked`), and the costs endpoint (`updateCosts`). Below they are called the **relocking saves**. A status move also clears `isUnlocked`, but its `STATUS_CHANGE` row already records that, so it writes no `LOCKED` row.

- **AC-1**: A relocking save that changes any cost field writes one `COST_UPDATE` row listing only the changed fields (the existing `costEvent` builder). The "after" values are each value the save writes, else the stored value, with `totalCost` as the save computes it. When the ticket was unlocked, its note is the ticket's stored `unlockReason`. A save that changes no cost, or a caller whose costs part is ignored (no `ticket.costs.edit`), writes no `COST_UPDATE`. Rows are written in the same transaction as the save.
- **AC-2**: `saveUnlocked`, when it changes `remarks` or `cancellationReason`, writes one `TICKET_EDITED` row listing only those changed fields (before: the stored value or null; after: the trimmed sent value), with `unlockReason` as its note, in the same transaction. Blank or whitespace text counts as not sent (it never clears a value, as today).
- **AC-3**: Every successful relocking save of a ticket that was unlocked writes one `LOCKED` row (change `isUnlocked`: `true` to `false`, note null), even when nothing else changed. A costs save on a ticket that was not unlocked writes no `LOCKED`. A save rejected by the stale check (409) writes no rows at all.
- **AC-3b**: Rows written by one action are stamped in write order, 1 ms apart, starting at the action's `now` (create: `CREATED`, then `MECHANIC_ASSIGNED`; relocking save: `COST_UPDATE`, then `TICKET_EDITED`, then `LOCKED`), so the timeline order never depends on random ids. The ticket's `updatedAt` is `now`, and `lastActivityAt` is the time of the newest row written (unchanged when no row is written).
- **AC-4**: Ticking a checklist step writes one `STEP_CHECKED` row; unticking writes one `STEP_UNCHECKED` row. Each row carries the changes `checked` (`false` to `true`, or the reverse), `step` (after: the step text with its 1 based position, `"2. Check brake fluid"`), `issueId` and `stepId`, and the actor from the token. The ticket read, the In progress and access checks, the conditional step update, the row and a re-read of the step all run in one transaction. The tick sets the ticket's `lastActivityAt` to the row time and never touches `updatedAt` (spec 0014).
- **AC-5**: Ticking a step that is already ticked (or unticking one that is already unticked) changes nothing, writes no row, and returns the step as it is now, in the same shape as today. Two people ticking the same step at the same moment produce exactly one `STEP_CHECKED` row.
- **AC-5b**: Creating a ticket with mechanics (it starts Assigned) writes a `MECHANIC_ASSIGNED` row (one `mechanic` change per mechanic name, no status change) after its `CREATED` row (AC-3b), in the same nested create (`auditLogs: { create: [created, assigned] }`). A ticket created Open writes only `CREATED`.
- **AC-6**: Every ticket action that exists today writes its audit row. A coverage test lists each ticket changing service method (create, create with mechanics, status move including its relock, unlock, `saveUnlocked`, `updateCosts`, known fix link, assign and unassign, the unassign on deactivation or role removal (the actor is the Admin who ran the release, as spec 0011 AC-33 says), attachment add, remove and move, details edit, issue add, edit and remove, step tick) and asserts the action it writes. (No action changes a ticket's garage today; `GARAGE_CHANGE` exists only in rows backfilled by spec 0003.) Each row has the ticket id, the event type, the actor (user id, name, email, role, or no actor with role `SYSTEM` for a row no person wrote), the time, a changes list, and a note or null (WL-219 and VRMS-90).

*Categories and the event contract*

- **AC-7**: Each event type belongs to exactly one of seven categories, held in one code catalog that the TypeScript compiler forces to cover every type:

  | Category | Types |
  |---|---|
  | `STATUS` | `CREATED`, `STATUS_CHANGE`, `STATUS_OVERRIDE`, `UNLOCK`, `LOCKED` |
  | `ASSIGNMENT` | `MECHANIC_ASSIGNED`, `MECHANIC_UNASSIGNED`, `TRANSFER_REQUESTED`, `TRANSFER_APPROVED`, `TRANSFER_DECLINED`, `TRANSFER_CANCELLED` |
  | `EDITS` | `TICKET_EDITED`, `ISSUE_ADDED`, `ISSUE_EDITED`, `ISSUE_REMOVED`, `GARAGE_CHANGE` |
  | `COSTS` | `COST_UPDATE` |
  | `FILES` | `ATTACHMENT_ADDED`, `ATTACHMENT_REMOVED`, `ATTACHMENT_MOVED` |
  | `CHECKLIST` | `STEP_CHECKED`, `STEP_UNCHECKED` |
  | `KNOWLEDGE` | `KNOWLEDGE_LINK` |

  `STATUS_OVERRIDE` and the four `TRANSFER_*` types are reserved: they are in the catalog (so filters accept them) but nothing writes them until features 33 and 30 add their builders, following the shapes in *Event contract for later features*.
- **AC-8**: Every event in the `GET /vrms/repairs/audit-logs` response carries its `category`, or `null` for a stored action that is not in the catalog.

*Filtering (backend-vrms)*

- **AC-9**: `GET /vrms/repairs/audit-logs` accepts `categories` (a comma list of category keys) and `types` (a comma list of event types). A row matches when its type is in `types` or its category is in `categories` (a union, expanded on the server to one `action IN (...)` list). It also accepts `actorRole` (`ADMIN`, `CHIEF_MECHANIC`, `MECHANIC` or `SYSTEM`; `SYSTEM` matches rows with no user id and no email, the same "no actor" rule `toAuditEvent` uses). All existing filters (person, date range, repair number, ticket, cursor) and the hidden events (AC-12) combine with these by AND. Stored actions outside the catalog match no category, and AC-10 rejects an unknown type, so they show only in a list with no category or type filter.
- **AC-10**: Values are exact and case sensitive. An empty list or empty items are ignored, and duplicates are removed. An unknown category, type or role, more than 7 categories or more than 30 types returns 400 naming the problem. The old single `type` parameter still works: it is merged into `types` (sending both is fine) and validated the same way. Validation always uses the full catalog: a caller without `ticket.costs.view` who asks for `COSTS` or `COST_UPDATE` gets an empty result, not a 400.
- **AC-11**: `GET /vrms/repairs/audit-logs/catalog`, behind `audit.view`, returns the categories in the AC-7 order, each with its types, so a page can build its filters from the server instead of its own copy.
- **AC-12**: A caller without `ticket.costs.view` never sees `COST_UPDATE` rows or document events (receipts and other documents, as spec 0017 already hides), in the list or in the catalog (the `COSTS` category is left out for them). A caller with it sees everything.

*Append only (database)*

- **AC-13**: After the migration, any `UPDATE`, `DELETE` or `TRUNCATE` on `audit_logs` fails with the error `audit_logs is append only`, from any connection, while `INSERT` and `SELECT` keep working.
- **AC-14**: No API route or service changes or deletes an audit row. A guard test fails the build if any non test file under `src/` (excluding `*.spec.ts`) calls `auditLog.update`, `updateMany`, `delete`, `deleteMany` or `upsert`. It is a best effort grep (it can't see raw SQL); the trigger is the real protection. The seed still resets a dev database: it runs `ALTER TABLE audit_logs DISABLE TRIGGER USER` before its cleanup and `ENABLE TRIGGER USER` in a `finally`, as the table owner.

*Web (web-vrms, minimal, no redesign)*

- **AC-15**: The current Audit log page and the ticket's Activity section show the three new types with their own icon and sentence instead of the raw fallback: `LOCKED` "{name} locked {REP} again", `STEP_CHECKED` "{name} ticked a step on {REP}" and `STEP_UNCHECKED` "{name} unticked a step on {REP}", each followed by the step text as a muted line. `ticketEditLines` gains `remarks` ("Remarks: old → new") and `cancellationReason` ("Cancel reason: old → new"), each clamped to 2 lines with the full text in its tooltip, so the new `TICKET_EDITED` rows don't render empty. The `AuditEvent` type gains `category: string | null`. Nothing else on either page changes.

## Decision

**Chosen option**: Option 1: Fix in place, with a category catalog and a trigger guard

Keep the hand written, per action audit rows of spec 0010, add the missing writes and a category catalog in `audit-events.ts`, filter by category on the server, and block changes to `audit_logs` with a Postgres trigger now and restricted grants when hosting is built.

**Implementation skills**: `nestjs-best-practices` (`.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`.claude/skills/prisma-client-api/`) · `prisma-cli` (`.claude/skills/prisma-cli/`, for the raw SQL migration and to confirm `migrate dev` leaves the trigger alone)

## Feature design

**Data model sketch**: no new tables or columns. `AuditLog` stays as spec 0010 left it (`repairTicketId`, `actorUserId`, `actorName`, `actorEmail`, `actorRole`, `action`, `changes` JSON list, `note`, `createdAt`). One migration adds only:

```sql
CREATE FUNCTION audit_logs_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'audit_logs is append only';
END $$;

CREATE TRIGGER audit_logs_no_change
  BEFORE UPDATE OR DELETE ON "audit_logs"
  FOR EACH ROW EXECUTE FUNCTION audit_logs_append_only();

CREATE TRIGGER audit_logs_no_truncate
  BEFORE TRUNCATE ON "audit_logs"
  FOR EACH STATEMENT EXECUTE FUNCTION audit_logs_append_only();
```

The `repair_ticket_id` foreign key keeps `ON DELETE RESTRICT`, so a ticket with audit rows can't be deleted either. Ticket ids never change, so its `ON UPDATE CASCADE` never reaches the trigger.

**Code catalog** (`welinc-backend-vrms/src/modules/vrms/audit-events.ts`):
- `AUDIT_ACTIONS` gains `LOCKED`, `STEP_CHECKED`, `STEP_UNCHECKED`, `STATUS_OVERRIDE`, `TRANSFER_REQUESTED`, `TRANSFER_APPROVED`, `TRANSFER_DECLINED`, `TRANSFER_CANCELLED`.
- `AUDIT_CATEGORIES` (ordered list of the seven keys) and `AUDIT_CATEGORY: Record<AuditAction, AuditCategory>`. A `Record` over the union makes a new type without a category a compile error.
- New builders: `lockedEvent()`, `stepTickEvent(checked, step: { id, position, text }, issueId)`, `closedTicketTextEvent(before, after, note)` (the `TICKET_EDITED` row for `remarks` and `cancellationReason`, listing only changed fields).
- `hideDocumentEvents` becomes `hiddenAuditEvents(canViewCosts)`: beside the existing jsonb clause for documents, it adds `action <> 'COST_UPDATE'` when the caller lacks `ticket.costs.view` (the two clauses AND together). `findAuditEvents` is the only reader that shows rows to a person, and it uses it; the internal scans (`lastRejectionFrom`, `lastReturnAt`) don't need it. Update the old name where `AGENTS.md` cites it (through `/sync`).
- A small `stampedAt(now, index)` helper returns `now + index ms`, for the AC-3b write order.

**Event contract for later features** (the reserved types; each feature adds its builder in `audit-events.ts`, writes the row in the same transaction as its change, and uses `auditData`):

| Type | Changes | Note | Written by |
|---|---|---|---|
| `STATUS_OVERRIDE` | `repairStatus` before and after (same field as `STATUS_CHANGE`) | the required reason | feature 33 |
| `TRANSFER_REQUESTED` | `mechanic` before (requester), `transferRequestId` | the request reason | feature 30 |
| `TRANSFER_APPROVED` | `mechanic` before and after, `transferRequestId` | optional | feature 30 |
| `TRANSFER_DECLINED` | `transferRequestId` | the decline reason | feature 30 |
| `TRANSFER_CANCELLED` | `transferRequestId` | optional | feature 30, only if requesters may withdraw |

Rules for any type added later: put it in `AUDIT_ACTIONS` and `AUDIT_CATEGORY`, keep extras (ids, kinds) as extra entries in `changes` the way `issueId` and `attachmentId` already ride, and give it a sentence in web-vrms `auditEvents.ts`. Hold for parts, outsourcing and outsourced approval are status moves (`ON_HOLD`, `OUTSOURCED`, `PENDING_APPROVAL`) and ride `STATUS_CHANGE` with their reason as the note. If feature 31 or 37 needs an approval that is not a status move, it adds a type under these rules.

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/repairs/audit-logs` | GET | existing (`limit`, `cursor`, `actorId`, `from`, `to`, `repairNumber`, `ticketId`), plus `categories`, `types`, `actorRole`; `type` kept as an alias | `data[]` (each with `category`), `nextCursor` | `audit.view` | 400 unknown category, type or role |
| `/vrms/repairs/audit-logs/catalog` | GET | none | `[{ category, types[] }]` in AC-7 order, `COSTS` left out without `ticket.costs.view` | `audit.view` | 403 |
| status endpoint save of an unlocked closed ticket (`saveUnlocked`, existing path) | PATCH | unchanged | unchanged | unchanged | 409 stale |
| costs endpoint (`updateCosts`, existing path) | PATCH | unchanged | unchanged | unchanged | 409 stale |
| `/vrms/repairs/:id/issues/:issueId/steps/:stepId` | PATCH | `checked` (unchanged) | the step (unchanged shape) | unchanged (`workAccess`) | 400 not In progress, 404 |

Both GET routes are declared before `:id`, like the existing audit routes. List params are parsed from comma lists in the DTO (`@Transform` split, trim, drop empties), at most 7 categories and 30 types.

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Relocking save, `COST_UPDATE` | before costs | the ticket row loaded before the save (guarded by the stale check) |
| Relocking save, `COST_UPDATE` | after costs | each value the save writes (`costData` in `saveUnlocked`, the computed amounts in `updateCosts`), else the stored value |
| Relocking save, rows | note (unlock reason) | the ticket's stored `unlockReason`, when `isUnlocked` was true |
| `saveUnlocked`, `TICKET_EDITED` | `remarks`, `cancellationReason` before and after | stored value before; trimmed `dto` value after, only when not blank and different |
| Relocking save, `LOCKED` | whether to write it | the loaded ticket's `isUnlocked` |
| Relocking save, all rows | actor | `actorFields(user)`; `saveUnlocked` gains the `user` argument |
| Every multi row action | each row's time | `stampedAt(now, index)` in write order (AC-3b) |
| Every action that writes rows | `lastActivityAt` | the newest row's time |
| Create with mechanics | mechanic names | the mechanics the create already loads for the assignments (`mechanicIds`) |
| Step tick | step text and position | the `RepairIssueStep` row (`text`, `position`) |
| Step tick | `issueId`, `stepId` | route params, already checked to belong to the ticket |
| Step tick | whether anything changed | `count` of a conditional `updateMany` (`checkedAt: null` when ticking, `not: null` when unticking) |
| Step tick | the returned step | a re-read of the step inside the transaction, on both paths |
| List | `category` per event | `AUDIT_CATEGORY[row.action]`; an unknown stored action reads as `null` |
| List | which rows a caller may see | `hiddenAuditEvents(canViewCosts(ability))` |
| Catalog | categories and types | `AUDIT_CATEGORIES` and `AUDIT_CATEGORY` |
| `actorRole=SYSTEM` filter | rows with no actor | `actorUserId IS NULL AND actorEmail IS NULL` |

**Key invariants**:
- An audit row is written in the same transaction as the change it records, or not at all.
- `audit_logs` is append only, enforced by the database (trigger now, grants with feature 26).
- Every event type has exactly one category (compile time check).
- Actor fields come from the verified token, never from a request body (spec 0010).
- Cost and document events never reach a caller without `ticket.costs.view`.
- A step tick or save that changes nothing writes no change row.
- Rows from one action never share a timestamp; `lastActivityAt` equals the ticket's newest audit row time.

**Security model**: reading the log stays behind `audit.view` (Admin on by default, spec 0011). Nobody can change or delete a row, through the API (no route) or the database (trigger). Writers are the existing service methods only. Grants that limit the app's database user to `SELECT` and `INSERT` on `audit_logs` are added by feature 26 (see Follow-up). Rows are kept forever; there is no purge.

**Configuration required**: none.

**Critical test scenarios**:
- Happy path: unlock a closed ticket, change parts cost and remarks, save. Three rows appear (`COST_UPDATE`, `TICKET_EDITED`, `LOCKED` newest), all with the unlock reason where stated. Verifies **AC-1**, **AC-2**, **AC-3**.
- Failure case: two concurrent ticks of one step write exactly one row; a stale closed save writes none. Verifies **AC-5**, **AC-3**.
- Database: a raw `UPDATE audit_logs SET note = 'x'` and a `DELETE` both fail with the append only error; an insert works. Verifies **AC-13**.
- Filtering: `categories=CHECKLIST&types=COST_UPDATE` returns only step ticks and cost rows; `actorRole=SYSTEM` returns only rows with no actor; `types=NOPE` gives 400. Verifies **AC-9**, **AC-10**.
- Auth/permission: a caller with `audit.view` but without `ticket.costs.view` gets no `COST_UPDATE` rows and no `COSTS` in the catalog. Verifies **AC-12**.

## Build plan

Tracer Bullet: the first slice runs one new event from the service through the response to the screen; later slices thicken it.

1. **Thin thread, relocking saves**: add the new types and `AUDIT_CATEGORY` to the catalog, `lockedEvent`, `closedTicketTextEvent` and `stampedAt`, pass `user` into `saveUnlocked`, write `COST_UPDATE`, `TICKET_EDITED` and `LOCKED` (with `unlockReason`) in `saveUnlocked` and `COST_UPDATE` note plus `LOCKED` in `updateCosts`, stamped in write order with `lastActivityAt`, add `category` to `toAuditEvent`, and the `LOCKED` sentence plus the remarks and cancel reason lines in web-vrms. Also add the `MECHANIC_ASSIGNED` row to the nested create when the ticket starts with mechanics. Satisfies **AC-1**, **AC-2**, **AC-3**, **AC-3b**, **AC-5b**, **AC-7**, **AC-8**, **AC-15**.
2. **Step ticks**: move the ticket read and the In progress and access checks into a transaction with the conditional `updateMany`, write `STEP_CHECKED` or `STEP_UNCHECKED` from `stepTickEvent` and set `lastActivityAt`, re-read and return the step on both paths, and add both sentences in web-vrms. Satisfies **AC-4**, **AC-5**, **AC-15**.
3. **Filters and catalog**: `categories`, `types`, `actorRole` and the `type` alias in `AuditEventsQueryDto` with 400s, the union filter, `GET audit-logs/catalog`, and `hiddenAuditEvents` hiding `COST_UPDATE`. Satisfies **AC-9**, **AC-10**, **AC-11**, **AC-12**.
4. **Append only**: the trigger migration (raw SQL), the seed cleanup that switches the trigger off and on in a `try`/`finally`, the guard test on `src/`, and a check that `prisma migrate dev` reports no drift and leaves the triggers. Satisfies **AC-13**, **AC-14**.
5. **Coverage and sweep**: the coverage test over every ticket changing method, lint, build and tests in both repos, and a live check of one row per new type on the Audit log page and the Activity section. Satisfies **AC-6**, **AC-15**.

## Consequences

**Positive**:
- The trail covers every ticket action that exists today, so the repair history (feature 32) and reports can rely on it.
- The log is tamper resistant at the database level, not just by convention.
- A later page redo filters with a handful of category chips built from the server catalog, instead of a hard coded list of 20 or more types.
- Features 30 and 33 get fixed names and shapes, so their audit work is a builder and a row.

**Negative / tradeoffs**:
- Step ticks add many rows (roughly one per step per ticket, more with unticks). The log grows faster, and unfiltered views get busier until the page redo uses categories.
- The trigger makes any future data fix on `audit_logs` harder: a migration that truly must touch it has to switch the trigger off inside the migration and say why.
- Until feature 26 adds the grants, the app's database user is still the table owner and could drop the trigger. The trigger stops mistakes, not a determined attacker with database access.
- Stamping rows 1 ms apart is a convention every multi row writer must follow (`stampedAt`). A different request landing inside that millisecond could interleave; that is accepted.
- Step ticks now move `lastActivityAt`, so a ticket being worked through its checklist no longer looks idle to stale ticket alerts (feature 43). That is intended, but it changes what "activity" means there.
- `STATUS_OVERRIDE` is a separate type, so anything that reads status history (send back scans, `statusChangedAt`, analytics) must include it on purpose when feature 33 ships.

**Neutral**:
- One raw SQL migration with no schema change; Prisma does not model triggers.
- The seed needs owner rights to switch the trigger off, which the dev database user has.
- No backfill: nothing is deployed, so existing ticks are seed and test data. The trail is complete from the migration on.
- Checked on 2026-11-04: the existing migrations only read `audit_logs`, and the Jest tests mock Prisma, so the trigger breaks nothing today. A future test against a real database that cleans `audit_logs` must use the same disable step as the seed.

## Migration plan

**Strategy**: no data migration; one additive migration (the triggers).
**Phases**:
1. Ship the code changes and the trigger migration together in backend-vrms.
2. Feature 26 later adds the restricted grants per environment.
**Rollback**: a follow up migration that drops both triggers and the function; the code changes revert with their commits.
**Risks**: a later migration or script that updates or deletes `audit_logs` fails loudly. That is intended; it must switch the trigger off inside itself and say why. `prisma migrate reset` drops the whole schema, so it is not affected, and Prisma does not introspect triggers, so `migrate dev` reports no drift.

## Follow-up

- [x] **Audit log page redesign** (you asked for this, kept out of this spec): enrolled as feature 64 on 2026-11-04, needing a decision on the design. It should build its filters from `GET audit-logs/catalog` and the category filter, and settle the noise from step ticks and photos.
- [ ] **Feature 26 (hosting)**: when milestone 3 creates the database roles, run migrations as the owner role and connect the app as a role with `GRANT SELECT, INSERT ON audit_logs TO <app_role>` and no `UPDATE`, `DELETE` or `TRUNCATE`, so the app user cannot drop the trigger.
- [ ] **Feature 33 (status override)**: write `STATUS_OVERRIDE` per the contract, set `statusChangedAt` itself, and make status history readers (`lastRejectionFrom`, `lastReturnAt`, analytics) decide on purpose whether to include it.
- [ ] **Feature 30 (transfer requests)**: write the `TRANSFER_*` types per the contract; decide whether requesters may withdraw (`TRANSFER_CANCELLED`).
- [ ] **Feature 32 (repair history timeline)**: filter by category, and hide cost events from mechanics through `hiddenAuditEvents` (already true for anyone without `ticket.costs.view`).
- [ ] **Feature 62 (costs after close)**: its cost changes on a closed ticket write `COST_UPDATE` without an unlock, so its note is its own reason, not an unlock reason.
- [x] **`/sync`**: record in `welinc-backend-vrms/AGENTS.md` that `audit_logs` is append only (trigger), that every type needs a category, and that a migration touching the table must switch the trigger off inside itself. Checked 2026-11-04: already recorded in `welinc-backend-vrms/AGENTS.md` (the `audit_logs` append only line), and `attachments/AGENTS.md` already names `hiddenAuditEvents`.
- [ ] **For the PM (Jira)**: this spec covers VRMS-89 (hook every action) and VRMS-90 (verify every event is logged) under WL-219. The Audit log page redesign has no Jira ticket yet.
