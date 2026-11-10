# 0008. Gateway for the whole suite

**Date**: 2026-11-10
**Status**: Accepted
**Scope row**: [S9. Gateway for the whole suite](../../../scope/_root/shared-services.md#s9-gateway-for-the-whole-suite--in-progress)
**Builds contract section**: [0001](../0001-shared-services-contract/index.md) section 3 (and amends it, see AC-27)

## Summary

The gateway is the one front door every app calls. Today it knows only auth and VRMS, and its config sits inside `welinc-auth`. This spec moves it to `infra/gateway/` in the workspace, adds the VMMS and BMS routes, and gives every failure a readable JSON answer, so a system that isn't running only breaks its own routes. The same template runs locally and on Azure, with only settings changing. VMMS and BMS don't change anything yet; their move is S11, so a test script with stand in containers proves their routes for now.

## Requirements

**User stories**:
- As a developer in any group, I want the gateway to start and serve its routes when other systems aren't running, so that I only need the shared services and my own system.
- As a web app, I want every gateway failure to be JSON with CORS headers, so that I can show a real error instead of a browser CORS failure.
- As the shared services owner, I want one config for every environment, so that a route can't work locally and be missing on Azure.

**Acceptance criteria**:

Routing
- **AC-1**: Each prefix in the route table below reaches its upstream with the path and query unchanged, through `<prefix>/...`.
- **AC-2**: `/vmms/analytics/x` reaches the VMMS analytics service and `/vmms/x` reaches the VMMS backend.
- **AC-3**: `/`, `/repairs/x`, `/vmmsx`, each bare prefix with no trailing slash (`/auth`, `/uploads`, `/vrms`, `/vmms`, `/vmms/analytics`, `/bms`) and any other path outside the table answer 404 `NOT_FOUND` and reach no upstream.
- **AC-4**: `GET /health` answers 200 `{ "status": "ok" }` with every upstream stopped.
- **AC-5**: With one system stopped, its routes answer 502 `UPSTREAM_UNAVAILABLE` and every other route keeps working. For up to 5 seconds right after the stop they may answer 504 `UPSTREAM_TIMEOUT` instead, while the gateway still holds the old address (the resolver's `valid=5s`). Once that system answers its own health check, its routes work within 10 seconds, with no gateway restart (the system's own boot time comes first: the local VRMS backend takes about 23 seconds). (Proven locally; what a stopped Azure app answers is a staging check, see Follow-up.)
- **AC-6**: For each route, a body exactly at the limit passes and one byte over answers 413 `PAYLOAD_TOO_LARGE`.
- **AC-7**: An upstream slower than its route's read timeout answers 504 `UPSTREAM_TIMEOUT` (proven live on the 30 s route). Each route's timeout and body limit in the loaded config (`nginx -T`) match the table.

CORS
- **AC-8**: A request from a listed origin gets `Access-Control-Allow-Origin` with that exact origin, `Access-Control-Allow-Credentials: true` and `Vary: Origin`. An unlisted origin gets no `Access-Control-Allow-*` header. No environment answers `*`.
- **AC-9**: A preflight from a listed origin answers 204 with the methods, request headers and max age below, and reaches no upstream. A preflight from an unlisted origin answers 204 with no `Access-Control-*` header at all.
- **AC-10**: `Access-Control-*` headers set by an upstream never reach the browser: a response carries only the gateway's, and one `Access-Control-Allow-Origin` at most.
- **AC-11**: The 404, 413, 429, 502 and 504 answers from the gateway are JSON in the error shape below and carry the same CORS headers as AC-8, plus `X-Request-Id`. An error body or status the upstream sends itself (a 503 from a health route, a 502 from a service) passes through untouched. Other errors nginx makes itself (400, 414 and the like) stay nginx's plain page; browsers don't reach them in normal use.
- **AC-12**: A credentialed `POST /vmms/session/refresh` from `http://localhost:8002` and `POST /bms/session/refresh` from `http://localhost:8003` pass CORS, and `Set-Cookie` reaches the browser unchanged. (`docs/integration/web-login.md`'s last step.)

Start up and config
- **AC-13**: The container exits at start with a message naming the setting when any rule below is broken: a required setting isn't set; an `ALLOWED_ORIGINS` entry is empty, a duplicate, holds an uppercase letter or isn't a plain `http://` or `https://` origin (spaces around the commas are trimmed; a `*`, a path or a trailing slash are refused); a `*_UPSTREAM` isn't `scheme://host[:port]` (a path or trailing slash is refused); `TRUST_EDGE_PROXY` isn't 0 or 1; the rate or burst isn't a positive whole number.
- **AC-14**: `infra/gateway/` builds one image that runs from settings alone: the test compose runs it with no bind mounts (local compose may mount `templates/` for quick edits). There is one template set for every environment. `docker-compose.shared.yml` uses it, and `welinc-auth/nginx.conf` no longer exists.

Forwarded headers
- **AC-15**: With `TRUST_EDGE_PROXY=0`, the upstream sees `X-Forwarded-For` as one value with no comma, the same whether or not the caller sent its own, and `X-Forwarded-Proto` as the gateway's scheme.
- **AC-16**: With `TRUST_EDGE_PROXY=1`, the upstream sees `X-Forwarded-For` as exactly the last entry of the incoming header, and `X-Forwarded-Proto` as the incoming value when it is `http` or `https`.
- **AC-17**: The upstream's `Host` is its own name from the upstream setting.
- **AC-18**: A caller's `X-Request-Id` matching `^[A-Za-z0-9._-]{1,64}$` is kept. Any other value, or none, is replaced with a generated id. The upstream, the response and the access log show the same id. Every gateway answer carries it: proxied, preflight, `/health` and errors.

Limits and logs
- **AC-19**: Past the flood limit, a caller gets 429 `RATE_LIMITED` with `Retry-After: 1`. Preflights and `GET /health` never count, and with `TRUST_EDGE_PROXY=1` one client's flood doesn't limit a different client address.
- **AC-20**: Each proxied request writes one JSON line to the container log with the fields below. Secrets in a query string (`?code=...`), `Authorization` and `Cookie` never appear in the container log, including when the upstream is down.
- **AC-21**: With `GATEWAY_HSTS` set to a value, every answer in the header table below carries `Strict-Transport-Security` with that value. With it empty, the header is absent.

Health routes
- **AC-22**: `GET /auth/health` needs no token. It answers 200 `{ "status": "ok", "checks": { "database": "ok" } }`, or 503 `{ "statusCode": 503, "message": "A health check failed", "error": "Service Unavailable", "code": "HEALTH_CHECK_FAILED", "status": "unavailable", "checks": { "database": "failed" } }` when a `SELECT 1` fails or takes over 2 seconds. It shows no error text from the failure.
- **AC-23**: `GET /vrms/health` follows AC-22 and adds `checks.permissions`: `"ok"` when the permission matrix has loaded, else `"failed"`. Either check failing answers 503.

Whole suite
- **AC-24**: Through the new gateway, the real stack still logs in through the portal, refreshes a VRMS session, and uploads a 25 MB attachment.
- **AC-25**: `sh scripts/clone-all.sh vmms` (also `vrms`, `bms`) clones the shared repos (`welinc-auth`, `welinc-web-portal`) plus that group's repos: `vrms` is `welinc-web-vrms` and `welinc-backend-vrms`; `vmms` is `welinc-web-vmms`, `welinc-backend-vmms`, `welinc-backend-vmms-analytics-ai` and `welinc-mobile-vrms_vmms`; `bms` is `welinc-web-bms`, `welinc-backend-bms` and `welinc-backend-bms-analytics-ai`. With no argument it clones everything, as today. An unknown group prints the usage and exits with an error.
- **AC-26**: The README is the one setup page: `docs/integration/setup-guide.md` is merged into it and removed, and nothing links to it except specs written before. The README's repos table lists every service in contract section 2 with its port, its plug in steps describe `infra/gateway/`, `infra/gateway/README.md` explains the routes, settings and how to add one, `docs/context/suite-overview.md` names the new config home, and the gateway line in `welinc-backend-vrms/src/modules/attachments/AGENTS.md` points to it with no `/repairs`.
- **AC-27**: Contract 0001 sections 2, 3, 11, 12 and 14 carry the amendments listed in the Build plan, as contract version 3.
- **AC-28**: `sh scripts/setup.sh <group>` takes a fresh clone of the workspace to a running, seeded stack (repos, `.env` files from the examples, signing keys, packages, migrations, seeds), and is safe to run again: it never overwrites a `.env` file or the keys, and never runs the VRMS seed on a database that holds tickets. `sh scripts/start.sh [<group>] [--build]` starts the shared stack before the group's and waits for `/health`, `/auth/health` and, for `vrms`, `/vrms/health` (VMMS and BMS add their `<prefix>/health` wait when they move onto the shared services in S11). `sh scripts/stop.sh` stops every stack and keeps the data. An unknown group prints the usage and exits with an error, and so does a closed Docker Desktop, with a plain message.

## Decision

**Chosen option**: Option 2: one nginx template in `infra/gateway/`, the same for every environment, with routes in small shared snippets.

Keep nginx, move it out of `welinc-auth`, build it as one image configured only by settings, and make every gateway answer JSON.

**Implementation skills**: `docker-patterns` (ask first; `.claude/skills/docker-patterns/`, for the Dockerfile and compose edits) · `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`, for the two health routes) · `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`, for the `SELECT 1`)

