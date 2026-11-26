# Verify: error scenes · spec 0028 · updated 2026-11-26
_Steps derived from spec 0028's acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Local stack: sign in on the portal (`http://localhost:8000`) as `vrms.admin@welinc.com` (the code is in `docker logs welinc_auth_service`). Reduced motion: the browser's `prefers-reduced-motion: reduce`, or the Still switch in `/dev/ui`.

## UI / manual

### The gallery
- [ ] Open `http://localhost:8001/dev/ui`, scroll to Error scenes → six panels, five bands (pole, reader, lanyard, wide gate, road) and 12 tiles; the bay and drawer sit side by side, as do the reader and lanyard → AC-20
- [ ] Watch each scene for a few seconds → every motion loops; nothing plays once and stops → AC-17
- [ ] Turn on Still → everything stops on its telling frame: hazards and beacon lit, the flickering lamp on, the camera aimed down at the gate, the drawer out, the pass on the reader, the bay dimmed but visible; no puffs, steam, sparks or contact arcs → AC-17
- [ ] Same with the system's reduced motion setting on and Still off → the same frames → AC-17
- [ ] Inspect any scene → `<svg aria-hidden="true" focusable="false" data-scene="…">`; no scene shows a real name, plate, ticket number or role → AC-18
- [ ] Run `npm run build:local` in web-vrms and search `dist/` for `Error scenes` → not there; with `VITE_DEV_UI=true` it is in its own `DevUiPage` chunk → AC-20
- [ ] On staging, open `/dev/ui` signed out (sent to sign in), then signed in (the kit with the Error scenes section) → AC-20

### Panels inside the shell (web-vrms)
- [ ] Open `/repairs/<a real uuid that doesn't exist>` (for example `00000000-0000-4000-8000-000000000000`) → sidebar and top bar stay; a white 720px card with "Repair ticket not found", the board's line, Back to repairs; the bay or the drawer → AC-3, AC-9
- [ ] Reload that page several times → both the bay and the drawer turn up over a few visits → AC-16
- [ ] As a mechanic, open a ticket assigned to someone else → the gate panel, "This ticket isn't assigned to you", no line, Back to repairs → AC-10
- [ ] Open a Settings section without its key (for example `/settings/modules` as a chief mechanic) → the gate panel, "This page needs a different role" / "Ask an admin to give you access if you need it for your work." / Back to dashboard → AC-10
- [ ] Turn Analytics off in Settings, Modules, then open `/analytics` → the shutter with Closed for now, "Analytics is turned off", copy unchanged → AC-11
- [ ] Stop the backend (`docker stop welinc_vrms_backend`), open `/repairs` → the idling truck panel, the page's own title, "Nothing you saved is lost.", Try again; no card around the panel → AC-3, AC-7
- [ ] With the backend still down, open a ticket you have a draft on → the load panel without "Nothing you saved is lost." (same in the knowledge base editor) → AC-7
- [ ] With the backend down, open My profile → the page panel for the profile; with only the activity or devices call failing, each card shows its tile (activity, devices), no navy scene, no reassurance → AC-8
- [ ] With the backend down: Users, Settings Vehicles and a Lookup list → the page panel with no table card around it; Settings Lookup lists' knowledge categories → the `list` tile inside its card → AC-3, AC-8
- [ ] With the backend down: the dashboard Team panel (people tile), an Analytics section (charts tile), a vehicle's history dialog (trucks tile), a knowledge entry's change history (history tile) → AC-8
- [ ] Start the backend again (`docker start welinc_vrms_backend`)
- [ ] Open `/knowledge-base/<missing id>` and `/knowledge-base/<missing id>/edit` → the drawer panel only, copy and button unchanged → AC-9
- [ ] At 360px wide, open any panel → the whole scene shows, scaled down, nothing cropped → AC-3

### Bands outside the shell (web-vrms)
- [ ] Open `http://localhost:8001/no-such-page` → the road band, "Error 404" / "Wrong turn" / the portal's line / Back to dashboard; the lockup links to the dashboard → AC-4, AC-15
- [ ] Sign in as an account with no VRMS role (or remove the VRMS role from a test account) → the wide gate band, "No VRMS access", Sign out → AC-12
- [ ] Block `/vrms/permissions/me` (devtools request blocking) and reload → the reader or lanyard band, "Could not load your permissions", Try again and an outlined Sign out → AC-13
- [ ] Press Try again while still blocked → the same picture comes back, never the other one → AC-16
- [ ] Stop `welinc_auth_service` and reload → the same band pair, "Can't reach the sign in service", Try again, no Sign out → AC-14
- [ ] At 360px and at 1440px, check each band → the truck, pole, gate, reader or rack stays in view; lane lines run the whole width, except on the road band, where the line stops short of the barrier and the barrier may crop at 360px (the portal road scene is reused as it stands) → AC-4
- [ ] On staging with `VITE_SENTRY_TEST_ROUTES=true`, trigger a crash on `/debug/sentry` → the hazard glow panel inside the shell; staff see the line and Reference code under it; an admin sees the details box and Copy details inside the panel → AC-5
- [ ] Trigger a crash of the shell itself → the blackout pole band with spec 0025's copy word for word, Back to dashboard as a plain link → AC-6
- [ ] With a screen reader on either crash → only the title and line are announced, not the code, details or buttons → AC-5, AC-18

