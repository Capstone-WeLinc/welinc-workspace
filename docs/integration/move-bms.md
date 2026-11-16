# Move BMS onto the shared services

The BMS checklist for [suite spec 0014](../specs/_root/0014-move-vmms-bms-shared-services/index.md). When you finish it, BMS has no login of its own and reads nothing from the old Capstone 1 database (`welinc_db`): people sign in once at the portal, welinc-auth issues every token, every BMS process checks them the way VRMS does, and trucks come from VMMS. You copy VRMS's code instead of writing your own, and a checker script tells you when you're done.

You change only your own repos: `welinc-backend-bms` (all its processes), `welinc-backend-bms-analytics-ai` and `welinc-web-bms`. Nothing in welinc-auth, the portal or the gateway needs a change from you. If something there looks wrong, tell the shared services lead.

## Before you start

- **The first time:** clone the workspace repo, then download your repos with `sh scripts/clone-all.sh bms` (it adds the shared repos and checks yours out on `development`, or your default branch when there is none). Then run `sh scripts/clone-all.sh vrms` too: the VRMS repos are where you copy the login code from, and you only read them, never change them.
- Work on one branch per repo (`feat/shared-services`) from the branch you push to today (`latest-bms-backend`, `latest-bms-frontend`, `main` for analytics), and open the pull requests into `development` (create it from that branch if it doesn't exist yet). Merge all three together at the end: the move is a hard switch.
- No data is moved. Every BMS database is reseeded from the suite's seed people, because no deployment holds real users.
- You can run `sh scripts/setup.sh bms` any time. Until `docker-compose.bms.yml` exists it only starts the shared stack (auth, portal, gateway) and fills auth with the test people; it makes your client key and starts your stack only after step 1 adds the compose file. If your old stack is still running and a port clashes, stop it first.
- Read [web-login.md](web-login.md) once before you start. It explains the session routes, which are most of the login work.
- For the exact inputs, replies and error codes of every welinc-auth route, open the API docs: `http://localhost:3000/auth/docs` with the shared stack running (and on staging), or the committed [`docs/openapi.json`](https://github.com/Capstone-WeLinc/welinc-auth/blob/development/docs/openapi.json) in welinc-auth. The contract ([suite spec 0001](../specs/_root/0001-shared-services-contract/index.md)) still wins on behavior; tell Samuel when the two disagree.
- The trucks part depends on VMMS serving the [fleet API](fleet-api.md). You can finish login first (a separate tick) and the fleet part when VMMS has it.

### Tools and versions

Set these first, on your machine and in every repo you change. Nothing else needs upgrading.

| What | Version | Where |
|---|---|---|
| Node | 24 | install Node 24; `.nvmrc` with `24`; `"engines": { "node": "24.x" }` in each backend's `package.json`; every Dockerfile `FROM node:24-alpine` (BMS has no Dockerfiles yet: step 1 adds them) |
| Package manager | npm | commit `package-lock.json`; no yarn or pnpm lock files |
| NestJS, Prisma | 11, 7 | you already use these; keep them |
| React, Vite, Tailwind (web app) | keep yours | the login move doesn't need an upgrade: the session code you copy is plain TypeScript |
| New packages | `jose` 6, `cookie-parser`, `@nestjs/config` | add them where you copy VRMS's `src/auth/verify/` and `src/session/` |

On Windows, type every command in **Git Bash** (the workspace [README](../../README.md#where-to-type-the-commands) shows how).

## What changes in one table

| Today | After the move |
|---|---|
| `bms-gateway` is a plain Node server with `auth-integration.mjs` reading the auth database | `bms-gateway` is NestJS, holds the BMS session routes, and reads no database |
| Processes share `JWT_SECRET` and check HS256 tokens | every process checks welinc-auth's ES256 tokens with its published keys |
| The web app has a password form, `jwt-decode` and a token in `localStorage` | the portal signs in; the token lives in memory; a HttpOnly cookie on `/bms/session` holds the refresh token |
| Drivers, vehicles and garages come from `welinc_db` | drivers live in dispatch's database; vehicles and garages come from VMMS's fleet API |
| Analytics reads `welinc_db` | analytics has its own read model database |
| The tracking link secret falls back to `JWT_SECRET` | `CUSTOMER_TRACKING_SECRET`, required, no fallback |

**Who uses what:** the BMS web app admits Admin, Customer Support and Operations. Drivers and helpers use the BMS phone app (`bms-mobile`, not released yet). welinc-auth enforces this, so a driver who opens the web app lands on the portal's "coming to the mobile app" page. Don't check roles for it anywhere.

**One identity:** BMS is one client, `bms`, with one private key in `welinc-backend-bms/.env`. Every process that calls welinc-auth or VMMS (the gateway, booking, dispatch) reads it from there and signs its own client assertions. Never log it.

## Ports and names

| Process | Docker service | Port |
|---|---|---|
| `bms-gateway` | `bms-gateway` (fixed: the suite gateway reaches you by it) | 3020 |
| `bms-booking-service` | `bms-booking` | 3021 |
| `bms-dispatch-service` | `bms-dispatch` | 3022 |
| `bms-completion-service` | `bms-completion` | 3023 |
| `bms-analytics-projection` | `bms-analytics-projection` | 3024 |
| `welinc-backend-bms-analytics-ai` | `bms-analytics` | 3025 |
| `welinc-web-bms` | `web-bms` | 8003 |

The browser reaches BMS only at `<gateway>/bms/...`. These public paths are fixed (the checker uses them): `/bms/health`, `/bms/session/*`, `/bms/booking`, `/bms/config/vehicles`, `/bms/dispatch/assignments`, `/bms/reports`. Whether `bms-gateway` strips `/bms` before it forwards is your call.

## Checklist

### 1. Stack and keys

- [ ] Add `docker-compose.bms.yml` at the workspace root from the template at the end of this guide. Open a pull request for it into the workspace `main`.
- [ ] A Dockerfile for every process on Node 24 (`Dockerfile.dev`, like `welinc-backend-vrms`'s).
- [ ] Add `welinc-backend-bms/.env.example` with the names every process shares (step 2). Setup copies it to `.env`.
- [ ] Run `sh scripts/setup.sh bms`. Once the compose file exists it makes BMS's client key (`npm run keys:client -- bms ...` in welinc-auth, private key into `welinc-backend-bms/.env`, public key into welinc-auth's `.env`), registers it, starts your stack, runs each service's migrations and seed, and waits for `/bms/health`. It never prints a key.
- [ ] Each service's `npm run seed` must keep data that is already there (setup runs it on every rerun).
- [ ] Make it hosting ready in the same pull requests: the checklist in [hosting.md](hosting.md#make-it-hosting-ready) (a `Dockerfile.prod`, the pool setting, no lasting files on local disk, every table and trigger from a migration). Added 2026-11-14.

### 2. Environment

- [ ] `welinc-backend-bms/.env` (secrets, shared by the processes through `env_file`): `AUTH_CLIENT_PRIVATE_KEY`, `CUSTOMER_TRACKING_SECRET`, `BMS_INTERNAL_SERVICE_KEY`.
- [ ] Every process that serves people: `AUTH_ISSUER`, `AUTH_JWKS_URL`, `AUTH_INTERNAL_URL`.
- [ ] The gateway also: `AUTH_CLIENT_ID=bms`, `WEB_APP_URL`, `PORTAL_URL`, `AUTH_PUBLIC_URL`, `API_PUBLIC_URL`, `SESSION_COOKIE_SECURE`, `TRUST_PROXY_HOPS`, and the internal address of each process.
- [ ] Booking and dispatch also: `AUTH_CLIENT_ID=bms`. Dispatch also `VMMS_INTERNAL_URL` (`http://vmms-backend:3010`).
- [ ] Remove `JWT_SECRET`, `JWT_ACCESS_EXPIRY`, `AUTH_DATABASE_URL`, `BMS_PARTNER_DATABASE_URL`, `PARTNER_BRIDGE_URL` and the analytics `MYSQL_*` names.
- [ ] Web app: `VITE_API_BASE_URL` (replaces `VITE_BMS_API_BASE_URL`) and `VITE_PORTAL_URL` for the API and login. `VITE_GOOGLE_MAPS_API_KEY` may stay: it is a browser key, so restrict it to your web addresses in Google Cloud.
- [ ] Every name in `.env.example`, never a value. Contract 0001 [section 15](../specs/_root/0001-shared-services-contract/index.md#15-configuration) has the meanings.

### 3. The BMS gateway in NestJS

- [ ] Port `bms-gateway` to NestJS on 3020, listening on all interfaces, everything under `/bms`, `trust proxy` from `TRUST_PROXY_HOPS`, `cookie-parser`.
- [ ] Keep the `owner()` route table and the raw proxy loop. Turn Nest's body parser off on proxied routes, stream bodies as they are, and cap them at 10 MB (the suite gateway's limit for `/bms/`). Keep `X-Request-Id`.
- [ ] Add analytics to the route table: `/bms/reports` and the forecast routes to `bms-analytics` on 3025.
- [ ] Forward no `/auth/*` path: the web app calls welinc-auth through the suite gateway. Delete `auth-integration.mjs` and its test, and any database code.
- [ ] Forward the user's bearer token unchanged to every process.
- [ ] `GET /bms/health`, public: `{ status: 'ok', checks: { ... } }`, 503 `HEALTH_CHECK_FAILED` when a check fails. Copy `welinc-backend-vrms/src/health/`.
- [ ] **Fallback** if the port can't land in time: the booking service hosts the session routes and `/bms/health` instead, and `bms-gateway` stays a plain proxy. Tell the shared services lead before you take it.

### 4. Token check in every process

- [ ] Copy `welinc-backend-vrms/src/auth/verify/` whole, tests included, into each process that serves people (gateway, booking, dispatch, completion, `welinc-backend-bms-analytics-ai`), and follow its [README](../../welinc-backend-vrms/src/auth/verify/README.md) (`SERVICE_AUDIENCE` `BMS`, `jose` 6, the Jest setting).
- [ ] Copy `welinc-backend-vrms/src/auth/account-check.ts` (the 30 s session check) and use `src/auth/guards/jwt-auth.guard.ts` as the model: `checkPerson`, then the account check, roles from the token.
- [ ] The internal service key between BMS processes stays your business.

### 5. Session routes (in the gateway)

- [ ] Copy `welinc-backend-vrms/src/session/` and rename the prefix: routes under `/bms/session/*`, cookies `bms_rt` and `bms_login_<state prefix>` on path `/bms/session`, callback `<API_PUBLIC_URL>/bms/session/callback`, and the `system` value in the callback's portal errors `BMS`. Keep the `APP_NOT_ALLOWED` handling. [web-login.md, Backend](web-login.md#backend-copy-the-vrms-session-folder) has the details.

### 6. No auth database: names and activity

- [ ] Approval submitter and reviewer names come from `POST /auth/directory/users/lookup` (booking holds the `bms` key and a `directory.read` token). An id in `missing` shows "Unknown user".
- [ ] The admin activity page combines your audit rows (names from the same lookup) with sign in events from `GET /auth/activity` (the BMS Admin's own bearer token, scoped to BMS). Other roles see your rows only. [account-screens.md, BMS](account-screens.md#bms) maps every field.
- [ ] Profile activity is the web app's direct call to `/auth/profile/activity`.
- [ ] Erasure: a crew member whose `user_id` comes back `erased` becomes `Deleted user` in `drivers.name` and `helpers.name`. Copy the VRMS directory reader (`welinc-backend-vrms/src/modules/vrms/directory/`, recommended) or look the linked ids up daily. See [account-screens.md, After an erasure](account-screens.md#after-an-erasure).
- [ ] Pick lists skip `temporaryRoles` ([account-screens.md, Temporary roles](account-screens.md#temporary-roles-in-pick-lists)).
- [ ] `CUSTOMER_TRACKING_SECRET` for tracking links, required at boot, no fallback (contract rule 8).

### 7. Drivers and trucks

- [ ] Move `drivers` from `welinc_db` into dispatch's database next to `helpers`, with the columns in spec 0014's data model plus `user_id uuid null unique`. `helpers` gains the same `user_id`.
- [ ] Seed `user_id` from `people.json`: driver n (`DRV-00n`) is the nth `"group": "driver"` row in file order (ids `...3401` up), helper n (`HLP-00n`) the nth `"group": "helper"` row. The seed fails when your crew counts differ from the manifest's (12 drivers, 20 helpers).
- [ ] Add `vehicle_dispatch_profiles` (dispatch) for the dispatch only fields, keyed by the VMMS `vehicle_id` with no foreign key.
- [ ] Read vehicles and garages from VMMS with a `fleet.read` service token: every rule (30 s list cache, fresh read at assignment, 409 `VEHICLE_UNAVAILABLE`, 503 `FLEET_UNAVAILABLE`, one retry on `TOKEN_EXPIRED`, "Unavailable vehicle") is in [fleet-api.md](fleet-api.md#bms-rules).
- [ ] Two assignments racing for one truck keep dispatch's existing guard: the unique index `dispatch_active_vehicle_slot_key` on `dispatch_assignments (vehicle_id, service_date, dispatch_time)`, which `confirmAssignment` turns from a Prisma `P2002` into a 409. Keep it: `vehicle_id` now holds a VMMS vehicle id.

### 8. Analytics

- [ ] `bms-analytics-projection` writes its read model into `bms-analytics-db`, a database container in `docker-compose.bms.yml` on its own host port (5437, never 5433).
- [ ] `welinc-backend-bms-analytics-ai` reads that database, checks tokens itself (step 4), and runs on 3025 behind `bms-gateway`. It never reads `welinc_db`.
- [ ] Analytics gets trucks, drivers and helpers from dispatch (`DISPATCH_API_URL`, `http://bms-dispatch:3022` in Docker), forwarding the signed in person's token, as the Resource Planning work already does. Dispatch is the only BMS process that calls the [fleet API](fleet-api.md).
- [ ] Remove the `user_activity_logs` mapping from analytics: sign in activity comes from welinc-auth ([account-screens.md, BMS](account-screens.md#bms)).

### 9. Web app

- [ ] No password form: `/login` sends the browser to `/bms/session/start`. Forgot password is the portal's.
- [ ] The boot sequence, the in memory token, Switch system and sign out: [web-login.md](web-login.md#web-app-the-boot-sequence). Copy `welinc-web-vrms/src/lib/session/`. Remove `jwt-decode`, every `localStorage` token and the `/auth/users/:id/password` call.
- [ ] Delete the Users page except crew management, which stays as its own page. The menu item opens `<portal>/admin/people?system=BMS`. Handle `ADMIN_CODE_REQUIRED` ([account-screens.md, Admin pages](account-screens.md#admin-pages-move-to-the-portal)).
- [ ] The profile page uses `reauthToken` and `GET /auth/profile/deletion-request` ([account-screens.md, Account deletion](account-screens.md#account-deletion)).
- [ ] Port 8003, API at `<api>/bms/`.

### 10. People in the seed

- [ ] A byte for byte copy of welinc-auth's `people.json` wherever a BMS seed needs people, checked with `npm --prefix welinc-auth run seed:check -- <your copy>`. Create no users. See [seed-accounts.md, For VMMS and BMS](seed-accounts.md#for-vmms-and-bms-in-s11-not-before).

### 11. Prove it

- [ ] When everything above is ticked, tell the shared services lead. They run `node scripts/check-system.mjs bms` from the workspace root against your stack (and VMMS's, for the fleet group). Every line must say `ok`. It checks:
  - **login**: `/bms/health`; a protected route refusing no token, a tampered token and a VRMS token; `session/start`, the callback cookie, the CSRF check, refresh, logout and the 31 s session end; `driver.ramon@` landing on the `APP_NOT_ALLOWED` page; a 5 MB body to `POST /bms/booking` passing your gateway and answering 400 from booking's validation (a 413 means a body limit below 10 MB somewhere).
  - **fleet**: VMMS's fleet routes refusing no token and a user token, and `GET /bms/config/vehicles` listing the same plates as VMMS.
  - **static**: a scan of your three repos for leftovers (`JWT_SECRET`, `AUTH_DATABASE_URL`, `BMS_PARTNER_DATABASE_URL`, `5433/welinc_db`, `HS256`, `jwt-decode`, a token in `localStorage` or a URL, calls to `/auth/users`). Each hit prints `file:line`. A line that must stay ends in `// check-system: allow <reason>`.
- [ ] While you work you may run `node scripts/check-system.mjs bms --static-only` yourselves: it only scans your repos for leftovers, so it finds old login code early. The full run is the shared services lead's.

### 12. Pull requests and sign off

- [ ] One pull request per repo into `development`. The shared services lead posts the checker's output on them.
- [ ] Your group lead confirms in writing that the checklist is done.
- [ ] The shared services lead runs the cross system steps and ticks BMS in the scope row (login done and fleet done are separate ticks).
- [ ] Once the checker passes, `welinc_db` leaves every BMS setup and the old `welinc-backend` repo is archived on GitHub (read only, history kept).

## Compose template

Save as `docker-compose.bms.yml` at the workspace root. It follows `docker-compose.vrms.yml`. `bms-gateway` and the ports are fixed by contract 0001 section 2; the database host ports keep the ones your `.env.example` files use today (5434 to 5436) plus 5437 for analytics. Secrets come from `welinc-backend-bms/.env` (`env_file`); the `environment` blocks hold none. Fill in the `environment` names your processes already read for their upstream addresses.

```yaml
name: bms-environment

x-auth: &auth
  AUTH_ISSUER: http://localhost:3000/auth
  AUTH_JWKS_URL: http://auth-service:3001/auth/.well-known/jwks.json
  AUTH_INTERNAL_URL: http://auth-service:3001
  NODE_ENV: development

x-db: &db
  image: postgres:16
  restart: unless-stopped
  networks:
    - welinc-network

x-node: &node
  restart: unless-stopped
  env_file:
    - path: ./welinc-backend-bms/.env
      required: false
  networks:
    - welinc-network

services:
  bms-booking-db:
    <<: *db
    container_name: welinc_bms_booking_db
    environment: { POSTGRES_USER: bms_user, POSTGRES_PASSWORD: bms_pass, POSTGRES_DB: bms_booking_db }
    ports: ["5434:5432"]
    volumes: [bms_booking_pgdata:/var/lib/postgresql/data]
    healthcheck: { test: ["CMD-SHELL", "pg_isready -U bms_user -d bms_booking_db"], interval: 10s, timeout: 5s, retries: 5 }

  bms-dispatch-db:
    <<: *db
    container_name: welinc_bms_dispatch_db
    environment: { POSTGRES_USER: bms_user, POSTGRES_PASSWORD: bms_pass, POSTGRES_DB: bms_dispatch_db }
    ports: ["5435:5432"]
    volumes: [bms_dispatch_pgdata:/var/lib/postgresql/data]
    healthcheck: { test: ["CMD-SHELL", "pg_isready -U bms_user -d bms_dispatch_db"], interval: 10s, timeout: 5s, retries: 5 }

  bms-completion-db:
    <<: *db
    container_name: welinc_bms_completion_db
    environment: { POSTGRES_USER: bms_user, POSTGRES_PASSWORD: bms_pass, POSTGRES_DB: bms_completion_db }
    ports: ["5436:5432"]
    volumes: [bms_completion_pgdata:/var/lib/postgresql/data]
    healthcheck: { test: ["CMD-SHELL", "pg_isready -U bms_user -d bms_completion_db"], interval: 10s, timeout: 5s, retries: 5 }

  bms-analytics-db:
    <<: *db
    container_name: welinc_bms_analytics_db
    environment: { POSTGRES_USER: bms_user, POSTGRES_PASSWORD: bms_pass, POSTGRES_DB: bms_analytics_db }
    ports: ["5437:5432"]
    volumes: [bms_analytics_pgdata:/var/lib/postgresql/data]
    healthcheck: { test: ["CMD-SHELL", "pg_isready -U bms_user -d bms_analytics_db"], interval: 10s, timeout: 5s, retries: 5 }

  bms-gateway:
    <<: *node
    build: { context: ./welinc-backend-bms/bms-gateway, dockerfile: Dockerfile.dev }
    container_name: welinc_bms_gateway
    ports: ["3020:3020"]
    volumes: [./welinc-backend-bms/bms-gateway:/app, /app/node_modules]
    environment:
      <<: *auth
      PORT: 3020
      AUTH_CLIENT_ID: bms
      WEB_APP_URL: http://localhost:8003
      PORTAL_URL: http://localhost:8000
      AUTH_PUBLIC_URL: http://localhost:3000/auth
      API_PUBLIC_URL: http://localhost:3000
      SESSION_COOKIE_SECURE: "false"
      TRUST_PROXY_HOPS: "1"
      BOOKING_API_URL: http://bms-booking:3021
      DISPATCH_API_URL: http://bms-dispatch:3022
      COMPLETION_API_URL: http://bms-completion:3023
      ANALYTICS_API_URL: http://bms-analytics:3025
    depends_on: [bms-booking, bms-dispatch, bms-completion, bms-analytics]

  bms-booking:
    <<: *node
    build: { context: ./welinc-backend-bms/bms-booking-service, dockerfile: Dockerfile.dev }
    container_name: welinc_bms_booking
    ports: ["3021:3021"]
    volumes: [./welinc-backend-bms/bms-booking-service:/app, /app/node_modules]
    environment:
      <<: *auth
      PORT: 3021
      AUTH_CLIENT_ID: bms
      DATABASE_URL: postgresql://bms_user:bms_pass@bms-booking-db:5432/bms_booking_db?schema=public
    depends_on: { bms-booking-db: { condition: service_healthy } }

  bms-dispatch:
    <<: *node
    build: { context: ./welinc-backend-bms/bms-dispatch-service, dockerfile: Dockerfile.dev }
    container_name: welinc_bms_dispatch
    ports: ["3022:3022"]
    volumes: [./welinc-backend-bms/bms-dispatch-service:/app, /app/node_modules]
    environment:
      <<: *auth
      PORT: 3022
      AUTH_CLIENT_ID: bms
      VMMS_INTERNAL_URL: http://vmms-backend:3010
      DATABASE_URL: postgresql://bms_user:bms_pass@bms-dispatch-db:5432/bms_dispatch_db?schema=public
    depends_on: { bms-dispatch-db: { condition: service_healthy } }

  bms-completion:
    <<: *node
    build: { context: ./welinc-backend-bms/bms-completion-service, dockerfile: Dockerfile.dev }
    container_name: welinc_bms_completion
    ports: ["3023:3023"]
    volumes: [./welinc-backend-bms/bms-completion-service:/app, /app/node_modules]
    environment:
      <<: *auth
      PORT: 3023
      DATABASE_URL: postgresql://bms_user:bms_pass@bms-completion-db:5432/bms_completion_db?schema=public
    depends_on: { bms-completion-db: { condition: service_healthy } }

  bms-analytics-projection:
    <<: *node
    build: { context: ./welinc-backend-bms/bms-analytics-projection, dockerfile: Dockerfile.dev }
    container_name: welinc_bms_analytics_projection
    ports: ["3024:3024"]
    volumes: [./welinc-backend-bms/bms-analytics-projection:/app, /app/node_modules]
    environment:
      BOOKING_API_URL: http://bms-booking:3021
      DISPATCH_API_URL: http://bms-dispatch:3022
      COMPLETION_API_URL: http://bms-completion:3023
      ANALYTICS_READ_MODEL_DATABASE_URL: postgresql://bms_user:bms_pass@bms-analytics-db:5432/bms_analytics_db
    depends_on: { bms-analytics-db: { condition: service_healthy } }

  bms-analytics:
    <<: *node
    build: { context: ./welinc-backend-bms-analytics-ai, dockerfile: Dockerfile.dev }
    container_name: welinc_bms_analytics
    ports: ["3025:3025"]
    volumes: [./welinc-backend-bms-analytics-ai:/app, /app/node_modules]
    environment:
      <<: *auth
      PORT: 3025
      DATABASE_URL: postgresql://bms_user:bms_pass@bms-analytics-db:5432/bms_analytics_db
      DISPATCH_API_URL: http://bms-dispatch:3022
    depends_on: { bms-analytics-db: { condition: service_healthy } }

  web-bms:
    build: { context: ./welinc-web-bms, dockerfile: Dockerfile.dev }
    container_name: welinc_bms_frontend
    restart: unless-stopped
    ports: ["8003:8003"]
    volumes: [./welinc-web-bms:/app, /app/node_modules]
    environment:
      VITE_API_BASE_URL: http://localhost:3000
      VITE_PORTAL_URL: http://localhost:8000
    networks:
      - welinc-network

volumes:
  bms_booking_pgdata:
  bms_dispatch_pgdata:
  bms_completion_pgdata:
  bms_analytics_pgdata:

networks:
  welinc-network:
    name: welinc-network
    external: true
```

`welinc-backend-bms-analytics-ai` keeps its own `.env` for `GROQ_API_KEY`: add `./welinc-backend-bms-analytics-ai/.env` to that service's `env_file` list.
