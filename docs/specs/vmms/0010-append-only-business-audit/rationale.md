# 0010. Append-only business audit: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

VMMS business history is stored in several existing tables and combined for
Admin review. Most rows describe immutable facts, but cancellation requests
and edit-unlock records are workflows whose review/consumption fields change.
Identity erasure also rewrites stored actor display names and emails.

## Options considered

### Migrate to one canonical event store

**Rejected for this slice**: requires broad backfill and coordinated changes
to every audit writer and reader.

### Protect existing immutable event tables (chosen)

Keep domain tables, reject ordinary mutation/deletion in PostgreSQL, permit
only the existing identity-redaction operation, and annotate the unified read
projection with categories.

**Advantages**:
- Enforces immutability below ORM/service code.
- Avoids copying historical data or changing event writers.
- Retains identity erasure and current Admin visibility.

**Tradeoff**: mutable review workflows cannot be immutable event tables
without a separate transition-event model, so they remain explicitly
categorized workflow records.

### Application-only write convention

**Rejected**: raw SQL, cascades, or a future code path could still alter or
erase event history.

## Smaller decisions

- Enforce delete protection in the database and prevent audit-child cascades
  with restrictive foreign keys.
- Allow only the known erased actor display/email markers to be updated.
- Keep current event table identities and Admin endpoint; add a backward-
  compatible category field.
