# 0001. Shared services contract: rationale

The decision record behind [index.md](index.md). `/develop` reads the index; this file is for the people who weigh, review or defend the decision.

## Context

> ⚠️ Premise note: this turns welinc-auth into a small authorization server, which is close to the "reinventing auth" failure pattern (refresh rotation, code flow and replay checks are each a place to get breached). It is still the right framing here because welinc-auth already owns accounts, lockout, OTP, admin scoping and the change record (specs 0009 and 0011), so the question is how to extend it safely, not whether to build auth. The guard is to follow the published standards to the letter (OAuth 2.1, PKCE, `private_key_jwt`, JWKS), use proven libraries for every signature, write no crypto of our own, and run every S row at the GA workflow. A hosted identity provider was weighed as Option 3 below.

The WeLinc suite is three systems built by three student groups (VRMS, VMMS, BMS) on shared auth, portal and gateway services. Only VRMS actually runs on them today. VMMS keeps a full copy of auth (users, roles, refresh tokens bound to web or mobile, login activity, phone verification, audit logs) that its web and mobile apps call. BMS verifies welinc-auth tokens with the shared `JWT_SECRET`, but its gateway reads the auth database directly, its web app calls three profile routes that exist nowhere, and its auth copy in the old `welinc-backend` repo has the admin checks removed for local testing. The full inventory is under *Current state* below.

