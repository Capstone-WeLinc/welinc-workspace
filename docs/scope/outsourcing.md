# Outsourcing

Jira WL-E4. In house first; outsourced shops never get accounts. Back to [index](index.md).

## Slice 4: Outsourcing

### 36. Outsourced shop directory · planned
WL-405. An Admin managed list of approved shops.
**Done when:** Admin can add, edit and deactivate shops, and deactivated shops leave pickers but stay on old tickets.
- [ ] Build it: `/develop outsourced shop directory`
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (long shop names and addresses, empty directory)

### 37. Transfer to outsourced shop · planned · needs a decision
WL-401 and WL-404. Outsourcing only when no in house option is free, with a printable job order for the shop.
**Done when:** outsourcing needs a justification or no available in house option, the ticket turns Outsourced with shop, date sent and expected completion, a job order PDF prints, and reports can show the in house vs outsourced ratio.
- Note (2026-11-01, replan): from spec 0014. The outsourced moves (M7 to M13 in its table) are written but off; switch them on through `applyStatusMove` with this feature's trigger. Same for features 38 and 39.
- [ ] Design it (spec): `/architect transfer to outsourced shop`
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (long job order text for the printable page)

### 38. Close outsourced repair · planned
WL-402. Admin or Chief Mechanic uploads the receipt and total cost and marks it done.
**Done when:** closing needs a receipt and a cost in PHP, the receipt counts as proof, and the cost shows in reports.
- [ ] Build it: `/develop close outsourced repair`
- [ ] Polish it (optional, ask first): `web-design-guidelines`

### 39. Management approval for outsourced repairs · planned
WL-403, built on Jira's proposed rules. An approver signs off outsourced work before it closes.
**Done when:** after the receipt upload the ticket waits for approval, the approver is notified and approves or rejects with a reason, and their name and date are recorded.
- [ ] Build it: `/develop management approval`
- [ ] Polish it (optional, ask first): `web-design-guidelines`
