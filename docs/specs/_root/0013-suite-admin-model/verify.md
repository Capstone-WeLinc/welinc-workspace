# Verify: suite admin model · spec 0013 · updated 2026-11-12
_Steps derived from spec 0013 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Slice 1 only so far (admin identity and the sign in code). Later slices append their steps here.

Verify run (2026-11-13): 124 of 141 steps ticked, each with evidence from a live run. Most came from the 2026-11-12 `/check verify` run (commands and UI, in subagents). The five steps that failed on old code (L17, L74, L76, L77, L86) and four partial ones (L68, L72, L73, L82) were run again on 2026-11-13 after the portal fixes (portal `79466c4`, `7476022`), and passed. Unit suites passed (auth 704, backend 1509, portal 73, web-vrms 493). The 17 steps left unticked were not proven by any run: L69, L75, L78, L83, L85, L105, L122, L123, L131, L150, L153, L172, L177, L181, L182, L193, L216.

Before you start: seed admin addresses get no mail. Set `ADMIN_SIGN_IN_CODE=false` in welinc-auth's `.env` only for the AC-8 steps; for the others leave `SMTP_*` blank and read the code from the auth log (`docker logs welinc_auth_service`). Curl calls need `Origin: http://localhost:8000` and `Content-Type: application/json`.

## UI / manual
- [x] Sign in at `http://localhost:8000` as `vrms.admin@welinc.com` → the "Confirm it's you" code screen, not the launcher; the right code lands on VRMS (one system) → AC-5, AC-22
- [x] Sign in as `suite.admin@welinc.com` and pass the code → the launcher shows "You hold no role in any system." with Open Admin, and the top bar shows Admin → AC-5, AC-22
- [x] As the suite admin, open `/admin` → lands on Overview; the sections list Overview, People, Deletion requests, Activity, Temporary access, Suite admins, Permissions → AC-23
- [x] As `vrms.admin@`, open `/admin` → lands on People; no Overview or Suite admins in the list → AC-23
- [x] As `multi.chief@` (not an admin) → no Admin entry in the top bar; `/admin` says "Admin is for admin accounts only." → AC-15, AC-22
- [x] Signed out, open `/admin` → the login form → AC-14
- [x] An admin session from before this ships (or one made with `ADMIN_SIGN_IN_CODE=false`, then switched back on and restarted): open `/admin` → the step up dialog opens at once; the right code shows the admin shell without a reload of the session → AC-6, AC-7, AC-22
- [x] In the step up dialog: a wrong code says the tries left; Cancel closes it and keeps the page; "Send a new code" waits out its countdown → AC-7, AC-22
- [x] The admin shell and the code screen at 375px: no sideways scroll, the sections wrap above the content, buttons at least 44px tall → AC-23

