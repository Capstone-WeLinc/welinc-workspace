# UI consistency pass and crew join date removal

Status: pushed, not yet in a pull request. Web branch: `BMS/ui-consistency-and-crew-join-date` (into `development`); backend branch: `BMS/ui-consistency-and-crew-join-date` (into `development`); workspace branch: `docs/bms-ui-consistency-and-crew-join-date` (into `main`).

Decision history: [rationale.md](rationale.md). Review checklist: [verify.md](verify.md).

Touches `welinc-web-bms` (items 1–8) and, for item 5 only, `welinc-backend-bms/bms-dispatch-service` and its database. The eight requests share this one spec.

## 1. No icon beside modal titles

**Problem:** every modal header showed a gold icon tile next to its title.

**What it does:**

- `ModalHeader` (used by every modal) no longer has an icon: navy bar, white title, gold subtitle, optional badge and the close button stay as they were.
- The `icon` option is removed from `ModalHeader` and from every modal that passed one (booking, scheduling, post-service, approvals, reports, services offered, vehicle/driver/helper details, crew edit, refund, submissions, job order).
- The delete confirmation (`DeleteConfirmModal`) loses the red warning icon beside its title; the title stays red.

## 2. Compact tables across BMS

Applies to every table in Admin, Operations and Customer Service. Set once in shared styles so new tables follow it too.

**What it does:**

- **Row height:** 64px for every body row, set globally in `index.css`. It's a minimum: a row with more content (two lines, badges, wrapped text) grows to fit. Empty-state and loading rows keep their own taller padding.
- **Header height:** 44px for every header row, set globally.
- **Cell padding:** 10–12px vertical and 16px horizontal. Most cells already used `px-4 py-2.5`; the outliers were changed:
  - shared table classes in `StandardTable` (used by Reports and the monthly report): from `px-2.5 py-2` to `px-4 py-2.5` (header) and `px-4 py-3` (cells); its "compact" density now uses the same values.
  - `.approval-data-table` (My Submissions): from 8/10px to 10/16px (header) and 12/16px (cells).
  - Activity Logs cells, forecast report tables and the database grid: from `px-3` to `px-4`.
  - Approvals cells: from `py-3.5` to `py-3`.
- **Vertical alignment:** Scheduling cells were top-aligned, which left their text at the top of the taller rows; they are now centred like every other table.
- **Coverage:** checked file by file: the 20 files with tables (Admin: Bookings, Scheduling, Post-Service, Approvals, Crew Management, Activity Logs, Sales Report, Reports and the monthly/forecast reports; Operations: Dashboard, Scheduling, Job Orders; Customer Service: Dashboard, Bookings, Daily Sales, Post-Service, My Submissions; shared `StandardTable` and `DbDataGrid`). No page builds a table out of divs.
- **Text:** 14px primary text, 12px secondary text and headers. The Scheduling table's base text goes from 11–12px to 14px, the forecast tables from 12px to 14px, and the Sales Report booking number under the client name from 11px to 12px.
- **Pagination:** the shared table pagination is tighter: less padding above and below, smaller gaps between page buttons, and a 32px "Show" dropdown (was 36px).

**Not changed:** colours, borders, columns, data, sorting, filters, actions, responsiveness. Date-picker calendars and the small "Requested change" table inside the submission modal keep their own sizing.

## 3. Card pagination on Vehicle & Team Availability

**Problem:** the Vehicles, Drivers and Helpers tabs loaded 12 cards at a time with a "Show more" button, so long lists only grew.

**What it does:**

- All three tabs show 12 cards per page (four rows of the three-column grid) with a pagination card below the grid.
- The pagination card is a white rounded card matching the availability cards. It shows "Showing 1–12 of N vehicles/drivers/helpers", previous and next arrows, and page numbers with ellipses for long lists. The current page is a navy circle, as in the table pagination.
- Changing tab, search or status filter goes back to page 1. If the live refresh shortens the list, the page moves back to the last page that still exists.
- The pagination card is hidden while vehicles are loading, when they fail to load, and when nothing matches.
- New shared component `src/components/ui/CardPagination.tsx` for any future card grid.

## 4. Approvals: Type column pills

**Problem:** the Type column showed small square-cornered tags.

