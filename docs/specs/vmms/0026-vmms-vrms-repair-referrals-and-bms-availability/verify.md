# Verification

## Contract and VMMS acceptance

- [ ] Submit a `For Repair` work order and verify one referral is queued with vehicle ID/plate, work-order ID/number, failed inspection findings, remarks, and odometer → referral AC.
- [ ] Make VRMS unreachable; verify retries use the same referral ID and increasing delays, stop after the configured age, and expose `Couldn't reach VRMS` → retry AC.
- [ ] As VMMS Admin, manually retry a failed referral and verify the same referral ID is reused → retry AC.
- [ ] Accept a referral into a new VRMS ticket and into an existing ticket; verify the ticket number and status are linked to only the relevant VMMS work order → referral AC.
- [ ] Reject a referral with a reason; verify the assigned mechanic sees the VRMS reason and the work order returns to `IN_PROGRESS` / `REJECTED` → outcome AC.
- [ ] Cancel a VRMS ticket; verify linked VMMS work remains open in `FOR_REPAIR` and the Chief Mechanic sees the cancellation reason → terminal AC.
- [ ] Complete a VRMS ticket; verify the linked work order is returned to `DONE` / `UNVERIFIED` for a new Chief Mechanic inspection, not completed by the event → terminal AC.
- [x] Unit-test VMMS service-side ticket status/history reads, cursor/limit handling, explicit failures, and role-based cost filtering → read and authorization AC.
  Evidence: `vrms-repair-reads.service.spec.ts` passes nine tests. It verifies current ticket status requests, bounded pagination, unavailable/missing-record responses, costs for Admin/Operations/Chief Mechanic, and cost omission for Mechanic.
- [x] Unit-test referral persistence/delivery, retry/manual retry, accepted-ticket linking, and rejection idempotency → referral and outcome AC.
  Evidence: `vrms-repair-referrals.service.spec.ts` passes six focused tests; `vrms-repair-events.service.spec.ts` passes three focused tests for ticket acceptance, rejection state changes, and duplicate/conflicting events.
- [ ] Verify live VRMS responses and the authenticated HTTP boundary; confirm no repair-history copy is persisted in VMMS → read and authorization AC.
- [ ] Send an outside-shop status whose name matches an active VMMS provider; verify the VMMS catalog name is shown. Send an unknown name and verify a conflict with no partial state change → provider AC.
- [x] Unit-test BMS availability event creation, versioned payload, retry identity/backoff, and ordering → availability AC.
  Evidence: `bms-availability.service.spec.ts` passes six tests for versioned outbox event creation, payload delivery, retries using the same event ID, and blocking later versions while an earlier event remains pending.
- [ ] Change a vehicle status through repair, maintenance, and Operations paths; verify one ordered BMS event per actual status transition, durable retry, and no BMS event for a no-op → availability AC.
- [ ] Verify a service token from the intended client/audience/scope succeeds and a user token, wrong client, audience, or missing scope is denied → security AC.

## VMMS-only delivery evidence

- [x] Backend build and Prisma schema validation; six focused integration suites pass 58 tests.
- [x] Web build, targeted vehicle-history ESLint, and repair-history state test pass.
- [x] Mobile lint and focused work-order test pass.
- [ ] Mobile typecheck/build and clean full web/mobile checks; the full web lint currently reports eight errors and one warning, and the mobile full test suite has three failures in two suites (details in spec 0024 verification).
- [ ] Apply migrations only in an explicitly authorized test/development database; no migration is applied by this spec.

## Cross-system evidence still required

- [ ] VMMS, VRMS, and BMS owners review and accept this proposed contract.
- [ ] Shared auth grants the proposed service scopes to `vmms` and `vrms`.
- [ ] VRMS implements referral intake, outcome/status events, and service status/history APIs.
- [ ] BMS implements and acknowledges vehicle-availability events.
- [ ] Integrated deployment verifies retry, callback, status precedence, trip/job-order follow-up, and notification behavior.

No cross-system or runtime acceptance is claimed until these dependencies exist.
