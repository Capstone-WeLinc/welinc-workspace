# Seed accounts

The test people every WeLinc system shares. Sign in with them at the portal:

| Where | Portal | Who's there |
|---|---|---|
| Your machine | `http://localhost:8000` | everyone below |
| Staging | `https://staging-portal.welinc.app` | everyone except the broken state accounts |

The passwords are public on purpose: these are test accounts only.

## Getting the emailed code

Admins (and `state.unverified@`) type a 6 digit code from their email when they sign in. Seed addresses aren't real inboxes, so:

- **Your machine:** the code is printed in the auth log: `docker logs welinc_auth_service`.
- **Staging:** the code goes to the team inbox `welinc.demo@gmail.com`. Each account has its own tag: `vrms.admin@welinc.com` gets mail at `welinc.demo+vrms.admin@gmail.com`, so search `to:welinc.demo+vrms.admin`. Ask the lead for access.
- **Real addresses** (an account you made with your own Gmail) get real mail, on your machine too. Don't send codes or resets to real people while testing.

## Suite admin

| Id | Email | Name | Roles | Password |
|---|---|---|---|---|
| 9001 | `suite.admin@welinc.com` | Leonora Castillo | none (manages every account in the portal) | `admin1234` |

### VRMS office accounts

| Id | Email | Name | Roles | Password |
|---|---|---|---|---|
| 1101 | `vrms.admin@welinc.com` | Victor Ramos | VRMS Admin | `admin1234` |
| 1102 | `vrms.admin2@welinc.com` | Teresita Aquino | VRMS Admin | `admin1234` |
| 1103 | `vrms.admin3@welinc.com` | Gilbert Navarro | VRMS Admin | `admin1234` |
| 1104 | `vrms.admin4@welinc.com` | Marissa Domingo | VRMS Admin | `admin1234` |
| 1105 | `vrms.admin5@welinc.com` | Rodrigo Salazar | VRMS Admin | `admin1234` |
| 1201 | `vrms.chief@welinc.com` | Ramon Villanueva | VRMS Chief Mechanic | `chief1234` |
| 1202 | `vrms.chief2@welinc.com` | Alfredo Bautista | VRMS Chief Mechanic | `chief1234` |
| 1203 | `vrms.chief3@welinc.com` | Nestor Pineda | VRMS Chief Mechanic | `chief1234` |
| 1204 | `vrms.chief4@welinc.com` | Lorna Galang | VRMS Chief Mechanic | `chief1234` |
| 1205 | `vrms.chief5@welinc.com` | Efren Lacson | VRMS Chief Mechanic | `chief1234` |

### VMMS office accounts

| Id | Email | Name | Roles | Password |
|---|---|---|---|---|
| 2101 | `vmms.admin@welinc.com` | Valerio Mercado | VMMS Admin | `admin1234` |
| 2102 | `vmms.admin2@welinc.com` | Cristina Velasco | VMMS Admin | `admin1234` |
| 2103 | `vmms.admin3@welinc.com` | Dominic Sison | VMMS Admin | `admin1234` |
| 2104 | `vmms.admin4@welinc.com` | Rowena Manalo | VMMS Admin | `admin1234` |
| 2105 | `vmms.admin5@welinc.com` | Leonardo Abad | VMMS Admin | `admin1234` |
| 2301 | `vmms.chief@welinc.com` | Ramon Garcia | VMMS Chief Mechanic | `chief1234` |
| 2302 | `vmms.chief2@welinc.com` | Diego Martinez | VMMS Chief Mechanic | `chief1234` |
| 2303 | `vmms.chief3@welinc.com` | Ariel Macaraeg | VMMS Chief Mechanic | `chief1234` |
| 2304 | `vmms.chief4@welinc.com` | Benigno Tuazon | VMMS Chief Mechanic | `chief1234` |
| 2305 | `vmms.chief5@welinc.com` | Celso Ramirez | VMMS Chief Mechanic | `chief1234` |
| 2201 | `vmms.ops@welinc.com` | Oscar Ramos | VMMS Operations | `ops1234` |
| 2202 | `vmms.ops2@welinc.com` | Imelda Fajardo | VMMS Operations | `ops1234` |
| 2203 | `vmms.ops3@welinc.com` | Rafael Ilagan | VMMS Operations | `ops1234` |
| 2204 | `vmms.ops4@welinc.com` | Josefina Dela Paz | VMMS Operations | `ops1234` |
| 2205 | `vmms.ops5@welinc.com` | Noel Samonte | VMMS Operations | `ops1234` |
| 2401 | `vmms.mech@welinc.com` | Ramil Aquino | VMMS Mechanic | `mechanic1234` |

`vmms.mech@` is the one person who holds VMMS Mechanic and nothing else (suite spec 0014, AC-8). The VMMS web app admits only Admin and Operations, so the portal shows them the phone only state, and the checker uses them for the `APP_NOT_ALLOWED` checks.

### BMS office accounts