## Commands
- [x] `POST /auth/login` for `vrms.admin@` → 200 `{ status: "SIGN_IN_CODE_REQUIRED", challengeId, email, resendAfter }` and no `Set-Cookie` → AC-5
- [x] `POST /auth/login` for `state.unverified@` → `EMAIL_VERIFICATION_REQUIRED` (one code only) → AC-5
- [x] `POST /auth/login/verify-email` with that ticket and code → 200 launcher body; `select sign_in_code_at from sessions order by created_at desc limit 1` is set, and an `ADMIN_CODE_PASSED` event exists for the admin → AC-5, AC-7
- [x] Same for a non admin through the code step (`state.unverified@` after verifying) → `sign_in_code_at` set, no `ADMIN_CODE_PASSED` → AC-5
- [x] A plain password login for `multi.chief@` → `sign_in_code_at` stays null → AC-5
- [x] `POST /auth/login` for `suite.admin@`, then the code → 200 with `"systems": []`, never 403 `NO_SYSTEM_ACCESS`; `GET /auth/sso` with that cookie answers the same → AC-5
- [x] With a VRMS admin bearer token whose session has `sign_in_code_at` null, `GET /auth/users` → 403 `ADMIN_CODE_REQUIRED`; after `POST /auth/admin/code` and `/code/verify` on the same cookie session, the same token → 200 → AC-6, AC-7
- [x] `POST /auth/admin/code` on a session that passed already → 200 `{ "passed": true }`, no mail in the log → AC-7
- [x] `POST /auth/admin/code/verify` with a ticket issued to another account → 400 `CODE_EXPIRED` → AC-7
- [x] `GET /auth/admin/me` without a cookie → 401 `NOT_SIGNED_IN`; as `multi.chief@` → 200 with `suiteAdmin: false`, `adminOf: []`; `POST /auth/admin/code` as `multi.chief@` → 403 `NOT_AN_ADMIN` → AC-14, AC-15
- [x] `POST /auth/admin/code` without the portal `Origin` → 403 `CSRF_REJECTED` → AC-14
- [x] `ADMIN_SIGN_IN_CODE=false`, restart welinc-auth: an admin login answers the launcher body, `me` shows `codeRequired: false`, `POST /auth/admin/code` → 409 `CODE_NOT_REQUIRED`, no `ADMIN_CODE_PASSED` written → AC-8
- [x] `NODE_ENV=production ADMIN_SIGN_IN_CODE=false npm run env:check` (after a build) → exits 1 naming `ADMIN_SIGN_IN_CODE` → AC-8
- [x] `docker exec welinc_auth_service npm run admin:recover -- --email vrms.admin@welinc.com --reason "Checking the refusal path"` → "Refused, nothing was written", exit 1 → AC-12
- [x] Same with `--reason "short"` → refused for the reason length → AC-12
- [x] Same for `state.unverified@`, `state.deactivated@` and an unknown address → each refused, nothing written → AC-12
- [x] Lock `suite.admin@` (5 wrong passwords), then `admin:recover -- --email suite.admin@welinc.com --reason "Lost access during testing"` → unlocked, its live sessions end with `ADMIN_ENDED`, an `ADMIN_RECOVERY` row holds the reason plus `host` and `osUser` → AC-12
- [x] `npm run seed` twice → one `suite_admins` row for id 9001 with `granted_by_id` and `reason` null, no `user_roles` rows for it → AC-33
- [x] `npm --prefix welinc-auth run seed:check -- welinc-backend-vrms/prisma/seeds/people.json` → "Matches people.json" → AC-33

