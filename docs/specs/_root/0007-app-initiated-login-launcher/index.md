# 0007. App initiated login and the portal launcher

**Date**: 2026-11-09
**Status**: Accepted
**Scope row**: [S4. App initiated login and launcher](../../../scope/_root/shared-services.md#s4-app-initiated-login-and-launcher--in-progress)
**Builds contract sections**: [0001](../0001-shared-services-contract/index.md) sections 5 (the `user` object of user grants), 7 (Switch system, the launcher), 10 (`/auth/login`, `/auth/sso`, `/auth/systems`), 12 (the `/auth/sso` limit)
**Replaces**: VRMS feature 60 (portal system picker), dropped 2026-11-07

## Summary

The portal gets a launcher: a page that lists the WeLinc systems you hold, each as a card with what it is and your role there. You see it when you open the portal yourself and hold two or more systems. With one system, the portal sends you straight in. Inside each app, a Switch system link takes you back to the launcher, and signing out anywhere signs you out everywhere. The login itself stays app initiated (each app starts its own sign in and gets you back through a one time code, which spec 0003 already built), so S4 adds the launcher answer in welinc-auth, the launcher page, Switch system in VRMS, a lighter portal stack (Tailwind v4 and shadcn), and a guide that tells VMMS and BMS how to join.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As someone who works in two or three systems, I want one page that lists them after I sign in, so I can pick where to work without typing addresses.
- As someone in one system, I want to land in it straight after signing in, never on a page with one choice.
- As anyone, I want a link I opened while signed out (a ticket, a filtered list) to bring me back to that exact place after I sign in.
- As someone in more than one system, I want a Switch system link inside each app, so I can move without signing in again.
- As a VMMS or BMS developer, I want a written recipe for the shared web login, so our app can join it in S11 without reverse engineering VRMS.

**Acceptance criteria**:

*welinc-auth*

- **AC-1**: `GET /auth/sso` with a live SSO session answers 200 `{ user: { id, name, email, picture }, systems: [{ system, name, description, url, roles: [{ code, name }] }] }`, with `Cache-Control: no-store`. `systems` holds every system where the user holds at least one role, in the fixed order BMS, VMMS, VRMS. `roles` lists the user's roles in that system in catalog order (`system_roles.sort_order`, ties broken by `code`), with catalog names. `url` is the `web_address`, returned exactly as stored, of the system's client with `kind = CONFIDENTIAL`, `is_active` and a non null `web_address` (the seed makes exactly one; if two ever match, the oldest by `created_at` wins and a warning is logged). `picture` is `users.profile_picture` as stored, or null. Without a live session it answers 401 `SESSION_ENDED`; an inactive or deleted user has no live session (`liveBySsoHandle` already returns null for them). With a live session but no role anywhere, 403 `NO_SYSTEM_ACCESS` with `user: { email }` added to the coded body, so the no access state can say who is signed in (it is the caller's own email, nothing else about them). The call never counts as activity: `sessions.last_activity_at` is unchanged after it.
- **AC-2**: A held system whose client is missing, switched off, or has no `web_address` is left out of `systems`, and welinc-auth logs one warning naming the system (never the user's email). If that leaves no system, the answer is 403 `NO_SYSTEM_ACCESS` with the same `user: { email }` (AC-1).
- **AC-3**: `POST /auth/login` answers the same body as AC-1 (and sets the SSO cookie as today). The body no longer takes `system`: sending it gets 400 from the strict validation pipe. `pickLoginSystem` and `PICK_ORDER` are deleted. The systems list (after AC-2's client filter) is built after the password check and before the session is created: if it is empty, the answer is 403 `NO_SYSTEM_ACCESS` with `user: { email }` (the password was already checked, so this is the caller's own email) and no session or SSO cookie is created.
- **AC-4**: `GET /auth/sso` allows 60 calls a minute per client address; more get 429 `RATE_LIMITED` (the code contract section 11 already uses) with a `Retry-After` header. It reuses the throttler storage pattern `/auth/authorize` already has (an `SSO_LIMIT` constant beside `AUTHORIZE_LIMIT`), keyed on `req.ip`, which `TRUST_PROXY_HOPS` already resolves to the real client behind the gateway.
- **AC-5**: Every system catalog file (`prisma/catalog/<system>.ts`) carries a `description` of 1 to 200 characters. `catalog:sync` copies it into the new `systems.description` column and refuses an empty or longer one, listing every problem. `GET /auth/systems` adds `description` to each system (its ETag changes with it). Seeded lines, which each group may reword in its own file: VRMS "Repair tickets, mechanics and workshop work", VMMS "Vehicles, maintenance and fleet upkeep", BMS "Bookings, dispatch and trips".
- **AC-6**: Every user grant answer (the `authorization_code` and `refresh_token` grants on `/auth/token`, and `/auth/mobile/login`) adds `user.systems`: the codes of every system the user holds a role in, in the order BMS, VMMS, VRMS, read fresh at that grant. It never goes in the access token, whose `roles` stay limited to `aud`.
- **AC-7**: No role, permission, catalog role entry or client is added or removed. `catalog:sync --dry-run` after the change reports only description changes.

*welinc-backend-vrms and welinc-web-vrms*

- **AC-8**: `POST /vrms/session/refresh` passes `user.systems` through unchanged. web-vrms keeps it in the auth store with the rest of `user`. A missing `systems` (an older welinc-auth) counts as an empty list.
- **AC-9**: web-vrms shows **Switch system** (lucide `LayoutGrid` icon) in the sidebar, the user menu and the phone sheet, in the spots the old VMMS switch held, only when `user.systems` has two or more entries. It opens `<PORTAL_URL>/?from=VRMS` in the same tab. The old `switchToVmms`, `canSwitchToVmms` and `VITE_VMMS_URL` are removed.
- **AC-10**: A visit to a VRMS deep link (path, query and hash) with no VRMS session goes through the portal (the form when signed out, no form when the SSO session is live) and lands back on that exact address, for one, two and three system accounts. The launcher never shows during an app initiated login (a `request` is present).

*welinc-web-portal: routing*

- **AC-11**: Opened with `reason=logout`, `reason=idle` or `reason=maxage`, the portal shows the form with its message and never calls `/auth/sso` (spec 0003 AC-36, kept).
- **AC-12**: Precedence when the address holds several values: `reason` first (AC-11), then `request` (this AC, any `error` ignored), then the rest (AC-13). No app sends `request` and `error` together. Opened with `request=<id>`, the portal keeps today's flow: if `/auth/sso` answers 200 it continues at `/auth/authorize/resume` without showing the form; otherwise it shows the form and resumes after sign in.
- **AC-13**: Opened directly (no `request`, no `reason`), the portal calls `/auth/sso`:
  - 401: the form, with the notice for any `error` in the address.
  - 200 with exactly one system and no `error`: `location.replace(url)`, with no launcher drawn.
  - 200 with two or more systems, or with an `error`: the launcher, with the `error` notice as a banner above the cards. It never auto forwards while an `error` is present, so a failing app can't loop.
  - 403 `NO_SYSTEM_ACCESS`: the no access state (AC-19).
  - 429, 5xx or a network failure: the launcher's error state (AC-20).
- **AC-14**: After a successful form sign in with no `request`, one system and no `error` in the address goes straight to its `url` with `location.replace` (amended 2026-11-14: unless the person holds `ADMIN` in that system, who sees the launcher so the Admin card from suite spec 0013 is reachable; this applies to AC-13's direct visit too); two or more systems, or an `error` still in the address, show the launcher built from the login answer (with the banner), with no second `/auth/sso` call. The same holds after AC-18's 401 sends the launcher back to the form.

*welinc-web-portal: the launcher*

- **AC-15**: The launcher shows a top bar (WeLinc logo and wordmark on the left, the account menu on the right), a greeting "Good morning", "Good afternoon" or "Good evening, <first name>" by the browser's local hour (before 12, before 18, else evening), one line "Pick where you want to work today.", then one card per system in answer order. Each card shows the system's icon in a soft tinted square (BMS `CalendarCheck`, VMMS `Truck`, VRMS `Wrench`, anything else `AppWindow`), the code as the title, the full name, the description, and one role pill per role in design.md's role colors. The whole card is one link (`<a href={url}>`, same tab) with a chevron.
- **AC-16**: With `from=<code>` in the address and that code among the user's systems, its card carries a "You're here" tag (gold fill, dark text) and still opens normally. Any other `from` value is ignored. Nothing about it is stored.
- **AC-17**: The account menu shows the picture (only when `picture` starts with `/uploads/`, loaded from `API_BASE_URL` + `picture`, the welinc-auth address the portal already calls, which serves `/uploads/`; the shadcn `Avatar` falls back to initials if it fails to load) or the initials, the name and the email, and **Sign out**. Sign out opens an alert dialog, "Sign out of every WeLinc system?", with Cancel and Sign out. Confirming posts `/auth/logout` with the SSO cookie, then goes to `/login?reason=logout`. A failure keeps the launcher and shows an error toast.
- **AC-18**: When the launcher tab becomes visible or regains focus, at most once every 10 seconds, it calls `/auth/sso` again: 200 redraws the cards (a lost system disappears, a new one appears; a single remaining system does not auto forward); 401 shows the form with "Your session ended. Sign in again."; 403 shows the no access state. These calls never count as activity.
- **AC-19**: The no access state shows "Your account has no access to any WeLinc system. Ask your admin for a role.", the email signed in (read from `user.email` in the 403 body of `/auth/sso` or `/auth/login`), and Sign out (AC-17's flow).
- **AC-20**: The launcher has its four states: loading (three skeleton cards shaped like real ones), error ("We couldn't load your systems." with Retry), no access (AC-19), and the cards. It works at 375px (one column), from 640px (two columns) and from 1024px (three columns), with no horizontal scroll, every card reachable by Tab with a visible focus ring, and motion limited to a 150 ms chevron shift that `prefers-reduced-motion` turns off.

*welinc-web-portal: stack and login pages*

- **AC-21**: The portal moves to Tailwind v4 and shadcn/ui: design.md tokens in `src/index.css` (`@theme`), Inter from `@fontsource-variable/inter`, shadcn `Button`, `Input`, `Label`, `Card`, `DropdownMenu`, `AlertDialog`, `Skeleton`, `Avatar` and `Badge`, and sonner replacing the hand made toast context. `tailwind.config.js` and the v3 PostCSS setup are gone. Lint fails on hex values and Tailwind palette classes in `src/`, as web-vrms does.
- **AC-22**: The login and forgot password pages keep today's look: the split layout, hero photo, gradient overlay, gold glows, logo and copy, now drawn with tokens. Only their states improve: a skeleton instead of the bold text while `/auth/sso` runs, notices with an icon and `role="alert"` for errors, shadcn inputs with labels, a disabled submit with a spinner while signing in, visible focus rings, 44px touch targets, and `text-base` inputs on phones.

*Shared docs*

- **AC-23**: Contract 0001 is amended in the same change, version staying 2: section 5 adds `user.systems` to the user grant answer and says clients ignore fields in `user` they don't know; section 7 says Switch system opens `<portal>/?from=<SYS>` and shows only with two or more systems, describes the launcher rules (AC-12 to AC-14), and says an app only ever sends a person to its own `session/start`, `<portal>/login?reason=…` or `<portal>/?error=…`, never the bare `<portal>/` for a missing session (that would loop with the one system forward); section 10 gives the final `/auth/login` and `/auth/sso` bodies, drops `system` from the login body, and adds `description` to `/auth/systems`; section 12 adds the `/auth/sso` limit; Decisions at a glance and the gap map mark the launcher as built in S4 and point the VMMS `?token=` and BMS handoff rows at the guide (AC-24) and S11.
- **AC-24**: `docs/integration/web-login.md` tells a system group how to join the shared web login: its client row is already seeded; copy `welinc-backend-vrms/src/session/` (routes, cookies, CSRF guard, auth client) under its own prefix; the web boot sequence (refresh, start once with the `sessionStorage` flag, give up to `<portal>/?error=LOGIN_FAILED`, one refresh at a time with a Web Lock); Switch system from `user.systems`; logout to `<portal>/login?reason=logout`; never send a signed out person to the bare `<portal>/` (go to your own `session/start`, or `<portal>/?error=…` on a failure), since a one system user would loop; ignore unknown fields in the `user` object; remove any `?token=` intake; the gateway route arrives with S9; and test with the one, two and three system seed accounts. `docs/integration/README.md` links to it.

## Decision

**Chosen option**: Option 1: a portal launcher on top of the app initiated code login, with the systems list served by welinc-auth.

Each app keeps starting its own login. The portal is only where you sign in and, with two or more systems, where you pick one. welinc-auth is the single source of which systems you hold, for the launcher (`/auth/sso`, `/auth/login`) and for each app's Switch system link (`user.systems`).

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` and `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-client-api/`, `.claude/skills/prisma-cli/`) · `tailwind-4-docs` (`.claude/skills/tailwind-4-docs/`) · `shadcn` (`.claude/skills/shadcn/`) · `vercel-react-best-practices` (`.claude/skills/vercel-react-best-practices/`) · `ask-sonner` (`.claude/skills/ask-sonner/`)

**Calls made in the spec** (pick, why, runner up):
- **403, not an empty list, for a live session with no system (AC-1).** It matches `/auth/login` and the code the apps already send. Runner up: 200 with `systems: []`, one more shape to handle.
- **Leave out a system with no usable client (AC-2).** A card that leads nowhere is worse than none, and the warning tells the owner. Runner up: a disabled card, which needs copy and a state for a seed mistake.
- **The `from` value only tags, never routes (AC-16).** Every launcher address comes from welinc-auth's answer, never from the query, so the portal can't become an open redirect. Runner up: dropping `from`, which loses the "You're here" cue.
- **Pictures only from `/uploads/` (AC-17).** That's the one form welinc-auth stores, and it stops a stored outside address from loading a tracker. Runner up: any `https` address.
- **A 60 a minute limit on `/auth/sso` (AC-4).** It's a public cookie route that now reads the catalog; focus checks (AC-18) stay far below it. Runner up: no limit, against the rule that every public route is limited.
- **Contract version stays 2 (AC-23).** `/auth/login` and `/auth/sso` are portal only by contract section 10, and the portal changes in the same merge; `user.systems` and `description` are additive. Runner up: version 3, which would tell VMMS and BMS something broke when nothing they call changed.
- **Role pill colors by role code across systems.** design.md's role table is suite wide. A code it doesn't list gets the slate tint.

## Feature design

**Data model sketch** (welinc-auth, one migration):

| Table | Change | Type | Rules |
|---|---|---|---|
| `systems` | add `description` | `VARCHAR(200) NOT NULL` | The migration adds it with a temporary default of `''` and drops the default; `db:deploy` runs `catalog:sync` right after, which writes the real lines and refuses an empty one. Never written by hand. |
| `oauth_clients` | none | | The card's `url` is the existing `web_address` of the system's active `CONFIDENTIAL` client. |

`SystemDefinition` in `src/auth/roles/catalog.types.ts` gains a required `description: string`. No per user state is stored: no last used system, no launcher preference. The launcher order is a constant `LAUNCHER_ORDER = [BMS, VMMS, VRMS]` in `src/auth/sessions/launcher.ts`, which replaces `tokens/login-system.ts`.

**State transitions**: none stored. The portal's screen choice is a pure function of the address and the `/auth/sso` (or login) answer, as AC-11 to AC-14 lay out:

```
checked in this order:
address has reason      -> form (no /auth/sso)
address has request     -> sso 200 ? resume : form, then resume (any error ignored)
otherwise, /auth/sso:
  401                   -> form (+ error notice)
  200, 1 system, no error -> location.replace(url)
  200, else             -> launcher (+ error banner)
  403                   -> no access
  429 / 5xx / network   -> launcher error state
```

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/sso` | GET | the `welinc_sso` cookie | `{ user: { id, name, email, picture }, systems: [{ system, name, description, url, roles: [{ code, name }] }] }` | SSO cookie | 401 `SESSION_ENDED`, 403 `NO_SYSTEM_ACCESS` (body adds `user: { email }`), 429 `RATE_LIMITED` |
| `/auth/login` | POST | `{ email, password }` (no `system`) | same body as `/auth/sso`; sets `welinc_sso` | none, `PortalCsrfGuard` | 400 (unknown field) is new; the rest unchanged (wrong password, `ACCOUNT_LOCKED`, `ACCOUNT_INACTIVE`, 403 `NO_SYSTEM_ACCESS` with `user: { email }`, 403 `CSRF_REJECTED`) |
| `/auth/logout` | POST | the SSO cookie, JSON body `{}` | 204, ends the `sid`, clears `welinc_sso` | SSO cookie, `PortalCsrfGuard` | none new |
| `/auth/systems` | GET | none | each system adds `description` | public | none new |
| `/auth/token` (user grants), `/auth/mobile/login` | POST | unchanged | `user` adds `systems: string[]` | unchanged | unchanged |
| `/vrms/session/refresh` | POST | the `vrms_rt` cookie | `user` adds `systems` (passed through) | cookie, CSRF guard | unchanged |
| portal `/` and `/login` | page | `request`, `reason`, `error`, `system`, `from` | form, launcher, no access, or a redirect (state diagram above) | | |

**Value sourcing**:

| Action | Value produced or displayed | Source |
|---|---|---|
| `/auth/sso`, `/auth/login` | `systems[].system` and order | `user_roles.system` for the user, distinct, sorted by `LAUNCHER_ORDER` |
| | `systems[].name`, `description` | `systems.name`, `systems.description` (catalog files) |
| | `systems[].url` | `oauth_clients.web_address` where `system` matches, `kind = CONFIDENTIAL`, `is_active` |
| | `systems[].roles[].code`, `name` | `user_roles.role` joined to `system_roles.name`, ordered by `system_roles.sort_order` |
| | `user.picture` | `users.profile_picture` |
| | the session | `welinc_sso` cookie through `SessionService.liveBySsoHandle` (spec 0003) |
| user grants | `user.systems` | `user_roles.system` for the user, distinct, `LAUNCHER_ORDER`, read inside the grant |
| launcher | greeting word | the browser's local hour (`new Date().getHours()`) |
| | first name | the first word of `user.name` |
| | card icon | a fixed map by system code in the portal (AC-15) |
| | role pill color | design.md role table by role code; slate otherwise |
| | "You're here" | the `from` query value, kept only if it equals a code in `systems` |
| | banner text | `noticeFor` from `error` and `system` in the address (spec 0003 messages, kept) |
| | initials | the first letters of the first and last words of `user.name` |
| web-vrms | Switch system shown | `user.systems.length >= 2` from `/vrms/session/refresh` |
| | Switch system address | `VITE_PORTAL_URL` (existing `PORTAL_URL`) + `/?from=VRMS` |

**Key invariants**:
- Every address the launcher opens comes from welinc-auth's answer; nothing in the portal's query string decides where the browser goes, apart from the login `request` id that goes back to welinc-auth.
- No token, code or SSO handle appears in any URL, `localStorage` or `sessionStorage` (the S3 rules, unchanged).
- The portal never auto forwards while an `error` is in the address, before or after a form sign in.
- No app sends a person with a missing session to the bare `<portal>/`; together with the rule above, nothing can bounce between the portal and an app on its own.
- A login that would end with no usable system creates no session.
- One system and no error means the launcher is never drawn.
- Access tokens keep `roles` for `aud` only; `user.systems` lives in grant answers, never in a JWT.
- The launcher's calls are never activity: viewing it doesn't extend the 30 minute idle cutoff.

**Security model**:
- `/auth/sso` reads only the caller's own session and roles. It shows system names, descriptions and role names (already public through `/auth/systems`) plus the caller's own name, email and picture. No other user's data. The `NO_SYSTEM_ACCESS` 403 carries only the caller's own email.
- `/auth/login` and `/auth/logout` keep `PortalCsrfGuard`. `/auth/sso` stays a GET without the guard (spec 0003: it changes nothing) and gains a rate limit.
- Signing out from the launcher or any app ends the shared `sid`, so every app's next refresh or status check fails within 30 seconds (spec 0003).
- No new role or permission (AC-7). Who may enter a system is still decided at `/auth/authorize` and every grant, not by the launcher: a stale card leads to `NO_SYSTEM_ACCESS` back on the portal.
- No regulated data. The launcher shows the person's own work email and name.

**Configuration required**:
- No new variables. web-vrms drops `VITE_VMMS_URL` from `.env.example`. The cards use the existing `CLIENT_<ID>_WEB_ADDRESS` values the client seed already writes.

**Critical test scenarios**:
- Happy path, three systems: `multi.lead@` opens `http://localhost:8000/`, signs in, sees BMS, VMMS and VRMS cards in that order with Operations, Operations and Chief Mechanic pills, opens VRMS with no password, clicks Switch system, sees "You're here" on VRMS, verifies **AC-1**, **AC-3**, **AC-9**, **AC-14** to **AC-16**
- One system: `vrms.admin@` signs in at the portal and lands in VRMS with no launcher; reopening the portal forwards again; Switch system is hidden in VRMS, verifies **AC-9**, **AC-13**, **AC-14**
- Deep link: signed out, open `http://localhost:8001/repairs?status=open#top` as a two system mechanic, sign in, land on that address, verifies **AC-10**, **AC-12**
- Failure, no loop: with a live session for two systems, open `http://localhost:8000/?error=LOGIN_FAILED`: the launcher with a banner, no redirect; for a one system account the same address shows its one card and doesn't forward, verifies **AC-13**
- Failure, stale tab: open the launcher, remove the user's VMMS role in another window, return to the tab: the VMMS card is gone; sign out in VRMS, return: the form with "Your session ended", verifies **AC-18**
- Auth: `POST /auth/login` with `system` gets 400; `/auth/sso` with no cookie gets 401; the 61st `/auth/sso` in a minute gets 429; a launcher URL like `/?from=https://evil.test` tags nothing and links only to registry addresses, verifies **AC-3**, **AC-4**, **AC-16**
- Catalog: an empty `description` in a catalog file makes `catalog:sync` refuse and name the file; `--dry-run` after the change shows only descriptions, verifies **AC-5**, **AC-7**

## Build plan

Tracer Bullet: a thin thread from welinc-auth through the portal to VRMS first, on real data, then the stack move and the full states, then the docs. The welinc-auth and portal branches merge together, because `/auth/login`'s body changes; backend-vrms and web-vrms are additive and may merge in the same set.

1. **welinc-auth, the answer.** The migration and `description` in the three catalog files and `catalog:sync` (refusals included); `description` in `/auth/systems`; `launcher.ts` with `LAUNCHER_ORDER` and one `heldSystems(userId)` query used by `/auth/sso`, `/auth/login` and the grants; the new `/auth/sso` and `/auth/login` bodies with the client filter and its warning; `system` removed from `LoginDto`; `login-system.ts` deleted; the `/auth/sso` limit; `user.systems` in every user grant answer. Unit and e2e tests for each. Satisfies **AC-1** to **AC-7**.
2. **The thin launcher on today's portal.** The routing rules (AC-11 to AC-14) in `lib/auth.ts` as pure functions with tests (`startFor`, `screenForAnswer` and `screenForSso`; only `error` stops the forward); a plain launcher list that opens each `url`; Sign out with its confirm. Proves the thread with `multi.lead@` before any styling. Satisfies **AC-11** to **AC-14**, **AC-17**.
3. **VRMS Switch system.** backend-vrms passes `user.systems`; web-vrms stores it, rewrites `useShellActions` (`canSwitchSystem`, `switchSystem`), updates the sidebar, user menu and phone sheet, removes `VITE_VMMS_URL`. Run the deep link check for one, two and three system accounts. Satisfies **AC-8** to **AC-10**.
4. **Portal stack move.** Tailwind v4 with the `@tailwindcss/vite` plugin, design.md tokens in `@theme`, Inter, shadcn init and the components AC-21 lists, sonner, the hex and palette lint rule. Login and forgot password move onto tokens with the same look and the improved states, existing tests kept green. Install new packages inside the portal container too. Satisfies **AC-21**, **AC-22**.
5. **The launcher, finished.** The Quiet workspace layout (top bar, greeting, card grid, icons, role pills, "You're here"), the account menu with picture or initials, the four states, the focus and visibility check, responsive columns, keyboard and reduced motion. One Playwright pass at 375px and 1280px with the one, two and three system accounts. Satisfies **AC-15** to **AC-20**.
6. **Docs.** Amend contract 0001 (AC-23), write `docs/integration/web-login.md` and link it from `docs/integration/README.md` (AC-24). Satisfies **AC-23**, **AC-24**.

## Consequences

**Positive**:
- People in several systems get one place to choose and move between them, the pattern Okta and Microsoft My Apps use, with no new login step.
- One system users never see a needless page.
- welinc-auth is the only place that knows which systems someone holds; the portal and the apps just read it.
- VMMS and BMS get a written recipe and a working reference before S11.
- The portal joins web-vrms on Tailwind v4 and shadcn, so both shared front ends use the same tokens and components.

**Negative / tradeoffs**:
- Until VMMS and BMS move in S11, their cards open those apps' own login pages, which ask for a password again. That's expected: the launcher shows the contract as it is meant to work, and the other groups adjust.
- The `/auth/login` body change needs the welinc-auth and portal PRs merged together.
- The portal stack move makes this PR larger than the launcher alone, and touches the login pages, which then need a careful look test.
- The login keeps its gradient and glows, which design.md bans. That's a deliberate exception for the login hero only, and the launcher follows design.md fully.
- Each app now trusts `user.systems` for showing a link. A stale list (between refreshes) shows or hides Switch system for at most one access token lifetime; access itself is never decided by it.

**Neutral**:
- `description` becomes a required catalog field; each group words its own line.
- The S12 notes that one, two and three system accounts "always land on the same system" stop applying: they now land on the launcher.
- `vmms-mobile` also gets `user.systems`, ready for the VRMS tab in VMMS mobile (scope feature 48), unused for now.

## Follow-up

- [ ] Update the S4 scope row with the build tasks above and this spec link (this run does it on confirmation).
- [ ] Tell VMMS and BMS once this lands: the launcher lists their system for anyone with a role there, the guide is `docs/integration/web-login.md`, and their web apps should drop `?token=` intake.
- [ ] S11: the migration guide links to `docs/integration/web-login.md` instead of repeating it.
- [ ] S9: the gateway CORS list and routes for `/vmms` and `/bms` session routes, so the guide's last step works.
- [x] Record the login hero exception (gradient and glows on the portal login only) in `design.md` (a shared file, so a workspace PR).
- [ ] `/sync`: welinc-web-portal `AGENTS.md` (Tailwind v4, shadcn, the launcher, the routing rules), welinc-auth `AGENTS.md` (the `/auth/login` body, `launcher.ts` replacing `login-system.ts`), `agents/vrms/AGENTS.md` (`tailwind-4-docs` note that the portal is still on v3), and `docs/integration/seed-accounts.md` (the "always land on the same system" note).
- [ ] S10: the suite admin will want a portal admin entry; this launcher's top bar is where it goes.
