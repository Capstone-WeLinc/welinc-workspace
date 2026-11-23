# Approvals table and side panel

Status: built and pushed. Branch `BMS/approvals-table-and-side-panel` in
`welinc-web-bms` (commit `c504f55`), into `development`. No pull request yet.

A redesign of the Admin **Approvals** page from a reference design: a cleaner
table, and a side panel instead of the review popup. The KPI cards also change
(section 4). Touches only `welinc-web-bms`. No backend change, no database
migrations, and no change to shared auth, portal or the suite gateway.

Unchanged on the page: the header and its date filter, the **Needs action /
History** tabs, the search box and the type filters, and the page numbers
under the table.

## 1. The table

File: `src/pages/admin/Approvals.tsx`

### What it does
- The search and filters and the table sit together in one rounded white card.
- A white header row with grey labels replaces the navy header.
- **Needs action** columns:

  | Column | Shows |
  |---|---|
  | (checkbox) | Ticked while that request is open in the side panel |
  | Request | Type icon, booking number, and client (or the leave dates for crew) |
  | Type | Coloured tag: Reschedule, Cancellation, Collection, Refund, Crew leave or Emergency |
  | Requester | Initials, name and role of whoever sent it |
  | Amount | In pesos, or "-" |
  | Due Date | When it becomes overdue (24 hours after it was sent), with "Due in 5h" (grey, or amber under 6 hours) or **Overdue** in red |
  | Status | The system-wide status badge (see below) |

- **History** shows **Decided** (the date and "by" who decided) instead of Due
  Date. The decision reason still shows when you hover over the status.
- The **status badge** is the same rounded, outlined, uppercase badge used
  across BMS (`StatusBadge` in `StandardTable`), with approval colours:
  - Pending (orange): this includes Requested and Verifying
  - Approved, Verified, Refunded, Confirmed (green)
  - Rejected, Cancelled, Withdrawn (red)
- BMS has no due dates on requests, so "Due" uses the existing overdue rule:
  24 hours after a request was sent. This is the same rule the old Overdue card
  used.

### Removed
- The Details, Waiting and Action (eye button) columns. Clicking anywhere on a
  row opens it now.

## 2. The side panel replaces the review popup

Files: `src/components/approvals/ApprovalPanel.tsx`,
`src/components/approvals/approvalUtils.ts`,
`src/components/approvals/ApprovalStatusBadge.tsx`

### How it opens
- Clicking a row, or its checkbox, opens that request in a panel to the right
  of the table. Clicking the same row again, or the X, closes it. Clicking
  another row switches to that one.
- **Wide screens (xl):** the panel sits beside the table and is as tall as the
  table, at least 560px. It **does not follow the page when you scroll**. Long
  content scrolls inside the panel.
- **Smaller screens:** the panel slides in over the page from the right, and
  tapping outside it closes it.
- Checkboxes open one request at a time. There is **no bulk approve**, because
  each rejection needs its own reason.

### What it shows, top to bottom
1. **Header:** the booking or employee number, the status badge (the same one
   as the table), and close.
2. **Summary card:**
   - The type icon and a title: what is being asked, or, for crew requests, the
     crew member's name, with "Driver" or "Helper" and the dates underneath.
     The amount sits on the right when there is one.
   - **Requester:** initials, name and role (shown as "Operations", not
     "OPERATIONS").
   - **Request type:** the same coloured tag as the table's Type column.
   - **Client** (not for crew requests), **Submitted**, and **Due** (pending
     only, with "Due in …" under the date) or **Decided** (with who decided).
   - Details for each type:
     - **Bookings:** service, booking date, pickup, delivery, and **Reason**
       (always shown for cancellations). Reschedules add the current versus
       requested table.
     - **Collections:** method, reference, recorded by.
     - **Refunds:** reason, original payment.
     - **Crew leave and emergencies:** employee ID, dates, duration, reason,
       the rejection reason if rejected, and trips affected.
   - **Decision note:** the rejection reason on decided non-crew requests.
3. **Audit Trail** (can be opened and closed): every recorded step, with when it
   happened and who did it. A pending request ends with "Pending your
   approval". It uses the `audit` list the approval detail endpoint already
   returns.
4. **Buttons** (pending only): a green **Approve** and a red **Reject**.
   - Collections say **Verify** and emergencies say **Confirm**.
   - A short line above the buttons says what approving does, as the popup
     did.
   - Reject asks for a reason first, then shows **Back / Confirm rejection**.

### Removed
- The review popup (`ApprovalReview`). Approve, reject, and the "find it in
  History" toasts work as before.
- The crew request's separate "Request" card, its second PENDING badge, its own
  status timeline, and the red "In effect now…" banner. The facts it showed are
  rows in the summary card now.
- **Comments:** tried, then removed, because it repeated the Reason row. BMS has
  no comment feature, so it only showed the reasons already listed.
- The "Emergency · Requested on …" line under the panel header. The request type
  and the submitted date are already in the summary card.

## 3. Unchanged elsewhere

`src/components/crewleave/CrewLeaveDetails.tsx` was given a "hide timeline"
option and then put back as it was. The panel no longer uses it. Other screens
that use it are unaffected.

## 4. KPI card: Pending replaces Overdue

Spec 0004 replaced "Total waiting" with **Overdue (over 24 h)**. This brings
back a total instead:

- **Pending** (orange clock, to match the Pending badge): every request still
  waiting for Admin (`/approvals/counts` `total`), which is the sum of the other
  four cards. Clicking it opens Needs action with no filter.
- The other four cards are unchanged: Reschedules & cancellations, Collections
  to verify, Refund requests, and Leave Request.
- **Trade-off:** there is no longer a one-click view of only the overdue
  requests. The table still marks them **Overdue** in red under Due Date. The
  `?overdue=true` link and its "Overdue only ✕" chip still work if opened
  directly. A Needs action dropdown (All / Overdue) was offered and declined.

## Testing

- The web app type-checks (`tsc -b`) and lints clean.
- No automated test covers the Approvals page, so none needed updating.
- Checked by the user in the browser while building, using the local stack
  (`localhost:8003`).
