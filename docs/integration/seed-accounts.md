# Seed accounts

The test people every WeLinc system shares, from [spec 0006](../specs/_root/0006-suite-seed-accounts/index.md). You sign in with these through the portal at `http://localhost:8000`.

## The manifest

- `welinc-auth/prisma/seeds/people.json` is the one list of seed people for the whole suite: 145 people, each with a fixed id, one email, their roles in each system, a password and a state.
- `npm run seed` in welinc-auth creates those people. Every other system copies the file and links its own rows (mechanics, crew, actor ids) to the same ids. It never creates accounts of its own.
- welinc-auth's file always wins. A copy that differs is out of date, never a second source. Need a new person or role? Ask the shared services owner to add them to the manifest.
- An id is one person forever. A removed person's id is retired, never reused.

## Email rule

| Who | Pattern | Example |
|---|---|---|
| Office accounts | `<system>.<role>@welinc.com`, numbered from the second person | `vmms.ops@`, `vmms.ops2@` |
| Field people (drivers, helpers, named mechanics) | `<role>.<first name>@welinc.com`, lowercased, spaces removed | `helper.markanthony@` |
| Bulk mechanics | `first.lastN@welinc.com` | `danilo.ramos1@` |
| People in more than one system | `multi.<label>@welinc.com` | `multi.lead@` |
| Broken accounts | `state.<state>@welinc.com` | `state.locked@` |

Every seed email ends in `@welinc.com`. The seed writes straight to the database, so the email domain check doesn't apply to it.

## Id ranges

Each id is `00000000-0000-4000-8000-` plus the 12 digit number below.

| Range | Who |
|---|---|
| 1 to 5, 11 to 15, 20 | The first seed people, kept (VRMS ticket data points at them) |
| 101 to 199 | VRMS office |
| 201 to 299 | VMMS office |
| 301 to 399 | BMS office |
| 401 to 499 | Multi system accounts |
| 501 to 599 | Broken state accounts |
| 900 | Reserved for the platform admin (S10) |
| 1001 to 1999 | Bulk mechanics (1001 to 1060 today) |
| 2001 to 2999 | BMS drivers (2001 to 2012 today) |
| 3001 to 3999 | BMS helpers (3001 to 3020 today) |

## Accounts

### VRMS office accounts

| Id | Email | Name | Roles | Password | State |
|---|---|---|---|---|---|
| 2 | `vrms.admin@welinc.com` | Victor Ramos | VRMS Admin | `admin1234` | active |
| 101 | `vrms.admin2@welinc.com` | Teresita Aquino | VRMS Admin | `admin1234` | active |
| 102 | `vrms.admin3@welinc.com` | Gilbert Navarro | VRMS Admin | `admin1234` | active |
| 103 | `vrms.admin4@welinc.com` | Marissa Domingo | VRMS Admin | `admin1234` | active |
| 104 | `vrms.admin5@welinc.com` | Rodrigo Salazar | VRMS Admin | `admin1234` | active |
| 20 | `vrms.chief@welinc.com` | Ramon Villanueva | VRMS Chief Mechanic | `chief1234` | active |
| 111 | `vrms.chief2@welinc.com` | Alfredo Bautista | VRMS Chief Mechanic | `chief1234` | active |
| 112 | `vrms.chief3@welinc.com` | Nestor Pineda | VRMS Chief Mechanic | `chief1234` | active |
| 113 | `vrms.chief4@welinc.com` | Lorna Galang | VRMS Chief Mechanic | `chief1234` | active |
| 114 | `vrms.chief5@welinc.com` | Efren Lacson | VRMS Chief Mechanic | `chief1234` | active |

### VMMS office accounts

| Id | Email | Name | Roles | Password | State |
|---|---|---|---|---|---|
| 3 | `vmms.admin@welinc.com` | Valerio Mercado | VMMS Admin | `admin1234` | active |
| 201 | `vmms.admin2@welinc.com` | Cristina Velasco | VMMS Admin | `admin1234` | active |
| 202 | `vmms.admin3@welinc.com` | Dominic Sison | VMMS Admin | `admin1234` | active |
| 203 | `vmms.admin4@welinc.com` | Rowena Manalo | VMMS Admin | `admin1234` | active |
| 204 | `vmms.admin5@welinc.com` | Leonardo Abad | VMMS Admin | `admin1234` | active |
| 220 | `vmms.chief@welinc.com` | Ramon Garcia | VMMS Chief Mechanic | `chief1234` | active |
| 221 | `vmms.chief2@welinc.com` | Diego Martinez | VMMS Chief Mechanic | `chief1234` | active |
| 222 | `vmms.chief3@welinc.com` | Ariel Macaraeg | VMMS Chief Mechanic | `chief1234` | active |
| 223 | `vmms.chief4@welinc.com` | Benigno Tuazon | VMMS Chief Mechanic | `chief1234` | active |
| 224 | `vmms.chief5@welinc.com` | Celso Ramirez | VMMS Chief Mechanic | `chief1234` | active |
| 210 | `vmms.ops@welinc.com` | Oscar Ramos | VMMS Operations | `ops1234` | active |
| 211 | `vmms.ops2@welinc.com` | Imelda Fajardo | VMMS Operations | `ops1234` | active |
| 212 | `vmms.ops3@welinc.com` | Rafael Ilagan | VMMS Operations | `ops1234` | active |
| 213 | `vmms.ops4@welinc.com` | Josefina Dela Paz | VMMS Operations | `ops1234` | active |
| 214 | `vmms.ops5@welinc.com` | Noel Samonte | VMMS Operations | `ops1234` | active |

