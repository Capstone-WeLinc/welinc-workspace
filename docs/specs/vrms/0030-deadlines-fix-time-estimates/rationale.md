# 0030. Rationale: due dates from priority, issue types and history

Back to the [spec](index.md).

## Context

VRMS tickets have had a `dueAt` column since spec 0010, and the list already sorts by it, filters overdue tickets and shows "Overdue" on the dashboards. But nothing sets it: only the seed writes a date, so every ticket created in the app has none. Jira asks for two ways to set it: WL-206, a target fix time per priority, recomputed when the priority changes; and WL-207, a duration per issue type, a logged reason for an Admin's change, and a warning to the mechanic 24 hours before. Both stories leave open the hours themselves and which rule wins when they disagree.

The date now matters outside VRMS. Spec 0029 (flow 3) sends it to BMS as the truck's expected return date, and BMS flags bookings and Job Orders before it. A date that is too early causes false rebookings; one that changes for no visible reason sends BMS noise. Spec 0029 child 0003 already made `setDueAt` the only writer of the date, with an audit row and a BMS update on every change.

The knowledge base (spec 0007) already knows how long known fixes really take: the median `hoursSpent` of closed repairs, shown once a fix has `knowledge.min_samples` of them. Settings (spec 0012) hold single numbers and yes or no values, not lists; issue types are the Admin managed `IssueCategory` list. VRMS has no notifications yet (feature 28 is planned), and the browser can't read settings (they need `settings.manage`).

The deadline is close (the final by Dec 20 at the latest), so the design has to be small enough to build in about a day and a half, yet realistic enough to defend.

## Options considered

### Option 1: Work the date out on read

Store only the inputs and compute the due date every time a ticket is listed or opened, from the current settings and history.

**Pros**:
- Always reflects the current settings and knowledge base, no backfill needed.
- No writes on create or edit.

**Cons**:
- The date drifts on its own as history grows or an Admin saves a setting, and BMS never hears of it (or hears of it on every read).
- Sorting and the overdue filter need a stored column; the list query would have to repeat the rule in SQL.
- No audit row explains why a date moved.

### Option 2: One calculator, stored at fixed moments, written through `setDueAt` (chosen)

A pure function works out the date at create, priority change, issue changes and known fix links; the result is stored through `setDueAt`. Hand changes and resets use the same writer.

**Pros**:
- Dates change only when something about the ticket changes, so BMS gets real changes only, each with a reason.
- One tested function holds every rule; the existing index, sort and overdue filter keep working.
- Every change is audited by the writer that already exists.

**Cons**:
- Needs a backfill for open tickets without a date.
- A settings change doesn't reach existing tickets (accepted on purpose, AC-7).
- Every path that changes priority or issues must remember to call it (mitigated by the call table in the spec and tests on each path).

### Option 3: A database trigger

A Postgres trigger works out `dueAt` on insert and update of tickets and issues.

**Pros**:
- No path can forget to call it.

**Cons**:
- The rule needs settings, the knowledge base medians and the module switch, which live in application code.
- It bypasses `setDueAt`, so no audit row and no BMS update without duplicating that logic in SQL.
- Harder to test and to explain at the defense.

## Rationale

Option 2 fits the force that matters most now: the date is a promise to another system. BMS plans around it, so it must change only when something real changes, and every change must carry a reason. Working it out on read (Option 1) breaks that by letting the date drift, and a trigger (Option 3) can't reach the audit and outbox code that spec 0029 already built. Option 2 reuses `setDueAt` as is, plus one flag so create doesn't send BMS two updates.

The rules follow the same force. "The later of the two" keeps the date from promising a truck back before the work can be done; summing issues matches one crew per bay; the knowledge base first makes dates learn from real repairs, while storing them keeps that learning from moving dates nobody touched. The escalation rule (now plus the priority hours) is what a shop means by raising a ticket to Critical, and it avoids a ticket going red the moment it is escalated. Priority hours of 8, 24, 72 and 168 follow the usual fleet shop tiers (truck down same day, then a day, three days, a week); under "the later of the two" they act as a floor, so Critical must stay short.

The 24 hour warning becomes Due soon on the screens instead of a message, because there is no notification channel and building one belongs to feature 28. The window shrinks to half the fix time for short tickets so that Due soon always means the time is running out. `dueSoonAt` is worked out on the backend because only the backend can read the setting, and the browser still compares it to its own fetch time, as the due helpers already do.

The hand change goes on the existing ticket detail page (your rule: new views on existing pages first) and opens to the Chief Mechanic as well as the Admin through one permission, so it can be switched per role in the permission matrix. The reason is free text for now and becomes a picker once feature 40's reasons list exists.
