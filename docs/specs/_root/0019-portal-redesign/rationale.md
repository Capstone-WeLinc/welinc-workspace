# 0019. Portal redesign: rationale

## Context

The portal is the first screen everyone in the suite sees, and the defense panel sees it first too. Spec 0016 gave it the Control room look, but the launcher, sign in and Suite management screens were still the pre redesign layouts. Rounds 12 to 37 (Nov 24) settled every screen on the canvas: the navy band launcher with a line drawing and livery trucks, sign in A with the branch map, four step forgot password, the Suite management shell, the filter popover, Add a user, the toasts, the 404 page, the reset email and the logo by place.

Three gaps sit under the boards. First, `screenForAnswer` sends anyone with one web system and no `ADMIN` there straight into that system, and the launcher answer doesn't say who is a suite admin, so a suite admin whose only role is temporary never reaches Suite management. Second, the Suite management strip shows counts, but the only route with them (`/auth/admin/report`) asks for the admin step up code, which would pop a prompt on the launcher. Third, Add a user checks the email as you type, but `users/lookup` matches partially and leaves out people who already hold the system, so it can't say "free" honestly.

The "Signed in until" pill drawn on early boards shows the 12 hour limit, while the 30 minute idle limit usually ends the session first, so the time is often wrong. The portal and web-vrms already warn with a banner two minutes before the cutoff (spec 0016 AC-12 to AC-12b), with careful timing, retry and cross tab rules.

The portal has no animation library (only `tw-animate-css` for shadcn parts). The launcher motion has three linked pieces: an arrival that must hand a truck into a running loop at the same speed, the loop itself, and a launch that plays while the browser leaves the page. The deadline is moving (final by Dec 20 at the latest, mock defense first), so the plan must survive losing the last milestone.

## Options considered

### Option 1: Restyle the existing screens in place

Keep the current launcher, sign in and shell structure and restyle them toward the boards, with CSS only motion.

**Pros**:
- Smallest change, no new dependency, no welinc-auth change.

**Cons**:
- The boards change structure, not only style (the strip, the switcher, the four step forgot password, the one screen dialog), so a restyle can't reach them.
- Leaves the suite admin gap and the step up prompt on the launcher.
- The arrival to loop hand off is hand written timing code.

### Option 2: Rebuild from the boards in milestones, motion last, with Motion and additive auth routes (chosen)

Build each board on spec 0016's tokens and components, add `suiteAdmin`, a counts only summary route and an exact email check to welinc-auth, and add Motion lazily as the last milestone.

**Pros**:
- Matches the picks exactly, closes all three gaps with additive changes.
- Motion handles exit animations, value hand off and reduced motion out of the box; loaded only where it's used.
- A static launcher is a complete, demoable state if motion slips.

**Cons**:
- A new dependency and three contract changes.
- More screens to verify against boards.

### Option 3: Rebuild with CSS keyframes and Web Animations only

As Option 2 but without a library: the loop as an infinite CSS translate, the arrival and launch with `element.animate()`.

**Pros**:
- No dependency; the lightest bundle.

**Cons**:
- Matching the arrival truck's position and speed into the loop, and cancelling cleanly on navigation or reduced motion, is custom code nobody else on the team knows.
- No exit animation story for the cards and toasts beyond what shadcn gives.

### Option 4: GSAP timelines

**Pros**:
- The strongest timeline tool, free since 2025.

**Cons**:
- Heavy for three short sequences, imperative and not idiomatic in React, and a second mental model beside Tailwind's motion tokens.

## Rationale

Option 2 is the only one that reaches the boards: they change structure, so restyling (Option 1) stops short, and the three data gaps need welinc-auth changes anyway. Each auth change is additive (a field and two read routes), which contract 0001 allows cheaply while the shared repos are closed.

Motion over CSS only (Option 3) is a team cost call: the arrival must hand off into the loop at the same speed, and the launch must cancel or fade cleanly under reduced motion. Motion's declarative API, `useReducedMotion` and `AnimatePresence` make that ordinary React code; with `LazyMotion` and `domAnimation` it costs about 15 to 20 kB, only on the sign in and launcher screens. GSAP (Option 4) solves a bigger problem than this one.

