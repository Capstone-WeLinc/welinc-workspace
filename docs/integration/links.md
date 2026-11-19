# Links: where to look at what

Every address to open or check, per system. No passwords here: local ones are in each compose file, hosted ones with the lead.

Staging is the only hosted environment. Its addresses start with `staging-` on `welinc.app`, and every Azure app and job ends in `-staging`.

## Quick health check

| What | Local | Staging |
|---|---|---|
| Gateway | http://localhost:3000/health | https://staging-api.welinc.app/health |
| welinc-auth | http://localhost:3000/auth/health | https://staging-api.welinc.app/auth/health |
| VRMS | http://localhost:3000/vrms/health | https://staging-api.welinc.app/vrms/health |
| VMMS | http://localhost:3000/vmms/health | https://staging-api.welinc.app/vmms/health |
| VMMS analytics | http://localhost:3000/vmms/analytics/health | https://staging-api.welinc.app/vmms/analytics/health |
| BMS | http://localhost:3000/bms/health | https://staging-api.welinc.app/bms/health |

Healthy is 200 with `{"status":"ok", ...}`. A group not yet turned on in staging answers 502 `UPSTREAM_UNAVAILABLE`.

Full check of a system on your local stack: `node scripts/check-system.mjs <vrms|vmms|bms>` from the workspace root.

## Shared services

