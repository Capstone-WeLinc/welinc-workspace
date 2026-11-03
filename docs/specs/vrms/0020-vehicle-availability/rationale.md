# 0020. Vehicle availability: rationale

**Status**: see [index.md](index.md)

## Context

WeLinc Logistics must not dispatch a truck that is being repaired or that is out of service. Jira WL-501 (VRMS-195) proposes three statuses (Available, Under Repair, Disabled), automatic changes from tickets, a manual Admin toggle with a required reason, and a history kept per vehicle. The stakeholder never answered who disables a truck or when, so the team decides.

Much of this already exists. Spec 0010 added `DISABLED`. Spec 0014 moved the release into the status transaction. Spec 0016 sets `UNDER_REPAIR` on create, stores `priorVehicleStatus` on the ticket so a Disabled truck goes back to Disabled after its repair, added the `vehicle.manage` key, the Settings Vehicles section and the `VehicleChange` history table (today only type changes write to it). Spec 0016 also warned that a manual toggle during an open ticket would be overwritten by the release.

The forces: about four weeks to deployment, a stakeholder flow (VRMS004: an unavailable truck is flagged) that only needs the status to be right, and vehicle status being shared with VMMS (`UNDER_MAINTENANCE`), which the integration meeting (feature 56) has not settled. Without a decision, the build would have to invent which statuses are manual, what a toggle does mid repair, and whether ticket driven changes are history.

## Options considered

### Option 1: Available and Disabled only, blocked while a ticket is open, full history

The Admin switches a truck between Available and Disabled with a reason. A truck with an open ticket can't be toggled. Create and release also write history rows, linked to the ticket by a new column.

**Pros**:
- What the row shows is what the truck is; there's no pending state to explain.
- The release rule from spec 0016 stays untouched.
- The history is complete and links each repair.

**Cons**:
- A truck meant to be retired shows Available briefly after its repair closes, until the Admin disables it.
- Needs a small migration for the ticket link.

### Option 2: Toggle while open sets what the release restores

The toggle is allowed during a repair. The truck stays Under repair, the choice is saved to the open ticket's `priorVehicleStatus`, and the release lands on it.

**Pros**:
- No gap: a truck to be retired goes straight to Disabled on close.
- Reuses an existing column and release rule.

**Cons**:
- A hidden pending state the UI must surface ("Disabled after repair"), or nobody knows it is set.
- The history row for the decision lands at close, not when the Admin clicked, unless a second row kind is added.
- About one more milestone of work.

### Option 3: Toggle overrides immediately, even mid repair

The Admin's choice applies at once, and the release learns to skip trucks the Admin changed.

**Pros**:
- The most direct control.

**Cons**:
- The truck can read Available while a mechanic is working on it, which is exactly what VRMS004 forbids.
- The release needs a new "did the Admin touch it" rule, a second source of truth.

### History sub options

Manual rows only (no create and release rows) was considered: less code, but the history would not explain most status changes. For the ticket link, putting the ticket in the note text or in the `after` JSON avoids a migration, but gives no reliable link and nothing for reports to join on.

## Rationale

The engineer chose Option 1 after weighing Option 2. The deciding forces are the deadline and the rule that a truck under repair must read Under repair: Option 3 breaks that rule, and Option 2 costs a milestone and a hidden state to close a gap the stakeholder never raised. Blocking keeps the ticket as the single owner of the status during a repair, so spec 0016's release rule needs no change. The gap is written down as a follow up, and Option 2 can be added later without undoing anything, since it only adds a write to `priorVehicleStatus`.

Writing ticket driven changes to the same history, with a real foreign key, makes the per vehicle history WL-501 asks for actually useful: every status the truck held is explained, and reports (feature 45) can join on the ticket. `SetNull` keeps history rows when a ticket is removed. Limiting the toggle to Available and Disabled leaves Under repair to tickets and Under maintenance to VMMS until feature 56 decides.

Smaller calls made here: a dedicated `POST /vrms/vehicles/:id/status` rather than widening the type `PATCH`, because the toggle has its own rules, errors and required reason (runner up: one `PATCH` with optional fields, which mixes two validations). A truck stuck in Under repair with no open ticket can be toggled, so a data glitch is fixable from the screen (runner up: refuse it too, which leaves a stuck truck with no fix but SQL). The history is keyset paged at 20 like the ticket Activity timeline (runner up: load all, which grows with every repair). The reason uses the 5 to 500 limits of the other note dialogs. The existing `vehicle.manage` key is reused, since an Admin can grant it to the Chief Mechanic (runner up: a separate status key, one more row in the matrix for no current need).
