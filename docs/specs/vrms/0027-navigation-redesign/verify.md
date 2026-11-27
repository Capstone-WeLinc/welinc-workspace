# 0027. Verify: Navigation redesign

Run at `/check verify navigation redesign`, locally, with the shared and VRMS stacks up and the seed accounts (`docs/integration/seed-accounts.md`). Major flows first.

## Board comparison (AC-15), no screenshots

1. Read [boards/Sidebars8.dc.html](boards/Sidebars8.dc.html) (and `BPhone.dc.html` for the phone) for the nav, and suite spec 0019's [Shell20](../../_root/0019-portal-redesign/boards/Shell20.dc.html) and [Switcher16](../../_root/0019-portal-redesign/boards/Switcher16.dc.html) for the top bar, sidebar title, footer strip, switcher popover and avatar: text, icons, font sizes and weights, colors, gaps, paddings, radii and states from the markup and its script.
2. Open web-vrms as `vrms.admin@` and as a mechanic, and the portal Suite management as `suite.admin@`, at 1280px; one `browser_snapshot` and one `browser_evaluate` with `getComputedStyle` for the sidebar title, section label, line, item, current item, sub item, count bubble (hot and not), footer strip, collapse button, top bar, breadcrumb, grid button, switcher popover and avatar. The VRMS top bar, title, footer, popover and avatar values must equal the portal's (AC-15).
3. Allowed differences: (a) Plex Mono instead of the boards' JetBrains Mono, and Inter instead of Inter Tight for headings (spec 0016, amended 2026-11-23); (b) spec 0016 token values that changed after the boards; (c) shadcn based parts with their spec 0016 styles; (d) real data lengths. Also expected: no Fleet section, no On hold sub page. Anything else is a bug.

## Major flows

