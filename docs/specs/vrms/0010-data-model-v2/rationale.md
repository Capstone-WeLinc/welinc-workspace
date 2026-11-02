# 0010. Data model v2: decision record

Back to the build spec: [index.md](index.md).

## Context

> ⚠️ Premise note: scope feature 4 asks for a schema that "supports slices 1 to 6 without another breaking migration". Only the breaking changes are built here; the new tables are designed but created later by their features. That still meets the goal, because adding a table or a nullable column never breaks anything. The real risk is different: once the 18 migrations are squashed, any open branch that still carries its own migration stops applying. That is why the build plan starts by clearing those branches.

welinc-backend-vrms (NestJS 11, Prisma 7, PostgreSQL 16) has 18 migrations. Many of them come from the Capstone 1 monolith: a `users` table, login lockout and profile fields that spec 0009 then deleted again, and one migration with no name. The schema also carries models copied from BMS and VMMS (`Booking`, `MaintenanceSchedule`, `ChecklistTemplate`, `ChecklistItem`) that no VRMS code reads or writes, a `ShopChangeLog` table nothing uses, and ticket columns that are never written (`isArchived`, `durationDays`, `durationHours`).

The Jira backlog needs a different ticket model from the one in the code. WL-200 asks for one official status list (Open, Assigned, In Progress, On Hold, For Verification, Outsourced, Closed, Cancelled, with WL-403 adding Pending Management Approval) where today there are five forward only statuses. WL-212 wants the verifier recorded on the ticket. WL-201 wants priority and reporter saved (the form already sends priority, but it is dropped). WL-219 wants every ticket event in one consistent audit shape. WL-218, WL-304, WL-204, WL-208, WL-401 to 405, WL-203, WL-206/207 and WL-501 each need new tables. Outsourced work today is modelled as fake mechanics with a typed shop name.

The forces: nothing is deployed and the local databases hold only seed data, so a reset costs nothing now and a lot later. Slice 1 starts next, and every Slice 1 feature touches ticket status. The deadline is the end of November 2026, so features can't afford to each reshape the ticket. Several features (16, 20, 28, 31, 37, 40, 42) still have their own design step, so this spec must decide the shape without taking their behaviour decisions away. The Python analytics service reads the VRMS database directly, and it is being retired (feature 3).

If nothing is decided, each Slice 1 feature renames statuses or reshapes the audit log on its own, the migration history keeps growing on top of the monolith leftovers, and the later tables get designed one at a time with nobody checking that they fit together.

## Options considered

### Option 1: Keep the history, add v2 migrations on top

Leave the 18 migrations and add a v2 migration that converts existing rows to the new statuses and shapes, then add each later table with its feature.

**Pros**:
- Proves a real data conversion, the path a live system would need.
- No reset for anyone.

**Cons**:
- The monolith history (users tables created then dropped, an unnamed migration) stays forever.
- Writes conversion code for data that is only seed data.
- Every reader of the migration folder keeps paying for history nobody needs.

### Option 2: Squash into one baseline with the breaking changes, design the later tables now (chosen)

Replace all 18 migrations with one baseline that builds the v2 schema from empty, including the breaking changes and the slice 1 columns, and record the design of every later table in this spec.

**Pros**:
- One readable migration, generated from the schema, with the two handwritten parts (`pg_trgm`, the category seed) kept.
- No conversion code: the seed simply writes the new shape.
- Breaking changes happen once, at the cheapest moment.
- Later tables arrive with the feature that uses them (Tracer Bullet) but already fit together.

**Cons**:
- Everyone resets and reseeds once.
- Open branches with their own migrations must be merged or rebased first.
- Doesn't exercise a live data conversion (nothing needs one yet).

### Option 3: Squash the old history, then add v2 as its own migration

Squash the 18 into a baseline equal to today's schema, then add v2 as a second migration that converts rows.

**Pros**:
- Clean history and a tested conversion.

**Cons**:
- The most work: two migrations plus conversion code for seed data.
- The conversion is thrown away the moment everyone reseeds.

### Option 4: Create every table now in one migration

Like Option 2, but also create the later tables (files, notifications, transfers, holds, shops, lookups) in the baseline.

**Pros**:
- One migration for slices 1 to 6.

**Cons**:
- Empty tables sit unused for weeks, against the project's Tracer Bullet approach.
- Feature specs (20, 28, 31, 37, 40) may still change them, and then they need a migration anyway.

