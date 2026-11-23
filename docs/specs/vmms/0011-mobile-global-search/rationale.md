# 0011. Mobile global search: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

The VMMS mobile header exposed a Global Search overlay backed by seven
hard-coded examples. Search matched only the sample title/category, and result
rows were not actionable. The mobile app already stores role-visible
maintenance schedules and vehicles in SQLite and loads notifications for the
signed-in user.

## Options considered

### Add a server-side global-search endpoint

Rejected for this slice. The mobile app already has the records needed for its
current workflows, including its offline snapshot. A new endpoint would add
cross-repository API work and would make offline search dependent on connectivity.

### Search the existing mobile data (chosen)

Search the current user's accessible schedules/work orders and loaded
notifications. Include a schedule's associated vehicle plate and model as
search terms, then use existing Work Orders and Notifications flows.

Advantages:

- Works from cached work-order data while offline.
- Reuses the app's role scoping and record workflows.
- Requires no new service, API, database table, or dependency.

Tradeoff: standalone vehicles without an accessible work order are not separate
results because the mobile app has no vehicle-detail screen. Their data is
searchable through associated work-order results.

## Smaller decisions

- Mechanics search only schedules assigned to themselves. Chief Mechanics
  search schedules supervised by themselves, matching the existing monitoring
  view; opening a result must use the same visibility boundary.
- Schedule results open their work-order detail. Notification results with a
  schedule ID use the existing notification-to-work-order path; other
  notifications open the Notifications screen.
- Search only uses fields already shown in those mobile workflows. It does not
  search profile credentials, arbitrary employee data, sensitive costs, or
  other systems.
- Query matching trims surrounding whitespace and ignores letter case.
- Recent queries are stored separately for Global Search and Work Orders,
  scoped to the signed-in account, and capped at 10 per surface. A query is
  saved on keyboard submission or result selection, not on every keystroke.
  Each Clear action erases only that surface's saved history; the input's
  separate clear control leaves history intact.
- Search history uses an additive local SQLite table. This keeps it available
  across app restarts and account sign-out/sign-in on the same device without
  adding a dependency or server-side data contract.
