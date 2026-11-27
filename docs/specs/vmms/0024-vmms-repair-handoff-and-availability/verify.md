# Verification

## VMMS backend

- [ ] Submit a Chief Mechanic `REPAIR` review and verify the schedule transition and referral outbox row commit atomically.
  Focused local checks: `maintenance-schedules.service.spec.ts` and `vrms-repair-referrals.service.spec.ts` pass 17 tests. They do not exercise the Chief Mechanic `REPAIR` action and transactional outbox creation together, so this acceptance criterion remains pending.
  Additional VMMS checklist evidence: `checklist-submission.spec.ts` passes 27 tests, including a Chief Mechanic `REPAIR` review that persists the referral in the schedule transaction without calling VRMS delivery from the request. The transaction is mocked, so database-backed atomicity remains pending.
- [x] Verify referral payload fields, stable idempotency ID, duplicate protection, and no attachment/cost leakage.
  Evidence: `vrms-repair-referrals.service.spec.ts` asserts the exact persisted and sent payload, confirms the referral ID is reused as the `Idempotency-Key`, excludes attachment/cost fields, and verifies duplicate referrals are not created.
- [x] Simulate network/timeout/5xx/429 responses; verify backoff and the configured maximum age. Verify non-retryable payload errors are surfaced.
  Evidence: `vrms-repair-referrals.service.spec.ts` passes 15 tests, including retries for 401/403/408/429/503, network and timeout failures, increasing delays across attempts, failure after the configured 24-hour window, and a surfaced `http_400` failure without retrying.
- [x] Verify manual retry is Admin-only and reuses the referral ID.
  Evidence: `vrms-repair-referrals.controller.spec.ts` passes five route tests using the real `RolesGuard` (JWT guard stubbed): VMMS Admin is allowed, Operations/Chief Mechanic/Mechanic and a VRMS Admin are denied. `vrms-repair-referrals.service.spec.ts` verifies retry uses the original referral ID as its idempotency key.
- [x] Accept a referral into a new and existing ticket; verify ticket ID/number, status, and explicit schedule linkage.
  Evidence: `vrms-repair-events.service.spec.ts` passes six service tests, including acceptance on a new `OPENED` ticket and linking an additional referral through `LINKS_UPDATED` on an existing ticket. A referral-only link update succeeds when the already-linked schedule has since changed state; version gaps are accepted and lower versions are ignored.
- [x] Use Prisma `executeRaw` for advisory locks in both VRMS event receivers.
  Evidence: `vrms-repair-events.service.spec.ts` passes with transaction mocks exposing `executeRaw` (not `queryRaw`) for the repair and referral-event receiver locks.
- [x] Accept a VRMS service odometer on `OPENED` and retain it as event evidence without changing the vehicle master reading.
  Evidence: `vrms-repair-events.service.spec.ts` verifies the opening reading is stored in the event receipt while the handler only changes repair availability.
- [x] Stage a VRMS `COMPLETED` reading for Operations confirmation before any vehicle master odometer update.
  Evidence: `vrms-repair-events.service.spec.ts` verifies only completed events with readings create a pending review alongside the event receipt. `vehicles.odometer-reviews.spec.ts` covers the pending queue, confirmation through the existing odometer transaction, lower-reading rejection, dismissal without a master update, and repeat decisions; `vehicles.controller.spec.ts` covers Operations-only authorization. The additive migration is created but not applied.
- [x] Reject a referral; verify only the referenced schedule returns to `IN_PROGRESS` / `REJECTED` with the VRMS reason.
  Evidence: `vrms-repair-events.service.spec.ts` verifies the update targets the referral's schedule ID only, sets `IN_PROGRESS` / `REJECTED`, trims and records the VRMS reason, and handles identical event replay idempotently.
