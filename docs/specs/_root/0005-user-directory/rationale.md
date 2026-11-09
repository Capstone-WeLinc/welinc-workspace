# 0005. Rationale: user directory for systems

The decision record behind [index.md](index.md). `/develop` skips this file.

## Context

welinc-auth owns every person in the suite. VRMS, VMMS and BMS each need a local copy of some of them: VRMS keeps a `mechanics` table for its picker and ticket assignments, VMMS schedules point to mechanics, BMS activity points to staff. Today VRMS refreshes its copy by downloading every VRMS user from `/auth/users` whenever the Users page or the New repair form opens and after every save; VMMS keeps its own users table; and the BMS gateway reads the auth database directly, which the suite rules forbid.

Contract 0001 section 9 already fixed the shape: a full list, a batch lookup and a change feed with cursors that never expire. What it left open is how welinc-auth produces the feed and how a reader consumes it safely. The hard part is completeness. welinc-auth changes people from many places: admin create and edit, role changes, activate, deactivate, delete, a person's own profile and picture, the seed script. One of them, the profile edit, already writes no record to the admin audit trail, which shows how easily a path gets missed. A missed change in a feed fails silently: the other systems just keep stale data.

Ordering is the second hard part. Rows get their numbers when they are written, but transactions commit in a different order, so a reader can pass a number whose transaction hasn't committed yet and never see it. The contract's answer (serve only rows older than 5 s) narrows that window but doesn't close it.

The forces: GA rigor (this is shared auth data for three systems), a small team that must operate it, Postgres 16 already in place, no message broker in the stack, and a deadline at the end of November. The other groups don't build on the shared repos until the S rows are done, so amending contract 0001 costs only the edit.

## Options considered

### Option 1: Feed table written by deferred Postgres triggers (chosen)

Triggers on `users` and `user_roles` write one snapshot row per user per transaction into `directory_changes` at commit. Readers page through it in transaction id order.

**Pros**:
- Complete by construction: every write, from any code path, present or future, lands in the feed in the same transaction.
- No new infrastructure; it is a table and two functions in the database already running.
- Transaction id ordering makes "never skipped" exact.

**Cons**:
- The logic lives in SQL, out of sight for someone reading only the NestJS code.
- A bug in the trigger blocks user writes, since it runs inside them.
- Harder to unit test than TypeScript; it needs database tests.

### Option 2: Outbox rows written by the app in each transaction

Each service method that changes a person also inserts a feed row, through a shared helper, inside its transaction (the transactional outbox pattern).

**Pros**:
- All logic in TypeScript, next to the write it records; easy to read and unit test.
- The app knows intent (who did it, why), which a trigger can't see.

**Cons**:
- Correct only as long as every path remembers the helper; the profile edit already forgot the audit trail.
- About eight call sites today, plus the seed script and anything added later.
- Same ordering problem as Option 1; needs the same transaction id fix.

### Option 3: Add a sequence to `user_changes`

Reuse the admin audit table as the feed by adding a sequence number and serving it.

**Pros**:
- No new table; admin changes are already recorded there.

**Cons**:
- It records per field rows with an actor, not the person's state, so readers would need a lookup per change.
- Self edits and seeds have no admin actor; the table would need reshaping.
- Mixes an audit trail (who did what) with a sync feed (what is true now), which have different retention and privacy needs.

### Option 4: Change data capture from the Postgres write ahead log

Stream changes from Postgres's internal log (logical decoding, usually through a tool like Debezium and a broker).

**Pros**:
- Complete and ordered by commit, with no triggers in the write path.

**Cons**:
- Needs a connector, a broker or a custom decoder, and replication slots to operate and watch; a stuck slot fills the disk.
- Far more operating cost than the suite's size justifies, and hosted Postgres plans may restrict it.

## Rationale

Completeness is the property that matters most, because its failure is silent. Option 2 is what most teams reach for first, and it reads well, but it depends on every current and future developer remembering a second step, and this codebase has already shown that step being forgotten. Option 1 gets the same guarantee as Option 4 (every committed change is recorded) without any new moving part, at the cost of logic in SQL. That cost is real but bounded: two trigger functions, covered by a test that drives every write path and counts rows, and a note in welinc-auth's `AGENTS.md`. The engineer chose Option 1 after comparing it with Option 2.

Snapshots (the person's state after the change, stored in the row) were chosen over storing only ids, because the contract promises "the state after the change" and because a reader replaying old rows must see what was true then, or the "lost the last role in my system" rule can't be expressed per system.

Transaction id ordering replaces the 5 s rule because it is exact for the same cost (one extra column and a different `WHERE`), and because GA work on shared auth shouldn't rest on a timing assumption. The contract is amended to match.

On the VRMS side, a short poll is the contract's own model and needs no endpoint on VRMS. The lease and per change commits make it safe with two hosted copies and after failures. Keeping the just in time update and adding an instant refresh after VRMS's own saves keeps the picker feeling immediate where people notice it, while dropping the full downloads on page loads.
