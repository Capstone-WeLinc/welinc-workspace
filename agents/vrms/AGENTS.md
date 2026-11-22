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
- **File storage**: Azurite (the local Blob Storage emulator, port 10000) in `docker-compose.vrms.yml`, Azure Blob Storage when hosted. Only `welinc-backend-vrms` talks to it (spec 0017); the browser gets signed links. The hosted account holds one container per system (`vrms-attachments`, `vmms-attachments`); each backend gets Storage Blob Data Contributor on its own container only, plus Storage Blob Delegator on the account to sign links. Bicep never removes a role assignment, so narrowing one means deleting the old one by hand after the apply.
- **Runtime**: Node 24 and npm (`package-lock.json`) in every Node repo.

## Build approach

Tracer Bullet: each feature is built end to end through every layer and working before the next. The UI refresh phase overrides this with Facade: build the UI first on the data it already has. Workflow level is Beta (after `/develop`: `/check verify`, then `/test`). Never run or suggest `/check review` in this project, VRMS or shared work, and never add a `Review it` box. Deadline: staging is the demo; the defense dates are moving (since 2026-11-22: final by Dec 20 at the latest, exact dates to come), and the Azure credit ends Dec 18. The plan lives in `docs/scope/vrms/index.md`.

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
node scripts/check-design-tokens.mjs   # suite spec 0016 AC-2: design.md's color tokens match both apps' src/index.css (exit 0 passes)
bash agents/vrms/overnight/start.sh [features] [--until HH:MM] [--plan] [--watch]   # unattended run: a fresh session per item, local commits only, morning report (agents/vrms/overnight/README.md)

# Gateway checks (needs Docker and openssl; starts and removes its own containers)
node infra/gateway/test/check-routes.mjs

# Azure setup as code (VRMS spec 0008; order and gotchas in infra/README.md; needs az, jq, psql, dig, gh)
bash infra/scripts/apply.sh <shared|budget|staging|prod> [--what-if] [--domains]
WHATIF_ARGS="--result-format ResourceIdOnly" bash infra/scripts/apply.sh <env> --what-if   # a what if that prints no secret values
```

- **Before `check-system.mjs vmms` or `bms` locally:** pull their clones on `development`, start their stacks with `--build -V`, wait for each backend to finish compiling (minutes on the Mac), then run `npx prisma migrate deploy` in each of their Prisma containers. Their containers don't migrate at startup, so a newer commit answers 500 (`P2022 ColumnNotFound`) or a 503 health on a stale local database. That's local, not their code.
- **Only staging is hosted** (spec 0008 AC-24, since 2026-11-20): production exists as code only (`apply.sh prod`, the production path of each `deploy.yml`) and is never called live. Don't apply `prod`. A manual production run stops at task 19a's guard while `AZURE_CLIENT_ID_PROD` is unset. Every staging app and job ends in `-staging` (task 18a, done 2026-11-20).
- **Always pass `--domains` to `apply.sh staging`** (and its what if): without it `env.bicep` sends the gateway an empty custom domain list and unbinds `staging-api.welinc.app`.
- **Azure CLI on the Mac** is `~/.local/bin/az` (not on the agent shell's PATH): call it by full path, or prefix `PATH="$HOME/.local/bin:$PATH"` for `apply.sh`.
- **1Password CLI on the Mac** is `~/.local/bin/op`, signed in through the desktop app (Touch ID), run with the sandbox off. Use the `WeLinc` vault only (the staging private file is the document "WeLinc private (staging)"); pipe secret values in through stdin, never as arguments, and never print them.

## Specs

Product backlog lives in Jira (read it through the Atlassian MCP); Jira wins when it disagrees with a doc.

## Rules

- Ask before any git write: commit, push, merge, branch switch, or opening a PR.
- Before calling a task done, run `npm run lint` and the build in every repo you touched (`build:local` in the two frontends, plus `npm run typecheck` in web-vrms).
- VMMS and BMS repos (both `*-analytics-ai` repos included) belong to other groups: read them for integration context, never edit them.
- One exception when turning a group on for staging (spec 0008 task 18): the lead adds `.github/workflows/deploy.yml` from `docs/integration/deploy-templates/` and the deploy repo variables and secrets to that group's repos, by branch and PR into `development`. Nothing else in their repos.
- `welinc-mobile-vrms_vmms` (Expo) is shared with VMMS: VRMS may edit it for its repair screens. Branch from `development` and open a PR into it, like every service repo.
- Playwright is expensive (snapshots and screenshots eat context). Do not run it after every change. Use it only for a new page or flow, a visual or layout change that code cannot prove, or at `/check verify` before a PR. Prefer `browser_snapshot` over screenshots, keep it to one pass, and never for backend-only or logic-only edits.
- Say "Using skill: <name>" in the reply each time a skill is invoked, so the user can see it was applied.
- UI follows the suite `design.md` at the workspace root plus our own rules in `docs/context/vrms/design.md` (ours win on VRMS screens). Read both before UI work.

## Git

- integration: on
- merge target: `development` in every service repo. Branch from it and open PRs against it, never `main`. (The workspace repo itself has only `main`.)
- branch prefix: feat/
- commit: per-milestone
- attribution: none. Never add a `Co-Authored-By` trailer or a "Generated with Claude Code" line to commits or PR descriptions; commits are authored by the developer alone.
- rulesets (since 2026-11-20, enforced only while the repos are public, until the final defense): in all 13 public repos `development` and `main` refuse force pushes and deletion; `development` in every service repo takes changes only through a PR with green required checks (`ci` and `gitleaks` in ours, plus `db` in auth; `ci` in VMMS and BMS, none yet in `welinc-mobile-bms` until it has CI); the workspace `main` is PR only with `gitleaks` required. Repository admins can bypass. A service repo's `main` still moves by the hand fast forward in spec 0008. Workspace CI skips docs only changes (`ci.yml` paths filter); `gitleaks` still runs.

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
