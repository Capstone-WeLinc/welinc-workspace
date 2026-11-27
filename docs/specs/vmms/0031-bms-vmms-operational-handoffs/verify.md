# Verify: BMS–VMMS operational handoffs · spec 0031

Steps derived from [spec 0031 acceptance criteria](index.md). No implementation or runtime verification has been performed.

## Contract and authorization

- [ ] Confirm BMS service tokens require audience `VMMS`, client ID `bms`, and only the approved flow-specific scopes.
- [ ] Verify user tokens, wrong clients/audiences/scopes, unknown or inactive vehicles, malformed IDs, and oversized payloads are rejected with explicit errors.
- [ ] Verify no cross-system database access, caller-selected VMMS user identity, customer/route data, or arbitrary receipt URL is accepted.
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

## Flow F: fuel handoff

- [ ] Submit a valid BMS purchase and verify it is pending review and has not created a confirmed `FuelFillUp` or entered reports/efficiency.
- [ ] Verify Operations can approve a purchase only after it resolves to an active station through the explicit BMS-ID mapping; station-name similarity alone must not resolve it.
- [ ] Approve a purchase and verify the existing VMMS fuel creation path calculates its total, stores source/purchase/trip IDs and station snapshot, and audits the actual Operations actor.
- [ ] Reject a purchase and verify it remains excluded from the confirmed ledger, reports, and efficiency calculations.
- [ ] Verify unknown BMS station IDs remain pending until Operations maps them or rejects the submission.
- [ ] Verify possible matches to manual entries remain visible for Operations review; they are not silently discarded or double-counted.
- [ ] Verify invalid fields and invalid PHP amounts are explicitly rejected, and an omitted `isFullTank` is treated as false.
- [ ] Verify BMS purchase retries do not duplicate intake records; changed payload under the same idempotency ID is rejected.
- [ ] Verify manual VMMS fuel entry remains unchanged and is not subject to the BMS integration review queue.
- [ ] Verify receipt reference is never followed as a URL and no BMS file is fetched or copied.

## Integration runtime

- [ ] Run BMS and VMMS with the shared auth/gateway services in an authorized test environment and exercise transient failures, retry/backoff, duplicate delivery, receiver restart, and operator retry.
- [ ] Verify Operations-only screens, audit trail, notification/report behavior, and stale-data recovery in browser acceptance.
- [ ] Do not apply migrations, add auth grants, deploy, or contact partner groups without explicit authorization.

## Status

All checks remain pending until VMMS implementation is explicitly authorized, the BMS/shared-auth contract is reviewed, and the required test environment is available. The three flows are independently testable; none establishes suite-wide acceptance by itself.
