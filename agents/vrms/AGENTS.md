# VRMS agent rules

The VRMS group's rules for AI tools: Vehicle Repair Management System, built by our group. They load only for people who ran `node scripts/use-agents.mjs vrms` (it adds `@agents/vrms/AGENTS.md` to a git ignored `CLAUDE.local.md`). Read them together with the suite rules in the root `AGENTS.md`. Paths below are from the workspace root.

- This file is the VRMS `AGENTS.md`. When a skill (`/sync`, `/audit`) wants to record a VRMS convention, it goes here, not in the root `AGENTS.md`. The root file is shared by all three groups: change it only through a pull request the other groups can see.
- Our skills, MCP servers and extra settings live in `agents/vrms/` and are copied into `.claude/skills/`, `.mcp.json` and `.claude/settings.local.json` by the script. To add or update a skill, change it locally, then run `node scripts/use-agents.mjs vrms --save` and commit `agents/vrms/`. Editing the copies alone is lost on the next run.

## Stack

| Repo | What it is | Port |
|---|---|---|
| `welinc-web-vrms` | React + Vite + Tailwind SPA | 8001 |
| `welinc-backend-vrms` | NestJS + Prisma + PostgreSQL API | 3002 |

- **Gateway route**: `/vrms/` (`/repairs` is gone since contract version 3). The gateway config lives in `infra/gateway/`.
- **File storage**: Azurite (the local Blob Storage emulator, port 10000) in `docker-compose.vrms.yml`, Azure Blob Storage when hosted. Only `welinc-backend-vrms` talks to it (spec 0017); the browser gets signed links.
- **Package manager**: npm in every Node repo (`package-lock.json`).
- **Runtime**: Node 24 everywhere (`.nvmrc` and the Dockerfiles in auth, backend-vrms, web-vrms and web-portal; `engines` is `24.x` in the backends).

## Build approach

Tracer Bullet: each feature is built end to end through every layer and working before the next. The UI refresh phase overrides this with Facade: build the UI first on the data it already has. Workflow level is Beta (after `/develop`: `/check verify`, then `/test`). Never run or suggest `/check review` in this project, VRMS or shared work (dropped 2026-11-11 for the deadline), and never add a `Review it` box. Deadline: deployed by the end of November 2026. The plan lives in `docs/scope/vrms/index.md`.

## Commands

```bash
# Whole stack (start the shared stack first: it creates the shared docker network)
docker compose -f docker-compose.shared.yml up -d
docker compose -f docker-compose.vrms.yml up -d

# Same thing with scripts (spec 0008): first time setup, then start and stop
sh scripts/setup.sh vrms   # clones, .env files, keys, packages, migrations, seeds; safe to run again
sh scripts/start.sh vrms   # starts the stack and prints ok per service
node scripts/check-system.mjs vrms   # suite spec 0014 checker: live login checks plus the leftovers scan (exit 0 passes)
sh scripts/stop.sh         # stops every welinc_ container

# Gateway checks (needs Docker; starts and removes its own containers)
node infra/gateway/test/check-routes.mjs

# Inside a Node repo
npm install
npm run lint
npm run build         # backends; in web-vrms and web-portal it needs real https VITE_* values (CI, hosting)
npm run build:local   # web-vrms and web-portal on your machine: builds with .env.development (spec 0010)
npm run typecheck     # web-vrms only; the backends typecheck through npm run build
npm run test        # NestJS repos (Jest) and web-vrms (Vitest, pure logic only)
```

## Specs

Stored in `docs/specs/vrms/`. Format: `docs/specs/vrms/NNNN-title/`. Product backlog lives in Jira (read it through the Atlassian MCP); Jira wins when it disagrees with a doc.

## Rules

