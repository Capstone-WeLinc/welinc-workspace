# Verification

Use the acceptance criteria in [index.md](index.md). Implementation evidence is distinct from live partner/runtime verification.

## Automated implementation evidence

- [x] Backend focused tests: 5 suites, 44 tests passed, including fuel-cost response filtering, referral idempotency, repair-event handoff, repeated-alert persistence, and retirement decisions/outbox retry.
- [x] Web focused tests: 4 files, 34 tests passed, covering referral UI/permissions, retirement review, and repeated-repair alert display.
- [x] VMMS backend build passed; Prisma schema validation passed.
- [x] VMMS web TypeScript and production build passed.
- [x] Prisma migration generated and schema validated; migration was not applied.

These automated tests do not establish production database behavior, service grants, partner contract acceptance, or live cross-system delivery.

## Backend

- [ ] Post a valid retirement request with a VRMS service token; verify durable request persistence and Operations-only pending reads.
- [ ] Replay an identical retirement event; verify duplicate success. Reuse an event or request ID with changed content; verify conflict and no mutation.
- [ ] Approve the sole open repair; verify transactionally that the request is decided, repair state is closed, vehicle is deactivated, status is recomputed, fleet invalidation exists, and one decision outbox row exists.
- [ ] Attempt approval with a second open repair; verify conflict and that request, vehicle, repair, and outbox remain unchanged.
- [ ] Decline with a valid reason; reject missing/blank/oversized reason and verify the vehicle and repair state do not change.
- [ ] Simulate route-16 success, network failure, timeout, retryable HTTP status, and non-retryable response; verify a stable event ID, retry state, and no duplicate decision.
- [ ] Post and replay a repeated-repair alert; reject changed-payload reuse and unknown vehicles. Verify bounded cursor pagination and Admin/Operations-only reads.
- [ ] Create a fuel referral from an open anomaly; verify the exact payload omits schedule/work-order/cost fields, uses the fill-up UUID and odometer, and persists once.
- [ ] Verify resolved anomalies cannot be referred, repeated submission returns the existing referral, and Admin retry uses the original referral ID.
- [ ] Verify Chief Mechanic anomaly response and referral endpoint contain no fuel costs; verify unauthorized roles are denied.
- [ ] Validate Prisma schema and migration without applying the migration to a database.

## Web

- [ ] Operations sees pending retirement requests and can approve/decline with a required reason; verify conflict and network errors are visible and the list refreshes after a successful decision.
- [ ] Non-Operations users cannot view or decide retirement requests, including by direct API call.
- [ ] Admin and Chief Mechanic see the fuel anomaly referral action. Chief Mechanic sees no fuel log, efficiency/cost controls, or fuel cost values; other unauthorized roles are denied.
- [ ] Verify duplicate referral shows its existing state and failures are surfaced.
- [ ] Verify VRMS repeated-repair alerts appear beside maintenance repeated failures, load older pages, and present empty/error states.

## Partner and deployment evidence

- [ ] VRMS accepts Flow 6 referrals without `maintenanceScheduleId` or `workOrderNumber`.
- [ ] VRMS sends Flows 4 and 5 using the documented client, audience, scopes, payloads, and retry IDs.
- [ ] Apply the migration in an authorized test environment and exercise the full VMMS/VRMS flows.
- [ ] Obtain partner review and verify the routes through the deployed gateway and auth grants.
