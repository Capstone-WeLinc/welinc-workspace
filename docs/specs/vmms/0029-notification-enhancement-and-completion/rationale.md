# Rationale

Decision record for [index.md](index.md).

## Context

VMMS currently persists schedule-specific notifications in `maintenance_notifications` and role-wide alerts in `notifications`. Web reads only the general table, while mobile fetches both sources independently and filters general events by title. The general list has no bound, and neither client can mark all read. Web hides fetch and read errors; mobile has a refresh error but uses client-derived unread counts from only loaded items.

VMMS owns the notifications in its database and derives recipients from VMMS roles. The mobile repository is shared with a future VRMS flow, so this implementation must remain within VMMS screens and behavior.

## Options considered

### Merge persistence tables

Rejected. It would require migrating existing read state, schedule uniqueness, and relationships without a user-visible benefit.

### Retain two client APIs and merge in each client

Rejected. It duplicates source mapping, pagination, counts, and read behavior and is already inconsistent between web and mobile.

### Keep source tables and unify the API (chosen)

The backend queries each source with per-source keyset cursors, merges a bounded page in stable order, and returns a source discriminator for read actions. Existing routes remain during client migration.

**Tradeoff**: the opaque cursor must retain independent continuation state for both tables, and count queries touch both sources.

### Store arbitrary route URLs

Rejected. Arbitrary URLs create unsafe navigation and put route compatibility in persisted data.

### Persist typed action targets (chosen)

Persist target type and optional record ID; clients map known types to local routes. Current permissions continue to govern target access.

**Tradeoff**: adding metadata requires an additive database migration and careful backfill. Old notifications without a recoverable target remain non-actionable.

## Decisions

- Preserve the existing due/overdue/odometer/fuel/report producers, recipients, and thresholds.
- Dedupe notification-producing events with stable keys; stateful staged delivery continues using its atomic claim and transaction.
- Keep the legacy APIs until all known VMMS callers use the unified inbox.
- Use server-provided unread counts instead of assuming the loaded page contains all unread records.
- Preserve loaded inbox data after a request failure and offer explicit retry.
- The VMMS envelope is proposed in [spec 0030](../0030-vmms-notification-contract/index.md); VMMS is the only implementation in this task.
- No push, SMS, new third-party provider, or workflow-engine behavior is introduced.
