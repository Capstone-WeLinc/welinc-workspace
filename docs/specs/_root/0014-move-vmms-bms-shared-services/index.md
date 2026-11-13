# 0014. Move VMMS and BMS onto the shared services

**Date**: 2026-11-13
**Status**: Proposed
**Scope row**: [S11. Move VMMS and BMS onto the shared services](../../../scope/_root/shared-services.md#s11-move-vmms-and-bms-onto-the-shared-services--in-progress)
**Builds contract sections**: [0001](../0001-shared-services-contract/index.md) version 8 (breaking: the launcher answer for people who hold a system only on a phone app, web clients limited to office roles; additive: `mobileSystems`, `fleet.read`, the lookup limit made real, the move order) and version 9 (breaking: the bearer admin routes removed, the last slice)
**Related**: [0002](../0002-signing-keys-service-identity/index.md) (token check, client keys), [0003](../0003-sessions-refresh-logout/index.md) (session routes, mobile login), [0004](../0004-roles-per-system/index.md) (catalog, `allowed_roles`), [0005](../0005-user-directory/index.md) (directory), [0006](../0006-suite-seed-accounts/index.md) (seed manifest), [0007](../0007-app-initiated-login-launcher/index.md) (launcher), [0008](../0008-suite-gateway/index.md) (gateway, ports, service names), [0009](../0009-email-verification/index.md) (code step), [0011](../0011-account-activity-audit/index.md) (activity), [0012](../0012-profile-extras/index.md) (deletion, erasure), [0013](../0013-suite-admin-model/index.md) (portal admin, deprecated bearer routes), VRMS feature 56 (domain contracts, which the fleet API starts)

## Summary

VMMS and BMS stop running their own login and user tables and move onto welinc-auth, the portal and the gateway, the way VRMS already does. Each group changes its own repos at the same time, using a move guide per system, a checker script that tests their system against the contract, and the VRMS code they copy. The shared side gets small changes to make that work: VMMS and BMS web apps only let office roles in (mechanics, drivers and helpers use the phone apps), the portal tells phone only people where to go, and BMS reads trucks from a new VMMS fleet API instead of the old Capstone 1 database. When both groups pass the checker and a cross system test, the old admin routes in welinc-auth are removed.

## Requirements

**User stories**:
- As the shared services owner, I want each group to get one guide, one checker and the VRMS code to copy, so that I can tell exactly when a system has moved without reading their code.
- As a VMMS or BMS developer, I want a checklist that tells me what to delete, what to copy and how to prove it works, so that I can move my system without guessing the contract.
- As a VMMS mechanic or a BMS driver, I want the portal to tell me my system is on the phone app, so that I'm not told I have no access when I do.
- As a BMS dispatcher, I want trucks and garages to come from VMMS, so that I can't dispatch a truck VMMS has just sent for maintenance.
- As any WeLinc user, I want one sign in across VRMS, VMMS and BMS, so that signing out or being deactivated in one place reaches all three.

**Acceptance criteria** (the contract; "you" is the shared services owner, "the group" is VMMS or BMS):

*Web and app rules in welinc-auth (you build)*
- **AC-1**: `clients.seed.ts` gives `vmms` `allowedRoles: { VMMS: ['ADMIN', 'OPERATIONS'] }` and `bms` `allowedRoles: { BMS: ['ADMIN', 'CUSTOMER_SUPPORT', 'OPERATIONS'] }`. A code exchange or refresh through either client for a person whose roles in that system are all outside the list answers 403 `APP_NOT_ALLOWED` (the spec 0004 mechanism, unchanged).
- **AC-2**: `/auth/authorize` for a person with a live SSO session who holds live roles in the client's system (`liveRoleWhere()`, the launcher's filter, so an expired temporary role never counts), none of them allowed on that client (the `allowed-roles.ts` check), issues no code. It redirects with the existing `withParams` helper to the client's `redirect_uri` with `error=access_denied`, `error_description=APP_NOT_ALLOWED` (a literal) and `state`, and logs `reason=app_not_allowed`. A person with no live role there, a suite admin included, keeps today's redirect (`error=access_denied`, no description).
- **AC-3**: The VRMS reference session callback (`welinc-backend-vrms/src/session/`) sends `error=access_denied` with `error_description=APP_NOT_ALLOWED`, and an exchange answered 403 `APP_NOT_ALLOWED`, to `<portal>/?error=APP_NOT_ALLOWED&system=VRMS`. The `system` value is an upper case literal in each copy (`VRMS`, `VMMS`, `BMS`). `auth-client.ts` returns a new kind `not_allowed`. A refresh answered `APP_NOT_ALLOWED` clears the cookie and answers 403 `APP_NOT_ALLOWED`. VRMS has no `allowedRoles`, so its own behavior doesn't change, but the copies in VMMS and BMS inherit the handling.
- **AC-4**: The launcher answer (`/auth/login`, `/auth/login/verify-email`, `/auth/sso`) splits the systems a person holds, using the launcher's existing live role query (`liveRoleWhere()`, temporary grants included) and the existing `allowed-roles.ts` check (no second copy). A held system is in `systems` when at least one of the person's live roles there passes that system's web client: the same active confidential client with a web address the launcher picks today (the oldest when there are several, with the duplicates warning kept); a system left out of the client's `allowedRoles` lets every role through. Otherwise it is in a new list `mobileSystems` when at least one role passes an active public native client of that system, as `{ system, description, roles, app: { clientId, released } }`. Otherwise it is left out, as today. Both lists keep launcher order (BMS, VMMS, VRMS) and are always present (`[]` when empty). `user.systems` in every grant answer is built from `systems` only, so Switch system never offers a phone only system.
- **AC-5**: A person whose `systems` is empty and `mobileSystems` is not gets 200 `{ user, systems: [], mobileSystems }` on all three launcher routes, never 403 `NO_SYSTEM_ACCESS`. 403 `NO_SYSTEM_ACCESS` remains for a person with both lists empty who is not a suite admin (including someone whose roles pass neither a web nor a phone client). A suite admin's answer is unchanged (200 with `systems: []`), with `mobileSystems` filled when a live temporary grant falls there. The portal never forwards a person whose `systems` is empty into a system.
- **AC-6**: `oauth_clients` gains `app_released boolean not null default false` (one migration). `ClientDefinition` in `clients.seed.ts` gains `appReleased` (default false), written like `allowedRoles`: the seed is authoritative and a rerun overwrites a hand edit. It is `true` for `vmms-mobile` and `false` for `bms-mobile`, and feeds `app.released` (AC-4) and nothing else.
- **AC-7**: The portal shows a phone only state when `systems` is empty and `mobileSystems` is not: one card per phone only system with its name, description and roles (catalog names from the answer), reading "<System> is on the WeLinc mobile app" when `released` is true and "<System> is coming to the WeLinc mobile app" when false, plus "Your role doesn't use the web version." There is no open button, only Sign out. When the launcher shows (two or more web systems), a quiet line under the cards lists the phone only systems ("On the mobile app: VMMS"). `<portal>/?error=APP_NOT_ALLOWED&system=<SYS>` shows "Your role in <System> uses the WeLinc mobile app, not the web" with Back to your systems and Sign out; the name comes from `/auth/systems` when `system` matches a code there, else the text says "this system" (the parameter is never shown raw). `?from=<SYS>` keeps spec 0007's rules (a person with one web system goes straight in, no loop). All of it uses `design.md` tokens and holds at 375px.
- **AC-8**: `people.json` gains `vmms.mech@welinc.com` (id `00000000-0000-4000-8000-000000002401`, one role: VMMS Mechanic, no VRMS role, `"password": "mechanic"` so it signs in with `mechanic1234`, like every mechanic). `docs/integration/seed-accounts.md` lists it, and the VRMS copy passes `seed:check`. It is the test account for AC-5 and AC-7.
- **AC-9**: `GET /auth/users/lookup` (until AC-33 removes it) and `GET /auth/admin/users/lookup` share one counter, key `lookup:<sub>`, 30 calls in 60 s, per welinc-auth container, in the existing throttler storage the way the activity feed counts (`activity-feed:<sub>`). Over the limit they answer 429 `RATE_LIMITED` with `Retry-After`, the activity feed's body. Contract 0001 section 12's promise becomes true.
- **AC-10**: `bms` gets `serviceScopes` `{ AUTH: ['directory.read', 'directory.contact'], VMMS: ['fleet.read'] }`. A client credentials call from `bms` with `audience=VMMS` and `scope=fleet.read` answers a service token with `aud: VMMS`, `token_use: service` and `scope: fleet.read`. Any other client asking for `audience=VMMS` answers 400 `invalid_target` (the spec 0002 check, unchanged). A unit test in `token-endpoint.service` proves a scope on an audience other than `AUTH`.
- **AC-11**: Contract 0001 reaches version 8: AC-1 to AC-10 in sections 4, 7, 10, 11 and 12; the fleet API's scope in section 4 (the routes live in `docs/integration/fleet-api.md`); the move order becomes "VMMS and BMS in parallel, each done at its checker and the cross check"; the gap map rows for S11 point here. The version entry lists each system's changes.

