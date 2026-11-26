# Verify: UI consistency pass and crew join date removal

Checklist derived from [index.md](index.md). Tick only what was actually checked.

## Web: modals

- [ ] Booking details, edit booking, new booking, reschedule: title with no icon beside it.
- [ ] Scheduling assign and schedule details: no icon.
- [ ] Post-service record, approvals details, sales report details, refund request, submission details: no icon.
- [ ] Vehicle, driver and helper details and crew edit: no icon.
- [ ] Services Offered add/edit/view: no icon.
- [ ] Delete confirmation: red title with no warning icon.
- [ ] Subtitle, badge and close button still show and work in each.

## Web: tables

- [ ] Admin: Bookings, Scheduling, Post-Service, Approvals, Crew Management, Activity Logs, Sales Report, Reports (daily and monthly): rows about 64px, headers about 44px.
- [ ] Operations: Dashboard, Scheduling, Job Orders: same.
- [ ] Customer Service: Dashboard, Bookings, Daily Sales, Post-Service, My Submissions: same.
- [ ] Rows with two lines of content (name and email, client and booking number) still fit without clipping.
- [ ] Empty and loading rows look the same as before.
- [ ] Pagination bar is tighter and still works (page buttons, "Show" rows).
- [ ] Date pickers still look the same.
- [ ] Tables still scroll sideways on narrow screens.

## Web: Vehicle & Team Availability

- [ ] Vehicles, Drivers and Helpers tabs show 12 cards and a pagination card below.
- [ ] "Showing 1–12 of N" text uses the tab's name; arrows and page numbers move between pages.
- [ ] Changing tab, search or status goes back to page 1.
- [ ] No pagination card while loading, on load error, or with no matches.
- [ ] Layout works at one, two and three columns.

## Web: Approvals

- [ ] Type column shows rounded pills with bold text, each type in its own colour.
- [ ] Pills fit in the row on narrow screens (the table scrolls sideways).

## Web: Services Offered

- [ ] Services, Additional Services and Protective Materials each show 12 cards and a pagination card below.
- [ ] The range text names the tab ("services", "additional services", "protective materials"); arrows and page numbers work.
- [ ] Changing tab or searching goes back to page 1.
- [ ] Deleting the last card on the last page moves to the previous page.
- [ ] No pagination card while loading or when nothing matches.

## Web: Team Management

- [ ] Drivers and Helpers tables: the Edit action is the pencil icon only, with an "Edit" tooltip, and opens the edit modal.
- [ ] The Edit icon looks like the Scheduling and Bookings action icons: same size, grey icon, light-grey hover, centred.

## Crew join date

- [ ] Edit driver: no Join date field; saving status, license and emergency contact works.
- [ ] Edit helper: no Join date field; saving works.
- [ ] Crew Management drivers and helpers tables: no Join date column.
- [ ] Driver and helper details modals: no Join date; helper cards: no "Joined" line.

## Database

- [x] Local: join dates exported to CSV before the drop (32 rows).
- [x] Local: `prisma migrate deploy` applied `20261126090000_drop_crew_join_date`; no `join_date` column left in `drivers` or `helpers`.
- [x] Local: after `prisma generate` and a restart, the service reads every driver and helper.

## API / automated

- [x] Dispatch contract test: an updated driver comes back without `joinDate`; helper optional fields still clear.

## Scope

- [x] Backend change is limited to the dispatch service's crew fields and one migration.
- [x] The three spec files are present in this folder.

## Commands

- [x] Web `lint`, `typecheck`, `test`, `build:prod` with the CI's `VITE_*` values pass locally.
- [x] Backend `prisma validate`, `lint:ci`, `typecheck`, `build`, `test` pass locally.
