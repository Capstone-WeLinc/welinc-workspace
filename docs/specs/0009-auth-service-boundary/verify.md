# Verify: Auth service boundary · spec 0009 · updated 2026-10-27
_Steps derived from spec 0009 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Reset and seed both databases first (`npx prisma migrate reset` in welinc-auth, then in welinc-backend-vrms). Restart `welinc_auth_service` and `welinc_vrms_backend` after code changes. Sign in through the portal as `vrms.admin@welinc.com` (seed) unless a step says otherwise.

## API / backend

### One owner
- [x] `POST localhost:3002/auth/login` with a seeded email and password → 404 → AC-1
- [ ] `welinc-backend-vrms/src/auth/` holds only the guards, decorator, strategy, `account-check.ts` and `roles.ts`; `src/auth/dto/` is gone → AC-1
- [x] `prisma/schema.prisma` in backend-vrms has no `User`, `UserRoleAssignment`, `PasswordResetToken`, `RefreshToken`, `UserRole`, `SystemType`; no backend-vrms import of `UserRole` or `SystemType` from `@prisma/client` → AC-2
- [x] Search backend-vrms for `passwordHash`, `otp`, `roleAssignment` → no hits outside migrations → AC-3

### Account check
- [x] Any `/vrms/*` call with a valid token → one `GET /auth/me?system=VRMS` reaches welinc-auth (its log); a second call within 30 s → none; after 30 s → one again → AC-4
- [x] Audit row written by a mechanic carries their welinc-auth `name` as `actorName` → AC-4, AC-10
- [x] Deactivate a signed in mechanic in welinc-auth; within 30 s their `GET /vrms/repairs` → 401 → AC-5
- [x] Lock a user (5 bad sign ins) while their token is live; within 30 s → 403 with the lock message → AC-5
- [x] Change a mechanic to ADMIN only; within 30 s an admin only route works for them and the mechanic rules no longer apply → AC-5
- [x] `docker stop welinc_auth_service`; a fresh token → 503 with "Sign in service unavailable. Try again in a moment."; a token checked under 30 s ago still works until its 30 s end; no row changes in either case → AC-6
- [x] With auth stopped, a 503 is not cached: start it again and the next call succeeds at once → AC-7
- [x] A token whose check returned 401 keeps returning 401 only while welinc-auth says so (reactivate → next call works) → AC-7
- [ ] Load the dashboard (several parallel requests) with an empty cache → welinc-auth logs one `/auth/me` call for that token, not one per request → AC-4
- [ ] Start backend-vrms with `AUTH_SERVICE_URL` unset → it refuses to start → AC-4
- [x] Call `GET /auth/me?system=VRMS` on welinc-auth with `Origin: http://localhost:8003` (BMS) → it still checks VRMS → AC-24
- [x] User with only BMS roles calls a VRMS route → 401 "User does not have access to this system" → AC-25
- [ ] Point `AUTH_SERVICE_URL` at a URL that returns HTML or 429 → VRMS answers 503 → AC-25

### VRMS data on the auth id
- [x] `mechanics` rows: in house rows have `auth_user_id` equal to the welinc-auth `users.id` for the same email; outsourced rows have null → AC-8, AC-22
- [x] `GET /vrms/mechanics/available` items include `authUserId` and `email` → AC-9
- [x] Audit filter `?actorId={welinc-auth id}` returns that person's rows; `GET /vrms/repairs/audit-logs/actors` returns ids that are welinc-auth ids with names, no entry with a null id, and the name from each person's newest row → AC-10
- [x] `POST /vrms/repairs` with an in house mechanic `id` → assigned to that row; an unknown or inactive id → 400 "In house mechanic not found"; two mechanics with the same name are assigned correctly by id → AC-27

### Sync
- [x] Create a user with role MECHANIC straight through `POST /auth/users`; `POST /vrms/mechanics/sync` → `created: 1`; call it again → all zeros → AC-11
- [x] Rename that user in welinc-auth; sync → `updated: 1` and the row's name and email follow → AC-11
- [x] Deactivate them; sync → `updated: 1` (a deactivated user is still on the list), row `is_active = false`; reactivate and sync → active again → AC-11, AC-14
- [x] Change them to ADMIN only; sync → their row goes inactive → AC-11
- [x] Fire two syncs at once → one row per `auth_user_id`, no 500 → AC-11
- [x] Lock a mechanic (5 bad sign ins), then sync → their row goes inactive and leaves the picker; unlock and sync → back → AC-11
- [x] Soft delete a mechanic in welinc-auth, then sync → their row goes inactive → AC-11
- [x] Stored `mechanics.email` is lowercase even when welinc-auth holds mixed case → AC-11
- [ ] A just in time write that fails (make the row write throw) is logged and the request still succeeds → AC-13
- [x] Outsourced rows unchanged by any sync → AC-11
- [x] As a mechanic, `POST /vrms/mechanics/sync` → 403 → AC-11

