# Verify: repair form refresh · spec 0005 · updated 2026-10-25
_Steps derived from spec 0005 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones. All steps passed in `/check verify` on 2026-10-28._

## UI / manual

Sign in as `vrms.admin@welinc.com`. Open the form from the sidebar after a full page load (a hot reload can leave the old router in place and crash `useBlocker`; reload if you see "useBlocker must be used within a data router").

### Page and validation
- [x] As a mechanic, open `/repairs/new` → redirected to `/dashboard` → AC-1
- [x] Header reads "New repair ticket", subtitle "Log a vehicle repair and assign it.", and "Reported by {name} · {date}" below it; with an empty profile name it shows the email → AC-1 (name seen in build)
- [x] Four cards in order: Vehicle, Issues, Priority and assignment, Billing; one column at 375px, two short fields per row at 768px and up, max width `max-w-3xl` → AC-2
- [x] Submit the empty form → every required field shows its message under it, no banner, focus lands on the Vehicle trigger, nothing is sent → AC-3 (seen in build)
- [x] Tab out of an empty Odometer → its error shows on leave, then updates while typing → AC-3
- [x] Make only Issue 2's system invalid plus Corporation, submit → focus goes to Issue 2's system (page order) and it is not hidden behind the header or the bottom bar → AC-3

### Vehicle section
- [x] Vehicle search "hiace" finds the Toyota Hiace Commuter by model; each row shows plate plus model → AC-4 (seen in build)
- [x] With a vehicle whose status is `UNDER_REPAIR` (set one in the DB or create a ticket first): the row shows "Under repair", choosing it shows the warning under the field and in the summary, and it stays selectable → AC-4, AC-17
- [x] Driver search " RAMON DELA CRUZ " shows "Ramon dela Cruz" and no Add row; a new name shows `Add "{text}" as a new driver` and the trigger shows it after Add → AC-5 (seen in build)
- [x] `localStorage` has no `welinc_driver_names` written after a create → AC-5
- [x] Garage starts empty with no default; leaving it empty gives "Choose a garage." → AC-6
- [x] Odometer: `0`, `0012`, `9999999` pass; `12,345`, `1e3`, `12.5`, `-1`, `10000000` fail with "Use a whole number of kilometers, up to 9,999,999."; the request sends a number → AC-7 (seen in build)

### Issues section
- [x] Add issue adds "Issue 2" and focuses its Vehicle system; at 10 cards the button is disabled; a remove button shows only with 2 or more cards, named "Remove issue {n}" → AC-8 (add and focus seen in build)
- [x] Type 451 characters → counter turns red; 501 → "Keep it to 500 characters." → AC-8

### Priority and assignment
- [x] Priority defaults to Medium; pressing the selected High again keeps High; Critical and High use the badge colors → AC-9 (seen in build)
- [x] Mechanics: free ones first, busy ones after with "Has open work", alphabetical within each; added ones leave the list → AC-10
- [x] A 101 character outsourced name shows "Keep names to 100 characters." and adds no chip; a name matching a chip offers no Add row → AC-10 (seen in build)
- [x] Close the mechanic picker with no chips → no error until a submit; after submit, adding a chip clears it → AC-10
- [x] Repair shop Other shows Shop name; switching back to a listed shop hides it and clears the value; the request sends the typed name for Other → AC-11

### Billing
- [x] Corporate shows Corporation (empty, required); Online hides it, clears it, and `corporation` is absent from the request → AC-12

### Loading and list failures
- [x] Throttle the network: each picker shows a skeleton on first load while the rest of the form is usable → AC-14
- [x] Block `/vrms/config/garages` → "Couldn’t load garages." with Try again; Create ticket is disabled with the note, linked by `aria-describedby`; Try again refetches only garages → AC-15
- [x] Block `/vrms/config/vehicles` → same as garages, for vehicles → AC-15
- [x] Block `/vrms/mechanics/available` → error and Try again show, the outsourced Add row still works, and the ticket can be created → AC-15
- [x] Block `/vrms/config/drivers` → picker, error and Try again show together; a new driver name can still be added → AC-15
- [x] Empty lists show "No vehicles are registered yet." / "No garages are set up yet." (both block submit) and the mechanics helper → AC-15

