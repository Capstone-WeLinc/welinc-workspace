# 0023. Per ticket checklist edits

**Date**: 2026-11-06
**Status**: In Progress

## Summary

Each issue on a ticket gets an Edit steps dialog where the people working it can add, reword, remove and reorder its checklist steps, without touching the knowledge base entry the steps came from. An issue with no known fix can get its own checklist the same way. Editing is open while the ticket is Assigned or In progress, behind a new permission key that is on for every role (a mechanic only on their own tickets). Every change writes its own audit row, steps added or reworded on the ticket carry a small tag so the verifier sees where the plan differs from the known fix, and the checklist has its own version counter (a lock), so a checklist save never makes anyone else's ticket edit go stale.

## Requirements

**User stories**:
- As a mechanic, I want to add a step the known fix forgot, or fix a step that is wrong for this truck, so that the checklist matches the work I really do.
- As a mechanic, I want to write my own checklist on an issue with no known fix, so that I can plan a job the knowledge base does not cover yet.
- As a Chief Mechanic, I want to adjust a ticket's steps before or during the work, so that the plan fits the truck.
- As a verifier, I want to see which steps were added or reworded on this ticket, so that I can tell where the work left the known fix.
- As an Admin, I want every checklist change in the audit log, and a switch to turn editing off for a role, so that the trail stays complete and the rights stay mine to set.

