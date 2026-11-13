# WeLinc workspace

WeLinc is a fleet suite of three systems, VRMS, VMMS and BMS, built by three groups. All three share one login (auth), one portal and one gateway.

This repo is the starting point. It holds the setup scripts, the Docker files, the gateway and the docs. Each system's code lives in its own `welinc-*` repo, which the setup script clones into this folder for you.

## Start here

You need **Git**, **Docker Desktop** (open and running) and **Node 24**.

### Where to type the commands

Every command in this README goes in a **terminal opened in this folder** (`welinc-workspace`):

| On | Open a terminal like this |
|---|---|
| Windows | **Git Bash**, which comes with Git. In VS Code: Terminal, New Terminal, then pick **Git Bash** from the dropdown next to `+`. Or right click the folder in Explorer and pick **Open Git Bash here**. PowerShell and Command Prompt can't run the `sh` scripts |
| Mac | **Terminal**, or VS Code's terminal |

Type a command, press Enter, and wait until it finishes. Where a command says `vrms`, type **your group** instead: `vrms`, `vmms` or `bms`.

### The first time (once)

```bash
git clone https://github.com/Capstone-WeLinc/welinc-workspace.git
cd welinc-workspace
sh scripts/setup.sh vrms
```

`setup.sh` downloads your group's repos, makes your settings files and keys, installs packages, starts everything, fills the databases with test data, and waits until it all answers. The first run takes a few minutes. When it prints **Setup finished**, open **http://localhost:8000** and sign in, for example as `vrms.admin@welinc.com` with password `admin1234`. All test accounts are in [docs/integration/seed-accounts.md](docs/integration/seed-accounts.md).

### Every day

Start the shared stack **first** (it creates the network your system joins), then yours:

```bash
docker compose -f docker-compose.shared.yml up -d
docker compose -f docker-compose.vrms.yml up -d
```

When you're done, stop them (your data stays):

```bash
docker compose -f docker-compose.vrms.yml stop
docker compose -f docker-compose.shared.yml stop
```

Docker Desktop's start and stop buttons do the same once setup has run: start `auth-infrastructure` (the shared stack) before your group's stack.

## Repositories

