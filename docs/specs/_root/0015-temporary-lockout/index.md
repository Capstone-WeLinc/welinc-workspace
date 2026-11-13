# 0015. Temporary lockout and a clear deactivated answer

**Date**: 2026-11-13
**Status**: Built
**Builds contract sections**: [0001](../0001-shared-services-contract/index.md) version 10 (breaking for a client that reads the lock as permanent or an inactive account as 401; additive: `lockedUntil`)
**Related**: [0009](../0009-email-verification/index.md) (a used code ends a lock), [0011](../0011-account-activity-audit/index.md) (sign in rows), [0012](../0012-profile-extras/index.md) (the lock on every user route), [0013](../0013-suite-admin-model/index.md) (admin unlock)

## Summary

Five wrong passwords in a row used to lock an account until an admin unlocked it. Anyone who knew someone's email could lock them out on purpose, which is the denial of service OWASP warns about for permanent lockouts. The lock now runs out on its own after 15 minutes. The per address limit (10 sign ins a minute) still caps guessing. Separately, a deactivated account used to get "Invalid credentials" even with the right password, so its owner never learned why they couldn't sign in. It now says so, but only after the right password.

## Acceptance criteria

- **AC-1**: The 5th wrong password in a row (sign in, `verify-password`, email change, password change) stamps `locked_at` as before. The lock runs while `now - locked_at < LOCK_MINUTES` (15, in `src/auth/lockout.ts` with `MAX_FAILED_ATTEMPTS`). Every lock check goes through `lockActive`: sign in, the code step finish, the bearer authenticator, the admin session guard, the password check, unlock, the people status filter and the suite report.
- **AC-2**: A lock that ran out needs no write to end. The next wrong password starts the count again at 1 (one atomic UPDATE, `countWrongPassword`), and the next right password clears `locked_at` and the count.
- **AC-3**: Every 403 `ACCOUNT_LOCKED` body carries `lockedUntil` (ISO time) next to the existing `isLocked: true` and `remainingAttempts: 0`. The portal shows "Too many wrong passwords. Try again at <time>, or reset your password."
- **AC-4**: A wrong password on a deactivated account is answered like any wrong password (401, `remainingAttempts`) and counts toward the lock.
- **AC-5**: The right password on a deactivated account answers 403 `ACCOUNT_INACTIVE` ("This account is deactivated. Ask your admin to turn it back on.") and records `SIGN_IN_FAILED` with reason `ACCOUNT_INACTIVE`. `/auth/login/verify-email` answers the same for an account deactivated during its code step (it was 401).
- **AC-6**: The portal words 429 `RATE_LIMITED` on sign in as a network limit, not as "Unable to reach the sign in service".
- **AC-7**: The seed keeps `state.locked@` locked: a reseed keeps a running lock and starts a fresh one when the old one ran out.
- **AC-8**: An admin unlock and a used reset or setup code still end a lock at once. A lock that ran out counts as not locked for unlock (no change row, no alert).

## Decisions

- **15 minutes, not exponential backoff.** One fixed window is simple to explain on the sign in page and in the activity log. The per address limit already slows a scripted guesser to 10 tries a minute.
- **The deactivated answer needs the right password.** Someone without it learns nothing new: a wrong password looks the same for every existing account.
- **No new event type.** A lock that runs out writes nothing; the next sign in row shows the account is usable again. `LOCKED_OUT` and `UNLOCKED` keep their meaning.
- **A constant, not a setting.** `MAX_FAILED_ATTEMPTS` was already a constant; the window sits beside it.
