# Verify: sessions, refresh and logout · spec 0003 · updated 2026-11-08 (milestone 4)
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

## Milestone 3: mobile routes
_Ticked steps passed during `/develop` on the local stack (curl through the gateway, `psql` in the container), 2026-11-08. Users: `vmms.admin` (VMMS only), `mech.carl` (VMMS and VRMS), `vrms.admin` (no VMMS). The login limit is 5 a minute per address, so space the logins out._

### Commands
- [x] `POST /auth/mobile/login` with `clientId: "vmms-mobile"` and `deviceName: "  Pixel 8 (Android 15)  "` → 200 `{ accessToken, refreshToken, expiresIn, sid, sessionExpiresAt, user }`, no `Set-Cookie`, `Cache-Control: no-store`; the row is `MOBILE`, `vmms-mobile`, device `Pixel 8 (Android 15)`, audiences `{VMMS}`, no absolute limit, no SSO handle, idle cutoff 7 days out; the token's `aud` is `VMMS` → AC-28
- [x] Mobile login for `vrms.admin` → 403 `NO_SYSTEM_ACCESS`; with `clientId: "vrms"` → 400 `INVALID_CLIENT`; a wrong password counts toward the shared lockout (`remainingAttempts: 4`) → AC-28
- [x] Refresh with `client_id=vmms-mobile` and no assertion → 200, rotated, `aud` `VMMS`, no `session_absolute_expires_at` → AC-29
- [x] `audience=VRMS` for `vmms.admin` → 403 `NO_SYSTEM_ACCESS`; `audience=BMS` → `invalid_target`; the same token still refreshes after both (nothing rotated) → AC-29, AC-41
- [x] `audience=VRMS` for `mech.carl` → a VRMS token with only VRMS roles, `audiences` `{VMMS,VRMS}`; backend-vrms answers 200 on `/vrms/permissions/me` with it → AC-29
- [x] Refresh with `client_id=vrms` and no assertion → `invalid_client` → AC-29
- [x] Last activity 3 days ago, then a refresh → the idle cutoff is back at 7 days; past the cutoff → `invalid_grant` and the row ends `IDLE` → AC-2, AC-29
- [x] Two refreshes with one mobile token inside 10 s → the same new token → AC-8, AC-29
- [x] The old mobile token after its grace → `invalid_grant`, the session ends `REFRESH_REUSE` → AC-9, AC-29
- [x] `POST /auth/logout` with `{ refreshToken, clientId: "vmms-mobile" }` (even an already used token of the session) → 204, the row ends `LOGOUT`, no unused tokens; again → 204; an unknown token, or the right token with `clientId: "vrms"` → 204 and nothing ends → AC-30
- [x] 6 or more mobile logins in a minute from one address → 429 `rate_limited` with `Retry-After` → AC-38
- [x] More than 30 `vmms-mobile` refreshes in a minute from one address → 429 → AC-38
- [x] The log lines for these runs carry `sid`, user, reason, client and `aud`, never a token → AC-39

### Value sourcing
- [x] `created_ip` is the request address through `TRUST_PROXY_HOPS` (locally the Docker bridge, `172.21.0.1`) → AC-28
- [x] A mobile refresh sets `last_seen_ip` from the request address, and an `X-WeLinc-User-Address` header on it is ignored → AC-43

## Acceptance criteria coverage (milestone 3)
- AC-28 · login, no access, client, lockout, row values · AC-29 · refresh, audience steps, idle roll, grace, reuse · AC-30 · logout steps · AC-38 · both limit steps · AC-2 (mobile) · idle roll and cutoff

## Milestone 4: seeing and ending sessions
_Ticked steps passed during `/develop` on the local stack (curl through the gateway, `psql`, one Playwright pass at desktop width), 2026-11-08. Make sessions to look at with a few web logins under different `User-Agent` values and one mobile login._

### UI / manual
- [x] Profile page → **Signed in devices** lists each live session: device label, systems, "active <relative time>", **This device** on the current one, **End** on every other row → AC-34
- [x] **End** on another device → a `destructive` confirm naming the device → the row goes, a toast says it signed out, and that session's token answers 401 → AC-31, AC-34
- [ ] Only this device signed in → "No other devices are signed in." under its row; the list failing → the error state with Try again; loading → two skeleton rows → AC-34
- [x] Users page, a user's ⋮ menu → **Sessions** opens a dialog listing their sessions (a mobile one shows the reported name and `VMMS`) → AC-35
- [x] **End all sessions** → a `destructive` confirm with the count → ended `ADMIN_ENDED`, one `SESSIONS_ENDED` change holding the count, a toast "signed out of 3 devices", and the dialog shows "Not signed in anywhere right now." with the button off → AC-32, AC-35
- [ ] Your own row on the Users page has no **Sessions** item → AC-35
- [ ] At 375px the card rows and the dialog (a bottom sheet) don't overflow with a long device name → AC-34, AC-35

### Commands
- [x] `GET /auth/me/sessions` → newest activity first, `current: true` only on the caller's `sid`, labels `Chrome on Windows` and `Firefox on macOS` from their `User-Agent` → AC-31, AC-33
- [x] `DELETE /auth/me/sessions/<another user's sid>` → 404; your other session → 204, `USER_ENDED`; the same again → 204 → AC-31
- [x] A mechanic on `GET /auth/users/:id/sessions` → 403; a VMMS admin on a VRMS only user → 404; a bad id → 400 → AC-32
- [x] `DELETE /auth/users/<your own id>/sessions` → 403 with the "Use Signed in devices" message → AC-32
- [x] `DELETE /auth/users/:id/sessions` → `{ ended: 1 }`, the row `ADMIN_ENDED` with the admin as `ended_by_id`, one `SESSIONS_ENDED` change (`new_value` the count, the admin as actor); the user's token then answers 401 → AC-32
- [ ] A list right after a session's idle cutoff passed (before the sweep) leaves that session out → AC-31
- [ ] The parser labels Edge, Opera, Samsung Internet and Safari on iPad, and an empty `User-Agent` reads "Unknown browser on Unknown OS" → AC-33 (a `/test` unit test fits best)

## Acceptance criteria coverage (milestone 4)
- AC-31 · list, end one, foreign sid, cutoff · AC-32 · refusals, own id, end all · AC-33 · labels in the list, parser cases · AC-34 · card, End, states, 375px · AC-35 · dialog, End all, own row, 375px