| Repo | Local app | Direct port | Hosted |
|---|---|---|---|
| [welinc-auth](https://github.com/Capstone-WeLinc/welinc-auth) | http://localhost:3000/auth/ | 3001 | Container App `auth-service-staging` |
| [welinc-web-portal](https://github.com/Capstone-WeLinc/welinc-web-portal) | http://localhost:8000 | 8000 | https://staging-portal.welinc.app (Static Web App `swa-welinc-staging-portal`) |
| Gateway (`infra/gateway/`) | http://localhost:3000 | 3000 | https://staging-api.welinc.app (Container App `api-gateway-staging`) |

- **API docs (Scalar):** http://localhost:3000/auth/docs, and on staging https://staging-api.welinc.app/auth/docs. The committed copy is [`docs/openapi.json`](https://github.com/Capstone-WeLinc/welinc-auth/blob/development/docs/openapi.json).
- **Database:** `localhost:5432`, database `welinc_auth_db`, user `welinc_auth_user` (container `welinc_auth_db`).
- **Logs:** `docker logs -f welinc_auth_service`, `docker logs -f welinc_api_gateway`, `docker logs -f welinc_portal`.

## VRMS

| Repo | Local app | Port | Hosted |
|---|---|---|---|
| [welinc-backend-vrms](https://github.com/Capstone-WeLinc/welinc-backend-vrms) | http://localhost:3000/vrms/ | 3002 | Container App `vrms-backend-staging` |
| [welinc-web-vrms](https://github.com/Capstone-WeLinc/welinc-web-vrms) | http://localhost:8001 | 8001 | https://staging-vrms.welinc.app (Static Web App `swa-welinc-staging-vrms`) |

- **API docs (Scalar):** http://localhost:3000/vrms/docs, and on staging https://staging-api.welinc.app/vrms/docs.
- **Database:** `localhost:5433`, database `welinc_vrms_db`, user `welinc_vrms_user` (container `welinc_vrms_db`, pgvector).
- **File storage:** Azurite on `localhost:10000` (container `welinc_vrms_azurite`). Open it in Azure Storage Explorer: *Attach to a local emulator*.
- **Logs:** `docker logs -f welinc_vrms_backend`.

## VMMS

| Repo | Local app | Port | Hosted |
|---|---|---|---|
| [welinc-backend-vmms](https://github.com/Capstone-WeLinc/welinc-backend-vmms) | http://localhost:3000/vmms/ | 3010 | Container App `vmms-backend-staging` |
| [welinc-backend-vmms-analytics-ai](https://github.com/Capstone-WeLinc/welinc-backend-vmms-analytics-ai) | http://localhost:3000/vmms/analytics/ | 3011 | Container App `vmms-analytics-staging` |
| [welinc-web-vmms](https://github.com/Capstone-WeLinc/welinc-web-vmms) | http://localhost:8002 | 8002 | https://staging-vmms.welinc.app (Static Web App `swa-welinc-staging-vmms`) |
| [welinc-mobile-vrms_vmms](https://github.com/Capstone-WeLinc/welinc-mobile-vrms_vmms) | Expo, against your LAN address on port 3000 | none | the app calls https://staging-api.welinc.app |

- **Database:** `localhost:5438`, database `welinc_vmms_db`, user `welinc_vmms_user` (container `welinc_vmms_db`). Analytics uses the same database.
- **Logs:** `docker logs -f welinc_vmms_backend`, `docker logs -f welinc_vmms_analytics`.
- **API docs:** none yet.

## BMS

| Repo | Process | Local | Port | Hosted Container App (staging) |
|---|---|---|---|---|
| [welinc-backend-bms](https://github.com/Capstone-WeLinc/welinc-backend-bms) | gateway | http://localhost:3000/bms/ | 3020 | `bms-gateway-staging` |
| | booking | | 3021 | `bms-booking-staging` |
| | dispatch | | 3022 | `bms-dispatch-staging` |
| | completion | | 3023 | `bms-completion-staging` |
| | analytics projection (a worker) | | 3024 | `bms-analytics-projection-staging` |
| [welinc-backend-bms-analytics-ai](https://github.com/Capstone-WeLinc/welinc-backend-bms-analytics-ai) | analytics | through `/bms/reports` | 3025 | `bms-analytics-staging` |
| [welinc-web-bms](https://github.com/Capstone-WeLinc/welinc-web-bms) | web app | http://localhost:8003 | 8003 | https://staging-bms.welinc.app (Static Web App `swa-welinc-staging-bms`) |

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
- **Hosted:** one PostgreSQL 16 server, `psql-welinc-staging` (host `psql-welinc-staging.postgres.database.azure.com`). Each database has an `<db>_owner` login (migrations) and an `<db>_app` login (the service). Their passwords are in `infra/private/staging.json` and the password manager. Add your IP to the server's firewall in the Azure portal before you connect.

## Azure

Open everything from the [Azure portal](https://portal.azure.com), *Resource groups*:

| Resource group | What's in it |
|---|---|
| `rg-welinc-shared` | the container registry (`acrwelinc...`) |
| `rg-welinc-staging` | everything else |

Inside `rg-welinc-staging`:

- **Container Apps** (backends, the gateway, migrate and seed jobs): environment `cae-welinc-staging`; every app and job name ends in `-staging`. Each app's *Log stream* shows live logs, and *Revisions* lets you roll back.
- **Logs and queries:** Log Analytics workspace `log-welinc-staging`.
- **Database:** `psql-welinc-staging`.
- **Static Web Apps:** `swa-welinc-staging-portal`, `-vrms`, `-vmms`, `-bms`.
- **Storage:** the account ending in `blob` (VRMS files).
- **Budget alerts** at $50, $100, $150 and $180: *Cost Management*, then *Budgets*.

Setup, order and gotchas: [infra/README.md](../../infra/README.md).

## GitHub

- **Org:** https://github.com/Capstone-WeLinc
- **CI and deploys:** each repo's *Actions* tab, for example https://github.com/Capstone-WeLinc/welinc-backend-vrms/actions. Every push to `development` deploys staging. Don't press "Run workflow".
- **Dependabot:** each repo's *Pull requests*, filtered by author `app/dependabot`.

## Outside accounts

| Service | What for | Where |
|---|---|---|
| Sentry | errors from `vrms-backend`, `vrms-web`, `welinc-auth`, `welinc-portal` | https://welinc.sentry.io |
| Brevo | the email welinc-auth sends (codes, resets, alerts) | https://app.brevo.com (*Transactional*, then *Logs*). Free plan: 300 emails a day |
| Name.com | the `welinc.app` domain and its DNS records | https://www.name.com/account/domain |
| Jira | the backlog, the source of truth | the team's Atlassian site |

Ask the lead for access to any of these.
