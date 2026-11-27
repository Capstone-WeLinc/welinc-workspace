# 0027. Navigation redesign: sections, sub pages with counts, top bar with switcher and account menu

**Date**: 2026-11-23
**Updated**: 2026-11-28: VRMS gets the Suite management top bar (suite spec 0019's `Shell20` and `Switcher16`). AC-8, AC-9, AC-10, AC-11, AC-12 and AC-15 are rewritten, AC-9a, AC-9b, AC-10a and AC-10b are added, and build steps 5 and 6 are added (the sweep is now step 7). Reasons in [rationale.md](rationale.md), *Update 2026-11-28*. Later on 2026-11-28 (`/architect`, the role tag source): welinc-auth adds `systemRoles` and `suiteAdmin` to the grant answer's `user`, AC-9a and the value sourcing rows are amended, and build step 6a is added. Reasons in [rationale.md](rationale.md), *Update 2026-11-28, the switcher's role source*.
**Status**: In Progress
**Scope row**: [70](../../../scope/vrms/ui-refresh.md#70-navigation-redesign--in-progress) (`docs/scope/vrms/ui-refresh.md`)
**Repos**: `welinc-web-vrms`, `welinc-backend-vrms`, `welinc-web-portal` (`AdminShell`, the launcher's `open` handoff), `welinc-auth` (one field on `/auth/admin/me`; `systemRoles` and `suiteAdmin` on the grant answer's `user`)
**Design source**: board `Sidebars8` for the nav (canvas "WeLinc design directions", https://claude.ai/artifact/VFhLSMNhfpAFD4D4c2VQzp, page "Round 8"), with round 1's `BPhone` for the phone; copies in [boards/](boards/). The top bar, sidebar title, footer strip, switcher and account menu follow suite spec 0019's boards `Shell20` and `Switcher16` ([copies](../../_root/0019-portal-redesign/boards/)) **as the portal built them**, so both apps match each other. The look, the collapse and the phone rule come from suite spec [0016](../../_root/0016-design-direction-refresh/index.md) *Layout and navigation* (amended 2026-11-28 by this spec); this spec decides what goes in the sidebar and the top bar.

## Summary

Spec 0016 settles how the sidebar looks; this spec settles what is in it and around it. VRMS gets the sections Work, Insights and Admin (no Fleet, because VMMS owns the trucks). Repair tickets and Knowledge base open into sub pages with live counts, gold when the count waits on you. Since 2026-11-28 VRMS uses the same frame as Suite management: a white top bar with the breadcrumb on the left and the grid switcher and avatar menu on the right, a sidebar that starts with "VRMS" and your role and ends with the "WeLinc Logistics" strip and the collapse button. New repair stays at the top of the sidebar. The notifications bell (feature 28) will go in the top bar, left of the grid. The portal takes back the `Shell20` frame it had and keeps the Deletion requests count.

## Requirements

**User stories**:
- As a chief mechanic, I want to see how many tickets wait for my sign off from any page, so that I don't miss them.
- As a mechanic, I want my tickets split into In progress, Sent back to me and Done, with a gold count on what was sent back, so that I know what needs me first.
- As an admin, I want New repair always one click away, so that a truck coming in gets a ticket fast.
- As someone in VRMS and VMMS, I want to switch systems from the top bar, the same place as in Suite management, so that I don't go through the portal by hand.

**Acceptance criteria**:

*Sections and pages (web-vrms)*
- **AC-1**: The sidebar sections, in order, each page shown only with its key (as `navItems.ts` does today): an unlabelled first section with Dashboard (`LayoutDashboard`; "My dashboard" without `ticket.view_all`); **Work**: Repair tickets (`Wrench`; "My repairs" without `ticket.view_all`; needs `ticket.view` or `ticket.view_all`), Repair history (`History`); **Insights**: Analytics (`BarChart2`, `analytics.view`), Knowledge base (`BookOpen`, `knowledge.view`); **Admin**: Users (`Users`, `team.manage`), Audit logs (`ScrollText`, `audit.view`), Settings (`Settings` cog, any settings key, no dropdown). An empty section is hidden. Section labels don't fold and a `sidebar-line` separates sections (spec 0016). Profile and New repair are no longer nav items. There is no Fleet section and no Inbox.
- **AC-2**: Repair tickets has sub pages. With `ticket.view_all`: "All open" (`/repairs?view=open`: every status except Closed and Cancelled, the existing open rule in `ticket-statuses.ts`), "Waiting for sign off" (`view=signoff`: For verification tickets the viewer may verify, so tickets they are assigned to are left out, matching spec 0014's rule that nobody verifies their own work), and "Assigned to me" (`view=mine`: the viewer's open tickets; only when the viewer is an assignable roster member, suite spec 0018 child 0002, AC-33). Without it (My repairs): "In progress" (`view=active`: the viewer's tickets in Assigned, In progress or On hold), "Sent back to me" (`view=sentBack`: the viewer's In progress tickets whose `sentBackAt` is set), "Done" (`view=done`: the viewer's Closed tickets; Cancelled ones are left out). "The viewer's tickets" means tickets they are assigned to. Knowledge base has "Guides" (`/knowledge-base`) and, with `knowledge.edit`, "Suggestions" (`/knowledge-base/suggestions`). "On hold" waits for feature 31.
- **AC-3**: A page with sub pages opens and closes on click of its chevron or name; clicking the name also goes to its first sub page. It opens by itself when the current route is one of its sub pages, and stays as you left it otherwise (kept per user in `localStorage` under `welinc:nav-open:<user id>` as a JSON array of parent paths such as `["/repairs"]`; unknown or no longer visible paths are ignored, and a read or write that throws is ignored). The current sub page uses `sidebar-current`; the parent then shows as idle. On a ticket (`/repairs/:id`) nothing under Repair tickets is current, and Repair tickets is.
- **AC-4**: `view` is a preset of the existing repair list: `useRepairListFilters` reads it, the list's other filters and search apply on top, choosing another status chip clears `view`, and the page header title follows it ("Waiting for sign off"). `GET /vrms/repairs` takes `view` with the same definitions so paging and totals match the counts; an unknown `view` answers 400 `VALIDATION_FAILED`, and a `view` the caller can't use (for example `mine` outside the roster) answers 403.

*Counts*
- **AC-5**: `GET /vrms/nav/counts` returns, for the caller, only the counts of sub pages they can see: `{ open?, signoff?, mine?, active?, sentBack?, suggestions? }`, each computed exactly as its `view` (suggestions: open fix library suggestions waiting for review). The sidebar shows each as a mono bubble beside its sub page, and on a folded parent the sum of its hot counts. 0 shows no bubble; above 99 shows "99+". Repair history, Done and Guides have no count.
- **AC-6**: Hot (gold bubble with navy text), per `docs/context/vrms/design.md`'s hot list: `signoff` for viewers with `ticket.verify` (its count already leaves out their own tickets, AC-2), `sentBack` always, `suggestions` for viewers with `knowledge.edit`. Every other count uses `sidebar-count`. Collapsed, a bubble becomes an 8px dot (gold when hot) on the parent's icon.
- **AC-7**: Counts load with the shell, refresh every 60 seconds while the tab is visible, on focus when the last read is older than 15 seconds, and right after any of the viewer's own ticket moves (create, status changes, send back, verify, assign or unassign) or suggestion reviews settle. A failed count call keeps the last numbers and shows no error; after a failure on first load no bubbles show. A user with no VRMS keys gets `{}`, never an error.

*The sidebar's top and bottom, and the top bar*
- **AC-8** (amended 2026-11-28): With `ticket.create`, a full width primary "New repair" button (`Plus` icon) sits under the sidebar title (AC-10a); collapsed, it is a 40px icon button with the tooltip "New repair". It goes to `/repairs/new`. Without the key, a `sidebar-line` and 12px of space sit under the title instead (`Sidebars8` N17). On phones New repair is the primary action in the header of the Repair tickets page and the dashboard, not in the tab bar or the top bar.
- **AC-9** (rewritten 2026-11-28, `Shell20`): A white top bar sits at the top of the content column at every size, built like the portal's Suite management top bar: sticky, 64px (`h-16`), `bg-card`, a `border-border` line under it, `px-4 sm:px-6 lg:px-8`, `gap-2`. On the left the breadcrumb (`nav` labelled "Breadcrumb", `text-small`): "VRMS", then the current top level page by its nav label, then the current sub page or record, separated by a 16px `ChevronRight` in `muted-foreground`. Every crumb but the last is a link in `muted-foreground` ("VRMS" goes to `/`, a page to its own path, Repair tickets or My repairs to `/repairs` with no `view`); the last is `font-medium` `text-foreground`, carries `aria-current="page"` and truncates. Examples: "VRMS › Dashboard", "VRMS › Repair tickets › Waiting for sign off", "VRMS › My repairs › Sent back to me", "VRMS › Repair tickets › REP-20261126-7J6W", "VRMS › Repair tickets › New repair", "VRMS › Knowledge base › Suggestions", "VRMS › Profile". Below 640px only the last crumb shows; from 640px the whole trail shows, the same rule as the portal, with nothing extra between 640 and 768px. On the right, in this order: the bell's place (AC-9b), the system switcher (AC-9a) and the avatar (AC-10). Below 768px the bar also holds, before the breadcrumb, the menu button that opens the sheet (when the person gets the sheet) or the W tile linking to `/` (when they get the tab bar), as the portal's bar does. This bar replaces the phone only header (`AppHeader`); `BannerHost` renders right under it, as the portal's banner sits under its header. Its buttons and links use the light ring (`focus-visible:ring-2 focus-visible:ring-ring`); `ring-on-dark` stays in the sidebar. `PageHeader` no longer renders a breadcrumb and loses its `crumb` prop; it keeps the title, the context line and the action. A crash inside the shell keeps the top bar (spec 0025 AC-7).
- **AC-9a** (added 2026-11-28, `Switcher16`): When `canSwitchSystem` is true (spec 0007: two or more systems, or a VRMS Admin; since step 6a also a suite admin), the top bar shows the grid button: 40px round (44px below 640px), the `Grip` icon at 20px, labelled "Switch system", `aria-expanded`, tinted `accent` while open. It opens a popover built like the portal's `SuiteSwitcher` (352px, `rounded-2xl`, aligned to its right edge): a title row "Switch to" with a **Home** pill (house icon) going to the launcher, `${PORTAL_URL}/?from=VRMS` (a plain link, since it leaves the app; the VRMS card is a router link); then wide cards, one per row. First **VRMS**, ticked: navy inset ring, navy tile with the gold `Wrench`, its one line, the tag "You are here", `aria-current="page"`, going to `/`. Then each other system in `user.systems` (the same list `canSwitchSystem` reads, so the grid and its cards always agree), **BMS then VMMS**, with its icon (`CalendarCheck`, `Truck`), its one line, and the person's role there as a tag, by the launcher's `roleTag` rule ("Admin" when they hold `ADMIN` there, else the first of their roles there in `user.systemRoles`, by its catalog name; no tag, and no empty tag box, when the answer holds no roles for that system), going to `openSystemUrl(system)` (the launcher's `open`, AC-13). Last, for a suite admin (`user.suiteAdmin`) or anyone holding `ADMIN` in any system (`user.systemRoles`, or the VRMS `ADMIN` in `user.roles`), **Suite management** (`ShieldCheck`, "Users and permissions", tag "Admin"), going to `${PORTAL_URL}/admin`. The one lines are the portal's `SYSTEM_LINES`. Without `canSwitchSystem` there is no grid button and the avatar sits alone. The sidebar holds no switcher.
- **AC-9b** (added 2026-11-28): The notifications bell (feature 28, with its unread count from feature 29) takes the first place in the top bar's right group, left of the grid button, as a 40px round button like it. This feature builds no bell and leaves no empty space for it.
- **AC-10** (rewritten 2026-11-28, `Switcher16`): The avatar, top right at every size, is the portal's light account menu button: a 40px circle with the person's initials (Shell20: navy initials on the soft blue tint), initials only (VRMS has no picture), opening a menu aligned to its right edge. As in the portal's `LauncherShell` avatar, it has no `aria-label`: the spoken name is the visible initials plus a hidden "Account menu for [name, else email]", so axe's `label-content-name-mismatch` passes. The menu: the name and email at the top, then **Your profile** (`/profile`, VRMS's own page), a separator, **Sign out** (spec 0007's sign out, through `useShellActions`). No role, no Switch system, no Home in it.
- **AC-10a** (added 2026-11-28, `Shell20`): The top of the sidebar is the VRMS title, built like Suite management's (suite spec 0019 AC-17): the gold W tile (32px), "VRMS" in `text-group` bold, and under it the person's VRMS role name in `text-caption` `sidebar-idle` (muted white, never gold; the name from the catalog, suite spec 0018 child 0002 AC-35, the code in title case while names load). The title is a link to `/` with `sidebar-hover` on hover. Collapsed, only the tile shows, with the tooltip "VRMS" and the accessible name "VRMS, [role], dashboard". A `sidebar-line` sits under it, then New repair (AC-8).
- **AC-10b** (added 2026-11-28, `Shell20` footer option 5, suite spec 0019 AC-18): The bottom of the sidebar is the portal's footer strip: a darker strip (`bg-black/15`, a `sidebar-line` above it, at least 56px tall) holding the ///L mark on its small tile and "WeLinc Logistics" on one line, with the collapse button at its right. Collapsed, the strip holds only the expand button, centred, labelled "Expand sidebar". There is no full width Collapse row and no account menu in the sidebar. The collapse state and its key stay as spec 0016 says (`welinc:sidebar:<user id>`).

*Phones*
- **AC-11** (amended 2026-11-28): Below 768px spec 0016's rule holds, counted once like this: the person's visible top level pages (AC-1's pages, sub pages not counted); at most 5 gives the tab bar, more gives the sheet. There is no Account tab: the avatar in the top bar holds Your profile and Sign out. So a mechanic (Dashboard, My repairs, Repair history, Knowledge base) and someone who also sees Analytics get the tab bar, and anyone who sees an Admin page gets the sheet. The tab bar shows a dot on Repairs when any of its counts is hot. The sheet shows the VRMS title at the top, the same sections with sub pages and counts, and the footer strip without the collapse button (the same classes, minus the button). Sub pages on phones are reached from the sheet or from the view chips on the repair list.

*Portal Suite management*
- **AC-12** (rewritten 2026-11-28): The portal's Suite management shell is suite spec 0019's (AC-17 to AC-20, boards `Shell20` and `Switcher16`) as built before commit `f6e4985`: the sidebar title "Suite management" with the role line, the footer strip with the collapse button, the breadcrumb, and the grid switcher and account menu top right at every size. From `f6e4985`, these are taken back: the sidebar switcher (`AdminSwitcher`, "Admin" and "WeLinc portal"), the sidebar account menu, the full width Collapse row, and the `Timer` and `Activity` icons (Temporary access keeps `KeyRound`, Activity keeps `History`). These are kept: the sections as they are (unlabelled Overview for suite admins; Accounts: People, Deletion requests, Suite admins for suite admins; Access: Roles (`IdCard`), Temporary access; Audit: Activity); the Deletion requests count bubble (hot for suite admins, a dot when collapsed and on the phone tab bar); the launcher's `open` (AC-13). `/auth/admin/me` carries `pendingDeletionRequests`: the number of deletion requests in status `PENDING` the caller can act on (suite admins: all; a system admin: those in their systems, the same scope as the Deletion requests list). The portal reads it with `me`, which it already reads on load and on focus, and again after an approve or reject.
- **AC-13**: The portal launcher reads `?open=<SYSTEM>` once, before `from`: when the signed in person can open that system, it starts that system card's existing handoff at once (`from` is then ignored); when they can't, or the handoff fails, it shows the launcher as usual with the error toast the card would show, and `from` keeps its spec 0007 meaning. Both parameters are removed from the address after they are read. Signed out, the login keeps `open` in its return path so the handoff runs after sign in.

*Quality*
- **AC-14**: Both shells read well at 375px and 1280px, every item is reachable by keyboard with spec 0016's ring (on navy in the sidebar, on light in the top bar), sub page groups use `aria-expanded`, counts have accessible names ("3 waiting for sign off"), and one axe pass shows no violations. `npm run lint`, `npm run typecheck`, `npm run build:local` and the tests pass in web-vrms and the portal; lint, build and tests in welinc-backend-vrms and welinc-auth; the API docs check passes in welinc-backend-vrms.
- **AC-15** (amended 2026-11-28): The built sidebar nav matches `Sidebars8` (N16 admin, N17 mechanic) in structure, wording, icons and spec 0016 token values. The top bar, sidebar title, footer strip, switcher popover and avatar match `Shell20` and `Switcher16`, and VRMS matches the portal's built shell value for value (where the portal's built values differ from the boards, such as the 64px bar against the board's 56px, the built values win). Checked by the board comparison in [verify.md](verify.md); allowed differences are the four listed there, plus no Fleet section and no On hold sub page.

## Decision

**Chosen option**: Option 2: `Sidebars8`'s sections and sub pages with live counts, minus Fleet, on today's permission gating; since 2026-11-28 inside the Suite management frame (`Shell20` top bar, `Switcher16` switcher and account menu), shared by both apps.

The sidebar becomes the place that says what waits on you; the top bar becomes the place that says where you are and where else you can go. Sub pages are presets of the existing repair list, counts come from one small endpoint, and pages still appear by permission key, never by role.

**Implementation skills**: `shadcn` (`.claude/skills/shadcn/`) · `vercel-composition-patterns` (`.claude/skills/vercel-composition-patterns/`) · `nestjs-best-practices` (`.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`.claude/skills/prisma-client-api/`)

## Feature design

**Data model** (welinc-backend-vrms): `repair_tickets.sent_back_at` `timestamptz(6)` null. Send back sets it to the move's time; the next send for verification, a close or a cancel clears it. The migration backfills it for In progress tickets from the existing send back scan (`lastRejectionFrom`), once. `view=sentBack` and its count read the column, so neither scans audit rows. The ticket detail's "sent back" notice keeps its own rule. Nothing else changes; counts are computed on request. The 2026-11-28 update changes no data.

**Nav model** (web-vrms `components/layout/navItems.ts`): `NavItem` gains `children?: NavItem[]` and `countKey?: keyof NavCounts`; `getNavSections(can, ctx)` takes `ctx = { inRoster: boolean }` (from the existing `/vrms/permissions/me` answer, which gains `inRoster`). `getMobileTabs` and `usesTabBar` keep working on top level items only; `ACCOUNT_TAB` goes (AC-11). `getActiveNavTrail` also returns the current sub page, matched by path plus `view`, so the top bar can build "VRMS › page › sub page".

**Shell parts** (web-vrms `components/layout/`, 2026-11-28):

| Part | What it is | Replaces |
|---|---|---|
| `TopBar.tsx` | the bar of AC-9, at every size; holds `Breadcrumbs`, the bell's place, `SystemSwitcher`, `AccountMenu`, and below 768px the menu button or the W tile | `AppHeader.tsx` |
| `Breadcrumbs` (in `TopBar.tsx`) | the trail from `getActiveNavTrail` plus an optional last crumb from the page | the breadcrumb in `PageHeader.tsx` |
| `BreadcrumbTail` context and `useBreadcrumbTail(label \| null)` | lets a page add the last crumb: the ticket number on `RepairDetailPage` (nothing while it loads), "New repair" on the new ticket form | the `crumb` prop |
| `SystemSwitcher.tsx` | the grid popover of AC-9a, a copy of the portal's `SuiteSwitcher` with VRMS as the ticked card | `SystemSwitcher` in `SidebarAccount.tsx` |
| `AccountMenu.tsx` | the avatar menu of AC-10 | `UserMenu.tsx` and `SidebarAccount` |
| `SidebarTitle` and `SidebarFooter` (in `Sidebar.tsx`) | AC-10a and AC-10b, shared by the sidebar and the sheet | the switcher row and the collapse and account rows |
| `lib/systems.ts` | `SYSTEM_ICONS` and `SYSTEM_LINES` copied from the portal's `src/pages/launcher/systemIcons.ts` | none |
| `components/brand/LogoMark.tsx` | the ///L mark copied from the portal's `src/components/LogoMark.tsx` | none |

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/nav/counts` | GET | none | `{ open?, signoff?, mine?, active?, sentBack?, suggestions? }` (numbers) | any VRMS user; each count by its key (below) | 401 |
| `/vrms/repairs` | GET | existing filters plus `view?` (`open`, `signoff`, `mine`, `active`, `sentBack`, `done`) | as today | as today, plus the view's rule | 400 `VALIDATION_FAILED`, 403 |
| `/vrms/permissions/me` | GET | as today | gains `inRoster: boolean` | as today | as today |
| `/auth/admin/me` (welinc-auth) | GET | as today | gains `pendingDeletionRequests: number` | as today | as today |

Count and view rules: `open`, `signoff` need `ticket.view_all`; `mine` needs an assignable roster row; `active`, `sentBack`, `done` are the caller's own assigned tickets (needs `ticket.view`); `suggestions` needs `knowledge.edit`. `Cache-Control: no-store`. The counts route is tagged authenticated (no key), as `route-permissions.spec.ts` requires every route to declare, and computes the ticket counts in one grouped query (conditional counts over the open and the caller's assigned tickets) plus one for suggestions. `inRoster` on `/vrms/permissions/me` is true when the caller's `Mechanic` row exists with `isActive` and `assignable` (suite spec 0018 child 0002, AC-33). The 2026-11-28 update adds no route: the switcher's systems and roles come from the session answer VRMS already holds, and the role names from `GET /auth/systems`, which VRMS already reads. Step 6a adds two fields to that answer instead (below).

**The grant answer's new fields** (welinc-auth, step 6a; contract 0001 section 5, additive). Every user grant answer (code exchange, refresh, mobile login) gains, beside `user.systems`:

| Field | Type | Value |
|---|---|---|
| `user.systemRoles` | `{ system: string; roles: string[] }[]` | one entry per system in `user.systems`, same order (VRMS included); `roles` are the live role codes held there (a temporary role included, an expired one left out, as `liveRoleWhere`), ordered by catalog `sortOrder`, then code (the launcher's comparator in `buildLauncherSystems`, moved into one shared helper both use); a held code with no catalog row (say a deleted custom role) is left out, as the launcher does, and a system left with none keeps its entry with `roles: []`. Not filtered by the client's `allowedRoles` (the launcher's `roles` aren't either), so VRMS's own entry can list a role `user.roles` omits; display only, so that is fine |
| `user.suiteAdmin` | `boolean` | whether a `suite_admins` row exists for the person, as the launcher's `suiteAdmin` |

`user.systems` holds web openable systems only (`webSystemsFor`), so a phone only system has no entry and no card. Both are read fresh at each grant, in the grant's own transaction, and never put in a token. All three grants build `user` in `finish()`, so a mobile login answers the same fields; the mobile app ignores them. welinc-auth computes them in one helper beside `webSystemsFor` in `launcher.ts`, taking the live rows `rolesFor` already read (`rows`), the transaction and the web systems list, adding two reads per grant: the held codes' `sortOrder` and the `suite_admins` row. The reply class and `docs/openapi.json` change with it. backend-vrms's `toGrant` keeps a `systemRoles` entry only when `system` is a string and `roles` an array of strings (else `[]`), takes `suiteAdmin` only when it is `true` (else `false`), and passes both on in the `user` of `POST /vrms/session/refresh`, as it does `systems`: the fields go on `UserGrant`, `toGrant`, the refresh answer's `user`, web-vrms's `toUser`, the cross tab `TokenMessage` and the `User` type, a missing value meaning `[]` and `false` at every hop (an older tab ignores them). The web app gets `user` only from that refresh, on first load too, so no other fallback is needed. Nothing stores them.

**Value sourcing**:

| Action | Value produced or displayed | Source |
|---|---|---|
| Sidebar | which pages and sub pages | the viewer's permission keys (`PermissionsProvider`) and `inRoster` (the `Mechanic` row: `isActive` and `assignable`) |
| Sidebar | page labels ("My dashboard", "My repairs") | `ticket.view_all` |
| Sub page | count | `/vrms/nav/counts` |
| Sub page | hot or not | AC-6's rule from the viewer's keys |
| Folded parent | bubble | sum of its children's hot counts, else nothing |
| Open groups | which are open | the current route, else `localStorage` `welinc:nav-open:<user id>` |
| Repair list | the preset filter | `view` in the address |
| New repair | shown or not | `ticket.create` |
| Sidebar title | role line | `authStore.user.role`, named by `useRoleLabel()` (`GET /auth/systems`), the code in title case until it loads |
| Breadcrumb | page and sub page crumbs | `getActiveNavTrail(pathname, view, sections)` (the nav labels) |
| Breadcrumb | last crumb on a record or a page outside the nav | `useBreadcrumbTail`, set only where the page already holds the value: the loaded ticket's `ticketNumber`; "New repair" on `/repairs/new`; "Profile" on `/profile`; the loaded guide's title on a knowledge base guide; the current tab's label on Settings. Users, Audit logs and Analytics stop at the page. None while loading; a page with no nav match and no tail shows "VRMS" alone |
| Switcher | shown or not | `canSwitchSystem(user)` (spec 0007), unchanged |
| Switcher | the other systems | `authStore.user.systems` (the list `canSwitchSystem` reads), minus VRMS, in BMS, VMMS order; a code the suite doesn't know is left out |
| Switcher | each system's role tag | `user.systemRoles` entry for that system (step 6a), by the portal's `roleTag` rule: "Admin" when its `roles` hold `ADMIN`, else the first code (catalog order), named by `useSystemRoleLabel()(system, code)` (`lib/roles.ts` keeps every system's names from `GET /auth/systems`, keyed by system and code, since codes such as `ADMIN` repeat across systems); the code in title case until it loads, which for a new custom role lasts until the catalog's refetch on focus |
| Switcher | Suite management card | shown when `user.suiteAdmin` is true, or any `user.systemRoles` entry holds `ADMIN`, or `user.roles` holds the VRMS `ADMIN` (so it still shows while the answer lacks the new fields) |
| Switcher | grid button | `canSwitchSystem`: two or more `user.systems`, or the VRMS `ADMIN`, or `user.suiteAdmin` (step 6a; this widens spec 0007's AC-9 and AC-14 rule for VRMS, recorded here rather than in 0007, because a suite admin now has a card to go to) |
| Switcher | targets | VRMS: `/`; another system: `openSystemUrl(system)` (`${PORTAL_URL}/?from=VRMS&open=<SYSTEM>`); Suite management: `${PORTAL_URL}/admin`; Home: `switchSystemUrl()` |
| Switcher | icons and one lines | `lib/systems.ts` (copied from the portal) |
| Avatar menu | initials, name, email, spoken name | `authStore.user` (`getInitials(name)`, the email when there is no name); spoken: the initials plus "Account menu for [name, else email]" |
| Sent back to me | which tickets | `repair_tickets.sent_back_at` set, status In progress, assigned to the viewer |
| Collapse | collapsed or not | `localStorage` `welinc:sidebar:<user id>` (spec 0016) |
| Portal sidebar | Deletion requests count and hot | `/auth/admin/me` `pendingDeletionRequests` (status `PENDING`, the caller's systems); hot when `suiteAdmin` |
| Portal launcher | system to open | `?open` read once, checked against the launcher's own `systems` |

**Key invariants**:
- A count is shown only to someone who can open the page it counts, and it equals that page's total.
- Pages appear by permission key; no role code decides the nav (suite spec 0018). The switcher's Suite management card is the one place a role code (`ADMIN`) decides what shows, because Suite management's own door is the admin role, not a VRMS key.
- `user.systemRoles` and `user.suiteAdmin` are display only in VRMS: no VRMS guard, permission check or query reads them, and backend-vrms never stores them. Access in VRMS is still the token's VRMS `roles` and the permission matrix.
- Gold appears only on hot counts, the logo tile and the ticked card's tile (spec 0016 Signature, spec 0019 AC-20).
- VRMS's shell and the portal's Suite management shell share one frame: a value changed in one is changed in the other.

**Security model**: counts reveal only totals the caller could already list. `view` never widens what the list returns; it only narrows it. The launcher's `open` can only start a handoff the person could start by clicking the card. The switcher lists only systems the person's own session answer names, and every target goes through the launcher's checks, so a stale tab can show a card the launcher then refuses (with its toast), never more access. The new fields hold only the person's own roles and suite admin flag, which their launcher already shows them; welinc-auth sends them only in that person's own grant answer, to the client the person signed in to.

**Critical test scenarios**:
- Chief: `vrms.chief@` sees Waiting for sign off with a gold count equal to the filtered list's total, verifies **AC-2**, **AC-5**, **AC-6**.
- Mechanic: a seed mechanic sees My repairs with In progress, Sent back to me (gold) and Done; no New repair; a line under the VRMS title, verifies **AC-2**, **AC-8**, **AC-10a**.
- Views: `/repairs?view=signoff` plus a garage filter pages correctly; `view=mine` for someone outside the roster answers 403, verifies **AC-4**.
- Refresh: sending a ticket for verification lowers Sent back to me without a reload, verifies **AC-7**.
- Top bar: on `/repairs?view=signoff` the breadcrumb reads "VRMS › Repair tickets › Waiting for sign off" and `PageHeader` shows no breadcrumb; on a ticket the last crumb is its number, verifies **AC-9**.
- Switcher: `multi.chief@` opens the grid, sees VRMS ticked first, then BMS and VMMS with their role tags (from `user.systemRoles`), and lands in VMMS without clicking the card; a VRMS only mechanic has no grid button; `vrms.admin@` sees VRMS and the Suite management card, verifies **AC-9a**, **AC-13**.
- Switcher sources (step 6a): a VMMS Admin who holds a non admin VRMS role sees "Admin" on the VMMS card and the Suite management card; a suite admin on a temporary non admin VRMS role (one system) gets the grid button and the Suite management card; with the new fields left out of the answer (an older welinc-auth) the cards show with no tag and the card follows the VRMS `ADMIN` alone, verifies **AC-9a**.
- Avatar: name and email, Your profile, Sign out, nothing else; axe finds no name mismatch, verifies **AC-10**, **AC-14**.
- Collapsed: dots on Repair tickets, the New repair icon, the W tile alone at the top, only the expand button in the footer strip, tooltips, verifies **AC-6**, **AC-8**, **AC-10a**, **AC-10b**.
- Phone: a mechanic gets the tab bar with no Account tab and a dot on Repairs, the top bar with the W tile and the avatar; an admin gets the sheet with the title, sub pages, counts and the footer strip, verifies **AC-9**, **AC-11**.
- Portal: a suite admin sees "Suite management" with the role line, the footer strip, the grid and avatar top right at 1280px, and Deletion requests with a gold count; a VRMS admin sees no Overview or Suite admins, verifies **AC-12**.

## Build plan

Facade first (the UI refresh phase's approach): the new sidebar on the data the app already has, then the counts and views behind it. Starts after S18's milestone 3 (the sidebar restyle and collapse, spec 0016 step 6) **and** after suite spec 0018 child 0002's step 2 (VRMS on permissions, the roster by `ticket.assignable`, role names from the catalog), since both touch `navItems.ts`, `session.ts`, `RoleBadge` and the account menu. Steps 5 and 6 are frontend only and change no route; build them on the existing `feat/navigation-redesign` branches. Step 6a adds no route either, but adds two fields to welinc-auth's grant answer, a shared repo (branch from `development`, PR the other groups can see).

1. [x] web-vrms: the nav model with sections, sub pages and open state, the switcher (menu or label), New repair button, account menu, Profile out of the nav; sub pages link to `view` presets that the list reads client side for now, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-8** (the switcher and account menu parts are redone in step 5)
2. [x] welinc-backend-vrms: the `sent_back_at` migration with its backfill and the moves that set and clear it; `view` on `GET /vrms/repairs` with the rules, `inRoster` on `/vrms/permissions/me`, `GET /vrms/nav/counts` (one grouped query, authenticated tag), tests per view and per count (each count equals its list total), the API docs; web-vrms switches the list to send `view`, satisfies **AC-2**, **AC-4**, **AC-5**
3. [x] web-vrms: count bubbles, hot rule, collapsed dots, refresh timing; phones (tab bar dot, sheet with sub pages and counts, New repair in page headers), satisfies **AC-5**, **AC-6**, **AC-7**, **AC-11**
4. [x] Portal and welinc-auth: `pendingDeletionRequests` on `/auth/admin/me`, the `AdminShell` sidebar frame (switcher, sections, Roles naming, count, account menu), the launcher's `open`, satisfies **AC-12** (the frame part is redone in step 6), **AC-13**
5. [x] web-vrms, the Suite management frame: `TopBar` with `Breadcrumbs` and `BreadcrumbTail` (ticket number, New repair), the grid `SystemSwitcher` popover with the role tags (`lib/roles.ts` keeps every system's names), `AccountMenu`, `SidebarTitle` and `SidebarFooter` (copy `LogoMark` and the system icons and lines from the portal); remove `AppHeader`, `UserMenu`, `SidebarAccount`, the sidebar switcher, `ACCOUNT_TAB` and `PageHeader`'s breadcrumb and `crumb` prop; the tab bar rule without the Account tab; the sheet with the title and footer strip; tests for the trail, the switcher's cards and tags, and the tab bar count, satisfies **AC-8**, **AC-9**, **AC-9a**, **AC-9b**, **AC-10**, **AC-10a**, **AC-10b**, **AC-11**
6. [x] Portal: take `Shell20` back in `AdminShell` by hand, using `f6e4985`'s parent (`4954145`) as the reference only (never check that file out: it predates the count, `open` and Roles). Drop `md:hidden` on the top right switcher and account group, remove `AdminSwitcher`, the sidebar account menu and the full width Collapse row, and restore the sidebar title and role line, the footer strip with the collapse button, the switcher and account menu top right at every size, `KeyRound` and `History`; keep the Deletion requests count (sidebar, collapsed dot, tab bar dot), the launcher's `open` and the `me` refresh; update the tests `f6e4985` changed, satisfies **AC-12**
6a. [x] welinc-auth, then backend-vrms, then web-vrms, the switcher's role source (one end to end slice): `systemRoles` and `suiteAdmin` on every user grant answer (the helper beside `webSystemsFor`, the reply class, `npm run openapi`, unit tests for order and ties, temporary and expired roles, a code with no catalog row, a mobile login and a suite admin; update any test that compares the whole `user`), the additive amendment to contract 0001 section 5; `toGrant` and the refresh answer in backend-vrms, with tests for missing and malformed fields; in web-vrms the fields through `toUser`, `TokenMessage` and the `User` type, `systemRoleTag` and `holdsAdminAnywhere` in `switchSystem.ts` rewritten to read `systemRoles` (and `suiteAdmin`) by the value sourcing table, `canSwitchSystem` with `suiteAdmin`, and tests for each rule plus the missing field fallback. Any deploy order is safe (each side tolerates the other's absence), satisfies **AC-9a**
7. [ ] Sweep: 375px and 1280px in both apps, keyboard, axe, lint, typecheck, builds, tests, the board comparison (VRMS against the portal value for value), the suite `design.md` lines this spec amends (Sidebar, Collapse, Page header, a new Top bar line; spec 0016 already carries the amendment), satisfies **AC-14**, **AC-15**

## Consequences

**Positive**:
- What waits on you is visible from every page, which covers feature 29's queue count half without a notification system.
- Mechanics get their own three way split of their work, matching how they think about it on the floor.
- Switching systems is one click for the people who need it, and invisible to those who don't.
- VRMS and Suite management now read as one product: the same bar, the same switcher, the same menu, in the same places. Someone moving between them never looks for the avatar.
- The bell has a settled home before feature 28 is designed, so it won't reopen the shell.

**Negative / tradeoffs**:
- One more request every 60 seconds per open tab (`/vrms/nav/counts`), on top of the permission poll; kept to two queries.
- A new `sent_back_at` column that the status moves must keep right; a missed clear would leave a ticket in "Sent back to me".
- "Waiting for sign off" can read lower for a chief than the plain For verification total, because their own tickets are left out.
- Sub pages are presets, not saved filters: a user can't add their own.
- The Admin's top level items exceed 5, so admins always get the sheet on phones, as today.
- The portal launcher learns an `open` parameter, a small cross repo change.
- The top bar takes 64px of height on every page, where VRMS desktop had none; long lists show about one row less.
- Two copies of the switcher (portal and VRMS) and of the system icons and lines, with no checker; a change to one must be made in both by hand.
- The switcher reads the session answer, so a role given or taken mid session shows on the next token refresh; the launcher's own checks still decide what opens.
- Every grant (and so every refresh, about every 15 minutes per tab) costs welinc-auth two more small reads, for the role order and the suite admin flag.
- backend-vrms now receives the person's roles in other systems. It must treat them as display only (the invariant above); a later change that reads them for access would cross the system boundary.
- Build steps 1 and 4 are partly redone: about a day of rework across web-vrms and the portal.

**Neutral**:
- Fleet waits for feature 56 to decide how VRMS and VMMS share trucks.
- On hold joins Repair tickets when feature 31 ships (its spec adds `view=onhold` and its count).

## Follow-up

- [ ] Feature 29's row: the queue counts half is delivered here; what remains is the bell and its unread count (feature 28).
- [x] Features 28 and 29: the bell goes in the VRMS top bar, left of the grid switcher (AC-9b). Note added to both rows (2026-11-28).
- [ ] Feature 31's spec adds the On hold sub page and its count.
- [ ] Feature 56's row gets the note "a truck that isn't in the VMMS fleet yet" (added with this spec).
- [ ] `/sync`: web-vrms `AGENTS.md` names `view` presets and `/vrms/nav/counts` as the way to add a queue to the sidebar, `useBreadcrumbTail` as the way a page names its record in the breadcrumb, and that the switcher and system icons are copies of the portal's (change both).

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
