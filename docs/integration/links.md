# Links: where to look at what

Every place to open, check or manage the suite, per system: local addresses, databases, API docs, hosted apps, and the outside accounts. It holds no passwords or keys: local database logins are in each compose file, hosted secrets in the password manager.

Hosted addresses use `welinc.app` (see [hosting.md](hosting.md)). Staging is the same name with `staging-` in front.

## Quick health check

| What | Local | Staging | Production |
|---|---|---|---|
| Gateway | http://localhost:3000/health | https://staging-api.welinc.app/health | https://api.welinc.app/health |
| welinc-auth | http://localhost:3000/auth/health | https://staging-api.welinc.app/auth/health | https://api.welinc.app/auth/health |
| VRMS | http://localhost:3000/vrms/health | https://staging-api.welinc.app/vrms/health | https://api.welinc.app/vrms/health |
| VMMS | http://localhost:3000/vmms/health | https://staging-api.welinc.app/vmms/health | https://api.welinc.app/vmms/health |
| VMMS analytics | http://localhost:3000/vmms/analytics/health | https://staging-api.welinc.app/vmms/analytics/health | https://api.welinc.app/vmms/analytics/health |
| BMS | http://localhost:3000/bms/health | https://staging-api.welinc.app/bms/health | https://api.welinc.app/bms/health |

A healthy answer is 200 with `{"status":"ok", ...}`. Before a group is turned on hosted, its routes answer 502 `UPSTREAM_UNAVAILABLE`.

The full contract check: `node scripts/check-system.mjs <vrms|vmms|bms>` from the workspace root (local stack).

## Shared services

