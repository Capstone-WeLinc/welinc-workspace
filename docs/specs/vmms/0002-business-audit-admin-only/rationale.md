# 0002. Restrict VMMS business audit logs to Admin: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

VMMS needs an audit record of business actions, but the audit feed is an
oversight surface rather than an Operations workflow. Shared services own login
activity and account-change auditing. The VMMS business audit is therefore
separate and must not be confused with shared authentication records.

The existing integration guidance allowed non-Admins to see business audit
rows. VMMS requirements do not clearly authorize that exposure, and the current
role model gives Operations, Chief Mechanic, and Mechanic operational duties that
do not require an oversight feed.

## Options considered

### Option 1: Keep the existing role access

Continue allowing the roles described by the integration guide to view VMMS
business audit rows.

**Pros**:
- Avoids a route and role-policy change.
- Preserves the current UI and API behavior.

**Cons**:
- Broader access than the requested oversight policy.
- Leaves a role boundary inconsistent with the Admin-only policy.

### Option 2: Restrict business audit rows to Admin (chosen)

Hide the navigation item and route from non-Admins, and enforce an Admin-only
backend role guard on the existing business audit endpoint.

**Pros**:
- Applies least privilege to an oversight-only feed.
- Needs no payload, database, migration, or route shape changes.
- Keeps shared login and account audit access in the portal.

**Cons**:
- Some existing integration guidance becomes outdated until it is reconciled.
- Client redirect behavior alone is insufficient; the API guard is still
  required.

## Rationale

Option 2 is the smallest policy change that closes an unauthorized read path.
Navigation hiding and route redirection improve UX, while the backend role guard
provides the actual security boundary.

The existing audit endpoint and response contract remain unchanged. Login and
account-change activity stay owned by shared auth and the portal; this spec
does not duplicate or extend that feature inside VMMS.
