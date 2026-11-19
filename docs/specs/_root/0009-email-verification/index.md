# 0009. Email verification and one shared code service

**Date**: 2026-11-10
**Status**: Accepted
**Amended**: 2026-11-19 (`/architect`, in place): AC-32, mail to seed addresses goes to the log on staging too, behind a staging only `SEED_MAIL_TO_LOG` setting, so seed admins can finish the sign in code step there and no code is mailed to `welinc.com`, a domain we don't own.
**Amended**: 2026-11-20 (`/architect`, in place): AC-33, on staging mail to seed addresses goes to one team Gmail inbox by plus addressing (`SEED_MAIL_REDIRECT`), so the defense demo signs in by an emailed code the panel can watch arrive. The seed addresses themselves don't change anywhere, so no group's seed or manifest changes.
**Scope row**: [S13. Email verification](../../../scope/_root/shared-services.md#s13-email-verification--done)
**Amends contract sections**: [0001](../0001-shared-services-contract/index.md) sections 8 (mobile login), 10 (routes for people), 11 (errors), 12 (limits)
**Related**: [0003](../0003-sessions-refresh-logout/index.md) (sessions, login), [0006](../0006-suite-seed-accounts/index.md) (the `state.unverified@` seed), [0007](../0007-app-initiated-login-launcher/index.md) (the `/auth/login` answer), VRMS spec 0009 (setup codes, admin resets) and 0011 (who may change whose email)

## Summary

Every WeLinc account must prove it owns its email before it can sign in. Proving means typing a 6 digit code that welinc-auth emails to that address. Someone with an unverified email gets the code step right after their password, on the portal and in the mobile apps. Changing your own email keeps the old one until you type the code sent to the new one, and both addresses are told.

All codes (setup, reset, sign in, email change) move into one table and one service: stored hashed (scrambled one way, so a database leak shows no usable code), dead after 5 wrong tries, and limited in how often they can be sent. Admins can no longer type or set anyone's password; setup and reset codes are the only way in.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As a person an admin just created, I want to set my password with the code I was emailed, so that only someone who reads that inbox can take the account.
- As a person whose email is not verified, I want to type a code right after my password, so that I can sign in without asking anyone.
- As a person changing my email, I want my old address kept until I confirm the new one, so that a typo or a stolen session can't take my account.
- As the owner of an old address, I want to be told when the account's email is being changed or was changed, so that I can react.
- As an admin, I want to see who never finished setup and whose email isn't verified, and to send them a reset code, so that I can help someone who is stuck.
- As anyone, I want codes that can't be guessed, so that nobody can reset my password by trying a million numbers.

**Acceptance criteria**:

*Codes, every kind (welinc-auth)*

- **AC-1**: Every code is 6 digits from `crypto.randomInt` (`newOtp()`). Only its argon2 hash is stored, in `verification_codes`; the `password_reset_tokens` table no longer exists. No log line holds a code, a sign in ticket, or a full email address (user id and purpose only); the mail success and failure lines in `MailService` and `trySendMail` change to that too. The one exception is MailService's fallback, which prints the whole email so codes can be read: in development when SMTP is blank (in production it throws instead), and for seed addresses as AC-32 says. A row older than 24 hours is deleted by the hourly session sweep (`session-sweeper.ts`).
- **AC-2**: A user has at most one live code per family. The families are *password* (`PASSWORD_SETUP` and `PASSWORD_RESET` together), *sign in* (`SIGN_IN`) and *email change* (`EMAIL_CHANGE`). Issuing a code retires (sets `used_at` on) the live code of the same family; families never retire each other. Any change of `users.email`, by anyone, retires every live code of that user.
- **AC-3**: `SIGN_IN`, `EMAIL_CHANGE` and `PASSWORD_RESET` codes live 10 minutes; `PASSWORD_SETUP` codes live 60 minutes. An expired code is refused even when it is right.
- **AC-4**: Every wrong code on any route that checks one adds 1 to that row's `attempts`, under a row lock, so two parallel guesses can't both count as the 4th. The 5th wrong try retires the code. A retired, used or expired code is refused even when it is right. On the new routes a wrong try with tries left answers 400 `INVALID_CODE` with `attemptsLeft`, and the 5th wrong try answers 400 `CODE_EXPIRED` (the old routes keep "Invalid or expired OTP"). A code that is not exactly 6 digits fails DTO validation with a plain 400 and is not counted. The lookup, the `argon2.verify` and the increment run inside one transaction holding the row lock. Wrong codes never touch `failed_login_attempts` or `locked_at`.
- **AC-5**: A family sends at most once per 60 seconds and 5 times per rolling hour per user, counted from all its rows' `created_at` (used and retired ones too). The limits bind every sender, admin actions included: creating a user and pressing Send reset code within 60 s answers the wait. Inside the wait or over the limit nothing is sent and the live code is not replaced. Issuing runs in this order: under the user row lock, insert the new row and retire the family's live row, commit, then send. When the send fails, a second transaction deletes the new row and clears `used_at` on the one row this call retired (by id, only if it hasn't expired), so a failed send counts toward neither limit and the earlier code still works.
- **AC-6**: The public code routes (`/auth/forgot-password`, `/auth/verify-otp`, `/auth/reset-password`, `/auth/login/verify-email`, `/auth/login/verify-email/resend`, `/auth/mobile/login/verify-email`, `/auth/mobile/login/verify-email/resend`) allow 10 calls a minute per client IP address (`req.ip`, which the gateway's single `X-Forwarded-For` and `TRUST_PROXY_HOPS` make the real caller, spec 0008), counted before any other work with the existing `ThrottlerStorage` pattern of `mobile.controller.ts`. Keys: `code-public:<ip>` for the three old routes, `code-signin:<ip>` for the four sign in routes. Over it: 429 with `Retry-After`, coded `RATE_LIMITED` on the portal and public routes, `{ "error": "rate_limited" }` on the mobile routes (contract section 12).

*The sign in step*

- **AC-7**: `POST /auth/login` with the right password, a held system and `email_verified` false answers 200 `{ status: "EMAIL_VERIFICATION_REQUIRED", challengeId, email, resendAfter }` with `Cache-Control: no-store`, creates no session, sets no cookie, and emails a `SIGN_IN` code to `users.email`. The checks run in today's order (locked, inactive, password, then 403 `NO_SYSTEM_ACCESS` from spec 0007 AC-3), and the step comes last, so nobody without a system is sent a code. A verified user gets today's answer unchanged.
- **AC-8**: Every right password on an unverified account answers a new `challengeId`: the live `SIGN_IN` row's `challenge_hash` is replaced in the same transaction, so the previous ticket stops working. If the live code was sent less than 60 s ago, or the hourly limit is reached while a code is still live, no email is sent and `resendAfter` gives the seconds left. If 60 s have passed and the limit allows, a fresh code is issued (AC-5) and carries the new ticket. With no live code and the hourly limit reached: 429 `CODE_SEND_LIMIT` with `Retry-After`. When the email fails: 503 `MAIL_FAILED`, handled as AC-5.
- **AC-9**: `POST /auth/login/verify-email` `{ challengeId, code }` (behind `PortalCsrfGuard`) runs in this order. (1) Find the row by `hashOpaque(challengeId)`; an unknown ticket, or one whose row is expired, used or retired: 400 `CODE_EXPIRED`. (2) Check the user as `/auth/login` would now (locked, deactivated, deleted) and work out the systems list again (403 `NO_SYSTEM_ACCESS` if empty); none of these counts a try. (3) Check the code (AC-4). (4) In one transaction: mark the code used and set `email_verified` true. (5) Finish exactly as `/auth/login` does, through one shared method both routes call: `createWeb` with `previousHandle` from the SSO cookie, `setSsoCookie`, and the launcher body.
- **AC-10**: `POST /auth/login/verify-email/resend` `{ challengeId }` with a live ticket sends a new code and retires the old one; the `challenge_hash` moves from the old row to the new one in the same transaction (the old row's is cleared first, keeping the unique index), so the same ticket keeps working; 200 `{ resendAfter: 60 }`. On a failed send AC-5 moves it back with the restored row. Inside the wait or over the hourly limit: 429 `CODE_SEND_LIMIT` with `Retry-After`. When the email fails: 503 `MAIL_FAILED`, and the old code stays live. A dead ticket: 400 `CODE_EXPIRED`.
- **AC-11**: `POST /auth/mobile/login` answers the same 200 body as AC-7 for an unverified user, after its client check, the password, and the `NO_SYSTEM_ACCESS` and `APP_NOT_ALLOWED` checks. Those checks move out of `UserGrantsService.startMobile` into a `checkMobileGrant(client, userId)` that starts nothing, called before the step; `startMobile` then only creates the session. `checkCredentials` also selects and returns `emailVerified`. `POST /auth/mobile/login/verify-email` `{ challengeId, code, clientId, deviceName }` follows AC-9's order, with the client check and `checkMobileGrant` in step (2), and answers the mobile login token body; `POST /auth/mobile/login/verify-email/resend` `{ challengeId }` works like AC-10. Errors follow AC-8 to AC-10 in the mobile error shape. An older mobile client that expects tokens can't read the step body; no mobile app signs in through welinc-auth yet, so S11's guide makes the code screen a required change.
- **AC-12**: Using a setup or reset code on `/auth/reset-password` sets `email_verified` and `password_set` true, on top of today's unlock and the ending of every session. An unverified account may request a reset code.

*Setup and reset codes*

- **AC-13**: `POST /auth/forgot-password` answers the same generic message to every public caller, also inside the wait or over the limit (and then sends nothing). When the caller is an admin of one of the user's systems (the token `OptionalJwtAuthGuard` reads), the wait or limit answers 429 `CODE_SEND_LIMIT` with `Retry-After` instead, so the admin screen can say so. It issues a `PASSWORD_SETUP` code (60 min, setup wording, as `createUser` sends) when `password_set` is false, and a `PASSWORD_RESET` code (10 min, reset wording) otherwise. The admin's `RESET_SENT` change record is written only after a successful send.
- **AC-14**: `/auth/verify-otp` and `/auth/reset-password` keep their URLs, bodies and messages ("Invalid or expired OTP"). They accept the live code of the password family, and only for an active, not deleted user (anyone else gets "Invalid or expired OTP"). `verify-otp` counts wrong tries (AC-4) but never uses up the code.
- **AC-15**: Admins can't set passwords anymore. `POST /auth/users` with `password` and `PATCH /auth/users/:id` with `password` answer 400 (unknown field); `PATCH /auth/users/:id/password` is removed (404). `POST /auth/users` always issues a `PASSWORD_SETUP` code and answers `setupEmailSent` as today, also when it creates the user inactive (as today; the code then works once an admin activates them, while it lives). A new user starts with `password_set` and `email_verified` false. Attaching an existing account (`attachExisting`) issues no code and changes neither flag.
- **AC-16**: `users.password_set` turns true when a password family code is used and stays true after the owner's own password change; nothing turns it back to false. The migration sets it true when `email_verified` is true, or when the user has no row in `password_reset_tokens` at all (an account whose admin typed its password never had a setup code), and false otherwise; it leaves `email_verified` as it is. Every seed person gets `password_set` true: the manifest's `stateFields` sets it, `users.seed.ts` writes it, and `--reset` also clears `verification_codes`. `state.unverified@` keeps `email_verified` false and so meets the sign in step.

*Changing your own email*

- **AC-17**: `POST /auth/profile/email` `{ newEmail, currentPassword }` (user token): a wrong password answers 400 "Current password is incorrect" (as `/auth/profile/password` does); the same address as today (compared lowercased): 400 `SAME_EMAIL`; a domain that can't receive mail: 400 as today; an address any other account holds, compared case insensitively and deleted accounts included (the unique index covers them): 409 `EMAIL_TAKEN`. The same address as the live pending change resends its code under AC-5 instead of starting a new change (there is no separate resend route). Two people may have the same address pending; the first to confirm wins (AC-18). Otherwise it emails an `EMAIL_CHANGE` code to `newEmail`, emails the old address a notice that a change was started (AC-24), and answers 200 `{ pendingEmail, expiresAt, resendAfter }`. `users.email` doesn't change. Inside the wait or over the limit: 429 `CODE_SEND_LIMIT`. When the code email fails: 503 `MAIL_FAILED`, nothing kept, no notice.
- **AC-18**: `POST /auth/profile/email/verify` `{ code }`: the right code sets `users.email` to the pending address and `email_verified` true, writes a `UserChange` (`UPDATED`, field `email`, the person as actor), retires every other live code of the user (AC-2), emails the old address that the change is done, and answers the profile body. Sessions stay. A wrong code: 400 `INVALID_CODE` with `attemptsLeft`. No live change: 400 `CODE_EXPIRED`. The address taken by someone else in the meantime: 409 `EMAIL_TAKEN` (caught from the unique index error, not only from a read before), and the pending change is retired. The check, the update and the retiring run in one transaction under the user row lock (`lockAccount`), so a parallel start or verify for the same user waits.
- **AC-19**: Resending is `POST /auth/profile/email` again with the pending address (AC-17), under AC-5's limits. `DELETE /auth/profile/email` retires the pending change and answers 204, also when none exists.
- **AC-20**: `PATCH /auth/profile` with `email` answers 400 (the field is removed). `GET /auth/me` keeps `emailVerified` and adds `passwordSet` and `pendingEmail` (the address of the live `EMAIL_CHANGE` code, or null).

*An admin changing someone's email*

- **AC-21**: `PATCH /auth/users/:id` with a new email keeps today's rules (system scope, the other system admin block of spec 0011 AC-28, `UserChange`), and also: an admin changing their own email here gets 409 `SELF_EMAIL` (own changes go through `/auth/profile/email`); a taken address answers 409 `EMAIL_TAKEN` (case insensitive, and from the unique index error); a change of letter case only is ignored. The email, `email_verified` false and the retiring of every live code of the user run in the same transaction as the rest of the update. After the commit it emails the old address that an admin changed it, and when `password_set` is false it issues a new `PASSWORD_SETUP` code to the new address (AC-5) and answers `setupEmailSent`, false when that send failed (the admin then presses Send setup code). A failed notice is only logged. Sessions stay; the person meets the sign in step at their next sign in.
- **AC-22**: `GET /auth/users` and every admin answer about a user carry `passwordSet`.
- **AC-23**: The directory feed shows your own email change only when it is confirmed, and an admin's change at once (the triggers already react to `users.email`). `email_verified` and `password_set` stay out of the feed snapshot, so the triggers don't change.
- **AC-24**: Emails, each with a text and an HTML part, with names and addresses HTML escaped: the sign in code, the email change code (to the new address), "an email change was started" and "your email was changed" (to the old address, naming the new one and saying: if this wasn't you, change your password and tell your admin), and "an admin changed your email" (to the old address). Code emails state the lifetime. The old address never receives a code.

*Portal*

- **AC-25**: On the step answer, the sign in card shows "Check your email", "We sent a 6 digit code to {email}", a six box code field (shadcn `InputOTP`) that submits on the 6th digit, a Verify button, Resend with a countdown from `resendAfter`, and "Use a different account" back to the password step. Messages: `INVALID_CODE` "That code isn't right. {n} tries left."; `CODE_EXPIRED` back to the password step with "That code expired. Sign in again to get a new one."; `MAIL_FAILED` "We couldn't send your code. Try again in a minute."; `CODE_SEND_LIMIT` "Too many codes sent. Try again in {n} minutes." Success continues exactly as a login does today (launcher, deep link, `?request=`). The ticket lives in component state only, never in the URL or browser storage.
- **AC-26**: The code field is one real input underneath (`autocomplete="one-time-code"`, `inputMode="numeric"`, digits only), pasting 6 digits fills every box, focus moves into it when the step opens, it has a label, errors are announced (`role="alert"`), and the step works at 375px with visible focus rings.

*VRMS web*

- **AC-27**: My profile shows the email read only with a Change email button. Its dialog asks for the new email and the current password, then the code (six box field, Resend countdown, Cancel), and maps the errors of AC-17 to AC-19 to the fields. While a change is pending (`pendingEmail`), the profile shows "Waiting for you to confirm {pendingEmail}" with Enter code and Cancel. On success a toast confirms it, and the app fetches `/auth/me` again so the profile and the shell show the new email.
- **AC-28**: When the signed in person's `emailVerified` is false (a session from before an admin changed the email), My profile says "Not verified yet. You'll confirm it the next time you sign in."
- **AC-29**: The Users page status is Setup pending when `passwordSet` is false, and a new Email not verified when `passwordSet` is true and `emailVerified` false. Sort order: Locked, Setup pending, Email not verified, Active, Inactive (Inactive last, decided 2026-11-11: the list leads with accounts that need an admin). The Reactivate wording reads `passwordSet`. For Email not verified the code action reads Send reset code and says "Using it sets a new password and confirms their email. They'll also get a code when they next sign in." When an admin edits the email, the field says "They'll confirm the new address at their next sign in, and we'll tell the old one."
- **AC-30**: web-vrms sends no `password` to any admin route, and its `ManagedUser` type carries `passwordSet`.

*Docs*

- **AC-31**: Contract 0001 is amended: section 8 (the mobile step and routes; the reserved OTP shape now shared with feature 34), section 10 (new routes, removed admin password route and fields, `/auth/me` fields), section 11 (`EMAIL_VERIFICATION_REQUIRED` status, `INVALID_CODE`, `CODE_EXPIRED`, `CODE_SEND_LIMIT`, `MAIL_FAILED`, `SAME_EMAIL`, `EMAIL_TAKEN`, `SELF_EMAIL`), section 12 (AC-5 and AC-6 limits). `docs/integration/seed-accounts.md` says `state.unverified@` meets the code step.
- **AC-32** (amended 2026-11-19): An address on a seed domain (`DEV_EMAIL_DOMAINS` in `src/shared/dev-email-domains.ts`: `welinc.com`, `localhost`, `test.com`, `example.com`) is never sent. MailService prints it with the fallback instead when `NODE_ENV` isn't `production`, or when the new setting `SEED_MAIL_TO_LOG` is `true`; the condition is `(!production || seedMailToLog) && isDevAddress(to)`, and it covers all `MailService` callers (codes, deletion, erasure, admin alerts; the seed job and `admin:recover` send no mail). `SEED_MAIL_TO_LOG` is read with the existing strict `flag` helper in `src/config/env.ts` (only `true` or `false`, blank is `false`, anything else fails boot) and listed in `.env.example` as `# SEED_MAIL_TO_LOG=`. The boot check refuses `SEED_MAIL_TO_LOG=true` together with `SENTRY_ENVIRONMENT=production`, worded like the `SENTRY_TEST_ROUTES` rule beside it (it can't refuse on `NODE_ENV=production`, which staging also runs). Bicep sets it on staging's `auth-service` app only, as `union(authSettings, prod ? {} : { SEED_MAIL_TO_LOG: 'true' })`, never in the shared `authSettings` (which also feed the jobs) and not through `seedAllow`. True with no SMTP needs no warning. Every other address goes through SMTP exactly as before, on staging too. In production without the setting, a seed address is sent like any other (as today). The fallback keeps its `[DEVELOPMENT MAIL FALLBACK]` banner so log searches still find it; the comments on `sendMail` and in `dev-email-domains.ts` that say "in development" are updated to name the staging case. The success line still names no address. Out of scope: the other `isDevAddress` use, the DNS check when an account is made (`validateEmailDomain` in `auth.service.ts`), stays development only. Unit tests in `mail.service.spec.ts`: production with the setting on, a seed address is logged and not sent; production with the setting on, a real address is sent; production with the setting off, a seed address is sent; development, a seed address is logged. `env.spec.ts`: `SEED_MAIL_TO_LOG=1` fails boot, and `true` with `SENTRY_ENVIRONMENT=production` is refused. `docs/integration/seed-accounts.md` says staging codes are read from the auth log (`az containerapp logs show -n auth-service -g rg-welinc-staging`).
- **AC-33** (added 2026-11-20): A new setting `SEED_MAIL_REDIRECT`, blank by default, holds an email address with `{tag}` in its local part, for example `welinc.demo+{tag}@gmail.com`. When it is set and the address is a seed address (`isDevAddress(to)`, the same test as AC-32), `MailService` sends the mail through SMTP to the template with `{tag}` replaced by the seed address's local part, lowercased, with any character outside `a` to `z`, `0` to `9`, `.`, `_` and `-` turned into `-` and cut to its first 40 characters (`vrms.admin@welinc.com` goes to `welinc.demo+vrms.admin@gmail.com`). A helper `seedMailRecipient(to, template)` beside `isDevAddress` in `src/shared/dev-email-domains.ts` builds it, and `MailService` reads the template in its constructor, like `seedMailToLog`. Every combination: redirect set, a seed address and SMTP configured → sent to the tagged address; redirect set with no SMTP → AC-32's rule decides (logged when `!production || seedMailToLog`, otherwise production's existing missing transport error); redirect blank → AC-32 unchanged; a real address → sent as is, whatever the settings. A set redirect beats `SEED_MAIL_TO_LOG`. Locally the redirect is blank by default, so nothing changes; a developer who sets it gets real mail in the team inbox, on purpose. Only the recipient changes: subject and body stay as written, so a mail that prints an address in its body (the email change notice, admin alerts) still names the seed address, which is fine for a demo. The success line still names no address (AC-1): `email sent ${tag} redirected`. Two seed addresses with the same local part on different seed domains share a tag; every seed address is `@welinc.com` today, so none collide. `env.ts` reads it as a string: blank, or exactly one `{tag}`, placed before the `@`, and an address that is valid once `{tag}` is replaced (anything else fails boot). The boot check refuses it together with `SENTRY_ENVIRONMENT=production`, worded like AC-32's rule; that is a second layer only (staging sets no `SENTRY_ENVIRONMENT` today), and the real guard is Bicep's `prod ? {} : {...}`. `.env.example` lists `# SEED_MAIL_REDIRECT=`. Bicep sets it on staging's auth app only (`auth-service${nameSuffix}`, live as `auth-service-staging` since VRMS spec 0008 task 18a), from a new `seedMailRedirect` parameter in `infra/env.bicep` (default blank) with its value in `infra/env/staging.parameters.json`, beside `SEED_MAIL_TO_LOG` in the same `prod ? {} : {...}` union, never in `authSettings` (so not on the jobs). `SEED_MAIL_TO_LOG` stays `true` on staging as the fallback if the parameter is blank. Unit tests in `mail.service.spec.ts`: redirect set and a seed address, sent to the tagged address and not logged; redirect set and a real address, sent to the real address; a local part with `+` or uppercase is normalized; a local part over 40 characters is cut; redirect set with no SMTP falls back to AC-32's log. `env.spec.ts`: a template without `{tag}`, with two, or with `{tag}` after the `@` fails boot; set with `SENTRY_ENVIRONMENT=production` is refused. `docs/integration/seed-accounts.md` says staging codes for seed accounts arrive in the team inbox (each account's tag after the `+`), and the auth log only if the redirect is blank.

## Decision

**Chosen option**: a 6 digit code, a sign in step that blocks until it is used, and one shared code service for every code.

Unverified accounts can't sign in until they type an emailed code, carried between requests by a sign in ticket; your own email changes only after the new address is confirmed; an admin's change switches at once and is confirmed at the next sign in; and every code kind shares one hashed, attempt limited, rate limited table.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` and `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-client-api/`, `.claude/skills/prisma-cli/`) · `shadcn` (`.claude/skills/shadcn/`, for `InputOTP` in the portal and web-vrms) · `react-hook-form` (`.claude/skills/react-hook-form/`, the VRMS change email dialog) · `ask-sonner` (`.claude/skills/ask-sonner/`, toasts)

**Recommendations made while writing** (each with the runner up):
- **Hash codes with argon2**, already a welinc-auth dependency, so no new secret. A 6 digit code can't resist an offline guess for long under any hash, but codes live 10 to 60 minutes, so slowing a guess is enough. Runner up: HMAC SHA-256 with a server key, faster and stronger against a database only leak, but one more secret to hold and rotate.
- **Hash sign in tickets with SHA-256** (`hashOpaque`), like login requests and codes in spec 0003: the ticket is long and random, so a fast hash is safe. Runner up: argon2, needless cost.
- **No new environment variables.** The lifetimes and limits live in one `src/auth/codes/code-config.ts`. Runner up: env overrides, which nothing needs yet.
- **A ticket works on either login route** (web or mobile). Whoever holds it already knew the password and reads the inbox, so binding it to a client adds a column for no real gain. Runner up: store the client id on the row.
- **Wrong codes never lock the account.** OWASP warns that lockouts let an attacker lock out a real user on purpose; the code dies instead.
- **The step comes after the system check**, so no code goes to someone with no access.
- **Sessions survive email changes.** A password is needed for your own change, and an admin change is fixed at the next sign in. This matches how a lock blocks new logins only (spec 0003).

## Feature design

**Data model**:

| Table | Column | Type | Rules |
|---|---|---|---|
| `users` (changed) | `password_set` | boolean, not null, default false | Filled from `email_verified` by the migration; turned true by AC-16 only |
| `verification_codes` (new) | `id` | uuid, PK | |
| | `user_id` | uuid, FK `users.id`, on delete cascade | many codes to one user |
| | `purpose` | enum `VerificationPurpose`: `PASSWORD_SETUP`, `PASSWORD_RESET`, `SIGN_IN`, `EMAIL_CHANGE` | |
| | `code_hash` | text, not null | argon2 of the 6 digits |
| | `challenge_hash` | char(64), null | SHA-256 of the sign in ticket; `SIGN_IN` only; unique where not null |
| | `new_email` | varchar(255), null | lowercased; `EMAIL_CHANGE` only |
| | `attempts` | int, not null, default 0 | retired at 5 |
| | `expires_at` | timestamptz, not null | |
| | `used_at` | timestamptz, null | used, or retired by a newer code, a dead count, or an email change |
| | `created_at` | timestamptz, not null, default now | the send limits count these |
| | index | `(user_id, purpose, created_at desc)` | |
| `password_reset_tokens` | | dropped | |

A check constraint holds `challenge_hash` to `SIGN_IN` rows and `new_email` to `EMAIL_CHANGE` rows. "Live" means `used_at` is null and `expires_at` is after now.

**The sign in step** (no stored state machine; a code row moves live → used, or live → retired):

```
password right, has a system
  ├─ email_verified  → session, launcher answer (today)
  └─ not verified    → 200 EMAIL_VERIFICATION_REQUIRED + ticket, code emailed
        ├─ right code      → email_verified = true, session, launcher answer
        ├─ wrong code      → 400 INVALID_CODE (5th wrong retires it)
        ├─ resend          → new code, same ticket
        └─ expired or dead → 400 CODE_EXPIRED, sign in again
```

**API surface** (welinc-auth; `/auth` through the gateway):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/login` | POST | `email`, `password` | launcher body, or 200 `{ status, challengeId, email, resendAfter }` | `PortalCsrfGuard` | as today, 429 `CODE_SEND_LIMIT`, 503 `MAIL_FAILED` |
| `/auth/login/verify-email` | POST | `challengeId`, `code` (6 digits) | launcher body, sets `welinc_sso` | `PortalCsrfGuard` | 400 `INVALID_CODE` (`attemptsLeft`), 400 `CODE_EXPIRED`, 401, 403 locked, 403 `NO_SYSTEM_ACCESS`, 429 `RATE_LIMITED` |
| `/auth/login/verify-email/resend` | POST | `challengeId` | `{ resendAfter }` | `PortalCsrfGuard` | 400 `CODE_EXPIRED`, 429 `CODE_SEND_LIMIT`, 429 `RATE_LIMITED`, 503 `MAIL_FAILED` |
| `/auth/mobile/login` | POST | as today | token body, or the 200 step body | none (public client) | as today, 429, 503 |
| `/auth/mobile/login/verify-email` | POST | `challengeId`, `code`, `clientId`, `deviceName` | token body | none | as `/auth/login/verify-email`, plus `INVALID_CLIENT`, `APP_NOT_ALLOWED` |
| `/auth/mobile/login/verify-email/resend` | POST | `challengeId` | `{ resendAfter }` | none | as the portal resend |
| `/auth/forgot-password` | POST | `email` | generic message | optional admin token | 429 `CODE_SEND_LIMIT` (admin caller only), 429 `RATE_LIMITED` |
| `/auth/verify-otp`, `/auth/reset-password` | POST | as today | as today | none | as today, 429 `RATE_LIMITED` |
| `/auth/profile/email` | POST | `newEmail`, `currentPassword` | `{ pendingEmail, expiresAt, resendAfter }` | user token | 400 wrong password, 400 `SAME_EMAIL`, 400 domain, 409 `EMAIL_TAKEN`, 429 `CODE_SEND_LIMIT`, 503 `MAIL_FAILED` |
| `/auth/profile/email/verify` | POST | `code` | profile body | user token | 400 `INVALID_CODE`, 400 `CODE_EXPIRED`, 409 `EMAIL_TAKEN` |
| `/auth/profile/email` | DELETE | none | 204 | user token | none |
| `/auth/profile` | PATCH | `name`, `contact` (no `email`) | profile body | user token | 400 for `email` |
| `/auth/me` | GET | as today | adds `passwordSet`, `pendingEmail` | user token | as today |
| `/auth/users` | POST | as today without `password` | as today | `@SystemAdmin()` | 400 for `password` |
| `/auth/users/:id` | PATCH | as today without `password` | adds `setupEmailSent` when a setup code was due | `@SystemAdmin()` | 400 for `password`, 409 `SELF_EMAIL`, 409 `EMAIL_TAKEN` |
| `/auth/users/:id/password` | PATCH | removed | | | 404 |

**Value sourcing**:

| Action | Value produced or shown | Source |
|---|---|---|
| Sign in step | `challengeId` | `newOpaque()`; only `hashOpaque(ticket)` stored in `challenge_hash` |
| Sign in step | `email` | `users.email` of the user whose password matched |
| Sign in step, resends | `resendAfter` | 60 minus seconds since the family's newest `created_at`, at least 0 |
| Any 429 `CODE_SEND_LIMIT` | `Retry-After` | the wait left, or when the oldest of the last 5 sends in the hour turns an hour old |
| Wrong code | `attemptsLeft` | 5 minus `attempts` after the increment |
| Code emails | lifetime text | `code-config.ts` for the purpose |
| Email change | `pendingEmail`, `expiresAt` | `new_email`, `expires_at` of the live `EMAIL_CHANGE` row |
| Notice emails | old address | `users.email` read inside the transaction, before the update |
| `/auth/me`, admin answers | `passwordSet` | `users.password_set` |
| VRMS status | Setup pending, Email not verified | `passwordSet`, `emailVerified` on `ManagedUser` |
| Portal and VRMS countdown | seconds | `resendAfter` from the last answer, counted down in the browser |
| Admin forgot password caller | is an admin | `OptionalJwtAuthGuard` user and `holdsAdmin` over the target's systems (existing code) |
| Forgot password, admin resend | setup or reset code | `users.password_set` (false: `PASSWORD_SETUP`) |
| Per address limit | the caller | `req.ip`, keys `code-public:<ip>` and `code-signin:<ip>` |
| Restoring after a failed send | which row to bring back | the id of the row this call retired, held in memory between the two transactions |

**Key invariants**:
- At most one live code per user per family (checked inside the transaction that issues one, under the user row lock).
- `users.email` changes only through an admin edit or a used `EMAIL_CHANGE` code; either one retires every live code of that user.
- A session is never created for a user whose `email_verified` is false.
- No code, ticket or full email in logs; codes and tickets are never stored in plain text.
- Code checks compare hashes only (`argon2.verify`), never the plain value.
- Systems identify a person by the token's `sub` only, never by its `email`: an access token issued before an email change carries the old address until it refreshes.
- `users.email`, `email_verified` and code retiring for one change commit in one transaction, so the deferred directory trigger writes one row per change.

**Security model**:
- Public routes (forgot, verify-otp, reset, the two sign in verify routes and their resends) rely on the code plus, for sign in, the ticket that only a right password yields. Each is rate limited per address (AC-6) and per code (AC-4).
- `/auth/profile/email*` act only on the token's own user; starting a change needs the current password.
- Admin email changes keep spec 0011's scope rules; admins can no longer set passwords.
- Enumeration: forgot-password stays generic to the public. `EMAIL_TAKEN` is shown only to a signed in user who just gave their password, an accepted trade for clear errors among staff.
- Personal data: `new_email` on a code row is the only new copy, deleted with the row after 24 hours (AC-1).
- Accepted risk: anyone who knows an address can spend its codes (5 wrong `verify-otp` calls) or its 5 sends an hour, delaying that person's setup or reset by up to an hour. Inside the 60 s wait nothing is replaced (AC-5), and admins see the wait. Locking out an account would be worse, and the address limit slows a single caller.

**Configuration required**: none. No new environment variables; the existing `SMTP_*` must work wherever unverified users exist, since they can't sign in without mail.

**Critical test scenarios**:
- Happy path: `state.unverified@` signs in on the portal, gets the step, types the code, lands on the launcher, and next time signs in straight away, verifies **AC-7**, **AC-9**, **AC-25**.
- Guessing: 5 wrong codes retire the code and a 6th right one is refused; 11 calls a minute from one address get 429, verifies **AC-4**, **AC-6**.
- Parallel guesses: two wrong codes sent at once leave `attempts` at exactly 2, verifies **AC-4**.
- Old reset route: a right reset code still works through the unchanged body; 5 wrong ones kill it, verifies **AC-14**.
- Email change: start, wrong code, resend, right code; the email changes only at the end, the old address gets both notices, the directory feed shows one change, verifies **AC-17**, **AC-18**, **AC-23**, **AC-24**.
- Admin change of a setup pending user: the setup code goes to the new address and the old code no longer works, verifies **AC-2**, **AC-21**.
- Mail down: the step answers 503 and the limits don't count it, verifies **AC-5**, **AC-8**.
- Denied: `PATCH /auth/users/:id/password` is 404, `password` on create is 400, `email` on profile PATCH is 400, verifies **AC-15**, **AC-20**.

## Build plan

Tracer Bullet: the first slice runs the whole sign in step end to end on the portal before the other code kinds move onto the service.

1. Migration: `verification_codes` with the enum, check constraint, unique partial index and index; `users.password_set` filled from `email_verified`; drop `password_reset_tokens`. `npx prisma generate`, and `test:db` covers the backfill, satisfies **AC-1**, **AC-16**
2. The code service in `src/auth/codes/`: `code-config.ts`, issue (family retire, wait and hourly limit, the restore on mail failure), check (row lock, argon2 verify, attempts, retire at 5), `retireAllFor(user)`, the 24 hour delete in `session-sweeper.ts`, the mail log lines without addresses, and unit tests for each rule, satisfies **AC-1** to **AC-5**
3. The sign in step on `/auth/login` (`emailVerified` from `checkCredentials`), `/auth/login/verify-email` and its resend, the shared login finishing method, the per address limit on them, the sign in code email; update `sso.controller.spec.ts` and the login specs for the new answer, satisfies **AC-6** to **AC-10**, **AC-24**
4. Portal: the code step in `Login.tsx` with shadcn `InputOTP`, its messages, focus and countdown; live check with `state.unverified@` (SMTP blank, code read from the log), satisfies **AC-25**, **AC-26**
5. Setup and reset onto the service: `forgotPassword`, `verifyOtp`, `otpResetPassword` and `createUser` use it; the admin 429 and `RESET_SENT` after the send; setup or reset by `password_set`; `password_set` writes; the per address limit on the three old routes; rewrite the unit specs that mock `passwordResetToken`, satisfies **AC-6**, **AC-12** to **AC-14**, **AC-16**
6. Remove typed passwords: `password` out of `CreateUserDto` and `UpdateUserDto`, the `PATCH /auth/users/:id/password` route and `resetPassword` gone, `passwordSet` on every admin answer; seed manifest, `users.seed.ts` and `--reset` handle `password_set` and `verification_codes`; remove or rewrite the admin password tests in `auth.service.admin.spec.ts`, `auth.service.roles.spec.ts` and `auth.service.scope.spec.ts`, satisfies **AC-15**, **AC-16**, **AC-22**
7. Email changes in welinc-auth: the three `/auth/profile/email*` routes, the `SELF_EMAIL` and `EMAIL_TAKEN` rules on the admin route, `email` out of `UpdateProfileDto`, `/auth/me` fields, the admin change rules in `updateUser`, the four notice and code emails, satisfies **AC-17** to **AC-21**, **AC-23**, **AC-24**
8. Mobile: `checkMobileGrant` split out of `startMobile`, the step on `/auth/mobile/login`, the two mobile routes, and the mobile controller and grants specs updated; tested by API, satisfies **AC-11**
9. web-vrms: `passwordSet` in `ManagedUser`, the two statuses and their wording, the Edit dialog note, My profile's Change email dialog and pending state with `InputOTP`, satisfies **AC-27** to **AC-30**
10. Contract 0001 amendments and `docs/integration/seed-accounts.md`, satisfies **AC-31**
11. (Amendment, 2026-11-19) `SEED_MAIL_TO_LOG` in `env.ts` and `.env.example`, the seed address rule in `MailService.sendMail`, the four unit tests, the boot refusal and its `env.spec.ts` cases, the comment updates, `SEED_MAIL_TO_LOG: 'true'` on staging's `auth-service` app only in `infra/env.bicep` (`union(authSettings, prod ? {} : {...})`, not in `authSettings`, so not on the jobs), and the staging line in `seed-accounts.md`, satisfies **AC-32**
12. (Amendment, 2026-11-20) `SEED_MAIL_REDIRECT` in `env.ts` and `.env.example`, the tag rule and its place before AC-32's in `MailService.sendMail`, the three unit tests, the boot checks and their `env.spec.ts` cases, the `seedMailRedirect` parameter in `infra/env.bicep` set in `staging.parameters.json`, then `apply.sh staging`, and the staging line in `seed-accounts.md`. Before the apply: the team creates the shared Gmail (its login in the password manager, two step sign in on) and Brevo's sender `WeLinc <noreply@welinc.app>` exists, satisfies **AC-33**

## Consequences

**Positive**:
- `emailVerified` finally means what it says, and every account proves its address before anyone relies on it.
- The reset route stops being guessable: today a 6 digit reset code can be tried without limit, and a right guess takes over the account.
- One code service means one place to audit, and feature 34's admin OTP can reuse the sign in ticket and step.
- Admins never know anyone's password.

**Negative / tradeoffs**:
- A mail outage now stops unverified people from signing in. Today nobody unverified exists outside the seed, but staging and production need working mail (feature 26 picks the provider) before real users are added.
- Dropping `password_reset_tokens` voids codes already sent; anyone mid setup or reset asks again. Only local data exists today.
- The `/auth/login` answer gains a second shape (a `status` body), so every login client must check for it: the portal now, the VMMS and BMS mobile apps in S11.
- Someone who knows an address can spend its codes and delay a setup or reset by up to an hour (accepted, see the Security model).
- Removing admin password routes breaks the BMS page that resets people to a fixed default password, once BMS moves onto welinc-auth (S11).
- The six box field adds the `input-otp` package to the portal and web-vrms.
- (AC-33) Anyone with the team Gmail's login reads every seed account's code on staging; that's the point (the panel watches it arrive), and those accounts' passwords are public anyway. Real people never touch it: only seed addresses are redirected. Bicep keeps it off production (only the staging parameters file sets it); the boot refusal with `SENTRY_ENVIRONMENT=production` is a second layer. Brevo's free plan (about 300 mails a day) covers demo use. The redirect is one parameter, so pointing it elsewhere (Testmail, another inbox) later is a value change, not code.
- (AC-32) On staging the auth log holds sign in codes and seed addresses for 30 days (the Log Analytics retention in `infra/modules/platform.bicep`). That's accepted: the codes expire after 10 minutes, those accounts' passwords are public anyway, and only people with access to the Azure subscription can read the log. Two guards keep it off production: Bicep sets it only when the environment isn't `prod`, and the boot check refuses it with `SENTRY_ENVIRONMENT=production`. Production also has no seed people (VRMS spec 0008, AC-15). A real person with an address on a seed domain (say `@example.com`) gets no mail on staging; that's fine for a test environment.

**Neutral**:
- A person whose email an admin changed keeps working until their session ends (at most 12 hours on the web), then meets the step.
- Codes remain plain digits in email bodies; anyone reading the mailbox can use them, which is the point of the proof.

## Migration plan

**Strategy**: one deploy of welinc-auth with its migration (`npm run db:deploy`), then the portal and web-vrms. The portal needs to ship with or right after welinc-auth, because an unverified user's login answer changes shape.
**Phases**:
1. welinc-auth: migration, service, routes.
2. Portal and web-vrms, merged in the same set of PRs.
**Rollback**: revert the app commits; the migration has no down step, so a rollback past it needs a new migration that brings back `password_reset_tokens` (empty) and drops the new table and column.
**Risks**: a portal older than welinc-auth shows the status body as a failed login for unverified users; merge the set together, as with spec 0007.

## Follow-up

- [ ] S11 migration guide: `vmms-mobile` and `bms-mobile` need the code screen (AC-11); BMS stops resetting to a default password and uses Send reset code; VMMS and BMS profile pages change email through `/auth/profile/email*`.
- [ ] S7: record code events (sent, mail failed, used, retired after 5 wrong tries) in account activity, with the real client address.
- [ ] S10: the portal admin section shows Setup pending and Email not verified and offers Send reset code.
- [ ] Feature 34 (admin OTP): reuse the sign in ticket and step with its own purpose instead of a new mechanism.
- [ ] Feature 26: working mail on staging before any real user is added (the step needs it); set `SMTP_*` there.
- [ ] VRMS spec 0006 (user management refresh): its account status list gains Email not verified (AC-29 here).
- [ ] `/sync` at merge: welinc-auth `AGENTS.md` (the code service, removed admin password routes, the `/auth/login` status body, `PasswordResetToken` gone from the key files row) and `welinc-web-vrms/AGENTS.md` (the statuses, `InputOTP`).
