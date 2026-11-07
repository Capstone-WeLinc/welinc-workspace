# Verify: signing keys and service identity · spec 0002 · updated 2026-11-08
_Steps derived from spec 0002 acceptance criteria and its Value sourcing table. `/check verify` runs these; `/test` locks the durable ones. A ticked step was run end to end through the local stack during `/develop` on 2026-11-08 (marked "seen")._

## UI / manual

- [ ] Portal: sign in as a VRMS mechanic → you land in VRMS (`:8001`) and the ticket list loads. `localStorage.welinc_system` is `VRMS`; the token in the URL has `aud: VRMS` and an ES256 header with the current `kid` → AC-1, AC-5, AC-6, AC-7
- [ ] Portal: sign in as a user who holds only BMS (`ops.user@welinc.com`) → you are sent to the BMS address (`:8003`), and `welinc_system` is `BMS` → AC-5, AC-7
- [ ] Portal: open `http://localhost:8000/` again with the stored token unexpired → it goes straight back to the stored system, without decoding the token to choose → AC-7
- [ ] Portal: delete `welinc_system` by hand, keep `welinc_token`, open `/` → you land on `/login`, with no loop between `/` and `/login` → AC-7
- [ ] Portal: an old HS256 token left in `welinc_token` from before the switch → `/` sends you to `/login` (no stored system) → AC-7
- [ ] Portal: Log out, and sign out for inactivity → `welinc_token`, `welinc_user` and `welinc_system` are all cleared → AC-7
- [ ] Portal: sign in with an account holding no system role → "no assigned subsystem access" message, nothing stored → AC-5, AC-7
- [ ] VRMS Settings, Users: an Admin presses sync → the mechanic list matches welinc-auth, and the auth log shows one `issued service token client=vrms` line → AC-14, AC-19, AC-21, AC-27
- [ ] Grant the Chief Mechanic `users.manage` in the matrix, then release a deactivated mechanic's tickets as the Chief → it works (before spec 0002 it failed on welinc-auth's admin only route); take the right away again after → AC-21
- [ ] Staging (once spec 0008 exists): one planned rotation per `welinc-auth/docs/keys.md`, with someone signed in to VRMS throughout → nobody is sent to the login page → AC-24, AC-26

## Commands

Through the gateway at `http://localhost:3000` unless a step says otherwise.

*Signing and publishing*
- [x] `GET /auth/.well-known/jwks.json` → 200, `Cache-Control: public, max-age=300`, every key with `kty, crv, x, y, kid, alg: ES256, use: sig`, no `d`, `status`, `addedAt` or `retiredAt` (seen) → AC-3
- [x] `GET /auth/.well-known/oauth-authorization-server` → `issuer` equals `AUTH_ISSUER`, `token_endpoint` and `jwks_uri` derived from it, `client_credentials`, `private_key_jwt`, `ES256` (seen) → AC-4
- [ ] `grep -rn "JWT_SECRET\|JWT_REFRESH_SECRET\|JWT_ACCESS_EXPIRY\|JWT_REFRESH_EXPIRY\|passport\|@nestjs/jwt" welinc-auth/src welinc-backend-vrms/src welinc-auth/.env.example welinc-backend-vrms/.env.example docker-compose.shared.yml docker-compose.vrms.yml` → no match → AC-1
- [ ] Start welinc-auth with each bad `AUTH_SIGNING_KEYS` (missing, not JSON, two `current`, none `current`, a public only key, `alg: ES384`, `use: enc`, a shared `kid`, status `old`, a private part from another key) and with no `AUTH_ISSUER` → it exits before listening, the message names the problem and never a key → AC-2
- [x] Startup log shows `signing key <kid> is current` for each key (seen) → AC-27

*Login token*
- [x] `POST /auth/login` as `vrms.admin@welinc.com` and as `vrms.chief@welinc.com` → 200 with `{ accessToken, system: "VRMS", user }`; the token has `iss`, `sub`, `aud: VRMS`, `client_id: portal`, `token_use: user`, only VRMS `roles`, a 15 minute life, a `jti`, no `sid` (seen) → AC-5, AC-6
- [ ] `POST /auth/login` as a user holding VRMS and BMS, with no `system` → `system: VRMS`; with `system: BMS` → `aud: BMS`, BMS roles only, while `user.roles` lists both → AC-5, AC-6
- [x] `POST /auth/login` as the VRMS admin with `system: BMS` → 403 `NO_SYSTEM_ACCESS`, no token (seen) → AC-5
- [x] `POST /auth/login` with `system: XYZ` → 400 (seen) → AC-5
- [ ] Five wrong passwords → the account still locks; a wrong password never reaches the system pick → AC-5

