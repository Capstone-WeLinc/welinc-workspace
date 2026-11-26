# Verify: Scheduling reschedule filter, single actions, Subcon assignments

Checklist derived from [index.md](index.md). Tick only what was actually checked.

## API / automated

- [x] Dispatch service test: a Subcon assignment checks only its helpers, rejects no helpers, and rejects a vehicle without a driver.
- [ ] `PUT /scheduling/:id/assign` with `deliveryType: "Subcon"`, dispatch time and helpers only succeeds and creates a job order with truck "Subcon".
- [ ] Same request for Inhouse without a vehicle or driver is still rejected.
- [ ] A Subcon helper already booked in the same slot is rejected.

## Database

- [ ] The Subcon assignment row has `garage`, `vehicle_id` and `driver_id` empty and the helpers filled in.

## Web (manual)

- [ ] Status filter lists All, Assigned, Unassigned, Needs reschedule.
- [ ] "Needs reschedule" shows only rows with that badge; "Unassigned" no longer shows them.
- [ ] An assignable unassigned row shows the Assign icon (no ⋮); clicking it opens the Assign form.
- [ ] A view-only user sees the eye icon (no ⋮); clicking it opens the details.
- [ ] Assigned and "Needs reschedule" rows still show the ⋮ menu with their actions.
- [ ] Choosing Subcon greys out Garage, Vehicle and Driver; they can't be clicked or typed in and show "Not needed for Subcon".
- [ ] Helper can still be picked and typed in, and Add Another Helper adds a field.
- [ ] Confirm assignment enables with dispatch time, Subcon and a helper, and saves.
- [ ] Switching back to Inhouse re-enables the three fields, empty.
- [ ] Customer "Team assigned" email for Subcon lists only helpers.

## Mobile

- [ ] Not affected (Subcon assignments have no driver, so they don't appear in any driver's jobs).

## Commands

- [x] Web: `lint`, `typecheck`, `test`, `build:prod` with the CI's `VITE_*` values pass locally.
- [x] Backend: `lint:ci`, `build`, `test` pass locally.
- [x] Three spec files present in this folder.
