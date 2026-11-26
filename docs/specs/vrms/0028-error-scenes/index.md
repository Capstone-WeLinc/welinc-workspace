# 0028. Error scenes: a drawn road and depot scene for every error state

**Date**: 2026-11-26
**Status**: Proposed
**Scope row**: [73](../../../scope/vrms/ui-refresh.md#73-error-scenes--in-progress) (`docs/scope/vrms/ui-refresh.md`)
**Repos**: `welinc-web-vrms` (every scene), `welinc-web-portal` (the same scene kit, its crash screens, failed loads and small errors), the workspace (`scripts/check-scenes.mjs` and a CI job)
**Design source**: the picked boards in [`docs/context/vrms/error-scene-boards/`](../../../context/vrms/error-scene-boards/README.md) (canvas rounds 38 to 43), the portal's `R34NotFound` in [`docs/specs/_root/0019-portal-redesign/boards/`](../../_root/0019-portal-redesign/boards/), and the new tile board from task 1. Rules from suite `design.md` and `docs/context/vrms/design.md` hold where the boards are silent.
**Related**: [0025](../0025-error-monitoring/index.md) (the crash screen's copy and behaviour, unchanged here), suite [0019](../../_root/0019-portal-redesign/index.md) (the portal's 404 road, `LiveryTruck`, `scene-blink`), suite [0016](../../_root/0016-design-direction-refresh/index.md) (tokens, motion)

## Summary

Every error a person can hit in VRMS stops being a small red icon and gets its own drawn WeLinc scene instead: a truck with its hazards on for a crash, an idling truck with an empty cargo box for a page that didn't load, a chained gate for no access, and so on. The words stay almost the same; the picture changes. The scenes are plain SVG (a drawing format the browser renders) inside React components, kept as identical copies in web-vrms and the portal, and a workspace check fails when the two copies drift apart. Nothing in the backend changes.

## Requirements

**User stories**:
- As a mechanic, I want an error to look like part of the app and tell me plainly what happened, so that I know whether to retry, go back or ask an admin.
- As an admin, I want a crash to still show me the details and Copy details, now inside the new panel, so that bug reports keep working.
- As the team, we want the portal and VRMS to share one set of drawings that cannot drift, so that the suite looks like one product at the defense.

**Acceptance criteria**:

*The scene kit (both apps)*
- **AC-1**: Both apps hold the same scene kit: every file under `src/components/brand/scenes/` and the file `src/styles/scenes.css`, byte for byte identical once line endings are normalized. The kit is the `.ts` and `.tsx` files in that folder and its subfolders plus `scenes.css`; tests never live in the folder (they sit beside it, per app, for example `src/components/brand/scenes.test.tsx`). Kit files import only `react`, `@/lib/utils` and other kit files by relative path (`./`), so a copy that compiles in one app compiles in the other. Kit classes use only tokens and utilities defined in both apps' `@theme` (the byte check can't see a missing class). `src/styles/scenes.css` holds every `--scene-*` and `--livery-*` token (in `:root`) and every scene motion utility (`scene-blink` and the rest), and each app's `src/index.css` pulls it in with `@import './styles/scenes.css'` after `@import 'tailwindcss'`, never from `main.tsx` (Tailwind would not process its `@utility` blocks there). Motion utilities that rotate, scale or move set `transform-box: fill-box` and their own `transform-origin`, as the portal's `wheel-turn` does. Colors the kit borrows from the theme (`--highlight`, `--sidebar`, `--white`, `--card`, the text tokens) stay in `index.css`, where `check-design-tokens.mjs` already keeps them equal.
- **AC-2**: `node scripts/check-scenes.mjs [vrms root] [portal root]` (defaults: `welinc-web-vrms` and `welinc-web-portal` beside it) exits 0 when the two kits match, and otherwise exits 1 naming each problem: a file in only one app, a file whose bytes differ (with the first differing line), or a kit file importing outside AC-1's list. Before comparing it normalizes CRLF to LF, strips a leading BOM and ignores a missing final newline. Imports are found in every form: `import … from`, `import type`, a bare `import '…'`, `export … from`, dynamic `import('…')`, and `@import` in `scenes.css` (which may import nothing). A `./` or `../` path is allowed only if it resolves (with or without `.ts`, `.tsx` or `.js`) to a kit file. The workspace `ci.yml` gains a `scenes` job, skipped when the workflow runs through `workflow_call` (the gateway deploy must not fail on web drift): it checks out `Capstone-WeLinc/welinc-web-vrms` and `Capstone-WeLinc/welinc-web-portal` at `development` into the paths `welinc-web-vrms` and `welinc-web-portal` (both public, no token, `persist-credentials: false`), sets up Node 24 with `actions/setup-node@v7`, and runs the script on push, pull request, the daily 06:00 Manila schedule and a manual run. `scripts/test/check-scenes.test.mjs` covers a match, a missing file, a changed byte, CRLF, BOM and final newline only differences (pass), and one bad import per import form.

