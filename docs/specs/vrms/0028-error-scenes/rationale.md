# 0028. Error scenes: rationale

## Context

web-vrms shows every error with the same small red icon inside a shadcn `Empty`: a crash, a list that didn't load, a ticket that doesn't exist, a page you can't open, a module that is off. The portal already drew its 404 as a WeLinc road scene (suite spec 0019), and across canvas rounds 38 to 43 you picked a drawn scene for each of web-vrms's error situations. Those picks have to become code without the canvas, whose generator scripts are gone; the boards in `docs/context/vrms/error-scene-boards/` are the only source.

Three forces shape the build. First, the portal and web-vrms must look like one suite, and the scope row requires that the portal's copies can't drift from web-vrms's without a check failing. Second, the deadline: the defense is by Dec 20 at the latest and nothing is planned after it, so new build tooling across repos is expensive. Third, error screens show up exactly when things are broken (offline, a chunk failed to load, the shell crashed), so whatever draws them must not depend on anything that can fail at that moment.

The code adds detail the inventory left out. Most missing permissions redirect to the dashboard with a banner rather than showing a page; `ForbiddenPage` only guards Settings sections. A ninth screen exists ("Can't reach the sign in service" in `RequireAuth`), and so do a ticket 403 and the knowledge base's own not found. The handoff said "No VRMS access" reuses a Round 34 gate scene, but the portal's `R34NoAccess` is the sign in split with the map, not a gate. The boards also change some copy (the no access title, "Nothing you saved is lost."), while spec 0025's crash copy must stay.

## Options considered

### Sharing: copies plus a drift check (chosen)

The same files sit in both apps under `src/components/brand/scenes/` plus `src/styles/scenes.css`, and a workspace script compares them byte for byte.

**Pros**: no new build, CI or Docker setup in either repo; each app builds alone as today; the check is the same kind as `check-design-tokens.mjs`, which the team already knows.
**Cons**: every kit change is two pull requests; drift is caught on the next CI run, not inside the app's pull request.

### Sharing: a shared package

One package (a git dependency or a workspace package) imported by both apps.

**Pros**: drift is impossible; one place to edit.
**Cons**: both Dockerfiles, both CI pipelines and both Vite configs change to resolve and build it; Tailwind v4 has to scan the package's classes; a version bump becomes a third step. All of that lands weeks before the defense, for about 20 drawings.

### Sharing: hand copies with no check

**Pros**: zero setup.
**Cons**: the copies drift unnoticed, which the scope row rules out.

### Where the check runs: workspace CI plus by hand (chosen), by hand only, each app's CI

The workspace `ci.yml` already checks out welinc-auth at `development` for the contract routes job and runs daily at 06:00 Manila, so a `scenes` job fits the same pattern. By hand only (like `check-design-tokens.mjs`) fails only when someone remembers. Each app's CI comparing against the other app's `development` blocks a pull request in one repo until the other catches up, which turns every kit change into a deadlock dance.

### What the check compares: whole files (chosen) or files plus parsed tokens

Moving the scene tokens and utilities into their own `scenes.css` lets the check compare whole files with no parsing, and makes "what is shared" a folder and a file anyone can see. Leaving them in each `index.css` keeps the portal untouched but needs a parser for tokens and `@utility` blocks, which is more code and more room for a gap.

### Drawing technique: inline SVG components with CSS loops (chosen), SVG files, or an animation runtime

Inline SVG in React with Tailwind `@utility` keyframes is exactly how the portal's 404, launcher band and launches are built, so there is nothing new to learn and the tokens drive every colour. SVG files loaded as images can't use the CSS tokens or the reduced motion utilities and would need a fetch. An animation runtime (a Lottie style player) adds a dependency and a design tool the team doesn't use, for loops CSS already does.

### Lazy loading the kit (rejected)

Splitting the scenes into their own chunk would trim the main bundle, but the screens that need them most are offline, a failed chunk load, or a crashed shell, where fetching another chunk fails. The size is accepted and measured instead.

## Rationale

Copies plus a check win because the deadline makes build plumbing across repos the expensive part, and the kit is small and changes rarely once drawn. The cost (two pull requests per change, drift caught by the next morning) is real but bounded, and the check makes it visible. A package would be right for a suite that keeps growing; this one ends at the defense.

Two layouts follow the rule already in the handoff: an error inside the shell keeps the sidebar and top bar and gets a 720px panel, and only an error outside the shell (or of the shell) gets the full page band like the 404. Choosing page or tile "by what the failure replaces" keeps one dashboard with three failing cards from stacking three big scenes, while a whole list that didn't load still gets the idling truck. Routed Settings sections count as pages, because each one is the whole content of its route.

For the screens the boards left open: the gate stands for "you can't go in" everywhere, so it covers `ForbiddenPage`, the ticket 403 and (drawn wide) "No VRMS access", instead of copying the portal's sign in split and map into web-vrms for one screen. "Can't reach the sign in service" reuses the permissions pair, because both mean "we couldn't confirm who you are", and the reader's sign already says NO ANSWER FROM DISPATCH. It gets no Sign out, since signing out needs the service that is down. The knowledge base's not found uses only the drawer, since the empty bay is a repair bay and reads as a ticket. You chose a tile per subject over stretching five drawings, so the seven new tiles go through one board round first, the same way every other scene was picked.

Random pairs pick once per visit and stay put, so a failed Try again doesn't look like something changed. Reduced motion stops everything on a frame that still tells the story, which is what `design.md` already promises ("scenes standing still").

## Board history

Rounds 38 to 43 on the "WeLinc design directions" canvas; the rejected boards were left on the canvas. The picked boards and the rules from your notes are in [`docs/context/vrms/error-scene-boards/README.md`](../../../context/vrms/error-scene-boards/README.md) and the 2026-11-26 handoff (item 2). Rejected along the way for no access: every sign on the gate (Round 40); the door, shutter, turnstile, stairs and dock (Round 41); the container, aisle and fuel island (Round 42); the lanes, weighbridge, wall and spikes (Round 43).
