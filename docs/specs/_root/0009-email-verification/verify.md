# 0009. Email verification: verify

Steps for `/check verify email verification`. Run them on the local stack.

**Mail:** local welinc-auth sends real email when `SMTP_*` is set. For this run, blank `SMTP_HOST`, `SMTP_USER` and `SMTP_PASS` in `welinc-auth/.env` and restart `welinc_auth_service` (then the gateway). MailService then writes each email to the container log, and you read codes with `docker logs welinc_auth_service`. Put the values back afterwards. Never set real addresses on test accounts.

**Mail failure:** to check `MAIL_FAILED`, point `SMTP_HOST` at an address that refuses connections (for example `127.0.0.1`, port 1) instead of leaving it blank.

## Automated

1. In welinc-auth: `npm run test` (the code service rules, AC-1 to AC-6, AC-13 to AC-21) and `docker exec welinc_auth_service npm run test:db` (the migration backfill and the parallel attempts case, AC-4, AC-16).
2. In welinc-web-portal and welinc-web-vrms: `npm run test`, `npm run typecheck`, `npm run lint`, `npm run build`.

## Manual, on the real stack

### Sign in step (portal)

1. Run `npm run seed` in the auth container. Sign in at `http://localhost:8000` as `state.unverified@welinc.com` / `mechanic1234`. The card shows "Check your email" with the address; focus is in the code field. No `welinc_sso` cookie is set yet. **AC-7**, **AC-26**
2. Sign in again within a minute: a new step, no new email in the log, the countdown shows the time left. The first ticket no longer works (retry it with curl). **AC-8**
3. Type a wrong code: "That code isn't right. 4 tries left." Paste the right code from the log: it fills all six boxes, submits, and lands in VRMS or the launcher. **AC-9**, **AC-25**, **AC-26**
4. Sign out and in again: no code step. **AC-7**
5. Reset with `npm run seed`, sign in, enter 5 wrong codes, then the right one: "That code expired. Sign in again to get a new one." **AC-4**
6. Resend twice inside a minute: the second answers "Too many codes sent". **AC-10**
7. With the refusing `SMTP_HOST`: sign in as `state.unverified@`: "We couldn't send your code." No row in `verification_codes`. **AC-5**, **AC-8**
8. At 375px and by keyboard only: the code step fits with no sideways scroll, Tab reaches Verify, Resend and "Use a different account", focus rings show. **AC-26**
9. Open a VRMS deep link while signed out, sign in as `state.unverified@`, finish the code: you land on the deep link. **AC-25**

### Limits

10. Send 11 `POST /auth/verify-otp` calls in a minute from one address: the 11th answers 429 with `Retry-After`. Repeat for `/auth/login/verify-email`. **AC-6**
11. Send two wrong codes in parallel (two curl calls started together): `attempts` is 2 in `verification_codes`. **AC-4**
12. `select code_hash from verification_codes`: no plain digits. `docker logs welinc_auth_service`: no ticket and no code outside the logged email body. **AC-1**

### Setup and reset

13. As `vrms.admin@`, add a user on the Users page with a throwaway address on a test domain: Setup pending. Read the setup code from the log and set a password at the portal's forgot password page: the user turns Active. **AC-12**, **AC-15**, **AC-29**
14. As that admin, press Send setup code twice within a minute: the second shows the wait. **AC-13**
15. curl `POST /auth/users` with a `password` field (400), `PATCH /auth/users/:id` with `password` (400), `PATCH /auth/users/:id/password` (404). **AC-15**
16. Forgot password from the portal for a verified account: the reset still works with the unchanged page. **AC-14**

### Email changes

17. Signed in to VRMS as a test user, My profile: Change email with a wrong password (error on the password field), the same address (error), an address another account holds (error). **AC-17**, **AC-27**
18. Change to a new test address: the log shows a code to the new address and a "change started" notice to the old one. The profile shows "Waiting for you to confirm". Reload: still pending. After a minute, start again with the same address: a new code, no second notice. Cancel: gone. Start again, type the code: the email changes, the log shows the "changed" notice to the old address. **AC-17** to **AC-19**, **AC-24**, **AC-27**
19. `GET /auth/directory/changes` (VRMS client token): one change for that person, at confirm time. **AC-23**
20. curl `PATCH /auth/profile` with `email`: 400. **AC-20**
21. As `vrms.admin@`, edit a verified user's email on the Users page: the helper text shows, the user turns Email not verified, the old address gets a notice. Signed in as that user, My profile says "Not verified yet". Sign out and in: the code step comes. **AC-21**, **AC-28**, **AC-29**
22. curl `PATCH /auth/users/<your own id>` with a new email as `vrms.admin@`: 409 `SELF_EMAIL`. Change another user's email to one differing only in letter case: nothing changes. **AC-21**
23. As the admin, edit the email of a Setup pending user: a new setup code goes to the new address, and the old code fails. **AC-2**, **AC-21**
24. On an Email not verified row, the code action reads Send reset code with the explaining text. Reactivate on that user says they can sign in with their current password. **AC-29**

