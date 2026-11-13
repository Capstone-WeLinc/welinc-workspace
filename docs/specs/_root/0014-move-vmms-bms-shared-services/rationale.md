# 0014. Move VMMS and BMS onto the shared services: rationale

The decision record for [index.md](index.md). `/develop` skips this file.

## Context

> ⚠️ Premise note: this row started as "move their logins over" and now also retires the old Capstone 1 database, which means a VMMS fleet API and BMS data moves (your call, 2026-11-13). That pulls part of VRMS feature 56 (domain contracts) into the cutover with about two and a half weeks to the deadline. The risk is that the fleet work, not the login work, decides when S11 closes. The guides keep the two apart (the fleet items are their own checklist block), so a group can pass the login checks first and the fleet checks after.

Contract 0001 (version 7) and the shared rows S2 to S10 and S12 to S14 are built and proven on VRMS. VMMS and BMS still run on what they had in Capstone 1. A read only check on 2026-11-13, after pulling every clone, found:

- **VMMS** (active, pushed on 2026-11-13): its own auth module (23 routes under `/auth`, HS256 with `JWT_SECRET`, the system guessed from `Origin` and the path), its own `users`, `user_roles`, `refresh_tokens`, `login_activities` and plaintext `password_reset_tokens`, phone codes kept in memory and sent through Semaphore, and a second admin surface under `/users`. About 40 user id columns, 9 with foreign keys to its `users`, the rest plain uuids; the new fuel and maintenance audit tables also copy `actorEmail`. A web vs mobile rule (`client-platform.ts`): Admin and Operations on the web only, Mechanic and Chief Mechanic on the phone only. Its web app takes `?token=` from the portal into `localStorage` and passes the token in the URL to VRMS. Its analytics service checks callers through VMMS's `/auth/me`. No global prefix, port 3000 (the suite gateway's), no compose file. 69 seed users with random ids; no real users.
- **BMS** (quiet since 2026-11-06): five processes behind a 160 line plain Node gateway (`/api` strip, port 3005, bound to `127.0.0.1`), each verifying HS256 tokens with `JWT_SECRET`. The gateway and booking read `users`, `user_roles` and `user_activity_logs` from `welinc_db`, the old Capstone 1 database on port 5433, and dispatch reads and writes `vehicles`, `drivers` and `garages` there; the analytics projection writes its read model there too. The web app posts a password to `/auth/login`, decodes the token with `jwt-decode` and keeps it in `localStorage`. Drivers and helpers are crew records with no login and no screens; BMS web has screens for Admin, Customer Support and Operations only. No Dockerfiles, no compose file, no user seed.
- **The gateway** already routes `/vmms/`, `/vmms/analytics/` and `/bms/` to `vmms-backend:3010`, `vmms-analytics:3011` and `bms-gateway:3020`, none of which exist yet. `docker-compose.vrms.yml` publishes `vrms-db` on 5433, the port `welinc_db` uses.
- **Open items from earlier rows**: contract 0001 promises `/auth/users/lookup` at 30 calls a minute, but nothing enforces it; spec 0013 deprecated the bearer admin routes until VMMS and BMS move.

The forces: the other groups own their repos and the shared owner may not edit them; the deadline is the end of November 2026 with staging still waiting on VRMS feature 26; nobody has real users, so the data side is free; and S11 is where a mistake exposes every system's sign in.

## Options considered

### Option 1: Move kit, groups move themselves in parallel (chosen)

You ship the shared changes, a guide per system, a checker that tests a system against the contract, and the VRMS code to copy; each group changes its own repos, both at once; done is the checker plus your cross check.

**Pros**: respects repo ownership; the checker makes done objective and reusable; nothing waits on the slower group.
**Cons**: two groups learn the same code at once; your cross checks bunch up near the deadline; three copies of the auth code.

### Option 2: You open the pull requests in their repos

You make the changes in VMMS and BMS yourself and they review.

**Pros**: fastest path to a working suite; one person who knows the contract writes every copy.
**Cons**: breaks the "never edit another group's repos" rule (and your settings block it); the groups don't learn their own login; you become the bottleneck for three systems.

### Option 3: Guides only, one group at a time (contract 0001's order)

Written guides with no checker, BMS first, then VMMS.

**Pros**: least to build; proves the guide on one group before the other.
**Cons**: done is a judgment call; VMMS, the active group, waits on BMS, the quiet one; a missed leftover (a token in `localStorage`) passes unseen.

## Rationale

Option 1 is the only one that fits both the ownership rule and the deadline. Option 2 is faster for one person but breaks the rule the suite runs on and leaves the groups unable to maintain their own sign in. Option 3 saves the checker's cost but makes "moved" a matter of trust, and in the riskiest part of the suite trust isn't a test. Running the groups in parallel removes the queue that contract 0001's order would put VMMS behind BMS; nothing in one move depends on the other, except BMS's fleet reads, which only need VMMS's three read routes.

The sub decisions follow from the same forces:

- **Reseed, no import.** No deployment holds a real person or real work, so mapping 40 VMMS id columns by email would be work with nothing to protect. `people.json` already holds every seed person under fixed ids.
- **Web vs app rules in welinc-auth.** Contract rule 5 says a system's role rules live in the catalog, not its code. `allowed_roles` already exists (spec 0004) and already limits the phone apps; limiting the web clients is the other half. Splitting the launcher answer keeps the portal honest: a mechanic isn't offered a VMMS card that would refuse them, and someone who holds a system only on a phone is told so instead of "no access". BMS gets the same rule because its web app has no screens for drivers and helpers.
- **Copy, don't package.** The security work is in `jose`; the VRMS folders are about 2,400 lines of glue. A package from private repos would need a GitHub token in every build and CI run and someone to cut releases, and BMS's gateway isn't Nest anyway. The checker tests behavior, so a wrong copy fails no matter who made it.
- **BMS's gateway becomes NestJS.** It is BMS's backend for frontend (the one server the browser talks to), and that is where the login belongs, as contract 0001 already says (`bms` is `bms-gateway`). S11 already deletes or rewrites most of `server.mjs` (the `/auth` bridge, the auth database reads, the prefix, the port, the bind address); what carries over is the route table and the proxy loop. Booking hosting the routes stays as the fallback.
- **All of `welinc_db` in S11.** The VRMS database already claims its port, the old database holds the BMS auth copy's users, and "no system reads another system's database" is the suite's architecture rule. Retiring it in one row is cleaner than a half state where BMS still reads trucks from a database nobody owns.
- **Live fleet reads.** A cached copy could let BMS dispatch a truck VMMS just sent for maintenance. A 30 s list cache keeps the pick list cheap, and the fresh read at assignment keeps the decision right. A second change feed would double the work for no gain at this scale.
- **The lookup limit.** Ten lines close an email enumeration path and make the contract true.
- **Remove the bearer admin routes here.** Once both groups pass, they have no caller; a dead admin write surface is an attack path with no user. Doing it in the last slice closes the cutover in one spec.

## Evidence: the 2026-11-13 pull

Pulled every VMMS and BMS clone on 2026-11-13. BMS has no commits since 2026-11-06 (one web branch, `feature/scheduling-dropdown-updates`, touches only the user page's selects). VMMS has 8 backend, 6 web and 4 mobile commits since then, mostly fuel and maintenance costing. Auth related: `GET /auth/me/login-activity` added to its auth copy, its `/users` controller made Admin only, about 12 new user id columns and `actorEmail` copies on the new audit tables, `getMobileAccessRole` filtered to VMMS roles, and the web client clearing its token on 401 only (not 403).
