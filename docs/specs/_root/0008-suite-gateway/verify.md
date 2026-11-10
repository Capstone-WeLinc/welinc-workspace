# 0008. Gateway for the whole suite: verify

Steps for `/check verify gateway for the whole suite`. Run them on the local stack. Don't trigger a real email flow: local auth sends real Gmail.

## Automated

1. From the workspace root, run `node infra/gateway/test/check-routes.mjs`. It covers **AC-1** to **AC-21** and exits non zero on any failure. Nothing it starts should be left running afterwards.

## Manual, on the real stack

Start with `docker compose -f docker-compose.shared.yml up -d --build`, then `docker compose -f docker-compose.vrms.yml up -d`.

2. `GET http://localhost:3000/health` answers 200, with the VRMS stack stopped too (**AC-4**).
3. Sign in through the portal at `http://localhost:8000` with a seeded VRMS account, and land in VRMS (**AC-24**).
4. Wait for or force a token refresh in VRMS. The session continues, and the `vrms_rt` cookie is set by way of `localhost:3000` (**AC-24**).
5. Upload a 25 MB attachment to a ticket. It succeeds, and the file opens (**AC-24**).
6. `GET http://localhost:3000/auth/health` and `/vrms/health` answer 200 with their checks. Stop `welinc_vrms_db`: `/vrms/health` answers 503 `HEALTH_CHECK_FAILED` with `"database": "failed"`. Start it again (**AC-22**, **AC-23**).
7. With the VRMS stack stopped, `/vrms/health` answers the JSON 502 and `/auth/health` still answers 200. Start it, and `/vrms/health` recovers within 10 seconds with no gateway restart (**AC-5**, on the real stack).

## Files

8. `welinc-auth/nginx.conf` is gone and `docker-compose.shared.yml` builds from `infra/gateway` (**AC-14**).
9. In an empty folder outside the workspace, run a copy of `clone-all.sh` with `vmms`, and confirm the list; run it with a made up group and confirm the usage error. Clone nothing you don't need to (**AC-25**).
10. The README, `infra/gateway/README.md`, the suite overview and the attachments `AGENTS.md` match (**AC-26**). Contract 0001 is version 3, with sections 2, 3, 11, 12 and 14 amended (**AC-27**).

## Scripts and the one page setup (added 2026-11-10, during the build)

The setup guide was merged into the workspace README, and `scripts/setup.sh`, `start.sh` and `stop.sh` were added. Run these in Git Bash on Windows and in a terminal on the Mac.

11. Fresh machine path: in an empty folder outside the workspace, clone the workspace and follow only the README's "Start here". `sh scripts/setup.sh vrms` finishes with every service ok, and you can sign in at `http://localhost:8000` as `vrms.admin@welinc.com`. Stop your main stack first, since both use the same ports and container names (**AC-24**, **AC-25**, **AC-26**, **AC-28**).
12. Run `sh scripts/setup.sh vrms` a second time on a working setup: it keeps every `.env` file, keeps the keys, applies no migrations and says it kept the VRMS data. A ticket you changed before is still changed (checked on the PC 2026-11-10). (**AC-28**)
13. `sh scripts/stop.sh` leaves no `welinc_` container running; `sh scripts/start.sh vrms` brings them back and prints ok for gateway, auth and vrms (checked on the PC 2026-11-10). (**AC-28**)
14. `sh scripts/start.sh oops` and `sh scripts/setup.sh` with no group print the usage and exit 1. (**AC-28**)
15. With Docker Desktop closed, `sh scripts/start.sh vrms` says to start Docker Desktop and exits 1. (**AC-28**)
16. No link in the workspace points to `docs/integration/setup-guide.md` except spec 0006's history (**AC-26**).

## Owed to staging (spec 0008 of VRMS, not this row)

See the staging item under Follow-up in [index.md](index.md).
