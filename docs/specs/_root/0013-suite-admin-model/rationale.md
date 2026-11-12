# 0013. Suite admin model: rationale

Decision record for [index.md](index.md). `/develop` doesn't read this file.

## Context

Today every admin right in the suite is a system admin right: each system's catalog marks one role `isSystemAdmin` (spec 0004), and that admin manages only the people who hold a role in their system (spec 0011). Nobody can manage an account across systems, close a shared account, decide a deletion request for someone with no admin left (spec 0012 follow up), or see who holds admin where. The VRMS Users page, the VMMS `UserManagement.tsx` (614 lines) and the BMS `admin/UserManagement.tsx` (837 lines) each repeat the same account actions on `/auth/users*`, and VMMS and BMS would have to port theirs in S11.

The Capstone 1 panel called a single everyday superuser role that skips every check insecure. VMMS asked that the top admin see no system data, since each system has its own admin. At the same time a small team needs a way to step in when a system's only admin is away or something is broken, and a way back in if every top admin is locked out.

Admin sign in today is a password only. VRMS feature 34 planned an OTP for admins, and spec 0009 already built an emailed sign in code (one table, argon2 hashed, 5 tries, send limits) that is only used for unverified emails. The mobile clients accept no admin role (`oauth_clients.allowed_roles`), so every admin signs in through the portal's web login.

VRMS keeps its own role permission matrix (VRMS spec 0011: `role_permissions`, a version row, `permission_changes`, an Admin edit screen). VMMS plans to move to permission checks too. The people who run each system's admin and the suite are the same small IT team. The deadline is deployment by the end of November 2026, with S11 and hosting still after this row.

## Options considered

### Option 1: An everyday superadmin role

One role in welinc-auth that passes every system's checks and manages everything.

**Pros**:
- Smallest build; one check everywhere.

**Cons**:
- Exactly what the Capstone 1 panel rejected: one stolen account reads every system's data, with no trail of why.
- VMMS asked for the opposite.

### Option 2: Platform admin with no data access and no way in

A suite admin manages accounts and roles only; using a system always needs a permanent role granted by another admin. Account actions stay in each system's own pages.

**Pros**:
- Strictest separation; nothing new in the token path.
- Smaller than option 3 (no portal admin section, no matrix move).

**Cons**:
- When a system's only admin is away, nobody can step in without a permanent grant that tends to stay.
- VMMS and BMS still port about 1,450 lines of user pages in S11, and three copies of the same rules drift.
- No central matrix, so each system invents its own permission editing.

### Option 3: Dedicated suite admin, temporary self grants, one portal admin section, central matrix (chosen)

Suite admins live in their own table (1 to 3), hold no system roles, and may give themselves one system role for 1 to 8 hours with a reason and alerts. Every admin passes an emailed code at portal sign in. All account actions move to cookie authenticated `/auth/admin/*` routes the portal uses, scoped by who is looking. The matrix moves to welinc-auth; systems read a cached copy.

**Pros**:
- No silent superuser, yet a fast, visible way in for emergencies.
- One admin screen and one set of rules for three systems; VMMS and BMS delete code instead of porting it.
- The access report and alerts make a second account trick visible.

**Cons**:
- The biggest build of the three: four repos, six slices.
- Two admin route families until S11 is done.
- Ending a temporary grant ends the holder's whole web session.

### Option 4: Option 3 with the matrix left in VRMS

Everything in option 3 except permission editing, which stays per system.

**Pros**:
- Saves slice 5 (about a quarter of the work) before the deadline.

**Cons**:
- A VRMS admin keeps the power to widen their own role's rights.
- Each system that moves to permission checks builds its own editor and history.

## Rationale

Option 3 is the only one that answers both the panel's objection and the small team's need. The forces were: no hidden superuser (the panel), no system data for the top admin (VMMS), someone must be able to step in (a team of a few people with one admin per system), and fewer copies of the same account screens (S11 is still ahead and the deadline is close). A temporary self grant with a reason, a cap of 8 hours, an alert to that system's admins and an automatic end gives the step in path without an everyday bypass. That is the time limited access with justification pattern big identity platforms use, sized down.

Suite admins get their own table instead of a `SUITE` system in the catalog. Every loop over systems (launcher, directory, `LAST_ADMIN`, deletion emails) would otherwise have to learn to skip it, and a missed one would leak suite admins into a system. "Separate accounts" (no permanent system roles for a suite admin) keeps the data boundary checkable with one rule (AC-3), at the cost of two logins for anyone with both jobs.

The emailed code reuses spec 0009 whole, so it is almost free and ships before the deadline. It is a weak second factor because password reset also goes by email; you chose it now with TOTP as an optional later step, and the spec says so in Consequences. It applies to every admin, not just suite admins, because a system admin can deactivate people, send reset codes and approve deletions; the cost is one screen on one login, since mobile clients take no admin role. Spec 0009's code rules win over feature 34's (5 minutes, a 15 minute lock) because a code lock that locks the account would let anyone lock an admin out by guessing.

