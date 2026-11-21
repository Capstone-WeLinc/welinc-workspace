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

- [ ] Build `welinc-backend-vmms`
- [ ] Build `welinc-web-vmms`
- [ ] Run the focused VMMS authorization test or test suite covering the
  business audit guard

## Acceptance-criteria coverage

- AC-1 through AC-6 by the role, route, API, response, and portal checks above.
