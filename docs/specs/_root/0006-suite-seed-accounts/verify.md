# Verify: suite seed accounts · spec 0006 · updated 2026-11-09
_Steps derived from spec 0006 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Run the database steps on a throwaway database so your real accounts stay as they are: `docker exec welinc_auth_db createdb -U welinc_auth_user seedtest`, then in welinc-auth `export DATABASE_URL='postgresql://welinc_auth_user:welinc_auth_pass@localhost:5432/seedtest?schema=public'` and `npm run db:deploy`. For VRMS, the same with `welinc_vrms_db`, port 5433 and `npx prisma migrate deploy`. Drop both afterwards. Steps marked (done 2026-11-09) were already run during `/develop` on such databases.

## Commands
- [x] `npm run seed` on a fresh database → 145 users, the roster's roles, printed table grouped by system → AC-1, AC-3, AC-12 (done 2026-11-09)
- [x] `npm run seed` again → 0 new `directory_changes` rows → AC-8 (done 2026-11-09)
- [x] A database seeded by the old seed (71 people), then the new `seed` → `bms.cs@` and `bms.ops@` are renamed in place, one `updated` row each, 74 `created`, 145 users, no duplicates → AC-7, AC-8 (done 2026-11-09 on the first ids; since the id change an older database stops on an email conflict and needs `seed -- --reset`, which the reset step covers)
- [x] Add a hand made user with a role and a live session, then `seed` → user and session still there, 0 feed rows → AC-7 (done 2026-11-09)
- [x] Lock `mech.juan@` and add a stray `BMS HELPER` role by hand, then `seed` → Juan has 0 attempts, no lock, only VRMS and VMMS Mechanic → AC-5, AC-7 (done 2026-11-09)
- [x] Set `state.deactivated@` active by hand, then `seed` → one `deactivated` row for that person → AC-8 (done 2026-11-09)
- [x] Delete the id of `bms.cs2@` and give a hand made user `bms.cs2@welinc.com`, then `seed` → exits 1 naming that email and both ids, nothing written → AC-7 (done 2026-11-09)
- [x] `seed -- --reset` with a hand made user present → one `deleted` row for that user, none for the 145 seed people, sessions gone → AC-8, AC-9 (done 2026-11-09, after the fix in `a0ef7f7`)
- [x] `NODE_ENV=production npm run seed` and with `SEED_ALLOW=yes` → the production refusal, before any connection → AC-10 (done 2026-11-09)
- [x] `NODE_ENV=production SEED_ALLOW=staging npm run seed` → 141 people applied, "Broken state accounts: skipped" → AC-10 (done 2026-11-09)
- [x] `SEED_ALLOW=staging npm run seed -- --reset`, and `--reset` with `DATABASE_URL` on `db.example.com` → "--reset runs only on a local database." → AC-9 (done 2026-11-09)
- [x] After `seed`, compare `oauth_clients` with a run of `npm run seed:clients` alone → identical rows → AC-11 (done 2026-11-09 by /check, 8 rows identical)
- [x] Edit one person in a scratch copy of `people.json` (a duplicate email, a `VRMS DRIVER` role, two VRMS roles, an admin in all three systems) and point the seed at it → all four problems listed, nothing written → AC-2 (unit tested in `src/auth/seed/manifest.spec.ts`; the real run is optional) (done 2026-11-09 by /check, 4 problems listed, 0 users written; edit was temporary and restored)
- [x] From the workspace, `npm --prefix welinc-auth run seed:check -- welinc-backend-vrms/prisma/seeds/people.json` → "Matches people.json", exit 0 → AC-13, AC-14 (done 2026-11-09)
- [x] Change one character in a copy, run `seed:check` on it → "Out of date: copy welinc-auth/prisma/seeds/people.json over <path>", exit 1; a missing path → "No file at <path>" → AC-13 (done 2026-11-09 by /check)
- [x] VRMS `npm run seed` with the full copy → 77 `Mechanic` rows (8 chiefs), 2 inactive (`state.deactivated@`, `state.deleted@`) with no ticket assignments → AC-15 (done 2026-11-09)
- [x] Grep backend-vrms seeds for `ops.user@` and `cs.user@` → none; `seedActor('vrms.chief@welinc.com').actorRole` is `CHIEF_MECHANIC`, and an unknown email gives `actorUserId` null → AC-14 (done 2026-11-09 by /check)

