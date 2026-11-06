# 0024. Ticket detail page around foldable issue rows

**Date**: 2026-11-06
**Status**: Proposed

## Summary

The repair ticket page is rebuilt around the work. Each issue becomes a row that folds open and closed (an accordion), showing its progress and state when closed, so a ticket with 10 issues and up to 20 steps each stays readable. Reference clutter goes (typical parts and hours), photos and AI fold into one line each, the title follows the design file, Cancel ticket moves into a menu, and on phones the issues come before people and details. It is a web only change on data the page already has: no new endpoint, no migration.

## Requirements

**User stories**:
- As a mechanic on my phone, I want the issue I am working on open and the rest folded, so that I tick steps without scrolling past finished work.
- As a verifier, I want every issue folded with what fixed it on the row, so that I can sign off a whole ticket from one screen.
- As an Admin, I want the page to look like a well made work order, plain where it can be and coloured only where it means something, so that the important things stand out.
- As anyone, I want the plate and the main issue as the title, so that I know which truck I am looking at.

**Acceptance criteria**:

Issue rows
- **AC-1**: Issues render as one list of foldable rows (shadcn Accordion, `type="multiple"`), split by thin dividers inside the Issues card, with no bordered box inside a row. The whole row header is one button (`aria-expanded`, `aria-controls`, at least 44px tall on phones), inside an `h3`, and folding uses the `ease-snappy` curve (none with reduced motion).
- **AC-2**: A closed row is at most two lines. Line 1: the issue number, the issue text (2 lines at most on phones, 1 from 768px, cut with an ellipsis), and on the right the progress and the chevron. Line 2, muted `text-xs`: the category, then the known fix name or "No known fix", then the word "Safety" in the warning colour when the linked known fix has safety notes (trimmed, not empty). The known fix name is plain text here (never a link: the header is one button with no controls inside), with its status badge when the entry is Draft or Inactive. Once the issue has a saved resolution, line 2 shows "What fixed it" instead: the note, else "Followed the known fix" when `followedKnownFix`, else nothing, cut to 1 line, then the hours as "2.5 h" when `hoursSpent` is set. A Done issue with no saved resolution while the ticket is In progress shows "Needs what fixed it" in muted text at the end of line 2.
- **AC-3**: The issue's state (derived, nothing stored) shows as the progress text with a slim bar under it (4px, full width of the progress column):
  - **Returned**: the issue has a saved resolution but no `resolvedAt` (spec 0014); gold `highlight` text "Returned", bar hidden. Wins over every other state.
  - **No checklist**: the issue has no steps; muted text, no bar.
  - **Not started**: steps exist, none ticked; muted "Not started", empty bar.
  - **In progress**: some ticked; "{x} of {y}" in tabular figures, bar in the In progress token.
  - **Done**: all ticked; "Done" in the `success` colour, full bar in `success`.
  Ticks made on this page count at once: the local tick overrides move up from `IssueBlock` into one `useTickOverrides` hook for the whole list (keyed by step id, cleared for an issue when its `checklistVersion` changes, and an override dropped once the server value equals it), so the closed row, the summary line and the open rule all read the same merged steps (`mergedSteps` in `lib/issueRow.ts`). The overrides live outside the folding content, so folding a row never drops a pending tick or its rollback. Returned rests on the rule that resolution notes are saved only on the move to For verification, so notes without `resolvedAt` mean the ticket came back.
