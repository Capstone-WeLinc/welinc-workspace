# Changes in the shared repos (Capstone 2)

A record of what changed in `welinc-auth` and `welinc-web-portal` during Capstone 2, and what is proposed next. Checked against each repo's `development` branch on 2026-11-03. All of this term's changes so far were made by the VRMS group, apart from Dependabot updates.

`main` in both repos is still the Capstone 1 state. Everything below is on `development`, the branch every system builds against.

## Changes that can affect a system

| Change | What it means for each system |
|---|---|
| **welinc-auth is the only owner of accounts** (VRMS spec 0009) | Login, OTP, password reset, users and roles live only in welinc-auth. VRMS deleted its own copy of the login module and its `users` table and now checks every request against welinc-auth. A backend that still carries a copied login module or `users` table from Capstone 1 should do the same. |
| **Repair, booking and maintenance tables dropped from the auth database** (`809e5a3`) | The early auth schema carried domain tables. They are gone. A system that read bookings or maintenance data from the auth database must keep that data in its own database. |
| **Admin endpoints are scoped by system** (VRMS spec 0011, `3051b75`) | An admin only sees and edits users who hold a role in the admin's own system (anyone else gives 404), and may only add, change or remove roles in that system. The user list shows roles for the admin's system plus an `otherSystems` list. |
| **Shared account rules** (VRMS spec 0011) | A person can hold roles in several systems. A shared account can't be deleted, and its password and email can't be set by an admin of one system when it is `ADMIN` in another (403). To give an existing person a role in a system, look them up with `GET /auth/users/lookup?q=` and create with `attachExisting: true`; a plain create with their email answers 409 `ACCOUNT_EXISTS`. |
| **Admin safety guards and change record** (VRMS spec 0009, `5f5ed68`) | No admin can deactivate, delete or demote themselves or the last active admin of a system (409). Every admin change to a user is recorded in a `UserChange` table, readable at `GET /auth/users/:id/changes`. |
| **Reset and lockout hardening** (VRMS spec 0009) | Codes never appear in logs. Reset links use `PORTAL_URL`. A locked account (5 failed logins) stays locked until an admin unlocks it. |
| **New role `CHIEF_MECHANIC`** (`59c2aa0`) | The role list is now `ADMIN`, `MECHANIC`, `CHIEF_MECHANIC`, `CUSTOMER_SUPPORT`, `OPERATIONS`. Code that switches on role names should handle the new one, or ignore it. |
| **Gateway: `/ai` and `/analytics` removed** (`6e682d7`) | VRMS moved its AI and analytics into its main backend, so those two gateway routes no longer exist. |
| **Gateway: bigger uploads on the VRMS routes** (`1803092`) | `/vrms` and `/repairs` allow 26 MB bodies and a 120 second read timeout. Other routes keep the Nginx default of 1 MB unless they set their own limit. |

## Changes to how the repos work

| Change | What it means for each system |
|---|---|
| **Node 24** | Docker images, `.nvmrc` and `engines` are on Node 24 in both repos. |
| **CI on every pull request** | A GitHub Actions workflow runs lint, build and (auth only) tests on pull requests into `development`. It warns but can't block a merge on GitHub Free. |
| **Branch rule** | Branch from `development` as `feat/<feature>`, open a pull request back into `development`, never into `main`. |
| **Env files** | Each repo has a `.env.example` with every variable name. Real values go in a local `.env` (never committed). The portal also commits a `.env.development` with safe defaults. |
| **SMS removed** | The unused Semaphore SMS variables are gone from auth. Codes go by email. |
| **AGENTS.md** | Each repo has an `AGENTS.md` describing its files, rules and gotchas, for people and AI tools. Read it before changing the repo. |
| **Portal** | Lint and build errors fixed, toast and subsystem files split, system names corrected to match the glossary. Behavior is the same as Capstone 1. Earlier Capstone 1 work that also never reached `main` is here too: the session inactivity monitor, the forgot password fix, and the login field fix. |

## Proposed changes

Not built. Each one changes the shared repos, so it needs agreement from every group before it is built. The VRMS scope tracks them; other groups can propose their own the same way.

| Proposal | Effect on the systems |
|---|---|
| **Portal system picker** (VRMS scope feature 60) | Today the portal sends a user with roles in several systems to VRMS first. The picker would send single system users straight in and let shared accounts choose, with a "Switch system" link in each app. |
| **Suite admin model** (VRMS scope feature 61) | A safe "can do everything" setup across systems: a platform admin who manages accounts but can't see any system's data without that system's role, plus break glass accounts with MFA. No single superadmin that skips checks. |
| **Admin OTP and reCAPTCHA** (VRMS scope features 34, 35) | Admins would confirm login with an OTP, and the login page would check reCAPTCHA. Both change the shared login. |
| **Portal on a design system** (VRMS scope feature 50) | The portal would move to Tailwind v4 and shared design tokens, changing the look of the shared login. Which design standard it follows is still open. |
| **Email through Brevo** | Auth sends mail through a personal Gmail account today. Before staging it would move to Brevo with a sender address the team controls. Only the `SMTP_*` values change. |
| **Hosting on Azure** (VRMS spec 0008) | The draft puts the shared gateway, auth, portal and one PostgreSQL server on Azure, with staging deployed from `development` and production from a `release` branch. Every system's services would need to fit the same setup. |
