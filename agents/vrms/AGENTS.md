# VRMS agent rules

VRMS (Vehicle Repair Management System) rules, loaded on top of the root `AGENTS.md`. Paths are from the workspace root.

- This file is the VRMS `AGENTS.md`. When a skill (`/sync`, `/audit`) wants to record a VRMS convention, it goes here, not in the root `AGENTS.md`. The root file is shared by all three groups: change it only through a pull request the other groups can see.
- To add or change a skill, edit it in `.claude/skills/`, run `node scripts/use-agents.mjs vrms --save`, then commit `agents/vrms/`. Editing the copies alone is lost on the next run.

## Stack

| Repo | What it is | Port |
|---|---|---|
| `welinc-web-vrms` | React + Vite + Tailwind SPA | 8001 |
| `welinc-backend-vrms` | NestJS + Prisma + PostgreSQL API | 3002 |

- **Gateway route**: `/vrms/`.
- **File storage**: Azurite (the local Blob Storage emulator, port 10000) in `docker-compose.vrms.yml`, Azure Blob Storage when hosted. Only `welinc-backend-vrms` talks to it (spec 0017); the browser gets signed links.
- **Runtime**: Node 24 and npm (`package-lock.json`) in every Node repo.

## Build approach

Tracer Bullet: each feature is built end to end through every layer and working before the next. The UI refresh phase overrides this with Facade: build the UI first on the data it already has. Workflow level is Beta (after `/develop`: `/check verify`, then `/test`). Never run or suggest `/check review` in this project, VRMS or shared work, and never add a `Review it` box. Deadline: deployed by the end of November 2026. The plan lives in `docs/scope/vrms/index.md`.

## Commands

```bash
# Whole stack (shared first)
docker compose -f docker-compose.shared.yml up -d
docker compose -f docker-compose.vrms.yml up -d

# Stop (data stays): the group stack first, the shared stack last
docker compose -f docker-compose.vrms.yml stop
docker compose -f docker-compose.shared.yml stop

# Scripts (run in Git Bash from the workspace root)
sh scripts/setup.sh vrms   # first time setup: clones, .env files, keys, packages, migrations, seeds; safe to run again
node scripts/check-system.mjs vrms   # suite spec 0014 checker: live login checks plus the leftovers scan (exit 0 passes)
node scripts/check-contract-routes.mjs <openapi.json>   # VRMS spec 0026: welinc-auth's docs against contract 0001 section 16 (exit 0 passes)

# Gateway checks (needs Docker; starts and removes its own containers)
node infra/gateway/test/check-routes.mjs

# Azure setup as code (VRMS spec 0008; order and gotchas in infra/README.md; needs az, jq, psql, dig, gh)
bash infra/scripts/apply.sh <shared|budget|staging|prod> [--what-if] [--domains]
```

## Specs

Product backlog lives in Jira (read it through the Atlassian MCP); Jira wins when it disagrees with a doc.

## Rules

- Ask before any git write: commit, push, merge, branch switch, or opening a PR.
- Before calling a task done, run `npm run lint` and the build in every repo you touched (`build:local` in the two frontends, plus `npm run typecheck` in web-vrms).
- VMMS and BMS repos (both `*-analytics-ai` repos and `welinc-mobile-vrms_vmms` included) belong to other groups: read them for integration context, never edit them.
- Playwright is expensive (snapshots and screenshots eat context). Do not run it after every change. Use it only for a new page or flow, a visual or layout change that code cannot prove, or at `/check verify` before a PR. Prefer `browser_snapshot` over screenshots, keep it to one pass, and never for backend-only or logic-only edits.
- Say "Using skill: <name>" in the reply each time a skill is invoked, so the user can see it was applied.
- UI follows the suite `design.md` at the workspace root plus our own rules in `docs/context/vrms/design.md` (ours win on VRMS screens). Read both before UI work.

## Git

- integration: on
- merge target: `development` in every service repo. Branch from it and open PRs against it, never `main`. (The workspace repo itself has only `main`.)
- branch prefix: feat/
- commit: per-milestone
- attribution: none. Never add a `Co-Authored-By` trailer or a "Generated with Claude Code" line to commits or PR descriptions; commits are authored by the developer alone.

## Agent skills

Reference skills load on their own when the work matches (say "Using skill: <name>"). Audit and polish skills never run on their own, not even as a step of `/develop` or `/check verify`: offer them in one line and wait for a yes. Never run more than one taste skill on a change.

- **Load on match:** `prisma-client-api`, `prisma-cli`, `nestjs-best-practices`, `tailwind-4-docs` (its docs snapshot is not downloaded yet), `vercel-composition-patterns`, `react-hook-form`, `ask-sonner`, `web-dnd-dnd-kit` (classic `@dnd-kit/core` and `@dnd-kit/sortable`), `sentry-nestjs-sdk`, `sentry-react-sdk` and `sentry-setup-releases` (Sentry setup and releases, spec 0025). Only for substantial work, not copy or class tweaks: `shadcn` and `vercel-react-best-practices`.
- **Ask first (demanding or writes extra code):**
  - `web-design-guidelines`: offer after a UI change.
  - `break-ui`: offer on pages with lists, tables or typed text.
  - `impeccable`: critique and polish only; the two design files win (never rewrite them or add a `PRODUCT.md`), keep its edit hook off. Offer on a new or reworked page, or when a screen looks off.
  - `docker-patterns`: offer on Dockerfile, compose, hosting or CI work (its examples use Node 22; we run 24).
  - Azure hosting (suite spec 0008): `azure-container-apps`, `azure-container-registry`, `azure-static-web-apps`, and `azure-deployment-preflight` before a Bicep deploy. Never `azure-prepare` or `azure-deploy` (they assume azd).
  - `emil-design-eng`: offer when animations, dialogs, popovers or tabs change; the effect rules in `welinc-web-vrms/AGENTS.md` win.

MCP servers (from `agents/vrms/mcp.json`): playwright, shadcn, atlassian (Jira; needs a one time sign in through `/mcp`), sentry (read real issues; sign in through `/mcp` once the Sentry org exists)

## Context files

- `docs/context/vrms/`: background only (overview, roles, glossary, BRD requirements with the Jira overrides); code and Jira win.
- Each repo's own `AGENTS.md` (auth, backend-vrms, web-vrms, web-portal) loads when you work in it.
