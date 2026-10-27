# Review, feat/auth-service-boundary, 2026-10-27

**Reviewed by**: claude-opus-5-5 (author on a different model, per /check review)
**Scope**: 85 files across three repos, branch vs `development` (welinc-auth 15 changed + 5 untracked, welinc-backend-vrms 50, welinc-web-vrms 20; package-lock.json ignored)
**Verdict**: Changes requested

## Summary
The change moves account ownership to welinc-auth. backend-vrms loses its copied auth module and user tables. It gains a live account check in `JwtAuthGuard` and keys `Mechanic` and `AuditLog` on the welinc-auth id. A sync with a just in time fallback keeps the mechanic list current. welinc-auth gains the 0006 hardening, the admin safety guards and the `UserChange` record. Overall quality is high. The account check matches AC-4/6/7/25 closely: SHA 256 key, only 200 cached, exp bound, in flight sharing, 5000 cap and fail closed. The last admin lock is correct under READ COMMITTED, and change rows sit in the same transaction as the write. The one Major is test coverage of the concurrency recovery paths that AC-11 and AC-13 explicitly promise. The rest are smaller races, scope creep and polish.

## Major

### 🟠 The race recovery paths in the mechanic sync have no tests, `welinc-backend-vrms/src/modules/vrms/mechanic-roster.service.ts:184-207`
**Problem**: AC-11 and AC-13 promise that two concurrent syncs, or a sync racing the just in time check, leave one row and never answer 500. A P2002 is supposed to be caught, read again and only updated if the row still differs. `mechanic-roster.service.spec.ts` covers create, update, deactivate, idempotence and the "never throws" case of `ensure`. No test throws a `PrismaClientKnownRequestError` P2002 from `upsert` to exercise the `catch` branch of `write()`: the re-read, the "unchanged" and "updated" outcomes, and a non-P2002 error being rethrown.
**Why it matters**: This is the branch the spec calls out as the safety net for the race, and it is security and data integrity adjacent (one row per `authUserId`). It is easy to break silently. For example, the `instanceof Prisma.PrismaClientKnownRequestError` check fails if the error comes from a different Prisma client instance or adapter wrapping. Nothing would catch that today.
**Suggested fix**: Add cases that make `prisma.mechanic.upsert` reject with a P2002 error, then assert the re-read and the conditional `update` with the right outcome and counts. Add one case where a non-P2002 error propagates from `sync` and is logged and swallowed in `ensure`.

## Minor

### 🟡 updateUser decides the admin guard and the change record from a read made outside the transaction, `welinc-auth/src/auth/auth.service.ts:423`
**Problem**: `existingUser` (isActive, roles, name, email) is read before `$transaction`. Inside the transaction, `assertAnotherAdmin` counts correctly after taking the lock. Whether it runs at all depends on the stale `existingUser.isActive` and `adminSystems(existingUser.roles)`. The same stale data feeds the `mergeRoleAssignments` result and the `oldValue` of the UPDATED and ROLE_CHANGED rows. `updateUserStatus`, `deleteUser` and `unlockUser` read inside the transaction. Only this path does not.
**Why it matters**: Under concurrent edits, the ROLE_CHANGED `oldValue` can be wrong, a role edit can silently undo a concurrent one, and in a narrow case (the target is reactivated between read and write) the last admin check is skipped. AC-19 says each check runs "inside the same transaction as the write".
**Suggested fix**: Move the `findUnique` (and the derived `is*Changing` flags) inside the transaction, after the lock where one is needed. Keep the argon2 hash outside.

### 🟡 Admins of more than one system take the role locks in DB order, `welinc-auth/src/auth/auth.service.ts:482,589,626` with `user-changes.ts:54-62`
**Problem**: The loop calls `assertAnotherAdmin` per system in the order `existing.roles` came back. Each call locks that system's ADMIN role rows. Two transactions on two multi-system admins can lock VRMS then BMS and BMS then VRMS.
**Why it matters**: Postgres resolves this with a deadlock error (40P01). `handlePrismaError` rethrows it as a 500.
**Suggested fix**: Sort `adminSystems(...)` before looping, or lock all affected systems' ADMIN rows in one `FOR UPDATE` query ordered by id.

