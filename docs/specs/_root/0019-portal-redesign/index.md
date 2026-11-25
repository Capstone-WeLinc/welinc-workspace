# 0019. Portal redesign from the design rounds

**Date**: 2026-11-24 (updated 2026-11-26: launcher, launches, sign in, the summary route and Motion, see *Update 2026-11-26* in [rationale.md](rationale.md))
**Status**: In Progress
**Scope row**: [S22](../../../scope/_root/shared-services.md) (shared services, Beta)
**Repos**: `welinc-web-portal` (almost everything), `welinc-auth` (two additive routes, one launcher answer field, two additive People list filters, the code email layout), `welinc-web-vrms` (the idle warning toast only), workspace (`design.md`, spec 0016 amendment lines, contract 0001)
**Design source**: the canvas "WeLinc design directions" (https://claude.ai/artifact/VFhLSMNhfpAFD4D4c2VQzp), pages "Round 12" to "Round 37", opened from the codesamtm claude.ai account; since the 2026-11-26 update, the sign in from "WeLinc portal redo" (Round 47) and the launcher from "WeLinc launcher: system pickers" (https://claude.ai/artifact/MCG63z1xfNtVSRmYz6pxRp, Rounds 49 to 69; history and generators in [`docs/context/vrms/portal-redo-boards/`](../../../context/vrms/portal-redo-boards/README.md)). Copies of every board named here live in [`boards/`](boards/); the copies are the source for `/develop` and `/check verify`. Older boards on the canvas are history.

## Summary

This spec turns the portal screens you picked into a build: a calm launcher of system tiles under a short navy band (no greeting, no moving vehicles), the sign in on a quiet drawn map with the form on navy glass, the four step forgot password, the Suite management shell, the filter popover, the one screen Add a user dialog, new toasts, a 404 page, branded code emails, the favicon and tab titles. Motion is plain CSS: the tiles slide in after a sign in, and opening a system plays one of three short launch scenes at random. A suite admin with no system role skips the launcher and lands in Suite management. Two small additive welinc-auth routes (email check, filter counts), one new launcher answer field (`suiteAdmin`) and a multi system, multi role filter on the People list close the gaps the boards leave. The "Signed in until" pill is not built; a "Still there?" toast, two minutes before the idle limit, replaces the signing out soon banner in the portal and in web-vrms.

## Requirements

**User stories**:
- As anyone signing in, I want a front door that looks like WeLinc Logistics, not a template, so the suite feels like one product.
- As a staff member with one system, I want to land straight in my system, and as anyone with more, I want one screen that shows every system I can open.
- As a suite admin, I want to land straight in Suite management, since it is the only place I can go.
- As anyone working in the portal or VRMS, I want a clear warning before I'm signed out for being idle, with one button to stay.
- As someone who gets dizzy from movement, I want the launcher to respect my reduced motion setting.

**Acceptance criteria**:

*Launcher*
- **AC-1**: The launcher matches the Round 69 person boards (`R69Victor`, `R69Danilo`, `R69Corazon`, `R69Felicidad`, `R69Armando`). The top is **Q1**: one 88 px navy band that is the whole navbar, holding the gold ///L `LogoMark`, "WeLinc Logistics" in white italic with "Operations Workspace" beside it, and the account button on the right (a **white circle with navy initials** from `initialsOf` in `lib/launcher.ts`, the email's first letter when there is no name, then the name cut with an ellipsis when long, and a chevron; its menu is AC-19's). **M1**: the ///L mark drawn oversized and faint on the band's right, with a soft light behind it and a thin gold fade along the band's bottom edge. There is no greeting and nothing in its place, no date, no line drawing, no road, no vehicles, no map, no "Signed in until" pill and no help button (the boards' "?" has no help page behind it). The bottom is **K3a** over **E1g**: a small stack of line drawn cartons (no labels, light navy ink with soft gold tape) standing at the bottom right on the content edge, over a still hairline, with "WeLinc Logistics" on the left and "EST. 2018" in mono on the right under it. No Privacy or Terms links.
- **AC-2**: The tiles are **L1 with N3 text**, three to a row (384 px each, 24 px gaps) from the top left, under a heading "Your systems" with the count of systems beside it (no other line). Systems are always ordered BMS, VMMS, VRMS and only those you hold a role in are shown (never greyed). Each tile: the **J1** system icon (the drawn ticket, gauge and wrench as built today), the code large, the full name as one line uppercase IBM Plex Mono label at 11.5 px, and the role alone at the bottom (`Admin` when you administer that system, else your real role name; no "Your role:" label). There is no description line and no "Open BMS" row. **P5**: each tile carries its number key at the top right, numbered in the shown order (the systems, then the Suite management tile, so Suite management is 2 with one system and 4 with three). Pressing that digit on the launcher opens that tile exactly as a click on it would (the same launch and skip rules, AC-10), unless focus is in a text field, a menu or dialog is open, a modifier key is held, or the key is repeating (`event.repeat`); a digit with no tile does nothing. The role on a tile: `Admin` when any role you hold there is `ADMIN` (a temporary one included), else the name of your first role there in catalog order, temporary roles shown by name like any other. The count beside "Your systems" counts system tiles only. The small mono labels "Systems" and "Admin" show only when you have both system tiles and the Suite management tile.
- **AC-3**: Anyone who administers something (a suite admin, or `ADMIN` in any system) gets a **Suite management tile** after the systems, under the "Admin" label: a white tile like the others (never navy), the **S5** team tree icon (a navy node over three, the middle one gold, as `gen69.py` draws it), "Suite management" in full, the label "People, roles and access", and at the bottom which systems it covers: "For VRMS", "For VMMS and VRMS", or "For BMS, VMMS and VRMS" for a suite admin. It links to `/admin` (a route inside the portal: no launch, by click or by key) and shows **no count**. The "For …" line names only systems you administer, never one where you hold only another role. With three systems it wraps to its own row under the "Admin" label. Someone with no admin role sees no Suite management tile.
- **AC-4**: For every person on the Round 69 boards, the whole launcher fits 1440×900, 1280×720 and 1024×768 with no page scroll. The phone layout (under 768 px, recorded by `/develop` on 2026-11-26): the band is 64 px with the account circle alone (no name or chevron) and no M1 mark, "Operations Workspace" hides under 640 px, the tiles stack one per row as a row each (the 44 px icon at the left; the code, the full name, which may wrap, and the role beside it), the number key caps hide, the cartons stand 80 px tall in their own room above the hairline, and the page may scroll.
- **AC-5**: The screen choice (`screenForAnswer` in `src/lib/auth.ts`) follows these rules, in order after the existing `APP_NOT_ALLOWED`, phone only and `next` rules: one web system, no `ADMIN` there, not a suite admin, and no `error` → straight into that system; no systems and a suite admin → straight into Suite management (`/admin`, which opens on People); no systems and not a suite admin → No access; everyone else → the launcher. A suite admin who holds a temporary system role reaches the launcher with that system and the Suite management tile.
- **AC-6**: welinc-auth adds `suiteAdmin: boolean` (required) to the launcher answer on every route that answers it (`GET /auth/sso`, `POST /auth/login`, `POST /auth/login/verify-email`). Contract 0001 gets an additive Changes line; `docs/openapi.json` is regenerated; the portal's `LauncherAnswer` gains the field.
- **AC-7**: *(Removed 2026-11-26.)* There is no `GET /auth/admin/summary`. The route built on welinc-auth's `feat/portal-redesign` (its service, controller entry and tests), the portal's `adminSummary` hook and its tests, and the route's contract 0001 Changes line and section 16 row come out before the welinc-auth PR, so it never reaches `development`.

*Motion*
- **AC-8**: **Arrival A3** (`R66A3`) plays only right after a sign in through the portal's own form in this tab (the password form, or the email code step that finishes it). A sign in that comes back by a full page load (an app initiated login, an SSO return) plays no arrival. The flag is in memory, read once by the launcher, and cleared when any other screen shows. The sign in fades out (0.25 s), then the tiles slide in from the left one at a time (0.45 s each, 40 px, about 0.09 s apart, the board's easing), each number key arriving with its own tile; the heading and labels fade in. Nothing else on the launcher moves. A reload, the back button, or Home from Suite management shows the tiles in place. A suite admin who skips the launcher (AC-5) gets a plain fade into Suite management, and the redirect clears the flag, so a later Home visit plays nothing. Keys pressed while the arrival plays are ignored until the last tile lands.
- **AC-9**: *(Replaced 2026-11-26.)* The launcher has no loop and no moving vehicles, road or cartons; the only launcher motion is AC-8 and AC-10.
- **AC-10**: **A random launch.** Each system tile is a real link (`href` is the system url). A left click or its number key plays one launch picked at random from **Launch 2** (dock door: the shutter rolls up and the truck pulls away, `R29LaunchDock`), **Launch 3** (route bar, the truck starting right of the garage, `R31LaunchRoute`, as built) and **Launch 4** (loading: cartons go into the van, the doors close and it pulls away, `L28MLoad`), never the same one twice in a row. Each is cut to at most 900 ms, keeping the board's key moment. The handler never calls `preventDefault`: the launch plays while the browser fetches the system, and the page unloads whenever the system answers. The launch is skipped when the event is already `defaultPrevented`, a modifier key is held (Ctrl, Cmd, Shift, Alt) or the button isn't the left one, so new tab clicks behave normally. The Suite management tile plays no launch (it is a route inside the portal). A 900 ms timer always removes the launch overlay, whether or not the animation reports its end (a hidden tab may never fire `animationend`); if the system is slow, the page simply waits on the launcher. On `pageshow` with `persisted` (Back from the system) the overlay is reset, so a frozen scene never shows.
- **AC-11**: With `prefers-reduced-motion: reduce`, the arrival is a fade with no movement and every launch becomes a fade of at most 200 ms before the navigation completes. Under 768 px the same reduced rules apply, so a phone gets no slide, on purpose, unless `/develop` records otherwise with the phone layout (AC-4).
- **AC-12**: All portal motion is CSS (keyframes and transitions on spec 0016's motion tokens, plus SVG `animateMotion` for the sign in trucks, as the board draws them). The `motion` package, the `LauncherMotion` lazy chunk and its `motion/` module come out; no animation library is added (`tw-animate-css` stays for the shadcn parts). Durations, distances, easing and stagger are copied from the boards (`R66A3`, `R29LaunchDock`, `L28MLoad`, `R31LaunchRoute`, `R47Quiet`) into one constants module, not chosen anew. Launch scenes are inline SVG, `aria-hidden`, and never show live data. Launch 3 is rebuilt in CSS from `R31LaunchRoute`, not kept on Motion.

*Sign in and forgot password*
- **AC-13**: Sign in matches **S27d Quiet** (`R47Quiet`): the drawn map of the WeLinc area traced from OpenStreetMap runs under the whole page (shores, lakes, roads and city dots dimmed to 42%), with the twelve trip runs brighter and wider (90%, 3.8 units) and the trucks driving them, and labels for the three garages (Marikina, Sta. Rosa, Pulilan) and the drop points only (no town names or road shields); the drop labels are exactly those in `drawnmap.json`'s label list, and under 768 px only the three garage labels show. The form sits on S27's navy glass panel. Copy, from the board: "#HASSLEFREE TRANSPORT SOLUTION" over "WeLinc Logistics Operations Workspace", then "Bookings, maintenance and repairs for the whole fleet, in one place."; the form "Sign in", "Use your WeLinc work email.", Work email, Password, Forgot password?, Sign in; under it "No account yet? Ask your admin to add you. You'll get an email to set your password."; at the foot "© 2026 WeLinc Logistics · © OpenStreetMap contributors" (the credit ODbL asks for). The map is one still layer; only the trucks move, and they park with reduced motion and pause while the tab is hidden. The map and trucks are decoration (static data, `aria-hidden`). The tab title is "Sign in · WeLinc Logistics Operations Workspace".
- **AC-14**: Forgot password is four steps (Round 31's steps and copy, approved as is) in the same glass panel over the AC-13 map; its exact look follows the S27d boards for the code step and forgot password once they are drawn, and until then reuses the sign in panel's fields and buttons: (1) email; (2) the 6 digit code, valid 10 minutes, resend after 60 s; (3) new password with the strength box listing welinc-auth's four password rules, a **Confirm new password** field and a "Passwords match" line; (4) done, centred, saying the reset signed out every session. Fields on the sign in page (sign in and forgot password) show focus as a navy border with a soft navy ring, never gold.
- **AC-15**: Messages on the sign in page: a sign out (`reason=logout`, or a sign out in another tab) shows the app's `Toast` as **success** (green) at the top of the form panel; a session ending (`reason=ended`, `idle`, `maxage`) shows the same toast as **warning** (amber) that stays until closed (`duration: Infinity`, no time bar), carrying today's wording for each reason. `noticeFor` changes its tone for `ended`, `idle` and `maxage` from `info` to `warning`, and for `logout` to `success`. These toasts come from a second sonner `Toaster` mounted only inside the sign in page's form panel with `position="top-center"`; the app's main Toaster keeps spec 0016 AC-11's placement. Errors that stop a sign in (`LOGIN_REQUEST_EXPIRED`, `LOGIN_STATE_INVALID` and the other `error=` codes) stay inline above the form.
- **AC-16**: **Signed out** and **No access** screens use the AC-13 page with their content centred in the glass panel, like forgot password step 4. No access names no systems.

*Suite management shell*
- **AC-17**: The admin area is called **Suite management** in the sidebar title, the breadcrumb and the switcher card. Under the title sits your role ("Suite admin" or "VRMS admin") in plain muted white, never gold (`Shell20`).
- **AC-18**: The sidebar footer is a darker strip holding the ///L mark and "WeLinc Logistics" on one line with the collapse button at its right. There is no full width Collapse row, no edge handle and no Back to home row; the logo goes Home (`/admin` when you have no launcher, AC-20). Collapsed, the strip holds only the expand button, centred (the double chevron pointing right, labelled "Expand sidebar"); the mark and name hide, as on `Shell20`. The collapsed sidebar's logo B is the header tile above, not the footer.
- **AC-19**: The account menu (avatar, top right, in Suite management and on the launcher alike) holds **Your profile** and **Sign out** only. Your profile shows only once S23's profile route exists (one constant, `PROFILE_PATH` in `src/lib/routes.ts`, `null` until S23); until then the menu holds Sign out alone.
- **AC-20**: The system switcher (grid button, top right, `Switcher16`) opens wide cards, one per row: the Suite management card first and ticked ("You are here", subtitle "Users and permissions"), then only the systems you hold a role in, each with your role as a tag and its url from the held launcher answer. The role line under the Suite management title (AC-17) comes from `/auth/admin/me`; if the two disagree (a role changed mid session), the held answer refreshes on the next session check. The popover title has a **Home** pill with a house icon. Whether the switcher and the Home pill show depends on the held answer having at least one web system (`systems.length > 0`), never on `suiteAdmin`: a suite admin with no system roles has no launcher (AC-5), so they get no switcher, no Home pill, and the logo goes to `/admin`; a suite admin with a temporary system role keeps both. The account menu holds Sign out (and Your profile, AC-19).
- **AC-21**: The People filter is one Filter button opening the `Filter18` popover. It replaces today's system select. Status is checkbox chips (no coloured dots): **Needs attention**, **Locked**, **Pending** (setup pending), **Active** and **Inactive**. System and role are accordion rows (the box picks the whole system, the row opens its roles, one open at a time, 180 ms fold), one row per system you admin (all three for a suite admin, one for an admin of one system), in VRMS, VMMS, BMS order. Roles are soft tint chips with a tick, in catalog order. A system row's pill reads "Everyone" (whole), the role's name (one role), "N roles" (some) or the system's count (off). Ticking every role of a system turns back into the whole system. Every status chip, system row and role chip shows its count from AC-21b. The picks are a draft: the list changes only on **Show N people**, and "N" is AC-21b's `total` for the draft. The header has Clear all; the footer says "N filters on" (ticked status chips plus systems that are not off). Applied picks live in the address as `status=` and `access=` (AC-21a's values), so reload, back and a shared link keep them. Every group call sends them, and `?system` keeps its spec 0017 meaning (the scope). While the counts load, each count shows a dash, and so does Show's number. If they fail, the dashes stay and Show still applies the picks.
  - *The draft*: opening the popover starts the draft from the applied picks; Esc or a click outside discards it; Clear all clears the draft only; Show with N = 0 is disabled and reads "No one matches"; Show with an unchanged draft just closes. "N filters on" counts each ticked status chip and each system that is not off (whole or partial counts 1; roles never count on their own), and the Filter button's badge shows the applied count from the same function.
  - *`?system`*: the popover writes only `access=`, never `?system`. When the address already carries `?system` (an old link), the popover shows only that system's row and the facets call sends `system`. Add a user preselects a system only when `access` is exactly one whole system (else as today).
  - *Groups under a filter*: while any `status` or `access` filter is on, group sections with 0 people hide; when every group is empty, a filtered empty state shows with **Clear filters** in place of Add a user (today's empty branch, keyed on `q || system`, also checks `status` and `access`).
  - *Search*: the facets call uses the applied `q` from the address, not text still being typed.
  - *Stale address values*: before any call, the portal drops `status` values that aren't chip values and `access` items whose system you don't admin or whose role the catalog doesn't list (as `parseListSystem` does), and rewrites the address with `replace`. The server stays strict.
  - *Facet failures*: a 429, `ADMIN_CODE_REQUIRED` or an aborted call leaves the dashes with no toast. Each call carries a sequence number, and an answer older than the newest sent is ignored. Show's N is a union of people, never a sum of chip counts; the portal never adds counts.
- **AC-21a**: welinc-auth's `GET /auth/admin/users` gains two additive filters. (1) `access`: a comma list where each item is a whole system (`VRMS`) or one role of it (`VMMS:MECHANIC`, written `SYSTEM:ROLE`), read as any of them. Checked in this order: an empty item, a malformed one, lowercase or whitespace is 400 `VALIDATION_FAILED`; more than 40 items or 600 characters is 400 `VALIDATION_FAILED`; an unknown system or role is 400 `UNKNOWN_ROLE`; a system outside the caller's scope is 403 `NOT_ADMIN_OF_SYSTEM`, and so is one other than `system` when `system` is sent (`system` stays the scope and `access` narrows inside it). Sending `access` together with the old `role` is 400 `VALIDATION_FAILED` (`role` stays for old callers). The server then normalizes: duplicates go, a whole system absorbs its own role items, items sort. It never turns "every role ticked" into the whole system (the popover does that). Holding a role means what it means in the list today (`roles: { some }`, temporary grants included as the list includes them), with no new expiry rule. Every catalog role is an item, `ADMIN` included. (2) `status` accepts two more values beside today's six: `ATTENTION` (exactly `groupWhere('attention')`) and `ACTIVE_GROUP` (exactly `groupWhere('active')`), never a copy of those rules. Statuses overlap on purpose: `ATTENTION` includes everyone `LOCKED` and `SETUP_PENDING` (which leaves out locked people) shows, plus pending deletion. `PENDING_DELETION` and `EMAIL_NOT_VERIFIED` stay valid values with no chip. The rules combine as any of inside `access`, any of inside `status`, then AND across search, `status`, `access` and `group`. Without `system`, each row still lists the person's roles in every system in the caller's scope. The cursor fingerprint (`filterKey`) includes the normalized `access` (items sorted), so a cursor reused with other picks answers `INVALID_CURSOR`. `counts` follow every filter, as today.
- **AC-21b**: welinc-auth adds `GET /auth/admin/users/facets` (SSO cookie, any admin, the same step up and read scope as the list, its own limit of 120 a minute per admin, counted per welinc-auth container, 429 `RATE_LIMITED` with `Retry-After`). It takes `system?`, `q?`, `status?` and `access?`, validated as AC-21a, and nothing about group, sort or paging: any other parameter (`group`, `sort`, `role`, `cursor`, `limit`) is 400 `VALIDATION_FAILED`, so the portal never forwards them. Every request counts toward the limit, those later refused for a filter error included, as lookup and the email check count. It answers counts only, no names: `{ total, status: { ATTENTION, LOCKED, SETUP_PENDING, ACTIVE_GROUP, INACTIVE }, systems: [{ system, count, roles: [{ code, count }] }] }`. `systems` lists only the systems in scope, in VRMS, VMMS, BMS order, with roles in catalog order (zeros included). `total` counts under every filter. Each facet counts under every filter except its own: the status counts ignore `status`, and the system and role counts ignore `access`. That way ticking Mechanic never zeroes Driver. This means a role count also ignores other systems' picks, which is right for any of; nobody should "fix" it. Each status count uses the same `statusWhere` or `groupWhere` as the list, and search uses the list's `searchWhere` with the caller's systems. Every count is distinct people, never role rows: a system's count is "holds any role there" (not the sum of its role counts), and a person with two roles in one system counts once there and once in each role. People with no role (in a suite admin's scope) count in `total` and the status counts but in no system or role count. Every status key is always present and every count is a whole number, zeros included; a role not in the catalog is absent. It runs as parallel Prisma counts built from the list's own where helpers, so no rule is ever written again in SQL: one count for `total`, one per status chip, one per system in scope, and one `groupBy` on `user_roles` by system and role (its unique index on person, role and system makes a row count a count of people). The portal asks when the popover opens and 250 ms after each draft change, cancelling any older call still running.
- **AC-22**: Add a user is the one screen dialog on `AddUser15`: email first, with the field's own icon as the check (red ! not an email, a spinner while checking, a navy tick when free, a person icon plus the existing account card when the email has an account); one **Full name** field; **Contact number** optional (welinc-auth's create request gains an optional `contact`, max 100 characters, stored in the existing `users.contact` column); system cards for a suite admin (none for a system admin, whose system is fixed); role cards with a one line meaning; no Temporary switch; one system per add. An existing account turns the dialog into "give access" for that person (today's `attachExisting`). The name search in today's dialog goes: the email is the only way in, and `users/lookup` stays in the API. The dialog checks only an email that passes the format check, 400 ms after typing stops, cancelling any older check still running.
- **AC-23**: welinc-auth adds `GET /auth/admin/users/email-check?email=&system=` (SSO cookie, any admin of `system`, the same step up rule as `users/lookup`, but its **own** rate limit counter of 60 a minute per admin, not lookup's 30). The email is trimmed and lowercased, and only the whole email matches (never partial). It answers one `status`, taking the first that applies in this order: `inactive` (deactivated or deleted, can't be added here), `suite-admin` (can't take a system role; **only a suite admin sees this**, a system admin gets `existing` with no systems list, so the route never tells them who is a suite admin), `in-system` (already holds a role in `system`), `existing` (can be given access), `free`. For `existing` and `in-system` it adds `name` and `picture`, and the systems list only where the caller is an admin.
- **AC-24**: The steering wheel wait (Round 29 option C, picked Round 33) replaces the spinner inside every busy button (Save, Send code, Sign in, Review and save) and the small loading spot when a list reloads or loads more. A page's first load keeps its skeletons. It stops spinning (static wheel) under reduced motion and keeps its `aria-busy` and label.

*Session warning*
- **AC-25**: In the portal and in web-vrms, the signing out soon **banner** is replaced by a warning **toast** with the same timing and rules as spec 0016 AC-12, AC-12a and AC-12b (check 120 s before the cutoff, reschedule when it moved, the last check before leaving, the cross tab sync, the failure retries). The toast is a `SessionToast` component that reads the session store and ticks its own countdown, fired through `toast.custom` with the fixed id `session-warning`, `duration: Infinity` and `dismissible: false`; the `Toast` component gains a variant with no close button and no time bar, and the limit of 3 skips this id. It shows independently of the offline banner (both can show; 0016 AC-12b's "under the offline banner" rule is dropped). In web-vrms the change touches `src/lib/session/*` and `src/components/feedback/*`; if its `Toast` lacks the variant, it gains the same one. Idle: title "Still there?", body "You'll be signed out in 1:45 for inactivity." with a live countdown, action **Stay signed in**. The 12 hour end: title "Your session ends at 2:30 PM" (time only, `h:mm a` in the browser's locale and time zone, from `sessionAbsoluteExpiresAt`), body "This is the 12 hour limit. Sign in again to keep working.", no action. The toast stays until Stay signed in succeeds, a check finds the cutoff moved, or the tab leaves; it has no close button and no time bar, and it never counts toward the limit of 3. It uses `role="status"`, never takes focus, keeps the ticking time `aria-hidden`, and announces once on open and again at 30 s, as AC-12 there. The offline banner stays a banner and shows alongside it.

*Other screens and brand*
- **AC-26**: Any unknown address (including an unknown `/admin/<view>`) shows the "Wrong turn" 404 page from Round 34, with a way Home; `/portal` keeps its redirect to `/`. A person link to someone who doesn't exist keeps S19's in pane not found state. The hosting already answers `index.html` for every unknown path (as for `/admin/*`), so the portal's router decides.
- **AC-27**: welinc-auth's code emails (password setup, password reset, sign in code, email change confirm) share one branded layout from the Round 34 reset email: the ///L mark (logo A, gold on the navy header as `R35LogoPlaces` places it, as a PNG sent as a CID attachment through nodemailer's `attachments` with a `cid`, never SVG, a data URI or a remote image; its `alt` is the "WeLinc Logistics" wordmark in text), a navy header, the code large in a monospace font, the existing wording and lifetimes, and a plain text part with the same content. Snapshot tests cover the HTML and the text part; a manual check (a `/test` item) confirms Gmail web, Gmail on Android and Outlook web.
- **AC-28**: `public/favicon.svg` is the ///L mark in badge B (Round 35); the Vite logo is gone. Logo by place: A on navy, B alone at small sizes (favicon, collapsed sidebar), F on white and in print. Every route sets the tab title as the most specific part first, then "WeLinc": "Sign in · WeLinc", "Forgot password · WeLinc", "Home · WeLinc", "People · Suite management · WeLinc", "Maria Santos · People · WeLinc" ("People · Suite management · WeLinc" while the person loads, "Person · People · WeLinc" with no name), "Page not found · WeLinc" (inside `/admin` too).

*Checks*
- **AC-29**: Every screen above matches its board within the allowed differences (forgot password, until its S27d boards exist: the `R47Quiet` panel's fields and buttons, with Round 31's steps and copy) (handoff 2026-11-24: Plex Mono for the boards' JetBrains Mono, Inter for Inter Tight, spec 0016's later token values, shadcn parts, real data lengths), compared from the board's values and the running page's computed styles and text. axe finds no serious issue at 1280 px and 375 px, no page scrolls sideways, and lint, typecheck, builds and tests pass in every touched repo.

## Decision

**Chosen option**: Option 2: rebuild the portal screens from the boards in milestones, motion last, on the existing tokens and components, with CSS for all motion (no animation library, since the 2026-11-26 update) and additive welinc-auth routes.

Build the picked boards on top of spec 0016's tokens and components, close the data gaps with small additive welinc-auth changes (`suiteAdmin`, `/auth/admin/users/email-check`, the People list's `access` filter and two `status` values, `/auth/admin/users/facets`), and add motion last so a static launcher can ship if time runs short.

**Implementation skills**: `tailwind-4-docs` (`lombiq/tailwind-agent-skills`, `.claude/skills/tailwind-4-docs/`) · `shadcn` (`shadcn-ui/ui`, `.claude/skills/shadcn/`) · `vercel-composition-patterns` and `vercel-react-best-practices` (`vercel-labs/agent-skills`, `.claude/skills/`) · `ask-sonner` (`.claude/skills/ask-sonner/`, the toast work) · `nestjs-best-practices` and `prisma-client-api` (`.claude/skills/`, the welinc-auth routes) · offer `emil-design-eng` once the motion milestone is built (ask first, per AGENTS.md)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Board index (copies in `boards/`)

| Board | Settles |
|---|---|
| `R69Victor`, `R69Danilo`, `R69Corazon`, `R69Felicidad`, `R69Armando` | The launcher for each kind of person: Q1 band, M1 mark, L1 tiles with N3 text three to a row, P5 keys, the S5 Suite management tile, K3a cartons and the E1g line, the 1440×900 fit (AC-1 to AC-4) |
| `R66A3` | Arrival A3 and its timing (AC-8) |
| `R29LaunchDock`, `R31LaunchRoute`, `L28MLoad` | Launches 2, 3 and 4 (AC-10, AC-12) |
| `R47Quiet` | Sign in S27d Quiet, the map, the copy (AC-13) |
| `R30Launcher`, `R37LineArt`, `R31ArrTruck`, `R32Sequence`, `R33Sequence`, `R34Sequence`, `R37SignIn` | History: the launcher, band, loop, Arrival 2 and sign in this update replaced |
| `R32Forgot1` to `R32Forgot4` | The four forgot password steps, navy focus, "Confirm new password" (AC-14) |
| `R36OutToast2`, `R36EndedToast2` | Signed out and session ended toasts (AC-15) |
| `R34NoAccess` | No access on the split, no system names (AC-16) |
| `Shell20` | Suite management sidebar, title, role line, footer (AC-17, AC-18) |
| `Switcher16` | Account menu and system switcher (AC-19, AC-20) |
| `Filter18` | Filter popover, option 2 soft tint chips, the counts on every chip and row (AC-21, AC-21a, AC-21b) |
| `AddUser15` | Add a user (AC-22) |
| `R33Wait`, `R29SpinSteer` | Steering wheel wait (AC-24) |
| `Motion18` | Save bar, toasts, dialogs and states in motion (reference for AC-24, AC-25) |
| `R34NotFound` | Wrong turn 404 (AC-26) |
| `R34Email` | Code email layout (AC-27) |
| `R35LogoPlaces` | Logo A, B and F by place (AC-28) |

Board notes text wins over the handoff where they differ only on wording; a picked option wins over the board's default toggle (for example `Shell20`'s footer is option 5, mark plus "WeLinc Logistics"; `Switcher16`'s area name is "Suite management", not its default).

## Feature design

**Data model sketch**: no schema change. The three new answers are computed from existing tables (`users`, `user_roles`, `suite_admins`, deletion requests, temporary grants), with the same queries People's counts and the lookup already use.

**Screen choice** (AC-5), as a decision table, applied after the `APP_NOT_ALLOWED` and `next` return path rules (both win first, unchanged); `from=` only marks the current card, as spec 0007:

| `systems` (web) | admin of one | `suiteAdmin` | Screen |
|---|---|---|---|
| 0 (phone only roles) | any | false | phone only (unchanged) |
| 0 | n/a | false | No access |
| 0 | n/a | true | straight into Suite management (`/admin`) |
| 1 | no | false | straight in (no `error`) |
| 1 | no | true | launcher, the system tile and the Suite management tile |
| 1 | yes | any | launcher, the system tile and the Suite management tile |
| 2 or 3 | any | any | launcher (the Suite management tile when they administer anything) |

**API surface** (all welinc-auth, through the gateway, SSO cookie):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/sso`, `/auth/login`, `/auth/login/verify-email` | GET, POST, POST | unchanged | the launcher answer plus `suiteAdmin: boolean` | unchanged | unchanged |
| `/auth/admin/users/email-check` | GET | `email` (req, a valid email; trimmed, lowercased), `system` (req, a system the caller admins; a suite admin may pass any) | `{ status: 'inactive' \| 'suite-admin' \| 'in-system' \| 'existing' \| 'free', name?, picture?, systems? }` | any admin of `system`, step up as `users/lookup`, own limit 60 a minute per admin | 400 malformed email, 403 not admin of `system`, 429 |
| `/auth/admin/users` (existing create) | POST | adds optional `contact` (string, max 100) | unchanged | unchanged | 400 too long |
| `/auth/admin/users` (existing list) | GET | adds `access?` (comma list of `SYSTEM` or `SYSTEM:ROLE`, any of, at most 40 items and 600 characters); `status` also takes `ATTENTION` and `ACTIVE_GROUP` | unchanged | unchanged | 400 `UNKNOWN_ROLE`, 400 `VALIDATION_FAILED` (`access` with `role`, too long, malformed), 403 `NOT_ADMIN_OF_SYSTEM` (an `access` system outside scope or other than `system`) |
| `/auth/admin/users/facets` | GET | `system?`, `q?`, `status?`, `access?` (as the list); any other parameter is 400 `VALIDATION_FAILED` | `{ total, status: { ATTENTION, LOCKED, SETUP_PENDING, ACTIVE_GROUP, INACTIVE }, systems: [{ system, count, roles: [{ code, count }] }] }` | any admin, step up as the list, the list's read scope, own limit 120 a minute per admin, every request counted | as the list's filter errors; 401, 403 `ADMIN_CODE_REQUIRED`, 429 `RATE_LIMITED` |

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Launcher band | Name and initials on the account button | `answer.user.name` (initials as `lib/launcher.ts` does today) |
| Launcher tiles | Code, full name, url, roles | `answer.systems[]` (`system`, `name`, `url`, `roles[].code`, `roles[].name`); the label is `name` set in uppercase by CSS, so the text stays readable to screen readers |
| Launcher tiles | Admin vs real role name | `administers(system)` (any `ADMIN` role, temporary included) else the first of `roles[]` in catalog order, by `name` |
| Launcher tiles | Number keys | the tile's position in the shown order (systems BMS, VMMS, VRMS, then Suite management) |
| Suite management tile | Shown or not | `answer.suiteAdmin` or `administers()` on any system |
| Suite management tile | "For …" systems | all three for `answer.suiteAdmin`, else the systems where `administers()` is true, in BMS, VMMS, VRMS order |
| Screen choice | Suite admin | `answer.suiteAdmin` (AC-6) |
| Arrival A3 | "Right after a sign in" | an in memory flag set by `Login`'s `onSignedIn` and the code step, read once by the launcher, never stored |
| Launch | Which scene plays | `Math.random()` over Launches 2, 3 and 4 minus the last one played; the last one's id (`2`, `3` or `4`) is kept in `sessionStorage` under `welinc.portal.lastLaunch`, since the page unloads after every launch; reads and writes are wrapped so a refused storage (private mode) falls back to a module variable and never blocks opening a system |
| Arrival, launches, sign in trucks | Durations, distances, easing | the CSS constants module, copied from the boards (AC-12) |
| Sign in map | Shores, roads, runs, garage and drop labels | a static SVG built once from `docs/context/vrms/portal-redo-boards/gen/drawnmap.json` (the board's drawn map), checked in to the portal |
| Footer | "EST. 2018" | static copy |
| Switcher | Systems, urls, roles | the held launcher answer (the session watch store already holds the latest one; Admin calls `/auth/sso` once when empty, spec 0016 AC-12b) |
| Switcher | Role under the Suite management title | `/auth/admin/me` (`suiteAdmin`, `adminOf`), as today |
| Filter footer | "Show N people" | `GET /auth/admin/users/facets` `total` for the draft picks |
| Filter chips and rows | Each status, system and role count | `GET /auth/admin/users/facets` (`status`, `systems[].count`, `systems[].roles[].count`) |
| Filter rows | Which systems and roles are offered | the systems in the viewer's admin scope (`/auth/admin/me`: `suiteAdmin`, `adminOf`), their roles and names from `/auth/systems` in catalog order |
| People list | The applied filters | `status=` and `access=` in the address, sent on every group call |
| Add a user | Email status, name, picture, systems | `GET /auth/admin/users/email-check` |
| Add a user | Role cards' one line meaning | the role catalog's `description` (`/auth/systems`) |
| Idle toast | Countdown | the held cutoff and clock gap (`lib/sessionWatch`) |
| 12 hour toast | "ends at 2:30 PM" | `sessionAbsoluteExpiresAt` in the browser's local time |
| Sign in toasts | Which message | `reason` in the address (`noticeFor` in `lib/auth.ts`) |
| Tab titles | Person's name | the loaded person in the People pane; "People" until it loads |
| Code emails | Name, code, lifetime, portal host | `passwordCodeEmail` and its siblings' existing inputs |

**Key invariants**:
- The trucks, cartons and scenes are decoration: no request, plate, count or place in them comes from data.
- Nothing about the session or the arrival flag is written to `localStorage`, `sessionStorage` or the url (spec 0003 AC-36). The one stored value is the last launch's scene id (AC-10), which says nothing about the person or session.
- The launcher never triggers the admin step up prompt.
- Every card stays a working link without JavaScript animation; a motion failure never blocks opening a system.
- Gold stays rare: the logo mark, the band's bottom fade, the S5 icon's middle node, the cartons' tape and `commit` buttons only; never text on white. Orange and blue go only on drawn vehicles.

**Security model**:
- No admin route skips the step up: with the summary route removed (AC-7), the launcher calls nothing under `/auth/admin`.
- `/auth/admin/users/email-check` reveals whether an exact email has an account only to an admin, only after step up, rate limited with the lookup limiter, and never by partial match. Systems are listed only where the caller is an admin.
- `suiteAdmin` in the launcher answer tells the person something about themselves only.
- The People list's `access` filter and `/auth/admin/users/facets` never widen the read scope: an `access` system outside it is refused (403), and facet counts cover only people the list would show that caller. The facets route needs the step up like the list, since a count per role under a search can narrow down to one person. Its search uses `searchWhere` with the caller's systems, so a role name from a system you don't admin never counts anyone.
- Code emails embed the logo inline (no remote image, no tracking pixel).

**Configuration required**: none. No new env vars.

**Critical test scenarios**:
- A suite admin with one temporary non admin VRMS role signs in and lands on the launcher with the VRMS tile and the Suite management tile ("For BMS, VMMS and VRMS"), verifies **AC-3**, **AC-5**, **AC-6**
- A suite admin with no system role signs in and lands on `/admin` People with no launcher flash, no switcher and no Home pill, verifies **AC-5**, **AC-20**
- A mechanic with only VRMS goes straight into VRMS with no launcher flash, verifies **AC-5**
- The suite admin with a temporary VRMS role opens Suite management: the switcher and the Home pill show, and Home returns to the launcher, verifies **AC-20**
- Press 4 on Armando's launcher: Suite management opens with no launch; press 9: nothing happens, verifies **AC-2**
- The launcher makes no request under `/auth/admin` and never shows a code prompt; `GET /auth/admin/summary` answers 404, verifies **AC-7**
- Press 2 on Danilo's launcher: VMMS opens with a launch; press 2 while typing in a field or with Cmd held: nothing happens, verifies **AC-2**, **AC-10**
- The email check with a partial email answers 400, a system admin sees no systems they don't admin, verifies **AC-23**
- The email check for a suite admin's address, asked by a system admin, answers `existing` with no systems; a deleted person answers `inactive`, verifies **AC-23**
- A suite admin ticks VRMS whole plus VMMS Mechanic and BMS Driver: the list shows anyone in VRMS or holding either role; ticking VMMS Mechanic leaves BMS Driver's count unchanged; Show's number equals the summed group counts after applying, verifies **AC-21**, **AC-21a**, **AC-21b**
- A VRMS admin sends `access=VMMS`: 403; `access` with `role`: 400; a cursor from other picks: `INVALID_CURSOR`, verifies **AC-21a**
- `status=ATTENTION` returns exactly the Needs attention group, and `ACTIVE_GROUP` includes an unverified email, verifies **AC-21a**
- `access` with a lowercase item, an empty item, or 41 items: 400 `VALIDATION_FAILED` each; `VMMS,VMMS:MECHANIC` and `VMMS:MECHANIC,VMMS:MECHANIC` (a duplicate) are accepted and normalized, with the same cursor key as `VMMS` and `VMMS:MECHANIC`, verifies **AC-21a**
- One person with two VMMS roles: VMMS count 1, each role count 1; a suite admin's person with no role counts in `total` and status only; the facets `total` equals the list's summed group `counts` and `status.ATTENTION` equals `counts.attention` under the same filters, verifies **AC-21b**
- A VRMS admin's facets list only VRMS, and a search for a VMMS role name counts no VMMS only person; facet status counts ignore `status`, verifies **AC-21b**
- Reload People with picks applied: the same picks and list come back from the address; a link with a removed role or a system you no longer admin loads with that item dropped and the address rewritten, verifies **AC-21**
- Esc discards the draft; with `status=LOCKED`, empty groups hide; with nothing matching, Clear filters shows, verifies **AC-21**
- Sign in through the form: the tiles slide in one by one with their keys; reload: tiles in place, nothing moves, verifies **AC-8**, **AC-9**
- Open systems ten times in a row: each launch is one of 2, 3 or 4, never the same twice running, and each ends within 900 ms, verifies **AC-10**
- Cmd click VRMS opens a new tab and the launcher stays still, verifies **AC-10**
- Reduced motion on: tiles fade in, launches are a 200 ms fade, the sign in trucks are parked, verifies **AC-11**, **AC-13**
- The built portal has no `motion` package in `package.json` or any chunk, verifies **AC-12**
- Idle for 28 minutes in Admin: "Still there?" shows with the countdown; Stay signed in closes it in every portal tab; in web-vrms the same toast replaces the banner, verifies **AC-25**
- Open `/admin/nope`: Wrong turn page, verifies **AC-26**
- The 1440×900, 1280×720 and 1024×768 fit for every Round 69 person, verifies **AC-4**

## Build plan

Facade per the VRMS UI refresh override: each milestone builds the screens on the data the portal already has, and the welinc-auth additions land just before the screen that needs them. Motion is last so it can slip without leaving anything half built.

0. Copy every board named in this spec into `boards/` as `.dc.html` (done with the spec, or first thing if missed), satisfies **AC-29**
1. *(built; step 9 takes the summary route out)* welinc-auth: `suiteAdmin` on the launcher answer, `GET /auth/admin/summary` (with the test that a session without the sign in code passes), `GET /auth/admin/users/email-check` with its own limiter, optional `contact` on create, the shared code email layout with the CID logo and snapshot tests; contract 0001 Changes line, `npm run openapi`, tests; branch and PR into `development`, satisfies **AC-6**, **AC-7**, **AC-23**, **AC-27**
2. Portal foundations: favicon and logo by place, tab titles on every route, the 404 page, the steering wheel wait in `Button` and the list loaders, satisfies **AC-24**, **AC-26**, **AC-28**
3. Session toasts in both apps: the idle and 12 hour toast replacing the banner in the portal and web-vrms (the timing modules stay, only the surface changes), and the sign in success and warning toasts, satisfies **AC-15**, **AC-25**
3a. welinc-auth, on the same `feat/portal-redesign` branch before its PR: the People list's `access` filter and the `ATTENTION` and `ACTIVE_GROUP` statuses (in `people-page.ts`, beside `statusesWhere`), `GET /auth/admin/users/facets`, the contract 0001 Changes line (section 10a and the section 16 row), `npm run openapi`, tests, satisfies **AC-21a**, **AC-21b**
4. Suite management shell: naming, sidebar footer, account menu, switcher from the held answer; then the filter popover on the facets route and the Add a user dialog with the email check, satisfies **AC-17** to **AC-23**
5. Sign in, forgot password, Signed out and No access on the new split, satisfies **AC-13**, **AC-14**, **AC-16**
6. *(built, superseded: steps 10 to 12 rework it, and its AC-1, AC-2, AC-3 and AC-11 text is replaced)* Static launcher: band with the line drawing and parked trucks, cards, strip with counts, the screen choice fix, the 1440×900 fit, phones, satisfies **AC-1** to **AC-5**, **AC-11** (the parked scene)
7. *(built, superseded: steps 10 to 12 replace it, and its AC-8 to AC-12 text is replaced)* Motion: add `motion` (lazy, `LazyMotion` plus `domAnimation`), Arrival 2, the loop with pause on hidden, Launch 3, reduced motion, check the Admin chunk has no motion import, satisfies **AC-8** to **AC-12**
**Rework from the 2026-11-26 update** (steps 1 to 7 were built against the older boards; these bring the build in line, in this order, before step 8):

9. *(built 2026-11-26, welinc-auth `00a6ced`)* welinc-auth, on `feat/portal-redesign` before its PR: remove `GET /auth/admin/summary` (service, controller entry, tests) and its contract 0001 Changes line and section 16 row, `npm run openapi`, tests, satisfies **AC-7**
10. *(built 2026-11-26, portal `56cc6bc`; the CSS motion constants module comes with step 12, its first user)* Portal motion out: remove the `motion` package, `src/pages/launcher/motion/` and the `LauncherMotion` chunk, the `BAND_SCENE` scenes and the band trucks, and the `adminSummary` hook and its tests; add the CSS motion constants module, satisfies **AC-9**, **AC-12**
11. *(built 2026-11-26, portal `56cc6bc`)* Launcher to the Round 69 boards: Q1 band with M1, L1 tiles with N3 text three to a row, P5 number keys, the S5 Suite management tile with its "For …" line, K3a and E1g at the bottom, the screen choice (suite admin straight to `/admin`) and the switcher and logo rules for that case, the three window fits; then design the phone layout and record it in AC-4, satisfies **AC-1** to **AC-5**, **AC-20**
12. Arrival A3 and the random launches 2, 3 and 4 in CSS, cut to 900 ms, reduced motion, satisfies **AC-8**, **AC-10**, **AC-11**
13. Sign in S27d Quiet: the drawn map as a static SVG from `drawnmap.json`, the twelve trucks on `animateMotion`, the glass panel, the copy and the OpenStreetMap credit; forgot password, Signed out and No access in the same panel, satisfies **AC-13**, **AC-14**, **AC-16**

8. Sweep (runs last, after step 13): board comparison, axe at 1280 px and 375 px, lint, typecheck, builds and tests in each touched repo, update `design.md` (*Motion*: the arrival, the random launches and their reduce rule, CSS only; *Feedback*: the idle toast in place of the signing out banner; *Brand surfaces*: the launcher band and tiles, the sign in map and logo by place), satisfies **AC-29**

## Migration plan

**Strategy**: no data migration; ordered deploys, additive first.
**Phases**:
1. welinc-auth PR into `development` (staging deploys it): `suiteAdmin`, the two routes, the People list filters, the email layout (the summary route is removed before this PR, AC-7). VMMS and BMS ignore the new field.
2. Portal and web-vrms PRs, one per milestone. Until step 1 is live, the portal treats a missing `suiteAdmin` as `false`, so a portal ahead of auth never breaks.
**Rollback**: revert the portal PR (the old screens come back); the auth additions can stay, nothing else reads them.
**Risks**: no merges in the 2 hours before a defense; the sign in map and the launch scenes are the riskiest work, which is why they come after the static launcher.

## Consequences

**Positive**:
- The front door finally looks like a logistics company, which is what the panel sees first.
- A suite admin with a temporary role is no longer locked out of Suite management.
- One warning pattern (a toast) across the portal and VRMS, and the misleading "Signed in until" time never ships.
- A suite admin goes straight to the only place they can work, and no admin route skips the code step.

**Negative / tradeoffs**:
- No animation library, but hand drawn SVG scenes (the sign in map, three launches, the cartons) that someone must maintain, and CSS keyframes in place of a library's helpers.
- Built work is thrown away: the Motion milestone, the band trucks, the summary route and hook, and the R37 sign in.
- Four additive contract 0001 changes (a launcher field, two routes, the list filters); VMMS and BMS don't use them but must see the Changes line.
- The facets route runs about ten small counts per call (in parallel), up to two calls a second while someone ticks chips; fine at the suite's few hundred people, but it is the first place to look if People feels slow. The faster shape (two raw SQL queries with a `FILTER` clause per status) would mean writing the status and group rules a second time in SQL, so it waits until People is measurably slow.
- web-vrms is pulled into a portal spec for the toast, so its banner code and tests change too.
- The email check confirms to an admin that an exact email has an account; accepted because admins need it to avoid duplicates and the check is behind step up and a rate limit.
- Spec 0016 AC-7's "no ring outside the box" now has an exception on the sign in page (AC-14).
- The sign in shows a map traced from OpenStreetMap, so it carries the ODbL credit.

**Neutral**:
- Spec 0016 needs amendment lines: AC-11 (a warning toast may be persistent, `duration: Infinity` with no time bar; the session warning doesn't count toward 3; the sign in split has its own Toaster), AC-12 and AC-12b (the banner becomes this spec's toast, and the "under the offline banner" rule is dropped), AC-7 (the sign in split's soft ring), *Feedback* banner list. Its timing rules stay.
- The S23 profile page will reuse the shell and the account menu item from AC-19.

## Follow-up

- [x] Boards copied into `boards/` (2026-11-24, canvas version 1795505694-e0cf, 25 boards; see *Board index*).
- [x] The garage ring hover rule is gone with the map (2026-11-26).
- [ ] Tell VMMS and BMS about the additive contract 0001 changes (no action needed from them).
- [ ] `motion` is removed (AC-12); if `welinc-web-portal/AGENTS.md` mentions it, `/sync` takes the line out.
- [ ] Draw the code step and forgot password on S27d Quiet, then point AC-14 at those boards.
- [x] Boards for the 2026-11-26 update copied into `boards/` (`R69Victor`, `R69Danilo`, `R69Corazon`, `R69Felicidad`, `R69Armando`, `R66A3`, `R29LaunchDock`, `L28MLoad`, `R47Quiet`).
