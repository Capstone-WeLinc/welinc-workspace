# Verify: permission matrix · spec 0011 · updated 2026-10-29
_Steps derived from spec 0011 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._
_Milestone 1 (thin thread) only. Later milestones append their steps below._

## UI / manual
- [ ] Sign in as Admin → sidebar shows Dashboard, Repair tickets, New repair, Repair history, Analytics, Knowledge base, Users, Audit logs → AC-14, AC-22
- [ ] Turn `analytics.view` on for Chief Mechanic by hand in the database and bump the version, focus the tab → Analytics appears for the Chief and `/analytics` opens; revert → it disappears and `/analytics` by URL goes to the dashboard → AC-22a
- [ ] Sign in as Chief Mechanic → nav shows "Repair tickets" (not "My repairs"), no New repair, Users or Audit logs; the list shows every open ticket with no cost columns → AC-14, AC-10
- [ ] Sign in as Mechanic → nav shows "My repairs"; the list holds only their assigned tickets → AC-10, AC-14
- [ ] As Mechanic, open `/repairs/new` by URL → sent to the dashboard → AC-22
- [ ] Throttle the network (slow 3G) and reload → shell skeleton shows, no nav item, until `/vrms/permissions/me` answers → AC-23
- [ ] Block `/vrms/permissions/me` in devtools and reload → "Could not load your permissions" with Try again; unblock and press it → the shell loads → AC-23
- [ ] Sign in as an account with only `CUSTOMER_SUPPORT` in VRMS → "No VRMS access" with Sign out → AC-5, AC-23
- [ ] Turn a key off by hand in the database and bump the version, then focus the tab → the nav item disappears without a reload → AC-20, AC-23

## Commands
- [ ] `GET /` before the matrix has loaded (stop the DB, restart the backend) → 503; after the DB is back and a request loads it → 200 → AC-21
- [ ] Fresh database: start the backend → log line "Permission backfill inserted 48 rows"; `select count(*) from role_permissions` → 48; `permission_changes` has 48 rows with a null actor; `permission_matrix.version` went up by one → AC-2, AC-3
- [ ] Restart again → no rows inserted, version unchanged, a hand edit to a cell survives → AC-3
- [ ] Start two backends at once on an empty table → 48 rows, not 96 → AC-3
- [ ] `GET /vrms/permissions/me` as each role → Admin 15 keys, Chief 7, Mechanic 5, and the matrix version; no rules in the body → AC-1, AC-16
- [ ] Set `ADMIN, users.manage` to false in the database and bump the version → the Admin still has `users.manage` in `/me` → AC-4
- [ ] Set `MECHANIC, audit.view` to true and bump the version → the next mechanic request to `GET /vrms/repairs/audit-logs` answers 200; revert → 403 → AC-20
- [ ] Delete one `MECHANIC` row and bump the version → that key is gone from the mechanic's `/me` → AC-6
- [ ] As Mechanic: `GET /vrms/repairs/:id` of another mechanic's ticket → 403 "You are not assigned to this repair ticket"; own ticket → 200 → AC-10
- [ ] As Chief: the same other ticket → 200 with no `totalCost`; history `summary.spend` is null → AC-10, AC-14
- [ ] As Mechanic: `POST /vrms/repairs` → 403 `{ statusCode: 403, message: 'You do not have permission to do that.', permission: 'ticket.create' }` → AC-8
- [ ] Two mechanics call `GET /vrms/repairs` one after the other on one replica → each sees only their own tickets → AC-9
- [ ] An account holding Mechanic and Admin in VRMS → `/me` holds both roles' keys → AC-5
- [ ] `npm run test` in welinc-backend-vrms (ability, service and guard specs) and `npm run test` in welinc-web-vrms (nav) → pass