### 🟡 Sync counts misreport some changes, `welinc-backend-vrms/src/modules/vrms/mechanic-roster.service.ts:147-164,193-198`
**Problem**: A mechanic who is inactive or locked in welinc-auth but active in VRMS goes through `write()` and is counted as `updated`, not `deactivated`. Only rows that left the mechanic set count as `deactivated`. Also, `write()` decides created or updated from a `findUnique` before the `upsert`. With two concurrent syncs, both can see "missing", the native upsert succeeds for both, and both report `created`.
**Why it matters**: Only the numbers are wrong; the rows are right. But AC-11 defines the counts as "only rows that actually changed", and the UI uses `created + updated + deactivated > 0` to refetch.
**Suggested fix**: Count an `isActive: true → false` transition as `deactivated`. Treat the concurrent create count as best effort and say so in a comment, or derive it from `createdAt === updatedAt` on the upsert result.

### 🟡 Admin password set through updateUser writes no change row, `welinc-auth/src/auth/auth.service.ts:474`
**Problem**: `updateUser` accepts `dto.password` and writes a new hash, but no `UserChange` row records that an admin set the password. AC-20 says "every admin write to a user writes UserChange rows". Its list does not name a password field, and no secret may be stored.
**Why it matters**: An admin taking over an account by setting its password is the change you most want traced.
**Suggested fix**: Write an `UPDATED` row with `field: 'password'` and null old and new values. Alternatively, record in the spec that this is deliberately out of scope.

### 🟡 Destructive migration outside the spec in a shared repo, `welinc-auth/prisma/migrations/20261027000100_drop_unused_domain_tables/migration.sql`
**Problem**: The spec says welinc-auth gets "one additive migration" (`UserChange`). This second migration drops 14 domain tables and 6 enums. It looks like a correct cleanup of drift: the schema has no such models, and VMMS and BMS use their own `welinc_db`. But it is not in the spec, and welinc-auth is shared with the other groups.
**Why it matters**: Other groups pull this repo. A destructive migration with no spec line or heads up is a coordination risk, and AGENTS.md says changes to shared pieces need a spec first.
**Suggested fix**: Add a line to spec 0009 (Decision or Migration plan) and the PR description. Tell the VMMS and BMS groups, or split it into its own PR.

### 🟡 Global 503 and 403 toasts can double up with page level error toasts, `welinc-web-vrms/src/lib/api/axios.ts:60,69`
**Problem**: Non-quiet requests get an interceptor toast on 503 and on a wrong role 403. Pages such as `useUserActions` and the repair form also catch the rejection and show their own error toast.
**Why it matters**: The user sees two toasts for one failure. AC-6 asks for at most one 503 toast per 10 seconds.
**Suggested fix**: Mark errors the interceptor already announced (for example `error.handled = true`) and have `getApiErrorMessage` callers skip them. Alternatively, pass `quiet` from callers that toast themselves.

### 🟡 New logic without direct tests: AC-27, the 5000 cap, JwtAuthGuard, audit actors, `welinc-backend-vrms/src/modules/vrms/repairs.service.ts:206-215`, `src/auth/account-check.ts:141-148`, `src/auth/guards/jwt-auth.guard.ts:17-30`, `repairs.service.ts:1182-1197`
**Problem**: No test covers:
- that an unknown or inactive in house id answers 400 "In house mechanic not found" (AC-27);
- that the cache drops its oldest entry at 5000 (AC-4);
- that `JwtAuthGuard` replaces `req.user` with the confirmed user and passes `exp` through;
- that `findAuditActors` returns the newest row per `userId` and leaves out null ids (AC-10; this is raw SQL, so only an integration or verify pass can prove it).
**Why it matters**: These are branching or security relevant paths named in the spec.
**Suggested fix**: Add small unit cases for the first three. Cover the actors query in `/check verify`.

