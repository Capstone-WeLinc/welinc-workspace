# 0018. Before and after photos: proof of completion from one photo strip

**Date**: 2026-11-02
**Status**: Accepted

## Summary

A ticket has one photo strip. Whether work has started decides each photo's label: photos added before are **Before** (how the truck arrived), photos added after are **After** (the proof the fix is done). Admin switches can require a Before photo to start work and an After photo to send for verification or to close. Verifiers see a quiet flag when an After photo was taken before work started, and photos added after a ticket was returned show a mark. No new table is needed: the two photo kinds from spec 0017 are reused, plus two nullable columns (when the phone took the photo, and when work first started on the ticket).

## Requirements

**User stories**:
- As a mechanic, I want one "Add photo" control that files my photo correctly by itself, so I never pick a type on my phone.
- As a Chief Mechanic, I want to see the After photos first, next to the Before photos, so I can verify the fix without asking.
- As an Admin, I want to decide which steps need photos, so the rules fit how our garages work.
- As a Chief Mechanic, I want to notice an old gallery photo passed off as proof, so evidence stays honest.

**Acceptance criteria**:
- **AC-1**: A photo uploaded before work has started on the ticket (`workStartedAt` is null) is stored as `VEHICLE_PHOTO` (shown as **Before**); after (`workStartedAt` set) it is stored as `PROOF` (shown as **After**). The server reads `workStartedAt` under the ticket row lock; the client cannot choose the kind.
- **AC-2**: After photos accept JPEG, PNG and HEIC only. A PDF sent as a photo gets 415 with the existing type message. Receipts and other documents are unchanged.
- **AC-3**: Before photos count against `uploads.max_vehicle_photos` (relabelled "Before photos per ticket", default 5). After photos count against the new `uploads.max_after_photos` ("After photos per ticket", default 10, range 1 to 30). An upload or a move into a full group gets 409 with that group's limit message. Lowering a limit below a ticket's live count keeps the photos and only blocks new ones.
- **AC-4**: While `tickets.require_before_photo_to_start` is on (default on), Start work (M3) needs at least one live Before photo. The server answers 400 `BEFORE_PHOTO_REQUIRED`. The ticket's `moves` mark M3 as blocked, and the web shows the button disabled with the text "Add a before photo first".
- **AC-5**: While `tickets.require_after_photo_to_send` is on (default on), Send for verification (M4) needs at least one live After photo: 400 `AFTER_PHOTO_REQUIRED`, blocked in `moves`, disabled with "Add an after photo first".
- **AC-6**: While `tickets.require_after_photo_to_close` is on (default off), Verify and close (M5) needs at least one live After photo: 400 `AFTER_PHOTO_REQUIRED`, blocked in `moves`, disabled with "Add an after photo before closing".
- **AC-7**: Each photo rule is checked inside `applyStatusMove`, after its conditional update takes the ticket row lock, counting live photos (not soft deleted); a failure throws and rolls the move back. It runs only for M3, M4 and M5, never for other callers of `applyStatusMove` (the mechanic release path). The existing checks (`resolutions` on M4, `COSTS_REQUIRED` on M5) run first and keep their errors. A rule is checked only at its move: removing or moving a photo later never changes the status and is never blocked by these rules.
- **AC-8**: The rules apply to every ticket from release, including tickets already `ASSIGNED` or `IN_PROGRESS`. The outsourced moves (M9 to M13) and Cancel (M14) carry no photo rule.
- **AC-9**: `PATCH /vrms/repairs/:id/attachments/:attachmentId` with `{ kind }` moves a photo between Before and After. Allowed for the uploader while they hold `ticket.files.add`, or for anyone holding `ticket.files.remove_any`. It writes an `ATTACHMENT_MOVED` audit event with the before and after label in the same transaction. Moving to the label it already has answers 200 with no audit row. Only photo kinds can be moved, and only to a photo kind (400 otherwise). A finished ticket answers 409 `TICKET_FINISHED`.
- **AC-10**: While `tickets.protect_before_photos` is on (default on) and work has started (`workStartedAt` set), removing a Before photo or moving it to After needs `ticket.files.remove_any`, else 403 `BEFORE_PHOTO_PROTECTED` ("Before photos are protected once work starts. Ask a Chief Mechanic or Admin."). Before work starts, or with the switch off, today's spec 0017 removal rules apply. Moving a photo *into* Before is never protected.
- **AC-11**: The attachment list returns `canRemove` and `canMove` per row that follow AC-9 and AC-10, so the web never offers an action the server refuses. The server checks both again under the row lock against a fresh read of the ticket and the attachment.
- **AC-12**: Before shrinking a photo, the browser reads its recorded time (`DateTimeOriginal`) from the original file with exifr and sends it as `takenAt`. The server stores it in `Attachment.takenAt` when it parses and lies between 2000-01-01 and 5 minutes after now; otherwise it stores null. A bad or missing `takenAt` is dropped silently and never fails an upload.
- **AC-13**: An After photo whose `takenAt` is more than 5 minutes earlier than the ticket's `workStartedAt` shows a small "Taken before work started" flag on its thumbnail and in the viewer, in any status. Only callers whose permissions grant the verify right (the permission behind M5, checked without the per ticket "not your own ticket" rule) see it: for everyone else the API omits `takenAt` and `takenBeforeWork`. A photo with no `takenAt`, or a ticket with no `workStartedAt`, shows no flag. The flag never blocks anything.
- **AC-14**: After photos uploaded strictly after the ticket's latest Return to mechanic (M6) show a chip "Added after return" on the thumbnail and the line "Added after the ticket was returned to the mechanic" in the viewer, for everyone who can see the ticket. The mark stays after the ticket is resent.
- **AC-15**: Move M6's label becomes "Return to mechanic", the spec 0014 banner reads "Returned by {name}, {relative time}", and every user facing "Send back" or "Sent back" in web-vrms uses "Return" wording. The move id, the API and the audit data are unchanged.
- **AC-16**: The ticket shows one photo strip with one add control (Take photo, Choose photos) and no type or issue picker. The strip has two labelled groups, Before and After, each with its count against its limit. Once work has started the After group comes first, before then the Before group. Issue tags on photos uploaded before this spec still show in the viewer; new uploads carry none.
- **AC-17**: The Settings hub shows the four new switches in the Tickets group and the new limit in the Files group, with no new UI code, and changes are logged like any other setting.
- **AC-18**: The audit timeline shows each move as "Moved a photo from Before to After" (or the reverse) with the actor and time. Photo audit events (added, removed, moved) name the groups Before and After, never "Vehicle photo" or "Proof of completion".
- **AC-19**: At 375px and 1280px: a disabled move button shows its reason as text (not color alone), the viewer's Move action is reachable by keyboard and screen reader, the flag and chip have text equivalents, and axe reports no violations on the ticket detail page.
- **AC-20**: While photos for this ticket are still in the upload queue, Start work is disabled with "Photos still uploading", so a photo picked before Start work can't land in After.
- **AC-21**: Before and After are one pool for duplicates: uploading a file already live in either group returns the existing photo as a duplicate (spec 0017 behavior), and a move never creates a second live copy.

