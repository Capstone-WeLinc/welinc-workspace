# Verify: Team Management reads drivers and helpers from Auth · spec 0012

Steps derived from [index.md](index.md). Ticked items were checked on 2026-11-25 on a local
stack running the change, with the migration applied.

## API / automated

- [x] `GET /bms/config/drivers` and `/helpers` list only people who hold the Driver or Helper role
  for good, with `userId`, `fullName`, `email` and `contact` from Auth, and no `empId`,
  `initials` or `totalTrips` (contract tests)
- [x] A person with a temporary grant, or with a non-crew role, is left out (contract tests)
- [x] A new account gets its BMS row on the first read; a second read creates nothing more
  (contract tests, and against a copy of the local database)
- [x] A helper whose row was turned off comes back while they hold the role (copy of the local
  database)
- [x] A helper who no longer holds the role can't be assigned (contract tests)
- [x] `PATCH` saves only the BMS details; `fullName`, `email` or `contact` answers 400 "Name, email
  and contact number are edited in the portal" (contract tests, and against the copy)
- [x] `POST` and `DELETE` on `/bms/config/drivers` and `/helpers` no longer exist
- [x] The directory roster reads every page, is reused for 30 seconds, and a failed read isn't
  kept (`directory.client.spec.ts`)
- [x] The dispatch service's directory token gets `phone`: the local roster returned 32 drivers and
  helpers, all with a phone number
- [x] A new crew leave request has no `crewEmpId`; the Approvals row is headed by the crew
  member's name (`crew-leave.spec.ts`)
- [ ] `tests/vehicle-team-availability.spec.ts` (Playwright) passes against the running stack

## Database

- [x] The migration applies cleanly to a copy of the local dispatch database (12 drivers, 20
  helpers, all with an account)
- [x] After it, Prisma reports no drift on the changed columns (the remaining drift on
  `license_type`, `address` and `updated_at` was there before)
- [x] Applied to the local dispatch database (backup taken first); the service starts with 0
  compile errors
- [ ] Staging: `SELECT count(*) FROM drivers WHERE user_id IS NULL` (and `helpers`) is 0 before
  deploying

## Web / manual

- [x] Team Management has no Add Driver / Add Helper button and no Employee ID column; the
  subtitle reads "Manage driver and helper dispatch details."
- [x] Each row has one **Edit** button with a pencil icon, and no ⋮ menu
- [x] The edit form shows name, email and contact number read-only under **Account**, with an
  **Edit in portal** link and no extra note
- [ ] **Edit in portal** opens `/admin/people/<user id>?system=BMS` in the portal for that person
- [ ] Saving the form changes only the BMS details, and the list shows them straight away
- [ ] Search finds crew by name, email, contact and license number
- [ ] Vehicle & Team Availability cards and detail windows show no Employee ID or Total trips,
  with initials from the name
- [ ] Admin and Operations Scheduling dropdowns show names without "(DRV-001)"
- [ ] Approvals: a crew leave row is headed by the name; the side panel shows "Crew member"
- [ ] Give someone the Helper role in the portal: they appear on Team Management within 30
  seconds. Remove it: they disappear and can't be assigned

## Mobile

- [ ] bms-mobile (not in this workspace): leave requests still show correctly without
  `crewEmpId`

## Commands

- [x] `bms-dispatch-service`: `npx tsc --noEmit`
- [x] `bms-dispatch-service`: `npm test` (38 contract tests, 107 Jest tests)
- [x] `bms-dispatch-service`: eslint on the changed files
- [x] `welinc-web-bms`: `npm run typecheck`
- [x] `welinc-web-bms`: eslint on the changed files (no errors; 5 warnings, all pre-existing)
- [x] `welinc-web-bms`: `npm test` (18 tests)
- [ ] `welinc-web-bms`: `npx playwright test tests/vehicle-team-availability.spec.ts`
- [x] `welinc-backend-bms` CI passes on `BMS/team-from-auth` (PR #69). The first run failed at
  `npm run lint:ci` (repo-wide `eslint .`): `test/demo-seed.integration.cjs` didn't parse
  because of a quote inside a single-quoted string. Fixed in `28b7b38`; the full CI sequence
  (lint, typecheck, build, test) was run locally before pushing.
- [x] `welinc-web-bms` CI passes on `BMS/team-from-auth`
