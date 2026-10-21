# 0001. Design system and UI foundation: rationale

Decision record for [index.md](index.md). `/develop` does not need this file.

## Context

> ⚠️ Premise note: this feature bundles three things that could each be their own task: a framework upgrade (React 19, Tailwind v4), the token layer, and a 20+ component kit plus an enforcement sweep over every page. Within a 5 week deadline the risk is that the foundation eats the first week and a half. The build plan contains it by making milestone 1 a thin thread that proves the whole chain on one component before widening, and by keeping each milestone a separate revertable commit. If time gets tight, milestone 4's sweep is the piece to slip, not the components the refresh pages need.

`welinc-web-vrms` (React 18, Vite 8, Tailwind 3.4) has an art direction in `design.md` but no system that enforces it. The current state:
- `index.css` is 1,489 lines with two overlapping variable sets (`--color-brand-*` and the VRMS short names) and about 214 custom classes.
- `tailwind.config.js` adds a third set (`brand-*`, `semantic-*`, `surface-*`) and a plugin with a raw hex focus ring.
- Components use 434 inline `var(--…)` references, about 254 default palette classes (`text-amber-500`) and 12 arbitrary values (`z-[999999]`).
- There is one hand written `Button`, a `ConfirmModal` in a banned style (dark glass, blur, bouncing icon), and a custom toast context. `components.json` exists, but no shadcn component is installed.
- Dark mode is half built: a toggle exists, but no dark tokens do.