## Decision

**Chosen option**: Option 2: one photo strip, labelled by whether work has started.

The upload service decides Before or After from the ticket's work start time, Admin switches gate Start work, Send for verification and Verify and close on those photos, and a viewer action fixes the occasional mislabel.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`) · `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-cli/`) · `vercel-react-best-practices` (`.claude/skills/vercel-react-best-practices/`)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch** (one migration, additive):

| Entity | Change | Notes |
|---|---|---|
| `RepairTicket` | add `workStartedAt DateTime?` (`work_started_at`, timestamptz) | set by `applyStatusMove` the first time the ticket enters `IN_PROGRESS` (M3) or `OUTSOURCED` (M9), in the same update; never cleared, not even when a release puts the ticket back to Open or Assigned, or an unlock reopens it |
| `Attachment` | add `takenAt DateTime?` (`taken_at`, timestamptz) | the phone's recorded time, from the browser (AC-12); null when absent or invalid |
| `Attachment.kind` | now updatable for photo rows (`VEHICLE_PHOTO` and `PROOF`) | the Move action (AC-9); no new enum value |
| `attachments_live_sha256_key` | the duplicate check treats both photo kinds as one pool | AC-21: `findDuplicate` looks across `VEHICLE_PHOTO` and `PROOF`; replace the partial unique index `(repair_ticket_id, kind, sha256)` with one keyed on a photo group expression (both photo kinds share a group) so the database backs the rule |
| `AuditLog` | new event `ATTACHMENT_MOVED`, `changes: [{ field: 'kind', before, after }]` | through `audit-events.ts`; the attachment id goes in the event data like spec 0017's attachment events |
| `KIND_RULES` | `PROOF.accepts` becomes images only; labels become "Before photo" and "After photo" | AC-2, AC-18; code only |

