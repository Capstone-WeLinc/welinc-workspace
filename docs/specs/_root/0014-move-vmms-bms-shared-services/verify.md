# Verify: move VMMS and BMS onto the shared services · spec 0014 · 2026-11-13
_Steps derived from spec 0014 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Before you start: the shared stack and VRMS running (`sh scripts/start.sh vrms`). Seed admin addresses get no mail, so use the non admin accounts named here. Curl calls to `/auth/login` need `Origin: http://localhost:8000` and `Content-Type: application/json`. Local welinc-auth mail is real: don't trigger reset or setup codes.

## Slice 1 and 2: the shared side (you)

### Commands
- [ ] `select id, allowed_roles, app_released, service_scopes from oauth_clients where id in ('vmms','bms','vmms-mobile','bms-mobile')` → `vmms` `{VMMS:[ADMIN,OPERATIONS]}`, `bms` `{BMS:[ADMIN,CUSTOMER_SUPPORT,OPERATIONS]}`, `vmms-mobile` released true, `bms-mobile` false, `bms` scopes include `VMMS: [fleet.read]` → AC-1, AC-6, AC-10
- [ ] `POST /auth/login` as `vmms.mech@` (`mechanic1234`) → 200 `{ systems: [], mobileSystems: [{ system: "VMMS", app: { clientId: "vmms-mobile", released: true }, ... }] }`, not 403 → AC-4, AC-5, AC-8
- [ ] `POST /auth/login` as `mech.juan@` → `systems` is `[VRMS]` only, `mobileSystems` is `[VMMS]` → AC-4
- [ ] `POST /auth/login` as a seed driver (`driver1234`) → `systems: []`, `mobileSystems: [{ system: "BMS", app: { clientId: "bms-mobile", released: false } }]` → AC-4, AC-5
- [ ] `POST /auth/login` as `multi.lead@` → `systems` BMS, VMMS, VRMS in that order, `mobileSystems: []` → AC-4
- [ ] Sign in as `mech.juan@`, then `POST /vrms/session/refresh` → `user.systems` is `["VRMS"]` only → AC-4
- [ ] `GET /auth/sso` with `state.deactivated@`'s old cookie (or any account with no live role) → still 403 `NO_SYSTEM_ACCESS` → AC-5
- [ ] With `vmms.mech@`'s SSO cookie, `GET /auth/authorize?client_id=vmms&...` (a valid PKCE request) → 302 to the VMMS callback with `error=access_denied&error_description=APP_NOT_ALLOWED`, no code row written; the auth log shows `reason=app_not_allowed` → AC-2
- [ ] VRMS callback given `error=access_denied&error_description=APP_NOT_ALLOWED` (a unit test or a crafted request with a valid login cookie) → 302 to `<portal>/?error=APP_NOT_ALLOWED&system=VRMS` → AC-3
- [ ] 31 calls to `GET /auth/users/lookup?q=ma` with a VRMS admin token (session passed the admin code) inside a minute → the 31st answers 429 `RATE_LIMITED` with `Retry-After`; the cookie route `/auth/admin/users/lookup` shares the count → AC-9
- [ ] `POST /auth/token` as `bms` (client credentials, `audience=VMMS`, `scope=fleet.read`) → a token whose `aud` is `VMMS` and `scope` `fleet.read`; as `vrms` with `audience=VMMS` → 400 `invalid_target` → AC-10
- [ ] `npm --prefix welinc-auth run seed:check -- welinc-backend-vrms/prisma/seeds/people.json` → matches → AC-8
- [ ] Contract 0001 reads `**Contract version**: 8`, the version entry lists VMMS and BMS changes, section 12's lookup row stands, the move order says parallel → AC-11

### UI / manual
- [ ] Sign in at the portal as `vmms.mech@` → the phone only state: "VMMS is on the WeLinc mobile app", the roles, "Your role doesn't use the web version.", Sign out, no open button → AC-7
- [ ] Sign in as a seed driver → "BMS is coming to the WeLinc mobile app" → AC-7
- [ ] Sign in as `multi.chief@` → straight into VRMS (one web system); open the portal again with `?from=VRMS` → no launcher loop → AC-4, AC-7
- [ ] Open `<portal>/?error=APP_NOT_ALLOWED&system=VMMS` signed in → "Your role in VMMS uses the WeLinc mobile app, not the web", Back to your systems, Sign out → AC-7
- [ ] The phone only state and the error page at 375px: no sideways scroll, buttons at least 44px tall → AC-7

## Slice 3: the kit

