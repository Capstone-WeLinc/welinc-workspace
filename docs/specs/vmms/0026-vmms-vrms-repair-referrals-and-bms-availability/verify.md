# Verification

## Contract and VMMS acceptance

- [ ] Submit a `For Repair` work order and verify one referral is queued with vehicle ID/plate, work-order ID/number, failed inspection findings, remarks, and odometer → referral AC.
- [ ] Make VRMS unreachable; verify retries use the same referral ID and increasing delays, stop after the configured age, and expose `Couldn't reach VRMS` → retry AC.
- [ ] As VMMS Admin, manually retry a failed referral and verify the same referral ID is reused → retry AC.
- [ ] Accept a referral into a new VRMS ticket and into an existing ticket; verify the ticket number and status are linked to only the relevant VMMS work order → referral AC.
- [ ] Reject a referral with a reason; verify the assigned mechanic sees the VRMS reason and the work order returns to `IN_PROGRESS` / `REJECTED` → outcome AC.
- [ ] Cancel a VRMS ticket; verify linked VMMS work remains open in `FOR_REPAIR` and the Chief Mechanic sees the cancellation reason → terminal AC.
- [ ] Complete a VRMS ticket; verify the linked work order is returned to `DONE` / `UNVERIFIED` for a new Chief Mechanic inspection, not completed by the event → terminal AC.
- [ ] Request ticket status and vehicle repair history from VMMS; verify current VRMS response, cursor paging, and no VMMS copy of repair issues/parts/costs → read AC.
- [ ] Verify repair-cost fields are present for Admin, Operations, and Chief Mechanic and absent for Mechanic at the backend boundary → authorization AC.
- [ ] Send an outside-shop status whose name matches an active VMMS provider; verify the VMMS catalog name is shown. Send an unknown name and verify a conflict with no partial state change → provider AC.
- [ ] Change a vehicle status through repair, maintenance, and Operations paths; verify one ordered BMS event per actual status transition, durable retry, and no BMS event for a no-op → availability AC.
- [ ] Verify a service token from the intended client/audience/scope succeeds and a user token, wrong client, audience, or missing scope is denied → security AC.

## VMMS-only delivery evidence

- [ ] Backend build and Prisma schema validation after implementation.
- [ ] Web build after implementation.
- [ ] Mobile type/lint/build checks after implementation using the repository's Expo SDK 56 toolchain.
- [ ] Apply migrations only in an explicitly authorized test/development database; no migration is applied by this spec.

## Cross-system evidence still required

- [ ] VMMS, VRMS, and BMS owners review and accept this proposed contract.
- [ ] Shared auth grants the proposed service scopes to `vmms` and `vrms`.
- [ ] VRMS implements referral intake, outcome/status events, and service status/history APIs.
- [ ] BMS implements and acknowledges vehicle-availability events.
- [ ] Integrated deployment verifies retry, callback, status precedence, trip/job-order follow-up, and notification behavior.

No cross-system or runtime acceptance is claimed until these dependencies exist.
