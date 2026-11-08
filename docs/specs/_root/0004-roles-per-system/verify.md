# Verify: roles per system · spec 0004 · updated 2026-11-08
_Steps derived from spec 0004 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._
_A ticked step was already run once on the local stack during `/develop` (2026-11-08); `/check verify` may run it again._

Getting a VRMS admin token by hand: `POST /auth/login` with `Origin: http://localhost:8000` and `Content-Type: application/json` (cookie jar), follow `GET /vrms/session/start`, then `POST /vrms/session/refresh` with `Origin: http://localhost:8001`. Mobile logins share a per address limit: wait a minute after about 5.

## Commands
- [x] `npm run db:deploy` in welinc-auth on the pre spec database → migration applies, then prints `VRMS: 3 roles, no change`, `VMMS: 4 roles, no change`, `BMS: 5 roles, no change` → AC-5, AC-6
- [x] `npm run catalog:sync` a second time → the same three "no change" lines, nothing written → AC-2
- [x] `npx prisma migrate diff --from-config-datasource --to-schema prisma/schema.prisma --script` → `-- This is an empty migration.` → AC-8 (no drift)
- [x] Migration fix on a fixture: copy the pre spec schema into a scratch database, insert a user with VRMS `MECHANIC` then VRMS `ADMIN`, one with BMS `MECHANIC` plus VMMS `MECHANIC`, one with only VRMS `CUSTOMER_SUPPORT`, run the migration SQL with `psql` → notices `removed BMS MECHANIC, not a BMS role`, `removed VRMS CUSTOMER_SUPPORT, not a VRMS role`, `removed VRMS MECHANIC, kept VRMS ADMIN`, `no roles left` for the third; `user_roles.role` is `varchar(40)`; no `UserRole` type; inserting VRMS `DRIVER` fails on `user_roles_system_role_fkey` → AC-7, AC-8
- [x] Drop `HELPER` from `prisma/catalog/bms.ts` while an account holds BMS `HELPER`, run `npm run catalog:sync` → exit code 1, lists the holder, `system_roles` unchanged → AC-3
- [x] Same with `--dry-run` and a harmless change (a new description) → prints the plan, writes nothing → AC-3
- [x] Run two `npm run catalog:sync` at once → the second waits for the first (advisory lock), both finish → AC-3
- [x] Rename `MECHANIC` to `TECHNICIAN` in `vrms.ts` → refused as a drop of a held role → AC-4
- [x] `npm run build` with `import { UserRole } from '@prisma/client'` in any file under `src/` → the prebuild gate fails and names the file → AC-14
- [x] `npm run seed:clients` → lists `bms-mobile`; `vmms-mobile` has `allowed_roles` VMMS and VRMS Mechanic and Chief Mechanic → AC-18
- [x] `npm run seed:clients` with the catalog emptied (a fresh database already has it, the migration seeds it) → "Run npm run db:deploy first." → AC-18
- [x] `npm run seed` → succeeds; role codes stored as text → AC-21

