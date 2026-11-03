# WeLinc design direction

Art direction for the WeLinc suite's web apps and the shared portal. Based on the WeLinc One UI standard (Google Drive), with its contradictions resolved toward what reads best. Token **values** live in each app's CSS (`src/index.css`); this file says what they mean and how to use them.

Each system adds rules for its own screens in `docs/context/<system>/design.md` (VRMS: [docs/context/vrms/design.md](docs/context/vrms/design.md)). Today `welinc-web-vrms` and `welinc-web-portal` follow this file; whether every system adopts it is for the groups to agree.

## Character

Calm, dense, trustworthy. Operations tools used in garages, yards and offices, by people who are not tech savvy. It should feel like a well made clipboard, not a startup landing page.

- **Clarity over decoration.** Every screen answers "what needs my attention?" first.
- **Phone first for field roles.** Screens for people on the floor (such as mechanics) are designed at 375px wide first, office screens at 1280px first. Both must work at both sizes.
- **One primary action per view.** Make it obvious and big enough to hit with a thumb.

## Color tokens

Components use semantic tokens only (`bg-primary`, `text-muted-foreground`, `border-border`). Never write a hex value in a component.

| Token | Value | Use |
|---|---|---|
| `primary` | `#1a1f6e` navy | Primary buttons, active nav, links, focus ring |
| `primary-hover` | `#151b4f` | Hover and pressed state of primary |
| `sidebar` | `#0f1445` deep navy | Sidebar background (darker than primary, so active items stand out) |
| `highlight` | `#e8b800` gold | Active nav marker, highlights, warning fills. Always dark text on it (`highlight-foreground`). |
| `accent` | `#f1f5f9` (slate 100) | shadcn's hover state for menu items and ghost buttons. Not gold. |
| `destructive` | `#c0392b` red | Delete, cancel, overdue, critical. Never decorative. |
| `success` | `#047857` (emerald 700) for text, `success-fill` `#10b981` for fills (dark text on it) | Completed, healthy |
| `foreground` | `#0f172a` (slate 900) | Body text |
| `muted-foreground` | `#64748b` (slate 500) | Secondary text, metadata, on `card` or `background` only |
| `muted-strong` | `#475569` (slate 600) | Secondary text on `muted` surfaces, such as table headers |
| `muted` | `#f1f5f9` (slate 100) | Muted surfaces: table header, skeletons |
| `background` | `#f8fafc` (slate 50) | Page canvas |
| `card` | `#ffffff` | Cards, tables, modals |
| `border` | `#e2e8f0` (slate 200) | Hairline borders and dividers |
| `input` | `#64748b` (slate 500) | Borders of inputs, selects, checkboxes and switches (3:1 against white) |
| `ring` | `#1a1f6e` | Focus ring |

**Contrast rules.** `muted-foreground` on `muted` fails AA (4.34:1), so text on a muted surface uses `muted-strong`. Gold (`highlight`) is never text on a light surface. Apps that switch off Tailwind's default palette make these tokens the only color classes, and lint can then fail on hex, `rgb()`, palette classes and bracketed values (web-vrms does).

Why these: the One UI palette's `#060C3C` and `#910000` are so dark they read as black and maroon, and the doc's own components already use `#1a1f6e`, `#c0392b` and `#e8b800`. The palette's darker navy survives as the sidebar color.

**Status colors** belong to each system, because each has its own statuses. Keep the same shape everywhere: a rounded full pill that pairs color with its text label (never color alone), uppercase `text-xs font-medium`, soft tinted background with darker text, and the same color for a status in badges and charts.

**Selected state of toggles and segmented pickers:** one style everywhere, solid `primary` fill with `primary-foreground` text. Unselected options are `card` with a `border` outline. Never show "selected" with a pale fill, which is invisible on white.

### Role colors

Roles are shared across the suite, so their badges are too. Same pill as status, always with the role name.

| Role | Style (tokens `role-<role>-bg` / `-fg`) |
|---|---|
| Admin | solid navy, white text |
| Chief mechanic | solid gold, dark text |
| Mechanic | emerald tint, emerald 800 text |
| Operations | navy tint, `primary` text |
| Customer support | sky tint, sky 800 text |
| Driver | slate tint, slate 700 text |

## Typography

