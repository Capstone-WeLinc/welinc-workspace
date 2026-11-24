# Verify: Portal redesign · spec 0019 · updated 2026-11-25
_Steps derived from spec 0019 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones. This first batch covers the People filter and Add a user (milestone 3 of S22); later milestones append theirs._

## UI / manual

*People filter (sign in as a suite admin, open `/admin/people`)*
- [ ] The list pane shows one **Filter** button beside the search and no system switcher → AC-21
- [ ] Open Filter: Status chips read Needs attention, Locked, Pending, Active, Inactive, each with a count; three system rows in VRMS, VMMS, BMS order, each with its count in the pill → AC-21, AC-21b
- [ ] Compare the open popover with `boards/Filter18.dc.html` option 2 (soft tint chips): 18px radius card, uppercase section labels, 50px system rows, 30px chips, navy Show button → AC-21, AC-29
- [ ] Open the VRMS row: its roles fold open in about 180 ms, any other open row closes; roles are in catalog order with counts → AC-21
- [ ] Tick VMMS Mechanic: BMS Driver's count stays the same; the VMMS pill reads "Mechanic"; tick a second VMMS role: "2 roles"; tick every VMMS role: the box turns full and the pill reads "Everyone" → AC-21, AC-21b
- [ ] With picks made, the footer says "N filters on" (status chips plus systems not off) and the address has not changed yet → AC-21
- [ ] Press Esc, open again: the draft is gone and the applied picks show → AC-21
- [ ] Tick VRMS whole plus VMMS Mechanic and BMS Driver, press Show: the address carries `access=VRMS,VMMS:MECHANIC,BMS:DRIVER`; the list shows anyone in VRMS or holding either role; Show's number equals the summed group counts → AC-21, AC-21a, AC-21b
- [ ] The Filter button shows a badge with the applied count → AC-21
- [ ] Tick Locked only and Show: groups with 0 people hide; with nothing matching, "No one matches these filters" shows with **Clear filters**, not Add user → AC-21
- [ ] Reload with picks applied: the same picks and list come back from the address → AC-21
- [ ] Open `/admin/people?status=LOCKED,BOGUS&access=VRMS:GONE,VMMS` as a VRMS only admin: the address is rewritten without the bad items before the list loads, and no 400 or 403 shows → AC-21
- [ ] Open `/admin/people?system=VMMS` from a strip link: the popover shows only the VMMS row, and the facets call sends `system=VMMS` → AC-21
- [ ] Type in the search without pausing and open Filter: the counts use the applied `q` in the address, not the half typed text → AC-21
- [ ] Throttle the network: every count and Show's number show a dash while loading; a facets failure leaves the dashes with no toast and Show still applies → AC-21, AC-21b
- [ ] With `access=VRMS` applied, Add user opens with VRMS preselected; with two systems applied, no system is preselected → AC-21

*Add a user*
- [ ] Add user opens one screen titled "Add a user", email first; compare with `boards/AddUser15.dc.html` (640px dialog, field heights, role cards two per row, grey summary box) → AC-22, AC-29
- [ ] Type `cristina.delacruz@welinc`: after the pause a red ! and "Enter the whole email, like name@welinc.com." show, and no email check call goes out (network panel) → AC-22
- [ ] Finish the email: the steering wheel shows while checking, then a navy tick ("Email is free"); the network shows one `email-check` call per pause, older ones cancelled → AC-22, AC-23
- [ ] With a free email, Full name and Contact number (optional) show; submit with no name or role: both errors show → AC-22
- [ ] Add with a contact number: the person page shows the contact; `users.contact` holds it → AC-22
- [ ] Type an email that has an account in VMMS only: the title turns to "Give access", the name fields hide, the card names the person, VMMS is greyed "Already has it" → AC-22, AC-23
- [ ] As a VRMS only admin, type a suite admin's email: the dialog shows "already has an account" with no systems listed, never "suite admin" → AC-23
- [ ] As a suite admin, type a suite admin's email: "A suite admin" card, the add button disabled → AC-23
- [ ] Type the email of someone already in the picked system: "Already in VRMS" card with **Open user**, which opens their page → AC-22, AC-23
- [ ] Type a deactivated or deleted account's email: "Account not active", add disabled → AC-23
- [ ] As an admin of one system: no system cards, the role label reads "Role in VRMS" → AC-22
- [ ] Give access from a person's Access tab: the email is fixed, the system preselected, the systems they hold greyed → AC-22
- [ ] The summary box says the setup code works for one hour → AC-22

## Commands
- [ ] `cd welinc-web-portal && npm run lint && npm run build:local` → both pass → AC-29
- [ ] `cd welinc-web-portal && npx vitest run --maxWorkers=2` → all pass (an unlimited run on the Intel Mac can time out under load) → AC-29
- [ ] `curl` the facets route with `access=VMMS:MECHANIC,VMMS:MECHANIC` and `access=VMMS:MECHANIC` (as an admin, with the cookie) → the same answer → AC-21a

## Value sourcing checks
- [ ] Filter rows offered come from the viewer's admin scope: a VRMS admin sees one row, a suite admin three → AC-21 (Value sourcing: Filter rows)
- [ ] Role chips and their names come from `/auth/systems` in catalog order (compare with the catalog answer) → AC-21
- [ ] "Show N people" equals the facets `total` for the draft, never a sum of chip counts → AC-21b
- [ ] The People list's group calls carry `status` and `access` from the address (network panel) → AC-21
- [ ] Role cards' one line meaning matches each role's `description` in `/auth/systems` → AC-22
- [ ] The email status, name and systems come from `email-check` (change the system card and see a new check for that system) → AC-23

## Acceptance-criteria coverage
- AC-21: filter steps 1 to 16 · AC-21a: step 8, command 3 · AC-21b: steps 2, 5, 8, 15, value checks 3 · AC-22: Add a user steps 1, 4 to 6, 9, 11 to 13 · AC-23: steps 2, 3, 6 to 10 · AC-29: board comparisons and commands
- Not yet covered here (later milestones): AC-1 to AC-14, AC-16, AC-27, the launcher and motion. AC-15, AC-17 to AC-20 and AC-24 to AC-26, AC-28 were built in earlier commits on `feat/portal-redesign`; append their steps when you next run `/develop` or `/check verify`.
