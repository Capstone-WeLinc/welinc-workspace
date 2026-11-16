# 0025. Error monitoring with Sentry and Azure alerts

**Date**: 2026-11-16
**Status**: In Progress
**Updated**: 2026-11-16, cross checked on another model; 17 gaps closed (health and filter reporting, the gateway tunnel mechanics, every config source, the role tag, double reporting, trace linking, map files) and 3 wording fixes. 2026-11-17, from the first live test: Sentry stores a location worked out from the sender's address, so `city` and `region` join the sensitive fields and AC-6 covers the location; the gateway's two trace headers moved into milestone 1.

## Summary

Every crash and server error in your four apps (backend-vrms, web-vrms, welinc-auth and the portal) gets reported to Sentry on staging and production, with the release, the environment and the user's id and role attached, and never a name, email, code or token. Browser reports travel through two small routes on our own gateway, so ad blockers and the strict content policy don't get in the way. Users see a calm crash screen with a Reload button instead of a white page. One cron monitor, one uptime check and a few Azure alert rules email you when a job stops, VRMS goes down, or the database or a container gets into trouble.

## Requirements

**User stories**:
- As the developer, I want every production crash reported with where it happened and which release caused it, so I fix bugs before a user reports them.
- As a mechanic or office user, I want a page that breaks to tell me what to do next, so I am never stuck on a blank screen.
- As the developer, I want an email when a job stops, VRMS goes down, or the database fills up, so problems surface before the defense does.

