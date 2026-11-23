# WeLinc design direction

Art direction for the WeLinc suite's web apps and the shared portal: direction B, "Control room" (suite spec 0016). Token values live in each app's `src/index.css` and must match the color token table below; `node scripts/check-design-tokens.mjs` checks that.

Each system adds rules for its own screens in `docs/context/<system>/design.md` (VRMS: [docs/context/vrms/design.md](docs/context/vrms/design.md)). Today `welinc-web-vrms` and `welinc-web-portal` follow this file; VMMS and BMS adopt it only if their groups choose to.

## Character

Calm and dense, a working tool with a point of view. Operations tools used in garages, yards and offices, by people who are not tech savvy.

- **Strong titles, numbers that read like a printed job card,** white cards that sit on the page instead of being drawn on it, and one rare accent color that always means something.
- **Clarity over decoration.** Every screen answers "what needs my attention?" first.
- **Phone first for field roles.** Screens for people on the floor (such as mechanics) are designed at 375px wide first, office screens at 1280px first. Both must work at both sizes.
- **One primary action per view.** Make it obvious and big enough to hit with a thumb.

## Signature

What makes a screen read as WeLinc:

1. **Navy save bar with a gold commit.** Changes to something that exists are batched, reviewed and saved from one floating navy bar (*Saving and drafts*).
2. **Mono for numbers and codes.** Standalone counts, costs, IDs, plates, dates, times and durations are in Plex Mono. Numbers inside a sentence stay in the sans.
3. **Gold means "needs you".** Gold appears only on: hot counts (sidebar bubbles and the StatCard "Needs you" tag), the draft bubble, the logo, the `commit` button, a moved item's landing flash, and the portal's navy band (*Brand surfaces*). Never as decoration, never as text on a light surface.
4. **Plate chip and initials tiles.** Trucks are named by their plate chip, roles by a square initials tile, people by a round one.

**Hot**: a count of items that wait on the viewer's own role to act. Each system lists its hot counts in its own design file. A count of 0 is never hot. The **draft bubble** is a gold count of unsaved changes on a list row.

## Color tokens

Components use semantic tokens only (`bg-primary`, `text-muted-foreground`). Never write a hex value in a component. "text" marks a token used for text; it meets 4.5:1 on every surface it is allowed on.

| Token | Value | Use |
|---|---|---|
| `background` | `#f3f5f9` | Page canvas |
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
| `accent` | `#eef1f6` | Hover of menu items, ghost buttons and clickable rows on white |
| `accent-foreground` | `#0f172a` | Text on accent (text) |
| `highlight` | `#e8b800` | Gold, under the Signature rule only |
| `highlight-foreground` | `#0f1445` | Text and icons on gold (text) |
| `commit-hover` | `#d4a800` | Hover and press of `commit` |
| `muted` | `#f1f5f9` | Muted surfaces on white, switch off track, skeletons on white |
| `track` | `#e6e9f2` | Segmented control tracks, meters, skeletons on the canvas |
| `table-head` | `#f6f7fb` | Table header row |
| `divider` | `#eef1f6` | Lines between rows inside a card |
| `muted-foreground` | `#5b6779` | Secondary text on white, canvas, `table-head`, `info-bg` (text) |
| `muted-strong` | `#475569` | Labels, table headers, unselected options (text) |
| `border` | `#e2e8f0` | Outlines of outline buttons and chips |
| `input` | `#64748b` | Borders of inputs, checkboxes and the off switch (3:1 on white) |
| `ring` | `#1a1f6e` | Keyboard ring on light surfaces |
| `ring-on-dark` | `#ffffff` | Keyboard ring on navy surfaces (sidebar, save bar, primary buttons) |
| `destructive` | `#b42318` | Delete, cancel, overdue, critical (text) |
| `destructive-foreground` | `#ffffff` | Text on destructive (text) |
| `success` | `#067647` | Success text and icons (text) |
| `success-bg` | `#ecfdf3` | Success tint |
| `success-fill` | `#10b981` | Success fills with dark text (charts, progress) |
| `success-fill-foreground` | `#0f172a` | Text on success fill (text) |
| `error` | `#b42318` | Error text, icons and field borders (text) |
| `error-bg` | `#fef3f2` | Error tint |
| `warning` | `#93370d` | Warning text and icons (text) |
| `warning-bg` | `#fffaeb` | Warning tint |
| `info-bg` | `#eef0f8` | Navy tint: info icon tiles, role chips, initials tiles |
| `draft-row` | `#fffbeb` | A row with an unsaved change |
| `draft-tag` | `#fdf3cc` | The "Not saved" tag |
| `draft-tag-foreground` | `#7a5b00` | Text on the "Not saved" tag (text) |
| `sidebar` | `#0f1445` | Sidebar, save bar, navy surfaces |
| `sidebar-foreground` | `#ffffff` | Current page and titles on navy (text) |
| `sidebar-idle` | `rgba(255,255,255,0.72)` | Idle page names and icons (text) |
| `sidebar-label` | `rgba(255,255,255,0.55)` | Section labels (text) |
| `sidebar-hover` | `rgba(255,255,255,0.08)` | Hover fill |
| `sidebar-current` | `rgba(255,255,255,0.13)` | Current page fill |
| `sidebar-line` | `rgba(255,255,255,0.08)` | Line between sections |
| `sidebar-count` | `rgba(255,255,255,0.12)` | A count bubble that isn't hot |
| `white` | `#ffffff` | Literal white |