| Repo | Local app | Direct port | Hosted |
|---|---|---|---|
| [welinc-auth](https://github.com/Capstone-WeLinc/welinc-auth) | http://localhost:3000/auth/ | 3001 | Container App `auth-service` |
| [welinc-web-portal](https://github.com/Capstone-WeLinc/welinc-web-portal) | http://localhost:8000 | 8000 | https://portal.welinc.app (Static Web App `swa-welinc-<env>-portal`) |
| Gateway (`infra/gateway/`) | http://localhost:3000 | 3000 | https://api.welinc.app (Container App `api-gateway`) |

- **API docs (Scalar):** http://localhost:3000/auth/docs, and on staging https://staging-api.welinc.app/auth/docs. Never in production (spec 0026). The committed copy is [`docs/openapi.json`](https://github.com/Capstone-WeLinc/welinc-auth/blob/development/docs/openapi.json).
- **Database:** `localhost:5432`, database `welinc_auth_db`, user `welinc_auth_user` (container `welinc_auth_db`).
- **Logs:** `docker logs -f welinc_auth_service`, `docker logs -f welinc_api_gateway`, `docker logs -f welinc_portal`.

## VRMS

| Repo | Local app | Port | Hosted |
|---|---|---|---|
| [welinc-backend-vrms](https://github.com/Capstone-WeLinc/welinc-backend-vrms) | http://localhost:3000/vrms/ | 3002 | Container App `vrms-backend` |
| [welinc-web-vrms](https://github.com/Capstone-WeLinc/welinc-web-vrms) | http://localhost:8001 | 8001 | https://vrms.welinc.app (Static Web App `swa-welinc-<env>-vrms`) |

- **API docs (Scalar):** http://localhost:3000/vrms/docs, and on staging https://staging-api.welinc.app/vrms/docs. Never in production.
- **Database:** `localhost:5433`, database `welinc_vrms_db`, user `welinc_vrms_user` (container `welinc_vrms_db`, pgvector).
- **File storage:** Azurite on `localhost:10000` (container `welinc_vrms_azurite`). Open it in Azure Storage Explorer: *Attach to a local emulator*.
- **Logs:** `docker logs -f welinc_vrms_backend`.

## VMMS

| Repo | Local app | Port | Hosted |
|---|---|---|---|
| [welinc-backend-vmms](https://github.com/Capstone-WeLinc/welinc-backend-vmms) | http://localhost:3000/vmms/ | 3010 | Container App `vmms-backend` |
| [welinc-backend-vmms-analytics-ai](https://github.com/Capstone-WeLinc/welinc-backend-vmms-analytics-ai) | http://localhost:3000/vmms/analytics/ | 3011 | Container App `vmms-analytics` |
| [welinc-web-vmms](https://github.com/Capstone-WeLinc/welinc-web-vmms) | http://localhost:8002 | 8002 | https://vmms.welinc.app (Static Web App `swa-welinc-<env>-vmms`) |
| [welinc-mobile-vrms_vmms](https://github.com/Capstone-WeLinc/welinc-mobile-vrms_vmms) | Expo, against your LAN address on port 3000 | none | the app calls https://api.welinc.app |

- **Database:** `localhost:5438`, database `welinc_vmms_db`, user `welinc_vmms_user` (container `welinc_vmms_db`). Analytics uses the same database.
- **Logs:** `docker logs -f welinc_vmms_backend`, `docker logs -f welinc_vmms_analytics`.
- **API docs:** none yet.

## BMS

| Repo | Process | Local | Port | Hosted Container App |
|---|---|---|---|---|
| [welinc-backend-bms](https://github.com/Capstone-WeLinc/welinc-backend-bms) | gateway | http://localhost:3000/bms/ | 3020 | `bms-gateway` |
| | booking | | 3021 | `bms-booking` |
| | dispatch | | 3022 | `bms-dispatch` |
| | completion | | 3023 | `bms-completion` |
| | analytics projection (a worker) | | 3024 | `bms-analytics-projection` |
| [welinc-backend-bms-analytics-ai](https://github.com/Capstone-WeLinc/welinc-backend-bms-analytics-ai) | analytics | through `/bms/reports` | 3025 | `bms-analytics` |
| [welinc-web-bms](https://github.com/Capstone-WeLinc/welinc-web-bms) | web app | http://localhost:8003 | 8003 | https://bms.welinc.app (Static Web App `swa-welinc-<env>-bms`) |

- **Databases**, all user `bms_user`:

  | Database | Local port | Container |
  |---|---|---|
  | `bms_booking_db` | 5434 | `welinc_bms_booking_db` |
  | `bms_dispatch_db` | 5435 | `welinc_bms_dispatch_db` |
  | `bms_completion_db` | 5436 | `welinc_bms_completion_db` |
  | `bms_analytics_db` | 5437 | `welinc_bms_analytics_db` |

- **Logs:** `docker logs -f welinc_bms_gateway` (and `welinc_bms_<process>` for the others).
- **API docs:** none yet.

## Looking inside the databases

- **Locally:** the VS Code PostgreSQL extension (or any Postgres client) on the ports above. The passwords are in each `docker-compose.*.yml`; they are local test values only.
- **Hosted:** one PostgreSQL 16 server per environment, `psql-welinc-staging` and `psql-welinc-prod` (host `psql-welinc-<env>.postgres.database.azure.com`). Each database has an `<db>_owner` login (migrations) and an `<db>_app` login (the service). Their passwords are in `infra/private/<env>.json` and the password manager. Add your IP to the server's firewall in the Azure portal before you connect.

## Azure

Open everything from the [Azure portal](https://portal.azure.com), *Resource groups*:

| Resource group | What's in it |
|---|---|
| `rg-welinc-shared` | the container registry (`acrwelinc...`), shared by both environments |
| `rg-welinc-staging` | everything for staging (names below with `<env>` = `staging`) |
| `rg-welinc-prod` | everything for production (`<env>` = `prod`) |

Inside an environment:

- **Container Apps** (backends, the gateway, migrate and seed jobs): environment `cae-welinc-<env>`. Each app's *Log stream* shows live logs, and *Revisions* lets you roll back.
- **Logs and queries:** Log Analytics workspace `log-welinc-<env>`.
- **Database:** `psql-welinc-<env>`.
- **Static Web Apps:** `swa-welinc-<env>-portal`, `-vrms`, `-vmms`, `-bms`.
- **Storage:** the account ending in `blob` (VRMS files).
- **Budget alerts** at $50, $100, $150 and $180: *Cost Management*, then *Budgets*.

Setup, order and gotchas: [infra/README.md](../../infra/README.md).

## GitHub

- **Org:** https://github.com/Capstone-WeLinc
- **CI and deploys:** each repo's *Actions* tab, for example https://github.com/Capstone-WeLinc/welinc-backend-vrms/actions. Staging deploys on every push to `development`; production is the "Run workflow" button on `main` (spec 0008).
- **Dependabot:** each repo's *Pull requests*, filtered by author `app/dependabot`.

## Outside accounts

| Service | What for | Where |
|---|---|---|
| Sentry | errors from `vrms-backend`, `vrms-web`, `welinc-auth`, `welinc-portal` (spec 0025) | https://welinc.sentry.io (org `welinc`, US region; how it was set up: [infra/RUNBOOK.md](../../infra/RUNBOOK.md)) |
| Brevo | the email welinc-auth sends (sign in codes, resets) | https://app.brevo.com (*Transactional*, then *Logs*) |
| Name.com | the `welinc.app` domain and its DNS records | https://www.name.com/account/domain |
| Jira | the backlog, the source of truth | the team's Atlassian site |

Logins for all of these live in the password manager.
