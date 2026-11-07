# 0023. Per ticket checklist edits: rationale

Back to [index](index.md).

## Context

Spec 0007 copies a known fix's steps onto a ticket's issue (`RepairIssueStep`) when the fix is linked, and lets the people working the ticket tick them while it is In progress. Nothing else can change a copied step. When the known fix misses a step, has one that does not fit this truck, or orders them badly, the mechanic either ignores the checklist or works around it, and the verifier cannot tell which steps really guided the work. Issues with no linked fix have no checklist at all.

You want the checklist to stay a helper for this ticket: editable per ticket, while the knowledge entry stays unchanged. That brings several forces into play:

- **Trust in the trail.** Spec 0021 made every ticket action write an audit row, including each tick, and made the log append only. Edits to the steps must fit that, or the ticks lose their meaning (a ticked step reworded into something else).
- **Concurrency.** Several people can hold a ticket open (the mechanic on a phone, the Chief, the Admin), and the page polls every 3 seconds. Spec 0019 locks ticket edits on the ticket's `updatedAt`; spec 0007 kept ticks off that lock on purpose, so ticking never makes another edit go stale.
- **Rights.** Spec 0011 says every new action gets its own key in the matrix. Ticking today rides on `ticket.work` (own tickets) and `ticket.administer` (any ticket), which leaves the Chief ticking only their own tickets.
- **Phones.** Mechanics work at 375px, so the edit surface must not crowd the tick targets (44px rows).

If nothing is decided, the checklist stays rigid and gets ignored, which undercuts the knowledge base's main use on the floor.

## Options considered

### Option 1: A full list save per issue, guarded by the issue's own lock

One dialog per issue edits the whole list; Save sends the ordered list to one `PUT`, which diffs it against the stored rows in a transaction, locked by a `checklistVersion` counter on the issue.

**Pros**:
- One request, one transaction, one prompt for every change in a session.
- The same pattern as knowledge entry steps (full replace) and spec 0019's mechanics `PUT`.
- The issue lock keeps checklist saves off the ticket's lock, so no new 409s elsewhere.

**Cons**:
- The server has to work out the diff (kept, reworded, moved, added, removed), including a minimal moved set.
- The relink path still checks the ticket lock, leaving a short window where a relink replaces fresh edits.

### Option 2: One endpoint per step action

`POST` add, `PATCH` reword, `PATCH` move, `DELETE` remove, each saved at once from a row menu.

**Pros**:
- Each request is trivial and its audit row is obvious.
- No diff logic.

**Cons**:
- Many requests on a weak phone connection, each with its own failure and retry.
- Reordering by single moves is chatty, and partial failure leaves a half edited checklist.
- No single place to warn about ticked steps before a batch of changes.

### Option 3: Edit in place, locked on the ticket like spec 0019

The checklist turns editable in place and saves with the ticket's `lastUpdatedAt`, stamping the ticket as edited.

**Pros**:
- Consistent with every other ticket edit.
- No new lock to explain.

**Cons**:
- Every checklist save would 409 anyone else holding the ticket open, on the most frequently touched part of the ticket.
- Editing and ticking share one area at 375px and are easy to mix up.

## Rationale

The checklist is the part of a ticket people touch most while the work happens, so its saves must not collide with the rest of the ticket. That rules out Option 3. Spec 0007 already kept ticks off the ticket lock for the same reason. The first draft reused the issue's `updatedAt` as the checklist lock, but the cross check found six other paths that move it (resolution notes, the `resolvedAt` reset on a move back, suggestion dismissal, approved suggestions, issue edits, links), which would have made open dialogs fail for unrelated reasons. A dedicated `checklistVersion` counter, raised only by the paths that change steps, costs one column in the migration already planned and gives the checklist a lock that means exactly one thing.

Between Options 1 and 2, the phone and the audit trail decide it. A mechanic on mobile data is better served by one save that succeeds or fails as a whole than by a run of small requests that can stop halfway. One save also gives one place to warn before ticked steps are removed or lose their tick, which is what keeps the spec 0021 trail honest. The cost is the diff on the server; it is a small pure function and easy to test, and computing the moved set as the steps outside the longest kept run keeps the log to one row per real move.

The new key follows spec 0011 instead of riding on `ticket.work`. Scoping it by `ticket.view_all` gives you what you asked for (all roles on, the mechanic limited to their own tickets) within a matrix whose keys cannot carry a different scope per role. The Chief can therefore adjust the plan on any ticket they can see, which fits their supervising role, while ticking keeps its current rules.

## Update 2026-11-06: a lighter sheet with drag

The first build worked, but each row carried a bordered field plus three buttons (Move up, Move down, Remove). At 375px that is a wall of controls, and moving step 6 to the top took five taps. You chose a lighter row (handle, number, a field that shows its border only on hover or focus, a tick mark, Remove) and dragging instead of the buttons.

Drag options weighed:

- **`@dnd-kit/sortable` (chosen)**: keyboard dragging and screen reader announcements are built in, touch works through pointer events, and a handle only drag keeps the sheet scrollable on a phone. Con: four packages and one more library to keep current.
- **Native HTML drag and drop**: no dependency. Con: no touch support on phones and no keyboard path, so the buttons would have to stay, which defeats the point.
- **`@dnd-kit/react` (the newer API)**: the library's future. Con: still settling, fewer examples, and the installed skill covers the classic API.
- **Keep Move up and Move down only**: nothing new to learn. Con: the crowded rows and the many taps this update exists to fix.

The Move buttons go away because the handle gives keyboard users the same power (Space, arrows, Space), with spoken instructions. Keeping both would bring the clutter back.

**The tie rule.** When several runs of kept steps are equally long, the first build kept the run that ends earliest in the new order. That logs "Step 5 → step 6" when someone drags step 6 above step 5, which is not what they did. Keeping the run through the lowest old positions logs "Step 6 → step 5" instead, which matches the usual drag of a later step upward, and it gives one clear answer on every tie. The rule stays on the server, worked out from the old and new order, so the web never has to report what it moved and the audit row cannot be faked by a client.

**Approved suggestions and own steps** (decided during the build). An approved knowledge suggestion links the entry to matching issues. If an issue already has steps (its own, or ones edited on the ticket), replacing them silently would throw away work, with no one there to answer a prompt. So those steps stay, and only an issue with no steps gets the entry's steps and the `checklistVersion` bump.
