# VRMS design direction

Art direction for `welinc-web-vrms` and `welinc-web-portal`. Based on the WeLinc One UI standard (Google Drive), with its contradictions resolved toward what reads best. Token **values** live in each app's CSS (`src/index.css`); this file says what they mean and how to use them.

## Character

Calm, dense, trustworthy. An operations tool used on a garage floor and in an office, by people who are not tech savvy. It should feel like a well made clipboard, not a startup landing page.

- **Clarity over decoration.** Every screen answers "what needs my attention?" first.
- **Phone first for mechanics.** Mechanic screens are designed at 375px wide first, admin screens at 1280px first. Both must work at both sizes.
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
| `destructive` | `#c0392b` red | Delete, cancel ticket, overdue, critical. Never decorative. |
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

**Contrast rules.** `muted-foreground` on `muted` fails AA (4.34:1), so text on a muted surface uses `muted-strong`. Gold (`highlight`) is never text on a light surface. Tailwind's default palette is switched off, so only these tokens exist as color classes, and lint fails on hex, `rgb()`, palette classes and bracketed values.

Why these: the One UI palette's `#060C3C` and `#910000` are so dark they read as black and maroon, and the doc's own components already use `#1a1f6e`, `#c0392b` and `#e8b800`. Those are also what VRMS uses today. The palette's darker navy survives as the sidebar color.

Retire the stray colors in the current code (`#3b82f6` blue, `#8b5cf6` purple, `#f59e0b`, `#ef4444`, `#dc2626`): each maps to one of the tokens above.

### Ticket status colors

Every status badge pairs color with its text label (never color alone). Rounded full pill, uppercase `text-xs font-medium`, soft tinted background with darker text.

| Status | Style (tokens) |
|---|---|
| Pending | amber tint, amber 800 text (`status-pending-bg` / `-fg`) |
| In Progress | navy tint, `primary` text (`status-in-progress-bg` / `-fg`) |
| For Verification | violet tint, violet 800 text (`status-for-verification-bg` / `-fg`; the one allowed extra hue: it marks "needs Admin") |
| Completed | emerald tint, emerald 800 text (`status-completed-bg` / `-fg`) |
| Cancelled | slate tint, slate 600 text (`status-cancelled-bg` / `-fg`, also used for any unknown value) |

Priority: Critical uses `destructive`, High uses `highlight`, Medium and Low use `secondary` with `muted-strong` text.

### Role colors

Role badges use the same pill as status, always with the role name.

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
- **Scale:** only `text-xs` (12), `text-sm` (14, default body), `text-base` (16), `text-xl` (20), `text-2xl` (24). Nothing below 12px. On phones, form inputs use `text-base` so iOS doesn't zoom.
- **Weights:** `font-semibold` for titles and KPI values, `font-medium` for labels and buttons, `font-normal` for body.
- **Casing:** sentence case for page titles, buttons and body. UPPERCASE with `tracking-wide` only for small labels: table headers, form labels, KPI captions. (One UI asks for all caps titles; that hurts readability for the users we have, so we keep caps to small labels.)
- **Numbers:** money, durations, counts and IDs use `tabular-nums`. Currency: `₱2,033,059.00`. Dates: `YYYY-MM-DD`, times 24 hour.

## Shape and spacing

- 4px grid only, no arbitrary values (`p-[18px]` is banned).
- Radius: `rounded-lg` (8px) for buttons, inputs, cards, menus. `rounded-xl` only for modals and the login card. `rounded-full` for badges and avatars.
- Card padding `p-5` desktop, `p-4` phone. Grid gap `gap-4`. Section spacing `mb-6`.
- Depth comes from borders, not shadows. `shadow-xs` at most on cards (Tailwind v4 name; v3 called it `shadow-sm`); `shadow-lg` only for modals, sheets and dropdown menus.
- Touch targets at least 44px tall on mechanic screens (`h-11`). Desktop buttons `h-9` or `h-10`.

## Layout and navigation

- Collapsible sidebar on desktop: `w-64` expanded, `w-16` icon only with tooltips, `sidebar` background, active item gets a gold left bar plus white text. One nesting level at most.
- On phones the sidebar becomes a bottom tab bar (max 5 items) for mechanics, and a sheet menu for Admin.
- Page header: title, one line of context, primary action on the right (full width at the bottom on phones).

## Components

Use shadcn/ui components (via the shadcn MCP and skill), themed with the tokens above. Don't hand roll what shadcn ships.

- **Tables:** light header (`bg-muted`, uppercase `text-xs` `muted-strong`), `divide-y` rows, `hover:bg-muted/50` only on clickable rows, actions in a `⋮` menu (View, Edit, Delete in red). Text wraps, no horizontal scroll on desktop. On phones, tables turn into stacked cards. (One UI's solid navy header is dropped: it shouts louder than the data.)
- **Forms:** label above input, required marker, helper or error text below in `text-xs`. Errors use `destructive` for the border and message, plus an icon. Submit buttons disable while saving and show a spinner.
- **Modals** for create and edit; **alert dialogs** for destructive confirmations; **sheets** on phones.
- **KPI cards:** caption (uppercase `text-xs`), value (`text-2xl font-semibold tabular-nums`), one line of context. One icon in a soft tinted square, no gradients.
- **Toasts** via sonner, `aria-live` polite (assertive for errors). Top center below 768px, bottom right from 768px up, at most 3 visible.
- **Confirm prompts** through `confirm()`, an alert dialog centered at every size.

## Browser support

Safari 16.4+, Chrome 111+, Firefox 128+ (Tailwind v4's floor). That rules out about iPhone 7 and older, and Android 6 and older. Older browsers get no fallback. The app is light only; there is no dark mode.

## Every screen has four states

Loading (skeletons shaped like the content, not spinners), empty (icon, one sentence, the action that fills it), error (what happened plus retry), and success. Mechanics on weak connections see the loading state most, so design it first.

## Accessibility (WCAG 2.1 AA)

- Text contrast 4.5:1. Gold is never used for text on white; it is a fill with dark text, or paired with an icon.
- Visible focus ring everywhere: 2px `primary` outline with offset.
- Every icon only button has an `aria-label`. Every input has a label.
- Respect `prefers-reduced-motion`. Motion is limited to 150 to 200ms fades and slides.

## Banned

Gradients, glassmorphism, glows, purple/indigo "AI" styling, cards inside cards, emoji in UI, heavy shadows on data cards, decorative color, centered paragraphs of body text, and anything that only works with a mouse.

## Icons

lucide-react only. 16px inline, 20px default, 24px in buttons on phones. `text-muted-foreground` by default; status icons take their status color.
