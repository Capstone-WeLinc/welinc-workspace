# Approvals: History details modal, matching Needs action side panel, plain Request and Requester

Status: pushed, not yet in a pull request. Branch `BMS/approvals-history-view-action` in
`welinc-web-bms`, into `development`.

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

Changes the Admin **Approvals** table. Touches only `welinc-web-bms`. No
backend, database, shared auth, portal, gateway or mobile change.

## Problem

- On the **History** tab, each row started with a checkbox. Ticking it opened the request in the
  side panel, but a checkbox reads as "select this row" (for a bulk action), and History has no
  bulk actions. It wasn't clear that it was the way to see a decided request's details.
- History requests are already decided, so there is nothing to act on beside the table. The team
  wants them to open in a modal, styled like the other One UI view modals, instead of the side
  panel.
- On both tabs, the **Request** column had a coloured request-type icon beside the booking number,
  and the **Requester** column had a coloured initials circle beside the name. The team wants
  those cells to show text only.

## What it does

Files: `src/pages/admin/Approvals.tsx`, `src/components/approvals/ApprovalDetailsModal.tsx` (new),
`src/components/approvals/ApprovalDetailCards.tsx` (new), `src/components/approvals/ApprovalPanel.tsx`,
`src/components/approvals/approvalUtils.ts`

### History tab

- The checkbox column is gone.
- A new last column, **Action**, comes after **Status**. Each row has a **View** icon (eye),
  styled like the View icon on Services Offered.
- Only the View icon opens the request, in the **Approval details** modal. Clicking anywhere
  else on a History row does nothing (no pointer cursor). History no longer uses the side panel.

### Approval details modal (One UI)

Built like Booking details:

- **Header:** the One UI navy bar with the gold icon tile, the title **Approval details**, the
  booking or request number in gold under it, the status badge, and the gold close button.
- **Body** (light blue-grey, scrolls inside the modal): white cards with the One UI section title
  (gold bar, navy uppercase text), each a list of label-on-the-left, value-on-the-right rows. Each
  fact appears once:
  1. **Request Details**: first a **Request type** row (Reschedule, Cancellation, Collection,
     Refund, Crew leave or Emergency), the only place the type is shown, then what was asked:
     - **Reschedule**: each changed field as one row, old value → new value (for example
       "Date: Nov 21, 2026 → Nov 26, 2026", the old value grey, a gold arrow, the new value navy),
       then the reason if one was given. This replaces the Field / Current / Requested table.
     - **Cancellation**: the reason.
     - **Collection**: client, amount, method, reference.
     - **Refund**: client, amount, reason, original payment.
     - **Crew leave** or **Emergency**: crew type (Driver or Helper), dates, duration, reason, and
       the trips affected (approved leave only). The crew member's name is the header's reference
       line, so it isn't repeated.
  2. **Booking Details** (reschedules and cancellations only): client, service, pickup, delivery, amount.
  3. **Timeline**: who did what, and when: each recorded step with its date, the person and their
     role (navy dot; gold for the decision). When no steps were recorded it shows the submission
     and the decision. The decision note, if any, sits under the steps.
- **Footer:** a **Close** button.
- **Not repeated:** the status (only in the header badge), the request's one-line summary and type
  tag (the Request type row says it), the submitted and decided dates and people (only in the
  Timeline), and a collection's "Recorded by" (the Timeline's submitter).
- It's read only: no Approve or Reject buttons. Like Booking details, it closes only from the
  close button or **Close**, not from Escape or a click outside.

### Needs action tab: side panel

The checkbox column stays and still opens the side panel. The panel keeps its own containers
(white header, a bordered first box, collapsible sections), but what's inside them looks and is
ordered exactly like the History modal: the same section titles, rows, change row and Timeline.

- **Header (as before):** the booking or request number and the status badge, with a close (×)
  button.
- **Section titles** (Request Details, Booking Details, Timeline) use the modal's One UI title: a
  gold bar, then small navy uppercase text.
- **Rows** use the modal's layout and fonts: label on the left (grey), value on the right (dark,
  medium weight), the same column split and spacing.
- **Request Details** (a bordered box, as the panel's first section was before): Request type,
  then what was asked. A reschedule shows each changed field as old → new, as in the modal (old
  grey, gold arrow, new navy).
- **Booking Details** (reschedules and cancellations only), a collapsible section like the old
  Audit Trail: client, service, pickup, delivery, amount.
- **Timeline**, a collapsible section styled like the modal's (navy dots, gold for the decision,
  a hollow gold dot for the open step; no step count): each step with its date, the person and
  their role, ending with **Waiting for your approval** and its due date and Due in / Overdue by.
  This replaces the separate Submitted and Due rows.
- **Reject:** the Reason for rejection box appears under the sections, as before.
- **Buttons** follow the system's standard footer buttons (as in Services Offered and Edit crew):
  right-aligned, 40px tall, no icons. **Reject** is the white outlined secondary button and
  **Approve** (Verify / Confirm) the navy primary button. While rejecting: **Back** (secondary)
  and **Confirm rejection** (red, same shape).
- **Note above the buttons:** the reschedule note ("Approving applies the requested change.
  Rescheduling releases the current assignment and returns the booking to plotting.") is removed.
  The notes for collections, refunds and cancellations stay.

Removed from the side panel because it repeated something:

| Removed | Still shown in |
|---|---|
| Summary at the top of the first box (title, subtitle, amount) | Request Details, Booking Details |
| Requester row with initials circle | Timeline (submitter, role) |
| Request type tag | Request Details' Request type row |
| Submitted row | Timeline |
| Due row | Timeline's waiting step |
| Booking date row | Request Details' change row (old → new) |
| Field / Current / Requested table | Request Details' change row |
| Collection "Recorded by" | Timeline |
| Crew member row, crew "Rejected" row | Header; Timeline's decision note |

### Both tabs

- **Request** shows only the booking number and, under it, the client (or the crew request's short
  details). The request-type icon beside it is gone. The **Type** column's coloured tag still tells
  the request types apart.
- **Requester** shows only the name and, under it, the role. The initials circle is gone.
- Switching tabs now closes any open request. Before, a request left open on Needs action stayed
  open after switching to History.

### Code

- The sections live in `ApprovalDetailCards.tsx`, used by both the modal (`variant="card"`, One UI
  cards) and the side panel (`variant="panel"`, the panel's own containers). Only the containers
  differ; titles, rows and the Timeline are the same code, so the two always look alike inside. The helpers they use (`text`, `titleCase`,
  `record`, `leaveDate`, `leaveDays`) moved to `approvalUtils.ts`. `initials` and `avatarTone`
  were removed; nothing uses them any more.

## Removed

- The checkbox column on the History tab.
- The side panel on the History tab (the modal replaces it).
- The side panel's old layout and its repeated rows (see the table above).
- The request-type icon in the Request column and the initials circle in the Requester column,
  on both tabs.

## Testing

- `welinc-web-bms`: the full CI sequence passes locally (`npm audit --omit=dev --audit-level=high`,
  `lint`, `typecheck`, `test`, `build:prod` with the CI's `VITE_*` values). Lint has no errors; its
  30 warnings are all in files this change doesn't touch and are on `development` already. Unit
  tests pass (20).
- The running dev server (restarted) serves the new files.
- Not yet checked by hand in the running app.

## Deploy notes

- Web only; deploy `welinc-web-bms`. Nothing else changes.