### BMS office accounts

| Id | Email | Name | Roles | Password | State |
|---|---|---|---|---|---|
| 1 | `bms.admin@welinc.com` | Bernardo Mendoza | BMS Admin | `admin1234` | active |
| 301 | `bms.admin2@welinc.com` | Evangeline Cortez | BMS Admin | `admin1234` | active |
| 302 | `bms.admin3@welinc.com` | Patrick Yap | BMS Admin | `admin1234` | active |
| 303 | `bms.admin4@welinc.com` | Gemma Lualhati | BMS Admin | `admin1234` | active |
| 304 | `bms.admin5@welinc.com` | Raul Tan | BMS Admin | `admin1234` | active |
| 4 | `bms.cs@welinc.com` | Clara Reyes | BMS Customer Support | `cs1234` | active |
| 321 | `bms.cs2@welinc.com` | Angelica Ong | BMS Customer Support | `cs1234` | active |
| 322 | `bms.cs3@welinc.com` | Mylene Serrano | BMS Customer Support | `cs1234` | active |
| 323 | `bms.cs4@welinc.com` | Jonathan Lim | BMS Customer Support | `cs1234` | active |
| 324 | `bms.cs5@welinc.com` | Kristine Valencia | BMS Customer Support | `cs1234` | active |
| 5 | `bms.ops@welinc.com` | Oscar Santos | BMS Operations | `ops1234` | active |
| 311 | `bms.ops2@welinc.com` | Melchor Agustin | BMS Operations | `ops1234` | active |
| 312 | `bms.ops3@welinc.com` | Liza Montemayor | BMS Operations | `ops1234` | active |
| 313 | `bms.ops4@welinc.com` | Hernani Cabral | BMS Operations | `ops1234` | active |
| 314 | `bms.ops5@welinc.com` | Susana Ventura | BMS Operations | `ops1234` | active |

### Multi system accounts

| Id | Email | Name | Roles | Password | State |
|---|---|---|---|---|---|
| 401 | `multi.chief@welinc.com` | Teodoro Manalastas | VRMS Chief Mechanic, VMMS Chief Mechanic | `chief1234` | active |
| 402 | `multi.admin@welinc.com` | Felicidad Roxas | VRMS Admin, VMMS Admin | `admin1234` | active |
| 403 | `multi.mixed@welinc.com` | Arturo Pangilinan | VRMS Chief Mechanic, VMMS Operations | `chief1234` | active |
| 404 | `multi.lead@welinc.com` | Corazon Villareal | VRMS Chief Mechanic, VMMS Operations, BMS Operations | `chief1234` | active |

### Broken state accounts

| Id | Email | Name | Roles | Password | State |
|---|---|---|---|---|---|
| 501 | `state.locked@welinc.com` | Lito Concepcion | VRMS Mechanic, VMMS Mechanic | `mechanic1234` | locked |
| 502 | `state.deactivated@welinc.com` | Nonoy Evangelista | VRMS Mechanic, VMMS Mechanic | `mechanic1234` | deactivated |
| 503 | `state.unverified@welinc.com` | Bong Rivera | VRMS Mechanic, VMMS Mechanic | `mechanic1234` | unverified |
| 504 | `state.deleted@welinc.com` | Junjun Marquez | VRMS Mechanic, VMMS Mechanic | `mechanic1234` | deleted |

### Mechanics and crew

| Group | Count | Ids | Roles | Password |
|---|---|---|---|---|
| Named mechanics | 5 | 11 to 15 (`mech.juan@`, `mech.pedro@`, `mech.rommel@`, `mech.isabel@`, `mech.carl@`) | VRMS Mechanic, VMMS Mechanic | `mechanic1234` |
| Bulk mechanics | 60 | 1001 to 1060 | VRMS Mechanic, VMMS Mechanic | `mechanic1234` |
| BMS drivers | 12 | 2001 to 2012 (`driver.ramon@` to `driver.antonio@`) | BMS Driver | `driver1234` |
| BMS helpers | 20 | 3001 to 3020 (`helper.markanthony@` to `helper.bryan@`) | BMS Helper | `helper1234` |