*The kit (you build)*
- **AC-12**: `node scripts/check-system.mjs <vrms|vmms|bms>` runs the live checks for that system through the gateway (default `http://localhost:3000`, overridable with `--api` and `--portal`), using seed accounts that need no emailed code (it needs slice 1's `vmms.mech@`). For every system: `<prefix>/health` answers 200 with `checks`; a protected route answers 401 with no token, a tampered token, and a token whose `aud` is another system (the checker signs `multi.lead@` in through client `vrms` with the full PKCE flow; for `vrms` itself it uses a VMMS token the same way once VMMS is on the stack, else skips that one check and says so); `GET <prefix>/session/start` redirects to `/auth/authorize` with `client_id=<sys>`, `code_challenge_method=S256` and the exact callback; a headless sign in (`POST /auth/login` with the portal `Origin`, then authorize, callback and refresh) gives a refresh cookie with the local name `<sys>_rt` (`__Secure-<sys>_rt` when hosted), HttpOnly, path `/<sys>/session`, and an access token with `aud` the system that opens a protected route; `refresh` without the right `Origin` answers 403 `CSRF_REJECTED`; after `logout`, `refresh` answers 401 and the old access token is refused within 31 s with `SESSION_ENDED` (the checker waits; there is no skip). For VMMS also: a sign in as `vmms.mech@` ends at `<portal>/?error=APP_NOT_ALLOWED&system=VMMS`; `/auth/mobile/login` as `vmms.mech@` with `vmms-mobile` gives a token that opens `/vmms/maintenance-schedules`; `/vmms/analytics/health` answers 200 and an analytics route takes the user token and refuses another `aud`. For BMS also: a sign in as `driver.ramon@` ends at `?error=APP_NOT_ALLOWED&system=BMS`; a 5 MB body to a booking `POST` answers 400 from booking validation (so the body passed the BMS gateway). The fleet checks run as their own group (`--fleet`, also on by default): VMMS's fleet routes answer 401 with no token and 403 `WRONG_TOKEN_USE` with a user token; `GET /bms/config/vehicles` as `bms.ops@` lists the same plate numbers as VMMS's `GET /vmms/vehicles` as `vmms.ops@` (proving `fleet.read` end to end). A missing scope (403 `FORBIDDEN`) needs a client key, so it is a VMMS unit test, not a checker check. Each check prints `ok` or `FAIL <reason>`, with a summary per group (login, fleet, static).
- **AC-13**: The same script scans the system's repos on disk (`--static-only` runs this alone, `--live-only` skips it) for leftovers, outside `node_modules`, `dist`, `build`, lockfiles and `*.md`, skipping comment lines, and prints `file:line` for each hit: `JWT_SECRET`, `AUTH_DATABASE_URL`, `BMS_PARTNER_DATABASE_URL`, `5433/welinc_db`, `HS256`, `jwt-decode`, `X-VMMS-Client`, `localStorage` or `sessionStorage` with `token` (any case) on the same line or the next two, a token read from the URL (`searchParams.get('token')`, `?token=`), `SEMAPHORE_`, and calls to `/auth/users` or `/auth/deletion-requests` (the routes AC-33 removes). A line ending in `// check-system: allow <reason>` is skipped and listed as allowed. For `vrms` it scans the VRMS repos and the portal; VRMS's own `/auth/users` call carries `// check-system: allow AC-33 pending` until task 13a removes it.
- **AC-14**: The script exits 0 only when every check passes, 1 on any failure, and 2 when the stack doesn't answer at all (with "start the stack first"). It reads no `.env` value and needs no client key: every token it uses comes from a seed account sign in. `check-system.mjs vrms` passes on today's VRMS before the guides go out (the checker is proven on a system known to be right).
- **AC-15**: `docs/integration/move-vmms.md`, `docs/integration/move-bms.md` and `docs/integration/fleet-api.md` exist and are listed in `docs/integration/README.md`. Each move guide covers every item in *Guide contents* below, as an ordered checklist that links the existing guides instead of repeating them, and ends with the checker command and the sign off step. `fleet-api.md` holds the fleet routes, fields, errors and the caching rule (AC-23, AC-28).
- **AC-16**: `scripts/setup.sh vmms|bms` and `scripts/start.sh vmms|bms` run the system's stack when `docker-compose.<sys>.yml` exists: compose up, then each service's migrations and seed, and `start.sh` waits for and prints `ok` per service's health route (`/vmms/health`, `/vmms/analytics/health`, `/bms/health`). `setup.sh` also runs `npm run keys:client -- <sys> ...` and `seed:clients` when the system's backend `.env` has no client key, found with the existing `has_value` presence check (it never prints a value). While the compose file is missing they keep today's message, now pointing at the move guide. Each guide carries a compose template made from `docker-compose.vrms.yml`, with the service names, ports and `welinc-network` (external) filled in.

*VMMS moves (the group builds; the checker and the cross check prove it)*
- **AC-17**: `welinc-backend-vmms` serves under the global prefix `vmms` on port 3010 as Docker service `vmms-backend`, with `trust proxy` from `TRUST_PROXY_HOPS` and `GET /vmms/health`. Every user route verifies an ES256 token from welinc-auth's published keys with `aud: VMMS` and runs the 30 s session check (the copied `src/auth/verify/` and `account-check.ts`), and reads roles from the token. It keeps no `users`, `user_roles`, `refresh_tokens`, `login_activities` or `password_reset_tokens` table, no `/auth/*` or `/users*` routes, no `JWT_SECRET`, no Semaphore code and no `X-VMMS-Client` handling.
- **AC-18**: VMMS serves the six session routes under `/vmms/session/*` as client `vmms`, copied from VRMS (cookies `vmms_rt` and `vmms_login_<state prefix>`, callback `<API_PUBLIC_URL>/vmms/session/callback`).
- **AC-19**: VMMS keeps people as `sub`s. Its `Mechanic` rows (and any other name copy) are fed by a copy of the VRMS directory reader with its own `directory_sync_state`. Every user id column keeps holding a welinc-auth user id (no foreign key). When the feed says `erased: true`, every copied name becomes `Deleted user` and every copied email the snapshot's `deleted-<id>@erased.invalid` (`actorEmail` on the audit tables included). The seed reads a byte for byte copy of `people.json` (`seed:check` passes) and creates no users.
- **AC-20**: `welinc-web-vmms` follows `web-login.md`: the boot sequence through `/vmms/session/*`, the access token in memory only, no `?token=` intake, Switch system from `user.systems`, and sign out to `<portal>/login?reason=logout`. Its Users page is deleted and the menu item opens `<portal>/admin/people?system=VMMS`. The profile page uses welinc-auth's routes per `account-activity.md` and `account-deletion.md` (no phone verification). The audit page shows sign in events from `/auth/activity` (admin only, scoped to the token's system) to VMMS Admins only; other roles see the business rows only. The VRMS link is gone (Switch system replaces it, no token in a URL). It runs on 8002.
- **AC-21**: `welinc-mobile-vrms_vmms` signs in through `/auth/mobile/login` with `clientId: vmms-mobile` and shows the `EMAIL_VERIFICATION_REQUIRED` code screen. It refreshes through `/auth/token` (rotating the stored refresh token), logs out with `{ refreshToken, clientId }`, shows the `APP_NOT_ALLOWED` message as given, and calls the API at `<api>/vmms/`. It has no `X-VMMS-Client` header and no client side role check (`getMobileAccessRole` is gone). The VRMS tab (a refresh with `audience=VRMS`) is out of scope: feature 48.
- **AC-22**: `welinc-backend-vmms-analytics-ai` serves under `vmms/analytics` on port 3011 as `vmms-analytics` with `GET /vmms/analytics/health`. It verifies user tokens itself (`aud: VMMS`, session check, roles from the token) and never calls a VMMS `/auth/me`. Its "assigned" rule keeps calling VMMS core with the user's token.
- **AC-23**: VMMS serves the fleet API in *Feature design*: `GET /vmms/fleet/vehicles`, `GET /vmms/fleet/vehicles/:id` and `GET /vmms/fleet/garages`, read only. Each takes only a service token with `aud: VMMS` and `fleet.read`, checked by the copied verify guards plus a scope guard (no token or a bad one: 401; a user token: 403 `WRONG_TOKEN_USE`; a service token without the scope: 403 `FORBIDDEN`, proven by a VMMS unit test), and answers soft deleted vehicles as absent (404 `VEHICLE_NOT_FOUND`).

