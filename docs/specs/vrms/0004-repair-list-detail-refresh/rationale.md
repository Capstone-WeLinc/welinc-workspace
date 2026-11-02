# 0004. Rationale: repair list and detail refresh

Decision record for [index.md](index.md). `/develop` builds from the index; this file explains why.

## Context

The repair list and the repair detail page are the two screens VRMS users spend most of their time on. Admins work the list from laptops to decide what needs attention; mechanics open it on phones to find their next truck, then move tickets forward from the detail page. Scope feature 11 asks for both to be rebuilt on the spec 0001 design system: clear status pills and filters, cards on a phone, a detail page laid out around its one next action, and the shared dialog for every modal and prompt.

Today the list shows open tickets newest first, ten at a time, filtered only by search and status, in a hand built table with a hand built row menu. An overdue ticket created last month can sit on page three. The data to do better is already on each ticket (`targetDueDate`, `garageLocation`, `mechanics`), but the list is paginated on the server, so any order or filter the server doesn't apply is only correct for the ten rows on screen. Leaving the page loses the filters.

The detail page is one long card. Its status control is a dropdown that offers every status, while the server allows only one move forward from each status (and cancel, for admins), so most choices fail with a 400. The unlock prompt is a hand built overlay, the cost panel and AI panel use inline styles and `LegacyButton`, and the ticket's history is split across a shop change list and an audit list in two shapes. Spec 0003 has since copied shop changes into `audit_logs` and built `AuditEventItem`, leaving a follow up for this feature to use it.

Several later features land on this same page: the status lifecycle (16), mechanic status updates (19), photos (21), proof of completion (22), verification (23), the ticket timeline (32) and the admin override (33). Whatever layout this feature picks is the frame they fill. Two constraints shape it: the UI refresh phase prefers frontend only work (`· Facade`), and the deadline is the end of November 2026.

## Options considered

### Option 1: Restyle in place

Keep both pages' structure and behavior, and swap every element for its spec 0001 counterpart: `DataTable` for the table, `Select` for the dropdowns, `ResponsiveDialog` for the unlock overlay, tokens for inline styles. Frontend only.

**Pros**:
- Smallest change and fastest to ship; no backend deploy.
- No behavior to relearn for users.

**Cons**:
- The list still hides overdue tickets behind newest first ordering, and filters still reset on every visit.
- The status dropdown keeps offering moves the server rejects, which the scope's "laid out around its one next action" rules out.
- The detail page stays one long card with no frame for the features that follow.

### Option 2: Rework both pages on the data the app already loads (pure Facade)

Build the new list and detail layouts, but sort and filter on the client: fetch every open ticket in one call (the endpoint already returns all rows when `page` and `limit` are absent, which the dashboard relies on) and page through them in the browser.

**Pros**:
- No backend change, true to the UI refresh's Facade rule.
- Urgency order, garage, mechanic and overdue filters are all possible from fields already on each ticket.

**Cons**:
- Each list visit downloads every open ticket with the full include (issues, mechanics, and for admins parts and audit rows), which grows with the fleet and is slow on a phone connection.
- The mechanic no linked record bug stays: such an account still sees every open ticket.
- Two code paths do the same paging (server for History, client for this list), and moving to server paging later means rewriting the list again.

### Option 3: Rework both pages, backed by a few new query params

The same new layouts as Option 2, with sorting and filtering moved to the server through new query params on `GET /vrms/repairs` (`garageId`, `mechanicId`, `overdue`, a fixed urgency order), a `ticketId` filter on the audit endpoint for the detail Activity, and validation limits on the status DTO. No migration.

**Pros**:
- The order and every filter are correct across pages, and each request returns only one page.
- Mechanic scoping is fixed on the server in the same change.
- Activity reads the same source and renders with the same component as the audit log page.
- Follows the pattern spec 0003 already set for History.

**Cons**:
- Needs a backend deploy, so the UI refresh is no longer frontend only for this feature.
- Touches the endpoint the dashboard also uses, so its calls must move to the new params object and be rechecked.

## Rationale

Option 3 is the only one that meets the scope's own words for this feature. "Laid out around its one next action" and a list that answers what needs attention both depend on order and filters that are right on every page, and with server side paging that means the server does them. Option 2 gets there on the client, but by downloading every open ticket with its full include on each visit; that is fine at today's seed size and wrong at fleet size, and it leaves the mechanic scoping hole open. Option 1 ships fastest but keeps the two problems that most hurt users: hidden overdue tickets and a status control that mostly fails.

The cost of Option 3 is small and already familiar. The backend change is query params, a DTO and one guard, with no migration, the same shape spec 0003 shipped a day earlier. The forward only status chain the server already enforces turns directly into the one button design, so the UI gets simpler rather than more complex, and later lifecycle work (feature 16) only edits one table of moves.

Inside that choice, the engineer picked each piece: open tickets only (History owns closed ones), urgency by due date without priority (so the list and dashboard agree), every filter in the URL, 20 rows, a row menu kept for read only viewing, a main column plus side panel, a sticky bottom bar on phones, a confirm dialog with an optional note, a warning instead of a block for completing without costs, one cost section with an edit mode, Activity merged and collapsed, admins allowed every forward move, `mechanicId` ignored for mechanics, a reload on a stale save, and refetch on tab focus instead of polling (polling would move rows under the cursor while someone scans the list). Priority was dropped from the list once it turned out nothing stores it; adding a column would get ahead of the data model work (feature 4).

## Evidence: current state (read on 2026-10-22)

| Area | Today |
|---|---|
| `RepairListPage.tsx` (243 lines) | Hand built `table` and row menu, inline styles, legacy classes; 10 per page; search sent on every keystroke; filters in component state |
| `GET /vrms/repairs` | Open statuses unless `status` is given; `search`, `status`, `page`, `limit` parsed with `parseInt`; ordered `completedAt asc nulls first, createdAt desc` (effectively newest first for open tickets); a mechanic with no linked record sees every open ticket |
| `RepairDetailPage.tsx` (464 lines) | One card; status dropdown offering all statuses to admins and three to mechanics; `confirm()` before saving; `LegacyButton`; unlock through `UnlockTicketModal` (fixed position overlay) |
| `updateStatus` rules | Forward only chain `PENDING` → `IN_PROGRESS` → `FOR_VERIFICATION` → `COMPLETED`; cancel from any status, admins only; mechanics limited to their assigned tickets and the first two moves; closed tickets need an unlock; `lastUpdatedAt` mismatch returns 409; no length limit on `remarks` or `cancellationReason` |
| `CostEncodingPanel.tsx` (321 lines) | Lump sum or itemized form with inline validation messages and `confirm()` before save; separate read only summary block on the page |
| `AiDiagnosticPanel.tsx` (389 lines) | Runs triage on demand, shows causes, parts, similar cases and a star rating; inline styles; posts feedback through the raw axios instance |
| History on the detail page | `shopChangeLog` and `auditLog` arrays in two shapes; `AuditLogCollapsible`; spec 0003 filters the audit list to three actions and leaves a follow up to switch to `AuditEventItem` |
| Priority | Sent by the create form, accepted by `create-repair.dto.ts`, absent from `schema.prisma`, never returned |
| Mechanic list | `GET /vrms/mechanics/available` returns active in house mechanics with their open ticket counts; outsourced mechanics are not included |
| Phone layout | `MobileTabBar` is fixed to the bottom below 768px (`md:hidden`); the shell pads content with `pb-24` there |
