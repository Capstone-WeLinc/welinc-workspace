# 0015. Chief Mechanic role: rationale

Back to [index.md](index.md).

## Context

The `CHIEF_MECHANIC` role exists since spec 0007. Spec 0011 lets it read every ticket, and spec 0014 lets it verify and send back work it did not do itself. But the web app still treats the Chief as a mechanic: `DashboardPage.tsx` picks the view from `ticket.work` without `ticket.administer`, so the Chief lands on the mechanic dashboard, which shows only their own assigned work. Nothing shows them what waits for their sign off, or what is happening across the three garages.

The repair list already filters by status (`/repairs?status=FOR_VERIFICATION`), but it sorts by urgency (`dueAt`, then newest). Nothing records when a ticket entered For verification. `lastActivityAt` moves with any audited action (a cost edit, a remark), so it can't order a fair queue.

Costs are Admin only today. In real garages the head mechanic (shop foreman) sees parts and labor to check work, while the service or fleet manager sets prices and budgets. Changing the Chief's default is not just a catalog edit: the startup backfill only inserts missing permission rows and never updates an existing one (`permissions.service.ts`), so every database that already has the Chief's row would keep it off.

The team decides without stakeholder input, and the deadline is the end of November 2026, so the change must reuse what exists: no new page (your preference), permission based screens (spec 0011), and the transition table (spec 0014).

## Options considered

### Option 1: Chief view on the existing dashboard, queue first (chosen)

A third view chosen from permissions: queue, own work, attention across garages, pipeline. The full queue is the existing list, filtered and sorted oldest first.

**Pros**: no new page or nav item; reuses the dashboard data hook and helpers; queue is the first thing the Chief sees.
**Cons**: a third view to maintain; one more dashboard variant to test at two widths.

### Option 2: Admin dashboard minus spend

Route the Chief to the admin view and hide the spend cards.

**Pros**: the least new UI.
**Cons**: the Chief's own assigned tickets vanish from their first screen; waiting tickets sit mixed into Needs attention in urgency order, not as a queue.

### Option 3: A dedicated verification page

A new `/verification` page and sidebar item.

**Pros**: most discoverable; room for verification tools later.
**Cons**: a second sidebar item for what is the repair list with one filter; against your rule of extending existing pages.

### Sub decisions

| Question | Chosen | Runner up and why not |
|---|---|---|
| Who owns the queue | Feature 17 | Feature 23: the Chief would have no queue until proof files exist |
| Costs | Read only by default | No costs: the Chief would verify without seeing an odd cost |
| Spend cards | Not on the Chief view | Show them: puts budget numbers on the work floor screen |
| History spend total | Keep (follows the key) | A new spend key: one more permission and migration for a small gain |
| Audit log | Stays Admin only | Open it: exposes account and permission changes |
| Garages | All for now | Own garage only: needs feature 59's home garage first |
| Assigning | Later, with feature 53 (default on there) | Now: no reassign endpoint exists yet |
| Rollout of the cost default | Guarded one off data migration | Change the backfill to update: weakens spec 0011 AC-3 for every key |
| Queue time source | New `status_changed_at` column | Read the audit log per request: a join on a paged list |
| Queue order | Oldest waiting first | Urgency order: a low priority truck can wait indefinitely |
| Own tickets in the queue | Left out of the dashboard queue | Shown, marked: the top of the queue would be things they can't act on |
| Queue entry | Dashboard See all only | A sidebar item: duplicates Repair tickets |
| Fallback when rights change | Mechanic view | Chief view with hidden sections: role based, more conditions |
| Closing without costs | Allowed by default, Admin setting to require costs | Always block: in most shops the truck leaves before invoices arrive, so blocking holds trucks for paperwork |

## Rationale

The Chief's job is oversight plus sign off, so their first screen should answer "what is waiting for me" before anything else, and then give the garage wide picture the admin view already computes. Option 1 does that with the parts that exist: `useDashboardData`, `attentionList`, `pipelineCounts`, `mechanicWorkList`, and the server's `can.verify` and `can.work` flags. Keeping the full queue on the existing list avoids a duplicate page and follows the "extend existing pages" rule.

A real column for the time of the last status change is the boring, correct fix: one write inside the transaction `applyStatusMove` already runs, an index, and a backfill from the audit log the project already trusts. It also serves later features that need time in status.

For costs, the shop foreman split (see work and parts, not prices or budgets) gives read only costs without spend. Real shops separate technical completion (the truck is released) from the financial close (invoices posted later), so closing without costs stays allowed by default; the setting serves garages that want the stricter rule, and the real fix (costs after close) is recorded as its own feature. The guarded data migration is the smallest way to make every existing database agree without changing the backfill's promise that a person's edit always survives.