**Acceptance criteria**:
- **AC-1**: A new key `ticket.checklist.edit` (group Tickets, label "Edit ticket checklists", description "Add, reword, remove and reorder the steps on a ticket's issues. Without See every ticket, only on tickets assigned to you.") is in `catalog.ts`, on by default for Admin, Chief Mechanic and Mechanic, with no module. It grants the CASL action `editChecklist` on `RepairTicket`: on any ticket when the caller also holds `ticket.view_all`, otherwise only on tickets assigned to them (the same `mine` condition as `ticket.work`). `keys.ts` in web-vrms mirrors it, and the startup backfill adds it to the stored matrix with those defaults.
- **AC-2**: The ticket response gains `can.editChecklist` (`ability.can('editChecklist', target)`). The web shows checklist edit controls only when it is true and the ticket is Assigned or In progress, never from a role.
- **AC-3**: The save endpoint answers 400 "Steps can only be edited while the ticket is Assigned or In progress." in any other status, 403 without `editChecklist` on the ticket, and 404 when the issue is not on the ticket. The status and access checks run inside the transaction, after the issue lock is taken (AC-6), so a save cannot land after the ticket left Assigned or In progress. Both sides read the allowed statuses from one shared constant (`LINKABLE_STATUSES` in backend-vrms, mirrored in web-vrms), not a list of their own.
- **AC-4**: Each issue block shows an "Edit steps" button under its checklist when the issue has steps, and an "Add steps" button when it has none, linked or not. It opens a dialog (a bottom sheet below 640px) titled "Edit steps", with the issue description as its subtitle. Each row has a text field, Move up, Move down and Remove buttons (each with an `aria-label` naming the step number); "Add step" appends an empty row and focuses it. Cancel or close with changes asks to discard (`guardedClose`).
- **AC-5**: Limits, checked in the dialog and on the server: 0 to 20 steps; each step 3 to 300 characters after normalizing (AC-8). Empty new rows are dropped before checking. A field message shows under the row in `text-xs` `destructive`; the server answers 400 with `{ message, fieldErrors: [{ index, message }] }`, where `index` is the row's place in the sent list, so the dialog maps each message to its row. Add step is disabled at 20 rows. Saving 0 steps is allowed, also on a linked issue: the link stays, the block then shows "Add steps" (AC-4), and "What fixed it" and `followedKnownFix` work as today.
- **AC-6**: Save calls `PUT /vrms/repairs/:id/issues/:issueId/steps` with `checklistVersion` (the issue's `checklistVersion` when the dialog opened) and `steps`, the full list in order, each `{ id?, text }` (an `id` for a kept step, none for a new one). The first write in the transaction is a guarded `updateMany` on the issue `where { id: issueId, repairTicketId: id, checklistVersion }` that sets `checklistVersion` to that value plus 1; it takes the issue's row lock, and a count of 0 answers 409 with code `STALE_CHECKLIST` (its own constant beside `STALE_TICKET`) and the message "This checklist changed since you opened it. Reload to see the latest.", with no data. The ticket's `updatedAt` is never touched, so a checklist save never makes another ticket edit, status move or link change stale; and nothing but the checklist paths moves `checklistVersion`, so a status move, a "What fixed it" note or a dismissed suggestion never makes an open dialog stale.
- **AC-7**: An `id` that is not a step of this issue, or the same `id` twice, answers 400. A kept step that was removed by someone else cannot be saved, because every path that removes or replaces steps moves `checklistVersion` (AC-14, Key invariants).
- **AC-8**: The save is applied as a diff of the stored steps against the list. After the lock, the stored steps are read with `SELECT … FOR UPDATE` (`$queryRaw`), so a tick arriving during the save waits for it. A kept step keeps its stored `checkedAt` and `checkedByEmail` (a tick made while the dialog was open survives). Text is normalized before storing and comparing: trimmed, with each run of whitespace (spaces, tabs, newlines) turned into one space; a kept step is reworded only when its normalized text differs from the stored text. A reworded step loses its tick, and when its `origin` is `KNOWN_FIX` its `editedAt` is set to now (an `ADDED` step never gets `editedAt`). A new step is stored with `origin` `ADDED`. A step missing from the list is deleted. Positions are written 1 to n in list order.
- **AC-9**: Before saving, the dialog asks with `confirm()` when the save removes ticked steps or rewords ticked steps, counted from the latest ticket data: "Save these changes?" with "{r} ticked steps will be removed. {c} ticked steps will lose their tick." (only the parts that apply, singular for 1). Cancel keeps the dialog open and returns focus to Save.
- **AC-10**: Each changed step writes one audit row in the Checklist category, stamped 1 ms apart with `stampedAt` in the order removed, reworded, moved, added, with `lastActivityAt` set to the newest stamp. Every row carries `issueId`, and `stepId` except `STEP_ADDED`, which carries the new step's id. The `changes` lists are:
  - `STEP_REMOVED`: `position` (before), `text` (before), and when it was ticked `checkedAt` and `checkedBy` (before).
  - `STEP_EDITED`: `position` (after), `text` (before and after), and when a tick was cleared `checkedAt` and `checkedBy` (before, after empty).
  - `STEP_MOVED`: `text` (as saved), `position` (before and after).
  - `STEP_ADDED`: `position` and `text` (after).
  A step counts as moved only when it is outside the longest run of kept steps that stayed in their old order (so moving one step writes one row, not one per shifted neighbour). When two runs are equally long, the run that ends earliest in the new order is kept. A step both reworded and moved writes both rows. Removing a step and adding one with the same text is a remove and an add, never a move. Clearing a tick by rewording writes no `STEP_UNCHECKED` row: the `STEP_EDITED` row holds that tick. The audit timeline and the Audit log page show them as "added a step to REP", "removed a step from REP", "reworded a step on REP" and "moved a step on REP", with the step as a muted line ("3. Torque the caliper bolts", "Old → new", or "Step 5 → step 2").
- **AC-11**: A save that changes nothing writes no audit row, does not move `checklistVersion` or `lastActivityAt` (the transaction rolls back the version bump), and returns 200 with the ticket as it is.
- **AC-12**: The save returns the full ticket, the same shape as the link endpoint. Each issue gains `checklistVersion`; each step gains `origin` and `editedAt`. They come through `formatIssue`, so the detail and list responses both carry them.
- **AC-13**: In the checklist, an `ADDED` step shows an "Added" tag and a `KNOWN_FIX` step with `editedAt` shows an "Edited" tag (`text-xs`, muted, with a tooltip "Added on this ticket" or "Reworded on this ticket"). The dialog shows the same tags. Ticks, the "{x} of {y} steps done" line and the who and when on hover work the same for every step.
- **AC-14**: Relinking or unlinking a known fix asks first when the issue has ticked steps or steps added or reworded on this ticket: "Replace the checklist?" with "{t} ticked steps will be cleared. {a} steps added or reworded on this ticket will be lost." (only the parts that apply). Linking a known fix on an issue with its own checklist replaces it the same way. Every path that deletes or replaces an issue's steps takes the same issue lock: `linkKnowledge`, the spec 0019 issue edit that clears a fix from another category (`clearsFix`), and an approved knowledge suggestion that adds steps to linked issues (`knowledge-entry-editor.service.ts`) each raise `checklistVersion` with an atomic increment (`checklistVersion: { increment: 1 }`) as the first write on that issue in their transaction, before they delete or copy steps. The increment takes the issue's row lock, so a save and a relink run one after the other, never interleaved, and a dialog opened before a relink gets 409. The link and issue edit paths keep their current ticket lock and behaviour otherwise.
- **AC-15**: Ticking stays as it is (spec 0007, AC-28; spec 0021, AC-4 and AC-5): In progress only, on `ticket.work` or `ticket.administer`, and a tick never moves `checklistVersion`.
- **AC-16**: Checklist editing (Edit steps and Add steps) works while the knowledge module is switched off: the key belongs to no module, and an own checklist needs no knowledge entry. Linking, relinking and unlinking stay blocked while it is off (spec 0012).
- **AC-17**: The dialog keeps the issue snapshot it opened with; the 3 second poll updates the page behind it but never the form (`useEditSession`). A 409 closes the dialog, reloads the ticket and shows the stale message as a toast.
- **AC-18**: The dialog, the tags and the confirm prompt pass axe at 375px and 1280px, every control is reachable by keyboard, and focus moves to the row that took the place of a removed step (or to Add step when the list is empty).

## Decision

**Chosen option**: Option 1: A full list save per issue, guarded by the issue's own lock.

The checklist is edited in one dialog and saved as one ordered list per issue through a new `PUT`, diffed on the server inside one transaction, locked by a new `checklistVersion` counter on the issue, written to the audit log one row per changed step, and gated by a new `ticket.checklist.edit` key.

**Implementation skills**: `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`) · `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-cli/`) · `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `react-hook-form` (`.claude/skills/react-hook-form/`, the dialog's field array)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch** (target; one migration, `20261106120000_checklist_edits`):

| Table | Change |
|---|---|
| `repair_issue_steps` (`RepairIssueStep`) | `origin StepOrigin @default(KNOWN_FIX)` (not null; every existing row backfills as copied); `editedAt DateTime? @map("edited_at") @db.Timestamptz(6)` |
| enum `StepOrigin` | `KNOWN_FIX`, `ADDED` |
| `repair_issue_steps` | keeps `@@unique([repairIssueId, position])` |
| `repair_issues` (`RepairIssue`) | `checklistVersion Int @default(0) @map("checklist_version")` (not null), the checklist lock. Not `updatedAt`: six other paths move that (resolution notes and the `resolvedAt` reset in `apply-status-move.ts`, suggestion dismissal, approved suggestions, issue edits, links) |

Relationships are unchanged: a ticket has many issues, an issue has 0 to 20 steps, cascade on delete. Steps copied by create, link, the spec 0019 add issue path and an approved knowledge suggestion (`knowledge-entry-editor.service.ts`, which only adds steps to linked issues that have none) get `KNOWN_FIX` from the default, with no code change there.

**State transitions**: none new. Editing is allowed in `ASSIGNED` and `IN_PROGRESS`; ticking stays `IN_PROGRESS` only.

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/repairs/:id/issues/:issueId/steps` | PUT | `checklistVersion` int ≥ 0 (req), `steps: { id?: uuid, text: string }[]` (req, `ArrayMaxSize(20)`, `ValidateNested`) | the full ticket (`present`) | `@RequirePermission('ticket.checklist.edit')`, then `editChecklist` on the ticket in the service | 400 status, limits (`fieldErrors`), foreign or duplicate id; 403; 404 ticket or issue; 409 `STALE_CHECKLIST` |
| `GET /vrms/repairs/:id`, the repair list and every ticket response | | | issue `checklistVersion`; step `origin`, `editedAt`; `can.editChecklist` | unchanged | unchanged |
| `PATCH .../issues/:issueId/knowledge`, `PATCH .../issues/:issueId` (with `clearsFix`), approving a knowledge suggestion | | unchanged | unchanged | unchanged | unchanged, plus they raise `checklistVersion` (AC-14) |
| `/vrms/repairs/audit-logs` and `.../catalog` | GET | | four new types under `CHECKLIST` | unchanged | unchanged |

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Save | the lock value | `checklistVersion` input, compared with `repair_issues.checklist_version` |
| Save | which steps are kept, new, removed | `steps[].id` against the stored rows of `repairIssueId`, read `FOR UPDATE` after the lock |
| Save | a kept step's tick | stored `checkedAt` and `checkedByEmail`, read `FOR UPDATE`; cleared when reworded |
| Save | reworded or not | stored `text` against `normalizeStepText(steps[].text)` (AC-8) |
| Save | the 400 row index | the step's index in the sent `steps` array |
| Save | `origin` | stored for kept steps; `ADDED` for new ones |
| Save | `editedAt` | now, on a reworded `KNOWN_FIX` step; kept as stored otherwise |
| Save | positions | index in `steps` plus 1 |
| Save | moved steps | derived: kept ids in old order against new order, outside the longest increasing run, ties to the run ending earliest (`checklistDiff`) |
| Save | audit actor, role, time | the JWT through `auditData`, `stampedAt` from the save's now |
| Save | `lastActivityAt` | the newest `stampedAt` of the save's rows |
| Dialog | the lock to send | `issue.checklistVersion` from the snapshot the dialog opened with |
| Confirm prompt (AC-9) | ticked steps removed or reworded | the dialog's list against the latest ticket data (`issue.steps` from the poll) |
| Relink prompt (AC-14) | custom step count | `issue.steps` where `origin === 'ADDED'` or `editedAt != null` |
| Tags (AC-13) | Added or Edited | step `origin` and `editedAt` |
| Edit controls | shown or hidden | `can.editChecklist` and `ticket.status` |
| Audit sentences | ticket number, step text, positions | the audit row's `changes` and the ticket join already used by the timeline |

