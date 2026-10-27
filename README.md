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

`clone-all.sh` checks out `development` in every repo that has one and leaves the others on their default branch.

### Environment files

Each backend has a `.env.example` that already points at the local Docker databases. Copy it to `.env`:

```bash
cp welinc-auth/.env.example welinc-auth/.env
cp welinc-backend-vrms/.env.example welinc-backend-vrms/.env
cp welinc-backend-vrms-analytics-ai/.env.example welinc-backend-vrms-analytics-ai/.env
```

Then add the values only you have:

| File | Variable | Needed for |
|---|---|---|
| `welinc-backend-vrms-analytics-ai/.env` | `GEMINI_API_KEY` | AI triage. Create one at aistudio.google.com (Get API key, then Create API key). |
| `welinc-auth/.env` | `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` (optional) | Sending OTP and reset emails. Left blank, emails are logged instead. |
| `welinc-auth/.env`, `welinc-backend-vrms/.env` | `SEMAPHORE_API_KEY` (optional) | SMS. No code uses it yet. |

The auth, VRMS backend and web containers take their settings from the compose files, so the stack starts without these. The one exception is auth: if `welinc-auth/.env` exists, the auth container also reads it, which is how it gets `SMTP_*` (without them, emails are printed to the auth log instead of sent). The compose values win on any overlap. The backend `.env` files are also used for running migrations, seeds or a service outside Docker. If you run one backend outside Docker, keep `JWT_SECRET` equal to the value in the compose files, or its tokens will not verify.

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

Seed logins for local testing are in `welinc-auth/prisma/seeds/users.seed.ts`, for example `vrms.admin@welinc.com`. The VRMS backend seed adds mechanics such as `mech.juan@welinc.com`.

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

## Update an existing setup

When teammates have pushed, bring your machine up to date. The workspace repo is on `main`; each service repo is on `development` (or your own `feat/` branch, which you should rebase or merge `development` into).

```bash
git pull --ff-only                                   # workspace docs and compose files
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
| `package.json` or `package-lock.json` | `npm install` in that repo |
| `prisma/migrations/` | `npx prisma migrate deploy` in that backend |
| Seed files | `npm run seed` in that backend |
| A new variable in `.env.example` | Add it to your own `.env` or `.env.local` |
| `Dockerfile` or compose files | `docker compose -f docker-compose.<name>.yml up -d --build` |

If a container then fails on a missing package, see the rebuild command under "Start the stack".

## Daily commands

Inside a Node repo:

```bash
npm run lint
npm run typecheck     # web apps
npm run build
npm run test          # NestJS repos only
```

Before calling a task done, run lint, typecheck and build in every repo you touched, and check UI changes in a real browser.

In `welinc-auth` and `welinc-backend-vrms`, `npm run lint` fixes files in place. `npm run lint:ci` only checks, and it is what CI runs.

### Continuous integration

Every service repo we own has a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs on pull requests into `development` and on pushes to it:

| Repo | Checks |
|---|---|
| `welinc-auth`, `welinc-backend-vrms` | `prisma generate`, `lint:ci`, build, tests |
| `welinc-web-vrms`, `welinc-web-portal` | lint, build (web-vrms also typechecks) |
| `welinc-backend-vrms-analytics-ai` | every Python file compiles (no linter or tests yet) |

The checks warn but do not block a merge: GitHub Free cannot require them.

## How we work

- **Branches:** this workspace repo uses `main`. In every service repo, branch from `development` as `feat/<feature>`, one per feature, and open PRs back into `development`, never `main`.
- **Commits:** Conventional Commits, one line, for example `feat(design-system): add DataTable`. One commit per milestone.
- **Pull requests:** open one per feature branch into `development`. Do not push straight to it.
- **One repo at a time.** A change that crosses repos (auth tokens, gateway routes, shared API shapes) needs a spec first.
- **Specs:** designed in `docs/specs/` before building. The product backlog is in Jira, and Jira wins when it disagrees with a doc.
- **UI:** follows `design.md`. Use theme tokens, never raw hex values in components. Lint enforces this.

## Troubleshooting

- **Port already in use:** another container or dev server holds it. Run `docker ps` and stop the old one.
- **Sent back to the portal login:** you were idle too long (15 minutes) or have no token. Sign in through the portal at port 8000.
- **A container can't find a package:** rebuild it as shown above.
- **Database empty or tables missing:** run the migrate and seed commands in "Start the stack".
