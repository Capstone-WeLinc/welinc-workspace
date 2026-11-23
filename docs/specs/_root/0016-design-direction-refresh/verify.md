# Verify: design direction refresh · spec 0016 · updated 2026-11-23
_Steps derived from spec 0016 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones. So far this covers build step 4a in all three repos and the fonts (step 2a); the page sweep adds its steps when it is built._

## Fonts (AC-3, build step 2a)
- [ ] `grep -rn "ibm-plex-sans\|IBM Plex Sans" welinc-web-portal/src welinc-web-portal/package.json welinc-web-vrms/src welinc-web-vrms/package.json` → nothing; both `package.json` list `@fontsource-variable/inter` and `@fontsource/ibm-plex-mono` → AC-3
- [ ] On the VRMS dashboard and the portal's People page, one `browser_evaluate` after `await document.fonts.ready`: `getComputedStyle(document.body).fontFamily` starts with `"Inter Variable"`, a StatCard number's starts with `"IBM Plex Mono"`, and `[...document.fonts]` holds a face with family `Inter Variable` and one with `IBM Plex Mono`, both with status `loaded` → AC-3 (value source: `--font-sans` and `--font-mono` in `src/index.css`)
- [ ] On a page that shows a peso amount in text (a web-vrms ticket's costs), the same check finds the Inter face whose unicode range covers `U+20B1` with status `loaded` → AC-3 (`₱` renders in Inter)
- [ ] Network tab on a fresh load → only `inter-latin` (plus `inter-latin-ext` when a page shows `₱`) and `ibm-plex-mono` woff2 files; nothing from `fonts.googleapis.com` or `fonts.gstatic.com` → AC-3

## Commands
- [ ] In `welinc-auth`: `npm run lint`, `npx jest`, `npm run build`, `npm run openapi:check` → all pass; `node scripts/check-contract-routes.mjs welinc-auth/docs/openapi.json` from the workspace root → ok → AC-12a
- [ ] In `welinc-web-vrms`: `npm run lint` (0 errors), `npm run typecheck`, `npx vitest run`, `npm run build:local` → all pass → AC-12, AC-21
- [ ] `grep -rn "IdleWarningDialog\|keepWorking\|dismissed" welinc-web-vrms/src/lib/session welinc-web-vrms/src/components` → nothing → AC-12 (the dialog and its focus rules are removed)

## API (welinc-auth through the gateway, `Origin: http://localhost:8000`, `Content-Type: application/json`)
- [ ] `POST /auth/login` with a verified non admin seed account → 200 with `sessionExpiresAt`, `sessionAbsoluteExpiresAt` and `serverTime`, all ISO; `sessionExpiresAt` about 30 minutes ahead, `sessionAbsoluteExpiresAt` about 12 hours ahead, `serverTime` about now → AC-12a
- [ ] With that cookie, `GET /auth/sso` → the same three fields; `sessionExpiresAt` equals `expiresAt` from `GET /auth/session` for the same session → AC-12a (value source: computed as `/auth/session` does)
- [ ] An unverified account through `POST /auth/login` (code step) then `POST /auth/login/verify-email` with the code from the auth log → 200 with the three fields → AC-12a
- [ ] A suite admin through the code step → 200 with `systems: []` and the three fields → AC-12a
- [ ] An account with no usable system → 403 `NO_SYSTEM_ACCESS`, no `Set-Cookie` → AC-12a (no session on a refused login still holds)
- [ ] `/auth/docs` shows the launcher answer schema with the three fields on `/auth/sso`, `/auth/login` (one of the answer or the code step) and `/auth/login/verify-email` → AC-12a

## UI / manual (web-vrms; to wait less, sign in and leave the tab idle about 28 minutes, or shorten the idle setting locally)
- [ ] 120 s before the idle cutoff → one `GET /vrms/session/status`; a floating "Signing out soon" banner with a countdown and **Stay signed in**; focus doesn't move → AC-12
- [ ] Work in another VRMS tab or in the portal during the last 2 minutes, then wait → the status check finds the later cutoff and the banner closes quietly, without signing out → AC-12 (value source: `GET /vrms/session/status`)
- [ ] While the banner shows, press a key → one `POST /vrms/session/activity`, then one `GET /vrms/session/status`, then the banner closes because the cutoff moved; a mouse move alone sends nothing → AC-12
- [ ] **Stay signed in** → an activity ping, then a status check; the banner closes; a second VRMS tab with the banner closes too → AC-12
- [ ] Leave it untouched → at the cutoff one last status check, then the tab goes to `<portal>/login?reason=idle` → AC-12
- [ ] Turn the network off (DevTools offline) during the banner → the offline banner shows on top; the tab still leaves at the cutoff → AC-12
- [ ] Near the 12 hour end (or a session whose cutoff Stay signed in can't move) → the title is "Signing out at HH:MM", the line says it can't be extended, no action; at the cutoff the tab goes to `?reason=maxage` → AC-12 (value source: `sessionAbsoluteExpiresAt` from the refresh answer, the 12 hour end when the two are within 1 s)
- [ ] With a screen reader (VoiceOver): the banner is announced as "Signing out in 2 minutes" once, again at "30 seconds", the ticking time is never read, and the switch to the 12 hour text is not announced; Tab reaches **Stay signed in** first → AC-12 (screen readers)

## Commands (portal)
- [ ] In `welinc-web-portal`: `npm run lint` (0 errors), `npx vitest run` (`src/lib/sessionWatch/` and `BannerHost.test.tsx` included), `npm run build:local` → all pass → AC-12b, AC-21

## UI / manual (portal, signed in on the launcher or in Admin; the DevTools Network tab open)
- [ ] Press a key or click → one `POST /auth/session/activity` with a JSON body, 204; more input in the same minute sends at most one more at the minute; mouse moves send nothing → AC-12a
- [ ] On `/login` (and its `reason=` screens) nothing is pinged or checked and no banner shows → AC-12b
- [ ] Work only in Admin for over 30 minutes (click around) → you stay signed in → AC-12a (the reason for the pinger)
- [ ] Leave the launcher idle → 120 s before the cutoff one `GET /auth/sso`, then the "Signing out soon" banner with a countdown and **Stay signed in**; focus doesn't move → AC-12b
- [ ] With the banner showing, work in VRMS (another tab) → at the portal's next check (or the last one at the cutoff) the banner closes quietly → AC-12b (value source: the fresh `/auth/sso` answer)
- [ ] **Stay signed in** → a ping, then one `GET /auth/sso`; the banner closes in this tab and in a second portal tab → AC-12b (several tabs)
- [ ] Leave it untouched → at the cutoff one last `GET /auth/sso` (401), then `/login?reason=idle`; a second portal tab on the launcher or Admin goes to the same page → AC-12b
- [ ] Change the computer's clock 10 minutes ahead (or behind) and reload → the check still runs 120 s before welinc-auth's cutoff, not the browser's → AC-12b (value source: the clock gap from `serverTime`)
- [ ] Reload a deep Admin link (`/admin/people`) → one `GET /auth/admin/me` and then one `GET /auth/sso`; going from the launcher to Admin sends no extra `/auth/sso` → AC-12b (the amended cold mount rule)
- [ ] Block `/auth/sso` in DevTools (request blocking) just before the check → the banner still shows on the held cutoff, retries at 5, 15 and 30 s, and at the cutoff the tab leaves → AC-12b (failures)
- [ ] Near the 12 hour end → "Signing out at HH:MM", it can't be extended, no action; at the cutoff `?reason=maxage` → AC-12b
- [ ] A screen reader hears "Signing out in 2 minutes" once and "30 seconds" later, never the ticking time; Tab reaches **Stay signed in** first → AC-12b (screen readers)

## Acceptance-criteria coverage
- AC-12 (web-vrms): the UI / manual steps and the two web-vrms commands
- AC-12a: the API steps and the welinc-auth commands
- AC-12b: the portal command and UI steps
- AC-21: the web-vrms and portal command steps (partial, the rest at the page sweep)

## Page sweep (AC-18 to AC-21, build step 8 and 9; added 2026-11-23)
- [ ] `grep -rnE "IBM Plex Sans|ease-snappy|ease-drawer|(^|[^-\w])shadow-(xs|sm|md|lg)([^-\w]|$)|(^|[^-\w])text-(xs|sm|base|lg|xl|2xl)([^-\w]|$)" welinc-web-portal/src welinc-web-vrms/src --include='*.ts*' | grep -v pages/auth/` → nothing; the only banned shadows left are the gold glows in the portal's `src/pages/auth/` (brand surface) → AC-18, AC-20
- [ ] No KPI card has a tinted icon square: `KpiCard` (web-vrms `components/shared`) and the Analytics `KpiCard` show a label, a mono number and one line → AC-18
- [ ] In both apps `npm run lint` exits 0 with the old sizes and shadows as errors (put `text-sm` in any page: lint fails) → AC-17, AC-21
- [ ] One Playwright `run_code`: every web-vrms page (dashboard, repairs, repairs/new, history, profile, users, audit-logs, analytics with each tab, knowledge-base and its new, suggestions and categories pages, settings and its sub pages) and the portal's launcher and Admin views at 375px and at 1280px → `document.documentElement.scrollWidth <= innerWidth` on each → AC-18
- [ ] axe through Playwright on the portal's People and Roles, and web-vrms dashboard, repair list and ticket detail → no `color-contrast` violations; Tab through the same pages → a visible focus ring on every control → AC-19
- [ ] The launcher band and the sign in hero look as before apart from the font: gold eyebrow in `text-label`, the greeting `text-display` from `sm`, the glows on the logo and the gold submit → AC-20
- [ ] Portal Sign out (account menu) as `vrms.admin@welinc.com` → "Sign out of WeLinc?" and "You'll be signed out of VRMS on this browser…"; from Admin or the no access page → "You'll need to sign in again." → scope note (S18 page sweep) (value source: `signedInSystems` of the launcher answer)
- [ ] Analytics: the period and sort switches are the white pill segmented control, the tabs are real tabs (arrow keys move between them), no gold text on white → AC-8, AC-18
