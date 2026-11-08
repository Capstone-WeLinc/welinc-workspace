# WeLinc workspace

The shared workspace for the WeLinc fleet suite (Capstone 2): three systems, VRMS, VMMS and BMS, on shared auth, portal and gateway services. It holds the docs, the local Docker stack, scripts and AI agent files for all three. The service code lives in separate `welinc-*` repos that you clone next to this one; this repo ignores them.

Each group owns its own system's folders and repos. The shared parts (the root files, `docker-compose.shared.yml`, `docs/integration/`, `docs/context/suite-overview.md`) belong to everyone, so change them through a pull request the other groups can see. For how the systems fit together, start with [docs/context/suite-overview.md](docs/context/suite-overview.md).

## What is where

| Path | What it is |
|---|---|
| `docs/context/suite-overview.md` | The three systems, the shared services, and how they fit together |
| `docs/context/<system>/` | One system's background, setup, design rules, roles and users, glossary and requirements |
| `docs/integration/` | What the systems share: setup guide, meeting notes, contracts |
| `docs/scope/` | The living plan. [index.md](docs/scope/index.md) maps each system's scope in `docs/scope/<system>/` |
| `docs/specs/<system>/` | One folder per designed feature (`NNNN-title/`) with its spec and verify steps. Suite wide specs go in `docs/specs/_root/` |
| `docs/reviews/<system>/` | Code review reports |
| `design.md` | Suite UI art direction and design tokens (VRMS and the portal follow it today). Each system adds its own rules in `docs/context/<system>/design.md` |
| `docker-compose.shared.yml` | The shared stack: auth, its database and Redis, the gateway, the portal |
| `docker-compose.<system>.yml` | One system's stack (only `docker-compose.vrms.yml` so far) |
| `scripts/clone-all.sh` | Clones every service repo |
| `scripts/use-agents.mjs` | Turns on your group's AI setup locally |
| `agents/<system>/` | Each group's AI rules, skills and tool settings (loaded only by `use-agents.mjs`) |
| `AGENTS.md` | Suite rules every group's AI tools share (`CLAUDE.md` imports it) |

## The repos

| Repo | Owner | What it is | Port |
|---|---|---|---|
| `welinc-auth` | shared | NestJS auth service (JWT), plus the gateway config | 3001 |
| `welinc-web-portal` | shared | SSO portal | 8000 |
| `welinc-web-vrms` | VRMS group | React, Vite and Tailwind app | 8001 |
| `welinc-backend-vrms` | VRMS group | NestJS, Prisma and PostgreSQL API | 3002 |
| `welinc-web-vmms`, `welinc-backend-vmms`, `welinc-backend-vmms-analytics-ai`, `welinc-mobile-vrms_vmms` | VMMS group | | |
| `welinc-web-bms`, `welinc-backend-bms`, `welinc-backend-bms-analytics-ai` | BMS group | | |

An Nginx gateway on port 3000 routes each path to its service (today `/auth`, `/vrms`, `/repairs`). Pick free ports for a new system and add them to this table.

## Set up (everyone)

You need Git, Docker Desktop, and Node 24 (use `nvm`; the `.nvmrc` files say 24).

```bash
git clone https://github.com/Capstone-WeLinc/welinc-workspace.git
cd welinc-workspace
sh scripts/clone-all.sh          # clones every service repo next to the workspace files
```

`clone-all.sh` checks out `development` in every repo that has one and leaves the others on their default branch.

### Turn on your group's AI setup

If you use an AI coding tool, load only your own group's rules and skills:

```bash
node scripts/use-agents.mjs <system>     # vrms, vmms or bms: whichever folder your group has in agents/
```

It copies `agents/<system>/` into git ignored spots, so it never reaches the other groups. Run it again after a pull that changes your folder. See [agents/README.md](agents/README.md).

### Environment files

Each backend has a `.env.example` that already points at the local Docker databases. Copy it to `.env` for the shared auth service, and for your own system's backend as its setup page says:

```bash
cp welinc-auth/.env.example welinc-auth/.env
```

| File | Variable | Needed for |
|---|---|---|
| `welinc-auth/.env` | `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` (optional) | Sending OTP and reset emails. Left blank, emails are logged instead. |

