# Verify: Crew details redesign and vehicle documents removal

Checklist derived from [index.md](index.md). Tick only what was actually checked.

## Investigation

- [x] VMMS `vehicles` table, fleet API mapping and web app: no registration, insurance or other document expiry field.
- [x] BMS schema (`vehicle_availability_sample_vehicles`, `vehicle_dispatch_profiles`, all models): no document column; nothing to drop.

## Web: Driver details

- [ ] Summary shows initials, name, "Driver · <license type>", status badge.
- [ ] Tiles: Assigned truck (plate or "None"), License (Valid green / Expiring soon amber / Expired red / Not recorded), Contact number.
- [ ] Sections: Contact details and License side by side; Emergency contact and Assigned truck side by side; one column on a phone.
- [ ] Assigned truck matches the plate on the driver's card; "No truck assigned" when free.
- [ ] License section: Expiry shows only the date (e.g. "Jun 18, 2028"), no badge; "Not recorded" when empty.
- [ ] On Leave driver: leave notice with the end date appears under the summary.

## Web: Helper details

- [ ] Tiles: Assigned truck, Contact number, Email.
- [ ] Sections: Contact details and Emergency contact side by side; Assigned truck across the width.
- [ ] On Leave helper: leave notice appears.

## Web: Vehicle details

- [ ] No Documents section; Vehicle information, Assigned crew, Current assignment / Status details and Upcoming schedule unchanged.

## Database

- [x] No migration needed (no column ever held registration or insurance expiry).

## Commands

- [x] Web `lint`, `typecheck`, `test`, `build:prod` with the CI's `VITE_*` values pass locally.
- [x] Backend `lint:ci`, `typecheck`, `build`, `test` pass locally.
- [x] The three spec files are present in this folder.
