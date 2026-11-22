# Approvals history and fixes

Status: built. Open for review in `welinc-backend-bms` #58 and `welinc-web-bms` #23
(branch `BMS/approvals-history-and-fixes`, into `development`).

Three changes that came out of using the approvals and Daily Sales screens after
spec 0003. Touches only BMS-owned repos (`welinc-backend-bms`, `welinc-web-bms`).
No database migrations, and no change to shared auth, portal or the suite gateway.

## 1. Admin Approvals keeps a history

### Problem
CS and Operations send requests to Admin. As soon as Admin approves or rejects
one, it disappears from the Approvals page, so Admin can't look back at what was
decided, by whom, or why. The old "Approved" filter showed only approvals (no
rejections or withdrawals), with no "decided by" or "decided on", and it hid
approved cancellations because their booking is cancelled.

### What it does
- The page has two tabs, **Waiting** and **History**, in the same tab style as
  Activity Logs and Team Management, above the summary cards.
- **History** lists everything that left the Waiting list:
  - **Approved**: this includes Verified collections and Refunded refunds.
  - **Rejected**: Admin's reason shows on hover.
  - **Withdrawn**: taken back by CS or Operations.
- History columns: Booking / Client, Type, Details, **Decision, Decided by,
  Decided on**, and View. View opens the same review popup, read-only, with the
  full timeline.
- History filters: type, decision (Approved / Rejected / Withdrawn), and search.
- The **date filter** sits in the page header, like Activity Logs. It applies to
  both tabs: the date a request was sent (Waiting) or decided (History). It stays
  set when switching tabs or cards.
- History replaces the old "Approved" option in the type filter. Approved
  cancellations now appear.

### Backend
`GET /approvals` gains:

| Parameter | Meaning |
|---|---|
| `status=history` | Decided items from bookings, collections, refunds and crew leave, each with `decidedBy`, `decidedByName`, `decidedAt`, newest decision first |
| `decision=approved\|rejected\|withdrawn` | History only; Verified and Refunded count as approved |
| `from`, `to` (YYYY-MM-DD) | Decided date in History, sent date in Waiting (Manila time) |
| `overdue=true` | Waiting more than 24 hours |

Each service reports its own history: the booking service for reschedules and
cancellations, completion for collections and refunds, and dispatch for crew
leave. A withdrawn collection stores no "withdrawn by/at", so that is read from
its audit trail. `status=approved` still works for anything that uses it.

## 2. "Total waiting" becomes "Overdue"

"Total waiting" was the sum of the other four cards, so it said nothing new. It
is replaced by **Overdue (over 24 h)**: requests waiting longer than a day. The
card turns red when anything is overdue, matches the red "Overdue" marks in the
table, and opens the Waiting list filtered to overdue requests (with an "Overdue
only ✕" chip to clear it).

## 3. A refund closes the money

### Problem
Daily Sales treated refunded money as unpaid. Every partly refunded booking came
back as a "Method needed" row asking CS to record the refunded amount as a new
payment (seen with the demo refunds DEMO-BN-0137 to 0140, each showing ¼ of the
booking). The same would happen with a real refund.

### What it does
Collected money counts as paid even if part of it was later refunded. This holds
in the four places that work out what is still owed:

1. the Daily Sales "to collect" rows
2. which bookings count as not fully paid
3. recording a collection ("Booking is already fully paid")
4. verifying a collection

A genuinely unpaid or partly paid balance is still listed.

### Trade-off
If Admin verifies a payment with the wrong amount and it is refunded to correct
it, CS can't record the corrected payment against the same booking. Wrong amounts
are normally rejected before verification, and that path is unchanged. If this
comes up in practice, add a refund choice: **"Money returned to client"** (closes
the money, as now) or **"Correcting a wrong payment"** (reopens the balance).

## 4. The "Team assigned" email names the truck and crew

### Problem
The customer email sent when Operations assigns a booking only said "a truck and
crew have been assigned". It also opened with "Good news:", which reads as
unprofessional.

### What it does
- The email now shows a box with the **truck, driver, helpers and dispatch time**
  above the booking summary, in both the HTML and plain-text versions.
- Editing an assignment sends a new email with the new team.
- The "Good news:" opener is removed.
- The driver's phone number is **not** included. Add it if the business wants
  customers to have it.

### How
- **Dispatch** sends the team with `ConfirmAssignment`. It has to: Booking sends
  the email while the assignment is still `PENDING` in Dispatch, so Booking can't
  look the team up itself.
- **Booking** keeps only plain, short names (120 characters, at most 10 helpers).
  It leaves the team out of the duplicate-command hash, so a retry isn't rejected
  if a crew member's name was edited in between.
- If the details are missing, the email still goes out without the team box.

## Testing

- New tests: approvals history and Overdue (4), refund closes the balance (3),
  Team assigned email (5).
- Full suites pass: booking 93, completion 98, dispatch 104. The web app
  type-checks and lints clean.
- Checked against the local stack:
  - the refunded demo bookings are gone from CS Daily Sales (52 genuinely unpaid
    remain)
  - History returns 105 decided items with decider names
  - Overdue matches the overdue rows (28)
- The email change was not sent live, because the local SMTP sends real mail. It
  is covered by tests that render the actual email.

## Deploy notes

- No database migrations.
- Merge the backend PR (#58) before or together with the web PR (#23). The web
  History tab needs the new backend parameters.
- Merging into `development` triggers the staging deploy.