### 🟡 backend-vrms AGENTS.md env list is now wrong, `welinc-backend-vrms/AGENTS.md:47`
**Problem**: The line still lists `JWT_ACCESS_EXPIRY`, `JWT_REFRESH_EXPIRY`, `SEMAPHORE_*` and `SMTP_*`, which this branch removed from `.env.example`. It also omits the new required `AUTH_SERVICE_URL`.
**Why it matters**: The next agent or teammate reads the wrong required config.
**Suggested fix**: Replace the list with the current `.env.example` keys, including `AUTH_SERVICE_URL`. Alternatively, leave it for `/sync`, but don't ship it half updated.

## Nits
- ⚪ `welinc-backend-vrms/src/auth/account-check.ts:79`: on a non-200 or non-401/403 status the response body is never read or cancelled. Undici holds the socket until GC, so call `res.body?.cancel()` before throwing.
- ⚪ `welinc-web-vrms/src/features/repair/lib/repairFormSchema.ts:165`: `id ?? ''` turns a missing id into a server side 400 instead of failing client validation. Prefer making the schema reject an in house chip with no id.
- ⚪ `welinc-auth/src/shared/mail.service.ts:52`: the dev fallback still logs the full email text, including the code, outside production. Fine for local use, but worth a comment that AC-16 relies on SMTP being set in production.
- ⚪ `welinc-backend-vrms/src/modules/vrms/mechanic-roster.service.ts:189`: the extra `findUnique` before `upsert` costs one query per write. `ensure` has already read the row, so it could pass the result in.
- ⚪ `welinc-backend-vrms/src/auth/account-check.fake.ts`: `FakeAccountCheck` has no `whenConfirmed`. Any future e2e that boots `VrmsModule` with the fake fails in `MechanicRoster.onModuleInit`, so add a no-op method.

## Strengths
- `AccountCheck` is a clean, faithful build of the contract. It keys the cache on a token hash, caches only 200s, bounds each entry by the token's `exp`, shares in flight calls without caching failures, caps the cache at 5000 and maps every failure to 503. It forwards only the caller's own already-verified bearer, with no Origin or Referer, to an internal URL from env, never logs the token, and refuses to start without `AUTH_SERVICE_URL`. Its spec covers almost every AC-25 row.
- The last admin guard is correct where it matters: `SELECT … FOR UPDATE` on the system's ADMIN role rows, then a fresh count under READ COMMITTED. Two admins demoting or deactivating each other serialize, and the second gets 409.
- `UserChange` rows are written inside the same interactive transaction as each write, no-op saves write nothing, and tests assert that no password or hash reaches a row.
- `MechanicRoster` never deletes, never touches outsourced rows, writes only on difference, and catches P2002 to keep one row per `authUserId`. `RolesGuard` lost about 70 lines of header and path guessing.

## Test coverage
- welinc-auth: strong. The new `auth.service.admin.spec.ts` covers the self and last admin guards, every change action, no-op saves, setupEmailSent, PORTAL_URL fallback and production refusal, code retirement, RESET_SENT scoping, unlock on reset and changes paging. `jwt.strategy.spec.ts` and `optional-jwt-auth.guard.spec.ts` cover AC-24 and the optional guard.
- welinc-backend-vrms: `account-check.spec.ts` covers the request shape, the 401 and 403 pass through, every 503 cause, TTL, the exp bound, never caching failures and in flight sharing. `mechanic-roster.service.spec.ts` covers the sync's happy path and idempotence, and `ensure`'s create, reactivate and swallow. Not covered: the P2002 recovery (Major), the 5000 cap, `JwtAuthGuard`, AC-27's 400, and the actors SQL.
- welinc-web-vrms: no runner by design. The interceptor's 401, locked 403, other 403 and 503 branches and the sync on open and after save should be exercised in `/check verify`.