- [ ] Cancel a ticket; verify the linked schedule remains open in `FOR_REPAIR`, the cancellation reason is visible, and the vehicle status is recalculated.
- [ ] Complete a ticket; verify linked schedules return to fresh Chief Mechanic verification and do not complete until normal VMMS approval.
- [x] Unit-test status/history read behavior, pagination, failure responses, and service-layer cost filtering.
  Evidence: `vrms-repair-reads.service.spec.ts` passes nine tests for fresh ticket status, bounded cursor pagination, explicit unavailable/not-found errors, and cost visibility for Admin, Operations, and Chief Mechanic while omitting it for Mechanic.
- [ ] Verify live VRMS status/history responses, controller authorization, and no persisted history copy.
- [x] Unit-test referral persistence, duplicate prevention, outbound retry/manual retry, ticket acceptance, and rejection handling.
  Evidence: `vrms-repair-referrals.service.spec.ts` passes 15 tests for exact referral payload shape (no attachment/cost fields), duplicate prevention, missing findings, successful delivery with the referral ID as `Idempotency-Key`, retry backoff and expiration, and manual retry with the original ID. `vrms-repair-events.service.spec.ts` passes six tests for accepted-ticket linking, rejection state updates, idempotent/conflicting event replay, and event-version handling.
- [ ] Verify mapped outsourced shops use the VMMS catalog name; unknown names cause no partial event update.
- [x] Serve active outsourced providers to VRMS with a non-cacheable response and client-bound `fleet.read` authorization.
  Evidence: `fleet.controller.spec.ts` verifies active-only, alphabetically ordered provider reads and `Cache-Control: no-store`; `guards.spec.ts` verifies VRMS is allowed and BMS is refused for the VRMS-bound read.
- [x] Unit-test BMS availability outbox event creation, payload delivery, retry identity/backoff, and per-vehicle ordering.
  Evidence: `bms-availability.service.spec.ts` passes seven tests covering versioned event creation, payload fields, successful delivery, retry with a stable event ID, backoff, prevention of later-version delivery while an earlier event is pending, and terminal handling of HTTP 400 without blocking later versions.
- [ ] Change a vehicle status from repair, maintenance, and Operations paths; verify one ordered outbox row per actual change and no event for a no-op.
- [ ] Simulate BMS unavailability and verify ordered retry, stable event IDs, and no rollback of the VMMS status change.
- [ ] With a BMS service token, read the VMMS garage and vehicle lists; verify only active, non-deleted fleet entries are returned and responses are not cacheable.
- [x] Unit-test the fleet-read service-client boundary: the BMS client with `fleet.read` is accepted, while another service client with that scope is refused. Evidence: `guards.spec.ts` passes 12 tests, including exact-client checks for BMS and the VRMS provider-list route.
- [ ] Read an active vehicle immediately before assignment; verify status, `availabilityVersion`, and `isAssignable` reflect the current VMMS record. Verify `UNDER_REPAIR` and `UNDER_MAINTENANCE` are nonassignable and inactive, deleted, missing, or VMMS-error cases fail closed (inactive/deleted/missing detail IDs retain `404`).
- [ ] Create, materially update, deactivate, and soft-delete a vehicle and garage; verify one durable fleet-change event per actual change and none for a no-op. Verify events contain only invalidation metadata and BMS refreshes canonical VMMS reads.
- [x] Refuse vehicle deactivation or soft deletion while a VRMS repair is open, and identify the ticket in the error.
  Evidence: `vehicles.service.spec.ts` passes 23 tests, including blocked `isActive: false` updates and deletion with an open ticket, plus successful deactivation when no open repair exists.
- [ ] Make BMS fleet-change delivery unavailable; verify VMMS retains the outbox event and retries without rolling back vehicle/garage changes.
- [x] Deliver each fleet invalidation to BMS and VRMS using separate audience-bound tokens; mark sent only after both accept.
  Evidence: `bms-fleet-changes.service.spec.ts` verifies the same event payload/ID is sent to each route with its own token, and a VRMS 503 retains the outbox event for retry.
- [ ] Verify that a repair availability event during an active BMS delivery flags the active assignment for follow-up and blocks new assignment without changing BMS's `ON_DELIVERY` trip state.

## VMMS web and mobile

