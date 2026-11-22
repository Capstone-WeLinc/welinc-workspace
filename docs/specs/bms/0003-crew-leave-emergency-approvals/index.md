# Crew leave and emergency approvals

Status: built and merged into `development` (`welinc-backend-bms` #57, `welinc-web-bms` #22).
Follow-up changes are in spec 0004.

Drivers and helpers have no BMS screen yet; their roles are meant for the future
BMS mobile app. Until then, **Operations files leave and emergency requests on the
crew member's behalf**, and **Admin decides them on the existing Approvals page**.
When the mobile app exists, crew file the same request themselves and the approval
step does not change.

Touches only BMS-owned repos (`welinc-backend-bms`, `welinc-web-bms`). No change to
shared auth, portal or the suite gateway.

## The rules

| | Leave (planned) | Emergency (happening now) |
|---|---|---|
| Who files | Operations | Operations |
| Takes effect | Only after Admin **approves** | **Immediately** when filed |
| Admin action | Approve or reject | Confirm or reject (after the fact) |
| If rejected | Crew stays Available | Crew goes back to Available |
| Dates | Start today or later | Starts today |

Common to both:

- A reason is required (up to 500 characters). Rejecting needs a reason too.
- End date is on or after start date, at most 30 days.
- One active (waiting or approved) request per person for overlapping dates.
- Only active crew members can have a request filed.
- Operations can **withdraw** a request while it is still waiting. Withdrawing an
  emergency ends it right away.
- The person who filed a request can't decide it.
- Every step is kept in the request's history (filed, approved/confirmed,
  rejected, withdrawn), like refunds.

### What "on leave" does

A crew member counts as **On Leave** for a date when an approved leave covers it,
or when an emergency that is still waiting or confirmed covers it. This is worked
out from the requests, not written over the crew member's manual status, so it
switches off by itself when the dates pass or a request is rejected or withdrawn.

- **Crew lists and availability pages** show *On Leave* for those dates.
- **Trips already assigned** to that person in those dates show a
  **"Crew unavailable – reassign"** warning for Operations. The approval is
  **not** blocked by these trips, and the warning clears when the trip is
  reassigned.
- **New trips can't be assigned** to that person on those dates. This applies to
  drivers and helpers alike. Today the assignment check only looks at the
  driver's manual status and doesn't check helper status at all, so this closes
  that gap too. Once the request is withdrawn or rejected, or the dates have
  passed, the person can be assigned again.
- **Operations is notified** through the notification bell when Admin approves,
  confirms or rejects a request they filed.

## Backend changes

### bms-dispatch-service (owns crew, so it owns the requests)

1. **New table `crew_leave_requests`** (Prisma model + migration): id, crew type
   (driver/helper), crew id, kind (leave/emergency), start date, end date, reason,
   status (`Requested`, `Approved`, `Rejected`, `Withdrawn`), filed by, filed at,
   decided by, decided at, decision reason. Plus a small history table for the
   audit steps.
2. **Operations endpoints** (role `OPERATIONS`, Admin can read):
   - `POST /crew-leave` file a request
   - `GET /crew-leave/mine` requests I filed
   - `POST /crew-leave/:id/withdraw`
   - `GET /crew-leave/conflicts` assigned trips affected by leave (for the warning)
3. **Internal endpoints for the Approvals page** (service key, same pattern as the
   completion service): list waiting, list decided, detail, approve/confirm,
   reject.
4. **On-leave logic** used by the crew lists, the availability pages and the
   assignment check. The check covers the driver and every helper against the
   trip's service date.
5. Activity-log labels for the new routes.

### bms-booking-service (runs the Approvals page)

Add a third source, **`crew`**, next to bookings and payments/refunds: include it
in the waiting list, the approved list, the counts, the detail view and the
approve/reject routing.

### bms-gateway (BMS's own gateway)

Route `/crew-leave` to the dispatch service.

## Web changes (welinc-web-bms)

- **Operations → For Approvals:** same layout and styling as the CS For Approvals
  page, but only for crew leave and emergencies. Pending / Approved / Rejected
  cards, search and status filter, a table of requests they filed, and a detail
  view with the status timeline, affected trips and **Withdraw request**. A **File
  leave / emergency** button opens the form (pick the person, Leave or Emergency,
  dates, reason). Trips that still have someone on leave are listed in a *"Crew
  unavailable – reassign"* box above the table and tagged on Scheduling.
- **Admin → Approvals:** a **Crew** filter and count. The row shows the person,
  kind, dates and reason. Emergencies get a red **EMERGENCY – already in effect**
  tag and the buttons read **Confirm / Reject**; leave reads **Approve / Reject**.
  The detail view lists any trips affected.
- **Crew pages:** show *On Leave* when a request covers today.
- **Scheduling:** people on leave for the trip's date are greyed out in the
  driver/helper pickers, with the reason "On leave until <date>".
- **Notification bell (Operations):** "Leave for <name> approved / rejected:
  <reason>", which links to the request.

## Later: the mobile app

Add `POST /crew-leave/self` and `GET /crew-leave/self` for the `DRIVER` and
`HELPER` roles. The crew member is matched through the existing link between
their login and their crew record. Requests land in the same Approvals queue with
the same rules. The shared login already supports mobile sign-in for these roles.

## Testing

- Automated tests for every rule above, in the style of the refund tests.
- A live check on the running stack using the seed accounts (Operations files,
  Admin decides), followed by removal of the test data.

## Not included

The mobile app itself, push/SMS notifications to crew, leave balances or payroll,
and automatic reassignment of trips.

## Decisions

1. **Maximum length is 30 days.** Longer leave is filed as a second request.
   Change this if the company has a set leave policy.
2. **Operations is notified** (the bell) when Admin decides.
3. **New assignments are blocked** while someone is on leave, for drivers and
   helpers, starting with this change.
