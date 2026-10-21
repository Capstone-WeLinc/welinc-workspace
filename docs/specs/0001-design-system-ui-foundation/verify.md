# Verify: design system and UI foundation · spec 0001 · updated 2026-10-22
_Steps derived from spec 0001 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Run the app locally (`npm run dev` in `welinc-web-vrms`) and open `/dev/ui`. The Docker container on port 8001 has stale `node_modules`, so use a local Vite server. If the session timeout warning opens, press "I'm still here" first.

## Milestone 3: forms and data display

### UI / manual
- [ ] At 1280px, press "Save ticket" on the empty sample form → every required field shows a red border, an error icon and its message in small text below; focus moves to "Plate number" → AC-11
- [ ] Inspect "Plate number" after that submit → `aria-invalid="true"`, and `aria-describedby` points at both its helper text and its error text → AC-11
- [ ] Fill the form validly and press "Save ticket" → the button shows a spinner and is disabled for about 1.5 seconds, then a success toast appears and the form resets → AC-11
- [ ] At 375px, measure the sample inputs, the combobox and the select → each is 44px tall with 16px text (no iOS zoom) → AC-11, AC-15
- [ ] Each required label shows a red asterisk, and a screen reader hears "(required)" → AC-11
- [ ] Data display section: every status, priority and role value shows its label in sentence case, rendered uppercase; `ON_HOLD`, `URGENT` and `AUDITOR` render gray with their raw text → AC-13
- [ ] Data table at 1280px, state "Ready": a table with no horizontal scroll, costs right aligned, rows highlight on hover; the read only table below does not highlight on hover → AC-12
- [ ] Press "Next" → skeleton rows replace the old rows, then "Page 2 of 6" shows tickets 00523 onward; "Previous" is disabled on page 1, "Next" on page 6 → AC-12
- [ ] Type 6 into "Go to page" → page 6 loads; typing 7 is ignored (the upper limit is `Math.ceil(47 / 8)` = 6) → AC-12
- [ ] Switch state to "Error" → the rows are hidden and an ErrorState shows; "Try again" shows skeletons, then the rows → AC-12
- [ ] Switch state to "Empty" → EmptyState with "New ticket", and no pagination → AC-12
- [ ] Open a row's ⋮ menu → View, Edit, and Delete in red; opening the menu does not open the row → AC-12
- [ ] At 375px the same table renders as stacked cards: ticket as the title, vehicle under it, the status badge top right beside a 44px ⋮ button, the other columns as a label and value list; cards fit with no horizontal scroll → AC-12
- [ ] Tap a card anywhere except the ⋮ → it opens (info toast); tap the ⋮ → only the menu opens → AC-12
- [ ] Keyboard at 1280px: Tab to a table row → a navy focus ring; Enter → the row opens; Tab to ⋮, Enter opens the menu, Esc closes it, and focus returns to ⋮ with a visible ring → AC-15
- [ ] Inject axe (`/node_modules/axe-core/axe.min.js`) and run `axe.run()` at 375px and at 1280px, with the form both empty and submitted invalid, and the table in each of its four states → zero serious or critical violations. Wait about half a second after a state switch, since a button mid color transition can report a false contrast failure → AC-15, AC-16
- [ ] Open `/repairs` → the status pills use the new badge and "Go to page" has a visible label; no console errors → AC-1, AC-4

### Value sourcing
- [ ] StatusBadge: render `status="PENDING_VERIFICATION"` and a made up value → "Pending verification" in pending colors, and the made up value in gray with its raw text → AC-13
- [ ] PriorityBadge: `MEDIUM` and `LOW` share the secondary background with `muted-strong` text → AC-13
- [ ] RoleBadge: sign in as an admin and as a mechanic, and render the user's role from `authStore` → navy Admin, green Mechanic → AC-13
- [ ] DataTable layout: resize across 768px → the table becomes cards at 767px and back at 768px (`useIsMobile`) → AC-12
- [ ] DataTable data: pass `total` 0 → no pagination; pass `total` 47 with `pageSize` 8 → last page 6 → AC-12
- [ ] Field error text: change a zod message in `FormsSection.tsx` → the new text shows inline → AC-11

