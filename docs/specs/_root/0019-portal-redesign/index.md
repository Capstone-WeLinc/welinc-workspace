# 0019. Portal redesign from the design rounds

**Date**: 2026-11-24
**Status**: Proposed
**Scope row**: [S22](../../../scope/_root/shared-services.md) (shared services, Beta)
**Repos**: `welinc-web-portal` (almost everything), `welinc-auth` (two additive routes, one launcher answer field, the code email layout), `welinc-web-vrms` (the idle warning toast only), workspace (`design.md`, spec 0016 amendment lines, contract 0001)
**Design source**: the canvas "WeLinc design directions" (https://claude.ai/artifact/VFhLSMNhfpAFD4D4c2VQzp), pages "Round 12" to "Round 37", opened from the codesamtm claude.ai account. Copies of every board named here live in [`boards/`](boards/); the copies are the source for `/develop` and `/check verify`. Older boards on the canvas are history.

## Summary

This spec turns the portal screens you picked on Nov 24 into a build: the launcher with its navy band, line drawing and livery trucks, the new sign in and four step forgot password, the Suite management shell, the filter popover, the one screen Add a user dialog, new toasts, a 404 page, branded code emails, the favicon and tab titles. Motion comes from the Motion library (`motion/react`), loaded only with the sign in and launcher code, and it is built last so that if time runs short only the movement slips. Two small additive welinc-auth routes (strip counts, email check) and one new launcher answer field (`suiteAdmin`) close the gaps the boards leave. The "Signed in until" pill is not built; a "Still there?" toast, two minutes before the idle limit, replaces the signing out soon banner in the portal and in web-vrms.

## Requirements

**User stories**:
- As anyone signing in, I want a front door that looks like WeLinc Logistics, not a template, so the suite feels like one product.
- As a staff member with one system, I want to land straight in my system, and as anyone with more, I want one screen that shows every system I can open.
- As an admin, I want the launcher to tell me how many people and requests need me, without asking me for a code first.
- As anyone working in the portal or VRMS, I want a clear warning before I'm signed out for being idle, with one button to stay.
- As someone who gets dizzy from movement, I want the launcher to respect my reduced motion setting.

**Acceptance criteria**:

*Launcher*
- **AC-1**: The launcher matches `R30Launcher` and `R37LineArt`: a navy band with the gold ///L `LogoMark` and "WeLinc Logistics" in white italic, the greeting, today's date, and the line drawing (warehouse, office, workshop, power lines, water tower with the ///L mark) in thin white lines at 34% opacity with one office window lit gold, over a road. Trucks are drawn in the real livery with a navy wordmark: the 14 ft with tail lift, the 10 ft closed van and the L300. There is no "Signed in until" pill, no map, no garage or branch names on the band. The page footer reads "WeLinc Logistics · Since 2018".
- **AC-2**: System cards are always ordered BMS, VMMS, VRMS. Each card shows the system icon, the code with one role chip, the full name, one line (BMS "bookings", VMMS "maintenance", VRMS "repair" wording from the board) and "Open BMS" (or VMMS, VRMS). An admin of the system sees the Admin chip only; anyone else sees their real role name (Operations, Chief Mechanic, Mechanic). Three or two systems sit in one row; one system is one wide card.
- **AC-3**: Anyone who administers something (suite admin, or `ADMIN` in any system) sees Suite management as one navy strip under the cards. Its header holds "Suite management" and an **Open Suite management** link to `/admin` (the way in for an admin who also holds systems). Three tiles follow: **Users need a look** (count) → `/admin/people` (People already opens with the Needs attention group first), **Deletion requests** (count) → `/admin/deletion-requests`, then **Temporary access** (count of active grants) → `/admin/temporary-access` for a suite admin, or **Audit log** (a link, no count) → `/admin/activity` for a system admin. Links are built with `viewHref` from `adminViews.ts`, so a system admin's links carry `system=<their system>` (the first in BMS, VMMS, VRMS order when they admin several). Counts use the odometer count kept from Round 23 and roll only when the number is above 0 (a plain 0 otherwise); while loading, or after the 3 s timeout or a failure, each tile shows a dash. A suite admin with no systems sees only a large Suite management card, full width, with the same tiles. Someone with no admin role sees no strip.
- **AC-4**: For every role and count rule on `R30Launcher` (its mockup switch), the whole launcher fits a 1440×900 window with no page scroll, and also fits 1280×720 and 1024×768 (projector sizes) with no page scroll. Below 768 px the band is shorter, the cards stack and the page may scroll.
- **AC-5**: The screen choice (`screenForAnswer` in `src/lib/auth.ts`) follows these rules, in order after the existing `APP_NOT_ALLOWED`, phone only and `next` rules: one web system, no `ADMIN` there, not a suite admin, and no `error` → straight into that system; no systems and not a suite admin → No access; everyone else → the launcher. A suite admin whose only role is temporary and not `ADMIN` reaches the launcher and Suite management.
- **AC-6**: welinc-auth adds `suiteAdmin: boolean` (required) to the launcher answer on every route that answers it (`GET /auth/sso`, `POST /auth/login`, `POST /auth/login/verify-email`). Contract 0001 gets an additive Changes line; `docs/openapi.json` is regenerated; the portal's `LauncherAnswer` gains the field.
- **AC-7**: welinc-auth adds `GET /auth/admin/summary` (SSO cookie, any admin, **no step up**: the controller sets `ADMIN_ROUTE_LEVEL` to `'admin'`, not the `AdminSessionGuard` default `'admin-code'`; no limit beyond the global throttler) answering only numbers, scoped exactly like People's read scope for that caller: `needsAttention` (computed by the same function as the `attention` group in `people-page.ts`, never a copy of its rule), `deletionRequests` (pending requests; for a system admin only those whose person holds a role in a system they admin; a suite admin sees all), and for a suite admin `temporaryGrants` (active now, the same query as `AdminReportService`'s temporary grants). No names, emails or ids. A non admin gets 403. The portal aborts the call at 3 s; a failure or timeout never blocks the launcher (AC-3's dash). The portal keeps the answer in memory for 30 s and fetches again when the window regains focus after that; counts don't update live while the page stays open.

*Motion*
- **AC-8**: **Arrival 2** (`R31ArrTruck`, `R32Sequence`) plays only right after a sign in through the portal's own form in this tab (the password form, or the email code step that finishes it). A sign in that comes back by a full page load (an app initiated login, an SSO return) plays no arrival. The flag is in memory, read once by the launcher, and cleared when any other screen shows (straight in, No access). The truck drives in and drops the cards, brakes to the loop's cruising speed (about 150 px/s) and drives on as the first loop truck, with no visible jump in position or speed. A reload, the back button, or Home from Suite management shows the launcher with the cards in place and the loop running.
- **AC-9**: The **loop**: a few trucks pass in one direction along the road at about 150 px/s. It pauses while the tab is hidden or the band is off screen, and resumes where it stopped. The scene is `aria-hidden`, takes no focus, and never shows live data (no real plates, routes or counts).
- **AC-10**: **Launch 3** (route bar, the truck starting right of the garage, no label, Round 31): each card is a real link (`href` is the system url). The click handler never calls `preventDefault`; it starts the launch (at most 900 ms) while the browser fetches the system, and the page unloads whenever the system answers. The launch is skipped when the event is already `defaultPrevented`, a modifier key is held (Ctrl, Cmd, Shift, Alt) or the button isn't the left one, so new tab clicks behave normally.
- **AC-11**: With `prefers-reduced-motion: reduce`, and on any screen under 768 px, the band shows the parked scene: two livery trucks standing on the road, no arrival and no loop. Cards fade in (no movement), and Launch 3 becomes a fade of at most 200 ms before the navigation completes.
- **AC-12**: Motion code (`motion/react`, through `LazyMotion` with the `domAnimation` features and `m` components) is imported only by the sign in and launcher screens. The Admin chunk does not load it, so Admin motion (the 180 ms filter fold, the steering wheel spin) is CSS on spec 0016's motion tokens. `tw-animate-css` stays for the shadcn parts; no other animation library is added. Truck count, spacing, sizes, the arrival's length and the card drop stagger are copied from `R37LineArt`'s constants (the newest board that plays the sequence; `R34Sequence`, `R33Sequence` and `R32Sequence` are history) into one launcher motion module, not chosen anew.

*Sign in and forgot password*
- **AC-13**: Sign in matches `R37SignIn` (layout A): a split with the navy side on the left holding the copy and the branch map (labels say "branch"), and the white form on the right. Copy: "#hasslefree transport solution" over "Keep the fleet moving.", then "Sign in with your WeLinc work account to pick up where you left off." There is no garage name eyebrow and no system names. Under the form: "No account yet? Ask your admin to add you. You'll get an email to set your password." The branch map is decoration: static labels (no data), `aria-hidden`.
- **AC-14**: Forgot password is four steps on the same split (Round 31, approved as is): (1) email; (2) the 6 digit code, valid 10 minutes, resend after 60 s; (3) new password with the strength box listing welinc-auth's four password rules, a **Confirm new password** field and a "Passwords match" line; (4) done, centred, saying the reset signed out every session. Fields on the split (sign in and forgot password) show focus as a navy border with a soft navy ring, never gold.
- **AC-15**: Messages on the sign in page: a sign out (`reason=logout`, or a sign out in another tab) shows the app's `Toast` as **success** (green) at the top of the white side; a session ending (`reason=ended`, `idle`, `maxage`) shows the same toast as **warning** (amber) that stays until closed (`duration: Infinity`, no time bar), carrying today's wording for each reason. `noticeFor` changes its tone for `ended`, `idle` and `maxage` from `info` to `warning`, and for `logout` to `success`. These toasts come from a second sonner `Toaster` mounted only inside the sign in split's white column with `position="top-center"`; the app's main Toaster keeps spec 0016 AC-11's placement. Errors that stop a sign in (`LOGIN_REQUEST_EXPIRED`, `LOGIN_STATE_INVALID` and the other `error=` codes) stay inline above the form.
- **AC-16**: **Signed out** and **No access** screens use the sign in split with their content centred on the white side, like forgot password step 4. No access names no systems.

*Suite management shell*
- **AC-17**: The admin area is called **Suite management** in the sidebar title, the breadcrumb and the switcher card. Under the title sits your role ("Suite admin" or "VRMS admin") in plain muted white, never gold (`Shell20`).
- **AC-18**: The sidebar footer is a darker strip holding the ///L mark and "WeLinc Logistics" on one line with the collapse button at its right. There is no full width Collapse row, no edge handle and no Back to home row; the logo goes Home. Collapsed, the strip shows the mark alone (logo B).
- **AC-19**: The account menu (avatar, top right, in Suite management and on the launcher alike) holds **Your profile** and **Sign out** only. Your profile shows only once S23's profile route exists (one constant, `PROFILE_PATH` in `src/lib/routes.ts`, `null` until S23); until then the menu holds Sign out alone.
- **AC-20**: The system switcher (grid button, top right, `Switcher16`) opens wide cards, one per row: the Suite management card first and ticked ("You are here", subtitle "Users and permissions"), then only the systems you hold a role in, each with your role as a tag and its url from the held launcher answer. The role line under the Suite management title (AC-17) comes from `/auth/admin/me`; if the two disagree (a role changed mid session), the held answer refreshes on the next session check. The popover title has a **Home** pill with a house icon. A suite admin with no system roles has no switcher; the logo and account menu go Home.
- **AC-21**: The People filter is one Filter button opening the `Filter18` popover: status as checkbox chips (no coloured dots); system and role as accordion rows (the box picks the whole system, the row opens its roles, one open at a time, 180 ms fold); roles as soft tint chips with a tick. Ticking every role of a system turns back into the whole system ("Everyone"). The header has Clear all; the footer says "N filters on" next to "Show N people", where the people count is the list total for the chosen filters (the grouped list answer's `counts`, summed over the groups shown; if `counts` don't follow a filter, `/develop` adds the total to the list answer rather than guessing).
- **AC-22**: Add a user is the one screen dialog on `AddUser15`: email first, with the field's own icon as the check (red ! not an email, a spinner while checking, a navy tick when free, a person icon plus the existing account card when the email has an account); one **Full name** field; **Contact number** optional (welinc-auth's create request gains an optional `contact`, max 100 characters, stored in the existing `users.contact` column); system cards for a suite admin (none for a system admin, whose system is fixed); role cards with a one line meaning; no Temporary switch; one system per add. An existing account turns the dialog into "give access" for that person (today's `attachExisting`). The name search in today's dialog goes: the email is the only way in, and `users/lookup` stays in the API. The dialog checks only an email that passes the format check, 400 ms after typing stops, cancelling any older check still running.
- **AC-23**: welinc-auth adds `GET /auth/admin/users/email-check?email=&system=` (SSO cookie, any admin of `system`, the same step up rule as `users/lookup`, but its **own** rate limit counter of 60 a minute per admin, not lookup's 30). The email is trimmed and lowercased, and only the whole email matches (never partial). It answers one `status`, taking the first that applies in this order: `inactive` (deactivated or deleted, can't be added here), `suite-admin` (can't take a system role; **only a suite admin sees this**, a system admin gets `existing` with no systems list, so the route never tells them who is a suite admin), `in-system` (already holds a role in `system`), `existing` (can be given access), `free`. For `existing` and `in-system` it adds `name` and `picture`, and the systems list only where the caller is an admin.
- **AC-24**: The steering wheel wait (Round 29 option C, picked Round 33) replaces the spinner inside every busy button (Save, Send code, Sign in, Review and save) and the small loading spot when a list reloads or loads more. A page's first load keeps its skeletons. It stops spinning (static wheel) under reduced motion and keeps its `aria-busy` and label.

*Session warning*
- **AC-25**: In the portal and in web-vrms, the signing out soon **banner** is replaced by a warning **toast** with the same timing and rules as spec 0016 AC-12, AC-12a and AC-12b (check 120 s before the cutoff, reschedule when it moved, the last check before leaving, the cross tab sync, the failure retries). The toast is a `SessionToast` component that reads the session store and ticks its own countdown, fired through `toast.custom` with the fixed id `session-warning`, `duration: Infinity` and `dismissible: false`; the `Toast` component gains a variant with no close button and no time bar, and the limit of 3 skips this id. It shows independently of the offline banner (both can show; 0016 AC-12b's "under the offline banner" rule is dropped). In web-vrms the change touches `src/lib/session/*` and `src/components/feedback/*`; if its `Toast` lacks the variant, it gains the same one. Idle: title "Still there?", body "You'll be signed out in 1:45 for inactivity." with a live countdown, action **Stay signed in**. The 12 hour end: title "Your session ends at 2:30 PM" (time only, `h:mm a` in the browser's locale and time zone, from `sessionAbsoluteExpiresAt`), body "This is the 12 hour limit. Sign in again to keep working.", no action. The toast stays until Stay signed in succeeds, a check finds the cutoff moved, or the tab leaves; it has no close button and no time bar, and it never counts toward the limit of 3. It uses `role="status"`, never takes focus, keeps the ticking time `aria-hidden`, and announces once on open and again at 30 s, as AC-12 there. The offline banner stays a banner and shows alongside it.

*Other screens and brand*
- **AC-26**: Any unknown address (including an unknown `/admin/<view>`) shows the "Wrong turn" 404 page from Round 34, with a way Home; `/portal` keeps its redirect to `/`. A person link to someone who doesn't exist keeps S19's in pane not found state. The hosting already answers `index.html` for every unknown path (as for `/admin/*`), so the portal's router decides.
- **AC-27**: welinc-auth's code emails (password setup, password reset, sign in code, email change confirm) share one branded layout from the Round 34 reset email: the ///L mark (logo F as a PNG sent as a CID attachment through nodemailer's `attachments` with a `cid`, never SVG, a data URI or a remote image; its `alt` is the "WeLinc Logistics" wordmark in text), a navy header, the code large in a monospace font, the existing wording and lifetimes, and a plain text part with the same content. Snapshot tests cover the HTML and the text part; a manual check (a `/test` item) confirms Gmail web, Gmail on Android and Outlook web.
- **AC-28**: `public/favicon.svg` is the ///L mark in badge B (Round 35); the Vite logo is gone. Logo by place: A on navy, B alone at small sizes (favicon, collapsed sidebar), F on white and in print. Every route sets the tab title as the most specific part first, then "WeLinc": "Sign in · WeLinc", "Forgot password · WeLinc", "Home · WeLinc", "People · Suite management · WeLinc", "Maria Santos · People · WeLinc" ("People · Suite management · WeLinc" while the person loads, "Person · People · WeLinc" with no name), "Page not found · WeLinc" (inside `/admin` too).

*Checks*
- **AC-29**: Every screen above matches its board within the allowed differences (handoff 2026-11-24: Plex Mono for the boards' JetBrains Mono, Inter for Inter Tight, spec 0016's later token values, shadcn parts, real data lengths), compared from the board's values and the running page's computed styles and text. axe finds no serious issue at 1280 px and 375 px, no page scrolls sideways, and lint, typecheck, builds and tests pass in every touched repo.

## Decision

**Chosen option**: Option 2: rebuild the portal screens from the boards in milestones, motion last, on the existing tokens and components, with Motion (`motion/react`) as the one animation library and two additive welinc-auth routes.

Build the picked boards on top of spec 0016's tokens and components, close the data gaps with small additive welinc-auth changes (`suiteAdmin`, `/auth/admin/summary`, `/auth/admin/users/email-check`), and add motion as the final milestone so a static launcher can ship if time runs short.

**Implementation skills**: `tailwind-4-docs` (`lombiq/tailwind-agent-skills`, `.claude/skills/tailwind-4-docs/`) · `shadcn` (`shadcn-ui/ui`, `.claude/skills/shadcn/`) · `vercel-composition-patterns` and `vercel-react-best-practices` (`vercel-labs/agent-skills`, `.claude/skills/`) · `ask-sonner` (`.claude/skills/ask-sonner/`, the toast work) · `nestjs-best-practices` and `prisma-client-api` (`.claude/skills/`, the welinc-auth routes) · offer `emil-design-eng` once the motion milestone is built (ask first, per AGENTS.md)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Board index (copies in `boards/`)

| Board | Settles |
|---|---|
| `R30Launcher` | Launcher layout, role and count rules (mockup switch), the 1440×900 fit (AC-2 to AC-5) |
| `R37LineArt` | Band visual, livery trucks, the sequence and motion constants (AC-1, AC-8, AC-9, AC-12) |
| `R31ArrTruck`, `R32Sequence`, `R33Sequence`, `R34Sequence` | Arrival 2 and the braking hand off; older takes of the sequence (AC-8) |
| `R31LaunchRoute` | Launch 3 (AC-10) |
| `R37SignIn` | Sign in A with the branch map (AC-13) |
| `R32Forgot1` to `R32Forgot4` | The four forgot password steps, navy focus, "Confirm new password" (AC-14) |
| `R36OutToast2`, `R36EndedToast2` | Signed out and session ended toasts (AC-15) |
| `R34NoAccess` | No access on the split, no system names (AC-16) |
| `Shell20` | Suite management sidebar, title, role line, footer (AC-17, AC-18) |
| `Switcher16` | Account menu and system switcher (AC-19, AC-20) |
| `Filter18` | Filter popover, option 2 soft tint chips (AC-21) |
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
| 0 | n/a | true | launcher, large Suite management card |
| 1 | no | false | straight in (no `error`) |
| 1 | no | true | launcher with the card and the strip |
| 1 | yes | any | launcher with the card and the strip |
| 2 or 3 | any | any | launcher (strip when they administer anything) |

**API surface** (all welinc-auth, through the gateway, SSO cookie):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/sso`, `/auth/login`, `/auth/login/verify-email` | GET, POST, POST | unchanged | the launcher answer plus `suiteAdmin: boolean` | unchanged | unchanged |
| `/auth/admin/summary` | GET | none | `{ needsAttention: number, deletionRequests: number, temporaryGrants?: number }` (`temporaryGrants` only for a suite admin) | any admin, route level `admin` (no step up) | 401 `SESSION_ENDED`, 403 not an admin, 429 (global throttler) |
| `/auth/admin/users/email-check` | GET | `email` (req, a valid email; trimmed, lowercased), `system` (req, a system the caller admins; a suite admin may pass any) | `{ status: 'inactive' \| 'suite-admin' \| 'in-system' \| 'existing' \| 'free', name?, picture?, systems? }` | any admin of `system`, step up as `users/lookup`, own limit 60 a minute per admin | 400 malformed email, 403 not admin of `system`, 429 |
| `/auth/admin/users` (existing create) | POST | adds optional `contact` (string, max 100) | unchanged | unchanged | 400 too long |

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Launcher band | Greeting name | `answer.user.name` (first word for the greeting, as `lib/launcher.ts` does today) |
| Launcher band | Today's date | the browser's clock and locale time zone, formatted like the board |
| Launcher cards | Code, full name, url, roles | `answer.systems[]` (`system`, `name`, `url`, `roles[].code`, `roles[].name`) |
| Launcher cards | One line wording | a static map in `systemIcons.ts` beside the icons, from the board copy (bookings, maintenance, repair) |
| Launcher cards | Admin chip vs real role name | `administers(system)` (`ADMIN` code) else `roles[].name` |
| Strip | Shown or not, which third tile | `answer.suiteAdmin` and `administers()` on any system |
| Strip | Three counts | `GET /auth/admin/summary` |
| Screen choice | Suite admin | `answer.suiteAdmin` (AC-6) |
| Arrival 2 | "Right after a sign in" | an in memory flag set by `Login`'s `onSignedIn` and the code step, read once by the launcher, never stored |
| Loop, Launch 3 | Speeds, durations | constants in the launcher motion module (150 px/s, at most 900 ms) |
| Footer | "Since 2018" | static copy |
| Switcher | Systems, urls, roles | the held launcher answer (the session watch store already holds the latest one; Admin calls `/auth/sso` once when empty, spec 0016 AC-12b) |
| Switcher | Role under the Suite management title | `/auth/admin/me` (`suiteAdmin`, `adminOf`), as today |
| Filter footer | "Show N people" | People's existing `counts` for the filters chosen |
| Add a user | Email status, name, picture, systems | `GET /auth/admin/users/email-check` |
| Add a user | Role cards' one line meaning | the role catalog's `description` (`/auth/systems`) |
| Idle toast | Countdown | the held cutoff and clock gap (`lib/sessionWatch`) |
| 12 hour toast | "ends at 2:30 PM" | `sessionAbsoluteExpiresAt` in the browser's local time |
| Sign in toasts | Which message | `reason` in the address (`noticeFor` in `lib/auth.ts`) |
| Tab titles | Person's name | the loaded person in the People pane; "People" until it loads |
| Code emails | Name, code, lifetime, portal host | `passwordCodeEmail` and its siblings' existing inputs |

**Key invariants**:
- The trucks and the scene are decoration: no request, plate, count or place in them comes from data.
- Nothing about the session or the arrival flag is written to `localStorage`, `sessionStorage` or the url (spec 0003 AC-36).
- The launcher never triggers the admin step up prompt.
- Every card stays a working link without JavaScript animation; a motion failure never blocks opening a system.
- Gold stays rare: the logo mark, the lit window and `commit` buttons only; never text on white.

**Security model**:
- `/auth/admin/summary` skips step up because it returns three counts and no person data; every list behind a count still asks for the code as today. It uses the caller's read scope, so a VRMS admin's numbers cover VRMS only.
- `/auth/admin/users/email-check` reveals whether an exact email has an account only to an admin, only after step up, rate limited with the lookup limiter, and never by partial match. Systems are listed only where the caller is an admin.
- `suiteAdmin` in the launcher answer tells the person something about themselves only.
- Code emails embed the logo inline (no remote image, no tracking pixel).

**Configuration required**: none. No new env vars.

**Critical test scenarios**:
- A suite admin with one temporary non admin VRMS role signs in and lands on the launcher with the VRMS card and the strip, verifies **AC-5**, **AC-6**
- A mechanic with only VRMS goes straight into VRMS with no launcher flash, verifies **AC-5**
- The strip's summary call fails: the tiles show without numbers and no code prompt appears, verifies **AC-3**, **AC-7**
- A non admin calls `/auth/admin/summary` and gets 403; a VRMS admin's counts exclude VMMS people, verifies **AC-7**
- The email check with a partial email answers 400, a system admin sees no systems they don't admin, verifies **AC-23**
- The email check for a suite admin's address, asked by a system admin, answers `existing` with no systems; a deleted person answers `inactive`, verifies **AC-23**
- The summary times out: dashes, no prompt; a refocus within 30 s doesn't refetch, verifies **AC-3**, **AC-7**
- Reload the launcher after sign in: no arrival, the loop runs; hide the tab and the loop pauses, verifies **AC-8**, **AC-9**
- Cmd click Open VRMS opens a new tab and the launcher stays still, verifies **AC-10**
- Reduced motion on: parked trucks, fades only, verifies **AC-11**
- Idle for 28 minutes in Admin: "Still there?" shows with the countdown; Stay signed in closes it in every portal tab; in web-vrms the same toast replaces the banner, verifies **AC-25**
- Open `/admin/nope`: Wrong turn page, verifies **AC-26**
- The 1440×900 fit for every `R30Launcher` switch state, verifies **AC-4**

## Build plan

Facade per the VRMS UI refresh override: each milestone builds the screens on the data the portal already has, and the welinc-auth additions land just before the screen that needs them. Motion is last so it can slip without leaving anything half built.

0. Copy every board named in this spec into `boards/` as `.dc.html` (done with the spec, or first thing if missed), satisfies **AC-29**
1. welinc-auth: `suiteAdmin` on the launcher answer, `GET /auth/admin/summary` (with the test that a session without the sign in code passes), `GET /auth/admin/users/email-check` with its own limiter, optional `contact` on create, the shared code email layout with the CID logo and snapshot tests; contract 0001 Changes line, `npm run openapi`, tests; branch and PR into `development`, satisfies **AC-6**, **AC-7**, **AC-23**, **AC-27**
2. Portal foundations: favicon and logo by place, tab titles on every route, the 404 page, the steering wheel wait in `Button` and the list loaders, satisfies **AC-24**, **AC-26**, **AC-28**
3. Session toasts in both apps: the idle and 12 hour toast replacing the banner in the portal and web-vrms (the timing modules stay, only the surface changes), and the sign in success and warning toasts, satisfies **AC-15**, **AC-25**
4. Suite management shell: naming, sidebar footer, account menu, switcher from the held answer; then the filter popover and the Add a user dialog with the email check, satisfies **AC-17** to **AC-23**
5. Sign in, forgot password, Signed out and No access on the new split, satisfies **AC-13**, **AC-14**, **AC-16**
6. Static launcher: band with the line drawing and parked trucks, cards, strip with counts, the screen choice fix, the 1440×900 fit, phones, satisfies **AC-1** to **AC-5**, **AC-11** (the parked scene)
7. Motion: add `motion` (lazy, `LazyMotion` plus `domAnimation`), Arrival 2, the loop with pause on hidden, Launch 3, reduced motion, check the Admin chunk has no motion import, satisfies **AC-8** to **AC-12**
8. Sweep: board comparison, axe at 1280 px and 375 px, lint, typecheck, builds and tests in each touched repo, update `design.md` (*Motion*: the launcher motion and its reduce rule; *Feedback*: the idle toast in place of the signing out banner; *Brand surfaces*: the new launcher band, sign in split and logo by place), satisfies **AC-29**

## Migration plan

**Strategy**: no data migration; ordered deploys, additive first.
**Phases**:
1. welinc-auth PR into `development` (staging deploys it): `suiteAdmin`, the two routes, the email layout. VMMS and BMS ignore the new field.
2. Portal and web-vrms PRs, one per milestone. Until step 1 is live, the portal treats a missing `suiteAdmin` as `false` and a failed summary call as "no numbers", so a portal ahead of auth never breaks.
**Rollback**: revert the portal PR (the old screens come back); the auth additions can stay, nothing else reads them.
**Risks**: no merges in the 2 hours before a defense; the launcher motion is the riskiest milestone, which is why it ships last and alone.

## Consequences

**Positive**:
- The front door finally looks like a logistics company, which is what the panel sees first.
- A suite admin with a temporary role is no longer locked out of Suite management.
- One warning pattern (a toast) across the portal and VRMS, and the misleading "Signed in until" time never ships.
- Admins see what needs them before opening Suite management, without a code prompt.

**Negative / tradeoffs**:
- A new dependency (Motion, about 15 to 20 kB on the sign in and launcher screens) and hand drawn SVG scenes that someone must maintain.
- Three additive contract 0001 changes; VMMS and BMS don't use them but must see the Changes line.
- web-vrms is pulled into a portal spec for the toast, so its banner code and tests change too.
- The email check confirms to an admin that an exact email has an account; accepted because admins need it to avoid duplicates and the check is behind step up and a rate limit.
- Spec 0016 AC-7's "no ring outside the box" now has an exception on the sign in split (AC-14).

**Neutral**:
- Spec 0016 needs amendment lines: AC-11 (a warning toast may be persistent, `duration: Infinity` with no time bar; the session warning doesn't count toward 3; the sign in split has its own Toaster), AC-12 and AC-12b (the banner becomes this spec's toast, and the "under the offline banner" rule is dropped), AC-7 (the sign in split's soft ring), *Feedback* banner list. Its timing rules stay.
- The S23 profile page will reuse the shell and the account menu item from AC-19.

## Follow-up

- [x] Boards copied into `boards/` (2026-11-24, canvas version 1795505694-e0cf, 25 boards; see *Board index*).
- [ ] The handoff says "card hover only lights the garage rings", but the map left the launcher; check `R30Launcher` when copying and drop the hover rule if there are no rings on the final board.
- [ ] Tell VMMS and BMS about the three additive contract 0001 changes (no action needed from them).
- [ ] Add `motion` to the portal's `## Agent skills` or Conventions in `welinc-web-portal/AGENTS.md` once it's in (for `/sync`).
