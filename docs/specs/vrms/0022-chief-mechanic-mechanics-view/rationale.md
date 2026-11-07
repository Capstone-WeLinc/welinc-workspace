# 0022. Chief dashboard rework: decision record

Back to [index.md](index.md).

## Context

Feature 57 put each mechanic's workload on Admin's Users page, which the Chief Mechanic cannot open. The first version of this spec (2026-11-04) gave the Chief a separate read only `/mechanics` page on a new VRMS roster read. It was built, and on review (2026-11-05) it did not hold up: 69 near identical rows of "Free, 0, 0, 0, 0", counts where a foreman thinks in plates, and nothing the Chief cannot already see standing on the shop floor. Adding it to the nav also forced a phone tab bar rule that still left the default Chief on the sheet menu, because they also hold Settings.

The Chief's real moments, worked out in the review, are the morning lineup (who holds which truck, and its state), covering for an absent mechanic (see one person's tickets and move them), and spotting stuck or piled up work (overdue, long on hold, one person holding too much). Picking someone for a new breakdown is already served by the Assign picker's counts and busy flag. The Chief spends the day on the floor, on a phone.

The Chief dashboard (spec 0015) was also judged confusing: four count tiles that repeat the lists below them, three tables with different column orders (two lead with the ticket ID against design.md's plate first rule), a "Needs attention" table whose overdue and inactive mechanic rows are really about people, and a pipeline bar that mixes open tickets with this month's closed ones under shared percentages.

## Options considered

### Option 1: Rework the Chief dashboard with a Team section, remove `/mechanics` (chosen)

Three sections (Sign off, My work, Team), one ticket row style, Team built from the dashboard's open tickets joined to the roster, Needs attention folded into Team, tiles and pipeline removed.

**Pros**: serves all three moments where the Chief already lands; says each thing once; no nav change; reuses the built backend and the Users page ticket list.
**Cons**: throws away much of the first build's web code; the Chief loses the pipeline and the Open and Overdue totals; the Chief and Admin dashboards drift further apart.

### Option 2: Keep `/mechanics`, redesigned as a board

Summary tiles, groups (working, waiting, free), plates inline.

**Pros**: a dedicated place with room for filters; little dashboard change.
**Cons**: one more place to visit on a phone for a daily glance; the phone nav question stays open; the confusing dashboard stays as it is, and its Needs attention would overlap the board.

### Option 3: A dashboard card plus the full page

**Pros**: a glance and a deep view.
**Cons**: the most surface to build and keep in step, for a roster of about 70 that fits one card.

### Option 4: Drop the feature

**Pros**: nothing to maintain; the Assign picker already shows load.
**Cons**: the lineup, absent mechanic and stuck work moments stay unserved.

## Rationale

The deciding force is where and how the Chief works: on the floor, on a phone, starting from the dashboard. A separate page asks them to go somewhere else for a daily glance, while the dashboard is where they already are. Folding Needs attention into Team works because its rows are about people (overdue work, a mechanic who left), and a person row shows that with the context of everything else that person holds. Tickets with no mechanic at all are the only ones without a person, so they get a small group of their own.

Plates beat counts because that is how a foreman names work (design.md, "Naming a ticket"). Time in status and the existing overdue rule flag stuck work without a new threshold to tune; a Settings threshold was the runner up and can come later if "On hold · 9 days" proves too subtle.

The sort leaves Occupied out on purpose. A list that refreshes every 3 seconds and sorts on Occupied would jump the moment someone presses Start work, which is exactly what happens during a lineup. Sorting on inactive, overdue and ticket count moves a row only when work is given, finished or goes overdue, a few times a day, so live re-sorting stays steady without the first version's "Sort again" button.

Reassign and Unassign in the person dialog reuse the Users page list, which already saves through the assignments route with the stale check and audit rows, and the server still checks `ticket.assign`. That turns covering for an absent mechanic from four steps per ticket into two.

The two column layout puts the Chief's own queue in a narrow left column and Team in the wide right one, so the visual order matches the reading and phone order (Sign off, My work, Team). The review first sketched Team on the left; it was swapped so keyboard and screen reader order follow what sighted users read.

The roster keeps its own poll (the built hook) rather than joining the dashboard's single fetch, so a roster failure only blanks Team. The cost is a few seconds where a brand new assignment shows under a fallback row named from the ticket.

### Superseded first version (2026-11-04)

Chose a separate `/mechanics` route with filters in the address, a load order fixed at load with "Sort again", links only (no Unassign or Reassign), and Mechanics replacing Knowledge base on the Chief's phone tab bar. Built, then replaced on review for the reasons in Context.

### Second design review pass (2026-11-05)

The first built layout was reviewed with the engineer and read as templated: four number cells of equal weight where only one number is something to act on, a grid of equal boxes for the team that could not be compared at a glance, and a sentence of up to 46 names under the free people. Three choices came out of it.

**The top of the page.** One summary with the verification count and a single action (chosen), over four equal count cells (the first version). The count the Chief acts on is the biggest thing on the page, and the rest of the numbers are said once as a small line, because "free" and "working" need no action. Runner up: keep the four cells but make the first one larger. Not chosen: it still shows four numbers of equal weight, and the Free count was the loudest number on a screen where it matters least.

**The team.** Rows with a workload bar (chosen), over person cards. Rows are one height, so people line up and the bars compare load down the list; cards varied in height, left gaps, and repeated the same name, pill and rows pattern. A bar answers "who is overloaded or idle" without reading, and the trucks open in place, because the lineup needs plates only when one person is picked. Cost: the bar and the roster `total` can differ for a few seconds, since they come from different reads.

**Free people.** A Busy and Free switch (chosen), over a Free section under the list. Busy is where the Chief acts, so it opens first; Free is one tap away with its count on the tab, in two columns instead of a sentence. Runner up: a Free section with columns under the list; it made the Team panel very long on a phone.

**Colour.** One family: navy for work, a light navy for not started, violet only for verification, red and amber only for trouble (overdue work, long waits). The status words on every truck line went, because many colours on one screen meant none of them marked anything. Wait limits of 24 and 48 hours are fixed in code for now; the Settings threshold runner up above still applies.
