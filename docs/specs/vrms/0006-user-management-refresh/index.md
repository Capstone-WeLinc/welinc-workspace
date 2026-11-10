# 0006. User management as a status first list, with emailed reset codes

**Date**: 2026-10-25
**Status**: In Progress
**Updated**: 2026-11-11 (staleness sweep). The route guard is `RequirePermission keys={['users.manage']}` (spec 0011). The table has Name, Email, Work (feature 57), Role, Status and Added. Deactivating someone with open work uses spec 0011's release flow (AC-32, AC-33: "Move them back to the queue" or "Keep them assigned", through `open-work` and `release-tickets`), not AC-16's "Reassign {name}'s work first" block, and the confirm reads "Their history stays.". The VRMS database holds no users: the backend reads `email` from `Mechanic.email`, not a linked VRMS user (AC-23).

## Summary

This spec rebuilds the Users page (`/users`) on the spec 0001 components, for scope feature 14. Users list with the accounts that need you on top (locked, then setup pending), clickable count tiles, filters kept in the address, and create and edit in a dialog. Reset password stops setting everyone to a shared `Password123!` and instead emails the user a one time code through the existing forgot password flow. Deactivating a mechanic who still has open tickets is blocked until the work is reassigned, which needs one small, additive field in welinc-backend-vrms; welinc-auth is not changed.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As an admin, I want locked accounts and unfinished setups at the top of the list, so that I fix what stops people from working first.
- As an admin, I want to send a user a reset code instead of a shared default password, so that nobody but the user ever knows their password.
- As an admin, I want to be stopped from deactivating a mechanic who still holds open tickets, so that no repair is left with someone who can't sign in.
- As an admin, I want to add or edit a user in a dialog with errors under each field, so that I can fix a typo without losing what I entered.
- As an admin on a phone, I want the list as cards and the form as a bottom sheet, so that I can unlock someone from the yard.

**Acceptance criteria**:

*Page and list*

