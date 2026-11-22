# 0003. Sessions, refresh and logout for web and mobile

**Date**: 2026-11-08
**Status**: Accepted
**Amended**: 2026-11-23, AC-23's warning is suite spec [0016](../0016-design-direction-refresh/index.md)'s signing out soon banner (its AC-12, AC-12b); value sourcing follows
**Scope row**: [S3. Sessions: refresh and logout, web and mobile](../../../scope/_root/shared-services.md#s3-sessions-refresh-and-logout-web-and-mobile--done)
**Builds contract sections**: [0001](../0001-shared-services-contract/index.md) sections 5 (refresh grant, opaque values), 6 (sessions, session check), 7 (web login flow, cookies, CSRF guard), 8 (mobile login), 10 (session routes), 12 (limits)

## Summary

A login becomes a real session that welinc-auth tracks on the server. It ends at logout, after 30 minutes without use, after 12 hours, or when an admin or a security event ends it. Web apps stop keeping a token in `localStorage` or getting one through the URL. Instead each system's backend holds a refresh cookie that page scripts can't read, and swaps it for a short lived access token kept in memory. This spec also builds the web code exchange that contract 0001 had put in S4, because a web app can only get that cookie through the exchange. That leaves S4 with the launcher and Switch system. VRMS and the portal move over in one hard switch, and the mobile routes are built and tested now so VMMS can use them in S11.

## Rationale

Reasoning, options and the current state: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As a VRMS user, I want to stay signed in while I work and be signed out when I walk away, so a shared shop PC doesn't stay open on my account.
- As a VRMS user, I want logout in one app to end my session in every system, and I want to see and end my other devices.
- As a VRMS admin, I want to end all of a user's sessions at once, after a lost phone or a staff member leaving.
- As the shared services owner, I want tokens out of URLs and browser storage, and a stolen refresh token to be useless once the real owner uses theirs.
- As the VMMS group, I want tested mobile login, refresh and logout routes ready when we move in S11.

**Acceptance criteria**:

*Sessions on the server*
- **AC-1**: Every login creates one `sessions` row. Every user access token from that login carries its `sid` (the session id) and `client_id`. A token with no `sid` (the S2 interim token) gets 401 `SESSION_ENDED` from `/auth/session` and from every VRMS route.
- **AC-2**: A web session ends 30 minutes after its last activity or 12 hours after login, whichever comes first (`WEB_SESSION_IDLE_MINUTES`, `WEB_SESSION_MAX_HOURS`). For web sessions, activity means only a real input ping, a login or a code exchange. A refresh is never activity for a web session. A mobile session ends 7 days after its last refresh (`MOBILE_SESSION_IDLE_DAYS`), and each mobile refresh extends it.
- **AC-3**: An idle or max age cutoff is enforced at the next check, with no wait for a job. The first `/auth/session`, refresh or activity call after the cutoff ends the session (`IDLE` or `MAX_AGE`) and answers 401 `SESSION_ENDED`. The hourly job ends the rest.
- **AC-4**: These end a session at once, with the reason recorded: logout (`LOGOUT`), the user ending one of their sessions (`USER_ENDED`), an admin ending them (`ADMIN_ENDED`), deactivation (`DEACTIVATED`), soft delete (`DELETED`), refresh token reuse (`REFRESH_REUSE`), login code reuse (`CODE_REUSE`), and an 11th live session (`MAX_SESSIONS`, which ends the least recently active one). A password change on `PATCH /auth/profile/password` ends every other session of that user (`PASSWORD_CHANGED`) and keeps the current one. An OTP password reset and an admin password set (`PATCH /auth/users/:id/password`) end all of them. The automatic lock after 5 failed logins blocks new logins only and ends no live session, so a stranger who knows an email can't sign a mechanic out mid shift; `/auth/session` doesn't refuse a locked account's live session.
- **AC-5**: Ending a session also ends its SSO handle and every refresh token under it. No ended session can be revived by any route.
- **AC-6**: A user holds at most `MAX_SESSIONS_PER_USER` (10) live sessions. The login transaction takes `pg_advisory_xact_lock` on the user id before counting, so two logins at once can't both pass. When the new session would be the 11th, the live session with the oldest `last_activity_at` ends (`MAX_SESSIONS`) before the new one is created.

*Refresh tokens*
- **AC-7**: Refresh tokens are 256 bit random values, stored only as SHA-256 hashes, one row per issued token. Each use rotates the token, marks the old row used and links it to the new one. At most one unused token exists per (session, client). A code exchange for a (session, client) that already holds an unused token (the cookie was lost but the session lives) marks that token used, with no grace, before inserting the new one.
- **AC-8**: Within `REFRESH_REUSE_GRACE_SECONDS` (10) of a rotation, presenting the previous token again returns the same new refresh token and a freshly signed access token, without ending anything. This works when the retry lands on a different welinc-auth replica.
- **AC-9**: Presenting a used token after its grace window ends the whole session (`REFRESH_REUSE`) and answers `invalid_grant`. A token that matches no row answers `invalid_grant` and ends nothing.
- **AC-10**: Two refreshes racing with the same token never both rotate it. Exactly one rotates, and the other gets the grace answer.

*Web login and the code exchange (VRMS and the portal)*
- **AC-11**: `POST /auth/login` from the portal checks the password (the existing lockout and reCAPTCHA stay), creates a web session, and sets the `welinc_sso` cookie (contract section 7 cookie table). It answers `{ user: { id, name, email }, system, url }` and never a token. `system` is the system welinc-auth picks today (spec 0002), and `url` is that client's web address. A user with no system role gets 403 `NO_SYSTEM_ACCESS` and no session. If the browser already holds a valid SSO cookie, that session ends (`LOGOUT`) and the new one replaces it, whoever it belonged to. (Since spec 0007 the body is the launcher answer `{ user: { id, name, email, picture }, systems: [...] }`, with no pick; contract 0001 section 10.)
- **AC-12**: `GET /auth/sso` with a valid SSO cookie answers `{ user, system, url }` (the same pick, until S4 adds the launcher list; spec 0007 did, so it now answers the same launcher body as `/auth/login`). Without a valid cookie it answers 401 `SESSION_ENDED`.
- **AC-13**: `GET /auth/authorize` checks `client_id` and the exact `redirect_uri` against the registry, and requires `code_challenge_method=S256`. On a bad client or address it shows an error page and never redirects. With a valid SSO cookie and a role in the client's system, it redirects to the callback with a code and the `state`. With a valid cookie but no role there, it redirects with `error=access_denied`. With no valid cookie, it stores a login request and redirects to `<portal>/login?request=<id>`. Inputs are capped (`state` at most 512 characters, `redirect_uri` at most 2048), `code_challenge` must be 43 base64url characters, the route allows 30 a minute per address, and the error page escapes everything it shows.
- **AC-14**: `GET /auth/authorize/resume?request=<id>` continues an unused, unexpired login request for a browser with a valid SSO cookie. An expired or used request redirects to `<portal>/?error=LOGIN_REQUEST_EXPIRED`.
- **AC-15**: A login code lives 60 s and works once. It is bound to its client, redirect address, PKCE challenge and `sid`. The `authorization_code` grant on `/auth/token` checks all four plus the client assertion. A second use of a code ends that session (`CODE_REUSE`). The VRMS callback checks and deletes its login state cookie before it calls `/auth/token`, so a browser retry or prefetch of the callback fails as `LOGIN_STATE_INVALID` and never reaches welinc-auth.
- **AC-16**: backend-vrms serves `GET /vrms/session/start`, `GET /vrms/session/callback`, `POST /vrms/session/refresh`, `POST /vrms/session/activity`, `POST /vrms/session/logout` and `GET /vrms/session/status` exactly as contract section 7 and the API surface below say. That includes the `return` check (same origin as `WEB_APP_URL`, else `/`), the login state cookie, the `vrms_rt` refresh cookie, and the callback failures mapped to `NO_SYSTEM_ACCESS`, `LOGIN_STATE_INVALID` and `LOGIN_FAILED` on the portal. The state cookie is named per attempt, `vrms_login_<first 8 characters of state>` (`__Secure-` prefixed when hosted), so several tabs logging in at once don't overwrite each other. `vrms_rt` lives for the session's remaining absolute time (12 hours from login), as contract section 7 says, not the idle cutoff. backend-vrms reads that end from `session_absolute_expires_at` in the `/auth/token` answer.
- **AC-16a**: backend-vrms calls welinc-auth with a 3 s timeout. On `refresh`, only `invalid_grant` or a `SESSION_ENDED` answer gives 401 `SESSION_ENDED` and clears `vrms_rt`; a 403 `NO_SYSTEM_ACCESS` gives 403 `NO_SYSTEM_ACCESS` and clears it; anything else (`invalid_client`, `invalid_target`, 429, 5xx, a timeout, a network error) gives 503 `AUTH_UNAVAILABLE` and keeps the cookie.
- **AC-17**: Every cookie authenticated route (`/vrms/session/refresh`, `activity`, `logout`, and welinc-auth's `/auth/login`, `/auth/logout`, `/auth/session/activity` with the SSO cookie) runs the CSRF guard: POST only, `Content-Type: application/json`, `Origin` exactly equal to the allowed web address (`WEB_APP_URL` for VRMS routes, `PORTAL_URL` for welinc-auth), and `Sec-Fetch-Site` `same-origin` or `same-site` when sent. Anything else gets 403 `CSRF_REJECTED`. GET routes that a page navigation reaches (`/auth/sso`, `/auth/authorize`, `/auth/authorize/resume`, `/vrms/session/start`, `/vrms/session/callback`) change no state a third party can trigger usefully and skip the guard, since a navigation sends `Sec-Fetch-Site: none` or `cross-site`.
- **AC-18**: The gateway answers CORS for `/auth` and `/vrms` (plus the VMMS and BMS prefixes since spec 0008, which also dropped `/repairs`) only for an exact allow list of web origins, and sends `Access-Control-Allow-Credentials: true` only for those. It never echoes an unknown `Origin`. Every CORS header carries `always` (so a 401 or 403 stays readable by the app), responses send `Vary: Origin`, and a preflight (`OPTIONS`) from an allowed origin answers 204 with the methods and the `Authorization` and `Content-Type` headers.

*The VRMS web app*
- **AC-19**: web-vrms holds the access token in memory only. Nothing in web-vrms reads or writes a token, a user or a last active stamp in `localStorage`, and nothing reads `?token=`. The `/login` route, `LoginPage`, `SsoHandoff`, `processToken` and `SessionMonitor` are gone. A `sessionStorage` flag for the boot loop guard is the one exception (contract section 7).
- **AC-20**: On load the app follows the contract's boot sequence. It refreshes; on 401 it goes to `start` once with the flag set; if it is still 401 after coming back, it sends the browser to `<portal>/?error=LOGIN_FAILED`. The flag holds a timestamp, is cleared on any 200, and is ignored once older than 2 minutes, so a tab that comes back later starts fresh. A deep link (path and query) survives the trip.
- **AC-21**: The app refreshes 60 s before `expiresIn` runs out, under the Web Lock `vrms-refresh`, so only one tab refreshes at a time. The tab that refreshes posts `{ accessToken, expiresAt, sessionExpiresAt }` on the `vrms-session` BroadcastChannel; a tab holding the lock first checks whether it already received a token that is still good for more than 60 s, and if so skips its own refresh. The channel is same origin and the token stays in memory. If an API call still gets 401 `TOKEN_EXPIRED`, the app refreshes once and retries that call once. A 401 `SESSION_ENDED` from any call drops the token and goes to `<portal>/login`.
- **AC-22**: While there is real input (key, click, touch, wheel), the app sends `POST /vrms/session/activity` at most once a minute. Background polling and timers never send it.
- **AC-23**: The app checks `GET /vrms/session/status` 60 s before the cutoff it knows. If the server cutoff is later (work in another tab or system), it reschedules quietly. If not, it shows a warning dialog with a countdown and two actions: **Stay signed in** (sends an activity ping, then checks status again) and **Log out**. When the cutoff is the session's 12 hour end (`sessionAbsoluteExpiresAt` from the last refresh, or Stay signed in finds the cutoff didn't move), nothing can extend it: the dialog says so and offers **Keep working** (closes it; a banner keeps counting down to the end) and **Sign out now**, and Escape counts as Keep working. When the cutoff passes, it goes to `<portal>/login?reason=idle`, or `<portal>/login?reason=maxage` when the cutoff was the 12 hour end. _Amended 2026-11-23 (suite spec 0016, AC-12): VRMS and the portal show this warning as the signing out soon banner instead of a dialog, checked 120 s before the cutoff, with **Stay signed in** and no Log out; at the 12 hour end the banner has no action. The cutoffs, the status check, the rescheduling and the `reason` stay as written here. VMMS and BMS may keep the dialog until their groups adopt spec 0016._
- **AC-24**: Logout calls `POST /vrms/session/logout` (with the access token as well as the cookie), then sends the browser to `<portal>/login?reason=logout`, where the portal always shows the form. If the cookie's token is used or unknown, backend-vrms ends the session from the bearer token's `sid` instead (through `/auth/logout` with its client assertion and `sid`). If the logout call fails, the app says so and offers to try again rather than leaving quietly. Other open VRMS tabs get a `vrms-session` BroadcastChannel message and do the same at once. Other systems lose the session at their next session check (30 s at most).
- **AC-25**: When welinc-auth or backend-vrms can't be reached during a refresh (503 `AUTH_UNAVAILABLE` or a network error), the app keeps its current token until it expires, shows a quiet "Reconnecting" banner, and retries at 5, 15 and 30 s, then every 30 s. It leaves for the portal only on a real 401 `SESSION_ENDED`, or once the current token has expired and a refresh still fails.

*Session check in backend-vrms*
- **AC-26**: Every VRMS request with a user token runs the session check (contract section 6) against `GET /auth/session`. The answer is cached by `sid` for at most 30 s, and the check fails closed (503 `AUTH_UNAVAILABLE`) with no fresh cached answer. `/auth/session` answers `{ active: true, sid, expiresAt, user: { id, name, email } }`, and backend-vrms takes the caller's name from it, so `/auth/me` is no longer called per request. `GET /vrms/session/status` always asks fresh and refreshes the cache. An ended answer (401) is cached too, until that token's `exp`. Concurrent misses for the same `sid` share one call to welinc-auth (single flight).
- **AC-27**: An expired access token gets 401 with `code: TOKEN_EXPIRED`. Any other bad token gets 401 with `code: SESSION_ENDED` or the existing codes.

*Mobile (`vmms-mobile`, built and tested by API)*
- **AC-28**: `POST /auth/mobile/login` with `{ email, password, clientId: "vmms-mobile", deviceName }` creates a mobile session and answers contract section 8's body in camel case, with no cookie. It shares the per account lockout, and it is limited to 5 a minute per address. A user with no VMMS role gets 403 `NO_SYSTEM_ACCESS`.
- **AC-29**: The mobile refresh (`grant_type=refresh_token`, `client_id=vmms-mobile`, optional `audience`) rotates under AC-7 to AC-10 and extends the session 7 days. An `audience` the client's row doesn't list gets `invalid_target`; one the user holds no role in gets 403 `NO_SYSTEM_ACCESS`. It is limited to 30 a minute per address.
- **AC-30**: `POST /auth/logout` with `{ refreshToken }` from `vmms-mobile` ends that session and answers 204, also for an unknown or already ended token.

*Rules shared by refresh, activity and logout*
- **AC-41**: Every refresh recomputes the user's roles for the audience. With no role left there (the user stays active but lost the system), it answers 403 `NO_SYSTEM_ACCESS`, rotates nothing and ends nothing; backend-vrms clears `vrms_rt` and sends the app to `<portal>/?error=NO_SYSTEM_ACCESS&system=VRMS`.
- **AC-42**: Logout and activity find the session from any refresh token row of the calling client, used or not, and never run reuse detection (only the `/auth/token` refresh grant does). Activity with a used token inside its grace window counts; past grace it answers 401 `SESSION_ENDED` and ends nothing. A confidential client may log out by `sid` with its assertion, but only a `sid` holding a refresh token of that client. When `/auth/logout` gets both a refresh token and the SSO cookie, the refresh token form wins.
- **AC-43**: Calls from a confidential client (with a valid assertion) may carry `X-WeLinc-User-Address`, the user's address as the system backend saw it; welinc-auth uses it for `last_seen_ip` and ignores the header on any call without a valid assertion. Assertion authenticated calls to `/auth/token` skip the per address limit and use a per client limit of 600 a minute (contract section 12 said 60).

*Seeing and ending sessions*
- **AC-31**: `GET /auth/me/sessions` lists the caller's live sessions, newest activity first: `sid`, kind, login client, device label, the systems it has received access tokens for, created, last active, and `current: true` for the caller's own `sid`. `DELETE /auth/me/sessions/:sid` ends one of the caller's own sessions (`USER_ENDED`). Ending the current one acts as logout. Another user's `sid` answers 404.
- **AC-32**: `GET /auth/users/:id/sessions` and `DELETE /auth/users/:id/sessions` work only for an admin who can see that user (spec 0011 scoping, the same check as `GET /auth/users/:id`). Delete ends every live session of the user (`ADMIN_ENDED`, with the admin as `endedById`) and writes one `UserChange` row (`SESSIONS_ENDED`, `newValue` holding the count) in the same transaction.
- **AC-33**: The device label is `<browser> on <OS>` from our own parser (Chrome, Edge, Safari, Firefox, Samsung Internet, Opera; Windows, macOS, iOS, Android, Linux, ChromeOS), "Unknown browser" or "Unknown OS" otherwise. For mobile it is the reported `deviceName`. The label is never used for a security decision.
- **AC-34**: The VRMS profile page shows a **Signed in devices** card: one row per session with the device label, the systems, last active (relative time), and a "This device" mark on the current one. Every other row has **End**, with a confirm step. Loading, empty (only this device) and error states are shown.
- **AC-35**: On the Users page, an admin's row action **Sessions** opens a dialog listing that user's sessions the same way, with **End all sessions** behind a confirm step. The action shows only when the caller has `users.manage` (the spec 0011 matrix key for adding, editing and deactivating users) and the user isn't the caller.

*The portal*
- **AC-36**: The portal holds no access token and stores nothing about the session in `localStorage`. It signs in through `POST /auth/login` with credentials. On `?request=<id>` it continues with `/auth/authorize/resume`; without one it goes to the `url` the login answer names. Opened directly with a valid SSO cookie (`GET /auth/sso` answers 200), it skips the form and goes to that `url`. With `reason=logout`, `reason=idle` or `reason=maxage` it always shows the form and never skips ahead through `/auth/sso`. It shows plain messages for `LOGIN_REQUEST_EXPIRED`, `LOGIN_STATE_INVALID`, `LOGIN_FAILED`, `NO_SYSTEM_ACCESS`, `reason=idle` and `reason=maxage` (the 12 hour limit, never the 30 minute idle wording), each with a button to sign in again. Its own `SessionMonitor` and `?token=` redirect are gone.

*Records, limits and setup*
- **AC-37**: The hourly job ends sessions past their cutoff, deletes ended sessions older than 90 days, deletes refresh token rows 1 day after their session ended, deletes expired login requests and codes, and clears grace ciphers older than the grace window. It runs from `@nestjs/schedule` on one replica at a time: the sweep runs inside one Prisma `$transaction` that first takes `pg_try_advisory_xact_lock` (and skips the run if another replica holds it), and deletes in batches of 1,000.
- **AC-38**: Limits hold as contract section 12 says: `/auth/session/activity` accepts and ignores more than 2 pings a minute per `sid`, `/auth/mobile/login` allows 5 a minute per address, the `vmms-mobile` refresh allows 30 a minute per address, `/auth/authorize` allows 30 a minute per address, and confidential clients get the AC-43 limits.
- **AC-39**: No log line, error body or `UserChange` row holds a refresh token, code, SSO handle, login request id or grace cipher. Session ends are logged with `sid`, user id, reason and client only.
- **AC-40**: Contract 0001 is updated in the same change (additive, version stays 1): web refresh isn't activity (section 6); `/auth/session` adds `user` (section 10); `/<sys>/session/status` joins the system session routes (section 7); `MAX_SESSIONS_PER_USER` and the `MAX_SESSIONS` reason (sections 6 and 15); `TOKEN_EXPIRED` and `CSRF_REJECTED` (section 11); the interim `/auth/login` and `/auth/sso` answers until S4 (section 10); "Built in" in Decisions at a glance and the Row column in section 10 move the web code exchange, `/auth/authorize`, `resume` and `/auth/sso` from S4 to S3; the automatic lock no longer ends live sessions (section 6); OTP reset and admin password set end every session (section 6); the GET navigation routes skip the CSRF guard (section 7); the per attempt login state cookie name (section 7); the `/auth/me/sessions` shape becomes `SessionView` (section 10); `X-WeLinc-User-Address`, the 600 a minute confidential client limit and the `/auth/authorize` limit (section 12); and `API_PUBLIC_URL` (section 15).

## Decision

**Chosen option**: Option 1: server side sessions in welinc-auth with chained refresh token rows, the grace pair encrypted under the old token, and the whole web transport (authorize, SSO cookie, VRMS's session routes) built in S3.

welinc-auth owns every session and is the only place that decides whether one is alive. Each system backend holds a refresh cookie and asks welinc-auth at most every 30 s whether the session still stands. S4 keeps only the launcher and Switch system.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` and `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-client-api/`, `.claude/skills/prisma-cli/`) · `vercel-react-best-practices` (`vercel-labs/agent-skills`, `.claude/skills/vercel-react-best-practices/`) for the boot, refresh and idle hooks · `shadcn` (`.claude/skills/shadcn/`) for the two dialogs and the devices card · `ask-sonner` (`.claude/skills/ask-sonner/`) for the "session ended" toasts

**Recommendations made in this spec** (yours to override):
- **The gateway CORS allow list now (AC-18).** Today nginx echoes any `Origin` with credentials. With refresh cookies, that would make the gateway's outer layer meaningless. So S3 fixes it in `welinc-auth/nginx.conf`, and S9 moves the file later. The runner up was to rely on the CSRF guard alone, which is one layer instead of two.
- **`/auth/sso` in S3, not S4 (AC-12).** The portal needs it to know a session exists when opened directly. Without it, every portal visit would make a new session. The launcher list it later returns stays S4. The runner up was to always show the form, at the cost of a session per visit.
- **Lazy cutoffs plus an hourly sweep (AC-3, AC-37).** Correctness never waits on the job, and the job only tidies. The runner up was a per minute job, which costs more and is still late by up to a minute.
- **A Postgres advisory lock for the job.** It keeps two replicas from sweeping at once with no new infrastructure. The runner up was a job table with a lease.
- **The grace cipher key is HKDF over the old token.** Only the holder of the old token can open it, and the database alone can't. The runner up was a server key in env, which adds a secret to rotate.
- **`SELECT ... FOR UPDATE` on the token row during rotation (AC-10).** It is the simplest race proof rotation in Postgres. The runner up was a conditional update on `usedAt IS NULL` plus a retry.

## Feature design

**Data model sketch** (welinc-auth, one migration; replaces today's unused `refresh_tokens`):

| Table | Field | Type | Null | Notes |
|---|---|---|---|---|
| `sessions` | `id` | uuid | no | PK, the `sid` |
| | `user_id` | uuid | no | FK `users.id`, cascade off (rows go with the 90 day purge) |
| | `kind` | enum `SessionKind` (`WEB`, `MOBILE`) | no | |
| | `login_client_id` | varchar(64) | no | FK `oauth_clients.id` (`portal` or `vmms-mobile`) |
| | `device_name` | varchar(100) | yes | mobile only, as reported |
| | `user_agent` | varchar(512) | yes | web only, truncated |
| | `created_ip` | varchar(45) | yes | from `X-Forwarded-For` through `TRUST_PROXY_HOPS` |
| | `last_seen_ip` | varchar(45) | yes | updated on refresh and activity |
| | `sso_handle_hash` | char(64) | yes | unique; web only; set at login |
| | `audiences` | `SystemType[]` | no | default empty; each system an access token was signed for, added at signing (shown as `systems`) |
| | `created_at` | timestamptz | no | |
| | `last_activity_at` | timestamptz | no | |
| | `idle_expires_at` | timestamptz | no | `last_activity_at` + idle limit |
| | `absolute_expires_at` | timestamptz | yes | web: `created_at` + 12 h; mobile: null |
| | `ended_at` | timestamptz | yes | |
| | `end_reason` | enum `SessionEndReason` | yes | set together with `ended_at` |
| | `ended_by_id` | uuid | yes | the admin, for `ADMIN_ENDED` |
| `refresh_tokens` | `id` | uuid | no | PK |
| | `session_id` | uuid | no | FK `sessions.id`, cascade delete |
| | `client_id` | varchar(64) | no | FK `oauth_clients.id` (whose token: `vrms`, `vmms-mobile`, ...) |
| | `token_hash` | char(64) | no | unique, SHA-256 hex |
| | `parent_id` | uuid | yes | FK self, unique (the token it replaced) |
| | `used_at` | timestamptz | yes | set when rotated |
| | `grace_cipher` | bytea | yes | the child token, AES-256-GCM, cleared after grace |
| | `grace_until` | timestamptz | yes | `used_at` + grace seconds |
| | `created_at` | timestamptz | no | |
| `login_requests` | `id_hash` | char(64) | no | PK |
| | `client_id` | varchar(64) | no | FK `oauth_clients.id` |
| | `redirect_uri`, `state`, `code_challenge` | text | no | as checked at authorize |
| | `expires_at` | timestamptz | no | 10 minutes |
| | `used_at` | timestamptz | yes | |
| `authorization_codes` | `code_hash` | char(64) | no | PK |
| | `client_id` | varchar(64) | no | FK `oauth_clients.id` |
| | `session_id` | uuid | no | FK `sessions.id`, cascade delete |
| | `redirect_uri`, `code_challenge` | text | no | |
| | `expires_at` | timestamptz | no | 60 s |
| | `used_at` | timestamptz | yes | |

- `SessionEndReason`: `LOGOUT`, `IDLE`, `MAX_AGE`, `USER_ENDED`, `ADMIN_ENDED`, `DEACTIVATED`, `DELETED`, `PASSWORD_CHANGED`, `REFRESH_REUSE`, `CODE_REUSE`, `MAX_SESSIONS`.
- `UserChangeAction` gains `SESSIONS_ENDED`.
- Indexes: `sessions (user_id, ended_at)`, `sessions (idle_expires_at) where ended_at is null`, `sessions (ended_at)`, `refresh_tokens (session_id, client_id) where used_at is null` (unique, the one live token rule), `login_requests (expires_at)`, `authorization_codes (expires_at)`.
- The `User.refreshTokens` relation becomes `User.sessions`.

**State transitions** (a session): `live` → `ended` (with one reason). There is no other state and no way back. "Expired" is not stored. A live row past `idle_expires_at` or `absolute_expires_at` is treated as ended and written as ended (`IDLE` or `MAX_AGE`) by the first call that sees it.

A refresh token: `unused` → `used, in grace` (10 s, `grace_cipher` set) → `used` (cipher cleared). Presenting it while `used` ends its session.

**Rotation, step by step** (`refresh_token` grant, one transaction):
1. Hash the presented token and `SELECT ... FOR UPDATE` its row with its session. No row: `invalid_grant`.
2. If the session has ended, or is past a cutoff (end it now): `invalid_grant`.
3. If the row's `client_id` isn't the caller (assertion client, or `vmms-mobile`): `invalid_grant`, ending nothing.
4. If the row is unused: make a new token, insert its row (`parent_id` = this row), set `used_at` and `grace_until`, and store `grace_cipher` = a random 12 byte nonce followed by AES-256-GCM(new token) with key = HKDF-SHA256(presented token, salt = row id, info = `welinc-refresh-grace`). For mobile, extend `idle_expires_at`. Update `last_seen_ip` (AC-43).
5. If the row is used and `now <= grace_until`: decrypt `grace_cipher` with the presented token and return that token.
6. If the row is used and past grace: end the session (`REFRESH_REUSE`) and answer `invalid_grant`.
7. Recompute the user's roles for the audience (the client's system, or the mobile `audience`). None left: answer 403 `NO_SYSTEM_ACCESS` and roll back, so nothing rotates (AC-41). Otherwise sign a fresh access token and add the audience to `sessions.audiences`.

**Code exchange** (`authorization_code` grant, one transaction): `SELECT ... FOR UPDATE` the code row; used: end the session (`CODE_REUSE`); expired, or client, redirect address or PKCE mismatch: `invalid_grant`; the session ended: `invalid_grant`. Otherwise mark the code used, mark any unused refresh token of this (session, client) used with no grace (AC-7), insert the new token, count the exchange as activity, and sign the access token as in step 7.

**API surface**:

welinc-auth (through the gateway, under `/auth`):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/login` | POST | `{ email, password, recaptchaToken }` | sets `welinc_sso`; `{ user: { id, name, email }, system, url }` | none; CSRF guard (portal origin) | 401 bad credentials, 423 locked, 403 `NO_SYSTEM_ACCESS`, 429 |
| `/auth/sso` | GET | `welinc_sso` cookie | `{ user, system, url }` | SSO cookie | 401 `SESSION_ENDED` |
| `/auth/logout` | POST | SSO cookie; or JSON `{ refreshToken }` with a client assertion (form fields) or `clientId: vmms-mobile` | 204, clears `welinc_sso` when cookie based | as listed; CSRF guard on the cookie form | none (always 204) |
| `/auth/authorize` | GET | `client_id`, `redirect_uri`, `state`, `code_challenge`, `code_challenge_method=S256` | 302 to the callback with `code` and `state`, or `error=access_denied`, or to `<portal>/login?request=` | SSO cookie if present | error page (400) for a bad client or address |
| `/auth/authorize/resume` | GET | `request` | 302 as above | SSO cookie | 302 `<portal>/?error=LOGIN_REQUEST_EXPIRED` |
| `/auth/token` | POST | `grant_type=authorization_code` (`code`, `redirect_uri`, `code_verifier`) or `refresh_token` (`refresh_token`, `audience?`) | contract section 5 user grant answer, plus `session_absolute_expires_at` for a web session (login + `WEB_SESSION_MAX_HOURS`; left out for mobile) | client assertion, or `client_id=vmms-mobile` for refresh | `invalid_grant`, `invalid_client`, `invalid_target`, 403 `NO_SYSTEM_ACCESS`, 429 |
| `/auth/mobile/login` | POST | `{ email, password, clientId, deviceName }` | `{ accessToken, refreshToken, expiresIn, sid, sessionExpiresAt, user }` | none | 401, 423, 403 `NO_SYSTEM_ACCESS`, 429 |
| `/auth/session` | GET | bearer user token | `{ active: true, sid, expiresAt, user: { id, name, email } }` | user token | 401 `SESSION_ENDED`, `ACCOUNT_INACTIVE`, `TOKEN_EXPIRED` (a locked account's live session still answers 200, AC-4) |
| `/auth/session/activity` | POST | form: client assertion plus `refresh_token`; or the SSO cookie | 204 | client assertion or SSO cookie (CSRF guard) | 401 `SESSION_ENDED` |
| `/auth/me/sessions` | GET | bearer | `{ sessions: SessionView[] }` | user token | 401 |
| `/auth/me/sessions/:sid` | DELETE | path `sid` | 204 | user token | 404 not yours |
| `/auth/users/:id/sessions` | GET | path `id` | `{ sessions: SessionView[] }` | admin of a system the user holds (spec 0011) | 403, 404 |
| `/auth/users/:id/sessions` | DELETE | path `id` | `{ ended: number }` | as above, and not the caller | 403, 404 |
| `/auth/.well-known/oauth-authorization-server` | GET | none | adds `authorization_endpoint`, grants `authorization_code` and `refresh_token`, `code_challenge_methods_supported: ["S256"]` | none | none |

```ts
type SessionView = {
  sid: string;
  kind: 'web' | 'mobile';
  device: string;          // AC-33 label
  client: string;          // the login client: 'portal' or 'vmms-mobile'
  systems: ('VRMS' | 'VMMS' | 'BMS')[]; // sessions.audiences
  createdAt: string;
  lastActiveAt: string;
  current: boolean;        // only on /auth/me/sessions
};
```

backend-vrms (under `/vrms/session`, contract section 7):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `start` | GET | `return` | sets `vrms_login_<state prefix>` (state, PKCE verifier, return); 302 to `/auth/authorize` | none | none |
| `callback` | GET | `code` and `state`, or `error` and `state` | clears the matching `vrms_login_<state prefix>` before the exchange, then sets `vrms_rt`; 302 to `WEB_APP_URL` + return | `vrms_login` cookie | 302 `<portal>/?error=NO_SYSTEM_ACCESS&system=VRMS`, `LOGIN_STATE_INVALID`, `LOGIN_FAILED` |
| `refresh` | POST | `vrms_rt` | `{ accessToken, expiresIn, sessionExpiresAt, sessionAbsoluteExpiresAt, user: { id, name, email, roles } }`; rotates `vrms_rt` | cookie, CSRF guard | 401 `SESSION_ENDED` (clears the cookie), 503 `AUTH_UNAVAILABLE` |
| `activity` | POST | `vrms_rt` | 204 | cookie, CSRF guard | 401 `SESSION_ENDED` |
| `logout` | POST | `vrms_rt` | 204, clears `vrms_rt` | cookie, CSRF guard | none |
| `status` | GET | bearer | `{ sessionExpiresAt }` | user token | 401, 503 |

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| Login | `system`, `url` | spec 0002's login system pick; `oauth_clients.web_address` of that system's client |
| Login, mobile login | `created_ip` | `X-Forwarded-For` through `TRUST_PROXY_HOPS` (spec 0002) |
| Refresh, activity, logout from a system backend | `last_seen_ip` | `X-WeLinc-User-Address`, set by backend-vrms from its own `X-Forwarded-For` through `TRUST_PROXY_HOPS`, trusted only with a valid assertion (AC-43); mobile refresh uses the request address |
| Login | the `welinc_sso` value | a new random 256 bit handle, base64url; only its SHA-256 is stored |
| Login | `welinc_sso` max age | `absolute_expires_at` minus now |
| VRMS start and callback | `redirect_uri` | `API_PUBLIC_URL` + `/vrms/session/callback`, which must equal the registry row character for character |
| VRMS start | `client_id` | `AUTH_CLIENT_ID` (spec 0002) |
| Login | `user_agent` | the request's `User-Agent`, truncated to 512 |
| Mobile login | `device_name` | the `deviceName` input, trimmed, at most 100 |
| Any session write | `idle_expires_at` | `last_activity_at` + `WEB_SESSION_IDLE_MINUTES` or `MOBILE_SESSION_IDLE_DAYS` |
| Web login | `absolute_expires_at` | `created_at` + `WEB_SESSION_MAX_HOURS` |
| Token answers, `/auth/session` | `sessionExpiresAt`, `expiresAt` | the earlier of `idle_expires_at` and `absolute_expires_at` |
| Code exchange, refresh | access token `aud` | the client's `system`; for `vmms-mobile`, the `audience` input or its default (`VMMS`) |
| Code exchange, refresh | `user` in the answer | `users` (name, email) and `user_roles` for that audience |
| Code exchange, refresh (web) | `session_absolute_expires_at` | `sessions.absolute_expires_at` |
| VRMS callback, refresh | `vrms_rt` max age | `session_absolute_expires_at` from the `/auth/token` answer minus now; `sessionExpiresAt` is the idle bound one and is not used for the cookie |
| VRMS start | `state`, PKCE verifier | 32 random bytes each, base64url; the challenge is SHA-256 of the verifier |
| VRMS start | return path | the `return` input, resolved against `WEB_APP_URL`, kept only if same origin |
| VRMS session check | caller name | `/auth/session` `user.name` (cached 30 s by `sid`) |
| Idle warning (the signing out soon banner since spec 0016) | the server cutoff | `GET /vrms/session/status`; before that, `sessionExpiresAt` from the last refresh |
| Idle warning, portal reason | whether the cutoff is the 12 hour end | `sessionAbsoluteExpiresAt` from the last refresh (`session_absolute_expires_at` of the `/auth/token` answer), within 1 s of the cutoff |
| Sessions list | `device` | AC-33 parser over `user_agent`, or `device_name` |
| Sessions list | `systems` | `sessions.audiences` |
| Sessions list | `client` | `sessions.login_client_id` |
| Sessions list | `current` | the caller token's `sid` |
| Admin end | the `UserChange` actor | the caller token's `sub` and `email` |
| Cap | which session to end | the caller's live session with the oldest `last_activity_at` |
| Logout from VRMS | the session to end | the `vrms_rt` cookie, passed to `/auth/logout` with VRMS's client assertion |

**Key invariants**:
- welinc-auth is the only writer of `sessions`. An ended session never becomes live again.
- At most one unused refresh token per (session, client), enforced by the partial unique index.
- At most 10 live sessions per user, enforced in the login transaction.
- No token, code, handle or request id is stored in plain text, logged, or put in a URL, apart from the one time `code` on the callback redirect and the login `request` id (both one use and short lived, as OAuth requires).
- Web refresh never moves `last_activity_at`. Mobile refresh does.
- Every system decides "alive" only through `/auth/session` or a refresh. No system reads these tables.

**Security model**:
- Users see and end only their own sessions (`sid` belongs to `sub`, else 404).
- Admins list and end sessions only of users they can already see under spec 0011. They can't end their own sessions through the admin route (they use logout or the devices card). The action is recorded in `user_changes`.
- `/auth/session/activity` and the VRMS `logout` prove the client with its assertion, so a stolen refresh token alone can't ping or log out through another client.
- Cookies are as contract section 7 sets them: `HttpOnly`, `SameSite=Lax`, host only, `Secure` and the `__Secure-` prefix when hosted.
- CSRF: the guard in AC-17 plus the gateway allow list in AC-18.
- Session fixation: the SSO handle and the session id are always new at login, never taken from the request.
- Accepted risk, cookie tossing: when hosted, a sibling subdomain could set a cookie with the same name for the parent domain, which the `__Secure-` prefix doesn't stop (only `__Host-` with `Path=/` would). Every subdomain of `<domain>` is ours and serves only static apps or the gateway, so this is written down and accepted rather than giving up the per system cookie paths.
- The automatic lock blocks logins only (AC-4), so a guessing attack costs the victim new logins for the lock period, never their live work.
- PII: IP addresses and user agents are personal data under the Philippine Data Privacy Act. They are shown only to the user and their admins, and purged with the session after 90 days.

**Configuration required**:

welinc-auth (`.env.example` only):
- `ACCESS_TOKEN_MINUTES` (15), `WEB_SESSION_IDLE_MINUTES` (30), `WEB_SESSION_MAX_HOURS` (12), `MOBILE_SESSION_IDLE_DAYS` (7), `REFRESH_REUSE_GRACE_SECONDS` (10), `MAX_SESSIONS_PER_USER` (10), `SESSION_RETENTION_DAYS` (90). Remove `JWT_ACCESS_EXPIRY` and `JWT_REFRESH_EXPIRY` if any are still left.
- `SSO_COOKIE_SECURE` (false locally, true hosted). `PORTAL_URL` (kept) is the portal origin for the CSRF guard.

backend-vrms:
- `WEB_APP_URL` (`http://localhost:8001`) and `PORTAL_URL` (`http://localhost:8000`).
- `SESSION_COOKIE_SECURE` (false locally, true hosted).
- `AUTH_PUBLIC_URL` (`http://localhost:3000/auth`): where the browser is sent for `/auth/authorize`. It is the issuer locally, and differs from `AUTH_INTERNAL_URL`.
- `API_PUBLIC_URL` (`http://localhost:3000`): the gateway address the browser sees, used to build the callback address. `AUTH_CLIENT_ID` (`vrms`) is kept from spec 0002.

Gateway (`welinc-auth/nginx.conf` at the time; since S9 it is `infra/gateway/` in the workspace, spec 0008): an exact origin allow list built from a `map` over `$http_origin` (portal, VRMS web, and the VMMS and BMS web addresses from contract section 1 for later).

web-vrms and portal: no new variables (`VITE_API_BASE_URL`, `VITE_PORTAL_URL` only).

**Critical test scenarios**:
- Happy path, web: open a VRMS deep link with no cookie, go through the portal login, come back to the same path with an access token in memory and no token in storage or any URL. Verifies AC-11, AC-13 to AC-16, AC-19, AC-20.
- Two tabs refreshing at the same moment both keep working, and the session stays alive. Verifies AC-8, AC-10, AC-21.
- A stolen token replayed after the owner refreshed ends the session for both. Verifies AC-9.
- An idle tab that keeps refreshing in the background is still signed out at 30 minutes; working in a second tab keeps the first one alive. Verifies AC-2, AC-3, AC-22, AC-23.
- Logout in VRMS: the other VRMS tab leaves at once, and a direct `/auth/session` call with the old token answers 401 within 30 s of cache. Verifies AC-24, AC-26.
- Deactivate a user while they are signed in: their next request after the cache window gets 401. Verifies AC-4, AC-26.
- An 11th login ends the oldest session. Verifies AC-6.
- A request from another origin to `/vrms/session/refresh` gets 403 `CSRF_REJECTED`, and the gateway sends no CORS headers for it. Verifies AC-17, AC-18.
- A code used twice ends the session. Verifies AC-15.
- welinc-auth stopped for 20 s: VRMS keeps working on its current token, shows "Reconnecting", then recovers. Verifies AC-25.
- A mechanic calling `DELETE /auth/users/:id/sessions` gets 403; an admin of another system who can't see the user gets 404. Verifies AC-32.
- Mobile login, refresh with `audience=VRMS` for a user without a VRMS role gets 403; a 7 day idle mobile session refuses refresh. Verifies AC-28, AC-29.

## Build plan

Tracer Bullet, with the hard switch at the end: the four repo branches (welinc-auth, backend-vrms, web-vrms, portal) and the workspace compose change merge together, as in spec 0002.

1. **The web thread, end to end** (the tracer bullet: log in, land on a deep link, refresh, call an API)
   - welinc-auth: one migration for the whole data model; the session service (create, cap, lazy cutoffs, end with reason); `/auth/login` with the SSO cookie and the interim answer; `/auth/sso`; `/auth/authorize` and `resume` with the error page; the `authorization_code` and `refresh_token` grants with rotation, grace and reuse; `sid` in tokens; `/auth/session` with `user`; metadata update; `cookie-parser`; the CSRF guard. Roles recomputed on every refresh; `X-WeLinc-User-Address` and the confidential client limits. Satisfies **AC-1**, **AC-5**, **AC-7** to **AC-15**, **AC-17**, **AC-27**, **AC-41**, **AC-43**.
   - backend-vrms: `cookie-parser`; the CSRF guard; `start`, `callback` (state check before exchange, per attempt state cookie), `refresh` with the error mapping and `status`; the account check moved from `/auth/me` to `/auth/session`, cached by `sid` with ended answers and single flight; forwarding the user address. Satisfies **AC-16**, **AC-16a**, **AC-26**, **AC-43**.
   - web-vrms: the in memory token store, the boot sequence and loop guard, proactive refresh under the Web Lock with one retry, the `TOKEN_EXPIRED` handling; remove `/login`, `LoginPage`, `SsoHandoff`, `processToken` and every `localStorage` token read. Satisfies **AC-19** to **AC-21**.
   - portal: login with credentials, `?request=` and resume, the direct open check through `/auth/sso`, the error messages; remove the token storage, `?token=` and its `SessionMonitor`. Satisfies **AC-36**.
   - Gateway CORS allow list; compose and `.env.example` in all repos; contract 0001 amendments. Satisfies **AC-18**, **AC-40**.
2. **Session endings and idle**
   - welinc-auth: `/auth/logout` (cookie and refresh token forms); `/auth/session/activity` with its per `sid` limit; ending on deactivate, delete, password change, OTP reset and admin password set (the automatic lock ends nothing); logout and activity resolving any token row, logout by `sid`; the hourly job with the transaction advisory lock; the log rules. Satisfies **AC-2** to **AC-4**, **AC-6**, **AC-37** to **AC-39**, **AC-42**.
   - backend-vrms: `activity` and `logout`, with the `sid` fallback. Satisfies **AC-16**, **AC-24**, **AC-42**.
   - web-vrms: the activity pinger on real input, the idle warning dialog with status checks, logout with the BroadcastChannel, the "Reconnecting" banner and retry schedule. Satisfies **AC-22** to **AC-25**.
3. **Mobile routes** (welinc-auth only, e2e tested): `/auth/mobile/login`, the `vmms-mobile` refresh with `audience`, logout by refresh token, rolling idle, and its limits. Satisfies **AC-28** to **AC-30**, **AC-38**.
4. **Seeing and ending sessions**
   - welinc-auth: `/auth/me/sessions` (list, end one), `/auth/users/:id/sessions` (list, end all, `UserChange`), the device label parser. Satisfies **AC-31** to **AC-33**.
   - web-vrms: the **Signed in devices** card on the profile page; the **Sessions** row action and dialog on the Users page. Satisfies **AC-34**, **AC-35**.

## Migration plan

**Strategy**: big bang (the hard switch the contract chose; VRMS and the portal are the only real users, and nothing outside them holds a session).

**Phases**:
1. Build all four slices on their branches, with tests green in every repo.
2. Merge the four repo PRs and the workspace PR together. Run the migration in welinc-auth, `npm install` in each container (`cookie-parser`), then `prisma generate` and a restart in welinc-auth.
3. Everyone logs in once more. Old `localStorage` tokens in browsers are ignored and cleared on the first load.

**Rollback**: revert the five merges together. The migration only adds tables, an enum value and swaps the unused `refresh_tokens`, so the down step drops the new tables and recreates the old empty one. Everyone logs in again.

**Risks**: cookies not sent because of a CORS or `SameSite` mistake (caught by the happy path e2e on the local stack); a redirect loop on boot (the `sessionStorage` guard); container `node_modules` missing `cookie-parser` (install inside the containers).

## Consequences

**Positive**:
- Tokens leave URLs and `localStorage`, so a script injected into a VRMS page can no longer take a session away with it.
- Logout, deactivation and an admin "end all" reach every system within 30 s, and a stolen refresh token dies the moment either side uses it twice.
- Idle and the 12 hour limit are enforced on the server, the same for every system, instead of a timer each app runs on its own.
- VMMS gets finished, tested mobile routes before its move, and VRMS's session routes become the reference the other groups copy.
- The capstone papers can name standard pieces: the OAuth code flow with PKCE, refresh token rotation with reuse detection, and server side session revocation.

**Negative / tradeoffs**:
- This is the largest piece of security code in the suite. A mistake in rotation or the CSRF guard affects every system, which is why the row runs at GA (fresh review, then document).
- One more call per 30 s per session from each backend to welinc-auth. If welinc-auth is down, new requests fail after 30 s (fail closed).
- The hard switch logs everyone out once, and the four PRs must merge together.
- Every web app must run the boot sequence, the Web Lock and the activity pinger. That is real work for VMMS and BMS in S11, softened by VRMS's code as the reference.
- The access token lives in memory, so a full reload always costs one refresh round trip before the first API call.
- Locally all `localhost` ports share cookies, so one browser profile can't hold two different users at once. Use a second browser profile for that.
- IP addresses and user agents are now stored, so they fall under the Data Privacy Act and must stay behind the purge.
- The automatic lock no longer signs a person out, so someone who already holds a stolen live session keeps it through a lock. Ending it takes deactivation or "End all sessions" by an admin.
- System backends must forward the user's address, a header every group's backend has to set in S11.

**Neutral**:
- S4 shrinks to the launcher list in `/auth/sso`, the launcher page, Switch system in each app, and the portal's design pass.
- `account-check.ts` keeps its cache and fail closed rules and only changes what it asks.
- The S2 interim token (no `sid`) stops working the moment this lands.

## Follow-up

- [ ] Update the S4 scope row: it no longer builds the code exchange, only the launcher, Switch system, and the launcher list in `/auth/sso`. (`/scope` or `/architect` S4 picks this up.)
- [ ] S11 guide: copy VRMS's `src/session/` module (session routes, CSRF guard, cookie names) and web-vrms's boot, refresh and activity hooks; list the cookie and CORS entries each group adds.
- [ ] S7 (activity) reads `sessions` and the end reasons; it should log logins, refreshes and ends as events, since sessions are purged after 90 days.
- [ ] Spec 0008 (hosting): set `SSO_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`, `AUTH_PUBLIC_URL` and the gateway origin allow list per environment, and keep welinc-auth at a minimum of 1 replica.
- [ ] Tell the VMMS and BMS groups once this lands: `/auth/login` no longer returns a token, and the mobile routes are ready for S11.
- [ ] `/sync` after the build: the session module in backend-vrms's and welinc-auth's `AGENTS.md`, and the token handling note in web-vrms's `AGENTS.md` (no more `localStorage`).
- [ ] Later hardening (not scheduled): bind refresh tokens to the device (DPoP) for mobile, and app attestation on `/auth/mobile/login` (already in 0001's follow-up).
