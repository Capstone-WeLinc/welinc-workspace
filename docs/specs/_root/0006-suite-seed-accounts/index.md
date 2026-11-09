# 0006. Suite seed accounts from one shared manifest

**Date**: 2026-11-09
**Status**: In Progress

## Summary

Today each system makes its own copy of the same test people, and the copies have drifted apart (one email is two different people). This spec makes one list of seed people, a JSON file in welinc-auth, that every system copies and links to by fixed ids. The list covers every role in every system, several people per role, people who hold two or three systems, and four broken accounts (locked, deactivated, never verified, deleted) for testing. Running the seed again puts seed people back to their listed state without touching anyone else, and it refuses to run on production.

Scope row: [S12 in the shared services scope](../../../scope/_root/shared-services.md#s12-suite-seed-accounts--planned--needs-a-decision--beta). Builds on [0002](../0002-signing-keys-service-identity/index.md) (the client seed it keeps), [0004](../0004-roles-per-system/index.md) (the role catalog it checks against) and [0005](../0005-user-directory/index.md) (the change feed it must not churn).

## Requirements

**User stories**:
- As a developer in any group, I want one list of test people with fixed ids, so my system's seed data points at the same people welinc-auth has.
- As a tester, I want people for every role, people in two and three systems, and broken accounts, so I can test lists, the launcher, lockout and leavers without making accounts by hand.
- As the shared services owner, I want the seed to refuse production and leave hand made accounts alone, so a rerun never destroys real data.

**Acceptance criteria**:

*The manifest*
- **AC-1**: `welinc-auth/prisma/seeds/people.json` is the only source of seed people. Its shape is in *Feature design*. `users.seed.ts` reads it and holds no names, emails or ids of its own. `welinc-auth/prisma/seeds/shared-ids.ts` is deleted.
- **AC-2**: Before opening any transaction, the seed checks the manifest and the catalog, and exits 1 listing every problem (not just the first) when: two people share an id or an email (compared lowercased); an email does not end in `@welinc.com`; an id is not `00000000-0000-4000-8000-` plus 12 digits; a role code is not in that system's catalog (`system_roles`); a person holds more roles in one system than its `maxRolesPerUser`; a person holds the admin role (`isSystemAdmin`) in all three systems; a `password` key is not in `passwords`; or a `state` is not one of the four listed values. Nothing is written.
- **AC-3**: The manifest holds exactly the people in the *Roster* below, with those ids, emails, names, roles, groups, states and passwords. Id `900` (`suite.admin@welinc.com`) is reserved for the S10 platform admin and is not in the manifest yet.
- **AC-4**: Emails follow one rule. Office accounts are `<system>.<role>@welinc.com`, numbered from the second person (`vmms.ops@`, `vmms.ops2@`). Field people are `<role>.<first name>@welinc.com`, with the first name lowercased and its spaces removed (`helper.markanthony@`). Bulk mechanics keep `first.lastN@welinc.com`. Multi system accounts are `multi.<label>@welinc.com`, and the broken accounts are `state.<state>@welinc.com`.

*Account states*
- **AC-5**: After a run, each seed person's row matches their `state`. Every state starts from the active values and changes only the fields named. "The run's time" is one `new Date()` taken once per run and used for every person.
  - `active`: `isActive` true, `deletedAt` null, `lockedAt` null, `failedLoginAttempts` 0, `emailVerified` true.
  - `locked`: `failedLoginAttempts` 5 and `lockedAt` set (kept if already set, else the run's time). Login answers 403 "Account is locked. Contact your Admin to unlock." with `isLocked: true`.
  - `deactivated`: `isActive` false. Login answers 401 "Invalid credentials" (the same answer as an unknown email; today's login gives an inactive account no message of its own).
  - `unverified`: `emailVerified` false. Its password works (today's login does not check `emailVerified`; S13 decides that rule).
  - `deleted`: `deletedAt` set (kept if already set, else the run's time) and `isActive` false; `lockedAt` null, `failedLoginAttempts` 0 and `emailVerified` true as active. Login answers 401 "Invalid credentials". Its role rows stay, as a real delete leaves them.
- **AC-6**: Each person's password is `passwords[person.password]`; that key alone decides, there is no rule by role. The keys are `admin1234`, `chief1234`, `ops1234`, `cs1234`, `mechanic1234`, `driver1234`, `helper1234`. The VRMS chief (`vrms.chief@`) moves from `mechanic1234` to `chief1234`.

*Running the seed*
- **AC-7**: `npm run seed` upserts by id, in one transaction. For each manifest person it sets name, email, contact, password, the state fields of AC-5, and exactly the listed roles (it adds missing role rows and deletes role rows not listed). Users whose id is not in the manifest are not touched, and no session, refresh token or change history row is deleted. Before any write, the seed reads the database as it was before the run and checks for conflicts. It exits 1 naming each email and the id that holds it, and writes nothing, when a manifest email (lowercased) belongs to a user with a different id, soft deleted users included. It does the same when two manifest people would swap emails with each other. A `--reset` run clears the first case.
- **AC-8**: A second run with an unchanged manifest, on a database nobody changed in between, writes no `directory_changes` rows: the password, lock, attempt count and verified flag are not in the feed snapshot, and `updatedAt` is ignored. If someone changed a seed person by hand in between (for example reactivated `state.deactivated@`), the run writes one row for that person putting them back. A `--reset` that recreates the same ids in its one transaction writes no rows for them; a user it removes for good gets one `deleted` row. A run that changes people writes at most one row per changed person (spec 0005, AC-3).
- **AC-9**: `npm run seed -- --reset` first deletes, in this order, every row of `sessions` (their `refresh_tokens` and `authorization_codes` cascade), `user_changes`, `password_reset_tokens`, `user_roles` and `users`, then seeds, all in the same transaction as AC-7. `login_requests` and `directory_changes` have no user foreign key and are left alone. It runs only when `NODE_ENV` is unset, `development` or `test`, `SEED_ALLOW` is unset, and the host in `DATABASE_URL` is `localhost`, `127.0.0.1` or a name with no dot in it (a compose service such as `welinc_auth_db`). Otherwise it exits 1 with "--reset runs only on a local database." and writes nothing.
- **AC-10**: The seed refuses when `NODE_ENV=production` unless `SEED_ALLOW=staging` is set, exiting 1 with "Seeding is off in production. Set SEED_ALLOW=staging only on the staging environment." The guard runs first in `seed.ts`, before the `pg.Pool` is created (today the pool is built at the top of the file, so it moves into `main()`). Any other value of `SEED_ALLOW` counts as unset. With `SEED_ALLOW=staging` the four `group: state` people are skipped, so staging has no broken accounts; the printed table says so. `seed:clients` is not affected by this rule.
- **AC-11**: After the people, `npm run seed` still applies the client registry exactly as spec 0002 AC-13 and spec 0004 AC-18 say. Nothing about clients changes.
- **AC-12**: When it finishes, the seed prints the office, multi system and state accounts grouped by system (email, name, roles, password, state), then one line each with the counts of named mechanics, bulk mechanics, drivers and helpers.

*The copy check*
- **AC-13**: `npm run seed:check -- <path>` in welinc-auth compares the file at `<path>` with `prisma/seeds/people.json` byte for byte (SHA-256). It prints "Matches people.json" and exits 0, or prints "Out of date: copy welinc-auth/prisma/seeds/people.json over <path>" and exits 1. A missing file exits 1 with "No file at <path>". welinc-auth and backend-vrms each add `prisma/seeds/people.json text eol=lf` to `.gitattributes`, so a Windows checkout keeps the same bytes.

*VRMS links to the shared ids*
- **AC-14**: `welinc-backend-vrms/prisma/seeds/people.json` is a byte for byte copy, and AC-13 passes for it. `welinc-backend-vrms/prisma/seeds/shared-ids.ts` becomes a loader that reads that copy and still exports `SEED_IDS`, `SeedPerson`, `VRMS_ADMIN`, `CHIEF`, `NAMED_MECHANICS`, `BULK_MECHANICS` and `seedActor` with the same meaning. The mapping: `VRMS_ADMIN` is id 2, `CHIEF` is id 20, `NAMED_MECHANICS` is `group: mechanic` in id order, `BULK_MECHANICS` is `group: bulk` in id order, and `SEED_IDS` keeps its keys `bmsAdmin` (1), `vrmsAdmin` (2), `vmmsAdmin` (3), `csUser` (4), `opsUser` (5) and `chief` (20). `seedActor(email)` returns the person's id, name and VRMS role from the manifest (`actorRole` null when they hold no VRMS role), and for an email not in the manifest keeps today's fallback (`actorUserId` null, `actorName` = email, `actorRole` null).
- **AC-15**: The VRMS mechanics seed creates one `Mechanic` row for every manifest person holding a VRMS `MECHANIC` or `CHIEF_MECHANIC` role, with `authUserId` = id, email lowercased, name, `role` = that VRMS role (a new column in its `createMany`), and `isActive` false only for `deactivated` and `deleted` people: 77 rows (65 mechanics, 8 chiefs: the 5 VRMS chiefs plus `multi.chief@`, `multi.mixed@` and `multi.lead@`, and the 4 state accounts). It creates no account anywhere. `repairs.seed.ts` reads only active mechanics (`where: { isActive: true }` on its `mechanic.findMany`), so the deactivated and deleted accounts get no ticket history. That one line is its only change.

*The guide*
- **AC-16**: `docs/integration/seed-accounts.md` exists and holds: the email rule, a table of the office, multi system and state accounts (email, name, systems and roles, password, state), the counts and id ranges of mechanics and crew, how to run `seed`, `--reset` and `seed:check`, and the steps VMMS and BMS take in S11 (in *Guide content* below). The README and `docs/integration/setup-guide.md` point to it instead of `users.seed.ts`.

## Decision

**Chosen option**: Option 2: one JSON manifest in welinc-auth, copied by each system, with an upsert seed.

welinc-auth owns a plain data file of seed people with fixed ids. Its seed upserts exactly those people, and every other system copies the file and links its rows to the ids, checked by `seed:check`.

**Implementation skills**: `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`) · `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-cli/`) · `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model**: no schema change in any repo. The seed writes the existing `users` and `user_roles` columns. The new artifact is the manifest file:

```json
{
  "version": 1,
  "passwords": {
    "admin": "admin1234", "chief": "chief1234", "ops": "ops1234", "cs": "cs1234",
    "mechanic": "mechanic1234", "driver": "driver1234", "helper": "helper1234"
  },
  "people": [
    {
      "id": "00000000-0000-4000-8000-000000000002",
      "email": "vrms.admin@welinc.com",
      "name": "Victor Ramos",
      "group": "office",
      "state": "active",
      "password": "admin",
      "contact": null,
      "roles": [{ "system": "VRMS", "role": "ADMIN" }]
    }
  ]
}
```

| Field | Type | Rule |
|---|---|---|
| `version` | number | `1`. Bumped only if the shape changes |
| `passwords` | object | key to plain password, seed only |
| `people[].id` | string | `00000000-0000-4000-8000-` plus the 12 digit id number, unique, never reused |
| `people[].email` | string | unique lowercased, `@welinc.com`, follows AC-4 |
| `people[].name` | string | 1 to 100 characters. Names may repeat; the email is the identity |
| `people[].group` | string | `office`, `mechanic`, `bulk`, `driver`, `helper`, `multi`, `state`. Used by loaders and the printed table |
| `people[].state` | string | `active`, `locked`, `deactivated`, `unverified`, `deleted` |
| `people[].password` | string | a key of `passwords` |
| `people[].contact` | string or null | `+63` phone for drivers and helpers, else null |
| `people[].roles` | array | `{ system, role }`, role codes as in `prisma/catalog/` |

People are listed in id order and written out in full (no generator), so any language can read the file and a diff shows exactly who changed. The 60 bulk mechanics are written out from today's generator output, unchanged.

**Id ranges** (the number at the end of the id):

| Range | Who |
|---|---|
| 1 to 5, 11 to 15, 20 | Today's people, kept (VRMS ticket data points at them) |
| 101 to 199 | VRMS office |
| 201 to 299 | VMMS office |
| 301 to 399 | BMS office |
| 401 to 499 | Multi system accounts |
| 501 to 599 | Broken state accounts |
| 900 | Reserved: S10 platform admin |
| 1001 to 1999 | Bulk mechanics (1001 to 1060 today) |
| 2001 to 2999 | BMS drivers |
| 3001 to 3999 | BMS helpers |

### Roster

Office accounts (`group: office`, `state: active`):

| Id | Email | Name | Roles | Password |
|---|---|---|---|---|
| 2 | vrms.admin@ | Victor Ramos | VRMS Admin | admin1234 |
| 101 | vrms.admin2@ | Teresita Aquino | VRMS Admin | admin1234 |
| 102 | vrms.admin3@ | Gilbert Navarro | VRMS Admin | admin1234 |
| 103 | vrms.admin4@ | Marissa Domingo | VRMS Admin | admin1234 |
| 104 | vrms.admin5@ | Rodrigo Salazar | VRMS Admin | admin1234 |
| 20 | vrms.chief@ | Ramon Villanueva | VRMS Chief Mechanic | chief1234 |
| 111 | vrms.chief2@ | Alfredo Bautista | VRMS Chief Mechanic | chief1234 |
| 112 | vrms.chief3@ | Nestor Pineda | VRMS Chief Mechanic | chief1234 |
| 113 | vrms.chief4@ | Lorna Galang | VRMS Chief Mechanic | chief1234 |
| 114 | vrms.chief5@ | Efren Lacson | VRMS Chief Mechanic | chief1234 |
| 3 | vmms.admin@ | Valerio Mercado | VMMS Admin | admin1234 |
| 201 | vmms.admin2@ | Cristina Velasco | VMMS Admin | admin1234 |
| 202 | vmms.admin3@ | Dominic Sison | VMMS Admin | admin1234 |
| 203 | vmms.admin4@ | Rowena Manalo | VMMS Admin | admin1234 |
| 204 | vmms.admin5@ | Leonardo Abad | VMMS Admin | admin1234 |
| 210 | vmms.ops@ | Oscar Ramos | VMMS Operations | ops1234 |
| 211 | vmms.ops2@ | Imelda Fajardo | VMMS Operations | ops1234 |
| 212 | vmms.ops3@ | Rafael Ilagan | VMMS Operations | ops1234 |
| 213 | vmms.ops4@ | Josefina Dela Paz | VMMS Operations | ops1234 |
| 214 | vmms.ops5@ | Noel Samonte | VMMS Operations | ops1234 |
| 220 | vmms.chief@ | Ramon Garcia | VMMS Chief Mechanic | chief1234 |
| 221 | vmms.chief2@ | Diego Martinez | VMMS Chief Mechanic | chief1234 |
| 222 | vmms.chief3@ | Ariel Macaraeg | VMMS Chief Mechanic | chief1234 |
| 223 | vmms.chief4@ | Benigno Tuazon | VMMS Chief Mechanic | chief1234 |
| 224 | vmms.chief5@ | Celso Ramirez | VMMS Chief Mechanic | chief1234 |
| 1 | bms.admin@ | Bernardo Mendoza | BMS Admin | admin1234 |
| 301 | bms.admin2@ | Evangeline Cortez | BMS Admin | admin1234 |
| 302 | bms.admin3@ | Patrick Yap | BMS Admin | admin1234 |
| 303 | bms.admin4@ | Gemma Lualhati | BMS Admin | admin1234 |
| 304 | bms.admin5@ | Raul Tan | BMS Admin | admin1234 |
| 5 | bms.ops@ | Oscar Santos | BMS Operations | ops1234 |
| 311 | bms.ops2@ | Melchor Agustin | BMS Operations | ops1234 |
| 312 | bms.ops3@ | Liza Montemayor | BMS Operations | ops1234 |
| 313 | bms.ops4@ | Hernani Cabral | BMS Operations | ops1234 |
| 314 | bms.ops5@ | Susana Ventura | BMS Operations | ops1234 |
| 4 | bms.cs@ | Clara Reyes | BMS Customer Support | cs1234 |
| 321 | bms.cs2@ | Angelica Ong | BMS Customer Support | cs1234 |
| 322 | bms.cs3@ | Mylene Serrano | BMS Customer Support | cs1234 |
| 323 | bms.cs4@ | Jonathan Lim | BMS Customer Support | cs1234 |
| 324 | bms.cs5@ | Kristine Valencia | BMS Customer Support | cs1234 |

Id 5 changes email from `ops.user@` to `bms.ops@`, and id 4 from `cs.user@` to `bms.cs@`. `ops.user@` and `cs.user@` no longer exist. VMMS's Oscar Ramos becomes `vmms.ops@`, and its chief mechanics `vmms.chiefmech@` and `vmms.chiefmech2@` become `vmms.chief@` and `vmms.chief2@`.

Mechanics (`state: active`, password `mechanic1234`, roles VRMS Mechanic and VMMS Mechanic):
- `group: mechanic`, ids 11 to 15: `mech.juan@` Juan dela Cruz, `mech.pedro@` Pedro Santos, `mech.rommel@` Rommel Cruz, `mech.isabel@` Isabel Reyes, `mech.carl@` Carl Santos (unchanged).
- `group: bulk`, ids 1001 to 1060: today's 60, same names and emails.

Multi system accounts (`group: multi`, `state: active`):

| Id | Email | Name | Roles | Password | Tests |
|---|---|---|---|---|---|
| 401 | multi.chief@ | Teodoro Manalastas | VRMS Chief Mechanic, VMMS Chief Mechanic | chief1234 | Same role in two systems |
| 402 | multi.admin@ | Felicidad Roxas | VRMS Admin, VMMS Admin | admin1234 | The admin elsewhere protection in `user-scope.ts`; an S10 case |
| 403 | multi.mixed@ | Arturo Pangilinan | VRMS Chief Mechanic, VMMS Operations | chief1234 | Different screens per system for one login |
| 404 | multi.lead@ | Corazon Villareal | VRMS Chief Mechanic, VMMS Operations, BMS Operations | chief1234 | Launcher with three systems |

With the mechanics (two systems) and everyone else (one system), the S4 launcher has one, two and three system accounts. A portal login that names no system picks one in the fixed order of `PICK_ORDER` in `welinc-auth/src/auth/tokens/login-system.ts` (unchanged), so these accounts always land on the same system until S4 adds the launcher.

The five VMMS chiefs (ids 220 to 224) replace VMMS's own `vmms.chiefmech@` and `vmms.chiefmech2@`. Today's welinc-auth seed has no VMMS chief at all.

Broken state accounts (`group: state`, password `mechanic1234`, roles VRMS Mechanic and VMMS Mechanic, so VRMS can test them now and VMMS after S11):

| Id | Email | Name | State |
|---|---|---|---|
| 501 | state.locked@ | Lito Concepcion | locked |
| 502 | state.deactivated@ | Nonoy Evangelista | deactivated |
| 503 | state.unverified@ | Bong Rivera | unverified |
| 504 | state.deleted@ | Junjun Marquez | deleted |

BMS crew (`state: active`): the 12 drivers and 20 helpers of `welinc-backend-bms/bms-dispatch-service/scripts/seed-crew.mjs` (branch `latest-bms-backend`, read 2026-11-09), in that file's order, with the same names and the same `contact` phones.
- Drivers: `group: driver`, ids 2001 to 2012, BMS Driver, `driver1234`, emails `driver.<first>@` (`driver.ramon@` for Ramon Dela Cruz up to `driver.antonio@` for Antonio Flores).
- Helpers: `group: helper`, ids 3001 to 3020, BMS Helper, `helper1234`, emails `helper.<first>@` (`helper.markanthony@` for Mark Anthony Cruz up to `helper.bryan@` for Bryan Galang). Helper n matches BMS `emp_id` `HLP-00n`, and driver n matches `DRV-00n`. The 32 first names are all different today; a later clash adds the last name (`helper.mark.cruz@`), and AC-2 refuses a duplicate email anyway.

Totals: 40 office, 5 named and 60 bulk mechanics, 4 multi, 4 state, 12 drivers and 20 helpers: 145 people.

**Seed flow** (welinc-auth `prisma/seed.ts`):
1. Environment guard (AC-9, AC-10), before the pool is created (the pool moves from the top of the file into `main()`).
2. Read and check the manifest against itself, then against the catalog read from `system_roles` (AC-2). Refuse with "Run npm run db:deploy first." when the catalog is empty, as `seed:clients` does.
3. Hash each distinct password once with argon2, outside the transaction.
4. One transaction (timeout 120 s): with `--reset`, the wipe; then the email conflict check (AC-7); then each person in id order: upsert the user by id, then set their role rows to exactly the listed ones.
5. `seedClients` as today (AC-11).
6. Print the table (AC-12).

**Interface surface**: no HTTP route changes. Commands:

| Command | Repo | Does | Exits 1 when |
|---|---|---|---|
| `npm run seed` | welinc-auth | Upsert seed people, then clients | AC-2, AC-7 conflict, AC-10 |
| `npm run seed -- --reset` | welinc-auth | Wipe all users, then the above | AC-9, plus the above |
| `npm run seed:check -- <path>` | welinc-auth | Compare a copy with `people.json` | AC-13 |
| `npm run seed` | backend-vrms | As today, now reading its copy; active mechanics only on tickets | the copy is missing or not valid JSON |

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| Upsert user | id, email, name, contact | manifest person |
| Upsert user | `passwordHash` | argon2 of `passwords[person.password]` |
| Upsert user | `isActive`, `emailVerified`, `failedLoginAttempts` | derived from `state` (AC-5) |
| Upsert user | `lockedAt`, `deletedAt` | existing value if set, else the run's `new Date()`, for `locked` and `deleted` only; else null |
| Role rows | system, role | `person.roles` |
| Validation | allowed role codes, `maxRolesPerUser`, admin role per system | `system_roles` and `systems` (spec 0004) |
| Guard | environment | `NODE_ENV`, `SEED_ALLOW`, the `--reset` argument |
| `seed:check` | match | SHA-256 of both files |
| VRMS `Mechanic` row | `authUserId`, email, name, `role`, `isActive` | manifest person, their VRMS role, `state` (AC-15) |
| VRMS `seedActor` | `actorRole` | the person's VRMS role in the manifest |
| Printed table and guide | every column | manifest |
| Crew names and phones | name, contact | BMS `seed-crew.mjs`, copied once into the manifest |

**Key invariants**:
- One id is one person and one email, in every system, forever. An id is never reused for someone else; a removed person's id stays retired.
- The manifest in welinc-auth wins. A copy that differs is out of date, never a second source.
- The seed only ever writes people whose id is in the manifest, unless `--reset` runs locally.
- No seed person is an admin in all three systems.
- The whole people step is one transaction: it fully applies or writes nothing.

**Security model**:
- The passwords are public test values, committed on purpose. That is safe only because the seed never runs on production (AC-10), and staging needs the explicit `SEED_ALLOW=staging`.
- Staging gets no broken state accounts (AC-10).
- Each distinct password is hashed once and the hash is shared by everyone with that password, so the salts repeat across seed people. Acceptable for public test passwords only.
- Staging seed accounts are reachable from the internet once hosted. The staging gateway address must not be shared outside the team and panel, and S10 or hosting (spec 0008) should decide whether staging seed passwords differ. Tracked in Follow-up.
- Seed writes go straight to the database, so they write no `user_changes` rows and skip the email domain check (already true today).
- `multi.admin@` (Admin in VRMS and VMMS) is protected by the admin elsewhere rule, so neither a VRMS nor a VMMS admin can reset its password or email through the API. That is intended, and it is a test case.

**Configuration required**:
- `SEED_ALLOW`: set to `staging` only in the staging environment's welinc-auth settings, to let `npm run seed` run there with `NODE_ENV=production`. Add it to `welinc-auth/.env.example` with that comment. Never set on production.

### Guide content

`docs/integration/seed-accounts.md` holds:
1. What the manifest is, where it lives, and that welinc-auth's copy wins.
2. The email rule (AC-4) and the id ranges.
3. The office, multi system and state account tables above, with passwords. The bulk mechanics and crew as counts and id ranges only.
4. Commands: `seed`, `--reset` (local only), `seed:check`, and `SEED_ALLOW` on staging.
5. What each broken account shows at login today (locked: the locked message; deactivated and deleted: "Invalid credentials"; unverified: signs in), that they exist only locally, and that S13 decides the unverified rule.
6. For VMMS and BMS, done as part of S11, not before:
   - Copy `people.json` into your seed folder and run `npm --prefix ../welinc-auth run seed:check -- <your copy>` from the workspace after each pull.
   - Stop creating users and roles in your seed. Link your rows to the manifest ids: VMMS `Mechanic.userId`, work order and audit actor ids; BMS `drivers` and `helpers` gain a user id column set from the manifest (driver n is `DRV-00n`, helper n is `HLP-00n`), and booking actor ids.
   - Use the manifest emails. VMMS: `ops.user@` becomes `vmms.ops@`, `vmms.chiefmech@` and `vmms.chiefmech2@` become `vmms.chief@` and `vmms.chief2@`. BMS: `cs.user@` becomes `bms.cs@`, `ops.user@` becomes `bms.ops@`, and crew emails move from `@welinc.ph` to the manifest's `@welinc.com`.
   - Need a new person or role? Ask the shared services owner to add them to the manifest; never add people only in your own seed.

**Critical test scenarios**:
- Happy path: fresh database, `db:deploy`, `seed`. 145 users with the roster's roles; `vrms.chief@` signs in with `chief1234`; `seed:check` passes on the VRMS copy; the VRMS seed then runs and makes 77 `Mechanic` rows, none of the 2 inactive ones on a ticket. Verifies **AC-1**, **AC-3**, **AC-6**, **AC-13**, **AC-14**, **AC-15**
- Rerun: `seed` twice; the second writes no `directory_changes` rows, keeps a hand made portal user and its sessions. Then activate `state.deactivated@` by hand and `seed` again: one `deactivated` row. Then `--reset`: no rows for seed ids, one `deleted` row for the hand made user. Verifies **AC-7**, **AC-8**, **AC-9**
- Repair: lock `mech.juan@` with five wrong passwords and add a stray role by hand, then `seed`; Juan is unlocked with only his two Mechanic roles. Verifies **AC-5**, **AC-7**
- Old database: a database seeded by today's seed, then `seed`; id 5 is now `bms.ops@` with one `updated` feed row; no duplicates. Verifies **AC-7**, **AC-8**
- Email conflict: create a user `bms.cs2@welinc.com` in the portal first, then `seed`; exits 1 naming that email, nothing written; `--reset` then succeeds. Swap the emails of ids 321 and 322 in the manifest; the seed refuses. Verifies **AC-7**, **AC-9**
- States: `state.locked@` gets 403 with `isLocked`, `state.deactivated@` and `state.deleted@` get 401 "Invalid credentials", `state.unverified@` signs in; VRMS shows Lito active and Nonoy and Junjun inactive. Verifies **AC-5**, **AC-15**
- Bad manifest: a duplicate email, a role `VRMS DRIVER`, two VRMS roles on one person, and an admin in three systems in one edit; the seed lists all four problems and writes nothing. Verifies **AC-2**
- Guard: `NODE_ENV=production` refuses before any connection; with `SEED_ALLOW=staging` it runs and seeds 141 people (no state accounts); `--reset` with `SEED_ALLOW=staging` refuses; `--reset` with `DATABASE_URL` pointing at `db.example.com` refuses. Verifies **AC-9**, **AC-10**
- Clients: after `seed`, `oauth_clients` matches the result of `seed:clients` alone. Verifies **AC-11**
- Stale copy: edit one character in the VRMS copy; `seed:check` exits 1 with the copy hint. Verifies **AC-13**

## Build plan

Tracer Bullet: the first slice runs the whole path (manifest, checks, upsert, VRMS copy and loader, copy check) with today's people only, so the pipeline is proven before the roster grows.

1. **Thin thread.** welinc-auth: `people.json` with today's 71 people exactly as seeded now (same ids, emails, names, roles, passwords, all `active`), a typed loader and the AC-2 checks (pure functions with unit tests), the environment guard first in `main()` with the pool moved inside it, the upsert by id with exact role rows and the email conflict check in one transaction, `seedClients` after it, delete `shared-ids.ts`, `seed:check` script, `SEED_ALLOW` in `.env.example`, the `.gitattributes` line. backend-vrms: copy `people.json` and its `.gitattributes` line, rewrite `shared-ids.ts` as the loader with the AC-14 mapping, the mechanics seed derived from roles and state with the `role` column, and the active only filter in `repairs.seed.ts`. Run both seeds twice on a local database and confirm no feed rows on the second. Satisfies **AC-1**, **AC-2**, **AC-7**, **AC-8**, **AC-10**, **AC-11**, **AC-13**, **AC-14**, **AC-15**
2. **The full roster.** Add every person in *Roster*, rename ids 4 and 5, the per role passwords (VRMS chief to `chief1234`), the four state accounts with their field values, the crew with phones. Copy the new file into backend-vrms (`seed:check` passes); update the VRMS printed login lines. Satisfies **AC-3**, **AC-4**, **AC-5**, **AC-6**, **AC-15**
3. **Reset, staging and output.** `--reset` with its ordered wipe and both guards; skipping state accounts under `SEED_ALLOW=staging`; the printed table and counts. Satisfies **AC-9**, **AC-10**, **AC-12**
4. **The guide.** Write `docs/integration/seed-accounts.md` per *Guide content*; point the README and setup guide at it. Lint, build and test in welinc-auth and backend-vrms. Satisfies **AC-16**

## Migration plan

**Strategy**: no schema migration. A data change applied by rerunning the seed.
**Phases**:
1. Merge welinc-auth and backend-vrms together (the VRMS loader needs its copy of the new file).
2. Each developer runs `npm run seed` in welinc-auth (upsert renames ids 4 and 5 in place), then reseeds VRMS. If the email conflict check refuses (a hand made account took a new seed email), run `--reset`.
**Rollback**: revert both merges, then `npm run seed -- --reset` with the old seed restores today's people.
**Risks**: VRMS seed data refers to ids, so it survives, but anyone used to `ops.user@`, `cs.user@` or the VRMS chief's `mechanic1234` will fail to sign in until they read the guide. The other groups' own seeds keep the old emails until S11, which is accepted: they don't use welinc-auth's accounts yet.

## Consequences

**Positive**:
- One email is one person across the suite, and the drift can't come back silently: `seed:check` catches a stale copy.
- Every role has several people, so lists, reassigning and the last admin rule are testable in every system.
- The launcher, lockout, leavers and S13's unverified rule all have ready accounts.
- A rerun is safe on staging and keeps hand made test accounts.

**Negative / tradeoffs**:
- Copies still exist. A group that forgets to recopy runs with old people until `seed:check` is run; nothing runs it automatically.
- 145 people written out in JSON is a long file to edit by hand, and a reviewer must read it carefully.
- Upsert is not a clean slate: junk accounts stay until `--reset` or a manual delete.
- The renamed emails and the chief's new password break habits and the handoff notes.
- The broken state accounts reset on every run, so a tester who unlocks `state.locked@` finds it locked again after a reseed (intended, but surprising).

**Neutral**:
- VMMS and BMS keep their own seeds until S11; their guide is ready now.
- Crew names and phones are copied once from BMS. If BMS changes its crew seed before S11, the manifest wins and BMS follows it.

## Follow-up

- [ ] S11: the migration guide links to `docs/integration/seed-accounts.md` step 6, and each group's move includes switching its seed.
- [ ] S10: add `suite.admin@welinc.com` (id 900) to the manifest when the platform admin exists.
- [ ] S13: decide the sign in rule for unverified accounts; `state.unverified@` is the test account.
- [ ] Hosting (spec 0008): decide whether staging seed passwords differ from the public ones, and set `SEED_ALLOW=staging` only there.
- [ ] `/sync`: update `welinc-auth/AGENTS.md` (`prisma/seeds/` row, `seed:check`, `--reset`, `SEED_ALLOW`) and `welinc-backend-vrms/AGENTS.md` (the seed reads its manifest copy).
- [ ] Update the handoff's "Test data and sign in" note (chief password, renamed emails) when this ships.
