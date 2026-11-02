# 0009. Rationale: auth service boundary

Decision record for [index.md](index.md). `/develop` doesn't read this file.

## Context

welinc-backend-vrms was created from the same template as welinc-auth (VMMS and BMS were too), so it carries a full copy of the auth module and four user tables. The gateway sends `/auth` to welinc-auth, and both frontends call `/auth/*` through it, so the copy is never used. It still runs, though, and port 3002 is published, so anyone can sign in against the stale VRMS `users` table by calling the backend directly.

The two `users` tables hold the same people under different random ids, kept in step only by two seeds. VRMS data points both ways: `Mechanic.userId` points at the VRMS copy, while `AuditLog.userId` holds the welinc-auth id. Code bridges the gap by matching emails. As a result, a user added on the Users page gets no `Mechanic` row and can't be assigned, an email edit silently breaks the mechanic match, and audit names come from a table nobody updates (spec 0006, Follow-up).

VRMS also trusts the token alone. Its strategy reads roles from the token claims and never looks at the account, so a deactivated, locked or demoted user keeps their VRMS rights until the 15 minute token expires. welinc-auth's own strategy does check the database. There is no refresh endpoint.

Constraints: welinc-auth and the portal are shared with the VMMS and BMS groups, so their API shapes must stay stable and their changes small. The feature is tagged GA (a mistake exposes data). Nothing is deployed yet and both databases hold only seed data. Admin OTP (WL-102) and reCAPTCHA (WL-103) are planned on login and need a single place to land.

## Options considered

### Option 1: Fix in place, keep both stores in sync

Keep the VRMS user tables and make welinc-auth push every account change to VRMS (or VRMS pull them), so the ids and fields match. Delete only the VRMS routes.

**Pros**: VRMS keeps local joins to names and emails; no change to how ticket code looks up people.
**Cons**: two copies of every account that can drift; a sync mechanism either inside the shared service or polling it; passwords and role tables still exist in VRMS for no reason.

### Option 2: welinc-auth owns every account; VRMS checks callers live and keys data on the auth id (chosen)

Delete the VRMS copy entirely. VRMS confirms each caller with welinc-auth (cached), stores the welinc-auth id on mechanics and audit rows, and syncs only what it truly owns (its `Mechanic` list) from welinc-auth.

**Pros**: one source of truth; no secrets or role data in VRMS; deactivation takes effect in VRMS; the shared service needs only additive changes.
**Cons**: VRMS depends on welinc-auth being up for every request; names on audit rows become snapshots; a sync is still needed for the mechanic list.

### Option 3: VRMS owns its own users

backend-vrms becomes the sign in service for VRMS users, and welinc-auth handles only the other systems.

**Pros**: VRMS is fully self contained.
**Cons**: breaks the shared SSO portal (it routes by roles across systems); duplicates lockout, OTP and reset; two places to add WL-102 and WL-103; the copied code is already stale.

## Rationale

Option 2 matches what already happens at runtime (welinc-auth serves every login) and removes the parts that only cause harm: an unused login with a live hole, a second account store, and an email bridge that breaks on edits. Option 1 keeps the drift problem and spreads it into the shared service. Option 3 fights the SSO portal the whole suite is built on.

The GA tag decides the revocation question. Trusting a 15 minute token means a removed mechanic can keep changing tickets and costs, so VRMS asks welinc-auth, caches for 30 seconds, and fails closed. Short tokens with refresh would be cleaner, but they change the portal and every group's frontend. The live check gets the same effect inside our own repo.

The `Mechanic` list is real VRMS data (outsourced shops, ticket links), so it stays, keyed on the welinc-auth id. The engineer chose a sync that heals itself (it runs after saves and on the two pages where admins assign) over a Retry button, because a missed Retry leaves a mechanic silently unassignable. The just in time creation on a mechanic's own request is a second safety net.

**Sub decisions taken in the conversation** (the runner up in brackets):
- Owner: welinc-auth owns all (split credentials and VRMS roles; VRMS owns VRMS users).
- Old module: delete it, keep the guards (proxy to welinc-auth; leave the routes and block them).
- User copy: drop it, key on the auth id, names on rows (slim copy refreshed from each token; keep as is).
- Fallback login in web-vrms: remove it, the portal is the one door (dev only; keep as is).
- New mechanic row: web-vrms triggers a VRMS sync, plus just in time (welinc-auth webhook; first sign in only).
- Revocation: ask welinc-auth, cache 30 seconds (trust the token; short tokens plus refresh).
- Auth unreachable: refuse with 503 (let the token through).
- Check scope: every protected route (writes only).
- Existing data: reseed with shared fixed ids (a one time script that maps both databases by email).
- welinc-auth hardening: all four groups, including the admin change record (the record waits for feature 5).
- Change record: one row per changed field, API only for now (one row per action with JSON; a Users page panel now).
- Mechanic on deactivate or role change: mark inactive (delete; leave as is).
- Guard error: 409 with a clear message (403; 400).

## Current state inventory (2026-10-27)

| What | Where | Note |
|---|---|---|
| Copied auth routes (17) | `welinc-backend-vrms/src/auth/auth.controller.ts` | Same list as welinc-auth; wired in `AppModule`; reachable on `:3002` |
| Drift between copies | `auth.service.ts`, `jwt.strategy.ts` | VRMS `profile/summary` counts real VRMS data (unused by web-vrms); VRMS strategy trusts claims, welinc-auth's checks the database |
| VRMS user tables | `welinc-backend-vrms/prisma/schema.prisma` | `User`, `UserRoleAssignment`, `PasswordResetToken`, `RefreshToken`, enums `UserRole`, `SystemType` |
| Mechanic link | `Mechanic.userId` → VRMS `users` | Lookups by `user.email` in `repairs.service.ts` and `config.service.ts` |
| Audit actor | `AuditLog.userId` = welinc-auth id | Names via `findUsersByEmail` on the VRMS copy |
| Token claims | welinc-auth `login` | `sub`, `email`, `roles[]`; no `name`; 15 minute expiry; no refresh endpoint |
| Frontend calls | portal `Login.tsx`, `ForgotPassword.tsx`; web-vrms `authApi.ts`, `StandaloneLoginForm.tsx` | All `/auth/*` through the gateway to welinc-auth |
| Other groups | welinc-backend-vmms, welinc-backend-bms | Same copied module and `users` table; not ours |
| analytics-ai | reads the VRMS Postgres | Uses none of the user tables, so it is unaffected |
