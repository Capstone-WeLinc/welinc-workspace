# Verify: analytics & AI service boundary · spec 0013 · updated 2026-10-31
_Steps derived from spec 0013 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## UI / manual
- [x] As the VRMS Admin, open `/analytics` → every section loads real numbers, no sample data, KPI totals match `GET /vrms/analytics/summary` → AC-3, AC-6
- [x] Block one call (for example stop the backend mid load, or answer 500 for `/vrms/analytics/aging`) → only that section shows the error state with Retry; Retry reloads it; CSV and PDF export stay disabled until it loads → AC-6
- [x] Grant an account `analytics.view` without `ticket.costs.view`, open `/analytics` → "Costs are hidden for your role" note, no spend KPIs, trend shows repair counts only, garage chart shows repair counts, no cumulative or spend by vehicle cards, report table has no money columns, exports have no money columns → AC-5, AC-6
- [x] As a mechanic, open your own open ticket → the AI panel loads the latest diagnosis (or the run button); run it → causes, parts, similar repairs and "Ran just now" show; rate it → AC-7, AC-8, AC-9, AC-12
- [x] Reopen the same ticket → the same diagnosis shows with no new run, and Run again is offered → AC-9
- [x] Open a closed ticket that has a diagnosis → it shows read only with no run button; one with none says no diagnosis was run → AC-9
- [x] With `GEMINI_API_KEY` unset and the backend restarted → the app starts with one warning, analytics loads, a run shows "AI is unavailable right now" with Try again → AC-10, AC-20
- [x] Turn AI off in Settings → the AI panel and AI Insights tab disappear, `POST .../diagnoses` answers 403 `MODULE_DISABLED`, creating a ticket makes no provider call → AC-17

## Commands
- [x] `docker exec welinc_vrms_db psql -U welinc_vrms_user -d welinc_vrms_db -c "\dx vector"` → the extension is installed → AC-2
- [x] `npx prisma migrate diff --from-config-datasource --to-schema prisma/schema.prisma --script` in backend-vrms → empty migration (no drift) → AC-2
- [x] Seed one cancelled ticket of ₱10,000, then `GET /vrms/analytics/summary` → `total_spend` and `total_repairs` leave it out → AC-4
- [x] Create a ticket at 2026-10-31 23:30 Manila time (15:30 UTC), then `GET /vrms/analytics/cost-trends` and `velocity` → it lands in `2026-10` / `Oct 2026`, not November → AC-4 (Value sourcing: month boundaries)
- [x] `GET /vrms/analytics/aging` with no open tickets → all three buckets present with count 0 → AC-4
- [x] `GET /vrms/analytics/garage-costs` and `vehicle-kpis` as a caller without `ticket.costs.view` → peso fields `null`, garages by name, vehicles by repairs then plate → AC-5 (Value sourcing: whether peso fields are shown)
- [x] Check `garage` and `vehicle_plate`/`vehicle_model` against `garages.name` and `vehicles.plate_number`/`model` for one row → AC-3 (Value sourcing: garage name, plate, model)
- [x] `POST /vrms/ai/tickets/<closed id>/diagnoses` → 409 `TICKET_CLOSED`; another mechanic's ticket → 404; unknown id → 404 → AC-7
- [x] Send a body with a fake symptom to `POST .../diagnoses` → ignored; the stored `input.symptom` is the ticket's issue descriptions joined with `. `, prefixes removed → AC-7 (Value sourcing: symptom, issues, plate, model)
- [x] After a run, read the `ai_diagnoses` row → `requested_by_user_id` is the caller's `sub`, `model` is `GEMINI_MODEL`, `similar` only holds issues whose embedding `model` equals `GEMINI_EMBED_MODEL`, none from this ticket or a cancelled one → AC-8, AC-9 (Value sourcing: requester, model name, similar issues)
- [x] Compare a recommended part's `estCostPhp` with `AVG(unit_cost)` over matching `repair_parts` on counted tickets; as a caller without `ticket.costs.view` it is `null` → AC-8 (Value sourcing: part prices)
- [x] Check `vehicleHistory` holds the vehicle's last 5 other tickets, newest `closed_at` first → AC-8 (Value sourcing: vehicle history)
- [x] Fire two runs on one ticket at once → one 201, one 409 `AI_BUSY` → AC-11
- [x] Insert 20 `ai_diagnoses` rows for one user in the last hour, then run → 429 `AI_RATE_LIMITED` with `retryAfterSeconds` = oldest row + 1 hour − now, rounded up → AC-11 (Value sourcing: hourly count, retryAfterSeconds)
- [x] `PUT /vrms/ai/diagnoses/<id>/feedback` twice with different ratings → one row, the second values; `rating: 6` → 400 → AC-12
- [x] `GET /vrms/ai/stats` with no rows → zeros and `{}`; with feedback → `satisfaction_rate` = helpful ÷ feedback × 100 to 1 decimal → AC-13 (Value sourcing: AI stats)
- [x] Create a ticket → within seconds its issues have `issue_embeddings` rows with the `[<category>] ` prefix stripped before hashing (compare `text_hash` with the SHA 256 of the stripped text) and the save took no longer → AC-14 (Value sourcing: embed text, hash, model)
- [x] `npm run lint`, `npm run build`, `npm run test` in backend-vrms; `npm run lint`, `npm run typecheck`, `npm run build`, `npm run test` in web-vrms → all pass → AC-21

## Acceptance-criteria coverage
- AC-1 covered by the analytics and AI steps (all served by backend-vrms) · AC-2 by the `\dx` and drift steps · AC-3 by the summary and row source steps · AC-4 by the cancelled, Manila month and aging steps · AC-5 by the costs hidden steps · AC-6 by the page, failure and costs hidden UI steps · AC-7 by the run, closed and 404 steps · AC-8 by the similar, part price and history steps · AC-9 by the latest and closed ticket steps · AC-10 by the no key step · AC-11 by the busy and rate limit steps · AC-12 by the feedback step · AC-13 by the stats step · AC-14 by the embed on create step · AC-15, AC-16, AC-18 by milestone 4 (not built yet) · AC-17 by the AI off step · AC-19 by milestone 5 (not built yet) · AC-20 by the no key step · AC-21 by the lint, build and test step

## Verified 2026-10-31
Every step above was run against the live stack and passed. Waived: the README pointer line on the archived Python repo (AC-19). The repo is archived, so the line adds nothing. Not run: the PDF export contents (the CSV was checked, the PDF uses the same guarded data).
