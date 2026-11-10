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
