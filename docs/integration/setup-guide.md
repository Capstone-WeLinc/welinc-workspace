# Shared stack setup guide

How to run the shared services (auth, portal, gateway) on your machine and plug a system into them. It applies to every group. Before you connect a system to the shared repos for real, agree it with the other groups.

## 1. Get the workspace

You need Git, Docker Desktop, and Node 24.

```bash
git clone https://github.com/Capstone-WeLinc/welinc-workspace.git
cd welinc-workspace
sh scripts/clone-all.sh
```

`clone-all.sh` clones every service repo next to the workspace files and checks out `development` where it exists. If your system's repos live somewhere else for now, clone them into this folder yourself with the same `welinc-*` names.

The workspace layout is in [README.md](../../README.md). Each group owns `agents/<system>/`, `docs/context/<system>/`, `docs/scope/<system>/`, `docs/specs/<system>/` and `docker-compose.<system>.yml`. Anything shared changes through a pull request.

If you use an AI coding tool, put your group's rules, skills and tool settings in `agents/<system>/` and turn them on with `node scripts/use-agents.mjs <system>`. It copies them into git ignored spots, so each group's setup stays separate. Only load your own group's folder. See [agents/README.md](../../agents/README.md).

## 2. Start the shared stack

```bash
cp welinc-auth/.env.example welinc-auth/.env     # optional: only needed for real email (SMTP_*)
docker compose -f docker-compose.shared.yml up -d
```

This starts:

| Container | What it is | Port on your machine |
|---|---|---|
| `welinc_auth_db` | PostgreSQL for auth | 5432 |
| `welinc_auth_redis` | Redis for auth | 6379 |
| `welinc_auth_service` | welinc-auth | 3001 |
| `welinc_api_gateway` | Nginx gateway | 3000 |
| `welinc_portal` | The SSO portal | 8000 |

It also creates the `welinc-network` Docker network. Always start this file first.

The first time, create the auth tables and seed users from your machine:

```bash
cd welinc-auth && npm install && npx prisma migrate deploy && npm run seed
```

Seed logins are in `welinc-auth/prisma/seeds/users.seed.ts`: one admin per system (`vrms.admin@welinc.com`, `vmms.admin@welinc.com`, `bms.admin@welinc.com`) and more.

## 3. Add your system's compose file

Create `docker-compose.<system>.yml` at the workspace root. `docker-compose.vrms.yml` is a working example of the pattern:

- Give the file its own `name:` (for example `name: <system>-environment`).
- Put every service on the shared network, declared as external:

  ```yaml
  networks:
    welinc-network:
      name: welinc-network
      external: true
  ```

- Use your own database container, never the auth database. Pick host ports nobody uses yet and add them to the repos table in `README.md`. Taken today: 3000, 3001, 3002, 5432, 5433, 6379, 8000, 8001, 10000. The portal already expects VMMS on 8002 and BMS on 8003.
- Give your backend the same `JWT_SECRET` as auth (`dev_secret_key_change_in_production` locally), or no token will verify.
- Point your backend at auth on the internal network: `http://auth-service:3001`.
- Give your web app `VITE_API_BASE_URL: http://localhost:3000`, so every API call goes through the gateway.

Then start it:

```bash
docker compose -f docker-compose.<system>.yml up -d
```

## 4. Route your API through the gateway

The gateway config is `welinc-auth/nginx.conf` (it may move into the workspace later). Each system gets a `location` block that sends its path prefix (for example `/vmms`, `/bms`) to its backend by Docker service name. Copy an existing block, change the path and the target (`set $<system>_backend http://<backend service name>:<port>;`), keep the `OPTIONS` handling for CORS, then test and reload:

```bash
docker exec welinc_api_gateway nginx -t && docker restart welinc_api_gateway
```

This is a change to a shared repo: open a pull request into welinc-auth `development`.

Auth only accepts browser calls from the origins in `CORS_ORIGINS` (in `docker-compose.shared.yml` locally). Make sure your web app's address is listed.

## 5. How login works

1. The user signs in on the portal (port 8000). The portal calls `/auth/login` through the gateway.
2. welinc-auth answers with a JWT that lists the user's roles per system: `roles: [{ role, system }]`, with `system` one of `VRMS`, `VMMS`, `BMS`. It expires after 15 minutes.
3. The portal sends the user to their system's app as `<app URL>/login?token=...`. The app stores it in `localStorage` under `welinc_token` (keep that key: the portal and every app share it).
4. The app sends `Authorization: Bearer <token>` on every API call.
5. The system's backend verifies the token with `JWT_SECRET` and checks the user's role **for that system** on the server. A backend can also call `GET /auth/me?system=<SYSTEM>` on each request, so a deactivated or locked account stops working at once (VRMS does this).

The portal reads each app's URL from `VITE_VRMS_URL`, `VITE_VMMS_URL` and `VITE_BMS_URL`. Update your system's value in the portal's `.env.example` through a pull request.

Users, passwords and roles are managed only in welinc-auth. Admin screens call its `/auth/users` endpoints, which only show users who hold a role in the caller's system. See [shared-repo-changes.md](shared-repo-changes.md) for the rules.

## 6. Working in the shared repos

- Branch from `development` as `feat/<feature>` and open a pull request back into `development`. Never push to `main`.
- Run `npm run lint`, `npm run build` (and `npm run test` in auth) before you open it. CI runs the same checks.
- Read the repo's `AGENTS.md` first. It lists the rules that keep every system working.
- A change that touches more than one repo (token contents, gateway routes, shared API shapes) needs a short spec agreed by the groups first, in `docs/specs/_root/`.
- New environment variables go in `.env.example` only. Never commit a `.env` file. `VITE_*` values reach the browser, so never put a secret in one.

## 7. Keeping up to date

```bash
git pull --ff-only
for d in welinc-*; do git -C "$d" pull --ff-only; done
```

After a pull, run `npm install` where `package.json` changed, `npx prisma migrate deploy` where migrations changed, and `docker compose -f <file> up -d --build` where a Dockerfile or compose file changed. Dependabot opens update pull requests in the shared repos; review them like any other pull request.

## Troubleshooting

- **Every request is 401:** your `JWT_SECRET` doesn't match auth's.
- **Your backend can't reach `auth-service`:** your container isn't on `welinc-network`, or the shared stack isn't running.
- **The gateway answers 502 for your path:** your backend's service name or port in `nginx.conf` doesn't match your compose file.
- **The browser blocks a call with a CORS error:** your app's origin is missing from `CORS_ORIGINS`.
- **413 from the gateway:** the upload is over the route's body limit (1 MB unless the route sets `client_max_body_size`).
- **Sent back to the portal login:** the token expired or you were idle 15 minutes. Sign in again.
