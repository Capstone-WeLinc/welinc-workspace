# Roles and users

> Source: VMMS role guards in `welinc-backend-vmms`, the VMMS web/mobile
> boundaries, and workspace auth architecture; checked 2026-11-22. The
> detailed BRD/RTM permissions remain subject to the reconciliation in the
> [VMMS scope](../../scope/vmms/index.md).

VMMS uses four system roles from shared auth: `ADMIN`, `OPERATIONS`,
`CHIEF_MECHANIC`, and `MECHANIC`. A person may have roles in multiple systems;
VMMS authorization must check the VMMS role, not just a role name from another
system.

| Role | Main VMMS responsibilities | Typical client |
|---|---|---|
| **Admin** | Management access, configuration and review actions explicitly guarded for Admin | Web |
| **Operations** | Vehicle/fleet records, schedule administration, fuel operations, and management reporting | Web |
| **Chief Mechanic** | Review assigned mechanics' submitted work and use permitted mechanic workflow views | Shared mobile app |
| **Mechanic** | View and progress assigned maintenance work, submit checklist/evidence, and use permitted mechanic views | Shared mobile app |

The web app admits Admin and Operations accounts. Mechanics and Chief
Mechanics use the shared mobile app. The client navigation is not an
authorization boundary: backend route guards enforce the role and assignment
rules.

Account lifecycle and sign-in are shared-service responsibilities. VMMS
consumes authenticated identities and VMMS roles; it does not own a duplicate
account store or account-administration workflow.

For exact access on a particular feature, use its controller guards and the
linked VMMS specification rather than inferring permissions from this
high-level summary.
