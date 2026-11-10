# 0005. Repair form on the design system, with pickers and inline validation

**Date**: 2026-10-25
**Status**: In Progress
**Updated**: 2026-11-11 (staleness sweep). The route guard is `RequirePermission keys={['ticket.create']}` (spec 0011; `RequireRole` is gone). Mechanics are sent by `Mechanic` id (spec 0010 AC-12); the outsourced chip waits for feature 36. The Repair shop field and `shopName` are gone (spec 0010). The driver picker is keyed by license with `driverId` or `newDriver` (spec 0016 AC-6), and corporation is `corporationId` from the lookup list (spec 0016 AC-4). The create body sends an `issues` list (at least one), not `issueDescription`, and priority, account type and corporation are now stored.

## Summary

This spec rebuilds the New repair ticket page (`/repairs/new`) on the spec 0001 components, for scope feature 12. The form becomes one page in four sections (Vehicle, Issues, Priority and assignment, Billing) with searchable pickers instead of typed fields, errors shown under each field, a submit bar within thumb reach on a phone, and a short summary to check before the ticket is created. It is a pure frontend change (Facade): no backend or database change. The rest of WL-201 (issue types, saved priority, open ticket counts, Assigned or Open on create) stays with feature 18.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As an admin, I want to pick the vehicle, driver, garage and mechanics from lists instead of typing them, so that a ticket never fails or lands on the wrong record because of a typo.
- As an admin, I want each mistake shown next to the field it belongs to, so that I can fix it without hunting through a banner.
- As an admin on a phone, I want the submit button within thumb reach and the inputs big enough to tap, so that I can log a repair from the yard.
- As an admin, I want a short summary before the ticket is created, so that I catch the wrong vehicle before it is marked under repair.
- As an admin, I want to be warned before I lose a half filled form, so that a stray tap on the sidebar doesn't cost me the work.

**Acceptance criteria**:

*Page and form behavior*

- **AC-1**: `/repairs/new` stays admin only (the existing `RequireRole role="ADMIN"` route guard and the backend `@Roles(ADMIN)`). The `PageHeader` reads "New repair ticket" with the `Wrench` icon and the subtitle "Log a vehicle repair and assign it." Under the header, a muted `text-sm` line reads "Reported by {user.name} · {date}" (falling back to `user.email` when the name is empty), where the date is `formatShortDate` of the time the page opened. This line is display only, is not sent, and does not update if the page stays open past midnight.
- **AC-2**: The form is one scrolling page of four `Card` sections, in this order, each with a heading: **Vehicle** (vehicle, driver, garage, odometer), **Issues**, **Priority and assignment** (priority, mechanics, repair shop), **Billing** (account type, corporation). Fields stack in one column on a phone; from 768px, short fields sit two per row inside a section. Below 1280px the sections stack in one column, aligned left with the page header at a max width of `max-w-3xl`. From 1280px the form uses the full page width in two columns, like the repair detail page: **Vehicle** and **Issues** in the left two thirds, **Priority and assignment** and **Billing** in the right third, with the action buttons across the bottom. Fields inside the right column always stack one per row.
- **AC-3**: The form is built with react-hook-form, one zod schema (`zodResolver`) and the shadcn `Field` parts. Validation mode is `onTouched`: a field shows its error after you leave it, then updates as you type. On a submit with errors, every error shows and focus moves to the first invalid field, scrolled into view; for a picker (`Combobox`, `Select`) the focus target is its trigger button, and for the mechanics list it is the mechanic picker's trigger. Every field wrapper carries a `scroll-mt` large enough that the focused field is not hidden by the header or the fixed action bar. Defaults: pickers and text fields start as `''`, Issues starts with one empty issue, Mechanics as `[]`, Priority `MEDIUM`, Account type `ONLINE`. Each error sits under its field per `design.md` (`destructive` border and message, an icon, `text-xs`), wired with `aria-invalid` and `aria-describedby`. Required fields carry the required marker. There is no page level banner for field errors.

*Vehicle section*

