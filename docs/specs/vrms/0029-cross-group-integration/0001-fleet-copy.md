# 0001. Fleet copy: VRMS keeps a read only copy of VMMS's trucks and garages

Child of [0029](index.md). Acceptance criteria AC-1 to AC-5 live in the umbrella.

## Summary

VMMS owns the trucks and garages. VRMS keeps a copy so its tickets, lists and analytics still join to a local table, but nobody in VRMS edits it. VMMS sends a short "this changed" message, VRMS reads the record fresh, and an hourly full read fixes anything a lost message missed. A one time script links today's VRMS rows to VMMS and archives the ones VMMS doesn't have, keeping their tickets.

## Design

**One time link, `npm run fleet:link` (backend-vrms `scripts/`)**
1. Read `GET /vmms/fleet/garages` and `GET /vmms/fleet/vehicles` (service token: audience `VMMS`, `fleet.read`).
2. Match garages by `lower(trim(name))` and trucks by `lower(trim(plateNumber))`. If two VRMS rows match one VMMS record, list them and exit 1 without changing anything.
3. Print the plan: the matches, the unmatched garages and trucks with their ticket counts, and the VMMS records VRMS lacks.
4. Without `--confirm`, exit 0 there. With `--confirm`, in one transaction:
   - set `vmmsGarageId` and `vmmsVehicleId` on the matches and copy their fields as the sync would
   - set the unmatched rows `isActive` false, leaving the VMMS id null; their tickets, history and audit rows stay untouched
   - insert every VMMS garage and truck VRMS doesn't have yet
5. It refuses to run with `--confirm` when `SENTRY_ENVIRONMENT=production`.

**Change messages, `POST /vrms/integrations/vmms/fleet-changes`**

| Field | Type | Rule |
|---|---|---|
| `eventId` | uuid | required |
| `entityType` | `VEHICLE` \| `GARAGE` | required |
| `entityId` | uuid | VMMS id, required |
| `changeType` | string | any of VMMS's values (`VEHICLE_CREATED`, `VEHICLE_IMPORTED`, `VEHICLE_UPDATED`, `ODOMETER_UPDATED`, `VEHICLE_DELETED`, `GARAGE_CREATED`, `GARAGE_UPDATED`, `GARAGE_DELETED`); only for logging |
| `occurredAt` | ISO 8601 | required |

Auth: audience `VRMS`, client `vmms`, scope `fleet.change.write`. Reply 202 `{ accepted: true }` at once, then read the entity fresh in the background (`GET /vmms/fleet/vehicles/:id`, or the garages list for a garage) and apply it. The message itself is never trusted for field values. A failed background read is logged and left for the reconcile. No receipt table: applying the same fresh read twice changes nothing.

**Reconcile job** (`FleetReconcileJob`, `@Interval` read from `fleet.reconcileMinutes`, checked each minute): read both lists, upsert by VMMS id, and set rows that are missing from VMMS's lists to `isActive` false. **Guard:** when a list is empty, or the missing rows are more than 20% of the active linked rows, it deactivates nothing and calls `reportJobFailure('fleet-reconcile', …)` with the counts. Upserts still apply. A failure calls `reportJobFailure('fleet-reconcile', error)` and never rethrows.

**Truck removed in VMMS (AC-35).** The flag is worked out on read, not stored: a ticket is "Truck removed in VMMS" when it is open and its truck has `isActive` false. The ticket detail page shows it as a banner, the ticket list as a chip, and the Admin dashboard as a card, "Trucks removed in VMMS (n)". The Admin cancels the ticket, or VMMS reactivates the truck and the next sync clears it. Its VMMS deliveries fail with 404 `VEHICLE_NOT_FOUND`, which shows on the Deliveries tab.

**Applying a VMMS record** (one function, `applyFleetVehicle(tx, record)`; the only writer of these fields). It first locks the local row (`SELECT … FOR UPDATE` by `vmmsVehicleId`), so a change message and the reconcile never write the same history twice:

