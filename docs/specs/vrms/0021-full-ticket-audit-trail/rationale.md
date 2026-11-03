# 0021. Full ticket audit trail: rationale

Back to [index.md](index.md).

## Context

WL-219 asks that every ticket action land in the audit log in one consistent shape, with actor, role, time, ticket, event type, before and after, and note, and that no entry can be edited or deleted from the UI. The repair history timeline (feature 32, WL-205) and the reports module (feature 45) are planned to read from this log, so a gap in it becomes a gap in every view built on top.

Spec 0010 gave the log one row shape (one row per event, its field changes as a JSON list). Specs 0011 to 0020 added events as each feature shipped, so 15 types are written today. Four ticket actions still write nothing, or less than they should: the save of an unlocked closed ticket (which can change costs, remarks and the cancel reason after close), the relock that save performs, ticking or unticking a known fix checklist step, and creating a ticket with mechanics already picked (it writes `CREATED` but no assignment row). The first is the most serious: a closed ticket's cost can change with no trace.

Nothing in the database stops an audit row from being changed. The "cannot be edited or deleted" rule holds only because no route does it today; any future code path, a script or a mistaken migration could rewrite history. The app connects as the table owner (one database user, spec 0008 not yet built).

The log is also getting harder to read. With 15 types today and more coming (transfers, override), a flat list of type filters doesn't scale, and step ticks will add the most rows of any type. Readers need a coarser way to filter, owned by the server so the web and later the mobile app agree.

## Options considered

### Option 1: Fix in place, with a category catalog and a trigger guard

Keep the hand written per action rows, add the missing writes, group types into categories in the code catalog, and block `UPDATE`, `DELETE` and `TRUNCATE` with a Postgres trigger (grants later with hosting).

**Pros**:
- Each row stays a meaningful event ("unlocked", "ticked step 2"), which the timeline and reports need.
- Small, contained change on a pattern the team already uses in 15 places.
- The trigger works today with one database user, locally and on Azure.

**Cons**:
- Every new action must remember to write its row; only the coverage test catches a miss.
- The trigger alone doesn't stop someone with owner rights from dropping it.

### Option 2: Prisma client extension that logs every write

A Prisma query extension intercepts every `update` and `create` on ticket tables and writes a generic diff row automatically.

**Pros**:
- No action can forget to log.

**Cons**:
- Rows become field diffs, not events: "unlock", "send back" and "step ticked" lose their meaning, and the 15 existing semantic types would sit beside generic ones.
- The actor and reason are not available inside a query extension without request scoped plumbing.
- Hidden magic in the data layer, harder to test and reason about.

### Option 3: Database triggers that capture changes

Postgres triggers on the ticket tables write the audit rows themselves from the row before and after.

**Pros**:
- Impossible to bypass from the app.

**Cons**:
- The database doesn't know the actor or the reason; passing them through session settings is fragile.
- Business logic (which change is which event) moves into SQL that the team doesn't otherwise write.
- Same loss of event meaning as option 2.

## Rationale

The log's job is to tell a story a person can read and a report can count: who unlocked, who sent back, who ticked which step. Options 2 and 3 guarantee coverage but trade away exactly that meaning, and both need awkward plumbing to know the actor and the reason, which the token based `actorFields` already gives option 1 for free. The real gaps are only four actions, so fixing them in place and adding a coverage test closes WL-219 at a fraction of the risk.

Categories live in the code catalog, typed as a `Record` over every action, so the compiler refuses a new type without one, and the server serves them so no client keeps its own copy. Filters take categories and exact types as a union, which lets a page offer seven chips and still allow "only unticks".

The trigger is the cheapest guard that works with today's single database user and needs no hosting work. Restricted grants are the stronger guard (the app user could otherwise drop the trigger), but they need the separate owner and app roles that feature 26 already plans. Doing that split locally now would change the connection setup and the migration flow while hosting is on hold, so the grants are staged to feature 26.

Transfers get one type per outcome, so "declined transfers" is a plain type filter rather than a search inside the JSON changes. The override gets its own type, so the send back scans that look for For verification to In progress moves never mistake an override for a rejection.

## Evidence: ticket actions and their audit rows (2026-11-04)

| Action | Code | Row today | After this spec |
|---|---|---|---|
| Create | `repairs.service.ts` create | `CREATED` only, even when created with mechanics | `CREATED`, plus `MECHANIC_ASSIGNED` when created with mechanics |
| Status move | `apply-status-move.ts` | `STATUS_CHANGE` | unchanged |
| Unlock | `repairs.service.ts` | `UNLOCK` | unchanged |
| Save unlocked closed ticket | `repairs.service.ts` `saveUnlocked` | none | `COST_UPDATE`, `TICKET_EDITED`, `LOCKED` |
| Costs | `repairs.service.ts` | `COST_UPDATE` | unchanged |
| Garage | none, no action changes it after create | `GARAGE_CHANGE` rows exist only from the spec 0003 backfill | unchanged |
| Known fix link | `repairs.service.ts`, `knowledge-entry-editor.service.ts` | `KNOWLEDGE_LINK` | unchanged |
| Step tick | `repairs.service.ts` step update | none | `STEP_CHECKED`, `STEP_UNCHECKED` |
| Assign, unassign, reassign | `ticket-edits.service.ts`, `mechanic-work.service.ts` | `MECHANIC_ASSIGNED`, `MECHANIC_UNASSIGNED` | unchanged |
| Attachments | `attachments.service.ts` | `ATTACHMENT_ADDED`, `ATTACHMENT_REMOVED`, `ATTACHMENT_MOVED` | unchanged |
| Details and issues edit | `ticket-edits.service.ts` | `TICKET_EDITED`, `ISSUE_ADDED`, `ISSUE_EDITED`, `ISSUE_REMOVED` | unchanged |
| Attachment purge (30 days) | `attachment-purge.job.ts` | none | none, the removal was logged at soft delete |
| Knowledge suggestion dismiss | `knowledge-suggestions.service.ts` | none | none, it is a knowledge base action, not a ticket change |