Forces:
- **Users**: mechanics on phones in bright garages, and non technical office staff. Readability, big targets and AA contrast are requirements, not polish.
- **Order of work**: eight UI refresh features (8 to 15) start right after this one and must only assemble parts. Anything this foundation leaves out gets invented per page.
- **Time**: deployed by end of November 2026, about 5 weeks.
- **Upstream**: current shadcn/ui targets Tailwind v4 and React 19 (components without `forwardRef`, relying on React 19's `ref` as a prop). On React 18 those refs break under Radix `asChild`.
- **Naming**: two legacy variables (`--muted`, `--accent`) share names with shadcn tokens but mean different things (gray text vs pale surface; gold vs hover gray).
- **Accessibility audit** (computed): input borders at 1.48:1 fail the 3:1 boundary rule, and `muted-foreground` on `muted` is 4.34:1, under 4.5.
- **Platform**: development happens on Windows, where `Button.tsx` and shadcn's `button.tsx` are the same file.

## Options considered

### Option 1: Fix in place

Restyle the existing hand written components and CSS classes to match `design.md`, consolidate the variables, stay on React 18 and Tailwind 3.

**Pros**:
- No upgrades and the smallest diff.
- Nothing new to learn.

**Cons**:
- Every dialog, select, menu and tooltip still has to be hand built with its own focus and keyboard handling, which is where AA usually fails.
- Leaves the Tailwind v4 goal and shadcn adoption (both named in the scope and `design.md`) undone, so the debt grows with each refresh page.

### Option 2: Strangler foundation on shadcn/ui, React 19 and Tailwind v4 (chosen)

Upgrade, write canonical shadcn named tokens with aliases for the legacy names, add a full shadcn kit beside the legacy styles, enforce tokens by lint, and retire legacy classes page by page.

**Pros**:
- Radix gives tested focus traps, keyboard handling and ARIA for every overlay.
- Pages keep working throughout; each refresh feature moves its page onto the kit.
- Future shadcn components drop in unedited, because token names match upstream.

**Cons**:
- Two upgrades at once in milestone 1.
- Aliases and legacy classes coexist until the refresh ends.

### Option 3: Replace directly

Upgrade, then rewrite every page onto the new kit inside this feature and delete all legacy CSS at once.

**Pros**:
- One clean styling system at the end, with no alias debt.

**Cons**:
- Merges this feature with features 8 to 15 into one big bang; every page is broken or in flux until the end, with nothing demoable midway.
- Removes the per page checkpoints the UI refresh epic was planned around.

### Option 4: Strangler on the current stack (shadcn on Tailwind 3 and React 18)

Same as Option 2, but install the older shadcn output that still targets Tailwind 3 and `forwardRef`, and upgrade later.

**Pros**:
- Defers upgrade risk.

**Cons**:
- Every component is restyled again at the later upgrade, and older shadcn output misses current fixes.
- Upgrades put off under deadline rarely happen.

## Rationale

Option 2 is the only one that serves the order of work: the refresh features need a complete, accessible kit now, and they need the existing pages to keep working while they move one by one (the strangler pattern applied to UI). Option 1 fails the accessibility force, since hand rolled overlays are where keyboard and focus bugs live. Option 3 fails the time force by turning eight checkpointed features into one big bang. Option 4 spends the same effort twice.

Upgrading React and Tailwind first is forced by upstream: current shadcn components assume both, and adding them on the old stack means editing every copied component (refs) or restyling later. The upgrade is small in practice, because the code has no `forwardRef` and all current dependencies support React 19.

The smaller calls, each with its runner up:
- **shadcn token names canonical, legacy as aliases** (runner up: rename all 434 uses now). Aliases keep pages stable, and only the two colliding names need a rename. Matching upstream names means future components need no edits.
- **Gold renamed `highlight`** (runner up: keep `accent` and edit components). shadcn uses `accent` for hover gray in every menu and ghost button; fighting that costs an edit on every future add.
- **Hex values** (runner up: OKLCH). The values stay comparable with `design.md` at a glance; Tailwind v4 tints hex through `color-mix`.
- **Light only** (runner up: full dark tokens). `design.md` has no dark palette, and one theme halves the contrast work under deadline.
- **Promise based `confirm()`** (runner up: declarative dialog). Many delete and cancel prompts are coming; one line per call beats open state per page.
- **sonner behind `useToast`** (runner up: rewrite 38 calls). Zero churn now, same result.
- **react-hook-form + zod + shadcn Field** (runner up: plain state with a Field wrapper). The repair form is large enough to need schema validation and field arrays; this is shadcn's documented form path.
- **Own DataTable with TanStack shaped columns** (runner up: TanStack now). All paged tables are sorted and filtered on the server; client side features have no current user. Mirroring `ColumnDef` keeps a later swap cheap.
- **Lint errors everywhere now** (runner up, which I recommended: errors on new code, warnings on a shrinking legacy list). You chose strict enforcement and accepted touching every page in milestone 4. It works, and it buys a guarantee that nothing off token survives; the cost is a second touch of each page during the refresh.
- **`/dev/ui` showcase over Storybook**: zero new tooling, and Playwright and axe can check it directly.
- **Input border slate 500**: the only slate that passes 3:1 on both white and the page background (4.76 and 4.55).
- **Six distinct role colors from the existing palette**, with violet kept for "For verification" only, so "needs admin" stays unmistakable.
- **ResponsiveDialog at 768px**, and **toasts top center on phones**, so the bottom tab bar and the full width primary action are never covered.
- **Strict browser floor (2023 browsers)**: only about 8 year old phones fall outside it, which is accepted pending one stakeholder check.

## Evidence

**Usage counts in `welinc-web-vrms/src`** (2026-10-22):

| Item | Count |
|---|---|
| Source files (`.ts`, `.tsx`) | 65 |
| Custom classes in `index.css` | about 214 |
| Inline `var(--…)` uses in components | 434 (`--muted` 104, `--danger` 59, `--primary` 56, `--border` 56, `--text` 39, `--success` 34, others below 22) |
| `var(--muted)` in `index.css` | 18 |
| `var(--accent)` in components / `index.css` | 10 / 1 |
| Default palette classes (`text-amber-500` and similar) | about 254 |
| Arbitrary value classes | 12 |
| Hex values in `.ts` / `.tsx` | 0 / 0 |
| Toast call sites | 38 |
| `ConfirmModal` users | 5 |
| `ui/Button` importers | 8 |
| `<table>` elements | 12 (5 paginated with `GoToPageInput`) |
| `.dark` rules | 9 |
| `forwardRef` uses | 0 |
