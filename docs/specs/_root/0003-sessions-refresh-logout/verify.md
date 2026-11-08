# Verify: sessions, refresh and logout · spec 0003 · updated 2026-11-08 (milestone 2)
_Steps derived from spec 0003 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones. Ticked steps passed during `/develop` on the local stack (curl or one Playwright pass), 2026-11-08._

## Milestone 1: the web thread

### UI / manual
- [x] Open `http://localhost:8001/repairs?status=open#top` with no cookie → the portal form with `?request=` → sign in → back on the same path and query, tickets load; `localStorage` and `sessionStorage` empty, `document.cookie` empty, no token in any URL → AC-11, AC-13 to AC-16, AC-19, AC-20
- [x] Open the portal (`http://localhost:8000/`) directly with a live SSO session → it skips the form and goes to VRMS → AC-12, AC-36
- [ ] Open `http://localhost:8000/login?reason=logout` and `?reason=idle` with a live session → the form shows with its message, and no `/auth/sso` call → AC-36
- [ ] Open `http://localhost:8000/?error=NO_SYSTEM_ACCESS&system=VRMS`, then `LOGIN_REQUEST_EXPIRED`, `LOGIN_STATE_INVALID`, `LOGIN_FAILED` → a plain message with Sign in again each → AC-36
- [ ] Two VRMS tabs open past 14 minutes → only one `POST /vrms/session/refresh` fires, and the other tab takes the token from the `vrms-session` channel → AC-21
- [ ] Sign in, wait for the boot flag case: answer the first refresh with 401 twice within 2 minutes (for example by deleting the session row while on the login trip) → `<portal>/?error=LOGIN_FAILED`, no loop → AC-20

### Commands
- [x] `GET /vrms/session/callback` a second time with the same `code` and `state` → 302 `<portal>/?error=LOGIN_STATE_INVALID`, welinc-auth not called → AC-15
- [ ] Exchange one login code twice at `/auth/token` (VRMS client assertion) → the second answers `invalid_grant` and the session ends with `CODE_REUSE` → AC-15
- [x] Present the previous `vrms_rt` within 10 s of a rotation → 200 with the same new refresh token → AC-8
- [x] Present it again after 10 s → 401 `SESSION_ENDED`, the session row has `end_reason = REFRESH_REUSE`, no unused tokens left, and the owner's current cookie fails too → AC-5, AC-9
- [ ] Send two refreshes with one cookie at the same moment → both 200 with the same new token, one rotation in `refresh_tokens` → AC-10
- [ ] Call `/vrms/permissions/me` with an expired access token → 401 `TOKEN_EXPIRED`; in the app, the call is retried once after a refresh → AC-21, AC-27
- [ ] Call `/auth/session` and a VRMS route with an S2 style token (no `sid`) → 401 `SESSION_ENDED` → AC-1
- [x] `POST /vrms/session/refresh` with `Origin: http://evil.test` → 403 `CSRF_REJECTED`; `POST /auth/login` with no `Origin` → 403 `CSRF_REJECTED` → AC-17
- [x] Preflight and a 401 from `http://localhost:8001` carry `Access-Control-Allow-Origin` and `Allow-Credentials`; an unknown origin gets neither; every answer has `Vary: Origin` → AC-18
- [x] `GET /auth/authorize` with an unregistered `redirect_uri` → 400 escaped error page, no redirect; with no SSO cookie → 302 `<portal>/login?request=` → AC-13
- [ ] `GET /auth/authorize/resume` with a used or expired request → 302 `<portal>/?error=LOGIN_REQUEST_EXPIRED` → AC-14
- [ ] `docker stop welinc_auth_service`, then refresh → 503 `AUTH_UNAVAILABLE` and `vrms_rt` is kept; start it again → refresh works → AC-16a
- [ ] Remove the user's VRMS role, then refresh → 403 `NO_SYSTEM_ACCESS`, `vrms_rt` cleared, nothing rotated; the app lands on `<portal>/?error=NO_SYSTEM_ACCESS&system=VRMS` → AC-41
- [ ] Log one user in 11 times → the session with the oldest `last_activity_at` ends with `MAX_SESSIONS`; 10 stay live → AC-6
- [ ] Deactivate a signed in user → within 30 s their VRMS requests answer 401 → AC-26 (milestone 2 ends the row itself)

### Value sourcing
- [ ] After a refresh from VRMS, `sessions.last_seen_ip` is the address backend-vrms saw (`X-WeLinc-User-Address`); the same header sent without an assertion changes nothing → AC-43
- [ ] `vrms_rt` and `welinc_sso` expire at login + 12 hours, not at the 30 minute idle cutoff; `sessionExpiresAt` in the refresh answer is the idle bound one and doesn't move on refresh → AC-2, AC-16
- [ ] `/auth/login` answers `url` from `oauth_clients.web_address` of the picked system's client (change `CLIENT_VRMS_WEB_ADDRESS`, run `seed:clients`, log in) → AC-11
- [ ] `aud` in a code exchange token is the client's system, and `roles` holds only that system's roles → AC-1, AC-41

