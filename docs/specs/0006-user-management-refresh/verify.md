# Verify: User management page · spec 0006 · updated 2026-10-25
_Steps derived from spec 0006 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Sign in as `vrms.admin@welinc.com` (seed). Restart `welinc_vrms_backend` first if the backend changed.

## UI / manual

### Page and list
- [x] As a mechanic, open `/users` → redirected away by `RequireRole`; no "Access Denied" card exists → AC-1
- [x] As admin, `/users` → header "Users", the subtitle, a primary "New user" button with the `UserPlus` icon → AC-1
- [ ] Give one user a lock (5 bad sign ins), leave one unverified, deactivate one → badges read Locked, Setup pending, Inactive; Inactive wins over Locked when both apply → AC-2
- [x] `/dev/ui` status row shows SETUP_PENDING and no PENDING_VERIFICATION → AC-2
- [ ] Tiles read Locked, Setup pending, Active, Inactive in that order; counts cover all users, not the filtered set (search "zzz" and the counts stay) → AC-3
- [x] Press Locked → `?status=LOCKED`, tile has `aria-pressed=true` and a ring; press it again → filter cleared. Press a tile with count 0 → the "No users match these filters" state → AC-3, AC-7
- [x] Accessible name of a tile is exactly "Locked, 0" (snapshot) → AC-3
- [x] Two tiles per row at 375px, four across at 1024px → AC-3
- [x] Open `/users?status=LOCKED&q=juan&role=MECHANIC&page=2` → filters and search box prefilled, Locked tile pressed → AC-4
- [x] `?role=DRIVER&status=FOO&page=-1` → reads as all roles, all statuses, page 1. A 150 character `q` is cut to 100 → AC-4
- [ ] Type in search: the URL changes about 300ms after typing stops, with `replace` (Back leaves the page, not each keystroke); any filter change resets `page` → AC-4
- [x] Type in search, then open New user within 300ms → the URL does not change while the dialog is open; it updates after closing → AC-4
- [x] "Clear filters" shows only while a filter is set and clears all three → AC-4
- [x] Order: Locked, then Setup pending, Active, Inactive; within a status by name ignoring case, then email → AC-5
- [x] With more than 20 users the pagination shows; with 20 or fewer it does not. `?page=99` shows the last page and the URL stays `page=99` → AC-6
- [ ] Desktop columns User (name, email, "You" on your row), Role (+n badge for more than one VRMS role), Status, Added. At 375px cards: name title, email subtitle, status badge, role field, no Added → AC-6
- [x] Click a row → edit dialog → AC-6
- [x] Throttle `/auth/users` to fail on first load → ErrorState with "Couldn't load users." (or the server message) and Try again; tiles hidden → AC-7
- [x] Delete every user from the response (mock) → "No users yet" with a New user action → AC-7
- [ ] Switch tabs and back → one `GET /auth/users`, no skeleton. Make it fail twice in a row → one "Couldn't refresh users." toast, rows kept → AC-8
- [ ] Start a Deactivate (confirm open), switch tabs and back → no list request while the action is in flight; the row ends Inactive → AC-8

### Row actions
- [x] Menu per status: Active = Edit, Send reset code, Deactivate. Setup pending = Edit, Resend setup code, Deactivate. Locked = Edit, Unlock and send reset code, Unlock, Deactivate. Inactive = Edit, Reactivate. Your own row has no Deactivate → AC-9, AC-22
- [x] Each trigger is named "Actions for {name}" → AC-9
- [x] After any action or its cancel, focus lands on that row's trigger; if the row moved off the page, on the search box → AC-9
- [ ] While an action runs on a row, picking another non Edit action on that row does nothing → AC-9

