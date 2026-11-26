# Crew details redesign and vehicle documents removal

Status: pushed, not yet in a pull request. Web branch: `BMS/crew-details-redesign-and-vehicle-documents` (into `development`); backend branch: `BMS/crew-details-redesign-and-vehicle-documents` (into `development`); workspace branch: `docs/bms-crew-details-redesign-and-vehicle-documents` (into `main`).

Decision history: [rationale.md](rationale.md). Review checklist: [verify.md](verify.md).

Touches `welinc-web-bms` (Vehicle & Team Availability details modals and the shared vehicle type) and one unused type field in `welinc-backend-bms/bms-dispatch-service`. No API behaviour, database or migration changes.

## 1. Driver and helper details redesigned

**Problem:** after the join date was removed (spec bms/0017), the driver modal had a single "License type" tile that repeated the License section, the helper modal was almost empty, and neither showed the truck the person is on, though the card does.

**What it does:** both modals follow the Vehicle details layout, 760px wide:

- **Summary card:** initials, name, role line ("Driver · Professional", "Helper"), status badge, and three tiles:
  - Driver: **Assigned truck** (plate or "None"), **License** (Valid in green, Expiring soon in amber, Expired in red, or "Not recorded"), **Contact number**.
  - Helper: **Assigned truck**, **Contact number**, **Email**.
- **Leave notice** (when On Leave): unchanged wording, now with a calendar icon, under the summary.
- **Sections in two columns** on wider screens, one column on phones:
  - Driver: Contact details (number, email, address) | License (no., type, expiry date); Emergency contact | Assigned truck (plate, model, garage).
  - The License section's **Expiry** row shows only the date, with no Valid / Expiring soon / Expired badge beside it: that status is already the coloured **License** tile in the summary.
  - Helper: Contact details (number, email) | Emergency contact; Assigned truck across both columns.
- "Assigned truck" uses the same vehicle list as the cards, so the modal and the card always agree. With no truck it says "No truck assigned".

## 2. Vehicle details: Documents removed

**Problem:** the Vehicle details modal had a Documents box with Registration expiry and Insurance expiry that could only ever say "Not recorded".

**Checked first:**

- **VMMS has no vehicle documents.** Its `vehicles` table (plate, make, model, year, engine type, size, capacity, status, odometer, maintenance defaults, garage) has no registration, insurance or other expiry field; its fleet API doesn't send any, and the VMMS web app has none. ("Registration" in VMMS code means adding a vehicle to the system.)
- **BMS doesn't store them either.** No BMS table or column holds them (`vehicle_availability_sample_vehicles` and `vehicle_dispatch_profiles` included). The dispatch service never filled them; only an optional `regExpiry` / `insExpiry` on its vehicle type mentioned them.

**What it does:**

- Removes the Documents section (title, Registration expiry and Insurance expiry rows) from Vehicle details. The rest of the modal is unchanged.
- Removes `regExpiry` / `insExpiry` from the web `Vehicle` type and from the Availability and Scheduling vehicle mappings, and from the dispatch service's `VehicleRecord` type.
- **Database:** nothing to drop: no column ever held these values.

## Removed

- The Documents section of Vehicle details.
- `regExpiry` and `insExpiry` from the web `Vehicle` type, the two vehicle mappings and the dispatch `VehicleRecord` type.
- The driver modal's lone "License type" tile (license type is now in the role line and the License section).
- The status badge beside the license expiry date, and the `VehicleExpiryRow` component that drew it (its only use left was this row).

## Testing

- `welinc-web-bms`: `lint` (0 errors; 30 warnings, all already on `development` in other files), `typecheck`, `test` (18 vitest + 20 node pass) and `build:prod` with the CI's `VITE_*` values pass locally.
- `welinc-backend-bms`: `lint:ci`, `typecheck`, `build` and `test` (dispatch 39 pass) pass locally.
- Not yet checked by hand in the running app.

## Deploy notes

- Deploy `welinc-web-bms`; the backend change is a type only, so its deploy order doesn't matter. No migration.
