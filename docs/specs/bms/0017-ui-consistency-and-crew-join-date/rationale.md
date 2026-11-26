# UI consistency pass and crew join date removal: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

Seven requests recorded in one spec, as the team asked. The first three are UI-only; items 4 (Approvals type pills) and 5 (remove crew join date, including from the database) were added later, then 6 (pagination on the Services Offered tabs), 7 (icon-only Edit in Team Management) and 8 (that icon styled like the other Actions columns):

1. Remove the icon beside every modal title.
2. Compact table layout across every BMS table: ~64–68px rows, 10–12px / 14–16px cell padding, 14px primary and 12–13px secondary text, 42–44px headers, tighter pagination. Change shared components and global styles first.
3. Card-style pagination on the Vehicles, Drivers and Helpers tabs of Vehicle & Team Availability.

## Options considered

### Modal icons

- **Remove the icon from `ModalHeader` and drop the `icon` option** (chosen). Pros: one place, every modal changes, and no unused option is left for someone to re-add an icon. Cons: touches every modal file to remove the prop.
- Keep the option and stop passing it. Pros: smaller diff. Cons: the icon can come back one modal at a time.

### Table row and header height

- **Global `tr` heights in `index.css`** (chosen). Pros: every current and future table follows it without editing each page; a `<tr>` height is a minimum, so rows with more content still grow (the "taller rows only when needed" rule). Cons: a global rule, so special tables need an exclusion (date pickers, the submission "Requested change" table).
- Add height classes to each table. Pros: explicit. Cons: 20 tables to edit and easy to miss on new ones.

### Cell padding

- Most tables already used `px-4 py-2.5` (16px / 10px), inside the requested range, so they were left alone. Only the shared `StandardTable` classes, the approval-table CSS and the few `px-3` / `py-3.5` cells were moved into range.

### Card pagination

- **Numbered pages in a separate card, 12 per page** (chosen). Pros: matches the request, the list no longer only grows, and the page-number pattern matches the tables. Cons: you can't see more than 12 at once.
- Table pagination component under the grid. Cons: it's built for tables (row-count dropdown with 8/10/25/50, flat border), which doesn't fit a three-column grid or the card look.

### Approvals type pills (added later)

- **Pill shape from the reference, each type keeps its colour** (chosen by the team). Pros: matches the reference look and you can still tell types apart at a glance. Cons: only the "Medium"-style amber is literally from the reference.
- All pills amber, exactly like the reference. Cons: every type looks the same.

### Join date (added later)

- **Remove it everywhere and drop the columns** (chosen). The team asked for it gone from the modal and from the database; once the column is dropped, the Crew Management column and the details entries would only ever say "Not recorded", so they go too.
- Hide the field but keep the column. Cons: not what was asked; the data stays with nothing to edit it.
- How it's made safe: the code stops using the column first and the migration runs after; `DROP COLUMN IF EXISTS` can be re-run; old clients sending `joinDate` are ignored rather than rejected; the deploy notes say to back up first because the values can't be recovered otherwise.

### Services Offered pagination (added later)

- **Reuse `CardPagination` with 12 per page** (chosen). Pros: the page is the same three-column card grid as Vehicle & Team Availability, so both card pages page the same way, with one component to maintain. Cons: none found.
- Table-style pagination. Cons: its row-count dropdown and flat bar don't fit a card grid.

### Icon-only Edit (added later)

- The button keeps its accessible label and gains a tooltip, so removing the visible word doesn't hide what it does from screen readers or mouse users. It matches the icon-only actions used in other tables (spec bms/0016).
- Item 8 then aligned its colours to the other tables: the team asked for Team Management to follow the other Actions columns, not the reverse. The Scheduling single-action style (grey icon, light-grey hover) was used because it's the shared pattern on the main tables; the navy-with-indigo-hover look existed only here.

## Rationale

- Shared components and global styles were changed first, as the request asks, so new tables and modals follow the design without extra work.
- Twelve cards is four full rows of the three-column grid, and also divides evenly into the one- and two-column layouts.
- The page is clamped after the one-minute refresh so a shrinking list never leaves an empty page.