- [ ] Admin sees referral delivery status and can retry a failed referral; non-Admin callers cannot invoke retry.
- [ ] Chief Mechanic sees the linked ticket number/live status and VRMS rejection/cancellation reason; a rejected work order returns to the assigned Mechanic.
- [ ] Vehicle detail shows paged VRMS repair history, loading/empty/error states, and no stale-success fallback.
- [x] Operations can review completed VRMS readings from the Vehicles page, confirm through the existing master-odometer workflow, or dismiss without changing the master.
  Evidence: `Vehicles.odometerReviews.test.tsx` passes three component tests for the ticket-linked reading, confirm/dismiss confirmation steps, and inactive/lower-reading handling.
- [x] Unit-test repair-history state isolation so responses/pages from a previous vehicle request are not shown or appended to the current vehicle.
  Evidence: `repairHistoryState.test.ts` passes three focused cases for vehicle-keyed history, stale-page rejection, and current-page append behavior.
- [ ] Mobile sync stores additive referral metadata without losing pending work-order progress or existing snapshots.
- [x] A Chief Mechanic may route a work order for repair whenever any inspection item fails, regardless of pass count.
  Evidence: `tests/inspectionRemark.integration.test.ts` verifies a single failure among multiple passing items routes to `For Repair`, while pending inspections remain unverified.
- [ ] Mechanics can see permitted history fields but never repair-cost fields.

## Delivery evidence and external dependencies

- [x] Run focused backend integration tests, backend build/schema validation, web build, and the available focused web/mobile checks.
  Evidence: this review's three targeted backend suites pass 60 tests; the backend build and `npx prisma validate` pass. Web `npm run build`, targeted ESLint, the repair-history state test, and the odometer-review component tests pass. Mobile lint and the focused work-order test pass.
- Web: `npm run build`, targeted ESLint, the repair-history state test, and the odometer-review component tests pass. Full `npm run lint` still reports eight errors and one warning in Sidebar, DatePicker, Maintenance Scheduling, and the WorkOrders search effect; no unrelated lint fixes were made.
- Backend lint: the new odometer-review service spec passes targeted ESLint. Existing findings outside the added review logic remain in `vehicles.service.ts` and `vrms-repair-events.service.ts`; they are not fixed as part of this slice.
- Mobile: `npm run lint` passes. The latest `npm test -- --runInBand` run passed 23 Node tests and 67 Jest tests; no mobile files were changed in this slice.
- 2026-11-27 local recheck:
  - Backend: the six focused repair, availability, and vehicle suites passed 46 tests; `npm run build` and `npx prisma validate` passed. Schema validation does not apply the migration.
  - Web: `npx vitest run src/pages/Vehicles/repairHistoryState.test.ts` passed three tests; `npm run build` and targeted ESLint for `Vehicles.tsx` and `repairHistoryState.test.ts` passed.
  - Mobile: `npm run lint` passed; `npm test -- --runInBand` passed 23 Node tests and 67 Jest tests.
- Closed implementation gap (2026-11-27): `GET /fleet/*` now uses `@ServiceRoute('fleet.read', 'bms')`; `requireService` rejects a different `client_id` even when it has the required scope. `npm test -- --runInBand src/auth/verify/guards.spec.ts` passes 11 tests, `npm run build` passes, and targeted ESLint passes. AC-9 live route access remains pending with the BMS auth grant and runtime environment.
- [ ] Resolve remaining broad-check failures and complete interactive/browser/device acceptance. The local browser preview could not exercise the flow because the VMMS API/session service was unavailable.
- [ ] Migration remains unapplied; the local database was unreachable during migration creation, and no live VRMS event has been exercised.
- [ ] BMS implements the fleet-change receiver, refreshes the VMMS fleet snapshot, and blocks dispatch whenever its pre-assignment VMMS read fails.
- [ ] Obtain VMMS, VRMS, and BMS review of the proposed shared contract, auth grants, partner implementations, and integrated runtime evidence.

No automated or integrated check is marked complete until it is actually run.