- **Font:** Inter (self hosted with `@fontsource-variable/inter`, no Google Fonts call), falling back to the system stack.
- **Scale:** only `text-xs` (12), `text-sm` (14, default body), `text-base` (16), `text-lg` (18, card and section headings), `text-xl` (20), `text-2xl` (24). Nothing below 12px. On phones, form inputs use `text-base` so iOS doesn't zoom.
- **Weights:** `font-semibold` for titles and KPI values, `font-medium` for labels and buttons, `font-normal` for body.
- **Casing:** sentence case for page titles, buttons and body. UPPERCASE with `tracking-wide` only for small labels: table headers, form labels, KPI captions. (One UI asks for all caps titles; that hurts readability for these users, so caps stay on small labels.)
- **Numbers:** money, durations, counts and IDs use `tabular-nums`. Currency: `₱2,033,059.00`. Dates: `YYYY-MM-DD`, times 24 hour (`2026-10-30 20:37`). Relative words ("today", "2 days late") may sit beside a date, never replace it in a table.

## Shape and spacing

- 4px grid only, no arbitrary values (`p-[18px]` is banned).
- Radius: `rounded-lg` (8px) for buttons, inputs, cards, menus. `rounded-xl` only for modals and the login card. `rounded-full` for badges and avatars. `rounded-sm` (4px) is kept for a system's own signature chip, so it never looks like a status pill.
- Card padding `p-5` desktop, `p-4` phone. Grid gap `gap-4`. Section spacing `mb-6`.
- Depth comes from borders, not shadows. `shadow-xs` at most on cards (Tailwind v4 name; v3 calls it `shadow-sm`); `shadow-lg` only for modals, sheets and dropdown menus.
- Touch targets at least 44px tall on field role screens (`h-11`). Desktop buttons `h-9` or `h-10`.

## Layout and navigation

- Collapsible sidebar on desktop: `w-64` expanded, `w-16` icon only with tooltips, `sidebar` background, active item gets a gold left bar plus white text. One nesting level at most.
- On phones the sidebar becomes a bottom tab bar when a role has at most 5 items, and a sheet menu otherwise.
- Page header: title, one line of context, primary action on the right (full width at the bottom on phones).

## Components

Use shadcn/ui components, themed with the tokens above. Don't hand roll what shadcn ships.

- **Tables:** light header (`bg-muted`, uppercase `text-xs` `muted-strong`), `divide-y` rows, `hover:bg-muted/50` only on clickable rows, actions in a `⋮` menu (View, Edit, Delete in red). Text wraps, no horizontal scroll on desktop. On phones, tables turn into stacked cards. (One UI's solid navy header is dropped: it shouts louder than the data.)
- **Forms:** label above input, required marker, helper or error text below in `text-xs`. Errors use `destructive` for the border and message, plus an icon. Submit buttons disable while saving and show a spinner.
- **Modals** for create and edit; **alert dialogs** for destructive confirmations; **sheets** on phones.
- **KPI cards:** caption (uppercase `text-xs`), value (`text-2xl font-semibold tabular-nums`), one line of context. One icon in a soft tinted square, no gradients.
- **Toasts** via sonner, `aria-live` polite (assertive for errors). Top center below 768px, bottom right from 768px up, at most 3 visible.
- **Confirm prompts:** an alert dialog centered at every size.
- **Repeated items inside a card:** separate them with `divide-y` or a small heading, never a bordered box per item. A card never contains another card, KPI cards included; KPIs inside a section sit as plain caption and value blocks.
- **Destructive actions next to a primary action:** put them in the `⋮` menu or show them as a quiet `ghost` button with `destructive` text, separated from the primary. Never two filled buttons side by side where one destroys.
- **Empty values:** if a column is empty for every visible row, hide the column. A single empty cell shows "—" in `muted-foreground`. A column always shows what its header says.

## Browser support

Safari 16.4+, Chrome 111+, Firefox 128+ (Tailwind v4's floor). That rules out about iPhone 7 and older, and Android 6 and older. Older browsers get no fallback. Apps are light only; there is no dark mode.

## Every screen has four states

Loading (skeletons shaped like the content, not spinners), empty (icon, one sentence, the action that fills it), error (what happened plus retry), and success. People on weak connections see the loading state most, so design it first.

## Accessibility (WCAG 2.1 AA)

- Text contrast 4.5:1. Gold is never used for text on white; it is a fill with dark text, or paired with an icon.
- Visible focus ring everywhere: 2px `primary` outline with offset.
- Every icon only button has an `aria-label`. Every input has a label.
- Respect `prefers-reduced-motion`. Motion is limited to 150 to 200ms fades and slides.

## Banned

Gradients, glassmorphism, glows, purple/indigo "AI" styling, cards inside cards, emoji in UI, heavy shadows on data cards, decorative color, centered paragraphs of body text, and anything that only works with a mouse.

## Icons

lucide-react only. 16px inline, 20px default, 24px in buttons on phones. `text-muted-foreground` by default; status icons take their status color.
