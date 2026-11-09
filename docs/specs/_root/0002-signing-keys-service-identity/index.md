# 0002. Signing keys and service identity

**Date**: 2026-11-08
**Status**: Accepted
**Partly superseded by**: [0005](../0005-user-directory/index.md) (AC-19 and AC-21: a service token no longer reads `GET /auth/users`; backends read `/auth/directory/*`)
**Scope row**: [S2. Signing keys and service identity](../../../scope/_root/shared-services.md#s2-signing-keys-and-service-identity--done)
**Builds contract sections**: [0001](../0001-shared-services-contract/index.md) section 4 (clients), section 5 (tokens, keys, `POST /auth/token` client credentials grant), section 10 (`.well-known` routes, `/auth/login`), section 12 (`/auth/token` limit), section 15 (configuration)

## Summary

Today one shared password (`JWT_SECRET`) both makes and checks every login token, and about eight services hold it, so any of them could forge a login for anyone. This spec gives welinc-auth a private signing key only it holds, publishes the matching public keys so services can check tokens without being able to make them, and gives each backend its own key to prove who it is when it calls welinc-auth. VRMS switches over in one coordinated release (everyone logs in again once). It then proves service identity by syncing its mechanics with its own token instead of borrowing a user's, and it ships the token check as a folder VMMS and BMS copy in S11.

## Rationale

Reasoning, options and the current state inventory: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As the shared services owner, I want only welinc-auth to be able to sign tokens, so a leak from any other service can't be used to log in anywhere.
- As a VRMS backend, I want to check tokens with welinc-auth's published keys and call welinc-auth as myself, so I hold no shared secret and need no user's token for background work.
- As whoever operates staging and production, I want to swap the signing key without logging anyone out, and to kill a leaked key immediately.
- As a VMMS or BMS developer, I want a tested token check I can copy, so my group doesn't write security checks from a list.

**Acceptance criteria**:

*Signing and publishing*
- **AC-1**: welinc-auth signs every access token with ES256 using the one key whose `status` is `current` in `AUTH_SIGNING_KEYS`. The header carries that key's `kid` and `typ: at+jwt`. Nothing in welinc-auth or backend-vrms reads `JWT_SECRET`, `JWT_REFRESH_SECRET`, `JWT_ACCESS_EXPIRY` or `JWT_REFRESH_EXPIRY`. Each is gone from wherever it appears today: both repos' `.env.example`, `docker-compose.shared.yml` (all four) and `docker-compose.vrms.yml` (`JWT_SECRET`).
- **AC-2**: welinc-auth refuses to start, with a message naming the problem (never the key), when:
  - `AUTH_SIGNING_KEYS` is missing or not valid JSON;
  - there is no key, or more than one, with `status: current`;
  - a key isn't a private EC P-256 key, has an `alg` other than `ES256`, or has a `use` other than `sig`;
  - two keys share a `kid`;
  - a `status` is outside `current`, `next`, `retired`;
  - a self test fails: at startup it signs and verifies a test token with each key, which catches a private part that doesn't match its public part.

  The same applies when `AUTH_ISSUER` is missing.
- **AC-3**: `GET /auth/.well-known/jwks.json` answers `{ keys: [...] }` with the public part of every `current`, `next` and `retired` key (each with `kty`, `crv`, `x`, `y`, `kid`, `alg: ES256`, `use: sig`) and never a private member (`d`) or the `status`, `addedAt` or `retiredAt` fields. It sends `Cache-Control: public, max-age=300` and needs no token.
- **AC-4**: `GET /auth/.well-known/oauth-authorization-server` answers the RFC 8414 metadata: `issuer` (`AUTH_ISSUER`), `token_endpoint` (`<issuer>/token`), `jwks_uri` (`<issuer>/.well-known/jwks.json`), `grant_types_supported: ["client_credentials"]`, `token_endpoint_auth_methods_supported: ["private_key_jwt"]`, `token_endpoint_auth_signing_alg_values_supported: ["ES256"]`. S3 and S4 add their grants and endpoints.

*Interim login token (until S4)*
- **AC-5**: `POST /auth/login` takes an optional `system` (`VRMS`, `VMMS` or `BMS`). After the password checks out (lockout unchanged), welinc-auth picks the system: the requested one if given; otherwise the only system the user holds; otherwise `VRMS` if held; otherwise the first held in the order `VRMS`, `VMMS`, `BMS`. A user holding no role in the picked system, or no system role at all, gets 403 with the 0001 section 11 body and `code: "NO_SYSTEM_ACCESS"`, and no token. An unknown `system` value gets 400.
- **AC-6**: The interim login token carries `iss` (`AUTH_ISSUER`), `sub`, `aud` (the picked system, a single string), `client_id: "portal"`, `token_use: "user"`, `email`, `roles` (only the picked system's roles, today's shape), `iat`, `exp` (`ACCESS_TOKEN_MINUTES`, default 15) and `jti` (a random uuid). It has no `sid` until S3. Nothing checks `client_id: "portal"` against the client registry until S4. The answer is today's `{ accessToken, user }` plus `system`. `user.roles` still lists every role the user holds. web-vrms needs no change: it decodes the payload, and its `roles` now holds only VRMS roles.
- **AC-7**: The portal sends no `system` on login. It redirects to the address of the `system` in the answer and stores that system in `localStorage` as `welinc_system`, overwritten on every login and cleared wherever `welinc_token` is cleared (logout, the no access path). On a return visit with a stored token that hasn't expired, it redirects to the stored system. With no stored system, it sends the user to `/login`. It no longer decodes the token to choose.

*Checking tokens*
- **AC-8**: welinc-auth checks tokens on its own routes against its own public keys in memory (no HTTP call to itself). It accepts only `alg: ES256`, `typ: at+jwt`, `iss` equal to `AUTH_ISSUER`, and an unexpired `exp` (5 s clock leeway). A user token must have `token_use: user` and `aud` in `VRMS`, `VMMS`, `BMS`. A service token must have `token_use: service` and `aud: AUTH`. `aud` must be a single string, not an array. Anything else gets 401, including an HS256 token or a token with no `token_use`. The optional guard on `forgot-password` treats any token that fails these checks as no token at all, never as an error.
- **AC-9**: On welinc-auth's user token routes, the system is the token's `aud`, with or without a `?system=`. A `?system=` that differs from `aud` gets 403 `WRONG_AUDIENCE`. User admin keeps today's scoping by the admin's system, which is now `aud`. The `Origin`, `Referer`, path, body and first role guessing in `jwt.strategy.ts` is deleted.
- **AC-10**: backend-vrms checks every bearer token with the reference module (AC-25) against `AUTH_JWKS_URL`. It accepts only `alg: ES256`, `typ: at+jwt`, `iss` equal to `AUTH_ISSUER`, `aud: VRMS` and an unexpired `exp` (5 s leeway). A good signature with the wrong `aud` gets 401 with code `WRONG_AUDIENCE`. A service token on a route for people gets 403 `WRONG_TOKEN_USE`. A token that fails any other check gets 401 `Invalid session`. The guard settles `token_use` before the account check, so the account check never sees a service token. Passing user tokens then go through the spec 0009 account check (`/auth/me`) as today.
- **AC-11**: backend-vrms caches the key set for 5 minutes. On a token whose `kid` isn't in the cache, it fetches the set again, at most once a minute. A `kid` still unknown after a fetch gets 401.
- **AC-12**: backend-vrms keeps the last key set it fetched successfully. When a fetch fails (welinc-auth down, a timeout after 3 s, a bad answer), it keeps verifying with that last good set for up to 1 hour after its last successful fetch. `jose`'s remote key set stops serving cached keys once its cache expires, so the verifier wraps it: fetch, keep the result, and verify through `createLocalJWKSet`. With no usable set, or with the token's `kid` missing from a set that couldn't be refreshed, the request gets 503 with code `AUTH_UNAVAILABLE` and the existing "Sign in service unavailable" message, never 401.

*Clients and service tokens*
- **AC-13**: welinc-auth's seed creates the seven clients of 0001 section 4 in `OAuthClient` with their kind, system, grants, user audiences and service scopes. `vrms` gets its public key from `CLIENT_VRMS_JWKS`; every other client gets the key from `CLIENT_<ID>_JWKS` when set (id upper cased, `-` as `_`), else `jwks` stays null. Running the seed again updates kind, system, grants, audiences and scopes in place. It changes `jwks` only when the env value is set, and sets `isActive` only when it creates the row, so a client switched off by hand stays off.
- **AC-14**: `POST /auth/token` takes `application/x-www-form-urlencoded` only. It parses its own body outside the global `ValidationPipe` (which uses `forbidNonWhitelisted`), so every error on this route uses the OAuth body. Any other content type, a missing field, or a repeated field gets 400 `invalid_request`. The fields are `grant_type=client_credentials`, `client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer`, `client_assertion`, `audience`, `scope` (space separated, required) and an optional `client_id`, which must equal the assertion's `iss` (else 401 `invalid_client`). Unknown fields are ignored, as RFC 6749 asks. The answer is `{ access_token, token_type: "Bearer", expires_in, scope }`, where `expires_in` is in seconds and `scope` echoes exactly the scopes requested. The token is a service token per 0001 section 5: `iss`, `sub: client:<id>`, `aud` (the requested audience), `client_id`, `token_use: service`, `scope`, `iat`, `exp` (`SERVICE_TOKEN_MINUTES`, default 5), `jti`. It returns no refresh token.
- **AC-15**: The checks run in this order, and the first failure answers 401 `{ "error": "invalid_client" }`, the same body for every reason:
  1. Decode the header and claims without trusting them. `iss` must name a client whose row is active and has keys.
  2. The header has `alg: ES256`, `typ: JWT`, and a `kid` matching one of that client's registered keys.
  3. The signature is valid for that key.
  4. `sub` equals `iss`.
  5. `aud` is the single string `<AUTH_ISSUER>/token`.
  6. `exp` is in the future, `iat` is present and not later than now, `nbf` (if present) is not later than now, and `exp - iat` is at most 60 s. The 5 s leeway applies to each time check.
  7. `jti` is a string of 1 to 128 characters.
- **AC-16**: Only after the assertion passes are the grant, audience and scope checked:
  - Any grant type other than `client_credentials` gets 400 `unsupported_grant_type` (S3 and S4 add theirs).
  - A grant missing from the client's `grants` gets 400 `unauthorized_client`.
  - An `audience` missing from its `serviceScopes` gets 400 `invalid_target`.
  - A scope not listed for that audience gets 400 `invalid_scope`.
- **AC-17**: The `jti` is recorded last, once every check in AC-15 and AC-16 has passed, so a refused grant or scope doesn't use it up. Its `expiresAt` is the assertion's `exp`. A `jti` this client already used gets 401 `invalid_client`. Two requests with the same client and `jti` at the same moment produce exactly one token; the other gets `invalid_client`. Every 10 minutes, rows whose `expiresAt` is more than a minute in the past are deleted. That minute covers the 5 s leeway with a wide margin.
- **AC-18**: `/auth/token` has two limits; over either one it answers 429 with `Retry-After` (seconds left on the limit's window) and `{ "error": "rate_limited", "error_description": "…" }`:
  - 120 requests a minute per caller address, checked before anything else;
  - 60 a minute per client, counted after the assertion passes, with the key `client:<id>` in the throttler storage.

  The throttler applies to this route only, not globally, so `/auth/login` stays unlimited until S3 and S4. welinc-auth trusts `TRUST_PROXY_HOPS` proxy hops (1 locally for nginx, 2 when hosted for the Container Apps ingress plus nginx), so the address is the real caller's, not the gateway's. A backend calling welinc-auth directly on the internal network is counted by its own address.
- **AC-19**: `GET /auth/users` accepts either a user token holding `ADMIN` in its `aud` (as today) or a service token with `aud: AUTH` and scope `directory.read`. A route marker (`@ServiceScope('directory.read')`) lets the service token in; `RolesGuard` never treats a client as an admin. For a service token, the route answers what an admin of the client's `system` would see, read only. A `?system=` that differs from that system gets 403 `WRONG_AUDIENCE`. Every welinc-auth route without the marker answers a service token with 403 `WRONG_TOKEN_USE`. *Superseded in part by [0005](../0005-user-directory/index.md) AC-9 (2026-11-09): `GET /auth/users` is admin only, and a service token gets 403 `WRONG_TOKEN_USE`. The first sentence no longer holds for this route.*

*VRMS as a client*
- **AC-20**: backend-vrms gets its service token with its own key (`AUTH_CLIENT_ID`, `AUTH_CLIENT_PRIVATE_KEY`), signing a fresh assertion (new `jti`, 60 s life) for every token request with `audience=AUTH` and `scope=directory.read`. It keeps the token until 60 s before it expires. Callers who need a token at the same moment share one request. If welinc-auth answers 401 to a call made with a cached token, backend-vrms drops it, gets a new one and retries once. A 403 is never retried.
- **AC-21**: The mechanic roster (`sync` and `refreshOne`) calls `/auth/users?system=VRMS` with the VRMS service token instead of the caller's token. A Chief Mechanic action that runs `refreshOne` now works. Failing to get a token answers 503 `AUTH_UNAVAILABLE`, as a failed roster call does today. *Superseded by [0005](../0005-user-directory/index.md) AC-21 (2026-11-09): the roster reads welinc-auth's directory (`/auth/directory/*`) with the same service token, not `/auth/users`.*
- **AC-22**: From slice 1, backend-vrms refuses to start when `AUTH_ISSUER`, `AUTH_JWKS_URL` or `AUTH_INTERNAL_URL` is missing, and `AUTH_SERVICE_URL` is renamed `AUTH_INTERNAL_URL`. From slice 2, it also refuses when `AUTH_CLIENT_ID` or `AUTH_CLIENT_PRIVATE_KEY` is missing, or when the private key isn't an EC P-256 private JWK with a `kid` and `alg: ES256`. `AUTH_ISSUER` is an identifier compared character for character, never an address anything fetches. Every service sets the identical string.

*Keys tooling*
- **AC-23**: `npm run keys:dev` in welinc-auth writes a fresh signing key (`status: current`) into `welinc-auth/.env` as `AUTH_SIGNING_KEYS`, a VRMS client key pair (private into `welinc-backend-vrms/.env` as `AUTH_CLIENT_PRIVATE_KEY`, public into `welinc-auth/.env` as `CLIENT_VRMS_JWKS`), and `AUTH_ISSUER=http://localhost:3000/auth` into both `.env` files where missing. It refuses to replace a value already set unless given `--force`. It prints only the new `kid`s, never a key.
- **AC-24**: `npm run keys:rotate -- <env file> <step>` edits the `AUTH_SIGNING_KEYS` line of that env style file (the spec 0008 private secrets file, or a local `.env`):
  - `add` appends a new key as `next` with `addedAt`; it refuses if a `next` key already exists.
  - `promote` makes the `next` key `current` and the old `current` key `retired` with `retiredAt`; it refuses unless the `next` key is at least 60 minutes old.
  - `remove` deletes `retired` keys whose `retiredAt` is at least the longer of `ACCESS_TOKEN_MINUTES` and `SERVICE_TOKEN_MINUTES`, plus 30 minutes, ago; it refuses if none qualify.
  - `promote --now` and `remove --now <kid>` skip the timing checks, for a leaked key. They print a warning: live tokens signed by the removed key stop working, and verifiers may keep accepting that key for up to 5 more minutes from their cache.
  - The waits count from the times the script writes (`addedAt`, `retiredAt`), so every step must be applied with `set-secrets.sh` right away; the script prints that reminder. A new Container Apps revision gets the whole key set at once, so by `promote` time every replica already publishes the `next` key.
  - Each step prints the resulting `kid`s and statuses and the next allowed step with its earliest time, and never prints key material. It reads and writes the plain `KEY=value` line format (the value single quoted), keeps every other line and comment, and writes through a temporary file and a rename. `npm run keys:client -- <client id> <private env file> <public env file>` makes a client key pair the same way, for staging and production.
- **AC-25**: backend-vrms holds the token check as a self contained folder, `src/auth/verify/`, importing nothing from the rest of VRMS. It holds the token verifier (user and service), the guards for routes meant for people and for services (`requireService(scope)`), the assertion signer, and the service token client. Its unit tests cover every rule in AC-10, AC-11, AC-12 and AC-20. A `README.md` in the folder says what to copy, which environment values it needs, and which Jest setting loads `jose`.

*Rotation and observability*
- **AC-26**: An automated test in welinc-auth runs a full rotation (add, promote, remove) and shows that a token signed by the old key keeps verifying while that key is `retired`, a token signed after `promote` carries the new `kid`, and a token signed by a removed key fails.
- **AC-27**: welinc-auth logs one line per service token issued (client, audience, scopes, `kid`, token `jti`) and one per refused assertion (the claimed client id, a reason code such as `bad_signature`, `unknown_kid`, `jti_reused`, `expired`, `bad_audience`, `lifetime_too_long`, `client_inactive`, the caller's address). It never logs a token, an assertion, or any key material. At startup it logs the `kid` and status of each signing key.

## Decision

**Chosen option**: Option 1: `jose` everywhere, keys in the environment, a tested reference module, scripted rotation.

welinc-auth signs with ES256 keys from `AUTH_SIGNING_KEYS` and checks client assertions with `jose`. Every backend checks tokens against the published key set and signs its own assertions with `jose`, starting with VRMS in one hard switch. The other groups copy VRMS's `src/auth/verify/` folder in S11.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` and `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-client-api/`, `.claude/skills/prisma-cli/`) · `docker-patterns` (ask first, for the compose edits; `.claude/skills/docker-patterns/`)

**Decisions made in the spec** (pick, why, runner up):
- **`kid` format**: `<purpose>-<yyyymmdd>-<6 hex>`, e.g. `auth-20261108-3fa9c1`, `vrms-20261108-77b2e0`. People can read the age and owner in a log line. Runner up: the RFC 7638 thumbprint, unique by construction but unreadable in a runbook.
- **Key metadata**: `status`, `addedAt` and `retiredAt` are extra members on each private JWK inside `AUTH_SIGNING_KEYS`. `jose` ignores unknown members and the JWKS route strips them. Runner up: a separate `AUTH_SIGNING_KEY_STATUS` value, which can drift from the keys.
- **Guards without passport**: welinc-auth and backend-vrms drop `passport`, `passport-jwt`, `@nestjs/passport` and `@nestjs/jwt`. The guards call the verifier directly. One less layer to copy for groups without passport. Runner up: a passport custom strategy wrapping `jose`, which keeps the old guard names but adds a dependency for nothing.
- **`jose` and Jest**: `jose` 6, with Jest set to transform it (`transformIgnorePatterns: ["/node_modules/(?!jose/)"]` and `ts-jest` with `allowJs` for `.js`). If that can't load cleanly, pin `jose` 5, which ships CommonJS with the same functions used here. Write down which one in the folder `README.md`.
- **Rate limit**: `@nestjs/throttler` as a guard on `/auth/token` keyed by address, and the per client count done in the token service after the assertion passes, through the throttler's storage. Keying the guard on the claimed client id before it is checked would let anyone use up another client's quota with fake assertions. Runner up: a hand written counter map.
- **`jti` cleanup**: a 10 minute interval started in the token module (`onModuleInit`, cleared on shutdown), with no new scheduling package. Runner up: `@nestjs/schedule`, one more dependency for one job.
- **Service token cache in VRMS**: in memory, one per process, with one shared request in flight. Runner up: none worth it. Tokens are cheap and last 5 minutes.
- **Proxy hops as a setting**: `TRUST_PROXY_HOPS` (1 locally, 2 hosted). One fixed number is wrong in one of the two places. Runner up: reading the address from a header the gateway sets, which is forgeable if the ingress doesn't strip it.
- **Clock leeway**: 5 s everywhere. Containers in one Azure environment share time sync, and 0001's 60 s assertion life leaves no room for minutes of skew.

## Feature design

**Data model sketch** (welinc-auth, one migration, additive):

`OAuthClient`
| Field | Type | Rules |
|---|---|---|
| `id` | `String @id` | client id: `portal`, `vrms`, `vmms`, `bms`, `vmms-mobile`, `vmms-analytics`, `bms-analytics` |
| `kind` | `ClientKind` enum: `FIRST_PARTY_WEB`, `CONFIDENTIAL`, `PUBLIC_NATIVE`, `SERVICE` | required |
| `system` | `SystemType?` | null only for `portal` |
| `grants` | `String[]` | values from `authorization_code`, `refresh_token`, `client_credentials`, `mobile_login`, `sso` |
| `userAudiences` | `String[]` | e.g. `{VRMS}` |
| `serviceScopes` | `Json` (default `{}`) | `{ "<audience>": ["<scope>", ...] }` |
| `redirectUris` | `String[]` (default empty) | filled by S4 |
| `webAddress` | `String?` | filled by S4 |
| `jwks` | `Json?` | `{ "keys": [ public ES256 JWK with kid ] }`, one or two keys |
| `isActive` | `Boolean @default(true)` | |
| `createdAt`, `updatedAt` | `DateTime` | |

`ClientAssertionJti`
| Field | Type | Rules |
|---|---|---|
| `clientId` | `String` | FK to `OAuthClient.id`, `onDelete: Cascade` |
| `jti` | `String` | |
| `expiresAt` | `DateTime` | `@@index` |
| | | `@@id([clientId, jti])` |

One `OAuthClient` has many `ClientAssertionJti` (1:N). Audience values (`VRMS`, `VMMS`, `BMS`, `AUTH`) are checked in code against one constant list, since `AUTH` isn't a `SystemType`.

**Seeded rows** (0001 section 4):
| id | kind | system | grants | userAudiences | serviceScopes |
|---|---|---|---|---|---|
| `portal` | `FIRST_PARTY_WEB` | null | `sso` | none | `{}` |
| `vrms` | `CONFIDENTIAL` | `VRMS` | `authorization_code`, `refresh_token`, `client_credentials` | `VRMS` | `{ "AUTH": ["directory.read", "directory.contact"] }` |
| `vmms` | `CONFIDENTIAL` | `VMMS` | same | `VMMS` | same |
| `bms` | `CONFIDENTIAL` | `BMS` | same | `BMS` | same |
| `vmms-mobile` | `PUBLIC_NATIVE` | `VMMS` | `mobile_login`, `refresh_token` | `VMMS` | `{}` |
| `vmms-analytics` | `SERVICE` | `VMMS` | `client_credentials` | none | `{ "AUTH": ["directory.read"] }` |
| `bms-analytics` | `SERVICE` | `BMS` | `client_credentials` | none | `{ "AUTH": ["directory.read"] }` |

`directory.contact` is listed now so the row matches the contract. Nothing accepts it until S6.

**`AUTH_SIGNING_KEYS` shape**:
```json
{ "keys": [
  { "kty": "EC", "crv": "P-256", "x": "…", "y": "…", "d": "…", "kid": "auth-20261108-3fa9c1",
    "alg": "ES256", "status": "current", "addedAt": "2026-11-08T09:00:00Z" },
  { "kty": "EC", "crv": "P-256", "x": "…", "y": "…", "d": "…", "kid": "auth-20261001-a1b2c3",
    "alg": "ES256", "status": "retired", "addedAt": "2026-10-01T09:00:00Z", "retiredAt": "2026-11-08T10:00:00Z" }
] }
```
Stored on one line in env files. `AUTH_CLIENT_PRIVATE_KEY` is one private JWK object with `kid` and `alg`. `CLIENT_<ID>_JWKS` is `{ "keys": [ public JWK ] }`.

**State transitions** (a signing key): (none) → `next` (via `add`) → `current` (via `promote`, at least 60 minutes after `add`) → `retired` (when the next key is promoted) → removed (via `remove`, at least `ACCESS_TOKEN_MINUTES` plus 30 minutes after `retiredAt`). With `--now`, `promote` and `remove` skip their waits.

**API surface** (welinc-auth unless marked):
| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/.well-known/jwks.json` | GET | none | `{ keys }` public JWKs | none | none |
| `/auth/.well-known/oauth-authorization-server` | GET | none | RFC 8414 metadata (AC-4) | none | none |
| `/auth/login` | POST | `email`, `password`, `system?` | `{ accessToken, system, user }` | none | 401 bad credentials, 403 locked (unchanged), 403 `NO_SYSTEM_ACCESS`, 400 unknown system |
| `/auth/token` | POST form | `grant_type=client_credentials`, `client_assertion_type`, `client_assertion`, `audience`, `scope` | `{ access_token, token_type, expires_in, scope }` | client assertion | 401 `invalid_client`, 400 `unauthorized_client`, `invalid_target`, `invalid_scope`, `unsupported_grant_type`, `invalid_request`, 429 `rate_limited` |
| `/auth/users` | GET | `system?` | unchanged | admin user token only since [0005](../0005-user-directory/index.md) AC-9 (was: or service token `aud: AUTH` with `directory.read`) | 403 `WRONG_AUDIENCE`, 403 `WRONG_TOKEN_USE` |
| every other user route | any | unchanged | unchanged | user token, system = `aud` | 401, 403 `WRONG_AUDIENCE`, 403 `WRONG_TOKEN_USE` |
| backend-vrms, every protected route | any | bearer user token | unchanged | user token `aud: VRMS` | 401 `WRONG_AUDIENCE`, 403 `WRONG_TOKEN_USE`, 503 `AUTH_UNAVAILABLE` |

Error bodies follow 0001 section 11: Nest's body plus `code` on normal routes, the OAuth `{ error, error_description }` on `/auth/token`. A missing or malformed form field on `/auth/token` is 400 `invalid_request`.

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| Sign any token | private key, `kid` | the `current` key in `AUTH_SIGNING_KEYS` |
| Sign any token | `iss` | `AUTH_ISSUER` |
| Sign any token | `jti` | `crypto.randomUUID()` at signing |
| Login token | `aud` | the AC-5 pick, from the `system` input and the user's `UserRoleAssignment` rows |
| Login token | `roles` | the user's role assignments filtered to `aud` |
| Login token | `client_id` | fixed `portal` until S4 |
| Login token | `exp` | now plus `ACCESS_TOKEN_MINUTES` (default 15) |
| Login answer | `system` | the same AC-5 pick |
| Portal redirect | target address | `SUBSYSTEMS[system].url` in the portal, keyed by the answer's `system` |
| JWKS | public keys | `AUTH_SIGNING_KEYS` with `d`, `status`, `addedAt`, `retiredAt` removed, keys with any status |
| Metadata | endpoint addresses | derived from `AUTH_ISSUER` |
| Check an assertion | client keys | `OAuthClient.jwks` for the client named by `iss` |
| Check an assertion | expected `aud` | `<AUTH_ISSUER>/token` |
| Check an assertion | seen before? | `ClientAssertionJti` (`clientId`, `jti`) |
| Record a `jti` | `expiresAt` | the assertion's `exp` |
| Service token | `aud`, `scope` | the `audience` and `scope` inputs, after checking `OAuthClient.serviceScopes` |
| Service token | `sub`, `client_id` | the checked client id |
| Service token | `exp`, `expires_in` | now plus `SERVICE_TOKEN_MINUTES` (default 5) |
| `/auth/users` with a service token | system | `OAuthClient.system` of the token's `client_id` |
| welinc-auth user routes | system | the token's `aud` |
| Rate limit before checks | address | `req.ip` with `trust proxy` set to `TRUST_PROXY_HOPS` |
| Rate limit after checks | client | the checked client id, key `client:<id>` |
| Service token on `/auth/users` | the list | today's admin scoping (`user-scope.ts`) run for `OAuthClient.system` |
| VRMS token request | `audience`, `scope` | fixed `AUTH`, `directory.read` |
| VRMS token check | public keys | `AUTH_JWKS_URL`, cached by `jose`'s remote key set |
| VRMS token check | expected `iss`, `aud` | `AUTH_ISSUER`, fixed `VRMS` |
| VRMS assertion | `iss`, `sub` | `AUTH_CLIENT_ID` |
| VRMS assertion | key, `kid` | `AUTH_CLIENT_PRIVATE_KEY` |
| VRMS assertion | `aud` | `<AUTH_ISSUER>/token` |
| VRMS token request | address | `<AUTH_INTERNAL_URL>/auth/token` |
| `keys:rotate` timing | key age | `addedAt` and `retiredAt` on each key; token life from `ACCESS_TOKEN_MINUTES` in the same file, default 15 |

**Key invariants**:
- Exactly one `current` signing key at any time. welinc-auth won't start otherwise.
- No private key member (`d`) ever leaves welinc-auth: not in the JWKS, a log line or an error.
- A token is accepted only with `alg: ES256`. The verifiers pin the algorithm, so `none` or HS256 can never pass.
- A `jti` is used at most once per client. The database primary key enforces it, not a read then a write.
- welinc-auth never holds a client's private key. Only public keys sit in `OAuthClient.jwks`.
- The `src/auth/verify/` folder imports nothing from the rest of backend-vrms.

**Security model**:
- Only welinc-auth can sign user or service tokens. Every other service holds public keys only, plus its own client key, which proves who it is to welinc-auth and signs nothing else.
- A user token works only in its `aud` system. A service token works only at its `aud`, for its scopes.
- `GET /auth/users` with a service token shows only the users of the client's own system, the same filter an admin of that system gets today (`user-scope.ts`).
- Client assertion failures look the same from outside (`invalid_client`), so a caller can't probe which check failed. The reason is in the log only.
- A leaked signing key: `keys:rotate add`, `promote --now`, `remove --now <kid>`, then `set-secrets.sh`. Everyone signed by the leaked key logs in again. A leaked client key: set `isActive` false on that client or register a new key and seed again.
- Compliance scope: staff names, emails and roles, no regulated data. Unchanged from spec 0008.

**Configuration required**:

welinc-auth (`.env.example` documents each; real values in `.env` locally and in Container Apps secrets when hosted):
- `AUTH_ISSUER`: the issuer from 0001 section 1 (`http://localhost:3000/auth` locally). An identifier, never fetched. Not secret.
- `TRUST_PROXY_HOPS`: proxy hops in front of welinc-auth (1 locally, 2 hosted).
- `AUTH_SIGNING_KEYS`: the private signing keys with their status (secret).
- `CLIENT_VRMS_JWKS`, and later `CLIENT_VMMS_JWKS`, `CLIENT_BMS_JWKS`, `CLIENT_VMMS_ANALYTICS_JWKS`, `CLIENT_BMS_ANALYTICS_JWKS`: each client's public keys, read by the seed. Not secret, but kept beside the secrets so the seed has one source.
- `ACCESS_TOKEN_MINUTES` (15), `SERVICE_TOKEN_MINUTES` (5).
- Removed: `JWT_SECRET`, `JWT_REFRESH_SECRET`, `JWT_ACCESS_EXPIRY`, `JWT_REFRESH_EXPIRY`.

backend-vrms:
- `AUTH_ISSUER`, `AUTH_JWKS_URL` (`http://auth-service:3001/auth/.well-known/jwks.json` in compose), `AUTH_INTERNAL_URL` (renamed from `AUTH_SERVICE_URL`), `AUTH_CLIENT_ID` (`vrms`), `AUTH_CLIENT_PRIVATE_KEY` (secret).
- Removed: `JWT_SECRET`.

Compose (`docker-compose.shared.yml`, `docker-compose.vrms.yml`): drop the `JWT_*` lines; set only the values that aren't secret (`AUTH_ISSUER`, `AUTH_JWKS_URL`, `AUTH_INTERNAL_URL`, `AUTH_CLIENT_ID`) in `environment`. Keys come from each repo's `.env` through the existing `env_file`.

New packages: `jose` (welinc-auth, backend-vrms), `@nestjs/throttler` (welinc-auth). Removed: `passport`, `passport-jwt`, `@nestjs/passport`, `@nestjs/jwt`, `@types/passport-jwt` (both repos, once nothing imports them).

**Critical test scenarios**:
- Happy path: log in at the portal as a VRMS mechanic, land in VRMS, and load the ticket list. The token in the URL has `aud: VRMS` and an ES256 header with the current `kid`. Verifies **AC-1**, **AC-5**, **AC-6**, **AC-7**, **AC-10**.
- Wrong audience: a valid BMS token (log in with `system: BMS` as a user holding both) sent to backend-vrms gets 401 `WRONG_AUDIENCE`. Verifies **AC-10**.
- Old token: an HS256 token signed with the old dev secret gets 401 at welinc-auth and at backend-vrms. Verifies **AC-8**, **AC-10**.
- Algorithm confusion: a token with `alg: none`, and an HS256 token whose secret is the public key, both fail. Verifies **AC-8**, **AC-10**.
- Bad config: welinc-auth started with two `current` keys, or a public only key, exits with a clear message. Verifies **AC-2**.
- Rotation with no logout: the AC-26 test, plus backend-vrms accepting a token whose new `kid` it hasn't cached (one refetch). Verifies **AC-11**, **AC-24**, **AC-26**.
- welinc-auth down: with no cached key, backend-vrms answers 503 `AUTH_UNAVAILABLE`, not 401. Verifies **AC-12**.
- Service token happy path: an admin presses sync in VRMS settings, and the mechanic list matches welinc-auth. The log shows one issued service token for `vrms`. Verifies **AC-14**, **AC-19**, **AC-21**, **AC-27**.
- Assertion replay: sending the same assertion twice, including twice at the same moment, gives one token and one `invalid_client`. Verifies **AC-15**, **AC-17**.
- Assertion checks: wrong `aud`, a lifetime of 61 s, an unknown `kid`, a client with null `jwks`, a forged signature: each gets `invalid_client` and a distinct reason in the log. Verifies **AC-15**, **AC-27**.
- Scope limits: `vmms-analytics` asking for `directory.contact` gets `invalid_scope`; any client asking for `audience=VMMS` gets `invalid_target`. Verifies **AC-16**.
- Permission: a service token on `/auth/me` gets 403 `WRONG_TOKEN_USE`; a VRMS admin user token with `?system=BMS` on `/auth/users` gets 403 `WRONG_AUDIENCE`. Verifies **AC-9**, **AC-19**.
- Rate limit: the 61st token request from `vrms` within a minute gets 429 with `Retry-After`. Verifies **AC-18**.
- Chief Mechanic: an action that calls `refreshOne` as a Chief Mechanic no longer fails on welinc-auth's admin only route. Verifies **AC-21**.

## Build plan

Tracer Bullet: the first slice is the whole hard switch, end to end through welinc-auth, backend-vrms, the portal and compose, because there is no dual run. It ships as four pull requests merged together (welinc-auth, backend-vrms and web-portal into `development`, and the workspace repo for the compose files). Each later slice thickens one layer and is proven on VRMS.

**Slice 1: ES256 end to end (the hard switch)**
1. In welinc-auth, add `jose` and set Jest to load it (the decision above). Write `keys:dev` and the key loader that checks `AUTH_SIGNING_KEYS` at startup, with the self test, satisfies **AC-2**, **AC-23**
1a. Add a test key fixture in welinc-auth and in backend-vrms (a fixed test only key pair, generated at test start, never committed as a `.env` value). Move every existing spec that builds a `JwtService` or `JWT_SECRET` config onto it, satisfies **AC-1**, **AC-8**, **AC-10**
2. Sign login tokens with the `current` key and the AC-6 claims. Add the AC-5 system pick, the `system` input and the answer field, satisfies **AC-1**, **AC-5**, **AC-6**
3. Add the JWKS and metadata routes, satisfies **AC-3**, **AC-4**
4. Replace welinc-auth's passport strategy and guards with a `jose` guard on its in memory public keys. Take the system from `aud`, reject a different `?system=`, delete the guessing, and handle service tokens. Remove `@nestjs/jwt` and the passport packages, satisfies **AC-8**, **AC-9**
5. In backend-vrms, build `src/auth/verify/` (verifier and guards first), swap the passport strategy for it in the existing guard ahead of the account check, and add the slice 1 startup checks and the `AUTH_SERVICE_URL` rename, satisfies **AC-10**, **AC-11**, **AC-12**, **AC-22**, **AC-25**
6. In the portal, redirect by the answer's `system` and store it; stop decoding the token to choose, satisfies **AC-7**
7. Update both compose files and every `.env.example`, removing the `JWT_*` values, satisfies **AC-1**, **AC-22**
8. Run lint, typecheck, build and tests in all three repos. Then log in end to end locally with a fresh `keys:dev`, satisfies **AC-1**, **AC-10**

**Slice 2: clients and service identity**
9. Write the migration for `OAuthClient`, `ClientKind` and `ClientAssertionJti`, and seed the seven clients from env, satisfies **AC-13**
10. Build `POST /auth/token` with the client credentials grant, the assertion checks, the `jti` record and its cleanup interval, satisfies **AC-14**, **AC-15**, **AC-16**, **AC-17**
11. Add `@nestjs/throttler` (on this route only) and `trust proxy` from `TRUST_PROXY_HOPS`, the address guard on `/auth/token` and the per client count, with a test that sends `X-Forwarded-For`, satisfies **AC-18**
12. Let `GET /auth/users` accept a `directory.read` service token scoped to the client's system, and make the other user routes refuse service tokens, satisfies **AC-19**
13. Add the logging of grants, refusals and startup keys, satisfies **AC-27**
14. In backend-vrms, add the assertion signer and the service token client to `src/auth/verify/`, and switch the mechanic roster's `sync` and `refreshOne` to it, and add the slice 2 startup checks for `AUTH_CLIENT_ID` and `AUTH_CLIENT_PRIVATE_KEY`, satisfies **AC-20**, **AC-21**, **AC-22**, **AC-25**

**Slice 3: rotation and handover**
15. Write `keys:rotate` and `keys:client` with their refusals and the `--now` path, satisfies **AC-24**
16. Write the AC-26 rotation test in welinc-auth, satisfies **AC-26**
17. Write `src/auth/verify/README.md` (what to copy, the env values, the Jest setting, baseline versions: Node 24, Nest 11, `jose` 6), satisfies **AC-25**
18. Write `welinc-auth/docs/keys.md`, a runbook covering local setup, a planned rotation, a leaked signing key and a leaked client key. Spec 0008's `infra/RUNBOOK.md` links to it when that file is written, satisfies **AC-24**

## Migration plan

**Strategy**: big bang (a hard switch, as 0001 decided: VRMS and the portal are the only real users, and BMS's local HS256 check was never connected).
**Phases**:
1. Merge slice 1's four pull requests together. Locally, everyone runs `npm run keys:dev` once and rebuilds the auth and VRMS containers.
2. Hosted (when spec 0008's environments exist): generate keys per environment with `keys:rotate <private file> add` then `promote --now` (there is no old key to protect), `keys:client vrms`, run `set-secrets.sh`, deploy auth first, then backend-vrms, then the portal. Old tokens stop working, so everyone logs in once. That order is safe: the old portal still works against the new auth (it reads the filtered roles and redirects to that system), while the new portal against the old auth would break. web-vrms needs no deploy.
3. Slices 2 and 3 are additive (new tables, a new route, a new token path) and deploy normally.
4. One planned rotation on staging before launch, following `docs/keys.md`, with someone logged in throughout to confirm nobody is logged out.

**Rollback**: revert the slice 1 merges in all four repos and put `JWT_SECRET` back. Keep the old private file values until slice 1 has run on staging for a day. The two tables from slice 2 are additive and can stay. A rollback logs everyone out a second time, since ES256 tokens stop working too.
**Risks**: a backend deployed before welinc-auth fails every request (deploy order above). A missing env value stops a service at startup, which is loud by design. BMS's and VMMS's local setups that verify HS256 tokens from welinc-auth stop matching, so they must be told before the merge.

## Consequences

**Positive**:
- No service but welinc-auth can mint a token, and a token from one system is refused in another.
- A key can be swapped with nobody logged out, and a leaked one killed in minutes, with the dangerous steps refused by the script.
- VRMS's background roster work no longer borrows a user's token, which fixes the Chief Mechanic `refreshOne` path.
- The other groups get a tested check to copy, written for one library that fits all their stacks, `bms-gateway` included.

**Negative / tradeoffs**:
- Everyone is logged out once at the switch, locally and on each environment.
- The signing key lives in an environment secret, so anyone who can read the Container App's secrets can read it. Key Vault signing would close that, at a cost this deadline can't carry.
- `jose` 6 is ESM only, which costs a Jest setting in every repo that tests it.
- The per address limit is in memory, per replica. With more than one welinc-auth replica, the real limit is the number of replicas times 120. Fine at one replica (spec 0008).
- Rate limiting and `trust proxy` arrive in welinc-auth with this spec, but only `/auth/token` uses them until S3 and S4 add the login limits.

**Neutral**:
- `aud` arrives before S4, so S4 changes only how the token travels, not what it says.
- The portal's choice of system moves to welinc-auth until S4's launcher replaces it.
- welinc-auth and backend-vrms lose passport and `@nestjs/jwt` entirely.

## Follow-up

- [x] Update 0001 (additive, contract version stays 1): section 5's key paragraph names `jose` instead of passport with `jwks-rsa`; section 10's `/auth/login` row gets the interim `system` input, the `system` answer field and 403 `NO_SYSTEM_ACCESS` until S4; section 5's client credentials grant marks `scope` required; section 12 adds the 120 a minute per address limit on `/auth/token` and the `rate_limited` body; user tokens carry no `sid` until S3; section 15 adds `TRUST_PROXY_HOPS` to welinc-auth's configuration.
- [ ] Tell the BMS and VMMS groups before slice 1 merges: HS256 and `JWT_SECRET` from welinc-auth stop working, and their local token checks must wait for S11. Add the line to `docs/_private/vrms/shared-services-questions.md`.
- [ ] S11 guide: copy `src/auth/verify/`, generate the client key with `keys:client`, and move to Node 24 (`welinc-backend-vmms-analytics-ai` pins Node 20, end of life since April 2026; `bms-gateway` allows it).
- [ ] S12 (seed accounts) builds on this spec's client seed and must keep it.
- [ ] Spec 0008: replace the `JWT_SECRET` row in its configuration table and the "rotating the JWT secret" runbook step with `AUTH_SIGNING_KEYS`, `CLIENT_VRMS_JWKS`, `AUTH_CLIENT_PRIVATE_KEY` and a link to `docs/keys.md`.
- [ ] After the capstone: consider Key Vault signing (rationale.md, Option 3) and a calendar rotation.
- [ ] `jose` and `@nestjs/throttler` have no Agent Skill installed (deferred on 2026-11-08). Look again if either causes trouble in the build.
- [ ] `/sync` after the build: welinc-auth's and backend-vrms's `AGENTS.md` (auth module and env sections) and the VRMS `AGENTS.md` stack notes on the token check.
