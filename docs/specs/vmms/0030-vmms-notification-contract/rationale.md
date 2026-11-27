# Rationale

Decision record for [index.md](index.md).

## Context

The suite overview identifies notifications and the mobile app as shared concerns, while each system owns its own database, roles, workflow, and deployment. Existing VMMS notifications are split between schedule-specific and general tables; this work needs a common client envelope without moving ownership to a shared service.

## Options considered

### Central notification service

Rejected for this slice. It would create a new cross-system dependency, identity/data contract, deployment, and delivery owner that the current suite does not have.

### Keep notifications entirely system-specific with no common contract

Rejected. It preserves ownership but leaves clients and future system integrations to invent incompatible action, pagination, and read-state behavior.

### System-owned persistence with a shared envelope (proposed)

VMMS continues owning its notifications and exposes an authenticated-user inbox. Clients resolve typed action targets locally. The approach is additive and does not create cross-system database coupling; other systems may assess the proposal independently.

## Decisions and constraints

- Treat this as a VMMS proposal; other systems must review and adopt it explicitly before relying on it.
- Keep recipient decisions server-side and tied to the owning system's current roles and workflow.
- Do not serialize arbitrary external URLs into action targets.
- Preserve system-local notification history and idempotency.
- Keep push and SMS out of scope absent a separate product/security decision.
- VMMS implements only its own slice; VRMS/BMS are not presumed to support VMMS routes or target types.
