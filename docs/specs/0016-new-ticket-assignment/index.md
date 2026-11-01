# 0016. New repair ticket and assignment: safe create, Open tickets, vehicle facts and lookup lists

**Date**: 2026-11-01
**Status**: Accepted

## Summary

Creating a repair ticket becomes one all or nothing save, and a truck can only have one open ticket at a time. A ticket may now start Open with nobody assigned, and an Admin or Chief Mechanic assigns it later from its detail page. Picking a truck fills in what the system knows about it (model, type, last reading, last repair, last driver), and the mechanic picker shows how busy each person is. Account type and corporation are finally saved, drivers are keyed by their real license number, and Admin gets two new lookup lists (vehicle types and corporations) plus a small Vehicles section in Settings.

## Requirements

**User stories**:
- As an Admin, I want to log a broken truck even when no mechanic is free, so the repair is on record right away.
- As an Admin or Chief Mechanic, I want to assign an Open ticket later, picking the least busy in house mechanic first.
- As an Admin, I want the form to fill in the truck's facts and its usual driver, so I type less and make fewer mistakes.
- As an Admin, I want the system to stop a second open ticket on the same truck, so one breakdown never shows up as two repairs.
- As an Admin, I want to manage vehicle types and corporations myself, without a developer.

**Acceptance criteria**:

