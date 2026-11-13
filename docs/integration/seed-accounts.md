# Seed accounts

The test people every WeLinc system shares, from [spec 0006](../specs/_root/0006-suite-seed-accounts/index.md). You sign in with these through the portal at `http://localhost:8000`.

## The manifest

- `welinc-auth/prisma/seeds/people.json` is the one list of seed people for the whole suite: 147 people (145, the suite admin from spec 0013 and `vmms.mech@` from spec 0014), each with a fixed id (see *Ids*), one email, their roles in each system, a password and a state.
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

## Ids

Every person has a fixed id: `00000000-0000-4000-8000-` plus a 12 digit number. The number is built the same way for every system, so you can read who someone is from it. No system gets special numbers.

| Number | Who |
|---|---|
| 1101 to 1199 | VRMS Admin |
| 1201 to 1299 | VRMS Chief Mechanic |
| 2101 to 2199 | VMMS Admin |
| 2201 to 2299 | VMMS Operations |
| 2301 to 2399 | VMMS Chief Mechanic |
| 2401 to 2499 | VMMS Mechanic only (`vmms.mech@`, spec 0014) |
| 3101 to 3199 | BMS Admin |
| 3201 to 3299 | BMS Operations |
| 3301 to 3399 | BMS Customer Support |
| 3401 to 3499 | BMS Driver |
| 3501 to 3599 | BMS Helper |
| 4001 to 4099 | People in more than one system (`multi.*`) |
| 4101 to 4199 | Named mechanics (VRMS and VMMS Mechanic) |
| 4201 to 4299 | Bulk mechanics (VRMS and VMMS Mechanic) |
| 5001 to 5099 | Broken state accounts |
| 9001 | The suite admin (spec 0013) |

Read it as: first digit is the system (1 VRMS, 2 VMMS, 3 BMS), second digit is the role in that system's catalog order, the last two digits count the people. A first digit of 4 means more than one system, and 5 means a broken account.

An id is one person forever. A removed person's id is retired, never reused. A new person takes the next free number in their block.

## Accounts

### Suite admin

| Id | Email | Name | Roles | Password | State |
|---|---|---|---|---|---|
| 9001 | `suite.admin@welinc.com` | Leonora Castillo | none (suite admin, spec 0013) | `admin1234` | active |

Every admin, this one included, confirms each portal sign in with an emailed code (`ADMIN_SIGN_IN_CODE`, on by default). Seed addresses aren't real inboxes, so on your machine auth never sends mail to `@welinc.com` (or `localhost`, `test.com`, `example.com`): it prints the whole email, code included, to `docker logs welinc_auth_service`, even with `SMTP_*` set. Mail to a real address, such as an account you made with your own Gmail, goes out through SMTP as usual.

### VRMS office accounts

| Id | Email | Name | Roles | Password | State |
|---|---|---|---|---|---|
| 1101 | `vrms.admin@welinc.com` | Victor Ramos | VRMS Admin | `admin1234` | active |
| 1102 | `vrms.admin2@welinc.com` | Teresita Aquino | VRMS Admin | `admin1234` | active |
| 1103 | `vrms.admin3@welinc.com` | Gilbert Navarro | VRMS Admin | `admin1234` | active |
| 1104 | `vrms.admin4@welinc.com` | Marissa Domingo | VRMS Admin | `admin1234` | active |
| 1105 | `vrms.admin5@welinc.com` | Rodrigo Salazar | VRMS Admin | `admin1234` | active |
| 1201 | `vrms.chief@welinc.com` | Ramon Villanueva | VRMS Chief Mechanic | `chief1234` | active |
| 1202 | `vrms.chief2@welinc.com` | Alfredo Bautista | VRMS Chief Mechanic | `chief1234` | active |
| 1203 | `vrms.chief3@welinc.com` | Nestor Pineda | VRMS Chief Mechanic | `chief1234` | active |
| 1204 | `vrms.chief4@welinc.com` | Lorna Galang | VRMS Chief Mechanic | `chief1234` | active |
| 1205 | `vrms.chief5@welinc.com` | Efren Lacson | VRMS Chief Mechanic | `chief1234` | active |