**Key invariants**:
- Steps of one issue always have positions 1 to n with no gaps. The save writes in this order inside one transaction: (1) the guarded `checklistVersion` bump (row lock); (2) the ticket status and access checks; (3) read the steps `FOR UPDATE`; (4) delete removed steps; (5) set every kept step to `position + 1000` (one `updateMany`); (6) update each kept step by id to its final position, with its text, tick and `editedAt` in that same write; (7) create the new steps at their positions; (8) the audit rows; (9) `tx.repairTicket.update({ lastActivityAt, updatedAt: ticket.updatedAt })`, passing the stored `updatedAt` through so `@updatedAt` leaves the ticket's lock alone (as `checkStep` does). With at most 20 steps, positions never pass 1020.
- Only the checklist paths move `checklistVersion`: the save, `linkKnowledge`, the `clearsFix` issue edit and an approved suggestion adding steps. Each raises it by exactly 1 inside its transaction: the save with its guarded `updateMany` (AC-6), the other three with an atomic increment before touching steps (AC-14).
- Only checklist saves write `origin` `ADDED` and `editedAt`. Create, link, add issue and approved suggestions copy entry steps with the defaults.
- A checklist save moves `checklistVersion` and `lastActivityAt`, never the ticket's `updatedAt`, never the issue's `updatedAt` meaningfully (the version bump touches it, nothing reads it as a lock) and never the `editedAt` stamp of spec 0019.
- A step tick moves no lock: it updates only the step row (spec 0021), and waits on the `FOR UPDATE` read while a save runs.
- `normalizeStepText` (trim, collapse whitespace runs to one space) is the one normalizer, used by the save, the limits and the web dialog (mirrored in `lib/checklist.ts`).
- Every new audit type has `CHECKLIST` in `AUDIT_CATEGORY`; `audit_logs` stays append only.
- The diff logic is one pure helper, `checklistDiff(stored, incoming)` in `modules/vrms/checklist-edits.ts`, returning the removed, reworded, moved and added steps; the service and its tests use it.

