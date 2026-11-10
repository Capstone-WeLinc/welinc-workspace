# 0009. Email verification and one shared code service: rationale

The decision record behind [index.md](index.md). `/develop` builds from `index.md` and can skip this file.

## Context

welinc-auth has an `email_verified` column, but it only means "this person used a setup or reset code once". An admin who types a password when creating an account skips the email entirely, an admin edit of someone's email keeps the old flag, and changing your own email on the profile switches it at once with no password and no record. So the flag can be true for an address nobody ever proved, and the suite then sends reset codes and notices to whatever address is stored, including a mistyped one that belongs to a stranger. (basis: `welinc-auth/src/auth/auth.service.ts`, `createUser`, `updateUser`, `updateOwnProfile`)

The existing codes have their own problem. Setup and reset codes sit in `password_reset_tokens` in plain text, and `/auth/verify-otp` and `/auth/reset-password` have no attempt count and no rate limit. A 6 digit code has a million values and lives 10 minutes, so an unlimited guesser can reset someone's password. The gateway's flood limit (20 a second per address, spec 0008) is far too loose to stop that. (basis: the same file, `verifyOtp`, `otpResetPassword`; spec 0008)

WeLinc has no public sign up: every account is staff created by an admin of some system. Mechanics, drivers and helpers sign in on phones through the VMMS and BMS mobile apps (contract section 8), so any proof must work in a native app without browser redirects. The suite must be deployed by the end of November 2026, and this row is planned to finish within days.

The scope row asks for: a code or link on every new account and email change, `emailVerified` true only after it is used, visibility and resend for admins and the user, and a decided and enforced rule for unverified accounts. The seed already has `state.unverified@welinc.com` waiting for that rule (spec 0006).

## Options considered

### How a person proves the address

**Option 1: a 6 digit code.** The address gets a short code that the person types where they already are.
- Pros: same pattern as the setup and reset codes people already know; works the same in the portal and in native apps; nothing for mail scanners to consume.
- Cons: typing six digits, and on a phone switching from the mail app; a code can be relayed by a phishing page in real time.

**Option 2: a link.** The address gets a one time link.
- Pros: one tap.
- Cons: the link opens wherever the mail client chooses, not where the sign in is waiting; native apps need deep links on a domain that isn't registered yet; mail security scanners open links and can use them up, which needs an extra confirm page.

**Option 3: both in one email.**
- Pros: the reader picks.
- Cons: two secrets for one job, each stored, limited and expired, and each must cancel the other; twice the testing.

### What an unverified account may do

**Option 1: block, with a code step right after the password.**
- Pros: one clear rule; catches a mistyped address on day one; one time cost for staff.
- Cons: a mail outage blocks unverified people from signing in.

**Option 2: allow for 7 days, then block.**
- Pros: an outage can't stop a first sign in.
- Cons: a deadline state, a banner, and more cases to test, for a population an admin just created.

**Option 3: always allow, banner only.**
- Pros: least work.
- Cons: the flag then protects nothing.

### How the sign in step remembers that the password was right

**Option 1: a ticket.** The login answers "next step" with a random ticket; the code only works together with it. This is the shape contract 0001 already reserved for the admin OTP.
- Pros: a code alone is useless, so nobody can guess codes without the password; the password is never sent twice; feature 34 reuses it.
- Cons: a second answer shape on `/auth/login` that every client must handle.

**Option 2: an error, then email plus code.**
- Pros: the login answer keeps one shape.
- Cons: the verify route takes only an email and a code, so anyone who knows a staff email can try codes; the fix (sending the password again) keeps the password in the browser.

### Changing your own email

**Option 1: keep the old address until the new one is confirmed, with the password.**
- Pros: a typo can't lock anyone out; a stolen session alone can't move the account.
- Cons: a pending state to show and cancel.

**Option 2: the same without the password.**
- Pros: one field less.
- Cons: a stolen session plus an attacker's own inbox moves the account.

**Option 3: switch at once, verify at next sign in.**
- Pros: least to build.
- Cons: a typo locks the person out; the takeover stays possible.

### An admin changing someone's email

**Option 1: switch at once, mark it unverified, confirm at the next sign in.**
- Pros: works when the old inbox is gone or the address was mistyped, which is why admins change emails; the sign in step already does the confirming.
- Cons: a careless admin can point an account at the wrong inbox until the next sign in.

