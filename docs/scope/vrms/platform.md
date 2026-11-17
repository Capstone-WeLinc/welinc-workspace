# Platform

Release, cross group integration, login security and the mechanic mobile app (Jira WL-E9, WL-E1, WL-E8). Back to [index](index.md).

## Release

Set up right after Slice 1 so every later slice demos from staging.

### 26. Hosting, CI/CD & environments · in-progress
- Note (2026-11-14, `/architect`, after the Slice 3 build): spec 0008 amended, cross checked on another model. `azure.extensions` adds `PG_TRGM`; the VRMS seed job runs as `vrms_owner`; Bicep builds every `DATABASE_URL` from the role passwords; all DDL comes from migrations, so every app (VMMS analytics included) uses its app role. VMMS and BMS can't deploy yet: their gaps are in the spec's `rationale.md` (*VMMS and BMS readiness*), to send them for task 18.
- Note (2026-11-14, `/architect`): spec 0008 updated for the whole suite and the defense dates (mock Nov 28, integration Dec 4, final Dec 5): production live by Nov 26, a freeze Nov 28 to Dec 5. Decided: VMMS and BMS in the same subscription with a template they copy and their own scoped logins, production fully warm and staging warm only for the gateway and timed apps, one PostgreSQL server per environment, `welinc.tech`, Brevo, Gemini free tier per environment, a $200 free account signed up the day staging is applied, and a shutdown copy after Dec 5 before the credit ends. Every replan note below is folded into the spec (the permission history export no longer applies: hosted databases start empty). Cross checked on another model, 25 fixes applied.
- Note (2026-11-16, `/architect`): superseded dates. Staging Nov 17, production live Nov 20, and the freeze is no longer Nov 28 to Dec 5: its dates are not set yet (likely December, Samuel decides). Production deploys from `main` by a one click promotion, and every deploy runs CI first (spec 0008 AC-4, AC-22).
- Note (2026-11-11, replan): back off hold. You first chose to build it right after S13 (superseded by the next note: it now runs after S7, S8, S10 and the S11 guide). Staging still unblocks S11. First run `/architect hosting & CI/CD` to update spec 0008 with what suite spec 0008 (S9) decided: the gateway image built from `infra/gateway/`, `/auth/health` and `/vrms/health` (already built, so milestone 2 shrinks), and the shared services hosted beside VRMS.
- Note (2026-11-11, replan, your call): hosting runs after S7, S8 and S10 and the S11 migration guide (see the order in the shared services epic). It stays the hard deadline: deployed by the end of November.
- Note (2026-11-11, replan, from suite spec 0010): pass `VITE_*` as build arguments in the deploy (plain `npm run build` now refuses missing or `localhost` values); set every required backend variable per environment, including `NODE_ENV=production`, `TRUST_PROXY_HOPS` of at least 1, `SSO_COOKIE_SECURE=true` (auth) and `SESSION_COOKIE_SECURE=true` (backend-vrms), SMTP and storage; run `npm run env:check` before `prisma migrate deploy` in the migration job.
- Note (2026-11-11, replan, from suite spec 0009): working mail on staging is now a hard need, not a nicety: an unverified account can't sign in until it types the emailed code, so a mail outage locks new people out. Set up the mail provider and `SMTP_*` (the Brevo note below) before any real user is added, and check it in the smoke test.
- Note (2026-11-09, replan, from suite spec 0005): set `idle_in_transaction_session_timeout` on the hosted auth database too. A transaction left open on the Postgres server holds back the directory feed for every system.
- Note (2026-11-09, replan, from suite spec 0006): decide whether staging seed passwords differ from the public ones in `docs/integration/seed-accounts.md`, and set `SEED_ALLOW=staging` only on staging (the seed refuses production otherwise).
- Note (2026-11-12, replan, from suite spec 0011): run `geo:fetch` in the welinc-auth image build and rebuild monthly (the DB-IP Lite files go stale), and credit DB-IP in the hosted docs. Without the files the app still works; places just show empty.
- Note (2026-11-13, replan, from suite spec 0013): on staging, run the permission history export against the staging VRMS database **before** the migration that drops VRMS `permission_changes` deploys, then the import into welinc-auth (the order in AC-28). Every admin portal sign in now emails a code, so `ADMIN_SIGN_IN_CODE` stays on and real mail must work before any admin signs in. The 17 unproven S10 verify steps (top of its `verify.md`) are worth a manual pass on staging.
- Note (2026-11-02, replan): from spec 0017. When the SPA host gets a Content Security Policy, `img-src` must allow the storage account host. Auth's profile pictures still sit on an Azure Files mount; moving them onto the blob store is a separate decision in welinc-auth (a shared repo), so raise it at the integration meeting (feature 55) rather than building it here.
WL-902 and WL-903. Staging and production with their own settings and databases, an automatic pipeline, and the go live. Decided in spec 0008: Azure (Static Web Apps, Container Apps, one shared PostgreSQL server) on free credit, GitHub Actions for CI and CD. This replaces the earlier Vercel and Render plan (Jira not yet updated).
**Done when:** pushing to `development` deploys to staging, production deploys only from a manual run on `main` (a fast forward from `development`), every deploy runs CI first, builds fail when tests fail, production has HTTPS and scheduled database backups, and a smoke test passes after deploy.
spec [0008](../../specs/vrms/0008-hosting-and-ci-cd/index.md) · code in `infra/` of the workspace repo, plus `.github/workflows/` in each repo
- [x] Design it (spec): `/architect hosting & CI/CD`
- [ ] Build it: `/develop hosting & CI/CD`
  - [x] CI on every pull request: `lint:ci` scripts and `ci.yml` in all five repos, can start now with no Azure (AC-1, AC-2, AC-11) (2026-10-26: PRs open, web-vrms #16, web-portal #4, backend-vrms #11, auth #5, analytics-ai #4; the first real GitHub run passed in all five. Milestones 2 to 5 are on hold: the team is not deploying yet)
  - [x] Make the apps deployable, no Azure needed (by Nov 18): Dockerfile.prod fixes and the full source `seed` image, `DB_POOL_MAX`, the VRMS seed guard and `--reference`, `admin:recover --create` (suite spec 0013 AC-12b), `staticwebapp.config.json` (AC-5, AC-6, AC-13, AC-15, AC-16, AC-21) (2026-11-14: built on `feat/hosting-deployable` in auth, backend-vrms, web-vrms and web-portal, including the two cross check fixes; 2026-11-16: merged into `development`, auth #38, portal #29, backend-vrms #59, web-vrms #64)
  - [ ] Setup as code, domain and mail (Bicep written Nov 14, staging applied Nov 17): Bicep for the whole suite, budget, `apply.sh` and the other scripts, `init.sql`, `welinc.app` and Brevo records, signup, both apply passes, six OIDC logins, `main` brought up to `development` (AC-5 to AC-8, AC-10 to AC-12, AC-14, AC-16, AC-17, AC-19, AC-21) (2026-11-14: Bicep, scripts and `init.sql` written in `infra/` (tasks 9 to 11); `init.sql` and the role split proven on local PostgreSQL 16 with a non superuser admin. Left: the domain and Brevo (task 12), signup and both apply passes (task 13). 2026-11-16: merged with workspace #33, which also adds the workspace CI (Bicep build, shellcheck, gateway checks); the target moved to staging by Nov 17 and production live by Nov 20. 2026-11-16 later: the Brevo SMTP login is in both parameter files (workspace #37); left for task 12 are the two keys in `infra/private/`, `welinc.app` (bought Nov 17, then the rename from `welinc.tech`) and its Brevo DNS records)
  - [ ] CD to staging, the thin thread (Nov 18): `deploy.yml` in four repos plus the gateway, revision wait, first staging deploy, seed jobs, the domain, mail, address, file, timer and rotation checks (AC-3, AC-4, AC-6, AC-7, AC-9, AC-10, AC-13, AC-14, AC-16 to AC-18, AC-21)
    - Note (2026-11-17, /develop): spec 0008 tasks 14 to 16 written on `feat/deploy-workflows` in all five repos (`deploy.yml` in four, `deploy-gateway.yml` in the workspace), checked offline only. Left: task 17, the first staging deploy, once Azure exists. Before the first production run, `main` must be brought up to `development` once per service repo (the one time step AC-10 lists): a manual run uses the workflow file on `main`, which has no `deploy.yml` yet.
  - [ ] VMMS and BMS on staging (Nov 19): `docs/integration/hosting.md`, workflow templates, their logins, secrets and client keys, suite spec 0014 AC-32 (AC-3, AC-4, AC-9, AC-11, AC-19) (2026-11-14: `docs/integration/hosting.md` written with the hosting ready checklist, linked from both move checklists; the two workflow templates and their repo variables come after our own `deploy.yml` works)
  - [ ] Production and safety (live Nov 20; drill and runbook by Nov 26): prod applied and bootstrapped, first deploy from `main`, restore drill, runbook; the shutdown copy after Dec 5 (AC-4, AC-5, AC-7, AC-8, AC-10, AC-12, AC-15, AC-16, AC-20)
- [ ] Verify it: `/check verify hosting & CI/CD`
- [ ] Test it: `/test hosting & CI/CD`
- [ ] Extra skills (optional, ask first): `docker-patterns` · `azure-container-apps` · `azure-container-registry` · `azure-static-web-apps` · `azure-deployment-preflight`
- Note (2026-10-29): email moves off the personal Gmail to Brevo (subject to change) before staging, with a sender address you control; only the `SMTP_*` values change. See feature 28.
- Note (2026-10-29): safe to build before the integration meeting, but feature 56 (integration contract) may change it: the Azure milestones host the shared gateway, auth and database, so the other groups' services must fit the same setup.
- Note (2026-10-31): from spec 0013. The Bicep must set the flexible server configuration `azure.extensions` to include `VECTOR` before the migration job runs, because the VRMS database now stores AI embeddings with pgvector. Before go live, move `GEMINI_API_KEY` to a paid tier (the free tier caps at 500 and 1K requests a day).
- Note (2026-11-03, replan): from spec 0019. Once every deployed web build uses `PUT /repairs/:id/assignments`, remove the old `POST` alias in backend-vrms.
- Note (2026-11-04, replan): from spec 0021. `audit_logs` is now append only through a trigger, but the app's database user is still the table owner and could drop it. In the database roles milestone, run migrations as the owner role and connect the app as a role with `GRANT SELECT, INSERT ON audit_logs` and no `UPDATE`, `DELETE` or `TRUNCATE`.
- Note (2026-11-08, replan): from suite specs 0001 and 0002, spec 0008 is now out of date. Before the Azure milestones, update it through `/architect`: register the custom domain (working name `welinc.tech`, note the renewal date) and put it on every Static Web App and the gateway Container App; gateway config from `infra/gateway/`; the new routes and ports; replace the `JWT_SECRET` row and the "rotating the JWT secret" step with `AUTH_SIGNING_KEYS`, `CLIENT_VRMS_JWKS`, `AUTH_CLIENT_PRIVATE_KEY` and a link to `docs/keys.md`. The staging key rotation check (spec 0002 AC-24 and AC-26) runs once staging exists.
- Note (2026-11-03, replan): the gateway change from spec 0017 (26 MB uploads and a 120 second read timeout on the VRMS routes, commit `1803092`) was pushed straight to welinc-auth `development` on 2026-11-03. Add it to the feature 55 list of changes you made to the shared repos.

### 27. Error monitoring · in-progress
Catch errors in production before users report them.
**Done when:** frontend and backend errors from staging and production reach one place with the release and user role attached, and no secrets or personal data are sent.
spec [0025](../../specs/vrms/0025-error-monitoring/index.md) · code in `welinc-backend-vrms`, `welinc-web-vrms`, `welinc-auth`, `welinc-web-portal`, `infra/gateway/`, `infra/`
- Note (2026-11-16, `/architect`): Sentry in your four apps (student offer, free plan fallback, US region), browser reports through two gateway tunnel routes, one cron monitor (directory poll) and one uptime check (`/vrms/health`), Azure metric alerts in Bicep, a crash screen with a reference code, staging only test routes. Milestones 3 and 4 wait for feature 26's `deploy.yml`. Cross checked on another model, 17 gaps closed.
- Note (2026-11-17, replan, from spec 0026 follow up): when milestone 1 adds the staging only test routes, hide them from the API docs in the same change (spec 0026 AC-7), then regenerate `docs/openapi.json`.
- [x] Design it (spec): `/architect error monitoring`
- [ ] Build it: `/develop error monitoring`
  - [x] Thin thread in VRMS: the Sentry org and projects, backend-vrms and web-vrms SDKs, scrubbing, crash screen, test route and page, proven from your laptop (AC-1 to AC-3, AC-6 to AC-9, AC-12, AC-14 to AC-16)
  - [x] The shared side: welinc-auth (with `CodeErrorFilter`), the portal, the gateway tunnel and CORS headers, contract 0001 (AC-1 to AC-9, AC-14 to AC-16). Tunnel envelope DSN check (task 7a) proven live 2026-11-17: the right DSN arrived, both cross project envelopes got 403 `TUNNEL_REJECTED`
  - [ ] Jobs and releases: job failure reports, the directory poll monitor, release tags, source map upload and removal in `deploy.yml` (AC-1, AC-3, AC-10, AC-17)
  - [ ] Alerts and hand off: Bicep settings and Azure alert rules, the uptime and cron alerts, the VMMS and BMS how to page (AC-10 to AC-14, AC-18)
- [ ] Verify it: `/check verify error monitoring`
- [ ] Test it: `/test error monitoring` (Testmail is not needed here; it is for the email code flows)

### 68. API docs · done
Interactive API docs generated from the NestJS controllers (`@nestjs/swagger`), so VMMS and BMS can read the auth API without the code, and the panel can see the API. Added 2026-11-16, after hosting and before the integration defense (Dec 4).
**Done when:** backend-vrms and welinc-auth each serve generated docs listing every route with its inputs, outputs and errors, kept in step with the code by the build, and production exposes them only as decided in the spec.
spec [0026](../../specs/vrms/0026-api-docs/index.md) · code in `welinc-auth/src/openapi/`, `welinc-backend-vrms/src/openapi/`, `docs/openapi.json` in both, `scripts/check-contract-routes.mjs`, `infra/env.bicep`, contract 0001 section 16
- Note (2026-11-16, `/architect`): Scalar at `/auth/docs` and `/vrms/docs`, served by each app (no CDN), on locally and on staging, never in production (Bicep sets `API_DOCS_ENABLED` from `prod`). Response classes and reply tests only for the contract routes and four ticket routes. A committed `openapi.json` checked in CI, and a contract route index checked by the workspace CI with a read only `AUTH_REPO_READ_TOKEN` you make. Cross checked on another model, 11 gaps closed.
- [x] Design it (spec): `/architect API docs`
- [x] Build it: `/develop API docs`
  - [x] Thin thread on welinc-auth: packages, plugin, `API_DOCS_ENABLED`, Scalar mount, `openapi` scripts, the first `docs/openapi.json`, CI check (AC-1 to AC-3, AC-7, AC-9, AC-12)
  - [x] welinc-auth thickened: tags, the five security schemes, error codes on contract routes, response classes and reply tests for the 12 integration routes (AC-4 to AC-8)
  - [x] Contract and workspace, after the auth PR merges: contract 0001 section 16, `check-contract-routes.mjs` and its CI job, the Bicep switch, links in `docs/integration/` (AC-1, AC-2, AC-10, AC-11)
  - [x] backend-vrms: the same setup copied, tags, schemes, generic errors, the four ticket response classes and tests (AC-1 to AC-9, AC-12)
- [x] Verify it: `/check verify API docs`
- [x] Test it: `/test API docs`

### 69. Security checks · planned
Free checks that catch leaks and weaknesses, with reports to cite in the papers. Added 2026-11-16. No spec needed: the tools and their place are settled.
**Done when:** every repo's CI fails a pull request that contains a secret (gitleaks), an OWASP ZAP baseline scan runs against staging weekly and on demand with its report kept, and production's Mozilla Observatory and SSL Labs grades are recorded in the runbook.
- [ ] Build it: `/develop security checks` (gitleaks any time; ZAP after staging exists)
- [ ] Verify it: `/check verify security checks`
- [ ] Test it: `/test security checks`

## Integration

The VMMS and BMS groups went separate ways after Capstone 1. The integration meeting is planned for after the first week of November 2026; these two features prepare it and then settle what the three systems share.

### 55. Integration kickoff prep · done
Get ready for the first integration meeting: know what the other groups changed, what you need to ask them, and how the shared setup works now.
**Done when:** a question list covers their repos, mobile app repo, services, auth, environments and CI; every change they made to the shared repos (welinc-auth, welinc-web-portal) is listed from a read only check; and a setup guide for the shared stack (auth, portal, gateway, docker network, CI, environments, dependency updates) is ready to hand over.
- [x] Question list for VMMS and BMS (2026-11-03: 32 questions, kept in `docs/_private/vrms/` outside git)
- [x] Shared repo drift check (read only) (2026-11-03: flipped to what you changed, [shared-repo-changes.md](../../context/shared-repo-changes.md))
- [x] Setup guide for the shared stack (2026-11-03; merged into the workspace [README](../../../README.md) on 2026-11-10)
- [x] Meeting held, answers recorded for feature 56 (skipped 2026-11-10: replaced by direct talks with each group; the answers are in the notes on the [shared services](../_root/shared-services.md) rows)
- Note (2026-10-29): add to the question list that `CHIEF_MECHANIC` now exists in the shared auth role list (spec 0007), and that the VMMS and BMS backends likely carry the same copied login module and `users` table that spec 0009 removed here.
- Note (2026-10-30): also ask which roles BMS has now (operations, customer service?), and tell them about feature 60 (the portal picker changes where their shared users land). Today admin is one separate grant per system; if the groups want a single suite wide superadmin instead, decide it in feature 56 (your Capstone 1 panel called one insecure).
- Note (2026-10-31): from spec 0013. Tell the other groups that VRMS removed `/ai` and `/analytics` from `welinc-auth/nginx.conf` (merged in welinc-auth PR 14, when feature 3 retired the Python service).
- Note (2026-11-03): the other groups work in their own repos, so the `welinc-web-vmms`, `welinc-backend-vmms`, `welinc-web-bms` and `welinc-backend-bms` clones here are stale and say nothing about their current systems. You asked them not to connect to the shared repos (or their `development` branch) or use the workspace repo until you tell them, so nobody else has changed welinc-auth or welinc-web-portal (a fetch on 2026-11-03 showed only your commits and dependabot). The drift check therefore flips: list what **you** changed in the shared repos since Capstone 1, so they know what to expect. Agreed vocabulary for all three papers: microservices **between** systems (each system its own containers, database and deployment, talking over APIs), and each system a modular monolith inside; auth, portal and gateway are the shared services. The meeting (after the first week of November) is about real integration on the shared services.
- Note (2026-11-03): the VMMS mobile app lives in another GitHub org for now and moves into the Capstone-WeLinc org once it is polished and tested (Eliab is testing). Still missing on their side: polish, testing, and forgot password for mechanics and chief mechanics. Ask them to build that forgot password on welinc-auth rather than their own. VRMS joins their app as a tab (feature 48); you don't need it yet. Their web app has two read only modules left with no integration needs, planned for next week.

### 60. Portal system picker for shared accounts · dropped · replaced by suite S4
People with roles in more than one system (for example a mechanic in both VRMS and VMMS) can't reach anything but VRMS today, because the shared portal always sends them there. Send single system users straight in, and let shared accounts choose.
**Done when:** someone with roles in one system lands in it with no extra screen; someone with roles in several sees a picker listing only their systems; each app's shell has a "Switch system" link back to the portal; no new role or permission is created (each system still checks its own roles on the server); and the change is agreed with the VMMS and BMS groups.
- Note (2026-10-30): you chose to build this before the integration meeting, VRMS side first, but feature 56 (integration contract) may change it: the portal and token handoff are shared, so the picker also changes the landing for VMMS and BMS users who hold several systems. Changing the redirect or handoff needs a spec first (welinc-web-portal `AGENTS.md`).
- Note (2026-11-07, replan): moved to the suite epic and reshaped as [S4. App initiated login and launcher](../_root/shared-services.md#s4-app-initiated-login-and-launcher--done): the app sends people to the portal and gets them back by a one time code, and the portal shows a launcher only when opened directly. Kept here for history.
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (one, two and three systems, long names)

### 56. Cross group integration contract · planned · needs a decision · GA
One spec for everything VRMS shares with VMMS and BMS, written after the meeting: roles in the shared auth, gateway routes, vehicle status, the notification service, the one mobile app, who owns the copied Booking and maintenance models, and the environment, CI and dependency update standards.
**Done when:** the spec records each shared contract, all three systems run together on staging behind one login, and every scope note that says feature 56 may change it is resolved.
- Note (2026-10-29): spec 0010 dropped the copied `Booking`, `MaintenanceSchedule`, `ChecklistTemplate` and `ChecklistItem` models from VRMS. Bring them back only if the meeting decides VRMS owns them. Vehicle status now also has `DISABLED`, which VMMS shares.
- Note (2026-11-01, replan): from spec 0016. Decide who owns vehicle type once VMMS shares vehicle records.
- Note (2026-11-03, replan): from spec 0020. Agree with VMMS who writes `UNDER_MAINTENANCE` (read only in VRMS today) and whether a VMMS status change writes `VehicleChange` rows through a VRMS API.
- Note (2026-11-07, replan): the auth, roles, login handoff, gateway routes, ports and environment parts move to the suite epic ([S1. Shared services contract](../_root/shared-services.md#s1-shared-services-contract--done) and its rows). This feature keeps the domain contracts: vehicle status and who writes it, `VehicleChange` from VMMS, vehicle type ownership, the notification service, the one mobile app, and the copied Booking and maintenance models. Design it after S1 (done, spec 0001) and the integration meeting (feature 55).
- Note (2026-11-10, replan): no integration meeting after all (feature 55 closed). Start this from the answers in the shared services notes, and settle anything still open directly with each group.
- [ ] Design it (spec): `/architect cross group integration`

### 61. Suite admin model · dropped · replaced by suite S10
A safe way to have "someone who can do everything" across VRMS, VMMS and BMS, the way industry does it, instead of one superadmin role that skips every check (which your Capstone 1 panel called insecure).
**Done when:** a platform admin in the shared auth can manage accounts and give or remove each system's roles but can't see any system's data without that system's own role; one or two break glass emergency accounts exist that need MFA, log a reason, and alert every admin on each login; an admin access report shows who holds admin in which system and since when; every admin role given or removed raises an alert and a log entry; nobody can raise their own access; and the VMMS and BMS groups agree.
- Note (2026-10-30): you chose these three pieces. Temporary elevation (time limited extra rights with a reason) was left out as future work, and a single everyday `SUPERADMIN` role that bypasses checks is out on purpose. It builds on what exists: spec 0009's change record, spec 0011's system scoping in welinc-auth, and feature 34's OTP for the MFA step. It lives in the shared welinc-auth and portal, so it follows feature 56; the picker (feature 60) shows a suite admin every system they hold.
- Note (2026-11-07, replan): moved unchanged (the full model) to the suite epic as [S10. Suite admin model](../_root/shared-services.md#s10-suite-admin-model--done--ga). Kept here for history.

## Slice 3: Login hardening

### 34. Admin OTP · dropped · replaced by suite S10
WL-102. Admins confirm login with the same OTP mechanics use.
- Note (2026-11-12): covered by suite [S10](../_root/shared-services.md#s10-suite-admin-model--done--ga), spec [0013](../../specs/_root/0013-suite-admin-model/index.md) AC-5 to AC-8: every admin (suite and system) confirms each portal sign in with spec 0009's emailed code, and admin routes refuse a session that didn't. Spec 0009's code rules (10 minutes, 5 wrong tries retire the code, never an account lock) replace this row's 5 minutes and 15 minute lock. Kept here for history.
**Done when:** Admin pages are unreachable without a completed OTP step (checked on the server), codes expire after 5 minutes and work once, 5 wrong tries lock for 15 minutes, resend waits 60 seconds, and every OTP event is logged.
- Note (2026-10-29): safe to build before the integration meeting, but feature 56 (integration contract) may change it: OTP lives in the shared welinc-auth and portal, which the other groups also use.
- Note (2026-11-10, from suite spec 0009): reuse its sign in ticket and step (`verification_codes` with a new purpose) instead of a new mechanism. Its rules (codes dead after 5 wrong tries, never an account lock, 10 minute lifetime) differ from this row's Done when (5 minutes, a 15 minute lock); settle that in this row's spec.
- [ ] Build it: `/develop admin OTP`
- [ ] Polish it (optional, ask first): `web-design-guidelines`

### 35. reCAPTCHA on login · planned · needs a decision · GA
WL-103. Block bots from guessing passwords.
**Done when:** the token is verified on the server before the password check, failures show a clear message, keys live only in environment variables per environment, and it works on a phone.
- Note (2026-10-29): safe to build before the integration meeting, but feature 56 (integration contract) may change it: the login page is the shared portal.
- [ ] Design it (spec): `/architect reCAPTCHA on login`
- [ ] Polish it (optional, ask first): `web-design-guidelines`

## Slice 7: Mechanic mobile app

After the web core loop. The responsive web stays the mechanic app until this ships.

### 48. Mechanic mobile app (shared with VMMS) · planned · needs a decision
WL-802. The mechanic side as a native app on the same API. Epic sized: split into smaller features once its spec exists.
**Done when:** a mechanic can log in with OTP, see their tickets, update status, upload photos and proof with the camera, get notifications and see history, from an installable build.
- Note (2026-10-29): VMMS already has a mobile app for the same garage mechanics. Before the spec, ask the VMMS group whether VRMS repairs can live as a module in their app (one app for mechanics) or whether VRMS ships its own app that matches theirs (same welinc-auth login, same look). Their app's platform should inform this decision, so the "(React Native)" in the title is not settled yet. Either path crosses repos, so it needs a spec first.
- Note (2026-10-29): decided, one mobile app shared with VMMS, not a separate VRMS app. VRMS adds its mechanic repair screens to it. Which app shell, repo and platform it uses is settled in feature 56 after the meeting.
- [ ] Design it (spec): `/architect mechanic mobile app`
- [ ] Polish it (optional, ask first): `impeccable` or `emil-design-eng` (one taste skill per change; motion: screen transitions and sheets) · `web-design-guidelines`

### 49. Offline save & sync · planned · needs a decision
WL-804. Mechanics keep working with no signal; changes sync when back online.
**Done when:** assigned tickets open offline, status changes, notes and photos queue locally with a pending count, sync is automatic, the conflict rule is recorded, and closing the app loses nothing.
- Note (2026-10-29): safe to build before the integration meeting, but feature 56 (integration contract) may change it: offline behavior lives in the shared mobile app, so its rules must work for VMMS too.
- Note (2026-11-03, replan): from spec 0018. Queued photo uploads must keep `takenAt`, read from the original file before it is queued.
- [ ] Design it (spec): `/architect offline save & sync`
- [ ] Polish it (optional, ask first): `web-design-guidelines`