**Security model**:
- Route: `@RequirePermission('ticket.checklist.edit')`. Service: load the ticket with `ownerInclude` (the `mine` condition needs `assignments.mechanic.authUserId`), then `ability.can('editChecklist', subject('RepairTicket', ticket))`, else 403 "You can't edit the checklist on this ticket." It does not use `workAccess`: `ticket.work` and `ticket.administer` neither grant nor are needed for checklist edits.
- CASL rule: add `'editChecklist'` to the `Actions` union in `ability.factory.ts` and a `case 'ticket.checklist.edit'`: `can('editChecklist', 'RepairTicket')` when the caller also holds `ticket.view_all`, else `can('editChecklist', 'RepairTicket', mine)` (the same pattern as `addFiles`).
- Catalog tests that list every key (`catalog.spec.ts`, `permissions.service.spec.ts`, `route-permissions.spec.ts`) gain the new key and route; the existing startup backfill adds the key with its defaults to the stored matrix.
- Defaults: Admin, Chief Mechanic and Mechanic on. Admin can turn it off per role in the matrix. Mechanics never see costs here: steps carry no money.
- Step text is plain text, rendered as text, never as HTML.

**Configuration required**: none.

**Critical test scenarios**:
- Happy path: a mechanic on an Assigned ticket rewords step 2, moves step 4 to the top, adds a step and saves; the checklist shows the new order with Edited and Added tags, the timeline shows one row each for reworded, moved and added, the ticket's `updatedAt` is unchanged. Verifies **AC-4**, **AC-6**, **AC-8**, **AC-10**, **AC-13**.
- Ticked steps: on an In progress ticket, remove one ticked step and reword another; the prompt counts both; after save the reworded step is unticked and the removed row holds the old tick. Verifies **AC-8**, **AC-9**, **AC-10**.
- Concurrency: two people open the dialog; the first saves, the second gets 409 and a reload. A tick made while a dialog is open survives its save. A relink while a dialog is open makes its save 409. A "What fixed it" note, a move back to In progress or a dismissed suggestion does not. A save racing a move to For verification is refused with the status 400. Verifies **AC-3**, **AC-6**, **AC-8**, **AC-14**, **AC-17**.
- Moved set: moving step 5 of 5 to the top writes one `STEP_MOVED`; swapping two steps writes one (the tie rule); rewording and moving one step writes both rows. Verifies **AC-10**.
- Own checklist: on an unlinked issue, Add steps creates three `ADDED` steps; linking a known fix then asks and replaces them. Verifies **AC-4**, **AC-14**.
- Auth: a mechanic not assigned to the ticket gets 403; a Chief edits any ticket; a role with the key off sees no button and gets 403. Verifies **AC-1**, **AC-2**, **AC-3**.
- No change: saving the list as it is writes nothing and moves no lock. Verifies **AC-11**.
- Limits: 21 steps, a 2 character step, a foreign step id, and a Closed ticket each get 400. Verifies **AC-3**, **AC-5**, **AC-7**.