## API
- [x] `GET /auth/systems` through the gateway, no token → 200, three systems in VRMS, VMMS, BMS order, roles in file order, `webAddress` per system, `Cache-Control: public, max-age=60`, an `ETag` → AC-16
- [x] Same request with `If-None-Match: <that ETag>` → 304 → AC-16
- [x] Switch the `vrms` client off (`is_active = false`) → VRMS `webAddress` is `null`; switch it back on → AC-16 (value source: the active confidential client)
- [x] Change one description in a catalog file, sync → the `ETag` changes → AC-16 (value source: hash of the body)
- [x] `GET /auth/me` with a VRMS token for an account with VRMS and VMMS roles → only the VRMS role → AC-17
- [x] `GET /auth/users?role=DRIVER` as VRMS admin → 400 `UNKNOWN_ROLE`, "VRMS has no role 'DRIVER'. Its roles are Admin, Chief Mechanic, Mechanic." → AC-9
- [x] `GET /auth/users?role=CHIEF_MECHANIC` → only `vrms.chief@welinc.com` → AC-9
- [x] `GET /auth/users?role=DRIVER` with the `vrms` service token (`directory.read`) → 400 `UNKNOWN_ROLE` → AC-9
- [x] `PATCH /auth/users/:id` with VRMS `DRIVER` → 400 `UNKNOWN_ROLE`; with `driver` → 400 from the DTO shape check → AC-9
- [x] A BMS admin sends BMS `MECHANIC` → message lists "Admin, Operations, Customer Support, Driver, Helper" → AC-9 (value source: `system_roles.name` in order)
- [x] `PATCH` with VRMS `ADMIN` and `MECHANIC` → 409 `ROLE_LIMIT`, "VRMS allows one role per person." → AC-10
- [x] Set `maxRolesPerUser: 2` for VRMS in a test catalog → the message reads "VRMS allows 2 roles per person." when exceeded → AC-10 (value source: `systems.max_roles_per_user`)
- [x] `PATCH` a mechanic to `CHIEF_MECHANIC` in one request → 200, roles `[CHIEF_MECHANIC@VRMS]`, VMMS role kept → AC-11
- [x] Four concurrent `PATCH`es on one account with different VRMS roles → all 200, the account ends with exactly one VRMS role → AC-13
- [x] VRMS admin edits their own role → 409 "You can't change your own role." → AC-12
- [x] VRMS admin `POST /auth/users` with their own email and `attachExisting: true` → 409, no role added → AC-12
- [ ] Deactivate the only active VRMS admin through `PATCH /auth/users/:id/status` (from a second admin you then remove) → 409 "This is the last VRMS admin." → AC-15 (not reachable live: the self deactivation 409 fires first; covered by `user-changes.spec.ts` and `auth.service.admin.spec.ts`)
- [x] Move the BMS admin flag to `OPERATIONS` in a test catalog while `ops.user` is active, sync → `ops.user` can call `GET /auth/users` with a BMS token, `bms.admin` gets 403; move it back → AC-14 (value source: `is_system_admin`, read per request)
- [x] `GET /auth/users/:id/sessions` as VRMS admin → 200; `GET /auth/users` with no token → 401 → AC-14
- [x] `ops.user` (BMS Operations) mobile login on `bms-mobile` → 403 `APP_NOT_ALLOWED` "This app is for Driver and Helper accounts.", no mobile session row → AC-19
- [x] `vmms.admin` mobile login on `vmms-mobile` → 403 `APP_NOT_ALLOWED` "This app is for Mechanic and Chief Mechanic accounts." → AC-19
- [x] A mechanic signs in on `vmms-mobile`, refreshes with `audience=VRMS` → VRMS Mechanic role; change their VRMS role to Admin → next refresh 403 `APP_NOT_ALLOWED`; change it back → the same refresh token works (the refusal wrote nothing) → AC-18, AC-19
- [x] The portal's password login for `ops.user` still works (no client limit) → AC-19

## UI / manual
- [x] Users page, New user → the Role dropdown lists Admin, Chief Mechanic, Mechanic in that order, each with its description under the name; the trigger shows only the name → AC-20
- [x] Network tab: opening Users makes one `GET /auth/systems`, also when the form and the filter both show → AC-20
- [x] Block `/auth/systems` (devtools request blocking), reload Users, open New user → dropdown disabled, "We couldn't load the roles." with Retry, Create user disabled; unblock, Retry → the roles load and Save works → AC-20
- [x] Role filter lists the catalog roles; `?role=SERVICE_ADVISOR` in the URL shows that code in the filter and can be cleared → AC-20
- [x] Edit yourself → Role dropdown disabled with "You can't change your own role." → AC-12, AC-20
- [x] 375px: the Role dropdown and its options fit with no sideways scroll → AC-20

## Acceptance-criteria coverage
- AC-1 catalog unit tests · AC-2 sync commands · AC-3 refusal commands plus `catalog.spec.ts` · AC-4 rename command · AC-5 `db:deploy` · AC-6 first sync plus the migration matching test · AC-7, AC-8 fixture run · AC-9 API filter and edit steps · AC-10 two roles and the limit message · AC-11 one edit change · AC-12 own role steps · AC-13 concurrent edits · AC-14 gate, flag move and admin routes · AC-15 last admin · AC-16 `/auth/systems` steps · AC-17 `/auth/me` · AC-18 seed steps · AC-19 mobile and refresh steps · AC-20 UI steps · AC-21 seed