*BMS moves (the group builds; the checker and the cross check prove it)*
- **AC-24**: `bms-gateway` is a NestJS app on port 3020 as Docker service `bms-gateway`, listening on all interfaces, serving everything under `/bms`. It keeps the `owner()` route table and the raw proxy loop (Nest's body parser off on proxied routes, bodies streamed as is, capped at 10 MB to match the suite gateway). It serves `GET /bms/health` and the six session routes as client `bms` (cookies `bms_rt` and `bms_login_<state prefix>`), and keeps `X-Request-Id`. It forwards no `/auth/*` path (the web app calls welinc-auth through the suite gateway) and has no auth database code. Its route table includes analytics (`/bms/reports` and the forecast routes to `welinc-backend-bms-analytics-ai` on 3025). It forwards the user's bearer token unchanged to every service.
- **AC-25**: Every BMS process that serves user requests (gateway, booking, dispatch, completion, `welinc-backend-bms-analytics-ai`) verifies ES256 tokens with `aud: BMS` and runs the session check. None holds `JWT_SECRET`. The tracking link secret is `CUSTOMER_TRACKING_SECRET`, required at boot with no fallback (contract rule 8). The internal service key between BMS processes stays BMS's own business. The `bms` client private key is never logged, and each process that holds it (gateway, booking, dispatch) signs its own client assertions with a fresh `jti` (the 600 a minute per client limit covers all three).
- **AC-26**: No BMS code reads the auth database. Approval submitter and reviewer names come from `POST /auth/directory/users/lookup` (`missing` ids show "Unknown user"). The admin activity page combines BMS's own audit rows (names from the same lookup) with sign in events from `/auth/activity` (the BMS Admin's bearer token, scoped to BMS); other roles see BMS's rows only. Profile activity is the web app's direct call to `/auth/profile/activity`. Crew names copied in `drivers.name` and `helpers.name` follow the directory: a crew member whose `user_id` comes back `erased` becomes `Deleted user` (BMS polls the feed or looks the linked ids up daily; the guide recommends the feed reader).
- **AC-27**: `welinc-web-bms` follows `web-login.md` like AC-20: no password form (`/login` sends the browser to `/bms/session/start`), no `localStorage` token, no `jwt-decode`, forgot password left to the portal, Switch system and sign out. The Users page is deleted except crew management, which stays as its own page; the menu links to `<portal>/admin/people?system=BMS`. The profile page uses `reauthToken` and `GET /auth/profile/deletion-request` per `account-deletion.md`. It runs on 8003 and calls `<api>/bms/`.
- **AC-28**: Drivers move from `welinc_db` into dispatch's database next to helpers, and both gain a nullable unique `user_id` set from `people.json`: driver n (`DRV-00n`) is the nth `"group": "driver"` row in file order (ids `...3401` up), helper n (`HLP-00n`) the nth `"group": "helper"` row; the BMS seed fails when its crew counts differ from the manifest's (12 and 20). Dispatch owns `vehicle_dispatch_profiles` (data model below). Vehicles and garages come from the VMMS fleet API with a `fleet.read` token, cached until 60 s before its `exp`: the list cached 30 s and showing every active vehicle with its VMMS status, and the one vehicle read fresh at assignment. An assignment to a vehicle whose fresh status isn't `AVAILABLE` (`UNDER_REPAIR` and `UNDER_MAINTENANCE` are not dispatchable) gets 409 `VEHICLE_UNAVAILABLE`. When VMMS doesn't answer (3 s) or answers 5xx, the list and the assignment answer 503 `FLEET_UNAVAILABLE`, no stale list is served, and nothing is assigned. A 401 `TOKEN_EXPIRED` gets one new token and one retry. An assignment whose vehicle VMMS answers 404 shows "Unavailable vehicle" and takes no new assignment. Two assignments racing for one truck keep dispatch's existing guard; `move-bms.md` names it.
- **AC-29**: The analytics projection writes its read model into `bms-analytics-db`, a database container BMS owns in `docker-compose.bms.yml` (its own host port, never 5433), and `welinc-backend-bms-analytics-ai` reads that database and the fleet API, never `welinc_db`. Both run in `docker-compose.bms.yml` (analytics on 3025 behind `bms-gateway`).
- **AC-30**: Once BMS's checker passes, `welinc_db` leaves every BMS setup and the old `welinc-backend` repo is archived on GitHub (read only, history kept). The static scan finds no `5433/welinc_db` in any BMS repo.