### Mobile (by API)

25. `POST /auth/mobile/login` for `state.unverified@` with `clientId: "vmms-mobile"`: the step body. `POST /auth/mobile/login/verify-email` with the code: the token body. **AC-11**

### Docs

26. Contract 0001 sections 8, 10, 11 and 12 and `docs/integration/seed-accounts.md` carry the changes. **AC-31**

## Added by /develop (2026-11-11)

_Extra steps from the build, one or more per acceptance criterion plus the Value sourcing rows. They overlap the steps above on purpose; skip a step the list above already ran._

**Before you start:** local welinc-auth sends real mail. Run it with mail off so codes print in its log, using a compose override that sets `SMTP_HOST`, `SMTP_USER` and `SMTP_PASS` to `""` on `auth-service` (`docker compose -f docker-compose.shared.yml -f <override> up -d --no-deps auth-service`, then restart `welinc_api_gateway`). Read a code with `docker logs welinc_auth_service 2>&1 | grep -A2 "<email phrase>"`. Run `npm run seed` in the auth container after each pass (it puts `state.unverified@` back). Put the container back on its normal settings when done.

### UI / manual
- [x] Portal, `state.unverified@` / `mechanic1234` → the card says "Check your email", "We sent a 6 digit code to state.unverified@welinc.com", focus is in the code field, Verify disabled, "Resend code in 60 s" → AC-7, AC-25, AC-26
- [x] Type a wrong code → "That code isn't right. 4 tries left." as an alert, boxes cleared, focus back in the field → AC-4, AC-25, AC-26
- [x] Type the right code → submits on the 6th digit and lands on the launcher (two systems); signing in again goes straight in → AC-9, AC-25
- [x] Open the portal with `?request=` from VRMS (an app initiated login) as `state.unverified@` → after the code, you land back in VRMS, not the launcher → AC-25
- [x] Paste 6 digits into the field → every box fills and it submits → AC-26
- [x] At 375px the step fits, the six boxes are 44px, focus rings show (the page's existing hero overflow of 18px is separate) → AC-26
- [x] Use a different account → back to the password step; the URL and sessionStorage hold no ticket → AC-25
- [x] Wait out a code (or force `expires_at` into the past) and verify → back to the password step with "That code expired. Sign in again to get a new one." → AC-25
- [x] VRMS My profile while unverified → "Not verified yet. You'll confirm it the next time you sign in." → AC-28
- [x] My profile → Change email with a wrong password → "That password isn't right." under the password field → AC-17, AC-27
- [x] Change email to your own address, to `vrms.admin@welinc.com`, and to a domain that can't receive mail (`x@nodomain.invalid`) → each message under the new email field → AC-17, AC-27
- [x] Change email properly → code step; close it → profile shows "Waiting for you to confirm …" with Enter code and Cancel; your email is unchanged → AC-17, AC-27
- [x] Enter code → the profile, the account summary and the shell show the new email, the toast confirms it, the session stays → AC-18, AC-27
- [ ] Start a change, then Cancel on the profile → the pending notice goes; `/auth/me` answers `pendingEmail: null` → AC-19, AC-27
- [x] Users page as `vrms.admin@`: a user with `password_set` false reads Setup pending, one with a password and `email_verified` false reads Email not verified; sort Locked, Setup pending, Email not verified, Active, Inactive (Inactive last by decision) → AC-29
- [x] Email not verified row → Send reset code says "Using it sets a new password and confirms their email. They'll also get a code when they next sign in." → AC-29
- [x] Edit a user and type a new email → the field says "They'll confirm the new address at their next sign in, and we'll tell the old one."; editing yourself, the email is read only with "Change your own email from My profile." → AC-21, AC-29
- [x] Reactivate a Setup pending user → the dialog reads "They still need to set a password…" → AC-29

### Commands
- [x] `POST /auth/login` (Origin `http://localhost:8000`) for `state.unverified@` → 200 `EMAIL_VERIFICATION_REQUIRED`, `Cache-Control: no-store`, no `Set-Cookie` → AC-7
- [x] The same login again inside 60 s → a new `challengeId`, no new email; the old ticket with the right code → 400 `CODE_EXPIRED` → AC-8
- [ ] A user with no system and an unverified email → 403 `NO_SYSTEM_ACCESS`, no code in the log → AC-7
- [x] `/auth/login/verify-email/resend` inside the wait → 429 `CODE_SEND_LIMIT` with `Retry-After`; after 60 s → 200 `{ resendAfter: 60 }` and the same ticket works → AC-5, AC-10
- [x] 11 calls a minute to `/auth/login/verify-email` from one address → the 11th is 429 `RATE_LIMITED` with `Retry-After`; same for `/auth/verify-otp` (`code-public`) → AC-6
- [x] `verify-email` with a 5 digit code → plain 400, `attempts` unchanged in `verification_codes` → AC-4
- [x] Mobile: `POST /auth/mobile/login` (`vmms-mobile`) for `state.unverified@` → the step body; wrong code → `INVALID_CODE`; right code → the token body; an `APP_NOT_ALLOWED` account gets 403 before any code → AC-11
- [x] `/auth/forgot-password` public, twice inside 60 s → the same generic message both times, one email; with an admin token the second answers 429 `CODE_SEND_LIMIT` → AC-5, AC-13
- [x] `/auth/verify-otp` 5 wrong times, then the right code → "Invalid or expired OTP" every time → AC-4, AC-14
- [x] `/auth/reset-password` with a right code → `email_verified` and `password_set` true, sessions ended, lock cleared → AC-12
- [x] `PATCH /auth/users/:id/password` → 404; `POST /auth/users` with `password` → 400; `PATCH /auth/profile` with `email` → 400 → AC-15, AC-20
- [x] `POST /auth/users` (no password) → `setupEmailSent: true`, the row has `password_set` and `email_verified` false; pressing Send reset code within 60 s → 429 → AC-5, AC-15
- [x] Admin changes a Setup pending user's email → old address gets "An admin changed your email", a setup code goes to the new one, the old code no longer works, `setupEmailSent: true` → AC-2, AC-21, AC-24
- [x] Admin changes their own email on `PATCH /auth/users/:id` → 409 `SELF_EMAIL`; to a taken address → 409 `EMAIL_TAKEN` → AC-21
- [x] Own email change start → `{ pendingEmail, expiresAt, resendAfter }`; old address gets "An email change was started"; `directory_changes` has no new row until the code is used, then exactly one → AC-17, AC-23, AC-24
- [x] `GET /auth/me` → `passwordSet`, `pendingEmail`; `GET /auth/users` rows carry `passwordSet` → AC-20, AC-22
- [x] `SELECT code_hash FROM verification_codes` → argon2 hashes only; `password_reset_tokens` doesn't exist; no log line outside the dev mail fallback holds an address or a code → AC-1
- [x] Set a code's `created_at` to 25 hours ago and run the sweep → the row is gone → AC-1
- [x] `docker exec welinc_auth_service npm run test:db` → the migration and code service specs pass → AC-1 to AC-5, AC-16
- [x] `npm run seed` → every seed person has `password_set` true and `state.unverified@` keeps `email_verified` false → AC-16
- [x] Contract 0001 reads version 4 with sections 8, 10, 11, 12 and 14 amended; `docs/integration/seed-accounts.md` says `state.unverified@` meets the code step → AC-31

### Value sourcing
- [x] `challengeId` is 43 base64url characters and only its SHA-256 is in `challenge_hash` → Value sourcing (ticket)
- [x] `resendAfter` counts down from the family's newest send: start, wait 20 s, sign in again → `resendAfter` about 40 → Value sourcing (resendAfter)
- [x] After 5 sends in an hour, `Retry-After` is when the oldest of the last 5 turns an hour old, not 60 → Value sourcing (Retry-After)
- [x] `attemptsLeft` is 5 minus the tries: 4, 3, 2, 1, then `CODE_EXPIRED` → Value sourcing (attemptsLeft)
- [x] A setup code email says "1 hour", the others "10 minutes" → Value sourcing (lifetime text)
- [x] The notice to the old address names the address from before the update, not the new one as "old" → Value sourcing (old address)
- [x] `forgot-password` for a user with `password_set` false sends setup wording, else reset wording → Value sourcing (setup or reset)
- [x] Make the mail fail on a resend (stop SMTP mid run) → 503 `MAIL_FAILED`, the earlier code still works, and the next send is allowed at once → Value sourcing (restore row)

### Acceptance-criteria coverage
- AC-1 command steps (hashes, sweep, logs) · AC-2 admin change step · AC-3 lifetime text · AC-4 wrong code UI and command steps · AC-5 limits steps · AC-6 address limit step · AC-7 login steps · AC-8 second login step · AC-9 portal right code · AC-10 resend step · AC-11 mobile step · AC-12 reset step · AC-13 forgot steps · AC-14 verify-otp step · AC-15 admin password steps · AC-16 seed and test:db steps · AC-17 to AC-20 profile steps · AC-21 admin email steps · AC-22 `/auth/users` step · AC-23 directory step · AC-24 notice steps · AC-25, AC-26 portal UI steps · AC-27, AC-28 My profile steps · AC-29 Users page steps · AC-30 `password` sent nowhere (no field in the web-vrms payload types) · AC-31 docs step

## Added by the amendment (2026-11-19, AC-32)

- [x] `mail.service.spec.ts`: the four cases of AC-32 pass (production with `SEED_MAIL_TO_LOG` on: seed address logged, real address sent; production without it: seed address sent; development: seed address logged) → AC-32 (2026-11-20: 823 tests green)
- [x] Staging: `az containerapp show -n auth-service -g rg-welinc-staging` lists `SEED_MAIL_TO_LOG=true`; production's `auth-service` doesn't have it → AC-32 (2026-11-20: `auth-service-staging` lists it; production is not hosted, VRMS spec 0008 AC-24)
- [ ] Staging portal, `vrms.admin@welinc.com` / `admin1234` → the code step appears; the code is in `az containerapp logs show -n auth-service -g rg-welinc-staging`, and typing it signs you in → AC-32 (superseded on staging by AC-33: seed mail now goes to the team inbox, not the log)
- [x] `env.spec.ts`: `SEED_MAIL_TO_LOG=1` fails boot; `SEED_MAIL_TO_LOG=true` with `SENTRY_ENVIRONMENT=production` is refused → AC-32 (2026-11-20: 823 tests green)
- [x] Staging: `auth-migrate` and `auth-seed` jobs don't list `SEED_MAIL_TO_LOG` (`az containerapp job show -n auth-seed -g rg-welinc-staging`) → AC-32 (2026-11-20: `auth-migrate-staging` and `auth-seed-staging` don't)