### VMMS office accounts

| Id | Email | Name | Roles | Password | State |
|---|---|---|---|---|---|
| 2101 | `vmms.admin@welinc.com` | Valerio Mercado | VMMS Admin | `admin1234` | active |
| 2102 | `vmms.admin2@welinc.com` | Cristina Velasco | VMMS Admin | `admin1234` | active |
| 2103 | `vmms.admin3@welinc.com` | Dominic Sison | VMMS Admin | `admin1234` | active |
| 2104 | `vmms.admin4@welinc.com` | Rowena Manalo | VMMS Admin | `admin1234` | active |
| 2105 | `vmms.admin5@welinc.com` | Leonardo Abad | VMMS Admin | `admin1234` | active |
| 2301 | `vmms.chief@welinc.com` | Ramon Garcia | VMMS Chief Mechanic | `chief1234` | active |
| 2302 | `vmms.chief2@welinc.com` | Diego Martinez | VMMS Chief Mechanic | `chief1234` | active |
| 2303 | `vmms.chief3@welinc.com` | Ariel Macaraeg | VMMS Chief Mechanic | `chief1234` | active |
| 2304 | `vmms.chief4@welinc.com` | Benigno Tuazon | VMMS Chief Mechanic | `chief1234` | active |
| 2305 | `vmms.chief5@welinc.com` | Celso Ramirez | VMMS Chief Mechanic | `chief1234` | active |
| 2201 | `vmms.ops@welinc.com` | Oscar Ramos | VMMS Operations | `ops1234` | active |
| 2202 | `vmms.ops2@welinc.com` | Imelda Fajardo | VMMS Operations | `ops1234` | active |
| 2203 | `vmms.ops3@welinc.com` | Rafael Ilagan | VMMS Operations | `ops1234` | active |
| 2204 | `vmms.ops4@welinc.com` | Josefina Dela Paz | VMMS Operations | `ops1234` | active |
| 2205 | `vmms.ops5@welinc.com` | Noel Samonte | VMMS Operations | `ops1234` | active |
| 2401 | `vmms.mech@welinc.com` | Ramil Aquino | VMMS Mechanic | `mechanic1234` | active |

`vmms.mech@` is the one person who holds VMMS Mechanic and nothing else (suite spec 0014, AC-8). The VMMS web app admits only Admin and Operations, so the portal shows them the phone only state, and the checker uses them for the `APP_NOT_ALLOWED` checks.

### BMS office accounts

| Id | Email | Name | Roles | Password | State |
|---|---|---|---|---|---|
| 3101 | `bms.admin@welinc.com` | Bernardo Mendoza | BMS Admin | `admin1234` | active |
| 3102 | `bms.admin2@welinc.com` | Evangeline Cortez | BMS Admin | `admin1234` | active |
| 3103 | `bms.admin3@welinc.com` | Patrick Yap | BMS Admin | `admin1234` | active |
| 3104 | `bms.admin4@welinc.com` | Gemma Lualhati | BMS Admin | `admin1234` | active |
| 3105 | `bms.admin5@welinc.com` | Raul Tan | BMS Admin | `admin1234` | active |
| 3301 | `bms.cs@welinc.com` | Clara Reyes | BMS Customer Support | `cs1234` | active |
| 3302 | `bms.cs2@welinc.com` | Angelica Ong | BMS Customer Support | `cs1234` | active |
| 3303 | `bms.cs3@welinc.com` | Mylene Serrano | BMS Customer Support | `cs1234` | active |
| 3304 | `bms.cs4@welinc.com` | Jonathan Lim | BMS Customer Support | `cs1234` | active |
| 3305 | `bms.cs5@welinc.com` | Kristine Valencia | BMS Customer Support | `cs1234` | active |
| 3201 | `bms.ops@welinc.com` | Oscar Santos | BMS Operations | `ops1234` | active |
| 3202 | `bms.ops2@welinc.com` | Melchor Agustin | BMS Operations | `ops1234` | active |
| 3203 | `bms.ops3@welinc.com` | Liza Montemayor | BMS Operations | `ops1234` | active |
| 3204 | `bms.ops4@welinc.com` | Hernani Cabral | BMS Operations | `ops1234` | active |
| 3205 | `bms.ops5@welinc.com` | Susana Ventura | BMS Operations | `ops1234` | active |

