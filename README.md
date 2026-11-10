# WeLinc workspace

The shared workspace for the WeLinc fleet suite (Capstone 2): three systems, VRMS, VMMS and BMS, built by three groups on shared auth, portal and gateway services. This repo holds the setup scripts, the Docker stacks, the gateway and the docs. Each service's code lives in its own `welinc-*` repo, cloned into this folder (this repo ignores them).

## Start here

You need **Git**, **Docker Desktop** and **Node 24**. On Windows, run every command below in **Git Bash** (it comes with Git), not PowerShell.

```bash
git clone https://github.com/Capstone-WeLinc/welinc-workspace.git
cd welinc-workspace
sh scripts/setup.sh vrms          # first time only. Use your group: vrms, vmms or bms
```

`setup.sh` clones your repos, makes the `.env` files and signing keys, installs packages, starts everything, creates the database tables and fills them with test data. It's safe to run again if something stopped halfway.

After that, every day:

```bash
sh scripts/start.sh vrms          # start, and wait until everything answers
sh scripts/stop.sh                # stop everything (your data stays)
```

Then sign in at **http://localhost:8000** with a seed account, for example `vrms.admin@welinc.com` and `admin1234`. Every seed login is in [docs/integration/seed-accounts.md](docs/integration/seed-accounts.md).

