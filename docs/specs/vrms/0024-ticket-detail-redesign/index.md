# 0024. Ticket detail page around foldable issue rows

**Date**: 2026-11-06
**Status**: In Progress

## Summary

The repair ticket page is rebuilt around the work. Each issue becomes a row that folds open and closed (an accordion), showing its progress and state when closed, so a ticket with 10 issues and up to 20 steps each stays readable. Reference clutter goes (typical parts and hours), photos get their own card after the issues with one add control that says where the photo lands, AI folds to one line, and no part of the page is joined by a dot, the title follows the design file, Cancel ticket moves into a menu, and on phones the issues come before people and details. It is a web only change on data the page already has: no new endpoint, no migration.

## Requirements

**User stories**:
- As a mechanic on my phone, I want the issue I am working on open and the rest folded, so that I tick steps without scrolling past finished work.
- As a verifier, I want every issue folded with what fixed it on the row, so that I can sign off a whole ticket from one screen.
- As an Admin, I want the page to look like a well made work order, plain where it can be and coloured only where it means something, so that the important things stand out.
- As anyone, I want the plate and the main issue as the title, so that I know which truck I am looking at.

**Acceptance criteria**:

Issue rows
- **AC-1**: Issues render as one list of foldable rows (shadcn Accordion, `type="multiple"`), split by thin dividers inside the Issues card, with no bordered box inside a row. The whole row header is one button (`aria-expanded`, `aria-controls`, at least 44px tall on phones), inside an `h3`, and folding uses the `ease-snappy` curve (none with reduced motion).
- **AC-2**: A closed row is at most two lines. Line 1: the issue number, the issue text (semibold, one step above body text: `text-base` from 768px, `text-sm` on phones) (2 lines at most on phones, 1 from 768px, cut with an ellipsis), and on the right the progress and the chevron. Line 2, muted `text-xs`, its parts split by space only (`gap-3`, never a dot or other symbol): the category, then "Known fix: {name}" or "No known fix", then the word "Safety" in the warning colour when the linked known fix has safety notes (trimmed, not empty). The known fix name is plain text here (never a link: the header is one button with no controls inside), with its status badge when the entry is Draft or Inactive. Once the issue has a saved resolution, line 2 shows "What fixed it" instead: the note, else "Followed the known fix" when `followedKnownFix`, else nothing, cut to 1 line, then the hours as "2.5 h" when `hoursSpent` is set, split from the note by space. A Done issue with no saved resolution while the ticket is In progress shows "Needs what fixed it" in muted text at the end of line 2. Once a resolution is saved, line 2 holds only What fixed it and the hours (no category, known fix or Safety word); the safety line inside the open row (AC-8) still shows. "Needs what fixed it" shows only while the ticket is In progress, never in On hold, Outsourced, Pending approval or later.
- **AC-3**: The issue's state (derived, nothing stored) shows as the progress text with a slim bar under it (4px, full width of the progress column):
  - **Returned**: the issue has a saved resolution but no `resolvedAt` (spec 0014); gold `highlight` text "Returned", bar hidden. Wins over every other state.
  - **No checklist**: the issue has no steps; muted text, no bar.
  - **Not started**: steps exist, none ticked; muted "Not started", empty bar.
  - **In progress**: some ticked; "{x} of {y}" in tabular figures, bar in the In progress token.
  - **Done**: all ticked; "Done" in the `success` colour, full bar in `success`.
  Ticks made on this page count at once: the local tick overrides move up from `IssueBlock` into one `useTickOverrides` hook for the whole list (keyed by step id, cleared for an issue when its `checklistVersion` changes, and an override dropped once the server value equals it), so the closed row, the summary line and the open rule all read the same merged steps (`mergedSteps` in `lib/issueRow.ts`). The overrides live outside the folding content, so folding a row never drops a pending tick or its rollback. Returned rests on the rule that resolution notes are saved only on the move to For verification, so notes without `resolvedAt` mean the ticket came back.