Ordering motion last answers the moving deadline: every milestone before it leaves a complete screen, and a parked truck launcher is already the reduced motion design, so it is not a stopgap.

**Smaller calls made in this spec** (the runner up in brackets):
- **Counts only summary route, no step up** (require step up): three numbers with no person data don't justify a code prompt on the front page; every list behind them still asks.
- **A new exact email check route** (reuse `users/lookup`): lookup matches partially and leaves out people already in the system, so it can't tell "free" from "already here"; a narrow route with five statuses gives the dialog honest answers and exposes less.
- **Arrival flag in memory only** (a `sessionStorage` flag): spec 0003 AC-36 keeps session hints out of storage, and a reload not replaying the arrival is the intended behaviour.
- **Launch 3 never delays navigation** (play, then navigate): the animation hides load time instead of adding it, and real links keep new tab clicks working.
- **The idle toast keeps 0016's timing modules** (rewrite them): only the surface changes; the retry, clock gap and cross tab rules were hard won and are tested.
- **A soft navy ring on the sign in split fields** (0016 AC-7's border only): the board shows it and sign in is a brand surface; working pages keep AC-7.
- **"Your profile" hidden until S23** (link to a placeholder): a menu item that lands on a 404 looks broken in a demo.
- **Code email layout for all four code emails** (reset only): they share helpers in `code-emails.ts`, and mixed looks read as a bug.
- **One `access` list for systems and roles** (separate `systems` and `roles` params; a POST search body): each item is exactly one row or chip of the popover, so there is nothing for two params to disagree on, and a GET keeps the address shareable and skips the CSRF guard. `system` keeps meaning the scope, so the strip's `viewHref` links and spec 0017's rules don't move.
- **A separate facets route** (facets on every list answer; no chip counts): the counts are needed only while the popover is open and change with a draft the list hasn't applied yet, so a list answer can't carry them, and putting them on every page would pay for them on each Load more.
- **Each facet ignores its own filter** (every count under every filter): the usual faceted search rule; otherwise ticking one role drops every other role to 0 and the counts stop helping you choose.
- **`ATTENTION` and `ACTIVE_GROUP` as status values defined by `groupWhere`** (the portal translating chips to today's six statuses): today's `ACTIVE` leaves out unverified emails and `PENDING_DELETION` ignores deactivation, so a translation would drift from the groups People shows. Reusing `groupWhere` keeps one rule, as the summary route already does.
- **Any of within a facet, AND across facets** (all of across systems): what the board's "Show N people" sum implies and what every filter UI the team has used does; finding shared accounts stays with the person page's system chips.

## Update (2026-11-25)

The People filter API (AC-21 to AC-21b) was added once the auth milestone showed `GET /auth/admin/users` could only take one system and one role, while `Filter18` ticks several of each and counts every chip. Two lines were also corrected against the boards: AC-27's email logo is A (gold on the navy header, `R35LogoPlaces`; the built `scripts/email-logo.mjs` already draws A), and AC-18's collapsed footer shows only the expand button (`Shell20`).

## Update (2026-11-25, during the build)

Building AC-21b showed its query shape could not hold together with its own rule. It asked for one SQL count with a `FILTER` clause per status chip, and also for every count to use the list's `statusWhere` and `groupWhere`. Those helpers are Prisma where objects, and Prisma 7 cannot turn a where object into SQL, so the `FILTER` shape would mean writing the lock, setup and pending deletion rules a second time in raw SQL. That copy would drift the first time someone changes a rule in `people-page.ts`, and the counts would stop matching the list, which is the whole point of the facets. So the route runs parallel Prisma counts on the same helpers (about ten small indexed counts, the pattern `groupCounts` already uses for People's three groups). Two raw SQL queries stay the option for later, if People is measurably slow at a much larger head count.

Two test lines were also wrong. One expected a duplicate `access` item to answer 400, while AC-21a says duplicates are normalized away; AC-21a is the contract (a shared link that repeats a pick should still load), so the test line now follows it. The same lines used `VMMS:DRIVER`, but Driver is a BMS role; they now use VMMS Mechanic and BMS Driver.

## Interview record (2026-11-24)

- Delivery: everything before the mock defense, motion as the last milestone.
- Motion library: Motion, lazy loaded. Launch 3: in scope.
- Strip counts: new counts only route, no step up; "Users need a look" is People's Needs attention group.
- Idle warning: 2 minutes, a toast in the portal and web-vrms, "Still there?" wording, the 12 hour end as the same toast without an action.
- Screen fix: `suiteAdmin` in the launcher answer.
- Reduced motion: parked scene. Loop: pause when hidden. Arrival: only right after sign in. Launch: about 900 ms with navigation at once. Phones: short band, parked trucks.
- Switcher: the held launcher answer. Email check: any admin, exact email only. Emails: all code emails, one layout. Wait: busy buttons and reloads, skeletons stay.
- Tab titles: page first, "WeLinc" last. Sign in messages: endings as toasts, errors inline. 404: any unknown address.
- People filter (2026-11-25): one `access` list; a facets route for the chip counts; the board's five status chips on the server's group rules; any of within a facet, AND across.
- Facets query shape (2026-11-25, found during the build): parallel Prisma counts on the list's own where helpers, not two raw SQL queries; a duplicate `access` item is normalized, not refused (AC-21a wins over the old test line).

## Update 2026-11-26

The launcher, the launch and the sign in went through more design rounds after this spec was written (launcher Rounds 49 to 69, sign in Round 47; history in `docs/context/vrms/portal-redo-boards/README.md`). This update brings the spec in line. The calls, with the reason for each:

- **The launcher is calm.** No greeting, no moving vehicles or road, no map, no counts. You found the road "too distracting", and counts on the Suite management tile repeated what People shows one click later. Tiles (L1, N3 text, three to a row, P5 number keys) read like the module launchers people already know.
- **A suite admin with no system role skips the launcher.** A suite admin can never hold a system role (spec 0013 AC-33), so the launcher only ever showed them one tile. Products with one destination per account (Google Admin, Okta, Microsoft Entra) send that account straight there. Rejected: filling the launcher with Suite management's areas (it breaks the rule that only systems and one Suite tile are clickable, and it repeats the sidebar), and keeping the one tile (a wasted click on every sign in).
- **`GET /auth/admin/summary` is removed, not kept unused.** Its only reader was the count on the strip, which is gone. It was the one admin route that skips the sign in code, so keeping it with no caller adds attack surface and maintenance for nothing. It was never merged, so removing it costs only the branch work.
- **CSS in place of the Motion library.** Option 3 below was rejected when the launcher had a truck loop and a braking hand off between Arrival 2 and the loop, which needed a library's springs and shared timing. Those are gone. What is left (the A3 tile slide, three launch scenes of at most 900 ms, the sign in trucks on SVG paths) is plain keyframes, the same way Admin already does motion. This drops a 32.5 kB lazy chunk and a dependency, and reduced motion becomes one media query. The cost is throwing away the built Motion milestone.
- **The launch is random among Launches 2, 3 and 4, never the same twice in a row.** Your call over one launch per system. The last scene id sits in `sessionStorage` because the page unloads after every launch, so memory alone cannot remember it; it holds a digit, nothing about the person or session, so spec 0003 AC-36 still holds. Launch 1 (the boom gate) is out.
- **The sign in is S27d Quiet** (Round 47) in place of `R37SignIn`: the drawn map under the whole page with the form on navy glass. The map is traced from OpenStreetMap, so the page carries the ODbL credit. The code step and forgot password on it are still to draw; AC-14 keeps Round 31's steps until then.
- **No help button**, although the boards draw a "?": there is no help page behind it, the same reason Privacy and Terms were left out.
- **The phone layout is designed during `/develop`**, not drawn first (your call), and recorded in AC-4 then.
