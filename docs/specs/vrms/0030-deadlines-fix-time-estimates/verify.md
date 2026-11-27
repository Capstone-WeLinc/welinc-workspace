# Verify: Deadlines & fix time estimates · spec 0030 · updated 2026-11-27
_Steps derived from spec 0030 acceptance criteria and its Value sourcing table. `/check verify` runs these; `/test` locks the durable ones._

Before you start: the stack is up, `docker exec welinc_auth_service npm run catalog:sync` has run (the `ticket.due_date.edit` key), and `npm run due:backfill` has run in the backend container. Sign in on the portal as `vrms.admin@welinc.com`, a Chief Mechanic and a Mechanic (see `docs/integration/seed-accounts.md`).

## UI / manual
- [ ] As Admin, create a High ticket with a Brakes issue and an Engine issue → the Due row says about 54 h from now (the date and time, "in 2 days"), and the ticket's history shows "Due date from issue times (54 h: Brakes 6 h, Engine 48 h)" → AC-1, AC-3
- [ ] Create a Critical ticket with one General issue → due 8 h after creation, history says "Due date from Critical priority (8 h)" (a tie or a smaller issue sum goes to priority) → AC-1, AC-2
- [ ] Settings, Due dates: the five settings show with their defaults (8, 24, 72, 168, and 24 for the warning); a value outside its range is refused → AC-2
- [ ] Settings, Lookup lists, Categories: the Fix time column shows Brakes 6 h to General 4 h; edit a category to 0.25 and 720 (saved), 0.1 and 721 (refused), and blank (clears it) → AC-4
- [ ] Link an issue to a known fix with at least `knowledge.min_samples` closed repairs → the date uses its typical hours and the history says "from N past repairs"; with fewer, the fix's estimate counts; with the Knowledge base module off, only the category's fix time counts → AC-3
- [ ] On an open automatic ticket: change the priority, add an issue, change an issue's system, remove an issue, and relink its known fix → each move works the date out again from creation, with the matching prefix ("Priority changed. ", "Issue added. " and the rest) in the history → AC-5
- [ ] Reword an issue without changing its system → the date stays and no due date row is written → AC-5
- [ ] On a ticket created 3 days ago at Medium, raise it to Critical → the date becomes now plus 8 h, and the history says "Raised to Critical after its time had passed" → AC-6
- [ ] Raise High to 48 h in Settings → an existing High ticket keeps its date, a new High ticket uses 48 h → AC-7
- [ ] Change a category's fix time → no existing ticket's date moves → AC-7
- [ ] As Chief Mechanic, open a ticket and click Change on the Due row → set a date 3 days out with a reason → saved, the Due row shows it, the history row carries the reason → AC-8
- [ ] In that dialog, try a past time and one 91 days out → refused with a message, nothing saved → AC-8
- [ ] As Mechanic → no Change action on the Due row; `PUT /vrms/repairs/:id/due-date` answers 403 → AC-8
- [ ] On the hand set ticket, open Change, pick "Use the automatic date" → the preview shows about the date and its reason; save with a reason → the date is the worked out one and the source is automatic again → AC-9
- [ ] Change the priority of the hand set ticket → its date stays → AC-5
- [ ] Close a ticket → no Change action; the date stays; it never shows Overdue or Due soon. Unlock it and add an issue → the date still stays → AC-14
- [ ] Open the same ticket in two tabs, change the date in the first, then save in the second → the second says the ticket changed and reloads, nothing written → AC-15
- [ ] A Critical ticket (8 h) shows "Due soon, in 3 h" once 4 h are left; a Low ticket (168 h) only once 24 h are left → AC-11
- [ ] Due soon and Overdue show on the repair list's Due column, the ticket's Status card, the Admin and Chief dashboards, and the Team panel; under 24 h the text counts hours ("Due in 5 h"), else days → AC-12
- [ ] As Mechanic, the dashboard shows an Overdue group, then a Due soon group, then Later, each only when it has tickets → AC-12
- [ ] An On hold or Outsourced ticket past its date shows Overdue → AC-14

## Commands
- [ ] `docker exec welinc_vrms_backend npm run due:backfill` on a database with open undated tickets → "Done: N of N open tickets got a due date."; run again → "Nothing to do" → AC-13
- [ ] After the backfill, `select count(*) from repair_tickets where due_at is null and repair_status not in ('CLOSED','CANCELLED')` → 0 → AC-13
- [ ] For a ticket on a VMMS linked truck: each due date change writes one `REPAIR_UPDATE` delivery whose `changeReason` is the history note, and create sends exactly one → AC-10
- [ ] Save a hand date equal to the current one → 200, no new audit row, no new delivery → AC-10
- [ ] `PUT /vrms/repairs/:id/due-date` with a `dueAt` without an offset → 400 → API surface
- [ ] `POST /vrms/repairs/:id/due-date/automatic` on an automatic ticket → 409 `NOT_MANUAL`; on a closed one → 409 `TICKET_NOT_OPEN` → AC-9, AC-14
- [ ] Staging, after the deploy: `npm run due:backfill` once, then `catalog:sync` in welinc-auth → Migration plan phase 2

## Value sourcing
- [ ] Priority hours come from the settings, not code: set Medium to 10 h, create a Medium ticket → due 10 h out
- [ ] Each issue's hours: knowledge typical hours, else the fix's estimate, else the category's fix time, else 0 (vary one at a time as in the steps above)
- [ ] The anchor is `created_at`: recompute a 2 day old ticket and check the new date counts from its creation, not from now (unless AC-6 applies)
- [ ] The AC-6 "now" is the request's: the escalated date is the save time plus the priority hours
- [ ] The hand change checks against now and now plus 90 days (server clock), whatever the browser's clock says
- [ ] The reason is the typed one for a hand change and reset, the rule text for automatic writes, and BMS's `changeReason` is the same text, with no issue description in it
- [ ] `dueSoonAt` on the list, detail and dashboard replies is `dueAt` minus the smaller of the setting and half the ticket's time; change `tickets.due_soon_hours` to 2 and check a Low ticket turns Due soon only 2 h before
- [ ] The label text is the browser's: change the computer's time zone and check the Due row shows the date in local time with the same hours left
- [ ] The mechanic's Due soon group follows each row's `dueSoonAt` against the fetch time (no new route is called)
- [ ] The backfill uses the run's now: an old open ticket gets now plus its priority hours

## Acceptance-criteria coverage
- AC-1: steps 1, 2 · AC-2: 2, 3, value 1 · AC-3: 1, 5 · AC-4: 4 · AC-5: 6, 7, 15 · AC-6: 8 · AC-7: 9, 10 · AC-8: 11 to 13 · AC-9: 14, command 6 · AC-10: commands 3, 4 · AC-11: 18, value 7 · AC-12: 19, 20 · AC-13: commands 1, 2 · AC-14: 16, 21, command 6 · AC-15: 17
