# Account deletion and password recheck

How a system's profile and admin screens use welinc-auth's account deletion routes (suite spec [0012](../specs/_root/0012-profile-extras/index.md)). Every route goes through the gateway's `/auth` path with the signed in person's user token. A service token gets 403 `WRONG_TOKEN_USE` on all of them.

## What happens, in order

1. The person types their password again. `POST /auth/profile/verify-password` answers a reauth token, good for 5 minutes, usable once, from the same session only.
2. The person sends the request with that token. Their account keeps working while the request waits.
3. Any one admin of any system the person holds a role in approves or rejects it. A reject needs a note, and the person sees it.
4. Approval closes the account at once: it is deleted, every session ends, and nobody can sign in with it.
5. After `ACCOUNT_ERASURE_GRACE_DAYS` (30 by default) welinc-auth erases the person's name, email, phone and picture. Records keep "Deleted user". Until then an admin can restore the account. A restored account comes back turned off.

An admin delete (`DELETE /auth/users/:id`) also starts the grace period, and closes a pending request if there is one.

## Routes for the person

| Step | Call | Answer | Errors to handle |
|---|---|---|---|
| Recheck the password | `POST /auth/profile/verify-password` `{ password, purpose: "ACCOUNT_DELETION" }` | 200 `{ reauthToken, expiresAt }` | 400 `WRONG_PASSWORD` with `attemptsLeft`; 403 `ACCOUNT_LOCKED` (the 5th wrong try locks the account, the same counter as sign in); 400 `VALIDATION_FAILED`; 429 `RATE_LIMITED` (10 a minute) |
| Ask for deletion | `POST /auth/profile/deletion-request` `{ reauthToken, reason? }` (reason up to 500 characters) | 201, the request with `status: "PENDING"` | 403 `REAUTH_REQUIRED` (check the password again); 409 `DELETION_PENDING`; 409 `LAST_ADMIN` (make someone else an admin first) |
| Show the state | `GET /auth/profile/deletion-request` | `{ request }`: the latest request, or `null` | none |
| Cancel | `DELETE /auth/profile/deletion-request` | 204, also when nothing is pending | none |

`request` is `{ id, status, reason, requestedAt, decidedAt, decisionNote, eraseAfter }`. Show `PENDING` with a Cancel button, and `REJECTED` with `decisionNote` and an Ask again button. `CANCELLED` and `RESTORED` mean the person may ask again.

The email change (`POST /auth/profile/email`) and password change (`PATCH /auth/profile/password`) routes now answer a wrong current password the same way: 400 `WRONG_PASSWORD` with `attemptsLeft`, then 403 `ACCOUNT_LOCKED`. The old bare 400 "Current password is incorrect" is gone.

## Routes for an admin

All need the system admin role of the token's system, and see only people who hold a role in it.

| Step | Call | Answer | Errors |
|---|---|---|---|
| Pending requests | `GET /auth/deletion-requests?view=pending&cursor=&limit=` | `{ data, nextCursor }`, oldest first; each item has `user: { id, name, email, systems }` | 400 `VALIDATION_FAILED`, `INVALID_CURSOR` |
| Accounts in grace | `GET /auth/deletion-requests?view=grace` | `{ data, nextCursor }` of `{ user, deletedAt, eraseAfter, requestId }`, soonest erasure first | same |
| Approve | `POST /auth/deletion-requests/:id/approve` | the request, now `APPROVED` with `eraseAfter` | 409 `NOT_PENDING`, 409 `LAST_ADMIN`, 403 `SELF_DECISION`, 404 |
| Reject | `POST /auth/deletion-requests/:id/reject` `{ note }` (1 to 500 characters) | the request, now `REJECTED` | 400, 409 `NOT_PENDING`, 403 `SELF_DECISION`, 404 |
| Restore | `POST /auth/users/:id/restore` | the user, turned off | 409 `NOT_RESTORABLE`, 404 |

`GET /auth/users` items carry `pendingDeletion: boolean`, so the users list can show a badge.

## What each group's screens change

- **BMS** (`welinc-web-bms`, `ProfilePage.tsx`): the verify call already posts to `/auth/profile/verify-password`. Add `purpose: "ACCOUNT_DELETION"` and keep `reauthToken` from the answer instead of reading `{ valid }`. Send `{ reauthToken, reason }` to `POST /auth/profile/deletion-request`. Read the state from `GET /auth/profile/deletion-request` instead of the user's `deletionRequestStatus`.
- **VMMS** (`welinc-web-vmms`, `Profile.tsx`): wire the existing delete dialog to the two calls above. Remove the phone verification calls (`/auth/profile/phone/send-verification` and `/auth/profile/phone/verify`) and the Semaphore code: no system sends SMS, and the phone is a plain contact field saved through `PATCH /auth/profile`.
- **VRMS** is done: the Delete account card on My profile and the Deletion requests chip on the Users page.

## Reading the directory after an erasure

The directory (`/auth/directory/*`) has no `phoneVerified` any more. `DirectoryUser.erased` is true once a person is erased. The feed says it with one `updated` change, and the person's earlier snapshots already read "Deleted user". Key on the flags (`deleted`, `isActive`, `erased`), never on the change type. A system that copies names or emails should rewrite its copies for that user id when `erased` turns true, as VRMS does (`welinc-backend-vrms/src/modules/vrms/directory/erasure-rewrite.ts`).
