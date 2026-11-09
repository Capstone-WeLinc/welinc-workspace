# 0006. Suite seed accounts: rationale

The decision record for [index.md](index.md). `/develop` builds from the index; this file explains why.

## Context

The suite has one account service (welinc-auth), but three sets of test people. welinc-auth's seed makes 71 people and gives them fixed ids (`prisma/seeds/shared-ids.ts`), and backend-vrms keeps a hand copy of that file so its `Mechanic` rows and ticket history point at the same ids. VMMS's seed (`welinc-backend-vmms/prisma/seeds/users.seed.ts`, `development`) creates its own copies of the same people with random ids in its own users table. BMS has no user seed of its own: its gateway reads the auth database, and its crew script makes 12 drivers and 20 helpers as crew records with `@welinc.ph` emails and no link to any account.

The copies have drifted. `ops.user@welinc.com` is Oscar Santos (BMS Operations) in welinc-auth and BMS, but Oscar Ramos (VMMS Operations) in VMMS. VMMS has two chief mechanics welinc-auth lacks. Once VMMS and BMS move onto welinc-auth (S11), one email can only be one person, so the drift becomes a real conflict. The role catalog (spec 0004) also added BMS Driver and Helper, and nobody holds them.

The current seed has two dangers. It deletes every user on every run (`cleanDatabase`), so any account made by hand for testing disappears, along with every session. And nothing stops it from running against a hosted database; staging will exist soon (spec 0008), and production after that. The user directory feed (spec 0005) adds a constraint: a rerun must not produce change rows for people who did not change, or every system's sync churns.

Testing needs are also growing. The launcher (S4) needs people holding one, two and three systems. Lockout, deactivation (VRMS flags a leaver's tickets, per the S10 notes), deletion (the feed's `deleted` event) and email verification (S13) all need ready accounts. With one person per role, lists, reassigning and the last admin rule can't be exercised. The other groups are kept off the shared repos until the shared services are finished, so their seeds can only change at S11, but they need written instructions to follow then.

## Options considered

### Option 1: Keep a TypeScript copy per repo

Extend today's `shared-ids.ts` with the new people and ask each system to keep its own copy in step, as backend-vrms does.

**Pros**:
- Nothing new to build; VRMS already works this way.
- Typed in TypeScript, so a typo in a field name fails the build.

**Cons**:
- This is the exact mechanism that drifted. Nothing tells a group its copy is stale.
- The file mixes data with code (a name generator, helpers), so a copy is never byte for byte equal and can't be checked mechanically.
- BMS's crew script is plain JavaScript (`.mjs`), and other tools (analytics in any language) can't read TypeScript.

### Option 2: One JSON manifest in welinc-auth, copied and checked (chosen)

A plain data file, `people.json`, holds every seed person written out in full. welinc-auth's seed reads it; every other system copies it byte for byte and links rows to its ids; `seed:check` compares a copy with the source.

**Pros**:
- One source, and staleness is detectable by a hash compare.
- Any language reads JSON; the file is data only, so a diff shows exactly who changed.
- Works offline: no system needs welinc-auth running to seed.

**Cons**:
- Copies still exist, and the check only helps when someone runs it.
- 145 people written out is long, and JSON has no comments, so the reasons live in the guide instead.

### Option 3: Look up ids at seed time through the directory

Each system's seed asks `/auth/directory/users` for the people it needs, by email, and links to whatever ids come back. No copy anywhere.

**Pros**:
- No copied file; the running welinc-auth is the only truth.
- New people appear in every system without anyone copying anything.

**Cons**:
- Every seed needs welinc-auth running, migrated and seeded first, with a client key; VMMS and BMS have no keys until S11.
- Ids are no longer fixed, so seed data that refers to a person by id in code (VRMS's ticket history) can't be written ahead of time.
- A seed that fails because another container is down is harder to debug than one that reads a file.

### Option 4: A private npm package

Publish the people list as `@welinc/seed-people` from GitHub Packages and depend on it from each repo.

**Pros**:
- Versioned; a group pins a version and upgrades on purpose.
- No hand copying.

**Cons**:
- Registry authentication in three groups' machines and CI for one data file.
- BMS's crew script and Python tools would still need a different path.
- A capstone team would spend more time on packaging than on the data.

## Rationale

The problem is drift between copies that nobody can see, so the fix has to make a stale copy visible, not just add more people. Option 2 does that with the least machinery: the file is plain data, so a byte compare is a complete check, and any language in the suite can read it. Option 3 removes copies entirely, but it trades a file read for a running service and gives up fixed ids, and fixed ids are what let VRMS (and later VMMS and BMS) write seed history that points at real people. Option 4 solves distribution well, but the cost lands on three student groups' setups for a list that changes a few times a semester. Option 1 is where we are, and it already failed.

The upsert by id, instead of today's wipe, follows from staging and the feed. A wipe can never be allowed on a hosted database, and on a laptop it destroys hand made accounts and sessions on every run. Upserting by id (not by email) is what lets ids 4 and 5 change email in place without a duplicate, and comparing the final state in one transaction is what keeps the feed quiet on a rerun. `--reset` stays for the case a wipe is really wanted, and only on a local database. The environment guard uses an explicit `SEED_ALLOW=staging` instead of trusting `NODE_ENV` alone, because a hosted staging service will almost certainly run with `NODE_ENV=production` (welinc-auth's mail service throws without SMTP there).

The roster choices follow the testing needs in Context. About five people per office role makes lists, filters and the last admin rule real. All 32 crew get accounts so every BMS crew record can link to a login in S11, and their names and phones come from BMS's own seed so their screens look the same. The multi system accounts cover each combination the rules allow (same role, different roles, admin in two, three systems), and none is admin in all three, because that person would be a hidden suite superadmin, which S10 is designed to avoid. The manifest check enforces that. The broken accounts all hold VRMS and VMMS Mechanic, so VRMS can test them today, and VMMS can after S11. The email rule was chosen for clarity over habit: `ops.user@` and `cs.user@` hid which system they belonged to, so they become `bms.ops@` and `bms.cs@`, and the role is readable from every address.

Decisions made while writing (each with its runner up):
- **Upsert keyed by id, not email.** It renames in place and never creates a duplicate person. Runner up: by email, which would turn every rename into a delete plus a create.
- **Passwords reset on every run.** It keeps "put back to the listed state" true, and the password is not in the feed snapshot, so no feed rows result. Runner up: only when argon2 verify fails, which costs about seven seconds of verifies per run.
- **The state accounts hold VRMS and VMMS Mechanic.** VRMS can test them now. Runner up: spread across systems, which leaves BMS ones untestable until S11.
- **People written out in full, no generator.** Any language reads the file, and a diff is exact. Runner up: keep the bulk generator in code, which brings back the mixing of data and code that broke byte compares.
- **The guide's account table is written by hand from the manifest.** A generated file in the workspace would need a cross repo write. Runner up: a `seed:guide` script that prints the markdown to copy in.
- **No `user_changes` rows from the seed.** The seed has no acting user, as today. Runner up: a nullable actor for system writes, which spec 0004 already rejected.