## Value sourcing
- [x] Whether login asks the code: make a person admin in a second system only (for example `multi.admin@`), confirm the code is asked; a chief in two systems is never asked → Value sourcing "login, whether to ask the code"
- [x] Code passed: end the cookie session, sign in again with the code; the new session's `sign_in_code_at` is set while the old one stays as it was (never cleared) → Value sourcing "admin gate, code passed"
- [x] The caller of a cookie route: two browsers signed in as different admins each get their own `me` → Value sourcing "any cookie route, the caller"

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
- [x] Portal `/admin/people` as `vrms.admin@`: VRMS people only, each row with role and status badges, Load more after 50 → AC-16, AC-23
- [x] Type a name in the search: the list narrows after a moment and `?q=` is in the address; pick Locked: only locked people, `?status=LOCKED` → AC-23
- [x] As `multi.admin@`: a VRMS and VMMS switcher shows; VMMS lists VMMS people only → AC-23
- [x] Open `/admin/people?system=BMS` as `vrms.admin@` → "You aren't an admin of BMS", no list → AC-16
- [x] Open `/admin/people/<id>?system=VRMS` for a VRMS mechanic: details, signed in devices, recent activity → AC-23
- [x] The same link for a BMS only person → "This person isn't in VRMS" → AC-16
- [x] `/admin/people/new?system=VRMS`: add a new address with Mechanic → the person page opens, a setup code goes out → AC-16, AC-23
- [x] Add again with an email that already has a VMMS account → "already has a WeLinc account" with Add the VRMS role; it attaches without touching their name or password → AC-16
- [x] Add a person with the Admin role → the password dialog opens before the save; Cancel leaves nothing created; the right password creates them → AC-14a
- [ ] Wrong password in that dialog → "That password is not right. N tries left"; 5 wrong ones lock your own account → AC-14
- [x] Edit a mechanic's name → saved with no password asked → AC-16
- [x] Edit a mechanic's role to Admin → password asked once, then saved; VRMS admins get an alert email → AC-14a, AC-13
- [x] On another VRMS admin's page: Send reset code, Unlock (lock them first), End all sessions, an email edit → each asks your password and sends an alert email to the VRMS admins → AC-14b, AC-13
- [x] The same actions on a mechanic → no password asked, no alert → AC-14b
- [x] Your own page: no Deactivate, Delete or End all sessions in the menu; the email edit is locked with "Change your own email from your profile" → AC-16
- [ ] Deactivate the last active VRMS Admin from another admin's account (deactivate the others first) → the server's last admin message shows → AC-16
- [x] Delete a VRMS only mechanic → back on People, they are gone; Deletion requests, Deleted, can restore lists them; Restore brings them back inactive → AC-16, AC-23
- [x] Delete a person shared with VMMS → the shared account message; nothing changes → AC-16
- [ ] Deletion requests: a pending request from VRMS My profile shows; Reject needs a 5 to 500 character note; Approve deletes and drops the row → AC-16, AC-23
- [x] Activity: VRMS events newest first with the person's name linking to their page; Load more works → AC-16, AC-23
- [x] A step up owed partway (flag on, a session from before): any People call opens Confirm it's you, then the call runs again → AC-22
- [x] VRMS `/users` as the VRMS Admin: no Edit, reset, unlock, sessions, activity, deactivate or Deletion requests chip; each row's menu has Manage account (portal, new tab, `?system=VRMS`) and Open tickets for mechanics → AC-31
- [x] VRMS Add user opens the portal's `/admin/people/new?system=VRMS` in a new tab; after adding, back in the VRMS tab the list refreshes → AC-31
- [ ] Click a mechanic row → their open tickets with Unassign and Reassign still work; the Work column updates → AC-31
- [x] Chief Mechanic dashboard Team section still opens a mechanic's open tickets → AC-31 (shared component kept)
- [ ] Settings, permissions: give Chief Mechanic `team.manage` → the Users item shows for them (the list itself still needs a VRMS Admin, see the scope note) → AC-31
- [x] With `ADMIN_SIGN_IN_CODE=true` and a VRMS session that never passed the code, open VRMS Users → toast "Confirm your sign in in the portal" with Open the portal; after the portal step up, Retry loads the list → AC-31, AC-6

## Commands
- [x] `curl -s http://localhost:3000/auth/admin/users?system=VRMS` with no cookie → 401 `NOT_SIGNED_IN` → AC-14
- [x] With an admin cookie, `PATCH /auth/admin/users/<id>/unlock` without the portal `Origin` → 403 `CSRF_REJECTED`; with it → 200 → AC-14
- [x] With an admin cookie, `GET /auth/admin/users?system=VMMS` as `vrms.admin@` → 403 `NOT_ADMIN_OF_SYSTEM` → AC-16
- [x] Bearer `PATCH /auth/users/<id>` giving VRMS Admin with no `reauthToken` → 403 `REAUTH_REQUIRED`; with a token from `POST /auth/profile/verify-password` purpose `ADMIN_ACTION` → 200; the same token again → 403 `REAUTH_REQUIRED` → AC-14a, AC-18
- [x] Bearer `POST /auth/profile/verify-password` purpose `ADMIN_ACTION` as a mechanic → 403 `NOT_AN_ADMIN`, no try counted → AC-14a
- [x] `POST /auth/admin/verify-password` purpose `TEMPORARY_ACCESS` as a VRMS admin → 403 `NOT_SUITE_ADMIN` → AC-14
- [x] Bearer `DELETE /auth/users/<admin id>/sessions` with no body → 403 `REAUTH_REQUIRED`; on a mechanic → 200 `{ ended }` → AC-14b, AC-18
- [x] Bearer `POST /auth/forgot-password` with an admin token for another admin's email and no `reauthToken` → 403 `REAUTH_REQUIRED`; anonymous → the usual 200 message → AC-14b
- [x] In `welinc_vrms_db`: `select role, allowed from role_permissions where permission='team.manage'` → ADMIN true, the others false → AC-31
- [x] `npm test` in welinc-auth (in the container), backend-vrms, the portal (from a `C:/` path on Windows) and web-vrms → all pass → AC-16, AC-18