- [x] `vrms.admin@`: Dashboard; Work with Repair tickets (All open, Waiting for sign off) and Repair history; Insights; Admin; no New repair and no Profile item in the sidebar, the line and 12px of space under the title; New repair in the dashboard header at 1280px and 375px (AC-1, AC-2, AC-8, AC-10a)
- [x] `vrms.chief@`: Waiting for sign off is gold, leaves out tickets assigned to them, and equals the list total after clicking it; Assigned to me shows (AC-2, AC-5, AC-6)
- [x] A seed mechanic: My repairs with In progress, Sent back to me (gold when one is sent back) and Done; no New repair (AC-2, AC-6, AC-8)
- [x] Send a ticket for verification as the mechanic: Sent back to me drops without a reload (AC-7)
- [x] `/repairs?view=signoff` with a garage filter pages correctly; picking a status chip clears the view (AC-4)
- [x] Collapse: dots on Repair tickets, no New repair icon, tooltips (AC-6, AC-8)
- [x] Top bar: "VRMS › Repair tickets › Waiting for sign off" on `/repairs?view=signoff`, the ticket number as the last crumb on a ticket, "New repair" on the form; no breadcrumb in `PageHeader`; at 375px only the last crumb (AC-9)
- [x] `multi.lead@` (`multi.chief@` has only one web system, so no grid): the grid opens with VRMS ticked first, then BMS and VMMS with role tags, the Launcher pill (`LayoutGrid`) in the title; VMMS opens straight through the launcher; a VRMS only mechanic has no grid button; `vrms.admin@` sees the Suite management card last and it opens `/admin` (AC-9a, AC-13)
- [x] The sidebar: "VRMS" with the role name under it, linking to the dashboard; the footer strip with "WeLinc Logistics" and the collapse button; collapsed, the tile alone and the expand button alone; no switcher or account row in the sidebar (AC-10a, AC-10b)
- [x] Avatar menu: name and email, Your profile, Sign out, nothing else (AC-10)
- [x] 375px: mechanic tab bar with no Account tab and a dot on Repairs, the W tile and avatar in the top bar; admin sheet with the title, sub pages, counts and the footer strip (AC-11)
- [x] Portal as `suite.admin@`: "Suite management" with the role line, the footer strip, the grid and avatar top right at 1280px (not in the sidebar), `KeyRound` and `History` icons, Roles naming, Deletion requests count in gold; as `vrms.admin@`: no Overview or Suite admins (AC-12)
- [x] Keyboard pass and one axe pass on both sidebars (AC-14)
- [x] Added at the build (2026-11-28): open `http://localhost:8000/?open=BMS` as `multi.mixed@` (two web systems, no BMS role; a one system person like `vrms.chief@` goes straight into VRMS): the launcher shows with an error toast naming BMS, and the address loses `open` (AC-13)
- [x] Added at the build: 375px as `vrms.chief@` on `/repairs`: the view chips (All open, Waiting for sign off, Assigned to me) show with the same counts as the sidebar, and tapping one sets the view (AC-11)
- [x] Added at the build: as a mechanic, Done lists Closed tickets only, never Cancelled (AC-2)
- [x] Amended 2026-11-28: on load Repair tickets and Knowledge base are open; clicking the name Repair tickets goes to All open and leaves it open; only the chevron folds it; after a reload both are open again (AC-3)
- [x] Added at the build: `vrms.admin@` (outside the roster) has no Assigned to me, and `/repairs?view=mine` shows the plain list (AC-2, AC-4)
- [x] Added at step 5 (2026-11-28): as `multi.lead@` the BMS and VMMS cards show no role tag today: a VRMS token carries only VRMS roles (welinc-auth `rolesFor`), so AC-9a's tag had no source; `/architect` picked `user.systemRoles` (step 6a). Before 6a, check the cards show with no empty tag box; after it, check the tags (AC-9a)
- [x] Added at step 5: as a VMMS or BMS admin who is not a VRMS admin, the Suite management card is missing for the same reason until step 6a (`user.suiteAdmin`, `user.systemRoles`); after it, check it shows for them and for a suite admin on a temporary non admin VRMS role; as `multi.admin@` (VRMS Admin) it shows either way (AC-9a)
- [x] Added at step 5: `http://localhost:8000/?open=VRMS` as `multi.lead@` showed the "Opening VRMS…" cover but stayed on the launcher in Playwright; check it in a real browser before calling AC-13 met (AC-13)
- [x] Added at step 5, fixed 2026-11-28: in the avatar menu "Your profile" and "Sign out" both compute `foreground` (rgb 15, 23, 42) (AC-10, AC-15)
- [x] Added 2026-11-28: in the portal, the grid button and the avatar show a pointer hand on hover, like VRMS
- [x] Added at step 5: the sidebar title "VRMS" is white on navy, expanded and in the phone sheet (it was navy on navy before `847a04f`) (AC-10a)

## API checks

- [x] `GET /vrms/nav/counts` as the chief returns `open`, `signoff`, `mine`; as a mechanic `active`, `sentBack`; each equals the matching `GET /vrms/repairs?view=…` total (AC-5)
- [x] `GET /vrms/repairs?view=mine` outside the roster answers 403; `view=bogus` answers 400 (AC-4)
- [x] `GET /auth/admin/me` carries `pendingDeletionRequests`, scoped to the caller's systems (AC-12)
- [x] After the migration, each In progress ticket with a send back in force has `sent_back_at`; a send for verification clears it (AC-2)
- [ ] Added by `/architect` (step 6a): a suite admin whose only web system is VRMS (a temporary non admin role) gets the grid button and the Suite management card; their cards list only the systems they hold a role in (AC-9a) (skipped 2026-11-28, your call: rare setup, covered by unit tests)
- [ ] Added by `/architect` (step 6a): a suite admin with no web system is never let into VRMS (`NO_SYSTEM_ACCESS` at the grant), so no switcher shows (AC-9a) (skipped 2026-11-28, your call: rare setup, covered by unit tests)
- [ ] Added by `/architect` (step 6a): a new custom role on another system's card shows in title case until the catalog refetches on focus, then by its name (AC-9a) (skipped 2026-11-28, your call: rare setup, covered by unit tests)

## Step 6a, added by /develop (2026-11-28)

