# Runbook

How to set up, run and recover the hosted WeLinc suite. Hosting spec 0008 (task 21) fills in the rest of this file: bootstrap, DNS and Brevo records, rollback, stopping staging, rotating keys and secrets, moving subscriptions, the freeze rule and the shutdown copy. Each section names the spec it comes from.

## Staging and production share one Container Apps environment (VRMS spec 0008, AC-23)

The trial subscription allows one Container Apps environment, so production's apps run in staging's `cae-welinc-staging`. Every app and job name ends in `-staging` or `-prod`; the details are in [infra/README.md](README.md#shared-environment-spec-0008-ac-23).

- **Never delete** `rg-welinc-staging` or `cae-welinc-staging` while production runs. Delete locks on the environment, `cert-api-prod` and `auth-uploads-prod` back this up.
- **Stopping staging** means scaling staging's apps to zero and stopping `psql-welinc-staging`, nothing else (the full command comes with task 21).
- **Deleting one of staging's certificates or storages** needs the environment's lock lifted first, then `apply.sh prod` to put it back (the README shows the command).

## Error monitoring: the Sentry org (VRMS spec 0025)

Set up by hand once, on 2026-11-17. Everything below lives in Sentry, not in this repo, so this is the record of how it was set.

### The org

- **Org:** `welinc` (https://welinc.sentry.io), region **United States**. The region can't be changed later; a new region means a new org and new DSNs everywhere.
- **Plan:** the GitHub Student Pack offer (50k errors a month for a year) if the claim went through, else the free Developer plan (5k errors, 1 seat, 1 cron monitor, 1 uptime monitor). The setup fits the free plan either way. Check under Settings → Subscription.
- **Owner:** Samuel. Groupmates join as members only once the student plan is active (the free plan has one seat).
- **GitHub:** the Sentry GitHub app is installed on `Capstone-WeLinc` with access to only `welinc-backend-vrms`, `welinc-web-vrms`, `welinc-auth` and `welinc-web-portal` (Settings → Integrations → GitHub). It gives suspect commits and links from stack frames to code.
- Save the login in 1Password.

### The four projects

| Project | App | Platform |
|---|---|---|
| `vrms-backend` | welinc-backend-vrms | NestJS |
| `vrms-web` | welinc-web-vrms | React |
| `welinc-auth` | welinc-auth | NestJS |
| `welinc-portal` | welinc-web-portal | React |

Staging and production share each project and are told apart by `environment`. To add one: Projects → Create Project, pick the platform, name it as above, and skip Sentry's install steps and its agent prompt (the SDKs are already set up in the code; the wizard would overwrite the privacy settings). A renamed project keeps its DSN.

Each project's DSN is under Project Settings → Client Keys (DSN). A DSN can only send events, so it isn't a secret, but keep a copy in 1Password with the others. Where each DSN goes is in spec 0025's value sourcing table.

### Privacy settings (org wide)

Settings → Security & Privacy (https://welinc.sentry.io/settings/security-and-privacy/), section **Data Scrubbing**. At the org level these switches read "Require…", and on means every project gets them.

- **Require Data Scrubber:** on
- **Require Using Default Scrubbers:** on
- **Prevent Storing of IP Addresses:** on
- **Global Sensitive Fields**, one per line:

```
code
otp
setupCode
reauthToken
refreshToken
accessToken
password
email
name
phone
city
region
```

`city` and `region` were added during the first live test, beyond spec 0025's list. Sentry works out a location from the address a report came from even with IP storage off, and it does so before the scrubbers run. These two lines (with `code`, which already catches `countryCode`) blank that location. The list also blanks harmless fields with the same names, such as a stack local called `name`; that is accepted.

Check after any change: send a test error (below) and open it. The user should show only an id, and `geo` should read `[Filtered]` throughout.

### Alert rules

One alert covers all four projects: **New or regressed issue (spec 0025)** (https://welinc.sentry.io/monitors/alerts/6357875/). It fires on a new issue and on a regression (a resolved issue comes back), in every environment, and emails the issue owners, falling back to the active members (you). The email names the environment.

Sentry also makes a "Send a notification for high priority issues" rule for each new project. Those are disabled so one problem sends one email. A project added later gets one too: disable it, and add the project to the alert above (Alerts → the alert → Edit → Connected projects).

The cron monitor (`vrms-directory-poll`) and the uptime monitor (`/vrms/health`) alert for **production only**. They come with spec 0025's milestones 3 and 4.

### Sending a test error

- **backend-vrms** (staging, or locally with `SENTRY_TEST_ROUTES=true`): `POST /vrms/debug/sentry-test` as a user with `settings.manage` answers 500 and creates one issue. Sentry drops an error identical to the last one from the same process, so a second identical call sends nothing until the app restarts.
- **web-vrms** (a build with `VITE_SENTRY_TEST_ROUTES=true`): open `/debug/sentry` as a user with `settings.manage` and press Crash this page. The crash screen's reference code matches the start of the event id.