## Value sourcing
- [x] The system an admin acts in is the `system` input checked against their admin roles: as `multi.admin@`, the same person under `?system=VRMS` and `?system=VMMS` shows that system's roles only → Value sourcing "which system the admin acts in"
- [x] The caller of a cookie route: in a second browser signed in as `vrms.admin2@`, the People list and the actor name in Activity are theirs → Value sourcing "any cookie route, the caller"
- [x] Alert recipients are the suite admins plus the active admins of the system concerned: give VRMS Admin to someone; `suite.admin@` and every active VRMS admin get one email each, a deactivated VRMS admin and the VMMS admins get none → Value sourcing "alert email, recipients"
- [x] Alert time is Asia/Manila: the email's When line matches the Manila clock, not UTC → Value sourcing "alert email, time"
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
- [x] `/admin` as the suite admin → Overview: admins per system (name, since, granted by), live temporary access under its system, Needs attention (only groups with a count), Recent admin changes → AC-19, AC-23
- [ ] Suite admins → the list with who added each and why; Add suite admin searches only active accounts with no role; reason under 10 characters is refused in the dialog; a wrong password says the tries left → AC-1, AC-24
- [ ] Add a second suite admin (a fresh account with no role), then remove them → both emails in the log reach every admin, the removed person included; Remove is hidden on your own row → AC-1, AC-2, AC-13
- [x] Temporary access → the dialog: system, role (changes with the system), hours 1 to 8 with 4 picked, reason with a counter, password; start VRMS Admin for 2 hours → banner "You have temporary VRMS Admin access until …" with Open VRMS and End now; VRMS admins get the email → AC-9, AC-13, AC-24
- [x] Open VRMS from the banner → you are in VRMS as Admin → AC-9
- [x] End now → it warns that it signs you out everywhere; confirm → back to the login screen; VRMS admins get "ended early" → AC-10, AC-24
- [x] People → "All people" first (people with no role included, every system's roles shown with the system name, a Suite admin badge); pick VRMS → Add person shows → AC-17, AC-23
- [x] A person page as the suite admin → the system switcher; a person not in that system says "Pick another system above" → AC-23
- [x] As `vrms.admin@` while the suite admin holds a live grant: People shows them with "Temporary until …"; editing that role → "End the grant instead"; Temporary access lists the grant with End now → AC-11
- [x] Activity → "Suite wide" tab lists everyone's events, former members included → AC-20
- [ ] Deletion requests → "All systems": orphans first with "No admin left" → AC-21
- [x] Overview, Temporary access, People and Suite admins at 375px: no sideways scroll, the dialog scrolls inside the screen → AC-23

## Commands
- [x] `POST /auth/admin/suite-admins` without a reauth token → 403 `REAUTH_REQUIRED`; for someone holding a role → 409 `HOLDS_SYSTEM_ROLES`; for `state.unverified@` → 409 `NOT_ELIGIBLE`; a fourth → 409 `SUITE_ADMIN_LIMIT` → AC-1
- [x] Two adds of a third and fourth suite admin at once (two shells, same moment) → one wins, the other gets `SUITE_ADMIN_LIMIT` → AC-1
- [x] `POST /auth/admin/suite-admins/<own id>/remove` → 409 `SELF_ROLE` → AC-2
- [x] `insert into user_roles (… user_id = 9001, temporary_grant_id null …)` in psql → `suite_admin_no_roles` at commit → AC-3
- [x] As `vrms.admin@`, `PATCH /auth/admin/users/<9001>/status` with `isActive: false` (while 9001 holds a VRMS grant) → 409 `IS_SUITE_ADMIN`; same for `DELETE` → AC-3
- [x] As the suite admin, `POST /auth/profile/deletion-request` → 409 `IS_SUITE_ADMIN` and the reauth token stays unused → AC-3
- [x] `POST /auth/admin/temporary-grants` with `hours: 9` → 400 `VALIDATION_FAILED`; a second VRMS grant while one is live → 409 `GRANT_ACTIVE`; as `vrms.admin@` → 403 `NOT_SUITE_ADMIN` → AC-9
- [x] A grant inserted with `expires_at` a minute away → within about two minutes `end_reason = EXPIRED`, no actor, its `user_roles` row gone, `TEMP_ACCESS_ENDED` written, the directory feed's latest roles for 9001 empty → AC-10
- [x] With `expires_at` in the past but before the sweep runs, a VRMS refresh for that session answers without the role → AC-10 lazy expiry
- [x] `GET /auth/admin/report` as `vrms.admin@` → 403 `NOT_SUITE_ADMIN`; `GET /auth/admin/temporary-grants?system=BMS` as `vrms.admin@` → 403 `NOT_ADMIN_OF_SYSTEM` → AC-11, AC-19
- [x] `GET /auth/admin/users`, `/activity` and `/deletion-requests` with no `system` as the suite admin → 200 suite wide; as `vrms.admin@` → 400 → AC-17, AC-20, AC-21
- [x] A suite admin `PATCH /auth/admin/users/:id` giving any VRMS role → 403 `REAUTH_REQUIRED` without a token; with one → VRMS admins get "given the … role by a suite admin" → AC-14c

## Value sourcing
- [x] Report `since`: change a VRMS admin's name (not their role) → `since` stays; remove and give the admin role again → `since` is the new time → Value sourcing "report, admins, since"
- [ ] Report `grantedBy`: give `vrms.chief@` the VRMS Admin role from the portal → Overview shows you as granted by; a seed admin shows none → Value sourcing "report, admins, grantedBy"
- [x] Grant `expiresAt`: start with 3 hours → `expires_at - started_at` is exactly 3 hours → Value sourcing "temporary grant, expiresAt"
- [x] `temporaryUntil` on user lists equals the grant's `expires_at` → Value sourcing "user lists, temporaryUntil"
- [ ] `orphan`: a VRMS only person asks for deletion while VRMS has other admins → not orphan; deactivate every other VRMS admin in a test copy → orphan → Value sourcing "deletion lists, orphan"
- [x] Alert recipients: a VRMS grant reaches suite admins and VRMS admins only, not VMMS or BMS admins → Value sourcing "alert email, recipients"

## Acceptance-criteria coverage
- AC-1, AC-2, AC-4: the Suite admins steps and the suite admin commands
- AC-3: the trigger, `IS_SUITE_ADMIN` and deletion request commands
- AC-9 to AC-11: the Temporary access steps, expiry and lazy expiry commands, the VRMS admin view
- AC-13, AC-14c: the alert checks in the log
- AC-17, AC-20, AC-21: All people, Suite wide activity, All systems deletion requests
- AC-19, AC-23, AC-24: Overview, the views, the banner, 375px
- Not built yet: the VRMS roster skip (AC-11 last part, waiting on the directory shape), AC-32, slices 5 and 6

# Verify: slice 4, VRMS leavers · spec 0013 · updated 2026-11-13
_Steps for build plan task 18. The local database already holds feed release rows from 2026-11-11, so the notice shows until 2026-11-18; after that, make a fresh one (deactivate a seed mechanic who holds an open ticket, wait 30 s). Local SMTP is real, so blank `SMTP_*` before any account change._

## UI / manual
- [x] Sign in as `vrms.chief@` and open the Dashboard → a "Released after account changes" notice under At a glance, one row per release: plate, "<name>, account deactivated" (or deleted, or VRMS role removed), "Now <status>, <time> ago" → AC-32
- [x] Click a row → that ticket's page opens → AC-32
- [x] As a mechanic only account (no `mechanics.view`) → no notice, and no request to `/vrms/mechanics/released` in the network tab → AC-32
- [ ] With no release in the last 7 days (or after the window passes) → the notice is gone, nothing else on the dashboard moves → AC-32
- [x] At 375px → rows wrap, no sideways scroll → AC-32

## Commands
- [x] `GET /vrms/mechanics/released` with no token → 401; as `vrms.mechanic@` → 403; as `vrms.chief@` → 200, newest first, at most 50 → AC-32
- [ ] As an Admin, release a person's tickets by hand on the Users page (`POST .../release-tickets`) → those rows do not appear (only the feed's `SYSTEM` rows count) → AC-32

