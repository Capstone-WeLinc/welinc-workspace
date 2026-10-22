# Verify: history & audit log refresh · spec 0003 · updated 2026-10-22
_Steps derived from spec 0003 acceptance criteria and its Value sourcing table. `/check verify` runs these; `/test` locks the durable ones._

Sign in for local testing: `vrms.admin@welinc.com` / `admin1234` (admin), `mech.juan@welinc.com` / `mechanic1234` (mechanic, has a mechanic record), then open `http://localhost:8001/login?token=<accessToken from POST /auth/login>`. After a backend edit, restart `welinc_vrms_backend`: file changes from Windows don't reach its watcher.

## UI / manual

### Repair history (`/history`)
- [x] As admin at 1280px: header reads "Repair history" with the History icon and "Closed repairs, completed and cancelled."; no primary action button → AC-1
- [x] Four tiles in one row: Closed, Completed (success tone), Cancelled, Total spend; Closed equals the table's total rows across all pages → AC-2
- [x] At 768px the tiles sit two by two; at 375px Closed and Total spend take a full row with Completed and Cancelled paired between (a peso total can't fit a half tile; see the note in the build report) → AC-2
- [x] Pick This month + Completed: tiles change to match only those rows; Total spend equals the sum of the Cost column across every page → AC-2, AC-3
- [x] Garage filter lists the garages from `getGarages()`; picking one narrows rows and tiles → AC-3
- [x] Date presets: This month, Last 90 days, This year each send `from`/`to` at local midnight (check the request in DevTools) → AC-3
- [x] Custom with only "From" set: no request is sent. Set "To" before "From": the inline error "Start date must be on or before the end date." shows and no request is sent → AC-3
- [x] Changing any filter while on page 3 returns to page 1 → AC-3
- [x] At 375px the filters stack with no horizontal scroll → AC-3, AC-20
- [x] Columns: Repair # (lock icon named "Locked", or a gold "Unlocked" badge), Vehicle, Outcome badge, Duration ("Same day", "1 day", "N days"; "—" for cancelled), Garage, Cost (admins only, right aligned), Closed (`Oct 22, 2026`). Rows newest closed first → AC-4
- [x] A cancelled ticket with a long reason shows one truncated muted line under its badge; hover or Tab to it shows the full reason in a tooltip → AC-4
- [x] Month headings ("October 2026") sit between rows on desktop and between cards on phones; a month split across pages 1 and 2 shows its heading on both pages → AC-5
- [x] Clicking a row opens `/repairs/:id?mode=readonly`; the row menu shows View details (both roles) and Edit ticket (admin only) → AC-6
- [x] 20 rows per page with Previous, Next and Go to page → AC-7
- [x] Loading shows skeleton tiles and skeleton rows; stop the backend and reload: an error state with "Try again" replaces tiles and table → AC-8
- [x] Search "zzzz": "No repairs match these filters" with "Clear filters", which resets search, outcome, garage and date range → AC-8
- [x] As mechanic: three tiles (no Total spend), no Cost column, only View details in the row menu → AC-2, AC-6, AC-18

### Audit log (`/audit-logs`)
- [x] Header reads "Audit log" with the ClipboardList icon and "Every change to repair tickets: who made it and when."; as mechanic the route sends you to the dashboard → AC-9
- [x] Events are grouped under "Today", "Yesterday", or `Mon, Oct 18` (with the year when it isn't this year); each shows a tinted type icon, time `10:42 AM` (tooltip with full date and time), initials avatar and name (email in tooltip), and the repair number linking to `/repairs/:id` → AC-10
- [x] Sentences per type: created / changed the status of (old → new badges) / updated the costs of ("₱0 → ₱4,000 total" plus "Parts … · Labor …", or "Lump sum") / unlocked (reason in quotes) / moved … to a different garage (old → new). A backfilled ticket reads "REP-… was created" with no avatar → AC-11
- [x] Type chips (one active at a time, `aria-pressed`), Person, Date range and Repair # each narrow the list on the server (check the request params). A 1 character repair search sends no `repairNumber`; 2+ characters send it after typing stops → AC-12
- [x] The first load shows 50 events. "Load older events" adds 50 at a time with a spinner, until "You’ve reached the start of the log." → AC-13
- [x] Block `/vrms/repairs/audit-logs` with a cursor in DevTools and click "Load older events": "Couldn’t load older events." with "Try again" appears, and the events already shown stay → AC-13
- [x] Skeleton while loading; error state with "Try again" on a failed first load; a filter that matches nothing shows "No events match these filters" with "Clear filters" → AC-14
- [x] Load to the end: the count of events equals `SELECT count(*) FROM audit_logs`, and no event id repeats → AC-15
- [x] Create a new event in another tab: it appears only after a filter change or reload, never in the middle of "Load older events" → AC-15

### Both pages
- [x] Inject axe (`/node_modules/axe-core/axe.min.js`) and run `axe.run()` on `/history` (admin and mechanic) and `/audit-logs` (admin) at 375px and 1280px → zero serious or critical → AC-20
- [x] No horizontal page scroll at 375px or 1280px on either page → AC-20
- [x] Open an old seeded ticket and a new ticket's detail page: both load, the audit panel lists only status, cost and unlock rows (no CREATED), and the dashboard still loads → AC-18b

## Commands
- [x] `docker exec welinc_vrms_backend npx jest` → all suites pass (cursor paging with ties, cost parsing, actor match by email, history summary and mechanic scoping, 403 on the audit routes) → AC-11, AC-15, AC-18
- [x] `docker exec welinc_vrms_backend npx prisma migrate status` → "Database schema is up to date!" → AC-17
- [x] `SELECT count(*) FROM repair_tickets WHERE repair_status IN ('COMPLETED','CANCELLED') AND completed_at IS NULL` → 0 → AC-17
- [x] Every ticket created before the migration has exactly one `CREATED` row: `SELECT repair_ticket_id FROM audit_logs WHERE action='CREATED' GROUP BY 1 HAVING count(*) > 1` → no rows → AC-17
- [x] Run the three backfill statements from the migration again by hand → `UPDATE 0`, `INSERT 0 0`, `INSERT 0 0` → AC-17
- [x] Create a ticket through the API → its first audit row is `CREATED` with the creator's user id and email → AC-16
- [x] Unlock a completed ticket and save it with the same status → `completedAt` unchanged and no new `STATUS_CHANGE` row → AC-16b
- [x] As mechanic: `GET /vrms/repairs/audit-logs` and `GET /vrms/repairs/audit-logs/actors` → 403 → AC-18
- [x] As mechanic: `GET /vrms/repairs/history` → no `totalCost` on rows, `summary.spend: null`. A mechanic login with no mechanic record → empty `data` and a zero summary → AC-18
- [x] `grep -rn "audit-logs/all\|getAuditLogs\|AuditEntry\|findAllAuditLogs" welinc-*/src` → nothing → AC-19
- [x] `npm run lint`, `npm run typecheck`, `npm run build` in welinc-web-vrms → pass → AC-20

## Value sourcing checks (vary the source, check the output)
- [x] Summary counts: pick Cancelled → Closed equals Cancelled, Completed is 0, spend is ₱0 → Value sourcing: History summary counts
- [x] Total spend: set one completed ticket's cost to null in the DB → spend drops by that ticket's old cost, nothing breaks → Value sourcing: Total spend
- [x] `closedAt`: a ticket closed at 23:30 local on the last day of a month sits under that month, not the next → Value sourcing: closedAt, Month heading
- [x] Duration: a ticket created 10:00 and closed 09:00 the next day reads "Same day"; closed 10:00 the next day reads "1 day" → Value sourcing: Duration
- [x] Cancellation reason and Locked / Unlocked: cancel with a reason, then unlock → the reason line shows and the badge switches to "Unlocked" for both roles → Value sourcing: Cancellation reason, Locked / Unlocked
- [x] Cost column: as mechanic, check the API response has no `totalCost` (not just a hidden column) → Value sourcing: Cost
- [x] Garage options: block `/vrms/config/garages` → the filter shows only "All garages" and the page still works → Value sourcing: Garage options
- [x] `from`/`to`: switch the browser time zone (DevTools Sensors) to UTC and to Asia/Manila; This month sends a different instant but always local midnight on the 1st → Value sourcing: History filters from, to
- [x] Day heading: an event at 23:59 yesterday reads under "Yesterday"; change the time zone and it can move to another day → Value sourcing: Day heading
- [x] Actor name: update an audit row's email to upper case in the DB → the name still resolves (case insensitive); set it to an email no VRMS user has → that email shows as the name → Value sourcing: Actor name, Actor email
- [x] Actor id: confirm `actor.id` equals the VRMS `users.id` (not the JWT `sub`) → Value sourcing: Actor id
- [x] `actor` null: a backfilled `CREATED` row (and any row with an empty email) uses the no actor wording with no avatar → Value sourcing: actor itself
- [x] Status before and after: a status row with no old value shows only the new badge → Value sourcing: Status before and after
- [x] Cost before and after: an old row with `{"partsCost":null,"laborCost":1000}` reads "₱1,000 → … total" and "Parts ₱0 → …"; a row with unreadable JSON shows only the sentence → Value sourcing: Cost before and after
- [x] Unlock reason and Garage before and after: insert a `SHOP_CHANGE` row by hand → "moved … to a different garage" with "old → new", and the Shop chip shows it → Value sourcing: Unlock reason, Garage before and after
- [x] `CREATED` actor: a ticket created after the migration names its creator; an older one reads "… was created" → Value sourcing: CREATED actor
- [x] `nextCursor`: give 120 rows the same `created_at` by hand, then page through → no repeats, none missing → Value sourcing: nextCursor
- [x] Person options and Person filter match: the list shows names from VRMS users, and picking one returns only rows with that email, matching case insensitively → Value sourcing: Person options, Person filter match

## Acceptance-criteria coverage
- AC-1 history header · AC-2 tiles and mechanic tiles · AC-3 filters, custom range, page reset, 375px · AC-4 columns, reason tooltip · AC-5 month headings · AC-6 row click and menu · AC-7 paging · AC-8 states
- AC-9 audit header and route · AC-10 event layout · AC-11 sentences per type · AC-12 filters on the server · AC-13 load older and its error · AC-14 states · AC-15 reach every row, no repeats
- AC-16 CREATED on create · AC-16b same status save · AC-17 migration and backfill rerun · AC-18 403 and history scoping · AC-18b detail page · AC-19 old endpoint gone · AC-20 tokens, lint, axe, widths
