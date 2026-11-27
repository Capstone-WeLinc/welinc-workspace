# Verify: BMS–VMMS operational handoffs · spec 0031

Steps derived from [spec 0031 acceptance criteria](index.md). No implementation or runtime verification has been performed.

## Contract and authorization

- [ ] Confirm BMS service tokens require audience `VMMS`, client ID `bms`, and only the approved flow-specific scopes.
- [ ] Verify user tokens, wrong clients/audiences/scopes, unknown or inactive vehicles, malformed IDs, and oversized payloads are rejected with explicit errors.
- [ ] Verify no cross-system database access, caller-selected VMMS user identity, customer/route data, or arbitrary attachment URL is accepted.
- [ ] Verify an identical retry returns the existing intake result; the same idempotency ID with changed content returns a conflict.
- [ ] Verify BMS retries transient failures using the approved schedule and does not retry other 4xx responses indefinitely.

## Flow D: trip odometer evidence

- [ ] Deliver a completed trip reading and verify it appears pending with BMS trip/source metadata while `Vehicle.odometer` and schedules remain unchanged.
- [ ] Confirm as Operations and verify master odometer audit and eligible schedule-state refresh use existing code paths.
- [ ] Dismiss as Operations and verify the master odometer remains unchanged with a review reason recorded.
- [ ] Verify stale/lower readings cannot overwrite a newer master; test equal readings, repeated deliveries, conflicting event IDs, and concurrent confirmations.

## Flow E: utilization

- [ ] Verify period bounds, trip count, distance, revision/idempotency, and vehicle ownership are validated.
- [ ] Verify the active VMMS-approved policy produces explainable suggestions with the period and evidence shown.
- [ ] Verify suggestions remain review-only and leave vehicle odometer, schedules, and work orders unchanged until an Operations user acts through existing maintenance workflows.
- [ ] Verify no scored/prioritized suggestion is produced while the policy is absent or disabled.
- [ ] Verify duplicate, corrected, late, empty, and out-of-order period summaries follow the agreed version rule.

## Flow F: pre-trip inspection defects

- [ ] Verify the assigned BMS driver completes the versioned checklist before dispatch and BMS retains the full answers, actor identity, and attachments.
- [ ] Verify a passing inspection remains in BMS and produces no VMMS defect event.
- [ ] Submit a failed inspection and verify the event contains only the agreed failed-item evidence and identifiers; no customer, booking, route, driver identity, or attachment content is copied to VMMS.
- [ ] Verify VMMS authenticates the exact BMS service identity, validates the vehicle and payload, and stores the report as pending Operations review.
- [ ] Retry the same event and verify idempotent acceptance; reuse the event ID with changed content and verify conflict.
- [ ] Confirm and dismiss defects as Operations; verify decision actor/reason are audited and confirmation does not automatically create a schedule/work order or change vehicle status.
- [ ] Verify a pre-trip odometer is not applied to `Vehicle.odometer`; completed-trip evidence still follows Flow D.
- [ ] After BMS/VMMS owners approve criticality rules, verify critical-failure dispatch blocking and any authorized override are enforced and audited by BMS.
- [ ] Verify BMS attachments remain in BMS and VMMS never follows arbitrary URLs or reads BMS storage.

## Integration runtime

- [ ] Run BMS and VMMS with the shared auth/gateway services in an authorized test environment and exercise transient failures, retry/backoff, duplicate delivery, receiver restart, and operator retry.
- [ ] Verify Operations-only screens, audit trail, notification/report behavior, and stale-data recovery in browser acceptance.
- [ ] Do not apply migrations, add auth grants, deploy, or contact partner groups without explicit authorization.

## Status

All checks remain pending until VMMS implementation is explicitly authorized, the BMS/shared-auth contract is reviewed, the critical-failure dispatch policy is agreed, and the required test environment is available. The three flows are independently testable; none establishes suite-wide acceptance by itself.
