# WeLinc VRMS workspace

Workspace for VRMS (Vehicle Repair Management System), one subsystem of the WeLinc fleet suite (Capstone 2). Each `welinc-*` folder is its own git repo, cloned with `scripts/clone-all.sh` and ignored by this workspace repo.

## Stack

| Repo | Owner | What it is | Port |
|---|---|---|---|
| `welinc-web-vrms` | us | React + Vite + Tailwind SPA | 8001 |
| `welinc-backend-vrms` | us | NestJS + Prisma + PostgreSQL API | 3002 |
| `welinc-backend-vrms-analytics-ai` | us | Python FastAPI: AI triage (Gemini, pgvector) and analytics (DuckDB, Redis, Mongo) | 8020 |
| `welinc-auth` | shared | NestJS + Prisma auth service (JWT) | 3001 |
| `welinc-web-portal` | shared | React + Vite SSO portal | 8000 |
| `welinc-web-vmms`, `welinc-backend-vmms`, `welinc-web-bms`, `welinc-backend-bms` | other groups | read only for us | |

- **Gateway**: Nginx on port 3000 routes `/auth`, `/vrms`, `/repairs`, `/ai` and `/analytics` (config currently in `welinc-auth/nginx.conf`).
- **Package manager**: npm in every Node repo (`package-lock.json`); pip `requirements.txt` for the Python service.
- **Runtime**: the backend `.nvmrc` files say Node 24, but the Dockerfiles use Node 20 and 22. Treat 24 as the target.

## Build approach

<TBD, set by /scope>

## Commands

```bash
# Whole stack (start auth first: it creates the shared docker network)
docker compose -f docker-compose.auth.yml up -d
docker compose -f docker-compose.vrms.yml up -d
docker compose -f docker-compose.analytics.yml up -d

# Inside a Node repo
npm install
npm run lint
npm run build
npm run test        # NestJS repos only (Jest); the frontends have no tests yet
```

## Specs

Stored in `docs/specs/`. Format: `docs/specs/NNNN-title.md`. Product backlog lives in Jira (read it through the Atlassian MCP); Jira wins when it disagrees with a doc.

## Rules

- Ask before any git write: commit, push, merge, branch switch, or opening a PR.
- VMMS and BMS repos belong to other groups. Read them for integration context, never edit them.
- Before calling a task done, run lint, typecheck and build in every repo you touched.
- Playwright is expensive (snapshots and screenshots eat context). Do not run it after every change. Use it only for a new page or flow, a visual or layout change that code cannot prove, or at `/check verify` before a PR. Prefer `browser_snapshot` over screenshots, keep it to one pass, and never for backend-only or logic-only edits.
- Say "Using skill: <name>" in the reply each time a skill is invoked, so the user can see it was applied.
- Never read, print or commit `.env` values. Document new variables in `.env.example` only. `VITE_*` variables ship to the browser, so they must never hold secrets.
- Work inside one repo at a time. Changes that cross repos (auth tokens, gateway routes, shared API shapes) need a spec first.
- UI follows `design.md` at this root. Use theme tokens, never raw hex values in components.

## Git

- integration: on
- merge target: `development` in every service repo. Branch from it and open PRs against it, never `main`. (This workspace repo itself has only `main`.)
- branch prefix: feat/
- commit: per-milestone

## Agent skills

- [prisma-client-api](.claude/skills/prisma-client-api/), [prisma-cli](.claude/skills/prisma-cli/): `prisma/skills`, Prisma 7 queries and CLI (backend-vrms, auth)
- [nestjs-best-practices](.claude/skills/nestjs-best-practices/): `kadajett/agent-nestjs-skills`, NestJS modules, DI, security (backend-vrms, auth)
- [tailwind-4-docs](.claude/skills/tailwind-4-docs/): `lombiq/tailwind-agent-skills`, Tailwind v4 docs and the v3 to v4 migration. The frontends are still on v3, so use it for the upgrade, not for v3 code. Its docs snapshot is not downloaded yet.
- [shadcn](.claude/skills/shadcn/): `shadcn-ui/ui`, shadcn/ui setup and component usage (frontends)
- [vercel-react-best-practices](.claude/skills/vercel-react-best-practices/), [vercel-composition-patterns](.claude/skills/vercel-composition-patterns/): `vercel-labs/agent-skills`, React patterns and React 19 component APIs (frontends)
- [fastapi](.claude/skills/fastapi/): `fastapi/fastapi`, FastAPI and Pydantic conventions (analytics-ai)

MCP servers (configured in `.mcp.json`): playwright, shadcn, atlassian (Jira; needs a one time sign in through `/mcp`)

## Context files

- [docs/context/](docs/context/): project background, system overview (decisions and open questions), roles and users, glossary. Background only; code and Jira win.
- [design.md](design.md): UI art direction and tokens for web-vrms and web-portal.
- [welinc-web-vrms/AGENTS.md](welinc-web-vrms/AGENTS.md): VRMS SPA structure, API and auth handling, color tokens, and effect rules.
- [welinc-backend-vrms/AGENTS.md](welinc-backend-vrms/AGENTS.md): NestJS API modules, guards, Prisma and migration rules, Docker restart gotcha.
- [welinc-backend-vrms-analytics-ai/AGENTS.md](welinc-backend-vrms-analytics-ai/AGENTS.md): FastAPI AI and analytics service, the 30 second sync, stores and env variables.

<!-- Nested AGENTS.md files are listed here as they are created -->

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