Driver n matches BMS `emp_id` `DRV-00n`, and helper n matches `HLP-00n`. Drivers and helpers carry their `+63` phone in `contact`, copied from the BMS crew seed.

Together these give the launcher (S4) accounts with one system (most office people), two (the mechanics, `multi.chief@`, `multi.admin@`, `multi.mixed@`) and three (`multi.lead@`). Until S4, a portal login that names no system always lands on the same system for these accounts.

## What the broken accounts show at login today

| Account | Login answers |
|---|---|
| `state.locked@` | 403 "Account is locked. Contact your Admin to unlock." with `isLocked: true` |
| `state.deactivated@` | 401 "Invalid credentials" |
| `state.deleted@` | 401 "Invalid credentials" (soft deleted; its roles stay) |
| `state.unverified@` | Signs in. S13 decides whether an unverified account may sign in |

They exist only on local databases, never on staging. A reseed puts them back in their state, so if you unlock `state.locked@`, it is locked again after the next `npm run seed`.

## Commands

You run these in `welinc-auth`, after `npm run db:deploy`.

| Command | What it does |
|---|---|
| `npm run seed` | Puts every seed person back to their listed state (name, email, password, state, exactly their roles), then applies the client registry. Accounts you made by hand and their sessions are left alone. Safe to run again: an unchanged run writes nothing to the directory feed |
| `npm run seed -- --reset` | Removes every user first (with their sessions, change history and reset codes), then seeds. Local databases only: it refuses unless `NODE_ENV` is unset, `development` or `test`, and the database host is `localhost`, `127.0.0.1` or a compose service name |
| `npm run seed:check -- <path>` | Compares a copy of `people.json` with welinc-auth's, byte for byte. Prints "Matches people.json", or tells you to copy the file again |

The seed stops and writes nothing when:
- the manifest has a problem (a duplicate email, a role not in the catalog, too many roles in one system, an admin in all three systems, and so on). It lists every problem at once.
- a manifest email already belongs to someone else, for example an account you made by hand with `bms.cs2@welinc.com`. Free that email, or run `--reset` locally.
- `NODE_ENV=production`, unless `SEED_ALLOW=staging` is set. Set that only in the staging environment's welinc-auth settings, never on production. With it, the seed skips the broken state accounts.

The passwords here are public on purpose. That is only safe because the seed never runs on production.

## Moving from the old seed

- `ops.user@welinc.com` is now `bms.ops@welinc.com` (the same person, id 5), and `cs.user@welinc.com` is now `bms.cs@welinc.com` (id 4).
- The VRMS chief `vrms.chief@welinc.com` now uses `chief1234`, not `mechanic1234`.
- Your next `npm run seed` renames them in place. If it stops on an email conflict, run `npm run seed -- --reset`.

## For VMMS and BMS (in S11, not before)

You switch your seed when your system moves onto the shared login (S11). Until then your own seed keeps working.

1. Copy `welinc-auth/prisma/seeds/people.json` into your seed folder, and add `<your path>/people.json text eol=lf` to your `.gitattributes` so a Windows checkout keeps the same bytes. After each pull of welinc-auth, check your copy from the workspace root:
   ```bash
   npm --prefix welinc-auth run seed:check -- <your repo>/<your path>/people.json
   ```
2. Stop creating users and roles in your seed. Link your rows to the manifest ids instead:
   - VMMS: `Mechanic.userId`, work order and audit actor ids.
   - BMS: `drivers` and `helpers` gain a user id column set from the manifest (driver n is `DRV-00n`, helper n is `HLP-00n`), plus booking actor ids.
3. Use the manifest emails:
   - VMMS: `ops.user@` becomes `vmms.ops@` (Oscar Ramos), and `vmms.chiefmech@` and `vmms.chiefmech2@` become `vmms.chief@` and `vmms.chief2@`.
   - BMS: `cs.user@` becomes `bms.cs@`, `ops.user@` becomes `bms.ops@`, and crew emails move from `@welinc.ph` to the manifest's `@welinc.com`.
4. Need a new person or role? Ask the shared services owner to add them to the manifest. Never add people only in your own seed.

VRMS already works this way: see `welinc-backend-vrms/prisma/seeds/shared-ids.ts`, which reads its copy and makes a `Mechanic` row for every VRMS mechanic and chief mechanic.
