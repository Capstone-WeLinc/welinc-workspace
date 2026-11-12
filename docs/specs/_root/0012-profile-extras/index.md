# 0012. Profile extras: password recheck and account deletion

**Date**: 2026-11-12
**Status**: Accepted

## Summary

welinc-auth gets the two account routes BMS and VMMS already have screens for: a "type your password again" check, and a request to delete your own account that an admin approves or rejects. An approved (or admin made) deletion stops the account at once, then erases the person's personal data after a 30 day grace period, everywhere in the suite, leaving "Deleted user" in history. Phone verification is dropped: no system sends SMS anymore, so the phone stays a plain contact field. VRMS gets the screens for it and stops leaving tickets with mechanics who are gone.

## Requirements

**User stories**:
- As anyone with a WeLinc account, I want to ask for my account to be deleted, so that my personal data does not stay in the suite after I leave.
- As a system admin, I want to see, approve, reject and undo deletions for people in my system, so that a deletion is deliberate and a mistake can be fixed.
- As a Chief Mechanic, I want tickets of a mechanic who is gone to come back to me, so that no repair waits on someone who can't work it.
- As the VMMS and BMS groups, we want working routes behind our existing verify password and deletion screens, so that our profile pages work after the move (S11).

**Acceptance criteria**:

*Password recheck*
- **AC-1**: `POST /auth/profile/verify-password` with `{ password, purpose: "ACCOUNT_DELETION" }` and the right password answers 200 `{ reauthToken, expiresAt }`. The token is a random 256 bit value, good for 5 minutes, stored only as its SHA-256 hash, bound to the user, the purpose and the session (`sid`) of the calling token. Any other `purpose` answers 400 `VALIDATION_FAILED`.
- **AC-2**: One helper, `verifyOwnPassword()`, checks the password on `verify-password`, `POST /auth/profile/email` and `PATCH /auth/profile/password` (replacing their inline checks and old bare 400). A wrong password answers 400 `WRONG_PASSWORD` with `attemptsLeft`, counts in the same `failed_login_attempts` as sign in, and writes `PASSWORD_CONFIRM_FAILED` with `attemptsLeft` and the reason `ACCOUNT_DELETION`, `EMAIL_CHANGE` or `PASSWORD_CHANGE`. The 5th wrong one in a row locks the account (`lockedAt`), writes `LOCKED_OUT` as sign in does, and answers 403 `ACCOUNT_LOCKED`. A right password resets the counter and writes `PASSWORD_CONFIRMED` with the same reason. A locked account never reaches this check: the request authenticator (spec 0002) already answers every user route except `/auth/session` with 403 `ACCOUNT_LOCKED`, right password or not, so no password is tried, no event is written and the counter doesn't move. That answer carries `code: "ACCOUNT_LOCKED"` on every one of those routes (not only on the 5th wrong try). The helper keeps its own locked check as a backstop only. A stored hash that isn't argon2 (the erased `!erased`) fails as a wrong password without counting and never throws. A lock ends no session (contract section 6): the person's refresh and `GET /auth/session` still answer, but the access token is refused on the other user routes until an admin unlocks. `verify-password` also takes at most 10 calls a minute per user (429 `RATE_LIMITED`).
- **AC-3**: A reauth token works once, before it expires, only for its purpose and only with a user token from the same session. An ended session is already refused by the user token guard (401). Anything else (missing, wrong, used, expired, other purpose, another live session) answers 403 `REAUTH_REQUIRED`.

