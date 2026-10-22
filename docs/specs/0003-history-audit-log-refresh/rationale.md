# 0003. Repair history and audit log: decision record

Build spec: [index.md](index.md).

## Context

Scope feature 13 asks for the Repair history and Audit log pages to be restyled on the design system. The engineer's main complaint is that both look like the repair ticket list. They do: all three pages are a search box, a status dropdown, a navy table and a row menu. History only adds Driver, Garage and Cost columns, and the audit log is a table with a free text action column. Yet the jobs are different. The ticket list is a work queue ("what do I act on next?"), history is an archive of closed work ("what happened and what did it cost?"), and the audit log is an activity record ("who changed what, and when?"). Pages that look the same make people unsure which one they're on, and hide the questions each page should answer.

The data limits what the pages can show. `GET /vrms/repairs/audit-logs/all` returns only the newest 50 rows and turns each row into an English sentence on the server ("Changed status of REP-… from PENDING to IN_PROGRESS"), even though `audit_logs` stores the action, field, old value, new value and user id separately. The page then filters and pages those 50 rows in the browser by matching words in the sentence. Only status changes, cost updates and unlocks are written to `audit_logs`; shop changes have their own `shop_change_logs` table that nothing writes to, and ticket creation is not recorded. The audit row keeps the actor's email and user id; names live in the VRMS `users` table.

History is paged on the server (`search`, `status`, `page`, `limit`), so totals for a range can't be added up in the browser. It sorts by `completed_at` descending; the status update code sets `completed_at` for both completed and cancelled tickets, but older and seeded rows have nulls, which Postgres sorts first, so some cancelled tickets jump to the top and show their last update time as the close date. There is no date or garage filter.

The UI refresh phase is built `· Facade` (restyle on the data the app already has, no backend change), and `AGENTS.md` says changes across repos need a spec first. Both repos here (web-vrms and backend-vrms) belong to this team.

## Options considered

### Option 1: Restyle in place

Move both pages onto `DataTable` and the spec 0001 components with today's columns, filters and data, as the scope row describes.

**Pros**:
- Smallest change, pure Facade, no backend work.
- Nothing users rely on moves.

**Cons**:
- The pages still look like the ticket list, which is the engineer's main complaint.
- The audit log stays capped at 50 rows with word matching filters.

### Option 2: New layouts on the existing data (Facade)

Give history month headings and an outcome and duration focus, and turn the audit log into a timeline, all built from what the current endpoints return. Parse the audit sentence on the client to get the type and values, and add up history totals from a large fetch.

**Pros**:
- Visually distinct pages without touching the backend.
- Keeps the phase's Facade rule.

**Cons**:
- Parsing English sentences breaks the moment the wording changes, and cost changes can't show amounts (the sentence doesn't carry them).
- The audit log can still never show more than 50 events, and its filters work only on those.
- History totals would need a 10000 row fetch and would still be wrong past that.

### Option 3: New layouts backed by a small API change

The same two layouts, but the audit endpoint sends structured, paginated, server filtered events, history gains date and garage filters plus a server computed summary, and one migration backfills close dates, creation events and shop changes.

**Pros**:
- Every audit event is reachable, filters are exact, and changes show real before and after values.
- History totals are exact for any filter, at any size.
- Removes the sentence formatter and the 50 row cap for good.

**Cons**:
- Breaks Facade for this feature: a migration and backend deploy.
- More to build and test (keyset paging, backfill, summary query).

## Rationale

The engineer's goal is distinct pages, and the distinction only holds if each page can show what its job needs. An archive needs ranges and totals; a timeline needs every event and its before and after. Option 1 doesn't change the look. Option 2 changes the look but builds the timeline on a sentence parser and a 50 row window, so the page would look like an audit log while hiding most of the audit. Option 3 costs a backend change, but both repos belong to this team, the data already exists in structured form, and the change is additive (nullable columns, new endpoints, extra rows), so it can be rolled back by reverting code. The engineer chose Option 3 knowing it breaks Facade for this feature.

Several smaller calls were made with the engineer. **History layout**: month grouped archive over receipt cards, because it scans faster with many rows and still works as `DataTable` cards on phones. **Audit layout**: day grouped timeline over a structured table, because it reads as "what happened" and looks nothing like the ticket list. **Closed date**: reuse `completed_at` and backfill the old nulls. A new `closed_at` column was considered and dropped once it was clear the status code already sets `completed_at` on cancel; a computed close date was dropped because the history list sorts, filters and pages on it, which Prisma can't do on a value from another table without raw SQL. **Creation events**: write a `CREATED` audit row at ticket creation (no schema change for new tickets) and backfill old tickets without an actor, rather than adding a `createdByUserId` column. **Paging**: a "Load older events" button with a keyset cursor (a bookmark of the last row's time and id) over page numbers, because headings would repeat across pages and offsets skip or repeat rows when new events arrive. **Shop events**: the engineer kept the Shop chip even though nothing writes shop changes yet; to avoid merging two tables under a cursor, existing `shop_change_logs` rows are copied into `audit_logs` once, and future shop changes must write there.

Decided here without a separate question: the event type chips are single select (one tap filters, and All resets), since multi select chips double the filter logic for little gain; the history page size is 20 (the runner up, 10, made month headings repeat on almost every page); history spend counts `COMPLETED` tickets only, matching the dashboard's exclusion of cancelled work; the previous total in a cost event is parts plus labor, since the old JSON never stored a total; day and month headings use the browser's time zone, matching spec 0002.

### Amendment 2026-10-22: actors resolve by email

Found during the `/develop` build. The spec first joined audit actors to `users` by `audit_logs.user_id`. That value is the JWT `sub`, which the auth service issues from its own database, so it never equals the VRMS `users.id` for the same person (for `vrms.admin@welinc.com`, the token carries `3b7a256d…` while the VRMS `users.id` is `c439b079…`). Every actor came back without a name and the Person list was empty. Email is the one identity both services share, and the existing code already relies on it (`getMechanicForUser` matches users by email). So actor name, actor id, the actors list and the Person filter now all go through `audit_logs.email`. Considered and dropped: syncing VRMS user ids to the auth ids (a cross service data change, out of scope for this feature), and storing the actor's name on each audit row (stale after a rename, and still no name for old rows). Accepted cost: backfilled `SHOP_CHANGE` rows carry a user id but no email, so they show no actor, and a user who changes their email loses the link to their older events.
