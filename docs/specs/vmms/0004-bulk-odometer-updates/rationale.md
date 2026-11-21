# 0004. Bulk odometer updates and schedule refresh: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

Vehicle odometer updates affect maintenance schedule state, but schedule rows
also contain their own reference readings, intervals, buffers, and thresholds.
These values serve different purposes and must not be rewritten when a new
master reading arrives.

Operations also needs to catch up multiple vehicles efficiently. A bulk import
must preview all intended changes, identify bad rows, and allow valid rows to
succeed independently.

## Options considered

### Option 1: Add odometer editing to every maintenance schedule

Let Operations edit a live reading or threshold on each schedule.

**Pros**:
- Simple to expose on an existing schedule screen.
- Gives one schedule immediate control.

**Cons**:
- Duplicates the vehicle master reading.
- Makes schedules disagree with the authoritative vehicle snapshot.
- Changes thresholds instead of deriving schedule state from a master update.

### Option 2: Recalculate schedules from the vehicle master (chosen)

Keep one master odometer write path, and recalculate eligible schedule states
after each update without changing schedule configuration.

**Pros**:
- Uses one source of truth.
- Preserves intervals, buffers, due thresholds, and reference readings.
- Keeps maintenance workflow states separate from odometer-derived status.

**Cons**:
- Requires central state derivation and transaction handling.
- Large reading jumps can affect several schedules at once.

### Option 3: Add spreadsheet writes without preview or row isolation

Apply workbook rows directly and reject the batch on one error.

**Pros**:
- Least UI and API work.

**Cons**:
- No review of plate matches or stale values.
- One bad row can block unrelated valid vehicles.
- Partial success is ambiguous to Operations.

## Rationale

Option 2 plus the spreadsheet preview/save flow preserves data ownership and
provides actionable fleet-wide updates. Bulk save uses the same validation and
transaction logic as the single-vehicle operation, preventing two inconsistent
odometer write paths.

Default interval and buffer values are copied to schedules when resolved. Later
changes affect future schedules only, because existing thresholds and workflow
states must remain stable unless a reading update changes their derived state.
