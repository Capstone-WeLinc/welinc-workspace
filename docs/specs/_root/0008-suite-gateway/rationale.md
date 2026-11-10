# 0008. Gateway for the whole suite: rationale

## Context

The gateway is nginx, configured by `welinc-auth/nginx.conf`, and it routes only `/auth`, `/vrms` and `/repairs`. Contract 0001 section 3 already fixes the target: the routes, limits, no path rewriting and `infra/gateway/` as the home. What it leaves open is how the config is built, how it fails and how far S9 goes before VMMS and BMS move in S11.

The forces that shaped this:

- Each group runs only the shared services and its own system, so an absent system is the normal case locally, not a fault.
- The same config has to work on Docker locally and on Azure Container Apps later, where DNS, `Host` handling and the proxy chain differ.
- VMMS and BMS can't listen on their contract ports until S11, so their routes have nothing real behind them during S9.
- The current file repeats about 30 lines of CORS and proxy settings in each location, so a new route is easy to get subtly wrong.
- Web apps read errors from the browser. An nginx HTML error has no CORS headers, so the browser reports a CORS failure and hides the real one.

What reading the code found, against the contract:

| Contract says | Code says |
|---|---|
| `/repairs` goes to backend-vrms | No controller serves it. backend-vrms has `vrms/repairs` only, and web-vrms uses `/repairs` only as a browser page path |
| Every upstream answers `<prefix>/health` | Neither `/auth/health` nor `/vrms/health` exists. VRMS's check is at `/`, which the gateway doesn't route |
| Services log `X-Request-Id` on every line | No service reads it |
| Services trust one proxy hop | Spec 0002 already set `TRUST_PROXY_HOPS` to 1 locally and 2 hosted |

No backend uses WebSockets or server sent events, so no upgrade or streaming settings are needed. No service reads the `Host` header, so sending each upstream its own name is safe everywhere.

## Options considered

### Option 1: Fix in place

Add the new routes to `welinc-auth/nginx.conf`, and write the hosted template separately under spec 0008.

**Pros**: smallest change today; nothing moves.

**Cons**: goes against the contract's config home; a suite wide file stays in one repo; two configs to keep in step; each route repeats the CORS block.

### Option 2: One template in `infra/gateway/` (chosen)

nginx stays. One template for every environment, shared snippets, settings for everything that differs, built into one image.

**Pros**: local and hosted can't drift; a route is a few lines; no new technology; the image's own template step does the work.

**Cons**: local needs a build; the template syntax needs care around nginx's `$` variables; one small start script.

### Option 3: Replace nginx with Azure path routing or an API gateway product

Use Container Apps path based routing, or a gateway such as Traefik or Kong.

**Pros**: Azure routing removes one container; products bring rate limiting and dashboards.

**Cons**: Azure routing does nothing locally, so local and hosted would be two systems; a new product is more to learn and operate weeks before the deadline, and solves nothing nginx doesn't.

## Rationale

Option 2 answers the two forces that matter: absent systems and two environments. It stays on the tool the team already runs. The extra files are small, and the repeated CORS block, the part most likely to break, ends up in one place.

Smaller calls, with the runner up:

| Call | Pick | Why | Runner up |
|---|---|---|---|
| Absent system | JSON 502 through the existing variable and resolver pattern | Apps get a readable error, and start up needs nothing to be present | Plain nginx page, which the browser turns into a CORS error |
| Proving `/vmms` and `/bms` | Stub containers and a script | Tests the longest prefix, limits and missing system now, and stays useful through S11 | Reading the config, which proves little |
| Flood limit | 20 a second, burst 40, per client, in settings | Stops a runaway client before it reaches a service; business limits stay in the services | No limit, which leaves VRMS and the others open to a loop bug |
| Real client address | `TRUST_EDGE_PROXY` flag and the last `X-Forwarded-For` entry | Container Apps gives no stable proxy address range to list without a custom network, and the edge appends the true address last | `set_real_ip_from` with an address range, which needs a value that doesn't exist yet |
| `X-Forwarded-For` | One value, replaced | A caller can't plant an address, and it fixes the fake `172.19.0.1` trouble S7 warns about | Appending, which keeps a caller's fake entry |
| Request id | Gateway now, services later | Gives a trace from the browser to a route today; service logging means changing every logger | Doing auth and VRMS now, which puts logger work inside a gateway feature |
| Logging | `$uri` and `error_log crit` | Login codes travel in query strings; nginx's error lines print the whole request line | Default logging, which writes those codes to the log |
| Unknown paths | JSON 404 and a separate `/health` | A typo should look wrong, and the probe should need no upstream | The 200 catch all |
| Hosted scope | Image ready, deploy stays in spec 0008 | Nothing exists on Azure to route to yet | Local only, which risks hidden local assumptions |
| HSTS | Hosted, one day at first | A mistake on a new domain costs a day, not a year | One year now |
| `X-VMMS-Client` | Not allowed | Web versus mobile comes from the client registry now | Allowing it until S11, a system exception in a shared list |
| Docker service names | `vmms-backend`, `vmms-analytics`, `bms-gateway` | Follows `vrms-backend` and the repo name of `bms-gateway` | Container names like `welinc_vmms_backend`, which are less portable between compose and Azure |
| Prefix matching | Locations end in a slash | `/vmmsx` can't match `/vmms` | Regex locations, harder to read and order |
| Health on `/auth` | New small controller | Keeps the auth controllers free of an unrelated route | Adding it to `AuthController` |
