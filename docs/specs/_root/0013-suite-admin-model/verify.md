# Verify: suite admin model · spec 0013 · updated 2026-11-12
_Steps derived from spec 0013 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Slice 1 only so far (admin identity and the sign in code). Later slices append their steps here.

Before you start: seed admin addresses get no mail. Set `ADMIN_SIGN_IN_CODE=false` in welinc-auth's `.env` only for the AC-8 steps; for the others leave `SMTP_*` blank and read the code from the auth log (`docker logs welinc_auth_service`). Curl calls need `Origin: http://localhost:8000` and `Content-Type: application/json`.

## UI / manual
- [ ] Sign in at `http://localhost:8000` as `vrms.admin@welinc.com` → the "Confirm it's you" code screen, not the launcher; the right code lands on VRMS (one system) → AC-5, AC-22
- [ ] Sign in as `suite.admin@welinc.com` and pass the code → the launcher shows "You hold no role in any system." with Open Admin, and the top bar shows Admin → AC-5, AC-22
- [ ] As the suite admin, open `/admin` → lands on Overview; the sections list Overview, People, Deletion requests, Activity, Temporary access, Suite admins, Permissions → AC-23
- [ ] As `vrms.admin@`, open `/admin` → lands on People; no Overview or Suite admins in the list → AC-23
- [ ] As `multi.chief@` (not an admin) → no Admin entry in the top bar; `/admin` says "Admin is for admin accounts only." → AC-15, AC-22
- [ ] Signed out, open `/admin` → the login form → AC-14
- [ ] An admin session from before this ships (or one made with `ADMIN_SIGN_IN_CODE=false`, then switched back on and restarted): open `/admin` → the step up dialog opens at once; the right code shows the admin shell without a reload of the session → AC-6, AC-7, AC-22
- [ ] In the step up dialog: a wrong code says the tries left; Cancel closes it and keeps the page; "Send a new code" waits out its countdown → AC-7, AC-22
- [ ] The admin shell and the code screen at 375px: no sideways scroll, the sections wrap above the content, buttons at least 44px tall → AC-23

## Commands
- [ ] `POST /auth/login` for `vrms.admin@` → 200 `{ status: "SIGN_IN_CODE_REQUIRED", challengeId, email, resendAfter }` and no `Set-Cookie` → AC-5
- [ ] `POST /auth/login` for `state.unverified@` → `EMAIL_VERIFICATION_REQUIRED` (one code only) → AC-5
- [ ] `POST /auth/login/verify-email` with that ticket and code → 200 launcher body; `select sign_in_code_at from sessions order by created_at desc limit 1` is set, and an `ADMIN_CODE_PASSED` event exists for the admin → AC-5, AC-7
- [ ] Same for a non admin through the code step (`state.unverified@` after verifying) → `sign_in_code_at` set, no `ADMIN_CODE_PASSED` → AC-5
- [ ] A plain password login for `multi.chief@` → `sign_in_code_at` stays null → AC-5
- [ ] `POST /auth/login` for `suite.admin@`, then the code → 200 with `"systems": []`, never 403 `NO_SYSTEM_ACCESS`; `GET /auth/sso` with that cookie answers the same → AC-5
- [ ] With a VRMS admin bearer token whose session has `sign_in_code_at` null, `GET /auth/users` → 403 `ADMIN_CODE_REQUIRED`; after `POST /auth/admin/code` and `/code/verify` on the same cookie session, the same token → 200 → AC-6, AC-7
- [ ] `POST /auth/admin/code` on a session that passed already → 200 `{ "passed": true }`, no mail in the log → AC-7
- [ ] `POST /auth/admin/code/verify` with a ticket issued to another account → 400 `CODE_EXPIRED` → AC-7
- [ ] `GET /auth/admin/me` without a cookie → 401 `NOT_SIGNED_IN`; as `multi.chief@` → 200 with `suiteAdmin: false`, `adminOf: []`; `POST /auth/admin/code` as `multi.chief@` → 403 `NOT_AN_ADMIN` → AC-14, AC-15
- [ ] `POST /auth/admin/code` without the portal `Origin` → 403 `CSRF_REJECTED` → AC-14
- [ ] `ADMIN_SIGN_IN_CODE=false`, restart welinc-auth: an admin login answers the launcher body, `me` shows `codeRequired: false`, `POST /auth/admin/code` → 409 `CODE_NOT_REQUIRED`, no `ADMIN_CODE_PASSED` written → AC-8
- [ ] `NODE_ENV=production ADMIN_SIGN_IN_CODE=false npm run env:check` (after a build) → exits 1 naming `ADMIN_SIGN_IN_CODE` → AC-8
- [ ] `docker exec welinc_auth_service npm run admin:recover -- --email vrms.admin@welinc.com --reason "Checking the refusal path"` → "Refused, nothing was written", exit 1 → AC-12
- [ ] Same with `--reason "short"` → refused for the reason length → AC-12
- [ ] Same for `state.unverified@`, `state.deactivated@` and an unknown address → each refused, nothing written → AC-12
- [ ] Lock `suite.admin@` (5 wrong passwords), then `admin:recover -- --email suite.admin@welinc.com --reason "Lost access during testing"` → unlocked, its live sessions end with `ADMIN_ENDED`, an `ADMIN_RECOVERY` row holds the reason plus `host` and `osUser` → AC-12
- [ ] `npm run seed` twice → one `suite_admins` row for id 9001 with `granted_by_id` and `reason` null, no `user_roles` rows for it → AC-33
- [ ] `npm --prefix welinc-auth run seed:check -- welinc-backend-vrms/prisma/seeds/people.json` → "Matches people.json" → AC-33

## Value sourcing
- [ ] Whether login asks the code: make a person admin in a second system only (for example `multi.admin@`), confirm the code is asked; a chief in two systems is never asked → Value sourcing "login, whether to ask the code"
- [ ] Code passed: end the cookie session, sign in again with the code; the new session's `sign_in_code_at` is set while the old one stays as it was (never cleared) → Value sourcing "admin gate, code passed"
- [ ] The caller of a cookie route: two browsers signed in as different admins each get their own `me` → Value sourcing "any cookie route, the caller"

## Acceptance-criteria coverage
- AC-5: login steps, launcher for the suite admin, the UI sign in steps
- AC-6: the bearer gate step, the old session step up in the UI
- AC-7: the step up commands, the dialog steps
- AC-8: the flag off steps and the production `env:check`
- AC-12: the four recovery script steps
- AC-14, AC-15: no cookie, CSRF, not an admin, the `me` answers
- AC-22, AC-23: the portal UI steps
- AC-33: the seed and `seed:check` steps
- Later slices (AC-1 to AC-4, AC-9 to AC-11, AC-13, AC-14a to AC-14c, AC-16 to AC-21, AC-24 to AC-32, AC-34): not built yet, steps come with them
