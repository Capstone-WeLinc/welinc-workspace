# 0027. Navigation redesign: sections, sub pages with counts, switcher and account menu

**Date**: 2026-11-23
**Status**: In Progress
**Scope row**: [70](../../../scope/vrms/ui-refresh.md#70-navigation-redesign--planned--needs-a-decision) (`docs/scope/vrms/ui-refresh.md`)
**Repos**: `welinc-web-vrms`, `welinc-backend-vrms`, `welinc-web-portal` (`AdminShell` sidebar, the launcher's `open` handoff), `welinc-auth` (one field on `/auth/admin/me`)
**Design source**: board `Sidebars8` (canvas "WeLinc design directions", https://claude.ai/artifact/VFhLSMNhfpAFD4D4c2VQzp, page "Round 8"), with round 1's `BPhone` for the phone. Copies live in [boards/](boards/). The look, the collapse and the phone rule come from suite spec [0016](../../_root/0016-design-direction-refresh/index.md) *Layout and navigation*; this spec decides what goes in the sidebar.

## Summary

Spec 0016 settles how the sidebar looks; this spec settles what is in it. VRMS gets the sections Work, Insights and Admin (Fleet is left out because VMMS owns the trucks). Repair tickets and Knowledge base open into sub pages (All open, Waiting for sign off, Assigned to me; for mechanics In progress, Sent back to me, Done; Guides and Suggestions) with live counts, gold when the count waits on you. A New repair button sits at the top, a system switcher shows for people with more than one system (and VRMS Admins), and an account menu at the bottom holds Profile and Sign out. The portal's Admin sidebar gets the same frame.

## Requirements

**User stories**:
- As a chief mechanic, I want to see how many tickets wait for my sign off from any page, so that I don't miss them.
- As a mechanic, I want my tickets split into In progress, Sent back to me and Done, with a gold count on what was sent back, so that I know what needs me first.
- As an admin, I want New repair always one click away, so that a truck coming in gets a ticket fast.
- As someone in VRMS and VMMS, I want to switch systems from the top of the sidebar, so that I don't go through the portal by hand.

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

*Top and bottom of the sidebar*
- **AC-8**: With `ticket.create`, a full width primary "New repair" button (`Plus` icon) sits under the system switcher; collapsed, it is a 40px icon button with the tooltip "New repair". It goes to `/repairs/new`. Without the key, a `sidebar-line` and 12px of space sit under the switcher instead (`Sidebars8` N17). On phones New repair is the primary action in the header of the Repair tickets page and the dashboard, not in the tab bar.
- **AC-9**: The system switcher at the top shows the WeLinc mark, "VRMS" and "Vehicle repairs". When `canSwitchSystem` is true (two or more systems, or a VRMS Admin, spec 0007), it is a button opening a menu: the person's systems in VRMS, VMMS, BMS order (a VRMS Admin with only VRMS sees just VRMS and the portal entry, which is how they reach the portal's Admin), VRMS checked and marked "You're here", each other system going to the portal launcher with `?from=VRMS&open=<SYSTEM>`, then a separator and "WeLinc portal" (the launcher). Otherwise it is a plain label with no menu. "Switch system" leaves the account menu. Collapsed, only the mark shows (the menu still opens from it when allowed).
- **AC-10**: The account menu at the bottom shows a round initials tile, the name and the role name (from the catalog, suite spec 0018 child 0002, AC-35; that step ships first, and the code in title case is the fallback while names load). Its menu: name and email, Profile, Sign out. Above it, the collapse toggle (spec 0016). On phones the header's user menu holds the same items.

*Phones*
- **AC-11**: Below 768px spec 0016's rule holds, counted once like this: the person's visible top level pages (AC-1's pages, sub pages not counted) plus one Account tab; at most 5 gives the tab bar, more gives the sheet. So a mechanic (Dashboard, My repairs, Repair history, Knowledge base, Account) gets the tab bar, and anyone who also sees Analytics or an Admin page gets the sheet. The tab bar shows a dot on Repairs when any of its counts is hot. The sheet shows the switcher at the top, the same sections with sub pages and counts, and the account items at the bottom. "Account" in the tab bar opens Profile. Sub pages on phones are reached from the sheet or from the view chips on the repair list.

*Portal Admin*
- **AC-12**: The portal `AdminShell` sidebar uses the same frame: the switcher shows the WeLinc mark, "Admin" and "WeLinc portal"; its menu lists "Launcher" and the person's systems (each through the launcher's `open`). Sections: unlabelled Overview (suite admins); Accounts: People, Deletion requests (with a count of pending requests, hot for suite admins), Suite admins (suite admins); Access: Roles (`IdCard`), Temporary access (`Timer`); Audit: Activity (`Activity`). The account menu at the bottom shows the name and "Suite admin" or "[System] admin", with Sign out. `/auth/admin/me` gains `pendingDeletionRequests`: the number of deletion requests in status `PENDING` the caller can act on (suite admins: all; a system admin: those in their systems, the same scope as the Deletion requests list). The portal reads it with `me`, which it already reads on load and on focus, and again after an approve or reject.
- **AC-13**: The portal launcher reads `?open=<SYSTEM>` once, before `from`: when the signed in person can open that system, it starts that system card's existing handoff at once (`from` is then ignored); when they can't, or the handoff fails, it shows the launcher as usual with the error toast the card would show, and `from` keeps its spec 0007 meaning. Both parameters are removed from the address after they are read. Signed out, the login keeps `open` in its return path so the handoff runs after sign in.

*Quality*
- **AC-14**: Both sidebars read well at 375px and 1280px, every item is reachable by keyboard with spec 0016's ring on navy, sub page groups use `aria-expanded`, counts have accessible names ("3 waiting for sign off"), and one axe pass shows no violations. `npm run lint`, `npm run typecheck`, `npm run build:local` and the tests pass in web-vrms and the portal; lint, build and tests in welinc-backend-vrms and welinc-auth; the API docs check passes in welinc-backend-vrms.
- **AC-15**: The built sidebar matches `Sidebars8` (N16 admin, N17 mechanic, the portal variant) in structure, wording, icons and spec 0016 token values, checked by the board comparison in [verify.md](verify.md); allowed differences are the four listed there, plus no Fleet section and no On hold sub page.

## Decision

**Chosen option**: Option 2: `Sidebars8`'s sections and sub pages with live counts, minus Fleet, on today's permission gating.

The sidebar becomes the place that says what waits on you: sub pages are presets of the existing repair list, counts come from one small endpoint, and pages still appear by permission key, never by role.

**Implementation skills**: `shadcn` (`.claude/skills/shadcn/`) · `vercel-composition-patterns` (`.claude/skills/vercel-composition-patterns/`) · `nestjs-best-practices` (`.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`.claude/skills/prisma-client-api/`)

## Feature design

**Data model** (welinc-backend-vrms): `repair_tickets.sent_back_at` `timestamptz(6)` null. Send back sets it to the move's time; the next send for verification, a close or a cancel clears it. The migration backfills it for In progress tickets from the existing send back scan (`lastRejectionFrom`), once. `view=sentBack` and its count read the column, so neither scans audit rows. The ticket detail's "sent back" notice keeps its own rule. Nothing else changes; counts are computed on request.

**Nav model** (web-vrms `components/layout/navItems.ts`): `NavItem` gains `children?: NavItem[]` and `countKey?: keyof NavCounts`; `getNavSections(can, ctx)` takes `ctx = { inRoster: boolean }` (from the existing `/vrms/permissions/me` answer, which gains `inRoster`). `getMobileTabs` and `usesTabBar` keep working on top level items only.

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/nav/counts` | GET | none | `{ open?, signoff?, mine?, active?, sentBack?, suggestions? }` (numbers) | any VRMS user; each count by its key (below) | 401 |
| `/vrms/repairs` | GET | existing filters plus `view?` (`open`, `signoff`, `mine`, `active`, `sentBack`, `done`) | as today | as today, plus the view's rule | 400 `VALIDATION_FAILED`, 403 |
| `/vrms/permissions/me` | GET | as today | gains `inRoster: boolean` | as today | as today |
| `/auth/admin/me` (welinc-auth) | GET | as today | gains `pendingDeletionRequests: number` | as today | as today |

Count and view rules: `open`, `signoff` need `ticket.view_all`; `mine` needs an assignable roster row; `active`, `sentBack`, `done` are the caller's own assigned tickets (needs `ticket.view`); `suggestions` needs `knowledge.edit`. `Cache-Control: no-store`. The counts route is tagged authenticated (no key), as `route-permissions.spec.ts` requires every route to declare, and computes the ticket counts in one grouped query (conditional counts over the open and the caller's assigned tickets) plus one for suggestions. `inRoster` on `/vrms/permissions/me` is true when the caller's `Mechanic` row exists with `isActive` and `assignable` (suite spec 0018 child 0002, AC-33).

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
| Switcher | shown as a menu or a label | `canSwitchSystem(user)` (spec 0007) |
| Switcher menu | the person's systems | `user.systems` (from the token) |
| Switcher menu | target of a system | `${PORTAL_URL}/?from=VRMS&open=<SYSTEM>` |
| Account menu | name, email, role name | `authStore.user`; the role name from `GET /auth/systems`, the code in title case until it loads |
| Sent back to me | which tickets | `repair_tickets.sent_back_at` set, status In progress, assigned to the viewer |
| Collapse | collapsed or not | `localStorage` `welinc:sidebar:<user id>` (spec 0016) |
| Portal sidebar | Deletion requests count and hot | `/auth/admin/me` `pendingDeletionRequests` (status `PENDING`, the caller's systems); hot when `suiteAdmin` |
| Portal launcher | system to open | `?open` read once, checked against the launcher's own `systems` |

**Key invariants**:
- A count is shown only to someone who can open the page it counts, and it equals that page's total.
- Pages appear by permission key; no role code decides the nav (suite spec 0018).
- Gold appears only on hot counts and the logo (spec 0016 Signature).

**Security model**: counts reveal only totals the caller could already list. `view` never widens what the list returns; it only narrows it. The launcher's `open` can only start a handoff the person could start by clicking the card.

**Critical test scenarios**:
- Chief: `vrms.chief@` sees Waiting for sign off with a gold count equal to the filtered list's total, verifies **AC-2**, **AC-5**, **AC-6**.
- Mechanic: a seed mechanic sees My repairs with In progress, Sent back to me (gold) and Done; no New repair; a line under the switcher, verifies **AC-2**, **AC-8**.
- Views: `/repairs?view=signoff` plus a garage filter pages correctly; `view=mine` for someone outside the roster answers 403, verifies **AC-4**.
- Refresh: sending a ticket for verification lowers Sent back to me without a reload, verifies **AC-7**.
- Switcher: `multi.chief@` opens VMMS from the switcher and lands in VMMS without clicking the card; a VRMS only mechanic sees a plain label, verifies **AC-9**, **AC-13**.
- Collapsed: dots on Repair tickets, the New repair icon, tooltips, verifies **AC-6**, **AC-8**.
- Phone: a mechanic gets the tab bar with a dot on Repairs; an admin gets the sheet with sub pages, verifies **AC-11**.
- Portal: a suite admin sees Deletion requests with a gold count; a VRMS admin sees no Overview or Suite admins, verifies **AC-12**.

## Build plan

Facade first (the UI refresh phase's approach): the new sidebar on the data the app already has, then the counts and views behind it. Starts after S18's milestone 3 (the sidebar restyle and collapse, spec 0016 step 6) **and** after suite spec 0018 child 0002's step 2 (VRMS on permissions, the roster by `ticket.assignable`, role names from the catalog), since both touch `navItems.ts`, `session.ts`, `RoleBadge` and the account menu.

1. [x] web-vrms: the nav model with sections, sub pages and open state, the switcher (menu or label), New repair button, account menu, Profile out of the nav; sub pages link to `view` presets that the list reads client side for now, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-8**, **AC-9**, **AC-10**
2. [x] welinc-backend-vrms: the `sent_back_at` migration with its backfill and the moves that set and clear it; `view` on `GET /vrms/repairs` with the rules, `inRoster` on `/vrms/permissions/me`, `GET /vrms/nav/counts` (one grouped query, authenticated tag), tests per view and per count (each count equals its list total), the API docs; web-vrms switches the list to send `view`, satisfies **AC-2**, **AC-4**, **AC-5**
3. [x] web-vrms: count bubbles, hot rule, collapsed dots, refresh timing; phones (tab bar dot, sheet with sub pages and counts, New repair in page headers), satisfies **AC-5**, **AC-6**, **AC-7**, **AC-11**
4. [x] Portal and welinc-auth: `pendingDeletionRequests` on `/auth/admin/me`, the `AdminShell` sidebar frame (switcher, sections, Roles naming, count, account menu), the launcher's `open`, satisfies **AC-12**, **AC-13**
5. Sweep: 375px and 1280px in both apps, keyboard, axe, lint, typecheck, builds, tests, the board comparison, satisfies **AC-14**, **AC-15**

## Consequences

**Positive**:
- What waits on you is visible from every page, which covers feature 29's queue count half without a notification system.
- Mechanics get their own three way split of their work, matching how they think about it on the floor.
- Switching systems is one click for the people who need it, and invisible to those who don't.

**Negative / tradeoffs**:
- One more request every 60 seconds per open tab (`/vrms/nav/counts`), on top of the permission poll; kept to two queries.
- A new `sent_back_at` column that the status moves must keep right; a missed clear would leave a ticket in "Sent back to me".
- "Waiting for sign off" can read lower for a chief than the plain For verification total, because their own tickets are left out.
- Sub pages are presets, not saved filters: a user can't add their own.
- The Admin's top level items exceed 5, so admins always get the sheet on phones, as today.
- The portal launcher learns an `open` parameter, a small cross repo change.

**Neutral**:
- Fleet waits for feature 56 to decide how VRMS and VMMS share trucks.
- On hold joins Repair tickets when feature 31 ships (its spec adds `view=onhold` and its count).

## Follow-up

- [ ] Feature 29's row: the queue counts half is delivered here; what remains is the bell and its unread count (feature 28).
- [ ] Feature 31's spec adds the On hold sub page and its count.
- [ ] Feature 56's row gets the note "a truck that isn't in the VMMS fleet yet" (added with this spec).
- [ ] `/sync`: web-vrms `AGENTS.md` names `view` presets and `/vrms/nav/counts` as the way to add a queue to the sidebar.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