The containers take their settings from the compose files, so the stack starts without these. If `welinc-auth/.env` exists, the auth container also reads it, which is how it gets `SMTP_*`. The compose values win on any overlap. The backend `.env` files are also used for running migrations, seeds or a service outside Docker. Before the first start, run `npm run keys:dev` in `welinc-auth`: it writes the signing keys into `welinc-auth/.env` and the VRMS client key into `welinc-backend-vrms/.env` (spec 0002). No service shares a secret any more: backends check tokens with welinc-auth's published keys.

| File | Purpose | Committed? |
|---|---|---|
| `.env.example` | Every variable name with safe placeholders | Yes |
| `.env.development` | Non secret dev defaults for the web apps (loaded by `npm run dev`) | Yes |
| `.env` | Your real values and secrets (backends) | Never |
| `.env.local`, `.env.*.local` | Your personal overrides | Never |
| `.env.production` | Production values, supplied by the host | Never |

Rules:
- Never commit a `.env` file or paste its values into chat or code.
- `VITE_*` variables ship to the browser. Never put a secret in one.
- Add any new variable to `.env.example` in the same change.

### Start the shared stack

Start it first: it creates the shared Docker network. Then start your own system (see its setup page).

```bash
docker compose -f docker-compose.shared.yml up -d
```

The containers do not run database migrations or seeds on start. The first time, run them for auth from your machine:

```bash
cd welinc-auth && npm install && npm run db:deploy && npm run seed
```

Seed logins are in `welinc-auth/prisma/seeds/users.seed.ts`, for example `vrms.admin@welinc.com`, `vmms.admin@welinc.com`, `bms.admin@welinc.com`.

| App | URL |
|---|---|
| Portal (sign in here) | http://localhost:8000 |
| Gateway | http://localhost:3000 |

Plugging a new system into the shared stack (compose file, gateway route, login) is covered in [docs/integration/setup-guide.md](docs/integration/setup-guide.md).

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
| `prisma/migrations/` | `npx prisma migrate deploy` in that backend; in `welinc-auth`, `npm run db:deploy` (migrations, then the role catalog sync) |
| `welinc-auth/prisma/catalog/` | `npm run catalog:sync` in `welinc-auth` (or `npm run db:deploy`) |
| Seed files | `npm run seed` in that backend |
| A new variable in `.env.example` | Add it to your own `.env` or `.env.local` |
| `Dockerfile` or compose files | `docker compose -f docker-compose.<name>.yml up -d --build` |
| Your group's `agents/<system>/` folder | `node scripts/use-agents.mjs <system>` |

If a container fails on a missing package after a `package.json` change, rebuild its image and refresh its `node_modules` volume: `docker compose -f docker-compose.<name>.yml up -d --build --renew-anon-volumes <service>`.

## Working in the shared parts

- **Shared repos** (`welinc-auth`, `welinc-web-portal`): branch from `development`, open a pull request back into `development`, never into `main`. Run `npm run lint` and `npm run build` (and `npm run test` in auth) first; CI runs the same checks on every pull request and warns but can't block a merge on GitHub Free.
- **Shared workspace files** (root files, `scripts/`, `docker-compose.shared.yml`, `docs/integration/`, `docs/context/suite-overview.md`): change them through a pull request the other groups can see.
- **One repo at a time.** A change that crosses repos (auth tokens, gateway routes, shared API shapes) needs a spec first, in `docs/specs/_root/`.
- **Your own system:** your group's repos and folders follow your group's own rules (its setup page and `agents/<system>/AGENTS.md`).

## Troubleshooting

- **Port already in use:** another container or dev server holds it. Run `docker ps` and stop the old one.
- **Sent back to the portal login:** you were idle too long (15 minutes) or have no token. Sign in through the portal at port 8000.
- **A container can't find a package:** rebuild it as shown under "Update an existing setup".
- **Database empty or tables missing:** run the migrate and seed commands for that backend.

## Each system's setup

Each group documents its own local setup (environment values, compose file, seed, apps, commands) in `docs/context/<system>/setup.md`.

| System | Setup page |
|---|---|
| VRMS | [docs/context/vrms/setup.md](docs/context/vrms/setup.md) |
| VMMS | not added yet |
| BMS | not added yet |