*The person's request*
- **AC-4**: `POST /auth/profile/deletion-request` with `{ reauthToken, reason? }` (reason up to 500 characters, trimmed, empty means none) uses up the token and answers 201 with the request (`status: PENDING`). It writes `DELETION_REQUESTED`, emails the person that the request was received, and emails every admin of every system the person holds (active, not deleted, not the person). A failed email is logged and the request is still saved.
- **AC-5**: A second request while one is pending answers 409 `DELETION_PENDING`. A person who is the last active admin of any system answers 409 `LAST_ADMIN` naming the system. Neither uses up the reauth token: the order is lock the account, check pending, check `LAST_ADMIN`, use the token, insert; a clash on the one pending index (`23505`) also answers `DELETION_PENDING` and rolls back.
- **AC-6**: `GET /auth/profile/deletion-request` answers `{ request }`: the person's latest request (status, reason, requestedAt, decisionNote when rejected, eraseAfter when approved) or `null`.
- **AC-7**: `DELETE /auth/profile/deletion-request` cancels a pending request (status `CANCELLED`, `DELETION_CANCELLED` written, the person emailed) and answers 204, also when nothing is pending or an admin decided it a moment earlier (then nothing changes). After a cancel or a rejection the person may ask again at once.
- **AC-8**: While a request is pending the account works as usual: sign in, sessions, every system.

