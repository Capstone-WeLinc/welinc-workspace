# 0027. Verify: Navigation redesign

Run at `/check verify navigation redesign`, locally, with the shared and VRMS stacks up and the seed accounts (`docs/integration/seed-accounts.md`). Major flows first.

## Board comparison (AC-15), no screenshots

1. Read [boards/Sidebars8.dc.html](boards/Sidebars8.dc.html) (and `BPhone.dc.html` for the phone) for the nav, and suite spec 0019's [Shell20](../../_root/0019-portal-redesign/boards/Shell20.dc.html) and [Switcher16](../../_root/0019-portal-redesign/boards/Switcher16.dc.html) for the top bar, sidebar title, footer strip, switcher popover and avatar: text, icons, font sizes and weights, colors, gaps, paddings, radii and states from the markup and its script.
2. Open web-vrms as `vrms.admin@` and as a mechanic, and the portal Suite management as `suite.admin@`, at 1280px; one `browser_snapshot` and one `browser_evaluate` with `getComputedStyle` for the sidebar title, New repair, section label, line, item, current item, sub item, count bubble (hot and not), footer strip, collapse button, top bar, breadcrumb, grid button, switcher popover and avatar. The VRMS top bar, title, footer, popover and avatar values must equal the portal's (AC-15).
3. Allowed differences: (a) Plex Mono instead of the boards' JetBrains Mono, and Inter instead of Inter Tight for headings (spec 0016, amended 2026-11-23); (b) spec 0016 token values that changed after the boards; (c) shadcn based parts with their spec 0016 styles; (d) real data lengths. Also expected: no Fleet section, no On hold sub page. Anything else is a bug.

## Major flows

- [ ] `vrms.admin@`: Dashboard; Work with Repair tickets (All open, Waiting for sign off) and Repair history; Insights; Admin; New repair at the top; no Profile item (AC-1, AC-2, AC-8)
- [ ] `vrms.chief@`: Waiting for sign off is gold, leaves out tickets assigned to them, and equals the list total after clicking it; Assigned to me shows (AC-2, AC-5, AC-6)
- [ ] A seed mechanic: My repairs with In progress, Sent back to me (gold when one is sent back) and Done; no New repair (AC-2, AC-6, AC-8)
- [ ] Send a ticket for verification as the mechanic: Sent back to me drops without a reload (AC-7)
- [ ] `/repairs?view=signoff` with a garage filter pages correctly; picking a status chip clears the view (AC-4)
- [ ] Collapse: dots on Repair tickets, New repair as an icon, tooltips (AC-6, AC-8)
- [ ] Top bar: "VRMS › Repair tickets › Waiting for sign off" on `/repairs?view=signoff`, the ticket number as the last crumb on a ticket, "New repair" on the form; no breadcrumb in `PageHeader`; at 375px only the last crumb (AC-9)
- [ ] `multi.chief@`: the grid opens with VRMS ticked first, then BMS and VMMS with role tags, Home in the title; VMMS opens straight through the launcher; a VRMS only mechanic has no grid button; `vrms.admin@` sees the Suite management card last and it opens `/admin` (AC-9a, AC-13)
- [ ] The sidebar: "VRMS" with the role name under it, linking to the dashboard; the footer strip with "WeLinc Logistics" and the collapse button; collapsed, the tile alone and the expand button alone; no switcher or account row in the sidebar (AC-10a, AC-10b)
- [ ] Avatar menu: name and email, Your profile, Sign out, nothing else (AC-10)
- [ ] 375px: mechanic tab bar with no Account tab and a dot on Repairs, the W tile and avatar in the top bar; admin sheet with the title, sub pages, counts and the footer strip (AC-11)
- [ ] Portal as `suite.admin@`: "Suite management" with the role line, the footer strip, the grid and avatar top right at 1280px (not in the sidebar), `KeyRound` and `History` icons, Roles naming, Deletion requests count in gold; as `vrms.admin@`: no Overview or Suite admins (AC-12)
- [ ] Keyboard pass and one axe pass on both sidebars (AC-14)
- [ ] Added at the build (2026-11-28): open `http://localhost:8000/?open=BMS` as `vrms.chief@` (no BMS role): the launcher shows with an error toast naming BMS, and the address loses `open` (AC-13)
- [ ] Added at the build: 375px as `vrms.chief@` on `/repairs`: the view chips (All open, Waiting for sign off, Assigned to me) show with the same counts as the sidebar, and tapping one sets the view (AC-11)
- [ ] Added at the build: as a mechanic, Done lists Closed tickets only, never Cancelled (AC-2)
- [ ] Added at the build: close Repair tickets, reload: it stays closed; open it again on another page and reload: it stays open (`welinc:nav-open:<user id>`, AC-3)
- [ ] Added at the build: `vrms.admin@` (outside the roster) has no Assigned to me, and `/repairs?view=mine` shows the plain list (AC-2, AC-4)

## API checks

- [ ] `GET /vrms/nav/counts` as the chief returns `open`, `signoff`, `mine`; as a mechanic `active`, `sentBack`; each equals the matching `GET /vrms/repairs?view=…` total (AC-5)
- [ ] `GET /vrms/repairs?view=mine` outside the roster answers 403; `view=bogus` answers 400 (AC-4)
- [ ] `GET /auth/admin/me` carries `pendingDeletionRequests`, scoped to the caller's systems (AC-12)
- [ ] After the migration, each In progress ticket with a send back in force has `sent_back_at`; a send for verification clears it (AC-2)