- **AC-4**: Which rows start open, on a first visit to this ticket in this tab: while the ticket is Open, Assigned, In progress, On hold, Outsourced or Pending approval (an allow list in `initialOpen`, not "every other status"), the first row that is not Done and not No checklist opens (a Returned row counts as not Done), and every row opens when the ticket has 3 issues or fewer; in For verification, Closed and Cancelled every row starts closed. The rule depends on status only, not role. Issue order is the array order the ticket response sends (by `createdAt`, then `id`; a backend test locks it). A link with `#issue-N` (N from 1, today's order) opens that row on top of whatever is open or stored, and scrolls it into view once per hash value (rows carry `scroll-margin-top` for the sticky header); an N out of range is ignored.
- **AC-5**: Open and closed rows, and the one Hide done steps switch, are remembered per ticket in `sessionStorage` (`vrms.ticket.<id>.view`, shape `{ open: string[], hideDone: boolean }`, checked when read, an older shape read as `hideDone: false`, at most the 20 most recent tickets kept). The open value lives in `useTicketView`, never derived from props, and drives the Accordion as a controlled `value`. A stored state wins over AC-4 on a reload. The 3 second refresh never opens or closes a row; an issue that appears later starts closed; a removed issue drops out of the stored state. If storage fails, the page uses AC-4 and keeps state in memory. When the stored shape is the older one (a list of issue ids under `hideDone`), that list is dropped and `hideDone` reads as false.
- **AC-6**: Above the rows, one line: "{d} of {n} issues done, {t} of {s} steps ticked" (the step part counts only issues with steps and is left out when none have steps; "1 issue" and "1 step" in the singular). On the right, one quiet control: "Hide done steps" (one switch for every issue, shown only once any step on the ticket is ticked). There is no Expand all or Collapse all: each row's header opens and closes it, and the open rows are remembered (AC-5). While no step on the ticket is ticked the switch is hidden and a stored `hideDone: true` is ignored, not reset.

Inside an open row
- **AC-7**: Top to bottom: the safety note, the checklist, one quiet "Edit steps" (or "Add steps") text button, then the resolution. The issue's other actions sit in a `⋮` row menu (`dropdown-menu`, 44px target on phones) at the right of the Edit steps line: Edit issue and Remove issue (spec 0019, Remove in `destructive` text), Change known fix (relink, spec 0007, only when the issue may be relinked) and Open known fix (`/knowledge-base/<entryId>`, only while `knowledgeOn`). Each keeps its current `can` rule; the `⋮` is not shown when the menu would be empty. Choosing Change known fix shows the link picker inline in the row with "Remove link" and "Keep it". Edit issue and Remove issue follow `canEditDetails` (the edit flag and `ticketEditable`, as today); Remove is hidden when the ticket has one issue (spec 0019, AC-17). The row menu sits in the open content, never inside the header button, and its trigger is named "More actions for issue {n}" and shows a "More actions" tooltip on hover and focus.
- **AC-8**: The safety note is one line of `warning` tinted text (no box, no icon) above the checklist, cut to 1 line (`line-clamp-1`) with "More" shown only when the text is actually cut off, expanding it in place. It never hides behind a fold other than the row itself, and the closed row's "Safety" word (AC-2) points to it.
- **AC-9**: The checklist keeps its ticks, rules and tags (specs 0007, 0021, 0023). Done steps show dimmed (no strikethrough). Step rows are at least 44px tall on phones and 36px from 768px. With the AC-6 Hide done steps switch on, each open row shows one line "{k} done steps hidden" in place of its done steps. The line reads "1 done step hidden" in the singular and sits above the remaining steps; a row whose steps are all done shows only that line above Edit steps.
- **AC-10**: Typical parts and typical hours are no longer shown on the ticket, and the open row has no separate known fix line: the name is on line 2 of the row header (AC-2) with its status badge when Draft or Inactive, and Open known fix and Change known fix live in the row menu (AC-7). An issue with no known fix keeps the link picker (when it may be linked) and "Suggest a known fix" inline in the open row.

Page
- **AC-11**: The title is the plate chip, then the model when `vehicleModel` is set, then the first issue's text (cut to 1 line; left out when the ticket has no issues); the ticket ID and garage sit below in `muted-foreground`, split by space (no dot), the ID never breaking (`docs/context/vrms/design.md`, Naming a ticket).
- **AC-12**: Issue text never shows the stored `[System] ` prefix anywhere on the page (rows, title, dialogs such as Edit steps); the category shows once, from `categoryName`.
- **AC-13**: Photos are their own card ("Photos"), right after the Issues card and before AI, with no fold and `scroll-margin-top` for the sticky header (as the rows, AC-4). Two groups in a fixed order, Before then After (side by side from 768px, Before on the left; stacked below 768px, Before on top), never swapping when work starts. Each group sits under a small heading with its count ("Before", then "2 of 5" in muted text, split by space). Thumbnails are fixed 72px squares, at most 4 slots in a row, so the row never wraps at any width:
  - **Photos in a group**: up to 3 thumbnails. With more than 3, it shows the first 2, then a "+{N} more" tile (N = count minus 2, named "Show {N} more {before|after} photos") that opens the viewer at the group's third photo. The viewer still walks every live photo on the ticket, Before then After, as today (spec 0017, AC-24); closing it returns focus to the thumbnail or tile that opened it. Each thumbnail keeps Remove (`canRemove`) and the viewer keeps Move (`canMove`, spec 0018, AC-9).
  - **The add tile**: the only add control, a 72px tile in the fourth slot of the group new photos land in, from `uploadGroup(ticket.workStartedAt != null)` (Before until work starts, After from then on, spec 0018). Its name is "Add before photo" or "Add after photo", it opens the file picker in the same click (the hidden file input sits inside the card, `aria-hidden`, driven by the tile) with no `capture` attribute, so a phone offers its camera or its gallery from the system sheet (the separate Take photo and Choose photos buttons go). The other group never has an add control. Which group a photo lands in stays the server's call (spec 0018); photos still uploading hold Start work as today (spec 0018, AC-20).
  - **Full**: when the target group has no room, counting queued uploads (`photoRoomLeft`), the tile is replaced by "{Before|After} photos full ({n} of {max})" in muted text. Picking or dropping more files than fit keeps the first ones that fit and shows today's message for the rest.
  - **Empty and read only**: a group with no photos and no tile says "None yet". People who can't add (no `can.addFiles`, or a finished ticket) see the same groups with no tile and no limit text, and no card at all while there are no photos (spec 0017, AC-20).
  - **Drop**: on a pointer device, files dropped anywhere on the card upload to the target group, and the whole card shows the drop highlight while dragging over it (today's ring). On touch the drop hint is not shown; the tile covers it.
  - **Queue**: the upload queue rows sit under both groups, full width, in a polite live region, as today.
  - **Needed hint**: the card header shows "Before photo needed" or "After photo needed" (from `blockedBy` through `photoNeededHint`) in `warning-text` at its top right, only while a photo blocks the next move; a reason that is not a photo shows no hint.
  - **Loading and errors**: on the first load only, each group shows its heading without a count and 3 skeleton squares; a refetch (focus, the 8 minute link refresh, after an upload) updates the card in place with no skeleton, and the "+N more" count follows the live list. The viewer clamps its index when photos drop out, as today. On a load error the card shows the error with Try again, which reloads the file list only.
  - **The blocked link**: only the two photo reasons (any wording `nextAction.ts` gives for `beforePhoto` or `afterPhoto`) become a link in the Status card; costs, uploading and other reasons stay plain text. `ticketActions` passes `blockedBy` along with the text. The link scrolls to the Photos card and focuses its add tile (it does not start the file picker, which browsers block after the click has passed); with no tile (the group is full, or the viewer can't add) it focuses the card's heading (`tabIndex=-1`). On phones the reason shows in the slim status line and the bottom bar as today, and the bar button's `aria-describedby` points at the visible reason.
- **AC-14**: AI diagnosis is a folded card right under the Photos card (under the Issues card when there is no Photos card): closed it shows one line ("AI suggests {category}, {priority} priority", or "No AI diagnosis yet" with Run); open it shows today's section. The latest diagnosis is fetched by the card whether folded or not (folding never unmounts the fetch). Priority shows in sentence case ("High"). States: loading (a one line skeleton), error (one line with Retry), none, and the module off (no card). It stays per ticket.
- **AC-15**: Activity is open and shows the 5 newest entries (`limit: 5`); "Show all" fetches the first 50 and replaces the 5, then pages on with today's cursor. The 3 second refresh does not reload it. Without `audit.view` there is no Activity card, as today; with no entries it says "No activity yet".
- **AC-16**: Vehicle & driver moves into the sidebar Details card, which drops Plate and Model (the title shows them) and Priority and Due date (the Status card shows them, AC-17), and groups the rest under two small headings split by a divider: **Vehicle** (odometer, driver with its verified mark, account as "Corporate, {corporation}" or "Online") and **Record** (garage, created, updated, last edit, closed). Its Edit button opens the details dialog as today. Notes (`ticket.remarks`, and the cancellation reason when set, as `NotesSection` shows them today) become a sidebar card after the Status card, a 3 line preview (`line-clamp-3`) with "Show more" only when cut off; no card when both are empty. The Edit button keeps its current rule (`canEditDetails`). Closed shows only once `closedAt` is set; empty fields show "—" as today. The cancellation reason stays in the Notes card at every width.
- **AC-17**: The Status card has no "Status" heading. Its first row is the status badge, the priority badge (when set) and the lock and mechanic badges (the status and priority badges show a "Ticket status" and a "Priority" tooltip on hover, and screen readers hear the same word before each), with a `⋮` More actions menu (`dropdown-menu`) on the right holding Cancel ticket in `destructive` text, opening today's cancel dialog; no other action is added to the menu now, and the `⋮` is not shown when the ticket has no cancel action. Next is the due date ("Due Nov 4, 2026"), with its due or overdue text on its own line under it (overdue in `destructive` with its icon, as today), never joined by a dot. Then the primary button and Return to mechanic, stacked, with the blocked reason as helper text under the primary button (`aria-describedby`). No priority means no priority badge; no `dueAt` means no due line. Closed and Cancelled tickets show the due date only, never due or overdue text; For verification and every open status keep it. The Status card trigger is named "More actions" and shows a "More actions" tooltip on hover and focus.
- **AC-18**: Below 1024px the page reads: a slim status line (the AC-17 badges and `⋮`, the due line, the blocked reason), the Notes preview, Issues, Photos, AI, Costs, People, Details, Activity. The primary action stays only in the fixed bottom bar, and the page keeps enough bottom padding that the bar never covers Activity. The chevron area and every `⋮` button are 44px targets on phones. From 1024px the sidebar returns to the right as today. The slim status line carries the priority badge and due line the same way as the Status card.

Look and quality
- **AC-19**: Built to `design.md` and `docs/context/vrms/design.md` with the work order look: hierarchy from size and weight, not boxes; no icon before a label; no box inside a box; no gradient or new shadow; colour only for status, progress state, overdue, safety, Returned and destructive actions; tabular figures for counts. No dot separator (`·`) anywhere on this page, its dialogs or the photo viewer: parts are split by space, commas, words or their own line. The wording: the summary "0 of 2 issues done, 2 of 6 steps ticked"; the account "Corporate, {corporation}"; the step tooltip "Ticked by {email} on {date}"; a Documents card row with the uploader on one line and the date on the next; the AI run line "Ran {time ago} with {model}, {confidence} confidence"; the photo viewer caption as three lines (the group, the date, the issue when tagged), since the date already holds commas; the Edit steps dialog's tag and ticked note split by space. A Vitest check fails when `·` appears in the ticket page code (`src/features/repair/` outside `repair-form/` and `RepairFormPage.tsx`). Tokens only (lint enforces it).
- **AC-20**: The page and its states (loading skeleton as 3 folded rows, empty issues, error) pass axe at 375px and 1280px, every row and control works by keyboard, and folding never moves focus. Both `⋮` menus open with Enter, Space and the arrow keys, and Escape closes them with focus back on their trigger.

## Decision

**Chosen option**: Option 1: Foldable issue rows on the existing page, built on the data the page already has.

The Issues card becomes an accordion of issue rows with a derived state, the reference clutter goes, and the side sections move to follow the design file, without any backend change.

**Implementation skills**: `shadcn` (`shadcn-ui/ui`, `.claude/skills/shadcn/`, adding the Accordion and theming it) · `vercel-react-best-practices` (`vercel-labs/agent-skills`, `.claude/skills/vercel-react-best-practices/`, the row state, effects and lists) · `tailwind-4-docs` (`.claude/skills/tailwind-4-docs/`, the fold animation and tokens)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch**: none. No schema change. Every value comes from the ticket response, the file list and the latest diagnosis the page already loads.

**State transitions**: none on the server. The issue state of AC-3 is derived on each render; its precedence is Returned, No checklist, Done, In progress, Not started.

**API surface**: no new or changed endpoint.

| Endpoint | Method | Use | Change |
|---|---|---|---|
| `GET /vrms/repairs/:id` | GET | issues, steps, resolution fields, `categoryName`, knowledge entry with `safetyNotes` | none |
| `GET /vrms/repairs/audit-logs?ticketId=` | GET | Activity | first call with `limit: 5`, then today's paging at 50 |
| `GET /vrms/ai/tickets/:id/diagnoses/latest` | GET | the AI one line | none |
| ticket attachments list (spec 0017) | GET | photo counts | none |

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Closed row | issue text without prefix | `issue.description` with a leading `[...] ` removed (`stripSystem` in a new `lib/issueRow.ts`, matching `issueDescription` in backend `ticket-inputs.ts`) |
| Closed row | category | `issue.categoryName` |
| Closed row | "Known fix: {name}", status, Safety word | `issue.knowledgeEntry` (`name`, `status`, `safetyNotes` trimmed and not empty) from the ticket response |
| Closed row | progress {x} of {y} | `mergedSteps(issue, overrides)`: `issue.steps` with `checkedAt` plus `useTickOverrides` at list level |
| Closed row | state | derived (AC-3) from steps, `resolvedAt`, and `hasSavedResolution` in `lib/resolutionForm.ts` |
| Closed row | What fixed it, hours | `issue.resolutionNote`, else "Followed the known fix" when `issue.followedKnownFix`; `issue.hoursSpent` through `formatHours` |
| Closed row | Needs what fixed it | state Done, no saved resolution, ticket In progress |
| Page load | which rows open | AC-4 rule from `ticket.status`, issue count and each state, unless `sessionStorage` or `#issue-N` says otherwise |
| Summary line | {d} of {n} issues done, {t} of {s} steps ticked | the AC-3 states and step counts over `ticket.issues` |
| Photos card | each group's count, its first 3 photos or first 2 plus "+N more" (N = count minus 2), where the viewer opens | `photoGroups(useTicketFiles().attachments, ticket.workStartedAt)` (spec 0018); the viewer index is the group's third photo in the flat Before then After list; skeletons on the first load only |
| Photos card | which group gets the add tile, its label; the needed hint | `uploadGroup(ticket.workStartedAt != null)` (the same rule the server uses); the next move's `blockedBy` through `photoNeededHint`; full from `photoRoomLeft` and `groupLimit` |
| Blocked link | where focus goes | the forward move's `blockedBy` (`beforePhoto` or `afterPhoto`), passed through `ticketActions`; focus lands on the Photos card's add tile |
| Title | plate, model | `ticket.vehiclePlate`, `ticket.vehicleModel` (left out when unset) |
| Title | main issue | `ticket.issues[0]` (response order, `createdAt` then `id`), through `stripSystem` |
| Title | ID, garage | `ticket.repairNumber`, `ticket.garageLocation` |
| AI line | category, priority | the latest diagnosis' `predictedCategory`, `predictedPriority` (sentence case), fetched by the AI card |
| Notes card | text | `ticket.remarks`, and the cancellation reason when set |
| Status card | priority, due, overdue | `ticket.priority`, `ticket.dueAt` through `dueLabel` (as the Details card did) |
| Row menu | which items show | `canEditDetails` (Edit, Remove with more than one issue), `canLink` (Change known fix), `knowledgeOn` and a linked entry (Open known fix) |
| Activity | 5 newest | `getAuditEvents({ ticketId, limit: 5 })`; Show all refetches `limit: 50` and pages by cursor |
| Remembered view | open rows, one Hide done steps switch | `sessionStorage` key `vrms.ticket.<ticketId>.view`, `{ open: string[], hideDone: boolean }` |

**Key invariants**:
- The issue state is never stored and never sent; one pure function (`issueState` in `lib/issueRow.ts`) decides it, used by the row, the summary line and the open rule.
- The refresh changes values on rows, never which rows are open.
- Nothing about permissions moves to the client: Edit steps, ticks, Edit issue, Remove issue, Change and Cancel keep their current `can` flags (`editChecklist`, `work`, `edit`, `administer`, and the ticket's cancel action).
- A step action never sits on the closed row; the closed row is for reading.
- No new colour tokens; the bar and words use `status-in-progress`, `success`, `highlight`, `warning` and `muted-foreground`.

**Security model**: unchanged. The page shows what the ticket response already carries for the caller; costs and documents keep their `ticket.costs.view` gate, Activity keeps `audit.view`, AI keeps its module switch.

**Configuration required**: none.

**Critical test scenarios**:
- Mechanic, In progress ticket with 5 issues where issue 1 is Done: issue 2 opens, the rest are closed, the summary reads "1 of 5 issues done", ticking the last step of issue 2 turns it Done at once and does not fold it. Verifies **AC-3**, **AC-4**, **AC-5**, **AC-6**.
- Verifier on For verification: all rows closed, each line 2 shows What fixed it and hours. Verifies **AC-2**, **AC-4**.
- Returned ticket (sent back): every issue with notes shows gold "Returned". Verifies **AC-3**.
- Reload keeps the rows you opened; a new tab starts from the rule; `#issue-3` opens issue 3. Verifies **AC-4**, **AC-5**.
- Issue with no steps and no known fix: "No checklist", line 2 "No known fix", picker and Suggest inside. Verifies **AC-2**, **AC-3**, **AC-10**.
- Blocked Send for verification with no photos: the Photos card after Issues says "After photo needed" at its top right and shows "+ Add after photo" only in After; the reason (under the button from 1024px, in the slim status line below) is a link that scrolls to the card and focuses the tile. Verifies **AC-13**, **AC-17**.
- 375px: status line with priority and due, Notes, Issues, then Photos, before People and Details; the main button only in the bottom bar; every `⋮` is a 44px target. Verifies **AC-17**, **AC-18**.
- Unit tests (pure, Vitest): `issueState` for each state and the precedence, `stripSystem`, the open rule for each status and the 3 issue limit, the summary counts, the stored view merge (new and removed issues). Verifies **AC-3** to **AC-6**, **AC-12**.

## Build plan

Facade: the UI is the whole change, so each slice is a working page on real data, biggest value first.

1. [x] **Pure rules**: `lib/issueRow.ts` with `stripSystem`, `mergedSteps`, `issueState`, `initialOpen` (AC-4) and `summaryCounts`, plus `useTicketView` (the `sessionStorage` state, its shape check and pruning, `#issue-N` once per hash) and `useTickOverrides` lifted from `IssueBlock`; Vitest tests; a backend test that ticket issues come ordered by `createdAt`, then `id`. Satisfies **AC-3** to **AC-6**, **AC-12**.
2. [x] **Issue rows** (its summary controls replaced by task 6): add the shadcn Accordion; rebuild `IssuesSection` as foldable rows with the closed row (AC-2, AC-3), the summary line with Expand all and Collapse all, and the open row order (safety line, checklist with dimmed done steps and Hide done steps, step actions with Edit steps, Edit issue and Remove issue, resolution); remove typical parts and hours and the known fix box; `stripSystem` in the Edit steps subtitle too. Satisfies **AC-1** to **AC-10**, **AC-12**.
3. [x] **Page frame** (its photos line replaced by task 6): the title (plate chip, model, first issue; ID and garage below); Notes and Vehicle into the sidebar; the `⋮` menu with Cancel ticket; the phone order with the slim status line; the photos line and the blocked reason link; AI as a folded card; Activity with the 5 newest. Confirm nothing besides the removed line reads typical hours. Satisfies **AC-11**, **AC-13** to **AC-18**.
4. [x] **Sweep**: the skeleton as folded rows, axe at 375px and 1280px with rows open and closed, keyboard pass, reduced motion, lint, typecheck, build, tests. Satisfies **AC-19**, **AC-20**.
5. [x] **Refinements** (agreed 2026-11-06 after the first build; replaces what tasks 2 and 3 built for the row controls, the known fix line, the per issue Hide done steps switch, the Status card heading and the Details layout): the row `⋮` menu and no known fix line (AC-7, AC-10); one Hide done steps switch on the summary line, stored as a boolean (AC-5, AC-6, AC-9); the photos line folded with the needed hint and the one line empty state (AC-13); the Status card without its heading, with priority, due and the reason under the button, on the phone line too (AC-17, AC-18); Details grouped into Vehicle and Record without plate, model, priority and due (AC-16); the semibold issue title and 36px step rows from 768px (AC-2, AC-9); unit tests for the stored view's new shape and the needed hint; axe at 375px and 1280px again.
6. [x] **Second refinements** (agreed 2026-11-07 after the refinements build; replaces what task 5 built for the photos line, the summary controls and every dot separator): the Photos card after Issues with Before and After side by side, one row each with "+N more", the one add tile in the target group, drop on the card, the needed hint at the top right, and the blocked link focusing the tile; `PhotosLine` and the page's `photosOpen` state go (AC-13, AC-14, AC-18); Expand all and Collapse all removed, with `expandAll` and `collapseAll` taken out of `useTicketView` (AC-6); no dot separator on the page: the summary sentence, row line 2, the header ID and garage, the due line, the account value, the step tick tooltip, the Documents card rows, the AI card's run line, the Edit steps dialog and the photo viewer caption (`photoCaption.ts`) (AC-2, AC-6, AC-11, AC-16, AC-17, AC-19); unit tests for the summary sentence, the "+N more" count and viewer index, the caption lines, and a check that no `·` is left in the ticket page code; AC-14's AI card now follows the Photos card; axe at 375px and 1280px again. Already built in `6e19286`: the hover labels on the status and priority badges and both `⋮` menus (AC-7, AC-17).

## Consequences

**Positive**:
- A 10 issue ticket fits on one or two screens; the work in progress is open, the rest reads at a glance.
- The verifier signs off from closed rows without clicking.
- The page now follows its own design file (title, phone order, Cancel, no boxes per item).
- No backend change, so no migration risk and nothing for the other groups.

**Negative / tradeoffs**:
- One Hide done steps switch hides done steps in every open row, including rows you have not read yet; each open row says how much it hides through its "{k} done steps hidden" line.
- One more tap to see a closed issue's steps.
- Without Expand all, reading every issue means opening each row; the verifier reads the closed rows instead, and the page remembers what was opened.
- A phone no longer has its own Take photo button; the one add tile reaches the camera through the system picker, which is one more tap on some phones.
- Typical parts and hours are only on the knowledge entry now; someone who used them as a quick parts list opens the entry.
- The "Done" state means all steps ticked, not that the mechanic says the issue is finished; an issue with no steps never shows Done.
- Per tab memory means a new tab or another device starts from the default rule.
- Verification stays per ticket; a per issue sign off (topic 3) would add an Approved state to the row later.
- The AI card stays per ticket even though it now sits next to the issues.

**Neutral**:
- Feature 11's deferred tests now wait for this build.
- The shadcn Accordion is a new UI component in `src/components/ui/`.

## Follow-up

- [ ] **Topic 3 (workflow review)**: per issue verification (sign off or return one issue, close when all are signed off). The closed row has room for an Approved mark.
- [ ] **Knowledge entry page**: check that typical parts and hours are easy to find there, since the ticket no longer shows them.
- [ ] **Feature 64**: group a checklist save's step rows in Activity when the Audit log page is redesigned.
- [ ] **AI per issue** (later, its own spec): a diagnosis per issue would need new AI endpoints.
- [ ] **`/sync`**: record in `welinc-web-vrms/AGENTS.md` that the issue state is derived only by `issueState` and that the ticket view lives in `sessionStorage` as `{ open: string[], hideDone: boolean }`.
- [ ] **For the PM (Jira)**: "Ticket detail redesign: foldable issues with progress and state, no typical parts or hours on tickets, title and phone order fixes, Cancel in a menu" (feature 65).