### Multi system accounts

| Id | Email | Name | Roles | Password | State |
|---|---|---|---|---|---|
| 4001 | `multi.chief@welinc.com` | Teodoro Manalastas | VRMS Chief Mechanic, VMMS Chief Mechanic | `chief1234` | active |
| 4002 | `multi.admin@welinc.com` | Felicidad Roxas | VRMS Admin, VMMS Admin | `admin1234` | active |
| 4003 | `multi.mixed@welinc.com` | Arturo Pangilinan | VRMS Chief Mechanic, VMMS Operations | `chief1234` | active |
| 4004 | `multi.lead@welinc.com` | Corazon Villareal | VRMS Chief Mechanic, VMMS Operations, BMS Operations | `chief1234` | active |

### Broken state accounts

| Id | Email | Name | Roles | Password | State |
|---|---|---|---|---|---|
| 5001 | `state.locked@welinc.com` | Lito Concepcion | VRMS Mechanic, VMMS Mechanic | `mechanic1234` | locked |
| 5002 | `state.deactivated@welinc.com` | Nonoy Evangelista | VRMS Mechanic, VMMS Mechanic | `mechanic1234` | deactivated |
| 5003 | `state.unverified@welinc.com` | Bong Rivera | VRMS Mechanic, VMMS Mechanic | `mechanic1234` | unverified |
| 5004 | `state.deleted@welinc.com` | Junjun Marquez | VRMS Mechanic, VMMS Mechanic | `mechanic1234` | deleted |

### Mechanics and crew

| Group | Count | Ids | Roles | Password |
|---|---|---|---|---|
| Named mechanics | 5 | 4101 to 4105 (`mech.juan@`, `mech.pedro@`, `mech.rommel@`, `mech.isabel@`, `mech.carl@`) | VRMS Mechanic, VMMS Mechanic | `mechanic1234` |
| Bulk mechanics | 60 | 4201 to 4260 | VRMS Mechanic, VMMS Mechanic | `mechanic1234` |
| BMS drivers | 12 | 3401 to 3412 (`driver.ramon@` to `driver.antonio@`) | BMS Driver | `driver1234` |
| BMS helpers | 20 | 3501 to 3520 (`helper.markanthony@` to `helper.bryan@`) | BMS Helper | `helper1234` |

Driver n matches BMS `emp_id` `DRV-00n`, and helper n matches `HLP-00n`. Drivers and helpers carry their `+63` phone in `contact`, copied from the BMS crew seed.

Together these give the launcher (S4) accounts with one system (most office people), two (the mechanics, `multi.chief@`, `multi.admin@`, `multi.mixed@`) and three (`multi.lead@`). A portal login with two or more systems lands on the launcher, and one with a single system goes straight in.

## What the broken accounts show at login today

| Account | Login answers |
|---|---|
| `state.locked@` | 403 `ACCOUNT_LOCKED` with `isLocked: true` and `lockedUntil` (suite spec 0015: a lock runs out after 15 minutes; a reseed starts a fresh one) |
| `state.deactivated@` | Right password: 403 `ACCOUNT_INACTIVE` "This account is deactivated." Wrong password: 401 "Invalid credentials", like any account |
| `state.deleted@` | 401 "Invalid credentials" (soft deleted; its roles stay) |
| `state.unverified@` | The right password answers the email step (200 `EMAIL_VERIFICATION_REQUIRED`, spec 0009), not a session: the portal and the mobile login ask for the 6 digit code emailed to it. Once the code is used it signs in like anyone else, until the next `npm run seed` makes it unverified again. Locally, run welinc-auth with SMTP blank so the code prints in its log instead of going out as real mail |