Stuck? See [Troubleshooting](#troubleshooting).

## The repos and ports

| Repo or service | Owner | What it is | Port | Gateway path |
|---|---|---|---|---|
| Gateway (`infra/gateway/`) | shared | Nginx, the one front door every app calls | 3000 | |
| `welinc-auth` | shared | NestJS auth service: login, tokens, users and roles | 3001 | `/auth`, `/uploads` |
| `welinc-web-portal` | shared | React portal where everyone signs in | 8000 | |
| `welinc-backend-vrms` | VRMS | NestJS, Prisma and PostgreSQL API | 3002 | `/vrms` |
| `welinc-web-vrms` | VRMS | React, Vite and Tailwind app | 8001 | |
| `welinc-backend-vmms` | VMMS | Backend | 3010 | `/vmms` |
| `welinc-backend-vmms-analytics-ai` | VMMS | Analytics and AI service | 3011 | `/vmms/analytics` |
| `welinc-web-vmms` | VMMS | Web app | 8002 | |
| `welinc-mobile-vrms_vmms` | VMMS | Mobile app | | |
| `bms-gateway` (in `welinc-backend-bms`) | BMS | BMS's own entry, which fans out to its services | 3020 | `/bms` |
| `bms-booking-service`, `bms-dispatch-service`, `bms-completion-service`, `bms-analytics-projection` (in `welinc-backend-bms`) | BMS | BMS services, reached through `bms-gateway` | 3021 to 3024 | |
| `welinc-backend-bms-analytics-ai` | BMS | Analytics and AI service | 3025 | |
| `welinc-web-bms` | BMS | Web app | 8003 | |

Databases and helpers: auth PostgreSQL 5432, auth Redis 6379, VRMS PostgreSQL 5433, Azurite (VRMS file storage) 10000. They are never reached through the gateway.

A new service takes the next free port in its group's block (VRMS 3003 to 3009, VMMS 3012 to 3019, BMS 3026 to 3029) and adds a row here. VMMS and BMS move onto these ports and the shared login in suite row S11; until then they also run their own way.

## How it fits together

```text
browser ──> gateway :3000 ──> /auth/    welinc-auth
                          ──> /vrms/    welinc-backend-vrms
                          ──> /vmms/    welinc-backend-vmms   (/vmms/analytics/ to its analytics service)
                          ──> /bms/     bms-gateway
```

- **Every app calls only the gateway**, never a service's own port. A system that isn't running only breaks its own paths: the gateway answers a JSON 502 there and keeps serving everyone else.
- **Everyone signs in on the portal.** Each system's backend then runs its own session and checks tokens with welinc-auth's published keys. How a web app joins: [docs/integration/web-login.md](docs/integration/web-login.md).
- **Each system owns its database.** No system reads another's; they talk only through APIs.

The bigger picture (the systems, who owns what, the architecture): [docs/context/suite-overview.md](docs/context/suite-overview.md). The gateway's routes, settings and how to add one: [infra/gateway/README.md](infra/gateway/README.md).

## Setup in detail

`setup.sh` does all of this. Read on if it stopped with an error, or to do one step by hand.

### Prerequisites

| Tool | Get it | Check |
|---|---|---|
| Git (includes Git Bash on Windows) | git-scm.com | `git --version` |
| Docker Desktop, running | docker.com | `docker info` |
| Node 24 | `nvm install 24`, then `nvm use 24` (nvm-windows on Windows) | `node -v` shows v24 |

### What `setup.sh` runs

1. **Clone the repos.** `sh scripts/clone-all.sh vrms` clones the shared repos (`welinc-auth`, `welinc-web-portal`) plus your group's, on `development` where it exists. With no group it clones every repo (only the shared services owner needs that).
2. **Make the `.env` files** from the examples, once: `cp welinc-auth/.env.example welinc-auth/.env`, and the same for your backend (`welinc-backend-vrms`). An existing `.env` is never touched.
3. **Install packages:** `npm install` in each repo.
4. **Make the signing keys:** `cd welinc-auth && npm run keys:dev`. It writes welinc-auth's signing key into `welinc-auth/.env` and VRMS's client key into `welinc-backend-vrms/.env`. It refuses to run twice; `--force` replaces the keys and signs everyone out.
5. **Start the shared stack:** `docker compose -f docker-compose.shared.yml up -d --build`. Always first: it creates the `welinc-network` Docker network every system joins.
6. **Auth tables and people:** `cd welinc-auth && npm run db:deploy && npm run seed`. The seed only adds or updates, so it's safe to run again.
7. **Your system.** For VRMS: `docker compose -f docker-compose.vrms.yml up -d --build`, then in `welinc-backend-vrms` run `npx prisma migrate deploy` and `npm run seed`. The VRMS seed **wipes and refills** the tickets, so `setup.sh` only runs it on an empty database.
8. **Wait until it answers:** `sh scripts/start.sh vrms`.

The containers don't run migrations or seeds on their own; that's what steps 6 and 7 are for.

### Environment files

The stack starts without filling anything in: the compose files carry the local settings, and the `.env` files only add keys and optional extras.

| File | Optional variable | What it turns on |
|---|---|---|
| `welinc-auth/.env` | `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` | Real setup and reset emails. Left blank, emails are logged instead. When set, local tests send real mail, so don't trigger those flows casually |
| `welinc-backend-vrms/.env` | `GEMINI_API_KEY` | VRMS AI diagnosis and issue matching. Create a key at aistudio.google.com (Get API key, then Create API key) |

| File | Purpose | Committed? |
|---|---|---|
| `.env.example` | Every variable name with safe placeholders | Yes |
| `.env.development` | Non secret defaults for the web apps | Yes |
| `.env` | Your real values and secrets (backends) | Never |
| `.env.local`, `.env.*.local` | Your personal overrides | Never |

Rules: never commit a `.env` file or paste its values into chat or code. `VITE_*` variables ship to the browser, so never put a secret in one. Add every new variable to `.env.example` in the same change.

### AI coding tools

Load only your own group's rules and skills, once: `node scripts/use-agents.mjs vrms`. It copies `agents/<group>/` into git ignored spots, so it never reaches the other groups. Run it again after a pull that changes your group's folder. See [agents/README.md](agents/README.md).

## Everyday commands

From the workspace root:

```bash
sh scripts/start.sh vrms                 # start and wait (add --build after a Dockerfile or package change)
sh scripts/stop.sh                       # stop everything, keep the data
docker ps                                # what is running
docker logs -f welinc_vrms_backend       # follow one container's log
docker restart welinc_vrms_backend       # restart one container
curl localhost:3000/vrms/health          # is it up? also /health and /auth/health
```

| Container | What it is |
|---|---|
| `welinc_api_gateway` | The gateway |
| `welinc_auth_service`, `welinc_auth_db`, `welinc_auth_redis` | Auth and its database and Redis |
| `welinc_portal` | The portal |
| `welinc_vrms_backend`, `welinc_vrms_frontend`, `welinc_vrms_db`, `welinc_vrms_azurite` | VRMS |

Inside a repo, before you push:

```bash
npm run lint
npm run typecheck     # web apps
npm run build
npm run test          # backends (Jest) and web-vrms (Vitest)
```

Two Docker habits to know:
- Running `npm run build` on your machine in `welinc-auth` or `welinc-backend-vrms` replaces the `dist` folder their container runs from, and the container stops. Restart it: `docker restart welinc_auth_service`.
- After a Prisma schema change, the container keeps its old Prisma client. Run `docker exec welinc_vrms_backend npx prisma generate`, then restart it.

## Update after a pull

When teammates have pushed, bring your copy up to date. The workspace repo is on `main`; each service repo is on `development` (or your own `feat/` branch, which you rebase on `development`).

```bash
git pull --ff-only                                   # this workspace
for d in welinc-*; do                                # every service repo
  [ -d "$d/.git" ] || continue
  git -C "$d" fetch --all --prune
  git -C "$d" switch development 2>/dev/null || true # stay put if the repo has no development branch
  git -C "$d" pull --ff-only
done
```

Then refresh only what changed:

| What changed | Run |
|---|---|
| `package.json` or `package-lock.json` | `npm install` in that repo, then `sh scripts/start.sh vrms --build` |
| `prisma/migrations/` | `npx prisma migrate deploy` in that backend; in `welinc-auth`, `npm run db:deploy` (also syncs the role catalog) |
| Seed files | `npm run seed` in that backend (remember the VRMS seed wipes tickets) |
| A new variable in `.env.example` | Add it to your own `.env` |
| A `Dockerfile`, a compose file or `infra/gateway/` | `sh scripts/start.sh vrms --build` |
| Your group's `agents/<group>/` folder | `node scripts/use-agents.mjs vrms` |

If a container can't find a package after a `package.json` change, rebuild it with a fresh `node_modules` volume: `docker compose -f docker-compose.vrms.yml up -d --build --renew-anon-volumes vrms-backend`.

## Plug a system into the shared stack

1. **Compose file.** Create `docker-compose.<group>.yml` at the root, like `docker-compose.vrms.yml`: its own `name:`, its own database (never auth's), the ports from your block in [The repos and ports](#the-repos-and-ports), the Docker service names from contract 0001 section 2 (`vmms-backend`, `vmms-analytics`, `bms-gateway`), and every service on the shared network:

   ```yaml
   networks:
     welinc-network:
       name: welinc-network
       external: true
   ```

2. **Gateway.** Your routes already exist (`/vmms/`, `/vmms/analytics/`, `/bms/`) and start working as soon as your service runs under the right name and port. A new route is five lines: [infra/gateway/README.md](infra/gateway/README.md).
3. **CORS.** Your web app's address must be in the gateway's `ALLOWED_ORIGINS` (in `docker-compose.shared.yml`; `localhost:8002` and `8003` are already there) and in welinc-auth's `CORS_ORIGINS`.
4. **Login.** Check tokens with welinc-auth's published keys (`/auth/.well-known/jwks.json`), never a shared secret: copy VRMS's `src/auth/verify/`. Point your backend at auth inside Docker as `http://auth-service:3001`, and give your web app `VITE_API_BASE_URL: http://localhost:3000`. Then follow [docs/integration/web-login.md](docs/integration/web-login.md) for the session routes and the boot sequence.
5. **Health.** Add `GET /<prefix>/health` like `/vrms/health`, so `start.sh` and the hosting probes can see your service.

## Working in the shared parts

- **Shared repos** (`welinc-auth`, `welinc-web-portal`): branch from `development`, open a pull request back into `development`, never into `main`. Run lint, build (and test in auth) first; CI runs the same checks.
- **Shared workspace files** (root files, `scripts/`, `infra/`, `docker-compose.shared.yml`, `docs/integration/`, `docs/context/suite-overview.md`): change them through a pull request the other groups can see.
- **One repo at a time.** A change that crosses repos (tokens, gateway routes, shared API shapes) needs a spec first, in `docs/specs/_root/`.
- **Your own system:** your group's repos and folders follow your group's rules (`agents/<group>/AGENTS.md`).

## Troubleshooting

| What you see | What it means and what to do |
|---|---|
| `Docker isn't running` | Start Docker Desktop and wait until it says it's running |
| A script fails with `$'\r': command not found` | Windows line endings. Pull again (`.gitattributes` now keeps scripts on LF), or run `git checkout -- scripts` |
| `port is already allocated` | Something else holds the port. `docker ps`, then stop the old container or dev server |
| JSON 502 `UPSTREAM_UNAVAILABLE` | That service isn't running, or is still starting. `docker ps`, then `docker logs <container>`. Right after a stop you may see a 504 for a few seconds first |
| JSON 504 `UPSTREAM_TIMEOUT` | The service took longer than its route allows (30 s for auth, 60 s VMMS and BMS, 120 s VRMS) |
| JSON 413 `PAYLOAD_TOO_LARGE` | The upload is over the route's limit (5 MB auth, 10 MB VMMS and BMS, 26 MB VRMS). An answer with a different `code`, like VRMS's `FILE_TOO_LARGE`, comes from the service itself |
| JSON 429 `RATE_LIMITED` | More than 20 requests a second from you (bursts of 40 are fine). Usually a request loop in an app |
| JSON 404 `NOT_FOUND` from the gateway | The path isn't routed. Paths start with the prefix and a slash: `/vrms/...`, never `/vrms` alone |
| The browser shows a CORS error | Your app's address is missing from `ALLOWED_ORIGINS` in `docker-compose.shared.yml` |
| The gateway keeps restarting | A setting is wrong: `docker logs welinc_api_gateway` names it |
| Every request answers 401 | The token's audience isn't your system, or your `AUTH_ISSUER` differs from welinc-auth's |
| Your backend can't reach `auth-service` | It isn't on `welinc-network`, or the shared stack isn't running |
| Sent back to the portal sign in | You were idle for 30 minutes, or signed out in another app. Sign in again |
| Tables missing or the app is empty | Run `sh scripts/setup.sh vrms` again: it applies migrations and seeds an empty database |

## What is where

| Path | What it is |
|---|---|
| `scripts/setup.sh`, `start.sh`, `stop.sh` | First time setup, daily start, stop |
| `scripts/clone-all.sh` | Clones the repos (`clone-all.sh <group>` for one group's) |
| `scripts/use-agents.mjs` | Turns on your group's AI setup |
| `infra/gateway/` | The gateway image, its routes and its tests |
| `docker-compose.shared.yml` | The shared stack: auth with its database and Redis, the gateway, the portal |
| `docker-compose.<group>.yml` | One system's stack (only VRMS so far) |
| `docs/context/` | Background: [suite-overview.md](docs/context/suite-overview.md), then one folder per system |
| `docs/integration/` | Reference shared between systems: [seed accounts](docs/integration/seed-accounts.md), [web login](docs/integration/web-login.md), [shared repo changes](docs/integration/shared-repo-changes.md) |
| `docs/scope/` | The living plan; [index.md](docs/scope/index.md) maps each system's |
| `docs/specs/<group>/` | One folder per designed feature; suite wide specs in `docs/specs/_root/` (the shared contract is [0001](docs/specs/_root/0001-shared-services-contract/index.md)) |
| `docs/reviews/<group>/` | Code review reports |
| `design.md` | Suite UI direction and design tokens; each system adds its own in `docs/context/<group>/design.md` |
| `agents/<group>/` | Each group's AI rules, skills and tool settings |
| `AGENTS.md` | Suite rules every group's AI tools share (`CLAUDE.md` imports it) |

Each group's own working notes (branches, CI, how the group works) are in `docs/context/<group>/setup.md`: [VRMS](docs/context/vrms/setup.md).
