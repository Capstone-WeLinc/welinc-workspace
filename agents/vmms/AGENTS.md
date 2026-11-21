# VMMS AI setup

VMMS rules, loaded on top of the root `AGENTS.md`. Paths are from the workspace root.

- This file is the VMMS `AGENTS.md`. VMMS-specific conventions go here, not in the root `AGENTS.md`, so shared rules remain visible to every group.
- To add or change a skill, edit it in `.claude/skills/`, run `node scripts/use-agents.mjs vmms --save`, then commit `agents/vmms/`. Editing the local copies alone is lost on the next run.

## Stack

| Repo | What it is | Port |
|---|---|---|
| `welinc-backend-vmms` | NestJS + Prisma + PostgreSQL API | 3010 |
| `welinc-backend-vmms-analytics-ai` | NestJS analytics/AI service + reporting data | 3011 |
| `welinc-web-vmms` | React + Vite admin SPA | 8002 |
| `welinc-mobile-vrms_vmms` | shared React Native VRMS/VMMS app | Expo |

- **Gateway route**: `/vmms/`.
- **File storage**: private Azure Blob Storage for VMMS attachments and fuel receipts; the hosted account holds one container per system. Only `welinc-backend-vmms` talks to VMMS storage.
- **Runtime**: Node 24 and npm (`package-lock.json`) in every Node repo.

## Scope and ownership

- VMMS repositories are `welinc-backend-vmms`, `welinc-backend-vmms-analytics-ai`, `welinc-web-vmms`, and `welinc-mobile-vrms_vmms` (the shared VRMS/VMMS mobile app).
- Work in one repository at a time. Check its `git status` before editing and preserve existing user changes.
- Do not edit `welinc-auth`, `welinc-web-portal`, another system's repository or setup, or workspace-level files. Cross-repository changes need a spec first.
- Shared accounts and roles come from `welinc-auth`. Do not add a second account store or read another system's database. Inter-service calls go through the documented service API or gateway.
- Never read, print, or commit `.env` values. Put new variable names and safe examples in `.env.example`. `VITE_*` values are public in the browser and must not contain secrets.

## Repository map

- `welinc-backend-vmms`: NestJS VMMS API, Prisma schema and PostgreSQL migrations.
- `welinc-backend-vmms-analytics-ai`: separate NestJS analytics/AI service, DuckDB reporting data, and authenticated calls to the core VMMS API.
- `welinc-web-vmms`: React + Vite VMMS admin frontend.
- `welinc-mobile-vrms_vmms`: shared React Native mobile app for VRMS and VMMS. Keep VMMS work within its VMMS screens and flows; do not change VRMS behavior.

## Project workflow

- Before every VMMS task, audit, or gap report, check the workspace `AGENTS.md`, the shared suite overview and relevant shared scope/specs, then check `docs/scope/vmms/index.md`, VMMS specs, and the target repository's instructions. Use both workspace ownership and VMMS scope to decide who owns a requirement; do not infer scope from code presence or the RTM alone.
- The suite scope assigns login activity and account-change auditing to shared services, with the portal as the audit UI. Account creation, role assignment, lock/unlock, deactivation, and account audit are not VMMS features. Do not report these as missing VMMS implementation or add duplicate VMMS account-management or login-audit screens. Report a VMMS integration gap only when an owned VMMS flow fails to consume or enforce the shared-service contract.
- The VMMS scope is tracked in `docs/scope/vmms/index.md` and linked from the shared suite index. Do not infer project completion from the VRMS backlog or old handoff notes. Use the user's current task, VMMS issue tracker, and VMMS specs as the source of VMMS work. Keep VMMS scope and specs in their VMMS-owned locations.
- VMMS specs live under `docs/specs/vmms/NNNN-title/`. For a material feature decision or approved feature slice, maintain three VMMS-owned files: `index.md` for the build contract, `rationale.md` for context, options, and the decision record, and `verify.md` for acceptance-criteria-derived verification steps. Link the rationale and verification files from `index.md`.
- Keep implementation and verification status separate in spec work. Record completed implementation and unresolved runtime, deployment, pilot, or interactive-acceptance checks in the relevant spec and report only evidence that was actually run.
- For feature work, identify the smallest complete user flow and trace the affected backend, analytics, web, and mobile surfaces before editing. Build the requested flow through its required layers before starting unrelated work.
- For VMMS UI design, review, or refinement, follow `skills/impeccable/SKILL.md` and its relevant reference. Keep its changes within VMMS-owned web/mobile surfaces and preserve the existing VMMS visual system unless the user asks for a redesign.
- For shared API, auth token, gateway route, or data contract changes, write a spec first and follow the workspace cross-repository rules.

Read the target repository's README, package scripts, and local instructions before changing it. Keep API contracts aligned with the VMMS specs and callers. Preserve role checks, work-order assignment checks, session validation, and response filtering for sensitive fields such as costs.

## Changes and verification

- Prefer focused changes that fit the repository's existing patterns.
- Do not add or run tests unless the user asks for tests or verification. When asked, use the target repository's documented scripts and report what ran.
- Do not deploy, publish, merge, push, or contact people unless the user explicitly asks.
- For audits, report actionable findings with severity, file and line, impact, and a concrete remediation. Separate confirmed defects from questions that need runtime or product confirmation.

## Commands

```bash
# Whole stack (shared first)
docker compose -f docker-compose.shared.yml up -d
docker compose -f docker-compose.vmms.yml up -d

# Stop (data stays): the VMMS stack first, the shared stack last
docker compose -f docker-compose.vmms.yml stop
docker compose -f docker-compose.shared.yml stop

# Workspace and suite checks
node scripts/check-system.mjs vmms
node scripts/check-contract-routes.mjs <openapi.json>
node scripts/check-names.mjs
```

## Specs

- Product backlog and Jira status are inputs to VMMS work; VMMS requirement artifacts remain VMMS-owned.
- VMMS specs live at `docs/specs/vmms/NNNN-title/`.
- Material feature decisions require `index.md`, `rationale.md`, and `verify.md`.
- `index.md` is the build contract, `rationale.md` records context and approved decisions, and `verify.md` records observable acceptance checks and remaining verification evidence.

## Git

- Integration: on
- Merge target: `development` in service repos; never merge VMMS service work into `main`.
- Branch prefix: `feat/`
- Commit: per milestone
- Work in one repository at a time unless the task has an approved spec and explicit cross-repository scope.
- Ask before commit, push, merge, branch switch, or opening a PR.

## Agent skills

Reference skills load when the work matches:

- `architect`, `coding`, `debug`, `check`, `testing`, `sync`, `requirements`, `audit`, `integration-review`, `project-workflow`, `stack-patterns`
- Frontend: `impeccable`, `shadcn`, `tailwind-4-docs`, `react-hook-form`, `ask-sonner`, `vercel-composition-patterns`, `vercel-react-best-practices`
- Backend: `nestjs-best-practices`, `prisma-client-api`, `prisma-cli`
- Verification: `playwright`, `break-ui`

Audit and UI-polish skills require an explicit verification or user-visible polish request; do not run them as an automatic step of every implementation.