| Repo | Group | What it does | Built with | Port | GitHub |
|---|---|---|---|---|---|
| `welinc-auth` | Shared | Login, accounts, roles, tokens | NestJS, Prisma, PostgreSQL | 3001 | [link](https://github.com/Capstone-WeLinc/welinc-auth) |
| `welinc-web-portal` | Shared | The page where everyone signs in and picks a system | React, Vite, Tailwind | 8000 | [link](https://github.com/Capstone-WeLinc/welinc-web-portal) |
| Gateway (`infra/gateway/` here) | Shared | The one address every app calls | Nginx | 3000 | this repo |
| `welinc-backend-vrms` | VRMS | Repair tickets API | NestJS, Prisma, PostgreSQL | 3002 | [link](https://github.com/Capstone-WeLinc/welinc-backend-vrms) |
| `welinc-web-vrms` | VRMS | Repair tickets web app | React, Vite, Tailwind | 8001 | [link](https://github.com/Capstone-WeLinc/welinc-web-vrms) |
| `welinc-backend-vmms` | VMMS | Vehicle maintenance API | NestJS, Prisma, PostgreSQL | 3010 | [link](https://github.com/Capstone-WeLinc/welinc-backend-vmms) |
| `welinc-backend-vmms-analytics-ai` | VMMS | Maintenance analytics and AI | NestJS, Prisma, PostgreSQL | 3011 | [link](https://github.com/Capstone-WeLinc/welinc-backend-vmms-analytics-ai) |
| `welinc-web-vmms` | VMMS | Vehicle maintenance web app | React, Vite, Tailwind | 8002 | [link](https://github.com/Capstone-WeLinc/welinc-web-vmms) |
| `welinc-mobile-vrms_vmms` | VMMS | Mobile app (VRMS joins it later as a tab) | Expo, React Native | | [link](https://github.com/Capstone-WeLinc/welinc-mobile-vrms_vmms) |
| `welinc-backend-bms` | BMS | Booking APIs: `bms-gateway` (3020) in front of the booking, dispatch, completion and analytics services (3021 to 3024) | Node.js, NestJS, Prisma, PostgreSQL | 3020 | [link](https://github.com/Capstone-WeLinc/welinc-backend-bms) |
| `welinc-backend-bms-analytics-ai` | BMS | Booking demand forecast | NestJS, Prisma, PostgreSQL | 3025 | [link](https://github.com/Capstone-WeLinc/welinc-backend-bms-analytics-ai) |
| `welinc-web-bms` | BMS | Booking web app | React, Vite, Tailwind | 8003 | [link](https://github.com/Capstone-WeLinc/welinc-web-bms) |

Other local ports: auth database 5432, VRMS database 5433, VRMS file storage (Azurite) 10000.

VMMS and BMS use these ports once they move onto the shared login (suite row S11). Until then they also run their own way.

## How it fits together

```text
web app ──> gateway (localhost:3000) ──> the right service
```

| Gateway path | Goes to |
|---|---|
| `/auth/...`, `/uploads/...` | `welinc-auth` |
| `/vrms/...` | `welinc-backend-vrms` |
| `/vmms/analytics/...` | `welinc-backend-vmms-analytics-ai` |
| `/vmms/...` | `welinc-backend-vmms` |
| `/bms/...` | `bms-gateway` |

| Rule | Why |
|---|---|
| Apps call only the gateway, never a service's own port | One address everywhere: locally, and later online |
| Everyone signs in on the portal | One account and one login for all three systems |
| Each system has its own database, and never reads another's | Systems can change and deploy without breaking each other |
| A stopped system only breaks its own paths | You only need the shared services plus your own system running |

More detail: [suite overview](docs/context/suite-overview.md), [how an app joins the login](docs/integration/web-login.md), [the gateway](infra/gateway/README.md).

## Commands

Run these from this folder.

| I want to... | Run |
|---|---|
| Start everything | `docker compose -f docker-compose.shared.yml up -d`, then `docker compose -f docker-compose.vrms.yml up -d` |
| Stop everything | `docker compose -f docker-compose.vrms.yml stop`, then `docker compose -f docker-compose.shared.yml stop` |
| Rebuild after a package or Dockerfile change | The two start commands with `--build` at the end |
| See what's running | `docker ps` |
| Read a service's log | `docker logs -f welinc_vrms_backend` |
| Restart one service | `docker restart welinc_vrms_backend` (it keeps the settings it started with) |
| Make a service read its `.env` again | `docker compose -f docker-compose.shared.yml up -d --force-recreate auth-service` (the compose file and service name it belongs to) |
| Check a service is up | `curl localhost:3000/vrms/health` (also `/health` and `/auth/health`) |
| Reset the VRMS test data (**deletes tickets**) | `cd welinc-backend-vrms && npm run seed` |
| Run the gateway tests | `node infra/gateway/test/check-routes.mjs` |

Inside a repo, before you push:

| Check | Command |
|---|---|
| Code style | `npm run lint` |
| Types (web apps) | `npm run typecheck` |
| It builds (backends) | `npm run build` |
| It builds (web apps) | `npm run build:local` (plain `npm run build` is the online build and needs real `https` addresses) |
| Tests | `npm run test` |

### Container names

| Container | What it is |
|---|---|
| `welinc_api_gateway` | Gateway |
| `welinc_auth_service` | Auth |
| `welinc_auth_db` | Auth's database |
| `welinc_portal` | Portal |
| `welinc_vrms_backend`, `welinc_vrms_frontend` | VRMS API and web app |
| `welinc_vrms_db`, `welinc_vrms_azurite` | VRMS database and file storage |

## After you pull

Get your teammates' latest work:

```bash
git pull
for d in welinc-*; do git -C "$d" pull; done
```

Then check what changed:

| If this changed | Run |
|---|---|
| `package.json` | `npm install` in that repo, then the start commands with `--build` |
| `prisma/migrations/` | In that backend: `npx prisma migrate deploy` (in `welinc-auth`: `npm run db:deploy`) |
| A Dockerfile, a compose file or `infra/gateway/` | The start commands with `--build` |
| `.env.example` got a new line | `node scripts/sync-env.mjs` adds it to your `.env` for you (setup does this too) |
| `agents/<group>/` | `node scripts/use-agents.mjs vrms` |

Or just run `sh scripts/setup.sh vrms` again. It's safe, and it does all of this for you.

## Environment files

Each backend has a `.env` file with your local settings and keys. `setup.sh` makes them for you, and when a teammate adds a new setting, running setup again adds it to your `.env` (it never changes a line you already have).

The web apps need no `.env`: they use the `.env.development` file that's already in git.

| File | Holds | Shared in git? |
|---|---|---|
| `.env.example` | The list of settings, with safe sample values | Yes |
| `.env.development` (web apps) | The local addresses the web app calls | Yes |
| `.env` | Your real values and keys | **Never** |
| `.env.local` | Your personal changes | **Never** |

**Every app checks its settings when it starts.** If one is missing or wrong, the app stops and lists each problem by name, for example `AUTH_ISSUER: is required`. It never shows the value. Fix the names it lists (usually by running `sh scripts/setup.sh vrms` again), then start it again. To check without starting the app, run `npm run env:check` in the backend.

Optional extras (mail, AI) don't stop the app. If one is off, the app starts anyway and writes one warning line in its log, which you can read with `docker logs welinc_vrms_backend` or `docker logs welinc_auth_service`.

Online (in production) the check is stricter: every address must use `https` and must not be `localhost`, cookies must be secure, and mail and file storage must be set. A bad setting there stops the deploy instead of breaking the live site.

Optional extras you can add to your `.env`:

| File | Setting | Turns on |
|---|---|---|
| `welinc-auth/.env` | `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` | Real emails for account setup, password reset and sign in codes. Without them, emails are only printed to the log. Mail to the made up seed addresses (`@welinc.com`) is always printed to the log on your machine, never sent |
| `welinc-backend-vrms/.env` | `GEMINI_API_KEY` | VRMS's AI features. Get a key at aistudio.google.com |

Never paste a `.env` value into chat, code or a commit. Settings starting with `VITE_` end up in the browser, so they must never hold a secret.

## What `setup.sh` does

If the script stops with an error, this table shows each step, so you can run the one that failed by hand.

| Step | Command |
|---|---|
| 1. Download your group's repos | `sh scripts/clone-all.sh vrms` |
| 2. Make the `.env` files | `cp welinc-auth/.env.example welinc-auth/.env` (and the same in your backend). If you already have them: `node scripts/sync-env.mjs` adds any new settings |
| 3. Install packages | `npm install` in each repo |
| 4. Make the login keys | `cd welinc-auth && npm run keys:dev` |
| 5. Start the shared services | `docker compose -f docker-compose.shared.yml up -d --build` |
| 6. Fill the auth database | `cd welinc-auth && npm run db:deploy && npm run seed` |
| 7. Start VRMS and fill its database | `docker compose -f docker-compose.vrms.yml up -d --build`, then in `welinc-backend-vrms`: `npx prisma migrate deploy && npm run seed` |
| 8. Wait until it's ready | `curl localhost:3000/auth/health` and `curl localhost:3000/vrms/health` until both answer |

`clone-all.sh` with no group downloads every repo. Only whoever maintains the shared services needs that.

## Scripts

Run them from this folder, in Git Bash on Windows or Terminal on a Mac. Scripts ending in `.sh` start with `sh`, scripts ending in `.mjs` with `node`.

| Command | Who runs it, and when | What it does |
|---|---|---|
| `sh scripts/setup.sh vrms` | Everyone: the first time, and again when something seems off after a pull | Everything to get running (see [The first time](#the-first-time-once)). Safe to run again: it skips what's done and never wipes your data |
| `node scripts/sync-env.mjs` | Everyone, after a pull that changed a `.env.example` (setup runs it for you) | Adds the settings your `.env` is missing, with their sample values. Never changes a line you already have |
| `node scripts/use-agents.mjs vrms` | Only people who use an AI coding tool, once | Turns on your group's AI setup ([AI coding tools](#ai-coding-tools)) |
| `sh scripts/clone-all.sh vrms` | Nobody by hand: setup runs it | Downloads the shared repos plus your group's repos |

## AI coding tools

Each group keeps its AI rules (an `AGENTS.md`), skills and tool settings in `agents/<group>/`. Nothing in there is active until you turn it on:

```bash
node scripts/use-agents.mjs vrms
```

It copies your group's setup into places git ignores: `.claude/skills/`, `.mcp.json`, `.claude/settings.local.json`, and a `CLAUDE.local.md` that loads `agents/<group>/AGENTS.md`. Your AI tool then follows your group's rules, and nobody else's setup loads. Run it again after a pull that changes `agents/<group>/`, then restart your AI tool. If you edit a skill locally, `node scripts/use-agents.mjs vrms --save` copies it back into `agents/<group>/` so you can commit it.

## Adding your system (VMMS and BMS)

Your group's checklist is the one page to follow: [move-vmms.md](docs/integration/move-vmms.md) or [move-bms.md](docs/integration/move-bms.md). It covers the compose file, the token check, the session routes, health and your data. The gateway needs nothing from you: `/vmms/` and `/bms/` already route to your service names.

## Team rules

| Rule | Details |
|---|---|
| Branches | Branch from `development` and open a pull request back into `development`, never `main`. This workspace repo uses `main` |
| Shared parts | `welinc-auth`, `welinc-web-portal` and this repo's shared files affect every group, so change them through a pull request everyone can see |
| Big changes | Anything that touches more than one repo (login, gateway paths, shared data) gets a written spec first, in `docs/specs/_root/` |
| Other groups' code | Read it to understand how things connect, but only change your own group's repos and folders |
| Secrets | Never commit a `.env` file |

## Troubleshooting

| What you see | What to do |
|---|---|
| `Docker isn't running` | Open Docker Desktop and wait until it says it's running |
| `Environment check failed` in a backend's log, and it won't start | The lines under it name each setting that's missing or wrong. Run `sh scripts/setup.sh vrms` again to add new ones, or fix the value in that backend's `.env` |
| `Environment check failed (mode production)` when building a web app | Use `npm run build:local` on your machine. Plain `npm run build` is for the online build |
| `$'\r': command not found` | You ran the script in PowerShell or with Windows line endings. Use Git Bash and pull again |
| `port is already allocated` | Something else uses that port. Run `docker ps` and stop the old one |
| Error `UPSTREAM_UNAVAILABLE` (502) | That service isn't running or is still starting. Wait a moment, or read its log |
| Error `UPSTREAM_TIMEOUT` (504) | The service is too slow or just stopped. Read its log |
| Error `PAYLOAD_TOO_LARGE` (413) | The upload is too big for that path (VRMS 26 MB, VMMS and BMS 10 MB, auth 5 MB) |
| Error `RATE_LIMITED` (429) | Over 20 requests a second. Usually an app stuck in a loop |
| Error `NOT_FOUND` (404) from the gateway | That path isn't routed. Paths look like `/vrms/...` |
| A CORS error in the browser | Your app's address is missing from `ALLOWED_ORIGINS` in `docker-compose.shared.yml` |
| The gateway keeps restarting | A setting is wrong. `docker logs welinc_api_gateway` says which |
| Every request gives 401 | Sign in again through the portal. If it keeps happening, your backend's `AUTH_ISSUER` doesn't match auth's |
| Sent back to the sign in page | You were idle 30 minutes, or signed out in another app |
| Pages are empty or tables are missing | Run `sh scripts/setup.sh vrms` again |
| A container can't find a package | The start commands with `--build` |
| You changed a `.env` and nothing changed | `docker restart` keeps the old settings. Recreate the container: `docker compose -f docker-compose.shared.yml up -d --force-recreate auth-service` |

## Folder map

| Folder or file | What's in it |
|---|---|
| `scripts/` | The scripts listed in [Scripts](#scripts) |
| `infra/gateway/` | The gateway: its settings, paths and tests |
| `docker-compose.shared.yml` | The shared services: auth, gateway, portal |
| `docker-compose.vrms.yml` | VRMS's services (one file per group) |
| `docs/context/` | Background on the suite and each system |
| `docs/integration/` | What VMMS and BMS follow to move onto the shared services: one checklist per group, plus references (web login, account screens, fleet API, test accounts) |
| `docs/scope/` | The plan: what's built and what's next |
| `docs/specs/` | Designs for each feature, before it's built |
| `docs/reviews/` | Code review reports |
| `design.md` | Colors, fonts and UI rules |
| `agents/` | Each group's AI rules and skills |
| `AGENTS.md` | Rules every group's AI tools follow |

## Where to read next

| You want to... | Read |
|---|---|
| Understand the whole suite | [docs/context/suite-overview.md](docs/context/suite-overview.md) |
| Move VMMS or BMS onto the shared services | [move-vmms.md](docs/integration/move-vmms.md) or [move-bms.md](docs/integration/move-bms.md) |
| Find a test account | [docs/integration/seed-accounts.md](docs/integration/seed-accounts.md) |
| Connect your web app to the login | [docs/integration/web-login.md](docs/integration/web-login.md) |
| See what changed in the shared services this term | [docs/context/shared-repo-changes.md](docs/context/shared-repo-changes.md) |
| Add or change a gateway path | [infra/gateway/README.md](infra/gateway/README.md) |
| See the shared rules in full | [Contract 0001](docs/specs/_root/0001-shared-services-contract/index.md) |
| Your group's own notes | `docs/context/<group>/setup.md` ([VRMS](docs/context/vrms/setup.md)) |
