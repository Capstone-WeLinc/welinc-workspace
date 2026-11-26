# Scheduling: reschedule filter, single actions, Subcon assignments: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

Three requests for the Scheduling page:

1. Add "Needs reschedule" to the status filter.
2. Drop the ⋮ menu when a row has only one action.
3. When the delivery type is Subcon, disable Garage, Vehicle and Driver on the Assign form and leave Helper as it is.

The third one is more than a UI change: the dispatch service refused any assignment without a garage, vehicle and driver, and job orders and distribution also required a driver.

## Options considered

### "Needs reschedule" filter

- **Same rule as the badge, and remove those rows from "Unassigned"** (chosen). Pros: what you filter by matches what the badge says. Cons: "Unassigned" filter count and the "Unassigned Bookings" KPI can differ.
- Same rule, but keep them under "Unassigned" too. Pros: no change to the Unassigned filter. Cons: rows badged "Needs reschedule" show under "Unassigned", which reads as a mismatch.

### Subcon

- **Web and backend** (chosen by the team). Grey out the fields and let the dispatch service save a Subcon assignment with only helpers. Pros: Subcon bookings can actually be assigned and go through job orders. Cons: touches the backend assignment rules.
- Web only. Pros: smallest change. Cons: every Subcon assignment would fail to save with "Complete dispatch time, garage, ...".

## Rationale

- The backend decides Subcon from the delivery type and ignores any garage, vehicle or driver sent with it, so a stale value from the form can never be saved against a Subcon booking.
- Helpers keep every existing check (role, status, leave, slot conflict, travel time) because they are still our people.
- The job order needs a truck and team label; "Subcon" and the helpers' names say who is going without inventing a plate or driver.
- Post-service, job order and distribution checks now accept a Subcon assignment without a driver, otherwise a Subcon booking would get stuck after assignment.
- The permit crew lock is unchanged: a permit filed under a truck and driver can't silently lose them by switching to Subcon.
- Single-action rows reuse the same icon and button size as the ⋮ trigger so the column stays aligned.
