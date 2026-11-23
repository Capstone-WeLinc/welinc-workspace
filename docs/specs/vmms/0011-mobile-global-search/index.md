# 0011. Mobile global search

**Status**: Implemented; device-level acceptance pending  
**Scope**: [Cross-cutting mobile synchronization](../../../scope/vmms/index.md#8-analytics-mobile-synchronization-and-release-readiness)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Replace the VMMS mobile app's sample-only Global Search with a role-scoped
search of its existing maintenance work and notification content. Search runs
against the local SQLite snapshot and the signed-in user's loaded notifications,
and results open the corresponding existing mobile workflow.

## Sources and decisions

- User request to search actual mobile app content and open its workflow.
- User selected the recommended scope: accessible maintenance schedules/work
  orders, associated vehicle details, and notifications.
- VMMS scope FR-28.1–28.3 establishes the mobile SQLite snapshot and offline
  synchronization model. No existing BRD/RTM requirement specifically covers
  Global Search; this is a VMMS-scoped mobile extension.

## Behavior and controls

- Search non-deleted maintenance schedules visible to the signed-in role:
  assigned schedules for a Mechanic and chief-supervised schedules for a Chief
  Mechanic. Include the associated vehicle plate and model as searchable text.
- Search notifications already loaded for the signed-in user. Do not query
  employee directories, profile secrets, another system, or unscoped fleet data.
- Trim query whitespace and compare case-insensitively against visible
  work-order/schedule fields and notification message/type.
- A work-order result opens that schedule in the existing Work Orders detail
  workflow. A notification with a schedule opens its associated work order;
  other notifications open the Notifications screen.
- Show separate recent-query histories for Global Search and the Work Orders
  search. Persist up to 10 queries per signed-in account and search surface in
  the local SQLite database. Record a query on keyboard submission or result
  selection, not on each keystroke. Selecting a history item reuses that query.
- Each history has a Clear action; it removes saved queries without changing
  the current search text. A separate input control clears only that text.
- Use cached work orders while offline. Show loading, empty, and data-load
  failure states explicitly; never substitute sample results on failure.
- No backend API or server database change is introduced. Search history uses
  an additive local SQLite table created on demand.

## Acceptance criteria

1. Search results come from current mobile VMMS content rather than fixtures.
2. Results are limited to the caller's existing work-order visibility and
   current-user notifications; vehicle fields are searchable only through an
   accessible associated schedule.
3. Matching is case-insensitive and ignores leading/trailing query whitespace.
4. Selecting a result routes to its existing work-order or notification
   workflow without granting new record access.
5. Empty queries, no matches, loading, and data-read failures have clear,
   distinct UI states.
6. Automated coverage verifies role scoping, real record construction, query
   normalization, and result routing.
7. Global Search and Work Orders each show their own recent searches, scoped to
   the signed-in account, and support clearing history independently of the
   current query.

## Impact

- `welinc-mobile-vrms_vmms`: global search data, result actions, and focused
  mobile tests, plus per-account local search history for Global Search and
  the Work Orders search.
- No backend, analytics, shared-auth, API, or persistence changes.

## Implementation and verification status

The mobile implementation is complete. The focused search/history tests,
TypeScript check, and ESLint checks passed. Device-level online/offline and
history persistence acceptance remain unverified; the full mobile suite was
not run because its known login/reset-password failures are outside this
search change.
