# Reports & AI

Jira WL-E6 and WL-E7. Back to [index](index.md).

## Slice 6: Reports & AI

### 45. Reports module with filters & export · planned · needs a decision
WL-601 and WL-602. One place for every export, with filters and a preview.
**Done when:** old export buttons are gone, filters cover date range, status, vehicle, mechanic, issue type, priority and in house vs outsourced, CSV and Excel export match the preview, large exports don't time out, and every export is logged.
- Note (2026-11-03): from feature 23. Ticket exports should carry the verifier's name and time (`verifiedByName`, `verifiedAt`), and a verifier filter like the one on History (`verifiedBy` on `GET /vrms/repairs/history`).
- Note (2026-11-03, replan): from spec 0020. Availability reports can join `vehicle_changes` on `repair_ticket_id`.
- [ ] Design it (spec): `/architect reports module`
- [ ] Polish it (optional, ask first): `impeccable` · `web-design-guidelines` · `break-ui` (huge result sets, empty filters, long names)

### 46. Ready made reports · planned
WL-603. The specific reports management asks for (outsourced cost, mechanic workload, overdue tickets, repairs per vehicle as a start).
**Done when:** each confirmed report type has its own view and export.
- [ ] Build it: `/develop ready made reports`
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (empty and huge reports)

### 47. AI repair suggestions · planned · needs a decision
Jira WL-E7 says optional local AI (Ollama); the code uses Gemini. Decide the provider and what the suggestion feature must do, building on feature G.
**Done when:** the provider is recorded, suggestions appear on the ticket from the chosen provider, and the app still works when AI is down.
- Note (2026-10-25): the AI is being rebuilt inside welinc-backend-vrms (see feature 3), so this builds on that rework and grounds its suggestions on the spec 0007 knowledge base, not on feature G. Design feature 3 first.
- Note (2026-10-31): spec 0013 moves the AI as is and leaves these ideas here. This feature owns the knowledge base grounding, triage while typing, search by meaning, note cleanup, drafted entries, duplicate warnings and the AI panel and feedback redesign. When grounding lands, declare `module.ai` as requiring `module.knowledge`.
- Note (2026-11-08, replan): from spec 0024. The AI card stays per ticket next to the issues; a diagnosis per issue would need new AI endpoints. Decide it here or in its own spec.
- [ ] Design it (spec): `/architect AI repair suggestions`
- [ ] Polish it (optional, ask first): `web-design-guidelines`

### 54. Account changes view · planned · from spec 0009
Admins see who changed an account and what changed, on the Users page, from the `GET /auth/users/:id/changes` endpoint spec 0009 already built.
**Done when:** an admin opens a user and sees their change record (who, when, what), newest first, with empty, loading and error states, and only admins can read it.
- Note (2026-10-28): enrolled from spec 0009's follow up. Feature 5 scopes the endpoint by system first, so build this after it. Small and frontend led, so likely no spec.
- [ ] Build it: `/develop account changes view`
- [ ] Polish it (optional, ask first): `web-design-guidelines` · `break-ui` (many changes, long values)
