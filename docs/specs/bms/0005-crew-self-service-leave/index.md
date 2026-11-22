# Crew file their own leave and emergency requests

Status: in progress.
Replaces the "Operations files on the crew member's behalf" part of spec 0003. The
approval step, the on-leave rules and the Scheduling warnings from 0003 do not change.

Touches only BMS-owned repos (`welinc-backend-bms`, `welinc-web-bms`). No change to
shared auth, portal or the suite gateway.

## What changes

| | Before (0003) | Now |
|---|---|---|
| Who files leave / emergency | Operations, for the crew member | The driver or helper, for themselves |
| Who withdraws a waiting request | Operations | The driver or helper who filed it |
| Who decides | Admin, on Approvals | Admin, on Approvals (no change) |
| Operations' For Approvals page | Files and tracks requests | **Removed** |
| Scheduling (on-leave pickers, "reassign" tags) | Operations sees them | No change |

Drivers and helpers sign in through the `bms-mobile` client (`DRIVER` / `HELPER`
roles, already in shared auth). Their app lives in `welinc-mobile-bms` (Expo), which is
still a blank scaffold, so this change ships the backend it will call. Until the app
has login and a leave screen, nobody can file new requests.

## Backend (bms-dispatch-service)

Removed (Operations):

- `POST /crew-leave`, `GET /crew-leave/mine`, `GET /crew-leave/:id`,
  `POST /crew-leave/:id/withdraw`

Added (roles `DRIVER`, `HELPER`):

| Route | What it does |
|---|---|
| `POST /crew-leave/self` | File a leave or emergency for yourself: `kind`, `startDate`, `endDate`, `reason` |
| `GET /crew-leave/self` | Your own requests, newest first |
| `GET /crew-leave/self/:id` | One of your requests, with its named history |
| `POST /crew-leave/self/:id/withdraw` | Withdraw one of your requests while it is waiting |

- The crew member is found from the login: the active driver or helper whose
  `user_id` is the signed-in person. A login with no linked crew record gets 403.
- Every rule from 0003 still applies: reason required, dates, 30-day maximum, no
  overlapping active requests, emergency starts today and is in effect at once, the
  filer can't decide their own request.
- Unchanged: `GET /crew-leave/active` and `GET /crew-leave/conflicts` (Admin,
  Operations) and the internal routes behind Admin's Approvals page.
- Activity log labels move to the new routes.

### Database

Migration `remove_operations_filed_crew_leave` deletes every existing row in
`crew_leave_requests` and `crew_leave_events`. All of them were filed by Operations,
the only way to file until now. The tables stay; crew requests use them.

## Web (welinc-web-bms)

- Remove the Operations **For Approvals** page, its routes
  (`/operations/for-approvals`, `/operations/crew-leave`) and its sidebar item.
- Operations' notification bell drops "your request was decided". It keeps
  **Crew conflict: reassign trip**.
- Admin Approvals: no layout change. The submitter is now the crew member.

## Testing

- Unit tests for the self routes: linked driver, linked helper, unlinked login,
  withdraw only your own, plus the 0003 rules through the new entry point.
- Build and lint both repos.
