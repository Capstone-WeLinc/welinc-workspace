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

# Verify: slice 2, system admins in the portal · spec 0013 · updated 2026-11-12
_Steps for build plan tasks 8 to 11. Sign in as `vrms.admin@` (VRMS Admin) or `multi.admin@` (VRMS and VMMS Admin) and pass the code first. Local SMTP sends real mail: use `ADMIN_SIGN_IN_CODE=false` or blank `SMTP_*` (code read from the log) before any signed in step._

## UI / manual
- [ ] Portal `/admin/people` as `vrms.admin@`: VRMS people only, each row with role and status badges, Load more after 50 → AC-16, AC-23
- [ ] Type a name in the search: the list narrows after a moment and `?q=` is in the address; pick Locked: only locked people, `?status=LOCKED` → AC-23
- [ ] As `multi.admin@`: a VRMS and VMMS switcher shows; VMMS lists VMMS people only → AC-23
- [ ] Open `/admin/people?system=BMS` as `vrms.admin@` → "You aren't an admin of BMS", no list → AC-16
- [ ] Open `/admin/people/<id>?system=VRMS` for a VRMS mechanic: details, signed in devices, recent activity → AC-23
- [ ] The same link for a BMS only person → "This person isn't in VRMS" → AC-16
- [ ] `/admin/people/new?system=VRMS`: add a new address with Mechanic → the person page opens, a setup code goes out → AC-16, AC-23
- [ ] Add again with an email that already has a VMMS account → "already has a WeLinc account" with Add the VRMS role; it attaches without touching their name or password → AC-16
- [ ] Add a person with the Admin role → the password dialog opens before the save; Cancel leaves nothing created; the right password creates them → AC-14a
- [ ] Wrong password in that dialog → "That password is not right. N tries left"; 5 wrong ones lock your own account → AC-14
- [ ] Edit a mechanic's name → saved with no password asked → AC-16
- [ ] Edit a mechanic's role to Admin → password asked once, then saved; VRMS admins get an alert email → AC-14a, AC-13
- [ ] On another VRMS admin's page: Send reset code, Unlock (lock them first), End all sessions, an email edit → each asks your password and sends an alert email to the VRMS admins → AC-14b, AC-13
- [ ] The same actions on a mechanic → no password asked, no alert → AC-14b
- [ ] Your own page: no Deactivate, Delete or End all sessions in the menu; the email edit is locked with "Change your own email from your profile" → AC-16
- [ ] Deactivate the last active VRMS Admin from another admin's account (deactivate the others first) → the server's last admin message shows → AC-16
- [ ] Delete a VRMS only mechanic → back on People, they are gone; Deletion requests, Deleted, can restore lists them; Restore brings them back inactive → AC-16, AC-23
- [ ] Delete a person shared with VMMS → the shared account message; nothing changes → AC-16
- [ ] Deletion requests: a pending request from VRMS My profile shows; Reject needs a 5 to 500 character note; Approve deletes and drops the row → AC-16, AC-23
- [ ] Activity: VRMS events newest first with the person's name linking to their page; Load more works → AC-16, AC-23
- [ ] A step up owed partway (flag on, a session from before): any People call opens Confirm it's you, then the call runs again → AC-22
- [ ] VRMS `/users` as the VRMS Admin: no Edit, reset, unlock, sessions, activity, deactivate or Deletion requests chip; each row's menu has Manage account (portal, new tab, `?system=VRMS`) and Open tickets for mechanics → AC-31
- [ ] VRMS Add user opens the portal's `/admin/people/new?system=VRMS` in a new tab; after adding, back in the VRMS tab the list refreshes → AC-31
- [ ] Click a mechanic row → their open tickets with Unassign and Reassign still work; the Work column updates → AC-31
- [ ] Chief Mechanic dashboard Team section still opens a mechanic's open tickets → AC-31 (shared component kept)
- [ ] Settings, permissions: give Chief Mechanic `team.manage` → the Users item shows for them (the list itself still needs a VRMS Admin, see the scope note) → AC-31
- [ ] With `ADMIN_SIGN_IN_CODE=true` and a VRMS session that never passed the code, open VRMS Users → toast "Confirm your sign in in the portal" with Open the portal; after the portal step up, Retry loads the list → AC-31, AC-6