## Rationale

Option 2 fits the forces exactly. There is no real data, so the only value of a conversion (Options 1 and 3) is practice, and it would be thrown away at the next reseed. Squashing removes the monolith leftovers that spec 0009 already cut out of the code. Doing the breaking changes now, before Slice 1, means features 16 to 25 build on final names instead of renaming them one by one. Designing the later tables now, but creating them with their features, keeps Tracer Bullet's "build it when you use it" without letting each feature invent its own shape. Option 4 was the runner up; it loses because empty tables wait weeks and their feature specs may still change them.

### The smaller calls inside the decision

- **Statuses**: the full WL-200 list plus `PENDING_APPROVAL`, with `COMPLETED` renamed `CLOSED`. You preferred Closed, and it is the right word: in ticketing, Closed means checked and final, which is what happens after verification (WL-212 uses the same word). Today only Admin closes, so `verifiedBy*` records the Admin; whether the Chief Mechanic closes is feature 16 and feature 5's call. Doing it now costs nothing extra because the statuses change anyway. Runner up: keep `COMPLETED` to avoid renaming the web app.
- **Names here, rules in feature 16**: this spec fixes the enum; feature 16 keeps the transition table, backward moves and what they do to the spec 0007 checklist. Runner up: both here, which would decide permissions before feature 5 exists.
- **Slice 1 columns in the baseline** (priority, reporter, verifier, `dueAtSource`, `lastActivityAt`): they sit on an existing table and Slice 1 uses them at once, so a tiny migration per feature would be pure overhead. Runner up: breaking changes only.
- **`TicketAssignment` instead of the hidden join table**: when and by whom a mechanic was assigned is what transfers and open ticket counts need, and the squash makes the switch free. Runner up: keep the hidden table and dig through audit rows.
- **No lead mechanic, no cap**: your choice. All assigned mechanics are equal, so stuck, stale and deadline alerts go to every assigned mechanic. The picker and the new workload view show each mechanic's load, as WL-201 asks, instead of a hard limit. The tradeoff to accept: on a shared ticket, nobody is singled out as responsible for WL-303's escalation.
- **Audit as one row per event with a JSON `changes` list**: your choice over my recommendation (one row per field, the existing shape). It is a sound choice: it groups a multi field edit as the single event it really is, it matches WL-219's "one consistent schema", and every later log copies it. What you accept: spec 0003's timeline and the knowledge history get rewritten, and filtering by one field needs a JSON query. `action` stays text from `audit-events.ts` (not a Postgres enum) so new events in features 24, 30, 31 and 37 need no migration. `ON DELETE RESTRICT` makes WL-219's "can't be deleted" hold in the database too.
- **Knowledge log on the same shape**: one audit shape across VRMS; the reset makes it free. Runner up: leave the verified knowledge log alone.
- **Drop `failedVerificationReason`**: a reject can happen several times, so the comment belongs on each reject event's `note`, not in one column that only keeps the last.
- **Drop the copied BMS and VMMS models now**: your choice over my recommendation (wait for feature 56). Nothing in VRMS uses them and each group owns its own database, so dropping is cleaner. What you accept: if feature 56 decides VRMS should hold them, they return as a new migration.
- **Outsourced shops as `OutsourcedShop` plus `OutsourcedJob`**: shops have no accounts (WL-402), so modelling them as mechanics was wrong. A job row per outsourcing keeps history if a ticket is sent twice and gives cost reports one table. Runner up: shop columns on the ticket.
- **One `LookupValue` table, parts separate**: the reason and location lists share one shape and one Settings hub screen; parts carry a price and feed `RepairPart`, so they get `Part`. Runner up: a table per list.
- **`dueAt` plus `dueAtSource`**: reports can split automatic from manual deadlines; which rule wins stays feature 42's call.
- **`lastActivityAt`**: `updatedAt` moves on every write, including the system's own escalations, which would reset the 30 day stale timer forever.
- **Python service left broken**: patching SQL in a service feature 3 deletes adds a third repo for throwaway code; its failures are already contained by the sample data fallback and the AI panel's error state.
- **Unassign deletes the assignment row**: open counts stay a plain count, and the audit event keeps who was removed and when. Runner up: keep rows with an `unassignedAt`, which every count query would then have to filter.