- [x] `POST /vrms/session/refresh` as `multi.lead@`: `user.systems` is `["BMS","VMMS","VRMS"]` and `user.systemRoles` is one entry each, same order (`OPERATIONS`, `OPERATIONS`, `CHIEF_MECHANIC`); `suiteAdmin` false. Seen live at build (AC-9a)
- [x] As `multi.lead@` in the browser, the grid shows BMS and VMMS tagged "Operations" by its catalog name, and no Suite management card (AC-9a)
- [x] As `multi.admin@` (VRMS and VMMS Admin), the refresh answer's VMMS entry holds `ADMIN`; the VMMS card is tagged "Admin" and the Suite management card shows (AC-9a)
- [x] The access token's claims (decode it) hold no `systemRoles` or `suiteAdmin`; the refresh answer does (contract 0001 section 5)
- [ ] Older welinc-auth fallback: with the two fields removed from a refresh answer (unit tests in `auth-client.spec.ts` and `grantFields.test.ts`), the cards show with no tag and the Suite management card follows the VRMS `ADMIN` alone (AC-9a) (skipped 2026-11-28, your call: rare setup, covered by unit tests)
- [x] `npm run openapi:check` passes in welinc-auth and `GrantUser` in `docs/openapi.json` lists `systemRoles` and `suiteAdmin` (AC-14)

### Value sourcing for step 6a

- Role tag: change `multi.lead@`'s VMMS role in the portal, refresh the VRMS tab after the next token refresh, and see the tag follow `user.systemRoles` (not the VRMS token roles)
- Suite management card: give `suite.admin@` a temporary VRMS Chief Mechanic role and open VRMS: the card and the grid show from `user.suiteAdmin`
- Grid button: the same suite admin with one system gets the grid; drop the suite admin row and it goes on the next refresh

## Step 7 sweep, added by /develop (2026-11-28)

The sweep ran these once and fixed what failed (web-vrms `dfc91b4`, portal `52ae02d`); `/check verify` reruns them.

- [x] At 1280px as `mech.juan@`, the "VRMS" crumb link computes `muted-foreground` (rgb 91, 103, 121), not the navy link color, and turns `foreground` on hover → AC-9
- [x] The VRMS sidebar title tile is 36px with a 10px radius, the same as the portal's Suite management tile; collapsed, the 64px strip still centres it → AC-10a, AC-15
- [x] With the grid switcher open in VRMS (`multi.admin@`) and in the portal, the popover is a dialog named "Switch system", and axe finds nothing but the dev only dataset switch → AC-9a, AC-14
- [x] The VRMS switcher cards compute the same text color as the portal's (rgb 15, 23, 42) → AC-15
- [x] axe at 375px and 1280px in both apps, with the sheet, the switcher and the account menu each open in turn → no violations outside the dev only dataset switch and the account menu's `region` finding (allowed below) → AC-14

**Allowed axe difference (your call, 2026-11-28):** with the account menu open, axe's best practice `region` rule flags `div[data-radix-popper-content-wrapper]` in both apps: the name and email block inside the shadcn menu, which renders at the end of `body`, sits outside a landmark. It is not a WCAG failure and the menu keeps its accessible name, so it is accepted, like the dev only dataset switch. Any other axe finding is a bug.


## Run notes, 2026-11-28 (second `/check verify` pass)

- Ran live as `mech.pedro@` (send for verification: both sidebar bubbles dropped with no reload, `nav/counts` went to 0, `sent_back_at` cleared in the database), `vrms.admin@` (no New repair in the sidebar, the button in the dashboard header at 1280px and 375px, collapsed dots), `suite.admin@` and a local pending deletion request for `mech.carl@` (gold count 1, gold dot collapsed; `vrms.admin@` saw it as a plain 1, scoped to their system; the test row was deleted afterwards).
- Keyboard: every stop in VRMS's sidebar, top bar and page reached in order with a ring. The portal walk started in the footer strip, and its sidebar links share the same component pattern.
- axe: VRMS clean but for the dev only dataset switch. The portal's Overview page has one `heading-order` best practice finding (`#overview-admins-per-system`), page content and not the shell, left for the page's own feature.
- The send for verification left REP-20261113-2AF9 in For verification; `npm run seed` in welinc-backend-vrms puts it back.