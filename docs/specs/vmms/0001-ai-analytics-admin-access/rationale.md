# Rationale — 0001 AI/Analytics Admin and Operations access

## Context

VMMS scope recorded a conflict between FR-27.10, which says the AI/Analytics
page is Admin-only, and BRD role descriptions that include Operations in
fleet dashboards and reports. The current web navigation includes Analytics
for Operations, the web application admits Admin and Operations, and the
analytics API's default fleet policy also admits those two roles.

The user resolved the conflict on 2026-11-25 in favor of Admin and Operations
access and asked to preserve the API fleet-role guard.

## Forces

- Operations uses fleet dashboards and reports as part of its VMMS role.
- Analytics remains a derived read surface and must not become an alternative
  authorization authority.
- Fleet-wide analytics should remain unavailable to mobile-only roles.
- Granting Operations read access must not grant Admin-only sync or change
  assignment-scoped work-order access.
- Schedule-specific odometer predictions have their own Operations-only
  contract in spec 0013.

## Options considered

1. **Keep the page Admin-only.** This would retain FR-27.10 literally but
   conflict with the BRD role descriptions and require removing existing
   Operations navigation/API access.
2. **Allow Admin and Operations (chosen).** Aligns analytics with the
   management-facing dashboard/report role descriptions and the existing
   API fleet policy.

## Approved decision

Allow Admin and Operations to use the web AI/Analytics page and fleet
analytics read endpoints. Treat the user's decision as the resolution of the
FR-27.10 conflict for VMMS implementation and record it in the VMMS scope.

Keep the API authorization boundaries otherwise unchanged:

- Fleet analytics reads use the Admin/Operations `fleet` policy.
- Manual analytics sync remains Admin-only.
- Work-order detail and AI advisory endpoints retain their existing
  assignment policies.
- The separate maintenance-schedule prediction endpoint remains
  Operations-only.
- Public health checks remain public.

## Tradeoffs

- **Benefits:** Operations retains the analytics needed for its fleet
  oversight role; the UI and API policy remain aligned.
- **Costs/risks:** Operations can see fleet-level analytics, so route and API
  role acceptance must confirm that no mobile-only role can reach those
  endpoints.
- **Excluded:** changing sync permissions, changing work-order assignment
  rules, changing the schedule prediction contract, and changing shared
  identity or gateway behavior.

## Remaining source alignment

The decision is recorded in VMMS-owned scope and specification documents.
If the original BRD/RTM source files are supplied in the workspace later,
their FR-27.10 wording should be updated to match this approved decision.