*Checking tokens*
- [x] VRMS token on `GET /auth/me?system=VRMS` → 200; on `?system=BMS` → 403 `WRONG_AUDIENCE` (seen) → AC-9
- [x] VRMS token on `GET /vrms/repairs` → 200 (seen) → AC-10
- [x] HS256 token signed with the old dev secret → 401 at `/auth/me` and at `/vrms/repairs` (seen) → AC-8, AC-10
- [ ] A BMS user token (log in with `system: BMS` as a user holding both) on `/vrms/repairs` → 401 `WRONG_AUDIENCE` → AC-10
- [ ] A token with `alg: none`, and an HS256 token keyed with the public JWK → 401 at both services → AC-8, AC-10
- [ ] `POST /auth/forgot-password` with a broken token → answers as for no token (never 401) → AC-8
- [ ] Stop `auth-service`, restart `vrms-backend` (empty key cache), call `/vrms/repairs` → 503 `AUTH_UNAVAILABLE`, not 401 → AC-12
- [ ] With welinc-auth stopped after VRMS cached the keys, a fresh token is still refused only by the account check (503 from `/auth/me`), never by the key check, for up to an hour → AC-12
- [ ] Rotate locally (`keys:rotate .env add`, `promote --now`, recreate auth-service), then use a token with the new `kid` on `/vrms/repairs` before 5 minutes pass → 200 after one refetch → AC-11