Backfill: set `workStartedAt` on existing tickets from the earliest `STATUS_CHANGE` audit row into `IN_PROGRESS` or `OUTSOURCED`, else from `statusChangedAt` when the ticket is in a started status today, else leave null. Existing `PROOF` rows: none outside tests, so no data change. If the live data holds duplicate photos across the two kinds, the index swap keeps the older row live and soft deletes the newer one, logged in the migration output.

**Settings** (in `src/settings/catalog.ts`):

| Key | Group | Type | Default | Label |
|---|---|---|---|---|
| `tickets.require_before_photo_to_start` | Tickets | boolean | true | Require a before photo to start work |
| `tickets.require_after_photo_to_send` | Tickets | boolean | true | Require an after photo to send for verification |
| `tickets.require_after_photo_to_close` | Tickets | boolean | false | Require an after photo to close |
| `tickets.protect_before_photos` | Tickets | boolean | true | Protect before photos once work starts |
| `uploads.max_after_photos` | Files | int 1 to 30 | 10 | After photos per ticket |
| `uploads.max_vehicle_photos` | Files | (unchanged) | 5 | label and description only: Before photos per ticket |

**Work started** is one helper, `workStarted(ticket)`: `workStartedAt` is not null. It decides the upload label (AC-1), the Before protection (AC-10) and the strip order (AC-16).

**State transitions**: the spec 0014 table is unchanged except for photo needs on three moves, each active only while its switch is on, plus the `workStartedAt` write on M3 and M9:

| Move | From → To | New need | Switch |
|---|---|---|---|
| M3 Start work | `ASSIGNED` → `IN_PROGRESS` | `beforePhoto` | `tickets.require_before_photo_to_start` |
| M4 Send for verification | `IN_PROGRESS` → `FOR_VERIFICATION` | `afterPhoto` (after `resolutions`) | `tickets.require_after_photo_to_send` |
| M5 Verify and close | `FOR_VERIFICATION` → `CLOSED` | `afterPhoto` (after `COSTS_REQUIRED`) | `tickets.require_after_photo_to_close` |
| M6 | label only: "Return to mechanic" | | |

