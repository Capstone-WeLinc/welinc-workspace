# Error monitoring with Sentry (optional)

How VMMS and BMS can report crashes and server errors to Sentry the same way VRMS, auth and the portal do. This is optional. If you skip it, nothing in the suite breaks. If you do it, you find out about a crash before the panel does.

What you get: an email for every new error, with the release (the commit), the environment, the stack trace mapped back to your TypeScript, and the user's id and role. Never a name, email, code or token. A web app also gets a calm crash screen instead of a white page.

The full design is VRMS spec [0025](../specs/vrms/0025-error-monitoring/index.md). This page is the short version of what to copy.

## What it costs

Nothing. Sentry's free Developer plan gives one organization 5,000 errors a month, 1 member, 1 cron monitor and 1 uptime monitor. That's plenty for staging.

## 1. Make your own Sentry organization

We recommend each group makes its **own** free organization at https://sentry.io, not a project inside the VRMS one. Your error quota and your monitors are then yours alone, and nobody waits on an invite.

- **Region:** United States. It can't be changed later.
- **Projects:** one per app you deploy, named after it: `vmms-backend`, `vmms-web`, `vmms-mobile`, or `bms-booking`, `bms-dispatch`, `bms-web` and so on. When Sentry offers its install wizard or its agent prompt, skip it (it would overwrite the privacy settings below).
- **DSN:** each project's DSN is under Project Settings → Client Keys (DSN). A DSN can only *send* events, so it's not a secret, and it's fine in a browser build. Keep a copy with your group's other settings anyway.
- **Alert:** in Alerts, make one rule for all your projects: "a new issue is created" or "an issue changes state from resolved to unresolved", in every environment, emailing your team. Disable the "Send a notification for high priority issues" rule that Sentry makes for each new project, so one problem sends one email.

## 2. Privacy settings (copy these exactly)

The suite promises that no personal data reaches Sentry. Settings → Security & Privacy → **Data Scrubbing**, at the organization level:

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

`city` and `region` are there because Sentry works out a location from the address a report came from, even with IP storage off. Add any field name of your own that holds personal data (a plate owner, a customer phone).

Your code must not rely on these settings alone. It also strips personal data before sending (sections 3 and 4).

## 3. Backend (NestJS)

