# 0017. Person page shows the whole person (People list and detail)

**Date**: 2026-11-23
**Status**: In Progress
**Scope row**: [S19](../../../scope/_root/shared-services.md#s19-person-page-shows-only-the-persons-systems--in-progress--beta)
**Design source**: board `People8` (canvas "WeLinc design directions", page "Round 8"), the Access rows of `People4`, and the Add person dialog AA of `AddPerson6`. Copies live in [boards/](boards/) (`.dc.html` source, readable from any account); the canvas is https://claude.ai/artifact/VFhLSMNhfpAFD4D4c2VQzp. Your picks: `docs/context/vrms/handoff-2026-11-18.md` (git, commit 33db0d0). The look follows spec [0016](../0016-design-direction-refresh/index.md).

## Summary

Today an admin who opens someone from People sees that person "inside one system", and gets a dead end with no name or email when the person isn't in that system. This spec rebuilds People as the approved `People8` page: the list on the left, the whole person on the right, with Overview, Access, Signed in devices and Activity tabs, and each system shown as a row in Access instead of something you pick first. welinc-auth learns one rule (leave out `system` and you get every system you admin), a `group` and a `sort` on the list, a `last_signed_in_at` column, and a few facts for the person header. The welinc-auth half can ship first; the page builds after S18's shell milestone, so it is built once, in the new look.

## Requirements

**User stories**:
- As a suite admin, I want to open anyone from People and always see who they are and where they have access, so that I never hit a dead end.
- As an admin of two or more systems (for example VRMS and VMMS), I want one People list across my systems and one page per person, so that I don't look up the same person per system.
- As an admin, I want the people who need me (locked, pending, pending deletion) at the top, so that I act on them first.

**Acceptance criteria**:

*Page and list*
- **AC-1**: `/admin/people` is one page with the list pane (360px) beside the person pane, on spec 0016's app shell, as on `People8`. Selecting a row shows the person and replaces the address with `/admin/people/:id` (keeping `?system`, `?q`, `?sort`), so Back leaves People instead of stepping through people. `/admin/people/new` (matched before `:id`, which is a UUID) opens the Add person dialog. The list does not scroll to or fetch a selected person who isn't in the loaded pages. On phones (below 768px) the list and the person are separate screens, the person with a back link. Leaving People keeps no system selection; other admin pages and their `useAdminSystem` picker are unchanged.
- **AC-2**: Opening any person never shows the old "This person isn't in [system]" dead end. The person and activity calls never send `system` (except the Activity filter, AC-15); `?system` only sets the list filter. A 404 shows "This account no longer exists, or isn't in your systems." with a link back to People; right after an action of this page, AC-18's message is used instead.
- **AC-3**: The list pane has the title "People" with "Add person", search (placeholder "Name, email or role"; matches name, email, or a role's display name in the systems in scope), the system filter, a count and sort row ("[n] people · Sort: Name, A to Z", n = the sum of the group counts), and the groups. The system filter is a segmented control: a suite admin gets All, VRMS, VMMS, BMS (suite wins when someone is both a suite admin and holds an admin role); an admin of two or more systems gets All plus their systems (All = everyone in their systems, once); an admin of one system gets no filter. A `?system` the viewer can't pick, or an unknown `?sort`, falls back to All and Name.
- **AC-4**: Sort options: "Name, A to Z" (default), "Last signed in" (newest first, never signed in last), "Newest first" (account made). Rows show no time unless sorted by last sign in ("Signed in [when]") or newest ("Added [date]"); otherwise the sub line is the role (with a system filter: the role in that system; in All: the roles in the viewer's systems, joined).
- **AC-5**: Groups, in order: "Needs attention", "Active", "Inactive", each with its count in mono and its own Load more (25 per page). The server puts each person in exactly one group: Needs attention if Locked, Pending (setup pending) or Pending deletion (on an active account); else Inactive if deactivated; else Active (including email not verified). A locked or pending account that is also deactivated is Inactive. An empty group is hidden. When all three are empty after a search or filter, spec 0016's no match state shows ("No one matches "[q]"", one hint, the active filters as removable chips with Clear all); an empty list with no search shows the empty state with "Add person".
- **AC-6**: Each row shows the round initials tile (no photo), the name, the sub line, and a mono code chip per system the person is in (built from `roles[].system` and `otherSystems`), filled for systems the viewer admins (suite admin: all), outlined for the others. A Pending person's tile is outlined.

*Person pane*
- **AC-7**: The header shows the round initials tile, the name in `text-title`, one status pill, and the role line ("[Role] in [first system], plus [n] more system(s)" in VRMS, VMMS, BMS order, role labels from the catalog; "No access to any system" for a person with no role). Pill, first that applies: "Deleted, restorable until [date]" (error), Pending deletion (warning), Inactive (muted), Locked (error), Pending (navy), Active (success). Email not verified shows Active, and the Sign in card says "Not verified".
- **AC-8**: Header buttons by status, as on `People8`: Pending shows "Resend invite" (sends the setup code), Locked shows "Unlock account", deleted in grace shows "Restore" (suite admins only; a deleted account shows nothing else); then "Edit details" (outline) and the ⋮ menu "More account actions": Send reset code (Send setup code while Pending), End all sessions, Deactivate or Reactivate, Delete account (destructive, last). Hidden: End all sessions, Deactivate and Delete on yourself; Deactivate and Delete on a suite admin (`IS_SUITE_ADMIN`); every action that needs a system on a person with no role (only Delete and Restore stay, AC-17). For a system admin, Delete on an account shared with a system they don't admin shows disabled with "Shared with [system]" (only a suite admin deletes a shared account). An action on an admin elsewhere asks for the viewer's password through the existing `ReauthDialog` (`POST /auth/admin/verify-password`, purpose `ADMIN_ACTION`, then `reauthToken`).
- **AC-9**: Under the header a facts strip shows Email, Last signed in ("Never" if never), Account made, Added by (the creator's name, or "—" when there is none).
- **AC-10**: The tabs are Overview, Access, Signed in devices, Activity (spec 0016 tabs), Overview first. Overview shows, as on `People8`: the Access card (one row per system: code chip, role label, "Until [date]" on temporary access, "No access to [systems]" under it, and "Change" which opens the Access tab), the Sign in card, and Recent activity (5 newest, "See all" opens the Activity tab).
- **AC-11**: The Sign in card shows Password ("Set", "Not set yet", "Locked"), Email ("Verified" or "Not verified"), Signed in devices (the same count as the devices tab, or "None"), and "Wrong passwords, last 30 days" (count of failed sign ins and lockouts, account wide). For a Pending person: Password "Not set yet", Email "Not verified", and "Setup code" "Ends [date]" or "Expired" (nothing when no code exists), with "Resend invite" as the card action.
- **AC-12**: The Access tab lists the systems as rows in VRMS, VMMS, BMS order, as on `People4`: for a system the viewer admins and the person is in: the role label, "Until [date]" when temporary, and "Change role"; for a system the viewer admins and the person is not in: "No access" and "Give access" (dashed); for a system the person is in that the viewer doesn't admin: the role label, "Managed by the [system] admin", no button. A suite admin sees all three systems; a system admin sees their own systems plus the person's other systems. Change role is hidden on your own page (`SELF_ROLE`), on a temporary row (it shows "Ends by itself · Temporary access" linking to the Temporary access page), and Change role and Give access are hidden on a suite admin (`SUITE_ADMIN_NO_ROLES`).
- **AC-13**: "Change role" opens a dialog "Change role in [system]" with the system's catalog roles as a single choice and Save ("Saving…" while it works); it replaces all the person's roles in that system with the one chosen, and when they hold two it says "This replaces [Role A] and [Role B]." Giving an admin role asks for the password first (AC-8's step). "Remove from [system]" (destructive) sits in the same dialog; when that system is the person's only access it is disabled with "This is their only access. Deactivate them instead." Errors show inline: 409 `LAST_ADMIN` "[Name] is the last active admin of [system]. Make someone else admin first.", 409 `TEMPORARY_ROLE` "This role is temporary and ends by itself.", 409 `ROLE_LIMIT` with the server's message. Success shows a toast and the row updates.
- **AC-14**: "Give access" and "Add person" open the Add person dialog AA ("Add a person", steps "1. Who", "2. Access", "3. Check and send"). From Give access it opens on step 2 with the person and system set and sends `POST /auth/admin/users` with `system`, the person's `email` and `attachExisting: true` plus the chosen role (field names as in `AdminCreateUserDto`); step 3 reads "[Name] gets [role] in [system]." and the toast "[Name] now has [role] in [system]." From Add person it starts at step 1, which searches existing accounts through `GET /auth/admin/users/lookup` (accounts outside the system) or takes a new name and email; someone already in the system shows "Already in [system]" with "Open person". There is no end date step.
- **AC-15**: Signed in devices shows today's sessions list (device, web or mobile app, systems, last active) with "End all sessions"; for a person with no role it shows "No sessions to show". Activity shows the person's events from every system the viewer admins (suite admins: all), newest first, each with its system code, with a filter of All plus the viewer's systems (suite: all three), using today's activity list and Load more; the type and date filters are not shown.
- **AC-16**: Account wide actions send, as `system`, the first system in VRMS, VMMS, BMS order that the person is in and the viewer admins (suite admins: the first system the person is in); the viewer never picks it. Delete and Restore by a suite admin send no system. Name and contact edits don't depend on the system sent; an email change and Delete follow the server's per system rules for the system sent (`assertNotAdminElsewhere`, `assertNotShared`), which AC-8 and AC-13 surface.
- **AC-17**: A person with no role (suite admins only) shows the header, "No access to VRMS, VMMS or BMS" in Access with "Give access" on each row, "No sessions to show", Activity, and Delete or Restore. Deleted people in their grace period are never in the list (as today); a suite admin reaches one from Deletion requests or a link, and sees the deleted pill and Restore. System admins never see deleted people.
- **AC-18**: After any action the person and the list refresh (once, after the action settles), and `me` is fetched again after a role change. If the server answers 404 or 409 because someone else changed the person, the page shows their current state with the toast "[Name] changed while you were here. Showing the latest.". If after this page's own action the person is no longer in the viewer's systems (404), the page goes back to the list with the toast "[Name] is no longer in your systems.".

*welinc-auth*
- **AC-19**: `GET /auth/admin/users`, `GET /auth/admin/users/:id` and `GET /auth/admin/users/:id/activity`: leaving out `system` means "every system you admin" for every admin, read at request time from the caller's standing (a suite admin: the whole suite, as today, even if they also hold admin roles). A system admin then gets only people holding a role in one of their systems (anyone else, including someone whose only roles are elsewhere, is 404), with every role of the person (all systems) and `otherSystems` empty; activity covers events tagged with one of the caller's systems plus account wide events, and the login client shows on rows tagged with any of the caller's systems. A soft deleted person is 404 for a system admin and found for a suite admin (as today). Passing `system` behaves exactly as today. Writes are unchanged and still require `system`.
- **AC-20**: `GET /auth/admin/users` takes `group` (`attention`, `active`, `inactive`, AC-5's rules), `sort` (`name`, default; `lastSignedIn`; `newest`), `status` (a single value as today, or a comma list read as any of), and `q` also matching role display names. With `group` set, the answer adds `counts: { attention, active, inactive }` (same `q` and `system` filter). Keyset cursors carry the sort and the filters; a cursor used with another sort or filter is 400 `INVALID_CURSOR`. Orders: `name ASC, id ASC`; `last_signed_in_at DESC NULLS LAST, id ASC`; `created_at DESC, id ASC`. Default `limit` stays 50; the portal asks 25.
- **AC-21**: Every `roles[]` entry gains `temporaryUntil` (ISO or null); the person level `temporaryUntil` is the latest of the returned roles. Items and the person answer carry `lastSignedInAt` (ISO or null) and `createdAt`. The person answer also carries `addedBy` (`{ id, name }`, null when the creator is the person, unknown, or erased), `failedSignIns30d` (count of `SIGN_IN_FAILED` and `LOCKED_OUT` events in the last 30 days, all systems), `sessionCount` (live sessions by the same rule as the sessions list), `setupCodeExpiresAt` (the newest unused setup code's expiry, even if past; null when none) and `restorableUntil` (`deletedAt` plus the erasure grace period, null when not deleted). These answer in parallel.
- **AC-22**: `users.last_signed_in_at` (`timestamptz(3)`, nullable) with a `DESC NULLS LAST, id` index is set to the sign in time at the two sign in sites that record `SIGNED_IN` (the web sign in and the code exchange in `session.service.ts`), in the same transaction, only moving forward; a token refresh or `SYSTEM_OPENED` never moves it. The migration backfills it from each account's newest kept `SIGNED_IN` event (older sign ins removed by event retention stay null).

*Quality*
- **AC-23**: The page reads well at 375px and 1280px, every control is reachable by keyboard with spec 0016's focus ring, and one axe pass shows no violations. `npm run lint`, `npm run typecheck`, `npm run build:local` and the tests pass in the portal; `npm run lint`, the build, the tests and `npm run openapi:check` pass in welinc-auth; `node scripts/check-contract-routes.mjs` passes after the OpenAPI file is regenerated.
- **AC-24**: The built page matches its boards in structure, wording and the spec 0016 token values, checked by the board comparison in `verify.md`; the only allowed differences are the four listed there.

## Decision

**Chosen option**: Option 2: build the approved `People8` page (person shown whole, systems as Access rows), with one read scope rule added to welinc-auth.

The person page stops being "a person inside one system": systems become rows, the list and the person sit side by side, and welinc-auth answers "every system you admin" when no system is given.

**Implementation skills**: `nestjs-best-practices` (`.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`.claude/skills/prisma-client-api/`) · `prisma-cli` (`.claude/skills/prisma-cli/`) · `shadcn` (`.claude/skills/shadcn/`) · `react-hook-form` (`.claude/skills/react-hook-form/`) · `ask-sonner` (`.claude/skills/ask-sonner/`)

## Feature design

**Data model sketch** (welinc-auth only; the portal stores nothing new):
- `users.last_signed_in_at` `timestamptz(3)` (milliseconds, so a cursor round trip through JavaScript never loses precision), nullable, `@map("last_signed_in_at")`. Index in the migration SQL: `(last_signed_in_at DESC NULLS LAST, id)`.
- `users.created_at` goes from `timestamptz(6)` to `timestamptz(3)` (amended 2026-11-23, during `/develop`), in its own migration (`20261123000100_users_created_at_ms`): the "Newest first" cursor goes through JavaScript, which keeps milliseconds only, so at microseconds a cursor could skip people made in the same millisecond. Existing values round by under a millisecond; changing a column type fires no row trigger, so the directory feed writes nothing. It gets no index (the suite is small; revisit past a few thousand people).
- No other table changes.

**Scope shape** (welinc-auth): `AccountScope` carries `systems: SystemType[] | null` instead of one `system`: one system given is a list of one, a suite admin with no system is `null`, a system admin with no system is their `adminOf` at request time. `assertInScope`, `mapScopedUser`, `listPeople`, `getPerson` and the activity service's `listForUser` take that shape ("a role in any of `systems`"; null = everyone). `otherSystems` fills only when `systems` has one entry (today's shape). Only the three read routes accept a list longer than one; write routes keep `systemScope` and a required `system`.

**API surface** (all under the portal cookie session and `AdminSessionGuard`; the bearer `/auth/users*` routes used by VMMS and BMS are untouched):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/admin/users` | GET | `system?`, `q?`, `group?`, `status?` (one or a comma list), `role?` (needs `system`), `sort?`, `cursor?`, `limit?` | `{ items, next, counts? }`; items gain `lastSignedInAt`, `createdAt`, per role `temporaryUntil` | admin of `system`; no `system`: any admin (their systems) or suite admin | 400 `INVALID_CURSOR`, `UNKNOWN_ROLE`, `VALIDATION_FAILED`; 403 `NOT_ADMIN_OF_SYSTEM` |
| `/auth/admin/users/:id` | GET | `system?` | the person; gains AC-21's fields | same | 404 outside scope, erased, or deleted for a system admin; 403 `NOT_ADMIN_OF_SYSTEM` |
| `/auth/admin/users/:id/activity` | GET | `system?`, the section 10 filters | events, newest first | same | 404 outside scope |
| Every other `/auth/admin/users*` route | as today | `system` as today (the portal sends AC-16's system) | as today | as today | as today |

Contract 0001: an additive amendment (no version bump: a former 400 now answers 200, and every former answer keeps its meaning). Step 7 edits section 10a's People list sentence ("sorted by name"), the rule that a system admin gets 400 when `system` is missing, and the section 16 route index rows for the three routes, plus the new fields.

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| List rows | name, status, group | `users` row; `group` decided by the server (AC-5) |
| List rows | code chips, filled or outlined | `roles[].system` and `otherSystems`, compared with `me.adminOf` (suite: all filled) |
| List rows | sub line role labels | `roles[]` codes mapped through the systems catalog (`useSystemsCatalog`, all three systems) |
| List rows | "Signed in [when]", "Added [date]" | `lastSignedInAt`, `createdAt` |
| Group headings and "[n] people" | counts | `counts` on the first page of each group call |
| Filter choices | All plus systems | `/auth/admin/me`: `suiteAdmin`, `adminOf` |
| Header | role line, pill | `roles` plus the catalog; AC-7's order from `deletedAt`, `pendingDeletion`, `isActive`, `isLocked`, `passwordSet` |
| Header | "restorable until [date]" | `restorableUntil` |
| Facts strip | Last signed in, Account made, Added by | `lastSignedInAt`, `createdAt`, `addedBy` |
| Sign in card | Password, Email, devices, wrong passwords, setup code | `passwordSet` and `isLocked`, `emailVerified`, `sessionCount`, `failedSignIns30d`, `setupCodeExpiresAt` |
| Access rows | role label, admin flag, "Until [date]" | `roles[]` and the catalog (`isSystemAdmin` per role), `roles[].temporaryUntil` |
| Access rows | Change role, Give access, read only, hidden cases | `me.suiteAdmin` and `me.adminOf`; `me.user.id`; `person.suiteAdmin`; `temporaryUntil` |
| Change role dialog | role choices, "only access" check | the catalog; the count of the person's systems in `roles` |
| Account actions | `system` sent | AC-16 from `roles` and `me.adminOf` |
| Delete disabled for a system admin | "Shared with [system]" | `roles` systems outside `me.adminOf` |
| Activity | events across systems, filter choices | `/users/:id/activity` without `system`; `me` |

**Key invariants**:
- A system admin can never read a person who holds no role in any system they admin, nor a deleted person (404, the same as unknown).
- Every write still names one system the caller admins; the wider scope is read only.
- Each person is in exactly one group.
- `last_signed_in_at` only moves forward (`updateMany` with `lastSignedInAt: null` or `lt` the new time), only at a sign in, in the same transaction as the `SIGNED_IN` event. It isn't in the directory snapshot and the trigger ignores `updated_at`, so a sign in writes no `directory_changes` row; no trigger change is needed.
- The UI never decides permissions: buttons follow `me` and the person, the server enforces.

**Security model**: suite admins as today (spec 0013 AC-17). A system admin, for people already in one of their systems, now also sees: role labels in the person's other systems (today only their codes), `lastSignedInAt` and `failedSignIns30d` across all systems, and the creator in `addedBy` (event rows already show actor names). Accepted as account wide facts an admin of that person needs. Out of scope people stay 404 (no way to tell them from unknown ids). Search can only enumerate people in the caller's systems; `lookupUsers` keeps its 30 a minute limit. Reauth rules on writes are unchanged.

**Configuration required**: none (the grace period comes from the existing `ACCOUNT_ERASURE_GRACE_DAYS`).

**Critical test scenarios**:
- Happy path: `multi.admin@` opens People, sees All, VRMS, VMMS, opens `multi.lead@` from All, sees VRMS and VMMS rows with Change role and a read only BMS row, verifies **AC-3**, **AC-12**, **AC-19**.
- Dead end gone: `/admin/people/<multi.lead id>?system=BMS` as `multi.admin@` shows the whole person, verifies **AC-2**.
- No role person as the suite admin: header, Give access on three rows, "No sessions to show", only Delete in ⋮, verifies **AC-8**, **AC-17**.
- Auth: a VRMS only admin asks for a BMS only person without `system` and gets 404; with `system=BMS` gets 403; a deleted VRMS person is 404 for them, verifies **AC-19**.
- Change role: to Admin asks for the password; on someone's only access "Remove" is disabled; the last admin gets the `LAST_ADMIN` message; a temporary row has no Change role, verifies **AC-12**, **AC-13**.
- Groups: an active person with a pending deletion appears once, in Needs attention; counts match after Load more, verifies **AC-5**, **AC-20**.
- Paging: Last signed in across a page boundary with ties and into the never signed in block, and a cursor reused with another sort answers 400, verifies **AC-4**, **AC-20**.
- Sign in sites: a web sign in and a mobile code exchange each move `last_signed_in_at`; a refresh doesn't, verifies **AC-22**.
- Concurrent change: another admin deactivates the person while the page is open; the next action shows the latest state with the toast, verifies **AC-18**.
- Deleted person as a suite admin, from Deletion requests: pill with the date and Restore, verifies **AC-7**, **AC-17**.

## Build plan

The welinc-auth steps (1 to 3) don't need S18 and can ship first. The portal steps (4 to 8) start after S18's milestones 1 to 3 (tokens and fonts, base components, `PageHeader`, `InitialsTile`, `RoleChip`, the sidebar and the app shell). Tracer Bullet inside each half.

1. [x] welinc-auth: migration for `last_signed_in_at` with its index and the backfill in SQL; the forward only write at both sign in sites with a unit test each, satisfies **AC-22**
2. [x] welinc-auth: the `systems` scope shape on the three read routes (person, activity, list), every role with per role `temporaryUntil`, AC-21's person fields, tests for each scope rule, satisfies **AC-19**, **AC-21**
3. [x] welinc-auth: `group` with `counts`, `sort` with keyset cursors that carry sort and filters, `status` lists, `q` on role labels; then the contract 0001 amendment, regenerated `docs/openapi.json`, `check-contract-routes.mjs`, satisfies **AC-20**, **AC-23**
4. Portal tracer: the `People8` page on the app shell with the list (Name sort, All filter, one group) and the person pane (header, facts strip, Overview's Access card) for `multi.admin@`; routes, deep links, `?system` handling, satisfies **AC-1**, **AC-2**, **AC-7**, **AC-9**, **AC-10**
5. Access tab with the three row kinds and hidden cases, the Change role dialog with its messages, and the AA dialog (replacing `AddPersonPage`) for Give access and Add person, satisfies **AC-12**, **AC-13**, **AC-14**, **AC-17**
6. Header actions by status, the ⋮ menu with its hidden and disabled cases, AC-16's system rule, reauth, the Sign in card, Signed in devices and Activity tabs, refresh and conflict handling, satisfies **AC-8**, **AC-11**, **AC-15**, **AC-16**, **AC-18**
7. The full list pane: three groups with counts and Load more, sorts, search, filters per admin kind, code chips, no match and empty states, phones as separate screens; retire `PeopleView`, `PersonPage` and `AddPersonPage`, and repoint their callers (`adminViews.ts`, the `AdminShell` nav, the Overview and Suite admins pages' person links), satisfies **AC-3**, **AC-4**, **AC-5**, **AC-6**
8. Sweep: 375px and 1280px, keyboard, axe, lint, typecheck, builds, tests, and the board comparison, satisfies **AC-23**, **AC-24**

## Migration plan

**Strategy**: strangler, two deploys.
**Phases**:
1. welinc-auth (steps 1 to 3): the column with its backfill inside the migration, `created_at` at milliseconds (a second migration), the wider read scope, `group`, `sort`, the new fields, the contract amendment. Additive only: today's portal, VMMS and BMS keep working unchanged.
2. Portal (steps 4 to 8): the new People page replaces `PeopleView`, `PersonPage` and `AddPersonPage` in one PR, with the spec 0013 deep links kept.
**Rollback**: revert the portal PR to bring the old pages back (they still work against the new auth); the welinc-auth changes can stay, or revert them too (the column is nullable and nothing else reads it).
**Risks**: the backfill scans `account_events` per account (fine at the suite's size; deploy outside a defense window, spec 0008's freeze rule); a missed sign in site leaves the column stale, which the per site tests catch.

## Consequences

**Positive**:
- The dead end is gone by design, not patched: nothing on the page depends on choosing a system.
- Admins of two systems get one list and one page, which the old per system screens never gave them.
- People, Roles (S20) and custom roles (S21) share one app shell pattern.
- One `systems` scope shape replaces the single system everywhere, so no third scope kind to maintain.

**Negative / tradeoffs**:
- A large portal change (list, person, Add person dialog) that waits on S18's shell, so S19's page can't ship before S18's milestone 3.
- System admins see a little more about people in their systems (security model above).
- Three group calls per page load (with counts) instead of one; fine at the suite's size.
- Restore stays a suite admin action reached from Deletion requests, as today.

**Neutral**:
- Two small migrations in welinc-auth; the column stays nullable, and accounts whose sign ins were pruned by event retention start as "Never". `created_at` keeps milliseconds from now on; nothing reads its microseconds.
- The account wide actions keep sending one system behind the scenes (AC-16).

## Follow-up

- [ ] `/sync` updates the welinc-auth `AGENTS.md` convention "admin user endpoints … list each user's roles for that system only, plus `otherSystems`" to name the wider read scope on the three routes.
- [ ] Decide in S21 whether custom roles show differently in the Access row (spec 0016: filled built in, outlined custom role chips).

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
