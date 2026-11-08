# 0004. Rationale: roles per system

Back to [index.md](index.md).

## Context

welinc-auth stores roles as one Postgres enum shared by every system (`UserRole`: `ADMIN`, `MECHANIC`, `CHIEF_MECHANIC`, `CUSTOMER_SUPPORT`, `OPERATIONS`) and a `user_roles` table pairing it with a `SystemType`. Any pair is accepted, so `MECHANIC` in BMS or `CUSTOMER_SUPPORT` in VRMS can be stored, and nothing limits how many roles a person holds in one system. Adding a role for one system (BMS needs Driver and Helper for its mobile app) means changing the enum every system's assignments share.

Each system already assumes rules welinc-auth doesn't know. VMMS requires exactly one VMMS role per account in its own code. The VRMS user form has a single role dropdown and the BMS web app reads `user.role` as one value, so both behave as one role per person. The VMMS mobile app (`AuthService.ts`, `getMobileAccessRole`) lets in only Mechanic and Chief Mechanic, and only after login succeeds; BMS mobile will serve only Driver and Helper. Contract 0001 promised (section 13, rule 5) that these rules move into welinc-auth's system catalog in S5, and listed `/auth/systems` as the route that publishes them.

The admin role is also hardcoded: every user admin route is guarded by `@Roles(UserRole.ADMIN)`, and the last admin rule and the admin reset test the literal `ADMIN`. VMMS has said its Admin now has less access and Operations runs most of its workflow, so "the admin is called ADMIN" may not hold for every system.

Forces: the change lands in a shared repo every group depends on, so changes must be reviewable; the deadline is the end of November 2026; only seed accounts exist in every database; the token's `roles` claim is read by VRMS's CASL matrix and soon by VMMS and BMS, so its shape can't move; S10 (suite admin, central permissions) and S4 (the launcher) will read whatever S5 publishes.

## Options considered

### Option 1: Keep the enums, add a rules map in code

A typed constant in welinc-auth lists each system's allowed roles and limit; the service checks it.

**Pros**:
- Smallest change; no migration.
- Easy to read in one file.

**Cons**:
- The database still accepts any pair, so a script, a seed or a bug writes bad data.
- The shared `UserRole` enum stays, so a BMS role is still a schema change for everyone.
- Nothing for `/auth/systems` to read except code, and no place for names and descriptions per system.

### Option 2: Tables synced from one reviewed file per system (chosen)

`systems` and `system_roles` tables, a foreign key from `user_roles`, filled only by a sync from per system files.

**Pros**:
- The database itself refuses a wrong pair.
- Each system's roles are one file; changes are reviewed in a pull request, like the client registry (`seed:clients`).
- The tables give `/auth/systems`, the admin guard and S10 one source.

**Cons**:
- A migration that converts a live column, plus a new deploy step that can refuse.
- A role change waits for a merge and a deploy.

### Option 3: Tables changed by migrations only

The same tables, but each role is added in a Prisma migration.

**Pros**:
- Fully strict; the migration history records every change.

**Cons**:
- Adding a role means writing SQL in a shared migration history, mixed with every other system's schema changes.
- No validation step that can explain a refusal ("5 people still hold HELPER").

### Option 4: Roles edited at runtime in an admin screen

Platform admins add and edit roles through the API.

**Pros**:
- Fastest change; no deploy.

**Cons**:
- Changes aren't reviewed, and catalogs edited this way drift (empty systems, undescribed roles, old and new names mixed, as seen in another company's suite).
- It needs the S10 admin model first.

## Rationale

Option 2 is the only one that makes a wrong role impossible to store and still keeps changes cheap and reviewable. The force that decides it is the shared repo: a role change for one group must be visible to the others and must not touch their roles, which a per system file in a pull request gives directly. The database foreign key matters because seeds, scripts and a future import (S11 merges VMMS and BMS users) all write `user_roles`, and a service check alone protects only one path. Option 1 is a fine stopgap but leaves the shared enum, which is the original problem. Option 3 gets the strictness but buries role changes in migration SQL, and Option 4 needs S10 and drifts.

The sync refusing a removed role that people still hold follows how Azure custom roles and AWS IAM handle deletes in reviewed configuration: the change is blocked until the holders are moved, so nobody loses access silently. The migration takes the opposite approach for existing bad data, fixing it automatically and keeping the most powerful role, because the engineer chose that and only seed data exists; the backup step in the migration plan is what makes that safe later.

One role per person is a per system limit (`maxRolesPerUser`), not a global rule, so a system that later wants two roles changes one number in its own file. The admin role is a flag rather than the literal `ADMIN` so a system like VMMS can move user admin to another role without code changes, and so S10 can build on it. Allowed apps sit on the client per audience because `vmms-mobile` serves two systems and a client with no list should allow everyone. The check runs on every grant, including refresh, so a role change reaches a phone within one access token lifetime instead of after its 7 day session.

Keeping the `SystemType` enum is deliberate: a new system is rare and already needs clients, gateway routes and ports, and changing the key would rework the client registry and sessions that specs 0002 and 0003 just verified.
