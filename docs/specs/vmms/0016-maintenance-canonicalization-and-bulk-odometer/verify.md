# Verify — 0016 Maintenance canonicalization, navigation alignment, and bulk odometer API

## Acceptance criteria coverage

| AC | Criteria | Verification | Status |
|---|---|---|---|
| AC1 | Deep-links use `search`/`q` front-end lookup and resolve correctly | Code audit: notification click opens Maintenance Scheduling with `?search=<maintenanceScheduleId>`; no remaining `scheduleId=` URL navigations in `welinc-web-vmms/src`; web build passed | Implemented in code; runtime/manual click-through pending |
| AC2 | TIME/odometer derived due/status align with backend rules; workflow states preserved | Canonical helpers in schedules service use `scheduleDue` precedence and Manila TIME `PENDING|DUE|OVERDUE` derivation for eligible statuses; workflow states preserved; targeted schedule-due/overdue/time tests and new canonical-response spec pass | Partial (targeted/static + unit tests; runtime/integration and full cross-path parity pending) |
| AC3 | API responses expose canonical/computed due/status fields | `findAll` (Prisma + schema-drift fallback), `create`, `update`, and `updateProgress`/`nextSchedule` responses now expose additive canonical `dueDate`/`dueOdometer`/`computedStatus`; frontend types/normalization prefer canonical fields; builds pass | Partial (key paths covered; exhaustive audit of every schedule-shaped response path and consumer parity pending) |
| AC4 | Bulk odometer JSON endpoint validates and returns per-item results; existing flows intact | `POST /vehicles/odometer/bulk` implemented with DTO validation, per-item domain processing, duplicate rejection per duplicate ID, and `UPDATED|UNCHANGED|ERROR` results; existing single/import paths unchanged; targeted existing vehicle/odometer suites and new bulk service/controller specs pass | Implemented in code + targeted tests; runtime/authz/manual mixed-batch and regression checks pending |
| AC5 | Vehicles bulk manual update uses bulk endpoint and reports outcomes | `bulkUpdateVehicleOdometerRecords` client and Vehicles manual bulk flow wired to bulk endpoint with per-item result handling; web build passed | Implemented in code; manual UX/runtime verification pending |
| AC6 | Builds/tests pass and docs reconciled | Backend/web builds and targeted backend tests pass (including new specs); spec docs updated with evidence/gaps; scope reconciliation notes prepared | Partial (automated evidence recorded; `docs/scope/vmms/index.md` reconciliation/runtime acceptance still pending) |

## Planned/Executed checks

### Repo-local validation (executed)
- `welinc-backend-vmms` `npm run build`: **passed** after canonical schedule response changes, bulk odometer endpoint/DTO/service changes, and `updateProgress`/`nextSchedule` canonical field additions.
- `welinc-web-vmms` `npm run build`: **passed** after deep-link fix, canonical maintenance normalization/type updates, and bulk odometer client/UI wiring.
- Targeted backend tests (existing): `schedule-due.spec.ts`, `maintenance-overdue.spec.ts`, `time-interval.spec.ts` — **42 passed**; `vehicles-odometer-import.spec.ts`, `vehicles.controller.spec.ts`, `vehicles.service.spec.ts` — **68 passed**.
- Targeted backend tests (added for this slice): `maintenance-schedules/maintenance-schedule-canonical.spec.ts`, `vehicles/vehicles-bulk-odometer.service.spec.ts`, `vehicles/vehicles-bulk-odometer.controller.spec.ts` — **7 passed**.

### Manual/integration checks (environment-dependent, pending)
- Notification deep-link opens correct schedule/work-order context via search prefill.
- TIME schedule with explicit `targetDueDate` shows consistent due/overdue in UI and API-derived fields.
- TIME schedule relying on computed interval due behaves consistently (no false overdue before derived due).
- Odometer schedules show Pending/Due/Overdue consistent with mileage/buffer rules and preserved workflow states in runtime scenarios.
- Vehicles bulk manual odometer: all-valid batch, mixed valid/invalid batch, domain-rejected updates, and unchanged rows show correct per-item results and UI messaging.
- Existing single odometer update and odometer import preview/save still function end-to-end.

## Evidence log

