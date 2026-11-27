# 0029. VMMS notification enhancement and completion

**Status**: VMMS implementation complete; migration and integrated acceptance pending  
**Scope**: [Maintenance scheduling and alerts](../../../scope/vmms/index.md#3-maintenance-scheduling-and-alerts), [Work orders, checklists, and maintenance history](../../../scope/vmms/index.md#4-work-orders-checklists-and-maintenance-history), and [Fuel expenses and anomaly handling](../../../scope/vmms/index.md#5-fuel-expenses-and-anomaly-handling)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Complete the VMMS in-app notifications flow across the core API, web inbox, and VMMS mobile screens. Keep the existing general and maintenance-specific tables and producers, expose a unified bounded inbox, persist typed action targets, make read state reliable, and retain existing role and escalation behavior. This implements the VMMS slice of proposed [VMMS notification contract 0030](../0030-vmms-notification-contract/index.md).

## Sources and decisions

- VMMS requirements FR-09.1–09.2 and notification behavior documented in [VMMS scope](../../../scope/vmms/index.md).
- Existing approved maintenance notification and escalation behavior in [spec 0012](../0012-maintenance-scheduling-completion/index.md).
- Fuel anomaly notification and staged escalation behavior in the Module 5 scope and existing VMMS fuel services.
- VMMS role, database, and service ownership in [workspace AGENTS.md](../../../../AGENTS.md) and [suite overview](../../../context/suite-overview.md).
- Decisions for this slice:
  - In-app only; Semaphore SMS remains excluded and no push provider is introduced.
  - Keep `notifications` and `maintenance_notifications`; unify them at the API boundary.
  - Only the authenticated user's records are returned or changed.
  - Use bounded keyset pagination across both sources and stable ordering; clients cannot choose recipients.
  - Persist category and typed action metadata for general notifications. Do not store arbitrary navigation URLs.
  - Existing notifications remain available through legacy routes while web/mobile migrate to the unified inbox.

## Behavior

### Sources, roles, and actions

| Source/event | Recipients | Category | Action |
|---|---|---|---|
| Maintenance assignment, due, overdue, odometer threshold | Assigned active Mechanic | `MAINTENANCE` | Open the existing schedule/work-order surface |
| Maintenance overdue day 1, day 3, day 7 | Chief Mechanic; Admin/Operations; all eligible roles respectively | `MAINTENANCE` | Open schedule/work order |
| Fuel anomaly detected | Admin and Operations | `FUEL` | Open Fuel Management |
| Fuel anomaly staged day 1/day 3/day 7 | Chief Mechanic; Admin/Operations; all eligible roles respectively | `FUEL` | Open Fuel Management |
| Daily/monthly scheduled fleet report | Admin and Operations | `REPORT` | Open the relevant reports surface |
| Existing general notification without a typed target | Existing producer-selected user | Producer category or `GENERAL` | No action |

Recipients are selected server-side using active, non-deleted identities and non-temporary roles, matching existing producers. This slice does not change alert thresholds or workflow decisions. Notification navigation never grants permission to the target record.

### Unified inbox contract

- `GET /notifications/inbox` accepts an optional opaque cursor, `limit` (default 30, maximum 100), category, and read-state filter.
- Return `{ items, nextCursor, counts }`; each item contains `id`, `source`, `category`, `title`, `message`, `severity`, `isRead`, `createdAt`, and an optional `{ type, id }` action target.
- The cursor tracks continuation independently for the general and maintenance tables so merging does not skip rows. Query filters are reset when changed.
- `PATCH /notifications/inbox/:source/:id/read` marks one owned item read. `PATCH /notifications/inbox/read-all` marks all eligible owned items read. Repeated calls are safe.
- Existing `GET /notifications`, `PATCH /notifications/:id/read`, and maintenance notification routes remain compatible for unmigrated callers.
- Stale schedule actions remain in history but cannot expose deleted/unassigned work; normal route/API authorization still applies.

### Web and mobile

- Web and mobile use the unified inbox; show accurate server unread counts, loading/error/empty states, retry, read state, and bounded continuation.
- Web supports category/read-state filtering and mark-all-read. Its bell/modal remains the entry point.
- Mobile supports pull-to-refresh, unread count, continuation, per-item/read-all actions, and account-switch isolation. Critical fuel acknowledgment remains a separate workflow action.
- Action targets are allow-listed by clients. Unknown or absent actions remain non-navigable.

## Acceptance criteria

1. A user can only read or update notifications addressed to their authenticated VMMS identity.
2. The unified inbox combines both notification sources with stable ordering, bounded pagination, category/read filters, and accurate unread counts.
3. Cursor navigation covers every eligible source row once, including timestamp ties; malformed cursors and invalid limits/filters are rejected.
4. Mark-one-read and mark-all-read are idempotent and do not update another user's or a reassigned/deleted schedule notification.
5. Existing producer recipient rules and staged escalation timings remain intact; duplicate scheduled events do not create duplicate notifications.
6. General notifications carry a stable category and optional typed action; arbitrary URLs are never stored or followed.
7. Web presents readable loading, error/retry, empty, unread, filtered, and continuation states; action routing is limited to known VMMS targets.
8. Mobile presents the same merged event stream, server unread count, refresh/continuation, reliable read/read-all behavior, and account isolation.
9. Fuel anomaly acknowledgment remains separate from notification read state; existing critical approval role rules are unchanged.
10. SMS and remote push are not added. No shared auth, portal, gateway, analytics, VRMS, or BMS implementation is changed.

## API, data, and migration impact

- Add category, target type, and target UUID fields to the general `Notification` model with safe defaults for existing rows.
- Add a migration that backfills categories and schedule action targets where known; do not apply it without authorization.
- Add unified inbox, mark-one-read, and mark-all-read routes; retain legacy routes.
- Update VMMS web/mobile callers and existing VMMS producers to populate stable category/action metadata and dedupe keys.

## Security and failure behavior

- Derive user identity from the authenticated JWT; do not accept user IDs in request bodies or query parameters.
- Scope every read, count, update, and cursor query to that identity and assigned active schedule relationship.
- Validate page size, cursor structure, category, read filter, source, and UUIDs. Return explicit errors and never silently substitute an unfiltered query.
- Preserve prior inbox items when refresh fails; show a retryable error.
- Deep links are typed local actions and do not replace backend permission checks.

## Affected repositories

- `welinc-backend-vmms`: inbox API, database migration, recipient/dedupe metadata, and tests.
- `welinc-web-vmms`: unified inbox and bell/modal improvements.
- `welinc-mobile-vrms_vmms`: VMMS notification service and screen only; do not change VRMS behavior.
- No analytics service, auth, portal, gateway, or other-system repository changes.

## Delivery status

The VMMS-owned implementation across the backend, web, and mobile code is complete. The schema migration remains unapplied unless separately authorized. Automated checks and remaining live/browser/device acceptance are recorded in [verify.md](verify.md).
