# Verify: sessions, refresh and logout · spec 0003 · updated 2026-11-08
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