## Acceptance criteria coverage (milestone 1)
- AC-1 · 1st UI step, S2 token step, value sourcing `aud` · AC-5 · reuse step · AC-6 · 11 logins · AC-7 to AC-10 · grace, reuse, race steps · AC-11 to AC-15 · UI steps, authorize and code steps · AC-16, AC-16a · callback, auth stopped · AC-17, AC-18 · CSRF and CORS steps · AC-19 to AC-21 · UI steps, expired token · AC-26, AC-27 · deactivate, expired token · AC-36 · portal steps · AC-40 · contract 0001 edited in the same change (workspace commit `a1d39f7`) · AC-41 · role removed · AC-43 · value sourcing

## Milestone 2: session endings and idle
_Ticked steps passed during `/develop` on the local stack (curl, `psql` in the container, one Playwright pass), 2026-11-08. To bring the idle warning on fast, pull the live row's `idle_expires_at` to `now() + 75 s` and reload the tab._

### UI / manual
- [x] With the cutoff 75 s away, reload → "Are you still there?" opens 60 s before it, with a countdown, **Log out** and **Stay signed in** → AC-23
- [x] **Stay signed in** → the dialog closes, the server cutoff is back at +30 minutes → AC-23
- [x] Leave the warning unanswered → at the cutoff the tab goes to `<portal>/login?reason=idle`, the row ends `IDLE`, the portal shows its idle message → AC-3, AC-23
- [ ] The warning opens with focus on **Stay signed in**, so Enter keeps the session (fixed after the pass) → AC-23
- [x] Two VRMS tabs, Sign out in one → both land on `<portal>/login?reason=logout` at once → AC-24
- [ ] Type in tab A, leave tab B alone past 29 minutes → B's status check finds the later cutoff and reschedules, no dialog → AC-2, AC-23
- [ ] A tab left alone (refreshing in the background every 14 minutes) is still warned and signed out at 30 minutes → AC-2
- [ ] `docker stop welinc_auth_service` until a background refresh fails → the "Reconnecting" banner, retries at 5, 15, 30 s then every 30 s, the page keeps working; start it again → the banner clears → AC-25
- [ ] Keep it stopped past the access token's expiry → the tab leaves for the portal → AC-25
- [ ] Sign out while welinc-auth is stopped → "Couldn't sign out" with **Try again**; start it, **Try again** → the session ends through the bearer's `sid` → AC-24
- [ ] A session at its 12 hour limit (set `absolute_expires_at` close) → Stay signed in shows "reached its 12 hour limit" and only **Log out** → AC-23

### Commands
- [x] Three `POST /vrms/session/activity` in a row → all 204; only the first two move `last_activity_at` → AC-22, AC-38
- [x] Activity with `Origin: http://evil.test` → 403 `CSRF_REJECTED`; with no cookie → 401 `SESSION_ENDED` → AC-17
- [x] `POST /vrms/session/logout` with cookie and bearer → 204, `vrms_rt` cleared, `end_reason = LOGOUT`, SSO handle null, no unused tokens; then refresh, `/auth/session`, a VRMS route and `/auth/sso` all answer 401 → AC-4, AC-5, AC-24
- [x] Logout with only the bearer (no cookie) → the session ends by `sid`; a garbage bearer and no cookie → 204, nothing ends → AC-24, AC-42
- [x] Password change on device 2 (`PATCH /auth/profile/password`) → device 1 ends `PASSWORD_CHANGED`, device 2 stays live → AC-4
- [x] Deactivate (`PATCH /auth/users/:id/status`) → every session ends `DEACTIVATED` with `ended_by_id`; admin password set → every session ends `PASSWORD_CHANGED` → AC-4
- [x] 5 failed logins → locked, the live session stays and refresh still answers 200; an OTP reset then ends it (`PASSWORD_CHANGED`) → AC-4
- [x] Age a session past its cutoff, run two sweeps at once → one skips on the advisory lock, the other ends it `IDLE` (sid, user, reason, client logged) and clears expired grace ciphers, login requests and codes → AC-3, AC-37, AC-39
- [ ] Delete a user (`DELETE /auth/users/:id`) → their sessions end `DELETED` → AC-4
- [ ] Activity with a refresh token used less than 10 s ago → 204; after 10 s → 401 and the session stays live → AC-42
- [ ] `/auth/logout` from another confidential client with a `sid` it never held → 204, nothing ends → AC-42
- [ ] Sweep with sessions ended more than 90 days ago and refresh tokens of sessions ended more than 1 day ago → both deleted, 1,000 per statement → AC-37
- [ ] After these runs, grep the welinc-auth log → no refresh token, code, SSO handle or request id; session lines carry only `sid`, user, reason and client → AC-39

### Value sourcing
- [x] After VRMS activity, `sessions.last_seen_ip` is the address backend-vrms forwarded → AC-43
- [ ] The same `X-WeLinc-User-Address` without an assertion changes nothing → AC-43
- [ ] A web refresh never moves `last_activity_at`; activity, login and a code exchange do → AC-2

## Acceptance criteria coverage (milestone 2)
- AC-2 · idle tab, tab A and B, value sourcing · AC-3 · unanswered warning, sweep · AC-4 · logout, password change, deactivate, admin set, lock and OTP, delete · AC-6 · built in milestone 1 (cap in `createWeb`), its 11 logins step above · AC-22 · three pings · AC-23 · warning, Stay signed in, unanswered, focus, 12 hour limit · AC-24 · two tabs, logout steps, logout while down · AC-25 · Reconnecting steps · AC-37 · sweep steps · AC-38 · three pings · AC-39 · log grep, sweep log · AC-42 · bearer only logout, grace activity, foreign sid
