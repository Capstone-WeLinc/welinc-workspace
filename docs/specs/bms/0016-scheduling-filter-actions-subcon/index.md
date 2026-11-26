# Scheduling: reschedule filter, single actions, Subcon assignments

Status: pushed, not yet in a pull request. Web branch: `BMS/scheduling-filter-actions-subcon` (into `development`); backend branch: `BMS/scheduling-filter-actions-subcon` (into `development`); workspace branch: `docs/bms-scheduling-filter-actions-subcon` (into `main`).

Decision history: [rationale.md](rationale.md). Review checklist: [verify.md](verify.md).

Touches only the Scheduling page in `welinc-web-bms` and the assignment rules in `welinc-backend-bms/bms-dispatch-service`.

## 1. "Needs reschedule" status filter

**Problem:** the table shows a red "Needs reschedule" badge, but the status filter only offers All, Assigned and Unassigned, so there was no way to list just those bookings.

**What it does:**

- The status filter now has **All**, **Assigned**, **Unassigned** and **Needs reschedule**.
- "Needs reschedule" uses the same rule as the badge: an unassigned booking whose service date, or today's pickup time, has passed.
- "Unassigned" now lists only unassigned bookings that can still be assigned. A row shows under one filter, matching its badge.
- The KPI cards are unchanged ("Unassigned Bookings" still counts every unassigned booking).

## 2. One action, no ellipsis

**Problem:** every row opened a ⋮ menu, even when the menu held a single action.

**What it does:**

- If a row has only one action, the Actions column shows that action's icon as a button, with a tooltip and screen-reader label:
  - View only (users who can't assign): the eye icon.
  - Unassigned and still assignable: the Assign icon.
- Rows with two or more actions keep the ⋮ menu: assigned rows (View, Edit) and "Needs reschedule" rows (View, disabled Assign/Edit and the reason note).

## 3. Subcon assignments need no garage, vehicle or driver

**Problem:** a subcontractor brings their own truck and driver, but the Assign form and the backend required our garage, vehicle and driver for every booking.

**What it does (web):**

- Choosing **Subcon** as the delivery type disables Garage, Vehicle and Driver: they are greyed out and can't be clicked or typed in. Their placeholders read "Not needed for Subcon", and any values already picked are cleared.
- **Helper** is unchanged: it can still be picked or typed, and **Add Another Helper** still works. At least one helper is required.
- Confirm assignment only needs dispatch time, delivery type and helpers for Subcon. The request leaves out garage, vehicle and driver.
- Switching back to Inhouse enables the three fields again, empty.

**What it does (backend, dispatch service):**

- A Subcon assignment is accepted with only dispatch time, delivery type and at least one helper. Garage, vehicle and driver are stored as empty (the columns were already nullable; no migration).
- Helpers still get every check: they must hold the Helper role, be Available or On Duty, not be on leave, not be double-booked in the same slot, and pass the travel-time check.
- The job order for a Subcon assignment shows truck "Subcon" and the helpers' names as the team.
- Job orders, distribution, the assigned-bookings list and post-service accept a Subcon assignment without a driver. Inhouse still needs a driver as before.
- Customer email: "Team assigned" lists only the helpers (no truck or driver rows). Tracking shows "Subcontractor" for the driver and "Subcontractor truck" for the vehicle.

**Not changed:** a permit booking that is already assigned keeps its truck, driver and helpers locked. Switching it to Subcon would drop the locked truck and driver, so the backend refuses it with the existing permit message.

## Removed

- The ⋮ menu on rows that have a single action.

## Testing

- `welinc-web-bms`: `lint` (0 errors; 30 warnings, all already on `development` in other files), `typecheck`, `test` (20 pass) and `build:prod` with the CI's `VITE_*` values all pass locally.
- `welinc-backend-bms`: `lint:ci`, `build` and `test` pass locally. New test: a Subcon assignment checks only its helpers (dispatch service, 39 pass).
- Not yet checked by hand in the running app.

## Deploy notes

- Deploy `welinc-backend-bms` (dispatch service) before or with `welinc-web-bms`: the web sends Subcon assignments without a vehicle or driver, which the old backend rejects.
- No database migration.
