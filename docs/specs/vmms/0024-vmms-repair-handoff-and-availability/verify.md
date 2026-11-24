# Verification

## VMMS backend

- [ ] Submit a Chief Mechanic `REPAIR` review and verify the schedule transition and referral outbox row commit atomically.
- [ ] Verify referral payload fields, stable idempotency ID, duplicate protection, and no attachment/cost leakage.
- [ ] Simulate network/timeout/5xx/429 responses; verify backoff and the configured maximum age. Verify non-retryable payload errors are surfaced.
- [ ] Verify manual retry is Admin-only and reuses the referral ID.
- [ ] Accept a referral into a new and existing ticket; verify ticket ID/number, status, and explicit schedule linkage.
- [ ] Reject a referral; verify only the referenced schedule returns to `IN_PROGRESS` / `REJECTED` with the VRMS reason.
- [ ] Cancel a ticket; verify the linked schedule remains open in `FOR_REPAIR`, the cancellation reason is visible, and the vehicle status is recalculated.
- [ ] Complete a ticket; verify linked schedules return to fresh Chief Mechanic verification and do not complete until normal VMMS approval.
- [ ] Verify status/history reads use the VMMS service identity, return explicit errors on unavailability, paginate history, and do not persist VRMS history.
- [ ] Verify costs are omitted for Mechanic and returned only to Admin, Operations, and Chief Mechanic.
- [ ] Verify mapped outsourced shops use the VMMS catalog name; unknown names cause no partial event update.
- [ ] Change a vehicle status from repair, maintenance, and Operations paths; verify one ordered outbox row per actual change and no event for a no-op.
- [ ] Simulate BMS unavailability and verify ordered retry, stable event IDs, and no rollback of the VMMS status change.
- [ ] With a BMS service token, read the VMMS garage and vehicle lists; verify only active, non-deleted fleet entries are returned and responses are not cacheable.
- [ ] Read an active vehicle immediately before assignment; verify status, `availabilityVersion`, and `isAssignable` reflect the current VMMS record. Verify `UNDER_REPAIR` and `UNDER_MAINTENANCE` are nonassignable and inactive, deleted, missing, or VMMS-error cases fail closed (inactive/deleted/missing detail IDs retain `404`).
- [ ] Create, materially update, deactivate, and soft-delete a vehicle and garage; verify one durable fleet-change event per actual change and none for a no-op. Verify events contain only invalidation metadata and BMS refreshes canonical VMMS reads.
- [ ] Make BMS fleet-change delivery unavailable; verify VMMS retains the outbox event and retries without rolling back vehicle/garage changes.
- [ ] Verify that a repair availability event during an active BMS delivery flags the active assignment for follow-up and blocks new assignment without changing BMS's `ON_DELIVERY` trip state.

## VMMS web and mobile

- [ ] Admin sees referral delivery status and can retry a failed referral; non-Admin callers cannot invoke retry.
- [ ] Chief Mechanic sees the linked ticket number/live status and VRMS rejection/cancellation reason; a rejected work order returns to the assigned Mechanic.
- [ ] Vehicle detail shows paged VRMS repair history, loading/empty/error states, and no stale-success fallback.
- [ ] Mobile sync stores additive referral metadata without losing pending work-order progress or existing snapshots.
- [ ] Mechanics can see permitted history fields but never repair-cost fields.

## Delivery evidence and external dependencies

- [ ] Run backend schema/build validation and web/mobile documented checks after implementation.
- [ ] Migration remains unapplied unless explicitly authorized.
- [ ] BMS implements the fleet-change receiver, refreshes the VMMS fleet snapshot, and blocks dispatch whenever its pre-assignment VMMS read fails.
- [ ] Obtain VMMS, VRMS, and BMS review of the proposed shared contract, auth grants, partner implementations, and integrated runtime evidence.

No automated or integrated check is marked complete until it is actually run.