**Kept in each system's own file:** `chart-1` to `chart-5`, `status-*` and priority tokens. Apps that switch off Tailwind's default palette make these tokens the only color classes, and lint fails on hex, `rgb()`, palette classes and bracketed values.

**Status pills:** each system owns its status colors. Keep the same shape everywhere: `rounded-full`, `text-caption` 500, sentence case, a soft tint with darker text and a `ring-inset` of the text color at 20%, always with the label (never color alone), and the same color for a status in pills and charts.

## Typography

- **Fonts:** Inter for everything (variable, 400 to 700) and IBM Plex Mono 500 and 600 for numbers and codes, self hosted through fontsource (`@fontsource-variable/inter`, `@fontsource/ibm-plex-mono`) with the latin and latin-ext subsets (the peso sign is in latin-ext), `font-display: swap`. No Google Fonts call, no font features, no preload. `--font-sans: 'Inter Variable', system-ui, sans-serif`; `--font-mono: 'IBM Plex Mono', ui-monospace, monospace`.
- **Scale:**

| Utility | Size / line height | Weight | Use |
|---|---|---|---|
| `text-display` | 32 / 1.1 | 700 | Portal greeting, a dashboard hello. Nowhere else. |
| `text-title` | 28 / 1.15, 24 below 768px | 700 | Page titles |
| `text-heading` | 20 / 1.3 | 600 | Section titles |
| `text-subheading` | 18 / 1.35 | 600 | Card titles |
| `text-group` | 16 / 1.4 | 600 | Group headers inside a card |
| `text-body` | 14 / 1.5 | 400 (500 for row names) | Body, the default |
| `text-small` | 13 / 1.45 | 400 | Context lines, helper text |
| `text-caption` | 12 / 1.4 | 500 | Metadata, pills |
| `text-label` | 11 / 1.3, uppercase, tracking 0.07em | 600 | Table headers, form labels, KPI captions, sidebar section labels, save bar group headers |
| `text-base-input` | 16 / 1.5 | 400 | Inputs on phones (16px so iOS doesn't zoom) |

- `text-title` and `text-label` are `@utility` blocks (they carry more than a size); the rest are `--text-*` theme values. Titles carry weight and tracking `-0.01em` from the utility.
- **Old sizes** (banned in lint): `text-xs` → `text-caption`, `text-sm` → `text-body`, `text-base` → `text-group` (or `text-base-input` on phone inputs), `text-lg` → `text-subheading`, `text-xl` → `text-heading`, `text-2xl` → `text-title`.
- Weights: 700 titles, 600 headings, labels and buttons, 500 row names and pills, 400 body. Mono uses 500 by default, 600 for StatCard numbers and plate chips.
- Nothing is smaller than 12px except `text-label` (caps read as large as 12px lowercase). Sentence case everywhere except `text-label`.
- **Numbers:** mono already has fixed width digits; numbers in sans in a table column use `tabular-nums`. Currency `₱2,033,059.00`, dates `YYYY-MM-DD`, times 24 hour. Relative words ("today", "2 days late") may sit beside a date, never replace it in a table.

## Shape and surfaces

- **Radius map** (each step is its own token, no `--radius` base):

| Class | Size | Use |
|---|---|---|
| `rounded-sm` | 4px | Plate chip only |
| `rounded-md` | 8px | Chips, role chips, menu items, tooltips, buttons inside the save bar |
| `rounded-lg` | 10px | Buttons, inputs, selects, comboboxes |
| `rounded-xl` | 12px | Save bar, toasts, banners, popovers, dropdown menus |
| `rounded-2xl` | 14px | Cards, tables |
| `rounded-3xl` | 16px | Dialogs, sheets |
| `rounded-full` | | Pills, avatars, round initials tiles |

- **Shadows:**

| Class | Use |
|---|---|
| `shadow-card` | Cards and tables. The 1px ring is the edge; a `border border-transparent` sits under it so the edge survives Windows high contrast. |
| `shadow-pop` | Menus, popovers, toasts, banners |
| `shadow-bar` | Save bar |
| `shadow-dialog` | Dialogs, sheets |

  The Tailwind `shadow-xs` to `shadow-lg` utilities are banned. A card never carries a visible border class.
- 4px grid only, no arbitrary values. Card padding 20px desktop, 16px phone; grid gap 16px; section spacing 24px.
- Repeated items inside a card are split by `divider` lines, never a box each. A card never holds a card; a table is a card of its own, not inside one.
- Skeletons are `muted` on white and `track` on the canvas.
- Touch targets at least 44px on field role screens.

## Motion

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

- Exits without a token of their own take two thirds of the enter time with `--ease-exit` (menu 90ms, toast 130ms, bar 130ms, sheet 150ms).
- The landing flash is a `highlight` background at 20% on a row that just moved or was just created, fading to none.
- **Reduced motion:** every enter and exit is a fade of the same length with no movement or scale; the switch knob, the press and the toast time bar change instantly.
- Don't use `ease-snappy` or `ease-drawer` in new code: they are kept only as aliases of `--ease-enter` until the base components move to the tokens above.

## Layout and navigation

- **Sidebar:** `sidebar` navy, 240px, the system switcher at the top and the account menu at the bottom. Every page has a lucide icon. Section labels (`text-label`, `sidebar-label`) don't fold; a 1px `sidebar-line` separates sections. Idle pages use `sidebar-idle`, hover `sidebar-hover`, the current page `sidebar-current` with `sidebar-foreground` semibold text; no gold edge, no dot. Only a page with pages under it opens and closes. Counts are small mono bubbles in `sidebar-count`, gold with navy text only when hot.
- **Collapse:** a toggle at the bottom collapses the sidebar to a 64px icon strip with a tooltip on each icon; the state is saved per user in `localStorage` (`welinc:sidebar:<user id>`). Collapsed: section labels hide, lines stay, the system switcher and account menu show only their icons, count bubbles become 8px dots (gold when hot), and clicking a page that has pages under it expands the sidebar and opens it. No flyouts.
- **Phones:** a bottom tab bar for roles with at most 5 items, a sheet otherwise.
- **Page header** (`PageHeader`): breadcrumb in `text-small` `muted-foreground`, title in `text-title`, one context line in `text-small`, the primary action on the right (full width at the bottom on phones).
- **App shell:** where a page has a list pane beside a detail, the sidebar, the list and the detail each scroll on their own.
- **Layers**, bottom to top: page, sidebar, save bar (z 30), toasts (z 40), banner (z 50), sheet (z 60), dialog (z 70).

## Components

Use shadcn/ui components, restyled with the tokens above. Every look decision lives in the tokens and `src/components/ui/`; pages compose them. Each app keeps its own copy of the components, so a change to one is made to both in the same session.

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

  A button shrinks to 96% for `--duration-press` on press. Loading keeps the width, shows a spinner before the label, and disables the button. A submit button reads "Saving…" while it works. Destructive actions next to a primary action are `destructive` buttons or sit in the `⋮` menu; never two filled buttons side by side where one destroys.

- **Fields:**

| State | Look |
|---|---|
| Rest | White, 1px `input` border, `rounded-lg`, 40px tall on desktop, 44px on phones, placeholder `muted-foreground` |
| Focus | 2px `primary` border, padding reduced by 1px, no outer ring |
| Invalid | 1px `error` border (2px on focus), message in `text-small` `error` with an icon below |
| Disabled | `muted` fill, `muted-foreground` text, no pointer |
| Read only | No border, `muted` fill, normal text, still selectable |

  Labels sit above in `text-label` `muted-strong`. A required field has a red `*` right after its label, and a form with required fields says once, above the first field, "Fields with * are required". Checkboxes and radios are 18px with an `input` border and a navy fill when checked. The OTP field uses the input rules per cell. Comboboxes and selects use the input rules plus a `shadow-pop` menu.
- **Keyboard ring:** buttons, links, switches, tabs and checkboxes show a 2px ring with a 2px offset on keyboard focus only (`focus-visible`): `ring` on light surfaces, `ring-on-dark` on navy surfaces. Fields use their border instead (above).
- **SegmentedControl** (replaces `toggle-group`): 40px tall, 34px pills inside a 4px `track` padding, a `role="group"` of buttons with `aria-pressed`. The selected option is a white pill with a 1px `rgba(15,20,69,.12)` ring and a soft shadow, `primary` text at 600; unselected options are `muted-strong` at 500. It scrolls sideways on phones if it overflows.
- **ChoiceChip** (a choice inside a form, such as a priority picker): selected is solid `primary` with white text, unselected white with an `input` border.
- **Tabs:** the selected tab has `foreground` text and a 2px navy underline, unselected tabs `muted-strong`.
- **Switch:** 44 by 26px with a white 20px knob. On is a navy track, off a `muted` track whose 1px `input` border gives the 3:1 edge. On field role screens its hit area is 44px tall. It never uses gold.
- **Tables:** `table-head` header row with `text-label` in `muted-strong`, `divider` rows, `accent` hover only on clickable rows, actions in a `⋮` menu (View, Edit, Delete in red). Text wraps, no horizontal scroll on desktop. On phones, rows become stacked cards. An empty column hides; an empty cell shows "—" in `muted-foreground`.
- **StatCard (KPI):** on `shadow-card`, 20px padding: an uppercase `text-label` caption, a large mono number (32px 600), a gold "Needs you" tag beside the number when it is hot, and one context line. The whole card is one link to the list behind the number, already filtered. No icon. The period comes from the page's filter, never written on the card.
- **RoleChip:** one neutral chip whatever the role. `info-bg` fill (built in) or white with a 1px `border` (custom), `primary` text, `text-caption` 600, `rounded-md`, 24px tall. Color never encodes a role.
- **InitialsTile:** 28px in lists, 40px in headers, `info-bg` fill, `primary` text, two letters at 600; square `rounded-md` for roles, round for people.
- **PlateChip:** mono 600 uppercase, `foreground` on `card`, 1px `input` border, `rounded-sm`, 24px tall (details in VRMS's file). The portal uses the same component when it shows trucks.
- **Meter:** a 6px `track` bar with a `primary` fill (gold when hot), with the count beside it in mono (`11/16`).
- **Dialogs** for create and edit, **alert dialogs** for destructive confirmations (centered at every size), **sheets** on phones. An action that would orphan data is blocked with the reason and the way out, instead of being confirmed.

## Saving and drafts

- Two ways to save, never mixed on one screen: the `SaveBar` for changing what exists (roles, settings, modules, thresholds), then a review dialog; a Save button that reads "Saving…" for making something new. Nothing saves itself field by field.
- **SaveBar:** `sidebar` navy, `rounded-xl`, `shadow-bar`, 640px wide, centered on the scroll container that holds the edited content, 24px above its bottom. On phones: full width minus 16px each side, 16px above the tab bar and `env(safe-area-inset-bottom)`. A page that can show the bar gets 96px of bottom padding. It appears on the first change and leaves when the changes are saved or discarded.
- **Contents:** a summary button ("N unsaved changes", a sub line from the caller, cut with an ellipsis), a line, Discard (`outline` on navy, 40% white border, no confirm), Review and save (`commit`).
- **Change list:** opens above the bar at the same width, `rounded-xl`, `shadow-pop`, at most 320px tall then scrolls. A header "Changes to [name]" with a quiet mono "+2 −1", changes grouped like the page under `text-label` group names, each row a 26px `+` or `−` tile, the item name, "~~From~~ → To" in `text-caption`, and a labelled Undo. At the bottom, the people it touches. No Undo all: Discard does that.
- **Drafts:** leaving the page with changes stores them in `localStorage` under `welinc:draft:<user id>:<screen id>` with the time and the "from" values, and shows the toast "Your N changes to [name] are kept for when you come back". Coming back restores them with the sub line "Kept from [time]". Restoring drops the whole draft, with a toast, when any stored "from" no longer matches the server. Drafts expire after 7 days. Signing out clears all of that user's drafts. Discard and a successful save clear the draft. Closing or reloading the tab gets the browser's own prompt.
- **Draft marks:** a row with an unsaved change uses `draft-row` and a "Not saved" tag (`draft-tag`); a list row that holds a draft shows the gold draft bubble.
- The review dialog, the saving state, a save failure and a conflict belong to the spec of the screen that uses the bar.

## Feedback

- **Toasts:** our `Toast` component through sonner's `toast.custom` (sonner keeps the stacking and swipe; the component owns the look, the time bar and the role). 380px wide (full width minus 16px on phones), `rounded-xl`, `shadow-pop`, 12px padding, a 24px round icon on its status tint, title in `text-body` 600, body in `text-small` `muted-foreground`, an action as an `outline` `sm` button, and a close button. Success and info last 5 seconds with a thin time bar that pauses on hover; warnings 8 seconds; errors stay until closed. At most 3 show (when full, the oldest non error goes first, then the oldest error). Bottom right from 768px up, top center below it; while a save bar shows, toasts sit 88px higher. Success, info and warning use `role="status"`, errors `role="alert"`.
- **Banners:** a floating card, top center of the content area, at most 560px wide (full width minus 16px on phones), `rounded-xl`, `shadow-pop`, a 28px status icon tile, title, one line and an optional action, `role="status"`. One shows at a time by priority: offline, then signing out soon, then the no access note, then back online. On phones the banner sits above the toasts.
  - **Offline:** shows when the browser reports offline, or a request fails with a network error or two 5xx answers in a row; it stays until a request succeeds. Then "Back online" shows for 4 seconds.
  - **Signing out soon:** shows 2 minutes before the session ends, with "Stay signed in" (refreshes the session).
  - **No access note:** opening a page you can't use sends you to your home page with a banner that names the page and why ("You were sent to your dashboard. That link was for Analytics, which Mechanics can't open."). It closes after 8 seconds or on its close button.
- **No match:** an icon tile, "No one matches "…"", one hint, and the active filters as removable chips with Clear all.
- **Wording:** a change is "Added" or "Removed"; access with no end shows "No end date", time boxed access "Until [date]".

## Every screen has four states

Loading (skeletons shaped like the content, not spinners), empty (icon, one sentence, the action that fills it), error (what happened plus retry), and success. People on weak connections see the loading state most, so design it first.

## Accessibility (WCAG 2.1 AA)

- Text 4.5:1, control edges and state indicators 3:1. Gold is never text on a light surface.
- The keyboard ring follows *Components*. Every icon only button has an `aria-label`, every input a label.
- Reduced motion follows *Motion*.

## Browser support

Safari 16.4+, Chrome 111+, Firefox 128+ (Tailwind v4's floor). That rules out about iPhone 7 and older, and Android 6 and older. Older browsers get no fallback. Light only, no dark mode.

## Banned

Gradients, glassmorphism, glows, purple "AI" styling, cards inside cards, emoji in UI, decorative color, a colored edge on the current page, color that encodes a role, KPI icons in tinted squares, centered paragraphs of body text, and anything that only works with a mouse. Exceptions: *Brand surfaces*.

## Brand surfaces (portal only)

The portal is the front door, so it carries the brand; working pages stay calm.

- **Login and forgot password hero** (`AuthHero.tsx`): its navy split layout with the gradient overlay and soft gold glows stays.
- **Launcher band:** `hero` navy tokens, the gold `LogoMark` (the SVG mark alone; never the square `welinc-logo.jpg` at icon size), the 32px `brand-grid` texture fading downward, the first cards overlapping the band by 48px, a gold `text-label` eyebrow (gold text is allowed on navy), the greeting in `text-display`, and the subtitle in white at 70%.
- **Accent icon squares:** a launcher card's lead icon may be a solid `primary` square with a gold icon to mark a brand item (the Admin card); system cards keep a soft tinted square.
- Working pages (Admin) use the plain app shell.

## Icons

lucide-react only. 16px inline, 20px default, 24px in buttons on phones. `muted-foreground` by default; status icons take their status color.
