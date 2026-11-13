# Move VMMS onto the shared services

The VMMS checklist for [suite spec 0014](../specs/_root/0014-move-vmms-bms-shared-services/index.md). When you finish it, VMMS has no login of its own: people sign in once at the portal, welinc-auth issues every token, and VMMS checks them the way VRMS does. You copy VRMS's code instead of writing your own, and a checker script tells you when you're done.

You change only your own repos: `welinc-backend-vmms`, `welinc-backend-vmms-analytics-ai`, `welinc-web-vmms` and `welinc-mobile-vrms_vmms`. Nothing in welinc-auth, the portal or the gateway needs a change from you. If something there looks wrong, tell Samuel.

## Before you start

- Work on one branch per repo (`feat/shared-services`), from `development`. Merge all four together at the end: the move is a hard switch, so the old login and the new one never run side by side.
- No data is moved. Every VMMS database is reseeded from the suite's seed people, because no deployment holds real users.
- Don't run `seed:clients` or `setup.sh vmms` against the shared stack until you start step 1: before that, your old login still runs.
- Read [web-login.md](web-login.md) once before you start. It explains the session routes, which are most of the work.

## What changes in one table

| Today | After the move |
|---|---|
| VMMS signs its own HS256 tokens with `JWT_SECRET` | welinc-auth signs ES256 tokens; VMMS checks them with welinc-auth's published keys |
| `users`, `user_roles`, `refresh_tokens`, `login_activities`, `password_reset_tokens` | gone; people are welinc-auth ids (`sub`) |
| `/auth/*` and `/users*` routes in VMMS | gone; the portal signs in, the portal admin manages people |
| Web app keeps the token in `localStorage` | the token lives in memory; a HttpOnly cookie on `/vmms/session` holds the refresh token |
| The mobile app sends `X-VMMS-Client` and checks roles itself | `/auth/mobile/login` with `clientId: vmms-mobile`; welinc-auth decides who may use the app |
| Analytics asks VMMS `/auth/me` | analytics checks the token itself |
| BMS reads trucks from the old `welinc_db` | BMS reads them from your new fleet API |

**Who uses what:** the VMMS web app admits only Admin and Operations. Mechanics and Chief Mechanics use the phone app (`vmms-mobile`). welinc-auth enforces this, so you don't check roles for it anywhere. A mechanic who opens the web app lands on the portal's "use the mobile app" page.

## Checklist

Tick these in order. Each links the guide that already explains it.

### 1. Stack and keys

- [ ] Add `docker-compose.vmms.yml` at the workspace root from the template at the end of this guide (service names, ports and `welinc-network` filled in). Open a pull request for it into the workspace `main`.
- [ ] Copy `.env.example` to `.env` in `welinc-backend-vmms` and `welinc-backend-vmms-analytics-ai` (setup does this for you). The names are in step 2.
- [ ] Run `sh scripts/setup.sh vmms`. Once the compose file exists it makes VMMS's client key (`npm run keys:client -- vmms ...` in welinc-auth, private key into `welinc-backend-vmms/.env`, public key into welinc-auth's `.env`), registers it, starts your stack, runs each service's migrations and seed, and waits for your health routes. It never prints a key.
- [ ] Each service's `npm run seed` must keep data that is already there (setup runs it on every rerun). Skip when your tables hold rows, the way VRMS's setup does.

### 2. Environment

