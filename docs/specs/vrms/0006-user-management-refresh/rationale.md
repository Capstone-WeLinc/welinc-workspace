# 0006. Rationale: user management refresh

Decision record for [index.md](index.md). `/develop` does not need this file.

## Context

Scope feature 14 restyles the Users page on the design system (spec 0001): every modal on the shared dialog, destructive actions confirmed, success and failure as toasts. The BRD (VR-LM-07 to 09) asks for admin only create, edit of name, username and role, deactivate and reactivate, a list with role and status, and account changes that take effect at once. Jira has no story for this page beyond VRMS-42 (a Chief Mechanic role option, feature 17).

The current page works but is legacy built, and reading it next to welinc-auth turned up real problems, not just styling:

- **Reset password sets a shared, known password.** The page sends `Password123!` to `PATCH /auth/users/:id/password` for every user, and its prompt says the user must change it at next sign in. welinc-auth has no such rule, so the default stays in place, the same for everyone.
- **Status is misleading.** "Pending verification" is shown ahead of "Inactive", so a deactivated user who never set a password still looks pending. "Locked" sits behind both.
- **Deactivate is a side effect of Save.** The form's "Active account" checkbox changes status with no confirm, next to the confirmed menu action.
- **Nothing stops an admin from deactivating themselves**, or a mechanic who still holds open tickets.

Constraints that shape the answer:

- The user endpoints live in **welinc-auth**, a shared repo used by other groups, and feature 2 (which service owns users) is undecided. Changes there need agreement and a cross repo spec.
- welinc-auth and welinc-backend-vrms use **separate databases**. `Mechanic.userId` points at the VRMS copy of a user, whose id is its own random uuid, so it never equals the welinc-auth id this page holds. Email is the only shared key.
- The project's UI refresh phase is Facade: UI first, on the data that already exists.
- What welinc-auth already offers: create without a password emails a 1 hour setup code; the public `POST /auth/forgot-password` emails a 10 minute reset code; completing either sets `emailVerified` but does not clear a lock; the JWT strategy rejects inactive users on every request, so deactivation already takes effect at once.

## Options considered

### Option 1: Restyle in place

Swap the markup for spec 0001 components and keep every behavior, including the fixed default password and the active checkbox.

**Pros**:
- Smallest change, frontend only, matches Facade strictly.

**Cons**:
- Ships a known shared password on a restyled page, which makes the flaw look finished.
- Keeps the misleading status order and the unconfirmed status change.

### Option 2: Rebuild on the design system, reset by emailed code, open work check

Rebuild the page around a derived status (sorted and filterable), move create and edit into a react-hook-form dialog, replace the reset with the existing forgot password email, and gate Deactivate on a fresh open work check. The check needs one additive `email` field on `GET /vrms/mechanics/available` in welinc-backend-vrms.

**Pros**:
- Removes the shared password without touching welinc-auth.
- Reuses flows the server already has (setup email, reset email, unlock).
- Fixes the status and self protection problems where the admin sees them.

**Cons**:
- Reset depends on email delivery, with no fallback on this page.
- One small backend change breaks strict Facade.
- Self protection and the open work block are client side only.

### Option 3: Fix it properly in welinc-auth first

Add a "must change password" flag, server side self protection, unlock on reset, and an audit trail, then build the page on top.

**Pros**:
- The rules hold for every client, not just this page.

**Cons**:
- A shared repo change that needs the other groups' agreement and a cross repo spec, and feature 2 may move these endpoints anyway.
- Blocks a UI refresh feature on a foundation decision.

## Rationale

Option 2 removes the one real security flaw (a known shared password) using only endpoints welinc-auth already exposes, so it fits both the Facade phase and the rule that cross repo changes need a spec first. Option 1 was rejected because restyling a broken reset makes it look done. Option 3 is the right end state, but it belongs to feature 2, which hasn't decided who owns users; doing it now risks building on endpoints that move. The server side gaps it would close are listed in the Follow-up for the welinc-auth owners.

The emailed code was picked over a generated temporary password because no admin ever learns the password, and welinc-auth already ties code completion to `emailVerified`. The cost is the dependency on mail, which the engineer accepted.

The open work block was the engineer's call over a warning: a mechanic who can't sign in should never hold an open ticket. Because a wrong match would either miss someone or trap the admin, the match uses email (unique in both databases and the login) instead of name, with name only as a fallback for mechanics with no linked user. The check fetches fresh at click time and fails closed for mechanics, since a stale or missing answer is exactly when tickets get stranded.