### Create and edit
- [ ] New user dialog: title, description, Name, Email (helper "This is their sign in."), Role toggle defaulting to Mechanic, no password, no active checkbox. At 375px it is a bottom sheet → AC-10
- [x] Submit empty → "Enter their name." and "Enter their email." under the fields, focus on Name → AC-10, AC-13
- [x] Create `New.Tech@welinc.com` → request body has lowercased email, `roleAssignments` VRMS, no `password`/`isActive`; toast "{name} added. A setup code was sent to {email}."; row appears as Setup pending at the top → AC-10, AC-5
- [x] Stop SMTP and create → dialog closes, row shows, toast "… was added, but the setup email couldn't be sent. Use Resend setup code." → AC-10
- [x] Edit with no changes and Save → closes, no request → AC-11
- [x] Edit name only → PATCH sends `name` only; toast "{name} updated." → AC-11
- [x] A user with two VRMS roles: role toggle disabled with "This user has a role this page can't edit yet."; Save never sends `roleAssignments` → AC-11
- [x] Edit your own name → header name updates; `welinc_user` and `welinc-auth-storage` hold it → AC-11
- [x] While the edit dialog is open, delete that user elsewhere and refocus the tab → dialog closes, info toast "{name} is no longer in the list." → AC-11
- [x] Change the email → "Change their sign in email?" prompt; Keep editing returns with values kept and sends nothing; on your own row the extra sentence shows → AC-12
- [x] Use an existing email → 409 → "An account with this email already exists." under Email → AC-13
- [ ] Use `x@nodomain.invalid` → domain message under Email → AC-13
- [x] Force a 500 on update → FormAlert and toast "Couldn't save: {message}"; offline → "Couldn't save. Check your connection and try again." → AC-13
- [x] While saving: spinner on primary, both buttons disabled, Escape and overlay click do nothing. Double Enter makes one request and one prompt → AC-13
- [ ] Type, press Escape → "Discard changes?"; Keep editing keeps the text; Discard closes; focus back on New user → AC-14
- [x] Your own row: role toggle disabled with "You can't change your own role." → AC-22

### Account actions
- [x] Deactivate a user with no open work → prompt, toast "{name} deactivated.", row moves to the bottom as Inactive → AC-15, AC-5
- [x] Deactivate Juan dela Cruz (seed, open tickets; `isAvailable` false on `GET /vrms/mechanics/available`) → "Reassign Juan dela Cruz's work first", no status request; Open their tickets → `/repairs?mechanic=<his mechanic id>` filtered → AC-16 (2026-10-28: ran, passed)
- [x] Block `/vrms/mechanics/available` and deactivate a mechanic → "Couldn't check open work" with Try again; for an admin only user the check is skipped → AC-16
- [x] Reactivate: description follows `emailVerified` and `isLocked`; toast "{name} reactivated." → AC-17
- [ ] Send reset code → `POST /auth/forgot-password` with the row's email; toast "Reset code sent to {email}." Failure → "Couldn't send the reset code: …" → AC-18
- [ ] Resend setup code → same call, its own title and toast → AC-19
- [x] Unlock and send reset code → unlock then forgot password; row no longer Locked; toast "{name} unlocked. A reset code was sent to {email}." Fail only the send → "{name} is unlocked, but the reset code couldn't be sent: …" → AC-20
- [x] Unlock → toast "{name} unlocked." → AC-21

### Value sourcing
- [ ] Status badge, tile counts, sort rank derive from `isActive`, `isLocked`, `emailVerified`: flip each field in the auth DB and reload → the badge follows the AC-2 order
- [ ] Role badge is the first `roles[]` entry with `system === 'VRMS'`: give a user a VMMS role first → still shows the VRMS role
- [ ] "You" badge from `authStore.user.id`: sign in as a second admin → the badge moves
- [ ] Added date from `createdAt` via `formatShortDate`
- [x] Filters and page come from the URL only: reload keeps them
- [x] Setup email comes from welinc-auth because no password is sent (check the create request body)
- [ ] Edit sends only the VRMS role; a user's VMMS role survives a role change
- [ ] Email change prompt compares trimmed, lowercased values: changing only the case of the email does not prompt
- [x] Reset recipient is the row's email (request body)
- [ ] Open work: a mechanic with `email: null` matches only by name and only for a VRMS MECHANIC user; one with an email matches only by email
- [x] "Open their tickets" uses `mechanic.id` in `/repairs?mechanic=`

## Commands
- [x] `curl -H "Authorization: Bearer $TOKEN" localhost:3000/vrms/mechanics/available` → each item has `email` (string or null), same order and fields as before → AC-23
- [ ] The repair form's mechanic picker still loads → AC-23
- [x] `grep -rn "Password123\|user-management/hooks/useUsersManager\|resetUserPassword" welinc-web-vrms/src` → nothing → AC-24
- [x] axe on `/users` at 375px and 1280px, with and without the New user dialog → no serious or critical issues; no horizontal scroll → AC-25
- [x] welinc-web-vrms: `npm run lint`, `npm run typecheck`, `npm run build` pass → AC-26
- [x] welinc-backend-vrms: `npm run build`, `npm run test` pass; `npm run lint` runs `--fix` and fails on pre-existing issues (see scope note) → AC-26

## Acceptance-criteria coverage
- AC-1 to AC-8: Page and list · AC-9: Row actions · AC-10 to AC-14, AC-22: Create and edit · AC-15 to AC-21: Account actions · AC-23 to AC-26: Commands
