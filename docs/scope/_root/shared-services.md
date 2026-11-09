# Scope: WeLinc shared services

The shared services (auth, portal, gateway) that VRMS, VMMS and BMS should all run on. Today only VRMS uses them: VMMS keeps its own copy of auth, BMS reads the auth database directly, and neither has a portal handoff. This epic turns the shared services into something the other two groups can actually move onto. Part of the [suite scope map](../index.md).

**Build approach:** Tracer Bullet (each piece built end to end and proven on VRMS first, since VRMS already runs on the shared services; the other groups then move onto it with S11).
**Workflow:** GA (after `/develop`: `/check verify`, `/test`, a fresh model `/check review`, then `/document`). Auth, sessions and admin rights are where a mistake exposes every system's data.

_These are recommendations to keep the build orderly, not requirements. Skip anything that does not fit. You decide when a row is `done`._

**Ownership:** these are shared files and shared repos (`welinc-auth`, `welinc-web-portal`, the gateway). Changes go through a spec in `docs/specs/_root/` and a pull request the other groups can see. The VMMS and BMS groups do their own moves in their own repos (S11); this epic gives them the contract, the routes and a migration guide.

**Start:** after VRMS feature 65 task 10 and the verify runs for features 58 and 65, with their PRs open (decided 2026-11-07). Before the VRMS workflow review topics.

## What the other systems have today (read only check, 2026-11-07)

- **VMMS** (`welinc-backend-vmms`, `development`): its own `users`, `user_roles`, refresh tokens bound to web or mobile (`X-VMMS-Client`), login activity, phone verification and `audit-logs`, all under its own `/auth/*`. Its web app (8002) and the mobile app (`welinc-mobile-vrms_vmms`, Expo) call that copy, not welinc-auth. A VMMS account must hold exactly one VMMS role (Admin, Operations, Chief Mechanic, Mechanic). Its web app already accepts `?token=` from the portal. Its analytics service checks callers with `GET auth/me?system=VMMS` on the VMMS backend.
- **BMS** (`welinc-backend-bms`, `latest-bms-backend`): five processes (booking 3002, dispatch 3003, completion 3004, gateway 3005, analytics projection). They verify welinc-auth tokens (HS256, shared `JWT_SECRET`), but the BMS gateway reads `users`, `user_roles` and `user_activity_logs` straight from the auth database. Its web app (5173) calls `/auth/profile/activity`, `/auth/profile/verify-password` and `/auth/profile/deletion-request`, which welinc-auth does not have, and has no portal handoff ("until Auth owners approve an SSO contract"). BMS roles: Admin, Customer Support, Operations. Its auth runs from the `latest-auth-backend` branch of the old `welinc-backend` repo (pushed 2026-11-06): systems are only `BMS` and `SHARED`, the admin checks are removed from every `/auth/users*` route for local testing (`LOCAL_DEV_BYPASS.md`), there is no refresh, and the only activity it logs is a successful login. `verify-password` and `deletion-request` exist nowhere, so the BMS profile page calls routes that always fail; the BMS gateway answers `profile/activity` itself from the auth database.
- **Seed accounts:** every system holds only seed accounts copied from the same shared seed, with drift: `ops.user@welinc.com` is Oscar Santos (BMS Operations) in welinc-auth and the BMS copy but Oscar Ramos (VMMS Operations) in VMMS; VMMS adds two chief mechanics (`vmms.chiefmech`, `vmms.chiefmech2`) that welinc-auth lacks; the 5 named and 60 bulk mechanics match by email but VMMS gives them only VMMS roles.
- **Ports that clash:** VMMS backend 3000 (the gateway), both analytics services default to 3001 (auth), BMS booking 3002 (backend-vrms). The gateway routes only `/auth`, `/vrms` and `/repairs`.
- **welinc-auth gaps:** a `RefreshToken` table but no refresh or logout route, no login activity, no phone verification, one shared signing secret every service holds.

## At a glance