They exist only on local databases, never on staging. A reseed puts them back in their state, so if you unlock `state.locked@` (or 15 minutes pass), it is locked again after the next `npm run seed`. A reseed also clears a lock on any active seed account you locked while testing.

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

- Every id changed when the numbers became one scheme per system (2026-11-09). A database seeded earlier holds the same people under their old ids, so the next `npm run seed` stops on an email conflict. On a local database run `npm run seed -- --reset`, then reseed VRMS.
- `ops.user@welinc.com` is now `bms.ops@welinc.com`, and `cs.user@welinc.com` is now `bms.cs@welinc.com`.
- The VRMS chief `vrms.chief@welinc.com` now uses `chief1234`, not `mechanic1234`.

## Adding your own seeded data

Your system's seed makes its own rows (tickets, work orders, bookings). When a row needs a person, such as the mechanic on a ticket or the user who made a booking, link it to the manifest person. Do it like this:

1. Copy the manifest into your seed folder (see the steps below) and read it in your seed code.
2. Find people by email or by role, never by a number you typed in. For example, the VRMS admin is the person whose email is `vrms.admin@welinc.com`, and the mechanics are everyone holding a VRMS Mechanic role. The id then comes from the file, so it stays right even if numbering changes.
3. Put that id in your foreign column (`authUserId`, `userId`, `actorUserId`). The person's name and email can be copied into your row too, if your table keeps them.
4. Read your rows back from the manifest on every seed run. Do not keep a second list of people in your own seed.

VRMS shows the pattern in `welinc-backend-vrms/prisma/seeds/shared-ids.ts`: it loads its copy, offers `seedActor(email)` and `vrmsRole(person)`, and `mechanics.seed.ts` makes a `Mechanic` row for each VRMS mechanic or chief.

Need a person that does not exist yet, for example a third VMMS operator? Add them to welinc-auth's `people.json` at the next free number in their block, run `npm run seed` there, copy the file into each system, and run `seed:check` on each copy.

## For VMMS and BMS (in S11, not before)

You switch your seed when your system moves onto the shared login (S11). Until then your own seed keeps working.

1. Copy `welinc-auth/prisma/seeds/people.json` into your seed folder, and add `<your path>/people.json text eol=lf` to your `.gitattributes` so a Windows checkout keeps the same bytes. After each pull of welinc-auth, check your copy from the workspace root:
   ```bash
   npm --prefix welinc-auth run seed:check -- <your repo>/<your path>/people.json
   ```
2. Stop creating users and roles in your seed. Link your rows to the manifest people instead (see *Adding your own seeded data* above):
   - VMMS: `Mechanic.userId`, work order and audit actor ids.
   - BMS: `drivers` and `helpers` gain a user id column set from the manifest (driver n is `DRV-00n`, helper n is `HLP-00n`), plus booking actor ids.
3. Use the manifest emails:
   - VMMS: `ops.user@` becomes `vmms.ops@` (Oscar Ramos), and `vmms.chiefmech@` and `vmms.chiefmech2@` become `vmms.chief@` and `vmms.chief2@`.
   - BMS: `cs.user@` becomes `bms.cs@`, `ops.user@` becomes `bms.ops@`, and crew emails move from `@welinc.ph` to the manifest's `@welinc.com`.
4. Need a new person or role? Ask the shared services owner to add them to the manifest. Never add people only in your own seed.

VRMS already works this way: see `welinc-backend-vrms/prisma/seeds/shared-ids.ts`, which reads its copy and makes a `Mechanic` row for every VRMS mechanic and chief mechanic.
