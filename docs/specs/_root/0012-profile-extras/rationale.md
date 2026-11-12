# 0012. Profile extras: rationale

The decision record behind [index.md](index.md). `/develop` builds from the index; this file explains why.

## Context

Contract 0001 reserved S8 for three account routes the other systems' screens already call: phone verification (VMMS), "type your password again" before a sensitive action (BMS), and an account deletion request (BMS). A read only check of the 2026-11-06 code found that none of them works anywhere. BMS's Profile page posts to `profile/verify-password` and expects `{ valid }`, then posts `profile/deletion-request` with no body and expects `deletionRequestStatus: PENDING`; neither route exists. VMMS's deletion dialog asks for the password and only shows a toast. VMMS verifies phones through its own auth copy with Semaphore SMS.

SMS is gone from the suite. VRMS ruled it out on 2026-10-29 for cost, welinc-auth dropped the Semaphore variables, and the VMMS group told Samuel they won't use SMS anymore. Phone verification has no channel left, so `DirectoryUser.phoneVerified` would stay false forever.

In welinc-auth, the only delete is an admin's soft delete, which keeps name, email, phone and picture forever, and specs 0005 and 0011 both passed "erasure on request" to S8. VRMS copies names and emails into about ten columns at the time of each action, and its `audit_logs` is append only, as is welinc-auth's `account_events`. The email and password change routes check the current password inline, without counting wrong guesses, so a stolen session could guess the password with no limit. The suite rule says no system reads another's database, so welinc-auth can't see anyone's open work.

The forces: the Philippine Data Privacy Act gives people a right to erasure; the audit trail must still hold together; a mistaken approval must be recoverable; a capstone deadline at the end of November; and three groups whose screens need a stable shape.

## Options considered

### Option 1: Soft delete only (the contract as written)

Request, admin approval, soft delete, history kept. No erasure.

**Pros**:
- Smallest build; no append only exceptions; nothing in VRMS changes.

**Cons**:
- The request becomes ceremony: the data stays forever, which does not meet a right to erasure, and specs 0005 and 0011 already flagged that gap.

### Option 2: Soft delete, erase after a grace period (chosen)

Request, admin approval (or an admin delete), soft delete at once, erasure by the hourly sweep after `ACCOUNT_ERASURE_GRACE_DAYS`, with an admin Restore during grace. Erasure replaces the person with "Deleted user" in welinc-auth, its logs and the directory, and each system rewrites its own copies when the feed shows `erased`.

**Pros**:
- A real erasure, and a mistaken approval can be undone for 30 days.
- One rule for every deletion, requested or not.
- Ids stay, so tickets and logs still join up.

**Cons**:
- Two narrow append only exceptions, and VRMS must keep a list of its copy columns.
- Free text names are not erased.

### Option 3: Erase at approval

The same as option 2 with no grace period.

**Pros**:
- Simplest privacy story; no sweep step, no restore.

**Cons**:
- A wrong approval, or an admin clicking the wrong row, destroys the account for good.

### Option 4: Hard delete the user row

Delete the `users` row and let the database cascade.

**Pros**:
- Nothing personal can survive in welinc-auth.

**Cons**:
- `account_events` restricts deletes, every system keeps dangling ids, and the audit trail of who approved the deletion disappears with it.

## Rationale

Option 2 is the only one that meets both forces that matter: the right to erasure, and an audit trail that still holds together. Pseudonymizing (keeping the record, replacing the person) is what Atlassian ("Former user"), GitHub ("ghost") and Slack do for the same reason. The grace period costs one sweep step, which already runs hourly for sessions and events, and buys a safe undo, which matters because any one admin of the person's systems can approve.

The smaller calls follow the same lines:
- **The reauth token is tied to one purpose, one session and one use.** It turns BMS's client side `{ valid }` check into something the server enforces, and a token leaked from one flow can't be used in another.
- **Wrong passwords share the login lockout.** That closes the guessing gap with the rule people already know, instead of a second limit.
- **Any one admin decides.** That avoids a deadlock between groups. The emails to every other admin keep the decision visible.
- **Systems clean up their own copies from the feed.** That follows the suite rule against reading another system's database.
- **VRMS unassigns open tickets on deletion, deactivation and role removal.** That covers every way a mechanic leaves, not just this one, through the unassign release VRMS already has.

Phone verification is dropped rather than sent by email: an emailed code proves nothing about a phone, and SMS is out of the suite. `phoneVerified` is removed rather than kept false, because a field that never changes misleads every reader. Contract changes are cheap while only VRMS reads the directory.

**Smaller calls made in the spec** (each with the runner up):
- **The `SIGN_IN` category for password confirm events**, so they carry address and device and age out after a year like other sign in rows. Runner up: `ACCOUNT`, which keeps them forever.
- **No new feed change type for erasure** (an `erased` flag on `updated`). Readers already apply snapshots, and a new type would break readers that reject unknown types. Runner up: an `erased` change type.
- **`deleted-<id>@erased.invalid` as the placeholder email.** `.invalid` can never receive mail, and the id keeps it unique. Runner up: null email, which the unique, non null column doesn't allow.
- **The literal `!erased` as the password hash**, which never parses as argon2. Runner up: a random hash, which works the same but hides the reason.
- **The last email goes to the old address after the erasure commits** (the address is read first), so the person knows it happened and a failed erasure never sends a false "erased". A send failure is only logged. Runner up: no last email.
- **Approving a request skips the shared account block** that guards admin deletes, because the request is the person's own consent. A direct admin delete of a shared account stays blocked. Runner up: requiring an admin of every system, which brings back the deadlock the team rejected.

**Cross check** (2026-11-12, Sonnet, read only): 25 items, 24 applied. They covered lock order and races, the directory trigger seeing no change on erasure, the order of steps around the reauth token, sessions and tokens left out of the erasure, email timing, the trigger column checks, event reasons, the users list badge source, the VRMS `release()` reuse and replay behavior, and a schema test for VRMS copy columns. Not applied: skipping the lockout count after a recent right password (the existing locked message already says to contact an admin).