## Value sourcing
- [ ] Caller's roles: change a user's VRMS role in welinc-auth → within 30 seconds `/me` follows it
- [ ] Each role's grants: a stored row change applies only after the version moves (edit without a bump → no change; bump → change)
- [ ] Locked cells: come from `catalog.ts`, never the row (step above for AC-4)
- [ ] `keys`: union over the caller's matrix roles only; a role outside the matrix adds nothing
- [ ] `version`: equals `permission_matrix.version` in the database
- [ ] Startup backfill default `allowed`: each inserted row matches its `catalog.ts` default

## Acceptance-criteria coverage
- AC-1 `/me` key counts · AC-2, AC-3 backfill steps · AC-4 locked cell · AC-5 multi role and CUSTOMER_SUPPORT · AC-6 deleted row · AC-8 POST as mechanic · AC-9 two mechanics · AC-10 detail scope · AC-14 role nav and list · AC-16 `/me` body · AC-20 version bump · AC-21 cold replica · AC-23 skeleton, error, no access, refetch
- Milestone 2 below covers AC-4, AC-7, AC-8, AC-11 to AC-13, AC-15, AC-17 to AC-19, AC-22, AC-22a, AC-24, AC-25
- Later milestones (AC-26 to AC-37): not yet

# Milestone 2: every route and screen on the matrix · updated 2026-10-29

## UI / manual
- [ ] As Admin, open Users → "Roles and permissions" lists every key by group against Admin, Chief Mechanic and Mechanic; Manage users and View and change permissions show a lock; Recent changes shows the last 10, with System for the backfill rows → AC-25
- [ ] As Chief Mechanic, open Users by URL → sent to the dashboard; the section never shows → AC-22, AC-25
- [ ] As Chief, open another mechanic's ticket → it reads "This ticket is assigned to someone else", with no action button, no Cancel, no Costs or Activity section → AC-12, AC-12a, AC-14
- [ ] As Chief, open your own Assigned ticket → Start work shows; at For verification it reads "Waiting for an admin to sign off" → AC-12
- [ ] As Admin, open a For verification ticket → Verify and close, Cancel, Costs and Activity all show; a Closed ticket offers Unlock → AC-12a, AC-14
- [ ] As Mechanic, the knowledge base shows Suggest buttons and no New entry; as Chief, New entry and no Suggest → AC-13, AC-22
- [ ] Turn `analytics.view` on for Chief by PATCH, then focus the Chief's tab → Analytics shows and the group reads "Analytics & AI"; on a phone width the bottom tab bar gives way to the sheet menu; revert → it goes, and `/analytics` by URL lands on the dashboard → AC-22a
- [ ] As Chief on the knowledge editor, turn `knowledge.edit` off for Chief, then save the entry → toast "You no longer have permission to do that.", the page moves to the dashboard; two quick 403s give one toast → AC-24

## Commands
- [ ] `npm run test` in welinc-backend-vrms → the route table (every route × Admin, Chief, Mechanic, Customer Support) and the decorator checks pass → AC-7, AC-15
- [ ] `GET /vrms/permissions` as Admin → 200 with groups Tickets 8, Records 3, Knowledge 3, Admin 2; as Chief → 403 `{ permission: 'permissions.manage' }` → AC-8, AC-17
- [ ] `PATCH /vrms/permissions` with `ADMIN users.manage false` → 400, nothing changes → AC-4
- [ ] PATCH with an unknown role or key, 101 changes, or a 501 character note → 400 → AC-18
- [ ] Two PATCHes sent at once with the same `version` → one 200, one 409 "The permissions were changed by someone else. Reload to see the latest." → AC-18
- [ ] PATCH a cell to the value it already has → 200, version unchanged, no change row → AC-18
- [ ] `GET /vrms/permissions/changes?limit=2` → newest first with `nextCursor`; follow it → the next two; `cursor=nope` → 400; `limit=101` → 400 → AC-19
- [ ] As Chief, `GET /vrms/repairs` → every row has `can`, and `partsCost`, `laborCost`, `totalCost` are null; as Admin, values → AC-11, AC-12a
- [ ] As Chief, `PATCH /vrms/repairs/:id/status` on another mechanic's ticket → 403 "You are not assigned to this repair ticket" → AC-12
- [ ] As Chief, a status move to In progress on your own ticket with `partsCost` in the body → the cost is unchanged → AC-11
- [ ] As Mechanic, `GET /vrms/knowledge/entries/:id` of a draft → 404; as Chief → 200 with `typicalCost` → AC-13
- [ ] Insert a row for a key not in the catalog, bump the version, run `npm run permissions:prune` → it logs the row, deletes it, writes a change row with `after` null, and bumps the version → AC-3
- [ ] `npm run seed` → the matrix holds the 48 default rows and 48 System change rows → seed reset

