# Operations

Lookup lists, deadlines, alerts and the remaining roles (Jira WL-E2, WL-E3, WL-E7, WL-E1). Back to [index](index.md).

## Slice 5: Lookups, deadlines & alerts

### 40. Lookup lists & fewer typed fields · planned · needs a decision
WL-203. Replace free text with Admin managed pickers (issue types, parts, reasons, locations), replacing the hardcoded options in the repair form.
**Done when:** every free text field is either a picker or an optional note, and Admin manages each list without a developer.
- Note (2026-10-25): spec 0007 already makes the repair form's "System" list admin managed (`IssueCategory`, with a categories page). Reuse it as the issue type list instead of building a second one; this feature still owns parts, reasons and locations.
- [ ] Design it (spec): `/architect lookup lists`

### 41. Common issues picker · dropped
WL-704 and WL-702. A curated list of recurring issues that fills in the ticket when picked. Decide how it relates to the existing AI knowledge base (feature G).
**Done when:** Admin and Chief Mechanic manage common issues, the form lists them searchable and most used first, picking one fills type, template, priority and estimate, and Other allows free text.
spec [0007](../specs/0007-knowledge-base-fix-library/index.md)
- Note (2026-10-25): merged into feature 15 (knowledge base page). Spec 0007 builds the common issues library (WL-704) and this picker (WL-702, its AC-24 to AC-26), so the work is tracked and built there. The estimate shows as info only; saving it is feature 42's call.
- [x] Design it (spec): covered by spec 0007

### 42. Deadlines & fix time estimates · planned · needs a decision
WL-206 and WL-207. Expected completion from priority and issue type, with a rule for which wins.
**Done when:** each ticket shows a deadline from creation, Admin configures durations, changes need a logged reason, overdue tickets are highlighted, and the mechanic is warned 24 hours before.
- [ ] Design it (spec): `/architect deadlines & fix time estimates`

### 43. Stuck and stale ticket alerts · planned · needs a decision
WL-302 and WL-303, built on proposed defaults. A scheduled check flags tickets stuck in Pending and escalates ones untouched for 30 days.
**Done when:** the threshold is Admin configurable, stuck tickets get a tag and a filter, and stale ones escalate weekly and show on a report.
- [ ] Design it (spec): `/architect stuck and stale ticket alerts`

### 44. Driver role · planned · needs a decision
WL-105. Jira has no proposed rules yet: decide whether drivers log in or are just names on a ticket.
**Done when:** the decision is recorded and, if a role is needed, drivers can record drop off and pick up at outsourced shops.
- [ ] Design it (spec): `/architect driver role`
