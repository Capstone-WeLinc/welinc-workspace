# 0016. Design direction refresh: the Control room look for the suite

**Date**: 2026-11-18
**Status**: Accepted
**Scope row**: suite S18 (`docs/scope/_root/shared-services.md`)
**Amended**: 2026-11-23, AC-12 option B: the signing out soon banner replaces spec 0003's idle dialog in web-vrms, and the portal gets it too (AC-12a, AC-12b, build plan step 4a; welinc-auth joins the repos; contract 0001 additive) · 2026-11-23, AC-12b: Admin with an empty store calls `/auth/sso` once at mount, since `/auth/admin/me` carries no cutoffs (found during the build) · 2026-11-23, AC-12b failures: the banner shows under the offline banner on a network failure and right away on a plain server error · 2026-11-23, fonts: Inter for text as on staging, Plex Mono stays for numbers and codes (AC-1, AC-3, AC-18, *Typography*, the `Fonts10` row, build plan step 2a)
**Repos**: workspace (`design.md`, `docs/context/vrms/design.md`, `scripts/check-design-tokens.mjs`), `welinc-web-portal`, `welinc-web-vrms`, `welinc-auth` (AC-12a only)
**Design source**: the canvas "WeLinc design directions" (https://claude.ai/artifact/VFhLSMNhfpAFD4D4c2VQzp), page "Round 8". The final boards are listed under *Board index*; older boards are history, not the source.

## Summary

The screens look plain and AI made because today's `design.md` asks for exactly the default shadcn look. This spec replaces it with direction B, "Control room": Inter for text and IBM Plex Mono for numbers and codes, a slightly darker canvas with white layered cards, navy as the working colour, and gold kept rare so that it always means "this needs you". It also fixes the shared parts every screen uses: buttons, fields, switches, toasts, banners, KPI cards, role chips, the sidebar and a new floating save bar. Both the portal and web-vrms get the new look on every page, but **nothing is built until you say go**.

## Requirements

**User stories**:
- As an admin, I want screens that look made for WeLinc, not like any template, so that the defense panel and the staff trust the product.
- As a mechanic on a phone, I want numbers, plates and codes I can read at a glance and buttons I can hit with a thumb, so that I can work a ticket on the garage floor.
- As a developer, I want one written standard with tokens and base components that a check can enforce, so that a new page comes out right without a design round.

**Acceptance criteria**:
- **AC-1**: The suite `design.md` is rewritten from the *Standard definition* below, with the sections Character, Signature, Color tokens, Typography, Shape and surfaces, Motion, Layout and navigation, Components, Feedback, Every screen has four states, Accessibility, Browser support, Banned, Brand surfaces (portal only), Icons. It no longer contains the tinted icon square KPI rule, the role color table, the gold left bar on the current page, or `shadow-xs` on cards, and its token table has no history notes. `docs/context/vrms/design.md` drops every rule that repeated the old suite values (it keeps ticket status colors, priority badges, plate chip, naming a ticket, list rows, detail order, inside ticket cards, and gains the VRMS "hot" list).
- **AC-2**: Both apps' `src/index.css` define every token in the `design.md` color token table with the same value. `node scripts/check-design-tokens.mjs` exits 0. It exits 1 and names the token and the file when a value differs, when a token is missing from an app, or when an app defines it twice (rules in *Token check*).
- **AC-3** (amended 2026-11-23): Both apps load Inter (`@fontsource-variable/inter`, latin and latin-ext only, through `src/fonts.css`) for text and IBM Plex Mono (`@fontsource/ibm-plex-mono`, weights 500 and 600, latin and latin-ext) for numbers and codes, with `font-display: swap`, and no other web font. `₱` renders in Inter in text and in Plex Mono in a number. `@fontsource-variable/ibm-plex-sans` is removed. No request goes to `fonts.googleapis.com` or `fonts.gstatic.com`.
- **AC-4**: The type utilities in the *Typography* table exist (`text-label` and `text-title` as `@utility` blocks, the rest as `--text-*` theme values), the old `text-xs` to `text-2xl` are mapped as listed and banned in lint. Every page title uses `text-title`. Every standalone count, cost, ID, plate, date, time and duration renders in `font-mono` (numbers inside a sentence stay in the sans).
- **AC-5**: Classes follow the *Radius map*: cards `rounded-2xl` with `shadow-card` and a transparent 1px border, buttons and inputs `rounded-lg`, chips `rounded-md`, save bar, toasts, banners and popovers `rounded-xl`, dialogs and sheets `rounded-3xl`, plate chip `rounded-sm`. No card carries `shadow-xs`, `shadow-sm`, `shadow-md`, `shadow-lg` or a visible border class.
- **AC-6**: `Button` has the variants `default` (navy), `outline`, `ghost`, `destructive` (quiet, red text), `link` and `commit` (gold, only on a navy surface) and the sizes in the *Buttons* table, with the hover, disabled and loading styles there. Every button on a field role screen uses a `touch` size. A button shrinks to 96% for 100ms on press.
- **AC-7**: Inputs, selects, textareas and comboboxes show focus as a 2px navy border (padding reduced by 1px so nothing moves) with no ring outside the box. Buttons, links, switches, tabs and checkboxes keep a 2px keyboard ring with a 2px offset on keyboard focus only: navy on light surfaces, white on navy surfaces. An invalid field has a red border (2px when focused) and a message under it with an icon. Disabled and read only fields follow the *Fields* table. A required field has a red `*` right after its label, and a form with required fields says once, above the first field, "Fields with * are required".
- **AC-8**: `SegmentedControl` (replacing `toggle-group`) shows the selected option as a white pill with a 1px `rgba(15,20,69,.12)` ring and a soft shadow on a `track` track, with `primary` text at 600; unselected options are `muted-strong` at 500. Tabs show the selected tab with `foreground` text and a 2px navy underline, unselected tabs `muted-strong`. A `ChoiceChip` inside a form (such as a priority picker) shows its selected value as solid navy with white text, unselected as white with an `input` border.
- **AC-9**: `Switch` is 44 by 26px with a white 20px knob: on is a navy track, off is a `muted` track whose 1px `input` border gives the 3:1 edge. On field role screens its hit area is 44px tall. It never uses gold.
- **AC-10**: `index.css` defines the motion tokens in the *Motion* table. With `prefers-reduced-motion: reduce`, every enter and exit becomes a fade of the same length with no movement or scale, and the switch knob, the press and the toast time bar change instantly.
- **AC-11**: Toasts are our own `Toast` component rendered through sonner's `toast.custom`, as in *Feedback*: 380px wide, light card, a round status icon, a title, an optional one line body, an optional action and a close button. Success and info last 5 seconds with a thin time bar that pauses on hover; warnings last 8 seconds; errors stay until closed. At most 3 show (when full, the oldest non error goes first, then the oldest error), bottom right from 768px up and top center below it. Success, info and warning use `role="status"`, errors `role="alert"`.
- **AC-12**: A `Banner` floating card (*Feedback*) exists for offline, back online and signing out soon, in both apps. Opening a page you can't use sends you to your home page with a banner that names the page and why ("You were sent to your dashboard. That link was for Analytics, which Mechanics can't open."). In web-vrms the signing out soon banner replaces spec 0003's idle warning dialog (AC-23 there is amended to point here): 120 s before the cutoff it knows, the app checks `GET /vrms/session/status`; a later server cutoff reschedules quietly, otherwise the banner shows a countdown and **Stay signed in** (an activity ping, then a status check). While the banner shows, every activity ping (real input sends one at most once a minute, as AC-22 there) is followed by one status check; the banner closes on Stay signed in or when a check finds the cutoff moved. Input alone never closes it. When the cutoff is the 12 hour end (or Stay signed in finds the cutoff didn't move), the banner says the limit can't be extended, shows the time, and has no action; that switch changes the text without announcing it again. Right before leaving at the cutoff, the app checks status one last time and leaves only when the server agrees (or the check fails and the cutoff has passed), so work in another tab or system is never cut off by a stale timer. It leaves even while a higher priority banner (offline) shows. At the cutoff the tab goes to `<portal>/login?reason=idle` or `?reason=maxage`, as before. The dialog and its focus rules are removed.
  - **Screen readers (both apps):** the banner never takes focus. The ticking time is `aria-hidden`; the announced text says the minutes left once ("Signing out in 2 minutes") and again at 30 seconds. **Stay signed in** is the banner's first focusable control.
- **AC-12a** (added 2026-11-23): The portal knows its session's cutoffs. welinc-auth adds three required fields to the launcher answer: `sessionExpiresAt` (the earlier of the idle and the 12 hour cutoff), `sessionAbsoluteExpiresAt` (the 12 hour cutoff) and `serverTime` (the server's clock when it answered), all ISO times. The launcher builder takes the session as well as the person (`answerFor(user, session)` in `launcher.ts`), so every route that answers it carries them: `GET /auth/sso`, `POST /auth/login` (from the session it just created) and `POST /auth/login/verify-email` (the only code step route that answers it); a suite admin's empty answer carries them too. Mobile login and `/auth/authorize/resume` don't answer the launcher body and are unchanged. `docs/openapi.json` is regenerated and the portal's `LauncherAnswer` type gains the three fields. While there is real input (key, click, touch, wheel; never pointer moves or background checks), the portal sends `POST /auth/session/activity` with the SSO cookie: on the first input, then at most once a minute per tab, as `api.post('/auth/session/activity', {})` (a JSON body, or the CSRF guard answers 403). 204 is fine; 401 `SESSION_ENDED` goes to `/login?reason=idle`; 429 and network errors are ignored with no retry. Without this, someone working only in Admin is signed out at 30 minutes while they work.
- **AC-12b** (added 2026-11-23): The portal shows the same signing out soon banner as web-vrms, only inside the signed in launcher and Admin (never on `/login` or its `reason=` screens). One in memory store holds the latest cutoffs and the clock gap (`serverTime` minus the browser's time when the answer arrived); every launcher answer writes it. Admin's own mount check (`GET /auth/admin/me`) carries no cutoffs, so when Admin mounts with the store empty (a reload, a bookmark or a pasted link; coming from the launcher keeps the store), it calls `GET /auth/sso` once, alongside `/auth/admin/me`, and writes that answer like any other; its failures follow the rules below. 120 s before the cutoff (on the server's clock), it calls `GET /auth/sso` again (never activity); a later cutoff reschedules quietly. **Stay signed in** sends the activity ping, then checks again. The 12 hour case, the closing rules, the last check before leaving, the offline case and the screen reader rules match AC-12. When a check fails: 401 `SESSION_ENDED` goes to `/login?reason=idle` (or `maxage` when the held cutoff was the 12 hour end) at once; 403 `NO_SYSTEM_ACCESS` goes to `/login` with its existing message; any other failure keeps the held cutoff and retries at 5, 15 and 30 s (after `Retry-After` on a 429), skipping retries past the cutoff, and the banner shows as follows: on a network failure (the request got no answer) it shows under the offline banner, which stays on top; on a plain server error (any answer that isn't 401 or 403) it shows right away, with no offline banner. Several portal tabs agree through the existing `welinc-session` BroadcastChannel: a tab posts fresh cutoffs and a Stay signed in click, and the others reschedule or close their banner; an idle or 12 hour end posts its `reason` so every portal tab leaves to the same page.
- **AC-13**: A `SaveBar` follows *Saving and drafts*: 640px, centered on the content area, 24px above the bottom (on phones the full width minus 16px each side, 16px above the tab bar plus the safe area), with the change list, Discard, Review and save, the draft kept and restored, and the browser's prompt on close or reload.
- **AC-14**: A `StatCard` (K15) shows an uppercase caption, a large mono number, a gold "Needs you" tag beside the number when it is hot, and one context line. The whole card is one link to the list behind the number, already filtered. It has no icon. web-vrms's dashboard KPIs use it.
- **AC-15**: Roles show as one neutral `RoleChip` (*Components*) whatever the role; a built in role is filled and a custom role outlined where the screen needs to tell them apart. Roles in lists get a square `InitialsTile`, people a round one. The `role-*` tokens and classes are gone from both apps.
- **AC-16**: The web-vrms sidebar and the portal's `AdminShell` sidebar follow *Layout and navigation*, including the collapse. Which sections and pages each role sees is feature 70's job, not this spec's.
- **AC-17**: Lint in both apps still fails on hex, `rgb()`, palette classes and bracketed values outside `index.css`, and now also fails on `role-*` classes, `shadow-xs`, `shadow-sm`, `shadow-md`, `shadow-lg`, `text-xs` to `text-2xl`, and the names `ease-snappy` and `ease-drawer`.
- **AC-18**: Every page in both apps is on the new look. A search of both `src` folders finds no `IBM Plex Sans`, no `role-` color class, no banned shadow or text size class, no `ease-snappy` or `ease-drawer`, and no KPI card with a tinted icon square. Each page reads well at 375px and 1280px.
- **AC-19**: Every text token pair marked "text" in the token table meets 4.5:1 on each surface it is allowed on, and control edges meet 3:1. One axe scan through Playwright at `/check verify` (portal People and Roles, web-vrms dashboard, repair list and ticket detail) shows no color contrast violations, and a keyboard pass on the same pages shows a visible focus ring on every control.
- **AC-20**: The portal keeps its two brand surfaces (*Brand surfaces*): the login and forgot password hero, and the navy launcher band with the grid texture. Only their fonts change.
- **AC-21**: In both apps `npm run lint`, `npm run typecheck` and `npm run build:local` pass, and the existing test suites pass.

## Decision

**Chosen option**: Option 1: Rewrite the standard in place on the current stack (shadcn, Tailwind v4, the token lint), then sweep every page.

Direction B "Control room" becomes the suite standard, written into `design.md`, enforced by the existing token lint plus a token check script, and rolled out to every page of the portal and web-vrms when you say go.

**Implementation skills**: `tailwind-4-docs` (`.claude/skills/tailwind-4-docs/`) · `shadcn` (`.claude/skills/shadcn/`) · `ask-sonner` (`.claude/skills/ask-sonner/`) · `vercel-composition-patterns` (`.claude/skills/vercel-composition-patterns/`)

## Standard definition

### Character

Calm and dense stays. What's new: a working tool with a point of view. Strong titles, numbers that read like a printed job card, white cards that sit on the page instead of being drawn on it, and one rare accent color that always means something.

### Signature (what makes a screen read as WeLinc)

1. **Navy save bar with a gold commit.** Changes to something that exists are batched, reviewed and saved from one floating navy bar.
2. **Mono for numbers and codes.** Standalone counts, costs, IDs, plates, dates, times and durations are in Plex Mono.
3. **Gold means "needs you".** Gold appears only on: hot counts (sidebar bubbles and the StatCard "Needs you" tag), the draft bubble, the logo, the `commit` button, a moved item's landing flash, and the portal's navy band (eyebrow text and the accent square, *Brand surfaces*). Never as decoration, never as text on a light surface.
4. **Plate chip and initials tiles.** Trucks are named by their plate chip, roles by a square initials tile, people by a round one.

**Hot**, defined once: a count of items that wait on the viewer's own role to act. Each system lists its hot counts in its own design file. VRMS: tickets waiting for sign off (Admin, Chief mechanic), tickets sent back to me (Mechanic), fix library suggestions to review (roles that can edit the fix library). A count of 0 is never hot. The **draft bubble** is a gold count of unsaved changes on a list row (for example a role row in S20).

### Color tokens

The table below becomes the token table in `design.md` (without the "Use" history). "text" marks a token used for text; it must meet 4.5:1 on every surface named.

| Token | Value | Use |
|---|---|---|
| `background` | `#f3f5f9` | Page canvas (was `#f8fafc`) |
| `foreground` | `#0f172a` | Body text (text) |
| `card` | `#ffffff` | Cards, tables, dialogs |
| `card-foreground` | `#0f172a` | Text on cards (text) |
| `popover` | `#ffffff` | Menus, popovers |
| `popover-foreground` | `#0f172a` | Text in menus (text) |
| `primary` | `#1a1f6e` | Primary buttons, links, selected form choices, switch on, focus ring on light (text on white) |
| `primary-foreground` | `#ffffff` | Text on primary (text) |
| `primary-hover` | `#151b4f` | Hover and press of primary |
| `secondary` | `#f1f5f9` | Secondary fills |
| `secondary-foreground` | `#0f172a` | Text on secondary (text) |
| `accent` | `#eef1f6` | Hover of menu items, ghost buttons and clickable rows on white (was `#f1f5f9`) |
| `accent-foreground` | `#0f172a` | Text on accent (text) |
| `highlight` | `#e8b800` | Gold, under the Signature rule only |
| `highlight-foreground` | `#0f1445` | Text and icons on gold (text; was `#0f172a`) |
| `commit-hover` | `#d4a800` | Hover and press of `commit` (replaces the portal's `highlight-hover`) |
| `muted` | `#f1f5f9` | Muted surfaces on white, switch off track, skeletons on white |
| `track` | `#e6e9f2` | Segmented control tracks, meters, skeletons on the canvas |
| `table-head` | `#f6f7fb` | Table header row |
| `divider` | `#eef1f6` | Lines between rows inside a card |
| `muted-foreground` | `#5b6779` | Secondary text on white, canvas, `table-head`, `info-bg` (text; was `#64748b`, which fails on the new canvas) |
| `muted-strong` | `#475569` | Labels, table headers, unselected options (text) |
| `border` | `#e2e8f0` | Outlines of outline buttons and chips |
| `input` | `#64748b` | Borders of inputs, checkboxes and the off switch (3:1 on white) |
| `ring` | `#1a1f6e` | Keyboard ring on light surfaces |
| `ring-on-dark` | `#ffffff` | Keyboard ring on navy surfaces (sidebar, save bar, primary buttons) |
| `destructive` | `#b42318` | Delete, cancel, overdue, critical (text; was `#c0392b`) |
| `destructive-foreground` | `#ffffff` | Text on destructive (text) |
| `success` | `#067647` | Success text and icons (text) |
| `success-bg` | `#ecfdf3` | Success tint |
| `success-fill` | `#10b981` | Success fills with dark text (charts, progress) |
| `success-fill-foreground` | `#0f172a` | Text on success fill (text) |
| `error` | `#b42318` | Error text, icons and field borders (text) |
| `error-bg` | `#fef3f2` | Error tint |
| `warning` | `#93370d` | Warning text and icons (text; no longer gold) |
| `warning-bg` | `#fffaeb` | Warning tint |
| `info-bg` | `#eef0f8` | Navy tint: info icon tiles, role chips, initials tiles |
| `draft-row` | `#fffbeb` | A row with an unsaved change |
| `draft-tag` | `#fdf3cc` | The "Not saved" tag |
| `draft-tag-foreground` | `#7a5b00` | Text on the "Not saved" tag (text) |
| `sidebar` | `#0f1445` | Sidebar, save bar, navy surfaces |
| `sidebar-foreground` | `#ffffff` | Current page and titles on navy (text) |
| `sidebar-idle` | `rgba(255,255,255,0.72)` | Idle page names and icons (text) |
| `sidebar-label` | `rgba(255,255,255,0.55)` | Section labels (text, 5.9:1) |
| `sidebar-hover` | `rgba(255,255,255,0.08)` | Hover fill |
| `sidebar-current` | `rgba(255,255,255,0.13)` | Current page fill |
| `sidebar-line` | `rgba(255,255,255,0.08)` | Line between sections |
| `sidebar-count` | `rgba(255,255,255,0.12)` | A count bubble that isn't hot |
| `white` | `#ffffff` | Literal white |

**Kept outside the table** (each system's own file): `chart-1` to `chart-5`, `status-*`, priority tokens, and VRMS's `warning-text`.
**Removed**: every `role-*` token, `sidebar-primary`, `--radius`, `--warning` as an alias of gold, and the VRMS legacy aliases (`--accent-strong`, `--danger`, `--success-soft` and the rest of that block); their uses move to the tokens above. The portal gains `--sidebar` and its siblings, and renames `highlight-hover` to `commit-hover`; its `hero*` tokens stay as brand tokens (*Brand surfaces*).

**Token check** (`scripts/check-design-tokens.mjs`): it reads only the color token table in `design.md`, one token per row, the token from column 1 and the value from column 2 (both in backticks). Values compare in lower case with spaces removed. For each app it finds `--<token>:` in `:root` of `src/index.css`. It fails when a value differs, a token is missing, a token is defined twice, or a table row doesn't parse, and it names the token, the file and both values. Tokens in an app but not in the table are allowed (system tokens).

### Typography

- **Fonts:** Inter for everything (variable, 400 to 700) and IBM Plex Mono 500 and 600 for numbers and codes, self hosted through fontsource with the latin and latin-ext subsets (the peso sign is in latin-ext), `font-display: swap`. No font features are switched on, so text looks as it does on staging. No preload: Vite renames the font files at build time, and `swap` with self hosting is enough. `--font-sans: 'Inter Variable', system-ui, sans-serif`; `--font-mono: 'IBM Plex Mono', ui-monospace, monospace`.
- **Scale:**

| Utility | Size / line height | Weight | Use |
|---|---|---|---|
| `text-display` | 32 / 1.1 | 700 | Portal greeting, a dashboard hello. Nowhere else. |
| `text-title` (`@utility`) | 28 / 1.15, 24 below 768px | 700 | Page titles |
| `text-heading` | 20 / 1.3 | 600 | Section titles |
| `text-subheading` | 18 / 1.35 | 600 | Card titles |
| `text-group` | 16 / 1.4 | 600 | Group headers inside a card |
| `text-body` | 14 / 1.5 | 400 (500 for row names) | Body, the default |
| `text-small` | 13 / 1.45 | 400 | Context lines, helper text |
| `text-caption` | 12 / 1.4 | 500 | Metadata, pills |
| `text-label` (`@utility`) | 11 / 1.3, uppercase, tracking 0.07em | 600 | Table headers, form labels, KPI captions, sidebar section labels, save bar group headers |

- **Old scale mapping** (then banned in lint): `text-xs` → `text-caption`, `text-sm` → `text-body`, `text-base` → `text-group` or `text-body` on phone inputs (16px stays on phone inputs so iOS doesn't zoom: use `text-base-input`, 16 / 1.5), `text-lg` → `text-subheading`, `text-xl` → `text-heading`, `text-2xl` → `text-title`. shadcn components get the same mapping when restyled.
- Titles use tracking `-0.01em`. Weights: 700 titles, 600 headings, labels and buttons, 500 row names and pills, 400 body. Mono uses 500 by default, 600 for StatCard numbers and plate chips.
- Nothing is smaller than 12px except `text-label` (caps read as large as 12px lowercase).
- Sentence case everywhere except `text-label`.
- Numbers: mono already has fixed width digits; numbers in sans in a table column use `tabular-nums`. Formats stay: `₱2,033,059.00`, `YYYY-MM-DD`, 24 hour times. Relative words ("today", "2 days late") may sit beside a date, never replace it in a table.

### Shape and surfaces

- **Radius map** (the `--radius` base is removed; each step is its own token): `--radius-sm` 4px → `rounded-sm` (plate chip only), `--radius-md` 8px → `rounded-md` (chips, role chips, menu items, tooltips, buttons inside the save bar), `--radius-lg` 10px → `rounded-lg` (buttons, inputs, selects, comboboxes), `--radius-xl` 12px → `rounded-xl` (save bar, toasts, banners, popovers, dropdown menus), `--radius-2xl` 14px → `rounded-2xl` (cards, tables), `--radius-3xl` 16px → `rounded-3xl` (dialogs, sheets). Pills, avatars and round initials tiles are `rounded-full`. Every existing `rounded-*` use is mapped to this table in the sweep, never left to change size silently.
- **Shadows:** `shadow-card` `0 0 0 1px rgba(15,20,69,.07), 0 1px 3px rgba(15,20,69,.06)` (cards and tables: the ring is the edge; a `border border-transparent` sits under it so the edge survives Windows high contrast); `shadow-pop` `0 0 0 1px rgba(15,20,69,.08), 0 12px 32px rgba(15,20,69,.18)` (menus, popovers, toasts, banners); `shadow-bar` `0 18px 44px rgba(15,20,69,.32)` (save bar); `shadow-dialog` `0 0 0 1px rgba(15,20,69,.08), 0 24px 60px rgba(15,20,69,.24)` (dialogs, sheets). The Tailwind `shadow-xs` to `shadow-lg` utilities are banned.
- 4px grid only. Card padding 20px desktop, 16px phone; grid gap 16px; section spacing 24px. Repeated items inside a card are split by `divider` lines, never a box each. A card never holds a card; a table is a card of its own, not inside one.
- Skeletons are `muted` on white and `track` on the canvas.
- Touch targets at least 44px on field role screens.

### Motion

| Token | Value | Use |
|---|---|---|
| `--ease-enter` | `cubic-bezier(0.2, 0.8, 0.2, 1)` | Everything that enters or moves into place |
| `--ease-exit` | `cubic-bezier(0.4, 0, 1, 1)` | Everything that leaves |
| `--duration-press` | 100ms | Button press, scale 0.96 |
| `--duration-menu` | 140ms | Menus and popovers: fade plus scale from 0.98, from their trigger |
| `--duration-tab` | 150ms | Tab content: fade plus 4px rise |
| `--duration-fold` | 180ms | A group opens or closes (height plus fade); a switch knob moves |
| `--duration-dialog-in` | 180ms | Scrim fades, dialog fades and rises 8px |
| `--duration-dialog-out` | 120ms | Dialog and scrim fade out |
| `--duration-toast` | 200ms | Toasts fade and rise 8px, 80ms apart |
| `--duration-bar` | 200ms | The save bar fades and rises 16px, 120ms after a switch that caused it (no delay after a text edit) |
| `--duration-sheet` | 220ms | Side sheet slides in from the right |
| `--duration-land` | 1200ms | Landing flash fades out |

- Exits that have no token of their own take two thirds of the enter time with `--ease-exit` (menu 90ms, toast 130ms, bar 130ms, sheet 150ms).
- The landing flash is a `highlight` background at 20% on a row that just moved or was just created, fading to none.
- Reduced motion: every enter and exit is a fade of the same length; the switch knob, the press and the toast time bar change instantly.
- shadcn's `tw-animate-css` slide and zoom classes in dialogs, sheets, menus and accordions are rewritten to these tokens in Build plan step 3. Until then `ease-snappy` and `ease-drawer` stay as aliases of `--ease-enter`; step 3 removes them.

### Layout and navigation

- **Sidebar:** `sidebar` navy, 240px, the system switcher at the top and the account menu at the bottom. Every page has a lucide icon. Section labels (`text-label`, `sidebar-label`) don't fold; a 1px `sidebar-line` separates sections. Idle pages use `sidebar-idle`, hover `sidebar-hover`, the current page `sidebar-current` with `sidebar-foreground` semibold text; no gold edge, no dot. Only a page with pages under it opens and closes. Counts are small mono bubbles, `sidebar-count`, gold with navy text only when hot.
- **Collapse:** a toggle at the bottom collapses the sidebar to a 64px icon strip with a tooltip on each icon; the state is saved per user in `localStorage` (`welinc:sidebar:<user id>`). Collapsed: section labels hide, lines stay, the system switcher and account menu show only their icons, count bubbles become 8px dots (gold when hot), and clicking a page that has pages under it expands the sidebar and opens it. No flyouts.
- **Phones:** a bottom tab bar for roles with at most 5 items, a sheet otherwise.
- **Page header** (`PageHeader`): breadcrumb in `text-small` `muted-foreground`, title in `text-title`, one context line in `text-small`, the primary action on the right (full width at the bottom on phones).
- **App shell:** where a page has a list pane beside a detail (Roles, People), the sidebar, the list and the detail each scroll on their own.
- **Layers**, bottom to top: page, sidebar, save bar (z 30), toasts (z 40), banner (z 50), sheet (z 60), dialog (z 70).

### Components

- **Buttons:**

| Size | Height | Use |
|---|---|---|
| `sm` | 36px | Inside dense rows and the save bar list |
| `default` | 40px | Office screens |
| `touch` | 44px | Every field role screen |
| `icon` / `icon-touch` | 40 / 44px square | Icon only buttons |

| Variant | Rest | Hover | Disabled |
|---|---|---|---|
| `default` | `primary` fill, white text | `primary-hover` | 50% opacity, no pointer |
| `outline` | white, 1px `border`, `foreground` text | `accent` fill | 50% opacity |
| `ghost` | no fill, `foreground` text | `accent` fill | 50% opacity |
| `destructive` | no fill, `destructive` text | `error-bg` fill | 50% opacity |
| `commit` | `highlight` fill, `highlight-foreground` text, on navy only | `commit-hover` | 50% opacity |
| `link` | `primary` text | underline | 50% opacity |

Loading keeps the width, shows a spinner before the label, and disables the button. A submit button reads "Saving…" while it works. Destructive actions next to a primary action are `destructive` buttons or sit in the `⋮` menu.

- **Fields:**

| State | Look |
|---|---|
| Rest | White, 1px `input` border, `rounded-lg`, 40px tall on desktop, 44px on phones, placeholder `muted-foreground` |
| Focus | 2px `primary` border, padding reduced by 1px, no outer ring |
| Invalid | 1px `error` border (2px on focus), message in `text-small` `error` with an icon below |
| Disabled | `muted` fill, `muted-foreground` text, no pointer |
| Read only | No border, `muted` fill, normal text, still selectable |

Labels sit above in `text-label` `muted-strong`. Checkboxes and radios are 18px with an `input` border and a navy fill when checked. The OTP field uses the input rules per cell. Comboboxes and selects use the input rules plus a `shadow-pop` menu.

- **SegmentedControl, ChoiceChip, Tabs, Switch:** AC-8 and AC-9. SegmentedControl is 40px tall (34px pills inside a 4px track padding), a `role="group"` of buttons with `aria-pressed`, and scrolls sideways on phones if it overflows.
- **Tables:** `table-head` header row with `text-label` in `muted-strong`, `divider` rows, `accent` hover only on clickable rows, actions in a `⋮` menu. On phones, rows become stacked cards. An empty column hides; an empty cell shows "—".
- **Status pills:** `rounded-full`, `text-caption` 500, sentence case, a soft tint with darker text and a `ring-inset` of the text color at 20%, always with the label (never color alone). Each system owns its colors.
- **StatCard (KPI):** AC-14, on `shadow-card`, 20px padding. The number is `font-mono` 32px 600. The period comes from the page's filter, never written on the card.
- **RoleChip:** `info-bg` fill (built in) or white with a 1px `border` (custom), `primary` text, `text-caption` 600, `rounded-md`, 24px tall. **InitialsTile:** 28px in lists, 40px in headers, `info-bg` fill, `primary` text, two letters at 600; square `rounded-md` for roles, round for people. Color never encodes a role.
- **PlateChip:** as in VRMS's file (mono 600 uppercase, `foreground` on `card`, 1px `input` border, `rounded-sm`, 24px tall). The portal gets the same component when it shows trucks.
- **Meter:** a 6px `track` bar with a `primary` fill (gold when hot), with the count beside it in mono (`11/16`).
- **Dialogs** for create and edit, **alert dialogs** for destructive confirmations (centered at every size), **sheets** on phones. An action that would orphan data is blocked with the reason and the way out, instead of being confirmed.

### Saving and drafts

- Two ways to save, never mixed on one screen: the `SaveBar` for changing what exists (roles, settings, modules, thresholds), then a review dialog; a Save button that reads "Saving…" for making something new. Nothing saves itself field by field.
- **SaveBar:** `sidebar` navy, `rounded-xl`, `shadow-bar`, 640px wide, centered on the scroll container that holds the edited content (the detail pane in the app shell), 24px above its bottom. On phones: full width minus 16px each side, 16px above the tab bar and `env(safe-area-inset-bottom)`. A page that can show the bar gets 96px of bottom padding so the bar never covers the last row. It appears on the first change and leaves when the changes are saved or discarded.
- Contents: a summary button ("N unsaved changes", sub line from the caller, cut with an ellipsis), a line, Discard (`outline` on navy, 40% white border), Review and save (`commit`). Discard needs no confirm: the change list shows what goes, and the draft is gone at once.
- **Change list:** opens above the bar at the same width, `rounded-xl`, `shadow-pop`, at most 320px tall then scrolls. A header "Changes to [name]" with a quiet mono "+2 −1", changes grouped like the page under `text-label` group names, each row a 26px `+` or `−` tile, the item name, "~~From~~ → To" in `text-caption`, and a labelled Undo. At the bottom, the people it touches (faces plus one line). No Undo all: Discard does that.
- The review dialog's contents, the saving state, a save failure and a conflict with someone else's save belong to the spec of the screen that uses the bar (S20 for roles).
- **Drafts:** leaving the page with changes stores them in `localStorage` under `welinc:draft:<user id>:<screen id>` with the time and the "from" values, and shows the toast "Your N changes to [name] are kept for when you come back". Coming back restores them with the bar sub line "Kept from [time]". Restoring drops the whole draft, with a toast, when any stored "from" no longer matches the server. Drafts expire after 7 days. Signing out clears all of that user's drafts. Discard and a successful save clear the draft. Closing or reloading the tab gets the browser's own prompt.
- **Draft marks:** a row with an unsaved change uses `draft-row` and a "Not saved" tag (`draft-tag`); a list row that holds a draft shows the gold draft bubble.

### Feedback

- **Toasts:** our `Toast` component through sonner's `toast.custom` (sonner keeps the stacking and swipe; the component owns the look, the time bar and the role). 380px wide (full width minus 16px on phones), `rounded-xl`, `shadow-pop`, 12px padding, a 24px round icon on its status tint, title in `text-body` 600, body in `text-small` `muted-foreground`, an action as an `outline` `sm` button. Position from a `(min-width: 768px)` media query. While a save bar shows, toasts sit 88px higher. Timing, the limit of 3 and roles: AC-11.
- **Banners:** a floating card, top center of the content area, at most 560px wide (full width minus 16px on phones), `rounded-xl`, `shadow-pop`, a 28px status icon tile, title, one line and an optional action, `role="status"`. One shows at a time by priority: offline, then signing out soon (the one exception: a signing out soon banner raised by a network failed check in the portal shows under the offline banner, AC-12b), then the no access note, then back online; a lower one waits until a higher one ends. On phones the banner sits above the toasts.
  - Offline: shows when the browser reports offline or a request fails with a network error or two 5xx answers in a row; it stays until a request succeeds. Then "Back online" shows for 4 seconds.
  - Signing out soon: shows 2 minutes before the session ends, with a countdown and "Stay signed in" (an activity ping, then a fresh look at the cutoff); it closes on that click or once the cutoff has moved. At the 12 hour end it has no action and says the limit can't be extended. It is the only warning: no dialog opens (AC-12, AC-12b).
  - No access note: closes after 8 seconds or on its close button. The page name, the plural role name and the home page name travel in router state (`state.noAccess`), set by the existing route guard.
- **No match:** an icon tile, "No one matches "…"", one hint, and the active filters as removable chips with Clear all.
- **Wording:** a change is "Added" or "Removed"; access with no end shows "No end date", time boxed access "Until [date]".

### Every screen has four states

Unchanged: loading (skeletons shaped like the content), empty (icon, one sentence, the action that fills it), error (what happened plus retry), success. Design the loading state first.

### Accessibility (WCAG 2.1 AA)

Text 4.5:1, control edges and state indicators 3:1. Gold is never text on a light surface. The keyboard ring follows AC-7. Every icon only button has an `aria-label`, every input a label. Reduced motion follows *Motion*.

### Browser support

Safari 16.4+, Chrome 111+, Firefox 128+ (Tailwind v4's floor). Light only, no dark mode.

### Banned

Gradients, glassmorphism, glows, purple "AI" styling, cards inside cards, emoji in UI, decorative color, a colored edge on the current page, color that encodes a role, KPI icons in tinted squares, centered paragraphs of body text, anything that only works with a mouse. Exceptions: *Brand surfaces*.

### Brand surfaces (portal only)

Unchanged from today apart from fonts: the login and forgot password hero (`AuthHero.tsx`, its navy split layout with the gradient overlay and soft gold glows); and the launcher's navy band (`hero` tokens, the gold `LogoMark`, the 32px `brand-grid` texture fading downward, the first cards overlapping the band by 48px, a gold `text-label` eyebrow, the greeting in `text-display`, the subtitle in white at 70%). A launcher card's lead icon may be a solid `primary` square with a gold icon to mark a brand item (the Admin card); system cards keep a soft tinted square. Working pages (Admin) use the plain app shell.

### Icons

lucide-react only. 16px inline, 20px default, 24px in buttons on phones. `muted-foreground` by default; status icons take their status color.

### Board index (the design source)

| Board (page "Round 8" unless noted) | Settles |
|---|---|
| `ControlRoom` (page "Rounds 1 to 7") | The direction: surfaces, navy, gold |
| `Sidebars8` | Sidebar |
| `SaveBar9`, `SaveWidths10` (640px) | Save bar and its change list |
| `Picks8` | Review, leaving with a draft, the two ways to save |
| `Roles9`, `DraftMarks` (B), `People8` | The app shell with list and detail panes (built in S20, S21, S19) |
| `Labels10` (L3) | Uppercase labels stay on table headers, form labels and captions |
| `Kpis13` (K15, whole card a link) | StatCard |
| `Fonts10` (F1) | IBM Plex Sans and Plex Mono (text overridden to Inter on 2026-11-23; Plex Mono kept) |
| `Selected10` (A) | Selected state, Signature |
| `Toasts6` (TA), `States6` (BB, NC), `Fields6` (FA, OB, SD), `Motion6` | Feedback, fields, motion |

**Canonical pattern** (a page composes base components; every look decision lives in the tokens and `src/components/ui/`):
```tsx
<PageHeader crumb="Repairs" title="Repair tickets" context="12 open across 3 garages">
  <Button>New ticket</Button>
</PageHeader>
<div className="grid gap-4 md:grid-cols-4">
  <StatCard caption="Waiting for sign off" value={3} hot context="Oldest waiting 2 days"
    href="/repairs?status=FOR_VERIFICATION" />
</div>
<Card>{/* shadow-card, rounded-2xl, p-4 md:p-5: from the component, never the page */}
  <Table>…<PlateChip plate="NDG 5821" /> <span className="font-mono text-caption">REP-20261030-5EBC</span>…</Table>
</Card>
// Wrong: <div className="rounded-lg border shadow-xs"> · <span className="bg-role-admin-bg"> · ease-snappy · text-sm · a hex value
```

**Replaces**:
- The current suite `design.md` (Inter only, titles capped at 24px, slate canvas with hairline borders, `shadow-xs` cards, KPI icon in a tinted square, role color table, gold left bar on the current page, a 2px ring outside every focused field, solid navy for every selected option).
- The look parts of VRMS spec 0001's token set (its token machinery, palette switch off and lint stay).
- `ease-snappy`, `ease-drawer`, `toggle-group`'s selected style, and the Tailwind `text-xs` to `text-2xl` and `shadow-xs` to `shadow-lg` utilities.

**Enforcement**:
- The existing token lint in both `eslint.config.js`, extended by AC-17.
- `scripts/check-design-tokens.mjs` (AC-2), run before every PR that touches either `index.css` or `design.md`.
- The base components in `src/components/ui/` are the only place the styles live; pages compose them. Each app keeps its own copy of the components (no shared package), so a change to one is made to both in the same session.

**Rollout**: one sweep of every page in both apps, in the order of the *Build plan*, **started only when you say go**. Until then the current look stays.

**Exceptions**: *Brand surfaces*. VMMS and BMS adopt the standard only if their groups choose to.

## Value sourcing

| Action | Value produced or displayed | Source |
|---|---|---|
| Token check | Expected token values | The color token table in `design.md`, columns 1 and 2 |
| Token check | Actual values | `--<token>:` lines in `:root` of each app's `src/index.css` |
| StatCard | Number, caption, context line | Props from the page (VRMS dashboard: its existing KPI data) |
| StatCard | Link target | Prop `href` from the page: the list route plus the card's filter plus the dashboard's current filters |
| StatCard, sidebar bubble | Hot or not | The system's hot list (VRMS: `docs/context/vrms/design.md`) applied to the viewer's role; the count from existing endpoints |
| Draft bubble | Count | Number of changes in that row's stored draft |
| SaveBar | "N unsaved changes" | Length of the caller's change list |
| SaveBar | Sub line ("Chief mechanic · affects 8 people") | Prop from the caller (S20 supplies the role and its people count) |
| SaveBar | Change list rows | Caller's change list: group, label, from, to, undo handler |
| SaveBar draft | Stored changes, "from" values, "Kept from [time]" | `localStorage` key `welinc:draft:<user id>:<screen id>`; the user id from the existing session |
| Sidebar collapse | Collapsed or not | `localStorage` key `welinc:sidebar:<user id>` |
| Toast | Time left bar | Fixed: 5000ms success and info, 8000ms warning, none for errors |
| No access banner | Page name, plural role name, home page name | Router state `noAccess`, set by the existing route guard from the route's label and the viewer's role |
| Offline banner | Offline or not | Browser `online` and `offline` events plus the shared API client's failed request count |
| Signing out banner, web-vrms | Cutoff, and whether it is the 12 hour end | `GET /vrms/session/status`; before that, `sessionExpiresAt` and `sessionAbsoluteExpiresAt` from the last refresh (spec 0003's value sourcing) |
| Signing out banner, portal | Cutoff, and whether it is the 12 hour end | `sessionExpiresAt` and `sessionAbsoluteExpiresAt` of the latest launcher answer (`/auth/sso`, the login answer or the code step answer; on Admin with an empty store, one `/auth/sso` call at mount), read again 120 s before the cutoff; welinc-auth computes the first as `/auth/session` does (`sessionExpiresAt()` in `session.service.ts`) and the second from the session's `absoluteExpiresAt`; the 12 hour end when the two are within 1 s |
| Portal clock gap | Offset to the server's clock | `serverTime` of the latest launcher answer minus the browser's `Date.now()` when it arrived |
| Signing out banner, portal | Time left | The cutoff minus (the browser's clock plus the clock gap), counted each second |
| Signing out banner, web-vrms | Time left | The cutoff minus the browser's clock (as spec 0003 today; skew is covered by the last status check) |
| Leaving at the cutoff | Whether to leave | One last check (`/vrms/session/status`, or `/auth/sso` in the portal): leave on 401 or when the returned cutoff has passed, or on a failed check once the held cutoff has passed |
| Portal activity ping | When to send | Real input events, at most once a minute (as spec 0003 AC-22) |

## Build plan

Nothing here starts until you say go. Tracer Bullet: the first slice proves the whole chain (written standard, tokens, fonts, check, one component) on one page in each app before the rest.

1. Rewrite `design.md` and trim `docs/context/vrms/design.md` (adding the VRMS hot list); add `scripts/check-design-tokens.mjs` (workspace PR), satisfies **AC-1**, **AC-2**
2. Tracer slice in both apps: swap Inter for Plex Sans and Plex Mono, set the color, radius, shadow, type and motion tokens in `index.css` (old ease names kept as aliases), restyle `Button` and `Card`, check the portal's People page and the VRMS dashboard at 375px and 1280px, run the token check, satisfies **AC-2**, **AC-3**, **AC-4**, **AC-5**, **AC-6**, **AC-10** (text font superseded by 2a)
2a. Fonts back to Inter (added 2026-11-23, before the page sweep): in each app run `npm uninstall @fontsource-variable/ibm-plex-sans && npm i @fontsource-variable/inter@^5.3.0` (commits `package-lock.json`), then rebuild its frontend container with `--build -V` (the portal in `docker-compose.shared.yml`, web-vrms in `docker-compose.vrms.yml`). Point the two `@font-face` rules in `src/fonts.css` at `inter-latin-wght-normal.woff2` and `inter-latin-ext-wght-normal.woff2` with family `'Inter Variable'`, keeping the unicode ranges and `font-weight: 100 700`, set `--font-sans` as in *Typography*, and keep the four Plex Mono imports in `main.tsx`. Not a `git revert` of portal `05ace1c` or web-vrms `fd156e0`: those also brought in Plex Mono. In the workspace, change `design.md`'s *Fonts* line (89) to match *Typography*; its Signature line on Plex Mono stays. Satisfies **AC-1**, **AC-3**
3. Fields, checkbox, combobox, OTP, `Switch`, `SegmentedControl` (from `toggle-group`), `ChoiceChip`, `Tabs`, `Dialog`, `Sheet`, `DropdownMenu`, `Popover`, `Tooltip`, `Table`, `Badge` (status pills) in both apps; rewrite their animations to the motion tokens and remove the old ease aliases, satisfies **AC-5**, **AC-7**, **AC-8**, **AC-9**, **AC-10**
4. Feedback: the `Toast` component through sonner, `Banner` with its priority and offline signal, the no access redirect note, the signing out banner, satisfies **AC-11**, **AC-12**
4a. Signing out soon everywhere (added 2026-11-23): welinc-auth adds the two cutoffs to the launcher answer (contract 0001, additive, `npm run openapi`, a branch and PR into `development`); web-vrms swaps the idle dialog for the banner and removes the dialog; the portal adds the activity pinger, the cutoff check and the banner. Satisfies **AC-12**, **AC-12a**, **AC-12b**
5. New components: `PageHeader`, `StatCard`, `Meter`, `RoleChip`, `InitialsTile`, `PlateChip` (portal), `SaveBar` with its draft hook and leave prompt; replace the role badges and the VRMS dashboard KPIs, satisfies **AC-13**, **AC-14**, **AC-15**
6. Sidebar restyle and collapse in web-vrms and the portal's `AdminShell` (feature 70 then changes sections and pages on top), satisfies **AC-16**
7. Lint additions in both apps, satisfies **AC-17**
8. Page sweep: every portal page, then every web-vrms page, at 375px and 1280px, mapping every `rounded-*` and old text size; search for the removed patterns; recheck the letter spacing of `text-display`, `text-title` and `text-label` with Inter (those values were tuned for Plex), satisfies **AC-18**, **AC-20**
9. Contrast check of the token table, axe and keyboard pass at verify, then lint, typecheck, `build:local` and tests in both apps, satisfies **AC-19**, **AC-21**

## Consequences

**Positive**:
- Screens stop looking like the shadcn starter; the four Signature rules give every new page a WeLinc look without a design round.
- One token table with a check keeps the portal and web-vrms from drifting.
- Gold gains meaning, so attention goes where work waits.

**Negative / tradeoffs**:
- A sweep of every page in two apps is a lot of UI churn close to the defenses, and it lands only when you call it. Until then new work is built on the old look and gets swept again.
- Inter for text keeps today's widths, so tables wrap as they do on staging. Plex Mono runs wider than Inter, so mono columns (costs, plates, IDs) still need a look at 1280px in the page sweep.
- Inter is the most used UI font, so the "any app" risk the board round named comes back for text; the mono numbers, the surfaces and the Signature carry the look instead.
- Keeping uppercase labels (L3) keeps one of the old "template" tells; Plex Mono and the new surfaces carry the change instead.
- The token check parses a markdown table: a badly formatted row in `design.md` fails the check (by design), not the apps.
- Components live as two copies (portal and web-vrms) with no drift check of their own; only the tokens are checked.
- AC-12 moves session behavior into a look spec: one quiet banner replaces a blocking dialog, so someone who ignores it is signed out without having pressed anything (the same end as an unanswered dialog). VMMS and BMS keep their copy of the dialog until their groups adopt this standard; both are valid under spec 0003's amended AC-23.
- The portal now pings activity like every system, so Admin work keeps the shared session alive. One more caller of `/auth/session/activity` (2 a minute per `sid`, extras ignored).
- Tests that assert old class names (`rounded-lg`, `shadow-xs`, `text-sm`, role badge classes) need updating.

**Neutral**:
- VRMS spec 0001 stays the record of the token machinery; its look values are superseded by this spec.
- S19, S20, S21 and feature 70 build their pages on this standard; their page layouts live in their own specs.

## Follow-up

- [ ] Say go before any build starts (the scope row records that it waits for you).
- [ ] The VRMS dashboard period and garage filter (picked on `Kpis13`) belongs to the dashboard's own feature; give the PM a ticket line for it.
- [ ] A "planned update" banner needs a source (a setting or an announcement endpoint); left out until one exists.
- [ ] After the sweep, offer `web-design-guidelines` and `impeccable` (critique only) on the portal Roles page and the VRMS dashboard.
- [ ] Recheck the switch once S20 is built: S1 (plain knob) matches every approved board; S3 (a check or cross in the knob) stays the fallback if testers miss the off state.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
