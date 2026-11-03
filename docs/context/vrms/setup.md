# VRMS setup

The VRMS group's local setup, on top of the shared steps in the workspace [README](../../../README.md). Our AI rules are in `agents/vrms/AGENTS.md`.

## Environment

```bash
cp welinc-backend-vrms/.env.example welinc-backend-vrms/.env
```

| File | Variable | Needed for |
|---|---|---|
| `welinc-backend-vrms/.env` | `GEMINI_API_KEY` | AI diagnosis and issue embeddings. Create one at aistudio.google.com (Get API key, then Create API key). |

The VRMS web app works with no setup. Only create `welinc-web-vrms/.env.local` to change a default.

## Start and seed

```bash
docker compose -f docker-compose.vrms.yml up -d
cd welinc-backend-vrms && npm install && npx prisma migrate deploy && npm run seed
```

The VRMS seed adds mechanics such as `mech.juan@welinc.com`, linked to the auth seed users by fixed ids.

| App | URL |
|---|---|
| VRMS web | http://localhost:8001 |
| VRMS API (through the gateway) | http://localhost:3000/vrms |

To work on the web app outside Docker: `cd welinc-web-vrms && npm install && npm run dev`.

## Daily commands

Inside a VRMS repo:

```bash
npm run lint
npm run typecheck     # web-vrms
npm run build
npm run test          # backend-vrms (Jest) and web-vrms (Vitest)
```

Before calling a task done, run lint, typecheck and build in every repo you touched, and check UI changes in a real browser. In `welinc-auth` and `welinc-backend-vrms`, `npm run lint` fixes files in place; `npm run lint:ci` only checks, and it is what CI runs.

| Repo | CI checks |
|---|---|
| `welinc-auth`, `welinc-backend-vrms` | `prisma generate`, `lint:ci`, build, tests |
| `welinc-web-vrms`, `welinc-web-portal` | lint, build (web-vrms also typechecks) |

## How we work

- **Branches:** branch from `development` as `feat/<feature>`, one per feature, and open PRs back into `development`. The workspace repo uses `main`.
- **Commits:** Conventional Commits, one line, for example `feat(design-system): add DataTable`. One commit per milestone.
- **Specs:** designed in `docs/specs/vrms/` before building. The backlog is in Jira (project `VRMS`), and Jira wins when it disagrees with a VRMS doc.
- **UI:** follows the suite `design.md` plus [design.md](design.md) in this folder. Use theme tokens, never raw hex values in components. Lint enforces this.
