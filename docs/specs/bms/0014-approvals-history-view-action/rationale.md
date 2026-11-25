# 0014. Approvals table: View icon on History, no icons beside Request and Requester: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

Spec 0007 gave the Approvals table a checkbox in front of each row that opens the request in the
side panel. On the History tab, where requests are already decided, the team asked to replace
that checkbox with a **View** icon in an **Action** column after **Status**, so opening a row's
details is an explicit action.

## Options considered

### Option 1: Keep the checkbox

**Pros**:
- No change.

**Cons**:
- A checkbox suggests selecting rows for a bulk action, which History doesn't have.

### Option 2: Replace it with a View icon in an Action column, on History only (chosen)

**Pros**:
- Matches the other BMS tables (Services Offered, Bookings, Sales Report), which put View in
  an action column at the end of the row.
- Opens the same side panel, so nothing about the details changes.

**Cons**:
- The two tabs of the same table now look slightly different (checkbox on Needs action, View icon
  on History).

### Option 3: Do the same on Needs action

**Pros**:
- Both tabs would look the same.

**Cons**:
- Not asked for; Needs action is where requests are approved or rejected, and the request was
  only for History.

## Rationale

Option 2 does what was asked, on the tab it was asked for, and reuses the side panel and the
View icon style already used elsewhere. Row click is kept so nothing that worked before stops
working. Needs action can follow later with the same change if the team wants both tabs to match.

## Follow-up: icons beside Request and Requester

The team then asked to remove the icons beside the text in the **Request** and **Requester**
columns.

- **Both tabs, not only History.** The two tabs share the same row layout, and the request didn't
  name a tab. Removing them on one tab only would make the same columns look different between
  tabs for no reason.
- **Table only, not the side panel.** The request was about the table columns. The panel keeps its
  icon and initials as its header.
- **Nothing is lost.** The request type is still shown by the Type column's coloured tag, and the
  requester's name and role are still there as text.

## Follow-up: a modal instead of the side panel, on History

The team then asked for the View icon to open a modal instead of the side panel, following the One
UI styling and layout.

### Options considered

**Option A: Reuse the side panel's content inside a plain modal.** Quick, but the panel's layout
(plain header, rows without section cards, collapsible audit trail) doesn't match the One UI view
modals, which was the point of the request.

**Option B: A new One UI modal, built like Booking details (chosen).** The shared `ModalHeader`
(navy bar, gold icon tile, gold reference number, status badge, gold close), the light blue-grey
body with titled white cards, label/value rows, and a Close footer. The per-type facts come from the
same `TypeDetails` the side panel uses, so the two never show different details.

### Decisions

- **History only.** History requests are decided, so the modal is read only. Needs action keeps
  the side panel, where Admin approves or rejects while still seeing the list.
- **The whole row opened the modal too** at first, as clicking the row did before. The team then
  asked for only the View icon to open it (see the last follow-up).
- **Closes like Booking details**: only from the close button or Close, not Escape or a click
  outside, to match the other One UI view modals.
- **Header icon**: the Approvals page icon (clipboard check), as Booking details uses its own
  page's icon.
- **Switching tabs closes the open request.** Without this, a request left open on Needs action
  would pop up as a modal after switching to History.
- **Shared helpers moved to `approvalUtils.ts`.** Exporting them from the panel's component file
  made the linter warn that hot reload would stop working for that file.

## Follow-up: no repeated facts, and no table in the modal

The team then asked to remove anything shown twice in Approval details, to drop the Field /
Current / Requested table's look, and to rearrange the modal.

What was shown twice, and where it now lives once:

| Fact | Was in | Now only in |
|---|---|---|
| Status | Header badge, Decision card | Header badge |
| Request type | Type tag, the type card's title, the one-line summary | The type card's title |
| What changed (reschedule) | The summary ("Reschedule to ..."), the table | The change row |
| Submitted (when, who) | Requester card, Audit Trail | Timeline |
| Decided (when, who) | Decision card, Audit Trail | Timeline |
| Crew member's name | Header reference line, Crew member row | Header reference line |
| Who recorded a collection | Recorded by, Requester | Timeline |

