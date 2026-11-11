# 0011. Account activity and audit: verify

Run on the local stack through the gateway (`http://localhost:3000`). Use seed accounts from `docs/integration/seed-accounts.md`. Don't trigger setup or reset codes to real inboxes; use `state.unverified@` only for the sign in code step if mail is acceptable, else check code events with tests.

## Recording
- [x] Portal sign in as `vrms.admin@`, open VRMS, sign out → rows `SIGNED_IN`, `SYSTEM_OPENED` (system VRMS), `SIGNED_OUT`, each with the browser's address (not `172.x`) and `Chrome on Windows` or similar → AC-1, AC-3, AC-4
- [x] 5 wrong passwords on a seed account → 4 `SIGN_IN_FAILED` (`attempts_left` 4 to 1) and one `LOCKED_OUT`; the 6th → `SIGN_IN_FAILED` `ACCOUNT_LOCKED` → AC-1
- [x] Sign in as `state.deactivated@` → `SIGN_IN_FAILED` `ACCOUNT_INACTIVE` → AC-1
- [x] 5 wrong passwords sent in parallel on a fresh seed account → exactly one `LOCKED_OUT`, and every `SIGN_IN_FAILED` row is present after its 401 → AC-1b, AC-7
- [x] Sign in with `nobody@welinc.com` → no row; the auth log has the address and `@welinc.com` only → AC-2, AC-21
- [x] Two refreshes in parallel for a new system → one `SYSTEM_OPENED`; logout twice → one `SIGNED_OUT` → AC-4
- [x] Leave a session past idle and run the sweep → one `SESSION_ENDED` `IDLE`, actor null, no address → AC-4
- [x] Admin ends all sessions of a user → one `SESSIONS_ENDED` plus a `SESSION_ENDED` `ADMIN_ENDED` per session, each with system VRMS → AC-4, AC-6
- [x] VRMS admin deactivates a user with a live session → `DEACTIVATED` plus a `SESSION_ENDED` `DEACTIVATED` tagged VRMS → AC-4
- [x] A VRMS backend refresh without `X-WeLinc-User-Address` → the `SYSTEM_OPENED` address is null, not the backend's → AC-3
- [x] Change your own name, password and picture on VRMS My profile → `UPDATED` (name), `PASSWORD_CHANGED`, `PICTURE_CHANGED` → AC-6
- [x] Give a person a VRMS role while they hold a BMS role → one `ROLE_CHANGED` with system VRMS and only VRMS roles in the values → AC-6

## Storage
- [x] `UPDATE account_events SET reason = 'x'` → error; `DELETE FROM account_events` → error → AC-8
- [x] Set one non `ACCOUNT` row's `created_at` to 400 days ago and one `ACCOUNT` row the same, run the sweep → only the first is gone → AC-9
- [x] After migrating a database with `user_changes` rows → counts match (plus splits), `user_changes` is gone, `RESET_SENT` rows read `CODE_SENT` → AC-10

## Reading
- [x] `GET /auth/profile/activity` as a user whose role an admin changed → the row's actor is `{ kind: "ADMIN" }` only → AC-11
- [x] As a VRMS admin, `GET /auth/users/<bms only person>/activity` → 404 → AC-12
- [x] `GET /auth/activity?q=multi` → only VRMS members' account wide rows and VRMS tagged rows; no `SYSTEM_OPENED` for BMS → AC-13
- [x] `?category=SIGN_IN,SESSION&type=SIGNED_IN,SIGNED_OUT` → both types; `?userId=<bms only person>` → empty page, not 404 → AC-13, AC-14
- [x] `?type=SIGNED_IN&category=CODE` → 400 `VALIDATION_FAILED`; `?cursor=abc` → 400 `INVALID_CURSOR`; a service token → 403 `WRONG_TOKEN_USE`; 61 feed calls in a minute → 429 → AC-13, AC-14
- [x] `GET /auth/activity/catalog` twice with `If-None-Match` → 304 → AC-15
- [x] `GET /auth/users/:id/changes` → 404 → AC-16

## Location
- [x] With no `geo/` files: auth starts with one warning; rows have no country → AC-17
- [x] `npm run geo:fetch` → both files in `geo/`; with no network and `--soft` → a warning and exit 0 → AC-18
- [x] Restart auth, sign in with `X-Forwarded-For: 8.8.8.8` through a direct call to auth (trusted hop) → country `US`, network Google → AC-17
- [x] Local rows answer `localNetwork: true` and the UI shows "Local network" → AC-17, AC-19

## VRMS screens
- [x] My profile Recent activity: 10 rows grouped by day, Show more adds the next page, DB-IP credit visible, loading, empty and error states → AC-19
- [x] Users page row menu → Activity → dialog with category chips, actor names, Show more; at 375px and 1280px → AC-20

## Added by /develop (2026-11-12)
- [x] Locally every request reaches the gateway from the Docker bridge, so rows read `172.19.0.1` (Local network). Check the real address instead with a direct call to auth (it trusts one hop): `POST http://localhost:3001/auth/login` with `X-Forwarded-For: 112.198.0.1` and a wrong password → the row's address is `112.198.0.1`, country `PH`, network Globe Telecom. Replaces "not `172.x`" in the first Recording step for local runs → AC-3, AC-17
- [x] Feed day edges: a row written at 23:30 Manila on the 11th (15:30 UTC) shows with `to=2026-11-11` and not with `from=2026-11-12` → AC-13, value sourcing (date filters)
- [x] Users page, Send reset code on someone → one `CODE_SENT` (reason `PASSWORD_RESET`) with you as actor; their own Recent activity reads "An admin sent you a code" without your name → AC-5, AC-11
- [x] Mobile login (`POST /auth/mobile/login` with `deviceName: "Pixel 8"`) → `SIGNED_IN` and `SYSTEM_OPENED` (VMMS) in the same second, device `Pixel 8` → AC-1, AC-4
- [x] Users page, Activity on Gilbert Navarro (his failed try from `112.198.0.1` has a place) → "Philippines · Globe Telecom" on the row and the "IP data by DB-IP" credit under the list → AC-18, AC-20