**Option 2: keep the old address until the person confirms.**
- Pros: safest against a bad admin.
- Cons: needs a public confirm screen, and fails when the person can't sign in with the old email.

### Where the codes live

**Option 1: one `verification_codes` table for every kind, with the old routes moved onto it.**
- Pros: one set of rules (hash, attempts, limits) and one place to audit; closes the guessable reset route in the same change.
- Cons: touches the setup and reset flows that work today.

**Option 2: keep `password_reset_tokens` as is and add a table for email codes.**
- Pros: smaller change.
- Cons: two tables with the same rules to keep in step, and the guessable reset route stays open.

## Rationale

The code wins because of where WeLinc's people sign in: a third of them on native mobile apps, and every one of them in a flow that is waiting on the same screen. A link's one advantage, a tap instead of six digits, matters for public sign ups where every lost click loses a customer. It doesn't matter for staff who do this about once. A link can still be added later without changing anything the code flow builds. (basis: OWASP Forgot Password Cheat Sheet on single use, short lived tokens)

Blocking at sign in follows from having no public sign up. Every unverified person is someone an admin just created or just re-pointed, so the step costs each of them one email once. A grace period would mean building a deadline state for nobody. The ticket follows the contract's reserved OTP shape, so the code alone is never enough and feature 34 gets the step for free. The step runs after the system check, so a person with no access is never mailed a code. (basis: contract 0001 section 8, the reserved `OTP_REQUIRED` shape)

For limits there is no single standard, so the numbers follow the references that agree: NIST's ten minute ceiling for out of band secrets and its call for rate limiting, Auth0's and Supabase's single live code and 60 second resend, and OWASP's warning against account lockouts. Codes die after 5 wrong tries rather than locking the account, which allows a typo or two and still caps a guesser at 25 tries an hour. Folding the old setup and reset codes into the same service was chosen because the unlimited reset route is a worse hole than the one this row was opened for. Leaving it open in a GA epic about auth isn't defensible. (basis: NIST SP 800-63B, Auth0 email OTP docs, Supabase passwordless docs, OWASP Forgot Password Cheat Sheet)

Removing typed passwords (on create and on edit) finishes the rule that an admin never knows a password, which is how workplace invites work. Completing setup is itself the email proof, so the common case of a new account needs no new flow at all. `password_set` exists only so admins can tell "never finished setup" from "email not verified": after an admin email change, the person has a password, and calling them Setup pending would be wrong.

The own change and admin change differ on purpose. Your own change has a working old inbox and a signed in session, so the safe pending model costs nothing. An admin change exists for the case where that inbox is gone, so it must switch at once, and the sign in step confirms it.

## References

**Project sources**:
- `welinc-auth/src/auth/auth.service.ts` (`createUser`, `updateUser`, `forgotPassword`, `verifyOtp`, `otpResetPassword`, `updateOwnProfile`, `changeOwnPassword`), `welinc-auth/prisma/schema.prisma`
- `welinc-auth/AGENTS.md` (sessions, `PortalCsrfGuard`, scope rules, the throttler storage pattern)
- Contract [0001](../0001-shared-services-contract/index.md) sections 8, 10 to 12; specs [0003](../0003-sessions-refresh-logout/index.md), [0006](../0006-suite-seed-accounts/index.md), [0007](../0007-app-initiated-login-launcher/index.md), [0008](../0008-suite-gateway/index.md)
- `welinc-web-vrms/src/features/user-management/lib/accountStatus.ts`, `welinc-web-portal/src/pages/auth/Login.tsx`

**Practices & standards**:
- Single use, short lived, securely stored reset tokens, with no account lockout (OWASP Forgot Password Cheat Sheet)
- Out of band secrets valid for at most 10 minutes, with rate limited attempts (NIST SP 800-63B, as read by a vendor; the NIST text itself was not opened)
- One live code at a time, a resend wait (Auth0 email OTP, Supabase passwordless email)

**Links** (found during the design conversation on 2026-11-10):
- NIST SP 800-63B-4, authenticators: https://pages.nist.gov/800-63-4/sp800-63b/authenticators
- Bird, how long an OTP should be valid: https://bird.com/explained/verify/how-long-should-an-otp-be-valid-and-how-many-digits.md
- Auth0, email OTP: https://auth0.com/docs/authenticate/passwordless/authentication-methods/email-otp
- Supabase, passwordless email: https://supabase.com/docs/guides/auth/auth-email-passwordless
- OWASP Forgot Password Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html