## Commands
- [ ] `curl -s http://localhost:3000/auth/admin/users?system=VRMS` with no cookie → 401 `NOT_SIGNED_IN` → AC-14
- [ ] With an admin cookie, `PATCH /auth/admin/users/<id>/unlock` without the portal `Origin` → 403 `CSRF_REJECTED`; with it → 200 → AC-14
- [ ] With an admin cookie, `GET /auth/admin/users?system=VMMS` as `vrms.admin@` → 403 `NOT_ADMIN_OF_SYSTEM` → AC-16
- [ ] Bearer `PATCH /auth/users/<id>` giving VRMS Admin with no `reauthToken` → 403 `REAUTH_REQUIRED`; with a token from `POST /auth/profile/verify-password` purpose `ADMIN_ACTION` → 200; the same token again → 403 `REAUTH_REQUIRED` → AC-14a, AC-18
- [ ] Bearer `POST /auth/profile/verify-password` purpose `ADMIN_ACTION` as a mechanic → 403 `NOT_AN_ADMIN`, no try counted → AC-14a
- [ ] `POST /auth/admin/verify-password` purpose `TEMPORARY_ACCESS` as a VRMS admin → 403 `NOT_SUITE_ADMIN` → AC-14
- [ ] Bearer `DELETE /auth/users/<admin id>/sessions` with no body → 403 `REAUTH_REQUIRED`; on a mechanic → 200 `{ ended }` → AC-14b, AC-18
- [ ] Bearer `POST /auth/forgot-password` with an admin token for another admin's email and no `reauthToken` → 403 `REAUTH_REQUIRED`; anonymous → the usual 200 message → AC-14b
- [ ] In `welinc_vrms_db`: `select role, allowed from role_permissions where permission='team.manage'` → ADMIN true, the others false → AC-31
- [ ] `npm test` in welinc-auth (in the container), backend-vrms, the portal (from a `C:/` path on Windows) and web-vrms → all pass → AC-16, AC-18

## Value sourcing
- [ ] The system an admin acts in is the `system` input checked against their admin roles: as `multi.admin@`, the same person under `?system=VRMS` and `?system=VMMS` shows that system's roles only → Value sourcing "which system the admin acts in"
- [ ] The caller of a cookie route: in a second browser signed in as `vrms.admin2@`, the People list and the actor name in Activity are theirs → Value sourcing "any cookie route, the caller"
- [ ] Alert recipients are the suite admins plus the active admins of the system concerned: give VRMS Admin to someone; `suite.admin@` and every active VRMS admin get one email each, a deactivated VRMS admin and the VMMS admins get none → Value sourcing "alert email, recipients"
- [ ] Alert time is Asia/Manila: the email's When line matches the Manila clock, not UTC → Value sourcing "alert email, time"
- [ ] Alert link uses `PORTAL_URL`: it opens `<PORTAL_URL>/admin/people/<id>?system=VRMS` → Value sourcing "alert email, VRMS links"

## Acceptance-criteria coverage
- AC-13 (slice 2 rows: admin role added or removed on create, attach, edit, delete, approve, restore; actions on an admin account): the alert steps. The suite admin, temporary access and matrix rows come with slices 3 and 5
- AC-14: the verify password, CSRF and no cookie steps
- AC-14a: the Add and Edit admin role steps, the bearer reauth steps
- AC-14b: the actions on another admin, the bearer sessions and forgot password steps
- AC-16: People, person page, Add, scope, self and last admin steps
- AC-18: the bearer route steps
- AC-23: the People, person, Deletion requests and Activity views
- AC-31: the VRMS Users page, Add user, open tickets, `team.manage` and the ADMIN_CODE_REQUIRED toast

# Verify: slice 3, suite admin powers · spec 0013 · updated 2026-11-13
_Steps for build plan tasks 12 to 17. Every add, remove, grant and early end sends alert emails, and local SMTP is real: blank `SMTP_*` (read mails from the auth log) before those steps. Sign in as `suite.admin@` (`admin1234`) and pass the code._