| # | Feature | Phase | Status |
|---|---------|-------|--------|
| S1 | Shared services contract | Contract | done |
| S2 | Signing keys and service identity | Core | done |
| S3 | Sessions: refresh and logout, web and mobile | Core | done |
| S5 | Roles per system | Core | done |
| S6 | User directory for systems | Core | done |
| S12 | Suite seed accounts | Core | planned |
| S4 | App initiated login and launcher | Login | planned |
| S9 | Gateway for the whole suite | Gateway | planned |
| S7 | Account activity and audit | Account | planned |
| S8 | Profile extras | Account | planned |
| S13 | Email verification | Account | planned |
| S11 | Move VMMS and BMS onto the shared services | Cutover | planned |
| S10 | Suite admin model | Admin | planned |

## Contract

### S1. Shared services contract · done
spec [0001](../../specs/_root/0001-shared-services-contract/index.md)

One suite spec that every group can build against: the auth API surface, the login handoff, token format and signing, per system roles, the user directory, gateway routes and the port map, and the order the other groups move over in. It replaces the auth and gateway part of VRMS feature 56.
**Done when:** `docs/specs/_root/` holds the contract with every route, claim and port, and each gap listed above maps to a row here.
- Note (2026-11-08): you decided the other groups don't review the spec; you tell them what changes as each piece lands.
- Note (2026-11-07): two questions for BMS are in `docs/_private/vrms/shared-services-questions.md` (outside git): whether their auth copy runs anywhere online, and whether `welinc-mobile-bms` is still used. Hosting is settled here instead of asked: the shared services run with VRMS's hosting (feature 26) behind one public gateway address, and each system adds its deployed web addresses to the CORS list and the login return allow list. Everything else is read from their code or decided by the team in this spec: the auth routes they need (listed above), which of their records point to user ids (their schemas), deep links surviving login, a code exchange on their backends, logout from one system ending the shared session, published keys instead of `JWT_SECRET` (the BMS tracking token gets its own secret), keeping VMMS's one role rule and web vs mobile sessions as their per system rules, phone numbers owned by welinc-auth (VMMS sends SMS with Semaphore), verify password only guarding the BMS deletion request, and a deletion request that an admin reviews before deactivating (history kept).
- Note (2026-11-08): spec 0001 is the contract (version 1). Decided: a token per system, ES256 published keys, a code exchange on each system's backend with an HttpOnly refresh cookie on a custom domain (working name `welinc.tech`), a native mobile login on its own route, 30 minutes idle (tracked on the server) and 12 hours for web, 7 days rolling for mobile, a 30 s session check, `private_key_jwt` for backends, a cursor change feed for users, prefixes owned by each service, gateway config in `infra/gateway/`, a port block per system, a hard switch with no dual run, and BMS moving before VMMS. Its gap map ties every gap above to a row.
- [x] Design it (spec): `/architect shared services contract`

## Core

### S2. Signing keys and service identity · done
spec [0002](../../specs/_root/0002-signing-keys-service-identity/index.md) · code in `welinc-auth/src/auth/` (keys, tokens, clients), `welinc-auth/scripts/`, `welinc-backend-vrms/src/auth/verify/`

