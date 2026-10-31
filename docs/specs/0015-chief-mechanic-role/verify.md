# Verify: Chief Mechanic role · spec 0015 · updated 2026-11-01
_Steps derived from spec 0015 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## UI / manual
- [x] Sign in as the Chief, open `/` → Chief view: four tiles (Waiting for you, My open work, Overdue, Open), then Waiting for your sign off, My work, Needs attention, pipeline, and no spend section → AC-11, AC-13, AC-17, AC-18
- [x] A mechanic sends a ticket for verification, reload the Chief dashboard → it appears in section 1 below older waits, with "Waiting under an hour" in a `<time>` element → AC-7, AC-14, AC-15
- [x] Click "See all" → `/repairs?status=FOR_VERIFICATION` lists the same order → AC-9, AC-14
- [x] Empty the queue → "Nothing waiting for your sign off" and no See all link → AC-14
- [x] The Chief sends their own assigned ticket for verification → missing from section 1 and the tile, present in Needs attention, and its detail page says "Someone else must verify work on a ticket you're assigned to." → AC-16, AC-18
- [x] Admin turns off the Chief's `ticket.verify` in Settings, wait for the refetch → Chief sees the mechanic dashboard; give the Chief `ticket.administer` → admin dashboard → AC-11, AC-12
- [x] Chief opens a ticket and Repair history → costs and the History spend summary show, no cost edit control → AC-3
- [x] Chief opens the close dialog on a ticket with no costs → "No costs recorded yet. An Admin will need to unlock this ticket to add them." with no Go to costs link; as Admin the old note and link show → AC-6
- [x] Settings → Thresholds → "Require costs before closing" is a switch, saved with the Save bar and logged in Change history → AC-4
- [x] With the switch on, a For verification ticket with no costs shows Verify and close disabled with "Add the costs before closing this ticket."; add one part and it enables → AC-5
- [x] Check 375px and 1280px with axe for Chief, Admin and Mechanic; sidebar unchanged for the Chief → AC-19, AC-20
- [x] Vary the clock: a ticket changed 59 minutes, 5 hours and 3 days ago reads "Waiting under an hour", "Waiting 5 h", "Waiting 3 days" (value sourcing: wait time)  → AC-15

## Commands
- [x] `npx prisma migrate status` in welinc-backend-vrms → all applied, and `select count(*) from repair_tickets where status_changed_at is null` → 0 → AC-8
- [x] Re-run `20261101120100_chief_mechanic_costs_view/migration.sql` → permission_matrix.version and permission_changes unchanged → AC-2
- [x] On a copy where an Admin once changed the Chief's `ticket.costs.view` (non null `actor_user_id`), run the migration → row untouched, no new history row → AC-2
- [x] `curl -X PATCH /vrms/repairs/:id/costs` as the Chief → 403 → AC-3
- [x] `PATCH /vrms/repairs/:id/status` to CLOSED with the setting on and no costs → 422 `COSTS_REQUIRED`; with the setting off → 200 → AC-5
- [x] `GET /vrms/repairs?status=FOR_VERIFICATION` → rows ordered by `statusChangedAt` ascending then id; without the status filter the urgency order holds → AC-9
- [x] `GET /vrms/repairs/:id` and a list row both carry `statusChangedAt` → AC-10
- [x] A ticket moved twice has `status_changed_at` equal to its second move's audit row; one with only a CREATED row gets that time → AC-7, AC-8
- [x] `npm run test`, `npm run lint`, `npm run build` in welinc-backend-vrms, and `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build` in welinc-web-vrms → pass → AC-1 to AC-20

## Acceptance-criteria coverage
- AC-1 · AC-2 · AC-3 … covered by the catalog, migration and costs steps · AC-4 · AC-5 · AC-6 … settings and close steps · AC-7 to AC-10 … status_changed_at steps · AC-11 · AC-12 … view choice steps · AC-13 to AC-19 … Chief view steps · AC-20 … sidebar step