*Done*
- **AC-31**: Local done, per group, in two ticks. **Login done**: the group's pull request into `development` shows passing login and static groups of `check-system.mjs` and the guide's login checklist ticked; the group lead confirms in writing; you run the cross system steps in `verify.md` (one sign in across three apps, Switch system, sign out everywhere within 30 s, a deactivation reaching all three within 30 s, a role change at the next refresh, an erasure reaching VMMS's and BMS's name copies) and tick it in the scope row. **Fleet done**: the `--fleet` group passes (VMMS serving, BMS reading) and you run the fleet steps in `verify.md`. A group may reach login done first.
- **AC-32**: Staging done: the same cross system steps pass on staging once VRMS feature 26 has deployed all three systems behind one gateway address, with each system's deployed web address in the client registry and the gateway's `ALLOWED_ORIGINS`.
- **AC-33**: After AC-31 holds for both groups, and VRMS's Users page no longer calls `GET /auth/users` (task 13a), and the static scan of all three systems and the portal finds no caller and no `allow AC-33 pending` line (a hard gate in task 13), welinc-auth removes the bearer admin routes: `/auth/users*` (lookup, list, create, edit, status, unlock, delete, restore, activity and sessions) and `/auth/deletion-requests*`, which then answer 404. `/auth/activity` and `/auth/activity/catalog` stay (the audit pages read them). Contract 0001 reaches version 9.

## Decision

**Chosen option**: Option 1: a move kit (guide per system, conformance checker, VRMS reference code) with each group moving its own repos in parallel and a hard switch per system.

You build the shared changes and the kit, prove the checker on VRMS, hand the guides over, and close each group with its checker run plus your cross system check. The groups copy the VRMS folders rather than install a shared package. BMS's gateway becomes NestJS and owns its login.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` and `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-client-api/`, `.claude/skills/prisma-cli/`) · `shadcn` (the portal states) · `docker-patterns` (ask first, for the compose templates; `.claude/skills/docker-patterns/`)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

### Settled calls

