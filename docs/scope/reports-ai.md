# Reports & AI

Jira WL-E6 and WL-E7. Back to [index](index.md).

## Slice 6: Reports & AI

### 45. Reports module with filters & export · planned · needs a decision
WL-601 and WL-602. One place for every export, with filters and a preview.
**Done when:** old export buttons are gone, filters cover date range, status, vehicle, mechanic, issue type, priority and in house vs outsourced, CSV and Excel export match the preview, large exports don't time out, and every export is logged.
- [ ] Design it (spec): `/architect reports module`

### 46. Ready made reports · planned
WL-603. The specific reports management asks for (outsourced cost, mechanic workload, overdue tickets, repairs per vehicle as a start).
**Done when:** each confirmed report type has its own view and export.
- [ ] Build it: `/develop ready made reports`

### 47. AI repair suggestions · planned · needs a decision
Jira WL-E7 says optional local AI (Ollama); the code uses Gemini. Decide the provider and what the suggestion feature must do, building on feature G.
**Done when:** the provider is recorded, suggestions appear on the ticket from the chosen provider, and the app still works when AI is down.
- [ ] Design it (spec): `/architect AI repair suggestions`