## Value sourcing
- [ ] Change rows' actor: PATCH with a body that also carries `actorName` → 400 (not whitelisted); the row's actor is the token's name and email
- [ ] `before`: hand edit a cell in the database without bumping, then PATCH it → the change row's `before` is the hand edited value
- [ ] Ticket `can` flags: reassign a ticket to the Chief → their next read flips `can.work` to true
- [ ] GET matrix locks and labels: come from `catalog.ts`; a hand edit of a locked row still shows the catalog value

# Milestone 3: welinc-auth scoped by system · updated 2026-10-29
_Send every request with the VRMS admin's token and `Origin: http://localhost:8001`, so the caller's system resolves to VRMS. The steps below leave the seed data as they found it._

## Commands
- [ ] `GET /auth/users` → every user holds a VRMS role, `roles` lists only VRMS roles, `otherSystems` names the rest (the seeded mechanics show `VMMS`); `?system=BMS` with a VRMS only admin → 403, it can't widen the list → AC-26
- [ ] `GET /auth/users/<bms.admin id>/changes` → 404 `User not found`; the same for PATCH, status, unlock, password and DELETE on that id → AC-26
- [ ] `GET /auth/users/lookup?q=b` → 400; `?q=bms.ad` → `[{ id, name, email, systems: ['BMS'] }]` with no other fields; at most 10 rows; the 31st call in a minute → 429 → AC-29
- [ ] `POST /auth/users` with `BMS.admin@welinc.com` and a VRMS Mechanic role → 409 `{ code: 'ACCOUNT_EXISTS', id, name, systems: ['BMS'] }` → AC-30
- [ ] The same body with `attachExisting: true` → 201, `roles` holds only VRMS Mechanic, `otherSystems` is `['BMS']`; bms.admin still signs in with `admin1234`; the change record's newest row is `ROLE_CHANGED` from `ADMIN@BMS` to `ADMIN@BMS,MECHANIC@VRMS`; sent once more → the plain 409 `Email already exists` → AC-30
- [ ] On that shared account: PATCH with a BMS role → 403 `You can only change VRMS roles.`; PATCH password, or PATCH a new email → 403 `This account is an admin in BMS. Send a reset code instead.`; DELETE → 403 `This account is shared with BMS. Remove its VRMS role instead.` → AC-27, AC-28
- [ ] PATCH it with `roleAssignments: []` → 200 and the account leaves VRMS (its changes now answer 404); the same on a VRMS only account → 400 `An account needs at least one role. Deactivate it instead.` → AC-28
- [ ] POST with a BMS role in `roleAssignments` → 403 → AC-27
- [ ] Deactivate a shared account (a seeded mechanic) → 200, and they can no longer sign in to VMMS either → AC-28
- [ ] `npm run test` in welinc-auth → `auth.service.scope.spec.ts` passes → AC-26 to AC-30

## Value sourcing
- [ ] Caller's system: the same admin token sent with `Origin: http://localhost:8000` and `?system=BMS` acts on BMS only if that account is a BMS admin, else 403
- [ ] Shared check: add a BMS role to a VRMS only user by hand in the database → the next list shows `otherSystems: ['BMS']` and DELETE now answers 403

## Acceptance-criteria coverage
- AC-26 list, changes, 404 on every write · AC-27 role edit and create · AC-28 admin elsewhere, delete, empty list, deactivate · AC-29 lookup and rate limit · AC-30 ACCOUNT_EXISTS, attach, plain 409