A photo need can't be supplied inside the move dialog (unlike `costs` or `resolutions`), so `moves` gains a separate `blockedBy` next to `needs`. When both apply, the web shows `blockedBy` first, because it must be fixed outside the dialog; the server error order stays as AC-7 says.

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/repairs/:id/attachments` | POST (multipart) | `kind`: new DTO value `PHOTO` (`VEHICLE_PHOTO` and `PROOF` still accepted and treated as `PHOTO`, for queued uploads in an open tab), or `RECEIPT` / `OTHER_DOCUMENT`; `file`; `takenAt` (optional string; parsed in the service, never validated by the global pipe, so a bad value is dropped not rejected); `issueId` ignored for photos | the stored attachment, with its real `kind` | `ticket.files.add` / `ticket.documents.add` (spec 0017) | spec 0017 order; type check for `PHOTO` is images only; 409 cap per derived kind |
| `/vrms/repairs/:id/attachments/:attachmentId` | PATCH | `kind`: `VEHICLE_PHOTO` or `PROOF` | the attachment view | AC-9 | see order below |
| `/vrms/repairs/:id/attachments/:attachmentId` | DELETE | | 204 | spec 0017 plus AC-10 | adds 403 `BEFORE_PHOTO_PROTECTED` after `NOT_YOUR_FILE` |
| `/vrms/repairs/:id/attachments` | GET | | each row adds `canMove`, `returnedAfter`, and for verifiers only `takenAt`, `takenBeforeWork`; `limits` adds `afterPhotoCount` and `maxAfterPhotos` next to the existing vehicle photo pair; `kinds[]` lists `PHOTO` with images only accepts, for the web's type check | spec 0017 | unchanged |
| `/vrms/repairs/:id/status` | PATCH | unchanged | unchanged | spec 0014 | adds 400 `BEFORE_PHOTO_REQUIRED`, 400 `AFTER_PHOTO_REQUIRED` |
| `/vrms/repairs/:id` | GET | | each entry in `moves` adds `blockedBy: 'beforePhoto' \| 'afterPhoto' \| null`; adds `workStartedAt` | spec 0014 | unchanged |

**Upload flow with a derived kind**: before the lock, derive an early kind from the ticket as read and run `canAdd`, the size and type checks, the duplicate lookup and the cap check against it (spec 0017 order). Under the lock, derive the kind again from the locked row; if it changed, run the duplicate and cap checks again for the new kind before the insert.

**PATCH and DELETE under the lock**: `lockOpenTicket` returns the locked status and `workStartedAt`; the attachment row is read again inside the transaction. Protection, ownership, kind, duplicate and cap checks run on those fresh values. PATCH error order (first failing check wins): 404 visibility → 400 kind → same kind 200 no op → 403 `NOT_YOUR_FILE` → 403 `BEFORE_PHOTO_PROTECTED` → 409 `TICKET_FINISHED` → 409 duplicate in the target group → 409 cap. A unique index violation from a race answers the same 409 duplicate, never 500.

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| status move | `workStartedAt` | `now` of the move, written by `applyStatusMove` on M3 or M9 only when the column is null |
| upload | stored kind | `workStarted(ticket)` from the locked row (AC-1), early kind from the pre lock read |
| upload | `takenAt` | browser: `exifr` reads `DateTimeOriginal` from the original `File` before the shrink (the shrink drops all metadata); exifr turns the wall time into a `Date` in the device's time zone; sent as ISO UTC; server range check (AC-12) |
| upload / move | group limit | `uploads.max_vehicle_photos` or `uploads.max_after_photos` via `SettingsService.get`, per request |
| upload / move | duplicate | `sha256` across both photo kinds, live rows only (AC-21) |
| status move | photo present | count of `Attachment` rows with the needed kind and `deletedAt` null, inside `applyStatusMove` after the lock |
| status move / `moves` | rule on or off | the three `tickets.require_*` settings via `SettingsService.get` |
| `moves[].blockedBy` | need unmet | the same switch and count as the server check (one shared `photoNeedUnmet()`), so the button and the server never disagree |
| list | `takenBeforeWork` | `kind = PROOF`, `takenAt` and `workStartedAt` both set, and `takenAt` < `workStartedAt` minus 5 minutes |
| list | `returnedAfter` | `kind = PROOF` and `createdAt` strictly greater than `createdAt` of the latest `STATUS_CHANGE` audit row from `FOR_VERIFICATION` to `IN_PROGRESS` (M6), found with the same newest first scan as spec 0014's `lastRejectionFrom` (`REJECTION_SCAN_ROWS`) but not stopping at a resend; false when none |
| list | `canMove`, `canRemove` | the static `canRemove()` and a new `canMove()`, whose `RemoveRights` gain `workStarted` and `protectBefore`: caller id, `ticket.files.add`, `ticket.files.remove_any`, `tickets.protect_before_photos`, `workStarted` |
| list | include `takenAt`, flag | `ability.can` the verify permission (the role permission behind M5), not the per ticket `mayMake` |
| web strip | group order and counts | `workStartedAt` on the ticket detail and the list `limits` |
| web next action | reason text | `moves[].blockedBy` mapped to the AC-4 to AC-6 strings; "Photos still uploading" from the upload queue's pending jobs for this ticket (AC-20) |
| audit timeline | move text | `ATTACHMENT_MOVED` `changes` before and after, labelled Before and After in the web |

**Key invariants**:
- No path other than `AttachmentsService.upload` creates a photo, and no path other than the PATCH changes `kind`.
- `workStartedAt` is written only by `applyStatusMove`, once, and never cleared.
- Photo counts for rules and caps are read after the ticket row lock is taken; upload, remove, move and status moves all take that lock, so they serialize.
- A rule check happens only at its move (AC-7).
- At most one live copy of a file per ticket across both photo kinds (AC-21).
- `takenAt` and `takenBeforeWork` never leave the server for a caller without the verify permission, in the list or any audit payload.

**Security model**:
- Add: unchanged (`ticket.files.add`, on for all three roles; visibility per spec 0011).
- Move: uploader with `ticket.files.add`, or holder of `ticket.files.remove_any` (Chief and Admin by default, locked off for Mechanic in spec 0017). Under Before protection, moving out of Before after work starts needs `remove_any`.
- Remove: spec 0017 rules, plus AC-10.
- Flag data: verify permission only (AC-13), so mechanics can't learn what sets the flag off.
- `takenAt` is client supplied and forgeable, like the metadata it comes from. It is a signal for a person, never an enforcement input.
- No new PII: only a timestamp is kept, never GPS or the device model.

**Configuration required**: no new environment variables. One new web dependency, `exifr` (load only the `DateTimeOriginal` tag, so the bundle stays small).

**Failure and edge cases**:
- Two people act at once: the row lock serializes, so the later one sees the true count.
- A photo removed after Send for verification: allowed; the close switch or a Return to mechanic catches it (AC-7).
- A forgotten Before photo taken after Start work: it lands in After, and the uploader moves it to Before.
- Before full when moving into it: 409 with the limit message; a Chief removes one or an Admin raises the limit.
- A ticket released back to Open or Assigned after work started: `workStartedAt` stays, so new photos stay After and protection holds.
- An upload queued before Start work: Start work waits for the queue (AC-20). A retry after Start work (for example after a network drop) lands in After; the move fixes it.
- A HEIC the browser can't shrink: exifr still reads the time from the original file.
- A screenshot or a photo app that strips the time: no `takenAt`, so no flag.
- An upload queued in an open tab before release sends `VEHICLE_PHOTO` or `PROOF` with an `issueId`: treated as `PHOTO`, labelled by work start, `issueId` ignored.
- A label decided at arrival, so a retried job's 409 (cap or duplicate) refers to the group chosen at that moment.

**Critical test scenarios**:
- Happy path: create ticket → Before photo → Start work → After photo → Send for verification → Chief sees After first and verifies. Verifies **AC-1**, **AC-4**, **AC-5**, **AC-16**.
- Rule blocked: Start work with no Before photo gets 400 `BEFORE_PHOTO_REQUIRED` and a disabled button with its reason; switch off, it passes. Verifies **AC-4**, **AC-11**, **AC-17**.
- Order: Send for verification missing both "What fixed it" and an After photo answers the `resolutions` error first. Verifies **AC-7**.
- Race: remove the last After photo while Send for verification runs; exactly one outcome holds and the status matches the count at commit. Verifies **AC-7**.
- Release: a ticket released to Open after Start work keeps `workStartedAt`; a new photo is After and Before stays protected. Verifies **AC-1**, **AC-10**.
- Protection: a mechanic removing or moving their own Before photo after Start work gets 403 `BEFORE_PHOTO_PROTECTED`; a Chief succeeds; with the switch off the mechanic succeeds. Verifies **AC-10**.
- Move: a mechanic moves their own After photo to Before, the audit row is written, and a move into a full group gets 409. Verifies **AC-9**, **AC-3**, **AC-18**.
- Duplicate: the same file uploaded before and after Start work returns the first photo as a duplicate. Verifies **AC-21**.
- Flag: an After photo with `takenAt` 10 minutes before the start shows the flag to the Chief, 2 minutes before shows none, and the mechanic's list has no `takenAt`. A bad `takenAt` still uploads. Verifies **AC-12**, **AC-13**.
- Return mark: Return to mechanic, add a photo, resend; the new photo keeps "Added after return" and the old ones don't. Verifies **AC-14**, **AC-15**.
- Queue: with a photo still uploading, Start work is disabled with "Photos still uploading". Verifies **AC-20**.
- PDF as photo: 415. Verifies **AC-2**.

## Build plan

Tracer Bullet: the first slice runs one photo through every layer with its label; each later slice thickens one strand.

1. **Thin thread, labelled photos.**
   - The migration: `workStartedAt` with its backfill, `takenAt`, and the photo group duplicate index.
   - `applyStatusMove` writes `workStartedAt` on M3 and M9.
   - The `PHOTO` DTO value with its aliases, the derived kind before and under the lock, PROOF images only, the shared duplicate pool, `uploads.max_after_photos` and the Before relabel, and caps per derived kind.
   - The list `limits` and `kinds[]` additions.
   - The web: one add control without the issue picker, `kind` and `issueId` removed from the upload queue jobs, and the strip's two groups with counts and order.
   - Satisfies **AC-1**, **AC-2**, **AC-3**, **AC-16**, **AC-17**, **AC-21**
2. **Photo rules on the moves.**
   - The three `tickets.require_*` switches and one shared `photoNeedUnmet()`, called inside `applyStatusMove` for M3, M4 and M5 after the existing checks, and from `moves[].blockedBy`.
   - The 400 codes.
   - Disabled buttons with their reason text in `nextAction.ts` and the next action bar, `blockedBy` shown before `needs`, and "Photos still uploading" from the queue.
   - Any upload, remove or move refreshes the ticket detail query as well as the attachments query.
   - Satisfies **AC-4**, **AC-5**, **AC-6**, **AC-7**, **AC-8**, **AC-17**, **AC-20**
3. **Move and protect.**
   - The PATCH endpoint, with `lockOpenTicket` returning status and `workStartedAt`, the fresh row read and its error order.
   - `tickets.protect_before_photos` on remove and move; `canMove` and `canRemove` with the new `RemoveRights` inputs.
   - `ATTACHMENT_MOVED` in the audit action list, the audit reader filter (next to `ATTACHMENT_ADDED` and `ATTACHMENT_REMOVED`) and the web timeline text; Before and After labels in all photo audit text.
   - The viewer's Move menu.
   - Satisfies **AC-9**, **AC-10**, **AC-11**, **AC-18**
4. **Evidence signals.**
   - exifr in the upload queue before the shrink, and the `takenAt` parse and range check in the service.
   - `takenBeforeWork` with the 5 minute tolerance, for the verify permission only.
   - `returnedAfter` with the chip and viewer line.
   - "Return to mechanic": the M6 label in `ticket-transitions.ts`, plus every user facing "Send back" or "Sent back" in web-vrms (NextActionBar, SendBackBanner, TicketNoteDialog, TicketSidePanel, IssuesSection, nextAction.ts, resolutionForm.ts, dev-ui/worst-case/ticketData.ts) and the tests that assert those strings.
   - Satisfies **AC-12**, **AC-13**, **AC-14**, **AC-15**
5. **Hardening.**
   - Accessibility at 375px and 1280px with axe.
   - The race and release tests.
   - Unit tests for `photoNeedUnmet()`, the error orders, the derived kind change under the lock, and the value sourcing rows.
   - Satisfies **AC-7**, **AC-19**

## Consequences

**Positive**:
- Mechanics never choose a type; the label is right by construction and can't be spoofed by the client.
- Every in house ticket can carry a before and after pair by default, which is what verification and disputes need.
- `workStartedAt` makes "has work started" one column read instead of an audit scan, and it survives releases and unlocks.
- No new table, and the switches reuse the Settings hub and the permission matrix as they are.

**Negative / tradeoffs**:
- The label follows timing, not intent: a late Before photo lands in After until someone moves it.
- After photos lose PDF support; a job sheet must go in Documents, which mechanics can't see without cost rights.
- One new web dependency (exifr). `takenAt` is client supplied, so the flag is a nudge, not proof.
- Swapping the duplicate index needs care if live data already holds the same photo in both kinds.
- The list read does one more audit scan (the latest return).
- Default on rules change behavior for tickets in flight on release day: an `ASSIGNED` ticket with no Before photo can't start until someone adds one.
- The "Return" wording touches about ten web files and their tests.

**Neutral**:
- One additive migration (two nullable columns, a backfill and an index swap).
- Spec 0017's optional issue tag stays in the data and the viewer, but no screen sets it any more.
- Feature 23 no longer owns the proof view on verification; it keeps the verifier in reports.

## Follow-up

- [x] Record `exifr` as a web-vrms dependency and its Agent Skill search as declined (2026-11-02) in `welinc-web-vrms/AGENTS.md` (via /sync).
- [x] backend-vrms `AGENTS.md`: `workStartedAt` is written only by `applyStatusMove`. Attachments `AGENTS.md`: the derived kind, the PATCH move, the Before protection, the duplicate pool and the photo rules (via /sync).
- [x] Feature 23: drop "showing proof files at verification" from its remaining work.
- [x] Feature 49 (offline): queued uploads must keep `takenAt` read from the original file.
- [ ] Outsourcing (features 37, 38): decide whether a returned truck needs an After photo; the rules here skip M9 to M13 (M9 only sets `workStartedAt`). Carried as a note on feature 37 (2026-11-03); the decision is still open.
- [x] Consider a `verify.md` for this spec before `/check verify`.