- Ask before any git write: commit, push, merge, branch switch, or opening a PR.
- Before calling a task done, run lint, typecheck and build in every repo you touched (`npm run build:local` in the two frontends).
- VMMS and BMS repos belong to other groups. Read them for integration context, never edit them (our settings block edits there).
- Playwright is expensive (snapshots and screenshots eat context). Do not run it after every change. Use it only for a new page or flow, a visual or layout change that code cannot prove, or at `/check verify` before a PR. Prefer `browser_snapshot` over screenshots, keep it to one pass, and never for backend-only or logic-only edits.
- Say "Using skill: <name>" in the reply each time a skill is invoked, so the user can see it was applied.
- UI follows the suite `design.md` at the workspace root plus our own rules in `docs/context/vrms/design.md` (ours win on VRMS screens). Read both before UI work. Use theme tokens, never raw hex values in components.

## Git

- integration: on
- merge target: `development` in every service repo. Branch from it and open PRs against it, never `main`. (The workspace repo itself has only `main`.)
- branch prefix: feat/
- commit: per-milestone
- attribution: none. Never add a `Co-Authored-By` trailer or a "Generated with Claude Code" line to commits or PR descriptions; commits are authored by the developer alone.

## Agent skills

Reference skills load on their own when the work matches (say "Using skill: <name>"). Audit and polish skills never run on their own, not even as a step of `/develop` or `/check verify`: offer them in one line and wait for a yes. Never run more than one taste skill on a change.

- **Backend, load on match:** `prisma-client-api` and `prisma-cli` for Prisma 7 (backend-vrms, auth); `nestjs-best-practices` for NestJS.
- **Frontend, load on match:** `tailwind-4-docs` (web-vrms and web-portal are both on v4; its docs snapshot is not downloaded yet), `vercel-composition-patterns`, `react-hook-form` for forms, `ask-sonner` for toasts, `web-dnd-dnd-kit` for drag and drop (classic `@dnd-kit/core` and `@dnd-kit/sortable`). Two larger ones load only for substantial work, not copy or class tweaks: `shadcn` when building, restyling, theming or adding shadcn UI, and `vercel-react-best-practices` for new components or hooks, effects, data fetching, lists, performance, or a React review.
- **Ask first (demanding or writes extra code):**
  - `web-design-guidelines`: accessibility and UX audit with `file:line` findings. Offer it after a UI change; it fetches its rules from GitHub.
  - `break-ui`: worst case data stress test behind a dev only toggle. Offer it on pages with lists, tables or typed text.
  - `impeccable`: critique and polish only; the two design files win, never rewrite them or add a `PRODUCT.md`, keep its edit hook off. Offer it on a new or reworked page, or when a screen looks off.
  - `docker-patterns`: Dockerfile, compose and container networking patterns (17 KB; examples use Node 22, we run 24). Offer it on any Dockerfile or compose edit, or hosting and CI work.
  - Azure hosting (spec 0008, about 63 KB together): `azure-container-apps`, `azure-container-registry`, `azure-static-web-apps`, and `azure-deployment-preflight` before a Bicep deploy. Offer them for hosting work. Skip `azure-prepare` and `azure-deploy`: they assume azd.
  - `emil-design-eng`: motion and polish review; yields to the effect rules in `welinc-web-vrms/AGENTS.md`. Offer it when animations, dialogs, popovers or tabs change.

MCP servers (from `agents/vrms/mcp.json`): playwright, shadcn, atlassian (Jira; needs a one time sign in through `/mcp`)

## Context files

- `docs/context/vrms/`: project background, system overview (decisions and open questions), roles and users, glossary, requirements (BRD field rules, limits and targets, with the Jira overrides). Background only; code and Jira win.
- `docs/scope/vrms/`, `docs/specs/vrms/`, `docs/reviews/vrms/`: our plan, specs and reviews.
- `design.md` (suite art direction and tokens, also the portal's) and `docs/context/vrms/design.md` (ticket status colors, priority badges, plate chip, ticket naming, list rows, phone detail order).
- `welinc-web-vrms/AGENTS.md`: VRMS SPA structure, API and auth handling, color tokens, and effect rules.
- `welinc-backend-vrms/AGENTS.md`: NestJS API modules (including analytics and AI), guards, Prisma and migration rules, Docker restart gotcha.
- `welinc-auth/AGENTS.md`: shared auth service routes, role per system JWT, lockout, gateway nginx and CORS.
- `welinc-web-portal/AGENTS.md`: SSO portal launcher and routing rules, Tailwind v4 and shadcn.
