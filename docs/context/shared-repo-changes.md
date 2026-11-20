# Changes in the shared repos (Capstone 2)

A record of what changed in `welinc-auth`, `welinc-web-portal` and the gateway during Capstone 2, and what is proposed next. Background only: to move a system onto the shared services, follow its checklist in [docs/integration/](../integration/README.md) instead. Last checked 2026-11-19. This term's changes were made by the VRMS group, apart from Dependabot updates.

Everything below is on `development`, the branch every system builds against and staging deploys from. Only staging is hosted; nobody works on `main`.

## Suite rows (the shared services epic)

Each row has a suite spec in `docs/specs/_root/`; the plan is [docs/scope/_root/shared-services.md](../scope/_root/shared-services.md). The rules all of them add up to are the shared services contract, [spec 0001](../specs/_root/0001-shared-services-contract/index.md) (S1).

| Row | What changed | What it means for VMMS and BMS |
|---|---|---|
| S2, keys and service identity ([0002](../specs/_root/0002-signing-keys-service-identity/index.md)) | welinc-auth alone signs ES256 tokens and publishes its keys; services call each other with client keys and service tokens | Drop `JWT_SECRET` and check tokens with the published keys (copy `welinc-backend-vrms/src/auth/verify/`) |
| S3, sessions ([0003](../specs/_root/0003-sessions-refresh-logout/index.md)) | Short access tokens, refresh and logout for web and the phone app, an idle cutoff | Your backend runs the session routes; the phone app signs in at `/auth/mobile/login` |
| S5, roles per system ([0004](../specs/_root/0004-roles-per-system/index.md)) | Each system declares its roles and rules in welinc-auth's catalog, which enforces them | No role rules copied into your code |
| S6, user directory ([0005](../specs/_root/0005-user-directory/index.md)) | A lookup API and a change feed of names, emails and roles | Read people from the directory instead of a `users` table |
| S12, seed accounts ([0006](../specs/_root/0006-suite-seed-accounts/index.md)) | One `people.json` manifest with fixed ids, copied by every system | Your seed copies it byte for byte ([seed-accounts.md](../integration/seed-accounts.md)) |
| S4, login and launcher ([0007](../specs/_root/0007-app-initiated-login-launcher/index.md)) | Apps start the login; one system people go straight in, others pick from a launcher; Switch system | [web-login.md](../integration/web-login.md) |
| S9, suite gateway ([0008](../specs/_root/0008-suite-gateway/index.md)) | The gateway moved to `infra/gateway/`: `/vmms/` and `/bms/` routes, JSON errors, `/health`, a flood limit; `/repairs` removed | Call only the gateway |
| S14, env checked at startup ([0010](../specs/_root/0010-startup-env-validation/index.md)) | Apps refuse to start with missing or malformed settings; `setup.sh` tops up an old `.env` | Every name in `.env.example` |
| S7, account activity ([0011](../specs/_root/0011-account-activity-audit/index.md)) | One log of sign ins, sessions, codes and account changes, with a person route, an admin feed and a label catalog | Your activity screens read it ([account-screens.md](../integration/account-screens.md#activity)) |
| S8, profile extras ([0012](../specs/_root/0012-profile-extras/index.md)) | Password recheck, deletion requests, a 30 day grace period and erasure; phone verification dropped | [account-screens.md, Account deletion](../integration/account-screens.md#account-deletion) |
| S13, email verification ([0009](../specs/_root/0009-email-verification/index.md)) | An emailed code proves a person owns their email at sign in and on every email change | The portal shows the code step; your app does nothing. Seed addresses never get real mail: locally and on staging the code is in the auth log (AC-32) |
| S10, suite admin ([0013](../specs/_root/0013-suite-admin-model/index.md)) | Suite admins, temporary access with a reason, an emailed code at each admin sign in, all account management in `<portal>/admin` | Delete your Users page ([account-screens.md, Admin pages](../integration/account-screens.md#admin-pages-live-in-the-portal)) |
| S11, the move ([0014](../specs/_root/0014-move-vmms-bms-shared-services/index.md)) | Moves done: both groups passed the checker on `development` on 2026-11-20 and the move checklists were removed; next is hosting them on staging | [hosting.md](../integration/hosting.md), [fleet-api.md](../integration/fleet-api.md) |
| S15, authenticator app for admins | Planned, after S11 and hosting | Nothing |

## Earlier changes (before the suite rows)

| Change | What it means for each system |
|---|---|
| **welinc-auth is the only owner of accounts** (VRMS spec 0009) | Login, codes, password reset, users and roles live only in welinc-auth. VRMS deleted its own login module and `users` table. |
| **Repair, booking and maintenance tables dropped from the auth database** (`809e5a3`) | A system that read domain data from the auth database keeps it in its own database. |
| **Admin endpoints scoped by system** (VRMS spec 0011, `3051b75`) | An admin only sees and edits people who hold a role in their own system, and only changes roles in that system. |
| **Shared account rules** (VRMS spec 0011) | A person can hold roles in several systems. An existing person is attached to a new system instead of created again (409 `ACCOUNT_EXISTS`). |
| **Admin safety guards** (VRMS spec 0009, `5f5ed68`) | No admin can deactivate, delete or demote themselves or the last active admin of a system (409). Every admin change is recorded (now the S7 log). |
| **Reset and lockout hardening** (VRMS spec 0009) | Codes never appear in logs. A locked account (5 failed sign ins) stays locked until an admin unlocks it. |
| **New role `CHIEF_MECHANIC`** (`59c2aa0`) | VRMS's role list gained it. |
| **Gateway: `/ai` and `/analytics` removed** (`6e682d7`) | VRMS moved its AI and analytics into its main backend. |
| **Gateway: bigger VRMS uploads** (`1803092`) | `/vrms/` allows 26 MB bodies and a 120 second read timeout; `/vmms/` and `/bms/` allow 10 MB, auth 5 MB. |

## Changes to how the repos work

| Change | What it means |
|---|---|
| **Node 24** | Docker images, `.nvmrc` and `engines` are on Node 24 in both repos. |
| **CI on every pull request** | Lint, build and (auth only) tests on pull requests into `development`. It warns but can't block a merge on GitHub Free. |
| **Branch rule** | Branch from `development` as `feat/<feature>`, open a pull request back into `development`, never into `main`. |
| **Env files** | Each repo has a `.env.example` with every variable name; real values go in a local `.env`. The portal also commits a `.env.development` with safe defaults. |
| **SMS removed** | No system sends SMS; codes go by email and the phone is a plain contact field. |
| **Deploys (VRMS spec 0008)** | A push to `development` deploys that repo to staging by itself; "Run workflow" on `main` is production's and stops at once with "production is not hosted" (AC-24). Every deploy runs CI on that exact commit first. Staging went live on Nov 19 at `staging-api`, `staging-portal`, `staging-vrms`, `staging-vmms` and `staging-bms`.welinc.app and is the only hosted environment; every Azure app and job ends in `-staging`. On staging, seed account mail goes to the team inbox `welinc.demo@gmail.com` (suite spec 0009 AC-33). |
| **Secret scan** | `gitleaks` runs on every pull request and push. Branch protection isn't available on GitHub Free private repos, so the team rule is: never merge on a red `ci` or `gitleaks`. |
| **Email through Brevo** | Auth sends mail through Brevo from `WeLinc <noreply@welinc.app>` when hosted. Locally it still uses whatever `SMTP_*` you set. |
| **AGENTS.md** | Each repo has an `AGENTS.md` describing its files, rules and gotchas. Read it before changing the repo. |
| **Portal on Tailwind v4 and shadcn** (suite spec 0007) | The portal uses Tailwind v4, shadcn and the shared design tokens in the workspace `design.md`. |

## Proposed changes

Not built. Each one changes the shared repos, so it gets a suite spec first (contract 0001, section 14).

| Proposal | Effect on the systems |
|---|---|
| **reCAPTCHA on login** (VRMS scope feature 35) | The portal's login page would check reCAPTCHA. |