| Id | Email | Name | Roles | Password |
|---|---|---|---|---|
| 3101 | `bms.admin@welinc.com` | Bernardo Mendoza | BMS Admin | `admin1234` |
| 3102 | `bms.admin2@welinc.com` | Evangeline Cortez | BMS Admin | `admin1234` |
| 3103 | `bms.admin3@welinc.com` | Patrick Yap | BMS Admin | `admin1234` |
| 3104 | `bms.admin4@welinc.com` | Gemma Lualhati | BMS Admin | `admin1234` |
| 3105 | `bms.admin5@welinc.com` | Raul Tan | BMS Admin | `admin1234` |
| 3301 | `bms.cs@welinc.com` | Clara Reyes | BMS Customer Support | `cs1234` |
| 3302 | `bms.cs2@welinc.com` | Angelica Ong | BMS Customer Support | `cs1234` |
| 3303 | `bms.cs3@welinc.com` | Mylene Serrano | BMS Customer Support | `cs1234` |
| 3304 | `bms.cs4@welinc.com` | Jonathan Lim | BMS Customer Support | `cs1234` |
| 3305 | `bms.cs5@welinc.com` | Kristine Valencia | BMS Customer Support | `cs1234` |
| 3201 | `bms.ops@welinc.com` | Oscar Santos | BMS Operations | `ops1234` |
| 3202 | `bms.ops2@welinc.com` | Melchor Agustin | BMS Operations | `ops1234` |
| 3203 | `bms.ops3@welinc.com` | Liza Montemayor | BMS Operations | `ops1234` |
| 3204 | `bms.ops4@welinc.com` | Hernani Cabral | BMS Operations | `ops1234` |
| 3205 | `bms.ops5@welinc.com` | Susana Ventura | BMS Operations | `ops1234` |

### Multi system accounts

| Id | Email | Name | Roles | Password |
|---|---|---|---|---|
| 4001 | `multi.chief@welinc.com` | Teodoro Manalastas | VRMS Chief Mechanic, VMMS Chief Mechanic | `chief1234` |
| 4002 | `multi.admin@welinc.com` | Felicidad Roxas | VRMS Admin, VMMS Admin | `admin1234` |
| 4003 | `multi.mixed@welinc.com` | Arturo Pangilinan | VRMS Chief Mechanic, VMMS Operations | `chief1234` |
| 4004 | `multi.lead@welinc.com` | Corazon Villareal | VRMS Chief Mechanic, VMMS Operations, BMS Operations | `chief1234` |

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

Drivers and helpers carry a `+63` phone. BMS no longer gives crew an employee ID (spec bms/0012), so they're matched by their account id.

`vmms.mech@` holds only VMMS Mechanic, so the VMMS web app turns them away (phone app only). The `multi.*` people hold two or three systems: they land on the launcher after sign in, while a one system person goes straight in.

## What the broken accounts show

These exist only on your machine, never on staging.

| Account | Login answers |
|---|---|
| `state.locked@` | 403 `ACCOUNT_LOCKED` with `isLocked: true` and `lockedUntil` (suite spec 0015: a lock runs out after 15 minutes; a reseed starts a fresh one) |
| `state.deactivated@` | Right password: 403 `ACCOUNT_INACTIVE` "This account is deactivated." Wrong password: 401 "Invalid credentials", like any account |
| `state.deleted@` | 401 "Invalid credentials" (soft deleted; its roles stay) |
| `state.unverified@` | The right password answers the email step (200 `EMAIL_VERIFICATION_REQUIRED`, spec 0009), not a session: the portal and the mobile login ask for the 6 digit code emailed to it. Once the code is used it signs in like anyone else, until the next `npm run seed` makes it unverified again. Locally, run welinc-auth with SMTP blank so the code prints in its log instead of going out as real mail |

A reseed puts each one back in its state.

## Commands

Run these in `welinc-auth`.

| Command | What it does |
|---|---|
| `npm run seed` | Puts every seed person back to their listed state. Accounts you made by hand stay. Safe to run again |
| `npm run seed -- --reset` | Deletes every user first, then seeds. Local only |
| `npm run seed:check -- <path>` | Checks that your copy of `people.json` matches welinc-auth's |

The seed stops without writing anything if an email it needs is already taken by an account you made by hand. Free that email, or use `--reset` locally.

Staging is seeded by the lead, never from your machine.

## Ids

Every person has a fixed id: `00000000-0000-4000-8000-` plus a 12 digit number. First digit: 1 VRMS, 2 VMMS, 3 BMS, 4 more than one system, 5 broken account, 9 suite admin. Second digit: the role. Last two: the person.

An id is one person forever, never reused.

## Using the seed people in your own seed

`welinc-auth/prisma/seeds/people.json` is the only list of seed people. Your seed never creates users. It links its own rows (mechanics, crew, bookings) to these people:

1. Keep a byte for byte copy of `people.json` in your seed folder, with `<path>/people.json text eol=lf` in `.gitattributes`.
2. After each pull of welinc-auth, check it from the workspace root: `npm --prefix welinc-auth run seed:check -- <your repo>/<path>/people.json`.
3. Find people by email or role, never by a typed id, and put their id in your column (`userId`, `authUserId`, `actorUserId`).

VRMS's version: `welinc-backend-vrms/prisma/seeds/shared-ids.ts`.

Need a new person or role? Ask the lead to add them to `people.json`, then copy the file again.
