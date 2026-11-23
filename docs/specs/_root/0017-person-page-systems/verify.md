# 0017. Verify: People list and person page

Run at `/check verify person page systems`, locally, with the shared and VRMS stacks up and the seed accounts (`docs/integration/seed-accounts.md`). Never use a real email address. Major flows first.

## Board comparison (AC-24), no screenshots

1. Read the board source from [boards/](boards/) (`People8.dc.html`, `People4.dc.html`, `AddPerson6.dc.html`; copies of the canvas boards, so any account works). Pull each element's values from the markup and its script: text, font size and weight, colors, gaps, paddings, radii, shadows, and the states its board switch shows.
2. Open the built page at 1280px with Playwright and take one `browser_snapshot` (structure and wording) and one `browser_evaluate` that returns `getComputedStyle` for the same elements (list pane, row, filter, groups, header tile, name, pill, facts strip, tabs, Access rows, Sign in card, AA dialog steps).
3. List every difference. Allowed only: (a) Plex Mono instead of the boards' JetBrains Mono, and Inter instead of Inter Tight for headings (spec 0016, amended 2026-11-23); (b) spec 0016 token values that changed after the boards (`muted-foreground` `#5b6779`, `destructive` and `error` `#b42318`, `background` `#f3f5f9`, its radius and shadow tables); (c) shadcn based parts with their spec 0016 styles; (d) real data lengths. Anything else is a bug to fix before the PR.

## Major flows

- [x] `multi.admin@` (VRMS and VMMS admin): People shows All, VRMS, VMMS; All lists `multi.lead@` once with VRMS and VMMS chips filled and BMS outlined (AC-3, AC-6)
- [x] Open `multi.lead@`: header, role line, facts strip, Overview cards; Access shows VRMS and VMMS with Change role and BMS read only "Managed by the BMS admin" (AC-7, AC-9, AC-10, AC-12)
- [x] Open `/admin/people/<multi.lead id>?system=BMS` as `multi.admin@`: the whole person shows, no dead end (AC-2)
- [ ] `vrms.admin@` (one system): no system filter (AC-3)
- [x] Suite admin: a person with no role shows the header, "No access to VRMS, VMMS or BMS", Give access on three rows, "No sessions to show", only Delete in ⋮ (AC-8, AC-15, AC-17)
- [ ] Change role to Admin asks for the password, then a toast; on someone's only access "Remove" is disabled with its message; a temporary row has no Change role (AC-12, AC-13)
- [ ] Give access opens AA on step 2 with the person and system set and ends with "[Name] now has [role] in [system]."; Add person opens AA at step 1 (AC-14)
- [ ] Locked person: "Unlock account"; Pending person: "Resend invite" and the setup code line; your own page hides Deactivate, End all sessions, Delete and Change role (AC-8, AC-11, AC-12)
- [ ] Groups: an active person with a pending deletion appears once, in Needs attention; counts in the headings match after Load more (AC-5)
- [x] Sort by Last signed in and Newest first, with Load more across a page boundary (AC-4)
- [ ] Activity shows VRMS and VMMS events with codes, and the filter lists only the viewer's systems (AC-15)
- [x] Suite admin opens a deleted person from Deletion requests: "Deleted, restorable until [date]" and Restore (AC-7, AC-17)
- [x] Phone width (375px): list and person are separate screens with a back link (AC-1, AC-23)
- [x] Keyboard pass and one axe pass on the People page (AC-23)

## API checks (curl through the gateway, cookie session)

- [x] As `multi.admin@`, `GET /auth/admin/users` without `system` lists people of VRMS and VMMS only; a BMS only person's id answers 404 on `/users/:id` without `system`, and 403 `NOT_ADMIN_OF_SYSTEM` with `system=BMS`; a deleted VRMS person is 404 (AC-19)
- [x] `group=attention` returns `counts`; `sort=lastSignedIn` pages by `lastSignedInAt` then `id`, never signed in last; a cursor reused with `sort=newest` answers 400 `INVALID_CURSOR`; `status=LOCKED,SETUP_PENDING` returns only those (AC-20)
- [x] The person answer carries `addedBy`, `failedSignIns30d`, `sessionCount`, `setupCodeExpiresAt`, `restorableUntil` and per role `temporaryUntil` (AC-21)
- [ ] Sign in as a seed account: its `lastSignedInAt` moved and no `directory_changes` row was written for it; a token refresh doesn't move it (AC-22)
- [x] `npm run openapi:check` in welinc-auth and `node scripts/check-contract-routes.mjs welinc-auth/docs/openapi.json` pass (AC-23)