## Added by the amendment (2026-11-20, AC-33)

- [x] `mail.service.spec.ts`: the three AC-33 cases pass (seed address redirected to the tagged address and not logged; real address sent as is; `+` and uppercase in the local part normalized; a local part over 40 characters cut; no SMTP falls back to the log) → AC-33 (2026-11-20: 823 tests green)
- [x] `env.spec.ts`: a template without `{tag}`, with two, or with `{tag}` after the `@` fails boot; set with `SENTRY_ENVIRONMENT=production` is refused → AC-33 (2026-11-20: 823 tests green)
- [x] Staging: `az containerapp show -n auth-service-staging -g rg-welinc-staging` lists `SEED_MAIL_REDIRECT`; `auth-migrate-staging` and `auth-seed-staging` don't → AC-33 (2026-11-20, after `apply.sh staging --domains`)
- [x] Staging portal, `vrms.admin@welinc.com` / `admin1234` → the code arrives in the team Gmail at `+vrms.admin`, from `WeLinc`, in the inbox (not spam); typing it signs you in; the auth log holds no code → AC-33 (2026-11-20: inbox, from WeLinc, signed by welinc.app, signed in; code not in the last 300 log lines)
- [x] A real address on staging (your own Gmail, through a password reset) still gets its own mail, not the team inbox → AC-33 (2026-11-20: a password reset to a personal Gmail landed in that inbox, not the team one)



## Added by the amendment (2026-11-20, AC-34)

- [x] Unit: the AC-34 test's builder table covers every builder in `code-emails.ts`, `admin-alert-emails.ts` and `deletion-emails.ts` (its guard fails on a new one); none adds `<a` or `http` → AC-34
- [x] Unit: `portalHostOf('http://localhost:8000')` is `localhost:8000`; `portalHostOf('https://staging-portal.welinc.app/')` is `staging-portal.welinc.app` → AC-34
- [x] Unit: the setup and reset emails name `{portalHost}` and Forgot password in both parts; the alert names `{portalHost}` and Admin; the deletion email names the Users page → AC-34
- [x] Staging: a setup code to a real Gmail (invite from People) and a reset code to a seed account: no button, the portal host shows as plain text, and if Gmail made it a link, hovering shows `staging-portal.welinc.app`, not `sendibt` → AC-34 (2026-11-20: the reset to `vrms.admin@` checked; setup uses the same builder and sentence, covered by the unit test)
- [ ] Staging: an admin alert (make and undo a test admin change) shows the host as plain text, no `sendibt` link → AC-34
- [ ] Brevo's transactional blocked contacts list holds none of the team inbox addresses → AC-34 (runbook)
