# Team Management reads drivers and helpers from Auth

Status: pushed, not yet in a pull request. Branch `BMS/team-from-auth` in `welinc-backend-bms`
and `welinc-web-bms`, into `development`.

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

Fixes the head developer's review of Team Management. Touches only BMS-owned repos
(`welinc-backend-bms`, `welinc-web-bms`). No change to shared auth, portal or the suite gateway:
BMS uses the directory routes and the `directory.contact` scope its client already has.
One database migration in `bms-dispatch-service`.

## Problem

BMS kept its own copy of each driver and helper:

- An **Employee ID** (`DRV-001`, `HLP-001`). No other system has one, and WeLinc doesn't use one.
  It showed on the Team Management list and search, the assign dropdowns, the Vehicle & Team
  Availability cards, and as a label on leave requests.
- A **Total trips** count that nothing kept up to date. It was seed data.
- **Initials** stored in their own column, instead of worked out from the name.
- **Name, email and contact number**, which already live on the person's account in Auth. The two
  copies could disagree.
- **Add Driver / Add Helper** buttons that made a BMS-only person with no account, and a
  **Delete** that removed them from BMS only.

## What it does

### Crew come from their account

- Everyone who holds the **Driver** or **Helper** role in BMS (from the portal) shows up on Team
  Management **by themselves**. Nobody is added in BMS.
- The link is the account's Auth user ID (`user_id` on `drivers` and `helpers`). The first time a
  new account is seen, BMS creates its row with empty BMS details.
- **Name, email and contact number** are read live from Auth's directory. BMS no longer stores them.
- Only people who hold the role **for good** count. A temporary grant, or a deactivated, deleted or
  erased account, is left out of the list and can't be assigned. That rule already existed.
- If someone's role is removed in the portal, they drop off the list. If it's given back, their
  same BMS row (and its details) comes back.
- The directory list is reused for 30 seconds, because Auth allows each system 120 directory
  calls a minute. A new account can take up to 30 seconds to appear.

### What BMS still keeps

Only the dispatch details, edited on Team Management:

| Drivers | Helpers |
|---|---|
| Status, join date | Status, join date |
| License number, type and expiry | |
| Emergency contact name and number | Emergency contact name and number |

A driver who just got an account has no license on file until Admin adds it, so
`license_number` may now be empty.

### Team Management page (`/admin/crew`)

Files: `src/pages/admin/CrewManagement.tsx`, `src/components/availability/CrewEditDialog.tsx`,
`src/lib/api/crewService.ts`, `src/components/availability/crewData.ts`

- **No Add Driver / Add Helper button.** The subtitle reads "Manage driver and helper dispatch
  details." When the list is empty, it says a driver or helper shows up once they have a BMS
  account with that role.
- **No Employee ID column.** The list is sorted by name. Search covers name, email, contact and
  license number.
- **Initials** in the avatar come from the name.
- Each row has one **Edit** button (pencil icon), in place of the old ⋮ menu. It opens the form
  for the BMS details above.
- **No Delete.** To take someone off the team, remove their role in the portal.
- The edit form shows the account's name, email and contact number read-only, under an
  **Account** title, with an **Edit in portal** link. There is no extra note: the link already
  says where they're edited. The link opens the person's page in the portal
  (`/admin/people/<user id>?system=BMS`) in a new tab, to change their name, email or contact
  number. The form edits only the BMS details.
- A separate "Edit account in portal" row action was tried and dropped: it repeated the link
  already in the form.

### Other screens

- **Vehicle & Team Availability**: the cards and detail windows lose the Employee ID and Total
  trips. Initials come from the name.
- **Scheduling (Admin and Operations), Operations Job Order**: the assign dropdowns show the name
  only, without "(DRV-001)". Crew are matched by their BMS ID only.
- **Approvals**: a crew leave or emergency row is headed by the crew member's name instead of the
  Employee ID. The side panel shows "Crew member: name (Driver)" instead of "Employee ID".

### Backend

`bms-dispatch-service`:

- `src/auth/directory.client.ts`: new `roster()` reads `GET /auth/directory/users` (every page,
  kept 30 seconds, a failed read is not kept). `DirectoryPerson` gets `phone`.
