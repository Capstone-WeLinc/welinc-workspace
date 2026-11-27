# Operations

Lookup lists, deadlines, alerts and the remaining roles (Jira WL-E2, WL-E3, WL-E7, WL-E1). Back to [index](index.md).

## Slice 5: Lookups, deadlines & alerts

### 40. Lookup lists & fewer typed fields · planned · needs a decision
WL-203. Replace free text with Admin managed pickers (issue types, parts, reasons, locations), replacing the hardcoded options in the repair form.
**Done when:** every free text field is either a picker or an optional note, and Admin manages each list without a developer.
- Note (2026-10-25): spec 0007 already makes the repair form's "System" list admin managed (`IssueCategory`, with a categories page). Reuse it as the issue type list instead of building a second one; this feature still owns parts, reasons and locations.
- Note (2026-10-29): the lists are managed from the Settings hub (feature 52), not on pages of their own.
- Note (2026-10-30): spec 0012 built the Lookup lists section of the hub with issue categories on `lookups.manage`. Add parts, reasons and locations there.
- Note (2026-11-01, replan): from spec 0016. Generic `LookupValue` lists already exist (vehicle types, corporations). Move root causes and other plain lists into them.
- Note (2026-11-27, from spec 0030): the due date dialog's reason becomes a picker plus an optional note once the reasons list exists.
- [ ] Design it (spec): `/architect lookup lists`
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (long list items, empty lists, many items)

### 41. Common issues picker · dropped
WL-704 and WL-702. A curated list of recurring issues that fills in the ticket when picked. Decide how it relates to the existing AI knowledge base (feature G).
**Done when:** Admin and Chief Mechanic manage common issues, the form lists them searchable and most used first, picking one fills type, template, priority and estimate, and Other allows free text.
spec [0007](../../specs/vrms/0007-knowledge-base-fix-library/index.md)
- Note (2026-10-25): merged into feature 15 (knowledge base page). Spec 0007 builds the common issues library (WL-704) and this picker (WL-702, its AC-24 to AC-26), so the work is tracked and built there. The estimate shows as info only; saving it is feature 42's call.
- [x] Design it (spec): covered by spec 0007

### 42. Deadlines & fix time estimates · in-progress
WL-206 and WL-207. Expected completion from priority and issue type, with a rule for which wins.
**Done when:** each ticket shows a deadline from creation, Admin configures durations, changes need a logged reason, overdue tickets are highlighted, and the mechanic is warned 24 hours before.
- Note (2026-10-30): spec 0012 follow up. Add the duration settings as entries in the settings catalog (Thresholds section), not code constants.
- Note (2026-11-01, replan): from spec 0015. Default the Chief Mechanic to **on** for setting fix time estimates. Reuse `repair_tickets.status_changed_at` for time in status.
- Note (2026-11-03, replan): from spec 0019. Admins can now change a ticket's priority after create. Decide whether that recomputes a `dueAt` that came from priority.
- Note (2026-11-21, integration talks): the due date becomes the **expected return date** BMS plans around (feature 56, flow 3 "Repair impact on bookings"). VRMS sends BMS every set or change of `dueAt`, and BMS flags bookings before it. This makes the feature a dependency of the integration defense (Dec 4), so design it with feature 56. Recommended answer to the priority question above: recompute only when `dueAtSource` is `PRIORITY` or `ISSUE_TYPE`, never `MANUAL`, and send BMS the new date either way. Inside VRMS it stays "due date"; toward BMS it's "expected return date".
- Note (2026-11-27, replan, from spec 0029): write `dueAt` only through child 0003's `setDueAt`, so BMS hears every change.
- Note (2026-11-27, `/architect`): spec [0030](../../specs/vrms/0030-deadlines-fix-time-estimates/index.md). One calculator, stored at create and on priority, issue, known fix, referral and expedite changes, written only through `setDueAt`. The later of priority hours (8, 24, 72, 168 by default) and the summed issue hours (knowledge base typical hours, then the fix's estimate, then the category's fix time); calendar hours from `createdAt`, now plus the priority hours when that is already past. Hand change and reset with `ticket.due_date.edit` (Admin and Chief Mechanic). Due soon at the smaller of 24 h and half the fix time. A one time `due:backfill`.
- Code: `welinc-backend-vrms/src/modules/vrms/due-dates.ts` (the calculator), `due-backfill.ts`, the due date routes in `ticket-edits.service.ts`; `welinc-web-vrms/src/features/repair/components/due/DueDateDialog.tsx`, `src/lib/utils/due.ts`; the permission in `welinc-auth/prisma/catalog/vrms.ts`. Branch `feat/deadlines-fix-time-estimates` in all three
- [x] Design it (spec): `/architect deadlines & fix time estimates`
- [ ] Build it: `/develop deadlines & fix time estimates`
  - [x] Priority dates end to end: the five settings, `computeDueAt`, create through `setDueAt`, `dueSoonAt`, hours in the due labels (AC-1, AC-2, AC-6, AC-10, AC-11)
  - [x] Issue hours: `fix_hours` migration and the categories page, the knowledge first sum, every recompute path, the seed (AC-3, AC-4, AC-5, AC-7)
  - [x] Hand change and reset: the permission, the PUT and `automatic` routes, the Change dialog on the ticket's Due row (AC-8, AC-9, AC-14, AC-15)
  - [ ] Due soon on screens and the backfill: chips, the mechanic's Due soon group, `npm run due:backfill` locally and on staging (AC-12, AC-13). Built and run locally 2026-11-27; the staging run waits for the deploy