*Two layouts*
- **AC-3**: **Scene panel** (an error inside the app shell): a white card 720px wide (`max-w-180`, full width below that), rounded and shadowed as on the boards, centred in the page area, with the navy scene on top (`viewBox 0 0 720 220`, scaled down whole on narrow screens, never cropped) and the text below: title (an `h2`, since the page keeps its own `h1` header), line (optional; the ticket 403 has none), any extra content (the admin crash details), then the buttons. The sidebar and top bar stay. A call site that wrapped its error in its own card (`RepairListPage`, `HistoryPage`, `AuditLogsPage`, `KnowledgeEditorPage` and the like) drops that wrapper, since the panel is the card.
- **AC-4**: **Scene band** (a full page error, outside the shell or when the shell itself failed): a `<main id="main">` (it replaces `CenteredPage`, which is deleted) with the navy band across the top holding the app's own brand lockup (web-vrms: `BrandMark tone="sidebar"` with its existing text; portal: `BrandLockup`). The lockup a band receives is never a router `Link`, because the full page crash renders above the Router (`main.tsx`); the 404 may wrap it in a link to home. Then the scene (`viewBox 0 0 1440 260`, `preserveAspectRatio="xMidYMax slice"`, height `h-40` and `sm:h-65` as the portal's 404), then the text centred below on the page background, its title an `h1`. The band crops from both sides on narrow screens, so every band scene keeps its subject (truck, pole, gate, reader) between x 420 and x 1020; the portal's road scene is reused as it stands. Lane lines run the whole width.