## Build plan

Tracer Bullet: the first slice runs one reword and one added step from the dialog through the lock, the diff, the audit rows and the tags; later slices thicken it with removal, reordering, own checklists and the relink prompt.

1. **Thin thread, reword and add**: the migration (`StepOrigin`, `origin`, `edited_at`, `checklist_version`); the `ticket.checklist.edit` key, its `Actions` entry, CASL rule and `can.editChecklist`; `keys.ts`; issue `checklistVersion` and step `origin`, `editedAt` in `formatIssue` and the web types; `normalizeStepText` and `checklistDiff` for kept, reworded and added steps; the `PUT` with its DTO and `fieldErrors`, the write order (lock, in-transaction status and access checks, `FOR UPDATE` read, writes, ticket pass-through) and 409 `STALE_CHECKLIST`; `STEP_EDITED` and `STEP_ADDED` builders, `changes` shapes and categories with their web sentences; the Edit steps dialog with text fields, Add step, limits and `useEditSession`; the Added and Edited tags. Satisfies **AC-1** to **AC-6**, **AC-8**, **AC-10** (edit and add), **AC-11** to **AC-13**, **AC-17**.
2. **Remove and reorder**: removal and the offset reorder in the transaction; the moved set (longest increasing run, the tie rule) in `checklistDiff`; `STEP_REMOVED` and `STEP_MOVED` with their `changes` and sentences; Move up, Move down and Remove in the dialog with focus rules; the confirm prompt for ticked steps with focus back on Save; foreign and duplicate id checks. Satisfies **AC-7** to **AC-10**, **AC-18** (focus).
3. **Own checklists and the shared lock**: Add steps on issues with no steps, linked or not, and the 0 step save; the `checklistVersion` bump in `linkKnowledge`, the `clearsFix` issue edit and approved suggestions; the relink and unlink prompt counting custom steps; check that the knowledge switch hides linking but not editing. Satisfies **AC-4**, **AC-5**, **AC-7**, **AC-14**, **AC-16**.
4. **Sweep**: `checklist-edits.spec.ts` (normalizer, the diff, the moved set and its tie rule), service tests for the lock, the in-transaction status check, access, tick merge, write order and audit order, version bumps on the three other paths and none on status moves or dismissals, the audit coverage test for the four types, the catalog and permission tests for the new key; a web test for the prompt counts and tags in a pure `lib/checklist.ts`; axe at 375px and 1280px; lint, typecheck, build. Satisfies **AC-15**, **AC-18**, and locks **AC-3**, **AC-6** to **AC-11**, **AC-14**.

