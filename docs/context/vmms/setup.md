# VMMS local setup

Use Node 24, npm, Docker Desktop, and the workspace setup instructions in the
root [README](../../../README.md). Never print, paste, or commit `.env`
values.

## First-time setup

From the workspace root, in Git Bash on Windows or a terminal on macOS:

```sh
sh scripts/setup.sh vmms
```

The workspace script clones VMMS and shared repositories, prepares local
environment files without replacing existing ones, installs dependencies,
starts shared services before VMMS, applies migrations, and seeds an empty
database as appropriate. Review the script before using it if the local
environment has uncommitted setup work.

## Start and stop

Start shared services first because they create the network used by each
system:

```sh
docker compose -f docker-compose.shared.yml up -d
docker compose -f docker-compose.vmms.yml up -d
```

Stop VMMS before shared services:

```sh
docker compose -f docker-compose.vmms.yml stop
docker compose -f docker-compose.shared.yml stop
```

The local VMMS web app is at `http://localhost:8002`. Its core API is routed
through `http://localhost:3000/vmms/`; analytics is routed through
`http://localhost:3000/vmms/analytics/`. Local service ports are listed in
[system overview](system-overview.md).

## Migrations and environment

Apply core database migrations through the owning backend service:

```sh
docker compose -f docker-compose.vmms.yml exec -T vmms-backend npx prisma migrate deploy
```

Use each repository's `.env.example` for environment variable names and safe
defaults. `node scripts/sync-env.mjs` adds missing names to existing local
environment files and prints names only; it does not print values. Provider
credentials and signing keys belong only in local/deployment secret storage,
never in docs or browser-exposed `VITE_*` variables.

## Development commands

Run commands from the workspace root:

```sh
npm --prefix welinc-backend-vmms run build
npm --prefix welinc-backend-vmms test -- --runInBand
npm --prefix welinc-backend-vmms-analytics-ai run build
npm --prefix welinc-web-vmms run dev
npm --prefix welinc-web-vmms run build
```

Read each repository's README, scripts, and instructions before choosing
additional checks. Do not run broad or destructive database resets; preserve
local volumes and data.