| VRMS column | Source (VMMS `FleetVehicle`) |
|---|---|
| `vmmsVehicleId` | `id` |
| `plateNumber`, `model`, `make`, `capacity`, `odometer` | same names |
| `truckSizeCategory` | `truckSizeCategory` |
| `vehicleTypeId` | the `vehicle_type` lookup value whose name matches `truckSizeCategory` (trimmed, case insensitive), created by the system if missing; null when `truckSizeCategory` is null |
| `status` | `status` (`AVAILABLE`, `UNDER_REPAIR`, `UNDER_MAINTENANCE`) |
| `garageId` | the local `Garage` whose `vmmsGarageId` is `garageId`; null if none |
| `isActive` | true while VMMS lists it; false after a 404 or when missing from the list |
| `syncedAt` | now |

Each changed field except `odometer` writes one `VehicleChange` row (`actorName: 'VMMS'`, `actorUserId: null`, `repairTicketId: null`). A plate that now clashes with another local row's plate (VMMS reused a plate) is skipped and logged, and reported through `reportJobFailure`. The other fields still apply.

Garages: `applyFleetGarage(tx, { id, name })` locks the row the same way, then sets `vmmsGarageId`, `name`, `isActive`, `syncedAt`. A name that clashes with another local garage (VMMS swapped or reused a name) is skipped and reported like a plate clash, and the next sync applies it once the other row has changed.

**Ticket create** (`repairs.service.ts` `create`): after the plate lookup and before the transaction opens, read `GET /vmms/fleet/vehicles/:vmmsVehicleId` (3 s timeout). Inside the transaction, after taking the open ticket lock on the vehicle row, apply what was read. On a 404, refuse with 422 `VEHICLE_NOT_IN_VMMS`. On a timeout or 5xx, go on with the copy and return `fleetStale: true`, which the form shows as "VMMS can't be reached, using the last copy". The `UNDER_MAINTENANCE` lock and the `vehicleStatusChange` calls in create and in `applyStatusMove` release are removed. The open ticket lock (`SELECT … FOR UPDATE` on the vehicle row, 409 `OPEN_TICKET_EXISTS`) stays.

**Removed**: `POST /vrms/vehicles/:id/status`, `PATCH /vrms/vehicles/:id`, `vehicleStatusChange`, the `DISABLED` enum value (migration maps any `DISABLED` row to `AVAILABLE` before the sync overwrites it), and the web toggle and type edit in `VehiclesSection.tsx`.

**Web**: Settings, Vehicles keeps the table (plate, model, size, garage, status, open ticket), adds "Managed in VMMS" with the last `syncedAt`, and keeps the history dialog. The new ticket form's truck picker reads `GET /vrms/config/vehicles` filtered to `isActive` and linked. Its empty state reads "Not in VMMS yet. Ask VMMS Operations to add it."

**Value sourcing**

| Action | Value | Source |
|---|---|---|
| Sync | every copied field | the VMMS fleet API record (table above) |
| Sync | `VehicleChange.actorName` | the literal `VMMS` |
| Ticket create | truck facts | fresh VMMS read, else the copy |
| Ticket create | ticket garage | the form's garage; for a referral, the truck's `garageId` (child 0002) |

**Invariants**
- Only `applyFleetVehicle` and `applyFleetGarage` write the copied fields, each with the row locked.
- A row with `vmmsVehicleId` null never appears in a picker. After `fleet:link`, every such row is archived.
- A truck VMMS stops listing is deactivated, never deleted.
- The reconcile never deactivates on an empty list or on more than 20% of rows at once.

**Critical test scenarios**
- A rename: VMMS renames a plate, and within a minute VRMS shows it, with a history row by VMMS. Verifies **AC-2**, **AC-3**.
- A bad answer: VMMS answers an empty truck list, and nothing is deactivated; a failure is reported. Verifies **AC-3**.
- A removed truck: VMMS deactivates a truck with an open ticket, and the ticket shows "Truck removed in VMMS". Verifies **AC-35**.
- `fleet:link`: two VRMS plates differing only in case stop the run; a clean run archives the unmatched trucks, and their tickets still open. Verifies **AC-1**.

**Inline rationale**: change messages plus a slow full read is how integrators of Stripe and Shopify webhooks keep copies. It's fast in the normal case and self healing when a message is lost. VMMS already sends these messages to BMS, so adding VRMS is one recipient. Reading the record fresh, instead of trusting the message body, means a late or reordered message can never write old data.