## Consequences

**Positive**:
- The checklist becomes a real plan for this truck, not a fixed copy, while the knowledge entry stays the clean source.
- Issues without a known fix can still be worked from a checklist.
- The verifier sees at a glance where the work left the known fix.
- A checklist save never makes someone else's open edit or status move go stale, the same promise ticks keep, and nothing outside the checklist makes an open dialog stale.

**Negative / tradeoffs**:
- The relink and issue edit paths keep the ticket's lock and only bump `checklistVersion`, so a relink sent from a page loaded before a checklist save still goes through and replaces those edits. The prompt (AC-14) counts them only once the poll has brought them in, which is at most 3 seconds.
- More audit rows: a busy checklist session can add several rows per save, on top of step ticks (at most about 40 for one save, so its stamps can run past the next action's time by a few ms, which is harmless). The Audit log page redesign (feature 64) has to keep the Checklist category from burying the rest.
- A second lock on the issue is one more rule to remember: any new path that deletes or replaces steps must raise `checklistVersion`, or open dialogs can save over it.
- The `FOR UPDATE` read makes a tick wait while a save runs; a save is a few ms, so it is not felt.
- Rewording a ticked step clears the tick even for a typo fix, so a mechanic may have to tick it again.
- The key's scope depends on `ticket.view_all`, so an Admin who takes See every ticket away from the Chief also narrows the Chief's checklist editing to their own tickets.

**Neutral**:
- One migration with defaults (`origin` `KNOWN_FIX`, `checklist_version` 0), no backfill script, no data loss.
- Knowledge entry step limits (20 steps, 3 to 300 characters) now apply to ticket checklists too.
- No new endpoint for reading; the ticket response carries everything.

## Follow-up

- [ ] **Knowledge base feedback** (decided not now): on the entry page, show how often its steps were added to or reworded on tickets, and let a knowledge editor adopt them. Worth a scope row once real data exists.
- [ ] **Feature 64 (Audit log page redesign)**: include the four new types in the Checklist chip, and consider folding a save's rows into one group in the timeline.
- [ ] **Feature 32 (repair history timeline)**: render the four new types with the shared event renderer.
- [ ] **`/sync`**: record in `welinc-backend-vrms/AGENTS.md` that a checklist save locks on `repair_issues.checklist_version` and never the ticket's `updatedAt`, that every path deleting or replacing steps must raise it, and that `checklistDiff` and `normalizeStepText` are the one diff and normalizer; in `welinc-web-vrms/AGENTS.md` that `can.editChecklist` gates the Edit steps dialog.
- [ ] **For the PM (Jira)**: no ticket yet for per ticket checklist edits (feature 58, from spec 0007).