Today every service holds the one `JWT_SECRET`, so any of about eight services could mint a token for any system. Move to keys only welinc-auth can sign with, published so services verify without a secret, plus a way for services to call each other (BMS's internal key, analytics checking callers).
**Done when:** only welinc-auth can sign tokens, every service verifies with the published keys, a key can be rotated without downtime, service to service calls carry their own identity, and no service needs `JWT_SECRET`.
- Note (2026-11-08): spec 0002 decided `jose` everywhere, ES256 keys in `AUTH_SIGNING_KEYS` with a rotation script that refuses unsafe steps, a seeded `OAuthClient` registry, the client credentials grant with a `jti` replay table, an interim login token whose `aud` welinc-auth picks until S4, and a copyable token check in backend-vrms (`src/auth/verify/`). Hard switch: auth, backend-vrms, portal and compose merge together.
- [x] Design it (spec): `/architect signing keys and service identity`
- [x] Build it: `/develop signing keys and service identity`
  - [x] ES256 end to end, the hard switch (keys loader, login `aud`, JWKS and metadata, both guards, portal redirect, compose and env) · AC-1 to AC-12, AC-22, AC-23, AC-25
  - [x] Clients and service identity (registry migration and seed, `/auth/token`, replay, rate limit, `/auth/users` for service tokens, VRMS roster on its own token) · AC-13 to AC-22, AC-27
  - [x] Rotation and handover (`keys:rotate`, `keys:client`, the rotation test, the folder README, `docs/keys.md`) · AC-24 to AC-26
- [x] Verify it: `/check verify signing keys and service identity` (2026-11-08, local stack; the staging rotation, AC-24 and AC-26, is owed until spec 0008 exists)
- [x] Test it: `/test signing keys and service identity` (2026-11-08; welinc-auth 230, backend-vrms 1400, portal 33 passing; UI look and cross origin redirect stay with verify)
- [x] Review it (fresh model): `/check review signing keys and service identity` (skipped by choice, 2026-11-08; not run)
- [x] Document it: `/document signing keys and service identity` (2026-11-08, PR bodies: auth #15, backend-vrms #45, portal #12, workspace #12)

### S3. Sessions: refresh and logout, web and mobile · done
spec [0003](../../specs/_root/0003-sessions-refresh-logout/index.md) · code in `welinc-auth/src/auth/` (sessions, token endpoint), `welinc-backend-vrms` (session routes, account check), `welinc-web-vrms` (boot, refresh, idle), `welinc-web-portal` (login)

Short lived access tokens with refresh and logout in welinc-auth, for web and for the mobile app, so VMMS can drop its own copy. Covers web vs mobile bound sessions, the way VMMS has them today.
**Done when:** web and mobile sessions refresh without a new login, refresh tokens rotate and a reused one ends the session, logout ends it on the server, an admin can end all of a user's sessions, and VRMS, VMMS web and the mobile app all use it.
- Note (2026-11-08): spec 0003 also builds the web code exchange (authorize, SSO cookie, VRMS's session routes) that 0001 had put in S4, since a web app only gets its refresh cookie through it. It also decides chained refresh token rows with the grace token encrypted under the old one, web refresh not counting as activity, a cap of 10 sessions, an automatic lock that blocks logins but ends no live session, and a hard switch of auth, backend-vrms, web-vrms and the portal together.
- [x] Design it (spec): `/architect sessions refresh and logout`
- [x] Build it: `/develop sessions refresh and logout`
  - [x] The web thread end to end (2026-11-08; migration, login with the SSO cookie, authorize and code exchange, rotation, `/auth/session`, VRMS session routes, in memory token, portal login, gateway CORS, contract amendments) · AC-1, AC-5, AC-7 to AC-21, AC-26, AC-27, AC-36, AC-40, AC-41, AC-43
  - [x] Session endings and idle (2026-11-08; logout, activity pings, ending events, cap, hourly job, idle warning, Reconnecting banner) · AC-2 to AC-4, AC-6, AC-22 to AC-25, AC-37 to AC-39, AC-42
  - [x] Mobile routes, tested by API (2026-11-08; `/auth/mobile/login`, mobile refresh with `audience`, logout by refresh token, 7 day rolling idle, limits; any public native client row works, so a later `bms-mobile` needs only a seed row) · AC-28 to AC-30, AC-38
  - [x] Seeing and ending sessions (2026-11-08; `/auth/me/sessions`, `/auth/users/:id/sessions` with end all and its change record, the device label parser, Signed in devices card, Sessions dialog on Users) · AC-31 to AC-35
- [x] Verify it: `/check verify sessions refresh and logout` (2026-11-08, local stack; every verify.md step passed, the 12 hour follow up included)
- [x] Test it: `/test sessions refresh and logout` (2026-11-08; welinc-auth 272, backend-vrms 1447, web-vrms 448, portal 10 passing; database, component and browser flows stay with verify)
- [x] Review it (fresh model): `/check review sessions refresh and logout` (skipped by choice, 2026-11-08; not run)
- [x] Document it: `/document sessions refresh and logout` (2026-11-08; PRs auth #16, backend-vrms #46, web-vrms #48, portal #13, workspace #13)

### S5. Roles per system · done
spec [0004](../../specs/_root/0004-roles-per-system/index.md) · code in `welinc-auth/prisma/catalog/`, `welinc-auth/src/auth/roles/`, `welinc-web-vrms/src/features/user-management/`

Each system declares its roles and rules (VMMS: exactly one role per account; BMS: Admin, Customer Support, Operations; VRMS: Admin, Chief Mechanic, Mechanic), and welinc-auth enforces them, instead of one shared enum and rules copied into each system.
**Done when:** each system's allowed roles and rules live in one place in welinc-auth, user admin rejects a role a system does not have, and adding a role to one system needs no change in the others.
- Note (2026-11-08, from a look at a friend's company suite (SBSI User & Access Management) on 2026-11-08, ideas to weigh in the spec, nothing decided): let each system publish its own permission catalog (VRMS already has its matrix and `/permissions/me`, spec 0011) and show them read only through `/auth/systems`, named `system.resource.action` (VRMS keys get a `vrms.` prefix there, e.g. `vrms.ticket.view_all`). Each system still decides and enforces its permissions; welinc-auth only shows them, so the S10 access report can answer "who can approve costs anywhere in the suite". Don't copy their model of one central catalog where the access service owns every permission (it drifts: empty systems, undescribed permissions, old and new slugs mixed), nor global roles shared across systems.
- Note (2026-11-08): BMS says `welinc-mobile-bms` is for drivers and helpers (WeLinc staff in the field), so BMS needs Driver and Helper roles here, and a `bms-mobile` client row like `vmms-mobile`. They log in with their own email like everyone else (any real email domain works).
- Note (2026-11-08): spec 0004 decided a role catalog in welinc-auth: `systems` and `system_roles` tables synced by `catalog:sync` from one file per system (`prisma/catalog/`), a foreign key from `user_roles`, one role per person in each system (`maxRolesPerUser`, a per system number), an `isSystemAdmin` flag replacing `@Roles(ADMIN)`, allowed roles per app per system (`vmms-mobile`: Mechanic and Chief Mechanic; a new `bms-mobile`: Driver and Helper) checked on every grant, a public `GET /auth/systems`, and the VRMS role picker reading it. The `SystemType` enum stays; the `UserRole` enum goes. The sync refuses dropping a role people hold; the migration fixes bad rows keeping the most powerful role. Deploys stop welinc-auth, run `npm run db:deploy`, then start it. Permissions stay for S10.
- [x] Design it (spec): `/architect roles per system`
- [x] Build it: `/develop roles per system`
  - [x] Thin thread: migration, catalog files and sync, `db:deploy`, role checks under the account lock, `GET /auth/systems`, VRMS picker on it · AC-1 to AC-11, AC-13, AC-16, AC-20
  - [x] Admin flag and `/auth/me`: `@SystemAdmin()`, every `UserRole` use moved (the raw SQL in `assertAnotherAdmin` included), the grep gate, own role tests · AC-12, AC-14, AC-15, AC-17
  - [x] Allowed apps: `allowed_roles`, `vmms-mobile` and `bms-mobile` seed, the grant filter and `APP_NOT_ALLOWED` · AC-18, AC-19
  - [x] Seed, docs and contract 0001 amendments, tests · AC-5, AC-21
- [x] Verify it: `/check verify roles per system`
- [x] Test it: `/test roles per system` (2026-11-09; welinc-auth 322, web-vrms 464 passing; role picker, `useVrmsRoles` and database flows stay with verify)
- [x] Review it (fresh model): `/check review roles per system` (skipped by choice, 2026-11-09; not run)
- [x] Document it: `/document roles per system` (2026-11-09; PRs welinc-auth #18, welinc-web-vrms #50, welinc-workspace #15)

### S6. User directory for systems · done
spec [0005](../../specs/_root/0005-user-directory/index.md) · code in `welinc-auth/prisma/migrations/` (feed trigger), `welinc-auth/src/auth/` (directory routes), `welinc-backend-vrms/src/modules/vrms/` (poll job, roster), `welinc-web-vrms/src/features/user-management/`

Systems need names, emails and roles for people their records point to (VMMS schedules, BMS activity, VRMS mechanics) without their own users table or reading the auth database. Give them a lookup API and a change feed, generalizing VRMS's mechanic sync.
**Done when:** a system can look up many users by id in one call, learns about created, changed and deactivated users without polling every user, keeps only a local copy of what it needs, and no system reads the auth database.
- Note (2026-11-09): spec 0005 decided a `directory_changes` feed written by deferred Postgres triggers (one row per person per save, only when something a system can see changed, a snapshot of the person after it), read in transaction order with an epoch in the cursor, three service only routes, and `/auth/users` back to admins only. VRMS polls every 30 s with a leased job, refreshes one person after its own Users page saves, keeps the just in time update, and drops the full downloads on page loads. Contract 0001 sections 9 and 10 get amended. Hard switch: auth, backend-vrms and web-vrms merge together.
- [x] Design it (spec): `/architect user directory for systems`
- [x] Build it: `/develop user directory for systems`
  - [x] Thin thread: feed migration and triggers, backfill, seed in one save, `/directory/changes` and `/directory/users`, VRMS sync state and the leased poll job · AC-1, AC-2, AC-4, AC-5, AC-7, AC-8, AC-11 to AC-13, AC-16
  - [x] Lookup and instant refresh: `/directory/users/lookup`, `refreshOne` and the refresh route, web-vrms drops page open syncs · AC-6, AC-18 to AC-20
  - [x] Hardening and the switch: apply failure, auth down, `INVALID_CURSOR`, recovery sync, `/auth/users` admin only, every write path tests · AC-3, AC-9, AC-14, AC-15, AC-17, AC-21
  - [x] Contract 0001 amendments and docs · AC-10
- [x] Verify it: `/check verify user directory for systems`
- [x] Test it: `/test user directory for systems`
- [x] Review it (fresh model): `/check review user directory for systems` (skipped by choice, 2026-11-09; not run)
- [x] Document it: `/document user directory for systems` (2026-11-09; PRs welinc-auth #19, welinc-backend-vrms #48, welinc-web-vrms #51, welinc-workspace #16)

### S12. Suite seed accounts · planned · needs a decision · Beta
One seed in welinc-auth for all three systems instead of three drifting copies: fixed ids every system links its own rows to (as VRMS already does with `SEED_IDS`), one person per email, and people chosen to test the shared login.
**Done when:** each system's roles have at least one seed person; there are accounts holding one, two and three systems for the launcher; a locked, a deactivated and a never verified account exist for testing; the platform admin from S10 has a seed account once S10 is built; no email means two different people across systems; and each system's own seed links to the shared ids instead of creating users.
- Note (2026-11-08, replan): from specs 0001 and 0002. This row gets its own spec, and it must keep and extend spec 0002's `OAuthClient` seed, creating the section 4 clients alongside the people.
- Note (2026-11-07): fixes the drift listed above (`ops.user` and the VMMS chief mechanics). Keep `@welinc.com` addresses for seeds. The seed writes users straight to the database, so no email check applies to them. Real users may use any email whose domain can receive mail, such as Gmail.
- Note (2026-11-09, from spec 0004 follow-up): the seed needs people for every role in the catalog, Driver and Helper (BMS) included, one role per person where a system says so.
- [ ] Design it (spec): `/architect suite seed accounts` (or inside the S1 spec)

## Login

### S4. App initiated login and launcher · planned · needs a decision
Replaces VRMS feature 60. Each app sends people to the portal with a return address and gets them back through a one time code it exchanges on its backend, not `?token=` in the URL. The portal shows a launcher of your systems only when opened directly (skipped when you have one), and each app gets a Switch system link.
**Done when:** a deep link into any system survives login; tokens never appear in a URL; return addresses are checked against an allow list; the launcher lists only the systems you hold; one system users never see it; Switch system and logout work from every app; no new role or permission is created; and VMMS and BMS can use it.
- Note (2026-11-07): chosen over the portal side picker (feature 60 as planned) and over separate login pages per system. Follows the app launcher pattern of Okta and Microsoft My Apps.
- [ ] Design it (spec): `/architect app initiated login and launcher`
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (one, two and three systems, long names)

## Gateway

### S9. Gateway for the whole suite · planned · needs a decision
One gateway that routes every system and analytics service, with a port map that has no clashes, and a decision on where the gateway config lives (today inside `welinc-auth`).
**Done when:** every system's API and analytics service is reachable through the gateway, each service has its own port in the README repos table, CORS and upload limits are set per route, and the config lives where the contract says.
- [ ] Design it (spec): `/architect gateway for the whole suite`
- [ ] Polish it (optional, ask first): `docker-patterns`

## Account

### S7. Account activity and audit · planned · needs a decision
Login activity and account change history from welinc-auth, so VMMS (`me/login-activity`, `users/:id/login-activity`, `audit-logs`) and BMS (`profile/activity`, its activity log page) stop keeping or reading their own.
**Done when:** each login, failed login, lockout, logout and refresh is recorded with device and address; a user sees their own; a system admin sees their system's users and account changes; and nothing outside welinc-auth reads those tables.
- Note (2026-11-08, from a look at a friend's company suite (SBSI User & Access Management) on 2026-11-08, ideas to weigh in the spec, nothing decided): one activity page with login events and account changes (`UserChange`) in a single timeline, filtered by category, actor, date and address, like their Security & Activity Audit Trail. Lessons from their bugs: log the real client address from `X-Forwarded-For` (they log the Docker gateway `172.19.0.1` for everyone), record a logout once (they log the same one twice in the same second), and keep emails out of the event text since the log is kept forever.
- [ ] Design it (spec): `/architect account activity and audit`

### S8. Profile extras · planned · needs a decision · Beta
The profile routes the other apps already call: phone verification (VMMS), verify password before a sensitive action and an account deletion request (BMS).
**Done when:** phone numbers can be verified by code, a sensitive action can ask for the password again, a user can request deletion and an admin of each of their systems sees it, and every one of these events is logged.
- Note (2026-11-09, replan, from spec 0005 follow-up): add a phone verified column in welinc-auth, put it in the `directory_changes` snapshot (a migration that changes the trigger) and map it to `phoneVerified`. If a deletion request erases personal data, it must also clear that person's feed snapshots, which otherwise keep names, emails and phones forever.
- [ ] Design it (spec): `/architect profile extras`

### S13. Email verification · planned · needs a decision
Prove a person owns their email before the suite relies on it, instead of only checking that the domain can receive mail. Today `emailVerified` turns true only when someone uses a setup or reset code; an account an admin creates with a typed password, and any email change by an admin or on the profile, is never checked.
**Done when:** every new account and every email change sends a code or link to that address; `emailVerified` is true only after it is used; admins and the user can see whether an email is verified and send the code again; the rule for an unverified account (sign in allowed or not, which emails it gets) is decided and enforced.
- Note (2026-11-08): found while checking the email domain rule. The domain check accepts any real domain (Gmail works); the test domain skip list now applies only outside production. Setup and reset codes used `Math.random()`; fixed the same day with `crypto.randomInt` (`newOtp()` in `auth.service.ts`). Questions for the spec: code or link; whether an unverified account may sign in; what happens to the old email on a change (keep it until the new one is verified, and tell the old address); and how this fits drivers and helpers on BMS mobile (S5).
- [ ] Design it (spec): `/architect email verification`

## Cutover

### S11. Move VMMS and BMS onto the shared services · planned · needs a decision
The move itself: their users merged into welinc-auth by email, their auth copies and direct database reads removed, their apps on the portal login. Their groups change their own repos; this row gives them the migration guide, a user import script and a test plan, and tracks it to the end.
**Done when:** every VMMS and BMS account logs in through welinc-auth with no duplicates, neither system has its own users or tokens tables or reads the auth database, all three systems run together behind one login on staging, and each group signs off.
- Note (2026-11-07): the old `welinc-backend` repo where BMS pushed an auth copy is part of this cleanup.
- Note (2026-11-08, replan): from spec 0002. The migration guide tells each group to copy `welinc-backend-vrms/src/auth/verify/`, make their client key with `keys:client`, and move to Node 24 (`welinc-backend-vmms-analytics-ai` pins Node 20, end of life since April 2026). From spec 0001: if `welinc-mobile-bms` is still in use, it becomes a `bms-mobile` client like `vmms-mobile`.
- Note (2026-11-08): BMS keeps the mobile app, but for different users than its web app. They likely haven't started building it, and you asked them on 2026-11-08 who will use it. If they are staff, it's a `bms-mobile` client plus a role in S5. If they are customers, their login is a separate suite decision that has to be made before this row's guide. The question is in `docs/_private/vrms/shared-services-questions.md`.
- Note (2026-11-09, from spec 0004 follow-up): the migration guide tells VMMS to drop its client side `getMobileAccessRole` check once `vmms-mobile` moves (welinc-auth now refuses it with `APP_NOT_ALLOWED`), and BMS to read role names from `GET /auth/systems`. Still to confirm with VMMS and BMS: BMS Driver and Helper, one role per person, any role they plan before the deadline, and whether the VMMS Admin still manages VMMS users.
- Note (2026-11-09, replan, from spec 0005 follow-up): the migration guide points VMMS and BMS at the VRMS directory reader as the one to copy (`welinc-backend-vrms/src/modules/vrms/directory/`: `directory_sync_state`, the lease, stop on failure), and the BMS gateway moves off `users`, `user_roles` and `user_activity_logs` onto `/auth/directory/*`.
- [ ] Design it (spec): `/architect move VMMS and BMS onto the shared services`

## Admin

### S10. Suite admin model · planned · needs a decision · GA
Replaces VRMS feature 61 with the same scope (the full model, chosen 2026-11-07). A platform admin in welinc-auth manages accounts and grants each system's roles but sees no system's data without that system's own role. One or two break glass accounts need MFA, log a reason and alert every admin on each login. An admin access report shows who holds admin where and since when. Every admin grant or removal alerts and logs, and nobody can raise their own access.
**Done when:** all of the above hold, checked on the server, and the VMMS and BMS groups agree.
- Note (2026-11-07): a single everyday `SUPERADMIN` role that skips checks stays out on purpose (the Capstone 1 panel called it insecure), as does temporary elevation. The MFA step uses VRMS feature 34's OTP. It builds on spec 0009's change record and spec 0011's system scoping.
- Note (2026-11-07, reopened, to discuss before `/architect`): two inputs to weigh against the model above.
  - Claude's suggestion: a real Super admin role in welinc-auth (at most 3 holders, MFA, the last one can't be removed); no hidden bypass, so using a system still needs that system's role; giving yourself a system role is allowed but expires (about 8 hours), needs a reason and alerts that system's admins; keep the access report and admin change alerts; break glass dropped for now.
  - A healthcare suite you heard about: an auth level admin with access to all four of their systems; inside each system a superadmin who can do everything across all branches and holds the system's configuration; and a branch admin (the manager) per branch, with branches and departments as scopes. Only an idea from their own system, not a model to copy. Decided 2026-11-07: no branch or garage level admin for WeLinc, since staff are few; each system keeps one Admin level that covers all garages and holds its settings (VRMS feature 52). Still open: whether the suite admin can open a system's data.
- Note (2026-11-08, from a look at a friend's company suite (SBSI User & Access Management) on 2026-11-08, ideas to weigh in the spec, nothing decided): make the admin access report the landing page of suite admin, like their governance dashboard: who holds admin in each system, locked accounts, recent role grants and removals, deletion requests waiting, the last account events. Add a "who has this permission" view (their Assign to Roles from the permission side) using the S5 catalog. Their split of IT Admin (accounts and roles) from Admin (business work) supports the platform admin idea; their everyday Super Admin role is the thing to avoid.
- Note (2026-11-08, leaning, may change in the spec): **no self grants.** Nobody can give themselves a role, superadmin included; the server blocks it, and another admin has to grant it. The one exception is **temporary access with a reason**: a superadmin may give themselves a system role that expires after a few hours, only with a written reason, and it alerts that system's admins and is logged. Every role grant or removal alerts that system's admins and shows in the access report, so a second account made to get around the rule is visible. Superadmin stays capped at about 3 people. This replaces the 2026-11-07 suggestion above where it differs.
- Note (2026-11-08, VMMS feedback): VMMS prefers the superadmin to have **no access to system data**, since each system has its own admin and the superadmin controls permissions; temporary access only in some cases. Their Admin now has reduced access (most of their workflow sits with Operations), and they plan to move to permission checks instead of role checks. To confirm with them: permissions granted to roles (the plan) or to individual people, and whether the VMMS Admin still manages VMMS users.
- Note (2026-11-08, leaning, may change in the spec): **user admin moves to the portal, scoped by who is looking.** Account actions (create, edit name and email, role, reset or setup code, unlock, sessions, deactivate, activity) live in a portal admin section: a system Admin sees only their system's people and gives only their system's roles; the superadmin sees everyone plus the access report and permission settings. Each system keeps only work data about the person. Read only check of the 2026-11-06 code: the VMMS (`UserManagement.tsx`, 614 lines) and BMS (`admin/UserManagement.tsx`, 837 lines) pages are pure account actions on `/auth/users*` with no work data, so they delete them and their sidebar item links to the portal; their profile pages (VMMS phone check, BMS activity, verify password, deletion) can use the portal's My account too. VRMS keeps its Users page as a team and work view (role and status shown, Work column, open tickets, Reassign; Edit, reset, unlock, sessions and deactivate become one **Manage account** link; **Add user** opens the portal form with VRMS picked), keeps the Chief Mechanic dashboard Team section, and keeps its own My profile page (it already calls welinc-auth). Leavers: the portal cuts the account off right away and warns that open work gets flagged; VRMS reacts to the S6 change feed (`deactivated`, `roles_changed`) by flagging the person's open tickets as needing reassignment and alerting Chief Mechanics, which also covers a shared account deactivated from another system. Tell VMMS and BMS not to build more user management meanwhile.
- Note (2026-11-08, leaning, may change in the spec): **permissions edited centrally, optional per system.** The system admins and the superadmins are the same IT/operations team, so the role to permission matrix moves to suite settings and only a superadmin edits it (like Auth0's RBAC). Each system's code still declares which permissions exist (`vrms.ticket.view_all`) and still runs the check itself, reading its matrix from welinc-auth and keeping a copy that refreshes on change; permissions don't go in the token. VRMS moves first, and its settings page stops editing the matrix. BMS and VMMS may keep checking roles in their own code and join later. Every matrix edit is logged and alerts that system's admins. Open: where the suite settings screen lives (the portal is the likely home). S5 only leaves room for this in `/auth/systems`.
- Note (2026-11-09, from spec 0004 follow-up): build on the `isSystemAdmin` flag and `GET /auth/systems` from S5 (additive permissions field later). Close the self grant hole with the temporary access exception here.
- [ ] Design it (spec): `/architect suite admin model`
- [ ] Polish it (optional, ask first): `web-design-guidelines` (access report)

## Why this order

- **The contract first.** The other groups are waiting on a supported contract (BMS says so in its code), and one spec stops three groups from guessing. (basis: spec first rule for shared repos in `AGENTS.md`)
- **Keys, sessions, roles and the directory before login.** The login handoff hands out tokens in the new format, with the new sessions, for the right roles; building it first means redoing it.
- **Gateway before account features.** The other groups can't call welinc-auth through one address until their routes and ports exist.
- **Account features before the move.** Their apps already call those routes; moving them earlier would break their screens.
- **Suite admin last.** It needs the new roles, the directory and OTP, and nobody is blocked without it.

## Legend

Same as the [VRMS legend](../vrms/index.md#legend). Rows here use `S` numbers so they never collide with a system's own numbers.