**Acceptance criteria**:
- **AC-1**: With `SENTRY_DSN` set, an unhandled exception or any 5xx answer (outside the health routes) in backend-vrms or welinc-auth creates a Sentry issue in that service's project within 1 minute, tagged with `environment` (`staging` or `production`), `release` (the commit SHA), `system`, and, on a signed in request, the user id and role. This includes 5xx answers produced by an existing exception filter (auth's `CodeErrorFilter`).
- **AC-2**: 4xx answers (validation, 401, 403, 404, 409, 429, every `HttpException` below 500) and every answer from a `/health` path (the 503 included) never create an issue.
- **AC-3**: A React render crash, an unhandled error or a rejected promise in web-vrms or the portal creates exactly one issue in that app's project with the same tags, and its stack trace shows the original TypeScript file and line.
- **AC-4**: Browser reports go to `https://<api>/monitoring/vrms-web` and `https://<api>/monitoring/portal` on the gateway. The browser never calls a `sentry.io` host, and the CSP `connect-src` stays as it is.
- **AC-5**: Each tunnel route answers `OPTIONS` with 204 and CORS headers, accepts `POST` up to 1 MB, and answers 405 to any other method and 413 to a larger body. It is rate limited per client (1 request a second, burst 10; 429 beyond), forwards only to its own fixed Sentry project, and sends Sentry no cookies, no `Authorization` header and no client IP address. With the tunnel settings blank, both routes answer 404.
- **AC-6**: No personal data or secret leaves any app: no request bodies, cookies, headers (other than `user-agent`) or query strings, and no email address, name, IP address, location worked out from an address (country, city, region), sign in code, token or password in any event. Checked on a test event from each app sent while seeded values are in play.
- **AC-7**: A page crash inside the app shell keeps the sidebar and top bar and shows the crash screen in the page area: a short message, **Reload**, **Back to dashboard** (portal: **Back to apps**), and a reference code (the first 8 characters of the Sentry event id; no code is shown when Sentry is off). A crash outside the shell (the login page, the shell itself) shows the full page version. Moving to another page clears it.
- **AC-8**: When a lazy loaded file fails to load (typically after a deploy), the page reloads once by itself and nothing is reported. A second failure in the same tab, or any failure while the browser is offline, shows the crash screen without reloading again, and is reported when online.
- **AC-9**: The browser does not report network failures, cancelled requests, offline errors, `ResizeObserver` noise, or API error answers (the server reports its own). API calls carry `sentry-trace` and `baggage` headers, so when a crash follows a failing API call, the browser event and the backend event share one trace id.
- **AC-10**: An exception thrown in any of the 6 scheduled jobs creates an issue tagged with the job name. The directory poll reports to one Sentry cron monitor, which emails when a production check in is missed or fails.
- **AC-11**: A Sentry uptime monitor calls `https://<api>/vrms/health` on production and emails when it fails.
- **AC-12**: Sentry emails the alert address for a new issue and a regression (a resolved issue comes back) on staging and production, with the environment in the email; the cron monitor (AC-10) and the uptime monitor (AC-11) alert for production.
- **AC-13**: Azure alert rules in each environment email the alert address when database storage passes 80%, database CPU stays above 85% for 15 minutes, or any Container App restarts more than 3 times in 15 minutes.
- **AC-14**: With `SENTRY_DSN` (or `VITE_SENTRY_DSN`) blank, an app runs normally and sends nothing; local `.env` files leave them blank. A Sentry outage or a failing tunnel never slows or breaks a request or a page.
- **AC-15**: When `SENTRY_ENVIRONMENT=production` and `SENTRY_DSN` is blank, the app still starts and logs one warning. `npm run env:check` exits 1 when `SENTRY_DSN` is set without a valid `SENTRY_ENVIRONMENT` (`staging` or `production`), or when `SENTRY_TEST_ROUTES=true` and `SENTRY_ENVIRONMENT=production`.
- **AC-16**: With `SENTRY_TEST_ROUTES` on, `POST /vrms/debug/sentry-test` (needs `settings.manage`) and `POST /auth/admin/debug/sentry-test` (needs a suite admin's admin session) throw a test error and answer 500. With `VITE_SENTRY_TEST_ROUTES=true`, each web app has a test page at `/debug/sentry` (no menu link), shown only to users with `settings.manage` (web-vrms) or suite admins (portal), whose button crashes the render. With the switches off, the routes answer 404 and the page's code is not in the build.
- **AC-17**: Source maps are uploaded to Sentry for each web release during the deploy, and no deployed site serves them: requesting any `*.js.map` answers 404, also for builds made without the upload token.
- **AC-18**: `docs/integration/error-monitoring.md` tells VMMS and BMS how to join (optional for them).

## Decision

**Chosen option**: Sentry SDKs in each app, browser reports tunneled through the gateway, free tier monitors, plus Azure metric alerts in Bicep.

Sentry covers application errors, one cron monitor and one uptime check; Azure Monitor covers the platform (database and containers). Sentry plan: the GitHub Student offer (unlimited members, 50k errors, one year), with the free Developer plan as the fallback. Everything is designed to fit the fallback (5k errors, 1 seat, 1 cron monitor, 1 uptime monitor). Data region: US.

**Implementation skills**: `sentry-nestjs-sdk` (`getsentry/sentry-for-ai`, `.claude/skills/sentry-nestjs-sdk/`) · `sentry-react-sdk` (`getsentry/sentry-for-ai`, `.claude/skills/sentry-react-sdk/`) · `sentry-setup-releases` (`getsentry/sentry-for-ai`, `.claude/skills/sentry-setup-releases/`) · `nestjs-best-practices` (`.claude/skills/nestjs-best-practices/`) · `azure-container-apps` (`.claude/skills/azure-container-apps/`, ask first)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch**: none. No table changes. All state lives in Sentry and Azure Monitor (and one in memory timestamp for the poll's check in throttle).

**Sentry layout** (one US org, `welinc`, set up by hand once on 2026-11-17, steps in `infra/RUNBOOK.md`; project slugs as in the table, so a project Sentry's onboarding names after the repo is renamed to match):

| Project | App | Platform |
|---|---|---|
| `vrms-backend` | welinc-backend-vrms | NestJS |
| `vrms-web` | welinc-web-vrms | React |
| `welinc-auth` | welinc-auth | NestJS |
| `welinc-portal` | welinc-web-portal | React |

Staging and production share each project and are told apart by `environment`. Org settings: *Prevent storing of IP addresses* on, *Data scrubber* on, and *Additional sensitive fields* `code, otp, setupCode, reauthToken, refreshToken, accessToken, password, email, name, phone, city, region`. Sentry works out `user.geo` from the address an event arrives from, even with IP storage off and with no IP in the event (the SDK's `infer_ip` hint is ignored for server events), and it does this before the scrubbers run; `city` and `region` blank that location, and `code` already catches `countryCode`. That list also blanks harmless fields with those names (a stack local called `name`, for example); accepted, because privacy wins over a slightly poorer stack view. Per project alert rules: a new issue and a regression, both environments, emailing the alert address. The cron monitor and the uptime monitor email the same address for production only.

**Backend setup (backend-vrms and welinc-auth)**:
- `src/instrument.ts` calls `Sentry.init` and is the first import in `main.ts`. `SentryModule.forRoot()` in the root module. Follow `sentry-nestjs-sdk` for the exact wiring.
- Init options: `dsn`, `environment`, `release`, `initialScope: { tags: { system } }` (`vrms` or `auth`), `sendDefaultPii: false`, `tracesSampleRate: 0` (no performance quota, but incoming `sentry-trace` headers still continue the browser's trace), no profiling, `maxBreadcrumbs: 20`. Check the installed major with `npm view @sentry/nestjs version` before pinning; option names differ between v10 and v11 (the plans check of 2026-11-16 could not confirm the current major).
- Exception filters: Nest runs the most specific matching filter, so a filter that catches an error type stops `SentryGlobalFilter` from seeing it. Register `{ provide: APP_FILTER, useClass: SentryGlobalFilter }` as the catch all, and inside every existing filter that can answer 5xx, call `Sentry.captureException(exception)` for those answers. Today that is welinc-auth's `CodeErrorFilter` (`auth.module.ts`, for `MailFailedError`); backend-vrms has none. `/develop` lists the filters again at build time and covers any new one. Then check what the installed `SentryGlobalFilter` does with an `HttpException` of 500 or more: if it treats it as expected and skips it, capture those in a small wrapper so AC-1 holds.
- `beforeSend` (an allowlist, so a new field can't leak by accident): drop the event when it is an `HttpException` below 500, or when `request.url`'s path ends in `/health`; rebuild `event.request` as only `{ method, url }` with the query string removed and `headers: { 'user-agent' }`; run `redact()` (below) over the message, every exception value and every breadcrumb message.
- User context: right after `request.user` is set (backend-vrms `src/auth/guards/jwt-auth.guard.ts`; welinc-auth `src/auth/guards/request-authenticator.ts`, which both its JWT guards use), call `Sentry.setUser({ id: user.id })` and `Sentry.setTag('role', <the caller's role names for this system, comma joined>)`. Role names, never permission keys. No role for this system means no `role` tag. Never set email, username or IP.
- Jobs: a shared `reportJobFailure(name, err)` helper per repo calls `Sentry.captureException(err, { tags: { job: name } })` and returns; each job's `catch` calls it and keeps its current logging, and never rethrows (a rethrow from a scheduler callback can double report or stop the scheduler). Job names: `directory-poll`, `permission-sync`, `embedding-catchup`, `attachment-purge` (backend-vrms), `temporary-grant-sweep`, `session-sweep` (welinc-auth).
- Directory poll monitor: the poll runs every 30 s (`DIRECTORY_POLL_MS`), but Sentry schedules count in minutes. After each run, send an `ok` check in when 5 minutes have passed since the last one sent (the last sent time is held in memory, so the first run after a boot checks in at once), and an `error` check in at once on a failure. No `in_progress` check ins. Slug `vrms-directory-poll`, config `{ schedule: { type: 'interval', value: 5, unit: 'minute' }, checkinMargin: 5, maxRuntime: 2 }`; the SDK creates the monitor on the first check in and tags each check in with the environment. Its alert is set to production only, because a staging app that sleeps or restarts would report false misses.

**Browser setup (web-vrms and the portal)**:
- `Sentry.init` in `src/main.tsx` before `createRoot`, only when `VITE_SENTRY_DSN` is set. Follow `sentry-react-sdk`.
- Init options: `dsn`, `environment`, `release`, `tunnel` (`VITE_SENTRY_TUNNEL`), `initialScope: { tags: { system } }` (`vrms-web` or `portal`), `sendDefaultPii: false`, `integrations: [browserTracingIntegration()]` with `tracesSampleRate: 0` (no spans sent, but the integration is what adds `sentry-trace` and `baggage` to API calls), `tracePropagationTargets: [<the API origin from VITE_API_BASE_URL>]`, no replay, `maxBreadcrumbs: 20`, console breadcrumbs off, fetch breadcrumbs reduced to method, path and status.
- `ignoreErrors` plus a `beforeSend` filter: `TypeError: Failed to fetch`, `NetworkError`, `Load failed`, `AbortError`, `ResizeObserver loop`, and every error the API client raises for an HTTP answer (it carries a status, so filter on that). `beforeSend` also drops `request.query_string`, strips the query from `request.url`, runs `redact()`, and stops after 10 events in one page load (a counter in memory), so a crash loop can't empty the quota.
- Single report per crash: a custom error boundary component captures in `componentDidCatch` with `Sentry.captureException(error, { contexts: { react: { componentStack } } })` and keeps the returned event id for the reference code. `createRoot` gets `onUncaughtError` and `onRecoverableError` set to `Sentry.reactErrorHandler()`, and `onCaughtError` set to a plain `console.error` (the boundary already reported it). Sentry's own `ErrorBoundary` is not used, since it would report a second time.
- Boundaries: one around the whole app (full page fallback) and one around the routed page inside `DashboardShell` (web-vrms) and the portal's shell, keyed on the location so a route change resets it. The fallback uses the design system (`design.md` and `docs/context/vrms/design.md`): title "Something went wrong on this page", one line "Try reloading. If it keeps happening, send this code to your admin.", the reference code in mono (left out when Sentry is off), **Reload**, **Back to dashboard** or **Back to apps**. English only until feature 7.
- User context: web-vrms sets it where the session is built (`toUser` in `src/lib/session/session.ts`): `Sentry.setUser({ id })` and tag `role` from the `roles` entry whose `system` is `VRMS`, read from the answer itself, not from `user.role` (which falls back to `MECHANIC`); no entry means no tag. `signOut` calls `Sentry.setUser(null)`. The portal does the same from its own session answer (`src/lib/auth.ts`), with `role` set to `suite_admin` when `suiteAdmin` is true, `system_admin` when `adminOf` is not empty, else `user`.
- Stale files (AC-8): listen for Vite's `vite:preloadError` window event (fired when a lazy file fails to load; the apps have three `lazy()` calls today, and the event covers any future ones). In the handler: if `navigator.onLine` is false, do nothing (the boundary shows the crash screen); else if `sessionStorage['chunk-reload']` is unset, set it, call `event.preventDefault()` and `location.reload()`, without reporting; else let the error through. Clear the flag on `window` `load` 10 seconds after a successful page load. Wrap every `sessionStorage` access in try/catch (a blocked storage means no auto reload, never a crash).
- Vite: `build.sourcemap: 'hidden'` (maps are built but the bundle doesn't point to them). `@sentry/vite-plugin` runs only when `SENTRY_AUTH_TOKEN` is set, with `org`, `project`, `authToken` from the environment, `release.name` equal to `VITE_SENTRY_RELEASE`, `sourcemaps.assets: 'dist/**'` and `sourcemaps.filesToDeleteAfterUpload: ['dist/**/*.map']`. Separately, every deploy job runs `find dist -name '*.map' -delete` after the build, whether or not the upload ran.
- The test page: route `/debug/sentry` registered only inside `if (import.meta.env.VITE_SENTRY_TEST_ROUTES === 'true')`, so Vite removes it from other builds (check with a search of `dist` for the page's text). No sidebar or menu link; you type the address.

**`redact()`** (one small helper per repo, unit tested): replace email addresses with `[email]`, JWT shaped strings (`eyJ…`) with `[token]`, and `Bearer <x>` with `Bearer [token]`. Runs on the server and in the browser.

**Gateway tunnel (`infra/gateway/`)**:
- Routes: `POST /monitoring/vrms-web` forwards to `https://${SENTRY_INGEST_HOST}/api/${SENTRY_PROJECT_VRMS_WEB}/envelope/`, and `POST /monitoring/portal` to `https://${SENTRY_INGEST_HOST}/api/${SENTRY_PROJECT_PORTAL}/envelope/`. The upstream is built into `$upstream`, so `proxy_pass $upstream` sends that exact path, through the existing `resolver` (`default.conf.template`) with `proxy_ssl_server_name on` and `Host` set to the ingest host.
- On or off: `05-check-env.sh` writes `/etc/nginx/generated/monitoring.conf` (the same pattern as `cors-origins.map`), and the server block includes it. All three settings blank: the file holds the two locations as `return 404`. All three set and valid: the real locations. Any other mix, or a host not matching `^o[0-9]+\.ingest(\.[a-z]{2})?\.sentry\.io$`, or a project id not matching `^[1-9][0-9]*$`: exit 1 naming the variable.
- A new snippet `snippets/tunnel.conf.template`, not the shared `route.conf` (that one forwards the client address and uses the shared `flood` zone): its own `limit_req_zone $client_addr zone=tunnel:1m rate=1r/s` with `burst=10 nodelay` and status 429; `client_max_body_size 1m`; `if ($request_method = OPTIONS) { return 204; }` with the CORS headers for our origins; `if ($request_method != POST) { return 405; }` with an `Allow: POST, OPTIONS` header; the usual `Access-Control-Allow-Origin` answer on the POST (the SDK posts `text/plain` with no preflight, so only this header matters; an origin outside `ALLOWED_ORIGINS` gets none); `proxy_set_header` blank for `Cookie`, `Authorization`, `X-Forwarded-For` and `X-Real-IP`; `X-Request-Id` not forwarded; `proxy_connect_timeout 5s`, `proxy_read_timeout 10s` (the SDK doesn't wait on the answer).
- CORS for API calls: add `sentry-trace, baggage` to `$cors_request_headers` (today `Authorization, Content-Type, X-Request-Id`). That one map serves every system, so VMMS and BMS calls may carry them too; harmless, and contract 0001 says so.
- `check-routes.mjs` gains cases: 404 when off, 405 for GET, 204 with CORS headers for OPTIONS, 413 for a 2 MB body, 429 for a burst, the allow origin header on a POST from an allowed origin and none from another, and no `Cookie` or client address reaching a stub upstream; plus a boot failure for a half set config.
- Contract 0001, next version: the `/monitoring/*` routes and the two allowed headers.

**Azure alerts (`infra/env.bicep`)**: `env.bicep` takes `alertEmail` from `infra/private/<env>.json` (the field is already in the private file's shape, and `subscription.bicep` reads the same file through `apply.sh`). One action group per environment emailing it, and three metric alert rules per environment:

| Rule | Resource | Metric | Condition |
|---|---|---|---|
| Database storage | PostgreSQL server | `storage_percent` | average > 80 over 15 min |
| Database CPU | PostgreSQL server | `cpu_percent` | average > 85 over 15 min |
| Restart loop | every Container App (one rule, scoped to the resource group, split by app) | `RestartCount` | total > 3 over 15 min |

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/monitoring/vrms-web` (gateway) | POST, OPTIONS | Sentry envelope body (`text/plain`) | Sentry's answer; 204 for OPTIONS | public, rate limited | 405, 413, 429, 404 when off |
| `/monitoring/portal` (gateway) | POST, OPTIONS | same | same | public, rate limited | same |
| `/vrms/debug/sentry-test` | POST | none | always throws, 500 | JWT with `settings.manage` | 404 when switch off, 401, 403 |
| `/auth/admin/debug/sentry-test` | POST | none | always throws, 500 | `AdminSessionGuard` plus a check that the caller is a suite admin (the admin session already required the emailed code at sign in, spec 0013) | 404 when switch off, 401, 403 |

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Backend event | `environment` | `SENTRY_ENVIRONMENT`, set by Bicep from `envName` (`prod` → `production`, `staging` → `staging`) |
| Backend event | `release` | `SENTRY_RELEASE`, baked into the image from build argument `GIT_SHA` (the staging deploy's commit); production promotes that same image, so the release matches |
| Browser event | `environment` | `VITE_SENTRY_ENVIRONMENT`, a literal in each deploy job (`staging` or `production`) |
| Browser event | `release` | `VITE_SENTRY_RELEASE` from `git rev-parse HEAD` after checkout (not `github.sha`, which is wrong for a production run with a `sha` input) |
| Any event | `system` tag | a constant in `initialScope` per app (`vrms`, `auth`, `vrms-web`, `portal`) |
| Backend event | user id, role | `request.user` in the guard named above (its id, and its role names for this system) |
| Browser event | user id, role | web-vrms: the refresh answer's `id` and its `VRMS` entry in `roles`; portal: its session answer (`suiteAdmin`, `adminOf`) |
| Job event | `job` tag | the fixed names passed to `reportJobFailure` |
| Crash screen | reference code | first 8 characters of the event id returned by the boundary's `captureException`; none when the SDK is off |
| Browser init | `VITE_SENTRY_DSN` | repo variables `SENTRY_DSN_VRMS_WEB` (web-vrms) and `SENTRY_DSN_PORTAL` (portal); one DSN serves both environments, since projects are shared |
| Browser init | `VITE_SENTRY_TUNNEL` | derived in the deploy job: the existing `STAGING_API_URL` or `PROD_API_URL` plus `/monitoring/vrms-web` or `/monitoring/portal`; no new variable |
| Browser init | `VITE_SENTRY_TEST_ROUTES` | the literal `true` in the staging deploy job only |
| Backend init | `SENTRY_DSN` | `infra/private/<env>.json`, new fields `sentry.dsn.vrmsBackend` and `sentry.dsn.auth` (DSNs are public values, so Bicep sets them as plain settings, not secrets) |
| Gateway | `SENTRY_INGEST_HOST`, `SENTRY_PROJECT_VRMS_WEB`, `SENTRY_PROJECT_PORTAL` | parsed by `apply.sh` from `sentry.dsn.vrmsWeb` and `sentry.dsn.portal` in the same private file (host and the trailing id of each DSN), passed into `gatewaySettings` (`env.bicep`); `apply.sh` exits if the two DSNs name different hosts |
| Backend init | `SENTRY_TEST_ROUTES` | Bicep: `'true'` when `envName == 'staging'`, unset for `prod` |
| Cron monitor | schedule | fixed: interval 5 minutes, margin 5, max runtime 2 |
| Alerts | recipient | `alertEmail` in `infra/private/<env>.json` (Azure); the Sentry alert rules (Sentry) |
| Source map upload | org, project, token | repo variables `SENTRY_ORG` and `SENTRY_PROJECT` (`vrms-web` or `welinc-portal`); repo secret `SENTRY_AUTH_TOKEN` |

**Key invariants**:
- Monitoring never blocks: no event send is awaited on a request or render path, and a blank DSN means off, never a crash.
- Nothing personal leaves: the client side allowlist and `redact()` and Sentry's server side scrubbing all apply; none is relied on alone.
- One event per failure: the server reports 5xx, the browser never reports an API answer, and a render crash is captured by the boundary only.
- Test routes never exist in production (boot refuses the combination; the web page is not in a production build).
- No `*.map` file is ever deployed.

**Security model**:
- The DSN is public by design (it can only send events), so `VITE_SENTRY_DSN` is fine in the browser. `SENTRY_AUTH_TOKEN` (can upload and read) lives only in GitHub Actions secrets with the narrowest scope (`project:releases`), never in an image or a `VITE_*` value.
- The tunnel is public because a crash can happen before sign in. The gateway can't read an envelope's key, but each route only ever forwards to its one fixed project, and Sentry checks that the envelope's key belongs to that project (task 7 confirms the rejection). If Sentry accepted a mismatched envelope, the worst case is junk in our own project, capped by the rate limit.
- The test routes need an admin (`settings.manage`, or a suite admin's admin session) and the staging only switch.
- Sentry members: you as owner; groupmates as members only once the student plan is active. Data is processed in the US by Sentry under its standard terms; no personal data is sent (AC-6), in line with the Data Privacy Act care the project already takes.

**Configuration required**:
- backend-vrms and welinc-auth (`env.ts` with a `superRefine` for the AC-15 rules, keyed on `SENTRY_ENVIRONMENT` because staging also runs `NODE_ENV=production`; `.env.example`; `Dockerfile.prod`; `infra/env.bicep`): `SENTRY_DSN` (optional), `SENTRY_ENVIRONMENT` (`staging` or `production`, required when the DSN is set), `SENTRY_RELEASE` (from `ARG GIT_SHA` in `Dockerfile.prod`), `SENTRY_TEST_ROUTES` (optional boolean).
- web-vrms and the portal (`.env.example`; spec 0010's build check must accept every one of these blank): `VITE_SENTRY_DSN`, `VITE_SENTRY_ENVIRONMENT`, `VITE_SENTRY_RELEASE`, `VITE_SENTRY_TUNNEL`, `VITE_SENTRY_TEST_ROUTES`. GitHub per web repo: variables `SENTRY_DSN_VRMS_WEB` or `SENTRY_DSN_PORTAL`, `SENTRY_ORG`, `SENTRY_PROJECT`, and secret `SENTRY_AUTH_TOKEN` (four values each).
- Gateway (`infra/gateway/README.md`, `05-check-env.sh`): `SENTRY_INGEST_HOST`, `SENTRY_PROJECT_VRMS_WEB`, `SENTRY_PROJECT_PORTAL`.
- `infra/private/<env>.json` and `infra/private.example.json`: `sentry.dsn.vrmsBackend`, `sentry.dsn.auth`, `sentry.dsn.vrmsWeb`, `sentry.dsn.portal`.
- Spec 0008's env tables gain every row above.

**Critical test scenarios**:
- Happy path: on staging, an admin hits each test route and test page; four issues arrive with the right environment, release, role and a readable TypeScript stack, one issue per crash, verifies **AC-1**, **AC-3**, **AC-16**, **AC-17**
- Hidden paths: a mail failure in auth (handled by `CodeErrorFilter`) creates an issue; a validation 400, a wrong password 401 and a failing health 503 create none, verifies **AC-1**, **AC-2**
- Noise and linking: a page with no network creates nothing; an API call carries `sentry-trace`, and a crash after a forced backend 500 shows the same trace id on both events, verifies **AC-9**
- Privacy: trigger the test error while signed in with a seeded account and a reset link with a code in its URL; the event holds no email, name, IP, code, token, header or query string, and `user.geo` reads `[Filtered]` throughout, verifies **AC-6**
- Crash screen: a crash inside the shell keeps the sidebar and shows the reference code that matches the Sentry event; navigating away clears it; with the DSN blank, no code shows, verifies **AC-7**, **AC-14**
- Stale deploy: delete a lazy chunk on staging; the page reloads once silently; delete it again and the crash screen appears; offline, no reload happens, verifies **AC-8**
- Tunnel: GET gets 405, OPTIONS 204, a 2 MB body 413, a burst 429, a half set config stops the gateway at boot, and the stub upstream sees no cookie or client address, verifies **AC-4**, **AC-5**
- Off switch and boot: with every DSN blank locally, the apps start and send nothing; `SENTRY_TEST_ROUTES=true` with `production` makes `npm run env:check` exit 1, verifies **AC-14**, **AC-15**
- Maps: after a staging deploy, any `*.js.map` URL answers 404; a build without the token leaves no `.map` in `dist`, verifies **AC-17**
- Jobs: force the directory poll to throw on staging; an issue tagged `job: directory-poll` arrives and the monitor shows an error check in, verifies **AC-10**
- Alerts: fire a test notification on each Azure rule and on the uptime monitor, and resolve then reproduce an issue for a regression; each email arrives, verifies **AC-11**, **AC-12**, **AC-13**

## Build plan

Tracer Bullet: one thin thread through backend-vrms and web-vrms first, proven against the real Sentry org from your laptop (set a DSN in your own local `.env` for the proof only), then the shared side, then the deploy and the alerts on staging. Milestones 3 and 4 need VRMS feature 26's `deploy.yml` (its milestone "CD to staging").

**Milestone 1: thin thread in VRMS**
1. Create the Sentry org (US), the 4 projects, the org scrubbing settings and the per project alert rules; record the steps in `infra/RUNBOOK.md`, satisfies **AC-6**, **AC-12**
2. backend-vrms: `instrument.ts`, `SentryModule`, `SentryGlobalFilter` (and the 5xx `HttpException` check), the allowlist `beforeSend` with the 4xx and health drops, `redact()` with unit tests, user context in the JWT guard, the env variables with the `superRefine` rules, satisfies **AC-1**, **AC-2**, **AC-6**, **AC-14**, **AC-15**
3. backend-vrms: `POST /vrms/debug/sentry-test` behind `settings.manage` and `SENTRY_TEST_ROUTES`, satisfies **AC-16**
   Also pulled forward from task 7 (workspace commit `efc94f9`): `sentry-trace, baggage` in the gateway's `$cors_request_headers`, its `check-routes.mjs` case and contract 0001 section 3, because the browser's API calls fail their preflight without them once `VITE_SENTRY_DSN` is set.
4. web-vrms: `Sentry.init` with `browserTracingIntegration`, the React 19 handlers, the custom boundaries with the crash screen, the ignore list, API answer filter and per page cap, user context from the `VRMS` role entry, the `vite:preloadError` reload, the build flagged test page, satisfies **AC-3**, **AC-7**, **AC-8**, **AC-9**, **AC-16**

**Milestone 2: the shared side**
5. welinc-auth: the same backend setup as tasks 2 and 3, plus `captureException` in `CodeErrorFilter` for its 5xx answers, and `POST /auth/admin/debug/sentry-test` behind the admin session and a suite admin check, satisfies **AC-1**, **AC-2**, **AC-6**, **AC-14**, **AC-15**, **AC-16**
6. web-portal: the same browser setup as task 4 (**Back to apps**, role from `suiteAdmin` and `adminOf`, test page for suite admins), satisfies **AC-3**, **AC-7**, **AC-8**, **AC-9**, **AC-16**
7. Gateway: `tunnel.conf.template`, the generated `monitoring.conf` with the on, off and refuse rules in `05-check-env.sh`, the new `check-routes.mjs` cases (the CORS headers already landed in milestone 1), a live check that Sentry rejects a mismatched envelope; contract 0001 next version, satisfies **AC-4**, **AC-5**, **AC-9**

**Milestone 3: jobs and releases**
8. Jobs: `reportJobFailure` in both backends, called from all 6 jobs; the throttled directory poll check ins, satisfies **AC-10**
9. Releases: `ARG GIT_SHA` and `SENTRY_RELEASE` in both `Dockerfile.prod`; in both web repos' `deploy.yml`, the `VITE_SENTRY_*` build values from the sources above, `build.sourcemap: 'hidden'`, the plugin upload, the unconditional `find dist -name '*.map' -delete`, and a map 404 check in the smoke test; repo variables and secret, satisfies **AC-1**, **AC-3**, **AC-17**

**Milestone 4: alerts and hand off**
10. Bicep and scripts: the `sentry` fields in `infra/private.example.json`, `apply.sh` parsing the gateway values from the DSNs, the `SENTRY_*` settings per app and in `gatewaySettings`; `alertEmail` into `env.bicep`, the action group and the three metric alert rules per environment, satisfies **AC-13**, **AC-14**
11. Sentry uptime monitor on production `/vrms/health` and the cron monitor's production only alert (hand set, in the runbook), satisfies **AC-10**, **AC-11**, **AC-12**
12. `docs/integration/error-monitoring.md` for VMMS and BMS (how to get a project, the tunnel route pattern, the scrubbing rules to copy), satisfies **AC-18**

## Consequences

**Positive**:
- Production bugs, stopped jobs, an unreachable VRMS and a filling database all reach your inbox before a user or the panel finds them.
- Every issue names the release, so a bad deploy is obvious and rollback (spec 0008) has evidence behind it.
- Users get a way forward instead of a white page, and the reference code ties a complaint to the exact event.

**Negative / tradeoffs**:
- Only 1 of the 6 jobs gets a missed run check; the other 5 report failures but not a silent stop. Buying 5 more monitors (about $4 a month) closes that later.
- Only VRMS gets an uptime check; auth relies on Azure's probes and Sentry issues.
- The fallback plan allows 5k errors a month. The per page cap (10), the tunnel limit (1 a second per client) and Sentry's spike protection slow a crash loop down, but a loop across many users can still use the month up, and events past the quota are dropped.
- Azure metric alerts cost a few cents a month each from the credit.
- One more account, one more token and four new settings per app to manage; staging alert email adds noise during the integration week.
- The broad sensitive fields list hides some harmless stack values, and it must grow when a new field holds personal data.
- `sentry-trace` and `baggage` become allowed headers for every system behind the gateway.

**Neutral**:
- Spec 0008's tables and `deploy.yml`, spec 0010's checks and contract 0001 all gain small additions.
- The `sentry` MCP server added to `agents/vrms/mcp.json` belongs to this spec; it lets the agent read real issues once the org exists.

## Follow-up

- [ ] Suite spec 0008's **CORS values** line still lists three request headers; `/sync` brings it in line with contract 0001 section 3.
- [ ] Claim the Sentry student offer through the GitHub Student Pack before task 1; if it fails, use the free Developer plan (the design fits it). Save the login in your password manager.
- [ ] `/sync` adds `sentry-nestjs-sdk`, `sentry-react-sdk` and `sentry-setup-releases` to the *Load on match* list and `sentry` to the MCP servers line in `agents/vrms/AGENTS.md`.
- [ ] `sentry-fix-issues` (`getsentry/sentry-for-ai`) is worth installing after go live, to triage real issues through the MCP server.
- [ ] Spec 0008: add the new variables, secrets and private fields to its tables, `GIT_SHA` to the image build, and the map steps to `deploy.yml`.
- [ ] Spec 0010: accept the optional `SENTRY_*` and `VITE_SENTRY_*` values and the AC-15 refusals.
- [ ] Later, if money allows: cron monitors for the other 5 jobs, an uptime check for `/auth/health`.
- [ ] The domain rename to `welinc.app` lands before this is built; every address here is written as `<api>`, so it is unaffected.