*Clients and service tokens*
- [x] `select id, kind, system, jwks is not null, is_active from oauth_clients` → the seven clients; only `vrms` has keys locally; the user count is unchanged after `npm run seed:clients` (seen) → AC-13
- [ ] Set `is_active = false` on `vrms`, run `npm run seed:clients` → it stays `false`; set it back → AC-13
- [x] Good assertion from VRMS → 200 `{ access_token, token_type, expires_in: 300, scope }`, no refresh token (seen) → AC-14
- [x] JSON body on `/auth/token` → 400 `invalid_request` (seen) → AC-14
- [ ] `/auth/token` with a missing `audience`, a repeated `scope`, and an unknown extra field → 400 `invalid_request`, 400 `invalid_request`, and the extra field ignored → AC-14
- [ ] `client_id=bms` beside a VRMS assertion → 401 `invalid_client` → AC-14
- [x] Lifetime 61 s and the wrong `aud` → 401 `invalid_client`, the same body, with `lifetime_too_long` and `bad_audience` in the log (seen) → AC-15, AC-27
- [ ] An unknown `kid`, a forged signature, and a client whose `jwks` is null → `invalid_client`, with `unknown_kid`, `bad_signature` and `client_inactive` in the log → AC-15, AC-27
- [x] `grant_type=password`, `audience=VMMS`, `scope=directory.write` → `unsupported_grant_type`, `invalid_target`, `invalid_scope` (seen) → AC-16
- [x] The same assertion twice at the same moment → one 200, one 401; a third time → 401; `jti_reused` in the log (seen) → AC-17
- [x] An assertion first refused for its scope, then sent with the right scope → 200 (the refusal didn't use the `jti` up) (seen) → AC-17
- [ ] Ten minutes after a burst of tokens, `select count(*) from client_assertion_jtis where expires_at < now() - interval '1 minute'` → 0 → AC-17
- [ ] 61 good requests from `vrms` within a minute → the 61st gets 429 with `Retry-After` and `{ "error": "rate_limited" }` → AC-18
- [ ] 121 requests a minute from one address → 429 before any check; the log shows the caller's real address, not the gateway's → AC-18
- [x] VRMS service token on `/auth/users?system=VRMS` → 200, VRMS users only; on `?system=BMS` → 403 `WRONG_AUDIENCE`; on `/auth/me` and `/auth/users/lookup` → 403 `WRONG_TOKEN_USE` (seen) → AC-19
- [x] An `aud: AUTH` service token on `/vrms/repairs` → 401 `WRONG_AUDIENCE` (seen) → AC-10
- [x] Three admin syncs in a row after a VRMS restart → one `issued service token` line (the token is kept) (seen) → AC-20, AC-21
- [ ] Stop auth-service, press sync → 503 `AUTH_UNAVAILABLE` → AC-21
- [ ] Start backend-vrms without each of `AUTH_ISSUER`, `AUTH_JWKS_URL`, `AUTH_INTERNAL_URL`, `AUTH_CLIENT_ID`, `AUTH_CLIENT_PRIVATE_KEY`, and with a public only client key → it refuses to start, naming the value → AC-22

*Keys tooling*
- [x] `keys:dev` on empty files → writes the four values and prints only kids; a second run → refused without `--force` (seen on scratch files) → AC-23
- [x] `keys:rotate` add, add again, early promote, promote `--now`, remove with nothing retired, remove `--now <kid>`, remove `--now <current kid>` → each answers as `docs/keys.md` says, keeps other lines, prints no key (seen on scratch files) → AC-24
- [x] `keys:client vrms` twice, and with an unknown client → written, then refused without `--force`, then refused (seen on scratch files) → AC-24
- [ ] `npm test` in welinc-auth → `rotation.spec.ts` passes the full add, promote, remove run → AC-26
- [ ] `src/auth/verify/` imports nothing outside itself: `grep -rn "from '\.\./" welinc-backend-vrms/src/auth/verify --include=*.ts | grep -v "testing/"` → no match → AC-25

## Value sourcing coverage

| Value | Checked by |
|---|---|
| Signing key and `kid` from the `current` key | the login header step, the local rotation step |
| `iss` from `AUTH_ISSUER` | the login claims step; change `AUTH_ISSUER` on one side only → every token refused |
| `jti` per token | the login claims step |
| Login `aud` and answer `system` from the pick | the two system pick steps |
| Login `roles` filtered to `aud` | the VRMS and BMS login steps |
| `client_id: portal` | the login claims step |
| `exp` from `ACCESS_TOKEN_MINUTES` | set it to 5, log in → `exp - iat` is 300 |
| Portal target from `SUBSYSTEMS[system].url` | the portal VRMS and BMS steps |
| JWKS from the key set, private members removed | the JWKS step |
| Metadata addresses from `AUTH_ISSUER` | the metadata step |
| Client keys from `OAuthClient.jwks` | the null `jwks` step |
| Assertion `aud` from `<AUTH_ISSUER>/token` | the wrong `aud` step |
| Replay from `ClientAssertionJti` | the replay steps |
| `expiresAt` from the assertion `exp` | the sweep step |
| Service token `aud` and `scope` from the request, checked against `serviceScopes` | the target and scope steps |
| Service token `sub` and `client_id` from the checked client | `decodeJwt` on a service token → `sub: client:vrms` |
| Service `exp` from `SERVICE_TOKEN_MINUTES` | the good assertion step (`expires_in: 300`) |
| `/auth/users` system from `OAuthClient.system` | the service token directory steps |
| welinc-auth user route system from `aud` | the `/auth/me?system=` steps |
| Rate limit address from `req.ip` with `TRUST_PROXY_HOPS` | the 121 requests step; set `TRUST_PROXY_HOPS: 0` → every caller counts as the gateway |
| Per client key `client:<id>` | the 61 requests step, then another client still succeeds |
| VRMS token request `audience` and `scope` fixed | the sync step (log shows `aud=AUTH scope="directory.read"`) |
| VRMS check keys from `AUTH_JWKS_URL` | the welinc-auth down step |
| VRMS expected `iss` and `aud` | the BMS token and `aud: AUTH` steps |
| VRMS assertion `iss`, `sub`, key and `kid` from `AUTH_CLIENT_ID` and `AUTH_CLIENT_PRIVATE_KEY` | the sync step; set `AUTH_CLIENT_ID` to `bms` → sync answers 503 and the log shows `invalid_client` |
| VRMS token address from `AUTH_INTERNAL_URL` | the startup check step |
| `keys:rotate` timing from `addedAt`, `retiredAt` and token life | the early promote and remove refusals |

## Acceptance criteria coverage

- AC-1 … login header, grep · AC-2 … bad key sets · AC-3 … JWKS · AC-4 … metadata · AC-5 … system pick and 403 · AC-6 … claims · AC-7 … portal steps · AC-8 … HS256, `alg: none`, forgot password · AC-9 … `?system=` steps · AC-10 … VRMS token steps · AC-11 … local rotation refetch · AC-12 … welinc-auth down · AC-13 … client rows, `is_active` kept · AC-14 … token answer, form errors · AC-15 … assertion refusals · AC-16 … grant, target, scope · AC-17 … replay, sweep · AC-18 … both 429s · AC-19 … service token directory steps · AC-20 … kept token · AC-21 … sync, Chief release, sync with auth down · AC-22 … backend-vrms startup checks · AC-23 … `keys:dev` · AC-24 … `keys:rotate`, `keys:client`, staging rotation · AC-25 … the import check, the README · AC-26 … `rotation.spec.ts`, staging rotation · AC-27 … log lines