*Admin review*
- **AC-9**: `GET /auth/deletion-requests?view=pending|grace` (a system admin of the token's `aud`) pages with `cursor` and `limit` (1 to 100, default 50). `pending` lists pending requests of people who hold a role in `aud` now, oldest first (cursor on `requested_at, id`). `grace` lists soft deleted, not yet erased accounts holding a role in `aud` (approved requests and admin deletes), soonest erasure first, each with `eraseAfter` (cursor on `deleted_at, id`). A cursor from the other view answers 400 `INVALID_CURSOR`. `GET /auth/users` items gain `pendingDeletion: boolean`.
- **AC-10**: `POST /auth/deletion-requests/:id/approve` soft deletes the account the way an admin delete does (deleted, inactive, every session ended with `DELETED`, the directory says `deleted`), but without the shared account block (`assertNotShared`): the request is the person's own consent, so an admin of `aud` decides for the whole account even when the person also holds roles in other systems. It sets the request `APPROVED` with the admin, the `aud` and the time, writes `DELETED` once with reason `DELETION_REQUEST`, emails the person the erasure date, and emails the admins of the person's systems except the deciding admin.
- **AC-11**: Every path that changes a request or its account (request, cancel, approve, reject, admin delete, restore, erasure) locks the `users` row first (`lockAccount`), then the request row, and changes status only `WHERE status = 'PENDING'` (or `APPROVED` for restore and erasure), checking the row count. Approve and reject answer 409 `NOT_PENDING` when the request is no longer pending (two admins at once, or a cancel just before), 403 `SELF_DECISION` on your own request, and 404 when the person holds no role in `aud`. Approve checks `LAST_ADMIN` again.
- **AC-12**: `POST /auth/deletion-requests/:id/reject` needs `{ note }` (1 to 500 characters, else 400 `VALIDATION_FAILED`). It sets `REJECTED`, writes `DELETION_REJECTED`, and emails the person the note; `GET /auth/profile/deletion-request` shows it.
- **AC-13**: An admin delete (`DELETE /auth/users/:id`) keeps its checks (`assertNotShared` included). When the person has a pending request, it also closes that request as `APPROVED` by that admin, writes `DELETED` once with reason `DELETION_REQUEST`, and sends the AC-10 emails. Earlier cancelled or rejected requests are left alone.
- **AC-14**: `POST /auth/users/:id/restore` (a system admin of `aud`, the person holds a role in `aud`) brings back an account in grace: `deletedAt` cleared, still inactive, roles kept; an `APPROVED` request becomes `RESTORED`; `RESTORED` is written; the person is emailed. Not deleted, or already erased, answers 409 `NOT_RESTORABLE`. The directory sends an `updated` change (not deleted, inactive); unassigned tickets stay unassigned. Deleting the same account again later makes no new request row (the grace item shows `requestId` null).

*Erasure*
- **AC-15**: The hourly sweep erases every account with `deletedAt` at least `ACCOUNT_ERASURE_GRACE_DAYS` ago and `erasedAt` null, at most 100 people a run, each in its own transaction after the sweep's lock is held (like the event sweep): name `Deleted user`, email `deleted-<id>@erased.invalid`, `contact` and `profilePicture` null, an unusable password hash (`!erased`), `emailVerified` and `passwordSet` false, `erasedAt` set. Its request (if any) becomes `ERASED` with `reason` and `decision_note` null. `ERASED` is written. The same transaction blanks `created_ip`, `last_seen_ip`, `user_agent` and `device_name` on the person's `sessions`, and deletes their refresh tokens, reauth tokens, verification codes and login requests. The old address is read before the transaction; after commit it gets a last "your data was erased" email and the picture file is removed (each failure logged, never retried).
- **AC-16**: The same transaction blanks the personal fields of `account_events` rows whose `user_id` is the person: `ip`, `device`, `userAgent`, `country`, `network`, `asn`, and `oldValue` and `newValue` on rows whose `field` is `name`, `email`, `contact` or `profilePicture`. Rows stay; rows where the person is only the actor on someone else keep just `actor_id`. The transaction's first statement is `set_config('welinc.erasure', 'on', true)`; the append only trigger then allows an `UPDATE` whose only changed columns are those, compares each column of OLD and NEW to prove it, and raises otherwise. Deletes keep their rules (`welinc.event_sweep` stays separate).
- **AC-17**: The same transaction rewrites the person's earlier `directory_changes` snapshots (`txid` other than the current one): name, email, contact and profilePicture get the erased values, and `erasedAt` is left out of them. The commit time trigger then sees a difference and writes exactly one `updated` row whose snapshot has `erasedAt` set, so `DirectoryUser.erased` (`snapshot.erasedAt` not null) is true in the feed and in a full read from `cursor=null`. Contract section 9's "keeps every change" line notes this rewrite.
- **AC-18**: After erasure the old email address is free: an admin can create a new account with it, which gets a new id and no link to the old one. An erased account never shows in `GET /auth/users`, lookups, the directory's people lists, or another person's activity, and `forgot-password` stays silent for it.
- **AC-19**: A failure erasing one person rolls back that person only, is logged with the user id, sends no email, and is tried again the next hour; the others still go through.

*Phone and logging*
- **AC-20**: A change to your own `contact` through `PATCH /auth/profile` writes `UPDATED` with `field: contact`. The catalog lists every new type with a `label` and `labelAdmin`.
- **AC-21**: Contract 0001 becomes version 6 (breaking): the phone routes and `DirectoryUser.phoneVerified` are removed, `DirectoryUser.erased` is added, the S8 rows read as built here with their error codes, and "welinc-auth owns phone numbers and their verified flag" becomes "welinc-auth stores the phone as a plain contact field; no system verifies it". `docs/integration/account-deletion.md` maps the BMS and VMMS screens onto the routes.

*VRMS*
- **AC-22**: My profile gets a Delete account card at the bottom (a danger zone). Delete account opens a dialog with the password, an optional reason (with a counter), and what happens next (an admin reviews; once approved you can't sign in; 30 days later your data is erased). It calls verify password, then the request. A wrong password shows `attemptsLeft` in the field. While pending, the card shows the request date and Cancel request; after a rejection it shows the note and lets you ask again.
- **AC-23**: The Users page gets a Deletion requests chip (admins only) with the pending count. Its view lists pending requests (name, email, reason, asked on) with Approve (a confirm dialog warning that their open tickets will be unassigned) and Reject (a dialog with the required note), then the accounts in grace with "Erased on <date>" and Restore (a confirm dialog). A person with a pending request shows a Pending deletion badge on their usual row (from `pendingDeletion`).
- **AC-24**: VRMS keys on the snapshot's state, never the change type. For each change the feed applier first updates the roster as today, then, when the person is deleted, inactive, or without `MECHANIC` or `CHIEF_MECHANIC` in VRMS, removes them from every ticket in the statuses `release()` covers (`OPEN`, `ASSIGNED`, `IN_PROGRESS`, `ON_HOLD`), in the same transaction as the cursor. Each removal writes a `MECHANIC_UNASSIGNED` audit row with the `SYSTEM` actor (`actorUserId` null, `actorRole` `SYSTEM`) and the reason, picked in the order deleted (`DELETED`, new), deactivated (`DEACTIVATED`), role removed (`ROLE_REMOVED`). Only an `ASSIGNED` ticket left with no mechanic changes status, back to `OPEN`. A ticket put back to `OPEN` joins the open queue like any unassigned ticket (spec 0019: `OPEN` never counts as No mechanic). A ticket past Assigned (`IN_PROGRESS` or `ON_HOLD`) that lost its mechanic keeps its status and shows in the Chief Mechanic dashboard's No mechanic panel. A restored (inactive) person keeps an inactive roster row. Applying the same change again, or replaying the whole feed, changes nothing more; the first replay after this ships releases tickets of mechanics who were already inactive, once. The manual release route stays and answers `{ released: 0 }` when there is nothing left, and its Users page button is hidden.
- **AC-25**: When the feed shows `erased: true`, VRMS sets that `mechanics` row (if any) to `Deleted user` with no email, and rewrites every name and email copy it keeps for that user id to `Deleted user` and null, including string values in audit `changes` equal to the name or email last stored for them. It does this even with no `mechanics` row (a former mechanic now only in another system). Free text that people typed (notes, comments) is left as written. `audit_logs_append_only()` allows exactly this `UPDATE` only when `vrms.erasure` is on in that transaction, comparing columns like AC-16; `TRUNCATE` and `DELETE` stay refused.

## Decision

**Chosen option**: Option 2: request, admin decision, soft delete, erasure after a grace period, all in welinc-auth, with each system cleaning up its own copies from the directory feed.

A purpose bound reauth token guards the request; any one admin of the person's systems decides; every soft deleted account (requested or not) is erased after `ACCOUNT_ERASURE_GRACE_DAYS`; erasure replaces the person with "Deleted user" in welinc-auth and, through a new `erased` flag in the directory, in every system.

**Implementation skills**: `prisma-client-api` and `prisma-cli` (`.claude/skills/`), for the migration, the trigger changes and the erasure transaction · `nestjs-best-practices` (`.claude/skills/`), for the new module and guards · `shadcn`, `react-hook-form` and `vercel-react-best-practices` (`.claude/skills/`), for the VRMS card, dialogs and the Users view.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch** (welinc-auth):

`account_deletion_requests` (new)

| Field | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `user_id` | uuid, FK `users`, Restrict | the person asking |
| `status` | enum `DeletionRequestStatus` | `PENDING`, `CANCELLED`, `REJECTED`, `APPROVED`, `RESTORED`, `ERASED` |
| `reason` | varchar(500) null | blanked at erasure |
| `requested_at` | timestamptz | default now |
| `decided_by_id` | uuid null, FK `users` | approve or reject, or the admin who deleted directly (AC-13) |
| `decided_system` | `SystemType` null | the `aud` the admin acted under |
| `decided_at` | timestamptz null | |
| `decision_note` | varchar(500) null | required on reject, kept after erasure |
| `cancelled_at`, `restored_at`, `erased_at` | timestamptz null | |
| `restored_by_id` | uuid null, FK `users` | |

Partial unique index on `user_id` where `status = 'PENDING'` (one pending per person). Index on `(status, requested_at)`.

`reauth_tokens` (new)

| Field | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `user_id` | uuid, FK `users`, Cascade | |
| `session_id` | FK `sessions`, Cascade | the `sid` of the token that asked |
| `purpose` | enum `ReauthPurpose` | `ACCOUNT_DELETION` |
| `token_hash` | char(64) unique | SHA-256 hex |
| `expires_at` | timestamptz | created + 5 minutes |
| `used_at` | timestamptz null | |
| `created_at` | timestamptz | |

The hourly sweep deletes rows older than 24 hours.

Changed:
- `users.erased_at` timestamptz null. "In grace" is `deleted_at` set and `erased_at` null; erasure is due at `deleted_at` + grace days. Soft delete keeps `user_roles` until erasure (that is what lets admins see and restore the account); erasure keeps them too, since history joins on them and the account can never sign in.
- `AccountEventType` adds `PASSWORD_CONFIRMED` and `PASSWORD_CONFIRM_FAILED` (category `SIGN_IN`, kept a year, carry address and device; `reason` is `ACCOUNT_DELETION`, `EMAIL_CHANGE` or `PASSWORD_CHANGE`, each with a catalog reason label; the failure stores `attemptsLeft`) and `DELETION_REQUESTED`, `DELETION_CANCELLED`, `DELETION_REJECTED`, `RESTORED`, `ERASED` (category `ACCOUNT`). Approval reuses `DELETED` with reason `DELETION_REQUEST`. The `CHECK` constraint is rebuilt from the type map.
- `account_events_append_only()` allows an `UPDATE` only when `current_setting('welinc.erasure', true) = 'on'` and only the columns in AC-16 change; everything else raises as today.
- `directory_snapshot()` adds `erasedAt`; `DirectoryUser` drops `phoneVerified` and adds `erased: boolean`. The change type stays `updated` for an erasure (no new type; readers check the flag).

welinc-backend-vrms: no new tables. The erasure rewrite covers every name or email copy column that sits beside a user id column, matched by that id. Known today: `mechanics` (name, email), `repair_tickets` (`reported_by_name`, `verified_by_name`, `edited_by_name`), `ticket_assignments.assigned_by_name`, `attachments` (`uploaded_by_name`, `deleted_by_name`), `audit_logs` (`actor_name`, `actor_email`, and string values in `changes`), and the `actor_name` of the knowledge, permission, setting, lookup and vehicle change tables. The list lives in one constant, and a unit test reads `prisma/schema.prisma` and fails when a `*_name` or `*email` column next to a `*_user_id` column is missing from it. `ReleaseReason` gains `DELETED`; the transaction body of `release()` moves into a function taking `tx` and an actor, so the feed applier calls it without the `stillActive` guard.

**Emails** (all through the existing mail service and template style, sent after commit, a failure logged and never blocking; dates in Asia/Manila):

| When | To | Says |
|---|---|---|
| request saved | the person | we received your request; an admin reviews it; you can cancel it from your profile |
| request saved | admins of each of the person's systems (active, not deleted, not the person; from `catalog.adminRoles`) | who asked, their reason quoted (or "no reason given"), where to review it |
| cancelled | the person | your request was cancelled |
| rejected | the person | your request was not approved, the admin's note quoted, you may ask again |
| approved or admin delete | the person | your account is closed, your data is erased on <date>, contact an admin before then to undo it |
| approved or admin delete | the admins of the person's systems except the decider | who was deleted, by whom, and the erasure date |
| restored | the person | your account was restored and stays off until an admin turns it on |
| erased | the old address | your personal data was erased |

**State transitions** (`account_deletion_requests.status`):
- `PENDING` → `CANCELLED` (the person) · `REJECTED` (an admin) · `APPROVED` (an admin, or an admin delete)
- `APPROVED` → `RESTORED` (an admin, within grace) · `ERASED` (the sweep)
- `CANCELLED`, `REJECTED`, `RESTORED`, `ERASED` are final. The account itself: active → soft deleted (inactive) → erased, with restore taking soft deleted back to inactive.

**API surface** (all through the gateway's `/auth` route):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/profile/verify-password` | POST | `password` (req), `purpose` (req) | `reauthToken`, `expiresAt` | user token | 400 `WRONG_PASSWORD` + `attemptsLeft`, 403 `ACCOUNT_LOCKED`, 400 `VALIDATION_FAILED` |
| `/auth/profile/deletion-request` | POST | `reauthToken` (req), `reason` (opt) | `DeletionRequestView` | user token | 403 `REAUTH_REQUIRED`, 409 `DELETION_PENDING`, 409 `LAST_ADMIN` |
| `/auth/profile/deletion-request` | GET | none | `{ request: DeletionRequestView \| null }` | user token | none |
| `/auth/profile/deletion-request` | DELETE | none | 204 | user token | none |
| `/auth/deletion-requests` | GET | `view` (req), `cursor`, `limit` | `{ data, nextCursor }` | system admin of `aud` | 400 `VALIDATION_FAILED`, `INVALID_CURSOR` |
| `/auth/deletion-requests/:id/approve` | POST | none | `DeletionRequestView` | system admin of `aud` | 409 `NOT_PENDING`, 409 `LAST_ADMIN`, 403 `SELF_DECISION`, 404 |
| `/auth/deletion-requests/:id/reject` | POST | `note` (req) | `DeletionRequestView` | system admin of `aud` | 400, 409 `NOT_PENDING`, 403 `SELF_DECISION`, 404 |
| `/auth/users/:id/restore` | POST | none | the user body of `/auth/users/:id` | system admin of `aud` | 409 `NOT_RESTORABLE`, 404 |
| `/auth/profile/email`, `/auth/profile/password` | POST, PATCH | as today | as today | user token | wrong password now 400 `WRONG_PASSWORD` + `attemptsLeft` (was a bare 400), 403 `ACCOUNT_LOCKED` |
| `/auth/users` | GET | as today | each item adds `pendingDeletion: boolean` | that system's admin | as today |

`DeletionRequestView` is `{ id, status, reason, requestedAt, decidedAt, decisionNote, eraseAfter, user? }`; `user: { id, name, email, systems }` only on admin routes. A `grace` item is `{ user: { id, name, email }, deletedAt, eraseAfter, requestId }` (`requestId` null for an admin delete). Service tokens get 403 `WRONG_TOKEN_USE` on all of these. `assertAnotherAdmin` gains the code `LAST_ADMIN` on its 409 (the message stays).

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| verify password | `attemptsLeft` | 5 minus `users.failed_login_attempts` after the increment |
| verify password | `expiresAt` | `reauth_tokens.expires_at` (created + 5 minutes, contract section 7) |
| verify password | the session to bind | `sid` claim of the calling user token |
| request | the admins to email | users holding a role whose `system_roles.is_system_admin` is true, in each system in the person's `user_roles`, active, not deleted, not the person |
| request, approve | `LAST_ADMIN` system name | `assertAnotherAdmin` per system the person holds an admin role in |
| approve | `decided_system` | the admin token's `aud` |
| approve, grace list, profile | `eraseAfter` | `users.deleted_at` + `ACCOUNT_ERASURE_GRACE_DAYS`, computed at read time |
| grace list | which accounts | `users` with `deleted_at` set, `erased_at` null, a `user_roles` row in `aud` |
| erasure | the placeholder email | `deleted-` + `users.id` + `@erased.invalid` |
| erasure | the unusable hash | the literal `!erased` (never a valid argon2 string, so every check fails) |
| erasure, emails | the old address for the last email | `users.email` read before the transaction |
| VRMS Users chip | pending count | `GET /auth/deletion-requests?view=pending` page length plus `nextCursor` presence; shown as "50+" past one page |
| VRMS Users badge | Pending deletion | `pendingDeletion` on each `GET /auth/users` item (an `EXISTS` on a pending request) |
| VRMS unassign | reason text | which of `deleted`, `isActive: false`, role missing the snapshot shows, first match in that order |
| VRMS erasure | the old name and email to match in JSON | the `mechanics` row (or the latest copy column) before the rewrite |
| emails | dates | Asia/Manila, like every suite email |

**Key invariants**:
- At most one `PENDING` request per person (the partial unique index).
- A reauth token is used at most once (`UPDATE ... SET used_at = now() WHERE used_at IS NULL AND expires_at > now()` returning a row, inside the request's transaction).
- No approval leaves a system without an active admin.
- Nobody decides their own request.
- An erased account can never sign in, be restored, or be erased again.
- `account_events` and `audit_logs` change only through the erasure, and only in the named columns.

**Security model**:
- The person: their own verify password and request routes, with a user token from any system. Their request is never shown to another person.
- A system admin (`isSystemAdmin` for the token's `aud`, checked on every request): requests and grace accounts of people who hold a role in `aud` now; approve, reject and restore for those people only. One admin's decision covers the whole account, and every other admin of the person's systems is told by email.
- Compliance: the Philippine Data Privacy Act of 2012 (the right to erasure). Every request, decision, restore and erasure is in `account_events`, and stays there with the personal fields blanked.
- Password guessing through a stolen session hits the same 5 try lockout as sign in.

**Configuration required**:
- `ACCOUNT_ERASURE_GRACE_DAYS`: days between a soft delete and erasure, default 30, a whole number from 1 to 365, checked at startup like `ACCOUNT_EVENT_RETENTION_DAYS` (spec 0010). Added to `.env.example` and the env checklist.

**Critical test scenarios**:
- Happy path: verify password, request, admin approve, sessions end, the clock moves past grace, the sweep erases, the feed shows `erased`, VRMS shows Deleted user on old tickets, verifies **AC-1**, **AC-4**, **AC-10**, **AC-15**, **AC-17**, **AC-25**
- Failure case: two admins approve at once, one wins and the other gets `NOT_PENDING`; a cancel racing an approve leaves exactly one outcome; a reauth token used twice or from another session gets `REAUTH_REQUIRED`, verifies **AC-3**, **AC-7**, **AC-11**
- Failure case: an erasure throwing for one person leaves them untouched, sends no email, and erases the rest, verifies **AC-15**, **AC-19**
- Feed: one erasure yields exactly one new feed row with `erased` true; a restore yields `updated` and an inactive roster row; replaying the feed releases nothing twice, verifies **AC-14**, **AC-17**, **AC-24**
- Trigger: an `UPDATE` of any other `account_events` or `audit_logs` column inside the erasure still raises, verifies **AC-16**, **AC-25**
- Lockout: 5 wrong passwords on the email change route lock the account, verifies **AC-2**
- Auth/permission: a VRMS admin can't see or approve a request from someone holding only BMS roles (404); a person approving their own request gets `SELF_DECISION`; the last admin can't ask, verifies **AC-5**, **AC-9**, **AC-11**
- VRMS: a deactivated mechanic's `ASSIGNED` ticket goes back to `OPEN` and shows in the open queue, and an `IN_PROGRESS` ticket of theirs shows under No mechanic, verifies **AC-24**

## Build plan

Tracer Bullet: the thinnest request to approval path end to end first, then each layer thickens.

1. **Thin thread.** Migration: both tables, the enums, `users.erased_at`, the new event types in the `CHECK`. `verifyOwnPassword()` with the shared counter on all three routes; `verify-password`; the request `POST`, `GET` and `DELETE`; approve and reject; events written. VRMS: the Delete account card and the Users page Deletion requests view with Approve and Reject. Satisfies **AC-1**, **AC-2**, **AC-3**, **AC-4** (without emails), **AC-5**, **AC-6**, **AC-7**, **AC-8**, **AC-9** (`pending`), **AC-10** (without emails), **AC-11**, **AC-12**, **AC-22**, **AC-23** (pending part)
2. **Emails, admin delete and restore.** The emails table (all but the erased one), the admin delete closing a pending request, restore, the `grace` view, `pendingDeletion` on the users list, the Pending deletion badge, Restore in VRMS. Satisfies **AC-4**, **AC-10**, **AC-13**, **AC-14**, **AC-9** (`grace`), **AC-23**
3. **Erasure in welinc-auth.** `ACCOUNT_ERASURE_GRACE_DAYS` in the env check; the capped sweep step; the `account_events` trigger exception; the sessions scrub and token deletes; the `directory_snapshot()` and trigger migration with `erasedAt`; the `directory_changes` rewrite; `DirectoryUser.erased`, `phoneVerified` removed; the erased email and picture removal after commit. Satisfies **AC-15**, **AC-16**, **AC-17**, **AC-18**, **AC-19**
4. **VRMS reacts to the feed.** Extract the `release()` body and add `DELETED`; unassign after the roster update on deleted, inactive or role removed; the manual release route answering `{ released: 0 }` and its button hidden; the erasure rewrite with the copy column constant, its schema test, and the `audit_logs` trigger exception. Satisfies **AC-24**, **AC-25**
5. **Phone and contract.** `UPDATED field=contact`, catalog labels, contract 0001 version 6, `docs/integration/account-deletion.md`. Satisfies **AC-20**, **AC-21**

## Consequences

**Positive**:
- BMS and VMMS get real routes behind screens that today do nothing, and the suite has a defensible answer to an erasure request.
- The password guessing gap on the email and password change routes closes.
- Tickets stop waiting on mechanics who are gone, whatever system removed them.

**Negative / tradeoffs**:
- Two append only tables gain a narrow exception. It is guarded by a transaction setting, but a bug in the erasure could now change history; the tests must cover the exact columns.
- VRMS must keep its rewrite list in step: any new name or email copy column added later has to join the erasure, or it leaks. `welinc-backend-vrms/AGENTS.md` should say so.
- Names people typed into free text (ticket notes, comments) are not erased, and audit `changes` holding a name from before a rename are not matched.
- An account whose last role in a system was removed before its deletion drops out of every admin's grace list, so nobody can restore it until S10's suite admin view exists.
- Automatic unassign changes VRMS behavior: the manual Release button goes away, and the first replay after shipping releases tickets of mechanics who were already inactive.
- Contract version 6 is breaking (`phoneVerified` removed, a new 400 code on two profile routes). Only VRMS reads the directory today and it ignores the field.
- A forgetful person can lock their own account from inside a session and needs an admin or a reset code to unlock it.

**Neutral**:
- Unassigning on deactivation means a mechanic back from leave starts with no tickets; the Chief Mechanic assigns them again.
- VMMS keeps Semaphore code in its repo until S11 removes it.

## Follow-up

- [x] Found by the second `/check verify` (2026-11-12), fixed by `/debug` the same day in welinc-auth (not committed yet; run `/check verify` once more for the steps still unticked): (1) welinc-auth `directory.service.ts`: `safePoint()` and `changes()` write `SELECT "txid"::text AS "txid" ... ORDER BY "txid"`, and Postgres sorts by that text alias, so once transaction ids pass 9999 the feed's safe point sticks at the last 4 digit id and every system stops seeing changes (VRMS stopped applying them, so AC-24 could not run live this time). Order by the real column. (2) `POST /auth/profile/deletion-request` and approve send every email before answering; with admins of two systems it ran past the gateway's 60 s and answered 504 (the request was saved). (3) The seed upsert in `prisma/seeds/users.seed.ts` never clears `erased_at`, so reseeding revives an erased account's name and password while it stays marked erased.
- [x] Fix found by `/check verify` (2026-11-12, fixed in welinc-auth, not committed yet): the request authenticator's 403 for a locked account (`request-authenticator.ts`) has no `code`. Add `code: "ACCOUNT_LOCKED"` to it (AC-2). Run `/debug profile extras`.
- [ ] S11 migration guide: BMS changes `{ valid }` to `reauthToken` and reads `GET /auth/profile/deletion-request` instead of `deletionRequestStatus`; VMMS wires its deletion dialog and deletes its phone verification and Semaphore code (they no longer send SMS).
- [ ] S10: the suite admin view shows deletion requests and accounts in grace across all systems (the access report landing page note), and decides requests for people with no system admin left.
- [ ] `/sync`: the erasure rewrite list rule goes into `welinc-backend-vrms/AGENTS.md`; the new routes and the trigger exception go into `welinc-auth/AGENTS.md`.
- [ ] Spec 0005's follow-up "clear the feed snapshots on a real deletion" and spec 0011's "S8 events join this table" close with this spec.