## UI / manual (on your real local databases, after you run the seeds there)
- [x] Portal login `vrms.chief@welinc.com` / `chief1234` → lands in VRMS as Chief Mechanic; `mechanic1234` no longer works → AC-6 (done 2026-11-09 by /check, through the gateway `/auth/login`)
- [x] Portal login `state.locked@` → "Account is locked. Contact your Admin to unlock." → AC-5 (done 2026-11-09 by /check, gateway)
- [x] Portal login `state.deactivated@` and `state.deleted@` → "Invalid credentials" → AC-5 (done 2026-11-09 by /check, gateway)
- [x] Portal login `state.unverified@` / `mechanic1234` → signs in → AC-5 (done 2026-11-09 by /check, gateway)
- [x] `bms.ops@` / `ops1234` and `bms.cs@` / `cs1234` sign in; `ops.user@` and `cs.user@` don't → AC-3, AC-4 (done 2026-11-09 by /check, gateway)
- [x] `multi.lead@` / `chief1234` → signs in (lands on the `PICK_ORDER` system until S4) → AC-3 (done 2026-11-09 by /check, gateway; it landed on VRMS)
- [x] VRMS Users page → Lito Concepcion and Bong Rivera active, Nonoy Evangelista and Junjun Marquez inactive → AC-15 (done 2026-11-09 by /check in the browser: Lito shows Locked, Bong Setup pending, Nonoy under Inactive; Junjun is not listed because the page hides deleted people, so the step's last name is a wording slip)
- [x] Open `docs/integration/seed-accounts.md` → email rule, account tables, counts and id ranges, commands, broken account answers, the S11 steps; README and setup guide link to it → AC-16 (headings and both links present, checked 2026-11-09)

## Value sourcing
- [x] `passwordHash`: each key signs in with its own password (`driver.ramon@` / `driver1234`, `helper.bryan@` / `helper1234`) (done 2026-11-09 by /check)
- [x] `isActive`, `emailVerified`, `failedLoginAttempts`: check the four `state.*` rows in `users` match AC-5 (done 2026-11-09 by /check)
- [x] `lockedAt`, `deletedAt`: note the time on `state.locked@` and `state.deleted@`, reseed, and see the same time (done 2026-11-09 by /check, same timestamps after a second seed)
- [x] `contact`: `driver.ramon@` is `+639171234501`, `helper.markanthony@` is `+639172350001`; office people are null (done 2026-11-09 by /check)
- [x] Catalog validation: a role added to the manifest but not in `prisma/catalog/` is refused by the seed (done 2026-11-09 by /check, refused with 'role BMS HELPER is not in the catalog', 0 users)
- [x] VRMS `Mechanic.role`: `multi.mixed@` is `CHIEF_MECHANIC`, `mech.juan@` is `MECHANIC` (done 2026-11-09 by /check)

## Acceptance-criteria coverage
- AC-1: manifest is the only source, `shared-ids.ts` deleted in welinc-auth (code), fresh seed step
- AC-2: unit tests plus the bad manifest step
- AC-3, AC-4: fresh seed count and the login steps
- AC-5: repair step, state login steps, value sourcing
- AC-6: chief login and the per key password step
- AC-7: old database, hand made user, repair and conflict steps
- AC-8: rerun, hand change and reset steps
- AC-9: reset and guard steps
- AC-10: production and staging steps
- AC-11: the clients comparison step
- AC-12: the printed table on the fresh seed
- AC-13: the two `seed:check` steps
- AC-14: the copy check and the `seedActor` step
- AC-15: the VRMS seed step and the Users page step
- AC-16: the guide step