Copy the setup from `welinc-backend-vrms` (read only for you; copy, don't import):

| File | What it does |
|---|---|
| `src/instrument.ts` | Starts Sentry before Nest. It must be the **first import** in `main.ts`. With no `SENTRY_DSN` it does nothing |
| `src/monitoring/sentry-options.ts` | The init options and `beforeSend`, an allowlist: it keeps only the method, the path without its query, and the user agent, and it drops 4xx errors and `/health` calls |
| `src/monitoring/redact.ts` | Replaces emails with `[email]` and tokens with `[token]` in every message |
| `src/monitoring/sentry-exception.filter.ts` | Reports 5xx `HttpException`s (Sentry's own filter skips them) |
| `src/monitoring/user-context.ts` | Sets the user as an id and a `role` tag only. Call it right after your guard sets `request.user` |
| `src/monitoring/job-failure.ts` | `reportJobFailure(name, error)`: call it in every scheduled job's `catch`, and never rethrow |
| `src/monitoring/monitoring.module.ts` | Wires the filter in |

Change the `system` tag in `sentry-options.ts` to your own (`vmms`, `bms-booking`, ...). The package is `@sentry/nestjs`.

**Settings** (add them to your env schema and `.env.example`):

| Setting | Value |
|---|---|
| `SENTRY_DSN` | the project's DSN; blank means off |
| `SENTRY_ENVIRONMENT` | `staging` (or `production`); required when the DSN is set |
| `SENTRY_RELEASE` | the commit SHA, baked into the image: `ARG GIT_SHA=` and `ENV SENTRY_RELEASE=$GIT_SHA` as the last lines of your `Dockerfile.prod`, and `--build-arg GIT_SHA="$SHA"` in your deploy's `docker build` |

**Locally, leave `SENTRY_DSN` and `SENTRY_ENVIRONMENT` blank.** A laptop set to `staging` reports as if it were staging, and its errors mix with the real ones. Prove Sentry on staging instead.

**On staging,** send the lead each backend project's DSN. The lead adds `SENTRY_DSN` and `SENTRY_ENVIRONMENT=staging` to your Container App's settings.

## 4. Web app (React and Vite)

Copy the setup from `welinc-web-vrms`:

| File | What it does |
|---|---|
| `src/lib/monitoring/sentry.ts` | `Sentry.init`, called from `main.tsx` before `createRoot`, only when `VITE_SENTRY_DSN` is set. Sets the user (id and `role` tag) and clears it on sign out |
| `src/lib/monitoring/filters.ts` | Drops network errors and every API error (your backend reports its own), strips query strings, and stops after 10 events in one page load |
| `src/lib/monitoring/redact.ts` | The same redaction as the backend |
| `src/lib/monitoring/chunkReload.ts` | After a deploy, a page that asks for a file that no longer exists reloads once instead of crashing |
| `src/components/monitoring/CrashBoundary.tsx`, `CrashScreen.tsx` | The only place a render crash is reported, and the crash screen with its reference code. Don't use Sentry's own `ErrorBoundary`: it would report each crash twice |

The package is `@sentry/react`. Change the `system` tag to your app's (`vmms-web`, `bms-web`).

**Settings** (build time, `.env.example`, all optional; blank means off):

| Setting | Value |
|---|---|
| `VITE_SENTRY_DSN` | the web project's DSN |
| `VITE_SENTRY_ENVIRONMENT` | `staging` |
| `VITE_SENTRY_RELEASE` | `git rev-parse HEAD` in the deploy job |
| `VITE_SENTRY_TUNNEL` | `https://staging-api.welinc.app/monitoring/<your app>` (below) |

### The tunnel (your crash reports go through our gateway)

Browsers with ad blockers drop calls to `sentry.io`, and your app's content policy only allows calls to the API address. So reports go to the gateway, which forwards them to Sentry. The gateway checks that each report carries **your** route's DSN and refuses anything else (403 `TUNNEL_REJECTED`), so nobody can use it to relay to another Sentry project.

To get a route, send the lead your web project's DSN and the route name you want (`vmms-web` or `bms-web`). The lead adds `POST /monitoring/<name>` to the gateway (contract 0001, section 3). Until then, leave `VITE_SENTRY_TUNNEL` blank and keep Sentry off in the web build.

The route takes a body up to 1 MB and 1 report a second per client (bursts of 10). It forwards no cookie, token or client address.

### Readable stack traces (source maps)

Copy two pieces from `welinc-web-vrms`:

- **`vite.config.ts`:** `build.sourcemap: 'hidden'`, and `@sentry/vite-plugin` only when `SENTRY_AUTH_TOKEN` is set. It uploads the maps and deletes them after.
- **`.github/workflows/deploy.yml`:** the *Release name* step, the `VITE_SENTRY_*` and `SENTRY_*` values on the build step, the *Remove source maps* step (it deletes every `.map` and fails if one is left), and the `.map` 404 check in the smoke test. **A source map must never be deployed:** it would publish your source code.

GitHub, in your web repo (Settings → Secrets and variables → Actions):

- **Secret** `SENTRY_AUTH_TOKEN`: an organization token from Sentry (Settings → Developer Settings → Organization Tokens). Only CI uses it. Never put it in a `VITE_*` value.
- **Variables** `SENTRY_ORG` (your org's slug), `SENTRY_PROJECT` (the web project), and your DSN variable.

## 5. Mobile (VMMS, Expo)

Use `@sentry/react-native` and send straight to Sentry. A phone app has no ad blocker or content policy in the way, so it needs no tunnel. Apply the same rules: user as an id and a role only, `sendDefaultPii: false`, the same redaction, no reporting of API errors (the backend reports its own), and `environment` set to `staging`.

## 6. Monitors (your free slots)

- **Cron monitor:** give it to the scheduled job whose silent stop hurts most. Check in from the job with `Sentry.captureCheckIn` at most once every few minutes (see `src/monitoring/directory-poll-monitor.ts` in `welinc-backend-vrms` for a throttled example). Its failures open issues, and your alert rule emails them.
- **Uptime monitor:** point it at your health route through the gateway, such as `https://staging-api.welinc.app/vmms/health`. One call proves the gateway, your backend and its database.

## 7. Check it works

1. Throw a test error on staging (VRMS uses an admin only route behind a staging only switch; turn it off when you're done).
2. Open the issue in Sentry and check:
   - the environment is `staging` and the release is the deployed commit,
   - the stack shows your TypeScript files,
   - the user shows only an id,
   - `geo` reads `[Filtered]`,
   - no email, name, token or query string appears anywhere.
3. On the web app: open any `https://staging-<app>.welinc.app/assets/<file>.js.map`. It must answer 404.

## What to send the lead

- Each backend project's DSN, for your app settings on staging.
- Your web project's DSN and the tunnel route name you want.
- Nothing else. Your Sentry token stays in your own repo's GitHub secrets.