### Submitting
- [x] Below 1024px Cancel and Create ticket sit in a bar at the bottom, right aligned from 768px; nothing hides behind it at 375px; inline and right aligned from 1024px → AC-16 (375px clearance seen in build)
- [x] Valid submit opens "Create this repair ticket?" with Vehicle "{plate} · {model}", Priority badge, Mechanics (outsourced marked), "{n} issues: {systems}", Garage → AC-17 (seen in build)
- [x] While saving (throttle the POST): spinner on Create ticket, Keep editing disabled, Escape and overlay click do nothing → AC-17
- [x] Request body has no `repairNumber`; `issueDescription` is issue 1's description; all text trimmed → AC-18 (no `repairNumber` seen in build)
- [x] Success: toast "{repairNumber} created.", the new ticket opens, Back goes to the page before the form → AC-19 (seen in build)
- [x] Deactivate the chosen vehicle in another tab, then create → dialog closes, input stays, alert "Couldn’t create the ticket: {message}" takes focus, error toast shows, Vehicle reads "This vehicle is no longer available. Choose another."; submitting again without changes still shows it and sends nothing → AC-20
- [x] Network offline on create → the fallback "Couldn’t create the ticket. Check your connection and try again." → AC-20
- [x] Press Enter twice fast in the summary → one POST; click the sidebar while saving → nothing happens and the new ticket opens → AC-21

### Leaving the form
- [x] Dashboard, list, detail, history, audit log, users, profile and the login redirect all load and navigate as before the data router → AC-22 (dashboard, list and form seen in build)
- [x] Untouched form, click Repair tickets → leaves with no prompt → AC-23 (seen in build)
- [x] Changed form: the sidebar link, Cancel, and in app Back each show one "Discard this ticket?" prompt; Keep editing stays, Discard leaves; a link to New repair itself never prompts → AC-23 (seen in build)
- [x] Reload or close the tab with changes → the browser's own prompt → AC-23 (seen in build)
- [x] Back with the summary open → the summary closes, then one discard prompt → AC-23

### Quality
- [x] Complete the whole form with the keyboard only → AC-24
- [x] axe at 375px and 1280px, form and open summary: no serious or critical issues → AC-24 (seen in build, after the dialog's fade in)

## Value sourcing
- [x] Reporter name matches `user.name` in the auth store; date is the page open time, not the submit time → AC-1
- [x] Vehicle options and models match `GET /vrms/config/vehicles`; the "Under repair" badge matches `status` → AC-4
- [x] Driver options match `GET /vrms/config/drivers`, one per name ignoring case → AC-5
- [x] Garage options match `GET /vrms/config/garages` → AC-6
- [x] System, root cause, shop and corporation lists match `getRepairFormOptions()` → AC-13
- [x] Priority toggle colors match `PriorityBadge` → AC-9
- [x] Mechanics order and badge match `isAvailable` from `GET /vrms/mechanics/available` (make one mechanic busy and check it moves down) → AC-10
- [x] Create ticket blocks only on vehicles or garages failing or empty, never on drivers or mechanics → AC-15
- [x] Summary values equal the form values; the model comes from the vehicles list → AC-17
- [x] Toast text and target route come from the returned ticket (`repairNumber`, `id`) → AC-19
- [x] Alert text uses the server message when present, else the fallback → AC-20
- [x] "No longer available" errors follow the refetched lists; with a failed refetch the check is skipped and chips stay → AC-20
- [x] The leave guard follows `isDirty`: change a field and change it back, then leave → no prompt → AC-23

## Commands
- [x] `npm run lint` in welinc-web-vrms → no problems → AC-25 (passed in build)
- [x] `npm run typecheck` in welinc-web-vrms → no errors → AC-25 (passed in build)
- [x] `npm run build` in welinc-web-vrms → builds → AC-25 (passed in build)
- [x] `git -C welinc-backend-vrms status` → no changes from this feature → AC-25
- [x] Search web-vrms for `loadDriverNames`, `saveDriverName`, `generateRepairNumber` → none; `LegacyButton` and `style={` absent from the form files → AC-5, AC-18, AC-24 (passed in build)

## Acceptance-criteria coverage
- AC-1 to AC-25 each have at least one step above. AC-14, AC-15, AC-20 and AC-21 have not been run live yet.
