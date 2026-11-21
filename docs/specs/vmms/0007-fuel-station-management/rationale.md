# 0007. Fuel station management: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

Fuel stations are reused across fill-ups and statement imports. A station
may need to be renamed or removed from future entry choices without destroying
historical records.

The existing active-only station endpoint is already the selector contract.
Management needs a separate all-stations view and Operations-only mutation
boundaries.

## Options considered

### Option 1: Hard-delete stations

Delete a station and its related references when it is no longer used.

**Pros**:
- Smallest list and database surface.

**Cons**:
- Breaks or obscures fill-ups that reference the station.
- Makes historical labels dependent on mutable or unavailable records.

### Option 2: Deactivate, rename, and snapshot names (chosen)

Keep station rows, expose active and inactive rows to management, and store the
station name on each fill-up when it is created.

**Pros**:
- Preserves history and existing fuel IDs.
- Prevents inactive stations from entering future workflows.
- Allows reactivation and avoids accidental data loss.

**Cons**:
- Adds a station-name snapshot and migration/backfill.
- Active selectors and management lists need coordinated behavior.

### Option 3: Store station names only and remove station IDs

Treat stations as free text in all fuel entries.

**Pros**:
- Eliminates station relations and management state.

**Cons**:
- Loses controlled station matching and deactivation.
- Allows duplicate and misspelled station names.

## Rationale

Option 2 is consistent with the existing station relationship and preserves
history. Deactivation is a status transition, not deletion. A fill-up snapshot
keeps its historical label while station renames apply only to future entries.

Separate active-only and management endpoints keep existing selectors
compatible while giving Operations explicit control over the full station
catalog.