## UI / manual
- [ ] `/admin` as the suite admin → Overview: admins per system (name, since, granted by), live temporary access under its system, Needs attention (only groups with a count), Recent admin changes → AC-19, AC-23
- [ ] Suite admins → the list with who added each and why; Add suite admin searches only active accounts with no role; reason under 10 characters is refused in the dialog; a wrong password says the tries left → AC-1, AC-24
- [ ] Add a second suite admin (a fresh account with no role), then remove them → both emails in the log reach every admin, the removed person included; Remove is hidden on your own row → AC-1, AC-2, AC-13
- [ ] Temporary access → the dialog: system, role (changes with the system), hours 1 to 8 with 4 picked, reason with a counter, password; start VRMS Admin for 2 hours → banner "You have temporary VRMS Admin access until …" with Open VRMS and End now; VRMS admins get the email → AC-9, AC-13, AC-24
- [ ] Open VRMS from the banner → you are in VRMS as Admin → AC-9
- [ ] End now → it warns that it signs you out everywhere; confirm → back to the login screen; VRMS admins get "ended early" → AC-10, AC-24
- [ ] People → "All people" first (people with no role included, every system's roles shown with the system name, a Suite admin badge); pick VRMS → Add person shows → AC-17, AC-23
- [ ] A person page as the suite admin → the system switcher; a person not in that system says "Pick another system above" → AC-23
- [ ] As `vrms.admin@` while the suite admin holds a live grant: People shows them with "Temporary until …"; editing that role → "End the grant instead"; Temporary access lists the grant with End now → AC-11
- [ ] Activity → "Suite wide" tab lists everyone's events, former members included → AC-20
- [ ] Deletion requests → "All systems": orphans first with "No admin left" → AC-21
- [ ] Overview, Temporary access, People and Suite admins at 375px: no sideways scroll, the dialog scrolls inside the screen → AC-23

## Commands
- [ ] `POST /auth/admin/suite-admins` without a reauth token → 403 `REAUTH_REQUIRED`; for someone holding a role → 409 `HOLDS_SYSTEM_ROLES`; for `state.unverified@` → 409 `NOT_ELIGIBLE`; a fourth → 409 `SUITE_ADMIN_LIMIT` → AC-1
- [ ] Two adds of a third and fourth suite admin at once (two shells, same moment) → one wins, the other gets `SUITE_ADMIN_LIMIT` → AC-1
- [ ] `POST /auth/admin/suite-admins/<own id>/remove` → 409 `SELF_ROLE` → AC-2
- [ ] `insert into user_roles (… user_id = 9001, temporary_grant_id null …)` in psql → `suite_admin_no_roles` at commit → AC-3
- [ ] As `vrms.admin@`, `PATCH /auth/admin/users/<9001>/status` with `isActive: false` (while 9001 holds a VRMS grant) → 409 `IS_SUITE_ADMIN`; same for `DELETE` → AC-3
- [ ] As the suite admin, `POST /auth/profile/deletion-request` → 409 `IS_SUITE_ADMIN` and the reauth token stays unused → AC-3
- [ ] `POST /auth/admin/temporary-grants` with `hours: 9` → 400 `VALIDATION_FAILED`; a second VRMS grant while one is live → 409 `GRANT_ACTIVE`; as `vrms.admin@` → 403 `NOT_SUITE_ADMIN` → AC-9
- [ ] A grant inserted with `expires_at` a minute away → within about two minutes `end_reason = EXPIRED`, no actor, its `user_roles` row gone, `TEMP_ACCESS_ENDED` written, the directory feed's latest roles for 9001 empty → AC-10
- [ ] With `expires_at` in the past but before the sweep runs, a VRMS refresh for that session answers without the role → AC-10 lazy expiry
- [ ] `GET /auth/admin/report` as `vrms.admin@` → 403 `NOT_SUITE_ADMIN`; `GET /auth/admin/temporary-grants?system=BMS` as `vrms.admin@` → 403 `NOT_ADMIN_OF_SYSTEM` → AC-11, AC-19
- [ ] `GET /auth/admin/users`, `/activity` and `/deletion-requests` with no `system` as the suite admin → 200 suite wide; as `vrms.admin@` → 400 → AC-17, AC-20, AC-21
- [ ] A suite admin `PATCH /auth/admin/users/:id` giving any VRMS role → 403 `REAUTH_REQUIRED` without a token; with one → VRMS admins get "given the … role by a suite admin" → AC-14c

## Value sourcing
- [ ] Report `since`: change a VRMS admin's name (not their role) → `since` stays; remove and give the admin role again → `since` is the new time → Value sourcing "report, admins, since"
- [ ] Report `grantedBy`: give `vrms.chief@` the VRMS Admin role from the portal → Overview shows you as granted by; a seed admin shows none → Value sourcing "report, admins, grantedBy"
- [ ] Grant `expiresAt`: start with 3 hours → `expires_at - started_at` is exactly 3 hours → Value sourcing "temporary grant, expiresAt"
- [ ] `temporaryUntil` on user lists equals the grant's `expires_at` → Value sourcing "user lists, temporaryUntil"
- [ ] `orphan`: a VRMS only person asks for deletion while VRMS has other admins → not orphan; deactivate every other VRMS admin in a test copy → orphan → Value sourcing "deletion lists, orphan"
- [ ] Alert recipients: a VRMS grant reaches suite admins and VRMS admins only, not VMMS or BMS admins → Value sourcing "alert email, recipients"

## Acceptance-criteria coverage
- AC-1, AC-2, AC-4: the Suite admins steps and the suite admin commands
- AC-3: the trigger, `IS_SUITE_ADMIN` and deletion request commands
- AC-9 to AC-11: the Temporary access steps, expiry and lazy expiry commands, the VRMS admin view
- AC-13, AC-14c: the alert checks in the log
- AC-17, AC-20, AC-21: All people, Suite wide activity, All systems deletion requests
- AC-19, AC-23, AC-24: Overview, the views, the banner, 375px
- Not built yet: the VRMS roster skip (AC-11 last part, waiting on the directory shape), AC-32, slices 5 and 6