- **AC-4**: Which rows start open, on a first visit to this ticket in this tab: while the ticket is Open, Assigned, In progress, On hold, Outsourced or Pending approval (an allow list in `initialOpen`, not "every other status"), the first row that is not Done and not No checklist opens (a Returned row counts as not Done), and every row opens when the ticket has 3 issues or fewer; in For verification, Closed and Cancelled every row starts closed. The rule depends on status only, not role. Issue order is the array order the ticket response sends (by `createdAt`, then `id`; a backend test locks it). A link with `#issue-N` (N from 1, today's order) opens that row on top of whatever is open or stored, and scrolls it into view once per hash value (rows carry `scroll-margin-top` for the sticky header); an N out of range is ignored.
- **AC-5**: Open and closed rows, and the Hide done steps switch, are remembered per ticket in `sessionStorage` (`vrms.ticket.<id>.view`, shape `{ open: string[], hideDone: string[] }` of issue ids, checked when read, at most the 20 most recent tickets kept). The open value lives in `useTicketView`, never derived from props, and drives the Accordion as a controlled `value`. A stored state wins over AC-4 on a reload. The 3 second refresh never opens or closes a row; an issue that appears later starts closed; a removed issue drops out of the stored state. If storage fails, the page uses AC-4 and keeps state in memory.
- **AC-6**: Above the rows, one line: "{d} of {n} issues done · {t} of {s} steps" (the step part counts only issues with steps and is left out when none have steps; "1 issue" and "1 step" in the singular), with "Expand all" and "Collapse all" as quiet text buttons on the right (hidden when there is one issue).

Inside an open row
- **AC-7**: Top to bottom: the safety note, the checklist, the step actions, then the resolution. Edit issue and Remove issue (spec 0019) move from the header into the open row, as quiet buttons on the step actions line.
- **AC-8**: The safety note is one line of `warning` tinted text (no box, no icon) above the checklist, cut to 1 line (`line-clamp-1`) with "More" shown only when the text is actually cut off, expanding it in place. It never hides behind a fold other than the row itself, and the closed row's "Safety" word (AC-2) points to it.
- **AC-9**: The checklist keeps its ticks, rules and tags (specs 0007, 0021, 0023). Done steps show dimmed (no strikethrough). A "Hide done steps" switch sits on the step actions line beside Edit steps, one per issue, off by default, remembered per AC-5; with it on, a line "{k} done steps hidden" stays in their place.
- **AC-10**: Typical parts and typical hours are no longer shown on the ticket. The known fix name stays, inside the open row as a link to `/knowledge-base/<entryId>` when the knowledge module is on (`knowledgeOn`) and as plain text when it is off, with its status badge when Draft or Inactive, with "Change" (relink, spec 0007) beside it as a quiet text button. The link picker and "Suggest a known fix" stay for an issue with none.

Page
- **AC-11**: The title is the plate chip, then the model when `vehicleModel` is set, then the first issue's text (cut to 1 line; left out when the ticket has no issues); the ticket ID and garage sit below in `muted-foreground`, the ID never breaking (`docs/context/vrms/design.md`, Naming a ticket).
- **AC-12**: Issue text never shows the stored `[System] ` prefix anywhere on the page (rows, title, dialogs such as Edit steps); the category shows once, from `categoryName`.
- **AC-13**: Photos are one line at the top of the Issues card: "Photos · {b} before · {a} after" with "Add photos". It opens to today's strip when the ticket has any photo, when the next move is blocked by a photo (`blockedBy`), or when tapped. The open state of the photos line moves up to the page so other parts can open it. While the file list loads the line shows "Photos" with no counts; on a load error it shows today's retry. Only the two photo reasons in the Status card (any wording `nextAction.ts` gives for `beforePhoto` or `afterPhoto`) become a link; costs, uploading and other reasons stay plain text. `ticketActions` passes `blockedBy` along with the text. The link scrolls to the photos line, opens it and focuses that group's Add button (it does not start the file picker, which browsers block after the click has passed).
- **AC-14**: AI diagnosis is a folded card right under the Issues card: closed it shows one line ("AI suggests {category}, {priority} priority", or "No AI diagnosis yet" with Run); open it shows today's section. The latest diagnosis is fetched by the card whether folded or not (folding never unmounts the fetch). Priority shows in sentence case ("High"). States: loading (a one line skeleton), error (one line with Retry), none, and the module off (no card). It stays per ticket.
- **AC-15**: Activity is open and shows the 5 newest entries (`limit: 5`); "Show all" fetches the first 50 and replaces the 5, then pages on with today's cursor. The 3 second refresh does not reload it. Without `audit.view` there is no Activity card, as today; with no entries it says "No activity yet".
- **AC-16**: Vehicle & driver moves into the sidebar Details card. Notes (`ticket.remarks`, and the cancellation reason when set, as `NotesSection` shows them today) become the first sidebar card, a 3 line preview (`line-clamp-3`) with "Show more" only when cut off; no card when both are empty.
- **AC-17**: Cancel ticket leaves the Status card's button stack and goes into a `⋮` More actions menu (`dropdown-menu`) beside the status badge, in `destructive` text, opening today's cancel dialog. No other action is added to the menu now, and the `⋮` button is not shown when the ticket has no cancel action.
- **AC-18**: Below 768px the page reads: a slim status line (badge, `⋮` menu, blocked reason), the Notes preview, Issues (photos line on top), AI, Costs, People, Details with vehicle, Activity. The primary action stays only in the fixed bottom bar, and the page keeps enough bottom padding that the bar never covers Activity. The chevron area and the `⋮` button are 44px targets on phones. From 1024px the sidebar returns to the right as today.

Look and quality
- **AC-19**: Built to `design.md` and `docs/context/vrms/design.md` with the work order look: hierarchy from size and weight, not boxes; no icon before a label; no box inside a box; no gradient or new shadow; colour only for status, progress state, overdue, safety, Returned and destructive actions; tabular figures for counts. Tokens only (lint enforces it).
- **AC-20**: The page and its states (loading skeleton as 3 folded rows, empty issues, error) pass axe at 375px and 1280px, every row and control works by keyboard, and folding never moves focus.

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
| Closed row | known fix name, status, Safety word | `issue.knowledgeEntry` (`name`, `status`, `safetyNotes` trimmed and not empty) from the ticket response |
| Closed row | progress {x} of {y} | `mergedSteps(issue, overrides)`: `issue.steps` with `checkedAt` plus `useTickOverrides` at list level |
| Closed row | state | derived (AC-3) from steps, `resolvedAt`, and `hasSavedResolution` in `lib/resolutionForm.ts` |
| Closed row | What fixed it, hours | `issue.resolutionNote`, else "Followed the known fix" when `issue.followedKnownFix`; `issue.hoursSpent` through `formatHours` |
| Closed row | Needs what fixed it | state Done, no saved resolution, ticket In progress |
| Page load | which rows open | AC-4 rule from `ticket.status`, issue count and each state, unless `sessionStorage` or `#issue-N` says otherwise |
| Summary line | {d} of {n} issues, {t} of {s} steps | the AC-3 states and step counts over `ticket.issues` |
| Photos line | {b} before, {a} after | `photoGroups(useTicketFiles().attachments, ticket.workStartedAt)` (spec 0018); no counts while loading |
| Photos line | opens on its own | any photo in the list, or the next move's `blockedBy` |
| Blocked link | which group to focus | the forward move's `blockedBy` (`beforePhoto` or `afterPhoto`), passed through `ticketActions` |
| Title | plate, model | `ticket.vehiclePlate`, `ticket.vehicleModel` (left out when unset) |
| Title | main issue | `ticket.issues[0]` (response order, `createdAt` then `id`), through `stripSystem` |
| Title | ID, garage | `ticket.repairNumber`, `ticket.garageLocation` |
| AI line | category, priority | the latest diagnosis' `predictedCategory`, `predictedPriority` (sentence case), fetched by the AI card |
| Notes card | text | `ticket.remarks`, and the cancellation reason when set |
| Activity | 5 newest | `getAuditEvents({ ticketId, limit: 5 })`; Show all refetches `limit: 50` and pages by cursor |
| Remembered view | open rows, Hide done steps per issue | `sessionStorage` key `vrms.ticket.<ticketId>.view`, `{ open: string[], hideDone: string[] }` |

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
- Blocked Send for verification: the reason link scrolls to Photos, opens it and the After picker. Verifies **AC-13**.
- 375px: status line, Notes, Issues before People and Details; the main button only in the bottom bar. Verifies **AC-18**.
- Unit tests (pure, Vitest): `issueState` for each state and the precedence, `stripSystem`, the open rule for each status and the 3 issue limit, the summary counts, the stored view merge (new and removed issues). Verifies **AC-3** to **AC-6**, **AC-12**.

## Build plan

Facade: the UI is the whole change, so each slice is a working page on real data, biggest value first.

1. **Pure rules**: `lib/issueRow.ts` with `stripSystem`, `mergedSteps`, `issueState`, `initialOpen` (AC-4) and `summaryCounts`, plus `useTicketView` (the `sessionStorage` state, its shape check and pruning, `#issue-N` once per hash) and `useTickOverrides` lifted from `IssueBlock`; Vitest tests; a backend test that ticket issues come ordered by `createdAt`, then `id`. Satisfies **AC-3** to **AC-6**, **AC-12**.
2. **Issue rows**: add the shadcn Accordion; rebuild `IssuesSection` as foldable rows with the closed row (AC-2, AC-3), the summary line with Expand all and Collapse all, and the open row order (safety line, checklist with dimmed done steps and Hide done steps, step actions with Edit steps, Edit issue and Remove issue, resolution); remove typical parts and hours and the known fix box; `stripSystem` in the Edit steps subtitle too. Satisfies **AC-1** to **AC-10**, **AC-12**.
3. **Page frame**: the title (plate chip, model, first issue; ID and garage below); Notes and Vehicle into the sidebar; the `⋮` menu with Cancel ticket; the phone order with the slim status line; the photos line and the blocked reason link; AI as a folded card; Activity with the 5 newest. Confirm nothing besides the removed line reads typical hours. Satisfies **AC-11**, **AC-13** to **AC-18**.
4. **Sweep**: the skeleton as folded rows, axe at 375px and 1280px with rows open and closed, keyboard pass, reduced motion, lint, typecheck, build, tests. Satisfies **AC-19**, **AC-20**.

## Consequences

**Positive**:
- A 10 issue ticket fits on one or two screens; the work in progress is open, the rest reads at a glance.
- The verifier signs off from closed rows without clicking.
- The page now follows its own design file (title, phone order, Cancel, no boxes per item).
- No backend change, so no migration risk and nothing for the other groups.

**Negative / tradeoffs**:
- One more tap to see a closed issue's steps.
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
- [ ] **`/sync`**: record in `welinc-web-vrms/AGENTS.md` that the issue state is derived only by `issueState` and that the ticket view lives in `sessionStorage`.
- [ ] **For the PM (Jira)**: "Ticket detail redesign: foldable issues with progress and state, no typical parts or hours on tickets, title and phone order fixes, Cancel in a menu" (feature 65).
