# BMS on the shared services

**Status: built, final checks left.** The BMS repos moved onto the shared login and are on `development`. The checker passed on the pull request branches (login 16 of 16, fleet 5 of 5), and the analytics compose fix is in `docker-compose.bms.yml`.

## Still open

| What | Who |
|---|---|
| Rerun `node scripts/check-system.mjs bms` on `development` (with VMMS on the same stack) | the lead |
| Your group lead confirms in writing that BMS is done | BMS |
| The cross system checks (one sign in across the apps, sign out and deactivation reaching BMS) | the lead |
| Remove `welinc_db` from every BMS setup and archive the old `welinc-backend` repo (read only, history kept) | BMS |
| The hosting ready items in [hosting.md](hosting.md#make-your-service-hosting-ready), before BMS is turned on in staging | BMS |

## How BMS works now

| Before | Now |
|---|---|
| `bms-gateway` read the auth database | `bms-gateway` is NestJS, holds the session routes, reads no database |
| Shared `JWT_SECRET`, HS256 tokens | every process checks welinc-auth's tokens |
| Password form, token in `localStorage` | sign in at the portal; token in memory; refresh token in an HttpOnly cookie on `/bms/session` |
| Drivers, vehicles and garages from `welinc_db` | drivers in dispatch's database; vehicles and garages from the VMMS [fleet API](fleet-api.md) |
| Analytics read `welinc_db` | analytics has its own read model database |
| Tracking links fell back to `JWT_SECRET` | `CUSTOMER_TRACKING_SECRET`, required |

- **Who uses what:** the web app admits Admin, Customer Support and Operations. Drivers and helpers use the BMS phone app (not released yet). welinc-auth enforces this; don't check it yourself.
- **Client keys:** the backend is one client, `bms`, with its key in `welinc-backend-bms/.env`. Analytics is its own client, `bms-analytics`, with its own key. Never log either.
- **Your stack:** `docker-compose.bms.yml` at the workspace root. Start it with `sh scripts/setup.sh bms` (safe to run again).
- **Before a pull request:** `node scripts/check-system.mjs bms --static-only` scans your repos for old login code.

## Ports and names

| Process | Docker service | Port |
|---|---|---|
| `bms-gateway` | `bms-gateway` | 3020 |
| `bms-booking-service` | `bms-booking` | 3021 |
| `bms-dispatch-service` | `bms-dispatch` | 3022 |
| `bms-completion-service` | `bms-completion` | 3023 |
| `bms-analytics-projection` | `bms-analytics-projection` | 3024 |
| `welinc-backend-bms-analytics-ai` | `bms-analytics` | 3025 |
| `welinc-web-bms` | `web-bms` | 8003 |

The browser reaches BMS only through the gateway at `/bms/...`. These paths are fixed because the checker uses them: `/bms/health`, `/bms/session/*`, `/bms/booking`, `/bms/config/vehicles`, `/bms/dispatch/assignments`, `/bms/reports`.

## Where to look

- Session routes and the web app's sign in: [web-login.md](web-login.md)
- Profile, activity, admin and deletion: [account-screens.md](account-screens.md)
- Trucks from VMMS: [fleet-api.md](fleet-api.md)
- Test logins: [seed-accounts.md](seed-accounts.md)
- Every welinc-auth route: `http://localhost:3000/auth/docs`
