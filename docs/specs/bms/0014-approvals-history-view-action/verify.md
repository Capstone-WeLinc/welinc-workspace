# Verify: Approvals History details modal and plain Request/Requester · spec 0014

Steps derived from [index.md](index.md). Ticked items were checked on 2026-11-25.

## Commands

- [x] `welinc-web-bms`: typecheck clean
- [x] `npx eslint src/pages/admin/Approvals.tsx src/components/approvals/`: no errors or warnings
- [x] `npm test`: 20 pass (after the side panel change too)
- [x] Full web CI sequence (`npm audit`, `lint`, `typecheck`, `test`, `build:prod` with the CI's
  `VITE_*` values) passes locally

## Web / manual (Admin → Approvals)

- [ ] History tab: no checkbox column; the last column is **Action**, after **Status**
- [ ] Each History row has a View (eye) icon; clicking it opens the Approval details modal, not
  the side panel
- [ ] Clicking elsewhere on a History row does nothing, and the row shows no pointer cursor
- [ ] Needs action rows still open the side panel when clicked anywhere
- [ ] Modal header: navy bar, gold icon tile, "Approval details", the booking/request number in
  gold, the status badge, gold close button
- [ ] Modal body, top to bottom: Request Details (its first row is Request type, e.g.
  "Reschedule"), Booking Details (reschedules and cancellations only), Timeline, with the gold-bar
  section titles; no separate request type strip
- [ ] A rescheduled booking shows "Date  Nov 21, 2026 → Nov 26, 2026" as one row, no table
  (checked in the local database: that reschedule's saved values are 2026-11-21 → 2026-11-26)
- [ ] Nothing shows twice: status only in the header, no type row or summary line, submitted and
  decided only in the Timeline, no crew name row, no collection "Recorded by"
- [ ] Timeline shows each step with date, person and role; a rejected request shows its decision
  note under the steps
- [ ] A crew leave shows crew type, dates, duration and reason; approved leave also shows trips
  affected
- [ ] The modal has no Approve or Reject buttons; Close and the close button close it; Escape and
  a click outside don't
- [ ] A long request scrolls inside the modal on a small screen
- [ ] Open a request on Needs action, switch to History: no modal opens
- [ ] Empty and loading states span the full width of the table on History
- [ ] Needs action tab: checkbox column still there; ticking it opens the side panel
- [ ] Side panel keeps its own look: plain white header with the number and status badge, a
  bordered Request Details box, then collapsible Booking Details and Timeline sections
- [ ] Side panel sections are in the same order as the History modal, with the same facts
- [ ] Each side panel section title has the gold bar and the modal's small navy uppercase text
- [ ] Side panel rows, the old → new row and the Timeline look the same as in the History modal
  (fonts, colours, spacing); the Timeline has no step count
- [ ] Timeline ends with "Waiting for your approval" showing the due date and Due in / Overdue by
- [ ] None of the removed rows appear: summary, Requester with initials, type tag, Submitted, Due,
  Booking date, the Field / Current / Requested table, Recorded by
- [ ] Buttons: right-aligned, Reject (white outlined) then Approve / Verify / Confirm (navy), same
  size as the Services Offered form buttons, no icons
- [ ] Reject shows the reason box; Back (outlined) and Confirm rejection (red); an empty reason
  shows the error; deciding works as before
- [ ] A reschedule shows no note above the buttons; a cancellation, collection or refund still does
- [ ] Below xl the panel still slides over the page; tapping outside closes it
- [ ] Both tabs: Request shows only the booking number and the line under it, no icon
- [ ] Both tabs: Requester shows only the name and role, no initials circle
