# Verify: Restrict VMMS business audit logs to Admin · spec 0002

Steps derived from the acceptance criteria in [index.md](index.md).

## UI and API / manual

- [ ] Sign in as Admin → open `/audit-logs` and confirm business audit records
  load without a response-contract change → AC-1
- [ ] Sign in as Operations → confirm Audit Logs is absent from navigation →
  open `/audit-logs` directly and confirm redirection to `/dashboard` → AC-2
- [ ] Send `GET /vmms/audit-logs/business` as Operations → confirm the request
  is denied without business audit data → AC-3
- [ ] Repeat direct web-route and API checks as Chief Mechanic and Mechanic →
  both remain denied → AC-4
- [ ] Compare an existing Admin audit result before and after the guard change →
  confirm result selection, ordering, and response shape are unchanged → AC-5
- [ ] Open the portal and confirm login/account activity behavior is unchanged;
  confirm VMMS does not add authentication activity to its business audit page
  → AC-6

## Commands

- [x] Build `welinc-backend-vmms`
- [x] Build `welinc-web-vmms`
- [x] Run the focused VMMS authorization test or test suite covering the
  business audit guard

## Acceptance-criteria coverage

- The focused API test covers Admin access and API denial for Operations,
  Chief Mechanic, and Mechanic (AC-3, AC-4). The web permission test covers
  role-based Audit Logs navigation visibility. Builds cover compilation only.
- Manual route, existing-record response comparison, and portal behavior checks
  remain pending (AC-1, AC-2, AC-5, AC-6).

## Implementation evidence

- `npm test -- --runInBand modules/vmms/audit/audit.controller.spec.ts` passed:
  Admin access succeeded; Operations, Chief Mechanic, and Mechanic were denied
  before any audit query.
- `npm run build` passed in `welinc-backend-vmms`.
- `npm exec vitest run src/lib/utils/permissions.test.ts` passed all five role
  visibility cases in `welinc-web-vmms`.
- `npm run build` passed in `welinc-web-vmms`.
- Interactive browser and shared-portal acceptance has not been run.
