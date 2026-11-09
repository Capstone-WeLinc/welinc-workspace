# Verify: app initiated login and launcher · spec 0007 · 2026-11-09
_Steps derived from spec 0007 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones. Accounts are from `docs/integration/seed-accounts.md`: one system `vrms.admin@` (`admin1234`), two systems `multi.mixed@` (`chief1234`) or any mechanic, three systems `multi.lead@` (`chief1234`). Don't trigger setup or reset codes: local mail is real._

## welinc-auth

### Commands
- [ ] `catalog:sync --dry-run` after the migration → only `description` changes for BMS, VMMS and VRMS, no role changes → AC-5, AC-7
- [ ] Blank the `description` in `prisma/catalog/bms.ts`, run `catalog:sync` → it refuses and names the file; restore it → AC-5
- [ ] `GET /auth/systems` → each system has `description`, and the ETag differs from before → AC-5
- [ ] `POST /auth/login` as `multi.lead@` (with `Origin: http://localhost:8000`) → 200 with `systems` BMS, VMMS, VRMS in that order, each with `url`, `description` and named roles; no token in the body → AC-1, AC-3
- [ ] `POST /auth/login` with `"system": "VMMS"` in the body → 400 → AC-3
- [ ] `GET /auth/sso` with the cookie from above → the same body; with no cookie → 401 `SESSION_ENDED` → AC-1
- [ ] Switch off the `vmms` client row by hand, `GET /auth/sso` as `multi.lead@` → VMMS is missing and the log has one warning naming VMMS; switch it back on → AC-2
- [ ] 61 `GET /auth/sso` calls in a minute from one address → the 61st answers 429 `RATE_LIMITED` with `Retry-After` → AC-4
- [ ] Note `last_activity_at` of the session, call `GET /auth/sso` → unchanged → AC-1
- [ ] Switch off every client of a test user's only system, `POST /auth/login` → 403 `NO_SYSTEM_ACCESS`, no new `sessions` row, no `welinc_sso` cookie; switch it back on → AC-2, AC-3
- [ ] Sign in through VRMS as `multi.mixed@`, then `POST /vrms/session/refresh` → `user.systems` is `["VMMS","VRMS"]`; decode the access token → `roles` hold only VRMS roles and there is no `systems` claim → AC-6, AC-8
- [ ] `POST /auth/mobile/login` as a mechanic with `vmms-mobile` → `user.systems` present → AC-6
- [ ] Remove every role of a test user while they hold a live SSO session, `GET /auth/sso` → 403 `NO_SYSTEM_ACCESS` with `user: { email }` naming only that user; restore the roles → AC-19 (added by /develop, 2026-11-10)

## Portal and VRMS

### UI / manual
- [ ] Open `http://localhost:8000/` signed out → the login form looks as it did before (split layout, photo, gradient, glows), with a skeleton while loading and labelled inputs → AC-13, AC-22
- [ ] Sign in as `vrms.admin@` → straight into VRMS, no launcher; open `http://localhost:8000/` again → forwards to VRMS; Switch system is not in the sidebar, user menu or phone sheet → AC-9, AC-13, AC-14
- [ ] Sign out, sign in as `multi.lead@` → the launcher with a greeting by local time, cards BMS, VMMS, VRMS with icons, descriptions and role pills → AC-14, AC-15
- [ ] Click the VRMS card → VRMS opens with no password; Switch system shows in all three spots; click it → the launcher with "You're here" on VRMS → AC-9, AC-15, AC-16
- [ ] Open `http://localhost:8000/?from=https://evil.test` → no tag, every card links to a registry address → AC-16
- [ ] Click the VMMS card → the VMMS app's own address opens (its own login until S11) → AC-15
- [ ] Signed out, open `http://localhost:8001/repairs?status=open#top` as `multi.mixed@`, then as `multi.lead@`, then as `vrms.admin@` → each signs in on the portal and lands on that exact address, never the launcher → AC-10, AC-12
- [ ] With a live two system session, open `http://localhost:8000/?error=LOGIN_FAILED` → the launcher with the banner, no redirect; as `vrms.admin@` → its one card with the banner, no forward → AC-13
- [ ] Signed out, open `http://localhost:8000/?error=LOGIN_FAILED` as `vrms.admin@` and sign in → the launcher with its one card and the banner, no forward → AC-14
- [ ] Open `http://localhost:8000/?from=VRMS` with a broken `picture` value on the test user → initials show in the account menu → AC-17
- [ ] Open `http://localhost:8000/login?reason=logout` with a live session → the form with "You signed out.", and no `/auth/sso` call in the network panel → AC-11
- [ ] Launcher open, remove `multi.lead@`'s BMS role in VRMS or with the API in another window, come back to the tab → the BMS card is gone → AC-18
- [ ] Launcher open, sign out in VRMS in another tab, come back → the form with "Your session ended. Sign in again." → AC-18
- [ ] Remove every role from a test user while their launcher is open, return to the tab → the no access state with their email and Sign out → AC-18, AC-19
- [ ] Account menu → Sign out → the dialog "Sign out of every WeLinc system?"; confirm → the form with "You signed out."; an open VRMS tab lands on the portal within 30 seconds → AC-17
- [ ] `docker stop welinc_auth_service`, reload the launcher → the error state with Retry; start it, Retry → the cards → AC-20
- [ ] At 375px, 640px and 1280px → one, two, three columns, no horizontal scroll; Tab reaches every card and the account menu with a visible ring; with reduced motion on, the chevron doesn't move → AC-20
- [ ] `localStorage`, `sessionStorage` and every URL hold no token or code through all of the above → AC-13 (invariant)
- [ ] With that same user's live session, open `http://localhost:8000/` → the no access state shows the message, "Signed in as <their email>" and Sign out → AC-19 (added by /develop, 2026-11-10)

### Commands
- [ ] `npm run lint`, `npm run build`, `npm run test` in welinc-web-portal → pass, and a hex value added to a component fails lint → AC-21
- [ ] `grep -rn "VITE_VMMS_URL\|switchToVmms" welinc-web-vrms/src welinc-web-vrms/.env.example` → nothing → AC-9

## Docs
- [ ] Contract 0001 sections 5, 7, 10 and 12 and the gap map match the spec; the version line still says 2 with a 2026-11 amendment note → AC-23
- [ ] `docs/integration/web-login.md` exists, covers every step AC-24 lists, and `docs/integration/README.md` links to it → AC-24
