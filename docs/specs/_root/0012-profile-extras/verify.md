# Verify: profile extras · spec 0012 · updated 2026-11-12
_Steps derived from spec 0012 acceptance criteria and its Value sourcing table. `/check verify` runs these; `/test` locks the durable ones. Local mail is real Gmail: use seed accounts on `@welinc.com` (logged, not sent) and never trigger mail to a real inbox._

## UI / manual (VRMS, signed in through the portal)
- [x] My profile as a mechanic (`vrms.mechanic…@welinc.com`) → the Delete account card shows at the bottom → AC-22
- [x] Delete account → wrong password → the field says "N tries left before your account locks", N goes 4, 3 … → AC-2, AC-22 (Value sourcing: `attemptsLeft` = 5 minus the counter)
- [x] Delete account → right password, a reason of 500 characters (counter shows 500 of 500), Ask to delete → card shows "You asked … on <Manila date>" with Cancel request → AC-1, AC-4, AC-22 (Value sourcing: dates in Asia/Manila; try with the device zone set to UTC)
- [x] Cancel request → confirm → card is back to Delete account; ask again at once works → AC-7
- [x] While pending, open another system and VRMS pages as that person: everything works → AC-8
- [x] As the VRMS admin, Users page → Deletion requests chip shows the pending count → AC-23 (Value sourcing: page length plus `nextCursor`, "50+" past one page)
- [x] The person's row shows a Pending deletion badge → AC-9, AC-23 (Value sourcing: `pendingDeletion`)
- [x] Reject with an empty note → field error; with a note → toast; the person's card shows the note and Ask again → AC-12, AC-22
- [x] Ask again, then Approve → confirm warns about unassigned tickets → the person is signed out everywhere within 30 s and can't sign in → AC-10
- [x] The approved person shows in "Deleted, not erased yet" with "Erased on <deletedAt + 30 days>" → AC-9 grace, AC-23 (Value sourcing: `eraseAfter` computed at read time)
- [x] Restore → the account is back, turned off, roles kept; "Deleted, not erased yet" no longer lists it → AC-14
- [x] A mechanic with an Assigned ticket is deactivated → within about 30 s the ticket is Open (in the open queue, not the No mechanic panel), its Activity shows "<name> was taken off. The ticket went back to Open." with the reason "Account deactivated" and no person named as the actor → AC-24
- [x] A mechanic with an In progress ticket is deactivated → within about 30 s the ticket keeps its status, shows "No mechanic" on the ticket and in the Chief Mechanic dashboard's No mechanic panel, and the roster shows them Inactive → AC-24 (run 2026-11-12)
- [x] Deactivate a mechanic with open tickets → one confirm says the tickets go back to the queue (no Keep choice) → AC-24
- [x] Change email or password with a wrong current password → the field shows the tries left → AC-2

## Commands
- [x] `docker exec welinc_auth_service npm run test:db` → 64 pass, including `account-erasure.db-spec.ts` → AC-15 to AC-17, key invariant (one pending)
- [ ] `curl -X POST localhost:3000/auth/profile/verify-password` with a service token → 403 `WRONG_TOKEN_USE` → API surface (not run live: needs the VRMS client key from `.env`; the guard is covered by the unit tests, `deletion.controller.ts` takes no service scope)
- [x] verify-password with `purpose: "OTHER"` → 400 `VALIDATION_FAILED` → AC-1
- [x] verify-password 11 times in a minute → the 11th answers 429 `RATE_LIMITED` with `Retry-After` → AC-2
- [x] Use one reauth token twice → second request 403 `REAUTH_REQUIRED`; use it from a second session of the same person → 403 `REAUTH_REQUIRED`; wait 5 minutes → 403 → AC-3 (Value sourcing: `sid` of the calling token, `expires_at` = created + 5 minutes)
- [x] Request while pending → 409 `DELETION_PENDING`; the token stays usable → AC-5
- [x] The only VRMS admin asks → 409 `LAST_ADMIN` naming VRMS, token unused → AC-5 (Value sourcing: `assertAnotherAdmin` per admin system)
- [x] Two approves of one request at once → one 200, one 409 `NOT_PENDING`; cancel racing approve → exactly one outcome → AC-11
- [x] Approve your own request → 403 `SELF_DECISION`; a VRMS admin approving a BMS only person → 404 → AC-11, Security model
- [x] Approve a person who also holds BMS roles → 200 (no shared account block), BMS admins get the email, the decider does not → AC-10 (Value sourcing: admins from `system_roles.is_system_admin`, active, not deleted, not the person)
- [x] `DELETE /auth/users/:id` on a person with a pending request → request `APPROVED` by that admin, one `DELETED` with reason `DELETION_REQUEST` → AC-13
- [x] Restore a person not deleted, or erased → 409 `NOT_RESTORABLE` → AC-14
- [x] `GET /auth/deletion-requests?view=grace&cursor=<a pending cursor>` → 400 `INVALID_CURSOR`; `limit=0` or `101` → 400 `VALIDATION_FAILED` → AC-9
- [x] Set a deleted person's `deleted_at` to 31 days ago, run the sweep (`SessionSweeper.sweep`) → name `Deleted user`, email `deleted-<id>@erased.invalid`, sessions without address, events without address, one feed `updated` row with `erasedAt` → AC-15 to AC-17 (Value sourcing: placeholder email from `users.id`, `!erased` hash, old address read before the transaction)
- [ ] After that, `POST /auth/users` with the old email → a new account with a new id → AC-18 (not run live: it emails a setup code through the real SMTP; covered by `account-erasure.db-spec.ts`, "frees the old email", AC-18)
- [x] Erased person in VRMS: their mechanics row, ticket names and audit actor read "Deleted user" with no email; audit `changes` that named them read "Deleted user"; ticket notes unchanged → AC-25
- [x] With `ACCOUNT_ERASURE_GRACE_DAYS=0` or `366` → the service refuses to start → Configuration
- [x] `PATCH /auth/profile` with a new contact → an `UPDATED` event with `field: contact` → AC-20
- [x] Lock an account (5 wrong passwords on `POST /auth/profile/email`), then call `verify-password`, `/auth/me` and `PATCH /auth/profile/password` with its token → every answer is 403 with `code: "ACCOUNT_LOCKED"`, no password event is written, `/auth/session` still answers 200; an admin unlock restores it → AC-2
- [x] Contract 0001 says version 6; `GET /auth/directory/users` items have `erased` and no `phoneVerified`; `POST /auth/profile/phone` answers 404; the section 10 rows, section 11 codes and section 12 limit match what the routes above answered → AC-21

## Acceptance-criteria coverage
- AC-1 … verify-password commands, Delete account flow · AC-2 … wrong password steps, rate limit · AC-3 … token reuse, other session, expiry
- AC-4 … request flow · AC-5 … DELETION_PENDING, LAST_ADMIN · AC-6 … card state · AC-7 … cancel · AC-8 … works while pending
- AC-9 … chip, badge, cursors · AC-10 … approve, emails · AC-11 … races, SELF_DECISION, 404 · AC-12 … reject · AC-13 … admin delete · AC-14 … restore
- AC-15 to AC-19 … sweep step, test:db, old email reuse · AC-20 … contact event · AC-21 … contract check step (written 2026-11-12, contract 0001 version 6)
- AC-22, AC-23 … VRMS UI steps · AC-24 … deactivate mechanic steps · AC-25 … erased rewrite step
