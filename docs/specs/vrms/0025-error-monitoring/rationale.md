# 0025. Error monitoring: rationale

The decision record behind [index.md](index.md). `/develop` skips this file.

## Context

The suite goes live on Azure on 2026-11-20 (spec 0008), with the mock defense on Nov 28 and the integration defense on Dec 4. Today nobody hears about a failure until someone complains: the backends use NestJS's default exception handling and print to the container log, both frontends have no error boundary (a render crash leaves a white page), and the only Azure alert is the budget.

Four of your repos are in play: backend-vrms and web-vrms (VRMS), and welinc-auth and the portal (shared, which you own). A sign in failure or a portal crash breaks VRMS too, so watching only VRMS would miss the failures that block everyone. Six scheduled jobs run inside the backends (directory poll every 30 s, permission sync, embedding catch up, attachment purge, temporary grant sweep, session sweep); a job that stops silently is invisible today.

Forces: no budget beyond the $200 Azure credit, and the only card on hand (Maya) is refused by foreign merchants, so anything paid is out for now. A strict CSP limits browser calls to our own domain. The suite handles personal data (names, emails, phone numbers, sign in codes), so nothing personal may leave for a third party service. One developer operates everything, so the setup must be small and mostly free of upkeep.

## Options considered

### Option 1: Sentry, with Azure alerts for the platform (chosen)

Sentry SDKs in all four apps, browser reports tunneled through the gateway, the free tier cron and uptime monitors, plus a few Azure Monitor metric alerts.

**Pros**: purpose built error grouping, release tracking and source maps; official NestJS and React 19 support and official agent skills; the student offer covers the whole team; Azure covers what Sentry can't see (database, restarts).
**Cons**: a third party receives event data (handled by scrubbing on both sides); free tier monitors are scarce (1 cron, 1 uptime); another account and token.

### Option 2: Honeybadger

The same idea from a smaller vendor, with uptime checks and check ins (job heartbeats) included more generously.

**Pros**: simpler product; check ins fit the six jobs well.
**Cons**: smaller community and fewer guides for NestJS 11 and React 19; no official agent skills or MCP server found; you already chose Sentry.

### Option 3: Azure only (Application Insights and Log Analytics)

Send errors and traces to Application Insights through OpenTelemetry, with alert rules on log queries.

**Pros**: no new vendor; data stays in the same subscription; costs come from the credit.
**Cons**: weak error grouping and no browser source map support out of the box; log query alerts take real KQL work; ingestion costs per GB eat the credit; the setup is heavier than the Sentry SDKs.

### Option 4: Logs only

Rely on the Log Analytics workspace that spec 0008 already creates, and read logs when something seems wrong.

**Pros**: nothing to build.
**Cons**: nothing alerts; browser crashes never reach a log at all; the scope's Done when (errors in one place with release and role) is not met.

## Rationale

Option 1 meets the scope's Done when with the least operating work: the SDKs, release tagging and source maps are the product's core, and its official skills give `/develop` the real setup instead of guesses. Azure alerts fill the gap Sentry can't see (database storage, CPU, restart loops) from inside the same Bicep that already runs the suite, so platform monitoring needs no second vendor.

The monitor choices follow the money force: the free tier's single cron monitor goes to the directory poll, the job whose silent stop does the most damage (VRMS stops seeing new, changed or removed people), and the single uptime check goes to `/vrms/health` through the gateway, which proves the gateway, the VRMS backend and its database in one call. The other jobs still report failures as normal issues, at no cost. This leaves silent stops of five jobs unwatched, a gap accepted until money allows.

The tunnel sits on the gateway instead of in app code because each route is hard wired to one project, so the usual reason to tunnel in code (checking the envelope's DSN) mostly goes away; Nginx gives method, size and rate limits natively, and junk browser traffic never reaches a backend. Tracing stays off (`tracesSampleRate: 0`) because no performance problem has been measured; trace headers still flow so a browser crash and its backend error share an id. Session replay stays out because it records screens full of names and ticket data.

A cross check on another model (2026-11-16) closed 17 gaps, the load bearing ones being: the health 503 and auth's own exception filter (one reported noise, the other hid mail failures), the gateway template (plain envsubst can't render a conditional route, so the check script now writes an include), a separate tunnel snippet (the shared one forwards the client address), every config value's source (DSNs in the private file, the tunnel URL derived from the API URL, the release from `git rev-parse HEAD` so a rollback is tagged right), the role tag (web-vrms's `MECHANIC` fallback would have tagged wrong), double reporting of render crashes (a custom boundary is now the only capturer), trace headers needing `browserTracingIntegration`, and map files left in builds without the upload token. The cron monitor's alert moved to production only, because a sleeping staging app would page you with false misses.

Small calls made while writing, without a separate question: one project per app (separate alert rules and quotas per app; runner up, one project per system); hidden source maps uploaded by the Vite plugin (runner up, the Sentry CLI in the workflow); a throttled 5 minute check in for the 30 s poll (Sentry schedules count in minutes; runner up, monitoring the permission sync instead); scrubbing on both sides (client `beforeSend` plus Sentry's server side scrubbing, so neither is a single point of failure).

## References

**Project sources**:
- VRMS feature 27 in `docs/scope/vrms/platform.md` (the Done when)
- Spec 0008 (hosting, `deploy.yml`, Bicep, `alertEmail`), spec 0010 (env checks at boot and build), suite spec 0008 (the gateway in `infra/gateway/`), contract 0001
- `welinc-backend-vrms/src/health/health.controller.ts`, the jobs listed in index.md, `infra/gateway/templates/default.conf.template` (`$cors_request_headers`)
- Installed skills: `sentry-nestjs-sdk`, `sentry-react-sdk`, `sentry-setup-releases` (`getsentry/sentry-for-ai`)

**Practices & standards**:
- Report server faults, not client mistakes (5xx only)
- Data minimization: send ids and roles, never names, emails or secrets
- Defense in depth for scrubbing (client and server)
- Monitoring must never block the request path
- Rate limit every public endpoint

**Links** (checked on 2026-11-16):
- Sentry pricing: https://sentry.io/pricing/
- Sentry for education (student offer): https://sentry.io/for/education
- NestJS guide: https://docs.sentry.io/platforms/javascript/guides/nestjs/
- React guide: https://docs.sentry.io/platforms/javascript/guides/react/
- SDK options, including `tunnel`: https://docs.sentry.io/platforms/javascript/configuration/options/
- Data storage location (cannot change later): https://docs.sentry.io/organization/data-storage-location/
- Server side scrubbing: https://docs.sentry.io/security-legal-pii/scrubbing/server-side-scrubbing/
- Agent skills: https://docs.sentry.io/ai/agent-skills
- MCP server: https://mcp.sentry.dev/mcp
- Student offer note: a Sentry forum thread reports pack verification failures, hence the fallback plan: https://forum.sentry.io/t/sentry-github-educational-pack/7568
