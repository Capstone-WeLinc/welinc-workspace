# 0001. Shared services contract for the WeLinc suite

**Date**: 2026-11-08
**Status**: Accepted
**Scope row**: [S1. Shared services contract](../../../scope/_root/shared-services.md#s1-shared-services-contract--planned--needs-a-decision)
**Contract version**: 1

## Summary

This is the one agreement every WeLinc system builds against for login, tokens, roles, user data, the gateway and ports. welinc-auth becomes a small OAuth style login server (OAuth is the industry standard way for apps to get tokens from a central login service). It signs tokens with a private key only it holds, gives each system its own token, and lets each system's backend swap a one time login code for a session kept in a cookie page scripts can't read. VMMS and BMS can now plan their move without guessing, and VRMS and the portal switch over first to prove each piece (the tracer bullet). Each row S2 to S12 designs its own insides later, but none of them may change what this page promises without updating it.

## Rationale

Reasoning, options and the current state inventory: see [rationale.md](rationale.md).

## Decision

**Chosen option**: Option 1: welinc-auth as a small authorization server (the service that logs people in and hands out tokens) with a token per system, ES256 published keys, a code exchange on each system's backend, and a cursor change feed for user data.

welinc-auth stays the only owner of accounts and the only service that can sign a token. Every other service checks tokens with welinc-auth's public keys, learns about users through an API, and never reads the auth database.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` and `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-client-api/`, `.claude/skills/prisma-cli/`) · `docker-patterns` (ask first, for the gateway move in S9; `.claude/skills/docker-patterns/`)

### Decisions at a glance

| Area | Decision | Built in |
|---|---|---|
| Token audience | One token per system: `aud` is that system, `roles` holds only that system's roles | S2, S5 |
| Signing | ES256 (elliptic curve), keys published at a JWKS address (a public list of the keys that verify tokens) | S2 |
| Web login | Code exchange on each system's backend (OAuth authorization code with PKCE), refresh token in an HttpOnly cookie on the shared domain, access token in memory only | S3 (spec 0003; S4 adds the launcher) |
| Web session | 30 minutes without user input in any app, or 12 hours since login, whichever comes first; idle is tracked on the server through a light activity ping | S3 |
| Mobile login | Native login screen in the app, calling its own welinc-auth route (`/auth/mobile/login`) as a first party mobile client | S3 |
| Mobile session | 7 days rolling (each refresh extends it) | S3 |
| Revocation | Each backend checks the session at most 30 s stale; deactivation and logout also revoke refresh tokens, so a backend that skipped the check still loses access when the 15 minute access token runs out. The automatic lock blocks new logins only (spec 0003) | S3 |
| Service identity | Signed client assertion (`private_key_jwt`): each backend proves itself with its own ES256 key | S2 |
| User directory | Batch lookup by id plus a cursor change feed; a thin webhook nudge is reserved for later | S6 |
| Gateway paths | Each service serves under its own prefix; the gateway forwards without rewriting | S9 |
| Gateway config | Workspace repo `infra/gateway/`, for local and hosted (as spec 0008 planned), out of `welinc-auth` | S9 |
| Ports | One block per system (below) | S9 |
| Old login | Hard switch: VRMS and the portal move straight to the new flow; `JWT_SECRET` and `?token=` are removed, no dual run | S2, S3 |
| Move order | VRMS and the portal first (tracer bullet), then BMS, then VMMS | S11 |

## Contract

Everything in this section is the promise. Paths are as seen through the gateway. `<api>` is the gateway address: `http://localhost:3000` locally, `https://api.<domain>` hosted.

### 1. Addresses and domain

| Thing | Local | Hosted (production) | Hosted (staging) |
|---|---|---|---|
| Gateway (the one API address) | `http://localhost:3000` | `https://api.<domain>` | `https://staging-api.<domain>` |
| Portal | `http://localhost:8000` | `https://portal.<domain>` | `https://staging-portal.<domain>` |
| VRMS web | `http://localhost:8001` | `https://vrms.<domain>` | `https://staging-vrms.<domain>` |
| VMMS web | `http://localhost:8002` | `https://vmms.<domain>` | `https://staging-vmms.<domain>` |
| BMS web | `http://localhost:8003` | `https://bms.<domain>` | `https://staging-bms.<domain>` |
| Token issuer (`iss`) | `http://localhost:3000/auth` | `https://api.<domain>/auth` | `https://staging-api.<domain>/auth` |

- `<domain>` is one registered domain, working name `welinc.tech` (see Follow-up). Every web app and the gateway share it, so the browser treats them as one site and the refresh cookie counts as first party. Locally, `localhost` on any port is also one site.
- All services sit behind the gateway. Only the gateway has a public address; every other container has internal ingress (reachable only inside the Azure environment), as spec 0008 already does for VRMS.

### 2. Port map

| Block | Service | Port |
|---|---|---|
| Shared | Gateway | 3000 |
| Shared | `welinc-auth` | 3001 |
| Shared | Portal | 8000 |
| VRMS | `welinc-backend-vrms` | 3002 |
| VRMS | `welinc-web-vrms` | 8001 |
| VMMS | `welinc-backend-vmms` | 3010 |
| VMMS | `welinc-backend-vmms-analytics-ai` | 3011 |
| VMMS | `welinc-web-vmms` | 8002 |
| BMS | `bms-gateway` | 3020 |
| BMS | `bms-booking-service` | 3021 |
| BMS | `bms-dispatch-service` | 3022 |
| BMS | `bms-completion-service` | 3023 |
| BMS | `bms-analytics-projection` | 3024 |
| BMS | `welinc-backend-bms-analytics-ai` | 3025 |
| BMS | `welinc-web-bms` | 8003 |

- Free in each block: VRMS 3003 to 3009, VMMS 3012 to 3019, BMS 3026 to 3029. A new service takes the next free port in its block and adds it to the README repos table.
- Databases keep their own container ports and are never reached through the gateway.

### 3. Gateway routes

| Path prefix | Goes to | Body limit | Read timeout |
|---|---|---|---|
| `/auth`, `/uploads` | `welinc-auth` 3001 | 5 MB | 30 s |
| `/vrms`, `/repairs` | `welinc-backend-vrms` 3002 | 26 MB | 120 s |
| `/vmms/analytics` | `welinc-backend-vmms-analytics-ai` 3011 | 1 MB | 120 s |
| `/vmms` | `welinc-backend-vmms` 3010 | 10 MB | 60 s |
| `/bms` | `bms-gateway` 3020 (which fans out to the BMS services and analytics itself) | 10 MB | 60 s |

- **No rewriting.** Each service serves its own prefix (VMMS sets a global `vmms` prefix and serves analytics under `vmms/analytics`; `bms-gateway` swaps its `/api` strip for `/bms`). The same path works directly on the service port and through the gateway.
- **Longest prefix wins** (`/vmms/analytics` before `/vmms`).
- **Headers the gateway sets:** `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Request-Id` (kept if the caller sent one). Services trust one proxy hop and log `X-Request-Id` on every line.
- **CORS:** the gateway answers preflight (the browser's "may I call this?" check) only for the web origins of its environment (section 1), with credentials allowed. Locally it also allows the `localhost` ports in section 2. No `*`.
- **Health:** every upstream answers `GET <prefix>/health` with 200 and a database check, for the spec 0008 smoke test.
- **Config home:** `infra/gateway/` in the workspace repo holds the nginx template (upstreams read from environment values, as spec 0008 describes) and the local config that `docker-compose.shared.yml` mounts. `welinc-auth/nginx.conf` is removed.
- A body limit or timeout change for one route is a one line PR to `infra/gateway/` that the owning group opens; it is not a contract change.

### 4. Clients (who may ask welinc-auth for tokens)

welinc-auth keeps a registry of clients, one per environment, set by its seed.

| Client id | Kind | System | Can use | User token audiences | Service token audiences and scopes | Redirect address |
|---|---|---|---|---|---|---|
| `portal` | first party web, no backend | none | SSO cookie routes only (section 7) | none | none | none |
| `vrms` | confidential backend | `VRMS` | authorization code, refresh, client credentials | `VRMS` | `AUTH` (`directory.read`, `directory.contact`); other systems per feature 56 | `<api>/vrms/session/callback` |
| `vmms` | confidential backend | `VMMS` | authorization code, refresh, client credentials | `VMMS` | `AUTH` (`directory.read`, `directory.contact`); other systems per feature 56 | `<api>/vmms/session/callback` |
| `bms` | confidential backend (`bms-gateway`) | `BMS` | authorization code, refresh, client credentials | `BMS` | `AUTH` (`directory.read`, `directory.contact`); other systems per feature 56 | `<api>/bms/session/callback` |
| `vmms-mobile` | first party native, public (holds no secret) | `VMMS` | mobile login, refresh | `VMMS` (default), later `VRMS` (scope feature 48) | none | none |
| `vmms-analytics` | service | `VMMS` | client credentials | none | `AUTH` (`directory.read`) | none |
| `bms-analytics` | service | `BMS` | client credentials | none | `AUTH` (`directory.read`) | none |

- **System** is the system a client acts for. It scopes the directory (section 9) and is the default audience of its user tokens.
- welinc-auth refuses any audience or scope a client's row doesn't list (`invalid_target` or `invalid_scope`, section 11).
- A confidential client registers one or two ES256 public keys as inline JWKs (two during a key change), each with its own `kid`. The keys come from the seed per environment; changing one means running the seed again. welinc-auth never holds a client's private key.
- Redirect addresses match exactly, character for character. No wildcards.
- Each client's registry row also holds its system's web address (section 1), where users land after login.
- Calls inside one system (the BMS services calling each other, for example) are that group's own business. A client identity is needed only for calls to welinc-auth or to another system.

### 5. Tokens

All signed tokens use ES256 with a `kid` header (the id of the key that signed it). Access tokens (user and service) carry `typ: at+jwt`; client assertions carry `typ: JWT`.

**User access token** (15 minutes):

| Claim | Value | Source |
|---|---|---|
| `iss` | issuer from section 1 | `AUTH_ISSUER` |
| `sub` | the user's id (uuid), the one user key across the suite | `users.id` |
| `aud` | `VRMS`, `VMMS` or `BMS` | the client that exchanged the code, or `audience` on a mobile refresh |
| `client_id` | e.g. `vrms`, `vmms-mobile` | the client |
| `sid` | session id (uuid) | the session created at login |
| `token_use` | `user` | fixed |
| `email` | the user's email | `users.email` |
| `roles` | `[{ "role": "ADMIN", "system": "VRMS" }]`, only roles for `aud` | user role assignments filtered by `aud` |
| `iat`, `exp`, `jti` | issued at, expiry, unique id | at signing |

- `roles` keeps today's shape on purpose, so code that reads it changes nothing but the filter.
- A token whose `aud` isn't the receiving system is rejected (401), even if the signature is good.
- No names, phone numbers or pictures in tokens. Systems get those from the directory (section 9).

**Service access token** (5 minutes, from client credentials):

| Claim | Value |
|---|---|
| `iss`, `iat`, `exp`, `jti` | as above |
| `sub` | `client:<client id>`, e.g. `client:vmms-analytics` |
| `aud` | the system or service being called, e.g. `AUTH` for the directory, `VMMS` for the VMMS backend |
| `client_id` | the caller |
| `token_use` | `service` |
| `scope` | space separated, e.g. `directory.read` |

- A service token has no `roles` and no `sid`. Routes meant for people reject it, and routes meant for services reject user tokens (403).
- welinc-auth defines the `directory.read` scope. Each system defines and documents the scopes for its own service routes (VRMS feature 56 lists the ones between systems).

**Client assertion** (what a confidential backend signs to prove itself, `private_key_jwt`):

| Claim | Value |
|---|---|
| `iss`, `sub` | the client id |
| `aud` | `<issuer>/token` |
| `exp` | at most 60 s after `iat` |
| `jti` | unique; welinc-auth refuses a `jti` it has seen before its expiry |
| header `kid` | required: which of the client's registered keys signed it |

Sent as `client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer` and `client_assertion=<jwt>`. Seen `jti` values are kept in the auth database until they expire, so the replay check holds across replicas.

**Opaque values** (random 256 bit strings, stored hashed, never decoded by anyone):

| Value | Lifetime | Rule |
|---|---|---|
| Login request (`request`) | 10 minutes | a server row holding the checked authorize parameters (client, redirect address, `state`, PKCE challenge); used once; `resume` continues it only for a browser with a valid SSO cookie |
| Login code | 60 s | used once; bound to client, redirect address, PKCE challenge and the `sid` it was issued for; a second use ends that session |
| Refresh token | the session's lifetime | rotates on every use. Within 10 s of a rotation, presenting the previous token again returns the same new pair (two tabs, or a retry after a lost answer). After that window, reusing an old token ends the whole session. |
| SSO handle (portal cookie) | the web session's lifetime | belongs to one `sid`; ending the `sid` kills it even while the cookie is still in the browser |
| Reauth token (S8) | 5 minutes | used once, only for the deletion request |

**Keys:** `GET /auth/.well-known/jwks.json` lists the public keys (`Cache-Control: max-age=300`). Each private key in `AUTH_SIGNING_KEYS` carries a `status`: `current` (signs everything, exactly one), `next` (published, signs nothing yet) or `retired` (published, signs nothing, removed later). A rotation: add the new key as `next` and wait at least one hour; swap it to `current` and the old one to `retired`; remove the retired key once 30 minutes have passed after its last token expired. So a rotation needs no downtime. Verifiers cache the list and fetch it again when they meet an unknown `kid` (at most once a minute). In Node, use `jose` (its remote key set, wrapped to keep the last good set during an outage) for checking tokens and signing client assertions; VRMS's `src/auth/verify/` folder is the reference to copy (spec 0002).

**`POST /auth/token`** (form encoded, per RFC 6749):

| Grant | Request fields | Client proof |
|---|---|---|
| `authorization_code` | `code`, `redirect_uri`, `code_verifier` | client assertion |
| `refresh_token` | `refresh_token`, optional `audience` (mobile only) | client assertion, or `client_id=vmms-mobile` |
| `client_credentials` | `audience`, `scope` (space separated, required) | client assertion |

User grants answer:

```json
{
  "access_token": "…", "token_type": "Bearer", "expires_in": 900,
  "refresh_token": "…", "sid": "uuid",
  "session_expires_at": "ISO 8601, the earlier of the idle and absolute cutoffs",
  "session_absolute_expires_at": "ISO 8601, web sessions only: login + 12 hours, the refresh cookie's max age (spec 0003)",
  "user": { "id": "uuid", "name": "…", "email": "…", "roles": [{ "role": "ADMIN", "system": "VRMS" }] }
}
```

The client credentials grant answers `{ access_token, token_type, expires_in, scope }`, with no refresh token. The system backend's own routes (section 7) take `name` and `roles` from this `user` object; tokens never carry a name.

### 6. Sessions

A session (`sid`) starts at login and ends at logout, timeout or revocation. Every token from that login carries its `sid`.

| Kind | Ends after | Enforced by |
|---|---|---|
| Web | 30 minutes without user input in any app on that session, or 12 hours after login | welinc-auth, from activity pings. Each web app, while there is real user input (keys, clicks, touches; background polling doesn't count), calls `POST /<sys>/session/activity` at most once a minute, and its backend passes it to `POST /auth/session/activity`. Working in BMS keeps your VRMS tab's session alive, because it is the same `sid`. Logins and code exchanges also count as activity. A web refresh never does, so a tab refreshing in the background still reaches the idle cutoff (spec 0003). |
| Mobile | 7 days without a refresh | welinc-auth; each refresh extends it 7 days. No absolute limit. |

- A user holds at most `MAX_SESSIONS_PER_USER` (10) live sessions. An 11th login ends the one with the oldest activity (`MAX_SESSIONS`).

- The session's expiry, as `/auth/session` and `session_expires_at` report it, is the earlier of the idle cutoff and the absolute cutoff.

- **One web login covers every system.** The portal's SSO cookie means opening a second system needs no password. Each system gets its own refresh token under the same `sid`.
- **Logout anywhere ends the session everywhere.** Logout from VRMS ends the `sid`, so VMMS and BMS lose it at their next session check (30 s at most).
- **What ends a session at once:** logout, the user or an admin ending it, deactivation, deletion, a password change on the profile (every other session of that user), an OTP reset or an admin password set (every session), reuse of an old refresh token or login code, and an 11th session. The automatic lock (5 failed logins) blocks new logins only and ends no live session, so a stranger who knows an email can't sign someone out mid shift (spec 0003).

**Session check** (each system backend, on every request with a user token):

1. Verify the signature, `iss`, `aud` (its own system) and `exp`.
2. Call `GET /auth/session` with the user's token, caching the answer by `sid` for at most 30 s. The check covers the account too (deactivated, locked or deleted ends it).
3. Use `roles` from the token for permission checks (VRMS keeps its CASL matrix on top, spec 0011).

**When welinc-auth is down:** the check fails closed. With no cached answer younger than 30 s, the request gets 503 `AUTH_UNAVAILABLE`, never "allowed". Health checks, public routes (BMS tracking links, BMS's Wix integration) and service token routes skip the session check. The mobile app keeps offline work in its local queue and sends it only after a refresh succeeds.

This generalizes VRMS's `account-check.ts` (spec 0009), which moves from `/auth/me?system=VRMS` to `/auth/session`.

### 7. Web login flow (VRMS, VMMS and BMS web)

Each system backend owns four routes under its prefix, and the web app never sees a code or a refresh token. VRMS builds them first as the reference implementation.

1. The web app has no access token (fresh load) and calls `POST /<sys>/session/refresh`. With no valid cookie it gets 401.
2. The web app navigates the whole page to `GET /<sys>/session/start?return=<path>`.
3. The backend checks `return` by resolving it against the system's web address and keeping it only if the result has the same origin; anything else becomes `/`. It makes a `state` and a PKCE verifier (a random secret it will show again at the exchange), keeps all three in a short lived HttpOnly cookie (`<sys>_login_<first 8 characters of state>`, so several tabs logging in at once don't overwrite each other; 10 minutes, path `/<sys>/session`), and redirects to `GET /auth/authorize?client_id=<sys>&redirect_uri=<api>/<sys>/session/callback&state=…&code_challenge=…&code_challenge_method=S256`.
4. welinc-auth checks the client and the exact redirect address (on mismatch it shows an error page and never redirects).
   - Valid SSO cookie and the user holds a role in the system: redirect to the callback with `code` and `state`.
   - Valid SSO cookie but no role in the system: redirect to the callback with `error=access_denied` and `state`.
   - No valid SSO cookie: store a login request (section 5) and redirect to `<portal>/login?request=<id>`. The portal signs in through `POST /auth/login` (which sets the SSO cookie), then sends the browser to `GET /auth/authorize/resume?request=<id>`, which continues as above. An expired or used request sends the browser to `<portal>/?error=LOGIN_REQUEST_EXPIRED`.
5. `GET /<sys>/session/callback?code&state` on the backend checks `state` against its `<sys>_login` cookie, clears that cookie, and calls `POST /auth/token` (authorization code grant, with the verifier and its client assertion).
6. The backend sets the refresh cookie and redirects to `<system web address><return>`.
7. The web app calls `POST /<sys>/session/refresh` again and now gets the access token, held in memory only.

**Callback failures** never show a raw error. The backend redirects to `<portal>/?error=<code>`: `access_denied` becomes `NO_SYSTEM_ACCESS` (with `&system=<SYS>`); a missing, expired or mismatched `<sys>_login` cookie becomes `LOGIN_STATE_INVALID`; a failed exchange becomes `LOGIN_FAILED`. The portal shows a plain message and a button to try again.

**Boot sequence in the web app** (no redirect loops):
1. Call `refresh`. On 200, the app runs.
2. On 401, go to `start` once, marking the attempt in `sessionStorage` (a flag, never a token).
3. If the app loads again with that flag set and `refresh` still answers 401, clear the flag and send the browser to `<portal>/?error=LOGIN_FAILED` instead of looping.
4. On a 401 `SESSION_ENDED` while the app is in use (logout elsewhere, idle cutoff, admin action), drop the in-memory token and go to `<portal>/login`.
5. Only one refresh runs at a time per app (a Web Lock named `<sys>-refresh`); other tabs wait for its result.

**Cookies:**

| Cookie | Set by | Name | Path | Flags | Max age |
|---|---|---|---|---|---|
| Refresh | each system backend | `<sys>_rt` (e.g. `vrms_rt`), `__Secure-<sys>_rt` when hosted | `/<sys>/session` | `HttpOnly`, `Secure` (hosted), `SameSite=Lax`, host only (no `Domain`) | the session's remaining 12 hours |
| Login state | each system backend | `<sys>_login_<state prefix>`, `__Secure-` prefixed when hosted | `/<sys>/session` | as above | 10 minutes |
| SSO | welinc-auth | `welinc_sso`, `__Secure-welinc_sso` when hosted | `/auth` | as above | the session's remaining 12 hours |

Host only cookies keep staging and production apart: `staging-api.<domain>` never sees `api.<domain>`'s cookies. Locally, cookies are shared across `localhost` ports, but the names differ.

**System backend session routes:**

| Route | Method | In | Out | Errors |
|---|---|---|---|---|
| `/<sys>/session/start` | GET | `return` (path) | sets `<sys>_login`, 302 to `/auth/authorize` | none |
| `/<sys>/session/callback` | GET | `code` and `state`, or `error` and `state` | sets `<sys>_rt`, 302 to the app | 302 to the portal with an error code (above) |
| `/<sys>/session/refresh` | POST | the `<sys>_rt` cookie | `{ accessToken, expiresIn, sessionExpiresAt, sessionAbsoluteExpiresAt, user: { id, name, email, roles } }` from the `/auth/token` answer (`sessionAbsoluteExpiresAt` is the 12 hour end, so the app can tell it from the idle cutoff; spec 0003 AC-23); rotates the cookie | 401 `SESSION_ENDED` |
| `/<sys>/session/activity` | POST | the `<sys>_rt` cookie | 204; passes the ping to `POST /auth/session/activity` | 401 `SESSION_ENDED` |
| `/<sys>/session/logout` | POST | the `<sys>_rt` cookie | 204, clears the cookie, ends the `sid` at welinc-auth (which kills the SSO handle too) | none (always clears) |
| `/<sys>/session/status` | GET | bearer user token | `{ sessionExpiresAt }`, asked fresh at welinc-auth, for the idle warning (spec 0003) | 401, 503 |

**CSRF guard** (stops another page from making calls with your cookie). It applies to every POST route that a cookie authenticates: the system's `refresh`, `activity` and `logout`, and welinc-auth's `/auth/login`, `/auth/logout` and `/auth/session/activity` when called with the SSO cookie. The GET routes a page navigation reaches (`/auth/sso`, `/auth/authorize`, `/auth/authorize/resume`, `/<sys>/session/start`, `/<sys>/session/callback`) change no state a third party can use and skip it, since a navigation sends `Sec-Fetch-Site: none` or `cross-site` (spec 0003).
1. POST only, with `Content-Type: application/json`. A refused request gets 403 `CSRF_REJECTED`.
2. The `Origin` header must equal exactly one allowed web address: the system's own for its routes, the portal's for welinc-auth's. Browsers set this header themselves, so a sibling subdomain can't fake it.
3. `Sec-Fetch-Site` must be `same-origin` or `same-site` when the browser sends it.
4. The gateway's CORS list is the outer layer.

- **Switch system** in every app links to the portal (`<portal>/`), which shows the launcher straight away thanks to the SSO cookie.
- After logout the web app sends the browser to `<portal>/login`. Since the `sid` is gone, the old SSO cookie no longer counts and the portal asks for the password.
- **The portal** is login plus launcher only. It authenticates with the SSO cookie on `/auth/login`, `/auth/logout`, `/auth/sso` and the authorize routes, and holds no access token. Profile pages live in each app.

### 8. Mobile login (`vmms-mobile`)

The app keeps its own native screens and talks to welinc-auth directly. The login rules (lockout, OTP, reset, rate limits) still run only on the server.

| Step | Call | Notes |
|---|---|---|
| Log in | `POST /auth/mobile/login` with `{ email, password, clientId: "vmms-mobile", deviceName }` | Answers like the `/auth/token` user grants (section 5), in camel case: `{ accessToken, refreshToken, expiresIn, sid, sessionExpiresAt, user }`, with `aud` set to the client's default system (`VMMS`). No cookie. A user with no role in that system gets 403 `NO_SYSTEM_ACCESS`. |
| Admin OTP (feature 34, later) | `POST /auth/mobile/login/otp` with `{ challengeId, code }` | Reserved: the login may answer `{ status: "OTP_REQUIRED", challengeId }`. The portal gets the same step on `/auth/login/otp`. |
| Refresh | `POST /auth/token` with `grant_type=refresh_token`, `refresh_token`, `client_id=vmms-mobile`, optional `audience` (`VMMS` or later `VRMS`) | Rotates the refresh token, with the same 10 s grace for a retry after a lost answer. One mobile session can get an access token for each system the user holds; an audience the user holds no role in gets 403 `NO_SYSTEM_ACCESS`. |
| Log out | `POST /auth/logout` with `{ refreshToken }` | Ends the `sid`. |
| Forgot password, OTP, reset | the existing `/auth/forgot-password`, `/auth/verify-otp`, `/auth/reset-password` | Unchanged. |

- The refresh token stays in `expo-secure-store`, as it does today.
- `deviceName` is what the user's phone reports. It is shown in session lists and activity, never trusted for a security decision.
- **Known gap, accepted:** anyone can call `/auth/mobile/login` claiming to be `vmms-mobile` (a public client has no secret), so reCAPTCHA (WL-103, web only) doesn't protect it. It keeps the same per account lockout and a stricter limit per address (section 12). App attestation (Apple App Attest, Google Play Integrity) is the later hardening step.
- `/auth/login` (the portal's) never returns tokens in the body, and `/auth/mobile/login` never sets a cookie.
- Local development: a phone or emulator can't reach `localhost`, so the app's API base is the computer's LAN address (`http://<lan ip>:3000`). The token issuer stays as configured; the app never checks it.
- The `X-VMMS-Client` header and VMMS's own `/auth/*` routes go away in S11.

### 9. User directory (for systems, with a service token holding `directory.read`)

The caller's system is its client's **System** (section 4), so `vmms-analytics` sees VMMS's view.

| Route | Method | In | Out |
|---|---|---|---|
| `/auth/directory/users/lookup` | POST | `{ ids: uuid[] }` (at most 200) | `{ users: DirectoryUser[], missing: uuid[] }` |
| `/auth/directory/users` | GET | `cursor?`, `limit?` (100, at most 500) | every user who holds a role in the caller's system: `{ users: DirectoryUser[], next, changesCursor }` (for the first sync) |
| `/auth/directory/changes` | GET | `after?` (cursor), `limit?` (100, at most 500) | `{ changes: DirectoryChange[], next, hasMore }` in order |

```ts
type DirectoryUser = {
  id: string;            // uuid, the same as the token's sub
  name: string;
  email: string;
  phone: string | null;   // null unless the token also holds directory.contact
  phoneVerified: boolean;
  picture: string | null; // an /uploads address
  isActive: boolean;
  deleted: boolean;       // soft deleted; name and email kept for history
  roles: string[];        // roles in the caller's system only
  updatedAt: string;      // ISO 8601
};

type DirectoryChange = {
  cursor: string;         // opaque, store the last one you processed
  type: 'created' | 'updated' | 'roles_changed' | 'activated' | 'deactivated' | 'deleted';
  at: string;
  user: DirectoryUser;    // the state after the change, so no extra lookup is needed
};
```

- **Which users a system sees:** only users who hold, or once held, a role in the caller's system. Lookup returns them with `roles` for that system (empty if they lost it, since a record may point to someone who has since left); every other id comes back in `missing`, deleted users included. Soft deleted users of the system come back with `deleted: true`.
- **What the feed carries:** every change to a user who holds a role in the caller's system at the time of the change. When a user loses their last role there, the system gets one `roles_changed` with `roles: []`, then no more changes about them until they get a role back (which arrives as `roles_changed`).
- **Cursors:** a cursor is an opaque wrapper around a sequence number welinc-auth assigns to each change. The feed only serves changes older than 5 s, so a slow transaction that commits late is never skipped. Leaving `after` out starts from the very first change. Cursors never expire, so a system that was down catches up from its last one.
- **First sync:** page through `/auth/directory/users`, then start the feed from the `changesCursor` of the first page. It is taken before the scan, so nothing that changes during the scan is lost (a change may arrive twice, which is harmless).
- **How systems use it:** keep a local copy of only what you show (name, email, roles, active), keyed by `sub`. Poll the feed every 30 to 60 s from the stored cursor and apply changes in order. Applying the same change twice must be harmless.
- **Reserved for later (not built):** an optional webhook nudge. welinc-auth would POST `{ "type": "directory.changed" }`, with no user data, to an address a system registers, and the system polls the feed at once. Adding it changes nothing above.
- No system reads the auth database. Security never rides on the feed: deactivation is caught by the session check (section 6).

### 10. welinc-auth routes for people

Existing routes stay unless marked. "System" means the token's `aud`; the old `?system=` parameter and the `Origin`, `Referer` and path guessing are removed.

| Route | Method | Who | Status | Row |
|---|---|---|---|---|
| `/auth/.well-known/jwks.json` | GET | anyone | new | S2 |
| `/auth/.well-known/oauth-authorization-server` | GET | anyone; issuer and endpoint addresses (RFC 8414) | new | S2 |
| `/auth/authorize`, `/auth/authorize/resume` | GET | browser | new | S3 |
| `/auth/token` | POST | clients | new | S2, S3, S4 |
| `/auth/login` | POST | portal only: sets the SSO cookie, no token in the body. Until S4 adds the launcher it answers `{ user: { id, name, email }, system, url }`: the system welinc-auth picks (spec 0002) and that client's web address; 403 `NO_SYSTEM_ACCESS` with no role anywhere | changed | S2, S3, S4 |
| `/auth/login/otp` | POST | portal | reserved | feature 34 |
| `/auth/mobile/login`, `/auth/mobile/login/otp` | POST | `vmms-mobile` (tokens in the body, section 8) | new (OTP reserved) | S3 |
| `/auth/logout` | POST | SSO cookie, a client with assertion and refresh token, or `vmms-mobile` with refresh token | new | S3 |
| `/auth/sso` | GET | SSO cookie (portal) | new: until S4, `{ user: { id, name, email }, system, url }` like `/auth/login`; S4 makes it `{ user: { id, name, email, picture }, systems: [{ system, name, url, roles }] }` | S3, S4 |
| `/auth/session` | GET | user token | new: `{ active: true, sid, expiresAt, user: { id, name, email } }` (`expiresAt` is the earlier of the idle and absolute cutoffs; systems take the caller's name from `user`) or 401 with `SESSION_ENDED`, `ACCOUNT_INACTIVE` or `TOKEN_EXPIRED`. A locked account's live session still answers 200 | S3 |
| `/auth/session/activity` | POST | a confidential client with its assertion and the user's refresh token, or the SSO cookie | new: 204, marks the `sid` active | S3 |
| `/auth/systems` | GET | anyone | new: each system's code, name, web address, roles and rules (e.g. VMMS: exactly one role) | S5 |
| `/auth/me` | GET | user token | changed: roles for `aud` only, no `?system=` | S5 |
| `/auth/me/sessions` | GET | user token | new: `{ sessions: SessionView[] }` (spec 0003: `sid`, kind, device, client, systems, created, last active, `current`) | S3 |
| `/auth/me/sessions/:sid` | DELETE | user token | new: end one of your sessions | S3 |
| `/auth/forgot-password`, `/auth/verify-otp`, `/auth/reset-password` | POST | anyone | kept | none |
| `/auth/profile`, `/auth/profile/password`, `/auth/profile/picture`, `/auth/profile/summary` | PATCH, POST, GET | user token | kept | none |
| `/auth/profile/activity` | GET | user token | new: your logins, failures, lockouts, logouts and refreshes, newest first, cursor paged | S7 |
| `/auth/profile/phone` | POST | user token | new: `{ phone }`, sends a code by SMS | S8 |
| `/auth/profile/phone/verify` | POST | user token | new: `{ code }` | S8 |
| `/auth/profile/verify-password` | POST | user token | new: `{ password }` gives `{ reauthToken }` | S8 |
| `/auth/profile/deletion-request` | POST | user token | new: `{ reauthToken, reason? }`; an admin reviews it | S8 |
| `/auth/users`, `/auth/users/lookup`, `/auth/users/:id`, `/auth/users/:id/status`, `/auth/users/:id/password`, `/auth/users/:id/unlock`, `/auth/users/:id/changes` | as today | that system's admin | kept, with the spec 0011 scoping | none |
| `/auth/users/:id/sessions` | GET, DELETE | that system's admin | new: list or end all of a user's sessions | S3 |
| `/auth/users/:id/activity` | GET | that system's admin | new | S7 |
| `/auth/activity` | GET | that system's admin | new: login activity of that system's users (BMS's activity page) | S7 |
| `/auth/deletion-requests` | GET | admin of any system the user holds | new | S8 |
| `/auth/deletion-requests/:id/approve`, `/reject` | POST | admin of any system the user holds | new: approve deactivates and soft deletes, history kept | S8 |

- VMMS's `me/login-activity` maps to `/auth/profile/activity`, its `users/:id/login-activity` to `/auth/users/:id/activity`, and its `audit-logs` for accounts to `/auth/users/:id/changes` plus `/auth/activity`.
- welinc-auth owns phone numbers and their verified flag (S8 picks the SMS provider; VMMS uses Semaphore today).
- S10 (suite admin) may add routes and roles. It must not change any claim above.

### 11. Errors

- welinc-auth and the system session routes answer with Nest's usual body plus a stable `code`: `{ "statusCode": 409, "message": "…", "error": "Conflict", "code": "ACCOUNT_EXISTS" }`. Clients branch on `code`, never on `message`.
- `/auth/token` answers in the OAuth format so standard libraries understand it: `{ "error": "invalid_grant", "error_description": "…" }` (400), `invalid_client` (401), or `invalid_target` and `invalid_scope` (400) for an audience or scope the client may not have.
- Codes this contract introduces: `SESSION_ENDED`, `ACCOUNT_INACTIVE`, `ACCOUNT_LOCKED`, `TOKEN_EXPIRED` (a good token past its `exp`: refresh and retry once), `CSRF_REJECTED`, `AUTH_UNAVAILABLE`, `NO_SYSTEM_ACCESS`, `WRONG_AUDIENCE`, `WRONG_TOKEN_USE`, `REAUTH_REQUIRED`, `RATE_LIMITED`, and the portal error codes `LOGIN_REQUEST_EXPIRED`, `LOGIN_STATE_INVALID`, `LOGIN_FAILED`.

### 12. Limits

| Route | Limit | Answer when over |
|---|---|---|
| `/auth/login` | 10 a minute per address and 5 failures per account (the existing lockout) | 429 `RATE_LIMITED` with `Retry-After`, or 423 locked |
| `/auth/mobile/login` | 5 a minute per address, sharing the per account lockout | as above |
| `/auth/token` | 600 a minute per client for calls with a valid assertion, which skip the per address count; 120 a minute per address for every other call and every refused assertion (spec 0003). `vmms-mobile` 30 a minute per address | 429 with `Retry-After` and `{ "error": "rate_limited" }` |
| `/auth/authorize` | 30 a minute per address | 429 error page |
| `/auth/session/activity` | 2 a minute per `sid` (extra pings are accepted and ignored) | none |
| `/auth/session` | none beyond the gateway; systems cache 30 s | none |
| `/auth/directory/*` | 120 a minute per client | 429 |
| `/auth/users/lookup` | 30 a minute (kept) | 429 |

- A confidential client's call with a valid assertion may carry `X-WeLinc-User-Address`, the user's address as the system backend saw it (its own `X-Forwarded-For` through `TRUST_PROXY_HOPS`). welinc-auth stores it as the session's last seen address and ignores the header on any call without a valid assertion (spec 0003).

S rows may tighten these and must note it here.

### 13. Rules every system follows

1. Store people by `sub` (the welinc-auth user id). Never key on email, never add a foreign key to an auth table, never read the auth database.
2. Accept only tokens whose `iss` is the issuer, whose `aud` is your system, and whose `token_use` fits the route.
3. Run the session check (section 6) on every user request.
4. Keep no password, code, refresh token or role assignment of your own. Your own permission rules on top of the token's roles are fine (VRMS's matrix).
5. Your system's own rules about roles (VMMS: exactly one role per account) live in welinc-auth's system catalog (S5), not copied into your code.
6. Web apps keep the access token in memory only; no `localStorage`, no token in a URL.
7. Secrets (your client private key) live in your Container Apps secrets and your git ignored `.env`, documented in `.env.example` only.
8. BMS's public tracking links keep their own secret inside BMS and never use welinc-auth's keys or tokens.

### 14. How the contract changes

- **Additive** (a new route, an optional field, a new claim, a new error code): update this spec in the same change.
- **Breaking** (removing or renaming a route, claim or field, or changing what one means): bump the contract version, list each system's change here, and tell the affected groups before it lands. The shared services owner decides; the other groups don't review this spec.
- Each S row spec links back here and states which sections it builds.

### 15. Configuration

**welinc-auth** (new or changed; values in `.env.example` only):
- `AUTH_ISSUER`: the issuer from section 1.
- `AUTH_SIGNING_KEYS`: the private signing keys as a JWK set, each with its `status` (section 5); a Container Apps secret when hosted. Replaces `JWT_SECRET`.
- `TRUST_PROXY_HOPS`: proxy hops in front of welinc-auth (1 locally, 2 hosted), for the per address limits (spec 0002).
- `ACCESS_TOKEN_MINUTES` (15), `SERVICE_TOKEN_MINUTES` (5), `WEB_SESSION_IDLE_MINUTES` (30), `WEB_SESSION_MAX_HOURS` (12), `MOBILE_SESSION_IDLE_DAYS` (7), `REFRESH_REUSE_GRACE_SECONDS` (10), `MAX_SESSIONS_PER_USER` (10), `SESSION_RETENTION_DAYS` (90). Replace `JWT_ACCESS_EXPIRY` and `JWT_REFRESH_EXPIRY`.
- `API_PUBLIC_URL`: the gateway address the browser sees; the seed builds each system's redirect address from it. `CLIENT_<ID>_WEB_ADDRESS` per system client (spec 0003).
- `PORTAL_URL` (kept), `SSO_COOKIE_SECURE` (true when hosted).
- The client registry (section 4) comes from the seed per environment, with each client's public keys and redirect address read from environment values.

**Each system backend:**
- `AUTH_ISSUER`, `AUTH_INTERNAL_URL` (welinc-auth's internal address for server calls), `AUTH_JWKS_URL`.
- `AUTH_CLIENT_ID`, `AUTH_CLIENT_PRIVATE_KEY` (secret; its own ES256 key).
- `WEB_APP_URL` (where users land, and the one `Origin` its cookie routes accept), `PORTAL_URL`.
- `AUTH_PUBLIC_URL` (welinc-auth as the browser sees it, for `/auth/authorize`), `API_PUBLIC_URL` (its callback is `<API_PUBLIC_URL>/<sys>/session/callback`), `SESSION_COOKIE_SECURE`, `TRUST_PROXY_HOPS` (spec 0003).

**Each web app:** `VITE_API_BASE_URL` and `VITE_PORTAL_URL` only. No secret, no token setting.

## Gap map

Every gap from the 2026-11-07 check, mapped to the row that closes it.

| Gap today | Closed by |
|---|---|
| One `JWT_SECRET` held by every service, so any of them can mint a token | S2 |
| VMMS has its own users, roles, refresh tokens, login activity, phone verification and account audit logs | S3, S5, S6, S7, S8, then S11 removes them |
| VMMS web takes `?token=` from the portal; VRMS and the portal do the same | S4 |
| VMMS mobile logs in against the VMMS copy (`X-VMMS-Client`) | S3 (mobile client), S11 |
| VMMS analytics checks callers through `GET auth/me?system=VMMS` on the VMMS backend | S2 (verify with JWKS), S3 (session check) |
| The BMS gateway reads `users`, `user_roles` and `user_activity_logs` straight from the auth database | S6, S7, then S11 |
| BMS calls `profile/activity`, `profile/verify-password` and `profile/deletion-request`, which don't exist | S7, S8 |
| BMS has no portal handoff | S4 |
| BMS runs auth from the old `welinc-backend` repo with admin checks removed and no refresh | S11 retires it |
| BMS roles (Admin, Customer Support, Operations) and VMMS's one role rule live only in their code | S5 |
| welinc-auth guesses the system from `?system=`, `Origin`, `Referer` and the path | S5 (the system is `aud`) |
| welinc-auth has a `RefreshToken` table but no refresh or logout | S3 |
| welinc-auth records no login activity | S7 |
| welinc-auth has no phone verification | S8 |
| Ports clash (VMMS 3000, both analytics 3001, BMS booking 3002) | S9 (section 2) |
| The gateway routes only `/auth`, `/vrms`, `/repairs`, and its config lives in `welinc-auth` | S9 (section 3) |
| Seed accounts drift across three copies (`ops.user`, VMMS chief mechanics) | S12 |
| No safe "can do everything" admin across systems | S10 (outside this contract) |

## Move order

Each step is proven end to end before the next starts (Tracer Bullet).

1. **VRMS and the portal, step by step with S2, S3, S5, S6, S4 and S9.** Signing moves to ES256 with S2 (no dual run: VRMS and the portal are the only real users). The `?token=` handoff goes when S4 lands. VRMS's mechanic sync moves onto the directory feed with S6.
2. **S7 and S8**, so the routes BMS and VMMS already call exist before they move.
3. **BMS (S11, first).** `bms-gateway` becomes client `bms`, drops its auth database reads and the old `welinc-backend` copy, moves to `/bms` and the 3020 block, and the BMS web app moves to the session routes.
4. **VMMS (S11, second).** The backend becomes client `vmms` and drops its `/auth/*` copy and user tables. The analytics service verifies tokens itself. The web app moves to the session routes, the mobile app to `vmms-mobile`, and everything to `/vmms` and the 3010 block. VMMS users merge into welinc-auth by email (S11's import script).
5. **S10**, the suite admin model, once roles, the directory and OTP exist.

The detailed per group guide, import script and test plan belong to S11.

## Consequences

**Positive**:
- One token can no longer act in every system, and no service except welinc-auth can mint one.
- Tokens leave URLs and browser storage; script injection on a page can't take a session with it.
- The other groups get a complete, stable list of routes, claims and ports to build against now.
- Removal of a user reaches every system within 30 seconds; even a backend that skips the check loses access when the 15 minute access token runs out.
- The standard names (OAuth code flow, PKCE, `private_key_jwt`, JWKS) give the capstone papers a clear security story.

**Negative / tradeoffs**:
- welinc-auth becomes a real authorization server the team must build and get right (code flow, rotation with reuse detection, assertion replay checks). That is the riskiest work in the suite, hence the GA workflow on every S row.
- Each system writes four session routes and a token check on keys; VRMS's reference implementation and S11's guide soften it, but it is real work for both other groups.
- A custom domain is now required for hosted login. Default Azure addresses no longer work for it, and the domain must be renewed after its free year.
- Mobile keeps a native login, so the app must follow login rule changes (such as OTP) with an app update.
- One more call per request group (the session check), cached, so welinc-auth being down blocks new requests after 30 s. welinc-auth keeps minimum replicas of 1 (spec 0008).
- Idle tracking on the server costs an activity ping from each open app, at most once a minute while someone is working.
- The mobile login isn't covered by reCAPTCHA. Lockout and a stricter limit per address stand in until app attestation.
- Hard switch: BMS's local setup that verifies HS256 tokens from its old copy stops matching welinc-auth. It wasn't connected, but it must be told.

**Neutral**:
- `roles` keeps its shape, so existing role checks only change their filter.
- Gateway config moves to `infra/gateway/` and `welinc-auth/nginx.conf` is deleted.
- VRMS's `account-check.ts`, `SsoHandoff.tsx`, `SessionMonitor.tsx` and the `localStorage` token in `axios.ts` are replaced as S3 and S4 land.

## Follow-up

- [ ] Register the domain (working name `welinc.tech`; the GitHub Student Developer Pack has offered a free year of `.tech`, check the current offer) and note the renewal date.
- [ ] Update spec 0008 (VRMS hosting): custom domain on every Static Web App and on the gateway Container App, the `infra/gateway/` local config, and the new routes and ports. A new VRMS spec or an update, through `/architect`.
- [ ] Add a line to `docs/_private/vrms/shared-services-questions.md` for BMS: HS256 tokens and `JWT_SECRET` go away when S2 lands, so they shouldn't build more on them; the contract is this spec.
- [ ] VRMS feature 56 (domain contracts) uses section 5's service tokens for calls between systems and lists each system's scopes there.
- [ ] S12 (suite seed accounts) gets its own spec, not this one; it must create the clients of section 4 alongside the people.
- [ ] Later hardening (not scheduled): app attestation on `/auth/mobile/login` (Apple App Attest, Google Play Integrity).
- [ ] `welinc-mobile-bms` is still used (BMS, 2026-11-08), for drivers and helpers, so WeLinc staff (answered 2026-11-08). It becomes a `bms-mobile` client like `vmms-mobile` (a public native row in section 4 with `mobile_login` and `refresh_token`; spec 0003's mobile routes take any such row, so no code change), and BMS gets Driver and Helper roles through S5.
- [ ] After S9, update the README repos table with section 2's ports and the root `AGENTS.md` shared services table (gateway config home). That is `/sync`'s job, through a PR.
- [ ] Run `/architect` for each S row in the epic's order (S2 first); each spec links back to the sections it builds.