| Call | Pick | Runner up |
|---|---|---|
| Who builds | You: shared changes, guides, checker; groups: their repos | You open PRs in their repos (breaks the ownership rule) |
| User data | No import: each system reseeds from `people.json`; no deployment holds real users | Remap ~40 VMMS user id columns by email |
| Order | Parallel, each done at its own checker and cross check | BMS first (contract 0001 version 7) |
| Done | Local gate (AC-31), then a staging gate (AC-32) | Hold the row until staging |
| VMMS and BMS web vs app | `allowedRoles` on the web clients, launcher split, phone only state | `allowedRoles` without the launcher split |
| Shared code | Copy the VRMS folders; the checker catches a wrong copy | A private npm package |
| Lookup limit | Add it (30 a minute) | Drop the promise |
| BMS login host | `bms-gateway` ported to NestJS (a backend for frontend) | Booking service hosts the session routes (the fallback the guide names if BMS can't take the port on) |
| Old Capstone 1 database | All in S11: drivers into BMS, fleet from a VMMS API, analytics read model into BMS | Drivers only; fleet waits for feature 56 |
| Fleet auth, freshness, BMS fields, garages | Service token `fleet.read`; live reads with a 30 s list cache and a fresh read at assignment; `vehicle_dispatch_profiles` in BMS; garages from VMMS | A synced copy through a second change feed |
| VMMS analytics | Verifies tokens itself | VMMS core keeps a `/vmms/me` |
| Bearer admin routes | Removed in this spec's last slice (AC-33) | A later spec |
| Checker | Live behavior plus a static scan | Live only |
| Old `welinc-backend` | Archived after BMS passes | Deleted |
| Phone only person at the portal | A "use the app" state | Today's no access state |
| BMS web | Office roles only, like VMMS | Open to drivers and helpers |
| BMS analytics | Its own read model database | Reads the booking and dispatch databases |
| Fleet contract home | This spec plus `fleet-api.md`; 0001 holds only the scope | A new section in 0001 |
| Sign off | Checker plus your cross check plus the lead's word | Checker only |

Calls made here (recommended, no question needed): the `bms` client key is one BMS identity, held by `bms-gateway` and by any BMS process that calls welinc-auth or VMMS (booking for the directory lookup, dispatch for the fleet), as VRMS holds one key (runner up: only the gateway calls out and enriches answers, which pushes domain logic into the edge). BMS dispatch calls VMMS at its internal address (`VMMS_INTERNAL_URL`, `http://vmms-backend:3010` locally), not through the public gateway (runner up: through the gateway, an extra hop and the flood limit for no gain). The phone only state reads `app_released` from welinc-auth, not a portal constant (runner up: a portal map, which drifts the day bms-mobile ships). The checker proves `fleet.read` through BMS's own vehicle list, so it needs no client key (runner up: a test client, one more seeded secret).

### Data model

**welinc-auth (one migration, you)**

| Table | Change |
|---|---|
| `oauth_clients` | `app_released boolean not null default false`. Seed: `vmms-mobile` true, `bms-mobile` false. Seed data, no column: `vmms.allowed_roles = { VMMS: [ADMIN, OPERATIONS] }`, `bms.allowed_roles = { BMS: [ADMIN, CUSTOMER_SUPPORT, OPERATIONS] }`, `bms.service_scopes.VMMS = [fleet.read]` |

**VMMS (the group)**

| Table | Change |
|---|---|
| `users`, `user_roles`, `refresh_tokens`, `login_activities`, `password_reset_tokens` | dropped, with the foreign keys from `notifications`, `maintenance_notifications`, `mechanics` and `maintenance_schedules` (the `user_id` style columns stay as plain uuids) |
| `mechanics` | kept; fed by the directory reader (`user_id` unique, the welinc-auth id) |
| `directory_sync_state` | new, copied from VRMS (one row: cursor, lease) |
| audit tables with `actor_email` | kept; rewritten on `erased` |

**BMS (the group)**

| Table (database) | Change |
|---|---|
| `drivers` (dispatch) | moved from `welinc_db`: `id uuid pk`, `emp_id` unique, `name`, `initials`, `crew_status`, `license_number`, `license_type`, `license_expiry`, `contact`, `email`, `address`, `emergency_name`, `emergency_contact`, `join_date`, `is_active`, `deleted_at`, plus `user_id uuid null unique` |
| `helpers` (dispatch) | gains `user_id uuid null unique` |
| `vehicle_dispatch_profiles` (dispatch) | `vehicle_id uuid pk` (the VMMS vehicle id, no foreign key), `required_helpers int not null default 0`, `truck_type_id varchar null`, `status_reason text null`, `status_since timestamptz null`, `expected_back_at timestamptz null`, `status_remarks text null`, `driver_id uuid null` (fk `drivers.id`), `updated_at timestamptz` |
| `dispatch_assignments.vehicle_id`, `driver_id` | unchanged columns; `vehicle_id` now names a VMMS vehicle id, `driver_id` a local driver |
| analytics read model | its own database in `docker-compose.bms.yml` |
| the ~20 user id columns in booking, dispatch, completion | unchanged; hold welinc-auth ids after the reseed |

No data migration anywhere: no deployment holds real people or work, so every system reseeds.

### API surface

**welinc-auth**

| Route | Method | Change | Auth | Key answers |
|---|---|---|---|---|
| `/auth/login`, `/auth/login/verify-email`, `/auth/sso` | POST, POST, GET | `mobileSystems` added; `systems` and `user.systems` keep only web openable systems; 200 for phone only people | as today | 200 `{ user, systems, mobileSystems }`, 403 `NO_SYSTEM_ACCESS` only with both lists empty |
| `/auth/authorize` | GET | `error_description=APP_NOT_ALLOWED` when roles are held but none allowed | SSO cookie | 302 to `redirect_uri` |
| `/auth/token` (client credentials) | POST | `bms` may ask `audience=VMMS`, `scope=fleet.read` | client assertion | 200 service token, 400 `invalid_target` |
| `/auth/users/lookup`, `/auth/admin/users/lookup` | GET | 30 a minute per admin | admin | 429 `RATE_LIMITED` |
| `/auth/users*`, `/auth/deletion-requests*` (bearer) | all | removed (AC-33, version 9) | none | 404 |

**VMMS fleet API** (written out again in `fleet-api.md`)

| Route | Method | Out |
|---|---|---|
| `/vmms/fleet/vehicles` | GET | `{ vehicles: FleetVehicle[] }`, every vehicle with `isActive` true and `deletedAt` null, ordered by `plateNumber`; `?garageId=` filters |
| `/vmms/fleet/vehicles/:id` | GET | `FleetVehicle`, 404 `VEHICLE_NOT_FOUND` |
| `/vmms/fleet/garages` | GET | `{ garages: { id, name }[] }`, active and not deleted, ordered by `name` |

```ts
type FleetVehicle = {
  id: string;            // uuid, VMMS vehicles.id
  plateNumber: string;
  make: string | null;
  model: string;
  year: number | null;
  truckSizeCategory: string | null;
  capacity: number;
  odometer: number;
  status: 'AVAILABLE' | 'UNDER_REPAIR' | 'UNDER_MAINTENANCE'; // VMMS VehicleStatus; BMS dispatches only 'AVAILABLE'
  garageId: string | null;
  updatedAt: string;     // ISO 8601
};
```

Auth on all three: a service token with `aud: VMMS` and `scope` containing `fleet.read`. 401 for none or bad, 401 `TOKEN_EXPIRED` for expired (get a new token, retry once), 403 `WRONG_TOKEN_USE` for a user token, 403 `FORBIDDEN` without the scope. No body, no writes. Answers carry `Cache-Control: no-store`; the caller owns its cache.

**System routes each group serves** (listed in the guides; contract 0001 sections 3 and 7 already define them): `<prefix>/health`, the six `<prefix>/session/*` routes, and everything else under `/vmms/`, `/vmms/analytics/` or `/bms/`.

### Value sourcing

| Action | Value | Source |
|---|---|---|
| Launcher split (AC-4) | whether a role opens a system on the web | `oauth_clients.allowed_roles` of the system's active confidential client with a `web_address` (missing system key: all roles) |
| Launcher split | `mobileSystems[].app.clientId`, `released` | the active `PUBLIC_NATIVE` client row with that `system` whose `allowed_roles` pass one held role; `app_released` |
| Launcher split | `description`, `roles[].name` | the system catalog (`systems`, `system_roles`), as spec 0007 |
| Portal phone only text | the system's display name | the catalog name already in the launcher answer |
| Authorize refusal (AC-2) | held vs allowed | live `user_roles` for the client's system against the client's `allowed_roles` |
| Portal error page | `system` | the `system` query parameter the system's callback adds (its own code) |
| Lookup limit | the counter key | the admin token's or cookie session's `sub` |
| Fleet token | `aud`, `scope` | the `bms` row's `service_scopes`; the request's `audience` and `scope` |
| Fleet vehicle fields | every `FleetVehicle` field | the VMMS `vehicles` column of the same name (`make`, `truckSizeCategory`, `odometer` included); `engineType` is not served |
| BMS vehicle list | dispatch only fields | `vehicle_dispatch_profiles` joined in BMS by `vehicle_id` (no profile row: `required_helpers` 0, the rest null) |
| BMS assignment check | availability | a fresh `GET /vmms/fleet/vehicles/:id`, `status === 'AVAILABLE'` |
| BMS approval and audit names | `name`, `email` | `POST /auth/directory/users/lookup` by the stored ids (`missing` shows "Unknown user") |
| BMS audit sign in rows | sign in events | `GET /auth/activity` with the admin's bearer token |
| Crew `user_id` | the welinc-auth id | the nth `"group": "driver"` (or `"helper"`) row of `people.json` in file order for `DRV-00n` (`HLP-00n`) |
| Erased copies | the replacement values | the feed snapshot: `Deleted user`, `deleted-<id>@erased.invalid` |
| Portal error page | the system's name | `/auth/systems` when the `system` parameter matches a code there, else "this system" |
| Checker accounts | emails, passwords | `docs/integration/seed-accounts.md` defaults in the script (`vmms.ops@`, `vmms.mech@`, `bms.ops@`, `bms.cs@`, `driver.ramon@`, `multi.lead@`, `vrms.chief@`), `--accounts <file>` to override |
| Checker fleet plates | expected plates | VMMS's own `GET /vmms/vehicles` as `vmms.ops@` (the fleet routes need a key the checker never holds) |

### Guide contents

Each move guide is an ordered checklist. Every item links the existing guide that already explains it.

**Both guides**: run `setup.sh <sys>` and the compose template (names, ports, `welinc-network`); make the client key (`keys:client`, `seed:clients`); env names (contract 0001 section 15) and removing `JWT_SECRET`; copy `src/auth/verify/`, `account-check.ts`, `src/session/` (with AC-3's handling) and the directory reader, renaming the prefix; the web boot, Switch system and sign out (`web-login.md`); delete the user pages and link the portal, handle `ADMIN_CODE_REQUIRED` and `SIGN_IN_CODE_REQUIRED` (`suite-admin.md`); the activity map (`account-activity.md`); the deletion and erasure changes (`account-deletion.md`); switch the seed to `people.json` (`seed-accounts.md` step 6); `<prefix>/health`; skip `temporaryRoles` in pick lists; run the checker; open the PR into `development`; sign off.

**VMMS only**: the global `vmms` prefix and port 3010; delete the auth module, the `/users` controller, `client-platform.ts`, the phone and Semaphore code, `password_reset_tokens` and the logging of OTPs and passwords; drop the auth tables (data model above); mobile login, code screen, refresh and logout (contract 0001 section 8); remove `getMobileAccessRole` and `X-VMMS-Client`; analytics under `vmms/analytics` on 3011 verifying itself; serve the fleet API (`fleet-api.md`); move profile pictures to welinc-auth's picture route; `erased` rewrites of `actorEmail`.

**BMS only**: port `bms-gateway` to NestJS (keep `owner()` and the raw proxy loop, body parser off, 10 MB, all interfaces, `/bms` prefix, port 3020), with booking as the named fallback; Dockerfiles for every process on Node 24; ports 3021 to 3025; delete `auth-integration.mjs`, `LogIn.tsx`'s password form, the `jwt-decode` and `localStorage` code and the `/auth/users/:id/password` call; verify tokens in every process; `CUSTOMER_TRACKING_SECRET` with no fallback; drivers into dispatch, `vehicle_dispatch_profiles`, the fleet client (`fleet-api.md`); the analytics read model database; archive `welinc-backend`.

### VRMS Users page source

Decided 2026-11-13 (task 13a): backend-vrms keeps a copy of every person holding a VRMS role from the directory feed it already polls (`id`, `name`, `email`, `picture`, `roles`, `temporaryRoles`, `isActive`, `deleted`, `erased`), not only mechanics and chiefs, and serves the Users page list from it, behind the page's existing permission (`team.manage` or `users.manage`). The page shows Active, Inactive and Deleted (grace) only. Locked, Setup pending and Email not verified live on the portal's person page, behind Manage account. The directory and contract 0001 don't change. Runner up: adding `locked`, `emailVerified` and `passwordSet` to `DirectoryUser` (a feed trigger migration, and every system would receive account state it doesn't use).

### Key invariants

- No system other than welinc-auth reads the auth database, and no system reads another system's database (`welinc_db` included).
- A system's web client and its phone app never both admit the same role: `vmms` and `vmms-mobile`, `bms` and `bms-mobile` have disjoint `allowed_roles`.
- `user.systems` and the launcher's `systems` are the same list, so Switch system never leads to an `APP_NOT_ALLOWED`.
- BMS never dispatches on a cached vehicle status: the assignment reads VMMS fresh.
- The checker never reads a secret; a system passes or fails on behavior and code, not on what its owner says.

### Security model

- Web clients: office roles only (AC-1); enforced in welinc-auth at authorize, code exchange and refresh, so a system can't loosen it.
- `fleet.read`: only `bms` holds it; VMMS checks `aud` and `scope` on every fleet call; the API is read only and returns no person data.
- The `bms` client private key is a BMS secret (Container Apps secret hosted, git ignored `.env` locally), shared by the BMS processes that call out.
- The lookup limit closes an email enumeration path (30 a minute instead of the gateway's 1,200).
- AC-33 removes an unused admin write surface once nothing calls it.
- The checker's static scan blocks the known unsafe leftovers: shared secrets, auth database reads, tokens in browser storage or URLs, logged codes.

### Configuration required

- welinc-auth: none new.
- VMMS backend: `AUTH_ISSUER`, `AUTH_JWKS_URL`, `AUTH_INTERNAL_URL`, `AUTH_CLIENT_ID=vmms`, `AUTH_CLIENT_PRIVATE_KEY`, `WEB_APP_URL`, `PORTAL_URL`, `AUTH_PUBLIC_URL`, `API_PUBLIC_URL`, `SESSION_COOKIE_SECURE`, `TRUST_PROXY_HOPS`, `PORT=3010`. Removed: `JWT_SECRET`, `JWT_ACCESS_EXPIRY`, `JWT_REFRESH_EXPIRY`, `SEMAPHORE_*`.
- VMMS analytics: `AUTH_ISSUER`, `AUTH_JWKS_URL`, `AUTH_INTERNAL_URL`, `VMMS_API_BASE_URL` (internal), `PORT=3011`.
- VMMS web: `VITE_API_BASE_URL`, `VITE_PORTAL_URL` only. Mobile: `EXPO_PUBLIC_API_BASE_URL` (the gateway, LAN address locally).
- BMS (each process that verifies or calls out): `AUTH_ISSUER`, `AUTH_JWKS_URL`, `AUTH_INTERNAL_URL`; the gateway also the session values above with `AUTH_CLIENT_ID=bms`; booking and dispatch also `AUTH_CLIENT_ID=bms` and `AUTH_CLIENT_PRIVATE_KEY`; dispatch `VMMS_INTERNAL_URL`; booking `CUSTOMER_TRACKING_SECRET` (required). Removed: `JWT_SECRET`, `AUTH_DATABASE_URL`, `BMS_PARTNER_DATABASE_URL`, `PARTNER_BRIDGE_URL`.
- BMS web: `VITE_API_BASE_URL`, `VITE_PORTAL_URL` only.
- Every new name in the matching `.env.example`, never a value.

### Critical test scenarios

- Happy path: `vmms.ops@` opens a VMMS deep link signed out, signs in at the portal, lands on it; Switch system to VRMS as `multi.lead@`; sign out in BMS ends VRMS and VMMS within 30 s, verifies **AC-12**, **AC-18**, **AC-20**, **AC-31**
- Phone only: `vmms.mech@` at the portal sees "VMMS is on the WeLinc mobile app"; a seed driver sees "coming to"; `mech.juan@` goes straight to VRMS, verifies **AC-4**, **AC-5**, **AC-7**
- Refusal: `vmms.mech@` opening VMMS web lands on the APP_NOT_ALLOWED page; the same person signs in on the phone app, verifies **AC-1**, **AC-2**, **AC-3**, **AC-21**
- Fleet: VMMS sends a truck to maintenance; a BMS assignment to it answers 409 `VEHICLE_UNAVAILABLE` at once although the list cache still shows it; VMMS stopped gives 503 `FLEET_UNAVAILABLE`, verifies **AC-28**
- Auth: a VRMS token on `/vmms/` and `/bms/` answers 401; a user token on the fleet API answers 403 `WRONG_TOKEN_USE`; `vmms` asking `audience=VMMS` answers `invalid_target`, verifies **AC-10**, **AC-17**, **AC-23**, **AC-25**
- Leftovers: a planted `localStorage.setItem('token', ...)` makes the static scan fail with its `file:line`, verifies **AC-13**
- Removal: after AC-33, `GET /auth/users` answers 404 and the portal admin People view still works, verifies **AC-33**

## Build plan

Tracer Bullet: each shared change goes end to end and is proven on VRMS (and the portal) before the guides go out, then each group's move is its own thread, and the cleanup comes last. Tasks 1 to 13 are yours; the groups' checklists live in their guides and are tracked in the scope row.

*Slice 1, the thin thread: web vs app rules end to end, proven with VRMS and the portal*
1. welinc-auth migration `app_released` and the seed changes (`vmms` and `bms` `allowedRoles`, `app_released`, `vmms.mech@` in `people.json`, the VRMS copy and `seed-accounts.md`), satisfies **AC-1**, **AC-6**, **AC-8**
2. Launcher split in `launcher.ts` (`systems`, `mobileSystems`, `user.systems`) and the 200 for phone only people on the three routes, satisfies **AC-4**, **AC-5**
3. `/auth/authorize` refusal with `error_description=APP_NOT_ALLOWED`, satisfies **AC-2**
4. VRMS reference callback, `auth-client.ts` `not_allowed` and refresh handling, satisfies **AC-3**
5. Portal: the phone only state, the launcher line and the `APP_NOT_ALLOWED` page, satisfies **AC-7**

*Slice 2, the rest of the shared side*
6. The lookup limit on both routes (one `lookup:<sub>` counter), satisfies **AC-9**
7. `bms` `serviceScopes` with `VMMS: [fleet.read]`, and the unit test for a scope on a non `AUTH` audience, satisfies **AC-10**
8. Contract 0001 version 8 (sections 4, 7, 10 to 14, move order, gap map), satisfies **AC-11**

*Slice 3, the kit, proven on VRMS*
9. `scripts/check-system.mjs`: the live checks (VRMS set first, then the VMMS and BMS extras behind their system, the fleet checks as their own group), the static scan, exit codes; mark VRMS's `GET /auth/users` call `// check-system: allow AC-33 pending`; `check-system.mjs vrms` passes, satisfies **AC-12**, **AC-13**, **AC-14**
10. `setup.sh` and `start.sh` for `vmms` and `bms` (compose when present, keys, migrations, seeds, health), satisfies **AC-16**
11. `move-vmms.md`, `move-bms.md`, `fleet-api.md`, the compose templates and the README rows; tell both groups, satisfies **AC-15**

*Slice 4, the moves (the groups build AC-17 to AC-30 in parallel; you track)*
12. Per group, when its PR is up: review the checker output (it proves the group's AC-17 to AC-23 for VMMS, AC-24 to AC-29 for BMS), then run the cross system steps in `verify.md` and tick the group in the scope row; after BMS, confirm `welinc-backend` is archived, satisfies **AC-17** to **AC-31**

*Slice 5, cleanup, after both groups pass*
13a. VRMS Users page off `GET /auth/users`: backend-vrms keeps every VRMS person from the directory feed and serves the list; the page shows Active, Inactive and Deleted only (*VRMS Users page source*); drop the `allow AC-33 pending` line, satisfies **AC-33**
13. Gate: `check-system.mjs vrms|vmms|bms --static-only` finds no `/auth/users` or `/auth/deletion-requests` caller and no `allow AC-33 pending` line, or the task stops. Then remove the bearer admin routes, their tests and DTOs; contract 0001 version 9, satisfies **AC-33**
14. Staging run of the cross system steps once VRMS feature 26 is live, satisfies **AC-32**

## Migration plan

**Strategy**: hard switch per system (contract 0001's rule), each system on its own branch, VMMS and BMS in parallel. No dual run: no system has real users or data to protect.
**Phases**:
1. Shared side (slices 1 to 3) merges into `development` first. VMMS and BMS keep working on their old auth meanwhile: nothing in slices 1 to 3 changes a route they call today (AC-1 and AC-4 only affect the new clients). The guides tell the groups not to run `seed:clients` against the shared stack before they start their move.
2. Each group's move merges as one set (backend, web, mobile or analytics together), after its checker passes, then the group reseeds.
3. Cleanup (slice 5) once both are in.
**Rollback**: a group's move reverts by reverting its own merge (its old auth comes back with its old seed). The shared side's slices are additive for VMMS and BMS until slice 5, which waits until nothing calls the routes.
**Risks**: a group stalls and holds AC-33 back (the bearer routes stay, deprecated, harmless); BMS's gateway port breaks uploads (the checker's large body check); VMMS's mobile app on a phone can't reach the gateway (LAN address, `web-login.md` and contract section 8); the fleet API adds a runtime dependency from BMS on VMMS (503 `FLEET_UNAVAILABLE`, no silent stale dispatch).

## Consequences

**Positive**:
- One login, one user list and one gateway for all three systems; contract 0001's gap map closes.
- The old Capstone 1 database and the auth copy with admin checks off are gone.
- The checker makes "moved" a fact anyone can rerun, and it keeps guarding against regressions after S11.
- The fleet API is the first real domain contract between systems and the pattern feature 56 builds on.

**Negative / tradeoffs**:
- S11 grew: the fleet API and BMS's data moves pull part of feature 56 forward, on a deadline (accepted, your call).
- BMS's dispatch now depends on VMMS being up; when it isn't, BMS can't list or assign trucks.
- Three copies of the VRMS auth code exist; a fix in one must be copied, and only the checker catches a missed copy.
- Mechanics who hold VRMS and VMMS go straight into VRMS instead of seeing the launcher, since VMMS no longer counts as a web system for them.
- The launcher answer changes shape for phone only people (200 instead of 403): a breaking change for any client other than the portal (none exists).
- Your cross check per group is manual time near the deadline.

**Neutral**:
- `app_released` must be flipped (a seed change) when bms-mobile ships.
- `/auth/activity` stays as a bearer admin read, the one admin route outside `/auth/admin/*`.
- VRMS's session code gains a branch it never takes itself (AC-3), for the copies' sake.

## Follow-up

- [ ] Tell VMMS and BMS when slice 3 lands: the guides, the checker, the deadline for their PRs, and that they decide nothing in the shared repos.
- [ ] VRMS feature 56 absorbs the fleet API as its first contract, and settles whether VRMS's and VMMS's garages are one list.
- [ ] Flip `bms-mobile` `app_released` to true when the BMS app ships (one seed line).
- [ ] If a fourth system joins or the copies drift, revisit a shared auth package.
- [ ] Spec 0008 (VRMS hosting) owes the VMMS and BMS services in the hosted setup, for AC-32.
- [ ] The checker also runs on each group's CI later (not required for S11).