# Milestone 4: open work and close out · updated 2026-10-29
_Use the seeded VRMS mechanics. Restart `welinc_vrms_backend` first (see the backend AGENTS.md). Put the data back when you finish._

## UI / manual
- [ ] Users page, deactivate a mechanic who holds an Assigned and an In progress ticket → the confirm shows the count by status, "Move them back to the queue" is selected, "Keep them assigned" is the other choice → AC-35
- [ ] Choose "Move them back to the queue" → the Assigned ticket is Open, the In progress one keeps its status and shows "Needs a mechanic", each ticket's activity shows a "removed a mechanic" event → AC-33, AC-34, AC-35
- [ ] Deactivate another mechanic and choose "Keep them assigned" → their tickets stay, the list shows "Inactive mechanic" → AC-34, AC-35
- [ ] Deactivate a mechanic with no open tickets → the plain Deactivate confirm, no choice → AC-35
- [ ] Deactivate a shared account (a seeded mechanic) → the confirm says "This also blocks their VMMS sign in." → AC-35
- [ ] Stop the backend, then confirm a deactivate with "Move them back" → the user is deactivated, a toast says the tickets couldn't be moved and offers Retry; Retry after the backend is back moves them → AC-35
- [ ] Edit a mechanic and change the role to Admin → asks about open tickets, then moves them with reason "VRMS role removed" → AC-33, AC-35
- [ ] Dashboard as Admin → "Needs attention" lists overdue first, then tickets with an inactive or missing mechanic, then waiting for sign off → AC-34
- [ ] New user → "Existing WeLinc account" → type 2 letters of a BMS only admin → the account shows with "In BMS"; pick it, choose a role, Add to VRMS → they appear in the list and keep their password → AC-36
- [ ] New user → "New account" with that account's email → "Add the Mechanic role in VRMS to it? They keep their current password." → confirm attaches → AC-36
- [ ] Edit a shared account → the dialog says a new email changes their sign in for every system; the email confirm repeats it → AC-36
- [ ] Edit an account that is ADMIN in another system, change the email → the dialog shows the server's message and the email field turns read only → AC-28, AC-36
- [ ] Dashboard dialogs and the Users page at 375px → the choice list and the picker fit without sideways scroll

## Commands
- [ ] `GET /vrms/mechanics/<authUserId>/open-work` as Admin → `{ total, byStatus }` with every open status as a key, zeros included; a person with no Mechanic row → total 0; as a Mechanic → 403 → AC-32
- [ ] `POST /vrms/mechanics/<id>/release-tickets` `{ reason: 'DEACTIVATED' }` for an active mechanic → 409 `They still have access to VRMS.`; unknown id → 404; a bad reason → 400 → AC-33
- [ ] The same call after deactivating them → `{ released, reopened }`; calling it again → `{ released: 0, reopened: 0 }` → AC-33
- [ ] Lock a mechanic with 5 wrong passwords, then `POST /vrms/mechanics/sync` → their Mechanic row stays active and their tickets show no badge → AC-31, AC-34
- [ ] `npm run lint`, `npm run build`, `npm run test` in backend-vrms and welinc-auth; `npm run lint`, `npm run typecheck`, `npm run build`, `npm run test` in web-vrms → all pass → AC-37

## Value sourcing
- [ ] `hasInactiveMechanic`: deactivate an assignee of an open ticket, keep assigned → the flag is true on list and detail; close the ticket → false
- [ ] `needsMechanic`: an In progress ticket with only an inactive assignee → true; assign an active mechanic → false
- [ ] Release `note`: reason DEACTIVATED → "Account deactivated", ROLE_REMOVED → "VRMS role removed" in the ticket's activity

## Acceptance-criteria coverage
- AC-31 roster ignores lock · AC-32 open work · AC-33 release and idempotence · AC-34 flags, badges, dashboard · AC-35 confirms and Retry · AC-36 Add user paths and shared notes · AC-37 close out