## Feature design

**Files** (workspace repo):

| Path | Holds |
|---|---|
| `infra/gateway/Dockerfile` | `FROM nginx:<current stable>-alpine`, pinned to a minor version at build (1.25.2 or later, for the resolver step). Copies `nginx.conf`, the templates and the start check, `RUN chmod +x` on the start check (the image silently skips a script that isn't executable); sets `NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1` |
| `infra/gateway/nginx.conf` | Our own main file, replacing the stock one, whose access log prints query strings: `worker_processes auto`, `error_log /var/log/nginx/error.log crit`, `events`, and an `http` block with `mime.types`, `sendfile on`, `server_tokens off`, `include /etc/nginx/conf.d/*.conf`. No access log here |
| `infra/gateway/templates/default.conf.template` | Everything at `http` level: resolver, maps, rate zone, log format, server, routes. The image's env substitution writes it to `conf.d/default.conf` |
| `infra/gateway/templates/snippets/route.conf.template` | What every route shares: `proxy_pass $upstream`, forwarded headers, the flood limit, CORS, preflight. Lands in `conf.d/snippets/`, which `conf.d/*.conf` doesn't include by itself. Snippets must be templates, because the image only fills in settings under `templates/` |
| `infra/gateway/templates/snippets/error-headers.conf.template` | The headers every gateway error carries |
| `infra/gateway/docker-entrypoint.d/05-check-env.sh` | The settings checks and writing the CORS map (AC-13). Tests for "set but may be empty" with `${VAR+x}` |
| `.gitattributes` (workspace root) | `*.sh text eol=lf`, because `core.autocrlf` is on and a Windows line ending stops the start check from running |
| `infra/gateway/test/` | `compose.yml`, `stub.mjs` (echoes method, path and headers as JSON, `?delay=<ms>`, any body), `check-routes.mjs` |
| `infra/gateway/README.md` | How to add a route, the settings, how to run the test |

Local compose builds the image from `./infra/gateway` and bind mounts `templates/`, so a route edit needs only `docker restart welinc_api_gateway`. The container name stays `welinc_api_gateway`, with no `depends_on`.

**Route table** (contract section 3, minus `/repairs`). Each is a prefix location ending in a slash, so `/vmmsx` can't match:

| Location | Upstream setting | Local value | Body limit | Read timeout |
|---|---|---|---|---|
| `/auth/` and `/uploads/` | `AUTH_UPSTREAM` | `http://auth-service:3001` | 5m | 30s |
| `/vrms/` | `VRMS_UPSTREAM` | `http://vrms-backend:3002` | 26m | 120s |
| `/vmms/analytics/` | `VMMS_ANALYTICS_UPSTREAM` | `http://vmms-analytics:3011` | 1m | 120s |
| `/vmms/` | `VMMS_UPSTREAM` | `http://vmms-backend:3010` | 10m | 60s |
| `/bms/` | `BMS_UPSTREAM` | `http://bms-gateway:3020` | 10m | 60s |

The server is `listen 3000 default_server; server_name _;`, IPv4 only. Every route uses `proxy_connect_timeout 5s`. Each location reads:

```nginx
location /vmms/ {
    client_max_body_size 10m;
    proxy_read_timeout 60s;
    set $upstream ${VMMS_UPSTREAM};
    include /etc/nginx/conf.d/snippets/route.conf;
}
```

Each bare prefix gets an exact location that answers the 404 (`location = /vmms { ... }`), so nginx's automatic 301 to the slash form never fires. `/vmms/analytics` needs one too.

**Gateway answers**, all `application/json` in contract section 11's shape: `{ "statusCode": 502, "message": "<text>", "error": "Bad Gateway", "code": "UPSTREAM_UNAVAILABLE" }`. The server has `error_page 413 @too_large; error_page 429 @rate_limited; error_page 502 @unavailable; error_page 504 @timeout;` (no `=` form). Each named location sets `default_type application/json`, includes `error-headers.conf` and ends in `return <status> '<body>'`. The 404 is a `return` in `location /` and the exact bare prefix locations, set up the same way. `proxy_intercept_errors` stays off, so only errors nginx makes itself go here.

| Status | `code` | `error` | `message` | When |
|---|---|---|---|---|
| 404 | `NOT_FOUND` | Not Found | Unknown path | Outside the route table |
| 413 | `PAYLOAD_TOO_LARGE` | Payload Too Large | Request body is over this route's limit | Body limit |
| 429 | `RATE_LIMITED` | Too Many Requests | Too many requests | Flood limit, plus `Retry-After: 1` |
| 502 | `UPSTREAM_UNAVAILABLE` | Bad Gateway | This service isn't reachable right now | Name doesn't resolve, lookup timed out, or connection refused |
| 504 | `UPSTREAM_TIMEOUT` | Gateway Timeout | This service took too long to answer | Past the route's read timeout, or the 5 s connect timeout |

**Which headers each answer carries** (every `add_header` uses `always`, and values are quoted so an empty one is left out):

| Answer | CORS | `X-Request-Id` | HSTS | `Retry-After` |
|---|---|---|---|---|
| Proxied | Yes, `route.conf` | Yes | Yes | Upstream's own |
| Preflight (the `if` block repeats them) | Yes, plus methods, request headers, max age | Yes | Yes | No |
| Gateway errors and 404 | Yes, `error-headers.conf` | Yes | Yes | 429 only, always 1 |
| `GET /health` | No | Yes | Yes | No |

**CORS values**: methods `GET, POST, PUT, PATCH, DELETE, OPTIONS`; request headers `Authorization, Content-Type, X-Request-Id`; exposed headers `X-Request-Id, Retry-After`; max age 600. Each of these, and the credentials value, comes from a map on `$cors_origin` that is empty for an unlisted origin, so nginx leaves the header out. `X-VMMS-Client` isn't allowed (S11 drops it). `proxy_hide_header` covers `Access-Control-Allow-Origin`, `-Credentials`, `-Methods`, `-Headers`, `-Expose-Headers`, `-Max-Age`, `Vary`, `X-Request-Id` and `Strict-Transport-Security`: the gateway owns those, so a service setting them itself can't break AC-18 or AC-21.

**The resolver, the flood limit and the maps** (at `http` level, except `limit_req`):

```nginx
resolver ${NGINX_LOCAL_RESOLVERS} valid=5s ipv6=off;
resolver_timeout 2s;
limit_req_status 429;
# in route.conf only, so /health and the 404s are never counted:
#   limit_req zone=flood burst=${GATEWAY_RATE_BURST} nodelay;

map $cors_origin $cors_credentials { default "true"; "" ""; }
# the same shape for $cors_methods, $cors_request_headers, $cors_expose_headers, $cors_max_age

map "${TRUST_EDGE_PROXY}:$http_x_forwarded_for" $client_addr {
    default $remote_addr;
    "~^1:(?:.*,)?\s*(?<last>[^,\s]+)\s*$" $last;
}
map "${TRUST_EDGE_PROXY}:$http_x_forwarded_proto" $forwarded_proto {
    default $scheme;
    "~^1:(?<proto>https?)$" $proto;
}
map $http_x_request_id $gateway_request_id {
    default $request_id;
    "~^[A-Za-z0-9._-]{1,64}$" $http_x_request_id;
}
map $http_origin $cors_origin {
    default "";
    include /etc/nginx/generated/cors-origins.map;
}
limit_req_zone $client_addr zone=flood:10m rate=${GATEWAY_RATE_PER_SECOND}r/s;
```

**Sent upstream**: `Host $proxy_host`; `X-Forwarded-For $client_addr` (a single value, replacing what came in); `X-Forwarded-Proto $forwarded_proto`; `X-Request-Id $gateway_request_id`. `proxy_ssl_server_name on`, for `https` upstreams on Azure.

**Log line** (`log_format ... escape=json`, to the container log): `time` ($time_iso8601), `request_id`, `client` ($client_addr), `method`, `path` ($uri, never `$request_uri`), `status`, `bytes` ($body_bytes_sent), `duration` ($request_time), `upstream` ($upstream_addr), `upstream_status`, `upstream_duration` ($upstream_response_time). `GET /health` isn't logged.

**Health routes**: `GET /auth/health` is a new controller in welinc-auth with no guard (auth's throttler is per route, so it isn't counted). `GET /vrms/health` is a new `@Public()` route under `@Controller('vrms')`, since backend-vrms has no global prefix; the existing root handler stays as it is. Both run `SELECT 1` through Prisma. The 2 seconds only stops the route waiting (a `Promise.race`); Prisma can't cancel the query itself.

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| Route a request | Upstream address | `*_UPSTREAM` settings, from compose locally and Bicep hosted |
| Resolve an upstream | DNS server | `NGINX_LOCAL_RESOLVERS`, set by the nginx image from the container's `/etc/resolv.conf` |
| CORS answer | Allowed origins | `ALLOWED_ORIGINS` (comma separated), written into `generated/cors-origins.map` at start |
| Rate key, `X-Forwarded-For`, log `client` | Real client | `$client_addr`, chosen by `TRUST_EDGE_PROXY` |
| `Retry-After` | 1 | Fixed; one second is the limit's own window |
| Flood limit | Rate and burst | `GATEWAY_RATE_PER_SECOND`, `GATEWAY_RATE_BURST` |
| HSTS | Header value | `GATEWAY_HSTS` |
| Request id | The id | Valid `X-Request-Id` from the caller, else nginx `$request_id` |
| Health answer | Checks | `SELECT 1`; VRMS also `PermissionsService.isReady` |

**Key invariants**:
- Every `add_header` lives in `route.conf` or `error-headers.conf` (plus `/health`'s two and the 429's `Retry-After`), because nginx drops inherited headers from any block that sets its own. A route location must never add one directly. The preflight `if` block repeats its headers on purpose.
- Every upstream goes through a variable and the `resolver`, never a literal in `proxy_pass` and never an `upstream {}` block. This is what lets the gateway start with a system missing.
- `X-Forwarded-For` is never appended to; it always leaves as one value, so a caller can't plant a fake address.
- The container log never holds a query string: the access log uses `$uri`, and `error_log` is at `crit`, because nginx's `error` level lines print the whole request line. The access log's `upstream_status` covers what those lines would have shown.
- The gateway never checks tokens. Authorization stays in each service.

**Security model**: the routes are public by design, and each service does its own auth. `/health`, `/auth/health` and `/vrms/health` answer without a token and reveal only ok or failed. `TRUST_EDGE_PROXY=1` is only safe behind a proxy that appends the real address (Azure's ingress). Locally it stays 0, or a caller could fake their address.

**Configuration required** (settings on the gateway; no secrets among them):
- `AUTH_UPSTREAM`, `VRMS_UPSTREAM`, `VMMS_UPSTREAM`, `VMMS_ANALYTICS_UPSTREAM`, `BMS_UPSTREAM`: upstream addresses, scheme included. Required. Hosted values must be full names, because nginx's resolver ignores search domains.
- `ALLOWED_ORIGINS`: comma separated exact origins. Required. Local: `http://localhost:8000,http://localhost:8001,http://localhost:8002,http://localhost:8003`.
- `TRUST_EDGE_PROXY`: `0` or `1`. Required. 0 locally, 1 hosted.
- `GATEWAY_RATE_PER_SECOND`, `GATEWAY_RATE_BURST`: required; 20 and 40 everywhere to begin with (`limit_req ... burst=${GATEWAY_RATE_BURST} nodelay`).
- `GATEWAY_HSTS`: must be set, may be empty. Empty locally, `max-age=86400` hosted to begin with.

No change to `TRUST_PROXY_HOPS` in the services: 1 locally, 2 hosted, as spec 0002 set it. The single value `X-Forwarded-For` keeps those numbers right.

**Test harness**: run from the workspace root with `node infra/gateway/test/check-routes.mjs` (needs Node 24 and the docker CLI, for compose and logs). `test/compose.yml` has its own project and network name, no `container_name`, no bind mounts on the gateways, and stubs under the real service names and ports.

| Instance | Published port | `TRUST_EDGE_PROXY` | Rate and burst | `GATEWAY_HSTS` | Proves |
|---|---|---|---|---|---|
| `gateway` | 3100 | 0 | 1000 and 1000 | empty | Routes, CORS, errors, limits, AC-15, AC-21 empty |
| `gateway-edge` | 3101 | 1 | 5 and 5 | `max-age=60` | AC-16, AC-19, AC-21 set |
| One off `compose run` of `gateway` with a bad setting, once per rule | None | n/a | n/a | n/a | AC-13: non zero exit and the setting's name in the output |

The stub accepts any body. Over limit checks send a real `Content-Length` and accept the 413 or a connection reset, since nginx closes after answering. Only the 30 s route is timed out live; the rest go through `nginx -T`. AC-24 is manual, in [verify.md](verify.md).

**Critical test scenarios** (all in `check-routes.mjs`):
- Every route reaches the right stub with its path intact, the longest prefix included: **AC-1**, **AC-2**
- Each bare prefix answers the JSON 404, and no stub sees it: **AC-3**
- Stop the `bms-gateway` stub: `/bms/x` answers JSON 502 with CORS, `/vrms/x` still works; start it, `/bms/x` works within 10 seconds of the stub answering: **AC-5**, **AC-11**
- Unlisted origin on a request and a preflight gets no `Access-Control-*` header: **AC-8**, **AC-9**
- `?code=topsecret` while the upstream is down, then search `docker compose logs`: no `topsecret`: **AC-20**
- On `gateway-edge`, two `X-Forwarded-For` client addresses limit separately: **AC-16**, **AC-19**

## Build plan

Tracer Bullet: the thin thread is the real auth and VRMS flow on the new config, then the routes and hardening grow on it, with the test script alongside.

1. [x] The thin thread: `infra/gateway/` (Dockerfile, our `nginx.conf`, start check, template with `/auth/`, `/uploads/` and `/vrms/`, the `route.conf` template), `.gitattributes`, and `docker-compose.shared.yml` switched to it. Prove login, refresh and an upload on the real stack. Confirm the image's local resolver step works under compose, satisfies **AC-14**, **AC-24**
2. [x] The test harness: `test/compose.yml`, `stub.mjs`, `check-routes.mjs`, covering the first routes, satisfies **AC-1**, **AC-14**
3. [x] All routes, no `/repairs`, slash ended prefixes, body limits and timeouts, satisfies **AC-1**, **AC-2**, **AC-6**, **AC-7**, **AC-12**
4. [x] Gateway answers: `/health`, the 404 catch all and bare prefix locations, named error locations, `error-headers.conf`, satisfies **AC-3**, **AC-4**, **AC-5**, **AC-11**
5. [x] CORS finished: the generated map, the settings checks, exposed headers, satisfies **AC-8**, **AC-9**, **AC-10**, **AC-13**
6. [x] Forwarded headers, request id, `Host` from the upstream, satisfies **AC-15**, **AC-16**, **AC-17**, **AC-18**
7. [x] Flood limit, JSON log, `error_log` level, HSTS, satisfies **AC-19**, **AC-20**, **AC-21**
8. [x] `/auth/health` in welinc-auth and `/vrms/health` in backend-vrms, satisfies **AC-22**, **AC-23**
9. [x] `scripts/clone-all.sh` group option, with a line in the setup guide, satisfies **AC-25**
10. [x] Docs: the README as the one setup page (the setup guide merged in and removed), `scripts/setup.sh`, `start.sh` and `stop.sh`, `suite-overview.md`, `infra/gateway/README.md`, the attachments `AGENTS.md` line in backend-vrms, satisfies **AC-26**, **AC-28**
11. [x] Contract 0001 amendments, as version 3, satisfies **AC-27**. Section 2: the Docker service names `vmms-backend`, `vmms-analytics`, `bms-gateway`, which S11's compose files must use. Section 3: drop `/repairs`; locations end in a slash; one template, no separate local config; the gateway's `/health`, 404 and error codes; the flood limit; `X-Forwarded-For` is one value and hops follow `TRUST_PROXY_HOPS`; service logging of `X-Request-Id` moves to a follow up; the CORS header lists. Section 11: the five new codes. Section 12: the flood limit row. Section 14: version 3. Also the headers the gateway hides.
12. [x] Delete `welinc-auth/nginx.conf` through its own PR, last, satisfies **AC-14**

## Migration plan

**Strategy**: hard switch, local only. Nothing is hosted yet and VMMS and BMS don't call these routes.

**Phases**:
1. Workspace PR: `infra/gateway/`, compose and docs, on `main`, once `/develop` asks you. Health routes go by PR into `development` in auth and backend-vrms.
2. welinc-auth PR into `development` deletes `nginx.conf`, only after phase 1 is merged and everyone has pulled it. Until S11 only the shared services owner runs the shared stack, so "everyone" means that person's machines: merge the workspace PR, run `git pull` and `sh scripts/start.sh vrms --build` on each machine, confirm `curl localhost:3000/health` answers, then open this PR. Anyone who pulls the deletion while still on the old compose would have Docker create a folder named `nginx.conf` in its place.

Everyone runs `docker compose -f docker-compose.shared.yml up -d --build` once after pulling.

**Rollback**: before phase 2, revert the workspace commit; `welinc-auth/nginx.conf` still exists. After phase 2, revert both.

**Risks**: `/develop` relies on the nginx image's resolver step, which task 1 proves first. Docker Desktop was off when this was written, so it hasn't been run on your machine.

## Consequences

**Positive**:
- A system that isn't running breaks only its own routes, with an answer apps can read.
- Local and hosted can't drift, and a new route is five lines.
- S11 can start from routes that are already proven.

**Negative / tradeoffs**:
- The flood limit counts per gateway replica, so with 2 replicas the real limit is up to twice the setting. Acceptable for a flood guard.
- A garage behind one address shares one flood allowance. Settings can raise it without a rebuild.
- `error_log` at `crit` hides nginx's own detail on upstream failures. The access log's `upstream_status` and `upstream` are what you debug from.
- Until S11, the `/vmms` and `/bms` routes answer 502 even when those groups run their systems, since their ports differ.
- A hosted setting (`TRUST_EDGE_PROXY`) rests on Azure's ingress appending the real address. It can only be proven on staging.

**Neutral**:
- `/uploads/` and `/auth/` move from nginx's default 1 MB limit to the contract's 5 MB.
- A bare prefix such as `/vrms` now answers 404. Nothing calls one today.

## Follow-up

- [ ] Update VRMS spec 0008 (hosting) through `/architect`, before feature 26's remaining milestones: image from `infra/gateway/Dockerfile`, the new settings, no `/repairs`, `/auth/health` and `/vrms/health` as probes, the gateway's `/health` for its own smoke check.
- [ ] On staging, confirm the real client address reaches `req.ip` with `TRUST_EDGE_PROXY=1` and `TRUST_PROXY_HOPS=2`, using two different client addresses. Check whether Azure's address entry carries a port (it would make the flood key per connection, needing the port stripped in the map), and what a stopped or scaled to zero Container App answers through the gateway. Raise `GATEWAY_HSTS` to a year once the domain is stable.
- [ ] S11 migration guide: use the service names from contract section 2; VMMS drops `X-VMMS-Client` and calls analytics through `/vmms/analytics`; BMS web moves from 5173 to 8003; VMMS and BMS add `<prefix>/health`; VMMS's `/uploads/` static route moves under `/vmms/` so it doesn't collide with auth's.
- [ ] Service logging of `X-Request-Id` (auth, backend-vrms, then the others).
- [ ] At S9's merge, `/sync` owes:
  - root `AGENTS.md`: the shared services table still says the gateway config is in `welinc-auth/nginx.conf`; it is `infra/gateway/`. Mention `scripts/setup.sh`, `start.sh` and `stop.sh` as the way to run the stack.
  - `agents/vrms/AGENTS.md`: the gateway routes still list `/repairs`; it is `/vrms/` only. The Commands block can use `sh scripts/start.sh vrms`.
  - `welinc-auth/AGENTS.md`: the `nginx.conf` row and its gotcha (once phase 2 deletes the file).
  - `docs/integration/shared-repo-changes.md`: an S9 row (the gateway moved to `infra/gateway/`, JSON errors, health routes, contract version 3).
  - `docs/context/vrms/setup.md`: much of it now repeats the README; trim it to the VRMS only notes.
- [ ] Run `check-routes.mjs` in CI when the gateway workflow arrives with spec 0008.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