*Create*
- **AC-1**: `POST /repairs` takes `mechanics` as optional (zero or more, same `[{ id }]` shape as today). With none, the ticket is created `OPEN`; with one or more, `ASSIGNED` (WL-201). `statusChangedAt` and `lastActivityAt` are set as today.
- **AC-2**: Checks that need no lock run first, outside the transaction: the vehicle by plate (active), the garage, categories, entries, mechanics, the corporation and `driverId`. Then one interactive transaction: `SELECT id, status, odometer FROM vehicles WHERE id = $1 AND is_active AND deleted_at IS NULL FOR UPDATE` (no row means 400 with the existing vehicle message), and only the values read under the lock are used after it. Inside: check for an open ticket, check the odometer, create or reactivate the driver, set the vehicle status, then create the ticket with its issues, assignments and `CREATED` audit row. A `repairNumber` unique collision (P2002 on that column) regenerates the number and retries once, then answers 500. Any failure leaves nothing written: no ticket, no new driver, and the truck's status unchanged. Embedding still runs after commit, not awaited (spec 0013, AC-14).
- **AC-3**: A vehicle with a ticket in an open status (`OPEN_STATUSES`) gets **409** `{ code: 'OPEN_TICKET_EXISTS', message: 'This truck already has an open repair, REP-…. Add the new issues there.', ticket: { id, repairNumber } }`. Two creates for the same truck at the same moment: the second waits on the row lock, then gets this 409. The old form warning (`UNDER_REPAIR_WARNING`) is replaced by this block.
- **AC-4**: `accountType` (`ONLINE` or `CORPORATE`) is required (400 otherwise). `CORPORATE` requires `corporationId`, an active value in the `corporation` lookup list (400 "Choose a corporation." when missing, 400 "This corporation is no longer available. Choose another." when inactive or unknown). With `ONLINE`, any `corporationId` is ignored and `corporation` is stored as null. The ticket stores `accountType` and `corporation` (the name, as a snapshot). The detail side panel shows both when set; old tickets with nulls show nothing for them.
- **AC-5**: `issueDescription` and `driverName` leave `CreateRepairDto` and the web payload. An issue's `description` is optional when it has a `knowledgeEntryId`: blank after trimming, the server uses the entry's name. Without an entry, `description` stays required (1 to 500 after trimming). The stored text keeps today's `[Category] rootCause: description` shape.
- **AC-6**: The body carries exactly one of `driverId` (an active existing driver) or `newDriver: { name, licenseNumber }`; both or neither is 400 "Choose or add a driver." `name` is 1 to 100 after trimming. `licenseNumber` is trimmed and uppercased, then must match `^[A-Z]\d{2}-\d{2}-\d{6}$` (400 "Use the format A01-23-456789."). A license that belongs to an active driver answers **409** `{ code: 'DRIVER_EXISTS', driver: { id, name } }`, including when a concurrent insert wins the unique index. A license that belongs to an inactive or soft deleted driver reactivates that driver in the transaction (`isActive: true`, `deletedAt: null`, stored name kept) and uses them. A `driverId` that is not an active driver is 400 "This driver is no longer available. Choose another." Existing slug drivers stay as they are and are picked like any other driver.
- **AC-7**: The odometer floor for a truck is the highest `odometer` on its non cancelled tickets whenever it has any, and `Vehicle.odometer` only when it has none. One helper, `vehicleOdometerFloor(tx, vehicleId)`, computes it for both create and the summary. A reading equal to the floor is accepted. A reading below the floor is **400** `{ code: 'ODOMETER_BELOW_LAST', last }` ("Odometer can't be lower than the last reading, 45,210 km."). A reading more than `tickets.odometer_jump_warn_km` above the floor needs `confirmOdometerJump: true` in the body, else **400** `{ code: 'ODOMETER_JUMP_UNCONFIRMED', last }`. When the floor is 0 (no baseline yet), the jump check is skipped. The form shows the jump in the summary dialog with a "The reading is right" checkbox that sets the flag.
- **AC-8**: The new setting `tickets.odometer_jump_warn_km` (int, default 20000, min 1000, max 200000, unit km) shows in Settings > Thresholds and is read through `SettingsService`.
- **AC-9**: The ticket stores `priorVehicleStatus`, the vehicle's status just before create. Create sets the vehicle to `UNDER_REPAIR` for every prior status, `DISABLED` included. The release in `applyStatusMove` (a move into a finished status) sets the vehicle to `DISABLED` when the ticket's `priorVehicleStatus` is `DISABLED`, and `AVAILABLE` otherwise (today's behavior, so old tickets with null are unchanged). `UNDER_MAINTENANCE` belongs to VMMS, so it still releases to `AVAILABLE` (feature 56 may revisit). `MovingTicket` gains `priorVehicleStatus`, and every caller that builds one selects it (the move paths in `repairs.service.ts` and `mechanic-work.service.ts`). `priorVehicleStatus` is never edited after create. A disabled truck stays selectable in the form with a "Disabled" tag and a note that it returns to Disabled after the repair.
- **AC-10**: "Reported by" and the report time come from the token and the server clock (as today). The form header shows "Reported by <your name>" read only.

*Vehicle facts on pick*
- **AC-11**: `GET /vrms/vehicles/:id/summary` (`ticket.create`) returns `{ id, plateNumber, model, status, type: { id, name } | null, lastOdometer, lastRepairAt | null, lastDriver: { id, name, licenseNumber } | null, openTicket: { id, repairNumber, repairStatus } | null }`. An inactive or unknown vehicle is 404. `lastDriver` is null when that driver is now inactive or deleted. If old data holds more than one open ticket on the truck, `openTicket` is the newest by `createdAt`.
- **AC-12**: Picking a vehicle calls the summary and shows a vehicle card (model, type, status, last reading, last repair date) within 1 second on the seeded data. The driver field is prefilled with `lastDriver` only while it is empty, and never overwrites a choice. The odometer field shows "Last reading 45,210 km" as a hint, not a value. With an `openTicket`, the form shows the AC-3 message up front with a link to that ticket and disables submit. If the summary fails, the card shows Retry and the form stays usable, and the server checks still apply.

*Drivers*
- **AC-13**: `GET /vrms/config/drivers?q=` returns active drivers only (`isActive`, no `deletedAt`), matching `q` against name or license (case insensitive contains, up to 20 rows by name; with no `q`, the first 20 by name). It returns `{ id, name, licenseNumber }` when the caller's ability has `ticket.create`, checked in the service, and `{ id, name }` to everyone else. The driver combobox searches on the server as you type. It shows name and license, and "Add new driver" reveals Name and License number fields in place. On `DRIVER_EXISTS`, the form shows "A driver with this license exists: <name>." with a "Use <name>" button that switches to that driver.

*Mechanic picker*
- **AC-14**: `GET /vrms/mechanics/available` adds `openCount` (the mechanic's assignments on tickets in `OPEN_STATUSES`) and `busy` (one of them is `IN_PROGRESS`) to each row, and keeps every field it returns today (the Users page needs `email` and `isAvailable`). The picker lists one "In house" group sorted by `openCount` ascending, then name, each row showing "N open" and a Busy badge. The unused `GET /repairs/available-mechanics` is removed.
- **AC-15**: With no mechanic picked, the summary dialog says "This ticket will be Open until someone is assigned." The mechanics field shows no required error.

*Assign later (move M1)*
- **AC-16**: A new permission key `ticket.assign` ("Assign mechanics", group Tickets) defaults to Admin on, Chief Mechanic on, Mechanic off. `ability.factory.ts` gets a case for it: a global `assign` action on the ticket subject (like `administer`, not per assignment). The ticket's `can` flags gain `assign`, and the web `can` type gains it too.
- **AC-17**: `POST /repairs/:id/assignments` (`ticket.assign`) takes `{ mechanics: [{ id }] (1 or more, unique), lastUpdatedAt }`. It works only on an `OPEN` ticket (anything else answers the existing 400 `INVALID_TRANSITION`). Every mechanic must be active (400 "In house mechanic not found"), and a stale `lastUpdatedAt` answers the existing 409. In one transaction, it creates the assignments (`assignedAt` = now, `assignedByUserId` and `assignedByName` from the token, as in create), then moves the ticket to `ASSIGNED` through `applyStatusMove` with M1. Its audit option takes a new builder, `mechanicAssignedEvent(names)`, which writes one `MECHANIC_ASSIGNED` row with changes `{ field: 'mechanic', before: null, after: <name> }` per mechanic, plus `{ field: 'repairStatus', before: 'OPEN', after: 'ASSIGNED' }`. Like M2's `MECHANIC_UNASSIGNED`, no separate `STATUS_CHANGE` row is written. It returns the presented ticket.
- **AC-18**: On a ticket with `repairStatus === 'OPEN'` and `can.assign` true, the detail page's next action is "Assign mechanic". The web derives it from those two values, not from `moves` (M1's trigger is `assignment`, so it carries no label). It opens a dialog with the AC-14 picker; on success it closes, shows a toast and the ticket shows Assigned. A 409 reload behaves like the other ticket actions. Without the flag there is no button, and the side panel says "No mechanic yet."

*Lookup lists*
- **AC-19**: A code catalog defines the generic lookup lists: `vehicle_type` ("Vehicle types") and `corporation` ("Corporations"). `GET /vrms/lookups/:list` (`config.read`) returns active values sorted by `sortOrder`, then name. `GET /vrms/lookups/:list/all` (`lookups.manage`) also returns inactive ones, for the Settings editor, so each route keeps exactly one permission decorator. `POST /vrms/lookups/:list` `{ name }` and `PATCH /vrms/lookups/:list/:id` `{ name?, isActive? }` need `lookups.manage`. An unknown list is 404. Names are 1 to 100 after trimming, and a duplicate `nameKey` in the same list is **409** "That name is already in the list." Values are never deleted. Each write adds a `LookupValueChange` row in the same transaction.
- **AC-20**: Settings > Lookup lists shows Vehicle types and Corporations beside Issue categories, with add, rename, deactivate and reactivate. Their changes appear in Settings > Change history: `LookupValueChange` becomes another source of the existing feed in `settings-admin.service.ts`, merged into its keyset order, labeled with the list's title and the value's name, with the action shown as Added, Renamed, Deactivated or Reactivated. The migration inserts the starting values with fixed `nameKey`s and `sortOrder` 10, 20, 30 and so on, in the listed order: the three corporation names from `repairOptions.ts`, and the vehicle types `4 wheeler`, `6 wheeler`, `10 wheeler`, `Wing van`, `Tractor head`, `Trailer`. `sortOrder` is not editable in this spec, and new values get the list's highest plus 10. The form's corporation select reads the `corporation` list, and `CORPORATION_OPTIONS` is deleted.

*Vehicles in Settings*
- **AC-21**: A new permission key `vehicle.manage` ("Manage vehicles", group Records) defaults to Admin on, others off, with its own case in `ability.factory.ts` (a key with no subject, like `lookups.manage`). Settings gets a Vehicles section, shown only with that key, listing every active vehicle with plate, model, status and a type select. `GET /vrms/vehicles` and `PATCH /vrms/vehicles/:id` `{ vehicleTypeId: uuid | null, updatedAt }` need `vehicle.manage`. A stale `updatedAt` is 409, and an inactive type or one from another list is 400. Each change writes a `VehicleChange` row (`field: 'vehicleType'`, before and after as `{ id, name }` or null) in the same transaction. `VehicleChange` rows are not shown anywhere yet (feature 25 shows a truck's history). Any create bumps `Vehicle.updatedAt`, so a Settings row may get the stale 409; the section then refetches that row and says "This truck changed. Check the type and save again." The seed gives each seeded truck a type through a new `type` field on each `VEHICLES` entry in `prisma/seeds/catalog.ts` (one of the starting vehicle type names, chosen per model when the seed is written). The migration sets no type on existing rows.

*Sweep*
- **AC-22**: The form, the assign dialog and both new Settings sections pass axe at 375px and 1280px. Lint, typecheck, build and tests pass in welinc-backend-vrms and welinc-web-vrms, with new unit tests for the floor and jump rules, the release restore, the driver choice and the lookup duplicate rule.

## Decision

**Chosen option**: fix the create flow in place (one transaction with a vehicle row lock), with generic lookup lists for simple Admin managed values.

`POST /repairs` becomes one locked transaction that refuses a second open ticket per truck. Tickets may start Open and are assigned later through M1. Vehicle facts come from one summary call per pick. Simple lists live in one `LookupValue` table behind `lookups.manage`, and truck edits sit behind a new `vehicle.manage` key with their own `VehicleChange` history.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` and `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-client-api/`, `.claude/skills/prisma-cli/`) · `react-hook-form` (`.claude/skills/react-hook-form/`) · `shadcn` (`shadcn-ui/ui`, `.claude/skills/shadcn/`)

## Feature design

**Data model** (one migration, all additive):

| Entity | Change | Fields | Keys and relations |
|---|---|---|---|
| `LookupValue` (new, `lookup_values`) | generic plain lists | `id` uuid, `list` varchar(40), `name` varchar(100), `nameKey` varchar(100) (trim + lowercase), `isActive` bool default true, `sortOrder` int default 0, `createdAt`, `updatedAt` | unique (`list`, `nameKey`); index (`list`, `isActive`) |
| `LookupValueChange` (new, `lookup_value_changes`) | list edit history | `id`, `lookupValueId`, `action` varchar(12) (`CREATE`, `RENAME`, `DEACTIVATE`, `REACTIVATE`), `before` Json, `after` Json, `actorUserId`, `actorName`, `actorEmail`, `createdAt` timestamptz(3) | N:1 `LookupValue`; index (`createdAt` desc, `id` desc) |
| `Vehicle` | add type | `vehicleTypeId` uuid nullable | N:1 `LookupValue`, onDelete Restrict |
| `VehicleChange` (new, `vehicle_changes`) | one history per truck | `id`, `vehicleId`, `field` varchar(30), `before` Json, `after` Json, `actorUserId`, `actorName`, `actorEmail`, `note` text nullable, `createdAt` timestamptz(3) | N:1 `Vehicle`; index (`vehicleId`, `createdAt`) |
| `RepairTicket` | add | `accountType` enum `TicketAccountType` (`ONLINE`, `CORPORATE`) nullable, `corporation` varchar(100) nullable, `priorVehicleStatus` `VehicleStatus` nullable | none new |
| `Driver` | none | new rows carry a real LTO license in `licenseNumber` (already unique) | |

Catalog changes with no migration: permission keys `ticket.assign` and `vehicle.manage` (the startup backfill adds their rows), setting `tickets.odometer_jump_warn_km`, and audit action `MECHANIC_ASSIGNED`. The `lookups.manage` description becomes "Add, rename and deactivate issue categories, vehicle types and corporations."

**State transitions**: create writes the first status (`OPEN` with no mechanics, `ASSIGNED` with one or more). After that, M1 (`OPEN` → `ASSIGNED`, trigger `assignment`) is switched on through `POST /repairs/:id/assignments`. M2 is unchanged (the release path). No other move changes.

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/repairs` | POST | `vehiclePlate`, `garageLocation`, `odometerReading`, `confirmOdometerJump?`, `driverId` or `newDriver {name, licenseNumber}`, `accountType`, `corporationId?`, `priority`, `mechanics?[]`, `issues[] {categoryId, rootCause, description?, knowledgeEntryId?}` | presented ticket | `ticket.create` | 400 (validation, `ODOMETER_BELOW_LAST`, `ODOMETER_JUMP_UNCONFIRMED`), 409 `OPEN_TICKET_EXISTS`, 409 `DRIVER_EXISTS` |
| `/repairs/:id/assignments` | POST | `mechanics[{ id }]`, `lastUpdatedAt` | presented ticket | `ticket.assign` | 400 (invalid move, unknown mechanic), 404, 409 (stale) |
| `/vrms/vehicles/:id/summary` | GET | id | AC-11 shape | `ticket.create` | 404 |
| `/vrms/vehicles` | GET | none | `[{ id, plateNumber, model, status, type, updatedAt }]` | `vehicle.manage` | |
| `/vrms/vehicles/:id` | PATCH | `vehicleTypeId \| null`, `updatedAt` | the row | `vehicle.manage` | 400, 404, 409 stale |
| `/vrms/lookups/:list` | GET | none | active `[{ id, name, isActive, sortOrder }]` | `config.read` | 404 list |
| `/vrms/lookups/:list/all` | GET | none | every value, inactive included | `lookups.manage` | 404 list |
| `/vrms/lookups/:list` | POST | `name` | the value | `lookups.manage` | 400, 404, 409 duplicate |
| `/vrms/lookups/:list/:id` | PATCH | `name?`, `isActive?` | the value | `lookups.manage` | 400, 404, 409 duplicate |
| `/vrms/mechanics/available` | GET | none | today's fields + `openCount`, `busy` | `config.read` | |
| `/vrms/config/drivers` | GET | `q?` | active drivers, up to 20: `{ id, name, licenseNumber? }` | `config.read` (license only with `ticket.create`) | |
| `/repairs/available-mechanics` | GET | | removed | | |

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| create | first status | derived: `mechanics.length` (0 → `OPEN`, else `ASSIGNED`) |
| create | open ticket check | `RepairTicket` where `vehicleId` and `repairStatus in OPEN_STATUSES`, after the row lock |
| create | odometer floor | max `RepairTicket.odometer` where `vehicleId` and status not `CANCELLED`; else `Vehicle.odometer` |
| create | jump threshold | `SettingsService.get('tickets.odometer_jump_warn_km')` |
| create | `priorVehicleStatus` | `Vehicle.status` read under the lock |
| create | `corporation` | `LookupValue.name` of `corporationId` (list `corporation`, active) |
| create | blank issue description | `KnowledgeEntry.name` of `knowledgeEntryId` |
| create | reporter, time | JWT `sub` + `whoName(user)`, server clock |
| release | vehicle status after finish | `RepairTicket.priorVehicleStatus` (`DISABLED` → `DISABLED`, else `AVAILABLE`) |
| summary | `lastOdometer` | the same floor rule |
| summary | `lastRepairAt` | max `closedAt` of the truck's `CLOSED` tickets |
| summary | `lastDriver` | driver of the truck's newest non cancelled ticket by `createdAt` |
| summary | `openTicket` | the truck's ticket in `OPEN_STATUSES` (at most one, by AC-3) |
| summary | `type` | `Vehicle.vehicleTypeId` → `LookupValue` |
| picker | `openCount`, `busy` | `TicketAssignment` joined to tickets in `OPEN_STATUSES`; `busy` when any is `IN_PROGRESS` |
| drivers | `licenseNumber` shown | included only when the caller's ability has `ticket.create` |
| assign | assigner | JWT, as in create |

**Key invariants**:
- At most one ticket per vehicle in an open status, enforced by the vehicle row lock in create. Every other path that could open a ticket goes through create. No move leaves a finished status (`TICKET_MOVES` has none), and unlock never changes `repairStatus`, so nothing reopens a ticket behind the check.
- After create, `repairStatus` changes only through `applyStatusMove` (spec 0014), and every status change sets `statusChangedAt` (spec 0015).
- A ticket's `corporation` is a snapshot. Renaming or deactivating a lookup value never rewrites a ticket.
- Lookup values and vehicles are never deleted from the app. A `Vehicle.vehicleTypeId` always points at a `vehicle_type` value (checked on write).
- A finished ticket never turns a `DISABLED` truck into `AVAILABLE`.

**Security model**:
- Create, vehicle summary and license numbers: `ticket.create` (Admin by default).
- Assign: `ticket.assign` (Admin and Chief by default). Mechanics can't assign themselves.
- Lookup list edits: `lookups.manage`. Reading active values: `config.read`.
- Truck type edits and the Vehicles list: `vehicle.manage` (Admin by default).
- License numbers are personal data. They never reach a caller without `ticket.create`, and they are never logged.
- Every route carries exactly one permission decorator (`route-permissions.spec.ts`).

**Configuration required**: no new environment variables.

**Critical test scenarios**:
- Happy path: create with no mechanic, the ticket is Open, then assign two mechanics; it is Assigned with one `MECHANIC_ASSIGNED` row. Verifies **AC-1**, **AC-17**, **AC-18**.
- Race: two creates for one truck at once; one succeeds, the other gets 409 `OPEN_TICKET_EXISTS`. Verifies **AC-2**, **AC-3**.
- Rollback: force the ticket insert to fail after a new driver; no driver row, truck status unchanged. Verifies **AC-2**.
- Odometer: below the floor is 400; equal is accepted; 25,000 km above without the flag is 400, and with it, success; a truck with floor 0 never asks. Cancel the high ticket and the floor drops. Verifies **AC-7**.
- Disabled truck: create, then close; the truck is `DISABLED` again. Verifies **AC-9**.
- Duplicate license: 409 with the existing active driver, and "Use" switches to them; an inactive driver's license reactivates them instead. Verifies **AC-6**, **AC-13**.
- Auth: a Mechanic gets 403 on assign, on `/vrms/vehicles` and on lookup writes, and sees no `licenseNumber` in drivers. Verifies **AC-13**, **AC-16**, **AC-19**, **AC-21**.

## Build plan

Tracer Bullet: first a thin thread through every layer (the safe create, end to end), then thicken it one strand at a time.

**Milestone 1: Thin thread, safe create**
1. One migration: the `TicketAccountType` enum, the three ticket columns, `lookup_values`, `lookup_value_changes`, `vehicles.vehicle_type_id`, `vehicle_changes`, plus the starting lookup values. Prisma schema updated. Satisfies **AC-4**, **AC-9**, **AC-19**, **AC-20**, **AC-21**.
2. Rewrite `RepairsService.create` as one interactive transaction with the vehicle row lock, the open ticket check, `priorVehicleStatus`, and optional mechanics with Open or Assigned. Satisfies **AC-1**, **AC-2**, **AC-3**, **AC-9**.
3. The release restore in `applyStatusMove`, with `priorVehicleStatus` on `MovingTicket` and selected by every caller. Satisfies **AC-9**.
4. Web: mechanics optional in `repairFormSchema.ts`, the Open note in the summary dialog, and the 409 `OPEN_TICKET_EXISTS` handling with a link. Satisfies **AC-1**, **AC-3**, **AC-15**.

**Milestone 2: Form data, the account, the driver and the odometer**
5. Lookup read endpoint and the `corporation` list on the form; `accountType` and `corporationId` stored; `issueDescription` and `driverName` dropped; the description fallback. Satisfies **AC-4**, **AC-5**, **AC-19**.
6. Driver choice (`driverId` or `newDriver`), the LTO check, 409 `DRIVER_EXISTS`, the license gated driver list, and the driver combobox with Add new and Use. Satisfies **AC-6**, **AC-13**.
7. The odometer floor and jump rules, the new setting, and the summary dialog confirm. Satisfies **AC-7**, **AC-8**.

**Milestone 3: Vehicle facts and the picker**
8. `GET /vrms/vehicles/:id/summary`, the vehicle card, the driver prefill, the odometer hint, the open ticket block, the disabled tag, and "Reported by". Satisfies **AC-10**, **AC-11**, **AC-12**, **AC-9**.
9. `openCount` and `busy` on the mechanics endpoint, the sorted picker, and removal of the old route. Satisfies **AC-14**.

**Milestone 4: Assign later**
10. The `ticket.assign` key with its `ability.factory.ts` case and `can.assign`, the `MECHANIC_ASSIGNED` action and `mechanicAssignedEvent`, `POST /repairs/:id/assignments` through M1, the Assign mechanic next action and dialog. Satisfies **AC-16**, **AC-17**, **AC-18**.

**Milestone 5: Settings and sweep**
11. Lookup write endpoints and `/all` with `LookupValueChange`, the Vehicle types and Corporations sections, and the new Change history source in `settings-admin.service.ts`. Satisfies **AC-19**, **AC-20**.
12. The `vehicle.manage` key, the `/vrms/vehicles` endpoints with `VehicleChange`, the Vehicles section, and seeded types. Satisfies **AC-21**.
13. Tests, fixtures, axe at 375px and 1280px, then lint, typecheck and build in both repos. Satisfies **AC-22**.

## Migration plan

**Strategy**: no data migration beyond inserts. Every change is additive (nullable columns, new tables, starting lookup rows).
**Phases**: one migration folder after the baseline; deploy backend and web together, since the web stops sending `issueDescription` and `driverName`, which the new DTO rejects (`forbidNonWhitelisted`).
**Rollback**: revert both repos together. The new columns and tables can stay; old code ignores them.
**Risks**: an old web build against the new API fails on create (400 for unknown fields). Ship both at once.

## Consequences

**Positive**:
- A failed create can no longer leave a truck stuck as Under repair, and one truck can't hold two open repairs.
- WL-201's Open on create and assign later both work, and M1 finally has a trigger.
- Feature 40 gets a ready home for plain lists, and feature 25 gets a vehicle history table and a Settings section to grow.

**Negative / tradeoffs**:
- The row lock serializes creates per truck. That's harmless at this fleet size, but it is a raw query inside Prisma.
- The "one open ticket" rule lives in application code, not a database constraint. A future path that inserts tickets without create would skip it.
- A generic lookup table can't make the database promise a value belongs to the right list. The server checks it on write.
- Three new permission keys or descriptions and two new Settings sections grow the matrix and the hub.
- Old slug drivers have no real license until someone fixes them (no edit UI here).
- The release restores the `priorVehicleStatus` stored at create. If feature 25 lets an Admin change a truck's status while a ticket is open, the release will overwrite it, so feature 25 must account for that.
- The floor ignores a `Vehicle.odometer` higher than every ticket once a truck has tickets. That's accepted, since tickets are the readings people can correct.

**Neutral**:
- Spec 0010's planned `VehicleStatusChange` is replaced by `VehicleChange` (`field: 'status'`) for feature 25.
- `Vehicle.odometer` is still synced on close, but the floor no longer relies on it once a truck has tickets.

## Follow-up

- [ ] Spec 0010: note that `VehicleChange` replaces the planned `VehicleStatusChange`, and the new ticket columns `accountType`, `corporation` and `priorVehicleStatus`.
- [ ] Spec 0014: note that M1 is switched on by `POST /repairs/:id/assignments`, and the release restores `DISABLED`.
- [ ] Spec 0012: note the generic lookup lists in Lookup lists, the Vehicles section, and the `tickets.odometer_jump_warn_km` threshold.
- [ ] Scope feature 25: use `VehicleChange` (`field: 'status'`) and add the status toggle to the Settings Vehicles section, behind `vehicle.manage`.
- [ ] Scope feature 53: reuse `ticket.assign` for reassign; let an Admin correct a ticket's odometer (the floor follows it); add mechanics to Assigned or In Progress tickets.
- [ ] Scope feature 57: reuse `openCount` and `busy`, and `ticket.assign` for Unassign and Reassign.
- [ ] Scope feature 40: move root causes and other plain lists into `LookupValue`.
- [ ] Scope feature 28: notify the mechanic on create with mechanics and on assign (WL-201, VRMS-67).
- [ ] Scope feature 36: add the outsourced group after In house in the picker (WL-401).
- [ ] Scope feature 56: decide who owns vehicle type once VMMS shares vehicle records.
- [ ] `docs/context/requirements.md` and the glossary: account type is now stored; the driver license is the key.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