- `src/auth/verify/verify.module.ts`: the directory token now asks for
  `directory.read directory.contact`, so `phone` is filled. The `bms` client already holds both
  scopes in Auth.
- `src/fleet/crew-roster.ts` (new): `linkedCrew()` (the roster plus each person's BMS row, made if
  missing) and `permanentCrew()` (moved here from `vmms-fleet.provider.ts`, still exported there).
- `GET /bms/config/drivers` and `/helpers` now answer `userId`, `fullName`, `email` and `contact`
  from Auth, plus the BMS details. `empId`, `initials` and `totalTrips` are gone.
- `PATCH /bms/config/drivers/:id` and `/helpers/:id` save only the BMS details. Sending
  `fullName`, `email` or `contact` answers 400 "Name, email and contact number are edited in the
  portal".
- Crew leave: a new request stores the account's name. `crewEmpId` is gone from requests and from
  the Approvals feed.

## Removed

- `POST` and `DELETE` on `/bms/config/drivers` and `/bms/config/helpers`, with their activity log
  labels ("Created driver", "Deleted helper"). Past activity log entries are kept as they are.
- Columns `emp_id`, `name`, `initials`, `contact`, `email`, `total_trips` on `drivers` and
  `helpers`; `crew_emp_id` on `crew_leave_requests`; the sequences `dispatch_driver_emp_no_seq`
  and `dispatch_helper_emp_no_seq`.
- The daily job that blanked an erased person's name and email in BMS. BMS no longer keeps them,
  and Auth already shows "Deleted user".

## Database migration

`bms-dispatch-service/prisma/migrations/20261125090000_crew_from_auth/migration.sql`

1. A row with no account (`user_id` empty) is turned off (`is_active = false`). It can't be listed
   or assigned any more. On every local database today, all 12 drivers and 20 helpers have an
   account, so nobody disappears.
2. Every row with an account is turned back on, so the old BMS-only Delete no longer hides anyone
   who still holds the role.
3. Drops the columns and sequences listed above. **This can't be undone**: the old Employee IDs
   and stored names are deleted. Names, emails and numbers stay in Auth.

## Testing

- `bms-dispatch-service`: typecheck clean; `npm test` passes (38 contract tests, 107 Jest tests).
  New tests cover the roster paging and cache, a new account getting its row, temporary and
  non-crew roles left out, a helper who lost the role being refused for assignment, account
  fields refused on edit, and no `empId`/`initials`/`totalTrips` in the answer.
- The migration was applied to a copy of the local dispatch database (12 drivers, 20 helpers). It
  applied cleanly, and Prisma reports no drift on the changed columns. The built service was then
  run against that copy: new accounts got rows, a removed helper came back, BMS details saved,
  account fields were refused, and a second read created nothing. The copy was deleted afterwards.
- `welinc-web-bms`: typecheck clean; changed files lint with no errors; unit tests pass (18).
  The Playwright test `tests/vehicle-team-availability.spec.ts` was rewritten for the new flow
  (it used to add a driver and helper). It has not been run yet; it needs the stack running this
  branch with the migration applied.
- Not yet checked by hand in the running app.

## Deploy notes

- Run `prisma migrate deploy` for `bms-dispatch-service` together with the new code. The old code
  can't run on the migrated database, and the new code can't run on the old one.
- On staging, check first that every driver and helper has a `user_id`:
  `SELECT count(*) FROM drivers WHERE user_id IS NULL` (and the same for `helpers`). Any such
  row will be turned off by the migration.
- `npm run seed` (`scripts/seed-crew.mjs`) now adds rows by account and only sets a demo license
  number. It no longer writes names or employee IDs.
- **bms-mobile**: the app isn't in this workspace, so it wasn't checked. If it shows `crewEmpId`
  on a leave request, that field is gone now.

## Decisions

- **Total trips is removed, not computed.** Nothing counted trips, and no screen needed it beyond
  the availability window. If it's wanted later, it can be counted from confirmed assignments
  instead of stored.
- **Delete is removed along with Add.** If BMS could delete someone, the roster would bring them
  straight back while they still hold the role. The portal is the one place to take someone off
  the team.
- **Leave requests keep the name as it was when filed.** It's a record of that request, like the
  names on past job orders.