### Commands
- [ ] `npm run lint` in `welinc-web-vrms` → 0 errors → AC-3
- [ ] `npm run build` → passes, and `dist/assets` has no `dev-ui` chunk → AC-1, AC-14

### Acceptance criteria coverage (milestone 3)
- AC-11: form submit, aria wiring, save spinner, 44px inputs, required marker, zod message
- AC-12: table, pagination, go to page limit, error and empty states, menu, phone cards, breakpoint, total
- AC-13: badge rows, unknown values, role from authStore
- AC-15: keyboard pass, axe at both widths
- AC-16: axe color contrast at both widths

## Milestone 4: enforcement sweep

### UI / manual
- [ ] Walk `/dashboard`, `/repairs`, a repair detail, `/repairs/new`, `/history`, `/profile`, `/users`, `/audit-logs`, `/analytics` and `/knowledge-base` at 1280px → each loads with no console errors, the same content and actions, and no horizontal scroll → AC-1, AC-4
- [ ] Same walk at 375px → no console errors. Some pages scroll sideways (repairs, history, users, analytics, profile, detail, dashboard), and they did so before this milestone too, with identical widths; the UI refresh (features 8 to 15) fixes that → AC-1
- [ ] Knowledge base: category badges (Engine, Electrical, Brakes, Transmission, Suspension) are tinted, not colorless; open "Read SOP" → the navy header text is readable, the modal fits the viewport, the body scrolls and the footer stays visible → AC-2, AC-4
- [ ] Knowledge base: create or delete an SOP → its own toast shows a solid green (success) or red (error) fill → AC-2
- [ ] Dashboard: the pipeline cards and export rows keep their soft tinted icon squares → AC-4
- [ ] Repair detail with "Run AI Triage": severity and confidence chips and the info boxes keep their soft tints → AC-4
- [ ] Session warning: in the console set `window.__WELINC_INACTIVITY_LIMIT__ = 30` and `localStorage.welinc_last_active = Date.now() - 22000` → the dark overlay shows a gold icon, ring and "I'm still here" button; pressing it closes the warning → AC-2
- [ ] Open `design.md` → gold is `highlight`, `accent` is the gray hover, `input` is slate 500, `muted-strong` and its rule, role colors, toast placement and the browser floor are all present → AC-17

### Value sourcing
- [ ] Render any color: in DevTools, change `--highlight` on `:root` → every gold fill on the knowledge base, session warning and sidebar marker follows, proving no hardcoded gold remains → AC-2
- [ ] Palette reset: in DevTools add class `text-amber-500` to any element → it gets no color (the class does not exist) → AC-2

### Commands
- [ ] `npm run lint` in `welinc-web-vrms` → 0 errors with the token rules applied to all of `src` → AC-3
- [ ] `printf 'export function X() { return <div className="text-amber-500 p-[18px]" style={{ color: "#fff" }} /> }\n' | npx eslint --stdin --stdin-filename src/features/repair/pages/Probe.tsx` → 3 errors (unknown class, arbitrary value, raw color) → AC-3
- [ ] `grep -rnE "#[0-9a-fA-F]{3,8}\b|rgba?\(" src --include=*.ts --include=*.tsx` → no matches → AC-3
- [ ] `npm run typecheck` and `npm run build` → pass; `dist/assets` has no `dev-ui` chunk → AC-1, AC-14

### Acceptance criteria coverage (milestone 4)
- AC-1: page walk at both widths, typecheck, build
- AC-2: palette reset check, token driven gold, toast and badge fills
- AC-3: lint on all of `src`, probe file, grep for raw colors
- AC-4: tints and legacy pages render the same
- AC-17: design.md review
