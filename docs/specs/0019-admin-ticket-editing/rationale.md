# 0019. Admin ticket editing: rationale

## Context

Today nothing on a ticket can change after create except status, costs, the known fix link and step ticks. Intake mistakes (wrong driver, mistyped odometer, wrong issue, wrong priority or corporation) stay wrong, or need a database edit with no audit. Mechanics can only be assigned while a ticket is Open (spec 0016), so work can't move once it has started, although spec 0015 decided the Chief Mechanic should be able to reassign.

The forces:
- **Audit**: every change must leave a before and after trail (spec 0010 audit shape), and the team wanted a quick "last edited by" on the ticket too.
- **Concurrency**: Admin, Chief and mechanics touch the same ticket. The existing optimistic lock (`lastUpdatedAt`, 409 `STALE_TICKET`) is the project's pattern.
- **Live view**: VR-RL-12 asks that a reassignment show on both platforms within 3 seconds. Today the dashboard polls every 15 seconds and the list refetches only on focus.
- **Invariants from earlier specs**: the transition table (spec 0014, M1/M2), the one issue minimum from create, the odometer floor (spec 0016), the "never verify your own ticket" rule, and the closed ticket lock with Admin unlock (specs 0004, 0014).
- **Time**: about four weeks to deployment, and hosting is not built yet, so new infrastructure is expensive.

## Options considered

### Option 1: Per section endpoints and dialogs, 3 second polling (chosen)
One small endpoint and dialog per block (details, mechanics, issues), each with its own stale check and audit rows; live view by polling the existing reads every 3 seconds while visible.

**Pros**: small saves mean cheap 409s; each endpoint has one permission key; matches the existing Costs edit and Assign dialog; no new infrastructure.
**Cons**: five new routes; polling load grows with users; the 3 second target is met as "at most 3 seconds late", not instantly.

### Option 2: One whole ticket edit mode, one PATCH
The detail page turns into a form, saved once with any subset of fields.

**Pros**: one route, one save, one place in the UI.
**Cons**: mixed permission keys in one body (details by Admin, mechanics by Chief); a 409 loses more typed work; one large mixed audit event is hard to filter.

### Option 3: Reuse the repair form page as an edit page
Open `/repairs/:id/edit` with the create form prefilled.

**Pros**: familiar screen, shared validation.
**Cons**: the form carries create only rules (one open ticket per truck, the vehicle picker); a new page where the existing one can hold the view (team preference); the same mixed key and big 409 problems as Option 2.

### Live update alternative: server sent events
Push a "ticket changed" event over one open connection.

**Pros**: near instant, and feature 28 could reuse it.
**Cons**: every write must publish an event; the gateway needs buffering off for that route; Azure Container Apps idle limits need heartbeats; more than one replica needs a shared bus. Too much new moving parts before hosting exists.

## Rationale

Per section editing fits the two permission keys the team chose (`ticket.edit` for Admin corrections, `ticket.assign` for the Chief's reassign from spec 0015). It keeps each optimistic lock window small, which matters because mechanics are working on the same ticket while an Admin edits. It also extends the detail page instead of adding a page.

Polling is boring and already the app's pattern (dashboard, permissions). At about 20 users it costs a few requests a second, needs no gateway or hosting change, and meets VR-RL-12. SSE is the better end state and is left to feature 28, where a push channel earns its cost.

The team chose to allow an empty mechanic list after work starts, because the ticket can always be reassigned. The spec keeps M2 on Assigned (an Assigned ticket with nobody is a contradiction) and adds a "No mechanic" attention flag so ownerless work is seen. Removing issues with recorded work is allowed because Admins correct mistakes, but the one issue minimum stays: create requires it, send for verification checks notes per issue, and reports group by issue system.

On unlocked closed tickets everything is editable, as the team asked. Two guards keep history honest: a required reason, and a block on adding the verifier as a mechanic.

Decisions made by the architect (runner up in brackets):
- **Odometer edit bounds**: floor from earlier tickets, ceiling from later ones, so readings stay in time order [floor from every other ticket, which would block lowering the latest wrong reading].
- **Mechanic audit**: two rows (`MECHANIC_UNASSIGNED`, then `MECHANIC_ASSIGNED`) reusing existing actions [a new `MECHANIC_REASSIGNED` action, which would add a filter name for a combined event].
- **Keep `POST /repairs/:id/assignments` as a thin alias over the PUT logic for now**: the web app and backend deploy separately, so an older web build keeps working; removal is a Follow-up [remove it now, which breaks an older client mid deploy].
- **Remove issue as `POST …/remove`**, not `DELETE` with a body, which some proxies drop [query params, which put the reason in access logs].
- **Edits on unlocked tickets do not relock**: an Admin may need several fixes; the existing status save still relocks [relock on first edit, which forces an unlock per fix].
- **Poll interval as a code constant**: not a Settings value, since it is a technical target, not a business rule [a setting].