- 2026-11-24: Spec 0016 created (index/rationale/verify).
- 2026-11-24: `welinc-web-vmms/src/components/Navbar/Navbar.tsx` notification deep-link changed from `scheduleId` query param to `search`; `npm run build` passed in `welinc-web-vmms`. Deep-link audit found no remaining `scheduleId=` URL navigations in `welinc-web-vmms/src`.
- 2026-11-24: `welinc-backend-vmms/src/modules/vmms/maintenance-schedules/maintenance-schedules.service.ts` updated to expose canonical derived `dueDate`/`dueOdometer` and additive `computedStatus` for TIME-derived `PENDING|DUE|OVERDUE` in `findAll` (normal and schema-drift fallback paths) and in `create`/`update` responses, preserving stored workflow states and fixing schema-drift fallback TIME-due computation; `npm run build` passed in `welinc-backend-vmms`.
- 2026-11-24: Targeted backend tests passed in `welinc-backend-vmms`: `schedule-due.spec.ts`, `maintenance-overdue.spec.ts`, `time-interval.spec.ts` (42 tests) and `vehicles-odometer-import.spec.ts`, `vehicles.controller.spec.ts`, `vehicles.service.spec.ts` (68 tests).
- 2026-11-24: `welinc-backend-vmms` vehicles module: added `POST /vehicles/odometer/bulk` (`BulkUpdateOdometerDto`, controller action, `VehiclesService.bulkUpdateOdometer`) returning per-item `UPDATED|UNCHANGED|ERROR` outcomes and summary counts with existing domain/authz rules; `npm run build` passed in `welinc-backend-vmms`.
- 2026-11-24: `welinc-web-vmms` updated maintenance types/API normalization to prefer backend canonical `computedStatus`/due fields when present, added `bulkUpdateVehicleOdometerRecords` client helper, and switched Vehicles manual bulk odometer save to the bulk JSON endpoint with per-item result handling; `npm run build` passed in `welinc-web-vmms` after wiring fixes.
- 2026-11-24: `welinc-backend-vmms` maintenance schedules: `updateProgress` and recurring `nextSchedule` response now include additive canonical `dueDate`/`dueOdometer`/`computedStatus` fields; `npm run build` passed in `welinc-backend-vmms`.
- 2026-11-24: Added targeted backend tests: [maintenance-schedules/maintenance-schedule-canonical.spec.ts](../../../../../welinc-backend-vmms/src/modules/vmms/maintenance-schedules/maintenance-schedule-canonical.spec.ts), [vehicles/vehicles-bulk-odometer.service.spec.ts](../../../../../welinc-backend-vmms/src/modules/vmms/vehicles/vehicles-bulk-odometer.service.spec.ts), [vehicles/vehicles-bulk-odometer.controller.spec.ts](../../../../../welinc-backend-vmms/src/modules/vmms/vehicles/vehicles-bulk-odometer.controller.spec.ts). `npx jest ... --runInBand` passed (**7 tests**, 3 suites).
- 2026-11-24: Reconciled Features 2, 3 and 4 in [docs/scope/vmms/index.md](../../index.md) with the implemented bulk odometer, canonical schedule response and deep-link evidence. Runtime and cross-role acceptance remain pending.
- 2026-11-24: Re-ran canonical/due/overdue/time suites: 45 tests passed across 4 suites. Re-ran bulk/single/import vehicle odometer suites: 72 tests passed across 5 suites.

## Reconciliation notes (b)

- **Delivered/verified in this slice:** spec-first VMMS contract/docs, notification deep-link alignment (`search`/`q`), additive canonical schedule fields on key schedule responses (`findAll`, `create`, `update`, `updateProgress`, `nextSchedule`), frontend canonical-field preference, JSON bulk odometer endpoint (`POST /vehicles/odometer/bulk`) with per-item partial-success semantics, frontend bulk wiring, and targeted builds/tests including new specs for canonical list fields and bulk odometer service/controller behavior.
- **Implemented behavior details to preserve:** TIME computed presentation status is additive and preserves stored workflow/protected states; odometer-derived `PENDING|DUE|OVERDUE` is not recomputed in schedule list/create/update mappings without vehicle odometer context (stored status preserved; frontend/existing logic may still derive where applicable). Bulk endpoint rejects duplicate vehicle IDs per duplicated item occurrence and processes valid non-duplicate items independently (no all-or-nothing transaction).
- **Scope reconciliation:** [docs/scope/vmms/index.md](../../index.md) now references Spec 0016 evidence for Features 2/3/4 (vehicle/odometer, maintenance scheduling/work orders/status and due handling). Feature statuses remain in progress until runtime/manual acceptance is available. No shared/gateway/auth/portal scope changes required.
- **Analytics follow-up:** `welinc-backend-vmms-analytics-ai` was not modified; additive VMMS API fields are expected to be low-risk, but contract/sync assumptions should be rechecked if analytics relies on specific schedule payload shapes or omits new fields during normalization.

## Remaining gaps / follow-ups

- **Exhaustive response-path audit:** verify/add canonical fields to any other client-consumed schedule/work-order payloads if discovered (e.g. extension/cancellation/unlock review responses that return schedule snapshots).
- **Test coverage gaps:** add dedicated tests for canonical fields in `create`/`update` responses and for additional bulk edge cases as needed (max batch size, authz/role matrix, mixed vehicle-not-found/conflict cases with current odometer lookup).
- **Runtime/manual verification:** end-to-end notification deep-link, TIME/odometer due-status parity across trigger types and roles, Vehicles bulk manual mixed outcomes and UX, and regression of single odometer update/import flows.
- **Cross-repo/client parity:** confirm VMMS mobile and analytics consumers are unaffected or aligned with canonical/computed fields if they consume these APIs.
- **FR/performance/broader acceptance:** not claimed complete by this slice.
