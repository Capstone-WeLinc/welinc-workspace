# 0001. AI/Analytics Admin and Operations access

**Status**: Role decision approved; runtime verification pending
**Scope**: [Analytics, mobile synchronization, and release readiness](../../../scope/vmms/index.md#8-analytics-mobile-synchronization-and-release-readiness)

Decision history: [rationale.md](rationale.md). Verification plan: [verify.md](verify.md).

## Summary

Resolve the VMMS AI/Analytics access conflict in favor of Admin and Operations
access. Operations may use the AI/Analytics page and fleet analytics read
endpoints, consistent with the BRD role descriptions for fleet dashboards and
reports. Preserve the analytics API's Admin/Operations fleet-role guard.

## Source requirements and decision

- VMMS cross-cutting requirement FR-27.10 originally specifies Admin-only
  access to the AI/Analytics page.
- The BRD role descriptions include Operations in fleet dashboards and
  reports.
- **User decision (2026-11-25):** Admin and Operations may use AI/Analytics.
  This resolves the FR-27.10 role conflict for VMMS implementation.

## Behavior

- Admin and Operations can access the AI/Analytics navigation item and
  `/ai-analytics` route, including by direct URL.
- Fleet analytics read endpoints continue to use the API's `fleet` policy,
  which admits Admin and Operations and denies mobile-only roles.
- The analytics sync endpoint remains Admin-only.
- Existing assigned-work-order and assigned-AI endpoint policies do not
  change. The separate Operations-only maintenance-schedule prediction
  endpoint remains governed by [spec 0013](../0013-predictive-maintenance-readiness/index.md).
- The public health endpoint remains public for service readiness checks.

## Acceptance criteria

1. Admin and Operations can reach the AI/Analytics page through navigation and
   by opening `/ai-analytics` directly.
2. Analytics fleet-read endpoints allow Admin and Operations and deny Chief
   Mechanic and Mechanic roles.
3. The sync endpoint allows Admin and denies Operations and mobile-only roles.
4. Existing assignment checks and response filtering for work-order endpoints
   remain unchanged.
5. The separate maintenance-schedule prediction endpoint remains
   Operations-only.

## API, data, and migration impact

- No API, payload, database, or migration change is required. The existing
  analytics API fleet policy already allows Admin and Operations.
- No shared auth, portal, gateway, mobile, or cross-system change is included.

## Security and failure behavior

- Keep authorization enforced by the analytics API; web navigation and route
  behavior do not replace the server-side role guard.
- Return the existing authorization denial for roles outside a route's
  policy. Do not silently substitute sample or unrestricted analytics data.
- Do not broaden sync or assigned-work-order permissions as a side effect of
  granting Operations fleet analytics access.

## Affected repositories

- `docs/scope/vmms` and `docs/specs/vmms`: record the approved role
  interpretation and verification plan.
- `welinc-web-vmms` and `welinc-backend-vmms-analytics-ai`: existing
  navigation, route, and API policies appear to match this decision; no code
  change is required for the approved access behavior.

## Verification plan and status

Planned role and regression checks are listed in [verify.md](verify.md).
Runtime/API acceptance has not been run as part of this documentation update.