- [x] Verify it: `/check verify deadlines & fix time estimates`. Passed locally 2026-11-27 (all AC-1 to AC-15, 37 of 38 steps); the staging backfill and `catalog:sync` wait for the deploy
- [x] Test it: `/test deadlines & fix time estimates`. 2026-11-27: 35 new tests in 4 specs (recompute, route DTOs, category fix time, setDueAt source only); backend 1,922 and web 766 pass
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (overdue by years, due today, missing estimates)

### 43. Stuck and stale ticket alerts · planned · needs a decision
WL-302 and WL-303, built on proposed defaults. A scheduled check flags tickets stuck in Pending and escalates ones untouched for 30 days.
**Done when:** the threshold is Admin configurable, stuck tickets get a tag and a filter, and stale ones escalate weekly and show on a report.
- Note (2026-10-30): spec 0012 follow up. Add the stuck and stale thresholds as entries in the settings catalog, not code constants.
- Note (2026-11-01, replan): from spec 0015. Measure time in status with `repair_tickets.status_changed_at`, not the audit log.
- Note (2026-11-05, replan): from spec 0022. The Chief dashboard colours a For verification wait amber at 24 hours and red at 48, fixed in code. Decide here whether those limits become Admin thresholds beside the stuck one, so there is one set of waiting rules.
- [ ] Design it (spec): `/architect stuck and stale ticket alerts`
- [ ] Polish it (optional, ask first): `web-design-guidelines`

### 44. Driver role · planned · needs a decision
WL-105. Jira has no proposed rules yet: decide whether drivers log in or are just names on a ticket.
**Done when:** the decision is recorded and, if a role is needed, drivers can record drop off and pick up at outsourced shops.
- [ ] Design it (spec): `/architect driver role`
- [ ] Polish it (optional, ask first): `web-design-guidelines`

### 59. Mechanic home garage · planned · needs a decision · from spec 0011
Mechanics belong to no garage today (only tickets do). Give each in house mechanic a home garage (branch), so Admin can move a mechanic between garages and the assignment picker can filter by the ticket's garage.
**Done when:** each mechanic has a home garage that Admin can change (audit logged), the assignment picker can filter by garage, and moving a mechanic has its own permission key in the matrix (feature 5).
- Note (2026-10-29): later, CASL rules can use it, for example a Chief Mechanic verifying only tickets in their garage.
- [ ] Design it (spec): `/architect mechanic home garage`
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (long garage names, mechanics with no garage)

### 71. Company profile settings · planned · needs a decision
A Company section in Admin Settings for what differs between companies: name and logo, garages (branches), working hours, the ticket ID prefix, and currency. Today these are fixed in code or seed data.
**Done when:** an Admin changes each of these in Settings without a deploy, every change is audit logged like other settings, and screens and exports read them from the settings service.
- Note (2026-11-18): your call: make as much configurable as makes sense. Roles become configurable in suite S21; lists stay with feature 40. The ticket status workflow and locked security rules stay fixed on purpose (a configurable workflow is a product of its own and would weaken verification and the audit trail).
- [ ] Design it (spec): `/architect company profile settings`