Cookie routes under `/auth/admin` (not tokens in the portal) keep contract 0001's promise that page scripts never hold tokens, and reuse the CSRF guard the portal already passes. One service layer under both route families keeps the rules identical while the bearer routes live on.

You chose to include the matrix (option 3 over option 4) because the IT team is the same people across systems and VMMS is moving to permission checks. Declaring keys in the welinc-auth catalog follows spec 0004's pull request flow for roles, and an ETag check every minute with a cached copy matches the directory's "within about a minute" promise without making VRMS fail when welinc-auth is down. Moving the old VRMS history (your call, over keeping it read only in VRMS) means one history per system in one place, paid for by an export and import pair run once.

## Recommendations made during writing

- **Temporary grant end cuts the session**: ending a grant ends the holder's live sessions that carry that system. Runner up: let the access token run out (up to 15 minutes). Chosen because the role must stop when it says it stops; VRMS sees an ended session within 30 s.
- **Sweep every minute** for expiries, under an advisory lock like the hourly sweep. Runner up: lazy expiry on read; rejected because the directory triggers would never fire.
- **Password recheck** (spec 0012 reauth token) for adding or removing a suite admin and for starting temporary access. Runner up: rely on the sign in code alone; rejected because these are the escalation steps.
- **`team.manage` replaces `users.manage`** in VRMS: the work routes behind `users.manage` (workload, open tickets, release, roster, sync) still need a gate after account actions leave. Runner up: reuse `mechanics.view`; rejected because Chief Mechanics hold it and shouldn't get Reassign on the Users page.
- **`ADMIN_SIGN_IN_CODE` switch**: seed admin addresses can't receive mail and local SMTP is real, so local work needs a way around the code; production refuses it.
- **Leaver alert as a dashboard notice**, built from the audit rows spec 0012 already writes. Runner up: emails to Chief Mechanics; rejected as noisy and VRMS has no mail path.
- **`temporaryRoles` beside `roles`** in the directory answer (you chose it during `/develop`, 2026-11-13). Runner up: `roles` as objects with `temporary: boolean`, as first written; rejected because it changes a shape contract 0001 section 9 already fixes (`roles: string[]`), while a second list is additive and a reader that ignores it keeps working. The stored snapshot still keeps the per role flag, since the feed is built from it.
- **`grantedBy` for system admins** read from the newest matching `ACCOUNT` event instead of a new `user_roles` column: the event already records the actor, and the confirmed model had no column for it.
- **Matrix move by scripts**, not a route: a one time job needs no permanent API surface or new scope.
- **After the cross check** (Sonnet, 2026-11-12): you closed two takeover paths. Actions on an admin account (email, reset code, unlock, sessions) need the actor's own password and alert the admins, and a suite admin's email changes only through their own inbox (AC-14b). Every role or account a suite admin gives needs a recheck and an alert, with no separate list; the second account trick stays as an accepted, loud residual risk (AC-14c). Also from the cross check: a deferred trigger for the no roles rule, lazy expiry beside the sweep, the `temporary` flag in the directory, an empty launcher for suite admins, the matrix rollout order and the empty matrix guard. One recheck purpose, `ADMIN_ACTION`, covers every admin level action; `TEMPORARY_ACCESS` stays separate.
- **Bearer admin routes deprecated, not removed**, until S11, so VMMS and BMS keep working while they delete their pages.

## Evidence: what exists today (read 2026-11-12)

- welinc-auth: `isSystemAdmin` per system in `prisma/catalog/*.ts`; `@SystemAdmin()` reads it per request; `user-scope.ts` scopes by `aud`; self role change answers 409 `SELF_ROLE`; `assertAnotherAdmin` guards the last admin; no suite, platform or super admin; no TOTP; `SIGN_IN` codes in `codes/sign-in-step.service.ts`; reauth tokens with purpose `ACCOUNT_DELETION` only; no email on role changes; `ACCESS_TOKEN_MINUTES` default 15; the session sweep runs hourly.
- Client registry: `vmms-mobile` allows VMMS and VRMS `MECHANIC` and `CHIEF_MECHANIC`; `bms-mobile` allows BMS `DRIVER` and `HELPER`. No admin role on mobile.
- welinc-web-portal: routes `/`, `/login`, `/forgot-password`; no admin section; the top bar account menu shows name, email and Sign out.
- welinc-web-vrms: the Users page (`features/user-management/pages/UsersPage.tsx`) calls `/auth/users*` for list, create, edit, status, unlock, sessions, activity, lookup and deletion decisions, behind `users.manage`.
- welinc-backend-vrms: `src/auth/permissions/catalog.ts` holds keys, labels, groups, defaults, locks and modules; `role_permissions`, `permission_matrix` (version) and `permission_changes`; `PATCH /vrms/permissions`; spec 0012's feed applier already unassigns a leaver's open tickets with `MECHANIC_UNASSIGNED` audit rows.