**What it does:** each type is a pill like the reference: fully rounded, soft fill, bold dark text, 14px, `px-3.5 py-1`. Each request type keeps its own colour family, now a `-100` fill with `-800` text: reschedule orange, change indigo, collection green, refund rose, crew leave purple (emergency red). The row icon tiles and the details panel are unchanged.

## 5. Join date removed from crew

**Problem:** BMS kept a join date for drivers and helpers that the team no longer needs.

**What it does:**

- **Edit driver / Edit helper modal:** the Join date field is gone; "Work details" now holds only Status. There is no Add driver or Add helper modal: since spec bms/0012 crew come from their Auth account, so only the edit modal had the field.
- **Elsewhere on the web,** because the value no longer exists: the Join date column on Crew Management, "Join date" in the driver and helper details modals, and "Joined" on the helper cards in Vehicle & Team Availability are removed.
- **Dispatch service:** stops reading, returning and saving `joinDate`. A request that still sends it (an older web page left open) is ignored, not rejected.
- **Database:** migration `20261126090000_drop_crew_join_date` drops `drivers.join_date` and `helpers.join_date` with `DROP COLUMN IF EXISTS`. Nothing else reads them (checked: the other BMS services, analytics and the mobile app).

## 6. Pagination on Services Offered

**Problem:** the Services, Additional Services and Protective Materials tabs listed every card on one long page.

**What it does:** all three tabs use the same pagination card as Vehicle & Team Availability (`CardPagination`): 12 cards per page, "Showing 1–12 of N services / additional services / protective materials", previous/next and page numbers. Changing tab or search goes back to page 1; after a delete shortens the list, the page moves back to the last one that still exists. The pagination card is hidden while loading and when nothing matches. Add, edit, view and delete are unchanged.

## 7. Team Management: icon-only Edit

**Problem:** the Actions column showed a pencil icon followed by the word "Edit".

**What it does:** the button shows only the pencil icon, in a 36px square like the other icon actions. Its screen-reader label ("Edit <name>") stays, and a tooltip says "Edit" on hover.

## 8. Team Management: action icon matches the other tables

**Problem:** after item 7 the Edit icon was navy with a light-indigo hover, unlike the action icons in the other tables.

**What it does:** it now uses the same style as the Scheduling and Bookings action icons: 36px square, rounded, grey (`text-slate-600`) 16px icon, light-grey hover (`hover:bg-slate-100`), navy focus ring, centred in the Actions cell. Behaviour is unchanged.

## Removed

- The gold icon tile in `ModalHeader` and its `icon` option; the warning icon in `DeleteConfirmModal`.
- The "Show more" button and its batch loading on Vehicle & Team Availability.
- The "Edit" text on the Team Management edit button.
- Join date: the edit-modal field, the Crew Management column, the details-modal and card entries, the API field, and the `drivers.join_date` / `helpers.join_date` columns.

## Testing

- `welinc-web-bms`: `lint` (0 errors; 30 warnings, all already on `development` in other files), `typecheck`, `test` (20 pass) and `build:prod` with the CI's `VITE_*` values all pass locally.
- `welinc-backend-bms`: `prisma validate`, `lint:ci`, `typecheck`, `build` and `test` (dispatch 39 pass; the driver contract test now checks no join date comes back) pass locally.
- Local database: the existing join dates (32 rows) were exported to a CSV first, then the migration ran; both columns are gone and the service reads all 12 drivers and 20 helpers.
- Not yet checked by hand in the running app.

## Deploy notes

- Order matters for item 5:
  1. Back up the dispatch database (or at least `SELECT id, user_id, join_date` from `drivers` and `helpers`) if the old join dates may be needed: the drop deletes them.
  2. Deploy `welinc-backend-bms` (dispatch service). Run `npx prisma generate` in the container if its `node_modules` volume is reused, otherwise the old client still asks for `join_date`.
  3. Run `npx prisma migrate deploy` for the dispatch service.
  4. Deploy `welinc-web-bms`.
- Rolling back after the migration needs the column re-added (`ALTER TABLE drivers ADD COLUMN join_date DATE; ALTER TABLE helpers ADD COLUMN join_date DATE;`) before the old code runs; the values come back only from the backup.
