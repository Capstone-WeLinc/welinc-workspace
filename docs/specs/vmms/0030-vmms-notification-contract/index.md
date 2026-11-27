# 0030. VMMS notification contract

**Status**: Proposed VMMS contract; other system adoption requires owner review  
**Scope**: System-owned in-app notifications and their web/mobile inboxes

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Define a compatible notification envelope and user-inbox behavior for suite systems without centralizing notification ownership or storing another system's data. Each system remains responsible for creating, authorizing, persisting, and presenting its own notifications. This proposal does not add a shared notification service.

## Sources and ownership

- Suite ownership and independent databases in [suite overview](../../../context/suite-overview.md).
- System-specific notification requirements remain in each system's scope and requirements.
- This contract proposal does not authorize edits to another group's repositories or changes to shared auth, portal, gateway, or push/SMS providers.
- The VMMS implementation slice is specified in [VMMS spec 0029](../0029-notification-enhancement-and-completion/index.md).

## Proposed contract

- A notification belongs to one system and one authenticated user. Its producer chooses eligible recipients using that system's role and workflow rules.
- A notification carries a stable category, display title and message, severity, creation time, read state, and an optional typed action target.
- Action targets are identifiers and allow-listed target types, not arbitrary URLs. The client maps a known target type to a route already protected by that system's authorization.
- Inbox reads are bounded and stably ordered. Pagination cursors are opaque and bound to the query/source state; counts are user-scoped.
- Mark-read and mark-all-read operate only on the authenticated user's records and are idempotent.
- Producers deduplicate retried events with a stable key or an atomic source-state transition.
- Systems retain their own notification database and API. Cross-system event notifications require an explicitly documented API and must not read another system's database.
- In-app notification delivery does not imply push or SMS delivery.

## Acceptance criteria

1. System ownership and role-scoped recipient selection remain with each system; no shared notification database or cross-system reads are introduced.
2. System implementations can expose the common envelope and bounded inbox semantics without exposing persistence details.
3. Clients navigate only through allow-listed target types and still rely on normal route/API authorization.
4. Duplicate event delivery does not create duplicate notifications when the producer has an idempotency key.
5. Push, SMS, and a centralized notification provider remain out of scope.

## API, data, and security impact

- This is a proposed compatibility contract, not a shared API or schema migration.
- Each system may add system-owned fields and endpoints while preserving the envelope, user scope, and pagination guarantees.
- No shared service, identity, gateway, or partner API change is authorized by this document.

## Affected repositories

- `welinc-backend-vmms`, `welinc-web-vmms`, and VMMS flows in `welinc-mobile-vrms_vmms` implement the VMMS slice in spec 0029.
- Other system repositories are not changed. Adoption by VRMS or BMS requires their owners' review and implementation.

## Delivery status

This VMMS contract is proposed. Implementation and evidence are tracked separately in [spec 0029](../0029-notification-enhancement-and-completion/index.md). It does not claim adoption by VRMS, BMS, or shared services.