- **AC-1**: `/users` stays admin only through the existing `RequireRole role="ADMIN"` route guard and the server's `@Roles(ADMIN)`. The in page `isAdmin` check and its "Access Denied" card are deleted (the guard already covers it). The `PageHeader` reads "Users" with the `Users` icon and the subtitle "Manage who can sign in to VRMS and what they can do." Its `action` slot holds a primary "New user" button (`UserPlus` icon).
- **AC-2**: Every user has one derived account status from `getAccountStatus(user)` in `features/user-management/lib/accountStatus.ts`, checked in this order: `INACTIVE` when `!isActive`, else `LOCKED` when `isLocked`, else `SETUP_PENDING` when `!emailVerified`, else `ACTIVE`. Labels: "Inactive", "Locked", "Setup pending", "Active". `StatusBadge` and `statusLabels` gain `SETUP_PENDING` (pending colors). `PENDING_VERIFICATION` is removed from both and from the `/dev/ui` showcase list, since this page was its only user.
- **AC-3**: Above the table, four `KpiCard` tiles in this order: **Locked** (`Lock`, `destructive` tone), **Setup pending** (`MailWarning`, `highlight`), **Active** (`UserCheck`, `success`), **Inactive** (`UserX`, `default`). Each count is over all loaded users, not the filtered set. Each tile is a toggle: pressing it sets the status filter to that status, and pressing the selected tile clears the status filter. `KpiCard` gains two optional props, `onSelect` and `selected`; without `onSelect` it renders exactly as today. With `onSelect`, the whole card is one `<button type="button">` (block, `text-left`, full card size, at least 44px tall, the standard focus ring) with `aria-pressed={selected}` and the accessible name "{caption}, {count}" (for example "Locked, 3"); the selected one shows a `ring-2 ring-ring` outline. A pressed tile whose count is 0 still filters, and the table shows the "no match" empty state (AC-7). Two tiles per row on a phone, four across from 1024px.
- **AC-4**: Search, role, status and page live in the URL as `?q=&role=&status=&page=`, read and written by `features/user-management/lib/userFilters.ts` (same pattern as `repairListFilters.ts`). `role` accepts `ADMIN` or `MECHANIC`, `status` accepts the four AC-2 values, and `page` accepts a whole number of 1 or more; anything else reads as "all" or page 1. Search is a text `Input` (`Search` icon, placeholder "Search by name or email", `maxLength` 100) matching the trimmed text, ignoring case, anywhere in the name or email. As in `useRepairListFilters`, the typed text is local state and only the debounced value (300ms) is written to `q`; a `q` over 100 characters is cut to 100 when read. Role ("All roles", "Admin", "Mechanic") and status ("All statuses" plus the four labels) are `Select`s. Each change writes the URL with `replace` and resets the page to 1 inside the `onChange`. A "Clear filters" button shows while any filter is set and clears all three. Nothing writes the URL while a dialog or `confirm()` is open: `ConfirmProvider` cancels every open prompt on any `location.search` change, so a URL write there would silently answer it "no".
- **AC-5**: The list is sorted by status rank (Locked 0, Setup pending 1, Active 2, Inactive 3), then by name (`localeCompare`, `sensitivity: 'base'`), then by email.
- **AC-6**: The list is the shared `DataTable` (label "Users"), paginated in the browser at 20 rows per page with its `Pagination` shown only when there is more than one page. A `page` past the last page shows the last page; the URL is not rewritten. A row that moves after an action (it sorts again) does not change the current page. Columns: **User** (name in `font-medium`, email under it in `text-muted-foreground`, plus a "You" badge on your own row; phone card `title` is the name, `subtitle` the email), **Role** (`RoleBadge` of the user's first VRMS role assignment, plus a "+{n}" `Badge` when they hold more than one VRMS role; phone `field`), **Status** (`StatusBadge` of AC-2; phone `badge`), **Added** (`formatShortDate(createdAt)`; phone `hidden`). Clicking or tapping a row opens the edit dialog (AC-11). The `rowActions` menu follows AC-9.
- **AC-7**: States. On first load only, the tiles show `Skeleton`s their size and the table uses its `loading` state. On a first load failure, the table shows its `ErrorState` with `getApiErrorMessage(err, "Couldn't load users.")` and Try again, and the tiles are hidden (only on error, not when empty). `DataTable` takes one `empty` object, so the page picks it: with no users at all, title "No users yet", description "Add the first admin or mechanic.", and a "New user" action; with filters that match nobody, "No users match these filters", with a "Clear filters" action.
- **AC-8**: The list refetches quietly when the tab becomes visible again (`visibilitychange`, as in `useRepairList`). During a background refetch the rows and tiles stay on screen with no skeleton. `useUsers` numbers each list request and drops any result older than the latest, and it skips a background refetch while a row action (AC-9) or a save (AC-13) is in flight, so a refetch can never overwrite a row just replaced by an action. A failed background refetch keeps the last rows and shows the error toast "Couldn't refresh users." once per run of failures; the next successful load resets it. Every action replaces its row from the server's response; a create inserts the returned user and the list sorts again.

*Row actions*

- **AC-9**: Each row's actions menu shows, in this order:
  - **Edit** (every row).
  - The reset action, named by status: **Send reset code** (Active), **Resend setup code** (Setup pending), **Unlock and send reset code** (Locked). Inactive rows have none.
  - **Unlock** (Locked only).
  - **Deactivate** (`destructive`; every status except Inactive, and never on your own row) or **Reactivate** (Inactive).

  While an action for a row is in flight (from its confirm to its last response), selecting any action on that row except Edit does nothing.

  Focus: the menu item that started an action unmounts, so `confirm()` and the dialog cannot hand focus back to it. When an action or the edit dialog ends, focus goes to that row's actions trigger if the row is still on the current page, otherwise to the table's search input. The dialog gets this through its `finalFocusRef`; for `confirm()` the page focuses the target after the promise settles. "New user" passes its own button as `finalFocusRef`. The shared `DataTable` gains an optional `rowActionsLabel(row)` prop (default stays "Row actions"), and this page passes "Actions for {name}" so each trigger has its own name.

*Create and edit*

- **AC-10**: "New user" opens a `ResponsiveDialog` titled "New user", described as "They'll get an email with a code to set their password." The form is react-hook-form with one zod schema (`zodResolver`) and the shadcn `Field` parts, mode `onTouched`. Fields:
  - **Name**: `Input`, required, 1 to 100 characters after trimming ("Enter their name." / "Keep it to 100 characters.").
  - **Email**: `Input type="email"`, required, a valid email format after trimming, up to 255 characters ("Enter their email." / "Enter a valid email address."). It is trimmed and lowercased only in the submit handler, so the text never changes under you while typing. Helper: "This is their sign in." No company domain rule on the client. (The 100 and 255 limits match the database columns; the server DTOs don't check length.)
  - **Role**: single choice `ToggleGroup` (Admin, Mechanic), default Mechanic, never empty (`onValueChange={(v) => v && field.onChange(v)}`).

  There is no password field and no active checkbox. The buttons are "Create user" (primary) and "Cancel". The request is `createUser({ name, email, roleAssignments: [{ role, system: 'VRMS' }] })`, with no `password` and no `isActive`, so the server emails the setup code. On success the dialog closes and the toast reads "{name} added. A setup code was sent to {email}." welinc-auth saves the user before it sends the mail, and a mail failure comes back as a 5xx with the user already saved. So on a create 5xx or network error, the page refetches the list first: if a user with that email now exists, the dialog closes, the row is shown, and the error toast reads "{name} was added, but the setup email couldn't be sent. Use Resend setup code." (Resend setup code, AC-19, is the recovery.) Otherwise AC-13 applies.
- **AC-11**: Edit opens the same dialog titled "Edit {name}" with no description, prefilled from a snapshot of the row taken when it opens (role from the first VRMS assignment), with buttons "Save changes" and "Cancel". The snapshot is the baseline for `isDirty` and for AC-12's "saved email"; a background refetch does not change the open form. If a refetch shows the row is gone, the dialog closes with the info toast "{name} is no longer in the list." When the user holds more than one VRMS role, or a role other than Admin or Mechanic, the Role `ToggleGroup` is disabled with the helper "This user has a role this page can't edit yet.", and `roleAssignments` is never sent, so no role is dropped. Pressing Save with no changes (`!isDirty`) closes the dialog without a request. Otherwise the request is `updateUser(id, …)` with `name`, plus `email` only when it changed, plus `roleAssignments: [{ role, system: 'VRMS' }]` only when the role changed. It never sends `password` or `isActive`. The server merges roles for other systems, so those stay. On success the dialog closes and the toast reads "{name} updated." When the edited row is your own, `authStore.user` (and the `welinc_user` copy, per the three copy rule in the web-vrms `AGENTS.md`) takes the new name and email from the response, so the header stays right.
- **AC-12**: When the trimmed, lowercased email differs from the saved one, Save first asks through `confirm()`: title "Change their sign in email?", description "{name} will sign in with {new} from now on. {old} will stop working.", confirm "Change email", cancel "Keep editing". On your own row the description adds "Use the new address the next time you sign in." Keep editing returns to the dialog with every value kept; nothing is sent.
- **AC-13**: Errors. Field errors sit under their field per `design.md`, wired with `aria-invalid` and `aria-describedby`; on a submit with errors, focus moves to the first invalid field. Server errors: a 409 sets the email field error "An account with this email already exists."; a 400 whose `getApiErrorMessage` text matches `/email domain/i` (welinc-auth's "Email domain does not exist or cannot receive mail") sets that message on the email field; any other 400 (for example a validation array, which `getApiErrorMessage` joins with ", ") and anything else shows a `FormAlert` in the dialog, "Couldn't save: {message}" (or "Couldn't save. Check your connection and try again." with no server message), and the error toast with the same text. The dialog stays open with everything kept. While saving, the primary button shows a spinner, both buttons are disabled, and the dialog ignores Escape, an overlay click and a swipe to close (its `onOpenChange` does nothing while saving). Only one save can be in flight: a `submitting` flag is set on the first Save press or Enter and covers the AC-12 prompt as well as the request, so a second press or Enter while the prompt is open does nothing and never queues a second prompt. Keep editing clears it.
- **AC-14**: Closing a dirty dialog (Cancel, Escape, an overlay click, a swipe) asks through `confirm()`: title "Discard changes?", description "What you entered will be lost.", confirm "Discard" (`tone: 'destructive'`), cancel "Keep editing". A clean dialog closes at once. The dialog stays mounted under the confirm prompt.

*Account actions*

- **AC-15**: **Deactivate** (once AC-16 allows it) asks: title "Deactivate {name}?", description "They'll be signed out and can't sign in until you reactivate them. Their tickets and history stay.", confirm "Deactivate" (`destructive`). It calls `setUserStatus(id, false)`. Toast "{name} deactivated." On failure: "Couldn't deactivate {name}: {message}."
- **AC-16**: Before the AC-15 prompt, the page fetches `getAvailableMechanics()` fresh (not a cached list) and finds every mechanic that matches this user: a mechanic whose `email`, lowercased, equals the user's email; and, only when the user has the VRMS `MECHANIC` role, a mechanic whose `email` is null and whose trimmed name equals the user's trimmed name ignoring case. If any match has `isAvailable === false` (open work means the server's `ACTIVE_STATUSES`: Pending, In progress, For verification, the same set the repair list shows), using the first such match, nothing is deactivated and `confirm()` shows: title "Reassign {name}'s work first", description "{name} still has open repair tickets. Reassign or close them, then deactivate.", confirm "Open their tickets", cancel "Close". Confirm navigates to `/repairs?mechanic={mechanic.id}`. If the fetch fails and the user has the VRMS `MECHANIC` role, the check fails closed: title "Couldn't check open work", description "We couldn't check whether {name} has open repair tickets, so they can't be deactivated yet.", confirm "Try again" (runs this check again), cancel "Close". For a user with only the `ADMIN` role, a failed fetch skips the check. No match, or matches with no open work, continues to AC-15. Accepted gaps: the endpoint lists only active in house mechanics, so a user whose `Mechanic` row is inactive, missing, or carries an old email (see Consequences) never matches and is never blocked; and a ticket assigned between the check and the deactivate is not caught.
- **AC-17**: **Reactivate** asks: title "Reactivate {name}?", with a description read from the raw fields, not the derived status: "They can sign in again with their current password." when `emailVerified`, else "They still need to set a password. Send them a setup code after reactivating."; when `isLocked`, it adds "They're still locked. Unlock them next." Confirm "Reactivate". It calls `setUserStatus(id, true)`. Toast "{name} reactivated."
- **AC-18**: **Send reset code** asks: title "Send {name} a reset code?", description "We'll email a code to {email}. It works for 10 minutes and lets them choose a new password from the sign in page. Their current password keeps working until then.", confirm "Send code". It calls a new `requestPasswordReset(email)` wrapper in `authApi.ts` (`POST /auth/forgot-password` with `{ email }`). Toast "Reset code sent to {email}." On a failure (a 5xx when mail fails, or a network error): the error toast "Couldn't send the reset code: {message}.", the row is unchanged, and you retry from the menu. Accepted: a new code does not cancel earlier unexpired codes (welinc-auth only adds codes), and the endpoint itself would also mail an inactive user (the menu never offers it for one).
- **AC-19**: **Resend setup code** is the same call, with title "Resend {name}'s setup code?", description "We'll email a new code to {email}. It works for 10 minutes.", confirm "Send code", and toast "Setup code sent to {email}."
- **AC-20**: **Unlock and send reset code** asks: title "Unlock {name} and send a reset code?", description "Their account locked after 5 failed sign ins. This unlocks it and emails a code to {email} so they can choose a new password.", confirm "Unlock and send". It calls `unlockUser(id)`, replaces the row, then calls `requestPasswordReset(email)`. If unlock fails, the error toast "Couldn't unlock {name}: {message}." shows and no code is sent. If only the send fails, the row stays unlocked and the error toast reads "{name} is unlocked, but the reset code couldn't be sent: {message}." Full success: "{name} unlocked. A reset code was sent to {email}."
- **AC-21**: **Unlock** asks: title "Unlock {name}?", description "They can sign in again with their current password.", confirm "Unlock". It calls `unlockUser(id)`. Toast "{name} unlocked."
- **AC-22**: Your own row (its `id` equals the signed in user's `id` from `authStore`) shows the "You" badge, has no Deactivate action, and in Edit its Role `ToggleGroup` is disabled with the helper "You can't change your own role." Name and email stay editable (AC-12 applies).

*Backend*

- **AC-23**: In welinc-backend-vrms, `GET /vrms/mechanics/available` adds `email: string | null` to each item, read from the linked VRMS user (`user: { select: { email: true } }`), null when the mechanic has no linked user. The existing fields, order, filters and roles are unchanged, and the repair form keeps working. The web `MechanicOption` type gains `email?: string | null`. No migration.

*Cleanup and quality*

- **AC-24**: The fixed `Password123!` and the `resetUserPassword` wrapper are deleted (nothing else calls `PATCH /auth/users/:id/password`). `UserForm.tsx`, `UsersTable.tsx` and `useUsersManager.ts` are replaced. `validatePassword` moves to `features/auth/lib/passwordRules.ts`, and `profileSchemas.ts` imports it from there. `validateEmail` and `getVrmsRoleAssignments` are replaced by the zod schema and a helper in `features/user-management/lib/`. A grep for `Password123` and `user-management/hooks/useUsersManager` returns nothing.
- **AC-25**: `UsersPage` and everything it renders use only spec 0001 components and theme tokens: no inline `style`, no legacy classes (`card`, `input`, `select`, `tag-pill`, `section-heading`, `dashboard-grid`, `summary-card`, `sidebar-btn` and the like), no `LegacyButton`, no hex values. Inputs use `text-base` on phones, and tap targets are at least 44px. Everything works with the keyboard alone. At 375px and 1280px there is no horizontal scroll, and axe reports no serious or critical issues on `/users`, including with the create dialog open.
- **AC-26**: `npm run lint`, `npm run typecheck` and `npm run build` pass in welinc-web-vrms; `npm run lint`, `npm run build` and `npm run test` pass in welinc-backend-vrms. welinc-auth is not changed.

## Decision

**Chosen option**: Option 2: Rebuild the page on the design system, with reset by emailed code and an open work check

The page is rebuilt as a status sorted `DataTable` with URL filters, selectable tiles and a react-hook-form dialog. Reset reuses the public forgot password endpoint instead of setting a known password. Deactivate is gated on a fresh open work check that matches users to mechanics by email, which is the only key the two databases share.

**Implementation skills**: `shadcn` (`shadcn-ui/ui`, `.claude/skills/shadcn/`, `ToggleGroup`, `Field`, `Select`) · `react-hook-form` (`.claude/skills/react-hook-form/`, the schema and dialog form) · `vercel-react-best-practices` (`vercel-labs/agent-skills`, `.claude/skills/vercel-react-best-practices/`) · `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) and `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`) for the one select change

**Calls made in this spec** (each with the runner up):
- **Fetch the mechanics list at Deactivate time**, not with the page. Assignments change from other screens, and one request per deactivate is cheap. Runner up: load it with the page and refetch on focus, which can be stale at the moment that matters.
- **Extend `KpiCard` with `onSelect` and `selected`** instead of wrapping it in a button per page. The dashboard can reuse it later. Runner up: a local wrapper in this feature.
- **Page size 20, paginated in the browser.** The server returns every VRMS user in one call and the list is in the tens. Runner up: 10 per page as today, which pushes locked users off page 1 less often but means more paging.
- **Keep a separate Unlock** next to "Unlock and send reset code", for a user who remembers their password and only tripped the lock. Runner up: only the combined action.
- **Last write wins on concurrent edits.** welinc-auth users carry no version field, and two admins editing one user at once is rare. Runner up: compare `updatedAt` on the client before saving, which is racy without server support.
- **Treat a 400 as an email field error only when its message mentions the domain**, because that is the one 400 welinc-auth returns for a well formed form. Runner up: send every 400 to the `FormAlert`.

## Feature design

**Data model**: no schema change in either database. Read from welinc-auth: `id`, `name`, `email`, `emailVerified`, `isActive`, `isLocked` (derived by the server from `lockedAt`), `createdAt`, `roles[]`. Read from welinc-backend-vrms: `Mechanic.id`, `name`, `isAvailable`, and the new `email` through the existing `Mechanic.user` relation.

**Account status** (derived, never stored): `INACTIVE > LOCKED > SETUP_PENDING > ACTIVE`, the first that applies (AC-2). It changes only through the server: Deactivate and Reactivate flip `isActive`; Unlock clears the lock; completing a reset or setup code sets `emailVerified`; 5 failed sign ins lock.

**API surface** (all through the axios instance; the gateway sends `/auth/*` to welinc-auth and `/vrms/*` to welinc-backend-vrms):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/users?system=VRMS` | GET | | `ManagedUser[]` | bearer, ADMIN | 401, 403 |
| `/auth/users` | POST | `name`, `email`, `roleAssignments[]` | `ManagedUser` | bearer, ADMIN | 400 (domain, validation), 409 email exists |
| `/auth/users/:id` | PATCH | `name`, `email?`, `roleAssignments?` | `ManagedUser` | bearer, ADMIN | 400, 404, 409 |
| `/auth/users/:id/status` | PATCH | `isActive` | `ManagedUser` | bearer, ADMIN | 404 |
| `/auth/users/:id/unlock` | PATCH | | `ManagedUser` | bearer, ADMIN | 404 |
| `/auth/forgot-password` | POST | `email` | `{ message }` (always generic) | public | 400 validation, 5xx when mail fails |
| `/vrms/mechanics/available` | GET | | `{ id, name, isAvailable, email }[]` (`email` new) | bearer, ADMIN or MECHANIC | 401, 403 |

No longer called: `PATCH /auth/users/:id/password`. Never called: `DELETE /auth/users/:id`.

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| List | status badge, tile counts, sort rank | derived by `getAccountStatus` from `isActive`, `isLocked`, `emailVerified` |
| List | role badge | first `roles[]` entry with `system === 'VRMS'` |
| List | "You" badge, own row guards | `row.id === authStore.user.id` (both are the welinc-auth user id from the token) |
| List | Added date | `createdAt`, `formatShortDate` |
| List | filters and page | URL query, parsed by `userFilters.ts` |
| Create | setup email | sent by welinc-auth because `password` is omitted (1 hour code) |
| Edit | role sent | the form; only the VRMS entry, the server merges other systems |
| Edit | email change prompt | form value compared with the row's saved `email`, both trimmed and lowercased |
| Reset actions | recipient | the row's `email` |
| Reset actions | "10 minutes" text | welinc-auth forgot password expiry (fixed in its code) |
| Deactivate | open work | `isAvailable === false` on the matched mechanic from a fresh `getAvailableMechanics()` |
| Deactivate | match key | `mechanic.email` lowercased vs `user.email`; trimmed name ignoring case only when `mechanic.email` is null |
| Deactivate | "Open their tickets" target | `/repairs?mechanic={mechanic.id}` (the repair list's existing `mechanic` filter, spec 0004) |
| Unlock text | "5 failed sign ins" | welinc-auth `MAX_FAILED_ATTEMPTS` (fixed in its code) |

**Key invariants**:
- The client never sets or sends a password for another user.
- A status change happens only through a confirmed row action, never as a side effect of Save.
- You can never deactivate yourself or change your own role from this page.
- A user matched to a mechanic with open tickets is never deactivated from this page; when the check can't run, a mechanic is never deactivated (fails closed).

**Security model**: admin only (route guard plus server `@Roles(ADMIN)` on every `/auth/users` route). The forgot password endpoint is public and always answers the same generic message, so the page can't tell whether the mail went out; the toast says "sent" because the address comes from a real account. No passwords or codes pass through or are shown by the client. Self protection (AC-22) is client side only; the server still allows it (see Follow-up). Account data is personal data (names, emails), already held by welinc-auth; this spec adds no new store of it.

**Configuration required**: none.

**Critical test scenarios**:
- Create with mail down: the user is saved, the dialog closes, the toast points to Resend setup code, and a retry is never needed; verifies **AC-10**.
- Stale refetch: refocus the tab while a deactivate is in flight; the row ends Inactive; verifies **AC-8**.
- Happy path: create a mechanic, see them on top as Setup pending with the toast; resend the setup code; edit their name; verifies **AC-3**, **AC-5**, **AC-10**, **AC-11**, **AC-19**.
- Reset: a Locked user offers "Unlock and send reset code"; after it, the row reads Active or Setup pending and one forgot password request went out; verifies **AC-9**, **AC-20**.
- Open work block: deactivating a seeded mechanic with an In Progress ticket shows "Reassign … first" and sends no status request; "Open their tickets" lands on the filtered repair list; with the mechanics request failing, the prompt is "Couldn't check open work"; verifies **AC-16**.
- Email change: editing the email prompts once; Keep editing sends nothing; a duplicate email shows the 409 field error; verifies **AC-12**, **AC-13**.
- Own row: no Deactivate, role disabled; verifies **AC-22**.
- Filters: `/users?status=LOCKED&q=juan` loads filtered, the Locked tile shows pressed, Back restores the earlier view; verifies **AC-3**, **AC-4**.
- Discard: type in New user, press Escape, choose Keep editing, then Discard; verifies **AC-14**.

## Build plan

Facade first: the page and dialog on the data the endpoints already return, then the account actions, then the one backend field for the open work check.

1. **Foundations**: `accountStatus.ts` (status, rank, sort), `userFilters.ts` (URL read and write, debounced search), `SETUP_PENDING` in `StatusBadge` and `statusLabels` with `PENDING_VERIFICATION` removed, `KpiCard` `onSelect` and `selected`, `DataTable` `rowActionsLabel`, a `useUsers` hook (first load, quiet refetch on `visibilitychange`, request numbering, refetch paused during actions, row replace and insert), and the `requestPasswordReset` wrapper. Satisfies **AC-2** to **AC-5**, **AC-8**, **AC-9** (label).
2. **Page and list**: header, selectable tiles, search and filter bar, `DataTable` columns, phone cards, row click, pagination, loading, error and both empty states. Satisfies **AC-1**, **AC-3**, **AC-6**, **AC-7**, **AC-22** (badge).
3. **Create and edit dialog**: the zod schema, `ResponsiveDialog` form with `ToggleGroup` role, row snapshot, create and update payloads, the create 5xx recovery, the email change prompt, server error mapping, the `submitting` lock, discard guard, own and multi role role locks, the `authStore` update for your own row, focus return. Satisfies **AC-10** to **AC-14**, **AC-22**.
4. **Account actions**: the per status menu, in flight lock per row, focus return after each prompt, Send reset code, Resend setup code, Unlock, Unlock and send, Reactivate, Deactivate prompt. Satisfies **AC-9**, **AC-15**, **AC-17** to **AC-21**, **AC-22** (no Deactivate).
5. **Open work check**: the `email` field in `ConfigService.listAvailableMechanics` (welinc-backend-vrms, restart the container before a live check), the `MechanicOption` type, then the fresh fetch, match, block, fail closed and "Open their tickets" link. Satisfies **AC-16**, **AC-23**.
6. **Cleanup and sweep**: delete the old components, hook, `Password123!` and `resetUserPassword`; move `validatePassword`; tokens only; keyboard pass; 375px and 1280px with axe; lint, typecheck, build and tests in both repos. Satisfies **AC-24** to **AC-26**.

## Consequences

**Positive**:
- No shared known password anymore; only the user ever chooses theirs.
- The accounts that need action sit on top and are one tap away from the tiles.
- Deactivating a mechanic can't strand open tickets.
- The page joins the dashboard and repair screens on the design system, with URL filters like the repair list.

**Negative / tradeoffs**:
- Reset now depends on email delivery. With SMTP down there is no fallback on this page, and the generic reply means a failed mail can look sent.
- The open work match relies on the VRMS user's email matching welinc-auth. After an email edit here, the VRMS copy keeps the old email, so the mechanic no longer matches (and the name fallback doesn't apply, because their `email` is not null). Such a mechanic would not be blocked.
- Self protection and the open work block are client side only; another client can still do either through the API.
- A new reset code works for 10 minutes, shorter than the 1 hour setup code, so a resent setup code needs quicker action from the user.
- Breaks Facade on purpose with one additive field in welinc-backend-vrms, like specs 0003 and 0004.

**Neutral**:
- `KpiCard` gains a selectable mode other pages may adopt, and `DataTable` gains an optional per row actions label; existing callers are unchanged.
- `PENDING_VERIFICATION` leaves the shared badge vocabulary in favor of `SETUP_PENDING`.

## Follow-up

- [ ] welinc-auth (your repo, but other subsystems and the portal use it, so keep the API shapes stable; likely under feature 2): `forgotPassword` logs every OTP with `console.log`, which leaks reset codes into container logs; remove it.
- [ ] welinc-auth: the setup and reset emails link to a hardcoded `http://localhost:8000/forgot-password`; it needs a configured portal URL before deployment.
- [ ] welinc-auth: completing a reset code does not clear `lockedAt`, and forgot password sends codes to inactive users; both should be fixed server side so AC-20's two calls can become one.
- [ ] welinc-auth: no server guard against an admin deactivating themselves or removing the last admin, and no audit record of admin user changes (BRD: every edit audited). Feature 5 (permission matrix) or feature 2.
- [ ] welinc-auth: `updateUser` logs the full DTO with `console.log`.
- [ ] welinc-auth: `createUser` returns a 5xx when the setup mail fails even though the user is saved (AC-10 works around it); it should return the user and report the mail failure separately. Resent codes should also cancel older unused ones.
- [ ] Mechanics created on this page get no in house `Mechanic` row in welinc-backend-vrms, so they can't be assigned tickets; today only the seed creates those rows. Belongs with feature 2 (auth service boundary) or feature 4 (data model v2).
- [ ] The VRMS `User.email` copy does not follow email edits made here (see Consequences). Same owner as the item above.
- [ ] Chief Mechanic becomes a third Role option when feature 17 lands (Jira VRMS-42).
- [ ] UI strings move to translation files with feature 7.