- [ ] Backend names (contract 0001 [section 15](../specs/_root/0001-shared-services-contract/index.md#15-configuration)): `AUTH_ISSUER`, `AUTH_JWKS_URL`, `AUTH_INTERNAL_URL`, `AUTH_CLIENT_ID=vmms`, `AUTH_CLIENT_PRIVATE_KEY` (secret), `WEB_APP_URL`, `PORTAL_URL`, `AUTH_PUBLIC_URL`, `API_PUBLIC_URL`, `SESSION_COOKIE_SECURE`, `TRUST_PROXY_HOPS`, `PORT=3010`.
- [ ] Remove `JWT_SECRET`, `JWT_ACCESS_EXPIRY`, `JWT_REFRESH_EXPIRY` and every `SEMAPHORE_*`.
- [ ] Analytics: `AUTH_ISSUER`, `AUTH_JWKS_URL`, `AUTH_INTERNAL_URL`, `VMMS_API_BASE_URL` (internal, `http://vmms-backend:3010/vmms`), `PORT=3011`.
- [ ] Web app: `VITE_API_BASE_URL` and `VITE_PORTAL_URL` only. `VITE_ANALYTICS_API_URL` goes: analytics is `<VITE_API_BASE_URL>/vmms/analytics/`.
- [ ] Mobile: `EXPO_PUBLIC_API_BASE_URL`, the gateway (your computer's LAN address locally, so a phone can reach it).
- [ ] Every name in `.env.example`, never a value.

### 3. Backend: prefix, health and token check

- [ ] Global prefix `vmms` (`app.setGlobalPrefix('vmms')`), port 3010, `trust proxy` from `TRUST_PROXY_HOPS`, `cookie-parser`.
- [ ] `GET /vmms/health`, public, answering `{ status: 'ok', checks: { database: 'ok' } }` and 503 `HEALTH_CHECK_FAILED` when a check fails. Copy `welinc-backend-vrms/src/health/`.
- [ ] Copy `welinc-backend-vrms/src/auth/verify/` whole, tests included, and follow its [README](../../welinc-backend-vrms/src/auth/verify/README.md) (set `SERVICE_AUDIENCE` to `VMMS`, `jose` 6, the Jest setting).
- [ ] Copy `welinc-backend-vrms/src/auth/account-check.ts` (the 30 s session check) and use `src/auth/guards/jwt-auth.guard.ts` as the model for your guard: `checkPerson`, then the account check, roles from the token. Rename `VRMS` to `VMMS` in both.
- [ ] Delete the auth module, the `/users` controller, `client-platform.ts`, the phone and Semaphore code, and every log line that prints an OTP or a password.

### 4. Backend: session routes

- [ ] Copy `welinc-backend-vrms/src/session/` and rename the prefix: routes under `/vmms/session/*`, cookies `vmms_rt` and `vmms_login_<state prefix>` on path `/vmms/session`, callback `<API_PUBLIC_URL>/vmms/session/callback`, and the `system` value in the callback's portal errors `VMMS` (upper case). The `APP_NOT_ALLOWED` handling is already in there: keep it. [web-login.md, Backend](web-login.md#backend-copy-the-vrms-session-folder) has the details.

### 5. Backend: people and data

- [ ] Drop `users`, `user_roles`, `refresh_tokens`, `login_activities` and `password_reset_tokens`, with the foreign keys from `notifications`, `maintenance_notifications`, `mechanics` and `maintenance_schedules`. Every user id column stays as a plain uuid holding a welinc-auth id.
- [ ] Copy the VRMS directory reader (`welinc-backend-vrms/src/modules/vrms/directory/`) with its own `directory_sync_state` table, and feed your `mechanics` rows from it (`user_id` unique). The client `vmms` already holds `directory.read`.
- [ ] Erasure: when the feed says `erased: true`, every copied name becomes `Deleted user` and every copied email `deleted-<id>@erased.invalid`, `actorEmail` on your audit tables included. Copy `erasure-rewrite.ts` and see [account-screens.md, After an erasure](account-screens.md#after-an-erasure).
- [ ] Seed: a byte for byte copy of welinc-auth's `people.json`, checked with `npm --prefix welinc-auth run seed:check -- welinc-backend-vmms/prisma/seeds/people.json`. Create no users. See [seed-accounts.md, For VMMS and BMS](seed-accounts.md#for-vmms-and-bms-in-s11-not-before).
- [ ] Pick lists skip `temporaryRoles` ([account-screens.md, Temporary roles](account-screens.md#temporary-roles-in-pick-lists)).
- [ ] Profile pictures move to welinc-auth's picture route (`POST /auth/profile/picture`).

### 6. Backend: the fleet API

- [ ] Serve `GET /vmms/fleet/vehicles`, `GET /vmms/fleet/vehicles/:id` and `GET /vmms/fleet/garages` for BMS, exactly as [fleet-api.md](fleet-api.md) says, with `@ServiceRoute('fleet.read')`.
- [ ] A unit test that a service token without `fleet.read` answers 403 `FORBIDDEN` (the checker can't make one).

### 7. Analytics

- [ ] Global prefix `vmms/analytics`, port 3011, Docker service `vmms-analytics`, `GET /vmms/analytics/health`.
- [ ] Check user tokens yourself (`aud: VMMS`, the session check, roles from the token) with the copied `token-verifier.ts`, `key-set.ts`, `guards.ts`, `errors.ts` and `account-check.ts`. Analytics never calls welinc-auth as a client, so it needs no client key: build the verifier without `AuthVerifyModule`'s assertion signer, or give it the module and skip the key settings it doesn't use.
- [ ] Never call a VMMS `/auth/me`. The "assigned" rule keeps calling VMMS core with the user's own token.

### 8. Web app

- [ ] The boot sequence, the in memory token, Switch system and sign out to `<portal>/login?reason=logout`: [web-login.md](web-login.md#web-app-the-boot-sequence). Copy `welinc-web-vrms/src/lib/session/`.
- [ ] Remove the `?token=` intake and the VRMS link (Switch system replaces it; no token in a URL). See [Remove the old handoff](web-login.md#remove-the-old-handoff).
- [ ] Delete the Users page; the menu item opens `<portal>/admin/people?system=VMMS`. Handle `ADMIN_CODE_REQUIRED` ([account-screens.md, Admin pages](account-screens.md#admin-pages-move-to-the-portal)).
- [ ] The profile page uses welinc-auth's routes: [account-screens.md, VMMS](account-screens.md#vmms) and [account-screens.md, Account deletion](account-screens.md#account-deletion). No phone verification.
- [ ] The audit page shows sign in events from `/auth/activity` to VMMS Admins only; other roles see the business rows only ([account-screens.md, Activity](account-screens.md#activity)).
- [ ] Port 8002.

### 9. Mobile app

- [ ] Sign in through `POST /auth/mobile/login` with `clientId: vmms-mobile`, and show the code screen for `EMAIL_VERIFICATION_REQUIRED` (contract 0001 [section 8](../specs/_root/0001-shared-services-contract/index.md#8-mobile-login-vmms-mobile)).
- [ ] Refresh through `POST /auth/token` (store the new refresh token each time: it rotates), log out with `{ refreshToken, clientId }`.
- [ ] Show the `APP_NOT_ALLOWED` message as welinc-auth gives it.
- [ ] Call the API at `<api>/vmms/`. Remove `X-VMMS-Client` and `getMobileAccessRole`.
- [ ] The VRMS tab is not part of this move (scope feature 48).

### 10. Prove it

- [ ] `node scripts/check-system.mjs vmms` from the workspace root, with your stack running. Every line must say `ok`. It checks:
  - **login**: `/vmms/health`; a protected route refusing no token, a tampered token and a VRMS token; `session/start`, the callback cookie, the CSRF check, refresh, logout and the 31 s session end; `vmms.mech@` landing on the `APP_NOT_ALLOWED` page on the web and signing in on the phone app; analytics health and its token check.
  - **fleet**: the fleet routes refusing no token and a user token, and (once BMS has moved) BMS listing the same plates as VMMS.
  - **static**: a scan of your four repos for leftovers (`JWT_SECRET`, `HS256`, `X-VMMS-Client`, a token in `localStorage` or a URL, `SEMAPHORE_`, calls to `/auth/users`). Each hit prints `file:line`. A line that must stay (a test proving `HS256` is refused, say) ends in `// check-system: allow <reason>`.
- [ ] Run one group at a time while you work: `--static-only`, `--login`, `--fleet`.

### 11. Pull requests and sign off

- [ ] Open one pull request per repo into `development`, with the checker's output pasted in.
- [ ] Your group lead confirms in writing that the checklist is done.
- [ ] Samuel runs the cross system steps (one sign in across three apps, sign out everywhere within 30 s, a deactivation and an erasure reaching VMMS) and ticks VMMS in the scope row. Login done and fleet done are separate ticks, so you can finish login first.

## Compose template

Save as `docker-compose.vmms.yml` at the workspace root. It follows `docker-compose.vrms.yml`. Service names (`vmms-backend`, `vmms-analytics`) and ports are fixed by contract 0001 section 2: the gateway reaches you by them. Container names are the ones `start.sh` prints in its hints. Secrets come from each repo's `.env` (`env_file`); the `environment` block holds none.

```yaml
name: vmms-environment

services:
  vmms-db:
    image: postgres:16
    container_name: welinc_vmms_db
    restart: unless-stopped
    environment:
      POSTGRES_USER: welinc_vmms_user
      POSTGRES_PASSWORD: welinc_vmms_pass
      POSTGRES_DB: welinc_vmms_db
    ports:
      - "5438:5432"
    volumes:
      - vmms_pgdata:/var/lib/postgresql/data
    networks:
      - welinc-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U welinc_vmms_user -d welinc_vmms_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  vmms-backend:
    build:
      context: ./welinc-backend-vmms
      dockerfile: Dockerfile.dev
    container_name: welinc_vmms_backend
    restart: unless-stopped
    ports:
      - "3010:3010"
    volumes:
      - ./welinc-backend-vmms:/app
      - /app/node_modules
    env_file:
      - path: ./welinc-backend-vmms/.env
        required: false
    environment:
      PORT: 3010
      DATABASE_URL: postgresql://welinc_vmms_user:welinc_vmms_pass@vmms-db:5432/welinc_vmms_db?schema=public
      AUTH_ISSUER: http://localhost:3000/auth
      AUTH_JWKS_URL: http://auth-service:3001/auth/.well-known/jwks.json
      AUTH_INTERNAL_URL: http://auth-service:3001
      AUTH_CLIENT_ID: vmms
      CORS_ORIGINS: http://localhost:8000,http://localhost:8002
      WEB_APP_URL: http://localhost:8002
      PORTAL_URL: http://localhost:8000
      AUTH_PUBLIC_URL: http://localhost:3000/auth
      API_PUBLIC_URL: http://localhost:3000
      SESSION_COOKIE_SECURE: "false"
      TRUST_PROXY_HOPS: "1"
      NODE_ENV: development
    depends_on:
      vmms-db:
        condition: service_healthy
    networks:
      - welinc-network

  vmms-analytics:
    build:
      context: ./welinc-backend-vmms-analytics-ai
      dockerfile: Dockerfile.dev
    container_name: welinc_vmms_analytics
    restart: unless-stopped
    ports:
      - "3011:3011"
    volumes:
      - ./welinc-backend-vmms-analytics-ai:/app
      - /app/node_modules
    env_file:
      - path: ./welinc-backend-vmms-analytics-ai/.env
        required: false
    environment:
      PORT: 3011
      AUTH_ISSUER: http://localhost:3000/auth
      AUTH_JWKS_URL: http://auth-service:3001/auth/.well-known/jwks.json
      AUTH_INTERNAL_URL: http://auth-service:3001
      VMMS_API_BASE_URL: http://vmms-backend:3010/vmms
      NODE_ENV: development
    depends_on:
      - vmms-backend
    networks:
      - welinc-network

  web-vmms:
    build:
      context: ./welinc-web-vmms
      dockerfile: Dockerfile.dev
    container_name: welinc_vmms_frontend
    restart: unless-stopped
    ports:
      - "8002:8002"
    volumes:
      - ./welinc-web-vmms:/app
      - /app/node_modules
    environment:
      VITE_API_BASE_URL: http://localhost:3000
      VITE_PORTAL_URL: http://localhost:8000
    networks:
      - welinc-network

volumes:
  vmms_pgdata:

networks:
  welinc-network:
    name: welinc-network
    external: true
```

If your analytics keeps its own database, add it like `vmms-db` on host port 5439 and set its `DATABASE_URL` in the `environment` block.