- **AC-4**: **Vehicle** is a searchable `Combobox` over `getVehicles()`, matching on plate or model (the model is passed as the option's search `keywords`). Each row shows the plate with the model as secondary text. Free typing is not possible, so only a registered, active plate can be sent. It starts empty and is required ("Choose a vehicle."). A vehicle whose `status` is `UNDER_REPAIR` shows an "Under repair" badge in the list, and when chosen, a warning helper under the field: "This vehicle already has a repair in progress. Check its open tickets before adding another." It stays selectable. The chosen vehicle's `plateNumber` is sent as `vehiclePlate`.
- **AC-5**: **Driver** is a searchable `Combobox` over the names from `getDrivers()`, deduplicated by trimmed name ignoring case (the first one in the response wins; the name is the value, since the server matches drivers by name). When the typed text, trimmed, matches no name (ignoring case), the list offers a row `Add "{text}" as a new driver`, which sets the value to that text; the trigger then shows that text even though it is not in the options. Required, up to 100 characters after trimming ("Choose or add a driver." / "Driver name must be 100 characters or fewer."). Helper text: "New names are saved as unverified drivers." The localStorage driver list (`loadDriverNames`, `saveDriverName`, key `welinc_driver_names`) is deleted, so suggestions are the same on every device.
- **AC-6**: **Garage location** is a `Select` over `getGarages()`. It starts empty, with no default, and is required ("Choose a garage."). The chosen garage's `name` is sent as `garageLocation`.
- **AC-7**: **Odometer reading** is a text `Input` with `inputMode="numeric"` and a "km" suffix. Required. After trimming, the text must match `^\d{1,7}$`: digits only, so commas, spaces inside, decimals, signs and `e` are rejected, and leading zeros are allowed ("Enter the odometer reading." / "Use a whole number of kilometers, up to 9,999,999."). The form holds it as a string and the schema outputs a number, so `useForm` is typed with `z.input` and `z.output` of the schema. It is sent as a number.

*Issues section*

- **AC-8**: Issues are a `useFieldArray` list of 1 to 10 cards titled "Issue {n}". Each card has **Vehicle system** and **Root cause** (`Select`s over the fixed lists, both starting empty, required: "Choose a system." / "Choose a root cause.") and **Description** (`Textarea`, required, 1 to 500 characters after trimming: "Describe the issue." / "Keep it to 500 characters."), with a live "{n} / 500" counter that turns `destructive` above 450. An "Add issue" button (`Plus` icon) adds a card and moves focus to its Vehicle system field; it is disabled at 10, with the helper "Up to 10 issues per ticket." Each card has a remove button (`Trash2` icon, accessible name "Remove issue {n}"), hidden while only one card exists. Removing needs no confirm.

*Priority and assignment section*

- **AC-9**: **Priority** is a single choice `ToggleGroup` (`type="single"`, Low, Medium, High, Critical), defaulting to Medium, labeled by its field label for screen readers. The selected item uses the `PriorityBadge` color for that level. It can never be empty: Radix sends `''` when the selected item is pressed again, and the handler ignores it (`onValueChange={(v) => v && field.onChange(v)}`).
- **AC-10**: **Mechanics** is a searchable `Combobox` used as an adder: choosing a mechanic adds a chip below the picker and clears the picker. It lists `getAvailableMechanics()`, free mechanics first, then busy ones (`isAvailable` false), alphabetical within each group; busy mechanics are selectable and carry a "Has open work" badge. Mechanics already added are left out of the list. Mechanics are listed and stored by name, since the server matches them by name. When the typed text, trimmed, matches no mechanic in the list and no chip (ignoring case), the list offers `Add "{text}" as outsourced`; if it matches an in house name, only that in house option shows. Adding text over 100 characters is refused with the field error "Keep names to 100 characters." Each chip shows the name, an "Outsourced" badge where it applies, and a remove button (accessible name "Remove {name}") that always works, also on a chip marked no longer available (AC-20). The form field is `{ name, isOutsourced }[]`. At least one mechanic is required ("Assign at least one mechanic."); this error shows only after a submit, not when the picker closes with no chips, and clears as soon as a chip is added. At submit, in house mechanics are sent as `{ name, isOutsourced: false }`, outsourced ones as `{ name, isOutsourced: true, shopName: name }`, as today.
- **AC-11**: **Repair shop** is a `Select` over the fixed shop list plus "Other". It starts empty and is required ("Choose a repair shop."). "Other" uses the sentinel value `__other__`, which cannot collide with a real shop name, and shows a **Shop name** `Input` below it, required, up to 100 characters ("Enter the shop name." / "Keep it to 100 characters."); the typed name is sent as `shopName`, otherwise the chosen shop is. Choosing a listed shop after Other hides the Shop name field and clears its value. The conditional rules for Other and for Corporate (AC-12) are checked in the schema's `superRefine`.

*Billing section*

- **AC-12**: **Account type** is a single choice `ToggleGroup` (Online, Corporate), defaulting to Online, never empty. Corporate shows a **Corporation** `Select` over the fixed list, starting empty and required while Corporate ("Choose a corporation."). Switching back to Online hides and clears it, and `corporation` is not sent.
- **AC-13**: Corporations, shops, vehicle systems and root causes stay hardcoded in `src/lib/repairOptions.ts`, read only through one getter, `getRepairFormOptions()`, so feature 40 can change the source without touching the form.

*Loading and list failures*

- **AC-14**: The four lists (vehicles, drivers, garages, mechanics) load in parallel when the page opens, each on its own. On that first load only, a loading list's field shows a `Skeleton` the size of the field; the rest of the form is usable. A later refetch (Try again, or AC-20) keeps the field and its current options on screen, so nothing unmounts or loses focus. Create ticket stays enabled while lists are still loading; the empty required fields then fail validation as usual.
- **AC-15**: When a list fails to load, its field shows an inline error ("Couldn't load vehicles.", "Couldn't load drivers.", "Couldn't load garages.", "Couldn't load mechanics.") with a "Try again" button that refetches that list only. Submitting is blocked only when the failure leaves a required field impossible to fill: if vehicles or garages failed, the Create ticket button is disabled and a note above it reads "Some lists couldn't load. Try again above before creating the ticket.", linked to the button with `aria-describedby`. If drivers failed, the driver picker, its error and Try again all show together, and the picker still accepts a new name through its Add row. If mechanics failed, the same applies, and the picker still offers the outsourced Add row. A list that loads empty shows a helper instead of an error: "No vehicles are registered yet." or "No garages are set up yet." (both block submitting the same way), and "No in house mechanics are set up yet. Add an outsourced one." for mechanics.

*Submitting*

- **AC-16**: The actions are **Cancel** (secondary) and **Create ticket** (primary). Below 1024px they sit in a bar fixed to the bottom of the screen, following `NextActionBar` (`fixed inset-x-0 bottom-0 z-30`, `border-t`, `bg-card`, safe area padding); admins have no `MobileTabBar`, so the bar sits at the bottom edge. The page adds a fixed bottom padding token sized for the bar's tallest case (the AC-15 note wrapped to two lines, plus the safe area), so nothing hides behind it without measuring. A `ResponsiveDialog` bottom sheet below 768px stacks above the bar. From 1024px up the actions sit inline at the end of the form, right aligned. Tap targets are at least 44px tall on a phone.
- **AC-17**: Pressing Create ticket (or Enter in a field) validates first; with errors, AC-3 applies and nothing is sent. With a valid form, a `ResponsiveDialog` titled "Create this repair ticket?" shows a summary: **Vehicle** "{plate} · {model}" (plus the AC-4 warning line when it is under repair), **Priority** as a `PriorityBadge`, **Mechanics** (names, outsourced ones marked), **Issues** "{n} issues: {systems, comma separated}", and **Garage**. Its buttons are "Create ticket" (primary) and "Keep editing". The dialog stays open while the request runs, its Create ticket button shows a spinner and is disabled, and "Keep editing" is disabled too. While saving, the dialog also ignores Escape, an overlay click and a swipe to close the sheet (its `onOpenChange` does nothing while saving).
- **AC-18**: The request is `createRepair()` with the existing `CreateRepairPayload`, all text trimmed, with these changes: `repairNumber` is no longer sent (the server generates it; `generateRepairNumber` is deleted from the client), `issueDescription` is the first issue's description (the DTO still requires it), `corporation` only for Corporate, and `shopName` per AC-11.
- **AC-19**: On success the dialog closes, a success toast reads "{repairNumber} created.", and the page navigates to `/repairs/{id}` from the returned ticket, replacing the form in history (so Back does not reopen an empty form). The leave guard (AC-22) does not fire for this navigation.
- **AC-20**: On failure, in this order: the dialog closes, everything typed stays, a `FormAlert` (`role="alert"`) in the page flow at the end of the form, just before the inline actions, shows "Couldn't create the ticket: {message}" using `getApiErrorMessage`, or "Couldn't create the ticket. Check your connection and try again." when there is no server message, and focus moves to that alert. An error toast shows the same text (on a phone, where the alert may sit behind the bar, the toast is the visible signal). Then all four lists refetch, and the form re-validates once every refetch has settled. "Still in its list" is part of the schema, not a one off `setError`: the resolver reads the current lists, so a chosen vehicle plate, garage name or in house mechanic name missing from its loaded list fails on every validation, with "This vehicle is no longer available. Choose another.", "This garage is no longer available. Choose another.", or, on the chip, "{name} is no longer available." The check is skipped for a list whose last load failed (the server's message stays the guide). Create ticket is enabled again, and the alert clears on the next submit.
- **AC-21**: Only one create request can be in flight: Create ticket is disabled while saving, and Enter while saving does nothing. While saving, the leave guard holds every in app navigation without asking (the blocker resets it), so the request always finishes on the form. After success, the page navigates only if it is still mounted.

*Leaving the form*

- **AC-22**: The app moves to a data router so navigation can be blocked: `main.tsx` uses `createBrowserRouter([{ path: '*', element: <App /> }])` with `RouterProvider`, and `App.tsx` keeps its `<Routes>` unchanged. Links in descendant routes resolve against `/`, so relative `to=` and `navigate('x')` calls are checked (grep) and made absolute if any exist. Every existing page still loads and navigates as before.
- **AC-23**: While the form has changes (`formState.isDirty`) and no create has succeeded, any in app navigation away (Cancel, the sidebar, header links, the browser Back button) is held by `useBlocker` and asks through `confirm()`: title "Discard this ticket?", description "What you entered on this form will be lost.", confirm "Discard" (`tone: 'destructive'`), cancel "Keep editing". Discard continues the navigation; Keep editing stays on the form. A tab close or reload with changes triggers the browser's own prompt (`beforeunload`, calling `preventDefault()` and setting `returnValue`), removed once a create succeeds. An untouched form leaves without asking. Cancel goes to `/repairs` and, when dirty, shows exactly one prompt (the blocker's). Wiring rules:
  - `useBlocker` takes the function form: block when `dirtyRef.current && !submittedRef.current && currentLocation.pathname !== nextLocation.pathname` (so a link to `/repairs/new` itself never prompts), or always while saving (AC-21). `dirtyRef` mirrors `formState.isDirty`, read through the `formState` proxy in render; `submittedRef` is set synchronously right before the success `navigate`, so the blocker never sees a stale value.
  - The prompt runs once per blocked navigation: a ref guards the effect on `blocker.state === 'blocked'` against the StrictMode double run. The sequence is `const ok = await confirm(...)`, then `ok ? blocker.proceed() : blocker.reset()`, each called once.
  - If the summary dialog is open when a navigation is blocked (Back pressed), it closes before the discard prompt shows, so two modals never stack.

*Quality*

- **AC-24**: `RepairFormPage` and every component it renders use only spec 0001 components and theme tokens: no inline `style`, no legacy classes (`card`, `input`, `field-grid`, `small-note`, `tag-pill` and the like), no `LegacyButton`, no hex values. `IssueLoggingSection` and `MechanicAssignmentSection` are rebuilt on react-hook-form or replaced. Inputs use `text-base` on phones (no iOS zoom). The whole form can be completed with the keyboard alone. At 375px and 1280px there is no horizontal scroll, and axe reports no serious or critical issues on `/repairs/new`, including with the summary dialog open.
- **AC-25**: `npm run lint`, `npm run typecheck` and `npm run build` pass in welinc-web-vrms. welinc-backend-vrms is not changed.

## Decision

**Chosen option**: Option 2: Rebuild the form on react-hook-form and the design system, on the data it already has

The page is rebuilt as one react-hook-form form with a single zod schema, shadcn pickers over the four existing config endpoints and the fixed lists, a summary confirm, and a navigation guard on a data router; the backend and the stored data stay as they are.

**Implementation skills**: `shadcn` (`shadcn-ui/ui`, `.claude/skills/shadcn/`, `ToggleGroup`, `Combobox`, `Field`) · `react-hook-form` (`pproenca/dot-skills`, `.claude/skills/react-hook-form/`, the schema, `useFieldArray` for issues, `useController` for the pickers) · `vercel-react-best-practices` (`vercel-labs/agent-skills`, `.claude/skills/vercel-react-best-practices/`) · `vercel-composition-patterns` (`vercel-labs/agent-skills`, `.claude/skills/vercel-composition-patterns/`, the Combobox extension)

**Calls made in this spec** (each with the runner up):
- **Extend the shared `Combobox`** with optional props: `description`, `badge` and `keywords` on an option (secondary text, a small badge, extra search terms passed to cmdk), and `onCreate(text)` with `createLabel(text)` for the Add row. The search text becomes controlled state inside `Combobox`, reset when the list closes; the Add row is `forceMount`ed so cmdk's filter never hides it, and shows only when `onCreate` is set and the trimmed text matches no option. When `value` matches no option, the trigger shows `value` itself (a newly added name). Existing callers are unchanged. Mechanics use it as an adder, with the chips rendered by the form. Runner up: a separate multi select component, which duplicates the search and popover code.
- **Summary confirm as a `ResponsiveDialog`**, because `confirm()` only takes a string description and the summary needs badges and lists. Runner up: widen `confirm()` to take a React node, which changes a shared API for one caller.
- **Data router by wrapping, not rewriting**: one splat route renders today's `<App />`, so `useBlocker` works and no route moves. Runner up: convert every route to route objects, which is cleaner long term but touches every route for no gain today.
- **System, root cause, garage and repair shop start empty**, like the garage you chose: a silent first option default (today's "Brakes" and "Wear and tear") puts wrong data on tickets that nobody notices. Priority and account type keep a default, because every option is visible in the toggle and Medium and Online are the honest common case. Runner up: keep the first option defaults.
- **Odometer as a text input with `inputMode="numeric"`**, not `type="number"`, which accepts `e`, changes on mouse wheel and gives a poor error. Upper bound 9,999,999 km. Runner up: `type="number"` as today.
- **Validation mode `onTouched`**, so errors don't appear while you are still typing your first value. Runner up: `onSubmit` only, which hides errors until the end of a long form.
- **Navigate with `replace` after a create**, so Back from the new ticket goes to where you were before the form. Runner up: a normal push, which makes Back open a blank form.
- **The schema and option getter live in `src/features/repair/lib/repairFormSchema.ts`** and `src/lib/repairOptions.ts`, beside the other repair helpers. Runner up: inline in the page.

## Feature design

**Data model**: no change. No migration, no new column, no new endpoint. Priority, account type, corporation and repair shop are still sent but still not stored (see Follow-up).

**State transitions**: none on the server. Client side, the form moves: editing → confirming (summary dialog) → saving → done (navigates away) or back to editing with an alert.

**API surface** (all existing, unchanged):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/config/vehicles` | GET | none | `{ id, plateNumber, model, status }[]`, active vehicles, by plate | bearer, ADMIN or MECHANIC | 401 |
| `/vrms/config/drivers` | GET | none | `{ id, name, licenseNumber }[]` | bearer, ADMIN or MECHANIC | 401 |
| `/vrms/config/garages` | GET | none | `{ id, name }[]` | bearer | 401 |
| `/vrms/mechanics/available` | GET | none | `{ id, name, isAvailable }[]`, active in house mechanics | bearer, ADMIN or MECHANIC | 401 |
| `/vrms/repairs` | POST | `CreateRepairPayload` without `repairNumber` | the created `RepairTicket` (`id`, `repairNumber`, ...) | bearer, ADMIN | 400 (unknown plate, garage or in house mechanic; DTO limits), 401, 403 |

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Header | Reporter name | `user.name` from `useAuthStore` |
| Header | Reported date | `formatShortDate` of the time the page mounted |
| Vehicle | Options, model text | `getVehicles()`: `plateNumber`, `model` |
| Vehicle | "Under repair" badge and warning | `getVehicles()`: `status === 'UNDER_REPAIR'` |
| Driver | Options | `getDrivers()`: `name`, unique by name |
| Driver | New driver row | The typed text when it matches no option |
| Garage | Options | `getGarages()`: `name` |
| Issues | System and root cause options | `getRepairFormOptions()` from `repairOptions.ts` |
| Priority | Options and colors | `PRIORITY_OPTIONS` and the `PriorityBadge` color map |
| Mechanics | Options, order, "Has open work" badge | `getAvailableMechanics()`: `name`, `isAvailable` |
| Mechanics | Outsourced row | The typed text when it matches no option and no chip |
| Repair shop, corporation | Options | `getRepairFormOptions()` |
| Submit | Whether a list blocks submit | The vehicles and garages queries' error or empty state |
| Summary | Plate, model, priority, mechanics, issue systems, garage | The current form values plus the chosen vehicle's `model` |
| Create | Payload | Form values mapped per AC-18 |
| Success | Toast text, target route | The returned ticket's `repairNumber` and `id` |
| Failure | Alert text | `getApiErrorMessage(err, '')`, else the fixed fallback |
| Failure | "No longer available" field errors | The refetched lists compared with the chosen vehicle plate, garage name and in house mechanic names |
| Leave guard | Has changes | `formState.isDirty`, plus a `submitted` flag set on success |

**Key invariants**:
- The form can only send a plate, garage and in house mechanic that were in the server's lists when it loaded, so the backend's strict lookups only fail on a change made meanwhile.
- No field silently defaults to a value the user didn't see: lists with hidden options start empty.
- "Still in its list" for vehicle, garage and in house mechanics is a schema rule, so it holds on every submit, not just after a failure.
- One schema is the only source of field rules and messages; the limits match `create-repair.dto.ts` (driver and names 100, issue description 500, odometer at least 0).
- One create request at a time.
- The fixed option lists are read only through `getRepairFormOptions()`.
- No inline style, hex value, legacy class or `LegacyButton` in the form page or its components.

**Security model**: unchanged. Only admins reach the page (client guard) and create tickets (server `@Roles(ADMIN)`). The reporter line uses the logged in user already in the store; nothing new is stored or sent. Removing the localStorage driver list stops driver names from lingering in the browser.

**Failure and edge cases**:
- A list fails or loads empty: AC-15.
- The server rejects the create (a vehicle or mechanic removed meanwhile, the network drops): AC-20.
- Two admins create tickets for one vehicle at once: both succeed (the server has no rule against it); the second one's summary showed "Under repair" only if its vehicle list loaded after the first create. Accepted; feature 18 can add a server check.
- A driver name that differs only in case or spacing from an existing one: the Add row is not offered (ignore case, trimmed), so the existing name is picked.
- Two in house mechanics with the same name: the server's `findFirst` by name would always pick the first. The picker dedupes by name, so only one shows. A known limit of name matching, left to feature 18.
- An outsourced mechanic name typed with the same name as an in house mechanic: the in house option matches, so no Add row is offered.
- A double tap on Create ticket: AC-21.
- The session expires while the form is open: the axios 401 handler sets `window.location.href = '/login'`, a full page load, so `useBlocker` does not see it but the `beforeunload` prompt does fire on a changed form. Leaving still loses the input. Accepted.
- The user changes a field and then changes it back: `isDirty` compares with the defaults, so the guard no longer fires. Expected.

**Configuration required**: none.

**Critical test scenarios**:
- Happy path: pick a vehicle, add a new driver name, pick a garage, enter an odometer, fill two issues, set High, add one in house and one outsourced mechanic, pick a shop, choose Corporate and a corporation; the summary shows these values; create; the toast names the repair number and the new ticket's page opens; Back skips the form. Verifies **AC-4** to **AC-12**, **AC-17** to **AC-19**
- Validation: submit an empty form; every required field shows its message, focus lands on Vehicle, and nothing is sent. Type 501 characters in a description; the counter turns red and the error shows. Verifies **AC-3**, **AC-8**
- Under repair: pick a vehicle with an open ticket; the badge and warning show in the field and the summary. Verifies **AC-4**, **AC-17**
- Busy mechanic: a mechanic with an active ticket is listed after free ones with "Has open work" and can be added. Verifies **AC-10**
- List failure: block `/vrms/config/garages`; the garage field shows its error and Try again, and Create ticket is disabled with the note. Block `/vrms/mechanics/available` instead; outsourced entry still works and the form can be created. Verifies **AC-14**, **AC-15**
- Server reject: deactivate the chosen vehicle in another tab, then create; the alert and toast show the server message, input stays, and the vehicle field reads "This vehicle is no longer available." Verifies **AC-20**
- Leave guard: type in a field, click Repairs in the sidebar; the discard prompt shows; Keep editing stays, Discard leaves. Press Back with changes; same prompt. Reload with changes; the browser prompt shows. Open the form and leave untouched; no prompt. Verifies **AC-23**
- Router: after the data router change, open the dashboard, list, detail, history, audit log, users, profile and the login redirect; all work as before. Verifies **AC-22**
- Phone: at 375px, the bar sits at the bottom with no content hidden behind it, inputs don't zoom, and the toggles and chips are easy to tap; at 1280px the actions are inline. Axe on the form and the open summary dialog. Verifies **AC-16**, **AC-24**
- Pickers: in the driver picker, typing " juan dela cruz " for an existing "Juan Dela Cruz" offers no Add row; a new name shows in the trigger after Add. A 101 character outsourced name is refused with its error. Vehicle search finds a vehicle by its model. Verifies **AC-4**, **AC-5**, **AC-10**
- Odometer: `0`, `0012` and `9999999` pass; `12,345`, `1e3`, `12.5`, `-1` and `10000000` fail. Verifies **AC-7**
- Stale value: after a failed create marks a vehicle no longer available, submitting again without changing it still shows the error and sends nothing. With mechanic chips added, a failed mechanics refetch leaves the chips and skips their check. Verifies **AC-20**
- Double submit: press Enter twice quickly in the summary dialog; one request goes out. Click the sidebar while saving; nothing happens and the new ticket opens. Verifies **AC-21**
- Back with the summary open: the summary closes and one discard prompt shows. Verifies **AC-23**
- Cleanup: searching web-vrms for `loadDriverNames`, `saveDriverName`, `generateRepairNumber`, `LegacyButton` and `style={` under the form's files finds nothing; `repairNumber` is absent from the request body. Verifies **AC-5**, **AC-18**, **AC-24**

## Build plan

Facade, as the scope row says: the form is rebuilt on the data the API already returns, with no backend change. Each step leaves the page working.

1. Data router: switch `main.tsx` to `createBrowserRouter([{ path: '*', element: <App /> }])` with `RouterProvider`, leaving `App.tsx` routes as they are; grep for relative links and navigates; click through every page to confirm nothing moved. Satisfies **AC-22**
2. Shared pieces (the riskiest step): add the shadcn `toggle-group` component; extend `Combobox` per the *Calls made* entry (option `description`, `badge`, `keywords`; controlled search reset on close; a `forceMount`ed Add row via `onCreate` and `createLabel`; the trigger showing an unmatched `value`), checking the dev UI page's existing usage still works; add `getRepairFormOptions()` to `repairOptions.ts` and delete `loadDriverNames` and `saveDriverName`. Satisfies **AC-5**, **AC-9**, **AC-10**, **AC-12**, **AC-13**
3. Schema and data: `repairFormSchema.ts` (a schema factory taking the current lists, so "still in its list" is a rule; every message from the ACs; `superRefine` for Other and Corporate; the default values; `z.input` and `z.output` types; and a `toCreatePayload()` mapper without `repairNumber`); a `useRepairFormOptions` hook that loads the four lists independently, each with its own first load, error, empty and `retry`, keeping old data during a refetch, plus a `refetchAll` that resolves when all four settle. Satisfies **AC-7**, **AC-8**, **AC-13**, **AC-14**, **AC-18**
4. Form shell and Vehicle section: `RepairFormPage` on `useForm` with `onTouched` and focus on the first error, the header and reporter line, the four section cards, the Vehicle section (vehicle, driver, garage, odometer) with its skeletons, list errors and under repair warning. Satisfies **AC-1** to **AC-7**, **AC-14**, **AC-15**
5. Issues section: rebuild `IssueLoggingSection` on `useFieldArray` (add with focus, remove, counter, 10 cap). Satisfies **AC-8**
6. Priority and assignment, and Billing: priority toggle, the mechanic adder with chips (rebuilding `MechanicAssignmentSection`), repair shop with Other, account type toggle and corporation. Satisfies **AC-9** to **AC-12**, **AC-15**
7. Submit flow: the action bar (fixed below 1024px, inline above), the summary `ResponsiveDialog`, the create call, success toast and `replace` navigation, the failure alert with refetch and "no longer available" errors, the in flight lock and the list failure block. Satisfies **AC-15** to **AC-21**
8. Leave guard: `useBlocker` in function form on the dirty, submitted and saving refs, the once only discard `confirm()` with proceed or reset, closing the summary first, and `beforeunload`. Satisfies **AC-21**, **AC-23**
9. Sweep: remove the old form code, legacy classes and inline styles; run lint, typecheck and build; check `/repairs/new` at 375px and 1280px in Playwright with axe (form and open dialog) and walk the leave guard once. Satisfies **AC-24**, **AC-25**

## Consequences

**Positive**:
- No more "Vehicle not found" or "In house mechanic not found" errors from typos; the form only offers what the server accepts.
- Mistakes show next to their field, and nothing lands on a ticket because of a hidden default.
- The form works with one thumb on a phone, and the summary catches the wrong vehicle before it is marked under repair.
- The data router and the extended `Combobox` are ready for the next forms (user management, lookup lists).

**Negative / tradeoffs**:
- Admin still fills in priority, account type, corporation and repair shop, and the server still throws them away. The form looks finished while four of its fields do nothing until feature 18 stores them.
- Repair shop is now a required pick for a value nobody stores, which adds a tap for no effect today.
- Vehicle system and root cause still reach the server only as text glued onto the issue description, so reports can't filter by them.
- Moving to a data router touches the app's entry point; a missed router assumption would break every page, not just this one.
- Per field list failures mean more states to build and verify than one page error.
- "Has open work" is a yes or no hint, not WL-201's open ticket count.
- Removing the localStorage list drops driver names typed on this device that never reached the server (only names from failed creates).

**Neutral**:
- The backend's `repairNumber` generator becomes the only source of repair numbers.
- The page uses the existing toast context, as the detail page does.

## Follow-up

- [ ] Feature 18 (WL-201, WL-202): store priority, account type, corporation and repair shop on the ticket (a migration); add the issue type picker and the "description optional with a common issue" rule; show open ticket counts instead of the yes or no badge; list in house shops first; create as Assigned or Open once feature 16 names the statuses; auto fill vehicle details (model, type, last repair date, odometer) and the mechanic from the login. This form's layout is the base it builds on.
- [ ] Feature 40 (WL-203): swap `getRepairFormOptions()` to Admin managed lists, and store vehicle system and root cause as fields instead of text in the description.
- [ ] Decide whether a second open ticket on an `UNDER_REPAIR` vehicle should be blocked by the server (feature 18 or 16). Today it is only a warning.
- [ ] `react-hook-form` and `ask-sonner` are installed skills that `AGENTS.md` does not list yet; `/sync` should add them to the root `## Agent skills`.
- [ ] `welinc-web-vrms/AGENTS.md` should note the data router (`createBrowserRouter` with a splat route) so later work uses `useBlocker` and data router APIs knowingly.
