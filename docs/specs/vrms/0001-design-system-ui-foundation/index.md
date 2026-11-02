# 0001. Design system and UI foundation for web-vrms

**Date**: 2026-10-22
**Status**: Accepted

## Summary

This spec turns `design.md` into real code in `welinc-web-vrms`: one set of color tokens, and one shared kit of components (buttons, fields, dialogs, confirm prompts, toasts, tables, badges, empty and error states) built on shadcn/ui. To get there, the app moves to React 19 and Tailwind v4, the half working dark mode is removed, and a lint rule blocks raw colors and made up sizes everywhere. Old styles keep working, so nothing breaks, and each UI refresh page (features 8 to 15) then only puts these parts together instead of inventing its own.

## Requirements

**User stories**:
- As a mechanic on a phone, I want buttons, fields and popups that are big, clear and readable in bright light, so that I can update a ticket with one thumb.
- As an admin, I want every page, modal and prompt to look and behave the same, so that the app feels trustworthy and I never guess what a button does.
- As a developer building the UI refresh, I want ready made components and tokens, so that each page is assembly, not design.

**Acceptance criteria**:
- **AC-1**: web-vrms runs React 19 and Tailwind v4 (CSS first config through `@tailwindcss/vite`). `tailwind.config.js`, `postcss.config.js` and `autoprefixer` are gone. `npm run lint`, `npm run typecheck` and `npm run build` pass. Login, dashboard, repair list, repair detail, repair form, history, audit log, users, analytics and knowledge base all still load and work as before.
- **AC-2**: `src/index.css` defines every token in the *Token set* below, in hex, with the values shown. Tailwind's default color palette is removed (`--color-*: initial`), so only token colors exist as utilities.
- **AC-3**: `src/**/*.{ts,tsx}` contains no hex or `rgb()` color values, no default palette classes (`text-amber-500`), and no bracketed arbitrary values (`p-[18px]`, `z-[999999]`). Lint reports each of these as an **error** in every file, legacy and new, including shadcn generated files in `ui/` (the builder edits generated code to comply). Tailwind v4's CSS variable syntax (`w-(--radix-popover-trigger-width)`) is not an arbitrary value and is allowed. The only exception is a line with an `eslint-disable-next-line` comment that gives a reason. `index.css` is not linted; it is the one place values live.
- **AC-4**: The colliding legacy variables are renamed at every use (`var(--muted)` becomes `var(--muted-foreground)`, and `var(--accent)` / `var(--accent-soft)` become the `--highlight` tokens). Every other legacy variable and `brand-*` class still resolves through an alias to a canonical token. The legacy classes in `index.css` still render. Pages look the same as before, apart from the intended fixes (input borders, contrast).
- **AC-5**: The app is light only. The Topbar theme toggle is removed, the 9 `.dark` rules are deleted, and `color-scheme: light` is set.
- **AC-6**: Inter is self hosted with `@fontsource-variable/inter`. The browser makes no request to Google Fonts.
- **AC-7**: Every component in the *Component inventory* exists at the listed path, follows `design.md`, and uses only tokens.
- **AC-8**: `confirm({ title, description?, confirmText?, cancelText?, tone? })` returns a promise that resolves to `true` on confirm, and `false` on cancel, Esc, a click outside, or a route change. Focus returns to the element that opened it. A second call while one is open waits in a queue and opens next. A route change (pathname or search) resolves the open confirm **and every queued one** `false`. Calling `confirm()` with no `ConfirmProvider` mounted throws an error naming the missing provider. `ConfirmModal.tsx` is deleted, and its 5 callers use `confirm()`.
- **AC-9**: Toasts use sonner. `useToast().showToast(message, type)` keeps its signature, so the 38 existing call sites work unchanged. `type` maps `success` to `toast.success`, `error` to `toast.error` and `info` to `toast.info`, and the default stays `success`. Toasts appear top center below 768px and bottom right from 768px up, with at most 3 visible. Error toasts are announced assertively (their text is also written to a visually hidden `role="alert"` region, since sonner's own region is polite only), and all others are announced politely. The custom `ToastContext` provider is deleted, and `useToast` no longer throws when there is no provider.
- **AC-10**: `ResponsiveDialog` opens as a centered dialog from 768px up and as a bottom sheet below 768px, with the same props. It traps focus, closes on Esc, and keeps its footer (the primary action) visible while the body scrolls.
- **AC-11**: Forms use react-hook-form, zod and the `Field` component. Each field has its label above, a required marker, and helper or error text below in `text-xs`. An invalid field shows a `destructive` border, an icon and the message, and sets `aria-invalid` and `aria-describedby`. The submit button is disabled and shows a spinner while saving. Inputs use `text-base` below 768px (no iOS zoom).
- **AC-12**: `DataTable` renders a table from 768px up and stacked cards below 768px, from one `columns` definition. It shows skeleton rows while loading, an `EmptyState` when there are no rows, and an `ErrorState` with a working retry on failure. Rows highlight on hover only when `onRowClick` is set. Row actions sit in a `⋮` menu, with destructive items in red. Server pagination includes `GoToPageInput`. There is no horizontal scroll at 1280px, and the cards fit at 375px. Pages are 1 based. The last page is `Math.ceil(total / pageSize)` (minimum 1), and that is also `GoToPageInput`'s upper limit. On a page change the table shows skeleton rows and hides the old rows. Pagination is optional.
- **AC-13**: `StatusBadge`, `PriorityBadge` and `RoleBadge` follow the *Badge mappings* below. Each always shows its text label in sentence case, and an unknown value renders with the `status-cancelled-*` tokens and its raw text.
- **AC-14**: A `/dev/ui` route shows every component in every state (default, hover hint, focus, disabled, loading, empty, error, destructive). It is reachable only in development builds and absent from the production bundle.
- **AC-15**: axe (an automated accessibility checker) reports zero serious or critical issues on `/dev/ui` at 375px and at 1280px. You can use every component by keyboard: Tab reaches it, Enter or Space activates it, Esc closes overlays, and focus returns. The focus ring is a visible 2px `ring` outline with offset. `prefers-reduced-motion` turns animation off. Touch size variants are at least 44px tall.
- **AC-16**: Every text and background pair in the *Contrast table* meets 4.5:1, and every UI boundary (input border, focus ring, active marker) meets 3:1.
- **AC-17**: `design.md` matches what was built: gold is named `highlight`, `input` is slate 500, the role colors and `muted-strong` rule are added, the toast placement is recorded, and the supported browser floor is stated.
- **AC-18**: The hand written `components/ui/Button.tsx` moves to `components/legacy/LegacyButton.tsx`, and its 8 importers are updated, so it can't collide with shadcn's `button.tsx` on a case insensitive filesystem (Windows).

## Decision

**Chosen option**: Option 2: Strangler foundation on shadcn/ui, React 19 and Tailwind v4.

Build the token layer and a full shadcn (Radix, `new-york` style) component kit beside the legacy styles, rename only the variables whose names collide, alias the rest, and enforce tokens with lint errors everywhere from day one. The legacy classes are then retired page by page during the UI refresh.

**Implementation skills**: `shadcn` (`shadcn-ui/ui`, `.claude/skills/shadcn/`) · `tailwind-4-docs` (`lombiq/tailwind-agent-skills`, `.claude/skills/tailwind-4-docs/`, use it for the v3 to v4 upgrade; its docs snapshot is not downloaded yet) · `ask-sonner` (`emilkowalski/skills`, `.claude/skills/ask-sonner/`) · `react-hook-form` (`pproenca/dot-skills`, `.claude/skills/react-hook-form/`, controlled shadcn inputs and field arrays) · `vercel-composition-patterns` (`vercel-labs/agent-skills`, `.claude/skills/vercel-composition-patterns/`, React 19 APIs and compound components) · `vercel-react-best-practices` (`vercel-labs/agent-skills`, `.claude/skills/vercel-react-best-practices/`)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

This feature has no data model, no state machine and no backend API. Its interface is the token set and the component APIs below.

**Stack changes** (all in `welinc-web-vrms`):

| Layer | Now | After |
|---|---|---|
| React | 18.3 | 19 (latest), `@types/react` 19; `react-router-dom` bumped to latest 6.x |
| Tailwind | 3.4, JS config, PostCSS | 4 (latest) with `@tailwindcss/vite`, config in `index.css` (`@theme inline`), `tw-animate-css` for motion |
| Components | hand written | shadcn/ui, style `new-york`, Radix primitives, `components.json` updated (`tailwind.config` empty, `style: new-york`) |
| Toasts | custom context | `sonner` |
| Forms | ad hoc state | `react-hook-form` + `zod` + `@hookform/resolvers` |
| Font | Inter by name | `@fontsource-variable/inter` |
| Lint | ESLint 9 | adds `eslint-plugin-better-tailwindcss` and a `no-restricted-syntax` color rule |
| A11y check | none | `axe-core` (dev dependency), injected into `/dev/ui` from `node_modules/axe-core/axe.min.js` through the Playwright MCP (`browser_evaluate` adds the script, then runs `axe.run()`) |

**Supported browsers**: Safari 16.4+, Chrome 111+, Firefox 128+ (Tailwind v4's floor). This rules out about iPhone 7 and older, and Android 6 and older. Older browsers are not supported and get no fallback CSS.

**Token set**. How it is laid out in `src/index.css`:
1. Each value is a plain CSS variable on `:root` (`--primary: #1a1f6e;`).
2. One `@theme inline` block opens with `--color-*: initial;` (the palette reset must come first, or it wipes the colors declared before it). It then maps each token: `--color-primary: var(--primary);`.
3. Legacy aliases sit on `:root` only, never in `@theme`, so they create no utility classes.
4. A base rule `*, ::before, ::after { border-color: var(--border); }` restores v3's default border color (v4 defaults to `currentColor`).

Tokens:

| Token | Value | Use |
|---|---|---|
| `background` | `#f8fafc` | Page canvas |
| `foreground` | `#0f172a` | Body text |
| `card` / `card-foreground` | `#ffffff` / `#0f172a` | Cards, tables, modals |
| `popover` / `popover-foreground` | `#ffffff` / `#0f172a` | Menus, selects, tooltips |
| `primary` / `primary-foreground` | `#1a1f6e` / `#ffffff` | Primary buttons, links, active nav |
| `primary-hover` | `#151b4f` | Hover and pressed primary |
| `secondary` / `secondary-foreground` | `#f1f5f9` / `#0f172a` | Secondary buttons |
| `muted` | `#f1f5f9` | Muted surfaces: table header, skeletons |
| `muted-foreground` | `#64748b` | Secondary text on `card` or `background` only |
| `muted-strong` | `#475569` | Secondary text on `muted` surfaces (table headers) |
| `accent` / `accent-foreground` | `#f1f5f9` / `#0f172a` | shadcn hover state for menu items and ghost buttons (not gold) |
| `highlight` / `highlight-foreground` | `#e8b800` / `#0f172a` | Gold: active nav marker, highlights, warning fills. Never text on white |
| `destructive` / `destructive-foreground` | `#c0392b` / `#ffffff` | Delete, cancel ticket, overdue, critical |
| `success` | `#047857` | Success text and icons |
| `success-fill` / `success-fill-foreground` | `#10b981` / `#0f172a` | Success fills (dark text, never white) |
| `border` | `#e2e8f0` | Hairlines and dividers on cards |
| `input` | `#64748b` | Borders of inputs, selects, checkboxes, switches |
| `ring` | `#1a1f6e` | Focus ring |
| `sidebar` / `sidebar-foreground` | `#0f1445` / `#ffffff` | Sidebar |
| `sidebar-primary` | `#e8b800` | Active item marker in the sidebar |
| `chart-1` to `chart-5` | `#1a1f6e`, `#e8b800`, `#10b981`, `#7c3aed`, `#94a3b8` | Chart series in order (unchanged) |
| `status-pending-bg` / `-fg` | `#fef3c7` / `#92400e` | Pending pill |
| `status-in-progress-bg` / `-fg` | `#e8e9f1` / `#1a1f6e` | In progress pill (primary at 10% on white, as a solid hex) |
| `status-for-verification-bg` / `-fg` | `#ede9fe` / `#5b21b6` | For verification pill |
| `status-completed-bg` / `-fg` | `#d1fae5` / `#065f46` | Completed pill |
| `status-cancelled-bg` / `-fg` | `#f1f5f9` / `#475569` | Cancelled pill, and any unknown value |
| `role-admin-bg` / `-fg` | `#1a1f6e` / `#ffffff` | Admin badge |
| `role-chief-mechanic-bg` / `-fg` | `#e8b800` / `#0f172a` | Chief mechanic badge |
| `role-mechanic-bg` / `-fg` | `#d1fae5` / `#065f46` | Mechanic badge |
| `role-operations-bg` / `-fg` | `#e8e9f1` / `#1a1f6e` | Operations badge |
| `role-customer-support-bg` / `-fg` | `#e0f2fe` / `#075985` | Customer support badge |
| `role-driver-bg` / `-fg` | `#f1f5f9` / `#334155` | Driver badge |
| `white` | `#ffffff` | Re-added after the palette reset, for overlays only |

Radius: `--radius: 0.5rem` (`rounded-lg`); Tailwind's default `rounded-xl` is already 12px, so cards and the login card don't change. Shadows use v4 names: `shadow-xs` on cards at most (v3's `shadow-sm`, which design.md means), and `shadow-lg` on dialogs, sheets and menus only. The legacy `--card-shadow` and `--elevation` become aliases of those. The old config's custom utilities (`shadow-card`, `shadow-elevation`, `shadow-sidebar`, `shadow-focus`, `outline-navy`, `transition-theme`, `focus-ring`, `focus-ring-inset`) have 0 uses in components and are removed. Focus styling comes from the `ring` token in each component (`focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`).

**Legacy aliases** (kept until the last use is gone; each refresh feature deletes the ones it frees):

| Legacy | Becomes |
|---|---|
| `--bg`, `--color-page-bg` | `var(--background)` |
| `--surface`, `--color-card-bg`, `--color-brand-surface` | `var(--card)` |
| `--surface-alt` | `var(--muted)` |
| `--text`, `--text-primary`, `--color-text-primary`, `--color-brand-black` | `var(--foreground)` |
| `--color-text-secondary` | `var(--muted-foreground)` |
| `--primary-strong`, `--color-brand-dark` | `var(--primary-hover)` |
| `--primary-soft` | `color-mix(in srgb, var(--primary) 10%, transparent)` |
| `--danger`, `--color-brand-danger` | `var(--destructive)` |
| `--danger-soft` | `color-mix(in srgb, var(--destructive) 10%, transparent)` |
| `--warning`, `--color-brand-warning`, `--accent-strong` | `var(--highlight)` |
| `--warning-soft` | `color-mix(in srgb, var(--highlight) 10%, transparent)` |
| `--warning-text` | `var(--status-pending-fg)` |
| `--success`, `--color-brand-success` | `var(--success)` (now `#047857`) |
| `--success-soft` | `color-mix(in srgb, var(--success-fill) 10%, transparent)` |
| `--info`, `--color-brand-primary` | `var(--primary)` |
| `--on-primary` / `--on-accent` | `var(--primary-foreground)` / `var(--highlight-foreground)` |
| `--status-*` (single color) | `var(--status-*-fg)` |
| `--color-surface-*`, `--color-input-*`, `--color-divider` | nearest token above |
| Tailwind `brand-*`, `semantic-*`, `surface-*`, `page`, `card`, `text-primary`, `text-secondary`, `border-default` | Not aliased: removed with the JS config; every use is rewritten to the token class in milestone 4 |

**Renamed, not aliased** (the name now means something else): `var(--muted)` (122 uses: gray text, now `var(--muted-foreground)`), `var(--accent)` (11 uses, gold, now `var(--highlight)`), `var(--accent-soft)` (1 use, now the highlight tint).

**Badge mappings**. All three badges share one pill: `rounded-full`, uppercase `text-xs font-medium tracking-wide`, label always shown. The label is written in sentence case, and the uppercase comes from CSS. Unknown values use `status-cancelled-*` and show the raw value.

| Badge | Value | Tokens (bg / fg) | Label |
|---|---|---|---|
| Status | `PENDING` | `status-pending-*` | Pending |
| Status | `PENDING_VERIFICATION` (legacy, not in `RepairStatus`) | `status-pending-*` | Pending verification |
| Status | `IN_PROGRESS` | `status-in-progress-*` | In progress |
| Status | `FOR_VERIFICATION` | `status-for-verification-*` | For verification |
| Status | `COMPLETED` | `status-completed-*` | Completed |
| Status | `CANCELLED` | `status-cancelled-*` | Cancelled |
| Status | `ACTIVE` | `status-completed-*` | Active |
| Status | `INACTIVE`, `LOCKED` | `status-cancelled-*` | Inactive, Locked |
| Priority | `CRITICAL` | `destructive` / `destructive-foreground` | Critical |
| Priority | `HIGH` | `highlight` / `highlight-foreground` | High |
| Priority | `MEDIUM`, `LOW` | `secondary` / `muted-strong` | Medium, Low |
| Role | `ADMIN` | `role-admin-*` | Admin |
| Role | `CHIEF_MECHANIC` (reserved, feature 17) | `role-chief-mechanic-*` | Chief mechanic |
| Role | `MECHANIC` | `role-mechanic-*` | Mechanic |
| Role | `OPERATIONS` | `role-operations-*` | Operations |
| Role | `CUSTOMER_SUPPORT` | `role-customer-support-*` | Customer support |
| Role | `DRIVER` (reserved, feature 44) | `role-driver-*` | Driver |

**Contrast table** (computed WCAG ratios; text needs 4.5, boundaries need 3):

| Pair | Ratio |
|---|---|
| `primary-foreground` on `primary` | 14.33 |
| `primary` on `background` (links, ring) | 13.70 |
| `sidebar-foreground` on `sidebar` | 17.41 |
| `sidebar-primary` marker on `sidebar` (boundary) | 9.36 |
| `highlight-foreground` on `highlight` | 9.60 |
| `destructive-foreground` on `destructive`, and `destructive` on white | 5.44 |
| `success` on white | 5.48 |
| `success-fill-foreground` on `success-fill` | 7.04 |
| `foreground` on `background` | 17.06 |
| `muted-foreground` on `card` / on `background` | 4.76 / 4.55 |
| `muted-strong` on `muted` | 6.92 |
| `input` border on `card` / on `background` (boundary) | 4.76 / 4.55 |
| Status pills (pending, in progress, for verification, completed, cancelled) | 6.37, 11.85, 7.57, 6.78, 6.92 |
| Role badges (admin, chief, mechanic, operations, support, driver) | 14.33, 9.60, 6.78, 11.85, 6.59, 9.45 |
| Priority badges (critical, high, medium/low) | 5.44, 9.60, 6.92 |
| Banned: `highlight` on white as text | 1.86 |
| Banned: `muted-foreground` on `muted` | 4.34 |

**Component inventory** (new unless noted; shadcn components land in `src/components/ui/` with lowercase file names, app compositions in `src/components/shared/`):

| Component | Path | Notes |
|---|---|---|
| Button | `ui/button.tsx` | Variants `default`, `secondary`, `outline`, `ghost`, `destructive`, `link`; sizes `sm` (h-9), `default` (h-10), `touch` (h-11), `icon`, `icon-touch`; `loading` prop shows a spinner and disables |
| Input, Textarea, Label, Checkbox, Switch | `ui/*.tsx` | `input` token border, `text-base` below 768px |
| Select | `ui/select.tsx` | Radix select for short fixed lists |
| Combobox | `ui/combobox.tsx` | Popover + Command (`cmdk`) for long or searchable lists |
| Field | `ui/field.tsx` | shadcn Field: label, required marker, helper, error; wraps react-hook-form `Controller` |
| Dialog, AlertDialog, Sheet | `ui/*.tsx` | Radix |
| ResponsiveDialog | `shared/ResponsiveDialog.tsx` | Dialog from 768px up, bottom Sheet below; props `open`, `onOpenChange`, `title`, `description`, `children`, `footer` |
| ConfirmProvider and `confirm()` | `shared/confirm/ConfirmProvider.tsx`, `shared/confirm/confirm.ts` | AlertDialog based, centered at every size; `tone: 'default' \| 'destructive'` |
| DropdownMenu, Tooltip, Tabs, Skeleton, Card, Badge, Table | `ui/*.tsx` | shadcn |
| Toaster | `ui/sonner.tsx` | Mounted once in `App.tsx` |
| `useToast` | `src/context/toast.ts` (rewritten) | Same signature, calls sonner |
| StatusBadge (replaces), PriorityBadge, RoleBadge | `shared/*.tsx` | From *Badge mappings* |
| KpiCard | `shared/KpiCard.tsx` | Caption, value (`text-2xl font-semibold tabular-nums`), context line, one icon in a tinted square |
| EmptyState, ErrorState | `shared/*.tsx` | Icon, one sentence, an action (empty) or a retry (error) |
| DataTable | `shared/data-table/DataTable.tsx` (+ `types.ts`) | See API below |
| Pagination | `shared/data-table/Pagination.tsx` | Previous, next, page info, existing `GoToPageInput` |
| `useIsMobile` | `src/hooks/useIsMobile.ts` | `matchMedia('(max-width: 767px)')` via `useSyncExternalStore` |
| `cn` | `src/lib/utils.ts` | `clsx` + `tailwind-merge` (both already installed) |
| UI showcase | `src/features/dev-ui/pages/DevUiPage.tsx` | Route `/dev/ui`, lazy, registered only when `import.meta.env.DEV` |

**Key APIs**:

```ts
// shared/confirm/confirm.ts
type ConfirmOptions = {
  title: string;
  description?: string;
  confirmText?: string;   // default 'Confirm'
  cancelText?: string;    // default 'Cancel'
  tone?: 'default' | 'destructive';
};
export function confirm(options: ConfirmOptions): Promise<boolean>;

// shared/data-table/types.ts (shaped like TanStack ColumnDef so a later swap is cheap)
type Column<T> = {
  id: string;
  header: string;
  cell: (row: T) => React.ReactNode;
  mobile?: 'title' | 'subtitle' | 'badge' | 'field' | 'hidden'; // default 'field'
  align?: 'start' | 'end';  // 'end' for money and counts (tabular-nums)
};
type DataTableProps<T> = {
  columns: Column<T>[];
  rows: T[];
  getRowId: (row: T) => string;
  state: 'loading' | 'error' | 'ready';
  onRetry?: () => void;
  empty: { title: string; description?: string; action?: React.ReactNode };
  onRowClick?: (row: T) => void;
  rowActions?: (row: T) => { label: string; onSelect: () => void; destructive?: boolean }[];
  pagination?: { page: number; pageSize: number; total: number; onPageChange: (p: number) => void };
};
```

Every component takes its visible text through props, with English defaults, so feature 7 (language support) can pass translated strings without changing component code.

**Component details**:
- **confirm wiring**: `ConfirmProvider` is mounted inside `BrowserRouter` in `App.tsx` and registers a module level handler on mount, which `confirm()` calls. It watches `useLocation()`, and a change in pathname or search resolves the open confirm and the whole queue `false`. With no handler registered, `confirm()` throws `Error('confirm() needs <ConfirmProvider> mounted')`.
- **Required marker**: a `destructive` asterisk with `aria-hidden="true"` after the label, plus visually hidden text "(required)" for screen readers.
- **Spinner**: lucide `Loader2` with `animate-spin`, 16px in `sm`/`default` buttons and 20px in `touch` buttons.
- **EmptyState**: icon (default lucide `Inbox`) in `text-muted-foreground`, a title, an optional description, an optional action. **ErrorState**: lucide `AlertCircle` in `text-destructive`, default title "Something went wrong", the caller's message, and a "Try again" button that calls `onRetry`.
- **KpiCard**: the icon square is `bg-primary/10` with a `text-primary` icon by default; `tone` can be `success`, `destructive` or `highlight` and uses that token at 10% with matching icon color.
- **DataTable phone cards**: the `title` column is the card heading (if none is marked, the first visible column is used). `subtitle` sits under it in `text-muted-foreground`. `badge` columns sit top right beside the `⋮` menu. `field` columns are a label and value list below. `hidden` columns are left out on phones. The `⋮` button uses size `icon-touch` (44px). With `onRowClick`, the whole card is the click target, and the menu stops the click from bubbling.
- **Field fallback**: use shadcn's `field` component if the `new-york` registry has it (check with the shadcn MCP). Otherwise write `ui/field.tsx` by hand with the same parts (`Field`, `FieldLabel`, `FieldDescription`, `FieldError`).
- **Sonner setup**: `<Toaster visibleToasts={3} position={isMobile ? 'top-center' : 'bottom-right'} />`. A `@media (prefers-reduced-motion: reduce)` rule sets `[data-sonner-toast] { transition: none; }`. `showToast` writes error text into a visually hidden `role="alert"` element that the Toaster wrapper renders once.

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Render any color | The hex value | Token in `index.css` (this spec's token set) |
| StatusBadge | Status color and label | `status` prop, from `RepairTicket.status` (`RepairStatus` in `src/types/index.ts`) or the user status, mapped by *Badge mappings* |
| PriorityBadge | Priority style and label | `priority` prop, from `PriorityLevel` in `src/types/index.ts` |
| RoleBadge | Role color and label | `role` prop: the signed in user's role from `authStore` (synced from the auth token), or a row's `UserRoleAssignment.role` in user lists. `CHIEF_MECHANIC` and `DRIVER` keys are reserved; features 17 and 44 confirm the exact enum names |
| DataTable, ResponsiveDialog, Toaster | Table vs cards, dialog vs sheet, toast position | `useIsMobile()` (viewport below 768px) |
| DataTable | Rows, total, page | Caller props; total and page from the API wrappers' normalized `{ data, total }` |
| DataTable | Loading, error, ready | Caller's fetch state |
| `confirm()` | `true` / `false` | The user's click; Esc, outside click and route change give `false` |
| `showToast` | Message, type, announcement level | Caller args; `type === 'error'` is announced assertively |
| Field | Error text | The zod schema message for that field, through react-hook-form |
| `/dev/ui` route | Whether it exists | `import.meta.env.DEV` |
| Font | Inter files | `@fontsource-variable/inter`, bundled by Vite |

**Key invariants**:
- No color, size or spacing value outside the token set and the Tailwind scale reaches a component. Lint fails on hex, `rgb()`, default palette classes and arbitrary values in every file.
- `highlight` is never text on a light surface. `muted-foreground` is never on `muted`; use `muted-strong` there.
- A badge never conveys meaning by color alone; the label is always rendered.
- Only one `Toaster` and one `ConfirmProvider` exist, both mounted in `App.tsx`.
- Shadows (v4 names): `shadow-xs` on cards at most, `shadow-lg` only on dialogs, sheets and menus. No gradients, blur or glass anywhere (the old ConfirmModal style is gone).
- The 4px grid holds in hand written code: spacing comes from whole steps of the Tailwind scale. shadcn generated components in `ui/` may keep their half steps (`gap-1.5`, `px-2.5`).

**Security model**: no data access changes. `/dev/ui` exists only in development builds, so production ships no extra route. No new env vars, and no `VITE_*` values.

**Failure and edge cases**:
- A `confirm()` call while one is open is queued, not dropped and not stacked.
- Navigating away while a confirm is open resolves it `false` and closes it, so no orphaned promise blocks a handler.
- Toast flood (for example a retry loop): sonner's visible limit is 3, and older toasts collapse.
- An error toast and a validation error at once: the field error stays inline, and the toast says what failed on the server.
- An unknown status or role value renders slate with its raw text, never crashes.
- A DataTable with a failed fetch keeps the previous rows hidden and shows `ErrorState`, so stale data never looks current.
- Slow connections: the skeleton matches the row shape and appears on the first render, before any spinner.
- `prefers-reduced-motion`: `tw-animate-css` animations and sonner transitions are off.
- A legacy class that depended on a removed Tailwind palette color: caught by the milestone 4 sweep, and lint errors keep it from coming back.

**Configuration required**: none.

**Critical test scenarios**:
- Happy path: open `/dev/ui` at 375px and 1280px, and every component renders in every state; then run axe with zero serious or critical issues. Verifies **AC-7**, **AC-14**, **AC-15**
- Regression: walk the 10 existing pages after the upgrade and after the sweep, with no console errors and the same content and actions. Verifies **AC-1**, **AC-4**
- Confirm: open a delete confirm, press Esc, and it resolves `false` with focus back on the trigger; call it twice quickly and the second opens after the first closes; with two queued, navigate away and both resolve `false`. Verifies **AC-8**
- Toast: trigger an existing `showToast('...', 'error')` call site, and the toast shows top center at 375px and bottom right at 1280px, announced assertively. Verifies **AC-9**
- Form: submit an invalid sample form on `/dev/ui`; errors appear inline with `aria-invalid`, and the submit disables with a spinner while a fake save runs. Verifies **AC-11**
- DataTable: switch a sample table between loading, empty, error (retry calls `onRetry`) and ready, at both widths. Verifies **AC-12**
- Lint: add `className="text-amber-500 p-[18px]"` and a `'#fff'` literal to a page, and `npm run lint` fails with errors. Verifies **AC-3**
- Production: `npm run build` output has no `/dev/ui` route chunk. Verifies **AC-14**

## Build plan

Tracer Bullet: milestone 1 is a thin thread through every layer of the system (upgrade, token, Tailwind utility, shadcn component, showcase, axe check, lint rule). Milestones 2 to 4 thicken it one strand at a time. The app stays working after every milestone.

**Milestone 1. Thin thread: upgrade, tokens, one component end to end**
1. Upgrade React to 19 (`react`, `react-dom`, `@types/react`, `@types/react-dom`) and `react-router-dom` to latest 6.x; fix any type errors. Satisfies **AC-1**
2. Upgrade Tailwind to v4 with the official upgrade tool (`npx @tailwindcss/upgrade`, on a clean git tree; it renames v3 scale classes such as `shadow-sm` to `shadow-xs`, so review its diff), switch to `@tailwindcss/vite`, delete `tailwind.config.js`, `postcss.config.js` and `autoprefixer`, drop the unused custom utilities, and keep the legacy classes in `@layer components`. Satisfies **AC-1**
3. Write the token set in `index.css` in the order in *Token set* (values on `:root`, the `@theme inline` mapping, aliases on `:root` only, the base border color rule). Rename `var(--muted)`, `var(--accent)` and `var(--accent-soft)` at every use (components and `index.css`). In this milestone the palette reset line is left commented out, so legacy palette classes still render until milestone 4. Satisfies **AC-2**, **AC-4**
4. Remove dark mode (Topbar toggle, `.dark` rules, theme state); set `color-scheme: light`. Satisfies **AC-5**
5. Install `@fontsource-variable/inter` and import it in `main.tsx`. Satisfies **AC-6**
6. Move `components/ui/Button.tsx` to `components/legacy/LegacyButton.tsx` and update its 8 importers. Satisfies **AC-18**
7. Update `components.json` (`new-york`, empty tailwind config), add `lib/utils.ts` `cn`, then add shadcn `button`. Satisfies **AC-7**
8. Create `/dev/ui` (dev only, lazy) showing Button in all variants and states; add `axe-core` as a dev dependency, inject `axe.min.js` through the Playwright MCP, and run `axe.run()` on it. Satisfies **AC-14**, **AC-15**
9. Add `eslint-plugin-better-tailwindcss` (entry point `src/index.css`) with `no-unregistered-classes` (catches default palette classes once the palette is reset) and `no-restricted-classes` with the pattern `^.*-\[.+\]$` (bracketed arbitrary values). Add `no-restricted-syntax` on `Literal` and `TemplateElement` values that match `#[0-9a-fA-F]{3,8}\b` or `rgba?\(`. Set these as errors on `components/ui` and `components/shared` for now. Satisfies **AC-3**

**Milestone 2. Feedback and overlays**
10. Add `sonner`, mount `Toaster` with the responsive position, rewrite `useToast` over sonner with the assertive error announcement, delete `ToastContext.tsx`. Satisfies **AC-9**
11. Add `dialog`, `alert-dialog`, `sheet`, `dropdown-menu`, `tooltip`; build `ResponsiveDialog` and `useIsMobile`. Satisfies **AC-7**, **AC-10**
12. Build `ConfirmProvider` and `confirm()` with the queue and route change handling; migrate the 5 `ConfirmModal` users; delete `ConfirmModal.tsx`. Satisfies **AC-8**
13. Add each to `/dev/ui` and run axe and the keyboard pass. Satisfies **AC-14**, **AC-15**

**Milestone 3. Forms and data display**
14. Add `react-hook-form`, `zod`, `@hookform/resolvers`; add `field`, `input`, `textarea`, `label`, `checkbox`, `switch`, `select`, and the combobox (`popover` + `command`). Build a sample form on `/dev/ui`. Satisfies **AC-11**
15. Add `table`, `card`, `badge`, `tabs`, `skeleton`; build `EmptyState`, `ErrorState`, `KpiCard`, `StatusBadge` (replacing the old one, same import path), `PriorityBadge`, `RoleBadge`. Satisfies **AC-7**, **AC-13**
16. Build `DataTable` and `Pagination` with `GoToPageInput`; add sample tables in every state to `/dev/ui`. Satisfies **AC-12**
17. Run axe and the keyboard pass on all of `/dev/ui` at 375px and 1280px. Satisfies **AC-15**, **AC-16**

**Milestone 4. Enforcement sweep**
18. Turn on the default palette reset (`--color-*: initial` as the first line of `@theme inline`, then re-add `white`); rewrite the about 254 default palette classes, 12 arbitrary values and all `brand-*` / `semantic-*` / `surface-*` / `page` / `card` / `text-primary` / `text-secondary` / `border-default` classes to token classes. Satisfies **AC-2**, **AC-3**
19. Turn the lint rules to errors across all of `src`; reach zero errors. Satisfies **AC-3**
20. Walk the 10 existing pages with Playwright at 375px and 1280px for regressions. Satisfies **AC-1**, **AC-4**
21. Update `design.md` (highlight rename, `input` slate 500, `muted-strong`, role colors, toast placement, browser floor). Satisfies **AC-17**
22. Run lint, typecheck and build. Satisfies **AC-1**

## Migration plan

**Strategy**: strangler. The new tokens and components land beside the legacy classes, and pages move onto them in features 8 to 15.
**Phases**:
1. Milestones 1 to 3 add the system; existing pages render the same through the aliases.
2. Milestone 4 removes every off token value from all pages (they look the same, but now use tokens).
3. Features 8 to 15 replace legacy classes and `LegacyButton` page by page, deleting each alias and class once it is unused.
**Rollback**: one commit per milestone (per your per milestone commit rule); reverting a milestone's commit restores the previous state. The React 19 and Tailwind v4 upgrades sit in milestone 1, so a revert there undoes both together.
**Risks**: the Tailwind upgrade tool can misconvert custom plugin and `@apply` rules (check `index.css` by hand); the palette reset can turn a legacy class colorless (milestone 4's page walk catches it); a library may not support React 19 (all current deps do as of today; check peer warnings at install).

## Consequences

**Positive**:
- Every refresh page (8 to 15) is assembly of tested parts, with one look and one behavior for dialogs, confirms, toasts and tables.
- Lint makes the "tokens only" rule automatic instead of a review burden.
- Fixes two real AA failures (input borders at 1.48:1, and gray text on gray at 4.34:1).
- The portal can later copy the same `index.css` token block and `components/ui` set.

**Negative / tradeoffs**:
- Milestone 4 touches every page now, and features 8 to 15 touch them again. That is the cost of lint errors everywhere from day one, chosen over warnings.
- React 19 and Tailwind v4 in one milestone makes it the riskiest commit of the feature.
- Two styling systems coexist until the refresh ends; the aliases and legacy classes are debt with a deadline.
- No dark mode, and no support for browsers older than 2023.
- Inputs get darker borders, which visibly changes existing forms.

**Neutral**:
- `design.md` changes in five places (AC-17); the workspace repo needs a commit for it.
- The shadcn CLI writes lowercase file names, while existing app files use PascalCase. Both conventions coexist by folder (`ui/` lowercase, everything else PascalCase).

## Follow-up

- [ ] Ask the stakeholder whether any garage phone is older than iPhone 8 or runs Android 6 or older (the Tailwind v4 browser floor).
- [ ] Feature 45 (Reports module): decide whether client side sorting, column hiding or bulk select justify adopting TanStack Table under `DataTable`.
- [ ] Portal follow up: copy the tokens and components into `welinc-web-portal` (already on React 19, still Tailwind 3); enroll it in the scope.
- [ ] Features 17 and 44: confirm the enum names for `CHIEF_MECHANIC` and `DRIVER` so `RoleBadge` matches.
- [ ] Download the `tailwind-4-docs` skill's docs snapshot before milestone 1.
- [ ] `ask-sonner` and `react-hook-form` are installed but not yet listed in `AGENTS.md` `## Agent skills`; they belong in `welinc-web-vrms/AGENTS.md` (frontend only).
- [ ] The web-vrms `AGENTS.md` color convention (legacy `var(--muted)`, `brand-*`) and its dark mode gotcha go stale after this feature; refresh them.
- [ ] Record the declined agent skill (`a11y-playwright-testing`) in `AGENTS.md` so it is not offered again.
