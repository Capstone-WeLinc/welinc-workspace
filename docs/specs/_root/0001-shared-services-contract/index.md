# 0001. Shared services contract for the WeLinc suite

**Date**: 2026-11-08
**Status**: Accepted
**Scope row**: [S1. Shared services contract](../../../scope/_root/shared-services.md#s1-shared-services-contract--done)
**Contract version**: 8.2
**Amended**: 2026-11-09, additive, from spec [0004](../0004-roles-per-system/index.md) (sections 4, 8, 10, 11, 12, 13) · 2026-11-09, version 2 (breaking), from spec [0005](../0005-user-directory/index.md) (sections 5, 9, 10, 11, 12, 14, 15 and the gap map) · 2026-11-11, version 3 (breaking, no caller affected), from spec [0008](../0008-suite-gateway/index.md) (sections 2, 3, 11, 12, 14) · 2026-11-11, version 4 (breaking), from spec [0009](../0009-email-verification/index.md) (sections 8, 10, 11, 12, 14) · 2026-11-12, version 5 (breaking), from spec [0011](../0011-account-activity-audit/index.md) (sections 10, 11, 12, 14 and the gap map) · 2026-11-12, version 6 (breaking), from spec [0012](../0012-profile-extras/index.md) (sections 7, 9, 10, 11, 12, 14 and the gap map) · 2026-11-13, version 7 (breaking), from spec [0013](../0013-suite-admin-model/index.md) (sections 4 to 15 and the gap map; the new section 10a) · 2026-11-13, version 8 (breaking), from spec [0014](../0014-move-vmms-bms-shared-services/index.md) (sections 4, 7, 10, 11, 12, 14, the gap map and the move order) · 2026-11-16, additive, from VRMS spec [0026](../../vrms/0026-api-docs/index.md) (section 14 and the new section 16, the route index) · 2026-11-17, additive, the domain is `welinc.app` instead of the working name `welinc.tech` (section 1 and Follow-up; no caller held the old name) · 2026-11-17, additive, from VRMS spec [0025](../../vrms/0025-error-monitoring/index.md) (section 3: `sentry-trace` and `baggage` allowed on preflights) · 2026-11-17, additive, from VRMS spec [0025](../../vrms/0025-error-monitoring/index.md) milestone 2 (section 3: the two `/monitoring/*` Sentry tunnel routes) · 2026-11-17, additive, from VRMS spec [0025](../../vrms/0025-error-monitoring/index.md) task 7a (sections 3 and 11: the tunnel's envelope DSN check and `TUNNEL_REJECTED`) · 2026-11-23, additive, from suite spec [0016](../0016-design-direction-refresh/index.md) AC-12a (section 10: `sessionExpiresAt`, `sessionAbsoluteExpiresAt` and `serverTime` on the launcher answer; the portal joins the web apps that send activity pings) · 2026-11-24, additive, from suite spec [0019](../0019-portal-redesign/index.md) (section 10: `suiteAdmin` on the launcher answer; section 10a: `GET /auth/admin/users/email-check`, an optional `contact` on `POST /auth/admin/users`; section 12: the email check limit; section 16: the route; the summary route drafted here was removed on 2026-11-26 before it shipped) · 2026-11-25, additive, from suite spec [0019](../0019-portal-redesign/index.md) AC-21a, AC-21b (section 10a: `access` and the `ATTENTION` and `ACTIVE_GROUP` statuses on `GET /auth/admin/users`, `GET /auth/admin/users/facets`; section 12: the facets limit; section 16: the route) · 2026-11-27, version 8.1 (additive), from suite spec [0018](../0018-roles-and-custom-roles/index.md) (sections 9, 10, 10a, 11, 13, 14 and 16: `builtIn` and revalidation on `/auth/systems`, custom role codes, the Roles routes) · 2026-11-28, version 8.2 (additive), from VRMS spec [0027](../../vrms/0027-navigation-redesign/index.md) (section 5: `user.systemRoles` and `user.suiteAdmin` on the user grants answer; the OpenAPI doc changes with it)

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
| Web login | Code exchange on each system's backend (OAuth authorization code with PKCE), refresh token in an HttpOnly cookie on the shared domain, access token in memory only | S3 (spec 0003) |
| Web session | 30 minutes without user input in any app, or 12 hours since login, whichever comes first; idle is tracked on the server through a light activity ping | S3 |
| Mobile login | Native login screen in the app, calling its own welinc-auth route (`/auth/mobile/login`) as a first party mobile client | S3 |
| Mobile session | 7 days rolling (each refresh extends it) | S3 |
| Revocation | Each backend checks the session at most 30 s stale; deactivation and logout also revoke refresh tokens, so a backend that skipped the check still loses access when the 15 minute access token runs out. The automatic lock blocks new logins only (spec 0003) | S3 |
| Service identity | Signed client assertion (`private_key_jwt`): each backend proves itself with its own ES256 key | S2 |
| Launcher | The portal lists the systems you hold when you open it yourself and hold two or more; with one it sends you straight in, unless you are that system's Admin (then the launcher, for the Admin card). Each app's Switch system opens `<portal>/?from=<SYS>` and shows with two or more systems, or for an Admin of that system (amended 2026-11-14, spec 0007 AC-9 and AC-14). Version 8: a system held only through its phone app is listed apart (`mobileSystems`) and never opened on the web | S4 (spec 0007), S11 (spec 0014) |
| User directory | Batch lookup by id plus a cursor change feed; a thin webhook nudge is reserved for later | S6 |
| Gateway paths | Each service serves under its own prefix; the gateway forwards without rewriting | S9 |
| Gateway config | Workspace repo `infra/gateway/`, for local and hosted (as spec 0008 planned), out of `welinc-auth` | S9 |
| Ports | One block per system (below) | S9 |
| Old login | Hard switch: VRMS and the portal move straight to the new flow; `JWT_SECRET` and `?token=` are removed, no dual run | S2, S3 |
| Move order | VRMS and the portal first (tracer bullet), then VMMS and BMS in parallel, each done at its checker and the cross check (version 8) | S11 (spec 0014) |
| Admin | 1 to 3 suite admins with no system roles (temporary access with a reason when they must look inside), an emailed code at every admin sign in, account management only in the portal admin section, the permission matrix optional in welinc-auth (version 7) | S10 (spec 0013) |

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

- `<domain>` is one registered domain, `welinc.app` (registered 2026-11-17, see Follow-up). Every web app and the gateway share it, so the browser treats them as one site and the refresh cookie counts as first party. Locally, `localhost` on any port is also one site.
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
- **Docker service names** (spec 0008): the gateway reaches each upstream by its Docker service name, so every compose file uses these: `auth-service`, `vrms-backend`, `vmms-backend`, `vmms-analytics`, `bms-gateway`. S11's compose files for VMMS and BMS must use them. Hosted, the same settings hold the full internal names instead.

### 3. Gateway routes

| Path prefix | Goes to | Body limit | Read timeout |
|---|---|---|---|
| `/auth/`, `/uploads/` | `welinc-auth` 3001 | 5 MB | 30 s |
| `/vrms/` | `welinc-backend-vrms` 3002 | 26 MB | 120 s |
| `/vmms/analytics/` | `welinc-backend-vmms-analytics-ai` 3011 | 1 MB | 120 s |
| `/vmms/` | `welinc-backend-vmms` 3010 | 10 MB | 60 s |
| `/bms/` | `bms-gateway` 3020 (which fans out to the BMS services and analytics itself) | 10 MB | 60 s |

- **Sentry tunnel** (VRMS spec 0025, additive): `POST /monitoring/vrms-web` and `POST /monitoring/portal`, exact paths, are the gateway's own routes for the browser crash reports of welinc-web-vrms and the portal. Each forwards only reports whose envelope header names its own app's DSN (the same key, host and project id) to that project's envelope address; any other body answers 403 `TUNNEL_REJECTED` and never reaches Sentry (Sentry files a report under the DSN inside it, not the address). Each has a 1 MB body limit, a 10 s read timeout and its own limit per client of 1 a second with bursts of 10 (429 `RATE_LIMITED`), and without `Cookie`, `Authorization`, `Referer`, `X-Request-Id` or any client address. `OPTIONS` answers 204 with CORS (methods `POST, OPTIONS`, request header `Content-Type`), any other method 405 `METHOD_NOT_ALLOWED` with `Allow: POST, OPTIONS`. Turned off (the tunnel settings blank, as locally), both answer 404 `NOT_FOUND`. Another system that wants a tunnel adds its own route the same way; `docs/integration/error-monitoring.md` (spec 0025, milestone 4) says how.
- **No rewriting.** Each service serves its own prefix (VMMS sets a global `vmms` prefix and serves analytics under `vmms/analytics`; `bms-gateway` swaps its `/api` strip for `/bms`). The same path works directly on the service port and through the gateway.
- **Prefixes end in a slash** (version 3). `/vmmsx` never matches `/vmms/`, and a bare prefix with no slash (`/vrms`) answers 404. **Longest prefix wins** (`/vmms/analytics/` before `/vmms/`). `/repairs` is gone (version 3): nothing served it.
- **Every connection** to an upstream gives up after 5 s (504).
- **The gateway's own answers.** `GET /health` answers 200 `{ "status": "ok" }` with no upstream running. Any path outside the table answers 404 `NOT_FOUND`. A body over the route's limit answers 413 `PAYLOAD_TOO_LARGE`, the flood limit 429 `RATE_LIMITED`, a service that isn't reachable 502 `UPSTREAM_UNAVAILABLE`, and one past its read timeout 504 `UPSTREAM_TIMEOUT`. Each is JSON in the section 11 shape, carries the CORS headers below and `X-Request-Id`. Right after a service stops, its routes may answer 504 for up to 5 s (the gateway's address cache) before the steady 502. An error a service sends itself passes through untouched.
- **Flood limit:** per client address, 20 a second with bursts of 40 (settings, section 12). Preflights, `/health` and the 404s never count.
- **Headers the gateway sends upstream:** `X-Forwarded-For` as **one value**, the real client (never appended to, so a caller can't plant an address; behind Azure's ingress it is the last entry the ingress appended); `X-Forwarded-Proto`; `X-Request-Id`, kept when the caller's matches `^[A-Za-z0-9._-]{1,64}$`, else a new one, and returned on every answer; `Host` as the upstream's own name. Services keep counting hops with `TRUST_PROXY_HOPS` (1 locally, 2 hosted), which the one value keeps right. Services logging `X-Request-Id` on every line is a follow up of spec 0008, not yet a rule.
- **Headers the gateway owns:** it hides any `Access-Control-*`, `Vary`, `X-Request-Id` or `Strict-Transport-Security` an upstream sends, and sets its own, so a browser sees one of each.
- **CORS:** the gateway answers only the exact web origins of its environment (section 1), listed in its `ALLOWED_ORIGINS` setting; locally the `localhost` ports in section 2. No `*`. A listed origin gets `Access-Control-Allow-Origin` with that origin, `Access-Control-Allow-Credentials: true`, `Vary: Origin` and `Access-Control-Expose-Headers: X-Request-Id, Retry-After`. Its preflight answers 204 with methods `GET, POST, PUT, PATCH, DELETE, OPTIONS`, request headers `Authorization, Content-Type, X-Request-Id, sentry-trace, baggage` (the last two since VRMS spec 0025: Sentry's trace headers, harmless for a system that doesn't read them) and a max age of 600, without reaching the service. An unlisted origin gets no `Access-Control-*` header at all.
- **HSTS:** every answer carries `Strict-Transport-Security` from the `GATEWAY_HSTS` setting when it is set (hosted), and none locally.
- **Health:** every upstream answers `GET <prefix>/health` with 200 `{ "status": "ok", "checks": { ... } }`, or 503 `HEALTH_CHECK_FAILED` with the failed check, needing no token and showing no error text. Each check counts as failed after 2 s. `/auth/health` and `/vrms/health` exist; VMMS and BMS add theirs in S11.
- **Config home:** `infra/gateway/` in the workspace repo builds one image from one template set, the same for every environment; only settings differ (`docker-compose.shared.yml` locally, the hosting settings online). There is no separate local config. `welinc-auth/nginx.conf` is removed.
- A body limit or timeout change for one route is a one line PR to `infra/gateway/` that the owning group opens; it is not a contract change.

### 4. Clients (who may ask welinc-auth for tokens)

welinc-auth keeps a registry of clients, one per environment, set by its seed.

| Client id | Kind | System | Can use | User token audiences | Service token audiences and scopes | Redirect address |
|---|---|---|---|---|---|---|
| `portal` | first party web, no backend | none | SSO cookie routes only (section 7) | none | none | none |
| `vrms` | confidential backend | `VRMS` | authorization code, refresh, client credentials | `VRMS` | `AUTH` (`directory.read`, no phones: spec 0005; `permissions.read`, version 7: its matrix, section 10a); other systems per feature 56 | `<api>/vrms/session/callback` |
| `vmms` | confidential backend | `VMMS` | authorization code, refresh, client credentials | `VMMS` | `AUTH` (`directory.read`, `directory.contact`); other systems per feature 56 | `<api>/vmms/session/callback` |
| `bms` | confidential backend (`bms-gateway`) | `BMS` | authorization code, refresh, client credentials | `BMS` | `AUTH` (`directory.read`, `directory.contact`); `VMMS` (`fleet.read`, version 8: the VMMS fleet API, below); other systems per feature 56 | `<api>/bms/session/callback` |
| `vmms-mobile` | first party native, public (holds no secret) | `VMMS` | mobile login, refresh | `VMMS` (default) and `VRMS` (a refresh with `audience=VRMS`, for the VRMS tab of scope feature 48; Mechanic and Chief Mechanic only, spec 0004) | none | none |
| `bms-mobile` | first party native, public (holds no secret) | `BMS` | mobile login, refresh | `BMS` | none | none |
| `vmms-analytics` | service | `VMMS` | client credentials | none | `AUTH` (`directory.read`) | none |
| `bms-analytics` | service | `BMS` | client credentials | none | `AUTH` (`directory.read`) | none |

- **System** is the system a client acts for. It scopes the directory (section 9) and is the default audience of its user tokens.
- welinc-auth refuses any audience or scope a client's row doesn't list (`invalid_target` or `invalid_scope`, section 11).
- A confidential client registers one or two ES256 public keys as inline JWKs (two during a key change), each with its own `kid`. The keys come from the seed per environment; changing one means running the seed again. welinc-auth never holds a client's private key.
- Redirect addresses match exactly, character for character. No wildcards.
- Each client's registry row also holds its system's web address (section 1), where users land after login.
- **Allowed roles** (spec 0004): a client may limit the roles it serves, per audience, in `allowed_roles` (`{ "<SYSTEM>": ["<role code>", ...] }`). A system left out of it lets every role of that system through. Seeded today: `vmms-mobile` allows Mechanic and Chief Mechanic for both `VMMS` and `VRMS`; `bms-mobile` allows Driver and Helper for `BMS`. Version 8 (spec 0014): the web clients admit office roles only, `vmms` Admin and Operations for `VMMS`, `bms` Admin, Customer Support and Operations for `BMS`; `vrms` names no list. A system's web client and its phone app never admit the same role. Every user grant (code exchange, refresh, mobile login) puts only allowed roles in the token. Someone who holds roles in the audience but none the client allows gets 403 `APP_NOT_ALLOWED` before anything is written; a role change reaches a signed in phone at its next refresh. The portal's password login (`/auth/login`) has no client and is never filtered. The seed is the only writer and refuses a code the catalog doesn't have.
- **App released** (version 8, spec 0014): `oauth_clients.app_released` says whether a phone app has shipped (`vmms-mobile` true, `bms-mobile` false). Set only by the seed, like `allowed_roles`; it feeds `mobileSystems[].app.released` (section 10) and nothing else.
- **Fleet API** (version 8, spec 0014): VMMS serves `GET /vmms/fleet/vehicles`, `GET /vmms/fleet/vehicles/:id` and `GET /vmms/fleet/garages`, read only, to a service token with `aud: VMMS` and `fleet.read` (only `bms` holds it). No token or a bad one: 401; a user token: 403 `WRONG_TOKEN_USE`; a service token without the scope: 403 `FORBIDDEN`. Routes, fields, errors and the caching rule live in [`docs/integration/fleet-api.md`](../../../integration/fleet-api.md); this section holds only the scope.
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
- welinc-auth defines the `directory.read` scope, `directory.contact` (phones in the directory, section 9) and, since version 7, `permissions.read` (the system's own permission matrix, section 10a). Each system defines and documents the scopes for its own service routes (VRMS feature 56 lists the ones between systems).

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
| Reauth token (version 6, spec 0012) | 5 minutes | a random 256 bit value stored only as its SHA-256 hash; bound to the user, its purpose and the session (`sid`) that asked; used once, only for a write of that purpose, only from the same session. Purposes: `ACCOUNT_DELETION` (the deletion request); version 7 adds `ADMIN_ACTION` (adding an admin role, actions on an admin account, every role a suite admin gives, suite admin changes; asked through `POST /auth/profile/verify-password` with an admin's user token, or `POST /auth/admin/verify-password` with the SSO cookie) and `TEMPORARY_ACCESS` (a suite admin's temporary grant, cookie route only). It is not bound to the target person. Anything else answers 403 `REAUTH_REQUIRED` |

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
  "user": {
    "id": "uuid", "name": "…", "email": "…",
    "roles": [{ "role": "ADMIN", "system": "VRMS" }],
    "systems": ["VMMS", "VRMS"],
    "systemRoles": [{ "system": "VMMS", "roles": ["ADMIN"] }, { "system": "VRMS", "roles": ["ADMIN"] }],
    "suiteAdmin": false
  }
}
```

`user.systems` (spec 0007, S4) lists every web openable system the user holds a role in (a phone only system is left out, version 8), in the order BMS, VMMS, VRMS, read fresh at each grant. It decides only whether an app shows Switch system; access is still decided by `roles` and every grant. It is never put in a token. Version 8.2 (VRMS spec 0027): `user.systemRoles` holds one entry per system in `user.systems`, same order, with the live role codes held there, ordered by catalog `sortOrder` then code (a code with no catalog row left out, so `roles` may be empty), and `user.suiteAdmin` says whether the person is a suite admin. Both are read fresh at each grant, never put in a token, and for display only (a system's switcher tags and its Suite management card): a backend never decides access from them. Clients ignore fields in `user` they don't know, so welinc-auth may add more.

The client credentials grant answers `{ access_token, token_type, expires_in, scope }`, with no refresh token. The system backend's own routes (section 7) take `name` and `roles` from this `user` object; tokens never carry a name.

### 6. Sessions

A session (`sid`) starts at login and ends at logout, timeout or revocation. Every token from that login carries its `sid`.

| Kind | Ends after | Enforced by |
|---|---|---|
| Web | 30 minutes without user input in any app on that session, or 12 hours after login | welinc-auth, from activity pings. Each web app, while there is real user input (keys, clicks, touches; background polling doesn't count), calls `POST /<sys>/session/activity` at most once a minute, and its backend passes it to `POST /auth/session/activity`. The portal, which has no backend, calls `POST /auth/session/activity` itself with the SSO cookie (since 2026-11-23, spec 0016). Working in BMS keeps your VRMS tab's session alive, because it is the same `sid`. Logins and code exchanges also count as activity. A web refresh never does, so a tab refreshing in the background still reaches the idle cutoff (spec 0003). |
| Mobile | 7 days without a refresh | welinc-auth; each refresh extends it 7 days. No absolute limit. |

- A user holds at most `MAX_SESSIONS_PER_USER` (10) live sessions. An 11th login ends the one with the oldest activity (`MAX_SESSIONS`).

- The session's expiry, as `/auth/session` and `session_expires_at` report it, is the earlier of the idle cutoff and the absolute cutoff.

- **One web login covers every system.** The portal's SSO cookie means opening a second system needs no password. Each system gets its own refresh token under the same `sid`.
- **Logout anywhere ends the session everywhere.** Logout from VRMS ends the `sid`, so VMMS and BMS lose it at their next session check (30 s at most).
- **What ends a session at once:** logout, the user or an admin ending it, deactivation, deletion, a password change on the profile (every other session of that user), an OTP reset or an admin password set (every session), reuse of an old refresh token or login code, an 11th session, and (version 7) the end of a temporary grant: every live session of its holder that opened the grant's system ends with the reason `TEMP_ACCESS_ENDED`, portal included (section 10a). The automatic lock (5 failed logins) blocks new logins only and ends no live session, so a stranger who knows an email can't sign someone out mid shift (spec 0003).

**Session check** (each system backend, on every request with a user token):

1. Verify the signature, `iss`, `aud` (its own system) and `exp`.
2. Call `GET /auth/session` with the user's token, caching the answer by `sid` for at most 30 s. The check covers the account too (deactivated, locked or deleted ends it).
3. Use `roles` from the token for permission checks (VRMS keeps its CASL matrix on top, spec 0011; since version 7 it reads that matrix from welinc-auth, section 10a). A token's `roles` may hold a temporary grant's role: it is a real role while it lasts, and the session ends when the grant does.

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
   - Valid SSO cookie, live roles in the system, none of them allowed on this client (version 8: a mechanic opening the VMMS web app): no code; redirect to the callback with `error=access_denied`, `error_description=APP_NOT_ALLOWED` and `state`.
   - No valid SSO cookie: store a login request (section 5) and redirect to `<portal>/login?request=<id>`. The portal signs in through `POST /auth/login` (which sets the SSO cookie), then sends the browser to `GET /auth/authorize/resume?request=<id>`, which continues as above. An expired or used request sends the browser to `<portal>/?error=LOGIN_REQUEST_EXPIRED`.
5. `GET /<sys>/session/callback?code&state` on the backend checks `state` against its `<sys>_login` cookie, clears that cookie, and calls `POST /auth/token` (authorization code grant, with the verifier and its client assertion).
6. The backend sets the refresh cookie and redirects to `<system web address><return>`.
7. The web app calls `POST /<sys>/session/refresh` again and now gets the access token, held in memory only.

**Callback failures** never show a raw error. The backend redirects to `<portal>/?error=<code>`: `access_denied` becomes `NO_SYSTEM_ACCESS` (with `&system=<SYS>`); `access_denied` with `error_description=APP_NOT_ALLOWED`, or an exchange answered 403 `APP_NOT_ALLOWED`, becomes `APP_NOT_ALLOWED` with `&system=<SYS>` (version 8; `<SYS>` is the system's own upper case code); a missing, expired or mismatched `<sys>_login` cookie becomes `LOGIN_STATE_INVALID`; a failed exchange becomes `LOGIN_FAILED`. The portal shows a plain message and a button to try again.

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
| `/<sys>/session/refresh` | POST | the `<sys>_rt` cookie | `{ accessToken, expiresIn, sessionExpiresAt, sessionAbsoluteExpiresAt, user: { id, name, email, roles, systems } }` (`systems` passed through; a missing one counts as empty); version 8.2: VRMS also passes `systemRoles` and `suiteAdmin` through, a missing one counting as `[]` and `false` from the `/auth/token` answer (`sessionAbsoluteExpiresAt` is the 12 hour end, so the app can tell it from the idle cutoff; spec 0003 AC-23); rotates the cookie | 401 `SESSION_ENDED`; 403 `APP_NOT_ALLOWED` (version 8: a role change left only phone app roles; the cookie is cleared) |
| `/<sys>/session/activity` | POST | the `<sys>_rt` cookie | 204; passes the ping to `POST /auth/session/activity` | 401 `SESSION_ENDED` |
| `/<sys>/session/logout` | POST | the `<sys>_rt` cookie | 204, clears the cookie, ends the `sid` at welinc-auth (which kills the SSO handle too) | none (always clears) |
| `/<sys>/session/status` | GET | bearer user token | `{ sessionExpiresAt }`, asked fresh at welinc-auth, for the idle warning (spec 0003) | 401, 503 |

**CSRF guard** (stops another page from making calls with your cookie). It applies to every POST route that a cookie authenticates: the system's `refresh`, `activity` and `logout`, and welinc-auth's `/auth/login`, `/auth/logout` and `/auth/session/activity` when called with the SSO cookie, plus (version 7) every `/auth/admin/*` write (`POST`, `PATCH`, `DELETE`). The GET routes a page navigation reaches (`/auth/sso`, `/auth/authorize`, `/auth/authorize/resume`, `/<sys>/session/start`, `/<sys>/session/callback`) change no state a third party can use and skip it, since a navigation sends `Sec-Fetch-Site: none` or `cross-site` (spec 0003).
1. POST only, with `Content-Type: application/json`. A refused request gets 403 `CSRF_REJECTED`.
2. The `Origin` header must equal exactly one allowed web address: the system's own for its routes, the portal's for welinc-auth's. Browsers set this header themselves, so a sibling subdomain can't fake it.
3. `Sec-Fetch-Site` must be `same-origin` or `same-site` when the browser sends it.
4. The gateway's CORS list is the outer layer.

- **Switch system** in every app opens `<portal>/?from=<SYS>` in the same tab and shows when `user.systems` has two or more entries, or when the person is Admin in that system, a temporary grant included (amended 2026-11-14). The launcher tags that system "You're here"; `from` never decides where the browser goes.
- After logout the web app sends the browser to `<portal>/login?reason=logout`. Since the `sid` is gone, the old SSO cookie no longer counts and the portal asks for the password.
- **Where an app may send a person:** only its own `/<sys>/session/start`, `<portal>/login?reason=…`, or `<portal>/?error=<code>`. Never the bare `<portal>/` for a missing session: the portal forwards a one system user straight back to their app, so that would loop.

**The launcher** (spec 0007). The portal picks its screen from the address and welinc-auth's answer, checked in this order:

| Address | Portal does |
|---|---|
| has `reason` (`logout`, `idle`, `maxage`) | the form with its message; never calls `/auth/sso` |
| has `request` (an app initiated login; any `error` ignored) | `/auth/sso` 200: continues at `/auth/authorize/resume` with no form and no launcher; otherwise the form, then resumes |
| neither: `/auth/sso` answers 401 | the form, with the notice for any `error` |
| 200 with one system and no `error` | `location.replace(url)`, no launcher drawn |
| 200 with two or more systems, or with an `error` | the launcher, with the `error` notice above the cards, and (version 8) a quiet line under them naming the phone only systems ("On the mobile app: VMMS"). It never forwards on its own while an `error` is present, so a failing app can't loop |
| `error=APP_NOT_ALLOWED` (version 8) with a live session | "Your role in <System> uses the WeLinc mobile app, not the web" with Back to your systems and Sign out; `<System>` only when `system` matches a code in `/auth/systems`, else "this system" |
| 200 with no systems but `mobileSystems` (version 8: a mechanic, driver or helper) | the phone only state: a card per phone only system with its roles, "<System> is on the WeLinc mobile app" (or "coming to" while `app.released` is false), "Your role doesn't use the web version." and Sign out; no open button |
| 200 with no systems (version 7: a suite admin, who holds no system role) | the no systems screen with the **Admin** entry in the top bar |
| 403 `NO_SYSTEM_ACCESS` | "no access to any WeLinc system" with the email and Sign out |
| 429, 5xx, no network | the launcher's error state with Retry |

After a form sign in with no `request`, the same rules use the login answer (no second `/auth/sso`). Every card address comes from welinc-auth's answer (each system's registered web address), never from the query string. The launcher asks `/auth/sso` again when its tab regains focus, at most every 10 seconds; these calls never count as activity. Sign out on the launcher ends the shared session for every app.
- **The portal** is login, launcher and (version 7) the admin section at `<portal>/admin`. It authenticates with the SSO cookie on `/auth/login`, `/auth/logout`, `/auth/sso`, the authorize routes and `/auth/admin/*` (section 10a), and holds no access token. The launcher top bar shows **Admin** to anyone `GET /auth/admin/me` calls an admin. Profile pages live in each app; account management lives only in the portal admin section, so a system links to `<portal>/admin/people?system=<SYS>` instead of keeping its own users page ([`docs/integration/account-screens.md`](../../../integration/account-screens.md#admin-pages-live-in-the-portal)).

### 8. Mobile login (`vmms-mobile`)

The app keeps its own native screens and talks to welinc-auth directly. The login rules (lockout, OTP, reset, rate limits) still run only on the server.

| Step | Call | Notes |
|---|---|---|
| Log in | `POST /auth/mobile/login` with `{ email, password, clientId: "vmms-mobile", deviceName }` | Answers like the `/auth/token` user grants (section 5), in camel case: `{ accessToken, refreshToken, expiresIn, sid, sessionExpiresAt, user }`, with `aud` set to the client's default system (`VMMS`). No cookie. A user with no role in that system gets 403 `NO_SYSTEM_ACCESS`; one whose roles there aren't allowed on this app (section 4) gets 403 `APP_NOT_ALLOWED`. The password is checked first, so `APP_NOT_ALLOWED` only follows a correct password, and a wrong one still counts toward the lockout. `bms-mobile` logs in the same way, with `clientId: "bms-mobile"` and `aud` `BMS`. |
| Confirm the email (version 4) | `POST /auth/mobile/login` may answer 200 `{ status: "EMAIL_VERIFICATION_REQUIRED", challengeId, email, resendAfter }` instead of tokens | An account whose email isn't verified gets this after the client, password, `NO_SYSTEM_ACCESS` and `APP_NOT_ALLOWED` checks, and a 6 digit code is emailed. No session exists yet. Show a code screen: `POST /auth/mobile/login/verify-email` with `{ challengeId, code, clientId, deviceName }` answers the token body above; `POST /auth/mobile/login/verify-email/resend` with `{ challengeId }` sends a new code on the same ticket and answers `{ resendAfter }`. Errors: 400 `INVALID_CODE` with `attemptsLeft`, 400 `CODE_EXPIRED` (sign in again), 429 `CODE_SEND_LIMIT` with `Retry-After`, 503 `MAIL_FAILED` (spec 0009). Every mobile app must handle this answer: an app that expects tokens can't sign these accounts in. Keep the ticket in memory only. |
| Admin sign in code (version 7) | none on mobile | The reserved `/auth/mobile/login/otp` and `/auth/login/otp` and the `OTP_REQUIRED` status are dropped (nothing served or called them). Admins confirm a portal sign in with `SIGN_IN_CODE_REQUIRED` on `/auth/login` instead (section 10). `/auth/mobile/login` is unchanged: the mobile clients take no admin role (`allowed_roles`, section 4), and every admin route checks the session's code. |
| Refresh | `POST /auth/token` with `grant_type=refresh_token`, `refresh_token`, `client_id=vmms-mobile`, optional `audience` (`VMMS` or `VRMS`) | Rotates the refresh token, with the same 10 s grace for a retry after a lost answer. One mobile session can get an access token for each system the user holds; an audience the user holds no role in gets 403 `NO_SYSTEM_ACCESS`, and one where none of their roles is allowed on the app gets 403 `APP_NOT_ALLOWED`. |
| Log out | `POST /auth/logout` with `{ refreshToken, clientId }` | Ends the `sid`. `clientId` names the public client (`vmms-mobile` or `bms-mobile`), as spec 0003 AC-30 says. |
| Forgot password, OTP, reset | the existing `/auth/forgot-password`, `/auth/verify-otp`, `/auth/reset-password` | Same addresses, bodies and messages (version 4: codes are 6 digits, die after 5 wrong tries, and the routes take 10 calls a minute per address, section 12). Using a code also confirms the email. |

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
| `/auth/directory/users/lookup` | POST | `{ ids: uuid[] }` (1 to 200 distinct uuids; the body holds nothing else) | `{ users: DirectoryUser[], missing: uuid[] }` |
| `/auth/directory/users` | GET | `cursor?`, `limit?` (100, at most 500) | every user who holds a role in the caller's system: `{ users: DirectoryUser[], next, changesCursor }` (for the first sync) |
| `/auth/directory/changes` | GET | `after?` (cursor), `limit?` (100, at most 500) | `{ changes: DirectoryChange[], next, hasMore }` in order |

```ts
type DirectoryUser = {
  id: string;            // uuid, the same as the token's sub
  name: string;
  email: string;
  phone: string | null;   // null unless the token also holds directory.contact
  picture: string | null; // an /uploads address
  isActive: boolean;
  deleted: boolean;       // soft deleted; name and email kept until erased
  erased: boolean;        // version 6: personal data erased; name is "Deleted user", email is deleted-<id>@erased.invalid
  roles: string[];        // roles in the caller's system only
  temporaryRoles: string[]; // version 7: the codes in roles that come from a live temporary grant (section 10a); empty when none
  updatedAt: string;      // ISO 8601
};

type DirectoryChange = {
  cursor: string;         // opaque, store the last one you processed
  type: 'created' | 'updated' | 'roles_changed' | 'activated' | 'deactivated' | 'deleted';
  at: string;
  user: DirectoryUser;    // the state after the change, so no extra lookup is needed
};
```

- **Which users a system sees:** only users who hold, or once held, a role in the caller's system. Lookup returns them with `roles` for that system (empty if they lost it, since a record may point to someone who has since left), in the order the ids were asked. Soft deleted users of the system come back with `deleted: true`. Every other id, unknown or hard deleted, comes back in `missing`, exactly as it was sent. A hard deleted person still has a `deleted` change in the feed.
- **What the feed carries:** every change to a user who holds a role in the caller's system at the time of the change. When a user loses their last role there, the system gets one `roles_changed` with `roles: []`, then no more changes about them until they get a role back (which arrives as `roles_changed`).
- **One change per save:** a save that touches a person (their fields, their roles, or both) gives at most one change for them, carrying their state after the save. A save that changes nothing a system can see gives none: a password change or reset, a lock or unlock, a failed login, or saving the same values.
- **What `type` means:** it compares the person with their previous change across the whole suite, and the first match wins: `created` (no earlier change, so new to the suite, not only to your system), `deleted` (soft deleted, or hard deleted), `deactivated`, `activated`, `roles_changed` (roles in any system), else `updated`. A change reaches every system the person held a role in before or after it, so you may get one with nothing new for you (a role changed in another system). Apply the `user` snapshot every time and treat `type` as information only.
- **`updatedAt`:** information only. The lookup and users routes read the account's current value; the feed carries the value at the person's last visible change, which can be older (a password change moves the column but writes no change). Don't compare it across routes.
- **Where the feed starts:** when the feed is created in an environment (its migration), it records one `created` change for everyone who then holds a role, soft deleted people included. So leaving `after` out gives the whole history, and lookup knows who "once held" a role from day one.
- **Cursors:** a cursor is opaque. It marks a place in the feed's order (the order the changes committed in) and the feed's epoch (an id the auth database gets when the feed is created). The feed serves only changes from transactions older than every transaction still running (the safe point), so a slow transaction that commits late is never skipped, however long it ran. When a page holds fewer than `limit` changes, `next` is the safe point, so asking again from it skips changes for other systems you have already passed. Cursors never expire, so a system that was down catches up from its last one.
- **After a restore:** a database restored from a backup or rebuilt gets a new epoch, and a cursor from before answers 400 `INVALID_CURSOR`. That means "read everything again": drop the cursor, do the first sync again, and apply it as usual (applying is harmless when nothing changed).
- **Paging:** the two kinds of cursor don't mix. `/auth/directory/users` answers a page cursor in `next` (`null` on the last page), only for its own `cursor`. `/auth/directory/changes` answers a feed cursor in `next`, never `null`: on a full page it is the last change's cursor and `hasMore: true` means call again at once; on a short page it is the safe point. An empty `cursor` or `after`, or one kind used for the other, is 400 `INVALID_CURSOR`, not "from the start" (leave the parameter out for that).
- **First sync:** page through `/auth/directory/users`, then start the feed from the `changesCursor` of the first page (only the first; later pages carry their own, ignore them). It is taken before the scan, so nothing that changes during the scan is lost (a change may arrive twice, which is harmless).
- **Who may call:** only a system backend's own service token (`aud: AUTH`) holding `directory.read`. No token, a bad one, or a token from a switched off client gives 401; an expired one gives 401 `TOKEN_EXPIRED` (get a new token and retry once). A person's token, an admin's included, gets 403 `FORBIDDEN`, as do a service token without `directory.read` and a client with no system. A bad cursor gives 400 `INVALID_CURSOR`; a `limit` outside 1 to 500 or a bad lookup body (not 1 to 200 distinct uuids) gives 400 `VALIDATION_FAILED`.
- **Temporary roles (version 7, additive):** a suite admin who gives themselves a role for a few hours (section 10a) shows in your system's feed like anyone else, with that role in `roles` and again in `temporaryRoles`. Snapshots from before version 7 have no flag and read as empty. Skip the codes in `temporaryRoles` wherever a role makes someone pickable for work (VRMS leaves them out of its mechanic roster), so a suite admin looking around is never assigned a job. The grant's end arrives as a `roles_changed`.
- **How systems use it:** keep a local copy of only what you show (name, email, roles, active), keyed by `sub`. Poll the feed every 30 to 60 s from the stored cursor and apply changes in order. Applying the same change twice must be harmless.
- **Reserved for later (not built):** an optional webhook nudge. welinc-auth would POST `{ "type": "directory.changed" }`, with no user data, to an address a system registers, and the system polls the feed at once. Adding it changes nothing above.
- **Lag:** a change usually reaches the feed as soon as it commits. Any long open transaction on the auth database's Postgres server holds the safe point back for every system until it ends, so a feed that stops moving means an open transaction, not lost changes. welinc-auth's database role closes transactions left idle for 60 s (section 15).
- **Erasure (version 6, spec 0012):** `ACCOUNT_ERASURE_GRACE_DAYS` (30 by default) after an account is soft deleted, welinc-auth erases the person's personal data (section 10). The feed then carries one more change for them: type `updated`, with `erased: true` and the erased name, email, phone and picture. There is no new change type, so check the flag, not `type`. The flag is also true in a full read from `/auth/directory/users` and the lookup. When you see `erased: true`, replace every copy of that person's name, email, phone and picture you keep with the values in the snapshot (`Deleted user`, no email), or with nothing, including copies in your own logs and history. Free text that people typed stays as written. A person who is only a record in your system is never deleted from it: keep keying on `sub`.
- **Retention:** the feed keeps every change forever, behind these routes only. Version 6 rewrites a person's earlier snapshots at erasure (name, email, phone and picture get the erased values), so the feed never serves an erased person's personal data again, from the first sync or the changes. The feed still holds one row per change, and the rewrite adds one `updated` row (the erasure).
- No system reads the auth database. Security never rides on the feed: deactivation is caught by the session check (section 6).

### 10. welinc-auth routes for people

Existing routes stay unless marked. "System" means the token's `aud`; the old `?system=` parameter and the `Origin`, `Referer` and path guessing are removed. The portal's admin routes are in section 10a.

**Deprecated (version 7):** every route below whose "Who" is "that system's admin" still works for system admins, unchanged apart from the version 7 rules in the last rows, but the portal admin section (section 10a) replaces it. Don't build new screens on them. Spec 0014 removes them in its last slice, once VMMS and BMS have moved and nothing calls them (version 9).

| Route | Method | Who | Status | Row |
|---|---|---|---|---|
| `/auth/.well-known/jwks.json` | GET | anyone | new | S2 |
| `/auth/.well-known/oauth-authorization-server` | GET | anyone; issuer and endpoint addresses (RFC 8414) | new | S2 |
| `/auth/authorize`, `/auth/authorize/resume` | GET | browser | new | S3 |
| `/auth/token` | POST | clients | new | S2, S3, S4 |
| `/auth/login` | POST | portal only: `{ email, password }` (`system` is gone; sending it gets 400). Sets the SSO cookie, no token in the body. Answers the same body as `/auth/sso`. No usable system means 403 `NO_SYSTEM_ACCESS` with `user: { email }` (your own) and no session is created. Version 4: an account whose email isn't verified gets 200 `{ status: "EMAIL_VERIFICATION_REQUIRED", challengeId, email, resendAfter }` with `Cache-Control: no-store`, no session and no cookie, last of all (after `NO_SYSTEM_ACCESS`), and a code is emailed; 429 `CODE_SEND_LIMIT` or 503 `MAIL_FAILED` when no code can go out. Version 7: a verified, active admin (a suite admin, or anyone holding an `isSystemAdmin` role) with the right password gets 200 `{ status: "SIGN_IN_CODE_REQUIRED", challengeId, email, resendAfter }`, the same body with a new status, also with no session and no cookie; an unverified admin gets only `EMAIL_VERIFICATION_REQUIRED` (one code covers both). Both finish through `/auth/login/verify-email`. A suite admin holds no system, so their launcher answer is a 200 with an empty `systems` list, never `NO_SYSTEM_ACCESS`. With `ADMIN_SIGN_IN_CODE` off (local only) no code is asked. Version 8: the answer carries `mobileSystems` (as `/auth/sso`), and a person whose roles pass only a phone app gets 200 with `systems: []`, not 403 | changed | S2, S3, S4, S13, S10, S11 |
| `/auth/login/verify-email` | POST | portal only (`PortalCsrfGuard`): `{ challengeId, code }`. A right code confirms the email and finishes exactly like `/auth/login` (SSO cookie, launcher body). Version 7: it also finishes the `SIGN_IN_CODE_REQUIRED` step, and the session any code step creates counts as having passed the admin code (section 10a). 400 `INVALID_CODE` with `attemptsLeft`, 400 `CODE_EXPIRED`, 403 `ACCOUNT_LOCKED` or `NO_SYSTEM_ACCESS`, 401 for an inactive account (version 10: 403 `ACCOUNT_INACTIVE`) | new | S13, S10 |
| `/auth/login/verify-email/resend` | POST | portal only (`PortalCsrfGuard`): `{ challengeId }`. A new code on the same ticket; `{ resendAfter }`. 400 `CODE_EXPIRED`, 429 `CODE_SEND_LIMIT` with `Retry-After`, 503 `MAIL_FAILED` | new | S13 |
| `/auth/login/otp` | POST | portal | removed (version 7): it was reserved and never built; the admin code is `SIGN_IN_CODE_REQUIRED` on `/auth/login` | S10 |
| `/auth/mobile/login` | POST | `vmms-mobile`, `bms-mobile` (tokens in the body, section 8) | new; version 4 adds the email step answer. The reserved `/auth/mobile/login/otp` is removed (version 7, never built) | S3, S13, S10 |
| `/auth/mobile/login/verify-email`, `/auth/mobile/login/verify-email/resend` | POST | `vmms-mobile`, `bms-mobile` (section 8) | new | S13 |
| `/auth/logout` | POST | SSO cookie, a client with assertion and refresh token, or `vmms-mobile` with refresh token | new | S3 |
| `/auth/sso` | GET | SSO cookie (portal) | new: `{ user: { id, name, email, picture }, systems: [{ system, name, description, url, roles: [{ code, name }] }] }` with `Cache-Control: no-store`. `systems` in the order BMS, VMMS, VRMS, each with your roles in catalog order; `url` is the web address of the system's active confidential client, and a system without one is left out. `picture` is the stored `/uploads/...` path or null. 401 `SESSION_ENDED` without a live session; 403 `NO_SYSTEM_ACCESS` with `user: { email }` (your own) when no usable system is left. Version 7: a suite admin gets 200 with `systems: []` instead. Version 8: a held system is in `systems` only when one of your live roles passes its web client's `allowed_roles`; otherwise it is in `mobileSystems: [{ system, name, description, roles, app: { clientId, released } }]` when a role passes an active phone app of that system, else left out. Both lists keep launcher order and are always present. 403 `NO_SYSTEM_ACCESS` only when both are empty and you are not a suite admin. `user.systems` in every grant answer lists `systems` only, so Switch system never offers a phone only system. Additive (2026-11-23, spec 0016): `sessionExpiresAt` (the earlier of the idle and the 12 hour cutoff), `sessionAbsoluteExpiresAt` (the 12 hour cutoff) and `serverTime` (the server's clock when it answered), ISO times, required on every launcher answer (`/auth/sso`, `/auth/login`, `/auth/login/verify-email`), a suite admin's included. Clients ignore unknown fields (version 2), so no version bump. Additive (2026-11-24, spec 0019): `suiteAdmin` (boolean, required) on every launcher answer, true when you are a suite admin, whatever roles you hold. Never counts as activity | S3, S4, S10, S11, S18 |
| `/auth/session` | GET | user token | new: `{ active: true, sid, expiresAt, user: { id, name, email } }` (`expiresAt` is the earlier of the idle and absolute cutoffs; systems take the caller's name from `user`) or 401 with `SESSION_ENDED`, `ACCOUNT_INACTIVE` or `TOKEN_EXPIRED`. A locked account's live session still answers 200 | S3 |
| `/auth/session/activity` | POST | a confidential client with its assertion and the user's refresh token, or the SSO cookie | new: 204, marks the `sid` active | S3 |
| `/auth/systems` | GET | anyone, no token | new: `{ systems: [{ code, name, description, webAddress, maxRolesPerUser, roles: [{ code, name, description, isSystemAdmin, builtIn }] }] }`, systems in `SystemType` order, roles in display order (also power order, most powerful first). Version 8.1 (suite spec 0018): `builtIn` is false for a custom role; built in roles come first in catalog order, then live custom roles by name; archived roles never appear. `description` is the system's one line launcher text from its catalog file (S4); `webAddress` is the web address of the system's active confidential client, or `null`; `maxRolesPerUser` is a whole number or `null` (no limit). Sends `Cache-Control: no-cache` (version 8.1; was `public, max-age=60`) and an `ETag`, and answers 304 to a matching `If-None-Match`, so each read revalidates cheaply and a new, renamed or deleted role shows on the next read. Reached through the gateway's existing `/auth` route, with its CORS list and rate limit, so browsers may call it. No user data and no permissions (version 7: a system reads its permission matrix from `GET /auth/permissions/:system` instead, section 10a) | S5 |
| `/auth/me` | GET | user token | changed: `roles` holds the account's roles in the token's `aud` only, not narrowed by the client's `allowed_roles` (the token's `roles` claim is). This narrows what the route returns; its only caller is VRMS, with VRMS tokens, so nothing it sees changes. A `?system=` that differs from `aud` answers 403 `WRONG_AUDIENCE`. Version 4 adds `passwordSet` and `pendingEmail` (the address of a change waiting for its code, or null) beside `emailVerified` | S5, S13 |
| `/auth/me/sessions` | GET | user token | new: `{ sessions: SessionView[] }` (spec 0003: `sid`, kind, device, client, systems, created, last active, `current`) | S3 |
| `/auth/me/sessions/:sid` | DELETE | user token | new: end one of your sessions | S3 |
| `/auth/forgot-password`, `/auth/verify-otp`, `/auth/reset-password` | POST | anyone | kept, same bodies and messages. Version 4: one hashed code per family, 6 digits, dead after 5 wrong tries (`verify-otp` counts tries but never uses the code up), 60 s between sends and 5 an hour; `forgot-password` sends a setup code while setup is pending, else a reset code, and stays generic to the public, but an admin of one of the user's systems gets 429 `CODE_SEND_LIMIT` or 503 `MAIL_FAILED`; using a code also sets `emailVerified` and `passwordSet` | S13 |
| `/auth/profile`, `/auth/profile/password`, `/auth/profile/picture`, `/auth/profile/summary` | PATCH, POST, GET | user token | kept. Version 4: `PATCH /auth/profile` no longer takes `email` (400). Version 6: a wrong current password on `PATCH /auth/profile/password` answers 400 `WRONG_PASSWORD` with `attemptsLeft` instead of a bare 400, and counts toward the same lockout as sign in (the 5th wrong one in a row answers 403 `ACCOUNT_LOCKED`). A change to `contact` is logged as `UPDATED` with `field: contact` | S13, S8 |
| `/auth/profile/email` | POST | user token: `{ newEmail, currentPassword }` | new: emails a code to the new address and a notice to the old one; your email stays until the code is used. The same pending address again resends the code. `{ pendingEmail, expiresAt, resendAfter }`. version 6: a wrong password is 400 `WRONG_PASSWORD` with `attemptsLeft` (it was a bare 400) and the 5th wrong one in a row locks the account (403 `ACCOUNT_LOCKED`), 400 `SAME_EMAIL`, 400 for a domain that can't receive mail, 409 `EMAIL_TAKEN`, 429 `CODE_SEND_LIMIT`, 503 `MAIL_FAILED` | S13 |
| `/auth/profile/email/verify` | POST | user token: `{ code }` | new: the right code makes the pending address your email and confirms it, and the old address is told; answers the profile body. Sessions stay. 400 `INVALID_CODE` with `attemptsLeft`, 400 `CODE_EXPIRED`, 409 `EMAIL_TAKEN` | S13 |
| `/auth/profile/email` | DELETE | user token | new: drops a pending change, 204 also when there is none | S13 |
| `/auth/profile/activity` | GET | user token | new (version 5): your own account events from every system (sign ins and refusals, lockouts, systems opened, sign outs and session ends, emailed codes, account changes), newest first. `cursor?`, `limit?` (1 to 100, default 50), `category?` (comma list). `{ data: EventView[], nextCursor }`; the actor is only `{ kind: SELF \| ADMIN \| SYSTEM }`, never the admin's name. `EventView` is `{ id, category, type, reason, system, sessionId, client, field, oldValue, newValue, attemptsLeft, address, localNetwork, device, userAgent, country, network, createdAt, actor }` (spec 0011) | S7 |
| `/auth/profile/verify-password` | POST | user token | new (version 6): `{ password, purpose: "ACCOUNT_DELETION" }` answers 200 `{ reauthToken, expiresAt }` (section 5: 5 minutes, once, same session). Version 7 also takes `purpose: "ADMIN_ACTION"` from an admin's token (403 `NOT_AN_ADMIN` otherwise), for the admin writes in the last rows. Any other `purpose` is 400 `VALIDATION_FAILED`. A wrong password is 400 `WRONG_PASSWORD` with `attemptsLeft`; the same counter as sign in, so the 5th wrong one in a row locks the account (403 `ACCOUNT_LOCKED`); a locked account gets 403 `ACCOUNT_LOCKED` (with the `code`, as on every user route) even with the right password, and no password is tried. A lock ends no session: refresh and `GET /auth/session` still answer, but the access token is refused on the other user routes until the lock runs out (version 10: 15 minutes) or an admin unlocks. 429 `RATE_LIMITED` past 10 a minute | S8 |
| `/auth/profile/deletion-request` | POST | user token | new (version 6): `{ reauthToken, reason? }` (reason up to 500 characters) answers 201 `DeletionRequestView` with `status: "PENDING"`. The person, and the admins of every system the person holds, are emailed. 403 `REAUTH_REQUIRED`, 409 `DELETION_PENDING`, 409 `LAST_ADMIN` (naming the system; a refused request does not use up the reauth token). Version 7: 409 `IS_SUITE_ADMIN` for a suite admin, checked before the reauth token is used | S8, S10 |
| `/auth/profile/deletion-request` | GET, DELETE | user token | new (version 6): GET answers `{ request: DeletionRequestView \| null }`, the person's latest request. DELETE cancels a pending one and answers 204, also when none is pending. The account works as usual while a request is pending | S8 |
| `/auth/users`, `/auth/users/lookup`, `/auth/users/:id`, `/auth/users/:id/status`, `/auth/users/:id/unlock` | as today | that system's admin | kept, with the spec 0011 scoping. Changed by S13 (version 4): admins can't set passwords. `PATCH /auth/users/:id/password` is removed (404) and `password` on create or edit answers 400; a new user always gets a setup code. Every answer carries `passwordSet`. A new email on `PATCH /auth/users/:id` sets `emailVerified` false (confirmed at the next sign in), tells the old address, sends a new setup code while setup is pending (`setupEmailSent`), and answers 409 `SELF_EMAIL` for your own email and 409 `EMAIL_TAKEN` for an address another account holds. Changed by S5: a role in `roleAssignments` must be one of the system's catalog roles (400 `UNKNOWN_ROLE`, naming its roles) and an account may hold at most `maxRolesPerUser` roles in one system (409 `ROLE_LIMIT`; a request is refused, never trimmed). `GET /auth/users` takes an optional `role` filter, checked the same way against the token's `aud`. Changed by S6 (version 2): admins only. A service token, with `directory.read` or not, gets 403 `WRONG_TOKEN_USE`; systems read people through the directory (section 9). Version 5: `/auth/users/:id/changes` is removed (404); the same history is in `/auth/users/:id/activity` (`category=ACCOUNT`). Version 8: `/auth/users/lookup` counts against the limit in section 12, shared with `/auth/admin/users/lookup` | S5, S6, S7 |
| `/auth/users/:id/sessions` | GET, DELETE | that system's admin | new: list or end all of a user's sessions | S3 |
| `/auth/users/:id/activity` | GET | that system's admin | new (version 5): one person's events tagged with the token's `aud` or account wide; 404 unless they hold a role in `aud` now. `cursor?`, `limit?`, `category?`, `type?` (comma lists), `from?`, `to?` (`YYYY-MM-DD`, Asia/Manila days, inclusive). The actor carries `id` and `name`; `client` only on rows tagged with your system | S7 |
| `/auth/activity` | GET | that system's admin | new (version 5): the system's feed: events tagged with `aud` for anyone (former members too), plus account wide events of people who hold a role in `aud` now. The filters above plus `userId`, `q` (2 or more characters of name or email) and `address` (exact). Each event adds `user: { id, name, email }`. A `userId` outside your scope gives an empty page | S7 |
| `/auth/activity/catalog` | GET | anyone | new (version 5): `{ categories, types, reasons }` with English labels (`labelAdmin` for the person's own view of an admin's action), `Cache-Control: public, max-age=300` and an `ETag` (304 on a match) | S7 |
| `/auth/deletion-requests` | GET | that system's admin | new (version 6): `?view=pending\|grace`, `cursor?`, `limit?` (1 to 100, default 50); `{ data, nextCursor }`. `pending`: pending requests of people who hold a role in `aud` now, oldest first. `grace`: soft deleted, not yet erased accounts holding a role in `aud` (approved requests and admin deletes), soonest erasure first, each `{ user, deletedAt, eraseAfter, requestId }` (`requestId` null for an admin delete). 400 `VALIDATION_FAILED`, 400 `INVALID_CURSOR` (a cursor from the other view) | S8 |
| `/auth/deletion-requests/:id/approve` | POST | that system's admin | new (version 6): soft deletes the account at once (deleted, inactive, every session ended, the directory says `deleted`), and closes the request `APPROVED`. The admin of `aud` decides for the whole account, even when the person also holds roles in other systems; the other admins of the person's systems are emailed. 409 `NOT_PENDING`, 409 `LAST_ADMIN`, 403 `SELF_DECISION`, 404 when the person holds no role in `aud` | S8 |
| `/auth/deletion-requests/:id/reject` | POST | that system's admin | new (version 6): `{ note }` (1 to 500 characters, else 400 `VALIDATION_FAILED`); the person is emailed the note and sees it in `GET /auth/profile/deletion-request`. 409 `NOT_PENDING`, 403 `SELF_DECISION`, 404 | S8 |
| `/auth/users/:id/restore` | POST | that system's admin | new (version 6): brings back an account in its grace period: `deletedAt` cleared, still inactive, roles kept, the person emailed; answers the user body of `/auth/users/:id`. 409 `NOT_RESTORABLE` (not deleted, or already erased), 404 | S8 |
| every "that system's admin" route above | | that system's admin | changed (version 7, deprecated): 403 `ADMIN_CODE_REQUIRED` while the token's session (`sid`) hasn't passed the admin sign in code (a session from before version 7, or someone made admin mid session; the step up is in the portal and works at once for tokens already issued). 409 `SUITE_ADMIN_NO_ROLES` on any write that would give a suite admin a permanent role. 409 `IS_SUITE_ADMIN` on deactivating or deleting a suite admin. 409 `TEMPORARY_ROLE` on a roles edit that touches a temporary grant's role (end the grant instead). `reauthToken` (purpose `ADMIN_ACTION`) in the body, else 403 `REAUTH_REQUIRED`, when adding an `isSystemAdmin` role (create, `attachExisting`, roles edit) and, when the target is an admin, on an email edit, a reset or setup code, unlock and ending their sessions; a suite admin's email changes only through their own profile (403 `SUITE_ADMIN_SELF_ONLY`). User items carry `temporaryUntil` (ISO 8601 or null). Each admin level change emails the admins concerned (section 10a) | S10 |

- VMMS's `me/login-activity` maps to `/auth/profile/activity`, its `users/:id/login-activity` to `/auth/users/:id/activity`, and its `audit-logs` for accounts to `/auth/activity`. BMS's `profile/activity` maps to `/auth/profile/activity` and its activity log page to `/auth/activity`. Field by field: [`docs/integration/account-screens.md`](../../../integration/account-screens.md#activity).
- Account activity (version 5, spec 0011) is append only. Sign in, session and code events are kept `ACCOUNT_EVENT_RETENTION_DAYS` (365 by default); account changes are kept for good. A service token on any activity route gets 403 `WRONG_TOKEN_USE`: systems never read this log. Places (`country`, `network`) come from DB-IP Lite and must be credited "IP data by DB-IP" wherever they show (CC BY 4.0).
- welinc-auth stores the phone as a plain contact field (`contact`); no system verifies it and nothing sends SMS (version 6: the phone routes and `phoneVerified` are removed, VMMS dropped SMS). VMMS's Semaphore code and phone verification go away in S11.
- `DeletionRequestView` (version 6) is `{ id, status, reason, requestedAt, decidedAt, decisionNote, eraseAfter, user? }`; `status` is `PENDING`, `CANCELLED`, `REJECTED`, `APPROVED`, `RESTORED` or `ERASED`; `user: { id, name, email, systems }` only on admin routes. `GET /auth/users` items carry `pendingDeletion: boolean`. A service token gets 403 `WRONG_TOKEN_USE` on every route in this group. After a cancel or a reject the person may ask again at once. An admin delete (`DELETE /auth/users/:id`) keeps its checks, starts the same grace period, and closes a pending request as `APPROVED`. Field by field for BMS and VMMS: [`docs/integration/account-screens.md`](../../../integration/account-screens.md#account-deletion).
- **Erasure (version 6, spec 0012):** every soft deleted account, requested or not, is erased `ACCOUNT_ERASURE_GRACE_DAYS` (30 by default, 1 to 365) after `deletedAt`, by the hourly sweep. The person becomes `Deleted user` with the email `deleted-<id>@erased.invalid`, no phone and no picture, an unusable password, and can never sign in, be restored or be erased again. Their sessions lose their address and device, their codes and tokens are deleted, and the personal fields of their account events and earlier directory snapshots are blanked (the rows stay). The old address is free to use for a new account, with a new id. An erased account never shows in `GET /auth/users`, lookups or another person's activity. Roles are kept, so history still joins. Every request, decision, restore and erasure is in the account events (types `DELETION_REQUESTED`, `DELETION_CANCELLED`, `DELETION_REJECTED`, `RESTORED`, `ERASED` in the category `ACCOUNT`; an approval or an admin delete writes `DELETED` with reason `DELETION_REQUEST`; password rechecks write `PASSWORD_CONFIRMED` and `PASSWORD_CONFIRM_FAILED` in `SIGN_IN` with the reason `ACCOUNT_DELETION`, `EMAIL_CHANGE` or `PASSWORD_CHANGE`), all in the catalog with labels. The Philippine Data Privacy Act of 2012 is the reason for it.
- "That system's admin" means the holder of the role its catalog marks `isSystemAdmin` (S5), checked against the token's `aud` on every request. Today that is `ADMIN` in every system. A service token is never a system admin, and no route in this table takes one; system backends use the directory routes of section 9.
- S10 (suite admin, version 7) added the section 10a routes and changed no token claim. A suite admin is not "that system's admin": they hold no permanent system role and work through section 10a. Only while a temporary grant gives them a system's admin role does their token for that system pass the bearer admin routes, like any admin's.

### 10a. Portal admin and permissions (version 7, spec 0013)

**Who is an admin.** A **suite admin** is one of 1 to 3 people in welinc-auth's `suite_admins` list. They manage every account and every system's roles but hold no permanent system role, so they see no system's data. A **system admin** holds a role its catalog marks `isSystemAdmin` and manages only their own system's people (the spec 0011 scope rules). People with both jobs use two accounts.

**How the routes authenticate.** Every `/auth/admin/*` route reads the `welinc_sso` cookie (the live web session it points to), never a bearer token, so only the portal calls them; every write runs the section 7 CSRF guard, and every answer is `Cache-Control: no-store`. No cookie or an ended session answers 401 `NOT_SIGNED_IN`; a person who is neither kind of admin gets 403 `NOT_AN_ADMIN` everywhere but `GET me`. Every route except `GET me`, `GET summary`, `POST code` and `POST code/verify` also needs a session that passed the admin sign in code (403 `ADMIN_CODE_REQUIRED`). Admin standing counts permanent roles only: a temporary grant works inside that system's app, not here.

**The admin sign in code.** An admin's `/auth/login` answers `SIGN_IN_CODE_REQUIRED` (section 10), and finishing it marks the session. A session that missed it (made admin mid session, or from before version 7) steps up through `POST /auth/admin/code`, then `POST /auth/admin/code/verify`. The mark is read from the session row on every request, so it covers tokens already issued for that session too, on the deprecated bearer admin routes as well. The code's lifetime, tries and send limits are spec 0009's. `ADMIN_SIGN_IN_CODE=false` (local only, refused in production) turns the step off: `codeRequired` is then false.

**Who acts where.** The account routes take `system` (query or body). A system admin must pass a system they are admin of (403 `NOT_ADMIN_OF_SYSTEM`) and gets exactly the deprecated bearer routes' rules for it. A suite admin may pass any system, or none on the list, person page, activity, delete, restore and deletion requests (then every person, people with no role anywhere included; items carry every system's `roles` and no `otherSystems`). **Read scope (amended 2026-11-23, suite spec 0017 AC-19, additive):** on the three reads (`GET /auth/admin/users`, `/auth/admin/users/:id`, `/auth/admin/users/:id/activity`) any admin may leave `system` out, meaning every system they admin, read at request time (a suite admin: the whole suite, as above, even when they also hold admin roles). A system admin then gets only people holding a role in one of their systems (anyone else is 404, a soft deleted person too), each with every role in every system and an empty `otherSystems`; the activity covers events tagged with one of their systems plus account wide events, with the login client on rows of any of their systems. Passing `system` behaves as before. Every other account route still needs `system` from a system admin (400 `VALIDATION_FAILED` when missing), and every write names one system. On top of that a suite admin may delete and restore a shared account and decide any deletion request; each system's last active admin rule still holds.

**Rechecks.** A write that needs one takes `reauthToken` from `POST /auth/admin/verify-password` (section 5), else 403 `REAUTH_REQUIRED`: `ADMIN_ACTION` for suite admin changes, adding any `isSystemAdmin` role, actions on an admin account (email edit, reset or setup code, unlock, ending sessions) and every role a suite admin gives or account a suite admin creates; `TEMPORARY_ACCESS` for a temporary grant. welinc-auth alone decides when a write needs it, so a client retries once with the password on that answer.

| Route | Method | Who | In | Out | Errors |
|---|---|---|---|---|---|
| `/auth/admin/me` | GET | anyone signed in | | `{ user: { id, name, email, picture }, suiteAdmin, adminOf: SystemType[], codeRequired, codePassed, temporaryGrants, pendingDeletionRequests }` (`temporaryGrants`: the caller's own live grants, empty unless a suite admin; `pendingDeletionRequests`: pending deletion requests the caller can act on, every one for a suite admin, their systems' for a system admin, 0 otherwise, VRMS spec 0027 AC-12) | 401 `NOT_SIGNED_IN` |
| `/auth/admin/code` | POST | admin | | `{ challengeId, email, resendAfter }`, or 200 `{ passed: true }` and no email when already passed | 409 `CODE_NOT_REQUIRED`, 429 `CODE_SEND_LIMIT`, 503 `MAIL_FAILED` |
| `/auth/admin/code/verify` | POST | admin | `{ challengeId, code }` | 204 | 400 `INVALID_CODE` with `attemptsLeft`, 400 `CODE_EXPIRED`, 409 `CODE_NOT_REQUIRED` |
| `/auth/admin/verify-password` | POST | admin | `{ password, purpose }` (`ADMIN_ACTION` or `TEMPORARY_ACCESS`) | `{ reauthToken, expiresAt }` | 400 `WRONG_PASSWORD` with `attemptsLeft`, 403 `ACCOUNT_LOCKED`, 403 `NOT_SUITE_ADMIN` (`TEMPORARY_ACCESS`), 429 `RATE_LIMITED` |
| `/auth/admin/users` | GET | admin of `system`, or any admin with no `system` (their systems), or suite | `system?`, `q?` (name, email, or a role's display name in the systems in scope), `status?` (`ACTIVE`, `INACTIVE`, `LOCKED`, `SETUP_PENDING`, `EMAIL_NOT_VERIFIED`, `PENDING_DELETION`; one, or a comma list read as any of), `group?` (`attention`: an active account that is locked, setup pending or pending deletion; `inactive`: deactivated; `active`: everyone else), `sort?` (`name`, default: `name ASC, id ASC`; `lastSignedIn`: `lastSignedInAt DESC NULLS LAST, id ASC`; `newest`: `createdAt DESC, id ASC`), `role?` (needs `system`), `cursor?`, `limit?` (1 to 100, default 50); additive (2026-11-25, spec 0019): `access?` (a comma list of `SYSTEM` or `SYSTEM:ROLE`, any of, at most 40 items and 600 characters, normalized: duplicates go, a whole system absorbs its roles, sorted; never with `role`; with `system`, only that system), and `status` also takes `ATTENTION` and `ACTIVE_GROUP` (exactly the `attention` and `active` groups) | people in the sort's order (keyset paged; a cursor carries its sort and filters), each with `roles` (each with `temporaryUntil`, ISO or null), `otherSystems`, `temporaryUntil`, `pendingDeletion`, `suiteAdmin`, `passwordSet`, `emailVerified`, `lastSignedInAt` (ISO or null), `createdAt`; `next`; and with `group`, `counts: { attention, active, inactive }` under the same filters | 403 `NOT_ADMIN_OF_SYSTEM`, 400 `VALIDATION_FAILED`, `INVALID_CURSOR` (also a cursor reused with another sort or filter), `UNKNOWN_ROLE` |
| `/auth/admin/users/facets` | GET | as the list (additive, 2026-11-25, spec 0019) | `system?`, `q?`, `status?`, `access?`, as the list; no group, sort or paging | `{ total, status: { ATTENTION, LOCKED, SETUP_PENDING, ACTIVE_GROUP, INACTIVE }, systems: [{ system, count, roles: [{ code, count }] }] }`, distinct people, no names: `total` under every filter; status counts ignore `status`, system and role counts ignore `access`; `systems` only those in scope, VRMS, VMMS, BMS, roles in catalog order, zeros included | as the list's filter errors, 429 `RATE_LIMITED` |
| `/auth/admin/users/lookup` | GET | admin of `system` | `system`, `q` (2 or more characters) | as the bearer lookup | 403 `NOT_ADMIN_OF_SYSTEM` |
| `/auth/admin/users/email-check` | GET | admin of `system` (additive, 2026-11-24, spec 0019) | `system`, `email` (one whole email, trimmed and lowercased; never a partial match) | `{ status, name?, picture?, systems? }`: `status` is the first that applies of `inactive` (deactivated or deleted), `suite-admin` (suite admins only see this; a system admin gets `existing` with `systems: []`), `in-system` (holds a role in `system`), `existing`, `free`; `name`, `picture` and `systems` (only the systems you admin) with `existing` and `in-system` | 400 `VALIDATION_FAILED`, 403 `NOT_ADMIN_OF_SYSTEM`, 429 `RATE_LIMITED` |
| `/auth/admin/users/:id` | GET | admin of `system`, or any admin with no `system` (their systems), or suite | `system?` | one person, as a list item, plus `deletedAt`, `addedBy` (`{ id, name }`, null when the person made it, nobody is known or the creator is erased), `failedSignIns30d` (`SIGN_IN_FAILED` and `LOCKED_OUT` in the last 30 days, every system), `sessionCount` (live sessions), `setupCodeExpiresAt` (the newest unused setup code's expiry, even when past, else null), `restorableUntil` (`deletedAt` plus the erasure grace period, else null) | 404 |
| `/auth/admin/users` | POST | admin of `system` | `system`, the bearer create body (`name`, `email`, `roleAssignments`, `attachExisting?`), `reauthToken?`; additive (2026-11-24, spec 0019): `contact?` (up to 100 characters, kept on a new account only) | the user | 409 `ACCOUNT_EXISTS`, `SUITE_ADMIN_NO_ROLES`, `ROLE_LIMIT`; 403 `REAUTH_REQUIRED` |
| `/auth/admin/users/:id` | PATCH | admin of `system` | `system`, the bearer edit body (name, email, roles, active), `reauthToken?` | the user | 409 `SELF_ROLE`, `LAST_ADMIN`, `TEMPORARY_ROLE`, `SUITE_ADMIN_NO_ROLES`, `EMAIL_TAKEN`; 403 `REAUTH_REQUIRED`, `SUITE_ADMIN_SELF_ONLY` |
| `/auth/admin/users/:id/status` | PATCH | admin of `system` | `system`, `isActive` | the user | 409 `LAST_ADMIN`, `IS_SUITE_ADMIN` |
| `/auth/admin/users/:id/unlock` | PATCH | admin of `system` | `system`, `reauthToken?` | the user | 403 `REAUTH_REQUIRED`, 404 |
| `/auth/admin/users/:id/reset-code` | POST | admin of `system` | `system`, `reauthToken?` | 204 (a setup code while setup is pending, else a reset code) | 403 `REAUTH_REQUIRED`, 429 `CODE_SEND_LIMIT`, 503 `MAIL_FAILED` |
| `/auth/admin/users/:id/sessions` | GET, DELETE | admin of `system` | `system` (query on GET, body with `reauthToken?` on DELETE) | `{ sessions }` / 204 | 403 `REAUTH_REQUIRED`, 404 |
| `/auth/admin/users/:id/activity` | GET | admin of `system`, or any admin with no `system` (their systems), or suite | `system?`, the section 10 activity filters | one person's events (a suite admin with no `system` sees them all; another admin with no `system`, those of their systems plus account wide) | 404 |
| `/auth/admin/users/:id` | DELETE | admin of `system`, or suite | `system?` | 204 | 403 for a shared account (system admins only), 409 `LAST_ADMIN`, `IS_SUITE_ADMIN` |
| `/auth/admin/users/:id/restore` | POST | admin of `system`, or suite | `system?` | the user | 409 `NOT_RESTORABLE` |
| `/auth/admin/activity` | GET | admin of `system`, or suite (no `system`: every person, former members included) | `system?`, the `/auth/activity` filters | events | 429 `RATE_LIMITED` |
| `/auth/admin/deletion-requests` | GET | admin of `system`, or suite | `view` (`pending`, `grace`), `system?`, `cursor?`, `limit?` | as `/auth/deletion-requests`; with no `system`, every request, each with `orphan` (no other active admin of any system the person holds, or no role now), orphans first | 400 `VALIDATION_FAILED`, `INVALID_CURSOR` |
| `/auth/admin/deletion-requests/:id/approve`, `/reject` | POST | admin of `system`, or suite | `system?`; `note` on reject | the request | 409 `NOT_PENDING`, `LAST_ADMIN`; 403 `SELF_DECISION` |
| `/auth/admin/suite-admins` | GET | suite | | `{ items: [{ id, name, email, grantedAt, grantedBy, reason }] }` (`grantedBy` `{ id, name }`, or null for the seed and the recovery script) | 403 `NOT_SUITE_ADMIN` |
| `/auth/admin/suite-admins` | POST | suite | `{ userId, reason, reauthToken }` (reason 10 to 500 characters) | the new row | 409 `SUITE_ADMIN_LIMIT` (3 exist), `ALREADY_SUITE_ADMIN`, `HOLDS_SYSTEM_ROLES`, `NOT_ELIGIBLE` (inactive, deleted, locked or email not verified); 404; 403 `REAUTH_REQUIRED` |
| `/auth/admin/suite-admins/:userId/remove` | POST | suite | `{ reason, reauthToken }` | 204; ends that person's live grants | 409 `SELF_ROLE`, `LAST_SUITE_ADMIN`; 403 `REAUTH_REQUIRED` |
| `/auth/admin/temporary-grants` | GET | suite (every system) or system admin (theirs) | `state` (`live`, `all`), `system?`, `cursor?`, `limit?` | grants, newest first | |
| `/auth/admin/temporary-grants` | POST | suite, for themselves | `{ system, role, hours?, reason, reauthToken }` (any catalog role; `hours` 1 to 8, default 4; reason 10 to 500 characters) | 201, the grant with `expiresAt` | 400 `UNKNOWN_ROLE`, `VALIDATION_FAILED`; 409 `GRANT_ACTIVE` (one live grant per person and system); 403 `REAUTH_REQUIRED`, `NOT_SUITE_ADMIN` |
| `/auth/admin/temporary-grants/:id` | DELETE | the holder, any suite admin, or that system's admin | | 204, also when it already ended | 404 |
| `/auth/admin/report` | GET | suite | | the landing report: suite admins; per system its admins (`since`, `grantedBy`) and live grants; the attention lists (locked, setup pending, email not verified, deletion requests with `orphan`, accounts in grace), counts plus the first 10 of each; `systemsWithoutAdmin`; the newest 20 admin level changes | 403 `NOT_SUITE_ADMIN` |
| `/auth/admin/permissions/:system` | GET | suite, or that system's admin (read only) | | `{ system, version, permissions: [{ key, label, group, description, lockedRoles }], grants, canEdit }` | 404 unknown system |
| `/auth/admin/permissions/:system` | PATCH | suite | `{ version, changes: [{ role, key, allowed }], note? }` (note 5 to 500 characters, required when a change takes a right away) | the matrix; a save that changes nothing answers 200 with no new version | 409 `MATRIX_STALE`, `LOCKED_CELL`; 400 `UNKNOWN_PERMISSION`, `UNKNOWN_ROLE`, `NOTE_REQUIRED`, `VALIDATION_FAILED`; 403 `NOT_SUITE_ADMIN` |
| `/auth/admin/permissions/:system/changes` | GET | suite, or that system's admin | `cursor?`, `limit?` | the matrix history, newest first (imported rows included) | |
| `/auth/admin/roles/:system` | GET | suite, or that system's admin (read only) (version 8.1, suite spec 0018) | | `{ system, supportsCustomRoles, canEdit, version, roles: [{ code, name, description, builtIn, isSystemAdmin, copiedFrom, peopleCount, graceCount, lastChanged }], groups: [{ name, permissions: [{ key, label, description, lockedRoles, defaultRoles }] }], cells: { <role>: [key, …] } }`, live roles only, built in first | 403 `NOT_ADMIN_OF_SYSTEM`, 404 |
| `/auth/admin/roles/:system/:code/history` | GET | as above | `cursor?`, `limit?` (default 25, max 100) | `{ items: [{ at, actorName, kind, key?, label?, before?, after?, fromValue?, toValue?, note? }], next }`: `kind` is `PERMISSION` or `CREATED`, `RENAMED`, `DESCRIBED`, `DELETED`, newest first; archived roles keep their history | 400 `INVALID_CURSOR`, 404 (a code that never existed) |
| `/auth/admin/roles/:system/:code/members` | POST | suite, or that system's admin | `{ userIds (1 to 50), reauthToken? }`: moves each person into the role, replacing their role in that system | `{ moved, skipped }` | 400 `NOT_IN_SYSTEM`, `UNKNOWN_ROLE` (also an archived role); 403 `REAUTH_REQUIRED`; 409 `SELF_ROLE`, `SUITE_ADMIN_NO_ROLES`, `TEMPORARY_ROLE`, `LAST_ADMIN`, `ROLE_LIMIT` |
| `/auth/admin/roles/:system` | POST | suite | `{ name, description?, from }`: name 2 to 40 characters with a letter A to Z or a digit, unique among the system's live roles ignoring case; description up to 200; `from` a live role whose saved cells are copied | 201 `{ role, cells, version }`: the new custom role (code `C_<NAME>`, never reused), its allowed keys and the new matrix version | 400 `VALIDATION_FAILED`, `UNKNOWN_ROLE`; 409 `ROLE_NAME_TAKEN`, `CUSTOM_ROLE_LIMIT` (20 live custom roles), `CUSTOM_ROLES_NOT_SUPPORTED` (a system without permission keys) |
| `/auth/admin/roles/:system/:code` | PATCH | suite | `{ name?, description? }` (at least one) | the role; the code never changes | 400 `BUILT_IN_ROLE`, `VALIDATION_FAILED`; 404; 409 `ROLE_NAME_TAKEN` |
| `/auth/admin/roles/:system/:code` | DELETE | suite | | `{ version }`: the custom role is archived and its cells removed | 400 `BUILT_IN_ROLE`; 404; 409 `ROLE_IN_USE` with `details.count` (live holders: people not deleted, deactivated included, and live temporary grants) |
| `/auth/permissions/:system` | GET | a system backend's service token with `permissions.read`, for its own system only | `If-None-Match` | `{ system, version, permissions: [{ key, lockedRoles }], grants: { <role>: [key, …] } }` with `ETag: "v<version>"`, or 304 | 401, 403 `WRONG_SYSTEM`, 404, 429 `RATE_LIMITED` |

- **Temporary access.** A suite admin may give themselves one system role for 1 to 8 hours with a written reason. While it lasts it is a real role: the next code exchange or refresh for that system carries it, the person shows in that system's user lists with `temporaryUntil`, and the directory lists the code in `temporaryRoles` (section 9). Nobody can edit that role (409 `TEMPORARY_ROLE`); they end the grant. A minute sweep ends expired grants, and token building leaves out an expired one even if the sweep stopped. Ending a grant (expiry, `DELETE`, or the holder's suite admin removal) removes the role and ends every live session of the holder that opened that system, with the reason `TEMP_ACCESS_ENDED` (section 6).
- **Never your own standing.** Nobody adds or removes their own suite admin row or changes their own roles; the only self grant is temporary access. A suite admin can't be given a permanent role on any route (409 `SUITE_ADMIN_NO_ROLES`, also enforced by the database), deactivated or deleted (409 `IS_SUITE_ADMIN`; remove the row first), or edit another suite admin's email (403 `SUITE_ADMIN_SELF_ONLY`).
- **Alerts.** welinc-auth emails every suite admin plus the admins of the system concerned, after the change commits (a failed email never blocks it), when: an admin role is added or removed, a suite admin is added or removed or the recovery script runs (every system), temporary access starts or ends early, a matrix is edited, an admin account's email, codes, lock or sessions are acted on, or a suite admin gives any role or creates an account. Expiry, the seed and `catalog:sync` send none.
- **Events.** Version 7 adds the account event types `SUITE_ADMIN_ACTIONED`, `SUITE_ADMIN_REMOVED`, `TEMP_ACCESS_STARTED`, `TEMP_ACCESS_ENDED` and `ADMIN_RECOVERY` (category `ACCOUNT`, kept for good) and `ADMIN_CODE_PASSED` (category `SIGN_IN`), with labels in `/auth/activity/catalog`; the session end reason `TEMP_ACCESS_ENDED`; the reauth reasons `ADMIN_ACTION` and `TEMPORARY_ACCESS`.
- **Recovery.** If no suite admin can sign in, whoever runs the server runs `npm run admin:recover -- --email <address> --reason "<text>"` in the auth container. It unlocks the account and makes it a suite admin, ends its sessions, logs it and alerts everyone. It sets no password.
- **The permission matrix.** welinc-auth holds each system's role to permission matrix: the keys, labels and defaults come from the system's catalog file (`prisma/catalog/<system>.ts`, `permissions`, written by `catalog:sync`), the cells are edited by suite admins only, and every changed cell is logged. A system reads its own matrix with `GET /auth/permissions/:system` and keeps a cached copy: poll about every 60 s with `If-None-Match`, replace your copy on a 200, keep it on a failure. Joining is optional. Only VRMS has keys today; VMMS and BMS have an empty matrix until they add `permissions` to their catalog files and ask for `permissions.read` on their client. The VRMS matrix routes `PATCH /vrms/permissions` and `GET /vrms/permissions/changes` are removed; VRMS keeps `GET /vrms/permissions/me` and a read only `GET /vrms/permissions`.
- **Custom roles (version 8.1, suite spec 0018).** A suite admin may make a role for a system that has permission keys (VRMS today) by copying a live role, then rename it, describe it and delete it once nobody holds it. A custom role is never the system admin role and has no locked cells. It travels like any role: its code is in access tokens' `roles`, `/auth/me`, the directory (section 9), the `/auth/users*` and `/auth/admin/users*` routes and the permission poll; an archived one is in none of them and can't be given (400 `UNKNOWN_ROLE`). Built in roles stay owned by the catalog file (no rename, no delete) and `catalog:sync` never touches a custom role. The `vmms-mobile` client still allows only `MECHANIC` and `CHIEF_MECHANIC` for VRMS, so a custom VRMS role gets `APP_NOT_ALLOWED` on the phone app. A Restore drops any archived role from the restored person.

### 11. Errors

- welinc-auth and the system session routes answer with Nest's usual body plus a stable `code`: `{ "statusCode": 409, "message": "…", "error": "Conflict", "code": "ACCOUNT_EXISTS" }`. Clients branch on `code`, never on `message`.
- `/auth/token` answers in the OAuth format so standard libraries understand it: `{ "error": "invalid_grant", "error_description": "…" }` (400), `invalid_client` (401), or `invalid_target` and `invalid_scope` (400) for an audience or scope the client may not have.
- Codes this contract introduces: `SESSION_ENDED`, `ACCOUNT_INACTIVE`, `ACCOUNT_LOCKED` (403, an account past its 5 failed attempts; since version 10 for 15 minutes, with `lockedUntil`, or until an admin unlocks it or a code resets the password), `TOKEN_EXPIRED` (a good token past its `exp`: refresh and retry once), `CSRF_REJECTED`, `AUTH_UNAVAILABLE`, `NO_SYSTEM_ACCESS`, `WRONG_AUDIENCE`, `WRONG_TOKEN_USE`, `REAUTH_REQUIRED`, `RATE_LIMITED`, `UNKNOWN_ROLE` (400, a role the system's catalog doesn't have), `ROLE_LIMIT` (409, more roles in one system than it allows), `APP_NOT_ALLOWED` (403, the account's roles aren't allowed on this app, section 4; its message names the allowed roles and is safe to show), the directory codes `INVALID_CURSOR` (400, a cursor welinc-auth did not issue or one from before a restore: read everything again), `VALIDATION_FAILED` (400, a bad `limit` or lookup body) and `FORBIDDEN` (403, a caller the directory doesn't serve, section 9), the portal error codes `LOGIN_REQUEST_EXPIRED`, `LOGIN_STATE_INVALID`, `LOGIN_FAILED`, and (version 4, spec 0009) the sign in status `EMAIL_VERIFICATION_REQUIRED` (a 200 answer, not an error) and the codes `INVALID_CODE` (400, a wrong code with tries left, with `attemptsLeft`), `CODE_EXPIRED` (400, an unknown, used, expired or dead code or ticket: start again), `CODE_SEND_LIMIT` (429 with `Retry-After`, inside the 60 s wait or over 5 sends an hour), `MAIL_FAILED` (503, the email could not be sent and nothing was kept), `SAME_EMAIL` (400), `EMAIL_TAKEN` (409) and `SELF_EMAIL` (409, change your own email from your profile). Version 5 (spec 0011) uses `VALIDATION_FAILED` (400, a bad activity filter or `limit`) and `INVALID_CURSOR` (400, an activity cursor welinc-auth did not hand out) on the activity routes too. Version 6 (spec 0012) adds `WRONG_PASSWORD` (400, a wrong current password on `verify-password`, `POST /auth/profile/email` and `PATCH /auth/profile/password`, with `attemptsLeft`; `ACCOUNT_LOCKED` follows on the 5th in a row), `REAUTH_REQUIRED` (403, a reauth token that is missing, wrong, used, expired, for another purpose or from another session: ask for the password again), `DELETION_PENDING` (409, one request is already waiting), `LAST_ADMIN` (409, the change would leave a system without an active admin; the message names the system), `NOT_PENDING` (409, the request was decided or cancelled a moment ago), `SELF_DECISION` (403, nobody decides their own request) and `NOT_RESTORABLE` (409, the account is not deleted or is already erased). It also uses `VALIDATION_FAILED` (a bad `purpose`, `note` or `view`), `INVALID_CURSOR` and `RATE_LIMITED` on the new routes. Version 7 (spec 0013) adds the sign in status `SIGN_IN_CODE_REQUIRED` (a 200 answer, not an error) and the codes `NOT_SIGNED_IN` (401, no live SSO session on an admin route), `NOT_AN_ADMIN` (403), `ADMIN_CODE_REQUIRED` (403, the session hasn't passed the admin sign in code: step up in the portal, also on the bearer admin routes), `NOT_ADMIN_OF_SYSTEM` (403), `NOT_SUITE_ADMIN` (403), `SUITE_ADMIN_SELF_ONLY` (403), `WRONG_SYSTEM` (403, a matrix read for another system), `CODE_NOT_REQUIRED` (409, the admin code is switched off), the 409s `SUITE_ADMIN_LIMIT`, `ALREADY_SUITE_ADMIN`, `HOLDS_SYSTEM_ROLES`, `NOT_ELIGIBLE`, `LAST_SUITE_ADMIN`, `SELF_ROLE`, `SUITE_ADMIN_NO_ROLES` (a suite admin can't hold a permanent role), `IS_SUITE_ADMIN` (remove the suite admin row first), `GRANT_ACTIVE`, `TEMPORARY_ROLE` (end the grant instead), `MATRIX_STALE` (someone saved first: reload) and `LOCKED_CELL`, and the 400s `UNKNOWN_PERMISSION` and `NOTE_REQUIRED`. `REAUTH_REQUIRED` now also covers the `ADMIN_ACTION` and `TEMPORARY_ACCESS` writes. Version 10 (spec 0015): a lock runs out after 15 minutes, and every `ACCOUNT_LOCKED` body carries `lockedUntil`; the right password on a deactivated account answers 403 `ACCOUNT_INACTIVE` on `/auth/login`, `/auth/login/verify-email` and `/auth/mobile/login` (a wrong one is still the plain 401). Version 8.1 (suite spec 0018) adds `BUILT_IN_ROLE` (400), `ROLE_NAME_TAKEN`, `CUSTOM_ROLE_LIMIT`, `CUSTOM_ROLES_NOT_SUPPORTED` and `ROLE_IN_USE` (409; the last carries `details: { count }`, the people who still hold the role). A body may carry an optional `details` object with extra facts; clients ignore it when they don't need it.
- Codes the gateway answers itself (version 3, section 3): `NOT_FOUND` (404), `PAYLOAD_TOO_LARGE` (413), `RATE_LIMITED` (429, with `Retry-After: 1`), `UPSTREAM_UNAVAILABLE` (502) and `UPSTREAM_TIMEOUT` (504), plus (VRMS spec 0025) `METHOD_NOT_ALLOWED` (405, anything but `POST` or `OPTIONS` on a Sentry tunnel route) and `TUNNEL_REJECTED` (403, a tunnel report whose envelope DSN isn't that route's own). Every health route answers `HEALTH_CHECK_FAILED` (503) when a check fails. A web app can tell a gateway answer from its own service's by these codes.
- `NO_SYSTEM_ACCESS` and `APP_NOT_ALLOWED` are about the account, not the client's request, so they use the coded body above on every route, `/auth/token` included (403), not the OAuth format.
- Version 8: `/auth/authorize` carries `APP_NOT_ALLOWED` as a literal `error_description` next to `error=access_denied` (section 7), and a system's `refresh` answers 403 `APP_NOT_ALLOWED` in the coded body.

### 12. Limits

| Route | Limit | Answer when over |
|---|---|---|
| `/auth/login` | 10 a minute per address and 5 failures per account (the existing lockout) | 429 `RATE_LIMITED` with `Retry-After`, or 403 `ACCOUNT_LOCKED` (the body keeps `isLocked: true` and `remainingAttempts: 0` for the portal) |
| `/auth/mobile/login` | 5 a minute per address for every mobile client together, sharing the per account lockout | as above |
| `/auth/token` | 600 a minute per client for calls with a valid assertion, which skip the per address count; 120 a minute per address for every other call and every refused assertion (spec 0003). public mobile clients (`vmms-mobile`, `bms-mobile`) 30 a minute per address, counted together | 429 with `Retry-After` and `{ "error": "rate_limited" }` |
| `/auth/authorize` | 30 a minute per address | 429 error page |
| `/auth/sso` | 60 a minute per address (S4); the launcher's focus checks stay far below it | 429 `RATE_LIMITED` with `Retry-After` |
| `/auth/session/activity` | 2 a minute per `sid` (extra pings are accepted and ignored) | none |
| `/auth/session` | none beyond the gateway; systems cache 30 s | none |
| `/auth/directory/*` | 120 a minute per client, one count shared by all three routes, counted after the token check (calls answered 401 or 403 don't count). A first sync plus a poll every 30 to 60 s stays far below it | 429 `RATE_LIMITED` with `Retry-After`: wait that many seconds |
| `/auth/users/lookup` and `/auth/admin/users/lookup` (enforced since version 8) | 30 a minute per admin (`sub`), one counter shared by both routes, counted per welinc-auth container | 429 `RATE_LIMITED` with `Retry-After` |
| `/auth/admin/users/email-check` (2026-11-24, spec 0019) | 60 a minute per admin, its own counter, counted per welinc-auth container | 429 `RATE_LIMITED` with `Retry-After` |
| `/auth/admin/users/facets` (2026-11-25, spec 0019) | 120 a minute per admin, its own counter, counted per welinc-auth container | 429 `RATE_LIMITED` with `Retry-After` |
| `/auth/activity` (version 5) | 60 a minute per admin (`sub`), counted per welinc-auth container | 429 `RATE_LIMITED` with `Retry-After` |
| `/auth/profile/verify-password` (version 6), `/auth/admin/verify-password` (version 7) | 10 a minute per user, the two counted together, on top of the 5 wrong tries that lock the account (shared with sign in) | 429 `RATE_LIMITED` with `Retry-After` |
| `/auth/admin/activity` (version 7) | 60 a minute per admin, as `/auth/activity` | 429 `RATE_LIMITED` with `Retry-After` |
| `/auth/admin/code` and its verify (version 7) | the emailed code limits below (the sign in family) | 429 `CODE_SEND_LIMIT` with `Retry-After` |
| `/auth/permissions/:system` (version 7) | 120 a minute per client, as the directory | 429 `RATE_LIMITED` with `Retry-After` |
| `/auth/forgot-password`, `/auth/verify-otp`, `/auth/reset-password` (version 4) | 10 a minute per address, counted together, before any other work | 429 `RATE_LIMITED` with `Retry-After` |
| `/auth/login/verify-email` and its resend, and the two mobile ones (version 4) | 10 a minute per address, the four counted together | 429 `RATE_LIMITED` with `Retry-After` (mobile: `{ "error": "rate_limited" }`) |
| Every emailed code (version 4) | per user and family (setup and reset together, sign in, email change): one send per 60 s and 5 per rolling hour, admin sends included; a failed send counts toward neither. Each code dies after 5 wrong tries; codes live 10 minutes (setup 60) | 429 `CODE_SEND_LIMIT` with `Retry-After`; a dead code answers `CODE_EXPIRED` (the old routes keep "Invalid or expired OTP") |
| Every gateway route (version 3) | 20 a second per client address with bursts of 40, from the gateway's settings; preflights, `/health` and 404s don't count. A flood guard in front of the limits above, never instead of them | 429 `RATE_LIMITED` with `Retry-After: 1` |

- A confidential client's call with a valid assertion may carry `X-WeLinc-User-Address`, the user's address as the system backend saw it (its own `X-Forwarded-For` through `TRUST_PROXY_HOPS`). welinc-auth stores it as the session's last seen address and ignores the header on any call without a valid assertion (spec 0003).

S rows may tighten these and must note it here.

### 13. Rules every system follows

1. Store people by `sub` (the welinc-auth user id). Never key on email, never add a foreign key to an auth table, never read the auth database.
2. Accept only tokens whose `iss` is the issuer, whose `aud` is your system, and whose `token_use` fits the route.
3. Run the session check (section 6) on every user request.
4. Keep no password, code, refresh token or role assignment of your own. Your own permission rules on top of the token's roles are fine. Since version 7 you may keep that matrix in welinc-auth instead, edited by suite admins and read with `GET /auth/permissions/:system` (section 10a), as VRMS does; joining is optional.
5. Your system's own rules about roles (VMMS: exactly one role per account) live in welinc-auth's system catalog (S5), not copied into your code. Your roles are your file `welinc-auth/prisma/catalog/<system>.ts` (file order is display order and power order, most powerful first; a code never changes once synced, add a new one instead), changed by a pull request to `welinc-auth` and a deploy (`npm run db:deploy` runs the sync); read role names and order from `/auth/systems` instead of a list of your own. Version 8.1: a system with permission keys (VRMS today) may also have custom roles made in the portal, with codes `C_<NAME>` made at runtime; decide behaviour by permission keys there, never by role code, and treat a role code you don't know as a role with no special powers (no crash, no 500).
6. Web apps keep the access token in memory only; no `localStorage`, no token in a URL.
7. Secrets (your client private key) live in your Container Apps secrets and your git ignored `.env`, documented in `.env.example` only.
8. BMS's public tracking links keep their own secret inside BMS and never use welinc-auth's keys or tokens.
9. Keep no account management screens of your own (version 7). Creating people, roles, codes, unlocking, sessions, deactivating and deleting live in the portal admin section; link your admin menu item to `<portal>/admin/people?system=<SYS>`. Work data about a person (assignments, crews, schedules) stays in your system.

### 14. How the contract changes

- **Additive** (a new route, an optional field, a new claim, a new error code): update this spec in the same change.
- **Breaking** (removing or renaming a route, claim or field, or changing what one means): bump the contract version, list each system's change here, and tell the affected groups before it lands. The shared services owner decides; the other groups don't review this spec.
- Each S row spec links back here and states which sections it builds.
- welinc-auth's generated API docs (`/auth/docs`, its `docs/openapi.json`) show the shapes the code really accepts and answers. This contract wins on behavior; where the two disagree, the gap is settled here or in the code, then the docs are regenerated (VRMS spec 0026). Section 16 lists the routes the docs are checked against.

**Versions:**
- **8.2** (2026-11-28, VRMS spec [0027](../../vrms/0027-navigation-redesign/index.md) step 6a, additive). Changes: `user.systemRoles` and `user.suiteAdmin` on every user grant answer (code exchange, refresh, mobile login; section 5), display only and never in a token. Changes per system: **VRMS** passes both through `POST /vrms/session/refresh` and reads them for its switcher's role tags and Suite management card. **VMMS** and **BMS**: none (clients ignore unknown `user` fields); the mobile app ignores them.
- **8.1** (2026-11-27, suite spec [0018](../0018-roles-and-custom-roles/index.md), S20 and S21, additive). Changes: `builtIn` on each role of `/auth/systems`, which now sends `Cache-Control: no-cache` and lists live roles only (section 10); role codes made at runtime: for a system that supports custom roles any code matching `^[A-Z][A-Z0-9_]{1,39}$` (custom ones start with `C_`) may appear in tokens, `/auth/me` and the directory feed (sections 9, 13); the Roles admin routes `GET /auth/admin/roles/:system`, `GET …/:code/history`, `POST …/:code/members`, `POST /auth/admin/roles/:system`, `PATCH` and `DELETE /auth/admin/roles/:system/:code`, plus `excludeRole` and `assignable` on `GET /auth/admin/users` (section 10a); the new error codes and `details` (section 11). Changes per system: **VRMS** decides behaviour by permission keys only and reads role names from `/auth/systems` (suite spec 0018 child 0002, AC-32 to AC-35); the portal shows the Roles page. **VMMS** and **BMS**: none. They have no permission keys, so they can't get custom roles, but a person holding one of their roles plus a custom VRMS role may sign in to them: their tokens and directory carry only their own system's roles, and the check in child 0002 AC-37 confirms they keep working.
- **Additive within 8** (2026-11-23, suite spec 0017, S19): the read scope in section 10a (a system admin may leave `system` out of the three People reads, where a missing `system` used to be 400); `group`, `sort`, status lists, role name search and `counts` on `GET /auth/admin/users`; `lastSignedInAt` and per role `temporaryUntil` on its items and the person; the person page facts on `GET /auth/admin/users/:id`. No version bump: a former 400 now answers 200, and every former answer keeps its meaning. Only the portal calls these routes; the bearer `/auth/users*` routes are unchanged.
- **8** (2026-11-13, spec 0014, S11).
  - Breaking: the launcher answer (`/auth/login`, `/auth/login/verify-email`, `/auth/sso`) splits web and phone only systems, and a person whose roles pass only a phone app gets 200 with `systems: []` where it was a launcher card or 403; `user.systems` lists web systems only; the `vmms` and `bms` web clients admit office roles only (sections 4, 7, 10).
  - Additive: `mobileSystems` and `app_released` (sections 4, 10); `error_description=APP_NOT_ALLOWED` on `/auth/authorize` and its callback mapping (sections 7, 11); the `fleet.read` scope for `bms` on `VMMS` and the fleet API's scope (section 4); the lookup limit made real (section 12); the seed person `vmms.mech@`; the move order (VMMS and BMS in parallel).
  - Changes per system: **VRMS** and the portal merge with welinc-auth: VRMS's session callback and refresh handle `APP_NOT_ALLOWED` (the reference the others copy), and the portal shows the phone only state, the mobile app line and the `APP_NOT_ALLOWED` page. VRMS's own behavior doesn't change (it names no allowed roles). **VMMS** moves per [`docs/integration/move-vmms.md`](../../../integration/move-vmms.md): client `vmms` with the session routes, no auth tables or `JWT_SECRET`, the directory reader, analytics verifying tokens itself, `vmms-mobile` with the code screen, and the fleet API. **BMS** moves per [`docs/integration/move-bms.md`](../../../integration/move-bms.md): `bms-gateway` in NestJS as client `bms`, every process verifying ES256 tokens, no `welinc_db` (drivers into dispatch, trucks and garages from the fleet API, its own analytics read model), and the old `welinc-backend` archived.
- **7** (2026-11-13, spec 0013, S10).
  - Breaking: `/auth/login` may answer `SIGN_IN_CODE_REQUIRED` for an admin instead of a login, and a suite admin's launcher answer is a 200 with no systems where it was 403 `NO_SYSTEM_ACCESS` (sections 7, 10); every bearer admin route (`@SystemAdmin()`) answers 403 `ADMIN_CODE_REQUIRED` until the session passed the admin code, and adding an admin role or acting on an admin account needs a `reauthToken` (403 `REAUTH_REQUIRED`); 409 `SUITE_ADMIN_NO_ROLES`, `IS_SUITE_ADMIN` and `TEMPORARY_ROLE` on the bearer writes; the bearer admin routes are deprecated (section 10); the reserved `/auth/login/otp` and `/auth/mobile/login/otp` and `OTP_REQUIRED` are removed (never built, section 8); a temporary grant's end ends sessions with `TEMP_ACCESS_ENDED` (section 6); VRMS's own `PATCH /vrms/permissions` and `GET /vrms/permissions/changes` are removed.
  - Additive: the `/auth/admin/*` routes and `GET /auth/permissions/:system` (section 10a); `temporaryRoles` on `DirectoryUser` (section 9); `temporaryUntil` on admin user items; the reauth purposes `ADMIN_ACTION` and `TEMPORARY_ACCESS` (section 5); the `permissions.read` scope on the `vrms` client (section 4); the event types, session end reason, codes and limits of sections 10a, 11 and 12; `ADMIN_SIGN_IN_CODE` (section 15); rule 9 and the optional central matrix in rule 4 (section 13).
  - Changes per system: **VRMS** and the portal merge with welinc-auth: the portal shows the code step and the admin section, the VRMS Users page becomes a team view with Manage account links, VRMS reads its matrix from welinc-auth and skips `temporaryRoles` in its mechanic roster. **VMMS** and **BMS**: their web apps call `/auth/users*` with admin tokens today, so an admin there gets 403 `ADMIN_CODE_REQUIRED` until they confirm the code once in the portal (sign in through the portal, or open `<portal>/admin`). Then, before or with S11, they delete their account management pages, link the menu item to `<portal>/admin/people?system=<SYS>`, handle `SIGN_IN_CODE_REQUIRED` wherever they call `/auth/login` themselves (BMS does) and `ADMIN_CODE_REQUIRED` on any admin call, and may join the central matrix later, following [`docs/integration/account-screens.md`](../../../integration/account-screens.md#admin-pages-live-in-the-portal).
- **6** (2026-11-12, spec 0012, S8).
  - Breaking: `DirectoryUser.phoneVerified` is removed and `DirectoryUser.erased` is added (section 9); the reserved `POST /auth/profile/phone` and `/auth/profile/phone/verify` are removed (nothing served or called them); a wrong current password on `POST /auth/profile/email` and `PATCH /auth/profile/password` is now 400 `WRONG_PASSWORD` with `attemptsLeft` instead of a bare 400, and counts toward the sign in lockout (section 10); "welinc-auth owns phone numbers and their verified flag" becomes "stores the phone as a plain contact field; no system verifies it".
  - Additive: the S8 routes (`verify-password`, the deletion request routes, the admin review routes and restore), `pendingDeletion` on `GET /auth/users`, the reauth token, erasure and its feed behavior, the account event types and catalog entries, the codes of section 11 and the `verify-password` limit (sections 7, 9 to 12).
  - Changes per system: **VRMS** drops nothing (it never read `phoneVerified`), adds the Delete account card and the Users page deletion view, reads `erased` from the feed, and unassigns open tickets of mechanics who are deleted, deactivated or lose the role. **VMMS** and **BMS**: none until S11. Then BMS changes `{ valid }` to `reauthToken` and reads `GET /auth/profile/deletion-request` instead of `deletionRequestStatus`, VMMS wires its deletion dialog and deletes its phone verification and Semaphore code, and both read `erased` from the directory if they keep copies of names or emails, following [`docs/integration/account-screens.md`](../../../integration/account-screens.md#account-deletion).
- **5** (2026-11-12, spec 0011, S7).
  - Breaking: `GET /auth/users/:id/changes` is removed (404); its rows live on as `ACCOUNT` events, and `RESET_SENT` became `CODE_SENT` with reason `PASSWORD_RESET`. A role change is now one `ROLE_CHANGED` per system, each side listing only that system's roles (section 10).
  - Additive: `/auth/profile/activity`, `/auth/users/:id/activity`, `/auth/activity`, `/auth/activity/catalog`, the `/auth/activity` limit, `VALIDATION_FAILED` and `INVALID_CURSOR` on those routes (sections 10 to 12).
  - Changes per system: **VRMS** shows Recent activity on My profile and an Activity dialog on the Users page; it never called `/changes`. **VMMS** and **BMS**: none until S11. Then they read these routes instead of their own tables and the BMS gateway stops reading `user_activity_logs`, following [`docs/integration/account-screens.md`](../../../integration/account-screens.md#activity).
- **4** (2026-11-11, spec 0009, S13).
  - Breaking: `PATCH /auth/users/:id/password` is removed and admins can't send `password` on create or edit; `PATCH /auth/profile` no longer takes `email`; `/auth/login` and `/auth/mobile/login` may answer the `EMAIL_VERIFICATION_REQUIRED` step instead of a login (sections 8, 10).
  - Additive: the verify and resend routes for that step, `/auth/profile/email*`, `passwordSet` and `pendingEmail`, the codes and limits of sections 11 and 12, and the 6 digit check on the old code routes.
  - Changes per system: **VRMS** web no longer sends `password` to admin routes, shows Setup pending and Email not verified from `passwordSet` and `emailVerified`, and changes your own email through `/auth/profile/email*`; the portal shows the code step; all merge with welinc-auth. **VMMS** and **BMS**: none until S11. Then `vmms-mobile` and `bms-mobile` must show the code screen, BMS stops resetting people to a default password and uses Send reset code, and their profile pages change email through `/auth/profile/email*`.
- **3** (2026-11-11, spec 0008, S9).
  - Breaking, with no caller affected: the `/repairs` route is removed (nothing served or called it), and a bare prefix with no slash (`/vrms`) answers 404 instead of reaching the service (nothing calls one).
  - Additive: the Docker service names (section 2); the gateway's `/health`, its JSON 404, 413, 429, 502 and 504 answers and their codes, the flood limit, `X-Forwarded-For` as one value, the request id rule, the headers it owns, the CORS header lists and HSTS (sections 3, 11, 12); `<prefix>/health` with `HEALTH_CHECK_FAILED`; the config home in `infra/gateway/`, one template for every environment.
  - Changes per system: **VRMS** none (`/vrms/health` is new). **VMMS** and **BMS**: none until S11. Then they use the section 2 service names, add `<prefix>/health`, and VMMS drops `X-VMMS-Client`, calls analytics through `/vmms/analytics/`, and moves its `/uploads/` static route under `/vmms/` so it doesn't collide with auth's.
- **2** (2026-11-09, spec 0005, S6).
  - Breaking: `GET /auth/users` no longer takes service tokens; it is for admins only (section 10).
  - Behaviour a reader may notice: the directory feed (section 9) writes at most one change per person per save, and none for a save nothing visible changed (a password change, a lock, the same values). Version 1 said "every change". No version 1 cursor was ever issued (the feed didn't exist yet), so none can break.
  - Additive: the feed serves up to the safe point instead of "older than 5 s" (a stronger guarantee, no reader change), the feed epoch and `INVALID_CURSOR` after a restore, the backfill, `phoneVerified` false until S8, and the directory codes `INVALID_CURSOR`, `VALIDATION_FAILED`, `FORBIDDEN` and `RATE_LIMITED` with `Retry-After` (sections 11, 12).
  - Changes per system: **VRMS** stops calling `/auth/users` with its service token and reads people through the directory, in the same release as welinc-auth. **VMMS** and **BMS**: none known. Their admin web apps call `/auth/users` with admins' user tokens, which still works, and their backends move onto the directory with S11.
  - Additive in the same version (2026-11-10, spec 0007, S4): `user.systems` in user grant answers and the session refresh, and clients ignore unknown `user` fields (sections 5, 7); the launcher rules, Switch system to `<portal>/?from=<SYS>`, and where an app may send a person (section 7); `description` on `/auth/systems`, the final `/auth/login` and `/auth/sso` bodies, and the `/auth/sso` limit (sections 10, 12). `/auth/login` dropping `system` changes a portal only route that merges with the portal. Changes per system: **VRMS** shows Switch system from `user.systems`. **VMMS** and **BMS**: none until S11; then follow `docs/integration/web-login.md`.
- **1** (2026-11-08): the first contract.

### 15. Configuration

**welinc-auth** (new or changed; values in `.env.example` only):
- `AUTH_ISSUER`: the issuer from section 1.
- `AUTH_SIGNING_KEYS`: the private signing keys as a JWK set, each with its `status` (section 5); a Container Apps secret when hosted. Replaces `JWT_SECRET`.
- `TRUST_PROXY_HOPS`: proxy hops in front of welinc-auth (1 locally, 2 hosted), for the per address limits (spec 0002).
- `ACCESS_TOKEN_MINUTES` (15), `SERVICE_TOKEN_MINUTES` (5), `WEB_SESSION_IDLE_MINUTES` (30), `WEB_SESSION_MAX_HOURS` (12), `MOBILE_SESSION_IDLE_DAYS` (7), `REFRESH_REUSE_GRACE_SECONDS` (10), `MAX_SESSIONS_PER_USER` (10), `SESSION_RETENTION_DAYS` (90). Replace `JWT_ACCESS_EXPIRY` and `JWT_REFRESH_EXPIRY`.
- `API_PUBLIC_URL`: the gateway address the browser sees; the seed builds each system's redirect address from it. `CLIENT_<ID>_WEB_ADDRESS` per system client (spec 0003).
- `PORTAL_URL` (kept), `SSO_COOKIE_SECURE` (true when hosted).
- `ADMIN_SIGN_IN_CODE` (version 7, default `true`): `false` turns the admin sign in code off locally (seed admin addresses can't receive mail); production refuses `false` at boot.
- Its database role runs with `idle_in_transaction_session_timeout = 60s` (set by the directory feed migration locally; spec 0008 sets it on the hosted database), so a forgotten open transaction can't hold the directory feed back for long (section 9).
- The client registry (section 4) comes from the seed per environment, with each client's public keys and redirect address read from environment values.

**Each system backend:**
- `AUTH_ISSUER`, `AUTH_INTERNAL_URL` (welinc-auth's internal address for server calls), `AUTH_JWKS_URL`.
- `AUTH_CLIENT_ID`, `AUTH_CLIENT_PRIVATE_KEY` (secret; its own ES256 key).
- `WEB_APP_URL` (where users land, and the one `Origin` its cookie routes accept), `PORTAL_URL`.
- `AUTH_PUBLIC_URL` (welinc-auth as the browser sees it, for `/auth/authorize`), `API_PUBLIC_URL` (its callback is `<API_PUBLIC_URL>/<sys>/session/callback`), `SESSION_COOKIE_SECURE`, `TRUST_PROXY_HOPS` (spec 0003).

**Each web app:** `VITE_API_BASE_URL` and `VITE_PORTAL_URL` only. No secret, no token setting.

### 16. Route index

Every welinc-auth route this contract promises, one row per method, from sections 3 and 5 to 10a (routes marked removed are left out). Added by VRMS spec [0026](../../vrms/0026-api-docs/index.md), additive.

- **What it is for.** welinc-auth's generated API docs (`/auth/docs` locally and on staging, and the committed [`docs/openapi.json`](https://github.com/Capstone-WeLinc/welinc-auth/blob/development/docs/openapi.json) in welinc-auth) show each route's inputs, replies and error codes. This index is the list those docs are held to: `node scripts/check-contract-routes.mjs <openapi.json>` fails when a row here is missing from the document, or when a row marked `yes` under *Reply schema* has no 200 or 201 reply schema there. It also prints, without failing, any documented `/auth/*` route with no row here. The workspace CI runs it against welinc-auth's `development` branch on every workspace change, daily and on demand.
- **Security** uses the scheme names of the generated docs: `userToken` (a user access token as `Authorization: Bearer`), `serviceToken` (a client credentials token as `Authorization: Bearer`), `ssoCookie` (welinc-auth's SSO cookie, portal and browser routes), `clientAssertion` (a `private_key_jwt` in the form body). `none` means no token or cookie.
- **Reply schema** `yes` marks the integration routes: the ones another system calls to plug in. Their success reply is described field by field in the docs and checked by a test in welinc-auth. The other routes show inputs, errors and the reply status, and the sections above describe their bodies.
- **Changing it.** Adding a route to the contract adds its row here in the same change (section 14). Removing one removes its row in the same change as the code. A path writes parameters as `:param`; the check turns them into the document's `{param}`.

| Method | Path | Security | Section | Reply schema |
|---|---|---|---|---|
| GET | `/auth/health` | none | 3 | |
| GET | `/auth/.well-known/jwks.json` | none | 5, 10 | yes |
| GET | `/auth/.well-known/oauth-authorization-server` | none | 10 | yes |
| POST | `/auth/token` | `clientAssertion` | 5, 7, 8, 10 | yes |
| GET | `/auth/session` | `userToken` | 6, 10 | yes |
| POST | `/auth/session/activity` | `ssoCookie`, `clientAssertion` | 6, 10 | |
| GET | `/auth/authorize` | `ssoCookie` | 7, 10 | |
| GET | `/auth/authorize/resume` | `ssoCookie` | 7, 10 | |
| POST | `/auth/login` | none | 7, 10 | |
| POST | `/auth/login/verify-email` | none | 7, 10 | |
| POST | `/auth/login/verify-email/resend` | none | 7, 10 | |
| GET | `/auth/sso` | `ssoCookie` | 7, 10 | |
| POST | `/auth/mobile/login` | none | 8, 10 | yes |
| POST | `/auth/mobile/login/verify-email` | none | 8, 10 | yes |
| POST | `/auth/mobile/login/verify-email/resend` | none | 8, 10 | |
| POST | `/auth/logout` | `ssoCookie`, `clientAssertion` | 8, 10 | |
| GET | `/auth/directory/users` | `serviceToken` | 9 | yes |
| POST | `/auth/directory/users/lookup` | `serviceToken` | 9 | yes |
| GET | `/auth/directory/changes` | `serviceToken` | 9 | yes |
| GET | `/auth/systems` | none | 10 | yes |
| GET | `/auth/me` | `userToken` | 10 | yes |
| GET | `/auth/me/sessions` | `userToken` | 10 | |
| DELETE | `/auth/me/sessions/:sid` | `userToken` | 10 | |
| POST | `/auth/forgot-password` | none | 10 | |
| POST | `/auth/verify-otp` | none | 10 | |
| POST | `/auth/reset-password` | none | 10 | |
| PATCH | `/auth/profile` | `userToken` | 10 | |
| PATCH | `/auth/profile/password` | `userToken` | 10 | |
| POST | `/auth/profile/picture` | `userToken` | 10 | |
| GET | `/auth/profile/summary` | `userToken` | 10 | |
| POST | `/auth/profile/email` | `userToken` | 10 | |
| POST | `/auth/profile/email/verify` | `userToken` | 10 | |
| DELETE | `/auth/profile/email` | `userToken` | 10 | |
| GET | `/auth/profile/activity` | `userToken` | 10 | |
| POST | `/auth/profile/verify-password` | `userToken` | 10 | |
| POST | `/auth/profile/deletion-request` | `userToken` | 10 | |
| GET | `/auth/profile/deletion-request` | `userToken` | 10 | |
| DELETE | `/auth/profile/deletion-request` | `userToken` | 10 | |
| GET | `/auth/users` | `userToken` | 10 | |
| POST | `/auth/users` | `userToken` | 10 | |
| GET | `/auth/users/lookup` | `userToken` | 10, 12 | |
| PATCH | `/auth/users/:id` | `userToken` | 10 | |
| DELETE | `/auth/users/:id` | `userToken` | 10 | |
| PATCH | `/auth/users/:id/status` | `userToken` | 10 | |
| PATCH | `/auth/users/:id/unlock` | `userToken` | 10 | |
| GET | `/auth/users/:id/sessions` | `userToken` | 10 | |
| DELETE | `/auth/users/:id/sessions` | `userToken` | 10 | |
| GET | `/auth/users/:id/activity` | `userToken` | 10 | |
| POST | `/auth/users/:id/restore` | `userToken` | 10 | |
| GET | `/auth/activity` | `userToken` | 10 | |
| GET | `/auth/activity/catalog` | none | 10 | |
| GET | `/auth/deletion-requests` | `userToken` | 10 | |
| POST | `/auth/deletion-requests/:id/approve` | `userToken` | 10 | |
| POST | `/auth/deletion-requests/:id/reject` | `userToken` | 10 | |
| GET | `/auth/admin/me` | `ssoCookie` | 10a | |
| POST | `/auth/admin/code` | `ssoCookie` | 10a | |
| POST | `/auth/admin/code/verify` | `ssoCookie` | 10a | |
| POST | `/auth/admin/verify-password` | `ssoCookie` | 10a | |
| GET | `/auth/admin/users` | `ssoCookie` | 10a | |
| GET | `/auth/admin/users/facets` | `ssoCookie` | 10a, 12 | |
| GET | `/auth/admin/users/lookup` | `ssoCookie` | 10a, 12 | |
| GET | `/auth/admin/users/email-check` | `ssoCookie` | 10a, 12 | |
| GET | `/auth/admin/users/:id` | `ssoCookie` | 10a | |
| POST | `/auth/admin/users` | `ssoCookie` | 10a | |
| PATCH | `/auth/admin/users/:id` | `ssoCookie` | 10a | |
| PATCH | `/auth/admin/users/:id/status` | `ssoCookie` | 10a | |
| PATCH | `/auth/admin/users/:id/unlock` | `ssoCookie` | 10a | |
| POST | `/auth/admin/users/:id/reset-code` | `ssoCookie` | 10a | |
| GET | `/auth/admin/users/:id/sessions` | `ssoCookie` | 10a | |
| DELETE | `/auth/admin/users/:id/sessions` | `ssoCookie` | 10a | |
| GET | `/auth/admin/users/:id/activity` | `ssoCookie` | 10a | |
| DELETE | `/auth/admin/users/:id` | `ssoCookie` | 10a | |
| POST | `/auth/admin/users/:id/restore` | `ssoCookie` | 10a | |
| GET | `/auth/admin/activity` | `ssoCookie` | 10a | |
| GET | `/auth/admin/deletion-requests` | `ssoCookie` | 10a | |
| POST | `/auth/admin/deletion-requests/:id/approve` | `ssoCookie` | 10a | |
| POST | `/auth/admin/deletion-requests/:id/reject` | `ssoCookie` | 10a | |
| GET | `/auth/admin/suite-admins` | `ssoCookie` | 10a | |
| POST | `/auth/admin/suite-admins` | `ssoCookie` | 10a | |
| POST | `/auth/admin/suite-admins/:userId/remove` | `ssoCookie` | 10a | |
| GET | `/auth/admin/temporary-grants` | `ssoCookie` | 10a | |
| POST | `/auth/admin/temporary-grants` | `ssoCookie` | 10a | |
| DELETE | `/auth/admin/temporary-grants/:id` | `ssoCookie` | 10a | |
| GET | `/auth/admin/report` | `ssoCookie` | 10a | |
| GET | `/auth/admin/permissions/:system` | `ssoCookie` | 10a | |
| PATCH | `/auth/admin/permissions/:system` | `ssoCookie` | 10a | |
| GET | `/auth/admin/permissions/:system/changes` | `ssoCookie` | 10a | |
| GET | `/auth/admin/roles/:system` | `ssoCookie` | 10a | |
| POST | `/auth/admin/roles/:system` | `ssoCookie` | 10a | |
| GET | `/auth/admin/roles/:system/:code/history` | `ssoCookie` | 10a | |
| POST | `/auth/admin/roles/:system/:code/members` | `ssoCookie` | 10a | |
| PATCH | `/auth/admin/roles/:system/:code` | `ssoCookie` | 10a | |
| DELETE | `/auth/admin/roles/:system/:code` | `ssoCookie` | 10a | |
| GET | `/auth/permissions/:system` | `serviceToken` | 10a | yes |

- `/auth/users` "as today" in section 10 is written here as the methods the code serves (`PATCH` and `DELETE` on `/auth/users/:id`, no `GET`), and the section 10 profile row as one method per path. Both readings are on spec 0026's Follow-up list until the section 10 rows say so themselves.
- The bearer admin routes (`/auth/users*`, `/auth/activity`, `/auth/deletion-requests*`) are deprecated (section 10). Spec 0014's cleanup removes their rows here in the same change that removes the routes.

## Gap map

Every gap from the 2026-11-07 check, mapped to the row that closes it.

| Gap today | Closed by |
|---|---|
| One `JWT_SECRET` held by every service, so any of them can mint a token | S2 |
| VMMS has its own users, roles, refresh tokens, login activity, phone verification and account audit logs | S3, S5, S6, S7, S8, then S11 removes them (spec 0014) |
| VMMS web takes `?token=` from the portal; VRMS and the portal do the same | S3 (VRMS and the portal), S4 (the launcher and the guide [`docs/integration/web-login.md`](../../../integration/web-login.md)), S11 (VMMS moves, spec 0014) |
| VMMS mobile logs in against the VMMS copy (`X-VMMS-Client`) | S3 (mobile client), S11 (spec 0014) |
| VMMS analytics checks callers through `GET auth/me?system=VMMS` on the VMMS backend | S2 (verify with JWKS), S3 (session check) |
| The BMS gateway reads `users`, `user_roles` and `user_activity_logs` straight from the auth database | S6, S7, then S11 (spec 0014) |
| BMS dispatch and analytics read and write `vehicles`, `drivers` and `garages` in `welinc_db`, the old Capstone 1 database | S11 (spec 0014: drivers into BMS dispatch, trucks and garages from the VMMS fleet API, BMS's own analytics database) |
| VMMS and BMS web apps admit every role, though mechanics, drivers and helpers work on phones | S11 (spec 0014, version 8: office roles only on the web clients, the phone only state) |
| Contract section 12 promised a lookup limit welinc-auth didn't enforce | S11 (spec 0014, version 8) |
| VRMS's mechanic sync downloads every user through `GET /auth/users` on page loads and after each save | S6 |
| BMS calls `profile/activity`, `profile/verify-password` and `profile/deletion-request`, which don't exist | S7 (closed by spec 0011, version 5), S8 (closed by spec 0012, version 6) |
| BMS has no portal handoff | S4 (the guide [`docs/integration/web-login.md`](../../../integration/web-login.md)), S11 (BMS moves, spec 0014) |
| BMS runs auth from the old `welinc-backend` repo with admin checks removed and no refresh | S11 retires it (spec 0014: archived once BMS passes its checker) |
| BMS roles (Admin, Customer Support, Operations) and VMMS's one role rule live only in their code | S5 |
| welinc-auth guesses the system from `?system=`, `Origin`, `Referer` and the path | S5 (the system is `aud`) |
| welinc-auth has a `RefreshToken` table but no refresh or logout | S3 |
| welinc-auth records no login activity | S7 (closed by spec 0011, contract version 5) |
| welinc-auth has no phone verification | Dropped by S8 (spec 0012, version 6): no system sends SMS, so the phone is a plain contact field |
| welinc-auth has no account deletion or erasure, and the feed keeps names and emails forever | S8 (spec 0012, version 6) |
| Ports clash (VMMS 3000, both analytics 3001, BMS booking 3002) | S9 (section 2) |
| The gateway routes only `/auth`, `/vrms`, `/repairs`, and its config lives in `welinc-auth` | S9 (section 3) |
| Seed accounts drift across three copies (`ops.user`, VMMS chief mechanics) | S12 |
| No safe "can do everything" admin across systems | S10 (closed by spec 0013, version 7: suite admins with no system roles, temporary access, the portal admin section) |
| VMMS and BMS each keep their own user management page | S10 (the portal admin section, version 7), then S11 deletes the pages ([`docs/integration/account-screens.md`](../../../integration/account-screens.md#admin-pages-live-in-the-portal), spec 0014) |

## Move order

Each step is proven end to end before the next starts (Tracer Bullet).

1. **VRMS and the portal, step by step with S2, S3, S5, S6, S4 and S9.** Signing moves to ES256 with S2 (no dual run: VRMS and the portal are the only real users). The `?token=` handoff goes when S4 lands. VRMS's mechanic sync moves onto the directory feed with S6.
2. **S7 and S8**, so the routes BMS and VMMS already call exist before they move.
3. **VMMS and BMS (S11, in parallel; version 8, spec 0014).** Each group moves its own repos with a move guide ([`move-vmms.md`](../../../integration/move-vmms.md), [`move-bms.md`](../../../integration/move-bms.md)), the checker (`scripts/check-system.mjs`) and the VRMS code to copy, as one hard switch per system. VMMS: client `vmms`, no `/auth/*` copy or user tables, analytics verifying tokens itself, `vmms-mobile`, everything under `/vmms` in the 3010 block, and the fleet API. BMS: `bms-gateway` in NestJS as client `bms`, no auth database reads, no `welinc_db`, `/bms` in the 3020 block, and the old `welinc-backend` archived. No user import: every system reseeds from `people.json`. A system is done at its checker plus the cross system check.
4. **Cleanup (S11's last slice, version 9).** Once both groups pass, the bearer admin routes go.
5. **S10**, the suite admin model, once roles, the directory and OTP exist. Replanned 2026-11-11 to land before the S11 moves (version 7), so VMMS and BMS move onto the portal admin section instead of porting their user pages.

The per group guides, the checker and the cross system steps belong to S11 (spec 0014).

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

- [x] Register the domain: `welinc.app`, bought 2026-11-17 with Name.com's GitHub Student Developer Pack offer (free first year, then $26.99 a year); the renewal date goes in spec 0008 (VRMS) once the domain sits in the lead's Name.com account.
- [ ] Update spec 0008 (VRMS hosting): custom domain on every Static Web App and on the gateway Container App, the `infra/gateway/` local config, and the new routes and ports. A new VRMS spec or an update, through `/architect`.
- [ ] Add a line to `docs/_private/vrms/shared-services-questions.md` for BMS: HS256 tokens and `JWT_SECRET` go away when S2 lands, so they shouldn't build more on them; the contract is this spec.
- [ ] VRMS feature 56 (domain contracts) uses section 5's service tokens for calls between systems and lists each system's scopes there.
- [ ] S12 (suite seed accounts) gets its own spec, not this one; it must create the clients of section 4 alongside the people.
- [ ] Later hardening (not scheduled): app attestation on `/auth/mobile/login` (Apple App Attest, Google Play Integrity).
- [ ] `welinc-mobile-bms` is still used (BMS, 2026-11-08), for drivers and helpers, so WeLinc staff (answered 2026-11-08). It becomes a `bms-mobile` client like `vmms-mobile` (a public native row in section 4 with `mobile_login` and `refresh_token`; spec 0003's mobile routes take any such row, so no code change), and BMS gets Driver and Helper roles through S5.
- [ ] After S9, update the README repos table with section 2's ports and the root `AGENTS.md` shared services table (gateway config home). That is `/sync`'s job, through a PR.
- [ ] Run `/architect` for each S row in the epic's order (S2 first); each spec links back to the sections it builds.
- [x] welinc-auth owes section 12's login answers (found 2026-11-11, decided: 403, not 423): the locked answer is 403 with `code: "ACCOUNT_LOCKED"` added, and `/auth/login` (10 a minute per address) gets its address limit with 429 `RATE_LIMITED` and `Retry-After`. Done 2026-11-11 (welinc-auth `de96585`); `/auth/mobile/login`'s 5 a minute limit already existed.
- [x] welinc-web-portal cleanup (found 2026-11-11): drop the `VITE_API_URL` fallback in `src/lib/api.ts` and rename it in `.env.example`. Done 2026-11-11 (welinc-web-portal `26ea274`).