The forces: every service holds one HS256 secret, so any of about eight services can mint a token for any system, and a leak anywhere is a leak everywhere. Tokens travel in the URL (`?token=`) and sit in `localStorage`, where any injected script can read them. welinc-auth guesses which system a request is for from `Origin`, `Referer` and the path. Ports clash (VMMS on the gateway's 3000, both analytics services on auth's 3001, BMS booking on VRMS's 3002), and the gateway knows only three routes. The other groups are waiting on a supported contract (BMS says so in its code), and the deadline is a deployed suite by the end of November 2026.

Hosting is settled by VRMS spec 0008 (Azure Static Web Apps for web apps, Container Apps for services, one public gateway), which planned on default Azure addresses. Those addresses put every web app and the gateway on different sites, which decides what kind of browser session is possible.

Without a contract, each group keeps guessing: VMMS keeps its copy, BMS keeps reading the auth database, and S2 to S12 each get designed in isolation with nothing holding them together.

## Options considered

### Option 1: welinc-auth as a small authorization server, token per system (chosen)

welinc-auth issues ES256 tokens with an audience per system, publishes its public keys, runs the OAuth authorization code flow with PKCE for web logins (exchanged on each system's backend, which keeps the refresh token in an HttpOnly cookie), gives the native mobile app a first party login, authenticates backends with signed client assertions, and serves a user directory with a change feed.

**Pros**:
- A leak of one system's token or key can't act in another system; only welinc-auth can sign.
- Tokens never sit in a URL or in browser storage readable by scripts.
- Builds on everything welinc-auth already has (accounts, lockout, OTP, scoping, change records), and every system keeps the libraries it uses.
- Every piece is a published standard, so the groups and the panel can look it up.

**Cons**:
- The most work of the three: the code flow, refresh rotation with reuse detection, assertion replay checks and the session routes in each system.
- Needs a custom domain for the cookie to be first party.
- The team owns the security of its own authorization server.

### Option 2: keep one suite wide token, just add refresh and published keys

One token with every role in every system, as today, signed with published keys instead of `JWT_SECRET`, with a refresh route added. Systems keep picking their own roles from the token. The portal keeps handing the token over, moved from the query string to a URL fragment.

**Pros**:
- Smallest change: no code flow, no session routes in the systems, no domain.
- Every group can adopt it in a day.

**Cons**:
- Any system, or a leak from it, can still act as the user in every other system.
- Tokens still pass through the browser address bar and live in storage readable by scripts.
- Logout and revocation stay weak without the per session model.
- It is the "one token everywhere" design the Capstone 1 panel already questioned.

### Option 3: replace welinc-auth with a hosted or self hosted identity provider

Keycloak (self hosted, Java) or a hosted service such as Microsoft Entra External ID or Auth0 takes over login, sessions, keys and clients, all of which they do out of the box.

**Pros**:
- Battle tested OAuth and OpenID Connect, refresh rotation, admin consoles and MFA with no code of our own.
- Hosted options remove the operational burden entirely.

**Cons**:
- Throws away welinc-auth's suite specific rules (system scoping, shared account rules, last admin guards, change records from specs 0009 and 0011), which would have to be rebuilt as extensions or kept in a side service anyway.
- Keycloak needs about 1 GB of memory on Container Apps (real cost on student credit) and Java knowledge nobody on the three teams has; hosted providers bring free tier limits and vendor lock in, and the BMS and VMMS profile routes still need a service of our own.
- The move from the current users and the portal becomes a migration of its own, near the deadline.

## Rationale

Option 1 wins because the forces in Context are about blast radius and token handling, and only Option 1 fixes both. A token per system and signing by welinc-auth alone mean a compromised BMS service can no longer act in VRMS. That is the core weakness Option 2 leaves in place. Option 3 would fix it too, but at the price of the suite rules the team already built and tested, plus a Java service or a vendor dependency, with three weeks to the deadline. Option 1 keeps the existing code, the existing libraries, and every account and rule in one place, and adds the standard pieces around them.

The cost is real: welinc-auth becomes the most security sensitive code in the suite. That is why the contract sticks to published standards with library support at every step, and why every S row runs at GA (verify, test, a fresh model review, then documentation).

### The individual calls

| Call | Chosen | Runner up | Why |
|---|---|---|---|
| Contract depth | Interface contract; S2 to S12 design the insides | Contract plus full S2, S3, S5 designs | Unblocks the other groups now; one giant spec would be slower to review and to build against. |
| Token audience | One token per system (`aud`) | One suite token | Limits what a leaked token can do to one system; the industry norm for OAuth audiences. |
| Signing | ES256 | RS256 | Every backend verifies through `passport-jwt` or `@nestjs/jwt` on `jsonwebtoken`, which supports ES256 but not EdDSA; ES256 keys and signatures are smaller than RSA. |
| Web token storage | HttpOnly refresh cookie on a custom domain, access token in memory | Both tokens in memory with rotation | Scripts can't read the refresh token, so an XSS bug can't take the session. Default Azure addresses are different sites (`azurestaticapps.net` is on the public suffix list), so Safari would block the cookie; a custom domain fixes it for about the price of a free student year. |
| Refresh holder | The system backend (code exchange on the backend, as decided in the S1 note) | welinc-auth sets the cookie itself | Keeps each backend a confidential client, so the refresh needs that backend's key as well as the cookie. |
| Web session length | 30 minutes idle, 12 hours max | 15 minutes idle, 8 hours | Covers a shop shift with one login and still locks an unattended screen. |
| Where idle is measured | On the server per `sid`, from activity pings at most once a minute | In each app's own timer | The cross check found that one app's timer would end the shared session while you worked in another app. Pings make the 30 minutes exact across all apps, for about one tiny call a minute. |
| Refresh rotation and concurrency | 10 s reuse grace plus one refresh at a time per app (Web Locks) | No grace | Strict reuse detection alone logs people out when two tabs refresh together or a phone retries after a lost answer; the short grace is the common fix and keeps theft detection. |
| Login request and code replay | A 10 minute single use server row; a replayed code ends its session | Parameters carried in the portal URL | Keeps every authorize parameter on the server, and follows RFC 9700 on replayed codes. |
| Directory privacy | Only users with a current or past role in the caller's system; phone behind `directory.contact` | Any id | A system with `directory.read` would otherwise see the whole suite's users. |
| Mobile login route | Its own `/auth/mobile/login` with a stricter limit | A `clientId` switch on `/auth/login` | Keeps the portal route cookie only and the mobile route token only, so neither can be talked into the other's mode, and lets the mobile route carry its own limits. |
| Mobile login | Native screen, first party client | System browser with PKCE | See *Engineer preference* below. |
| Mobile session length | 7 days rolling | 30 days rolling | Chosen by the engineer; weekly login for anyone off longer, a shorter window for a lost phone. |
| Revocation | 30 s cached session check plus refresh revocation | Pushed logout events | Already built and proven in VRMS (spec 0009). About 70 accounts make the call cost negligible, and push needs delivery, retries and an endpoint in each group. |
| Service identity | `private_key_jwt` | Client id and secret | welinc-auth stores only public keys, so its database leaking exposes no client credential, and no secret ever travels. About 20 lines per group with the library they already have. Mutual TLS was too heavy for Container Apps and local Docker. |
| User directory | Cursor change feed plus batch lookup, webhook nudge reserved | Full webhooks | Nothing is lost when a system is down, there is no new infrastructure, and it builds on the `UserChange` rows and VRMS's mechanic sync. Big webhook users (Stripe, GitHub, FHIR subscriptions) keep a pull API beside their webhooks for exactly this reason. Security doesn't depend on its speed. |
| Gateway paths | Each service owns its prefix | Gateway strips the prefix | The same URL locally and hosted, real paths in logs, no broken absolute links; one line of change per group. |
| Gateway config | Workspace `infra/gateway/` | Stay in `welinc-auth` | Spec 0008 already deploys the gateway from there; a route for BMS shouldn't be a PR to the auth service. |
| Ports | One block per system | Move the gateway off 3000 | Shared services and VRMS keep their ports; blocks leave room to grow; 8003 already means BMS in welinc-auth. |
| Cutover | Hard switch | Both flows until S11 | Only VRMS and the portal use welinc-auth for real, and the same team owns both, so dual code would protect nobody. |
| Move order | BMS before VMMS | VMMS first | BMS already verifies welinc-auth tokens and holds only seed users; VMMS has a full copy and the mobile app, so it goes second on a proven path. |
| Roles claim shape | Keep `[{ role, system }]`, filtered to `aud` | A flat `roles: string[]` | No call site has to change its parsing. |
| Error shape | Nest body plus `code`; OAuth format on `/auth/token` | RFC 9457 problem details everywhere | Matches what welinc-auth already returns (`ACCOUNT_EXISTS`); OAuth clients expect the OAuth format on the token route. |
| Login start | Backend `session/start` makes `state` and the PKCE verifier | The web app makes them | The web app never handles a code or a verifier, and `state` is checked against an HttpOnly cookie. |
| CSRF on session routes | POST with JSON and an `Origin` check, plus CORS | A separate CSRF token | `SameSite=Lax` already blocks cross site posts; JSON plus `Origin` closes the gap from other subdomains without extra state. |
| Second system on mobile | `audience` on refresh, one session | A second login | Lets the VRMS tab (scope feature 48) get a VRMS token from the same session. |

### Engineer preference: native mobile login

The engineer chose a native login screen for the mobile app. The recommended option was the system browser with PKCE, the OAuth standard for native apps (RFC 8252): the app never touches a password, and one login page serves the whole suite. Native login is still a sound choice for a first party app (one built by the suite's own team), and the contract keeps it safe: every login rule runs on the server, only registered first party native clients may post a password with a client id, and lockout plus rate limits stand in for reCAPTCHA. The tradeoff the team accepts: when admin OTP (feature 34) or another login step arrives, the app needs new screens and a store update. And because a public client has no secret, anyone can call the mobile login route without reCAPTCHA. Lockout and a stricter limit per address stand in, and app attestation is the later fix.

## Current state (read only check, 2026-11-07, clones fetched again 2026-11-08 with nothing new)

**welinc-auth** (`development`): routes `login`, `forgot-password`, `verify-otp`, `reset-password`, `me`, `users` (list, lookup, create, update, status, delete, changes, password, unlock), `profile` (update, password, picture, summary). Tokens are HS256 with `sub`, `email`, `roles: [{ role, system }]`, signed with `JWT_SECRET`. The JWT strategy takes the system from `?system=`, the token, `Origin`, `Referer` or the path. The schema has `User`, `UserRoleAssignment`, `PasswordResetToken`, an unused `RefreshToken`, and `UserChange`. `nginx.conf` here is the suite gateway (`/auth`, `/vrms`, `/repairs`).

**VRMS**: `welinc-backend-vrms/src/auth/account-check.ts` checks `GET /auth/me?system=VRMS` with a 30 s cache. The portal sends users to `<app>/login?token=<token>` (`welinc-web-portal/src/App.tsx`, `pages/auth/Login.tsx`), and `welinc-web-vrms` keeps the token in `localStorage` (`welinc_token`).

**VMMS** (`development`): its own `/auth/*` with `users`, `user_roles`, refresh tokens bound to web or mobile through `X-VMMS-Client`, login activity, phone verification and `audit-logs`. Backend on 3000, analytics on 3001 checking callers through `GET auth/me?system=VMMS` on the VMMS backend, web on 8002 (already accepts `?token=`). The mobile app (`welinc-mobile-vrms_vmms`, Expo 56) logs in natively against `/auth/login`, refreshes through `/auth/refresh`, and keeps tokens in `expo-secure-store`, with an offline SQLite sync. VMMS controllers have no common prefix (`vehicles`, `checklists`, `maintenance-schedules`, `vmms/config`, `users`, `notifications`, `auth`). One VMMS role per account.

**BMS** (`latest-bms-backend`, `latest-bms-frontend`): `bms-gateway` (3005) strips `/api` and routes to booking 3002, dispatch 3003, completion 3004, analytics and the projection; it answers `/auth/profile/activity` and `/activity-logs` itself from the auth database and bridges `/auth/*`. Services verify HS256 tokens with `@nestjs/jwt`. Web on 5173, calling `/api`. Auth runs from the `latest-auth-backend` branch of the old `welinc-backend` repo, with systems `BMS` and `SHARED` only, admin checks removed (`LOCAL_DEV_BYPASS.md`), no refresh. `welinc-backend-bms-analytics-ai` defaults to 3001 and uses MySQL. Roles: Admin, Customer Support, Operations.

**JWT libraries in use**: `@nestjs/jwt` and `passport-jwt` (auth, VMMS backend), `passport-jwt` (VRMS backend, BMS analytics), `@nestjs/jwt` (BMS booking, dispatch, completion), `jwt-decode` (BMS web). All verification runs on `jsonwebtoken`.

## References

**Project sources** (in this repo):
- `docs/scope/_root/shared-services.md`: rows S1 to S12, the S1 note with the calls already made, and the 2026-11-07 inventory.
- `AGENTS.md` (root): shared files need a spec and a PR the other groups can see; no system reads another system's database.
- VRMS spec 0008 (hosting): Static Web Apps, Container Apps, gateway config in `infra/gateway/`, minimum replicas.
- VRMS spec 0009 (auth service boundary): welinc-auth owns every account; the 30 s account check; `UserChange` and the changes cursor.
- VRMS spec 0011 (permission matrix): admin scoping by system in welinc-auth, the CASL matrix in VRMS.
- `welinc-auth/AGENTS.md`: current routes, guards, lockout, CORS and gateway notes.

**Practices & standards**:
- OAuth 2.1 (draft) and RFC 6749: authorization code, refresh and client credentials grants; removal of the password grant for third party clients.
- RFC 7636 (PKCE) and RFC 8252 (OAuth for native apps).
- RFC 9700 (OAuth 2.0 security best current practice): refresh token rotation with reuse detection, exact redirect matching.
- RFC 7523 and OpenID Connect client authentication (`private_key_jwt`).
- RFC 7517 (JWK sets, JWKS) and RFC 8414 (authorization server metadata).
- RFC 9068 (JWT profile for access tokens: `typ: at+jwt`, `client_id`).
- OAuth for browser based apps (IETF draft): the backend for frontend pattern and HttpOnly cookies.
- OWASP session management guidance: idle and absolute timeouts, `HttpOnly`, `Secure`, `SameSite`.
- Pull with catch up as the source of truth, push as a hint (the Stripe and GitHub events APIs beside their webhooks).
