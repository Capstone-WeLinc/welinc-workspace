# 0002. Restrict VMMS business audit logs to Admin

**Date**: 2026-11-19
**Status**: Implemented; API authorization and builds verified; manual acceptance pending
**Scope**: [Module 7: Reports and fleet dashboard](../../../scope/vmms/index.md)

Decision history (context, options, rationale): [rationale.md](rationale.md). Verification steps: [verify.md](verify.md).

## Summary

Restrict the VMMS business audit log to Admin. Operations, Chief Mechanic, and Mechanic must not access the page or its API, including through a direct URL or direct request. This is separate from authentication and account activity, which is owned by shared auth and the portal.

## Rationale

The audit log is an oversight surface, not an Operations workflow. Admin-only access applies least privilege and separates operational changes from their review. Operations continues to use the normal VMMS workflows for its business records.

The existing VMMS integration guide says other roles may see business audit rows. This policy decision supersedes that guidance; it must be aligned through the shared-document review process before the guide is treated as current.

## Requirements and decision

- **RTM FR-03.2** explicitly limits the recent login-activity log to Admin. It does not itself specify access to VMMS business audit rows.
- **BRD SC-16** requires system actions to be logged; it does not define who may read the VMMS business audit feed.
- **Existing integration guidance** says non-Admins see business rows only.
- **User decision (2026-11-19)**: extend Admin-only access to the VMMS business audit feed.

## Behavior

- The VMMS web Audit Logs navigation item is visible only to Admin.
- A non-Admin opening `/audit-logs` is redirected to `/dashboard`.
- The VMMS backend authorizes `GET /vmms/audit-logs/business` for Admin only. Operations and mobile-only roles receive the existing authorization denial.
- Response shape, business-event selection, ordering, and retention do not change.
- Authentication/login activity remains in shared auth and the portal; this change does not add those records to the VMMS business audit page.

## Acceptance criteria

1. Admin can open the web Audit Logs page and load business audit records.
2. Operations does not see the Audit Logs navigation item and is redirected when opening `/audit-logs` directly.
3. An Operations request to `GET /vmms/audit-logs/business` is denied by the backend, independent of client-side navigation.
4. Chief Mechanic and Mechanic remain denied by both the web application and backend.
5. Existing Admin audit results and response shape are unchanged.
6. The portal remains the UI for login and account activity; its access behavior is unchanged.

## API, data, and migration impact

No route, payload, database, or migration changes. Tighten the existing backend role guard and keep the existing response contract.

## Security and failure behavior

The backend role guard is authoritative. Hiding navigation or redirecting a route is supplemental only. Unauthorized API requests use the repository's existing `RolesGuard` denial behavior; do not return business audit data as a success-shaped empty result.

## Affected repositories

- `welinc-backend-vmms`: enforce Admin-only access on the business audit controller.
- `welinc-web-vmms`: show and route the page for Admin only.

The shared integration guide is not changed in this implementation because it is a shared workspace file and requires the spec-first pull-request process. Its current Operations-access statement remains to be reconciled in that review.

## Verification plan

- Build the VMMS backend and web app.
- Check the role matrix for Admin, Operations, Chief Mechanic, and Mechanic at both the direct web route and API boundary.
- Confirm the web page still consumes only business audit records and that shared portal login-activity access is unchanged.
