# WeLinc workspace

Shared workspace for the WeLinc fleet suite (Capstone 2): three systems, VRMS, VMMS and BMS, each built by its own group on shared auth, portal and gateway services. Each `welinc-*` folder is its own git repo, cloned with `scripts/clone-all.sh` and ignored by this workspace repo. The suite level picture is in [docs/context/suite-overview.md](docs/context/suite-overview.md).

This file holds only the rules every group shares. Each group's own AI rules, skills and tool settings live in `agents/<system>/` and load only for the people who turn them on (see "Per group AI setup" below).

## Shared services

| Repo | What it is | Port |
|---|---|---|
| `welinc-auth` | NestJS + Prisma auth service (JWT, a role per system) | 3001 |
| `welinc-web-portal` | React + Vite SSO portal | 8000 |
| Gateway | Nginx; config in `infra/gateway/` (this repo, spec 0008) | 3000 |

- Run them with `docker compose -f docker-compose.shared.yml up -d`, always first: it creates the `welinc-network` Docker network every system joins. Its compose project name stays `auth-infrastructure` so existing containers and volumes keep working.
- Architecture: microservices between systems (own containers, database and deployment, API calls through the gateway), a modular monolith inside each system. No system reads another system's database.

## Ownership

- **Shared:** `welinc-auth`, `welinc-web-portal`, and the shared files here (root files, `scripts/`, `docker-compose.shared.yml`, `docs/integration/`, `docs/context/suite-overview.md`, `docs/scope/index.md`, `docs/specs/_root/`). A change to any of them affects every group: write a spec first and open a pull request the other groups can see.
- **Per system:** each group owns its repos, its folders (`agents/<system>/`, `docs/context/<system>/`, `docs/scope/<system>/`, `docs/specs/<system>/`, `docs/reviews/<system>/`) and `docker-compose.<system>.yml`. Don't edit another group's repos or folders.

## Per group AI setup

- Each group keeps its AI rules (`AGENTS.md`), skills, MCP servers and tool settings in `agents/<system>/`. Nothing in there loads on its own.
- Turn yours on with `node scripts/use-agents.mjs <system>`. It copies them into git ignored spots (`.claude/skills/`, `.mcp.json`, `.claude/settings.local.json`, and a `CLAUDE.local.md` that imports `agents/<system>/AGENTS.md`). Run it again after a pull that changes your folder.
- Only ever load your own group's setup. Another group's skills and rules don't apply to your work.

## Docs layout

- `docs/context/`: `suite-overview.md`, then one folder per system.
- `docs/integration/`: setup guide and shared material between systems.
- `docs/scope/index.md` maps each system's scope (`docs/scope/<system>/`); suite wide work goes in `docs/scope/_root/`.
- `docs/specs/<system>/NNNN-title/`, numbered per system; suite wide specs in `docs/specs/_root/`.

## Suite rules

- Never read, print or commit `.env` values. Document new variables in `.env.example` only. `VITE_*` variables ship to the browser, so they must never hold secrets.
- In the shared repos, branch from `development` and open a pull request back into `development`, never into `main`.
- Work inside one repo at a time. Changes that cross repos (auth tokens, gateway routes, shared API shapes) need a spec first.
- A new system picks free ports and adds them to the repos table in `README.md`.