*Each situation (web-vrms)*
- **AC-5**: **Crash inside the app** (`CrashScreen variant="page"`): the scene panel with the hazard glow scene (`R39CrashGlow`: the truck stopped on a darkened road, hazards blinking amber onto the asphalt, steam from the engine). Spec 0025 AC-7 and AC-7a hold unchanged: the title "Something went wrong on this page", the staff line with or without a code, the reference code, and for admins the line, the details box and Copy details inside the panel, then Reload and Back to dashboard. Only the title and line sit in the alert: the staff reference code moves out of it (today it is inside), on purpose, so a screen reader announces the message and the code stays on screen. Spec 0025's `CrashScreen` tests, written against the shadcn `Empty` markup, are rewritten with the same assertions on the new structure.
- **AC-6**: **Full page crash** (`CrashScreen variant="full"`): the scene band with the snapped line on the pole (`R43FullPole`, no fusebox; of the four lamps one flickers, two are nearly out with a faint flicker, one is dark). The copy is spec 0025's, word for word, as in AC-5 (the board's shorter title is not used). Back to dashboard stays a plain `<a href="/dashboard">`.
- **AC-7**: **Page didn't load** (`ErrorState kind="page"`): the scene panel with the idling truck (`R39LoadIdle`: the cargo box open and empty, the empty spots blinking in turn, exhaust puffs, the truck rocking slightly). The title and message stay each call site's own; under the message a second line reads "Nothing you saved is lost.", except on `RepairDetailPage` and `KnowledgeEditorPage`, where unsaved drafts (`lib/drafts`) can exist and the claim isn't safe (a `reassure={false}` prop turns it off); the retry button keeps its call site's label. The call sites are listed in *Call sites* below.
- **AC-8**: **Small errors in cards, sections, tabs, charts and dialogs** (`ErrorState kind="tile" subject=…`): a light line art tile (`viewBox 0 0 120 88`) above the title, message and retry, as on `R39SmallMatched`, with no navy scene and no "Nothing you saved is lost." line. There are 12 subjects: the five picked (`devices`, `history`, `tickets`, `trucks`, `parts`) and seven drawn in task 1 (`activity`, `charts`, `settings`, `people`, `knowledge`, `roles`, `list`). `subject` is required with `kind="tile"`, so the type rejects a tile without one.
- **AC-9**: **Record not found**: "Repair ticket not found" (`RepairDetailPage`, a 404) shows the scene panel with one of two scenes picked per AC-16: the empty bay (`R40NotFoundBay`: the lamps flicker hard and the bay dims, tyre tracks, an oil stain, the empty RT-0999 hook) or the ticket drawer (`R39NotFoundDrawer`: the drawer slides out, the 0999 folder missing). Copy from the board: "Repair ticket not found" / "It may have been deleted, or the link has a typo. Check the ticket number and try again." / Back to repairs. "This entry isn't available." (`KnowledgeEntryPage` and `KnowledgeEditorPage`, a 404 or 400) shows the scene panel with the drawer scene only, its copy and button unchanged. The drawn number stays RT-0999 and 0999; a scene never shows the number you asked for.
- **AC-10**: **No access to a page**: `ForbiddenPage` (a Settings section opened without its key) shows the scene panel with the gate (`R43Gate`: a palisade gate chained shut with a swinging padlock, a hooded bullet CCTV camera aimed down at the gate and panning slowly, never up at the sky, an amber beacon, the guard hut with a lit window; no sign on the gate). New copy: "This page needs a different role" / "Ask an admin to give you access if you need it for your work." / Back to dashboard. "This ticket isn't assigned to you" (`RepairDetailPage`, a 403) shows the same gate panel with its title and Back to repairs unchanged. Pages that send you to the dashboard with the no access banner (`RequirePermission`) keep doing that.
- **AC-11**: **Module turned off** (`ModuleOffPage`): the scene panel with the shutter down and the Closed for now sign (`R38OffA`). Copy unchanged: "<Module> is turned off" / "This module is turned off by your Admin. Its data is kept for when it comes back." / Back to dashboard.
- **AC-12**: **No VRMS access** (`PermissionsGate`, signed in with no VRMS keys): the scene band with the gate scene drawn wide (the same gate, guard hut, camera and beacon centred at x 720, the fence, ground and road carried out to the band's full width). Copy and Sign out unchanged: "No VRMS access" / "Your account has no permissions in VRMS. Ask an admin to give you a VRMS role."
- **AC-13**: **Permissions didn't load** (`PermissionsGate`, the first fetch failed): the scene band with one of two scenes picked per AC-16 (`R43PermSwitch`): the card reader (the pass lands flat on the reader, contact arcs pulse, the light blinks amber and never turns green) or the lanyard rack (your pass blank). Copy from the board: "Could not load your permissions" / the call's message, or "Check your connection, then try again." / Try again, and a new outlined Sign out (the board's), which runs `signOutFlow({ ask: false })` as the no access screen does.
- **AC-14**: **Sign in service unreachable** (`RequireAuth`, `status === 'unavailable'`): the same band and pair as AC-13, picked per AC-16. Copy and Try again unchanged ("Can't reach the sign in service" / "Check your connection, then try again."); no Sign out, since signing out needs the service that can't be reached.
- **AC-15**: **Page not found** (`NotFoundPage`, any address web-vrms doesn't know): the scene band with the portal's road scene (`R34NotFound`, the truck stopped at a road barrier, its lamps blinking), and the portal's copy: "Error 404" / "Wrong turn" / "This page doesn't exist or has moved. Head back and pick another route." / Back to dashboard (a router link to `/dashboard`).

*Behaviour (both apps)*
- **AC-16**: A screen with two scenes picks one when it appears (`useScenePick(2)`, a `useState` initializer over `Math.random`) and keeps it until it unmounts, so a failed Try again never swaps the picture; the next visit picks again. `useScenePick` takes an optional random function so tests can fix the pick. Where a retry swaps the error for a skeleton and back (`PermissionsGate`, `RequireAuth`), the hook is called at the top of that component, before its early returns, and the pick is passed down, so the remount doesn't pick again.
- **AC-17**: Every scene's motion loops (no one time entrance), animates only `opacity` and `transform` except the board's colour pulses (the empty spots' fill), and stops entirely under `prefers-reduced-motion: reduce` or inside an element with `data-motion="still"`. Stopped, each scene rests on a frame that still tells its story: hazards and beacons lit, the flickering lamp on, the camera aimed down at the gate, the drawer out, the pass on the reader, the bay dimmed but visible. Transient puffs, steam and sparks are hidden in the still frame.
- **AC-18**: Every scene and tile is an `<svg aria-hidden="true" focusable="false">`; the words on it (CLOSED FOR NOW, STOPPED, NO ANSWER FROM DISPATCH, RT-0999, WeLinc) are decoration and are never the only place a fact is said. Scenes never show live data (names, plates, ticket numbers, roles). In panels and bands the alert role sits on the title and line only (today `ErrorState` puts it on the whole block, button included); a tile is silent except for a `role="status"` on its title and message, so several failing cards don't interrupt each other. Focus behaviour is unchanged. Each scene's `data-scene` name is one of: `crash`, `pole`, `load`, `not-found-bay`, `not-found-drawer`, `closed`, `gate`, `gate-wide`, `reader`, `lanyard`, `road`, `tile-<subject>`.
- **AC-19**: The seven new tile subjects (AC-8) are drawn first on one board in the `R39SmallMatched` style (light line art on the white card, matching the five picked tiles in stroke weight and size), two takes per subject, screenshotted and checked before you see them. Once you pick, the picked board is copied into `docs/context/vrms/error-scene-boards/` with a row in its README, and the build follows it.
- **AC-20**: web-vrms's `/dev/ui` (dev builds only, as today) gains a Scenes section: every panel scene, band scene and tile, both picks of each random pair side by side, and a Still switch that sets `data-motion="still"` on the section to show the reduced motion frames. Nothing of it reaches a built app.

*The portal slice*
- **AC-21**: The portal moves its scene parts into the kit with no visible change: `LiveryTruck.tsx` (all three vehicles) into `src/components/brand/scenes/`, the road scene from `NotFound.tsx` into a kit file, and every `--scene-*`, `--livery-*` token and `scene-blink` from `index.css` into `src/styles/scenes.css`. The launch, sign in and launcher drawings keep looking and moving exactly as now; the `--signin-*` tokens and the `launch-*` utilities stay in `index.css`.
- **AC-22**: Then the portal uses the scenes: `CrashScreen variant="page"` (in `AdminShell`, `LauncherShell` and `LauncherFrame`) gets AC-5's panel and `variant="full"` (in `main.tsx`) gets AC-6's band, both with spec 0025's portal copy (Back to apps, to `/`: a `Link` in the page version, `<a href="/">` in the full one); `LauncherError` ("We couldn't load your systems.") and `AdminPage`'s load failure ("We couldn't load Admin.") get AC-7's panel; `ViewError` takes the same `kind` and `subject` as `ErrorState`, mapped in *Call sites*. `ViewError` has no title today: it gains an optional `title` defaulting to "We couldn't load this", its message stays the call site's, and its button stays "Retry" with its icon. "No access yet" (the sign in split, `R34NoAccess`) and the 404 (its copy, "Back to home" and `/`) stay as they are. In the launcher a scene replaces only the tiles below the band, which keeps the launcher's calm top.
- **AC-23**: Unchanged in both apps: the offline banner, toasts, field errors, form alerts, skeletons, empty states that are not errors ("No activity yet" and the like), the no access banner after a redirect, and the one line text failures inside a working view ("Couldn't load older events" in `AuditTimeline`, `DeleteAccountCard`'s line, the portal's "We couldn't load more …" rows).

## Decision

**Chosen options**: inline SVG scene components with CSS loop utilities, kept as identical copies in both apps under `src/components/brand/scenes/` plus `src/styles/scenes.css`, guarded by `scripts/check-scenes.mjs` in workspace CI; two layouts (panel inside the shell, band for full page); `ErrorState` and the portal's `ViewError` choose page or tile by what the failure replaces.

The scene kit ships in each app's main bundle and is never lazy loaded: the screens that need it most (offline, a failed chunk, a crashed shell) are exactly the ones where fetching another chunk fails.

**Implementation skills**: `tailwind-4-docs` (`.claude/skills/tailwind-4-docs/`, the `@utility` and `@import` rules for `scenes.css`) · `vercel-composition-patterns` (`.claude/skills/vercel-composition-patterns/`, `ScenePanel` and `SceneBand` take slots instead of boolean props). Offer, never run on their own: `emil-design-eng` (looping motion, reduced motion), `web-design-guidelines`.

## Feature design

**Data model**: none. No backend, schema or API change.

**The kit** (identical in both apps; names are the build's to keep):

| File | What it is |
|---|---|
| `scenes/ScenePanel.tsx` | AC-3's card: `scene` (an SVG node), `title`, `line`, `children` (extra content), `actions`, and `alert` (default true) to put the alert role on the title and line |
| `scenes/SceneBand.tsx` | AC-4's full page layout: `lockup` (each app passes its own), `scene`, `eyebrow?`, `title`, `line`, `children`, `actions` |
| `scenes/useScenePick.ts` | AC-16 |
| `scenes/LiveryTruck.tsx` | moved from the portal: `LiveryTruck`, `LiveryVan`, `LiveryL300` |
| `scenes/CrashScene.tsx`, `LoadScene.tsx`, `NotFoundBayScene.tsx`, `NotFoundDrawerScene.tsx`, `ClosedScene.tsx`, `GateScene.tsx` | the 720 by 220 panel scenes; `GateScene` also takes `wide` for AC-12, drawing its backdrop at 1440 by 260 with the subject centred |
| `scenes/PoleScene.tsx`, `ReaderScene.tsx`, `LanyardScene.tsx`, `RoadScene.tsx` | the 1440 by 260 band scenes (`RoadScene` is the portal's `RoadBlock`) |
| `scenes/ErrorTile.tsx` | AC-8's tiles: `subject` picks one of 12 drawings; exports the `TileSubject` type |
| `styles/scenes.css` | tokens in `:root`, one `@utility scene-<motion>` per motion (blink, flicker, puff, steam, rock, sway, pan, arc, pulse, glow and so on as the boards need), each with `animation: none` under reduced motion and under `[data-motion='still']` |

Each scene's root `<svg>` carries `data-scene="<name>"` (for example `crash`, `load`, `not-found-bay`, `gate-wide`, `tile-devices`), so tests and `/check verify` can tell which scene drew. Every element's resting attributes are its still frame (AC-17); keyframes only move away from it and back.

**`ErrorState` (web-vrms) and `ViewError` (portal)**: a union prop, so each call site chooses on purpose:

```ts
type ErrorStateProps =
  | { kind: 'page'; title?: string; message: string; onRetry?: () => void; retryText?: string }
  | { kind: 'tile'; subject: TileSubject; title?: string; message: string; onRetry?: () => void; retryText?: string };
```

`DataTable` takes `errorKind` (default `'tile'`) and `errorSubject` (default `'list'`) and passes them on.

**Call sites, web-vrms** (from `origin/development` on 2026-11-26; a new call site follows the same rule: emptying the page's main content means page, otherwise tile):

| Call site | Now | Becomes |
|---|---|---|
| `CrashScreen` page / full | icon | crash panel (AC-5) / pole band (AC-6) |
| `App.tsx` `RequireAuth` unavailable | `ErrorState` in `CenteredPage` | reader or lanyard band (AC-14) |
| `PermissionsGate` error / no keys | `ErrorState` / `EmptyState` | reader or lanyard band (AC-13) / wide gate band (AC-12) |
| `NotFoundPage` | plain card | road band (AC-15) |
| `ForbiddenPage` | `EmptyState` | gate panel, new copy (AC-10) |
| `ModuleOffPage` | `EmptyState` | closed panel (AC-11) |
| `RepairDetailPage` 404 / 403 / other | `EmptyState` / `EmptyState` / `ErrorState` | bay or drawer panel (AC-9) / gate panel (AC-10) / page |
| `KnowledgeEntryPage`, `KnowledgeEditorPage` 404 | `EmptyState` | drawer panel (AC-9) |
| `RepairListPage`, `HistoryPage`, `AuditLogsPage`, `ProfilePage`, `AdminDashboard`, `ChiefDashboard`, `MechanicDashboard`, `KnowledgeLibraryPage`, `KnowledgeEntryPage` (load), `KnowledgeEditorPage` (load), `KnowledgeSuggestionsPage` | `ErrorState` | `kind="page"` |
| `ModulesSection`, `ThresholdsSection`, `HistorySection` (each is a routed Settings page) | `ErrorState` | `kind="page"` |
| `RecentActivityCard` | `ErrorState` | tile `activity` |
| `SignedInDevicesCard` | `ErrorState` | tile `devices` |
| `ChartPrimitives` (an Analytics section) | `ErrorState` | tile `charts` |
| `TeamSection` | `ErrorState` | tile `people` |
| `ChangeHistoryDialog` (knowledge base) | `ErrorState` | tile `history` |
| `VehicleHistoryDialog` | `ErrorState` | tile `trucks` |
| `DataTable` | `ErrorState` | its props, default tile `list` |
| `UsersPage`, `VehiclesSection`, `LookupListPanel` (each a routed page whose content is the table) | `DataTable` error | `errorKind="page"` |
| `CategoriesPanel` (knowledge base) | `DataTable` error | tile `list` (the default) |
| `DataTableSection` (dev UI) | `DataTable` error | the default |
| `DataDisplaySection` (dev UI) | `ErrorState` | one of each kind |

The `tickets`, `parts`, `settings`, `knowledge` and `roles` tiles have no web-vrms call site yet; they are drawn because they are picked or needed by the portal, and the gallery shows them.

**Call sites, portal**:

| Call site | Becomes |
|---|---|
| `CrashScreen` page (`AdminShell`, `LauncherShell`, `LauncherFrame`) / full (`main.tsx`) | crash panel / pole band |
| `LauncherError`, `AdminPage` load failure | `kind="page"` panel |
| `OverviewView`, `ActivityList`, `SuiteAdminsView`, `TemporaryAccessView` | `ViewError kind="page"` |
| `DeletionRequestsView` (both lists) | tile `people` |
| `RolesPage` (a pane of the two pane split) | tile `roles` |
| `PeopleListPane`, `PersonPane` (the person) | tile `people` |
| `PersonPane` (activity) | tile `activity` |
| `PersonTabs` (sessions) | tile `devices` |
| `RoleHistory` | tile `history` |
| `RolePeople`, `AddPeopleDialog` | tile `people` |
| `NotFound` | unchanged look, now drawn by the kit's `RoadScene` |

**Value sourcing**:

| Action | Value produced or displayed | Source |
|---|---|---|
| Crash panel and band | title, line, code, admin details, Copy details | spec 0025 (`CrashScreen`, `crashDetails`, `crashViewerIsAdmin`, the boundary's code), unchanged |
| Page and tile errors | title, message, retry label | each call site, as today (`getApiErrorMessage` and the defaults in the table above) |
| Page errors | "Nothing you saved is lost." | fixed in `ErrorState` and `ViewError` for `kind="page"` (AC-7) |
| Tile picture | which drawing | the call site's `subject`, per the tables above |
| Bay or drawer, reader or lanyard | which of two | `useScenePick(2)` (AC-16) |
| Module off title | the module's name | `MODULE_LABELS[module]`, as today |
| Band lockup | the brand block | each app's own (web-vrms sidebar brand, portal `BrandLockup`) |
| Still frame | whether motion runs | the `prefers-reduced-motion` media query or `data-motion="still"` in CSS; no JavaScript reads it |
| Drawing colours | every fill and stroke | `scenes.css` tokens, plus the theme tokens AC-1 names |

**Key invariants**:
- The two kits are byte identical; a kit file never imports app code (AC-1, AC-2).
- No scene shows live data or carries meaning the text doesn't (AC-18).
- Barriers keep a gap from trucks and never point at one; trucks sit on the asphalt with a shadow; no warning triangles; no "WeLinc yard" text (your board rules).
- The livery's orange and blue appear only on drawn vehicles.
- A random pick never changes while the screen is showing (AC-16).

**Security model**: no change. The admin crash details stay admin only (spec 0025 AC-7a). No access copy names no roles and no people. Scenes are decoration and read no data.

**Configuration required**: none.

**Critical test scenarios**:
- `check-scenes.mjs`: matching kits pass; a missing file, a changed byte or an import of `@/components/ui/button` from a kit file fails with its name; CRLF only passes, verifies **AC-1**, **AC-2**
- `ErrorState kind="page"` draws `data-scene="load"` with "Nothing you saved is lost."; `kind="tile" subject="devices"` draws `tile-devices` without it; a tile without `subject` fails typecheck, verifies **AC-7**, **AC-8**
- `CrashScreen` (staff with a code, staff without, admin): 0025's assertions hold on the rewritten tests, the alert holds only the title and line, and it draws `crash` in page and `pole` in full; the full version renders with no Router around it, verifies **AC-4**, **AC-5**, **AC-6**
- `useScenePick` with an injected random returns the same index across rerenders and a failed retry; a remount picks again; `PermissionsGate` going error, loading, error keeps the same scene, verifies **AC-16**
- `PermissionsGate` error shows Try again and Sign out over `reader` or `lanyard`; no keys shows `gate-wide`; `RequireAuth` unavailable shows no Sign out, verifies **AC-12**, **AC-13**, **AC-14**
- `RepairDetailPage` 404 shows the new copy over `not-found-bay` or `not-found-drawer`; 403 shows `gate`; the knowledge entry 404 shows `not-found-drawer` only, verifies **AC-9**, **AC-10**
- `ForbiddenPage` copy; `ModuleOffPage` draws `closed`; `NotFoundPage` draws `road` with "Wrong turn", verifies **AC-10**, **AC-11**, **AC-15**
- Every scene svg is `aria-hidden` and the alert holds only the title and line, verifies **AC-18**
- At `/check verify`: each scene loops, stops on its telling frame under reduced motion (and with the gallery's Still switch), the panel at 360px shows the whole picture, and the bands keep their subject in view, verifies **AC-3**, **AC-4**, **AC-17**, **AC-20**
- Portal: sign in, launcher, launches and 404 look and move as before the move; the portal's crash, launcher, Admin and `ViewError` sites draw their mapped scenes, verifies **AC-21**, **AC-22**

## Build plan

Facade, as the UI refresh phase sets it: the screens first, on the errors the app already raises. No backend slice exists. web-vrms is built whole before the portal copies the kit in, and the CI job lands last, so the daily check never fails while the portal catches up. One branch and pull request per repo (`feat/error-scenes`), into `development`; the workspace changes on their own branch into `main`.

1. **Tile board round** (workspace): draw the seven new tile subjects, two takes each, in the `R39SmallMatched` style; render and screenshot, fix, then show you; on your pick, copy the board into `docs/context/vrms/error-scene-boards/` with a README row, satisfies **AC-19**
2. **web-vrms kit foundation**: `src/styles/scenes.css` (the portal's `--scene-*` and `--livery-*` values, `scene-blink`, and the motion utilities the boards use, each with reduced motion and `data-motion` stops), imported from `index.css`; `ScenePanel`, `SceneBand`, `useScenePick`, `LiveryTruck.tsx` copied from the portal; the `/dev/ui` Scenes section with the Still switch, satisfies **AC-1**, **AC-3**, **AC-4**, **AC-16**, **AC-17**, **AC-18**, **AC-20**
3. **web-vrms panel scenes**: `CrashScene`, `LoadScene`, `NotFoundBayScene`, `NotFoundDrawerScene`, `ClosedScene`, `GateScene`, drawn from their boards; wire `CrashScreen` page, `ErrorState kind="page"` and its page call sites (dropping their card wrappers), the not found, 403, `ForbiddenPage` and `ModuleOffPage` screens, satisfies **AC-5**, **AC-7**, **AC-9**, **AC-10**, **AC-11**
4. **web-vrms band scenes**: `PoleScene`, `ReaderScene`, `LanyardScene`, `RoadScene` (from the portal), `GateScene wide`; wire `CrashScreen` full, `PermissionsGate` (both states, Sign out added to the error), `RequireAuth` unavailable, `NotFoundPage`, satisfies **AC-4**, **AC-6**, **AC-12**, **AC-13**, **AC-14**, **AC-15**
5. **web-vrms tiles**: `ErrorTile` with all 12 subjects, `ErrorState kind="tile"`, `DataTable`'s two props, and every tile call site, satisfies **AC-8**
6. **web-vrms tests and checks**: the scenarios above; `npm run lint`, `npm run typecheck`, `npm run build:local`; report the main bundle's gzip size change (over 25 KB comes back to you through this spec before the pull request); check that AC-23's untouched states still look as before, satisfies **AC-1** to **AC-20**, **AC-23**
7. **Portal move**: kit copied in from web-vrms (`LiveryTruck.tsx` moved into it, `RoadScene` from `NotFound.tsx`), its scene tokens and `scene-blink` moved into `scenes.css`, imports updated; check sign in, launcher, launches and 404 look the same, satisfies **AC-1**, **AC-21**
8. **Portal scenes**: `CrashScreen` panel and band, `LauncherError`, `AdminPage`, `ViewError`'s `kind` and `subject` with every call site; tests; lint and `build:local`, satisfies **AC-22**, **AC-23**
9. **Workspace check**: `scripts/check-scenes.mjs`, `scripts/test/check-scenes.test.mjs`, and the `scenes` job in `.github/workflows/ci.yml`; run it locally against both repos' `development` once both pull requests are merged, satisfies **AC-2**

## Consequences

**Positive**:
- Every error reads as WeLinc, with one picture per situation, which the defense panel will notice.
- One kit serves both apps, and drift is caught by a machine, not by memory.
- `ErrorState`'s required `kind` forces a decision at every call site, so a new screen can't fall back to the old icon by accident.

**Negative / tradeoffs**:
- Two copies to keep in step: each kit change is two pull requests, and the CI job only catches drift on its next run (at worst the next morning), not inside the app's own pull request. Rule: a kit change merges in both apps the same day, or the daily job stays red until it does. The job is not a required check (only `gitleaks` is on the workspace), so it never blocks a merge.
- The kit is a lot of SVG markup (about 20 drawings) in both main bundles, loaded by everyone for screens few people see. Lazy loading would break the offline case, so the size is accepted and measured in task 6.
- Hand drawn SVG is slow to change: a tweak means editing coordinates, and the generator scripts that made the boards are gone.
- If the web repos turn private after the defense, the `scenes` job needs a read token like `AUTH_REPO_READ_TOKEN`.
- The portal move touches the drawings spec 0019 just shipped, so task 7 needs a careful look that nothing moved.

**Neutral**:
- The no access copy on `ForbiddenPage` changes; QA's test cases for it need the new words.
- `ErrorState` and `ViewError` gain a required prop: every call site is edited once.

## Follow-up

- [ ] `/sync`: add `node scripts/check-scenes.mjs` to the Commands block in `agents/vrms/AGENTS.md`, and a line in both apps' `AGENTS.md` that the kit is shared and edited in both repos.
- [ ] Tell the PM: no Jira ticket exists for the error scenes; one for the build and one for QA's test cases (new copy on the no access page and the 404).
- [ ] The mechanic mobile app (feature 48) is out of scope; its error screens decide separately whether to reuse these drawings.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