### Portal
- [ ] Sign in page, launcher, each launch (2, 3, 4) and `http://localhost:8000/nope` → look and move exactly as before the move → AC-21
- [ ] Block `/auth/sso` and open the launcher → the band stays calm; the idling truck panel replaces only the tiles, "We couldn't load your systems.", the reassurance, Retry → AC-22
- [ ] Block the Admin first load (`/auth/admin/me`) → "We couldn't load Admin." in the load panel → AC-22
- [ ] With Admin open, block each view's call: Overview, Activity, Suite admins, Temporary access → the page panel, default title "We couldn't load this", the view's own message, Retry with its icon → AC-22
- [ ] Block the people, roles and sessions calls → People list and person (people tile), person activity (activity tile), sessions tab (devices tile), role history (history tile), role people and Add people dialog (people tile), the roles pane (roles tile), deletion requests (people tile) → AC-22
- [ ] Crash a portal view (or force one in dev) → the hazard glow panel, Back to apps → AC-22

### Unchanged
- [ ] The offline banner, toasts, field errors, form alerts, skeletons, "No activity yet" and other empty states, the no access banner after a redirect, "Couldn't load older events" in the audit timeline, `DeleteAccountCard`'s line and the portal's "We couldn't load more …" rows look as before → AC-23

## Commands
- [ ] `node scripts/check-scenes.mjs` (workspace root) → "Scene kit matches: 18 files" and exit 0 → AC-1, AC-2
- [ ] Change one byte of `welinc-web-portal/src/styles/scenes.css`, run it again → exit 1 naming the file and line; undo the change → AC-2
- [ ] `node --test scripts/test/check-scenes.test.mjs` → 16 pass → AC-2
- [ ] Once both web pull requests are merged into `development`: run the CI workflow by hand (Actions, CI, Run workflow) → the `scenes` job passes → AC-2
- [ ] In web-vrms: `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build:local` → all green → AC-1 to AC-20
- [ ] In the portal: `npm run lint`, `npm run test`, `npm run build:local` → all green → AC-21, AC-22

## Value sourcing
- [ ] Crash copy, code and details → spec 0025's words unchanged in both apps, staff with and without a code, admin → row "Crash panel and band"
- [ ] Page and tile errors keep each call site's title, message and retry label (for example Analytics says "This section didn't load" and "Retry") → row "Page and tile errors"
- [ ] "Nothing you saved is lost." only on page kind, never on tiles, never on the ticket or the editor → row "Page errors"
- [ ] Each tile matches its call site's subject per the spec's tables → row "Tile picture"
- [ ] Bay or drawer, reader or lanyard: picked per visit, kept across a failed retry → row "Bay or drawer, reader or lanyard"
- [ ] Module off title follows the module's label (Analytics, Knowledge base) → row "Module off title"
- [ ] Band lockup: web-vrms's sidebar brand, the portal's `BrandLockup`, never a router link on a crash → row "Band lockup"
- [ ] Still frame comes from CSS only (reduced motion or `data-motion="still"`), no script → row "Still frame"
- [ ] No hex in any scene component (lint), every colour a `scenes.css` token or a shared theme token → row "Drawing colours"

## Acceptance-criteria coverage
- AC-1, AC-2: commands, `check-scenes` · AC-3: missing ticket, backend down, 360px · AC-4: 404, band widths · AC-5: crash in a page · AC-6: shell crash · AC-7: backend down, drafts · AC-8: tiles · AC-9: ticket and knowledge 404 · AC-10: ticket 403, ForbiddenPage · AC-11: module off · AC-12: no VRMS role · AC-13: permissions blocked · AC-14: auth stopped · AC-15: 404 · AC-16: repeated visits, failed retry · AC-17: gallery motion and Still · AC-18: svg attributes, screen reader · AC-19: done in the build (board `R44Tiles.html` picked) · AC-20: gallery, dist search · AC-21: portal look unchanged · AC-22: portal sites · AC-23: unchanged states
