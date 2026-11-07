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
| S2 | Signing keys and service identity | Core | in-progress |
| S3 | Sessions: refresh and logout, web and mobile | Core | planned |
| S5 | Roles per system | Core | planned |
| S6 | User directory for systems | Core | planned |
| S12 | Suite seed accounts | Core | planned |
| S4 | App initiated login and launcher | Login | planned |
| S9 | Gateway for the whole suite | Gateway | planned |
| S7 | Account activity and audit | Account | planned |
| S8 | Profile extras | Account | planned |
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

### S2. Signing keys and service identity · in-progress
spec [0002](../../specs/_root/0002-signing-keys-service-identity/index.md)

Today every service holds the one `JWT_SECRET`, so any of about eight services could mint a token for any system. Move to keys only welinc-auth can sign with, published so services verify without a secret, plus a way for services to call each other (BMS's internal key, analytics checking callers).
**Done when:** only welinc-auth can sign tokens, every service verifies with the published keys, a key can be rotated without downtime, service to service calls carry their own identity, and no service needs `JWT_SECRET`.
- Note (2026-11-08): spec 0002 decided `jose` everywhere, ES256 keys in `AUTH_SIGNING_KEYS` with a rotation script that refuses unsafe steps, a seeded `OAuthClient` registry, the client credentials grant with a `jti` replay table, an interim login token whose `aud` welinc-auth picks until S4, and a copyable token check in backend-vrms (`src/auth/verify/`). Hard switch: auth, backend-vrms, portal and compose merge together.
- [x] Design it (spec): `/architect signing keys and service identity`
- [ ] Build it: `/develop signing keys and service identity`
  - [x] ES256 end to end, the hard switch (keys loader, login `aud`, JWKS and metadata, both guards, portal redirect, compose and env) · AC-1 to AC-12, AC-22, AC-23, AC-25
  - [ ] Clients and service identity (registry migration and seed, `/auth/token`, replay, rate limit, `/auth/users` for service tokens, VRMS roster on its own token) · AC-13 to AC-22, AC-27
  - [ ] Rotation and handover (`keys:rotate`, `keys:client`, the rotation test, the folder README, `docs/keys.md`) · AC-24 to AC-26
- [ ] Verify it: `/check verify signing keys and service identity`
- [ ] Test it: `/test signing keys and service identity`
- [ ] Review it (fresh model): `/check review signing keys and service identity`
- [ ] Document it: `/document signing keys and service identity`

### S3. Sessions: refresh and logout, web and mobile · planned · needs a decision
Short lived access tokens with refresh and logout in welinc-auth, for web and for the mobile app, so VMMS can drop its own copy. Covers web vs mobile bound sessions, the way VMMS has them today.
**Done when:** web and mobile sessions refresh without a new login, refresh tokens rotate and a reused one ends the session, logout ends it on the server, an admin can end all of a user's sessions, and VRMS, VMMS web and the mobile app all use it.
- [ ] Design it (spec): `/architect sessions refresh and logout`

### S5. Roles per system · planned · needs a decision
Each system declares its roles and rules (VMMS: exactly one role per account; BMS: Admin, Customer Support, Operations; VRMS: Admin, Chief Mechanic, Mechanic), and welinc-auth enforces them, instead of one shared enum and rules copied into each system.
**Done when:** each system's allowed roles and rules live in one place in welinc-auth, user admin rejects a role a system does not have, and adding a role to one system needs no change in the others.
- Note (2026-11-08, from a look at a friend's company suite (SBSI User & Access Management) on 2026-11-08, ideas to weigh in the spec, nothing decided): let each system publish its own permission catalog (VRMS already has its matrix and `/permissions/me`, spec 0011) and show them read only through `/auth/systems`, named `system.resource.action` (VRMS keys get a `vrms.` prefix there, e.g. `vrms.ticket.view_all`). Each system still decides and enforces its permissions; welinc-auth only shows them, so the S10 access report can answer "who can approve costs anywhere in the suite". Don't copy their model of one central catalog where the access service owns every permission (it drifts: empty systems, undescribed permissions, old and new slugs mixed), nor global roles shared across systems.
- [ ] Design it (spec): `/architect roles per system`

### S6. User directory for systems · planned · needs a decision
Systems need names, emails and roles for people their records point to (VMMS schedules, BMS activity, VRMS mechanics) without their own users table or reading the auth database. Give them a lookup API and a change feed, generalizing VRMS's mechanic sync.
**Done when:** a system can look up many users by id in one call, learns about created, changed and deactivated users without polling every user, keeps only a local copy of what it needs, and no system reads the auth database.
- [ ] Design it (spec): `/architect user directory for systems`

### S12. Suite seed accounts · planned · needs a decision · Beta
One seed in welinc-auth for all three systems instead of three drifting copies: fixed ids every system links its own rows to (as VRMS already does with `SEED_IDS`), one person per email, and people chosen to test the shared login.
**Done when:** each system's roles have at least one seed person; there are accounts holding one, two and three systems for the launcher; a locked, a deactivated and a never verified account exist for testing; the platform admin from S10 has a seed account once S10 is built; no email means two different people across systems; and each system's own seed links to the shared ids instead of creating users.
- Note (2026-11-07): fixes the drift listed above (`ops.user` and the VMMS chief mechanics). Keep `@welinc.com` addresses, since welinc-auth checks the email domain on account creation.
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
- [ ] Design it (spec): `/architect profile extras`

## Cutover

### S11. Move VMMS and BMS onto the shared services · planned · needs a decision
The move itself: their users merged into welinc-auth by email, their auth copies and direct database reads removed, their apps on the portal login. Their groups change their own repos; this row gives them the migration guide, a user import script and a test plan, and tracks it to the end.
**Done when:** every VMMS and BMS account logs in through welinc-auth with no duplicates, neither system has its own users or tokens tables or reads the auth database, all three systems run together behind one login on staging, and each group signs off.
- Note (2026-11-07): the old `welinc-backend` repo where BMS pushed an auth copy is part of this cleanup.
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