### Decisions

- **The change as a row, not a table.** A reschedule usually changes one field (the date), so a
  three-column table was mostly header. "Date: old → new" reads in one line and uses the same
  label/value rows as every other card. Dates show as "Nov 21, 2026", like the rest of the modal.
- **Request first, then the booking, then the Timeline.** What was asked is what Admin opens it
  for; the booking is context; the Timeline answers who and when.
- **One Timeline instead of Requester, Decision and Audit Trail.** All three told who did what and
  when. The Timeline keeps each person's role, which was the only fact the Requester card added.
  When the backend recorded no steps, the Timeline still shows the submission and the decision
  from the request itself.
- **The modal has its own layout; the side panel keeps its own.** Sharing the per-type rows would
  have forced the side panel (Needs action) to change too, which wasn't asked for.

## Follow-up: request type at the top, "Booking Details"

The team asked to call the booking card **Booking Details** and to state the request type at the
top of the modal.

- The type first sat in its own strip above the cards. The team preferred no extra block, so it
  is now the first row of **Request Details** ("Request type: Reschedule"), still the first fact
  Admin reads.
- To keep each fact shown once, the first card is called **Request Details** for every type,
  instead of being named for the type.

## Follow-up: the Needs action side panel matches the modal

The team asked for the side panel (opened from the checkbox on Needs action) to look like the
Approval details modal, and to drop anything it showed twice.

### Options considered

**Option A: Restyle the panel's own code to look like the modal.** Two copies of the same layout
would drift apart the next time either is changed.

**Option B: Share the cards (chosen).** The modal's Request Details, Booking Details and Timeline
cards moved to `ApprovalDetailCards.tsx`, and both the modal and the panel render them. The panel
keeps only what the modal doesn't need: Approve / Reject and the rejection reason.

### Decisions

- **Panel stays a panel.** Needs action still opens beside the table, so Admin can work down the
  list while deciding; only its look changed.
- **Due date moves into the Timeline** as the open "Waiting for your approval" step, rather than a
  separate row, so who/when facts all sit in one place.
- **No status badge in the panel header.** Every request on Needs action is pending; the badge
  would repeat the table's Status column. The modal keeps its badge because History mixes
  Approved, Rejected and Withdrawn.
- **The approve/reject note and buttons are unchanged**, so deciding works exactly as before.

## Follow-up: the side panel keeps its own look

After seeing the One UI side panel, the team asked to bring back the panel's original design and
only rearrange its contents like the modal; to make Approve and Reject look like the system's
other buttons; and to drop the reschedule note above the buttons.

- **One set of sections, two looks.** `ApprovalDetailCards` takes a `variant`: `card` (One UI cards,
  for the modal) or `panel` (the panel's bordered first box, collapsible sections and smaller rows).
  The order and the facts stay shared, so removing a repeated fact in one removes it in both.
- **Buttons.** The system's forms (Services Offered, Edit crew) use right-aligned 40px buttons with
  no icons: a white outlined secondary button and a navy primary one. Reject is the secondary
  action and Approve the primary, so Reject sits on the left. Confirm rejection uses red in the
  same shape, as Confirm Delete does.
- **Reschedule note removed.** Only that note was asked to go; the notes for collections, refunds
  and cancellations stay, since they say what deciding will do to money or the booking.
- The earlier One UI panel (navy header, cards) is replaced by this.
- The team then asked for the gold bar before each section title in the panel, the one detail
  of the One UI cards brought into the panel's own look.
- The team then asked for the panel to use the modal's fonts and layout too. The panel keeps its
  containers (header, bordered box, collapsible sections); the titles, rows, change row and
  Timeline inside are now the modal's, with no panel-only styling left except the containers.

## Follow-up: History rows open only from the View icon

The team asked that clicking a History row no longer open Approval details; only the View icon
should. The row click and its pointer cursor are now Needs action only, where clicking a row still
opens the side panel. With the row not clickable, the View icon's cell no longer needs to stop the
click from reaching the row.