- [ ] `node scripts/check-system.mjs vrms` on the running stack → every check `ok`, exit 0 → AC-12, AC-14
- [ ] Stop the gateway, run it again → exit 2 with "start the stack first" → AC-14
- [ ] `--static-only` on VRMS lists `welinc-web-vrms/src/lib/api/authApi.ts` as allowed (`AC-33 pending`), not as a failure → AC-13
- [ ] Plant `localStorage.setItem('token', t)` in a scratch file inside `welinc-web-vrms/src`, run `--static-only` → FAIL with that `file:line`, exit 1; add `// check-system: allow test` → listed as allowed, exit 0; delete the file → AC-13
- [ ] `grep -n "process.env\|readFileSync.*\.env" scripts/check-system.mjs` → no read of a `.env` file → AC-14
- [ ] `docs/integration/README.md` lists `move-vmms.md`, `move-bms.md`, `fleet-api.md`; each move guide has every *Guide contents* item, the compose template, the checker command and the sign off step → AC-15
- [ ] `sh scripts/setup.sh vmms` with no `docker-compose.vmms.yml` → the "doesn't exist yet" message names `docs/integration/move-vmms.md` → AC-16
- [ ] Once a group adds `docker-compose.vmms.yml` (or `bms`): `sh scripts/setup.sh vmms` makes the client key once (`welinc-backend-vmms/.env` gets `AUTH_CLIENT_PRIVATE_KEY`, welinc-auth's `.env` gets `CLIENT_VMMS_JWKS`, no value printed), starts the stack, runs `migrate` and `seed` in each service container, and a second run says `keep` for the key and leaves the data; `sh scripts/start.sh vmms` waits for `/vmms/health` and `/vmms/analytics/health` (`bms`: `/bms/health`) → AC-16
- [ ] In `welinc-backend-vrms`, `npx jest src/auth/verify/guards.spec.ts` → a person's token on a `@ServiceRoute` answers 403 `WRONG_TOKEN_USE`, a service token without the scope 403 `FORBIDDEN` (the copy VMMS's fleet routes inherit) → AC-23

## Slice 4: per group (after each PR is up)

### VMMS
- [ ] `node scripts/check-system.mjs vmms` → every live and static check `ok` (health, analytics health, 401s, authorize redirect, headless sign in, cookie flags, CSRF, logout and `SESSION_ENDED` within 31 s, `vmms.mech@` refused on the web, mobile login token on `/vmms/maintenance-schedules`, analytics `aud`, fleet 401 and `WRONG_TOKEN_USE`) → AC-12, AC-13, AC-17, AC-18, AC-21, AC-22, AC-23
- [ ] `sh scripts/start.sh vmms` → `ok` for `/vmms/health` and `/vmms/analytics/health` → AC-16, AC-17, AC-22
- [ ] `npm --prefix welinc-auth run seed:check -- welinc-backend-vmms/prisma/seeds/people.json` → matches; the VMMS database has no `users` table → AC-19
- [x] On a phone or emulator: sign in as `mech.juan@` in the VMMS app, see the code screen for `state.unverified@`, sign out → AC-21

### BMS
- [ ] `node scripts/check-system.mjs bms` → login and static groups `ok` (health, 401s, authorize redirect, headless sign in, cookie flags, CSRF, logout, `driver.ramon@` refused on the web, a 5 MB booking POST answered 400 by booking) → login done → AC-12, AC-13, AC-24, AC-25, AC-27
- [ ] `node scripts/check-system.mjs bms --fleet` (VMMS up) → the BMS vehicle list has VMMS's plates with their statuses → fleet done → AC-12, AC-28
- [ ] Stop `vmms-backend`; `GET /bms/config/vehicles` as `bms.ops@` → 503 `FLEET_UNAVAILABLE`; start it again → the list returns → AC-28
- [ ] Mark a truck `UNDER_MAINTENANCE` in VMMS, then assign it in BMS within 30 s → 409 `VEHICLE_UNAVAILABLE` (the list may still show it, with its new status after 30 s) → AC-28
- [ ] Soft delete a truck in VMMS that has a BMS assignment → BMS shows "Unavailable vehicle" on it and refuses a new assignment → AC-28
- [ ] Approvals and Activity logs show names (not ids) for seed people; Activity logs include sign in rows → AC-26
- [ ] No BMS container or `.env.example` names `welinc_db` or port 5433; the `welinc-backend` repo shows Archived on GitHub → AC-29, AC-30

## Cross system (AC-31; again on staging for AC-32)

- [x] Signed out, open a VMMS deep link → portal → sign in as `multi.lead@` → back on that exact VMMS address → AC-31
- [x] Switch system from VMMS → launcher with "You're here" on VMMS → open BMS, then VRMS, with no password asked → AC-31
- [x] Sign out in BMS → VMMS and VRMS tabs open in the same browser ask for sign in within 30 s → AC-31
- [x] Deactivate `multi.lead@` in the portal admin section → requests in all three apps fail within 30 s → reactivate → AC-31
- [ ] Remove `multi.lead@`'s BMS role → at the next BMS refresh (15 minutes at most, or sign in again) BMS refuses and the launcher drops BMS → put it back → AC-31
- [x] Erase a test person who appears in VMMS audit rows and BMS approvals (local only: soft delete, then backdate that user's `deleted_at` past `ACCOUNT_ERASURE_GRACE_DAYS` (1 day at least) and wait for the hourly sweep) → VMMS `actorEmail` copies and BMS names show "Deleted user" → AC-19, AC-26, AC-31
- [ ] Each group lead's written OK is noted in the scope row with the date → AC-31

## Slice 5: cleanup

- [ ] `node scripts/check-system.mjs vrms`, `vmms` and `bms` with `--static-only` → no `/auth/users` or `/auth/deletion-requests` caller anywhere → AC-33
- [ ] After the removal: `GET /auth/users` with an admin token → 404; `GET /auth/activity` → still 200; the portal admin People, Deletion requests and Activity views still work → AC-33
- [ ] Contract 0001 reads `**Contract version**: 9` → AC-33
