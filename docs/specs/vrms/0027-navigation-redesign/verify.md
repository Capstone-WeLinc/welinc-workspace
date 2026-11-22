# 0027. Verify: Navigation redesign

Run at `/check verify navigation redesign`, locally, with the shared and VRMS stacks up and the seed accounts (`docs/integration/seed-accounts.md`). Major flows first.

## Board comparison (AC-15), no screenshots

1. Read [boards/Sidebars8.dc.html](boards/Sidebars8.dc.html) (and `BPhone.dc.html` for the phone): text, icons, font sizes and weights, colors, gaps, paddings, radii and states from the markup and its script.
2. Open web-vrms as `vrms.admin@` and as a mechanic, and the portal Admin as `suite.admin@`, at 1280px; one `browser_snapshot` and one `browser_evaluate` with `getComputedStyle` for the switcher, New repair, section label, line, item, current item, sub item, count bubble (hot and not), account menu and collapse toggle.
3. Allowed differences: (a) IBM Plex instead of the boards' fonts; (b) spec 0016 token values that changed after the boards; (c) shadcn based parts with their spec 0016 styles; (d) real data lengths. Also expected: no Fleet section, no On hold sub page. Anything else is a bug.

## Major flows

- [ ] `vrms.admin@`: Dashboard; Work with Repair tickets (All open, Waiting for sign off) and Repair history; Insights; Admin; New repair at the top; no Profile item (AC-1, AC-2, AC-8)
- [ ] `vrms.chief@`: Waiting for sign off is gold, leaves out tickets assigned to them, and equals the list total after clicking it; Assigned to me shows (AC-2, AC-5, AC-6)
- [ ] A seed mechanic: My repairs with In progress, Sent back to me (gold when one is sent back) and Done; no New repair (AC-2, AC-6, AC-8)
- [ ] Send a ticket for verification as the mechanic: Sent back to me drops without a reload (AC-7)
- [ ] `/repairs?view=signoff` with a garage filter pages correctly; picking a status chip clears the view (AC-4)
- [ ] Collapse: dots on Repair tickets, New repair as an icon, tooltips (AC-6, AC-8)
- [ ] `multi.chief@`: the switcher menu opens VMMS straight through the launcher; a VRMS only mechanic sees a plain label (AC-9, AC-13)
- [ ] Account menu: name, role name, Profile, Sign out (AC-10)
- [ ] 375px: mechanic tab bar with a dot on Repairs; admin sheet with sub pages and counts (AC-11)
- [ ] Portal as `suite.admin@`: the new frame, Roles naming, Deletion requests count in gold; as `vrms.admin@`: no Overview or Suite admins (AC-12)
- [ ] Keyboard pass and one axe pass on both sidebars (AC-14)

## API checks

- [ ] `GET /vrms/nav/counts` as the chief returns `open`, `signoff`, `mine`; as a mechanic `active`, `sentBack`; each equals the matching `GET /vrms/repairs?view=…` total (AC-5)
- [ ] `GET /vrms/repairs?view=mine` outside the roster answers 403; `view=bogus` answers 400 (AC-4)
- [ ] `GET /auth/admin/me` carries `pendingDeletionRequests`, scoped to the caller's systems (AC-12)
- [ ] After the migration, each In progress ticket with a send back in force has `sent_back_at`; a send for verification clears it (AC-2)
