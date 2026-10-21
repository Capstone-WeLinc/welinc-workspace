# WeLinc workspace

The workspace for the WeLinc fleet suite (Capstone 2). It holds the specs, scope, design direction and the local Docker stack. The service code lives in separate `welinc-*` repos that you clone next to this one; this repo ignores them.

Our group builds **VRMS** (Vehicle Repair Management System). VMMS and BMS belong to other groups: read them for context, never edit them.

## What is where

| Path | What it is |
|---|---|
| `docs/context/` | Project background, system overview, roles and users, glossary |
| `docs/scope/` | The living plan: epics, features and their status |
| `docs/specs/` | One folder per designed feature (`NNNN-title/`) with its spec and verify steps |
| `design.md` | UI art direction and design tokens for the web apps |
| `docker-compose.*.yml` | The local stack: auth, VRMS and analytics |
| `scripts/clone-all.sh` | Clones every service repo |
| `AGENTS.md` | Project rules and context for AI tools (`CLAUDE.md` imports it) |

## The repos

| Repo | Owner | What it is | Port |
|---|---|---|---|
| `welinc-web-vrms` | us | React, Vite and Tailwind app | 8001 |
| `welinc-backend-vrms` | us | NestJS, Prisma and PostgreSQL API | 3002 |
| `welinc-backend-vrms-analytics-ai` | us | FastAPI: AI triage and analytics | 8020 |
| `welinc-auth` | shared | NestJS auth service (JWT) | 3001 |
| `welinc-web-portal` | shared | SSO portal | 8000 |
| `welinc-web-vmms`, `welinc-backend-vmms`, `welinc-web-bms`, `welinc-backend-bms` | other groups | read only for us | |

An Nginx gateway on port 3000 routes `/auth`, `/vrms`, `/repairs`, `/ai` and `/analytics`.

## Set up

You need Git, Docker Desktop, and Node 24 (use `nvm`; the `.nvmrc` files say 24).

```bash
git clone https://github.com/Capstone-WeLinc/welinc-workspace.git
cd welinc-workspace
sh scripts/clone-all.sh          # clones every service repo next to the workspace files
```

### Environment files

Each repo has a `.env.example`. Copy it to `.env` for the backends and fill in what is blank.

```bash
cp welinc-auth/.env.example welinc-auth/.env
cp welinc-backend-vrms/.env.example welinc-backend-vrms/.env
cp welinc-backend-vrms-analytics-ai/.env.example welinc-backend-vrms-analytics-ai/.env   # add your GEMINI_API_KEY
```

| File | Purpose | Committed? |
|---|---|---|
| `.env.example` | Every variable name with safe placeholders | Yes |
| `.env.development` | Non secret dev defaults for the two web apps (loaded by `npm run dev`) | Yes |
| `.env` | Your real values and secrets (backends) | Never |
| `.env.local`, `.env.*.local` | Your personal overrides | Never |
| `.env.production` | Production values, supplied by the host | Never |

Rules:
- Never commit a `.env` file or paste its values into chat or code.
- `VITE_*` variables ship to the browser. Never put a secret in one.
- Add any new variable to `.env.example` in the same change.
- The web apps work with no setup. Only create `.env.local` to change a default.

### Start the stack

Start auth first: it creates the shared Docker network.

```bash
docker compose -f docker-compose.auth.yml up -d
docker compose -f docker-compose.vrms.yml up -d
docker compose -f docker-compose.analytics.yml up -d
```

The containers do not run database migrations or seeds on start. The first time, run them from each backend repo on your machine (`.env` there points at the Docker databases on localhost):

```bash
cd welinc-auth && npm install && npx prisma migrate deploy && npm run seed
cd ../welinc-backend-vrms && npm install && npx prisma migrate deploy && npm run seed
```

Seed logins for local testing are in `welinc-auth/prisma/seeds/users.seed.ts`.

### Open the apps

| App | URL |
|---|---|
| Portal (sign in here) | http://localhost:8000 |
| VRMS web | http://localhost:8001 |
| Gateway | http://localhost:3000 |

To work on a web app outside Docker: `cd welinc-web-vrms && npm install && npm run dev`.

If a container fails on a missing package after a `package.json` change, rebuild its image and refresh its `node_modules` volume:

```bash
docker compose -f docker-compose.vrms.yml up -d --build --renew-anon-volumes web-vrms
```

## Daily commands

Inside a Node repo:

```bash
npm run lint
npm run typecheck     # web apps
npm run build
npm run test          # NestJS repos only
```

Before calling a task done, run lint, typecheck and build in every repo you touched, and check UI changes in a real browser.

## How we work

- **Branches:** this workspace repo uses `main`. In the service repos, work on short lived branches named `feat/<feature>`, one per feature. The long lived branch differs per repo (for example `welinc-web-vrms` has an empty `main`, and the real work sits on `week-6`), so ask the team which branch to branch from and merge into before you start.
- **Commits:** Conventional Commits, one line, for example `feat(design-system): add DataTable`. One commit per milestone.
- **Pull requests:** open one per feature branch into that repo's long lived branch. Do not push straight to it.
- **One repo at a time.** A change that crosses repos (auth tokens, gateway routes, shared API shapes) needs a spec first.
- **Specs:** designed in `docs/specs/` before building. The product backlog is in Jira, and Jira wins when it disagrees with a doc.
- **UI:** follows `design.md`. Use theme tokens, never raw hex values in components. Lint enforces this.

## Troubleshooting

- **Port already in use:** another container or dev server holds it. Run `docker ps` and stop the old one.
- **Sent back to the portal login:** you were idle too long (15 minutes) or have no token. Sign in through the portal at port 8000.
- **A container can't find a package:** rebuild it as shown above.
- **Database empty or tables missing:** run the migrate and seed commands in "Start the stack".
