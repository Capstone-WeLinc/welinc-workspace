# 0016. Rationale: new repair ticket and assignment

Back to [index.md](index.md).

## Context

Every repair starts at `POST /repairs` (WL-201, confirmed by the stakeholder). The code that runs it today has real gaps:

- **Not atomic.** It upserts the driver and sets the truck to `UNDER_REPAIR` before the ticket insert, outside any transaction. A failed insert leaves a truck marked Under repair with no ticket, and an orphan driver row.
- **Two open tickets per truck.** The form only warns, the server allows it, and two creates racing for one truck both succeed.
- **No Open tickets.** A mechanic is required, so a ticket can't start Open, and move M1 (Open to Assigned, spec 0014) has no trigger.
- **Data thrown away.** Account type, corporation and `issueDescription` are validated, then discarded (spec 0005 rationale, spec 0010 follow up).
- **Name matched drivers.** A driver is matched by a slug of their name stored as `licenseNumber`, so two people with the same name merge, while the BRD wants the license as the unique key (VR-RL-06).
- **No workload in the picker.** It shows a yes or no availability flag, while WL-201 asks for each mechanic's open ticket count, in house first (WL-401).
- **No vehicle facts.** WL-202 wants the vehicle's details filled in within 1 second of picking, but the Vehicle table has no type and no driver link. Drivers are not tied to one truck.

The team cannot ask the stakeholder (they decide internally), and the account type field is wanted by the company without a stated use. The VMMS vehicle table is the same copy as ours and has no type field either, so VRMS is free to add one now. Feature 56 may later move vehicle ownership. The deadline is the end of November 2026, so the design has to reuse what exists: `applyStatusMove`, the settings catalog, the permission matrix, and the issue categories pattern.

## Options considered

### Option 1: Fix create in place, with one locked transaction (chosen)

Keep the endpoint, move every write into one interactive transaction that locks the vehicle row first, and add the missing fields and rules.

**Pros**: smallest change, and all or nothing by construction. The lock also closes the race without a database constraint Prisma can't model.
**Cons**: the "one open ticket" rule lives in app code; a raw `FOR UPDATE` query inside Prisma.

### Option 2: Partial unique index on open tickets per vehicle

Put the rule in Postgres: a unique index on `vehicle_id` where the status is open.

**Pros**: airtight even against paths that skip create.
**Cons**: Prisma can't model a partial index, so a later generated migration may drop it (the drift risk already flagged for features 30 and 31). Every status move into or out of an open status now risks a unique violation to handle.

### Option 3: Separate draft then submit flow

Save a draft ticket first, then a submit step that assigns and opens it.

**Pros**: lets a form be saved halfway.
**Cons**: a new status and screens nobody asked for, and it doesn't fix the atomicity gap by itself.

**Sub decisions taken during the interview** (each an Admin facing choice, picked by the engineer):
- **Lookup storage:** one generic `LookupValue` table, rather than a table per list or a Postgres enum, because feature 40 will add more plain name lists. Issue categories stay their own table, since they carry entries, descriptions and a change log.
- **Truck history:** `VehicleChange` rather than a type only table, so a truck has one history. It replaces spec 0010's `VehicleStatusChange`.
- **Disabled trucks:** allowed, and restored to `DISABLED` after the repair, through `priorVehicleStatus`.
- **Odometer floor:** computed from tickets rather than a stored value an Admin resets, so fixing or cancelling a bad ticket fixes the floor, with no new screen.

## Rationale

Option 1 fixes the root causes (no transaction, no lock) where they live, using patterns the codebase already has: interactive transactions in `applyStatusMove`, and stale checks on every update path. The row lock gives the same guarantee as Option 2 for every path that exists today, without a constraint that Prisma's migration generator would fight. That trade is worth it because create is the only way a ticket is born.

Account type and corporation are stored minimally (nullable columns, the corporation name as a snapshot) because the company wants the data but no report needs it yet. Storing is cheap, and throwing input away is worse than either storing or dropping. Corporations moving into the lookup table costs almost nothing once the table and its Settings UI exist, and it replaces three made up names.

Vehicle type is configurable from VRMS because no other system holds it today. If feature 56 moves vehicle records to VMMS, type either stays a VRMS field or is mapped then. Driver data is never stored per truck, since drivers rotate; the last driver is derived from tickets and offered only as a suggestion.

Assigning later is limited to Open tickets so this feature stays small and feature 53 (Admin ticket editing) keeps ownership of add, remove and swap on tickets already in work. The new `ticket.assign` key follows spec 0015's call that the Chief Mechanic reassigns by default, and features 53 and 57 reuse it.
