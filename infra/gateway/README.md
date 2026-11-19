# Suite gateway

The one front door every app calls (spec [0008](../../docs/specs/_root/0008-suite-gateway/index.md)). It is nginx, built as one image that runs the same everywhere: locally from `docker-compose.shared.yml`, hosted on Azure. Only the settings change.

The gateway routes and answers; it never checks tokens. Each service does its own auth.

## Files

| Path | What it holds |
|---|---|
| `Dockerfile` | `nginx:1.30-alpine` plus our files |
| `nginx.conf` | Our main file (no access log here, `error_log` at `crit` so query strings never reach the log) |
| `templates/default.conf.template` | Everything else: resolver, maps, flood limit, log format, the routes, the error answers |
| `templates/snippets/route.conf.template` | What every route shares: proxy, forwarded headers, CORS, preflight, flood limit |
| `templates/snippets/error-headers.conf.template` | The headers every gateway error carries |
| `templates/snippets/tunnel.conf.template` | What both public Sentry tunnel routes share (VRMS spec 0025): their own rate limit, CORS, the method checks, and the envelope DSN check |
| `templates/snippets/tunnel-forward.conf.template` | What both internal tunnel locations share: the forward to Sentry and the headers stripped before it |
| `njs/tunnel.js` | The envelope DSN check (njs): forwards a report only when its DSN is the route's own |
| `docker-entrypoint.d/05-check-env.sh` | Refuses to start on a bad setting, naming it, and writes the CORS origin map and the tunnel routes with their DSN parts (`/etc/nginx/generated/monitoring.conf`) |
| `test/` | The test harness: `compose.yml`, `stub.mjs` (also the https Sentry stand in), `check-routes.mjs` (needs `openssl` for that stand in's throwaway cert) |

At start the nginx image fills every `${SETTING}` in `templates/` and writes the result to `/etc/nginx/conf.d/`. Words like `$upstream` or `$uri` are nginx's own variables and stay as they are.

## Routes

| Path | Goes to (setting) | Body limit | Read timeout |
|---|---|---|---|
| `/auth/`, `/uploads/` | `AUTH_UPSTREAM` | 5 MB | 30 s |
| `/vrms/` | `VRMS_UPSTREAM` | 26 MB | 120 s |
| `/vmms/analytics/` | `VMMS_ANALYTICS_UPSTREAM` | 1 MB | 120 s |
| `/vmms/` | `VMMS_UPSTREAM` | 10 MB | 60 s |
| `/bms/` | `BMS_UPSTREAM` | 10 MB | 60 s |

Paths pass through unchanged: each service serves its own prefix. `GET /health` is the gateway's own check. Anything else, including a bare `/vrms` with no slash, answers a JSON 404.

### Sentry tunnel (VRMS spec 0025)

| Path | Goes to | Body limit | Read timeout |
|---|---|---|---|
| `POST /monitoring/vrms-web` | the envelope address of `SENTRY_DSN_VRMS_WEB`, `https://<host>/api/<project id>/envelope/` | 1 MB | 10 s |
| `POST /monitoring/portal` | the envelope address of `SENTRY_DSN_PORTAL` | 1 MB | 10 s |

Exact paths only. The browser SDKs send their crash reports here, so the browser never calls a `sentry.io` host. `OPTIONS` answers 204 with CORS, any method but `POST` a JSON 405 with `Allow: POST, OPTIONS`. Each client gets 1 request a second with a burst of 10 (its own limit, not the flood limit). Sentry gets no `Cookie`, `Authorization`, `Referer`, `X-Request-Id` or client address. With both `SENTRY_DSN_*` settings blank (local) both routes answer the JSON 404.

Sentry files a report under the DSN in the envelope's first line and ignores the project in the address, so the gateway checks that DSN itself (`njs/tunnel.js`). It forwards only when the envelope's header line (within the first 8 KB, uncompressed, one `"dsn"` and no `\u` escape) is JSON whose `dsn` is exactly the route's own DSN. Anything else answers a JSON 403 `TUNNEL_REJECTED` and never reaches Sentry. Each report logs one access line; nothing from the body is logged. `/_tunnel/vrms-web` and `/_tunnel/portal` are internal and answer 404 from outside.

## Add a route

1. Add a setting for the upstream, for example `FOO_UPSTREAM: http://foo-backend:3030`, in `docker-compose.shared.yml`, in `test/compose.yml` (both gateways), in the required list in `05-check-env.sh`, and in the hosted settings.
2. Add the location in `templates/default.conf.template`, next to the others. End the path with a slash, and include the snippet last:

   ```nginx
   location /foo/ {
       client_max_body_size 10m;
       proxy_read_timeout 60s;
       set $upstream ${FOO_UPSTREAM};
       include /etc/nginx/conf.d/snippets/route.conf;
   }
   ```

3. Add `location = /foo { return 404; }` beside the other bare prefixes.
4. Add the route to the checks in `test/check-routes.mjs` and to contract 0001 section 3.
5. `docker restart welinc_api_gateway` (local compose mounts `templates/`, so no rebuild), then run the test.

Two rules keep it working:
- **Never call `add_header` inside a route location.** nginx drops every inherited header from a block that sets its own, so CORS and the request id would vanish. Headers live in the two snippets.
- **Always go through `set $upstream` and the resolver.** Never write a literal address in `proxy_pass` or use an `upstream {}` block. That is what lets the gateway start and keep serving everyone else while one system is missing.

## Settings

All required except the two `SENTRY_DSN_*` ones. None of them is a secret.

| Setting | Local | Hosted | What it does |
|---|---|---|---|
| `AUTH_UPSTREAM`, `VRMS_UPSTREAM`, `VMMS_UPSTREAM`, `VMMS_ANALYTICS_UPSTREAM`, `BMS_UPSTREAM` | `http://<service name>:<port>` | full internal names | Where each route goes: `scheme://host[:port]`, no path, no trailing slash |
| `ALLOWED_ORIGINS` | the four `http://localhost:800x` apps | the deployed web addresses | Exact origins that get CORS answers, comma separated. Never `*` |
| `TRUST_EDGE_PROXY` | `0` | `1` | `1` takes the client address from the last `X-Forwarded-For` entry. Only safe behind a proxy that appends it (Azure's ingress) |
| `GATEWAY_RATE_PER_SECOND`, `GATEWAY_RATE_BURST` | `20`, `40` | `20`, `40` | Flood limit per client address. Preflights and `/health` never count |
| `GATEWAY_HSTS` | empty | `max-age=86400` | The `Strict-Transport-Security` value; empty leaves the header out |
| `SENTRY_DSN_VRMS_WEB`, `SENTRY_DSN_PORTAL` | empty (tunnel off) | the `vrms-web` and `welinc-portal` DSNs (the same values the web builds get as `VITE_SENTRY_DSN`) | The Sentry tunnel (VRMS spec 0025). Optional, but both or neither. Each must be `https://<32 lowercase hex>@o123.ingest.us.sentry.io/456`: no port, password, path or trailing slash |

A bad setting stops the container at start with a line naming it: read it with `docker logs welinc_api_gateway`.

## Answers the gateway makes itself

Each is JSON in the suite error shape (`statusCode`, `message`, `error`, `code`), with CORS headers so the browser can read it, and an `X-Request-Id`.

| Status | `code` | When |
|---|---|---|
| 403 | `TUNNEL_REJECTED` | A Sentry tunnel report whose envelope DSN isn't that route's own |
| 404 | `NOT_FOUND` | The path isn't in the route table |
| 405 | `METHOD_NOT_ALLOWED` | Anything but `POST` or `OPTIONS` on a Sentry tunnel route (with `Allow: POST, OPTIONS`) |
| 413 | `PAYLOAD_TOO_LARGE` | The body is over the route's limit |
| 429 | `RATE_LIMITED` | Over the flood limit (with `Retry-After: 1`), or the tunnel's own limit |
| 502 | `UPSTREAM_UNAVAILABLE` | The service isn't running or its name doesn't resolve |
| 504 | `UPSTREAM_TIMEOUT` | The service took longer than the route's read timeout, or 5 s to connect |

Right after a service stops, its routes answer 504 for up to 5 seconds (nginx still holds the old address), then 502. A service's own errors pass through untouched.

## Logs

One JSON line per request in `docker logs welinc_api_gateway`: time, request id, client, method, path (never the query string), status, bytes, duration, upstream, upstream status and upstream duration. Find one request with its `X-Request-Id`.

## Test

From the workspace root, with Docker running (about a minute; it starts its own copies on ports 3100 and 3101 and removes them afterwards):

```bash
node infra/gateway/test/check-routes.mjs           # add --keep to leave the harness running
```

## Deploys

Staging deploys on every push to `main` that changes this folder (`.github/workflows/deploy-gateway.yml`); production is a manual "Run workflow". Only those commits have a gateway image, so the very first staging deploy (2026-11-19) came from the commit that added this section.