### Just in time
- [x] Create a mechanic in welinc-auth with no sync; they sign in and open a page → a `mechanics` row with their `auth_user_id` exists → AC-13
- [x] Repeat with two parallel first requests (two tabs) → still exactly one row → AC-13

### welinc-auth hardening
- [x] `forgot-password` and `PATCH /auth/users/:id` → `docker logs welinc_auth_service` shows no code and no request body → AC-16
- [ ] Reset email link starts with the configured `PORTAL_URL`; with `NODE_ENV=production` and no `PORTAL_URL` the service fails to start → AC-16
- [x] Lock a user, then complete a reset with the code → they can sign in; `locked_at` null, `failed_login_attempts` 0 → AC-17
- [x] `forgot-password` for an inactive user → generic message, no code row created, no mail → AC-17
- [x] Request two codes for one user → the first no longer works, the second does → AC-17
- [ ] With SMTP pointed at a dead host, `POST /auth/users` → 201 with `setupEmailSent: false`; the user exists → AC-18
- [x] As the only VRMS admin: deactivate yourself, change your own role, delete yourself → 409 with the three messages → AC-19
- [x] Create a second admin, then try to demote or deactivate the first from the second while the first is the last other admin → 409 "This is the last VRMS admin." only when it really is the last → AC-19
- [x] With exactly two admins, send "deactivate the other" from each at the same moment (two parallel requests) → one succeeds, the other gets 409; one active admin remains → AC-19

### Admin change record
- [x] Create a user → one `CREATED` row; edit name and contact → two `UPDATED` rows with old and new values; save with no change → no row → AC-20
- [x] Change roles → one `ROLE_CHANGED` row with sorted `ROLE@SYSTEM` lists → AC-20
- [x] Deactivate, reactivate, unlock, delete → `DEACTIVATED`, `ACTIVATED`, `UNLOCKED`, `DELETED` rows → AC-20
- [x] Send a reset code from the Users page → `RESET_SENT` with the admin as actor; the same call with no token (portal) → no row → AC-20
- [x] `user_changes` holds no password, hash or code value anywhere → AC-20
- [x] `GET /auth/users/:id/changes` newest first; `limit=2` gives a `nextCursor` that returns the next two; unknown id → 404; as a mechanic → 403 → AC-21

## UI / manual

- [x] Users page: add mechanic Pedro → open `/repairs/new` → Pedro is in the mechanic picker with no other step → AC-12, AC-11
- [x] Block `POST /vrms/mechanics/sync` (devtools) and add a mechanic → warning toast "Saved, but VRMS couldn't update its mechanic list. It will catch up next time this page opens."; unblock and reload `/users` → they appear in the picker → AC-12
- [x] With the sync blocked, opening `/users` or `/repairs/new` shows no toast and the page loads → AC-12
- [x] Deactivate a mechanic with an In progress ticket → still blocked with "Reassign … first" (match now by `authUserId`) → AC-9
- [x] Open `localhost:8001/login` with no token → lands on the portal login; sign in → back in web-vrms → AC-15
- [x] Stop `welinc_auth_service` while on the dashboard and wait 30 s → one error toast "Sign in service unavailable. Try again in a moment.", still signed in → AC-6
- [x] Lock a signed in user; within 30 s their next action signs them out to the portal with the lock message → AC-26
- [x] As a mechanic, call an admin only VRMS route → a toast with the 403 message, still signed in → AC-26
- [x] New repair: pick a mechanic, submit → the request body carries their `id`, not their name → AC-27
- [ ] As the only admin, try to deactivate yourself through the API (the button is hidden) → 409; any 409 the page triggers shows its message as is → AC-19
- [x] Sign in as a seeded mechanic through the portal → sees only their own tickets and can update one → AC-22

## Quality

- [x] welinc-auth and welinc-backend-vrms: `npm run lint`, `npm run build`, `npm run test` pass → AC-23
- [x] welinc-web-vrms: `npm run lint`, `npm run typecheck`, `npm run build` pass → AC-23
- [x] `git status` in welinc-web-portal shows no change; `welinc-auth/nginx.conf` unchanged → AC-23