## Value sourcing
- [x] Released tickets come from `audit_logs` `MECHANIC_UNASSIGNED` rows with `actor_role = 'SYSTEM'`: compare the list with `select … where action = 'MECHANIC_UNASSIGNED' and actor_role = 'SYSTEM' and created_at >= now() - interval '7 days'` → same rows → Value sourcing "Chief notice, released tickets"
- [ ] Edge: a row 8 days old (move one row's `created_at` back in a test copy, with the append only trigger off) → it drops out → Value sourcing "Chief notice, released tickets"
- [ ] Erase a released person → the row now reads "Deleted user, account deleted" → Value sourcing "Chief notice, released tickets"

## Acceptance-criteria coverage
- AC-32: every step above

# Verify: slice 5, central permissions · spec 0013 · updated 2026-11-13
_Steps for build plan tasks 19 to 24. Already run once locally in the AC-28 order (catalog:sync, export, import, VRMS sync, drop). A matrix save sends alert emails and local SMTP is real: blank `SMTP_*` (read mails from the auth log) before saving. Sign in to the portal as `suite.admin@` (`admin1234`) and pass the code._

## UI / manual
- [x] Portal `/admin/permissions` as the suite admin → VRMS picked; groups Tickets, Records, Knowledge, Admin; columns Admin, Chief Mechanic, Mechanic; Admin on Manage the team and Change settings, and Mechanic on Remove anyone's files, show a lock and can't be clicked → AC-27
- [x] Flip a Mechanic cell on → it highlights, "1 change not saved" with Discard and Review and save; flip it back → the bar goes → AC-27
- [ ] Review and save a right added → the note is optional; save → toast, the Change history shows it at the top with your name; VRMS admins get "permissions were changed" with a link to the Permissions view → AC-27, AC-13
- [x] Take a right away → the dialog asks for a note of 5 to 500 characters and refuses "meh" → AC-27
- [x] Open the matrix in two tabs, save in one, then save in the other → "Someone saved this matrix after you opened it" with Reload the matrix → AC-27
- [x] As `vrms.admin@`: Permissions shows the VRMS matrix read only (no checkboxes enabled), with the history → AC-27
- [x] Change history → the 87 rows moved from VRMS read ", moved from VRMS"; Load more pages → AC-28
- [x] Within about a minute of a save, sign in to VRMS as that role → the right is there (or gone) with no restart → AC-29
- [x] VRMS Settings as `vrms.admin@` → no Roles and permissions section; "Permissions are edited in the portal. Open Permissions" opens the portal view in a new tab; the History filter offers All, Settings, Lookup lists → AC-30
- [x] Portal Permissions at 375px → each permission stacks with its role checkboxes named, no sideways page scroll → AC-27

## Commands
- [x] `npm run catalog:sync` twice in welinc-auth → the second prints "VRMS permissions: no changes" → AC-25
- [x] Set a locked cell by hand (`update role_permissions set allowed = false where role = 'ADMIN' and key = 'team.manage'`), run catalog:sync → "1 locked cells reset", one "Catalog sync" history row, version up by one → AC-25
- [x] `update permission_changes set note = 'x'` and `delete from permission_changes` in psql → both refused "append only" → AC-27
- [x] `GET /auth/permissions/VRMS` with VRMS's service token → 200 with `ETag: "v<n>"`; again with `If-None-Match` → 304; `GET /auth/permissions/BMS` with it → 403 `WRONG_SYSTEM`; a user token → 403 → AC-26
- [x] `PATCH /auth/admin/permissions/VRMS` as `vrms.admin@` → 403 `NOT_SUITE_ADMIN`; as the suite admin with an old `version` → 409 `MATRIX_STALE`; a locked cell → 409 `LOCKED_CELL`; role `DRIVER` → 400 `UNKNOWN_ROLE`; key `ticket.fly` → 400 `UNKNOWN_PERMISSION`; the same cell twice → 400 `VALIDATION_FAILED`; a save of current values → 200, same version → AC-27
- [x] `npm run permissions:import -- VRMS <file>` a second time → refused, "history was imported already" → AC-28
- [x] Stop welinc-auth for two minutes → VRMS logs one "Permission matrix sync failing" warning and keeps working on its copy; start it → "is back after … s" → AC-29
- [x] Make welinc-auth answer an empty matrix (every VRMS cell false in a test copy, version raised) → VRMS refuses it, keeps its copy and warns once → AC-29
- [x] `PATCH /vrms/permissions` and `GET /vrms/permissions/changes` → 404; `GET /vrms/permissions` as `vrms.admin@` → the synced copy with `source.etag` → AC-30
- [x] `npm run test` in backend-vrms → `catalog.spec.ts` keeps VRMS's keys equal to welinc-auth's 27 → AC-25, AC-30

## Value sourcing
- [x] Matrix ETag is `permission_matrices.version`: save once → the tag VRMS stores in `permission_sync_state.etag` moves from `"v<n>"` to `"v<n+1>"` → Value sourcing "matrix read, ETag"
- [ ] Import actor: a VRMS history row whose actor no longer exists here keeps its name with `actor_id` null; a VRMS backfill row (no actor) reads "VRMS (automatic)" → Value sourcing "matrix import, history actor"
- [x] VRMS sync matrix: a cell changed in the portal shows in VRMS's `role_permissions` after the next tick, and `GET /vrms/permissions/me` follows → Value sourcing "VRMS sync, matrix"
- [x] Alert recipients for a VRMS matrix save: suite admins and VRMS admins only → AC-13 table "permission matrix edited"

## Acceptance-criteria coverage
- AC-25: the catalog:sync and locked cell commands, the key match test
- AC-26: the service token commands
- AC-27: the Permissions view steps and the PATCH commands
- AC-28: the import rerun and the moved history rows
- AC-29: the sync, outage and empty matrix steps
- AC-30: the VRMS Settings step and the removed routes

# Verify: slice 6, contract and guide · spec 0013 · updated 2026-11-13
_Steps for build plan task 25 (AC-34). Docs only: no app needs to run._

## Commands
- [x] Contract 0001's header reads `**Contract version**: 7`, and its Amended line ends with the version 7 entry naming spec 0013 → AC-34
- [x] Each AC-34 item is in the contract: `SIGN_IN_CODE_REQUIRED` (section 10, `/auth/login`), `ADMIN_CODE_REQUIRED` (sections 10, 10a, 11), `SUITE_ADMIN_NO_ROLES` (sections 10, 10a, 11), `TEMP_ACCESS_ENDED` (section 6), `temporaryRoles` (section 9), the `/auth/admin/*` and `/auth/permissions/:system` routes (section 10a), the bearer admin routes marked deprecated (section 10), and the removed VRMS matrix routes (sections 10a, 14) → AC-34
- [x] Every `@Get`, `@Post`, `@Patch` and `@Delete` in welinc-auth's `admin.controller.ts`, `admin-accounts.controller.ts`, `suite-admin.controller.ts`, `admin-permissions.controller.ts` and `permissions.controller.ts` has a row in the section 10a table, and every row has a route → AC-34
- [x] `docs/integration/suite-admin.md` tells VMMS and BMS to delete their user pages (BMS keeps its crew screens), link the menu item to `<portal>/admin/people?system=<SYS>`, handle `SIGN_IN_CODE_REQUIRED` and `ADMIN_CODE_REQUIRED`, and that the central matrix is optional; every link in it and the contract's new links open → AC-34

## Acceptance-criteria coverage
- AC-34: the four steps above
